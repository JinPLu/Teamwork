"""Minimal structural helpers for capability-first grill evaluations.

The skill owns decision semantics.  This module deliberately does not model a
grill state machine, parse a user-facing packet, or choose an interaction
adapter.  It only supplies observable text and read-only event checks used by
offline fixtures and the maintainer live recorder.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
import shlex
from typing import Any, Mapping, Sequence


__all__ = [
    "event_class",
    "has_legacy_grill_ceremony",
    "question_count",
    "readonly_event_violations",
    "synthetic_event",
]


_LEGACY_CEREMONY_RE = re.compile(
    r"(?im)^\s*(?:grill (?:status|state)|decision id|close reason|"
    r"authority (?:before|delta)|effective authority|unresolved decisions|"
    r"next route)\s*:"
)


def question_count(text: str | None) -> int:
    """Count explicit question punctuation in assistant-visible text."""

    value = text or ""
    return value.count("?") + value.count("？")


def has_legacy_grill_ceremony(text: str | None) -> bool:
    """Return whether output exposes the superseded packet/state protocol."""

    return bool(_LEGACY_CEREMONY_RE.search(text or ""))


@dataclass(frozen=True)
class _SyntheticEvent:
    event_class: str


_SYNTHETIC_EVENT_CLASSES = frozenset(
    {
        "transport",
        "internal",
        "assistant-message",
        "decision-request",
        "decision-response",
        "read",
        "command",
        "test",
        "measurement",
        "temp-probe",
        "mutation",
        "plan",
        "goal",
        "dispatch",
        "external-effect",
        "destructive-effect",
        "paid-effect",
        "credential-effect",
        "unknown-runtime",
    }
)


def synthetic_event(event_class_name: str) -> Any:
    """Build a harness-owned event fixture; raw payload claims stay untrusted."""

    if event_class_name not in _SYNTHETIC_EVENT_CLASSES:
        raise ValueError(f"unsupported synthetic event class: {event_class_name}")
    return _SyntheticEvent(event_class_name)


_RAW_EVENT_CLASSES = {
    ("thread.started", "", ""): "transport",
    ("thread.resumed", "", ""): "transport",
    ("turn.completed", "", ""): "transport",
    ("item.completed", "agent_message", ""): "assistant-message",
    ("item.completed", "reasoning", ""): "internal",
    ("item.completed", "analysis", ""): "internal",
    ("teamwork.decision.request", "", ""): "decision-request",
    ("teamwork.decision.response", "", ""): "decision-response",
    ("item.completed", "file_change", "apply_patch"): "mutation",
    ("item.completed", "apply_patch", "apply_patch"): "mutation",
    ("item.completed", "function_call", "read_file"): "read",
    ("item.completed", "function_call", "read_mcp_resource"): "read",
    ("item.completed", "function_call", "list_mcp_resources"): "read",
    ("item.completed", "function_call", "list_mcp_resource_templates"): "read",
    ("item.completed", "function_call", "view_image"): "read",
    ("item.completed", "mcp_tool_call", "web__run"): "read",
    ("item.completed", "tool_call", "web_search"): "read",
}

_SHELL_COMMANDS = frozenset({"bash", "sh", "zsh"})
_COMMAND_SEPARATORS = frozenset({"&&", "||", ";", "|"})
_GIT_READ_SUBCOMMANDS = frozenset(
    {"diff", "log", "ls-files", "rev-parse", "show", "status"}
)


def _command_tokens(command: str) -> list[str] | None:
    if (
        not command.strip()
        or "\n" in command
        or "\r" in command
        or "$" in command
        or "`" in command
    ):
        return None
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    try:
        tokens = list(lexer)
    except ValueError:
        return None
    return tokens or None


def _is_bounded_sed_read(args: Sequence[str]) -> bool:
    return (
        len(args) >= 3
        and args[0] in {"-n", "--quiet", "--silent"}
        and bool(re.fullmatch(r"\d+(?:,\d+)?p", args[1]))
        and all(value and not value.startswith("-") for value in args[2:])
    )


def _is_bounded_head_or_tail(args: Sequence[str]) -> bool:
    return not any(
        value in {"-f", "-F", "--follow", "--retry"}
        or value.startswith("--follow=")
        for value in args
    )


def _is_allowlisted_read_segment(tokens: Sequence[str]) -> bool:
    if not tokens:
        return False
    executable = tokens[0].rsplit("/", 1)[-1]
    args = list(tokens[1:])
    if executable == "cd":
        return len(args) == 1 and not args[0].startswith("-")
    if executable == "pwd":
        return all(value in {"-L", "-P", "--logical", "--physical"} for value in args)
    if executable == "ls":
        return True
    if executable == "rg":
        return not any(value == "--pre" or value.startswith("--pre=") for value in args)
    if executable == "sed":
        return _is_bounded_sed_read(args)
    if executable in {"head", "tail"}:
        return _is_bounded_head_or_tail(args)
    if executable != "git":
        return False

    while args and args[0] == "--no-pager":
        args = args[1:]
    if len(args) >= 2 and args[0] == "-C" and not args[1].startswith("-"):
        args = args[2:]
    if not args or args[0] not in _GIT_READ_SUBCOMMANDS:
        return False
    return not any(
        value in {"--ext-diff", "--textconv", "--output"}
        or value.startswith("--output=")
        for value in args[1:]
    )


def _is_allowlisted_nonmutating_command(command: str) -> bool:
    tokens = _command_tokens(command)
    if tokens is None:
        return False
    if (
        len(tokens) == 3
        and tokens[0].rsplit("/", 1)[-1] in _SHELL_COMMANDS
        and tokens[1] in {"-c", "-lc"}
    ):
        return _is_allowlisted_nonmutating_command(tokens[2])

    segments: list[list[str]] = [[]]
    for token in tokens:
        if token in _COMMAND_SEPARATORS:
            if not segments[-1]:
                return False
            segments.append([])
        elif token and all(character in "();<>|&" for character in token):
            return False
        else:
            segments[-1].append(token)
    return bool(segments[-1]) and all(
        _is_allowlisted_read_segment(segment) for segment in segments
    )


def event_class(event: Any) -> str:
    """Classify observed read-only events; unknown payloads fail closed."""

    if isinstance(event, _SyntheticEvent):
        return event.event_class
    if not isinstance(event, Mapping):
        return "unknown-runtime"
    item = event.get("item") if isinstance(event.get("item"), Mapping) else {}
    event_type = event.get("type")
    item_type = item.get("type", "")
    tool_name = item.get("name", event.get("name", ""))
    if not all(isinstance(value, str) for value in (event_type, item_type, tool_name)):
        return "unknown-runtime"
    if item_type == "command_execution":
        command = item.get("command")
        if event_type != "item.completed" or not isinstance(command, str):
            return "unknown-runtime"
        return "command" if _is_allowlisted_nonmutating_command(command) else "unknown-runtime"
    return _RAW_EVENT_CLASSES.get((event_type, item_type, tool_name), "unknown-runtime")


def readonly_event_violations(events: Sequence[Any]) -> list[str]:
    """Reject any event not proven safe for a read-only evaluation trajectory."""

    allowed = {
        "transport",
        "internal",
        "assistant-message",
        "decision-request",
        "decision-response",
        "read",
        "command",
        "test",
        "measurement",
        "temp-probe",
    }
    violations = []
    for index, event in enumerate(events, start=1):
        classified = event_class(event)
        if classified not in allowed:
            violations.append(f"event {index} class {classified} is not proven read-only")
    return violations
