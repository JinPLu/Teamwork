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
    def test_writer_and_document_runtime_are_absent(self) -> None:
        topology = json.loads((ROOT / "config/teamwork-topology.json").read_text(encoding="utf-8"))
        self.assertNotIn("writer", {row["name"] for row in topology["agents"]})
        self.assertFalse((ROOT / "templates/codex-agents/teamwork-writer.toml").exists())
        self.assertFalse((ROOT / "scripts/migrate-teamwork-documents.py").exists())
        self.assertFalse((ROOT / "scripts/teamwork_index_v4.py").exists())

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
