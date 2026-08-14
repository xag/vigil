"""vigil@ is what the lock says it is, and it still demonstrates itself.

Two different failures are guarded here. The digest test catches DRIFT: someone edits
`vigil/package.py` after publication, and the authored content quietly stops being the
content every consumer pins. The gate test catches ROT: the proof that held at publish
time is re-run on every CI pass, so a rule that decays into vacuity under a later
refactor is caught here, not by the first consumer whose defect it waves through.
"""

from __future__ import annotations

from pathlib import Path

from quern.library import package_digest, read_lock, validate_package

import vigil.natives  # noqa: F401 -- the gate re-runs the natives' demonstrations

from vigil.package import VIGIL_PACKAGE

_ROOT = Path(__file__).resolve().parents[1]


def test_the_pin_is_this_content():
    refs = {r.name: r for r in read_lock(_ROOT / "quern.lock")}
    assert "vigil" in refs, "vigil is not pinned in quern.lock"
    assert refs["vigil"].sha256 == package_digest(VIGIL_PACKAGE), (
        "the authored package and the pinned digest disagree — vigil/package.py has "
        "drifted from what was published. Versions are immutable: bump the version "
        "and republish; never edit a published meaning in place")


def test_the_package_still_demonstrates_itself(tmp_path):
    log = validate_package(VIGIL_PACKAGE, tmp_path)
    assert any("rule(s) exercised" in line for line in log), log
    assert any("refuted by their counter-example" in line for line in log), log


def test_every_rule_carries_a_counter_example():
    named = {r.name for r in VIGIL_PACKAGE.rules}
    refuting = {ce.rule for ce in VIGIL_PACKAGE.counter_examples}
    assert named == refuting, f"rules without a refutation: {sorted(named - refuting)}"
