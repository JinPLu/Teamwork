#!/usr/bin/env python3
"""Build an isolated full-history disposable candidate snapshot."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


HEX64 = re.compile(r"^[0-9a-f]{64}$")
STRICT_TOP_KEYS = {
    "schema_version",
    "success",
    "project_root",
    "paths_file",
    "snapshot_root",
    "candidate_path_count",
    "safe_target",
    "object_isolation",
    "git",
}
STRICT_SAFE_TARGET = {
    "validated": True,
    "parents_under_temp": True,
    "no_overlap": True,
    "snapshot_leaf_previously_nonexistent": True,
    "report_leaf_previously_nonexistent": True,
}
STRICT_OBJECT_KEYS = {
    "source_objects_pre_digest",
    "source_objects_post_digest",
    "source_objects_unchanged",
    "source_index_refs_worktree_unchanged",
}
STRICT_GIT_PROOF = {
    "snapshot_git_exists": True,
    "no_alternates": True,
    "no_hardlinks_to_source": True,
    "no_fetch_or_network": True,
}


class SnapshotError(Exception):
    pass


def canonical_json_bytes(data: object) -> bytes:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def write_canonical_json(path: Path, data: object) -> None:
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


def canonical_abs(path: Path) -> str:
    return os.path.realpath(os.fspath(path))


def is_relative_to(child: str, parent: str) -> bool:
    try:
        return os.path.commonpath([child, parent]) == parent
    except ValueError:
        return False


def strictly_under(child: str, parent: str) -> bool:
    return child != parent and is_relative_to(child, parent)


def paths_overlap(a: str, b: str) -> bool:
    return is_relative_to(a, b) or is_relative_to(b, a)


def resolve_existing_parent_no_symlink(path: Path) -> str:
    parent = path.parent
    if not parent.is_absolute():
        raise SnapshotError(f"path must be absolute: {path}")
    current = Path(parent.anchor)
    parts = parent.parts[1:]
    for part in parts:
        current = current / part
        try:
            info = os.lstat(current)
        except FileNotFoundError as exc:
            raise SnapshotError(f"parent component does not exist: {current}") from exc
        if stat.S_ISLNK(info.st_mode):
            raise SnapshotError(f"parent component is a symlink: {current}")
        if not stat.S_ISDIR(info.st_mode):
            raise SnapshotError(f"parent component is not a directory: {current}")
    return os.path.realpath(parent)


def validate_safe_targets(project_root: Path, paths_file: Path, snapshot_root: Path, report: Path) -> dict[str, bool]:
    project = canonical_abs(project_root)
    source_git = canonical_abs(project_root / ".git")
    source_objects = canonical_abs(project_root / ".git" / "objects")
    home = canonical_abs(Path.home())
    temp_root = canonical_abs(Path(tempfile.gettempdir()))
    for label, path in (("snapshot_root", snapshot_root), ("report", report)):
        if not path.is_absolute():
            raise SnapshotError(f"{label} must be absolute")
        if os.fspath(path) == "/":
            raise SnapshotError(f"{label} cannot be /")
        if canonical_abs(path) == home:
            raise SnapshotError(f"{label} cannot be home")
    if not paths_file.is_absolute():
        raise SnapshotError("--paths must be absolute")
    try:
        path_info = os.lstat(paths_file)
    except FileNotFoundError as exc:
        raise SnapshotError("--paths must exist") from exc
    if stat.S_ISLNK(path_info.st_mode) or not stat.S_ISREG(path_info.st_mode):
        raise SnapshotError("--paths must be a non-symlink regular file")
    snapshot_parent = resolve_existing_parent_no_symlink(snapshot_root)
    report_parent = resolve_existing_parent_no_symlink(report)
    if snapshot_root.exists() or os.path.lexists(snapshot_root):
        raise SnapshotError("snapshot leaf already exists")
    if report.exists() or os.path.lexists(report):
        raise SnapshotError("report leaf already exists")
    if not strictly_under(snapshot_parent, temp_root) or not strictly_under(report_parent, temp_root):
        raise SnapshotError("snapshot and report parents must be strictly under temporary root")
    snapshot = os.path.join(snapshot_parent, snapshot_root.name)
    report_real = os.path.join(report_parent, report.name)
    paths_real = canonical_abs(paths_file)
    forbidden = {
        project,
        source_git,
        source_objects,
        home,
        paths_real,
    }
    for label, target in (("snapshot_root", snapshot), ("report", report_real)):
        if target == "/":
            raise SnapshotError(f"{label} overlaps forbidden path: /")
        for forbidden_path in forbidden:
            if paths_overlap(target, forbidden_path):
                raise SnapshotError(f"{label} overlaps forbidden path: {forbidden_path}")
        if strictly_under(target, project) or strictly_under(target, source_git) or strictly_under(target, source_objects):
            raise SnapshotError(f"{label} is inside source repository")
    if paths_overlap(snapshot, report_real):
        raise SnapshotError("snapshot and report overlap")
    if strictly_under(snapshot, report_parent):
        raise SnapshotError("snapshot cannot be inside report parent")
    if strictly_under(snapshot, os.path.dirname(paths_real)):
        raise SnapshotError("snapshot cannot be inside paths-file parent")
    if strictly_under(paths_real, snapshot):
        raise SnapshotError("paths file cannot be inside snapshot")
    return dict(STRICT_SAFE_TARGET)


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fingerprint_tree(root: Path) -> tuple[str, list[dict[str, Any]]]:
    entries: list[dict[str, Any]] = []
    if not root.is_dir():
        raise SnapshotError(f"object database missing: {root}")
    for path in sorted((root, *root.rglob("*")), key=lambda item: item.relative_to(root).as_posix() if item != root else ""):
        info = path.lstat()
        rel = "." if path == root else path.relative_to(root).as_posix()
        entry: dict[str, Any] = {
            "path": rel,
            "mode": stat.S_IMODE(info.st_mode),
            "size": info.st_size,
            "dev": info.st_dev,
            "ino": info.st_ino,
            "nlink": info.st_nlink,
        }
        if stat.S_ISDIR(info.st_mode):
            entry["type"] = "directory"
        elif stat.S_ISREG(info.st_mode):
            entry["type"] = "file"
            entry["sha256"] = hash_file(path)
        elif stat.S_ISLNK(info.st_mode):
            entry["type"] = "symlink"
            entry["target_sha256"] = hashlib.sha256(os.readlink(path).encode("utf-8")).hexdigest()
        else:
            entry["type"] = "other"
        entries.append(entry)
    return hashlib.sha256(canonical_json_bytes(entries)).hexdigest(), entries


def source_state_digest(project_root: Path) -> str:
    git_dir = project_root / ".git"
    entries: list[dict[str, Any]] = []
    for rel in ("HEAD", "index", "packed-refs"):
        path = git_dir / rel
        if path.exists() and path.is_file():
            info = path.lstat()
            entries.append({"path": f".git/{rel}", "mode": stat.S_IMODE(info.st_mode), "sha256": hash_file(path), "size": info.st_size})
    refs = git_dir / "refs"
    if refs.exists():
        for path in sorted(refs.rglob("*")):
            info = path.lstat()
            rel = path.relative_to(project_root).as_posix()
            row: dict[str, Any] = {"path": rel, "mode": stat.S_IMODE(info.st_mode), "size": info.st_size}
            if stat.S_ISREG(info.st_mode):
                row.update({"type": "file", "sha256": hash_file(path)})
            elif stat.S_ISDIR(info.st_mode):
                row["type"] = "directory"
            elif stat.S_ISLNK(info.st_mode):
                row.update({"type": "symlink", "target_sha256": hashlib.sha256(os.readlink(path).encode("utf-8")).hexdigest()})
            entries.append(row)
    status_raw = subprocess.check_output(["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"], cwd=project_root)
    entries.append({"git_status_z_sha256": hashlib.sha256(status_raw).hexdigest()})
    return hashlib.sha256(canonical_json_bytes(entries)).hexdigest()


def read_paths(paths_file: Path) -> list[str]:
    raw = paths_file.read_bytes()
    paths = [item.decode("utf-8") for item in raw.split(b"\0") if item]
    if not paths:
        raise SnapshotError("paths file is empty")
    for path in paths:
        if path.startswith("/") or "\\" in path or "\0" in path:
            raise SnapshotError(f"unsafe candidate path: {path!r}")
        parts = path.split("/")
        if any(part in ("", ".", "..") for part in parts):
            raise SnapshotError(f"unsafe candidate path: {path!r}")
    return sorted(set(paths), key=lambda item: item.encode("utf-8"))


def git_env(snapshot_root: Path, work_tree: Path | None = None) -> dict[str, str]:
    env = os.environ.copy()
    env.pop("GIT_ALTERNATE_OBJECT_DIRECTORIES", None)
    env.pop("GIT_COMMON_DIR", None)
    env.update(
        {
            "GIT_DIR": str(snapshot_root / ".git"),
            "GIT_OBJECT_DIRECTORY": str(snapshot_root / ".git" / "objects"),
            "GIT_INDEX_FILE": str(snapshot_root / ".git" / "index"),
        }
    )
    if work_tree is not None:
        env["GIT_WORK_TREE"] = str(work_tree)
    else:
        env.pop("GIT_WORK_TREE", None)
    return env


def run_git(args: list[str], *, cwd: Path, env: dict[str, str] | None = None, input_bytes: bytes | None = None) -> None:
    subprocess.run(["git", *args], cwd=cwd, env=env, input=input_bytes, check=True)


def alternates_absent(snapshot_root: Path) -> bool:
    alternates = snapshot_root / ".git" / "objects" / "info" / "alternates"
    return not alternates.exists() or alternates.read_bytes() == b""


def run_no_hardlink_helper(project_root: Path, snapshot_root: Path) -> None:
    helper = project_root / "scripts" / "verify-no-hardlinked-git-objects.py"
    if not helper.is_file():
        raise SnapshotError(f"missing no-hardlink helper: {helper}")
    subprocess.run(
        [sys.executable, str(helper), "--source", str(project_root / ".git" / "objects"), "--snapshot", str(snapshot_root / ".git" / "objects")],
        cwd=project_root,
        check=True,
    )


def build_snapshot(project_root: Path, paths_file: Path, snapshot_root: Path, report: Path) -> dict[str, Any]:
    safe_target = validate_safe_targets(project_root, paths_file, snapshot_root, report)
    project = Path(canonical_abs(project_root))
    paths_real = Path(canonical_abs(paths_file))
    snapshot = Path(os.path.join(resolve_existing_parent_no_symlink(snapshot_root), snapshot_root.name))
    report_real = Path(os.path.join(resolve_existing_parent_no_symlink(report), report.name))
    paths = read_paths(paths_real)
    pre_digest, pre_entries = fingerprint_tree(project / ".git" / "objects")
    source_state_pre = source_state_digest(project)
    clone_env = os.environ.copy()
    clone_env.pop("GIT_INDEX_FILE", None)
    clone_env.pop("GIT_ALTERNATE_OBJECT_DIRECTORIES", None)
    clone_env.pop("GIT_COMMON_DIR", None)
    run_git(["clone", "--no-checkout", "--no-hardlinks", "--no-local", str(project), str(snapshot)], cwd=project, env=clone_env)
    if not alternates_absent(snapshot):
        raise SnapshotError("snapshot alternates file is present")
    run_git(["read-tree", "HEAD"], cwd=snapshot, env=git_env(snapshot))
    pathspec = b"".join(path.encode("utf-8") + b"\0" for path in paths)
    run_git(["add", "-A", "--pathspec-from-file=-", "--pathspec-file-nul"], cwd=project, env=git_env(snapshot, project), input_bytes=pathspec)
    snapshot.mkdir(parents=True, exist_ok=True)
    run_git(["checkout-index", "-a", "-f"], cwd=snapshot, env=git_env(snapshot, snapshot))
    commit_env = git_env(snapshot, snapshot)
    commit_env.update(
        {
            "GIT_AUTHOR_NAME": "Teamwork Candidate Snapshot",
            "GIT_AUTHOR_EMAIL": "teamwork@example.invalid",
            "GIT_AUTHOR_DATE": "2026-07-29T00:00:00Z",
            "GIT_COMMITTER_NAME": "Teamwork Candidate Snapshot",
            "GIT_COMMITTER_EMAIL": "teamwork@example.invalid",
            "GIT_COMMITTER_DATE": "2026-07-29T00:00:00Z",
        }
    )
    run_git(["commit", "--allow-empty", "-m", "candidate snapshot"], cwd=snapshot, env=commit_env)
    run_no_hardlink_helper(project, snapshot)
    post_digest, post_entries = fingerprint_tree(project / ".git" / "objects")
    source_state_post = source_state_digest(project)
    if pre_entries != post_entries:
        raise SnapshotError("source object database changed")
    if source_state_pre != source_state_post:
        raise SnapshotError("source index, refs, or worktree status changed")
    report_data = {
        "schema_version": 1,
        "success": True,
        "project_root": str(project),
        "paths_file": str(paths_real),
        "snapshot_root": str(snapshot),
        "candidate_path_count": len(paths),
        "safe_target": safe_target,
        "object_isolation": {
            "source_objects_pre_digest": pre_digest,
            "source_objects_post_digest": post_digest,
            "source_objects_unchanged": True,
            "source_index_refs_worktree_unchanged": True,
        },
        "git": {
            "snapshot_git_exists": (snapshot / ".git").is_dir(),
            "no_alternates": alternates_absent(snapshot),
            "no_hardlinks_to_source": True,
            "no_fetch_or_network": True,
        },
    }
    validate_snapshot_report(report_data)
    write_canonical_json(report_real, report_data)
    return report_data


def validate_snapshot_report(data: object) -> None:
    if not isinstance(data, dict):
        raise SnapshotError("snapshot report must be an object")
    if set(data) != STRICT_TOP_KEYS:
        raise SnapshotError("snapshot report keys mismatch")
    if data.get("schema_version") != 1:
        raise SnapshotError("snapshot report schema_version invalid")
    if data.get("success") is not True:
        raise SnapshotError("snapshot report success not true")
    for key in ("project_root", "paths_file", "snapshot_root"):
        value = data.get(key)
        if not isinstance(value, str) or value != os.path.realpath(value) or not os.path.isabs(value):
            raise SnapshotError(f"snapshot report {key} is not canonical absolute")
    count = data.get("candidate_path_count")
    if type(count) is not int or count <= 0:
        raise SnapshotError("candidate_path_count must be int, not bool, and > 0")
    if data.get("safe_target") != STRICT_SAFE_TARGET:
        raise SnapshotError("safe_target proof mismatch")
    object_isolation = data.get("object_isolation")
    if not isinstance(object_isolation, dict) or set(object_isolation) != STRICT_OBJECT_KEYS:
        raise SnapshotError("object_isolation keys mismatch")
    pre_digest = object_isolation.get("source_objects_pre_digest")
    post_digest = object_isolation.get("source_objects_post_digest")
    if not isinstance(pre_digest, str) or not HEX64.match(pre_digest):
        raise SnapshotError("source_objects_pre_digest invalid")
    if not isinstance(post_digest, str) or not HEX64.match(post_digest):
        raise SnapshotError("source_objects_post_digest invalid")
    if pre_digest != post_digest:
        raise SnapshotError("source object digest mismatch")
    if object_isolation.get("source_objects_unchanged") is not True:
        raise SnapshotError("source_objects_unchanged must be true")
    if object_isolation.get("source_index_refs_worktree_unchanged") is not True:
        raise SnapshotError("source_index_refs_worktree_unchanged must be true")
    if data.get("git") != STRICT_GIT_PROOF:
        raise SnapshotError("git proof mismatch")
    snapshot_root = data["snapshot_root"]
    if not os.path.isdir(os.path.join(snapshot_root, ".git")):
        raise SnapshotError("snapshot .git missing")
    if not os.path.isdir(os.path.join(snapshot_root, ".git", "objects")):
        raise SnapshotError("snapshot .git/objects missing")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--paths", required=True)
    parser.add_argument("--snapshot-root", required=True)
    parser.add_argument("--report", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        build_snapshot(Path(args.project_root), Path(args.paths), Path(args.snapshot_root), Path(args.report))
    except (SnapshotError, OSError, subprocess.CalledProcessError) as exc:
        print(f"PREWRITE_SAFE: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
