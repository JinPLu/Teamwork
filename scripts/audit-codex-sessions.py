#!/usr/bin/env python3
"""Summarize Codex session orchestration without emitting transcript content."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


COORDINATION_CALLS = {
    "followup_task",
    "interrupt_agent",
    "list_agents",
    "send_message",
    "spawn_agent",
    "wait_agent",
}
COMPACTION_TYPES = {"compacted", "context_compacted", "context_compaction"}


class AuditError(Exception):
    pass


def normalize_thread_id(value: str) -> str:
    thread_id = value.rstrip("/").rsplit("/", 1)[-1]
    if len(thread_id) != 36 or thread_id.count("-") != 4:
        raise AuditError(f"invalid thread id: {value}")
    return thread_id


def parse_profile(value: str) -> tuple[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("profile must be THREAD_ID=PROFILE")
    thread_id, profile = value.split("=", 1)
    try:
        thread_id = normalize_thread_id(thread_id)
    except AuditError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    if not profile:
        raise argparse.ArgumentTypeError("profile value must not be empty")
    return thread_id, profile


def locate_session(sessions_root: Path, thread_id: str) -> Path:
    matches = sorted(sessions_root.rglob(f"*{thread_id}.jsonl"))
    if not matches:
        raise AuditError(f"session not found for {thread_id} under {sessions_root}")
    if len(matches) > 1:
        paths = ", ".join(str(path) for path in matches)
        raise AuditError(f"multiple sessions found for {thread_id}: {paths}")
    return matches[0]


def json_size(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, str):
        return len(value.encode("utf-8", errors="replace"))
    return len(json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8"))


def parse_arguments(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def call_fingerprint(name: str, arguments: Any) -> str:
    raw = json.dumps(
        {"name": name, "arguments": arguments},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8", errors="replace")
    return hashlib.sha256(raw).hexdigest()


def audit_file(path: Path, thread_id: str) -> dict[str, Any]:
    calls: Counter[str] = Counter()
    fingerprints: Counter[str] = Counter()
    fork_modes: Counter[str] = Counter()
    models: Counter[str] = Counter()
    efforts: Counter[str] = Counter()
    child_activity: Counter[str] = Counter()
    direct_children: dict[str, dict[str, Any]] = {}
    session_meta: dict[str, Any] = {}
    final_usage: dict[str, Any] = {}
    last_context_window: int | None = None
    tool_output_bytes = 0
    compactions = 0
    line_count = 0
    own_started_at: str | None = None

    try:
        handle = path.open(encoding="utf-8")
    except OSError as exc:
        raise AuditError(f"cannot read {path}: {exc}") from exc

    with handle:
        for line_count, line in enumerate(handle, start=1):
            try:
                event = json.loads(line)
            except json.JSONDecodeError as exc:
                raise AuditError(f"{path}:{line_count}: invalid JSON: {exc}") from exc

            event_type = event.get("type")
            payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
            payload_type = payload.get("type")

            if event_type == "session_meta" and payload.get("id") == thread_id:
                session_meta = payload
                timestamp = payload.get("timestamp", event.get("timestamp"))
                if isinstance(timestamp, str):
                    own_started_at = timestamp
            event_timestamp = event.get("timestamp")
            if (
                own_started_at
                and isinstance(event_timestamp, str)
                and event_timestamp < own_started_at
            ):
                continue
            if event_type == "turn_context":
                if isinstance(payload.get("model"), str):
                    models[payload["model"]] += 1
                if isinstance(payload.get("effort"), str):
                    efforts[payload["effort"]] += 1
            if event_type in COMPACTION_TYPES or payload_type in COMPACTION_TYPES:
                compactions += 1

            if payload_type == "token_count":
                info = payload.get("info") if isinstance(payload.get("info"), dict) else {}
                usage = info.get("total_token_usage")
                if isinstance(usage, dict):
                    final_usage = usage
                window = info.get("model_context_window")
                if isinstance(window, int):
                    last_context_window = window

            if payload_type in {"function_call", "custom_tool_call"}:
                name = payload.get("name")
                if isinstance(name, str):
                    raw_arguments = payload.get("arguments", payload.get("input"))
                    arguments = parse_arguments(raw_arguments)
                    calls[name] += 1
                    fingerprints[call_fingerprint(name, arguments)] += 1
                    if name == "spawn_agent" and isinstance(arguments, dict):
                        fork_modes[str(arguments.get("fork_turns", "unspecified"))] += 1

            if payload_type in {"function_call_output", "custom_tool_call_output"}:
                tool_output_bytes += json_size(payload.get("output"))

            if payload_type == "sub_agent_activity":
                kind = str(payload.get("kind", "unknown"))
                child_activity[kind] += 1
                child_id = payload.get("agent_thread_id")
                if kind == "started" and isinstance(child_id, str):
                    direct_children[child_id] = {
                        "thread_id": child_id,
                        "agent_path": payload.get("agent_path"),
                    }

    input_tokens = int(final_usage.get("input_tokens", 0) or 0)
    cached_tokens = int(final_usage.get("cached_input_tokens", 0) or 0)
    usage = {
        "input_tokens": input_tokens,
        "cached_input_tokens": cached_tokens,
        "cached_input_ratio": round(cached_tokens / input_tokens, 4) if input_tokens else None,
        "output_tokens": int(final_usage.get("output_tokens", 0) or 0),
        "reasoning_output_tokens": int(final_usage.get("reasoning_output_tokens", 0) or 0),
        "total_tokens": int(final_usage.get("total_tokens", 0) or 0),
        "context_window": last_context_window,
    }
    duplicate_groups = sum(1 for count in fingerprints.values() if count > 1)
    repeated_calls = sum(count - 1 for count in fingerprints.values() if count > 1)
    source = session_meta.get("source")
    spawn = source.get("subagent", {}).get("thread_spawn", {}) if isinstance(source, dict) else {}

    return {
        "thread_id": thread_id,
        "path": str(path),
        "timestamp": session_meta.get("timestamp"),
        "thread_source": session_meta.get("thread_source"),
        "parent_thread_id": session_meta.get("parent_thread_id", spawn.get("parent_thread_id")),
        "agent_path": session_meta.get("agent_path", spawn.get("agent_path")),
        "agent_role": spawn.get("agent_role"),
        "model_attribution": (
            "configured-role" if spawn.get("agent_role") else
            "generic-or-parent-inherited" if session_meta.get("thread_source") == "subagent" else
            "root-session"
        ),
        "models": dict(models),
        "efforts": dict(efforts),
        "lines": line_count,
        "file_bytes": path.stat().st_size,
        "compactions": compactions,
        "tool_calls": dict(calls),
        "coordination_calls": {
            name: calls[name] for name in sorted(COORDINATION_CALLS) if calls[name]
        },
        "fork_modes": dict(fork_modes),
        "child_activity": dict(child_activity),
        "direct_children": list(direct_children.values()),
        "duplicate_call_groups": duplicate_groups,
        "repeated_calls": repeated_calls,
        "tool_output_bytes": tool_output_bytes,
        "operational_token_telemetry": usage,
    }


def aggregate(root: dict[str, Any], children: list[dict[str, Any]]) -> dict[str, Any]:
    sessions = [root, *children]
    usage_keys = [
        "input_tokens",
        "cached_input_tokens",
        "output_tokens",
        "reasoning_output_tokens",
        "total_tokens",
    ]
    totals = {
        key: sum(session["operational_token_telemetry"][key] for session in sessions)
        for key in usage_keys
    }
    totals["cached_input_ratio"] = (
        round(totals["cached_input_tokens"] / totals["input_tokens"], 4)
        if totals["input_tokens"] else None
    )
    return {
        "sessions": len(sessions),
        "compactions": sum(session["compactions"] for session in sessions),
        "tool_output_bytes": sum(session["tool_output_bytes"] for session in sessions),
        "repeated_calls": sum(session["repeated_calls"] for session in sessions),
        "operational_token_telemetry": totals,
    }


def audit_thread(
    sessions_root: Path,
    thread_id: str,
    profile: str | None,
) -> dict[str, Any]:
    root = audit_file(locate_session(sessions_root, thread_id), thread_id)
    children: list[dict[str, Any]] = []
    missing_children: list[str] = []
    for child in root["direct_children"]:
        child_id = child["thread_id"]
        try:
            children.append(audit_file(locate_session(sessions_root, child_id), child_id))
        except AuditError:
            missing_children.append(child_id)
    return {
        "thread_id": thread_id,
        "profile_at_session_time": {
            "value": profile,
            "source": "explicit-cli" if profile else "unknown",
            "confidence": "explicit" if profile else "unknown",
        },
        "root": root,
        "direct_children": children,
        "missing_child_sessions": missing_children,
        "aggregate": aggregate(root, children),
        "limitations": [
            "Operational token telemetry includes cached and replayed input; it is not billing or unique context.",
            "Root plus child totals intentionally include inherited input seen by more than one model session.",
            "Child files can replay inherited historical events; aggregate compaction, call, and output counts are operational upper bounds.",
            "Current profile markers are not applied retroactively to historical sessions.",
            "Transcript semantics, user corrections, and scope drift are not inferred by this metadata-only audit.",
        ],
    }


def render_text(reports: list[dict[str, Any]], current_profile: str | None) -> str:
    lines = [
        "WARNING: token values are cumulative operational telemetry, not billing or unique context.",
    ]
    if current_profile:
        lines.append(
            f"Current installed profile marker: {current_profile} (reported only; not applied to history)."
        )
    for report in reports:
        root = report["root"]
        aggregate_data = report["aggregate"]
        usage = aggregate_data["operational_token_telemetry"]
        lines.extend(
            [
                "",
                f"Thread {report['thread_id']}",
                f"  profile_at_session_time: {report['profile_at_session_time']['value'] or 'unknown'}",
                f"  root model/effort: {root['models']} / {root['efforts']}",
                f"  direct children: {len(report['direct_children'])} (missing files: {len(report['missing_child_sessions'])})",
                f"  root fork modes: {root['fork_modes']}",
                f"  root coordination calls: {root['coordination_calls']}",
                f"  root compactions/repeated calls: {root['compactions']}/{root['repeated_calls']}",
                f"  aggregate sessions (root + direct children): {aggregate_data['sessions']}",
                f"  input/cached/output/total: {usage['input_tokens']}/{usage['cached_input_tokens']}/{usage['output_tokens']}/{usage['total_tokens']}",
                f"  cached input ratio: {usage['cached_input_ratio']}",
                f"  tool output bytes: {aggregate_data['tool_output_bytes']}",
            ]
        )
    return "\n".join(lines)


def current_profile_marker() -> str | None:
    markers = (
        Path.home() / ".agents" / "skills" / ".teamwork-profile",
        Path.home() / ".codex" / "skills" / ".teamwork-profile",
    )
    for marker in markers:
        try:
            value = marker.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if value:
            return value
    return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit Codex session orchestration without printing transcript content."
    )
    parser.add_argument("threads", nargs="+", help="thread UUID or codex://threads/<UUID>")
    parser.add_argument(
        "--sessions-root",
        type=Path,
        default=Path.home() / ".codex" / "sessions",
        help="Codex sessions root (default: ~/.codex/sessions)",
    )
    parser.add_argument(
        "--profile",
        action="append",
        default=[],
        type=parse_profile,
        metavar="THREAD_ID=PROFILE",
        help="explicit historical profile evidence; repeat per thread",
    )
    parser.add_argument("--json", action="store_true", help="emit structured JSON")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    profiles = dict(args.profile)
    try:
        thread_ids = [normalize_thread_id(value) for value in args.threads]
        reports = [
            audit_thread(args.sessions_root.resolve(), thread_id, profiles.get(thread_id))
            for thread_id in thread_ids
        ]
    except AuditError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    current_profile = current_profile_marker()
    if args.json:
        print(
            json.dumps(
                {
                    "schema_version": 1,
                    "current_installed_profile_marker": current_profile,
                    "reports": reports,
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(render_text(reports, current_profile))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
