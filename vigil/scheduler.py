"""The scheduler: turns the pure daemon tick into a long-running watcher.

Deliberately thin — all the intelligence is in `daemon.tick`; this loop only decides
*when* to call it and *whom* to tell. Clock and sleep are injected so the loop is
testable to the second (and so a recording consumer can feed a recorded clock), and a
notifier is any callable-shaped object: the default prints, a real deployment plugs in
push/mail without this module changing.

The loop never lets one bad tick kill the watch: an unexpected error is journaled as a
`gap` (visible, never silent) and the next tick proceeds.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable, Iterable, Protocol

from quern import Quern

from .daemon import TickReport, tick
from .feeds import Feed
from .journal import Journal


class Notifier(Protocol):
    def notify(self, report: TickReport) -> None: ...


class StdoutNotifier:
    """The development notifier: firings and gaps, one line each."""

    def notify(self, report: TickReport) -> None:
        for f in report.firings:
            print(f"[{report.at.isoformat()}] {f.role.upper()} FIRED "
                  f"{f.subject} :: {f.claim}")
        for g in report.gaps:
            print(f"[{report.at.isoformat()}] GAP {g}")


@dataclass
class Scheduler:
    tree: Quern
    journal: Journal
    feed: Feed
    notifier: Notifier
    subjects: Iterable[str] = field(default_factory=list)
    period: timedelta = timedelta(minutes=15)
    clock: Callable[[], datetime] = datetime.now
    sleep: Callable[[float], None] = time.sleep

    def run_once(self) -> TickReport:
        now = self.clock()
        try:
            report = tick(self.tree, self.journal, self.feed, now,
                          list(self.subjects))
        except Exception as e:  # a broken tick must not end the watch
            self.journal.append("gap", now, error=f"tick failed: {e}")
            report = TickReport(at=now, gaps=[f"tick failed: {e}"])
        if report.firings or report.gaps:
            self.notifier.notify(report)
        return report

    def run(self, ticks: int | None = None) -> list[TickReport]:
        """Tick forever (or `ticks` times), sleeping `period` in between."""
        reports = []
        while ticks is None or len(reports) < ticks:
            reports.append(self.run_once())
            if ticks is None or len(reports) < ticks:
                self.sleep(self.period.total_seconds())
        return reports
