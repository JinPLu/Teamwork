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
            "slug": "recovery-route",
            "title": title,
            "updated": updated,
            "goal": "Preserve one recoverable durable decision.",
            "current_branch": "Choose the artifact transition route.",
            "settled": ["Ordinary memory is not a Grill mirror."],
            "still_open": ["Does the transaction survive process loss?"],
            "return_path": "Resume at the recovery proof.",
            "blockers": ["The interruption proof is pending."],
            "convergence": "One exact recovery proof passes.",
            "key_evidence": ["The journal stores exact preimages."],
        }

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
            "schema_version": 1,
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
        updated = self.record(title="Choose the verified recovery route", updated="2026-07-20")
        result = self.apply(self.request("update", record=updated))
        self.assertEqual(result.returncode, 0, result.stderr)
        stale = self.apply(
            {
                "schema_version": 1,
                "operation": "update",
                "expected_revision": "0" * 64,
                "record": updated,
            }
        )
        self.assertNotEqual(stale.returncode, 0)
        self.assertEqual(json.loads(stale.stderr)["category"], "PREWRITE_SAFE")

        closed = self.apply(self.request("close", close_status="accepted"))
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

    def test_hard_interruption_auto_recovers_exact_preimage_on_next_inspect(self) -> None:
        self.create()
        before = self.snapshot()
        updated = self.record(title="Interrupted update", updated="2026-07-20")
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
            self.request("update", record=self.record(title="Will roll back", updated="2026-07-20")),
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


if __name__ == "__main__":
    unittest.main()
