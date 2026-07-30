from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BUILD_SCRIPT = ROOT / "scripts/build-codex-plugin.py"
CURRENT_VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
FIXED_DAY = "2026-07-30"
MIGRATION_SEED = "51" * 32
UPDATED_AT = "2026-07-30T00:00:00+00:00"


def load_builder() -> Any:
    spec = importlib.util.spec_from_file_location("build_codex_plugin", BUILD_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load builder from {BUILD_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_runtime_contract(package_root: Path) -> dict[str, Any]:
    spec = importlib.util.spec_from_file_location(
        "installed_discussion_transaction",
        package_root / "scripts/discussion-transaction.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load installed discussion transaction")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return {
        "migration_phase_request": module.migration_phase_request,
    }


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def legacy_index() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "last_updated": FIXED_DAY,
        "project": {"name": "Installed E2E", "root": ".", "description": "sanitized legacy fixture"},
        "active": {
            "current": "docs/teamwork/current.md",
            "design": None,
            "plan": None,
            "progress": None,
            "report": None,
            "results": [],
            "collaborate": None,
        },
        "entries": [
            {
                "topic": "project-initialization",
                "kind": "result",
                "title": "Teamwork project initialization",
                "status": "active",
                "currentness": "current",
                "authority": "active-summary",
                "path": "docs/teamwork/current.md",
                "applies_to": ["docs/teamwork/"],
                "linked": [],
                "evidence_paths": ["docs/teamwork/current.md"],
                "supersedes": [],
                "search_keys": ["teamwork-init", "legacy"],
                "updated": FIXED_DAY,
                "summary": "Sanitized legacy v1 fixture for installed-package E2E.",
            }
        ],
    }


def write_legacy_project(project: Path) -> None:
    memory = project / "docs/teamwork"
    memory.mkdir(parents=True)
    (memory / "index.json").write_text(
        json.dumps(legacy_index(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (memory / "current.md").write_text("# Current\n\nLegacy current state.\n", encoding="utf-8")
    (memory / "README.md").write_text("# README\n\nLegacy memory map.\n", encoding="utf-8")
    reports = memory / "reports"
    reports.mkdir()
    (reports / "2026-07-30-installed-e2e.md").write_text(
        "# Report\n\nLegacy durable report.\n",
        encoding="utf-8",
    )
    os.chmod(memory / "current.md", 0o640)
    os.chmod(memory / "README.md", 0o600)


def tree_fingerprint(root: Path, relative: str) -> dict[str, dict[str, Any]]:
    base = root / relative
    if not base.exists():
        return {}
    fingerprint: dict[str, dict[str, Any]] = {}
    for path in sorted(base.rglob("*")):
        rel = path.relative_to(root).as_posix()
        info = path.lstat()
        mode = stat.S_IMODE(info.st_mode)
        if stat.S_ISREG(info.st_mode):
            fingerprint[rel] = {"type": "file", "mode": mode, "sha256": sha256_file(path)}
        elif stat.S_ISDIR(info.st_mode):
            fingerprint[rel] = {"type": "dir", "mode": mode}
        elif stat.S_ISLNK(info.st_mode):
            fingerprint[rel] = {"type": "symlink", "mode": mode, "target": os.readlink(path)}
        else:
            fingerprint[rel] = {"type": "other", "mode": mode}
    return fingerprint


class InstalledCaseBundleE2ETests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix=".case-installed-e2e-", dir=ROOT)
        self.tmp = Path(self.temporary.name)
        self.cache = self.tmp / "cache"
        self.package_root = self.cache / f"teamwork/teamwork-skill/{CURRENT_VERSION}"
        builder = load_builder()
        stage = builder.build_stage(ROOT, self.tmp)
        self.package_root.parent.mkdir(parents=True)
        shutil.copytree(stage, self.package_root, symlinks=True)
        shutil.rmtree(stage.parent)
        self.contract = load_runtime_contract(self.package_root)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @property
    def transaction_cli(self) -> Path:
        return self.package_root / "scripts/discussion-transaction.py"

    @property
    def init_cli(self) -> Path:
        return self.package_root / "scripts/init-project-files.py"

    @property
    def helper_cli(self) -> Path:
        return self.package_root / "scripts/teamwork-case-migration.py"

    @property
    def runtime_root_cli(self) -> Path:
        return self.package_root / "scripts/plugin-runtime-root.py"

    def run_pkg(
        self,
        script: Path,
        *args: str,
        env: dict[str, str] | None = None,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        merged = os.environ.copy()
        if env:
            merged.update(env)
        result = subprocess.run(
            [sys.executable, str(script), *args],
            cwd=self.package_root,
            text=True,
            capture_output=True,
            env=merged,
            check=False,
        )
        if check:
            self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def json_pkg(
        self,
        script: Path,
        *args: str,
        env: dict[str, str] | None = None,
        check: bool = True,
    ) -> dict[str, Any]:
        result = self.run_pkg(script, *args, env=env, check=check)
        stream = result.stdout if result.returncode == 0 else result.stderr
        try:
            payload = json.loads(stream)
        except json.JSONDecodeError as exc:
            raise AssertionError(f"expected JSON output, got stdout={result.stdout!r} stderr={result.stderr!r}") from exc
        return payload

    def write_fresh_v2_project(self, project: Path, label: str = "Fresh Installed E2E") -> None:
        project.mkdir()
        self.run_pkg(
            self.init_cli,
            "--project-root",
            str(project),
            "write-context",
            "--today",
            FIXED_DAY,
            "--project-label",
            label,
        )

    def case_inspect(self, project: Path) -> dict[str, Any]:
        return self.json_pkg(self.transaction_cli, "case-inspect", "--project-root", str(project))

    def case_apply(self, project: Path, request: dict[str, Any]) -> dict[str, Any]:
        return self.json_pkg(
            self.transaction_cli,
            "case-apply",
            "--project-root",
            str(project),
            "--request-json",
            json.dumps(request, ensure_ascii=False, sort_keys=True),
        )

    def case_writer_request(self, project: Path, operation: str, case: dict[str, Any] | None = None, **extra: Any) -> dict[str, Any]:
        inspected = self.case_inspect(project)
        request: dict[str, Any] = {
            "schema_version": 2,
            "operation": operation,
            "expected_revision": inspected["revision"],
            "updated_at": extra.pop("updated_at", UPDATED_AT),
        }
        if case is not None:
            request["case_id"] = case["case_id"]
            request["expected_manifest_revision"] = case["manifest_revision"]
        request.update(extra)
        return request

    def case_writer_body_request(self, project: Path, operation: str, case: dict[str, Any], body: str, **extra: Any) -> dict[str, Any]:
        request = self.case_writer_request(
            project,
            operation,
            case,
            source_digest=sha256_bytes(body.encode("utf-8")),
            body=body,
            **extra,
        )
        return request

    def migration_request(self, project: Path, operation: str) -> dict[str, Any]:
        return self.json_pkg(
            self.transaction_cli,
            "migration-request",
            "--project-root",
            str(project),
            "--request-json",
            json.dumps({"schema_version": 1, "operation": operation, "migration_seed": MIGRATION_SEED}),
        )

    def migration_apply(
        self,
        project: Path,
        request: dict[str, Any],
        *,
        env: dict[str, str] | None = None,
        check: bool = True,
    ) -> dict[str, Any]:
        return self.json_pkg(
            self.transaction_cli,
            "migration-apply",
            "--project-root",
            str(project),
            "--request-json",
            json.dumps(request, ensure_ascii=False, sort_keys=True),
            env=env,
            check=check,
        )

    def phase_request(
        self,
        operation: str,
        migration_id: str,
        baseline_digest: str,
        *,
        cutover_authority: str | None = None,
    ) -> dict[str, Any]:
        return self.contract["migration_phase_request"](
            operation,
            migration_id,
            baseline_digest,
            cutover_authority=cutover_authority,
        )

    def make_legacy_project(self, name: str = "legacy-project") -> Path:
        project = self.tmp / name
        project.mkdir()
        write_legacy_project(project)
        claude = project / ".claude"
        claude.mkdir()
        (claude / "settings.json").write_text('{"permissions":{"allow":[]}}\n', encoding="utf-8")
        return project

    def test_installed_runtime_root_is_cache_version_tail_and_integrity_checked(self) -> None:
        self.assertEqual(
            self.package_root.relative_to(self.cache).as_posix(),
            f"teamwork/teamwork-skill/{CURRENT_VERSION}",
        )
        self.assertEqual(
            (self.package_root / "VERSION").read_text(encoding="utf-8").strip(),
            CURRENT_VERSION,
        )
        result = self.run_pkg(self.runtime_root_cli)
        self.assertEqual(Path(result.stdout.strip()).resolve(), self.package_root.resolve())
        self.assertTrue(self.helper_cli.is_file(), "installed package must ship scripts/teamwork-case-migration.py")
        helper_project = self.make_legacy_project("helper-read-only-project")
        before = tree_fingerprint(helper_project, ".")
        helper = self.json_pkg(self.helper_cli, "request-inputs", "--project-root", str(helper_project))
        self.assertEqual(helper["classification"]["mode"], "legacy-v1")
        self.assertIn("baseline_digest", helper["baseline"])
        self.assertEqual(before, tree_fingerprint(helper_project, "."))

        tampered_root = self.tmp / f"tampered/teamwork/teamwork-skill/{CURRENT_VERSION}"
        shutil.copytree(self.package_root, tampered_root, symlinks=True)
        transaction = tampered_root / "scripts/discussion-transaction.py"
        transaction.write_text(transaction.read_text(encoding="utf-8") + "\n# tamper\n", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(tampered_root / "scripts/plugin-runtime-root.py")],
            cwd=tampered_root,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("runtime hash mismatch", result.stderr)

    def test_installed_helper_rejects_symlink_project_roots_before_writes(self) -> None:
        for kind in ("leaf", "ancestor"):
            with self.subTest(kind=kind):
                project = self.make_legacy_project(f"symlink-{kind}-target")
                outside = self.tmp / f"symlink-{kind}-outside"
                outside.mkdir()
                if kind == "leaf":
                    alias = self.tmp / "leaf-project-alias"
                    os.symlink(project, alias)
                    project_root = alias
                    alias_to_check = alias
                else:
                    alias_parent = self.tmp / "ancestor-parent-alias"
                    os.symlink(self.tmp, alias_parent)
                    project_root = alias_parent / project.name
                    alias_to_check = alias_parent
                target_before = tree_fingerprint(project, ".")
                alias_target = os.readlink(alias_to_check)

                result = self.run_pkg(
                    self.helper_cli,
                    "migrate",
                    "--project-root",
                    str(project_root),
                    "--cutover",
                    "--cleanup",
                    check=False,
                )

                self.assertNotEqual(result.returncode, 0)
                self.assertIn("symlink", result.stderr)
                self.assertEqual(tree_fingerprint(project, "."), target_before)
                self.assertTrue(alias_to_check.is_symlink())
                self.assertEqual(os.readlink(alias_to_check), alias_target)
                self.assertEqual(list(outside.iterdir()), [])

    def test_fresh_init_uses_v2_index_without_legacy_current_or_readme(self) -> None:
        project = self.tmp / "fresh-project"
        self.write_fresh_v2_project(project)

        index = json.loads((project / "docs/teamwork/index.json").read_text(encoding="utf-8"))
        self.assertEqual(set(index), {"schema_version", "project", "active_cases", "claim_heads", "aliases", "recent_cases", "migration"})
        self.assertEqual(index["schema_version"], 2)
        self.assertFalse((project / "docs/teamwork/current.md").exists())
        self.assertFalse((project / "docs/teamwork/README.md").exists())

    def test_fresh_v2_writer_uses_case_route_for_workflow_artifacts(self) -> None:
        project = self.tmp / "fresh-v2-writer-route"
        self.write_fresh_v2_project(project, "Fresh V2 Writer Route")

        legacy_probe = self.run_pkg(
            self.transaction_cli,
            "artifact-inspect",
            "--project-root",
            str(project),
            check=False,
        )
        self.assertNotEqual(legacy_probe.returncode, 0, "v2 Writer must not treat legacy artifact-inspect as success")
        self.assertFalse((project / "docs/teamwork/plans").exists())

        initial = self.case_inspect(project)
        self.assertEqual(initial["schema_mode"], "case-v2")
        self.assertEqual(initial["active_cases"], [])
        create_schema = self.json_pkg(self.transaction_cli, "case-schema", "create")
        self.assertEqual(create_schema["expected_revision"], "<revision from case-inspect>")

        case = self.case_apply(
            project,
            self.case_writer_request(
                project,
                "create",
                case_seed="61" * 32,
                title="Fresh V2 Writer Route",
                task_key="fresh-v2-writer-route",
                aliases=["fresh-v2-writer-route"],
                initial_phase="collaborating",
            ),
        )
        case_id = case["case_id"]
        self.assertTrue((project / f"docs/teamwork/cases/{case_id}/manifest.json").is_file())

        sequence: list[tuple[str, dict[str, Any]]] = [
            (
                "collaborate-upsert",
                {
                    "body": "## Collaborate\n\n- First sustained checkpoint.",
                },
            ),
            (
                "collaborate-upsert",
                {
                    "body": "## Collaborate\n\n- Second sustained checkpoint.",
                },
            ),
            (
                "accept-decision",
                {
                    "body": "## Decision\n\n- Accepted decision checkpoint.",
                },
            ),
            ("update", {"phase": "collecting"}),
            (
                "research-add",
                {
                    "body": "## Research\n\n- Cited external evidence packet.",
                },
            ),
            (
                "debug-add",
                {
                    "body": "## Debug\n\n- Cause and verification packet.",
                },
            ),
            (
                "init-result",
                {
                    "body": "## Init\n\n- Project-local receipt.",
                },
            ),
            (
                "update-result",
                {
                    "body": "## Update\n\n- Global update receipt.",
                },
            ),
            (
                "native-result",
                {
                    "body": "## Execution\n\n- Terminal native execution handoff.",
                },
            ),
            ("update", {"phase": "planned"}),
            (
                "plan-review-add",
                {
                    "body": "## Plan Review\n\n- Plan review verdict.",
                    "sealed_candidate_digest": "71" * 32,
                },
            ),
            (
                "plan-upsert",
                {
                    "body": "## Plan\n\n- Execution-ready plan.",
                },
            ),
            (
                "goal-acquire",
                {
                    "body": "## Goal\n\n- Objective and first attempt.",
                    "claim_seed": "72" * 32,
                    "owner": "Goal",
                },
            ),
            (
                "goal-update",
                {
                    "body": "## Goal\n\n- Attempt evidence update.",
                    "claim_seed": "72" * 32,
                    "owner": "Goal",
                },
            ),
            (
                "review-add",
                {
                    "body": "## Review\n\n- Integrated candidate verdict.",
                    "sealed_candidate_digest": "73" * 32,
                },
            ),
            (
                "code-review-add",
                {
                    "body": "## Code Review\n\n- Delta candidate verdict.",
                    "sealed_candidate_digest": "73" * 32,
                    "delta": True,
                },
            ),
            ("repair-return", {}),
            (
                "result-add",
                {
                    "body": "## Result\n\n- Final result packet.",
                },
            ),
            ("close", {"closed_at": UPDATED_AT}),
        ]

        expected_paths: set[str] = {f"docs/teamwork/cases/{case_id}/manifest.json"}
        for operation, fields in sequence:
            if "body" in fields:
                request = self.case_writer_body_request(project, operation, case, str(fields.pop("body")), **fields)
            else:
                request = self.case_writer_request(project, operation, case, **fields)
            case = self.case_apply(project, request)
            self.assertEqual(case["schema_mode"], "case-v2")
            self.assertEqual(case["case_id"], case_id)
            self.assertIn(f"docs/teamwork/cases/{case_id}/manifest.json", case["changed_paths"])
            expected_paths.update(case["changed_paths"])

        inspected = self.case_inspect(project)
        self.assertEqual(inspected["schema_mode"], "case-v2")
        self.assertEqual(inspected["active_cases"], [])
        self.assertEqual(inspected["recent_cases"][0]["case_id"], case_id)
        manifest = json.loads((project / f"docs/teamwork/cases/{case_id}/manifest.json").read_text(encoding="utf-8"))
        for artifact_id, row in manifest["artifacts"].items():
            artifact_path = project / row["path"]
            with self.subTest(artifact=artifact_id):
                self.assertTrue(artifact_path.is_file(), row["path"])
                self.assertEqual(row["byte_digest"], sha256_file(artifact_path))
        roles = {row["role"] for row in manifest["artifacts"].values()}
        self.assertTrue({"collaborate", "decision", "evidence", "plan", "goal", "review", "result"} <= roles)
        live_collaborate = [
            row for row in manifest["artifacts"].values()
            if row["path"] == f"docs/teamwork/cases/{case_id}/live/collaborate.md"
        ]
        self.assertEqual(len(live_collaborate), 1)
        self.assertTrue([
            row for row in manifest["artifacts"].values()
            if row["subtype"] == "collaborate"
            and row["path"].startswith(f"docs/teamwork/cases/{case_id}/history/live/")
        ])
        self.assertTrue(manifest["claims"])
        self.assertTrue((project / f"docs/teamwork/cases/{case_id}/plan.md").is_file())
        self.assertTrue((project / f"docs/teamwork/cases/{case_id}/decision.md").is_file())
        self.assertTrue((project / f"docs/teamwork/cases/{case_id}/live/collaborate.md").is_file())
        self.assertTrue((project / f"docs/teamwork/cases/{case_id}/live/goal.md").is_file())
        self.assertTrue((project / f"docs/teamwork/cases/{case_id}/reviews/{'73' * 32}.md").is_file())
        self.assertTrue((project / f"docs/teamwork/cases/{case_id}/reviews/{'73' * 32}-delta.md").is_file())
        self.assertTrue(list((project / f"docs/teamwork/cases/{case_id}/results").glob("a-*.md")))
        self.assertFalse((project / "docs/teamwork/plans").exists())
        self.assertFalse((project / "docs/teamwork/reports").exists())
        self.assertTrue(expected_paths)

    def test_legacy_v1_runtime_routes_are_no_longer_publicly_callable(self) -> None:
        project = self.make_legacy_project()
        before_index = (project / "docs/teamwork/index.json").read_bytes()
        retired_commands = [
            ("inspect", "--project-root", str(project)),
            ("schema", "create"),
            ("apply", "--project-root", str(project), "--request-json", "{}"),
            ("design-inspect", "--project-root", str(project)),
            ("design-schema", "create"),
            ("design-apply", "--project-root", str(project), "--request-json", "{}"),
            ("goal-inspect", "--project-root", str(project)),
            ("goal-schema", "acquire"),
            ("goal-apply", "--project-root", str(project), "--request-json", "{}"),
            ("artifact-inspect", "--project-root", str(project)),
            ("artifact-schema", "create"),
            ("artifact-apply", "--project-root", str(project), "--request-json", "{}"),
            ("collaborate-inspect", "--project-root", str(project)),
            ("collaborate-schema", "create"),
            ("collaborate-apply", "--project-root", str(project), "--request-json", "{}"),
        ]
        for command in retired_commands:
            with self.subTest(command=command[0]):
                result = self.run_pkg(self.transaction_cli, *command, check=False)
                self.assertNotEqual(result.returncode, 0)

        self.assertEqual((project / "docs/teamwork/index.json").read_bytes(), before_index)
        self.assertFalse((project / "docs/teamwork/plans").exists())
        self.assertEqual(json.loads(before_index)["schema_version"], 1)

    def test_full_legacy_migration_cutover_recovery_cleanup_and_post_cutover_guards(self) -> None:
        project = self.make_legacy_project()
        claude_before = tree_fingerprint(project, ".claude")
        baseline_bytes = {
            path.relative_to(project).as_posix(): path.read_bytes()
            for path in (project / "docs/teamwork").rglob("*")
            if path.is_file()
        }

        approve_request = self.migration_request(project, "approve-baseline")
        if self.helper_cli.exists():
            helper_before = self.json_pkg(self.helper_cli, "request-inputs", "--project-root", str(project))
            self.assertEqual(helper_before["classification"]["mode"], "legacy-v1")
            self.assertEqual(helper_before["baseline"]["baseline_digest"], approve_request["baseline_digest"])

        approved = self.migration_apply(project, approve_request)
        self.assertEqual(approved["phase"], "baseline_approved")
        migration_id = approved["migration_id"]
        baseline_digest = approve_request["baseline_digest"]

        archived = self.migration_apply(project, self.migration_request(project, "materialize-archive"))
        self.assertEqual(archived["phase"], "archive_durable")
        archive_manifest_path = project / f".teamwork/cold-archive/v1/manifests/{migration_id}.json"
        archive_manifest = json.loads(archive_manifest_path.read_text(encoding="utf-8"))
        object_by_source = {row["source_path"]: row for row in archive_manifest["objects"]}
        self.assertEqual(set(object_by_source), set(baseline_bytes))
        for source_path, expected_bytes in baseline_bytes.items():
            row = object_by_source[source_path]
            object_path = project / row["object_path"]
            self.assertTrue(object_path.is_file())
            self.assertEqual(object_path.stat().st_mode & 0o777, 0o444)
            self.assertEqual(object_path.read_bytes(), expected_bytes)
            self.assertEqual(row["sha256"], sha256_bytes(expected_bytes))
            self.assertEqual(row["mode"], (project / source_path).stat().st_mode & 0o777)

        candidate = self.migration_apply(project, self.migration_request(project, "prepare-candidate"))
        self.assertEqual(candidate["phase"], "candidate_validated")
        restore = self.migration_apply(project, self.migration_request(project, "restore-drill"))
        self.assertEqual(restore["phase"], "candidate_validated")
        restore_report = json.loads(
            (project / f".teamwork/runtime/migrations/{migration_id}/restore-drill/report.json").read_text(encoding="utf-8")
        )
        self.assertEqual(restore_report["status"], "passed")
        self.assertEqual(restore_report["checked_objects"], len(baseline_bytes))

        cutover_request = self.phase_request(
            "cutover",
            migration_id,
            baseline_digest,
            cutover_authority="I authorize Teamwork memory cutover",
        )
        interrupted = self.migration_apply(
            project,
            cutover_request,
            env={"TEAMWORK_MIGRATION_FAILPOINT": "after-old-tree-renamed"},
            check=False,
        )
        self.assertEqual(interrupted["category"], "INDETERMINATE")

        recovered = self.migration_apply(project, cutover_request)
        self.assertEqual(recovered["phase"], "committed")
        self.assertEqual(json.loads((project / "docs/teamwork/index.json").read_text(encoding="utf-8"))["schema_version"], 2)
        self.assertFalse((project / "docs/teamwork/current.md").exists())
        self.assertFalse((project / "docs/teamwork/README.md").exists())
        self.assertEqual(claude_before, tree_fingerprint(project, ".claude"))

        post_cutover = self.run_pkg(
            self.transaction_cli,
            "artifact-inspect",
            "--project-root",
            str(project),
            check=False,
        )
        self.assertNotEqual(post_cutover.returncode, 0)
        self.assertFalse((project / "docs/teamwork/plans").exists())

        cleanup = self.migration_apply(project, self.phase_request("cleanup", migration_id, baseline_digest))
        self.assertEqual(cleanup["phase"], "cleanup_complete")
        journal = json.loads((project / f".teamwork/runtime/migrations/{migration_id}/journal.json").read_text(encoding="utf-8"))
        self.assertEqual(journal["cleanup"], "complete")
        self.assertEqual(claude_before, tree_fingerprint(project, ".claude"))

    def test_installed_helper_migrate_reports_case_v2_cleanup_complete(self) -> None:
        project = self.make_legacy_project("helper-terminal-mode")

        result = self.run_pkg(
            self.helper_cli,
            "migrate",
            "--project-root",
            str(project),
            "--cutover",
            "--cleanup",
        )
        payload = json.loads(result.stdout)

        self.assertEqual(payload["mode"], "case-v2")
        self.assertEqual(payload["phase"], "cleanup_complete")
        installed = json.loads((project / "docs/teamwork/index.json").read_text(encoding="utf-8"))
        self.assertEqual(installed["schema_version"], 2)
        self.assertEqual(installed["migration"]["phase"], "cleanup_complete")

    def test_installed_helper_resume_cleanup_rejects_hybrid_terminal_readback(self) -> None:
        project = self.make_legacy_project("helper-hybrid-terminal")
        migrated = self.run_pkg(
            self.helper_cli,
            "migrate",
            "--project-root",
            str(project),
            "--cutover",
            "--cleanup",
        )
        migration_id = json.loads(migrated.stdout)["migration_id"]
        self.assertEqual(json.loads(migrated.stdout)["phase"], "cleanup_complete")

        index_path = project / "docs/teamwork/index.json"
        index = json.loads(index_path.read_text(encoding="utf-8"))
        index["last_updated"] = FIXED_DAY
        index["active"] = {"current": "docs/teamwork/current.md", "design": None, "plan": None, "progress": None, "report": None, "results": [], "collaborate": None}
        index["entries"] = []
        index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        outside = self.tmp / "helper-hybrid-terminal-outside"
        outside.mkdir()
        before = tree_fingerprint(project, ".")

        failed = self.run_pkg(
            self.helper_cli,
            "resume",
            "--project-root",
            str(project),
            "--migration-id",
            migration_id,
            "--cleanup",
            check=False,
        )

        self.assertNotEqual(failed.returncode, 0)
        self.assertIn("case-v2", failed.stderr)
        self.assertEqual(tree_fingerprint(project, "."), before)
        self.assertEqual(list(outside.iterdir()), [])

    def test_hybrid_and_tampered_archive_fail_before_mutating_project(self) -> None:
        hybrid = self.make_legacy_project("hybrid-project")
        index_path = hybrid / "docs/teamwork/index.json"
        index = json.loads(index_path.read_text(encoding="utf-8"))
        index.update({"schema_version": 2, "active_cases": [], "claim_heads": [], "aliases": {}, "recent_cases": [], "migration": None})
        index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        before = tree_fingerprint(hybrid, ".")
        failed = self.run_pkg(
            self.transaction_cli,
            "case-inspect",
            "--project-root",
            str(hybrid),
            check=False,
        )
        self.assertNotEqual(failed.returncode, 0)
        self.assertIn("hybrid", failed.stderr)
        self.assertEqual(before, tree_fingerprint(hybrid, "."))

        project = self.make_legacy_project("tampered-archive-project")
        approve_request = self.migration_request(project, "approve-baseline")
        approved = self.migration_apply(project, approve_request)
        migration_id = approved["migration_id"]
        baseline_digest = approve_request["baseline_digest"]
        self.migration_apply(project, self.migration_request(project, "materialize-archive"))
        self.migration_apply(project, self.migration_request(project, "prepare-candidate"))

        object_path = next((project / ".teamwork/cold-archive/v1/objects/sha256").rglob("*"))
        while object_path.is_dir():
            object_path = next(object_path.rglob("*"))
        os.chmod(object_path, 0o644)
        object_path.write_bytes(object_path.read_bytes() + b"tamper")
        os.chmod(object_path, 0o444)
        before_tampered = tree_fingerprint(project, ".")
        failed_restore = self.migration_apply(
            project,
            self.phase_request("restore-drill", migration_id, baseline_digest),
            check=False,
        )
        self.assertEqual(failed_restore["category"], "INDETERMINATE")
        self.assertEqual(before_tampered, tree_fingerprint(project, "."))


if __name__ == "__main__":
    unittest.main()
