#!/usr/bin/env python3
"""Build the tracked Codex Marketplace bundle from Teamwork's canonical files.

The Marketplace package is intentionally a checked-in release artifact: users
install the cache copy, not a Teamwork checkout.  Keeping the copy deterministic
means contributors edit the canonical sources and regenerate it instead of
patching files under ``plugins/teamwork-skill`` by hand.
"""

from __future__ import annotations

import argparse
import filecmp
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path


PLUGIN_NAME = "teamwork-skill"
RUNTIME_MARKER = "TEAMWORK_CODEX_PLUGIN_RUNTIME=1\n"
COPY_ITEMS = (
    ("VERSION", "VERSION"),
    (".codex-plugin", ".codex-plugin"),
    ("skills", "skills"),
    ("install.sh", "install.sh"),
    ("scripts/install", "scripts/install"),
    ("scripts/check-update.sh", "scripts/check-update.sh"),
    ("scripts/check-codex-routing.py", "scripts/check-codex-routing.py"),
    ("scripts/codex_routing_config.py", "scripts/codex_routing_config.py"),
    ("scripts/configure-codex-routing.py", "scripts/configure-codex-routing.py"),
    ("scripts/configure-notifications.py", "scripts/configure-notifications.py"),
    ("scripts/init-project.sh", "scripts/init-project.sh"),
    ("scripts/init-project-files.py", "scripts/init-project-files.py"),
    ("scripts/plugin-activation.py", "scripts/plugin-activation.py"),
    ("scripts/validate_teamwork_index.py", "scripts/validate_teamwork_index.py"),
    ("templates/codex-agents", "templates/codex-agents"),
    ("hooks/notify.py", "hooks/notify.py"),
)
EXPECTED_SKILLS = (
    "using-teamwork",
    "grill-me",
    "teamwork-debug",
    "teamwork-init",
    "teamwork-goal",
    "teamwork-research",
    "teamwork-plan",
    "teamwork-execute",
    "teamwork-review",
    "teamwork-update",
)
TRANSIENT_NAMES = {"__pycache__"}
TRANSIENT_SUFFIXES = (".pyc", ".pyo")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail when the tracked bundle differs from canonical sources",
    )
    return parser.parse_args()


def copy_item(source: Path, destination: Path) -> None:
    if not source.exists():
        raise SystemExit(f"missing canonical plugin input: {source}")
    if source.is_dir():
        # Python bytecode is a local execution by-product, never a plugin
        # resource.  Ignoring it here keeps the checked-in bundle stable even
        # when a maintainer has recently run the skill helpers.
        shutil.copytree(
            source,
            destination,
            symlinks=True,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
        )
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination, follow_symlinks=False)


def validate_marketplace(root: Path) -> None:
    path = root / ".agents/plugins/marketplace.json"
    try:
        marketplace = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"invalid Marketplace manifest {path}: {exc}") from exc
    expected = {
        "name": PLUGIN_NAME,
        "source": {"source": "local", "path": f"./plugins/{PLUGIN_NAME}"},
        "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
        "category": "Productivity",
    }
    if marketplace.get("name") != "teamwork":
        raise SystemExit("Marketplace name must be 'teamwork'")
    if marketplace.get("interface", {}).get("displayName") != "Teamwork":
        raise SystemExit("Marketplace display name must be 'Teamwork'")
    entries = marketplace.get("plugins")
    if entries != [expected]:
        raise SystemExit("Marketplace must contain the exact teamwork-skill entry")


def validate_source(root: Path) -> None:
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    try:
        manifest = json.loads((root / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"invalid canonical plugin manifest: {exc}") from exc
    if manifest.get("name") != PLUGIN_NAME or manifest.get("version") != version:
        raise SystemExit("canonical plugin manifest name/version must match VERSION")
    prompts = manifest.get("interface", {}).get("defaultPrompt")
    if not isinstance(prompts, list) or len(prompts) != 3:
        raise SystemExit("canonical plugin manifest must expose exactly three default prompts")
    validate_marketplace(root)


def build_stage(root: Path, parent: Path) -> Path:
    stage_parent = Path(tempfile.mkdtemp(prefix=f".{PLUGIN_NAME}.build-", dir=parent))
    stage = stage_parent / PLUGIN_NAME
    try:
        stage.mkdir()
        for source_rel, destination_rel in COPY_ITEMS:
            copy_item(root / source_rel, stage / destination_rel)
        (stage / ".teamwork-plugin-runtime").write_text(RUNTIME_MARKER, encoding="utf-8")
        validate_bundle(stage, root)
        return stage
    except BaseException:
        shutil.rmtree(stage_parent, ignore_errors=True)
        raise


def validate_bundle(bundle: Path, root: Path) -> None:
    manifest_path = bundle / ".codex-plugin/plugin.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_manifest = json.loads((root / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
    if manifest != source_manifest:
        raise SystemExit("bundle manifest drifted from canonical .codex-plugin/plugin.json")
    if "hooks" in manifest:
        raise SystemExit("bundle manifest must not declare hooks")
    actual_skills = tuple(sorted(path.name for path in (bundle / "skills").iterdir() if path.is_dir()))
    if actual_skills != tuple(sorted(EXPECTED_SKILLS)):
        raise SystemExit("bundle must contain exactly the ten public Teamwork skills")
    if (bundle / "hooks/hooks.json").exists():
        raise SystemExit("bundle must not carry plugin-bundled hooks/hooks.json")
    if not (bundle / "hooks/notify.py").is_file():
        raise SystemExit("bundle is missing the notification runtime")
    if (bundle / ".teamwork-plugin-runtime").read_text(encoding="utf-8") != RUNTIME_MARKER:
        raise SystemExit("bundle runtime marker is invalid")
    for path in bundle.rglob("*"):
        if path.name in TRANSIENT_NAMES or path.suffix in TRANSIENT_SUFFIXES:
            raise SystemExit(f"bundle must not contain transient runtime output: {path}")
    for executable in (
        "install.sh",
        "scripts/check-update.sh",
        "scripts/init-project.sh",
        "skills/using-teamwork/scripts/discussion-transaction.py",
        "skills/using-teamwork/scripts/plugin-runtime-root.py",
    ):
        path = bundle / executable
        if not path.is_file() or not os.access(path, os.X_OK):
            raise SystemExit(f"bundle runtime executable is missing or not executable: {executable}")


def tree_entries(root: Path) -> dict[str, tuple[str, bytes | str, int]]:
    entries: dict[str, tuple[str, bytes | str, int]] = {}
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        mode = path.lstat().st_mode & 0o777
        if path.is_symlink():
            entries[rel] = ("link", os.readlink(path), mode)
        elif path.is_dir():
            entries[rel] = ("dir", "", mode)
        elif path.is_file():
            entries[rel] = ("file", path.read_bytes(), mode)
        else:
            raise SystemExit(f"unsupported bundle entry: {path}")
    return entries


def bundle_matches(current: Path, staged: Path) -> bool:
    if not current.is_dir():
        return False
    # filecmp keeps the common path cheap; the full signature below also checks
    # permissions and catches untracked hand edits deterministically.
    if filecmp.dircmp(current, staged).left_only or filecmp.dircmp(current, staged).right_only:
        return False
    return tree_entries(current) == tree_entries(staged)


def replace_bundle(stage: Path, target: Path) -> None:
    backup = target.parent / f".{PLUGIN_NAME}.previous-{os.getpid()}"
    if backup.exists():
        shutil.rmtree(backup)
    try:
        if target.exists():
            os.replace(target, backup)
        os.replace(stage, target)
    except BaseException:
        if not target.exists() and backup.exists():
            os.replace(backup, target)
        raise
    finally:
        if backup.exists() and target.exists():
            shutil.rmtree(backup)


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    target = root / "plugins" / PLUGIN_NAME
    target.parent.mkdir(parents=True, exist_ok=True)
    validate_source(root)
    stage = build_stage(root, target.parent)
    stage_parent = stage.parent
    try:
        if args.check:
            if not bundle_matches(target, stage):
                print("Codex plugin bundle is out of date; run ./scripts/build-codex-plugin.py", file=sys.stderr)
                return 1
            print("Codex plugin bundle is current")
            return 0
        replace_bundle(stage, target)
        print(f"Built Codex plugin bundle: {target}")
        return 0
    finally:
        shutil.rmtree(stage_parent, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
