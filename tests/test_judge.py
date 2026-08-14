"""The pending queue and the verdict: judgement proposes, and the queue clears."""

from __future__ import annotations

from datetime import datetime

from vigil.journal import Journal
from vigil.judge import Verdict, file_verdict, pending_judgements

AT = datetime(2026, 8, 12, 9, 0)

VERDICT = Verdict(reading="genuine", subject_challenged=True,
                  reasoning="the change is the fact the claim feared",
                  proposes="review", confidence=0.9)


def _fire(j: Journal, node="s/c"):
    j.append("criterion-fired", AT, subject="s", node=node, role="criterion",
             claim="it changed")


def test_a_firing_pends_until_judged(tmp_path):
    j = Journal(tmp_path / "j.jsonl")
    _fire(j)
    assert len(pending_judgements(j)) == 1
    file_verdict(j, VERDICT, subject="s", node="s/c", at=AT)
    assert pending_judgements(j) == []


def test_a_refire_after_judgement_pends_again(tmp_path):
    j = Journal(tmp_path / "j.jsonl")
    _fire(j)
    file_verdict(j, VERDICT, subject="s", node="s/c", at=AT)
    _fire(j)
    assert len(pending_judgements(j)) == 1


def test_pending_filters_by_subject(tmp_path):
    j = Journal(tmp_path / "j.jsonl")
    _fire(j, node="s/c")
    j.append("criterion-fired", AT, subject="other", node="other/c",
             role="criterion", claim="x")
    assert len(pending_judgements(j)) == 2
    assert len(pending_judgements(j, subject="s")) == 1


def test_the_verdict_event_carries_provenance_and_source(tmp_path):
    j = Journal(tmp_path / "j.jsonl")
    _fire(j)
    file_verdict(j, VERDICT, subject="s", node="s/c", at=AT)
    [e] = j.events("judgement")
    assert e.body["provenance"] == "inferred"
    assert e.body["source"] == "ai client"
    assert e.body["reading"] == "genuine"
    assert e.body["proposes"] == "review"
