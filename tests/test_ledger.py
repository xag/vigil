"""The ledger's own rules, asserted as what they are: green today, and red the moment a
founding decision stops naming what it rejected.

The suite asserts what is TRUE, never what we wish were true. The one deliberate debt
this repo carries (the source still ships its copy of the loop) is authored with its
discharge condition, so it is green under the rules while remaining visibly owed.
"""

from __future__ import annotations

from quern import run_rules

from vigil.tree import build


def test_the_ledger_is_green():
    results = run_rules(build())
    red = [f"{r.rule} @ {r.node}: {r.detail}" for r in results if not r.ok]
    assert not red, "the ledger is red:\n" + "\n".join(red)


def test_the_founding_record_is_actually_there():
    """A green ledger with nothing in it is green for the wrong reason."""
    tree = build()
    kinds = [c.kind for c in tree.root.children]
    assert kinds.count("decision") >= 3
    assert kinds.count("hypothesis") >= 1
    assert kinds.count("debt") >= 1


def test_the_rules_are_the_pinned_packages_own():
    """The rules that judge this ledger are the pinned `ledger@`'s — not re-authored.

    The list is exact, so a version bump lands here deliberately: reading the new
    rules and saying they are the ones now judging this ledger is the point of the
    guard, and a set loosened to `>=` would let a rule vanish silently.
    """
    tree = build()
    assert {r.name for r in tree.rules} == {
        "a-decision-names-what-it-rejected",
        "a-hypothesis-is-falsifiable",
        "a-debt-states-how-it-is-discharged",
        "nothing-unsound-passes-a-gate",
        "what-a-decision-rests-on-still-stands",
        "what-a-hypothesis-rests-on-still-stands",
        "what-a-debt-rests-on-still-stands",
        "a-retraction-names-what-it-buried",
        "a-compaction-names-what-it-buried",
        "a-decision-fits-its-reader",
        "a-hypothesis-fits-its-reader",
        "a-debt-fits-its-reader",
    }, "the effective rules are not the twelve the pinned ledger@ ships"

    fired = {r.rule for r in run_rules(tree)}
    assert "a-decision-names-what-it-rejected" in fired
    assert "a-hypothesis-is-falsifiable" in fired
    assert "a-debt-states-how-it-is-discharged" in fired
