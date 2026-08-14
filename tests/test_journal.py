"""The journal is append-only, seq-chained, and refuses edited history."""

from __future__ import annotations

from datetime import datetime

import pytest

from vigil.journal import Journal, JournalError

AT = datetime(2026, 8, 10, 9, 0)


def test_append_assigns_dense_seq(tmp_path):
    j = Journal(tmp_path / "j.jsonl")
    e1 = j.append("observation", AT, subject="s", node="s/c", ok=False)
    e2 = j.append("criterion-fired", AT, subject="s", node="s/c", claim="x")
    assert (e1.seq, e2.seq) == (1, 2)
    assert len(j) == 2


def test_reload_reads_back_what_was_written(tmp_path):
    path = tmp_path / "j.jsonl"
    j = Journal(path)
    j.append("observation", AT, subject="s", node="s/c", ok=True, window={"k": [1]})
    j2 = Journal(path)
    [e] = j2.events()
    assert e.kind == "observation"
    assert e.subject == "s"
    assert e.body["window"] == {"k": [1]}


def test_a_broken_chain_refuses_to_load(tmp_path):
    path = tmp_path / "j.jsonl"
    j = Journal(path)
    j.append("observation", AT)
    j.append("observation", AT)
    lines = path.read_text(encoding="utf-8").splitlines()
    path.write_text(lines[1] + "\n", encoding="utf-8")  # history edited: seq starts at 2
    with pytest.raises(JournalError, match="chain is broken"):
        Journal(path)


def test_projections_filter_by_kind_subject_node(tmp_path):
    j = Journal(tmp_path / "j.jsonl")
    j.append("observation", AT, subject="a", node="a/c")
    j.append("observation", AT, subject="b", node="b/c")
    j.append("gap", AT, subject="a", node="a/c", error="x")
    assert len(j.events("observation")) == 2
    assert len(j.events(subject="a")) == 2
    assert j.last("gap").subject == "a"
    assert j.last("judgement") is None


def test_status_is_a_projection(tmp_path):
    j = Journal(tmp_path / "j.jsonl")
    assert j.status_of("s") == "watched"
    j.append("status-changed", AT, subject="s", to="retired")
    assert j.status_of("s") == "retired"
