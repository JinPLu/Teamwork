#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import validate_teamwork_index as validator


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "scripts/validate_teamwork_index.py"
DISCUSSION_PATH = "docs/teamwork/discussion/2026-07-15-path-safety.md"


class DiscussionIndexSafetyTests(unittest.TestCase):
    def artifact(
        self,
        *,
        status: str = "active",
        still_open: str | None = None,
        superseded_by: str | None = None,
    ) -> str:
        if still_open is None:
            still_open = (
                "- Confirm every runtime-memory path is a regular project file."
                if status == "active"
                else "None."
            )
        if superseded_by is None:
            superseded_by = "Replaced by a later discussion route." if status == "superseded" else "none"
        return f"""Artifact Type: discussion
Status: {status}
Authority: supporting
Last Updated: 2026-07-15
Search Keys: path, safety, discussion
Abstract: Preserve the discussion validator path-safety decision.
Linked Artifacts: none
Superseded By: {superseded_by}

# Keep discussion artifacts inside the project

## Goal

Prevent runtime-memory validation from following external symbolic links.

## Settled

- Runtime memory belongs to the project that owns its index.

## Still open

{still_open}

## Key evidence

- Symbolic links can otherwise make validation read an external file.

## Continue here

Run the focused validator safety tests.
"""

    def index(self, *, active_discussion: bool = True) -> dict:
        active = {
            "current": "docs/teamwork/current.md",
            "discussion": DISCUSSION_PATH if active_discussion else None,
            "results": [],
        }
        entries = [
            {
                "topic": "continuity",
                "kind": "progress",
                "title": "Current state",
                "status": "active",
                "currentness": "current",
                "authority": "active-summary",
                "path": "docs/teamwork/current.md",
                "updated": "2026-07-15",
                "summary": "Current runtime state.",
            }
        ]
        if active_discussion:
            entries.append(
                {
                    "topic": "path-safety",
                    "kind": "discussion",
                    "title": "Discussion path safety",
                    "status": "active",
                    "currentness": "current",
                    "authority": "supporting",
                    "path": DISCUSSION_PATH,
                    "updated": "2026-07-15",
                    "summary": "Keep discussion artifacts inside the project.",
                }
            )
        return {
            "schema_version": 1,
            "last_updated": "2026-07-15",
            "project": {"name": "fixture", "root": ".", "description": "Validator fixture."},
            "source_of_truth_order": ["docs/teamwork/index.json"],
            "ignore_globs": [".planning/**"],
            "budgets": {"header_first": True},
            "active": active,
            "entries": entries,
            "profiles": {"default": {}},
        }

    def write_project(self, base: Path, index: dict, *, artifact_status: str = "active") -> Path:
        project = base / "project"
        (project / "docs/teamwork/discussion").mkdir(parents=True)
        (project / "docs/teamwork/index.json").write_text(json.dumps(index), encoding="utf-8")
        anchor = index["active"]["discussion"] or "none"
        (project / "docs/teamwork/current.md").write_text(
            f"# Current\n\n- Active discussion: {anchor}.\n", encoding="utf-8"
        )
        (project / "docs/teamwork/README.md").write_text(
            f"# Runtime memory\n\n- Active discussion route: {anchor}\n", encoding="utf-8"
        )
        if any(entry["kind"] == "discussion" for entry in index["entries"]):
            (project / DISCUSSION_PATH).write_text(
                self.artifact(status=artifact_status), encoding="utf-8"
            )
        return project

    def run_validator(self, project: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(VALIDATOR), str(project / "docs/teamwork/index.json")],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_rejects_external_discussion_artifact_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            project = self.write_project(base, self.index())
            outside = base / "outside-artifact.md"
            outside.write_text(self.artifact(), encoding="utf-8")
            (project / DISCUSSION_PATH).unlink()
            os.symlink(outside, project / DISCUSSION_PATH)

            result = self.run_validator(project)

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("must be a regular project file", result.stderr)

    def test_accepts_single_link_regular_canonical_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self.write_project(Path(tmp), self.index())

            result = self.run_validator(project)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("PASS: Teamwork index contract/template validation", result.stdout)

    def test_rejects_hardlinked_active_discussion_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            project = self.write_project(base, self.index())
            os.link(project / DISCUSSION_PATH, base / "artifact-hardlink.md")

            result = self.run_validator(project)

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("discussion artifact must have exactly one hard link", result.stderr)

    def test_rejects_hardlinked_historical_discussion_artifacts(self) -> None:
        for status, authority in (("accepted", "supporting"), ("superseded", "superseded")):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as tmp:
                base = Path(tmp)
                index = self.index(active_discussion=False)
                index["entries"].append(
                    {
                        "topic": "path-safety",
                        "kind": "discussion",
                        "title": "Discussion path safety",
                        "status": status,
                        "currentness": "historical",
                        "authority": authority,
                        "path": DISCUSSION_PATH,
                        "updated": "2026-07-15",
                        "summary": "Keep discussion artifacts inside the project.",
                    }
                )
                project = self.write_project(base, index, artifact_status=status)
                os.link(project / DISCUSSION_PATH, base / f"{status}-artifact-hardlink.md")

                result = self.run_validator(project)

                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn(
                    "discussion artifact must have exactly one hard link",
                    result.stderr,
                )

    def test_rejects_partial_canonical_state_when_transaction_marker_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self.write_project(Path(tmp), self.index())
            (project / "docs/teamwork/current.md").write_bytes(b"partial canonical bytes")
            (project / "docs/teamwork/.discussion-transaction.json").write_text(
                '{"phase":"prepared"}',
                encoding="utf-8",
            )

            result = self.run_validator(project)

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("pending or indeterminate discussion transaction", result.stderr)

    def test_rejects_transaction_marker_of_any_filesystem_type(self) -> None:
        marker_kinds = ("regular", "symlink", "directory", "fifo")
        for marker_kind in marker_kinds:
            with self.subTest(marker_kind=marker_kind), tempfile.TemporaryDirectory() as tmp:
                base = Path(tmp)
                project = self.write_project(base, self.index())
                marker = project / "docs/teamwork/.discussion-transaction.json"
                if marker_kind == "regular":
                    marker.write_text("{}", encoding="utf-8")
                elif marker_kind == "symlink":
                    outside = base / "outside-marker.json"
                    outside.write_text("{}", encoding="utf-8")
                    os.symlink(outside, marker)
                elif marker_kind == "directory":
                    marker.mkdir()
                else:
                    os.mkfifo(marker)

                result = self.run_validator(project)

                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn(
                    "pending or indeterminate discussion transaction",
                    result.stderr,
                )

    def test_rejects_special_active_discussion_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self.write_project(Path(tmp), self.index())
            artifact = project / DISCUSSION_PATH
            artifact.unlink()
            os.mkfifo(artifact)

            result = self.run_validator(project)

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("discussion artifact must be a regular project file", result.stderr)

    def test_rejects_file_replacement_during_fd_read(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self.write_project(Path(tmp), self.index())
            current = project / "docs/teamwork/current.md"
            displaced = project / "docs/teamwork/displaced-current.md"
            reader = validator.SafeProjectReader(project)
            original_read = os.read
            replaced = False

            def replace_then_read(fd: int, size: int) -> bytes:
                nonlocal replaced
                if not replaced:
                    replaced = True
                    current.rename(displaced)
                    current.write_text(displaced.read_text(encoding="utf-8"), encoding="utf-8")
                return original_read(fd, size)

            try:
                with mock.patch.object(validator.os, "read", side_effect=replace_then_read):
                    with self.assertRaisesRegex(
                        validator.ValidationError,
                        "active.current changed identity while being read",
                    ):
                        reader.read_text(
                            validator.PurePosixPath("docs/teamwork/current.md"),
                            "active.current",
                        )
            finally:
                reader.close()

    def test_rejects_canonical_namespace_replacement_during_fd_read(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self.write_project(Path(tmp), self.index())
            memory = project / "docs/teamwork"
            displaced = project / "docs/displaced-teamwork"
            reader = validator.SafeProjectReader(project)
            original_read = os.read
            replaced = False

            def replace_namespace_then_read(fd: int, size: int) -> bytes:
                nonlocal replaced
                if not replaced:
                    replaced = True
                    memory.rename(displaced)
                    memory.mkdir()
                return original_read(fd, size)

            try:
                with mock.patch.object(
                    validator.os,
                    "read",
                    side_effect=replace_namespace_then_read,
                ):
                    with self.assertRaisesRegex(
                        validator.ValidationError,
                        "canonical docs/teamwork namespace changed identity",
                    ):
                        reader.read_text(
                            validator.PurePosixPath("docs/teamwork/current.md"),
                            "active.current",
                        )
            finally:
                reader.close()

    def test_rejects_invalid_calendar_dates(self) -> None:
        mutations = (
            ("index", lambda index: index.__setitem__("last_updated", "2026-02-30")),
            ("entry", lambda index: index["entries"][0].__setitem__("updated", "2026-02-30")),
        )
        for label, mutate in mutations:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as tmp:
                index = self.index()
                mutate(index)
                project = self.write_project(Path(tmp), index)

                result = self.run_validator(project)

                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("must be a valid YYYY-MM-DD date", result.stderr)

        with tempfile.TemporaryDirectory() as tmp:
            project = self.write_project(Path(tmp), self.index())
            artifact = self.artifact().replace(
                "Last Updated: 2026-07-15",
                "Last Updated: 2026-02-30",
            )
            (project / DISCUSSION_PATH).write_text(artifact, encoding="utf-8")

            result = self.run_validator(project)

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn(
                "discussion artifact Last Updated must be a valid YYYY-MM-DD date",
                result.stderr,
            )

    def test_requires_coherent_superseded_by_header(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = self.write_project(Path(tmp), self.index())
            artifact = self.artifact().replace("Superseded By: none\n", "")
            (project / DISCUSSION_PATH).write_text(artifact, encoding="utf-8")

            result = self.run_validator(project)

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("discussion artifact missing header: Superseded By", result.stderr)

        with tempfile.TemporaryDirectory() as tmp:
            project = self.write_project(Path(tmp), self.index())
            (project / DISCUSSION_PATH).write_text(
                self.artifact(superseded_by="another route"),
                encoding="utf-8",
            )

            result = self.run_validator(project)

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("active discussion artifact Superseded By must be none", result.stderr)

        with tempfile.TemporaryDirectory() as tmp:
            index = self.index(active_discussion=False)
            index["entries"].append(
                {
                    "topic": "path-safety",
                    "kind": "discussion",
                    "title": "Discussion path safety",
                    "status": "superseded",
                    "currentness": "historical",
                    "authority": "superseded",
                    "path": DISCUSSION_PATH,
                    "updated": "2026-07-15",
                    "summary": "Keep discussion artifacts inside the project.",
                }
            )
            project = self.write_project(Path(tmp), index, artifact_status="superseded")
            (project / DISCUSSION_PATH).write_text(
                self.artifact(status="superseded", superseded_by="none"),
                encoding="utf-8",
            )

            result = self.run_validator(project)

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn(
                "superseded discussion artifact must name a successor or reason",
                result.stderr,
            )

    def test_rejects_index_file_symlink_before_reading_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            project = self.write_project(base, self.index())
            index_path = project / "docs/teamwork/index.json"
            outside = base / "outside-index.json"
            index_path.rename(outside)
            os.symlink(outside, index_path)

            result = self.run_validator(project)

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("index input must be a regular project file", result.stderr)

    def test_rejects_symlinked_runtime_memory_ancestors(self) -> None:
        for relative_ancestor in (Path("docs"), Path("docs/teamwork")):
            with self.subTest(ancestor=relative_ancestor), tempfile.TemporaryDirectory() as tmp:
                base = Path(tmp)
                project = self.write_project(base, self.index())
                ancestor = project / relative_ancestor
                outside = base / f"outside-{'-'.join(relative_ancestor.parts)}"
                ancestor.rename(outside)
                os.symlink(outside, ancestor)

                result = self.run_validator(project)

                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("must be a non-symlink directory", result.stderr)

    def test_rejects_symlinked_project_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            project = self.write_project(base, self.index())
            linked_project = base / "linked-project"
            os.symlink(project, linked_project)

            result = self.run_validator(linked_project)

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn(
                "index input project root must be a non-symlink directory",
                result.stderr,
            )

    def test_rejects_symlinked_discussion_directory_ancestor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            project = self.write_project(base, self.index())
            discussion_dir = project / "docs/teamwork/discussion"
            outside_dir = base / "outside-discussion"
            outside_dir.mkdir()
            (outside_dir / Path(DISCUSSION_PATH).name).write_text(
                self.artifact(), encoding="utf-8"
            )
            (project / DISCUSSION_PATH).unlink()
            discussion_dir.rmdir()
            os.symlink(outside_dir, discussion_dir)

            result = self.run_validator(project)

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("must be a regular project file", result.stderr)

    def test_rejects_duplicate_historical_discussion_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            index = self.index(active_discussion=False)
            historical = {
                "topic": "path-safety",
                "kind": "discussion",
                "title": "Discussion path safety",
                "status": "accepted",
                "currentness": "historical",
                "authority": "supporting",
                "path": DISCUSSION_PATH,
                "updated": "2026-07-15",
                "summary": "Keep discussion artifacts inside the project.",
            }
            index["entries"].extend((historical, {**historical, "topic": "other-route"}))
            project = self.write_project(base, index, artifact_status="accepted")

            result = self.run_validator(project)

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("duplicate discussion entries.path", result.stderr)

    def test_rejects_closed_discussion_with_an_unresolved_item(self) -> None:
        for status, authority in (("accepted", "supporting"), ("superseded", "superseded")):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as tmp:
                base = Path(tmp)
                index = self.index(active_discussion=False)
                index["entries"].append(
                    {
                        "topic": "path-safety",
                        "kind": "discussion",
                        "title": "Discussion path safety",
                        "status": status,
                        "currentness": "historical",
                        "authority": authority,
                        "path": DISCUSSION_PATH,
                        "updated": "2026-07-15",
                        "summary": "Keep discussion artifacts inside the project.",
                    }
                )
                project = self.write_project(base, index, artifact_status=status)
                (project / DISCUSSION_PATH).write_text(
                    self.artifact(
                        status=status,
                        still_open="- Decide whether another safety check is required.",
                    ),
                    encoding="utf-8",
                )

                result = self.run_validator(project)

                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn(
                    "closed discussion artifact Still open must explicitly be none",
                    result.stderr,
                )

    def test_rejects_duplicate_required_discussion_header(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            project = self.write_project(base, self.index())
            artifact = self.artifact().replace(
                "Status: active\n",
                "Status: accepted\nStatus: active\n",
            )
            (project / DISCUSSION_PATH).write_text(artifact, encoding="utf-8")

            result = self.run_validator(project)

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn(
                "discussion artifact header must appear exactly once: Status",
                result.stderr,
            )

    def test_rejects_duplicate_required_discussion_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            project = self.write_project(base, self.index())
            artifact = self.artifact() + """
## Still open

- Confirm no second unresolved item can hide behind the first section.
"""
            (project / DISCUSSION_PATH).write_text(artifact, encoding="utf-8")

            result = self.run_validator(project)

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn(
                "discussion artifact section must appear exactly once: Still open",
                result.stderr,
            )

    def test_rejects_duplicate_optional_decision_map(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            project = self.write_project(base, self.index())
            decision_map = """
## Decision map

```mermaid
flowchart LR
    input[Input] --> validation[Validation]
```
"""
            (project / DISCUSSION_PATH).write_text(
                self.artifact() + decision_map + decision_map,
                encoding="utf-8",
            )

            result = self.run_validator(project)

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn(
                "discussion artifact section must appear at most once: Decision map",
                result.stderr,
            )

    def test_rejects_external_current_and_readme_symlinks(self) -> None:
        for runtime_path in ("docs/teamwork/current.md", "docs/teamwork/README.md"):
            with self.subTest(runtime_path=runtime_path), tempfile.TemporaryDirectory() as tmp:
                base = Path(tmp)
                project = self.write_project(base, self.index())
                target = project / runtime_path
                outside = base / target.name
                outside.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
                target.unlink()
                os.symlink(outside, target)

                result = self.run_validator(project)

                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("must be a regular project file", result.stderr)

    def test_rejects_switching_active_current_away_from_the_canonical_digest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            index = self.index()
            alternate_path = "docs/teamwork/alternate-current.md"
            index["active"]["current"] = alternate_path
            index["entries"][0]["path"] = alternate_path
            project = self.write_project(base, index)
            (project / "docs/teamwork/current.md").rename(project / alternate_path)

            result = self.run_validator(project)

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn(
                "actual project index active.current must be docs/teamwork/current.md",
                result.stderr,
            )

    def test_rejects_candidate_discussion_even_without_an_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            index = self.index(active_discussion=False)
            index["entries"].append(
                {
                    "topic": "candidate-route",
                    "kind": "discussion",
                    "title": "Candidate discussion route",
                    "status": "candidate",
                    "currentness": "candidate",
                    "authority": "candidate",
                    "path": DISCUSSION_PATH,
                    "updated": "2026-07-15",
                    "summary": "Candidate route has no artifact yet.",
                }
            )
            project = self.write_project(base, index)
            (project / DISCUSSION_PATH).unlink()

            result = self.run_validator(project)

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("discussion entry status has unknown value: candidate", result.stderr)

    def test_rejects_undefined_discussion_index_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            index = self.index(active_discussion=False)
            index["entries"].append(
                {
                    "topic": "blocked-route",
                    "kind": "discussion",
                    "title": "Blocked discussion route",
                    "status": "blocked",
                    "currentness": "historical",
                    "authority": "supporting",
                    "path": DISCUSSION_PATH,
                    "updated": "2026-07-15",
                    "summary": "This status is outside the discussion protocol.",
                }
            )
            project = self.write_project(base, index, artifact_status="blocked")

            result = self.run_validator(project)

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("discussion entry status has unknown value", result.stderr)


if __name__ == "__main__":
    unittest.main()
