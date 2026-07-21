#!/usr/bin/env python3
"""Merge Teamwork-owned MCP server entries into Cursor mcp.json."""

from __future__ import annotations

import argparse
import json
import os
import stat
import sys
import tempfile
from pathlib import Path
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_SERVERS = REPOSITORY_ROOT / "templates" / "cursor-mcp" / "servers.json"
SIDECAR_VERSION = 1


class CursorMcpError(Exception):
    pass


def cursor_home(home: Path | None = None) -> Path:
    return (home or Path.home()) / ".cursor"


def default_mcp_config(home: Path | None = None) -> Path:
    return cursor_home(home) / "mcp.json"


def sidecar_path(home: Path | None = None) -> Path:
    return cursor_home(home) / ".teamwork-mcp.json"


def load_json(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CursorMcpError(f"cannot read {path}: {exc}") from exc
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CursorMcpError(f"malformed JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise CursorMcpError(f"top-level JSON value must be an object: {path}")
    return value


def refuse_unsafe_path(path: Path, *, label: str) -> None:
    if path.is_symlink():
        raise CursorMcpError(f"refusing to replace symlink: {label}: {path}")
    if path.exists() and not stat.S_ISREG(path.stat().st_mode):
        raise CursorMcpError(f"refusing to replace non-regular file: {label}: {path}")


def atomic_write(path: Path, text: str) -> None:
    refuse_unsafe_path(path, label=path.name)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    mode: int | None = None
    if path.exists():
        mode = stat.S_IMODE(path.stat().st_mode)
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            delete=False,
        ) as handle:
            handle.write(text)
            temporary = Path(handle.name)
        if mode is not None:
            temporary.chmod(mode)
        if path.is_symlink():
            raise CursorMcpError(f"refusing to replace symlink: {path}")
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def load_canonical_servers() -> dict[str, dict[str, Any]]:
    value = load_json(CANONICAL_SERVERS)
    if not isinstance(value, dict):
        raise CursorMcpError("canonical Teamwork MCP server definitions must be an object")
    servers: dict[str, dict[str, Any]] = {}
    for key, entry in value.items():
        if not isinstance(key, str) or not key:
            raise CursorMcpError("canonical MCP server names must be non-empty strings")
        if not isinstance(entry, dict):
            raise CursorMcpError(f"canonical MCP server {key!r} must be an object")
        servers[key] = json.loads(json.dumps(entry))
    return servers


def load_sidecar(home: Path | None) -> set[str]:
    path = sidecar_path(home)
    if not path.exists():
        return set()
    refuse_unsafe_path(path, label=".teamwork-mcp.json")
    payload = load_json(path)
    version = payload.get("version")
    servers = payload.get("servers")
    if version != SIDECAR_VERSION:
        raise CursorMcpError("unsupported Teamwork MCP ownership sidecar version")
    if not isinstance(servers, list) or not all(isinstance(item, str) and item for item in servers):
        raise CursorMcpError("Teamwork MCP ownership sidecar servers must be a non-empty string list")
    return set(servers)


def write_sidecar(home: Path | None, servers: set[str]) -> None:
    payload = {
        "version": SIDECAR_VERSION,
        "servers": sorted(servers),
    }
    atomic_write(
        sidecar_path(home),
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
    )


def remove_sidecar(home: Path | None) -> None:
    path = sidecar_path(home)
    if not path.exists():
        return
    refuse_unsafe_path(path, label=".teamwork-mcp.json")
    path.unlink()


def normalize_config(raw: dict[str, Any]) -> dict[str, Any]:
    servers = raw.get("mcpServers")
    if servers is None:
        return {"mcpServers": {}}
    if not isinstance(servers, dict):
        raise CursorMcpError("mcp.json mcpServers must be an object")
    return raw


def apply_config(
    *,
    config_path: Path,
    home: Path | None,
    force: bool,
    track_ownership: bool,
) -> dict[str, Any]:
    canonical = load_canonical_servers()
    owned = load_sidecar(home) if track_ownership else set()
    effective_force = force or not track_ownership
    if config_path.exists():
        refuse_unsafe_path(config_path, label="mcp.json")
        current = normalize_config(load_json(config_path))
    else:
        current = {"mcpServers": {}}

    servers = current.setdefault("mcpServers", {})
    if not isinstance(servers, dict):
        raise CursorMcpError("mcp.json mcpServers must be an object")

    changed = False
    for name, definition in canonical.items():
        if name in servers and not effective_force and name not in owned:
            continue
        if servers.get(name) == definition and (not track_ownership or name in owned):
            continue
        servers[name] = json.loads(json.dumps(definition))
        if track_ownership:
            owned.add(name)
        changed = True

    if changed or (track_ownership and not sidecar_path(home).exists() and owned):
        atomic_write(
            config_path,
            json.dumps(current, ensure_ascii=False, indent=2) + "\n",
        )
        if track_ownership:
            write_sidecar(home, owned)
    return current


def remove_config(*, config_path: Path, home: Path | None, track_ownership: bool) -> dict[str, Any]:
    owned = load_sidecar(home) if track_ownership else set(load_canonical_servers())
    if config_path.exists():
        refuse_unsafe_path(config_path, label="mcp.json")
        current = normalize_config(load_json(config_path))
    else:
        current = {"mcpServers": {}}

    servers = current.get("mcpServers")
    if not isinstance(servers, dict):
        raise CursorMcpError("mcp.json mcpServers must be an object")

    changed = False
    for name in sorted(owned):
        if name in servers:
            del servers[name]
            changed = True

    if changed:
        atomic_write(
            config_path,
            json.dumps(current, ensure_ascii=False, indent=2) + "\n",
        )
    if track_ownership:
        remove_sidecar(home)
    return current


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        help="Cursor MCP config path (default: ~/.cursor/mcp.json)",
    )
    parser.add_argument(
        "--home",
        type=Path,
        help="HOME directory for global ownership sidecar resolution (default: Path.home())",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--apply", action="store_true", help="add or refresh Teamwork MCP servers")
    mode.add_argument("--remove", action="store_true", help="remove Teamwork-owned MCP servers")
    parser.add_argument(
        "--force",
        action="store_true",
        help="refresh Teamwork-owned MCP servers even when already present",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    home = args.home.expanduser().resolve() if args.home else None
    config_path = (
        args.config.expanduser().resolve()
        if args.config
        else default_mcp_config(home)
    )
    track_ownership = args.config is None
    sidecar_home = home if track_ownership else None
    try:
        if args.remove:
            remove_config(
                config_path=config_path,
                home=sidecar_home,
                track_ownership=track_ownership,
            )
        else:
            apply_config(
                config_path=config_path,
                home=sidecar_home,
                force=args.force,
                track_ownership=track_ownership,
            )
    except CursorMcpError as exc:
        print(f"Teamwork Cursor MCP configuration refused: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
