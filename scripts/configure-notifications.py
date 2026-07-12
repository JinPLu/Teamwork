#!/usr/bin/env python3
"""Install, remove, or inspect Teamwork notification hooks in user JSON config."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import stat
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any


EVENTS = ("Stop", "PermissionRequest")


class ConfigError(Exception):
    pass


def load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError(f"cannot read valid JSON from {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"{path} must contain a JSON object")
    hooks = data.get("hooks")
    if hooks is not None and not isinstance(hooks, dict):
        raise ConfigError(f"{path}: hooks must be a JSON object")
    return data


def command_for(notifier: Path) -> str:
    return f"python3 {shlex.quote(os.path.abspath(notifier))}"


def handler_command(value: Any) -> str | None:
    if not isinstance(value, dict) or value.get("type") != "command":
        return None
    command = value.get("command")
    return command if isinstance(command, str) else None


def is_teamwork_command(command: str | None) -> bool:
    if not command:
        return False
    try:
        target = shlex.split(command)[-1]
    except (ValueError, IndexError):
        target = command
    normalized = target.replace("\\", "/")
    return normalized.endswith("/teamwork/notify.py")


def strip_teamwork_handlers(data: dict[str, Any]) -> int:
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        return 0
    removed = 0
    for event, groups in list(hooks.items()):
        if not isinstance(groups, list):
            continue
        kept_groups = []
        for group in groups:
            if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
                kept_groups.append(group)
                continue
            handlers = group["hooks"]
            kept_handlers = []
            for handler in handlers:
                if is_teamwork_command(handler_command(handler)):
                    removed += 1
                else:
                    kept_handlers.append(handler)
            if kept_handlers:
                updated = dict(group)
                updated["hooks"] = kept_handlers
                kept_groups.append(updated)
        if kept_groups:
            hooks[event] = kept_groups
        else:
            hooks.pop(event, None)
    if not hooks:
        data.pop("hooks", None)
    return removed


def install_handlers(data: dict[str, Any], command: str) -> None:
    strip_teamwork_handlers(data)
    hooks = data.setdefault("hooks", {})
    for event in EVENTS:
        groups = hooks.setdefault(event, [])
        groups.append({"hooks": [{"type": "command", "command": command}]})


def status(data: dict[str, Any], expected_command: str) -> str:
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        return "disabled"
    exact_events: Counter[str] = Counter()
    stale = 0
    for event, groups in hooks.items():
        if not isinstance(groups, list):
            continue
        for group in groups:
            if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
                continue
            for handler in group["hooks"]:
                command = handler_command(handler)
                if command == expected_command:
                    exact_events[event] += 1
                elif is_teamwork_command(command):
                    stale += 1
    if all(exact_events[event] == 1 for event in EVENTS) and stale == 0:
        return "installed"
    if any(exact_events[event] > 1 for event in EVENTS):
        return "duplicate"
    if exact_events or stale:
        return "stale"
    return "disabled"


def write_atomic(path: Path, data: dict[str, Any]) -> None:
    try:
        destination = path.resolve(strict=False) if path.is_symlink() else path
    except (OSError, RuntimeError) as exc:
        raise ConfigError(f"cannot resolve config path {path}: {exc}") from exc
    destination.parent.mkdir(parents=True, exist_ok=True)
    mode = stat.S_IMODE(destination.stat().st_mode) if destination.exists() else 0o600
    fd, raw_tmp = tempfile.mkstemp(
        prefix=f".{destination.name}.", dir=destination.parent
    )
    tmp = Path(raw_tmp)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        os.chmod(tmp, mode)
        os.replace(tmp, destination)
    finally:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("install", "remove", "status"))
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--notifier", required=True, type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.action == "remove" and not args.config.exists():
            return 0
        data = load_config(args.config)
        command = command_for(args.notifier)
        if args.action == "status":
            print(status(data, command))
            return 0
        if args.action == "install":
            install_handlers(data, command)
        else:
            strip_teamwork_handlers(data)
        write_atomic(args.config, data)
    except ConfigError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
