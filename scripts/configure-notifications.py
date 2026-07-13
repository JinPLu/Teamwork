#!/usr/bin/env python3
"""Install, remove, or inspect Teamwork notification hooks in user JSON config."""

from __future__ import annotations

import argparse
import json
import os
import queue
import shlex
import stat
import subprocess
import sys
import tempfile
import threading
import time
from collections import Counter
from pathlib import Path
from typing import Any


EVENTS = ("Stop", "PermissionRequest")
RUNTIME_EVENTS = {"stop", "permissionrequest"}


class ConfigError(Exception):
    pass


class RuntimeProbeError(Exception):
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


def codex_runtime_status(
    result: Any, expected_command: str, cwd: Path
) -> str:
    if not isinstance(result, dict) or not isinstance(result.get("data"), list):
        return "runtime-unverified"
    row = next(
        (
            item
            for item in result["data"]
            if isinstance(item, dict) and item.get("cwd") == str(cwd)
        ),
        None,
    )
    if not isinstance(row, dict) or not isinstance(row.get("hooks"), list):
        return "runtime-unverified"

    matched: dict[str, list[dict[str, Any]]] = {}
    for hook in row["hooks"]:
        if not isinstance(hook, dict) or hook.get("command") != expected_command:
            continue
        event = "".join(
            character
            for character in str(hook.get("eventName", "")).lower()
            if character.isalnum()
        )
        if event in RUNTIME_EVENTS:
            matched.setdefault(event, []).append(hook)

    if set(matched) != RUNTIME_EVENTS:
        return "runtime-unverified"
    if any(len(hooks) != 1 for hooks in matched.values()):
        return "duplicate"
    matched_hooks = [hook for hooks in matched.values() for hook in hooks]
    if any(
        hook.get("trustStatus") == "untrusted" and not hook.get("isManaged")
        for hook in matched_hooks
    ):
        return "review-required"
    if all(
        hook.get("isManaged") is True or hook.get("trustStatus") == "trusted"
        for hook in matched_hooks
    ):
        return "installed"
    return "runtime-unverified"


def query_codex_hooks(cwd: Path, timeout: float = 5.0) -> dict[str, Any]:
    try:
        process = subprocess.Popen(
            ["codex", "app-server", "--stdio"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
            cwd=cwd,
        )
    except OSError as exc:
        raise RuntimeProbeError(f"cannot start Codex app server: {exc}") from exc
    assert process.stdin is not None
    assert process.stdout is not None
    messages: queue.Queue[dict[str, Any]] = queue.Queue()

    def read_stdout() -> None:
        for line in process.stdout:
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                messages.put(value)

    threading.Thread(target=read_stdout, daemon=True).start()

    def send(value: dict[str, Any]) -> None:
        process.stdin.write(json.dumps(value, separators=(",", ":")) + "\n")
        process.stdin.flush()

    def response(request_id: int) -> dict[str, Any]:
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise RuntimeProbeError("Codex app server hook query timed out")
            try:
                message = messages.get(timeout=remaining)
            except queue.Empty as exc:
                raise RuntimeProbeError("Codex app server hook query timed out") from exc
            if message.get("id") != request_id:
                continue
            if "error" in message:
                raise RuntimeProbeError(f"Codex app server returned: {message['error']}")
            result = message.get("result")
            if not isinstance(result, dict):
                raise RuntimeProbeError("Codex app server returned an invalid result")
            return result

    try:
        send(
            {
                "id": 1,
                "method": "initialize",
                "params": {
                    "clientInfo": {
                        "name": "teamwork-notification-status",
                        "version": "1",
                    },
                    "capabilities": {},
                },
            }
        )
        response(1)
        send({"method": "initialized", "params": {}})
        send({"id": 2, "method": "hooks/list", "params": {"cwds": [str(cwd)]}})
        return response(2)
    finally:
        process.terminate()
        try:
            process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=1)


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
    parser.add_argument(
        "--codex-runtime",
        action="store_true",
        help="for status, verify that Codex has trusted the installed hooks",
    )
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.action == "remove" and not args.config.exists():
            return 0
        data = load_config(args.config)
        command = command_for(args.notifier)
        if args.action == "status":
            result = status(data, command)
            if args.codex_runtime and result == "installed":
                try:
                    runtime = query_codex_hooks(args.cwd.resolve())
                except RuntimeProbeError:
                    result = "runtime-unverified"
                else:
                    result = codex_runtime_status(
                        runtime, command, args.cwd.resolve()
                    )
            print(result)
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
