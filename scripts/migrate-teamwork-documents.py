#!/usr/bin/env python3
"""Mechanical staging, coverage, cutover, readback, and rollback for Teamwork v4.

The helper never interprets or rewrites document bodies. Writer creates the
typed documents and coverage choices in external staging; Reviewer judges the
actual result. This script only inventories paths, checks registration and
coverage, copies an explicit external backup, and switches the exact
<project>/docs/teamwork tree.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
import sys
from pathlib import Path, PurePosixPath
from typing import NoReturn

from teamwork_index_v4 import (
    DOCUMENT_DIRECTORIES,
    IndexValidationError,
    load_index,
    validate_document_files,
    validate_index,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
INDEX_TEMPLATE = REPOSITORY_ROOT / "templates/teamwork-memory/index.json"
STATE_NAME = "migration-state.json"
COVERAGE_NAME = "coverage.json"
STATE_FIELDS = {
    "mechanics_version",
    "phase",
    "project_root",
    "backup_root",
    "source_schema_version",
    "source_cases",
    "source_entries",
}
PHASES = {"prepared", "cutover", "rolled-back"}
DISPOSITIONS = {"migrated", "consolidated", "obsolete-storage-only"}
TYPED_DIRECTORIES = set(DOCUMENT_DIRECTORIES.values())
LEGACY_ANCHORS = {"cases", "current.md", "README.md", "discussion", "collaborate", "design"}
SWAP_NEW_NAME = ".teamwork-migration-new"
SWAP_OLD_NAME = ".teamwork-migration-old"


class MigrationError(RuntimeError):
    pass


def fail(message: str) -> NoReturn:
    raise MigrationError(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def _absolute_path(raw: str, label: str, *, must_exist: bool) -> Path:
    require(bool(raw) and not any(ord(character) < 32 or ord(character) == 127 for character in raw), f"{label} must not contain control characters")
    supplied = Path(raw).expanduser()
    require(supplied.is_absolute(), f"{label} must be an absolute path")
    path = Path(os.path.abspath(supplied))
    require(str(supplied) == str(path), f"{label} must be normalized")
    require(path != Path(path.anchor), f"{label} must not be a filesystem root")
    current = Path(path.anchor)
    for part in path.parts[1:]:
        current /= part
        try:
            info = current.lstat()
        except FileNotFoundError:
            break
        except OSError as exc:
            fail(f"cannot inspect {label} component {current}: {exc}")
        require(not stat.S_ISLNK(info.st_mode), f"{label} must not contain symlink components: {current}")
        if current != path:
            require(stat.S_ISDIR(info.st_mode), f"{label} parent must be a directory: {current}")
    if must_exist:
        require(path.exists(), f"{label} does not exist: {path}")
        info = path.lstat()
        require(stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode), f"{label} must be a non-symlink directory: {path}")
    return path


def _inside(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _external_roots(project_root: Path, staging_root: Path, backup_root: Path) -> None:
    require(not _inside(staging_root, project_root), "staging root must be external to the project")
    require(not _inside(backup_root, project_root), "backup root must be external to the project")
    require(not _inside(project_root, staging_root), "staging root must not contain the project")
    require(not _inside(project_root, backup_root), "backup root must not contain the project")
    require(not _inside(staging_root, backup_root) and not _inside(backup_root, staging_root), "staging and backup roots must be separate")


def _safe_tree_entries(root: Path, label: str) -> list[dict[str, object]]:
    require(root.exists(), f"{label} does not exist: {root}")
    root_info = root.lstat()
    require(stat.S_ISDIR(root_info.st_mode) and not stat.S_ISLNK(root_info.st_mode), f"{label} must be a non-symlink directory")
    entries: list[dict[str, object]] = []
    for current, directories, files in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        directories.sort()
        files.sort()
        for name in directories:
            path = current_path / name
            info = path.lstat()
            require(stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode), f"{label} contains an unsafe directory: {path}")
            entries.append({"path": path.relative_to(root).as_posix(), "type": "directory"})
        for name in files:
            path = current_path / name
            info = path.lstat()
            require(stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode), f"{label} contains an unsafe file: {path}")
            entries.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "type": "file",
                    "size": info.st_size,
                    "mtime_ns": info.st_mtime_ns,
                }
            )
    return sorted(entries, key=lambda item: (str(item["path"]), str(item["type"])))


def _read_json(path: Path, label: str) -> object:
    try:
        info = path.lstat()
        require(stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode), f"{label} must be a regular non-symlink file")
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        fail(f"cannot read {label} {path}: {exc}")


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / f".{path.name}.tmp"
    require(not temporary.exists() and not temporary.is_symlink(), f"temporary path already exists: {temporary}")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise


def _project_memory(project_root: Path) -> Path:
    docs = project_root / "docs"
    memory = docs / "teamwork"
    require(docs.exists() and docs.is_dir() and not docs.is_symlink(), "project docs must be a non-symlink directory")
    require(memory.exists() and memory.is_dir() and not memory.is_symlink(), "project docs/teamwork must be a non-symlink directory")
    return memory


def inventory_project(project_root: Path, *, allow_current: bool = False) -> dict[str, object]:
    memory = _project_memory(project_root)
    entries = _safe_tree_entries(memory, "project Teamwork memory")
    raw_index = _read_json(memory / "index.json", "Teamwork source index")
    require(isinstance(raw_index, dict), "Teamwork source index must be an object")
    assert isinstance(raw_index, dict)
    version = raw_index.get("schema_version")
    require(isinstance(version, int), "Teamwork source index has no integer schema_version")
    top_names = {path.name for path in memory.iterdir()}
    if version == 4:
        require(allow_current, "project already uses schema v4; no legacy migration inventory is needed")
        try:
            index = load_index(memory / "index.json")
            validate_document_files(index, memory)
        except IndexValidationError as exc:
            fail(str(exc))
        return {
            "source_schema_version": 4,
            "format": "typed-v4",
            "source_count": 0,
            "source_cases": [],
            "source_entries": entries,
            "writer_required": False,
            "reviewer_required": False,
        }
    require(version in {1, 2, 3}, "unsupported Teamwork source schema; explicit migration cannot inventory it")
    require(not (top_names & TYPED_DIRECTORIES), "mixed legacy and schema-v4 typed directories are not allowed")

    source_cases: list[dict[str, object]] = []
    cases_root = memory / "cases"
    if version in {2, 3}:
        require(not (top_names & (LEGACY_ANCHORS - {"cases"})), "mixed legacy Teamwork storage formats are not allowed")
        if cases_root.exists():
            require(cases_root.is_dir() and not cases_root.is_symlink(), "legacy cases must be a non-symlink directory")
            for case_root in sorted(cases_root.iterdir(), key=lambda item: item.name):
                info = case_root.lstat()
                require(stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode), f"legacy cases contains an unsafe entry: {case_root}")
                case_entries = _safe_tree_entries(case_root, f"legacy source case {case_root.name}")
                content_paths = [
                    (case_root / entry["path"]).relative_to(project_root).as_posix()
                    for entry in case_entries
                    if entry["type"] == "file"
                ]
                require(any(path.endswith("/manifest.json") for path in content_paths), f"legacy source case has no manifest.json: {case_root.name}")
                source_cases.append(
                    {
                        "source_case": case_root.relative_to(project_root).as_posix(),
                        "content_paths": content_paths,
                    }
                )
    else:
        require(not cases_root.exists(), "schema-v1 memory mixed with case storage is not allowed")
        for entry in entries:
            entry_path = str(entry["path"])
            if entry["type"] != "file" or not entry_path.endswith(".md"):
                continue
            source = (memory / entry_path).relative_to(project_root).as_posix()
            source_cases.append({"source_case": source, "content_paths": [source]})
    return {
        "source_schema_version": version,
        "format": "case-bundle" if version in {2, 3} else "legacy-index",
        "source_count": len(source_cases),
        "source_cases": source_cases,
        "source_entries": entries,
        "writer_required": True,
        "reviewer_required": True,
    }


def _new_staging_index(project_root: Path, source_index: dict[str, object]) -> dict[str, object]:
    template = _read_json(INDEX_TEMPLATE, "schema-v4 index template")
    require(isinstance(template, dict), "schema-v4 index template must be an object")
    assert isinstance(template, dict)
    source_project = source_index.get("project")
    if isinstance(source_project, dict) and isinstance(source_project.get("name"), str) and source_project["name"].strip():
        template["project"]["name"] = source_project["name"].strip()
    else:
        template["project"]["name"] = project_root.name
    validate_index(template)
    return template


def _state_path(staging_root: Path) -> Path:
    return staging_root / STATE_NAME


def _coverage_path(staging_root: Path) -> Path:
    return staging_root / COVERAGE_NAME


def _load_state(staging_root: Path) -> dict[str, object]:
    value = _read_json(_state_path(staging_root), "migration mechanics state")
    require(isinstance(value, dict) and set(value) == STATE_FIELDS, "migration mechanics state has invalid fields")
    assert isinstance(value, dict)
    require(value["mechanics_version"] == 1, "migration mechanics state version is unsupported")
    require(value["phase"] in PHASES, "migration mechanics phase is invalid")
    require(isinstance(value["project_root"], str) and isinstance(value["backup_root"], str), "migration mechanics paths are invalid")
    require(value["source_schema_version"] in {1, 2, 3}, "migration source schema is invalid")
    require(isinstance(value["source_cases"], list) and isinstance(value["source_entries"], list), "migration source inventory is invalid")
    return value


def prepare(project_root: Path, staging_root: Path, backup_root: Path) -> dict[str, object]:
    _external_roots(project_root, staging_root, backup_root)
    require(not staging_root.exists() and not staging_root.is_symlink(), "staging root must not already exist")
    require(not backup_root.exists() and not backup_root.is_symlink(), "backup root must not already exist")
    inventory = inventory_project(project_root)
    require(inventory["source_count"] > 0, "legacy inventory contains no source documents for Writer")
    memory = _project_memory(project_root)
    source_index = _read_json(memory / "index.json", "Teamwork source index")
    assert isinstance(source_index, dict)
    try:
        staging_memory = staging_root / "docs/teamwork"
        staging_memory.mkdir(parents=True)
        _write_json(staging_memory / "index.json", _new_staging_index(project_root, source_index))
        (backup_root / "docs").mkdir(parents=True)
        shutil.copytree(memory, backup_root / "docs/teamwork")
        source_cases = inventory["source_cases"]
        assert isinstance(source_cases, list)
        coverage = {
            "source_cases": [
                {"source_case": row["source_case"], "disposition": None, "documents": []}
                for row in source_cases
                if isinstance(row, dict)
            ]
        }
        _write_json(_coverage_path(staging_root), coverage)
        state = {
            "mechanics_version": 1,
            "phase": "prepared",
            "project_root": str(project_root),
            "backup_root": str(backup_root),
            "source_schema_version": inventory["source_schema_version"],
            "source_cases": source_cases,
            "source_entries": inventory["source_entries"],
        }
        _write_json(_state_path(staging_root), state)
        require(_safe_tree_entries(backup_root / "docs/teamwork", "external Teamwork backup") == inventory["source_entries"], "external backup inventory does not cover the source tree")
    except BaseException:
        if staging_root.exists() and not staging_root.is_symlink():
            shutil.rmtree(staging_root)
        if backup_root.exists() and not backup_root.is_symlink():
            shutil.rmtree(backup_root)
        raise
    return {
        "status": "prepared",
        "source_count": inventory["source_count"],
        "staging_root": str(staging_root),
        "backup_root": str(backup_root),
        "writer_required": True,
        "reviewer_required": True,
    }


def _registered_paths(index: dict[str, object]) -> set[str]:
    result: set[str] = set()
    tasks = index["tasks"]
    assert isinstance(tasks, dict)
    for task in tasks.values():
        assert isinstance(task, dict)
        documents = task["documents"]
        assert isinstance(documents, list)
        for document in documents:
            assert isinstance(document, dict)
            result.add(str(document["path"]))
    return result


def _validate_typed_memory(memory: Path) -> tuple[dict[str, object], set[str]]:
    try:
        index = load_index(memory / "index.json")
        validate_document_files(index, memory)
    except IndexValidationError as exc:
        fail(str(exc))
    top_names = {path.name for path in memory.iterdir()}
    require(not (top_names & LEGACY_ANCHORS), "schema-v4 candidate contains a legacy live/case route")
    require(top_names <= {"index.json", *TYPED_DIRECTORIES}, "schema-v4 candidate contains unsupported runtime entries")
    registered = _registered_paths(index)
    actual_documents: set[str] = set()
    for directory in TYPED_DIRECTORIES:
        root = memory / directory
        if not root.exists():
            continue
        require(root.is_dir() and not root.is_symlink(), f"typed directory is unsafe: {root}")
        for entry in _safe_tree_entries(root, f"typed directory {directory}"):
            require(entry["type"] == "file", f"typed directory must not contain nested directories: {directory}/{entry['path']}")
            require(str(entry["path"]).endswith(".md"), f"typed directory contains a non-Markdown file: {directory}/{entry['path']}")
            actual_documents.add(f"docs/teamwork/{directory}/{entry['path']}")
    require(actual_documents == registered, "typed document files and index registrations do not match")
    return index, registered


def validate_coverage(staging_root: Path) -> dict[str, object]:
    state = _load_state(staging_root)
    staging_memory = staging_root / "docs/teamwork"
    index, registered = _validate_typed_memory(staging_memory)
    raw = _read_json(_coverage_path(staging_root), "temporary migration coverage map")
    require(isinstance(raw, dict) and set(raw) == {"source_cases"}, "coverage map has invalid fields")
    rows = raw["source_cases"]
    require(isinstance(rows, list), "coverage source_cases must be an array")
    expected_rows = state["source_cases"]
    assert isinstance(expected_rows, list)
    expected = {
        str(row["source_case"])
        for row in expected_rows
        if isinstance(row, dict) and isinstance(row.get("source_case"), str)
    }
    seen: set[str] = set()
    for position, row in enumerate(rows):
        require(isinstance(row, dict) and set(row) == {"source_case", "disposition", "documents"}, f"coverage source_cases[{position}] has invalid fields")
        assert isinstance(row, dict)
        source = row["source_case"]
        require(isinstance(source, str) and source in expected, f"coverage source_cases[{position}] has an unknown source_case")
        require(source not in seen, f"coverage repeats source_case: {source}")
        seen.add(source)
        disposition = row["disposition"]
        require(disposition in DISPOSITIONS, f"coverage source_cases[{position}] has an invalid disposition")
        documents = row["documents"]
        require(isinstance(documents, list) and all(isinstance(path, str) for path in documents), f"coverage source_cases[{position}].documents must be an array of paths")
        require(len(set(documents)) == len(documents), f"coverage source_cases[{position}].documents contains duplicates")
        if disposition in {"migrated", "consolidated"}:
            require(bool(documents), f"coverage {disposition} source must name at least one typed document: {source}")
            require(set(documents) <= registered, f"coverage source references an unregistered typed document: {source}")
        else:
            require(documents == [], f"obsolete-storage-only source must not name a typed document: {source}")
    require(seen == expected, "coverage map must cover every inventoried source case exactly once")
    return {
        "status": "coverage-valid",
        "source_count": len(expected),
        "registered_documents": len(registered),
        "reviewer_required": True,
        "index": index,
    }


def _checked_state_paths(project_root: Path, staging_root: Path, state: dict[str, object]) -> Path:
    require(str(project_root) == state["project_root"], "project root does not match migration mechanics state")
    backup_root = _absolute_path(str(state["backup_root"]), "backup root", must_exist=True)
    _external_roots(project_root, staging_root, backup_root)
    return backup_root


def _swap_paths(project_root: Path) -> tuple[Path, Path, Path, Path]:
    memory = _project_memory(project_root)
    docs = memory.parent
    new_tree = docs / SWAP_NEW_NAME
    old_tree = docs / SWAP_OLD_NAME
    for path in (new_tree, old_tree):
        require(
            not path.exists() and not path.is_symlink(),
            f"migration swap path must not already exist: {path}",
        )
    return docs, memory, new_tree, old_tree


def _remove_safe_tree(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return
    info = path.lstat()
    require(
        stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode),
        f"migration swap path is unsafe: {path}",
    )
    shutil.rmtree(path)


def _restore_exchange(memory: Path, new_tree: Path, old_tree: Path) -> None:
    """Restore old_tree after either rename boundary failed."""

    if old_tree.exists():
        if memory.exists():
            require(not new_tree.exists(), f"cannot recover while both active and new swap trees exist: {new_tree}")
            os.replace(memory, new_tree)
        os.replace(old_tree, memory)
    _remove_safe_tree(new_tree)


def _exchange_prepared_tree(
    memory: Path,
    new_tree: Path,
    old_tree: Path,
    validate_active: object,
) -> None:
    """Exchange a fully copied sibling tree and recover on rename/validation failure."""

    try:
        os.replace(memory, old_tree)
        os.replace(new_tree, memory)
        validate_active(memory)
    except BaseException:
        _restore_exchange(memory, new_tree, old_tree)
        raise
    try:
        shutil.rmtree(old_tree)
    except BaseException:
        # Do not accept a cutover that leaves a swap sibling. The old tree is
        # still present, so restore it before reporting the cleanup failure.
        _restore_exchange(memory, new_tree, old_tree)
        raise


def cutover(project_root: Path, staging_root: Path) -> dict[str, object]:
    state = _load_state(staging_root)
    require(state["phase"] in {"prepared", "rolled-back"}, "cutover requires a prepared or rolled-back migration")
    backup_root = _checked_state_paths(project_root, staging_root, state)
    coverage = validate_coverage(staging_root)
    current = inventory_project(project_root)
    require(current["source_schema_version"] == state["source_schema_version"], "source schema changed after staging")
    require(
        current["source_entries"] == state["source_entries"],
        "source file metadata or path inventory changed after staging",
    )
    backup_memory = backup_root / "docs/teamwork"
    require(_safe_tree_entries(backup_memory, "external Teamwork backup") == state["source_entries"], "external backup no longer covers the source path inventory")
    staging_memory = staging_root / "docs/teamwork"
    _docs, memory, new_tree, old_tree = _swap_paths(project_root)
    try:
        shutil.copytree(staging_memory, new_tree)
        _validate_typed_memory(new_tree)
        _exchange_prepared_tree(memory, new_tree, old_tree, _validate_typed_memory)
    except BaseException as exc:
        _remove_safe_tree(new_tree)
        fail(f"cutover failed before a complete swap; the original Teamwork tree remains active: {exc}")
    state["phase"] = "cutover"
    _write_json(_state_path(staging_root), state)
    return {
        "status": "cutover",
        "source_count": coverage["source_count"],
        "registered_documents": coverage["registered_documents"],
        "backup_root": str(backup_root),
        "reviewer_required": True,
    }


def readback(project_root: Path, staging_root: Path) -> dict[str, object]:
    state = _load_state(staging_root)
    _checked_state_paths(project_root, staging_root, state)
    require(state["phase"] == "cutover", "readback requires a completed cutover")
    index, registered = _validate_typed_memory(_project_memory(project_root))
    tasks = index["tasks"]
    assert isinstance(tasks, dict)
    return {
        "status": "readback-valid",
        "tasks": len(tasks),
        "registered_documents": len(registered),
        "reviewer_required": True,
    }


def rollback(project_root: Path, staging_root: Path) -> dict[str, object]:
    state = _load_state(staging_root)
    require(state["phase"] == "cutover", "rollback requires a completed cutover")
    backup_root = _checked_state_paths(project_root, staging_root, state)
    backup_memory = backup_root / "docs/teamwork"
    require(_safe_tree_entries(backup_memory, "external Teamwork backup") == state["source_entries"], "external backup no longer covers the source path inventory")
    _docs, memory, new_tree, old_tree = _swap_paths(project_root)

    def validate_restored(path: Path) -> None:
        require(
            _safe_tree_entries(path, "restored Teamwork memory") == state["source_entries"],
            "restored source path inventory is incomplete",
        )

    try:
        shutil.copytree(backup_memory, new_tree)
        validate_restored(new_tree)
        _exchange_prepared_tree(memory, new_tree, old_tree, validate_restored)
    except BaseException as exc:
        _remove_safe_tree(new_tree)
        fail(f"rollback failed before a complete swap; the schema-v4 Teamwork tree remains active: {exc}")
    state["phase"] = "rolled-back"
    _write_json(_state_path(staging_root), state)
    return {
        "status": "rolled-back",
        "source_count": len(state["source_cases"]),
        "backup_root": str(backup_root),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    inventory = sub.add_parser("inventory")
    inventory.add_argument("--project-root", required=True)
    prepare_parser = sub.add_parser("prepare")
    prepare_parser.add_argument("--project-root", required=True)
    prepare_parser.add_argument("--staging-root", required=True)
    prepare_parser.add_argument("--backup-root", required=True)
    for name in ("validate-coverage", "cutover", "readback", "rollback"):
        command = sub.add_parser(name)
        command.add_argument("--project-root", required=name in {"cutover", "readback", "rollback"})
        command.add_argument("--staging-root", required=True)
    return parser


def main() -> int:
    arguments = _parser().parse_args()
    try:
        if arguments.command == "inventory":
            project = _absolute_path(arguments.project_root, "project root", must_exist=True)
            result = inventory_project(project)
        elif arguments.command == "prepare":
            project = _absolute_path(arguments.project_root, "project root", must_exist=True)
            staging = _absolute_path(arguments.staging_root, "staging root", must_exist=False)
            backup = _absolute_path(arguments.backup_root, "backup root", must_exist=False)
            result = prepare(project, staging, backup)
        else:
            staging = _absolute_path(arguments.staging_root, "staging root", must_exist=True)
            if arguments.command == "validate-coverage":
                result = validate_coverage(staging)
                result.pop("index", None)
            else:
                project = _absolute_path(arguments.project_root, "project root", must_exist=True)
                if arguments.command == "cutover":
                    result = cutover(project, staging)
                elif arguments.command == "readback":
                    result = readback(project, staging)
                else:
                    result = rollback(project, staging)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (MigrationError, IndexValidationError) as exc:
        print(f"Teamwork document migration refused: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
