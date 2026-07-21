from __future__ import annotations

import copy
import json
import runpy
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "scripts/discussion-transaction.py"
TEMPLATES = ROOT / "templates/teamwork-memory"
CONTRACT = runpy.run_path(str(CLI), run_name="teamwork_currentness_contract")


class ActiveArtifactCurrentnessTests(unittest.TestCase):
    def design_state(self, **overrides: object) -> dict[str, object]:
        state: dict[str, object] = {
            "schema_version": 2,
            "artifact_type": "design",
            "slug": "architecture",
            "title": "Current architecture",
            "updated": "2026-07-19",
            "status": "current",
            "superseded_by": None,
            "evidence_waves": ["Local evidence"],
            "alternatives": ["Selected route", "Legacy route"],
            "exclusions": ["Nested route"],
            "challenge_result": "survives",
            "decision_frontier": [],
            "settled": ["One selected direction"],
            "open_items": [],
            "plan_handoff": "Plan receives the selected direction.",
            "review_handoff": "Review receives the acceptance evidence.",
            "decision_rule": "Prefer coherent ownership.",
            "recommendation": "Use the selected route.",
            "largest_downside": "Migration requires care.",
            "rejected_alternatives": [{"option": "Legacy route", "reason": "It retains recursive ownership."}],
            "residual_uncertainty": "No material dissent remains.",
        }
        state.update(overrides)
        return state

    def goal_state(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "artifact_type": "goal",
            "slug": "finish-v4",
            "title": "Finish v4",
            "objective": "Finish the v4 change.",
            "scope": {"included": ["Target work"]},
            "protected_boundaries": ["No release."],
            "invariants": ["Preserve compatibility."],
            "success_signal": "Real suite passes.",
            "budget": {"token_budget": 1},
            "hard_stops": ["No authority."],
            "status": "active",
            "current_unmet_claim": "Real suite has not passed.",
            "started_at": "2026-07-19",
            "updated": "2026-07-19",
            "next_strategy": "Run the real suite.",
            "attempts": [],
            "state_revision": 1,
            "closure": None,
        }

    def entry(self, kind: str, path: str, title: str, updated: str) -> dict[str, object]:
        return {
            "topic": kind,
            "kind": kind,
            "title": title,
            "status": "accepted" if kind != "progress" else "active",
            "currentness": "current",
            "authority": "canonical",
            "path": path,
            "linked": [],
            "evidence_paths": [path],
            "supersedes": [],
            "search_keys": [kind],
            "updated": updated,
            "summary": f"Current {kind} artifact.",
        }

    def project_and_index(self) -> tuple[tempfile.TemporaryDirectory[str], Path, dict[str, object]]:
        temporary = tempfile.TemporaryDirectory()
        project = Path(temporary.name) / "project"
        memory = project / "docs/teamwork"
        memory.mkdir(parents=True)
        for name in ("index.json", "current.md", "README.md"):
            (memory / name).write_bytes((TEMPLATES / name).read_bytes())
        index = json.loads((memory / "index.json").read_text(encoding="utf-8"))
        return temporary, project, index

    def valid_index_and_targets(self) -> tuple[tempfile.TemporaryDirectory[str], Path, dict[str, object]]:
        temporary, project, index = self.project_and_index()
        memory = project / "docs/teamwork"
        design = self.design_state()
        goal = self.goal_state()
        design_path = CONTRACT["design_path"](design)
        goal_path = CONTRACT["goal_path"](goal)
        plan_path = "docs/teamwork/plans/2026-07-19-implementation.md"
        for relative, text in (
            (design_path, CONTRACT["render_design_artifact"](design)),
            (goal_path, CONTRACT["render_goal_artifact"](goal)),
            (plan_path, "Artifact Type: plan\nLast Updated: 2026-07-19\n\n# Current implementation\n"),
        ):
            path = project / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        index["active"].update({"design": design_path, "plan": plan_path, "progress": goal_path})
        index["entries"].extend(
            [
                self.entry("design", design_path, design["title"], design["updated"]),
                self.entry("plan", plan_path, "Current implementation", "2026-07-19"),
                self.entry("progress", goal_path, goal["title"], goal["updated"]),
            ]
        )
        (memory / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
        return temporary, project, index

    def test_template_has_no_discussion_or_legacy_goal_pointer(self) -> None:
        index = json.loads((TEMPLATES / "index.json").read_text(encoding="utf-8"))
        self.assertNotIn("discussion", index["active"])
        self.assertNotIn("goal", index["active"])
        self.assertEqual(CONTRACT["parse_index"](json.dumps(index))["active"]["progress"], None)

    def test_active_targets_must_exist_parse_and_agree_with_index_metadata(self) -> None:
        temporary, project, index = self.valid_index_and_targets()
        try:
            CONTRACT["validate_currentness"](project, CONTRACT["parse_index"](json.dumps(index)))
        finally:
            temporary.cleanup()

    def test_missing_target_and_artifact_drift_fail_closed(self) -> None:
        temporary, project, index = self.valid_index_and_targets()
        try:
            broken = copy.deepcopy(index)
            missing = project / broken["active"]["design"]
            missing.unlink()
            with self.assertRaises(CONTRACT["TransactionError"]):
                CONTRACT["validate_currentness"](project, CONTRACT["parse_index"](json.dumps(broken)))

            # Restore the target and make its title disagree with the index.
            state = self.design_state(title="Different title")
            target = project / broken["active"]["design"]
            target.write_text(CONTRACT["render_design_artifact"](state), encoding="utf-8")
            with self.assertRaisesRegex(CONTRACT["TransactionError"], "active.design artifact"):
                CONTRACT["validate_currentness"](project, CONTRACT["parse_index"](json.dumps(broken)))
        finally:
            temporary.cleanup()

    def test_null_or_ambiguous_active_pointer_cannot_hide_current_artifacts(self) -> None:
        temporary, _project, index = self.valid_index_and_targets()
        try:
            null = copy.deepcopy(index)
            null["active"]["design"] = None
            with self.assertRaisesRegex(CONTRACT["TransactionError"], "active.design is null"):
                CONTRACT["parse_index"](json.dumps(null))

            ambiguous = copy.deepcopy(index)
            duplicate = copy.deepcopy(ambiguous["entries"][-3])
            duplicate["topic"] = "other"
            duplicate["path"] = "docs/teamwork/design/2026-07-19-other.md"
            duplicate["evidence_paths"] = [duplicate["path"]]
            ambiguous["entries"].append(duplicate)
            with self.assertRaisesRegex(CONTRACT["TransactionError"], "active.design is ambiguous"):
                CONTRACT["parse_index"](json.dumps(ambiguous))
        finally:
            temporary.cleanup()

    def test_discussion_or_goal_mirror_key_is_rejected(self) -> None:
        temporary, _project, index = self.valid_index_and_targets()
        try:
            for key in ("discussion", "goal"):
                legacy = copy.deepcopy(index)
                legacy["active"][key] = None
                with self.subTest(key=key):
                    with self.assertRaises(CONTRACT["TransactionError"]):
                        CONTRACT["parse_index"](json.dumps(legacy))
        finally:
            temporary.cleanup()


if __name__ == "__main__":
    unittest.main()
