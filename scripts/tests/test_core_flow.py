from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]


class CoreFlowTests(unittest.TestCase):
    def test_writer_and_plain_markdown_document_templates_are_complete(self) -> None:
        topology = json.loads((ROOT / "config/teamwork-topology.json").read_text(encoding="utf-8"))
        agents = {row["name"]: row["templates"] for row in topology["agents"]}
        self.assertEqual(
            agents["writer"],
            {
                "codex": "templates/codex-agents/teamwork-writer.toml",
                "cursor": "templates/cursor-agents/writer.md",
                "claude": "templates/claude-agents/writer.md",
            },
        )
        writer = (ROOT / agents["writer"]["codex"]).read_text(encoding="utf-8")
        self.assertIn('model = "gpt-5.6-luna"', writer)
        self.assertIn('model_reasoning_effort = "xhigh"', writer)
        self.assertIn('service_tier = "default"', writer)
        self.assertIn('sandbox_mode = "workspace-write"', writer)

        documents = {row["name"]: row["path"] for row in topology["document_templates"]}
        self.assertEqual(
            set(documents),
            {"discussion", "research", "debug", "plan", "review", "report"},
        )
        for path in documents.values():
            template = (ROOT / path).read_text(encoding="utf-8")
            self.assertTrue(template.startswith("# "), path)
            self.assertIn("## History", template, path)
            self.assertIn("Append only", template, path)

    def test_writer_document_resources_resolve_after_copy_install(self) -> None:
        expected = {
            "teamwork-collaborate": "references/discussion.md",
            "teamwork-research": "references/research.md",
            "teamwork-debug": "references/debug.md",
            "teamwork-plan": "references/plan.md",
            "teamwork-review": "references/review.md",
            "teamwork-goal": "references/report.md",
            "teamwork-init": "references/report.md",
            "teamwork-update": "references/report.md",
        }
        with tempfile.TemporaryDirectory() as raw:
            env = os.environ.copy()
            env["HOME"] = raw
            env["CODEX_HOME"] = str(Path(raw) / ".codex")
            result = subprocess.run(
                [
                    str(ROOT / "install.sh"),
                    "--copy",
                    "--no-notifications",
                    "--no-codex-routing",
                    "codex",
                ],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            installed = Path(raw) / ".agents/skills"
            for skill, reference in expected.items():
                skill_root = installed / skill
                skill_text = (skill_root / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn(f"`{reference}`", skill_text)
                self.assertTrue((skill_root / reference).is_file(), f"{skill}/{reference}")

            report_texts = {
                (installed / skill / "references/report.md").read_text(encoding="utf-8")
                for skill in ("teamwork-goal", "teamwork-init", "teamwork-update")
            }
            self.assertEqual(len(report_texts), 1)

    def test_schema_index_and_migration_runtime_remain_absent(self) -> None:
        retired = (
            "scripts/migrate-teamwork-documents.py",
            "scripts/teamwork_index_v4.py",
            "scripts/teamwork-documents-schema.json",
        )
        for path in retired:
            self.assertFalse((ROOT / path).exists(), path)

    def test_project_init_is_idempotent_and_stateless(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            project = Path(raw)
            command = [
                sys.executable,
                str(ROOT / "scripts/init-project-files.py"),
                "--project-root",
                str(project),
                "initialize",
            ]
            subprocess.run(command, check=True)
            subprocess.run(command, check=True)
            agents = (project / "AGENTS.md").read_text(encoding="utf-8")
            self.assertEqual(agents.count("<!-- TEAMWORK_PROJECT_START -->"), 1)
            self.assertIn("no required project-local workflow or state", agents)
            self.assertFalse((project / "docs/teamwork").exists())

    def test_readiness_is_informational(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            env = os.environ.copy()
            env["HOME"] = raw
            env["CODEX_HOME"] = str(Path(raw) / ".codex")
            result = subprocess.run(
                [str(ROOT / "scripts/check-update.sh"), "--readiness"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("INSTALL_STATE=partial", result.stdout)
            self.assertIn("BLOCKS_OTHER_WORK=no", result.stdout)


if __name__ == "__main__":
    unittest.main()
