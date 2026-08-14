# vigil

The watch-and-judge loop, as a substrate: criteria as data, deterministic watching at a cadence, firings queued for judgment, and verdicts that **propose** — never act.

A **criterion** is a node in a [quern](https://github.com/xag/quern) tree carrying four things as payload: a prose `claim` (the meaning), its compiled `expr` (a quern rule expression over `solve()`/`ctx()` — the mechanization; when they disagree, the claim wins and the expr is a bug), a `cadence`, and the `feed` its evidence comes from. A deterministic daemon watches every criterion at its cadence, journals an **observation** on every look, fires a **criterion-fired** only on the false → true edge, and files a **gap** — visibly, never silently — when it cannot watch: a missing feed, a broken expr, a window too short to answer. A firing is then **judged**: someone answers the one question the rule cannot — is this the fact the claim feared, an artifact of the instrument, or noise that happens to satisfy the predicate? — and the **judgement** proposes. Humans move subjects; nothing in this library ever does.

The loop names no domain. What a subject is — a falsifiable thesis, a rendered screen, an app in production — and what a firing means for it are the adopter's words: a domain package `requires vigil@` and specializes the criterion shape under its own kind names, and the daemon watches any node carrying an `expr` without interpreting one word of the domain's vocabulary. Evidence is equally untyped: `window(key, as_of)` returns whatever the feed serves — floats, digests, rendered prose — because typing the evidence types the domain. Swapping a live feed for a recorded one replays history through the identical evaluation path, so the backtest is the same code as production.

## What lives here

- **`vigil/package.py` → `vigil@`** — the vocabulary as data: the `criterion` kind, the five journal event kinds as conventions (observation, criterion-fired, judgement, gap, proposal), one rule (`a-criterion-is-watchable`, wrapped around the `vigil/watchable` contract) with the counter-examples that prove it fires, and the `vigil/*` solver contracts. Published to the registry, pinned by digest.
- **`vigil/journal.py`** — the append-only record: one JSONL file, dense monotonic `seq`, refuses to load a broken chain. A subject's status is a projection of its journal; there is no second copy to drift.
- **`vigil/feeds.py`** — the daemon's only door to the world, and the replay lever. `StaticFeed` is the test and backtest workhorse; `as_of` is honoured so a feed can never leak the future.
- **`vigil/daemon.py`** — the pure tick: due → materialise windows → lift the expr into a path-pinned rule → evaluate → journal. A fired criterion whose payload names `proposes` gets a proposal journaled; the daemon never moves anything.
- **`vigil/scheduler.py`** — the thin loop that turns ticks into a long-running watcher. Clock and sleep are injected; one bad tick journals a gap and the watch continues.
- **`vigil/judge.py`** — the pending queue (`pending_judgements`), the verdict (`file_verdict`; provenance `inferred`, source recorded), and the opt-in unattended API judge for deployments where verdicts must land with nobody around. The primary path is the AI client the human arrives with: zero marginal cost, and the human is needed to act on the verdict anyway.
- **`vigil/contracts.py`** — the native implementations of `vigil/watchable` and `vigil/changed`, with their demonstrations registered beside the code. Refusal is an answer: a window too short to say whether anything changed raises, and the daemon journals the gap.
- **`vigil/boundary.py`** — the declared nondeterminism seam ([flight-recorder](https://github.com/xag/flight-recorder)): the journal file. Clocks are arguments and feeds are the consumer's boundary, on purpose.
- **`vigil/tree.py`** — this repo's own design ledger (`python -m vigil.check`): the extraction decisions with their rejected alternatives, the standing hypothesis (*one loop watches any evidence* — killable, on-adoption), and the extraction debt with its discharge condition.
- **`vigil/demo.py`** — a surface critic in miniature (`python -m vigil.demo`): a walker's rendered-prose readings as a feed, a criterion that fires when the screen changes, a judgment that proposes a review. Deterministic end to end.

## The loop, in one demo

```
$ uv run python -m vigil.demo
day 1 - one reading cannot answer "did it change" - a visible gap, never a silent green
day 2 - watched, quiet
day 3 - FIRED: the checkout screen reads differently than when it was last judged
verdict: genuine (confidence 0.9) - proposes 'review'
The verdict proposes; nothing moved.
```

## License

Apache-2.0 — see [LICENSE](LICENSE).

© 2026 Xavier Grehant
