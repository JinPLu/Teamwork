#!/usr/bin/env python3
"""Check Teamwork Codex profiles without calling models or comparing versions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

from codex_routing_config import RoutingConfigError, inspect_config
from teamwork_tooling.topology import host_role_paths

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None


ROOT = Path(__file__).resolve().parents[1]
ROLE_SANDBOX = {
    "researcher": "read-only",
    "explorer": "read-only",
    "debugger": "workspace-write",
    "challenger": "read-only",
    "planner": "read-only",
    "reviewer": "read-only",
    "worker": "workspace-write",
    "writer": "workspace-write",
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


class CheckFailure(RuntimeError):
    pass


def load_profile(path: Path) -> dict[str, object]:
    if tomllib is None:
        raise CheckFailure("Python 3.11 or newer is required")
    try:
        with path.open("rb") as handle:
            return tomllib.load(handle)
    except (OSError, ValueError) as exc:
        raise CheckFailure(f"invalid profile {path}: {exc}") from exc


def validate_profiles(agents_dir: Path) -> tuple[int, int]:
    expected = {
        Path(path).name: (f"teamwork_{role}", ROLE_SANDBOX[role])
        for role, path in host_role_paths(ROOT)["codex"].items()
    }
    names: set[str] = set()
    nicknames: set[str] = set()
    for filename, (expected_name, expected_sandbox) in expected.items():
        path = agents_dir / filename
        if not path.is_file():
            raise CheckFailure(f"missing Teamwork profile: {path}")
        data = load_profile(path)
        missing = sorted(REQUIRED_FIELDS - data.keys())
        if missing:
            raise CheckFailure(f"{filename} missing fields: {', '.join(missing)}")
        if data["name"] != expected_name or data["sandbox_mode"] != expected_sandbox:
            raise CheckFailure(f"{filename} has an unexpected role identity or sandbox")
        if data["name"] in names:
            raise CheckFailure(f"duplicate Agent name: {data['name']}")
        names.add(data["name"])
        values = data["nickname_candidates"]
        if not isinstance(values, list) or not values:
            raise CheckFailure(f"{filename} needs nickname candidates")
        for value in values:
            if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9 _-]+", value):
                raise CheckFailure(f"{filename} has an invalid nickname")
            if value in nicknames:
                raise CheckFailure(f"duplicate nickname: {value}")
            nicknames.add(value)
    unexpected = sorted(
        path.name
        for path in agents_dir.glob("teamwork-*.toml")
        if path.name not in expected
    )
    if unexpected:
        raise CheckFailure(f"unexpected Teamwork profiles: {', '.join(unexpected)}")
    return len(expected), len(nicknames)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agents-dir", type=Path, default=Path.home() / ".codex/agents")
    parser.add_argument("--config", type=Path, default=Path.home() / ".codex/config.toml")
    parser.add_argument("--profiles-only", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--skip-prompt", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--timeout-seconds", type=float, help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        profile_count, nickname_count = validate_profiles(args.agents_dir.resolve())
        result: dict[str, object] = {
            "status": "ok",
            "profiles": profile_count,
            "nicknames": nickname_count,
            "agent_routing": "optional",
        }
        if not args.profiles_only:
            routing = inspect_config(args.config)
            result["routing"] = routing.to_dict()
    except (CheckFailure, RoutingConfigError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for key, value in result.items():
            print(f"{key.upper()}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
