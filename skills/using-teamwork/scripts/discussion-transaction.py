#!/usr/bin/env python3
"""Apply one fail-closed Teamwork discussion lifecycle transaction."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import inspect
import json
import os
import re
import secrets
import stat
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path, PurePosixPath
from typing import NoReturn


DISCUSSION_RE = re.compile(
    r"^docs/teamwork/discussion/(\d{4}-\d{2}-\d{2})-([a-z0-9]+(?:-[a-z0-9]+)*)\.md$"
)
REQUIRED_HEADERS = (
    "Artifact Type",
    "Status",
    "Authority",
    "Last Updated",
    "Search Keys",
    "Abstract",
    "Linked Artifacts",
    "Superseded By",
)
REQUIRED_SECTIONS = ("Goal", "Settled", "Still open", "Key evidence", "Continue here")
ENTRY_REQUIRED = (
    "topic",
    "kind",
    "title",
    "status",
    "currentness",
    "authority",
    "path",
    "updated",
    "summary",
)
SUMMARY_FIELDS = (
    "last_updated",
    "current_focus",
    "progress_summary",
    "latest_result",
    "next_action",
)
SUMMARY_MARKERS = {
    "last_updated": "Last Updated:",
    "current_focus": "- Current focus:",
    "progress_summary": "- Progress summary:",
    "latest_result": "- Latest result:",
    "next_action": "- Next action:",
}
MAX_REQUEST_BYTES = 128 * 1024
MAX_SCALAR_CHARS = 4000
MAX_LIST_ITEMS = 50
MAX_ITEM_CHARS = 1000
MARKER_NAME = ".discussion-transaction.json"
INIT_MARKER_NAME = ".teamwork-init-transaction.json"
CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
RECORD_COMMON_FIELDS = {
    "title", "search_keys", "abstract", "linked_artifacts", "summary",
    "goal", "settled", "still_open", "key_evidence", "continue_here",
}
KINDS = {"result", "progress", "design", "decision", "discussion", "plan", "report", "research", "runbook"}
STATUSES = {"active", "historical", "superseded", "blocked", "candidate", "accepted"}
CURRENTNESS = {"current", "stale", "historical", "candidate"}
AUTHORITIES = {"canonical", "active-summary", "supporting", "candidate", "historical", "superseded"}
ACTIVE_POINTER_KEYS = ("current", "design", "plan", "progress", "goal", "report", "discussion")
GUARD_ENV = {
    "root": "TEAMWORK_DISCUSSION_GUARD_ROOT_FD",
    "docs": "TEAMWORK_DISCUSSION_GUARD_DOCS_FD",
    "teamwork": "TEAMWORK_DISCUSSION_GUARD_TEAMWORK_FD",
    "lock": "TEAMWORK_DISCUSSION_GUARD_LOCK_FD",
}
GUARD_TOKEN_ENV = "TEAMWORK_DISCUSSION_GUARD_TOKEN"


class TransactionError(Exception):
    def __init__(self, message: str, category: str = "PREWRITE_SAFE") -> None:
        super().__init__(message)
        self.category = category


class SimulatedInterruption(Exception):
    pass


def fail(message: str, *, category: str | None = None) -> NoReturn:
    if category is None:
        category = "INDETERMINATE" if message.startswith("INDETERMINATE:") else "PREWRITE_SAFE"
    raise TransactionError(message, category)


def read_inline_spec(argument: str) -> object:
    raw = argument.encode("utf-8")
    if len(raw) > MAX_REQUEST_BYTES:
        fail("request exceeds the maximum payload size")
    try:
        return json.loads(argument)
    except json.JSONDecodeError as exc:
        fail(f"cannot parse inline JSON spec: {exc}")


def read_spec(argument: str) -> object:
    require_fd_platform()
    if argument == "-":
        fail("stdin is not supported; use --request-json or a request file")
    path = Path(os.path.abspath(argument))
    try:
        before = path.lstat()
    except OSError as exc:
        fail(f"cannot inspect spec file: {exc}")
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        fail("spec file must be a single-link non-symlink regular file")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        fail(f"cannot open spec file without following links: {exc}")
    try:
        opened = os.fstat(fd)
        if (
            opened.st_dev != before.st_dev
            or opened.st_ino != before.st_ino
            or opened.st_nlink != 1
            or not stat.S_ISREG(opened.st_mode)
        ):
            fail("spec file changed identity while being opened")
        chunks: list[bytes] = []
        total = 0
        while chunk := os.read(fd, min(65536, MAX_REQUEST_BYTES + 1 - total)):
            chunks.append(chunk)
            total += len(chunk)
            if total > MAX_REQUEST_BYTES:
                fail("request exceeds the maximum payload size")
        return json.loads(b"".join(chunks).decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        fail(f"cannot parse JSON spec file: {exc}")
    finally:
        os.close(fd)


def schema_template(lifecycle: str) -> dict[str, object]:
    operation = "close" if lifecycle in {"close", "supersede"} else lifecycle
    record: dict[str, object] = {
        "title": "<title>",
        "search_keys": ["<search-key>"],
        "abstract": "<abstract>",
        "linked_artifacts": [],
        "summary": "<index-summary>",
        "goal": "<goal>",
        "settled": ["<settled-fact>"],
        "still_open": [] if lifecycle in {"close", "supersede"} else ["<open-question>"],
        "key_evidence": ["<key-evidence>"],
        "continue_here": "<next-step>",
    }
    if lifecycle in {"create", "replace"}:
        record["topic"] = "<topic-kebab-case>"
        record["slug"] = "<slug-kebab-case>"
    template: dict[str, object] = {
        "schema_version": 1,
        "operation": operation,
        "expected_revision": "<expected-revision-from-inspect>",
        "record": record,
        "current_summary": {
            "last_updated": "<YYYY-MM-DD>",
            "current_focus": "<current-focus>",
            "progress_summary": "<progress-summary>",
            "latest_result": "<latest-result>",
            "next_action": "<next-action>",
        },
    }
    if lifecycle == "close":
        template["close_status"] = "accepted"
    elif lifecycle == "supersede":
        template["close_status"] = "superseded"
        template["superseded_by"] = "<successor-or-reason>"
    return template


def require_object(value: object, *, label: str) -> dict[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        fail(f"{label} must be a JSON object")
    return value


def require_single_line(value: object, *, label: str) -> str:
    if (
        not isinstance(value, str) or not value.strip() or "\n" in value or "\r" in value
        or CONTROL_RE.search(value) is not None or len(value) > MAX_SCALAR_CHARS
    ):
        fail(f"{label} must be a non-empty single-line string")
    normalized = value.strip()
    if normalized.startswith("<") and normalized.endswith(">"):
        fail(f"{label} must not be a placeholder")
    return normalized


def require_string_list(
    value: object, *, label: str, allow_empty: bool = False
) -> list[str]:
    if not isinstance(value, list) or len(value) > MAX_LIST_ITEMS or (not value and not allow_empty):
        fail(f"{label} must be a bounded string array")
    result: list[str] = []
    for position, item in enumerate(value):
        text = require_single_line(item, label=f"{label}[{position}]")
        if len(text) > MAX_ITEM_CHARS:
            fail(f"{label}[{position}] is too long")
        result.append(text)
    return result


def validate_slug(value: object, *, label: str) -> str:
    slug = require_single_line(value, label=label)
    if re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug) is None or len(slug) > 80:
        fail(f"{label} must be bounded kebab-case")
    return slug


def parse_decision_map(value: object) -> dict[str, object]:
    decision = require_object(value, label="record.decision_map")
    if set(decision) != {"direction", "nodes", "edges"}:
        fail("record.decision_map fields must be direction, nodes, and edges")
    direction = decision["direction"]
    if direction not in {"TB", "TD", "BT", "RL", "LR"}:
        fail("record.decision_map.direction is invalid")
    nodes_raw = decision["nodes"]
    edges_raw = decision["edges"]
    if not isinstance(nodes_raw, list) or not 1 <= len(nodes_raw) <= 30:
        fail("record.decision_map.nodes must contain 1-30 nodes")
    if not isinstance(edges_raw, list) or len(edges_raw) > 60:
        fail("record.decision_map.edges must contain at most 60 edges")
    nodes: list[dict[str, str]] = []
    ids: set[str] = set()
    for position, raw in enumerate(nodes_raw):
        node = require_object(raw, label=f"record.decision_map.nodes[{position}]")
        if set(node) != {"id", "label"}:
            fail("decision-map node fields must be id and label")
        node_id = require_single_line(node["id"], label=f"record.decision_map.nodes[{position}].id")
        label = require_single_line(node["label"], label=f"record.decision_map.nodes[{position}].label")
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", node_id) is None or node_id in ids:
            fail("decision-map node id is invalid or duplicated")
        if any(character in label for character in ('"', "[", "]")):
            fail("decision-map node label contains unsupported punctuation")
        ids.add(node_id)
        nodes.append({"id": node_id, "label": label})
    edges: list[dict[str, str]] = []
    for position, raw in enumerate(edges_raw):
        edge = require_object(raw, label=f"record.decision_map.edges[{position}]")
        if set(edge) != {"from", "to", "label"}:
            fail("decision-map edge fields must be from, to, and label")
        source = require_single_line(edge["from"], label="decision-map edge from")
        target = require_single_line(edge["to"], label="decision-map edge to")
        label = require_single_line(edge["label"], label="decision-map edge label")
        if source not in ids or target not in ids or "|" in label:
            fail("decision-map edge references an unknown node or invalid label")
        edges.append({"from": source, "to": target, "label": label})
    return {"direction": direction, "nodes": nodes, "edges": edges}


def parse_record(value: object, *, operation: str) -> dict[str, object]:
    record = require_object(value, label="spec.record")
    required = set(RECORD_COMMON_FIELDS)
    if operation in {"create", "replace"}:
        required |= {"topic", "slug"}
    allowed = required | {"decision_map"}
    if set(record) - allowed or not required.issubset(record):
        fail(f"record fields are invalid for {operation}")
    parsed: dict[str, object] = {}
    for key in ("title", "abstract", "summary", "goal", "continue_here"):
        parsed[key] = require_single_line(record[key], label=f"record.{key}")
    parsed["search_keys"] = require_string_list(record["search_keys"], label="record.search_keys")
    linked = require_string_list(record["linked_artifacts"], label="record.linked_artifacts", allow_empty=True)
    for path in linked:
        pure = PurePosixPath(path)
        if pure.is_absolute() or ".." in pure.parts or pure.as_posix() != path:
            fail("record.linked_artifacts must contain safe project-relative paths")
    parsed["linked_artifacts"] = linked
    parsed["settled"] = require_string_list(record["settled"], label="record.settled", allow_empty=True)
    parsed["still_open"] = require_string_list(record["still_open"], label="record.still_open", allow_empty=True)
    parsed["key_evidence"] = require_string_list(record["key_evidence"], label="record.key_evidence")
    if operation in {"create", "replace"}:
        parsed["topic"] = validate_slug(record["topic"], label="record.topic")
        parsed["slug"] = validate_slug(record["slug"], label="record.slug")
    if "decision_map" in record:
        parsed["decision_map"] = parse_decision_map(record["decision_map"])
    return parsed


def parse_spec(value: object) -> tuple[str, dict[str, object], dict[str, str], str, str | None, str | None]:
    spec = require_object(value, label="spec")
    base = {"schema_version", "operation", "expected_revision", "record", "current_summary"}
    operation = spec.get("operation")
    allowed = set(base)
    if operation == "close":
        allowed.add("close_status")
        if spec.get("close_status") == "superseded":
            allowed.add("superseded_by")
    if set(spec) != allowed:
        fail(f"spec fields are invalid for operation {operation}")
    if spec["schema_version"] != 1:
        fail("spec.schema_version must be 1")
    if operation not in {"create", "update", "close", "replace"}:
        fail("spec.operation must be create, update, close, or replace")
    expected_revision = require_single_line(spec["expected_revision"], label="spec.expected_revision")
    if re.fullmatch(r"[0-9a-f]{64}", expected_revision) is None:
        fail("spec.expected_revision must be the opaque SHA-256 revision returned by inspect")
    record = parse_record(spec["record"], operation=operation)
    summary_raw = require_object(spec["current_summary"], label="spec.current_summary")
    if set(summary_raw) != set(SUMMARY_FIELDS):
        fail(f"spec.current_summary fields must be exactly: {', '.join(SUMMARY_FIELDS)}")
    summary = {
        key: require_single_line(summary_raw[key], label=f"spec.current_summary.{key}")
        for key in SUMMARY_FIELDS
    }
    try:
        date.fromisoformat(summary["last_updated"])
    except ValueError:
        fail("current_summary.last_updated must be a valid YYYY-MM-DD date")
    close_status = None
    superseded_by = None
    if operation == "close":
        close_status = spec["close_status"]
        if close_status not in {"accepted", "superseded"}:
            fail("spec.close_status must be accepted or superseded")
        if close_status == "superseded":
            superseded_by = require_single_line(spec["superseded_by"], label="spec.superseded_by")
    return operation, record, summary, expected_revision, close_status, superseded_by


def artifact_headers(text: str) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for line in text.splitlines():
        if line.startswith("#"):
            break
        if ":" in line:
            key, value = line.split(":", 1)
            result.setdefault(key.strip(), []).append(value.strip())
    return result


def section(text: str, heading: str) -> str:
    matches = list(
        re.finditer(
            rf"^## {re.escape(heading)}\s*$\n(?P<body>.*?)(?=^## |\Z)",
            text,
            re.MULTILINE | re.DOTALL,
        )
    )
    if len(matches) != 1 or not matches[0].group("body").strip():
        fail(f"artifact must contain exactly one non-empty {heading} section")
    return matches[0].group("body").strip()


def is_none(value: str) -> bool:
    normalized = re.sub(r"^[\s>*+-]+", "", value.strip().lower()).strip("`*_ .")
    return normalized in {"none", "n/a", "not applicable", "nothing"}


def is_placeholder_text(value: str) -> bool:
    normalized = value.strip()
    return not normalized or (normalized.startswith("<") and normalized.endswith(">"))


def validate_artifact(text: str, *, operation: str, entry: dict[str, object]) -> str:
    headers_raw = artifact_headers(text)
    headers: dict[str, str] = {}
    for key in REQUIRED_HEADERS:
        values = headers_raw.get(key, [])
        if len(values) != 1 or is_placeholder_text(values[0]):
            fail(f"artifact header must appear exactly once with a concrete value: {key}")
        headers[key] = values[0]
    if headers["Artifact Type"] != "discussion" or headers["Authority"] != "supporting":
        fail("artifact must be a supporting discussion")
    status = headers["Status"]
    allowed = {"active"} if operation in {"create", "update"} else {"accepted", "superseded"}
    if status not in allowed:
        fail(f"artifact status is incoherent with {operation}")
    if status != entry.get("status"):
        fail("artifact Status must exactly equal entry.status")
    superseded_by = headers["Superseded By"]
    if status == "superseded" and is_none(superseded_by):
        fail("superseded artifact must name a successor or reason in Superseded By")
    if status == "active" and not is_none(superseded_by):
        fail("active artifact Superseded By must be none")
    try:
        date.fromisoformat(headers["Last Updated"])
    except ValueError:
        fail("artifact Last Updated must be a valid YYYY-MM-DD date")
    if headers["Last Updated"] != entry["updated"]:
        fail("artifact Last Updated must equal entry.updated")
    titles = re.findall(r"^# (?!#)(.+?)\s*$", text, re.MULTILINE)
    if len(titles) != 1 or is_placeholder_text(titles[0]) or titles[0].strip().casefold() == "teamwork discussion":
        fail("artifact must contain one concrete H1")
    bodies = {heading: section(text, heading) for heading in REQUIRED_SECTIONS}
    for heading, body in bodies.items():
        if is_placeholder_text(body):
            fail(f"artifact {heading} section must not be a placeholder")
    if status == "active" and is_none(bodies["Still open"]):
        fail("active artifact Still open must name an unresolved item")
    if status != "active" and not is_none(bodies["Still open"]):
        fail("closed artifact Still open must explicitly be none")
    decision_maps = list(
        re.finditer(
            r"^## Decision map\s*$\n(?P<body>.*?)(?=^## |\Z)",
            text,
            re.MULTILINE | re.DOTALL,
        )
    )
    if len(decision_maps) > 1:
        fail("artifact Decision map section must appear at most once")
    if decision_maps:
        body = decision_maps[0].group("body").strip()
        mermaid = re.search(r"```mermaid\s*\n(?P<diagram>.*?)```", body, re.DOTALL)
        if mermaid is None:
            fail("artifact Decision map must contain Mermaid")
        diagram = mermaid.group("diagram")
        if re.search(r"^\s*flowchart(?:\s+(?:TB|TD|BT|RL|LR))?\s*$", diagram, re.MULTILINE) is None:
            fail("artifact Decision map must be a flowchart")
        if re.search(r"^\s*[A-Za-z_][A-Za-z0-9_-]*\s*(?:\[|\(|\{)", diagram, re.MULTILINE) is None:
            fail("artifact Decision map must include a node")
    return status


def render_list(items: list[str], *, none_when_empty: bool = True) -> str:
    if not items and none_when_empty:
        return "- None"
    return "\n".join(f"- {item}" for item in items)


def render_decision_map(decision: dict[str, object]) -> str:
    direction = decision["direction"]
    nodes = decision["nodes"]
    edges = decision["edges"]
    assert isinstance(direction, str) and isinstance(nodes, list) and isinstance(edges, list)
    lines = [f"flowchart {direction}"]
    for node in nodes:
        assert isinstance(node, dict)
        lines.append(f'    {node["id"]}["{node["label"]}"]')
    for edge in edges:
        assert isinstance(edge, dict)
        lines.append(f'    {edge["from"]} -->|{edge["label"]}| {edge["to"]}')
    return "## Decision map\n\n```mermaid\n" + "\n".join(lines) + "\n```\n\n"


def render_artifact(
    record: dict[str, object], *, status: str, updated: str, superseded_by: str
) -> str:
    search_keys = record["search_keys"]
    linked = record["linked_artifacts"]
    settled = record["settled"]
    still_open = record["still_open"]
    evidence = record["key_evidence"]
    assert all(isinstance(value, list) for value in (search_keys, linked, settled, still_open, evidence))
    if status == "active" and not still_open:
        fail("active record must contain at least one still_open item")
    if status != "active" and still_open:
        fail("closed record still_open must be empty")
    linked_text = ", ".join(linked) if linked else "none"
    decision_text = ""
    if "decision_map" in record:
        decision = record["decision_map"]
        assert isinstance(decision, dict)
        decision_text = render_decision_map(decision)
    text = f"""Artifact Type: discussion
Status: {status}
Authority: supporting
Last Updated: {updated}
Search Keys: {", ".join(search_keys)}
Abstract: {record["abstract"]}
Linked Artifacts: {linked_text}
Superseded By: {superseded_by}

# {record["title"]}

## Goal

{record["goal"]}

## Settled

{render_list(settled)}

## Still open

{render_list(still_open)}

## Key evidence

{render_list(evidence)}

{decision_text}## Continue here

{record["continue_here"]}
"""
    return text


def canonical_entry_from_record(
    record: dict[str, object],
    *,
    topic: str,
    path: str,
    status: str,
    updated: str,
    supersedes: list[str],
) -> dict[str, object]:
    return {
        "topic": topic,
        "kind": "discussion",
        "title": record["title"],
        "status": status,
        "currentness": "current" if status == "active" else "historical",
        "authority": "supporting" if status in {"active", "accepted"} else "superseded",
        "path": path,
        "linked": list(record["linked_artifacts"]),
        "evidence_paths": [path],
        "supersedes": list(supersedes),
        "search_keys": list(record["search_keys"]),
        "updated": updated,
        "summary": record["summary"],
    }


def rewrite_replaced_artifact(text: str, *, new_path: str, updated: str) -> str:
    result = replace_unique_line(text, "Status:", "superseded")
    result = replace_unique_line(result, "Last Updated:", updated)
    result = replace_unique_line(result, "Superseded By:", new_path)
    pattern = re.compile(r"(^## Still open\s*$\n)(.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL)
    matches = list(pattern.finditer(result))
    if len(matches) != 1:
        fail("active artifact must contain exactly one Still open section")
    match = matches[0]
    return result[: match.start()] + match.group(1) + "\n- None\n\n" + result[match.end() :]


def parse_index(text: str) -> dict[str, object]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        fail(f"index.json is invalid JSON: {exc}")
    index = require_object(value, label="index.json")
    validate_index_structure(index)
    validate_discussion_entries(index)
    return index


def valid_date(value: object) -> bool:
    if not isinstance(value, str) or re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) is None:
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def validate_index_structure(index: dict[str, object]) -> None:
    required = {
        "schema_version", "last_updated", "project", "source_of_truth_order",
        "ignore_globs", "budgets", "active", "entries", "profiles",
    }
    missing = sorted(required - set(index))
    if missing:
        fail(f"index.json missing fields: {', '.join(missing)}")
    if index["schema_version"] != 1 or not valid_date(index["last_updated"]):
        fail("index.json must have schema_version 1 and a valid last_updated date")
    project = index["project"]
    if not isinstance(project, dict) or any(not isinstance(project.get(key), str) or not project[key] for key in ("name", "root", "description")):
        fail("index.json project must contain non-empty name, root, and description")
    if project["root"] != ".":
        fail("actual-project index project.root must be .")
    source_order = index["source_of_truth_order"]
    if not isinstance(source_order, list) or not source_order:
        fail("index.json source_of_truth_order must be a non-empty array")
    ignores = index["ignore_globs"]
    if not isinstance(ignores, list) or ".planning/**" not in ignores:
        fail("index.json ignore_globs must include .planning/**")
    budgets = index["budgets"]
    if not isinstance(budgets, dict) or set(budgets) not in (
        {"header_first"},
        {"default_max_files", "default_max_artifact_bodies", "header_first"},
    ) or budgets.get("header_first") is not True:
        fail("index.json budgets must be a supported header-first shape")
    if "default_max_files" in budgets:
        max_files = budgets["default_max_files"]
        max_bodies = budgets["default_max_artifact_bodies"]
        if (
            not isinstance(max_files, int) or isinstance(max_files, bool) or not 1 <= max_files <= 10
            or not isinstance(max_bodies, int) or isinstance(max_bodies, bool) or not 0 <= max_bodies <= 5
        ):
            fail("index.json legacy budget values are invalid")
    active = index["active"]
    entries = index["entries"]
    if not isinstance(active, dict) or not isinstance(entries, list) or not entries:
        fail("index.json must contain an active object and non-empty entries array")
    if active.get("current") != "docs/teamwork/current.md":
        fail("actual-project index active.current must be docs/teamwork/current.md")
    for key in ACTIVE_POINTER_KEYS:
        value = active.get(key)
        if key in active and value is not None and (not isinstance(value, str) or not value):
            fail(f"index.json active.{key} must be null or a non-empty string")
    results = active.get("results", [])
    if not isinstance(results, list) or any(not isinstance(item, str) or not item for item in results) or len(results) != len(set(results)):
        fail("index.json active.results must contain unique non-empty paths")
    seen_active: set[tuple[object, object]] = set()
    for position, entry in enumerate(entries):
        if not isinstance(entry, dict):
            fail(f"index.json entries[{position}] must be an object")
        missing_entry = [key for key in ENTRY_REQUIRED if key not in entry]
        if missing_entry:
            fail(f"index.json entries[{position}] is missing fields: {', '.join(missing_entry)}")
        if entry["kind"] not in KINDS or entry["status"] not in STATUSES or entry["currentness"] not in CURRENTNESS or entry["authority"] not in AUTHORITIES:
            fail(f"index.json entries[{position}] has an invalid lifecycle value")
        for key in ("topic", "title", "path", "summary"):
            if not isinstance(entry[key], str) or not entry[key]:
                fail(f"index.json entries[{position}].{key} must be a non-empty string")
        if not valid_date(entry["updated"]):
            fail(f"index.json entries[{position}].updated must be a valid date")
        if entry["status"] == "active":
            active_key = (entry["topic"], entry["kind"])
            if active_key in seen_active:
                fail("index.json has duplicate active topic/kind entries")
            seen_active.add(active_key)
    by_path: dict[str, list[dict[str, object]]] = {}
    for entry in entries:
        assert isinstance(entry, dict)
        by_path.setdefault(str(entry["path"]), []).append(entry)
    pointers = [(f"active.{key}", active.get(key)) for key in ACTIVE_POINTER_KEYS]
    pointers.extend((f"active.results[{i}]", value) for i, value in enumerate(results))
    for label, value in pointers:
        if value is None:
            continue
        eligible = [
            entry for entry in by_path.get(str(value), [])
            if entry["status"] in {"active", "accepted"}
            and entry["currentness"] == "current"
            and entry["authority"] in {"canonical", "active-summary", "supporting"}
        ]
        if not eligible:
            fail(f"index.json {label} has no eligible matching entry")
    profiles = index["profiles"]
    if not isinstance(profiles, dict) or not profiles:
        fail("index.json profiles must be a non-empty object")
    pending = index.get("pending", [])
    if not isinstance(pending, list) or len(pending) > 5:
        fail("index.json pending must be an array with at most five items")


def validate_discussion_entries(index: dict[str, object]) -> None:
    active = index["active"]
    entries = index["entries"]
    assert isinstance(active, dict) and isinstance(entries, list)
    active_path = active.get("discussion")
    discussions = [entry for entry in entries if isinstance(entry, dict) and entry.get("kind") == "discussion"]
    paths: set[str] = set()
    for entry in discussions:
        path = entry["path"]
        match = DISCUSSION_RE.fullmatch(path) if isinstance(path, str) else None
        if match is None:
            fail("index.json discussion entry path must be dated kebab-case Markdown")
        try:
            date.fromisoformat(match.group(1))
        except ValueError:
            fail("index.json discussion entry path must begin with a valid calendar date")
        if path in paths:
            fail(f"index.json has duplicate discussion path: {path}")
        paths.add(path)
        status = entry["status"]
        if status not in {"active", "accepted", "superseded"}:
            fail("index.json discussion entry has an invalid status")
        if status == "accepted" and (entry["currentness"], entry["authority"]) != ("historical", "supporting"):
            fail("accepted discussion must be historical supporting context")
        if status == "superseded" and (entry["currentness"], entry["authority"]) != ("historical", "superseded"):
            fail("superseded discussion must be historical superseded context")
    if active_path is None:
        if any(entry["status"] == "active" or entry["currentness"] == "current" for entry in discussions):
            fail("active.discussion is null but an active/current discussion remains")
    else:
        matching = [entry for entry in discussions if entry["path"] == active_path]
        if len(matching) != 1 or (
            matching[0]["status"], matching[0]["currentness"], matching[0]["authority"]
        ) != ("active", "current", "supporting"):
            fail("active.discussion must resolve to one active current supporting entry")
        if any(
            entry is not matching[0] and (entry["status"] == "active" or entry["currentness"] == "current")
            for entry in discussions
        ):
            fail("only active.discussion may be active/current")


def normalized_anchor(value: str) -> str:
    value = value.strip()
    if value.startswith("`") and value.endswith("`."):
        value = value[:-1]
    if value.startswith("`") and value.endswith("`"):
        value = value[1:-1].strip()
    if value == "none.":
        return "none"
    if value.endswith(".md."):
        return value[:-1]
    return value


def anchor(text: str, marker: str, *, label: str) -> str:
    values = [normalized_anchor(line[len(marker) :]) for line in text.splitlines() if line.startswith(marker)]
    if len(values) != 1 or not values[0]:
        fail(f"{label} must contain exactly one non-empty discussion anchor")
    return values[0]


def validate_agreement(index: dict[str, object], current: str, readme: str) -> str:
    active = index["active"]
    assert isinstance(active, dict)
    value = active.get("discussion")
    if value is not None and not isinstance(value, str):
        fail("index active.discussion must be null or a string")
    expected = value or "none"
    if anchor(current, "- Active discussion:", label="current.md") != expected:
        fail("current.md Active discussion anchor disagrees with index")
    if anchor(readme, "- Active discussion route:", label="README.md") != expected:
        fail("README.md Active discussion route disagrees with index")
    return expected


def parsed_artifact_record(text: str) -> dict[str, object]:
    headers = artifact_headers(text)
    return {
        "headers": {
            key: values[0] if len(values) == 1 else values
            for key, values in headers.items()
        },
        "title": (re.findall(r"^# (?!#)(.+?)\s*$", text, re.MULTILINE) or [None])[0],
        "sections": {heading: section(text, heading) for heading in REQUIRED_SECTIONS},
    }


def replace_unique_line(text: str, marker: str, value: str, *, suffix: str = "") -> str:
    lines = text.splitlines(keepends=True)
    matching = [i for i, line in enumerate(lines) if line.rstrip("\r\n").startswith(marker)]
    if len(matching) != 1:
        fail(f"anchor must occur exactly once before update: {marker}")
    index = matching[0]
    ending = lines[index][len(lines[index].rstrip("\r\n")) :]
    lines[index] = f"{marker} {value}{suffix}{ending}"
    return "".join(lines)


def updated_current(text: str, summary: dict[str, str], active: str | None) -> str:
    result = text
    for key in SUMMARY_FIELDS:
        result = replace_unique_line(result, SUMMARY_MARKERS[key], summary[key])
    return replace_unique_line(result, "- Active discussion:", active or "none", suffix=".")


def updated_readme(text: str, active: str | None) -> str:
    return replace_unique_line(text, "- Active discussion route:", active or "none")


@dataclass(frozen=True)
class FdSnapshot:
    logical: str
    parent_fd: int
    name: str
    exists: bool
    device: int | None = None
    inode: int | None = None
    mode: int | None = None
    data: bytes | None = None


@dataclass
class FdStaged:
    before: FdSnapshot
    stage_name: str
    intended: bytes
    intended_mode: int
    stage_created: bool
    stage_device: int
    stage_inode: int
    backup_name: str | None = None
    backup_created: bool = False
    target_installed: bool = False
    installed_device: int | None = None
    installed_inode: int | None = None


class Faults:
    def __init__(self) -> None:
        self.counts: dict[str, int] = {}

    def hit(self, kind: str) -> None:
        self.counts[kind] = self.counts.get(kind, 0) + 1
        raw = os.environ.get(f"TEAMWORK_DISCUSSION_TRANSACTION_FAIL_{kind}_N")
        if raw is None:
            return
        try:
            requested = int(raw)
        except ValueError:
            fail(f"failure injection {kind} must be a positive integer")
        if requested < 1:
            fail(f"failure injection {kind} must be a positive integer")
        if requested == self.counts[kind]:
            raise OSError(f"injected {kind.lower()} failure {requested}")


def require_fd_platform() -> None:
    if not getattr(os, "O_NOFOLLOW", 0) or not getattr(os, "O_DIRECTORY", 0):
        fail("platform lacks O_NOFOLLOW/O_DIRECTORY")
    for function in (os.open, os.stat, os.mkdir, os.unlink, os.rmdir):
        if function not in os.supports_dir_fd:
            fail(f"platform lacks dir_fd support for {function.__name__}")
    parameters = inspect.signature(os.replace).parameters
    if "src_dir_fd" not in parameters or "dst_dir_fd" not in parameters:
        fail("platform lacks descriptor-relative os.replace")


class FdTree:
    def __init__(self, project_root: str) -> None:
        require_fd_platform()
        self.root_path = os.path.abspath(project_root)
        self.fds: dict[str, int] = {}
        self.identities: dict[str, tuple[int, int, int] | None] = {}
        self.lock_fd: int | None = None
        self.initialized = False
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        try:
            root_fd = os.open(self.root_path, flags)
        except OSError as exc:
            fail(f"cannot open project root safely: {exc}")
        self.fds["root"] = root_fd
        root_info = os.fstat(root_fd)
        if not stat.S_ISDIR(root_info.st_mode):
            fail("project root must be a directory")
        self.device = root_info.st_dev
        self.identities["root"] = self._identity(root_info)
        try:
            self._open_child("root", "docs", "docs")
        except FileNotFoundError:
            return
        try:
            self._open_child("docs", "teamwork", "teamwork")
        except FileNotFoundError:
            return
        try:
            self._open_child("teamwork", "discussion", "discussion")
        except FileNotFoundError:
            self.identities["discussion"] = None
        self._require_no_markers()
        anchors_present: list[bool] = []
        for name in ("index.json", "current.md", "README.md"):
            try:
                os.stat(name, dir_fd=self.fds["teamwork"], follow_symlinks=False)
                anchors_present.append(True)
            except FileNotFoundError:
                anchors_present.append(False)
        if not all(anchors_present):
            if any(anchors_present):
                fail("partial Teamwork runtime initialization")
        self.lock_fd = os.dup(self.fds["teamwork"])
        try:
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            fail(f"cannot acquire index transaction lock: {exc}")
        self._require_no_markers()
        self.initialized = all(anchors_present)

    @staticmethod
    def _identity(info: os.stat_result) -> tuple[int, int, int]:
        return (info.st_dev, info.st_ino, stat.S_IMODE(info.st_mode))

    def _require_no_markers(self) -> None:
        for marker in (MARKER_NAME, INIT_MARKER_NAME):
            try:
                os.stat(marker, dir_fd=self.fds["teamwork"], follow_symlinks=False)
            except FileNotFoundError:
                continue
            label = "discussion" if marker == MARKER_NAME else "Teamwork init"
            fail(
                f"INDETERMINATE: an unfinished {label} transaction marker exists",
                category="INDETERMINATE",
            )

    def _open_child(self, parent_key: str, name: str, key: str) -> None:
        parent_fd = self.fds[parent_key]
        before = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        if stat.S_ISLNK(before.st_mode) or not stat.S_ISDIR(before.st_mode):
            fail(f"{key} must be a non-symlink directory")
        if before.st_dev != self.device:
            fail(f"{key} must be on the project-root device")
        fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent_fd)
        opened = os.fstat(fd)
        if self._identity(opened) != self._identity(before):
            os.close(fd)
            fail(f"{key} changed identity while opening")
        self.fds[key] = fd
        self.identities[key] = self._identity(opened)

    def ensure_discussion(self) -> bool:
        if "discussion" in self.fds:
            return False
        os.mkdir("discussion", mode=0o755, dir_fd=self.fds["teamwork"])
        try:
            self._open_child("teamwork", "discussion", "discussion")
        except Exception as original:
            try:
                os.rmdir("discussion", dir_fd=self.fds["teamwork"])
            except OSError as cleanup:
                fail(f"INDETERMINATE: could not safely open or remove new discussion directory: {original}; {cleanup}")
            raise
        return True

    def verify_linked(self) -> None:
        root_now = os.stat(self.root_path, follow_symlinks=False)
        if self._identity(root_now) != self.identities["root"] or not stat.S_ISDIR(root_now.st_mode):
            fail("project root identity changed")
        for parent, name, key in (("root", "docs", "docs"), ("docs", "teamwork", "teamwork")):
            now = os.stat(name, dir_fd=self.fds[parent], follow_symlinks=False)
            if self._identity(now) != self.identities[key] or not stat.S_ISDIR(now.st_mode):
                fail(f"{key} directory identity changed")
        expected = self.identities.get("discussion")
        try:
            now = os.stat("discussion", dir_fd=self.fds["teamwork"], follow_symlinks=False)
        except FileNotFoundError:
            if expected is not None:
                fail("discussion directory disappeared")
        else:
            if expected is None or self._identity(now) != expected or not stat.S_ISDIR(now.st_mode):
                fail("discussion directory identity changed")

    def metadata(self) -> dict[str, tuple[int, int, int] | None]:
        return dict(self.identities)

    def remove_created_discussion(self) -> None:
        fd = self.fds.pop("discussion", None)
        if fd is not None:
            os.close(fd)
        os.rmdir("discussion", dir_fd=self.fds["teamwork"])
        self.identities["discussion"] = None

    def close(self) -> None:
        lock_fd = getattr(self, "lock_fd", None)
        if lock_fd is not None:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
            except OSError:
                pass
            try:
                os.close(lock_fd)
            except OSError:
                pass
            self.lock_fd = None
        for key in ("discussion", "teamwork", "docs", "root"):
            fd = self.fds.pop(key, None)
            if fd is not None:
                try:
                    os.close(fd)
                except OSError:
                    pass


@dataclass(frozen=True)
class GuardCreatedDirectory:
    parent_key: str
    name: str
    key: str
    identity: tuple[int, int, int]


class GuardTree:
    def __init__(self, project_root: str, *, allow_init_recovery: bool = False) -> None:
        require_fd_platform()
        self.root_path = os.path.abspath(project_root)
        self.fds: dict[str, int] = {}
        self.identities: dict[str, tuple[int, int, int]] = {}
        self.created: list[GuardCreatedDirectory] = []
        self.device: int | None = None
        self.locked = False
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        try:
            root_fd = os.open(self.root_path, flags)
        except OSError as exc:
            fail(f"cannot open project root safely: {exc}")
        self.fds["root"] = root_fd
        root_info = os.fstat(root_fd)
        if not stat.S_ISDIR(root_info.st_mode):
            fail("project root must be a directory")
        self.device = root_info.st_dev
        self.identities["root"] = self._identity(root_info)
        try:
            self._open_or_create_child("root", "docs", "docs")
            self._open_or_create_child("docs", "teamwork", "teamwork")
            self.fds["lock"] = os.dup(self.fds["teamwork"])
            try:
                fcntl.flock(self.fds["lock"], fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                fail(f"cannot acquire Teamwork initialization guard: {exc}")
            self.locked = True
            if allow_init_recovery:
                self.verify_marker_absent(allow_init_recovery=True)
            else:
                self.verify_marker_absent()
            self.verify_linked()
        except Exception as original:
            try:
                self.cleanup_created()
            except TransactionError as cleanup:
                self.close()
                raise cleanup from original
            self.close()
            raise

    @staticmethod
    def _identity(info: os.stat_result) -> tuple[int, int, int]:
        return (info.st_dev, info.st_ino, stat.S_IMODE(info.st_mode))

    def _open_or_create_child(self, parent_key: str, name: str, key: str) -> None:
        parent_fd = self.fds[parent_key]
        created = False
        try:
            before = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            try:
                os.mkdir(name, mode=0o755, dir_fd=parent_fd)
            except FileExistsError:
                fail(f"{key} appeared concurrently during guarded creation")
            else:
                created = True
            try:
                before = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
            except OSError as exc:
                category = "INDETERMINATE" if created else "PREWRITE_SAFE"
                fail(
                    f"{category}: {key} could not be inspected after directory creation: {exc}",
                    category=category,
                )
        if stat.S_ISLNK(before.st_mode) or not stat.S_ISDIR(before.st_mode):
            category = "INDETERMINATE" if created else "PREWRITE_SAFE"
            fail(f"{category}: {key} must be a non-symlink directory", category=category)
        identity = self._identity(before)
        if created:
            self.created.append(GuardCreatedDirectory(parent_key, name, key, identity))
        if before.st_dev != self.device:
            fail(f"{key} must be on the project-root device")
        fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent_fd)
        opened = os.fstat(fd)
        if self._identity(opened) != identity:
            os.close(fd)
            fail(f"{key} changed identity while opening")
        self.fds[key] = fd
        self.identities[key] = self._identity(opened)
        if created:
            os.fsync(parent_fd)

    def verify_marker_absent(self, *, allow_init_recovery: bool = False) -> None:
        markers = (MARKER_NAME,) if allow_init_recovery else (MARKER_NAME, INIT_MARKER_NAME)
        for marker in markers:
            try:
                os.stat(marker, dir_fd=self.fds["teamwork"], follow_symlinks=False)
            except FileNotFoundError:
                continue
            label = "discussion" if marker == MARKER_NAME else "Teamwork init"
            fail(
                f"INDETERMINATE: an unfinished {label} transaction marker exists",
                category="INDETERMINATE",
            )

    def verify_linked(self) -> None:
        root_now = os.stat(self.root_path, follow_symlinks=False)
        if self._identity(root_now) != self.identities["root"] or not stat.S_ISDIR(root_now.st_mode):
            fail("INDETERMINATE: project root identity changed while guarded")
        for parent, name, key in (("root", "docs", "docs"), ("docs", "teamwork", "teamwork")):
            now = os.stat(name, dir_fd=self.fds[parent], follow_symlinks=False)
            if (
                self._identity(now) != self.identities[key]
                or not stat.S_ISDIR(now.st_mode)
                or now.st_dev != self.device
            ):
                fail(f"INDETERMINATE: {key} directory identity changed while guarded")

    def cleanup_created(self) -> None:
        """Remove only directories this guard created and can still prove empty."""
        for created in reversed(self.created):
            parent_fd = self.fds.get(created.parent_key)
            child_fd = self.fds.get(created.key)
            if parent_fd is None or child_fd is None:
                fail(
                    f"INDETERMINATE: cannot clean created {created.key} without retained descriptors",
                    category="INDETERMINATE",
                )
            try:
                linked = os.stat(created.name, dir_fd=parent_fd, follow_symlinks=False)
                opened = os.fstat(child_fd)
            except OSError as exc:
                fail(
                    f"INDETERMINATE: cannot verify created {created.key} before cleanup: {exc}",
                    category="INDETERMINATE",
                )
            if (
                self._identity(linked) != created.identity
                or self._identity(opened) != created.identity
                or not stat.S_ISDIR(linked.st_mode)
                or linked.st_dev != self.device
            ):
                fail(
                    f"INDETERMINATE: created {created.key} identity changed before cleanup",
                    category="INDETERMINATE",
                )
            try:
                entries = os.listdir(child_fd)
            except OSError as exc:
                fail(
                    f"INDETERMINATE: cannot inspect created {created.key} before cleanup: {exc}",
                    category="INDETERMINATE",
                )
            if entries:
                fail(
                    f"INDETERMINATE: created {created.key} is no longer empty",
                    category="INDETERMINATE",
                )
            try:
                os.rmdir(created.name, dir_fd=parent_fd)
                os.fsync(parent_fd)
            except OSError as exc:
                fail(
                    f"INDETERMINATE: could not durably remove created {created.key}: {exc}",
                    category="INDETERMINATE",
                )
            try:
                os.stat(created.name, dir_fd=parent_fd, follow_symlinks=False)
            except FileNotFoundError:
                pass
            except OSError as exc:
                fail(
                    f"INDETERMINATE: cannot confirm removal of created {created.key}: {exc}",
                    category="INDETERMINATE",
                )
            else:
                fail(
                    f"INDETERMINATE: created {created.key} remained after cleanup",
                    category="INDETERMINATE",
                )
            self.created.pop()

    def close(self) -> None:
        lock_fd = self.fds.get("lock")
        if lock_fd is not None and self.locked:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
            except OSError:
                pass
        for key in ("lock", "teamwork", "docs", "root"):
            fd = self.fds.pop(key, None)
            if fd is not None:
                try:
                    os.close(fd)
                except OSError:
                    pass
        self.locked = False


def guard_command(project_root: str, command: list[str], *, allow_init_recovery: bool = False) -> int:
    if not command:
        fail("guard requires a command after --")
    tree = GuardTree(project_root, allow_init_recovery=allow_init_recovery)
    try:
        try:
            token = secrets.token_hex(32)
            environment = os.environ.copy()
            for key, variable in GUARD_ENV.items():
                environment[variable] = str(tree.fds[key])
            environment[GUARD_TOKEN_ENV] = token
            child = subprocess.Popen(
                command,
                env=environment,
                pass_fds=tuple(tree.fds[key] for key in ("root", "docs", "teamwork", "lock")),
            )
        except Exception as original:
            try:
                tree.cleanup_created()
            except TransactionError as cleanup:
                raise cleanup from original
            raise
        child_exit = child.wait()
        tree.verify_marker_absent()
        tree.verify_linked()
        return child_exit
    finally:
        tree.close()


def snapshot_at(tree: FdTree, parent_key: str, name: str, logical: str, *, required: bool) -> FdSnapshot:
    parent_fd = tree.fds[parent_key]
    try:
        before = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        if required:
            fail(f"missing {logical}")
        return FdSnapshot(logical, parent_fd, name, False)
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        fail(f"{logical} must be a single-link non-symlink regular file")
    if before.st_dev != tree.device:
        fail(f"{logical} must be on the project-root device")
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent_fd)
    try:
        opened = os.fstat(fd)
        if opened.st_dev != before.st_dev or opened.st_ino != before.st_ino or opened.st_nlink != 1:
            fail(f"{logical} changed identity while opening")
        chunks: list[bytes] = []
        while chunk := os.read(fd, 1024 * 1024):
            chunks.append(chunk)
    finally:
        os.close(fd)
    return FdSnapshot(
        logical, parent_fd, name, True, before.st_dev, before.st_ino,
        stat.S_IMODE(before.st_mode), b"".join(chunks),
    )


def assert_fd_snapshot(tree: FdTree, before: FdSnapshot) -> None:
    current = snapshot_at(tree, "discussion" if before.logical.startswith("docs/teamwork/discussion/") else "teamwork", before.name, before.logical, required=before.exists)
    if not before.exists:
        if current.exists:
            fail(f"{before.logical} appeared during preparation")
        return
    if (current.device, current.inode, current.mode, current.data) != (
        before.device, before.inode, before.mode, before.data,
    ):
        fail(f"{before.logical} changed during preparation")


def decode_fd(snapshot: FdSnapshot) -> str:
    assert snapshot.data is not None
    try:
        return snapshot.data.decode("utf-8")
    except UnicodeDecodeError as exc:
        fail(f"{snapshot.logical} is not UTF-8: {exc}")


def fd_revision(directories: dict[str, tuple[int, int, int] | None], files: list[FdSnapshot]) -> str:
    digest = hashlib.sha256()
    for key in sorted(directories):
        digest.update(key.encode() + b"\0" + repr(directories[key]).encode() + b"\0")
    for item in sorted(files, key=lambda value: value.logical):
        digest.update(item.logical.encode() + b"\0")
        digest.update(repr((item.exists, item.device, item.inode, item.mode)).encode() + b"\0")
        digest.update(item.data or b"")
        digest.update(b"\0")
    return digest.hexdigest()


def discussion_snapshots(tree: FdTree, index: dict[str, object]) -> dict[str, FdSnapshot]:
    entries = index["entries"]
    assert isinstance(entries, list)
    discussions = [entry for entry in entries if isinstance(entry, dict) and entry.get("kind") == "discussion"]
    if discussions and "discussion" not in tree.fds:
        fail("indexed discussions require the discussion directory")
    result: dict[str, FdSnapshot] = {}
    for entry in discussions:
        path = str(entry["path"])
        name = PurePosixPath(path).name
        snap = snapshot_at(tree, "discussion", name, path, required=True)
        operation = "update" if entry["status"] == "active" else "close"
        validate_artifact(decode_fd(snap), operation=operation, entry=entry)
        result[path] = snap
    return result


def inspect_project(project_root: str) -> dict[str, object]:
    tree = FdTree(project_root)
    try:
        if not tree.initialized:
            return {"initialized": False, "active": None}
        index_snap = snapshot_at(tree, "teamwork", "index.json", "docs/teamwork/index.json", required=True)
        current_snap = snapshot_at(tree, "teamwork", "current.md", "docs/teamwork/current.md", required=True)
        readme_snap = snapshot_at(tree, "teamwork", "README.md", "docs/teamwork/README.md", required=True)
        index = parse_index(decode_fd(index_snap))
        current = decode_fd(current_snap)
        readme = decode_fd(readme_snap)
        active_path = validate_agreement(index, current, readme)
        artifacts = discussion_snapshots(tree, index)
        active_record = None
        if active_path != "none":
            entries = index["entries"]
            assert isinstance(entries, list)
            entry = next(item for item in entries if isinstance(item, dict) and item.get("kind") == "discussion" and item.get("path") == active_path)
            active_record = {
                "path": active_path,
                "entry": entry,
                "artifact": parsed_artifact_record(decode_fd(artifacts[active_path])),
            }
        tree.verify_linked()
        return {
            "initialized": True,
            "revision": fd_revision(tree.metadata(), [index_snap, current_snap, readme_snap, *artifacts.values()]),
            "active": active_record,
        }
    finally:
        tree.close()


def random_name(base: str, role: str) -> str:
    forced = os.environ.get("TEAMWORK_DISCUSSION_TRANSACTION_TEST_NAME_TOKEN")
    token = forced if forced is not None else secrets.token_hex(12)
    return f".{base}.discussion-{role}-{token}"


def absent_random_name(parent_fd: int, base: str, role: str) -> str:
    for _ in range(32):
        candidate = random_name(base, role)
        if not entry_exists(parent_fd, candidate):
            return candidate
    fail(f"cannot reserve a collision-free {role} name for {base}")


def stage_at(before: FdSnapshot, intended: bytes, faults: Faults) -> FdStaged:
    mode = before.mode if before.exists else 0o644
    assert mode is not None
    name = random_name(before.name, "stage")
    fd: int | None = None
    created = False
    created_info: os.stat_result | None = None
    try:
        faults.hit("STAGE")
        fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, mode, dir_fd=before.parent_fd)
        created = True
        created_info = os.fstat(fd)
        os.fchmod(fd, mode)
        offset = 0
        while offset < len(intended):
            offset += os.write(fd, intended[offset:])
        faults.hit("FSYNC")
        os.fsync(fd)
        info = os.fstat(fd)
        os.close(fd)
        fd = None
        return FdStaged(before, name, intended, mode, True, info.st_dev, info.st_ino)
    except Exception:
        if fd is not None:
            os.close(fd)
        if created:
            try:
                assert created_info is not None
                current = os.stat(name, dir_fd=before.parent_fd, follow_symlinks=False)
                if current.st_dev != created_info.st_dev or current.st_ino != created_info.st_ino:
                    fail("INDETERMINATE: staging temp identity changed before cleanup")
                os.unlink(name, dir_fd=before.parent_fd)
            except FileNotFoundError:
                pass
            except OSError as cleanup:
                fail(f"INDETERMINATE: staging failed and temporary cleanup failed: {cleanup}")
        raise


def entry_exists(parent_fd: int, name: str) -> bool:
    try:
        os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        return True
    except FileNotFoundError:
        return False


def create_marker(tree: FdTree, metadata: dict[str, object]) -> bytes:
    data = (json.dumps(metadata, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()
    fd: int | None = None
    created = False
    identity: tuple[int, int] | None = None
    try:
        fd = os.open(
            MARKER_NAME,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            dir_fd=tree.fds["teamwork"],
        )
        created = True
        os.fchmod(fd, 0o600)
        info = os.fstat(fd)
        identity = (info.st_dev, info.st_ino)
        offset = 0
        while offset < len(data):
            offset += os.write(fd, data[offset:])
        os.fsync(fd)
        os.close(fd)
        fd = None
        os.fsync(tree.fds["teamwork"])
        return data
    except Exception as original:
        if fd is not None:
            os.close(fd)
        if created:
            try:
                current = os.stat(MARKER_NAME, dir_fd=tree.fds["teamwork"], follow_symlinks=False)
                if identity is None or (current.st_dev, current.st_ino) != identity:
                    fail("INDETERMINATE: transaction marker identity changed during creation")
                os.unlink(MARKER_NAME, dir_fd=tree.fds["teamwork"])
                os.fsync(tree.fds["teamwork"])
            except OSError as cleanup:
                fail(f"INDETERMINATE: marker creation failed and cleanup was not durable: {original}; {cleanup}")
        elif isinstance(original, FileExistsError):
            fail("INDETERMINATE: transaction marker appeared concurrently")
        raise


def clear_marker(tree: FdTree, expected: bytes) -> None:
    try:
        tree.verify_linked()
    except TransactionError as exc:
        fail(f"INDETERMINATE: cannot clear marker through changed canonical linkage: {exc}")
    try:
        marker = snapshot_at(tree, "teamwork", MARKER_NAME, f"docs/teamwork/{MARKER_NAME}", required=True)
    except (TransactionError, OSError) as exc:
        fail(f"INDETERMINATE: cannot verify transaction marker before deletion: {exc}")
    if marker.data != expected or marker.mode != 0o600:
        fail("INDETERMINATE: transaction marker changed unexpectedly")
    try:
        os.unlink(MARKER_NAME, dir_fd=tree.fds["teamwork"])
    except OSError as exc:
        fail(f"INDETERMINATE: cannot delete transaction marker: {exc}")
    try:
        os.fsync(tree.fds["teamwork"])
    except OSError as original:
        try:
            fd = os.open(
                MARKER_NAME,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=tree.fds["teamwork"],
            )
            os.fchmod(fd, 0o600)
            offset = 0
            while offset < len(expected):
                offset += os.write(fd, expected[offset:])
            os.fsync(fd)
            os.close(fd)
            os.fsync(tree.fds["teamwork"])
        except OSError as restore:
            fail(f"INDETERMINATE: marker deletion durability failed and marker restore failed: {original}; {restore}")
        fail(f"INDETERMINATE: marker deletion was not durably confirmed: {original}")


def cleanup_stages(staged: list[FdStaged]) -> None:
    errors: list[str] = []
    for item in staged:
        try:
            if item.stage_created and entry_exists(item.before.parent_fd, item.stage_name):
                current = os.stat(item.stage_name, dir_fd=item.before.parent_fd, follow_symlinks=False)
                if (current.st_dev, current.st_ino) != (item.stage_device, item.stage_inode):
                    errors.append(f"{item.before.logical}: stage identity changed")
                    continue
                os.unlink(item.stage_name, dir_fd=item.before.parent_fd)
                item.stage_created = False
        except OSError as exc:
            errors.append(f"{item.before.logical}: {exc}")
    if errors:
        fail(f"INDETERMINATE: temporary cleanup failed: {'; '.join(errors)}")


def verify_prestate(tree: FdTree, staged: list[FdStaged], created_discussion: bool) -> None:
    errors: list[str] = []
    for item in staged:
        try:
            current = snapshot_at(
                tree,
                "discussion" if item.before.logical.startswith("docs/teamwork/discussion/") else "teamwork",
                item.before.name,
                item.before.logical,
                required=item.before.exists,
            )
            if item.before.exists:
                if (current.device, current.inode, current.mode, current.data) != (
                    item.before.device, item.before.inode, item.before.mode, item.before.data,
                ):
                    errors.append(f"{item.before.logical}: mismatch")
            elif current.exists:
                errors.append(f"{item.before.logical}: newly created file remains")
        except TransactionError as exc:
            errors.append(str(exc))
    if created_discussion and "discussion" in tree.fds:
        errors.append("new discussion directory remains")
    if errors:
        fail(f"INDETERMINATE: rollback verification failed: {'; '.join(errors)}")


def rollback_fd(
    tree: FdTree,
    staged: list[FdStaged],
    created_discussion: bool,
    faults: Faults,
) -> None:
    errors: list[str] = []
    modified_parents: dict[int, str] = {}
    for item in reversed(staged):
        fd = item.before.parent_fd
        parent_label = (
            "docs/teamwork/discussion"
            if item.before.logical.startswith("docs/teamwork/discussion/")
            else "docs/teamwork"
        )
        try:
            target_exists = entry_exists(fd, item.before.name)
            if item.backup_created and item.backup_name:
                safe_to_restore = False
                if item.target_installed:
                    if target_exists:
                        current = os.stat(item.before.name, dir_fd=fd, follow_symlinks=False)
                        safe_to_restore = (current.st_dev, current.st_ino) == (
                            item.installed_device,
                            item.installed_inode,
                        )
                else:
                    safe_to_restore = not target_exists
                if not safe_to_restore:
                    errors.append(f"{item.before.logical}: target ownership changed; concurrent file preserved")
                else:
                    os.replace(item.backup_name, item.before.name, src_dir_fd=fd, dst_dir_fd=fd)
                    item.backup_created = False
                    item.target_installed = False
                    modified_parents[fd] = parent_label
            elif not item.before.exists and item.target_installed:
                if not target_exists:
                    errors.append(f"{item.before.logical}: installed target disappeared")
                else:
                    current = os.stat(item.before.name, dir_fd=fd, follow_symlinks=False)
                    if (current.st_dev, current.st_ino) != (item.installed_device, item.installed_inode):
                        errors.append(f"{item.before.logical}: concurrent target preserved")
                    else:
                        os.unlink(item.before.name, dir_fd=fd)
                        item.target_installed = False
                        modified_parents[fd] = parent_label
            if item.stage_created and entry_exists(fd, item.stage_name):
                current = os.stat(item.stage_name, dir_fd=fd, follow_symlinks=False)
                if (current.st_dev, current.st_ino) != (item.stage_device, item.stage_inode):
                    errors.append(f"{item.before.logical}: concurrent stage preserved")
                else:
                    os.unlink(item.stage_name, dir_fd=fd)
                    item.stage_created = False
                    modified_parents[fd] = parent_label
        except OSError as exc:
            errors.append(f"{item.before.logical}: {exc}")
    if not errors:
        try:
            verify_prestate(tree, staged, False)
        except TransactionError as exc:
            errors.append(str(exc))
    if created_discussion and not errors:
        discussion_fd = tree.fds.get("discussion")
        if discussion_fd is not None and discussion_fd in modified_parents:
            try:
                faults.hit("ROLLBACK_FSYNC")
                os.fsync(discussion_fd)
            except OSError as exc:
                errors.append(f"docs/teamwork/discussion: {exc}")
            modified_parents.pop(discussion_fd, None)
        try:
            tree.verify_linked()
            tree.remove_created_discussion()
            modified_parents[tree.fds["teamwork"]] = "docs/teamwork"
        except (OSError, TransactionError) as exc:
            errors.append(f"discussion directory: {exc}")
    try:
        tree.verify_linked()
    except TransactionError as exc:
        errors.append(f"canonical linkage: {exc}")
    for fd, label in sorted(modified_parents.items(), key=lambda item: item[1]):
        try:
            faults.hit("ROLLBACK_FSYNC")
            os.fsync(fd)
        except OSError as exc:
            errors.append(f"{label}: {exc}")
    if errors:
        fail(f"INDETERMINATE: rollback operations failed: {'; '.join(errors)}")
    if os.environ.get("TEAMWORK_DISCUSSION_TRANSACTION_FAIL_ROLLBACK_CONFIRM_N") == "1":
        fail("INDETERMINATE: injected rollback confirmation failure")


def inject_namespace_exchange(tree: FdTree, point: str) -> None:
    requested = os.environ.get("TEAMWORK_DISCUSSION_TRANSACTION_EXCHANGE_AT")
    if requested not in {f"discussion_{point}", f"teamwork_{point}"}:
        return
    key = requested.split("_", 1)[0]
    if key == "discussion":
        parent_fd = tree.fds["teamwork"]
        name = "discussion"
    else:
        parent_fd = tree.fds["docs"]
        name = "teamwork"
    displaced = absent_random_name(parent_fd, name, "exchange")
    os.replace(name, displaced, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
    os.mkdir(name, mode=0o755, dir_fd=parent_fd)


def commit_fd(tree: FdTree, staged: list[FdStaged], faults: Faults, created_discussion: bool) -> None:
    replace_raw = os.environ.get("TEAMWORK_DISCUSSION_TRANSACTION_FAIL_REPLACE_N")
    replace_fail = int(replace_raw) if replace_raw and replace_raw.isdigit() and int(replace_raw) > 0 else None
    if replace_raw is not None and replace_fail is None:
        fail("replace failure injection must be a positive integer")
    replace_count = 0
    concurrent_injected = False
    try:
        tree.verify_linked()
        for item in staged:
            fd = item.before.parent_fd
            if (
                not item.before.exists
                and not concurrent_injected
                and os.environ.get("TEAMWORK_DISCUSSION_TRANSACTION_CONCURRENT_TARGET") == item.before.logical
            ):
                concurrent_fd = os.open(
                    item.before.name,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    0o644,
                    dir_fd=fd,
                )
                os.write(concurrent_fd, b"concurrent-owner\n")
                os.fsync(concurrent_fd)
                os.close(concurrent_fd)
                concurrent_injected = True
            assert_fd_snapshot(tree, item.before)
            stage_now = os.stat(item.stage_name, dir_fd=fd, follow_symlinks=False)
            if (stage_now.st_dev, stage_now.st_ino) != (item.stage_device, item.stage_inode):
                fail(f"{item.before.logical} stage identity changed before install")
            if item.before.exists:
                faults.hit("BACKUP")
                item.backup_name = absent_random_name(fd, item.before.name, "backup")
                replace_count += 1
                if replace_count == replace_fail:
                    raise OSError(f"injected replace failure {replace_count}")
                os.replace(item.before.name, item.backup_name, src_dir_fd=fd, dst_dir_fd=fd)
                item.backup_created = True
                backup = snapshot_at(
                    tree,
                    "discussion" if item.before.logical.startswith("docs/teamwork/discussion/") else "teamwork",
                    item.backup_name,
                    item.before.logical,
                    required=True,
                )
                if (backup.device, backup.inode, backup.mode, backup.data) != (
                    item.before.device, item.before.inode, item.before.mode, item.before.data,
                ):
                    fail(f"{item.before.logical} changed during backup rename")
                if (
                    item.before.logical == "docs/teamwork/index.json"
                    and os.environ.get("TEAMWORK_DISCUSSION_TRANSACTION_INTERRUPT_AFTER_INDEX_BACKUP") == "1"
                ):
                    raise SimulatedInterruption("injected interruption after index backup")
            replace_count += 1
            if replace_count == replace_fail:
                raise OSError(f"injected replace failure {replace_count}")
            os.replace(item.stage_name, item.before.name, src_dir_fd=fd, dst_dir_fd=fd)
            item.stage_created = False
            installed = os.stat(item.before.name, dir_fd=fd, follow_symlinks=False)
            item.target_installed = True
            item.installed_device = installed.st_dev
            item.installed_inode = installed.st_ino
        inject_namespace_exchange(tree, "commit")
        for fd in sorted({item.before.parent_fd for item in staged}):
            faults.hit("FSYNC")
            os.fsync(fd)
    except Exception as original:
        if isinstance(original, SimulatedInterruption):
            raise
        try:
            rollback_fd(tree, staged, created_discussion, faults)
        except TransactionError as rollback:
            fail(f"INDETERMINATE: commit failed ({original}); {rollback}")
        fail(
            f"transaction commit failed and exact prestate was restored: {original}",
            category="ROLLED_BACK",
        )


def verify_intended(tree: FdTree, item: FdStaged) -> FdSnapshot:
    parent = "discussion" if item.before.logical.startswith("docs/teamwork/discussion/") else "teamwork"
    observed = snapshot_at(tree, parent, item.before.name, item.before.logical, required=True)
    if observed.data != item.intended or observed.mode != item.intended_mode:
        fail(f"final exact bytes/mode mismatch: {item.before.logical}")
    return observed


def run(project_root: str, spec_value: object) -> dict[str, object]:
    operation, record, summary, expected_revision, close_status, superseded_by = parse_spec(spec_value)
    faults = Faults()
    tree = FdTree(project_root)
    staged: list[FdStaged] = []
    created_discussion = False
    commit_started = False
    marker_bytes: bytes | None = None
    try:
        if not tree.initialized:
            fail("Teamwork runtime is not initialized")
        index_before = snapshot_at(tree, "teamwork", "index.json", "docs/teamwork/index.json", required=True)
        current_before = snapshot_at(tree, "teamwork", "current.md", "docs/teamwork/current.md", required=True)
        readme_before = snapshot_at(tree, "teamwork", "README.md", "docs/teamwork/README.md", required=True)
        index = parse_index(decode_fd(index_before))
        current = decode_fd(current_before)
        readme = decode_fd(readme_before)
        pre_active = validate_agreement(index, current, readme)
        existing_artifacts = discussion_snapshots(tree, index)
        revision_files = [index_before, current_before, readme_before, *existing_artifacts.values()]
        observed_revision = fd_revision(tree.metadata(), revision_files)
        entries = index["entries"]
        assert isinstance(entries, list)
        active_matches = [
            (position, entry) for position, entry in enumerate(entries)
            if isinstance(entry, dict) and entry.get("kind") == "discussion" and entry.get("path") == pre_active
        ] if pre_active != "none" else []
        if operation == "create":
            if pre_active != "none":
                fail("create requires no active discussion")
        elif len(active_matches) != 1:
            fail(f"{operation} requires exactly one active discussion entry")
        if observed_revision != expected_revision:
            fail("stale expected_revision; inspect again")

        updated = summary["last_updated"]
        old_path = pre_active if pre_active != "none" else None
        old_position = active_matches[0][0] if active_matches else None
        old_entry = active_matches[0][1] if active_matches else None
        old_snapshot = existing_artifacts.get(old_path) if old_path else None
        if operation in {"create", "replace"}:
            slug = record["slug"]
            assert isinstance(slug, str)
            new_path = f"docs/teamwork/discussion/{updated}-{slug}.md"
            if any(isinstance(entry, dict) and entry.get("kind") == "discussion" and entry.get("path") == new_path for entry in entries):
                fail("derived discussion path already has an index entry")
            if new_path == old_path:
                fail("replace must derive a distinct successor path")
        else:
            assert old_path is not None
            new_path = old_path

        if operation == "close":
            assert close_status is not None
            new_status = close_status
            artifact_superseded_by = superseded_by if close_status == "superseded" else "none"
            active_path = None
        else:
            new_status = "active"
            artifact_superseded_by = "none"
            active_path = new_path
        if operation in {"create", "replace"}:
            topic = record["topic"]
            assert isinstance(topic, str)
        else:
            assert isinstance(old_entry, dict) and isinstance(old_entry.get("topic"), str)
            topic = old_entry["topic"]
        prior_supersedes = []
        if isinstance(old_entry, dict) and isinstance(old_entry.get("supersedes"), list):
            prior_supersedes = list(old_entry["supersedes"])
        entry_supersedes = [old_path] if operation == "replace" and old_path else prior_supersedes
        final_entry = canonical_entry_from_record(
            record,
            topic=topic,
            path=new_path,
            status=new_status,
            updated=updated,
            supersedes=entry_supersedes,
        )
        artifact_text = render_artifact(
            record,
            status=new_status,
            updated=updated,
            superseded_by=artifact_superseded_by or "none",
        )
        validate_artifact(
            artifact_text,
            operation="update" if new_status == "active" else "close",
            entry=final_entry,
        )

        proposed = json.loads(json.dumps(index))
        proposed["last_updated"] = updated
        proposed_active = proposed["active"]
        proposed_entries = proposed["entries"]
        assert isinstance(proposed_active, dict) and isinstance(proposed_entries, list)
        proposed_active["discussion"] = active_path
        if operation == "create":
            proposed_entries.append(final_entry)
        elif operation == "replace":
            assert old_position is not None and isinstance(old_entry, dict) and old_path is not None and old_snapshot is not None
            superseded_entry = dict(old_entry)
            superseded_entry.update(
                status="superseded",
                currentness="historical",
                authority="superseded",
                updated=updated,
            )
            proposed_entries[old_position] = superseded_entry
            proposed_entries.append(final_entry)
        else:
            assert old_position is not None
            proposed_entries[old_position] = final_entry
        validate_index_structure(proposed)
        validate_discussion_entries(proposed)
        new_current = updated_current(current, summary, active_path)
        new_readme = updated_readme(readme, active_path)
        validate_agreement(proposed, new_current, new_readme)
        new_index = (json.dumps(proposed, indent=2, ensure_ascii=False) + "\n").encode()
        tree.verify_linked()
        for snap in revision_files:
            assert_fd_snapshot(tree, snap)
        planned_artifacts: list[tuple[str, bytes, dict[str, object], str, FdSnapshot | None]] = []
        if operation == "replace":
            assert old_snapshot is not None and old_path is not None and isinstance(old_entry, dict)
            old_text = rewrite_replaced_artifact(decode_fd(old_snapshot), new_path=new_path, updated=updated)
            superseded_entry = proposed_entries[old_position]  # type: ignore[index]
            assert isinstance(superseded_entry, dict)
            validate_artifact(old_text, operation="close", entry=superseded_entry)
            planned_artifacts.append((old_path, old_text.encode(), superseded_entry, "close", old_snapshot))
        planned_artifacts.append(
            (
                new_path,
                artifact_text.encode(),
                final_entry,
                "update" if new_status == "active" else "close",
                existing_artifacts.get(new_path),
            )
        )
        intended_hashes = {
            **{path: hashlib.sha256(data).hexdigest() for path, data, _, _, _ in planned_artifacts},
            "docs/teamwork/current.md": hashlib.sha256(new_current.encode()).hexdigest(),
            "docs/teamwork/README.md": hashlib.sha256(new_readme.encode()).hexdigest(),
            "docs/teamwork/index.json": hashlib.sha256(new_index).hexdigest(),
        }
        marker_bytes = create_marker(
            tree,
            {
                "schema_version": 1,
                "operation": operation,
                "expected_revision": expected_revision,
                "outputs": intended_hashes,
            },
        )
        if "discussion" not in tree.fds:
            created_discussion = tree.ensure_discussion()
        artifact_outputs: list[tuple[FdSnapshot, bytes, dict[str, object], str]] = []
        for path, intended, expected_entry, validation_operation, before in planned_artifacts:
            if before is None:
                before = snapshot_at(
                    tree,
                    "discussion",
                    PurePosixPath(path).name,
                    path,
                    required=operation in {"update", "close"},
                )
            if operation in {"create", "replace"} and path == new_path and before.exists:
                fail("derived discussion artifact path already exists")
            artifact_outputs.append((before, intended, expected_entry, validation_operation))
        for before, intended, _, _ in artifact_outputs:
            staged.append(stage_at(before, intended, faults))
        staged.append(stage_at(current_before, new_current.encode(), faults))
        staged.append(stage_at(readme_before, new_readme.encode(), faults))
        staged.append(stage_at(index_before, new_index, faults))
        commit_started = True
        commit_fd(tree, staged, faults, created_discussion)

        try:
            final = [verify_intended(tree, item) for item in staged]
            final_by_path = {item.logical: item for item in final}
            final_index_snap = final_by_path["docs/teamwork/index.json"]
            final_current_snap = final_by_path["docs/teamwork/current.md"]
            final_readme_snap = final_by_path["docs/teamwork/README.md"]
            final_index = parse_index(decode_fd(final_index_snap))
            if final_index != proposed or final_index_snap.data != new_index:
                fail("final index differs from the exact proposed object/bytes")
            if decode_fd(final_current_snap) != new_current or decode_fd(final_readme_snap) != new_readme:
                fail("final anchor bytes differ from the intended output")
            validate_agreement(final_index, decode_fd(final_current_snap), decode_fd(final_readme_snap))
            for before, _, expected_entry, validation_operation in artifact_outputs:
                validate_artifact(
                    decode_fd(final_by_path[before.logical]),
                    operation=validation_operation,
                    entry=expected_entry,
                )
            inject_namespace_exchange(tree, "readback")
            tree.verify_linked()
            final_artifacts = discussion_snapshots(tree, final_index)
            next_revision = fd_revision(
                tree.metadata(),
                [final_index_snap, final_current_snap, final_readme_snap, *final_artifacts.values()],
            )
            faults.hit("POST_READBACK")
        except Exception as original:
            try:
                rollback_fd(tree, staged, created_discussion, faults)
            except TransactionError as rollback:
                fail(f"INDETERMINATE: post-readback failed ({original}); {rollback}")
            fail(
                f"post-readback validation failed and exact prestate was restored: {original}",
                category="ROLLED_BACK",
            )

        try:
            for item in staged:
                if item.backup_created and item.backup_name:
                    faults.hit("CLEANUP")
            for item in staged:
                if item.backup_created and item.backup_name:
                    backup = os.stat(item.backup_name, dir_fd=item.before.parent_fd, follow_symlinks=False)
                    if (backup.st_dev, backup.st_ino) != (item.before.device, item.before.inode):
                        fail("INDETERMINATE: backup identity changed before cleanup")
                    os.unlink(item.backup_name, dir_fd=item.before.parent_fd)
                    item.backup_created = False
            for fd in sorted({item.before.parent_fd for item in staged}):
                os.fsync(fd)
        except Exception as original:
            try:
                rollback_fd(tree, staged, created_discussion, faults)
            except TransactionError as rollback:
                fail(f"INDETERMINATE: backup cleanup failed ({original}); {rollback}")
            fail(
                f"backup cleanup failed and exact prestate was restored: {original}",
                category="ROLLED_BACK",
            )

        assert marker_bytes is not None
        clear_marker(tree, marker_bytes)
        marker_bytes = None

        changed_paths = [
            *(before.logical for before, _, _, _ in artifact_outputs),
            "docs/teamwork/current.md",
            "docs/teamwork/README.md",
            "docs/teamwork/index.json",
        ]
        return {
            "operation": operation,
            "path": new_path,
            "revision": next_revision,
            "changed_paths": changed_paths,
        }
    except Exception as original:
        if isinstance(original, SimulatedInterruption):
            raise
        if not commit_started:
            try:
                tree.verify_linked()
            except TransactionError as exc:
                fail(f"INDETERMINATE: precommit cleanup lost canonical linkage: {exc}")
            if staged:
                cleanup_stages(staged)
            if created_discussion and "discussion" in tree.fds:
                try:
                    tree.verify_linked()
                    tree.remove_created_discussion()
                except (OSError, TransactionError) as exc:
                    fail(f"INDETERMINATE: could not remove created discussion directory: {exc}")
            if marker_bytes is not None:
                clear_marker(tree, marker_bytes)
                marker_bytes = None
        elif isinstance(original, TransactionError) and original.category == "ROLLED_BACK":
            if marker_bytes is None:
                fail("INDETERMINATE: verified rollback lost its transaction marker")
            clear_marker(tree, marker_bytes)
            marker_bytes = None
        raise
    finally:
        tree.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    schema_parser = subparsers.add_parser("schema", help="print a lifecycle request template")
    schema_parser.add_argument("lifecycle", choices=("create", "update", "close", "supersede", "replace"))
    inspect_parser = subparsers.add_parser("inspect", help="safely inspect current discussion state")
    inspect_parser.add_argument("--project-root", default=".")
    guard_parser = subparsers.add_parser("guard", help="run one command under the Teamwork directory lock")
    guard_parser.add_argument("--project-root", default=".")
    guard_parser.add_argument("--allow-init-recovery", action="store_true", help=argparse.SUPPRESS)
    guard_parser.add_argument("guard_argv", nargs=argparse.REMAINDER)
    apply_parser = subparsers.add_parser("apply", help="apply one revision-checked transaction")
    apply_parser.add_argument("--project-root", default=".")
    request_source = apply_parser.add_mutually_exclusive_group(required=True)
    request_source.add_argument("--request", help="JSON request file; stdin sentinel - is not supported")
    request_source.add_argument("--request-json", help="inline JSON request")
    arguments = parser.parse_args()
    try:
        if arguments.command == "schema":
            print(
                json.dumps(
                    schema_template(arguments.lifecycle),
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
            )
            return 0
        if arguments.command == "inspect":
            result = inspect_project(arguments.project_root)
        elif arguments.command == "guard":
            command = list(arguments.guard_argv)
            if command[:1] == ["--"]:
                command = command[1:]
            return guard_command(
                arguments.project_root,
                command,
                allow_init_recovery=arguments.allow_init_recovery,
            )
        else:
            if arguments.request_json is not None:
                spec_value = read_inline_spec(arguments.request_json)
            else:
                assert arguments.request is not None
                spec_value = read_spec(arguments.request)
            result = run(arguments.project_root, spec_value)
    except TransactionError as exc:
        print(
            json.dumps(
                {"ok": False, "category": exc.category, "message": str(exc)},
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1
    except OSError as exc:
        print(
            json.dumps(
                {"ok": False, "category": "PREWRITE_SAFE", "message": str(exc)},
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1
    except Exception as exc:
        print(
            json.dumps(
                {"ok": False, "category": "INDETERMINATE", "message": str(exc)},
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
