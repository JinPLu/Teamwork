"""Fault-focused unit proof for the canonical release-index transaction."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest


SOURCE = pathlib.Path(__file__).resolve().parents[1] / "release-index-transaction.py"
SPEC = importlib.util.spec_from_file_location("release_index_transaction", SOURCE)
assert SPEC and SPEC.loader
TX = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TX)


def run(root: pathlib.Path, *arguments: str, input_text: str | None = None) -> str:
    result = subprocess.run(
        ["git", *arguments], cwd=root, text=True, input=input_text,
        capture_output=True, check=False,
    )
    if result.returncode:
        raise AssertionError(result.stderr)
    return result.stdout.strip()


def digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RepositoryFixture:
    def __init__(self, root: pathlib.Path) -> None:
        self.root = root
        run(root, "init", "-q")
        run(root, "config", "user.name", "Release Test")
        run(root, "config", "user.email", "release@example.invalid")
        (root / ".gitignore").write_text(".runtime/\n", encoding="utf-8")
        (root / "modify.txt").write_text("before\n", encoding="utf-8")
        (root / "delete.txt").write_text("delete\n", encoding="utf-8")
        (root / "stable.txt").write_text("same\n", encoding="utf-8")
        self.plan = root / "plan.md"
        self.evidence = root / "evidence.txt"
        self.plan.write_text("accepted plan\n", encoding="utf-8")
        self.evidence.write_text("barrier evidence\n", encoding="utf-8")
        run(root, "add", ".gitignore", "modify.txt", "delete.txt", "stable.txt", "plan.md", "evidence.txt")
        run(root, "commit", "-qm", "base")
        self.base = run(root, "rev-parse", "HEAD")
        (root / "modify.txt").write_text("after\n", encoding="utf-8")
        (root / "delete.txt").unlink()
        (root / "added.txt").write_text("added\n", encoding="utf-8")
        (root / "ita.txt").write_text("intent\n", encoding="utf-8")
        run(root, "add", "-N", "ita.txt")
        self.index = root / ".git/index"
        self.index_bytes = self.index.read_bytes()
        self.index_mode = self.index.stat().st_mode & 0o7777
        self.runtime = root / ".runtime"
        self.paths = self.runtime / "paths.json"
        self.manifest = self.runtime / "candidate.json"
        self.state_dir = self.runtime / "state"
        self.ledger = self.runtime / "inputs/ledger.jsonl"
        self.ownership = self.runtime / "inputs/ownership.json"
        self.forbidden = root / "forbidden"
        self.forbidden.mkdir()
        (self.forbidden / "user.txt").write_text("private\n", encoding="utf-8")
        self._write_contract()

    def _write_contract(self) -> None:
        self.ledger.parent.mkdir(parents=True, exist_ok=True)
        paths = [
            ("added.txt", "A"), ("delete.txt", "D"),
            ("ita.txt", "A"), ("modify.txt", "M"),
        ]
        metadata = {
            "schema_version": 1, "record_type": "metadata", "base_commit": self.base,
            "frozen_candidate_paths": [path for path, _ in paths],
        }
        rows = [metadata]
        for index, (path, status) in enumerate(paths, 1):
            rows.append({
                "ledger_id": f"v4-{index:05d}", "record_type": "candidate-path",
                "source_id": path, "owner": "TEST", "path": path,
                "preimage": {"file_type": "file", "mode": "0644", "sha256": "0" * 64},
                "disposition": "retire" if status == "D" else "revise",
                "evidence": "fixture", "reason": "fixture candidate",
                "release_candidate_eligible": True, "observed_status": status,
            })
        rows.append({
            "ledger_id": "v4-99999", "record_type": "forbidden-snapshot",
            "source_id": "forbidden/**", "owner": "FORBIDDEN", "path": "forbidden/**",
            "preimage": {"file_type": "directory", "mode": "0755", "sha256": TX.recursive_snapshot(self.forbidden)},
            "disposition": "preserve-user", "evidence": "fixture", "reason": "fixture protected tree",
            "release_candidate_eligible": False,
        })
        self.ledger.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        self.ownership.write_text(json.dumps({
            "schema_version": 1, "base_commit": self.base,
            "default_owner": "FORBIDDEN", "forbidden_prefixes": ["forbidden/"],
            "owners": [{
                "owner": "TEST", "paths": [path for path, _ in paths],
                "prefixes": [], "exclude": [], "exclude_prefixes": [],
            }],
        }), encoding="utf-8")

    def args(self) -> argparse.Namespace:
        return argparse.Namespace(
            project_root=str(self.root), ledger=str(self.ledger), ownership=str(self.ownership),
            paths=str(self.paths), manifest=str(self.manifest), state_dir=str(self.state_dir),
            scope_revision="7" * 64, candidate_id="C0", repair_generation=0,
            predecessor_manifest=None, predecessor_state_dir=None,
        )

    def assert_index_preserved(self, test: unittest.TestCase) -> None:
        test.assertEqual(self.index_bytes, self.index.read_bytes())
        test.assertEqual(self.index_mode, self.index.stat().st_mode & 0o7777)


class ReleaseIndexTransactionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temporary.name)
        self.fixture = RepositoryFixture(self.root)
        self.original_base = TX.BASE_COMMIT
        TX.BASE_COMMIT = self.fixture.base

    def tearDown(self) -> None:
        TX.BASE_COMMIT = self.original_base
        os.environ.pop(TX.FAILPOINT_ENV, None)
        self.temporary.cleanup()

    def prepare(self) -> dict:
        TX.prepare(self.fixture.args())
        return json.loads(self.fixture.manifest.read_text(encoding="utf-8"))

    def complete_candidate(self, verdict: str = "ACCEPT") -> dict:
        writing = self.prepare()
        TX.seal(argparse.Namespace(
            project_root=str(self.root), manifest=str(self.fixture.manifest),
            state_dir=str(self.fixture.state_dir),
        ))
        return self.complete_existing_candidate(writing, verdict)

    def complete_existing_candidate(self, writing: dict, verdict: str = "ACCEPT") -> dict:
        validation = self.fixture.runtime / "validation.json"
        validation.write_text(json.dumps({
            "schema_version": 1, "status": "PASS",
            **TX.candidate_triplet(writing),
            "candidate_fingerprint": writing["candidate_fingerprint"],
        }), encoding="utf-8")
        TX.validate(argparse.Namespace(
            project_root=str(self.root), manifest=str(self.fixture.manifest),
            evidence=str(validation), state_dir=str(self.fixture.state_dir),
        ))
        validated = json.loads(self.fixture.manifest.read_text(encoding="utf-8"))
        review = self.fixture.runtime / "review.json"
        review.write_text(json.dumps({
            "schema_version": 1,
            **TX.candidate_triplet(validated),
            "candidate_fingerprint": validated["candidate_fingerprint"],
            "reviewer_identity": "teamwork_deep_reviewer",
            "reviewer_model": "gpt-5.6-sol",
            "reviewer_effort": "max",
            "review_pass": "initial",
            "verdict": verdict,
            "findings": [],
            "validation_artifact_sha256": digest(validation),
            "plan": {"path": "plan.md", "sha256": digest(self.fixture.plan)},
            "evidence": [{"path": "evidence.txt", "sha256": digest(self.fixture.evidence)}],
        }), encoding="utf-8")
        TX.review(argparse.Namespace(
            project_root=str(self.root), manifest=str(self.fixture.manifest),
            review=str(review), state_dir=str(self.fixture.state_dir),
        ))
        return json.loads(self.fixture.manifest.read_text(encoding="utf-8"))

    def test_prepare_uses_base_index_typed_allowlist_and_preserves_real_index(self) -> None:
        manifest = self.prepare()
        self.assertEqual("writing", manifest["state"])
        self.assertEqual(["added.txt", "delete.txt", "ita.txt", "modify.txt"], [e["path"] for e in manifest["entries"]])
        self.assertEqual(["A", "D", "A", "M"], [e["status"] for e in manifest["entries"]])
        self.assertEqual("7" * 64, manifest["scope_revision"])
        self.assertEqual("C0", manifest["candidate_id"])
        self.assertEqual(0, manifest["repair_generation"])
        self.assertIsNone(manifest["sealed_manifest_sha256"])
        self.assertIsNone(manifest["review_artifact_sha256"])
        self.assertEqual(digest(self.fixture.paths), manifest["paths_manifest_sha256"])
        candidate_index = self.fixture.state_dir / "candidate.index"
        self.assertEqual(manifest["candidate_tree_oid"], TX.git(self.root, "write-tree", index=candidate_index, text=True).stdout.strip())
        ita = manifest["real_index_prestate"]["intent_to_add"]
        self.assertEqual([("ita.txt", "100644", 0, "20004000")], [(e["path"], e["mode"], e["stage"], e["flags"]) for e in ita])
        self.assertEqual(40, len(ita[0]["blob_oid"]))
        self.fixture.assert_index_preserved(self)

    def test_prepare_does_not_refresh_real_index_stat_cache(self) -> None:
        """An atomic source replacement must not make our probes write .git/index."""
        stable = self.root / "stable.txt"
        replacement = self.root / ".stable-replacement"
        replacement.write_bytes(stable.read_bytes())
        os.replace(replacement, stable)

        manifest = self.prepare()

        self.assertEqual("writing", manifest["state"])
        self.fixture.assert_index_preserved(self)

    def test_lifecycle_leases_and_artifacts_are_bound_to_one_candidate_triplet(self) -> None:
        writing = self.prepare()
        run_args = argparse.Namespace(
            project_root=str(self.root), manifest=str(self.fixture.manifest),
            state_dir=str(self.fixture.state_dir),
            command=[sys.executable, "-c", "import pathlib; assert pathlib.Path('added.txt').read_text() == 'added\\n'; assert not pathlib.Path('delete.txt').exists()"],
        )
        with self.assertRaisesRegex(TX.TransactionError, "state/base mismatch"):
            TX.run_command(run_args)
        lease_args = argparse.Namespace(project_root=str(self.root), manifest=str(self.fixture.manifest), state_dir=str(self.fixture.state_dir), writer_id="writer-1")
        TX.acquire_writer(lease_args)
        with self.assertRaisesRegex(TX.TransactionError, "writer leases"):
            TX.seal(argparse.Namespace(project_root=str(self.root), manifest=str(self.fixture.manifest), state_dir=str(self.fixture.state_dir)))
        TX.release_writer(lease_args)
        TX.seal(argparse.Namespace(project_root=str(self.root), manifest=str(self.fixture.manifest), state_dir=str(self.fixture.state_dir)))
        self.assertEqual(0, TX.run_command(run_args))
        self.assertEqual("sealed", json.loads(self.fixture.manifest.read_text())["state"])
        reviewed = self.complete_existing_candidate(writing)
        self.assertEqual("reviewed", reviewed["state"])
        self.assertEqual("ACCEPT", reviewed["review_verdict"])
        self.fixture.assert_index_preserved(self)

    def test_run_uses_disposable_git_metadata(self) -> None:
        self.prepare()
        TX.seal(argparse.Namespace(
            project_root=str(self.root), manifest=str(self.fixture.manifest),
            state_dir=str(self.fixture.state_dir),
        ))
        configuration = self.root / ".git" / "config"
        original_configuration = configuration.read_bytes()
        command = [
            sys.executable,
            "-c",
            "import os, subprocess; "
            "assert 'GIT_ALTERNATE_OBJECT_DIRECTORIES' not in os.environ; "
            "assert subprocess.check_output(['git', 'rev-parse', '--is-inside-work-tree'], text=True).strip() == 'true'; "
            "safe_env = {'HOME': os.environ['HOME'], 'PATH': os.environ.get('PATH', ''), 'GIT_CONFIG_NOSYSTEM': '1'}; "
            "subprocess.run(['git', 'status', '--porcelain=v1', '--untracked-files=all'], env=safe_env, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE); "
            "subprocess.run(['git', 'config', 'core.worktree', 'candidate-only'], check=True)",
        ]

        self.assertEqual(0, TX.run_command(argparse.Namespace(
            project_root=str(self.root), manifest=str(self.fixture.manifest),
            state_dir=str(self.fixture.state_dir), command=command,
        )))

        self.assertEqual(original_configuration, configuration.read_bytes())
        self.fixture.assert_index_preserved(self)

    def test_source_change_invalidates_candidate_and_repair_is_one_successor_generation(self) -> None:
        writing = self.prepare()
        lease_args = argparse.Namespace(project_root=str(self.root), manifest=str(self.fixture.manifest), state_dir=str(self.fixture.state_dir), writer_id="repair-writer")
        TX.acquire_writer(lease_args)
        (self.root / "modify.txt").write_text("late source write\n", encoding="utf-8")
        TX.release_writer(lease_args)
        with self.assertRaisesRegex(TX.TransactionError, "post-image changed"):
            TX.seal(argparse.Namespace(project_root=str(self.root), manifest=str(self.fixture.manifest), state_dir=str(self.fixture.state_dir)))
        (self.root / "modify.txt").write_text("after\n", encoding="utf-8")
        reviewed = self.complete_existing_after_seal(writing, "REVISE")
        (self.root / "modify.txt").write_text("merged repair\n", encoding="utf-8")
        args = self.fixture.args()
        args.candidate_id = "C1"
        args.repair_generation = 1
        args.predecessor_manifest = str(self.fixture.manifest)
        args.predecessor_state_dir = str(self.fixture.state_dir)
        args.paths = str(self.fixture.runtime / "successor-paths.json")
        args.manifest = str(self.fixture.runtime / "successor.json")
        args.state_dir = str(self.fixture.runtime / "successor-state")
        TX.prepare(args)
        successor = json.loads(pathlib.Path(args.manifest).read_text())
        self.assertEqual(1, successor["repair_generation"])
        self.assertEqual("C0", successor["predecessor_candidate_id"])
        self.assertNotEqual(reviewed["candidate_tree_oid"], successor["candidate_tree_oid"])
        successor_lifecycle = argparse.Namespace(project_root=str(self.root), manifest=args.manifest, state_dir=args.state_dir)
        TX.seal(successor_lifecycle)
        validation = self.fixture.runtime / "successor-validation.json"
        validation.write_text(json.dumps({"schema_version": 1, "status": "PASS", **TX.candidate_triplet(successor), "candidate_fingerprint": successor["candidate_fingerprint"]}), encoding="utf-8")
        TX.validate(argparse.Namespace(**vars(successor_lifecycle), evidence=str(validation)))
        review_path = self.fixture.runtime / "successor-review.json"
        review_value = {
            "schema_version": 1, **TX.candidate_triplet(successor),
            "candidate_fingerprint": successor["candidate_fingerprint"],
            "reviewer_identity": "teamwork_deep_reviewer", "reviewer_model": "gpt-5.6-sol",
            "reviewer_effort": "max", "review_pass": "initial", "verdict": "ACCEPT", "findings": [],
            "validation_artifact_sha256": digest(validation),
            "plan": {"path": "plan.md", "sha256": digest(self.fixture.plan)},
            "evidence": [{"path": "evidence.txt", "sha256": digest(self.fixture.evidence)}],
        }
        review_path.write_text(json.dumps(review_value), encoding="utf-8")
        review_args = argparse.Namespace(**vars(successor_lifecycle), review=str(review_path))
        with self.assertRaisesRegex(TX.TransactionError, "review pass exceeds"):
            TX.review(review_args)
        review_value["review_pass"] = "delta-recheck"
        review_value["verdict"] = "REVISE"
        review_path.write_text(json.dumps(review_value), encoding="utf-8")
        with self.assertRaisesRegex(TX.TransactionError, "cannot create another repair"):
            TX.review(review_args)
        review_value["verdict"] = "ACCEPT"
        review_path.write_text(json.dumps(review_value), encoding="utf-8")
        TX.review(review_args)
        self.assertEqual("reviewed", json.loads(pathlib.Path(args.manifest).read_text())["state"])
        args.candidate_id = "C2"
        args.repair_generation = 2
        with self.assertRaisesRegex(TX.TransactionError, "must be 0 or 1"):
            TX.prepare(args)

    def complete_existing_after_seal(self, writing: dict, verdict: str) -> dict:
        TX.seal(argparse.Namespace(project_root=str(self.root), manifest=str(self.fixture.manifest), state_dir=str(self.fixture.state_dir)))
        return self.complete_existing_candidate(writing, verdict)

    def test_commit_faults_restore_exact_index_before_commit(self) -> None:
        self.complete_candidate()
        message = self.fixture.runtime / "message.txt"
        message.write_text("release candidate\n", encoding="utf-8")
        args = argparse.Namespace(
            project_root=str(self.root), manifest=str(self.fixture.manifest),
            state_dir=str(self.fixture.state_dir), message_file=str(message),
        )
        for point in (
            "commit.before_stage", "commit.after_stage", "commit.before_compare",
            "commit.after_compare", "commit.before_invoke",
        ):
            with self.subTest(point=point):
                os.environ[TX.FAILPOINT_ENV] = point
                with self.assertRaises(TX.TransactionError):
                    TX.commit(args)
                self.fixture.assert_index_preserved(self)
                self.assertEqual(self.fixture.base, run(self.root, "rev-parse", "HEAD"))

    def test_commit_stages_exact_reviewed_tree_and_invokes_one_commit(self) -> None:
        reviewed = self.complete_candidate()
        message = self.fixture.runtime / "message.txt"
        message.write_text("release candidate\n", encoding="utf-8")
        TX.commit(argparse.Namespace(
            project_root=str(self.root), manifest=str(self.fixture.manifest),
            state_dir=str(self.fixture.state_dir), message_file=str(message),
        ))
        self.assertNotEqual(self.fixture.base, run(self.root, "rev-parse", "HEAD"))
        self.assertEqual(reviewed["candidate_tree_oid"], run(self.root, "rev-parse", "HEAD^{tree}"))
        self.assertEqual("release candidate", run(self.root, "log", "-1", "--pretty=%s"))

    def test_commit_rechecks_sealed_review_plan_and_evidence_bindings(self) -> None:
        self.complete_candidate()
        message = self.fixture.runtime / "message.txt"
        message.write_text("release candidate\n", encoding="utf-8")
        args = argparse.Namespace(
            project_root=str(self.root), manifest=str(self.fixture.manifest),
            state_dir=str(self.fixture.state_dir), message_file=str(message),
        )
        original_manifest = self.fixture.manifest.read_bytes()
        review = self.fixture.runtime / "review.json"
        original_review = review.read_bytes()
        validation = self.fixture.runtime / "validation.json"
        original_validation = validation.read_bytes()
        original_plan = self.fixture.plan.read_bytes()
        original_evidence = self.fixture.evidence.read_bytes()

        def remove_manifest_field(field: str) -> None:
            manifest = json.loads(original_manifest)
            manifest.pop(field)
            self.fixture.manifest.write_text(json.dumps(manifest), encoding="utf-8")

        cases = (
            ("review artifact", lambda: review.write_text("{}\n", encoding="utf-8"), "review artifact candidate triplet mismatch"),
            ("validation artifact", lambda: validation.write_text("{}\n", encoding="utf-8"), "validation artifact candidate triplet mismatch"),
            ("bound Plan", lambda: self.fixture.plan.write_text("tampered\n", encoding="utf-8"), "Plan evidence hash mismatch"),
            ("bound evidence", lambda: self.fixture.evidence.write_text("tampered\n", encoding="utf-8"), "review evidence .*hash mismatch"),
            ("review binding", lambda: remove_manifest_field("review_binding"), "review binding differs"),
            ("review artifact hash", lambda: remove_manifest_field("review_artifact_sha256"), "unsupported candidate manifest schema"),
            ("sealed manifest hash", lambda: remove_manifest_field("sealed_manifest_sha256"), "unsupported candidate manifest schema"),
        )
        for label, tamper, expected in cases:
            with self.subTest(binding=label):
                try:
                    tamper()
                    with self.assertRaisesRegex(TX.TransactionError, expected):
                        TX.commit(args)
                    self.fixture.assert_index_preserved(self)
                    self.assertEqual(self.fixture.base, run(self.root, "rev-parse", "HEAD"))
                finally:
                    self.fixture.manifest.write_bytes(original_manifest)
                    review.write_bytes(original_review)
                    validation.write_bytes(original_validation)
                    self.fixture.plan.write_bytes(original_plan)
                    self.fixture.evidence.write_bytes(original_evidence)

    def test_failed_commit_invocation_restores_index_and_head(self) -> None:
        self.complete_candidate()
        message = self.fixture.runtime / "message.txt"
        message.write_text("release candidate\n", encoding="utf-8")
        hook = self.root / ".git/hooks/pre-commit"
        hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        os.chmod(hook, 0o755)
        with self.assertRaises(TX.TransactionError):
            TX.commit(argparse.Namespace(
                project_root=str(self.root), manifest=str(self.fixture.manifest),
                state_dir=str(self.fixture.state_dir), message_file=str(message),
            ))
        self.fixture.assert_index_preserved(self)
        self.assertEqual(self.fixture.base, run(self.root, "rev-parse", "HEAD"))

    def test_forbidden_preimage_change_blocks_prepare_without_index_mutation(self) -> None:
        self.assertIn("forbidden/user.txt", TX.working_delta_paths(self.root, self.fixture.base))
        self.prepare()
        self.fixture.assert_index_preserved(self)
        (self.fixture.forbidden / "user.txt").write_text("tampered\n", encoding="utf-8")
        with self.assertRaisesRegex(TX.TransactionError, "forbidden-preimage-changed"):
            TX.prepare(self.fixture.args())
        self.fixture.assert_index_preserved(self)

    def test_prepare_failpoints_never_change_real_index(self) -> None:
        for point in (
            "prepare.before_read_tree", "prepare.after_read_tree",
            "prepare.before_stage", "prepare.after_stage",
            "prepare.before_compare", "prepare.after_compare",
        ):
            with self.subTest(point=point):
                os.environ[TX.FAILPOINT_ENV] = point
                with self.assertRaises(TX.TransactionError):
                    TX.prepare(self.fixture.args())
                self.fixture.assert_index_preserved(self)
        os.environ.pop(TX.FAILPOINT_ENV, None)

    def test_missing_malformed_and_unlisted_inputs_fail_closed(self) -> None:
        self.fixture.ledger.unlink()
        with self.assertRaises(TX.TransactionError):
            TX.prepare(self.fixture.args())
        self.fixture.ledger.write_text("not-json\n", encoding="utf-8")
        with self.assertRaises(TX.TransactionError):
            TX.prepare(self.fixture.args())
        self.fixture._write_contract()
        (self.root / "unlisted.txt").write_text("must not leak\n", encoding="utf-8")
        with self.assertRaisesRegex(TX.TransactionError, "unlisted working delta"):
            TX.prepare(self.fixture.args())
        self.fixture.assert_index_preserved(self)

    def test_restore_is_atomic_and_recovers_exact_bytes_mode_and_ita_flags(self) -> None:
        self.prepare()
        self.fixture.index.write_bytes(b"corrupt index")
        os.chmod(self.fixture.index, 0o600)
        TX.restore(argparse.Namespace(project_root=str(self.root), state_dir=str(self.fixture.state_dir)))
        self.fixture.assert_index_preserved(self)
        snapshot = TX.snapshot_index(self.root)
        self.assertEqual([("ita.txt", "100644", 0, "20004000")], [(e["path"], e["mode"], e["stage"], e["flags"]) for e in snapshot["intent_to_add"]])


if __name__ == "__main__":
    unittest.main()
