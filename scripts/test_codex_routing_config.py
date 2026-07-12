#!/usr/bin/env python3
"""Focused tests for Teamwork's Codex routing config migration."""

from __future__ import annotations

import os
import pathlib
import stat
import tempfile
import unittest

from codex_routing_config import RoutingConfigError
from codex_routing_config import apply_config
from codex_routing_config import inspect_config


class CodexRoutingConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temporary.name)
        self.config = self.root / ".codex" / "config.toml"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write(self, text: str) -> None:
        self.config.parent.mkdir(parents=True, exist_ok=True)
        self.config.write_text(text, encoding="utf-8")

    def read(self) -> str:
        return self.config.read_text(encoding="utf-8")

    def test_missing_config_is_created_with_private_permissions(self) -> None:
        report = apply_config(self.config)
        self.assertEqual(report.status, "updated")
        self.assertTrue(report.restart_required)
        self.assertTrue(inspect_config(self.config).ready)
        self.assertIn('[features.multi_agent_v2]\n', self.read())
        self.assertIn('tool_namespace = "teamwork"\n', self.read())
        self.assertIn('max_concurrent_threads_per_session = 9\n', self.read())
        mode = stat.S_IMODE(self.config.stat().st_mode)
        self.assertEqual(mode, 0o600)

    def test_scalar_v2_and_legacy_limit_are_migrated_without_losing_other_keys(self) -> None:
        self.write(
            '# keep top comment\n'
            '[agents]\n'
            'max_threads = 4 # child capacity\n'
            'max_depth = 2\n\n'
            '[features]\n'
            'js_repl = false\n'
            'multi_agent_v2 = false\n'
        )
        apply_config(self.config)
        text = self.read()
        self.assertIn('# keep top comment', text)
        self.assertIn('max_depth = 2', text)
        self.assertNotIn('max_threads', text)
        self.assertNotIn('multi_agent_v2 = false', text)
        self.assertIn('max_concurrent_threads_per_session = 9', text)
        self.assertTrue(inspect_config(self.config).ready)

    def test_existing_v2_table_is_updated_and_preserves_extensions(self) -> None:
        self.write(
            '[features.multi_agent_v2]\n'
            'enabled = false # Teamwork owns this value\n'
            'hide_spawn_agent_metadata = true\n'
            'tool_namespace = "collaboration"\n'
            'max_concurrent_threads_per_session = 12\n'
            'usage_hint_text = "keep me"\n'
        )
        apply_config(self.config)
        text = self.read()
        self.assertIn('enabled = true # Teamwork owns this value', text)
        self.assertIn('hide_spawn_agent_metadata = false', text)
        self.assertIn('tool_namespace = "teamwork"', text)
        self.assertIn('max_concurrent_threads_per_session = 9', text)
        self.assertIn('usage_hint_text = "keep me"', text)

    def test_teamwork_limit_replaces_legacy_and_stale_v2_limits(self) -> None:
        self.write(
            '[agents]\n'
            'max_threads = 9\n\n'
            '[features.multi_agent_v2]\n'
            'enabled = true\n'
            'hide_spawn_agent_metadata = false\n'
            'tool_namespace = "teamwork"\n'
            'max_concurrent_threads_per_session = 3\n'
        )
        apply_config(self.config)
        text = self.read()
        self.assertNotIn('max_threads', text)
        self.assertIn('max_concurrent_threads_per_session = 9', text)

    def test_apply_is_byte_idempotent(self) -> None:
        self.write('[features]\njs_repl = false\n')
        first = apply_config(self.config)
        after_first = self.config.read_bytes()
        second = apply_config(self.config)
        self.assertEqual(first.status, "updated")
        self.assertEqual(second.status, "current")
        self.assertFalse(second.restart_required)
        self.assertEqual(self.config.read_bytes(), after_first)

    def test_invalid_toml_is_rejected_without_mutation(self) -> None:
        original = '[features\ninvalid = true\n'
        self.write(original)
        with self.assertRaises(RoutingConfigError):
            apply_config(self.config)
        self.assertEqual(self.read(), original)

    def test_inline_v2_table_is_rejected_without_mutation(self) -> None:
        original = (
            '[features]\n'
            'multi_agent_v2 = { enabled = false, tool_namespace = "other" }\n'
        )
        self.write(original)
        with self.assertRaises(RoutingConfigError):
            apply_config(self.config)
        self.assertEqual(self.read(), original)

    def test_dotted_legacy_agent_limit_is_rejected_without_mutation(self) -> None:
        original = 'agents.max_threads = 4\n'
        self.write(original)
        with self.assertRaises(RoutingConfigError):
            apply_config(self.config)
        self.assertEqual(self.read(), original)

    def test_symlinked_config_keeps_the_symlink(self) -> None:
        target = self.root / "dotfiles" / "codex.toml"
        target.parent.mkdir(parents=True)
        target.write_text('[features]\njs_repl = false\n', encoding="utf-8")
        self.config.parent.mkdir(parents=True)
        os.symlink(target, self.config)
        apply_config(self.config)
        self.assertTrue(self.config.is_symlink())
        self.assertTrue(inspect_config(self.config).ready)
        self.assertIn('tool_namespace = "teamwork"', target.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
