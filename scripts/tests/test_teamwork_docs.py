from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]


class DocsMaintenanceTests(unittest.TestCase):
    def test_facts_yaml_matches_closed_kind_set(self) -> None:
        sys.path.insert(0, str(ROOT / "scripts"))
        from teamwork_tooling.simple_yaml import load_simple_yaml

        facts = load_simple_yaml(ROOT / "config/teamwork-facts.yaml")
        self.assertEqual(
            facts["kinds"],
            [
                "discussions",
                "research",
                "debug",
                "plans",
                "reviews",
                "reports",
                "experiments",
            ],
        )
        self.assertEqual(facts["checkpoint_path"], "docs/teamwork/<kind>/<slug>.md")
        self.assertEqual(facts["hosts"]["cursor"]["skills"], 6)
        self.assertEqual(facts["hosts"]["cursor"]["roles"], 6)
        self.assertEqual(facts["hosts"]["claude"]["roles"], 7)
        self.assertEqual(facts["hosts"]["codex"]["roles"], 8)
        self.assertEqual(len(facts["cursor_skills"]), 6)
        self.assertNotIn("teamwork-debug", facts["cursor_skills"])
        self.assertNotIn("teamwork-goal", facts["cursor_skills"])

    def test_generated_fact_blocks_are_fresh(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/render-teamwork-facts.py"), "--check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_index_script_builds_index_and_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            docs = Path(raw) / "docs" / "teamwork"
            discussions = docs / "discussions"
            experiments = docs / "experiments"
            discussions.mkdir(parents=True)
            experiments.mkdir(parents=True)
            (discussions / "alpha.md").write_text(
                "---\n"
                "status: active\n"
                "superseded-by:\n"
                "created: 2026-08-20\n"
                "updated: 2026-08-20\n"
                "---\n\n"
                "# Alpha\n\n"
                "## Current synthesis\n\n"
                "Keep the same slug.\n",
                encoding="utf-8",
            )
            (discussions / "2026-07-01-old-topic.md").write_text(
                "---\n"
                "status: archived\n"
                "superseded-by:\n"
                "created: 2026-07-01\n"
                "updated: 2026-07-01\n"
                "---\n\n"
                "# Old topic\n\n"
                "Historical note.\n",
                encoding="utf-8",
            )
            (experiments / "probe.md").write_text(
                "---\n"
                "status: active\n"
                "superseded-by:\n"
                "created: 2026-08-20\n"
                "updated: 2026-08-20\n"
                "declared-slot: exploratory probe\n"
                "adjudicated-slot:\n"
                "---\n\n"
                "# Probe\n\n"
                "## Declaration\n\n"
                "Claim draft only.\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/teamwork-index.py"),
                    "--docs-root",
                    str(docs),
                    "--repo-root",
                    str(ROOT),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            index = (docs / "INDEX.md").read_text(encoding="utf-8")
            self.assertIn("## discussions", index)
            self.assertIn("## Optional", index)
            self.assertIn("alpha.md", index)
            self.assertIn("2026-07-01-old-topic.md", index)
            self.assertIn("Derived from checkpoint files", index)
            ledger = (experiments / "LEDGER.md").read_text(encoding="utf-8")
            self.assertIn("main-table-earned:", ledger)
            self.assertIn("probes: 1", ledger)
            self.assertIn("not a CI gate", ledger)
            check = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/teamwork-index.py"),
                    "--check",
                    "--docs-root",
                    str(docs),
                    "--repo-root",
                    str(ROOT),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(check.returncode, 0, check.stderr)

    def test_append_history_is_append_only(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "note.md"
            path.write_text(
                "---\nstatus: active\nupdated: 2026-01-01\n---\n\n"
                "# Note\n\n"
                "## History\n\n"
                "### 2026-01-01 — first\n\n"
                "Keep me.\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/teamwork-index.py"),
                    "--append-history",
                    str(path),
                    "### 2026-08-20 — second\n\nNew entry.\n",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            text = path.read_text(encoding="utf-8")
            self.assertIn("Keep me.", text)
            self.assertIn("New entry.", text)
            self.assertLess(text.find("Keep me."), text.find("New entry."))
            self.assertRegex(text, r"updated: 20\d{2}-\d{2}-\d{2}")

    def test_backfill_adds_archived_frontmatter(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            docs = Path(raw) / "docs" / "teamwork"
            plans = docs / "plans"
            plans.mkdir(parents=True)
            target = plans / "2026-08-01-legacy.md"
            target.write_text("# Legacy\n\nBody.\n", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/teamwork-index.py"),
                    "--backfill",
                    "--docs-root",
                    str(docs),
                    "--repo-root",
                    str(ROOT),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            text = target.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\n"))
            self.assertIn("status: archived", text)
            self.assertIn("created: 2026-08-01", text)
            self.assertIn("# Legacy", text)
            self.assertEqual(target.name, "2026-08-01-legacy.md")

    def test_backfill_skips_slug_only_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            docs = Path(raw) / "docs" / "teamwork"
            plans = docs / "plans"
            plans.mkdir(parents=True)
            slug = plans / "new-identity.md"
            slug.write_text("# New identity\n\nBody.\n", encoding="utf-8")
            dated = plans / "2026-08-01-legacy.md"
            dated.write_text("# Legacy\n\nBody.\n", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/teamwork-index.py"),
                    "--backfill",
                    "--docs-root",
                    str(docs),
                    "--repo-root",
                    str(ROOT),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("skipped slug-only files without status: 1", result.stdout)
            self.assertTrue(dated.read_text(encoding="utf-8").startswith("---\n"))
            self.assertIn("status: archived", dated.read_text(encoding="utf-8"))
            self.assertEqual(slug.read_text(encoding="utf-8"), "# New identity\n\nBody.\n")
            forced = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/teamwork-index.py"),
                    "--backfill",
                    "--force",
                    "--docs-root",
                    str(docs),
                    "--repo-root",
                    str(ROOT),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(forced.returncode, 0, forced.stderr)
            self.assertIn("status: archived", slug.read_text(encoding="utf-8"))

    def test_ledger_inflation_is_inf_when_declared_without_earned(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            docs = Path(raw) / "docs" / "teamwork"
            experiments = docs / "experiments"
            experiments.mkdir(parents=True)
            (experiments / "claim.md").write_text(
                "---\n"
                "status: active\n"
                "declared-slot: main table\n"
                "adjudicated-slot:\n"
                "---\n\n"
                "# Claim\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/teamwork-index.py"),
                    "--docs-root",
                    str(docs),
                    "--repo-root",
                    str(ROOT),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            ledger = (experiments / "LEDGER.md").read_text(encoding="utf-8")
            self.assertIn("declared main-table: 1", ledger)
            self.assertIn("earned: 0", ledger)
            self.assertIn("ratio (declared / earned): inf", ledger)
            self.assertNotIn("ratio (declared / earned): n/a", ledger)

    def test_public_docs_drop_plugin_install_and_name_source_pointer(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        readme_en = (ROOT / "README.en.md").read_text(encoding="utf-8")
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        architecture = (ROOT / "docs/architecture.md").read_text(encoding="utf-8")
        contributing = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
        self.assertNotIn("codex plugin marketplace add", readme)
        self.assertNotIn("codex plugin marketplace add", readme_en)
        self.assertIn("codex plugin remove teamwork-skill", readme)
        self.assertIn("codex plugin remove teamwork-skill", readme_en)
        self.assertIn("./install.sh codex", readme)
        self.assertIn("./install.sh codex", readme_en)
        self.assertNotIn("regenerate the plugin bundle", agents)
        self.assertNotIn("plugin manifest", agents)
        self.assertNotIn("build-codex-plugin.py", contributing)
        self.assertNotIn("plugins/teamwork-skill", architecture)
        self.assertIn("enhance native host modes", architecture)
        self.assertIn("~/.teamwork/install.json", architecture)
        self.assertIn("yields to host Debug and Explore", architecture)
        self.assertIn("yields to Explore", architecture)

        check = subprocess.run(
            [sys.executable, str(ROOT / "scripts/write-source-pointer.py"), "check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(check.returncode, 0, check.stderr)

        with tempfile.TemporaryDirectory() as raw:
            written = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/write-source-pointer.py"),
                    "write",
                    "--root",
                    str(ROOT),
                    "--version",
                    "7.10.1",
                    "--home",
                    raw,
                    "--host",
                    "codex",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(written.returncode, 0, written.stderr)
            status = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/write-source-pointer.py"),
                    "status",
                    "--home",
                    raw,
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(status.returncode, 0, status.stderr)
            self.assertEqual(status.stdout.strip(), "valid")

    def test_doctor_reports_only(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            docs = Path(raw) / "docs" / "teamwork"
            reviews = docs / "reviews"
            reviews.mkdir(parents=True)
            (reviews / "dup-a.md").write_text(
                "---\nstatus: active\nsuperseded-by: missing.md\n---\n\n# Dup\n",
                encoding="utf-8",
            )
            (reviews / "2026-01-01-dup-a.md").write_text(
                "---\nstatus: archived\n---\n\n# Also dup\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/teamwork-index.py"),
                    "--doctor",
                    "--docs-root",
                    str(docs),
                    "--repo-root",
                    str(ROOT),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            combined = result.stdout + result.stderr
            self.assertIn("duplicate slug", combined)
            self.assertIn("broken superseded-by", combined)
            self.assertIn("Report only", combined)


if __name__ == "__main__":
    unittest.main()
