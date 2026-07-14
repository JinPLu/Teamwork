"""Command-line entry point for deterministic Teamwork eval validation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .cases import selected_cases, validate_ledger_lines
from .contracts import EvalError, LEDGER_SCHEMAS, PLATFORMS, SPLITS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Teamwork eval fixtures.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--split", choices=sorted(SPLITS))
    group.add_argument("--all", action="store_true", help="validate all cases")
    group.add_argument("--optimizer-ledger", type=Path, metavar="PATH", help="validate one optimizer candidate ledger")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.optimizer_ledger:
        path = args.optimizer_ledger.resolve()
        try:
            count = validate_ledger_lines(path, "optimizer-candidates.jsonl", LEDGER_SCHEMAS["optimizer-candidates.jsonl"])
        except EvalError as exc:
            print(json.dumps({"status": "fail", "error": str(exc)}, sort_keys=True), file=sys.stderr)
            print(f"FAIL: {exc}", file=sys.stderr)
            return 1
        print(json.dumps({"status": "pass", "selection": "optimizer-ledger", "rows": count}, sort_keys=True))
        print(f"OK: optimizer ledger passed ({count} rows)")
        return 0

    selection = "all" if args.all else args.split
    try:
        cases = selected_cases(selection)
    except EvalError as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    by_split = {split: 0 for split in SPLITS}
    by_platform = {platform: 0 for platform in PLATFORMS}
    for case in cases:
        by_split[case["split"]] += 1
        for platform in case["platforms"]:
            by_platform[platform] += 1
    detail = ", ".join(f"{split}={count}" for split, count in sorted(by_split.items()) if count)
    summary = {
        "status": "pass",
        "selection": selection,
        "cases": len(cases),
        "by_split": {split: count for split, count in sorted(by_split.items()) if count},
        "by_platform": {platform: count for platform, count in sorted(by_platform.items()) if count},
        "case_ids": [case["id"] for case in cases],
    }
    print(json.dumps(summary, sort_keys=True))
    print(f"OK: Teamwork eval {selection} passed ({len(cases)} cases; {detail})")
    return 0
