import copy
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "skills/using-teamwork/references/teamwork-index-template.json"
VALIDATOR = ROOT / "scripts/validate_teamwork_index.py"
INIT = ROOT / "scripts/init-project.sh"


class TeamworkIndexBudgetCompatibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.template = json.loads(TEMPLATE.read_text(encoding="utf-8"))

    def validate(self, data: dict) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.json"
            path.write_text(json.dumps(data) + "\n", encoding="utf-8")
            return subprocess.run(
                ["python3", str(VALIDATOR), str(path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

    def test_legacy_valid(self) -> None:
        fixture = copy.deepcopy(self.template)
        fixture["budgets"] = {
            "default_max_files": 5,
            "default_max_artifact_bodies": 2,
            "header_first": True,
        }
        result = self.validate(fixture)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_header_only_valid(self) -> None:
        result = self.validate(self.template)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_partial_invalid(self) -> None:
        fixture = copy.deepcopy(self.template)
        fixture["budgets"] = {"default_max_files": 5, "header_first": True}
        result = self.validate(fixture)
        self.assertNotEqual(result.returncode, 0)

    def test_wrong_hybrid_invalid(self) -> None:
        fixture = copy.deepcopy(self.template)
        fixture["budgets"] = {
            "default_max_files": 5,
            "default_max_artifact_bodies": 2,
            "header_first": True,
            "max_tokens": 1000,
        }
        result = self.validate(fixture)
        self.assertNotEqual(result.returncode, 0)


class TeamworkInitPreservationTests(unittest.TestCase):
    def run_init(self, project: Path, home: Path) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.update(
            {
                "HOME": str(home),
                "TEAMWORK_INIT_CODEGRAPH": "0",
                "TEAMWORK_INIT_CURSOR_POLICY_COPY": "0",
            }
        )
        return subprocess.run(
            [
                str(INIT),
                "--copy",
                "--no-codegraph",
                "--no-cursor-policy-copy",
                "--project-root",
                str(project),
            ],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_new_init_emits_header_only_and_minimal_agents_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            project = base / "project"
            home = base / "home"
            project.mkdir()
            home.mkdir()
            (project / "README.md").write_text("# Local Display Label\n", encoding="utf-8")
            (project / ".gitignore").write_text("# Keep this user rule\n", encoding="utf-8")

            result = self.run_init(project, home)
            self.assertEqual(result.returncode, 0, result.stderr)

            index = json.loads((project / "docs/teamwork/index.json").read_text(encoding="utf-8"))
            self.assertEqual(index["budgets"], {"header_first": True})
            self.assertEqual(index["project"]["name"], "Local Display Label")
            self.assertEqual(index["project"]["description"], "Local Teamwork memory index for this project.")

            agents = (project / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("Project label (local routing only): `Local Display Label`", agents)
            self.assertIn("docs/teamwork/index.json", agents)
            for unsupported in (
                "Project identity:",
                "CodeGraph:",
                "Docs MCP:",
                "Required values, credentials",
                "Keep volatile task progress",
            ):
                self.assertNotIn(unsupported, agents)

            gitignore = (project / ".gitignore").read_text(encoding="utf-8")
            self.assertIn("# Keep this user rule", gitignore)
            for local_package_path in (".agents/", ".codex/", ".cursor/", ".claude/"):
                self.assertNotIn(local_package_path, gitignore)
            for local_package_path in (
                project / ".agents",
                project / ".codex" / "agents",
                project / ".cursor" / "skills",
                project / ".claude" / "skills",
            ):
                self.assertFalse(local_package_path.exists(), local_package_path)

    def test_existing_index_byte_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            project = base / "project"
            memory = project / "docs/teamwork"
            home = base / "home"
            memory.mkdir(parents=True)
            home.mkdir()

            index_bytes = TEMPLATE.read_bytes()
            readme_bytes = b"# Existing runtime README\n\nKeep these exact bytes.\n"
            current_bytes = b"# Existing current state\n\nKeep these exact bytes.\n"
            (memory / "index.json").write_bytes(index_bytes)
            (memory / "README.md").write_bytes(readme_bytes)
            (memory / "current.md").write_bytes(current_bytes)

            result = self.run_init(project, home)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((memory / "index.json").read_bytes(), index_bytes)
            self.assertEqual((memory / "README.md").read_bytes(), readme_bytes)
            self.assertEqual((memory / "current.md").read_bytes(), current_bytes)

    def test_project_only_flag_is_rejected(self) -> None:
        result = subprocess.run(
            [str(INIT), "--project-only"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("--project-only was removed", result.stderr)


if __name__ == "__main__":
    unittest.main()
