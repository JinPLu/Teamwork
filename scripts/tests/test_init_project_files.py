import fcntl
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "scripts/init-project-files.py"
TEMPLATE = ROOT / "skills/using-teamwork/references/teamwork-index-template.json"


def legacy_artifact() -> str:
    return """Artifact Type: discussion
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
- Promotion: none

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


class GuardedProject:
    def __init__(self, base: Path) -> None:
        self.project = base / "project"
        self.memory = self.project / "docs/teamwork"
        self.memory.mkdir(parents=True)
        self.root_fd = os.open(self.project, os.O_RDONLY | os.O_DIRECTORY)
        self.docs_fd = os.open("docs", os.O_RDONLY | os.O_DIRECTORY, dir_fd=self.root_fd)
        self.teamwork_fd = os.open("teamwork", os.O_RDONLY | os.O_DIRECTORY, dir_fd=self.docs_fd)
        self.lock_fd = os.dup(self.teamwork_fd)
        fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)

    @property
    def pass_fds(self) -> tuple[int, ...]:
        return self.root_fd, self.docs_fd, self.teamwork_fd, self.lock_fd

    def env(self) -> dict[str, str]:
        env = os.environ.copy()
        env.update(
            {
                "TEAMWORK_DISCUSSION_GUARD_ROOT_FD": str(self.root_fd),
                "TEAMWORK_DISCUSSION_GUARD_DOCS_FD": str(self.docs_fd),
                "TEAMWORK_DISCUSSION_GUARD_TEAMWORK_FD": str(self.teamwork_fd),
                "TEAMWORK_DISCUSSION_GUARD_LOCK_FD": str(self.lock_fd),
                "TEAMWORK_DISCUSSION_GUARD_TOKEN": "a" * 64,
                "TEAMWORK_PROJECT_ROOT": str(self.project),
            }
        )
        return env

    def run(
        self,
        *args: str,
        env_update: dict[str, str] | None = None,
        pass_fds: tuple[int, ...] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        env = self.env()
        if env_update:
            env.update(env_update)
        return subprocess.run(
            ["python3", str(HELPER), *args],
            cwd=ROOT,
            env=env,
            pass_fds=self.pass_fds if pass_fds is None else pass_fds,
            text=True,
            capture_output=True,
            check=False,
        )

    def close(self) -> None:
        fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
        for fd in (self.lock_fd, self.teamwork_fd, self.docs_fd, self.root_fd):
            os.close(fd)


class InitProjectFilesTests(unittest.TestCase):
    def guarded(self, base: Path) -> GuardedProject:
        guard = GuardedProject(base)
        self.addCleanup(guard.close)
        return guard

    def initialize(self, guard: GuardedProject) -> None:
        result = guard.run("write-context", "--today", "2026-07-15", "--project-label", "Fixture")
        self.assertEqual(result.returncode, 0, result.stderr)

    def memory_snapshot(self, memory: Path) -> dict[str, tuple[int, bytes]]:
        result: dict[str, tuple[int, bytes]] = {}
        for path in sorted(memory.rglob("*")):
            if path.is_file():
                result[path.relative_to(memory).as_posix()] = (
                    path.stat().st_mode & 0o777,
                    path.read_bytes(),
                )
        return result

    def identity_snapshot(self, root: Path) -> dict[str, tuple[object, ...]]:
        result: dict[str, tuple[object, ...]] = {}
        for path in sorted((root, *root.rglob("*")), key=lambda value: str(value)):
            info = path.lstat()
            relative = "." if path == root else path.relative_to(root).as_posix()
            if path.is_file():
                result[relative] = ("file", info.st_dev, info.st_ino, info.st_mode, path.read_bytes())
            elif path.is_dir():
                result[relative] = ("directory", info.st_dev, info.st_ino, info.st_mode)
            else:
                result[relative] = ("other", info.st_dev, info.st_ino, info.st_mode)
        return result

    def make_three_file_migration(self, guard: GuardedProject) -> None:
        self.initialize(guard)
        index_path = guard.memory / "index.json"
        current_path = guard.memory / "current.md"
        readme_path = guard.memory / "README.md"
        index = json.loads(index_path.read_text(encoding="utf-8"))
        del index["active"]["discussion"]
        index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
        current_path.write_text(
            current_path.read_text(encoding="utf-8").replace("- Active discussion: none.\n", ""),
            encoding="utf-8",
        )
        readme_path.write_text(
            readme_path.read_text(encoding="utf-8").replace("- Active discussion route: none\n", ""),
            encoding="utf-8",
        )
        os.chmod(index_path, 0o640)
        os.chmod(current_path, 0o600)
        os.chmod(readme_path, 0o644)

    def test_write_context_creates_only_required_runtime_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            guard = self.guarded(Path(tmp))

            self.initialize(guard)

            self.assertEqual(
                sorted(path.name for path in guard.memory.iterdir()),
                ["README.md", "current.md", "index.json", "plans", "reports", "research", "workflows"],
            )
            self.assertFalse((guard.memory / "discussion").exists())
            self.assertIn("Fixture", (guard.project / "AGENTS.md").read_text(encoding="utf-8"))
            self.assertIn("docs/teamwork/discussion/", (guard.project / ".gitignore").read_text(encoding="utf-8"))
            self.assertIn("docs/teamwork/.teamwork-init-transaction.json*", (guard.project / ".gitignore").read_text(encoding="utf-8"))
            validated = guard.run("validate")
            self.assertEqual(validated.returncode, 0, validated.stderr)

    def test_write_context_uses_project_directory_as_label_without_readme(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            guard = self.guarded(Path(tmp))

            result = guard.run("write-context", "--today", "2026-07-15")

            self.assertEqual(result.returncode, 0, result.stderr)
            agents = (guard.project / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("Project label (local routing only): `project`", agents)
            index = json.loads((guard.memory / "index.json").read_text(encoding="utf-8"))
            self.assertEqual(index["project"]["name"], "project")

    def test_write_stays_on_retained_inode_after_canonical_memory_is_replaced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            guard = self.guarded(Path(tmp))
            retained = guard.project / "docs/retained-teamwork"
            guard.memory.rename(retained)
            transient = guard.project / "docs/teamwork"
            transient.mkdir()

            result = guard.run("write-context", "--today", "2026-07-15", "--project-label", "Retained")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((retained / "index.json").is_file())
            self.assertTrue((retained / "research").is_dir())
            self.assertEqual(list(transient.iterdir()), [])

    def test_marker_and_invalid_token_are_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            guard = self.guarded(Path(tmp))
            (guard.memory / ".discussion-transaction.json").write_text("{}\n", encoding="utf-8")
            marker = guard.run("preflight")
            self.assertNotEqual(marker.returncode, 0)
            self.assertIn("unfinished discussion transaction marker", marker.stderr)
            (guard.memory / ".discussion-transaction.json").unlink()

            token = guard.run("preflight", env_update={"TEAMWORK_DISCUSSION_GUARD_TOKEN": "bad"})
            self.assertNotEqual(token.returncode, 0)
            self.assertIn("token is malformed", token.stderr)

    def test_forged_lock_descriptor_is_refused_while_real_guard_holds_lock(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            guard = self.guarded(Path(tmp))
            forged = os.open(guard.memory, os.O_RDONLY | os.O_DIRECTORY)
            self.addCleanup(os.close, forged)

            result = guard.run(
                "preflight",
                env_update={"TEAMWORK_DISCUSSION_GUARD_LOCK_FD": str(forged)},
                pass_fds=(guard.root_fd, guard.docs_fd, guard.teamwork_fd, forged),
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("does not own the guard lock", result.stderr)

    def test_invalid_or_unpassed_descriptor_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            guard = self.guarded(Path(tmp))
            invalid = guard.run(
                "preflight",
                env_update={"TEAMWORK_DISCUSSION_GUARD_TEAMWORK_FD": "not-an-fd"},
            )
            self.assertNotEqual(invalid.returncode, 0)
            self.assertIn("not a file descriptor", invalid.stderr)

            closed_in_child = guard.run("preflight", pass_fds=())
            self.assertNotEqual(closed_in_child.returncode, 0)
            self.assertIn("cannot inspect inherited guard descriptor", closed_in_child.stderr)

    def test_nonregular_root_output_is_refused_before_directory_creation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            guard = self.guarded(Path(tmp))
            (guard.project / "AGENTS.md").mkdir()

            result = guard.run("write-context", "--today", "2026-07-15")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("project output must be a single-link regular file", result.stderr)
            self.assertEqual(list(guard.memory.iterdir()), [])

    def test_migration_rolls_back_all_files_and_preserves_modes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            guard = self.guarded(Path(tmp))
            self.initialize(guard)
            index_path = guard.memory / "index.json"
            current_path = guard.memory / "current.md"
            readme_path = guard.memory / "README.md"
            index = json.loads(index_path.read_text(encoding="utf-8"))
            del index["active"]["discussion"]
            index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
            current_path.write_text(
                current_path.read_text(encoding="utf-8").replace("- Active discussion: none.\n", ""),
                encoding="utf-8",
            )
            current_read = readme_path.read_text(encoding="utf-8")
            current_block = """## Read Order

1. For Grill/discussion continuation, load `grill-me`, resolve the installed
   `scripts/discussion-transaction.py` from the loaded `using-teamwork` skill,
   and run `inspect` from the project root first.
   Its result is the sole discussion read path.
   For that continuation, do not directly read `index.json`,
   `current.md`, this README, or a discussion artifact.
2. For ordinary non-discussion memory, read `docs/teamwork/index.json` first,
   then this README.
3. Follow `active.current` and other non-discussion `active` pointers before
   any broad scan.
4. Prefer headers before full artifact bodies and use the stage-specific
   profiles from the index."""
            legacy_block = """## Read Order

1. Read `docs/teamwork/index.json` first.
2. Follow `active.current`, then `active.discussion` when present, then the other `active` pointers before any broad scan.
3. Prefer headers before full artifact bodies.
4. Use stage-specific profiles from the index."""
            readme_path.write_text(
                current_read.replace(current_block, legacy_block).replace(
                    "- `discussion`: use the helper's `inspect` result; never open\n  `active.discussion` or its artifact directly.",
                    "- `discussion`: read the active discussion before continuing dependent work.",
                ).replace("- Active discussion route: none\n", ""),
                encoding="utf-8",
            )
            os.chmod(index_path, 0o640)
            os.chmod(current_path, 0o600)
            os.chmod(readme_path, 0o644)
            before = self.memory_snapshot(guard.memory)

            failed = guard.run(
                "migrate",
                env_update={"TEAMWORK_TEST_FAIL_MIGRATION_REPLACE_AT": "2"},
            )

            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("was rolled back", failed.stderr)
            self.assertEqual(self.memory_snapshot(guard.memory), before)

            migrated = guard.run("migrate")
            self.assertEqual(migrated.returncode, 0, migrated.stderr)
            after = self.memory_snapshot(guard.memory)
            self.assertEqual(after["index.json"][0], 0o640)
            self.assertEqual(after["current.md"][0], 0o600)
            self.assertEqual(after["README.md"][0], 0o644)
            self.assertIn("active.discussion", readme_path.read_text(encoding="utf-8"))
            self.assertEqual(guard.run("migrate").returncode, 0)
            self.assertEqual(self.memory_snapshot(guard.memory), after)

    def test_write_context_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            guard = self.guarded(Path(tmp))
            self.initialize(guard)
            before = self.memory_snapshot(guard.memory)
            root_before = {
                name: (guard.project / name).read_bytes()
                for name in ("AGENTS.md", ".gitignore")
            }

            second = guard.run("write-context", "--today", "2026-07-15", "--project-label", "Fixture")

            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(self.memory_snapshot(guard.memory), before)
            self.assertEqual(
                {name: (guard.project / name).read_bytes() for name in root_before},
                root_before,
            )

    def test_hard_exit_after_each_canonical_replace_recovers_exact_file_prestate(self) -> None:
        for ordinal in range(1, 6):
            with self.subTest(ordinal=ordinal), tempfile.TemporaryDirectory() as tmp:
                guard = self.guarded(Path(tmp))
                failed = guard.run(
                    "write-context",
                    "--today", "2026-07-15",
                    "--project-label", "Fixture",
                    env_update={"TEAMWORK_TEST_HARD_EXIT_INIT_REPLACE_AT": str(ordinal)},
                )
                self.assertEqual(failed.returncode, 86, failed.stderr)
                marker = guard.memory / ".teamwork-init-transaction.json"
                self.assertTrue(marker.is_file())
                formal = subprocess.run(
                    ["python3", str(ROOT / "scripts/validate_teamwork_index.py"), str(guard.memory / "index.json")],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertNotEqual(formal.returncode, 0)
                self.assertIn("Teamwork init transaction marker", formal.stderr)

                recovered = guard.run("preflight")
                self.assertEqual(recovered.returncode, 0, recovered.stderr)
                self.assertFalse(marker.exists())
                self.assertEqual(self.memory_snapshot(guard.memory), {})
                self.assertFalse((guard.project / "AGENTS.md").exists())
                self.assertFalse((guard.project / ".gitignore").exists())
                self.assertEqual(
                    [path for path in guard.project.rglob("*") if ".teamwork-init-" in path.name],
                    [],
                )

    def test_hard_exit_phase_recovery_uses_durable_commit_point(self) -> None:
        for phase in ("preparing", "prepared", "committed", "cleanup"):
            with self.subTest(phase=phase), tempfile.TemporaryDirectory() as tmp:
                guard = self.guarded(Path(tmp))
                failed = guard.run(
                    "write-context",
                    "--today", "2026-07-15",
                    "--project-label", "Fixture",
                    env_update={"TEAMWORK_TEST_HARD_EXIT_INIT_PHASE": phase},
                )
                self.assertEqual(failed.returncode, 86, failed.stderr)
                recovered = guard.run("preflight")
                self.assertEqual(recovered.returncode, 0, recovered.stderr)
                committed = phase in {"committed", "cleanup"}
                self.assertEqual((guard.memory / "index.json").exists(), committed)
                self.assertEqual((guard.project / "AGENTS.md").exists(), committed)
                self.assertFalse((guard.memory / ".teamwork-init-transaction.json").exists())
                self.assertEqual(
                    [path for path in guard.project.rglob("*") if ".teamwork-init-" in path.name],
                    [],
                )

    def test_migration_hard_exit_after_each_replace_restores_exact_bytes_and_modes(self) -> None:
        for ordinal in range(1, 4):
            with self.subTest(ordinal=ordinal), tempfile.TemporaryDirectory() as tmp:
                guard = self.guarded(Path(tmp))
                self.make_three_file_migration(guard)
                before = self.memory_snapshot(guard.memory)

                failed = guard.run(
                    "migrate",
                    env_update={"TEAMWORK_TEST_HARD_EXIT_MIGRATION_REPLACE_AT": str(ordinal)},
                )
                self.assertEqual(failed.returncode, 86, failed.stderr)
                self.assertTrue((guard.memory / ".teamwork-init-transaction.json").is_file())

                recovered = guard.run("preflight")
                self.assertEqual(recovered.returncode, 0, recovered.stderr)
                self.assertEqual(self.memory_snapshot(guard.memory), before)
                self.assertEqual(
                    [path for path in guard.project.rglob("*") if ".teamwork-init-" in path.name],
                    [],
                )

    def test_migration_refuses_noncanonical_legacy_discussion_before_transaction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            guard = self.guarded(Path(tmp))
            self.initialize(guard)
            discussion = guard.memory / "discussion"
            discussion.mkdir()
            legacy = discussion / "legacy.md"
            legacy.write_text(legacy_artifact(), encoding="utf-8")
            before = self.identity_snapshot(guard.project)

            migrated = guard.run("migrate")

            self.assertNotEqual(migrated.returncode, 0)
            self.assertIn("canonical dated-kebab filename", migrated.stderr)
            self.assertEqual(self.identity_snapshot(guard.project), before)
            self.assertFalse((guard.memory / ".teamwork-init-transaction.json").exists())

    def test_init_recovery_refuses_same_bytes_destination_inode_aba(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            guard = self.guarded(Path(tmp))
            failed = guard.run(
                "write-context",
                "--today", "2026-07-15",
                env_update={"TEAMWORK_TEST_HARD_EXIT_INIT_REPLACE_AT": "1"},
            )
            self.assertEqual(failed.returncode, 86, failed.stderr)
            readme = guard.memory / "README.md"
            same_bytes = readme.read_bytes()
            readme.unlink()
            readme.write_bytes(same_bytes)

            recovered = guard.run("preflight")

            self.assertNotEqual(recovered.returncode, 0)
            self.assertIn("output inode does not match", recovered.stderr)
            self.assertTrue((guard.memory / ".teamwork-init-transaction.json").is_file())

    def test_init_recovery_refuses_same_bytes_stage_inode_aba(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            guard = self.guarded(Path(tmp))
            failed = guard.run(
                "write-context",
                "--today", "2026-07-15",
                env_update={"TEAMWORK_TEST_HARD_EXIT_INIT_PHASE": "prepared"},
            )
            self.assertEqual(failed.returncode, 86, failed.stderr)
            stage = next(path for path in guard.memory.iterdir() if ".teamwork-init-stage-" in path.name)
            same_bytes = stage.read_bytes()
            stage.unlink()
            stage.write_bytes(same_bytes)

            recovered = guard.run("preflight")

            self.assertNotEqual(recovered.returncode, 0)
            self.assertIn("temporary inode does not match", recovered.stderr)
            self.assertTrue((guard.memory / ".teamwork-init-transaction.json").is_file())

    def test_recovery_parent_fsync_failure_preserves_journal_until_retry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            guard = self.guarded(Path(tmp))
            failed = guard.run(
                "write-context",
                "--today", "2026-07-15",
                env_update={"TEAMWORK_TEST_HARD_EXIT_INIT_REPLACE_AT": "2"},
            )
            self.assertEqual(failed.returncode, 86, failed.stderr)
            marker = guard.memory / ".teamwork-init-transaction.json"

            first_recovery = guard.run(
                "preflight",
                env_update={"TEAMWORK_TEST_FAIL_INIT_RECOVERY_PARENT_FSYNC_AT": "1"},
            )
            self.assertNotEqual(first_recovery.returncode, 0)
            self.assertIn("journal preserved", first_recovery.stderr)
            self.assertTrue(marker.is_file())

            retry = guard.run("preflight")
            self.assertEqual(retry.returncode, 0, retry.stderr)
            self.assertFalse(marker.exists())
            self.assertEqual(self.memory_snapshot(guard.memory), {})

    def test_invalid_journal_record_never_partially_recovers_other_records(self) -> None:
        for corruption in (
            "malformed", "unknown-identity", "duplicate-target",
            "unauthorized-target", "cross-target-temp",
        ):
            with self.subTest(corruption=corruption), tempfile.TemporaryDirectory() as tmp:
                guard = self.guarded(Path(tmp))
                failed = guard.run(
                    "write-context",
                    "--today", "2026-07-15",
                    env_update={"TEAMWORK_TEST_HARD_EXIT_INIT_REPLACE_AT": "2"},
                )
                self.assertEqual(failed.returncode, 86, failed.stderr)
                marker = guard.memory / ".teamwork-init-transaction.json"
                journal = json.loads(marker.read_text(encoding="utf-8"))
                if corruption == "malformed":
                    del journal["changes"][0]["after_mode"]
                elif corruption == "unknown-identity":
                    journal["changes"][0]["stage_inode"] += 1
                else:
                    if corruption == "duplicate-target":
                        journal["changes"][0] = dict(journal["changes"][1])
                    elif corruption == "unauthorized-target":
                        journal["changes"][0]["parent"] = "root"
                        journal["changes"][0]["name"] = "README.md"
                        journal["changes"][0]["logical"] = "README.md"
                    else:
                        agents = next(record for record in journal["changes"] if record["name"] == "AGENTS.md")
                        gitignore = next(record for record in journal["changes"] if record["name"] == ".gitignore")
                        agents["stage"] = gitignore["stage"]
                        agents["stage_device"] = gitignore["stage_device"]
                        agents["stage_inode"] = gitignore["stage_inode"]
                marker.write_text(json.dumps(journal) + "\n", encoding="utf-8")
                before = self.identity_snapshot(guard.project)

                recovered = guard.run("preflight")

                self.assertNotEqual(recovered.returncode, 0)
                self.assertEqual(self.identity_snapshot(guard.project), before)
                self.assertTrue(marker.is_file())

    def test_legacy_discussion_schema_is_migrated_and_malformed_route_is_refused(self) -> None:
        for malformed in (False, True):
            with self.subTest(malformed=malformed), tempfile.TemporaryDirectory() as tmp:
                guard = self.guarded(Path(tmp))
                discussion_dir = guard.memory / "discussion"
                discussion_dir.mkdir()
                artifact_path = discussion_dir / "2026-06-01-release-evidence.md"
                artifact = legacy_artifact()
                if malformed:
                    artifact = artifact.replace('R1["R1 · Release evidence · current"]', 'release["Release"]')
                artifact_path.write_text(artifact, encoding="utf-8")
                relative = "docs/teamwork/discussion/2026-06-01-release-evidence.md"
                index = json.loads(TEMPLATE.read_text(encoding="utf-8"))
                index["active"]["discussion"] = relative
                index["entries"].append(
                    {
                        "topic": "release-evidence",
                        "kind": "discussion",
                        "title": "Choose the release evidence boundary",
                        "status": "active",
                        "currentness": "current",
                        "authority": "supporting",
                        "path": relative,
                        "updated": "2026-06-01",
                        "summary": "Preserve the release evidence decision route.",
                    }
                )
                (guard.memory / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
                (guard.memory / "current.md").write_text(
                    f"# Existing current\n\n- Active discussion: {relative}.\n", encoding="utf-8"
                )
                (guard.memory / "README.md").write_text(
                    f"# Existing README\n\n- Active discussion route: {relative}\n", encoding="utf-8"
                )
                before = self.memory_snapshot(guard.memory)

                result = guard.run("migrate")

                if malformed:
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("unsupported or malformed legacy discussion artifact", result.stderr)
                    self.assertEqual(self.memory_snapshot(guard.memory), before)
                else:
                    self.assertEqual(result.returncode, 0, result.stderr)
                    migrated = artifact_path.read_text(encoding="utf-8")
                    self.assertIn("Superseded By: none", migrated)
                    self.assertIn("# Choose the evidence boundary for release", migrated)
                    self.assertNotIn("## Route Map", migrated)
                    first = self.memory_snapshot(guard.memory)
                    self.assertEqual(guard.run("migrate").returncode, 0)
                    self.assertEqual(self.memory_snapshot(guard.memory), first)

    def test_codegraph_command_runs_from_retained_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            guard = self.guarded(Path(tmp))
            result = guard.run(
                "codegraph",
                "--",
                "python3",
                "-c",
                "import os; print(os.getcwd())",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(Path(result.stdout.strip()).samefile(guard.project))


if __name__ == "__main__":
    unittest.main()
