"""Run the ledger's own rules. `uv run python -m vigil.check`

Exit 1 while any rule is red, so this is a CI gate. A decision that names no rejected
alternative, a belief with nothing that could kill it, a debt with no discharge
condition: each is red here, and none of them can be made green by editing this file.
Green comes from doing the work the red node names.
"""

from __future__ import annotations

import sys

from quern import get_node, run_rules

from .tree import build


def main() -> int:
    tree = build()
    results = run_rules(tree)
    red = [r for r in results if not r.ok]

    # ASCII only: this prints to a Windows console under cp1252, which mangles anything
    # prettier and turns a clear report into mojibake exactly when it matters.
    for r in sorted(results, key=lambda r: (r.ok, r.rule, r.node)):
        mark = "ok  " if r.ok else "RED "
        at = f" @ {r.node}" if r.node else ""
        detail = f" - {r.detail}" if r.detail else ""
        print(f"{mark}{r.rule}{at}{detail}")

    print()
    if not red:
        print(f"{len(results)} rule(s), all green.")
        return 0
    print(f"{len(red)} of {len(results)} rule(s) RED.")
    print()
    for r in red:
        node = get_node(tree, r.node) if r.node else None
        why = (node.payload.get("note") if node else None) or r.detail or ""
        print(f"  {r.node or r.rule}: {why}")
    print()
    print("Discharge a red node by doing the work it names - never by editing the ledger.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
