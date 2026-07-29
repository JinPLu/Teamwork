#!/usr/bin/env python3
"""Capture and compare dirty-tree candidate path ownership."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
FORBIDDEN_PREFIX = ".claude/"


class PreflightError(Exception):
    pass


def canonical_json_bytes(data: object) -> bytes:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def write_canonical_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(canonical_json_bytes(data))
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass
        raise


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PreflightError(f"invalid JSON {path}: {exc}") from exc


def run_git(project_root: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=project_root)


def normalize_project_path(path: str) -> str:
    if "\0" in path or path.startswith("/") or "\\" in path:
        raise PreflightError(f"unsafe repository path: {path!r}")
    parts = path.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise PreflightError(f"unsafe repository path: {path!r}")
    return "/".join(parts)


def normalize_status_path(path: str) -> tuple[str, bool]:
    directory_record = path.endswith("/")
    if not directory_record:
        return normalize_project_path(path), False
    if not path.startswith(FORBIDDEN_PREFIX):
        raise PreflightError(f"unsafe repository path: {path!r}")
    normalized = normalize_project_path(path.rstrip("/"))
    if not path_is_forbidden(normalized, [FORBIDDEN_PREFIX]):
        raise PreflightError(f"unsafe repository path: {path!r}")
    return normalized, True


def parse_porcelain_z(raw: bytes) -> list[dict[str, Any]]:
    fields = raw.split(b"\0")
    records: list[dict[str, Any]] = []
    index = 0
    while index < len(fields):
        field = fields[index]
        index += 1
        if not field:
            continue
        text = field.decode("utf-8", "surrogateescape")
        if len(text) < 4:
            raise PreflightError(f"malformed porcelain record: {text!r}")
        status = text[:2]
        path, directory_record = normalize_status_path(text[3:])
        record: dict[str, Any] = {
            "status": status,
            "path": path,
            "orig_path": None,
            "directory_record": directory_record,
        }
        if status[0] in {"R", "C"} or status[1] in {"R", "C"}:
            if index >= len(fields) or not fields[index]:
                raise PreflightError(f"missing rename source for {path}")
            orig_path, orig_directory_record = normalize_status_path(fields[index].decode("utf-8", "surrogateescape"))
            record["orig_path"] = orig_path
            record["orig_directory_record"] = orig_directory_record
            index += 1
        records.append(record)
    records.sort(key=lambda item: ((item["path"] or "").encode("utf-8"), (item["orig_path"] or "").encode("utf-8")))
    return records


def status_records(project_root: Path) -> list[dict[str, Any]]:
    raw = run_git(project_root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    return parse_porcelain_z(raw)


def path_is_forbidden(path: str, forbidden_prefixes: list[str]) -> bool:
    return any(path == prefix.rstrip("/") or path.startswith(prefix) for prefix in forbidden_prefixes)


def load_ownership(path: Path) -> dict[str, Any]:
    data = load_json(path)
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise PreflightError("ownership fixture must be a schema_version 1 object")
    if data.get("default_owner") != "FORBIDDEN":
        raise PreflightError("ownership fixture default_owner must be FORBIDDEN")
    forbidden = data.get("forbidden_prefixes")
    owners = data.get("owners")
    if not isinstance(forbidden, list) or not all(isinstance(item, str) and item.endswith("/") for item in forbidden):
        raise PreflightError("ownership forbidden_prefixes must be slash-terminated strings")
    if not isinstance(owners, list):
        raise PreflightError("ownership owners must be a list")
    return data


def classify_path(path: str, ownership: dict[str, Any]) -> list[str]:
    normalize_project_path(path)
    if path_is_forbidden(path, ownership["forbidden_prefixes"]):
        return ["FORBIDDEN"]
    matches: list[str] = []
    for entry in ownership["owners"]:
        if not isinstance(entry, dict) or not isinstance(entry.get("owner"), str):
            raise PreflightError("ownership entry is malformed")
        owner = entry["owner"]
        exact_paths = entry.get("paths", [])
        prefixes = entry.get("prefixes", [])
        exclude = set(entry.get("exclude", []))
        exclude_prefixes = entry.get("exclude_prefixes", [])
        if path in exclude or any(path.startswith(prefix) for prefix in exclude_prefixes):
            continue
        if path in exact_paths or any(path.startswith(prefix) for prefix in prefixes):
            matches.append(owner)
    return matches


def require_exact_owner(path: str, ownership: dict[str, Any]) -> str:
    matches = classify_path(path, ownership)
    if matches == ["FORBIDDEN"]:
        return "FORBIDDEN"
    if not matches:
        raise PreflightError(f"unowned path: {path}")
    if len(matches) > 1:
        raise PreflightError(f"overlapping ownership for {path}: {matches}")
    return matches[0]


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_fingerprint(root: Path) -> list[dict[str, Any]]:
    if not root.exists():
        return []
    entries: list[dict[str, Any]] = []
    for path in sorted((root, *root.rglob("*")), key=lambda item: item.relative_to(root.parent).as_posix()):
        rel = path.relative_to(root.parent).as_posix()
        info = path.lstat()
        mode = stat.S_IMODE(info.st_mode)
        entry: dict[str, Any] = {"path": rel, "mode": mode, "type": "other"}
        if stat.S_ISDIR(info.st_mode):
            entry["type"] = "directory"
        elif stat.S_ISREG(info.st_mode):
            entry.update({"type": "file", "sha256": hash_file(path), "size": info.st_size})
        elif stat.S_ISLNK(info.st_mode):
            target = os.readlink(path)
            entry.update({"type": "symlink", "target_sha256": hashlib.sha256(target.encode("utf-8")).hexdigest()})
        entries.append(entry)
    return entries


def classify_records(records: list[dict[str, Any]], ownership: dict[str, Any]) -> list[dict[str, Any]]:
    classified: list[dict[str, Any]] = []
    for record in records:
        path = record["path"]
        owner = require_exact_owner(path, ownership)
        orig_path = record.get("orig_path")
        orig_owner = require_exact_owner(orig_path, ownership) if orig_path else owner
        if orig_path and owner != orig_owner:
            raise PreflightError(f"rename outside one owner: {orig_path} -> {path}")
        classified.append({**record, "owner": owner})
    return classified


def final_candidate_paths(records: list[dict[str, Any]]) -> list[str]:
    paths: set[str] = set()
    for record in records:
        if record["owner"] == "FORBIDDEN":
            continue
        paths.add(record["path"])
    return sorted(paths, key=lambda value: value.encode("utf-8"))


def verify_generated_bundle_matches_builder(project_root: Path) -> None:
    builder_path = project_root / "scripts" / "build-codex-plugin.py"
    if not builder_path.is_file():
        raise PreflightError(f"missing atomic bundle builder: {builder_path}")
    spec = importlib.util.spec_from_file_location("teamwork_build_codex_plugin", builder_path)
    if spec is None or spec.loader is None:
        raise PreflightError(f"cannot load atomic bundle builder: {builder_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    temp_parent = Path(tempfile.mkdtemp(prefix="teamwork-bundle-preflight."))
    try:
        module.validate_source(project_root)
        stage = module.build_stage(project_root, temp_parent)
        if not module.bundle_matches(project_root / "plugins" / module.PLUGIN_NAME, stage):
            raise PreflightError("plugins/teamwork-skill differs from atomic builder output")
    finally:
        shutil.rmtree(temp_parent, ignore_errors=True)


def validate_fixture_invariants(ownership: dict[str, Any]) -> None:
    gitignore_owner = require_exact_owner(".gitignore", ownership)
    if gitignore_owner != "Public docs/version/metadata":
        raise PreflightError(".gitignore must be exclusively Public docs/version/metadata-owned")
    for candidate_path in (
        "scripts/candidate-path-preflight.py",
        "scripts/build-candidate-snapshot.py",
        "scripts/tests/test_candidate_path_preflight.py",
        "scripts/tests/test_build_candidate_snapshot.py",
        "scripts/tests/fixtures/v5-unified-collaborate-path-ownership.json",
    ):
        if require_exact_owner(candidate_path, ownership) != "Candidate preflight":
            raise PreflightError(f"{candidate_path} must be Candidate preflight-owned")


def capture(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    ownership = load_ownership(Path(args.ownership))
    validate_fixture_invariants(ownership)
    records = classify_records(status_records(project_root), ownership)
    data = {
        "schema_version": SCHEMA_VERSION,
        "project_root": str(project_root),
        "ownership": str(Path(args.ownership).resolve()),
        "records": records,
        "forbidden_tree": tree_fingerprint(project_root / ".claude"),
    }
    write_canonical_json(Path(args.output), data)
    return 0


def compare(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    ownership = load_ownership(Path(args.ownership))
    validate_fixture_invariants(ownership)
    baseline = load_json(Path(args.baseline))
    if not isinstance(baseline, dict) or baseline.get("schema_version") != SCHEMA_VERSION:
        raise PreflightError("baseline schema mismatch")
    if baseline.get("project_root") != str(project_root):
        raise PreflightError("baseline project_root mismatch")
    baseline_forbidden = baseline.get("forbidden_tree")
    current_forbidden = tree_fingerprint(project_root / ".claude")
    if baseline_forbidden != current_forbidden:
        raise PreflightError(".claude forbidden state changed")
    current_records = classify_records(status_records(project_root), ownership)
    if any(record["path"].startswith("plugins/teamwork-skill/") for record in current_records):
        verify_generated_bundle_matches_builder(project_root)
    paths = final_candidate_paths(current_records)
    state_dir = Path(args.state_dir)
    paths_file = state_dir / "final-candidate-paths.z"
    paths_file.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=".final-candidate-paths.", suffix=".tmp", dir=paths_file.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            for path in paths:
                handle.write(path.encode("utf-8") + b"\0")
        os.replace(tmp_name, paths_file)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass
        raise
    report = {
        "schema_version": SCHEMA_VERSION,
        "success": True,
        "project_root": str(project_root),
        "baseline": str(Path(args.baseline).resolve()),
        "ownership": str(Path(args.ownership).resolve()),
        "candidate_path_count": len(paths),
        "candidate_paths_file": str(paths_file.resolve()),
        "current_records": current_records,
        "forbidden_claude_unchanged": True,
        "gitignore_owner": require_exact_owner(".gitignore", ownership),
    }
    write_canonical_json(Path(args.report), report)
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    capture_parser = subparsers.add_parser("capture")
    capture_parser.add_argument("--project-root", required=True)
    capture_parser.add_argument("--ownership", required=True)
    capture_parser.add_argument("--state-dir", required=True)
    capture_parser.add_argument("--output", required=True)
    compare_parser = subparsers.add_parser("compare")
    compare_parser.add_argument("--project-root", required=True)
    compare_parser.add_argument("--ownership", required=True)
    compare_parser.add_argument("--baseline", required=True)
    compare_parser.add_argument("--state-dir", required=True)
    compare_parser.add_argument("--report", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        if args.command == "capture":
            return capture(args)
        if args.command == "compare":
            return compare(args)
    except (PreflightError, subprocess.CalledProcessError, OSError) as exc:
        print(f"PREWRITE_SAFE: {exc}", file=sys.stderr)
        return 1
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
