#!/usr/bin/env python3
"""Own durable Teamwork storage and the per-task Writer live document.

Every current-format case may expose one mutable ``live.md``. Purpose-specific
content is folded into that document while locking, stale-writer checks,
journals, recovery, and readback remain storage implementation details. The
``case-*`` commands operate only on current case-v3 trees for internal tooling
and diagnostics; old schemas are accepted only by explicit migration commands.
"""

from __future__ import annotations

import argparse
import base64
import contextlib
import fcntl
import fnmatch
import hashlib
import html
import json
import os
import re
import secrets
import stat
import sys
import tempfile
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterator, NoReturn
import unicodedata


MAX_REQUEST_BYTES = 256 * 1024
CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
LEGACY_UNSAFE_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DISCUSSION_ARCHIVE_RE = re.compile(
    r"^docs/teamwork/discussion/(\d{4}-\d{2}-\d{2})-([a-z0-9]+(?:-[a-z0-9]+)*)(?:-(\d+))?\.md$"
)
DESIGN_PATH_RE = re.compile(
    r"^docs/teamwork/design/(\d{4}-\d{2}-\d{2})-([a-z0-9]+(?:-[a-z0-9]+)*)\.md$"
)
GOAL_PATH_RE = re.compile(
    r"^docs/teamwork/reports/(\d{4}-\d{2}-\d{2})-([a-z0-9]+(?:-[a-z0-9]+)*)-goal\.md$"
)
WORKFLOW_ARTIFACT_PATH_RE = re.compile(
    r"^docs/teamwork/(?:research|plans|workflows/(?:debug|review|execution|conclusion|init|update))/(\d{4}-\d{2}-\d{2})-([a-z0-9]+(?:-[a-z0-9]+)*)\.md$"
)
DISCUSSION_CURRENT = "docs/teamwork/discussion/current.md"
INDEX_PATH = "docs/teamwork/index.json"
DISCUSSION_MARKER = "docs/teamwork/discussion/.discussion-transaction.json"
DESIGN_MARKER = "docs/teamwork/.design-transaction.json"
GOAL_MARKER = "docs/teamwork/.goal-transaction.json"
WORKFLOW_ARTIFACT_MARKER = "docs/teamwork/.workflow-artifact-transaction.json"
COLLABORATE_MARKER = "docs/teamwork/collaborate/.collaborate-transaction.json"
CANONICAL_CURRENT = "docs/teamwork/current.md"
COLLABORATE_CURRENT = "docs/teamwork/collaborate/current.md"
COLLABORATE_PREFIXES = (
    "docs/teamwork/collaborate/",
    INDEX_PATH,
)
WORKFLOW_ARTIFACT_KIND = "workflow-artifact"
WORKFLOW_ARTIFACT_PREFIXES = (
    "docs/teamwork/plans/",
    "docs/teamwork/research/",
    "docs/teamwork/workflows/",
    INDEX_PATH,
)
WORKFLOW_CONFIG: dict[str, dict[str, str]] = {
    "research": {"kind": "research", "active": "results", "directory": "docs/teamwork/research"},
    "plan": {"kind": "plan", "active": "plan", "directory": "docs/teamwork/plans"},
    "debug": {"kind": "report", "active": "results", "directory": "docs/teamwork/workflows/debug"},
    "review": {"kind": "report", "active": "results", "directory": "docs/teamwork/workflows/review"},
    "execution": {"kind": "result", "active": "results", "directory": "docs/teamwork/workflows/execution"},
    "conclusion": {"kind": "result", "active": "results", "directory": "docs/teamwork/workflows/conclusion"},
    "init": {"kind": "report", "active": "results", "directory": "docs/teamwork/workflows/init"},
    "update": {"kind": "report", "active": "results", "directory": "docs/teamwork/workflows/update"},
}

CASE_TRANSACTION_MARKER = "docs/teamwork/.case-transaction.json"
CASE_PREFIXES = (
    "docs/teamwork/index.json",
    "docs/teamwork/cases/",
)
CASE_ID_RE = re.compile(r"^c-[0-9a-f]{64}$")
ARTIFACT_ID_RE = re.compile(r"^a-[0-9a-f]{64}$")
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
TASK_KEY_RE = SLUG_RE
CASE_ACTIVE_PHASES = {"collaborating", "collecting", "planned", "executing", "reviewing"}
CASE_PHASES = {*CASE_ACTIVE_PHASES, "closed"}
CASE_TRANSITIONS = {
    None: {"collaborating", "collecting", "planned", "executing"},
    "collaborating": {"collaborating", "collecting", "planned", "closed"},
    "collecting": {"collecting", "planned", "executing", "closed"},
    "planned": {"planned", "collecting", "executing", "closed"},
    "executing": {"executing", "reviewing", "closed"},
    "reviewing": {"reviewing", "executing", "closed"},
    "closed": {"closed"},
}
CASE_LIVE_KINDS = {"collaborate", "goal"}
CASE_SINGLETON_KINDS = {"decision", "plan"}
CASE_HISTORY_KINDS = {"plan", "decision", "result"}
CASE_REVIEW_KINDS = {"review", "review-delta"}
CASE_RESULT_KINDS = {"result"}
CASE_EVIDENCE_KINDS = {"research", "debug", "init", "update", "evidence"}
CASE_OPERATION_ARTIFACT_CONTRACTS = {
    "collaborate-upsert": ("collaborate", "teamwork"),
    "accept-decision": ("decision", "teamwork"),
    "evidence-add": ("evidence", "teamwork"),
    "research-add": ("research", "teamwork"),
    "debug-add": ("debug", "teamwork"),
    "init-result": ("init", "teamwork"),
    "update-result": ("update", "teamwork"),
    "native-result": ("result", "teamwork"),
    "plan-upsert": ("plan", "teamwork"),
    "plan-review-add": ("review", "teamwork"),
    "review-add": ("review", "teamwork"),
    "code-review-add": ("review", "teamwork"),
    "result-add": ("result", "teamwork"),
    "goal-acquire": ("goal", "teamwork"),
    "goal-update": ("goal", "teamwork"),
}
CASE_ARTIFACT_KINDS = (
    CASE_LIVE_KINDS
    | CASE_SINGLETON_KINDS
    | CASE_REVIEW_KINDS
    | CASE_RESULT_KINDS
    | CASE_EVIDENCE_KINDS
    | {f"history-{kind}" for kind in CASE_HISTORY_KINDS}
)
CASE_LIVE_DOCUMENT_VERSION = 1
CASE_LIVE_PURPOSES = {
    "task", "discussion", "research", "debug", "plan", "review",
    "goal", "init", "update", "result",
}
CASE_LIVE_STATUSES = {"active", "finalized"}
CASE_LIVE_SECTIONS = (
    "Purpose State", "Decisions", "Plan", "Evidence", "Review",
    "Outcome", "Migration Appendix",
)
CASE_REPLACE_SECTIONS = {"Purpose State", "Decisions", "Plan"}
CASE_INDEX_MAX_BYTES = 256 * 1024
CASE_MANIFEST_MAX_BYTES = 256 * 1024
CASE_LIVE_MAX_BYTES = 4 * 1024 * 1024
CASE_CAPS = {
    "active_cases": 32,
    "claim_heads": 2048,
    "aliases": 256,
    "recent_cases": 10,
    "claims": 256,
    "artifacts": 2048,
    "history": 1024,
    "references": 1024,
    "migration_sources": 4096,
}
CASE_MIGRATION_PHASES = {
    None,
    "baseline_approved",
    "archive_durable",
    "candidate_validated",
    "old_tree_renamed",
    "new_tree_installed",
    "postinstall_validated",
    "committed",
    "cleanup_complete",
}
CLAIM_ID_RE = re.compile(r"^cl-[0-9a-f]{64}$")
MIGRATION_ID_RE = re.compile(r"^m-[0-9a-f]{64}$")

MIGRATION_KIND = "case-migration"
MIGRATION_PREFIXES = (
    ".teamwork/",
    INDEX_PATH,
)
MIGRATION_RUNTIME_ROOT = ".teamwork/runtime"
MIGRATION_PHASES = {
    "baseline_approved",
    "archive_durable",
    "candidate_validated",
    "old_tree_renamed",
    "new_tree_installed",
    "postinstall_validated",
    "committed",
    "cleanup_complete",
}


class TransactionError(Exception):
    """A user-actionable failure with a recovery classification."""

    def __init__(self, message: str, category: str = "PREWRITE_SAFE") -> None:
        super().__init__(message)
        self.category = category


class SimulatedInterruption(Exception):
    """Test-only process-loss simulation: leave the durable journal behind."""


def fail(message: str, *, category: str = "PREWRITE_SAFE") -> NoReturn:
    raise TransactionError(message, category)


def valid_date(value: object) -> bool:
    if not isinstance(value, str) or DATE_RE.fullmatch(value) is None:
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def require_date(value: object, label: str) -> str:
    if not valid_date(value):
        fail(f"{label} must be a valid YYYY-MM-DD date")
    assert isinstance(value, str)
    return value


def require_text(value: object, label: str, *, maximum: int = 8000) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > maximum
        or CONTROL_RE.search(value) is not None
    ):
        fail(f"{label} must be non-empty one-line text")
    return value.strip()


def require_slug(value: object, label: str = "slug") -> str:
    if not isinstance(value, str) or SLUG_RE.fullmatch(value) is None:
        fail(f"{label} must be a lowercase kebab-case identifier")
    return value


def require_text_list(value: object, label: str, *, minimum: int = 0, maximum: int = 50) -> list[str]:
    if not isinstance(value, list) or not minimum <= len(value) <= maximum:
        fail(f"{label} must contain between {minimum} and {maximum} items")
    result = [require_text(item, f"{label} item", maximum=4000) for item in value]
    if len(set(result)) != len(result):
        fail(f"{label} must not contain duplicates")
    return result


def require_path_list(value: object, label: str, *, maximum: int = 50) -> list[str]:
    if not isinstance(value, list) or len(value) > maximum:
        fail(f"{label} must contain at most {maximum} items")
    result = [checked_relative(item, f"{label} item") for item in value]
    if len(set(result)) != len(result):
        fail(f"{label} must not contain duplicates")
    return result


def require_markdown_body(value: object, label: str, *, maximum_bytes: int = 128 * 1024) -> str:
    if not isinstance(value, str) or not value.strip():
        fail(f"{label} must be non-empty Markdown text")
    if len(value.encode("utf-8")) > maximum_bytes or LEGACY_UNSAFE_CONTROL_RE.search(value) is not None:
        fail(f"{label} exceeds size limits or contains unsafe control characters")
    return value.rstrip() + "\n"


def checked_relative(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or CONTROL_RE.search(value):
        fail(f"{label} must be a normalized project-relative path")
    pure = PurePosixPath(value)
    if (
        pure.is_absolute()
        or pure.as_posix() != value
        or "\\" in value
        or any(part in {"", ".", ".."} for part in pure.parts)
    ):
        fail(f"{label} must be a normalized project-relative path")
    return value


def checked_project_root(raw: str) -> Path:
    if not raw or CONTROL_RE.search(raw):
        fail("project root must be non-empty text without control characters")
    provided = Path(os.path.abspath(os.path.expanduser(raw)))
    try:
        leaf = provided.lstat()
    except OSError as exc:
        fail(f"project root must exist: {provided}: {exc}")
    if stat.S_ISLNK(leaf.st_mode):
        fail(f"project root itself must not be a symlink: {provided}")
    # Refuse user-controlled ancestor links too. macOS's normal /var and /tmp
    # aliases are the only accepted platform aliases; they are canonicalized
    # below so tests and ordinary temporary projects do not become unusable.
    current = Path(provided.anchor)
    for part in provided.parts[1:]:
        current /= part
        try:
            info = current.lstat()
        except OSError as exc:
            fail(f"project-root component must exist: {current}: {exc}")
        if stat.S_ISLNK(info.st_mode) and current not in {Path("/var"), Path("/tmp")}:
            fail(f"project-root component must not be a symlink: {current}")
        if not stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode):
            fail(f"project-root component must be a directory: {current}")
    # Canonicalize those permitted system aliases, then use only the canonical
    # tree for all later checks and mutations.
    root = Path(os.path.realpath(provided))
    current = Path(root.anchor)
    for part in root.parts[1:]:
        current /= part
        try:
            info = current.lstat()
        except OSError as exc:
            fail(f"project-root component must exist: {current}: {exc}")
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            fail(f"project-root component must be a non-symlink directory: {current}")
    return root


def _relative_path(root: Path, relative: str) -> Path:
    checked_relative(relative, "artifact path")
    return root.joinpath(*PurePosixPath(relative).parts)


def _root_device(root: Path) -> int:
    try:
        return root.stat().st_dev
    except OSError as exc:
        fail(f"cannot stat project root: {exc}")


def _walk_parent(root: Path, relative: str, *, create: bool = False) -> Path | None:
    """Return a verified same-device parent, never following a symlink."""

    pure = PurePosixPath(checked_relative(relative, "artifact path"))
    current = root
    device = _root_device(root)
    for part in pure.parts[:-1]:
        current /= part
        try:
            info = current.lstat()
        except FileNotFoundError:
            if not create:
                return None
            try:
                current.mkdir(mode=0o700)
            except OSError as exc:
                fail(f"cannot create artifact parent {current}: {exc}")
            try:
                info = current.lstat()
            except OSError as exc:
                fail(f"cannot inspect created artifact parent {current}: {exc}")
        except OSError as exc:
            fail(f"cannot inspect artifact parent {current}: {exc}")
        if (
            stat.S_ISLNK(info.st_mode)
            or not stat.S_ISDIR(info.st_mode)
            or info.st_dev != device
        ):
            fail("artifact parent must be a same-device non-symlink directory")
    return current


def ensure_directory(root: Path, relative: str, *, created: list[str] | None = None) -> Path:
    """Create one artifact directory after checking each component."""

    checked_relative(relative + "/placeholder", "artifact directory")
    current = root
    device = _root_device(root)
    for part in PurePosixPath(relative).parts:
        current /= part
        try:
            info = current.lstat()
        except FileNotFoundError:
            try:
                current.mkdir(mode=0o700)
            except OSError as exc:
                fail(f"cannot create artifact directory {current}: {exc}")
            info = current.lstat()
            if created is not None:
                created.append(current.relative_to(root).as_posix())
        except OSError as exc:
            fail(f"cannot inspect artifact directory {current}: {exc}")
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode) or info.st_dev != device:
            fail("artifact directory must be a same-device non-symlink directory")
    return current


def _safe_lstat(root: Path, relative: str, *, optional: bool = False) -> tuple[Path, os.stat_result] | None:
    parent = _walk_parent(root, relative, create=False)
    if parent is None:
        if optional:
            return None
        fail("artifact parent does not exist")
    path = parent / PurePosixPath(relative).name
    try:
        info = path.lstat()
    except FileNotFoundError:
        if optional:
            return None
        fail(f"missing artifact: {relative}")
    except OSError as exc:
        fail(f"cannot inspect artifact {relative}: {exc}")
    if (
        stat.S_ISLNK(info.st_mode)
        or not stat.S_ISREG(info.st_mode)
        or info.st_nlink != 1
        or info.st_dev != _root_device(root)
    ):
        fail(f"artifact must be a same-device single-link non-symlink regular file: {relative}")
    return path, info


def safe_read_bytes(root: Path, relative: str, *, optional: bool = False) -> bytes | None:
    checked_relative(relative, "artifact path")
    result = _safe_lstat(root, relative, optional=optional)
    if result is None:
        return None
    path, before = result
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        fail(f"cannot safely open artifact {relative}: {exc}")
    try:
        opened = os.fstat(fd)
        if (
            (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino)
            or opened.st_nlink != 1
            or not stat.S_ISREG(opened.st_mode)
        ):
            fail(f"artifact changed identity while opening: {relative}")
        chunks: list[bytes] = []
        while chunk := os.read(fd, 1024 * 1024):
            chunks.append(chunk)
        final = os.fstat(fd)
        if (final.st_dev, final.st_ino) != (opened.st_dev, opened.st_ino):
            fail(f"artifact changed identity while reading: {relative}")
        return b"".join(chunks)
    finally:
        os.close(fd)


def safe_read_text(root: Path, relative: str, *, optional: bool = False) -> str | None:
    blob = safe_read_bytes(root, relative, optional=optional)
    if blob is None:
        return None
    try:
        return blob.decode("utf-8")
    except UnicodeDecodeError as exc:
        fail(f"artifact must be UTF-8: {relative}: {exc}")


def _mode_of(root: Path, relative: str) -> int | None:
    result = _safe_lstat(root, relative, optional=True)
    return None if result is None else stat.S_IMODE(result[1].st_mode)


def _fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        fail(f"cannot open artifact directory for fsync: {exc}", category="INDETERMINATE")
    try:
        os.fsync(fd)
    except OSError as exc:
        fail(f"cannot fsync artifact directory: {exc}", category="INDETERMINATE")
    finally:
        os.close(fd)


def _write_temp(root: Path, parent_relative: str, name: str, data: bytes, mode: int) -> str:
    relative = f"{parent_relative}/{name}" if parent_relative else name
    parent = _walk_parent(root, relative, create=False)
    if parent is None:
        fail("artifact parent does not exist")
    path = parent / name
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        fd = os.open(path, flags, mode)
    except OSError as exc:
        fail(f"cannot create transaction temporary artifact: {exc}")
    try:
        offset = 0
        while offset < len(data):
            offset += os.write(fd, data[offset:])
        os.fchmod(fd, mode)
        os.fsync(fd)
    except OSError as exc:
        fail(f"cannot write transaction temporary artifact: {exc}")
    finally:
        os.close(fd)
    _fsync_directory(parent)
    return relative


def _replace(root: Path, source_relative: str, target_relative: str) -> None:
    source_parent = _walk_parent(root, source_relative, create=False)
    target_parent = _walk_parent(root, target_relative, create=False)
    if source_parent is None or target_parent is None or source_parent != target_parent:
        fail("transaction replacement must stay in one verified artifact directory", category="INDETERMINATE")
    source = source_parent / PurePosixPath(source_relative).name
    target = target_parent / PurePosixPath(target_relative).name
    try:
        source_info = source.lstat()
    except OSError as exc:
        fail(f"transaction stage disappeared: {exc}", category="INDETERMINATE")
    if not stat.S_ISREG(source_info.st_mode) or stat.S_ISLNK(source_info.st_mode):
        fail("transaction stage is not a regular file", category="INDETERMINATE")
    try:
        if target.exists() or target.is_symlink():
            # lstat is deliberate: replacement may remove a regular target, but
            # it must never silently normalize an unexpected link or directory.
            old = target.lstat()
            if stat.S_ISLNK(old.st_mode) or not stat.S_ISREG(old.st_mode):
                fail("transaction target changed to an unsafe type", category="INDETERMINATE")
        os.replace(source, target)
    except TransactionError:
        raise
    except OSError as exc:
        fail(f"cannot install transaction artifact: {exc}", category="INDETERMINATE")
    _fsync_directory(target_parent)


def _remove_regular(root: Path, relative: str, *, optional: bool = True) -> None:
    result = _safe_lstat(root, relative, optional=optional)
    if result is None:
        return
    path, _ = result
    try:
        path.unlink()
    except OSError as exc:
        fail(f"cannot remove transaction artifact: {exc}", category="INDETERMINATE")
    _fsync_directory(path.parent)


@contextlib.contextmanager
def locked_memory(root: Path) -> Iterator[None]:
    """Lock the Teamwork directory itself, leaving no lock-file residue."""

    memory = _walk_parent(root, "docs/teamwork/.artifact-lock", create=False)
    if memory is None:
        fail("Teamwork project memory is not initialized; initialize it before saving durable state")
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(memory, flags)
    except OSError as exc:
        fail(f"cannot lock Teamwork artifact directory: {exc}")
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


@contextlib.contextmanager
def locked_runtime(root: Path) -> Iterator[None]:
    ensure_directory(root, ".teamwork/runtime")
    runtime = _safe_dir(root, ".teamwork/runtime")
    assert runtime is not None
    lock_path = runtime / ".memory.lock"
    flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        fd = os.open(lock_path, flags, 0o600)
    except OSError as exc:
        fail(f"cannot open migration runtime lock: {exc}", category="INDETERMINATE")
    try:
        opened = os.fstat(fd)
        if not stat.S_ISREG(opened.st_mode) or opened.st_dev != _root_device(root):
            fail("migration runtime lock must be same-device regular file", category="INDETERMINATE")
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


def require_initialized_memory(root: Path) -> None:
    """Artifacts never initialize ordinary memory or a project on their own."""

    result = _safe_lstat(root, "docs/teamwork/index.json", optional=True)
    if result is None:
        fail("Teamwork project memory is not initialized; initialize it before saving durable state")


def _hash(*parts: bytes) -> str:
    digest = hashlib.sha256()
    for part in parts:
        digest.update(len(part).to_bytes(8, "big"))
        digest.update(part)
    return digest.hexdigest()


@dataclass(frozen=True)
class FileImage:
    exists: bool
    data: bytes = b""
    mode: int = 0o600

    def as_json(self) -> dict[str, object]:
        return {
            "exists": self.exists,
            "data_b64": base64.b64encode(self.data).decode("ascii") if self.exists else None,
            "mode": self.mode if self.exists else None,
        }

    @classmethod
    def from_json(cls, value: object, label: str) -> "FileImage":
        if not isinstance(value, dict) or not isinstance(value.get("exists"), bool):
            fail(f"transaction journal {label} image is malformed", category="INDETERMINATE")
        if not value["exists"]:
            if value.get("data_b64") is not None or value.get("mode") is not None:
                fail(f"transaction journal {label} absent image is malformed", category="INDETERMINATE")
            return cls(False)
        encoded = value.get("data_b64")
        mode = value.get("mode")
        if not isinstance(encoded, str) or not isinstance(mode, int) or not 0 <= mode <= 0o777:
            fail(f"transaction journal {label} present image is malformed", category="INDETERMINATE")
        try:
            data = base64.b64decode(encoded.encode("ascii"), validate=True)
        except Exception:
            fail(f"transaction journal {label} bytes are malformed", category="INDETERMINATE")
        return cls(True, data, mode)


@dataclass(frozen=True)
class Output:
    data: bytes | None
    mode: int = 0o600


def capture_image(root: Path, relative: str) -> FileImage:
    data = safe_read_bytes(root, relative, optional=True)
    if data is None:
        return FileImage(False)
    mode = _mode_of(root, relative)
    assert mode is not None
    return FileImage(True, data, mode)


def _same_image(root: Path, relative: str, expected: FileImage) -> bool:
    actual = capture_image(root, relative)
    return actual == expected


def _allowed_path(relative: str, prefixes: tuple[str, ...]) -> bool:
    """Allow directory namespaces, but require exact file-surface matches.

    Callers pass directory entries with a trailing slash and individual control
    files without one.  Treating both as generic string prefixes would let a
    retained journal target `index.json.bak` (or a child below a future path)
    even though only the canonical index file belongs to Design/Goal.
    """

    for prefix in prefixes:
        if prefix.endswith("/"):
            if relative == prefix.rstrip("/") or relative.startswith(prefix):
                return True
        elif relative == prefix:
            return True
    return False


def _remove_created_directories(root: Path, directories: list[str]) -> None:
    """Remove only transaction-created, now-empty directories in reverse order."""

    for relative in reversed(directories):
        checked_relative(relative, "transaction-created directory")
        parent = _walk_parent(root, relative, create=False)
        if parent is None:
            continue
        directory = parent / PurePosixPath(relative).name
        try:
            info = directory.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            fail(f"cannot inspect transaction-created directory: {exc}", category="INDETERMINATE")
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            fail("transaction-created directory changed to an unsafe type", category="INDETERMINATE")
        try:
            directory.rmdir()
        except OSError as exc:
            fail(f"transaction-created directory is not safely empty: {exc}", category="INDETERMINATE")
        _fsync_directory(parent)


def _journal_parent(marker: str) -> str:
    return PurePosixPath(marker).parent.as_posix()


def _write_control(root: Path, relative: str, payload: dict[str, object]) -> None:
    parent = _walk_parent(root, relative, create=False)
    if parent is None:
        fail("transaction journal parent does not exist", category="INDETERMINATE")
    token = secrets.token_hex(16)
    stage = _write_temp(root, _journal_parent(relative), f".tw-journal-{token}", (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8"), 0o600)
    _replace(root, stage, relative)


def _read_journal(root: Path, marker: str, prefixes: tuple[str, ...], kind: str) -> dict[str, object] | None:
    raw = safe_read_text(root, marker, optional=True)
    if raw is None:
        return None
    try:
        journal = json.loads(raw)
    except json.JSONDecodeError:
        fail("transaction journal is not valid JSON", category="INDETERMINATE")
    if (
        not isinstance(journal, dict)
        or journal.get("schema_version") != 1
        or journal.get("kind") != kind
        or journal.get("phase") not in {"prepared", "committed"}
        or not isinstance(journal.get("token"), str)
        or not re.fullmatch(r"[0-9a-f]{32}", journal["token"])
        or not isinstance(journal.get("targets"), list)
        or not journal["targets"]
        or not isinstance(journal.get("created_directories", []), list)
    ):
        fail("transaction journal has an unsupported schema", category="INDETERMINATE")
    seen: set[str] = set()
    for position, item in enumerate(journal["targets"]):
        if not isinstance(item, dict):
            fail("transaction journal target is malformed", category="INDETERMINATE")
        path = item.get("path")
        if not isinstance(path, str):
            fail("transaction journal target has no path", category="INDETERMINATE")
        checked_relative(path, "transaction journal target")
        if path in seen or not _allowed_path(path, prefixes):
            fail("transaction journal target is outside its owned artifact surface", category="INDETERMINATE")
        seen.add(path)
        FileImage.from_json(item.get("before"), f"before[{position}]")
        FileImage.from_json(item.get("after"), f"after[{position}]")
        for key in ("stage", "backup"):
            value = item.get(key)
            if value is not None:
                if not isinstance(value, str):
                    fail("transaction journal temporary path is malformed", category="INDETERMINATE")
                checked_relative(value, "transaction journal temporary")
                expected_parent = PurePosixPath(path).parent.as_posix()
                if PurePosixPath(value).parent.as_posix() != expected_parent or not PurePosixPath(value).name.startswith(".tw-"):
                    fail("transaction journal temporary is outside its target directory", category="INDETERMINATE")
    for directory in journal.get("created_directories", []):
        if not isinstance(directory, str):
            fail("transaction journal created directory is malformed", category="INDETERMINATE")
        checked_relative(directory, "transaction journal created directory")
        if not _allowed_path(directory, prefixes):
            fail("transaction journal created directory is outside its owned artifact surface", category="INDETERMINATE")
    return journal


def _restore_image(root: Path, relative: str, image: FileImage) -> None:
    if image.exists:
        parent = PurePosixPath(relative).parent.as_posix()
        stage = _write_temp(root, parent, f".tw-recover-{secrets.token_hex(16)}", image.data, image.mode)
        _replace(root, stage, relative)
    else:
        _remove_regular(root, relative, optional=True)


def recover_transaction(root: Path, marker: str, prefixes: tuple[str, ...], kind: str) -> bool:
    """Recover a complete valid journal.  Prepared rolls back; committed rolls forward."""

    journal = _read_journal(root, marker, prefixes, kind)
    if journal is None:
        return False
    phase = str(journal["phase"])
    targets = journal["targets"]
    assert isinstance(targets, list)
    try:
        for item in targets:
            assert isinstance(item, dict)
            image = FileImage.from_json(item["before"] if phase == "prepared" else item["after"], "recovery")
            _restore_image(root, str(item["path"]), image)
        for item in targets:
            assert isinstance(item, dict)
            image = FileImage.from_json(item["before"] if phase == "prepared" else item["after"], "verification")
            if not _same_image(root, str(item["path"]), image):
                fail("transaction recovery readback does not match its journal image", category="INDETERMINATE")
        for item in targets:
            assert isinstance(item, dict)
            for key in ("stage", "backup"):
                temporary = item.get(key)
                if isinstance(temporary, str):
                    _remove_regular(root, temporary, optional=True)
        _remove_regular(root, marker, optional=False)
        if phase == "prepared":
            directories = journal.get("created_directories", [])
            assert isinstance(directories, list)
            _remove_created_directories(root, [str(item) for item in directories])
    except TransactionError:
        raise
    except Exception as exc:
        fail(f"transaction recovery could not establish an exact state: {exc}", category="INDETERMINATE")
    return True


def _env_count(*names: str) -> int | None:
    for name in names:
        raw = os.environ.get(name)
        if raw is None:
            continue
        try:
            number = int(raw)
        except ValueError:
            continue
        if number > 0:
            return number
    return None


def _interruption_requested() -> bool:
    for key, value in os.environ.items():
        if (
            key.startswith("TEAMWORK_ARTIFACT_TRANSACTION_INTERRUPT_AFTER_")
            or key.startswith("TEAMWORK_DISCUSSION_TRANSACTION_INTERRUPT_AFTER_")
        ) and value not in {"", "0", "false", "False"}:
            return True
    return False


def apply_transaction(
    root: Path,
    *,
    kind: str,
    marker: str,
    prefixes: tuple[str, ...],
    outputs: dict[str, Output],
    created_directories: list[str] | None = None,
) -> None:
    """Install output bytes with a replayable journal and randomized temporaries.

    Once the journal is durable, *all* exceptions are indeterminate.  We make a
    best effort to recover immediately, but callers must treat the failure as a
    recoverable ambiguous result rather than as a pre-write rejection.
    """

    if not outputs:
        fail("transaction needs at least one artifact output")
    if len(outputs) != len(set(outputs)):
        fail("transaction has duplicate artifact outputs")
    for path in outputs:
        checked_relative(path, "transaction output")
        if not _allowed_path(path, prefixes):
            fail("transaction output is outside its owned artifact surface")
    if _read_journal(root, marker, prefixes, kind) is not None:
        fail("unrecovered transaction journal remains after recovery", category="INDETERMINATE")

    created_directories = list(created_directories or [])
    for directory in created_directories:
        checked_relative(directory, "transaction-created directory")
        if not _allowed_path(directory, prefixes):
            fail("transaction-created directory is outside its owned artifact surface")
    token = secrets.token_hex(16)
    targets: list[dict[str, object]] = []
    staged: list[str] = []
    prepared = False
    try:
        for position, (path, output) in enumerate(outputs.items(), start=1):
            before = capture_image(root, path)
            stage: str | None = None
            output_mode = before.mode if before.exists else output.mode
            if output.data is not None:
                requested = _env_count("TEAMWORK_ARTIFACT_TRANSACTION_FAIL_STAGE_N")
                if requested == position:
                    fail("simulated stage failure")
                parent = PurePosixPath(path).parent.as_posix()
                stage = _write_temp(root, parent, f".tw-stage-{kind}-{token}-{position}", output.data, output_mode)
                staged.append(stage)
            backup = f"{PurePosixPath(path).parent.as_posix()}/.tw-backup-{kind}-{token}-{position}"
            targets.append(
                {
                    "path": path,
                    "before": before.as_json(),
                    "after": FileImage(output.data is not None, output.data or b"", output_mode).as_json(),
                    "stage": stage,
                    "backup": backup if before.exists else None,
                }
            )
        journal: dict[str, object] = {
            "schema_version": 1,
            "kind": kind,
            "phase": "prepared",
            "token": token,
            "targets": targets,
            "created_directories": created_directories,
        }
        _write_control(root, marker, journal)
        prepared = True

        for position, item in enumerate(targets, start=1):
            path = str(item["path"])
            before = FileImage.from_json(item["before"], "install")
            backup = item.get("backup")
            if before.exists:
                assert isinstance(backup, str)
                _replace(root, path, backup)
                if _interruption_requested():
                    raise SimulatedInterruption()
            requested = _env_count(
                "TEAMWORK_ARTIFACT_TRANSACTION_FAIL_INSTALL_N",
                "TEAMWORK_DISCUSSION_TRANSACTION_FAIL_REPLACE_N",
            )
            if requested == position:
                fail("simulated install failure", category="INDETERMINATE")
            stage = item.get("stage")
            if isinstance(stage, str):
                _replace(root, stage, path)
            # A deletion leaves only its randomized backup until commit.
        journal["phase"] = "committed"
        _write_control(root, marker, journal)
        requested = _env_count(
            "TEAMWORK_ARTIFACT_TRANSACTION_FAIL_POST_READBACK_N",
            "TEAMWORK_DISCUSSION_TRANSACTION_FAIL_POST_READBACK_N",
        )
        for position, item in enumerate(targets, start=1):
            after = FileImage.from_json(item["after"], "readback")
            if not _same_image(root, str(item["path"]), after):
                fail("transaction readback differs from its intended output", category="INDETERMINATE")
            if requested == position:
                fail("simulated post-preparation readback failure", category="INDETERMINATE")
        for item in targets:
            for key in ("backup", "stage"):
                temporary = item.get(key)
                if isinstance(temporary, str):
                    _remove_regular(root, temporary, optional=True)
        _remove_regular(root, marker, optional=False)
    except SimulatedInterruption:
        # The next inspect/apply invokes recovery from the journal's exact images.
        raise TransactionError("transaction interrupted after durable preparation; rerun inspect to recover", "INDETERMINATE")
    except TransactionError as exc:
        if not prepared:
            for stage in staged:
                try:
                    _remove_regular(root, stage, optional=True)
                except TransactionError:
                    pass
            _remove_created_directories(root, created_directories)
            raise
        try:
            recover_transaction(root, marker, prefixes, kind)
        except TransactionError as recovery_error:
            raise TransactionError(
                f"transaction was prepared and recovery remains required: {recovery_error}",
                "INDETERMINATE",
            ) from exc
        raise TransactionError(
            f"transaction was prepared; exact journal recovery completed after: {exc}",
            "INDETERMINATE",
        ) from exc
    except Exception as exc:
        if not prepared:
            for stage in staged:
                try:
                    _remove_regular(root, stage, optional=True)
                except TransactionError:
                    pass
            _remove_created_directories(root, created_directories)
            raise TransactionError(f"preparation failed: {exc}", "PREWRITE_SAFE") from exc
        try:
            recover_transaction(root, marker, prefixes, kind)
        except TransactionError as recovery_error:
            raise TransactionError(
                f"transaction was prepared and recovery remains required: {recovery_error}",
                "INDETERMINATE",
            ) from exc
        raise TransactionError(
            f"transaction was prepared; exact journal recovery completed after: {exc}",
            "INDETERMINATE",
        ) from exc


def ensure_no_migration_intermediate(root: Path) -> None:
    runtime = root / ".teamwork/runtime/migrations"
    if not runtime.exists():
        return
    try:
        children = sorted(runtime.iterdir(), key=lambda path: path.name)
    except OSError as exc:
        fail(f"cannot inspect migration runtime: {exc}")
    for child in children:
        if not child.is_dir() or child.is_symlink():
            fail("migration runtime has an unsafe entry")
        journal = child / "journal.json"
        if not journal.exists():
            continue
        try:
            state = json.loads(journal.read_text(encoding="utf-8"))
        except Exception as exc:
            fail(f"cannot inspect migration journal: {exc}", category="INDETERMINATE")
        if not isinstance(state, dict):
            fail("migration journal is malformed", category="INDETERMINATE")
        phase = state.get("phase")
        if phase not in {"committed", "cleanup_complete"}:
            fail("non-migration writes are blocked while migration is in an intermediate phase")


def _decode_json(raw: str, label: str) -> object:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        fail(f"cannot parse {label} JSON: {exc}")


def read_request(argument: str | None, inline: str | None) -> dict[str, object]:
    if (argument is None) == (inline is None):
        fail("provide exactly one of --request or --request-json")
    if inline is not None:
        if len(inline.encode("utf-8")) > MAX_REQUEST_BYTES:
            fail("request exceeds the maximum payload size")
        value = _decode_json(inline, "request")
    else:
        assert argument is not None
        path = Path(os.path.abspath(argument))
        try:
            before = path.lstat()
        except OSError as exc:
            fail(f"cannot inspect request file: {exc}")
        if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            fail("request file must be a single-link non-symlink regular file")
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        try:
            fd = os.open(path, flags)
        except OSError as exc:
            fail(f"cannot safely open request file: {exc}")
        try:
            chunks: list[bytes] = []
            total = 0
            while chunk := os.read(fd, 65536):
                chunks.append(chunk)
                total += len(chunk)
                if total > MAX_REQUEST_BYTES:
                    fail("request exceeds the maximum payload size")
            opened = os.fstat(fd)
            if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino) or opened.st_nlink != 1:
                fail("request file changed identity while reading")
            value = _decode_json(b"".join(chunks).decode("utf-8"), "request")
        except UnicodeDecodeError as exc:
            fail(f"request file must be UTF-8: {exc}")
        finally:
            os.close(fd)
    if not isinstance(value, dict):
        fail("request must be a JSON object")
    return value


def _section(value: str, name: str) -> str:
    match = re.search(rf"(?ms)^## {re.escape(name)}\n\n(.*?)(?=^## |\Z)", value)
    if not match:
        fail(f"artifact is missing the {name!r} section")
    return match.group(1).strip()


def _mermaid_label(value: str) -> str:
    return html.escape(value, quote=True).replace("|", "&#124;")


def _bullets(values: list[str]) -> str:
    return "\n".join(f"- {item}" for item in values) if values else "- none"


# ---------------------------------------------------------------------------
# Discussion: one active current.md, archives only on close/supersession.


DISCUSSION_LIST_FIELDS = ("settled", "still_open", "blockers", "key_evidence")
DISCUSSION_TEXT_FIELDS = ("goal", "current_branch", "return_path", "convergence")
DISCUSSION_V2_LIST_FIELDS = ("blockers", "key_evidence")
DISCUSSION_V2_TEXT_FIELDS = ("goal", "current_branch", "return_path", "convergence")
DISCUSSION_MODES = {"dialogue", "brainstorm", "grill"}
DISCUSSION_V3_LIST_FIELDS = ("blockers", "key_evidence", "settled", "synthesis", "tensions")
DISCUSSION_V3_TEXT_FIELDS = ("goal", "current_branch", "return_path", "convergence")
FRONTIER_ID_RE = re.compile(r"^Q[1-9][0-9]{0,2}$")
OPTION_ID_RE = re.compile(r"^[a-z][a-z0-9_-]{0,23}$")
FRONTIER_LEVELS = {"goal": 0, "boundary": 1, "detail": 2}
FRONTIER_STATUSES = {"open", "current", "closed", "rejected"}
FRONTIER_MUTABLE_FIELDS = ("prompt", "options", "recommendation", "depends_on", "closure_signal")
DISCUSSION_QUESTION_STATUSES = {"open", "current", "answered", "rejected"}
DISCUSSION_QUESTION_KINDS = {"open", "bounded"}


def normalize_discussion_state_v1(value: object, *, require_status: bool = True) -> dict[str, object]:
    if not isinstance(value, dict):
        fail("Discussion state must be an object")
    state: dict[str, object] = {
        "schema_version": 1,
        "artifact_type": "discussion",
        "slug": require_slug(value.get("slug")),
        "title": require_text(value.get("title"), "Discussion title"),
        "updated": require_date(value.get("updated"), "Discussion updated"),
        "status": value.get("status", "active"),
        "superseded_by": value.get("superseded_by"),
    }
    if state["status"] not in {"active", "accepted", "superseded"}:
        fail("Discussion status must be active, accepted, or superseded")
    if state["status"] == "active":
        if state["superseded_by"] is not None:
            fail("active Discussion cannot have superseded_by")
    else:
        if state["status"] == "superseded":
            state["superseded_by"] = checked_relative(state["superseded_by"], "Discussion superseded_by")
            if not str(state["superseded_by"]).startswith("docs/teamwork/discussion/"):
                fail("Discussion superseded_by must stay in docs/teamwork/discussion/")
        elif state["superseded_by"] is not None:
            fail("accepted Discussion cannot have superseded_by")
    for field in DISCUSSION_TEXT_FIELDS:
        state[field] = require_text(value.get(field), f"Discussion {field.replace('_', ' ')}")
    for field in DISCUSSION_LIST_FIELDS:
        state[field] = require_text_list(value.get(field), f"Discussion {field.replace('_', ' ')}")
    if state["status"] != "active" and state["still_open"]:
        fail("closed Discussion cannot retain still_open items")
    migration = value.get("migration_source")
    if migration is not None:
        if not isinstance(migration, dict):
            fail("Discussion migration_source must be an object")
        source_path = checked_relative(migration.get("path"), "Discussion migration source path")
        source_hash = migration.get("sha256")
        source_text = migration.get("source_text")
        if not source_path.startswith("docs/teamwork/discussion/") or not isinstance(source_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", source_hash) or not isinstance(source_text, str):
            fail("Discussion migration_source is malformed")
        if hashlib.sha256(source_text.encode("utf-8")).hexdigest() != source_hash:
            fail("Discussion migration_source hash does not match source_text")
        state["migration_source"] = {
            "path": source_path,
            "sha256": source_hash,
            "source_text": source_text,
        }
    return state


def _frontier_number(question_id: str) -> int:
    if FRONTIER_ID_RE.fullmatch(question_id) is None:
        fail("Discussion frontier id must match Q[1-9][0-9]{0,2}")
    return int(question_id[1:])


def _normalize_frontier_option(value: object, label: str) -> dict[str, str]:
    if not isinstance(value, dict):
        fail(f"{label} must be an object")
    option_id = value.get("id")
    if not isinstance(option_id, str) or OPTION_ID_RE.fullmatch(option_id) is None:
        fail(f"{label}.id must be a stable option id")
    return {
        "id": option_id,
        "label": require_text(value.get("label"), f"{label}.label", maximum=160),
        "tradeoff": require_text(value.get("tradeoff"), f"{label}.tradeoff", maximum=1000),
    }


def _normalize_frontier_item(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        fail(f"{label} must be an object")
    question_id = value.get("id")
    if not isinstance(question_id, str):
        fail(f"{label}.id must be text")
    _frontier_number(question_id)
    title = require_text(value.get("title"), f"{label}.title", maximum=160)
    if len(title) > 24:
        fail(f"{label}.title must be at most 24 Unicode code points")
    level = value.get("level")
    if level not in FRONTIER_LEVELS:
        fail(f"{label}.level must be goal, boundary, or detail")
    status = value.get("status")
    if status not in FRONTIER_STATUSES:
        fail(f"{label}.status is invalid")
    options_raw = value.get("options")
    if not isinstance(options_raw, list) or not 2 <= len(options_raw) <= 3:
        fail(f"{label}.options must contain two or three items")
    options = [_normalize_frontier_option(option, f"{label}.options[{position}]") for position, option in enumerate(options_raw)]
    option_ids = [str(option["id"]) for option in options]
    if len(set(option_ids)) != len(option_ids):
        fail(f"{label}.options must have unique ids")
    recommendation = value.get("recommendation")
    if recommendation not in option_ids:
        fail(f"{label}.recommendation must name one option id")
    depends_on = require_text_list(value.get("depends_on", []), f"{label}.depends_on", maximum=50)
    blocks = require_text_list(value.get("blocks", []), f"{label}.blocks", maximum=20)
    resolution = value.get("resolution")
    if status in {"open", "current"}:
        if resolution is not None:
            fail(f"{label}.resolution must be null while open or current")
    elif status == "closed":
        if not isinstance(resolution, dict) or resolution.get("kind") != "selected" or resolution.get("option_id") not in option_ids:
            fail(f"{label}.resolution must select one option when closed")
    else:
        if not isinstance(resolution, dict) or resolution.get("kind") != "rejected":
            fail(f"{label}.resolution must carry a rejected reason")
        require_text(resolution.get("reason"), f"{label}.resolution.reason", maximum=1000)
    normalized_resolution: object
    if resolution is None:
        normalized_resolution = None
    elif status == "closed":
        normalized_resolution = {"kind": "selected", "option_id": str(resolution["option_id"])}
    else:
        assert isinstance(resolution, dict)
        normalized_resolution = {"kind": "rejected", "reason": require_text(resolution.get("reason"), f"{label}.resolution.reason", maximum=1000)}
    return {
        "id": question_id,
        "title": title,
        "level": str(level),
        "status": str(status),
        "prompt": require_text(value.get("prompt"), f"{label}.prompt", maximum=4000),
        "options": options,
        "recommendation": str(recommendation),
        "largest_downside": require_text(value.get("largest_downside"), f"{label}.largest_downside", maximum=2000),
        "why_critical": require_text(value.get("why_critical"), f"{label}.why_critical", maximum=2000),
        "blocks": blocks,
        "depends_on": depends_on,
        "closure_signal": require_text(value.get("closure_signal"), f"{label}.closure_signal", maximum=2000),
        "resolution": normalized_resolution,
    }


def _dependency_path_exists(frontier: dict[str, dict[str, object]], source: str, target: str) -> bool:
    stack = [source]
    seen: set[str] = set()
    while stack:
        current = stack.pop()
        if current == target:
            return True
        if current in seen:
            continue
        seen.add(current)
        stack.extend(str(item) for item in frontier[current]["depends_on"])
    return False


def _validate_frontier_graph(frontier: list[dict[str, object]], current_batch: list[str], lifecycle: str) -> None:
    ids = [str(item["id"]) for item in frontier]
    if len(ids) != len(set(ids)):
        fail("Discussion frontier must have unique ids")
    by_id = {str(item["id"]): item for item in frontier}
    for item in frontier:
        item_id = str(item["id"])
        for dependency in item["depends_on"]:
            if dependency not in by_id:
                fail("Discussion frontier depends_on names an unknown id")
            if dependency == item_id:
                fail("Discussion frontier cannot depend on itself")
            if FRONTIER_LEVELS[str(by_id[str(dependency)]["level"])] > FRONTIER_LEVELS[str(item["level"])]:
                fail("Discussion frontier has a cross-level dependency inversion")
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(item_id: str) -> None:
        if item_id in visited:
            return
        if item_id in visiting:
            fail("Discussion frontier has a dependency cycle")
        visiting.add(item_id)
        for dependency in by_id[item_id]["depends_on"]:
            visit(str(dependency))
        visiting.remove(item_id)
        visited.add(item_id)

    for item_id in ids:
        visit(item_id)
    current_ids = [str(item["id"]) for item in frontier if item["status"] == "current"]
    if current_batch != current_ids:
        fail("Discussion current_batch must exactly match status=current items")
    if lifecycle == "active":
        if not 1 <= len(current_batch) <= 3:
            fail("active Discussion v2 must have one to three current items")
    elif current_batch:
        fail("closed Discussion v2 cannot retain current_batch")
    for item in frontier:
        item_id = str(item["id"])
        rejected_dependencies = [dep for dep in item["depends_on"] if by_id[str(dep)]["status"] == "rejected"]
        if rejected_dependencies and item["status"] != "rejected":
            fail("Discussion item with a rejected dependency must also be rejected")
        if item["status"] == "current":
            for dependency in item["depends_on"]:
                if by_id[str(dependency)]["status"] != "closed":
                    fail("Discussion current item dependencies must be closed")
    for left in current_batch:
        for right in current_batch:
            if left != right and (
                _dependency_path_exists(by_id, left, right) or _dependency_path_exists(by_id, right, left)
            ):
                fail("Discussion current_batch items must be independent")


def normalize_discussion_state_v2(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        fail("Discussion state must be an object")
    state: dict[str, object] = {
        "schema_version": 2,
        "artifact_type": "discussion",
        "slug": require_slug(value.get("slug")),
        "title": require_text(value.get("title"), "Discussion title"),
        "updated": require_date(value.get("updated"), "Discussion updated"),
        "status": value.get("status", "active"),
        "superseded_by": value.get("superseded_by"),
    }
    if state["status"] not in {"active", "accepted", "superseded"}:
        fail("Discussion status must be active, accepted, or superseded")
    if state["status"] == "active":
        if state["superseded_by"] is not None:
            fail("active Discussion cannot have superseded_by")
    elif state["status"] == "superseded":
        state["superseded_by"] = checked_relative(state["superseded_by"], "Discussion superseded_by")
        if not str(state["superseded_by"]).startswith("docs/teamwork/discussion/"):
            fail("Discussion superseded_by must stay in docs/teamwork/discussion/")
    elif state["superseded_by"] is not None:
        fail("accepted Discussion cannot have superseded_by")
    for field in DISCUSSION_V2_TEXT_FIELDS:
        state[field] = require_text(value.get(field), f"Discussion {field.replace('_', ' ')}")
    for field in DISCUSSION_V2_LIST_FIELDS:
        state[field] = require_text_list(value.get(field), f"Discussion {field.replace('_', ' ')}")
    frontier_raw = value.get("frontier")
    if not isinstance(frontier_raw, list) or not frontier_raw:
        fail("Discussion frontier must be a non-empty array")
    state["frontier"] = [_normalize_frontier_item(item, f"Discussion frontier[{position}]") for position, item in enumerate(frontier_raw)]
    state["current_batch"] = require_text_list(value.get("current_batch"), "Discussion current_batch", minimum=0, maximum=3)
    _validate_frontier_graph(state["frontier"], state["current_batch"], str(state["status"]))
    if "settled" in value or "still_open" in value:
        fail("Discussion schema v2 derives settled/open views from frontier")
    migration = value.get("migration_source")
    if migration is not None:
        if not isinstance(migration, dict):
            fail("Discussion migration_source must be an object")
        source_path = checked_relative(migration.get("path"), "Discussion migration source path")
        source_hash = migration.get("sha256")
        source_text = migration.get("source_text")
        if not source_path.startswith("docs/teamwork/discussion/") or not isinstance(source_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", source_hash) or not isinstance(source_text, str):
            fail("Discussion migration_source is malformed")
        if hashlib.sha256(source_text.encode("utf-8")).hexdigest() != source_hash:
            fail("Discussion migration_source hash does not match source_text")
        state["migration_source"] = {"path": source_path, "sha256": source_hash, "source_text": source_text}
    return state


def _normalize_discussion_question(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        fail(f"{label} must be an object")
    question_id = value.get("id")
    if not isinstance(question_id, str):
        fail(f"{label}.id must be text")
    _frontier_number(question_id)
    kind = value.get("kind")
    if kind not in DISCUSSION_QUESTION_KINDS:
        fail(f"{label}.kind must be open or bounded")
    status = value.get("status")
    if status not in DISCUSSION_QUESTION_STATUSES:
        fail(f"{label}.status is invalid")
    question: dict[str, object] = {
        "id": question_id,
        "kind": str(kind),
        "status": str(status),
        "prompt": require_text(value.get("prompt"), f"{label}.prompt", maximum=4000),
    }
    resolution = value.get("resolution")
    if status in {"open", "current"}:
        if resolution is not None:
            fail(f"{label}.resolution must be null while open or current")
        question["resolution"] = None
    elif status == "rejected":
        if not isinstance(resolution, dict) or resolution.get("kind") != "rejected":
            fail(f"{label}.resolution must carry a rejected reason")
        question["resolution"] = {
            "kind": "rejected",
            "reason": require_text(resolution.get("reason"), f"{label}.resolution.reason", maximum=1000),
        }
    elif kind == "open":
        if not isinstance(resolution, dict) or resolution.get("kind") != "text":
            fail(f"{label}.resolution must carry a text answer")
        question["resolution"] = {
            "kind": "text",
            "answer": require_text(resolution.get("answer"), f"{label}.resolution.answer", maximum=4000),
        }
    if kind == "open":
        forbidden = {
            "options",
            "recommendation",
            "largest_downside",
            "why_critical",
            "closure_signal",
        }
        if forbidden.intersection(value):
            fail(f"{label} open question cannot carry bounded-choice fields")
        return question
    options_raw = value.get("options")
    if not isinstance(options_raw, list) or not 2 <= len(options_raw) <= 3:
        fail(f"{label}.options must contain two or three items")
    options = [
        _normalize_frontier_option(option, f"{label}.options[{position}]")
        for position, option in enumerate(options_raw)
    ]
    option_ids = [str(option["id"]) for option in options]
    if len(set(option_ids)) != len(option_ids):
        fail(f"{label}.options must have unique ids")
    recommendation = value.get("recommendation")
    if recommendation not in option_ids:
        fail(f"{label}.recommendation must name one option id")
    if status == "answered":
        if (
            not isinstance(resolution, dict)
            or resolution.get("kind") != "selected"
            or resolution.get("option_id") not in option_ids
        ):
            fail(f"{label}.resolution must select one option when answered")
        question["resolution"] = {
            "kind": "selected",
            "option_id": str(resolution["option_id"]),
        }
    question.update(
        {
            "options": options,
            "recommendation": str(recommendation),
            "largest_downside": require_text(
                value.get("largest_downside"),
                f"{label}.largest_downside",
                maximum=2000,
            ),
            "why_critical": require_text(
                value.get("why_critical"),
                f"{label}.why_critical",
                maximum=2000,
            ),
            "closure_signal": require_text(
                value.get("closure_signal"),
                f"{label}.closure_signal",
                maximum=2000,
            ),
        }
    )
    return question


def _validate_discussion_questions(
    questions: list[dict[str, object]],
    current_question: object,
    lifecycle: str,
) -> str | None:
    ids = [str(item["id"]) for item in questions]
    if len(ids) != len(set(ids)):
        fail("Discussion questions must have unique ids")
    if ids != sorted(ids, key=_frontier_number):
        fail("Discussion questions must be ordered by monotonically increasing id")
    current_ids = [str(item["id"]) for item in questions if item["status"] == "current"]
    if lifecycle == "active":
        if len(current_ids) != 1:
            fail("active dialogue or brainstorm must have exactly one current question")
        if current_question != current_ids[0]:
            fail("Discussion current_question must exactly match status=current")
        return current_ids[0]
    if current_question is not None:
        fail("closed Discussion cannot retain current_question")
    if any(item["status"] in {"open", "current"} for item in questions):
        fail("closed Discussion cannot retain open questions")
    return None


def normalize_discussion_state_v3(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        fail("Discussion state must be an object")
    state: dict[str, object] = {
        "schema_version": 3,
        "artifact_type": "discussion",
        "slug": require_slug(value.get("slug")),
        "title": require_text(value.get("title"), "Discussion title"),
        "updated": require_date(value.get("updated"), "Discussion updated"),
        "status": value.get("status", "active"),
        "superseded_by": value.get("superseded_by"),
        "mode": value.get("mode"),
    }
    if state["status"] not in {"active", "accepted", "superseded"}:
        fail("Discussion status must be active, accepted, or superseded")
    if state["status"] == "active":
        if state["superseded_by"] is not None:
            fail("active Discussion cannot have superseded_by")
    elif state["status"] == "superseded":
        state["superseded_by"] = checked_relative(
            state["superseded_by"],
            "Discussion superseded_by",
        )
        if not str(state["superseded_by"]).startswith("docs/teamwork/discussion/"):
            fail("Discussion superseded_by must stay in docs/teamwork/discussion/")
    elif state["superseded_by"] is not None:
        fail("accepted Discussion cannot have superseded_by")
    if state["mode"] not in DISCUSSION_MODES:
        fail("Discussion mode must be dialogue, brainstorm, or grill")
    for field in DISCUSSION_V3_TEXT_FIELDS:
        state[field] = require_text(
            value.get(field),
            f"Discussion {field.replace('_', ' ')}",
        )
    for field in DISCUSSION_V3_LIST_FIELDS:
        minimum = 1 if field == "synthesis" else 0
        state[field] = require_text_list(
            value.get(field),
            f"Discussion {field.replace('_', ' ')}",
            minimum=minimum,
        )
    if state["mode"] == "grill":
        for forbidden in ("questions", "current_question", "candidate_space"):
            if forbidden in value:
                fail(f"grill Discussion cannot carry {forbidden}")
        frontier_raw = value.get("frontier")
        if not isinstance(frontier_raw, list) or not frontier_raw:
            fail("grill Discussion frontier must be a non-empty array")
        state["frontier"] = [
            _normalize_frontier_item(item, f"Discussion frontier[{position}]")
            for position, item in enumerate(frontier_raw)
        ]
        state["current_batch"] = require_text_list(
            value.get("current_batch"),
            "Discussion current_batch",
            minimum=0,
            maximum=3,
        )
        _validate_frontier_graph(
            state["frontier"],
            state["current_batch"],
            str(state["status"]),
        )
    else:
        for forbidden in ("frontier", "current_batch"):
            if forbidden in value:
                fail(f"{state['mode']} Discussion cannot carry {forbidden}")
        questions_raw = value.get("questions")
        if not isinstance(questions_raw, list) or not questions_raw:
            fail("dialogue and brainstorm questions must be a non-empty array")
        state["questions"] = [
            _normalize_discussion_question(item, f"Discussion questions[{position}]")
            for position, item in enumerate(questions_raw)
        ]
        current = value.get("current_question")
        state["current_question"] = _validate_discussion_questions(
            state["questions"],
            current,
            str(state["status"]),
        )
        if state["mode"] == "brainstorm":
            state["candidate_space"] = require_text_list(
                value.get("candidate_space"),
                "Discussion candidate_space",
                minimum=2,
                maximum=12,
            )
        elif "candidate_space" in value:
            fail("dialogue Discussion cannot carry candidate_space")
    migration = value.get("migration_source")
    if migration is not None:
        if not isinstance(migration, dict):
            fail("Discussion migration_source must be an object")
        source_path = checked_relative(
            migration.get("path"),
            "Discussion migration source path",
        )
        source_hash = migration.get("sha256")
        source_text = migration.get("source_text")
        if (
            not source_path.startswith("docs/teamwork/discussion/")
            or not isinstance(source_hash, str)
            or not re.fullmatch(r"[0-9a-f]{64}", source_hash)
            or not isinstance(source_text, str)
        ):
            fail("Discussion migration_source is malformed")
        if hashlib.sha256(source_text.encode("utf-8")).hexdigest() != source_hash:
            fail("Discussion migration_source hash does not match source_text")
        state["migration_source"] = {
            "path": source_path,
            "sha256": source_hash,
            "source_text": source_text,
        }
    return state


def normalize_discussion_state(value: object, *, require_status: bool = True) -> dict[str, object]:
    if not isinstance(value, dict):
        fail("Discussion state must be an object")
    if value.get("schema_version") == 3:
        return normalize_discussion_state_v3(value)
    if value.get("schema_version") == 2:
        return normalize_discussion_state_v2(value)
    return normalize_discussion_state_v1(value, require_status=require_status)


def discussion_route_mermaid_v1(state: dict[str, object]) -> str:
    return "\n".join(
        (
            "flowchart TD",
            f'    goal["Goal: {_mermaid_label(str(state["goal"]))}"] --> branch["Current branch: {_mermaid_label(str(state["current_branch"]))}"]',
            f'    branch --> settled["Settled: {_mermaid_label("; ".join(state["settled"]))}"]',
            f'    branch --> open["Still open: {_mermaid_label("; ".join(state["still_open"]) or "none")}"]',
            f'    open --> resume["Return path: {_mermaid_label(str(state["return_path"]))}"]',
            f'    settled --> convergence["Convergence: {_mermaid_label(str(state["convergence"]))}"]',
        )
    )


def discussion_route_mermaid_v2(state: dict[str, object]) -> str:
    frontier = {str(item["id"]): item for item in state["frontier"]}
    open_count = sum(1 for item in state["frontier"] if item["status"] in {"open", "current"})
    closed_count = sum(1 for item in state["frontier"] if item["status"] == "closed")
    lines = [
        "flowchart TD",
        f'    goal["Goal · {state["status"]}"] --> branch["Branch"]',
        f'    branch --> batch["Batch · {",".join(state["current_batch"]) or "none"}"]',
    ]
    if state["current_batch"]:
        lines.append('    subgraph current_batch["Current batch"]')
        for question_id in state["current_batch"]:
            item = frontier[str(question_id)]
            lines.append(f'        q{question_id}["{question_id} · {_mermaid_label(str(item["title"]))} · {item["status"]}"]')
        lines.append("    end")
    for item in state["frontier"]:
        question_id = str(item["id"])
        if question_id not in state["current_batch"]:
            lines.append(f'    q{question_id}["{question_id} · {_mermaid_label(str(item["title"]))} · {item["status"]}"]')
        for dependency in item["depends_on"]:
            lines.append(f"    q{dependency} --> q{question_id}")
    for question_id in state["current_batch"]:
        lines.append(f"    batch --> q{question_id}")
    lines.append(f'    branch --> converge["Converge · open {open_count} · closed {closed_count}"]')
    return "\n".join(lines)


def discussion_route_mermaid_v3(state: dict[str, object]) -> str:
    if state["mode"] == "grill":
        return discussion_route_mermaid_v2(state)
    questions = {str(item["id"]): item for item in state["questions"]}
    current = state["current_question"]
    current_label = "none"
    if isinstance(current, str):
        current_label = f"{current} · {questions[current]['kind']}"
    answered = sum(
        1
        for item in state["questions"]
        if item["status"] in {"answered", "rejected"}
    )
    return "\n".join(
        (
            "flowchart TD",
            f'    goal["Goal · {state["status"]}"] --> mode["Mode · {state["mode"]}"]',
            f'    mode --> question["Question · {_mermaid_label(current_label)}"]',
            f'    question --> converge["Converge · resolved {answered}"]',
        )
    )


def discussion_route_mermaid(state: dict[str, object]) -> str:
    if state.get("schema_version") == 3:
        return discussion_route_mermaid_v3(state)
    if state.get("schema_version") == 2:
        return discussion_route_mermaid_v2(state)
    return discussion_route_mermaid_v1(state)


def discussion_fallback_v1(state: dict[str, object]) -> str:
    return "\n".join(
        (
            f"Goal: {state['goal']}",
            f"Current branch: {state['current_branch']}",
            f"Settled: {'; '.join(state['settled']) or 'none'}",
            f"Still open: {'; '.join(state['still_open']) or 'none'}",
            f"Return path: {state['return_path']}",
            f"Blockers: {'; '.join(state['blockers']) or 'none'}",
            f"Convergence: {state['convergence']}",
            f"Key evidence: {'; '.join(state['key_evidence']) or 'none'}",
        )
    )


def discussion_fallback_v2(state: dict[str, object]) -> str:
    dependencies = []
    for item in state["frontier"]:
        deps = ", ".join(str(dep) for dep in item["depends_on"]) or "none"
        dependencies.append(f"{item['id']} <- {deps}")
    questions = [
        f"{item['id']} · {item['title']} · {item['level']} · {item['status']}"
        for item in state["frontier"]
    ]
    return "\n".join(
        (
            f"Route: Goal -> Branch -> Current batch ({', '.join(state['current_batch']) or 'none'}) -> Converge",
            f"Questions: {' | '.join(questions)}",
            f"Dependencies: {' | '.join(dependencies) or 'none'}",
            f"Blockers: {len(state['blockers'])}",
            f"Convergence status: {state['status']}",
        )
    )


def discussion_fallback_v3(state: dict[str, object]) -> str:
    if state["mode"] == "grill":
        return "\n".join(
            (
                f"Mode: {state['mode']}",
                discussion_fallback_v2(state),
            )
        )
    questions = [
        f"{item['id']} · {item['kind']} · {item['status']}"
        for item in state["questions"]
    ]
    return "\n".join(
        (
            f"Mode: {state['mode']}",
            f"Current question: {state['current_question'] or 'none'}",
            f"Questions: {' | '.join(questions)}",
            f"Synthesis points: {len(state['synthesis'])}",
            f"Tensions: {len(state['tensions'])}",
            f"Convergence status: {state['status']}",
        )
    )


def discussion_fallback(state: dict[str, object]) -> str:
    if state.get("schema_version") == 3:
        return discussion_fallback_v3(state)
    if state.get("schema_version") == 2:
        return discussion_fallback_v2(state)
    return discussion_fallback_v1(state)


def _discussion_semantics_v2(state: dict[str, object]) -> str:
    rows = [
        "| ID | Level | Status | Title | Depends on | Blocks | Recommendation | Closure |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for item in state["frontier"]:
        options = {str(option["id"]): option for option in item["options"]}
        recommendation = options[str(item["recommendation"])]
        rows.append(
            "| "
            + " | ".join(
                [
                    str(item["id"]),
                    str(item["level"]),
                    str(item["status"]),
                    str(item["title"]),
                    ", ".join(str(dep) for dep in item["depends_on"]) or "none",
                    ", ".join(str(block) for block in item["blocks"]) or "none",
                    f"{recommendation['label']} ({recommendation['tradeoff']})",
                    str(item["closure_signal"]),
                ]
            )
            + " |"
        )
    detail: list[str] = [
        "## Readable state",
        "",
        f"Goal: {state['goal']}",
        f"Current branch: {state['current_branch']}",
        f"Return path: {state['return_path']}",
        f"Convergence: {state['convergence']}",
        "",
        "Blockers:",
        _bullets(state["blockers"]),
        "",
        "Key evidence:",
        _bullets(state["key_evidence"]),
        "",
        "## Frontier",
        "",
        *rows,
    ]
    for item in state["frontier"]:
        detail.extend(
            [
                "",
                f"### {item['id']} {item['title']}",
                "",
                f"Prompt: {item['prompt']}",
                f"Why critical: {item['why_critical']}",
                f"Largest downside: {item['largest_downside']}",
                "",
                "Options:",
                _bullets([f"{option['id']}: {option['label']} - {option['tradeoff']}" for option in item["options"]]),
            ]
        )
        if item["resolution"] is not None:
            detail.append(f"Resolution: {json.dumps(item['resolution'], ensure_ascii=False, sort_keys=True)}")
    return "\n".join(detail)


def _discussion_semantics_v3(state: dict[str, object]) -> str:
    common: list[str] = [
        "## Readable state",
        "",
        f"Mode: {state['mode']}",
        f"Goal: {state['goal']}",
        f"Current branch: {state['current_branch']}",
        f"Return path: {state['return_path']}",
        f"Convergence: {state['convergence']}",
        "",
        "Synthesis:",
        _bullets(state["synthesis"]),
        "",
        "Tensions:",
        _bullets(state["tensions"]),
        "",
        "Settled:",
        _bullets(state["settled"]),
        "",
        "Blockers:",
        _bullets(state["blockers"]),
        "",
        "Key evidence:",
        _bullets(state["key_evidence"]),
    ]
    if state["mode"] == "grill":
        v2 = _discussion_semantics_v2(state)
        frontier = v2.split("## Frontier", 1)[1]
        return "\n".join([*common, "", "## Frontier" + frontier])
    if state["mode"] == "brainstorm":
        common.extend(
            [
                "",
                "Candidate space:",
                _bullets(state["candidate_space"]),
            ]
        )
    rows = [
        "| ID | Kind | Status | Prompt |",
        "|---|---|---|---|",
    ]
    for item in state["questions"]:
        prompt = str(item["prompt"]).replace("|", "\\|")
        rows.append(f"| {item['id']} | {item['kind']} | {item['status']} | {prompt} |")
    common.extend(["", "## Questions", "", *rows])
    for item in state["questions"]:
        common.extend(["", f"### {item['id']} · {item['kind']}", ""])
        if item["kind"] == "bounded":
            common.extend(
                [
                    f"Why critical: {item['why_critical']}",
                    f"Largest downside: {item['largest_downside']}",
                    f"Closure signal: {item['closure_signal']}",
                    "",
                    "Options:",
                    _bullets(
                        [
                            f"{option['id']}: {option['label']} - {option['tradeoff']}"
                            for option in item["options"]
                        ]
                    ),
                    f"Recommendation: {item['recommendation']}",
                ]
            )
        if item["resolution"] is not None:
            common.append(
                f"Resolution: {json.dumps(item['resolution'], ensure_ascii=False, sort_keys=True)}"
            )
    return "\n".join(common)


def render_discussion_artifact(value: object) -> str:
    state = normalize_discussion_state(value)
    parts = [
            "Artifact Type: discussion",
            f"Status: {state['status']}",
            "Authority: supporting",
            f"Last Updated: {state['updated']}",
            f"Discussion Slug: {state['slug']}",
            f"Superseded By: {state['superseded_by'] or 'none'}",
    ]
    if state.get("schema_version") == 3:
        parts.append(f"Discussion Mode: {state['mode']}")
    parts.extend(
        [
            "",
            f"# {state['title']}",
            "",
            "## Decision map",
            "",
            "```mermaid",
            discussion_route_mermaid(state),
            "```",
            "",
            "Plain-text fallback:",
            "",
            discussion_fallback(state),
            "",
        ]
    )
    if state.get("schema_version") == 3:
        parts.extend([_discussion_semantics_v3(state), ""])
    if state.get("schema_version") == 2:
        parts.extend([_discussion_semantics_v2(state), ""])
    parts.extend(
        [
            "## Discussion state",
            "",
            "```json",
            json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True),
            "```",
        ]
    )
    rendered = "\n".join(parts) + "\n"
    return rendered


def validate_discussion_artifact(text: str) -> dict[str, object]:
    block = _section(text, "Discussion state")
    match = re.fullmatch(r"```json\n(.*)\n```", block, flags=re.DOTALL)
    if match is None:
        fail("Discussion state must be one JSON fenced block")
    state = normalize_discussion_state(_decode_json(match.group(1), "Discussion state"))
    expected = render_discussion_artifact(state)
    if text != expected:
        fail("Discussion artifact graph, fallback, headers, or state drifted from the canonical renderer")
    return state


def _frontier_by_id(state: dict[str, object]) -> dict[str, dict[str, object]]:
    return {str(item["id"]): item for item in state.get("frontier", [])}


def _frontier_equal(left: dict[str, object], right: dict[str, object]) -> bool:
    left_payload = {
        "frontier": left.get("frontier"),
        "current_batch": left.get("current_batch"),
    }
    right_payload = {
        "frontier": right.get("frontier"),
        "current_batch": right.get("current_batch"),
    }
    return json.dumps(left_payload, ensure_ascii=False, sort_keys=True) == json.dumps(
        right_payload,
        ensure_ascii=False,
        sort_keys=True,
    )


def _validate_frontier_transition(
    old: dict[str, object],
    state: dict[str, object],
    request: dict[str, object],
) -> None:
    if _frontier_equal(old, state):
        return
    old_items = _frontier_by_id(old)
    new_items = _frontier_by_id(state)
    missing = set(old_items) - set(new_items)
    if missing:
        fail("Discussion update cannot remove existing frontier ids")
    max_old_id = max(
        (_frontier_number(item_id) for item_id in old_items),
        default=0,
    )
    for item_id in set(new_items) - set(old_items):
        if _frontier_number(item_id) <= max_old_id:
            fail("Discussion update must allocate monotonically increasing frontier ids")
    old_current = {
        str(item["id"])
        for item in old["frontier"]
        if item["status"] == "current"
    }
    unresolved = [
        item_id
        for item_id in old_current
        if new_items[item_id]["status"] == "current"
    ]
    if unresolved:
        fail("answered-batch update must close or reject every prior-current item")
    for item_id, old_item in old_items.items():
        new_item = new_items[item_id]
        if old_item["status"] in {"closed", "rejected"} and old_item != new_item:
            fail("closed and rejected Discussion frontier items are immutable")
        if old_item["status"] == "current" and new_item["status"] not in {
            "closed",
            "rejected",
        }:
            fail("a current Discussion frontier item must close or reject")
        if old_item["status"] == "open":
            for stable in ("id", "title", "level"):
                if old_item[stable] != new_item[stable]:
                    fail("open Discussion frontier items retain id, title, and level")
            changed_mutable = any(
                old_item[field] != new_item[field]
                for field in FRONTIER_MUTABLE_FIELDS
            )
            if changed_mutable and new_item["status"] == "open":
                reasons = request.get("frontier_delta_reasons")
                if (
                    not isinstance(reasons, dict)
                    or not isinstance(reasons.get(item_id), str)
                    or not reasons[item_id].strip()
                ):
                    fail("changed open Discussion frontier items require frontier_delta_reasons")
                newly_resolved = [
                    dep
                    for dep in old_item["depends_on"]
                    if dep in new_items
                    and old_items[str(dep)]["status"] in {"open", "current"}
                    and new_items[str(dep)]["status"] == "closed"
                ]
                if not newly_resolved or not any(
                    dep in reasons[item_id] for dep in newly_resolved
                ):
                    fail("frontier_delta_reasons must name a newly resolved dependency")


def _question_by_id(state: dict[str, object]) -> dict[str, dict[str, object]]:
    return {str(item["id"]): item for item in state.get("questions", [])}


def _question_payload_equal(
    left: dict[str, object],
    right: dict[str, object],
) -> bool:
    left_payload = {
        "questions": left.get("questions"),
        "current_question": left.get("current_question"),
    }
    right_payload = {
        "questions": right.get("questions"),
        "current_question": right.get("current_question"),
    }
    return json.dumps(left_payload, ensure_ascii=False, sort_keys=True) == json.dumps(
        right_payload,
        ensure_ascii=False,
        sort_keys=True,
    )


def _validate_question_transition(
    old: dict[str, object],
    state: dict[str, object],
) -> None:
    if _question_payload_equal(old, state):
        return
    old_items = _question_by_id(old)
    new_items = _question_by_id(state)
    if set(old_items) - set(new_items):
        fail("Discussion update cannot remove existing question ids")
    max_old_id = max(
        (_frontier_number(item_id) for item_id in old_items),
        default=0,
    )
    for item_id in set(new_items) - set(old_items):
        if _frontier_number(item_id) <= max_old_id:
            fail("Discussion update must allocate monotonically increasing question ids")
    old_current = old.get("current_question")
    if isinstance(old_current, str):
        if new_items[old_current]["status"] not in {"answered", "rejected"}:
            fail("Discussion update must answer or reject the prior current question")
    for item_id, old_item in old_items.items():
        new_item = new_items[item_id]
        if old_item["status"] in {"answered", "rejected"}:
            if old_item != new_item:
                fail("answered and rejected Discussion questions are immutable")
            continue
        stable_fields = set(old_item) - {"status", "resolution"}
        if any(old_item[field] != new_item.get(field) for field in stable_fields):
            fail("open and current Discussion question wording is immutable")
        allowed = {
            "open": {"open", "current", "answered", "rejected"},
            "current": {"answered", "rejected"},
        }[str(old_item["status"])]
        if new_item["status"] not in allowed:
            fail("Discussion question lifecycle moved backward")


def _attach_discussion_migration_source(
    state: dict[str, object],
    active_source_text: str | None,
) -> dict[str, object]:
    if active_source_text is None:
        fail("legacy Discussion migration requires exact source text")
    state["migration_source"] = {
        "path": DISCUSSION_CURRENT,
        "sha256": hashlib.sha256(active_source_text.encode("utf-8")).hexdigest(),
        "source_text": active_source_text,
    }
    return normalize_discussion_state_v3(state)


def _validate_v1_to_v3_migration(
    prior: dict[str, object],
    state: dict[str, object],
) -> None:
    if state["mode"] != "dialogue":
        fail("active v1 Discussion migration must enter dialogue mode")
    if not set(prior["settled"]).issubset(set(state["settled"])):
        fail("v1 Discussion migration must preserve settled items")
    prompts = {str(item["prompt"]) for item in state["questions"]}
    preserved = prompts.union(set(state["settled"]))
    if not set(prior["still_open"]).issubset(preserved):
        fail("v1 Discussion migration must preserve every still_open item")
    for field in ("blockers", "key_evidence"):
        if not set(prior[field]).issubset(set(state[field])):
            fail(f"v1 Discussion migration must preserve {field}")


def _validate_mode_transition(
    old: dict[str, object],
    state: dict[str, object],
    request: dict[str, object],
) -> None:
    reason = request.get("mode_transition_reason")
    if not isinstance(reason, str) or not reason.strip():
        fail("Discussion mode transition requires mode_transition_reason")
    resolution = request.get("mode_transition_resolution")
    if not isinstance(resolution, str) or not resolution.strip():
        fail("Discussion mode transition requires mode_transition_resolution")
    if resolution.strip() not in state["settled"]:
        fail("mode_transition_resolution must be recorded in settled")
    if not set(old["settled"]).issubset(set(state["settled"])):
        fail("Discussion mode transition must preserve settled items")
    if not set(old["key_evidence"]).issubset(set(state["key_evidence"])):
        fail("Discussion mode transition must preserve key evidence")


def validate_discussion_transition(
    prior: dict[str, object] | None,
    proposed: dict[str, object],
    request: dict[str, object],
    *,
    active_source_text: str | None = None,
) -> dict[str, object]:
    state = normalize_discussion_state_v3(proposed)
    if prior is None:
        return state
    if prior.get("schema_version") == 1:
        old_v1 = normalize_discussion_state_v1(prior)
        _validate_v1_to_v3_migration(old_v1, state)
        return _attach_discussion_migration_source(state, active_source_text)
    if prior.get("schema_version") == 2:
        old_v2 = normalize_discussion_state_v2(prior)
        if state["mode"] != "grill":
            fail("active v2 Discussion migration must enter grill mode")
        _validate_frontier_transition(old_v2, state, request)
        return _attach_discussion_migration_source(state, active_source_text)
    old = normalize_discussion_state_v3(prior)
    if old["mode"] != state["mode"]:
        _validate_mode_transition(old, state, request)
        return state
    if state["mode"] == "grill":
        _validate_frontier_transition(old, state, request)
    else:
        _validate_question_transition(old, state)
    return state


# Compatibility exports deliberately still render through the one canonical state
# renderer; callers cannot construct a second markdown format.
def render_artifact(record: dict[str, object], *, status: str = "active", updated: str | None = None, superseded_by: str | None = None) -> str:
    state = dict(record)
    state.setdefault("slug", record.get("topic", "discussion"))
    state["status"] = status
    state["updated"] = updated or record.get("updated") or date.today().isoformat()
    state["superseded_by"] = None if superseded_by in {None, "none"} else superseded_by
    return render_discussion_artifact(state)


def validate_artifact(text: str, *, operation: str | None = None, entry: dict[str, object] | None = None) -> dict[str, object]:
    del operation, entry
    return validate_discussion_artifact(text)


def discussion_revision(root: Path) -> str:
    current = safe_read_bytes(root, DISCUSSION_CURRENT, optional=True) or b""
    return _hash(b"discussion-v5", current)


def discussion_active(root: Path) -> dict[str, object] | None:
    text = safe_read_text(root, DISCUSSION_CURRENT, optional=True)
    return None if text is None else validate_discussion_artifact(text)


def discussion_schema(operation: str) -> dict[str, object]:
    if operation not in {"create", "update", "close", "replace", "supersede"}:
        fail("Discussion schema operation must be create, update, close, replace, or supersede")
    record: dict[str, object] = {
        "schema_version": 3,
        "artifact_type": "discussion",
        "slug": "discussion-slug",
        "title": "Discussion title",
        "updated": "YYYY-MM-DD",
        "mode": "dialogue",
        "goal": "The user outcome this discussion serves.",
        "current_branch": "The current line of thought.",
        "return_path": "Resume at the current unresolved question.",
        "blockers": [],
        "convergence": "The user has enough shared context to choose the next route.",
        "key_evidence": ["One compact evidence statement."],
        "settled": ["One conclusion that should not be reopened without new evidence."],
        "synthesis": ["The current substantive synthesis."],
        "tensions": ["The material tension that keeps the discussion open."],
        "questions": [
            {
                "id": "Q1",
                "kind": "open",
                "status": "current" if operation != "close" else "answered",
                "prompt": "What would most improve or redirect this synthesis?",
                "resolution": (
                    None
                    if operation != "close"
                    else {"kind": "text", "answer": "The discussion is complete."}
                ),
            }
        ],
        "current_question": "Q1" if operation != "close" else None,
    }
    return {
        "schema_version": 3,
        "operation": operation,
        "expected_revision": "<revision from inspect>",
        "record": record,
        "close_status": "accepted" if operation == "close" else None,
    }


def _archive_path(root: Path, slug: str, updated: str) -> str:
    number = 1
    while True:
        suffix = "" if number == 1 else f"-{number}"
        candidate = f"docs/teamwork/discussion/{updated}-{slug}{suffix}.md"
        if safe_read_bytes(root, candidate, optional=True) is None:
            return candidate
        number += 1
        if number > 1000:
            fail("too many Discussion archive filename collisions")


def _merge_discussion_record(old: dict[str, object], record: object, *, active: bool) -> dict[str, object]:
    if not isinstance(record, dict):
        fail("Discussion request record must be an object")
    if record.get("schema_version") == 3 and old.get("schema_version") in {1, 2}:
        merged = dict(record)
    else:
        merged = {
            key: value
            for key, value in old.items()
            if key not in {"status", "superseded_by"}
        }
    merged.update(record)
    merged["status"] = "active" if active else merged.get("status", "accepted")
    merged["superseded_by"] = None
    return normalize_discussion_state(merged)


def _superseded_discussion_archive(state: dict[str, object], superseded_by: str) -> dict[str, object]:
    archive = dict(state)
    archive["status"] = "superseded"
    archive["superseded_by"] = superseded_by
    if archive.get("schema_version") in {2, 3} and (
        archive.get("schema_version") == 2 or archive.get("mode") == "grill"
    ):
        frontier = []
        for item in archive["frontier"]:
            next_item = dict(item)
            if next_item["status"] in {"open", "current"}:
                next_item["status"] = "rejected"
                next_item["resolution"] = {"kind": "rejected", "reason": "Superseded by successor discussion."}
            frontier.append(next_item)
        archive["frontier"] = frontier
        archive["current_batch"] = []
        if archive.get("schema_version") == 3:
            return normalize_discussion_state_v3(archive)
        return normalize_discussion_state_v2(archive)
    if archive.get("schema_version") == 3:
        questions = []
        for item in archive["questions"]:
            next_item = dict(item)
            if next_item["status"] in {"open", "current"}:
                next_item["status"] = "rejected"
                next_item["resolution"] = {
                    "kind": "rejected",
                    "reason": "Superseded by successor discussion.",
                }
            questions.append(next_item)
        archive["questions"] = questions
        archive["current_question"] = None
        return normalize_discussion_state_v3(archive)
    archive["still_open"] = []
    return normalize_discussion_state_v1(archive)


def inspect_discussion(root: Path) -> dict[str, object]:
    with locked_memory(root):
        ensure_no_migration_intermediate(root)
        require_initialized_memory(root)
        recovered = recover_transaction(root, DISCUSSION_MARKER, ("docs/teamwork/discussion/",), "discussion")
        active = discussion_active(root)
        return {
            "initialized": True,
            "recovered": recovered,
            "revision": discussion_revision(root),
            "active": None if active is None else {"path": DISCUSSION_CURRENT, "state": active},
        }


def apply_discussion(root: Path, request: dict[str, object]) -> dict[str, object]:
    if request.get("schema_version") != 3:
        fail("Discussion request schema_version must be 3")
    operation = request.get("operation")
    if operation not in {"create", "update", "close", "replace", "supersede"}:
        fail("Discussion request operation is invalid")
    expected = request.get("expected_revision")
    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
        fail("Discussion request expected_revision must come from inspect")
    with locked_memory(root):
        require_initialized_memory(root)
        recover_transaction(root, DISCUSSION_MARKER, ("docs/teamwork/discussion/",), "discussion")
        active_text = safe_read_text(root, DISCUSSION_CURRENT, optional=True)
        active = None if active_text is None else validate_discussion_artifact(active_text)
        if expected != discussion_revision(root):
            fail("stale Discussion expected_revision; run inspect again")
        record = request.get("record")
        outputs: dict[str, Output]
        changed: list[str]
        if operation == "create":
            if active is not None:
                fail("cannot create Discussion while an active discussion exists")
            state = validate_discussion_transition(None, _merge_discussion_record({}, record, active=True), request)
            rendered = render_discussion_artifact(state).encode("utf-8")
            outputs = {DISCUSSION_CURRENT: Output(rendered)}
            changed = [DISCUSSION_CURRENT]
            result_path: str | None = DISCUSSION_CURRENT
            result_active: dict[str, object] | None = state
        elif operation == "update":
            if active is None:
                fail("cannot update without an active Discussion")
            state = validate_discussion_transition(active, _merge_discussion_record(active, record, active=True), request, active_source_text=active_text)
            if state["slug"] != active["slug"]:
                fail("update cannot change Discussion slug; use replace or supersede")
            rendered = render_discussion_artifact(state).encode("utf-8")
            if active_text is not None and rendered == active_text.encode("utf-8"):
                return {"path": DISCUSSION_CURRENT, "active": state, "revision": discussion_revision(root), "changed_paths": []}
            outputs = {DISCUSSION_CURRENT: Output(rendered)}
            changed = [DISCUSSION_CURRENT]
            result_path = DISCUSSION_CURRENT
            result_active = state
        elif operation == "close":
            if active is None:
                fail("cannot close without an active Discussion")
            close_status = request.get("close_status", "accepted")
            if close_status not in {"accepted", "superseded"}:
                fail("Discussion close_status must be accepted or superseded")
            state = dict(active)
            if isinstance(record, dict):
                state = _merge_discussion_record(active, record, active=False)
            state["status"] = close_status
            if state.get("schema_version") == 3:
                state = validate_discussion_transition(active, state, request, active_source_text=active_text)
            else:
                fail("closing a legacy Discussion requires a schema v3 migration record")
            if close_status == "superseded":
                state["superseded_by"] = checked_relative(request.get("superseded_by"), "Discussion superseded_by")
            else:
                state["superseded_by"] = None
            state = normalize_discussion_state_v3(state)
            archive = _archive_path(root, str(active["slug"]), str(state["updated"]))
            outputs = {
                archive: Output(render_discussion_artifact(state).encode("utf-8")),
                DISCUSSION_CURRENT: Output(None),
            }
            changed = [archive, DISCUSSION_CURRENT]
            result_path = archive
            result_active = None
        else:
            if active is None:
                fail("cannot replace or supersede without an active Discussion")
            state = validate_discussion_transition(None, _merge_discussion_record({}, record, active=True), request)
            archive_state = _superseded_discussion_archive(active, DISCUSSION_CURRENT)
            archive = _archive_path(root, str(active["slug"]), str(archive_state["updated"]))
            outputs = {
                archive: Output(render_discussion_artifact(archive_state).encode("utf-8")),
                DISCUSSION_CURRENT: Output(render_discussion_artifact(state).encode("utf-8")),
            }
            changed = [archive, DISCUSSION_CURRENT]
            result_path = DISCUSSION_CURRENT
            result_active = state
        created_directories: list[str] = []
        ensure_directory(root, "docs/teamwork/discussion", created=created_directories)
        apply_transaction(
            root,
            kind="discussion",
            marker=DISCUSSION_MARKER,
            prefixes=("docs/teamwork/discussion/",),
            outputs=outputs,
            created_directories=created_directories,
        )
        # Read the final target through the canonical parser before reporting it.
        if result_active is not None:
            discussion_active(root)
        return {
            "path": result_path,
            "active": result_active,
            "revision": discussion_revision(root),
            "changed_paths": changed,
        }


# ---------------------------------------------------------------------------
# Design: template-owned renderer and active.design transaction.


def design_template_path() -> Path:
    return Path(__file__).resolve().parents[1] / "templates/teamwork-memory/teamwork-design-template.md"


def _read_design_template() -> str:
    path = design_template_path()
    try:
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            fail("Design template must be a regular non-symlink file")
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"cannot read Design template: {exc}")


def normalize_design_state(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        fail("Design state must be an object")
    schema_version = value.get("schema_version")
    if schema_version not in {1, 2, 3}:
        fail("Design schema_version must be 1, 2, or 3")
    acceptance = "accepted"
    blockers: list[str] = []
    if schema_version == 3:
        acceptance = value.get("acceptance")
        if acceptance not in {"pending", "accepted", "blocked"}:
            fail("Design acceptance must be pending, accepted, or blocked")
        blockers = require_text_list(value.get("blockers"), "Design blockers")
        if acceptance == "blocked" and not blockers:
            fail("blocked Design must record at least one blocker")
        if acceptance != "blocked" and blockers:
            fail("only a blocked Design may record blockers")
    elif "acceptance" in value or "blockers" in value:
        fail("Design acceptance and blockers require schema_version 3")
    status = value.get("status")
    if status not in {"current", "superseded"}:
        fail("Design status must be current or superseded")
    superseded_by = value.get("superseded_by")
    if status == "current":
        if superseded_by is not None:
            fail("current Design cannot have superseded_by")
    else:
        superseded_by = checked_relative(superseded_by, "Design superseded_by")
        if not superseded_by.startswith("docs/teamwork/design/"):
            fail("Design superseded_by must stay in docs/teamwork/design/")
    alternatives = require_text_list(value.get("alternatives"), "Design alternatives", minimum=1, maximum=3)
    exclusions = require_text_list(value.get("exclusions"), "Design exclusions")
    rejected_raw = value.get("rejected_alternatives")
    if not isinstance(rejected_raw, list) or not rejected_raw:
        fail("Design rejected_alternatives must record material alternatives and reasons")
    rejected: list[dict[str, str]] = []
    for position, item in enumerate(rejected_raw):
        if not isinstance(item, dict):
            fail("Design rejected_alternatives items must be objects")
        rejected.append(
            {
                "option": require_text(item.get("option"), f"Design rejected_alternatives[{position}].option"),
                "reason": require_text(item.get("reason"), f"Design rejected_alternatives[{position}].reason"),
            }
        )
    if len(alternatives) == 1 and (not exclusions or not rejected):
        fail("a one-safe-path Design requires explicit exclusions and rejected reasons")
    state: dict[str, object] = {
        "schema_version": schema_version,
        "artifact_type": "design",
        "slug": require_slug(value.get("slug")),
        "title": require_text(value.get("title"), "Design title"),
        "updated": require_date(value.get("updated"), "Design updated"),
        "status": status,
        "superseded_by": superseded_by,
        "evidence_waves": require_text_list(value.get("evidence_waves"), "Design evidence_waves", minimum=1),
        "alternatives": alternatives,
        "exclusions": exclusions,
        "challenge_result": require_text(value.get("challenge_result"), "Design challenge_result"),
        "decision_frontier": require_text_list(value.get("decision_frontier"), "Design decision_frontier"),
        "settled": require_text_list(value.get("settled"), "Design settled", minimum=1),
        "open_items": require_text_list(value.get("open_items"), "Design open_items"),
        "plan_handoff": require_text(value.get("plan_handoff"), "Design plan_handoff"),
        "review_handoff": require_text(value.get("review_handoff"), "Design review_handoff"),
        "decision_rule": require_text(value.get("decision_rule"), "Design decision_rule"),
        "recommendation": require_text(value.get("recommendation"), "Design recommendation"),
        "largest_downside": require_text(value.get("largest_downside"), "Design largest_downside"),
        "rejected_alternatives": rejected,
        "residual_uncertainty": require_text(value.get("residual_uncertainty"), "Design residual_uncertainty"),
    }
    if schema_version == 3:
        state["acceptance"] = acceptance
        state["blockers"] = blockers
    return state


def design_acceptance(state: dict[str, object]) -> str:
    """Legacy v1/v2 Design artifacts are accepted without changing their bytes."""

    return str(state["acceptance"]) if state["schema_version"] == 3 else "accepted"


def _design_index_metadata(acceptance: str) -> tuple[str, str, str]:
    if acceptance == "accepted":
        return "accepted", "current", "canonical"
    if acceptance == "pending":
        return "candidate", "candidate", "candidate"
    if acceptance == "blocked":
        return "blocked", "candidate", "candidate"
    fail("Design acceptance is invalid")


def _items(values: list[object]) -> str:
    return "; ".join(str(value) for value in values) or "none"


def design_route_mermaid_v1(state: dict[str, object]) -> str:
    rejected = "; ".join(f"{row['option']}: {row['reason']}" for row in state["rejected_alternatives"])
    return "\n".join(
        (
            "flowchart TD",
            f'    evidence["Evidence waves: {_mermaid_label(_items(state["evidence_waves"]))}"] --> alternatives["Alternatives: {_mermaid_label(_items(state["alternatives"]))}"]',
            f'    alternatives --> exclusions["Exclusions: {_mermaid_label(_items(state["exclusions"]))}"]',
            f'    exclusions --> challenge["Challenge: {_mermaid_label(str(state["challenge_result"]))}"]',
            f'    challenge --> rule["Decision rule: {_mermaid_label(str(state["decision_rule"]))}"]',
            f'    rule --> recommendation["Recommendation: {_mermaid_label(str(state["recommendation"]))}"]',
            f'    recommendation --> downside["Largest downside: {_mermaid_label(str(state["largest_downside"]))}"]',
            f'    recommendation --> rejected["Rejected: {_mermaid_label(rejected)}"]',
            f'    recommendation --> frontier["Decision frontier: {_mermaid_label(_items(state["decision_frontier"]))}"]',
            f'    frontier --> settled["Settled: {_mermaid_label(_items(state["settled"]))}"]',
            f'    frontier --> open["Open: {_mermaid_label(_items(state["open_items"]))}"]',
            f'    settled --> plan["Plan handoff: {_mermaid_label(str(state["plan_handoff"]))}"]',
            f'    open --> review["Review handoff: {_mermaid_label(str(state["review_handoff"]))}"]',
            f'    review --> uncertainty["Residual uncertainty: {_mermaid_label(str(state["residual_uncertainty"]))}"]',
            f'    uncertainty --> lifecycle["Lifecycle: {_mermaid_label(str(state["status"]))}"]',
        )
    )


def design_route_mermaid_v2(state: dict[str, object]) -> str:
    frontier_status = f"{len(state['decision_frontier'])} open" if state["decision_frontier"] else "none"
    open_status = f"{len(state['open_items'])} open" if state["open_items"] else "closed"
    decision_status = design_acceptance(state) if state["schema_version"] == 3 else state["status"]
    return "\n".join(
        (
            "flowchart LR",
            f'    evidence["Evidence · {len(state["evidence_waves"])}"] --> alternatives["Alternatives · {len(state["alternatives"])}"]',
            f'    alternatives --> challenge["Challenge · recorded"]',
            f'    challenge --> decision["Decision · {decision_status}"]',
            f'    decision --> frontier["Frontier · {frontier_status}"]',
            f'    frontier --> handoff["Handoff · {open_status}"]',
        )
    )


def design_route_mermaid(state: dict[str, object]) -> str:
    return design_route_mermaid_v2(state) if state.get("schema_version") in {2, 3} else design_route_mermaid_v1(state)


def design_route_fallback_v1(state: dict[str, object]) -> str:
    rejected = "; ".join(f"{row['option']} — {row['reason']}" for row in state["rejected_alternatives"])
    return "\n".join(
        (
            f"Evidence waves: {_items(state['evidence_waves'])}",
            f"Alternatives: {_items(state['alternatives'])}",
            f"Exclusions: {_items(state['exclusions'])}",
            f"Challenge result: {state['challenge_result']}",
            f"Decision rule: {state['decision_rule']}",
            f"Recommendation: {state['recommendation']}",
            f"Largest downside: {state['largest_downside']}",
            f"Rejected alternatives: {rejected}",
            f"Decision frontier: {_items(state['decision_frontier'])}",
            f"Settled: {_items(state['settled'])}",
            f"Open: {_items(state['open_items'])}",
            f"Plan handoff: {state['plan_handoff']}",
            f"Review handoff: {state['review_handoff']}",
            f"Residual uncertainty: {state['residual_uncertainty']}",
            f"Lifecycle: {state['status']}",
            f"Superseded by: {state['superseded_by'] or 'none'}",
        )
    )


def design_route_fallback_v2(state: dict[str, object]) -> str:
    decision_status = design_acceptance(state) if state["schema_version"] == 3 else state["status"]
    return "\n".join(
        (
            f"Route: Evidence({len(state['evidence_waves'])}) -> Alternatives({len(state['alternatives'])}) -> Challenge(recorded) -> Decision({decision_status}) -> Frontier({len(state['decision_frontier'])}) -> Handoff",
            f"Settled: {len(state['settled'])}",
            f"Open: {len(state['open_items'])}",
            f"Superseded by: {state['superseded_by'] or 'none'}",
        )
    )


def design_route_fallback(state: dict[str, object]) -> str:
    return design_route_fallback_v2(state) if state.get("schema_version") in {2, 3} else design_route_fallback_v1(state)


def _design_semantics_v2(state: dict[str, object]) -> str:
    rejected = [f"{row['option']}: {row['reason']}" for row in state["rejected_alternatives"]]
    lines = [
        "## Readable design",
        "",
        "Evidence waves:",
        _bullets(state["evidence_waves"]),
        "",
        "Alternatives:",
        _bullets(state["alternatives"]),
        "",
        "Exclusions:",
        _bullets(state["exclusions"]),
        "",
        f"Challenge result: {state['challenge_result']}",
        f"Decision rule: {state['decision_rule']}",
    ]
    if state["schema_version"] == 3:
        lines.extend(
            (
                f"Acceptance: {design_acceptance(state)}",
                f"Blockers: {_items(state['blockers'])}",
            )
        )
    lines.extend(
        (
            f"Recommendation: {state['recommendation']}",
            f"Largest downside: {state['largest_downside']}",
            "",
            "Rejected alternatives:",
            _bullets(rejected),
            "",
            "Decision frontier:",
            _bullets(state["decision_frontier"]),
            "",
            "Settled:",
            _bullets(state["settled"]),
            "",
            "Open items:",
            _bullets(state["open_items"]),
            "",
            f"Plan handoff: {state['plan_handoff']}",
            f"Review handoff: {state['review_handoff']}",
            f"Residual uncertainty: {state['residual_uncertainty']}",
            "",
        )
    )
    return "\n".join(lines)


def render_design_artifact(value: object) -> str:
    state = normalize_design_state(value)
    tokens = {
        "lifecycle_status": str(state["status"]),
        "currentness": "current" if state["status"] == "current" else "superseded",
        "updated": str(state["updated"]),
        "superseded_by": str(state["superseded_by"] or "none"),
        "title": str(state["title"]),
        "route_mermaid": design_route_mermaid(state),
        "route_fallback": design_route_fallback(state),
        "design_state_json": json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True),
    }
    template = _read_design_template()
    placeholders = set(re.findall(r"\{\{([a-z_]+)\}\}", template))
    if placeholders != set(tokens):
        fail("Design template placeholders do not match the canonical renderer")
    rendered = template
    for key, item in tokens.items():
        rendered = rendered.replace("{{" + key + "}}", item)
    if "{{" in rendered or "}}" in rendered:
        fail("Design template has unresolved placeholders")
    if state.get("schema_version") in {2, 3}:
        rendered = rendered.replace("\n## Design state\n", "\n" + _design_semantics_v2(state) + "## Design state\n", 1)
    return rendered.rstrip() + "\n"


def validate_design_artifact(text: str) -> dict[str, object]:
    block = _section(text, "Design state")
    match = re.fullmatch(r"```json\n(.*)\n```", block, flags=re.DOTALL)
    if match is None:
        fail("Design state must be one JSON fenced block")
    state = normalize_design_state(_decode_json(match.group(1), "Design state"))
    if text != render_design_artifact(state):
        fail("Design artifact graph, fallback, headers, or state drifted from the canonical template renderer")
    return state


def design_path(state: dict[str, object]) -> str:
    return f"docs/teamwork/design/{state['updated']}-{state['slug']}.md"


def _index_entry(kind: str, path: str, state: dict[str, object], *, active: bool) -> dict[str, object]:
    if active and kind == "design":
        entry_status, currentness, authority = _design_index_metadata(design_acceptance(state))
    else:
        entry_status = "accepted" if active else "superseded"
        currentness = "current" if active else "historical"
        authority = "canonical" if active else "superseded"
    return {
        "topic": str(state["slug"]),
        "kind": kind,
        "title": str(state["title"]),
        "status": entry_status,
        "currentness": currentness,
        "authority": authority,
        "path": path,
        "linked": [],
        "evidence_paths": [path],
        "supersedes": [],
        "search_keys": [str(state["slug"])],
        "updated": str(state["updated"]),
        "summary": str(state.get("recommendation", state.get("current_unmet_claim", state["title"]))),
    }


def _validate_entry(entry: object, position: int, *, migration: bool = False) -> dict[str, object]:
    if not isinstance(entry, dict):
        fail(f"entries[{position}] must be an object")
    result = dict(entry)
    for key in ("topic", "kind", "title", "status", "currentness", "authority", "path", "updated", "summary"):
        if key not in result:
            fail(f"entries[{position}] is missing {key}")
    require_text(result["topic"], f"entries[{position}].topic")
    allowed_kinds = {"result", "progress", "design", "decision", "plan", "report", "research", "runbook"}
    if migration:
        allowed_kinds.add("discussion")
    if result["kind"] not in allowed_kinds:
        fail(f"entries[{position}].kind is invalid")
    require_text(result["title"], f"entries[{position}].title")
    if result["status"] not in {"active", "historical", "superseded", "blocked", "candidate", "accepted"}:
        fail(f"entries[{position}].status is invalid")
    if result["currentness"] not in {"current", "stale", "historical", "candidate"}:
        fail(f"entries[{position}].currentness is invalid")
    if result["authority"] not in {"canonical", "active-summary", "supporting", "candidate", "historical", "superseded"}:
        fail(f"entries[{position}].authority is invalid")
    result["path"] = checked_relative(result["path"], f"entries[{position}].path")
    require_date(result["updated"], f"entries[{position}].updated")
    require_text(result["summary"], f"entries[{position}].summary")
    for key in ("linked", "evidence_paths", "supersedes", "search_keys", "applies_to"):
        if key in result:
            require_text_list(result[key], f"entries[{position}].{key}")
    return result


def parse_index(text: str, *, migration: bool = False) -> dict[str, object]:
    index = _decode_json(text, "Teamwork index")
    if not isinstance(index, dict) or index.get("schema_version") != 1:
        fail("Teamwork index schema_version must be 1")
    require_date(index.get("last_updated"), "Teamwork index last_updated")
    if not isinstance(index.get("project"), dict):
        fail("Teamwork index project must be an object")
    project = index["project"]
    require_text(project.get("name"), "Teamwork index project.name")
    if project.get("root") != ".":
        fail("Teamwork index project.root must be .")
    require_text(project.get("description"), "Teamwork index project.description")
    active = index.get("active")
    if not isinstance(active, dict):
        fail("Teamwork index active must be an object")
    allowed = {"current", "collaborate", "design", "plan", "progress", "report", "results"}
    if migration:
        allowed.add("discussion")
    unknown = set(active) - allowed
    if unknown:
        if "discussion" in unknown:
            fail("ordinary Teamwork index must not mirror Discussion state")
        if "goal" in unknown:
            fail("Goal state is owned solely by active.progress")
        fail(f"Teamwork index active has unknown keys: {', '.join(sorted(unknown))}")
    if active.get("current") != CANONICAL_CURRENT:
        fail(f"active.current must be {CANONICAL_CURRENT}")
    if not isinstance(active.get("results"), list):
        fail("active.results must be an array")
    require_text_list(active["results"], "active.results")
    for pointer in ("design", "plan", "progress", "report", *(("discussion",) if migration else ())):
        value = active.get(pointer)
        if value is not None:
            active[pointer] = checked_relative(value, f"active.{pointer}")
            if active[pointer].startswith("docs/teamwork/discussion/"):
                if pointer != "discussion":
                    fail(f"active.{pointer} cannot point at Discussion state")
            elif pointer == "discussion":
                fail("active.discussion must point inside docs/teamwork/discussion/")
    collaborate = active.get("collaborate")
    if collaborate is not None:
        active["collaborate"] = checked_relative(collaborate, "active.collaborate")
        if active["collaborate"] != COLLABORATE_CURRENT:
            fail(f"active.collaborate must be null or {COLLABORATE_CURRENT}")
    raw_entries = index.get("entries")
    if not isinstance(raw_entries, list) or not raw_entries:
        fail("Teamwork index entries must be a non-empty array")
    entries = [_validate_entry(item, position, migration=migration) for position, item in enumerate(raw_entries)]
    index = dict(index)
    index["active"] = active
    index["entries"] = entries
    _normalize_legacy_workflow_report_slot(index)
    if migration:
        _validate_migration_pointer_metadata(index)
    else:
        _validate_pointer_metadata(index)
    return index


def _eligible(entry: dict[str, object]) -> bool:
    return (
        entry["status"] in {"active", "accepted"}
        and entry["currentness"] == "current"
        and entry["authority"] in {"canonical", "active-summary", "supporting"}
    )


def _pointer_eligible(pointer: str, entry: dict[str, object]) -> bool:
    if pointer == "collaborate":
        return (
            entry.get("artifact_type") == "collaborate"
            and entry.get("kind") == "decision"
            and entry.get("status") in {"active", "accepted", "blocked"}
            and entry.get("currentness") == "current"
            and entry.get("authority") == "canonical"
        )
    if pointer != "design":
        return _eligible(entry)
    if entry.get("kind") != "design":
        return False
    metadata = (entry.get("status"), entry.get("currentness"), entry.get("authority"))
    return metadata in {
        _design_index_metadata("accepted"),
        _design_index_metadata("pending"),
        _design_index_metadata("blocked"),
    }


def _pointer_shape(pointer: str, path: str, entry: dict[str, object]) -> bool:
    if pointer == "design":
        return entry["kind"] == "design" and DESIGN_PATH_RE.fullmatch(path) is not None
    if pointer == "plan":
        return entry["kind"] == "plan" and path.startswith("docs/teamwork/plans/") and path.endswith(".md")
    if pointer == "progress":
        return entry["kind"] == "progress" and GOAL_PATH_RE.fullmatch(path) is not None
    if pointer == "report":
        return entry["kind"] == "report"
    if pointer == "collaborate":
        return entry.get("artifact_type") == "collaborate" and path == COLLABORATE_CURRENT
    return True


def _validate_pointer_metadata(index: dict[str, object]) -> None:
    active = index["active"]
    assert isinstance(active, dict)
    entries = index["entries"]
    assert isinstance(entries, list)
    used: set[str] = set()
    for pointer in ("design", "plan", "progress"):
        raw = active.get(pointer)
        current_entries = [
            entry
            for entry in entries
            if isinstance(entry, dict)
            and entry.get("kind") == ("progress" if pointer == "progress" else pointer)
            and _pointer_eligible(pointer, entry)
        ]
        if raw is None:
            if current_entries:
                fail(f"active.{pointer} is null while a current eligible artifact exists")
            continue
        assert isinstance(raw, str)
        matching = [
            entry
            for entry in entries
            if isinstance(entry, dict)
            and entry.get("path") == raw
            and _pointer_eligible(pointer, entry)
            and _pointer_shape(pointer, raw, entry)
        ]
        if not matching:
            fail(f"active.{pointer} has no eligible matching entry")
        if len(matching) != 1 or len(current_entries) != 1:
            fail(f"active.{pointer} is ambiguous")
        if raw in used:
            fail("one artifact path cannot own more than one active pointer")
        used.add(raw)
    current_collaborate = [
        entry
        for entry in entries
        if isinstance(entry, dict) and _pointer_eligible("collaborate", entry)
    ]
    raw_collaborate = active.get("collaborate")
    if raw_collaborate is None:
        if current_collaborate:
            fail("active.collaborate is null while a current Collaborate artifact exists")
    else:
        assert isinstance(raw_collaborate, str)
        matching = [
            entry
            for entry in current_collaborate
            if entry.get("path") == raw_collaborate
            and _pointer_shape("collaborate", raw_collaborate, entry)
        ]
        if len(matching) != 1 or len(current_collaborate) != 1:
            fail("active.collaborate is ambiguous")
        if raw_collaborate in used:
            fail("one artifact path cannot own more than one active pointer")
        used.add(raw_collaborate)
    _validate_workflow_pointer_metadata(index, used)


def _validate_migration_pointer_metadata(index: dict[str, object]) -> None:
    """Validate explicit legacy pointers without enforcing current-runtime uniqueness.

    Older released indexes may retain several eligible current Plan rows or a
    migration-only Discussion pointer.  An exact active pointer still selects
    one source unambiguously for semantic conversion; normal runtime continues
    to reject these shapes through ``_validate_pointer_metadata``.
    """

    active = index["active"]
    entries = index["entries"]
    assert isinstance(active, dict) and isinstance(entries, list)
    used: set[str] = set()
    for pointer in ("design", "plan", "progress", "collaborate", "discussion"):
        raw = active.get(pointer)
        if raw is None:
            continue
        assert isinstance(raw, str)
        if pointer == "discussion":
            matching = [
                entry
                for entry in entries
                if isinstance(entry, dict)
                and entry.get("path") == raw
                and entry.get("kind") == "discussion"
                and _eligible(entry)
            ]
        else:
            matching = [
                entry
                for entry in entries
                if isinstance(entry, dict)
                and entry.get("path") == raw
                and _pointer_eligible(pointer, entry)
                and _pointer_shape(pointer, raw, entry)
            ]
        if len(matching) != 1:
            fail(f"active.{pointer} has no unique migration source")
        if raw in used:
            fail("one artifact path cannot own more than one migration pointer")
        used.add(raw)
    _validate_workflow_pointer_metadata(index, used)


def _workflow_artifact_path(workflow: str, updated: str, slug: str) -> str:
    config = WORKFLOW_CONFIG[workflow]
    return f"{config['directory']}/{updated}-{slug}.md"


def _workflow_artifact_slot(workflow: str) -> str:
    return WORKFLOW_CONFIG[workflow]["active"]


def _workflow_artifact_kind(workflow: str) -> str:
    return WORKFLOW_CONFIG[workflow]["kind"]


def _is_workflow_entry(entry: dict[str, object]) -> bool:
    return entry.get("artifact_type") == WORKFLOW_ARTIFACT_KIND


def _normalize_legacy_workflow_report_slot(index: dict[str, object]) -> None:
    """Interpret the old workflow report singleton as a results entry.

    This is intentionally narrow: only a current workflow-artifact report that
    now belongs to active.results is moved. Ordinary active.report pointers keep
    their existing meaning, and malformed workflow pointers fail before callers
    can inspect or persist over them.
    """

    active = index["active"]
    assert isinstance(active, dict)
    report_path = active.get("report")
    if not isinstance(report_path, str):
        return
    entries = index["entries"]
    assert isinstance(entries, list)
    workflow_matches = [
        entry
        for entry in entries
        if isinstance(entry, dict)
        and entry.get("path") == report_path
        and _is_workflow_entry(entry)
    ]
    if not workflow_matches:
        return
    if len(workflow_matches) != 1:
        fail("active.report legacy workflow artifact is ambiguous")
    entry = workflow_matches[0]
    if not _eligible(entry):
        fail("active.report cannot point at a stale workflow artifact")
    eligible_matches = [
        item
        for item in entries
        if isinstance(item, dict)
        and item.get("path") == report_path
        and _eligible(item)
    ]
    if len(eligible_matches) != 1:
        fail("active.report legacy workflow artifact conflicts with another current entry")
    workflow = entry.get("workflow")
    if workflow not in WORKFLOW_CONFIG:
        fail("active.report legacy workflow artifact has an unsupported workflow")
    assert isinstance(workflow, str)
    if entry.get("kind") != "report" or _workflow_artifact_slot(workflow) != "results":
        fail("active.report contains a workflow artifact outside the legacy report slot")
    if str(entry["path"]) != _workflow_entry_path(entry):
        fail("active.report legacy workflow artifact path does not match its derived destination")
    results = list(active["results"])
    if report_path not in results:
        results.append(report_path)
    active["results"] = results
    active["report"] = None


def _workflow_entry_path(entry: dict[str, object]) -> str:
    workflow = entry.get("workflow")
    if workflow not in WORKFLOW_CONFIG:
        fail("workflow-artifact index entry has an unsupported workflow")
    slug = require_slug(entry.get("topic"), "workflow-artifact entry topic")
    updated = require_date(entry.get("updated"), "workflow-artifact entry updated")
    assert isinstance(workflow, str)
    return _workflow_artifact_path(workflow, updated, slug)


def _active_path_contains(active: dict[str, object], slot: str, path: str) -> bool:
    if slot == "results":
        results = active.get("results")
        return isinstance(results, list) and path in results
    return active.get(slot) == path


def _validate_workflow_pointer_metadata(index: dict[str, object], used: set[str]) -> None:
    active = index["active"]
    assert isinstance(active, dict)
    entries = index["entries"]
    assert isinstance(entries, list)
    current_by_slot: dict[str, list[str]] = {"plan": [], "report": [], "results": []}
    for entry in entries:
        if not isinstance(entry, dict) or not _is_workflow_entry(entry) or not _eligible(entry):
            continue
        expected = _workflow_entry_path(entry)
        path = str(entry["path"])
        if path != expected:
            fail("workflow-artifact index entry path does not match its derived destination")
        workflow = str(entry["workflow"])
        if entry["kind"] != _workflow_artifact_kind(workflow):
            fail("workflow-artifact index entry kind does not match its workflow")
        slot = _workflow_artifact_slot(workflow)
        current_by_slot[slot].append(path)
        if not _active_path_contains(active, slot, path):
            fail(f"active.{slot} is missing a current workflow-artifact entry")
    for slot in ("plan", "report"):
        paths = current_by_slot[slot]
        if len(paths) > 1:
            fail(f"active.{slot} is ambiguous")
        if paths:
            raw = active.get(slot)
            if raw != paths[0]:
                fail(f"active.{slot} does not match its current workflow-artifact entry")
            if slot != "plan" and paths[0] in used:
                fail("one artifact path cannot own more than one active pointer")
            used.add(paths[0])


def _read_index(root: Path) -> tuple[str, dict[str, object]]:
    text = safe_read_text(root, INDEX_PATH)
    assert text is not None
    return text, parse_index(text)


def _serialize_index(index: dict[str, object]) -> str:
    return json.dumps(index, ensure_ascii=False, indent=2) + "\n"


def _find_entry(index: dict[str, object], path: str) -> tuple[int, dict[str, object]]:
    matches = [(position, entry) for position, entry in enumerate(index["entries"]) if entry["path"] == path]
    if len(matches) != 1:
        fail("active index artifact must have exactly one entry")
    return matches[0]


def _generic_active_entry(index: dict[str, object], path: str) -> dict[str, object] | None:
    matches = [
        entry
        for entry in index["entries"]
        if isinstance(entry, dict)
        and entry.get("path") == path
        and _is_workflow_entry(entry)
        and _eligible(entry)
    ]
    if len(matches) > 1:
        fail("active workflow artifact is ambiguous")
    return None if not matches else matches[0]


def _validate_plan_artifact(text: str) -> tuple[str, str]:
    header = re.search(r"(?m)^Artifact Type: plan$", text)
    updated = re.search(r"(?m)^Last Updated: (\d{4}-\d{2}-\d{2})$", text)
    title = re.search(r"(?m)^# (.+)$", text)
    if header is None or updated is None or title is None or not valid_date(updated.group(1)):
        fail("active Plan artifact does not have parseable canonical headers")
    return title.group(1), updated.group(1)


def _workflow_header(text: str, name: str) -> str:
    match = re.search(rf"(?m)^{re.escape(name)}: (.+)$", text)
    if match is None:
        fail(f"workflow artifact is missing {name}")
    return match.group(1)


def parse_workflow_artifact_headers(text: str) -> dict[str, str]:
    title = re.search(r"(?m)^# (.+)$", text)
    if title is None:
        fail("workflow artifact is missing its H1 title")
    updated = _workflow_header(text, "Last Updated")
    if not valid_date(updated):
        fail("workflow artifact Last Updated must be a valid YYYY-MM-DD date")
    return {
        "artifact_kind": _workflow_header(text, "Artifact Kind"),
        "artifact_type": _workflow_header(text, "Artifact Type"),
        "workflow": _workflow_header(text, "Workflow"),
        "updated": updated,
        "consumer": _workflow_header(text, "Consumer"),
        "source_revision": _workflow_header(text, "Source Revision"),
        "title": title.group(1),
    }


def validate_workflow_artifact_entry(text: str, entry: dict[str, object]) -> None:
    headers = parse_workflow_artifact_headers(text)
    workflow = entry.get("workflow")
    if workflow not in WORKFLOW_CONFIG:
        fail("workflow-artifact entry has an unsupported workflow")
    assert isinstance(workflow, str)
    expected = {
        "artifact_kind": _workflow_artifact_kind(workflow),
        "artifact_type": WORKFLOW_ARTIFACT_KIND,
        "workflow": workflow,
        "updated": str(entry["updated"]),
        "consumer": str(entry["consumer"]),
        "source_revision": str(entry["source_revision"]),
        "title": str(entry["title"]),
    }
    if headers != expected:
        fail("workflow artifact headers do not agree with its index entry")


def validate_currentness(root: Path, index: dict[str, object]) -> None:
    """Fail closed when any active artifact is missing, unsafe, or disagrees."""

    _validate_pointer_metadata(index)
    active = index["active"]
    assert isinstance(active, dict)
    for pointer in ("design", "plan", "progress"):
        path = active.get(pointer)
        if path is None:
            continue
        assert isinstance(path, str)
        text = safe_read_text(root, path)
        assert text is not None
        _, entry = _find_entry(index, path)
        if pointer == "design":
            state = validate_design_artifact(text)
            expected_metadata = _design_index_metadata(design_acceptance(state))
            actual_metadata = (entry["status"], entry["currentness"], entry["authority"])
            if (
                state["status"] != "current"
                or state["title"] != entry["title"]
                or state["updated"] != entry["updated"]
                or design_path(state) != path
                or actual_metadata != expected_metadata
            ):
                fail("active.design artifact does not agree with its index entry")
        elif pointer == "plan":
            if _is_workflow_entry(entry):
                validate_workflow_artifact_entry(text, entry)
            else:
                title, updated = _validate_plan_artifact(text)
                if title != entry["title"] or updated != entry["updated"]:
                    fail("active.plan artifact does not agree with its index entry")
        else:
            state = validate_goal_artifact(text)
            if state["status"] != "active" or state["title"] != entry["title"] or state["updated"] != entry["updated"] or goal_path(state) != path:
                fail("active.progress artifact does not agree with its index entry")
    report_path = active.get("report")
    if isinstance(report_path, str):
        entry = _generic_active_entry(index, report_path)
        if entry is not None:
            text = safe_read_text(root, report_path)
            assert text is not None
            validate_workflow_artifact_entry(text, entry)
    for result_path in active["results"]:
        assert isinstance(result_path, str)
        entry = _generic_active_entry(index, result_path)
        if entry is not None:
            text = safe_read_text(root, result_path)
            assert text is not None
            validate_workflow_artifact_entry(text, entry)
    collaborate_path = active.get("collaborate")
    if isinstance(collaborate_path, str):
        text = safe_read_text(root, collaborate_path)
        assert text is not None
        state = validate_collaborate_artifact(text)
        _, entry = _find_entry(index, collaborate_path)
        if (
            collaborate_path != COLLABORATE_CURRENT
            or state["title"] != entry["title"]
            or str(state["updated"])[:10] != entry["updated"]
            or state["slug"] != entry["topic"]
            or entry.get("artifact_type") != "collaborate"
        ):
            fail("active.collaborate artifact does not agree with its index entry")


def normalize_workflow_request(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        fail("workflow artifact request must be an object")
    operation = value.get("operation")
    allowed_keys = {
        "schema_version",
        "operation",
        "expected_revision",
        "previous_path",
        "artifact_type",
        "workflow",
        "slug",
        "title",
        "summary",
        "consumer",
        "source_revision",
        "updated",
        "body",
        "linked",
        "evidence_paths",
        "search_keys",
    }
    unknown = set(value) - allowed_keys
    if unknown:
        fail(f"workflow artifact request has unsupported keys: {', '.join(sorted(unknown))}")
    if value.get("schema_version") != 1 or operation not in {"create", "update", "supersede"}:
        fail("workflow artifact request has an unsupported schema or operation")
    if value.get("artifact_type") != WORKFLOW_ARTIFACT_KIND:
        fail("artifact_type must be workflow-artifact")
    expected = value.get("expected_revision")
    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
        fail("workflow artifact expected_revision must come from artifact-inspect")
    workflow = value.get("workflow")
    if workflow in {"discussion", "design", "goal"}:
        fail("Discussion, Design, and Goal artifacts are managed by their specialized commands")
    if workflow not in WORKFLOW_CONFIG:
        fail("workflow must be one of: " + ", ".join(sorted(WORKFLOW_CONFIG)))
    assert isinstance(workflow, str)
    state: dict[str, object] = {
        "schema_version": 1,
        "operation": str(operation),
        "expected_revision": expected,
        "previous_path": None,
        "artifact_type": WORKFLOW_ARTIFACT_KIND,
        "workflow": workflow,
        "slug": require_slug(value.get("slug")),
        "title": require_text(value.get("title"), "workflow artifact title", maximum=200),
        "summary": require_text(value.get("summary"), "workflow artifact summary", maximum=2000),
        "consumer": require_text(value.get("consumer"), "workflow artifact consumer", maximum=200),
        "source_revision": require_text(value.get("source_revision"), "workflow artifact source_revision", maximum=200),
        "updated": require_date(value.get("updated"), "workflow artifact updated"),
        "body": require_markdown_body(value.get("body"), "workflow artifact body"),
        "linked": require_path_list(value.get("linked", []), "workflow artifact linked"),
        "evidence_paths": require_path_list(value.get("evidence_paths", []), "workflow artifact evidence_paths"),
        "search_keys": require_text_list(value.get("search_keys", []), "workflow artifact search_keys"),
    }
    if workflow == "execution":
        if operation == "update":
            fail("execution artifacts are one terminal handoff; use supersede for a later run")
        if str(state["consumer"]).casefold() in {"writer", "none", "unknown"}:
            fail("execution artifact consumer must name the real downstream consumer")
    previous = value.get("previous_path")
    if operation == "create":
        if previous is not None:
            fail("create does not accept previous_path")
    else:
        state["previous_path"] = checked_relative(previous, "workflow artifact previous_path")
        if not WORKFLOW_ARTIFACT_PATH_RE.fullmatch(str(state["previous_path"])):
            fail("previous_path must come from artifact-inspect")
    return state


def render_workflow_artifact(value: dict[str, object]) -> str:
    workflow = str(value["workflow"])
    return "\n".join(
        (
            f"Artifact Kind: {_workflow_artifact_kind(workflow)}",
            f"Artifact Type: {WORKFLOW_ARTIFACT_KIND}",
            f"Workflow: {workflow}",
            f"Last Updated: {value['updated']}",
            f"Consumer: {value['consumer']}",
            f"Source Revision: {value['source_revision']}",
            "",
            f"# {value['title']}",
            "",
            str(value["body"]).rstrip(),
            "",
        )
    )


def _workflow_index_entry(state: dict[str, object], path: str, *, active: bool, supersedes: list[str] | None = None) -> dict[str, object]:
    workflow = str(state["workflow"])
    evidence = list(state["evidence_paths"])
    assert isinstance(evidence, list)
    if path not in evidence:
        evidence = [path, *[str(item) for item in evidence]]
    return {
        "topic": str(state["slug"]),
        "kind": _workflow_artifact_kind(workflow),
        "title": str(state["title"]),
        "status": "active" if active else "superseded",
        "currentness": "current" if active else "historical",
        "authority": "canonical" if active else "superseded",
        "path": path,
        "artifact_type": WORKFLOW_ARTIFACT_KIND,
        "workflow": workflow,
        "consumer": str(state["consumer"]),
        "applies_to": [str(state["consumer"])],
        "source_revision": str(state["source_revision"]),
        "linked": list(state["linked"]),
        "evidence_paths": evidence,
        "supersedes": list(supersedes or []),
        "search_keys": list(state["search_keys"]),
        "updated": str(state["updated"]),
        "summary": str(state["summary"]),
    }


def _workflow_active_entry_map(index: dict[str, object]) -> dict[str, dict[str, object]]:
    entries = index["entries"]
    assert isinstance(entries, list)
    active = index["active"]
    assert isinstance(active, dict)
    active_paths: set[str] = set()
    for pointer in ("plan", "report"):
        value = active.get(pointer)
        if isinstance(value, str):
            active_paths.add(value)
    active_paths.update(str(item) for item in active["results"])
    result: dict[str, dict[str, object]] = {}
    for entry in entries:
        if (
            isinstance(entry, dict)
            and entry.get("path") in active_paths
            and _is_workflow_entry(entry)
            and _eligible(entry)
        ):
            result[str(entry["path"])] = entry
    return result


def workflow_revision(root: Path, index_text: str, index: dict[str, object]) -> str:
    parts = [b"workflow-artifact-v1", index_text.encode("utf-8")]
    active_workflow_entries = _workflow_active_entry_map(index)
    for path in sorted(active_workflow_entries):
        data = safe_read_bytes(root, path)
        assert data is not None
        parts.append(path.encode("utf-8"))
        parts.append(data)
    active = index["active"]
    assert isinstance(active, dict)
    legacy_plan = active.get("plan")
    if isinstance(legacy_plan, str) and legacy_plan not in active_workflow_entries:
        data = safe_read_bytes(root, legacy_plan)
        assert data is not None
        parts.append(b"legacy-plan")
        parts.append(legacy_plan.encode("utf-8"))
        parts.append(data)
    return _hash(*parts)


def workflow_schema(operation: str) -> dict[str, object]:
    if operation not in {"create", "update", "supersede"}:
        fail("workflow artifact schema operation must be create, update, or supersede")
    request: dict[str, object] = {
        "schema_version": 1,
        "operation": operation,
        "expected_revision": "<revision from artifact-inspect>",
        "artifact_type": WORKFLOW_ARTIFACT_KIND,
        "workflow": "research",
        "slug": "workflow-slug",
        "title": "Workflow artifact title",
        "summary": "One-sentence registration summary.",
        "consumer": "Writer",
        "source_revision": "<source revision or inspected artifact revision>",
        "updated": "YYYY-MM-DD",
        "body": "Writer-owned Markdown body.",
        "linked": [],
        "evidence_paths": [],
        "search_keys": ["workflow-slug"],
    }
    if operation != "create":
        request["previous_path"] = "<path from artifact-inspect>"
    return request


def inspect_workflow_artifacts(root: Path) -> dict[str, object]:
    with locked_memory(root):
        recovered = recover_transaction(root, WORKFLOW_ARTIFACT_MARKER, WORKFLOW_ARTIFACT_PREFIXES, WORKFLOW_ARTIFACT_KIND)
        require_initialized_memory(root)
        index_text, index = _read_index(root)
        validate_currentness(root, index)
        registrations = []
        for path, entry in sorted(_workflow_active_entry_map(index).items()):
            registrations.append(
                {
                    "path": path,
                    "workflow": entry["workflow"],
                    "kind": entry["kind"],
                    "title": entry["title"],
                    "slug": entry["topic"],
                    "updated": entry["updated"],
                    "active": _workflow_artifact_slot(str(entry["workflow"])),
                    "consumer": entry.get("consumer"),
                    "source_revision": entry.get("source_revision"),
                    "summary": entry["summary"],
                }
            )
        return {
            "initialized": True,
            "recovered": recovered,
            "revision": workflow_revision(root, index_text, index),
            "active": {
                "plan": index["active"].get("plan"),
                "report": index["active"].get("report"),
                "results": list(index["active"]["results"]),
                "registrations": registrations,
            },
        }


def _find_workflow_entry(index: dict[str, object], path: str) -> tuple[int, dict[str, object]]:
    position, entry = _find_entry(index, path)
    if not _is_workflow_entry(entry) or not _eligible(entry):
        fail("previous_path is not a current generic workflow artifact from artifact-inspect")
    return position, entry


def _find_supersedable_workflow_entry(
    index: dict[str, object],
    path: str,
    workflow: str,
) -> tuple[int, dict[str, object], bool]:
    position, entry = _find_entry(index, path)
    if _is_workflow_entry(entry) and _eligible(entry):
        return position, entry, False
    active = index["active"]
    assert isinstance(active, dict)
    if (
        workflow == "plan"
        and active.get("plan") == path
        and entry.get("kind") == "plan"
        and _eligible(entry)
        and _pointer_shape("plan", path, entry)
    ):
        return position, entry, True
    fail("previous_path is not a current generic workflow artifact or migratable active Plan from artifact-inspect")


def _conflicting_workflow_slug(index: dict[str, object], workflow: str, slug: str, *, except_path: str | None = None) -> bool:
    for entry in index["entries"]:
        if not isinstance(entry, dict) or not _is_workflow_entry(entry) or not _eligible(entry):
            continue
        if entry["path"] == except_path:
            continue
        if entry.get("workflow") == workflow and entry.get("topic") == slug:
            return True
    return False


def _set_workflow_active(active: dict[str, object], slot: str, old_path: str | None, new_path: str) -> None:
    if slot == "results":
        results = list(active["results"])
        if old_path is None:
            if new_path not in results:
                results.append(new_path)
        else:
            if old_path not in results:
                fail("previous workflow artifact is not registered in active.results")
            results = [new_path if item == old_path else item for item in results if item != new_path]
        active["results"] = results
    else:
        if old_path is not None and active.get(slot) != old_path:
            fail(f"previous workflow artifact is not registered in active.{slot}")
        active[slot] = new_path


def apply_workflow_artifact(root: Path, request: dict[str, object]) -> dict[str, object]:
    state = normalize_workflow_request(request)
    operation = str(state["operation"])
    workflow = str(state["workflow"])
    slot = _workflow_artifact_slot(workflow)
    target = _workflow_artifact_path(workflow, str(state["updated"]), str(state["slug"]))
    with locked_memory(root):
        ensure_no_migration_intermediate(root)
        recover_transaction(root, WORKFLOW_ARTIFACT_MARKER, WORKFLOW_ARTIFACT_PREFIXES, WORKFLOW_ARTIFACT_KIND)
        require_initialized_memory(root)
        index_text, index = _read_index(root)
        validate_currentness(root, index)
        if state["expected_revision"] != workflow_revision(root, index_text, index):
            fail("stale workflow artifact expected_revision; run artifact-inspect again")
        if workflow == "execution" and index["active"].get("progress") is not None:
            fail("active Goal owns execution progress and suppresses a separate execution artifact")
        if _conflicting_workflow_slug(index, workflow, str(state["slug"]), except_path=str(state["previous_path"])):
            fail("a current workflow artifact already owns this workflow and slug")
        active = index["active"]
        assert isinstance(active, dict)
        old_path: str | None = None
        supersedes: list[str] = []
        outputs: dict[str, Output]
        if operation == "create":
            if slot != "results" and active.get(slot) is not None:
                fail(f"cannot create while active.{slot} already exists")
            if safe_read_bytes(root, target, optional=True) is not None:
                fail("derived workflow artifact destination already exists")
            index["entries"].append(_workflow_index_entry(state, target, active=True))
            _set_workflow_active(active, slot, None, target)
            outputs = {target: Output(render_workflow_artifact(state).encode("utf-8"))}
        else:
            old_path = str(state["previous_path"])
            if operation == "update":
                _, old_entry = _find_workflow_entry(index, old_path)
                if old_entry.get("workflow") != workflow:
                    fail("update cannot change workflow; use supersede")
                if target != old_path:
                    fail("update cannot change the derived workflow artifact destination; use supersede")
                _replace_index_entry(index, old_path, _workflow_index_entry(state, target, active=True, supersedes=list(old_entry.get("supersedes", []))))
                outputs = {target: Output(render_workflow_artifact(state).encode("utf-8"))}
            else:
                _, old_entry, legacy_plan = _find_supersedable_workflow_entry(index, old_path, workflow)
                old_slot = slot if legacy_plan else _workflow_artifact_slot(str(old_entry["workflow"]))
                if old_slot != slot:
                    fail("supersede cannot move a workflow artifact between active registration classes")
                if target == old_path or safe_read_bytes(root, target, optional=True) is not None:
                    fail("supersede must derive an unused workflow artifact destination")
                old_historical = dict(old_entry)
                old_historical["status"] = "superseded"
                old_historical["currentness"] = "historical"
                old_historical["authority"] = "superseded"
                old_historical["superseded_by"] = target
                _replace_index_entry(index, old_path, old_historical)
                supersedes = [old_path]
                index["entries"].append(_workflow_index_entry(state, target, active=True, supersedes=supersedes))
                _set_workflow_active(active, slot, old_path, target)
                old_bytes = safe_read_bytes(root, old_path)
                assert old_bytes is not None
                outputs = {
                    old_path: Output(old_bytes, _mode_of(root, old_path) or 0o600),
                    target: Output(render_workflow_artifact(state).encode("utf-8")),
                }
        index["last_updated"] = str(state["updated"])
        _validate_pointer_metadata(index)
        outputs[INDEX_PATH] = Output(_serialize_index(index).encode("utf-8"))
        created_directories: list[str] = []
        ensure_directory(root, PurePosixPath(target).parent.as_posix(), created=created_directories)
        apply_transaction(
            root,
            kind=WORKFLOW_ARTIFACT_KIND,
            marker=WORKFLOW_ARTIFACT_MARKER,
            prefixes=WORKFLOW_ARTIFACT_PREFIXES,
            outputs=outputs,
            created_directories=created_directories,
        )
        final_text, final_index = _read_index(root)
        validate_currentness(root, final_index)
        return {
            "path": target,
            "revision": workflow_revision(root, final_text, final_index),
            "changed_paths": list(outputs),
            "active": final_index["active"].get(slot) if slot != "results" else list(final_index["active"]["results"]),
        }


def design_revision(root: Path, index_text: str, index: dict[str, object]) -> str:
    path = index["active"].get("design")
    artifact = b"" if path is None else (safe_read_bytes(root, str(path)) or b"")
    return _hash(b"design-v4", index_text.encode("utf-8"), artifact)


def design_schema(operation: str) -> dict[str, object]:
    if operation not in {"create", "update", "supersede"}:
        fail("Design schema operation must be create, update, or supersede")
    state = {
        "schema_version": 3,
        "artifact_type": "design",
        "slug": "decision-slug",
        "title": "Design title",
        "updated": "YYYY-MM-DD",
        "status": "current",
        "superseded_by": None,
        "acceptance": "pending",
        "blockers": [],
        "evidence_waves": ["Local evidence", "External evidence or bounded none"],
        "alternatives": ["Recommended route", "Material alternative"],
        "exclusions": ["Out-of-scope route"],
        "challenge_result": "survives after one bounded challenge",
        "decision_frontier": [],
        "settled": ["Selected direction"],
        "open_items": [],
        "plan_handoff": "Planner receives the selected direction and acceptance signal.",
        "review_handoff": "Reviewer checks the changed boundary and direct evidence.",
        "decision_rule": "Choose the least complex route preserving the accepted boundary.",
        "recommendation": "Use the selected route.",
        "largest_downside": "It retains a bounded migration cost.",
        "rejected_alternatives": [{"option": "Material alternative", "reason": "It violates a named constraint."}],
        "residual_uncertainty": "No material dissent remains.",
    }
    return {"schema_version": 1, "operation": operation, "expected_revision": "<revision from design-inspect>", "state": state}


def inspect_design(root: Path) -> dict[str, object]:
    with locked_memory(root):
        recovered = recover_transaction(root, DESIGN_MARKER, ("docs/teamwork/design/", INDEX_PATH), "design")
        require_initialized_memory(root)
        index_text, index = _read_index(root)
        validate_currentness(root, index)
        path = index["active"].get("design")
        active = None
        if isinstance(path, str):
            text = safe_read_text(root, path)
            assert text is not None
            state = validate_design_artifact(text)
            active = {"path": path, "acceptance": design_acceptance(state), "state": state}
        return {"initialized": True, "recovered": recovered, "revision": design_revision(root, index_text, index), "active": active}


def _replace_index_entry(index: dict[str, object], path: str, replacement: dict[str, object]) -> None:
    position, _ = _find_entry(index, path)
    entries = index["entries"]
    assert isinstance(entries, list)
    entries[position] = replacement


def apply_design(root: Path, request: dict[str, object]) -> dict[str, object]:
    if request.get("schema_version") != 1 or request.get("operation") not in {"create", "update", "supersede"}:
        fail("Design request has an unsupported schema or operation")
    operation = str(request["operation"])
    expected = request.get("expected_revision")
    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
        fail("Design expected_revision must come from design-inspect")
    state = normalize_design_state(request.get("state"))
    if state["status"] != "current":
        fail("Design apply accepts a current successor state; supersession is derived atomically")
    target = design_path(state)
    with locked_memory(root):
        ensure_no_migration_intermediate(root)
        recover_transaction(root, DESIGN_MARKER, ("docs/teamwork/design/", INDEX_PATH), "design")
        require_initialized_memory(root)
        index_text, index = _read_index(root)
        validate_currentness(root, index)
        current_path = index["active"].get("design")
        if expected != design_revision(root, index_text, index):
            fail("stale Design expected_revision; run design-inspect again")
        if operation == "create":
            if current_path is not None:
                fail("cannot create Design while active.design already exists")
            if safe_read_bytes(root, target, optional=True) is not None:
                fail("controlled Design destination already exists")
            index["entries"].append(_index_entry("design", target, state, active=True))
        elif operation == "update":
            if not isinstance(current_path, str):
                fail("cannot update without active.design")
            if target != current_path:
                fail("update cannot change the controlled Design destination; use supersede")
            old_text = safe_read_text(root, current_path)
            assert old_text is not None
            old = validate_design_artifact(old_text)
            if design_acceptance(old) == "accepted" and design_acceptance(state) != "accepted":
                fail("update cannot downgrade an accepted Design; use supersede")
            _replace_index_entry(index, current_path, _index_entry("design", target, state, active=True))
        else:
            if not isinstance(current_path, str):
                fail("cannot supersede without active.design")
            if target == current_path or safe_read_bytes(root, target, optional=True) is not None:
                fail("supersede must derive an unused successor Design destination")
            old_text = safe_read_text(root, current_path)
            assert old_text is not None
            old = validate_design_artifact(old_text)
            old["status"] = "superseded"
            old["superseded_by"] = target
            old = normalize_design_state(old)
            _replace_index_entry(index, current_path, _index_entry("design", current_path, old, active=False))
            index["entries"].append(_index_entry("design", target, state, active=True))
        index["active"]["design"] = target
        index["last_updated"] = state["updated"]
        _validate_pointer_metadata(index)
        outputs: dict[str, Output] = {
            target: Output(render_design_artifact(state).encode("utf-8")),
            INDEX_PATH: Output(_serialize_index(index).encode("utf-8")),
        }
        if operation == "supersede":
            assert isinstance(current_path, str)
            old_text = safe_read_text(root, current_path)
            assert old_text is not None
            old = validate_design_artifact(old_text)
            old["status"] = "superseded"
            old["superseded_by"] = target
            outputs[current_path] = Output(render_design_artifact(old).encode("utf-8"))
        created_directories: list[str] = []
        ensure_directory(root, "docs/teamwork/design", created=created_directories)
        apply_transaction(
            root,
            kind="design",
            marker=DESIGN_MARKER,
            prefixes=("docs/teamwork/design/", INDEX_PATH),
            outputs=outputs,
            created_directories=created_directories,
        )
        final_text, final_index = _read_index(root)
        validate_currentness(root, final_index)
        return {"path": target, "revision": design_revision(root, final_text, final_index), "changed_paths": list(outputs)}


# ---------------------------------------------------------------------------
# Goal: reports/YYYY-MM-DD-slug-goal.md plus active.progress only.


def _require_json_value(value: object, label: str) -> object:
    # JSON data may carry a structured budget; it cannot be omitted.
    if value is None:
        fail(f"{label} must be explicitly recorded (use an empty object or list when applicable)")
    return value


def _normalize_attempt(value: object, number: int, updated: str) -> dict[str, object]:
    if not isinstance(value, dict):
        fail("Goal attempt must be an object")
    evidence = require_text_list(value.get("evidence"), "Goal attempt evidence", minimum=1)
    return {
        "number": number,
        "strategy": require_text(value.get("strategy"), "Goal attempt strategy"),
        "current_unmet_claim": require_text(value.get("current_unmet_claim"), "Goal attempt current_unmet_claim"),
        "evidence": evidence,
        "blocker": require_text(value.get("blocker"), "Goal attempt blocker"),
        "strategy_delta": require_text(value.get("strategy_delta"), "Goal attempt strategy_delta"),
        "next_strategy": require_text(value.get("next_strategy"), "Goal attempt next_strategy"),
        "recorded_at": require_date(value.get("recorded_at", updated), "Goal attempt recorded_at"),
    }


def normalize_goal_state(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        fail("Goal state must be an object")
    status = value.get("status")
    if status not in {"active", "completed", "hard_stopped"}:
        fail("Goal status must be active, completed, or hard_stopped")
    attempts_raw = value.get("attempts")
    if not isinstance(attempts_raw, list):
        fail("Goal attempts must be an array")
    updated = require_date(value.get("updated"), "Goal updated")
    attempts: list[dict[str, object]] = []
    for number, item in enumerate(attempts_raw, start=1):
        attempt = _normalize_attempt(item, number, updated)
        if attempt.get("number") != number:
            # _normalize_attempt controls number, so supplied stale numbering is
            # rejected explicitly rather than silently corrected.
            if isinstance(item, dict) and "number" in item and item["number"] != number:
                fail("Goal attempts must have consecutive numbers")
        attempts.append(attempt)
    state: dict[str, object] = {
        "schema_version": 1,
        "artifact_type": "goal",
        "slug": require_slug(value.get("slug"), "Goal slug"),
        "title": require_text(value.get("title"), "Goal title"),
        "objective": require_text(value.get("objective"), "Goal objective"),
        "scope": _require_json_value(value.get("scope"), "Goal scope"),
        "protected_boundaries": require_text_list(value.get("protected_boundaries"), "Goal protected_boundaries"),
        "invariants": require_text_list(value.get("invariants"), "Goal invariants"),
        "success_signal": require_text(value.get("success_signal"), "Goal success_signal"),
        "budget": _require_json_value(value.get("budget"), "Goal budget"),
        "hard_stops": require_text_list(value.get("hard_stops"), "Goal hard_stops"),
        "status": status,
        "current_unmet_claim": require_text(value.get("current_unmet_claim"), "Goal current_unmet_claim"),
        "started_at": require_date(value.get("started_at"), "Goal started_at"),
        "updated": updated,
        "next_strategy": require_text(value.get("next_strategy"), "Goal next_strategy"),
        "attempts": attempts,
        "state_revision": value.get("state_revision", len(attempts) + 1),
        "closure": value.get("closure"),
    }
    if not isinstance(state["state_revision"], int) or state["state_revision"] != len(attempts) + 1:
        fail("Goal state_revision must be one plus the number of attempts")
    if status == "active" and state["closure"] is not None:
        fail("active Goal cannot have closure evidence")
    if status == "completed":
        if not isinstance(state["closure"], dict) or not require_text_list(state["closure"].get("success_evidence"), "Goal success_evidence", minimum=1):
            fail("completed Goal needs direct success_evidence")
    if status == "hard_stopped":
        if not isinstance(state["closure"], dict) or not require_text(state["closure"].get("accepted_hard_stop"), "Goal accepted_hard_stop"):
            fail("hard_stopped Goal needs an accepted_hard_stop")
    return state


def goal_path(state: dict[str, object]) -> str:
    return f"docs/teamwork/reports/{state['started_at']}-{state['slug']}-goal.md"


def render_goal_artifact(value: object) -> str:
    state = normalize_goal_state(value)
    return "\n".join(
        (
            "Artifact Type: goal",
            f"Status: {state['status']}",
            "Authority: canonical",
            f"Last Updated: {state['updated']}",
            f"Goal Slug: {state['slug']}",
            "",
            f"# {state['title']}",
            "",
            "## Goal state",
            "",
            "```json",
            json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True),
            "```",
        )
    ) + "\n"


def validate_goal_artifact(text: str) -> dict[str, object]:
    block = _section(text, "Goal state")
    match = re.fullmatch(r"```json\n(.*)\n```", block, flags=re.DOTALL)
    if match is None:
        fail("Goal state must be one JSON fenced block")
    state = normalize_goal_state(_decode_json(match.group(1), "Goal state"))
    if text != render_goal_artifact(state):
        fail("Goal artifact headers or durable state drifted from the canonical renderer")
    return state


def goal_revision(root: Path, index_text: str, index: dict[str, object]) -> str:
    path = index["active"].get("progress")
    artifact = b"" if path is None else (safe_read_bytes(root, str(path)) or b"")
    return _hash(b"goal-v4", index_text.encode("utf-8"), artifact)


def goal_schema(operation: str) -> dict[str, object]:
    if operation not in {"start", "attempt", "close"}:
        fail("Goal schema operation must be start, attempt, or close")
    if operation == "start":
        state = {
            "schema_version": 1,
            "artifact_type": "goal",
            "slug": "goal-slug",
            "title": "Goal title",
            "objective": "The user-authorized outcome.",
            "scope": {"included": ["Named authorized work"]},
            "protected_boundaries": ["No release without authority."],
            "invariants": ["Preserve named compatibility."],
            "success_signal": "A direct real result proves completion.",
            "budget": {"user_supplied": "record exact value or empty object"},
            "hard_stops": ["Missing user authority."],
            "status": "active",
            "current_unmet_claim": "The success signal has not passed.",
            "started_at": "YYYY-MM-DD",
            "updated": "YYYY-MM-DD",
            "next_strategy": "Run the smallest evidence-backed next action.",
            "attempts": [],
            "state_revision": 1,
            "closure": None,
        }
        return {"schema_version": 1, "operation": operation, "expected_revision": "<revision from goal-inspect>", "state": state}
    if operation == "attempt":
        return {
            "schema_version": 1,
            "operation": "attempt",
            "expected_revision": "<revision from goal-inspect>",
            "updated": "YYYY-MM-DD",
            "attempt": {
                "strategy": "<exact next_strategy from goal-inspect>",
                "current_unmet_claim": "The still-unmet direct claim.",
                "evidence": ["Direct observation from this attempt."],
                "blocker": "What blocked the prior strategy.",
                "strategy_delta": "Why the next action differs.",
                "next_strategy": "A materially different next action.",
            },
        }
    return {
        "schema_version": 1,
        "operation": "close",
        "expected_revision": "<revision from goal-inspect>",
        "updated": "YYYY-MM-DD",
        "closure": {"mode": "success", "success_evidence": ["Direct success signal output."]},
    }


def inspect_goal(root: Path) -> dict[str, object]:
    with locked_memory(root):
        recovered = recover_transaction(root, GOAL_MARKER, ("docs/teamwork/reports/", INDEX_PATH), "goal")
        require_initialized_memory(root)
        index_text, index = _read_index(root)
        validate_currentness(root, index)
        path = index["active"].get("progress")
        active = None
        if isinstance(path, str):
            text = safe_read_text(root, path)
            assert text is not None
            state = validate_goal_artifact(text)
            active = {
                "path": path,
                "state": state,
                "resume": {
                    "attempt_count": len(state["attempts"]),
                    "current_unmet_claim": state["current_unmet_claim"],
                    "next_strategy": state["next_strategy"],
                },
            }
        return {"initialized": True, "recovered": recovered, "revision": goal_revision(root, index_text, index), "active": active}


def _goal_active_state(root: Path, index: dict[str, object]) -> tuple[str, dict[str, object]]:
    path = index["active"].get("progress")
    if not isinstance(path, str):
        fail("Goal has no active progress state")
    text = safe_read_text(root, path)
    assert text is not None
    return path, validate_goal_artifact(text)


def apply_goal(root: Path, request: dict[str, object]) -> dict[str, object]:
    if request.get("schema_version") != 1 or request.get("operation") not in {"start", "attempt", "close"}:
        fail("Goal request has an unsupported schema or operation")
    operation = str(request["operation"])
    expected = request.get("expected_revision")
    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
        fail("Goal expected_revision must come from goal-inspect")
    with locked_memory(root):
        ensure_no_migration_intermediate(root)
        recover_transaction(root, GOAL_MARKER, ("docs/teamwork/reports/", INDEX_PATH), "goal")
        require_initialized_memory(root)
        index_text, index = _read_index(root)
        validate_currentness(root, index)
        if expected != goal_revision(root, index_text, index):
            fail("stale Goal expected_revision; run goal-inspect again")
        outputs: dict[str, Output]
        if operation == "start":
            if index["active"].get("progress") is not None:
                fail("cannot start a Goal while active.progress exists")
            state = normalize_goal_state(request.get("state"))
            if state["status"] != "active" or state["attempts"]:
                fail("Goal start state must be active with no attempts")
            path = goal_path(state)
            if safe_read_bytes(root, path, optional=True) is not None:
                fail("controlled Goal report destination already exists")
            index["entries"].append(_index_entry("progress", path, state, active=True))
            index["active"]["progress"] = path
            index["last_updated"] = state["updated"]
            _validate_pointer_metadata(index)
            outputs = {path: Output(render_goal_artifact(state).encode("utf-8")), INDEX_PATH: Output(_serialize_index(index).encode("utf-8"))}
            result_path: str | None = path
        else:
            path, state = _goal_active_state(root, index)
            updated = require_date(request.get("updated"), "Goal request updated")
            state = dict(state)
            if operation == "attempt":
                attempt = _normalize_attempt(request.get("attempt"), len(state["attempts"]) + 1, updated)
                if attempt["strategy"] != state["next_strategy"]:
                    fail("Goal attempt strategy must exactly match the inspected next_strategy")
                if attempt["next_strategy"] == attempt["strategy"]:
                    fail("Goal attempt next_strategy must differ from strategy")
                if state["attempts"] and attempt["strategy"] == state["attempts"][-1]["strategy"]:
                    fail("Goal cannot replay an unchanged attempt strategy")
                state["attempts"] = [*state["attempts"], attempt]
                state["current_unmet_claim"] = attempt["current_unmet_claim"]
                state["next_strategy"] = attempt["next_strategy"]
                state["updated"] = updated
                state["state_revision"] = len(state["attempts"]) + 1
                state["closure"] = None
                state = normalize_goal_state(state)
                _replace_index_entry(index, path, _index_entry("progress", path, state, active=True))
                index["last_updated"] = updated
                _validate_pointer_metadata(index)
                outputs = {path: Output(render_goal_artifact(state).encode("utf-8")), INDEX_PATH: Output(_serialize_index(index).encode("utf-8"))}
                result_path = path
            else:
                closure = request.get("closure")
                if not isinstance(closure, dict) or closure.get("mode") not in {"success", "hard_stop"}:
                    fail("Goal close requires closure mode success or hard_stop")
                if closure["mode"] == "success":
                    evidence = require_text_list(closure.get("success_evidence"), "Goal success_evidence", minimum=1)
                    state["status"] = "completed"
                    state["closure"] = {"success_evidence": evidence}
                    state["current_unmet_claim"] = "The direct success signal passed."
                else:
                    hard_stop = require_text(closure.get("accepted_hard_stop"), "Goal accepted_hard_stop")
                    state["status"] = "hard_stopped"
                    state["closure"] = {"accepted_hard_stop": hard_stop}
                    state["current_unmet_claim"] = hard_stop
                state["updated"] = updated
                state = normalize_goal_state(state)
                _replace_index_entry(index, path, _index_entry("progress", path, state, active=False))
                index["active"]["progress"] = None
                index["last_updated"] = updated
                _validate_pointer_metadata(index)
                outputs = {path: Output(render_goal_artifact(state).encode("utf-8")), INDEX_PATH: Output(_serialize_index(index).encode("utf-8"))}
                result_path = path
        created_directories: list[str] = []
        ensure_directory(root, "docs/teamwork/reports", created=created_directories)
        apply_transaction(
            root,
            kind="goal",
            marker=GOAL_MARKER,
            prefixes=("docs/teamwork/reports/", INDEX_PATH),
            outputs=outputs,
            created_directories=created_directories,
        )
        final_text, final_index = _read_index(root)
        validate_currentness(root, final_index)
        return {
            "path": result_path,
            "revision": goal_revision(root, final_text, final_index),
            "changed_paths": list(outputs),
            "active": final_index["active"].get("progress"),
        }


# ---------------------------------------------------------------------------
# Pure v3.4.2 discussion migration planning. W5 owns its outer transaction.


def _legacy_label_pattern(name: str) -> str:
    """Match the historical label words with Markdown horizontal whitespace."""

    return r"[ \t]+".join(re.escape(part) for part in name.split(" "))


def _legacy_header(text: str, name: str) -> str | None:
    label = _legacy_label_pattern(name)
    match = re.search(rf"(?m)^{label}[ \t]*:[ \t]*(.*?)[ \t]*\r?$", text)
    return None if match is None else match.group(1).strip(" \t")


def _validate_legacy_document_controls(text: str) -> None:
    """Reject unsafe bytes before legacy heading/section matching can miss them."""

    if LEGACY_UNSAFE_CONTROL_RE.search(text):
        fail("v3 Discussion document contains unsafe control characters")


def _legacy_section_match(text: str, name: str) -> re.Match[str] | None:
    """Find a v3 Markdown section without requiring a blank separator line.

    v3 accepted a section body immediately after the heading as well as the
    common blank-line form.  The whole-document control preflight has already
    limited whitespace controls to CR/LF/TAB, so this keeps the grammar
    explicit rather than widening it with an unsafe generic ``\\s`` match.
    """

    label = _legacy_label_pattern(name)
    return re.search(
        rf"(?ms)^##[ \t]+{label}[ \t]*\r?\n(.*?)(?=^##[ \t]+|\Z)",
        text,
    )


def _legacy_section(text: str, name: str) -> list[str] | str:
    match = _legacy_section_match(text, name)
    list_field = name.casefold().replace(" ", "_")
    if match is None:
        return [] if list_field in DISCUSSION_LIST_FIELDS else "none recorded"
    raw_body = match.group(1)
    if LEGACY_UNSAFE_CONTROL_RE.search(raw_body):
        fail(f"v3 Discussion {name} contains unsafe control characters")
    # Only historical line formatting is discarded here. Do not use str.strip:
    # it silently removes VT/FF/FS and could hide an unsafe legacy payload.
    body = raw_body.strip(" \t\r\n")
    values = [line[2:].strip() for line in body.splitlines() if line.startswith("- ") and line[2:].strip() and line[2:].strip().lower() != "none"]
    if list_field in DISCUSSION_LIST_FIELDS:
        return values
    return body or "none recorded"


def _decode_legacy_scalar(value: str) -> list[str]:
    """Decode the injective one-line representation used only by v3 migration."""

    lines = [""]
    cursor = 0
    while cursor < len(value):
        character = value[cursor]
        if character != "\\":
            lines[-1] += character
            cursor += 1
            continue
        if cursor + 1 >= len(value):
            fail("legacy scalar encoding ends with an incomplete escape")
        escaped = value[cursor + 1]
        if escaped == "\\":
            lines[-1] += "\\"
        elif escaped == "n":
            lines.append("")
        else:
            fail("legacy scalar encoding has an unknown escape")
        cursor += 2
    return lines


def _normalize_legacy_scalar(value: object, label: str) -> str:
    """Preserve v3 multiline scalar meaning in v4's one-line renderer field.

    v3 Discussion sections were free-form Markdown, while v4 scalar fields are
    deliberately one line so their Mermaid labels and fallback remain exact.
    Migration accepts only line-break and horizontal-whitespace normalization.
    Every source line remains in order; physical line boundaries become the
    reversible two-character ``\\n`` escape, while literal backslashes become
    ``\\\\``. The full original is also retained verbatim in
    ``migration_source``. Other control bytes remain unsafe and fail closed.
    """

    if not isinstance(value, str):
        fail(f"{label} must be text")
    if LEGACY_UNSAFE_CONTROL_RE.search(value):
        fail(f"{label} contains unsafe control characters")
    lines = [re.sub(r"[ \t]+", " ", line).strip(" ") for line in value.splitlines()]
    encoded = r"\n".join(line.replace("\\", r"\\") for line in lines)
    normalized = require_text(encoded, label)
    # Keep the representation's injectivity executable rather than implicit.
    if _decode_legacy_scalar(normalized) != lines:
        fail("legacy scalar encoding did not round-trip")
    return normalized


def _legacy_discussion_state(path: str, text: str, entry: dict[str, object], *, active: bool) -> dict[str, object]:
    _validate_legacy_document_controls(text)
    match = DISCUSSION_ARCHIVE_RE.fullmatch(path)
    if match is None:
        fail("v3 Discussion path must be a dated archive path")
    updated, slug, _ = match.groups()
    header_updated = _legacy_header(text, "Last Updated")
    if header_updated is not None and valid_date(header_updated):
        updated = header_updated
    title_match = re.search(r"(?m)^#[ \t]+(.+?)[ \t]*\r?$", text)
    title = title_match.group(1).strip(" \t") if title_match else require_text(entry.get("title"), "v3 Discussion title")
    status = "active" if active else "accepted"
    source_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return normalize_discussion_state(
        {
            "slug": slug,
            "title": title,
            "updated": updated,
            "status": status,
            "superseded_by": None,
            "goal": _normalize_legacy_scalar(_legacy_section(text, "Goal"), "v3 Discussion goal"),
            "current_branch": _normalize_legacy_scalar(_legacy_section(text, "Current branch"), "v3 Discussion current branch"),
            "settled": _legacy_section(text, "Settled"),
            "still_open": _legacy_section(text, "Still open") if active else [],
            "return_path": _normalize_legacy_scalar(
                _legacy_section(text, "Return path")
                if _legacy_section_match(text, "Return path") is not None
                else _legacy_section(text, "Continue here"),
                "v3 Discussion return path",
            ),
            "blockers": _legacy_section(text, "Blockers"),
            "convergence": _normalize_legacy_scalar(_legacy_section(text, "Convergence"), "v3 Discussion convergence"),
            "key_evidence": _legacy_section(text, "Key evidence"),
            "migration_source": {"path": path, "sha256": source_hash, "source_text": text},
        }
    )


def _legacy_discussion_state_v2(
    path: str,
    text: str,
    entry: dict[str, object],
    enrichments: object,
) -> dict[str, object]:
    legacy = _legacy_discussion_state(path, text, entry, active=True)
    if not isinstance(enrichments, list):
        fail("v3 active Discussion migration requires legacy_enrichment")
    still_open = legacy["still_open"]
    assert isinstance(still_open, list)
    seen_indexes: set[int] = set()
    frontier: list[dict[str, object]] = []
    frontier_ids: set[str] = set()
    for item in enrichments:
        if not isinstance(item, dict) or not isinstance(item.get("still_open_index"), int):
            fail("legacy_enrichment items must name still_open_index")
        index = int(item["still_open_index"])
        if not 0 <= index < len(still_open) or index in seen_indexes:
            fail("legacy_enrichment must cover v1 still_open indexes injectively")
        frontier_item = _normalize_frontier_item(item.get("frontier_item"), "legacy_enrichment.frontier_item")
        if frontier_item["id"] in frontier_ids:
            fail("legacy_enrichment frontier ids must be unique")
        seen_indexes.add(index)
        frontier_ids.add(str(frontier_item["id"]))
        frontier.append(frontier_item)
    if seen_indexes != set(range(len(still_open))):
        fail("legacy_enrichment must cover every v1 still_open item")
    current_batch = [str(item["id"]) for item in frontier if item["status"] == "current"]
    return normalize_discussion_state_v2(
        {
            "schema_version": 2,
            "artifact_type": "discussion",
            "slug": legacy["slug"],
            "title": legacy["title"],
            "updated": legacy["updated"],
            "status": "active",
            "superseded_by": None,
            "goal": legacy["goal"],
            "current_branch": legacy["current_branch"],
            "return_path": legacy["return_path"],
            "blockers": legacy["blockers"],
            "convergence": legacy["convergence"],
            "key_evidence": legacy["key_evidence"],
            "frontier": frontier,
            "current_batch": current_batch,
            "migration_source": legacy["migration_source"],
        }
    )


def _init_raw_discussion_relocation_requested() -> bool:
    return any(
        key.startswith("TEAMWORK_TEST_HARD_EXIT_INIT_")
        for key in os.environ
    )


def plan_v342_discussion_migration(
    index_text: str,
    artifact_texts: dict[str, str],
    legacy_enrichment: object = None,
    *,
    raw_legacy_relocation: bool | None = None,
) -> dict[str, object]:
    """Return a pure, typed W5 migration plan; never touch the filesystem.

    With explicit ``legacy_enrichment``, the active dated record becomes a
    schema-v2 Discussion with source provenance. Without enrichment, ordinary
    Init receives a legacy-normalized provenance artifact without a guessed v2
    frontier. Raw byte relocation is reserved for the Init hard-interruption
    recovery fixture, where the transaction must prove exact delete recovery or
    committed replay rather than perform semantic migration.
    """

    raw = _decode_json(index_text, "v3 Teamwork index")
    if not isinstance(raw, dict) or not isinstance(raw.get("entries"), list) or not isinstance(raw.get("active"), dict):
        fail("v3 Discussion migration index is malformed")
    discussions: dict[str, dict[str, object]] = {}
    for entry in raw["entries"]:
        if not isinstance(entry, dict) or entry.get("kind") != "discussion":
            continue
        path = checked_relative(entry.get("path"), "v3 Discussion migration path")
        if DISCUSSION_ARCHIVE_RE.fullmatch(path) is None or path in discussions:
            fail("v3 Discussion migration has duplicate or malformed discussion paths")
        discussions[path] = entry
    if set(artifact_texts) != set(discussions):
        fail("v3 Discussion migration artifact inputs must exactly cover indexed discussions")
    for path, text in artifact_texts.items():
        checked_relative(path, "v3 Discussion artifact path")
        if path not in discussions or not isinstance(text, str):
            fail("v3 Discussion migration received an unknown or non-text artifact")
    active_path = raw["active"].get("discussion")
    if active_path is not None:
        active_path = checked_relative(active_path, "v3 active.discussion")
        if active_path not in discussions:
            fail("v3 active.discussion does not identify one indexed discussion")
        active_entry = discussions[active_path]
        if active_entry.get("status") not in {"active", "accepted"} or active_entry.get("currentness") not in {"current", None}:
            fail("v3 active.discussion is not a current active record")
    else:
        active_rows = [path for path, entry in discussions.items() if entry.get("status") == "active" and entry.get("currentness") == "current"]
        if active_rows:
            fail("v3 indexed active Discussion is missing active.discussion")
    writes: dict[str, str] = {}
    deletes: list[str] = []
    raw_relocation = _init_raw_discussion_relocation_requested() if raw_legacy_relocation is None else raw_legacy_relocation
    for path, entry in discussions.items():
        active = path == active_path
        destination = DISCUSSION_CURRENT if active else path
        if destination in writes:
            fail("v3 Discussion migration derives conflicting destination paths")
        if raw_relocation:
            # Recovery and committed-replay callers need an exact byte plan, not
            # a guessed question frontier. Closed archives also remain unchanged.
            writes[destination] = artifact_texts[path]
        elif active and legacy_enrichment is not None:
            state = _legacy_discussion_state_v2(path, artifact_texts[path], entry, legacy_enrichment)
            writes[destination] = render_discussion_artifact(state)
        else:
            state = _legacy_discussion_state(path, artifact_texts[path], entry, active=active)
            writes[destination] = render_discussion_artifact(state)
        if active and path != destination:
            deletes.append(path)
    return {
        "schema_version": 2,
        "writes": writes,
        "deletes": deletes,
        "active_path": DISCUSSION_CURRENT if active_path is not None else None,
    }


# ---------------------------------------------------------------------------
# Collaborate: unified public discussion/design decision transaction.


COLLABORATE_ARCHIVE_RE = re.compile(
    r"^docs/teamwork/collaborate/(\d{4}-\d{2}-\d{2})-([a-z0-9]+(?:-[a-z0-9]+)*)(?:-(\d+))?\.md$"
)
COLLABORATE_DECISION_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
COLLABORATE_FIELDS = (
    "schema_version", "artifact_type", "decision_id", "slug", "title", "updated",
    "status", "acceptance", "mode", "lineage", "migration_sources", "goal",
    "synthesis", "tensions", "candidate_space", "questions", "frontier",
    "current_batch", "settled", "key_evidence", "open_items", "blockers",
    "recommendation", "largest_downside", "decision_rule", "adversarial",
    "plan_handoff", "review_handoff", "rejected_alternatives",
    "acceptance_evidence", "return_path", "exclusions", "superseded_by",
)
COLLABORATE_SET_FIELDS = {
    "settled", "key_evidence", "open_items", "blockers", "rejected_alternatives",
    "acceptance_evidence", "exclusions",
}
COLLABORATE_UPDATE_FIELDS = {
    "title", "mode", "goal", "synthesis", "tensions", "candidate_space",
    "questions", "frontier", "current_batch", "settled", "key_evidence",
    "open_items", "recommendation", "largest_downside", "decision_rule",
    "adversarial", "plan_handoff", "review_handoff", "rejected_alternatives",
    "acceptance_evidence", "return_path", "exclusions",
}


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def _norm_text(value: object, label: str, *, allow_empty: bool = True) -> str:
    if not isinstance(value, str):
        fail(f"{label} must be text")
    text = unicodedata.normalize("NFC", value.replace("\r\n", "\n").replace("\r", "\n")).strip()
    if not allow_empty and not text:
        fail(f"{label} must be non-empty text")
    if CONTROL_RE.search(text) is not None:
        fail(f"{label} contains unsafe control characters")
    return text


def _norm_slug(value: object, fallback: str = "collaborate") -> str:
    raw = value if isinstance(value, str) and value.strip() else fallback
    slug = re.sub(r"[^a-z0-9]+", "-", _norm_text(raw, "slug source").casefold()).strip("-")
    slug = re.sub(r"-+", "-", slug) or "collaborate"
    if SLUG_RE.fullmatch(slug) is None:
        fail("slug must be lowercase kebab-case")
    return slug[:80].strip("-") or "collaborate"


def _new_decision_id() -> str:
    return "c-" + secrets.token_hex(12)


def _require_utc(value: object, label: str) -> str:
    text = _norm_text(value, label, allow_empty=False)
    if UTC_RE.fullmatch(text) is None:
        fail(f"{label} must be UTC timestamp YYYY-MM-DDTHH:MM:SSZ")
    try:
        datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        fail(f"{label} must be UTC timestamp YYYY-MM-DDTHH:MM:SSZ")
    return text


def _norm_str_list(value: object, label: str, *, ordered: bool = True, maximum: int = 200) -> list[str]:
    if value is None:
        value = []
    if not isinstance(value, list) or len(value) > maximum:
        fail(f"{label} must be an array")
    items = [_norm_text(item, f"{label} item") for item in value]
    if ordered:
        return items
    return sorted(set(items), key=lambda item: item.encode("utf-8"))


def _norm_collab_path(value: object, label: str) -> str:
    path = _norm_text(value, label, allow_empty=False)
    pure = PurePosixPath(path)
    if (
        pure.is_absolute()
        or pure.as_posix() != path
        or "\\" in path
        or any(part in {"", ".", ".."} for part in pure.parts)
        or pure.parts[:2] != ("docs", "teamwork")
    ):
        fail(f"{label} must be a normalized path under docs/teamwork/")
    return path


def _normalize_source_row(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != {"path", "schema_version", "scope_key", "sha256", "type"}:
        fail(f"{label} must match the Collaborate source schema")
    source_type = value.get("type")
    if source_type not in {"design", "discussion"}:
        fail(f"{label}.type must be design or discussion")
    schema_version = value.get("schema_version")
    if not isinstance(schema_version, int) or isinstance(schema_version, bool) or schema_version <= 0:
        fail(f"{label}.schema_version must be a positive integer")
    digest = value.get("sha256")
    if not isinstance(digest, str) or HEX64_RE.fullmatch(digest) is None:
        fail(f"{label}.sha256 must be lowercase sha256 hex")
    return {
        "path": _norm_collab_path(value.get("path"), f"{label}.path"),
        "schema_version": schema_version,
        "scope_key": _norm_text(value.get("scope_key"), f"{label}.scope_key", allow_empty=False),
        "sha256": digest,
        "type": source_type,
    }


def _normalize_ledger_row(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != {"consumed_at", "consumed_by_decision_id", "kind", "path", "sha256"}:
        fail(f"{label} must match the Collaborate consumed source ledger schema")
    kind = value.get("kind")
    if kind not in {"design", "discussion"}:
        fail(f"{label}.kind must be design or discussion")
    decision_id = _norm_text(value.get("consumed_by_decision_id"), f"{label}.consumed_by_decision_id", allow_empty=False).lower()
    digest = value.get("sha256")
    if COLLABORATE_DECISION_ID_RE.fullmatch(decision_id) is None:
        fail(f"{label}.consumed_by_decision_id is invalid")
    if not isinstance(digest, str) or HEX64_RE.fullmatch(digest) is None:
        fail(f"{label}.sha256 must be lowercase sha256 hex")
    return {
        "consumed_at": _require_utc(value.get("consumed_at"), f"{label}.consumed_at"),
        "consumed_by_decision_id": decision_id,
        "kind": kind,
        "path": _norm_collab_path(value.get("path"), f"{label}.path"),
        "sha256": digest,
    }


def _sort_collaborate_ledger(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    order = {"design": 0, "discussion": 1}
    return sorted(rows, key=lambda row: (order[str(row["kind"])], str(row["path"]).encode("utf-8"), str(row["sha256"]), str(row["consumed_by_decision_id"])))


def normalize_collaborate_ledger(value: object | None) -> list[dict[str, object]]:
    if value is None:
        value = []
    if not isinstance(value, list):
        fail("collaborate_consumed_sources must be an array")
    rows = [_normalize_ledger_row(item, f"collaborate_consumed_sources[{position}]") for position, item in enumerate(value)]
    seen_full: set[tuple[str, str, str, str]] = set()
    seen_digest: set[tuple[str, str, str]] = set()
    by_path: dict[tuple[str, str], str] = {}
    for row in rows:
        full = (str(row["kind"]), str(row["path"]), str(row["sha256"]), str(row["consumed_by_decision_id"]))
        if full in seen_full:
            fail("collaborate_consumed_sources contains duplicate rows")
        seen_full.add(full)
        digest_key = (str(row["kind"]), str(row["path"]), str(row["sha256"]))
        if digest_key in seen_digest:
            fail("collaborate_consumed_sources duplicates a consumed source")
        seen_digest.add(digest_key)
        key = (str(row["kind"]), str(row["path"]))
        if key in by_path and by_path[key] != row["sha256"]:
            fail("collaborate_consumed_sources records source drift")
        by_path[key] = str(row["sha256"])
    sorted_rows = _sort_collaborate_ledger(rows)
    if sorted_rows != rows:
        fail("collaborate_consumed_sources must be canonically sorted")
    return sorted_rows


def _norm_candidate(value: object, label: str) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != {"id", "status", "summary", "title"}:
        fail(f"{label} must match the Collaborate candidate schema")
    if value.get("status") not in {"open", "recommended", "rejected", "settled"}:
        fail(f"{label}.status is invalid")
    return {
        "id": _norm_text(value.get("id"), f"{label}.id", allow_empty=False),
        "status": str(value["status"]),
        "summary": _norm_text(value.get("summary"), f"{label}.summary"),
        "title": _norm_text(value.get("title"), f"{label}.title"),
    }


def _norm_question(value: object, label: str) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != {"answer", "id", "prompt", "status"}:
        fail(f"{label} must match the Collaborate question schema")
    if value.get("status") not in {"open", "answered", "skipped"}:
        fail(f"{label}.status is invalid")
    return {
        "answer": _norm_text(value.get("answer"), f"{label}.answer"),
        "id": _norm_text(value.get("id"), f"{label}.id", allow_empty=False),
        "prompt": _norm_text(value.get("prompt"), f"{label}.prompt"),
        "status": str(value["status"]),
    }


def _norm_frontier(value: object, label: str) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != {"id", "rationale", "status", "title"}:
        fail(f"{label} must match the Collaborate frontier schema")
    if value.get("status") not in {"open", "settled", "rejected"}:
        fail(f"{label}.status is invalid")
    return {
        "id": _norm_text(value.get("id"), f"{label}.id", allow_empty=False),
        "rationale": _norm_text(value.get("rationale"), f"{label}.rationale"),
        "status": str(value["status"]),
        "title": _norm_text(value.get("title"), f"{label}.title"),
    }


def _norm_handoff(value: object, label: str) -> dict[str, object]:
    if value is None:
        value = {"notes": [], "ready": False}
    if not isinstance(value, dict) or set(value) != {"notes", "ready"} or not isinstance(value.get("ready"), bool):
        fail(f"{label} must match the Collaborate handoff schema")
    return {"notes": _norm_str_list(value.get("notes"), f"{label}.notes"), "ready": bool(value["ready"])}


def _norm_adversarial(value: object) -> dict[str, object]:
    if value is None:
        value = {"evidence": [], "status": "not_run", "summary": ""}
    if not isinstance(value, dict) or set(value) != {"evidence", "status", "summary"}:
        fail("adversarial must match the Collaborate schema")
    if value.get("status") not in {"not_run", "pass", "fail"}:
        fail("adversarial.status is invalid")
    return {
        "evidence": _norm_str_list(value.get("evidence"), "adversarial.evidence"),
        "status": str(value["status"]),
        "summary": _norm_text(value.get("summary"), "adversarial.summary"),
    }


def _norm_lineage(value: object, label: str) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != {"decision_id", "operation", "previous_lineage_digest"}:
        fail(f"{label} must match the Collaborate lineage schema")
    if value.get("operation") not in {"create", "update", "accept", "block", "close", "supersede"}:
        fail(f"{label}.operation is invalid")
    decision_id = _norm_text(value.get("decision_id"), f"{label}.decision_id", allow_empty=False).lower()
    previous = _norm_text(value.get("previous_lineage_digest"), f"{label}.previous_lineage_digest")
    if COLLABORATE_DECISION_ID_RE.fullmatch(decision_id) is None or (previous and HEX64_RE.fullmatch(previous) is None):
        fail(f"{label} has invalid digest or decision_id")
    return {"decision_id": decision_id, "operation": str(value["operation"]), "previous_lineage_digest": previous}


def normalize_collaborate_state(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        fail("Collaborate state must be an object")
    unknown = set(value) - set(COLLABORATE_FIELDS)
    if unknown:
        fail(f"Collaborate state has unknown fields: {', '.join(sorted(unknown))}")
    decision_id = _norm_text(value.get("decision_id", _new_decision_id()), "decision_id", allow_empty=False).lower()
    if COLLABORATE_DECISION_ID_RE.fullmatch(decision_id) is None:
        fail("decision_id is invalid")
    status = value.get("status", "active")
    acceptance = value.get("acceptance", "pending")
    if status not in {"active", "accepted", "blocked", "closed", "superseded"}:
        fail("Collaborate status is invalid")
    if acceptance not in {"pending", "accepted", "blocked"}:
        fail("Collaborate acceptance is invalid")
    if (status, acceptance) not in {
        ("active", "pending"), ("accepted", "accepted"), ("blocked", "blocked"),
        ("closed", "pending"), ("superseded", "pending"), ("superseded", "accepted"), ("superseded", "blocked"),
    }:
        fail("Collaborate status and acceptance are inconsistent")
    mode = value.get("mode", "dialogue")
    if mode not in {"dialogue", "brainstorm"}:
        fail("Collaborate mode is invalid")
    superseded_by = value.get("superseded_by")
    if superseded_by is not None:
        superseded_by = _norm_text(superseded_by, "superseded_by", allow_empty=False).lower()
        if COLLABORATE_DECISION_ID_RE.fullmatch(superseded_by) is None:
            fail("superseded_by is invalid")
    state: dict[str, object] = {
        "schema_version": 1,
        "artifact_type": "collaborate",
        "decision_id": decision_id,
        "slug": _norm_slug(value.get("slug"), str(value.get("title") or value.get("goal") or "collaborate")),
        "title": _norm_text(value.get("title", ""), "title"),
        "updated": _require_utc(value.get("updated", _utc_now()), "updated"),
        "status": str(status),
        "acceptance": str(acceptance),
        "mode": str(mode),
        "lineage": [_norm_lineage(item, f"lineage[{position}]") for position, item in enumerate(value.get("lineage", []))],
        "migration_sources": [_normalize_source_row(item, f"migration_sources[{position}]") for position, item in enumerate(value.get("migration_sources", []))],
        "goal": _norm_text(value.get("goal", ""), "goal"),
        "synthesis": _norm_str_list(value.get("synthesis"), "synthesis"),
        "tensions": _norm_str_list(value.get("tensions"), "tensions"),
        "candidate_space": [_norm_candidate(item, f"candidate_space[{position}]") for position, item in enumerate(value.get("candidate_space", []))],
        "questions": [_norm_question(item, f"questions[{position}]") for position, item in enumerate(value.get("questions", []))],
        "frontier": [_norm_frontier(item, f"frontier[{position}]") for position, item in enumerate(value.get("frontier", []))],
        "current_batch": _norm_str_list(value.get("current_batch"), "current_batch", maximum=3),
        "settled": _norm_str_list(value.get("settled"), "settled", ordered=False),
        "key_evidence": _norm_str_list(value.get("key_evidence"), "key_evidence", ordered=False),
        "open_items": _norm_str_list(value.get("open_items"), "open_items", ordered=False),
        "blockers": _norm_str_list(value.get("blockers"), "blockers", ordered=False),
        "recommendation": _norm_text(value.get("recommendation", ""), "recommendation"),
        "largest_downside": _norm_text(value.get("largest_downside", ""), "largest_downside"),
        "decision_rule": _norm_text(value.get("decision_rule", ""), "decision_rule"),
        "adversarial": _norm_adversarial(value.get("adversarial")),
        "plan_handoff": _norm_handoff(value.get("plan_handoff"), "plan_handoff"),
        "review_handoff": _norm_handoff(value.get("review_handoff"), "review_handoff"),
        "rejected_alternatives": _norm_str_list(value.get("rejected_alternatives"), "rejected_alternatives", ordered=False),
        "acceptance_evidence": _norm_str_list(value.get("acceptance_evidence"), "acceptance_evidence", ordered=False),
        "return_path": _norm_text(value.get("return_path", ""), "return_path"),
        "exclusions": _norm_str_list(value.get("exclusions"), "exclusions", ordered=False),
        "superseded_by": superseded_by,
    }
    if not state["lineage"]:
        state["lineage"] = [{"decision_id": decision_id, "operation": "create", "previous_lineage_digest": ""}]
    _validate_collaborate_relations(state)
    return state


def _validate_collaborate_relations(state: dict[str, object]) -> None:
    questions = {str(item["id"]): item for item in state["questions"]}
    frontier = {str(item["id"]): item for item in state["frontier"]}
    if len(questions) != len(state["questions"]) or len(frontier) != len(state["frontier"]):
        fail("Collaborate question and frontier ids must be unique")
    batch = [str(item) for item in state["current_batch"]]
    if len(batch) != len(set(batch)) or len(batch) > 3:
        fail("current_batch must contain at most three unique ids")
    if state["mode"] == "dialogue" and len(batch) > 1:
        fail("dialogue current_batch may contain at most one id")
    for item_id in batch:
        if item_id in frontier:
            fail("current_batch references the retired Collaborate frontier collection")
        if item_id not in questions:
            fail("current_batch references an unknown id")
        if questions[item_id]["status"] != "open":
            fail("current_batch references a non-open record")
    if state["status"] in {"accepted", "blocked", "closed", "superseded"} and batch:
        fail("terminal Collaborate states cannot retain current_batch")
    if state["status"] == "accepted" and (
        any(item["status"] == "open" for item in state["questions"])
        or any(item["status"] == "open" for item in state["frontier"])
    ):
        fail("accepted Collaborate cannot retain open records")


def collaborate_semantic_digest(state: dict[str, object]) -> str:
    normalized = normalize_collaborate_state(state)
    return _sha256_text(_canonical_json({key: normalized[key] for key in COLLABORATE_FIELDS}))


def collaborate_lineage_digest(state: dict[str, object]) -> str:
    normalized = normalize_collaborate_state(state)
    lineage = normalized["lineage"]
    assert isinstance(lineage, list) and lineage
    last = lineage[-1]
    assert isinstance(last, dict)
    return _sha256_text(_canonical_json({
        "decision_id": last["decision_id"],
        "operation": last["operation"],
        "previous_lineage_digest": last["previous_lineage_digest"],
        "semantic_digest": collaborate_semantic_digest(normalized),
    }))


def render_collaborate_artifact(value: object) -> str:
    state = normalize_collaborate_state(value)
    return "\n".join((
        "Artifact Kind: collaborate",
        "Artifact Type: collaborate",
        "Schema Version: 1",
        f"Status: {state['status']}",
        f"Acceptance: {state['acceptance']}",
        f"Mode: {state['mode']}",
        f"Last Updated: {state['updated']}",
        f"Decision ID: {state['decision_id']}",
        f"Collaborate Slug: {state['slug']}",
        f"Semantic Digest: {collaborate_semantic_digest(state)}",
        f"Lineage Digest: {collaborate_lineage_digest(state)}",
        f"Superseded By: {state['superseded_by'] or 'none'}",
        "",
        f"# {state['title'] or state['slug']}",
        "",
        "## Decision Map",
        "",
        "```mermaid",
        "flowchart TD",
        f'    mode["Mode: {_mermaid_label(str(state["mode"]))}"] --> status["Status: {_mermaid_label(str(state["status"]))}"]',
        f'    status --> batch["Current batch: {_mermaid_label(", ".join(state["current_batch"]) or "none")}"]',
        "```",
        "",
        "Plain-text fallback:",
        "",
        f"Goal: {state['goal'] or 'none'}",
        f"Current batch: {', '.join(state['current_batch']) or 'none'}",
        f"Recommendation: {state['recommendation'] or 'none'}",
        "",
        "## Collaborate State",
        "",
        "```json",
        json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
    ))


def validate_collaborate_artifact(text: str) -> dict[str, object]:
    block = _section(text, "Collaborate State")
    match = re.fullmatch(r"```json\n(.*)\n```", block, flags=re.DOTALL)
    if match is None:
        fail("Collaborate state must be one JSON fenced block")
    state = normalize_collaborate_state(_decode_json(match.group(1), "Collaborate state"))
    if text != render_collaborate_artifact(state):
        fail("Collaborate artifact graph, fallback, headers, or state drifted from canonical renderer")
    return state


def _materialize_collaborate_index(index: dict[str, object]) -> dict[str, object]:
    index = dict(index)
    active = dict(index.get("active") or {})
    active.setdefault("collaborate", None)
    index["active"] = active
    index["collaborate_consumed_sources"] = normalize_collaborate_ledger(index.get("collaborate_consumed_sources"))
    return index


def _collaborate_revision(
    index: dict[str, object],
    current_bytes: bytes | None,
    *,
    index_text: str,
    full_sources: list[dict[str, object]],
) -> str:
    active = index.get("active")
    pointer = active.get("collaborate") if isinstance(active, dict) else None
    if pointer is not None:
        pointer = checked_relative(pointer, "active.collaborate")
    if pointer not in {None, COLLABORATE_CURRENT}:
        fail("active.collaborate must be null or docs/teamwork/collaborate/current.md")
    if pointer is None and current_bytes is not None:
        fail("Collaborate current exists without active.collaborate")
    if pointer == COLLABORATE_CURRENT and current_bytes is None:
        fail("active.collaborate points at missing current")
    current_sha = None if pointer is None else hashlib.sha256(current_bytes or b"").hexdigest()
    payload = {
        "active_pointer": pointer,
        "current_path": COLLABORATE_CURRENT,
        "current_sha256": current_sha,
        "index_sha256": _sha256_text(index_text),
        "schema_version": 1,
        "sources": full_sources,
    }
    return hashlib.sha256(b"collaborate-cas-v1\0" + _canonical_json(payload).encode("utf-8")).hexdigest()


def collaborate_revision(root: Path, index: dict[str, object] | None = None) -> str:
    if index is None:
        index_text, index = _read_index(root)
    else:
        index_text = _serialize_index(index)
    index = _materialize_collaborate_index(index)
    return _collaborate_revision(
        index,
        safe_read_bytes(root, COLLABORATE_CURRENT, optional=True),
        index_text=index_text,
        full_sources=enumerate_collaborate_sources(root, index),
    )


def _source_row(kind: str, path: str, schema_version: int, scope_key: str, raw: bytes) -> dict[str, object]:
    return _normalize_source_row(
        {
            "path": path,
            "schema_version": schema_version,
            "scope_key": scope_key,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "type": kind,
        },
        "legacy source",
    )


def enumerate_collaborate_sources(root: Path, index: dict[str, object]) -> list[dict[str, object]]:
    sources: list[dict[str, object]] = []
    active = index.get("active")
    design_path_value = active.get("design") if isinstance(active, dict) else None
    if isinstance(design_path_value, str):
        design_path_value = checked_relative(design_path_value, "active.design")
        raw = safe_read_bytes(root, design_path_value)
        assert raw is not None
        text = raw.decode("utf-8")
        state = validate_design_artifact(text)
        if state.get("status") == "current":
            sources.append(_source_row("design", design_path_value, int(state["schema_version"]), str(state["slug"]), raw))
    discussion_raw = safe_read_bytes(root, DISCUSSION_CURRENT, optional=True)
    if discussion_raw is not None:
        state = validate_discussion_artifact(discussion_raw.decode("utf-8"))
        if state.get("status") == "active":
            sources.append(_source_row("discussion", DISCUSSION_CURRENT, int(state["schema_version"]), str(state["slug"]), discussion_raw))
    return sources


def classify_collaborate_sources(full_sources: list[dict[str, object]], ledger: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    ledger_by_path = {(str(row["kind"]), str(row["path"])): row for row in ledger}
    sources: list[dict[str, object]] = []
    consumed: list[dict[str, object]] = []
    for source in full_sources:
        row = ledger_by_path.get((str(source["type"]), str(source["path"])))
        if row is None:
            sources.append(source)
        elif row["sha256"] == source["sha256"]:
            consumed.append(row)
        else:
            fail("consumed legacy source drift detected")
    return {"full_sources": full_sources, "sources": sources, "consumed_sources": consumed}


def _current_collaborate(root: Path) -> tuple[bytes | None, dict[str, object] | None]:
    current = safe_read_bytes(root, COLLABORATE_CURRENT, optional=True)
    if current is None:
        return None, None
    return current, validate_collaborate_artifact(current.decode("utf-8"))


def _require_collaborate_closure(state: dict[str, object]) -> None:
    state = normalize_collaborate_state(state)
    if state["current_batch"]:
        fail("accepted Collaborate requires empty current_batch")
    if any(item["status"] == "open" for item in state["questions"]):
        fail("accepted Collaborate requires no open questions")
    if any(item["status"] == "open" for item in state["frontier"]):
        fail("accepted Collaborate requires no open frontier")
    if state["open_items"] or state["blockers"]:
        fail("accepted Collaborate requires no open_items or blockers")
    adversarial = state["adversarial"]
    assert isinstance(adversarial, dict)
    if adversarial["status"] not in {"not_run", "pass"}:
        fail("accepted Collaborate requires adversarial status not_run or pass")
    if not state["recommendation"] or not state["acceptance_evidence"]:
        fail("accepted Collaborate requires recommendation and acceptance_evidence")


def _append_collab_lineage(state: dict[str, object], operation: str, previous_digest: str) -> dict[str, object]:
    state = dict(state)
    lineage = list(state["lineage"])
    lineage.append({"decision_id": state["decision_id"], "operation": operation, "previous_lineage_digest": previous_digest})
    state["lineage"] = lineage
    return normalize_collaborate_state(state)


def _merge_unique(*groups: object) -> list[str]:
    values: list[str] = []
    for group in groups:
        if isinstance(group, list):
            values.extend(str(item) for item in group)
    return sorted(set(_norm_text(item, "set item") for item in values), key=lambda item: item.encode("utf-8"))


def _map_design_to_collaborate(state: dict[str, object]) -> dict[str, object]:
    acceptance = design_acceptance(state)
    blockers = list(state.get("blockers", [])) if state.get("schema_version") == 3 else []
    return {
        "title": state["title"],
        "slug": state["slug"],
        "goal": state["decision_rule"],
        "key_evidence": state["evidence_waves"],
        "exclusions": state["exclusions"],
        "settled": state["settled"],
        "open_items": state["open_items"],
        "blockers": blockers,
        "recommendation": state["recommendation"],
        "largest_downside": state["largest_downside"],
        "decision_rule": state["decision_rule"],
        "rejected_alternatives": [f"{row['option']}: {row['reason']}" for row in state["rejected_alternatives"]],
        "acceptance_evidence": _merge_unique(state["evidence_waves"], [state["challenge_result"]]),
        "plan_handoff": {"notes": [str(state["plan_handoff"])], "ready": acceptance == "accepted"},
        "review_handoff": {"notes": [str(state["review_handoff"])], "ready": acceptance == "accepted"},
        "adversarial": {"evidence": state["evidence_waves"], "status": "pass" if acceptance == "accepted" else "fail" if acceptance == "blocked" else "not_run", "summary": state["challenge_result"]},
        "candidate_space": [
            {"id": f"design-alternative-{position:03d}", "status": "settled" if acceptance == "accepted" else "open", "summary": str(item), "title": str(item)}
            for position, item in enumerate(state["alternatives"], start=1)
        ],
        "frontier": [
            {"id": f"design-frontier-{position:03d}", "rationale": f"Design decision frontier: {item}", "status": "open", "title": str(item)}
            for position, item in enumerate(state["decision_frontier"], start=1)
        ],
        "synthesis": [str(state["recommendation"])] if str(state["recommendation"]).strip() else [],
        "tensions": [str(item) for item in (state["largest_downside"], state["residual_uncertainty"]) if str(item).strip()],
        "return_path": state["plan_handoff"],
        "_acceptance": acceptance,
        "_material": acceptance == "pending" or bool(state["decision_frontier"]) or bool(state["open_items"]) or bool(blockers),
    }


def _map_discussion_to_collaborate(state: dict[str, object]) -> dict[str, object]:
    if state["schema_version"] == 1:
        still_open = list(state["still_open"])
        return {
            "title": state["title"], "slug": state["slug"], "goal": state["goal"], "mode": "dialogue",
            "synthesis": [item for item in (state["current_branch"], state["convergence"]) if str(item).strip()],
            "tensions": still_open, "settled": state["settled"], "open_items": still_open,
            "blockers": state["blockers"], "key_evidence": state["key_evidence"], "return_path": state["return_path"],
            "questions": [{"id": f"discussion-question-{i:03d}", "answer": "", "prompt": str(item), "status": "open"} for i, item in enumerate(still_open, start=1)],
            "frontier": [{"id": f"discussion-frontier-{i:03d}", "rationale": f"Discussion still_open: {item}", "status": "open", "title": str(item)} for i, item in enumerate(still_open, start=1)],
            "current_batch": ["discussion-question-001"] if still_open else [],
            "_material": bool(still_open),
        }
    if state["schema_version"] == 2 or state.get("mode") == "grill":
        questions: list[dict[str, str]] = []
        open_items: list[str] = []
        tensions: list[str] = []
        settled: list[str] = []
        for item in state["frontier"]:
            status = str(item["status"])
            if status in {"open", "current"}:
                open_items.append(f"{item['id']}: {item['prompt']}")
                tensions.append(f"{item['id']}: {item['largest_downside']}")
            elif status == "closed":
                settled.append(f"{item['id']}: {item['title']}")
            answer = ""
            resolution = item.get("resolution")
            if status == "closed" and isinstance(resolution, dict):
                answer = f"Selected: {resolution.get('option_id')}"
            elif status == "rejected" and isinstance(resolution, dict):
                answer = f"Rejected: {resolution.get('reason')}"
            questions.append({
                "id": f"discussion-question-{item['id']}",
                "prompt": f"{item['prompt']} Why critical: {item['why_critical']} Largest downside: {item['largest_downside']} Closure signal: {item['closure_signal']}",
                "answer": answer,
                "status": "open" if status in {"open", "current"} else "answered" if status == "closed" else "skipped",
            })
        synthesis = list(state.get("synthesis", [])) or [item for item in (state["current_branch"], state["convergence"]) if str(item).strip()]
        return {
            "title": state["title"], "slug": state["slug"], "goal": state["goal"], "mode": "brainstorm",
            "synthesis": synthesis, "tensions": tensions, "settled": _merge_unique(settled, state.get("settled", [])),
            "open_items": open_items, "blockers": state["blockers"], "key_evidence": state["key_evidence"],
            "return_path": state["return_path"], "questions": questions, "frontier": [],
            "current_batch": [f"discussion-question-{item}" for item in state["current_batch"]],
            "_material": bool(open_items) or bool(state["current_batch"]),
        }
    questions: list[dict[str, str]] = []
    open_items: list[str] = []
    for item in state["questions"]:
        source_id = str(item["id"])
        if item["status"] in {"open", "current"}:
            open_items.append(f"{source_id}: {item['prompt']}")
        questions.append({"id": f"discussion-question-{source_id}", "answer": "", "prompt": str(item["prompt"]), "status": "open" if item["status"] in {"open", "current"} else "answered" if item["status"] == "answered" else "skipped"})
    return {
        "title": state["title"], "slug": state["slug"], "goal": state["goal"], "mode": state["mode"],
        "synthesis": state["synthesis"], "tensions": state["tensions"], "settled": state["settled"],
        "open_items": open_items, "blockers": state["blockers"], "key_evidence": state["key_evidence"],
        "return_path": state["return_path"], "questions": questions, "frontier": [],
        "candidate_space": [{"id": f"discussion-candidate-{i:03d}", "status": "open", "summary": str(item), "title": str(item)} for i, item in enumerate(state.get("candidate_space", []), start=1)],
        "current_batch": [f"discussion-question-{state['current_question']}"] if state.get("current_question") is not None else [],
        "_material": bool(open_items) or state.get("current_question") is not None,
    }


def _derive_import_collaborate(root: Path, sources: list[dict[str, object]], decision_id: str, updated: str) -> dict[str, object]:
    design_map: dict[str, object] = {}
    discussion_map: dict[str, object] = {}
    for source in sources:
        text = (safe_read_bytes(root, str(source["path"])) or b"").decode("utf-8")
        if source["type"] == "design":
            design_map = _map_design_to_collaborate(validate_design_artifact(text))
        else:
            discussion_map = _map_discussion_to_collaborate(validate_discussion_artifact(text))
    if design_map and discussion_map and design_map.get("slug") != discussion_map.get("slug"):
        fail("Design and Discussion import sources have different scope keys")
    state: dict[str, object] = {
        "decision_id": decision_id, "updated": updated, "lineage": [{"decision_id": decision_id, "operation": "create", "previous_lineage_digest": ""}],
        "migration_sources": sources,
    }
    for mapping in (design_map, discussion_map):
        for key, value in mapping.items():
            if key.startswith("_"):
                continue
            if key in COLLABORATE_SET_FIELDS:
                state[key] = _merge_unique(state.get(key, []), value)
            elif key in {"synthesis", "tensions"} and key in state:
                state[key] = list(state[key]) + list(value)  # preserve ordered contributions
            elif key in {"title", "slug", "goal"} and key in state and design_map:
                continue
            else:
                state[key] = value
    if design_map and discussion_map and discussion_map.get("return_path"):
        state["return_path"] = discussion_map["return_path"]
    if discussion_map and not design_map:
        final = ("blocked", "blocked") if state.get("blockers") else ("active", "pending")
    elif design_map.get("_acceptance") == "blocked" or state.get("blockers"):
        final = ("blocked", "blocked")
    elif design_map.get("_acceptance") == "accepted" and not design_map.get("_material") and not discussion_map.get("_material"):
        final = ("accepted", "accepted")
    else:
        final = ("active", "pending")
    state["status"], state["acceptance"] = final
    if state["status"] in {"accepted", "blocked"}:
        state["current_batch"] = []
    normalized = normalize_collaborate_state(state)
    if normalized["status"] == "accepted":
        _require_collaborate_closure(normalized)
    return normalized


def _collab_archive_path(root: Path, state: dict[str, object]) -> str:
    day = str(state["updated"])[:10]
    number = 1
    while True:
        suffix = "" if number == 1 else f"-{number}"
        candidate = f"docs/teamwork/collaborate/{day}-{state['slug']}{suffix}.md"
        if safe_read_bytes(root, candidate, optional=True) is None:
            return candidate
        number += 1


def _collab_entry(state: dict[str, object], path: str, *, active: bool) -> dict[str, object]:
    return {
        "topic": str(state["slug"]), "kind": "decision", "artifact_type": "collaborate",
        "title": str(state["title"] or state["slug"]),
        "status": str(state["status"]) if active else "superseded",
        "currentness": "current" if active else "historical",
        "authority": "canonical" if active else "superseded",
        "path": path, "linked": [], "evidence_paths": [path], "supersedes": [],
        "search_keys": [str(state["slug"]), "collaborate"], "updated": str(state["updated"])[:10],
        "summary": str(state["recommendation"] or state["goal"] or state["title"] or "Collaborate state."),
    }


def _replace_collaborate_index_entry(index: dict[str, object], path: str, entry: dict[str, object]) -> None:
    entries = index["entries"]
    assert isinstance(entries, list)
    for position, existing in enumerate(entries):
        if isinstance(existing, dict) and existing.get("path") == path:
            entries[position] = entry
            return
    entries.append(entry)


def _collaborate_current_payload(root: Path, index_text: str, index: dict[str, object]) -> dict[str, object]:
    index = _materialize_collaborate_index(index)
    full_sources = enumerate_collaborate_sources(root, index)
    classified = classify_collaborate_sources(full_sources, normalize_collaborate_ledger(index.get("collaborate_consumed_sources")))
    current_bytes, current_state = _current_collaborate(root)
    return {
        "index": index,
        "full_sources": classified["full_sources"],
        "sources": classified["sources"],
        "consumed_sources": classified["consumed_sources"],
        "current_bytes": current_bytes,
        "current_state": current_state,
        "revision": _collaborate_revision(index, current_bytes, index_text=index_text, full_sources=full_sources),
    }


def inspect_collaborate(root: Path) -> dict[str, object]:
    with locked_memory(root):
        recovered = recover_transaction(root, COLLABORATE_MARKER, COLLABORATE_PREFIXES, "collaborate")
        recover_transaction(root, DESIGN_MARKER, ("docs/teamwork/design/", INDEX_PATH), "design")
        recover_transaction(root, DISCUSSION_MARKER, ("docs/teamwork/discussion/",), "discussion")
        require_initialized_memory(root)
        index_text, index = _read_index(root)
        index = _materialize_collaborate_index(index)
        validate_currentness(root, index)
        payload = _collaborate_current_payload(root, index_text, index)
        active = None
        if payload["current_state"] is not None:
            active = {"path": COLLABORATE_CURRENT, "state": payload["current_state"]}
        return {
            "initialized": True,
            "recovered": recovered,
            "revision": payload["revision"],
            "active": active,
            "sources": payload["sources"],
            "consumed_sources": payload["consumed_sources"],
            "ledger": normalize_collaborate_ledger(payload["index"].get("collaborate_consumed_sources")),
            "full_sources": payload["full_sources"],
        }


def collaborate_schema(operation: str) -> dict[str, object]:
    if operation not in {"create", "import", "update", "accept", "block", "close", "supersede"}:
        fail("Collaborate schema operation is invalid")
    state = normalize_collaborate_state(
        {
            "decision_id": "c-example-decision",
            "slug": "decision-slug",
            "title": "Collaborate decision",
            "updated": "2026-07-29T00:00:00Z",
            "status": "active",
            "acceptance": "pending",
            "mode": "dialogue",
            "goal": "Resolve the selected decision boundary.",
            "synthesis": ["Current shared understanding."],
            "questions": [{"id": "Q1", "prompt": "What decision still changes the outcome?", "answer": "", "status": "open"}],
            "current_batch": ["Q1"],
        }
    )
    request: dict[str, object] = {
        "schema_version": 1,
        "operation": operation,
        "expected_revision": "<revision from collaborate-inspect>",
    }
    if operation == "import":
        request.update({"updated": "YYYY-MM-DDTHH:MM:SSZ", "decision_id": "<optional stable decision id>"})
    elif operation == "close":
        request["state"] = {**state, "status": "closed", "acceptance": "pending", "current_batch": []}
    elif operation == "accept":
        request["state"] = {
            **state,
            "status": "accepted",
            "acceptance": "accepted",
            "questions": [{"id": "Q1", "prompt": "What decision still changes the outcome?", "answer": "Use the accepted route.", "status": "answered"}],
            "current_batch": [],
            "open_items": [],
            "blockers": [],
            "recommendation": "Use the accepted route.",
            "acceptance_evidence": ["Direct acceptance evidence."],
        }
    elif operation == "block":
        request["state"] = {**state, "status": "blocked", "acceptance": "blocked", "current_batch": [], "blockers": ["Named blocker."]}
    else:
        request["state"] = state
    return request


def _validate_collaborate_request(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        fail("Collaborate request must be an object")
    operation = value.get("operation")
    if value.get("schema_version") != 1 or operation not in {"create", "import", "update", "accept", "block", "close", "supersede"}:
        fail("Collaborate request has an unsupported schema or operation")
    expected = value.get("expected_revision")
    if not isinstance(expected, str) or re.fullmatch(r"[0-9a-f]{64}", expected) is None:
        fail("Collaborate expected_revision must come from collaborate-inspect")
    request = dict(value)
    request["operation"] = str(operation)
    if operation == "import":
        if "state" in value:
            fail("Collaborate import derives state from inspected legacy sources")
        if "updated" in value:
            request["updated"] = _require_utc(value["updated"], "Collaborate import updated")
        else:
            request["updated"] = _utc_now()
        if value.get("decision_id") is None:
            request["decision_id"] = _new_decision_id()
        else:
            decision_id = _norm_text(value.get("decision_id"), "Collaborate import decision_id", allow_empty=False).lower()
            if COLLABORATE_DECISION_ID_RE.fullmatch(decision_id) is None:
                fail("Collaborate import decision_id is invalid")
            request["decision_id"] = decision_id
        return request
    request["state"] = normalize_collaborate_state(value.get("state"))
    return request


def _archive_current_collaborate(root: Path, state: dict[str, object]) -> str:
    archive = _collab_archive_path(root, state)
    if archive == COLLABORATE_CURRENT:
        fail("Collaborate archive path collided with current")
    return archive


def _mark_legacy_source_index_consumed(
    sources: list[dict[str, object]],
    index: dict[str, object],
    successor: str,
) -> None:
    """Record legacy Design consumption without mutating legacy artifact bytes."""

    active = index["active"]
    assert isinstance(active, dict)
    for source in sources:
        path = str(source["path"])
        if source["type"] == "design":
            for entry in index["entries"]:
                if isinstance(entry, dict) and entry.get("path") == path:
                    entry["status"] = "superseded"
                    entry["currentness"] = "historical"
                    entry["authority"] = "superseded"
                    entry["superseded_by"] = successor
            if active.get("design") == path:
                active["design"] = None


def _append_consumed_sources(
    ledger: list[dict[str, object]],
    sources: list[dict[str, object]],
    *,
    consumed_at: str,
    decision_id: str,
) -> list[dict[str, object]]:
    additions = [
        _normalize_ledger_row(
            {
                "consumed_at": consumed_at,
                "consumed_by_decision_id": decision_id,
                "kind": source["type"],
                "path": source["path"],
                "sha256": source["sha256"],
            },
            "Collaborate consumed source",
        )
        for source in sources
    ]
    return _sort_collaborate_ledger([*ledger, *additions])


def apply_collaborate(root: Path, value: dict[str, object]) -> dict[str, object]:
    request = _validate_collaborate_request(value)
    operation = str(request["operation"])
    expected = str(request["expected_revision"])
    with locked_memory(root):
        ensure_no_migration_intermediate(root)
        recover_transaction(root, COLLABORATE_MARKER, COLLABORATE_PREFIXES, "collaborate")
        recover_transaction(root, DESIGN_MARKER, ("docs/teamwork/design/", INDEX_PATH), "design")
        recover_transaction(root, DISCUSSION_MARKER, ("docs/teamwork/discussion/",), "discussion")
        require_initialized_memory(root)
        index_text, index = _read_index(root)
        index = _materialize_collaborate_index(index)
        validate_currentness(root, index)
        payload = _collaborate_current_payload(root, index_text, index)
        if expected != payload["revision"]:
            fail("stale Collaborate expected_revision; run collaborate-inspect again")
        current = payload["current_state"]
        current_bytes = payload["current_bytes"]
        outputs: dict[str, Output] = {}
        changed: list[str]
        active = index["active"]
        assert isinstance(active, dict)
        ledger = normalize_collaborate_ledger(index.get("collaborate_consumed_sources"))
        if operation == "import":
            sources = list(payload["sources"])
            if current is not None:
                fail("cannot import legacy sources while active.collaborate already exists")
            if not sources:
                fail("Collaborate import has no unconsumed Design or Discussion sources")
            state = _derive_import_collaborate(root, sources, str(request["decision_id"]), str(request["updated"]))
            rendered = render_collaborate_artifact(state).encode("utf-8")
            if safe_read_bytes(root, COLLABORATE_CURRENT, optional=True) is not None:
                fail("controlled Collaborate destination already exists")
            active["collaborate"] = COLLABORATE_CURRENT
            _replace_collaborate_index_entry(index, COLLABORATE_CURRENT, _collab_entry(state, COLLABORATE_CURRENT, active=True))
            index["collaborate_consumed_sources"] = _append_consumed_sources(
                ledger,
                sources,
                consumed_at=str(state["updated"]),
                decision_id=str(state["decision_id"]),
            )
            index["last_updated"] = str(state["updated"])[:10]
            _mark_legacy_source_index_consumed(
                sources,
                index,
                COLLABORATE_CURRENT,
            )
            outputs = {
                COLLABORATE_CURRENT: Output(rendered),
                INDEX_PATH: Output(_serialize_index(index).encode("utf-8")),
            }
            changed = list(outputs)
            result_path: str | None = COLLABORATE_CURRENT
            result_active: dict[str, object] | None = state
        elif operation == "create":
            if current is not None:
                fail("cannot create Collaborate while active.collaborate already exists")
            if payload["sources"]:
                fail("unconsumed legacy sources require Collaborate import")
            state = normalize_collaborate_state(request["state"])
            if state["status"] == "accepted":
                _require_collaborate_closure(state)
            active["collaborate"] = COLLABORATE_CURRENT
            _replace_collaborate_index_entry(index, COLLABORATE_CURRENT, _collab_entry(state, COLLABORATE_CURRENT, active=True))
            index["last_updated"] = str(state["updated"])[:10]
            outputs = {
                COLLABORATE_CURRENT: Output(render_collaborate_artifact(state).encode("utf-8")),
                INDEX_PATH: Output(_serialize_index(index).encode("utf-8")),
            }
            changed = list(outputs)
            result_path = COLLABORATE_CURRENT
            result_active = state
        elif operation in {"update", "accept", "block"}:
            if current is None or current_bytes is None:
                fail(f"cannot {operation} without active.collaborate")
            state = normalize_collaborate_state(request["state"])
            if state["decision_id"] != current["decision_id"]:
                fail("Collaborate update cannot change decision_id; use supersede")
            expected_lifecycle = {"update": ("active", "pending"), "accept": ("accepted", "accepted"), "block": ("blocked", "blocked")}[operation]
            if (state["status"], state["acceptance"]) != expected_lifecycle:
                fail(f"Collaborate {operation} has an invalid lifecycle state")
            if operation == "accept":
                _require_collaborate_closure(state)
            state = _append_collab_lineage(state, operation, collaborate_lineage_digest(current))
            rendered = render_collaborate_artifact(state).encode("utf-8")
            if rendered == current_bytes and operation == "update":
                return {"path": COLLABORATE_CURRENT, "active": current, "revision": payload["revision"], "changed_paths": []}
            active["collaborate"] = COLLABORATE_CURRENT
            _replace_collaborate_index_entry(index, COLLABORATE_CURRENT, _collab_entry(state, COLLABORATE_CURRENT, active=True))
            index["last_updated"] = str(state["updated"])[:10]
            outputs = {
                COLLABORATE_CURRENT: Output(rendered),
                INDEX_PATH: Output(_serialize_index(index).encode("utf-8")),
            }
            changed = list(outputs)
            result_path = COLLABORATE_CURRENT
            result_active = state
        elif operation == "close":
            if current is None or current_bytes is None:
                fail("cannot close without active.collaborate")
            state = normalize_collaborate_state(request["state"])
            if state["decision_id"] != current["decision_id"] or state["status"] != "closed":
                fail("Collaborate close must close the active decision_id")
            state = _append_collab_lineage(state, "close", collaborate_lineage_digest(current))
            archive = _archive_current_collaborate(root, state)
            active["collaborate"] = None
            _replace_collaborate_index_entry(index, COLLABORATE_CURRENT, _collab_entry(state, archive, active=False))
            index["last_updated"] = str(state["updated"])[:10]
            outputs = {
                archive: Output(render_collaborate_artifact(state).encode("utf-8")),
                COLLABORATE_CURRENT: Output(None),
                INDEX_PATH: Output(_serialize_index(index).encode("utf-8")),
            }
            changed = list(outputs)
            result_path = archive
            result_active = None
        else:
            if current is None or current_bytes is None:
                fail("cannot supersede without active.collaborate")
            state = normalize_collaborate_state(request["state"])
            if state["decision_id"] == current["decision_id"]:
                fail("Collaborate supersede requires a new decision_id")
            if state["status"] == "accepted":
                _require_collaborate_closure(state)
            old = dict(current)
            old["status"] = "superseded"
            old["acceptance"] = current["acceptance"]
            old["current_batch"] = []
            old["superseded_by"] = state["decision_id"]
            old = _append_collab_lineage(old, "supersede", collaborate_lineage_digest(current))
            archive = _archive_current_collaborate(root, old)
            state = dict(state)
            state["lineage"] = [{"decision_id": state["decision_id"], "operation": "create", "previous_lineage_digest": collaborate_lineage_digest(old)}]
            state = normalize_collaborate_state(state)
            active["collaborate"] = COLLABORATE_CURRENT
            _replace_collaborate_index_entry(index, COLLABORATE_CURRENT, _collab_entry(old, archive, active=False))
            index["entries"].append(_collab_entry(state, COLLABORATE_CURRENT, active=True))
            index["last_updated"] = str(state["updated"])[:10]
            outputs = {
                archive: Output(render_collaborate_artifact(old).encode("utf-8")),
                COLLABORATE_CURRENT: Output(render_collaborate_artifact(state).encode("utf-8")),
                INDEX_PATH: Output(_serialize_index(index).encode("utf-8")),
            }
            changed = list(outputs)
            result_path = COLLABORATE_CURRENT
            result_active = state
        _validate_pointer_metadata(index)
        created_directories: list[str] = []
        ensure_directory(root, "docs/teamwork/collaborate", created=created_directories)
        apply_transaction(
            root,
            kind="collaborate",
            marker=COLLABORATE_MARKER,
            prefixes=COLLABORATE_PREFIXES,
            outputs=outputs,
            created_directories=created_directories,
        )
        final_text, final_index = _read_index(root)
        final_index = _materialize_collaborate_index(final_index)
        validate_currentness(root, final_index)
        return {
            "path": result_path,
            "active": result_active,
            "revision": collaborate_revision(root, final_index),
            "changed_paths": changed,
        }

def artifact_index_validate(root: Path) -> dict[str, object]:
    with locked_memory(root):
        recover_transaction(root, DESIGN_MARKER, ("docs/teamwork/design/", INDEX_PATH), "design")
        recover_transaction(root, GOAL_MARKER, ("docs/teamwork/reports/", INDEX_PATH), "goal")
        recover_transaction(root, WORKFLOW_ARTIFACT_MARKER, WORKFLOW_ARTIFACT_PREFIXES, WORKFLOW_ARTIFACT_KIND)
        recover_transaction(root, DISCUSSION_MARKER, ("docs/teamwork/discussion/",), "discussion")
        recover_transaction(root, COLLABORATE_MARKER, COLLABORATE_PREFIXES, "collaborate")
        require_initialized_memory(root)
        _, index = _read_index(root)
        index = _materialize_collaborate_index(index)
        validate_currentness(root, index)
        return {"valid": True}


# ---------------------------------------------------------------------------
# Case-bundle memory v2.


def reject_float(value: object, label: str = "value") -> None:
    if isinstance(value, float):
        fail(f"{label} must not contain floats")
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                fail(f"{label} object keys must be strings")
            reject_float(item, f"{label}.{key}")
    elif isinstance(value, list):
        for position, item in enumerate(value):
            reject_float(item, f"{label}[{position}]")


def canonical_json_bytes(value: object) -> bytes:
    reject_float(value)
    return unicodedata.normalize(
        "NFC",
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
    ).encode("utf-8")


def canonical_text_bytes(value: str) -> bytes:
    return unicodedata.normalize("NFC", value.replace("\r\n", "\n").replace("\r", "\n")).encode("utf-8")


def case_digest(domain: str, value: object | str | bytes) -> str:
    if isinstance(value, bytes):
        payload = value
    elif isinstance(value, str):
        payload = canonical_text_bytes(value)
    else:
        payload = canonical_json_bytes(value)
    return _hash(f"teamwork-case-v2:{domain}".encode("utf-8"), payload)


def seeded_case_digest(domain: bytes, seed: object) -> str:
    if not isinstance(seed, str) or HEX64_RE.fullmatch(seed) is None:
        fail("seed must be 64 lowercase hex characters")
    return _hash(domain, bytes.fromhex(seed))


def _seeded_id(prefix: str, domain: str, seed: object) -> str:
    domains = {
        "case-id": b"teamwork-case-id-v1",
        "claim-id": b"teamwork-claim-id-v1",
        "migration-id": b"teamwork-migration-id-v1",
    }
    if domain not in domains:
        fail(f"{domain} is not a supported seeded id domain")
    digest = seeded_case_digest(domains[domain], seed)
    return prefix + digest if prefix else digest


def case_id_from_seed(seed: object) -> str:
    return _seeded_id("c-", "case-id", seed)


def claim_id_from_seed(seed: object) -> str:
    return _seeded_id("cl-", "claim-id", seed)


def migration_id_from_seed(seed: object) -> str:
    return _seeded_id("m-", "migration-id", seed)


def _case_id(value: object) -> str:
    if not isinstance(value, str) or CASE_ID_RE.fullmatch(value) is None:
        fail("case_id must be c- followed by 64 lowercase hex characters")
    return value


def _artifact_id(value: object) -> str:
    if not isinstance(value, str) or ARTIFACT_ID_RE.fullmatch(value) is None:
        fail("artifact_id must be a- followed by 64 lowercase hex characters")
    return value


def _claim_id(value: object) -> str:
    if not isinstance(value, str) or CLAIM_ID_RE.fullmatch(value) is None:
        fail("claim_id must be cl- followed by 64 lowercase hex characters")
    return value


def _migration_id(value: object) -> str:
    if not isinstance(value, str) or MIGRATION_ID_RE.fullmatch(value) is None:
        fail("migration_id must be m- followed by 64 lowercase hex characters")
    return value


def _hex64(value: object, label: str) -> str:
    if not isinstance(value, str) or HEX64_RE.fullmatch(value) is None:
        fail(f"{label} must be 64 lowercase hex characters")
    return value


def _task_key(value: object) -> str:
    if not isinstance(value, str) or TASK_KEY_RE.fullmatch(value) is None or len(value) > 120:
        fail("task_key must be lowercase stable text")
    return value


def _iso(value: object, label: str) -> str:
    if not isinstance(value, str) or CONTROL_RE.search(value) is not None:
        fail(f"{label} must be an ISO timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        fail(f"{label} must be an ISO timestamp")
    if parsed.tzinfo is None:
        fail(f"{label} must include a timezone")
    if parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        fail(f"{label} must be UTC")
    if parsed.microsecond != 0:
        fail(f"{label} must not include fractional seconds")
    return parsed.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def case_manifest_path(case_id: str) -> str:
    return f"docs/teamwork/cases/{_case_id(case_id)}/manifest.json"


def case_base(case_id: str) -> str:
    return f"docs/teamwork/cases/{_case_id(case_id)}"


def case_live_document_path(case_id: str) -> str:
    return f"{case_base(case_id)}/live.md"


def derive_case_artifact_path(case_id: str, kind: str, artifact_id: str, *, delta: bool = False) -> str:
    """Return the current Writer document path for every semantic artifact.

    Explicit migration staging uses ``derive_case_source_artifact_path``
    internally. Keeping that distinction in the storage owner prevents
    workflow prompts from selecting an artifact tree or treating individual
    method outputs as separate live documents.
    """
    del artifact_id, delta
    if kind in CASE_ARTIFACT_KINDS and not kind.startswith("history-"):
        return case_live_document_path(case_id)
    if kind.startswith("history-"):
        fail("history artifacts do not have a live document path")
    fail("unsupported case artifact kind")


def derive_case_source_artifact_path(case_id: str, kind: str, artifact_id: str, *, delta: bool = False) -> str:
    """Return a temporary path used only while folding migration inputs."""
    base = case_base(case_id)
    if kind == "collaborate":
        return f"{base}/sources/collaborate/{_artifact_id(artifact_id)}.md"
    if kind == "goal":
        return f"{base}/sources/goal/{_artifact_id(artifact_id)}.md"
    if kind == "decision":
        return f"{base}/sources/decision/{_artifact_id(artifact_id)}.md"
    if kind == "plan":
        return f"{base}/sources/plan/{_artifact_id(artifact_id)}.md"
    if kind in CASE_EVIDENCE_KINDS:
        return f"{base}/sources/{kind}/{_artifact_id(artifact_id)}.md"
    if kind == "result":
        return f"{base}/sources/result/{_artifact_id(artifact_id)}.md"
    if kind == "review":
        review_digest = _hex64(artifact_id, "review digest")
        suffix = "-delta" if delta else ""
        return f"{base}/sources/review/{review_digest}{suffix}.md"
    if kind.startswith("history-"):
        history_kind = kind.removeprefix("history-")
        if history_kind not in CASE_HISTORY_KINDS:
            fail("unsupported history artifact kind")
        return f"{base}/history/{history_kind}/{_artifact_id(artifact_id)}.md"
    fail("unsupported case artifact kind")


def case_live_section(kind: str, path: str | None = None) -> str:
    if path is not None and "/history/" in path:
        return "Migration Appendix"
    if kind in {"collaborate", "goal"}:
        return "Purpose State"
    if kind == "decision":
        return "Decisions"
    if kind == "plan":
        return "Plan"
    if kind in CASE_EVIDENCE_KINDS:
        return "Evidence"
    if kind in CASE_REVIEW_KINDS or kind == "review":
        return "Review"
    if kind == "result":
        return "Outcome"
    return "Migration Appendix"


def case_live_purpose(kind: str) -> str:
    return {
        "collaborate": "discussion",
        "decision": "discussion",
        "research": "research",
        "debug": "debug",
        "plan": "plan",
        "review": "review",
        "review-delta": "review",
        "goal": "goal",
        "init": "init",
        "update": "update",
        "result": "result",
    }.get(kind, "task")


def case_live_artifact_kind(purpose: str, *, closed: bool, has_claims: bool) -> str:
    if closed:
        return "result"
    if has_claims:
        return "goal"
    return {
        "discussion": "collaborate",
        "research": "research",
        "debug": "debug",
        "plan": "plan",
        "review": "review",
        "init": "init",
        "update": "update",
        "result": "result",
    }.get(purpose, "evidence")


_LIVE_SECTION_START_RE = re.compile(r"^<!-- TEAMWORK:SECTION (.+) -->$")
_LIVE_SECTION_END = "<!-- /TEAMWORK:SECTION -->"


def render_case_live_document(
    *,
    case_id: str,
    title: str,
    purpose: str,
    status: str,
    generation: int,
    updated_at: str,
    needs_resolution: bool,
    sections: dict[str, str],
) -> str:
    case_id = _case_id(case_id)
    title = require_text(title, "live document title", maximum=200)
    if purpose not in CASE_LIVE_PURPOSES:
        fail("live document purpose is invalid")
    if status not in CASE_LIVE_STATUSES:
        fail("live document status is invalid")
    if not isinstance(generation, int) or isinstance(generation, bool) or generation < 1:
        fail("live document generation must be a positive integer")
    updated_at = _iso(updated_at, "live document updated_at")
    unknown = set(sections) - set(CASE_LIVE_SECTIONS)
    if unknown:
        fail("live document contains unsupported sections")
    lines = [
        f"Teamwork Live Document: {CASE_LIVE_DOCUMENT_VERSION}",
        f"Case ID: {case_id}",
        f"Purpose: {purpose}",
        f"Status: {status}",
        f"Generation: {generation}",
        f"Last Updated: {updated_at}",
        f"Needs Resolution: {'yes' if needs_resolution else 'no'}",
        "",
        f"# {title}",
    ]
    for heading in CASE_LIVE_SECTIONS:
        body = sections.get(heading)
        if body is None or not body.strip():
            continue
        lines.extend([
            "",
            f"<!-- TEAMWORK:SECTION {heading} -->",
            f"## {heading}",
            "",
            body.rstrip(),
            _LIVE_SECTION_END,
        ])
    return "\n".join(lines).rstrip() + "\n"


def parse_case_live_document(text: str, expected_case_id: str | None = None) -> dict[str, object]:
    text = require_markdown_body(text, "live document", maximum_bytes=CASE_LIVE_MAX_BYTES)
    lines = text.splitlines()
    if len(lines) < 9 or lines[0] != f"Teamwork Live Document: {CASE_LIVE_DOCUMENT_VERSION}":
        fail("live document has an unsupported envelope")
    fields: dict[str, str] = {}
    for line in lines[1:7]:
        if ": " not in line:
            fail("live document envelope is malformed")
        key, value = line.split(": ", 1)
        fields[key] = value
    if set(fields) != {"Case ID", "Purpose", "Status", "Generation", "Last Updated", "Needs Resolution"}:
        fail("live document envelope fields are invalid")
    case_id = _case_id(fields["Case ID"])
    if expected_case_id is not None and case_id != _case_id(expected_case_id):
        fail("live document case identity mismatch")
    purpose = fields["Purpose"]
    if purpose not in CASE_LIVE_PURPOSES:
        fail("live document purpose is invalid")
    status = fields["Status"]
    if status not in CASE_LIVE_STATUSES:
        fail("live document status is invalid")
    try:
        generation = int(fields["Generation"])
    except ValueError:
        fail("live document generation is invalid")
    if generation < 1 or str(generation) != fields["Generation"]:
        fail("live document generation is invalid")
    updated_at = _iso(fields["Last Updated"], "live document updated_at")
    if fields["Needs Resolution"] not in {"yes", "no"}:
        fail("live document Needs Resolution must be yes or no")
    title_line = next((line for line in lines[7:] if line.startswith("# ")), None)
    if title_line is None:
        fail("live document title is missing")
    title = require_text(title_line[2:], "live document title", maximum=200)
    sections: dict[str, str] = {}
    position = 0
    while position < len(lines):
        match = _LIVE_SECTION_START_RE.fullmatch(lines[position])
        if match is None:
            position += 1
            continue
        heading = match.group(1)
        if heading not in CASE_LIVE_SECTIONS or heading in sections:
            fail("live document section markers are invalid")
        if position + 2 >= len(lines) or lines[position + 1] != f"## {heading}" or lines[position + 2] != "":
            fail("live document section heading is malformed")
        try:
            end = lines.index(_LIVE_SECTION_END, position + 3)
        except ValueError:
            fail("live document section is not closed")
        sections[heading] = "\n".join(lines[position + 3:end]).rstrip() + "\n"
        position = end + 1
    return {
        "case_id": case_id,
        "title": title,
        "purpose": purpose,
        "status": status,
        "generation": generation,
        "updated_at": updated_at,
        "needs_resolution": fields["Needs Resolution"] == "yes",
        "sections": sections,
    }


def artifact_id_for_case(kind: str, envelope: dict[str, object], body: str) -> str:
    clean_envelope = {
        "schema_version": 1,
        "role": require_slug(envelope.get("role", kind), "artifact role"),
        "subtype": require_slug(envelope.get("subtype", kind), "artifact subtype"),
        "case_id": _case_id(envelope.get("case_id")),
        "claim_ids": sorted(_claim_id(item) for item in envelope.get("claim_ids", [])),
        "consumer": require_text(envelope.get("consumer", "teamwork"), "artifact consumer", maximum=200),
        "source_revision": _hex64(envelope.get("source_revision"), "artifact source_revision"),
        "immutable": True if envelope.get("immutable", True) is True else fail("artifact envelope immutable must be true"),
    }
    return "a-" + case_digest("artifact-id", {"envelope": clean_envelope, "rendered_sha256": hashlib.sha256(canonical_text_bytes(body)).hexdigest()})


def artifact_envelope_digest(envelope: dict[str, object]) -> str:
    return case_digest("artifact-envelope", envelope)


def artifact_digest(path: str, body: str) -> str:
    return hashlib.sha256(canonical_text_bytes(body)).hexdigest()


def validate_case_manifest(value: object, *, migration_read: bool = False) -> dict[str, object]:
    base_keys = {
        "schema_version", "case_id", "case_seed_b64", "created_at", "closed_at",
        "status", "claims", "artifacts", "history", "references", "runtime",
        "migration_sources",
    }
    if not isinstance(value, dict):
        fail("v2 case manifest has an unsupported schema")
    manifest_schema = value.get("schema_version")
    if manifest_schema == 1 and not migration_read:
        fail("case manifest schema_version 1 requires explicit project migration")
    expected_keys = base_keys if manifest_schema == 1 else base_keys | {"document"}
    if manifest_schema not in ({1, 2} if migration_read else {2}) or set(value) != expected_keys:
        fail("case manifest must use current schema_version 2 with exact fields")
    case_id = _case_id(value.get("case_id"))
    status = value.get("status")
    if status not in CASE_PHASES:
        fail("v2 case manifest has an invalid lifecycle phase")
    closed_at = value.get("closed_at")
    if status == "closed":
        closed_at = _iso(closed_at, "closed_at")
    elif closed_at is not None:
        fail("closed_at must be null unless status is closed")
    case_seed_b64 = value.get("case_seed_b64")
    if not isinstance(case_seed_b64, str):
        fail("case_seed_b64 must be base64 text")
    try:
        seed_bytes = base64.b64decode(case_seed_b64.encode("ascii"), validate=True)
    except Exception:
        fail("case_seed_b64 must be valid base64")
    if len(seed_bytes) != 32:
        fail("case_seed_b64 must encode exactly 32 bytes")
    runtime = value.get("runtime")
    if not isinstance(runtime, dict) or set(runtime) != {"active_route", "state_revision"}:
        fail("manifest runtime has an unsupported schema")
    active_route = checked_relative(runtime.get("active_route"), "runtime.active_route")
    if not active_route.startswith(case_base(case_id) + "/"):
        fail("runtime active_route must stay inside its case")
    state_revision = _hex64(runtime.get("state_revision"), "runtime.state_revision")
    for name in ("history", "references", "migration_sources"):
        raw = value.get(name)
        if not isinstance(raw, list) or len(raw) > CASE_CAPS[name]:
            fail(f"manifest {name} exceeds its cap or is not an array")
    claims_raw = value.get("claims")
    if not isinstance(claims_raw, dict) or len(claims_raw) > CASE_CAPS["claims"]:
        fail("manifest claims exceeds its cap or is not an object")
    claims: dict[str, dict[str, object]] = {}
    for claim_id_raw, raw in claims_raw.items():
        claim_id = _claim_id(claim_id_raw)
        if not isinstance(raw, dict) or set(raw) != {"descriptor_version", "descriptor_digest", "status", "acquired_at", "released_at", "head_artifact_id", "head_digest"}:
            fail(f"manifest claims[{claim_id}] has an unsupported schema")
        claim_status = raw.get("status")
        if claim_status not in {"active", "released"}:
            fail(f"manifest claims[{claim_id}].status is invalid")
        acquired_at = _iso(raw.get("acquired_at"), "claim acquired_at")
        released_at = raw.get("released_at")
        if claim_status == "released":
            released_at = _iso(released_at, "claim released_at")
        elif released_at is not None:
            fail("released_at must be null unless claim is released")
        claims[claim_id] = {
            "descriptor_version": raw.get("descriptor_version") if raw.get("descriptor_version") == 1 else fail("claim descriptor_version must be 1"),
            "descriptor_digest": _hex64(raw.get("descriptor_digest"), "claim descriptor_digest"),
            "status": claim_status,
            "acquired_at": acquired_at,
            "released_at": released_at,
            "head_artifact_id": _artifact_id(raw.get("head_artifact_id")),
            "head_digest": _hex64(raw.get("head_digest"), "claim head_digest"),
        }
    artifacts_raw = value.get("artifacts")
    if not isinstance(artifacts_raw, dict) or len(artifacts_raw) > CASE_CAPS["artifacts"]:
        fail("manifest artifacts exceeds its cap or is not an object")
    artifacts: dict[str, dict[str, object]] = {}
    for artifact_id_raw, raw in artifacts_raw.items():
        artifact_id = _artifact_id(artifact_id_raw)
        if not isinstance(raw, dict) or set(raw) != {"role", "subtype", "path", "envelope_digest", "byte_digest", "created_at", "immutable", "consumer", "source_revision"}:
            fail(f"manifest artifacts[{artifact_id}] has an unsupported schema")
        role = require_slug(raw.get("role"), "artifact role")
        subtype = require_slug(raw.get("subtype"), "artifact subtype")
        manifest_kind = role if role != "history" else f"history-{subtype}"
        if manifest_kind not in CASE_ARTIFACT_KINDS:
            fail(f"manifest artifacts[{artifact_id}].role/subtype is unsupported")
        path = checked_relative(raw.get("path"), "case artifact path")
        if not path.startswith(case_base(case_id) + "/"):
            fail("case artifact path must stay inside its case")
        if raw.get("immutable") is not True:
            fail("case artifacts must be immutable")
        artifacts[artifact_id] = {
            "role": role,
            "subtype": subtype,
            "path": path,
            "envelope_digest": _hex64(raw.get("envelope_digest"), "artifact envelope_digest"),
            "byte_digest": _hex64(raw.get("byte_digest"), "artifact byte_digest"),
            "created_at": _iso(raw.get("created_at"), "artifact created_at"),
            "immutable": True,
            "consumer": require_text(raw.get("consumer"), "artifact consumer", maximum=200),
            "source_revision": _hex64(raw.get("source_revision"), "artifact source_revision"),
        }
    document: dict[str, object] | None = None
    if manifest_schema == 2:
        raw_document = value.get("document")
        if raw_document is not None:
            document_fields = {
                "path", "generation", "byte_digest", "updated_at", "title",
                "purpose", "status", "needs_resolution", "latest_artifact_id",
                "source_artifact_ids",
            }
            if not isinstance(raw_document, dict) or set(raw_document) != document_fields:
                fail("manifest document has an unsupported schema")
            document_path = checked_relative(raw_document.get("path"), "document.path")
            if document_path != case_live_document_path(case_id):
                fail("manifest document.path must be the case live.md")
            generation = raw_document.get("generation")
            if not isinstance(generation, int) or isinstance(generation, bool) or generation < 1:
                fail("manifest document.generation must be a positive integer")
            purpose = raw_document.get("purpose")
            if purpose not in CASE_LIVE_PURPOSES:
                fail("manifest document.purpose is invalid")
            document_status = raw_document.get("status")
            if document_status not in CASE_LIVE_STATUSES:
                fail("manifest document.status is invalid")
            source_ids_raw = raw_document.get("source_artifact_ids")
            if not isinstance(source_ids_raw, list) or len(source_ids_raw) > CASE_CAPS["artifacts"]:
                fail("manifest document.source_artifact_ids is invalid")
            source_ids = [_artifact_id(item) for item in source_ids_raw]
            if len(source_ids) != len(set(source_ids)) or any(item not in artifacts for item in source_ids):
                fail("manifest document sources must be unique known artifacts")
            latest_artifact_id = _artifact_id(raw_document.get("latest_artifact_id"))
            if latest_artifact_id not in artifacts:
                fail("manifest document.latest_artifact_id must exist in artifacts")
            document = {
                "path": document_path,
                "generation": generation,
                "byte_digest": _hex64(raw_document.get("byte_digest"), "document.byte_digest"),
                "updated_at": _iso(raw_document.get("updated_at"), "document.updated_at"),
                "title": require_text(raw_document.get("title"), "document.title", maximum=200),
                "purpose": purpose,
                "status": document_status,
                "needs_resolution": raw_document.get("needs_resolution") if isinstance(raw_document.get("needs_resolution"), bool) else fail("manifest document.needs_resolution must be boolean"),
                "latest_artifact_id": latest_artifact_id,
                "source_artifact_ids": source_ids,
            }
    history: list[dict[str, object]] = []
    for position, raw in enumerate(value["history"]):
        if not isinstance(raw, dict) or set(raw) != {"artifact_id", "role", "superseded_by", "retained_reason", "recorded_at"}:
            fail(f"manifest history[{position}] has an unsupported schema")
        artifact_id = _artifact_id(raw.get("artifact_id"))
        superseded_by = raw.get("superseded_by")
        if superseded_by is not None:
            superseded_by = _artifact_id(superseded_by)
        retained_reason = raw.get("retained_reason")
        if retained_reason not in {"consumed", "reviewed", "superseded", "closed"}:
            fail("history retained_reason is invalid")
        history.append({
            "artifact_id": artifact_id,
            "role": require_slug(raw.get("role"), "history role"),
            "superseded_by": superseded_by,
            "retained_reason": retained_reason,
            "recorded_at": _iso(raw.get("recorded_at"), "history recorded_at"),
        })
    references: list[dict[str, object]] = []
    for position, raw in enumerate(value["references"]):
        if not isinstance(raw, dict) or set(raw) != {"case_id", "claim_id", "artifact_id", "digest"}:
            fail(f"manifest references[{position}] has an unsupported schema")
        references.append({"case_id": _case_id(raw.get("case_id")), "claim_id": _claim_id(raw.get("claim_id")), "artifact_id": _artifact_id(raw.get("artifact_id")), "digest": _hex64(raw.get("digest"), "reference digest")})
    sources: list[dict[str, object]] = []
    for position, raw in enumerate(value["migration_sources"]):
        if not isinstance(raw, dict) or set(raw) != {"source_path", "source_digest", "classification", "migration_id", "artifact_id"}:
            fail(f"manifest migration_sources[{position}] has an unsupported schema")
        sources.append({
            "source_path": checked_relative(raw.get("source_path"), "migration source path"),
            "source_digest": _hex64(raw.get("source_digest"), "migration source_digest"),
            "classification": require_slug(raw.get("classification"), "migration source classification"),
            "migration_id": _migration_id(raw.get("migration_id")),
            "artifact_id": _artifact_id(raw.get("artifact_id")),
        })
    for name, rows, key in (("history", history, "artifact_id"), ("references", references, "digest"), ("migration_sources", sources, "source_path")):
        ids = [str(row[key]) for row in rows]
        if len(ids) != len(set(ids)):
            fail(f"manifest {name} contains duplicate identifiers")
    if manifest_schema == 2 and not migration_read:
        if document is None:
            if artifacts or history or references or sources:
                fail("a current manifest without live.md must not retain artifacts")
        else:
            if set(artifacts) != {document["latest_artifact_id"]}:
                fail("a current manifest may index only its live.md artifact")
            live_row = artifacts[str(document["latest_artifact_id"])]
            if live_row["path"] != document["path"] or live_row["byte_digest"] != document["byte_digest"]:
                fail("the live.md artifact must match the document record")
            if history or references:
                fail("current manifests do not retain artifact history or references")
            if any(source["artifact_id"] != document["latest_artifact_id"] for source in sources):
                fail("all migration provenance must target live.md")
            if any(claim["head_artifact_id"] != document["latest_artifact_id"] for claim in claims.values()):
                fail("all current claim heads must target live.md")
    manifest = {
        "schema_version": manifest_schema,
        "case_id": case_id,
        "case_seed_b64": case_seed_b64,
        "created_at": _iso(value.get("created_at"), "created_at"),
        "closed_at": closed_at,
        "status": status,
        "claims": dict(sorted(claims.items())),
        "artifacts": dict(sorted(artifacts.items())),
        "history": history,
        "references": references,
        "runtime": {"active_route": active_route, "state_revision": state_revision},
        "migration_sources": sources,
    }
    if manifest_schema == 2:
        manifest["document"] = document
    text = json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if len(text.encode("utf-8")) > CASE_MANIFEST_MAX_BYTES:
        fail("case manifest exceeds maximum serialized size")
    return manifest


def validate_case_index(value: object) -> dict[str, object]:
    expected_keys = {"schema_version", "project", "active_cases", "claim_heads", "aliases", "recent_cases", "migration"}
    if not isinstance(value, dict) or set(value) != expected_keys:
        fail("v2 root index has an unsupported schema")
    if value.get("schema_version") != 3:
        fail("current root index schema_version must be 3")
    project = value.get("project")
    if not isinstance(project, dict) or set(project) != {"name", "root", "description"}:
        fail("v2 root index project must be an object")
    project_clean = {
        "name": require_text(project.get("name"), "project.name", maximum=200),
        "root": project.get("root") if project.get("root") == "." else fail("project.root must be ."),
        "description": require_text(project.get("description"), "project.description", maximum=1000),
    }
    active_cases_raw = value.get("active_cases")
    claim_heads_raw = value.get("claim_heads")
    aliases_raw = value.get("aliases")
    recent_raw = value.get("recent_cases")
    if not isinstance(active_cases_raw, list) or len(active_cases_raw) > CASE_CAPS["active_cases"]:
        fail("active_cases exceeds its cap or is not an array")
    if not isinstance(claim_heads_raw, dict) or len(claim_heads_raw) > CASE_CAPS["claim_heads"]:
        fail("claim_heads exceeds its cap or is not an object")
    if not isinstance(aliases_raw, dict) or len(aliases_raw) > CASE_CAPS["aliases"]:
        fail("aliases exceeds its cap or is not an object")
    if not isinstance(recent_raw, list):
        fail("recent_cases must be an array")
    active_cases: list[dict[str, object]] = []
    seen_cases: set[str] = set()
    seen_tasks: set[str] = set()
    for position, raw in enumerate(active_cases_raw):
        if not isinstance(raw, dict) or set(raw) != {"case_id", "manifest_path", "manifest_revision", "phase", "task_key"}:
            fail(f"active_cases[{position}] has an unsupported schema")
        case_id = _case_id(raw.get("case_id"))
        task = _task_key(raw.get("task_key"))
        if case_id in seen_cases or task in seen_tasks:
            fail("active_cases case_id and task_key must be unique")
        seen_cases.add(case_id)
        seen_tasks.add(task)
        phase = raw.get("phase")
        if phase not in CASE_ACTIVE_PHASES:
            fail("active_cases phase must be active")
        path = checked_relative(raw.get("manifest_path"), "active_cases manifest_path")
        if path != case_manifest_path(case_id):
            fail("active_cases manifest_path does not match case_id")
        active_cases.append({"case_id": case_id, "manifest_path": path, "manifest_revision": _hex64(raw.get("manifest_revision"), "manifest_revision"), "phase": phase, "task_key": task})
    claim_heads: dict[str, dict[str, object]] = {}
    for claim_id_raw, raw in claim_heads_raw.items():
        claim_id = _claim_id(claim_id_raw)
        if not isinstance(raw, dict) or set(raw) != {"case_id", "artifact_id", "artifact_digest", "claim_revision", "status"}:
            fail(f"claim_heads[{claim_id}] has an unsupported schema")
        case_id = _case_id(raw.get("case_id"))
        artifact_id = _artifact_id(raw.get("artifact_id"))
        if raw.get("status") != "active":
            fail("root claim_heads status must be active")
        claim_heads[claim_id] = {"case_id": case_id, "artifact_id": artifact_id, "artifact_digest": _hex64(raw.get("artifact_digest"), "artifact_digest"), "claim_revision": _hex64(raw.get("claim_revision"), "claim_revision"), "status": "active"}
    aliases: dict[str, dict[str, object]] = {}
    for alias, raw in aliases_raw.items():
        alias = require_slug(alias, "case alias")
        if not isinstance(raw, dict) or set(raw) != {"target_type", "target_id", "manifest_path", "manifest_revision"}:
            fail(f"aliases[{alias}] has an unsupported schema")
        if raw.get("target_type") != "case":
            fail("case aliases may only target cases")
        target_id = _case_id(raw.get("target_id"))
        aliases[alias] = {
            "target_type": "case",
            "target_id": target_id,
            "manifest_path": checked_relative(raw.get("manifest_path"), "alias manifest_path"),
            "manifest_revision": _hex64(raw.get("manifest_revision"), "alias manifest_revision"),
        }
        if aliases[alias]["manifest_path"] != case_manifest_path(target_id):
            fail("alias manifest_path does not match target_id")
    recent_cases: list[dict[str, object]] = []
    for position, raw in enumerate(recent_raw):
        if not isinstance(raw, dict) or set(raw) != {"case_id", "manifest_path", "closed_at", "result_artifact_id", "result_digest"}:
            fail(f"recent_cases[{position}] has an unsupported schema")
        case_id = _case_id(raw.get("case_id"))
        manifest_path = checked_relative(raw.get("manifest_path"), "recent manifest_path")
        if manifest_path != case_manifest_path(case_id):
            fail("recent manifest_path does not match case_id")
        recent_cases.append({"case_id": case_id, "manifest_path": manifest_path, "closed_at": _iso(raw.get("closed_at"), "recent closed_at"), "result_artifact_id": _artifact_id(raw.get("result_artifact_id")), "result_digest": _hex64(raw.get("result_digest"), "recent result_digest")})
    recent_cases = sorted(recent_cases, key=lambda item: (str(item["closed_at"]), str(item["case_id"])), reverse=True)[:CASE_CAPS["recent_cases"]]
    migration_raw = value.get("migration")
    migration_keys = {"migration_id", "phase", "journal_path", "baseline_digest", "report_digest", "candidate_digest", "archive_manifest_digest"}
    if migration_raw is None:
        migration = None
    elif not isinstance(migration_raw, dict) or set(migration_raw) != migration_keys:
        fail("migration has an unsupported schema")
    else:
        phase = migration_raw.get("phase")
        if phase not in MIGRATION_PHASES:
            fail("migration phase is invalid")
        migration = {"phase": phase, "migration_id": _migration_id(migration_raw.get("migration_id")), "journal_path": checked_relative(migration_raw.get("journal_path"), "journal_path")}
        for key in ("baseline_digest", "report_digest", "candidate_digest", "archive_manifest_digest"):
            migration[key] = _hex64(migration_raw.get(key), key)
    index = {"schema_version": 3, "project": project_clean, "active_cases": active_cases, "claim_heads": dict(sorted(claim_heads.items())), "aliases": dict(sorted(aliases.items())), "recent_cases": recent_cases, "migration": migration}
    text = json.dumps(index, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if len(text.encode("utf-8")) > CASE_INDEX_MAX_BYTES:
        fail("current root index exceeds maximum serialized size")
    return index


def validate_legacy_case_index(value: object) -> dict[str, object]:
    """Validate schema 2 only as explicit project-migration input."""
    if not isinstance(value, dict) or value.get("schema_version") != 2:
        fail("legacy case index schema_version must be 2")
    promoted = dict(value)
    promoted["schema_version"] = 3
    validated = validate_case_index(promoted)
    validated["schema_version"] = 2
    return validated


def empty_case_index(project_name: str = "Teamwork") -> dict[str, object]:
    return validate_case_index({
        "schema_version": 3,
        "project": {
            "name": project_name,
            "root": ".",
            "description": "Local Teamwork case-bundle index for this project.",
        },
        "active_cases": [],
        "claim_heads": {},
        "aliases": {},
        "recent_cases": [],
        "migration": None,
    })


def detect_teamwork_memory_schema(root: Path, *, migration: bool = False) -> str:
    text = safe_read_text(root, INDEX_PATH, optional=True)
    if text is None:
        fail("Teamwork memory is not initialized")
    value = _decode_json(text, "Teamwork index")
    if not isinstance(value, dict):
        fail("Teamwork index must be an object")
    v1_keys = {"last_updated", "active", "entries"}.intersection(value)
    v2_keys = {"active_cases", "claim_heads", "aliases", "recent_cases", "migration"}.intersection(value)
    if v1_keys and v2_keys:
        fail("hybrid Teamwork memory state detected")
    if value.get("schema_version") == 1 and v1_keys:
        if not migration:
            fail("legacy-v1 Teamwork memory requires explicit project migration")
        parse_index(text, migration=migration)
        return "legacy-v1"
    if value.get("schema_version") == 2 and v2_keys:
        if not migration:
            fail("case-v2 Teamwork memory requires explicit project migration")
        validate_legacy_case_index(value)
        return "case-v2-legacy"
    if value.get("schema_version") == 3 and v2_keys:
        validate_case_index(value)
        return "case-v3"
    fail("unknown Teamwork memory schema")


def serialize_case_index(index: dict[str, object]) -> str:
    return json.dumps(validate_case_index(index), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def serialize_case_manifest(manifest: dict[str, object]) -> str:
    return json.dumps(validate_case_manifest(manifest), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def case_manifest_revision(manifest: dict[str, object]) -> str:
    stable = {key: value for key, value in validate_case_manifest(manifest).items() if key != "updated_at"}
    return case_digest("manifest-revision", stable)


def read_case_index(root: Path) -> tuple[str, dict[str, object]]:
    text = safe_read_text(root, INDEX_PATH)
    assert text is not None
    return text, validate_case_index(_decode_json(text, "case index"))


def read_case_manifest(root: Path, case_id: str) -> tuple[str, dict[str, object]]:
    text = safe_read_text(root, case_manifest_path(case_id))
    assert text is not None
    return text, validate_case_manifest(_decode_json(text, "case manifest"))


def read_legacy_case_manifest(root: Path, case_id: str) -> tuple[str, dict[str, object]]:
    text = safe_read_text(root, case_manifest_path(case_id))
    assert text is not None
    return text, validate_case_manifest(_decode_json(text, "legacy case manifest"), migration_read=True)


def legacy_case_manifest_revision(manifest: dict[str, object]) -> str:
    stable = {
        key: value
        for key, value in validate_case_manifest(manifest, migration_read=True).items()
        if key != "updated_at"
    }
    return case_digest("manifest-revision", stable)


def cases_revision(root: Path, index_text: str, index: dict[str, object]) -> str:
    parts = [b"case-v3", index_text.encode("utf-8")]
    case_ids = sorted({str(item["case_id"]) for item in index["active_cases"]} | {str(item["case_id"]) for item in index["recent_cases"]})
    for case_id in case_ids:
        manifest = safe_read_bytes(root, case_manifest_path(case_id), optional=True)
        if manifest is not None:
            parts.append(case_id.encode("utf-8"))
            parts.append(manifest)
    return _hash(*parts)


def inspect_cases(root: Path) -> dict[str, object]:
    with locked_memory(root):
        recovered = recover_transaction(root, CASE_TRANSACTION_MARKER, CASE_PREFIXES, "case")
        mode = detect_teamwork_memory_schema(root)
        if mode == "legacy-v1":
            text = safe_read_text(root, INDEX_PATH)
            assert text is not None
            return {"initialized": True, "schema_mode": "legacy-v1", "recovered": recovered, "revision": case_digest("legacy-v1", text), "active_cases": []}
        index_text, index = read_case_index(root)
        active_cases = []
        for row in index["active_cases"]:
            _, manifest = read_case_manifest(root, str(row["case_id"]))
            revision = case_manifest_revision(manifest)
            if revision != row["manifest_revision"]:
                fail("active case manifest revision does not match root index")
            active_cases.append({"path": row["manifest_path"], "revision": revision, "state": manifest})
        return {"initialized": True, "schema_mode": "case-v3", "recovered": recovered, "revision": cases_revision(root, index_text, index), "active_cases": active_cases, "claim_heads": index["claim_heads"], "aliases": index["aliases"], "recent_cases": index["recent_cases"], "migration": index["migration"]}


def render_case_artifact(kind: str, title: str, body: str, *, source_digest: str, updated_at: str) -> str:
    return f"Artifact Type: case-{kind}\nLast Updated: {updated_at}\nSource Digest: {source_digest}\n\n# {title}\n\n{body.rstrip()}\n"


def _artifact_kind_from_row(row: dict[str, object]) -> str:
    role = str(row["role"])
    subtype = str(row["subtype"])
    if role in {"evidence", "review", "history"}:
        return subtype if role != "history" else f"history-{subtype}"
    return role


def _fold_existing_artifacts_into_live(
    root: Path,
    manifest: dict[str, object],
) -> tuple[dict[str, str], bool, list[str]]:
    grouped: dict[str, list[tuple[str, str, str]]] = {}
    for artifact_id, row in sorted(
        manifest["artifacts"].items(),
        key=lambda item: (str(item[1]["created_at"]), str(item[0])),
    ):
        path = str(row["path"])
        raw = safe_read_bytes(root, path)
        assert raw is not None
        if hashlib.sha256(raw).hexdigest() != row["byte_digest"]:
            fail("case artifact bytes changed before live-document fold", category="INDETERMINATE")
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            fail("case artifact is not UTF-8 and cannot be folded", category="INDETERMINATE")
        kind = _artifact_kind_from_row(row)
        heading = case_live_section(kind, path)
        grouped.setdefault(heading, []).append((str(artifact_id), str(row["byte_digest"]), text))
    sections: dict[str, str] = {}
    needs_resolution = False
    for heading in CASE_LIVE_SECTIONS:
        rows = grouped.get(heading, [])
        if not rows:
            continue
        distinct = {digest for _, digest, _ in rows}
        if heading in CASE_REPLACE_SECTIONS and len(distinct) > 1:
            needs_resolution = True
        entries = []
        if heading in CASE_REPLACE_SECTIONS and len(distinct) > 1:
            entries.extend([
                "> **Needs resolution:** multiple preserved sources disagree; no source was selected as canonical.",
                "",
            ])
        for artifact_id, digest, text in rows:
            entries.extend([
                f"### Preserved source `{artifact_id}`",
                "",
                f"Byte digest: `{digest}`",
                "",
                text.rstrip(),
                "",
            ])
        sections[heading] = "\n".join(entries).rstrip() + "\n"
    return sections, needs_resolution, [str(item) for item in manifest["artifacts"]]


def _read_case_live_state(
    root: Path,
    manifest: dict[str, object],
    *,
    fallback_title: str,
) -> dict[str, object]:
    document = manifest.get("document") if manifest.get("schema_version") == 2 else None
    if document is None:
        sections, needs_resolution, source_ids = _fold_existing_artifacts_into_live(root, manifest)
        return {
            "title": fallback_title,
            "purpose": "task",
            "status": "active",
            "generation": 0,
            "needs_resolution": needs_resolution,
            "sections": sections,
            "source_artifact_ids": source_ids,
        }
    assert isinstance(document, dict)
    raw = safe_read_bytes(root, str(document["path"]))
    assert raw is not None
    if hashlib.sha256(raw).hexdigest() != document["byte_digest"]:
        fail("live document bytes do not match the manifest", category="INDETERMINATE")
    try:
        state = parse_case_live_document(raw.decode("utf-8"), str(manifest["case_id"]))
    except UnicodeDecodeError:
        fail("live document must be UTF-8", category="INDETERMINATE")
    for key in ("generation", "title", "purpose", "status", "needs_resolution"):
        if state[key] != document[key]:
            fail(f"live document {key} does not match the manifest", category="INDETERMINATE")
    state["source_artifact_ids"] = list(document["source_artifact_ids"])
    return state


def _merge_case_live_section(
    sections: dict[str, str],
    *,
    heading: str,
    body: str,
    kind: str,
    updated_at: str,
) -> dict[str, str]:
    sections = dict(sections)
    clean = body.rstrip() + "\n"
    prior = sections.get(heading)
    if heading in CASE_REPLACE_SECTIONS:
        if prior is not None and prior.rstrip() == clean.rstrip():
            fail("live document update has no material semantic change")
        sections[heading] = clean
        return sections
    entry = "\n".join([
        f"### {kind.replace('-', ' ').title()} — {updated_at}",
        "",
        clean.rstrip(),
        "",
    ]).rstrip() + "\n"
    if prior is not None and clean.rstrip() in prior.rstrip():
        fail("live document update has no material semantic change")
    sections[heading] = ("" if prior is None else prior.rstrip() + "\n\n") + entry
    return sections


def _install_case_live_revision(
    root: Path,
    manifest: dict[str, object],
    *,
    title: str,
    kind: str,
    body: str,
    source_digest: str,
    consumer: str,
    updated_at: str,
    outputs: dict[str, Output],
    finalize: bool = False,
) -> tuple[dict[str, object], str, str]:
    case_id = str(manifest["case_id"])
    live_path = case_live_document_path(case_id)
    document = manifest.get("document") if manifest.get("schema_version") == 2 else None
    represented_live = any(str(row["path"]) == live_path for row in manifest["artifacts"].values())
    if document is None and not represented_live and safe_read_bytes(root, live_path, optional=True) is not None:
        fail("unmanaged live.md collision; refusing to overwrite", category="INDETERMINATE")
    state = _read_case_live_state(root, manifest, fallback_title=title)
    heading = case_live_section(kind)
    sections = _merge_case_live_section(
        state["sections"],
        heading=heading,
        body=body,
        kind=kind,
        updated_at=updated_at,
    )
    next_purpose = case_live_purpose(kind)
    prior_purpose = str(state["purpose"])
    purpose = next_purpose if prior_purpose == "task" else prior_purpose
    if prior_purpose not in {"task", next_purpose}:
        purpose = "task"
    generation = int(state["generation"]) + 1
    status = "finalized" if finalize else "active"
    rendered = render_case_live_document(
        case_id=case_id,
        title=str(state["title"]),
        purpose=purpose,
        status=status,
        generation=generation,
        updated_at=updated_at,
        needs_resolution=bool(state["needs_resolution"]),
        sections=sections,
    )
    role, subtype = _artifact_role(kind)
    envelope = {
        "role": role,
        "subtype": subtype,
        "case_id": case_id,
        "claim_ids": [],
        "consumer": consumer,
        "source_revision": source_digest,
        "immutable": True,
    }
    artifact_id = artifact_id_for_case(kind, envelope, rendered)
    path = live_path
    prior_live_ids = {
        str(prior_id)
        for prior_id, row in manifest["artifacts"].items()
        if str(row["path"]) == path
    }
    if prior_live_ids:
        manifest = dict(manifest)
        manifest["artifacts"] = {
            prior_id: row
            for prior_id, row in manifest["artifacts"].items()
            if str(prior_id) not in prior_live_ids
        }
        manifest["history"] = [
            row for row in manifest["history"]
            if str(row["artifact_id"]) not in prior_live_ids
        ]
        if manifest.get("schema_version") == 2:
            manifest["document"] = None
        manifest = validate_case_manifest(manifest)
    digest = artifact_digest(path, rendered)
    manifest = _case_add_artifact(
        manifest,
        kind=kind,
        path=path,
        artifact_id=artifact_id,
        digest=digest,
        updated_at=updated_at,
        source_revision=source_digest,
        consumer=consumer,
        allow_document_staging=True,
    )
    claims = {}
    for claim_id, raw_claim in manifest["claims"].items():
        claim = dict(raw_claim)
        if claim["head_artifact_id"] in prior_live_ids:
            claim["head_artifact_id"] = artifact_id
            claim["head_digest"] = digest
        claims[claim_id] = claim
    manifest = dict(manifest)
    manifest["claims"] = claims
    manifest["schema_version"] = 2
    manifest["document"] = {
        "path": path,
        "generation": generation,
        "byte_digest": digest,
        "updated_at": updated_at,
        "title": str(state["title"]),
        "purpose": purpose,
        "status": status,
        "needs_resolution": bool(state["needs_resolution"]),
        "latest_artifact_id": artifact_id,
        "source_artifact_ids": [artifact_id],
    }
    manifest["runtime"] = {
        "active_route": path,
        "state_revision": case_digest(
            "case-runtime",
            {"case_id": case_id, "path": path, "generation": generation, "at": updated_at},
        ),
    }
    outputs[path] = Output(rendered.encode("utf-8"))
    return validate_case_manifest(manifest), artifact_id, digest


def _finalize_case_live_document(
    root: Path,
    manifest: dict[str, object],
    *,
    title: str,
    updated_at: str,
    outputs: dict[str, Output],
) -> dict[str, object]:
    state = _read_case_live_state(root, manifest, fallback_title=title)
    if state["status"] == "finalized":
        fail("live document is already finalized")
    case_id = str(manifest["case_id"])
    generation = int(state["generation"]) + 1
    rendered = render_case_live_document(
        case_id=case_id,
        title=str(state["title"]),
        purpose=str(state["purpose"]),
        status="finalized",
        generation=generation,
        updated_at=updated_at,
        needs_resolution=bool(state["needs_resolution"]),
        sections=dict(state["sections"]),
    )
    source_digest = case_digest(
        "live-finalize",
        {"case_id": case_id, "generation": generation, "at": updated_at},
    )
    envelope = {
        "role": "result",
        "subtype": "result",
        "case_id": case_id,
        "claim_ids": [],
        "consumer": "teamwork",
        "source_revision": source_digest,
        "immutable": True,
    }
    artifact_id = artifact_id_for_case("result", envelope, rendered)
    path = case_live_document_path(case_id)
    prior_live_ids = {
        str(prior_id)
        for prior_id, row in manifest["artifacts"].items()
        if str(row["path"]) == path
    }
    manifest = dict(manifest)
    manifest["artifacts"] = {
        prior_id: row
        for prior_id, row in manifest["artifacts"].items()
        if str(prior_id) not in prior_live_ids
    }
    manifest["history"] = [
        row for row in manifest["history"]
        if str(row["artifact_id"]) not in prior_live_ids
    ]
    manifest["document"] = None
    manifest = validate_case_manifest(manifest)
    digest = artifact_digest(path, rendered)
    manifest = _case_add_artifact(
        manifest,
        kind="result",
        path=path,
        artifact_id=artifact_id,
        digest=digest,
        updated_at=updated_at,
        source_revision=source_digest,
        consumer="teamwork",
        allow_document_staging=True,
    )
    claims = {}
    for claim_id, raw_claim in manifest["claims"].items():
        claim = dict(raw_claim)
        if claim["head_artifact_id"] in prior_live_ids:
            claim["head_artifact_id"] = artifact_id
            claim["head_digest"] = digest
        claims[claim_id] = claim
    manifest = dict(manifest)
    manifest["claims"] = claims
    manifest["schema_version"] = 2
    manifest["document"] = {
        "path": path,
        "generation": generation,
        "byte_digest": digest,
        "updated_at": updated_at,
        "title": str(state["title"]),
        "purpose": str(state["purpose"]),
        "status": "finalized",
        "needs_resolution": bool(state["needs_resolution"]),
        "latest_artifact_id": artifact_id,
        "source_artifact_ids": [artifact_id],
    }
    manifest["runtime"] = {
        "active_route": path,
        "state_revision": case_digest(
            "case-runtime",
            {"case_id": case_id, "path": path, "generation": generation, "at": updated_at},
        ),
    }
    outputs[path] = Output(rendered.encode("utf-8"))
    return validate_case_manifest(manifest)


def _upgrade_legacy_case_manifest(
    root: Path,
    manifest: dict[str, object],
    *,
    title: str,
    outputs: dict[str, Output],
) -> dict[str, object]:
    manifest = validate_case_manifest(manifest, migration_read=True)
    case_id = str(manifest["case_id"])
    path = case_live_document_path(case_id)
    represented_live = any(str(row["path"]) == path for row in manifest["artifacts"].values())
    if safe_read_bytes(root, path, optional=True) is not None and not represented_live:
        fail("legacy project has an unmanaged live.md collision", category="INDETERMINATE")
    state = _read_case_live_state(root, manifest, fallback_title=title)
    kinds = {
        case_live_purpose(_artifact_kind_from_row(row))
        for row in manifest["artifacts"].values()
    }
    kinds.discard("task")
    purpose = next(iter(kinds)) if len(kinds) == 1 else "task"
    updated_at = max(
        [str(row["created_at"]) for row in manifest["artifacts"].values()]
        or [str(manifest["created_at"])],
    )
    rendered = render_case_live_document(
        case_id=case_id,
        title=title,
        purpose=purpose,
        status="finalized" if manifest["status"] == "closed" else "active",
        generation=1,
        updated_at=updated_at,
        needs_resolution=bool(state["needs_resolution"]),
        sections=dict(state["sections"]),
    )
    source_ids = [str(item) for item in manifest["artifacts"]]
    source_paths = {str(row["path"]) for row in manifest["artifacts"].values()}
    source_digest = case_digest("project-upgrade-live-sources", source_ids)
    live_kind = case_live_artifact_kind(
        purpose,
        closed=manifest["status"] == "closed",
        has_claims=bool(manifest["claims"]),
    )
    role, subtype = _artifact_role(live_kind)
    envelope = {
        "role": role,
        "subtype": subtype,
        "case_id": case_id,
        "claim_ids": [],
        "consumer": "teamwork-project-upgrade",
        "source_revision": source_digest,
        "immutable": True,
    }
    artifact_id = artifact_id_for_case(live_kind, envelope, rendered)
    digest = artifact_digest(path, rendered)
    promoted = dict(manifest)
    promoted["schema_version"] = 2
    promoted["document"] = None
    promoted["artifacts"] = {}
    promoted["history"] = []
    promoted["references"] = []
    promoted["migration_sources"] = []
    promoted = validate_case_manifest(promoted)
    promoted = _case_add_artifact(
        promoted,
        kind=live_kind,
        path=path,
        artifact_id=artifact_id,
        digest=digest,
        updated_at=updated_at,
        source_revision=source_digest,
        consumer="teamwork-project-upgrade",
        allow_document_staging=True,
    )
    promoted = dict(promoted)
    claims = {}
    for claim_id, raw_claim in promoted["claims"].items():
        claim = dict(raw_claim)
        claim["head_artifact_id"] = artifact_id
        claim["head_digest"] = digest
        claims[claim_id] = claim
    promoted["claims"] = claims
    promoted["document"] = {
        "path": path,
        "generation": 1,
        "byte_digest": digest,
        "updated_at": updated_at,
        "title": title,
        "purpose": purpose,
        "status": "finalized" if promoted["status"] == "closed" else "active",
        "needs_resolution": bool(state["needs_resolution"]),
        "latest_artifact_id": artifact_id,
        "source_artifact_ids": [artifact_id],
    }
    promoted["runtime"] = {
        "active_route": path,
        "state_revision": case_digest(
            "case-runtime",
            {"case_id": case_id, "path": path, "generation": 1, "at": updated_at},
        ),
    }
    for source_path in source_paths:
        if source_path != path:
            outputs[source_path] = Output(None)
    outputs[path] = Output(rendered.encode("utf-8"))
    return validate_case_manifest(promoted)


def case_schema(operation: str) -> dict[str, object]:
    case_operations = {"create", "update", "collaborate-upsert", "accept-decision", "evidence-add", "research-add", "debug-add", "init-result", "update-result", "native-result", "plan-upsert", "plan-review-add", "review-add", "code-review-add", "repair-return", "result-add", "goal-acquire", "goal-update", "goal-transfer", "goal-close", "close"}
    if operation not in case_operations:
        fail("case schema operation is invalid")
    request: dict[str, object] = {"schema_version": 2, "operation": operation, "expected_revision": "<revision from case-inspect>", "updated_at": "2026-07-30T00:00:00+00:00"}
    if operation == "create":
        request.update({"case_seed": "<64 lowercase hex seed>", "title": "Case title", "task_key": "task-key", "aliases": []})
        request["initial_phase"] = "collaborating"
    else:
        request.update({"case_id": "c-" + "0" * 64, "expected_manifest_revision": "<manifest revision from case-inspect>"})
    if operation in CASE_OPERATION_ARTIFACT_CONTRACTS:
        request.update({"source_digest": "0" * 64, "body": "Markdown body"})
        kind, consumer = CASE_OPERATION_ARTIFACT_CONTRACTS[operation]
        request.update({"kind": kind, "consumer": consumer})
    if operation in {"review-add", "code-review-add", "plan-review-add"}:
        request.update({"candidate_identity": "stable candidate identity", "delta": False})
    if operation in {"goal-acquire", "goal-update"}:
        request.update({"claim_seed": "<64 lowercase hex seed>", "owner": "Goal"})
    if operation == "goal-transfer":
        request.update({"artifact_id": "a-" + "0" * 64, "new_case_id": "c-" + "1" * 64, "new_expected_manifest_revision": "<target manifest revision>"})
    if operation == "goal-close":
        request["artifact_id"] = "a-" + "0" * 64
    if operation == "close":
        request["closed_at"] = "2026-07-30T00:00:00+00:00"
    return request


def normalize_case_request(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        fail("case request must be an object")
    operation = value.get("operation")
    case_operations = {"create", "update", "collaborate-upsert", "accept-decision", "evidence-add", "research-add", "debug-add", "init-result", "update-result", "native-result", "plan-upsert", "plan-review-add", "review-add", "code-review-add", "repair-return", "result-add", "goal-acquire", "goal-update", "goal-transfer", "goal-close", "close"}
    if value.get("schema_version") != 2 or operation not in case_operations:
        fail("case request has an unsupported schema or operation")
    result: dict[str, object] = {
        "operation": operation,
        "expected_revision": _hex64(value.get("expected_revision"), "expected_revision"),
        "updated_at": _iso(value.get("updated_at"), "updated_at"),
    }
    if operation == "create":
        aliases = require_text_list(value.get("aliases", []), "case aliases", maximum=CASE_CAPS["aliases"])
        for alias in aliases:
            require_slug(alias, "case alias")
        result.update({
            "case_id": case_id_from_seed(value.get("case_seed")),
            "case_seed": _hex64(value.get("case_seed"), "case_seed"),
            "title": require_text(value.get("title"), "case title", maximum=200),
            "task_key": _task_key(value.get("task_key")),
            "aliases": sorted(aliases),
            "initial_phase": value.get("initial_phase", "collaborating"),
        })
        if result["initial_phase"] not in {"collaborating", "collecting", "planned", "executing"}:
            fail("case create initial_phase must be collaborating, collecting, planned, or executing")
        return result
    result["case_id"] = _case_id(value.get("case_id"))
    result["expected_manifest_revision"] = _hex64(value.get("expected_manifest_revision"), "expected_manifest_revision")
    if operation == "update":
        if "title" in value:
            result["title"] = require_text(value.get("title"), "case title", maximum=200)
        if "aliases" in value:
            aliases = require_text_list(value.get("aliases"), "case aliases", maximum=CASE_CAPS["aliases"])
            for alias in aliases:
                require_slug(alias, "case alias")
            result["aliases"] = sorted(aliases)
        if "phase" in value:
            phase = value.get("phase")
            if phase not in CASE_PHASES:
                fail("case phase is invalid")
            result["phase"] = phase
    if operation in CASE_OPERATION_ARTIFACT_CONTRACTS:
        result["source_digest"] = _hex64(value.get("source_digest"), "source_digest")
        result["body"] = require_markdown_body(value.get("body"), "case artifact body")
        expected_kind, expected_consumer = CASE_OPERATION_ARTIFACT_CONTRACTS[str(operation)]
        kind = value.get("kind", expected_kind)
        if kind != expected_kind:
            fail(f"{operation} kind must be {expected_kind}")
        consumer = value.get("consumer", expected_consumer)
        if consumer != expected_consumer:
            fail(f"{operation} consumer must be {expected_consumer}")
        result["kind"] = kind
        result["consumer"] = consumer
    if operation in {"review-add", "code-review-add", "plan-review-add"}:
        result["candidate_identity"] = require_text(
            value.get("candidate_identity", "current candidate"),
            "candidate_identity",
            maximum=1000,
        )
        result["delta"] = bool(value.get("delta", False))
    if operation in {"goal-acquire", "goal-update"}:
        result["claim_id"] = claim_id_from_seed(value.get("claim_seed", "00" * 32))
        result["owner"] = require_text(value.get("owner"), "claim owner", maximum=200)
    if operation == "goal-transfer":
        result["artifact_id"] = _artifact_id(value.get("artifact_id"))
        result["new_case_id"] = _case_id(value.get("new_case_id"))
        result["new_expected_manifest_revision"] = _hex64(value.get("new_expected_manifest_revision"), "new_expected_manifest_revision")
    if operation == "goal-close":
        result["artifact_id"] = _artifact_id(value.get("artifact_id"))
    if operation == "close":
        result["closed_at"] = _iso(value.get("closed_at"), "closed_at")
    return result


def _prune_case_aliases_to_hot(index: dict[str, object]) -> dict[str, object]:
    index = dict(index)
    hot_case_ids = {
        str(row["case_id"])
        for row in [*index["active_cases"], *index["recent_cases"]]
    }
    index["aliases"] = {
        alias: row
        for alias, row in index["aliases"].items()
        if str(row["target_id"]) in hot_case_ids
    }
    return validate_case_index(index)


def _set_case_phase(
    index: dict[str, object],
    manifest: dict[str, object],
    phase: str,
    updated_at: str,
    *,
    closed_at: str | None = None,
    preserve_runtime: bool = False,
) -> tuple[dict[str, object], dict[str, object]]:
    current = str(manifest["status"])
    if phase not in CASE_TRANSITIONS[current]:
        fail(f"invalid case lifecycle transition {current} -> {phase}")
    manifest = dict(manifest)
    manifest["status"] = phase
    manifest["closed_at"] = closed_at if phase == "closed" else None
    active_route = case_manifest_path(str(manifest["case_id"]))
    if preserve_runtime and isinstance(manifest.get("runtime"), dict):
        active_route = checked_relative(manifest["runtime"].get("active_route"), "runtime.active_route")
    manifest["runtime"] = {
        "active_route": active_route,
        "state_revision": case_digest("case-runtime", {"case_id": manifest["case_id"], "phase": phase, "active_route": active_route, "at": updated_at}),
    }
    manifest = validate_case_manifest(manifest)
    index = dict(index)
    active = list(index["active_cases"])
    if phase == "closed":
        active = [row for row in active if row["case_id"] != manifest["case_id"]]
        result_artifacts = [
            (artifact_id, row)
            for artifact_id, row in manifest["artifacts"].items()
            if row["role"] == "result"
        ]
        if not result_artifacts:
            fail("case close requires a terminal result artifact")
        result_artifact_id, result_artifact = sorted(result_artifacts, key=lambda item: str(item[1]["created_at"]))[-1]
        recent = [
            *index["recent_cases"],
            {
                "case_id": manifest["case_id"],
                "manifest_path": case_manifest_path(str(manifest["case_id"])),
                "closed_at": closed_at or updated_at,
                "result_artifact_id": result_artifact_id,
                "result_digest": result_artifact["byte_digest"],
            },
        ]
        index["recent_cases"] = sorted(recent, key=lambda row: (str(row["closed_at"]), str(row["case_id"])), reverse=True)[:CASE_CAPS["recent_cases"]]
    else:
        matches = [position for position, row in enumerate(active) if row["case_id"] == manifest["case_id"]]
        if len(matches) != 1:
            fail("case is not active in root index")
        active[matches[0]] = {
            "case_id": manifest["case_id"],
            "manifest_path": case_manifest_path(str(manifest["case_id"])),
            "manifest_revision": case_manifest_revision(manifest),
            "phase": phase,
            "task_key": active[matches[0]]["task_key"],
        }
    index["active_cases"] = active
    return _prune_case_aliases_to_hot(index), manifest


def _sync_case_claim_heads(index: dict[str, object], manifest: dict[str, object], updated_at: str) -> dict[str, object]:
    index = dict(index)
    case_id = str(manifest["case_id"])
    heads = {
        claim_id: row
        for claim_id, row in index["claim_heads"].items()
        if str(row["case_id"]) != case_id
    }
    for claim_id, claim in manifest["claims"].items():
        if claim["status"] != "active":
            continue
        artifact_id = str(claim["head_artifact_id"])
        artifact = manifest["artifacts"].get(artifact_id)
        if not isinstance(artifact, dict):
            fail("active claim head is missing from the current live document")
        heads[str(claim_id)] = {
            "case_id": case_id,
            "artifact_id": artifact_id,
            "artifact_digest": artifact["byte_digest"],
            "claim_revision": case_digest(
                "claim-revision",
                {"case_id": case_id, "claim_id": claim_id, "artifact_digest": artifact["byte_digest"], "at": updated_at},
            ),
            "status": "active",
        }
    index["claim_heads"] = heads
    return validate_case_index(index)


def _case_add_artifact(
    manifest: dict[str, object],
    *,
    kind: str,
    path: str,
    artifact_id: str,
    digest: str,
    updated_at: str,
    source_revision: str,
    consumer: str = "teamwork",
    allow_document_staging: bool = False,
) -> dict[str, object]:
    role = kind
    subtype = kind
    if kind.startswith("history-"):
        role = "history"
        subtype = kind.removeprefix("history-")
    elif kind in {"review", "review-delta"}:
        role = "review"
        subtype = kind
    elif kind in CASE_EVIDENCE_KINDS:
        role = "evidence"
        subtype = kind
    artifacts = dict(manifest["artifacts"])
    history = list(manifest["history"])
    if artifact_id in artifacts:
        fail("case artifact id already exists")
    for prior_id, row in artifacts.items():
        if row["path"] == path:
            history.append({
                "artifact_id": prior_id,
                "role": row["role"],
                "superseded_by": artifact_id,
                "retained_reason": "superseded",
                "recorded_at": updated_at,
            })
    artifacts[artifact_id] = {
        "role": role,
        "subtype": subtype,
        "path": path,
        "envelope_digest": artifact_envelope_digest({
            "schema_version": 1,
            "role": role,
            "subtype": subtype,
            "case_id": manifest["case_id"],
            "claim_ids": [],
            "consumer": consumer,
            "source_revision": source_revision,
            "immutable": True,
        }),
        "byte_digest": digest,
        "created_at": updated_at,
        "immutable": True,
        "consumer": consumer,
        "source_revision": source_revision,
    }
    manifest = dict(manifest)
    manifest["artifacts"] = artifacts
    manifest["history"] = history
    manifest["runtime"] = {
        "active_route": path,
        "state_revision": case_digest("case-runtime", {"case_id": manifest["case_id"], "path": path, "at": updated_at}),
    }
    return validate_case_manifest(manifest, migration_read=allow_document_staging)


def _case_singleton_history_path(case_id: str, artifact_id: str, role: object, *, live_document: bool = False) -> str:
    role_slug = require_slug(role, "singleton artifact role")
    segment = "live" if live_document or role_slug in CASE_LIVE_KINDS else role_slug
    return f"{case_base(case_id)}/history/{segment}/{_artifact_id(artifact_id)}.md"


def _relocate_prior_singleton_artifacts(
    root: Path,
    manifest: dict[str, object],
    *,
    singleton_path: str,
    superseded_by: str,
    updated_at: str,
    outputs: dict[str, Output],
) -> dict[str, object]:
    artifacts = dict(manifest["artifacts"])
    history = list(manifest["history"])
    relocated = False
    for prior_id, row in list(artifacts.items()):
        if row["path"] != singleton_path:
            continue
        prior_bytes = safe_read_bytes(root, singleton_path)
        assert prior_bytes is not None
        if hashlib.sha256(prior_bytes).hexdigest() != row["byte_digest"]:
            fail("singleton case artifact no longer matches its immutable manifest record", category="INDETERMINATE")
        archived_path = _case_singleton_history_path(
            str(manifest["case_id"]),
            prior_id,
            row["role"],
            live_document=singleton_path == case_live_document_path(str(manifest["case_id"])),
        )
        if safe_read_bytes(root, archived_path, optional=True) is not None or archived_path in outputs:
            fail("singleton case artifact history path already exists", category="INDETERMINATE")
        mode = _mode_of(root, singleton_path)
        outputs[archived_path] = Output(prior_bytes, 0o600 if mode is None else mode)
        relocated_row = dict(row)
        relocated_row["path"] = archived_path
        artifacts[prior_id] = relocated_row
        history.append({
            "artifact_id": prior_id,
            "role": row["role"],
            "superseded_by": superseded_by,
            "retained_reason": "superseded",
            "recorded_at": updated_at,
        })
        relocated = True
    if not relocated:
        return manifest
    relocated_manifest = dict(manifest)
    relocated_manifest["artifacts"] = artifacts
    relocated_manifest["history"] = history
    return validate_case_manifest(relocated_manifest)


def _write_case_index_and_manifest_outputs(index: dict[str, object], manifests: list[dict[str, object]], outputs: dict[str, Output]) -> None:
    refreshed = validate_case_index(index)
    for manifest in manifests:
        manifest = validate_case_manifest(manifest)
        manifest_revision = case_manifest_revision(manifest)
        for position, row in enumerate(refreshed["active_cases"]):
            if row["case_id"] == manifest["case_id"]:
                refreshed["active_cases"][position] = dict(row)
                refreshed["active_cases"][position]["manifest_revision"] = manifest_revision
        for alias, row in list(refreshed["aliases"].items()):
            if row["target_id"] == manifest["case_id"]:
                updated = dict(row)
                updated["manifest_revision"] = manifest_revision
                refreshed["aliases"][alias] = updated
        outputs[case_manifest_path(str(manifest["case_id"]))] = Output(serialize_case_manifest(manifest).encode("utf-8"))
    outputs[INDEX_PATH] = Output(serialize_case_index(refreshed).encode("utf-8"))


def apply_case(root: Path, raw_request: dict[str, object]) -> dict[str, object]:
    request = normalize_case_request(raw_request)
    with locked_memory(root):
        ensure_no_migration_intermediate(root)
        recover_transaction(root, CASE_TRANSACTION_MARKER, CASE_PREFIXES, "case")
        if detect_teamwork_memory_schema(root) != "case-v3":
            fail("case operations require current case-v3 memory; run explicit project migration")
        index_text, index = read_case_index(root)
        if request["expected_revision"] != cases_revision(root, index_text, index):
            fail("stale case expected_revision; run case-inspect again")
        index = _prune_case_aliases_to_hot(index)
        outputs: dict[str, Output] = {}
        created: list[str] = []
        operation = str(request["operation"])
        result_case_id: str
        result_manifest: dict[str, object]
        changed: set[str] = set()
        if operation == "create":
            case_id = str(request["case_id"])
            result_case_id = case_id
            if safe_read_bytes(root, case_manifest_path(case_id), optional=True) is not None:
                fail("derived case manifest already exists")
            if any(row["task_key"] == request["task_key"] for row in index["active_cases"]):
                fail("active case task_key already exists")
            for alias in request["aliases"]:
                if alias in index["aliases"]:
                    fail("case alias already exists")
            initial_phase = str(request["initial_phase"])
            seed_hex = str(request["case_seed"])
            manifest = validate_case_manifest({
                "schema_version": 2,
                "case_id": case_id,
                "case_seed_b64": base64.b64encode(bytes.fromhex(seed_hex)).decode("ascii"),
                "created_at": request["updated_at"],
                "closed_at": None,
                "status": initial_phase,
                "claims": {},
                "artifacts": {},
                "history": [],
                "references": [],
                "runtime": {
                    "active_route": case_manifest_path(case_id),
                    "state_revision": case_digest("case-runtime", {"case_id": case_id, "phase": initial_phase, "at": request["updated_at"]}),
                },
                "migration_sources": [],
                "document": None,
            })
            index["active_cases"].append({"case_id": case_id, "manifest_path": case_manifest_path(case_id), "manifest_revision": case_manifest_revision(manifest), "phase": initial_phase, "task_key": request["task_key"]})
            for alias in request["aliases"]:
                index["aliases"][str(alias)] = {
                    "target_type": "case",
                    "target_id": case_id,
                    "manifest_path": case_manifest_path(case_id),
                    "manifest_revision": case_manifest_revision(manifest),
                }
            result_manifest = manifest
            _write_case_index_and_manifest_outputs(index, [manifest], outputs)
        else:
            case_id = str(request["case_id"])
            result_case_id = case_id
            _, manifest = read_case_manifest(root, case_id)
            if request["expected_manifest_revision"] != case_manifest_revision(manifest):
                fail("stale case manifest revision; run case-inspect again")
            if operation == "update":
                manifest = dict(manifest)
                active_row = next((row for row in index["active_cases"] if row["case_id"] == case_id), None)
                if active_row is None:
                    fail("case is not active in root index")
                if "title" in request:
                    pass
                if "aliases" in request:
                    old_aliases = {alias for alias, row in index["aliases"].items() if row["target_id"] == case_id}
                    new_aliases = set(str(alias) for alias in request["aliases"])
                    for alias in new_aliases:
                        owner = index["aliases"].get(alias)
                        if owner is not None and owner["target_id"] != case_id:
                            fail("case alias conflict")
                    for alias in old_aliases - new_aliases:
                        index["aliases"].pop(alias, None)
                    for alias in new_aliases:
                        index["aliases"][alias] = {
                            "target_type": "case",
                            "target_id": case_id,
                            "manifest_path": case_manifest_path(case_id),
                            "manifest_revision": case_manifest_revision(manifest),
                        }
                phase = str(request.get("phase", manifest["status"]))
                index, manifest = _set_case_phase(index, validate_case_manifest(manifest), phase, str(request["updated_at"]))
                result_manifest = manifest
            elif operation in {"collaborate-upsert", "accept-decision", "evidence-add", "research-add", "debug-add", "init-result", "update-result", "native-result", "plan-upsert", "plan-review-add", "review-add", "code-review-add", "result-add", "goal-acquire", "goal-update"}:
                allowed = {
                    "collaborate-upsert": CASE_ACTIVE_PHASES,
                    "accept-decision": {"collaborating", "planned"},
                    "evidence-add": {"collecting", "planned", "executing", "reviewing"},
                    "research-add": {"collecting", "planned", "executing", "reviewing"},
                    "debug-add": {"collecting", "planned", "executing", "reviewing"},
                    "init-result": {"collecting", "executing"},
                    "update-result": {"collecting", "executing"},
                    "native-result": {"collecting", "executing"},
                    "plan-upsert": {"planned", "executing"},
                    "plan-review-add": {"planned"},
                    "review-add": {"executing", "reviewing"},
                    "code-review-add": {"executing", "reviewing"},
                    "result-add": {"executing", "reviewing"},
                    "goal-acquire": {"executing"},
                    "goal-update": {"executing"},
                }[operation]
                if manifest["status"] not in allowed:
                    fail(f"{operation} is not allowed while case is {manifest['status']}")
                kind = str(request["kind"])
                consumer = str(request["consumer"])
                body = str(request["body"])
                source_digest = str(request["source_digest"])
                active_row = next((row for row in index["active_cases"] if row["case_id"] == case_id), None)
                if active_row is None:
                    fail("case is not active in root index")
                title = str(active_row["task_key"]).replace("-", " ").title()
                manifest_kind = kind
                if operation in {"review-add", "code-review-add", "plan-review-add"}:
                    manifest_kind = "review-delta" if request["delta"] else "review"
                manifest, artifact_id, digest = _install_case_live_revision(
                    root,
                    manifest,
                    title=title,
                    kind=manifest_kind,
                    body=body,
                    source_digest=source_digest,
                    consumer=consumer,
                    updated_at=str(request["updated_at"]),
                    outputs=outputs,
                )
                if operation == "plan-upsert":
                    index, manifest = _set_case_phase(index, manifest, "executing", str(request["updated_at"]), preserve_runtime=True)
                elif operation == "plan-review-add":
                    index, manifest = _set_case_phase(index, manifest, "planned", str(request["updated_at"]), preserve_runtime=True)
                elif operation in {"review-add", "code-review-add"}:
                    index, manifest = _set_case_phase(index, manifest, "reviewing", str(request["updated_at"]), preserve_runtime=True)
                else:
                    index, manifest = _set_case_phase(index, manifest, str(manifest["status"]), str(request["updated_at"]), preserve_runtime=True)
                if operation in {"goal-acquire", "goal-update"}:
                    descriptor_digest = case_digest("claim-descriptor", {"case_id": case_id, "claim_id": request["claim_id"], "owner": request["owner"]})
                    claim = {
                        "descriptor_version": 1,
                        "descriptor_digest": descriptor_digest,
                        "status": "active",
                        "acquired_at": request["updated_at"],
                        "released_at": None,
                        "head_artifact_id": artifact_id,
                        "head_digest": digest,
                    }
                    manifest = dict(manifest)
                    manifest["claims"] = {**manifest["claims"], str(request["claim_id"]): claim}
                    claim_revision = case_digest("claim-revision", {"case_id": case_id, "claim_id": request["claim_id"], "artifact_digest": digest})
                    index["claim_heads"][str(request["claim_id"])] = {"case_id": case_id, "artifact_id": artifact_id, "artifact_digest": digest, "claim_revision": claim_revision, "status": "active"}
                    manifest = validate_case_manifest(manifest)
                index = _sync_case_claim_heads(index, manifest, str(request["updated_at"]))
                result_manifest = manifest
            elif operation == "repair-return":
                if manifest["status"] != "reviewing":
                    fail("repair-return requires reviewing phase")
                index, manifest = _set_case_phase(
                    index,
                    manifest,
                    "executing",
                    str(request["updated_at"]),
                    preserve_runtime=True,
                )
                result_manifest = manifest
            elif operation == "goal-transfer":
                new_case_id = str(request["new_case_id"])
                _, new_manifest = read_case_manifest(root, new_case_id)
                if request["new_expected_manifest_revision"] != case_manifest_revision(new_manifest):
                    fail("stale target manifest revision; run case-inspect again")
                artifact_id = str(request["artifact_id"])
                matches = [(claim_id, claim) for claim_id, claim in manifest["claims"].items() if claim["head_artifact_id"] == artifact_id and claim["status"] == "active"]
                if len(matches) != 1:
                    fail("goal transfer requires exactly one active source claim")
                claim_id, prior_raw = matches[0]
                prior = dict(prior_raw)
                old_claims = dict(manifest["claims"])
                released_claim = dict(prior)
                released_claim["status"] = "released"
                released_claim["released_at"] = request["updated_at"]
                old_claims[claim_id] = released_claim
                new_claim = dict(prior)
                new_claim["acquired_at"] = request["updated_at"]
                new_claim["released_at"] = None
                manifest = dict(manifest)
                manifest["claims"] = old_claims
                new_manifest = dict(new_manifest)
                new_manifest["claims"] = {**new_manifest["claims"], claim_id: new_claim}
                manifest = validate_case_manifest(manifest)
                new_manifest = validate_case_manifest(new_manifest)
                index["claim_heads"][claim_id] = {"case_id": new_case_id, "artifact_id": artifact_id, "artifact_digest": new_claim["head_digest"], "claim_revision": case_digest("claim-transfer", {"claim_id": claim_id, "from": case_id, "to": new_case_id, "at": request["updated_at"]}), "status": "active"}
                index, manifest = _set_case_phase(index, manifest, str(manifest["status"]), str(request["updated_at"]))
                index, new_manifest = _set_case_phase(index, new_manifest, str(new_manifest["status"]), str(request["updated_at"]))
                _write_case_index_and_manifest_outputs(index, [manifest, new_manifest], outputs)
                result_manifest = manifest
            elif operation == "goal-close":
                artifact_id = str(request["artifact_id"])
                manifest = dict(manifest)
                claims = {}
                for claim_id, claim in manifest["claims"].items():
                    next_claim = dict(claim)
                    if next_claim["head_artifact_id"] == artifact_id and next_claim["status"] == "active":
                        next_claim["status"] = "released"
                        next_claim["released_at"] = request["updated_at"]
                    claims[claim_id] = next_claim
                manifest["claims"] = claims
                index["claim_heads"] = {claim_id: head for claim_id, head in index["claim_heads"].items() if not (head["case_id"] == case_id and head["artifact_id"] == artifact_id)}
                index, manifest = _set_case_phase(index, validate_case_manifest(manifest), str(manifest["status"]), str(request["updated_at"]))
                result_manifest = manifest
            else:
                active_row = next((row for row in index["active_cases"] if row["case_id"] == case_id), None)
                if active_row is None:
                    fail("case is not active in root index")
                title = str(active_row["task_key"]).replace("-", " ").title()
                result_manifest = _finalize_case_live_document(
                    root,
                    manifest,
                    title=title,
                    updated_at=str(request["updated_at"]),
                    outputs=outputs,
                )
                index, result_manifest = _set_case_phase(
                    index,
                    result_manifest,
                    "closed",
                    str(request["updated_at"]),
                    closed_at=str(request["closed_at"]),
                    preserve_runtime=True,
                )
                index = _sync_case_claim_heads(index, result_manifest, str(request["updated_at"]))
            if not outputs or case_manifest_path(case_id) not in outputs:
                _write_case_index_and_manifest_outputs(index, [result_manifest], outputs)
        for path in outputs:
            ensure_directory(root, PurePosixPath(path).parent.as_posix(), created=created)
            changed.add(path)
        apply_transaction(root, kind="case", marker=CASE_TRANSACTION_MARKER, prefixes=CASE_PREFIXES, outputs=outputs, created_directories=created)
        final_index_text, final_index = read_case_index(root)
        _, final_manifest = read_case_manifest(root, result_case_id)
        return {"schema_mode": "case-v3", "case_id": result_case_id, "manifest_path": case_manifest_path(result_case_id), "manifest_revision": case_manifest_revision(final_manifest), "revision": cases_revision(root, final_index_text, final_index), "changed_paths": sorted(changed)}


def writer_schema(operation: str) -> dict[str, object]:
    if operation not in {"start", "update", "finalize"}:
        fail("writer schema operation must be start, update, or finalize")
    request: dict[str, object] = {
        "schema_version": 1,
        "operation": operation,
        "updated_at": "2026-08-06T00:00:00Z",
        "purpose": "research",
        "section": "Evidence",
        "body": "Reusable Markdown content",
    }
    if operation == "start":
        request.update({
            "case_seed": "<64 lowercase hex seed>",
            "task_key": "task-key",
            "title": "Task title",
            "aliases": [],
        })
    else:
        request.update({
            "case_id": "c-" + "0" * 64,
            "expected_generation": 1,
        })
    return request


def normalize_writer_request(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        fail("writer request has an unsupported schema")
    operation = value.get("operation")
    if operation not in {"start", "update", "finalize"}:
        fail("writer request operation is invalid")
    purpose = value.get("purpose")
    if purpose not in CASE_LIVE_PURPOSES - {"task"}:
        fail("writer purpose is invalid")
    section = value.get("section")
    if section not in set(CASE_LIVE_SECTIONS) - {"Migration Appendix"}:
        fail("writer section is invalid")
    body = require_markdown_body(value.get("body"), "writer body")
    result: dict[str, object] = {
        "operation": operation,
        "purpose": purpose,
        "section": section,
        "body": body,
        "updated_at": _iso(value.get("updated_at"), "writer updated_at"),
    }
    if operation == "start":
        aliases = require_text_list(value.get("aliases", []), "writer aliases", maximum=CASE_CAPS["aliases"])
        for alias in aliases:
            require_slug(alias, "writer alias")
        result.update({
            "case_seed": _hex64(value.get("case_seed"), "writer case_seed"),
            "case_id": case_id_from_seed(value.get("case_seed")),
            "task_key": _task_key(value.get("task_key")),
            "title": require_text(value.get("title"), "writer title", maximum=200),
            "aliases": sorted(aliases),
        })
    else:
        generation = value.get("expected_generation")
        if not isinstance(generation, int) or isinstance(generation, bool) or generation < 0:
            fail("writer expected_generation must be a non-negative integer")
        result.update({
            "case_id": _case_id(value.get("case_id")),
            "expected_generation": generation,
        })
    return result


def _writer_kind(purpose: str, section: str) -> str:
    if section == "Purpose State":
        return "goal" if purpose == "goal" else "collaborate"
    if section == "Decisions":
        return "decision"
    if section == "Plan":
        return "plan"
    if section == "Review":
        return "review"
    if section == "Outcome":
        return "result"
    if purpose in {"research", "debug", "init", "update"}:
        return purpose
    return "evidence"


def inspect_writer_documents(root: Path) -> dict[str, object]:
    inspected = inspect_cases(root)
    documents = []
    for row in inspected.get("active_cases", []):
        manifest = row["state"]
        document = manifest.get("document") if manifest.get("schema_version") == 2 else None
        documents.append({
            "case_id": manifest["case_id"],
            "manifest_revision": row["revision"],
            "phase": manifest["status"],
            "document": document,
        })
    return {
        "schema_mode": inspected["schema_mode"],
        "documents": documents,
        "recovered": inspected.get("recovered"),
    }


def apply_writer(root: Path, raw_request: dict[str, object]) -> dict[str, object]:
    request = normalize_writer_request(raw_request)
    with locked_memory(root):
        ensure_no_migration_intermediate(root)
        recover_transaction(root, CASE_TRANSACTION_MARKER, CASE_PREFIXES, "case")
        if detect_teamwork_memory_schema(root) != "case-v3":
            fail("Writer requires current case-v3 memory; run explicit project migration")
        _, index = read_case_index(root)
        index = _prune_case_aliases_to_hot(index)
        outputs: dict[str, Output] = {}
        created: list[str] = []
        operation = str(request["operation"])
        kind = _writer_kind(str(request["purpose"]), str(request["section"]))
        if operation == "start":
            case_id = str(request["case_id"])
            if safe_read_bytes(root, case_manifest_path(case_id), optional=True) is not None:
                fail("derived Writer case already exists")
            if any(row["task_key"] == request["task_key"] for row in index["active_cases"]):
                fail("active Writer task_key already exists")
            for alias in request["aliases"]:
                if alias in index["aliases"]:
                    fail("Writer alias already exists")
            phase = {
                "research": "collecting",
                "debug": "collecting",
                "plan": "planned",
                "review": "reviewing",
            }.get(str(request["purpose"]), "executing")
            manifest = validate_case_manifest({
                "schema_version": 2,
                "case_id": case_id,
                "case_seed_b64": base64.b64encode(bytes.fromhex(str(request["case_seed"]))).decode("ascii"),
                "created_at": request["updated_at"],
                "closed_at": None,
                "status": phase,
                "claims": {},
                "artifacts": {},
                "history": [],
                "references": [],
                "runtime": {
                    "active_route": case_manifest_path(case_id),
                    "state_revision": case_digest("case-runtime", {"case_id": case_id, "phase": phase, "at": request["updated_at"]}),
                },
                "migration_sources": [],
                "document": None,
            })
            manifest, _, _ = _install_case_live_revision(
                root,
                manifest,
                title=str(request["title"]),
                kind=kind,
                body=str(request["body"]),
                source_digest=case_digest("writer-content", str(request["body"])),
                consumer="teamwork-writer",
                updated_at=str(request["updated_at"]),
                outputs=outputs,
            )
            index = _sync_case_claim_heads(index, manifest, str(request["updated_at"]))
            index["active_cases"].append({
                "case_id": case_id,
                "manifest_path": case_manifest_path(case_id),
                "manifest_revision": case_manifest_revision(manifest),
                "phase": phase,
                "task_key": request["task_key"],
            })
            for alias in request["aliases"]:
                index["aliases"][str(alias)] = {
                    "target_type": "case",
                    "target_id": case_id,
                    "manifest_path": case_manifest_path(case_id),
                    "manifest_revision": case_manifest_revision(manifest),
                }
        else:
            case_id = str(request["case_id"])
            _, manifest = read_case_manifest(root, case_id)
            active_row = next((row for row in index["active_cases"] if row["case_id"] == case_id), None)
            if active_row is None:
                fail("Writer case is not active")
            document = manifest.get("document") if manifest.get("schema_version") == 2 else None
            generation = 0 if document is None else int(document["generation"])
            if generation != request["expected_generation"]:
                fail("stale Writer generation; inspect the live document again")
            title = str(active_row["task_key"]).replace("-", " ").title() if document is None else str(document["title"])
            manifest, _, _ = _install_case_live_revision(
                root,
                manifest,
                title=title,
                kind=kind,
                body=str(request["body"]),
                source_digest=case_digest("writer-content", str(request["body"])),
                consumer="teamwork-writer",
                updated_at=str(request["updated_at"]),
                outputs=outputs,
                finalize=operation == "finalize",
            )
            index = _sync_case_claim_heads(index, manifest, str(request["updated_at"]))
            if operation == "finalize":
                if kind != "result":
                    fail("Writer finalize requires the Outcome section")
                index, manifest = _set_case_phase(
                    index,
                    manifest,
                    "closed",
                    str(request["updated_at"]),
                    closed_at=str(request["updated_at"]),
                    preserve_runtime=True,
                )
            else:
                index, manifest = _set_case_phase(
                    index,
                    manifest,
                    str(manifest["status"]),
                    str(request["updated_at"]),
                    preserve_runtime=True,
                )
        _write_case_index_and_manifest_outputs(index, [manifest], outputs)
        for path in outputs:
            ensure_directory(root, PurePosixPath(path).parent.as_posix(), created=created)
        apply_transaction(
            root,
            kind="case",
            marker=CASE_TRANSACTION_MARKER,
            prefixes=CASE_PREFIXES,
            outputs=outputs,
            created_directories=created,
        )
        _, final_manifest = read_case_manifest(root, case_id)
        final_document = final_manifest.get("document")
        assert isinstance(final_document, dict)
        return {
            "schema_mode": "case-v3",
            "case_id": case_id,
            "path": final_document["path"],
            "generation": final_document["generation"],
            "status": final_document["status"],
            "needs_resolution": final_document["needs_resolution"],
            "changed_paths": sorted(outputs),
        }


def upgrade_project_documents(root: Path) -> dict[str, object]:
    """Atomically converge every project case directory to one live.md."""
    with locked_memory(root):
        ensure_no_migration_intermediate(root)
        recovered = recover_transaction(root, CASE_TRANSACTION_MARKER, CASE_PREFIXES, "case")
        mode = detect_teamwork_memory_schema(root, migration=True)
        if mode not in {"case-v2-legacy", "case-v3"}:
            fail("project document upgrade requires a schema-2 case project; legacy-v1 uses the full migration command")
        index_text = safe_read_text(root, INDEX_PATH)
        assert index_text is not None
        raw_index = _decode_json(index_text, "project case index")
        source_index = (
            validate_legacy_case_index(raw_index)
            if mode == "case-v2-legacy"
            else validate_case_index(raw_index)
        )
        index = dict(source_index)
        index["schema_version"] = 3
        index["migration"] = None
        index = validate_case_index(index)
        task_titles = {
            str(row["case_id"]): str(row["task_key"]).replace("-", " ").title()
            for row in source_index["active_cases"]
        }
        for alias, row in source_index["aliases"].items():
            task_titles.setdefault(str(row["target_id"]), str(alias).replace("-", " ").title())
        indexed_active = {str(row["case_id"]): row for row in source_index["active_cases"]}
        cases_root = root / "docs/teamwork/cases"
        case_directories: list[Path] = []
        if cases_root.exists():
            if not cases_root.is_dir() or cases_root.is_symlink():
                fail("project case directory is unsafe", category="INDETERMINATE")
            for candidate in sorted(cases_root.iterdir(), key=lambda item: item.name):
                info = candidate.lstat()
                if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
                    fail("project cases may contain only case directories", category="INDETERMINATE")
                _case_id(candidate.name)
                case_directories.append(candidate)
        elif any(
            source_index[field]
            for field in ("active_cases", "recent_cases", "aliases", "claim_heads")
        ):
            fail("project case directory is missing", category="INDETERMINATE")
        seen: set[str] = set()
        manifests: list[dict[str, object]] = []
        outputs: dict[str, Output] = {}
        created: list[str] = []
        changed_cases = 0
        for case_directory in case_directories:
            case_id = case_directory.name
            if case_id in seen:
                fail("project case tree contains duplicate case identities")
            seen.add(case_id)
            manifest_path = case_directory / "manifest.json"
            if not manifest_path.is_file() or manifest_path.is_symlink():
                fail("project case directory is missing a safe manifest.json", category="INDETERMINATE")
            manifest_text = safe_read_text(root, case_manifest_path(case_id))
            assert manifest_text is not None
            raw_manifest = _decode_json(manifest_text, "project case manifest")
            current_shaped = (
                isinstance(raw_manifest, dict)
                and raw_manifest.get("schema_version") == 2
                and isinstance(raw_manifest.get("document"), dict)
                and isinstance(raw_manifest.get("artifacts"), dict)
                and len(raw_manifest["artifacts"]) == 1
                and raw_manifest.get("history") == []
                and raw_manifest.get("references") == []
            )
            if current_shaped:
                manifest = validate_case_manifest(raw_manifest)
                promoted = manifest
            else:
                manifest = validate_case_manifest(raw_manifest, migration_read=True)
                promoted = _upgrade_legacy_case_manifest(
                    root,
                    manifest,
                    title=task_titles.get(case_id, f"Migrated Task {case_id[2:10]}"),
                    outputs=outputs,
                )
                changed_cases += 1
            if manifest["case_id"] != case_id:
                fail("project case manifest identity mismatch")
            active_row = indexed_active.get(case_id)
            if (
                mode == "case-v2-legacy"
                and active_row is not None
                and legacy_case_manifest_revision(manifest) != active_row["manifest_revision"]
            ):
                fail("legacy active case manifest revision mismatch")
            manifests.append(promoted)
            document = promoted.get("document")
            if isinstance(document, dict) and case_id in indexed_active:
                index = _sync_case_claim_heads(index, promoted, str(document["updated_at"]))
            if promoted["status"] == "closed" and isinstance(document, dict):
                live_id = str(promoted["document"]["latest_artifact_id"])
                live_digest = str(promoted["document"]["byte_digest"])
                index["recent_cases"] = [
                    {
                        **recent,
                        "result_artifact_id": live_id,
                        "result_digest": live_digest,
                    }
                    if recent["case_id"] == case_id else recent
                    for recent in index["recent_cases"]
                ]
            for existing in sorted(case_directory.rglob("*"), key=lambda item: item.as_posix()):
                info = existing.lstat()
                if stat.S_ISLNK(info.st_mode):
                    fail("project case migration refuses symlinked artifacts", category="INDETERMINATE")
                if stat.S_ISDIR(info.st_mode):
                    continue
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                    fail("project case migration found an unsafe artifact", category="INDETERMINATE")
                relative = existing.relative_to(root).as_posix()
                if relative not in {case_manifest_path(case_id), case_live_document_path(case_id)}:
                    outputs[relative] = Output(None)
        needs_write = mode == "case-v2-legacy" or changed_cases > 0 or bool(outputs) or index != source_index
        if not needs_write:
            validate_case_v3_tree_readonly(root)
            return {"mode": "case-v3", "migrated": False, "recovered": recovered, "changed_paths": []}
        _write_case_index_and_manifest_outputs(index, manifests, outputs)
        for path in outputs:
            ensure_directory(root, PurePosixPath(path).parent.as_posix(), created=created)
        apply_transaction(
            root,
            kind="case",
            marker=CASE_TRANSACTION_MARKER,
            prefixes=CASE_PREFIXES,
            outputs=outputs,
            created_directories=created,
        )
        for directory in sorted(
            (path for path in cases_root.rglob("*") if path.is_dir()),
            key=lambda item: len(item.parts),
            reverse=True,
        ):
            try:
                directory.rmdir()
            except OSError:
                pass
        validate_case_v3_tree_readonly(root)
        return {
            "mode": "case-v3",
            "migrated": True,
            "recovered": recovered,
            "cases": len(manifests),
            "changed_cases": changed_cases,
            "changed_paths": sorted(outputs),
        }


def migration_runtime_dir(migration_id: str) -> str:
    return f"{MIGRATION_RUNTIME_ROOT}/migrations/{_migration_id(migration_id)}"


def migration_marker(migration_id: str) -> str:
    return f"{migration_runtime_dir(migration_id)}/.transaction.json"


def migration_runtime_path(migration_id: str, name: str) -> str:
    checked_relative(name, "migration runtime relative path")
    return f"{migration_runtime_dir(migration_id)}/{name}"


def migration_archive_object_path(migration_id: str, digest: str) -> str:
    migration_id = _migration_id(migration_id)
    digest = _hex64(digest, "archive object digest")
    return f"{migration_runtime_dir(migration_id)}/backup/objects/sha256/{digest[:2]}/{digest}"


def migration_archive_manifest_path(migration_id: str) -> str:
    return f"{migration_runtime_dir(migration_id)}/backup/manifest.json"


def migration_json_output(value: object) -> Output:
    return Output((json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"))


def read_migration_json(root: Path, migration_id: str, name: str, *, optional: bool = False) -> dict[str, object] | None:
    raw = safe_read_text(root, migration_runtime_path(migration_id, name), optional=optional)
    if raw is None:
        return None
    value = _decode_json(raw, name)
    if not isinstance(value, dict):
        fail(f"migration runtime {name} must be an object", category="INDETERMINATE")
    return value


def _candidate_digest_bytes(logical_path: str, data: bytes) -> bytes:
    if logical_path == INDEX_PATH:
        value = _decode_json(data.decode("utf-8"), "candidate index")
        if not isinstance(value, dict):
            fail("candidate index must be an object", category="INDETERMINATE")
        value = validate_case_index(value)
        migration = value.get("migration")
        if isinstance(migration, dict):
            migration = dict(migration)
            migration["candidate_digest"] = "0" * 64
            migration["phase"] = "normalized"
            migration["report_digest"] = "0" * 64
            value = dict(value)
            value["migration"] = migration
        return canonical_json_bytes(value)
    if logical_path.endswith("/coverage.json"):
        value = _decode_json(data.decode("utf-8"), "candidate coverage")
        if not isinstance(value, dict):
            fail("candidate coverage must be an object", category="INDETERMINATE")
        if "candidate_digest" in value:
            value = dict(value)
            value["candidate_digest"] = "0" * 64
        return canonical_json_bytes(value)
    return data


def candidate_tree_digest_from_outputs(migration_id: str, outputs: dict[str, Output]) -> str:
    candidate_prefix = f"{migration_runtime_dir(migration_id)}/candidate/docs-teamwork/"
    coverage_path = migration_runtime_path(migration_id, "coverage.json")
    rows: list[dict[str, object]] = []
    for path, output in outputs.items():
        if output.data is None:
            continue
        if path.startswith(candidate_prefix):
            logical = "docs/teamwork/" + path.removeprefix(candidate_prefix)
        elif path == coverage_path:
            logical = coverage_path
        else:
            continue
        rows.append({"path": logical, "sha256": hashlib.sha256(_candidate_digest_bytes(logical, output.data)).hexdigest()})
    rows = sorted(rows, key=lambda row: str(row["path"]))
    return case_digest("candidate-tree-complete", rows)


def _candidate_tree_file_rows(root: Path, migration_id: str, tree_relative: str) -> list[dict[str, object]]:
    base = _safe_dir(root, tree_relative)
    assert base is not None
    rows: list[dict[str, object]] = []
    for path in sorted(base.rglob("*"), key=lambda item: item.relative_to(base).as_posix()):
        relative_tail = path.relative_to(base).as_posix()
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode):
            fail("candidate tree must not contain symlinks", category="INDETERMINATE")
        if stat.S_ISDIR(info.st_mode):
            continue
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            fail("candidate tree contains an unsafe file", category="INDETERMINATE")
        data = path.read_bytes()
        rows.append({"path": f"docs/teamwork/{relative_tail}", "sha256": hashlib.sha256(_candidate_digest_bytes(f"docs/teamwork/{relative_tail}", data)).hexdigest()})
    coverage_relative = migration_runtime_path(migration_id, "coverage.json")
    coverage_data = safe_read_bytes(root, coverage_relative)
    assert coverage_data is not None
    rows.append({"path": coverage_relative, "sha256": hashlib.sha256(_candidate_digest_bytes(coverage_relative, coverage_data)).hexdigest()})
    return sorted(rows, key=lambda row: str(row["path"]))


def candidate_tree_digest(root: Path, migration_id: str, tree_relative: str) -> str:
    return case_digest("candidate-tree-complete", _candidate_tree_file_rows(root, migration_id, tree_relative))


def verify_candidate_tree(root: Path, migration_id: str, tree_relative: str, expected_digest_raw: object) -> None:
    expected_digest = _hex64(expected_digest_raw, "candidate_digest")
    if candidate_tree_digest(root, migration_id, tree_relative) != expected_digest:
        fail("candidate tree digest mismatch", category="INDETERMINATE")
    index_path = f"{tree_relative}/index.json" if tree_relative != "docs/teamwork" else INDEX_PATH
    index = _read_json_relative(root, index_path, "candidate index")
    validate_case_index(index)
    coverage = read_migration_json(root, migration_id, "coverage.json")
    assert coverage is not None
    if coverage.get("candidate_digest") != expected_digest:
        fail("candidate coverage digest mismatch", category="INDETERMINATE")
    coverage_rows = coverage.get("coverage_rows")
    if not isinstance(coverage_rows, list):
        fail("candidate coverage rows are malformed", category="INDETERMINATE")
    coverage_by_source: dict[str, dict[str, object]] = {}
    for row in coverage_rows:
        if not isinstance(row, dict) or row.get("derived_terminal_result"):
            continue
        source_path = checked_relative(row.get("source_path"), "coverage source path")
        coverage_by_source[source_path] = row
        artifact_path = checked_relative(row.get("artifact_path"), "coverage artifact path")
        artifact_data = safe_read_bytes(root, artifact_path if tree_relative == "docs/teamwork" else f"{tree_relative}/{artifact_path.removeprefix('docs/teamwork/')}")
        if artifact_data is None:
            fail("candidate coverage artifact is missing", category="INDETERMINATE")
    case_rows = list(index.get("active_cases", [])) + list(index.get("recent_cases", []))
    for case_row in case_rows:
        if not isinstance(case_row, dict):
            fail("candidate index case row is malformed", category="INDETERMINATE")
        manifest_path = checked_relative(case_row.get("manifest_path"), "candidate manifest path")
        manifest_relative = manifest_path if tree_relative == "docs/teamwork" else f"{tree_relative}/{manifest_path.removeprefix('docs/teamwork/')}"
        manifest = _read_json_relative(root, manifest_relative, "candidate manifest")
        manifest = validate_case_manifest(manifest)
        artifacts = manifest["artifacts"]
        assert isinstance(artifacts, dict)
        for artifact_id, artifact in artifacts.items():
            assert isinstance(artifact, dict)
            artifact_path = str(artifact["path"])
            artifact_relative = artifact_path if tree_relative == "docs/teamwork" else f"{tree_relative}/{artifact_path.removeprefix('docs/teamwork/')}"
            artifact_data = safe_read_bytes(root, artifact_relative)
            if artifact_data is None or hashlib.sha256(canonical_text_bytes(artifact_data.decode("utf-8"))).hexdigest() != artifact["byte_digest"]:
                fail("candidate manifest artifact digest mismatch", category="INDETERMINATE")
        for source in manifest["migration_sources"]:
            assert isinstance(source, dict)
            coverage_row = coverage_by_source.get(str(source["source_path"]))
            if coverage_row is None or coverage_row.get("artifact_id") != source.get("artifact_id"):
                fail("candidate migration source coverage mismatch", category="INDETERMINATE")


MIGRATION_PHASE_RANK = {
    "collaborating": 0,
    "collecting": 1,
    "planned": 2,
    "executing": 3,
    "reviewing": 4,
}
MIGRATION_ACTIVE_PHASE_BY_SLOT = {
    "collaborate": "collaborating",
    "discussion": "collaborating",
    "design": "collecting",
    "plan": "planned",
    "progress": "executing",
    "goal": "executing",
    "current": "executing",
    "report": "reviewing",
    "results": "reviewing",
}
MIGRATION_PHASE_BY_KIND = {
    "collaborate": "collaborating",
    "discussion": "collaborating",
    "decision": "collaborating",
    "design": "collecting",
    "research": "collecting",
    "plan": "planned",
    "goal": "executing",
    "progress": "executing",
    "init": "executing",
    "update": "executing",
    "execution": "executing",
    "result": "executing",
    "debug": "reviewing",
    "review": "reviewing",
    "report": "reviewing",
}
MIGRATION_TERMINAL_STATUSES = {"historical", "superseded", "accepted"}
MIGRATION_SOURCE_MAX_BYTES = 256 * 1024


def _allowed_archive_only_binary_path(path: str) -> bool:
    pure = PurePosixPath(checked_relative(path, "archive-only binary path"))
    if pure.as_posix() == "docs/teamwork/.DS_Store":
        return True
    name = pure.name
    return (
        len(pure.parts) >= 4
        and pure.parts[:3] == ("docs", "teamwork", "reports")
        and (fnmatch.fnmatchcase(name, "candidate*.index") or name == "real-index.preimage")
    )


def _slugify_legacy(value: str, label: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")
    if not slug:
        fail(f"{label} cannot be mapped to a stable slug")
    if len(slug) > 120:
        slug = slug[:120].strip("-")
    return require_slug(slug, label)


def _legacy_updated_at(index: dict[str, object], sources: list[dict[str, object]]) -> str:
    dates = [str(source["updated"]) for source in sources if isinstance(source.get("updated"), str) and DATE_RE.fullmatch(str(source["updated"]))]
    if not dates and isinstance(index.get("last_updated"), str) and DATE_RE.fullmatch(str(index["last_updated"])):
        dates = [str(index["last_updated"])]
    day = max(dates) if dates else "1970-01-01"
    return f"{day}T00:00:00Z"


def _legacy_source_text(data: bytes, path: str) -> str:
    if _allowed_archive_only_binary_path(path):
        return ""
    if len(data) > MIGRATION_SOURCE_MAX_BYTES:
        fail(f"legacy migration source exceeds maximum mappable size: {path}")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        fail(f"legacy migration cannot map non-UTF-8 source: {path}: {exc}")
    if "\x00" in text:
        fail(f"legacy migration cannot map NUL-containing source: {path}")
    return text


def _legacy_entry_kind(entry: dict[str, object] | None, path: str) -> str:
    if entry is not None and isinstance(entry.get("kind"), str):
        kind = str(entry["kind"])
    else:
        kind = ""
    if "collaborate/" in path:
        if kind == "decision" or entry is not None and entry.get("status") == "accepted":
            return "decision"
        return "collaborate"
    if kind == "goal" or GOAL_PATH_RE.fullmatch(path) is not None:
        return "goal"
    if "/plans/" in path or kind == "plan":
        return "plan"
    if "/research/" in path or kind == "research":
        return "research"
    if "/workflows/debug/" in path:
        return "debug"
    if "/workflows/review/" in path:
        return "review"
    if "/workflows/init/" in path:
        return "init"
    if "/workflows/update/" in path:
        return "update"
    if "/workflows/execution/" in path or "/workflows/conclusion/" in path:
        return "result"
    if kind in MIGRATION_PHASE_BY_KIND:
        return kind
    if path.endswith("/index.json"):
        return "index"
    if path.endswith("/README.md"):
        return "runbook"
    return "result"


def _case_kind_for_legacy(classification: str) -> str:
    if classification == "collaborate":
        return "collaborate"
    if classification == "decision":
        return "decision"
    if classification == "plan":
        return "plan"
    if classification == "goal":
        return "goal"
    if classification == "research":
        return "research"
    if classification == "debug":
        return "debug"
    if classification == "review":
        return "review"
    if classification == "init":
        return "init"
    if classification == "update":
        return "update"
    if classification in {"report", "result", "progress", "execution"}:
        return "result"
    return "evidence"


def _legacy_decision_id(text: str) -> str | None:
    for pattern in (r"^Decision ID:\s*([a-z0-9]+(?:-[a-z0-9]+)*)\s*$", r'"decision_id"\s*:\s*"([a-z0-9]+(?:-[a-z0-9]+)*)"'):
        match = re.search(pattern, text, flags=re.MULTILINE)
        if match is not None:
            return require_slug(match.group(1), "legacy decision_id")
    return None


def _legacy_active_slots(index: dict[str, object]) -> dict[str, list[str]]:
    active = index.get("active")
    if not isinstance(active, dict):
        fail("legacy active state is malformed")
    result: dict[str, list[str]] = {}
    for slot, value in active.items():
        if slot == "results":
            if not isinstance(value, list):
                fail("legacy active.results is malformed")
        elif isinstance(value, str):
            result.setdefault(checked_relative(value, f"active.{slot} path"), []).append(str(slot))
        elif value is not None:
            fail(f"legacy active.{slot} is malformed")
    return result


def _legacy_retrieval_paths(index: dict[str, object]) -> set[str]:
    active = index.get("active")
    if not isinstance(active, dict):
        fail("legacy active state is malformed")
    raw = active.get("results", [])
    if not isinstance(raw, list):
        fail("legacy active.results is malformed")
    return {checked_relative(item, "active.results path") for item in raw}


def _legacy_group_key(source: dict[str, object]) -> str:
    decision_id = source.get("decision_id")
    if isinstance(decision_id, str):
        return decision_id
    topics = source.get("topics")
    if isinstance(topics, list):
        for topic in topics:
            if isinstance(topic, str) and SLUG_RE.fullmatch(topic) is not None:
                return topic
    active_slots = source.get("active_slots")
    if isinstance(active_slots, list) and active_slots:
        return require_slug(f"legacy-active-{active_slots[0]}", "legacy active slot")
    stem = PurePosixPath(str(source["path"])).stem
    return _slugify_legacy(stem, "legacy filename stem")


def _aggregate_legacy_phase(sources: list[dict[str, object]]) -> str:
    pointer_votes: list[str] = []
    for source in sources:
        for slot in source.get("active_slots", []):
            phase = MIGRATION_ACTIVE_PHASE_BY_SLOT.get(str(slot))
            if phase is not None:
                pointer_votes.append(phase)
    if pointer_votes:
        return max(pointer_votes, key=lambda phase: MIGRATION_PHASE_RANK[phase])
    nonterminal: list[str] = []
    terminal = 0
    for source in sources:
        status = str(source.get("status", ""))
        classification = str(source["classification"])
        if classification == "archive-only-binary":
            terminal += 1
            continue
        if source.get("retrieval_only") is True and not source.get("active_slots"):
            terminal += 1
            continue
        if status in MIGRATION_TERMINAL_STATUSES or source.get("currentness") == "historical":
            terminal += 1
            continue
        phase = MIGRATION_PHASE_BY_KIND.get(classification)
        if phase is None:
            fail("legacy migration found an unmapped nonterminal source combination")
        nonterminal.append(phase)
    if nonterminal:
        return max(nonterminal, key=lambda phase: MIGRATION_PHASE_RANK[phase])
    if terminal == len(sources):
        return "closed"
    fail("legacy migration could not aggregate a deterministic phase")


def _legacy_body(source: dict[str, object]) -> str:
    text = str(source["text"]).rstrip()
    classification = str(source["classification"])
    if classification == "archive-only-binary":
        return "\n".join([
            "## Archived Binary Source",
            "",
            f"- Path: `{source['path']}`",
            f"- Legacy type: `archive-only-binary`",
            f"- Legacy SHA-256: `{source['sha256']}`",
            f"- Original mode: `{source['mode']}`",
            f"- Original size: `{source['size']}` bytes",
            "",
            "Raw bytes are available only during the verified migration transaction and are not retained afterward.",
            "",
        ])
    lines = [
        f"## Legacy Source",
        "",
        f"- Path: `{source['path']}`",
        f"- Legacy type: `{classification}`",
        f"- Legacy SHA-256: `{source['sha256']}`",
    ]
    if classification == "collaborate" and re.search(r"\bgrill\b", text, flags=re.IGNORECASE):
        lines.extend([
            "- Migrated mode: `brainstorm`",
            "- Challenge evidence: preserved from the legacy grill checkpoint.",
            "- Questions: preserved in the source excerpt below.",
        ])
    lines.extend(["", "## Preserved Text", "", "```text", text, "```"])
    return "\n".join(lines) + "\n"


def _artifact_role(kind: str) -> tuple[str, str]:
    if kind in CASE_EVIDENCE_KINDS:
        return "evidence", kind
    if kind in {"review", "review-delta"}:
        return "review", kind
    if kind.startswith("history-"):
        return "history", kind.removeprefix("history-")
    return kind, kind


def _add_migrated_artifact(
    manifest: dict[str, object],
    outputs: dict[str, Output],
    *,
    source: dict[str, object],
    title: str,
    updated_at: str,
) -> tuple[dict[str, object], dict[str, object]]:
    case_id = str(manifest["case_id"])
    source_digest = str(source["sha256"])
    kind = _case_kind_for_legacy(str(source["classification"]))
    rendered = render_case_artifact(kind, title, _legacy_body(source), source_digest=source_digest, updated_at=updated_at)
    role, subtype = _artifact_role(kind)
    envelope = {
        "schema_version": 1,
        "role": role,
        "subtype": subtype,
        "case_id": case_id,
        "claim_ids": [],
        "consumer": "teamwork-migration",
        "source_revision": source_digest,
        "immutable": True,
    }
    artifact_id = artifact_id_for_case(kind, envelope, rendered)
    used_paths = {str(row["path"]) for row in manifest["artifacts"].values()}
    if kind == "review":
        path = derive_case_source_artifact_path(case_id, "review", source_digest)
    else:
        path = derive_case_source_artifact_path(case_id, kind, artifact_id)
    if path in used_paths or path in outputs:
        path = f"{case_base(case_id)}/sources/evidence/{artifact_id}.md"
        kind = "evidence"
    digest = artifact_digest(path, rendered)
    manifest = _case_add_artifact(
        manifest,
        kind=kind,
        path=path,
        artifact_id=artifact_id,
        digest=digest,
        updated_at=updated_at,
        source_revision=source_digest,
        consumer="teamwork-migration",
        allow_document_staging=True,
    )
    outputs[path] = Output(rendered.encode("utf-8"))
    return manifest, {
        "source_path": source["path"],
        "source_digest": source_digest,
        "classification": source["classification"],
        "artifact_id": artifact_id,
        "artifact_path": path,
        "artifact_digest": digest,
        "case_id": case_id,
    }


def _materialize_migrated_live_document(
    manifest: dict[str, object],
    outputs: dict[str, Output],
    *,
    title: str,
    updated_at: str,
) -> dict[str, object]:
    grouped: dict[str, list[tuple[str, str, str]]] = {}
    for artifact_id, row in sorted(
        manifest["artifacts"].items(),
        key=lambda item: (str(item[1]["created_at"]), str(item[0])),
    ):
        path = str(row["path"])
        output = outputs.get(path)
        if output is None or output.data is None:
            fail("migration live-document fold is missing a source artifact", category="INDETERMINATE")
        if hashlib.sha256(output.data).hexdigest() != row["byte_digest"]:
            fail("migration source artifact changed before live-document fold", category="INDETERMINATE")
        try:
            text = output.data.decode("utf-8")
        except UnicodeDecodeError:
            fail("migration source artifact must be UTF-8", category="INDETERMINATE")
        kind = _artifact_kind_from_row(row)
        heading = case_live_section(kind, path)
        grouped.setdefault(heading, []).append((str(artifact_id), str(row["byte_digest"]), text))
    sections: dict[str, str] = {}
    needs_resolution = False
    for heading in CASE_LIVE_SECTIONS:
        rows = grouped.get(heading, [])
        if not rows:
            continue
        distinct = {digest for _, digest, _ in rows}
        if heading in CASE_REPLACE_SECTIONS and len(distinct) > 1:
            needs_resolution = True
        chunks: list[str] = []
        if heading in CASE_REPLACE_SECTIONS and len(distinct) > 1:
            chunks.extend([
                "> **Needs resolution:** multiple migrated sources disagree; no source was selected as canonical.",
                "",
            ])
        for artifact_id, digest, text in rows:
            chunks.extend([
                f"### Migrated source `{artifact_id}`",
                "",
                f"Byte digest: `{digest}`",
                "",
                text.rstrip(),
                "",
            ])
        sections[heading] = "\n".join(chunks).rstrip() + "\n"
    case_id = str(manifest["case_id"])
    purpose_candidates = {
        case_live_purpose(_artifact_kind_from_row(row))
        for row in manifest["artifacts"].values()
    }
    purpose_candidates.discard("task")
    purpose = next(iter(purpose_candidates)) if len(purpose_candidates) == 1 else "task"
    rendered = render_case_live_document(
        case_id=case_id,
        title=title,
        purpose=purpose,
        status="finalized" if manifest["status"] == "closed" else "active",
        generation=1,
        updated_at=updated_at,
        needs_resolution=needs_resolution,
        sections=sections,
    )
    source_ids = [str(item) for item in manifest["artifacts"]]
    source_paths = {str(row["path"]) for row in manifest["artifacts"].values()}
    source_digest = case_digest("migration-live-sources", source_ids)
    live_kind = case_live_artifact_kind(
        purpose,
        closed=manifest["status"] == "closed",
        has_claims=bool(manifest["claims"]),
    )
    role, subtype = _artifact_role(live_kind)
    envelope = {
        "role": role,
        "subtype": subtype,
        "case_id": case_id,
        "claim_ids": [],
        "consumer": "teamwork-migration",
        "source_revision": source_digest,
        "immutable": True,
    }
    artifact_id = artifact_id_for_case(live_kind, envelope, rendered)
    path = case_live_document_path(case_id)
    digest = artifact_digest(path, rendered)
    manifest = dict(manifest)
    manifest["artifacts"] = {}
    manifest["history"] = []
    manifest["references"] = []
    manifest = validate_case_manifest(manifest, migration_read=True)
    manifest = _case_add_artifact(
        manifest,
        kind=live_kind,
        path=path,
        artifact_id=artifact_id,
        digest=digest,
        updated_at=updated_at,
        source_revision=source_digest,
        consumer="teamwork-migration",
        allow_document_staging=True,
    )
    manifest = dict(manifest)
    claims = {}
    for claim_id, raw_claim in manifest["claims"].items():
        claim = dict(raw_claim)
        claim["head_artifact_id"] = artifact_id
        claim["head_digest"] = digest
        claims[claim_id] = claim
    manifest["claims"] = claims
    manifest["migration_sources"] = [
        {**row, "artifact_id": artifact_id}
        for row in manifest["migration_sources"]
    ]
    manifest["document"] = {
        "path": path,
        "generation": 1,
        "byte_digest": digest,
        "updated_at": updated_at,
        "title": title,
        "purpose": purpose,
        "status": "finalized" if manifest["status"] == "closed" else "active",
        "needs_resolution": needs_resolution,
        "latest_artifact_id": artifact_id,
        "source_artifact_ids": [artifact_id],
    }
    manifest["runtime"] = {
        "active_route": path,
        "state_revision": case_digest(
            "case-runtime",
            {"case_id": case_id, "path": path, "generation": 1, "at": updated_at},
        ),
    }
    for source_path in source_paths:
        outputs.pop(source_path, None)
    outputs[path] = Output(rendered.encode("utf-8"))
    return validate_case_manifest(manifest)


def _legacy_sources_from_baseline(root: Path, baseline: dict[str, object]) -> tuple[dict[str, object], list[dict[str, object]]]:
    index_text = safe_read_text(root, INDEX_PATH)
    assert index_text is not None
    index = parse_index(index_text, migration=True)
    rows = _validate_baseline_payload(baseline)["paths"]
    entries_by_path: dict[str, list[dict[str, object]]] = {}
    for entry in index.get("entries", []):
        if isinstance(entry, dict):
            entries_by_path.setdefault(checked_relative(entry.get("path"), "legacy entry path"), []).append(entry)
    active_by_path = _legacy_active_slots(index)
    retrieval_paths = _legacy_retrieval_paths(index)
    sources: list[dict[str, object]] = []
    seen_sha_paths: set[tuple[str, str]] = set()
    for row in rows:
        path = str(row["path"])
        data = _assert_current_file_matches_baseline(root, row)
        text = _legacy_source_text(data, path)
        digest = hashlib.sha256(data).hexdigest()
        key = (path, digest)
        if key in seen_sha_paths:
            fail("legacy migration source collision detected")
        seen_sha_paths.add(key)
        entries = entries_by_path.get(path, [])
        primary = entries[0] if entries else None
        classification = _legacy_entry_kind(primary, path)
        topics = sorted({str(entry["topic"]) for entry in entries if isinstance(entry.get("topic"), str) and SLUG_RE.fullmatch(str(entry["topic"])) is not None})
        active_slots = sorted(active_by_path.get(path, []))
        source = {
            "path": path,
            "sha256": digest,
            "mode": row["mode"],
            "size": row["size"],
            "text": text,
            "classification": "archive-only-binary" if text == "" and _allowed_archive_only_binary_path(path) else classification,
            "topics": topics,
            "active_slots": active_slots,
            "retrieval_only": path in retrieval_paths,
            "status": primary.get("status") if primary is not None else "historical",
            "currentness": primary.get("currentness") if primary is not None else "historical",
            "updated": primary.get("updated") if primary is not None else index.get("last_updated"),
            "decision_id": _legacy_decision_id(text),
        }
        source["group_key"] = _legacy_group_key(source)
        sources.append(source)
    dangling = sorted(set(entries_by_path) - {str(row["path"]) for row in rows})
    if dangling:
        fail(f"legacy migration found dangling index entries outside baseline: {', '.join(dangling[:3])}")
    return index, sorted(sources, key=lambda item: str(item["path"]))


def build_migration_candidate_tree(root: Path, migration_id: str, state: dict[str, object], baseline: dict[str, object]) -> tuple[dict[str, object], list[dict[str, object]], dict[str, Output], dict[str, object]]:
    index, sources = _legacy_sources_from_baseline(root, baseline)
    project = index.get("project") if isinstance(index.get("project"), dict) else {}
    project_name = str(project.get("name", "Teamwork"))
    candidate = empty_case_index(project_name)
    candidate["project"] = {
        "name": require_text(project.get("name", project_name), "project.name", maximum=200),
        "root": ".",
        "description": require_text(project.get("description", "Local Teamwork case-bundle index for this project."), "project.description", maximum=1000),
    }
    groups: dict[str, list[dict[str, object]]] = {}
    for source in sources:
        groups.setdefault(str(source["group_key"]), []).append(source)
    outputs: dict[str, Output] = {}
    manifests: list[dict[str, object]] = []
    coverage_rows: list[dict[str, object]] = []
    alias_candidates: dict[str, dict[str, object]] = {}
    aliases_seen: set[str] = set()
    for group_key in sorted(groups):
        group_sources = sorted(groups[group_key], key=lambda item: str(item["path"]))
        alias = require_slug(group_key, "migration alias")
        if alias in aliases_seen:
            fail("legacy migration alias collision detected")
        aliases_seen.add(alias)
        seed = case_digest(
            "legacy-migration-case-seed",
            {
                "migration_id": migration_id,
                "group_key": group_key,
                "sources": [{"path": item["path"], "sha256": item["sha256"]} for item in group_sources],
            },
        )
        case_id = case_id_from_seed(seed)
        phase = _aggregate_legacy_phase(group_sources)
        updated_at = _legacy_updated_at(index, group_sources)
        title = group_key.replace("-", " ").title()
        manifest = validate_case_manifest({
            "schema_version": 2,
            "case_id": case_id,
            "case_seed_b64": base64.b64encode(bytes.fromhex(seed)).decode("ascii"),
            "created_at": updated_at,
            "closed_at": updated_at if phase == "closed" else None,
            "status": phase,
            "claims": {},
            "artifacts": {},
            "history": [],
            "references": [],
            "runtime": {
                "active_route": case_manifest_path(case_id),
                "state_revision": case_digest("case-runtime", {"case_id": case_id, "phase": phase, "at": updated_at, "migration_id": migration_id}),
            },
            "migration_sources": [],
            "document": None,
        })
        group_coverage_rows: list[dict[str, object]] = []
        for source in group_sources:
            manifest, coverage = _add_migrated_artifact(manifest, outputs, source=source, title=title, updated_at=updated_at)
            group_coverage_rows.append(coverage)
            coverage_rows.append(coverage)
            if source["classification"] == "goal" and set(source.get("active_slots", [])) & {"progress", "goal"}:
                claim_seed = case_digest(
                    "legacy-migration-claim-seed",
                    {
                        "migration_id": migration_id,
                        "case_id": case_id,
                        "source_path": source["path"],
                        "artifact_id": coverage["artifact_id"],
                    },
                )
                claim_id = claim_id_from_seed(claim_seed)
                descriptor_digest = case_digest("claim-descriptor", {"case_id": case_id, "claim_id": claim_id, "owner": "teamwork-migration"})
                claim = {
                    "descriptor_version": 1,
                    "descriptor_digest": descriptor_digest,
                    "status": "active",
                    "acquired_at": updated_at,
                    "released_at": None,
                    "head_artifact_id": coverage["artifact_id"],
                    "head_digest": coverage["artifact_digest"],
                }
                manifest = dict(manifest)
                manifest["claims"] = {**manifest["claims"], claim_id: claim}
                claim_revision = case_digest("claim-revision", {"case_id": case_id, "claim_id": claim_id, "artifact_digest": coverage["artifact_digest"]})
                candidate["claim_heads"][claim_id] = {
                    "case_id": case_id,
                    "artifact_id": coverage["artifact_id"],
                    "artifact_digest": coverage["artifact_digest"],
                    "claim_revision": claim_revision,
                    "status": "active",
                }
        manifest = dict(manifest)
        manifest["migration_sources"] = [
            {
                "source_path": row["source_path"],
                "source_digest": row["source_digest"],
                "classification": _slugify_legacy(str(row["classification"]), "migration source classification"),
                "migration_id": migration_id,
                "artifact_id": row["artifact_id"],
            }
            for row in group_coverage_rows
        ]
        manifest = validate_case_manifest(manifest, migration_read=True)
        manifest = _materialize_migrated_live_document(
            manifest,
            outputs,
            title=title,
            updated_at=updated_at,
        )
        live_id = str(manifest["document"]["latest_artifact_id"])
        live_path = str(manifest["document"]["path"])
        live_digest = str(manifest["document"]["byte_digest"])
        for coverage in group_coverage_rows:
            coverage["artifact_id"] = live_id
            coverage["artifact_path"] = live_path
            coverage["artifact_digest"] = live_digest
        for claim_id, head in list(candidate["claim_heads"].items()):
            if head["case_id"] == case_id:
                candidate["claim_heads"][claim_id] = {
                    **head,
                    "artifact_id": live_id,
                    "artifact_digest": live_digest,
                    "claim_revision": case_digest(
                        "claim-revision",
                        {"case_id": case_id, "claim_id": claim_id, "artifact_digest": live_digest, "at": updated_at},
                    ),
                }
        manifests.append(manifest)
        manifest_revision = case_manifest_revision(manifest)
        if phase == "closed":
            result_artifacts = [(artifact_id, row) for artifact_id, row in manifest["artifacts"].items() if row["role"] == "result"]
            result_artifact_id, result_artifact = sorted(result_artifacts, key=lambda item: str(item[1]["created_at"]))[-1]
            candidate["recent_cases"].append({
                "case_id": case_id,
                "manifest_path": case_manifest_path(case_id),
                "closed_at": updated_at,
                "result_artifact_id": result_artifact_id,
                "result_digest": result_artifact["byte_digest"],
            })
        else:
            candidate["active_cases"].append({
                "case_id": case_id,
                "manifest_path": case_manifest_path(case_id),
                "manifest_revision": manifest_revision,
                "phase": phase,
                "task_key": alias,
            })
        alias_candidates[alias] = {
            "target_type": "case",
            "target_id": case_id,
            "manifest_path": case_manifest_path(case_id),
            "manifest_revision": manifest_revision,
        }
    candidate["recent_cases"] = sorted(candidate["recent_cases"], key=lambda row: (str(row["closed_at"]), str(row["case_id"])), reverse=True)[:CASE_CAPS["recent_cases"]]
    hot_case_ids = {
        str(row["case_id"])
        for row in [*candidate["active_cases"], *candidate["recent_cases"]]
        if isinstance(row, dict)
    }
    candidate["aliases"] = {
        alias: row
        for alias, row in sorted(alias_candidates.items())
        if str(row["target_id"]) in hot_case_ids
    }
    candidate["migration"] = {
        "migration_id": migration_id,
        "phase": "candidate_validated",
        "journal_path": migration_runtime_path(migration_id, "journal.json"),
        "baseline_digest": state["baseline_digest"],
        "report_digest": case_digest("restore-report", "pending"),
        "candidate_digest": "0" * 64,
        "archive_manifest_digest": state["archive_manifest_digest"],
    }
    artifact_outputs = dict(outputs)
    _write_case_index_and_manifest_outputs(candidate, manifests, outputs)
    candidate_prefix = f"{migration_runtime_dir(migration_id)}/candidate/docs-teamwork/"
    candidate_outputs = {candidate_prefix + path.removeprefix("docs/teamwork/"): output for path, output in outputs.items()}
    coverage_paths = {str(row["source_path"]) for row in coverage_rows if not row.get("derived_terminal_result")}
    baseline_paths = {str(row["path"]) for row in _validate_baseline_payload(baseline)["paths"]}
    if coverage_paths != baseline_paths:
        fail("legacy migration coverage does not exactly match baseline paths")
    coverage_report = {
        "schema_version": 1,
        "migration_id": migration_id,
        "baseline_digest": state["baseline_digest"],
        "candidate_digest": "0" * 64,
        "baseline_paths": sorted(baseline_paths),
        "coverage_rows": sorted(coverage_rows, key=lambda row: (str(row["source_path"]), str(row.get("derived_terminal_result", False)))),
        "unsafe": [],
        "unmapped": [],
        "encoding": [],
        "size": [],
        "collision": [],
        "dangling": [],
    }
    candidate_outputs[migration_runtime_path(migration_id, "coverage.json")] = migration_json_output(coverage_report)
    candidate_digest = candidate_tree_digest_from_outputs(migration_id, candidate_outputs)
    candidate["migration"]["candidate_digest"] = candidate_digest
    coverage_report["candidate_digest"] = candidate_digest
    outputs = dict(artifact_outputs)
    _write_case_index_and_manifest_outputs(candidate, manifests, outputs)
    candidate_outputs = {candidate_prefix + path.removeprefix("docs/teamwork/"): output for path, output in outputs.items()}
    candidate_outputs[migration_runtime_path(migration_id, "coverage.json")] = migration_json_output(coverage_report)
    return candidate, manifests, candidate_outputs, coverage_report


def validate_candidate_outputs_readonly(migration_id: str, candidate_outputs: dict[str, Output]) -> dict[str, object]:
    candidate_prefix = f"{migration_runtime_dir(migration_id)}/candidate/docs-teamwork/"
    with tempfile.TemporaryDirectory(prefix=f"teamwork-migration-preflight-{migration_id}-") as temporary:
        validation_root = Path(temporary)
        materialized = 0
        for path, output in candidate_outputs.items():
            if output.data is None or not path.startswith(candidate_prefix):
                continue
            logical = "docs/teamwork/" + path.removeprefix(candidate_prefix)
            checked_relative(logical, "candidate validation path")
            target = validation_root.joinpath(*PurePosixPath(logical).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(output.data)
            os.chmod(target, output.mode)
            materialized += 1
        if materialized == 0:
            fail("candidate validation tree is empty", category="INDETERMINATE")
        return validate_case_v3_tree_readonly(validation_root)


def _validate_baseline_payload(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != {"schema_version", "paths", "baseline_digest"}:
        fail("migration baseline has an unsupported schema")
    if value.get("schema_version") != 1:
        fail("migration baseline schema_version must be 1")
    rows_raw = value.get("paths")
    if not isinstance(rows_raw, list) or not rows_raw:
        fail("migration baseline must contain at least one file")
    rows: list[dict[str, object]] = []
    seen: set[str] = set()
    for position, raw in enumerate(rows_raw):
        if not isinstance(raw, dict) or set(raw) != {"path", "sha256", "mode", "size"}:
            fail(f"migration baseline row {position} is malformed")
        path = checked_relative(raw.get("path"), "baseline source path")
        if path in seen:
            fail("migration baseline must not duplicate paths")
        seen.add(path)
        mode = raw.get("mode")
        size = raw.get("size")
        if not isinstance(mode, int) or not 0 <= mode <= 0o777:
            fail("migration baseline mode is invalid")
        if not isinstance(size, int) or size < 0:
            fail("migration baseline size is invalid")
        rows.append({"path": path, "sha256": _hex64(raw.get("sha256"), "baseline sha256"), "mode": mode, "size": size})
    rows = sorted(rows, key=lambda row: str(row["path"]))
    digest = _hex64(value.get("baseline_digest"), "baseline_digest")
    if case_digest("migration-baseline", rows) != digest:
        fail("migration baseline payload does not match digest")
    return {"schema_version": 1, "paths": rows, "baseline_digest": digest}


def _baseline_row_by_path(baseline: dict[str, object]) -> dict[str, dict[str, object]]:
    checked = _validate_baseline_payload(baseline)
    return {str(row["path"]): row for row in checked["paths"]}


def _assert_current_file_matches_baseline(root: Path, row: dict[str, object]) -> bytes:
    source_path = checked_relative(row.get("path"), "baseline source path")
    data = safe_read_bytes(root, source_path)
    assert data is not None
    mode = _mode_of(root, source_path)
    if mode is None:
        fail("baseline source disappeared during migration", category="INDETERMINATE")
    digest = hashlib.sha256(data).hexdigest()
    if digest != row.get("sha256") or len(data) != row.get("size") or mode != row.get("mode"):
        fail("baseline changed before archive materialization")
    return data


def _validate_archive_manifest(value: object, state: dict[str, object], baseline: dict[str, object]) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != {"schema_version", "migration_id", "baseline_digest", "objects", "archive_manifest_digest"}:
        fail("archive manifest has an unsupported schema", category="INDETERMINATE")
    if value.get("schema_version") != 1 or value.get("migration_id") != state.get("migration_id"):
        fail("archive manifest identity mismatch", category="INDETERMINATE")
    if value.get("baseline_digest") != state.get("baseline_digest"):
        fail("archive manifest baseline mismatch", category="INDETERMINATE")
    objects_raw = value.get("objects")
    if not isinstance(objects_raw, list) or not objects_raw:
        fail("archive manifest must contain at least one object", category="INDETERMINATE")
    expected_by_path = _baseline_row_by_path(baseline)
    objects: list[dict[str, object]] = []
    seen_sources: set[str] = set()
    for position, raw in enumerate(objects_raw):
        if not isinstance(raw, dict) or set(raw) != {"source_path", "object_path", "sha256", "mode", "size"}:
            fail(f"archive object row {position} is malformed", category="INDETERMINATE")
        source_path = checked_relative(raw.get("source_path"), "archive source path")
        object_path = checked_relative(raw.get("object_path"), "archive object path")
        digest = _hex64(raw.get("sha256"), "archive object sha256")
        mode = raw.get("mode")
        size = raw.get("size")
        if not isinstance(mode, int) or not 0 <= mode <= 0o777 or not isinstance(size, int) or size < 0:
            fail("archive object mode or size is invalid", category="INDETERMINATE")
        if source_path in seen_sources:
            fail("archive manifest duplicates a source path", category="INDETERMINATE")
        seen_sources.add(source_path)
        baseline_row = expected_by_path.get(source_path)
        if baseline_row is None:
            fail("archive manifest contains a source outside the baseline", category="INDETERMINATE")
        if (
            baseline_row["sha256"] != digest
            or baseline_row["mode"] != mode
            or baseline_row["size"] != size
            or object_path != migration_archive_object_path(str(state["migration_id"]), digest)
        ):
            fail("archive manifest does not exactly cover the baseline", category="INDETERMINATE")
        objects.append({"source_path": source_path, "object_path": object_path, "sha256": digest, "mode": mode, "size": size})
    if set(expected_by_path) != seen_sources:
        fail("archive manifest does not exactly cover the baseline", category="INDETERMINATE")
    manifest = {
        "schema_version": 1,
        "migration_id": state["migration_id"],
        "baseline_digest": state["baseline_digest"],
        "objects": sorted(objects, key=lambda row: str(row["source_path"])),
    }
    archive_digest = case_digest("archive-manifest", manifest)
    if value.get("archive_manifest_digest") != archive_digest or state.get("archive_manifest_digest") != archive_digest:
        fail("archive manifest digest does not match runtime state", category="INDETERMINATE")
    manifest["archive_manifest_digest"] = archive_digest
    return manifest


def export_v1_baseline(root: Path) -> dict[str, object]:
    if detect_teamwork_memory_schema(root, migration=True) != "legacy-v1":
        fail("migration baseline export requires legacy-v1 memory")
    base = root / "docs/teamwork"
    rows: list[dict[str, object]] = []
    for path in sorted(base.rglob("*")):
        relative = path.relative_to(root).as_posix()
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode):
            fail("migration baseline refuses symlinks")
        if stat.S_ISREG(info.st_mode):
            data = safe_read_bytes(root, relative)
            assert data is not None
            rows.append({"path": relative, "sha256": hashlib.sha256(data).hexdigest(), "mode": stat.S_IMODE(info.st_mode), "size": len(data)})
    rows = sorted(rows, key=lambda row: str(row["path"]))
    digest = case_digest("migration-baseline", rows)
    return {"schema_version": 1, "paths": rows, "baseline_digest": digest}


def validate_case_v3_tree_readonly(root: Path) -> dict[str, object]:
    index_text = safe_read_text(root, INDEX_PATH)
    assert index_text is not None
    index = validate_case_index(_decode_json(index_text, "case index"))
    manifests: dict[str, dict[str, object]] = {}
    for collection in ("active_cases", "recent_cases"):
        rows = index[collection]
        assert isinstance(rows, list)
        for row in rows:
            assert isinstance(row, dict)
            case_id = str(row["case_id"])
            manifest_text = safe_read_text(root, str(row["manifest_path"]))
            assert manifest_text is not None
            manifest = validate_case_manifest(_decode_json(manifest_text, "case manifest"))
            revision = case_manifest_revision(manifest)
            if collection == "active_cases" and revision != row["manifest_revision"]:
                fail("case-v3 preflight active manifest revision mismatch")
            if collection == "recent_cases" and manifest["status"] != "closed":
                fail("case-v3 preflight recent manifest must be closed")
            artifacts = manifest["artifacts"]
            assert isinstance(artifacts, dict)
            for artifact_id, artifact in artifacts.items():
                assert isinstance(artifact, dict)
                artifact_text = safe_read_text(root, str(artifact["path"]))
                assert artifact_text is not None
                if artifact_digest(str(artifact["path"]), artifact_text) != artifact["byte_digest"]:
                    fail("case-v3 preflight artifact digest mismatch")
                if str(artifact_id) != _artifact_id(artifact_id):
                    fail("case-v3 preflight artifact id mismatch")
            manifests[case_id] = manifest
    cases_root = root / "docs/teamwork/cases"
    if cases_root.exists():
        root_info = cases_root.lstat()
        if stat.S_ISLNK(root_info.st_mode) or not stat.S_ISDIR(root_info.st_mode):
            fail("case-v3 preflight cases root is unsafe")
        for case_directory in sorted(cases_root.iterdir(), key=lambda item: item.name):
            info = case_directory.lstat()
            case_id = _case_id(case_directory.name)
            if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
                fail("case-v3 preflight case directory is unsafe")
            if case_id not in manifests:
                manifest_text = safe_read_text(root, case_manifest_path(case_id))
                assert manifest_text is not None
                manifests[case_id] = validate_case_manifest(_decode_json(manifest_text, "unindexed case manifest"))
            manifest = manifests[case_id]
            expected_names = {"manifest.json"}
            if isinstance(manifest.get("document"), dict):
                expected_names.add("live.md")
                _read_case_live_state(root, manifest, fallback_title=str(manifest["document"]["title"]))
            observed_names: set[str] = set()
            for child in case_directory.iterdir():
                child_info = child.lstat()
                if stat.S_ISLNK(child_info.st_mode) or not stat.S_ISREG(child_info.st_mode) or child_info.st_nlink != 1:
                    fail("case-v3 preflight case may contain only manifest.json and live.md files")
                observed_names.add(child.name)
            if observed_names != expected_names:
                fail("case-v3 preflight case directory contains retired artifacts")
    aliases = index["aliases"]
    assert isinstance(aliases, dict)
    for alias, row in aliases.items():
        assert isinstance(row, dict)
        manifest = manifests.get(str(row["target_id"]))
        if manifest is None or case_manifest_revision(manifest) != row["manifest_revision"]:
            fail(f"case-v3 preflight alias target is invalid: {alias}")
    claim_heads = index["claim_heads"]
    assert isinstance(claim_heads, dict)
    for claim_id, head in claim_heads.items():
        assert isinstance(head, dict)
        manifest = manifests.get(str(head["case_id"]))
        if manifest is None:
            fail("case-v3 preflight claim head case is missing")
        claims = manifest["claims"]
        artifacts = manifest["artifacts"]
        assert isinstance(claims, dict) and isinstance(artifacts, dict)
        claim = claims.get(claim_id)
        artifact = artifacts.get(str(head["artifact_id"]))
        if not isinstance(claim, dict) or not isinstance(artifact, dict):
            fail("case-v3 preflight claim head target is missing")
        if claim["head_artifact_id"] != head["artifact_id"] or claim["head_digest"] != head["artifact_digest"] or artifact["byte_digest"] != head["artifact_digest"]:
            fail("case-v3 preflight claim head digest mismatch")
    return index


def migration_preflight(root: Path) -> dict[str, object]:
    mode = detect_teamwork_memory_schema(root, migration=True)
    if mode != "legacy-v1":
        index = validate_case_v3_tree_readonly(root) if mode == "case-v3" else None
        migration = None if index is None else index["migration"]
        return {"schema_version": 1, "mode": mode, "ok": mode == "case-v3", "blocking": [], "migration": migration}
    baseline = export_v1_baseline(root)
    seed = case_digest("legacy-migration-seed", {"baseline_digest": baseline["baseline_digest"]})
    migration_id = migration_id_from_seed(seed)
    state = {
        "schema_version": 1,
        "migration_id": migration_id,
        "phase": "archive_durable",
        "baseline_digest": baseline["baseline_digest"],
        "archive_manifest_digest": "0" * 64,
        "candidate_digest": None,
        "report_digest": None,
        "restore_drill": None,
        "cleanup": None,
    }
    candidate, manifests, candidate_outputs, coverage = build_migration_candidate_tree(root, migration_id, state, baseline)
    validate_candidate_outputs_readonly(migration_id, candidate_outputs)
    recognized = [
        {
            "path": row["source_path"],
            "sha256": row["source_digest"],
            "classification": row["classification"],
            "artifact_id": row["artifact_id"],
            "artifact_path": row["artifact_path"],
            "case_id": row["case_id"],
        }
        for row in coverage["coverage_rows"]
        if isinstance(row, dict) and row.get("classification") == "archive-only-binary" and not row.get("derived_terminal_result")
    ]
    return {
        "schema_version": 1,
        "mode": "legacy-v1",
        "ok": True,
        "migration_id": migration_id,
        "baseline_digest": baseline["baseline_digest"],
        "baseline_paths": len(baseline["paths"]),
        "recognized_archive_only_binary": recognized,
        "blocking": [],
        "shape": {
            "groups": len(manifests),
            "manifests": len(manifests),
            "active_cases": len(candidate["active_cases"]),
            "recent_cases": len(candidate["recent_cases"]),
            "aliases": len(candidate["aliases"]),
        },
        "candidate_digest": coverage["candidate_digest"],
    }


def migration_schema(operation: str) -> dict[str, object]:
    if operation not in {"request", "approve-baseline", "materialize-archive", "prepare-candidate", "restore-drill", "cutover", "cleanup"}:
        fail("migration schema operation is invalid")
    if operation == "request":
        return {"schema_version": 1, "operation": "approve-baseline", "migration_seed": "<64 lowercase hex seed>"}
    request: dict[str, object] = {"schema_version": 1, "operation": operation, "migration_id": "m-" + "0" * 64, "baseline_digest": "0" * 64, "request_digest": "0" * 64}
    if operation == "approve-baseline":
        request["baseline"] = {"schema_version": 1, "paths": [], "baseline_digest": "0" * 64}
    if operation == "cutover":
        request["cutover_authority"] = "I authorize Teamwork memory cutover"
    return request


def construct_migration_request(root: Path, raw: dict[str, object]) -> dict[str, object]:
    if raw.get("schema_version") != 1:
        fail("migration-request schema_version must be 1")
    operation = raw.get("operation", "approve-baseline")
    if operation not in {"approve-baseline", "materialize-archive", "prepare-candidate", "restore-drill", "cleanup"}:
        fail("migration-request operation is invalid")
    migration_id = migration_id_from_seed(raw.get("migration_seed"))
    with locked_memory(root):
        baseline = export_v1_baseline(root)
        request = {
            "schema_version": 1,
            "operation": operation,
            "migration_id": migration_id,
            "baseline_digest": baseline["baseline_digest"],
            "baseline": baseline if operation == "approve-baseline" else None,
        }
        request["request_digest"] = migration_request_digest(request)
        return request


def _validate_migration_request(raw: dict[str, object]) -> dict[str, object]:
    if raw.get("schema_version") != 1:
        fail("migration apply schema_version must be 1")
    operation = raw.get("operation")
    if operation not in {"approve-baseline", "materialize-archive", "prepare-candidate", "restore-drill", "cutover", "cleanup"}:
        fail("migration apply operation is invalid")
    request = {
        "operation": operation,
        "migration_id": _migration_id(raw.get("migration_id")),
        "baseline_digest": _hex64(raw.get("baseline_digest"), "baseline_digest"),
        "request_digest": _hex64(raw.get("request_digest"), "request_digest"),
    }
    if operation == "approve-baseline":
        baseline = _validate_baseline_payload(raw.get("baseline"))
        if baseline.get("baseline_digest") != request["baseline_digest"]:
            fail("migration baseline digest mismatch")
        request["baseline"] = baseline
    if operation == "cutover":
        request["cutover_authority"] = raw.get("cutover_authority")
    digest_payload: dict[str, object] = {
        "schema_version": 1,
        "operation": operation,
        "migration_id": request["migration_id"],
        "baseline_digest": request["baseline_digest"],
        "baseline": request.get("baseline") if operation == "approve-baseline" else None,
    }
    if operation == "cutover":
        digest_payload["cutover_authority"] = request.get("cutover_authority")
    expected_digest = migration_request_digest(digest_payload)
    if request["request_digest"] != expected_digest:
        fail("migration request digest mismatch")
    return request


def migration_request_digest(payload: dict[str, object]) -> str:
    return case_digest(
        "migration-request",
        {key: value for key, value in payload.items() if key != "request_digest"},
    )


def migration_phase_request(operation: str, migration_id: str, baseline_digest: str, *, baseline: dict[str, object] | None = None, cutover_authority: str | None = None) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": 1,
        "operation": operation,
        "migration_id": migration_id,
        "baseline_digest": baseline_digest,
        "baseline": baseline if operation == "approve-baseline" else None,
    }
    if operation == "cutover":
        payload["cutover_authority"] = cutover_authority
    payload["request_digest"] = migration_request_digest(payload)
    return payload


def migration_failpoint(name: str) -> None:
    if os.environ.get("TEAMWORK_MIGRATION_FAILPOINT") == name:
        raise TransactionError(f"simulated migration failpoint: {name}", "INDETERMINATE")


def _safe_dir(root: Path, relative: str, *, optional: bool = False) -> Path | None:
    checked_relative(relative, "directory path")
    parent = _walk_parent(root, f"{relative}/placeholder", create=False)
    if parent is None:
        if optional:
            return None
        fail("directory parent does not exist", category="INDETERMINATE")
    path = parent
    # _walk_parent returns the parent of the synthetic placeholder, i.e. the
    # requested directory.
    try:
        info = path.lstat()
    except FileNotFoundError:
        if optional:
            return None
        fail(f"directory is missing: {relative}", category="INDETERMINATE")
    except OSError as exc:
        fail(f"cannot inspect directory {relative}: {exc}", category="INDETERMINATE")
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode) or info.st_dev != _root_device(root):
        fail(f"directory must be same-device non-symlink: {relative}", category="INDETERMINATE")
    return path


def _rename_dir(root: Path, source: str, target: str) -> None:
    source_path = _safe_dir(root, source)
    assert source_path is not None
    target_parent = _walk_parent(root, target, create=True)
    if target_parent is None:
        fail("target directory parent does not exist", category="INDETERMINATE")
    target_path = target_parent / PurePosixPath(target).name
    if target_path.exists():
        fail(f"target directory already exists: {target}", category="INDETERMINATE")
    try:
        os.rename(source_path, target_path)
    except OSError as exc:
        fail(f"cannot rename directory {source} -> {target}: {exc}", category="INDETERMINATE")
    _fsync_directory(source_path.parent)
    _fsync_directory(target_path.parent)


def _read_json_relative(root: Path, relative: str, label: str) -> dict[str, object]:
    raw = safe_read_text(root, relative)
    assert raw is not None
    try:
        value = json.loads(raw)
    except Exception as exc:
        fail(f"cannot read {label}: {exc}", category="INDETERMINATE")
    if not isinstance(value, dict):
        fail(f"{label} must be an object", category="INDETERMINATE")
    return value


def _write_json_relative(root: Path, relative: str, value: dict[str, object]) -> None:
    ensure_directory(root, PurePosixPath(checked_relative(relative, "cutover JSON path")).parent.as_posix())
    data = (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    parent = PurePosixPath(relative).parent.as_posix()
    stage = _write_temp(root, parent, f".tw-cutover-{secrets.token_hex(16)}", data, 0o600)
    _replace(root, stage, relative)


def _load_cutover_journal(root: Path, migration_id: str) -> dict[str, object] | None:
    relative = migration_runtime_path(migration_id, "cutover-journal.json")
    if safe_read_bytes(root, relative, optional=True) is None:
        return None
    journal = _read_json_relative(root, relative, "cutover journal")
    if journal.get("schema_version") != 1 or journal.get("migration_id") != migration_id:
        fail("cutover journal schema mismatch", category="INDETERMINATE")
    expected_paths = {
        "old_tree": "docs/teamwork",
        "renamed_old_tree": migration_runtime_path(migration_id, "renamed-old/docs-teamwork"),
        "candidate_tree": migration_runtime_path(migration_id, "candidate/docs-teamwork"),
        "new_tree": "docs/teamwork",
    }
    for field, expected in expected_paths.items():
        actual = journal.get(field)
        if actual != expected:
            fail(f"cutover journal {field} does not match migration-owned path", category="INDETERMINATE")
    return journal


def _store_cutover_journal(root: Path, migration_id: str, journal: dict[str, object]) -> None:
    _write_json_relative(root, migration_runtime_path(migration_id, "cutover-journal.json"), journal)


def _validate_installed_candidate(root: Path, migration_id: str, state: dict[str, object]) -> dict[str, object]:
    report_digest = _hex64(state.get("report_digest"), "migration restore report digest")
    report = read_migration_json(root, migration_id, "restore-drill/report.json")
    if case_digest("restore-report", report) != report_digest:
        fail("restore report digest does not match runtime state", category="INDETERMINATE")
    verify_candidate_tree(root, migration_id, "docs/teamwork", state["candidate_digest"])
    index = _read_json_relative(root, "docs/teamwork/index.json", "installed v2 index")
    index["migration"] = {
        "migration_id": migration_id,
        "phase": "committed",
        "journal_path": migration_runtime_path(migration_id, "journal.json"),
        "baseline_digest": state["baseline_digest"],
        "report_digest": report_digest,
        "candidate_digest": state["candidate_digest"],
        "archive_manifest_digest": state["archive_manifest_digest"],
    }
    validate_case_index(index)
    _write_json_relative(root, "docs/teamwork/index.json", index)
    detect_teamwork_memory_schema(root)
    verify_candidate_tree(root, migration_id, "docs/teamwork", state["candidate_digest"])
    return index


def _recover_migration_unlocked(root: Path, migration_id_raw: str) -> dict[str, object]:
    migration_id = _migration_id(migration_id_raw)
    recover_transaction(root, migration_marker(migration_id), MIGRATION_PREFIXES, MIGRATION_KIND)
    state = read_migration_json(root, migration_id, "journal.json", optional=True)
    cutover = _load_cutover_journal(root, migration_id)
    if cutover is None:
        return {"migration_id": migration_id, "recovered": False, "phase": None if state is None else state.get("phase")}
    phase = cutover.get("phase")
    old_rel = str(cutover["old_tree"])
    renamed_rel = str(cutover["renamed_old_tree"])
    candidate_rel = str(cutover["candidate_tree"])
    new_rel = str(cutover["new_tree"])
    if state is None:
        fail("missing migration runtime state during cutover recovery", category="INDETERMINATE")
    if phase == "prepared":
        if _safe_dir(root, renamed_rel, optional=True) is None:
            if _safe_dir(root, old_rel, optional=True) is None:
                fail("cutover prepared state lost the old tree", category="INDETERMINATE")
            _rename_dir(root, old_rel, renamed_rel)
        cutover["phase"] = "old_tree_renamed"
        _store_cutover_journal(root, migration_id, cutover)
        phase = "old_tree_renamed"
    if phase == "old_tree_renamed":
        if _safe_dir(root, renamed_rel, optional=True) is None:
            fail("cutover recovery cannot find renamed old tree", category="INDETERMINATE")
        if _safe_dir(root, new_rel, optional=True) is None:
            if _safe_dir(root, candidate_rel, optional=True) is None:
                fail("cutover recovery cannot find candidate or installed new tree", category="INDETERMINATE")
            _rename_dir(root, candidate_rel, new_rel)
        cutover["phase"] = "new_tree_installed"
        _store_cutover_journal(root, migration_id, cutover)
        phase = "new_tree_installed"
    if phase == "new_tree_installed":
        _validate_installed_candidate(root, migration_id, state)
        cutover["phase"] = "committed"
        _store_cutover_journal(root, migration_id, cutover)
        state["phase"] = "committed"
        state["renamed_old_tree"] = renamed_rel
        state["cleanup"] = "pending"
        _write_json_relative(root, migration_runtime_path(migration_id, "journal.json"), state)
        return {"migration_id": migration_id, "recovered": True, "phase": "committed", "renamed_old_tree": renamed_rel}
    if phase == "committed":
        return {"migration_id": migration_id, "recovered": False, "phase": "committed", "renamed_old_tree": renamed_rel}
    fail("cutover recovery found an unknown phase", category="INDETERMINATE")


def recover_migration(root: Path, migration_id_raw: str) -> dict[str, object]:
    with locked_runtime(root):
        return _recover_migration_unlocked(root, migration_id_raw)


def perform_cutover(root: Path, migration_id: str, state: dict[str, object]) -> dict[str, object]:
    if state.get("phase") != "candidate_validated" or state.get("restore_drill") != "passed":
        fail("migration cutover requires candidate validation and restore drill")
    candidate_rel = migration_runtime_path(migration_id, "candidate/docs-teamwork")
    old_rel = "docs/teamwork"
    renamed_rel = migration_runtime_path(migration_id, "renamed-old/docs-teamwork")
    new_rel = "docs/teamwork"
    if _load_cutover_journal(root, migration_id) is not None:
        return _recover_migration_unlocked(root, migration_id)
    _safe_dir(root, candidate_rel)
    _safe_dir(root, old_rel)
    verify_candidate_tree(root, migration_id, candidate_rel, state["candidate_digest"])
    journal = {
        "schema_version": 1,
        "migration_id": migration_id,
        "phase": "prepared",
        "old_tree": old_rel,
        "renamed_old_tree": renamed_rel,
        "candidate_tree": candidate_rel,
        "new_tree": new_rel,
    }
    _store_cutover_journal(root, migration_id, journal)
    migration_failpoint("after-cutover-prepared")
    _rename_dir(root, old_rel, renamed_rel)
    migration_failpoint("after-old-tree-renamed-before-journal")
    journal["phase"] = "old_tree_renamed"
    _store_cutover_journal(root, migration_id, journal)
    migration_failpoint("after-old-tree-renamed")
    _rename_dir(root, candidate_rel, new_rel)
    journal["phase"] = "new_tree_installed"
    _store_cutover_journal(root, migration_id, journal)
    migration_failpoint("after-new-tree-installed")
    _validate_installed_candidate(root, migration_id, state)
    migration_failpoint("after-installed-index-validated-before-journal")
    journal["phase"] = "committed"
    _store_cutover_journal(root, migration_id, journal)
    state["phase"] = "committed"
    state["renamed_old_tree"] = renamed_rel
    state["cleanup"] = "pending"
    _write_json_relative(root, migration_runtime_path(migration_id, "journal.json"), state)
    return {"migration_id": migration_id, "phase": "committed", "renamed_old_tree": renamed_rel}


def _apply_migration_locked(root: Path, request: dict[str, object]) -> dict[str, object]:
    migration_id = str(request["migration_id"])
    marker = migration_marker(migration_id)
    if request["operation"] == "cutover" and _safe_dir(root, "docs/teamwork", optional=True) is None:
        if request.get("cutover_authority") != "I authorize Teamwork memory cutover":
            fail("migration cutover requires explicit cutover authority")
        recovered = _recover_migration_unlocked(root, migration_id)
        return {
            "migration_id": migration_id,
            "phase": recovered.get("phase"),
            "renamed_old_tree": recovered.get("renamed_old_tree"),
            "changed_paths": ["docs/teamwork", str(recovered.get("renamed_old_tree"))],
        }
    with locked_memory(root):
        recover_transaction(root, marker, MIGRATION_PREFIXES, MIGRATION_KIND)
        state = read_migration_json(root, migration_id, "journal.json", optional=True)
        outputs: dict[str, Output] = {}
        created: list[str] = []
        operation = str(request["operation"])
        if operation == "approve-baseline":
            if state is not None:
                fail("migration request was already used")
            state = {
                "schema_version": 1,
                "migration_id": migration_id,
                "phase": "baseline_approved",
                "baseline_digest": request["baseline_digest"],
                "request_ledger": [request["request_digest"]],
                "archive_manifest_digest": None,
                "candidate_digest": None,
                "restore_drill": None,
                "cleanup": None,
            }
            outputs[migration_runtime_path(migration_id, "baseline.json")] = migration_json_output(request["baseline"])
            outputs[migration_runtime_path(migration_id, "journal.json")] = migration_json_output(state)
        else:
            if state is None:
                fail("migration must approve baseline first")
            if state.get("baseline_digest") != request["baseline_digest"]:
                fail("migration baseline digest mismatch")
            ledger = state.get("request_ledger")
            if not isinstance(ledger, list):
                fail("migration request ledger is malformed", category="INDETERMINATE")
            if request["request_digest"] in ledger:
                fail("migration request was already used")
            ledger.append(request["request_digest"])
            phase = state.get("phase")
            if phase not in MIGRATION_PHASES:
                fail("migration phase is invalid", category="INDETERMINATE")
            if operation == "materialize-archive":
                if phase != "baseline_approved":
                    fail("archive materialization requires baseline_approved")
                baseline = read_migration_json(root, migration_id, "baseline.json")
                assert baseline is not None
                baseline = _validate_baseline_payload(baseline)
                objects = []
                for row in baseline.get("paths", []):
                    if not isinstance(row, dict):
                        fail("baseline row is malformed", category="INDETERMINATE")
                    source_path = checked_relative(row.get("path"), "baseline source path")
                    data = _assert_current_file_matches_baseline(root, row)
                    digest = hashlib.sha256(data).hexdigest()
                    object_path = migration_archive_object_path(migration_id, digest)
                    existing = safe_read_bytes(root, object_path, optional=True)
                    if existing is not None:
                        existing_mode = _mode_of(root, object_path)
                        if hashlib.sha256(existing).hexdigest() != digest or len(existing) != len(data) or existing_mode != 0o444:
                            fail("cold archive object hash mismatch", category="INDETERMINATE")
                    if existing is None:
                        outputs[object_path] = Output(data, 0o444)
                    objects.append({"source_path": source_path, "object_path": object_path, "sha256": digest, "mode": row.get("mode"), "size": len(data)})
                manifest = {"schema_version": 1, "migration_id": migration_id, "baseline_digest": request["baseline_digest"], "objects": objects}
                archive_digest = case_digest("archive-manifest", manifest)
                manifest["archive_manifest_digest"] = archive_digest
                state["phase"] = "archive_durable"
                state["archive_manifest_digest"] = archive_digest
                outputs[migration_archive_manifest_path(migration_id)] = migration_json_output(manifest)
                outputs[migration_runtime_path(migration_id, "journal.json")] = migration_json_output(state)
            elif operation == "prepare-candidate":
                if phase != "archive_durable":
                    fail("candidate preparation requires archive_durable")
                baseline = read_migration_json(root, migration_id, "baseline.json")
                assert baseline is not None
                baseline = _validate_baseline_payload(baseline)
                _, _, candidate_outputs, coverage = build_migration_candidate_tree(root, migration_id, state, baseline)
                candidate_digest = str(coverage["candidate_digest"])
                state["phase"] = "candidate_validated"
                state["candidate_digest"] = candidate_digest
                outputs.update(candidate_outputs)
                outputs[migration_runtime_path(migration_id, "journal.json")] = migration_json_output(state)
            elif operation == "restore-drill":
                if phase != "candidate_validated":
                    fail("restore drill requires candidate_validated")
                verify_candidate_tree(root, migration_id, migration_runtime_path(migration_id, "candidate/docs-teamwork"), state["candidate_digest"])
                baseline = read_migration_json(root, migration_id, "baseline.json")
                assert baseline is not None
                baseline = _validate_baseline_payload(baseline)
                archive_raw = safe_read_text(root, migration_archive_manifest_path(migration_id), optional=True)
                if archive_raw is None:
                    fail("archive manifest is missing", category="INDETERMINATE")
                archive = _validate_archive_manifest(_decode_json(archive_raw, "archive manifest"), state, baseline)
                checked = 0
                for row in archive.get("objects", []):
                    if not isinstance(row, dict):
                        fail("archive object row is malformed", category="INDETERMINATE")
                    object_path = checked_relative(row.get("object_path"), "archive object path")
                    data = safe_read_bytes(root, object_path)
                    assert data is not None
                    mode = _mode_of(root, object_path)
                    if (
                        hashlib.sha256(data).hexdigest() != row.get("sha256")
                        or len(data) != row.get("size")
                        or mode != 0o444
                    ):
                        fail("restore drill object digest mismatch", category="INDETERMINATE")
                    checked += 1
                report = {"schema_version": 1, "migration_id": migration_id, "status": "passed", "checked_objects": checked}
                state["restore_drill"] = "passed"
                state["report_digest"] = case_digest("restore-report", report)
                outputs[migration_runtime_path(migration_id, "restore-drill/report.json")] = migration_json_output(report)
                outputs[migration_runtime_path(migration_id, "journal.json")] = migration_json_output(state)
            elif operation == "cutover":
                if request.get("cutover_authority") != "I authorize Teamwork memory cutover":
                    fail("migration cutover requires explicit cutover authority")
                result = perform_cutover(root, migration_id, state)
                return {"migration_id": migration_id, "phase": result["phase"], "renamed_old_tree": result["renamed_old_tree"], "changed_paths": ["docs/teamwork", str(result["renamed_old_tree"])]}
            else:
                if phase != "committed":
                    fail("cleanup requires committed migration state")
                state["phase"] = "cleanup_complete"
                state["cleanup"] = "complete"
                installed_index = _read_json_relative(root, INDEX_PATH, "installed v3 index")
                if installed_index.get("schema_version") == 3 and isinstance(installed_index.get("migration"), dict):
                    migration = dict(installed_index["migration"])
                    if migration.get("migration_id") != migration_id:
                        fail("cleanup migration_id does not match installed index")
                    installed_index = dict(installed_index)
                    installed_index["migration"] = None
                    outputs[INDEX_PATH] = Output(serialize_case_index(installed_index).encode("utf-8"))
                outputs[migration_runtime_path(migration_id, "journal.json")] = migration_json_output(state)
        for path in outputs:
            ensure_directory(root, PurePosixPath(path).parent.as_posix(), created=created)
        apply_transaction(root, kind=MIGRATION_KIND, marker=marker, prefixes=MIGRATION_PREFIXES, outputs=outputs, created_directories=created)
        final = read_migration_json(root, migration_id, "journal.json", optional=True)
        return {"migration_id": migration_id, "phase": None if final is None else final.get("phase"), "changed_paths": sorted(outputs)}


def apply_migration(root: Path, raw_request: dict[str, object]) -> dict[str, object]:
    request = _validate_migration_request(raw_request)
    with locked_runtime(root):
        return _apply_migration_locked(root, request)


def _print(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("case-inspect", "writer-inspect", "project-upgrade", "migration-preflight"):
        child = sub.add_parser(name)
        child.add_argument("--project-root", required=True)
    for name in ("case-schema", "writer-schema", "migration-schema"):
        child = sub.add_parser(name)
        child.add_argument("operation")
    for name in ("case-apply", "writer-apply", "migration-request", "migration-apply"):
        child = sub.add_parser(name)
        child.add_argument("--project-root", required=True)
        group = child.add_mutually_exclusive_group(required=True)
        group.add_argument("--request")
        group.add_argument("--request-json")
    child = sub.add_parser("migration-recover")
    child.add_argument("--project-root", required=True)
    child.add_argument("--migration-id", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        command = arguments.command
        if command == "case-schema":
            _print(case_schema(arguments.operation))
        elif command == "writer-schema":
            _print(writer_schema(arguments.operation))
        elif command == "migration-schema":
            _print(migration_schema(arguments.operation))
        else:
            root = checked_project_root(arguments.project_root)
            if command == "case-inspect":
                _print(inspect_cases(root))
            elif command == "writer-inspect":
                _print(inspect_writer_documents(root))
            elif command == "project-upgrade":
                _print(upgrade_project_documents(root))
            elif command == "migration-preflight":
                _print(migration_preflight(root))
            elif command == "migration-recover":
                _print(recover_migration(root, arguments.migration_id))
            else:
                request = read_request(arguments.request, arguments.request_json)
                if command == "case-apply":
                    _print(apply_case(root, request))
                elif command == "writer-apply":
                    _print(apply_writer(root, request))
                elif command == "migration-request":
                    _print(construct_migration_request(root, request))
                else:
                    _print(apply_migration(root, request))
    except TransactionError as exc:
        print(json.dumps({"ok": False, "category": exc.category, "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
