#!/usr/bin/env python3
"""Read-only readiness checks for Teamwork Codex custom-agent routing."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import shutil
import subprocess
import sys
from typing import Any

from codex_routing_config import RoutingConfigError
from codex_routing_config import inspect_config

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11 uses the narrow fallback below.
    tomllib = None  # type: ignore[assignment]


EXPECTED_PROFILES = {
    "teamwork-researcher.toml": ("teamwork_researcher", "read-only"),
    "teamwork-explorer.toml": ("teamwork_explorer", "read-only"),
    "teamwork-worker.toml": ("teamwork_worker", "workspace-write"),
    "teamwork-debugger.toml": ("teamwork_debugger", "workspace-write"),
    "teamwork-designer.toml": ("teamwork_designer", "read-only"),
    "teamwork-planner.toml": ("teamwork_planner", "workspace-write"),
    "teamwork-plan-reviewer.toml": ("teamwork_plan_reviewer", "read-only"),
    "teamwork-reviewer.toml": ("teamwork_reviewer", "read-only"),
}
REQUIRED_FIELDS = {
    "name",
    "description",
    "developer_instructions",
    "nickname_candidates",
    "model",
    "model_reasoning_effort",
    "sandbox_mode",
}
LEAF_CONTRACT = "Do not spawn or delegate."
NICKNAME_PATTERN = re.compile(r"^[A-Za-z0-9 _-]+$")
PROMPT_MARKERS = {
    "global_policy": "Teamwork Codex Global Policy",
    "project_instructions": "Teamwork Project Instructions",
}


class CheckFailure(RuntimeError):
    pass


def _fallback_profile_parse(path: pathlib.Path) -> dict[str, Any]:
    """Parse Teamwork's simple top-level profile contract without extra deps."""
    text = path.read_text(encoding="utf-8")
    data: dict[str, Any] = {}
    for key in REQUIRED_FIELDS - {"nickname_candidates", "developer_instructions"}:
        match = re.search(
            rf'^\s*{re.escape(key)}\s*=\s*("(?:[^"\\]|\\.)*")\s*$',
            text,
            re.MULTILINE,
        )
        if match:
            data[key] = json.loads(match.group(1))

    nicknames = re.search(
        r"^\s*nickname_candidates\s*=\s*(\[[^\n]*\])\s*$",
        text,
        re.MULTILINE,
    )
    if nicknames:
        data["nickname_candidates"] = json.loads(nicknames.group(1))

    instructions = re.search(
        r'^\s*developer_instructions\s*=\s*"""(.*?)"""',
        text,
        re.MULTILINE | re.DOTALL,
    )
    if instructions:
        data["developer_instructions"] = instructions.group(1)
    return data


def load_profile(path: pathlib.Path) -> dict[str, Any]:
    try:
        if tomllib is None:
            return _fallback_profile_parse(path)
        with path.open("rb") as handle:
            return tomllib.load(handle)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise CheckFailure(f"invalid profile {path}: {exc}") from exc


def validate_profiles(agents_dir: pathlib.Path) -> tuple[list[dict[str, Any]], int]:
    if not agents_dir.is_dir():
        raise CheckFailure(f"agent directory not found: {agents_dir}")

    records: list[dict[str, Any]] = []
    agent_names: dict[str, pathlib.Path] = {}
    nicknames: dict[str, pathlib.Path] = {}

    for filename, (expected_name, expected_sandbox) in EXPECTED_PROFILES.items():
        path = agents_dir / filename
        if not path.is_file():
            raise CheckFailure(f"missing Teamwork profile: {path}")
        data = load_profile(path)

        missing = sorted(REQUIRED_FIELDS - data.keys())
        if missing:
            raise CheckFailure(f"{filename} missing fields: {', '.join(missing)}")
        if data["name"] != expected_name:
            raise CheckFailure(
                f"{filename} name must be {expected_name!r}, got {data['name']!r}"
            )
        if data["sandbox_mode"] != expected_sandbox:
            raise CheckFailure(
                f"{filename} sandbox_mode must be {expected_sandbox!r}, "
                f"got {data['sandbox_mode']!r}"
            )

        for field in ("description", "developer_instructions", "model", "model_reasoning_effort"):
            if not isinstance(data[field], str) or not data[field].strip():
                raise CheckFailure(f"{filename} field {field} must be a non-empty string")
        if LEAF_CONTRACT not in data["developer_instructions"]:
            raise CheckFailure(f"{filename} is missing the explicit leaf-agent contract")

        name = data["name"]
        if name in agent_names:
            raise CheckFailure(f"duplicate agent name {name!r}: {agent_names[name]} and {path}")
        agent_names[name] = path

        profile_nicknames = data["nickname_candidates"]
        if not isinstance(profile_nicknames, list) or not profile_nicknames:
            raise CheckFailure(f"{filename} nickname_candidates must be a non-empty list")
        for nickname in profile_nicknames:
            if (
                not isinstance(nickname, str)
                or not nickname
                or not NICKNAME_PATTERN.fullmatch(nickname)
            ):
                raise CheckFailure(f"{filename} has invalid nickname {nickname!r}")
            if nickname in nicknames:
                raise CheckFailure(
                    f"duplicate nickname {nickname!r}: {nicknames[nickname]} and {path}"
                )
            nicknames[nickname] = path

        records.append(
            {
                "file": filename,
                "name": name,
                "model": data["model"],
                "effort": data["model_reasoning_effort"],
                "sandbox_mode": data["sandbox_mode"],
            }
        )

    for path in sorted(agents_dir.glob("*.toml")):
        if path.name in EXPECTED_PROFILES:
            continue
        if path.name.startswith("teamwork-"):
            raise CheckFailure(f"unexpected Teamwork profile: {path}")
        data = load_profile(path)
        name = data.get("name")
        if isinstance(name, str):
            if name in agent_names:
                raise CheckFailure(
                    f"duplicate agent name {name!r}: {agent_names[name]} and {path}"
                )
            agent_names[name] = path
        profile_nicknames = data.get("nickname_candidates", [])
        if not isinstance(profile_nicknames, list):
            raise CheckFailure(f"{path.name} nickname_candidates must be a list")
        for nickname in profile_nicknames:
            if not isinstance(nickname, str) or not NICKNAME_PATTERN.fullmatch(nickname):
                raise CheckFailure(f"{path.name} has invalid nickname {nickname!r}")
            if nickname in nicknames:
                raise CheckFailure(
                    f"duplicate nickname {nickname!r}: {nicknames[nickname]} and {path}"
                )
            nicknames[nickname] = path
    return records, len(nicknames)


def run_command(command: list[str], timeout_seconds: float | None) -> str:
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise CheckFailure(f"could not run {' '.join(command)}: {exc}") from exc
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "no diagnostic output"
        raise CheckFailure(f"{' '.join(command)} failed: {detail}")
    return result.stdout


def inspect_catalog(
    codex: str,
    profiles: list[dict[str, Any]],
    timeout_seconds: float | None,
) -> dict[str, dict[str, Any]]:
    raw = run_command([codex, "debug", "models", "--bundled"], timeout_seconds)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CheckFailure(f"codex bundled catalog is not valid JSON: {exc}") from exc

    entries = payload.get("models") if isinstance(payload, dict) else payload
    if not isinstance(entries, list):
        raise CheckFailure("codex bundled catalog does not contain a model list")
    by_slug = {
        entry.get("slug", entry.get("id")): entry
        for entry in entries
        if isinstance(entry, dict) and entry.get("slug", entry.get("id"))
    }

    report: dict[str, dict[str, Any]] = {}
    for profile in profiles:
        model = profile["model"]
        effort = profile["effort"]
        entry = by_slug.get(model)
        if entry is None:
            raise CheckFailure(f"configured model {model!r} is absent from the bundled catalog")
        levels = entry.get("supported_reasoning_levels", [])
        supported = {
            level.get("effort") if isinstance(level, dict) else level
            for level in levels
        }
        if effort not in supported:
            raise CheckFailure(
                f"configured effort {effort!r} is not supported by model {model!r}"
            )
        model_report = report.setdefault(
            model,
            {
                "multi_agent_version": entry.get("multi_agent_version", "unknown"),
                "configured_efforts": [],
            },
        )
        if effort not in model_report["configured_efforts"]:
            model_report["configured_efforts"].append(effort)

    for model_report in report.values():
        model_report["configured_efforts"].sort()
    return report


def inspect_prompt(
    codex: str,
    timeout_seconds: float | None,
) -> dict[str, str]:
    raw = run_command([codex, "debug", "prompt-input"], timeout_seconds)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CheckFailure(f"codex prompt input is not valid JSON: {exc}") from exc

    # `codex debug prompt-input` emits AGENTS.md context in a generated user-role
    # message, so marker checks must cover the complete debug payload. This
    # command accepts no task prompt and the payload is never persisted or shown.
    prompt_text = json.dumps(payload, ensure_ascii=False)
    status = {
        name: "loaded" if marker in prompt_text else "missing"
        for name, marker in PROMPT_MARKERS.items()
    }
    if "loaded" not in status.values():
        raise CheckFailure(
            "current prompt contains neither the Teamwork global policy nor project instructions"
        )
    return status


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    agents_dir = args.agents_dir.expanduser().resolve()
    profiles, nickname_count = validate_profiles(agents_dir)
    report: dict[str, Any] = {
        "status": "ok",
        "mode": "profiles-only" if args.profiles_only else "readiness",
        "agents_dir": str(agents_dir),
        "profile_count": len(profiles),
        "nickname_count": nickname_count,
    }
    if args.profiles_only:
        return report

    codex = shutil.which("codex")
    if codex is None:
        raise CheckFailure("codex executable not found on PATH")
    report["codex_version"] = run_command([codex, "--version"], args.timeout_seconds).strip()
    report["models"] = inspect_catalog(codex, profiles, args.timeout_seconds)
    report["prompt"] = (
        {"status": "skipped"}
        if args.skip_prompt
        else inspect_prompt(codex, args.timeout_seconds)
    )
    try:
        routing = inspect_config(args.config)
    except RoutingConfigError as exc:
        raise CheckFailure(f"could not inspect Codex routing config: {exc}") from exc
    report["routing"] = routing.to_dict()
    if not routing.ready:
        raise CheckFailure(
            "Codex custom-agent routing is not ready: " + "; ".join(routing.issues)
        )
    report["spawn_selector"] = (
        "config ready; a fresh callable-schema or live spawn probe remains the behavioral proof"
    )
    report["mutations"] = "none"
    report["model_calls"] = "none"
    return report


def print_text_report(report: dict[str, Any]) -> None:
    print(f"STATUS={report['status']}")
    print(f"MODE={report['mode']}")
    print(f"AGENTS_DIR={report['agents_dir']}")
    print(f"PROFILES={report['profile_count']}")
    print(f"NICKNAMES={report['nickname_count']}")
    if report["mode"] == "profiles-only":
        return
    print(f"CODEX_VERSION={report['codex_version']}")
    for model, details in sorted(report["models"].items()):
        efforts = ",".join(details["configured_efforts"])
        print(
            f"MODEL={model} efforts={efforts} "
            f"multi_agent_version={details['multi_agent_version']}"
        )
    prompt = report["prompt"]
    if prompt.get("status") == "skipped":
        print("PROMPT=skipped")
    else:
        print(f"PROMPT_GLOBAL_POLICY={prompt['global_policy']}")
        print(f"PROMPT_PROJECT_INSTRUCTIONS={prompt['project_instructions']}")
    routing = report["routing"]
    print(f"ROUTING_CONFIG={routing['status']}")
    print(f"ROUTING_NAMESPACE=teamwork")
    print(f"SPAWN_SELECTOR={report['spawn_selector']}")
    print("MUTATIONS=none")
    print("MODEL_CALLS=none")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate Teamwork Codex agent profiles and, unless --profiles-only is "
            "used, check the local bundled model catalog and prompt loading without "
            "calling a model or changing configuration."
        )
    )
    parser.add_argument(
        "--agents-dir",
        type=pathlib.Path,
        default=pathlib.Path.home() / ".codex" / "agents",
        help="Teamwork Codex agent directory (default: ~/.codex/agents)",
    )
    parser.add_argument(
        "--config",
        type=pathlib.Path,
        default=pathlib.Path.home() / ".codex" / "config.toml",
        help="Codex config path (default: ~/.codex/config.toml)",
    )
    parser.add_argument(
        "--profiles-only",
        action="store_true",
        help="validate profile contracts without requiring the Codex CLI",
    )
    parser.add_argument(
        "--skip-prompt",
        action="store_true",
        help="skip codex debug prompt-input while still checking the bundled catalog",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        help="optional per-command timeout; unset means use the command's own limits",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report = build_report(args)
    except CheckFailure as exc:
        if args.json:
            print(json.dumps({"status": "failed", "error": str(exc)}, indent=2))
        else:
            print("STATUS=failed")
            print(f"ERROR={exc}")
        return 1

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
