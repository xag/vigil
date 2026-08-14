"""Feeds: the daemon's only door to the world — and the replay lever.

A feed materialises the evidence window a criterion evaluates against. All I/O lives
here; exprs and solvers stay pure over the window they are handed (quern's `ctx()`
discipline), so swapping a live feed for a recorded one replays history through the
*identical* evaluation path — the backtest is the same code as production.

`window(key, as_of)` returns the evidence for `key` as known at `as_of`, most recent
last. The values are whatever the feed serves — floats, digests, rendered prose — this
library never types the evidence, because typing the evidence types the domain.
Honouring `as_of` is what makes replay honest: a feed must never leak values from after
the asked-for instant (no look-ahead).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol


class FeedError(KeyError):
    """The feed cannot serve this key — the daemon files a gap, never guesses."""


class Feed(Protocol):
    def window(self, key: str, as_of: datetime) -> list[Any]: ...


class StaticFeed:
    """An in-memory feed: {key: [(timestamp, value), ...]}. The test and replay
    workhorse — point it at recorded history and the daemon backtests itself."""

    def __init__(self, series: dict[str, list[tuple[datetime, Any]]]) -> None:
        self._series = {k: sorted(v, key=lambda tv: tv[0]) for k, v in series.items()}

    def window(self, key: str, as_of: datetime) -> list[Any]:
        if key not in self._series:
            raise FeedError(f"no series '{key}' in this feed")
        pts = [v for (t, v) in self._series[key] if t <= as_of]
        if not pts:
            raise FeedError(f"'{key}' has no points at or before {as_of.isoformat()}")
        return pts


class MergedFeed:
    """Several feeds behind one door; first feed that serves a key wins."""

    def __init__(self, *feeds: Feed) -> None:
        self._feeds = feeds

    def window(self, key: str, as_of: datetime) -> list[Any]:
        for f in self._feeds:
            try:
                return f.window(key, as_of)
            except FeedError:
                continue
        raise FeedError(f"no feed serves '{key}'")
