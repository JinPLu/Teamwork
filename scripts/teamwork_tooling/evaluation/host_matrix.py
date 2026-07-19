"""Candidate-isolated installed-host trajectories for Teamwork v4.

This module deliberately treats a host transcript as evidence, not as a
declaration.  A successful record therefore has three independently checkable
things: a frozen candidate tree, an actual host/tool trace, and a case-specific
artifact produced in a disposable scenario copied from that tree.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import tarfile
import tempfile
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterator, Sequence

from .contracts import CANONICAL_ROLES

SCHEMA_VERSION = 4
STATUSES = {"PASS", "FAIL", "UNSUPPORTED"}
PROFILES = {"performance-first", "cost-first"}
HOSTS = {"codex", "cursor", "claude"}
OBJECT_ID_RE = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
RELEASE_PATHS_NAME = "v4-release-paths.json"
RELEASE_CASE_PATH = "evals/teamwork/live-cases/v4-release-matrix.json"
RELEASE_SCHEMA_PATH = "evals/teamwork/schemas/host-trajectory-v4.schema.json"
STRUCTURAL_EVENT_TYPES = {
    "thread.started", "thread.resumed", "thread.completed",
    "subagent.start", "subagent.started", "subagent.stop", "subagent.completed",
    "SubagentStart", "SubagentStop", "agent.started", "agent.completed",
    "tool_call", "tool_result", "tool_use", "assistant.tool_use", "tool.call", "tool.result",
    "item.completed", "item.started",
}
GENERIC_OBSERVATIONS = {
    "", "unknown", "unobserved", "observed-model", "observed-effort",
    "host-observed", "host-default", "x", "n/a", "none", "null",
}
TRAJECTORY_FIELDS = {
    "schema_version", "record_type", "host", "host_version", "invocation_id",
    "started_at", "finished_at", "case_id", "profile", "selected_skill",
    "role_identity", "roles_observed", "actual_model", "actual_effort",
    "tool_observations", "authority_observation", "sanitized_input_sha256",
    "artifact", "result", "exit_status", "status", "privacy_scan",
    "failure_classification",
}


class HostMatrixError(ValueError):
    """Raised when candidate or trajectory evidence is invalid."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _candidate_fingerprint(value: dict[str, Any]) -> str:
    payload = {
        "scope_revision": value.get("scope_revision"),
        "candidate_id": value.get("candidate_id"),
        "candidate_tree_oid": value.get("candidate_tree_oid"),
        "repair_generation": value.get("repair_generation"),
        "base_commit": value.get("base_commit"),
        "paths_manifest_sha256": value.get("paths_manifest_sha256"),
        "entries": value.get("entries"),
    }
    data = (json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()
    return sha256_bytes(data)


def _absolute_path(path: Path) -> Path:
    """Normalize `.`/`..` without following caller-controlled filesystem links."""

    absolute = Path(os.path.abspath(os.fspath(path)))
    # macOS exposes normal temporary paths through /var -> /private/var. This
    # fixed OS alias is not a caller-selected component; canonicalize it before
    # enforcing the no-link invariant for every remaining component.
    if absolute.parts[:2] == ("/", "var") and os.path.realpath("/var") == "/private/var":
        return Path("/private/var").joinpath(*absolute.parts[2:])
    return absolute


def _checked_directory(path: Path, label: str) -> Path:
    """Return an existing directory only after rejecting every symlink component."""

    absolute = _absolute_path(path)
    current = Path(absolute.anchor)
    try:
        root_info = current.lstat()
    except OSError as exc:
        raise HostMatrixError(f"{label} root is unavailable: {current}: {exc}") from exc
    if stat.S_ISLNK(root_info.st_mode) or not stat.S_ISDIR(root_info.st_mode):
        raise HostMatrixError(f"{label} root must be a non-symlink directory")
    for part in absolute.parts[1:]:
        current /= part
        try:
            info = current.lstat()
        except OSError as exc:
            raise HostMatrixError(f"{label} directory is unavailable: {current}: {exc}") from exc
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            raise HostMatrixError(f"{label} directory must not contain a symlink: {current}")
    return absolute


def _relative_under(root: Path, path: Path, label: str) -> str:
    """Return a lexical, package-relative child path without dereferencing it."""

    raw = Path(path)
    if raw.is_absolute():
        absolute = _absolute_path(raw)
        try:
            relative = absolute.relative_to(root)
        except ValueError as exc:
            raise HostMatrixError(f"{label} must be inside project root: {path}") from exc
        return safe_relative(relative.as_posix(), label)
    return safe_relative(raw.as_posix(), label)


def _child(root: Path, relative: str, label: str) -> Path:
    """Build a child path while refusing a link in any existing component."""

    root = _checked_directory(root, f"{label} root")
    pure = PurePosixPath(safe_relative(relative, label))
    current = root
    for part in pure.parts[:-1]:
        current /= part
        try:
            info = current.lstat()
        except FileNotFoundError:
            return root.joinpath(*pure.parts)
        except OSError as exc:
            raise HostMatrixError(f"cannot inspect {label} parent {current}: {exc}") from exc
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            raise HostMatrixError(f"{label} parent must be a non-symlink directory: {current}")
    path = current / pure.name
    try:
        info = path.lstat()
    except FileNotFoundError:
        return path
    except OSError as exc:
        raise HostMatrixError(f"cannot inspect {label}: {path}: {exc}") from exc
    if stat.S_ISLNK(info.st_mode):
        raise HostMatrixError(f"{label} must not be a symlink: {path}")
    return path


def _regular_child(root: Path, relative: str, label: str) -> Path:
    path = _child(root, relative, label)
    try:
        info = path.lstat()
    except OSError as exc:
        raise HostMatrixError(f"{label} is unavailable: {path}: {exc}") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise HostMatrixError(f"{label} must be a single-link regular non-symlink file: {path}")
    return path


def _ensure_absolute_directory(path: Path, label: str) -> Path:
    """Create a directory path one component at a time without accepting links."""

    absolute = _absolute_path(path)
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        try:
            info = current.lstat()
        except FileNotFoundError:
            try:
                current.mkdir(mode=0o700)
                info = current.lstat()
            except OSError as exc:
                raise HostMatrixError(f"cannot create {label} directory {current}: {exc}") from exc
        except OSError as exc:
            raise HostMatrixError(f"cannot inspect {label} directory {current}: {exc}") from exc
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            raise HostMatrixError(f"{label} directory must not contain a symlink: {current}")
    return absolute


def _prepare_output_path(root: Path, relative: str) -> Path:
    pure = PurePosixPath(safe_relative(relative, "installed output"))
    parent = _ensure_absolute_directory(root.joinpath(*pure.parts[:-1]), "installed output")
    path = parent / pure.name
    try:
        info = path.lstat()
    except FileNotFoundError:
        return path
    except OSError as exc:
        raise HostMatrixError(f"cannot inspect installed output {path}: {exc}") from exc
    if stat.S_ISLNK(info.st_mode):
        raise HostMatrixError(f"installed output must not be a symlink: {path}")
    raise HostMatrixError(f"output already exists: {path}")


def _read_regular_bytes(path: Path, label: str) -> bytes:
    """Read one checked regular file without following a final symlink."""

    try:
        before = path.lstat()
    except OSError as exc:
        raise HostMatrixError(f"cannot inspect {label} {path}: {exc}") from exc
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        raise HostMatrixError(f"{label} must be a single-link regular non-symlink file: {path}")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise HostMatrixError(f"cannot safely open {label} {path}: {exc}") from exc
    try:
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_nlink != 1
            or (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino)
        ):
            raise HostMatrixError(f"{label} changed identity while opening: {path}")
        chunks: list[bytes] = []
        while chunk := os.read(descriptor, 1024 * 1024):
            chunks.append(chunk)
        final = os.fstat(descriptor)
        if (final.st_dev, final.st_ino) != (opened.st_dev, opened.st_ino):
            raise HostMatrixError(f"{label} changed identity while reading: {path}")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def sha256_file(path: Path) -> str:
    return sha256_bytes(_read_regular_bytes(path, "file"))


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(_read_regular_bytes(path, label).decode("utf-8"))
    except (HostMatrixError, UnicodeError, json.JSONDecodeError) as exc:
        raise HostMatrixError(f"cannot read {label} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise HostMatrixError(f"{label} {path} must be a JSON object")
    return value


def _sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        raise HostMatrixError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _object_id(value: Any, label: str) -> str:
    if not isinstance(value, str) or not OBJECT_ID_RE.fullmatch(value):
        raise HostMatrixError(f"{label} must be a full lowercase Git object id")
    return value


def safe_relative(value: Any, label: str = "path") -> str:
    if not isinstance(value, str) or not value or any(char in value for char in ("\x00", "\n", "\r", "\t")):
        raise HostMatrixError(f"invalid {label}")
    candidate = PurePosixPath(value)
    if candidate.is_absolute() or any(part in {"", ".", ".."} for part in candidate.parts):
        raise HostMatrixError(f"unsafe {label}: {value!r}")
    return candidate.as_posix()


def _inside(root: Path, path: Path, label: str) -> Path:
    root = _checked_directory(root, "project root")
    return _child(root, _relative_under(root, path, label), label)


def _git(project_root: Path, *arguments: str, text: bool = True) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(
        ["git", "-C", str(project_root), *arguments], text=text,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )


def _canonical_commit(project_root: Path, value: str) -> str:
    resolved = _git(project_root, "rev-parse", f"{value}^{{commit}}")
    if resolved.returncode or resolved.stdout.strip() != value:
        raise HostMatrixError("base_commit must resolve to its exact immutable commit id")
    return value


def _canonical_tree(project_root: Path, value: str) -> str:
    resolved = _git(project_root, "rev-parse", f"{value}^{{tree}}")
    if resolved.returncode or resolved.stdout.strip() != value:
        raise HostMatrixError("candidate_tree_oid must resolve to its exact immutable tree id")
    return value


def _parse_raw_diff(raw: bytes) -> list[dict[str, Any]]:
    fields = raw.split(b"\0")
    if fields and fields[-1] == b"":
        fields.pop()
    result: list[dict[str, Any]] = []
    index = 0
    while index < len(fields):
        try:
            header = fields[index].decode("ascii")
        except UnicodeDecodeError as exc:
            raise HostMatrixError("candidate raw diff has a non-ASCII header") from exc
        index += 1
        parts = header.split()
        if len(parts) != 5 or not parts[0].startswith(":"):
            raise HostMatrixError("candidate raw diff is malformed")
        status = parts[4][:1]
        if status not in {"A", "M", "D", "R"} or index >= len(fields):
            raise HostMatrixError("candidate raw diff has an unsupported status")
        try:
            first = safe_relative(fields[index].decode("utf-8"), "candidate delta path")
        except UnicodeDecodeError as exc:
            raise HostMatrixError("candidate raw diff has a non-UTF-8 path") from exc
        index += 1
        item: dict[str, Any] = {
            "status": status,
            "mode_before": None if parts[0][1:] == "000000" else parts[0][1:],
            "mode_after": None if parts[1] == "000000" else parts[1],
            "blob_oid_before": None if parts[2] == "0" * len(parts[2]) else parts[2],
            "blob_oid_after": None if parts[3] == "0" * len(parts[3]) else parts[3],
            "path": first,
        }
        if status == "R":
            if index >= len(fields):
                raise HostMatrixError("candidate rename has no destination")
            try:
                item["old_path"] = first
                item["path"] = safe_relative(fields[index].decode("utf-8"), "candidate rename destination")
            except UnicodeDecodeError as exc:
                raise HostMatrixError("candidate rename has a non-UTF-8 path") from exc
            index += 1
        result.append(item)
    return result


def _tree_diff(project_root: Path, base: str, tree: str) -> list[dict[str, Any]]:
    completed = _git(
        project_root, "diff-tree", "--no-commit-id", "-r", "--raw", "--full-index",
        "--find-renames", "-z", base, tree, text=False,
    )
    if completed.returncode:
        raise HostMatrixError("cannot compare candidate tree to base commit")
    result = _parse_raw_diff(completed.stdout)
    for item in result:
        if item["status"] == "D":
            item["sha256_after"] = None
            continue
        blob = item["blob_oid_after"]
        if not isinstance(blob, str):
            raise HostMatrixError("candidate post-image lacks a blob id")
        data = _git(project_root, "cat-file", "blob", blob, text=False)
        if data.returncode:
            raise HostMatrixError("candidate post-image blob is unavailable")
        item["sha256_after"] = sha256_bytes(data.stdout)
    return result


def _validate_paths_manifest(value: dict[str, Any], base_commit: str) -> dict[str, dict[str, Any]]:
    if value.get("schema_version") != 1 or value.get("base_commit") != base_commit:
        raise HostMatrixError("release paths manifest schema/base binding is invalid")
    entries = value.get("entries")
    if not isinstance(entries, list) or not entries:
        raise HostMatrixError("release paths manifest must contain non-empty entries")
    paths: list[str] = []
    ledger_ids: set[str] = set()
    result: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise HostMatrixError("release paths manifest entry must be an object")
        ledger_id = entry.get("ledger_id")
        owner = entry.get("owner")
        path = safe_relative(entry.get("path"), "release path")
        allowed = entry.get("allowed_statuses")
        if not isinstance(ledger_id, str) or not ledger_id or ledger_id in ledger_ids:
            raise HostMatrixError("release paths manifest has duplicate or invalid ledger_id")
        if not isinstance(owner, str) or not owner:
            raise HostMatrixError("release paths manifest owner is invalid")
        if not isinstance(allowed, list) or not allowed or len(allowed) != len(set(allowed)) or any(status not in {"A", "M", "D", "R"} for status in allowed):
            raise HostMatrixError(f"release paths manifest has invalid allowed_statuses for {path}")
        if entry.get("old_path") is not None:
            safe_relative(entry["old_path"], "release rename old_path")
            if "R" not in allowed:
                raise HostMatrixError(f"release paths manifest has a rename source without R status: {path}")
        elif "R" in allowed:
            raise HostMatrixError(f"release paths manifest R status lacks old_path: {path}")
        paths.append(path)
        ledger_ids.add(ledger_id)
        result[path] = entry
    if paths != sorted(paths, key=lambda item: item.encode("utf-8")) or len(paths) != len(set(paths)):
        raise HostMatrixError("release paths manifest entries must be unique UTF-8 sorted")
    return result


def _validate_candidate_entries(
    entries: Any, allowlist: dict[str, dict[str, Any]], observed: list[dict[str, Any]],
) -> None:
    if not isinstance(entries, list) or not entries:
        raise HostMatrixError("candidate manifest entries must be a non-empty list")
    paths: list[str] = []
    ledger_ids: set[str] = set()
    observed_by_path = {entry["path"]: entry for entry in observed}
    if len(observed_by_path) != len(observed):
        raise HostMatrixError("candidate tree contains duplicate deltas")
    for entry in entries:
        if not isinstance(entry, dict):
            raise HostMatrixError("candidate manifest entry must be an object")
        required = {
            "ledger_id", "owner", "path", "status", "mode_before", "mode_after",
            "blob_oid_before", "blob_oid_after", "sha256_after",
        }
        if required - set(entry):
            raise HostMatrixError("candidate manifest entry lacks typed post-image fields")
        ledger_id = entry.get("ledger_id")
        owner = entry.get("owner")
        path = safe_relative(entry.get("path"), "candidate path")
        status = entry.get("status")
        rule = allowlist.get(path)
        if not isinstance(ledger_id, str) or not ledger_id or ledger_id in ledger_ids:
            raise HostMatrixError("candidate manifest has duplicate or invalid ledger_id")
        if not isinstance(owner, str) or not owner or rule is None:
            raise HostMatrixError(f"candidate manifest contains an unlisted path: {path}")
        if ledger_id != rule.get("ledger_id") or owner != rule.get("owner"):
            raise HostMatrixError(f"candidate manifest ledger/owner binding differs for {path}")
        if status not in rule.get("allowed_statuses", []):
            raise HostMatrixError(f"candidate manifest status is not allowed for {path}")
        if status == "R":
            if safe_relative(entry.get("old_path"), "candidate rename old_path") != rule.get("old_path"):
                raise HostMatrixError(f"candidate rename source differs for {path}")
        elif entry.get("old_path") is not None:
            raise HostMatrixError(f"non-rename candidate entry has old_path: {path}")
        if status == "D":
            if any(entry.get(key) is not None for key in ("mode_after", "blob_oid_after", "sha256_after")):
                raise HostMatrixError(f"deletion has a post-image: {path}")
        else:
            _sha256(entry.get("sha256_after"), f"candidate post-image hash for {path}")
            if entry.get("mode_after") not in {"100644", "100755"}:
                raise HostMatrixError(f"candidate post-image mode is invalid for {path}")
            _object_id(entry.get("blob_oid_after"), f"candidate post-image blob for {path}")
        actual = observed_by_path.get(path)
        if actual is None:
            raise HostMatrixError(f"candidate manifest path has no tree delta: {path}")
        for key in ("status", "mode_before", "mode_after", "blob_oid_before", "blob_oid_after", "sha256_after"):
            if entry.get(key) != actual.get(key):
                raise HostMatrixError(f"candidate manifest {key} does not bind tree delta for {path}")
        if entry.get("old_path") != actual.get("old_path"):
            raise HostMatrixError(f"candidate manifest rename does not bind tree delta for {path}")
        paths.append(path)
        ledger_ids.add(ledger_id)
    if paths != sorted(paths, key=lambda item: item.encode("utf-8")) or len(paths) != len(set(paths)):
        raise HostMatrixError("candidate entries must be unique UTF-8 sorted")
    if set(paths) != set(allowlist) or set(paths) != set(observed_by_path):
        raise HostMatrixError("candidate entries must exactly bind allowlist and candidate tree deltas")


def validate_candidate(project_root: Path, manifest_path: Path) -> dict[str, Any]:
    """Fail closed unless candidate, allowlist and Git tree agree byte-for-byte."""

    project_root = _checked_directory(project_root, "project root")
    manifest_relative = _relative_under(project_root, manifest_path, "candidate manifest")
    manifest_path = _regular_child(project_root, manifest_relative, "candidate manifest")
    value = load_json(manifest_path, "candidate manifest")
    required = {
        "schema_version", "state", "base_commit", "candidate_tree_oid",
        "scope_revision", "candidate_id", "repair_generation", "predecessor_candidate_id",
        "paths_manifest_sha256", "candidate_fingerprint", "sealed_manifest_sha256",
        "validation_artifact_sha256", "review_artifact_sha256", "review_verdict", "writer_leases",
        "real_index_prestate", "protected_preimages", "entries",
    }
    if value.get("schema_version") != 1 or required - set(value):
        raise HostMatrixError("candidate manifest has unsupported schema")
    if value.get("state") not in {"sealed", "validated", "reviewed"}:
        raise HostMatrixError("host matrix requires a sealed candidate")
    _sha256(value.get("scope_revision"), "scope_revision")
    candidate_id = value.get("candidate_id")
    if not isinstance(candidate_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", candidate_id):
        raise HostMatrixError("candidate_id must be an explicit stable identifier")
    if type(value.get("repair_generation")) is not int or value["repair_generation"] not in {0, 1}:
        raise HostMatrixError("repair_generation must be 0 or 1")
    if value["repair_generation"] == 0 and value.get("predecessor_candidate_id") is not None:
        raise HostMatrixError("initial candidate must not name a predecessor")
    if value["repair_generation"] == 1 and not isinstance(value.get("predecessor_candidate_id"), str):
        raise HostMatrixError("repair candidate must name a predecessor")
    if value.get("writer_leases") != []:
        raise HostMatrixError("sealed candidate must not retain writer leases")
    if not isinstance(value.get("real_index_prestate"), dict) or not isinstance(value.get("protected_preimages"), list):
        raise HostMatrixError("candidate manifest lacks typed transaction prestate")
    for protected in value["protected_preimages"]:
        if not isinstance(protected, dict) or not isinstance(protected.get("path"), str) or not protected["path"].endswith("/**"):
            raise HostMatrixError("candidate manifest has malformed protected preimage")
        safe_relative(protected["path"][:-3], "protected preimage root")
        _sha256(protected.get("sha256"), "protected preimage hash")
    base = _canonical_commit(project_root, _object_id(value.get("base_commit"), "base_commit"))
    tree = _canonical_tree(project_root, _object_id(value.get("candidate_tree_oid"), "candidate_tree_oid"))
    paths_sha = _sha256(value.get("paths_manifest_sha256"), "paths_manifest_sha256")
    for field in ("candidate_fingerprint", "sealed_manifest_sha256"):
        _sha256(value.get(field), field)
    for field in ("validation_artifact_sha256", "review_artifact_sha256"):
        if value.get(field) is not None:
            _sha256(value[field], field)
    paths_relative = "/".join((*PurePosixPath(manifest_relative).parts[:-1], RELEASE_PATHS_NAME))
    paths_path = _regular_child(project_root, paths_relative, "release paths manifest")
    if sha256_file(paths_path) != paths_sha:
        raise HostMatrixError("paths-manifest-changed")
    allowlist = _validate_paths_manifest(load_json(paths_path, "release paths manifest"), base)
    observed = _tree_diff(project_root, base, tree)
    _validate_candidate_entries(value.get("entries"), allowlist, observed)
    if value["candidate_fingerprint"] != _candidate_fingerprint(value):
        raise HostMatrixError("candidate-fingerprint-changed")
    return value


def _validate_archive_member(member: tarfile.TarInfo) -> None:
    safe_relative(member.name.rstrip("/"), "candidate archive member")
    if member.isdir() or member.isfile():
        return
    if member.issym() or member.islnk():
        raise HostMatrixError(f"candidate archive must not contain a link: {member.name}")
    raise HostMatrixError(f"unsupported candidate archive member: {member.name}")


def _validate_materialized_postimages(tree_root: Path, entries: list[dict[str, Any]]) -> None:
    for entry in entries:
        path = _child(tree_root, entry["path"], "candidate post-image")
        if entry["status"] == "D":
            if path.exists() or path.is_symlink():
                raise HostMatrixError(f"deleted candidate path returned: {entry['path']}")
            continue
        try:
            info = path.lstat()
        except OSError as exc:
            raise HostMatrixError(f"candidate post-image missing: {entry['path']}") from exc
        mode = entry["mode_after"]
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode) or mode not in {"100644", "100755"}:
            raise HostMatrixError(f"candidate post-image mode changed: {entry['path']}")
        executable = bool(stat.S_IMODE(info.st_mode) & 0o111)
        if executable != (mode == "100755"):
            raise HostMatrixError(f"candidate post-image executable bit changed: {entry['path']}")
        content = _read_regular_bytes(path, "candidate post-image")
        if sha256_bytes(content) != entry["sha256_after"]:
            raise HostMatrixError(f"candidate post-image mismatch: {entry['path']}")


def _validate_materialized_tree(tree_root: Path) -> None:
    """Ensure no archive entry can become an external path during scenario copy."""

    for parent, directories, files in os.walk(tree_root, followlinks=False):
        parent_path = Path(parent)
        try:
            parent_info = parent_path.lstat()
        except OSError as exc:
            raise HostMatrixError(f"cannot inspect materialized candidate directory: {exc}") from exc
        if stat.S_ISLNK(parent_info.st_mode) or not stat.S_ISDIR(parent_info.st_mode):
            raise HostMatrixError(f"candidate archive contains an unsafe directory: {parent_path}")
        for name in [*directories, *files]:
            path = parent_path / name
            try:
                info = path.lstat()
            except OSError as exc:
                raise HostMatrixError(f"cannot inspect materialized candidate path: {exc}") from exc
            if stat.S_ISLNK(info.st_mode):
                raise HostMatrixError(f"candidate archive contains a symlink: {path.relative_to(tree_root)}")
            if name in directories and not stat.S_ISDIR(info.st_mode):
                raise HostMatrixError(f"candidate archive directory changed type: {path.relative_to(tree_root)}")
            if name in files and (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1):
                raise HostMatrixError(f"candidate archive contains an unsafe file: {path.relative_to(tree_root)}")


@contextmanager
def materialize_candidate(project_root: Path, manifest: dict[str, Any]) -> Iterator[Path]:
    """Extract only the immutable candidate tree into a private directory."""

    project_root = _checked_directory(project_root, "project root")
    temporary = Path(tempfile.mkdtemp(prefix="teamwork-v4-candidate-"))
    archive = temporary / "candidate.tar"
    tree_root = temporary / "tree"
    tree_root.mkdir(mode=0o700)
    try:
        with archive.open("wb") as handle:
            completed = _git(project_root, "archive", manifest["candidate_tree_oid"], text=False)
            if completed.returncode:
                raise HostMatrixError("cannot archive candidate tree")
            handle.write(completed.stdout)
        with tarfile.open(archive, "r") as bundle:
            members = bundle.getmembers()
            for member in members:
                _validate_archive_member(member)
            for member in members:
                bundle.extract(member, tree_root, set_attrs=True, numeric_owner=False, filter="data")
        _validate_materialized_tree(tree_root)
        _validate_materialized_postimages(tree_root, manifest["entries"])
        yield tree_root
    finally:
        shutil.rmtree(temporary, ignore_errors=True)


def _events(stdout: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for line in stdout.splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            result.append(value)
    return result


def _walk(value: Any) -> Iterator[tuple[str, Any]]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield key, child
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _event_type(event: dict[str, Any]) -> str:
    value = event.get("type")
    return value if isinstance(value, str) else ""


def _structural_events(events: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    return [event for event in events if _event_type(event) in STRUCTURAL_EVENT_TYPES]


def observed_values(events: Sequence[dict[str, Any]], keys: set[str]) -> list[str]:
    normalized_keys = {key.casefold().replace("_", "-") for key in keys}
    values: list[str] = []
    for event in _structural_events(events):
        for key, value in _walk(event):
            if key.casefold().replace("_", "-") in normalized_keys and isinstance(value, str) and value.strip():
                normalized = value.strip().casefold().replace("_", "-")
                if normalized not in values:
                    values.append(normalized)
    return values


def normalize_roles(values: Sequence[str]) -> list[str]:
    roles: list[str] = []
    for value in values:
        candidate = value.removeprefix("teamwork-")
        if candidate in CANONICAL_ROLES and candidate not in roles:
            roles.append(candidate)
    return roles


def observed_tools(events: Sequence[dict[str, Any]]) -> list[str]:
    """Return actual tool event kinds; never promote arbitrary JSON `type` fields."""

    tools: list[str] = []
    for event in _structural_events(events):
        event_type = _event_type(event)
        item = event.get("item") if isinstance(event.get("item"), dict) else event
        item_type = item.get("type") if isinstance(item, dict) else None
        name = ""
        if isinstance(item_type, str) and item_type in {
            "command_execution", "web_search", "web_fetch", "file_read", "file_write", "mcp_tool_call",
        }:
            name = item_type
        elif event_type in {"tool_call", "tool_result", "tool_use", "assistant.tool_use", "tool.call", "tool.result"}:
            candidate = item.get("tool_name") if isinstance(item, dict) else None
            candidate = candidate or event.get("tool_name") or event.get("name")
            if isinstance(candidate, str) and candidate.strip():
                raw = candidate.strip().casefold().replace("_", "-")
                aliases = {
                    "websearch": "web_search", "web-search": "web_search",
                    "webfetch": "web_fetch", "web-fetch": "web_fetch",
                    "bash": "command_execution", "shell": "command_execution", "command": "command_execution",
                    "read": "file_read", "grep": "file_read", "glob": "file_read",
                    "write": "file_write", "edit": "file_write",
                }
                name = aliases.get(raw, f"tool:{raw}")
        if name and name not in tools:
            tools.append(name)
    return tools


def _case_profile_expectation(case: dict[str, Any], host: str, profile: str) -> dict[str, str]:
    profile_matrix = case.get("role_expectations")
    role = case.get("required_role")
    try:
        expected = profile_matrix[host][profile][role]
    except (KeyError, TypeError) as exc:
        raise HostMatrixError(f"case {case.get('id')} lacks {host}/{profile}/{role} role expectation") from exc
    if not isinstance(expected, dict) or set(expected) != {"model", "effort"}:
        raise HostMatrixError(f"case {case.get('id')} has malformed role expectation")
    model, effort = expected.get("model"), expected.get("effort")
    if not isinstance(model, str) or not model or not isinstance(effort, str) or not effort:
        raise HostMatrixError(f"case {case.get('id')} has empty model/effort expectation")
    return {"model": model.casefold(), "effort": effort.casefold()}


def _validate_scenario_spec(value: dict[str, Any], case: dict[str, Any]) -> None:
    if value.get("schema_version") != 1 or value.get("case_id") != case["id"]:
        raise HostMatrixError(f"scenario fixture does not bind case {case['id']}")
    allowed_fields = {"schema_version", "case_id", "private_paths", "files", "verification"}
    if set(value) - allowed_fields:
        raise HostMatrixError(f"scenario fixture {case['id']} has unsupported fields")
    files = value.get("files")
    if not isinstance(files, list) or not files:
        raise HostMatrixError(f"scenario fixture {case['id']} needs concrete setup files")
    paths: set[str] = set()
    content_by_path: dict[str, str] = {}
    for item in files:
        if not isinstance(item, dict) or set(item) != {"path", "content"}:
            raise HostMatrixError(f"scenario fixture {case['id']} has malformed setup file")
        path = safe_relative(item.get("path"), "scenario setup path")
        if path in paths or not isinstance(item.get("content"), str):
            raise HostMatrixError(f"scenario fixture {case['id']} has duplicate or non-text setup")
        paths.add(path)
        content_by_path[path] = item["content"]
    evidence = case["evidence"]
    artifact_path = safe_relative(evidence["artifact_path"], "case artifact_path")
    if evidence["kind"] == "workspace" and artifact_path not in paths:
        raise HostMatrixError(f"workspace case {case['id']} must seed its concrete artifact path")
    if evidence["kind"] == "workspace" and any(marker in content_by_path[artifact_path] for marker in evidence["markers"]):
        raise HostMatrixError(f"workspace case {case['id']} pre-seeds its own success evidence")
    verification = value.get("verification")
    if evidence["kind"] == "workspace":
        if not isinstance(verification, dict) or set(verification) != {"argv", "immutable_paths"}:
            raise HostMatrixError(f"workspace case {case['id']} needs a concrete verifier contract")
        argv = verification.get("argv")
        immutable = verification.get("immutable_paths")
        if not isinstance(argv, list) or len(argv) < 2 or argv[0] not in {"python3", "sh", "bash"} or not all(isinstance(arg, str) and arg for arg in argv):
            raise HostMatrixError(f"workspace case {case['id']} has invalid verifier argv")
        if safe_relative(argv[1], "scenario verifier path") not in paths:
            raise HostMatrixError(f"workspace case {case['id']} verifier is not candidate-tracked setup")
        if not isinstance(immutable, list) or not immutable or not all(safe_relative(item, "immutable verifier path") in paths for item in immutable):
            raise HostMatrixError(f"workspace case {case['id']} has invalid immutable verifier paths")
        if artifact_path in immutable:
            raise HostMatrixError(f"workspace case {case['id']} makes its result artifact immutable")
    elif verification is not None:
        raise HostMatrixError(f"trace case {case['id']} must not declare a workspace verifier")
    private_paths = value.get("private_paths", [])
    if not isinstance(private_paths, list) or not all(safe_relative(path, "private scenario path") in paths for path in private_paths):
        raise HostMatrixError(f"scenario fixture {case['id']} has invalid private_paths")


def load_case_manifest(path: Path, only_cases: set[str] | None = None, *, root: Path | None = None) -> list[dict[str, Any]]:
    """Load a matrix manifest and all scenario fixtures from one candidate tree."""

    raw_path = Path(path)
    default_root = _absolute_path(raw_path).parents[3]
    root = _checked_directory(root or default_root, "case manifest root")
    path = _regular_child(root, _relative_under(root, raw_path, "case manifest"), "case manifest")
    value = load_json(path, "case manifest")
    if value.get("schema_version") != SCHEMA_VERSION:
        raise HostMatrixError("case manifest must use schema_version 4")
    required_roles = value.get("required_roles_per_slice")
    if not isinstance(required_roles, list) or set(required_roles) != CANONICAL_ROLES:
        raise HostMatrixError("case manifest must require every canonical role per slice")
    role_expectations = value.get("role_expectations")
    if not isinstance(role_expectations, dict):
        raise HostMatrixError("case manifest must bind every host/profile/role expectation")
    expectation_probe = {"role_expectations": role_expectations, "required_role": "worker", "id": "matrix"}
    for host in HOSTS:
        for profile in PROFILES:
            for role in CANONICAL_ROLES:
                expectation_probe["required_role"] = role
                _case_profile_expectation(expectation_probe, host, profile)
    cases = value.get("cases")
    if not isinstance(cases, list) or len(cases) != 12:
        raise HostMatrixError("case manifest must contain exactly twelve cases")
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            raise HostMatrixError("every release-matrix case must be an object")
        required = {
            "id", "selected_skill", "required_role", "expected_roles",
            "authority", "required_tools", "scenario", "evidence", "prompt", "private_markers",
        }
        if required - set(case):
            raise HostMatrixError("release-matrix case lacks evidence-binding fields")
        case_id = case.get("id")
        prompt = case.get("prompt")
        roles = case.get("expected_roles")
        if not isinstance(case_id, str) or not case_id or case_id in seen:
            raise HostMatrixError("release-matrix case ids must be unique non-empty strings")
        if not isinstance(prompt, str) or not prompt.strip():
            raise HostMatrixError(f"case {case_id} needs a non-empty prompt")
        if not isinstance(case.get("selected_skill"), str) or not case["selected_skill"]:
            raise HostMatrixError(f"case {case_id} needs a selected_skill")
        if case.get("required_role") not in CANONICAL_ROLES:
            raise HostMatrixError(f"case {case_id} has invalid required_role")
        if not isinstance(roles, list) or not roles or not set(roles) <= CANONICAL_ROLES or case["required_role"] not in roles:
            raise HostMatrixError(f"case {case_id} has invalid expected_roles")
        if case.get("authority") not in {"read-only", "workspace-write"}:
            raise HostMatrixError(f"case {case_id} has invalid authority")
        tools = case.get("required_tools")
        if not isinstance(tools, list) or not tools or not all(isinstance(tool, str) and tool for tool in tools):
            raise HostMatrixError(f"case {case_id} has invalid required_tools")
        markers = case.get("private_markers")
        if not isinstance(markers, list) or not all(isinstance(marker, str) and marker for marker in markers):
            raise HostMatrixError(f"case {case_id} has invalid private_markers")
        evidence = case.get("evidence")
        if not isinstance(evidence, dict) or set(evidence) != {"kind", "artifact_path", "markers"}:
            raise HostMatrixError(f"case {case_id} has malformed evidence contract")
        if evidence.get("kind") not in {"workspace", "trace"}:
            raise HostMatrixError(f"case {case_id} evidence kind must be workspace or trace")
        if not isinstance(evidence.get("markers"), list) or not evidence["markers"] or not all(isinstance(item, str) and item for item in evidence["markers"]):
            raise HostMatrixError(f"case {case_id} needs non-empty direct evidence markers")
        safe_relative(evidence.get("artifact_path"), "case artifact_path")
        forbidden = list(markers) + list(evidence["markers"])
        if any(marker in prompt for marker in forbidden):
            raise HostMatrixError(f"case {case_id} prompt must not contain private or evidence markers")
        case = {**case, "role_expectations": role_expectations}
        _case_profile_expectation(case, "codex", "performance-first")
        for host in HOSTS:
            for profile in PROFILES:
                _case_profile_expectation(case, host, profile)
        scenario_path = _regular_child(root, safe_relative(case.get("scenario"), "case scenario"), "case scenario")
        _validate_scenario_spec(load_json(scenario_path, "scenario fixture"), case)
        seen.add(case_id)
        if only_cases is None or case_id in only_cases:
            result.append(case)
    if only_cases is not None and seen & only_cases != only_cases:
        raise HostMatrixError(f"unknown --only-cases values: {sorted(only_cases - seen)}")
    return result


def load_trajectory_schema(path: Path) -> dict[str, Any]:
    schema = load_json(path, "trajectory schema")
    properties = schema.get("properties")
    version_schema = properties.get("schema_version") if isinstance(properties, dict) else None
    record_type_schema = properties.get("record_type") if isinstance(properties, dict) else None
    if (
        schema.get("$id") != "https://teamwork.example/schemas/host-trajectory-v4.schema.json"
        or schema.get("type") != "object" or schema.get("additionalProperties") is not False
        or not isinstance(schema.get("required"), list) or set(schema["required"]) != TRAJECTORY_FIELDS
        or not isinstance(properties, dict) or set(properties) != TRAJECTORY_FIELDS
        or not isinstance(version_schema, dict) or version_schema.get("const") != SCHEMA_VERSION
        or not isinstance(record_type_schema, dict) or record_type_schema.get("const") != "teamwork_host_trajectory_v4"
    ):
        raise HostMatrixError("trajectory schema does not preserve the v4 record contract")
    return schema


def _schema_error(value: Any, schema: dict[str, Any], root: dict[str, Any], location: str = "record") -> None:
    if "$ref" in schema:
        ref = schema["$ref"]
        if not isinstance(ref, str) or not ref.startswith("#/$defs/"):
            raise HostMatrixError(f"{location}: unsupported schema reference")
        name = ref.rsplit("/", 1)[-1]
        target = root.get("$defs", {}).get(name)
        if not isinstance(target, dict):
            raise HostMatrixError(f"{location}: missing schema definition {name}")
        _schema_error(value, target, root, location)
    for branch in schema.get("allOf", []):
        if not isinstance(branch, dict):
            raise HostMatrixError(f"{location}: malformed allOf schema")
        _schema_error(value, branch, root, location)
    if "const" in schema and value != schema["const"]:
        raise HostMatrixError(f"{location}: must equal {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        raise HostMatrixError(f"{location}: value is outside schema enum")
    expected = schema.get("type")
    if expected is not None:
        candidates = expected if isinstance(expected, list) else [expected]
        checks = {
            "object": lambda item: isinstance(item, dict),
            "array": lambda item: isinstance(item, list),
            "string": lambda item: isinstance(item, str),
            "integer": lambda item: isinstance(item, int) and not isinstance(item, bool),
            "boolean": lambda item: isinstance(item, bool),
            "null": lambda item: item is None,
        }
        if not any(checks.get(kind, lambda _item: False)(value) for kind in candidates):
            raise HostMatrixError(f"{location}: schema type mismatch")
    if isinstance(value, str):
        if isinstance(schema.get("minLength"), int) and len(value) < schema["minLength"]:
            raise HostMatrixError(f"{location}: schema minimum length failed")
        if isinstance(schema.get("pattern"), str) and re.fullmatch(schema["pattern"], value) is None:
            raise HostMatrixError(f"{location}: schema pattern failed")
    if isinstance(value, list):
        if schema.get("uniqueItems") and len(value) != len({json.dumps(item, sort_keys=True) for item in value}):
            raise HostMatrixError(f"{location}: schema uniqueItems failed")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                _schema_error(item, item_schema, root, f"{location}[{index}]")
    if isinstance(value, dict):
        required = schema.get("required", [])
        if isinstance(required, list):
            missing = [key for key in required if key not in value]
            if missing:
                raise HostMatrixError(f"{location}: schema missing fields: {', '.join(missing)}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            unknown = set(value) - set(properties)
            if unknown:
                raise HostMatrixError(f"{location}: schema forbids fields: {', '.join(sorted(unknown))}")
        if isinstance(properties, dict):
            for key, child_schema in properties.items():
                if key in value and isinstance(child_schema, dict):
                    _schema_error(value[key], child_schema, root, f"{location}.{key}")


def validate_trajectory(record: dict[str, Any], schema: dict[str, Any] | None = None) -> None:
    if schema is None:
        schema = load_trajectory_schema(Path(__file__).resolve().parents[3] / RELEASE_SCHEMA_PATH)
    _schema_error(record, schema, schema)
    if record["status"] == "PASS":
        if record["role_identity"] not in CANONICAL_ROLES or not record["roles_observed"]:
            raise HostMatrixError("PASS requires observed formal role identity")
        if record["selected_skill"] == "UNSUPPORTED":
            raise HostMatrixError("PASS requires selected Skill observation")
        for field in ("actual_model", "actual_effort", "authority_observation"):
            value = str(record[field]).casefold()
            if value == "unsupported" or value in GENERIC_OBSERVATIONS:
                raise HostMatrixError(f"PASS requires non-generic {field} observation")
        if record["privacy_scan"] != "PASS":
            raise HostMatrixError("PASS requires a passing privacy scan")
        if not record["tool_observations"] or any(tool in {"type", "tool", "unknown"} for tool in record["tool_observations"]):
            raise HostMatrixError("PASS requires actual non-generic tool observations")
        if not record["result"]["direct_success"]:
            raise HostMatrixError("PASS requires a direct scenario success")
        for evidence_name in ("artifact", "result"):
            evidence = record[evidence_name]
            if not isinstance(evidence.get("path"), str) or not evidence["path"] or not isinstance(evidence.get("sha256"), str):
                raise HostMatrixError(f"PASS requires {evidence_name} path and hash evidence")


def _verified_evidence_path(slice_root: Path, evidence: dict[str, Any], label: str) -> Path:
    relative = safe_relative(evidence.get("path"), f"{label} path")
    if not relative.startswith("artifacts/"):
        raise HostMatrixError(f"{label} must be stored in the per-slice artifacts namespace")
    path = _child(slice_root, relative, label)
    if not path.is_file() or path.is_symlink():
        raise HostMatrixError(f"{label} file is missing")
    if sha256_file(path) != _sha256(evidence.get("sha256"), f"{label} sha256"):
        raise HostMatrixError(f"{label} hash does not match its stored file")
    return path


def validate_record_binding(
    record: dict[str, Any], case: dict[str, Any], schema: dict[str, Any], slice_root: Path,
) -> None:
    """Bind a typed PASS to its exact case, host profile, and persisted evidence."""

    validate_trajectory(record, schema)
    host, profile = record["host"], record["profile"]
    if record["case_id"] != case["id"] or record["selected_skill"] != case["selected_skill"]:
        raise HostMatrixError("record case or selected Skill does not bind the matrix manifest")
    if record["role_identity"] != case["required_role"] or set(record["roles_observed"]) != set(case["expected_roles"]):
        raise HostMatrixError("record role identity/coverage does not bind the matrix case")
    expected = _case_profile_expectation(case, host, profile)
    if record["actual_model"] != expected["model"] or record["actual_effort"] != expected["effort"]:
        raise HostMatrixError("record model/effort does not bind its host profile and role")
    if record["authority_observation"] != case["authority"]:
        raise HostMatrixError("record authority does not bind the case")
    if not set(case["required_tools"]).issubset(set(record["tool_observations"])):
        raise HostMatrixError("record tool evidence does not bind the case")
    if record["sanitized_input_sha256"] != sha256_bytes(case["prompt"].encode()):
        raise HostMatrixError("record sanitized input hash does not bind the case prompt")
    if record["status"] != "PASS":
        raise HostMatrixError("record is a FAIL/UNSUPPORTED blocker")
    artifact = _verified_evidence_path(slice_root, record["artifact"], "artifact")
    result = _verified_evidence_path(slice_root, record["result"], "result")
    result_bytes = result.read_bytes()
    if not all(marker.encode() in result_bytes for marker in case["evidence"]["markers"]):
        raise HostMatrixError("result artifact lacks case-specific direct evidence markers")
    secrets = [marker.encode() for marker in case["private_markers"]]
    if any(marker in artifact.read_bytes() or marker in result_bytes for marker in secrets):
        raise HostMatrixError("stored trajectory evidence leaked a private marker")


def _unsupported_record(
    host: str, profile: str, case: dict[str, Any], classification: str,
    *, invocation_id: str | None = None, host_version: str = "UNSUPPORTED",
) -> dict[str, Any]:
    now = utc_now()
    return {
        "schema_version": SCHEMA_VERSION, "record_type": "teamwork_host_trajectory_v4",
        "host": host, "host_version": host_version,
        "invocation_id": invocation_id or str(uuid.uuid4()), "started_at": now, "finished_at": now,
        "case_id": case["id"], "profile": profile, "selected_skill": "UNSUPPORTED",
        "role_identity": "UNSUPPORTED", "roles_observed": [],
        "actual_model": "UNSUPPORTED", "actual_effort": "UNSUPPORTED",
        "tool_observations": [], "authority_observation": "UNSUPPORTED",
        "sanitized_input_sha256": sha256_bytes(case["prompt"].encode()),
        "artifact": {"path": None, "sha256": None},
        "result": {"path": None, "sha256": None, "direct_success": False},
        "exit_status": None, "status": "UNSUPPORTED", "privacy_scan": "NOT_RUN",
        "failure_classification": classification,
    }


def _apply_scenario(tree: Path, scenario: Path, spec: dict[str, Any]) -> None:
    shutil.copytree(tree, scenario, symlinks=False)
    for item in spec["files"]:
        path = _child(scenario, item["path"], "scenario setup path")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(item["content"], encoding="utf-8")


def _immutable_scenario_hashes(scenario: Path, spec: dict[str, Any]) -> dict[str, str]:
    verification = spec.get("verification")
    if not isinstance(verification, dict):
        return {}
    return {
        path: sha256_file(_child(scenario, path, "immutable verifier path"))
        for path in verification["immutable_paths"]
    }


def _run_scenario_verifier(
    scenario: Path, spec: dict[str, Any], before: dict[str, str], timeout_seconds: int,
) -> tuple[bool, str | None]:
    verification = spec.get("verification")
    if not isinstance(verification, dict):
        return True, None
    for path, digest in before.items():
        target = _child(scenario, path, "immutable verifier path")
        try:
            unchanged = sha256_file(target) == digest
        except HostMatrixError:
            unchanged = False
        if not unchanged:
            return False, "scenario-verifier-modified"
    try:
        completed = subprocess.run(
            verification["argv"], cwd=scenario, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, timeout=timeout_seconds, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False, "scenario-verifier-unavailable"
    return (completed.returncode == 0, None if completed.returncode == 0 else "scenario-verifier-failed")


def _private_write(path: Path, value: bytes) -> None:
    parent = _ensure_absolute_directory(path.parent, "trajectory evidence")
    target = parent / path.name
    try:
        info = target.lstat()
    except FileNotFoundError:
        info = None
    except OSError as exc:
        raise HostMatrixError(f"cannot inspect trajectory evidence {target}: {exc}") from exc
    if info is not None:
        if stat.S_ISLNK(info.st_mode):
            raise HostMatrixError(f"trajectory evidence must not be a symlink: {target}")
        raise HostMatrixError(f"trajectory evidence already exists: {target}")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        descriptor = os.open(target, flags, 0o600)
    except OSError as exc:
        raise HostMatrixError(f"cannot create trajectory evidence {target}: {exc}") from exc
    try:
        offset = 0
        while offset < len(value):
            offset += os.write(descriptor, value[offset:])
        os.fchmod(descriptor, 0o600)
    finally:
        os.close(descriptor)


def _artifact_path(output: Path, invocation_id: str, name: str) -> tuple[Path, str]:
    relative = f"artifacts/{invocation_id}/{safe_relative(name, 'artifact name')}"
    return output.parent / relative, relative


def _write_evidence_file(output: Path, invocation_id: str, name: str, value: bytes) -> dict[str, str]:
    path, relative = _artifact_path(output, invocation_id, name)
    _private_write(path, value)
    return {"path": relative, "sha256": sha256_file(path)}


def _non_agent_trace(events: Sequence[dict[str, Any]]) -> str:
    filtered = [event for event in events if _event_type(event) != "agent_message" and not (
        _event_type(event) == "item.completed" and isinstance(event.get("item"), dict)
        and event["item"].get("type") == "agent_message"
    )]
    return "\n".join(json.dumps(event, sort_keys=True) for event in filtered)


def _direct_scenario_evidence(
    *, case: dict[str, Any], scenario: Path, events: Sequence[dict[str, Any]],
    output: Path, invocation_id: str, workspace_before: str | None,
    verification_ok: bool = True, verification_failure: str | None = None,
) -> tuple[bool, dict[str, str], dict[str, str], str | None]:
    evidence = case["evidence"]
    marker_values = evidence["markers"]
    trace = _non_agent_trace(events).encode()
    trace_evidence = _write_evidence_file(output, invocation_id, "host-trace.jsonl", trace)
    if not verification_ok:
        return False, trace_evidence, {}, verification_failure or "scenario-verifier-failed"
    if evidence["kind"] == "workspace":
        target = _child(scenario, evidence["artifact_path"], "workspace evidence artifact")
        try:
            data = _read_regular_bytes(target, "workspace evidence artifact")
        except HostMatrixError:
            return False, trace_evidence, {}, "missing-workspace-artifact"
        if workspace_before is None or sha256_bytes(data) == workspace_before:
            return False, trace_evidence, {}, "workspace-artifact-unchanged"
        if not all(marker.encode() in data for marker in marker_values):
            return False, trace_evidence, {}, "workspace-markers-missing"
        result = _write_evidence_file(output, invocation_id, "scenario-result.bin", data)
        return True, trace_evidence, result, None
    if not trace or not all(marker.encode() in trace for marker in marker_values):
        return False, trace_evidence, {}, "trace-markers-missing"
    result = _write_evidence_file(output, invocation_id, "scenario-result.jsonl", trace)
    return True, trace_evidence, result, None


def _host_argv(
    host: str, executable: str, scenario: Path, prompt: str, authority: str,
    expectation: dict[str, str],
) -> list[str]:
    if host == "codex":
        return [
            executable, "exec", "--ephemeral", "--json", "--model", expectation["model"],
            "-c", f'model_reasoning_effort="{expectation["effort"]}"', "--sandbox", authority,
            "--cd", str(scenario), prompt,
        ]
    if host == "cursor":
        return [executable, "--print", "--output-format", "stream-json", "--workspace", str(scenario), prompt]
    permission = "plan" if authority == "read-only" else "acceptEdits"
    return [executable, "--print", "--output-format", "stream-json", "--permission-mode", permission, prompt]


def run_host_matrix(
    *, host: str, binary: str, profile: str, project_root: Path,
    candidate_manifest: Path, case_manifest: Path, output: Path,
    repeats: int, timeout_seconds: int, extra: dict[str, str],
    only_cases: set[str] | None = None, max_trajectories: int | None = None,
) -> int:
    # Kept for adapter compatibility; model/effort come only from the frozen
    # candidate matrix's profile-rendered role expectation.
    del extra
    if host not in HOSTS or profile not in PROFILES:
        raise HostMatrixError("unsupported host or profile")
    if repeats < 1 or timeout_seconds < 1:
        raise HostMatrixError("invalid repeats or timeout")
    project_root = _checked_directory(project_root, "project root")
    output_relative = _relative_under(project_root, output, "installed output")
    output_prefix = "evals/teamwork/outputs/installed-v4/"
    if not output_relative.startswith(output_prefix):
        raise HostMatrixError(f"v4 installed output must be under {project_root / output_prefix}")
    case_relative = _relative_under(project_root, case_manifest, "case manifest")
    if case_relative != RELEASE_CASE_PATH:
        raise HostMatrixError(f"case manifest must name the candidate matrix: {RELEASE_CASE_PATH}")
    # Deliberately inspect only the pointer's type, never its dirty content.
    # The actual bytes are loaded below from the isolated candidate tree.
    _child(project_root, case_relative, "case manifest input")
    manifest = validate_candidate(project_root, candidate_manifest)
    output = _prepare_output_path(project_root, output_relative)
    executable = shutil.which(binary) if not Path(binary).is_absolute() else binary
    version = "UNSUPPORTED"
    if executable:
        probe = subprocess.run([str(executable), "--version"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        version = (probe.stdout or probe.stderr).strip() or "UNSUPPORTED"
    records: list[dict[str, Any]] = []
    with materialize_candidate(project_root, manifest) as tree:
        candidate_manifest_path = _regular_child(tree, RELEASE_CASE_PATH, "candidate case manifest")
        schema = load_trajectory_schema(_regular_child(tree, RELEASE_SCHEMA_PATH, "candidate trajectory schema"))
        cases = load_case_manifest(candidate_manifest_path, only_cases, root=tree)
        requested = len(cases) * repeats
        if max_trajectories is not None and requested > max_trajectories:
            raise HostMatrixError("requested trajectories exceed --max-trajectories")
        for case in cases:
            scenario_spec = load_json(
                _regular_child(tree, case["scenario"], "candidate scenario"), "scenario fixture"
            )
            for _ in range(repeats):
                if not executable:
                    record = _unsupported_record(host, profile, case, "missing-host-binary", host_version=version)
                    validate_trajectory(record, schema)
                    records.append(record)
                    continue
                started = utc_now()
                invocation_id = str(uuid.uuid4())
                with tempfile.TemporaryDirectory(prefix=f"teamwork-{host}-home-") as home_name, tempfile.TemporaryDirectory(prefix="teamwork-scenario-") as scenario_name:
                    home = Path(home_name)
                    scenario = Path(scenario_name) / "candidate"
                    _apply_scenario(tree, scenario, scenario_spec)
                    immutable_before = _immutable_scenario_hashes(scenario, scenario_spec)
                    workspace_before = None
                    if case["evidence"]["kind"] == "workspace":
                        workspace_before = sha256_file(
                            _child(scenario, case["evidence"]["artifact_path"], "workspace evidence artifact")
                        )
                    env = {"HOME": str(home), "PATH": os.environ.get("PATH", os.defpath)}
                    install = subprocess.run(
                        [str(_regular_child(tree, "install.sh", "candidate installer")), "--copy", "--no-notifications", "--profile", profile, host],
                        cwd=tree, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                        timeout=timeout_seconds, check=False,
                    )
                    if install.returncode != 0:
                        record = _unsupported_record(host, profile, case, "isolated-install-failed", invocation_id=invocation_id, host_version=version)
                        validate_trajectory(record, schema)
                        records.append(record)
                        continue
                    expectation = _case_profile_expectation(case, host, profile)
                    completed = subprocess.run(
                        _host_argv(host, str(executable), scenario, case["prompt"], case["authority"], expectation),
                        cwd=scenario, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                        timeout=timeout_seconds, check=False,
                    )
                    events = _events(completed.stdout)
                    roles = normalize_roles(observed_values(events, {"role-identity", "agent-name", "agent-type", "subagent-type", "role"}))
                    models = observed_values(events, {"model", "actual-model", "resolved-model"})
                    efforts = observed_values(events, {"effort", "actual-effort", "reasoning-effort", "model-reasoning-effort"})
                    skills = observed_values(events, {"selected-skill", "skill"})
                    authorities = observed_values(events, {"authority", "authority-observation", "permission-mode", "sandbox"})
                    tools = observed_tools(events)
                    verification_ok, verification_failure = _run_scenario_verifier(
                        scenario, scenario_spec, immutable_before, timeout_seconds,
                    )
                    direct, artifact, result, direct_failure = _direct_scenario_evidence(
                        case=case, scenario=scenario, events=events, output=output, invocation_id=invocation_id,
                        workspace_before=workspace_before,
                        verification_ok=verification_ok, verification_failure=verification_failure,
                    )
                    output_stream = (completed.stdout + "\n" + completed.stderr).encode()
                    for evidence in (artifact, result):
                        evidence_path = evidence.get("path") if isinstance(evidence, dict) else None
                        if isinstance(evidence_path, str):
                            stored = _child(output.parent, evidence_path, "stored trajectory evidence")
                            output_stream += _read_regular_bytes(stored, "stored trajectory evidence")
                    private = [marker.encode() for marker in case["private_markers"]]
                    privacy = "FAIL" if any(marker in output_stream for marker in private) else "PASS"
                    actual_model = models[-1] if models else "UNSUPPORTED"
                    actual_effort = efforts[-1] if efforts else "UNSUPPORTED"
                    selected_skill = skills[-1] if skills else "UNSUPPORTED"
                    authority = authorities[-1] if authorities else "UNSUPPORTED"
                    bound = (
                        set(case["expected_roles"]).issubset(roles) and selected_skill == case["selected_skill"]
                        and actual_model == expectation["model"] and actual_effort == expectation["effort"]
                        and set(case["required_tools"]).issubset(tools) and authority == case["authority"]
                    )
                    status = "PASS" if completed.returncode == 0 and direct and bound and privacy == "PASS" else "FAIL"
                    failure = None
                    if status != "PASS":
                        if completed.returncode:
                            failure = "host-exit"
                        elif privacy != "PASS":
                            failure = "privacy-leak"
                        elif not direct:
                            failure = direct_failure or "missing-direct-scenario-evidence"
                        else:
                            failure = "host-observation-does-not-bind-case"
                    record = {
                        "schema_version": SCHEMA_VERSION, "record_type": "teamwork_host_trajectory_v4",
                        "host": host, "host_version": version, "invocation_id": invocation_id,
                        "started_at": started, "finished_at": utc_now(), "case_id": case["id"], "profile": profile,
                        "selected_skill": selected_skill, "role_identity": case["required_role"] if case["required_role"] in roles else "UNSUPPORTED",
                        "roles_observed": roles, "actual_model": actual_model, "actual_effort": actual_effort,
                        "tool_observations": tools, "authority_observation": authority,
                        "sanitized_input_sha256": sha256_bytes(case["prompt"].encode()),
                        "artifact": artifact if artifact else {"path": None, "sha256": None},
                        "result": {**(result if result else {"path": None, "sha256": None}), "direct_success": direct},
                        "exit_status": completed.returncode, "status": status, "privacy_scan": privacy,
                        "failure_classification": failure,
                    }
                    validate_trajectory(record, schema)
                    records.append(record)
    serialized: list[bytes] = []
    for record in records:
        validate_trajectory(record, schema)
        serialized.append((json.dumps(record, sort_keys=True) + "\n").encode("utf-8"))
    _private_write(output, b"".join(serialized))
    return 0 if records and all(record["status"] == "PASS" for record in records) else 1
