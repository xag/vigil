"""Importing this module registers the vigil/* native contracts.

`quern publish --natives MODULE` imports a module for its `register_native` side
effects, because native contracts are host code: they travel as Python, never in the
artifact, and the proof gate must re-run their demonstrations in-process. That
convention needs a module whose IMPORT registers — `vigil` itself only exposes the
function, and a package that registered on import would fire the side effect on anyone
who merely wanted to read the vocabulary.

So: `import vigil.natives` (or `--natives vigil.natives`) to arm the contracts;
`from vigil.contracts import register_vigil_natives` to arm them explicitly. Both call
the same idempotent registration.
"""

from __future__ import annotations

from .contracts import register_vigil_natives

register_vigil_natives()
