from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from teamwork_tooling import live_canary
from teamwork_tooling.semantic_review import trajectory_sha256


CASES = sorted(live_canary.FROZEN_GOLD_CASES | live_canary.FROZEN_CONTROL_CASES)
RUBRIC = json.loads((ROOT / live_canary.DEFAULT_PAIRWISE_RUBRIC).read_text(encoding="utf-8"))


class PairwiseComparisonTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.arms: list[tuple[str, Path]] = []
        for arm_id in ("opaque-one", "opaque-two"):
            directory = self.base / arm_id
            directory.mkdir()
            records = []
            links = []
            for case_id in CASES:
                record = {
                    "schema_version": 5,
                    "record_type": "teamwork_live_trajectory",
                    "run_id": f"{arm_id}-{case_id}-r1",
                    "case_id": case_id,
                    "repeat_index": 1,
                    "category": "test",
                    "unscored_annotations": {"expected": ["precise"]},
                    "status": "completed",
                    "execution_status": "completed",
                    "structural_status": "passed",
                    "model_provenance_status": "verified",
                    "final_output": f"neutral response {case_id} {len(records)}",
                    "turns": [{"final_output": f"turn response {case_id}"}],
                }
                records.append(record)
                links.append({"run_id": record["run_id"], "trajectory_sha256": trajectory_sha256(record)})
            (directory / live_canary.RAW_NAME).write_text(
                "".join(json.dumps(item) + "\n" for item in records), encoding="utf-8"
            )
            inventory_size = 20 if arm_id == "opaque-one" else 10
            (directory / live_canary.MANIFEST_NAME).write_text(json.dumps({
                "record_type": "teamwork_installed_canary_manifest",
                "trajectories": links,
                "inventory": [{
                    "path": "skills/example/SKILL.md",
                    "size": inventory_size,
                    "sha256": "a" * 64,
                }],
            }), encoding="utf-8")
            self.arms.append((arm_id, directory))
        self.review_dir = self.base / "comparison"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def arm_args(self) -> list[str]:
        result: list[str] = []
        for arm_id, directory in self.arms:
            result.extend(["--arm", f"{arm_id}={directory}"])
        return result

    def prepare(self) -> None:
        argv = [
            "compare", "prepare", "--review-dir", str(self.review_dir),
            *self.arm_args(), "--comparison-id", "private-dev-001",
            "--reviewer-id", "reviewer-x", "--reviewer-id", "reviewer-y",
            "--seed", "17", "--transition", "a-to-b", "--stage", "dev",
        ]
        self.assertEqual(live_canary.main(argv), 0)

    def write_reviews(self, candidate_better: bool = True) -> None:
        controller = json.loads((self.review_dir / live_canary.PAIRWISE_CONTROLLER_NAME).read_text(encoding="utf-8"))
        schedules = {(row["reviewer_id"], row["pair_id"]): row for row in controller["schedule"]}
        for reviewer in controller["reviewers"]:
            payload = json.loads((self.review_dir / live_canary.PAIRWISE_INPUTS_DIR / f"{reviewer}.json").read_text(encoding="utf-8"))
            judgments = []
            for pair in payload["pairs"]:
                row = schedules[(reviewer, pair["pair_id"])]
                if not candidate_better:
                    outcome = "TIE"
                else:
                    outcome = "LEFT_BETTER" if row["left_arm_id"] == "opaque-two" else "RIGHT_BETTER"
                judgments.append({
                    "pair_id": pair["pair_id"], "case_id": pair["case_id"],
                    "repeat_index": pair["repeat_index"],
                    "left_trajectory_sha256": pair["left_trajectory_sha256"],
                    "right_trajectory_sha256": pair["right_trajectory_sha256"],
                    "outcome": outcome,
                    "hard_gates": {
                        criterion["id"]: {"left": True, "right": True}
                        for criterion in RUBRIC["criteria"]
                    },
                    "rationale": "Neutral sides were compared against every hard gate.",
                })
            review = {
                "schema_version": 1, "record_type": "teamwork_pairwise_review",
                "comparison_id": payload["comparison_id"], "reviewer_id": reviewer,
                "rubric_id": payload["rubric_id"], "judgments": judgments,
                "timestamp": "2026-07-15T12:00:00Z",
            }
            (self.review_dir / live_canary.PAIRWISE_REVIEWS_DIR / f"{reviewer}.json").write_text(json.dumps(review), encoding="utf-8")

    def test_prepare_is_blind_balanced_and_finalize_selects_candidate(self) -> None:
        self.prepare()
        for path in (self.review_dir / live_canary.PAIRWISE_INPUTS_DIR).glob("*.json"):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("opaque-one", text)
            self.assertNotIn("opaque-two", text)
            self.assertNotIn(str(self.arms[0][1]), text)
        controller = json.loads((self.review_dir / live_canary.PAIRWISE_CONTROLLER_NAME).read_text(encoding="utf-8"))
        left_counts = {arm_id: 0 for arm_id, _ in self.arms}
        for row in controller["schedule"]:
            left_counts[row["left_arm_id"]] += 1
        self.assertEqual(len(set(left_counts.values())), 1)
        self.write_reviews()
        self.assertEqual(live_canary.main([
            "compare", "finalize", "--review-dir", str(self.review_dir), *self.arm_args()
        ]), 0)
        result = json.loads((self.review_dir / live_canary.PAIRWISE_RESULT_NAME).read_text(encoding="utf-8"))
        self.assertEqual(result["selection"], "opaque-two")
        self.assertEqual(result["status"], "SELECTED")

    def test_finalize_rejects_reviewer_map_leak(self) -> None:
        self.prepare()
        self.write_reviews()
        path = self.review_dir / live_canary.PAIRWISE_REVIEWS_DIR / "reviewer-x.json"
        review = json.loads(path.read_text(encoding="utf-8"))
        review["judgments"][0]["rationale"] = "opaque-two is the candidate"
        path.write_text(json.dumps(review), encoding="utf-8")
        with self.assertRaisesRegex(live_canary.LiveCanaryError, "mapping leaked"):
            live_canary.main(["compare", "finalize", "--review-dir", str(self.review_dir), *self.arm_args()])

    def test_finalize_rejects_tampered_reviewer_packet(self) -> None:
        self.prepare()
        self.write_reviews()
        path = self.review_dir / live_canary.PAIRWISE_INPUTS_DIR / "reviewer-x.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["pairs"][0]["left"]["response"] = "tampered response"
        payload["pairs"][0]["required_evidence"] = {"category": "tampered"}
        path.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(live_canary.LiveCanaryError, "changed since prepare"):
            live_canary.main([
                "compare", "finalize", "--review-dir", str(self.review_dir),
                *self.arm_args(),
            ])

    def test_all_tie_uses_only_manifest_bound_inventory_metric(self) -> None:
        self.prepare()
        self.write_reviews(candidate_better=False)
        controller = json.loads(
            (self.review_dir / live_canary.PAIRWISE_CONTROLLER_NAME).read_text(encoding="utf-8")
        )
        hashes = {
            item["arm_id"]: item["manifest_sha256"]
            for item in controller["arm_mapping"]
        }
        evidence = self.base / "footprint.json"
        evidence.write_text(json.dumps({
            "record_type": "teamwork-pairwise-footprint-v1",
            "metric": "installed_inventory_bytes",
            "candidate_arm_id": "opaque-two",
            "incumbent_arm_id": "opaque-one",
            "candidate_manifest_sha256": hashes["opaque-two"],
            "incumbent_manifest_sha256": hashes["opaque-one"],
        }), encoding="utf-8")
        self.assertEqual(live_canary.main([
            "compare", "finalize", "--review-dir", str(self.review_dir),
            *self.arm_args(), "--smaller-footprint-evidence", str(evidence),
        ]), 0)
        result = json.loads(
            (self.review_dir / live_canary.PAIRWISE_RESULT_NAME).read_text(encoding="utf-8")
        )
        self.assertEqual(result["selection"], "opaque-two")
        self.assertEqual(result["smaller_footprint_evidence"]["candidate_value"], 10)

    def test_all_tie_rejects_arbitrary_metric_and_unbound_hashes(self) -> None:
        self.prepare()
        self.write_reviews(candidate_better=False)
        evidence = self.base / "bad-footprint.json"
        evidence.write_text(json.dumps({
            "record_type": "teamwork-pairwise-footprint-v1",
            "metric": "bananas",
            "candidate_arm_id": "opaque-two",
            "incumbent_arm_id": "opaque-one",
            "candidate_manifest_sha256": "0" * 64,
            "incumbent_manifest_sha256": "0" * 64,
        }), encoding="utf-8")
        with self.assertRaisesRegex(
            live_canary.LiveCanaryError, "verified installed_inventory_bytes metric"
        ):
            live_canary.main([
                "compare", "finalize", "--review-dir", str(self.review_dir),
                *self.arm_args(), "--smaller-footprint-evidence", str(evidence),
            ])


if __name__ == "__main__":
    unittest.main()
