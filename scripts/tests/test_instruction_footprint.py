from __future__ import annotations

from pathlib import Path
import unittest

from scripts.teamwork_tooling.instruction_footprint import (
    FOOTPRINT_BASELINE,
    REGRESSION_MIN_GROWTH,
    REGRESSION_MULTIPLIER,
    compactness_failures,
    max_surface_size,
    size,
)


def fixture() -> dict[str, object]:
    return {
        "paths": {key: dict(value) for key, value in FOOTPRINT_BASELINE.items()},
        "telemetry": {
            "union": {"words": 999999, "bytes": 999999, "surfaces": 999},
            "skills": {
                "words": 999999,
                "bytes": 999999,
                "surfaces": 123,
                "max_skill_words": 999999,
                "behavior_references": 77,
                "cross_skill_loads": 0,
                "dependency_cycles": 0,
            },
        },
    }


class InstructionFootprintTests(unittest.TestCase):
    def test_size_normalizes_whitespace_and_utf8(self) -> None:
        self.assertEqual(size(" alpha\n beta  "), {"words": 2, "bytes": 10})

    def test_max_surface_size_tracks_independent_maxima(self) -> None:
        measured = max_surface_size([("words", "one two three four"), ("bytes", "字" * 7)])
        self.assertEqual(4, measured["words"])
        self.assertEqual("words", measured["words_path"])
        self.assertEqual(len(("字" * 7).encode()), measured["bytes"])
        self.assertEqual("bytes", measured["bytes_path"])

    def test_baseline_is_telemetry_not_an_absolute_squeeze(self) -> None:
        result = fixture()
        result["paths"]["max_skill_bundle"]["words"] += 1
        result["paths"]["global_policy_codex"]["bytes"] += 1
        self.assertEqual([], compactness_failures(result))

    def test_material_growth_requires_review(self) -> None:
        result = fixture()
        baseline = FOOTPRINT_BASELINE["max_skill_bundle"]["words"]
        threshold = max(
            int(baseline * REGRESSION_MULTIPLIER),
            baseline + REGRESSION_MIN_GROWTH["words"],
        )
        result["paths"]["max_skill_bundle"]["words"] = threshold + 1
        failures = compactness_failures(result)
        self.assertEqual(1, len(failures))
        self.assertIn("instruction-footprint regression", failures[0])

    def test_inventory_counts_are_telemetry(self) -> None:
        result = fixture()
        result["telemetry"]["skills"]["surfaces"] = 2
        result["telemetry"]["skills"]["behavior_references"] = 99
        self.assertEqual([], compactness_failures(result))

    def test_dependency_regressions_still_fail(self) -> None:
        result = fixture()
        result["telemetry"]["skills"]["cross_skill_loads"] = 1
        result["telemetry"]["skills"]["dependency_cycles"] = 1
        self.assertEqual(
            [
                "skill topology must keep cross_skill_loads=0: 1",
                "skill topology must keep dependency_cycles=0: 1",
            ],
            compactness_failures(result),
        )

    def test_no_abstract_inventory_count_constants_remain(self) -> None:
        root = Path(__file__).resolve().parents[2]
        source = (root / "scripts/teamwork_tooling/instruction_footprint.py").read_text()
        self.assertNotIn("CANONICAL_SKILL_COUNT", source)
        self.assertNotIn("CANONICAL_REFERENCE_COUNT", source)


if __name__ == "__main__":
    unittest.main()
