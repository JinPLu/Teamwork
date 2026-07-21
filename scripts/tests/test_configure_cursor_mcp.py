#!/usr/bin/env python3
"""Tests for Teamwork Cursor MCP merge helper."""

from __future__ import annotations

import json
import os
import pathlib
import stat
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
HELPER = REPO_ROOT / "scripts/install/configure_cursor_mcp.py"
CANONICAL = REPO_ROOT / "templates/cursor-mcp/servers.json"


class ConfigureCursorMcpTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.home = pathlib.Path(self.tempdir.name) / "home"
        self.home.mkdir()
        self.cursor_dir = self.home / ".cursor"
        self.cursor_dir.mkdir()
        self.mcp_path = self.cursor_dir / "mcp.json"
        self.sidecar_path = self.cursor_dir / ".teamwork-mcp.json"

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def run_helper(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(HELPER), *args, "--home", str(self.home)],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def load_mcp(self) -> dict[str, object]:
        return json.loads(self.mcp_path.read_text(encoding="utf-8"))

    def test_apply_is_idempotent(self) -> None:
        first = self.run_helper("--apply")
        self.assertEqual(first.returncode, 0, first.stderr)
        before = self.mcp_path.read_bytes()
        sidecar_before = self.sidecar_path.read_bytes()

        second = self.run_helper("--apply")
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(self.mcp_path.read_bytes(), before)
        self.assertEqual(self.sidecar_path.read_bytes(), sidecar_before)

    def test_apply_preserves_unrelated_servers(self) -> None:
        self.mcp_path.write_text(
            json.dumps({"mcpServers": {"custom-server": {"command": "keep-me"}}}) + "\n",
            encoding="utf-8",
        )
        result = self.run_helper("--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        servers = self.load_mcp()["mcpServers"]
        self.assertIn("custom-server", servers)
        self.assertIn("codegraph", servers)
        self.assertIn("gpu-broker", servers)

    def test_malformed_existing_config_is_refused(self) -> None:
        self.mcp_path.write_text("{not-json", encoding="utf-8")
        result = self.run_helper("--apply")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("malformed JSON", result.stderr)

    def test_remove_deletes_teamwork_servers_and_sidecar(self) -> None:
        apply = self.run_helper("--apply")
        self.assertEqual(apply.returncode, 0, apply.stderr)
        self.mcp_path.write_text(
            json.dumps(
                {
                    "mcpServers": {
                        "custom-server": {"command": "keep-me"},
                        **json.loads(CANONICAL.read_text(encoding="utf-8")),
                    }
                }
            )
            + "\n",
            encoding="utf-8",
        )
        remove = self.run_helper("--remove")
        self.assertEqual(remove.returncode, 0, remove.stderr)
        servers = self.load_mcp()["mcpServers"]
        self.assertIn("custom-server", servers)
        self.assertNotIn("codegraph", servers)
        self.assertNotIn("gpu-broker", servers)
        self.assertFalse(self.sidecar_path.exists())

    def test_refuses_symlink_mcp_json(self) -> None:
        target = self.cursor_dir / "real-mcp.json"
        target.write_text('{"mcpServers": {}}\n', encoding="utf-8")
        if self.mcp_path.exists():
            self.mcp_path.unlink()
        os.symlink(target, self.mcp_path)
        result = self.run_helper("--apply")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("refusing to replace symlink", result.stderr)

    def test_force_refreshes_teamwork_owned_entry(self) -> None:
        apply = self.run_helper("--apply")
        self.assertEqual(apply.returncode, 0, apply.stderr)
        payload = self.load_mcp()
        payload["mcpServers"]["codegraph"] = {"command": "stale"}
        self.mcp_path.write_text(json.dumps(payload) + "\n", encoding="utf-8")

        refresh = self.run_helper("--apply", "--force")
        self.assertEqual(refresh.returncode, 0, refresh.stderr)
        servers = self.load_mcp()["mcpServers"]
        self.assertEqual(servers["codegraph"]["command"], "codegraph")

    def test_project_config_does_not_write_global_sidecar(self) -> None:
        project = self.home / "project"
        project.mkdir()
        project_mcp = project / ".cursor" / "mcp.json"
        project_mcp.parent.mkdir(parents=True)
        result = subprocess.run(
            [
                sys.executable,
                str(HELPER),
                "--apply",
                "--config",
                str(project_mcp),
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(project_mcp.exists())
        self.assertFalse(self.sidecar_path.exists())


if __name__ == "__main__":
    raise SystemExit(unittest.main())
