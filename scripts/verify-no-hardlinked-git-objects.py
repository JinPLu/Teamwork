#!/usr/bin/env python3
"""Verify that two Git object directories do not share object inodes.

The helper is intentionally read-only. It walks both object trees with lstat
semantics, records source non-directory inodes, and rejects any snapshot
non-directory entry with the same device/inode pair.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import stat
import sys


class VerificationError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="source .git/objects directory")
    parser.add_argument("--snapshot", required=True, help="snapshot .git/objects directory")
    return parser.parse_args()


def require_directory(path: Path, label: str) -> Path:
    try:
        st = path.lstat()
    except OSError as exc:
        raise VerificationError(f"{label} object directory is unavailable: {path}") from exc
    if stat.S_ISLNK(st.st_mode):
        raise VerificationError(f"{label} object directory must not be a symlink: {path}")
    if not stat.S_ISDIR(st.st_mode):
        raise VerificationError(f"{label} object directory is not a directory: {path}")
    return path


def iter_nondirectory_inodes(root: Path) -> dict[tuple[int, int], str]:
    entries: dict[tuple[int, int], str] = {}
    stack = [root]
    while stack:
        directory = stack.pop()
        try:
            with os.scandir(directory) as scan:
                children = sorted(scan, key=lambda entry: entry.name)
                for child in children:
                    child_path = Path(child.path)
                    try:
                        st = child.stat(follow_symlinks=False)
                    except OSError as exc:
                        raise VerificationError(f"cannot inspect object entry: {child_path}") from exc
                    if stat.S_ISDIR(st.st_mode):
                        if child.is_symlink():
                            raise VerificationError(f"object directory entry is a symlinked directory: {child_path}")
                        stack.append(child_path)
                        continue
                    rel = child_path.relative_to(root).as_posix()
                    entries.setdefault((st.st_dev, st.st_ino), rel)
        except OSError as exc:
            raise VerificationError(f"cannot scan object directory: {directory}") from exc
    return entries


def verify_no_hardlinks(source: Path, snapshot: Path) -> None:
    source_dir = require_directory(source, "source")
    snapshot_dir = require_directory(snapshot, "snapshot")
    source_real = source_dir.resolve()
    snapshot_real = snapshot_dir.resolve()
    if source_real == snapshot_real:
        raise VerificationError("source and snapshot object directories are the same directory")

    source_inodes = iter_nondirectory_inodes(source_dir)
    for inode, snapshot_rel in iter_nondirectory_inodes(snapshot_dir).items():
        source_rel = source_inodes.get(inode)
        if source_rel is not None:
            raise VerificationError(
                "snapshot object shares a hardlink with source object: "
                f"source={source_rel} snapshot={snapshot_rel}"
            )


def main() -> int:
    args = parse_args()
    try:
        verify_no_hardlinks(Path(args.source), Path(args.snapshot))
    except VerificationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("OK: snapshot Git objects do not share hardlinks with source")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
