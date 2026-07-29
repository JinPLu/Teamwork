from __future__ import annotations

import importlib.util
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/verify-no-hardlinked-git-objects.py"


def load_module():
    spec = importlib.util.spec_from_file_location("verify_no_hardlinked_git_objects", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VERIFY = load_module()


def tree_snapshot(root: Path) -> dict[str, tuple[str, int, int, int, str]]:
    result: dict[str, tuple[str, int, int, int, str]] = {}
    for path in sorted(root.rglob("*")):
        st = path.lstat()
        rel = path.relative_to(root).as_posix()
        mode = stat.S_IMODE(st.st_mode)
        if path.is_symlink():
            result[rel] = ("symlink", mode, st.st_nlink, st.st_ino, os.readlink(path))
        elif path.is_file():
            result[rel] = ("file", mode, st.st_nlink, st.st_ino, path.read_text(encoding="utf-8"))
        elif path.is_dir():
            result[rel] = ("directory", mode, st.st_nlink, st.st_ino, "")
    return result


class VerifyNoHardlinkedGitObjectsTests(unittest.TestCase):
    def run_helper(self, source: Path, snapshot: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--source", str(source), "--snapshot", str(snapshot)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_distinct_object_trees_pass_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "source"
            snapshot = base / "snapshot"
            (source / "aa").mkdir(parents=True)
            (snapshot / "aa").mkdir(parents=True)
            (source / "aa" / "1111").write_text("source object\n", encoding="utf-8")
            (snapshot / "aa" / "1111").write_text("snapshot object\n", encoding="utf-8")
            before = (tree_snapshot(source), tree_snapshot(snapshot))

            result = self.run_helper(source, snapshot)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(before, (tree_snapshot(source), tree_snapshot(snapshot)))

    def test_shared_regular_file_inode_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "source"
            snapshot = base / "snapshot"
            (source / "aa").mkdir(parents=True)
            (snapshot / "aa").mkdir(parents=True)
            source_object = source / "aa" / "1111"
            source_object.write_text("shared object\n", encoding="utf-8")
            os.link(source_object, snapshot / "aa" / "1111")

            result = self.run_helper(source, snapshot)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("shares a hardlink", result.stderr)

    def test_symlink_targets_are_not_followed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            shared_target = base / "target"
            shared_target.write_text("external target\n", encoding="utf-8")
            source = base / "source"
            snapshot = base / "snapshot"
            (source / "info").mkdir(parents=True)
            (snapshot / "info").mkdir(parents=True)
            os.symlink(shared_target, source / "info" / "link")
            os.symlink(shared_target, snapshot / "info" / "link")

            result = self.run_helper(source, snapshot)

            self.assertEqual(result.returncode, 0, result.stderr)

    def test_hardlinked_symlink_inode_fails_when_platform_supports_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            target = base / "target"
            target.write_text("external target\n", encoding="utf-8")
            source = base / "source"
            snapshot = base / "snapshot"
            (source / "info").mkdir(parents=True)
            (snapshot / "info").mkdir(parents=True)
            source_link = source / "info" / "link"
            os.symlink(target, source_link)
            try:
                os.link(source_link, snapshot / "info" / "link", follow_symlinks=False)
            except (NotImplementedError, OSError):
                self.skipTest("platform does not support hardlinking a symlink itself")

            result = self.run_helper(source, snapshot)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("shares a hardlink", result.stderr)

    def test_rejects_missing_or_symlink_object_roots_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            source = base / "source"
            snapshot = base / "snapshot"
            source.mkdir()
            snapshot.mkdir()
            before = (tree_snapshot(source), tree_snapshot(snapshot))

            missing = self.run_helper(source / "missing", snapshot)
            self.assertNotEqual(missing.returncode, 0)

            link = base / "source-link"
            os.symlink(source, link)
            linked = self.run_helper(link, snapshot)
            self.assertNotEqual(linked.returncode, 0)
            self.assertEqual(before, (tree_snapshot(source), tree_snapshot(snapshot)))


if __name__ == "__main__":
    unittest.main()
