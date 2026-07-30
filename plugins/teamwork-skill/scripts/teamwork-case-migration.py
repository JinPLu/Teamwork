#!/usr/bin/env python3
"""Read-only helpers for Teamwork v1 -> v2 case-bundle migration.

This script deliberately performs no managed writes.  Mutating migration phases
belong to scripts/discussion-transaction.py so they share the same lock,
journal, recovery, and path ownership checks as the rest of Teamwork memory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
from pathlib import Path, PurePosixPath
from typing import Any, NoReturn


CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
MIGRATION_ID_RE = re.compile(r"^m-[0-9a-f]{64}$")
INDEX_PATH = "docs/teamwork/index.json"


class HelperError(Exception):
    pass


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
    root = Path(os.path.realpath(os.path.abspath(os.path.expanduser(raw))))
    if not root.is_dir():
        fail("project root must exist")
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["classify", "export", "verify", "probe", "request-inputs"])
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--baseline")
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
        else:
            payload = request_inputs(root)
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 0
    except HelperError as exc:
        print(json.dumps({"ok": False, "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
