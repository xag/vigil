"""The daemon tick: deterministic watching, no judgement, no action.

One tick does, for every subject path it is handed:

1. find its watchable children — nodes carrying a compiled `payload.expr`;
2. decide if each is due (its `payload.cadence` vs the journal's last observation);
3. materialise the feed window for every `ctx('key')` the expr names (all I/O here —
   the evaluation itself stays pure over the window, so replaying recorded windows
   through this same function IS the backtest);
4. lift the expr into a path-pinned quern rule and evaluate it;
5. journal an `observation` every time, a `criterion-fired` only on the
   **false -> true edge** (a criterion that stays breached must not re-fire every
   tick), and a `gap` when a watcher cannot watch (missing feed, broken expr, a
   window too short to answer) — an unwatched criterion must be visible, never silent;
6. for a fired criterion whose payload names `proposes`, append a `proposal` to move
   the subject there. The daemon NEVER moves the subject — proposing is data, moving
   is a human act that lives with whoever owns the subject's state machine.

Which subjects are watched is the caller's decision (a notebook watches its active
theses; a surface critic watches its surfaces) — the tick takes the paths and asks no
question about what they mean.

Returns the tick's firings and gaps so a caller can notify. Notification transport,
judgement gates and any acting-on-verdicts all live above this layer.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Iterable

from quern import Quern, Rule, find_nodes, run_rules

from .feeds import Feed, FeedError
from .journal import Journal

CADENCES: dict[str, timedelta] = {
    "minutely": timedelta(minutes=1),
    "hourly": timedelta(hours=1),
    "daily": timedelta(days=1),
    "weekly": timedelta(weeks=1),
    "monthly": timedelta(days=30),
    "quarterly": timedelta(days=90),
}

_CTX_KEYS = re.compile(r"ctx\(\s*['\"]([^'\"]+)['\"]\s*\)")


@dataclass
class Firing:
    subject: str
    node: str
    role: str          # the criterion node's kind — vigil never interprets it
    claim: str
    expr: str


@dataclass
class TickReport:
    at: datetime
    checked: list[str] = field(default_factory=list)
    firings: list[Firing] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)      # human-readable, journaled too


def watchables(tree: Quern, subject_path: str) -> list[tuple[str, "object"]]:
    """(path, node) pairs under the subject that carry a compiled expr."""
    return [(p, n) for p, n in find_nodes(tree, under=subject_path, limit=1000)
            if isinstance(n.payload.get("expr"), str)]


def due(journal: Journal, node_path: str, cadence: str, now: datetime) -> bool:
    period = CADENCES.get(cadence)
    if period is None:
        return True  # unknown cadence: check rather than silently skip
    last = journal.last("observation", node=node_path)
    if last is None:
        return True
    return now - datetime.fromisoformat(last.at) >= period


def evaluate(tree: Quern, node_path: str, expr: str, context: dict) -> bool:
    """Lift the node's expr into a path-pinned rule and run it — the exact evaluation
    path quern's own checks use, pure over the supplied context."""
    staged = tree.model_copy()          # shallow: shares the root, replaces rules
    staged.rules = [Rule(name=f"{node_path}::watch", path=node_path, expr=expr)]
    [res] = run_rules(staged, path=node_path, context=context)
    if res.detail:
        raise ValueError(res.detail)    # a broken rule is a gap, not a quiet False
    return res.ok


def tick(tree: Quern, journal: Journal, feed: Feed, now: datetime,
         subjects: Iterable[str]) -> TickReport:
    report = TickReport(at=now)
    for subject_path in subjects:
        for node_path, node in watchables(tree, subject_path):
            cadence = str(node.payload.get("cadence", ""))
            if not due(journal, node_path, cadence, now):
                continue
            report.checked.append(node_path)
            expr = node.payload["expr"]

            try:
                context = {k: feed.window(k, now) for k in _CTX_KEYS.findall(expr)}
                ok = evaluate(tree, node_path, expr, context)
            except (FeedError, ValueError) as e:
                msg = f"{node_path}: cannot watch — {e}"
                journal.append("gap", now, subject=subject_path, node=node_path,
                               error=str(e))
                report.gaps.append(msg)
                continue

            prev = journal.last("observation", node=node_path)
            journal.append("observation", now, subject=subject_path, node=node_path,
                           ok=ok, role=node.kind,
                           window={k: v[-4:] for k, v in context.items()})

            if ok and not (prev and prev.body.get("ok")):   # false -> true edge
                claim = str(node.payload.get("claim", node.name or node_path))
                journal.append("criterion-fired", now, subject=subject_path,
                               node=node_path, role=node.kind, claim=claim)
                report.firings.append(Firing(subject=subject_path, node=node_path,
                                             role=node.kind, claim=claim, expr=expr))
                proposes = node.payload.get("proposes")
                if isinstance(proposes, str) and proposes:
                    journal.append("proposal", now, subject=subject_path,
                                   node=node_path, to=proposes,
                                   why=f"criterion fired: {claim}")
    return report


def replay(tree: Quern, journal: Journal, feed: Feed, ticks: list[datetime],
           subjects: Iterable[str]) -> list[TickReport]:
    """The backtest: the production tick over recorded windows, one call per instant.
    Determinism is inherited, not implemented — evaluation is pure over what the feed
    serves at each `as_of`."""
    subjects = list(subjects)
    return [tick(tree, journal, feed, t, subjects) for t in ticks]
