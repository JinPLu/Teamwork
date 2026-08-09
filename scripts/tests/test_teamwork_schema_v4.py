from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INIT = ROOT / "scripts/init-project.sh"
PROJECT_FILES = ROOT / "scripts/init-project-files.py"
VALIDATOR = ROOT / "scripts/validate_teamwork_index.py"
HELPER_PATH = ROOT / "scripts/teamwork_index_v4.py"
TEMPLATES = ROOT / "templates/teamwork-memory"


def load_helper():
    specification = importlib.util.spec_from_file_location("teamwork_index_v4", HELPER_PATH)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


HELPER = load_helper()


class TeamworkSchemaV4Tests(unittest.TestCase):
    def test_fresh_init_creates_only_empty_index_and_context(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary).resolve() / "sample-project"
            project.mkdir()

            result = subprocess.run(
                [str(INIT), "--project-root", str(project), "--no-codegraph"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            memory = project / "docs/teamwork"
            self.assertEqual(
                sorted(path.relative_to(memory).as_posix() for path in memory.rglob("*") if path.is_file()),
                ["index.json"],
            )
            index = json.loads((memory / "index.json").read_text(encoding="utf-8"))
            self.assertEqual(set(index), {"schema_version", "project", "tasks"})
            self.assertEqual(index["schema_version"], 4)
            self.assertEqual(index["tasks"], {})
            agents = (project / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("schema v4 is the only normal Teamwork document route", agents)
            self.assertIn("discussions,research,debug,plans,reviews,reports", agents)
            self.assertIn("Init never migrates", agents)
            self.assertNotIn("cases/<case_id>", agents)
            self.assertNotIn("one live document", agents)

    def test_repeated_init_fails_closed_without_rewriting_context(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary).resolve() / "sample-project"
            project.mkdir()
            first = subprocess.run(
                [str(INIT), "--project-root", str(project), "--no-codegraph"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            observed = {
                path: path.read_text(encoding="utf-8")
                for path in (
                    project / "AGENTS.md",
                    project / ".gitignore",
                    project / "docs/teamwork/index.json",
                )
            }

            repeated = subprocess.run(
                [str(INIT), "--project-root", str(project), "--no-codegraph"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(repeated.returncode, 0)
            self.assertIn("Init is fresh-only", repeated.stderr)
            self.assertEqual(
                observed,
                {path: path.read_text(encoding="utf-8") for path in observed},
            )

    def test_update_refreshes_existing_context_without_rewriting_index(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary).resolve() / "sample-project"
            project.mkdir()
            initialized = subprocess.run(
                [str(INIT), "--project-root", str(project), "--no-codegraph"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(initialized.returncode, 0, initialized.stderr)
            index_path = project / "docs/teamwork/index.json"
            index_before = index_path.read_text(encoding="utf-8")
            agents_path = project / "AGENTS.md"
            agents_path.write_text(
                "User preface.\n\n<!-- TEAMWORK_PROJECT_START -->\nstale\n<!-- TEAMWORK_PROJECT_END -->\n",
                encoding="utf-8",
            )

            refreshed = subprocess.run(
                [
                    sys.executable,
                    str(PROJECT_FILES),
                    "--project-root",
                    str(project),
                    "refresh-context",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(refreshed.returncode, 0, refreshed.stderr)
            self.assertEqual(index_before, index_path.read_text(encoding="utf-8"))
            agents = agents_path.read_text(encoding="utf-8")
            self.assertIn("User preface.", agents)
            self.assertIn("schema v4 is the only normal Teamwork document route", agents)
            self.assertNotIn("\nstale\n", agents)

    def test_six_types_are_discoverable_and_lifecycle_is_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary).resolve() / "project"
            memory = project / "docs/teamwork"
            memory.mkdir(parents=True)
            index = json.loads((TEMPLATES / "index.json").read_text(encoding="utf-8"))
            index["project"]["name"] = "Fixture"
            HELPER.register_task(
                index,
                task_key="typed-document-lifecycle",
                title="Typed document lifecycle",
                summary="Six semantic document types are discoverable through one task entry.",
                search_terms=["typed documents", "lifecycle"],
            )
            for document_type in HELPER.DOCUMENT_DIRECTORIES:
                path = HELPER.document_path(document_type, "2026-08-06", f"sample-{document_type}")
                target = project / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(f"# {document_type.title()} sample\n\nSemantic body.\n", encoding="utf-8")
                HELPER.register_document(
                    index,
                    task_key="typed-document-lifecycle",
                    document_type=document_type,
                    path=path,
                )
            HELPER.write_index(memory / "index.json", index)

            result = subprocess.run(
                [sys.executable, str(VALIDATOR), str(memory / "index.json")],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            discovered = HELPER.discover_documents(HELPER.load_index(memory / "index.json"))
            self.assertEqual({row["type"] for row in discovered}, set(HELPER.DOCUMENT_DIRECTORIES))
            self.assertEqual(len(discovered), 6)

            first = discovered[0]
            HELPER.finalize_document(index, task_key=first["task_key"], path=first["path"])
            with self.assertRaises(HELPER.IndexValidationError):
                HELPER.register_document(
                    index,
                    task_key="typed-document-lifecycle",
                    document_type=first["type"],
                    path=first["path"],
                )
            new_path = HELPER.document_path(first["type"], "2026-08-06", f"new-scope-{first['type']}")
            HELPER.register_document(
                index,
                task_key="typed-document-lifecycle",
                document_type=first["type"],
                path=new_path,
            )
            self.assertEqual(
                [item["status"] for item in index["tasks"]["typed-document-lifecycle"]["documents"] if item["type"] == first["type"]],
                ["final", "active"],
            )

    def test_paths_and_old_formats_fail_closed(self) -> None:
        invalid = (
            "../review.md",
            "/docs/teamwork/reviews/2026-08-06-review.md",
            "docs/teamwork/reviews/not-a-date-review.md",
            "docs/teamwork/research/2026-08-06-wrong-directory.md",
            "docs/teamwork/cases/2026-08-06-live.md",
        )
        for path in invalid:
            with self.subTest(path=path), self.assertRaises(HELPER.IndexValidationError):
                HELPER.validate_document_path(path, "review")

        with self.assertRaisesRegex(HELPER.IndexValidationError, "explicit Update migration"):
            HELPER.validate_index({"schema_version": 3, "project": {}, "tasks": {}})

    def test_template_directory_has_exactly_six_semantic_templates(self) -> None:
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), str(TEMPLATES)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            {path.name for path in TEMPLATES.glob("*.md")},
            {"discussion.md", "research.md", "debug.md", "plan.md", "review.md", "report.md"},
        )

    def test_review_template_has_claim_sensitive_sections_and_one_verdict(self) -> None:
        text = (TEMPLATES / "review.md").read_text(encoding="utf-8")
        self.assertIn("## Outcome Fit", text)
        self.assertIn("## Engineering Quality", text)
        self.assertIn("## Real-Path Evidence", text)
        self.assertIn("applicability", text)
        self.assertIn("reason", text)
        self.assertIn("evidence", text)
        self.assertIn("findings", text)
        outcome = text.split("## Engineering Quality", 1)[0]
        self.assertIn("applicability: applicable", outcome)
        self.assertNotIn("not applicable", outcome)
        self.assertIn("not applicable", text.split("## Engineering Quality", 1)[1])
        self.assertEqual(text.count("## Verdict"), 1)
        self.assertIn("## Residual Risk and Next Action", text)

    def test_update_check_only_readiness_requires_an_exact_explorer(self) -> None:
        text = (ROOT / "skills/teamwork-update/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("every check-only readiness inspection", text)
        self.assertIn("exact installed\nExplorer through `agent_type`", text)
        self.assertIn("observe a live child start", text)
        self.assertIn("cannot substitute for Explorer", text)
        self.assertIn("If the\nexact Explorer is not observed, return the real blocker", text)


if __name__ == "__main__":
    unittest.main()
