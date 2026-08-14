"""This repo's own design ledger — the decisions that founded it, as data a rule can go red on.

Not a changelog and not a README section: a README states a caveat and then cannot
notice when the caveat is violated. Here a decision that names no rejected alternative
is red, a belief carrying no observation that would kill it is red, a debt with no
discharge condition is red — and `vigil.check` exits 1 while any is.

The vocabulary is `ledger@`, pinned from the registry like anything else; it is not
re-authored here.
"""

from __future__ import annotations

import os
from pathlib import Path

import quern.grounding  # noqa: F401 -- the grounding natives, for the ledger's own rules
from quern import Quern, Node
from quern.library import consume
from quern.provenance import Quantity

_ROOT = Path(__file__).resolve().parents[1]


def build() -> Quern:
    lib, refs = consume(_ROOT, os.environ.get("QUERN_REGISTRY", _ROOT.parent / "quern-registry"))
    quern = Quern(packages=[next(r for r in refs if r.name == "ledger")])
    quern = lib.effective(quern)
    quern.root.children = [_EXTRACTED, _PROPOSES, _WINDOWS, _NAMES,
                           _ONE_LOOP, _COPY_DEBT]
    return quern


_EXTRACTED = Node(
    id="the-loop-is-extracted-not-invented",
    kind="decision",
    name="vigil is the watch-and-judge loop lifted out of the notebook that first grew it, "
         "with the domain removed",
    payload={
        "rationale":
            "The loop existed and worked: criteria as {claim, expr, cadence, feed} "
            "payloads, a deterministic tick that fires on the false->true edge and "
            "files gaps, a pending queue, verdicts that propose. Three kinds in the "
            "notebook's own package share that anatomy and say so only in prose — a "
            "true sentence that cannot fire. Extraction turns the shared anatomy into "
            "a package a domain requires and a library a server imports; the domain "
            "keeps its own kind names by precedence and migrates nothing it authored.",
        "note":
            "Extraction is also the cheaper thing to be wrong about: digest pinning "
            "means no consumer's meaning moves until it repins, so a bad cut is a "
            "version nobody adopts, not a migration anybody suffers.",
    },
    children=[
        Node(id="alt-build-fresh", kind="alternative",
             name="Write a new loop for the next domain that needs one",
             payload={"why":
                      "Relocated duplication. Two loops drift, and the second one "
                      "re-learns edge-firing, visible gaps and propose-only the hard "
                      "way — the lessons the first loop already paid for."}),
        Node(id="alt-import-from-the-notebook", kind="alternative",
             name="Leave the loop where it grew and import it from there",
             payload={"why":
                      "The dependency points the wrong way: a library consumed by "
                      "many apps cannot live inside one of them, and the notebook's "
                      "loop carries its domain's words in field names and a "
                      "role-name special case."}),
        Node(id="alt-push-proof-further", kind="alternative",
             name="Extend the proof substrate instead — more expressible predicates, "
                  "more proof coverage",
             payload={"why":
                      "Out of scope by that substrate's own doctrine: proof displaces "
                      "execution, never judgment. The gap this repo exists for is the "
                      "judged watch — the part that cannot compile to a model."}),
    ],
)


_PROPOSES = Node(
    id="the-special-case-becomes-data",
    kind="decision",
    name="A firing's consequence is payload.proposes — the loop knows no role names",
    payload={
        "rationale":
            "The notebook special-cased one role name in the tick: its kill criterion "
            "auto-proposed invalidation. Generalized, the consequence rides on the "
            "node as data — any criterion may name the status its firing proposes — "
            "and the loop stays vocabulary-blind. The judging notifier takes its "
            "role filter as a constructor argument for the same reason.",
    },
    children=[
        Node(id="alt-role-table", kind="alternative",
             name="Keep a table of role names and their consequences in the loop",
             payload={"why":
                      "The loop would carry one domain's words, and every next "
                      "domain patches the table — the exact coupling extraction "
                      "exists to remove."}),
    ],
)


_WINDOWS = Node(
    id="evidence-is-any-window",
    kind="decision",
    name="A feed serves list[Any]: prices, digests and rendered prose are the same "
         "evidence to the loop",
    payload={
        "rationale":
            "window(key, as_of) returns whatever the feed serves, most recent last, "
            "no look-ahead. The loop never interprets a value — contracts compare by "
            "equality and refuse what they cannot answer — so the same tick that "
            "watches a revenue series watches a screen's rendered text. Typing the "
            "evidence would type the domain.",
    },
    children=[
        Node(id="alt-floats-only", kind="alternative",
             name="Keep list[float], the shape the notebook needed",
             payload={"why":
                      "Prices are floats; surfaces are prose and digests. A float "
                      "window forces every non-numeric domain to encode meaning "
                      "into numbers before the loop will look at it."}),
    ],
)


_NAMES = Node(
    id="journal-words-survive-extraction",
    kind="decision",
    name="Event kinds keep their born names; only the owner field generalizes to "
         "`subject`",
    payload={
        "rationale":
            "observation, criterion-fired, judgement, gap and proposal are the "
            "loop's own words and travel unchanged, so an adopter's tooling reads "
            "any vigil journal. The one field that named the domain (the subject of "
            "the watch) generalizes; an app migrating an existing journal converts "
            "that field at the seam it owns.",
    },
    children=[
        Node(id="alt-clean-rename", kind="alternative",
             name="Rename the event kinds to fresh generic words at extraction",
             payload={"why":
                      "Renaming buys nothing but a migration: the journal is "
                      "append-only history, and history that must be rewritten to "
                      "adopt a library is history the library destroyed."}),
    ],
)


_ONE_LOOP = Node(
    id="one-loop-watches-any-evidence",
    kind="hypothesis",
    name="The loop that watches price series watches rendered surfaces, tapes, and "
         "feeds not yet imagined, unchanged",
    payload={
        "held_because":
            "Nothing in due/evaluate/edge-fire/gap/pending is about what was "
            "watched — it is about time, answers, and who has not yet judged. The "
            "notebook proved the shape for series; the extraction removed the only "
            "series-shaped assumption (the window's value type). What remains is a "
            "claim about watching, not about evidence.",
        "consequence_if_wrong":
            "Bounded: a domain the shape cannot carry forks the loop, and the fork's "
            "diff IS the missing concept, named. The cost of being wrong is one "
            "honest fork, not a rewrite of adopters.",
    },
    children=[
        Node(
            id="a-watcher-the-shape-cannot-carry",
            kind="falsification",
            name="The first real adoption outside the notebook domain that the shape "
                 "cannot express",
            payload={
                "claim":
                    "An adoption needs a criterion the {claim, expr, cadence, feed} "
                    "payload cannot carry, or an act the five journal kinds cannot "
                    "record — not 'is awkward': cannot. That kills this.",
                "cadence": "on-adoption",
                "discharge_route":
                    "Name the missing concept, add it to vigil@ behind the unchanged "
                    "library surface if it is generic, or fork if it is one domain's — "
                    "and record here which it was.",
            },
        ),
    ],
)


_COPY_DEBT = Node(
    id="the-source-still-carries-the-copy",
    kind="debt",
    name="The notebook this loop was lifted from still ships its own copy — the "
         "duplication is extracted, not yet removed",
    params={
        # Ungrounded by construction: the count states what extraction left behind,
        # and only the notebook's own migration can ground it at 1.
        "copies": Quantity(
            value=2, unit="copy", provenance="asserted", grounded=False,
            source="the loop exists here and in the notebook it was lifted from; "
                   "nobody competent has yet verified the two still agree"),
    },
    payload={
        "note":
            "Deliberate, not forgotten: digest pinning makes migration explicit and "
            "unhurried, and a live app migrates on its own clock. Until it requires "
            "vigil@ and deletes its copy, a fix to the loop lands in one place and "
            "silently not the other.",
    },
    children=[
        Node(id="the-notebook-requires-vigil", kind="discharge",
             payload={
                 "condition":
                     "The notebook's next package version requires vigil@ and its "
                     "server imports this library where its own loop modules were. "
                     "Whoever does that work grounds the count above at 1.",
             }),
    ],
)
