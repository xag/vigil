"""The boundary declaration builds, and it names the journal's storage seams."""

from __future__ import annotations

from vigil.boundary import boundary


def test_the_boundary_builds_and_names_the_storage_seams():
    b = boundary()
    [(module, names, *_)] = b.effects
    assert module.__name__ == "vigil.storage"
    assert set(names) == {"exists", "read_text", "write_text", "append_line"}
