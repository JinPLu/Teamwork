#!/usr/bin/env python3
"""Inspect and orchestrate Teamwork v1 -> v2 case-bundle migration.

Read-only commands never mutate managed memory.  The ``migrate`` and ``resume``
commands sequence controlled transaction phases; all managed writes, locks,
journals, recovery, and path ownership checks remain in
scripts/discussion-transaction.py.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any, NoReturn


CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
MIGRATION_ID_RE = re.compile(r"^m-[0-9a-f]{64}$")
INDEX_PATH = "docs/teamwork/index.json"


class HelperError(Exception):
    pass


_TRANSACTION_MODULE: Any | None = None


def fail(message: str) -> NoReturn:
    raise HelperError(message)


def checked_relative(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or CONTROL_RE.search(value):
        fail(f"{label} must be a normalized relative path")
    pure = PurePosixPath(value)
    if pure.is_absolute() or pure.as_posix() != value or "\\" in value or any(part in {"", ".", ".."} for part in pure.parts):
        fail(f"{label} must be a normalized relative path")
    return value


def checked_root(raw: str) -> Path:
    global _TRANSACTION_MODULE
    if _TRANSACTION_MODULE is None:
        cli = Path(__file__).with_name("discussion-transaction.py")
        spec = importlib.util.spec_from_file_location("teamwork_migration_transaction_contract", cli)
        if spec is None or spec.loader is None:
            fail("cannot load transaction root validator")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        try:
            spec.loader.exec_module(module)
        except Exception as exc:
            fail(f"cannot load transaction root validator: {exc}")
        _TRANSACTION_MODULE = module
    try:
        root = _TRANSACTION_MODULE.checked_project_root(raw)
    except Exception as exc:
        fail(str(exc))
    if not isinstance(root, Path):
        fail("transaction root validator returned an invalid root")
    return root


def safe_read(root: Path, relative: str) -> bytes:
    relative = checked_relative(relative, "path")
    path = root.joinpath(*PurePosixPath(relative).parts)
    try:
        info = path.lstat()
    except OSError as exc:
        fail(f"cannot inspect {relative}: {exc}")
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        fail(f"{relative} must be a single-link non-symlink file")
    return path.read_bytes()


def _hash(*parts: bytes) -> str:
    digest = hashlib.sha256()
    for part in parts:
        digest.update(len(part).to_bytes(8, "big"))
        digest.update(part)
    return digest.hexdigest()


def case_digest(domain: str, value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _hash(f"teamwork-case-v2:{domain}".encode("utf-8"), payload)


def load_index(root: Path) -> dict[str, Any]:
    try:
        return json.loads(safe_read(root, INDEX_PATH).decode("utf-8"))
    except Exception as exc:
        fail(f"cannot read Teamwork index: {exc}")


def classify(root: Path) -> dict[str, Any]:
    index = load_index(root)
    v1_keys = bool({"last_updated", "active", "entries"}.intersection(index))
    v2_keys = bool({"active_cases", "claim_heads", "aliases", "recent_cases", "migration"}.intersection(index))
    if v1_keys and v2_keys:
        mode = "hybrid"
    elif index.get("schema_version") == 1 and v1_keys:
        mode = "legacy-v1"
    elif index.get("schema_version") == 2 and v2_keys:
        mode = "case-v2"
    else:
        mode = "unknown"
    return {"schema_version": index.get("schema_version"), "mode": mode}


def export_baseline(root: Path) -> dict[str, Any]:
    if classify(root)["mode"] != "legacy-v1":
        fail("baseline export requires legacy-v1 Teamwork memory")
    base = root / "docs/teamwork"
    rows: list[dict[str, Any]] = []
    for path in sorted(base.rglob("*")):
        relative = path.relative_to(root).as_posix()
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode):
            fail("baseline export refuses symlinks")
        if stat.S_ISREG(info.st_mode):
            data = safe_read(root, relative)
            rows.append({
                "path": relative,
                "sha256": hashlib.sha256(data).hexdigest(),
                "mode": stat.S_IMODE(info.st_mode),
                "size": len(data),
            })
    rows = sorted(rows, key=lambda row: str(row["path"]))
    digest = case_digest("migration-baseline", rows)
    return {"schema_version": 1, "paths": rows, "baseline_digest": digest}


def verify_baseline(root: Path, baseline_path: str) -> dict[str, Any]:
    baseline_file = Path(os.path.abspath(os.path.expanduser(baseline_path)))
    baseline = json.loads(baseline_file.read_text(encoding="utf-8"))
    if not isinstance(baseline, dict) or not isinstance(baseline.get("paths"), list):
        fail("baseline file is malformed")
    mismatches: list[str] = []
    for row in baseline["paths"]:
        if not isinstance(row, dict):
            fail("baseline row is malformed")
        data = safe_read(root, checked_relative(row.get("path"), "baseline path"))
        if hashlib.sha256(data).hexdigest() != row.get("sha256"):
            mismatches.append(str(row.get("path")))
    return {"valid": not mismatches, "mismatches": mismatches}


def request_inputs(root: Path) -> dict[str, Any]:
    classification = classify(root)
    result = {"classification": classification}
    if classification["mode"] == "legacy-v1":
        result["baseline"] = export_baseline(root)
    return result


def candidate_preflight(root: Path) -> dict[str, Any]:
    return transaction_json(root, "migration-preflight")


def migration_id_from_seed(seed: object) -> str:
    if not isinstance(seed, str) or HEX64_RE.fullmatch(seed) is None:
        fail("migration seed must be 64 lowercase hex characters")
    return "m-" + _hash(b"teamwork-migration-id-v1", bytes.fromhex(seed))


def deterministic_migration_seed(root: Path) -> str:
    baseline = export_baseline(root)
    return case_digest("legacy-migration-seed", {"baseline_digest": baseline["baseline_digest"]})


def migration_request_digest(payload: dict[str, Any]) -> str:
    return case_digest("migration-request", {key: value for key, value in payload.items() if key != "request_digest"})


def migration_phase_request(operation: str, migration_id: str, baseline_digest: str, *, cutover_authority: str | None = None) -> dict[str, Any]:
    if not MIGRATION_ID_RE.fullmatch(migration_id):
        fail("migration_id is invalid")
    if operation not in {"materialize-archive", "prepare-candidate", "restore-drill", "cutover", "cleanup"}:
        fail("migration phase operation is invalid")
    payload: dict[str, Any] = {
        "schema_version": 1,
        "operation": operation,
        "migration_id": migration_id,
        "baseline_digest": baseline_digest,
        "baseline": None,
    }
    if operation == "cutover":
        payload["cutover_authority"] = cutover_authority
    payload["request_digest"] = migration_request_digest(payload)
    return payload


def transaction_json(root: Path, command: str, request: dict[str, Any] | None = None) -> dict[str, Any]:
    cli = Path(__file__).with_name("discussion-transaction.py")
    argv = [sys.executable, str(cli), command, "--project-root", str(root)]
    if request is not None:
        argv.extend(["--request-json", json.dumps(request, ensure_ascii=False, sort_keys=True)])
    result = subprocess.run(argv, text=True, capture_output=True, check=False)
    stream = result.stdout if result.returncode == 0 else result.stderr
    try:
        payload = json.loads(stream)
    except json.JSONDecodeError as exc:
        fail(f"transaction {command} did not return JSON: {exc}: {stream}")
    if result.returncode != 0:
        fail(str(payload.get("message", payload)))
    if not isinstance(payload, dict):
        fail(f"transaction {command} returned a non-object payload")
    return payload


def request_for_seed(root: Path, operation: str, seed: str) -> dict[str, Any]:
    return transaction_json(root, "migration-request", {"schema_version": 1, "operation": operation, "migration_seed": seed})


def read_journal(root: Path, migration_id: str) -> dict[str, Any]:
    raw = safe_read(root, f".teamwork/runtime/migrations/{migration_id}/journal.json")
    try:
        value = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        fail(f"cannot read migration journal: {exc}")
    if not isinstance(value, dict) or value.get("migration_id") != migration_id:
        fail("migration journal identity mismatch")
    return value


def terminal_resume_state(root: Path, migration_id: str, baseline_digest: str, phase: object, steps: list[dict[str, Any]]) -> dict[str, Any]:
    classification = classify(root)
    if phase not in {"committed", "cleanup_complete"}:
        return {"mode": classification["mode"], "migration_id": migration_id, "phase": phase, "steps": steps}
    if classification["mode"] != "case-v2":
        fail("terminal migration readback did not produce case-v2 memory")
    preflight = candidate_preflight(root)
    if preflight.get("mode") != "case-v2" or preflight.get("ok") is not True:
        fail("case-v2 migration readback failed")
    index = load_index(root)
    migration = index.get("migration")
    if not isinstance(migration, dict):
        fail("case-v2 migration readback is missing migration state")
    if migration.get("migration_id") != migration_id or migration.get("baseline_digest") != baseline_digest:
        fail("case-v2 migration readback does not match runtime journal")
    return {"mode": "case-v2", "migration_id": migration_id, "phase": migration.get("phase"), "steps": steps}


def resume_migration(root: Path, migration_id: str, *, cutover: bool = False, cleanup: bool = False) -> dict[str, Any]:
    journal_path = root / ".teamwork/runtime/migrations" / migration_id / "journal.json"
    if not journal_path.is_file() and classify(root)["mode"] == "case-v2":
        candidate_preflight(root)
        index = load_index(root)
        migration = index.get("migration")
        if migration is None or (isinstance(migration, dict) and migration.get("phase") == "cleanup_complete"):
            return {"mode": "case-v2", "migration_id": migration_id, "phase": "already-case-v2", "steps": []}
        fail("case-v2 migration state names a missing runtime journal")
    journal = read_journal(root, migration_id)
    baseline_digest = str(journal.get("baseline_digest"))
    if HEX64_RE.fullmatch(baseline_digest) is None:
        fail("migration journal baseline_digest is invalid")
    index_migration: dict[str, Any] | None = None
    if classify(root)["mode"] == "case-v2":
        index = load_index(root)
        raw_migration = index.get("migration")
        if isinstance(raw_migration, dict):
            index_migration = raw_migration
            if index_migration.get("migration_id") != migration_id or index_migration.get("baseline_digest") != baseline_digest:
                fail("case-v2 migration index and runtime journal do not match")
    steps: list[dict[str, Any]] = []
    while True:
        phase = journal.get("phase")
        restore_drill = journal.get("restore_drill")
        next_operation: str | None = None
        if phase == "baseline_approved":
            next_operation = "materialize-archive"
        elif phase == "archive_durable":
            next_operation = "prepare-candidate"
        elif phase == "candidate_validated" and restore_drill != "passed":
            next_operation = "restore-drill"
        elif phase == "candidate_validated" and cutover:
            next_operation = "cutover"
        elif phase == "committed" and cleanup:
            next_operation = "cleanup"
        else:
            return terminal_resume_state(root, migration_id, baseline_digest, phase, steps)
        request = migration_phase_request(
            next_operation,
            migration_id,
            baseline_digest,
            cutover_authority="I authorize Teamwork memory cutover" if next_operation == "cutover" else None,
        )
        applied = transaction_json(root, "migration-apply", request)
        steps.append({"operation": next_operation, "result": applied})
        if next_operation == "cutover":
            if cleanup:
                journal = read_journal(root, migration_id)
                continue
            return {"mode": "case-v2", "migration_id": migration_id, "phase": applied.get("phase"), "steps": steps}
        journal = read_journal(root, migration_id)


def migrate(root: Path, *, cutover: bool = False, cleanup: bool = False) -> dict[str, Any]:
    classification = classify(root)
    if classification["mode"] == "case-v2":
        candidate_preflight(root)
        index = load_index(root)
        migration = index.get("migration")
        if migration is None:
            return {"mode": "case-v2", "phase": "already-case-v2", "steps": []}
        if isinstance(migration, dict) and migration.get("phase") == "cleanup_complete":
            return {"mode": "case-v2", "phase": "already-case-v2", "steps": []}
        if isinstance(migration, dict):
            migration_id = migration.get("migration_id")
            if not isinstance(migration_id, str) or MIGRATION_ID_RE.fullmatch(migration_id) is None:
                fail("case-v2 migration state has invalid migration_id")
            if migration.get("phase") == "committed" and not cleanup:
                return {"mode": "case-v2", "migration_id": migration_id, "phase": "committed", "steps": []}
            return resume_migration(root, migration_id, cutover=cutover, cleanup=cleanup)
        fail("case-v2 migration state is malformed")
    if classification["mode"] != "legacy-v1":
        fail("migration requires an exact legacy-v1 or case-v2 Teamwork root")
    preflight = candidate_preflight(root)
    if not preflight.get("ok"):
        fail("migration preflight did not pass")
    baseline_digest = preflight.get("baseline_digest")
    if not isinstance(baseline_digest, str) or HEX64_RE.fullmatch(baseline_digest) is None:
        fail("migration preflight returned an invalid baseline_digest")
    seed = case_digest("legacy-migration-seed", {"baseline_digest": baseline_digest})
    migration_id = migration_id_from_seed(seed)
    if (root / ".teamwork/runtime/migrations" / migration_id / "journal.json").is_file():
        return resume_migration(root, migration_id, cutover=cutover, cleanup=cleanup)
    approved_request = request_for_seed(root, "approve-baseline", seed)
    approved = transaction_json(root, "migration-apply", approved_request)
    migration_id = str(approved["migration_id"])
    resumed = resume_migration(root, migration_id, cutover=cutover, cleanup=cleanup)
    return {
        "mode": resumed.get("mode", "legacy-v1"),
        "migration_id": migration_id,
        "phase": resumed.get("phase"),
        "steps": [{"operation": "approve-baseline", "result": approved}, *resumed.get("steps", [])],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["classify", "export", "verify", "probe", "request-inputs", "candidate-preflight", "migrate", "resume"])
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--baseline")
    parser.add_argument("--migration-id")
    parser.add_argument("--cutover", action="store_true")
    parser.add_argument("--cleanup", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        root = checked_root(args.project_root)
        if args.command == "classify":
            payload = classify(root)
        elif args.command == "export":
            payload = export_baseline(root)
        elif args.command == "verify":
            if args.baseline is None:
                fail("--baseline is required for verify")
            payload = verify_baseline(root, args.baseline)
        elif args.command == "probe":
            payload = {"read_only": True, **classify(root)}
        elif args.command == "candidate-preflight":
            payload = candidate_preflight(root)
        elif args.command == "migrate":
            payload = migrate(root, cutover=args.cutover, cleanup=args.cleanup)
        elif args.command == "resume":
            if args.migration_id is None:
                fail("--migration-id is required for resume")
            payload = resume_migration(root, args.migration_id, cutover=args.cutover, cleanup=args.cleanup)
        else:
            payload = request_inputs(root)
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 0
    except HelperError as exc:
        print(json.dumps({"ok": False, "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
