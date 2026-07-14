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
                "union words exceeds compactness limit: 20501 > 20500",
                "codex bytes exceeds compactness limit: 1801 > 1800",
            ],
        )


if __name__ == "__main__":
    unittest.main()
