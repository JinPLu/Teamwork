#!/usr/bin/env python3
"""Measure real host instruction paths and keep repository-wide totals as telemetry."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
ENFORCED_LIMITS = {
    # These surfaces can be loaded together in real use. The complete
    # repository union and all ten full skills are telemetry only because host
    # template families are mutually exclusive and skills are loaded on demand.
    "global_policy_codex": {"words": 430, "bytes": 3800},
    "global_policy_cursor": {"words": 430, "bytes": 3800},
    "global_policy_claude": {"words": 430, "bytes": 3800},
    "max_single_skill": {"words": 1150, "bytes": 8500},
    "max_skill_bundle": {"words": 1850, "bytes": 13500},
    "max_role_template": {"words": 330, "bytes": 2500},
    "skill_discovery_catalog": {"words": 650, "bytes": 4500},
    "project_instruction_block": {"words": 220, "bytes": 1700},
    "repository_instructions": {"words": 750, "bytes": 5500},
    "runtime_memory_readme": {"words": 320, "bytes": 2300},
    "runtime_memory_index": {"words": 200, "bytes": 1800},
    "worst_static_root_path": {"words": 3300, "bytes": 25000},
    "worst_static_leaf_path": {"words": 3200, "bytes": 24000},
    "worst_repository_root_path": {"words": 3900, "bytes": 30000},
}
CANONICAL_SKILL_COUNT = 10
CANONICAL_REFERENCE_COUNT = 4

# Backward-compatible name for tests and callers. Values are enforced limits,
# not telemetry totals.
COMPACTNESS_LIMITS = ENFORCED_LIMITS

sys.path.insert(0, str(ROOT / "scripts"))
from teamwork_tooling.evaluation.sources import validate_skill_topology  # noqa: E402


def normalized(text: str) -> str:
    return " ".join(text.split())


def size(text: str) -> dict[str, int]:
    value = normalized(text)
    return {"words": len(value.split()), "bytes": len(value.encode("utf-8"))}


def manifest_interface(path: Path) -> str:
    interface = json.loads(path.read_text(encoding="utf-8"))["interface"]
    return "\n".join(
        [
            interface.get("shortDescription", ""),
            interface.get("longDescription", ""),
            *interface.get("defaultPrompt", []),
        ]
    )


def generated_surfaces() -> dict[str, str]:
    with tempfile.TemporaryDirectory() as temp:
        # init-project rejects lexical symlink ancestors so a caller cannot
        # redirect writes outside its declared project boundary. macOS exposes
        # the temporary root through /var -> /private/var, so use its physical
        # spelling for this controlled fixture.
        temp_root = Path(temp).resolve()
        project = temp_root / "project"
        home = temp_root / "home"
        project.mkdir()
        home.mkdir()
        env = os.environ.copy()
        env["HOME"] = str(home)
        subprocess.run(
            [
                str(ROOT / "scripts/init-project.sh"),
                "--project-root",
                str(project),
                "--copy",
                "--no-codegraph",
                "--no-cursor-policy-copy",
            ],
            cwd=ROOT,
            env=env,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        agents = (project / "AGENTS.md").read_text(encoding="utf-8")
        match = re.search(
            r"<!-- TEAMWORK_PROJECT_START -->(.*?)<!-- TEAMWORK_PROJECT_END -->",
            agents,
            re.DOTALL,
        )
        if not match:
            raise RuntimeError("generated AGENTS.md lacks the Teamwork project block")
        return {
            "project_block": match.group(1),
            "memory_readme": (project / "docs/teamwork/README.md").read_text(encoding="utf-8"),
            "memory_index": (project / "docs/teamwork/index.json").read_text(encoding="utf-8"),
        }


def skill_bundle_text(skill_file: Path, behavior_refs: list[str]) -> str:
    skill_dir = skill_file.parent
    texts = [skill_file.read_text(encoding="utf-8")]
    prefix = f"skills/{skill_dir.name}/"
    for reference in behavior_refs:
        if reference.startswith(prefix):
            texts.append((ROOT / reference).read_text(encoding="utf-8"))
    return "\n".join(texts)


def skill_frontmatter_catalog(skill_files: list[Path]) -> str:
    entries: list[str] = []
    for path in sorted(skill_files):
        lines = path.read_text(encoding="utf-8").splitlines()
        try:
            end = lines.index("---", 1)
        except ValueError as exc:
            raise RuntimeError(f"{path} lacks closed frontmatter") from exc
        entries.extend(lines[1:end])
    return "\n".join(entries)


def rendered_policy(platform: str) -> str:
    rendered = subprocess.run(
        [str(ROOT / "install.sh"), f"{platform}-policy"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    match = re.search(
        rf"<!-- TEAMWORK_{platform.upper()}_GLOBAL_START -->(.*?)"
        rf"<!-- TEAMWORK_{platform.upper()}_GLOBAL_END -->",
        rendered,
        re.DOTALL,
    )
    if not match:
        raise RuntimeError(f"rendered {platform} policy lacks managed markers")
    return match.group(1)


def max_surface_size(items: list[tuple[str, str]]) -> dict[str, object]:
    word_path, word_text = max(items, key=lambda item: size(item[1])["words"])
    byte_path, byte_text = max(items, key=lambda item: size(item[1])["bytes"])
    return {
        "words": size(word_text)["words"],
        "words_path": word_path,
        "bytes": size(byte_text)["bytes"],
        "bytes_path": byte_path,
    }


def measure() -> dict[str, object]:
    surfaces: list[str] = []
    for base, patterns in (
        (ROOT / "skills", ("*.md", "*.json")),
        (ROOT / "templates", ("*.md", "*.toml")),
    ):
        for pattern in patterns:
            surfaces.extend(
                path.read_text(encoding="utf-8")
                for path in sorted(base.rglob(pattern))
            )
    surfaces.extend(
        manifest_interface(ROOT / path)
        for path in (".codex-plugin/plugin.json", ".claude-plugin/plugin.json")
    )
    generated = generated_surfaces()
    surfaces.extend(generated.values())

    topology = validate_skill_topology(ROOT)
    skill_files = [ROOT / "skills" / skill / "SKILL.md" for skill in topology["skills"]]
    skill_texts = [path.read_text(encoding="utf-8") for path in skill_files]
    skill_sizes = [size(text) for text in skill_texts]
    behavior_refs = list(topology["behavior_references"])
    skill_bundles = [
        (path, skill_bundle_text(path, behavior_refs))
        for path in skill_files
    ]
    role_templates = [
        path
        for base in ("codex-agents", "cursor-agents", "claude-agents")
        for path in (ROOT / "templates" / base).iterdir()
        if path.is_file() and path.suffix in {".md", ".toml"}
    ]
    policies = {platform: rendered_policy(platform) for platform in ("codex", "cursor", "claude")}
    discovery_catalog = skill_frontmatter_catalog(skill_files)
    repository_instructions = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    worst_static_candidates = [
        (
            f"{platform}+catalog+project_block+{path.relative_to(ROOT).as_posix()}+runtime_memory",
            "\n".join(
                [
                    policy,
                    discovery_catalog,
                    generated["project_block"],
                    bundle,
                    generated["memory_index"],
                    generated["memory_readme"],
                ]
            ),
        )
        for platform, policy in policies.items()
        for path, bundle in skill_bundles
    ]
    worst_leaf_candidates = [
        (
            f"{platform}+catalog+project_block+{path.relative_to(ROOT).as_posix()}+{role.relative_to(ROOT).as_posix()}",
            "\n".join(
                [
                    policy,
                    discovery_catalog,
                    generated["project_block"],
                    bundle,
                    role.read_text(encoding="utf-8"),
                ]
            ),
        )
        for platform, policy in policies.items()
        for path, bundle in skill_bundles
        for role in role_templates
    ]
    worst_repository_candidates = [
        (
            f"{platform}+repository_instructions+catalog+{path.relative_to(ROOT).as_posix()}+runtime_memory",
            "\n".join(
                [
                    policy,
                    repository_instructions,
                    discovery_catalog,
                    bundle,
                    generated["memory_index"],
                    generated["memory_readme"],
                ]
            ),
        )
        for platform, policy in policies.items()
        for path, bundle in skill_bundles
    ]

    enforced = {
        "global_policy_codex": size(policies["codex"]),
        "global_policy_cursor": size(policies["cursor"]),
        "global_policy_claude": size(policies["claude"]),
        "max_single_skill": max_surface_size(
            [(path.relative_to(ROOT).as_posix(), path.read_text(encoding="utf-8")) for path in skill_files]
        ),
        "max_skill_bundle": max_surface_size(
            [(path.relative_to(ROOT).as_posix(), text) for path, text in skill_bundles]
        ),
        "max_role_template": max_surface_size(
            [(path.relative_to(ROOT).as_posix(), path.read_text(encoding="utf-8")) for path in role_templates]
        ),
        "skill_discovery_catalog": size(discovery_catalog),
        "project_instruction_block": size(generated["project_block"]),
        "repository_instructions": size(repository_instructions),
        "runtime_memory_readme": size(generated["memory_readme"]),
        "runtime_memory_index": size(generated["memory_index"]),
        "worst_static_root_path": max_surface_size(worst_static_candidates),
        "worst_static_leaf_path": max_surface_size(worst_leaf_candidates),
        "worst_repository_root_path": max_surface_size(worst_repository_candidates),
    }
    telemetry = {
        "union": {"surfaces": len(surfaces), **size("\n".join(normalized(x) for x in surfaces))},
        "skills": {
            "surfaces": len(skill_texts),
            **size("\n".join(normalized(text) for text in skill_texts)),
            "max_skill_words": max(item["words"] for item in skill_sizes),
            "behavior_references": len(topology["behavior_references"]),
            "cross_skill_loads": len(topology["cross_skill_loads"]),
            "dependency_cycles": len(topology["cycles"]),
        },
    }
    return {"enforced": enforced, "telemetry": telemetry, "topology": topology}


def compactness_failures(result: dict[str, object]) -> list[str]:
    failures: list[str] = []
    enforced = result.get("enforced", result)
    assert isinstance(enforced, dict)
    for surface, limit in ENFORCED_LIMITS.items():
        measured = enforced[surface]
        assert isinstance(measured, dict)
        for metric in ("words", "bytes"):
            if int(measured[metric]) > limit[metric]:
                failures.append(
                    f"{surface} {metric} exceeds compactness limit: "
                    f"{measured[metric]} > {limit[metric]}"
                )
    telemetry = result.get("telemetry", result)
    assert isinstance(telemetry, dict)
    skills = telemetry["skills"]
    assert isinstance(skills, dict)
    # Callers that compare only byte/word ceilings may pass synthetic legacy
    # measurements. Topology is enforced whenever the real measurement fields
    # are present; the source validator independently enforces it on every eval.
    if "surfaces" in skills:
        if int(skills["surfaces"]) != CANONICAL_SKILL_COUNT:
            failures.append(
                "canonical skill inventory must contain "
                f"{CANONICAL_SKILL_COUNT} skills: {skills['surfaces']}"
            )
        if int(skills["behavior_references"]) != CANONICAL_REFERENCE_COUNT:
            failures.append(
                "canonical reference inventory must contain "
                f"{CANONICAL_REFERENCE_COUNT} references: {skills['behavior_references']}"
            )
        for metric in ("cross_skill_loads", "dependency_cycles"):
            if int(skills[metric]) != 0:
                failures.append(f"skill topology must keep {metric}=0: {skills[metric]}")
    return failures


# Kept as a narrow compatibility alias for callers that used the old helper.
def regressions(result: dict[str, object]) -> list[str]:
    return compactness_failures(result)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = measure()
    failures = compactness_failures(result)
    if args.json:
        print(json.dumps({"limits": ENFORCED_LIMITS, "measured": result, "failures": failures}, sort_keys=True))
    else:
        print("enforced:")
        enforced = result["enforced"]
        assert isinstance(enforced, dict)
        for surface in ENFORCED_LIMITS:
            print(f"  {surface}: {enforced[surface]} limit={ENFORCED_LIMITS[surface]}")
        print("telemetry:")
        telemetry = result["telemetry"]
        assert isinstance(telemetry, dict)
        for surface in ("union", "skills"):
            print(f"  {surface}: {telemetry[surface]}")
        for failure in failures:
            print(f"FAIL: {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
