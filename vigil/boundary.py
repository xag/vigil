"""This repo's own nondeterminism boundary.

A program's execution is fully determined by its code plus its nondeterministic
inputs. vigil has very few of its own: the journal file it appends to and reads back.
Everything else is injected by design — the tick takes `now` as an argument, the
scheduler's clock and sleep are constructor fields, and a Feed is the CONSUMER's door
to the world (whatever IO a feed does — prices, tapes, rendered surfaces — lives with
whoever implements it and belongs on *their* boundary). A boundary declared while it
is one module stays true; a boundary retrofitted after the IO has spread is an
archaeology exercise.

Nothing here is recorded by default: this declaration is the artifact, and an app (or
a test) that wants a tape of the loop's execution calls
`flight_recorder.install(boundary(), ...)` with it. The library records and judges
nothing on its own.
"""

from __future__ import annotations

from flight_recorder import Boundary

from vigil import storage


def boundary() -> Boundary:
    """The declaration. A function, not a module constant, because building it imports
    the module it names — and `import vigil` must stay free of everything."""
    return Boundary(
        effects=[
            # The journal file. Every byte the loop persists or reloads crosses
            # these seams (journal.py routes through storage on purpose).
            (storage, ["exists", "read_text", "write_text", "append_line"]),
        ],
    )
