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
from codex_routing_config import preview_config


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
        self.assertIn('[features]\n', self.read())
        self.assertIn('multi_agent = true\n', self.read())
        self.assertNotIn('multi_agent_v2', self.read())
        mode = stat.S_IMODE(self.config.stat().st_mode)
        self.assertEqual(mode, 0o600)

    def test_scalar_v2_is_migrated_without_losing_other_keys(self) -> None:
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
        self.assertIn('max_threads = 4 # child capacity', text)
        self.assertIn('max_depth = 2', text)
        self.assertNotIn('multi_agent_v2 = false', text)
        self.assertIn('multi_agent = true', text)
        self.assertTrue(inspect_config(self.config).ready)

    def test_existing_v2_table_is_removed_and_stable_feature_is_set(self) -> None:
        self.write(
            '[features]\n'
            'js_repl = false\n'
            'multi_agent = false\n\n'
            '[features.multi_agent_v2]\n'
            'enabled = false\n'
            'hide_spawn_agent_metadata = true\n'
            'tool_namespace = "collaboration"\n'
            'max_concurrent_threads_per_session = 12\n'
            'usage_hint_text = "keep me"\n'
        )
        apply_config(self.config)
        text = self.read()
        self.assertIn('js_repl = false', text)
        self.assertIn('multi_agent = true', text)
        self.assertNotIn('multi_agent_v2', text)
        self.assertNotIn('usage_hint_text', text)

    def test_stable_feature_preserves_agent_limits_and_removes_stale_v2_limits(self) -> None:
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
        self.assertIn('max_threads = 9', text)
        self.assertIn('multi_agent = true', text)
        self.assertNotIn('max_concurrent_threads_per_session', text)

    def test_apply_is_byte_idempotent(self) -> None:
        self.write('[features]\njs_repl = false\n')
        first = apply_config(self.config)
        after_first = self.config.read_bytes()
        second = apply_config(self.config)
        self.assertEqual(first.status, "updated")
        self.assertEqual(second.status, "current")
        self.assertFalse(second.restart_required)
        self.assertEqual(self.config.read_bytes(), after_first)

    def test_preview_validates_the_exact_migration_without_writing(self) -> None:
        original = '[features]\njs_repl = false\n'
        self.write(original)
        report = preview_config(self.config)
        self.assertEqual(report.status, "would-update")
        self.assertTrue(report.ready)
        self.assertTrue(report.restart_required)
        self.assertEqual(self.read(), original)

    def test_invalid_toml_is_rejected_without_mutation(self) -> None:
        original = '[features\ninvalid = true\n'
        self.write(original)
        with self.assertRaises(RoutingConfigError):
            apply_config(self.config)
        self.assertEqual(self.read(), original)

    def test_inline_v2_table_is_removed(self) -> None:
        original = (
            '[features]\n'
            'multi_agent_v2 = { enabled = false, tool_namespace = "other" }\n'
        )
        self.write(original)
        apply_config(self.config)
        self.assertIn('multi_agent = true', self.read())
        self.assertNotIn('multi_agent_v2', self.read())

    def test_invalid_stable_feature_is_rejected_without_mutation(self) -> None:
        original = '[features]\nmulti_agent = "yes"\n'
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
        self.assertIn('multi_agent = true', target.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
