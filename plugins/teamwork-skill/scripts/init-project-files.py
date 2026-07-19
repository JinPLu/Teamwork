#!/usr/bin/env python3
"""Initialize project-local Teamwork context through a recoverable FD journal.

W4 owns discussion artifact interpretation, rendering, and validation.  Init
only asks its migration planner for exact replacement bytes, journals those
bytes with the ordinary-memory anchors, and never reimplements that format.
"""

from __future__ import annotations

import argparse
import base64
import fcntl
import hashlib
import json
import os
import re
import runpy
import stat
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path, PurePosixPath
from typing import NoReturn

import validate_teamwork_index as validator


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIRECTORY = REPOSITORY_ROOT / "templates/teamwork-memory"
V342_OWNED_SURFACES = REPOSITORY_ROOT / "scripts/tests/fixtures/v3.4.2-owned-surfaces.json"
V4_MIGRATION_LEDGER = REPOSITORY_ROOT / "evals/teamwork/ledgers/v4-capability-migration.jsonl"
W4_DISCUSSION_API = REPOSITORY_ROOT / "scripts/discussion-transaction.py"
INIT_JOURNAL = ".teamwork-init-transaction.json"
DISCUSSION_MARKER = ".discussion-transaction.json"
JOURNAL_SCHEMA_VERSION = 4
CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
HASH_RE = re.compile(r"[0-9a-f]{64}")
DISCUSSION_CURRENT_PATH = "docs/teamwork/discussion/current.md"
DISCUSSION_ARCHIVE_NAME_RE = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9]+(?:-[a-z0-9]+)*\.md"
)
MANAGED_START = "<!-- TEAMWORK_PROJECT_START -->"
MANAGED_END = "<!-- TEAMWORK_PROJECT_END -->"
IGNORE_START = "# TEAMWORK_LOCAL_START"
IGNORE_END = "# TEAMWORK_LOCAL_END"


class InitError(Exception):
    pass


def fail(message: str) -> NoReturn:
    raise InitError(message)


def checked_project_root(raw: str) -> Path:
    if not raw or CONTROL_RE.search(raw):
        fail("project root must be non-empty text without control characters")
    root = Path(os.path.abspath(os.path.expanduser(raw)))
    current = Path(root.anchor)
    for part in root.parts[1:]:
        current /= part
        try:
            info = current.lstat()
        except OSError as exc:
            fail(f"project-root component must exist: {current}: {exc}")
        if stat.S_ISLNK(info.st_mode):
            fail(f"refusing symlinked project-root component: {current}")
        if not stat.S_ISDIR(info.st_mode):
            fail(f"project-root component must be a directory: {current}")
    return root


def checked_relative(value: str, *, label: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if (
        not value
        or CONTROL_RE.search(value)
        or "\\" in value
        or path.is_absolute()
        or path.as_posix() != value
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        fail(f"{label} must be a normalized project-relative path")
    return path


def read_template(name: str) -> str:
    path = TEMPLATE_DIRECTORY / name
    try:
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            fail(f"Teamwork memory template must be a regular file: {path}")
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        fail(f"cannot read Teamwork memory template {path}: {exc}")


def render_memory_files(today: str, label: str) -> dict[str, str]:
    try:
        date.fromisoformat(today)
    except ValueError:
        fail("--today must be a valid YYYY-MM-DD date")
    index_text = read_template("index.json")
    try:
        index = json.loads(index_text)
    except json.JSONDecodeError as exc:
        fail(f"Teamwork memory index template is invalid JSON: {exc}")
    index["last_updated"] = today
    index["project"]["name"] = label
    for entry in index["entries"]:
        entry["updated"] = today
    rendered_index = json.dumps(index, indent=2, ensure_ascii=False) + "\n"
    current = read_template("current.md").replace("YYYY-MM-DD", today)
    readme = read_template("README.md")
    validator.validate_index(index, Path("templates/teamwork-memory/index.json"))
    return {
        "docs/teamwork/index.json": rendered_index,
        "docs/teamwork/current.md": current,
        "docs/teamwork/README.md": readme,
    }


def project_label(root: Path, explicit: str | None) -> str:
    label = explicit if explicit is not None else root.name
    label = label.strip()
    if not label or CONTROL_RE.search(label):
        fail("project label must be non-empty text without control characters")
    return label


def managed_agents_block(tree: "InitTree", label: str) -> str:
    lines = [
        f"- Project label (local routing only): `{label}`.",
        "- For saved, resumed, or independently major Grill discussion, use only `docs/teamwork/discussion/current.md`; never mirror it into ordinary memory.",
        "- For ordinary durable memory, read `docs/teamwork/index.json` first, then `docs/teamwork/README.md`; keep volatile progress in its actual artifact.",
    ]
    codegraph = tree.stat("root", ".codegraph")
    if (
        codegraph is not None
        and stat.S_ISDIR(codegraph.st_mode)
        and not stat.S_ISLNK(codegraph.st_mode)
        and codegraph.st_dev == tree.device
    ):
        lines.append("- CodeGraph: this project has a local `.codegraph/` index.")
    return (
        f"{MANAGED_START}\n"
        "## Teamwork Project Instructions\n\n"
        + "\n".join(lines)
        + f"\n{MANAGED_END}\n"
    )


GITIGNORE_BLOCK = f"""{IGNORE_START}
# Teamwork local runtime state
.codegraph/
docs/teamwork/plans/
docs/teamwork/design/
docs/teamwork/discussion/
docs/teamwork/research/
docs/teamwork/reports/
docs/teamwork/workflows/
docs/teamwork/index.json
docs/teamwork/README.md
docs/teamwork/current.md
{INIT_JOURNAL}
.*.teamwork-init-*
docs/teamwork/{INIT_JOURNAL}
# Legacy v3 location retained as a fail-closed migration interlock.
docs/teamwork/{DISCUSSION_MARKER}
docs/teamwork/discussion/{DISCUSSION_MARKER}
docs/teamwork/.*.teamwork-init-*
{IGNORE_END}
"""


def _identity(info: os.stat_result) -> tuple[int, int, int]:
    return info.st_dev, info.st_ino, stat.S_IMODE(info.st_mode)


def _fd_flags(*, directory: bool = False) -> int:
    if not getattr(os, "O_NOFOLLOW", 0) or (directory and not getattr(os, "O_DIRECTORY", 0)):
        fail("platform lacks required no-follow directory operations")
    return (
        os.O_RDONLY
        | os.O_NOFOLLOW
        | getattr(os, "O_CLOEXEC", 0)
        | (os.O_DIRECTORY if directory else 0)
    )


@dataclass(frozen=True)
class FdSnapshot:
    parent: str
    name: str
    logical: str
    exists: bool
    device: int | None = None
    inode: int | None = None
    mode: int | None = None
    data: bytes | None = None


class InitTree:
    """Descriptor-relative project tree retained for the whole operation."""

    CHILDREN = (
        ("root", "docs", "docs"),
        ("docs", "teamwork", "teamwork"),
        ("teamwork", "discussion", "discussion"),
    )

    def __init__(self, root: Path) -> None:
        expected = root.lstat()
        try:
            root_fd = os.open(root, _fd_flags(directory=True))
        except OSError as exc:
            fail(f"cannot safely open project root: {exc}")
        opened = os.fstat(root_fd)
        if not stat.S_ISDIR(expected.st_mode) or _identity(opened) != _identity(expected):
            os.close(root_fd)
            fail("project root changed identity while opening")
        self.root = root
        self.device = opened.st_dev
        self.fds: dict[str, int] = {"root": root_fd}
        self.identities: dict[str, tuple[int, int, int]] = {"root": _identity(opened)}
        self.lock_fd: int | None = None

    def stat(self, parent: str, name: str) -> os.stat_result | None:
        try:
            return os.stat(name, dir_fd=self.fds[parent], follow_symlinks=False)
        except FileNotFoundError:
            return None
        except OSError as exc:
            fail(f"cannot inspect project entry {name}: {exc}")

    def open_existing(self, parent: str, name: str, key: str) -> os.stat_result | None:
        before = self.stat(parent, name)
        if before is None:
            return None
        if stat.S_ISLNK(before.st_mode) or not stat.S_ISDIR(before.st_mode) or before.st_dev != self.device:
            fail(f"project directory must be a same-device non-symlink directory: {name}")
        try:
            fd = os.open(name, _fd_flags(directory=True), dir_fd=self.fds[parent])
        except OSError as exc:
            fail(f"cannot safely open project directory {name}: {exc}")
        opened = os.fstat(fd)
        if _identity(opened) != _identity(before):
            os.close(fd)
            fail(f"project directory changed identity while opening: {name}")
        old = self.fds.get(key)
        if old is not None:
            os.close(old)
        self.fds[key] = fd
        self.identities[key] = _identity(opened)
        return before

    def lock_teamwork(self) -> None:
        if "teamwork" not in self.fds:
            fail("cannot lock missing docs/teamwork directory")
        if self.lock_fd is not None:
            return
        self.lock_fd = os.dup(self.fds["teamwork"])
        try:
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            os.close(self.lock_fd)
            self.lock_fd = None
            fail(f"cannot acquire Teamwork init lock: {exc}")

    def verify(self) -> None:
        try:
            now = self.root.lstat()
        except OSError as exc:
            fail(f"cannot recheck project root: {exc}")
        if _identity(now) != self.identities["root"] or not stat.S_ISDIR(now.st_mode):
            fail("project root identity changed during initialization")
        for parent, name, key in self.CHILDREN:
            if key not in self.fds:
                continue
            current = self.stat(parent, name)
            if current is None or _identity(current) != self.identities[key] or not stat.S_ISDIR(current.st_mode):
                fail(f"project directory identity changed during initialization: {key}")

    def close(self) -> None:
        if self.lock_fd is not None:
            try:
                fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
            finally:
                os.close(self.lock_fd)
            self.lock_fd = None
        for key in tuple(reversed(tuple(self.fds))):
            try:
                os.close(self.fds.pop(key))
            except OSError:
                pass


def _snapshot(tree: InitTree, parent: str, name: str, logical: str) -> FdSnapshot:
    before = tree.stat(parent, name)
    if before is None:
        return FdSnapshot(parent, name, logical, False)
    if (
        stat.S_ISLNK(before.st_mode)
        or not stat.S_ISREG(before.st_mode)
        or before.st_nlink != 1
        or before.st_dev != tree.device
    ):
        fail(f"project output must be a single-link same-device regular file: {logical}")
    try:
        fd = os.open(name, _fd_flags(), dir_fd=tree.fds[parent])
    except OSError as exc:
        fail(f"cannot safely open project output {logical}: {exc}")
    try:
        opened = os.fstat(fd)
        if _identity(opened) != _identity(before) or opened.st_nlink != 1:
            fail(f"project output changed identity while opening: {logical}")
        chunks: list[bytes] = []
        while chunk := os.read(fd, 1024 * 1024):
            chunks.append(chunk)
        final = os.fstat(fd)
        current = tree.stat(parent, name)
        if (
            current is None
            or _identity(final) != _identity(opened)
            or _identity(current) != _identity(opened)
            or final.st_nlink != 1
        ):
            fail(f"project output changed identity while reading: {logical}")
        return FdSnapshot(
            parent,
            name,
            logical,
            True,
            opened.st_dev,
            opened.st_ino,
            stat.S_IMODE(opened.st_mode),
            b"".join(chunks),
        )
    finally:
        os.close(fd)


def _snapshot_text(snapshot: FdSnapshot, label: str) -> str:
    if not snapshot.exists or snapshot.data is None:
        fail(f"missing project output: {label}")
    try:
        return snapshot.data.decode("utf-8")
    except UnicodeDecodeError as exc:
        fail(f"{label} must be UTF-8: {exc}")


def _same_snapshot(left: FdSnapshot, right: FdSnapshot) -> bool:
    return (
        left.parent,
        left.name,
        left.logical,
        left.exists,
        left.device,
        left.inode,
        left.mode,
        left.data,
    ) == (
        right.parent,
        right.name,
        right.logical,
        right.exists,
        right.device,
        right.inode,
        right.mode,
        right.data,
    )


def _same_file_preimage(left: FdSnapshot, right: FdSnapshot) -> bool:
    """Compare file identity/content while permitting a transaction backup name."""

    return (
        left.exists,
        left.device,
        left.inode,
        left.mode,
        left.data,
    ) == (
        right.exists,
        right.device,
        right.inode,
        right.mode,
        right.data,
    )


def _snapshot_record(snapshot: FdSnapshot) -> dict[str, object]:
    if not snapshot.exists:
        return {"exists": False}
    assert snapshot.data is not None and snapshot.mode is not None
    return {
        "exists": True,
        "device": snapshot.device,
        "inode": snapshot.inode,
        "mode": snapshot.mode,
        "sha256": hashlib.sha256(snapshot.data).hexdigest(),
        "bytes_b64": base64.b64encode(snapshot.data).decode("ascii"),
    }


def _record_snapshot(parent: str, name: str, logical: str, value: object) -> FdSnapshot:
    if not isinstance(value, dict) or not isinstance(value.get("exists"), bool):
        fail("init journal has an invalid file preimage")
    if not value["exists"]:
        if set(value) != {"exists"}:
            fail("absent init journal preimage has extra fields")
        return FdSnapshot(parent, name, logical, False)
    required = {"exists", "device", "inode", "mode", "sha256", "bytes_b64"}
    if set(value) != required:
        fail("init journal file preimage fields are invalid")
    device, inode, mode = value["device"], value["inode"], value["mode"]
    digest, encoded = value["sha256"], value["bytes_b64"]
    if (
        not all(isinstance(item, int) and item >= 0 for item in (device, inode, mode))
        or not isinstance(digest, str)
        or HASH_RE.fullmatch(digest) is None
        or not isinstance(encoded, str)
    ):
        fail("init journal file preimage types are invalid")
    try:
        data = base64.b64decode(encoded.encode("ascii"), validate=True)
    except (ValueError, UnicodeEncodeError) as exc:
        fail(f"init journal file preimage bytes are invalid: {exc}")
    if hashlib.sha256(data).hexdigest() != digest:
        fail("init journal file preimage hash does not match bytes")
    return FdSnapshot(parent, name, logical, True, device, inode, mode, data)


def _validate_journal_target(parent: str, name: str, logical: str) -> None:
    if "/" in name or "\\" in name or name in {".", ".."}:
        fail("init journal target name is unsafe")
    expected_logical = {
        "root": name,
        "teamwork": f"docs/teamwork/{name}",
        "discussion": f"docs/teamwork/discussion/{name}",
        "plans": f"docs/teamwork/plans/{name}",
    }.get(parent)
    if expected_logical != logical:
        fail("init journal target parent and logical path disagree")
    if parent == "root" and name not in {"AGENTS.md", ".gitignore"}:
        fail("init journal has an unsupported project-root target")
    if parent == "teamwork" and name not in {"index.json", "current.md", "README.md"}:
        fail("init journal has an unsupported ordinary-memory target")
    if parent == "discussion" and name != "current.md" and not re.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9]+(?:-[a-z0-9]+)*\.md", name
    ):
        fail("init journal has an unsupported W4 discussion target")
    if parent == "plans" and (not name.endswith(".md") or name == ".md"):
        fail("init journal has an unsupported active Plan guard")


def _guard_record(snapshot: FdSnapshot) -> dict[str, object]:
    return {
        "parent": snapshot.parent,
        "name": snapshot.name,
        "logical": snapshot.logical,
        "before": _snapshot_record(snapshot),
    }


def _guard_from_record(record: object) -> FdSnapshot:
    if not isinstance(record, dict) or set(record) != {"parent", "name", "logical", "before"}:
        fail("init journal guard record has invalid fields")
    parent, name, logical = record["parent"], record["name"], record["logical"]
    if not all(isinstance(value, str) and value for value in (parent, name, logical)):
        fail("init journal guard record has invalid names")
    assert isinstance(parent, str) and isinstance(name, str) and isinstance(logical, str)
    _validate_journal_target(parent, name, logical)
    return _record_snapshot(parent, name, logical, record["before"])


def _directory_record(tree: InitTree, parent: str, name: str, key: str) -> dict[str, object]:
    before = tree.stat(parent, name)
    if before is None:
        state: dict[str, object] = {"exists": False}
    else:
        if stat.S_ISLNK(before.st_mode) or not stat.S_ISDIR(before.st_mode) or before.st_dev != tree.device:
            fail(f"project directory must be a same-device non-symlink directory: {name}")
        state = {
            "exists": True,
            "device": before.st_dev,
            "inode": before.st_ino,
            "mode": stat.S_IMODE(before.st_mode),
        }
    return {"parent": parent, "name": name, "key": key, "before": state, "after": None}


def _valid_directory_state(value: object) -> bool:
    if not isinstance(value, dict) or not isinstance(value.get("exists"), bool):
        return False
    if value["exists"] is False:
        return set(value) == {"exists"}
    return (
        set(value) == {"exists", "device", "inode", "mode"}
        and all(isinstance(value.get(key), int) and value[key] >= 0 for key in ("device", "inode", "mode"))
    )


def _directory_matches(info: os.stat_result | None, state: object) -> bool:
    if not _valid_directory_state(state):
        fail("init journal has an invalid directory record")
    assert isinstance(state, dict)
    if not state["exists"]:
        return info is None
    return (
        info is not None
        and stat.S_ISDIR(info.st_mode)
        and not stat.S_ISLNK(info.st_mode)
        and (info.st_dev, info.st_ino, stat.S_IMODE(info.st_mode))
        == (state["device"], state["inode"], state["mode"])
    )


def _directory_state(info: os.stat_result) -> dict[str, object]:
    return {
        "exists": True,
        "device": info.st_dev,
        "inode": info.st_ino,
        "mode": stat.S_IMODE(info.st_mode),
    }


def _temp_name(tree: InitTree, parent: str, name: str, role: str) -> str:
    for ordinal in range(1000):
        candidate = f".{name}.teamwork-init-{role}-{os.getpid()}-{ordinal}"
        if tree.stat(parent, candidate) is None:
            return candidate
    fail(f"cannot reserve a transaction temporary for {name}")


def _write_temp(tree: InitTree, parent: str, name: str, data: bytes, mode: int) -> os.stat_result:
    try:
        fd = os.open(
            name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0),
            mode,
            dir_fd=tree.fds[parent],
        )
    except OSError as exc:
        fail(f"cannot create transaction staging file {name}: {exc}")
    try:
        os.fchmod(fd, mode)
        offset = 0
        while offset < len(data):
            offset += os.write(fd, data[offset:])
        os.fsync(fd)
        info = os.fstat(fd)
    except OSError as exc:
        fail(f"cannot durably stage transaction file {name}: {exc}")
    finally:
        os.close(fd)
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_dev != tree.device:
        fail("transaction staging file has an unsafe type, link count, or device")
    return info


def _unlink_verified(tree: InitTree, parent: str, name: str, identity: tuple[int, int] | None) -> None:
    info = tree.stat(parent, name)
    if info is None:
        return
    if (
        stat.S_ISLNK(info.st_mode)
        or not stat.S_ISREG(info.st_mode)
        or info.st_nlink != 1
        or identity is None
        or (info.st_dev, info.st_ino) != identity
    ):
        fail(f"transaction temporary changed identity: {name}")
    try:
        os.unlink(name, dir_fd=tree.fds[parent])
        os.fsync(tree.fds[parent])
    except OSError as exc:
        fail(f"cannot remove transaction temporary {name}: {exc}")


def _journal_bytes(value: dict[str, object]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"


def _marker_temp_name(tree: InitTree, parent: str) -> str:
    for ordinal in range(1000):
        candidate = f".{INIT_JOURNAL}.journal-{os.getpid()}-{ordinal}"
        if tree.stat(parent, candidate) is None:
            return candidate
    fail("cannot reserve init journal staging name")


def _write_marker_at(tree: InitTree, parent: str, data: bytes) -> None:
    temp = _marker_temp_name(tree, parent)
    staged = _write_temp(tree, parent, temp, data, 0o600)
    try:
        os.replace(temp, INIT_JOURNAL, src_dir_fd=tree.fds[parent], dst_dir_fd=tree.fds[parent])
        os.fsync(tree.fds[parent])
    except OSError as exc:
        _unlink_verified(tree, parent, temp, (staged.st_dev, staged.st_ino))
        fail(f"cannot atomically update init journal: {exc}")


def _read_marker_at(tree: InitTree, parent: str) -> tuple[dict[str, object], bytes] | None:
    snapshot = _snapshot(tree, parent, INIT_JOURNAL, INIT_JOURNAL)
    if not snapshot.exists:
        return None
    assert snapshot.data is not None and snapshot.mode is not None
    if snapshot.mode != 0o600:
        fail("init journal must have mode 0600")
    try:
        value = json.loads(snapshot.data)
    except json.JSONDecodeError as exc:
        fail(f"init journal is malformed: {exc}")
    if not isinstance(value, dict):
        fail("init journal root must be an object")
    return value, snapshot.data


def _remove_marker_at(tree: InitTree, parent: str, expected: bytes) -> None:
    snapshot = _snapshot(tree, parent, INIT_JOURNAL, INIT_JOURNAL)
    if not snapshot.exists:
        return
    if snapshot.data != expected:
        fail("init journal changed before cleanup")
    try:
        os.unlink(INIT_JOURNAL, dir_fd=tree.fds[parent])
        os.fsync(tree.fds[parent])
    except OSError as exc:
        fail(f"cannot remove init journal: {exc}")


def _require_known_managed_block(
    original: str,
    start: str,
    end: str,
    block: str,
    *,
    prefix: str = "",
    known_heading: str,
) -> str:
    starts = original.count(start)
    ends = original.count(end)
    if (starts, ends) == (0, 0):
        base = original if original else prefix
        return base.rstrip() + ("\n\n" if base.strip() else "") + block.rstrip() + "\n"
    if (starts, ends) != (1, 1):
        fail(f"managed block markers are ambiguous: {start} / {end}")
    start_at = original.index(start)
    end_at = original.index(end, start_at)
    if end_at < start_at:
        fail(f"managed block markers are reversed: {start} / {end}")
    managed = original[start_at : end_at + len(end)]
    if known_heading not in managed:
        fail(f"managed block has an unknown or user-owned shape: {start}")
    return (original[:start_at] + block.rstrip() + original[end_at + len(end) :]).rstrip() + "\n"


def _load_v342_authority() -> tuple[dict[str, object], list[dict[str, object]]]:
    try:
        fixture = json.loads(V342_OWNED_SURFACES.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail("v3.4.2 owned-surface inventory is unavailable; migration preflight is blocked")
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"v3.4.2 owned-surface inventory is unreadable: {exc}")
    if (
        not isinstance(fixture, dict)
        or fixture.get("schema_version") != 1
        or fixture.get("tag") != "v3.4.2"
        or not isinstance(fixture.get("deterministic_surfaces"), list)
        or not isinstance(fixture.get("runtime_surfaces"), list)
    ):
        fail("v3.4.2 owned-surface inventory has an unsupported schema")
    deterministic = fixture["deterministic_surfaces"]
    runtime = fixture["runtime_surfaces"]
    if not deterministic or not runtime:
        fail("v3.4.2 owned-surface inventory is incomplete")
    for row in deterministic:
        if not isinstance(row, dict) or not all(
            isinstance(row.get(key), str) and row[key]
            for key in ("path", "file_type", "mode", "sha256")
        ):
            fail("v3.4.2 deterministic inventory row is malformed")
    for row in runtime:
        if not isinstance(row, dict) or not all(
            isinstance(row.get(key), str) and row[key]
            for key in ("path_pattern", "file_type", "schema", "hash_policy")
        ):
            fail("v3.4.2 runtime inventory row is malformed")
    try:
        ledger_rows = [json.loads(line) for line in V4_MIGRATION_LEDGER.read_text(encoding="utf-8").splitlines() if line]
    except FileNotFoundError:
        fail("v4 capability migration ledger is unavailable; migration preflight is blocked")
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"v4 capability migration ledger is unreadable: {exc}")
    if not ledger_rows or not all(isinstance(row, dict) for row in ledger_rows):
        fail("v4 capability migration ledger is malformed")
    return fixture, ledger_rows


@dataclass(frozen=True)
class W4RuntimeAPI:
    discussion_planner: Callable[[str, dict[str, str]], object]
    parse_index: Callable[[str], dict[str, object]]
    validate_currentness: Callable[[Path, dict[str, object]], None]
    is_eligible: Callable[[dict[str, object]], bool]


def _load_w4_runtime_api() -> W4RuntimeAPI:
    """Load W4's public migration and final-validation semantics."""

    try:
        info = W4_DISCUSSION_API.lstat()
    except OSError as exc:
        fail(f"W4 discussion migration API is unavailable: {exc}")
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        fail("W4 discussion migration API must be a regular source file")
    try:
        exports = runpy.run_path(str(W4_DISCUSSION_API), run_name="teamwork_init_w4_api")
    except Exception as exc:
        fail(f"cannot load the W4 discussion migration API: {exc}")
    planner = exports.get("plan_v342_discussion_migration")
    parse_index = exports.get("parse_index")
    validate_currentness = exports.get("validate_currentness")
    is_eligible = exports.get("_eligible")
    if not callable(planner):
        fail("W4 discussion migration API does not provide plan_v342_discussion_migration")
    if not callable(parse_index) or not callable(validate_currentness):
        fail("W4 artifact API does not provide final index/currentness validation")
    if not callable(is_eligible):
        fail("W4 artifact API does not provide canonical currentness eligibility")
    return W4RuntimeAPI(planner, parse_index, validate_currentness, is_eligible)


@dataclass(frozen=True)
class W4DiscussionMigrationPlan:
    writes: dict[str, str]
    deletes: tuple[str, ...]
    active_path: str | None


def _w4_discussion_plan(
    index_text: str,
    artifact_texts: dict[str, str],
    planner: Callable[[str, dict[str, str]], object],
) -> W4DiscussionMigrationPlan:
    try:
        raw_plan = planner(index_text, artifact_texts)
    except Exception as exc:
        fail(f"W4 discussion migration planning refused the project state: {exc}")
    if (
        not isinstance(raw_plan, dict)
        or set(raw_plan) != {"schema_version", "writes", "deletes", "active_path"}
        or raw_plan.get("schema_version") != 2
        or not isinstance(raw_plan.get("writes"), dict)
        or not isinstance(raw_plan.get("deletes"), list)
    ):
        fail("W4 discussion migration API returned a non-object change plan")
    writes: dict[str, str] = {}
    for path, text in raw_plan["writes"].items():
        if not isinstance(path, str) or not isinstance(text, str):
            fail("W4 discussion migration API returned a non-text write")
        pure = checked_relative(path, label="W4 discussion migration write path")
        if len(pure.parts) != 4 or pure.parts[:3] != ("docs", "teamwork", "discussion"):
            fail("W4 discussion migration write path is outside docs/teamwork/discussion/")
        if pure.name != "current.md" and DISCUSSION_ARCHIVE_NAME_RE.fullmatch(pure.name) is None:
            fail("W4 discussion migration write path has an unsupported name")
        writes[path] = text
    deletes: list[str] = []
    for path in raw_plan["deletes"]:
        if not isinstance(path, str) or path in deletes or path not in artifact_texts:
            fail("W4 discussion migration API returned an unsafe delete")
        pure = checked_relative(path, label="W4 discussion migration delete path")
        if len(pure.parts) != 4 or pure.parts[:3] != ("docs", "teamwork", "discussion"):
            fail("W4 discussion migration delete path is outside docs/teamwork/discussion/")
        if DISCUSSION_ARCHIVE_NAME_RE.fullmatch(pure.name) is None or path in writes:
            fail("W4 discussion migration delete path conflicts with its writes")
        deletes.append(path)
    active_path = raw_plan["active_path"]
    if active_path not in {None, DISCUSSION_CURRENT_PATH}:
        fail("W4 discussion migration API returned an unsupported active path")
    if active_path == DISCUSSION_CURRENT_PATH and active_path not in writes:
        fail("W4 discussion migration active path is missing from writes")
    return W4DiscussionMigrationPlan(writes, tuple(deletes), active_path)


def _indexed_discussion_paths(index: object) -> list[tuple[str, str]]:
    """Route indexed discussion inputs into the journal without parsing artifacts."""

    if not isinstance(index, dict) or not isinstance(index.get("entries"), list):
        fail("discussion migration index is missing its entries collection")
    paths: list[tuple[str, str]] = []
    seen: set[str] = set()
    for entry in index["entries"]:
        if not isinstance(entry, dict) or entry.get("kind") != "discussion":
            continue
        raw_path = entry.get("path")
        if not isinstance(raw_path, str):
            fail("discussion migration index entry has no string path")
        pure = checked_relative(raw_path, label="discussion migration path")
        if len(pure.parts) != 4 or pure.parts[:3] != ("docs", "teamwork", "discussion"):
            fail("discussion migration path must be directly under docs/teamwork/discussion/")
        if raw_path in seen:
            fail("discussion migration index has duplicate artifact paths")
        seen.add(raw_path)
        paths.append((raw_path, pure.name))
    return paths


def _repair_v342_discussion_index(index: object) -> str | None:
    """Remove v3 discussion bookkeeping after W4 has planned every artifact."""

    if not isinstance(index, dict) or not isinstance(index.get("active"), dict):
        fail("discussion migration index is missing its active collection")
    entries = index.get("entries")
    if not isinstance(entries, list):
        fail("discussion migration index is missing its entries collection")
    has_discussions = any(isinstance(entry, dict) and entry.get("kind") == "discussion" for entry in entries)
    active = index["active"]
    has_legacy_pointer = "discussion" in active
    legacy_pointer = active.get("discussion")
    if not has_discussions and not has_legacy_pointer:
        return None
    if legacy_pointer is not None and not isinstance(legacy_pointer, str):
        fail("discussion migration active.discussion must be null or a string")
    repaired = json.loads(json.dumps(index, ensure_ascii=False))
    repaired_active = repaired["active"]
    assert isinstance(repaired_active, dict)
    repaired_active.pop("discussion", None)
    repaired_entries = repaired["entries"]
    assert isinstance(repaired_entries, list)
    repaired["entries"] = [
        entry for entry in repaired_entries
        if not isinstance(entry, dict) or entry.get("kind") != "discussion"
    ]
    try:
        validator.validate_index(repaired, Path("docs/teamwork/index.json"))
    except validator.ValidationError as exc:
        fail(f"discussion migration index repair is invalid: {exc}")
    return json.dumps(repaired, ensure_ascii=False, indent=2) + "\n"


def _repair_discussion_anchor(text: str, marker: str, value: str, suffix: str) -> str:
    matches = list(re.finditer(rf"(?m)^{re.escape(marker)}[^\r\n]*$", text))
    replacement = f"{marker} {value}{suffix}"
    if len(matches) > 1:
        fail(f"ordinary-memory {marker[2:-1].lower()} anchor is ambiguous")
    if len(matches) == 1:
        match = matches[0]
        return text[: match.start()] + replacement + text[match.end() :]
    # Fresh v4 ordinary-memory templates deliberately omit these old v3
    # discussion anchors.  Only rewrite an anchor that is actually present;
    # Init must not reintroduce a cross-boundary pointer during a no-op run.
    return text


def _unfinished_w4_discussion_transaction(tree: InitTree) -> bool:
    """Recognize W4's v4 journal and the former parent-directory location."""

    return (
        ("discussion" in tree.fds and tree.stat("discussion", DISCUSSION_MARKER) is not None)
        or ("teamwork" in tree.fds and tree.stat("teamwork", DISCUSSION_MARKER) is not None)
    )


class InitTransaction:
    """A journaled project-only context update with exact preimage recovery."""

    DIRECTORY_LAYOUT = (
        ("root", "docs", "docs"),
        ("docs", "teamwork", "teamwork"),
        ("teamwork", "research", "research"),
        ("teamwork", "design", "design"),
        ("teamwork", "plans", "plans"),
        ("teamwork", "reports", "reports"),
        ("teamwork", "workflows", "workflows"),
    )

    def __init__(self, root: Path, args: argparse.Namespace) -> None:
        self.root = root
        self.args = args
        self.tree = InitTree(root)
        self.journal: dict[str, object] | None = None
        self.guards: dict[tuple[str, str], FdSnapshot] = {}

    def close(self) -> None:
        self.tree.close()

    def _guard(self, snapshot: FdSnapshot) -> None:
        if snapshot.exists:
            self.guards[(snapshot.parent, snapshot.name)] = snapshot

    def _verify_guards(self) -> None:
        for snapshot in self.guards.values():
            if snapshot.parent not in self.tree.fds:
                fail(f"transaction guard parent is unavailable: {snapshot.logical}")
            current = _snapshot(self.tree, snapshot.parent, snapshot.name, snapshot.logical)
            if not _same_snapshot(current, snapshot):
                fail(f"project input changed during transaction: {snapshot.logical}")

    def _open_existing_layout(self) -> list[dict[str, object]]:
        records: list[dict[str, object]] = []
        for parent, name, key in self.DIRECTORY_LAYOUT:
            if parent not in self.tree.fds:
                records.append({"parent": parent, "name": name, "key": key, "before": {"exists": False}, "after": None})
                continue
            records.append(_directory_record(self.tree, parent, name, key))
            if self.tree.stat(parent, name) is not None:
                self.tree.open_existing(parent, name, key)
        if "teamwork" in self.tree.fds:
            self.tree.lock_teamwork()
            self.tree.open_existing("teamwork", "discussion", "discussion")
        return records

    def _provision_directories(self, records: list[dict[str, object]], *, recovery: bool) -> None:
        for record in records:
            if set(record) != {"parent", "name", "key", "before", "after"}:
                fail("init journal directory record has invalid fields")
            parent, name, key = record["parent"], record["name"], record["key"]
            if not all(isinstance(value, str) and value for value in (parent, name, key)):
                fail("init journal directory record has invalid names")
            if (parent, name, key) not in self.DIRECTORY_LAYOUT:
                fail("init journal directory record is outside the owned layout")
            if parent not in self.tree.fds:
                if recovery and _directory_matches(None, record["before"]):
                    continue
                fail("init journal directory parent is unavailable")
            current = self.tree.stat(parent, name)
            before = record["before"]
            after = record["after"]
            if not _valid_directory_state(before) or (after is not None and not _valid_directory_state(after)):
                fail("init journal directory state is invalid")
            if isinstance(before, dict) and before["exists"]:
                if not _directory_matches(current, before):
                    fail(f"project directory changed before transaction: {name}")
            elif current is None:
                if recovery:
                    continue
                try:
                    os.mkdir(name, 0o755, dir_fd=self.tree.fds[parent])
                    os.fsync(self.tree.fds[parent])
                except OSError as exc:
                    fail(f"cannot create project directory {name}: {exc}")
                current = self.tree.stat(parent, name)
                assert current is not None
                record["after"] = _directory_state(current)
                self._write_journal()
            elif after is None or not _directory_matches(current, after):
                fail(f"project directory appeared outside the transaction: {name}")
            if key not in self.tree.fds:
                self.tree.open_existing(parent, name, key)
        if "teamwork" in self.tree.fds:
            self.tree.lock_teamwork()
        self.tree.verify()

    def _write_journal(self) -> bytes:
        if self.journal is None:
            fail("cannot write a missing init journal")
        data = _journal_bytes(self.journal)
        _write_marker_at(self.tree, "root", data)
        if "teamwork" in self.tree.fds:
            _write_marker_at(self.tree, "teamwork", data)
        return data

    def _clear_mirrored_journal(self) -> None:
        """Remove a valid mirror while treating the root journal as authority.

        The two durable markers cannot be updated in one filesystem operation.
        A hard exit after the root replacement and before the docs/teamwork
        replacement therefore leaves an older, but still valid, mirror.  That
        is an expected recovery state, not an external ABA change: the root
        marker is the sole recovery authority and the mirror is only a W4
        interlock.  Reject malformed mirrors, but remove either generation
        once the root-owned transaction is completing or rolling back.
        """

        if "teamwork" not in self.tree.fds:
            return
        marker = _read_marker_at(self.tree, "teamwork")
        if marker is None:
            return
        value, data = marker
        _parse_journal(value)
        _remove_marker_at(self.tree, "teamwork", data)

    def _clear_journal(self) -> None:
        if self.journal is None:
            return
        data = _journal_bytes(self.journal)
        self._clear_mirrored_journal()
        _remove_marker_at(self.tree, "root", data)

    def _memory_snapshots(self) -> tuple[dict[str, FdSnapshot], dict[str, object] | None]:
        if "teamwork" not in self.tree.fds:
            return {}, None
        snapshots = {
            name: _snapshot(self.tree, "teamwork", name, f"docs/teamwork/{name}")
            for name in ("index.json", "current.md", "README.md")
        }
        present = [snapshot.exists for snapshot in snapshots.values()]
        if any(present) and not all(present):
            fail("partial Teamwork runtime initialization; all three ordinary-memory anchors are required")
        if all(present):
            index = snapshots["index.json"]
            assert index.data is not None
            try:
                value = json.loads(index.data)
            except json.JSONDecodeError as exc:
                fail(f"cannot parse docs/teamwork/index.json: {exc}")
            reader = validator.SafeProjectReader(self.root)
            try:
                validator.validate_index(value, self.root / "docs/teamwork/index.json", reader, migration_read=True)
            finally:
                reader.close()
            for snapshot in snapshots.values():
                self._guard(snapshot)
            return snapshots, value
        return snapshots, None

    def _discussion_migration_candidates(
        self,
        memory: dict[str, FdSnapshot],
        index: dict[str, object],
    ) -> list[tuple[str, str, str, bytes | None]]:
        w4 = _load_w4_runtime_api()
        index_snapshot = memory["index.json"]
        assert index_snapshot.data is not None
        try:
            index_text = index_snapshot.data.decode("utf-8")
        except UnicodeDecodeError as exc:
            fail(f"docs/teamwork/index.json must be UTF-8: {exc}")
        paths = _indexed_discussion_paths(index)
        artifacts: dict[str, str] = {}
        if paths:
            if "discussion" not in self.tree.fds:
                if self.tree.open_existing("teamwork", "discussion", "discussion") is None:
                    fail("indexed discussion artifacts require docs/teamwork/discussion/")
            for logical, name in paths:
                snapshot = _snapshot(self.tree, "discussion", name, logical)
                if not snapshot.exists or snapshot.data is None:
                    fail(f"indexed discussion artifact is missing: {logical}")
                self._guard(snapshot)
                try:
                    artifacts[logical] = snapshot.data.decode("utf-8")
                except UnicodeDecodeError as exc:
                    fail(f"indexed discussion artifact must be UTF-8: {logical}: {exc}")
        plan = _w4_discussion_plan(index_text, artifacts, w4.discussion_planner)
        candidates: list[tuple[str, str, str, bytes | None]] = [
            ("discussion", PurePosixPath(path).name, path, text.encode("utf-8"))
            for path, text in sorted(plan.writes.items())
        ]
        candidates.extend(
            ("discussion", PurePosixPath(path).name, path, None)
            for path in plan.deletes
        )
        repaired_index = _repair_v342_discussion_index(index)
        candidate_index_text = index_text if repaired_index is None else repaired_index
        try:
            candidate_index = json.loads(candidate_index_text)
        except json.JSONDecodeError as exc:  # pragma: no cover - the repair validates before returning
            fail(f"cannot parse candidate Teamwork index: {exc}")
        plan_repair = self._repair_v342_plan_currentness(candidate_index, w4)
        if plan_repair is not None:
            candidate_index = plan_repair
            candidate_index_text = json.dumps(candidate_index, ensure_ascii=False, indent=2) + "\n"
        try:
            parsed_candidate = w4.parse_index(candidate_index_text)
            w4.validate_currentness(self.root, parsed_candidate)
        except Exception as exc:
            fail(f"W4 final artifact-index validation refused the project state: {exc}")
        if repaired_index is not None or plan_repair is not None:
            candidates.append(
                ("teamwork", "index.json", "docs/teamwork/index.json", candidate_index_text.encode("utf-8"))
            )
        current = memory["current.md"]
        readme = memory["README.md"]
        assert current.data is not None and readme.data is not None
        try:
            current_text = current.data.decode("utf-8")
            readme_text = readme.data.decode("utf-8")
        except UnicodeDecodeError as exc:
            fail(f"ordinary-memory anchor file must be UTF-8: {exc}")
        repaired_current = _repair_discussion_anchor(
            current_text, "- Active discussion:", "none", "."
        )
        repaired_readme = _repair_discussion_anchor(
            readme_text, "- Active discussion route:", "none", ""
        )
        if repaired_current != current_text:
            candidates.append(("teamwork", "current.md", "docs/teamwork/current.md", repaired_current.encode("utf-8")))
        if repaired_readme != readme_text:
            candidates.append(("teamwork", "README.md", "docs/teamwork/README.md", repaired_readme.encode("utf-8")))
        return candidates

    def _repair_v342_plan_currentness(
        self,
        index: object,
        w4: W4RuntimeAPI,
    ) -> dict[str, object] | None:
        if not isinstance(index, dict) or not isinstance(index.get("active"), dict):
            fail("plan-currentness migration index is missing its active collection")
        entries = index.get("entries")
        if not isinstance(entries, list):
            fail("plan-currentness migration index is missing its entries collection")
        active = index["active"]
        assert isinstance(active, dict)
        eligible_positions = [
            position
            for position, entry in enumerate(entries)
            if isinstance(entry, dict)
            and entry.get("kind") == "plan"
            and w4.is_eligible(entry)
        ]
        raw_plan = active.get("plan")
        if raw_plan is None:
            if eligible_positions:
                fail("active.plan is null while eligible legacy Plan entries exist")
            return None
        if not isinstance(raw_plan, str):
            fail("active.plan must be null or a normalized Plan path")
        pure = checked_relative(raw_plan, label="active.plan")
        if (
            len(pure.parts) != 4
            or pure.parts[:3] != ("docs", "teamwork", "plans")
            or pure.suffix != ".md"
            or pure.name == ".md"
        ):
            fail("active.plan must be directly under docs/teamwork/plans/ with a .md name")
        matches = [
            position
            for position, entry in enumerate(entries)
            if isinstance(entry, dict) and entry.get("path") == raw_plan
        ]
        if len(matches) != 1:
            fail("active.plan must identify exactly one index row")
        target_position = matches[0]
        if target_position not in eligible_positions:
            fail("active.plan target must be an eligible current Plan entry")
        if "plans" not in self.tree.fds:
            fail("active.plan artifact directory is missing")
        artifact = _snapshot(self.tree, "plans", pure.name, raw_plan)
        if not artifact.exists:
            fail(f"active.plan artifact is missing: {raw_plan}")
        self._guard(artifact)
        demotions = [position for position in eligible_positions if position != target_position]
        if not demotions:
            return None
        repaired = json.loads(json.dumps(index, ensure_ascii=False))
        repaired_entries = repaired["entries"]
        assert isinstance(repaired_entries, list)
        for position in demotions:
            entry = repaired_entries[position]
            assert isinstance(entry, dict)
            entry["currentness"] = "historical"
        return repaired

    def _planned_files(self) -> list[dict[str, object]]:
        self.guards.clear()
        memory, index = self._memory_snapshots()
        label = project_label(self.root, self.args.project_label)
        rendered = render_memory_files(self.args.today, label)
        candidates: list[tuple[str, str, str, bytes | None]] = []
        if not memory:
            candidates.extend(
                ("teamwork", PurePosixPath(path).name, path, text.encode("utf-8"))
                for path, text in rendered.items()
            )
        else:
            assert index is not None
            candidates.extend(self._discussion_migration_candidates(memory, index))

        agents = _snapshot(self.tree, "root", "AGENTS.md", "AGENTS.md")
        agents_text = "" if not agents.exists else _snapshot_text(agents, "AGENTS.md")
        agents_after = _require_known_managed_block(
            agents_text,
            MANAGED_START,
            MANAGED_END,
            managed_agents_block(self.tree, label),
            prefix="# Repository Guidelines\n",
            known_heading="Teamwork Project Instructions",
        ).encode("utf-8")
        candidates.append(("root", "AGENTS.md", "AGENTS.md", agents_after))

        ignored = _snapshot(self.tree, "root", ".gitignore", ".gitignore")
        ignored_text = "" if not ignored.exists else _snapshot_text(ignored, ".gitignore")
        ignored_after = _require_known_managed_block(
            ignored_text,
            IGNORE_START,
            IGNORE_END,
            GITIGNORE_BLOCK,
            known_heading="Teamwork local runtime state",
        ).encode("utf-8")
        candidates.append(("root", ".gitignore", ".gitignore", ignored_after))

        files: list[dict[str, object]] = []
        seen_targets: set[tuple[str, str]] = set()
        for parent, name, logical, after in candidates:
            target = (parent, name)
            if target in seen_targets:
                fail(f"init transaction has conflicting planned outputs: {logical}")
            seen_targets.add(target)
            before = _snapshot(self.tree, parent, name, logical) if parent in self.tree.fds else FdSnapshot(parent, name, logical, False)
            if after is None:
                if not before.exists:
                    fail(f"W4 discussion migration delete target is missing: {logical}")
                files.append(
                    {
                        "parent": parent,
                        "name": name,
                        "logical": logical,
                        "operation": "delete",
                        "before": _snapshot_record(before),
                        "after_sha256": None,
                        "after_mode": None,
                        "after_bytes_b64": None,
                        "stage": None,
                        "backup": None,
                        "installed": None,
                    }
                )
                continue
            if before.exists and before.data == after:
                continue
            mode = 0o644 if before.mode is None else before.mode
            files.append(
                {
                    "parent": parent,
                    "name": name,
                    "logical": logical,
                    "operation": "write",
                    "before": _snapshot_record(before),
                    "after_sha256": hashlib.sha256(after).hexdigest(),
                    "after_mode": mode,
                    "after_bytes_b64": base64.b64encode(after).decode("ascii"),
                    "stage": None,
                    "backup": None,
                    "installed": None,
                }
            )
        written = {(str(record["parent"]), str(record["name"])) for record in files}
        self.guards = {
            key: snapshot for key, snapshot in self.guards.items() if key not in written
        }
        return files

    @staticmethod
    def _file_from_record(
        record: dict[str, object],
    ) -> tuple[FdSnapshot, bytes | None, int | None, str]:
        required = {
            "parent", "name", "logical", "operation", "before", "after_sha256", "after_mode",
            "after_bytes_b64", "stage", "backup", "installed",
        }
        if set(record) != required:
            fail("init journal file record has invalid fields")
        parent, name, logical = record["parent"], record["name"], record["logical"]
        if not all(isinstance(value, str) and value for value in (parent, name, logical)):
            fail("init journal file record has invalid names")
        assert isinstance(parent, str) and isinstance(name, str) and isinstance(logical, str)
        _validate_journal_target(parent, name, logical)
        if parent == "plans":
            fail("init journal cannot mutate an active Plan artifact")
        before = _record_snapshot(parent, name, logical, record["before"])
        operation = record["operation"]
        if operation not in {"write", "delete"}:
            fail("init journal operation is invalid")
        encoded, digest, mode = record["after_bytes_b64"], record["after_sha256"], record["after_mode"]
        after: bytes | None
        if operation == "write":
            if not isinstance(encoded, str) or not isinstance(digest, str) or HASH_RE.fullmatch(digest) is None:
                fail("init journal postimage is invalid")
            if not isinstance(mode, int) or mode < 0:
                fail("init journal postimage mode is invalid")
            try:
                after = base64.b64decode(encoded.encode("ascii"), validate=True)
            except (ValueError, UnicodeEncodeError) as exc:
                fail(f"init journal postimage bytes are invalid: {exc}")
            if hashlib.sha256(after).hexdigest() != digest:
                fail("init journal postimage hash does not match bytes")
        else:
            if not before.exists or any(value is not None for value in (encoded, digest, mode)):
                fail("init journal delete record is invalid")
            after = None
        identities: dict[str, dict[str, object] | None] = {}
        for key in ("stage", "backup", "installed"):
            value = record[key]
            if value is None:
                identities[key] = None
                continue
            if (
                not isinstance(value, dict)
                or set(value) != {"name", "device", "inode"}
                or not isinstance(value["name"], str)
                or not isinstance(value["device"], int)
                or not isinstance(value["inode"], int)
            ):
                fail(f"init journal {key} identity is invalid")
            identities[key] = value
        stage = identities["stage"]
        backup = identities["backup"]
        installed = identities["installed"]
        if stage is not None:
            stage_name = stage["name"]
            assert isinstance(stage_name, str)
            if (
                operation != "write"
                or re.fullmatch(
                    rf"\.{re.escape(before.name)}\.teamwork-init-stage-[0-9]+-[0-9]+",
                    stage_name,
                )
                is None
            ):
                fail("init journal staging identity has an unsafe name")
        if backup is not None:
            backup_name = backup["name"]
            assert isinstance(backup_name, str)
            if (
                not before.exists
                or re.fullmatch(
                    rf"\.{re.escape(before.name)}\.teamwork-init-backup-[0-9]+-[0-9]+",
                    backup_name,
                )
                is None
                or (backup["device"], backup["inode"]) != (before.device, before.inode)
            ):
                fail("init journal backup identity is invalid")
        if installed is not None:
            if installed["name"] != before.name:
                fail("init journal installed identity has an unsafe name")
            if operation == "write":
                if stage is None or (installed["device"], installed["inode"]) != (
                    stage["device"], stage["inode"]
                ):
                    fail("init journal installed write identity is invalid")
            elif (installed["device"], installed["inode"]) != (before.device, before.inode):
                fail("init journal installed delete identity is invalid")
        return before, after, mode, operation

    def _stage_records(self, records: list[dict[str, object]]) -> None:
        for record in records:
            before, after, mode, operation = self._file_from_record(record)
            if before.parent not in self.tree.fds:
                fail("init transaction target parent is unavailable")
            if operation == "write":
                assert after is not None and mode is not None
                stage = _temp_name(self.tree, before.parent, before.name, "stage")
                stage_info = _write_temp(self.tree, before.parent, stage, after, mode)
                record["stage"] = {"name": stage, "device": stage_info.st_dev, "inode": stage_info.st_ino}
            if before.exists:
                backup = _temp_name(self.tree, before.parent, before.name, "backup")
                # Journal the original identity before moving it.  On rollback we
                # rename this exact inode back rather than recreating equivalent
                # bytes, so an interrupted update restores the real preimage.
                assert before.device is not None and before.inode is not None
                record["backup"] = {"name": backup, "device": before.device, "inode": before.inode}
            self._write_journal()
        assert self.journal is not None
        self.journal["phase"] = "prepared"
        self._write_journal()
        if os.environ.get("TEAMWORK_TEST_HARD_EXIT_INIT_PHASE") == "prepared":
            os._exit(86)

    def _install_records(self, records: list[dict[str, object]]) -> None:
        raw = os.environ.get("TEAMWORK_TEST_FAIL_INIT_REPLACE_AT")
        hard_raw = os.environ.get("TEAMWORK_TEST_HARD_EXIT_INIT_REPLACE_AT")
        try:
            fail_at = None if raw is None else int(raw)
            hard_at = None if hard_raw is None else int(hard_raw)
        except ValueError:
            fail("init replacement failure injection must be an integer")
        if fail_at is not None and not 1 <= fail_at <= len(records):
            fail("init replacement failure injection is outside the planned replacements")
        if hard_at is not None and not 1 <= hard_at <= len(records):
            fail("hard-exit replacement injection is outside the planned replacements")
        assert self.journal is not None
        self.journal["phase"] = "committing"
        self._write_journal()
        if os.environ.get("TEAMWORK_TEST_HARD_EXIT_INIT_PHASE") == "committing":
            os._exit(86)
        for ordinal, record in enumerate(records, start=1):
            self._verify_guards()
            before, after, mode, operation = self._file_from_record(record)
            current = _snapshot(self.tree, before.parent, before.name, before.logical)
            if not _same_snapshot(current, before):
                fail(f"project output changed before transaction write: {before.logical}")
            if fail_at == ordinal:
                raise OSError(f"injected init replacement failure at {ordinal}")
            stage = record["stage"]
            if operation == "write":
                if not isinstance(stage, dict):
                    fail("transaction write is missing its staging file")
                stage_name = stage["name"]
                assert isinstance(stage_name, str)
                stage_info = self.tree.stat(before.parent, stage_name)
                if stage_info is None or (stage_info.st_dev, stage_info.st_ino) != (stage["device"], stage["inode"]):
                    fail("transaction staging file changed before install")
            elif stage is not None:
                fail("transaction delete unexpectedly has a staging file")
            try:
                if before.exists:
                    backup = record["backup"]
                    if not isinstance(backup, dict):
                        fail("transaction is missing its original-file reservation")
                    backup_name = backup["name"]
                    if not isinstance(backup_name, str) or self.tree.stat(before.parent, backup_name) is not None:
                        fail("transaction original-file reservation changed before install")
                    # Move, rather than copy, the old target.  The journal already
                    # names its original identity, so recovery can distinguish a
                    # half-installed replacement from an external ABA change.
                    os.replace(
                        before.name,
                        backup_name,
                        src_dir_fd=self.tree.fds[before.parent],
                        dst_dir_fd=self.tree.fds[before.parent],
                    )
                    os.fsync(self.tree.fds[before.parent])
                    backup_snapshot = _snapshot(self.tree, before.parent, backup_name, before.logical)
                    if (
                        not _same_file_preimage(backup_snapshot, before)
                        or (backup_snapshot.device, backup_snapshot.inode)
                        != (backup["device"], backup["inode"])
                    ):
                        fail("transaction original-file backup changed during install")
                if operation == "write":
                    assert isinstance(stage, dict)
                    stage_name = stage["name"]
                    assert isinstance(stage_name, str)
                    os.replace(
                        stage_name,
                        before.name,
                        src_dir_fd=self.tree.fds[before.parent],
                        dst_dir_fd=self.tree.fds[before.parent],
                    )
                    os.fsync(self.tree.fds[before.parent])
            except OSError as exc:
                fail(f"cannot install transaction output {before.logical}: {exc}")
            final = _snapshot(self.tree, before.parent, before.name, before.logical)
            if operation == "write":
                assert after is not None and mode is not None and isinstance(stage, dict)
                if (
                    not final.exists
                    or final.data != after
                    or final.mode != mode
                    or final.device != stage["device"]
                    or final.inode != stage["inode"]
                ):
                    fail(f"transaction output readback differs from intended bytes: {before.logical}")
                record["installed"] = {"name": before.name, "device": final.device, "inode": final.inode}
            else:
                if final.exists or not before.exists:
                    fail(f"transaction delete readback differs from intended absence: {before.logical}")
                assert before.device is not None and before.inode is not None
                record["installed"] = {"name": before.name, "device": before.device, "inode": before.inode}
            self._write_journal()
            if hard_at == ordinal:
                os._exit(86)
        self.journal["phase"] = "committed"
        self._write_journal()
        if os.environ.get("TEAMWORK_TEST_HARD_EXIT_INIT_PHASE") == "committed":
            os._exit(86)

    def _postcommit_cleanup(self, records: list[dict[str, object]]) -> None:
        for record in records:
            before, _after, _mode, _operation = self._file_from_record(record)
            backup = record["backup"]
            if backup is not None:
                assert isinstance(backup, dict)
                _unlink_verified(
                    self.tree,
                    before.parent,
                    str(backup["name"]),
                    (int(backup["device"]), int(backup["inode"])),
                )
        if os.environ.get("TEAMWORK_TEST_HARD_EXIT_INIT_PHASE") == "cleanup":
            os._exit(86)

    def _rollback(self, records: list[dict[str, object]], directories: list[dict[str, object]]) -> None:
        # The root journal remains the recovery authority while the mirrored
        # docs/teamwork marker is removed so a transaction-created memory
        # directory can become provably empty and be rolled back.
        if self.journal is not None and "teamwork" in self.tree.fds:
            self._clear_mirrored_journal()
        for record in reversed(records):
            before, after, mode, operation = self._file_from_record(record)
            if before.parent not in self.tree.fds:
                if (
                    not before.exists
                    and record["stage"] is None
                    and record["backup"] is None
                    and record["installed"] is None
                ):
                    continue
                fail("init rollback target parent is unavailable")
            current = _snapshot(self.tree, before.parent, before.name, before.logical)
            stage = record["stage"]
            backup = record["backup"]

            def backup_matches_preimage() -> bool:
                if not isinstance(backup, dict):
                    return False
                backup_name = backup["name"]
                assert isinstance(backup_name, str)
                snapshot = _snapshot(self.tree, before.parent, backup_name, before.logical)
                return (
                    snapshot.exists
                    and _same_file_preimage(snapshot, before)
                    and (snapshot.device, snapshot.inode)
                    == (backup["device"], backup["inode"])
                )

            def restore_backup() -> None:
                if not backup_matches_preimage():
                    fail("init rollback backup changed before restoration")
                assert isinstance(backup, dict)
                backup_name = backup["name"]
                assert isinstance(backup_name, str)
                try:
                    os.replace(
                        backup_name,
                        before.name,
                        src_dir_fd=self.tree.fds[before.parent],
                        dst_dir_fd=self.tree.fds[before.parent],
                    )
                    os.fsync(self.tree.fds[before.parent])
                except OSError as exc:
                    fail(f"cannot restore transaction preimage {before.logical}: {exc}")

            if operation == "write":
                assert after is not None and mode is not None
                installed = record["installed"]
                is_after = current.exists and current.data == after and current.mode == mode
                if installed is not None:
                    assert isinstance(installed, dict)
                    is_after = is_after and (current.device, current.inode) == (
                        installed["device"], installed["inode"]
                    )
                elif stage is not None:
                    assert isinstance(stage, dict)
                    is_after = is_after and (current.device, current.inode) == (
                        stage["device"], stage["inode"]
                    )
                if is_after:
                    if before.exists:
                        restore_backup()
                    else:
                        try:
                            os.unlink(before.name, dir_fd=self.tree.fds[before.parent])
                            os.fsync(self.tree.fds[before.parent])
                        except OSError as exc:
                            fail(f"cannot restore transaction preimage {before.logical}: {exc}")
                elif before.exists:
                    if backup_matches_preimage() and not current.exists:
                        restore_backup()
                    elif not _same_snapshot(current, before):
                        fail(f"init rollback refused because output changed externally: {before.logical}")
                elif not _same_snapshot(current, before):
                    fail(f"init rollback refused because output changed externally: {before.logical}")
            else:
                # A delete stages no replacement.  Its preimage was atomically
                # renamed to the reserved backup name, so restoring that inode
                # proves we did not recreate merely equivalent bytes.
                assert before.exists and after is None and stage is None
                if backup_matches_preimage() and not current.exists:
                    restore_backup()
                elif not _same_snapshot(current, before):
                    fail(f"init rollback refused because output changed externally: {before.logical}")
            stage = record["stage"]
            if stage is not None:
                assert isinstance(stage, dict)
                _unlink_verified(
                    self.tree,
                    before.parent,
                    str(stage["name"]),
                    (int(stage["device"]), int(stage["inode"])),
                )
            backup = record["backup"]
            if backup is not None:
                assert isinstance(backup, dict)
                _unlink_verified(
                    self.tree,
                    before.parent,
                    str(backup["name"]),
                    (int(backup["device"]), int(backup["inode"])),
                )
        for record in reversed(directories):
            before, after = record["before"], record["after"]
            if not isinstance(before, dict) or before.get("exists") or after is None:
                continue
            parent, name, key = record["parent"], record["name"], record["key"]
            if not isinstance(parent, str) or not isinstance(name, str) or not isinstance(key, str):
                fail("init rollback directory record is malformed")
            if parent not in self.tree.fds:
                continue
            current = self.tree.stat(parent, name)
            if not _directory_matches(current, after):
                fail(f"init rollback directory changed externally: {name}")
            assert key in self.tree.fds
            try:
                if os.listdir(self.tree.fds[key]):
                    fail(f"init rollback directory is no longer empty: {name}")
                os.close(self.tree.fds.pop(key))
                self.tree.identities.pop(key, None)
                os.rmdir(name, dir_fd=self.tree.fds[parent])
                os.fsync(self.tree.fds[parent])
            except OSError as exc:
                fail(f"cannot remove transaction-created directory {name}: {exc}")

    def run(self) -> None:
        directories = self._open_existing_layout()
        try:
            files = self._planned_files()
            if not files and all(isinstance(record["before"], dict) and record["before"].get("exists") for record in directories):
                return
            self.journal = {
                "schema_version": JOURNAL_SCHEMA_VERSION,
                "owner": "teamwork-init",
                "phase": "preparing",
                "directories": directories,
                "files": files,
                "guards": [_guard_record(snapshot) for snapshot in self.guards.values()],
                "codegraph": "separate-consented-phase",
            }
            self._write_journal()
            if os.environ.get("TEAMWORK_TEST_HARD_EXIT_INIT_PHASE") == "preparing":
                os._exit(86)
            self._provision_directories(directories, recovery=False)
            self._write_journal()
            self._verify_guards()
            self._stage_records(files)
            self._install_records(files)
            self._postcommit_cleanup(files)
            self._clear_journal()
            self.journal = None
            self._validate_poststate()
        except BaseException as original:
            if isinstance(original, SystemExit):
                raise
            if self.journal is None:
                raise
            try:
                self._rollback(files if "files" in locals() else [], directories)
                self._clear_journal()
                self.journal = None
            except BaseException as rollback:
                fail(f"init transaction rollback was incomplete; journal preserved: {original}; {rollback}")
            if isinstance(original, InitError):
                raise
            fail(f"init transaction failed and exact prestate was restored: {original}")

    def _validate_poststate(self) -> None:
        if "teamwork" not in self.tree.fds:
            fail("Teamwork memory directory is missing after initialization")
        index = _snapshot(self.tree, "teamwork", "index.json", "docs/teamwork/index.json")
        assert index.exists and index.data is not None
        try:
            value = json.loads(index.data)
        except json.JSONDecodeError as exc:
            fail(f"cannot parse post-init index: {exc}")
        reader = validator.SafeProjectReader(self.root)
        try:
            validator.validate_index(value, self.root / "docs/teamwork/index.json", reader)
        finally:
            reader.close()
        memory = {
            "index.json": index,
            "current.md": _snapshot(self.tree, "teamwork", "current.md", "docs/teamwork/current.md"),
            "README.md": _snapshot(self.tree, "teamwork", "README.md", "docs/teamwork/README.md"),
        }
        if not all(snapshot.exists for snapshot in memory.values()):
            fail("ordinary-memory anchors are missing after initialization")
        if self._discussion_migration_candidates(memory, value):
            fail("post-init discussion migration or anchor repair remains pending")
        self.tree.verify()


def _parse_journal(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != {
        "schema_version", "owner", "phase", "directories", "files", "guards", "codegraph"
    }:
        fail("init journal fields are invalid")
    if value["schema_version"] != JOURNAL_SCHEMA_VERSION or value["owner"] != "teamwork-init":
        fail("init journal owner or schema is unsupported")
    if value["phase"] not in {"preparing", "prepared", "committing", "committed"}:
        fail("init journal phase is invalid")
    if (
        not isinstance(value["directories"], list)
        or not isinstance(value["files"], list)
        or not isinstance(value["guards"], list)
    ):
        fail("init journal changes are invalid")
    if value["codegraph"] != "separate-consented-phase":
        fail("init journal CodeGraph phase is invalid")
    return value


def _recover_init_transaction(root: Path) -> None:
    tree = InitTree(root)
    try:
        root_marker = _read_marker_at(tree, "root")
        docs = tree.open_existing("root", "docs", "docs")
        if docs is not None:
            tree.open_existing("docs", "teamwork", "teamwork")
        if "teamwork" in tree.fds:
            tree.open_existing("teamwork", "discussion", "discussion")
            if _unfinished_w4_discussion_transaction(tree):
                fail("an unfinished W4 discussion transaction blocks Init recovery")
        if root_marker is None:
            if "teamwork" in tree.fds and _read_marker_at(tree, "teamwork") is not None:
                fail("orphaned docs/teamwork init journal exists without the root recovery journal")
            return
        raw, _root_bytes = root_marker
        journal = _parse_journal(raw)
        txn = object.__new__(InitTransaction)
        txn.root = root
        txn.args = argparse.Namespace()
        txn.tree = tree
        txn.journal = journal
        directories = journal["directories"]
        files = journal["files"]
        guards = journal["guards"]
        assert isinstance(directories, list) and isinstance(files, list) and isinstance(guards, list)
        txn._provision_directories(directories, recovery=True)
        if "teamwork" in tree.fds:
            mirror = _read_marker_at(tree, "teamwork")
            if mirror is not None:
                # Root is the recovery authority.  The mirror may be the
                # immediately preceding valid generation if a hard exit split
                # the two marker replacements; it remains only an interlock
                # until recovery clears it.
                _parse_journal(mirror[0])
        for record in files:
            if not isinstance(record, dict):
                fail("init journal file record is invalid")
            InitTransaction._file_from_record(record)
        for record in guards:
            snapshot = _guard_from_record(record)
            if snapshot.parent not in tree.fds:
                fail("init journal guard target parent is unavailable")
            current = _snapshot(tree, snapshot.parent, snapshot.name, snapshot.logical)
            if not _same_snapshot(current, snapshot):
                fail(f"init journal guard changed externally: {snapshot.logical}")
        if journal["phase"] == "committed":
            for record in files:
                assert isinstance(record, dict)
                before, after, mode, operation = InitTransaction._file_from_record(record)
                if before.parent not in tree.fds:
                    fail("committed init journal target parent is unavailable")
                current = _snapshot(tree, before.parent, before.name, before.logical)
                installed = record["installed"]
                if not isinstance(installed, dict):
                    fail(f"committed init transaction has no installed identity: {before.logical}")
                if operation == "write":
                    if (
                        not current.exists
                        or current.data != after
                        or current.mode != mode
                        or (current.device, current.inode)
                        != (installed.get("device"), installed.get("inode"))
                    ):
                        fail(f"committed init transaction output changed before recovery: {before.logical}")
                else:
                    assert before.exists and after is None and mode is None
                    if (
                        current.exists
                        or installed.get("name") != before.name
                        or (installed.get("device"), installed.get("inode"))
                        != (before.device, before.inode)
                    ):
                        fail(f"committed init transaction delete changed before recovery: {before.logical}")
            txn._postcommit_cleanup(files)
            txn._clear_journal()
            txn.journal = None
        else:
            txn._rollback(files, directories)
            txn._clear_journal()
            txn.journal = None
    finally:
        tree.close()


def _preflight_runtime(root: Path) -> None:
    """Read-only project checks after any interrupted transaction is recovered."""

    tree = InitTree(root)
    try:
        tree.open_existing("root", "docs", "docs")
        if "docs" in tree.fds:
            tree.open_existing("docs", "teamwork", "teamwork")
        if "teamwork" not in tree.fds:
            return
        tree.lock_teamwork()
        tree.open_existing("teamwork", "discussion", "discussion")
        if _unfinished_w4_discussion_transaction(tree):
            fail("an unfinished W4 discussion transaction marker exists")
        for name in ("index.json", "current.md", "README.md"):
            _snapshot(tree, "teamwork", name, f"docs/teamwork/{name}")
        index = _snapshot(tree, "teamwork", "index.json", "docs/teamwork/index.json")
        if index.exists:
            assert index.data is not None
            try:
                value = json.loads(index.data)
            except json.JSONDecodeError as exc:
                fail(f"cannot parse docs/teamwork/index.json: {exc}")
            reader = validator.SafeProjectReader(root)
            try:
                validator.validate_index(value, root / "docs/teamwork/index.json", reader, migration_read=True)
            finally:
                reader.close()
        tree.verify()
    finally:
        tree.close()


def preflight(root: Path) -> None:
    _recover_init_transaction(root)
    _preflight_runtime(root)


def _capability_matrix() -> dict[str, object]:
    fixture, ledger = _load_v342_authority()
    deterministic = fixture["deterministic_surfaces"]
    runtime = fixture["runtime_surfaces"]
    assert isinstance(deterministic, list) and isinstance(runtime, list)
    return {
        "schema_version": 1,
        "mode": "full-bootstrap",
        "sources": {
            "v342_owned_surfaces": str(V342_OWNED_SURFACES.relative_to(REPOSITORY_ROOT)),
            "v4_migration_ledger": str(V4_MIGRATION_LEDGER.relative_to(REPOSITORY_ROOT)),
        },
        "published_surface_counts": {"deterministic": len(deterministic), "runtime": len(runtime)},
        "migration_ledger_rows": len(ledger),
        "promotion": "external memory and docs-graph remain candidates without explicit Root-authorized gates",
    }


def _check_candidate_flags(args: argparse.Namespace) -> None:
    candidates = [value for value in (args.candidate_memory, args.candidate_docs_graph) if value]
    if not candidates:
        return
    for raw in candidates:
        path = Path(raw)
        try:
            info = path.lstat()
        except OSError as exc:
            fail(f"candidate input cannot be inspected: {path}: {exc}")
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            fail(f"candidate input must be a non-symlink regular file: {path}")
    if args.promote_candidates:
        if not args.full_bootstrap or not args.root_authorized_promotion:
            fail("candidate promotion requires explicit full bootstrap and Root authority")
        fail(
            "candidate promotion is blocked until a W4-owned currentness, scope, evidence, "
            "privacy, and protected-data validation API is available"
        )


def command_write_context(root: Path, args: argparse.Namespace) -> None:
    _check_candidate_flags(args)
    preflight(root)
    transaction = InitTransaction(root, args)
    try:
        transaction.run()
    finally:
        transaction.close()
    if args.full_bootstrap:
        print(json.dumps(_capability_matrix(), ensure_ascii=False, sort_keys=True))


def command_validate(root: Path, _args: argparse.Namespace) -> None:
    preflight(root)
    transaction = InitTransaction(root, _args)
    try:
        transaction._open_existing_layout()
        if "teamwork" not in transaction.tree.fds:
            fail("docs/teamwork is not initialized")
        memory, index = transaction._memory_snapshots()
        if not memory or index is None:
            fail("docs/teamwork ordinary-memory anchors are incomplete")
        if transaction._discussion_migration_candidates(memory, index):
            fail("W4 discussion migration or ordinary-memory anchor repair is pending")
        transaction.tree.verify()
    finally:
        transaction.close()


def command_codegraph(root: Path, args: argparse.Namespace) -> None:
    command = list(args.command)
    if command[:1] == ["--"]:
        command = command[1:]
    if not command:
        fail("codegraph requires an explicit command")
    result = subprocess.run(command, cwd=root, check=False)
    if result.returncode != 0:
        fail(f"CodeGraph separate phase failed with exit status {result.returncode}")


def command_v342_preflight(_root: Path, _args: argparse.Namespace) -> None:
    fixture, ledger = _load_v342_authority()
    print(
        json.dumps(
            {
                "ok": True,
                "deterministic_surfaces": len(fixture["deterministic_surfaces"]),
                "runtime_surfaces": len(fixture["runtime_surfaces"]),
                "ledger_rows": len(ledger),
                "skill_subset_authoritative": False,
            },
            sort_keys=True,
        )
    )


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--project-root", default=os.environ.get("TEAMWORK_PROJECT_ROOT", os.getcwd()))
    sub = result.add_subparsers(dest="action", required=True)
    sub.add_parser("preflight")
    sub.add_parser("print-root")
    write = sub.add_parser("write-context")
    write.add_argument("--today", default=date.today().isoformat())
    write.add_argument("--project-label")
    write.add_argument("--full-bootstrap", action="store_true")
    write.add_argument("--candidate-memory")
    write.add_argument("--candidate-docs-graph")
    write.add_argument("--promote-candidates", action="store_true")
    write.add_argument("--root-authorized-promotion", action="store_true")
    sub.add_parser("validate")
    sub.add_parser("v342-preflight")
    graph = sub.add_parser("codegraph")
    graph.add_argument("command", nargs=argparse.REMAINDER)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        root = checked_project_root(args.project_root)
        if args.action == "preflight":
            preflight(root)
        elif args.action == "print-root":
            print(root)
        elif args.action == "write-context":
            command_write_context(root, args)
        elif args.action == "validate":
            command_validate(root, args)
        elif args.action == "codegraph":
            command_codegraph(root, args)
        elif args.action == "v342-preflight":
            command_v342_preflight(root, args)
        else:  # pragma: no cover - argparse owns the action set
            fail(f"unknown action: {args.action}")
    except (InitError, validator.ValidationError) as exc:
        print(f"Teamwork project init refused: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
