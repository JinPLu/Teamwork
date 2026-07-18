#!/usr/bin/env python3
"""Read and migrate the Teamwork-owned Codex subagent routing contract."""

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


ROUTING_NAMESPACE = "teamwork"
ROUTING_TABLE = "features.multi_agent_v2"
TOTAL_THREAD_LIMIT = 9
DESIRED_VALUES: dict[str, Any] = {
    "enabled": True,
    "hide_spawn_agent_metadata": False,
    "tool_namespace": ROUTING_NAMESPACE,
    "max_concurrent_threads_per_session": TOTAL_THREAD_LIMIT,
}

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
    routing = features.get("multi_agent_v2")
    if not isinstance(routing, dict):
        issues.append("features.multi_agent_v2 must be a table")
    else:
        for key, expected in DESIRED_VALUES.items():
            if routing.get(key) != expected:
                issues.append(f"{ROUTING_TABLE}.{key} must be {expected!r}")

    agents = data.get("agents", {})
    if agents is not None and not isinstance(agents, dict):
        issues.append("agents must be a TOML table")
    elif isinstance(agents, dict) and "max_threads" in agents:
        issues.append("agents.max_threads conflicts with multi_agent_v2")
    return issues


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
        status="ready" if not issues else "drift",
        config_path=str(resolved),
        ready=not issues,
        issues=issues,
    )


def _resolved_write_path(path: pathlib.Path) -> pathlib.Path:
    expanded = path.expanduser()
    if expanded.is_symlink():
        return expanded.resolve(strict=False)
    return expanded


def _section_names(lines: list[str]) -> list[str]:
    names: list[str] = []
    for line in lines:
        match = TABLE_RE.match(line)
        if match:
            names.append(match.group(1).strip())
    return names


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


def _validate_supported_layout(
    data: dict[str, Any], lines: list[str], path: pathlib.Path
) -> None:
    sections = _section_names(lines)
    if any(name.startswith(f"{ROUTING_TABLE}.") for name in sections) and ROUTING_TABLE not in sections:
        raise RoutingConfigError(
            f"cannot safely add [{ROUTING_TABLE}] after an existing child table in {path}"
        )

    features = data.get("features", {})
    if not isinstance(features, dict):
        raise RoutingConfigError(f"[features] is not a table in {path}")
    routing = features.get("multi_agent_v2")
    if isinstance(routing, dict) and ROUTING_TABLE not in sections:
        raise RoutingConfigError(
            f"{ROUTING_TABLE} uses an inline or dotted layout that Teamwork will not rewrite"
        )
    if routing is not None and not isinstance(routing, (bool, dict)):
        raise RoutingConfigError(
            f"features.multi_agent_v2 must be a boolean or table in {path}"
        )

    agents = data.get("agents", {})
    if agents is not None and not isinstance(agents, dict):
        raise RoutingConfigError(f"[agents] is not a table in {path}")
    if isinstance(agents, dict) and "max_threads" in agents:
        value = agents["max_threads"]
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise RoutingConfigError("agents.max_threads must be a positive integer")
        if "agents" not in sections:
            raise RoutingConfigError(
                "agents.max_threads uses a dotted or inline layout that Teamwork will not rewrite"
            )


def migrate_text(text: str, path: pathlib.Path) -> tuple[str, list[str]]:
    data = _parse_toml(text, path)
    lines = text.splitlines(keepends=True)
    _validate_supported_layout(data, lines, path)
    newline = _newline_for(text)
    changes: list[str] = []

    features = data.get("features", {})
    routing = features.get("multi_agent_v2") if isinstance(features, dict) else None
    desired = dict(DESIRED_VALUES)

    section = ""
    table_found = False
    seen_desired: set[str] = set()
    transformed: list[str] = []
    for line in lines:
        table_match = TABLE_RE.match(line)
        if table_match:
            section = table_match.group(1).strip()
            table_found = table_found or section == ROUTING_TABLE
            transformed.append(line)
            continue

        key = _line_key(line)
        if section == "features" and key == "multi_agent_v2":
            if not isinstance(routing, bool):
                raise RoutingConfigError(
                    "features.multi_agent_v2 assignment is not a scalar boolean"
                )
            changes.append("replace scalar features.multi_agent_v2 with a table")
            continue
        if section == "" and key == "features.multi_agent_v2":
            if not isinstance(routing, bool):
                raise RoutingConfigError(
                    "features.multi_agent_v2 dotted assignment is not a scalar boolean"
                )
            changes.append("replace dotted features.multi_agent_v2 with a table")
            continue
        if section == "agents" and key == "max_threads":
            changes.append("remove incompatible agents.max_threads")
            continue
        if section == ROUTING_TABLE and key in desired:
            seen_desired.add(key)
            replacement = _replace_assignment(line, key, desired[key], newline)
            if replacement != line:
                changes.append(f"set {ROUTING_TABLE}.{key}")
            transformed.append(replacement)
            continue
        transformed.append(line)

    if table_found:
        missing = [key for key in desired if key not in seen_desired]
        if missing:
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
            additions = [f"{key} = {_toml_literal(desired[key])}{newline}" for key in missing]
            transformed[insert_at:insert_at] = additions
            changes.extend(f"add {ROUTING_TABLE}.{key}" for key in missing)
    else:
        if transformed and transformed[-1] and not transformed[-1].endswith(("\n", "\r")):
            transformed[-1] += newline
        if transformed and any(line.strip() for line in transformed):
            if transformed[-1].strip():
                transformed.append(newline)
        transformed.append(f"[{ROUTING_TABLE}]{newline}")
        for key, value in desired.items():
            transformed.append(f"{key} = {_toml_literal(value)}{newline}")
        changes.append(f"add [{ROUTING_TABLE}] routing table")

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
        return RoutingReport(
            status="current",
            config_path=str(resolved),
            ready=True,
        )
    try:
        _atomic_write(resolved, candidate)
    except OSError as exc:
        raise RoutingConfigError(f"could not update {resolved}: {exc}") from exc
    return RoutingReport(
        status="updated",
        config_path=str(resolved),
        ready=True,
        changes=changes,
        restart_required=True,
    )


def preview_config(path: pathlib.Path) -> RoutingReport:
    """Validate the exact routing migration without writing user configuration."""
    resolved = _resolved_write_path(path)
    text, _ = _read_config(resolved)
    candidate, changes = migrate_text(text, resolved)
    return RoutingReport(
        status="current" if candidate == text else "would-update",
        config_path=str(resolved),
        ready=True,
        changes=changes,
        restart_required=candidate != text,
    )


def print_report(report: RoutingReport, as_json: bool = False) -> None:
    if as_json:
        print(report.to_json())
        return
    print(f"CODEX_ROUTING={report.status}")
    print(f"CONFIG={report.config_path}")
    print(f"READY={'yes' if report.ready else 'no'}")
    print(f"RESTART_REQUIRED={'yes' if report.restart_required else 'no'}")
    if report.issues:
        print("ISSUES=" + "; ".join(report.issues))
    if report.changes:
        print("CHANGES=" + "; ".join(report.changes))
