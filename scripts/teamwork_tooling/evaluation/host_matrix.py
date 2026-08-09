"""Run change-scoped Teamwork scenarios through installed host CLIs.

Records contain observed host output and verifier outcomes. They do not seal,
fingerprint, or infer semantic acceptance from source text.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import stat
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Sequence


SCHEMA_VERSION = 2
STATUSES = {"PASS", "FAIL", "UNSUPPORTED"}
PROFILES = {"performance-first", "cost-first"}
HOSTS = {"codex", "cursor", "claude"}
SUPPORT_EXPECTATIONS = {"required", "conditional-exact-role"}
RELEASE_CASE_PATH = "evals/teamwork/live-cases/release-matrix.json"
RELEASE_SCHEMA_PATH = "evals/teamwork/schemas/host-trajectory.schema.json"
RELEASE_TEMP_ROOT = Path("/tmp/teamwork-release-matrix")
CURSOR_AUTH_REQUIRED = (
    "Error: Authentication required. Please run 'agent login' first, "
    "or set CURSOR_API_KEY environment variable."
)
SKILL_READ_RE = re.compile(r"(?:^|[\s'\"]|/)(?:\.agents/)?skills/([A-Za-z0-9][A-Za-z0-9_-]*)/SKILL\.md")
CHILD_START_EVENT_TYPES = {
    "subagent.start", "subagent.started", "SubagentStart", "agent.started",
}
CANONICAL_AGENTS = {
    "researcher", "explorer", "debugger", "challenger", "planner", "reviewer", "worker", "writer",
}


class HostMatrixError(ValueError):
    """Raised when a host scenario or observation is invalid."""


class HostProbeError(HostMatrixError):
    """Raised when the host executable or its version cannot be observed."""

    def __init__(self, classification: str):
        super().__init__(classification)
        self.classification = classification


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def safe_relative(value: Any, label: str = "path") -> str:
    if not isinstance(value, str) or not value:
        raise HostMatrixError(f"{label} must be non-empty text")
    path = PurePosixPath(value)
    if path.is_absolute() or "\\" in value or any(part in {"", ".", ".."} for part in path.parts):
        raise HostMatrixError(f"{label} must be a normalized relative path")
    return path.as_posix()


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HostMatrixError(f"cannot read {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise HostMatrixError(f"{label} must be an object")
    return value


def validate_candidate(project_root: Path, _manifest_path: Path | None = None) -> dict[str, Any]:
    """Validate the ordinary current source layout used by the host runner."""

    root = project_root.resolve()
    required = (
        "install.sh",
        "policy/teamwork-global.md",
        "config/teamwork-topology.json",
        "scripts/teamwork_index_v4.py",
        "templates/teamwork-memory/index.json",
    )
    missing = [relative for relative in required if not (root / relative).is_file()]
    if missing:
        raise HostMatrixError(f"candidate source layout is incomplete: {missing}")
    return {"root": str(root), "surfaces": list(required)}


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise HostMatrixError(f"{label} must be non-empty text")
    return value


def load_case_manifest(
    path: Path, only_cases: set[str] | None = None, *, root: Path | None = None,
) -> list[dict[str, Any]]:
    value = load_json(path, "live case manifest")
    if value.get("schema_version") != 3 or not isinstance(value.get("cases"), list):
        raise HostMatrixError("live case manifest must use schema_version 3")
    candidate_root = (root or path.resolve().parents[3]).resolve()
    cases: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in value["cases"]:
        required = {
            "name", "prompt", "selected_skill", "required_agents",
            "expected_outcomes", "scenario", "authority", "support",
        }
        if not isinstance(raw, dict) or set(raw) != required:
            raise HostMatrixError("live case has an invalid shape")
        name = _text(raw.get("name"), "case name")
        if name in seen:
            raise HostMatrixError("live case names must be unique")
        seen.add(name)
        outcomes = raw.get("expected_outcomes")
        if not isinstance(outcomes, list) or not outcomes or not all(isinstance(item, str) and item.strip() for item in outcomes):
            raise HostMatrixError(f"{name}: expected_outcomes must contain outcome text")
        required_agents = raw.get("required_agents")
        if (
            not isinstance(required_agents, list)
            or len(required_agents) != len(set(required_agents))
            or not all(isinstance(item, str) and item in CANONICAL_AGENTS for item in required_agents)
        ):
            raise HostMatrixError(f"{name}: required_agents must be unique canonical Agent names")
        scenario = raw.get("scenario")
        if scenario is not None:
            relative = safe_relative(scenario, f"{name}.scenario")
            scenario_path = candidate_root / relative
            if not scenario_path.is_file():
                raise HostMatrixError(f"{name}: scenario is missing")
            scenario_spec = load_json(scenario_path, f"{name} scenario")
            verification = scenario_spec.get("verification")
            if (
                not isinstance(verification, dict)
                or not isinstance(verification.get("argv"), list)
                or not verification["argv"]
            ):
                raise HostMatrixError(f"{name}: scenario must declare verification argv")
        _text(raw.get("selected_skill"), f"{name}.selected_skill")
        _text(raw.get("prompt"), f"{name}.prompt")
        if raw.get("authority") not in {"read-only", "workspace-write"}:
            raise HostMatrixError(f"{name}: authority is invalid")
        support = raw.get("support")
        if (
            not isinstance(support, dict)
            or set(support) != HOSTS
            or any(value not in SUPPORT_EXPECTATIONS for value in support.values())
        ):
            raise HostMatrixError(
                f"{name}: support must declare every host as required or conditional-exact-role"
            )
        if not required_agents and "conditional-exact-role" in support.values():
            raise HostMatrixError(
                f"{name}: an Agent-free case cannot declare conditional exact-role support"
            )
        if only_cases is None or name in only_cases:
            cases.append(dict(raw))
    if only_cases is not None and {case["name"] for case in cases} != only_cases:
        raise HostMatrixError("requested live case is not declared")
    if not cases:
        raise HostMatrixError("no live cases selected")
    return cases


def load_trajectory_schema(path: Path) -> dict[str, Any]:
    value = load_json(path, "trajectory schema")
    if value.get("type") != "object":
        raise HostMatrixError("trajectory schema must describe an object")
    return value


def validate_trajectory(record: dict[str, Any], _schema: dict[str, Any] | None = None) -> None:
    required = {
        "schema_version", "record_type", "host", "host_executable", "host_version", "profile",
        "case_name", "started_at", "finished_at", "selected_skill", "requested_authority",
        "route_observed", "agent_observations", "tool_observations", "final_output", "scenario_verification",
        "candidate_artifact", "exit_status", "status", "failure_classification",
    }
    if _schema:
        schema_required = _schema.get("required")
        if not isinstance(schema_required, list) or set(schema_required) != required:
            raise HostMatrixError("trajectory schema and runtime contract differ")
    if set(record) != required:
        raise HostMatrixError("trajectory record has an invalid shape")
    if record.get("schema_version") != SCHEMA_VERSION or record.get("record_type") != "teamwork_host_observation":
        raise HostMatrixError("trajectory record has an unsupported schema")
    if record.get("host") not in HOSTS or record.get("profile") not in PROFILES:
        raise HostMatrixError("trajectory host or profile is invalid")
    if record.get("status") not in STATUSES:
        raise HostMatrixError("trajectory status is invalid")
    if record.get("requested_authority") not in {"read-only", "workspace-write"}:
        raise HostMatrixError("trajectory requested authority is invalid")
    for field in ("host_version", "case_name", "started_at", "finished_at", "selected_skill", "final_output"):
        if not isinstance(record.get(field), str):
            raise HostMatrixError(f"trajectory {field} must be text")
    executable = record.get("host_executable")
    if executable is not None and (
        not isinstance(executable, str) or not executable or not Path(executable).is_absolute()
    ):
        raise HostMatrixError("trajectory host_executable must be an absolute path or null")
    if record.get("candidate_artifact") is not None and not isinstance(record.get("candidate_artifact"), str):
        raise HostMatrixError("trajectory candidate_artifact must be text or null")
    if record.get("scenario_verification") not in {"PASS", "FAIL", "NOT_RUN"}:
        raise HostMatrixError("trajectory scenario verification is invalid")
    if record.get("exit_status") is not None and not isinstance(record.get("exit_status"), int):
        raise HostMatrixError("trajectory exit status must be integer or null")
    if not isinstance(record.get("route_observed"), bool):
        raise HostMatrixError("trajectory route_observed must be boolean")
    for field in ("agent_observations", "tool_observations"):
        values = record.get(field)
        if not isinstance(values, list) or not all(isinstance(item, str) for item in values):
            raise HostMatrixError(f"trajectory {field} must be a text list")
    if record.get("status") == "PASS":
        if not isinstance(executable, str) or not executable:
            raise HostMatrixError("PASS trajectory must retain its resolved host executable")
        if not record.get("route_observed"):
            raise HostMatrixError("PASS trajectory must observe its selected route")
        if record.get("exit_status") != 0:
            raise HostMatrixError("PASS trajectory must have exit status 0")
        if record.get("scenario_verification") == "FAIL":
            raise HostMatrixError("PASS trajectory cannot have failed scenario verification")
        if not str(record.get("final_output", "")).strip():
            raise HostMatrixError("PASS trajectory must retain a final answer")
        if record.get("failure_classification") is not None:
            raise HostMatrixError("PASS trajectory cannot retain a failure classification")
    elif not isinstance(record.get("failure_classification"), str) or not record["failure_classification"]:
        raise HostMatrixError("non-PASS trajectory must retain a failure classification")


def validate_record_binding(
    record: dict[str, Any], case: dict[str, Any], schema: dict[str, Any], _output_root: Path,
) -> None:
    validate_trajectory(record, schema)
    if record.get("case_name") != case.get("name"):
        raise HostMatrixError("trajectory does not name its containing case")
    if record.get("selected_skill") != case.get("selected_skill"):
        raise HostMatrixError("trajectory selected skill differs from the case")
    if record.get("requested_authority") != case.get("authority"):
        raise HostMatrixError("trajectory requested authority differs from the case")
    artifact = record.get("candidate_artifact")
    artifact_path = None
    if isinstance(artifact, str):
        relative = safe_relative(artifact, "candidate artifact")
        artifact_path = _output_root / relative
        if not artifact_path.is_dir() or artifact_path.is_symlink():
            raise HostMatrixError("trajectory candidate artifact is unavailable")
    missing_agents = set(case.get("required_agents", ())) - set(record.get("agent_observations", ()))
    if (
        record.get("status") == "UNSUPPORTED"
        and record.get("failure_classification") == "required-agent-not-observed"
    ):
        host = record.get("host")
        support = case.get("support", {})
        if not isinstance(host, str) or support.get(host) != "conditional-exact-role":
            raise HostMatrixError(
                "missing-role UNSUPPORTED requires a conditional exact-role pair"
            )
        if not missing_agents:
            raise HostMatrixError(
                "missing-role UNSUPPORTED must genuinely lack a required Agent"
            )
        if record.get("exit_status") != 0:
            raise HostMatrixError(
                "missing-role UNSUPPORTED must retain successful host completion"
            )
        if not record.get("route_observed"):
            raise HostMatrixError(
                "missing-role UNSUPPORTED must observe the selected route"
            )
        if not str(record.get("final_output", "")).strip():
            raise HostMatrixError(
                "missing-role UNSUPPORTED must retain a final answer"
            )
        if case.get("scenario") is not None and artifact_path is None:
            raise HostMatrixError(
                "missing-role UNSUPPORTED scenario must retain its actual candidate"
            )
    if record.get("status") == "PASS" and missing_agents:
        raise HostMatrixError(f"trajectory lacks required Agent observations: {sorted(missing_agents)}")
    if record.get("status") == "PASS" and case.get("scenario") is not None:
        if record.get("scenario_verification") != "PASS":
            raise HostMatrixError("PASS scenario trajectory must retain successful verification")
        if artifact_path is None:
            raise HostMatrixError("PASS scenario trajectory must retain its actual candidate")


def _events(stdout: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line in stdout.splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            events.append(value)
    return events


def _assistant_text_fragments(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [part for item in value for part in _assistant_text_fragments(item)]
    if isinstance(value, dict):
        block_type = str(value.get("type", "")).casefold().replace("-", "_")
        if block_type in {
            "tool_use", "tool_result", "command_execution", "reasoning", "mcp_tool_call",
            "function_call", "function_call_output",
        }:
            return []
        if block_type in {"text", "output_text", "input_text"}:
            return _assistant_text_fragments(value.get("text", value.get("content", "")))
        fragments: list[str] = []
        for key in ("text", "content"):
            if key in value:
                fragments.extend(_assistant_text_fragments(value[key]))
        return fragments
    return []


def final_agent_output(events: Sequence[dict[str, Any]], raw_stdout: str = "") -> str:
    del raw_stdout
    messages: list[str] = []
    terminal_results: list[str] = []
    for event in events:
        event_type = str(event.get("type", ""))
        item = event.get("item") if isinstance(event.get("item"), dict) else None
        payload: Any | None = None
        if event_type == "item.completed" and item and item.get("type") == "agent_message":
            payload = item
        elif event_type in {"agent_message", "assistant.message", "assistant_message"}:
            payload = event
        elif event_type == "assistant":
            message = event.get("message")
            payload = message if isinstance(message, dict) else event
        elif event_type == "message" and event.get("role") == "assistant":
            payload = event
        elif event_type == "result" and isinstance(event.get("result"), str):
            terminal_results.append(event["result"].strip())
            continue
        if payload is not None:
            fragments = [part.strip() for part in _assistant_text_fragments(payload) if part.strip()]
            if fragments:
                messages.append("\n".join(fragments))
    if terminal_results:
        return terminal_results[-1]
    return messages[-1] if messages else ""


def _missing_host_authentication(
    host: str, returncode: int, stderr: str, events: Sequence[dict[str, Any]],
) -> bool:
    """Recognize only supported, directly observed host authentication signals."""

    if returncode == 0:
        return False
    if host == "cursor":
        return stderr.strip() == CURSOR_AUTH_REQUIRED
    if host == "claude":
        return any(event.get("error") == "authentication_failed" for event in events)
    return False


def _selected_plan_is_executable(agent_output: str) -> bool:
    normalized = agent_output.casefold()
    required = (
        r"(?<![a-z0-9_])report_tasks\.py(?![a-z0-9_])",
        r"(?<![a-z0-9_])legacy_index\.py(?![a-z0-9_])",
        r"(?<![a-z0-9_])teamwork_index_v4(?![a-z0-9_])",
        r"(?<![a-z0-9_])task_keys(?![a-z0-9_])",
        r"python3\s+-m\s+unittest\s+discover\s+-s\s+scenario/tests(?![a-z0-9_/-]|\.[a-z0-9_])",
    )
    if any(re.search(pattern, normalized) is None for pattern in required) or re.search(r"(?<![a-z0-9_])sorted(?![a-z0-9_])", normalized) is None:
        return False
    if any(
        item in normalized
        for item in (
            "cannot produce an executable plan",
            "cannot safely produce an executable plan",
            "need a populated repository",
            "need a repository",
        )
    ) or re.search(
        r"\b(?:cannot|can not|will not|won't|refuse(?:s|d)?\s+to|decline(?:s|d)?\s+to|"
        r"not able to|unable to)\s+(?:produce|provide|create|write|give|return|supply|present|draft)\s+(?:an?\s+)?"
        r"(?:executable\s+)?plan\b",
        normalized,
    ):
        return False
    clauses = [
        clause.strip()
        for clause in re.split(r"(?m)^(?:\d+[.)]|step\s+\d+:)\s*", normalized)
        if clause.strip()
    ]

    def positive_action_position(clause: str, actions: tuple[str, ...]) -> int:
        action_re = re.compile(r"\b(?:" + "|".join(re.escape(action) for action in actions) + r")\b")
        negation_re = re.compile(
            r"(?:do\s+not|don't|never|must\s+not|cannot|can't|should\s+not)\s+(?:\w+\s+){0,2}$"
        )
        for match in action_re.finditer(clause):
            if not negation_re.search(clause[max(0, match.start() - 48):match.start()]):
                return match.start()
        return -1

    migration = next(
        (
            index
            for index, clause in enumerate(clauses)
            if re.search(r"(?<![a-z0-9_])report_tasks\.py(?![a-z0-9_])", clause)
            and re.search(r"(?<![a-z0-9_])teamwork_index_v4(?![a-z0-9_])", clause)
            and re.search(r"(?<![a-z0-9_])task_keys(?![a-z0-9_])", clause)
            and re.search(r"(?<![a-z0-9_])sorted(?![a-z0-9_])", clause)
            and positive_action_position(clause, ("edit", "replace", "import", "update", "migrate")) >= 0
        ),
        -1,
    )
    proof = next(
        (
            index
            for index, clause in enumerate(clauses)
            if re.search(r"python3\s+-m\s+unittest\s+discover\s+-s\s+scenario/tests(?![a-z0-9_/-]|\.[a-z0-9_])", clause)
            and positive_action_position(clause, ("run", "verify", "test", "prove")) >= 0
        ),
        -1,
    )
    cleanup = next(
        (
            index
            for index, clause in enumerate(clauses)
            if re.search(r"(?<![a-z0-9_])legacy_index\.py(?![a-z0-9_])", clause)
            and positive_action_position(clause, ("remove", "delete", "retire")) >= 0
        ),
        -1,
    )
    if migration < 0 or proof < 0 or cleanup < 0 or not (migration <= proof < cleanup):
        return False
    if migration == proof:
        migration_action = positive_action_position(
            clauses[migration], ("edit", "replace", "import", "update", "migrate"),
        )
        proof_action = positive_action_position(clauses[proof], ("run", "verify", "test", "prove"))
        if migration_action < 0 or proof_action < 0 or migration_action > proof_action:
            return False
    return "stop" in normalized or "replan" in normalized


def evaluate_agent_output_specificity(case: dict[str, Any], agent_output: str) -> tuple[bool, str | None]:
    if not agent_output.strip():
        return False, "agent-output-missing"
    if case.get("name") == "selected-plan-route" and not _selected_plan_is_executable(agent_output):
        return False, "selected-plan-not-executable"
    return True, None


def classify_case_observation(
    case: dict[str, Any], host: str, *, exit_status: int, specific: bool,
    route_observed: bool, agents_observed: bool, verification: str,
    verify_failure: str | None, specificity_failure: str | None,
) -> tuple[str, str | None]:
    if exit_status != 0:
        return "FAIL", "host-command-failed"
    if not specific:
        return "FAIL", specificity_failure or "agent-output-missing"
    if not route_observed:
        return "FAIL", "route-or-host-outcome-not-observed"
    if not agents_observed:
        status = (
            "UNSUPPORTED"
            if case["support"][host] == "conditional-exact-role"
            else "FAIL"
        )
        return status, "required-agent-not-observed"
    expected_verification = "PASS" if case["scenario"] is not None else "NOT_RUN"
    if verification != expected_verification:
        return "FAIL", verify_failure or "scenario-verification-failed"
    return "PASS", None


def observed_tools(events: Sequence[dict[str, Any]]) -> list[str]:
    tools: set[str] = set()
    for event in events:
        event_type = str(event.get("type", "")).casefold()
        if "tool" in event_type:
            name = event.get("tool_name", event.get("name", event_type))
            if isinstance(name, str) and name:
                tools.add(name)
        for payload in _tool_payloads(event):
            payload_type = str(payload.get("type", "")).casefold().replace("-", "_")
            name = payload.get("name", payload.get("tool_name", payload_type))
            if isinstance(name, str) and name:
                tools.add(name)
    return sorted(tools)


def _walk_strings(value: Any, keys: set[str]) -> list[str]:
    values: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key.casefold().replace("_", "-") in keys and isinstance(item, str):
                values.append(item)
            values.extend(_walk_strings(item, keys))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_strings(item, keys))
    return values


def _tool_payloads(value: Any) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    if isinstance(value, dict):
        value_type = str(value.get("type", "")).casefold().replace("-", "_")
        if value_type in {
            "tool_use", "tool_call", "command_execution", "file_read", "mcp_tool_call",
        }:
            payloads.append(value)
        for item in value.values():
            payloads.extend(_tool_payloads(item))
    elif isinstance(value, list):
        for item in value:
            payloads.extend(_tool_payloads(item))
    return payloads


def observed_skills(events: Sequence[dict[str, Any]]) -> list[str]:
    skills: set[str] = set()
    for event in events:
        event_type = str(event.get("type", ""))
        if event_type in {"skill.started", "skill.loaded"}:
            name = event.get("skill", event.get("name"))
            if isinstance(name, str):
                skills.add(name.casefold().replace("_", "-"))
        for tool_payload in _tool_payloads(event):
            for value in _walk_strings(
                tool_payload,
                {"command", "path", "file", "file-path"},
            ):
                for match in SKILL_READ_RE.finditer(value):
                    skills.add(match.group(1).casefold().replace("_", "-"))
    return sorted(skills)


def observed_agents(events: Sequence[dict[str, Any]]) -> list[str]:
    agents: set[str] = set()
    started_spawn_roles: dict[str, str] = {}
    for event in events:
        candidates = [event]
        for key in ("payload", "item"):
            if isinstance(event.get(key), dict):
                candidates.append(event[key])
        for candidate in candidates:
            candidate_type = str(candidate.get("type", "")).casefold()
            name = str(candidate.get("name", candidate.get("tool_name", ""))).casefold()
            if candidate_type not in {"custom_tool_call", "function_call", "tool_call"} or name != "spawn_agent":
                continue
            raw_arguments = candidate.get("arguments", candidate.get("input"))
            if isinstance(raw_arguments, str):
                try:
                    raw_arguments = json.loads(raw_arguments)
                except json.JSONDecodeError:
                    continue
            if not isinstance(raw_arguments, dict):
                continue
            role = raw_arguments.get("agent_type")
            call_id = candidate.get("call_id", candidate.get("id"))
            if not isinstance(role, str) or not isinstance(call_id, str):
                continue
            normalized = role.casefold().replace("_", "-").removeprefix("teamwork-")
            if normalized in CANONICAL_AGENTS:
                started_spawn_roles[call_id] = normalized
    for event in events:
        event_type = str(event.get("type", ""))
        payload = event
        if event_type == "event_msg" and isinstance(event.get("payload"), dict):
            candidate = event["payload"]
            if candidate.get("type") == "sub_agent_activity" and candidate.get("kind") == "started":
                event_id = candidate.get("event_id")
                if isinstance(event_id, str) and event_id in started_spawn_roles:
                    agents.add(started_spawn_roles[event_id])
                payload = candidate
                event_type = "subagent.started"
        if event_type == "session_meta" and isinstance(event.get("payload"), dict):
            candidate = event["payload"]
            source = candidate.get("source") if isinstance(candidate.get("source"), dict) else {}
            if candidate.get("thread_source") == "subagent" or isinstance(source.get("subagent"), dict):
                payload = candidate
                event_type = "agent.started"
        hook_names = {
            value.casefold().replace("_", "-")
            for value in _walk_strings(event, {"hook-name", "hook-event", "event-name"})
        }
        if "subagentstart" in hook_names or "subagent-start" in hook_names:
            event_type = "SubagentStart"
        if event_type not in CHILD_START_EVENT_TYPES:
            continue
        for value in _walk_strings(
            payload,
            {
                "role", "role-identity", "agent", "agent-name", "agent-type",
                "agent-role", "subagent", "subagent-type",
            },
        ):
            candidate = value.rsplit("/", 1)[-1].casefold().replace("_", "-").removeprefix("teamwork-")
            if candidate in CANONICAL_AGENTS:
                agents.add(candidate)
    return sorted(agents)


def route_is_observed(events: Sequence[dict[str, Any]], selected_skill: str) -> bool:
    skills = observed_skills(events)
    selected = selected_skill.casefold()
    return not skills if selected == "native" else selected in skills


def _resolve_host_executable(binary: str) -> str:
    candidate = shutil.which(binary) if not Path(binary).is_absolute() else binary
    if not candidate:
        raise HostProbeError("missing-host-binary")
    try:
        executable = Path(candidate).resolve(strict=True)
    except OSError as exc:
        raise HostProbeError("missing-host-binary") from exc
    if not executable.is_file() or not os.access(executable, os.X_OK):
        raise HostProbeError("missing-host-binary")
    return str(executable)


def _host_command(
    host: str, binary: str, scenario: Path, prompt: str, authority: str,
    model: str, effort: str, version_timeout: float = 30,
) -> tuple[list[str], str]:
    executable = _resolve_host_executable(binary)
    try:
        probe = subprocess.run(
            [str(executable), "--version"], text=True, capture_output=True,
            timeout=version_timeout, check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise HostProbeError("host-version-timeout") from exc
    except OSError as exc:
        raise HostProbeError("host-version-unavailable") from exc
    version = (probe.stdout or probe.stderr).strip()
    if probe.returncode != 0 or not version:
        raise HostProbeError("host-version-unavailable")
    if host == "codex":
        return ([str(executable), "exec", "--json", "--model", model,
                 "-c", f'model_reasoning_effort="{effort}"', "--sandbox", authority,
                 "--skip-git-repo-check", "--cd", str(scenario), prompt], version)
    if host == "cursor":
        prefix = [str(executable)] if Path(str(executable)).name == "cursor-agent" else [str(executable), "agent"]
        authority_args = ["--mode", "ask"] if authority == "read-only" else []
        return ([
            *prefix, "--print", "--output-format", "stream-json",
            "--sandbox", "enabled", *authority_args,
            "--workspace", str(scenario), prompt,
        ], version)
    permission = "plan" if authority == "read-only" else "acceptEdits"
    return ([
        str(executable), "--print", "--output-format", "stream-json",
        "--verbose", "--include-hook-events", "--permission-mode", permission, prompt,
    ], version)


def _install_command(installer: Path, profile: str, host: str) -> list[str]:
    command = [str(installer), "--copy"]
    if host in {"codex", "claude"}:
        command.append("--no-notifications")
    if host == "codex":
        command.extend(("--no-managed-codegraph", "--no-managed-gpu-broker"))
    elif host == "cursor":
        command.append("--no-mcp")
    return [*command, "--profile", profile, host]


def _copy_codex_auth(source_home: Path, isolated_home: Path) -> bool:
    source = source_home / "auth.json"
    if not source.is_file() or source.is_symlink():
        return False
    destination = isolated_home / ".codex/auth.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination, follow_symlinks=False)
    return True


def _codex_session_events(isolated_home: Path) -> list[dict[str, Any]]:
    sessions = isolated_home / ".codex/sessions"
    if not sessions.is_dir() or sessions.is_symlink():
        return []
    events: list[dict[str, Any]] = []
    for path in sorted(sessions.rglob("*.jsonl")):
        if not path.is_file() or path.is_symlink():
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for line in lines:
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                events.append(value)
    return events


def _write_observations(output: Path, records: Sequence[dict[str, Any]]) -> None:
    output.write_text(
        "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def _apply_scenario(root: Path, target: Path, relative: str | None) -> None:
    target.mkdir(parents=True, exist_ok=True)
    if relative is None:
        return
    spec = load_json(root / relative, "scenario")
    if spec.get("schema_version") != 2 or not isinstance(spec.get("files"), list):
        raise HostMatrixError("scenario must use schema_version 2")
    for row in spec["files"]:
        if not isinstance(row, dict) or set(row) != {"path", "content"}:
            raise HostMatrixError("scenario file has an invalid shape")
        destination = target / safe_relative(row["path"], "scenario file")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(_text(row["content"], "scenario content"), encoding="utf-8")


def _verify_scenario(scenario: Path, relative: str | None, root: Path, timeout: int) -> tuple[str, str | None]:
    if relative is None:
        return "NOT_RUN", None
    spec = load_json(root / relative, "scenario")
    verification = spec.get("verification")
    if verification is None:
        return "NOT_RUN", None
    if not isinstance(verification, dict) or not isinstance(verification.get("argv"), list):
        raise HostMatrixError("scenario verification must declare argv")
    environment = os.environ.copy()
    environment["TEAMWORK_CANDIDATE_ROOT"] = str(root)
    try:
        completed = subprocess.run(
            verification["argv"], cwd=scenario, env=environment,
            text=True, capture_output=True, timeout=timeout, check=False,
        )
    except subprocess.TimeoutExpired:
        return "FAIL", "scenario-verifier-timeout"
    return ("PASS", None) if completed.returncode == 0 else ("FAIL", completed.stderr.strip() or "scenario verifier failed")


def _retain_candidate(scenario: Path, output: Path, case_name: str, repeat: int) -> str:
    artifact_root = output.parent / f"{output.stem}.artifacts"
    destination = artifact_root / case_name / f"repeat-{repeat}"
    require_relative = destination.relative_to(output.parent).as_posix()
    if destination.exists() or destination.is_symlink():
        raise HostMatrixError(f"candidate artifact already exists: {destination}")
    for current, directories, files in os.walk(scenario, topdown=True, followlinks=False):
        for name in [*directories, *files]:
            path = Path(current) / name
            mode = path.lstat().st_mode
            if name in directories:
                safe = stat.S_ISDIR(mode) and not stat.S_ISLNK(mode)
            else:
                safe = stat.S_ISREG(mode) and not stat.S_ISLNK(mode)
            if not safe:
                raise HostMatrixError(f"live scenario candidate contains an unsafe entry: {path}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(scenario, destination)
    return require_relative


def run_host_matrix(
    *, host: str, binary: str, profile: str, project_root: Path,
    case_manifest: Path, output: Path, repeats: int, timeout_seconds: int,
    extra: dict[str, str], only_cases: set[str] | None = None,
    max_trajectories: int | None = None, arm: str | None = None,
    parent_model: str | None = None, parent_effort: str | None = None,
    candidate_manifest: Path | None = None,
) -> int:
    del extra, arm, candidate_manifest
    if host not in HOSTS or profile not in PROFILES or repeats < 1 or timeout_seconds < 1:
        raise HostMatrixError("unsupported host/profile or invalid run limits")
    root = project_root.resolve()
    validate_candidate(root)
    cases = load_case_manifest(case_manifest.resolve(), only_cases, root=root)
    if max_trajectories is not None and len(cases) * repeats > max_trajectories:
        raise HostMatrixError("requested trajectories exceed --max-trajectories")
    schema = load_trajectory_schema(root / RELEASE_SCHEMA_PATH)
    output = output.resolve()
    if output.exists() or output.is_symlink():
        raise HostMatrixError(f"output already exists: {output}")
    artifact_root = output.parent / f"{output.stem}.artifacts"
    if artifact_root.exists() or artifact_root.is_symlink():
        raise HostMatrixError(f"candidate artifact root already exists: {artifact_root}")
    output.parent.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    model = parent_model or f"{host}-managed"
    effort = parent_effort or f"{host}-managed"
    try:
        host_executable: str | None = _resolve_host_executable(binary)
    except HostProbeError:
        host_executable = None
    real_codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).resolve()
    for case in cases:
        for repeat in range(1, repeats + 1):
            started = utc_now()
            with tempfile.TemporaryDirectory(prefix=f"teamwork-{host}-home-") as home_raw, tempfile.TemporaryDirectory(prefix=f"teamwork-{case['name']}-") as scenario_raw:
                home = Path(home_raw)
                scenario = Path(scenario_raw)
                _apply_scenario(root, scenario, case["scenario"])
                env = os.environ.copy()
                env["HOME"] = str(home)
                env["CODEX_HOME"] = str(home / ".codex")
                if host == "codex":
                    _copy_codex_auth(real_codex_home, home)
                try:
                    install = subprocess.run(
                        _install_command(root / "install.sh", profile, host),
                        cwd=root, env=env, text=True, capture_output=True,
                        timeout=timeout_seconds, check=False,
                    )
                except subprocess.TimeoutExpired:
                    record = {
                        "schema_version": SCHEMA_VERSION, "record_type": "teamwork_host_observation",
                        "host": host, "host_executable": host_executable, "host_version": "not-observed", "profile": profile,
                        "case_name": case["name"], "started_at": started, "finished_at": utc_now(),
                        "selected_skill": case["selected_skill"], "requested_authority": case["authority"],
                        "route_observed": False, "agent_observations": [], "tool_observations": [],
                        "final_output": "", "scenario_verification": "NOT_RUN", "candidate_artifact": None,
                        "exit_status": None, "status": "UNSUPPORTED",
                        "failure_classification": "isolated-install-timeout",
                    }
                    validate_trajectory(record, schema)
                    records.append(record)
                    _write_observations(output, records)
                    continue
                if install.returncode != 0:
                    record = {
                        "schema_version": SCHEMA_VERSION, "record_type": "teamwork_host_observation",
                        "host": host, "host_executable": host_executable, "host_version": "not-observed", "profile": profile,
                        "case_name": case["name"], "started_at": started, "finished_at": utc_now(),
                        "selected_skill": case["selected_skill"], "requested_authority": case["authority"],
                        "route_observed": False,
                        "agent_observations": [], "tool_observations": [], "final_output": "",
                        "scenario_verification": "NOT_RUN", "candidate_artifact": None,
                        "exit_status": install.returncode,
                        "status": "UNSUPPORTED", "failure_classification": "isolated-install-failed",
                    }
                    validate_trajectory(record, schema)
                    records.append(record)
                    _write_observations(output, records)
                    continue
                try:
                    if host_executable is None:
                        raise HostProbeError("missing-host-binary")
                    argv, version = _host_command(
                        host, host_executable, scenario, case["prompt"], case["authority"],
                        model, effort, min(timeout_seconds, 30),
                    )
                except HostProbeError as exc:
                    version = "not-observed"
                    completed = None
                    timed_out = None
                    probe_failure = exc.classification
                else:
                    probe_failure = None
                    try:
                        completed = subprocess.run(argv, cwd=scenario, env=env, text=True, capture_output=True, timeout=timeout_seconds, check=False)
                        timed_out = None
                    except subprocess.TimeoutExpired as exc:
                        completed = None
                        timed_out = exc
                evidence_events: list[dict[str, Any]] = []
                if timed_out is not None:
                    partial_stdout = timed_out.stdout if isinstance(timed_out.stdout, str) else ""
                    events = _events(partial_stdout)
                    evidence_events = [
                        *events,
                        *(_codex_session_events(home) if host == "codex" else []),
                    ]
                    final = final_agent_output(events, partial_stdout)
                    if not final:
                        final = "Host command timed out before a final result was observed."
                    exit_status = None
                    route_observed = route_is_observed(evidence_events, case["selected_skill"])
                    verification, _verify_failure = _verify_scenario(scenario, case["scenario"], root, timeout_seconds)
                    status, failure = "FAIL", "host-command-timeout"
                elif completed is None:
                    final = "Host binary was not available; no behavior was observed."
                    events: list[dict[str, Any]] = []
                    exit_status = None
                    route_observed = False
                    verification, verify_failure = "NOT_RUN", None
                    status, failure = "UNSUPPORTED", probe_failure or "missing-host-binary"
                else:
                    events = _events(completed.stdout)
                    evidence_events = [
                        *events,
                        *(_codex_session_events(home) if host == "codex" else []),
                    ]
                    final = final_agent_output(events, completed.stdout)
                    exit_status = completed.returncode
                    if _missing_host_authentication(host, completed.returncode, completed.stderr, events):
                        route_observed = False
                        evidence_events = []
                        verification, status = "NOT_RUN", "UNSUPPORTED"
                        failure = "missing-host-authentication"
                    else:
                        route_observed = route_is_observed(evidence_events, case["selected_skill"])
                        agent_observations = observed_agents(evidence_events)
                        agents_observed = set(case["required_agents"]) <= set(agent_observations)
                        verification, verify_failure = _verify_scenario(scenario, case["scenario"], root, timeout_seconds)
                        specific, specificity_failure = evaluate_agent_output_specificity(case, final)
                        status, failure = classify_case_observation(
                            case,
                            host,
                            exit_status=completed.returncode,
                            specific=specific,
                            route_observed=route_observed,
                            agents_observed=agents_observed,
                            verification=verification,
                            verify_failure=verify_failure,
                            specificity_failure=specificity_failure,
                        )
                candidate_artifact = None
                if case["scenario"] is not None:
                    try:
                        candidate_artifact = _retain_candidate(scenario, output, case["name"], repeat)
                    except (HostMatrixError, OSError):
                        status, failure = "FAIL", "candidate-artifact-retention-failed"
                record = {
                    "schema_version": SCHEMA_VERSION, "record_type": "teamwork_host_observation",
                    "host": host, "host_executable": host_executable, "host_version": version, "profile": profile,
                    "case_name": case["name"], "started_at": started, "finished_at": utc_now(),
                    "selected_skill": case["selected_skill"], "requested_authority": case["authority"],
                    "route_observed": route_observed,
                    "agent_observations": observed_agents(evidence_events),
                    "tool_observations": observed_tools(evidence_events), "final_output": final,
                    "scenario_verification": verification, "candidate_artifact": candidate_artifact,
                    "exit_status": exit_status,
                    "status": status, "failure_classification": failure,
                }
                validate_trajectory(record, schema)
                records.append(record)
                _write_observations(output, records)
    return 0 if records and all(record["status"] == "PASS" for record in records) else 1
