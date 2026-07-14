from __future__ import annotations

import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from teamwork_tooling import live_canary
from teamwork_tooling.semantic_review import trajectory_sha256


RUBRIC_PATH = ROOT / "evals/teamwork/rubrics/teamwork-live-semantic-v1.json"
RUBRIC = json.loads(RUBRIC_PATH.read_text(encoding="utf-8"))


class Completed:
    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def trajectory(run_id: str = "installed-test-r1", secret: str = "RAW SECRET PROSE") -> dict[str, object]:
    return {
        "schema_version": 5,
        "record_type": "teamwork_live_trajectory",
        "run_id": run_id,
        "case_id": "test",
        "status": "completed",
        "execution_status": "completed",
        "structural_status": "passed",
        "model_provenance_status": "verified",
        "model": "fake-model",
        "resolved_model": "fake-model",
        "effort": "max",
        "usage": [{"input_tokens": 10, "output_tokens": 2}],
        "reported_costs": [0.01],
        "config_source": {"codex_version": "codex-cli 0.test"},
        "turns": [
            {
                "prompt": secret,
                "final_output": f"answer {secret}",
                "raw_events": [{"type": "agent_message", "text": secret}],
            }
        ],
    }


def review_for(record: dict[str, object]) -> dict[str, object]:
    return {
        "schema_version": 1,
        "run_id": record["run_id"],
        "trajectory_sha256": trajectory_sha256(record),
        "rubric_id": "teamwork-live-semantic-v1",
        "reviewer": {"kind": "HUMAN", "identity": "external-reviewer", "version": "1"},
        "verdict": "ACCEPT",
        "criteria": [
            {
                "criterion_id": criterion["id"],
                "outcome": "PASS",
                "score": 4,
                "evidence": [{"turn": 1}],
            }
            for criterion in RUBRIC["criteria"]
        ],
        "activation_evidence": {
            "claim": "AVAILABILITY_ONLY",
            "sources": [{"kind": "INSTALLED_FILE", "path": "skills/test/SKILL.md", "sha256": "a" * 64}],
        },
        "rationale": "External review completed against the retained record.",
        "confidence": 0.9,
        "timestamp": "2026-07-15T12:00:00Z",
    }


class LiveCanaryRunTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.workdir = self.base / "repo"
        self.workdir.mkdir()
        (self.workdir / ".git").mkdir()
        (self.workdir / "install.sh").write_text("#!/bin/sh\n", encoding="utf-8")
        (self.workdir / "scripts").mkdir()
        (self.workdir / "scripts/run-teamwork-live-eval.py").write_text("# fake\n", encoding="utf-8")
        self.case = self.base / "case.json"
        self.case.write_text(
            json.dumps({"id": "test", "sandbox": "read-only"}), encoding="utf-8"
        )
        self.auth = self.base / "source-auth.json"
        self.auth.write_text('{"token":"top-secret"}', encoding="utf-8")
        self.review_dir = self.base / "review"
        self.homes: list[Path] = []
        self.calls: list[tuple[list[str], dict[str, str]]] = []

    def tearDown(self) -> None:
        self.temp.cleanup()

    def argv(self, *extra: str) -> list[str]:
        return [
            "run", "--model", "fake-model", "--effort", "max",
            "--profile", "performance-first", "--workdir", str(self.workdir),
            "--cases", str(self.case), "--repeats", "1",
            "--timeout-seconds", "30", "--max-trajectories", "1",
            "--review-dir", str(self.review_dir), "--auth-file", str(self.auth),
            *extra,
        ]

    def fake_run(self, argv: list[str], **kwargs: object) -> Completed:
        env = dict(kwargs["env"])
        self.calls.append((list(argv), env))
        if argv[0] == "git":
            return Completed(stdout=f"{self.workdir}\n")
        codex_home = Path(env["CODEX_HOME"])
        if Path(argv[0]).name == "install.sh":
            self.assertEqual(
                argv[1:],
                ["--copy", "--no-notifications", "--profile", "performance-first", "codex"],
            )
            (codex_home / "skills/test").mkdir(parents=True)
            (codex_home / "skills/test/SKILL.md").write_text("installed skill", encoding="utf-8")
            (codex_home / "skills/.teamwork-version").write_text("9.9.9\n", encoding="utf-8")
            (codex_home / "skills/.teamwork-profile").write_text("performance-first\n", encoding="utf-8")
            (codex_home / "agents").mkdir()
            (codex_home / "agents/teamwork-worker.toml").write_text("model = 'fake'\n", encoding="utf-8")
            (codex_home / "AGENTS.md").write_text("installed policy\n", encoding="utf-8")
            (codex_home / "config.toml").write_text("max_threads = 9\n", encoding="utf-8")
            (self.workdir / ".teamwork-profile").write_text("mutated\n", encoding="utf-8")
            return Completed()
        auth_copy = codex_home / "auth.json"
        if "--dry-run" not in argv:
            self.assertEqual(auth_copy.read_text(encoding="utf-8"), self.auth.read_text(encoding="utf-8"))
            self.assertEqual(stat.S_IMODE(auth_copy.stat().st_mode), 0o600)
        else:
            self.assertFalse(auth_copy.exists())
        output = Path(argv[argv.index("--output") + 1])
        output.write_text(json.dumps(trajectory()) + "\n", encoding="utf-8")
        return Completed()

    def fake_mkdtemp(self, **_: object) -> str:
        home = self.base / f"isolated-{len(self.homes)}"
        home.mkdir()
        self.homes.append(home)
        return str(home)

    def test_rejects_max_bound_before_creating_review_dir(self) -> None:
        with self.assertRaisesRegex(live_canary.LiveCanaryError, "exceeds --max-trajectories"):
            live_canary.main(self.argv("--repeats", "2"))
        self.assertFalse(self.review_dir.exists())

    def test_rejects_non_read_only_case(self) -> None:
        self.case.write_text(json.dumps({"id": "test", "sandbox": "workspace-write"}), encoding="utf-8")
        with self.assertRaisesRegex(live_canary.LiveCanaryError, "must declare sandbox read-only"):
            live_canary.main(self.argv())
        self.assertFalse(self.review_dir.exists())

    def test_rejects_fake_git_directory_before_creating_review_dir(self) -> None:
        with self.assertRaisesRegex(live_canary.LiveCanaryError, "real Git worktree root"):
            live_canary.main(self.argv())
        self.assertFalse(self.review_dir.exists())

    def test_dry_run_rejects_auth_before_creating_review_dir(self) -> None:
        with self.assertRaisesRegex(live_canary.LiveCanaryError, "not allowed with --dry-run"):
            live_canary.main(self.argv("--dry-run"))
        self.assertFalse(self.review_dir.exists())

    def test_isolated_auth_cleanup_inventory_and_marker_restoration(self) -> None:
        marker = self.workdir / ".teamwork-profile"
        marker.write_text("original\n", encoding="utf-8")
        marker.chmod(0o640)
        with mock.patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "ambient-openai-secret",
                "AWS_SECRET_ACCESS_KEY": "ambient-cloud-secret",
                "LIVE_CANARY_SENTINEL_CREDENTIAL": "ambient-sentinel-secret",
            },
        ), mock.patch.object(
            live_canary.tempfile, "mkdtemp", self.fake_mkdtemp
        ), mock.patch.object(live_canary.subprocess, "run", self.fake_run):
            self.assertEqual(live_canary.main(self.argv()), 0)
        self.assertTrue(self.homes and not self.homes[0].exists())
        self.assertEqual(marker.read_text(encoding="utf-8"), "original\n")
        self.assertEqual(stat.S_IMODE(marker.stat().st_mode), 0o640)
        manifest_path = self.review_dir / live_canary.MANIFEST_NAME
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest_text = manifest_path.read_text(encoding="utf-8")
        self.assertNotIn("top-secret", manifest_text)
        self.assertNotIn(str(self.auth), manifest_text)
        self.assertTrue(
            all(str(self.auth) not in " ".join(argv) for argv, _ in self.calls)
        )
        for _, env in self.calls:
            self.assertNotIn("OPENAI_API_KEY", env)
            self.assertNotIn("AWS_SECRET_ACCESS_KEY", env)
            self.assertNotIn("LIVE_CANARY_SENTINEL_CREDENTIAL", env)
        child_envs = [env for argv, env in self.calls if argv[0] != "git"]
        self.assertTrue(child_envs)
        for env in child_envs:
            self.assertEqual(set(env), {"HOME", "CODEX_HOME", "PATH"})
            self.assertEqual(env["CODEX_HOME"], str(Path(env["HOME"]) / ".codex"))
        paths = {item["path"] for item in manifest["inventory"]}
        self.assertIn("skills/test/SKILL.md", paths)
        self.assertIn("agents/teamwork-worker.toml", paths)
        self.assertIn("AGENTS.md", paths)
        self.assertIn("config.toml", paths)
        self.assertIn("skills/.teamwork-version", paths)
        self.assertIn("skills/.teamwork-profile", paths)
        self.assertNotIn("auth.json", paths)
        self.assertEqual(manifest["activation_evidence"]["claim"], "AVAILABILITY_ONLY")
        self.assertEqual(manifest["package_version"], "9.9.9")
        self.assertEqual(manifest["host"]["codex_version"], "codex-cli 0.test")
        self.assertEqual(stat.S_IMODE(manifest_path.stat().st_mode), 0o400)
        self.assertEqual(stat.S_IMODE(self.review_dir.stat().st_mode), 0o700)

    def test_dry_run_uses_fake_install_and_runner_without_auth(self) -> None:
        argv = self.argv("--dry-run")
        auth_index = argv.index("--auth-file")
        del argv[auth_index : auth_index + 2]
        with mock.patch.object(live_canary.tempfile, "mkdtemp", self.fake_mkdtemp), mock.patch.object(
            live_canary.subprocess, "run", self.fake_run
        ):
            self.assertEqual(live_canary.main(argv), 0)
        self.assertIn("--dry-run", self.calls[-1][0])
        self.assertFalse(self.homes[0].exists())

    def test_cleanup_and_absent_marker_restoration_on_runner_failure(self) -> None:
        def failing(argv: list[str], **kwargs: object) -> Completed:
            completed = self.fake_run(argv, **kwargs)
            if argv[0] != "git" and Path(argv[0]).name != "install.sh":
                Path(argv[argv.index("--output") + 1]).unlink()
                return Completed(7, stderr="fake runner failure")
            return completed

        with mock.patch.object(live_canary.tempfile, "mkdtemp", self.fake_mkdtemp), mock.patch.object(
            live_canary.subprocess, "run", failing
        ):
            with self.assertRaisesRegex(live_canary.LiveCanaryError, "failed before producing output"):
                live_canary.main(self.argv())
        self.assertFalse(self.homes[0].exists())
        self.assertFalse((self.workdir / ".teamwork-profile").exists())

    def test_primary_and_temp_cleanup_failures_are_both_reported(self) -> None:
        def failing(argv: list[str], **kwargs: object) -> Completed:
            completed = self.fake_run(argv, **kwargs)
            if argv[0] != "git" and Path(argv[0]).name != "install.sh":
                Path(argv[argv.index("--output") + 1]).unlink()
                return Completed(7, stderr="primary fake runner failure")
            return completed

        with mock.patch.object(
            live_canary.tempfile, "mkdtemp", self.fake_mkdtemp
        ), mock.patch.object(
            live_canary.subprocess, "run", failing
        ), mock.patch.object(
            live_canary.shutil, "rmtree", side_effect=OSError("fake cleanup denied")
        ):
            with self.assertRaisesRegex(
                live_canary.LiveCanaryError,
                "primary fake runner failure.*finalization failures.*fake cleanup denied",
            ):
                live_canary.main(self.argv())

    def test_primary_and_profile_restoration_failures_are_both_reported(self) -> None:
        def failing(argv: list[str], **kwargs: object) -> Completed:
            completed = self.fake_run(argv, **kwargs)
            if argv[0] != "git" and Path(argv[0]).name != "install.sh":
                Path(argv[argv.index("--output") + 1]).unlink()
                return Completed(7, stderr="primary fake runner failure")
            return completed

        with mock.patch.object(
            live_canary.tempfile, "mkdtemp", self.fake_mkdtemp
        ), mock.patch.object(
            live_canary.subprocess, "run", failing
        ), mock.patch.object(
            live_canary, "_restore_marker",
            side_effect=live_canary.LiveCanaryError("fake marker restore denied"),
        ):
            with self.assertRaisesRegex(
                live_canary.LiveCanaryError,
                "primary fake runner failure.*finalization failures.*fake marker restore denied",
            ):
                live_canary.main(self.argv())


class LiveCanaryFinalizeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.review_dir = self.base / "review"
        self.reviews = self.review_dir / live_canary.REVIEWS_DIR
        self.reviews.mkdir(parents=True)
        self.record = trajectory()
        self.raw = self.review_dir / live_canary.RAW_NAME
        self.raw.write_text(json.dumps(self.record) + "\n", encoding="utf-8")
        manifest = {
            "record_type": "teamwork_installed_canary_manifest",
            "package_version": "9.9.9",
            "profile": "performance-first",
            "host": {"codex_version": "codex-cli 0.test"},
            "activation_evidence": {
                "claim": "AVAILABILITY_ONLY",
                "sources": [{
                    "kind": "INSTALLED_FILE",
                    "path": "skills/test/SKILL.md",
                    "sha256": "a" * 64,
                }],
            },
            "trajectories": [{
                "run_id": self.record["run_id"],
                "trajectory_sha256": trajectory_sha256(self.record),
            }],
        }
        (self.review_dir / live_canary.MANIFEST_NAME).write_text(json.dumps(manifest), encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def argv(self, *extra: str) -> list[str]:
        return ["finalize", "--review-dir", str(self.review_dir), "--rubric", str(RUBRIC_PATH), *extra]

    def write_review(self, value: dict[str, object] | None = None, name: str | None = None) -> Path:
        path = self.reviews / f"{name or self.record['run_id']}.json"
        path.write_text(json.dumps(value or review_for(self.record)), encoding="utf-8")
        return path

    def test_requires_exact_review_coverage(self) -> None:
        with self.assertRaisesRegex(live_canary.LiveCanaryError, "missing"):
            live_canary.main(self.argv())
        self.write_review()
        self.write_review(review_for(self.record), "unexpected")
        with self.assertRaisesRegex(live_canary.LiveCanaryError, "extra"):
            live_canary.main(self.argv())
        self.assertTrue(self.raw.exists())

    def test_invalid_review_preserves_raw(self) -> None:
        review = review_for(self.record)
        review["trajectory_sha256"] = "0" * 64
        self.write_review(review)
        with self.assertRaisesRegex(live_canary.LiveCanaryError, "trajectory_sha256 does not match"):
            live_canary.main(self.argv("--delete-raw"))
        self.assertTrue(self.raw.exists())
        self.assertTrue((self.reviews / f"{self.record['run_id']}.json").exists())
        self.assertFalse((self.review_dir / live_canary.SUMMARY_NAME).exists())

    def test_review_activation_sources_must_match_manifest(self) -> None:
        review = review_for(self.record)
        review["activation_evidence"]["sources"][0]["sha256"] = "b" * 64
        self.write_review(review)
        with self.assertRaisesRegex(live_canary.LiveCanaryError, "absent from the install manifest"):
            live_canary.main(self.argv("--delete-raw"))
        self.assertTrue(self.raw.exists())
        self.assertFalse((self.review_dir / live_canary.SUMMARY_NAME).exists())

    def test_success_writes_redacted_summary_then_deletes_raw(self) -> None:
        self.record["usage"] = [{
            "input_tokens": 10,
            "RAW SECRET PROSE AS DICT KEY": 999,
        }]
        self.raw.write_text(json.dumps(self.record) + "\n", encoding="utf-8")
        manifest_path = self.review_dir / live_canary.MANIFEST_NAME
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["trajectories"][0]["trajectory_sha256"] = trajectory_sha256(self.record)
        manifest["host"]["RAW SECRET HOST KEY"] = 123
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        review_path = self.write_review()
        self.assertEqual(live_canary.main(self.argv("--delete-raw")), 0)
        self.assertFalse(self.raw.exists())
        self.assertTrue(review_path.exists())
        summary_path = self.review_dir / live_canary.SUMMARY_NAME
        summary_text = summary_path.read_text(encoding="utf-8")
        self.assertNotIn("RAW SECRET PROSE", summary_text)
        self.assertNotIn("RAW SECRET PROSE AS DICT KEY", summary_text)
        self.assertNotIn("RAW SECRET HOST KEY", summary_text)
        for forbidden in ("prompt", "final_output", "raw_events", "rationale", "evidence"):
            self.assertNotIn(f'"{forbidden}"', summary_text)
        summary = json.loads(summary_text)
        result = summary["results"][0]
        self.assertEqual(result["verdict"], "ACCEPT")
        self.assertEqual(result["activation_claim"], "AVAILABILITY_ONLY")
        self.assertEqual(summary["package_version"], "9.9.9")
        self.assertEqual(summary["host"]["codex_version"], "codex-cli 0.test")
        self.assertIn("usage", result)
        self.assertIn("reported_costs", result)
        self.assertIn("trajectory_sha256", result["hashes"])


if __name__ == "__main__":
    unittest.main()
