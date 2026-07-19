from __future__ import annotations

import json
import os
import runpy
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "scripts/discussion-transaction.py"
TEMPLATES = ROOT / "templates/teamwork-memory"
TEMPLATE = TEMPLATES / "teamwork-design-template.md"
CONTRACT = runpy.run_path(str(CLI), run_name="teamwork_design_contract")


class DesignArtifactSchemaTests(unittest.TestCase):
    def state(self, **overrides: object) -> dict[str, object]:
        state: dict[str, object] = {
            "schema_version": 1,
            "artifact_type": "design",
            "slug": "skill-architecture-v4",
            "title": "Skill architecture v4",
            "updated": "2026-07-19",
            "status": "current",
            "superseded_by": None,
            "evidence_waves": ["Local topology", "External Superpowers patterns"],
            "alternatives": ["Focused self-contained Skills", "Retain a Router hierarchy"],
            "exclusions": ["Recursive Skill orchestration"],
            "challenge_result": "survives one bounded challenge pass",
            "decision_frontier": ["Exact Plan handoff"],
            "settled": ["Research is external-only"],
            "open_items": ["Cross-host profile proof"],
            "plan_handoff": "Plan sequences the selected direction and acceptance evidence.",
            "review_handoff": "Review checks convergence and unsupported claims.",
            "decision_rule": "Prefer the smallest coherent ownership boundary.",
            "recommendation": "Use focused self-contained Skills.",
            "largest_downside": "Migration changes existing invocation paths.",
            "rejected_alternatives": [
                {"option": "Retain a Router hierarchy", "reason": "It preserves unnecessary recursive behavior."}
            ],
            "residual_uncertainty": "Installed host wording remains a compatibility check.",
        }
        state.update(overrides)
        return state

    def render(self, state: dict[str, object] | None = None) -> str:
        return CONTRACT["render_design_artifact"](state or self.state())

    def project(self, temporary: str) -> Path:
        project = Path(temporary) / "project"
        memory = project / "docs/teamwork"
        memory.mkdir(parents=True)
        for name in ("index.json", "current.md", "README.md"):
            (memory / name).write_bytes((TEMPLATES / name).read_bytes())
        return project

    def command(self, *arguments: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        merged = os.environ.copy()
        if env:
            merged.update(env)
        return subprocess.run(
            [sys.executable, str(CLI), *arguments],
            cwd=ROOT,
            text=True,
            capture_output=True,
            env=merged,
            check=False,
        )

    def snapshot(self, project: Path) -> dict[str, tuple[object, ...]]:
        result: dict[str, tuple[object, ...]] = {}
        for path in sorted((project, *project.rglob("*")), key=str):
            relative = "." if path == project else path.relative_to(project).as_posix()
            info = path.lstat()
            if stat.S_ISREG(info.st_mode):
                result[relative] = ("file", stat.S_IMODE(info.st_mode), path.read_bytes())
            elif stat.S_ISDIR(info.st_mode):
                result[relative] = ("dir", stat.S_IMODE(info.st_mode))
        return result

    def test_template_is_authoritative_and_title_precedes_generated_route(self) -> None:
        owners = list((ROOT / "templates").rglob("teamwork-design-template.md"))
        self.assertEqual(owners, [TEMPLATE])
        rendered = self.render()
        self.assertIn("# Skill architecture v4\n\n## Route and convergence\n\n```mermaid\n", rendered)
        self.assertNotIn("{{", rendered)
        self.assertEqual(CONTRACT["validate_design_artifact"](rendered), self.state())

    def test_graph_fallback_and_structured_state_cover_all_design_semantics(self) -> None:
        state = self.state()
        opening = self.render(state).split("## Design state", 1)[0]
        required = [
            *state["evidence_waves"],
            *state["alternatives"],
            *state["exclusions"],
            state["challenge_result"],
            state["decision_rule"],
            state["recommendation"],
            state["largest_downside"],
            state["rejected_alternatives"][0]["option"],
            state["rejected_alternatives"][0]["reason"],
            state["residual_uncertainty"],
            state["plan_handoff"],
            state["review_handoff"],
        ]
        for value in required:
            with self.subTest(value=value):
                self.assertGreaterEqual(opening.count(str(value)), 2)
        with self.assertRaises(CONTRACT["TransactionError"]):
            CONTRACT["validate_design_artifact"](self.render().replace("Decision rule:", "Wrong rule:", 1))

    def test_one_safe_path_is_valid_only_with_explicit_exclusion_and_rejection_reason(self) -> None:
        one_safe = self.state(
            alternatives=["Use the only safe migration path"],
            exclusions=["Other routes violate the public compatibility boundary"],
            rejected_alternatives=[
                {"option": "Retain legacy state", "reason": "It cannot recover a partial migration."}
            ],
        )
        self.assertEqual(CONTRACT["validate_design_artifact"](self.render(one_safe)), one_safe)
        with self.assertRaises(CONTRACT["TransactionError"]):
            self.render(self.state(alternatives=["Only safe"], exclusions=[]))

    def test_controlled_design_apply_derives_path_and_updates_active_design(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = self.project(temporary)
            inspected = self.command("design-inspect", "--project-root", str(project))
            self.assertEqual(inspected.returncode, 0, inspected.stderr)
            request = {
                "schema_version": 1,
                "operation": "create",
                "expected_revision": json.loads(inspected.stdout)["revision"],
                "state": self.state(),
            }
            created = self.command(
                "design-apply",
                "--project-root",
                str(project),
                "--request-json",
                json.dumps(request),
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            output = json.loads(created.stdout)
            self.assertEqual(output["path"], "docs/teamwork/design/2026-07-19-skill-architecture-v4.md")
            artifact = project / output["path"]
            self.assertEqual(CONTRACT["validate_design_artifact"](artifact.read_text(encoding="utf-8")), self.state())
            index = json.loads((project / "docs/teamwork/index.json").read_text(encoding="utf-8"))
            self.assertEqual(index["active"]["design"], output["path"])

    def test_read_only_helpers_use_same_template_contract(self) -> None:
        state = self.state()
        rendered = self.command("design-render", "--state-json", json.dumps(state))
        self.assertEqual(rendered.returncode, 0, rendered.stderr)
        self.assertEqual(rendered.stdout, self.render(state))
        with tempfile.TemporaryDirectory() as temporary:
            artifact = Path(temporary) / "design.md"
            artifact.write_text(rendered.stdout, encoding="utf-8")
            checked = self.command("design-validate", "--artifact", str(artifact))
        self.assertEqual(checked.returncode, 0, checked.stderr)
        self.assertTrue(json.loads(checked.stdout)["valid"])

    def test_design_inspect_recovers_a_prepared_interrupted_index_transaction(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = self.project(temporary)
            revision = json.loads(self.command("design-inspect", "--project-root", str(project)).stdout)["revision"]
            before = self.snapshot(project)
            request = {"schema_version": 1, "operation": "create", "expected_revision": revision, "state": self.state()}
            interrupted = self.command(
                "design-apply",
                "--project-root",
                str(project),
                "--request-json",
                json.dumps(request),
                env={"TEAMWORK_ARTIFACT_TRANSACTION_INTERRUPT_AFTER_BACKUP": "1"},
            )
            self.assertNotEqual(interrupted.returncode, 0)
            self.assertEqual(json.loads(interrupted.stderr)["category"], "INDETERMINATE")
            marker = project / "docs/teamwork/.design-transaction.json"
            self.assertTrue(marker.is_file())
            recovered = self.command("design-inspect", "--project-root", str(project))
            self.assertEqual(recovered.returncode, 0, recovered.stderr)
            self.assertTrue(json.loads(recovered.stdout)["recovered"])
            self.assertEqual(self.snapshot(project), before)

    def test_design_retained_journal_rejects_index_file_prefix_collisions_before_mutation(self) -> None:
        for collision in ("docs/teamwork/index.json.bak", "docs/teamwork/index.json/child"):
            with self.subTest(collision=collision), tempfile.TemporaryDirectory() as temporary:
                project = self.project(temporary)
                marker = project / "docs/teamwork/.design-transaction.json"
                if collision.endswith(".bak"):
                    (project / collision).write_bytes(b"must remain untouched\n")
                journal = {
                    "schema_version": 1,
                    "kind": "design",
                    "phase": "prepared",
                    "token": "1" * 32,
                    "created_directories": [],
                    "targets": [
                        {
                            "path": collision,
                            "before": {"exists": False, "data_b64": None, "mode": None},
                            "after": {"exists": False, "data_b64": None, "mode": None},
                            "stage": None,
                            "backup": None,
                        }
                    ],
                }
                marker.write_text(json.dumps(journal), encoding="utf-8")
                before = self.snapshot(project)

                rejected = self.command("design-inspect", "--project-root", str(project))

                self.assertNotEqual(rejected.returncode, 0)
                self.assertEqual(json.loads(rejected.stderr)["category"], "INDETERMINATE")
                self.assertEqual(self.snapshot(project), before)


if __name__ == "__main__":
    unittest.main()
