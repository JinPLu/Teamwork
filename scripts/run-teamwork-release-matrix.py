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
    load_json,
    load_case_manifest,
    load_trajectory_schema,
    validate_record_binding,
)


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
        case_name = record.get("case_name")
        case = cases.get(case_name) if isinstance(case_name, str) else None
        if case is None:
            raise HostMatrixError(f"{path}:{number}: record references an unknown matrix case")
        validate_record_binding(record, case, schema, path.parent)
        records.append(record)
    return records


def support_result(
    *, host: str, case: dict[str, object], record: dict[str, object]
) -> tuple[bool, str]:
    support = case["support"]
    if not isinstance(support, dict) or host not in support:
        return False, "support expectation is missing"
    expectation = support[host]
    status = record.get("status")
    if expectation == "required":
        return (
            (True, "required-pass")
            if status == "PASS"
            else (False, f"required case returned {status}")
        )
    if expectation == "conditional-exact-role":
        if status == "PASS":
            return True, "conditional-pass"
        if (
            status == "UNSUPPORTED"
            and record.get("failure_classification") == "required-agent-not-observed"
        ):
            return True, "conditional-unsupported"
        return False, (
            "conditional exact-role case must PASS or retain "
            "UNSUPPORTED/required-agent-not-observed"
        )
    return False, f"unknown support expectation {expectation!r}"


def manifest_release_hosts(path: Path) -> list[str]:
    value = load_json(path, "live case manifest")
    hosts = value.get("release_hosts")
    if (
        not isinstance(hosts, list)
        or not hosts
        or not all(isinstance(host, str) for host in hosts)
        or len(hosts) != len(set(hosts))
        or not set(hosts) <= HOSTS
    ):
        raise HostMatrixError(
            "live case manifest release_hosts must be a unique non-empty supported host list"
        )
    return list(hosts)


def validate_requested_release_hosts(requested: list[str], declared: list[str]) -> None:
    if requested != declared:
        raise HostMatrixError(
            f"release matrix hosts must exactly match manifest release_hosts: {declared}"
        )


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
    if not args.hosts or len(set(args.hosts)) != len(args.hosts) or not set(args.hosts) <= HOSTS:
        raise HostMatrixError("release matrix hosts must be a unique non-empty supported subset")
    if not args.profiles or len(set(args.profiles)) != len(args.profiles) or not set(args.profiles) <= PROFILES:
        raise HostMatrixError("release matrix profiles must be a unique non-empty supported subset")
    manifest_path = args.manifest.resolve()
    manifest_root = manifest_path.parents[3]
    release_hosts = manifest_release_hosts(manifest_path)
    validate_requested_release_hosts(args.hosts, release_hosts)
    manifest_cases = load_case_manifest(manifest_path, root=manifest_root)
    cases = {case["name"]: case for case in manifest_cases}
    schema = load_trajectory_schema(args.schema.resolve())
    output_root = args.output_root.resolve()
    failures: list[str] = []
    slices: list[dict[str, object]] = []
    total = 0
    support_counts = {
        "required-pass": 0,
        "conditional-pass": 0,
        "conditional-unsupported": 0,
    }
    expected_per_output = len(cases)
    for host, profile, arm, path in output_slices(output_root, args.hosts, args.profiles):
        try:
            records = read_records(path, host=host, profile=profile, cases=cases, schema=schema)
        except HostMatrixError as exc:
            failures.append(f"{host}/{arm}: {exc}")
            records = []
        total += len(records)
        case_names = [record.get("case_name") for record in records]
        statuses = {str(record.get("status")) for record in records}
        if len(records) != expected_per_output:
            failures.append(f"{host}/{arm}: expected {expected_per_output} records, got {len(records)}")
        if len(case_names) != len(set(case_names)) or set(case_names) != set(cases):
            failures.append(f"{host}/{arm}: case coverage differs from the case manifest")
        blockers: list[str] = []
        for record in records:
            case_name = record.get("case_name")
            case = cases.get(case_name) if isinstance(case_name, str) else None
            if case is None:
                continue
            accepted, result = support_result(host=host, case=case, record=record)
            if accepted:
                support_counts[result] += 1
            else:
                blockers.append(f"{case_name}: {result}")
        if blockers:
            failures.append(
                f"{host}/{arm}: contains {len(blockers)} support blockers: "
                + "; ".join(blockers)
            )
        slices.append({
            "host": host, "profile": profile, "arm": arm, "records": len(records),
            "statuses": sorted(statuses),
            "support_observation": (
                "conditional-unsupported"
                if "UNSUPPORTED" in statuses and not blockers
                else "all-observed-pass" if statuses == {"PASS"} and not blockers
                else "blocked"
            ),
            "contract_satisfied": not blockers and len(records) == expected_per_output
            and len(case_names) == len(set(case_names)) and set(case_names) == set(cases),
        })
    expected_total = len(output_slices(output_root, args.hosts, args.profiles)) * expected_per_output
    if total != expected_total:
        failures.append(f"matrix expected {expected_total} total records, got {total}")
    summary = {
        "schema_version": 2, "status": "FAIL" if failures else "PASS",
        "release_hosts": release_hosts,
        "total_records": total, "expected_total_records": expected_total,
        "support_counts": support_counts, "slices": slices, "failures": failures,
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
