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
CONTRACT = runpy.run_path(str(CLI), run_name="teamwork_goal_contract")


class GoalStateLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.project = Path(self.temporary.name) / "project"
        self.memory = self.project / "docs/teamwork"
        self.memory.mkdir(parents=True)
        for name in ("index.json", "current.md", "README.md"):
            (self.memory / name).write_bytes((TEMPLATES / name).read_bytes())

    def tearDown(self) -> None:
        self.temporary.cleanup()

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

    def inspect(self) -> dict[str, object]:
        result = self.command("goal-inspect", "--project-root", str(self.project))
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def state(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "artifact_type": "goal",
            "slug": "finish-v4",
            "title": "Finish Teamwork v4",
            "objective": "Deliver the accepted v4 architecture.",
            "scope": {"included": ["W4 artifact boundary"], "excluded": ["Release publication"]},
            "protected_boundaries": ["No release without explicit authority."],
            "invariants": ["Keep ordinary memory separate from Grill discussion."],
            "success_signal": "The real release matrix passes.",
            "budget": {"token_budget": 12000},
            "hard_stops": ["Required authority is unavailable."],
            "status": "active",
            "current_unmet_claim": "The release matrix has not passed.",
            "started_at": "2026-07-19",
            "updated": "2026-07-19",
            "next_strategy": "Implement the artifact transaction boundary.",
            "attempts": [],
            "state_revision": 1,
            "closure": None,
        }

    def apply(self, request: dict[str, object], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        return self.command(
            "goal-apply",
            "--project-root",
            str(self.project),
            "--request-json",
            json.dumps(request),
            env=env,
        )

    def start(self) -> dict[str, object]:
        request = {
            "schema_version": 1,
            "operation": "start",
            "expected_revision": self.inspect()["revision"],
            "state": self.state(),
        }
        result = self.apply(request)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def attempt_request(self, *, next_strategy: str = "Exercise fresh-process recovery before the next attempt.") -> dict[str, object]:
        return {
            "schema_version": 1,
            "operation": "attempt",
            "expected_revision": self.inspect()["revision"],
            "updated": "2026-07-20",
            "attempt": {
                "strategy": "Implement the artifact transaction boundary.",
                "current_unmet_claim": "Fresh-process recovery is not yet proven.",
                "evidence": ["Focused artifact tests reached the recoverable journal path."],
                "blocker": "A hard interruption has not been replayed by a new inspect process.",
                "strategy_delta": "Move from implementation to an interruption recovery proof.",
                "next_strategy": next_strategy,
            },
        }

    def snapshot(self) -> dict[str, tuple[object, ...]]:
        result: dict[str, tuple[object, ...]] = {}
        for path in sorted((self.project, *self.project.rglob("*")), key=str):
            relative = "." if path == self.project else path.relative_to(self.project).as_posix()
            info = path.lstat()
            if stat.S_ISREG(info.st_mode):
                result[relative] = ("file", stat.S_IMODE(info.st_mode), path.read_bytes())
            elif stat.S_ISDIR(info.st_mode):
                result[relative] = ("dir", stat.S_IMODE(info.st_mode))
            elif stat.S_ISLNK(info.st_mode):
                result[relative] = ("symlink", os.readlink(path))
        return result

    def test_goal_report_persists_full_state_before_attempt_one(self) -> None:
        output = self.start()
        path = output["path"]
        self.assertEqual(path, "docs/teamwork/reports/2026-07-19-finish-v4-goal.md")
        artifact = self.project / path
        state = CONTRACT["validate_goal_artifact"](artifact.read_text(encoding="utf-8"))
        for key in ("scope", "protected_boundaries", "invariants", "budget", "hard_stops", "current_unmet_claim", "attempts"):
            self.assertIn(key, state)
        self.assertEqual(state["attempts"], [])
        index = json.loads((self.memory / "index.json").read_text(encoding="utf-8"))
        self.assertEqual(index["active"]["progress"], path)
        self.assertNotIn("goal", index["active"])

    def test_attempt_persists_claim_evidence_blocker_delta_and_next_strategy(self) -> None:
        self.start()
        result = self.apply(self.attempt_request())
        self.assertEqual(result.returncode, 0, result.stderr)
        inspected = self.inspect()["active"]
        self.assertEqual(inspected["resume"]["attempt_count"], 1)
        self.assertEqual(inspected["resume"]["current_unmet_claim"], "Fresh-process recovery is not yet proven.")
        self.assertEqual(inspected["resume"]["next_strategy"], "Exercise fresh-process recovery before the next attempt.")
        state = inspected["state"]
        self.assertEqual(
            set(state["attempts"][0]),
            {"number", "strategy", "current_unmet_claim", "evidence", "blocker", "strategy_delta", "next_strategy", "recorded_at"},
        )

    def test_replay_of_an_unchanged_strategy_is_rejected(self) -> None:
        self.start()
        self.assertEqual(self.apply(self.attempt_request()).returncode, 0)
        replay = self.attempt_request(next_strategy="A distinct next action.")
        replay["attempt"]["strategy"] = "Implement the artifact transaction boundary."
        rejected = self.apply(replay)
        self.assertNotEqual(rejected.returncode, 0)
        self.assertEqual(json.loads(rejected.stderr)["category"], "PREWRITE_SAFE")

    def test_hard_interrupt_auto_recovers_exact_goal_and_index_preimage(self) -> None:
        self.start()
        before = self.snapshot()
        interrupted = self.apply(
            self.attempt_request(),
            env={"TEAMWORK_ARTIFACT_TRANSACTION_INTERRUPT_AFTER_BACKUP": "1"},
        )
        self.assertNotEqual(interrupted.returncode, 0)
        self.assertEqual(json.loads(interrupted.stderr)["category"], "INDETERMINATE")
        marker = self.memory / ".goal-transaction.json"
        self.assertTrue(marker.is_file())
        resumed = self.inspect()
        self.assertTrue(resumed["recovered"])
        self.assertFalse(marker.exists())
        self.assertEqual(self.snapshot(), before)

    def test_close_requires_direct_success_or_accepted_hard_stop_and_clears_active_pointer(self) -> None:
        started = self.start()
        close = {
            "schema_version": 1,
            "operation": "close",
            "expected_revision": self.inspect()["revision"],
            "updated": "2026-07-20",
            "closure": {"mode": "success", "success_evidence": ["The real release matrix passed."]},
        }
        result = self.apply(close)
        self.assertEqual(result.returncode, 0, result.stderr)
        index = json.loads((self.memory / "index.json").read_text(encoding="utf-8"))
        self.assertIsNone(index["active"]["progress"])
        state = CONTRACT["validate_goal_artifact"]((self.project / started["path"]).read_text(encoding="utf-8"))
        self.assertEqual(state["status"], "completed")
        self.assertIn("success_evidence", state["closure"])

    def test_hard_stop_requires_an_explicitly_accepted_stop_record(self) -> None:
        started = self.start()
        rejected = self.apply(
            {
                "schema_version": 1,
                "operation": "close",
                "expected_revision": self.inspect()["revision"],
                "updated": "2026-07-20",
                "closure": {"mode": "hard_stop"},
            }
        )
        self.assertNotEqual(rejected.returncode, 0)
        self.assertEqual(json.loads(rejected.stderr)["category"], "PREWRITE_SAFE")
        accepted = self.apply(
            {
                "schema_version": 1,
                "operation": "close",
                "expected_revision": self.inspect()["revision"],
                "updated": "2026-07-20",
                "closure": {"mode": "hard_stop", "accepted_hard_stop": "The user accepted the exhausted budget."},
            }
        )
        self.assertEqual(accepted.returncode, 0, accepted.stderr)
        state = CONTRACT["validate_goal_artifact"]((self.project / started["path"]).read_text(encoding="utf-8"))
        self.assertEqual(state["status"], "hard_stopped")
        self.assertEqual(state["closure"]["accepted_hard_stop"], "The user accepted the exhausted budget.")

    def test_goal_retained_journal_rejects_index_file_prefix_collisions_before_mutation(self) -> None:
        for collision in ("docs/teamwork/index.json.bak", "docs/teamwork/index.json/child"):
            with self.subTest(collision=collision):
                marker = self.memory / ".goal-transaction.json"
                if collision.endswith(".bak"):
                    (self.project / collision).write_bytes(b"must remain untouched\n")
                journal = {
                    "schema_version": 1,
                    "kind": "goal",
                    "phase": "prepared",
                    "token": "2" * 32,
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
                before = self.snapshot()

                rejected = self.command("goal-inspect", "--project-root", str(self.project))

                self.assertNotEqual(rejected.returncode, 0)
                self.assertEqual(json.loads(rejected.stderr)["category"], "INDETERMINATE")
                self.assertEqual(self.snapshot(), before)
                marker.unlink()


if __name__ == "__main__":
    unittest.main()
