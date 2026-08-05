#!/usr/bin/env python3
"""Verify exact, evidence-bound per-host/per-profile Teamwork trajectories."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from teamwork_tooling.evaluation.host_matrix import (  # noqa: E402
    RELEASE_TEMP_ROOT,
    HOSTS,
    PROFILES,
    HostMatrixError,
    load_case_manifest,
    load_trajectory_schema,
    validate_record_binding,
)
from teamwork_tooling.evaluation.contracts import CANONICAL_ROLES  # noqa: E402


def read_records(
    path: Path, *, host: str, profile: str, cases: dict[str, dict[str, object]], schema: dict[str, object],
) -> list[dict[str, object]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise HostMatrixError(f"cannot read slice output {path}: {exc}") from exc
    records: list[dict[str, object]] = []
    for number, line in enumerate(lines, start=1):
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise HostMatrixError(f"{path}:{number}: invalid JSON: {exc}") from exc
        if not isinstance(record, dict):
            raise HostMatrixError(f"{path}:{number}: record must be an object")
        if record.get("host") != host or record.get("profile") != profile:
            raise HostMatrixError(
                f"{path}:{number}: record host/profile does not match containing output slice {host}/{profile}"
            )
        case_id = record.get("case_id")
        case = cases.get(case_id) if isinstance(case_id, str) else None
        if case is None:
            raise HostMatrixError(f"{path}:{number}: record references an unknown matrix case")
        validate_record_binding(record, case, schema, path.parent)
        records.append(record)
    return records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    verify = sub.add_parser("verify")
    verify.add_argument("--manifest", required=True, type=Path)
    verify.add_argument("--output-root", required=True, type=Path)
    verify.add_argument("--schema", required=True, type=Path)
    verify.add_argument("--hosts", required=True, nargs="+")
    verify.add_argument("--profiles", required=True, nargs="+")
    verify.add_argument("--summary", required=True, type=Path)
    return parser.parse_args()


def output_slices(
    output_root: Path, hosts: list[str], profiles: list[str],
) -> list[tuple[str, str, str, Path]]:
    return [
        (host, profile, profile, output_root / host / f"{profile}.jsonl")
        for host in hosts
        for profile in profiles
    ]


def main() -> int:
    args = parse_args()
    expected_output_root = RELEASE_TEMP_ROOT / "outputs/installed"
    expected_summary = expected_output_root / "matrix-summary.json"
    if args.output_root != expected_output_root or args.summary != expected_summary:
        raise HostMatrixError(
            "matrix output root and summary must use the exact /tmp/teamwork-release-matrix/outputs/installed paths"
        )
    if set(args.hosts) != HOSTS or len(args.hosts) != len(HOSTS):
        raise HostMatrixError("release matrix must contain codex, cursor, and claude exactly once")
    if set(args.profiles) != PROFILES or len(args.profiles) != len(PROFILES):
        raise HostMatrixError("release matrix must contain every declared profile exactly once")
    manifest_path = args.manifest.resolve()
    manifest_root = manifest_path.parents[3]
    manifest_cases = load_case_manifest(manifest_path, root=manifest_root)
    cases = {case["id"]: case for case in manifest_cases}
    schema = load_trajectory_schema(args.schema.resolve())
    output_root = args.output_root.resolve()
    failures: list[str] = []
    slices: list[dict[str, object]] = []
    total = 0
    expected_per_output = len(cases)
    for host, profile, arm, path in output_slices(output_root, args.hosts, args.profiles):
        try:
            records = read_records(path, host=host, profile=profile, cases=cases, schema=schema)
        except HostMatrixError as exc:
            failures.append(f"{host}/{arm}: {exc}")
            records = []
        total += len(records)
        case_ids = [record.get("case_id") for record in records]
        roles = {
            dispatch.get("role")
            for record in records
            for dispatch in record.get("dispatches", [])
            if isinstance(dispatch, dict) and isinstance(dispatch.get("role"), str)
        }
        statuses = {str(record.get("status")) for record in records}
        if len(records) != expected_per_output:
            failures.append(f"{host}/{arm}: expected {expected_per_output} records, got {len(records)}")
        if len(case_ids) != len(set(case_ids)) or set(case_ids) != set(cases):
            failures.append(f"{host}/{arm}: case coverage differs from the case manifest")
        missing_roles = sorted(set(CANONICAL_ROLES) - roles)
        if missing_roles:
            failures.append(f"{host}/{arm}: missing observed roles {missing_roles}")
        blockers = [record for record in records if record.get("status") != "PASS"]
        if blockers:
            failures.append(f"{host}/{arm}: contains {len(blockers)} FAIL/UNSUPPORTED blockers")
        slices.append({
            "host": host, "profile": profile, "arm": arm, "records": len(records),
            "dispatch_roles": sorted(roles), "statuses": sorted(statuses),
            "passed": not blockers and not missing_roles and len(records) == expected_per_output
            and len(case_ids) == len(set(case_ids)) and set(case_ids) == set(cases),
        })
    expected_total = len(output_slices(output_root, args.hosts, args.profiles)) * expected_per_output
    if total != expected_total:
        failures.append(f"matrix expected {expected_total} total records, got {total}")
    summary = {
        "schema_version": 1, "status": "FAIL" if failures else "PASS",
        "total_records": total, "expected_total_records": expected_total,
        "slices": slices, "failures": failures,
    }
    if args.summary.exists():
        raise HostMatrixError(f"summary already exists: {args.summary}")
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print(f"OK: verified {total} Teamwork host trajectories")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except HostMatrixError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
