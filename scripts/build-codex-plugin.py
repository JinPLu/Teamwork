#!/usr/bin/env python3
"""Build the tracked Codex Marketplace bundle from Teamwork's canonical files.

The Marketplace package is intentionally a checked-in release artifact: users
install the cache copy, not a Teamwork checkout.  Keeping the copy deterministic
means contributors edit the canonical sources and regenerate it instead of
patching files under ``plugins/teamwork-skill`` by hand.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path


PLUGIN_NAME = "teamwork-skill"
RUNTIME_MARKER = "TEAMWORK_CODEX_PLUGIN_RUNTIME=1\n"
TOPOLOGY_REL = "config/teamwork-topology.json"
MAX_DEFAULT_PROMPT_CHARS = 128
COPY_ITEMS = (
    ("VERSION", "VERSION"),
    (".codex-plugin", ".codex-plugin"),
    (TOPOLOGY_REL, TOPOLOGY_REL),
    ("skills", "skills"),
    ("policy/teamwork-global.md", "policy/teamwork-global.md"),
    ("install.sh", "install.sh"),
    ("scripts/install", "scripts/install"),
    ("scripts/check-update.sh", "scripts/check-update.sh"),
    ("scripts/teamwork_tooling/topology.py", "scripts/teamwork_tooling/topology.py"),
    ("scripts/check-codex-routing.py", "scripts/check-codex-routing.py"),
    ("scripts/codex_routing_config.py", "scripts/codex_routing_config.py"),
    ("scripts/configure-codex-routing.py", "scripts/configure-codex-routing.py"),
    ("scripts/configure-notifications.py", "scripts/configure-notifications.py"),
    ("scripts/init-project.sh", "scripts/init-project.sh"),
    ("scripts/init-project-files.py", "scripts/init-project-files.py"),
    ("scripts/plugin-activation.py", "scripts/plugin-activation.py"),
    ("scripts/plugin-runtime-root.py", "scripts/plugin-runtime-root.py"),
    ("templates/codex-agents", "templates/codex-agents"),
    ("templates/cursor-agents", "templates/cursor-agents"),
    ("templates/claude-agents", "templates/claude-agents"),
    ("hooks/notify.py", "hooks/notify.py"),
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


def load_topology(root: Path) -> dict[str, object]:
    path = root / TOPOLOGY_REL
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"invalid topology manifest {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit("topology manifest must be a JSON object")
    for key in ("public_skills", "agents", "owned_references", "document_templates"):
        if key not in value:
            raise SystemExit(f"topology manifest lacks {key}")
    return value


def expected_bundle_surfaces(
    root: Path,
) -> tuple[
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    dict[str, tuple[str, ...]],
    tuple[str, ...],
]:
    topology = load_topology(root)
    skills = tuple(sorted(row["name"] for row in topology["public_skills"]))
    references = tuple(sorted(topology["owned_references"]))
    metadata = tuple(sorted(f"skills/{name}/agents/openai.yaml" for name in skills))
    roles: dict[str, list[str]] = {"codex-agents": [], "cursor-agents": [], "claude-agents": []}
    host_directories = {"codex": "codex-agents", "cursor": "cursor-agents", "claude": "claude-agents"}
    for row in topology["agents"]:
        for host, path in row["templates"].items():
            directory = host_directories[host]
            roles[directory].append(Path(path).name)
    documents = tuple(sorted(row["path"] for row in topology["document_templates"]))
    return (
        skills,
        references,
        metadata,
        {directory: tuple(sorted(files)) for directory, files in roles.items()},
        documents,
    )


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
    topology = load_topology(root)
    declared_paths = [row["path"] for row in topology["public_skills"]]
    declared_paths.extend(topology["owned_references"])
    declared_paths.extend(row["path"] for row in topology["document_templates"])
    for row in topology["agents"]:
        declared_paths.extend(row["templates"].values())
    missing = [path for path in declared_paths if not (root / path).is_file()]
    if missing:
        raise SystemExit(f"topology declares missing canonical files: {', '.join(sorted(missing))}")
    for manifest_rel, label in (
        (".codex-plugin/plugin.json", "Codex"),
        (".claude-plugin/plugin.json", "Claude Code"),
    ):
        try:
            manifest = json.loads((root / manifest_rel).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SystemExit(f"invalid canonical {label} plugin manifest: {exc}") from exc
        if manifest.get("name") != PLUGIN_NAME:
            raise SystemExit(f"canonical {label} plugin manifest has an unexpected name")
        prompts = manifest.get("interface", {}).get("defaultPrompt")
        if not isinstance(prompts, list) or not prompts:
            raise SystemExit(f"canonical {label} plugin manifest must expose default prompts")
        if any(not isinstance(prompt, str) or len(prompt) > MAX_DEFAULT_PROMPT_CHARS for prompt in prompts):
            raise SystemExit(
                f"canonical {label} plugin default prompts must be strings of at most "
                f"{MAX_DEFAULT_PROMPT_CHARS} characters"
            )
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
    (
        expected_skills,
        expected_references,
        expected_metadata,
        expected_roles,
        expected_documents,
    ) = expected_bundle_surfaces(root)
    if load_topology(bundle) != load_topology(root):
        raise SystemExit("bundle topology manifest drifted from canonical source")
    manifest_path = bundle / ".codex-plugin/plugin.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_manifest = json.loads((root / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
    if manifest != source_manifest:
        raise SystemExit("bundle manifest drifted from canonical .codex-plugin/plugin.json")
    if "hooks" in manifest:
        raise SystemExit("bundle manifest must not declare hooks")
    actual_skills = tuple(sorted(path.name for path in (bundle / "skills").iterdir() if path.is_dir()))
    if actual_skills != expected_skills:
        raise SystemExit("bundle skill inventory differs from the topology manifest")
    actual_references = tuple(
        sorted(
            path.relative_to(bundle).as_posix()
            for path in (bundle / "skills").rglob("*")
            if path.is_file() and "references" in path.relative_to(bundle).parts
        )
    )
    if actual_references != expected_references:
        raise SystemExit("bundle reference inventory differs from the topology manifest")
    actual_agent_metadata = tuple(
        sorted(
            path.relative_to(bundle).as_posix()
            for path in (bundle / "skills").rglob("*")
            if path.is_file() and "agents" in path.relative_to(bundle).parts
        )
    )
    if actual_agent_metadata != expected_metadata:
        raise SystemExit("bundle skill UI metadata differs from the topology manifest")
    for directory, expected_files in expected_roles.items():
        actual_files = tuple(
            sorted(path.name for path in (bundle / "templates" / directory).iterdir() if path.is_file())
        )
        if actual_files != expected_files:
            raise SystemExit(
                f"bundle templates/{directory} differs from the topology manifest"
            )
    if not set(expected_documents).issubset(actual_references):
        raise SystemExit("bundle Teamwork document templates are not self-contained Skill resources")
    if (bundle / "hooks/hooks.json").exists():
        raise SystemExit("bundle must not carry plugin-bundled hooks/hooks.json")
    if not (bundle / "hooks/notify.py").is_file():
        raise SystemExit("bundle is missing the notification runtime")
    if (bundle / ".teamwork-plugin-runtime").read_text(encoding="utf-8") != RUNTIME_MARKER:
        raise SystemExit("bundle runtime marker is invalid")
    if (bundle / ".teamwork-runtime-integrity.json").exists():
        raise SystemExit("bundle must not contain retired runtime integrity metadata")
    for required in ("policy/teamwork-global.md",):
        if not (bundle / required).is_file():
            raise SystemExit(f"bundle is missing current runtime surface: {required}")
    for path in bundle.rglob("*"):
        if path.name in TRANSIENT_NAMES or path.suffix in TRANSIENT_SUFFIXES:
            raise SystemExit(f"bundle must not contain transient runtime output: {path}")
    for executable in (
        "install.sh",
        "scripts/check-update.sh",
        "scripts/init-project.sh",
        "scripts/plugin-runtime-root.py",
    ):
        path = bundle / executable
        if not path.is_file() or not os.access(path, os.X_OK):
            raise SystemExit(f"bundle runtime executable is missing or not executable: {executable}")


def tree_entries(root: Path) -> dict[str, tuple[str, bytes | str, int]]:
    entries: dict[str, tuple[str, bytes | str, int]] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(part in TRANSIENT_NAMES for part in relative.parts) or path.suffix in TRANSIENT_SUFFIXES:
            continue
        rel = relative.as_posix()
        mode = path.lstat().st_mode & 0o777
        if path.is_symlink():
            entries[rel] = ("link", os.readlink(path), mode)
        elif path.is_dir():
            # Git and the Marketplace artifact carry files and symlinks, not
            # standalone directory entries. An empty local directory therefore
            # cannot make the published bundle stale.
            continue
        elif path.is_file():
            entries[rel] = ("file", path.read_bytes(), mode)
        else:
            raise SystemExit(f"unsupported bundle entry: {path}")
    return entries


def bundle_matches(current: Path, staged: Path) -> bool:
    if not current.is_dir():
        return False
    # Compare the generated tree directly, including permissions and symlinks.
    return tree_entries(current) == tree_entries(staged)


def remove_entry(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def replace_bundle(stage: Path, target: Path) -> None:
    """Synchronize the generated tree without renaming the tracked root.

    Directory-level swaps can leave the tracked bundle absent in
    file-provider-backed workspaces.  The stage has already been fully
    validated, so update the stable root in place while still removing stale
    generated entries.
    """

    target.mkdir(parents=True, exist_ok=True)
    staged_paths = {path.relative_to(stage) for path in stage.rglob("*")}
    current_paths = sorted(
        (path.relative_to(target) for path in target.rglob("*")),
        key=lambda path: len(path.parts),
        reverse=True,
    )
    for relative in current_paths:
        if relative not in staged_paths:
            remove_entry(target / relative)

    for source in sorted(stage.rglob("*"), key=lambda path: len(path.relative_to(stage).parts)):
        relative = source.relative_to(stage)
        destination = target / relative
        if source.is_symlink():
            if destination.exists() or destination.is_symlink():
                remove_entry(destination)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.symlink_to(os.readlink(source))
        elif source.is_dir():
            if destination.is_symlink() or (destination.exists() and not destination.is_dir()):
                remove_entry(destination)
            destination.mkdir(parents=True, exist_ok=True)
        elif source.is_file():
            if destination.is_symlink() or (destination.exists() and destination.is_dir()):
                remove_entry(destination)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination, follow_symlinks=False)


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
