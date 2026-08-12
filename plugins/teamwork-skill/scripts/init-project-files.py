#!/usr/bin/env python3
"""Create or refresh Teamwork's small project-local AGENTS.md block."""

from __future__ import annotations

import argparse
import os
import re
import stat
import sys
from pathlib import Path


MANAGED_START = "<!-- TEAMWORK_PROJECT_START -->"
MANAGED_END = "<!-- TEAMWORK_PROJECT_END -->"
CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")


class InitError(RuntimeError):
    pass


def checked_project_root(raw: str) -> Path:
    if not raw or CONTROL_RE.search(raw):
        raise InitError("project root must be non-empty text without control characters")
    root = Path(os.path.abspath(os.path.expanduser(raw)))
    if not root.is_dir():
        raise InitError(f"project root is not a directory: {root}")
    return root


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise InitError(f"target must be a regular non-symlink file: {path}")
    return path.read_text(encoding="utf-8")


def project_label(root: Path, explicit: str | None) -> str:
    label = (explicit or root.name).strip()
    if not label or CONTROL_RE.search(label):
        raise InitError("project label must be non-empty text without control characters")
    return label


def managed_block(label: str) -> str:
    return (
        f"{MANAGED_START}\n"
        "## Teamwork Project Instructions\n\n"
        f"- Project label: `{label}`.\n"
        "- Teamwork adds no required project-local workflow or state. Follow this "
        "project's normal instructions and invoke a named Skill only when its trigger matches.\n"
        f"{MANAGED_END}\n"
    )


def replace_block(text: str, block: str) -> str:
    if text.count(MANAGED_START) != text.count(MANAGED_END) or text.count(MANAGED_START) > 1:
        raise InitError("Teamwork managed block markers are ambiguous")
    if MANAGED_START in text:
        before, rest = text.split(MANAGED_START, 1)
        _old, after = rest.split(MANAGED_END, 1)
        return before + block + after.lstrip("\n")
    if not text:
        return "# Repository Guidelines\n\n" + block
    return text + ("\n" if text.endswith("\n") else "\n\n") + block


def write_agents(root: Path, label: str) -> None:
    path = root / "AGENTS.md"
    before = read_text(path)
    after = replace_block(before, managed_block(label))
    if after == before:
        return
    temporary = path.with_name(f".{path.name}.teamwork-tmp")
    if temporary.exists() or temporary.is_symlink():
        raise InitError(f"temporary path already exists: {temporary}")
    try:
        temporary.write_text(after, encoding="utf-8")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def validate(root: Path) -> None:
    text = read_text(root / "AGENTS.md")
    if text.count(MANAGED_START) != 1 or text.count(MANAGED_END) != 1:
        raise InitError("AGENTS.md Teamwork managed block is missing or ambiguous")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--project-root", default=os.getcwd())
    sub = result.add_subparsers(dest="action", required=True)
    sub.add_parser("print-root")
    sub.add_parser("preflight")
    initialize = sub.add_parser("initialize")
    initialize.add_argument("--project-label")
    initialize.add_argument("--full-bootstrap", action="store_true")
    refresh = sub.add_parser("refresh-context")
    refresh.add_argument("--project-label")
    sub.add_parser("validate")
    return result


def main() -> int:
    arguments = parser().parse_args()
    try:
        root = checked_project_root(arguments.project_root)
        if arguments.action == "print-root":
            print(root)
        elif arguments.action == "preflight":
            text = read_text(root / "AGENTS.md")
            replace_block(text, managed_block(project_label(root, None)))
        elif arguments.action in {"initialize", "refresh-context"}:
            write_agents(root, project_label(root, arguments.project_label))
            validate(root)
        else:
            validate(root)
    except (InitError, OSError, UnicodeError) as exc:
        print(f"Teamwork project init failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
