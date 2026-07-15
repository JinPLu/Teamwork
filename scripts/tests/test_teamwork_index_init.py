import copy
import fcntl
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "skills/using-teamwork/references/teamwork-index-template.json"
VALIDATOR = ROOT / "scripts/validate_teamwork_index.py"
INIT = ROOT / "scripts/init-project.sh"
INSTALL = ROOT / "install.sh"
PROFILE = ROOT / ".teamwork-profile"


class TeamworkIndexBudgetCompatibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.template = json.loads(TEMPLATE.read_text(encoding="utf-8"))

    def validate(self, data: dict) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.json"
            path.write_text(json.dumps(data) + "\n", encoding="utf-8")
            return subprocess.run(
                ["python3", str(VALIDATOR), str(path)],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

    def test_legacy_valid(self) -> None:
        fixture = copy.deepcopy(self.template)
        fixture["budgets"] = {
            "default_max_files": 5,
            "default_max_artifact_bodies": 2,
            "header_first": True,
        }
        result = self.validate(fixture)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_header_only_valid(self) -> None:
        result = self.validate(self.template)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_partial_invalid(self) -> None:
        fixture = copy.deepcopy(self.template)
        fixture["budgets"] = {"default_max_files": 5, "header_first": True}
        result = self.validate(fixture)
        self.assertNotEqual(result.returncode, 0)

    def test_wrong_hybrid_invalid(self) -> None:
        fixture = copy.deepcopy(self.template)
        fixture["budgets"] = {
            "default_max_files": 5,
            "default_max_artifact_bodies": 2,
            "header_first": True,
            "max_tokens": 1000,
        }
        result = self.validate(fixture)
        self.assertNotEqual(result.returncode, 0)


class TeamworkInitPreservationTests(unittest.TestCase):
    def run_init(
        self,
        project: Path,
        home: Path,
        extra_env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.update(
            {
                "HOME": str(home),
                "TEAMWORK_INIT_CODEGRAPH": "0",
                "TEAMWORK_INIT_CURSOR_POLICY_COPY": "0",
            }
        )
        if extra_env:
            env.update(extra_env)
        return subprocess.run(
            [
                str(INIT),
                "--copy",
                "--no-codegraph",
                "--no-cursor-policy-copy",
                "--project-root",
                str(project),
            ],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def filesystem_state(self, root: Path) -> dict[str, tuple[object, ...]]:
        state: dict[str, tuple[object, ...]] = {}
        for path in sorted((root, *root.rglob("*")), key=lambda item: str(item)):
            relative = "." if path == root else path.relative_to(root).as_posix()
            mode = path.lstat().st_mode
            if path.is_symlink():
                state[relative] = ("symlink", mode, os.readlink(path))
            elif path.is_file():
                state[relative] = ("file", mode, path.read_bytes())
            elif path.is_dir():
                state[relative] = ("directory", mode)
            else:
                state[relative] = ("other", mode)
        return state

    def test_direct_init_uses_default_copy_mode_when_flag_is_omitted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            project = base / "project"
            home = base / "home"
            project.mkdir()
            home.mkdir()
            env = os.environ.copy()
            env.update(
                {
                    "HOME": str(home),
                    "TEAMWORK_INIT_CODEGRAPH": "0",
                    "TEAMWORK_INIT_CURSOR_POLICY_COPY": "0",
                }
            )
            result = subprocess.run(
                [
                    str(INIT),
                    "--no-codegraph",
                    "--no-cursor-policy-copy",
                    "--project-root",
                    str(project),
                ],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((project / "docs/teamwork/index.json").is_file())

    def test_install_entry_does_not_write_profile_before_project_preflight(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            project = base / "project"
            home = base / "home"
            project.mkdir()
            home.mkdir()
            (project / ".gitignore").mkdir()
            before_profile = PROFILE.read_bytes() if PROFILE.exists() else None

            env = os.environ.copy()
            env.update(
                {
                    "HOME": str(home),
                    "TEAMWORK_INIT_CODEGRAPH": "0",
                    "TEAMWORK_INIT_CURSOR_POLICY_COPY": "0",
                }
            )
            result = subprocess.run(
                [
                    str(INSTALL),
                    "--profile",
                    "cost-first",
                    "--project-root",
                    str(project),
                    "--no-notifications",
                    "init-project",
                ],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            after_profile = PROFILE.read_bytes() if PROFILE.exists() else None
            self.assertEqual(after_profile, before_profile)
            self.assertEqual(list(home.iterdir()), [])

    def test_global_install_failure_still_initializes_project_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            project = base / "project"
            home = base / "home"
            project.mkdir()
            home.mkdir()
            (home / ".codex").write_text("blocks Codex install\n", encoding="utf-8")

            result = self.run_init(project, home)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("continuing with project context setup", result.stderr)
            self.assertTrue((project / "AGENTS.md").is_file())
            self.assertTrue((project / "docs/teamwork/index.json").is_file())
            self.assertIn("global setup still requires repair", result.stderr)

    def test_codegraph_failure_is_nonfatal_and_context_is_written(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            project = base / "project"
            home = base / "home"
            bin_dir = base / "bin"
            project.mkdir()
            home.mkdir()
            bin_dir.mkdir()
            codegraph = bin_dir / "codegraph"
            codegraph.write_text("#!/usr/bin/env bash\nexit 23\n", encoding="utf-8")
            codegraph.chmod(0o755)
            env = os.environ.copy()
            env.update(
                {
                    "HOME": str(home),
                    "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
                    "TEAMWORK_INIT_CURSOR_POLICY_COPY": "0",
                }
            )

            result = subprocess.run(
                [
                    str(INIT),
                    "--copy",
                    "--no-cursor-policy-copy",
                    "--project-root",
                    str(project),
                ],
                cwd=ROOT,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("CodeGraph: init failed; continuing", result.stdout)
            self.assertTrue((project / "AGENTS.md").is_file())
            self.assertTrue((project / "docs/teamwork/index.json").is_file())

    def test_final_runtime_validation_failure_is_fatal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            project = base / "project"
            home = base / "home"
            bin_dir = base / "bin"
            project.mkdir()
            home.mkdir()
            bin_dir.mkdir()
            python_wrapper = bin_dir / "python3"
            python_wrapper.write_text(
                """#!/usr/bin/env bash
if [[ "${1:-}" == */scripts/init-project-files.py && "${2:-}" == validate ]]; then
  exit 17
fi
exec "$TEAMWORK_TEST_REAL_PYTHON" "$@"
""",
                encoding="utf-8",
            )
            python_wrapper.chmod(0o755)

            result = self.run_init(
                project,
                home,
                {
                    "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
                    "TEAMWORK_TEST_REAL_PYTHON": sys.executable,
                },
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Teamwork memory: index invalid", result.stderr)

    def test_new_init_emits_header_only_and_minimal_agents_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            project = base / "project"
            home = base / "home"
            project.mkdir()
            home.mkdir()
            (project / "README.md").write_text("# Local Display Label\n", encoding="utf-8")
            (project / ".gitignore").write_text("# Keep this user rule\n", encoding="utf-8")

            result = self.run_init(project, home)
            self.assertEqual(result.returncode, 0, result.stderr)

            index = json.loads((project / "docs/teamwork/index.json").read_text(encoding="utf-8"))
            self.assertEqual(index["budgets"], {"header_first": True})
            self.assertEqual(index["project"]["name"], "Local Display Label")
            self.assertEqual(index["project"]["description"], "Local Teamwork memory index for this project.")

            agents = (project / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("Project label (local routing only): `Local Display Label`", agents)
            self.assertIn("For Grill/discussion continuation, load `grill-me`", agents)
            self.assertIn("run `inspect` from the project root", agents)
            self.assertIn("sole discussion read path", agents)
            self.assertIn("do not directly read `index.json`", agents)
            self.assertIn("Ordinary non-discussion memory reads", agents)

            runtime_readme = (project / "docs/teamwork/README.md").read_text(encoding="utf-8")
            normalized_runtime_readme = " ".join(runtime_readme.split())
            self.assertIn("For Grill/discussion continuation, load `grill-me`", runtime_readme)
            self.assertIn("run `inspect` from the project root", runtime_readme)
            self.assertIn("sole discussion read path", normalized_runtime_readme)
            self.assertIn("do not directly read `index.json`", normalized_runtime_readme)
            self.assertIn("For ordinary non-discussion memory", runtime_readme)
            for unsafe_discussion_read in (
                "Follow `active.current`, then `active.discussion`",
                "read the active discussion before continuing dependent work",
            ):
                self.assertNotIn(unsafe_discussion_read, agents)
                self.assertNotIn(unsafe_discussion_read, runtime_readme)
            for unsupported in (
                "Project identity:",
                "CodeGraph:",
                "Docs MCP:",
                "Required values, credentials",
                "Keep volatile task progress",
            ):
                self.assertNotIn(unsupported, agents)

            gitignore = (project / ".gitignore").read_text(encoding="utf-8")
            self.assertIn("# Keep this user rule", gitignore)
            for local_package_path in (".agents/", ".codex/", ".cursor/", ".claude/"):
                self.assertNotIn(local_package_path, gitignore)
            for local_package_path in (
                project / ".agents",
                project / ".codex" / "agents",
                project / ".cursor" / "skills",
                project / ".claude" / "skills",
            ):
                self.assertFalse(local_package_path.exists(), local_package_path)

    def test_existing_index_byte_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            project = base / "project"
            memory = project / "docs/teamwork"
            home = base / "home"
            memory.mkdir(parents=True)
            home.mkdir()

            index_bytes = TEMPLATE.read_bytes()
            readme_bytes = (
                b"# Existing runtime README\n\n"
                b"- Active discussion route: none\n\n"
                b"Keep these exact bytes.\n"
            )
            current_bytes = (
                b"# Existing current state\n\n"
                b"- Active discussion: none.\n\n"
                b"Keep these exact bytes.\n"
            )
            (memory / "index.json").write_bytes(index_bytes)
            (memory / "README.md").write_bytes(readme_bytes)
            (memory / "current.md").write_bytes(current_bytes)

            result = self.run_init(project, home)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((memory / "index.json").read_bytes(), index_bytes)
            self.assertEqual((memory / "README.md").read_bytes(), readme_bytes)
            self.assertEqual((memory / "current.md").read_bytes(), current_bytes)

    def test_discussion_transaction_marker_refuses_init_before_any_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            project = base / "project"
            memory = project / "docs/teamwork"
            home = base / "home"
            memory.mkdir(parents=True)
            home.mkdir()

            (memory / "index.json").write_bytes(TEMPLATE.read_bytes())
            (memory / "current.md").write_text(
                "# Existing current\n\n- Active discussion: none.\n",
                encoding="utf-8",
            )
            (memory / "README.md").write_text(
                """# Existing runtime README

## Read Order

1. Read `docs/teamwork/index.json` first.
2. Follow `active.current`, then `active.discussion` when present, then the other `active` pointers before any broad scan.
3. Prefer headers before full artifact bodies.
4. Use stage-specific profiles from the index.

## Stage Notes

- `discussion`: read the active discussion before continuing dependent work.

- Active discussion route: none
""",
                encoding="utf-8",
            )
            (memory / ".discussion-transaction.json").write_text(
                '{"operation":"update","phase":"commit"}\n',
                encoding="utf-8",
            )
            before = self.filesystem_state(base)

            result = self.run_init(project, home)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unfinished discussion transaction marker", result.stderr)
            self.assertEqual(self.filesystem_state(base), before)

    def test_full_init_recovers_hard_exit_journal_before_continuing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            project = base / "project"
            home = base / "home"
            project.mkdir()
            home.mkdir()
            (project / "README.md").write_text("# Recovery Fixture\n", encoding="utf-8")

            interrupted = self.run_init(
                project,
                home,
                {"TEAMWORK_TEST_HARD_EXIT_INIT_REPLACE_AT": "2"},
            )
            self.assertNotEqual(interrupted.returncode, 0)
            marker = project / "docs/teamwork/.teamwork-init-transaction.json"
            self.assertTrue(marker.is_file())

            recovered = self.run_init(project, home)

            self.assertEqual(recovered.returncode, 0, recovered.stderr)
            self.assertFalse(marker.exists())
            self.assertTrue((project / "docs/teamwork/index.json").is_file())
            self.assertTrue((project / "AGENTS.md").is_file())
            self.assertEqual(
                [path for path in project.rglob("*") if ".teamwork-init-" in path.name],
                [],
            )

    def test_full_init_migration_interrupts_before_home_write_then_recovers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            project = base / "project"
            home = base / "home"
            project.mkdir()
            home.mkdir()
            first = self.run_init(project, home)
            self.assertEqual(first.returncode, 0, first.stderr)
            memory = project / "docs/teamwork"
            index_path = memory / "index.json"
            index = json.loads(index_path.read_text(encoding="utf-8"))
            del index["active"]["discussion"]
            index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
            current = memory / "current.md"
            current.write_text(
                current.read_text(encoding="utf-8").replace("- Active discussion: none.\n", ""),
                encoding="utf-8",
            )
            readme = memory / "README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8").replace("- Active discussion route: none\n", ""),
                encoding="utf-8",
            )
            home_before = self.filesystem_state(home)

            interrupted = self.run_init(
                project,
                home,
                {"TEAMWORK_TEST_HARD_EXIT_MIGRATION_REPLACE_AT": "2"},
            )
            self.assertNotEqual(interrupted.returncode, 0)
            self.assertEqual(self.filesystem_state(home), home_before)
            self.assertTrue((memory / ".teamwork-init-transaction.json").is_file())

            recovered = self.run_init(project, home)
            self.assertEqual(recovered.returncode, 0, recovered.stderr)
            self.assertFalse((memory / ".teamwork-init-transaction.json").exists())
            self.assertEqual(
                [path for path in project.rglob("*") if ".teamwork-init-" in path.name],
                [],
            )

    def test_discussion_marker_blocks_init_journal_recovery_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            project = base / "project"
            home = base / "home"
            project.mkdir()
            home.mkdir()
            interrupted = self.run_init(
                project,
                home,
                {"TEAMWORK_TEST_HARD_EXIT_INIT_REPLACE_AT": "1"},
            )
            self.assertNotEqual(interrupted.returncode, 0)
            memory = project / "docs/teamwork"
            (memory / ".discussion-transaction.json").write_text(
                '{"operation":"update","phase":"commit"}\n',
                encoding="utf-8",
            )
            before = self.filesystem_state(base)

            refused = self.run_init(project, home)

            self.assertNotEqual(refused.returncode, 0)
            self.assertIn("unfinished discussion transaction marker", refused.stderr)
            self.assertEqual(self.filesystem_state(base), before)

    def test_discussion_transaction_lock_refuses_init_before_any_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            project = base / "project"
            memory = project / "docs/teamwork"
            home = base / "home"
            memory.mkdir(parents=True)
            home.mkdir()
            (memory / "index.json").write_bytes(TEMPLATE.read_bytes())
            (memory / "current.md").write_text(
                "# Existing current\n\n- Active discussion: none.\n",
                encoding="utf-8",
            )
            (memory / "README.md").write_text(
                "# Existing README\n\n- Active discussion route: none\n",
                encoding="utf-8",
            )
            before = self.filesystem_state(base)

            lock_fd = os.open(memory, os.O_RDONLY | os.O_DIRECTORY)
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                result = self.run_init(project, home)
            finally:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
                os.close(lock_fd)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("cannot acquire Teamwork initialization guard", result.stderr)
            self.assertEqual(self.filesystem_state(base), before)

    def test_inherited_guard_fd_must_own_the_lock_it_claims(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            project = base / "project"
            docs = project / "docs"
            memory = docs / "teamwork"
            home = base / "home"
            memory.mkdir(parents=True)
            home.mkdir()
            (memory / "index.json").write_bytes(TEMPLATE.read_bytes())
            (memory / "current.md").write_text(
                "# Existing current\n\n- Active discussion: none.\n",
                encoding="utf-8",
            )
            (memory / "README.md").write_text(
                "# Existing README\n\n- Active discussion route: none\n",
                encoding="utf-8",
            )
            before = self.filesystem_state(base)

            root_fd = os.open(project, os.O_RDONLY | os.O_DIRECTORY)
            docs_fd = os.open(docs, os.O_RDONLY | os.O_DIRECTORY)
            teamwork_fd = os.open(memory, os.O_RDONLY | os.O_DIRECTORY)
            claimed_lock_fd = os.open(memory, os.O_RDONLY | os.O_DIRECTORY)
            actual_lock_fd = os.open(memory, os.O_RDONLY | os.O_DIRECTORY)
            try:
                fcntl.flock(actual_lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                env = os.environ.copy()
                env.update(
                    {
                        "HOME": str(home),
                        "TEAMWORK_INIT_CODEGRAPH": "0",
                        "TEAMWORK_INIT_CURSOR_POLICY_COPY": "0",
                        "TEAMWORK_DISCUSSION_GUARD_ROOT_FD": str(root_fd),
                        "TEAMWORK_DISCUSSION_GUARD_DOCS_FD": str(docs_fd),
                        "TEAMWORK_DISCUSSION_GUARD_TEAMWORK_FD": str(teamwork_fd),
                        "TEAMWORK_DISCUSSION_GUARD_LOCK_FD": str(claimed_lock_fd),
                        "TEAMWORK_DISCUSSION_GUARD_TOKEN": "a" * 64,
                    }
                )
                result = subprocess.run(
                    [
                        str(INIT),
                        "--copy",
                        "--no-codegraph",
                        "--no-cursor-policy-copy",
                        "--project-root",
                        str(project),
                    ],
                    cwd=ROOT,
                    env=env,
                    pass_fds=(root_fd, docs_fd, teamwork_fd, claimed_lock_fd),
                    text=True,
                    capture_output=True,
                    check=False,
                )
            finally:
                fcntl.flock(actual_lock_fd, fcntl.LOCK_UN)
                for fd in (actual_lock_fd, claimed_lock_fd, teamwork_fd, docs_fd, root_fd):
                    os.close(fd)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("does not own the discussion lock", result.stderr)
            self.assertEqual(self.filesystem_state(base), before)

    def test_legacy_runtime_readme_routing_migrates_once_and_preserves_custom_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            project = base / "project"
            memory = project / "docs/teamwork"
            home = base / "home"
            memory.mkdir(parents=True)
            home.mkdir()

            (memory / "index.json").write_bytes(TEMPLATE.read_bytes())
            (memory / "current.md").write_text(
                "# Existing current\n\n- Active discussion: none.\n",
                encoding="utf-8",
            )
            (memory / "README.md").write_text(
                """# Existing runtime README

Keep this custom introduction.

## Read Order

1. Read `docs/teamwork/index.json` first.
2. Follow `active.current`, then `active.discussion` when present, then the other `active` pointers before any broad scan.
3. Prefer headers before full artifact bodies.
4. Use stage-specific profiles from the index.

## Stage Notes

- `research`: keep this custom research note.
- `discussion`: read the active discussion before continuing dependent work.
- `review`: keep this custom review note.

## Current Anchors

- Active discussion route: none

Keep this custom footer.
""",
                encoding="utf-8",
            )

            result = self.run_init(project, home)
            self.assertEqual(result.returncode, 0, result.stderr)

            migrated = (memory / "README.md").read_text(encoding="utf-8")
            self.assertIn("For Grill/discussion continuation, load `grill-me`", migrated)
            self.assertIn("sole discussion read path", migrated)
            self.assertIn("For ordinary non-discussion memory", migrated)
            self.assertIn("use the helper's `inspect` result", migrated)
            self.assertNotIn("Follow `active.current`, then `active.discussion`", migrated)
            self.assertNotIn("read the active discussion before continuing dependent work", migrated)
            for preserved in (
                "Keep this custom introduction.",
                "- `research`: keep this custom research note.",
                "- `review`: keep this custom review note.",
                "- Active discussion route: none",
                "Keep this custom footer.",
            ):
                self.assertIn(preserved, migrated)

            migrated_bytes = (memory / "README.md").read_bytes()
            result = self.run_init(project, home)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((memory / "README.md").read_bytes(), migrated_bytes)

    def test_customized_legacy_runtime_readme_routing_is_left_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            project = base / "project"
            memory = project / "docs/teamwork"
            home = base / "home"
            memory.mkdir(parents=True)
            home.mkdir()

            (memory / "index.json").write_bytes(TEMPLATE.read_bytes())
            (memory / "current.md").write_text(
                "# Existing current\n\n- Active discussion: none.\n",
                encoding="utf-8",
            )
            customized = """# Customized runtime README

## Read Order

1. Read `docs/teamwork/index.json` first.
2. Follow the project's custom memory route before any broad scan.
3. Prefer headers before full artifact bodies.
4. Use stage-specific profiles from the index.

## Stage Notes

- `discussion`: read the active discussion before continuing dependent work.

- Active discussion route: none
"""
            (memory / "README.md").write_text(customized, encoding="utf-8")

            before = self.filesystem_state(base)
            result = self.run_init(project, home)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "unsupported or customized legacy runtime README retrieval blocks",
                result.stderr,
            )
            self.assertEqual(self.filesystem_state(base), before)

    def test_legacy_runtime_memory_is_migrated_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            project = base / "project"
            memory = project / "docs/teamwork"
            home = base / "home"
            memory.mkdir(parents=True)
            home.mkdir()

            legacy_index = json.loads(TEMPLATE.read_text(encoding="utf-8"))
            legacy_index["active"].pop("discussion")
            (memory / "index.json").write_text(
                json.dumps(legacy_index, indent=2) + "\n",
                encoding="utf-8",
            )
            (memory / "README.md").write_text(
                "# Existing runtime README\n\nKeep this README content.\n",
                encoding="utf-8",
            )
            (memory / "current.md").write_text(
                "# Existing current state\n\nKeep this current-state content.\n",
                encoding="utf-8",
            )

            result = self.run_init(project, home)
            self.assertEqual(result.returncode, 0, result.stderr)

            migrated_index = json.loads((memory / "index.json").read_text(encoding="utf-8"))
            self.assertIsNone(migrated_index["active"]["discussion"])

            readme = (memory / "README.md").read_text(encoding="utf-8")
            current = (memory / "current.md").read_text(encoding="utf-8")
            self.assertEqual(readme.count("- Active discussion route: none"), 1)
            self.assertEqual(current.count("- Active discussion: none."), 1)
            self.assertIn("Keep this README content.", readme)
            self.assertIn("Keep this current-state content.", current)
            self.assertFalse((memory / "discussion").exists())

            migrated_bytes = {
                name: (memory / name).read_bytes()
                for name in ("index.json", "README.md", "current.md")
            }
            result = self.run_init(project, home)
            self.assertEqual(result.returncode, 0, result.stderr)
            for name, expected in migrated_bytes.items():
                self.assertEqual((memory / name).read_bytes(), expected, name)

    def test_symlinked_runtime_paths_fail_before_any_project_write(self) -> None:
        protected_paths = (
            "docs",
            "docs/teamwork",
            "docs/teamwork/research",
            "docs/teamwork/plans",
            "docs/teamwork/reports",
            "docs/teamwork/workflows",
            "docs/teamwork/discussion",
            "docs/teamwork/index.json",
            "docs/teamwork/current.md",
            "docs/teamwork/README.md",
        )
        for relative in protected_paths:
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as tmp:
                base = Path(tmp).resolve()
                project = base / "project"
                home = base / "home"
                external = base / "external"
                project.mkdir()
                home.mkdir()
                external.mkdir()

                link = project / relative
                link.parent.mkdir(parents=True, exist_ok=True)
                if Path(relative).suffix:
                    target = external / "protected-file"
                    target.write_bytes(b"external bytes must not change\n")
                else:
                    target = external / "protected-directory"
                    target.mkdir()
                    (target / "sentinel").write_bytes(b"external bytes must not change\n")
                link.symlink_to(target, target_is_directory=target.is_dir())

                before = {
                    path.relative_to(base): path.read_bytes()
                    for path in external.rglob("*")
                    if path.is_file()
                }
                result = self.run_init(project, home)
                self.assertNotEqual(result.returncode, 0)
                self.assertRegex(
                    result.stderr,
                    r"(?:non-symlink directory|single-link regular file)",
                )
                after = {
                    path.relative_to(base): path.read_bytes()
                    for path in external.rglob("*")
                    if path.is_file()
                }
                self.assertEqual(after, before)
                self.assertFalse((project / "AGENTS.md").exists())
                self.assertFalse((project / ".gitignore").exists())
                self.assertEqual(list(home.iterdir()), [])

    def test_symlinked_discussion_artifact_fails_before_any_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            project = base / "project"
            home = base / "home"
            discussion = project / "docs/teamwork/discussion"
            external = base / "external-discussion.md"
            discussion.mkdir(parents=True)
            home.mkdir()
            external.write_bytes(b"external discussion bytes must not change\n")
            (discussion / "2026-06-01-external.md").symlink_to(external)

            result = self.run_init(project, home)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("non-symlink regular file", result.stderr)
            self.assertEqual(external.read_bytes(), b"external discussion bytes must not change\n")
            self.assertFalse((project / "AGENTS.md").exists())
            self.assertFalse((project / ".gitignore").exists())
            self.assertFalse((project / "docs/teamwork/index.json").exists())
            self.assertEqual(list(home.iterdir()), [])

    def test_symlinked_project_output_targets_fail_before_any_write(self) -> None:
        for name in ("AGENTS.md", ".gitignore"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                base = Path(tmp).resolve()
                project = base / "project"
                home = base / "home"
                external = base / f"external-{name.lstrip('.')}"
                project.mkdir()
                home.mkdir()
                external.write_bytes(b"external target bytes must not change\n")
                (project / name).symlink_to(external)

                result = self.run_init(project, home)

                self.assertNotEqual(result.returncode, 0)
                self.assertIn("project output must be a single-link regular file", result.stderr)
                self.assertEqual(external.read_bytes(), b"external target bytes must not change\n")
                self.assertTrue((project / "docs/teamwork").is_dir())
                self.assertEqual(list(home.iterdir()), [])

    def test_project_root_symlink_ancestor_fails_before_any_write(self) -> None:
        for source in ("argument", "default-pwd"):
            with self.subTest(source=source), tempfile.TemporaryDirectory() as tmp:
                base = Path(tmp).resolve()
                external = base / "external"
                real_project = external / "project"
                parent_link = base / "parent-link"
                project_via_link = parent_link / "project"
                home = base / "home"
                real_project.mkdir(parents=True)
                home.mkdir()
                (real_project / "sentinel.txt").write_bytes(
                    b"external project bytes must not change\n"
                )
                parent_link.symlink_to(external, target_is_directory=True)
                before = self.filesystem_state(base)

                if source == "argument":
                    result = self.run_init(project_via_link, home)
                else:
                    env = os.environ.copy()
                    env.update(
                        {
                            "HOME": str(home),
                            "PWD": str(project_via_link),
                            "TEAMWORK_INIT_CODEGRAPH": "0",
                            "TEAMWORK_INIT_CURSOR_POLICY_COPY": "0",
                        }
                    )
                    result = subprocess.run(
                        [str(INIT), "--copy", "--no-codegraph", "--no-cursor-policy-copy"],
                        cwd=project_via_link,
                        env=env,
                        text=True,
                        capture_output=True,
                        check=False,
                    )

                self.assertNotEqual(result.returncode, 0)
                self.assertIn("refusing symlinked Teamwork project-root component", result.stderr)
                self.assertEqual(self.filesystem_state(base), before)

    def test_nonregular_project_output_targets_fail_before_any_write(self) -> None:
        for name, kind in (("AGENTS.md", "directory"), (".gitignore", "fifo")):
            with self.subTest(name=name, kind=kind), tempfile.TemporaryDirectory() as tmp:
                base = Path(tmp).resolve()
                project = base / "project"
                home = base / "home"
                project.mkdir()
                home.mkdir()
                target = project / name
                if kind == "directory":
                    target.mkdir()
                else:
                    os.mkfifo(target)

                result = self.run_init(project, home)

                self.assertNotEqual(result.returncode, 0)
                self.assertIn("project output must be a single-link regular file", result.stderr)
                if kind == "directory":
                    self.assertTrue(target.is_dir())
                else:
                    self.assertTrue(target.exists())
                    self.assertFalse(target.is_file())
                self.assertTrue((project / "docs/teamwork").is_dir())
                self.assertEqual(list(home.iterdir()), [])

    def test_wrong_runtime_path_types_fail_before_any_write(self) -> None:
        cases = (
            ("docs/teamwork/research", "file"),
            ("docs/teamwork/index.json", "directory"),
            ("docs/teamwork/current.md", "fifo"),
            ("docs/teamwork/discussion/2026-06-01-wrong.md", "directory"),
        )
        for relative, kind in cases:
            with self.subTest(relative=relative, kind=kind), tempfile.TemporaryDirectory() as tmp:
                base = Path(tmp).resolve()
                project = base / "project"
                home = base / "home"
                wrong = project / relative
                project.mkdir()
                home.mkdir()
                wrong.parent.mkdir(parents=True, exist_ok=True)
                if kind == "file":
                    wrong.write_bytes(b"wrong type must remain unchanged\n")
                elif kind == "directory":
                    wrong.mkdir()
                else:
                    os.mkfifo(wrong)
                sentinel = project / "sentinel.txt"
                sentinel.write_bytes(b"project bytes must not change\n")

                result = self.run_init(project, home)
                self.assertNotEqual(result.returncode, 0)
                self.assertRegex(
                    result.stderr,
                    r"must be (?:a single-link (?:non-symlink )?regular file|a non-symlink directory)",
                )
                self.assertEqual(sentinel.read_bytes(), b"project bytes must not change\n")
                if kind == "file":
                    self.assertEqual(wrong.read_bytes(), b"wrong type must remain unchanged\n")
                self.assertFalse((project / "AGENTS.md").exists())
                self.assertFalse((project / ".gitignore").exists())
                self.assertEqual(list(home.iterdir()), [])

    def legacy_discussion(self, *, promotion: str = "none") -> str:
        return f"""Artifact Type: discussion
Status: active
Authority: supporting
Last Updated: 2026-06-01
Search Keys: continuity, migration
Abstract: Preserve the chosen route and its recovery point.
Linked Artifacts: none

# Teamwork Discussion

This artifact supports continuity for a long, cross-context, handoff-sensitive,
or materially branching Grill. It is not a transcript and grants no execution
authority.

## Starting Question

- Mainline or project goal: Keep the release decision recoverable.
- Decision: Choose the evidence boundary for release
- Why now: The next session must continue without reopening settled scope.

## Decision State

- Decisions: Keep validation and fresh review.
- Open: Whether the platform smoke adds distinct evidence.
- Rejected: Re-running unrelated evaluations because they do not cover the boundary.
- Evidence: The release contract requires validation and fresh review.
- Resume point: Compare platform smoke coverage with validation.
- Promotion: {promotion}

## Route Map

Show the full material route, including every settled, open, and rejected
branch. Use artifact-local node keys such as `R1`, include textual status in
every node, and keep detailed evidence and outcomes in Decision State rather
than duplicating them here.

```mermaid
flowchart TD
    R1["R1 · Release evidence · current"]
    R2["R2 · Platform smoke · open"]
    R1 --> R2
```

## Textual Playback

Validation and review were settled; only distinct smoke coverage remains open.

## Update Rules

Update only at a material checkpoint: a decision changes or closes a branch,
evidence materially changes a route, the mainline changes, continuity is about
to cross a context or handoff boundary, or the discussion is promoted or
superseded. Do not update per turn. Store decision-relevant, privacy-safe
summaries only; exclude raw transcripts, hidden reasoning, secrets, and
unnecessary personal data. Promotion does not grant execution authority.
"""

    def write_legacy_discussion_runtime(
        self,
        base: Path,
        artifact_text: str,
    ) -> tuple[Path, Path, Path, Path]:
        project = base / "project"
        home = base / "home"
        memory = project / "docs/teamwork"
        discussion = memory / "discussion/2026-06-01-release-evidence.md"
        discussion.parent.mkdir(parents=True)
        home.mkdir()

        discussion_path = "docs/teamwork/discussion/2026-06-01-release-evidence.md"
        index = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        index["active"]["discussion"] = discussion_path
        index["entries"].append(
            {
                "topic": "release-evidence",
                "kind": "discussion",
                "title": "Choose the release evidence boundary",
                "status": "active",
                "currentness": "current",
                "authority": "supporting",
                "path": discussion_path,
                "updated": "2026-06-01",
                "summary": "Preserve the release evidence decision route.",
            }
        )
        (memory / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
        (memory / "README.md").write_text(
            f"# Existing README\n\n- Active discussion route: {discussion_path}\n",
            encoding="utf-8",
        )
        (memory / "current.md").write_text(
            f"# Existing current\n\n- Active discussion: {discussion_path}.\n",
            encoding="utf-8",
        )
        discussion.write_text(artifact_text, encoding="utf-8")
        return project, home, memory, discussion

    def test_unknown_legacy_status_and_route_map_fail_before_any_write(self) -> None:
        mutations = (
            (
                "unknown status",
                lambda text: text.replace("Status: active", "Status: mystery", 1),
                "unknown value",
            ),
            (
                "nonlegacy route map",
                lambda text: text.replace(
                    'R1["R1 · Release evidence · current"]',
                    'release["Release evidence"]',
                    1,
                ),
                "unsupported or malformed legacy discussion artifact",
            ),
        )
        for label, mutate, error in mutations:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as tmp:
                base = Path(tmp).resolve()
                project, home, _, _ = self.write_legacy_discussion_runtime(
                    base,
                    mutate(self.legacy_discussion()),
                )
                before = self.filesystem_state(base)

                result = self.run_init(project, home)

                self.assertNotEqual(result.returncode, 0)
                self.assertIn(error, result.stderr)
                self.assertEqual(self.filesystem_state(base), before)

    def test_later_malformed_legacy_artifact_prevents_all_migration_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            project, home, memory, discussion = self.write_legacy_discussion_runtime(
                base,
                self.legacy_discussion(),
            )
            malformed = memory / "discussion/2026-06-02-malformed.md"
            malformed.write_text(
                self.legacy_discussion().replace("- Promotion: none\n", ""),
                encoding="utf-8",
            )
            before = self.filesystem_state(base)

            result = self.run_init(project, home)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unsupported or malformed legacy discussion artifact", result.stderr)
            self.assertEqual(self.filesystem_state(base), before)
            self.assertIn("# Teamwork Discussion", discussion.read_text(encoding="utf-8"))

    def test_readonly_runtime_file_is_replaced_without_partial_migration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            project, home, memory, discussion = self.write_legacy_discussion_runtime(
                base,
                self.legacy_discussion(),
            )
            current = memory / "current.md"
            current.write_text("# Existing current without an anchor\n", encoding="utf-8")
            current.chmod(0o444)

            result = self.run_init(project, home)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(current.stat().st_mode & 0o777, 0o444)
            self.assertIn(
                "- Active discussion: docs/teamwork/discussion/2026-06-01-release-evidence.md.",
                current.read_text(encoding="utf-8"),
            )
            self.assertIn("# Choose the evidence boundary for release", discussion.read_text(encoding="utf-8"))
            self.assertFalse(list(memory.rglob("*.tmp")))

    def test_second_replace_failure_rolls_back_all_migration_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            project, home, memory, _ = self.write_legacy_discussion_runtime(
                base,
                self.legacy_discussion(),
            )
            current = memory / "current.md"
            current.write_text("# Current state without the legacy anchor\n", encoding="utf-8")
            current.chmod(0o640)
            before = self.filesystem_state(base)

            result = self.run_init(
                project,
                home,
                {"TEAMWORK_TEST_FAIL_MIGRATION_REPLACE_AT": "2"},
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("atomic migration commit failed and was rolled back", result.stderr)
            self.assertEqual(
                self.filesystem_state(base),
                before,
                "a later replacement failure must restore every committed byte and mode",
            )

    def test_matching_legacy_discussion_body_migrates_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            project = base / "project"
            memory = project / "docs/teamwork"
            discussion = memory / "discussion/2026-06-01-release-evidence.md"
            home = base / "home"
            discussion.parent.mkdir(parents=True)
            home.mkdir()

            index = json.loads(TEMPLATE.read_text(encoding="utf-8"))
            index["active"]["discussion"] = "docs/teamwork/discussion/2026-06-01-release-evidence.md"
            index["entries"].append(
                {
                    "topic": "release-evidence",
                    "kind": "discussion",
                    "title": "Choose the release evidence boundary",
                    "status": "active",
                    "currentness": "current",
                    "authority": "supporting",
                    "path": "docs/teamwork/discussion/2026-06-01-release-evidence.md",
                    "updated": "2026-06-01",
                    "summary": "Preserve the release evidence decision route.",
                }
            )
            (memory / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
            (memory / "README.md").write_text(
                "# Existing README\n\n- Active discussion route: docs/teamwork/discussion/2026-06-01-release-evidence.md\n",
                encoding="utf-8",
            )
            (memory / "current.md").write_text(
                "# Existing current\n\n- Active discussion: docs/teamwork/discussion/2026-06-01-release-evidence.md.\n",
                encoding="utf-8",
            )
            discussion.write_text(self.legacy_discussion(), encoding="utf-8")

            result = self.run_init(project, home)
            self.assertEqual(result.returncode, 0, result.stderr)
            migrated = discussion.read_text(encoding="utf-8")
            self.assertIn("Superseded By: none", migrated)
            self.assertIn("# Choose the evidence boundary for release", migrated)
            for heading in ("Goal", "Settled", "Still open", "Key evidence", "Continue here"):
                self.assertEqual(migrated.count(f"## {heading}"), 1)
            for preserved in (
                "Keep the release decision recoverable.",
                "Keep validation and fresh review.",
                "Whether the platform smoke adds distinct evidence.",
                "The release contract requires validation and fresh review.",
                "Compare platform smoke coverage with validation.",
                "Validation and review were settled; only distinct smoke coverage remains open.",
            ):
                self.assertIn(preserved, migrated)
            for retired in (
                "Starting Question",
                "Decision State",
                "Route Map",
                "Textual Playback",
                "Update Rules",
                "Decision map",
                "Mainline or project goal:",
                "Decision:",
                "Decisions:",
                "Rejected:",
                "Evidence:",
                "Promotion:",
                "Legacy textual playback",
                "flowchart TD",
                "Update only when the evidence boundary changes.",
            ):
                self.assertNotIn(retired, migrated)
            self.assertNotIn("Promote this discussion", migrated)
            validation = subprocess.run(
                ["python3", str(VALIDATOR), str(memory / "index.json")],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(validation.returncode, 0, validation.stderr)

            first_bytes = discussion.read_bytes()
            result = self.run_init(project, home)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(discussion.read_bytes(), first_bytes)

            discussion.write_text(
                self.legacy_discussion(
                    promotion="docs/teamwork/plans/release.md when the evidence boundary is settled"
                ),
                encoding="utf-8",
            )
            result = self.run_init(project, home)
            self.assertEqual(result.returncode, 0, result.stderr)
            promoted = discussion.read_text(encoding="utf-8")
            self.assertIn(
                "The settled result continues in docs/teamwork/plans/release.md when the evidence boundary is settled",
                promoted,
            )
            self.assertNotIn("Promotion:", promoted)
            promoted_bytes = discussion.read_bytes()
            result = self.run_init(project, home)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(discussion.read_bytes(), promoted_bytes)

    def test_nonmatching_legacy_discussion_fails_before_any_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            project = base / "project"
            memory = project / "docs/teamwork"
            discussion = memory / "discussion/2026-06-01-release-evidence.md"
            home = base / "home"
            discussion.parent.mkdir(parents=True)
            home.mkdir()

            index = json.loads(TEMPLATE.read_text(encoding="utf-8"))
            index["active"]["discussion"] = "docs/teamwork/discussion/2026-06-01-release-evidence.md"
            index["entries"].append(
                {
                    "topic": "release-evidence",
                    "kind": "discussion",
                    "title": "Choose the release evidence boundary",
                    "status": "active",
                    "currentness": "current",
                    "authority": "supporting",
                    "path": "docs/teamwork/discussion/2026-06-01-release-evidence.md",
                    "updated": "2026-06-01",
                    "summary": "Preserve the release evidence decision route.",
                }
            )
            (memory / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
            (memory / "README.md").write_text(
                "# Existing README\n\n- Active discussion route: docs/teamwork/discussion/2026-06-01-release-evidence.md\n",
                encoding="utf-8",
            )
            (memory / "current.md").write_text(
                "# Existing current\n\n- Active discussion: docs/teamwork/discussion/2026-06-01-release-evidence.md.\n",
                encoding="utf-8",
            )
            unmatched = self.legacy_discussion().replace("- Promotion: none\n", "")
            discussion.write_text(unmatched, encoding="utf-8")

            before = self.filesystem_state(base)
            result = self.run_init(project, home)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unsupported or malformed legacy discussion artifact", result.stderr)
            self.assertEqual(
                self.filesystem_state(base),
                before,
                "malformed legacy migration must not change project or HOME bytes",
            )

    def test_project_only_flag_is_rejected(self) -> None:
        result = subprocess.run(
            [str(INIT), "--project-only"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("--project-only was removed", result.stderr)


class TeamworkDiscussionLifecycleTests(unittest.TestCase):
    discussion_path = "docs/teamwork/discussion/2026-06-01-continuity.md"
    updated = "2026-06-01"

    def setUp(self) -> None:
        self.template = json.loads(TEMPLATE.read_text(encoding="utf-8"))

    def artifact(self, status: str) -> str:
        still_open = (
            "- Whether the next evidence changes the chosen route."
            if status == "active"
            else "- None."
        )
        superseded_by = (
            "docs/teamwork/discussion/2026-06-02-follow-up.md because the route was replaced"
            if status == "superseded"
            else "none"
        )
        return f"""Artifact Type: discussion
Status: {status}
Authority: supporting
Last Updated: {self.updated}
Search Keys: continuity, handoff
Abstract: Preserve the material decision route across a handoff.
Linked Artifacts: none
Superseded By: {superseded_by}

# Preserve continuity across the handoff

## Goal

Preserve the decision route across a handoff so a second session can resume
without reconstructing the conversation.

## Settled

- Retain one supporting artifact for the decision; a per-turn transcript was
  rejected because it adds noise without improving recovery.

## Still open

{still_open}

## Key evidence

- The handoff needs settled choices and one exact resume point, establishing
  that a single supporting artifact is sufficient.

## Continue here

Assess the next decision-relevant evidence before changing the route.
"""

    def write_project(
        self,
        base: Path,
        index: dict,
        *,
        current_anchor: str,
        readme_anchor: str,
        artifact_status: str | None = None,
    ) -> Path:
        project = base / "project"
        memory = project / "docs/teamwork"
        memory.mkdir(parents=True, exist_ok=True)
        (memory / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
        (memory / "current.md").write_text(
            f"# Teamwork Current State\n\n- Active discussion: {current_anchor}.\n",
            encoding="utf-8",
        )
        (memory / "README.md").write_text(
            f"# Teamwork Runtime Index README\n\n- Active discussion route: {readme_anchor}\n",
            encoding="utf-8",
        )
        if artifact_status is not None:
            artifact = project / self.discussion_path
            artifact.parent.mkdir(parents=True, exist_ok=True)
            artifact.write_text(self.artifact(artifact_status), encoding="utf-8")
        return memory / "index.json"

    def validate(self, path: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(VALIDATOR), str(path)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def open_index(self) -> dict:
        index = copy.deepcopy(self.template)
        index["active"]["discussion"] = self.discussion_path
        index["entries"].append(
            {
                "topic": "continuity",
                "kind": "discussion",
                "title": "Continuity decision route",
                "status": "active",
                "currentness": "current",
                "authority": "supporting",
                "path": self.discussion_path,
                "updated": self.updated,
                "summary": "The current supporting route for the handoff decision.",
            }
        )
        return index

    def test_fresh_project_without_discussion_directory_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_project(
                Path(tmp),
                copy.deepcopy(self.template),
                current_anchor="none",
                readme_anchor="none",
            )
            result = self.validate(path)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((path.parent / "discussion").exists())

    def test_open_discussion_requires_index_artifact_and_runtime_anchors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            path = self.write_project(
                base,
                self.open_index(),
                current_anchor=self.discussion_path,
                readme_anchor=self.discussion_path,
                artifact_status="active",
            )
            result = self.validate(path)
            self.assertEqual(result.returncode, 0, result.stderr)

            path = self.write_project(
                base,
                self.open_index(),
                current_anchor=f"`{self.discussion_path}`",
                readme_anchor=f"`{self.discussion_path}`",
                artifact_status="active",
            )
            result = self.validate(path)
            self.assertEqual(result.returncode, 0, result.stderr)

            invalid = json.loads(path.read_text(encoding="utf-8"))
            invalid_path = "docs/teamwork/discussion/current.md"
            invalid["active"]["discussion"] = invalid_path
            invalid["entries"][-1]["path"] = invalid_path
            path.write_text(json.dumps(invalid, indent=2) + "\n", encoding="utf-8")
            result = self.validate(path)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("dated kebab-case Markdown", result.stderr)

    def test_closed_discussion_clears_active_pointer_and_uses_historical_record(self) -> None:
        closed = self.open_index()
        closed["active"]["discussion"] = None
        record = closed["entries"][-1]
        record["status"] = "accepted"
        record["currentness"] = "historical"

        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_project(
                Path(tmp),
                closed,
                current_anchor="none",
                readme_anchor="none",
                artifact_status="accepted",
            )
            result = self.validate(path)
            self.assertEqual(result.returncode, 0, result.stderr)

            invalid = json.loads(path.read_text(encoding="utf-8"))
            invalid["entries"][-1]["currentness"] = "current"
            path.write_text(json.dumps(invalid, indent=2) + "\n", encoding="utf-8")
            result = self.validate(path)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("active.discussion is null", result.stderr)

    def test_superseded_discussion_is_historical_and_cannot_keep_supporting_authority(self) -> None:
        superseded = self.open_index()
        superseded["active"]["discussion"] = None
        record = superseded["entries"][-1]
        record["status"] = "superseded"
        record["currentness"] = "historical"
        record["authority"] = "superseded"

        with tempfile.TemporaryDirectory() as tmp:
            path = self.write_project(
                Path(tmp),
                superseded,
                current_anchor="none",
                readme_anchor="none",
                artifact_status="superseded",
            )
            result = self.validate(path)
            self.assertEqual(result.returncode, 0, result.stderr)

            invalid = json.loads(path.read_text(encoding="utf-8"))
            invalid["entries"][-1]["authority"] = "supporting"
            path.write_text(json.dumps(invalid, indent=2) + "\n", encoding="utf-8")
            result = self.validate(path)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("superseded discussion", result.stderr)

    def test_active_discussion_rejects_stale_current_anchor_and_missing_template_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            path = self.write_project(
                base,
                self.open_index(),
                current_anchor="none",
                readme_anchor=self.discussion_path,
                artifact_status="active",
            )
            result = self.validate(path)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("current.md Active discussion anchor", result.stderr)

            (base / "project/docs/teamwork/current.md").write_text(
                f"# Teamwork Current State\n\n- Active discussion: {self.discussion_path}.\n",
                encoding="utf-8",
            )
            artifact = base / "project" / self.discussion_path
            artifact.write_text(
                self.artifact("active").replace("## Goal\n", "## Objective\n"),
                encoding="utf-8",
            )
            result = self.validate(path)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing section: Goal", result.stderr)


if __name__ == "__main__":
    unittest.main()
