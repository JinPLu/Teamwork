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
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BUILD_SCRIPT = ROOT / "scripts/build-codex-plugin.py"
CURRENT_VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()


def load_builder() -> Any:
    spec = importlib.util.spec_from_file_location("build_codex_plugin", BUILD_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load builder from {BUILD_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RuntimeIntegrityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix=".runtime-integrity-", dir=ROOT)
        self.tmp = Path(self.temporary.name)
        builder = load_builder()
        self.stage = builder.build_stage(ROOT, self.tmp)
        self.package_root = self.tmp / f"cache/teamwork/teamwork-skill/{CURRENT_VERSION}"
        self.package_root.parent.mkdir(parents=True)
        shutil.copytree(self.stage, self.package_root, symlinks=True)
        shutil.rmtree(self.stage.parent)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @property
    def runtime_root_cli(self) -> Path:
        return self.package_root / "scripts/plugin-runtime-root.py"

    def run_runtime_root(self, package_root: Path | None = None) -> subprocess.CompletedProcess[str]:
        root = package_root or self.package_root
        return subprocess.run(
            [sys.executable, str(root / "scripts/plugin-runtime-root.py")],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )

    def copy_package(self, name: str) -> Path:
        destination = self.tmp / name / f"teamwork/teamwork-skill/{CURRENT_VERSION}"
        destination.parent.mkdir(parents=True)
        shutil.copytree(self.package_root, destination, symlinks=True)
        return destination

    def assert_runtime_rejected(self, package_root: Path, expected: str) -> None:
        result = self.run_runtime_root(package_root)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn(expected, result.stderr)

    def integrity_files(self) -> set[str]:
        manifest = json.loads((self.package_root / ".teamwork-runtime-integrity.json").read_text(encoding="utf-8"))
        files = manifest.get("files")
        self.assertIsInstance(files, dict)
        return set(files)

    def actual_package_files(self) -> set[str]:
        actual: set[str] = set()
        for path in self.package_root.rglob("*"):
            rel = path.relative_to(self.package_root).as_posix()
            if rel == ".teamwork-runtime-integrity.json":
                continue
            info = path.lstat()
            if stat.S_ISDIR(info.st_mode):
                continue
            self.assertTrue(stat.S_ISREG(info.st_mode), rel)
            actual.add(rel)
        return actual

    def test_runtime_integrity_manifest_covers_exact_packaged_file_inventory(self) -> None:
        files = self.integrity_files()
        self.assertEqual(self.actual_package_files(), files)
        self.assertIn("skills/teamwork-collaborate/SKILL.md", files)
        self.assertIn("templates/codex-agents/teamwork-writer.toml", files)
        self.assertIn("templates/cursor-agents/writer.md", files)
        self.assertIn("templates/claude-agents/writer.md", files)
        self.assertIn("install.sh", files)
        self.assertIn("scripts/check-update.sh", files)
        self.assertIn("scripts/configure-codex-routing.py", files)
        self.assertIn("scripts/plugin-activation.py", files)
        self.assertIn("scripts/discussion-transaction.py", files)
        self.assertIn("hooks/notify.py", files)
        self.assertNotIn(".teamwork-runtime-integrity.json", files)
        self.assertFalse(any(path.startswith("docs/teamwork/") for path in files))

        result = self.run_runtime_root()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(Path(result.stdout.strip()).resolve(), self.package_root.resolve())

    def test_runtime_root_rejects_modified_behavior_bearing_files(self) -> None:
        cases = {
            "skill": "skills/teamwork-collaborate/SKILL.md",
            "writer-template": "templates/codex-agents/teamwork-writer.toml",
            "installer": "install.sh",
            "runtime-helper": "scripts/teamwork-case-migration.py",
        }
        for label, rel in cases.items():
            with self.subTest(label=label):
                package = self.copy_package(f"tampered-{label}")
                path = package / rel
                path.write_text(path.read_text(encoding="utf-8") + "\n# tamper\n", encoding="utf-8")
                self.assert_runtime_rejected(package, f"runtime hash mismatch for {rel}")

    def test_runtime_root_rejects_extra_missing_and_mixed_package_files(self) -> None:
        extra = self.copy_package("extra-behavior")
        (extra / "scripts/unlisted-behavior.py").write_text("# unexpected behavior\n", encoding="utf-8")
        os.chmod(extra / "scripts/unlisted-behavior.py", 0o755)
        self.assert_runtime_rejected(extra, "integrity file inventory mismatch")

        missing = self.copy_package("missing-skill")
        (missing / "skills/teamwork-review/SKILL.md").unlink()
        self.assert_runtime_rejected(missing, "integrity file inventory mismatch")

        mixed = self.copy_package("mixed-root")
        shutil.copytree(ROOT / ".claude-plugin", mixed / ".claude-plugin", symlinks=True)
        self.assert_runtime_rejected(mixed, "integrity file inventory mismatch")


if __name__ == "__main__":
    unittest.main()
