#!/usr/bin/env python3
"""Measure always-loaded policy and runtime instruction footprint."""

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
COMPACTNESS_LIMITS = {
    # The v4 architecture removes the router, generic Execute skill, and the
    # shared behavioral-reference graph. These ceilings intentionally make that
    # simplification observable without rewarding code-golf inside a skill.
    "union": {"words": 12500, "bytes": 95000},
    "skills": {"words": 6000, "bytes": 45000},
    "codex": {"words": 340, "bytes": 2800},
    "cursor": {"words": 350, "bytes": 2900},
    "claude": {"words": 340, "bytes": 2800},
}
MAX_SKILL_WORDS = 900
CANONICAL_SKILL_COUNT = 10
CANONICAL_REFERENCE_COUNT = 3

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


def generated_surfaces() -> list[str]:
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
        return [
            match.group(1),
            (project / "docs/teamwork/README.md").read_text(encoding="utf-8"),
            (project / "docs/teamwork/index.json").read_text(encoding="utf-8"),
        ]


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
    surfaces.extend(generated_surfaces())

    topology = validate_skill_topology(ROOT)
    skill_texts = [
        (ROOT / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
        for skill in topology["skills"]
    ]
    skill_sizes = [size(text) for text in skill_texts]
    result: dict[str, object] = {
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
    for platform in ("codex", "cursor", "claude"):
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
        result[platform] = size(match.group(1))
    return result


def compactness_failures(result: dict[str, object]) -> list[str]:
    failures: list[str] = []
    for surface, limit in COMPACTNESS_LIMITS.items():
        measured = result[surface]
        assert isinstance(measured, dict)
        for metric in ("words", "bytes"):
            if int(measured[metric]) > limit[metric]:
                failures.append(
                    f"{surface} {metric} exceeds compactness limit: "
                    f"{measured[metric]} > {limit[metric]}"
                )
    skills = result["skills"]
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
        if int(skills["max_skill_words"]) > MAX_SKILL_WORDS:
            failures.append(
                f"largest SKILL.md exceeds focused-skill limit: "
                f"{skills['max_skill_words']} > {MAX_SKILL_WORDS}"
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
        print(json.dumps({"limits": COMPACTNESS_LIMITS, "measured": result, "failures": failures}, sort_keys=True))
    else:
        for surface in ("union", "skills", "codex", "cursor", "claude"):
            print(f"{surface}: {result[surface]}")
        for failure in failures:
            print(f"FAIL: {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
