#!/usr/bin/env python3
"""Reachability check for every configured provider key.

Loads the key files (same order as Isaac at startup), then probes each
provider's API once. Keys are never printed - only status, HTTP code and a
masked hint.

Usage:
    python3 scripts/check_key_health.py
    python3 scripts/check_key_health.py --json
    python3 scripts/check_key_health.py --no-bootstrap --timeout 5
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from key_health import format_table, run_key_health, write_report  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print the machine-readable report")
    parser.add_argument(
        "--no-bootstrap",
        action="store_true",
        help="do not load key files first (use the process environment only)",
    )
    parser.add_argument("--timeout", type=float, default=None, help="per-probe timeout in seconds")
    args = parser.parse_args()

    if not args.no_bootstrap:
        try:
            from secrets_bootstrap import bootstrap_secrets

            stats = bootstrap_secrets()
            files = (stats.get("from_files") or {}).get("sources") or []
            print(f"Key-Dateien gelesen: {', '.join(files) if files else 'keine'}", file=sys.stderr)
        except Exception as exc:  # bootstrap must never block the check
            print(f"Bootstrap uebersprungen: {type(exc).__name__}", file=sys.stderr)

    report = run_key_health(timeout=args.timeout)
    write_report(report)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(format_table(report))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
