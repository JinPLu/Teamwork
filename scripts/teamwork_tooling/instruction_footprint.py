#!/usr/bin/env python3
"""Measure always-loaded policy and runtime instruction footprint."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
BASELINE = {
    "union": {"words": 18142, "bytes": 132316},
    "codex": {"words": 182, "bytes": 1410},
    "cursor": {"words": 181, "bytes": 1404},
    "claude": {"words": 182, "bytes": 1409},
}


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
        temp_root = Path(temp)
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
                "--project-only",
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

    result: dict[str, object] = {
        "union": {"surfaces": len(surfaces), **size("\n".join(normalized(x) for x in surfaces))}
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


def regressions(result: dict[str, object]) -> list[str]:
    failures: list[str] = []
    for surface, baseline in BASELINE.items():
        measured = result[surface]
        assert isinstance(measured, dict)
        for metric in ("words", "bytes"):
            if int(measured[metric]) >= baseline[metric]:
                failures.append(
                    f"{surface} {metric} must decrease: "
                    f"{measured[metric]} >= {baseline[metric]}"
                )
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = measure()
    failures = regressions(result)
    if args.json:
        print(json.dumps({"baseline": BASELINE, "measured": result, "failures": failures}, sort_keys=True))
    else:
        for surface in ("union", "codex", "cursor", "claude"):
            print(f"{surface}: {result[surface]}")
        for failure in failures:
            print(f"FAIL: {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
