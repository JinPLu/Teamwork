#!/usr/bin/env python3
"""Create, validate, seal, and commit an index-isolated release candidate."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import pathlib
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from typing import Any, Iterable, Iterator


SCHEMA_VERSION = 1
BASE_COMMIT = "93572a3e8029b5348ee31d2a65b0c9a06b45beed"
VALID_STATUSES = {"A", "M", "D", "R"}
VALID_STATES = {"writing", "sealed", "validated", "reviewed"}
FAILPOINT_ENV = "TEAMWORK_RELEASE_INDEX_FAILPOINT"
CANDIDATE_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")


class TransactionError(RuntimeError):
    """A typed, fail-closed transaction error."""


def failpoint(name: str) -> None:
    if os.environ.get(FAILPOINT_ENV) == name:
        raise TransactionError(f"injected failure: {name}")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def require_sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise TransactionError(f"{label} must be a SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as error:
        raise TransactionError(f"{label} must be a SHA-256 hex digest") from error
    return value


def require_candidate_id(value: Any, label: str = "candidate_id") -> str:
    if not isinstance(value, str) or not CANDIDATE_ID_RE.fullmatch(value):
        raise TransactionError(f"{label} must be an explicit stable identifier")
    return value


def require_repair_generation(value: Any) -> int:
    if type(value) is not int or value not in {0, 1}:
        raise TransactionError("repair_generation must be 0 or 1")
    return value


def safe_relative(value: Any, label: str = "path") -> str:
    if not isinstance(value, str) or not value or any(character in value for character in ("\x00", "\n", "\r", "\t")):
        raise TransactionError(f"invalid {label}")
    path = pathlib.PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise TransactionError(f"unsafe {label}: {value!r}")
    return path.as_posix()


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def read_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise TransactionError(f"cannot read valid JSON: {path}") from error
    if not isinstance(value, dict):
        raise TransactionError(f"JSON root must be an object: {path}")
    return value


def atomic_write(path: pathlib.Path, data: bytes, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = pathlib.Path(temporary)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary_path, mode)
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def git(
    root: pathlib.Path,
    *arguments: str,
    index: pathlib.Path | None = None,
    work_tree: pathlib.Path | None = None,
    check: bool = True,
    text: bool = False,
) -> subprocess.CompletedProcess[Any]:
    environment = os.environ.copy()
    if index is not None:
        environment["GIT_INDEX_FILE"] = str(index)
    if work_tree is not None:
        environment["GIT_WORK_TREE"] = str(work_tree)
        git_dir = subprocess.run(
            ["git", "rev-parse", "--absolute-git-dir"], cwd=root,
            text=True, capture_output=True, check=True,
        ).stdout.strip()
        environment["GIT_DIR"] = git_dir
    result = subprocess.run(
        ["git", *arguments], cwd=work_tree or root, env=environment,
        capture_output=True, text=text, check=False,
    )
    if check and result.returncode:
        stderr = result.stderr if text else result.stderr.decode(errors="replace")
        raise TransactionError(f"git {' '.join(arguments)} failed: {stderr.strip()}")
    return result


def repository_root(value: str) -> pathlib.Path:
    root = pathlib.Path(value).resolve()
    actual = git(root, "rev-parse", "--show-toplevel", text=True).stdout.strip()
    if pathlib.Path(actual).resolve() != root:
        raise TransactionError("--project-root must be the repository root")
    return root


def resolve_input(root: pathlib.Path, value: str) -> pathlib.Path:
    path = pathlib.Path(value)
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def require_inside(root: pathlib.Path, path: pathlib.Path, label: str) -> pathlib.Path:
    try:
        path.relative_to(root)
    except ValueError as error:
        raise TransactionError(f"{label} must be inside the project root") from error
    return path


def real_index_path(root: pathlib.Path) -> pathlib.Path:
    raw = git(root, "rev-parse", "--git-path", "index", text=True).stdout.strip()
    path = pathlib.Path(raw)
    return path.resolve() if path.is_absolute() else (root / path).resolve()


@contextlib.contextmanager
def index_probe(index_path: pathlib.Path) -> Iterator[pathlib.Path]:
    """Yield a disposable copy of an index for read-only Git inspection.

    Commands such as ``git diff`` refresh stat-cache entries when a tracked file
    was atomically replaced.  Running those commands against the shared index
    would mutate user state even though its staged tree is unchanged.  All
    transaction probes therefore inspect a private copy instead.
    """
    try:
        info = index_path.stat()
        data = index_path.read_bytes()
    except OSError as error:
        raise TransactionError(f"index probe source is unreadable: {index_path}") from error
    if not stat.S_ISREG(info.st_mode):
        raise TransactionError("index probe source is not a regular file")
    descriptor, temporary = tempfile.mkstemp(prefix=".teamwork-index-probe.", dir=index_path.parent)
    probe = pathlib.Path(temporary)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(probe, stat.S_IMODE(info.st_mode))
        yield probe
    finally:
        probe.unlink(missing_ok=True)
        pathlib.Path(f"{probe}.lock").unlink(missing_ok=True)


def parse_debug_flags(debug: str, stage: str) -> list[dict[str, Any]]:
    stages: dict[str, tuple[str, str, int]] = {}
    for line in stage.splitlines():
        try:
            metadata, path = line.split("\t", 1)
            mode, blob_oid, stage_number = metadata.split()
            stages[path] = (mode, blob_oid, int(stage_number))
        except (ValueError, TypeError) as error:
            raise TransactionError("malformed ls-files --stage output") from error
    records: list[dict[str, Any]] = []
    current: str | None = None
    for line in debug.splitlines():
        if line and not line[0].isspace():
            current = line
        elif current is not None and line.strip().startswith("size:") and "flags:" in line:
            flags = line.rsplit("flags:", 1)[1].strip()
            try:
                numeric = int(flags, 16)
            except ValueError as error:
                raise TransactionError("malformed ls-files --debug flags") from error
            if numeric & 0x20000000:
                if current not in stages:
                    raise TransactionError("intent-to-add path is absent from staged metadata")
                mode, blob_oid, stage_number = stages[current]
                records.append({
                    "path": current, "mode": mode, "blob_oid": blob_oid,
                    "stage": stage_number, "flags": flags,
                })
    return records


def snapshot_index(root: pathlib.Path) -> dict[str, Any]:
    path = real_index_path(root)
    try:
        info = path.stat()
        data = path.read_bytes()
    except OSError as error:
        raise TransactionError(f"real index is unreadable: {path}") from error
    if not stat.S_ISREG(info.st_mode):
        raise TransactionError("real index is not a regular file")
    # Do not run Git's read paths against ``path``: a stat-cache refresh is a
    # raw index mutation and must never be caused by candidate preparation.
    with index_probe(path) as probe:
        debug = git(root, "ls-files", "--debug", index=probe, text=True).stdout
        stage = git(root, "ls-files", "--stage", index=probe, text=True).stdout
        write_tree = git(root, "write-tree", index=probe, text=True).stdout.strip()
        cached_raw = git(root, "diff", "--cached", "--raw", "--full-index", index=probe, text=True).stdout
        unmerged = git(root, "ls-files", "--unmerged", index=probe, text=True).stdout
    return {
        "path": str(path),
        "mode": f"{stat.S_IMODE(info.st_mode):04o}",
        "sha256": sha256_bytes(data),
        "write_tree": write_tree,
        "cached_raw": cached_raw,
        "unmerged": unmerged,
        "ls_files_debug_sha256": sha256_bytes(debug.encode()),
        "ls_files_stage_sha256": sha256_bytes(stage.encode()),
        "intent_to_add": parse_debug_flags(debug, stage),
    }


def assert_index_snapshot(root: pathlib.Path, expected: dict[str, Any]) -> None:
    actual = snapshot_index(root)
    if actual != expected:
        raise TransactionError("real-index-prestate-changed")


def load_ledger(path: pathlib.Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    try:
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise TransactionError(f"cannot read valid migration ledger: {path}") from error
    if not rows or not isinstance(rows[0], dict):
        raise TransactionError("migration ledger has no metadata record")
    metadata = rows[0]
    if metadata.get("schema_version") != SCHEMA_VERSION or metadata.get("record_type") != "metadata":
        raise TransactionError("unsupported migration ledger schema")
    if metadata.get("base_commit") != BASE_COMMIT:
        raise TransactionError("migration ledger base commit mismatch")
    records = rows[1:]
    if any(not isinstance(row, dict) for row in records):
        raise TransactionError("migration ledger rows must be objects")
    ids = [row.get("ledger_id") for row in records]
    if any(not isinstance(value, str) or not value for value in ids) or len(ids) != len(set(ids)):
        raise TransactionError("migration ledger IDs must be unique non-empty strings")
    frozen = metadata.get("frozen_candidate_paths")
    candidate_rows = [row for row in records if row.get("record_type") == "candidate-path"]
    if not isinstance(frozen, list) or set(frozen) != {row.get("path") for row in candidate_rows}:
        raise TransactionError("migration ledger candidate freeze is inconsistent")
    return metadata, records


def load_owner_map(path: pathlib.Path) -> dict[str, Any]:
    value = read_json(path)
    required = {"schema_version", "base_commit", "default_owner", "forbidden_prefixes", "owners"}
    if value.get("schema_version") != SCHEMA_VERSION or required - value.keys():
        raise TransactionError("unsupported path-ownership schema")
    if value["base_commit"] != BASE_COMMIT or value["default_owner"] != "FORBIDDEN":
        raise TransactionError("path-ownership base/default mismatch")
    if not isinstance(value["owners"], list) or not isinstance(value["forbidden_prefixes"], list):
        raise TransactionError("malformed path-ownership rules")
    return value


def rule_matches(rule: dict[str, Any], path: str) -> bool:
    if path in rule.get("exclude", []) or any(path.startswith(value) for value in rule.get("exclude_prefixes", [])):
        return False
    return path in rule.get("paths", []) or any(path.startswith(value) for value in rule.get("prefixes", []))


def resolve_owner(mapping: dict[str, Any], path: str) -> str:
    if any(path.startswith(prefix) for prefix in mapping["forbidden_prefixes"]):
        return "FORBIDDEN"
    owners = [rule.get("owner") for rule in mapping["owners"] if isinstance(rule, dict) and rule_matches(rule, path)]
    if len(owners) != 1:
        if not owners:
            return "FORBIDDEN"
        raise TransactionError(f"multiple owners for {path}")
    owner = owners[0]
    if not isinstance(owner, str) or not owner:
        raise TransactionError(f"invalid owner for {path}")
    return owner


def derive_allowlist(records: list[dict[str, Any]], owners: dict[str, Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in records:
        if row.get("record_type") != "candidate-path" or row.get("release_candidate_eligible") is not True:
            continue
        path = safe_relative(row.get("path"), "ledger path")
        if path in seen:
            raise TransactionError(f"duplicate eligible candidate path: {path}")
        seen.add(path)
        owner = resolve_owner(owners, path)
        if owner == "FORBIDDEN" or row.get("owner") != owner:
            raise TransactionError(f"ledger/ownership mismatch for {path}")
        if row.get("disposition") not in {"reuse", "revise", "restore", "retire"}:
            raise TransactionError(f"ineligible disposition for {path}")
        status = row.get("observed_status")
        if status not in VALID_STATUSES:
            raise TransactionError(f"invalid observed status for {path}")
        entry: dict[str, Any] = {
            "ledger_id": row["ledger_id"], "owner": owner, "path": path,
            "allowed_statuses": [status],
        }
        if status == "R":
            entry["old_path"] = safe_relative(row.get("old_path"), "rename old_path")
        entries.append(entry)
    entries.sort(key=lambda entry: entry["path"].encode("utf-8"))
    if not entries:
        raise TransactionError("migration ledger yields an empty release allowlist")
    return entries


def recursive_snapshot(root: pathlib.Path) -> str:
    if not root.is_dir() or root.is_symlink():
        raise TransactionError(f"protected snapshot root is not a directory: {root}")
    lines: list[tuple[bytes, bytes]] = []
    for path in root.rglob("*"):
        relative = path.relative_to(root).as_posix()
        info = path.lstat()
        mode = f"{stat.S_IMODE(info.st_mode):04o}"
        if stat.S_ISREG(info.st_mode):
            kind, value = "file", sha256_bytes(path.read_bytes())
        elif stat.S_ISLNK(info.st_mode):
            kind, value = "symlink", sha256_bytes(os.readlink(path).encode("utf-8"))
        elif stat.S_ISDIR(info.st_mode):
            kind, value = "directory", "-"
        else:
            kind, value = "other", "-"
        encoded_path = relative.encode("utf-8")
        line = encoded_path + b"\0" + kind.encode() + b"\0" + mode.encode() + b"\0" + value.encode() + b"\n"
        lines.append((encoded_path, line))
    return sha256_bytes(b"".join(line for _, line in sorted(lines, key=lambda item: item[0])))


def protected_preimages(
    root: pathlib.Path, records: list[dict[str, Any]], owners: dict[str, Any]
) -> list[dict[str, str]]:
    by_pattern = {
        row.get("path"): row for row in records if row.get("record_type") == "forbidden-snapshot"
    }
    output: list[dict[str, str]] = []
    for prefix in owners["forbidden_prefixes"]:
        if not isinstance(prefix, str) or not prefix.endswith("/"):
            raise TransactionError("forbidden prefixes must be relative directory prefixes")
        relative_root = safe_relative(prefix.rstrip("/"), "forbidden root")
        pattern = f"{relative_root}/**"
        row = by_pattern.get(pattern)
        if not isinstance(row, dict) or row.get("owner") != "FORBIDDEN" \
                or row.get("disposition") != "preserve-user" \
                or row.get("release_candidate_eligible") is not False:
            raise TransactionError(f"missing canonical forbidden snapshot: {pattern}")
        preimage = row.get("preimage")
        if not isinstance(preimage, dict) or preimage.get("file_type") != "directory":
            raise TransactionError(f"malformed forbidden snapshot: {pattern}")
        expected = require_sha256(preimage.get("sha256"), f"forbidden snapshot {pattern}")
        actual = recursive_snapshot(root / relative_root)
        if actual != expected:
            raise TransactionError(f"forbidden-preimage-changed: {pattern}")
        output.append({"path": pattern, "sha256": expected})
    return output


def assert_protected_preimages(root: pathlib.Path, entries: Any) -> None:
    if not isinstance(entries, list):
        raise TransactionError("candidate manifest lacks protected preimages")
    for entry in entries:
        if not isinstance(entry, dict):
            raise TransactionError("protected preimage entry must be an object")
        pattern = entry.get("path")
        if not isinstance(pattern, str) or not pattern.endswith("/**"):
            raise TransactionError("invalid protected preimage path")
        relative_root = safe_relative(pattern[:-3], "protected root")
        expected = require_sha256(entry.get("sha256"), f"protected snapshot {pattern}")
        if recursive_snapshot(root / relative_root) != expected:
            raise TransactionError(f"forbidden-preimage-changed: {pattern}")


def parse_raw_diff(raw: bytes) -> list[dict[str, str]]:
    fields = raw.split(b"\0")
    if fields and fields[-1] == b"":
        fields.pop()
    result: list[dict[str, str]] = []
    index = 0
    while index < len(fields):
        header = fields[index].decode("ascii")
        index += 1
        parts = header.split()
        if len(parts) != 5 or not parts[0].startswith(":"):
            raise TransactionError("malformed candidate raw diff")
        status_token = parts[4]
        status = status_token[0]
        if status not in VALID_STATUSES:
            raise TransactionError(f"unsupported candidate status: {status_token}")
        if index >= len(fields):
            raise TransactionError("candidate raw diff is missing a path")
        first_path = fields[index].decode("utf-8")
        index += 1
        item = {
            "status": status, "mode_before": parts[0][1:], "mode_after": parts[1],
            "blob_oid_before": parts[2], "blob_oid_after": parts[3], "path": first_path,
        }
        if status in {"R", "C"}:
            if index >= len(fields):
                raise TransactionError("rename is missing its destination")
            item["old_path"] = first_path
            item["path"] = fields[index].decode("utf-8")
            index += 1
        result.append(item)
    return result


def candidate_diff(root: pathlib.Path, candidate_index: pathlib.Path, base: str) -> list[dict[str, Any]]:
    raw = git(
        root, "diff-index", "--cached", "--raw", "--full-index", "--find-renames", "-z", base,
        index=candidate_index,
    ).stdout
    entries = parse_raw_diff(raw)
    for entry in entries:
        if entry["status"] == "D":
            entry.update(mode_after=None, blob_oid_after=None, sha256_after=None)
        else:
            blob = git(root, "cat-file", "blob", entry["blob_oid_after"]).stdout
            entry["sha256_after"] = sha256_bytes(blob)
        if entry["mode_before"] == "000000":
            entry.update(mode_before=None, blob_oid_before=None)
        if entry["mode_after"] == "000000":
            entry["mode_after"] = None
    return entries


def working_delta_paths(root: pathlib.Path, base: str) -> set[str]:
    # ``git diff`` refreshes stat-cache entries.  Use a private index so a
    # candidate probe cannot mutate the real index while it is proving that it
    # remains byte-identical.
    with index_probe(real_index_path(root)) as probe:
        tracked = git(root, "diff", "--name-only", "--no-renames", "-z", base, index=probe).stdout
        untracked = git(root, "ls-files", "--others", "--exclude-standard", "-z", index=probe).stdout
    try:
        return {
            safe_relative(value.decode("utf-8"), "working delta path")
            for value in (tracked + untracked).split(b"\0") if value
        }
    except UnicodeDecodeError as error:
        raise TransactionError("working delta contains a non-UTF-8 path") from error


def validate_observed(allowed: list[dict[str, Any]], observed: list[dict[str, Any]]) -> list[dict[str, Any]]:
    allowed_by_path = {entry["path"]: entry for entry in allowed}
    if len(allowed_by_path) != len(allowed):
        raise TransactionError("duplicate release path")
    seen: set[str] = set()
    output: list[dict[str, Any]] = []
    for actual in observed:
        path = actual["path"]
        rule = allowed_by_path.get(path)
        if rule is None:
            raise TransactionError(f"unlisted candidate delta: {path}")
        if actual["status"] not in rule["allowed_statuses"]:
            raise TransactionError(f"status not allowed for {path}: {actual['status']}")
        if actual.get("old_path") != rule.get("old_path"):
            raise TransactionError(f"rename source mismatch for {path}")
        seen.add(path)
        output.append({
            "ledger_id": rule["ledger_id"], "owner": rule["owner"], **actual,
        })
    missing = set(allowed_by_path) - seen
    if missing:
        raise TransactionError(f"allowlisted paths have no candidate delta: {', '.join(sorted(missing))}")
    output.sort(key=lambda entry: entry["path"].encode("utf-8"))
    return output


def checked_runtime_path(root: pathlib.Path, path: pathlib.Path, label: str) -> None:
    require_inside(root, path, label)
    relative = path.relative_to(root).as_posix()
    with index_probe(real_index_path(root)) as probe:
        if git(root, "check-ignore", "-q", "--", relative, index=probe, check=False).returncode != 0:
            raise TransactionError(f"{label} must be ignored runtime state: {relative}")
        if git(root, "ls-files", "--error-unmatch", "--", relative, index=probe, check=False).returncode == 0:
            raise TransactionError(f"{label} must not be tracked: {relative}")


def state_metadata_path(state_dir: pathlib.Path) -> pathlib.Path:
    return state_dir / "transaction.json"


def candidate_triplet(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "scope_revision": require_sha256(manifest.get("scope_revision"), "scope_revision"),
        "candidate_id": require_candidate_id(manifest.get("candidate_id")),
        "candidate_tree_oid": manifest.get("candidate_tree_oid"),
        "repair_generation": require_repair_generation(manifest.get("repair_generation")),
    }


def candidate_fingerprint(manifest: dict[str, Any]) -> str:
    value = {
        **candidate_triplet(manifest),
        "base_commit": manifest.get("base_commit"),
        "paths_manifest_sha256": manifest.get("paths_manifest_sha256"),
        "entries": manifest.get("entries"),
    }
    return sha256_bytes(canonical_json_bytes(value))


def artifact_triplet(root: pathlib.Path, path: pathlib.Path, label: str, manifest: dict[str, Any]) -> tuple[dict[str, Any], str]:
    require_inside(root, path, label)
    try:
        data = path.read_bytes()
    except OSError as error:
        raise TransactionError(f"cannot read {label}") from error
    value = read_json(path)
    expected = candidate_triplet(manifest)
    if any(value.get(key) != expected[key] for key in expected):
        raise TransactionError(f"{label} candidate triplet mismatch")
    if value.get("candidate_fingerprint") != manifest.get("candidate_fingerprint"):
        raise TransactionError(f"{label} candidate fingerprint mismatch")
    return value, sha256_bytes(data)


def load_state(root: pathlib.Path, state_dir: pathlib.Path) -> dict[str, Any]:
    state = read_json(state_metadata_path(state_dir))
    if state.get("schema_version") != SCHEMA_VERSION or state.get("project_root") != str(root):
        raise TransactionError("transaction state does not match this repository")
    return state


def restore_bytes(index_path: pathlib.Path, snapshot_path: pathlib.Path, mode: int) -> None:
    data = snapshot_path.read_bytes()
    descriptor, temporary = tempfile.mkstemp(prefix=".teamwork-index-restore.", dir=index_path.parent)
    temporary_path = pathlib.Path(temporary)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary_path, mode)
        os.replace(temporary_path, index_path)
        if index_path.read_bytes() != data or stat.S_IMODE(index_path.stat().st_mode) != mode:
            raise TransactionError("real index restore readback failed")
    finally:
        temporary_path.unlink(missing_ok=True)


def prepare(args: argparse.Namespace) -> None:
    root = repository_root(args.project_root)
    scope_revision = require_sha256(args.scope_revision, "scope_revision")
    candidate_id = require_candidate_id(args.candidate_id)
    repair_generation = require_repair_generation(args.repair_generation)
    predecessor_candidate_id: str | None = None
    predecessor_tree_oid: str | None = None
    predecessor_manifest = getattr(args, "predecessor_manifest", None)
    predecessor_state_dir = getattr(args, "predecessor_state_dir", None)
    if repair_generation == 0:
        if predecessor_manifest or predecessor_state_dir:
            raise TransactionError("initial candidate must not name a predecessor")
    else:
        if not predecessor_manifest or not predecessor_state_dir:
            raise TransactionError("repair candidate requires predecessor manifest and state")
        predecessor_path = require_inside(root, resolve_input(root, predecessor_manifest), "predecessor manifest")
        predecessor_state_path = resolve_input(root, predecessor_state_dir)
        predecessor, predecessor_state = verify_candidate(
            root, predecessor_path, predecessor_state_path, {"reviewed"}, verify_worktree=False,
        )
        verify_review_binding(root, predecessor, predecessor_state)
        if predecessor.get("scope_revision") != scope_revision or predecessor.get("repair_generation") != 0:
            raise TransactionError("repair predecessor scope/generation mismatch")
        if predecessor.get("review_verdict") != "REVISE":
            raise TransactionError("repair predecessor must have a REVISE review")
        predecessor_candidate_id = require_candidate_id(predecessor.get("candidate_id"), "predecessor candidate_id")
        predecessor_tree_oid = predecessor.get("candidate_tree_oid")
        if predecessor_candidate_id == candidate_id:
            raise TransactionError("source repair must create a successor candidate_id")
    ledger_path = require_inside(root, resolve_input(root, args.ledger), "ledger")
    owner_path = require_inside(root, resolve_input(root, args.ownership), "ownership map")
    paths_path = resolve_input(root, args.paths)
    manifest_path = resolve_input(root, args.manifest)
    state_dir = resolve_input(root, args.state_dir)
    for path, label in ((paths_path, "paths manifest"), (manifest_path, "candidate manifest"), (state_dir, "state directory")):
        checked_runtime_path(root, path, label)
    head = git(root, "rev-parse", "HEAD", text=True).stdout.strip()
    if head != BASE_COMMIT:
        raise TransactionError(f"HEAD must equal {BASE_COMMIT}")
    _, records = load_ledger(ledger_path)
    owners = load_owner_map(owner_path)
    allowed = derive_allowlist(records, owners)
    protected = protected_preimages(root, records, owners)
    paths_document = {"schema_version": SCHEMA_VERSION, "base_commit": BASE_COMMIT, "entries": allowed}
    paths_bytes = canonical_json_bytes(paths_document)
    prestate = snapshot_index(root)
    real_index = pathlib.Path(prestate["path"])
    state_dir.mkdir(parents=True, exist_ok=True)
    if state_dir.stat().st_dev != real_index.parent.stat().st_dev:
        raise TransactionError("state directory and real index must share a filesystem")
    candidate_index = state_dir / "candidate.index"
    snapshot_path = state_dir / "real-index.preimage"
    atomic_write(snapshot_path, real_index.read_bytes(), int(prestate["mode"], 8))
    candidate_index.unlink(missing_ok=True)
    failpoint("prepare.before_read_tree")
    git(root, "read-tree", f"{BASE_COMMIT}^{{tree}}", index=candidate_index)
    failpoint("prepare.after_read_tree")
    explicit_paths: list[str] = []
    for entry in allowed:
        explicit_paths.extend([entry["path"]])
        if "old_path" in entry:
            explicit_paths.append(entry["old_path"])
    protected_prefixes = tuple(owners["forbidden_prefixes"])
    unexpected = {
        path for path in working_delta_paths(root, BASE_COMMIT) - set(explicit_paths)
        if not path.startswith(protected_prefixes)
    }
    if unexpected:
        raise TransactionError(f"unlisted working delta: {', '.join(sorted(unexpected))}")
    failpoint("prepare.before_stage")
    git(root, "add", "-A", "--", *explicit_paths, index=candidate_index)
    failpoint("prepare.after_stage")
    assert_index_snapshot(root, prestate)
    failpoint("prepare.before_compare")
    observed = validate_observed(allowed, candidate_diff(root, candidate_index, BASE_COMMIT))
    tree_oid = git(root, "write-tree", index=candidate_index, text=True).stdout.strip()
    if predecessor_tree_oid is not None and tree_oid == predecessor_tree_oid:
        raise TransactionError("source repair must create a different successor tree")
    failpoint("prepare.after_compare")
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "state": "writing",
        "base_commit": BASE_COMMIT,
        "scope_revision": scope_revision,
        "candidate_id": candidate_id,
        "candidate_tree_oid": tree_oid,
        "repair_generation": repair_generation,
        "predecessor_candidate_id": predecessor_candidate_id,
        "paths_manifest_sha256": sha256_bytes(paths_bytes),
        "candidate_fingerprint": None,
        "sealed_manifest_sha256": None,
        "validation_artifact_sha256": None,
        "review_artifact_sha256": None,
        "review_verdict": None,
        "writer_leases": [],
        "real_index_prestate": prestate,
        "protected_preimages": protected,
        "entries": observed,
    }
    manifest["candidate_fingerprint"] = candidate_fingerprint(manifest)
    state = {
        "schema_version": SCHEMA_VERSION,
        "project_root": str(root),
        "ledger": str(ledger_path),
        "ownership": str(owner_path),
        "paths_manifest": str(paths_path),
        "candidate_manifest": str(manifest_path),
        "candidate_index": str(candidate_index),
        "real_index_snapshot": str(snapshot_path),
        "validation_artifact": None,
        "review_artifact": None,
    }
    atomic_write(paths_path, paths_bytes)
    atomic_write(manifest_path, canonical_json_bytes(manifest))
    atomic_write(state_metadata_path(state_dir), canonical_json_bytes(state))
    assert_index_snapshot(root, prestate)
    assert_protected_preimages(root, protected)


def validate_manifest_shape(manifest: dict[str, Any], states: set[str]) -> None:
    required = {
        "schema_version", "state", "base_commit", "candidate_tree_oid",
        "scope_revision", "candidate_id", "repair_generation", "predecessor_candidate_id",
        "paths_manifest_sha256", "candidate_fingerprint", "sealed_manifest_sha256",
        "validation_artifact_sha256", "review_artifact_sha256", "review_verdict", "writer_leases",
        "real_index_prestate", "entries",
        "protected_preimages",
    }
    if manifest.get("schema_version") != SCHEMA_VERSION or required - manifest.keys():
        raise TransactionError("unsupported candidate manifest schema")
    if manifest.get("state") not in states or manifest.get("base_commit") != BASE_COMMIT:
        raise TransactionError("candidate manifest state/base mismatch")
    require_sha256(manifest.get("paths_manifest_sha256"), "paths manifest hash")
    candidate_triplet(manifest)
    require_sha256(manifest.get("candidate_fingerprint"), "candidate fingerprint")
    if manifest["candidate_fingerprint"] != candidate_fingerprint(manifest):
        raise TransactionError("candidate-fingerprint-changed")
    generation = manifest["repair_generation"]
    predecessor = manifest.get("predecessor_candidate_id")
    if (generation == 0 and predecessor is not None) or (generation == 1 and not isinstance(predecessor, str)):
        raise TransactionError("candidate predecessor/generation mismatch")
    if generation == 1:
        require_candidate_id(predecessor, "predecessor candidate_id")
    if not isinstance(manifest.get("writer_leases"), list):
        raise TransactionError("candidate writer leases must be a list")
    if manifest["state"] != "writing" and manifest["writer_leases"]:
        raise TransactionError("sealed candidate retains writer leases")
    for field in ("sealed_manifest_sha256", "validation_artifact_sha256", "review_artifact_sha256"):
        if manifest.get(field) is not None:
            require_sha256(manifest[field], field)
    if not isinstance(manifest.get("entries"), list):
        raise TransactionError("candidate entries must be a list")
    paths: list[str] = []
    for entry in manifest["entries"]:
        if not isinstance(entry, dict):
            raise TransactionError("candidate entry must be an object")
        path = safe_relative(entry.get("path"), "candidate path")
        paths.append(path)
        if entry.get("status") not in VALID_STATUSES:
            raise TransactionError(f"invalid candidate status: {path}")
        if entry["status"] == "D":
            if any(entry.get(key) is not None for key in ("mode_after", "blob_oid_after", "sha256_after")):
                raise TransactionError(f"deletion has a post-image: {path}")
        else:
            require_sha256(entry.get("sha256_after"), f"post-image hash for {path}")
    if paths != sorted(paths, key=lambda value: value.encode("utf-8")) or len(paths) != len(set(paths)):
        raise TransactionError("candidate entries must be uniquely UTF-8 sorted")


def verify_candidate(
    root: pathlib.Path,
    manifest_path: pathlib.Path,
    state_dir: pathlib.Path,
    states: set[str],
    verify_worktree: bool = True,
) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = read_json(manifest_path)
    validate_manifest_shape(manifest, states)
    state = load_state(root, state_dir)
    if pathlib.Path(state.get("candidate_manifest", "")) != manifest_path:
        raise TransactionError("candidate manifest path differs from transaction state")
    paths_path = pathlib.Path(state["paths_manifest"])
    candidate_index = pathlib.Path(state["candidate_index"])
    snapshot_path = pathlib.Path(state["real_index_snapshot"])
    if candidate_index != state_dir / "candidate.index" \
            or snapshot_path != state_dir / "real-index.preimage":
        raise TransactionError("transaction state contains an unexpected state-file path")
    checked_runtime_path(root, paths_path, "paths manifest")
    if sha256_bytes(paths_path.read_bytes()) != manifest["paths_manifest_sha256"]:
        raise TransactionError("paths-manifest-changed")
    tree_oid = git(root, "write-tree", index=candidate_index, text=True).stdout.strip()
    if tree_oid != manifest["candidate_tree_oid"]:
        raise TransactionError("candidate-index-tree-changed")
    assert_index_snapshot(root, manifest["real_index_prestate"])
    assert_protected_preimages(root, manifest["protected_preimages"])
    if verify_worktree:
        for entry in manifest["entries"]:
            path = root / entry["path"]
            if entry["status"] == "D":
                if path.exists() or path.is_symlink():
                    raise TransactionError(f"deleted candidate path returned: {entry['path']}")
            else:
                try:
                    info = path.lstat()
                    if entry["mode_after"] == "120000":
                        if not stat.S_ISLNK(info.st_mode):
                            raise TransactionError(f"candidate post-image type changed: {entry['path']}")
                        data = os.readlink(path).encode("utf-8")
                    else:
                        if entry["mode_after"] not in {"100644", "100755"} or not stat.S_ISREG(info.st_mode):
                            raise TransactionError(f"unsupported candidate post-image mode: {entry['path']}")
                        executable = bool(stat.S_IMODE(info.st_mode) & 0o111)
                        if executable != (entry["mode_after"] == "100755"):
                            raise TransactionError(f"candidate post-image mode changed: {entry['path']}")
                        data = path.read_bytes()
                except OSError as error:
                    raise TransactionError(f"candidate post-image missing: {entry['path']}") from error
                if sha256_bytes(data) != entry["sha256_after"]:
                    raise TransactionError(f"candidate post-image changed: {entry['path']}")
    return manifest, state


def run_command(args: argparse.Namespace) -> int:
    root = repository_root(args.project_root)
    manifest_path = resolve_input(root, args.manifest)
    state_dir = resolve_input(root, args.state_dir)
    manifest, state = verify_candidate(root, manifest_path, state_dir, {"sealed", "validated", "reviewed"}, verify_worktree=False)
    if not args.command:
        raise TransactionError("run requires a command after --")
    with tempfile.TemporaryDirectory(prefix="teamwork-release-candidate-") as temporary:
        temporary_root = pathlib.Path(temporary)
        worktree = temporary_root / "worktree"
        home = temporary_root / "home"
        worktree.mkdir()
        home.mkdir()
        candidate_index = pathlib.Path(state["candidate_index"])
        # Materialize a complete disposable repository rather than pointing the
        # child at this repository's .git directory.  Candidate commands may
        # initialize fixtures or change local Git config; neither action may
        # leak into the user's checkout.
        environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        environment["HOME"] = str(home)
        environment["XDG_CONFIG_HOME"] = str(home / ".config")
        environment["GIT_CONFIG_NOSYSTEM"] = "1"
        source_git_dir = pathlib.Path(git(root, "rev-parse", "--absolute-git-dir", text=True).stdout.strip())
        environment["TEAMWORK_CANDIDATE_ISOLATED"] = "1"
        initialized = subprocess.run(["git", "init", "-q"], cwd=worktree, env=environment, capture_output=True, text=True, check=False)
        if initialized.returncode:
            raise TransactionError(f"cannot initialize candidate repository: {initialized.stderr.strip()}")
        # Persist the read-only object-store link in disposable Git metadata so
        # nested tools that deliberately sanitize GIT_* variables still see a
        # complete repository. Nothing is written into the source repository.
        alternates = worktree / ".git" / "objects" / "info" / "alternates"
        try:
            alternates.parent.mkdir(parents=True, exist_ok=True)
            alternates.write_text(f"{source_git_dir / 'objects'}\n", encoding="utf-8")
        except OSError as error:
            raise TransactionError("cannot bind candidate object store") from error
        anchored = subprocess.run(["git", "update-ref", "HEAD", manifest["base_commit"]], cwd=worktree, env=environment, capture_output=True, text=True, check=False)
        if anchored.returncode:
            raise TransactionError(f"cannot anchor candidate repository: {anchored.stderr.strip()}")
        runtime_index = worktree / ".git" / "index"
        shutil.copy2(candidate_index, runtime_index)
        checkout = subprocess.run(
            ["git", "checkout-index", "--all", "--force", f"--prefix={worktree.as_posix()}/"],
            cwd=worktree, env=environment, capture_output=True, text=True, check=False,
        )
        if checkout.returncode:
            raise TransactionError(f"cannot materialize candidate worktree: {checkout.stderr.strip()}")
        result = subprocess.run(args.command, cwd=worktree, env=environment, check=False)
    assert_index_snapshot(root, manifest["real_index_prestate"])
    assert_protected_preimages(root, manifest["protected_preimages"])
    return result.returncode


def file_binding(root: pathlib.Path, value: Any, label: str) -> dict[str, str]:
    if not isinstance(value, dict):
        raise TransactionError(f"{label} binding must be an object")
    relative = safe_relative(value.get("path"), f"{label} path")
    expected = require_sha256(value.get("sha256"), f"{label} hash")
    path = root / relative
    try:
        if not stat.S_ISREG(path.lstat().st_mode) or path.is_symlink():
            raise TransactionError(f"{label} evidence must be a regular in-repository file")
        actual = sha256_bytes(path.read_bytes())
    except OSError as error:
        raise TransactionError(f"cannot read {label} evidence") from error
    if actual != expected:
        raise TransactionError(f"{label} evidence hash mismatch")
    return {"path": relative, "sha256": expected}


def mutate_writer_lease(args: argparse.Namespace, acquire: bool) -> None:
    root = repository_root(args.project_root)
    manifest_path = resolve_input(root, args.manifest)
    state_dir = resolve_input(root, args.state_dir)
    manifest, _ = verify_candidate(root, manifest_path, state_dir, {"writing"}, verify_worktree=False)
    writer_id = require_candidate_id(args.writer_id, "writer_id")
    leases = manifest["writer_leases"]
    if acquire:
        if writer_id in leases:
            raise TransactionError("writer lease already held")
        leases.append(writer_id)
        leases.sort()
    else:
        if writer_id not in leases:
            raise TransactionError("writer lease is not held")
        leases.remove(writer_id)
    atomic_write(manifest_path, canonical_json_bytes(manifest))


def acquire_writer(args: argparse.Namespace) -> None:
    mutate_writer_lease(args, True)


def release_writer(args: argparse.Namespace) -> None:
    mutate_writer_lease(args, False)


def seal(args: argparse.Namespace) -> None:
    root = repository_root(args.project_root)
    manifest_path = resolve_input(root, args.manifest)
    state_dir = resolve_input(root, args.state_dir)
    manifest, _ = verify_candidate(root, manifest_path, state_dir, {"writing"})
    if manifest["writer_leases"]:
        raise TransactionError("cannot seal candidate while writer leases are active")
    writing_hash = sha256_bytes(manifest_path.read_bytes())
    manifest["sealed_manifest_sha256"] = writing_hash
    manifest["state"] = "sealed"
    atomic_write(manifest_path, canonical_json_bytes(manifest))
    verify_candidate(root, manifest_path, state_dir, {"sealed"}, verify_worktree=False)


def validate(args: argparse.Namespace) -> None:
    root = repository_root(args.project_root)
    manifest_path = resolve_input(root, args.manifest)
    state_dir = resolve_input(root, args.state_dir)
    evidence_path = require_inside(root, resolve_input(root, args.evidence), "validation artifact")
    manifest, state = verify_candidate(root, manifest_path, state_dir, {"sealed"}, verify_worktree=False)
    evidence, evidence_hash = artifact_triplet(root, evidence_path, "validation artifact", manifest)
    if evidence.get("schema_version") != SCHEMA_VERSION or evidence.get("status") != "PASS":
        raise TransactionError("validation artifact must report PASS")
    manifest["validation_artifact_sha256"] = evidence_hash
    manifest["state"] = "validated"
    state["validation_artifact"] = str(evidence_path)
    atomic_write(manifest_path, canonical_json_bytes(manifest))
    atomic_write(state_metadata_path(state_dir), canonical_json_bytes(state))


def verify_validation_binding(root: pathlib.Path, manifest: dict[str, Any], state: dict[str, Any]) -> None:
    expected = require_sha256(manifest.get("validation_artifact_sha256"), "validation artifact hash")
    value = state.get("validation_artifact")
    if not isinstance(value, str) or not value:
        raise TransactionError("transaction state lacks validation artifact")
    _, actual = artifact_triplet(root, pathlib.Path(value), "validation artifact", manifest)
    if actual != expected:
        raise TransactionError("validation-artifact-changed")


def review(args: argparse.Namespace) -> None:
    root = repository_root(args.project_root)
    manifest_path = resolve_input(root, args.manifest)
    state_dir = resolve_input(root, args.state_dir)
    review_path = require_inside(root, resolve_input(root, args.review), "review artifact")
    manifest, state = verify_candidate(root, manifest_path, state_dir, {"validated"}, verify_worktree=False)
    verify_validation_binding(root, manifest, state)
    value, review_hash = artifact_triplet(root, review_path, "review artifact", manifest)
    required = {"schema_version", "reviewer_identity", "reviewer_model", "reviewer_effort", "review_pass", "verdict", "findings", "validation_artifact_sha256", "plan", "evidence"}
    if required - value.keys():
        raise TransactionError("unsupported implementation-review schema")
    expected_pass = "initial" if manifest["repair_generation"] == 0 else "delta-recheck"
    if value.get("review_pass") != expected_pass:
        raise TransactionError("candidate review pass exceeds the initial plus one delta-recheck budget")
    if value.get("reviewer_identity") != "teamwork_deep_reviewer" or value.get("reviewer_model") != "gpt-5.6-sol" or value.get("reviewer_effort") != "max":
        raise TransactionError("implementation review is not from the named max Reviewer")
    if value.get("validation_artifact_sha256") != manifest["validation_artifact_sha256"]:
        raise TransactionError("implementation review validation binding mismatch")
    if value.get("verdict") not in {"ACCEPT", "REVISE"} or not isinstance(value.get("findings"), list):
        raise TransactionError("implementation review verdict/findings are invalid")
    if value["verdict"] == "REVISE" and manifest["repair_generation"] == 1:
        raise TransactionError("delta recheck cannot create another repair generation")
    plan = file_binding(root, value["plan"], "Plan")
    if not isinstance(value["evidence"], list) or not value["evidence"]:
        raise TransactionError("implementation review evidence must be non-empty")
    evidence = [file_binding(root, item, "review evidence") for item in value["evidence"]]
    manifest["review_artifact_sha256"] = review_hash
    manifest["review_verdict"] = value["verdict"]
    manifest["review_binding"] = {"plan": plan, "evidence": evidence}
    manifest["state"] = "reviewed"
    state["review_artifact"] = str(review_path)
    atomic_write(manifest_path, canonical_json_bytes(manifest))
    atomic_write(state_metadata_path(state_dir), canonical_json_bytes(state))


def verify_review_binding(root: pathlib.Path, manifest: dict[str, Any], state: dict[str, Any]) -> None:
    verify_validation_binding(root, manifest, state)
    expected = require_sha256(manifest.get("review_artifact_sha256"), "review artifact hash")
    value = state.get("review_artifact")
    if not isinstance(value, str) or not value:
        raise TransactionError("transaction state lacks review artifact")
    review_value, actual = artifact_triplet(root, pathlib.Path(value), "review artifact", manifest)
    if actual != expected:
        raise TransactionError("review-artifact-changed")
    if review_value.get("verdict") != manifest.get("review_verdict"):
        raise TransactionError("review verdict binding mismatch")
    if review_value.get("validation_artifact_sha256") != manifest.get("validation_artifact_sha256"):
        raise TransactionError("implementation review validation binding mismatch")
    plan = file_binding(root, review_value.get("plan"), "Plan")
    evidence_value = review_value.get("evidence")
    if not isinstance(evidence_value, list) or not evidence_value:
        raise TransactionError("implementation review evidence must be non-empty")
    evidence = [file_binding(root, item, "review evidence") for item in evidence_value]
    if manifest.get("review_binding") != {"plan": plan, "evidence": evidence}:
        raise TransactionError("review binding differs from the reviewed artifact")


def manifest_explicit_paths(entries: Iterable[dict[str, Any]]) -> list[str]:
    paths: list[str] = []
    for entry in entries:
        paths.append(entry["path"])
        if entry.get("old_path"):
            paths.append(entry["old_path"])
    return paths


def restore(args: argparse.Namespace) -> None:
    root = repository_root(args.project_root)
    state_dir = resolve_input(root, args.state_dir)
    state = load_state(root, state_dir)
    snapshot = pathlib.Path(state["real_index_snapshot"])
    if snapshot != state_dir / "real-index.preimage":
        raise TransactionError("restore snapshot path differs from canonical state path")
    manifest = read_json(pathlib.Path(state["candidate_manifest"]))
    expected = manifest["real_index_prestate"]
    if pathlib.Path(expected.get("path", "")) != real_index_path(root):
        raise TransactionError("restore target differs from the repository index")
    if sha256_bytes(snapshot.read_bytes()) != expected.get("sha256"):
        raise TransactionError("restore snapshot hash mismatch")
    if git(root, "rev-parse", "HEAD", text=True).stdout.strip() != manifest["base_commit"]:
        raise TransactionError("restore refuses after HEAD changed")
    restore_bytes(pathlib.Path(expected["path"]), snapshot, int(expected["mode"], 8))
    assert_index_snapshot(root, expected)


def commit(args: argparse.Namespace) -> None:
    root = repository_root(args.project_root)
    manifest_path = resolve_input(root, args.manifest)
    state_dir = resolve_input(root, args.state_dir)
    message_path = require_inside(root, resolve_input(root, args.message_file), "commit message")
    manifest, state = verify_candidate(root, manifest_path, state_dir, {"reviewed"}, verify_worktree=False)
    verify_review_binding(root, manifest, state)
    if manifest.get("review_verdict") != "ACCEPT":
        raise TransactionError("commit requires an accepted reviewed candidate")
    if git(root, "rev-parse", "HEAD", text=True).stdout.strip() != BASE_COMMIT:
        raise TransactionError("commit base changed")
    prestate = manifest["real_index_prestate"]
    if prestate["cached_raw"] or prestate["unmerged"]:
        raise TransactionError("real-index-cached-or-unmerged-blocker")
    allowed = set(manifest_explicit_paths(manifest["entries"]))
    unexpected_ita = {entry["path"] for entry in prestate["intent_to_add"]} - allowed
    if unexpected_ita:
        raise TransactionError("real-index-nonallowlisted-ita-blocker")
    real_index = pathlib.Path(prestate["path"])
    descriptor, backup_name = tempfile.mkstemp(prefix=".teamwork-index-release.", dir=real_index.parent)
    os.close(descriptor)
    backup = pathlib.Path(backup_name)
    backup.write_bytes(real_index.read_bytes())
    os.chmod(backup, int(prestate["mode"], 8))
    committed = False
    try:
        failpoint("commit.before_stage")
        git(root, "add", "-A", "--", *manifest_explicit_paths(manifest["entries"]), index=real_index)
        failpoint("commit.after_stage")
        failpoint("commit.before_compare")
        if git(root, "write-tree", index=real_index, text=True).stdout.strip() != manifest["candidate_tree_oid"]:
            raise TransactionError("real staged tree differs from verified candidate")
        staged = validate_observed(
            [
                {
                    "ledger_id": entry["ledger_id"], "owner": entry["owner"], "path": entry["path"],
                    "old_path": entry.get("old_path"), "allowed_statuses": [entry["status"]],
                }
                for entry in manifest["entries"]
            ],
            candidate_diff(root, real_index, BASE_COMMIT),
        )
        comparable = [
            {key: entry.get(key) for key in ("path", "old_path", "status", "mode_before", "mode_after", "blob_oid_before", "blob_oid_after", "sha256_after")}
            for entry in staged
        ]
        expected = [
            {key: entry.get(key) for key in ("path", "old_path", "status", "mode_before", "mode_after", "blob_oid_before", "blob_oid_after", "sha256_after")}
            for entry in manifest["entries"]
        ]
        if comparable != expected:
            raise TransactionError("real staged diff differs from verified candidate")
        failpoint("commit.after_compare")
        assert_protected_preimages(root, manifest["protected_preimages"])
        failpoint("commit.before_invoke")
        git(root, "commit", "--file", str(message_path), index=real_index)
        if git(root, "rev-parse", "HEAD^{tree}", text=True).stdout.strip() != manifest["candidate_tree_oid"]:
            raise TransactionError("commit tree differs from verified candidate")
        committed = True
    finally:
        if not committed:
            restore_bytes(real_index, backup, int(prestate["mode"], 8))
            assert_index_snapshot(root, prestate)
        backup.unlink(missing_ok=True)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    subcommands = result.add_subparsers(dest="subcommand", required=True)
    common: dict[str, Any] = {"required": True}
    prepare_parser = subcommands.add_parser("prepare")
    prepare_parser.add_argument("--project-root", **common)
    prepare_parser.add_argument("--ledger", **common)
    prepare_parser.add_argument("--ownership", default="scripts/tests/fixtures/v4-path-ownership.json")
    prepare_parser.add_argument("--paths", **common)
    prepare_parser.add_argument("--manifest", **common)
    prepare_parser.add_argument("--state-dir", **common)
    prepare_parser.add_argument("--scope-revision", **common)
    prepare_parser.add_argument("--candidate-id", **common)
    prepare_parser.add_argument("--repair-generation", required=True, type=int)
    prepare_parser.add_argument("--predecessor-manifest")
    prepare_parser.add_argument("--predecessor-state-dir")
    prepare_parser.set_defaults(handler=prepare)
    run_parser = subcommands.add_parser("run")
    run_parser.add_argument("--project-root", **common)
    run_parser.add_argument("--manifest", **common)
    run_parser.add_argument("--state-dir", **common)
    run_parser.add_argument("command", nargs=argparse.REMAINDER)
    run_parser.set_defaults(handler=run_command)
    seal_parser = subcommands.add_parser("seal")
    seal_parser.add_argument("--project-root", **common)
    seal_parser.add_argument("--manifest", **common)
    seal_parser.add_argument("--state-dir", **common)
    seal_parser.set_defaults(handler=seal)
    for name, handler in (("acquire-writer", acquire_writer), ("release-writer", release_writer)):
        lease_parser = subcommands.add_parser(name)
        lease_parser.add_argument("--project-root", **common)
        lease_parser.add_argument("--manifest", **common)
        lease_parser.add_argument("--state-dir", **common)
        lease_parser.add_argument("--writer-id", **common)
        lease_parser.set_defaults(handler=handler)
    validate_parser = subcommands.add_parser("validate")
    validate_parser.add_argument("--project-root", **common)
    validate_parser.add_argument("--manifest", **common)
    validate_parser.add_argument("--state-dir", **common)
    validate_parser.add_argument("--evidence", **common)
    validate_parser.set_defaults(handler=validate)
    review_parser = subcommands.add_parser("review")
    review_parser.add_argument("--project-root", **common)
    review_parser.add_argument("--manifest", **common)
    review_parser.add_argument("--state-dir", **common)
    review_parser.add_argument("--review", **common)
    review_parser.set_defaults(handler=review)
    commit_parser = subcommands.add_parser("commit")
    commit_parser.add_argument("--project-root", **common)
    commit_parser.add_argument("--manifest", **common)
    commit_parser.add_argument("--state-dir", **common)
    commit_parser.add_argument("--message-file", **common)
    commit_parser.set_defaults(handler=commit)
    restore_parser = subcommands.add_parser("restore")
    restore_parser.add_argument("--project-root", **common)
    restore_parser.add_argument("--state-dir", **common)
    restore_parser.set_defaults(handler=restore)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if getattr(args, "command", None) and args.command[0] == "--":
        args.command = args.command[1:]
    try:
        outcome = args.handler(args)
        return int(outcome or 0)
    except (TransactionError, OSError) as error:
        print(f"release-index transaction blocked: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
