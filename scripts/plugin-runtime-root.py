#!/usr/bin/env python3
"""Print the containing Teamwork runtime root after validating its layout."""

from __future__ import annotations

import json
import stat
from pathlib import Path
from typing import Any


PLUGIN_NAME = "teamwork-skill"
RUNTIME_MARKER = "TEAMWORK_CODEX_PLUGIN_RUNTIME=1\n"
SUPPORTED_AGENT_HOSTS = frozenset({"codex", "cursor", "claude"})
REQUIRED_RUNTIME_FILES = {
    "install.sh",
    "policy/teamwork-global.md",
    "config/teamwork-topology.json",
    ".codex-plugin/plugin.json",
    "scripts/check-update.sh",
    "scripts/init-project-files.py",
    "scripts/plugin-activation.py",
    "scripts/plugin-runtime-root.py",
    "hooks/notify.py",
}


def load_json(path: Path) -> dict[str, Any]:
    require_regular_file(path)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"not a Teamwork plugin runtime: {path} is not an object")
    return value


def require_regular_file(path: Path) -> None:
    try:
        info = path.lstat()
    except OSError as exc:
        raise SystemExit(f"not a Teamwork plugin runtime: missing {path}") from exc
    if not stat.S_ISREG(info.st_mode):
        raise SystemExit(f"not a Teamwork plugin runtime: non-regular runtime file {path}")


def validate_manifests(root: Path) -> None:
    manifest = load_json(root / ".codex-plugin" / "plugin.json")
    if manifest.get("name") != PLUGIN_NAME:
        raise SystemExit("not a Teamwork plugin runtime: unexpected Codex manifest")
    claude_manifest = root / ".claude-plugin" / "plugin.json"
    if claude_manifest.exists() or claude_manifest.is_symlink():
        claude = load_json(claude_manifest)
        if claude.get("name") != PLUGIN_NAME:
            raise SystemExit("not a Teamwork plugin runtime: unexpected Claude manifest")


def _relative_file(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise SystemExit(f"not a Teamwork plugin runtime: invalid {label}")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise SystemExit(f"not a Teamwork plugin runtime: invalid {label}")
    return path.as_posix()


def validate_topology_layout(root: Path) -> None:
    topology = load_json(root / "config" / "teamwork-topology.json")
    skills = topology.get("public_skills")
    agents = topology.get("agents")
    if not isinstance(skills, list) or not skills or not isinstance(agents, list) or not agents:
        raise SystemExit("not a Teamwork plugin runtime: incomplete topology inventory")
    for row in skills:
        if not isinstance(row, dict):
            raise SystemExit("not a Teamwork plugin runtime: invalid skill topology")
        require_regular_file(root / _relative_file(row.get("path"), "skill path"))
    for row in agents:
        if not isinstance(row, dict) or not isinstance(row.get("templates"), dict):
            raise SystemExit("not a Teamwork plugin runtime: invalid agent topology")
        templates = row["templates"]
        hosts = set(templates)
        # Validate each declared host file. Do not require {codex,cursor,claude}
        # on every agent: Codex is the supported minimum when present, and a
        # host may be omitted when the topology row intentionally drops it.
        # Explorer therefore passes with only a Codex template.
        if not hosts or not hosts.issubset(SUPPORTED_AGENT_HOSTS):
            raise SystemExit("not a Teamwork plugin runtime: invalid agent host topology")
        for host, relative in templates.items():
            require_regular_file(root / _relative_file(relative, f"{host} agent template"))


def validate_runtime_root(root: Path) -> None:
    marker = root / ".teamwork-plugin-runtime"
    if marker.exists() or marker.is_symlink():
        require_regular_file(marker)
        if marker.read_text(encoding="utf-8") != RUNTIME_MARKER:
            raise SystemExit("not a Teamwork Marketplace runtime: marker mismatch")
    elif not (root / ".git").is_dir():
        raise SystemExit("not a Teamwork Marketplace runtime or source checkout")

    validate_manifests(root)
    for relative in REQUIRED_RUNTIME_FILES:
        require_regular_file(root / relative)
    validate_topology_layout(root)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    try:
        validate_runtime_root(root)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"not a Teamwork plugin runtime: {exc}") from exc
    print(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
