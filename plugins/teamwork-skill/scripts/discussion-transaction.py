#!/usr/bin/env python3
"""Own the durable Discussion, Design, and Goal artifact transactions.

The command intentionally has a small public surface: inspect -> schema ->
apply.  Markdown is generated from structured state; callers never select an
artifact filename or edit a generated artifact in place.  Every mutation is a
recoverable, journaled transaction with exact preimages.
"""

from __future__ import annotations

import argparse
import base64
import contextlib
import fcntl
import hashlib
import html
import json
import os
import re
import secrets
import stat
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path, PurePosixPath
from typing import Any, Iterator, NoReturn


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
    r"^docs/teamwork/(?:research|plans|workflows/(?:debug|review|conclusion|init|update))/(\d{4}-\d{2}-\d{2})-([a-z0-9]+(?:-[a-z0-9]+)*)\.md$"
)
DISCUSSION_CURRENT = "docs/teamwork/discussion/current.md"
INDEX_PATH = "docs/teamwork/index.json"
DISCUSSION_MARKER = "docs/teamwork/discussion/.discussion-transaction.json"
DESIGN_MARKER = "docs/teamwork/.design-transaction.json"
GOAL_MARKER = "docs/teamwork/.goal-transaction.json"
WORKFLOW_ARTIFACT_MARKER = "docs/teamwork/.workflow-artifact-transaction.json"
CANONICAL_CURRENT = "docs/teamwork/current.md"
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
    "debug": {"kind": "report", "active": "report", "directory": "docs/teamwork/workflows/debug"},
    "review": {"kind": "report", "active": "report", "directory": "docs/teamwork/workflows/review"},
    "conclusion": {"kind": "result", "active": "results", "directory": "docs/teamwork/workflows/conclusion"},
    "init": {"kind": "report", "active": "report", "directory": "docs/teamwork/workflows/init"},
    "update": {"kind": "report", "active": "report", "directory": "docs/teamwork/workflows/update"},
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
FRONTIER_ID_RE = re.compile(r"^Q[1-9][0-9]{0,2}$")
OPTION_ID_RE = re.compile(r"^[a-z][a-z0-9_-]{0,23}$")
FRONTIER_LEVELS = {"goal": 0, "boundary": 1, "detail": 2}
FRONTIER_STATUSES = {"open", "current", "closed", "rejected"}
FRONTIER_MUTABLE_FIELDS = ("prompt", "options", "recommendation", "depends_on", "closure_signal")


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


def normalize_discussion_state(value: object, *, require_status: bool = True) -> dict[str, object]:
    if not isinstance(value, dict):
        fail("Discussion state must be an object")
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


def discussion_route_mermaid(state: dict[str, object]) -> str:
    return discussion_route_mermaid_v2(state) if state.get("schema_version") == 2 else discussion_route_mermaid_v1(state)


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


def discussion_fallback(state: dict[str, object]) -> str:
    return discussion_fallback_v2(state) if state.get("schema_version") == 2 else discussion_fallback_v1(state)


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


def render_discussion_artifact(value: object) -> str:
    state = normalize_discussion_state(value)
    parts = [
            "Artifact Type: discussion",
            f"Status: {state['status']}",
            "Authority: supporting",
            f"Last Updated: {state['updated']}",
            f"Discussion Slug: {state['slug']}",
            f"Superseded By: {state['superseded_by'] or 'none'}",
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
    return json.dumps(left, ensure_ascii=False, sort_keys=True) == json.dumps(right, ensure_ascii=False, sort_keys=True)


def validate_discussion_transition(
    prior: dict[str, object] | None,
    proposed: dict[str, object],
    request: dict[str, object],
    *,
    active_source_text: str | None = None,
) -> dict[str, object]:
    state = normalize_discussion_state_v2(proposed)
    if prior is None:
        return state
    if prior.get("schema_version") != 2:
        enrichments = request.get("legacy_enrichment")
        if not isinstance(enrichments, list):
            fail("active v1 Discussion migration requires legacy_enrichment")
        legacy_open = prior.get("still_open")
        if not isinstance(legacy_open, list):
            fail("active v1 Discussion has no migratable open list")
        seen_indexes: set[int] = set()
        seen_ids: set[str] = set()
        for item in enrichments:
            if not isinstance(item, dict) or not isinstance(item.get("still_open_index"), int) or not isinstance(item.get("frontier_id"), str):
                fail("legacy_enrichment items must map one v1 still_open index to one frontier id")
            index = int(item["still_open_index"])
            if not 0 <= index < len(legacy_open) or index in seen_indexes:
                fail("legacy_enrichment must cover v1 still_open indexes injectively")
            seen_indexes.add(index)
            frontier_id = str(item["frontier_id"])
            if frontier_id in seen_ids:
                fail("legacy_enrichment must map to unique frontier ids")
            seen_ids.add(frontier_id)
            matches = [frontier for frontier in state["frontier"] if frontier["id"] == frontier_id]
            if len(matches) != 1:
                fail("legacy_enrichment frontier_id must exist exactly once in v2 frontier")
        if seen_indexes != set(range(len(legacy_open))):
            fail("legacy_enrichment must cover every v1 still_open item")
        if active_source_text is None:
            fail("active v1 Discussion migration requires exact source text")
        source_path = DISCUSSION_CURRENT
        state["migration_source"] = {
            "path": source_path,
            "sha256": hashlib.sha256(active_source_text.encode("utf-8")).hexdigest(),
            "source_text": active_source_text,
        }
        return normalize_discussion_state_v2(state)
    old = normalize_discussion_state_v2(prior)
    if _frontier_equal(old, state):
        return state
    old_items = _frontier_by_id(old)
    new_items = _frontier_by_id(state)
    missing = set(old_items) - set(new_items)
    if missing:
        fail("Discussion update cannot remove existing frontier ids")
    max_old_id = max((_frontier_number(item_id) for item_id in old_items), default=0)
    for item_id in set(new_items) - set(old_items):
        if _frontier_number(item_id) <= max_old_id:
            fail("Discussion update must allocate monotonically increasing frontier ids")
    old_current = {str(item["id"]) for item in old["frontier"] if item["status"] == "current"}
    if old_current:
        unresolved = [item_id for item_id in old_current if new_items[item_id]["status"] == "current"]
        if unresolved:
            fail("answered-batch update must close or reject every prior-current item")
    for item_id, old_item in old_items.items():
        new_item = new_items[item_id]
        if old_item["status"] in {"closed", "rejected"} and old_item != new_item:
            fail("closed and rejected Discussion frontier items are immutable")
        if old_item["status"] == "open":
            for stable in ("id", "title", "level"):
                if old_item[stable] != new_item[stable]:
                    fail("open Discussion frontier items retain id, title, and level")
            changed_mutable = any(old_item[field] != new_item[field] for field in FRONTIER_MUTABLE_FIELDS)
            if changed_mutable and new_item["status"] == "open":
                reasons = request.get("frontier_delta_reasons")
                if not isinstance(reasons, dict) or not isinstance(reasons.get(item_id), str) or not reasons[item_id].strip():
                    fail("changed open Discussion frontier items require frontier_delta_reasons")
                newly_resolved = [
                    dep for dep in old_item["depends_on"]
                    if dep in new_items and old_items[str(dep)]["status"] in {"open", "current"} and new_items[str(dep)]["status"] == "closed"
                ]
                if not newly_resolved or not any(dep in reasons[item_id] for dep in newly_resolved):
                    fail("frontier_delta_reasons must name a newly resolved dependency")
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
    return _hash(b"discussion-v4", current)


def discussion_active(root: Path) -> dict[str, object] | None:
    text = safe_read_text(root, DISCUSSION_CURRENT, optional=True)
    return None if text is None else validate_discussion_artifact(text)


def discussion_schema(operation: str) -> dict[str, object]:
    if operation not in {"create", "update", "close", "replace", "supersede"}:
        fail("Discussion schema operation must be create, update, close, replace, or supersede")
    record: dict[str, object] = {
        "schema_version": 2,
        "artifact_type": "discussion",
        "slug": "decision-slug",
        "title": "Decision title",
        "updated": "YYYY-MM-DD",
        "goal": "The user outcome this discussion protects.",
        "current_branch": "The current material branch.",
        "return_path": "Resume at the named discriminator.",
        "blockers": ["none recorded"],
        "convergence": "What directly closes this discussion.",
        "key_evidence": ["One compact evidence statement."],
        "frontier": [
            {
                "id": "Q1",
                "title": "Decision route",
                "level": "goal",
                "status": "current" if operation != "close" else "closed",
                "prompt": "Which route should this discussion choose?",
                "options": [
                    {"id": "recommended", "label": "Recommended route", "tradeoff": "Preserves the accepted boundary."},
                    {"id": "alternate", "label": "Alternate route", "tradeoff": "Changes a named constraint."},
                ],
                "recommendation": "recommended",
                "largest_downside": "The recommended route still has one explicit cost.",
                "why_critical": "The answer changes the selected outcome.",
                "blocks": ["selected direction"],
                "depends_on": [],
                "closure_signal": "The user selects one option or rejects the premise.",
                "resolution": None if operation != "close" else {"kind": "selected", "option_id": "recommended"},
            }
        ],
        "current_batch": ["Q1"] if operation != "close" else [],
    }
    return {
        "schema_version": 2,
        "operation": operation,
        "expected_revision": "<revision from inspect>",
        "record": record,
        "close_status": "accepted" if operation == "close" else None,
    }


def schema_template(lifecycle: str) -> dict[str, object]:
    """Backward-compatible import name for the Discussion schema command."""

    return discussion_schema(lifecycle)


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
    merged = {key: value for key, value in old.items() if key not in {"status", "superseded_by", "migration_source"}}
    merged.update(record)
    merged["status"] = "active" if active else merged.get("status", "accepted")
    merged["superseded_by"] = None
    return normalize_discussion_state(merged)


def _superseded_discussion_archive(state: dict[str, object], superseded_by: str) -> dict[str, object]:
    archive = dict(state)
    archive["status"] = "superseded"
    archive["superseded_by"] = superseded_by
    if archive.get("schema_version") == 2:
        frontier = []
        for item in archive["frontier"]:
            next_item = dict(item)
            if next_item["status"] in {"open", "current"}:
                next_item["status"] = "rejected"
                next_item["resolution"] = {"kind": "rejected", "reason": "Superseded by successor discussion."}
            frontier.append(next_item)
        archive["frontier"] = frontier
        archive["current_batch"] = []
        return normalize_discussion_state_v2(archive)
    archive["still_open"] = []
    return normalize_discussion_state_v1(archive)


def inspect_discussion(root: Path) -> dict[str, object]:
    with locked_memory(root):
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
    if request.get("schema_version") != 2:
        fail("Discussion request schema_version must be 2")
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
            if state.get("schema_version") == 2:
                state = validate_discussion_transition(active, state, request, active_source_text=active_text)
            else:
                fail("closing an active v1 Discussion requires a schema v2 migration record")
            if close_status == "superseded":
                state["superseded_by"] = checked_relative(request.get("superseded_by"), "Discussion superseded_by")
            else:
                state["superseded_by"] = None
            state = normalize_discussion_state_v2(state)
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


def _validate_entry(entry: object, position: int) -> dict[str, object]:
    if not isinstance(entry, dict):
        fail(f"entries[{position}] must be an object")
    result = dict(entry)
    for key in ("topic", "kind", "title", "status", "currentness", "authority", "path", "updated", "summary"):
        if key not in result:
            fail(f"entries[{position}] is missing {key}")
    require_text(result["topic"], f"entries[{position}].topic")
    if result["kind"] not in {"result", "progress", "design", "decision", "plan", "report", "research", "runbook"}:
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


def parse_index(text: str) -> dict[str, object]:
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
    allowed = {"current", "design", "plan", "progress", "report", "results"}
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
    for pointer in ("design", "plan", "progress", "report"):
        value = active.get(pointer)
        if value is not None:
            active[pointer] = checked_relative(value, f"active.{pointer}")
            if active[pointer].startswith("docs/teamwork/discussion/"):
                fail(f"active.{pointer} cannot point at Discussion state")
    raw_entries = index.get("entries")
    if not isinstance(raw_entries, list) or not raw_entries:
        fail("Teamwork index entries must be a non-empty array")
    entries = [_validate_entry(item, position) for position, item in enumerate(raw_entries)]
    index = dict(index)
    index["active"] = active
    index["entries"] = entries
    _validate_pointer_metadata(index)
    return index


def _eligible(entry: dict[str, object]) -> bool:
    return (
        entry["status"] in {"active", "accepted"}
        and entry["currentness"] == "current"
        and entry["authority"] in {"canonical", "active-summary", "supporting"}
    )


def _pointer_eligible(pointer: str, entry: dict[str, object]) -> bool:
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
    for path in sorted(_workflow_active_entry_map(index)):
        data = safe_read_bytes(root, path)
        assert data is not None
        parts.append(path.encode("utf-8"))
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
        recover_transaction(root, WORKFLOW_ARTIFACT_MARKER, WORKFLOW_ARTIFACT_PREFIXES, WORKFLOW_ARTIFACT_KIND)
        require_initialized_memory(root)
        index_text, index = _read_index(root)
        validate_currentness(root, index)
        if state["expected_revision"] != workflow_revision(root, index_text, index):
            fail("stale workflow artifact expected_revision; run artifact-inspect again")
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
            _, old_entry = _find_workflow_entry(index, old_path)
            if operation == "update":
                if old_entry.get("workflow") != workflow:
                    fail("update cannot change workflow; use supersede")
                if target != old_path:
                    fail("update cannot change the derived workflow artifact destination; use supersede")
                _replace_index_entry(index, old_path, _workflow_index_entry(state, target, active=True, supersedes=list(old_entry.get("supersedes", []))))
                outputs = {target: Output(render_workflow_artifact(state).encode("utf-8"))}
            else:
                old_slot = _workflow_artifact_slot(str(old_entry["workflow"]))
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


def artifact_index_validate(root: Path) -> dict[str, object]:
    with locked_memory(root):
        recover_transaction(root, DESIGN_MARKER, ("docs/teamwork/design/", INDEX_PATH), "design")
        recover_transaction(root, GOAL_MARKER, ("docs/teamwork/reports/", INDEX_PATH), "goal")
        recover_transaction(root, WORKFLOW_ARTIFACT_MARKER, WORKFLOW_ARTIFACT_PREFIXES, WORKFLOW_ARTIFACT_KIND)
        recover_transaction(root, DISCUSSION_MARKER, ("docs/teamwork/discussion/",), "discussion")
        require_initialized_memory(root)
        _, index = _read_index(root)
        validate_currentness(root, index)
        return {"valid": True}


def _print(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("inspect", "design-inspect", "goal-inspect", "artifact-inspect", "artifact-index-validate"):
        child = sub.add_parser(name)
        child.add_argument("--project-root", required=True)
    child = sub.add_parser("schema")
    child.add_argument("operation")
    for name in ("design-schema", "goal-schema", "artifact-schema"):
        child = sub.add_parser(name)
        child.add_argument("operation")
    for name in ("apply", "design-apply", "goal-apply", "artifact-apply"):
        child = sub.add_parser(name)
        child.add_argument("--project-root", required=True)
        group = child.add_mutually_exclusive_group(required=True)
        group.add_argument("--request")
        group.add_argument("--request-json")
    child = sub.add_parser("design-render")
    child.add_argument("--state-json", required=True)
    child = sub.add_parser("design-validate")
    child.add_argument("--artifact", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        command = arguments.command
        if command == "schema":
            _print(discussion_schema(arguments.operation))
        elif command == "design-schema":
            _print(design_schema(arguments.operation))
        elif command == "goal-schema":
            _print(goal_schema(arguments.operation))
        elif command == "artifact-schema":
            _print(workflow_schema(arguments.operation))
        elif command == "design-render":
            print(render_design_artifact(_decode_json(arguments.state_json, "Design state")), end="")
        elif command == "design-validate":
            path = Path(os.path.abspath(arguments.artifact))
            try:
                info = path.lstat()
                if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
                    fail("Design artifact input must be a regular non-symlink file")
                text = path.read_text(encoding="utf-8")
            except OSError as exc:
                fail(f"cannot read Design artifact input: {exc}")
            _print({"valid": True, "state": validate_design_artifact(text)})
        else:
            root = checked_project_root(arguments.project_root)
            if command == "inspect":
                _print(inspect_discussion(root))
            elif command == "design-inspect":
                _print(inspect_design(root))
            elif command == "goal-inspect":
                _print(inspect_goal(root))
            elif command == "artifact-inspect":
                _print(inspect_workflow_artifacts(root))
            elif command == "artifact-index-validate":
                _print(artifact_index_validate(root))
            else:
                request = read_request(arguments.request, arguments.request_json)
                if command == "apply":
                    _print(apply_discussion(root, request))
                elif command == "design-apply":
                    _print(apply_design(root, request))
                elif command == "goal-apply":
                    _print(apply_goal(root, request))
                else:
                    _print(apply_workflow_artifact(root, request))
    except TransactionError as exc:
        print(json.dumps({"ok": False, "category": exc.category, "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
