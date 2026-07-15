from __future__ import annotations

import copy
import fcntl
import json
import os
import runpy
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import validate_teamwork_index as index_validator


ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "skills/using-teamwork/scripts/discussion-transaction.py"
VALIDATOR = ROOT / "scripts/validate_teamwork_index.py"
ARTIFACT = "docs/teamwork/discussion/2026-07-15-output-wording.md"


class DiscussionTransactionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.project = Path(self.temporary.name) / "project"
        self.memory = self.project / "docs/teamwork"
        self.memory.mkdir(parents=True)
        self.initial_entry = {
            "topic": "project-initialization",
            "kind": "result",
            "title": "Teamwork project initialization",
            "status": "active",
            "currentness": "current",
            "authority": "active-summary",
            "path": "docs/teamwork/current.md",
            "applies_to": ["AGENTS.md", "docs/teamwork/"],
            "linked": [],
            "evidence_paths": ["docs/teamwork/current.md"],
            "supersedes": [],
            "search_keys": ["teamwork-init", "project-init", "initialization"],
            "updated": "2026-07-15",
            "summary": "Initial Teamwork runtime memory entry created by project init.",
        }
        self.write_index([copy.deepcopy(self.initial_entry)], active=None)
        (self.memory / "current.md").write_text(
            """# Teamwork Current State

Last Updated: 2026-07-15

## Active Snapshot

- Current focus: Initial Teamwork project setup.
- Active discussion: none.
- Active plan/design: none.
- Progress summary: Teamwork runtime memory was initialized for this project.
- Latest result: Project instructions and Teamwork runtime memory are ready for use.
- Blockers: none recorded.
- Next action: Replace this digest when material project state changes.
""",
            encoding="utf-8",
        )
        (self.memory / "README.md").write_text(
            """# Teamwork Runtime Index README

## Current Anchors

- Active state: `docs/teamwork/current.md`
- Active discussion route: none
""",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_index(self, entries: list[dict[str, object]], *, active: str | None) -> None:
        index = {
            "schema_version": 1,
            "last_updated": "2026-07-15",
            "project": {"name": "Fixture", "root": ".", "description": "Fixture project."},
            "source_of_truth_order": ["active", "linked", "header_search", "fulltext"],
            "ignore_globs": [".planning/**"],
            "budgets": {"header_first": True},
            "active": {
                "current": "docs/teamwork/current.md",
                "design": None,
                "plan": None,
                "progress": None,
                "goal": None,
                "report": None,
                "discussion": active,
                "results": [],
            },
            "entries": entries,
            "profiles": {
                "status": ["index", "current", "active_discussion", "topic"],
                "implementation": ["index", "current", "active_discussion", "active_design_or_plan", "linked_research_headers"],
                "review": ["index", "current", "active_discussion", "active_design_or_plan", "active_progress", "verification"],
                "research": ["index", "current", "active_discussion", "topic_headers", "linked_artifacts"],
                "design": ["index", "current", "active_discussion", "accepted_decisions", "active_design_plan", "linked_research"],
            },
            "pending": [],
        }
        (self.memory / "index.json").write_text(
            json.dumps(index, indent=2) + "\n", encoding="utf-8"
        )

    def artifact(self, status: str, *, settled: str = "Use plain wording.") -> str:
        still_open = "- Which evidence should lead the reply?" if status == "active" else "- None"
        return f"""Artifact Type: discussion
Status: {status}
Authority: supporting
Last Updated: 2026-07-15
Search Keys: output wording, evidence
Abstract: Tracks the remaining evidence-order decision.
Linked Artifacts: none
Superseded By: none

# Researcher-facing output wording

## Goal

Keep replies concise and decision-relevant.

## Settled

- {settled}

## Still open

{still_open}

## Key evidence

- The audience rubric rejects internal process inventory.

## Continue here

Choose the evidence that should lead the next reply.
"""

    def entry(self, summary: str = "Tracks the active output wording decision.") -> dict[str, object]:
        return {
            "topic": "output-wording",
            "kind": "incorrect-on-purpose",
            "title": "Researcher-facing output wording",
            "status": "incorrect-on-purpose",
            "currentness": "incorrect-on-purpose",
            "authority": "incorrect-on-purpose",
            "path": "incorrect/on-purpose.md",
            "applies_to": ["skills/using-teamwork/"],
            "linked": [],
            "evidence_paths": [ARTIFACT],
            "supersedes": [],
            "search_keys": ["output wording", "evidence order"],
            "updated": "2026-07-15",
            "summary": summary,
        }

    def inspect_cli(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CLI), "inspect", "--project-root", str(self.project)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def revision(self) -> str:
        result = self.inspect_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)["revision"]

    def spec(
        self,
        operation: str,
        *,
        expected_revision: str | None = None,
        close_status: str = "accepted",
        superseded_by: str = "obsolete decision route",
        **record_overrides: object,
    ) -> dict[str, object]:
        record: dict[str, object] = {
            "title": "Researcher-facing output wording",
            "search_keys": ["output wording", "evidence order"],
            "abstract": "Tracks the remaining evidence-order decision.",
            "linked_artifacts": [],
            "summary": "Tracks the active output wording decision.",
            "goal": "Keep replies concise and decision-relevant.",
            "settled": ["Use plain wording."],
            "still_open": [] if operation == "close" else ["Which evidence should lead the reply?"],
            "key_evidence": ["The audience rubric rejects internal process inventory."],
            "continue_here": "Choose the evidence that should lead the next reply.",
        }
        if operation in {"create", "replace"}:
            record.update(topic="output-wording", slug="output-wording")
        record.update(record_overrides)
        result = {
            "schema_version": 1,
            "operation": operation,
            "expected_revision": expected_revision or self.revision(),
            "record": record,
            "current_summary": {
                "last_updated": "2026-07-15",
                "current_focus": "Researcher-facing output wording.",
                "progress_summary": "The discussion recovery checkpoint is current.",
                "latest_result": "The current wording choice is recorded.",
                "next_action": "Resolve the remaining evidence-order choice.",
            },
        }
        if operation == "close":
            result["close_status"] = close_status
            if close_status == "superseded":
                result["superseded_by"] = superseded_by
        return result

    def run_cli(
        self,
        spec: dict[str, object] | str,
        *,
        env: dict[str, str] | None = None,
        spec_file: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        command = [sys.executable, str(CLI), "apply", "--project-root", str(self.project)]
        if spec_file is None:
            payload = spec if isinstance(spec, str) else json.dumps(spec)
            command.extend(("--request-json", payload))
        else:
            command.extend(("--request", str(spec_file)))
        process_env = os.environ.copy()
        if env:
            process_env.update(env)
        return subprocess.run(
            command,
            cwd=ROOT,
            env=process_env,
            text=True,
            capture_output=True,
            check=False,
        )

    def run_guard(
        self,
        command: list[str],
        *,
        project: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(CLI),
                "guard",
                "--project-root",
                str(project or self.project),
                "--",
                *command,
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def load_index(self) -> dict[str, object]:
        return json.loads((self.memory / "index.json").read_text(encoding="utf-8"))

    def validate(self) -> None:
        reader = index_validator.SafeProjectReader(self.project)
        try:
            index_validator.validate_index(
                self.load_index(),
                self.memory / "index.json",
                reader,
            )
        except index_validator.ValidationError as exc:
            self.fail(str(exc))
        finally:
            reader.close()

    def assert_formal_invalid(self, index: dict[str, object]) -> None:
        reader = index_validator.SafeProjectReader(self.project)
        try:
            with self.assertRaises(index_validator.ValidationError):
                index_validator.validate_index(index, self.memory / "index.json", reader)
        finally:
            reader.close()

    def filesystem_state(self) -> dict[str, tuple[object, ...]]:
        state: dict[str, tuple[object, ...]] = {}
        for path in sorted((self.project, *self.project.rglob("*")), key=str):
            relative = "." if path == self.project else path.relative_to(self.project).as_posix()
            info = path.lstat()
            if stat.S_ISREG(info.st_mode):
                state[relative] = ("file", info.st_dev, info.st_ino, stat.S_IMODE(info.st_mode), path.read_bytes())
            elif stat.S_ISDIR(info.st_mode):
                state[relative] = ("directory", info.st_dev, info.st_ino, stat.S_IMODE(info.st_mode))
            elif stat.S_ISLNK(info.st_mode):
                state[relative] = ("symlink", os.readlink(path))
            else:
                state[relative] = ("other", stat.S_IFMT(info.st_mode))
        return state

    def activate_fixture(self, *, duplicate: bool = False) -> None:
        discussion = self.memory / "discussion"
        discussion.mkdir()
        (self.project / ARTIFACT).write_text(self.artifact("active"), encoding="utf-8")
        active_entry = self.entry()
        active_entry.update(
            {"kind": "discussion", "path": ARTIFACT, "status": "active", "currentness": "current", "authority": "supporting"}
        )
        entries = [copy.deepcopy(self.initial_entry), active_entry]
        if duplicate:
            entries.append(copy.deepcopy(active_entry))
        self.write_index(entries, active=ARTIFACT)
        current = (self.memory / "current.md").read_text(encoding="utf-8")
        current = current.replace("- Active discussion: none.", f"- Active discussion: {ARTIFACT}.")
        (self.memory / "current.md").write_text(current, encoding="utf-8")
        readme = (self.memory / "README.md").read_text(encoding="utf-8")
        readme = readme.replace("- Active discussion route: none", f"- Active discussion route: {ARTIFACT}")
        (self.memory / "README.md").write_text(readme, encoding="utf-8")

    def test_inspect_defaults_project_root_to_working_directory(self) -> None:
        result = subprocess.run(
            [sys.executable, str(CLI), "inspect"],
            cwd=self.project,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["initialized"])
        self.assertIsNone(payload["active"])
        self.assertRegex(payload["revision"], r"^[0-9a-f]{64}$")

    def test_apply_defaults_project_root_to_working_directory(self) -> None:
        request = self.spec("create")
        result = subprocess.run(
            [sys.executable, str(CLI), "apply", "--request-json", json.dumps(request)],
            cwd=self.project,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["operation"], "create")
        self.assertEqual(self.load_index()["active"]["discussion"], ARTIFACT)
        self.validate()

    def test_guard_passes_verifiable_fds_token_and_exclusive_lock(self) -> None:
        validator = r'''
import fcntl
import os
import re
import stat
import sys

names = ("ROOT", "DOCS", "TEAMWORK", "LOCK")
fds = {name: int(os.environ[f"TEAMWORK_DISCUSSION_GUARD_{name}_FD"]) for name in names}
infos = {name: os.fstat(fd) for name, fd in fds.items()}
assert all(stat.S_ISDIR(info.st_mode) for info in infos.values())
assert len({infos[name].st_dev for name in names}) == 1
assert re.fullmatch(r"[0-9a-f]{64}", os.environ["TEAMWORK_DISCUSSION_GUARD_TOKEN"])
docs = os.stat("docs", dir_fd=fds["ROOT"], follow_symlinks=False)
teamwork = os.stat("teamwork", dir_fd=fds["DOCS"], follow_symlinks=False)
assert (docs.st_dev, docs.st_ino) == (infos["DOCS"].st_dev, infos["DOCS"].st_ino)
assert (teamwork.st_dev, teamwork.st_ino) == (infos["TEAMWORK"].st_dev, infos["TEAMWORK"].st_ino)
probe = os.open("teamwork", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fds["DOCS"])
try:
    try:
        fcntl.flock(probe, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        pass
    else:
        raise AssertionError("guard lock was not held by the parent")
finally:
    os.close(probe)
sys.exit(0)
'''
        result = self.run_guard([sys.executable, "-c", validator])

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_guard_returns_child_exit_code_without_shell_interpretation(self) -> None:
        result = self.run_guard([sys.executable, "-c", "import sys; sys.exit(7)", "; exit 0"])

        self.assertEqual(result.returncode, 7)

    def test_guard_allows_partial_runtime_initialization(self) -> None:
        (self.memory / "README.md").unlink()

        result = self.run_guard([sys.executable, "-c", "import sys; sys.exit(0)"])

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_guard_creates_absent_runtime_and_runs_child_with_locked_fds(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            project.mkdir()
            sentinel = project / "command-ran"
            validator = f'''
import fcntl
import os
import stat
from pathlib import Path

names = ("ROOT", "DOCS", "TEAMWORK", "LOCK")
fds = {{name: int(os.environ[f"TEAMWORK_DISCUSSION_GUARD_{{name}}_FD"]) for name in names}}
infos = {{name: os.fstat(fd) for name, fd in fds.items()}}
assert all(stat.S_ISDIR(info.st_mode) for info in infos.values())
docs = os.stat("docs", dir_fd=fds["ROOT"], follow_symlinks=False)
teamwork = os.stat("teamwork", dir_fd=fds["DOCS"], follow_symlinks=False)
assert (docs.st_dev, docs.st_ino) == (infos["DOCS"].st_dev, infos["DOCS"].st_ino)
assert (teamwork.st_dev, teamwork.st_ino) == (infos["TEAMWORK"].st_dev, infos["TEAMWORK"].st_ino)
probe = os.open("teamwork", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fds["DOCS"])
try:
    try:
        fcntl.flock(probe, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        pass
    else:
        raise AssertionError("guard lock was not held by the parent")
finally:
    os.close(probe)
Path({str(sentinel)!r}).touch()
'''
            result = self.run_guard(
                [sys.executable, "-c", validator],
                project=project,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(sentinel.exists())
            self.assertTrue((project / "docs/teamwork").is_dir())

    def test_guard_cleans_created_directories_if_child_cannot_start(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            project.mkdir()

            result = self.run_guard(["/definitely/not/a/real/executable"], project=project)

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(json.loads(result.stderr)["category"], "PREWRITE_SAFE")
            self.assertFalse((project / "docs").exists())

    def test_guard_checks_lock_before_marker_and_never_runs_child(self) -> None:
        marker = self.memory / ".discussion-transaction.json"
        marker.write_text("{}\n", encoding="utf-8")
        lock_fd = os.open(self.memory, os.O_RDONLY | os.O_DIRECTORY)
        sentinel = self.project / "command-ran"
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            result = self.run_guard(
                [sys.executable, "-c", f"from pathlib import Path; Path({str(sentinel)!r}).touch()"]
            )
        finally:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            os.close(lock_fd)

        self.assertNotEqual(result.returncode, 0)
        error = json.loads(result.stderr)
        self.assertEqual(error["category"], "PREWRITE_SAFE")
        self.assertIn("cannot acquire Teamwork initialization guard", error["message"])
        self.assertFalse(sentinel.exists())

    def test_guard_rejects_marker_after_acquiring_lock(self) -> None:
        (self.memory / ".discussion-transaction.json").write_text("{}\n", encoding="utf-8")
        sentinel = self.project / "command-ran"
        result = self.run_guard(
            [sys.executable, "-c", f"from pathlib import Path; Path({str(sentinel)!r}).touch()"]
        )

        self.assertNotEqual(result.returncode, 0)
        error = json.loads(result.stderr)
        self.assertEqual(error["category"], "INDETERMINATE")
        self.assertIn("unfinished discussion transaction marker", error["message"])
        self.assertFalse(sentinel.exists())

    def test_guard_fails_closed_if_child_replaces_canonical_teamwork_directory(self) -> None:
        replacer = r'''
import os
docs_fd = int(os.environ["TEAMWORK_DISCUSSION_GUARD_DOCS_FD"])
os.rename("teamwork", "teamwork.displaced", src_dir_fd=docs_fd, dst_dir_fd=docs_fd)
os.mkdir("teamwork", 0o755, dir_fd=docs_fd)
'''
        result = self.run_guard([sys.executable, "-c", replacer])
        replacement = self.project / "docs/teamwork"
        displaced = self.project / "docs/teamwork.displaced"
        try:
            self.assertNotEqual(result.returncode, 0)
            error = json.loads(result.stderr)
            self.assertEqual(error["category"], "INDETERMINATE")
            self.assertIn("directory identity changed while guarded", error["message"])
        finally:
            replacement.rmdir()
            displaced.rename(replacement)

    def test_inspect_rechecks_init_marker_after_acquiring_lock(self) -> None:
        namespace = runpy.run_path(str(CLI))
        original_flock = namespace["fcntl"].flock
        calls = 0

        def inject_after_first_flock(fd: int, operation: int) -> object:
            nonlocal calls
            result = original_flock(fd, operation)
            calls += 1
            if calls == 1:
                marker = self.memory / ".teamwork-init-transaction.json"
                marker.write_text("{}\n", encoding="utf-8")
                os.chmod(marker, 0o600)
            return result

        with mock.patch.object(namespace["fcntl"], "flock", side_effect=inject_after_first_flock):
            with self.assertRaises(namespace["TransactionError"]) as raised:
                namespace["inspect_project"](str(self.project))

        self.assertEqual(raised.exception.category, "INDETERMINATE")
        self.assertIn("unfinished Teamwork init transaction marker", str(raised.exception))
        self.assertTrue((self.memory / ".teamwork-init-transaction.json").is_file())

    def test_inspect_no_anchors_rechecks_marker_before_normal_return(self) -> None:
        namespace = runpy.run_path(str(CLI))
        tree_type = namespace["FdTree"]
        original_check = tree_type._require_no_markers
        calls = 0
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            memory = project / "docs/teamwork"
            memory.mkdir(parents=True)

            def inject_after_first_check(tree: object) -> None:
                nonlocal calls
                original_check(tree)
                calls += 1
                if calls == 1:
                    marker = memory / ".teamwork-init-transaction.json"
                    marker.write_text("{}\n", encoding="utf-8")
                    os.chmod(marker, 0o600)

            with mock.patch.object(tree_type, "_require_no_markers", inject_after_first_check):
                with self.assertRaises(namespace["TransactionError"]) as raised:
                    namespace["inspect_project"](str(project))

            self.assertEqual(raised.exception.category, "INDETERMINATE")
            self.assertIn("unfinished Teamwork init transaction marker", str(raised.exception))
            self.assertTrue((memory / ".teamwork-init-transaction.json").is_file())

    def test_guard_fails_closed_on_concurrent_ahead_directory_creation(self) -> None:
        namespace = runpy.run_path(str(CLI))
        guard_tree = namespace["GuardTree"].__new__(namespace["GuardTree"])
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            project.mkdir()
            root_fd = os.open(project, os.O_RDONLY | os.O_DIRECTORY)
            guard_tree.root_path = str(project)
            guard_tree.fds = {"root": root_fd}
            root_info = os.fstat(root_fd)
            guard_tree.identities = {"root": guard_tree._identity(root_info)}
            guard_tree.created = []
            guard_tree.device = root_info.st_dev
            guard_tree.locked = False
            original_mkdir = os.mkdir

            def racing_mkdir(name: str, mode: int, *, dir_fd: int) -> None:
                original_mkdir(name, mode, dir_fd=dir_fd)
                raise FileExistsError(name)

            try:
                with mock.patch("os.mkdir", side_effect=racing_mkdir):
                    with self.assertRaisesRegex(
                        namespace["TransactionError"], "appeared concurrently"
                    ):
                        guard_tree._open_or_create_child("root", "docs", "docs")
                self.assertEqual(guard_tree.created, [])
                self.assertNotIn("docs", guard_tree.fds)
                self.assertTrue((project / "docs").is_dir())
            finally:
                guard_tree.close()

    def test_guard_rejects_concurrent_marker_and_retains_nonempty_created_tree(self) -> None:
        namespace = runpy.run_path(str(CLI))
        guard_type = namespace["GuardTree"]
        original_verify = guard_type.verify_marker_absent
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "project"
            project.mkdir()

            def inject_marker(tree: object) -> None:
                teamwork_fd = tree.fds["teamwork"]
                marker_fd = os.open(
                    ".discussion-transaction.json",
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    0o600,
                    dir_fd=teamwork_fd,
                )
                os.close(marker_fd)
                os.fsync(teamwork_fd)
                original_verify(tree)

            with mock.patch.object(guard_type, "verify_marker_absent", inject_marker):
                with self.assertRaisesRegex(namespace["TransactionError"], "no longer empty") as raised:
                    guard_type(str(project))
            self.assertEqual(raised.exception.category, "INDETERMINATE")
            self.assertTrue((project / "docs/teamwork/.discussion-transaction.json").is_file())

    def test_guard_rejects_cross_device_child_before_open(self) -> None:
        namespace = runpy.run_path(str(CLI))
        guard_tree = namespace["GuardTree"].__new__(namespace["GuardTree"])
        root_fd = os.open(self.project, os.O_RDONLY | os.O_DIRECTORY)
        guard_tree.fds = {"root": root_fd}
        guard_tree.identities = {}
        guard_tree.created = []
        guard_tree.device = os.fstat(root_fd).st_dev
        observed = os.stat(self.project / "docs", follow_symlinks=False)
        values = list(observed)
        values[2] = observed.st_dev + 1
        cross_device = os.stat_result(values)
        try:
            with mock.patch("os.stat", return_value=cross_device):
                with self.assertRaisesRegex(namespace["TransactionError"], "project-root device"):
                    guard_tree._open_or_create_child("root", "docs", "docs")
        finally:
            os.close(root_fd)

    def test_schema_prints_exact_project_independent_lifecycle_templates(self) -> None:
        common_record = {
            "title", "search_keys", "abstract", "linked_artifacts", "summary",
            "goal", "settled", "still_open", "key_evidence", "continue_here",
        }
        expected = {
            "create": ("create", common_record | {"topic", "slug"}, set()),
            "update": ("update", common_record, set()),
            "close": ("close", common_record, {"close_status"}),
            "supersede": ("close", common_record, {"close_status", "superseded_by"}),
            "replace": ("replace", common_record | {"topic", "slug"}, set()),
        }
        with tempfile.TemporaryDirectory() as empty_project:
            for lifecycle, (operation, record_fields, extras) in expected.items():
                with self.subTest(lifecycle=lifecycle):
                    result = subprocess.run(
                        [sys.executable, str(CLI), "schema", lifecycle],
                        cwd=empty_project,
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertNotIn('\": ', result.stdout)
                    template = json.loads(result.stdout)
                    self.assertEqual(
                        set(template),
                        {"schema_version", "operation", "expected_revision", "record", "current_summary"} | extras,
                    )
                    self.assertEqual(template["schema_version"], 1)
                    self.assertEqual(template["operation"], operation)
                    self.assertEqual(set(template["record"]), record_fields)
                    self.assertEqual(
                        set(template["current_summary"]),
                        {"last_updated", "current_focus", "progress_summary", "latest_result", "next_action"},
                    )
                    self.assertRegex(template["expected_revision"], r"^<.+>$")
                    if lifecycle == "close":
                        self.assertEqual(template["close_status"], "accepted")
                    if lifecycle == "supersede":
                        self.assertEqual(template["close_status"], "superseded")
                        self.assertRegex(template["superseded_by"], r"^<.+>$")

    def test_apply_request_sources_are_exclusive_and_stdin_sentinel_is_rejected(self) -> None:
        request = self.spec("create")
        request_file = Path(self.temporary.name) / "request.json"
        request_file.write_text(json.dumps(request), encoding="utf-8")
        both = subprocess.run(
            [
                sys.executable, str(CLI), "apply", "--project-root", str(self.project),
                "--request", str(request_file), "--request-json", json.dumps(request),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(both.returncode, 2)
        self.assertIn("not allowed with argument", both.stderr)

        neither = subprocess.run(
            [sys.executable, str(CLI), "apply", "--project-root", str(self.project)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(neither.returncode, 2)
        self.assertIn("one of the arguments", neither.stderr)

        sentinel = subprocess.run(
            [sys.executable, str(CLI), "apply", "--project-root", str(self.project), "--request", "-"],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            text=True,
            capture_output=True,
            check=False,
            timeout=2,
        )
        self.assertEqual(sentinel.returncode, 1)
        error = json.loads(sentinel.stderr)
        self.assertEqual(error["category"], "PREWRITE_SAFE")
        self.assertIn("stdin is not supported", error["message"])

    def test_create_update_close_preserve_project_init_entry_and_validate(self) -> None:
        managed = [self.memory / name for name in ("index.json", "current.md", "README.md")]
        for path in managed:
            path.chmod(0o640)
        inspected = self.inspect_cli()
        self.assertEqual(inspected.returncode, 0, inspected.stderr)
        inspected_payload = json.loads(inspected.stdout)
        self.assertTrue(inspected_payload["initialized"])
        self.assertIsNone(inspected_payload["active"])
        self.assertRegex(inspected_payload["revision"], r"^[0-9a-f]{64}$")
        create = self.run_cli(self.spec("create"))
        self.assertEqual(create.returncode, 0, create.stderr)
        self.assertEqual(json.loads(create.stdout)["operation"], "create")
        self.assertEqual(json.loads(create.stdout)["changed_paths"][-1], "docs/teamwork/index.json")
        index = self.load_index()
        self.assertEqual(index["entries"][0], self.initial_entry)
        self.assertEqual(index["entries"][1]["kind"], "discussion")
        self.assertEqual(index["entries"][1]["status"], "active")
        self.assertEqual(index["active"]["discussion"], ARTIFACT)
        rendered = (self.project / ARTIFACT).read_text(encoding="utf-8")
        self.assertEqual(
            rendered,
            """Artifact Type: discussion
Status: active
Authority: supporting
Last Updated: 2026-07-15
Search Keys: output wording, evidence order
Abstract: Tracks the remaining evidence-order decision.
Linked Artifacts: none
Superseded By: none

# Researcher-facing output wording

## Goal

Keep replies concise and decision-relevant.

## Settled

- Use plain wording.

## Still open

- Which evidence should lead the reply?

## Key evidence

- The audience rubric rejects internal process inventory.

## Continue here

Choose the evidence that should lead the next reply.
""",
        )
        self.assertTrue(all(stat.S_IMODE(path.stat().st_mode) == 0o640 for path in managed))
        self.validate()
        active_inspection = self.inspect_cli()
        self.assertEqual(active_inspection.returncode, 0, active_inspection.stderr)
        self.assertEqual(json.loads(active_inspection.stdout)["active"]["path"], ARTIFACT)

        update_spec = self.spec(
            "update",
            summary="Updated recovery summary.",
            settled=["Use observed facts before conclusions."],
        )
        update = self.run_cli(update_spec)
        self.assertEqual(update.returncode, 0, update.stderr)
        index = self.load_index()
        self.assertEqual(index["entries"][0], self.initial_entry)
        self.assertEqual(index["entries"][1]["summary"], "Updated recovery summary.")
        self.assertEqual(len(index["entries"]), 2)
        self.validate()

        close = self.run_cli(self.spec("close", close_status="accepted"))
        self.assertEqual(close.returncode, 0, close.stderr)
        index = self.load_index()
        self.assertEqual(index["entries"][0], self.initial_entry)
        self.assertEqual(index["entries"][1]["status"], "accepted")
        self.assertEqual(index["entries"][1]["currentness"], "historical")
        self.assertIsNone(index["active"]["discussion"])
        self.assertIn("- Active discussion: none.", (self.memory / "current.md").read_text(encoding="utf-8"))
        self.assertIn("- Active discussion route: none", (self.memory / "README.md").read_text(encoding="utf-8"))
        self.validate()

    def test_superseded_close_is_semantic_and_clears_all_anchors(self) -> None:
        self.activate_fixture()
        result = self.run_cli(
            self.spec(
                "close",
                close_status="superseded",
                superseded_by="replaced by the canonical plan decision",
            )
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        index = self.load_index()
        entry = index["entries"][-1]
        self.assertEqual(
            (entry["status"], entry["currentness"], entry["authority"]),
            ("superseded", "historical", "superseded"),
        )
        artifact = (self.project / ARTIFACT).read_text(encoding="utf-8")
        self.assertIn("Status: superseded", artifact)
        self.assertIn("Superseded By: replaced by the canonical plan decision", artifact)
        self.assertIn("## Still open\n\n- None", artifact)
        self.assertIsNone(index["active"]["discussion"])
        self.validate()

    def test_inspect_rejects_superseded_artifact_for_accepted_entry(self) -> None:
        self.activate_fixture()
        closed = self.run_cli(self.spec("close", close_status="accepted"))
        self.assertEqual(closed.returncode, 0, closed.stderr)
        artifact = self.project / ARTIFACT
        artifact.write_text(
            artifact.read_text(encoding="utf-8")
            .replace("Status: accepted", "Status: superseded", 1)
            .replace("Superseded By: none", "Superseded By: replacement route", 1),
            encoding="utf-8",
        )

        inspected = self.inspect_cli()

        self.assertNotEqual(inspected.returncode, 0)
        error = json.loads(inspected.stderr)
        self.assertEqual(error["category"], "PREWRITE_SAFE")
        self.assertIn("exactly equal entry.status", error["message"])

    def test_inspect_rejects_accepted_artifact_for_superseded_entry(self) -> None:
        self.activate_fixture()
        closed = self.run_cli(
            self.spec(
                "close",
                close_status="superseded",
                superseded_by="replacement route",
            )
        )
        self.assertEqual(closed.returncode, 0, closed.stderr)
        artifact = self.project / ARTIFACT
        artifact.write_text(
            artifact.read_text(encoding="utf-8")
            .replace("Status: superseded", "Status: accepted", 1)
            .replace("Superseded By: replacement route", "Superseded By: none", 1),
            encoding="utf-8",
        )

        inspected = self.inspect_cli()

        self.assertNotEqual(inspected.returncode, 0)
        error = json.loads(inspected.stderr)
        self.assertEqual(error["category"], "PREWRITE_SAFE")
        self.assertIn("exactly equal entry.status", error["message"])

    def test_replace_atomically_supersedes_old_and_appends_new_active_record(self) -> None:
        self.activate_fixture()
        old_entry = copy.deepcopy(self.load_index()["entries"][-1])
        request = self.spec(
            "replace",
            slug="successor-wording",
            topic="successor-wording",
            title="Successor output wording",
        )
        result = self.run_cli(request)
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        new_path = "docs/teamwork/discussion/2026-07-15-successor-wording.md"
        self.assertEqual(output["path"], new_path)
        self.assertEqual(
            output["changed_paths"],
            [ARTIFACT, new_path, "docs/teamwork/current.md", "docs/teamwork/README.md", "docs/teamwork/index.json"],
        )
        self.assertEqual(len(output["changed_paths"]), len(set(output["changed_paths"])))
        index = self.load_index()
        self.assertEqual(index["entries"][0], self.initial_entry)
        old = index["entries"][1]
        self.assertEqual(old["path"], old_entry["path"])
        self.assertEqual((old["status"], old["currentness"], old["authority"]), ("superseded", "historical", "superseded"))
        new = index["entries"][2]
        self.assertEqual((new["path"], new["status"], new["currentness"], new["authority"]), (new_path, "active", "current", "supporting"))
        self.assertEqual(index["active"]["discussion"], new_path)
        self.assertIn(f"Superseded By: {new_path}", (self.project / ARTIFACT).read_text(encoding="utf-8"))
        self.assertTrue((self.project / new_path).is_file())
        self.validate()

    def test_replace_failure_injections_restore_exact_prestate(self) -> None:
        self.activate_fixture()
        before = self.filesystem_state()
        cases = (("STAGE", range(1, 6)), ("REPLACE", range(1, 10)), ("POST_READBACK", range(1, 2)))
        for kind, positions in cases:
            for nth in positions:
                with self.subTest(kind=kind, nth=nth):
                    result = self.run_cli(
                        self.spec("replace", slug="successor-wording", topic="successor-wording"),
                        env={f"TEAMWORK_DISCUSSION_TRANSACTION_FAIL_{kind}_N": str(nth)},
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(self.filesystem_state(), before)

    def test_update_rejects_duplicate_or_missing_exact_match_before_writing(self) -> None:
        self.activate_fixture()
        revision = self.revision()
        index = self.load_index()
        index["entries"].append(copy.deepcopy(index["entries"][-1]))
        (self.memory / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
        before = self.filesystem_state()
        duplicate = self.run_cli(self.spec("update", expected_revision=revision))
        self.assertNotEqual(duplicate.returncode, 0)
        self.assertEqual(json.loads(duplicate.stderr)["category"], "PREWRITE_SAFE")
        self.assertEqual(self.filesystem_state(), before)

        entries = [copy.deepcopy(self.initial_entry)]
        self.write_index(entries, active=ARTIFACT)
        before = self.filesystem_state()
        missing = self.run_cli(self.spec("update", expected_revision=revision))
        self.assertNotEqual(missing.returncode, 0)
        self.assertEqual(self.filesystem_state(), before)

    def test_apply_rejects_stale_inspection_revision_without_writing(self) -> None:
        request = self.spec("create")
        current = self.memory / "current.md"
        current.write_text(
            current.read_text(encoding="utf-8").replace(
                "- Blockers: none recorded.", "- Blockers: an independently recorded change."
            ),
            encoding="utf-8",
        )
        before = self.filesystem_state()
        result = self.run_cli(request)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stderr)["category"], "PREWRITE_SAFE")
        self.assertEqual(self.filesystem_state(), before)

    def test_inspect_fails_closed_while_runtime_directory_lock_is_held(self) -> None:
        fd = os.open(self.memory, os.O_RDONLY | os.O_DIRECTORY)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            before = self.filesystem_state()
            result = self.inspect_cli()
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(self.filesystem_state(), before)
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)

    def test_inspect_distinguishes_uninitialized_partial_and_unsafe_projects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "empty"
            root.mkdir()
            result = subprocess.run(
                [sys.executable, str(CLI), "inspect", "--project-root", str(root)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), {"active": None, "initialized": False})

            memory = root / "docs/teamwork"
            memory.mkdir(parents=True)
            (memory / "index.json").write_text("{}\n", encoding="utf-8")
            partial = subprocess.run(
                [sys.executable, str(CLI), "inspect", "--project-root", str(root)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(partial.returncode, 0)
            self.assertEqual(json.loads(partial.stderr)["category"], "PREWRITE_SAFE")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "unsafe"
            root.mkdir()
            outside = Path(tmp) / "outside"
            outside.mkdir()
            (root / "docs").symlink_to(outside)
            unsafe = subprocess.run(
                [sys.executable, str(CLI), "inspect", "--project-root", str(root)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(unsafe.returncode, 0)
            self.assertEqual(json.loads(unsafe.stderr)["category"], "PREWRITE_SAFE")

    def test_rejects_unsafe_canonical_nodes(self) -> None:
        spec = self.spec("create")
        original_index = self.memory / "index.json"
        outside = Path(self.temporary.name) / "outside-index.json"
        outside.write_bytes(original_index.read_bytes())
        original_index.unlink()
        original_index.symlink_to(outside)
        before = self.filesystem_state()
        result = self.run_cli(spec)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stderr)["category"], "PREWRITE_SAFE")
        self.assertEqual(self.filesystem_state(), before)

    def test_rejects_hardlinked_anchor_and_symlink_spec_file(self) -> None:
        spec = self.spec("create")
        hardlink = Path(self.temporary.name) / "current-hardlink.md"
        os.link(self.memory / "current.md", hardlink)
        before = self.filesystem_state()
        result = self.run_cli(spec)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stderr)["category"], "PREWRITE_SAFE")
        self.assertEqual(self.filesystem_state(), before)

        hardlink.unlink()
        real_spec = Path(self.temporary.name) / "spec.json"
        real_spec.write_text(json.dumps(spec), encoding="utf-8")
        linked_spec = Path(self.temporary.name) / "spec-link.json"
        linked_spec.symlink_to(real_spec)
        before = self.filesystem_state()
        result = self.run_cli({}, spec_file=linked_spec)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stderr)["category"], "PREWRITE_SAFE")
        self.assertEqual(self.filesystem_state(), before)

    def test_malformed_spec_and_artifact_fail_without_writes(self) -> None:
        before = self.filesystem_state()
        malformed_json = self.run_cli("{not json")
        self.assertNotEqual(malformed_json.returncode, 0)
        self.assertEqual(json.loads(malformed_json.stderr)["category"], "PREWRITE_SAFE")
        self.assertEqual(self.filesystem_state(), before)

        spec = self.spec("create")
        spec["record"]["unknown"] = "rejected"
        malformed_artifact = self.run_cli(spec)
        self.assertNotEqual(malformed_artifact.returncode, 0)
        self.assertEqual(self.filesystem_state(), before)

    def test_rejects_caller_authored_outputs_unknown_fields_controls_and_oversize(self) -> None:
        before = self.filesystem_state()
        for mutation in ("artifact_text", "artifact_path", "entry"):
            with self.subTest(field=mutation):
                request = self.spec("create")
                request[mutation] = "caller-controlled"
                result = self.run_cli(request)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(json.loads(result.stderr)["category"], "PREWRITE_SAFE")
                self.assertEqual(self.filesystem_state(), before)

        control = self.spec("create")
        control["record"]["title"] = "unsafe\x01title"
        result = self.run_cli(control)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.filesystem_state(), before)

        oversized = "{" + '"padding":"' + ("x" * (130 * 1024)) + '"}'
        result = self.run_cli(oversized)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stderr)["category"], "PREWRITE_SAFE")
        self.assertEqual(self.filesystem_state(), before)

    def test_semantic_decision_map_is_rendered_deterministically(self) -> None:
        decision_map = {
            "direction": "LR",
            "nodes": [
                {"id": "A", "label": "Current evidence"},
                {"id": "B", "label": "Chosen wording"},
            ],
            "edges": [{"from": "A", "to": "B", "label": "supports"}],
        }
        result = self.run_cli(self.spec("create", decision_map=decision_map))
        self.assertEqual(result.returncode, 0, result.stderr)
        artifact = (self.project / ARTIFACT).read_text(encoding="utf-8")
        self.assertIn(
            '## Decision map\n\n```mermaid\nflowchart LR\n    A["Current evidence"]\n'
            '    B["Chosen wording"]\n    A -->|supports| B\n```',
            artifact,
        )
        self.validate()

    def test_injected_nth_replace_failure_restores_exact_prestate(self) -> None:
        before = self.filesystem_state()
        for nth in range(1, 8):
            with self.subTest(nth=nth):
                result = self.run_cli(
                    self.spec("create"),
                    env={"TEAMWORK_DISCUSSION_TRANSACTION_FAIL_REPLACE_N": str(nth)},
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(json.loads(result.stderr)["category"], "ROLLED_BACK")
                self.assertEqual(self.filesystem_state(), before)

    def test_machine_error_categories_cover_safe_rollback_and_indeterminate(self) -> None:
        before = self.filesystem_state()
        rolled_back = self.run_cli(
            self.spec("create"),
            env={"TEAMWORK_DISCUSSION_TRANSACTION_FAIL_REPLACE_N": "1"},
        )
        self.assertNotEqual(rolled_back.returncode, 0)
        self.assertEqual(json.loads(rolled_back.stderr)["category"], "ROLLED_BACK")
        self.assertEqual(self.filesystem_state(), before)

        indeterminate = self.run_cli(
            self.spec("create"),
            env={
                "TEAMWORK_DISCUSSION_TRANSACTION_FAIL_REPLACE_N": "1",
                "TEAMWORK_DISCUSSION_TRANSACTION_FAIL_ROLLBACK_CONFIRM_N": "1",
            },
        )
        self.assertNotEqual(indeterminate.returncode, 0)
        self.assertEqual(json.loads(indeterminate.stderr)["category"], "INDETERMINATE")
        self.assertTrue((self.memory / ".discussion-transaction.json").is_file())

    def assert_rollback_fsync_failure_is_fail_closed(self, nth: int) -> None:
        before = self.filesystem_state()
        result = self.run_cli(
            self.spec("create"),
            env={
                "TEAMWORK_DISCUSSION_TRANSACTION_FAIL_POST_READBACK_N": "1",
                "TEAMWORK_DISCUSSION_TRANSACTION_FAIL_ROLLBACK_FSYNC_N": str(nth),
            },
        )

        self.assertNotEqual(result.returncode, 0)
        error = json.loads(result.stderr)
        self.assertEqual(error["category"], "INDETERMINATE")
        self.assertIn("rollback operations failed", error["message"])
        marker = self.memory / ".discussion-transaction.json"
        self.assertTrue(marker.is_file())
        after = self.filesystem_state()
        after.pop("docs/teamwork/.discussion-transaction.json")
        self.assertEqual(after, before)
        inspected = self.inspect_cli()
        self.assertNotEqual(inspected.returncode, 0)
        self.assertEqual(json.loads(inspected.stderr)["category"], "INDETERMINATE")

    def test_discussion_parent_rollback_fsync_failure_retains_marker(self) -> None:
        self.assert_rollback_fsync_failure_is_fail_closed(1)

    def test_teamwork_parent_rollback_fsync_failure_retains_marker(self) -> None:
        self.assert_rollback_fsync_failure_is_fail_closed(2)

    def test_injected_stage_fsync_backup_cleanup_and_readback_failures_restore_prestate(self) -> None:
        cases = (
            ("STAGE", range(1, 5)),
            ("FSYNC", range(1, 7)),
            ("BACKUP", range(1, 4)),
            ("CLEANUP", range(1, 4)),
            ("POST_READBACK", range(1, 2)),
        )
        before = self.filesystem_state()
        for kind, positions in cases:
            for nth in positions:
                with self.subTest(kind=kind, nth=nth):
                    result = self.run_cli(
                        self.spec("create"),
                        env={f"TEAMWORK_DISCUSSION_TRANSACTION_FAIL_{kind}_N": str(nth)},
                    )
                    self.assertNotEqual(result.returncode, 0, result.stdout)
                    self.assertEqual(self.filesystem_state(), before)

    def test_validator_parity_rejects_malformed_profiles(self) -> None:
        index = self.load_index()
        index["profiles"] = []
        (self.memory / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")

        helper = self.inspect_cli()
        validator = subprocess.run(
            [sys.executable, str(VALIDATOR), str(self.memory / "index.json")],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertNotEqual(helper.returncode, 0)
        self.assertNotEqual(validator.returncode, 0)
        self.assertEqual(json.loads(helper.stderr)["category"], "PREWRITE_SAFE")

    def test_validator_parity_rejects_malformed_optional_decision_map(self) -> None:
        self.activate_fixture()
        artifact = self.project / ARTIFACT
        artifact.write_text(
            artifact.read_text(encoding="utf-8")
            + "\n## Decision map\n\n```mermaid\nsequenceDiagram\nA->>B: invalid shape\n```\n",
            encoding="utf-8",
        )

        helper = self.inspect_cli()
        validator = subprocess.run(
            [sys.executable, str(VALIDATOR), str(self.memory / "index.json")],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertNotEqual(helper.returncode, 0)
        self.assertNotEqual(validator.returncode, 0)
        self.assertEqual(json.loads(helper.stderr)["category"], "PREWRITE_SAFE")

    def test_validator_parity_rejects_actual_project_root_current_and_calendar_gaps(self) -> None:
        mutations = (
            ("project-root", lambda index: index["project"].__setitem__("root", "src")),
            ("active-current", lambda index: index["active"].__setitem__("current", "docs/other.md")),
        )
        for label, mutate in mutations:
            with self.subTest(label=label):
                index = self.load_index()
                mutate(index)
                (self.memory / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
                before = self.filesystem_state()
                helper = self.inspect_cli()
                self.assertNotEqual(helper.returncode, 0)
                self.assertEqual(json.loads(helper.stderr)["category"], "PREWRITE_SAFE")
                self.assert_formal_invalid(index)
                self.assertEqual(self.filesystem_state(), before)
                self.write_index([copy.deepcopy(self.initial_entry)], active=None)

        self.activate_fixture()
        invalid_path = "docs/teamwork/discussion/2026-02-31-output-wording.md"
        (self.project / ARTIFACT).rename(self.project / invalid_path)
        index = self.load_index()
        index["active"]["discussion"] = invalid_path
        index["entries"][-1]["path"] = invalid_path
        (self.memory / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
        current = (self.memory / "current.md").read_text(encoding="utf-8").replace(ARTIFACT, invalid_path)
        readme = (self.memory / "README.md").read_text(encoding="utf-8").replace(ARTIFACT, invalid_path)
        (self.memory / "current.md").write_text(current, encoding="utf-8")
        (self.memory / "README.md").write_text(readme, encoding="utf-8")
        helper = self.inspect_cli()
        self.assertNotEqual(helper.returncode, 0)
        self.assertEqual(json.loads(helper.stderr)["category"], "PREWRITE_SAFE")
        self.assert_formal_invalid(index)

    def test_validator_parity_rejects_placeholder_header_h1_and_required_section(self) -> None:
        self.activate_fixture()
        artifact = self.project / ARTIFACT
        original = artifact.read_text(encoding="utf-8")
        variants = {
            "header": original.replace(
                "Abstract: Tracks the remaining evidence-order decision.",
                "Abstract: <abstract>",
            ),
            "h1": original.replace(
                "# Researcher-facing output wording",
                "# <title>",
            ),
            "section": original.replace(
                "Keep replies concise and decision-relevant.",
                "<goal>",
            ),
        }
        for label, malformed in variants.items():
            with self.subTest(label=label):
                artifact.write_text(malformed, encoding="utf-8")
                helper = self.inspect_cli()
                self.assertNotEqual(helper.returncode, 0)
                self.assertEqual(json.loads(helper.stderr)["category"], "PREWRITE_SAFE")
                self.assert_formal_invalid(self.load_index())
        artifact.write_text(original, encoding="utf-8")

    def test_stage_collision_preserves_other_process_file(self) -> None:
        discussion = self.memory / "discussion"
        discussion.mkdir()
        collision = discussion / ".2026-07-15-output-wording.md.discussion-stage-collision"
        collision.write_text("other-owner\n", encoding="utf-8")
        request = self.spec("create")
        before = self.filesystem_state()
        result = self.run_cli(
            request,
            env={"TEAMWORK_DISCUSSION_TRANSACTION_TEST_NAME_TOKEN": "collision"},
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stderr)["category"], "PREWRITE_SAFE")
        self.assertEqual(collision.read_text(encoding="utf-8"), "other-owner\n")
        self.assertEqual(self.filesystem_state(), before)

    def test_concurrent_absent_target_is_preserved_and_reported_indeterminate(self) -> None:
        (self.memory / "discussion").mkdir()
        request = self.spec("create")
        result = self.run_cli(
            request,
            env={"TEAMWORK_DISCUSSION_TRANSACTION_CONCURRENT_TARGET": ARTIFACT},
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stderr)["category"], "INDETERMINATE")
        self.assertEqual((self.project / ARTIFACT).read_text(encoding="utf-8"), "concurrent-owner\n")
        self.assertTrue((self.memory / ".discussion-transaction.json").is_file())
        inspect = self.inspect_cli()
        self.assertNotEqual(inspect.returncode, 0)
        self.assertEqual(json.loads(inspect.stderr)["category"], "INDETERMINATE")

    def test_namespace_exchange_during_commit_is_indeterminate(self) -> None:
        self.activate_fixture()
        result = self.run_cli(
            self.spec("update"),
            env={"TEAMWORK_DISCUSSION_TRANSACTION_EXCHANGE_AT": "discussion_commit"},
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stderr)["category"], "INDETERMINATE")
        self.assertTrue((self.memory / ".discussion-transaction.json").is_file())

    def test_namespace_exchange_during_readback_is_indeterminate(self) -> None:
        self.activate_fixture()
        result = self.run_cli(
            self.spec("update"),
            env={"TEAMWORK_DISCUSSION_TRANSACTION_EXCHANGE_AT": "teamwork_readback"},
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stderr)["category"], "INDETERMINATE")

    def test_interruption_after_index_backup_leaves_durable_marker_and_blocks_inspect(self) -> None:
        result = self.run_cli(
            self.spec("create"),
            env={"TEAMWORK_DISCUSSION_TRANSACTION_INTERRUPT_AFTER_INDEX_BACKUP": "1"},
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stderr)["category"], "INDETERMINATE")
        marker = self.memory / ".discussion-transaction.json"
        self.assertTrue(marker.is_file())
        marker_data = json.loads(marker.read_text(encoding="utf-8"))
        self.assertEqual(marker_data["operation"], "create")
        self.assertIn("docs/teamwork/index.json", marker_data["outputs"])
        inspect = self.inspect_cli()
        self.assertNotEqual(inspect.returncode, 0)
        self.assertEqual(json.loads(inspect.stderr)["category"], "INDETERMINATE")

    def test_unfinished_init_marker_blocks_discussion_inspect_and_apply(self) -> None:
        request = self.spec("create")
        (self.memory / ".teamwork-init-transaction.json").write_text("{}\n", encoding="utf-8")

        inspect = self.inspect_cli()
        apply = self.run_cli(request)

        self.assertNotEqual(inspect.returncode, 0)
        self.assertEqual(json.loads(inspect.stderr)["category"], "INDETERMINATE")
        self.assertNotEqual(apply.returncode, 0)
        self.assertEqual(json.loads(apply.stderr)["category"], "INDETERMINATE")


if __name__ == "__main__":
    unittest.main()
