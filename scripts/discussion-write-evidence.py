#!/usr/bin/env python3
"""Capture and verify a temporary project's discussion write footprint.

This helper is for an explicitly authorized workspace-write experiment.  It
never invokes Codex, reads credentials, or modifies the observed project.
Store the pre-treatment manifest outside that project, run the treatment, then
use ``verify`` to fail closed on any write outside the discussion lifecycle.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from teamwork_tooling.discussion_lifecycle import (  # noqa: E402
    DiscussionLifecycleError,
    WorkspaceManifest,
    capture_workspace_manifest,
    validate_discussion_write_footprint,
)


def _outside_project(path: Path, project_root: Path, *, label: str) -> Path:
    resolved = path.expanduser().resolve()
    canonical_project_root = project_root.resolve()
    try:
        resolved.relative_to(canonical_project_root)
    except ValueError:
        return resolved
    raise DiscussionLifecycleError(
        f"{label} must be outside the observed project to avoid contaminating its footprint: {resolved}"
    )


def _write_manifest_exclusive(path: Path, manifest: WorkspaceManifest) -> None:
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(manifest.to_dict(), handle, ensure_ascii=False, sort_keys=True, indent=2)
            handle.write("\n")
    except OSError as exc:
        raise DiscussionLifecycleError(f"cannot create manifest {path}: {exc}") from exc


def _read_manifest(path: Path) -> WorkspaceManifest:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise DiscussionLifecycleError(f"cannot read manifest {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise DiscussionLifecycleError(f"invalid JSON manifest {path}: {exc}") from exc
    return WorkspaceManifest.from_dict(value)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture and verify a temporary project's Teamwork discussion write footprint."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    snapshot = subparsers.add_parser("snapshot", help="write a pre-treatment manifest")
    snapshot.add_argument("--project", required=True, type=Path)
    snapshot.add_argument("--output", required=True, type=Path)

    verify = subparsers.add_parser("verify", help="compare a post-treatment project to a manifest")
    verify.add_argument("--project", required=True, type=Path)
    verify.add_argument("--before", required=True, type=Path)
    verify.add_argument(
        "--require-memory-anchor-updates",
        action="store_true",
        help="require index.json, current.md, and README.md to all change",
    )
    discussion_mode = verify.add_mutually_exclusive_group()
    discussion_mode.add_argument(
        "--allow-no-discussion-change",
        action="store_true",
        help="allow an anchor-only lifecycle phase (the default requires one dated artifact)",
    )
    discussion_mode.add_argument(
        "--replacement",
        action="store_true",
        help=(
            "verify a strict replacement: exactly one existing dated artifact modified, "
            "one new dated artifact created, and all three memory anchors updated"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_root = Path(os.path.abspath(os.fspath(args.project.expanduser())))
    try:
        if args.command == "snapshot":
            output = _outside_project(args.output, project_root, label="--output")
            manifest = capture_workspace_manifest(project_root)
            _write_manifest_exclusive(output, manifest)
            print(f"wrote pre-treatment manifest: {output}")
            return 0

        before_path = _outside_project(args.before, project_root, label="--before")
        before = _read_manifest(before_path)
        after = capture_workspace_manifest(project_root)
        report = validate_discussion_write_footprint(
            before,
            after,
            require_discussion_change=not args.allow_no_discussion_change,
            require_memory_anchor_updates=args.require_memory_anchor_updates,
            allow_discussion_replacement=args.replacement,
        )
        print(json.dumps(report.to_dict(), ensure_ascii=False, sort_keys=True))
        return 0
    except DiscussionLifecycleError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
