#!/usr/bin/env python3
"""Atomically record and inspect a Teamwork Codex plugin activation."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
PLUGIN_NAME = "teamwork-skill"
MARKETPLACE_NAME = "teamwork"
VALID_PROFILES = {
    "performance-first",
    "cost-first",
    "gpt56-role",
    "gpt56-high",
    "gpt56-xhigh",
    "gpt55-high",
    "gpt55-xhigh",
}
VALID_NOTIFICATIONS = {"enabled", "disabled"}


class ActivationError(RuntimeError):
    """An activation marker is missing or unsafe to replace."""


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("action", choices=("write", "status"))
    result.add_argument("--path", type=Path, required=True)
    result.add_argument("--version")
    result.add_argument("--profile")
    result.add_argument("--notifications", choices=sorted(VALID_NOTIFICATIONS))
    result.add_argument("--json", action="store_true")
    return result


def read_marker(path: Path) -> dict[str, Any] | None:
    if path.is_symlink():
        raise ActivationError(f"Teamwork activation marker must not be a symlink: {path}")
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ActivationError(f"cannot read a valid Teamwork activation marker at {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ActivationError(f"Teamwork activation marker at {path} must be a JSON object")
    validate_marker(value, path)
    return value


def validate_marker(value: dict[str, Any], path: Path) -> None:
    if value.get("schema_version") != SCHEMA_VERSION:
        raise ActivationError(f"unsupported Teamwork activation marker schema at {path}")
    if value.get("plugin") != PLUGIN_NAME or value.get("marketplace") != MARKETPLACE_NAME:
        raise ActivationError(f"activation marker at {path} is not owned by Teamwork Codex plugin")
    if not isinstance(value.get("version"), str) or not value["version"].strip():
        raise ActivationError(f"activation marker at {path} has no plugin version")
    if value.get("profile") not in VALID_PROFILES:
        raise ActivationError(f"activation marker at {path} has an invalid profile")
    if value.get("notifications") not in VALID_NOTIFICATIONS:
        raise ActivationError(f"activation marker at {path} has an invalid notification setting")


def status(path: Path, version: str | None) -> dict[str, Any]:
    try:
        marker = read_marker(path)
    except ActivationError as exc:
        return {"status": "invalid", "detail": str(exc)}
    if marker is None:
        return {"status": "missing"}
    if version is not None and marker["version"] != version:
        return {"status": "stale", "marker": marker}
    return {"status": "current", "marker": marker}


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, raw_tmp = tempfile.mkstemp(prefix=f".{path.name}.teamwork-", dir=path.parent)
    temporary = Path(raw_tmp)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    args = parser().parse_args()
    path = args.path.expanduser()
    if args.action == "status":
        result = status(path, args.version)
        if args.json:
            print(json.dumps(result, sort_keys=True))
        else:
            print(result["status"])
        return 0 if result["status"] != "invalid" else 1

    if not args.version or not args.profile or not args.notifications:
        raise SystemExit("write requires --version, --profile, and --notifications")
    if args.profile not in VALID_PROFILES:
        raise SystemExit(f"unsupported Teamwork profile: {args.profile}")
    try:
        existing = read_marker(path)
    except ActivationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    value = {
        "schema_version": SCHEMA_VERSION,
        "plugin": PLUGIN_NAME,
        "marketplace": MARKETPLACE_NAME,
        "version": args.version,
        "profile": args.profile,
        "notifications": args.notifications,
    }
    # A valid earlier Teamwork marker is intentionally upgraded in place; any
    # other file is refused above instead of being silently overwritten.
    _ = existing
    try:
        atomic_write(path, value)
    except OSError as exc:
        print(f"ERROR: cannot write Teamwork activation marker at {path}: {exc}", file=sys.stderr)
        return 1
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
