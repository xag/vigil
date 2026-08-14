"""Every demonstration holds: the state, the call, the answer — including refusals."""

from __future__ import annotations

import pytest

from quern import Quern, solve_contract

import vigil.natives  # noqa: F401 -- arms the vigil/* contracts

from vigil.contracts import CHANGED_SPEC, WATCHABLE_SPEC


def _stage(dem) -> Quern:
    tree = Quern()
    tree.root.children = list(dem.nodes)
    return tree


@pytest.mark.parametrize("dem", CHANGED_SPEC + WATCHABLE_SPEC,
                         ids=lambda d: f"{d.contract}:{d.because[:40]}")
def test_demonstration_holds(dem):
    tree = _stage(dem)
    if getattr(dem, "expect_error", None):
        with pytest.raises(Exception, match=dem.expect_error):
            solve_contract(tree, dem.contract, list(dem.args))
    else:
        assert solve_contract(tree, dem.contract, list(dem.args)) == dem.expect, \
            dem.because
