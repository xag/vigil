"""The seams a domain adopts through: event class, legacy decode, live subject
selection, and the domain's own verdict schema. Each test plays the adopting domain."""

from __future__ import annotations

import json
from datetime import datetime, timedelta

from pydantic import BaseModel
from quern import Node, Quern

import vigil.natives  # noqa: F401

from vigil.daemon import tick
from vigil.feeds import StaticFeed
from vigil.journal import Event, Journal
from vigil.judge import Judge, JudgingNotifier
from vigil.scheduler import Scheduler

T0 = datetime(2026, 8, 10, 9, 0)


# --- journal: event_class + _decode ------------------------------------------------

class OwnerEvent(Event):
    @property
    def owner(self) -> str:  # the domain's word for the subject
        return self.subject


class OwnerJournal(Journal):
    event_class = OwnerEvent

    def _decode(self, d: dict) -> Event:
        d = dict(d)
        d.setdefault("subject", d.pop("owner", ""))  # legacy files named it 'owner'
        return super()._decode(d)


def test_a_domain_reads_its_legacy_field_without_rewriting_history(tmp_path):
    path = tmp_path / "j.jsonl"
    legacy = {"seq": 1, "at": T0.isoformat(), "kind": "criterion-fired",
              "owner": "t", "node": "t/kill", "body": {"claim": "x"}}
    path.write_text(json.dumps(legacy) + "\n", encoding="utf-8")

    j = OwnerJournal(path)
    [e] = j.events()
    assert e.owner == "t" and e.subject == "t"

    j.append("judgement", T0, subject="t", node="t/kill", reading="genuine")
    lines = path.read_text(encoding="utf-8").splitlines()
    assert "owner" in lines[0] and "subject" in lines[1]  # history untouched, new shape forward
    assert all(isinstance(e, OwnerEvent) for e in OwnerJournal(path).events())


# --- scheduler: live subject selection + the tick_once seam ------------------------

def _tree() -> Quern:
    tree = Quern()
    tree.root.children = [
        Node(id="s", kind="surface", name="s",
             children=[Node(id="c", kind="criterion", name="c",
                            payload={"claim": "grew", "expr": "len(ctx('k')) >= 2",
                                     "cadence": "daily", "feed": "f"})]),
    ]
    return tree


def test_callable_subjects_are_reselected_every_tick(tmp_path):
    j = Journal(tmp_path / "j.jsonl")
    feed = StaticFeed({"k": [(T0, "a"), (T0 + timedelta(days=1), "a")]})
    active: list[str] = []

    class Sink:
        def notify(self, r): ...

    clock = iter([T0, T0 + timedelta(days=1)])
    sched = Scheduler(tree=_tree(), journal=j, feed=feed, notifier=Sink(),
                      subjects=lambda: list(active),
                      clock=lambda: next(clock), sleep=lambda s: None)
    assert sched.run_once().checked == []      # nothing selected: nothing watched
    active.append("s")
    assert sched.run_once().checked == ["s/c"]  # selection re-evaluated live


def test_a_domain_overrides_tick_once_and_keeps_the_watch_loop(tmp_path):
    j = Journal(tmp_path / "j.jsonl")

    class DomainScheduler(Scheduler):
        def tick_once(self, now):
            raise RuntimeError("domain tick broke")

    class Sink:
        def __init__(self): self.reports = []
        def notify(self, r): self.reports.append(r)

    sink = Sink()
    sched = DomainScheduler(tree=_tree(), journal=j, feed=StaticFeed({}),
                            notifier=sink, clock=lambda: T0, sleep=lambda s: None)
    report = sched.run_once()                  # the loop survives and journals a gap
    assert report.gaps and j.events("gap")
    assert sink.reports == [report]


# --- judge: the domain's own verdict schema ----------------------------------------

class DomainVerdict(BaseModel):
    reading: str
    severity: str          # a field the loop's Verdict does not have
    reasoning: str
    confidence: float


class StubClient:
    def __init__(self, verdict):
        self.requests = []
        outer = self

        class _Messages:
            def parse(self, **kwargs):
                outer.requests.append(kwargs)

                class R:
                    parsed_output = verdict
                    stop_reason = "end_turn"
                return R()

        self.messages = _Messages()


def test_the_judge_enforces_the_domains_schema_and_journals_its_fields(tmp_path):
    tree = _tree()
    j = Journal(tmp_path / "j.jsonl")
    feed = StaticFeed({"k": [(T0, "a"), (T0 + timedelta(days=1), "a")]})
    report = tick(tree, j, feed, T0 + timedelta(days=1), ["s"])
    assert report.firings

    verdict = DomainVerdict(reading="genuine", severity="high",
                            reasoning="the domain knows", confidence=0.7)
    client = StubClient(verdict)
    judge = Judge(client=client, verdict_model=DomainVerdict)
    JudgingNotifier(type("Sink", (), {"notify": lambda self, r: None})(),
                    judge, tree, j).notify(report)

    [req] = client.requests
    assert req["output_format"] is DomainVerdict   # identity: the schema is the domain's
    [ev] = j.events("judgement")
    assert ev.body["severity"] == "high"
