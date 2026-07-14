from __future__ import annotations

import unittest

from scripts.teamwork_tooling.instruction_footprint import regressions, size


class InstructionFootprintTests(unittest.TestCase):
    def test_size_normalizes_whitespace_and_utf8(self) -> None:
        self.assertEqual(size(" alpha\n beta  "), {"words": 2, "bytes": 10})

    def test_equal_or_larger_measurement_fails(self) -> None:
        result = {
            key: {**value, "surfaces": 58} if key == "union" else dict(value)
            for key, value in {
                "union": {"words": 18142, "bytes": 132316},
                "codex": {"words": 181, "bytes": 1409},
                "cursor": {"words": 180, "bytes": 1403},
                "claude": {"words": 181, "bytes": 1408},
            }.items()
        }
        self.assertEqual(
            regressions(result),
            [
                "union words must decrease: 18142 >= 18142",
                "union bytes must decrease: 132316 >= 132316",
            ],
        )


if __name__ == "__main__":
    unittest.main()
