"""The append-only journal: the watch's storage model, not a feature of it.

Lab-record discipline — every observation, firing, judgement, gap and status change is
an event appended to a JSONL file, never rewritten. A subject's current state is a
*projection* of its journal, which makes the immutability principle structural rather
than disciplinary.

Event shape (one JSON object per line):
    {"seq": int, "at": "<iso8601>", "kind": str, "subject": str, "node": str,
     "body": {...}}
`seq` is dense and monotonic — the file refuses to load if the chain is broken, so
truncation or hand-editing is detected instead of silently absorbed.

`subject` is the path of whatever the criterion watches over — a thesis, a surface, an
app; this library never interprets it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from . import storage


class JournalError(ValueError):
    """A broken chain, a bad event, or an attempt to rewrite history."""


@dataclass
class Event:
    seq: int
    at: str            # ISO-8601, supplied by the caller (the daemon owns the clock)
    kind: str          # observation | criterion-fired | judgement | gap | proposal |
    #                    status-changed | note ...
    subject: str = ""  # path of the watched subject this event belongs to ("" = global)
    node: str = ""     # the specific criterion node, if any
    body: dict[str, Any] = field(default_factory=dict)

    def dump(self) -> str:
        return json.dumps({"seq": self.seq, "at": self.at, "kind": self.kind,
                           "subject": self.subject, "node": self.node,
                           "body": self.body}, ensure_ascii=False)


class Journal:
    """Append-only event log over one JSONL file.

    There is deliberately no update or delete: the only mutation is `append`, and it
    assigns the next `seq` itself so callers cannot leave holes or overwrite.

    Two subclass seams, because an append-only file outlives field names and a library
    that cannot read a predecessor's files forces history rewrites: `event_class` is
    the Event type constructed everywhere (a domain may extend it with its own
    accessors), and `_decode` turns one stored dict into an Event (a domain whose old
    journals named the owner field differently maps it here — the file is never
    rewritten, and new events write the current shape).
    """

    event_class: type[Event] = Event

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self._events: list[Event] = []
        if storage.exists(self.path):
            self._events = list(self._load())

    def _decode(self, d: dict) -> Event:
        """One stored dict -> one Event. The legacy-field seam."""
        return self.event_class(
            seq=int(d["seq"]), at=str(d["at"]), kind=str(d["kind"]),
            subject=str(d.get("subject", "")), node=str(d.get("node", "")),
            body=dict(d.get("body", {})))

    def _load(self) -> Iterator[Event]:
        want = 1
        for i, line in enumerate(storage.read_text(self.path).splitlines(), 1):
            if not line.strip():
                continue
            try:
                ev = self._decode(json.loads(line))
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as e:
                raise JournalError(f"line {i} is not a valid event: {e}") from e
            if ev.seq != want:
                raise JournalError(
                    f"line {i}: seq {ev.seq}, expected {want} — the chain is broken "
                    "(the journal is append-only; a hole means history was edited)")
            want += 1
            yield ev

    # -- the one write path ------------------------------------------------------

    def append(self, kind: str, at: datetime | str, subject: str = "",
               node: str = "", **body: Any) -> Event:
        ts = at.isoformat() if isinstance(at, datetime) else str(at)
        ev = self.event_class(seq=len(self._events) + 1, at=ts, kind=kind,
                              subject=subject, node=node, body=body)
        storage.append_line(self.path, ev.dump())
        self._events.append(ev)
        return ev

    # -- projections --------------------------------------------------------------

    def __len__(self) -> int:
        return len(self._events)

    def events(self, kind: str | None = None, subject: str | None = None,
               node: str | None = None) -> list[Event]:
        return [e for e in self._events
                if (kind is None or e.kind == kind)
                and (subject is None or e.subject == subject)
                and (node is None or e.node == node)]

    def last(self, kind: str | None = None, subject: str | None = None,
             node: str | None = None) -> Event | None:
        matches = self.events(kind, subject, node)
        return matches[-1] if matches else None

    def status_of(self, subject: str, default: str = "watched") -> str:
        """A subject's current status IS the projection of its status-changed events —
        there is no second copy to drift."""
        ev = self.last("status-changed", subject=subject)
        return str(ev.body["to"]) if ev else default
