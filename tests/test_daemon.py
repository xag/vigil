"""The tick: due, edge-firing, visible gaps, and proposals as data."""

from __future__ import annotations

from datetime import datetime, timedelta

from quern import Node, Quern

import vigil.natives  # noqa: F401 -- arms the vigil/* contracts

from vigil.daemon import tick
from vigil.feeds import StaticFeed
from vigil.journal import Journal

D1 = datetime(2026, 8, 10, 9, 0)
D2 = D1 + timedelta(days=1)
D3 = D2 + timedelta(days=1)
D4 = D3 + timedelta(days=1)


def _tree(expr: str, proposes: str | None = None) -> Quern:
    payload = {"claim": "the surface changed", "expr": expr,
               "cadence": "daily", "feed": "walker"}
    if proposes is not None:
        payload["proposes"] = proposes
    tree = Quern()
    tree.root.children = [
        Node(id="surface", kind="surface", name="a watched surface",
             children=[Node(id="crit", kind="criterion", name="it changed",
                            payload=payload)]),
    ]
    return tree


def _feed(values):
    return StaticFeed({"k": values})


def test_short_window_is_a_gap_never_a_silent_green(tmp_path):
    tree = _tree("solve('vigil/changed', ctx('k')) >= 1")
    j = Journal(tmp_path / "j.jsonl")
    r = tick(tree, j, _feed([(D1, "a")]), D1, ["surface"])
    assert r.firings == []
    assert len(r.gaps) == 1
    [gap] = j.events("gap")
    assert "at least 2" in gap.body["error"]


def test_fires_on_the_false_to_true_edge_only(tmp_path):
    tree = _tree("solve('vigil/changed', ctx('k')) >= 1")
    j = Journal(tmp_path / "j.jsonl")
    feed = _feed([(D1, "a"), (D2, "a"), (D3, "b")])
    assert tick(tree, j, feed, D2, ["surface"]).firings == []   # a,a: unchanged
    r3 = tick(tree, j, feed, D3, ["surface"])                   # a,b: changed
    assert len(r3.firings) == 1
    f = r3.firings[0]
    assert (f.subject, f.node, f.role) == ("surface", "surface/crit", "criterion")


def test_a_criterion_that_stays_breached_does_not_refire(tmp_path):
    # `len(ctx('k')) >= 2` becomes true on day 2 and stays true after.
    tree = _tree("len(ctx('k')) >= 2")
    j = Journal(tmp_path / "j.jsonl")
    feed = _feed([(D1, "a"), (D2, "a"), (D3, "a"), (D4, "a")])
    assert tick(tree, j, feed, D1, ["surface"]).firings == []
    assert len(tick(tree, j, feed, D2, ["surface"]).firings) == 1
    assert tick(tree, j, feed, D3, ["surface"]).firings == []   # still true: no edge
    assert tick(tree, j, feed, D4, ["surface"]).firings == []
    assert len(j.events("criterion-fired")) == 1


def test_cadence_spaces_the_looks(tmp_path):
    tree = _tree("len(ctx('k')) >= 2")
    j = Journal(tmp_path / "j.jsonl")
    feed = _feed([(D1, "a"), (D2, "a")])
    tick(tree, j, feed, D2, ["surface"])
    same_day = tick(tree, j, feed, D2 + timedelta(hours=1), ["surface"])
    assert same_day.checked == []                               # daily: not due yet
    next_day = tick(tree, j, feed, D3, ["surface"])
    assert next_day.checked == ["surface/crit"]


def test_a_fired_proposes_payload_journals_a_proposal(tmp_path):
    tree = _tree("len(ctx('k')) >= 2", proposes="review")
    j = Journal(tmp_path / "j.jsonl")
    feed = _feed([(D1, "a"), (D2, "a")])
    tick(tree, j, feed, D2, ["surface"])
    [p] = j.events("proposal")
    assert p.body["to"] == "review"
    assert "criterion fired" in p.body["why"]


def test_no_proposes_means_no_proposal(tmp_path):
    tree = _tree("len(ctx('k')) >= 2")
    j = Journal(tmp_path / "j.jsonl")
    tick(tree, j, _feed([(D1, "a"), (D2, "a")]), D2, ["surface"])
    assert j.events("proposal") == []


def test_a_missing_feed_key_is_a_gap(tmp_path):
    tree = _tree("solve('vigil/changed', ctx('absent')) >= 1")
    j = Journal(tmp_path / "j.jsonl")
    r = tick(tree, j, _feed([(D1, "a"), (D2, "a")]), D2, ["surface"])
    assert len(r.gaps) == 1
    assert "no series" in j.events("gap")[0].body["error"]


def test_every_look_is_an_observation_with_the_window_tail(tmp_path):
    tree = _tree("solve('vigil/changed', ctx('k')) >= 1")
    j = Journal(tmp_path / "j.jsonl")
    tick(tree, j, _feed([(D1, "a"), (D2, "b")]), D2, ["surface"])
    [obs] = j.events("observation")
    assert obs.body["ok"] is True
    assert obs.body["window"]["k"] == ["a", "b"]
