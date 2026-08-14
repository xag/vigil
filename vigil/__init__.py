"""vigil — the watch-and-judge loop, extracted as a substrate.

A criterion is data on a quern node: a prose `claim`, its compiled `expr`, a `cadence`,
and the `feed` its evidence comes from. A deterministic daemon watches every criterion
at its cadence, journals an observation on every look, fires on the false -> true edge,
and files a gap — visibly, never silently — when it cannot watch. A firing is then
JUDGED: someone answers the one question the rule cannot (is this the fact the claim
feared, an artifact of the instrument, or noise that happens to satisfy the predicate?),
and the verdict PROPOSES. Nothing in this library ever moves a subject's state.

Modules: `journal` (append-only record), `feeds` (the evidence door), `daemon` (the pure
tick), `scheduler` (the long-running watcher), `judge` (pending queue, verdicts, and the
opt-in unattended judge), `contracts`/`natives` (the vigil/* solver contracts),
`package` (the vigil@ vocabulary), `boundary` (the declared nondeterminism seam),
`demo` (a surface critic in miniature: `python -m vigil.demo`).

`import vigil` stays free of quern and flight-recorder imports on purpose — import the
module you need.
"""

__version__ = "0.1.1"
