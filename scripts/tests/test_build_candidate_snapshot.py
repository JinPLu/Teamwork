from __future__ import annotations

import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/build-candidate-snapshot.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_candidate_snapshot", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BCS = load_module()


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.pop("GIT_INDEX_FILE", None)
    env.pop("GIT_ALTERNATE_OBJECT_DIRECTORIES", None)
    env.pop("GIT_COMMON_DIR", None)
    return subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, check=False)


def init_source_repo(root: Path) -> None:
    run(["git", "init"], root).check_returncode()
    run(["git", "config", "user.email", "fixture@example.invalid"], root).check_returncode()
    run(["git", "config", "user.name", "Fixture"], root).check_returncode()
    (root / "scripts").mkdir()
    (root / "scripts/verify-no-hardlinked-git-objects.py").write_text(
        """#!/usr/bin/env python3
import argparse
import os
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument("--source", required=True)
p.add_argument("--snapshot", required=True)
args = p.parse_args()
source = Path(args.source)
snapshot = Path(args.snapshot)
if not source.is_dir() or not snapshot.is_dir():
    raise SystemExit(1)
for snap_file in snapshot.rglob("*"):
    if not snap_file.is_file():
        continue
    for src_file in source.rglob("*"):
        if src_file.is_file() and os.stat(snap_file).st_ino == os.stat(src_file).st_ino and os.stat(snap_file).st_dev == os.stat(src_file).st_dev:
            raise SystemExit(1)
""",
        encoding="utf-8",
    )
    os.chmod(root / "scripts/verify-no-hardlinked-git-objects.py", 0o755)
    (root / "candidate.txt").write_text("base\n", encoding="utf-8")
    run(["git", "add", "."], root).check_returncode()
    run(["git", "commit", "-m", "base"], root).check_returncode()
    run(["git", "tag", "base-tag"], root).check_returncode()


def object_digest(root: Path) -> str:
    digest, _ = BCS.fingerprint_tree(root / ".git" / "objects")
    return digest


class BuildCandidateSnapshotTests(unittest.TestCase):
    def test_builds_full_history_snapshot_and_strict_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            source = base / "source"
            source.mkdir()
            init_source_repo(source)
            (source / "candidate.txt").write_text("candidate\n", encoding="utf-8")
            state = base / "state"
            state.mkdir()
            paths = state / "final-candidate-paths.z"
            paths.write_bytes(b"candidate.txt\0")
            snapshot_parent = base / "snapshot-parent"
            snapshot_parent.mkdir()
            snapshot = snapshot_parent / "snapshot"
            report = state / "snapshot-isolation-report.json"
            before = object_digest(source)

            result = run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--project-root",
                    str(source),
                    "--paths",
                    str(paths),
                    "--snapshot-root",
                    str(snapshot),
                    "--report",
                    str(report),
                ],
                ROOT,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(object_digest(source), before)
            self.assertTrue((snapshot / ".git/objects").is_dir())
            self.assertEqual((snapshot / "candidate.txt").read_text(encoding="utf-8"), "candidate\n")
            self.assertEqual(run(["git", "rev-parse", "base-tag^{commit}"], snapshot).returncode, 0)
            data = json.loads(report.read_text(encoding="utf-8"))
            BCS.validate_snapshot_report(data)
            self.assertEqual(data["snapshot_root"], os.path.realpath(snapshot))
            self.assertEqual(data["candidate_path_count"], 1)

    def test_safe_target_validation_rejects_named_negative_cases_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            source = base / "source"
            source.mkdir()
            init_source_repo(source)
            state = base / "state"
            state.mkdir()
            paths = state / "final-candidate-paths.z"
            paths.write_bytes(b"candidate.txt\0")
            symlink_parent_target = base / "symlink-target"
            symlink_parent_target.mkdir()
            symlink_parent = base / "symlink-parent"
            symlink_parent.symlink_to(symlink_parent_target, target_is_directory=True)
            existing_snapshot = base / "existing-snapshot"
            existing_snapshot.mkdir()
            existing_report = state / "existing-report.json"
            existing_report.write_text("preexisting\n", encoding="utf-8")
            paths_symlink = state / "paths-link.z"
            paths_symlink.symlink_to(paths)
            paths_dir = state / "paths-dir.z"
            paths_dir.mkdir()
            cases = [
                ("root", Path("/"), state / "r-root.json", paths),
                ("home", Path.home(), state / "r-home.json", paths),
                ("project-root", source, state / "r-project.json", paths),
                ("project-git", source / ".git", state / "r-git.json", paths),
                ("source-objects", source / ".git/objects", state / "r-objects.json", paths),
                ("ancestor-overlap", base / "a/snapshot", base / "a/snapshot/report.json", paths),
                ("descendant-overlap", base / "b/snapshot/child", base / "b/snapshot", paths),
                ("same-path-overlap", base / "same", base / "same", paths),
                ("symlink-parent", symlink_parent / "snapshot", state / "r-symlink.json", paths),
                ("preexisting-snapshot", existing_snapshot, state / "r-existing-snapshot.json", paths),
                ("preexisting-report", base / "snap-existing-report", existing_report, paths),
                ("report-inside-snapshot", base / "inside-snapshot", base / "inside-snapshot/report.json", paths),
                ("snapshot-inside-report-parent", state / "snap-under-report-parent", state / "r-parent.json", paths),
                ("paths-file-overlap", paths, state / "r-paths-overlap.json", paths),
                ("snapshot-inside-paths-parent", state / "snap-under-paths-parent", base / "outside-report.json", paths),
                ("paths-missing", base / "missing-paths-snap", state / "r-missing-paths.json", state / "missing.z"),
                ("paths-symlink", base / "paths-symlink-snap", state / "r-paths-symlink.json", paths_symlink),
                ("paths-nonregular", base / "paths-dir-snap", state / "r-paths-dir.json", paths_dir),
            ]
            for name, snapshot, report, case_paths in cases:
                with self.subTest(name=name):
                    if not snapshot.parent.exists() and snapshot.parent != Path("/"):
                        snapshot.parent.mkdir(parents=True, exist_ok=True)
                    if not report.parent.exists() and report.parent != Path("/"):
                        report.parent.mkdir(parents=True, exist_ok=True)
                    snapshot_existed = snapshot.exists()
                    report_existed = report.exists()
                    before = object_digest(source)
                    result = run(
                        [
                            sys.executable,
                            str(SCRIPT),
                            "--project-root",
                            str(source),
                            "--paths",
                            str(case_paths),
                            "--snapshot-root",
                            str(snapshot),
                            "--report",
                            str(report),
                        ],
                        ROOT,
                    )
                    self.assertNotEqual(result.returncode, 0, name)
                    self.assertIn("PREWRITE_SAFE:", result.stderr)
                    self.assertEqual(object_digest(source), before, name)
                    if not snapshot_existed and name not in {"root", "home"}:
                        self.assertFalse(snapshot.exists(), name)
                    if not report_existed:
                        self.assertFalse(report.exists(), name)

    def test_strict_report_validation_rejects_malformed_proofs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            snapshot = base / "snapshot"
            (snapshot / ".git/objects").mkdir(parents=True)
            paths = base / "final-candidate-paths.z"
            paths.write_bytes(b"x\0")
            digest = "0" * 64
            valid = {
                "schema_version": 1,
                "success": True,
                "project_root": os.path.realpath(base),
                "paths_file": os.path.realpath(paths),
                "snapshot_root": os.path.realpath(snapshot),
                "candidate_path_count": 1,
                "safe_target": dict(BCS.STRICT_SAFE_TARGET),
                "object_isolation": {
                    "source_objects_pre_digest": digest,
                    "source_objects_post_digest": digest,
                    "source_objects_unchanged": True,
                    "source_index_refs_worktree_unchanged": True,
                },
                "git": dict(BCS.STRICT_GIT_PROOF),
            }
            BCS.validate_snapshot_report(valid)

            mutations = {
                "success_false": lambda data: data.__setitem__("success", False),
                "missing_key": lambda data: data.pop("git"),
                "extra_key": lambda data: data.__setitem__("extra", True),
                "noncanonical_path": lambda data: data.__setitem__("snapshot_root", str(snapshot / ".." / "snapshot")),
                "bool_candidate_count": lambda data: data.__setitem__("candidate_path_count", True),
                "digest_mismatch": lambda data: data["object_isolation"].__setitem__("source_objects_post_digest", "1" * 64),
                "uppercase_digest": lambda data: data["object_isolation"].__setitem__("source_objects_pre_digest", "A" * 64),
                "missing_git_dir": lambda data: data.__setitem__("snapshot_root", os.path.realpath(base / "no-git")),
                "missing_objects_dir": lambda data: (shutil.rmtree(snapshot / ".git/objects"), None),
                "object_false": lambda data: data["object_isolation"].__setitem__("source_objects_unchanged", False),
                "git_false": lambda data: data["git"].__setitem__("no_alternates", False),
            }
            for name, mutate in mutations.items():
                with self.subTest(name=name):
                    (snapshot / ".git/objects").mkdir(parents=True, exist_ok=True)
                    candidate = json.loads(json.dumps(valid))
                    mutate(candidate)
                    with self.assertRaises(BCS.SnapshotError):
                        BCS.validate_snapshot_report(candidate)


if __name__ == "__main__":
    unittest.main()
