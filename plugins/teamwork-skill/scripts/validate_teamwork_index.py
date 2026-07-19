#!/usr/bin/env python3
"""Validate ordinary Teamwork memory without owning Grill discussion state."""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
from datetime import date
from pathlib import Path, PurePosixPath


DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
CURRENT_KINDS = {
    "result",
    "progress",
    "design",
    "decision",
    "plan",
    "report",
    "research",
    "runbook",
    # W4 owns discussion artifact interpretation and lifecycle validation.  The
    # ordinary-memory validator accepts its indexed metadata but never treats it
    # as an ordinary active pointer target.
    "discussion",
}
STATUSES = {"active", "historical", "superseded", "blocked", "candidate", "accepted"}
CURRENTNESS = {"current", "stale", "historical", "candidate"}
AUTHORITIES = {"canonical", "active-summary", "supporting", "candidate", "historical", "superseded"}
ACTIVE_STATUSES = {"active", "accepted"}
ACTIVE_AUTHORITIES = {"canonical", "active-summary", "supporting"}
ACTIVE_POINTER_KEYS = ("current", "design", "plan", "progress", "goal", "report")
# W4 may retain a nullable compatibility slot while it owns the discussion
# lifecycle. A non-null pointer is legacy migration input, not post-v4 truth.
ALLOWED_ACTIVE_KEYS = {*ACTIVE_POINTER_KEYS, "results", "discussion"}
CANONICAL_CURRENT_PATH = "docs/teamwork/current.md"


class ValidationError(Exception):
    pass


def fail(message: str) -> None:
    raise ValidationError(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def valid_date(value: object) -> bool:
    if not isinstance(value, str) or DATE_RE.fullmatch(value) is None:
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def validate_memory_path(value: object, label: str) -> PurePosixPath:
    require(isinstance(value, str) and value, f"{label} must be a non-empty string")
    assert isinstance(value, str)
    path = PurePosixPath(value)
    require(
        not path.is_absolute()
        and path.as_posix() == value
        and "\\" not in value
        and CONTROL_RE.search(value) is None
        and ".." not in path.parts
        and len(path.parts) >= 3
        and path.parts[:2] == ("docs", "teamwork"),
        f"{label} must be a normalized path under docs/teamwork/",
    )
    return path


class SafeProjectReader:
    """Small no-follow reader for validating active project-memory paths."""

    def __init__(self, project_root: Path):
        self.project_root = Path(os.path.abspath(os.fspath(project_root)))
        current = Path(self.project_root.anchor)
        for part in self.project_root.parts[1:]:
            current /= part
            try:
                info = current.lstat()
            except OSError as exc:
                fail(f"project root must exist: {current}: {exc}")
            require(
                stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode),
                f"project root must not contain symlink components: {current}",
            )
        self.root_device = self.project_root.stat().st_dev

    def close(self) -> None:
        return

    def read_text(
        self,
        relative_path: PurePosixPath,
        label: str,
        *,
        require_single_link: bool = True,
    ) -> str:
        validate_memory_path(relative_path.as_posix(), label)
        current = self.project_root
        for part in relative_path.parts[:-1]:
            current /= part
            try:
                info = current.lstat()
            except OSError as exc:
                fail(f"cannot inspect {label} parent: {exc}")
            require(
                stat.S_ISDIR(info.st_mode)
                and not stat.S_ISLNK(info.st_mode)
                and info.st_dev == self.root_device,
                f"{label} parent must be a same-device non-symlink directory",
            )
        path = current / relative_path.name
        try:
            expected = path.lstat()
        except OSError as exc:
            fail(f"missing or unreadable {label}: {path}: {exc}")
        require(
            stat.S_ISREG(expected.st_mode)
            and not stat.S_ISLNK(expected.st_mode)
            and (not require_single_link or expected.st_nlink == 1),
            f"{label} must be a {'single-link ' if require_single_link else ''}non-symlink regular file",
        )
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
        try:
            fd = os.open(path, flags)
        except OSError as exc:
            fail(f"cannot safely open {label}: {exc}")
        try:
            opened = os.fstat(fd)
            require(
                (opened.st_dev, opened.st_ino) == (expected.st_dev, expected.st_ino),
                f"{label} changed identity while opening",
            )
            chunks: list[bytes] = []
            while chunk := os.read(fd, 1024 * 1024):
                chunks.append(chunk)
            final = os.fstat(fd)
            require(
                (final.st_dev, final.st_ino) == (opened.st_dev, opened.st_ino),
                f"{label} changed identity while reading",
            )
            try:
                return b"".join(chunks).decode("utf-8")
            except UnicodeDecodeError as exc:
                fail(f"{label} must be UTF-8: {exc}")
        finally:
            os.close(fd)


def validate_string_list(value: object, label: str) -> None:
    require(isinstance(value, list), f"{label} must be an array")
    assert isinstance(value, list)
    require(
        all(isinstance(item, str) and item for item in value),
        f"{label} must contain only non-empty strings",
    )
    require(len(value) == len(set(value)), f"{label} must not contain duplicates")


def validate_entry(entry: object, index: int, *, migration_read: bool = False) -> dict:
    require(isinstance(entry, dict), f"entries[{index}] must be an object")
    assert isinstance(entry, dict)
    required = (
        "topic",
        "kind",
        "title",
        "status",
        "currentness",
        "authority",
        "path",
        "updated",
        "summary",
    )
    for key in required:
        require(key in entry, f"entries[{index}] missing required key: {key}")
    for key in ("topic", "title", "summary"):
        require(
            isinstance(entry[key], str) and entry[key].strip(),
            f"entries[{index}].{key} must be non-empty text",
        )
    require(
        isinstance(entry["kind"], str) and entry["kind"] in CURRENT_KINDS,
        f"entries[{index}].kind has unknown value: {entry['kind']}",
    )
    require(
        isinstance(entry["status"], str) and entry["status"] in STATUSES,
        f"entries[{index}].status has unknown value: {entry['status']}",
    )
    require(
        isinstance(entry["currentness"], str) and entry["currentness"] in CURRENTNESS,
        f"entries[{index}].currentness has unknown value: {entry['currentness']}",
    )
    require(
        isinstance(entry["authority"], str) and entry["authority"] in AUTHORITIES,
        f"entries[{index}].authority has unknown value: {entry['authority']}",
    )
    validate_memory_path(entry["path"], f"entries[{index}].path")
    require(valid_date(entry["updated"]), f"entries[{index}].updated must be a valid YYYY-MM-DD date")
    for key in ("applies_to", "linked", "evidence_paths", "supersedes", "search_keys"):
        if key in entry:
            validate_string_list(entry[key], f"entries[{index}].{key}")
    return entry


def validate_active(
    active: object,
    entries: list[dict],
    reader: SafeProjectReader | None,
    *,
    migration_read: bool = False,
) -> None:
    require(isinstance(active, dict), "active must be an object")
    assert isinstance(active, dict)
    unknown = set(active) - ALLOWED_ACTIVE_KEYS
    require(not unknown, f"active has unknown keys: {', '.join(sorted(unknown))}")
    require(active.get("current") == CANONICAL_CURRENT_PATH, f"active.current must be {CANONICAL_CURRENT_PATH}")
    require("results" in active, "active.results is required")
    validate_string_list(active["results"], "active.results")
    for key in ACTIVE_POINTER_KEYS:
        value = active.get(key)
        require(value is None or isinstance(value, str), f"active.{key} must be null or a string")
        if isinstance(value, str):
            validate_memory_path(value, f"active.{key}")
            require(
                value != "docs/teamwork/discussion/current.md",
                f"active.{key} must not point at Grill discussion state",
            )
    legacy_discussion = active.get("discussion")
    require(
        legacy_discussion is None or isinstance(legacy_discussion, str),
        "legacy active.discussion must be null or a string",
    )
    if isinstance(legacy_discussion, str):
        validate_memory_path(legacy_discussion, "legacy active.discussion")

    by_path: dict[str, list[dict]] = {}
    for entry in entries:
        by_path.setdefault(entry["path"], []).append(entry)
    pointers = [
        (f"active.{key}", value)
        for key in ACTIVE_POINTER_KEYS
        if isinstance((value := active.get(key)), str)
    ]
    pointers.extend((f"active.results[{position}]", value) for position, value in enumerate(active["results"]))
    for label, path in pointers:
        matching = [
            entry
            for entry in by_path.get(path, [])
            if entry["kind"] != "discussion"
            and entry["status"] in ACTIVE_STATUSES
            and entry["currentness"] == "current"
            and entry["authority"] in ACTIVE_AUTHORITIES
        ]
        require(matching, f"{label} has no eligible ordinary-memory entry: {path}")
        if reader is not None:
            reader.read_text(PurePosixPath(path), label)


def validate_index(
    index: object,
    index_path: Path,
    project_reader: SafeProjectReader | None = None,
    *,
    migration_read: bool = False,
) -> None:
    require(isinstance(index, dict), "index root must be an object")
    assert isinstance(index, dict)
    require(index.get("schema_version") == 1, "schema_version must be 1")
    require(valid_date(index.get("last_updated")), "last_updated must be a valid YYYY-MM-DD date")
    project = index.get("project")
    require(isinstance(project, dict), "project must be an object")
    assert isinstance(project, dict)
    require(
        isinstance(project.get("name"), str) and project["name"].strip(),
        "project.name must be non-empty text",
    )
    require(project.get("root") == ".", "project.root must be .")
    require(
        isinstance(project.get("description"), str) and project["description"].strip(),
        "project.description must be non-empty text",
    )
    validate_string_list(index.get("source_of_truth_order"), "source_of_truth_order")
    validate_string_list(index.get("ignore_globs"), "ignore_globs")
    budgets = index.get("budgets")
    require(
        isinstance(budgets, dict) and budgets.get("header_first") is True,
        "budgets.header_first must be true",
    )
    entries_raw = index.get("entries")
    require(isinstance(entries_raw, list) and entries_raw, "entries must be a non-empty array")
    assert isinstance(entries_raw, list)
    entries = [
        validate_entry(entry, position, migration_read=migration_read)
        for position, entry in enumerate(entries_raw)
    ]
    validate_active(index.get("active"), entries, project_reader, migration_read=migration_read)
    profiles = index.get("profiles")
    require(isinstance(profiles, dict) and profiles, "profiles must be a non-empty object")
    assert isinstance(profiles, dict)
    for name, values in profiles.items():
        require(isinstance(name, str) and name, "profile names must be non-empty strings")
        validate_string_list(values, f"profiles.{name}")
    pending = index.get("pending")
    require(isinstance(pending, list), "pending must be an array")


def read_regular_text(path: Path, label: str) -> str:
    try:
        expected = path.lstat()
    except OSError as exc:
        fail(f"cannot inspect {label}: {exc}")
    require(
        stat.S_ISREG(expected.st_mode) and not stat.S_ISLNK(expected.st_mode),
        f"{label} must be a non-symlink regular file",
    )
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        fail(f"cannot safely open {label}: {exc}")
    try:
        opened = os.fstat(fd)
        require(
            (opened.st_dev, opened.st_ino) == (expected.st_dev, expected.st_ino),
            f"{label} changed identity while opening",
        )
        chunks: list[bytes] = []
        while chunk := os.read(fd, 1024 * 1024):
            chunks.append(chunk)
        try:
            return b"".join(chunks).decode("utf-8")
        except UnicodeDecodeError as exc:
            fail(f"{label} must be UTF-8: {exc}")
    finally:
        os.close(fd)


def validate_memory_templates(directory: Path) -> None:
    index_text = read_regular_text(directory / "index.json", "memory index template")
    current = read_regular_text(directory / "current.md", "memory current template")
    readme = read_regular_text(directory / "README.md", "memory README template")
    try:
        index = json.loads(index_text)
    except json.JSONDecodeError as exc:
        fail(f"memory index template is invalid JSON: {exc}")
    validate_index(index, directory / "index.json")
    active = index["active"]
    require(active.get("discussion") is None, "memory index template discussion compatibility slot must be null")
    require(
        all(entry["kind"] != "discussion" for entry in index["entries"]),
        "memory index template must not contain discussion entries",
    )
    combined = "\n".join((index_text, current, readme)).casefold()
    for forbidden in ("discussion-transaction", "using-teamwork/scripts"):
        require(forbidden not in combined, f"ordinary memory templates must not contain {forbidden!r}")
    require("YYYY-MM-DD" in current, "memory current template must retain the date placeholder")
    require(len(current.splitlines()) <= 80, "memory current template exceeds 80 lines")
    require(len(readme.splitlines()) <= 80, "memory README template exceeds 80 lines")


def canonical_project_root(index_path: Path) -> Path | None:
    if (
        index_path.name == "index.json"
        and index_path.parent.name == "teamwork"
        and index_path.parent.parent.name == "docs"
    ):
        return index_path.parent.parent.parent
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--migration-read",
        action="store_true",
        help="accept the legacy CLI spelling; W4 owns discussion lifecycle validation",
    )
    parser.add_argument("index")
    arguments = parser.parse_args()
    path = Path(os.path.abspath(arguments.index))
    try:
        text = read_regular_text(path, "index input")
        try:
            index = json.loads(text)
        except json.JSONDecodeError as exc:
            fail(f"invalid JSON: {exc}")
        if path.parent.name == "teamwork-memory" and path.parent.parent.name == "templates":
            validate_memory_templates(path.parent)
        elif (root := canonical_project_root(path)) is not None:
            reader = SafeProjectReader(root)
            try:
                validate_index(index, path, reader, migration_read=arguments.migration_read)
            finally:
                reader.close()
        else:
            validate_index(index, path, migration_read=arguments.migration_read)
    except ValidationError as exc:
        print(f"invalid Teamwork index: {exc}", file=sys.stderr)
        return 1
    print(f"valid Teamwork index: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
