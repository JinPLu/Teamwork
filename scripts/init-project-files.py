#!/usr/bin/env python3
"""Initialize Teamwork project files through an inherited, locked FD tree.

The caller must enter the discussion transaction guard first and pass its four
directory descriptors.  Project files are never reopened through a project-root
path; the retained descriptors remain authoritative even if a directory name is
replaced while this process is running.
"""

from __future__ import annotations

import argparse
import errno
import fcntl
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path, PurePosixPath
from typing import NoReturn

import validate_teamwork_index as validator


GUARD_ENV = {
    "root": "TEAMWORK_DISCUSSION_GUARD_ROOT_FD",
    "docs": "TEAMWORK_DISCUSSION_GUARD_DOCS_FD",
    "teamwork": "TEAMWORK_DISCUSSION_GUARD_TEAMWORK_FD",
    "lock": "TEAMWORK_DISCUSSION_GUARD_LOCK_FD",
}
TOKEN_ENV = "TEAMWORK_DISCUSSION_GUARD_TOKEN"
MARKER = ".discussion-transaction.json"
INIT_MARKER = ".teamwork-init-transaction.json"
INIT_MARKER_TEMP_RE = re.compile(r"^\.teamwork-init-transaction\.json\.teamwork-init-marker-[0-9]+-[0-9]+$")
CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")


class InitError(Exception):
    pass


def fail(message: str) -> NoReturn:
    raise InitError(message)


def identity(info: os.stat_result) -> tuple[int, int, int]:
    return info.st_dev, info.st_ino, stat.S_IFMT(info.st_mode)


def fd_number(name: str) -> int:
    raw = os.environ.get(name)
    if raw is None:
        fail(f"missing inherited guard variable: {name}")
    try:
        value = int(raw)
    except ValueError:
        fail(f"inherited guard variable is not a file descriptor: {name}")
    if value < 0:
        fail(f"inherited guard variable is not a file descriptor: {name}")
    return value


class GuardFds:
    """Borrow and validate the caller-owned guard descriptors."""

    def __init__(self) -> None:
        if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
            fail("platform lacks required descriptor-relative no-follow operations")
        token = os.environ.get(TOKEN_ENV, "")
        if len(token) != 64 or any(char not in "0123456789abcdef" for char in token):
            fail("inherited guard token is malformed")
        self.fds = {key: fd_number(name) for key, name in GUARD_ENV.items()}
        try:
            self.stats = {key: os.fstat(fd) for key, fd in self.fds.items()}
        except OSError as exc:
            fail(f"cannot inspect inherited guard descriptor: {exc}")
        for key, info in self.stats.items():
            if not stat.S_ISDIR(info.st_mode):
                fail(f"inherited {key} descriptor is not a directory")
        devices = {info.st_dev for info in self.stats.values()}
        if len(devices) != 1:
            fail("inherited guard descriptors cross devices")
        if identity(self.stats["teamwork"]) != identity(self.stats["lock"]):
            fail("inherited lock descriptor does not identify docs/teamwork")
        self.device = self.stats["root"].st_dev
        self._require_lock()
        self.require_no_marker()
        recover_init_transaction(self)
        self.require_no_marker()

    def _require_lock(self) -> None:
        try:
            fcntl.flock(self.fds["lock"], fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            fail(f"inherited lock descriptor does not own the guard lock: {exc}")
        probe = os.open(
            ".",
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
            dir_fd=self.fds["teamwork"],
        )
        try:
            try:
                fcntl.flock(probe, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                if exc.errno not in (errno.EACCES, errno.EAGAIN):
                    fail(f"cannot verify inherited guard lock: {exc}")
            else:
                fcntl.flock(probe, fcntl.LOCK_UN)
                fail("inherited guard lock is not held")
        finally:
            os.close(probe)

    def require_no_marker(self) -> None:
        try:
            info = os.stat(MARKER, dir_fd=self.fds["teamwork"], follow_symlinks=False)
        except FileNotFoundError:
            return
        except OSError as exc:
            fail(f"cannot determine discussion transaction marker state: {exc}")
        fail("an unfinished discussion transaction marker exists")

    def verify_retained(self) -> None:
        for key, fd in self.fds.items():
            try:
                now = os.fstat(fd)
            except OSError as exc:
                fail(f"retained {key} descriptor became invalid: {exc}")
            if identity(now) != identity(self.stats[key]) or now.st_dev != self.device:
                fail(f"retained {key} descriptor changed identity")
        self.require_no_marker()


def _safe_name(name: str) -> None:
    if not name or name in {".", ".."} or "/" in name or "\0" in name:
        fail(f"unsafe project entry name: {name!r}")


def entry_stat(parent_fd: int, name: str) -> os.stat_result | None:
    _safe_name(name)
    try:
        return os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return None
    except OSError as exc:
        fail(f"cannot inspect project entry {name}: {exc}")


def open_dir(parent_fd: int, name: str, device: int, *, create: bool = False) -> int:
    before = entry_stat(parent_fd, name)
    if before is None:
        if not create:
            fail(f"missing project directory: {name}")
        try:
            os.mkdir(name, 0o755, dir_fd=parent_fd)
            os.fsync(parent_fd)
        except OSError as exc:
            fail(f"cannot create project directory {name}: {exc}")
        before = entry_stat(parent_fd, name)
    assert before is not None
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISDIR(before.st_mode):
        fail(f"project entry must be a non-symlink directory: {name}")
    if before.st_dev != device:
        fail(f"project directory crosses the root device: {name}")
    try:
        fd = os.open(
            name,
            os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
            dir_fd=parent_fd,
        )
    except OSError as exc:
        fail(f"cannot safely open project directory {name}: {exc}")
    opened = os.fstat(fd)
    if identity(opened) != identity(before) or opened.st_dev != device:
        os.close(fd)
        fail(f"project directory changed identity while opening: {name}")
    return fd


def read_file(parent_fd: int, name: str, logical: str, *, required: bool = True) -> tuple[bytes, int] | None:
    before = entry_stat(parent_fd, name)
    if before is None:
        if required:
            fail(f"missing project file: {logical}")
        return None
    if (
        stat.S_ISLNK(before.st_mode)
        or not stat.S_ISREG(before.st_mode)
        or before.st_nlink != 1
    ):
        fail(f"project file must be a single-link non-symlink regular file: {logical}")
    try:
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent_fd)
    except OSError as exc:
        fail(f"cannot safely open project file {logical}: {exc}")
    try:
        opened = os.fstat(fd)
        if identity(opened) != identity(before) or opened.st_nlink != 1:
            fail(f"project file changed identity while opening: {logical}")
        chunks: list[bytes] = []
        while chunk := os.read(fd, 1024 * 1024):
            chunks.append(chunk)
        final = os.fstat(fd)
        current = entry_stat(parent_fd, name)
        if current is None or identity(final) != identity(opened) or identity(current) != identity(opened):
            fail(f"project file changed identity while reading: {logical}")
        return b"".join(chunks), stat.S_IMODE(opened.st_mode)
    finally:
        os.close(fd)


def read_text(parent_fd: int, name: str, logical: str, *, required: bool = True) -> tuple[str, int] | None:
    result = read_file(parent_fd, name, logical, required=required)
    if result is None:
        return None
    data, mode = result
    try:
        return data.decode("utf-8"), mode
    except UnicodeDecodeError as exc:
        fail(f"project file must be UTF-8: {logical}: {exc}")


@dataclass
class Change:
    parent_fd: int
    name: str
    logical: str
    before: bytes | None
    mode: int
    after: bytes
    stage: str | None = None
    backup: str | None = None


def _change_parent_key(guard: GuardFds, change: Change) -> str:
    current = identity(os.fstat(change.parent_fd))
    for key in ("root", "teamwork"):
        if current == identity(guard.stats[key]):
            return key
    if change.logical.startswith("docs/teamwork/discussion/"):
        return "discussion"
    fail(f"cannot journal unknown init output parent: {change.logical}")


def _journal_parent_fd(guard: GuardFds, parent: object) -> tuple[int, bool]:
    if parent in {"root", "teamwork"}:
        return guard.fds[str(parent)], False
    if parent == "discussion":
        return open_dir(guard.fds["teamwork"], "discussion", guard.device), True
    fail("init transaction journal has an invalid parent")


def _safe_temp(value: object, *, optional: bool = False) -> str | None:
    if optional and value is None:
        return None
    if not isinstance(value, str) or re.fullmatch(r"\..+\.teamwork-init-(?:stage|backup)-[0-9]+-[0-9]+", value) is None:
        fail("init transaction journal has an invalid temporary name")
    return value


def _write_init_marker(guard: GuardFds, journal: dict[str, object]) -> None:
    data = json.dumps(journal, sort_keys=True, separators=(",", ":")).encode() + b"\n"
    temp: str | None = None
    for ordinal in range(1000):
        candidate = f"{INIT_MARKER}.teamwork-init-marker-{os.getpid()}-{ordinal}"
        if entry_stat(guard.fds["teamwork"], candidate) is None:
            temp = candidate
            break
    if temp is None:
        fail("cannot reserve init transaction marker temporary name")
    _write_temp(guard.fds["teamwork"], temp, data, 0o600)
    try:
        os.replace(temp, INIT_MARKER, src_dir_fd=guard.fds["teamwork"], dst_dir_fd=guard.fds["teamwork"])
        temp = None
        os.fsync(guard.fds["teamwork"])
    finally:
        if temp is not None:
            try:
                os.unlink(temp, dir_fd=guard.fds["teamwork"])
            except FileNotFoundError:
                pass


def _read_init_marker(guard: GuardFds) -> dict[str, object] | None:
    result = read_file(guard.fds["teamwork"], INIT_MARKER, f"docs/teamwork/{INIT_MARKER}", required=False)
    if result is None:
        return None
    raw, mode = result
    if mode != 0o600:
        fail("init transaction marker must have mode 0600")
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        fail(f"init transaction marker is malformed: {exc}")
    if not isinstance(value, dict) or set(value) != {"schema_version", "owner", "phase", "changes"}:
        fail("init transaction marker has invalid fields")
    if value["schema_version"] != 1 or value["owner"] != "teamwork-init":
        fail("init transaction marker has an invalid owner or schema")
    if value["phase"] not in {"preparing", "prepared", "committed"} or not isinstance(value["changes"], list):
        fail("init transaction marker has an invalid phase or change list")
    return value


def _remove_temp(parent_fd: int, name: str | None) -> None:
    if name is None:
        return
    try:
        info = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        fail("init transaction temporary entry is unsafe")
    os.unlink(name, dir_fd=parent_fd)


def _clear_init_marker(guard: GuardFds, journal: dict[str, object]) -> None:
    os.unlink(INIT_MARKER, dir_fd=guard.fds["teamwork"])
    try:
        os.fsync(guard.fds["teamwork"])
    except OSError as original:
        try:
            _write_init_marker(guard, journal)
        except BaseException as restore:
            fail(f"init marker deletion durability failed and marker restore failed: {original}; {restore}")
        fail(f"init marker deletion was not durably confirmed: {original}")


def _recover_init_journal(guard: GuardFds, journal: dict[str, object]) -> None:
    phase = journal["phase"]
    records = journal["changes"]
    assert isinstance(records, list)
    fsync_at_raw = os.environ.get("TEAMWORK_TEST_FAIL_INIT_RECOVERY_PARENT_FSYNC_AT")
    try:
        fsync_at = None if fsync_at_raw is None else int(fsync_at_raw)
    except ValueError:
        fail("recovery parent fsync failure injection must be an integer")
    fsync_count = 0

    def sync_parent(fd: int) -> None:
        nonlocal fsync_count
        fsync_count += 1
        if fsync_at == fsync_count:
            raise OSError(f"injected recovery parent fsync failure at {fsync_count}")
        os.fsync(fd)

    plans: list[dict[str, object]] = []
    retained_parents: list[int] = []
    seen_targets: set[tuple[object, str]] = set()
    seen_temps: set[tuple[object, str]] = set()
    seen_temp_identities: set[tuple[int, int]] = set()
    try:
        # Pass 1 is strictly read-only. A malformed or unknown record must not
        # make recovery partially apply any other record.
        for raw in reversed(records):
            if not isinstance(raw, dict) or set(raw) != {
                "parent", "name", "logical", "before_sha256", "before_mode",
                "after_sha256", "after_mode", "stage", "backup",
                "stage_device", "stage_inode", "backup_device", "backup_inode",
            }:
                fail("init transaction journal has a malformed change record")
            name = raw["name"]
            parent = raw["parent"]
            logical = raw["logical"]
            if not isinstance(name, str) or not name or "/" in name or name in {".", ".."}:
                fail("init transaction journal has an invalid target name")
            expected_logical = {
                "root": name,
                "teamwork": f"docs/teamwork/{name}",
                "discussion": f"docs/teamwork/discussion/{name}",
            }.get(parent)
            if expected_logical is None or logical != expected_logical:
                fail("init transaction journal parent and logical path do not agree")
            allowed = (
                (parent == "root" and name in {"AGENTS.md", ".gitignore"})
                or (parent == "teamwork" and name in {"README.md", "current.md", "index.json"})
                or (
                    parent == "discussion"
                    and re.fullmatch(
                        r"[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9]+(?:-[a-z0-9]+)*\.md",
                        name,
                    ) is not None
                )
            )
            if not allowed:
                fail("init transaction journal target is outside the init allowlist")
            target = (parent, name)
            if target in seen_targets:
                fail("init transaction journal contains a duplicate target")
            seen_targets.add(target)
            before_hash = raw["before_sha256"]
            after_hash = raw["after_sha256"]
            before_mode = raw["before_mode"]
            after_mode = raw["after_mode"]
            if before_hash is not None and (not isinstance(before_hash, str) or re.fullmatch(r"[0-9a-f]{64}", before_hash) is None):
                fail("init transaction journal has an invalid preimage hash")
            if not isinstance(after_hash, str) or re.fullmatch(r"[0-9a-f]{64}", after_hash) is None:
                fail("init transaction journal has an invalid output hash")
            if before_mode is not None and (not isinstance(before_mode, int) or not 0 <= before_mode <= 0o7777):
                fail("init transaction journal has an invalid preimage mode")
            if not isinstance(after_mode, int) or not 0 <= after_mode <= 0o7777:
                fail("init transaction journal has an invalid output mode")
            stage = _safe_temp(raw["stage"])
            backup = _safe_temp(raw["backup"], optional=True)
            assert isinstance(stage, str)
            if re.fullmatch(
                rf"\.{re.escape(name)}\.teamwork-init-stage-[0-9]+-[0-9]+",
                stage,
            ) is None:
                fail("init transaction stage name is not bound to its target")
            if backup is not None and re.fullmatch(
                rf"\.{re.escape(name)}\.teamwork-init-backup-[0-9]+-[0-9]+",
                backup,
            ) is None:
                fail("init transaction backup name is not bound to its target")
            for temp_name in (stage, backup):
                if temp_name is None:
                    continue
                resource = (parent, temp_name)
                if resource in seen_temps:
                    fail("init transaction journal reuses a temporary resource")
                seen_temps.add(resource)
            stage_identity = (raw["stage_device"], raw["stage_inode"])
            backup_identity = (raw["backup_device"], raw["backup_inode"])
            for label, saved_identity in (("stage", stage_identity), ("backup", backup_identity)):
                if saved_identity != (None, None) and not all(isinstance(part, int) and part >= 0 for part in saved_identity):
                    fail(f"init transaction journal has an invalid {label} identity")
                if saved_identity != (None, None):
                    assert isinstance(saved_identity[0], int) and isinstance(saved_identity[1], int)
                    if saved_identity in seen_temp_identities:
                        fail("init transaction journal reuses a temporary inode")
                    seen_temp_identities.add(saved_identity)
            if phase in {"prepared", "committed"} and stage_identity == (None, None):
                fail("prepared init transaction is missing a staged-file identity")
            if before_hash is None:
                if before_mode is not None or backup is not None or backup_identity != (None, None):
                    fail("absent init preimage has unexpected backup metadata")
            elif phase in {"prepared", "committed"} and (backup is None or backup_identity == (None, None)):
                fail("prepared init transaction is missing a backup identity")
            parent_fd, close_parent = _journal_parent_fd(guard, parent)
            if close_parent:
                retained_parents.append(parent_fd)
            current = read_file(parent_fd, name, logical, required=False)
            current_info = entry_stat(parent_fd, name)
            current_hash = None if current is None else hashlib.sha256(current[0]).hexdigest()
            current_state: str
            if current_hash == after_hash and current is not None and current[1] == after_mode:
                if current_info is None or (current_info.st_dev, current_info.st_ino) != stage_identity:
                    fail("init transaction output inode does not match its staged file")
                current_state = "after"
            elif current_hash == before_hash and (current is None or current[1] == before_mode):
                current_state = "before"
            else:
                fail("init transaction target changed outside the guarded transaction")
            if phase == "committed" and current_state != "after":
                fail("committed init transaction output changed before recovery cleanup")
            stage_info = entry_stat(parent_fd, stage)
            if stage_info is not None and (
                stage_identity == (None, None)
                or (stage_info.st_dev, stage_info.st_ino) != stage_identity
            ):
                fail("init transaction temporary inode does not match its journal")
            backup_info = None if backup is None else entry_stat(parent_fd, backup)
            if backup_info is not None:
                if (backup_info.st_dev, backup_info.st_ino) != backup_identity:
                    fail("init transaction backup inode does not match its journal")
                saved = read_file(parent_fd, backup, logical, required=True)
                assert saved is not None
                if hashlib.sha256(saved[0]).hexdigest() != before_hash or saved[1] != before_mode:
                    fail("init transaction backup does not match its recorded preimage")
            if phase != "committed" and current_state == "after" and before_hash is not None and backup_info is None:
                fail("init transaction recovery requires its recorded backup")
            plans.append({
                "raw": raw,
                "parent_fd": parent_fd,
                "current_state": current_state,
                "stage": stage,
                "backup": backup,
                "stage_identity": stage_identity,
                "backup_identity": backup_identity,
            })

        # Pass 2 mutates only after every record and observed object is proven.
        for plan in plans:
            raw = plan["raw"]
            assert isinstance(raw, dict)
            parent_fd = plan["parent_fd"]
            assert isinstance(parent_fd, int)
            name = raw["name"]
            logical = raw["logical"]
            assert isinstance(name, str) and isinstance(logical, str)
            stage = plan["stage"]
            backup = plan["backup"]
            stage_identity = plan["stage_identity"]
            backup_identity = plan["backup_identity"]
            assert isinstance(stage, str) and isinstance(stage_identity, tuple) and isinstance(backup_identity, tuple)
            if plan["current_state"] == "after" and phase != "committed":
                current_info = entry_stat(parent_fd, name)
                if current_info is None or (current_info.st_dev, current_info.st_ino) != stage_identity:
                    fail("init transaction output changed after recovery validation")
                if raw["before_sha256"] is None:
                    os.unlink(name, dir_fd=parent_fd)
                else:
                    assert isinstance(backup, str)
                    saved_info = entry_stat(parent_fd, backup)
                    saved = read_file(parent_fd, backup, logical, required=True)
                    if (
                        saved_info is None
                        or (saved_info.st_dev, saved_info.st_ino) != backup_identity
                        or saved is None
                        or hashlib.sha256(saved[0]).hexdigest() != raw["before_sha256"]
                        or saved[1] != raw["before_mode"]
                    ):
                        fail("init transaction backup changed after recovery validation")
                    os.replace(backup, name, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
                    backup = None
                sync_parent(parent_fd)
            for temp_name, expected_identity in ((stage, stage_identity), (backup, backup_identity)):
                if temp_name is None:
                    continue
                assert isinstance(temp_name, str) and isinstance(expected_identity, tuple)
                temp_info = entry_stat(parent_fd, temp_name)
                if temp_info is None:
                    continue
                if expected_identity == (None, None) or (temp_info.st_dev, temp_info.st_ino) != expected_identity:
                    fail("init transaction temporary changed after recovery validation")
                _remove_temp(parent_fd, temp_name)
            sync_parent(parent_fd)
        _clear_init_marker(guard, journal)
    finally:
        for parent_fd in retained_parents:
            os.close(parent_fd)


def recover_init_transaction(guard: GuardFds) -> None:
    journal = _read_init_marker(guard)
    if journal is not None:
        try:
            _recover_init_journal(guard, journal)
        except OSError as exc:
            fail(f"init transaction recovery was not durably completed; journal preserved: {exc}")
    if any(INIT_MARKER_TEMP_RE.fullmatch(name) for name in os.listdir(guard.fds["teamwork"])):
        fail("an untracked init marker temporary file exists; recovery cannot prove its identity")


def _temp_name(parent_fd: int, base: str, role: str) -> str:
    for ordinal in range(1000):
        name = f".{base}.teamwork-init-{role}-{os.getpid()}-{ordinal}"
        if entry_stat(parent_fd, name) is None:
            return name
    fail(f"cannot reserve temporary name for {base}")


def _write_temp(parent_fd: int, name: str, data: bytes, mode: int) -> None:
    try:
        fd = os.open(
            name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            mode,
            dir_fd=parent_fd,
        )
        try:
            os.fchmod(fd, mode)
            offset = 0
            while offset < len(data):
                offset += os.write(fd, data[offset:])
            os.fsync(fd)
        finally:
            os.close(fd)
    except OSError as exc:
        try:
            os.unlink(name, dir_fd=parent_fd)
        except OSError:
            pass
        fail(f"cannot stage project file: {exc}")


def apply_changes(guard: GuardFds, changes: list[Change], *, migration: bool = False) -> None:
    changes = [change for change in changes if change.before != change.after]
    if not changes:
        return
    fail_at_raw = os.environ.get(
        "TEAMWORK_TEST_FAIL_MIGRATION_REPLACE_AT" if migration else "TEAMWORK_TEST_FAIL_INIT_REPLACE_AT"
    )
    hard_exit_raw = os.environ.get(
        "TEAMWORK_TEST_HARD_EXIT_MIGRATION_REPLACE_AT" if migration else "TEAMWORK_TEST_HARD_EXIT_INIT_REPLACE_AT"
    )
    fail_at: int | None = None
    if fail_at_raw is not None:
        try:
            fail_at = int(fail_at_raw)
        except ValueError:
            fail("replacement failure injection must be an integer")
        if not 1 <= fail_at <= len(changes):
            fail("replacement failure injection is outside the planned replacements")
    hard_exit_at: int | None = None
    if hard_exit_raw is not None:
        try:
            hard_exit_at = int(hard_exit_raw)
        except ValueError:
            fail("hard-exit replacement injection must be an integer")
        if not 1 <= hard_exit_at <= len(changes):
            fail("hard-exit replacement injection is outside the planned replacements")
    records: list[dict[str, object]] = []
    for change in changes:
        change.stage = _temp_name(change.parent_fd, change.name, "stage")
        change.backup = None if change.before is None else _temp_name(change.parent_fd, change.name, "backup")
        records.append({
            "parent": _change_parent_key(guard, change),
            "name": change.name,
            "logical": change.logical,
            "before_sha256": None if change.before is None else hashlib.sha256(change.before).hexdigest(),
            "before_mode": None if change.before is None else change.mode,
            "after_sha256": hashlib.sha256(change.after).hexdigest(),
            "after_mode": change.mode,
            "stage": change.stage,
            "backup": change.backup,
            "stage_device": None,
            "stage_inode": None,
            "backup_device": None,
            "backup_inode": None,
        })
    journal: dict[str, object] = {
        "schema_version": 1,
        "owner": "teamwork-init",
        "phase": "preparing",
        "changes": records,
    }
    _write_init_marker(guard, journal)
    hard_phase = os.environ.get("TEAMWORK_TEST_HARD_EXIT_INIT_PHASE")
    if hard_phase == "preparing":
        os._exit(86)
    try:
        for change, record in zip(changes, records):
            assert change.stage is not None
            _write_temp(change.parent_fd, change.stage, change.after, change.mode)
            stage_info = entry_stat(change.parent_fd, change.stage)
            assert stage_info is not None
            record["stage_device"], record["stage_inode"] = stage_info.st_dev, stage_info.st_ino
            _write_init_marker(guard, journal)
            if change.before is not None:
                assert change.backup is not None
                _write_temp(change.parent_fd, change.backup, change.before, change.mode)
                backup_info = entry_stat(change.parent_fd, change.backup)
                assert backup_info is not None
                record["backup_device"], record["backup_inode"] = backup_info.st_dev, backup_info.st_ino
                _write_init_marker(guard, journal)
            os.fsync(change.parent_fd)
        journal["phase"] = "prepared"
        _write_init_marker(guard, journal)
        if hard_phase == "prepared":
            os._exit(86)
        for ordinal, change in enumerate(changes, start=1):
            current = read_file(change.parent_fd, change.name, change.logical, required=False)
            current_bytes = None if current is None else current[0]
            current_mode = change.mode if current is None else current[1]
            if current_bytes != change.before or (current is not None and current_mode != change.mode):
                fail(f"project file changed during transaction preparation: {change.logical}")
            if fail_at == ordinal:
                raise OSError(f"injected init replacement failure at {ordinal}")
            assert change.stage is not None
            if change.before is None:
                os.link(
                    change.stage,
                    change.name,
                    src_dir_fd=change.parent_fd,
                    dst_dir_fd=change.parent_fd,
                    follow_symlinks=False,
                )
                os.unlink(change.stage, dir_fd=change.parent_fd)
            else:
                os.replace(
                    change.stage,
                    change.name,
                    src_dir_fd=change.parent_fd,
                    dst_dir_fd=change.parent_fd,
                )
            change.stage = None
            if hard_exit_at == ordinal:
                os._exit(86)
            os.fsync(change.parent_fd)
        for change in changes:
            final = read_file(change.parent_fd, change.name, change.logical)
            assert final is not None
            if final != (change.after, change.mode):
                fail(f"init transaction readback differs from intended output: {change.logical}")
        journal["phase"] = "committed"
        _write_init_marker(guard, journal)
        if hard_phase == "committed":
            os._exit(86)
        for change in changes:
            _remove_temp(change.parent_fd, change.backup)
            change.backup = None
            os.fsync(change.parent_fd)
        if hard_phase == "cleanup":
            os._exit(86)
        _clear_init_marker(guard, journal)
    except BaseException as original:
        try:
            current_journal = _read_init_marker(guard)
            if current_journal is None:
                fail("init transaction marker disappeared during failure handling")
            _recover_init_journal(guard, current_journal)
        except BaseException as rollback:
            fail(f"init transaction failed and rollback was incomplete; journal preserved: {original}; {rollback}")
        if isinstance(original, InitError):
            raise
        if current_journal["phase"] == "committed":
            fail(f"init transaction committed; durable cleanup completed after failure: {original}")
        if migration:
            fail(f"atomic migration commit failed and was rolled back: {original}")
        fail(f"init transaction failed and was rolled back: {original}")


def change_for(parent_fd: int, name: str, logical: str, text: str, *, missing_mode: int = 0o644) -> Change:
    current = read_file(parent_fd, name, logical, required=False)
    before = None if current is None else current[0]
    mode = missing_mode if current is None else current[1]
    return Change(parent_fd, name, logical, before, mode, text.encode("utf-8"))


LEGACY_RUNTIME_READ_ORDERS = (
    """## Read Order

1. Read `docs/teamwork/index.json` first.
2. Follow `active.current`, then `active.discussion` when present, then the other `active` pointers before any broad scan.
3. Prefer headers before full artifact bodies.
4. Use stage-specific profiles from the index.""",
    """## Read Order

1. Read `docs/teamwork/index.json` first.
2. Follow `active.current`, then `active.discussion` when present, then the
   other `active` pointers before any broad scan.
3. Prefer headers before full artifact bodies.
4. Use stage-specific profiles from the index.""",
)
LEGACY_RUNTIME_DISCUSSION_NOTE = "- `discussion`: read the active discussion before continuing dependent work."
CURRENT_RUNTIME_READ_ORDER = """## Read Order

1. For Grill/discussion continuation, load `grill-me`, resolve the installed
   `scripts/discussion-transaction.py` from the loaded `using-teamwork` skill,
   and run `inspect` from the project root first.
   Its result is the sole discussion read path.
   For that continuation, do not directly read `index.json`,
   `current.md`, this README, or a discussion artifact.
2. For ordinary non-discussion memory, read `docs/teamwork/index.json` first,
   then this README.
3. Follow `active.current` and other non-discussion `active` pointers before
   any broad scan.
4. Prefer headers before full artifact bodies and use the stage-specific
   profiles from the index."""
CURRENT_RUNTIME_DISCUSSION_NOTE = """- `discussion`: use the helper's `inspect` result; never open
  `active.discussion` or its artifact directly."""


def migrate_readme_routing(text: str) -> str:
    matching = [block for block in LEGACY_RUNTIME_READ_ORDERS if text.count(block) == 1]
    legacy = "Follow `active.current`, then `active.discussion`" in text or LEGACY_RUNTIME_DISCUSSION_NOTE in text
    if not legacy:
        return text
    if (
        len(matching) != 1
        or text.count(LEGACY_RUNTIME_DISCUSSION_NOTE) != 1
        or CURRENT_RUNTIME_READ_ORDER in text
        or CURRENT_RUNTIME_DISCUSSION_NOTE in text
    ):
        fail("unsupported or customized legacy runtime README retrieval blocks; no migration files were changed")
    return text.replace(matching[0], CURRENT_RUNTIME_READ_ORDER, 1).replace(
        LEGACY_RUNTIME_DISCUSSION_NOTE, CURRENT_RUNTIME_DISCUSSION_NOTE, 1
    )


def ensure_anchor(text: str, marker: str, value: str, suffix: str = "") -> str:
    lines = text.splitlines(keepends=True)
    expected = f"{marker} {value}{suffix}"
    matches = [index for index, line in enumerate(lines) if line.rstrip("\r\n").startswith(marker)]
    if len(matches) == 1 and lines[matches[0]].rstrip("\r\n") == expected:
        return text
    newline = "\r\n" if any(line.endswith("\r\n") for line in lines) else "\n"
    result: list[str] = []
    written = False
    for line in lines:
        if line.rstrip("\r\n").startswith(marker):
            if written:
                continue
            ending = line[len(line.rstrip("\r\n")) :]
            result.append(expected + ending)
            written = True
        else:
            result.append(line)
    updated = "".join(result)
    if not written:
        if updated and not updated.endswith(("\n", "\r")):
            updated += newline
        updated += expected + newline
    return updated


LEGACY_SECTIONS = (
    "Starting Question", "Decision State", "Route Map", "Textual Playback", "Update Rules"
)
LEGACY_INTRO = """This artifact supports continuity for a long, cross-context, handoff-sensitive,
or materially branching Grill. It is not a transcript and grants no execution
authority."""
LEGACY_ROUTE_GUIDANCE = """Show the full material route, including every settled, open, and rejected
branch. Use artifact-local node keys such as `R1`, include textual status in
every node, and keep detailed evidence and outcomes in Decision State rather
than duplicating them here."""
LEGACY_PLAYBACK_GUIDANCE = """Concise chronological recovery of the route: starting question, evidence or
decision that changed each material branch, current settled/open/rejected state,
and the exact point at which to resume. This complements the Route Map; do not
reproduce dialogue or a raw transcript."""
LEGACY_UPDATE_RULES = """Update only at a material checkpoint: a decision changes or closes a branch,
evidence materially changes a route, the mainline changes, continuity is about
to cross a context or handoff boundary, or the discussion is promoted or
superseded. Do not update per turn. Store decision-relevant, privacy-safe
summaries only; exclude raw transcripts, hidden reasoning, secrets, and
unnecessary personal data. Promotion does not grant execution authority."""


def normalized(text: str) -> str:
    return " ".join(text.split())


def valid_legacy_route_map(section: str) -> bool:
    fences = list(re.finditer(r"```mermaid\s*\n(?P<diagram>.*?)```", section, re.S))
    if len(fences) != 1:
        return False
    fence = fences[0]
    outside = (section[: fence.start()] + section[fence.end() :]).strip()
    if normalized(outside) != normalized(LEGACY_ROUTE_GUIDANCE):
        return False
    diagram = fence.group("diagram")
    if re.search(r"(?m)^\s*flowchart(?:\s+(?:TB|TD|BT|RL|LR))?\s*$", diagram) is None:
        return False
    nodes = re.findall(r'(?m)^\s*(R[1-9][0-9]*)\s*\["([^"]+)"\]\s*$', diagram)
    if not nodes:
        return False
    keys = [key for key, _ in nodes]
    if len(keys) != len(set(keys)):
        return False
    defined = set(keys)
    for edge in re.findall(r"(?m)^\s*(R[1-9][0-9]*)\s*-->\s*(R[1-9][0-9]*)\s*$", diagram):
        if any(key not in defined for key in edge):
            return False
    for key, label in nodes:
        if not normalized(label).casefold().startswith(key.casefold() + " "):
            return False
        if re.search(r"(?i)\b(?:evidence|outcome|reason|mainline impact)\s*:", label):
            return False
    return True


def _section_fields(section: str, labels: tuple[str, ...]) -> dict[str, str] | None:
    observed = tuple(re.findall(r"(?m)^- ([^:\n]+):", section))
    if observed != labels:
        return None
    values: dict[str, str] = {}
    for index, label in enumerate(labels):
        next_label = labels[index + 1] if index + 1 < len(labels) else None
        pattern = rf"(?ms)^- {re.escape(label)}:[ \t]*(.*?)(?=^- {re.escape(next_label)}:|\Z)" if next_label else rf"(?ms)^- {re.escape(label)}:[ \t]*(.*?)\s*\Z"
        match = re.search(pattern, section)
        if not match or not match.group(1).strip():
            return None
        values[label] = match.group(1).strip()
    return values


def looks_legacy_discussion(text: str) -> bool:
    return "# Teamwork Discussion" in text or sum(
        heading in text for heading in ("## Starting Question", "## Decision State", "## Route Map")
    ) >= 3


def migrate_legacy_discussion(text: str) -> str | None:
    h1s = list(re.finditer(r"(?m)^# ([^\n]+?)\s*$", text))
    headings = list(re.finditer(r"(?m)^## ([^\n]+?)\s*$", text))
    if len(h1s) != 1 or h1s[0].group(1) != "Teamwork Discussion":
        return None
    if tuple(match.group(1) for match in headings) != LEGACY_SECTIONS:
        return None
    if normalized(text[h1s[0].end() : headings[0].start()].strip()) != normalized(LEGACY_INTRO):
        return None
    sections: dict[str, str] = {}
    for position, match in enumerate(headings):
        end = headings[position + 1].start() if position + 1 < len(headings) else len(text)
        sections[match.group(1)] = text[match.end() : end].strip()
    starting = _section_fields(sections["Starting Question"], ("Mainline or project goal", "Decision", "Why now"))
    state = _section_fields(sections["Decision State"], ("Decisions", "Open", "Rejected", "Evidence", "Resume point", "Promotion"))
    if starting is None or state is None:
        return None
    if any("<" in value or ">" in value for value in (*starting.values(), *state.values())):
        return None
    title = " ".join(starting["Decision"].split())
    if not title:
        return None
    if not valid_legacy_route_map(sections["Route Map"]):
        return None
    if normalized(sections["Update Rules"]) != normalized(LEGACY_UPDATE_RULES):
        return None
    header = text[: h1s[0].start()].rstrip()
    if not re.search(r"(?m)^Superseded By:", header):
        header += "\nSuperseded By: none"
    settled = [state["Decisions"], f"Alternative not chosen: {state['Rejected']}"]
    playback = sections["Textual Playback"]
    if normalized(playback) != normalized(LEGACY_PLAYBACK_GUIDANCE):
        settled.append(playback)
    promotion = state["Promotion"].strip()
    if promotion.rstrip(".").lower() != "none":
        settled.append(f"The settled result continues in {promotion}")
    return f"""{header}

# {title}

## Goal

{starting['Mainline or project goal']}

{starting['Why now']}

## Settled

{''.join(f'- {item}' + chr(10) for item in settled).rstrip()}

## Still open

- {state['Open']}

## Key evidence

- {state['Evidence']}

## Continue here

{state['Resume point']}
"""


class RetainedReader:
    """Validator adapter whose reads stay on the inherited Teamwork FD."""

    def __init__(self, guard: GuardFds, logical_root: Path) -> None:
        self.guard = guard
        self.project_root = logical_root
        self.root_fd = guard.fds["root"]
        self.docs_fd = guard.fds["docs"]
        self.memory_fd = guard.fds["teamwork"]

    def require_no_pending_discussion_transaction(self) -> None:
        self.guard.require_no_marker()

    def read_text(self, relative_path: PurePosixPath, label: str, *, require_single_link: bool = True) -> str:
        parts = relative_path.parts
        if len(parts) < 3 or parts[:2] != ("docs", "teamwork") or ".." in parts:
            validator.fail(f"{label} path must remain inside docs/teamwork")
        parent = os.dup(self.memory_fd)
        try:
            for part in parts[2:-1]:
                next_fd = open_dir(parent, part, self.guard.device)
                os.close(parent)
                parent = next_fd
            result = read_text(parent, parts[-1], relative_path.as_posix())
            assert result is not None
            return result[0]
        except InitError as exc:
            validator.fail(str(exc))
        finally:
            os.close(parent)


def logical_root() -> Path:
    raw = os.environ.get("TEAMWORK_PROJECT_ROOT", "")
    if not raw or not os.path.isabs(raw) or CONTROL_RE.search(raw):
        fail("TEAMWORK_PROJECT_ROOT must be an absolute logical project path")
    return Path(os.path.normpath(raw))


def validate_retained(guard: GuardFds, *, planned: dict[str, str] | None = None) -> None:
    index_result = read_text(guard.fds["teamwork"], "index.json", "docs/teamwork/index.json")
    assert index_result is not None
    try:
        index = json.loads(index_result[0])
    except json.JSONDecodeError as exc:
        fail(f"cannot parse docs/teamwork/index.json: {exc}")
    reader = RetainedReader(guard, logical_root())
    if planned:
        original = reader.read_text

        def planned_read(path: PurePosixPath, label: str, *, require_single_link: bool = True) -> str:
            value = planned.get(path.as_posix())
            return value if value is not None else original(path, label, require_single_link=require_single_link)

        reader.read_text = planned_read  # type: ignore[method-assign]
    validator.validate_index(index, logical_root() / "docs/teamwork/index.json", reader)


def command_preflight(guard: GuardFds, _args: argparse.Namespace) -> None:
    for name in ("AGENTS.md", ".gitignore"):
        info = entry_stat(guard.fds["root"], name)
        if info is not None and (
            stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
        ):
            fail(f"project output must be a single-link regular file: {name}")
    for name in ("research", "plans", "reports", "workflows"):
        info = entry_stat(guard.fds["teamwork"], name)
        if info is not None and (stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode)):
            fail(f"runtime path must be a non-symlink directory: docs/teamwork/{name}")
    for name in ("index.json", "current.md", "README.md"):
        info = entry_stat(guard.fds["teamwork"], name)
        if info is not None and (
            stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
        ):
            fail(f"runtime path must be a single-link regular file: docs/teamwork/{name}")
    discussion = entry_stat(guard.fds["teamwork"], "discussion")
    if discussion is not None:
        if stat.S_ISLNK(discussion.st_mode) or not stat.S_ISDIR(discussion.st_mode):
            fail("docs/teamwork/discussion must be a non-symlink directory")
        discussion_fd = open_dir(guard.fds["teamwork"], "discussion", guard.device)
        try:
            for name in os.listdir(discussion_fd):
                if name.endswith(".md"):
                    read_file(discussion_fd, name, f"docs/teamwork/discussion/{name}")
        finally:
            os.close(discussion_fd)
    guard.verify_retained()


def command_migrate(guard: GuardFds, _args: argparse.Namespace) -> None:
    command_preflight(guard, _args)
    raw_index = read_text(guard.fds["teamwork"], "index.json", "docs/teamwork/index.json", required=False)
    if raw_index is None:
        return
    try:
        index = json.loads(raw_index[0])
    except json.JSONDecodeError as exc:
        fail(f"cannot parse docs/teamwork/index.json: {exc}")
    if not isinstance(index, dict) or index.get("schema_version") != 1 or not isinstance(index.get("active"), dict):
        fail("docs/teamwork/index.json is not supported schema_version 1")
    updates: dict[str, str] = {}
    active = index["active"]
    if "discussion" not in active:
        active["discussion"] = None
        updates["docs/teamwork/index.json"] = json.dumps(index, indent=2, ensure_ascii=False) + "\n"
    discussion = active["discussion"]
    if discussion is not None and (not isinstance(discussion, str) or not discussion):
        fail("active.discussion must be null or a non-empty string")
    anchor = "none" if discussion is None else discussion
    current_result = read_text(guard.fds["teamwork"], "current.md", "docs/teamwork/current.md")
    readme_result = read_text(guard.fds["teamwork"], "README.md", "docs/teamwork/README.md")
    assert current_result is not None and readme_result is not None
    current = ensure_anchor(current_result[0], "- Active discussion:", anchor, ".")
    readme = ensure_anchor(migrate_readme_routing(readme_result[0]), "- Active discussion route:", anchor)
    updates["docs/teamwork/current.md"] = current
    updates["docs/teamwork/README.md"] = readme
    discussion_fd: int | None = None
    if entry_stat(guard.fds["teamwork"], "discussion") is not None:
        discussion_fd = open_dir(guard.fds["teamwork"], "discussion", guard.device)
        for name in sorted(os.listdir(discussion_fd)):
            if not name.endswith(".md"):
                continue
            result = read_text(discussion_fd, name, f"docs/teamwork/discussion/{name}")
            assert result is not None
            if not looks_legacy_discussion(result[0]):
                continue
            if re.fullmatch(
                r"[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9]+(?:-[a-z0-9]+)*\.md",
                name,
            ) is None:
                fail(
                    "legacy discussion migration requires a canonical dated-kebab filename: "
                    f"docs/teamwork/discussion/{name}"
                )
            migrated = migrate_legacy_discussion(result[0])
            if migrated is None:
                fail(f"unsupported or malformed legacy discussion artifact: docs/teamwork/discussion/{name}")
            validator.validate_discussion_artifact_text(migrated)
            updates[f"docs/teamwork/discussion/{name}"] = migrated
    planned = dict(updates)
    # Validate the complete planned view before changing any file.
    if "docs/teamwork/index.json" in updates:
        index_for_validation = json.loads(updates["docs/teamwork/index.json"])
    else:
        index_for_validation = index
    reader = RetainedReader(guard, logical_root())
    original_read = reader.read_text

    def planned_read(path: PurePosixPath, label: str, *, require_single_link: bool = True) -> str:
        value = planned.get(path.as_posix())
        return value if value is not None else original_read(path, label, require_single_link=require_single_link)

    reader.read_text = planned_read  # type: ignore[method-assign]
    validator.validate_index(index_for_validation, logical_root() / "docs/teamwork/index.json", reader)
    changes: list[Change] = []
    for path, text in sorted(updates.items(), key=lambda item: (item[0].endswith("index.json"), item[0])):
        pure = PurePosixPath(path)
        parent = guard.fds["teamwork"] if len(pure.parts) == 3 else discussion_fd
        assert parent is not None
        result = read_file(parent, pure.name, path)
        assert result is not None
        changes.append(Change(parent, pure.name, path, result[0], result[1], text.encode()))
    try:
        apply_changes(guard, changes, migration=True)
    finally:
        if discussion_fd is not None:
            os.close(discussion_fd)
    guard.verify_retained()


RUNTIME_README = """# Teamwork Runtime Index README

## Purpose

This local runtime README is the entrypoint for ordinary, non-discussion
Teamwork memory in this project.
Project instructions may point here, but should not inline this runtime narrative.

## Read Order

1. For Grill/discussion continuation, load `grill-me`, resolve the installed
   `scripts/discussion-transaction.py` from the loaded `using-teamwork` skill,
   and run `inspect` from the project root first.
   Its result is the sole discussion read path.
   For that continuation, do not directly read `index.json`,
   `current.md`, this README, or a discussion artifact.
2. For ordinary non-discussion memory, read `docs/teamwork/index.json` first,
   then this README.
3. Follow `active.current` and other non-discussion `active` pointers before
   any broad scan.
4. Prefer headers before full artifact bodies and use the stage-specific
   profiles from the index.

Legacy numeric budgets are compatibility retrieval hints, not execution limits
or hard stops. New indexes use header-first retrieval without numeric defaults.

## Stage Notes

- `research`: read topic headers first, then selective bodies.
- `discussion`: use the helper's `inspect` result; never open
  `active.discussion` or its artifact directly.
- `plan`: read active design/plan before adding or replacing plan state.
- `execute`: read active plan/progress before implementation updates.
- `review`: verify active claims against commands/logs/results.

## Current Anchors

- Active state: `docs/teamwork/current.md`
- The discussion anchor below is helper-managed metadata; never open it directly.
- Active discussion route: none

## Bounds

Keep this file concise and operational.
"""


def initial_current(today: str) -> str:
    return f"""# Teamwork Current State

Last Updated: {today}

## Active Snapshot

- Current focus: Initial Teamwork project setup.
- Active discussion: none.
- Active plan/design: none.
- Progress summary: Teamwork runtime memory was initialized for this project.
- Latest result: Project instructions and Teamwork runtime memory are ready for use.
- Blockers: none recorded.
- Next action: Replace this digest when material project state changes.

## Verification Anchors

- Commands: discover from project files before changing behavior.
- Logs/Artifacts: none recorded.
- Result paths: `docs/teamwork/index.json`, `docs/teamwork/current.md`.

## Supersession

- Supersedes: none.
- Superseded by: none.

## Pending

- None.

## Notes

This is a compact digest, not a running log. Replace in place as state changes.
"""


def initial_index(today: str, label: str) -> str:
    value = {
        "schema_version": 1,
        "last_updated": today,
        "project": {"name": label, "root": ".", "description": "Local Teamwork memory index for this project."},
        "source_of_truth_order": ["active", "linked", "header_search", "fulltext"],
        "ignore_globs": [".planning/**"],
        "budgets": {"header_first": True},
        "active": {"current": "docs/teamwork/current.md", "design": None, "plan": None, "progress": None, "goal": None, "report": None, "discussion": None, "results": []},
        "entries": [{
            "topic": "project-initialization", "kind": "result", "title": "Teamwork project initialization",
            "status": "active", "currentness": "current", "authority": "active-summary",
            "path": "docs/teamwork/current.md", "applies_to": ["AGENTS.md", "docs/teamwork/"],
            "linked": [], "evidence_paths": ["docs/teamwork/current.md"], "supersedes": [],
            "search_keys": ["teamwork-init", "project-init", "initialization"], "updated": today,
            "summary": "Initial Teamwork runtime memory entry created by project init."
        }],
        "profiles": {
            "status": ["index", "current", "active_discussion", "topic"],
            "implementation": ["index", "current", "active_discussion", "active_design_or_plan", "linked_research_headers"],
            "review": ["index", "current", "active_discussion", "active_design_or_plan", "active_progress", "verification"],
            "research": ["index", "current", "active_discussion", "topic_headers", "linked_artifacts"],
            "design": ["index", "current", "active_discussion", "accepted_decisions", "active_design_plan", "linked_research"]
        },
        "pending": [],
    }
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def replace_block(original: str, start: str, end: str, block: str, prefix: str = "") -> str:
    source = original if original else prefix
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end) + r"\n?", re.S)
    updated = pattern.sub(block, source) if pattern.search(source) else source.rstrip() + "\n\n" + block
    return updated.rstrip() + "\n"


def _read_root_optional(guard: GuardFds, name: str) -> str:
    result = read_text(guard.fds["root"], name, name, required=False)
    return "" if result is None else result[0]


def project_label(guard: GuardFds, explicit: str | None) -> str:
    if explicit:
        label = explicit.strip()
        if not label or CONTROL_RE.search(label):
            fail("project label must be non-empty text")
        return label
    for name in ("README.md", "README.en.md", "readme.md"):
        result = read_text(guard.fds["root"], name, name, required=False)
        if result:
            for line in result[0].splitlines():
                if line.startswith("# ") and line[2:].strip():
                    return line[2:].strip()
    return logical_root().name or "Project"


def configured(guard: GuardFds, needle: str) -> str | None:
    candidates = ((None, ".mcp.json", ".mcp.json"), (".cursor", "mcp.json", ".cursor/mcp.json"))
    for directory, name, logical in candidates:
        parent = guard.fds["root"]
        child: int | None = None
        try:
            if directory:
                if entry_stat(parent, directory) is None:
                    continue
                child = open_dir(parent, directory, guard.device)
                parent = child
            result = read_text(parent, name, logical, required=False)
            if result and needle in result[0].lower():
                return logical
        finally:
            if child is not None:
                os.close(child)
    return None


def command_write_context(guard: GuardFds, args: argparse.Namespace) -> None:
    command_preflight(guard, args)
    try:
        date.fromisoformat(args.today)
    except ValueError:
        fail("--today must be a valid YYYY-MM-DD date")
    label = project_label(guard, args.project_label)
    child_fds: list[int] = []
    try:
        for name in ("research", "plans", "reports", "workflows"):
            child_fds.append(open_dir(guard.fds["teamwork"], name, guard.device, create=True))
        changes: list[Change] = []
        if entry_stat(guard.fds["teamwork"], "README.md") is None:
            changes.append(change_for(guard.fds["teamwork"], "README.md", "docs/teamwork/README.md", RUNTIME_README))
        if entry_stat(guard.fds["teamwork"], "current.md") is None:
            changes.append(change_for(guard.fds["teamwork"], "current.md", "docs/teamwork/current.md", initial_current(args.today)))
        if entry_stat(guard.fds["teamwork"], "index.json") is None:
            changes.append(change_for(guard.fds["teamwork"], "index.json", "docs/teamwork/index.json", initial_index(args.today, label)))

        project_lines = [
            f"- Project label (local routing only): `{label}`.",
            "- For Grill/discussion continuation, load `grill-me`, resolve the installed `scripts/discussion-transaction.py` from the loaded `using-teamwork` skill, and run `inspect` from the project root first; its result is the sole discussion read path, so do not directly read `index.json`, `current.md`, `README.md`, or a discussion artifact for that continuation.",
            "- Ordinary non-discussion memory reads `docs/teamwork/index.json` first, then `docs/teamwork/README.md` when durable memory is relevant.",
        ]
        codegraph_config = configured(guard, "codegraph")
        if entry_stat(guard.fds["root"], ".codegraph") is not None:
            project_lines.append("- CodeGraph: this project has a local `.codegraph/` index.")
        elif codegraph_config:
            project_lines.append(f"- CodeGraph: project configuration declares it in `{codegraph_config}`.")
        docs_config = configured(guard, "context7")
        if docs_config:
            project_lines.append(f"- Docs MCP: project configuration declares Context7 in `{docs_config}`.")
        agents_block = "<!-- TEAMWORK_PROJECT_START -->\n## Teamwork Project Instructions\n\n" + "\n".join(project_lines) + "\n<!-- TEAMWORK_PROJECT_END -->\n"
        gitignore_block = """# TEAMWORK_LOCAL_START
# Teamwork local runtime state
.codegraph/
.*.teamwork-init-stage-*
.*.teamwork-init-backup-*
docs/teamwork/plans/
docs/teamwork/discussion/
docs/teamwork/research/
docs/teamwork/reports/
docs/teamwork/workflows/
docs/teamwork/index.json
docs/teamwork/README.md
docs/teamwork/current.md
docs/teamwork/.teamwork-init-transaction.json*
docs/teamwork/.*.teamwork-init-stage-*
docs/teamwork/.*.teamwork-init-backup-*
# TEAMWORK_LOCAL_END
"""
        agents = _read_root_optional(guard, "AGENTS.md")
        gitignore = _read_root_optional(guard, ".gitignore")
        changes.append(change_for(
            guard.fds["root"], "AGENTS.md", "AGENTS.md",
            replace_block(agents, "<!-- TEAMWORK_PROJECT_START -->", "<!-- TEAMWORK_PROJECT_END -->", agents_block, "# Repository Guidelines\n"),
        ))
        changes.append(change_for(
            guard.fds["root"], ".gitignore", ".gitignore",
            replace_block(gitignore, "# TEAMWORK_LOCAL_START", "# TEAMWORK_LOCAL_END", gitignore_block),
        ))
        apply_changes(guard, changes)
    finally:
        for fd in child_fds:
            os.close(fd)
    guard.verify_retained()


def command_validate(guard: GuardFds, _args: argparse.Namespace) -> None:
    validate_retained(guard)
    guard.verify_retained()


def command_codegraph(guard: GuardFds, args: argparse.Namespace) -> None:
    command = args.command or ["codegraph", "init", "-i"]
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        fail("codegraph requires a command")
    saved = os.open(".", os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fchdir(guard.fds["root"])
        result = subprocess.run(command, check=False)
    finally:
        os.fchdir(saved)
        os.close(saved)
    if result.returncode != 0:
        fail(f"codegraph command failed with exit status {result.returncode}")
    guard.verify_retained()


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    sub = result.add_subparsers(dest="action", required=True)
    sub.add_parser("preflight")
    sub.add_parser("migrate")
    write = sub.add_parser("write-context")
    write.add_argument("--today", default=date.today().isoformat())
    write.add_argument("--project-label")
    sub.add_parser("validate")
    graph = sub.add_parser("codegraph")
    graph.add_argument("command", nargs=argparse.REMAINDER)
    return result


def main() -> int:
    args = parser().parse_args()
    try:
        guard = GuardFds()
        actions = {
            "preflight": command_preflight,
            "migrate": command_migrate,
            "write-context": command_write_context,
            "validate": command_validate,
            "codegraph": command_codegraph,
        }
        actions[args.action](guard, args)
    except (InitError, validator.ValidationError) as exc:
        print(f"Teamwork project init refused: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
