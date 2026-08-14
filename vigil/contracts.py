"""vigil/* solver contracts — the loop's own primitives, and their proof.

Two contracts, deliberately few. `vigil/watchable` reads a criterion node and counts
what makes it unwatchable-as-meant; the package's one rule wraps it, so a tree that
carries criteria gets the guard for free. `vigil/changed` answers the one question a
generic watch can ask of any evidence window — did the latest value differ from the
one before — over values of any type, because typing the evidence types the domain.

Each contract is a pure function of its arguments. Native ABI in quern: a native is
`fn(quern, *args)` — the first argument is the tree, which `changed` ignores (its
input is the window in `*args`) and `watchable` reads (its input is a node path).

Refusal is an answer, and the one most often left to chance: a window too short to say
whether anything changed raises rather than returning 0 — the daemon journals it as a
gap, visible, instead of a green that means nothing.

`register_vigil_natives()` installs these as first-class native implementations of the
`vigil/…` contracts, with their demonstrations registered HERE, beside the code — a
native is host code, and a proof its own package could soften is no proof. If a native
ever disagrees with the contract prose in package.py, the native is the bug.
"""

from __future__ import annotations

from typing import Any, Sequence

from quern import Demonstration, Node, get_node, register_native


def changed(_quern, window: Sequence[Any]) -> float:
    """1 if the window's last value differs from the one before it, else 0.

    Values compare by equality, whatever their type — a price, a digest, a rendered
    screen's prose. Fewer than two observations cannot answer the question and refuse.
    """
    if window is None:
        raise ValueError("window is missing (nothing supplied in the context)")
    xs = list(window)
    if len(xs) < 2:
        raise ValueError(
            f"changed needs at least 2 observations to answer, got {len(xs)}")
    return 1.0 if xs[-1] != xs[-2] else 0.0


def watchable(quern, path: str) -> float:
    """Count of defects that make the criterion at `path` unwatchable as meant.

    A criterion needs a non-empty prose `claim` (the meaning), a non-empty `expr` (its
    mechanization), and a non-empty `cadence` (an unstated cadence silently becomes
    every-tick, the most expensive schedule, chosen by omission). If `proposes` is
    present it must name a destination — an empty one is an act nobody can take.
    A count, not a flag: a rule wants `== 0`, a diagnostic wants how many.
    """
    node = get_node(quern, path)
    if node is None:
        raise ValueError(f"nothing at '{path}'")
    defects = 0
    for field in ("claim", "expr", "cadence"):
        v = node.payload.get(field)
        if not isinstance(v, str) or not v.strip():
            defects += 1
    if "proposes" in node.payload:
        p = node.payload["proposes"]
        if not isinstance(p, str) or not p.strip():
            defects += 1
    return float(defects)


VIGIL_NATIVES = {
    "vigil/changed": changed,
    "vigil/watchable": watchable,
}


# --- demonstrations: the state, the call, the answer --------------------------------
# Written as SCENARIOS where a wrong answer is still plausible — the short window that
# quietly answers 0, the criterion missing exactly one field — because those are the
# cases that turn a gate green while meaning nothing.

def _criterion(**payload: Any) -> Node:
    return Node(id="crit", kind="criterion", name="a criterion under proof",
                payload=payload)


_SOUND = dict(claim="The notice board reads differently than at last inspection",
              expr="solve('vigil/changed', ctx('notice-board')) >= 1",
              cadence="daily", feed="harbour-log")


CHANGED_SPEC = [
    Demonstration(
        contract="vigil/changed", args=[["a", "a"]], expect=0,
        because="two identical readings: nothing changed"),
    Demonstration(
        contract="vigil/changed", args=[["a", "b"]], expect=1,
        because="the latest reading differs from the one before"),
    Demonstration(
        contract="vigil/changed", args=[[1.0, 2.0, 2.0]], expect=0,
        because="only the last step matters: an old change is not a current one"),
    Demonstration(
        contract="vigil/changed", args=[[1.0, 1.0, 2.0]], expect=1,
        because="numbers answer exactly as digests do — the evidence is untyped"),
    Demonstration(
        contract="vigil/changed", args=[["only-one"]], expect_error="at least 2",
        because="one reading cannot say whether anything changed: refusing beats a "
                "0 that reads as 'no change' on day one"),
    Demonstration(
        contract="vigil/changed", args=[[]], expect_error="at least 2",
        because="an empty window is the same refusal, not a quieter one"),
]

WATCHABLE_SPEC = [
    Demonstration(
        contract="vigil/watchable", nodes=[_criterion(**_SOUND)], args=["crit"],
        expect=0,
        because="claim, expr and cadence all present: watchable as meant"),
    Demonstration(
        contract="vigil/watchable",
        nodes=[_criterion(**{k: v for k, v in _SOUND.items() if k != "claim"})],
        args=["crit"], expect=1,
        because="an expr with no claim is a mechanization of nothing"),
    Demonstration(
        contract="vigil/watchable",
        nodes=[_criterion(**{k: v for k, v in _SOUND.items() if k != "expr"})],
        args=["crit"], expect=1,
        because="a claim with no expr is an expectation, a different word — a "
                "criterion IS the compiled watch"),
    Demonstration(
        contract="vigil/watchable",
        nodes=[_criterion(**{k: v for k, v in _SOUND.items() if k != "cadence"})],
        args=["crit"], expect=1,
        because="an unstated cadence silently becomes every-tick"),
    Demonstration(
        contract="vigil/watchable", nodes=[_criterion(**_SOUND, proposes="")],
        args=["crit"], expect=1,
        because="a proposal with no destination is an act nobody can take"),
    Demonstration(
        contract="vigil/watchable", nodes=[_criterion(expr="1 == 1")],
        args=["crit"], expect=2,
        because="it counts, it does not flag: missing claim and missing cadence "
                "answer 2, so a diagnostic may read the number"),
    Demonstration(
        contract="vigil/watchable", nodes=[_criterion(**_SOUND)], args=["gone"],
        expect_error="nothing at",
        because="a guard pointed at a node that does not exist says so, instead of "
                "a 0 that reads as sound"),
]


def register_vigil_natives() -> None:
    """Idempotent: installs both contracts with their demonstrations beside them."""
    register_native("vigil/changed", changed, spec=CHANGED_SPEC)
    register_native("vigil/watchable", watchable, spec=WATCHABLE_SPEC)
