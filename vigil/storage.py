"""File-content seams: every byte vigil reads from or writes to disk crosses one of
these functions. They exist so the flight recorder can treat file contents as what they
are — nondeterministic inputs — by declaring this module an effect boundary (see
boundary.py). Keep all journal file I/O routed through here."""

from __future__ import annotations

from pathlib import Path


def exists(path: Path | str) -> bool:
    return Path(path).exists()


def read_text(path: Path | str) -> str:
    return Path(path).read_text(encoding="utf-8")


def write_text(path: Path | str, text: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def append_line(path: Path | str, line: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8", newline="\n") as f:
        f.write(line + "\n")
