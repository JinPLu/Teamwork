from __future__ import annotations

import unittest

from scripts.teamwork_tooling.instruction_footprint import (
    COMPACTNESS_LIMITS,
    compactness_failures,
    size,
)


class InstructionFootprintTests(unittest.TestCase):
    def test_size_normalizes_whitespace_and_utf8(self) -> None:
        self.assertEqual(size(" alpha\n beta  "), {"words": 2, "bytes": 10})

    def test_equal_measurement_passes_without_rewarding_deletion(self) -> None:
        result = {
            key: {**value, "surfaces": 58} if key == "union" else dict(value)
            for key, value in COMPACTNESS_LIMITS.items()
        }
        self.assertEqual(compactness_failures(result), [])

    def test_measurement_above_compactness_limit_fails(self) -> None:
        result = {
            key: {**value, "surfaces": 58} if key == "union" else dict(value)
            for key, value in COMPACTNESS_LIMITS.items()
        }
        result["union"]["words"] = COMPACTNESS_LIMITS["union"]["words"] + 1
        result["codex"]["bytes"] = COMPACTNESS_LIMITS["codex"]["bytes"] + 1
        self.assertEqual(
            compactness_failures(result),
            [
                "union words exceeds compactness limit: "
                f"{COMPACTNESS_LIMITS['union']['words'] + 1} > "
                f"{COMPACTNESS_LIMITS['union']['words']}",
                "codex bytes exceeds compactness limit: "
                f"{COMPACTNESS_LIMITS['codex']['bytes'] + 1} > "
                f"{COMPACTNESS_LIMITS['codex']['bytes']}",
            ],
        )

    def test_v4_skill_and_reference_inventory_is_exact(self) -> None:
        result = {key: dict(value) for key, value in COMPACTNESS_LIMITS.items()}
        result["skills"].update(
            {
                "surfaces": 10,
                "max_skill_words": 1,
                "behavior_references": 4,
                "cross_skill_loads": 0,
                "dependency_cycles": 0,
            }
        )
        self.assertEqual(compactness_failures(result), [])

    def test_v4_skill_and_reference_inventory_rejects_legacy_counts(self) -> None:
        result = {key: dict(value) for key, value in COMPACTNESS_LIMITS.items()}
        result["skills"].update(
            {
                "surfaces": 9,
                "max_skill_words": 1,
                "behavior_references": 0,
                "cross_skill_loads": 0,
                "dependency_cycles": 0,
            }
        )
        self.assertEqual(
            compactness_failures(result),
            [
                "canonical skill inventory must contain 10 skills: 9",
                "canonical reference inventory must contain 4 references: 0",
            ],
        )


if __name__ == "__main__":
    unittest.main()
