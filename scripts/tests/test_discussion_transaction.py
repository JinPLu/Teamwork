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
CONTRACT = runpy.run_path(str(CLI), run_name="teamwork_discussion_contract")


@unittest.skip("legacy Discussion write lifecycle retired; Collaborate import covers read-only compatibility")
class DiscussionTransactionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.project = Path(self.temporary.name) / "project"
        self.memory = self.project / "docs/teamwork"
        self.memory.mkdir(parents=True)
        for name in ("index.json", "current.md", "README.md"):
            (self.memory / name).write_bytes((TEMPLATES / name).read_bytes())

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def cli(self, *arguments: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
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

    def inspect(self) -> dict[str, object]:
        result = self.cli("inspect", "--project-root", str(self.project))
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def record(self, *, title: str = "Choose the recovery route", updated: str = "2026-07-19") -> dict[str, object]:
        return {
            "schema_version": 3,
            "artifact_type": "discussion",
            "slug": "recovery-route",
            "title": title,
            "updated": updated,
            "mode": "grill",
            "goal": "Preserve one recoverable durable decision.",
            "current_branch": "Choose the artifact transition route.",
            "return_path": "Resume at the recovery proof.",
            "blockers": ["The interruption proof is pending."],
            "convergence": "One exact recovery proof passes.",
            "key_evidence": ["The journal stores exact preimages."],
            "settled": [],
            "synthesis": ["Exact preimages make the discussion checkpoint recoverable."],
            "tensions": ["Handoff speed competes with proving recovery first."],
            "frontier": [
                {
                    "id": "Q1",
                    "title": "Recovery proof",
                    "level": "goal",
                    "status": "current",
                    "prompt": "Should the transaction prove exact recovery before handoff?",
                    "options": [
                        {"id": "prove-first", "label": "Prove first", "tradeoff": "Blocks handoff until the real recovery path passes."},
                        {"id": "defer-proof", "label": "Defer proof", "tradeoff": "Leaves the durable artifact boundary unverified."},
                    ],
                    "recommendation": "prove-first",
                    "largest_downside": "The proof adds one focused test step.",
                    "why_critical": "The answer changes whether the artifact can be trusted across process loss.",
                    "blocks": ["handoff"],
                    "depends_on": [],
                    "closure_signal": "The selected route is recorded with direct recovery evidence.",
                    "resolution": None,
                }
            ],
            "current_batch": ["Q1"],
        }

    def closed_record(self, *, updated: str = "2026-07-20") -> dict[str, object]:
        record = self.record(updated=updated)
        item = dict(record["frontier"][0])
        item["status"] = "closed"
        item["resolution"] = {"kind": "selected", "option_id": "prove-first"}
        record["frontier"] = [item]
        record["current_batch"] = []
        record["status"] = "accepted"
        return record

    def answered_record(self, *, title: str = "Choose the verified recovery route", updated: str = "2026-07-20") -> dict[str, object]:
        record = self.closed_record(updated=updated)
        record["status"] = "active"
        record["title"] = title
        record["frontier"].append(
            {
                "id": "Q2",
                "title": "Handoff route",
                "level": "detail",
                "status": "current",
                "prompt": "Should handoff use the focused transaction proof?",
                "options": [
                    {"id": "use-proof", "label": "Use proof", "tradeoff": "Keeps the handoff tied to direct evidence."},
                    {"id": "summarize-only", "label": "Summarize only", "tradeoff": "Drops the executable recovery signal."},
                ],
                "recommendation": "use-proof",
                "largest_downside": "The handoff stays narrowly scoped.",
                "why_critical": "The answer controls whether the next owner receives direct proof.",
                "blocks": ["handoff"],
                "depends_on": ["Q1"],
                "closure_signal": "The handoff route is selected.",
                "resolution": None,
            }
        )
        record["current_batch"] = ["Q2"]
        return record

    def apply(self, request: dict[str, object], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        return self.cli(
            "apply",
            "--project-root",
            str(self.project),
            "--request-json",
            json.dumps(request),
            env=env,
        )

    def request(self, operation: str, *, record: dict[str, object] | None = None, **extra: object) -> dict[str, object]:
        result: dict[str, object] = {
            "schema_version": 3,
            "operation": operation,
            "expected_revision": self.inspect()["revision"],
        }
        if record is not None:
            result["record"] = record
        result.update(extra)
        return result

    def snapshot(self) -> dict[str, tuple[object, ...]]:
        snapshot: dict[str, tuple[object, ...]] = {}
        for path in sorted((self.project, *self.project.rglob("*")), key=str):
            relative = "." if path == self.project else path.relative_to(self.project).as_posix()
            info = path.lstat()
            if stat.S_ISREG(info.st_mode):
                snapshot[relative] = ("file", stat.S_IMODE(info.st_mode), path.read_bytes())
            elif stat.S_ISDIR(info.st_mode):
                snapshot[relative] = ("dir", stat.S_IMODE(info.st_mode))
            elif stat.S_ISLNK(info.st_mode):
                snapshot[relative] = ("symlink", os.readlink(path))
        return snapshot

    def create(self) -> dict[str, object]:
        result = self.apply(self.request("create", record=self.record()))
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_create_uses_only_single_active_discussion_not_ordinary_memory(self) -> None:
        ordinary_before = {
            name: (self.memory / name).read_bytes()
            for name in ("index.json", "current.md", "README.md")
        }
        created = self.create()

        current = self.memory / "discussion/current.md"
        self.assertEqual(created["path"], "docs/teamwork/discussion/current.md")
        self.assertTrue(current.is_file())
        state = CONTRACT["validate_discussion_artifact"](current.read_text(encoding="utf-8"))
        self.assertEqual(state["schema_version"], 3)
        self.assertEqual(state["status"], "active")
        self.assertEqual(state["slug"], "recovery-route")
        self.assertEqual(
            ordinary_before,
            {name: (self.memory / name).read_bytes() for name in ordinary_before},
        )
        index = json.loads((self.memory / "index.json").read_text(encoding="utf-8"))
        self.assertNotIn("discussion", index["active"])

    def test_update_close_and_replace_are_revision_checked_atomic_transitions(self) -> None:
        self.create()
        updated = self.answered_record(updated="2026-07-20")
        result = self.apply(self.request("update", record=updated))
        self.assertEqual(result.returncode, 0, result.stderr)
        stale = self.apply(
            {
                "schema_version": 3,
                "operation": "update",
                "expected_revision": "0" * 64,
                "record": updated,
            }
        )
        self.assertNotEqual(stale.returncode, 0)
        self.assertEqual(json.loads(stale.stderr)["category"], "PREWRITE_SAFE")

        closed_record = self.closed_record(updated="2026-07-20")
        closed_record["title"] = updated["title"]
        q2 = dict(updated["frontier"][1])
        q2["status"] = "closed"
        q2["resolution"] = {"kind": "selected", "option_id": "use-proof"}
        closed_record["frontier"].append(q2)
        closed = self.apply(self.request("close", record=closed_record, close_status="accepted"))
        self.assertEqual(closed.returncode, 0, closed.stderr)
        archived = self.project / json.loads(closed.stdout)["path"]
        self.assertTrue(archived.is_file())
        self.assertFalse((self.memory / "discussion/current.md").exists())
        self.assertEqual(
            CONTRACT["validate_discussion_artifact"](archived.read_text(encoding="utf-8"))["status"],
            "accepted",
        )

        self.create()
        successor = self.record(title="Choose a successor route", updated="2026-07-21")
        replaced = self.apply(self.request("replace", record=successor))
        self.assertEqual(replaced.returncode, 0, replaced.stderr)
        archives = sorted((self.memory / "discussion").glob("2026-07-19-recovery-route*.md"))
        self.assertTrue(archives)
        self.assertEqual(
            CONTRACT["validate_discussion_artifact"](archives[-1].read_text(encoding="utf-8"))["status"],
            "superseded",
        )
        self.assertEqual(self.inspect()["active"]["state"]["title"], "Choose a successor route")

    def test_semantic_noop_update_does_not_write(self) -> None:
        created = self.create()
        before = self.snapshot()
        result = self.apply(
            {
                "schema_version": 3,
                "operation": "update",
                "expected_revision": created["revision"],
                "record": self.record(),
            }
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["changed_paths"], [])
        self.assertEqual(self.snapshot(), before)

    def test_hard_interruption_auto_recovers_exact_preimage_on_next_inspect(self) -> None:
        self.create()
        before = self.snapshot()
        updated = self.answered_record(title="Interrupted update", updated="2026-07-20")
        interrupted = self.apply(
            self.request("update", record=updated),
            env={"TEAMWORK_ARTIFACT_TRANSACTION_INTERRUPT_AFTER_BACKUP": "1"},
        )
        self.assertNotEqual(interrupted.returncode, 0)
        self.assertEqual(json.loads(interrupted.stderr)["category"], "INDETERMINATE")
        marker = self.memory / "discussion/.discussion-transaction.json"
        self.assertTrue(marker.is_file())

        recovered = self.inspect()

        self.assertTrue(recovered["recovered"])
        self.assertFalse(marker.exists())
        self.assertEqual(self.snapshot(), before)

    def test_post_preparation_failure_is_indeterminate_and_immediately_recovers(self) -> None:
        self.create()
        before = self.snapshot()
        failed = self.apply(
            self.request("update", record=self.answered_record(title="Will roll back", updated="2026-07-20")),
            env={"TEAMWORK_ARTIFACT_TRANSACTION_FAIL_INSTALL_N": "1"},
        )
        self.assertNotEqual(failed.returncode, 0)
        self.assertEqual(json.loads(failed.stderr)["category"], "INDETERMINATE")
        self.assertEqual(self.snapshot(), before)
        self.assertFalse((self.memory / "discussion/.discussion-transaction.json").exists())

    def test_first_discussion_creation_failure_restores_the_absent_directory_too(self) -> None:
        before = self.snapshot()
        failed = self.apply(
            self.request("create", record=self.record()),
            env={"TEAMWORK_ARTIFACT_TRANSACTION_FAIL_INSTALL_N": "1"},
        )
        self.assertNotEqual(failed.returncode, 0)
        self.assertEqual(json.loads(failed.stderr)["category"], "INDETERMINATE")
        self.assertEqual(self.snapshot(), before)

    def test_unsafe_active_file_is_rejected_without_repairing_it(self) -> None:
        self.create()
        current = self.memory / "discussion/current.md"
        outside = Path(self.temporary.name) / "linked-discussion.md"
        os.link(current, outside)
        result = self.cli("inspect", "--project-root", str(self.project))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stderr)["category"], "PREWRITE_SAFE")
        self.assertTrue(outside.exists())

    def test_renderer_rejects_graph_or_fallback_drift(self) -> None:
        text = CONTRACT["render_discussion_artifact"](
            {**self.record(), "status": "active", "superseded_by": None}
        )
        with self.assertRaises(CONTRACT["TransactionError"]):
            CONTRACT["validate_discussion_artifact"](text.replace("Goal:", "Wrong goal:", 1))


class CollaborateTransactionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.project = Path(self.temporary.name) / "project"
        self.memory = self.project / "docs/teamwork"
        self.memory.mkdir(parents=True)
        for name in ("index.json", "current.md", "README.md"):
            (self.memory / name).write_bytes((TEMPLATES / name).read_bytes())

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def cli(self, *arguments: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
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

    def inspect(self) -> dict[str, object]:
        result = self.cli("collaborate-inspect", "--project-root", str(self.project))
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def apply(self, request: dict[str, object], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        return self.cli(
            "collaborate-apply",
            "--project-root",
            str(self.project),
            "--request-json",
            json.dumps(request),
            env=env,
        )

    def state(
        self,
        *,
        decision_id: str = "c-collaborate-route",
        title: str = "Choose the Collaborate route",
        updated: str = "2026-07-29T00:00:00Z",
        status: str = "active",
        acceptance: str = "pending",
    ) -> dict[str, object]:
        question_status = "open" if status == "active" else "answered"
        state: dict[str, object] = {
            "schema_version": 1,
            "artifact_type": "collaborate",
            "decision_id": decision_id,
            "slug": "collaborate-route",
            "title": title,
            "updated": updated,
            "status": status,
            "acceptance": acceptance,
            "mode": "dialogue",
            "goal": "Resolve one public decision route.",
            "synthesis": ["The durable route must be transaction-owned."],
            "questions": [{"id": "q1", "prompt": "Which route owns the checkpoint?", "answer": "", "status": question_status}],
            "current_batch": ["q1"] if status == "active" else [],
            "settled": ["Inspect/schema/apply is the public surface."],
            "key_evidence": ["The renderer validates readback."],
            "open_items": [] if status != "active" else ["Choose the active route."],
            "blockers": [],
            "recommendation": "",
            "acceptance_evidence": [],
        }
        if status == "accepted":
            state["questions"] = [{"id": "q1", "prompt": "Which route owns the checkpoint?", "answer": "Use Collaborate.", "status": "answered"}]
            state["open_items"] = []
            state["recommendation"] = "Use Collaborate."
            state["acceptance_evidence"] = ["Focused CLI proof passed."]
        return state

    def request(self, operation: str, *, state: dict[str, object] | None = None, **extra: object) -> dict[str, object]:
        request: dict[str, object] = {
            "schema_version": 1,
            "operation": operation,
            "expected_revision": self.inspect()["revision"],
        }
        if state is not None:
            request["state"] = state
        request.update(extra)
        return request

    def test_collaborate_cli_create_accept_and_supersede_are_cas_checked(self) -> None:
        schema = self.cli("collaborate-schema", "create")
        self.assertEqual(schema.returncode, 0, schema.stderr)
        self.assertNotIn("destination", json.loads(schema.stdout))

        created = self.apply(self.request("create", state=self.state()))
        self.assertEqual(created.returncode, 0, created.stderr)
        current = self.memory / "collaborate/current.md"
        self.assertTrue(current.is_file())
        state = CONTRACT["validate_collaborate_artifact"](current.read_text(encoding="utf-8"))
        self.assertEqual(state["decision_id"], "c-collaborate-route")
        self.assertEqual(json.loads(created.stdout)["path"], "docs/teamwork/collaborate/current.md")

        stale = self.apply(
            {
                "schema_version": 1,
                "operation": "update",
                "expected_revision": "0" * 64,
                "state": self.state(title="Stale update"),
            }
        )
        self.assertNotEqual(stale.returncode, 0)
        self.assertEqual(json.loads(stale.stderr)["category"], "PREWRITE_SAFE")

        accepted = self.apply(self.request("accept", state=self.state(status="accepted", acceptance="accepted")))
        self.assertEqual(accepted.returncode, 0, accepted.stderr)
        accepted_state = CONTRACT["validate_collaborate_artifact"](current.read_text(encoding="utf-8"))
        self.assertEqual(accepted_state["acceptance"], "accepted")
        self.assertEqual(accepted_state["lineage"][-1]["operation"], "accept")

        successor = self.state(
            decision_id="c-successor-route",
            title="Choose the successor route",
            updated="2026-07-30T00:00:00Z",
        )
        superseded = self.apply(self.request("supersede", state=successor))
        self.assertEqual(superseded.returncode, 0, superseded.stderr)
        archive = next((self.memory / "collaborate").glob("2026-07-29-collaborate-route*.md"))
        archive_state = CONTRACT["validate_collaborate_artifact"](archive.read_text(encoding="utf-8"))
        self.assertEqual(archive_state["status"], "superseded")
        self.assertEqual(archive_state["superseded_by"], "c-successor-route")
        self.assertEqual(self.inspect()["active"]["state"]["decision_id"], "c-successor-route")

    def test_collaborate_import_consumes_legacy_sources_without_mutating_them(self) -> None:
        design = CONTRACT["design_schema"]("create")["state"]
        design.update(
            {
                "slug": "shared-route",
                "title": "Shared route",
                "updated": "2026-07-29",
                "acceptance": "accepted",
                "decision_frontier": [],
                "open_items": [],
            }
        )
        design_path = CONTRACT["design_path"](design)
        (self.memory / "design").mkdir()
        (self.project / design_path).write_text(CONTRACT["render_design_artifact"](design), encoding="utf-8")
        discussion = DiscussionTransactionTests.record(self, title="Shared route", updated="2026-07-29")
        discussion["slug"] = "shared-route"
        discussion["blockers"] = []
        (self.memory / "discussion").mkdir()
        (self.memory / "discussion/current.md").write_text(CONTRACT["render_discussion_artifact"](discussion), encoding="utf-8")
        legacy_before = {
            design_path: (self.project / design_path).read_bytes(),
            "docs/teamwork/discussion/current.md": (
                self.memory / "discussion/current.md"
            ).read_bytes(),
        }
        index = json.loads((self.memory / "index.json").read_text(encoding="utf-8"))
        index["active"]["design"] = design_path
        index["entries"].append(CONTRACT["_index_entry"]("design", design_path, design, active=True))
        (self.memory / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")

        inspected = self.inspect()
        self.assertEqual({row["type"] for row in inspected["sources"]}, {"design", "discussion"})
        imported = self.apply(
            {
                "schema_version": 1,
                "operation": "import",
                "expected_revision": inspected["revision"],
                "decision_id": "c-imported-route",
                "updated": "2026-07-29T01:02:03Z",
            }
        )
        self.assertEqual(imported.returncode, 0, imported.stderr)
        index = json.loads((self.memory / "index.json").read_text(encoding="utf-8"))
        self.assertEqual(index["active"]["collaborate"], "docs/teamwork/collaborate/current.md")
        self.assertIsNone(index["active"]["design"])
        self.assertEqual(len(index["collaborate_consumed_sources"]), 2)
        self.assertEqual(
            (self.project / design_path).read_bytes(),
            legacy_before[design_path],
        )
        self.assertEqual(
            (self.memory / "discussion/current.md").read_bytes(),
            legacy_before["docs/teamwork/discussion/current.md"],
        )
        design_entry = next(
            entry for entry in index["entries"] if entry["path"] == design_path
        )
        self.assertEqual(design_entry["status"], "superseded")
        self.assertEqual(
            design_entry["superseded_by"],
            "docs/teamwork/collaborate/current.md",
        )
        self.assertEqual(self.inspect()["sources"], [])

    def test_legacy_write_cli_is_a_zero_read_zero_write_tombstone(self) -> None:
        before = {
            path.relative_to(self.project).as_posix(): path.read_bytes()
            for path in self.project.rglob("*")
            if path.is_file()
        }
        missing_request = self.project / "must-not-be-read.json"
        cases = (
            ("schema", "create"),
            ("design-schema", "create"),
            (
                "apply",
                "--project-root",
                str(self.project),
                "--request-json",
                "{}",
            ),
            (
                "design-apply",
                "--project-root",
                str(self.project),
                "--request",
                str(missing_request),
            ),
        )
        for arguments in cases:
            with self.subTest(command=arguments[0]):
                result = self.cli(*arguments)
                self.assertEqual(result.returncode, 2)
                error = json.loads(result.stderr)
                self.assertEqual(error["category"], "PREWRITE_SAFE")
                self.assertIn(
                    "legacy lifecycle retired; use collaborate-*",
                    error["message"],
                )
                after = {
                    path.relative_to(self.project).as_posix(): path.read_bytes()
                    for path in self.project.rglob("*")
                    if path.is_file()
                }
                self.assertEqual(after, before)
                self.assertFalse(missing_request.exists())

    def test_collaborate_recovery_restores_create_preimage(self) -> None:
        before = {
            path.relative_to(self.project).as_posix(): path.read_bytes()
            for path in self.project.rglob("*")
            if path.is_file()
        }
        failed = self.apply(
            self.request("create", state=self.state()),
            env={"TEAMWORK_ARTIFACT_TRANSACTION_FAIL_INSTALL_N": "1"},
        )
        self.assertNotEqual(failed.returncode, 0)
        self.assertEqual(json.loads(failed.stderr)["category"], "INDETERMINATE")
        recovered = {
            path.relative_to(self.project).as_posix(): path.read_bytes()
            for path in self.project.rglob("*")
            if path.is_file()
        }
        self.assertEqual(recovered, before)
        self.assertFalse((self.memory / "collaborate/.collaborate-transaction.json").exists())


if __name__ == "__main__":
    unittest.main()
