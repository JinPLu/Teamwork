#!/usr/bin/env python3
"""Create or validate minimal schema-v4 Teamwork project context.

Init creates an empty typed-document index and the managed project instruction
block.  It never creates typed directories or documents and never migrates an
older Teamwork format.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
from pathlib import Path
from typing import NoReturn

from teamwork_index_v4 import IndexValidationError, load_index, validate_index


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
INDEX_TEMPLATE = REPOSITORY_ROOT / "templates/teamwork-memory/index.json"
MANAGED_START = "<!-- TEAMWORK_PROJECT_START -->"
MANAGED_END = "<!-- TEAMWORK_PROJECT_END -->"
IGNORE_START = "# TEAMWORK_LOCAL_START"
IGNORE_END = "# TEAMWORK_LOCAL_END"
CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
RETIRED_MARKERS = (
    ".teamwork-init-transaction.json",
    "docs/teamwork/.teamwork-init-transaction.json",
    "docs/teamwork/.discussion-transaction.json",
    "docs/teamwork/discussion/.discussion-transaction.json",
)


class InitError(RuntimeError):
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


def project_label(root: Path, explicit: str | None) -> str:
    label = (explicit if explicit is not None else root.name).strip()
    if not label or CONTROL_RE.search(label):
        fail("project label must be non-empty text without control characters")
    return label


def _regular_text(path: Path, label: str) -> str:
    try:
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            fail(f"{label} must be a regular non-symlink file")
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        fail(f"cannot read {label}: {exc}")


def _checked_directory(path: Path, label: str) -> None:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return
    except OSError as exc:
        fail(f"cannot inspect {label}: {exc}")
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        fail(f"{label} must be a non-symlink directory")


def _replace_managed_block(
    text: str,
    *,
    start: str,
    end: str,
    block: str,
    prefix: str = "",
) -> str:
    starts = text.count(start)
    ends = text.count(end)
    if starts != ends or starts > 1:
        fail("managed block markers are ambiguous")
    if starts == 1:
        before, remainder = text.split(start, 1)
        _old, after = remainder.split(end, 1)
        return before + block + after.lstrip("\n")
    if not text:
        return prefix + block
    separator = "\n" if text.endswith("\n") else "\n\n"
    return text + separator + block


def _managed_agents_block(root: Path, label: str) -> str:
    lines = [
        f"- Project label (local routing only): `{label}`.",
        "- Read `docs/teamwork/index.json` first; schema v4 is the only normal Teamwork document route.",
        "- Writer creates material reusable output under `docs/teamwork/{discussions,research,debug,plans,reviews,reports}/<YYYY-MM-DD>-<semantic-slug>.md` and registers it in the task index.",
        "- One human-readable task key may reference several typed documents. Writer updates only material semantic changes and finalizes each document at its owning stage boundary.",
        "- Same-scope editorial or link corrections may update a final document in place; materially new scope uses a new same-type path and preserves the final document.",
        "- Older schemas, `cases/`, manifests, and `live.md` are migration-only inputs for Update; normal readers fail closed and Init never migrates them.",
    ]
    return (
        f"{MANAGED_START}\n"
        "## Teamwork Project Instructions\n\n"
        + "\n".join(lines)
        + f"\n{MANAGED_END}\n"
    )


GITIGNORE_BLOCK = f"""{IGNORE_START}
# Teamwork local runtime state
docs/teamwork/**
.teamwork/runtime/**
{IGNORE_END}
"""


def _render_index(label: str) -> str:
    try:
        template = json.loads(_regular_text(INDEX_TEMPLATE, "Teamwork index template"))
    except json.JSONDecodeError as exc:
        fail(f"Teamwork index template is invalid JSON: {exc}")
    template["project"]["name"] = label
    validate_index(template)
    return json.dumps(template, ensure_ascii=False, indent=2) + "\n"


def _inspect_memory(root: Path) -> dict[str, object] | None:
    docs = root / "docs"
    memory = docs / "teamwork"
    _checked_directory(docs, "docs")
    _checked_directory(memory, "docs/teamwork")
    for relative in RETIRED_MARKERS:
        marker = root / relative
        if marker.exists() or marker.is_symlink():
            fail(f"retired Teamwork transaction state requires Update cleanup: {relative}")
    if not memory.exists():
        return None
    index_path = memory / "index.json"
    if not index_path.exists() and not index_path.is_symlink():
        try:
            has_content = next(memory.iterdir(), None) is not None
        except OSError as exc:
            fail(f"cannot inspect docs/teamwork: {exc}")
        if has_content:
            fail("Teamwork memory without schema-v4 index requires explicit Update migration")
        return None
    try:
        index = load_index(index_path)
    except IndexValidationError as exc:
        fail(str(exc))
    legacy_paths = (memory / "cases", memory / "current.md", memory / "README.md", memory / "discussion")
    if any(path.exists() or path.is_symlink() for path in legacy_paths):
        fail("legacy live/case Teamwork routes require explicit Update migration")
    return index


def preflight(root: Path) -> None:
    if _inspect_memory(root) is not None:
        fail("Teamwork context is already initialized; Init is fresh-only, use Update to refresh it")
    for path, label in ((root / "AGENTS.md", "AGENTS.md"), (root / ".gitignore", ".gitignore")):
        if path.exists() or path.is_symlink():
            _regular_text(path, label)


def _atomic_write(path: Path, text: str) -> None:
    if path.exists() or path.is_symlink():
        existing = _regular_text(path, str(path))
        if existing == text:
            return
        mode = stat.S_IMODE(path.lstat().st_mode)
    else:
        mode = 0o644
    temporary = path.parent / f".{path.name}.teamwork-init-tmp"
    if temporary.exists() or temporary.is_symlink():
        fail(f"temporary Init path already exists: {temporary}")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise


def _write_project_context(
    root: Path,
    arguments: argparse.Namespace,
    *,
    require_existing_index: bool,
) -> None:
    if (
        getattr(arguments, "candidate_memory", None)
        or getattr(arguments, "candidate_docs_graph", None)
        or getattr(arguments, "promote_candidates", False)
    ):
        fail("candidate promotion is retired; Init never migrates or promotes Teamwork documents")
    existing_index = _inspect_memory(root)
    if require_existing_index and existing_index is None:
        fail("Update context refresh requires an existing schema-v4 Teamwork index")
    if not require_existing_index and existing_index is not None:
        fail("Teamwork context is already initialized; Init is fresh-only, use Update to refresh it")
    label = project_label(root, arguments.project_label)
    agents_path = root / "AGENTS.md"
    ignore_path = root / ".gitignore"
    agents_before = "" if not agents_path.exists() else _regular_text(agents_path, "AGENTS.md")
    ignore_before = "" if not ignore_path.exists() else _regular_text(ignore_path, ".gitignore")
    agents_after = _replace_managed_block(
        agents_before,
        start=MANAGED_START,
        end=MANAGED_END,
        block=_managed_agents_block(root, label),
        prefix="# Repository Guidelines\n\n",
    )
    ignore_after = _replace_managed_block(
        ignore_before,
        start=IGNORE_START,
        end=IGNORE_END,
        block=GITIGNORE_BLOCK,
    )
    index_after = None if require_existing_index else _render_index(label)

    docs = root / "docs"
    memory = docs / "teamwork"
    created: list[Path] = []
    before: dict[Path, str | None] = {
        agents_path: agents_before if agents_path.exists() else None,
        ignore_path: ignore_before if ignore_path.exists() else None,
    }
    index_path = memory / "index.json"
    if index_after is not None:
        before[index_path] = None
    try:
        if not docs.exists():
            docs.mkdir()
            created.append(docs)
        if not memory.exists():
            memory.mkdir()
            created.append(memory)
        if index_after is not None:
            _atomic_write(index_path, index_after)
        _atomic_write(agents_path, agents_after)
        _atomic_write(ignore_path, ignore_after)
    except BaseException:
        for path, old_text in reversed(tuple(before.items())):
            if old_text is None:
                try:
                    path.unlink()
                except FileNotFoundError:
                    pass
            elif path.parent.exists():
                _atomic_write(path, old_text)
        for directory in reversed(created):
            try:
                directory.rmdir()
            except OSError:
                pass
        raise
    command_validate(root, arguments)
    if getattr(arguments, "full_bootstrap", False):
        print(
            json.dumps(
                {
                    "schema_version": 4,
                    "mode": "full-bootstrap",
                    "project_memory": "empty typed-document index",
                    "migration": "older project memory is handled by Update, not Init",
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )


def command_initialize(root: Path, arguments: argparse.Namespace) -> None:
    _write_project_context(root, arguments, require_existing_index=False)


def command_refresh_context(root: Path, arguments: argparse.Namespace) -> None:
    _write_project_context(root, arguments, require_existing_index=True)


def command_validate(root: Path, _arguments: argparse.Namespace) -> None:
    index = _inspect_memory(root)
    if index is None:
        fail("docs/teamwork/index.json is not initialized")
    validate_index(index)
    agents_path = root / "AGENTS.md"
    if not agents_path.exists():
        fail("AGENTS.md does not contain Teamwork project context")
    agents = _regular_text(agents_path, "AGENTS.md")
    if agents.count(MANAGED_START) != 1 or agents.count(MANAGED_END) != 1:
        fail("AGENTS.md Teamwork managed block is missing or ambiguous")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--project-root", default=os.environ.get("TEAMWORK_PROJECT_ROOT", os.getcwd()))
    sub = result.add_subparsers(dest="action", required=True)
    sub.add_parser("preflight")
    sub.add_parser("print-root")
    initialize = sub.add_parser("initialize")
    initialize.add_argument("--today", help="accepted for stable caller compatibility; document dates belong to Writer")
    initialize.add_argument("--project-label")
    initialize.add_argument("--full-bootstrap", action="store_true")
    initialize.add_argument("--candidate-memory")
    initialize.add_argument("--candidate-docs-graph")
    initialize.add_argument("--promote-candidates", action="store_true")
    initialize.add_argument("--root-authorized-promotion", action="store_true")
    refresh = sub.add_parser("refresh-context")
    refresh.add_argument("--project-label")
    sub.add_parser("validate")
    return result


def main() -> int:
    arguments = parser().parse_args()
    try:
        root = checked_project_root(arguments.project_root)
        if arguments.action == "preflight":
            preflight(root)
        elif arguments.action == "print-root":
            print(root)
        elif arguments.action == "initialize":
            command_initialize(root, arguments)
        elif arguments.action == "refresh-context":
            command_refresh_context(root, arguments)
        elif arguments.action == "validate":
            command_validate(root, arguments)
    except (InitError, IndexValidationError) as exc:
        print(f"Teamwork project init refused: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
