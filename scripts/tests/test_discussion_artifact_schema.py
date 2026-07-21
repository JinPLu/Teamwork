from __future__ import annotations

import html
import json
import re
import runpy
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "scripts/discussion-transaction.py"
CONTRACT = runpy.run_path(str(CLI), run_name="teamwork_discussion_schema_v2_contract")


class DiscussionArtifactSchemaV2Tests(unittest.TestCase):
    def question(self, question_id: str, *, title: str, status: str, depends_on: list[str] | None = None) -> dict[str, object]:
        resolution = None
        if status == "closed":
            resolution = {"kind": "selected", "option_id": "yes"}
        elif status == "rejected":
            resolution = {"kind": "rejected", "reason": "Rejected by a source-backed dependency."}
        return {
            "id": question_id,
            "title": title,
            "level": "goal" if question_id == "Q1" else "boundary",
            "status": status,
            "prompt": f"Long prompt for {question_id} that must stay outside the graph label and remain readable exactly once.",
            "options": [
                {"id": "yes", "label": f"Use {question_id}", "tradeoff": f"Tradeoff for {question_id} yes"},
                {"id": "no", "label": f"Skip {question_id}", "tradeoff": f"Tradeoff for {question_id} no"},
            ],
            "recommendation": "yes",
            "largest_downside": f"Largest downside for {question_id} remains readable but not in the graph.",
            "why_critical": f"Critical reason for {question_id} changes the selected outcome.",
            "blocks": [f"gate-{question_id.lower()}"],
            "depends_on": depends_on or [],
            "closure_signal": f"Closure signal for {question_id}",
            "resolution": resolution,
        }

    def state(self, **overrides: object) -> dict[str, object]:
        state: dict[str, object] = {
            "schema_version": 2,
            "artifact_type": "discussion",
            "slug": "layered-route",
            "title": "Layered route",
            "updated": "2026-07-20",
            "status": "active",
            "superseded_by": None,
            "goal": "Choose the durable discussion route.",
            "current_branch": "Ask independent material questions.",
            "return_path": "Resume at the current batch.",
            "blockers": ["Host mapping must remain stable."],
            "convergence": "All current questions close with one atomic update.",
            "key_evidence": ["The renderer uses the structured frontier."],
            "frontier": [
                self.question("Q1", title="Global route", status="closed"),
                self.question("Q2", title="Boundary choice", status="current", depends_on=["Q1"]),
                self.question("Q3", title="Renderer proof", status="current", depends_on=["Q1"]),
            ],
            "current_batch": ["Q2", "Q3"],
        }
        state.update(overrides)
        return state

    def render(self, state: dict[str, object] | None = None) -> str:
        return CONTRACT["render_discussion_artifact"](state or self.state())

    def mermaid(self, text: str) -> str:
        return text.split("```mermaid\n", 1)[1].split("\n```", 1)[0]

    def fallback(self, text: str) -> str:
        return text.split("Plain-text fallback:\n\n", 1)[1].split("\n\n## Readable state", 1)[0]

    def decoded_labels(self, mermaid: str) -> list[str]:
        labels = []
        for line in mermaid.splitlines():
            match = re.search(r'\["(.+?)"\]', line)
            if match:
                labels.append(html.unescape(match.group(1)))
        return labels

    def test_v2_renderer_keeps_graph_and_fallback_concise(self) -> None:
        state = self.state()
        rendered = self.render(state)
        self.assertEqual(CONTRACT["validate_discussion_artifact"](rendered), state)
        graph = self.mermaid(rendered)
        fallback = self.fallback(rendered)
        for label in self.decoded_labels(graph):
            self.assertLessEqual(len(label), 48)
            self.assertNotIn(";", label)
        for item in state["frontier"]:
            self.assertIn(f"{item['id']} · {item['title']} · {item['status']}", graph)
            self.assertEqual(rendered.split("## Discussion state", 1)[0].count(str(item["prompt"])), 1)
            self.assertNotIn(str(item["prompt"]), graph)
            self.assertNotIn(str(item["prompt"]), fallback)
            self.assertNotIn(str(item["largest_downside"]), graph)
            self.assertNotIn(str(item["why_critical"]), graph)

    def test_v1_discussion_artifact_still_validates_through_frozen_renderer(self) -> None:
        state = {
            "schema_version": 1,
            "artifact_type": "discussion",
            "slug": "legacy-route",
            "title": "Legacy route",
            "updated": "2026-07-19",
            "status": "active",
            "superseded_by": None,
            "goal": "Preserve old records.",
            "current_branch": "Read the legacy current file.",
            "settled": ["Legacy renderer remains exact."],
            "still_open": ["Migration needs explicit enrichment."],
            "return_path": "Resume at enrichment.",
            "blockers": [],
            "convergence": "The old artifact validates unchanged.",
            "key_evidence": ["Schema version dispatch selected v1."],
        }
        rendered = self.render(state)
        validated = CONTRACT["validate_discussion_artifact"](rendered)
        self.assertEqual(validated["schema_version"], 1)
        self.assertIn("Still open:", rendered)

    def test_frontier_state_invariants_reject_invalid_batches(self) -> None:
        valid = self.state()
        dependent = json.loads(json.dumps(valid))
        dependent["frontier"][2]["depends_on"] = ["Q2"]
        with self.assertRaises(CONTRACT["TransactionError"]):
            self.render(dependent)

        over_limit = json.loads(json.dumps(valid))
        over_limit["frontier"].append(self.question("Q4", title="Extra", status="current", depends_on=["Q1"]))
        over_limit["frontier"].append(self.question("Q5", title="Fourth current", status="current", depends_on=["Q1"]))
        over_limit["current_batch"] = ["Q2", "Q3", "Q4", "Q5"]
        with self.assertRaises(CONTRACT["TransactionError"]):
            self.render(over_limit)

        bad_recommendation = json.loads(json.dumps(valid))
        bad_recommendation["frontier"][1]["recommendation"] = "missing"
        with self.assertRaises(CONTRACT["TransactionError"]):
            self.render(bad_recommendation)

    def test_transition_rejects_partial_answer_and_mutable_open_without_delta_reason(self) -> None:
        old = self.state()
        proposed = json.loads(json.dumps(old))
        proposed["frontier"][1]["status"] = "closed"
        proposed["frontier"][1]["resolution"] = {"kind": "selected", "option_id": "yes"}
        proposed["current_batch"] = ["Q3"]
        with self.assertRaises(CONTRACT["TransactionError"]):
            CONTRACT["validate_discussion_transition"](old, proposed, {"schema_version": 2})

        open_old = self.state(
            frontier=[
                self.question("Q1", title="Global route", status="closed"),
                {**self.question("Q2", title="Boundary choice", status="open", depends_on=["Q1"])},
                self.question("Q3", title="Renderer proof", status="current", depends_on=["Q1"]),
            ],
            current_batch=["Q3"],
        )
        open_new = json.loads(json.dumps(open_old))
        open_new["frontier"][1]["prompt"] = "Changed prompt after new evidence."
        with self.assertRaises(CONTRACT["TransactionError"]):
            CONTRACT["validate_discussion_transition"](open_old, open_new, {"schema_version": 2})


if __name__ == "__main__":
    unittest.main()
