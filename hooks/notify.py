#!/usr/bin/env python3
"""Fail-open, metadata-only desktop sound hook for Teamwork."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


NEUTRAL_RESPONSE: dict[str, object] = {}
READY_EVENTS = {"stop", "agent-turn-complete", "task-complete", "task_complete"}
ATTENTION_EVENTS = {
    "permissionrequest",
    "permission-request",
    "permission_requested",
    "approval-requested",
    "needs-input",
    "needs_input",
}
ATTENTION_NOTIFICATIONS = {"permission_prompt", "elicitation_dialog", "idle_prompt"}
METADATA_KEYS = (
    "hook_event_name",
    "event_name",
    "event",
    "type",
    "notification_type",
    "session_id",
    "thread_id",
    "thread-id",
    "turn_id",
    "turn-id",
    "request_id",
    "tool_use_id",
)
IDENTITY_KEYS = (
    "session_id",
    "thread_id",
    "thread-id",
    "turn_id",
    "turn-id",
    "request_id",
    "tool_use_id",
)


def metadata(payload: Any) -> dict[str, str]:
    """Copy only routing and identity metadata; never inspect message content."""
    if not isinstance(payload, dict):
        return {}
    return {
        key: str(value)
        for key in METADATA_KEYS
        if isinstance((value := payload.get(key)), (str, int))
    }


def classify(meta: dict[str, str]) -> str | None:
    event = next(
        (str(meta[key]).strip().lower() for key in ("hook_event_name", "event_name", "event", "type") if key in meta),
        "",
    )
    if event == "subagentstop":
        return None
    if event in READY_EVENTS:
        return "ready"
    if event in ATTENTION_EVENTS:
        return "attention"
    if event == "notification" and str(meta.get("notification_type", "")).lower() in ATTENTION_NOTIFICATIONS:
        return "attention"
    return None


def claim_once(event: str, meta: dict[str, str], ttl: float = 2.0) -> bool:
    identity = {key: meta[key] for key in IDENTITY_KEYS if key in meta}
    if not identity:
        identity = {key: meta[key] for key in METADATA_KEYS if key in meta}
    digest = hashlib.sha256(
        json.dumps([event, identity], sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()[:24]
    marker = Path(tempfile.gettempdir()) / f"teamwork-notify-{digest}"
    try:
        marker.touch(exist_ok=False)
        return True
    except FileExistsError:
        try:
            if time.time() - marker.stat().st_mtime <= ttl:
                return False
            marker.unlink()
            marker.touch(exist_ok=False)
            return True
        except (FileNotFoundError, FileExistsError, OSError):
            return False
    except OSError:
        return True


def playback_command(event: str) -> list[str] | None:
    system = platform.system()
    configured = os.environ.get(f"TEAMWORK_{event.upper()}_SOUND")
    if system == "Darwin":
        sound = configured or (
            "/System/Library/Sounds/Glass.aiff" if event == "ready" else "/System/Library/Sounds/Ping.aiff"
        )
        player = shutil.which("afplay")
        return [player, sound] if player and Path(sound).is_file() else None
    if system == "Linux":
        if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
            return None
        sound = configured or (
            "/usr/share/sounds/freedesktop/stereo/complete.oga"
            if event == "ready"
            else "/usr/share/sounds/freedesktop/stereo/dialog-warning.oga"
        )
        player = shutil.which("paplay")
        return [player, sound] if player and Path(sound).is_file() else None
    if system == "Windows":
        player = shutil.which("powershell") or shutil.which("pwsh")
        if not player:
            return None
        if configured:
            if not Path(configured).is_file():
                return None
            escaped = configured.replace("'", "''")
            script = f"(New-Object Media.SoundPlayer '{escaped}').PlaySync()"
        else:
            name = "Asterisk" if event == "ready" else "Exclamation"
            script = f"[System.Media.SystemSounds]::{name}.Play()"
        return [player, "-NoProfile", "-NonInteractive", "-Command", script]
    return None


def play(event: str) -> None:
    if os.environ.get("TEAMWORK_NOTIFY_DRY_RUN") == "1" or os.environ.get("TEAMWORK_NOTIFY_HEADLESS") == "1":
        return
    command = playback_command(event)
    if not command:
        return
    try:
        subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError:
        pass


def read_payload(argv: list[str]) -> Any:
    raw = argv[1] if len(argv) > 1 else sys.stdin.read()
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None


def main(argv: list[str] | None = None) -> int:
    try:
        meta = metadata(read_payload(argv or sys.argv))
        event = classify(meta)
        if event and claim_once(event, meta):
            play(event)
    except Exception:
        pass
    print(json.dumps(NEUTRAL_RESPONSE, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
