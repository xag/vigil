"""Judgement: the qualitative review when a deterministic threshold trips.

When a criterion FIRES, someone must answer the question the rule cannot — is this
firing the fact the claim feared, an artifact of the instrument or feed, or noise that
happens to satisfy the predicate? Two paths provide that answer; both journal the same
`judgement` event (structured Verdict, provenance `inferred`) and both **propose
only** — nothing in this library moves a subject, and whoever owns the subject's state
machine should refuse every non-human transition.

**Primary path — the AI client (subscription intelligence, zero marginal cost).**
The daemon stays deterministic and dumb; the intelligence is the client's. The daemon
journals the firing and notifies; the next time a session opens over this journal,
`pending_judgements()` lists what fired unjudged, the client judges with the subject's
context in view, and `file_verdict()` journals its verdict (source "ai client"). Since
acting on a verdict needs the human anyway — and the human arrives WITH the client —
this loses nothing but the API bill.

**Opt-in path — the unattended API judge (`Judge`/`JudgingNotifier`).** Only for a
deployment where verdicts must land within minutes with nobody around. Metered
Anthropic API (official SDK, imported lazily; adaptive thinking, schema-validated
structured output via `messages.parse`). Nothing instantiates it by default. A judge
failure is a `gap`, never a blocked watch. The system prompt and the per-firing prompt
are injectable, because what a judge must know is the domain's — the defaults only know
the loop.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Iterable, Literal

from pydantic import BaseModel

from quern import Quern, get_node

from .daemon import Firing, TickReport
from .journal import Journal

MODEL = "claude-opus-5"

DEFAULT_SYSTEM = (
    "You are the judgement gate of a vigil — a deterministic watcher just fired one of "
    "a subject's compiled criteria against real evidence, and you are asked the one "
    "question the rule cannot answer: is this firing the fact the claim was written to "
    "catch, an artifact (an instrument change, a feed glitch, a re-rendering that "
    "means nothing), or noise that happens to satisfy the predicate?\n\n"
    "Rules of the vigil you must respect:\n"
    "- The prose claim is the meaning; the expr is only its mechanization. Judge "
    "against the claim.\n"
    "- You PROPOSE only. Humans move subjects. Calibrate your confidence honestly — "
    "your verdicts are journaled and reviewed against outcomes later.\n"
    "- Prefer 'artifact' or 'noise' when the window itself looks inconsistent with "
    "the claim; say so plainly in the reasoning."
)


class Verdict(BaseModel):
    """The structured judgement, schema-enforced by the API."""

    reading: Literal["genuine", "artifact", "noise"]
    subject_challenged: bool
    reasoning: str
    proposes: str = ""   # a status the judge proposes moving the subject to; "" = none
    confidence: float    # 0..1, self-assessed


class JudgeError(RuntimeError):
    """The gate could not produce a verdict (refusal, API failure, bad output)."""


# --- the primary path: judgement by the AI client -----------------------------------

def pending_judgements(journal: Journal, subject: str | None = None) -> list:
    """The review queue: `criterion-fired` events not yet answered by a `judgement`
    for the same node. A later judgement clears the firings before it; a re-fire after
    a judgement pends again. This is what a server built on vigil serves the AI client
    when the user opens it."""
    pending: dict[str, list] = {}
    for e in journal.events():
        if subject is not None and e.subject != subject:
            continue
        if e.kind == "criterion-fired":
            pending.setdefault(e.node, []).append(e)
        elif e.kind == "judgement":
            pending.pop(e.node, None)
    return sorted((e for firings in pending.values() for e in firings),
                  key=lambda e: e.seq)


def file_verdict(journal: Journal, verdict: Verdict, *, subject: str, node: str,
                 at: datetime | str, source: str = "ai client"):
    """Journal a verdict produced by the AI client — the exact event shape the API
    judge writes, so calibration review later cannot tell the paths apart except by
    `source`. Proposes only, like everything non-human."""
    return journal.append(
        "judgement", at, subject=subject, node=node,
        **verdict.model_dump(), provenance="inferred", source=source)


# --- the opt-in path: the unattended API judge --------------------------------------

def default_prompt(tree: Quern, journal: Journal, firing: Firing) -> str:
    subject = get_node(tree, firing.subject)
    obs = journal.events("observation", node=firing.node)[-6:]
    history = "\n".join(
        f"- {e.at}: ok={e.body.get('ok')} window={e.body.get('window')}"
        for e in obs) or "(no prior observations)"
    payload = dict(subject.payload) if subject is not None else {}
    return (
        f"SUBJECT ({firing.subject}): {subject.name if subject else '?'}\n"
        f"subject payload: {payload}\n\n"
        f"FIRED {firing.role} ({firing.node}):\n"
        f"claim: {firing.claim}\n"
        f"compiled test: {firing.expr}\n\n"
        f"recent observations of this criterion (oldest first):\n{history}\n\n"
        "Judge this firing.")


class Judge:
    """Wraps one firing -> one verdict via the metered Anthropic API. Opt-in: use only
    when verdicts must land unattended; the primary path is the AI client (see module
    docstring). `client` is any object with the `messages.parse` surface — the real
    `anthropic.Anthropic()` by default, a stub in tests. `system` and `prompt` inject
    the domain's knowledge; the defaults only know the loop."""

    def __init__(self, client: Any = None, model: str = MODEL,
                 system: str = DEFAULT_SYSTEM,
                 prompt: Callable[[Quern, Journal, Firing], str] = default_prompt,
                 ) -> None:
        if client is None:
            import anthropic  # lazy: the core never needs the SDK unless judging
            client = anthropic.Anthropic()
        self._client = client
        self._model = model
        self._system = system
        self._prompt = prompt

    def review(self, tree: Quern, journal: Journal, firing: Firing,
               at: datetime) -> Verdict:
        """Judge one firing, journal the verdict, return it. Raises JudgeError."""
        prompt = self._prompt(tree, journal, firing)
        try:
            response = self._client.messages.parse(
                model=self._model,
                max_tokens=16000,
                thinking={"type": "adaptive"},
                system=self._system,
                messages=[{"role": "user", "content": prompt}],
                output_format=Verdict,
            )
        except Exception as e:
            raise JudgeError(f"judgement call failed: {e}") from e
        if getattr(response, "stop_reason", None) == "refusal":
            raise JudgeError("judgement refused by the model's safety layer")
        verdict = getattr(response, "parsed_output", None)
        if verdict is None:
            raise JudgeError("no structured verdict in the response")
        journal.append(
            "judgement", at, subject=firing.subject, node=firing.node,
            **verdict.model_dump(),
            provenance="inferred", source=f"llm {self._model}")
        return verdict


class JudgingNotifier:
    """Composes the gate into the scheduler without touching it: judges firings,
    journals verdicts (failures journal as gaps), then forwards the report to the
    wrapped notifier. Implements the Notifier protocol, so it drops into
    Scheduler(notifier=...). `roles=None` judges every firing; pass an iterable of
    criterion kinds to judge only those — the roles are the domain's words, and this
    class carries none of its own."""

    def __init__(self, inner, judge: Judge, tree: Quern, journal: Journal,
                 roles: Iterable[str] | None = None) -> None:
        self._inner = inner
        self._judge = judge
        self._tree = tree
        self._journal = journal
        self._roles = None if roles is None else set(roles)

    def notify(self, report: TickReport) -> None:
        for f in report.firings:
            if self._roles is not None and f.role not in self._roles:
                continue
            try:
                self._judge.review(self._tree, self._journal, f, report.at)
            except JudgeError as e:
                self._journal.append("gap", report.at, subject=f.subject,
                                     node=f.node, error=str(e))
                report.gaps.append(f"{f.node}: {e}")
        self._inner.notify(report)
