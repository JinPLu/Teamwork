#!/usr/bin/env python3
"""Schema-v4 Teamwork typed-document index and path operations.

This module owns only normalized paths, schema validation, safe discovery, and
explicit task/document registration or lifecycle updates.  It never reads,
summarizes, templates, or rewrites document bodies.  Writer decides whether a
change is a same-scope correction or materially new semantic scope: corrections
may keep a finalized path, while new scope must be registered at a new path.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
from datetime import date
from pathlib import Path, PurePosixPath
from typing import NoReturn


SCHEMA_VERSION = 4
DOCUMENT_DIRECTORIES = {
    "discussion": "discussions",
    "research": "research",
    "debug": "debug",
    "plan": "plans",
    "review": "reviews",
    "report": "reports",
}
DOCUMENT_STATUSES = {"active", "final"}
TASK_STATUSES = {"active", "final"}
TEMPLATE_FILES = {f"{name}.md" for name in DOCUMENT_DIRECTORIES}
CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
SEMANTIC_KEY_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
DOCUMENT_PATH_RE = re.compile(
    r"docs/teamwork/"
    r"(?P<directory>discussions|research|debug|plans|reviews|reports)/"
    r"(?P<day>\d{4}-\d{2}-\d{2})-"
    r"(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)\.md"
)
OPAQUE_HEX_RE = re.compile(r"(?:[a-f0-9]+-?){1,2}[a-f0-9]{24,}")


class IndexValidationError(ValueError):
    """The index or one of its registered paths violates schema v4."""


def fail(message: str) -> NoReturn:
    raise IndexValidationError(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def _plain_text(value: object, label: str, *, maximum: int) -> str:
    require(isinstance(value, str), f"{label} must be text")
    assert isinstance(value, str)
    require(value == value.strip() and bool(value), f"{label} must be non-empty trimmed text")
    require(not CONTROL_RE.search(value), f"{label} must not contain control characters")
    require(len(value) <= maximum, f"{label} is too long")
    return value


def validate_task_key(value: object, label: str = "task_key") -> str:
    key = _plain_text(value, label, maximum=120)
    require(SEMANTIC_KEY_RE.fullmatch(key) is not None, f"{label} must be normalized kebab-case")
    require(any(character.isalpha() for character in key), f"{label} must be human-readable")
    require(OPAQUE_HEX_RE.fullmatch(key) is None, f"{label} must not be an opaque identifier")
    return key


def validate_document_path(value: object, document_type: str | None = None, label: str = "path") -> PurePosixPath:
    text = _plain_text(value, label, maximum=240)
    path = PurePosixPath(text)
    require(
        not path.is_absolute()
        and "\\" not in text
        and path.as_posix() == text
        and all(part not in {"", ".", ".."} for part in path.parts),
        f"{label} must be a normalized project-relative path",
    )
    match = DOCUMENT_PATH_RE.fullmatch(text)
    require(match is not None, f"{label} must use docs/teamwork/<typed-dir>/YYYY-MM-DD-<semantic-slug>.md")
    assert match is not None
    try:
        date.fromisoformat(match.group("day"))
    except ValueError:
        fail(f"{label} contains an invalid calendar date")
    slug = match.group("slug")
    require(any(character.isalpha() for character in slug), f"{label} must use a semantic slug")
    require(OPAQUE_HEX_RE.fullmatch(slug) is None, f"{label} must not use an opaque slug")
    if document_type is not None:
        require(document_type in DOCUMENT_DIRECTORIES, f"{label} has an invalid document type")
        require(
            match.group("directory") == DOCUMENT_DIRECTORIES[document_type],
            f"{label} does not match document type {document_type!r}",
        )
    return path


def document_path(document_type: str, day: str, semantic_slug: str) -> str:
    require(document_type in DOCUMENT_DIRECTORIES, "document type is invalid")
    try:
        date.fromisoformat(day)
    except ValueError:
        fail("day must be a valid YYYY-MM-DD date")
    validate_task_key(semantic_slug, "semantic_slug")
    result = f"docs/teamwork/{DOCUMENT_DIRECTORIES[document_type]}/{day}-{semantic_slug}.md"
    validate_document_path(result, document_type)
    return result


def validate_index(index: object) -> dict[str, object]:
    require(isinstance(index, dict), "index must be a JSON object")
    assert isinstance(index, dict)
    version = index.get("schema_version")
    if version != SCHEMA_VERSION:
        fail("schema_version must be 4; older Teamwork formats require explicit Update migration")
    require(set(index) == {"schema_version", "project", "tasks"}, "index has invalid top-level fields")

    project = index["project"]
    require(isinstance(project, dict), "project must be an object")
    assert isinstance(project, dict)
    require(set(project) == {"name", "root", "description"}, "project has invalid fields")
    _plain_text(project["name"], "project.name", maximum=160)
    require(project["root"] == ".", "project.root must be '.'")
    _plain_text(project["description"], "project.description", maximum=280)

    tasks = index["tasks"]
    require(isinstance(tasks, dict), "tasks must be an object keyed by task_key")
    assert isinstance(tasks, dict)
    seen_paths: set[str] = set()
    for raw_key, raw_task in tasks.items():
        task_key = validate_task_key(raw_key, "tasks key")
        require(isinstance(raw_task, dict), f"tasks.{task_key} must be an object")
        task = raw_task
        assert isinstance(task, dict)
        require(
            set(task) == {"title", "summary", "search_terms", "status", "documents"},
            f"tasks.{task_key} has invalid fields",
        )
        _plain_text(task["title"], f"tasks.{task_key}.title", maximum=200)
        summary = _plain_text(task["summary"], f"tasks.{task_key}.summary", maximum=400)
        require("\n" not in summary and "\r" not in summary, f"tasks.{task_key}.summary must be one line")
        terms = task["search_terms"]
        require(isinstance(terms, list), f"tasks.{task_key}.search_terms must be an array")
        assert isinstance(terms, list)
        require(len(terms) <= 8, f"tasks.{task_key}.search_terms must stay small (at most 8)")
        normalized_terms: set[str] = set()
        for position, raw_term in enumerate(terms):
            term = _plain_text(raw_term, f"tasks.{task_key}.search_terms[{position}]", maximum=80)
            folded = term.casefold()
            require(folded not in normalized_terms, f"tasks.{task_key}.search_terms must not contain duplicates")
            normalized_terms.add(folded)
        require(task["status"] in TASK_STATUSES, f"tasks.{task_key}.status is invalid")
        documents = task["documents"]
        require(isinstance(documents, list), f"tasks.{task_key}.documents must be an array")
        assert isinstance(documents, list)
        for position, raw_document in enumerate(documents):
            label = f"tasks.{task_key}.documents[{position}]"
            require(isinstance(raw_document, dict), f"{label} must be an object")
            document = raw_document
            assert isinstance(document, dict)
            require(set(document) == {"type", "path", "status"}, f"{label} has invalid fields")
            document_type = document["type"]
            require(document_type in DOCUMENT_DIRECTORIES, f"{label}.type is invalid")
            path = validate_document_path(document["path"], str(document_type), f"{label}.path").as_posix()
            require(path not in seen_paths, f"document path is registered more than once: {path}")
            seen_paths.add(path)
            require(document["status"] in DOCUMENT_STATUSES, f"{label}.status is invalid")
        if task["status"] == "final":
            require(bool(documents), f"final task {task_key!r} must have at least one document")
            require(
                all(isinstance(item, dict) and item.get("status") == "final" for item in documents),
                f"final task {task_key!r} must not contain active documents",
            )
    return index


def load_index(index_path: Path) -> dict[str, object]:
    try:
        info = index_path.lstat()
        require(stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode), f"index must be a regular non-symlink file: {index_path}")
        value = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        fail(f"cannot read Teamwork index {index_path}: {exc}")
    return validate_index(value)


def _safe_regular_file(memory_root: Path, relative: PurePosixPath) -> Path:
    require(relative.parts[:2] == ("docs", "teamwork"), "registered path is outside docs/teamwork")
    current = memory_root
    try:
        root_info = current.lstat()
    except OSError as exc:
        fail(f"cannot inspect Teamwork memory root {current}: {exc}")
    require(stat.S_ISDIR(root_info.st_mode) and not stat.S_ISLNK(root_info.st_mode), f"Teamwork memory root must be a non-symlink directory: {current}")
    for part in relative.parts[2:-1]:
        current /= part
        try:
            info = current.lstat()
        except OSError as exc:
            fail(f"registered document parent is missing: {current}: {exc}")
        require(stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode), f"registered document parent must be a non-symlink directory: {current}")
    target = current / relative.name
    try:
        info = target.lstat()
    except OSError as exc:
        fail(f"registered document is missing: {target}: {exc}")
    require(stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode), f"registered document must be a regular non-symlink file: {target}")
    return target


def validate_document_files(index: dict[str, object], memory_root: Path) -> None:
    validate_index(index)
    tasks = index["tasks"]
    assert isinstance(tasks, dict)
    for task in tasks.values():
        assert isinstance(task, dict)
        documents = task["documents"]
        assert isinstance(documents, list)
        for document in documents:
            assert isinstance(document, dict)
            path = validate_document_path(document["path"], str(document["type"]))
            _safe_regular_file(memory_root, path)


def discover_documents(
    index: dict[str, object],
    *,
    task_key: str | None = None,
    document_type: str | None = None,
    status: str | None = None,
) -> list[dict[str, str]]:
    validate_index(index)
    if task_key is not None:
        validate_task_key(task_key)
    if document_type is not None:
        require(document_type in DOCUMENT_DIRECTORIES, "document type filter is invalid")
    if status is not None:
        require(status in DOCUMENT_STATUSES, "document status filter is invalid")
    tasks = index["tasks"]
    assert isinstance(tasks, dict)
    rows: list[dict[str, str]] = []
    for key in sorted(tasks):
        if task_key is not None and key != task_key:
            continue
        task = tasks[key]
        assert isinstance(task, dict)
        documents = task["documents"]
        assert isinstance(documents, list)
        for document in documents:
            assert isinstance(document, dict)
            if document_type is not None and document["type"] != document_type:
                continue
            if status is not None and document["status"] != status:
                continue
            rows.append(
                {
                    "task_key": key,
                    "task_status": str(task["status"]),
                    "type": str(document["type"]),
                    "path": str(document["path"]),
                    "status": str(document["status"]),
                }
            )
    return rows


def register_task(
    index: dict[str, object],
    *,
    task_key: str,
    title: str,
    summary: str,
    search_terms: list[str],
) -> None:
    validate_index(index)
    key = validate_task_key(task_key)
    tasks = index["tasks"]
    assert isinstance(tasks, dict)
    require(key not in tasks, f"task already exists: {key}")
    tasks[key] = {
        "title": title,
        "summary": summary,
        "search_terms": search_terms,
        "status": "active",
        "documents": [],
    }
    validate_index(index)


def update_task_metadata(
    index: dict[str, object],
    *,
    task_key: str,
    title: str,
    summary: str,
    search_terms: list[str],
) -> None:
    validate_index(index)
    key = validate_task_key(task_key)
    tasks = index["tasks"]
    assert isinstance(tasks, dict)
    require(key in tasks, f"unknown task: {key}")
    task = tasks[key]
    assert isinstance(task, dict)
    task["title"] = title
    task["summary"] = summary
    task["search_terms"] = search_terms
    validate_index(index)


def register_document(
    index: dict[str, object],
    *,
    task_key: str,
    document_type: str,
    path: str,
    status: str = "active",
) -> None:
    validate_index(index)
    key = validate_task_key(task_key)
    require(document_type in DOCUMENT_DIRECTORIES, "document type is invalid")
    require(status in DOCUMENT_STATUSES, "document status is invalid")
    normalized = validate_document_path(path, document_type).as_posix()
    tasks = index["tasks"]
    assert isinstance(tasks, dict)
    require(key in tasks, f"unknown task: {key}")
    task = tasks[key]
    assert isinstance(task, dict)
    require(task["status"] == "active", f"cannot add a document to final task: {key}")
    documents = task["documents"]
    assert isinstance(documents, list)
    require(
        all(not isinstance(item, dict) or item.get("path") != normalized for item in documents),
        f"document is already registered: {normalized}",
    )
    documents.append({"type": document_type, "path": normalized, "status": status})
    validate_index(index)


def finalize_document(index: dict[str, object], *, task_key: str, path: str) -> None:
    validate_index(index)
    key = validate_task_key(task_key)
    normalized = validate_document_path(path).as_posix()
    tasks = index["tasks"]
    assert isinstance(tasks, dict)
    require(key in tasks, f"unknown task: {key}")
    task = tasks[key]
    assert isinstance(task, dict)
    documents = task["documents"]
    assert isinstance(documents, list)
    matches = [item for item in documents if isinstance(item, dict) and item.get("path") == normalized]
    require(len(matches) == 1, f"unknown document for task {key!r}: {normalized}")
    matches[0]["status"] = "final"
    validate_index(index)


def finalize_task(index: dict[str, object], *, task_key: str) -> None:
    validate_index(index)
    key = validate_task_key(task_key)
    tasks = index["tasks"]
    assert isinstance(tasks, dict)
    require(key in tasks, f"unknown task: {key}")
    task = tasks[key]
    assert isinstance(task, dict)
    documents = task["documents"]
    assert isinstance(documents, list)
    require(bool(documents), f"cannot finalize task without documents: {key}")
    require(
        all(isinstance(item, dict) and item.get("status") == "final" for item in documents),
        f"cannot finalize task while documents remain active: {key}",
    )
    task["status"] = "final"
    validate_index(index)


def write_index(index_path: Path, index: dict[str, object]) -> None:
    validate_index(index)
    parent = index_path.parent
    require(parent.is_dir() and not parent.is_symlink(), f"index parent must be a non-symlink directory: {parent}")
    if index_path.exists() or index_path.is_symlink():
        info = index_path.lstat()
        require(stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode), f"index must be a regular non-symlink file: {index_path}")
    temporary = parent / ".teamwork-index.tmp"
    require(not temporary.exists() and not temporary.is_symlink(), f"temporary index path already exists: {temporary}")
    payload = json.dumps(index, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, index_path)
    except BaseException:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise


def validate_template_directory(directory: Path) -> None:
    require(directory.is_dir() and not directory.is_symlink(), f"template path must be a non-symlink directory: {directory}")
    actual = {path.name for path in directory.iterdir() if path.is_file() and not path.is_symlink()}
    expected = {"index.json", *TEMPLATE_FILES}
    require(actual == expected, f"template directory must contain index.json and exactly six semantic templates: {sorted(expected)}")
    load_index(directory / "index.json")
    for name in sorted(TEMPLATE_FILES):
        path = directory / name
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            fail(f"cannot read semantic template {path}: {exc}")
        require(bool(text.strip()), f"semantic template must not be empty: {path}")


def _memory_root_for_index(index_path: Path) -> Path | None:
    if index_path.name == "index.json" and index_path.parent.name == "teamwork" and index_path.parent.parent.name == "docs":
        return index_path.parent
    return None


def _cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("path", type=Path)
    validate.add_argument("--documents", action="store_true", help="also require every registered document file")
    discover = sub.add_parser("discover")
    discover.add_argument("index", type=Path)
    discover.add_argument("--task-key")
    discover.add_argument("--type", choices=sorted(DOCUMENT_DIRECTORIES))
    discover.add_argument("--status", choices=sorted(DOCUMENT_STATUSES))
    path_command = sub.add_parser("path")
    path_command.add_argument("--type", required=True, choices=sorted(DOCUMENT_DIRECTORIES))
    path_command.add_argument("--date", required=True)
    path_command.add_argument("--slug", required=True)
    task = sub.add_parser("register-task")
    task.add_argument("index", type=Path)
    task.add_argument("--task-key", required=True)
    task.add_argument("--title", required=True)
    task.add_argument("--summary", required=True)
    task.add_argument("--search-term", action="append", default=[])
    update = sub.add_parser("update-task")
    update.add_argument("index", type=Path)
    update.add_argument("--task-key", required=True)
    update.add_argument("--title", required=True)
    update.add_argument("--summary", required=True)
    update.add_argument("--search-term", action="append", default=[])
    document = sub.add_parser("register-document")
    document.add_argument("index", type=Path)
    document.add_argument("--task-key", required=True)
    document.add_argument("--type", required=True, choices=sorted(DOCUMENT_DIRECTORIES))
    document.add_argument("--path", required=True)
    document.add_argument("--status", default="active", choices=sorted(DOCUMENT_STATUSES))
    final_document = sub.add_parser("finalize-document")
    final_document.add_argument("index", type=Path)
    final_document.add_argument("--task-key", required=True)
    final_document.add_argument("--path", required=True)
    final_task = sub.add_parser("finalize-task")
    final_task.add_argument("index", type=Path)
    final_task.add_argument("--task-key", required=True)
    return parser


def main() -> int:
    arguments = _cli().parse_args()
    try:
        if arguments.command == "validate":
            if arguments.path.is_dir():
                validate_template_directory(arguments.path)
            else:
                index = load_index(arguments.path)
                memory_root = _memory_root_for_index(arguments.path)
                if arguments.documents or memory_root is not None:
                    require(memory_root is not None, "--documents requires docs/teamwork/index.json")
                    validate_document_files(index, memory_root)
        elif arguments.command == "discover":
            index = load_index(arguments.index)
            rows = discover_documents(
                index,
                task_key=arguments.task_key,
                document_type=arguments.type,
                status=arguments.status,
            )
            memory_root = _memory_root_for_index(arguments.index)
            if memory_root is not None:
                validate_document_files(index, memory_root)
            print(json.dumps(rows, ensure_ascii=False, indent=2))
        elif arguments.command == "path":
            print(document_path(arguments.type, arguments.date, arguments.slug))
        else:
            index = load_index(arguments.index)
            if arguments.command == "register-task":
                register_task(
                    index,
                    task_key=arguments.task_key,
                    title=arguments.title,
                    summary=arguments.summary,
                    search_terms=arguments.search_term,
                )
            elif arguments.command == "update-task":
                update_task_metadata(
                    index,
                    task_key=arguments.task_key,
                    title=arguments.title,
                    summary=arguments.summary,
                    search_terms=arguments.search_term,
                )
            elif arguments.command == "register-document":
                register_document(
                    index,
                    task_key=arguments.task_key,
                    document_type=arguments.type,
                    path=arguments.path,
                    status=arguments.status,
                )
                memory_root = _memory_root_for_index(arguments.index)
                if memory_root is not None:
                    validate_document_files(index, memory_root)
            elif arguments.command == "finalize-document":
                finalize_document(index, task_key=arguments.task_key, path=arguments.path)
            elif arguments.command == "finalize-task":
                finalize_task(index, task_key=arguments.task_key)
            write_index(arguments.index, index)
    except IndexValidationError as exc:
        print(f"Teamwork index validation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
