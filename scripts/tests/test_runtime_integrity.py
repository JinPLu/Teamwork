from __future__ import annotations

import json
import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CURRENT_VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()


def load_bundle_builder():
    spec = importlib.util.spec_from_file_location(
        "teamwork_bundle_builder",
        ROOT / "scripts/build-codex-plugin.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load plugin builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RuntimeLayoutTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.package_root = Path(self.temporary.name) / "teamwork-skill"
        topology = json.loads((ROOT / "config/teamwork-topology.json").read_text(encoding="utf-8"))
        files = {
            "VERSION",
            "install.sh",
            "policy/teamwork-global.md",
            "config/teamwork-topology.json",
            ".codex-plugin/plugin.json",
            ".claude-plugin/plugin.json",
            "scripts/check-update.sh",
            "scripts/init-project-files.py",
            "scripts/teamwork_index_v4.py",
            "scripts/migrate-teamwork-documents.py",
            "scripts/validate_teamwork_index.py",
            "scripts/plugin-activation.py",
            "scripts/plugin-runtime-root.py",
            "hooks/notify.py",
        }
        files.update(row["path"] for row in topology["public_skills"])
        for row in topology["agents"]:
            files.update(row["templates"].values())
        for relative in files:
            destination = self.package_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, destination)
        (self.package_root / ".teamwork-plugin-runtime").write_text(
            "TEAMWORK_CODEX_PLUGIN_RUNTIME=1\n", encoding="utf-8"
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_runtime_root(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(self.package_root / "scripts/plugin-runtime-root.py")],
            cwd=self.package_root,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_runtime_root_accepts_normal_layout_without_integrity_file(self) -> None:
        self.assertFalse((self.package_root / ".teamwork-runtime-integrity.json").exists())
        result = self.run_runtime_root()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(Path(result.stdout.strip()).resolve(), self.package_root.resolve())

    def test_runtime_root_accepts_content_changes_without_content_identity_check(self) -> None:
        policy = self.package_root / "policy/teamwork-global.md"
        policy.write_text(policy.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        result = self.run_runtime_root()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_runtime_root_rejects_missing_required_regular_file(self) -> None:
        (self.package_root / "scripts/teamwork_index_v4.py").unlink()
        result = self.run_runtime_root()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing", result.stderr)

    def test_runtime_root_rejects_manifest_identity_mismatch(self) -> None:
        manifest = self.package_root / ".codex-plugin/plugin.json"
        value = json.loads(manifest.read_text(encoding="utf-8"))
        value["name"] = "not-teamwork"
        manifest.write_text(json.dumps(value), encoding="utf-8")
        result = self.run_runtime_root()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("manifest name/version mismatch", result.stderr)

    def test_generated_bundle_comparison_ignores_python_cache_output(self) -> None:
        builder = load_bundle_builder()
        with tempfile.TemporaryDirectory() as current_raw, tempfile.TemporaryDirectory() as staged_raw:
            current = Path(current_raw)
            staged = Path(staged_raw)
            for root in (current, staged):
                (root / "scripts").mkdir()
                (root / "scripts/tool.py").write_text("print('ok')\n", encoding="utf-8")
            cache = current / "scripts/__pycache__"
            cache.mkdir()
            (cache / "tool.cpython-313.pyc").write_bytes(b"runtime cache")
            (current / "empty-local-directory").mkdir()
            self.assertTrue(builder.bundle_matches(current, staged))


if __name__ == "__main__":
    unittest.main()
