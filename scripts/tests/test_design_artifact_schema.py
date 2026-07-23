from __future__ import annotations

import hashlib
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
            "schema_version": 3,
            "artifact_type": "design",
            "slug": "skill-architecture-v4",
            "title": "Skill architecture v4",
            "updated": "2026-07-19",
            "status": "current",
            "superseded_by": None,
            "acceptance": "pending",
            "blockers": [],
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
                {"option": "Router hierarchy rejection", "reason": "It preserves unnecessary recursive behavior."}
            ],
            "residual_uncertainty": "Installed host wording remains a compatibility check.",
        }
        state.update(overrides)
        if state["schema_version"] in {1, 2}:
            state.pop("acceptance", None)
            state.pop("blockers", None)
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

    def inspect(self, project: Path) -> dict[str, object]:
        inspected = self.command("design-inspect", "--project-root", str(project))
        self.assertEqual(inspected.returncode, 0, inspected.stderr)
        return json.loads(inspected.stdout)

    def apply(
        self,
        project: Path,
        operation: str,
        state: dict[str, object],
        *,
        revision: str | None = None,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        expected = revision or str(self.inspect(project)["revision"])
        request = {"schema_version": 1, "operation": operation, "expected_revision": expected, "state": state}
        return self.command(
            "design-apply",
            "--project-root",
            str(project),
            "--request-json",
            json.dumps(request),
            env=env,
        )

    def index_entry(self, project: Path, path: str) -> dict[str, object]:
        index = json.loads((project / "docs/teamwork/index.json").read_text(encoding="utf-8"))
        return next(entry for entry in index["entries"] if entry["path"] == path)

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

    def test_v2_graph_is_concise_and_readable_state_covers_design_semantics_once(self) -> None:
        state = self.state(schema_version=2)
        opening = self.render(state).split("## Design state", 1)[0]
        mermaid = opening.split("```mermaid\n", 1)[1].split("\n```", 1)[0]
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
                self.assertEqual(opening.count(str(value)), 1)
                self.assertNotIn(str(value), mermaid)
        for line in mermaid.splitlines():
            if '["' in line:
                label = line.split('["', 1)[1].split('"]', 1)[0]
                self.assertLessEqual(len(label), 48)
        with self.assertRaises(CONTRACT["TransactionError"]):
            CONTRACT["validate_design_artifact"](self.render().replace("Decision rule:", "Wrong rule:", 1))

    def test_v1_v2_design_artifacts_still_validate_through_frozen_renderers(self) -> None:
        expected_hashes = {
            1: "8b48dd90fb668f0b318bc537f5ec04008e1fb0a22ebf4a54858af8c4bea6cc2b",
            2: "304e74ff2c7a813e26c161051cf4b19a7dbebab867d14099eb45942ac1931080",
        }
        for version in (1, 2):
            with self.subTest(version=version):
                state = self.state(schema_version=version)
                rendered = self.render(state)
                validated = CONTRACT["validate_design_artifact"](rendered)
                self.assertEqual(validated, state)
                self.assertEqual(hashlib.sha256(rendered.encode("utf-8")).hexdigest(), expected_hashes[version])
                self.assertEqual(CONTRACT["design_acceptance"](validated), "accepted")
        self.assertNotIn("## Readable design", self.render(self.state(schema_version=1)))

    def test_v3_schema_defaults_to_pending_and_blocked_requires_explicit_blockers(self) -> None:
        schema = self.command("design-schema", "create")
        self.assertEqual(schema.returncode, 0, schema.stderr)
        state = json.loads(schema.stdout)["state"]
        self.assertEqual(state["schema_version"], 3)
        self.assertEqual(state["acceptance"], "pending")
        self.assertEqual(state["blockers"], [])
        with self.assertRaisesRegex(CONTRACT["TransactionError"], "at least one blocker"):
            self.render(self.state(acceptance="blocked"))
        with self.assertRaisesRegex(CONTRACT["TransactionError"], "only a blocked Design"):
            self.render(self.state(acceptance="accepted", blockers=["stale blocker"]))
        legacy_with_pending = self.state(schema_version=2)
        legacy_with_pending["acceptance"] = "pending"
        with self.assertRaisesRegex(CONTRACT["TransactionError"], "require schema_version 3"):
            self.render(legacy_with_pending)

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

    def test_pending_create_and_same_path_acceptance_update_change_index_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = self.project(temporary)
            created = self.apply(project, "create", self.state())
            self.assertEqual(created.returncode, 0, created.stderr)
            output = json.loads(created.stdout)
            self.assertEqual(output["path"], "docs/teamwork/design/2026-07-19-skill-architecture-v4.md")
            artifact = project / output["path"]
            self.assertEqual(CONTRACT["validate_design_artifact"](artifact.read_text(encoding="utf-8")), self.state())
            index = json.loads((project / "docs/teamwork/index.json").read_text(encoding="utf-8"))
            self.assertEqual(index["active"]["design"], output["path"])
            pending_entry = self.index_entry(project, output["path"])
            self.assertEqual(
                (pending_entry["status"], pending_entry["currentness"], pending_entry["authority"]),
                ("candidate", "candidate", "candidate"),
            )
            self.assertEqual(self.inspect(project)["active"]["acceptance"], "pending")

            accepted = self.apply(
                project,
                "update",
                self.state(acceptance="accepted"),
                revision=str(output["revision"]),
            )
            self.assertEqual(accepted.returncode, 0, accepted.stderr)
            accepted_entry = self.index_entry(project, output["path"])
            self.assertEqual(
                (accepted_entry["status"], accepted_entry["currentness"], accepted_entry["authority"]),
                ("accepted", "current", "canonical"),
            )
            self.assertEqual(self.inspect(project)["active"]["acceptance"], "accepted")

    def test_same_path_update_cannot_downgrade_an_accepted_design(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = self.project(temporary)
            created = self.apply(project, "create", self.state(acceptance="accepted"))
            self.assertEqual(created.returncode, 0, created.stderr)
            before = self.snapshot(project)
            for acceptance, blockers in (("pending", []), ("blocked", ["Reviewer rejected the boundary."])):
                with self.subTest(acceptance=acceptance):
                    rejected = self.apply(
                        project,
                        "update",
                        self.state(acceptance=acceptance, blockers=blockers),
                        revision=str(json.loads(created.stdout)["revision"]),
                    )
                    self.assertNotEqual(rejected.returncode, 0)
                    self.assertIn("cannot downgrade an accepted Design", rejected.stderr)
                    self.assertEqual(self.snapshot(project), before)

    def test_blocked_create_and_pending_to_blocked_update_are_not_plan_ready(self) -> None:
        blocked = self.state(acceptance="blocked", blockers=["Security owner has not approved the boundary."])
        with tempfile.TemporaryDirectory() as temporary:
            project = self.project(temporary)
            created = self.apply(project, "create", blocked)
            self.assertEqual(created.returncode, 0, created.stderr)
            output = json.loads(created.stdout)
            entry = self.index_entry(project, output["path"])
            self.assertEqual((entry["status"], entry["currentness"], entry["authority"]), ("blocked", "candidate", "candidate"))
            self.assertEqual(self.inspect(project)["active"]["state"]["blockers"], blocked["blockers"])

        with tempfile.TemporaryDirectory() as temporary:
            project = self.project(temporary)
            created = self.apply(project, "create", self.state())
            self.assertEqual(created.returncode, 0, created.stderr)
            updated = self.apply(project, "update", blocked, revision=str(json.loads(created.stdout)["revision"]))
            self.assertEqual(updated.returncode, 0, updated.stderr)
            entry = self.index_entry(project, json.loads(updated.stdout)["path"])
            self.assertEqual((entry["status"], entry["currentness"], entry["authority"]), ("blocked", "candidate", "candidate"))
            accepted = self.apply(
                project,
                "update",
                self.state(acceptance="accepted"),
                revision=str(json.loads(updated.stdout)["revision"]),
            )
            self.assertEqual(accepted.returncode, 0, accepted.stderr)
            entry = self.index_entry(project, json.loads(accepted.stdout)["path"])
            self.assertEqual((entry["status"], entry["currentness"], entry["authority"]), ("accepted", "current", "canonical"))

    def test_supersede_accepts_pending_accepted_and_blocked_successors(self) -> None:
        cases = (
            ("pending", [], "accepted", []),
            ("accepted", [], "pending", []),
            ("accepted", [], "blocked", ["The migration owner has not approved execution."]),
        )
        for old_acceptance, old_blockers, new_acceptance, new_blockers in cases:
            with self.subTest(old=old_acceptance, new=new_acceptance), tempfile.TemporaryDirectory() as temporary:
                project = self.project(temporary)
                old_state = self.state(acceptance=old_acceptance, blockers=old_blockers)
                created = self.apply(project, "create", old_state)
                self.assertEqual(created.returncode, 0, created.stderr)
                old_path = json.loads(created.stdout)["path"]
                successor = self.state(
                    slug="skill-architecture-v5",
                    title="Skill architecture v5",
                    updated="2026-07-20",
                    acceptance=new_acceptance,
                    blockers=new_blockers,
                )
                superseded = self.apply(
                    project,
                    "supersede",
                    successor,
                    revision=str(json.loads(created.stdout)["revision"]),
                )
                self.assertEqual(superseded.returncode, 0, superseded.stderr)
                new_path = json.loads(superseded.stdout)["path"]
                old_entry = self.index_entry(project, old_path)
                new_entry = self.index_entry(project, new_path)
                expected_new = CONTRACT["_design_index_metadata"](new_acceptance)
                self.assertEqual((old_entry["status"], old_entry["currentness"], old_entry["authority"]), ("superseded", "historical", "superseded"))
                self.assertEqual((new_entry["status"], new_entry["currentness"], new_entry["authority"]), expected_new)
                old_artifact = CONTRACT["validate_design_artifact"]((project / old_path).read_text(encoding="utf-8"))
                self.assertEqual(old_artifact["status"], "superseded")
                self.assertEqual(CONTRACT["design_acceptance"](old_artifact), old_acceptance)

    def test_legacy_v1_v2_transactions_are_interpreted_as_accepted(self) -> None:
        for version in (1, 2):
            with self.subTest(version=version), tempfile.TemporaryDirectory() as temporary:
                project = self.project(temporary)
                state = self.state(schema_version=version)
                created = self.apply(project, "create", state)
                self.assertEqual(created.returncode, 0, created.stderr)
                output = json.loads(created.stdout)
                entry = self.index_entry(project, output["path"])
                self.assertEqual((entry["status"], entry["currentness"], entry["authority"]), ("accepted", "current", "canonical"))
                active = self.inspect(project)["active"]
                self.assertEqual(active["acceptance"], "accepted")
                self.assertNotIn("acceptance", active["state"])
                self.assertEqual((project / output["path"]).read_text(encoding="utf-8"), self.render(state))

    def test_design_acceptance_and_index_metadata_drift_fail_closed(self) -> None:
        cases = (
            ("pending", [], ("accepted", "current", "canonical")),
            ("accepted", [], ("candidate", "candidate", "candidate")),
            ("blocked", ["A named blocker remains."], ("candidate", "candidate", "candidate")),
        )
        for acceptance, blockers, drifted in cases:
            with self.subTest(acceptance=acceptance), tempfile.TemporaryDirectory() as temporary:
                project = self.project(temporary)
                created = self.apply(project, "create", self.state(acceptance=acceptance, blockers=blockers))
                self.assertEqual(created.returncode, 0, created.stderr)
                path = json.loads(created.stdout)["path"]
                index_path = project / "docs/teamwork/index.json"
                index = json.loads(index_path.read_text(encoding="utf-8"))
                entry = next(item for item in index["entries"] if item["path"] == path)
                entry["status"], entry["currentness"], entry["authority"] = drifted
                index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")

                rejected = self.command("design-inspect", "--project-root", str(project))

                self.assertNotEqual(rejected.returncode, 0)
                self.assertIn("active.design artifact does not agree", rejected.stderr)

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
