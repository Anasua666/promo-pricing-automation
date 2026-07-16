"""CLI entry point: run one submission+approval cycle for a fiscal week.

Usage:
    python -m src.main --week 2026-W29 --quarter Q3
"""
from __future__ import annotations

import argparse

from src.graph.workflow import run_cycle


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one pricing submission+approval cycle")
    parser.add_argument("--week", required=True, help="Fiscal week, e.g. 2026-W29")
    parser.add_argument("--quarter", required=True, help="Quarter, e.g. Q3")
    args = parser.parse_args()

    result = run_cycle(args.week, args.quarter)

    print(f"\nCycle complete for {args.week} ({args.quarter})")
    print(f"  Flagged (needs review before submission): {len(result.get('flagged', []))}")
    print(f"  Submitted for approval: {len(result.get('submissions', []))}")
    print(f"  Approved: {len(result.get('approved', []))}")
    print(f"  Rejected: {len(result.get('rejected', []))}")
    print(f"  Pending: {len(result.get('pending', []))}")


if __name__ == "__main__":
    main()
