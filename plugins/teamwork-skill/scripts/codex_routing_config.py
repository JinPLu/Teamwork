#!/usr/bin/env python3
"""Read and migrate Teamwork's static Codex subagent configuration."""

from __future__ import annotations

import json
import os
import pathlib
import re
import tempfile
from dataclasses import asdict, dataclass, field
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - depends on the host Python.
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError:  # pragma: no cover - reported at runtime.
        tomllib = None  # type: ignore[assignment]


ROUTING_TABLE = "features"
ROUTING_KEY = "multi_agent"
ROUTING_NAME = f"{ROUTING_TABLE}.{ROUTING_KEY}"
DESIRED_VALUE = True

TABLE_RE = re.compile(r"^\s*\[([^\[\]]+)\]\s*(?:#.*)?(?:\r?\n)?$")
KEY_RE = re.compile(r"^(?P<indent>\s*)(?P<key>[A-Za-z0-9_.-]+)\s*=.*$")


class RoutingConfigError(RuntimeError):
    """Raised when a config cannot be inspected or migrated safely."""


@dataclass
class RoutingReport:
    status: str
    config_path: str
    ready: bool
    issues: list[str] = field(default_factory=list)
    changes: list[str] = field(default_factory=list)
    restart_required: bool = False
    experimental_multi_agent_v2: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


def _toml_loader() -> Any:
    if tomllib is None:
        raise RoutingConfigError(
            "Python 3.11+ or the 'tomli' package is required to preserve and validate config.toml"
        )
    return tomllib


def _read_config(path: pathlib.Path) -> tuple[str, dict[str, Any]]:
    if not path.exists():
        return "", {}
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RoutingConfigError(f"could not read {path}: {exc}") from exc
    return text, _parse_toml(text, path)


def _parse_toml(text: str, path: pathlib.Path) -> dict[str, Any]:
    loader = _toml_loader()
    try:
        data = loader.loads(text)
    except (ValueError, TypeError) as exc:
        raise RoutingConfigError(f"invalid TOML in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise RoutingConfigError(f"invalid TOML document in {path}")
    return data


def _routing_issues(data: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    features = data.get("features", {})
    if not isinstance(features, dict):
        return ["features must be a TOML table"]
    routing = features.get(ROUTING_KEY, DESIRED_VALUE)
    if routing is not DESIRED_VALUE:
        issues.append(f"{ROUTING_NAME} must be true or omitted")
    agents = data.get("agents", {})
    if agents is not None and not isinstance(agents, dict):
        issues.append("agents must be a TOML table")
    return issues


def _experimental_v2_status(data: dict[str, Any]) -> str:
    features = data.get("features", {})
    return (
        "present-unmanaged"
        if isinstance(features, dict) and "multi_agent_v2" in features
        else "absent"
    )


def inspect_config(path: pathlib.Path) -> RoutingReport:
    resolved = _resolved_write_path(path)
    if not resolved.exists():
        return RoutingReport(
            status="missing",
            config_path=str(resolved),
            ready=False,
            issues=["config.toml is missing"],
        )
    _, data = _read_config(resolved)
    issues = _routing_issues(data)
    return RoutingReport(
        status="configured" if not issues else "drift",
        config_path=str(resolved),
        ready=not issues,
        issues=issues,
        experimental_multi_agent_v2=_experimental_v2_status(data),
    )


def _resolved_write_path(path: pathlib.Path) -> pathlib.Path:
    expanded = path.expanduser()
    if expanded.is_symlink():
        return expanded.resolve(strict=False)
    return expanded


def _line_key(line: str) -> str | None:
    stripped = line.lstrip()
    if not stripped or stripped.startswith("#") or stripped.startswith("["):
        return None
    match = KEY_RE.match(line.rstrip("\r\n"))
    return match.group("key") if match else None


def _newline_for(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def _toml_literal(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    raise RoutingConfigError(f"unsupported routing value: {value!r}")


def _replace_assignment(line: str, key: str, value: Any, newline: str) -> str:
    body = line.rstrip("\r\n")
    match = KEY_RE.match(body)
    indent = match.group("indent") if match else ""
    comment_match = re.search(r"\s+(#.*)$", body)
    comment = f" {comment_match.group(1)}" if comment_match else ""
    return f"{indent}{key} = {_toml_literal(value)}{comment}{newline}"


def _validate_supported_layout(data: dict[str, Any], path: pathlib.Path) -> None:
    features = data.get("features", {})
    if not isinstance(features, dict):
        raise RoutingConfigError(f"[features] is not a table in {path}")
    routing = features.get(ROUTING_KEY)
    if routing is not None and not isinstance(routing, bool):
        raise RoutingConfigError(f"{ROUTING_NAME} must be a boolean in {path}")

    agents = data.get("agents", {})
    if agents is not None and not isinstance(agents, dict):
        raise RoutingConfigError(f"[agents] is not a table in {path}")


def migrate_text(text: str, path: pathlib.Path) -> tuple[str, list[str]]:
    data = _parse_toml(text, path)
    lines = text.splitlines(keepends=True)
    _validate_supported_layout(data, path)
    newline = _newline_for(text)
    changes: list[str] = []

    section = ""
    features_table_found = False
    features_child_table_index: int | None = None
    features_dotted_key_found = False
    seen_desired = False
    transformed: list[str] = []
    for line in lines:
        table_match = TABLE_RE.match(line)
        if table_match:
            section = table_match.group(1).strip()
            features_table_found = features_table_found or section == ROUTING_TABLE
            if (
                features_child_table_index is None
                and section.startswith(f"{ROUTING_TABLE}.")
            ):
                features_child_table_index = len(transformed)
            transformed.append(line)
            continue

        key = _line_key(line)
        if section == "" and key is not None and key.startswith(f"{ROUTING_TABLE}."):
            features_dotted_key_found = True
        if section == ROUTING_TABLE and key == ROUTING_KEY:
            seen_desired = True
            replacement = _replace_assignment(line, ROUTING_KEY, DESIRED_VALUE, newline)
            if replacement != line:
                changes.append(f"set {ROUTING_NAME}")
            transformed.append(replacement)
            continue
        if section == "" and key == ROUTING_NAME:
            seen_desired = True
            replacement = _replace_assignment(line, ROUTING_NAME, DESIRED_VALUE, newline)
            if replacement != line:
                changes.append(f"set {ROUTING_NAME}")
            transformed.append(replacement)
            continue
        transformed.append(line)

    if seen_desired:
        pass
    elif features_table_found:
        section_start = next(
            index
            for index, line in enumerate(transformed)
            if (match := TABLE_RE.match(line))
            and match.group(1).strip() == ROUTING_TABLE
        )
        insert_at = len(transformed)
        for index in range(section_start + 1, len(transformed)):
            if TABLE_RE.match(transformed[index]):
                insert_at = index
                break
        transformed.insert(insert_at, f"{ROUTING_KEY} = {_toml_literal(DESIRED_VALUE)}{newline}")
        changes.append(f"add {ROUTING_NAME}")
    elif features_child_table_index is not None:
        transformed[features_child_table_index:features_child_table_index] = [
            f"[{ROUTING_TABLE}]{newline}",
            f"{ROUTING_KEY} = {_toml_literal(DESIRED_VALUE)}{newline}",
        ]
        changes.append(f"add {ROUTING_NAME}")
    elif features_dotted_key_found:
        insert_at = next(
            (index for index, line in enumerate(transformed) if TABLE_RE.match(line)),
            len(transformed),
        )
        transformed.insert(
            insert_at,
            f"{ROUTING_NAME} = {_toml_literal(DESIRED_VALUE)}{newline}",
        )
        changes.append(f"add {ROUTING_NAME}")
    else:
        if transformed and transformed[-1] and not transformed[-1].endswith(("\n", "\r")):
            transformed[-1] += newline
        if transformed and any(line.strip() for line in transformed):
            if transformed[-1].strip():
                transformed.append(newline)
        transformed.append(f"[{ROUTING_TABLE}]{newline}")
        transformed.append(f"{ROUTING_KEY} = {_toml_literal(DESIRED_VALUE)}{newline}")
        changes.append(f"add {ROUTING_NAME}")

    candidate = "".join(transformed)
    candidate_data = _parse_toml(candidate, path)
    issues = _routing_issues(candidate_data)
    if issues:
        raise RoutingConfigError(
            "migrated config did not satisfy routing contract: " + "; ".join(issues)
        )
    return candidate, changes


def _atomic_write(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = (path.stat().st_mode & 0o777) if path.exists() else 0o600
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.teamwork-", dir=path.parent)
    temporary_path = pathlib.Path(temporary)
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def apply_config(path: pathlib.Path) -> RoutingReport:
    resolved = _resolved_write_path(path)
    text, _ = _read_config(resolved)
    candidate, changes = migrate_text(text, resolved)
    if candidate == text:
        candidate_data = _parse_toml(candidate, resolved)
        return RoutingReport(
            status="current",
            config_path=str(resolved),
            ready=True,
            experimental_multi_agent_v2=_experimental_v2_status(candidate_data),
        )
    try:
        _atomic_write(resolved, candidate)
    except OSError as exc:
        raise RoutingConfigError(f"could not update {resolved}: {exc}") from exc
    candidate_data = _parse_toml(candidate, resolved)
    return RoutingReport(
        status="updated",
        config_path=str(resolved),
        ready=True,
        changes=changes,
        restart_required=True,
        experimental_multi_agent_v2=_experimental_v2_status(candidate_data),
    )


def preview_config(path: pathlib.Path) -> RoutingReport:
    """Validate the exact routing migration without writing user configuration."""
    resolved = _resolved_write_path(path)
    text, _ = _read_config(resolved)
    candidate, changes = migrate_text(text, resolved)
    candidate_data = _parse_toml(candidate, resolved)
    return RoutingReport(
        status="current" if candidate == text else "would-update",
        config_path=str(resolved),
        ready=True,
        changes=changes,
        restart_required=candidate != text,
        experimental_multi_agent_v2=_experimental_v2_status(candidate_data),
    )


def print_report(report: RoutingReport, as_json: bool = False) -> None:
    if as_json:
        print(report.to_json())
        return
    print(f"CODEX_ROUTING={report.status}")
    print(f"CONFIG={report.config_path}")
    print(f"STATIC_CONFIGURED={'yes' if report.ready else 'no'}")
    print("EXACT_ROLE_ACTIVATION=live-probe-required")
    print(f"EXPERIMENTAL_MULTI_AGENT_V2={report.experimental_multi_agent_v2}")
    print(f"RESTART_REQUIRED={'yes' if report.restart_required else 'no'}")
    if report.issues:
        print("ISSUES=" + "; ".join(report.issues))
    if report.changes:
        print("CHANGES=" + "; ".join(report.changes))
