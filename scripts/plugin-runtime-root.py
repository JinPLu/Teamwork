#!/usr/bin/env python3
"""Print the containing Teamwork runtime root after validating its boundary.

Marketplace cache copies carry a runtime marker and integrity manifest. Source
checkouts do not carry the marker, but may still resolve as a development root
when their manifests and executable runtime files are internally consistent.
"""

from __future__ import annotations

import hashlib
import json
import stat
from pathlib import Path


PLUGIN_NAME = "teamwork-skill"
RUNTIME_MARKER = "TEAMWORK_CODEX_PLUGIN_RUNTIME=1\n"
RUNTIME_INTEGRITY_MANIFEST = ".teamwork-runtime-integrity.json"
RUNTIME_INTEGRITY_EXCLUDED_FILES = {RUNTIME_INTEGRITY_MANIFEST}
TRANSIENT_NAMES = {"__pycache__"}
TRANSIENT_SUFFIXES = (".pyc", ".pyo")
SOURCE_REQUIRED_RUNTIME_FILES = {
    "install.sh",
    "scripts/check-update.sh",
    "scripts/discussion-transaction.py",
    "scripts/init-project-files.py",
    "scripts/teamwork-case-migration.py",
    "scripts/validate_teamwork_index.py",
    "scripts/plugin-runtime-root.py",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"not a Teamwork plugin runtime: {path} is not an object")
    return value


def require_regular_single_link(path: Path) -> None:
    try:
        info = path.lstat()
    except OSError as exc:
        raise SystemExit(f"not a Teamwork plugin runtime: missing {path}") from exc
    if not stat.S_ISREG(info.st_mode):
        raise SystemExit(f"not a Teamwork plugin runtime: non-regular runtime file {path}")
    if info.st_nlink != 1:
        raise SystemExit(f"not a Teamwork plugin runtime: multi-link runtime file {path}")


def runtime_integrity_paths(root: Path) -> set[str]:
    paths: set[str] = set()
    for path in root.rglob("*"):
        rel = path.relative_to(root).as_posix()
        if rel in RUNTIME_INTEGRITY_EXCLUDED_FILES:
            continue
        if path.name in TRANSIENT_NAMES or path.suffix in TRANSIENT_SUFFIXES:
            continue
        info = path.lstat()
        if stat.S_ISDIR(info.st_mode):
            continue
        if not stat.S_ISREG(info.st_mode):
            raise SystemExit(f"not a Teamwork plugin runtime: unsupported runtime entry {rel}")
        paths.add(rel)
    return paths


def read_version(root: Path) -> str:
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    if not version:
        raise SystemExit("not a Teamwork plugin runtime: empty VERSION")
    return version


def validate_manifests(root: Path, version: str) -> dict[str, object]:
    manifest = load_json(root / ".codex-plugin" / "plugin.json")
    if manifest.get("name") != PLUGIN_NAME or manifest.get("version") != version:
        raise SystemExit("not a Teamwork plugin runtime: Codex manifest name/version mismatch")
    claude_manifest = root / ".claude-plugin" / "plugin.json"
    if claude_manifest.exists():
        claude = load_json(claude_manifest)
        if claude.get("name") != PLUGIN_NAME or claude.get("version") != version:
            raise SystemExit("not a Teamwork source root: Claude manifest name/version mismatch")
    return manifest


def validate_runtime_integrity(root: Path, version: str) -> None:
    integrity = load_json(root / RUNTIME_INTEGRITY_MANIFEST)
    if set(integrity) != {"schema_version", "version", "marker", "manifest_sha256", "files"}:
        raise SystemExit("not a Teamwork plugin runtime: integrity schema mismatch")
    if integrity.get("schema_version") != 1 or integrity.get("version") != version:
        raise SystemExit("not a Teamwork plugin runtime: integrity version mismatch")
    if integrity.get("marker") != RUNTIME_MARKER.rstrip("\n"):
        raise SystemExit("not a Teamwork plugin runtime: integrity marker mismatch")
    if integrity.get("manifest_sha256") != sha256_file(root / ".codex-plugin" / "plugin.json"):
        raise SystemExit("not a Teamwork plugin runtime: manifest hash mismatch")
    files = integrity.get("files")
    if not isinstance(files, dict):
        raise SystemExit("not a Teamwork plugin runtime: integrity file inventory mismatch")
    actual_files = runtime_integrity_paths(root)
    if set(files) != actual_files:
        raise SystemExit("not a Teamwork plugin runtime: integrity file inventory mismatch")
    for rel, expected in files.items():
        if not isinstance(expected, dict):
            raise SystemExit(f"not a Teamwork plugin runtime: invalid integrity entry {rel}")
        if set(expected) != {"sha256", "mode"}:
            raise SystemExit(f"not a Teamwork plugin runtime: invalid integrity entry {rel}")
        path = root / rel
        require_regular_single_link(path)
        if expected.get("sha256") != sha256_file(path):
            raise SystemExit(f"not a Teamwork plugin runtime: runtime hash mismatch for {rel}")
        mode = expected.get("mode")
        actual_mode = f"{path.stat().st_mode & 0o777:04o}"
        if mode != actual_mode:
            raise SystemExit(f"not a Teamwork plugin runtime: runtime mode mismatch for {rel}")


def validate_source_checkout(root: Path, version: str) -> None:
    if not (root / ".git").exists():
        raise SystemExit("not a Teamwork Marketplace runtime or source checkout")
    validate_manifests(root, version)
    for rel in SOURCE_REQUIRED_RUNTIME_FILES:
        require_regular_single_link(root / rel)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    marker = root / ".teamwork-plugin-runtime"
    try:
        version = read_version(root)
        validate_manifests(root, version)
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"not a Teamwork plugin runtime: {exc}") from exc
    if marker.exists():
        if marker.read_text(encoding="utf-8") != RUNTIME_MARKER:
            raise SystemExit("not a Teamwork Marketplace runtime: marker mismatch")
        validate_runtime_integrity(root, version)
    else:
        validate_source_checkout(root, version)
    print(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
