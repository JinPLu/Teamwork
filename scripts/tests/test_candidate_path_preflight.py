from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/candidate-path-preflight.py"
FIXTURE = ROOT / "scripts/tests/fixtures/v5-unified-collaborate-path-ownership.json"


def load_module():
    spec = importlib.util.spec_from_file_location("candidate_path_preflight", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CPF = load_module()


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)


def init_repo(root: Path) -> None:
    run(["git", "init"], root).check_returncode()
    run(["git", "config", "user.email", "fixture@example.invalid"], root).check_returncode()
    run(["git", "config", "user.name", "Fixture"], root).check_returncode()
    (root / "README.md").write_text("base\n", encoding="utf-8")
    (root / ".gitignore").write_text(".codegraph/\n", encoding="utf-8")
    (root / "scripts/tests").mkdir(parents=True)
    (root / "scripts/candidate-path-preflight.py").write_text("base\n", encoding="utf-8")
    run(["git", "add", "."], root).check_returncode()
    run(["git", "commit", "-m", "base"], root).check_returncode()


def root_fingerprint(root: Path) -> list[dict[str, object]]:
    return CPF.tree_fingerprint(root)


class CandidatePathPreflightTests(unittest.TestCase):
    def test_fixture_classifies_required_boundaries_exactly_once(self) -> None:
        ownership = CPF.load_ownership(FIXTURE)
        CPF.validate_fixture_invariants(ownership)
        self.assertEqual(CPF.require_exact_owner(".gitignore", ownership), "Public docs/version/metadata")
        self.assertEqual(
            CPF.require_exact_owner("scripts/build-candidate-snapshot.py", ownership),
            "Candidate preflight",
        )
        self.assertEqual(
            CPF.require_exact_owner(".claude/" + "settings." + "local.json", ownership),
            "FORBIDDEN",
        )
        with self.assertRaisesRegex(CPF.PreflightError, "unowned path"):
            CPF.require_exact_owner("unplanned.txt", ownership)

    def test_parse_porcelain_z_preserves_rename_source_and_nul_paths(self) -> None:
        raw = b"R  scripts/build-candidate-snapshot.py\0scripts/candidate-path-preflight.py\0 M .gitignore\0"
        records = CPF.parse_porcelain_z(raw)
        self.assertEqual(
            records,
            [
                {"status": " M", "path": ".gitignore", "orig_path": None, "directory_record": False},
                {
                    "status": "R ",
                    "path": "scripts/build-candidate-snapshot.py",
                    "orig_path": "scripts/candidate-path-preflight.py",
                    "directory_record": False,
                    "orig_directory_record": False,
                },
            ],
        )

    def test_parse_porcelain_z_accepts_trailing_slash_only_for_forbidden_claude(self) -> None:
        self.assertEqual(
            CPF.parse_porcelain_z(b"?? .claude/worktrees/agent-a6c892a8a1fcfa567/\0"),
            [
                {
                    "status": "??",
                    "path": ".claude/worktrees/agent-a6c892a8a1fcfa567",
                    "orig_path": None,
                    "directory_record": True,
                }
            ],
        )
        with self.assertRaisesRegex(CPF.PreflightError, "unsafe repository path"):
            CPF.parse_porcelain_z(b"?? nested-repo/\0")

    def test_rename_across_owners_fails_closed(self) -> None:
        ownership = CPF.load_ownership(FIXTURE)
        with self.assertRaisesRegex(CPF.PreflightError, "rename outside one owner"):
            CPF.classify_records(
                [{"status": "R ", "path": ".gitignore", "orig_path": "scripts/candidate-path-preflight.py"}],
                ownership,
            )

    def test_capture_compare_writes_final_nul_paths_and_preserves_claude_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            init_repo(root)
            state = Path(tmp) / "state"
            state.mkdir()
            claude = root / ".claude" / ("settings." + "local.json")
            claude.parent.mkdir()
            claude.write_text('{"permission":"user"}\n', encoding="utf-8")
            baseline = state / "baseline.json"
            capture = run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "capture",
                    "--project-root",
                    str(root),
                    "--ownership",
                    str(FIXTURE),
                    "--state-dir",
                    str(state),
                    "--output",
                    str(baseline),
                ],
                ROOT,
            )
            self.assertEqual(capture.returncode, 0, capture.stderr)

            (root / "scripts/candidate-path-preflight.py").write_text("candidate\n", encoding="utf-8")
            report = state / "final-report.json"
            compare = run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "compare",
                    "--project-root",
                    str(root),
                    "--ownership",
                    str(FIXTURE),
                    "--baseline",
                    str(baseline),
                    "--state-dir",
                    str(state),
                    "--report",
                    str(report),
                ],
                ROOT,
            )
            self.assertEqual(compare.returncode, 0, compare.stderr)
            self.assertEqual(
                (state / "final-candidate-paths.z").read_bytes(),
                b"scripts/candidate-path-preflight.py\0",
            )
            data = json.loads(report.read_text(encoding="utf-8"))
            self.assertTrue(data["success"])
            self.assertTrue(data["forbidden_claude_unchanged"])

    def test_compare_rejects_changed_claude_tree_before_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            init_repo(root)
            state = Path(tmp) / "state"
            state.mkdir()
            claude = root / ".claude" / ("settings." + "local.json")
            claude.parent.mkdir()
            claude.write_text("before\n", encoding="utf-8")
            baseline = state / "baseline.json"
            self.assertEqual(
                run(
                    [
                        sys.executable,
                        str(SCRIPT),
                        "capture",
                        "--project-root",
                        str(root),
                        "--ownership",
                        str(FIXTURE),
                        "--state-dir",
                        str(state),
                        "--output",
                        str(baseline),
                    ],
                    ROOT,
                ).returncode,
                0,
            )
            claude.write_text("after\n", encoding="utf-8")
            result = run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "compare",
                    "--project-root",
                    str(root),
                    "--ownership",
                    str(FIXTURE),
                    "--baseline",
                    str(baseline),
                    "--state-dir",
                    str(state),
                    "--report",
                    str(state / "final-report.json"),
                ],
                ROOT,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(".claude forbidden state changed", result.stderr)
            self.assertFalse((state / "final-report.json").exists())
            self.assertFalse((state / "final-candidate-paths.z").exists())

    def test_untracked_nested_repo_under_claude_is_forbidden_fingerprinted_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            init_repo(root)
            state = Path(tmp) / "state"
            state.mkdir()
            nested = root / ".claude/worktrees/agent-a6c892a8a1fcfa567"
            nested.mkdir(parents=True)
            run(["git", "init"], nested).check_returncode()
            run(["git", "config", "user.email", "nested@example.invalid"], nested).check_returncode()
            run(["git", "config", "user.name", "Nested"], nested).check_returncode()
            (nested / "inner.txt").write_text("inner\n", encoding="utf-8")
            run(["git", "add", "."], nested).check_returncode()
            run(["git", "commit", "-m", "nested"], nested).check_returncode()
            before_source = root_fingerprint(root)

            baseline = state / "baseline.json"
            capture = run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "capture",
                    "--project-root",
                    str(root),
                    "--ownership",
                    str(FIXTURE),
                    "--state-dir",
                    str(state),
                    "--output",
                    str(baseline),
                ],
                ROOT,
            )
            self.assertEqual(capture.returncode, 0, capture.stderr)
            self.assertEqual(root_fingerprint(root), before_source)
            baseline_data = json.loads(baseline.read_text(encoding="utf-8"))
            self.assertEqual(baseline_data["records"][0]["owner"], "FORBIDDEN")
            self.assertTrue(baseline_data["records"][0]["directory_record"])
            saved_claude = Path(tmp) / "repo-saved-claude"
            shutil.copytree(root / ".claude", saved_claude, symlinks=True)

            unchanged_report = state / "unchanged-report.json"
            unchanged = run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "compare",
                    "--project-root",
                    str(root),
                    "--ownership",
                    str(FIXTURE),
                    "--baseline",
                    str(baseline),
                    "--state-dir",
                    str(state / "unchanged"),
                    "--report",
                    str(unchanged_report),
                ],
                ROOT,
            )
            self.assertEqual(unchanged.returncode, 0, unchanged.stderr)
            self.assertEqual(root_fingerprint(root), before_source)
            self.assertEqual((state / "unchanged/final-candidate-paths.z").read_bytes(), b"")

            for name, mutate in (
                ("inner-file", lambda: (nested / "inner.txt").write_text("changed\n", encoding="utf-8")),
                ("inner-path", lambda: (nested / "new.txt").write_text("new\n", encoding="utf-8")),
                ("inner-symlink", lambda: (nested / "link").symlink_to("inner.txt")),
            ):
                with self.subTest(name=name):
                    shutil.rmtree(root / ".claude")
                    shutil.copytree(saved_claude, root / ".claude", symlinks=True)
                    mutate()
                    result = run(
                        [
                            sys.executable,
                            str(SCRIPT),
                            "compare",
                            "--project-root",
                            str(root),
                            "--ownership",
                            str(FIXTURE),
                            "--baseline",
                            str(baseline),
                            "--state-dir",
                            str(state / name),
                            "--report",
                            str(state / f"{name}.json"),
                        ],
                        ROOT,
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(".claude forbidden state changed", result.stderr)
                    self.assertFalse((state / f"{name}.json").exists())

    def test_capture_rejects_unowned_dirty_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            init_repo(root)
            (root / "unplanned.txt").write_text("no owner\n", encoding="utf-8")
            state = Path(tmp) / "state"
            state.mkdir()
            result = run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "capture",
                    "--project-root",
                    str(root),
                    "--ownership",
                    str(FIXTURE),
                    "--state-dir",
                    str(state),
                    "--output",
                    str(state / "baseline.json"),
                ],
                ROOT,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unowned path: unplanned.txt", result.stderr)
            self.assertFalse((state / "baseline.json").exists())


if __name__ == "__main__":
    unittest.main()
