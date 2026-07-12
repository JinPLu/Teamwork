#!/usr/bin/env python3
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "notify.py"
SPEC = importlib.util.spec_from_file_location("teamwork_notify", HOOK)
notify = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(notify)
CONFIGURE_PATH = ROOT / "scripts" / "configure-notifications.py"
CONFIGURE_SPEC = importlib.util.spec_from_file_location("teamwork_configure_notifications", CONFIGURE_PATH)
configure = importlib.util.module_from_spec(CONFIGURE_SPEC)
assert CONFIGURE_SPEC.loader
CONFIGURE_SPEC.loader.exec_module(configure)


class NotifyHookTests(unittest.TestCase):
    def run_hook(self, raw: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["TEAMWORK_NOTIFY_DRY_RUN"] = "1"
        return subprocess.run(
            [sys.executable, str(HOOK)],
            input=raw,
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

    def test_event_mapping(self) -> None:
        self.assertEqual(notify.classify(notify.metadata({"hook_event_name": "Stop"})), "ready")
        self.assertEqual(notify.classify(notify.metadata({"type": "agent-turn-complete"})), "ready")
        self.assertEqual(notify.classify(notify.metadata({"hook_event_name": "PermissionRequest"})), "attention")
        self.assertEqual(
            notify.classify(notify.metadata({"hook_event_name": "Notification", "notification_type": "permission_prompt"})),
            "attention",
        )
        self.assertEqual(
            notify.classify(notify.metadata({"hook_event_name": "Notification", "notification_type": "idle_prompt"})),
            "attention",
        )
        self.assertEqual(notify.classify(notify.metadata({"type": "needs-input"})), "attention")

    def test_subagent_and_unrelated_events_are_silent(self) -> None:
        self.assertIsNone(notify.classify(notify.metadata({"hook_event_name": "SubagentStop"})))
        self.assertIsNone(notify.classify(notify.metadata({"hook_event_name": "PreToolUse"})))

    def test_message_content_is_not_copied_to_metadata(self) -> None:
        meta = notify.metadata(
            {"type": "agent-turn-complete", "last-assistant-message": "secret", "transcript_path": "/secret"}
        )
        self.assertEqual(meta, {"type": "agent-turn-complete"})

    def test_malformed_input_fails_open_with_neutral_output(self) -> None:
        result = self.run_hook("not json")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), {})
        self.assertEqual(result.stderr, "")

    def test_missing_player_and_headless_runtime_fail_open(self) -> None:
        with mock.patch.object(notify.platform, "system", return_value="Linux"), mock.patch.object(
            notify.shutil, "which", return_value=None
        ), mock.patch.dict(os.environ, {"DISPLAY": ":0"}, clear=True):
            self.assertIsNone(notify.playback_command("ready"))
        with mock.patch.dict(os.environ, {"TEAMWORK_NOTIFY_HEADLESS": "1"}, clear=True), mock.patch.object(
            notify.subprocess, "Popen"
        ) as popen:
            notify.play("attention")
            popen.assert_not_called()

    def test_ready_and_attention_use_distinct_configurable_sounds(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ready = Path(directory) / "ready.wav"
            attention = Path(directory) / "attention.wav"
            ready.touch()
            attention.touch()
            env = {"TEAMWORK_READY_SOUND": str(ready), "TEAMWORK_ATTENTION_SOUND": str(attention)}
            with mock.patch.object(notify.platform, "system", return_value="Darwin"), mock.patch.object(
                notify.shutil, "which", return_value="/usr/bin/afplay"
            ), mock.patch.dict(os.environ, env, clear=True):
                self.assertEqual(notify.playback_command("ready"), ["/usr/bin/afplay", str(ready)])
                self.assertEqual(notify.playback_command("attention"), ["/usr/bin/afplay", str(attention)])

    def test_dry_run_is_nonblocking_and_neutral(self) -> None:
        result = self.run_hook(json.dumps({"hook_event_name": "Stop", "session_id": "dry-run"}))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '{}\n')

    def test_duplicate_event_is_deduplicated(self) -> None:
        meta = {"type": "agent-turn-complete", "thread-id": "dedupe-test", "turn-id": "one"}
        equivalent = {"hook_event_name": "Stop", "thread-id": "dedupe-test", "turn-id": "one"}
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(notify.tempfile, "gettempdir", return_value=directory):
            self.assertTrue(notify.claim_once("ready", meta))
            self.assertFalse(notify.claim_once("ready", equivalent))
            self.assertTrue(notify.claim_once("attention", meta))

    def test_config_install_is_idempotent_and_preserves_unrelated_hooks(self) -> None:
        data = {
            "theme": "dark",
            "hooks": {
                "Stop": [{"hooks": [{"type": "command", "command": "python3 other.py"}]}]
            },
        }
        command = "python3 /tmp/teamwork/notify.py"
        configure.install_handlers(data, command)
        configure.install_handlers(data, command)
        self.assertEqual(configure.status(data, command), "installed")
        self.assertEqual(data["theme"], "dark")
        stop_commands = [
            handler["command"]
            for group in data["hooks"]["Stop"]
            for handler in group["hooks"]
        ]
        self.assertEqual(stop_commands, ["python3 other.py", command])

    def test_config_remove_only_removes_teamwork_handlers(self) -> None:
        command = "python3 /tmp/teamwork/notify.py"
        unrelated_notify = "python3 /tmp/other/hooks/notify.py"
        data = {"hooks": {"Stop": [{"hooks": [
            {"type": "command", "command": "python3 other.py"},
            {"type": "command", "command": unrelated_notify},
            {"type": "command", "command": command},
        ]}]}}
        self.assertEqual(configure.strip_teamwork_handlers(data), 1)
        self.assertEqual(configure.status(data, command), "disabled")
        commands = [handler["command"] for handler in data["hooks"]["Stop"][0]["hooks"]]
        self.assertEqual(commands, ["python3 other.py", unrelated_notify])

    def test_config_updates_preserve_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "managed.json"
            config = root / "settings.json"
            target.write_text('{"theme":"dark"}\n', encoding="utf-8")
            config.symlink_to(target.name)
            command = "python3 /tmp/teamwork/notify.py"

            data = configure.load_config(config)
            configure.install_handlers(data, command)
            configure.write_atomic(config, data)
            self.assertTrue(config.is_symlink())
            self.assertEqual(configure.status(configure.load_config(config), command), "installed")

            data = configure.load_config(config)
            configure.strip_teamwork_handlers(data)
            configure.write_atomic(config, data)
            self.assertTrue(config.is_symlink())
            self.assertEqual(configure.status(configure.load_config(config), command), "disabled")
            self.assertEqual(configure.load_config(config)["theme"], "dark")


if __name__ == "__main__":
    unittest.main()
