from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "policy/teamwork-global.md"
BASELINE = ("--profile", "performance-first", "--no-managed-codegraph", "--no-managed-gpu-broker")


class PolicyContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.home = Path(self.temporary.name) / "home"
        self.home.mkdir()
        self.env = os.environ.copy()
        self.env["HOME"] = str(self.home)
        self.env["CODEX_HOME"] = str(self.home / ".codex")
        for key in tuple(self.env):
            if key.startswith("TEAMWORK_"):
                self.env.pop(key)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def install(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(ROOT / "install.sh"), *arguments],
            cwd=ROOT,
            env=self.env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_canonical_policy_is_one_readable_source_with_owned_principles(self) -> None:
        text = POLICY.read_text(encoding="utf-8")
        sections = text.strip().split("\n\n")
        self.assertEqual(sections[0], "# Teamwork Global Policy")
        self.assertIn("Clear work stays native", text)
        self.assertIn("Calibrate verification", text)
        self.assertIn("smallest sufficient control", text)
        self.assertIn("framework itself does not use them", text)

    def test_canonical_policy_separates_typed_claims_from_effect_authority(self) -> None:
        text = POLICY.read_text(encoding="utf-8")
        for phrase in (
            "Discussion owns intended result, options, and user decisions",
            "Research owns external findings at its cutoff",
            "Debug owns cause, fix, and same-path evidence",
            "Plan owns selected scope, work, dependencies, and proof targets",
            "Report owns observed execution and resulting state",
            "Review owns the verdict on its stable candidate",
            "Current consequential effect authority",
            "permission does not manufacture authority",
            "Same-claim conflicts are surfaced and become unresolved",
            "Clear authorized local work remains native",
        ):
            self.assertIn(phrase, text)

    def test_codex_and_claude_managed_blocks_preserve_surrounding_content(self) -> None:
        codex = self.home / ".codex/AGENTS.md"
        claude = self.home / ".claude/CLAUDE.md"
        codex.parent.mkdir(parents=True)
        claude.parent.mkdir(parents=True)
        codex.write_text("before codex\n\nafter codex\n", encoding="utf-8")
        claude.write_text("before claude\n\nafter claude\n", encoding="utf-8")

        codex_result = self.install(*BASELINE, "--no-codex-routing", "codex")
        claude_result = self.install("--profile", "performance-first", "claude")
        self.assertEqual(codex_result.returncode, 0, codex_result.stderr + codex_result.stdout)
        self.assertEqual(claude_result.returncode, 0, claude_result.stderr + claude_result.stdout)
        for path, before, after in (
            (codex, "before codex", "after codex"),
            (claude, "before claude", "after claude"),
        ):
            installed = path.read_text(encoding="utf-8")
            self.assertIn(before, installed)
            self.assertIn(after, installed)
            self.assertEqual(installed.count("Clear work stays native"), 1)
            self.assertEqual(installed.count("Current consequential effect authority"), 1)
            self.assertIn("permission does not manufacture authority", installed)
        self.assertIn("global policy activation: current", codex_result.stdout)
        self.assertIn("global policy activation: current", claude_result.stdout)

    def test_cursor_policy_is_always_reported_as_manual_partial(self) -> None:
        result = self.install("--profile", "performance-first", "--no-mcp", "cursor")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("Cursor static skills/agents: installed", result.stdout)
        self.assertIn("Cursor global policy activation: partial", result.stdout)
        self.assertIn("manual action required", result.stdout)
        self.assertIn("Cursor Settings -> Rules -> User Rules", result.stdout)

    def test_update_distinguishes_failed_cutover_from_post_cutover_rollback(self) -> None:
        text = (ROOT / "skills/teamwork-update/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("fails before the migration\nstate reaches `cutover`", text)
        self.assertIn("without calling\nthe phase-gated rollback command", text)
        self.assertIn("cutover succeeds but readback", text)
        self.assertIn("invokes rollback from the prepared external\ncopy", text)


if __name__ == "__main__":
    unittest.main()
