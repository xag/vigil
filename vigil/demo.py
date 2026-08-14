"""A surface critic in miniature. `uv run python -m vigil.demo`

The founding scar of the estate's testing story: an empty screen that said "there is
nothing to add" forty pixels above a button marked ADD — with 486 tests passing,
because none of them reads. This demo is the standing loop that would have caught the
day it shipped: a walker deposits each day's rendered prose into a feed; a criterion
watches "did the screen change since it was last judged"; the firing queues for
judgment; the verdict proposes a review and moves nothing.

Everything is deterministic — fixed dates, an in-memory feed, a journal in a temp
directory — so two runs print the same story.
"""

from __future__ import annotations

import tempfile
from datetime import datetime
from pathlib import Path

from quern import Node, Quern

import vigil.natives  # noqa: F401 -- arms the vigil/* contracts

from .daemon import tick
from .feeds import StaticFeed
from .journal import Journal
from .judge import Verdict, file_verdict, pending_judgements

DAY1 = datetime(2026, 8, 10, 9, 0)
DAY2 = datetime(2026, 8, 11, 9, 0)
DAY3 = datetime(2026, 8, 12, 9, 0)

SCREEN_OK = "Your basket is empty. | [ ADD ITEM ]"
SCREEN_SCAR = "There is nothing to add. | [ ADD ITEM ]"


def build_tree() -> Quern:
    tree = Quern()
    tree.root.children = [
        Node(id="checkout", kind="surface", name="the checkout screen",
             children=[
                 Node(id="reads-differently", kind="criterion",
                      name="The checkout screen reads differently than when it was "
                           "last judged",
                      payload={
                          "claim": "The rendered prose of the checkout screen "
                                   "differs from what the last judgement read",
                          "expr": "solve('vigil/changed', ctx('surface:checkout')) >= 1",
                          "cadence": "daily",
                          "feed": "walker",
                      }),
             ]),
    ]
    return tree


def main() -> None:
    tree = build_tree()
    feed = StaticFeed({"surface:checkout": [
        (DAY1, SCREEN_OK),
        (DAY2, SCREEN_OK),
        (DAY3, SCREEN_SCAR),
    ]})
    journal = Journal(Path(tempfile.mkdtemp()) / "vigil-demo.jsonl")
    subjects = ["checkout"]

    print("day 1 - the walker's first reading of the surface")
    r1 = tick(tree, journal, feed, DAY1, subjects)
    for g in r1.gaps:
        print(f"  GAP {g}")
    print("  one reading cannot answer 'did it change' - a visible gap, never a "
          "silent green.\n")

    print("day 2 - same prose as yesterday")
    r2 = tick(tree, journal, feed, DAY2, subjects)
    print(f"  firings: {len(r2.firings)}, gaps: {len(r2.gaps)} - watched, quiet.\n")

    print("day 3 - the empty state now contradicts the button beneath it")
    r3 = tick(tree, journal, feed, DAY3, subjects)
    for f in r3.firings:
        print(f"  FIRED {f.node}: {f.claim}")

    queue = pending_judgements(journal)
    print(f"\npending judgements: {len(queue)} - the critical eye opens on demand,")
    print("not on every walk. A reader now judges the firing against the claim:")
    print(f'  before: "{SCREEN_OK}"')
    print(f'  after:  "{SCREEN_SCAR}"')

    verdict = Verdict(
        reading="genuine",
        subject_challenged=True,
        reasoning="The empty state now asserts there is nothing to add directly "
                  "above a control offering to add - the copy contradicts the "
                  "surface it lives on. Not an instrument artifact: the walker's "
                  "window shows a real change in rendered prose.",
        proposes="review",
        confidence=0.9,
    )
    file_verdict(journal, verdict, subject="checkout",
                 node=queue[0].node, at=DAY3)
    print(f"\nverdict: {verdict.reading} (confidence {verdict.confidence}) - "
          f"proposes '{verdict.proposes}'.")
    print(f"pending after judgement: {len(pending_judgements(journal))}")

    print("\njournal, in full:")
    for e in journal.events():
        print(f"  {e.seq}. {e.at} {e.kind:<16} {e.node or e.subject}")

    print("\nThe verdict proposes; nothing moved. Moving the subject is a human "
          "act,\nrecorded by whoever owns its state machine.")


if __name__ == "__main__":
    main()
