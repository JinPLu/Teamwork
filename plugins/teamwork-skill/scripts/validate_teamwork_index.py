#!/usr/bin/env python3
"""Validate ordinary Teamwork memory without owning Discuss checkpoint state."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import stat
import sys
from datetime import date, timezone, datetime
from pathlib import Path, PurePosixPath
import unicodedata


DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
CASE_ID_RE = re.compile(r"^c-[0-9a-f]{64}$")
CLAIM_ID_RE = re.compile(r"^cl-[0-9a-f]{64}$")
ARTIFACT_ID_RE = re.compile(r"^a-[0-9a-f]{64}$")
MIGRATION_ID_RE = re.compile(r"^m-[0-9a-f]{64}$")
KEBAB_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CURRENT_INDEX_MAX_BYTES = 262144
CURRENT_MANIFEST_MAX_BYTES = 262144
CURRENT_ACTIVE_CASES_MAX = 32
CURRENT_CLAIM_HEADS_MAX = 2048
CURRENT_ALIASES_MAX = 256
CURRENT_RECENT_CASES_MAX = 10
CURRENT_MANIFEST_CLAIMS_MAX = 256
CURRENT_MANIFEST_ARTIFACTS_MAX = 2048
CURRENT_MANIFEST_HISTORY_MAX = 1024
CURRENT_MANIFEST_REFS_MAX = 1024
CURRENT_MANIFEST_MIGRATION_SOURCES_MAX = 4096
CURRENT_CASE_PHASES = {"collaborating", "collecting", "planned", "executing", "reviewing"}
CURRENT_CASE_LIFECYCLES = {"collaborating", "collecting", "planned", "executing", "reviewing", "closed"}
CURRENT_LIVE_PURPOSES = {"task", "discussion", "research", "debug", "plan", "review", "goal", "init", "update", "result"}
CURRENT_LIVE_STATUSES = {"active", "finalized"}
CURRENT_CLAIM_HEAD_STATUSES = {"active"}
CURRENT_MIGRATION_PHASES = {
    "baseline_approved",
    "archive_durable",
    "candidate_validated",
    "old_tree_renamed",
    "new_tree_installed",
    "postinstall_validated",
    "committed",
    "cleanup_complete",
}
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
COLLABORATE_CURRENT_PATH = "docs/teamwork/collaborate/current.md"
# A nullable discussion slot is accepted only while validating legacy migration
# input. A non-null pointer is never current runtime truth.
ALLOWED_ACTIVE_KEYS = {*ACTIVE_POINTER_KEYS, "results", "collaborate", "discussion"}
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


def validate_sha256(value: object, label: str) -> None:
    require(
        isinstance(value, str) and HEX64_RE.fullmatch(value) is not None,
        f"{label} must be lowercase sha256 hex",
    )


def validate_case_id(value: object, label: str) -> str:
    require(
        isinstance(value, str) and CASE_ID_RE.fullmatch(value) is not None,
        f"{label} must be c- followed by lowercase sha256 hex",
    )
    assert isinstance(value, str)
    return value


def validate_claim_id(value: object, label: str) -> str:
    require(
        isinstance(value, str) and CLAIM_ID_RE.fullmatch(value) is not None,
        f"{label} must be cl- followed by lowercase sha256 hex",
    )
    assert isinstance(value, str)
    return value


def validate_artifact_id(value: object, label: str) -> str:
    require(
        isinstance(value, str) and ARTIFACT_ID_RE.fullmatch(value) is not None,
        f"{label} must be a- followed by lowercase sha256 hex",
    )
    assert isinstance(value, str)
    return value


def validate_migration_id(value: object, label: str) -> str:
    require(
        isinstance(value, str) and MIGRATION_ID_RE.fullmatch(value) is not None,
        f"{label} must be m- followed by lowercase sha256 hex",
    )
    assert isinstance(value, str)
    return value


def validate_kebab(value: object, label: str) -> str:
    require(
        isinstance(value, str) and KEBAB_RE.fullmatch(value) is not None,
        f"{label} must be lowercase kebab text",
    )
    assert isinstance(value, str)
    return value


def validate_case_manifest_path(value: object, label: str, *, expected_case_id: str | None = None) -> PurePosixPath:
    path = validate_memory_path(value, label)
    require(
        len(path.parts) == 5
        and path.parts[:3] == ("docs", "teamwork", "cases")
        and path.name == "manifest.json",
        f"{label} must be docs/teamwork/cases/c-<64hex>/manifest.json",
    )
    case_id = path.parts[3]
    validate_case_id(case_id, f"{label}.case_id")
    if expected_case_id is not None:
        require(case_id == expected_case_id, f"{label} must match {expected_case_id}")
    return path


def validate_any_relative_path(value: object, label: str) -> PurePosixPath:
    require(isinstance(value, str) and value, f"{label} must be a non-empty string")
    assert isinstance(value, str)
    path = PurePosixPath(value)
    require(
        not path.is_absolute()
        and path.as_posix() == value
        and "\\" not in value
        and CONTROL_RE.search(value) is None
        and "." not in path.parts
        and ".." not in path.parts
        and len(path.parts) >= 1,
        f"{label} must be a normalized relative path",
    )
    return path


def _hash(*parts: bytes) -> str:
    digest = hashlib.sha256()
    for part in parts:
        digest.update(len(part).to_bytes(8, "big"))
        digest.update(part)
    return digest.hexdigest()


def _reject_float(value: object) -> None:
    if isinstance(value, float):
        fail("canonical JSON does not allow floats")
    if isinstance(value, dict):
        for item in value.values():
            _reject_float(item)
    if isinstance(value, list):
        for item in value:
            _reject_float(item)


def canonical_json_bytes(value: object) -> bytes:
    _reject_float(value)
    return unicodedata.normalize(
        "NFC",
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
    ).encode("utf-8")


def case_digest(domain: str, value: object | str | bytes) -> str:
    if isinstance(value, bytes):
        payload = value
    elif isinstance(value, str):
        payload = unicodedata.normalize("NFC", value.replace("\r\n", "\n").replace("\r", "\n")).encode("utf-8")
    else:
        payload = canonical_json_bytes(value)
    # Frozen digest namespace: changing it would invalidate existing current manifests.
    return _hash(f"teamwork-case-v2:{domain}".encode("utf-8"), payload)


def computed_case_manifest_revision(manifest: dict[str, object]) -> str:
    return case_digest("manifest-revision", manifest)


def validate_case_artifact_path(value: object, label: str, case_id: str) -> PurePosixPath:
    path = validate_memory_path(value, label)
    require(
        len(path.parts) >= 5
        and path.parts[:4] == ("docs", "teamwork", "cases", case_id),
        f"{label} must stay inside docs/teamwork/cases/{case_id}/",
    )
    require(path.name != "manifest.json", f"{label} must not point at the manifest")
    return path


def validate_utc_timestamp(value: object, label: str) -> None:
    require(isinstance(value, str), f"{label} must be a UTC timestamp")
    assert isinstance(value, str)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        fail(f"{label} must be a UTC timestamp")
    require(parsed.tzinfo is not None and parsed.utcoffset() == timezone.utc.utcoffset(parsed), f"{label} must be UTC")


def validate_collaborate_consumed_sources(value: object) -> None:
    require(isinstance(value, list), "collaborate_consumed_sources must be an array")
    assert isinstance(value, list)
    seen: set[tuple[str, str, str]] = set()
    for position, row in enumerate(value):
        require(isinstance(row, dict), f"collaborate_consumed_sources[{position}] must be an object")
        assert isinstance(row, dict)
        require(
            set(row) == {"consumed_at", "consumed_by_decision_id", "kind", "path", "sha256"},
            f"collaborate_consumed_sources[{position}] has invalid fields",
        )
        validate_utc_timestamp(row["consumed_at"], f"collaborate_consumed_sources[{position}].consumed_at")
        require(
            isinstance(row["consumed_by_decision_id"], str) and row["consumed_by_decision_id"].strip(),
            f"collaborate_consumed_sources[{position}].consumed_by_decision_id must be text",
        )
        require(row["kind"] in {"design", "discussion"}, f"collaborate_consumed_sources[{position}].kind is invalid")
        validate_memory_path(row["path"], f"collaborate_consumed_sources[{position}].path")
        validate_sha256(row["sha256"], f"collaborate_consumed_sources[{position}].sha256")
        key = (str(row["kind"]), str(row["path"]), str(row["sha256"]))
        require(key not in seen, "collaborate_consumed_sources must not duplicate source digests")
        seen.add(key)


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
                f"active.{key} must not point at Discuss checkpoint state",
            )
    legacy_discussion = active.get("discussion")
    require(
        legacy_discussion is None or isinstance(legacy_discussion, str),
        "legacy active.discussion must be null or a string",
    )
    if isinstance(legacy_discussion, str):
        validate_memory_path(legacy_discussion, "legacy active.discussion")
    collaborate = active.get("collaborate")
    require(
        collaborate is None or collaborate == COLLABORATE_CURRENT_PATH,
        f"active.collaborate must be null or {COLLABORATE_CURRENT_PATH}",
    )

    by_path: dict[str, list[dict]] = {}
    for entry in entries:
        by_path.setdefault(entry["path"], []).append(entry)
    pointers = [
        (f"active.{key}", value)
        for key in ACTIVE_POINTER_KEYS
        if isinstance((value := active.get(key)), str)
    ]
    if isinstance(active.get("collaborate"), str):
        pointers.append(("active.collaborate", str(active["collaborate"])))
    pointers.extend((f"active.results[{position}]", value) for position, value in enumerate(active["results"]))
    for label, path in pointers:
        matching = [
            entry
            for entry in by_path.get(path, [])
            if (
                entry["kind"] != "discussion"
                and entry["status"] in ACTIVE_STATUSES
                and entry["currentness"] == "current"
                and entry["authority"] in ACTIVE_AUTHORITIES
            )
            or (
                label == "active.collaborate"
                and entry["kind"] == "decision"
                and entry.get("artifact_type") == "collaborate"
                and entry["status"] in {"active", "accepted", "blocked"}
                and entry["currentness"] == "current"
                and entry["authority"] == "canonical"
            )
        ]
        require(matching, f"{label} has no eligible ordinary-memory entry: {path}")
        if reader is not None:
            reader.read_text(PurePosixPath(path), label)


def validate_v1_index(
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
    validate_collaborate_consumed_sources(index.get("collaborate_consumed_sources", []))
    profiles = index.get("profiles")
    require(isinstance(profiles, dict) and profiles, "profiles must be a non-empty object")
    assert isinstance(profiles, dict)
    for name, values in profiles.items():
        require(isinstance(name, str) and name, "profile names must be non-empty strings")
        validate_string_list(values, f"profiles.{name}")
    pending = index.get("pending")
    require(isinstance(pending, list), "pending must be an array")


def validate_current_migration(value: object) -> None:
    if value is None:
        return
    require(isinstance(value, dict), "migration must be null or an object")
    assert isinstance(value, dict)
    expected = {
        "migration_id",
        "phase",
        "journal_path",
        "baseline_digest",
        "report_digest",
        "candidate_digest",
        "archive_manifest_digest",
    }
    require(set(value) == expected, "migration has invalid fields")
    validate_migration_id(value["migration_id"], "migration.migration_id")
    require(value["phase"] in CURRENT_MIGRATION_PHASES, "migration.phase is invalid")
    validate_any_relative_path(value["journal_path"], "migration.journal_path")
    for key in ("baseline_digest", "report_digest", "candidate_digest", "archive_manifest_digest"):
        validate_sha256(value[key], f"migration.{key}")


def validate_current_root_index(
    index: object,
    index_path: Path,
    project_reader: SafeProjectReader | None = None,
    *,
    raw_bytes: int | None = None,
    migration_read: bool = False,
) -> None:
    if raw_bytes is not None:
        require(raw_bytes <= CURRENT_INDEX_MAX_BYTES, "current index exceeds 262144 bytes")
    require(isinstance(index, dict), "index root must be an object")
    assert isinstance(index, dict)
    expected = {
        "schema_version",
        "project",
        "active_cases",
        "claim_heads",
        "aliases",
        "recent_cases",
        "migration",
    }
    require(set(index) == expected, "v2 index top-level fields are invalid")
    require(
        index["schema_version"] == (2 if migration_read else 3),
        "schema_version requires explicit project migration" if migration_read else "schema_version must be 3",
    )
    project = index["project"]
    require(isinstance(project, dict), "project must be an object")
    assert isinstance(project, dict)
    require(set(project) == {"name", "root", "description"}, "project fields are invalid")
    require(isinstance(project["name"], str) and project["name"].strip(), "project.name must be non-empty text")
    require(project["root"] == ".", "project.root must be .")
    require(
        isinstance(project["description"], str) and project["description"].strip(),
        "project.description must be non-empty text",
    )

    active_cases = index["active_cases"]
    require(isinstance(active_cases, list), "active_cases must be an array")
    assert isinstance(active_cases, list)
    require(len(active_cases) <= CURRENT_ACTIVE_CASES_MAX, "active_cases exceeds 32 records")
    active_case_ids: set[str] = set()
    active_task_keys: set[str] = set()
    for position, row in enumerate(active_cases):
        require(isinstance(row, dict), f"active_cases[{position}] must be an object")
        assert isinstance(row, dict)
        require(
            set(row) == {"case_id", "manifest_path", "manifest_revision", "phase", "task_key"},
            f"active_cases[{position}] has invalid fields",
        )
        case_id = validate_case_id(row["case_id"], f"active_cases[{position}].case_id")
        require(case_id not in active_case_ids, "active_cases must not duplicate case_id")
        active_case_ids.add(case_id)
        validate_case_manifest_path(row["manifest_path"], f"active_cases[{position}].manifest_path", expected_case_id=case_id)
        validate_sha256(row["manifest_revision"], f"active_cases[{position}].manifest_revision")
        require(row["phase"] in CURRENT_CASE_PHASES, f"active_cases[{position}].phase is invalid")
        task_key = validate_kebab(row["task_key"], f"active_cases[{position}].task_key")
        require(task_key not in active_task_keys, "active_cases must not duplicate task_key")
        active_task_keys.add(task_key)

    claim_heads = index["claim_heads"]
    require(isinstance(claim_heads, dict), "claim_heads must be an object")
    assert isinstance(claim_heads, dict)
    require(len(claim_heads) <= CURRENT_CLAIM_HEADS_MAX, "claim_heads exceeds 2048 records")
    for claim_id, row in claim_heads.items():
        validate_claim_id(claim_id, f"claim_heads key {claim_id!r}")
        require(isinstance(row, dict), f"claim_heads[{claim_id}] must be an object")
        assert isinstance(row, dict)
        require(
            set(row) == {"case_id", "artifact_id", "artifact_digest", "claim_revision", "status"},
            f"claim_heads[{claim_id}] has invalid fields",
        )
        validate_case_id(row["case_id"], f"claim_heads[{claim_id}].case_id")
        validate_artifact_id(row["artifact_id"], f"claim_heads[{claim_id}].artifact_id")
        validate_sha256(row["artifact_digest"], f"claim_heads[{claim_id}].artifact_digest")
        validate_sha256(row["claim_revision"], f"claim_heads[{claim_id}].claim_revision")
        require(row["status"] in CURRENT_CLAIM_HEAD_STATUSES, f"claim_heads[{claim_id}].status is invalid")

    aliases = index["aliases"]
    require(isinstance(aliases, dict), "aliases must be an object")
    assert isinstance(aliases, dict)
    require(len(aliases) <= CURRENT_ALIASES_MAX, "aliases exceeds 256 records")
    for alias, row in aliases.items():
        validate_kebab(alias, f"aliases key {alias!r}")
        require(isinstance(row, dict), f"aliases.{alias} must be an object")
        assert isinstance(row, dict)
        require(set(row) == {"target_type", "target_id", "manifest_path", "manifest_revision"}, f"aliases.{alias} has invalid fields")
        require(row["target_type"] == "case", f"aliases.{alias}.target_type must be case")
        target_id = validate_case_id(row["target_id"], f"aliases.{alias}.target_id")
        validate_case_manifest_path(row["manifest_path"], f"aliases.{alias}.manifest_path", expected_case_id=target_id)
        validate_sha256(row["manifest_revision"], f"aliases.{alias}.manifest_revision")

    recent_cases = index["recent_cases"]
    require(isinstance(recent_cases, list), "recent_cases must be an array")
    assert isinstance(recent_cases, list)
    require(len(recent_cases) <= CURRENT_RECENT_CASES_MAX, "recent_cases exceeds 10 records")
    recent_ids: set[str] = set()
    for position, row in enumerate(recent_cases):
        require(isinstance(row, dict), f"recent_cases[{position}] must be an object")
        assert isinstance(row, dict)
        require(
            set(row) == {"case_id", "manifest_path", "closed_at", "result_artifact_id", "result_digest"},
            f"recent_cases[{position}] has invalid fields",
        )
        case_id = validate_case_id(row["case_id"], f"recent_cases[{position}].case_id")
        require(case_id not in recent_ids, "recent_cases must not duplicate case_id")
        recent_ids.add(case_id)
        require(case_id not in active_case_ids, "recent_cases must not duplicate active cases")
        validate_case_manifest_path(row["manifest_path"], f"recent_cases[{position}].manifest_path", expected_case_id=case_id)
        validate_utc_timestamp(row["closed_at"], f"recent_cases[{position}].closed_at")
        validate_artifact_id(row["result_artifact_id"], f"recent_cases[{position}].result_artifact_id")
        validate_sha256(row["result_digest"], f"recent_cases[{position}].result_digest")

    validate_current_migration(index["migration"])

    if project_reader is not None:
        loaded_manifests: dict[str, dict[str, object]] = {}
        for collection, rows in (("active_cases", active_cases), ("recent_cases", recent_cases)):
            for position, row in enumerate(rows):
                manifest_path = validate_case_manifest_path(
                    row["manifest_path"],
                    f"{collection}[{position}].manifest_path",
                    expected_case_id=str(row["case_id"]),
                )
                text = project_reader.read_text(manifest_path, f"{collection}[{position}].manifest", require_single_link=True)
                try:
                    manifest = json.loads(text)
                except json.JSONDecodeError as exc:
                    fail(f"{collection}[{position}].manifest is invalid JSON: {exc}")
                validate_current_case_manifest(
                    manifest,
                    Path(manifest_path.as_posix()),
                    project_reader,
                    raw_bytes=len(text.encode("utf-8")),
                    expected_case_id=str(row["case_id"]),
                    expected_revision=str(row["manifest_revision"]) if collection == "active_cases" else None,
                    migration_read=migration_read,
                )
                loaded_manifests[str(row["case_id"])] = manifest
                if collection == "recent_cases":
                    require(manifest["status"] == "closed", f"{collection}[{position}].manifest must be closed")
                    artifacts = manifest["artifacts"]
                    assert isinstance(artifacts, dict)
                    artifact = artifacts.get(row["result_artifact_id"])
                    require(isinstance(artifact, dict), f"{collection}[{position}].result_artifact_id must exist in manifest")
                    assert isinstance(artifact, dict)
                    require(artifact.get("role") == "result", f"{collection}[{position}].result_artifact_id must be a result")
                    require(artifact.get("byte_digest") == row["result_digest"], f"{collection}[{position}].result_digest must match manifest")
        if not migration_read:
            cases_root = project_reader.project_root / "docs/teamwork/cases"
            if cases_root.exists():
                cases_info = cases_root.lstat()
                require(
                    stat.S_ISDIR(cases_info.st_mode)
                    and not stat.S_ISLNK(cases_info.st_mode)
                    and cases_info.st_dev == project_reader.root_device,
                    "project cases root must be a same-device non-symlink directory",
                )
                for case_directory in sorted(cases_root.iterdir(), key=lambda item: item.name):
                    case_info = case_directory.lstat()
                    require(
                        CASE_ID_RE.fullmatch(case_directory.name) is not None
                        and stat.S_ISDIR(case_info.st_mode)
                        and not stat.S_ISLNK(case_info.st_mode)
                        and case_info.st_dev == project_reader.root_device,
                        "project cases root may contain only safe case-id directories",
                    )
                    manifest_path = PurePosixPath(f"docs/teamwork/cases/{case_directory.name}/manifest.json")
                    if case_directory.name not in loaded_manifests:
                        manifest_text = project_reader.read_text(
                            manifest_path,
                            f"unindexed case {case_directory.name} manifest",
                            require_single_link=True,
                        )
                        try:
                            manifest = json.loads(manifest_text)
                        except json.JSONDecodeError as exc:
                            fail(f"unindexed case {case_directory.name} manifest is invalid JSON: {exc}")
                        validate_current_case_manifest(
                            manifest,
                            Path(manifest_path.as_posix()),
                            project_reader,
                            raw_bytes=len(manifest_text.encode("utf-8")),
                            expected_case_id=case_directory.name,
                        )
                        loaded_manifests[case_directory.name] = manifest
                    manifest = loaded_manifests[case_directory.name]
                    document = manifest.get("document")
                    expected_names = {"manifest.json"}
                    if isinstance(document, dict):
                        expected_names.add("live.md")
                    observed_names: set[str] = set()
                    for child in case_directory.iterdir():
                        child_info = child.lstat()
                        require(
                            stat.S_ISREG(child_info.st_mode)
                            and not stat.S_ISLNK(child_info.st_mode)
                            and child_info.st_dev == project_reader.root_device
                            and child_info.st_nlink == 1,
                            f"case {case_directory.name} may contain only manifest.json and live.md files",
                        )
                        observed_names.add(child.name)
                    require(
                        observed_names == expected_names,
                        f"case {case_directory.name} must contain exactly manifest.json"
                        + (" and live.md" if "live.md" in expected_names else ""),
                    )
        for alias, row in aliases.items():
            manifest = loaded_manifests.get(str(row["target_id"]))
            require(manifest is not None, f"aliases.{alias} target must exist")
            require(computed_case_manifest_revision(manifest) == row["manifest_revision"], f"aliases.{alias}.manifest_revision must match target")
        for claim_id, row in claim_heads.items():
            manifest = loaded_manifests.get(str(row["case_id"]))
            require(manifest is not None, f"claim_heads[{claim_id}] case must exist")
            claims = manifest["claims"]
            artifacts = manifest["artifacts"]
            assert isinstance(claims, dict) and isinstance(artifacts, dict)
            claim = claims.get(claim_id)
            require(isinstance(claim, dict), f"claim_heads[{claim_id}] claim must exist in manifest")
            assert isinstance(claim, dict)
            require(claim.get("status") == "active", f"claim_heads[{claim_id}] claim must be active")
            require(claim.get("head_artifact_id") == row["artifact_id"], f"claim_heads[{claim_id}].artifact_id must match manifest claim")
            require(claim.get("head_digest") == row["artifact_digest"], f"claim_heads[{claim_id}].artifact_digest must match manifest claim")
            artifact = artifacts.get(row["artifact_id"])
            require(isinstance(artifact, dict), f"claim_heads[{claim_id}] artifact must exist in manifest")
            assert isinstance(artifact, dict)
            require(artifact.get("byte_digest") == row["artifact_digest"], f"claim_heads[{claim_id}].artifact_digest must match manifest artifact")


def validate_current_case_manifest(
    manifest: object,
    manifest_path: Path,
    project_reader: SafeProjectReader | None = None,
    *,
    raw_bytes: int | None = None,
    expected_case_id: str | None = None,
    expected_revision: str | None = None,
    migration_read: bool = False,
) -> None:
    if raw_bytes is not None:
        require(raw_bytes <= CURRENT_MANIFEST_MAX_BYTES, "case manifest exceeds 262144 bytes")
    require(isinstance(manifest, dict), "case manifest root must be an object")
    assert isinstance(manifest, dict)
    base_fields = {
        "schema_version",
        "case_id",
        "case_seed_b64",
        "created_at",
        "closed_at",
        "status",
        "claims",
        "artifacts",
        "history",
        "references",
        "runtime",
        "migration_sources",
    }
    manifest_schema = manifest.get("schema_version")
    expected = base_fields if manifest_schema == 1 else base_fields | {"document"}
    require(set(manifest) == expected, "case manifest top-level fields are invalid")
    require(
        manifest_schema in ({1, 2} if migration_read else {2}),
        "case manifest requires explicit project migration" if migration_read else "case manifest schema_version must be 2",
    )
    case_id = validate_case_id(manifest["case_id"], "case_id")
    if expected_case_id is not None:
        require(case_id == expected_case_id, "case manifest case_id does not match index")
    case_seed_b64 = manifest["case_seed_b64"]
    require(isinstance(case_seed_b64, str), "case_seed_b64 must be base64 text")
    assert isinstance(case_seed_b64, str)
    try:
        seed = base64.b64decode(case_seed_b64.encode("ascii"), validate=True)
    except Exception as exc:
        fail(f"case_seed_b64 must be valid base64: {exc}")
    require(len(seed) == 32, "case_seed_b64 must encode exactly 32 bytes")
    require(manifest["status"] in CURRENT_CASE_LIFECYCLES, "status is invalid")
    validate_utc_timestamp(manifest["created_at"], "created_at")
    closed_at = manifest["closed_at"]
    require(closed_at is None or isinstance(closed_at, str), "closed_at must be null or a UTC timestamp")
    if isinstance(closed_at, str):
        validate_utc_timestamp(closed_at, "closed_at")
    require((manifest["status"] == "closed") == (closed_at is not None), "closed_at must agree with status")
    if expected_revision is not None:
        require(computed_case_manifest_revision(manifest) == expected_revision, "case manifest revision does not match index")

    claims = manifest["claims"]
    require(isinstance(claims, dict), "claims must be an object")
    assert isinstance(claims, dict)
    require(len(claims) <= CURRENT_MANIFEST_CLAIMS_MAX, "claims exceeds 256 records")
    for claim_id, row in claims.items():
        validate_claim_id(claim_id, f"claims key {claim_id!r}")
        require(isinstance(row, dict), f"claims[{claim_id}] must be an object")
        assert isinstance(row, dict)
        require(set(row) == {"descriptor_version", "descriptor_digest", "status", "acquired_at", "released_at", "head_artifact_id", "head_digest"}, f"claims[{claim_id}] has invalid fields")
        require(row["descriptor_version"] == 1, f"claims[{claim_id}].descriptor_version must be 1")
        validate_sha256(row["descriptor_digest"], f"claims[{claim_id}].descriptor_digest")
        require(row["status"] in {"active", "released"}, f"claims[{claim_id}].status is invalid")
        validate_utc_timestamp(row["acquired_at"], f"claims[{claim_id}].acquired_at")
        released_at = row["released_at"]
        require(released_at is None or isinstance(released_at, str), f"claims[{claim_id}].released_at must be null or timestamp")
        if isinstance(released_at, str):
            validate_utc_timestamp(released_at, f"claims[{claim_id}].released_at")
        require((row["status"] == "released") == (released_at is not None), f"claims[{claim_id}].released_at must agree with status")
        validate_artifact_id(row["head_artifact_id"], f"claims[{claim_id}].head_artifact_id")
        validate_sha256(row["head_digest"], f"claims[{claim_id}].head_digest")

    artifacts = manifest["artifacts"]
    require(isinstance(artifacts, dict), "artifacts must be an object")
    assert isinstance(artifacts, dict)
    require(len(artifacts) <= CURRENT_MANIFEST_ARTIFACTS_MAX, "artifacts exceeds 2048 records")
    for artifact_id, row in artifacts.items():
        validate_artifact_id(artifact_id, f"artifacts key {artifact_id!r}")
        require(isinstance(row, dict), f"artifacts[{artifact_id}] must be an object")
        assert isinstance(row, dict)
        require(
            set(row) == {"role", "subtype", "path", "envelope_digest", "byte_digest", "created_at", "immutable", "consumer", "source_revision"},
            f"artifacts[{artifact_id}] has invalid fields",
        )
        validate_kebab(row["role"], f"artifacts[{artifact_id}].role")
        validate_kebab(row["subtype"], f"artifacts[{artifact_id}].subtype")
        validate_case_artifact_path(row["path"], f"artifacts[{artifact_id}].path", case_id)
        validate_sha256(row["envelope_digest"], f"artifacts[{artifact_id}].envelope_digest")
        validate_sha256(row["byte_digest"], f"artifacts[{artifact_id}].byte_digest")
        validate_utc_timestamp(row["created_at"], f"artifacts[{artifact_id}].created_at")
        require(row["immutable"] is True, f"artifacts[{artifact_id}].immutable must be true")
        require(isinstance(row["consumer"], str) and row["consumer"].strip(), f"artifacts[{artifact_id}].consumer must be text")
        validate_sha256(row["source_revision"], f"artifacts[{artifact_id}].source_revision")

    if manifest_schema == 2:
        document = manifest["document"]
        if document is not None:
            require(isinstance(document, dict), "document must be null or an object")
            assert isinstance(document, dict)
            require(
                set(document) == {
                    "path", "generation", "byte_digest", "updated_at", "title",
                    "purpose", "status", "needs_resolution", "latest_artifact_id",
                    "source_artifact_ids",
                },
                "document has invalid fields",
            )
            live_path = validate_case_artifact_path(document["path"], "document.path", case_id)
            require(
                live_path.as_posix() == f"docs/teamwork/cases/{case_id}/live.md",
                "document.path must be the case live.md",
            )
            generation = document["generation"]
            require(
                isinstance(generation, int) and not isinstance(generation, bool) and generation >= 1,
                "document.generation must be a positive integer",
            )
            validate_sha256(document["byte_digest"], "document.byte_digest")
            validate_utc_timestamp(document["updated_at"], "document.updated_at")
            require(isinstance(document["title"], str) and document["title"].strip(), "document.title must be text")
            require(document["purpose"] in CURRENT_LIVE_PURPOSES, "document.purpose is invalid")
            require(document["status"] in CURRENT_LIVE_STATUSES, "document.status is invalid")
            require(isinstance(document["needs_resolution"], bool), "document.needs_resolution must be boolean")
            latest_id = validate_artifact_id(document["latest_artifact_id"], "document.latest_artifact_id")
            require(latest_id in artifacts, "document.latest_artifact_id must exist in artifacts")
            source_ids = document["source_artifact_ids"]
            require(isinstance(source_ids, list), "document.source_artifact_ids must be an array")
            assert isinstance(source_ids, list)
            normalized_sources = [validate_artifact_id(item, "document.source_artifact_ids item") for item in source_ids]
            require(len(normalized_sources) == len(set(normalized_sources)), "document source artifact ids must be unique")
            require(all(item in artifacts for item in normalized_sources), "document source artifact ids must exist in artifacts")
            if project_reader is not None:
                live_text = project_reader.read_text(live_path, "case live document", require_single_link=True)
                require(hashlib.sha256(live_text.encode("utf-8")).hexdigest() == document["byte_digest"], "live document digest must match manifest")
                envelope = {
                    line.split(": ", 1)[0]: line.split(": ", 1)[1]
                    for line in live_text.splitlines()[:7]
                    if ": " in line
                }
                require(live_text.startswith("Teamwork Live Document: 1\n"), "live document schema is invalid")
                require(envelope.get("Case ID") == case_id, "live document case id is invalid")
                require(envelope.get("Purpose") == document["purpose"], "live document purpose differs from manifest")
                require(envelope.get("Status") == document["status"], "live document status differs from manifest")
                require(envelope.get("Generation") == str(generation), "live document generation differs from manifest")
                require(envelope.get("Last Updated") == document["updated_at"], "live document updated_at differs from manifest")
                require(envelope.get("Needs Resolution") == ("yes" if document["needs_resolution"] else "no"), "live document resolution state differs from manifest")

    for collection, limit in (
        ("history", CURRENT_MANIFEST_HISTORY_MAX),
        ("references", CURRENT_MANIFEST_REFS_MAX),
        ("migration_sources", CURRENT_MANIFEST_MIGRATION_SOURCES_MAX),
    ):
        rows = manifest[collection]
        require(isinstance(rows, list), f"{collection} must be an array")
        assert isinstance(rows, list)
        require(len(rows) <= limit, f"{collection} exceeds {limit} records")
        seen: set[str] = set()
        for position, row in enumerate(rows):
            require(isinstance(row, dict), f"{collection}[{position}] must be an object")
            assert isinstance(row, dict)
            if collection == "history":
                require(set(row) == {"artifact_id", "role", "superseded_by", "retained_reason", "recorded_at"}, f"{collection}[{position}] has invalid fields")
                artifact_id = validate_artifact_id(row["artifact_id"], f"{collection}[{position}].artifact_id")
                validate_kebab(row["role"], f"{collection}[{position}].role")
                superseded_by = row["superseded_by"]
                require(superseded_by is None or isinstance(superseded_by, str), f"{collection}[{position}].superseded_by must be null or artifact id")
                if isinstance(superseded_by, str):
                    validate_artifact_id(superseded_by, f"{collection}[{position}].superseded_by")
                require(row["retained_reason"] in {"consumed", "reviewed", "superseded", "closed"}, f"{collection}[{position}].retained_reason is invalid")
                validate_utc_timestamp(row["recorded_at"], f"{collection}[{position}].recorded_at")
                key = artifact_id
            elif collection == "references":
                require(set(row) == {"case_id", "claim_id", "artifact_id", "digest"}, f"{collection}[{position}] has invalid fields")
                validate_case_id(row["case_id"], f"{collection}[{position}].case_id")
                validate_claim_id(row["claim_id"], f"{collection}[{position}].claim_id")
                validate_artifact_id(row["artifact_id"], f"{collection}[{position}].artifact_id")
                validate_sha256(row["digest"], f"{collection}[{position}].digest")
                key = str(row["digest"])
            else:
                require(set(row) == {"source_path", "source_digest", "classification", "migration_id", "artifact_id"}, f"{collection}[{position}] has invalid fields")
                validate_any_relative_path(row["source_path"], f"{collection}[{position}].source_path")
                validate_sha256(row["source_digest"], f"{collection}[{position}].source_digest")
                validate_kebab(row["classification"], f"{collection}[{position}].classification")
                validate_migration_id(row["migration_id"], f"{collection}[{position}].migration_id")
                artifact_id = validate_artifact_id(row["artifact_id"], f"{collection}[{position}].artifact_id")
                require(artifact_id in artifacts, f"{collection}[{position}].artifact_id must exist in artifacts")
                key = str(row["source_path"])
            require(key not in seen, f"{collection} must not duplicate paths")
            seen.add(key)

    runtime = manifest["runtime"]
    require(isinstance(runtime, dict), "runtime must be an object")
    assert isinstance(runtime, dict)
    require(set(runtime) == {"active_route", "state_revision"}, "runtime has invalid fields")
    active_route = validate_memory_path(runtime["active_route"], "runtime.active_route")
    require(
        len(active_route.parts) >= 5 and active_route.parts[:4] == ("docs", "teamwork", "cases", case_id),
        "runtime.active_route must stay inside its case",
    )
    validate_sha256(runtime["state_revision"], "runtime.state_revision")
    if manifest_schema == 2 and not migration_read:
        document = manifest["document"]
        if document is None:
            require(not artifacts and not manifest["history"] and not manifest["references"] and not manifest["migration_sources"], "a current manifest without live.md must not retain artifacts")
        else:
            assert isinstance(document, dict)
            latest_id = str(document["latest_artifact_id"])
            require(set(artifacts) == {latest_id}, "a current manifest may index only live.md")
            latest = artifacts[latest_id]
            require(latest["path"] == document["path"], "live.md artifact path must match document")
            require(latest["byte_digest"] == document["byte_digest"], "live.md artifact digest must match document")
            require(not manifest["history"] and not manifest["references"], "current manifests do not retain artifact history or references")
            require(
                all(row["artifact_id"] == latest_id for row in manifest["migration_sources"]),
                "all migration provenance must target live.md",
            )
            require(all(claim["head_artifact_id"] == latest_id for claim in claims.values()), "all current claim heads must target live.md")


def validate_index(
    index: object,
    index_path: Path,
    project_reader: SafeProjectReader | None = None,
    *,
    migration_read: bool = False,
    raw_bytes: int | None = None,
) -> None:
    require(isinstance(index, dict), "index root must be an object")
    assert isinstance(index, dict)
    version = index.get("schema_version")
    if version == 1:
        validate_v1_index(index, index_path, project_reader, migration_read=migration_read)
    elif version == 2 and migration_read:
        validate_current_root_index(index, index_path, project_reader, raw_bytes=raw_bytes, migration_read=True)
    elif version == 3:
        validate_current_root_index(index, index_path, project_reader, raw_bytes=raw_bytes)
    else:
        fail("schema_version must be current version 3; older versions require explicit project migration")


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
    try:
        index = json.loads(index_text)
    except json.JSONDecodeError as exc:
        fail(f"memory index template is invalid JSON: {exc}")
    validate_index(index, directory / "index.json", raw_bytes=len(index_text.encode("utf-8")))
    require(index.get("schema_version") == 3, "memory index template must use schema_version 3")
    combined = index_text.casefold()
    for forbidden in (
        "discussion-transaction",
        "using-teamwork/scripts",
        "docs/teamwork/current.md",
        "docs/teamwork/readme.md",
    ):
        require(forbidden not in combined, f"ordinary memory templates must not contain {forbidden!r}")
    live_template = read_regular_text(directory / "teamwork-live-template.md", "Writer live document template")
    for required in (
        "Teamwork Live Document: 1",
        "Case ID: {{case_id}}",
        "Purpose: {{purpose}}",
        "Status: {{status}}",
        "Generation: {{generation}}",
        "Needs Resolution: {{needs_resolution}}",
        "{{purpose_specific_sections}}",
    ):
        require(required in live_template, f"Writer live document template is missing {required!r}")
    folded = live_template.casefold()
    for forbidden in ("case-inspect", "case-schema", "case-apply", "sha256", "transaction"):
        require(forbidden not in folded, f"Writer live document template must hide storage mechanic {forbidden!r}")


def canonical_project_root(index_path: Path) -> Path | None:
    if (
        index_path.name == "index.json"
        and index_path.parent.name == "teamwork"
        and index_path.parent.parent.name == "docs"
    ):
        return index_path.parent.parent.parent
    return None


def canonical_case_project_root(manifest_path: Path) -> Path | None:
    parts = manifest_path.parts
    if (
        manifest_path.name == "manifest.json"
        and len(parts) >= 5
        and parts[-5:-2] == ("docs", "teamwork", "cases")
        and CASE_ID_RE.fullmatch(parts[-2]) is not None
    ):
        return Path(*parts[:-5]) if parts[:-5] else Path("/")
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
            value = json.loads(text)
        except json.JSONDecodeError as exc:
            fail(f"invalid JSON: {exc}")
        if path.parent.name == "teamwork-memory" and path.parent.parent.name == "templates":
            validate_memory_templates(path.parent)
        elif (case_root := canonical_case_project_root(path)) is not None:
            reader = SafeProjectReader(case_root)
            try:
                validate_current_case_manifest(
                    value,
                    path,
                    reader,
                    raw_bytes=len(text.encode("utf-8")),
                    expected_case_id=path.parent.name,
                )
            finally:
                reader.close()
        elif (root := canonical_project_root(path)) is not None:
            reader = SafeProjectReader(root)
            try:
                validate_index(
                    value,
                    path,
                    reader,
                    migration_read=arguments.migration_read,
                    raw_bytes=len(text.encode("utf-8")),
                )
            finally:
                reader.close()
        else:
            validate_index(
                value,
                path,
                migration_read=arguments.migration_read,
                raw_bytes=len(text.encode("utf-8")),
            )
    except ValidationError as exc:
        print(f"invalid Teamwork index: {exc}", file=sys.stderr)
        return 1
    print(f"valid Teamwork index: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
