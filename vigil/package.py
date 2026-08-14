"""vigil@0.1.0 — the watch-and-judge vocabulary for the `quern` substrate.

What this package *is* (all data, all served through the same API as the tree):

- **vocabulary** — what a criterion *means*: a fact about a watched subject that,
  if observed, demands judgment; plus the journal event kinds the loop writes, as
  conventions, so the words have one definition.
- **rules** — the structural invariant of a well-formed watch (a criterion is
  watchable as meant), wrapped around the `vigil/watchable` contract.
- **solvers** — the `vigil/*` contracts (see contracts.py), declared here as native.
  A criterion's compiled expression reaches them with solve(); its evidence arrives
  as ctx() from the daemon's feed window.
- **examples** — worked criteria that exercise the rule (the publish gate runs them).

What this package is NOT, on purpose ("meaning is data, safety is code"): the
append-only journal, the tick, the scheduler, the pending queue and the judge all live
in the vigil *library*, never as refinable content. And it names NO domain: what a
subject is (a thesis, a rendered surface, an app in production), what a firing means
for it, and who may move it are the adopting package's words. A domain package
`requires` vigil@ and specializes — its criterion kinds keep their own names and ride
on this shape.

A live criterion is NOT shipped as a package rule (the publish gate has no feed to
evaluate ctx() against). It rides on its node as data, e.g.

  kind: criterion
  payload:
    claim:   "The checkout screen reads differently than when it was last judged"
    expr:    "solve('vigil/changed', ctx('surface:checkout')) >= 1"
    cadence: "daily"
    feed:    "walker"

and the daemon lifts `expr` into a path-pinned Rule, evaluates it with the feed window
as context, and journals the result. demo.py runs exactly that path.
"""

from __future__ import annotations

from quern import KindDef, Node, Package, Rule, SolverDef
from quern.library import CounterExample

# Absolute on purpose: `quern publish vigil/package.py:VIGIL_PACKAGE` file-loads this
# module with no parent package, and a relative import would refuse to resolve.
from vigil.contracts import VIGIL_NATIVES


# --- vocabulary: what the loop's words mean ------------------------------------

VOCABULARY = [
    KindDef(
        kind="criterion",
        description="A fact about a watched subject that, if observed, demands "
        "judgment. Carries its compiled test as payload.expr (a quern rule expression "
        "over solve()/ctx), a prose payload.claim, and payload.cadence/feed. The claim "
        "is the meaning and the expr its mechanization — when they disagree, the claim "
        "wins and the expr is a bug. An optional payload.proposes names the status a "
        "firing proposes moving the subject to; the loop only ever proposes, and "
        "whoever owns the subject's state machine should refuse every non-human "
        "transition. Domain packages requiring vigil@ specialize this shape under "
        "their own kind names; the loop watches any node carrying an expr and "
        "interprets none of the domain's words.",
    ),
    # The journal kinds are conventions, not tree shapes: journal events live in the
    # append-only JSONL (journal.py), never as nodes, and the vocabulary carries them
    # so the words have one definition.
    KindDef(
        kind="observation",
        convention=True,
        description="A journal event, never a node: one look at one criterion at one "
        "instant — the evaluated answer and the window's tail (measured, source = the "
        "feed). Append-only; written on every due look, breached or not, because the "
        "record of watching is what makes silence detectable.",
    ),
    KindDef(
        kind="criterion-fired",
        convention=True,
        description="A journal event, never a node: a criterion's answer crossed from "
        "false to true. Fired once per edge — a criterion that stays breached does not "
        "re-fire every tick. What a firing means for the subject is the domain's word, "
        "not the loop's.",
    ),
    KindDef(
        kind="judgement",
        convention=True,
        description="A journal event, never a node: the qualitative answer to a "
        "firing — genuine fact, artifact of the instrument, or noise (provenance "
        "inferred, source names who judged). A judgement PROPOSES; humans move "
        "subjects. Kept even when later falsified — the calibration record is the "
        "point.",
    ),
    KindDef(
        kind="gap",
        convention=True,
        description="A journal event, never a node: a watcher that could not watch — "
        "a missing feed, a broken expr, a window too short to answer. An unwatched "
        "criterion must be visible, never silent; a gap is the loop refusing to let "
        "absence read as green.",
    ),
    KindDef(
        kind="proposal",
        convention=True,
        description="A journal event, never a node: a fired criterion's payload named "
        "a destination (proposes) and the loop wrote the proposal down. Nothing in the "
        "loop acts on it — moving a subject is a human act recorded by whoever owns "
        "its state machine.",
    ),
]


# --- rules: the structural invariant of a well-formed watch ---------------------
# Provable with no feed — the publish gate re-runs the native's demonstrations and
# then holds the examples to this.

RULES = [
    Rule(
        name="a-criterion-is-watchable",
        kind="criterion",
        description="A criterion missing its claim is a mechanization of nothing; "
        "missing its expr it is an expectation wearing the wrong word; missing its "
        "cadence it silently becomes an every-tick watch; proposing an empty "
        "destination it asks for an act nobody can take. The contract counts the "
        "defects; a sound criterion counts zero.",
        expr="solve('vigil/watchable', self) == 0",
    ),
]


# --- solvers: the vigil/* contracts, declared native ----------------------------
# Prose here is the contract; contracts.py is its native implementation, with the
# demonstrations registered beside the code. A guest WASM module honouring the same
# names could replace it.

_CONTRACT_DOC = {
    "vigil/watchable": "args: (path). -> count of defects making the criterion at "
    "path unwatchable as meant: missing/empty claim, expr or cadence, and a present-"
    "but-empty proposes. Refuses a path with no node. A rule wants == 0; a diagnostic "
    "reads the count.",
    "vigil/changed": "args: (window). -> 1 if the window's last value differs from "
    "the one before, else 0. Values of any type, compared by equality — a price, a "
    "digest, a rendered screen's prose. Refuses windows shorter than 2: one reading "
    "cannot answer 'did it change', and the refusal surfaces as a gap instead of a "
    "green that means nothing.",
}

SOLVERS = [
    SolverDef(name=name, native=True, reads=[], description=doc,
              params_doc={"window": "evidence values, most recent last"}
              if name == "vigil/changed" else
              {"path": "path of the criterion node under test"})
    for name, doc in _CONTRACT_DOC.items()
]

assert set(_CONTRACT_DOC) == set(VIGIL_NATIVES), "contract docs and natives drifted"


# --- examples: worked criteria that exercise the rule ---------------------------
# A neutral fixture domain (a harbour and its keeper), on purpose: a fixture drawn
# from a real adopter teaches the substrate that adopter's accidents.

EXAMPLES = [
    Node(
        id="the-notice-board-changed",
        kind="criterion",
        name="The harbour notice board reads differently than at last inspection",
        payload={
            "claim": "The notice board's posted text differs from what the last "
                     "inspection recorded",
            "expr": "solve('vigil/changed', ctx('notice-board')) >= 1",
            "cadence": "daily",
            "feed": "harbour-log",
        },
    ),
    Node(
        id="the-light-failed-two-nights",
        kind="criterion",
        name="The passage light showed on neither of the last two nights",
        payload={
            "claim": "Two consecutive nights with no light is a passage nobody "
                     "should trust",
            "expr": "sum(ctx('lit-last-two-nights')) == 0",
            "cadence": "daily",
            "feed": "harbour-log",
            "proposes": "unsafe",
        },
    ),
]


# --- counter-examples: the rule must be able to reject its own defect -----------
# Each staged node carries exactly one defect — well-formed otherwise, so the refusal
# proves the rule and not some neighbouring accident.

COUNTER_EXAMPLES = [
    CounterExample(
        rule="a-criterion-is-watchable",
        because="an expr with no claim is a mechanization of nothing — when expr and "
        "claim disagree the claim wins, and here there is nothing to win",
        node=Node(id="claimless", kind="criterion", name="A watch on nothing stated",
                  payload={"expr": "solve('vigil/changed', ctx('x')) >= 1",
                           "cadence": "daily", "feed": "harbour-log"}),
    ),
    CounterExample(
        rule="a-criterion-is-watchable",
        because="a claim with no expr is an expectation, a different word — a "
        "criterion IS the compiled watch, and prose cannot fire",
        node=Node(id="exprless", kind="criterion", name="A claim nothing can run",
                  payload={"claim": "The board changed since last inspection",
                           "cadence": "daily", "feed": "harbour-log"}),
    ),
    CounterExample(
        rule="a-criterion-is-watchable",
        because="an unstated cadence silently becomes 'every tick' — the most "
        "expensive schedule, chosen by omission instead of decision",
        node=Node(id="cadenceless", kind="criterion", name="A watch nobody scheduled",
                  payload={"claim": "The board changed since last inspection",
                           "expr": "solve('vigil/changed', ctx('x')) >= 1",
                           "feed": "harbour-log"}),
    ),
    CounterExample(
        rule="a-criterion-is-watchable",
        because="a firing that proposes must name its destination — an empty one is "
        "an act nobody can take, recorded as if somebody could",
        node=Node(id="proposes-nothing", kind="criterion",
                  name="A proposal with no destination",
                  payload={"claim": "Two dark nights make the passage unsafe",
                           "expr": "sum(ctx('lit')) == 0",
                           "cadence": "daily", "feed": "harbour-log",
                           "proposes": ""}),
    ),
]


VIGIL_PACKAGE = Package(
    name="vigil",
    version="0.1.0",
    description="The watch-and-judge loop's vocabulary: a criterion is a prose claim "
    "with its compiled expr, a cadence and a feed, watched deterministically, fired on "
    "the false->true edge, judged qualitatively — and every verdict PROPOSES, because "
    "humans move subjects. The package names no domain: adopters require it and "
    "specialize the criterion shape under their own kind names. Journal, tick, "
    "scheduler and judge stay in the vigil library — meaning is data, safety is code.",
    publisher="vigil",
    vocabulary=VOCABULARY,
    rules=RULES,
    solvers=SOLVERS,
    examples=EXAMPLES,
    counter_examples=COUNTER_EXAMPLES,
)


def build() -> Package:
    return VIGIL_PACKAGE
