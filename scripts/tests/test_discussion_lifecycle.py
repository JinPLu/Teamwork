from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

from teamwork_tooling.discussion_lifecycle import (
    DiscussionLifecycleError,
    FreshSessionRecoveryError,
    WorkspaceManifest,
    _entry_from_dirent,
    assert_fresh_session_recovery,
    capture_workspace_manifest,
    manifest_changes,
    validate_discussion_write_footprint,
)


ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "scripts/discussion-write-evidence.py"


class DiscussionLifecycleFootprintTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "project"
        self.root.mkdir()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write(self, relative: str, content: str) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def write_runtime_anchors(self) -> None:
        self.write("docs/teamwork/index.json", '{"active": {"discussion": null}}\n')
        self.write("docs/teamwork/current.md", "# Current\n")
        self.write("docs/teamwork/README.md", "# Runtime Memory\n")

    def test_activation_permits_the_three_anchors_and_one_dated_artifact(self) -> None:
        before = capture_workspace_manifest(self.root)
        self.write_runtime_anchors()
        self.write(
            "docs/teamwork/discussion/2026-07-15-community-output.md",
            "# Discussion\n",
        )
        after = capture_workspace_manifest(self.root)

        report = validate_discussion_write_footprint(
            before,
            after,
            require_memory_anchor_updates=True,
        )

        self.assertEqual(
            report.discussion_path,
            "docs/teamwork/discussion/2026-07-15-community-output.md",
        )
        self.assertEqual(
            report.changed_memory_anchors,
            (
                "docs/teamwork/index.json",
                "docs/teamwork/current.md",
                "docs/teamwork/README.md",
            ),
        )
        self.assertEqual(
            set(report.changed_paths),
            {
                "docs",
                "docs/teamwork",
                "docs/teamwork/discussion",
                "docs/teamwork/index.json",
                "docs/teamwork/current.md",
                "docs/teamwork/README.md",
                "docs/teamwork/discussion/2026-07-15-community-output.md",
            },
        )

    def test_checkpoint_can_update_the_same_artifact_without_rewriting_anchors(self) -> None:
        self.write_runtime_anchors()
        artifact = "docs/teamwork/discussion/2026-07-15-community-output.md"
        self.write(artifact, "# Discussion\n\nOpen: source choice\n")
        before = capture_workspace_manifest(self.root)
        self.write(artifact, "# Discussion\n\nSettled: plain terminology\n")
        after = capture_workspace_manifest(self.root)

        report = validate_discussion_write_footprint(before, after)

        self.assertEqual(report.changed_paths, (artifact,))
        self.assertEqual(report.changed_memory_anchors, ())

    def test_checkpoint_allows_an_atomic_artifact_write_with_new_identity(self) -> None:
        self.write_runtime_anchors()
        artifact = "docs/teamwork/discussion/2026-07-15-community-output.md"
        artifact_path = self.write(artifact, "# Discussion\n")
        before = capture_workspace_manifest(self.root)
        replacement = artifact_path.with_name("atomic-replacement.tmp")
        replacement.write_text("# Discussion\n\nUpdated atomically\n", encoding="utf-8")
        replacement.chmod(artifact_path.stat().st_mode)
        os.replace(replacement, artifact_path)
        after = capture_workspace_manifest(self.root)

        report = validate_discussion_write_footprint(before, after)

        self.assertEqual(report.changed_paths, (artifact,))
        self.assertNotEqual(
            before.entries[artifact].inode,
            after.entries[artifact].inode,
        )

    def test_rejects_a_write_outside_the_explicit_allowlist(self) -> None:
        self.write_runtime_anchors()
        artifact = "docs/teamwork/discussion/2026-07-15-community-output.md"
        self.write(artifact, "# Discussion\n")
        before = capture_workspace_manifest(self.root)
        self.write(artifact, "# Discussion\n\nSettled: public wording\n")
        self.write("notes.txt", "unrelated\n")
        after = capture_workspace_manifest(self.root)

        with self.assertRaisesRegex(
            DiscussionLifecycleError, "write outside the discussion lifecycle allowlist: notes.txt"
        ):
            validate_discussion_write_footprint(before, after)

    def test_rejects_same_content_atomic_replacement_outside_allowlist(self) -> None:
        self.write_runtime_anchors()
        artifact = "docs/teamwork/discussion/2026-07-15-community-output.md"
        self.write(artifact, "# Discussion\n")
        notes = self.write("notes.txt", "unchanged bytes\n")
        before = capture_workspace_manifest(self.root)
        replacement = notes.with_name("notes-replacement.tmp")
        replacement.write_bytes(notes.read_bytes())
        replacement.chmod(notes.stat().st_mode)
        os.replace(replacement, notes)
        self.write(artifact, "# Discussion\n\nUpdated\n")
        after = capture_workspace_manifest(self.root)

        self.assertNotEqual(
            before.entries["notes.txt"].inode,
            after.entries["notes.txt"].inode,
        )
        with self.assertRaisesRegex(
            DiscussionLifecycleError,
            "write outside the discussion lifecycle allowlist: notes.txt",
        ):
            validate_discussion_write_footprint(before, after)

    def test_rejects_same_metadata_replacement_of_existing_directory(self) -> None:
        self.write_runtime_anchors()
        artifact = "docs/teamwork/discussion/2026-07-15-community-output.md"
        self.write(artifact, "# Discussion\n")
        existing = self.root / "cache"
        existing.mkdir()
        before = capture_workspace_manifest(self.root)
        replacement = self.root / "cache-replacement"
        replacement.mkdir(mode=existing.stat().st_mode)
        os.replace(replacement, existing)
        self.write(artifact, "# Discussion\n\nUpdated\n")
        after = capture_workspace_manifest(self.root)

        self.assertNotEqual(
            before.entries["cache"].inode,
            after.entries["cache"].inode,
        )
        with self.assertRaisesRegex(
            DiscussionLifecycleError,
            "write outside the discussion lifecycle allowlist: cache",
        ):
            validate_discussion_write_footprint(before, after)

    def test_rejects_a_nondated_or_malformed_discussion_filename(self) -> None:
        before = capture_workspace_manifest(self.root)
        self.write_runtime_anchors()
        self.write("docs/teamwork/discussion/current.md", "# Discussion\n")
        after = capture_workspace_manifest(self.root)

        with self.assertRaisesRegex(
            DiscussionLifecycleError,
            "discussion artifact must be dated kebab-case Markdown",
        ):
            validate_discussion_write_footprint(
                before,
                after,
                require_memory_anchor_updates=True,
            )

    def test_rejects_two_discussion_artifacts_in_one_lifecycle_step(self) -> None:
        self.write_runtime_anchors()
        first = "docs/teamwork/discussion/2026-07-15-first-route.md"
        second = "docs/teamwork/discussion/2026-07-15-second-route.md"
        self.write(first, "# First\n")
        self.write(second, "# Second\n")
        before = capture_workspace_manifest(self.root)
        self.write(first, "# First\n\nUpdated\n")
        self.write(second, "# Second\n\nUpdated\n")
        after = capture_workspace_manifest(self.root)

        with self.assertRaisesRegex(
            DiscussionLifecycleError, "at most one dated discussion artifact may change"
        ):
            validate_discussion_write_footprint(before, after)

    def test_replacement_requires_one_modified_artifact_one_created_artifact_and_anchors(self) -> None:
        self.write_runtime_anchors()
        existing = "docs/teamwork/discussion/2026-07-15-first-route.md"
        replacement = "docs/teamwork/discussion/2026-07-15-second-route.md"
        self.write(existing, "# First\n")
        before = capture_workspace_manifest(self.root)
        self.write(existing, "# First\n\nSuperseded\n")
        self.write(replacement, "# Second\n")
        self.write("docs/teamwork/index.json", '{"active": {"discussion": "second-route"}}\n')
        self.write("docs/teamwork/current.md", "# Current\n\nSecond route\n")
        self.write("docs/teamwork/README.md", "# Runtime Memory\n\nSecond route\n")
        after = capture_workspace_manifest(self.root)

        report = validate_discussion_write_footprint(
            before,
            after,
            allow_discussion_replacement=True,
        )

        self.assertEqual(report.discussion_path, replacement)
        self.assertEqual(
            [change.action for change in report.changes if "discussion/" in change.path],
            ["modified", "created"],
        )

    def test_replacement_rejects_two_created_or_two_modified_artifacts(self) -> None:
        self.write_runtime_anchors()
        before = capture_workspace_manifest(self.root)
        for name in ("first", "second"):
            self.write(f"docs/teamwork/discussion/2026-07-15-{name}.md", f"# {name}\n")
        for anchor in (
            "docs/teamwork/index.json",
            "docs/teamwork/current.md",
            "docs/teamwork/README.md",
        ):
            self.write(anchor, self.root.joinpath(anchor).read_text() + "updated\n")
        after = capture_workspace_manifest(self.root)
        with self.assertRaisesRegex(
            DiscussionLifecycleError,
            "replacement must modify one existing.*create one new",
        ):
            validate_discussion_write_footprint(
                before, after, allow_discussion_replacement=True
            )

        first = "docs/teamwork/discussion/2026-07-15-first.md"
        second = "docs/teamwork/discussion/2026-07-15-second.md"
        before = after
        self.write(first, "# first\n\nupdated\n")
        self.write(second, "# second\n\nupdated\n")
        after = capture_workspace_manifest(self.root)
        with self.assertRaisesRegex(
            DiscussionLifecycleError,
            "replacement must modify one existing.*create one new",
        ):
            validate_discussion_write_footprint(
                before, after, allow_discussion_replacement=True
            )

    def test_replacement_rejects_deletion_and_requires_all_anchor_updates(self) -> None:
        self.write_runtime_anchors()
        existing = "docs/teamwork/discussion/2026-07-15-first.md"
        self.write(existing, "# First\n")
        before = capture_workspace_manifest(self.root)
        (self.root / existing).unlink()
        self.write("docs/teamwork/discussion/2026-07-15-second.md", "# Second\n")
        after = capture_workspace_manifest(self.root)
        with self.assertRaisesRegex(
            DiscussionLifecycleError,
            "discussion artifact must remain a regular file.*did not update every runtime-memory anchor",
        ):
            validate_discussion_write_footprint(
                before, after, allow_discussion_replacement=True
            )

    def test_capture_rejects_any_symlink_in_the_observed_tree(self) -> None:
        outside = self.root.parent / "outside.txt"
        outside.write_text("outside\n", encoding="utf-8")
        os.symlink("../outside.txt", self.root / "escape")

        with self.assertRaisesRegex(
            DiscussionLifecycleError, "symlink is not permitted in observed project"
        ):
            capture_workspace_manifest(self.root)

    def test_cli_snapshot_rejects_an_external_target_symlink_before_treatment(self) -> None:
        outside = self.root.parent / "outside.txt"
        outside.write_text("before\n", encoding="utf-8")
        os.symlink("../outside.txt", self.root / "escape")
        result = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "snapshot",
                "--project",
                str(self.root),
                "--output",
                str(self.root.parent / "symlink-before.json"),
            ],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("symlink is not permitted", result.stderr)
        self.assertFalse((self.root.parent / "symlink-before.json").exists())
        self.assertEqual(outside.read_text(encoding="utf-8"), "before\n")

    def test_capture_rejects_regular_files_with_multiple_hard_links(self) -> None:
        outside = self.root.parent / "outside.txt"
        outside.write_text("outside\n", encoding="utf-8")
        os.link(outside, self.root / "escape.txt")

        with self.assertRaisesRegex(
            DiscussionLifecycleError, "regular file must have exactly one hard link"
        ):
            capture_workspace_manifest(self.root)

    def test_capture_rejects_fifo_special_nodes(self) -> None:
        os.mkfifo(self.root / "escape.fifo")

        with self.assertRaisesRegex(
            DiscussionLifecycleError, "special filesystem node is not permitted"
        ):
            capture_workspace_manifest(self.root)

    def test_entry_capture_rejects_a_cross_device_boundary(self) -> None:
        entry = SimpleNamespace(
            name="mounted",
            path="mounted",
            stat=lambda *, follow_symlinks: SimpleNamespace(st_dev=202),
        )

        with self.assertRaisesRegex(
            DiscussionLifecycleError, "crosses project root device boundary"
        ):
            _entry_from_dirent(
                entry,
                -1,
                display_path="mounted",
                root_device=101,
            )

    def test_cli_snapshot_rejects_a_symlink_project_root(self) -> None:
        claimed_root = self.root.parent / "claimed-project"
        os.symlink(self.root, claimed_root)
        manifest_path = self.root.parent / "root-symlink-before.json"
        result = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "snapshot",
                "--project",
                str(claimed_root),
                "--output",
                str(manifest_path),
            ],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("project root must not be a symlink", result.stderr)
        self.assertFalse(manifest_path.exists())

    def test_rejects_unsafe_managed_modes_and_existing_file_mode_changes(self) -> None:
        self.write_runtime_anchors()
        artifact = "docs/teamwork/discussion/2026-07-15-community-output.md"
        artifact_path = self.write(artifact, "# Discussion\n")
        artifact_path.chmod(0o777)
        before = capture_workspace_manifest(self.root)
        self.write("docs/teamwork/index.json", '{"updated": true}\n')
        after = capture_workspace_manifest(self.root)
        with self.assertRaisesRegex(
            DiscussionLifecycleError, "unsafe permissions on managed discussion artifact"
        ):
            validate_discussion_write_footprint(
                before, after, require_discussion_change=False
            )

        artifact_path.chmod(0o644)
        before = capture_workspace_manifest(self.root)
        self.write(artifact, "# Discussion\n\nUpdated\n")
        artifact_path.chmod(0o600)
        after = capture_workspace_manifest(self.root)
        with self.assertRaisesRegex(
            DiscussionLifecycleError, "modified existing file must preserve mode"
        ):
            validate_discussion_write_footprint(before, after)

    def test_rejects_unsafe_new_markdown_and_directory_modes(self) -> None:
        self.write_runtime_anchors()
        before = capture_workspace_manifest(self.root)
        artifact = self.write(
            "docs/teamwork/discussion/2026-07-15-community-output.md",
            "# Discussion\n",
        )
        artifact.chmod(0o755)
        after = capture_workspace_manifest(self.root)
        with self.assertRaisesRegex(
            DiscussionLifecycleError, "unsafe permissions on managed discussion artifact"
        ):
            validate_discussion_write_footprint(before, after)

        empty_root = Path(self.temporary.name) / "empty-project"
        empty_root.mkdir()
        before = capture_workspace_manifest(empty_root)
        discussion = empty_root / "docs/teamwork/discussion"
        discussion.mkdir(parents=True)
        discussion.chmod(0o777)
        (discussion / "2026-07-15-community-output.md").write_text(
            "# Discussion\n", encoding="utf-8"
        )
        after = capture_workspace_manifest(empty_root)
        with self.assertRaisesRegex(
            DiscussionLifecycleError, "new directory must not be group/world writable"
        ):
            validate_discussion_write_footprint(before, after)

    def test_rejects_unsafe_unchanged_managed_ancestor_directory(self) -> None:
        self.write_runtime_anchors()
        artifact = "docs/teamwork/discussion/2026-07-15-community-output.md"
        self.write(artifact, "# Discussion\n")
        for index, relative in enumerate(
            ("docs", "docs/teamwork", "docs/teamwork/discussion")
        ):
            with self.subTest(relative=relative):
                directory = self.root / relative
                directory.chmod(0o777)
                before = capture_workspace_manifest(self.root)
                self.write(artifact, f"# Discussion\n\nUpdated {index}\n")
                after = capture_workspace_manifest(self.root)
                with self.assertRaisesRegex(
                    DiscussionLifecycleError,
                    "managed ancestor directory must not be group/world writable",
                ):
                    validate_discussion_write_footprint(before, after)
                directory.chmod(0o755)

    def test_rejects_artifact_deletion_or_symlink_substitution(self) -> None:
        self.write_runtime_anchors()
        artifact = "docs/teamwork/discussion/2026-07-15-community-output.md"
        artifact_path = self.write(artifact, "# Discussion\n")
        before = capture_workspace_manifest(self.root)
        artifact_path.unlink()
        os.symlink("/tmp/not-a-discussion", artifact_path)
        with self.assertRaisesRegex(
            DiscussionLifecycleError, "symlink is not permitted in observed project"
        ):
            capture_workspace_manifest(self.root)

    def test_requires_anchor_updates_when_requested(self) -> None:
        self.write_runtime_anchors()
        artifact = "docs/teamwork/discussion/2026-07-15-community-output.md"
        self.write(artifact, "# Discussion\n")
        before = capture_workspace_manifest(self.root)
        self.write(artifact, "# Discussion\n\nSettled: plain language\n")
        after = capture_workspace_manifest(self.root)

        with self.assertRaisesRegex(
            DiscussionLifecycleError,
            "discussion lifecycle did not update every runtime-memory anchor",
        ):
            validate_discussion_write_footprint(
                before,
                after,
                require_memory_anchor_updates=True,
            )

    def test_manifest_rejects_git_metadata_writes_outside_the_allowlist(self) -> None:
        self.write_runtime_anchors()
        artifact = "docs/teamwork/discussion/2026-07-15-community-output.md"
        self.write(artifact, "# Discussion\n")
        git_config = self.write(".git/config", "before\n")
        before = capture_workspace_manifest(self.root)
        self.write(artifact, "# Discussion\n\nUpdated\n")
        git_config.write_text("after\n", encoding="utf-8")
        after = capture_workspace_manifest(self.root)

        with self.assertRaisesRegex(
            DiscussionLifecycleError, "write outside the discussion lifecycle allowlist: .git/config"
        ):
            validate_discussion_write_footprint(before, after)

    def test_manifest_round_trip_and_cross_root_comparison_fail_closed(self) -> None:
        self.write_runtime_anchors()
        first = capture_workspace_manifest(self.root)
        restored = WorkspaceManifest.from_dict(first.to_dict())
        self.assertEqual(restored, first)

        other_root = self.root.parent / "other"
        other_root.mkdir()
        other = capture_workspace_manifest(other_root)
        with self.assertRaisesRegex(DiscussionLifecycleError, "different project roots"):
            manifest_changes(first, other)

        missing_inode = first.to_dict()
        del missing_inode["entries"]["docs"]["inode"]
        with self.assertRaisesRegex(
            DiscussionLifecycleError,
            "directory entry docs must include device and inode",
        ):
            WorkspaceManifest.from_dict(missing_inode)

    def test_manifest_rejects_project_root_mode_changes(self) -> None:
        self.write_runtime_anchors()
        artifact = "docs/teamwork/discussion/2026-07-15-community-output.md"
        self.write(artifact, "# Discussion\n")
        self.root.chmod(0o700)
        before = capture_workspace_manifest(self.root)
        self.root.chmod(0o755)
        self.write(artifact, "# Discussion\n\nUpdated\n")
        after = capture_workspace_manifest(self.root)

        with self.assertRaisesRegex(
            DiscussionLifecycleError, "project root mode changed"
        ):
            validate_discussion_write_footprint(before, after)

    def test_manifest_rejects_project_root_identity_and_type_changes(self) -> None:
        manifest = capture_workspace_manifest(self.root)
        changed_identity = replace(
            manifest,
            root_metadata=replace(
                manifest.root_metadata, inode=manifest.root_metadata.inode + 1
            ),
        )
        with self.assertRaisesRegex(
            DiscussionLifecycleError, "project root identity changed"
        ):
            manifest_changes(manifest, changed_identity)

        changed_type = replace(
            manifest,
            root_metadata=replace(manifest.root_metadata, kind="file"),
        )
        with self.assertRaisesRegex(
            DiscussionLifecycleError, "project root type changed"
        ):
            manifest_changes(manifest, changed_type)

    def test_cli_captures_and_verifies_a_clean_activation_footprint(self) -> None:
        manifest_path = self.root.parent / "before.json"
        snapshot = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "snapshot",
                "--project",
                str(self.root),
                "--output",
                str(manifest_path),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(snapshot.returncode, 0, snapshot.stdout + snapshot.stderr)
        self.assertTrue(manifest_path.is_file())
        self.write_runtime_anchors()
        self.write(
            "docs/teamwork/discussion/2026-07-15-community-output.md",
            "# Discussion\n",
        )

        verify = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "verify",
                "--project",
                str(self.root),
                "--before",
                str(manifest_path),
                "--require-memory-anchor-updates",
            ],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(verify.returncode, 0, verify.stdout + verify.stderr)
        report = json.loads(verify.stdout)
        self.assertEqual(
            report["discussion_path"],
            "docs/teamwork/discussion/2026-07-15-community-output.md",
        )

    def test_cli_verifies_an_explicit_replacement(self) -> None:
        self.write_runtime_anchors()
        existing = "docs/teamwork/discussion/2026-07-15-first.md"
        replacement = "docs/teamwork/discussion/2026-07-15-second.md"
        self.write(existing, "# First\n")
        manifest_path = self.root.parent / "replacement-before.json"
        snapshot = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "snapshot",
                "--project",
                str(self.root),
                "--output",
                str(manifest_path),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(snapshot.returncode, 0, snapshot.stdout + snapshot.stderr)
        self.write(existing, "# First\n\nSuperseded\n")
        self.write(replacement, "# Second\n")
        for anchor in (
            "docs/teamwork/index.json",
            "docs/teamwork/current.md",
            "docs/teamwork/README.md",
        ):
            self.write(anchor, self.root.joinpath(anchor).read_text() + "updated\n")

        verify = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "verify",
                "--project",
                str(self.root),
                "--before",
                str(manifest_path),
                "--replacement",
            ],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(verify.returncode, 0, verify.stdout + verify.stderr)
        self.assertEqual(json.loads(verify.stdout)["discussion_path"], replacement)

    def test_cli_refuses_to_store_a_manifest_inside_the_observed_project(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "snapshot",
                "--project",
                str(self.root),
                "--output",
                str(self.root / "before.json"),
            ],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("must be outside the observed project", result.stderr)


class FreshSessionRecoveryTests(unittest.TestCase):
    def test_matches_decision_recovery_anchors_with_at_most_one_question(self) -> None:
        report = assert_fresh_session_recovery(
            "Settled: preserve public wording. Resume point: choose the source boundary?",
            required_fragments=("preserve public wording", "resume point"),
        )

        self.assertEqual(
            report.matched_fragments,
            ("preserve public wording", "resume point"),
        )
        self.assertEqual(report.question_mark_count, 1)

    def test_rejects_missing_anchor_or_question_spam(self) -> None:
        with self.assertRaisesRegex(
            FreshSessionRecoveryError, "did not recover required fragment"
        ):
            assert_fresh_session_recovery(
                "Settled: use plain language.",
                required_fragments=("resume point",),
            )
        with self.assertRaisesRegex(FreshSessionRecoveryError, "exceeds the question bound"):
            assert_fresh_session_recovery(
                "Resume point: source? Audience? Evidence?",
                required_fragments=("resume point",),
            )


if __name__ == "__main__":
    unittest.main()
