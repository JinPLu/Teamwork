from __future__ import annotations

import hashlib
import json
import runpy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "scripts/discussion-transaction.py"
TEMPLATES = ROOT / "templates/teamwork-memory"
CONTRACT = runpy.run_path(str(CLI), run_name="teamwork_discussion_migration_contract")


class DiscussionIndexSafetyTests(unittest.TestCase):
    def initialized_project(self, temporary: str) -> Path:
        project = Path(temporary) / "project"
        memory = project / "docs/teamwork"
        memory.mkdir(parents=True)
        for name in ("index.json", "current.md", "README.md"):
            (memory / name).write_bytes((TEMPLATES / name).read_bytes())
        return project

    def command(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CLI), *arguments],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_ordinary_templates_have_no_discussion_anchor_or_mirror(self) -> None:
        index = json.loads((TEMPLATES / "index.json").read_text(encoding="utf-8"))
        self.assertNotIn("discussion", index["active"])
        combined = "\n".join(
            (TEMPLATES / name).read_text(encoding="utf-8")
            for name in ("index.json", "current.md", "README.md")
        ).lower()
        self.assertNotIn("active discussion", combined)
        self.assertNotIn("active_discussion", combined)
        self.assertNotIn("discussion/current.md", (TEMPLATES / "index.json").read_text(encoding="utf-8"))

    def test_discussion_never_initializes_ordinary_memory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "uninitialized"
            project.mkdir()
            result = self.command("inspect", "--project-root", str(project))
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((project / "docs").exists())

    def test_unindexed_archive_never_becomes_active_and_ordinary_pointer_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = self.initialized_project(temporary)
            discussion = project / "docs/teamwork/discussion"
            discussion.mkdir()
            (discussion / "2026-07-19-rogue.md").write_text("# rogue\n", encoding="utf-8")
            inspected = self.command("inspect", "--project-root", str(project))
            self.assertEqual(inspected.returncode, 0, inspected.stderr)
            self.assertIsNone(json.loads(inspected.stdout)["active"])

            index_path = project / "docs/teamwork/index.json"
            index = json.loads(index_path.read_text(encoding="utf-8"))
            index["active"]["current"] = "docs/teamwork/discussion/current.md"
            index_path.write_text(json.dumps(index), encoding="utf-8")
            validated = self.command("artifact-index-validate", "--project-root", str(project))
            self.assertNotEqual(validated.returncode, 0)
            self.assertEqual(json.loads(validated.stderr)["category"], "PREWRITE_SAFE")

    def legacy_artifact(self, *, title: str, status: str, updated: str) -> str:
        return "\n".join(
            (
                "Artifact Type: discussion",
                f"Status: {status}",
                "Authority: supporting",
                f"Last Updated: {updated}",
                "",
                f"# {title}",
                "",
                "## Goal",
                "",
                "Preserve the decision.",
                "",
                "## Current branch",
                "",
                "Select the recovery route.",
                "",
                "## Settled",
                "",
                "- One existing constraint.",
                "",
                "## Still open",
                "",
                "- One remaining choice." if status == "active" else "- None",
                "",
                "## Return path",
                "",
                "Return to the named choice.",
                "",
                "## Blockers",
                "",
                "- none",
                "",
                "## Convergence",
                "",
                "A verified decision.",
                "",
                "## Key evidence",
                "",
                "- Existing source snapshot.",
                "",
            )
        )

    def test_pure_v2_migration_maps_one_active_record_and_keeps_closed_archives(self) -> None:
        active = "docs/teamwork/discussion/2026-07-19-live-route.md"
        closed = "docs/teamwork/discussion/2026-07-18-closed-route.md"
        index = {
            "entries": [
                {"kind": "discussion", "path": active, "title": "Live route", "status": "active", "currentness": "current"},
                {"kind": "discussion", "path": closed, "title": "Closed route", "status": "accepted", "currentness": "historical"},
            ],
            "active": {"discussion": active},
        }
        plan = CONTRACT["plan_v342_discussion_migration"](
            json.dumps(index),
            {
                active: self.legacy_artifact(title="Live route", status="active", updated="2026-07-19"),
                closed: self.legacy_artifact(title="Closed route", status="accepted", updated="2026-07-18"),
            },
        )
        self.assertEqual(plan["schema_version"], 2)
        self.assertEqual(plan["active_path"], "docs/teamwork/discussion/current.md")
        self.assertEqual(plan["deletes"], [active])
        self.assertEqual(set(plan["writes"]), {"docs/teamwork/discussion/current.md", closed})
        state = CONTRACT["validate_discussion_artifact"](plan["writes"]["docs/teamwork/discussion/current.md"])
        self.assertEqual(state["migration_source"]["path"], active)
        self.assertIn("Artifact Type: discussion", state["migration_source"]["source_text"])

    def test_v342_migration_encodes_multiline_legacy_scalars_injectively_and_preserves_raw_source(self) -> None:
        path = "docs/teamwork/discussion/2026-07-19-live-route.md"
        index = {
            "entries": [
                {"kind": "discussion", "path": path, "title": "Live route", "status": "active", "currentness": "current"},
            ],
            "active": {"discussion": path},
        }
        legacy = self.legacy_artifact(title="Live route", status="active", updated="2026-07-19")
        legacy = (
            legacy.replace("Preserve the decision.", "Preserve the decision.\nKeep the recovery meaning visible.")
            .replace("Select the recovery route.", "Select the recovery route.\nDo not replay an unchanged branch.")
            .replace("Return to the named choice.", "Return to the named choice.\nResume from the direct evidence.")
            .replace("A verified decision.", "A verified decision.\nThe acceptance signal must be direct.")
        )

        plan = CONTRACT["plan_v342_discussion_migration"](json.dumps(index), {path: legacy})
        state = CONTRACT["validate_discussion_artifact"](plan["writes"]["docs/teamwork/discussion/current.md"])

        self.assertEqual(state["goal"], r"Preserve the decision.\nKeep the recovery meaning visible.")
        self.assertEqual(state["current_branch"], r"Select the recovery route.\nDo not replay an unchanged branch.")
        self.assertEqual(state["return_path"], r"Return to the named choice.\nResume from the direct evidence.")
        self.assertEqual(state["convergence"], r"A verified decision.\nThe acceptance signal must be direct.")
        self.assertEqual(
            CONTRACT["_decode_legacy_scalar"](state["goal"]),
            ["Preserve the decision.", "Keep the recovery meaning visible."],
        )
        self.assertEqual(state["migration_source"]["source_text"], legacy)

        literal_delimiter = legacy.replace(
            "Preserve the decision.\nKeep the recovery meaning visible.",
            "Preserve the decision. / Keep the recovery meaning visible.",
        )
        delimiter_state = CONTRACT["validate_discussion_artifact"](
            CONTRACT["plan_v342_discussion_migration"](json.dumps(index), {path: literal_delimiter})["writes"]["docs/teamwork/discussion/current.md"]
        )
        self.assertEqual(delimiter_state["goal"], "Preserve the decision. / Keep the recovery meaning visible.")
        self.assertNotEqual(delimiter_state["goal"], state["goal"])

        literal_escape = legacy.replace(
            "Preserve the decision.\nKeep the recovery meaning visible.",
            r"A literal \n marker remains content.",
        )
        escaped_state = CONTRACT["validate_discussion_artifact"](
            CONTRACT["plan_v342_discussion_migration"](json.dumps(index), {path: literal_escape})["writes"]["docs/teamwork/discussion/current.md"]
        )
        self.assertEqual(escaped_state["goal"], r"A literal \\n marker remains content.")
        self.assertEqual(CONTRACT["_decode_legacy_scalar"](escaped_state["goal"]), [r"A literal \n marker remains content."])

        for unsafe in ("\x0bLeading VT", "Trailing FF\x0c", "Trailing FS\x1c"):
            with self.subTest(unsafe=repr(unsafe)):
                unsafe_legacy = legacy.replace(
                    "Preserve the decision.\nKeep the recovery meaning visible.", unsafe
                )
                with self.assertRaises(CONTRACT["TransactionError"]):
                    CONTRACT["plan_v342_discussion_migration"](json.dumps(index), {path: unsafe_legacy})

    def test_v342_migration_rejects_unsafe_controls_in_heading_title_and_date_before_matching(self) -> None:
        path = "docs/teamwork/discussion/2026-07-19-control-route.md"
        index = {
            "entries": [
                {"kind": "discussion", "path": path, "title": "Control route", "status": "active", "currentness": "current"},
            ],
            "active": {"discussion": path},
        }
        legacy = self.legacy_artifact(title="Control route", status="active", updated="2026-07-19")
        variants = {
            "tabbed_heading": legacy.replace("## Goal", "##\tGoal\t\x0b"),
            "title": legacy.replace("# Control route", "# Control\x0b route"),
            "date": legacy.replace("Last Updated: 2026-07-19", "Last Updated: 2026-07-19\x0b"),
        }
        for label, unsafe_legacy in variants.items():
            with self.subTest(label=label):
                with self.assertRaises(CONTRACT["TransactionError"]):
                    CONTRACT["plan_v342_discussion_migration"](json.dumps(index), {path: unsafe_legacy})

    def test_v342_migration_reads_crlf_scalars_and_continue_here_without_fallback(self) -> None:
        path = "docs/teamwork/discussion/2026-07-19-crlf-route.md"
        index = {
            "entries": [
                {"kind": "discussion", "path": path, "title": "CRLF route", "status": "active", "currentness": "current"},
            ],
            "active": {"discussion": path},
        }
        legacy = self.legacy_artifact(title="CRLF route", status="active", updated="2026-07-19")
        legacy = (
            legacy.replace("Preserve the decision.", "Goal line one.\tkeeps tab formatting.\nGoal line two.")
            .replace("Select the recovery route.", "Branch line one.\nBranch line two.")
            .replace("Return to the named choice.", "Return line one.\nReturn line two.")
            .replace("A verified decision.", "Convergence line one.\nConvergence line two.")
            .replace("\n", "\r\n")
        )

        state = CONTRACT["validate_discussion_artifact"](
            CONTRACT["plan_v342_discussion_migration"](json.dumps(index), {path: legacy})["writes"]["docs/teamwork/discussion/current.md"]
        )
        self.assertEqual(state["goal"], r"Goal line one. keeps tab formatting.\nGoal line two.")
        self.assertEqual(state["current_branch"], r"Branch line one.\nBranch line two.")
        self.assertEqual(state["return_path"], r"Return line one.\nReturn line two.")
        self.assertEqual(state["convergence"], r"Convergence line one.\nConvergence line two.")
        self.assertNotIn("none recorded", {state["goal"], state["current_branch"], state["return_path"], state["convergence"]})
        self.assertIn("\t", legacy)
        self.assertEqual(state["migration_source"]["source_text"], legacy)

        continue_path = "docs/teamwork/discussion/2026-07-19-continue-route.md"
        continue_index = {
            "entries": [
                {"kind": "discussion", "path": continue_path, "title": "Continue route", "status": "active", "currentness": "current"},
            ],
            "active": {"discussion": continue_path},
        }
        continue_legacy = self.legacy_artifact(title="Continue route", status="active", updated="2026-07-19")
        continue_legacy = continue_legacy.replace(
            "## Return path\n\nReturn to the named choice.\n\n",
            "## Continue here\n\nContinue line one.\nContinue line two.\n\n",
        ).replace("\n", "\r\n")
        continue_state = CONTRACT["validate_discussion_artifact"](
            CONTRACT["plan_v342_discussion_migration"](json.dumps(continue_index), {continue_path: continue_legacy})["writes"]["docs/teamwork/discussion/current.md"]
        )
        self.assertEqual(continue_state["return_path"], r"Continue line one.\nContinue line two.")
        self.assertNotEqual(continue_state["return_path"], "none recorded")
        self.assertEqual(continue_state["migration_source"]["source_text"], continue_legacy)

    def test_v342_migration_accepts_v3_horizontal_tabs_and_immediate_section_bodies(self) -> None:
        for newline, suffix in (("\n", "lf"), ("\r\n", "crlf")):
            with self.subTest(newline=repr(newline)):
                path = f"docs/teamwork/discussion/2026-07-18-tabbed-{suffix}.md"
                index = {
                    "entries": [
                        {
                            "kind": "discussion",
                            "path": path,
                            "title": "Index fallback title",
                            "status": "active",
                            "currentness": "current",
                        },
                    ],
                    "active": {"discussion": path},
                }
                legacy = self.legacy_artifact(title="Tabbed legacy title", status="active", updated="2026-07-19")
                legacy = (
                    legacy.replace("Last Updated: 2026-07-19", "Last\tUpdated\t:\t2026-07-20\t")
                    .replace("# Tabbed legacy title", "#\tTabbed legacy title\t")
                    .replace(
                        "## Goal\n\nPreserve the decision.\n\n",
                        "##\tGoal\t\nGoal follows its heading immediately.\n\n",
                    )
                    .replace(
                        "## Return path\n\nReturn to the named choice.\n\n",
                        "## Return\tpath\t\n\t\nReturn follows a tab-only separator.\n\n",
                    )
                    .replace("\n", newline)
                )

                state = CONTRACT["validate_discussion_artifact"](
                    CONTRACT["plan_v342_discussion_migration"](json.dumps(index), {path: legacy})["writes"]["docs/teamwork/discussion/current.md"]
                )
                self.assertEqual(state["title"], "Tabbed legacy title")
                self.assertEqual(state["updated"], "2026-07-20")
                self.assertEqual(state["goal"], "Goal follows its heading immediately.")
                self.assertEqual(state["return_path"], "Return follows a tab-only separator.")
                self.assertNotIn("none recorded", {state["goal"], state["return_path"]})
                self.assertEqual(state["migration_source"]["source_text"], legacy)
                self.assertEqual(state["migration_source"]["sha256"], hashlib.sha256(legacy.encode("utf-8")).hexdigest())

    def test_v342_migration_accepts_tabbed_continue_here_with_immediate_body(self) -> None:
        for newline, suffix in (("\n", "lf"), ("\r\n", "crlf")):
            with self.subTest(newline=repr(newline)):
                path = f"docs/teamwork/discussion/2026-07-19-continue-tabs-{suffix}.md"
                index = {
                    "entries": [
                        {
                            "kind": "discussion",
                            "path": path,
                            "title": "Continue route",
                            "status": "active",
                            "currentness": "current",
                        },
                    ],
                    "active": {"discussion": path},
                }
                legacy = self.legacy_artifact(title="Continue route", status="active", updated="2026-07-19")
                legacy = legacy.replace(
                    "## Return path\n\nReturn to the named choice.\n\n",
                    "##\tContinue\there\t\nContinue follows its heading immediately.\n\n",
                ).replace("\n", newline)

                state = CONTRACT["validate_discussion_artifact"](
                    CONTRACT["plan_v342_discussion_migration"](json.dumps(index), {path: legacy})["writes"]["docs/teamwork/discussion/current.md"]
                )
                self.assertEqual(state["return_path"], "Continue follows its heading immediately.")
                self.assertNotEqual(state["return_path"], "none recorded")
                self.assertEqual(state["migration_source"]["source_text"], legacy)
                self.assertEqual(state["migration_source"]["sha256"], hashlib.sha256(legacy.encode("utf-8")).hexdigest())

    def test_migration_rejects_unknown_or_incomplete_artifact_inputs(self) -> None:
        path = "docs/teamwork/discussion/2026-07-19-live-route.md"
        index = {"entries": [{"kind": "discussion", "path": path, "title": "Live", "status": "active", "currentness": "current"}], "active": {"discussion": path}}
        with self.assertRaises(CONTRACT["TransactionError"]):
            CONTRACT["plan_v342_discussion_migration"](json.dumps(index), {"docs/teamwork/discussion/2026-07-19-extra.md": "x"})


if __name__ == "__main__":
    unittest.main()
