#!/usr/bin/env python3
"""Validate a Teamwork schema-v4 index or the canonical template directory."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from teamwork_index_v4 import (
    IndexValidationError,
    load_index,
    validate_document_files,
    validate_template_directory,
)


def memory_root_for_index(index_path: Path) -> Path | None:
    if index_path.name == "index.json" and index_path.parent.name == "teamwork" and index_path.parent.parent.name == "docs":
        return index_path.parent
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument(
        "--documents",
        action="store_true",
        help="require each registered document to exist as a safe regular file",
    )
    arguments = parser.parse_args()
    try:
        if arguments.path.is_dir():
            validate_template_directory(arguments.path)
        else:
            index = load_index(arguments.path)
            memory_root = memory_root_for_index(arguments.path)
            if memory_root is not None or arguments.documents:
                if memory_root is None:
                    raise IndexValidationError("--documents requires docs/teamwork/index.json")
                validate_document_files(index, memory_root)
    except IndexValidationError as exc:
        print(f"Teamwork index validation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
