from __future__ import annotations

from pathlib import Path
import unittest

from scripts.teamwork_tooling.instruction_footprint import (
    COMPACTNESS_LIMITS,
    compactness_failures,
    max_surface_size,
    size,
)


class InstructionFootprintTests(unittest.TestCase):
    def test_size_normalizes_whitespace_and_utf8(self) -> None:
        self.assertEqual(size(" alpha\n beta  "), {"words": 2, "bytes": 10})

    def test_max_surface_size_tracks_word_and_byte_maxima_independently(self) -> None:
        measured = max_surface_size(
            [
                ("word-heavy", "one two three four"),
                ("byte-heavy", "字" * 7),
            ]
        )
        self.assertEqual(measured["words"], 4)
        self.assertEqual(measured["words_path"], "word-heavy")
        self.assertEqual(measured["bytes"], len(("字" * 7).encode("utf-8")))
        self.assertEqual(measured["bytes_path"], "byte-heavy")

    def test_equal_measurement_passes_without_rewarding_deletion(self) -> None:
        result = {
            "enforced": {key: dict(value) for key, value in COMPACTNESS_LIMITS.items()},
            "telemetry": {
                "union": {"words": 999999, "bytes": 999999, "surfaces": 58},
                "skills": {
                    "words": 999999,
                    "bytes": 999999,
                    "surfaces": 10,
                    "max_skill_words": 999999,
                    "behavior_references": 4,
                    "cross_skill_loads": 0,
                    "dependency_cycles": 0,
                },
            },
        }
        self.assertEqual(compactness_failures(result), [])

    def test_measurement_above_compactness_limit_fails(self) -> None:
        result = {
            "enforced": {key: dict(value) for key, value in COMPACTNESS_LIMITS.items()},
            "telemetry": {
                "union": {"words": 1, "bytes": 1, "surfaces": 58},
                "skills": {
                    "words": 1,
                    "bytes": 1,
                    "surfaces": 10,
                    "max_skill_words": 1,
                    "behavior_references": 4,
                    "cross_skill_loads": 0,
                    "dependency_cycles": 0,
                },
            },
        }
        result["enforced"]["max_skill_bundle"]["words"] = COMPACTNESS_LIMITS["max_skill_bundle"]["words"] + 1
        result["enforced"]["global_policy_codex"]["bytes"] = COMPACTNESS_LIMITS["global_policy_codex"]["bytes"] + 1
        self.assertEqual(
            compactness_failures(result),
            [
                "global_policy_codex bytes exceeds compactness limit: "
                f"{COMPACTNESS_LIMITS['global_policy_codex']['bytes'] + 1} > "
                f"{COMPACTNESS_LIMITS['global_policy_codex']['bytes']}",
                "max_skill_bundle words exceeds compactness limit: "
                f"{COMPACTNESS_LIMITS['max_skill_bundle']['words'] + 1} > "
                f"{COMPACTNESS_LIMITS['max_skill_bundle']['words']}",
            ],
        )

    def test_v4_skill_and_reference_inventory_is_exact(self) -> None:
        result = {
            "enforced": {key: dict(value) for key, value in COMPACTNESS_LIMITS.items()},
            "telemetry": {
                "skills": {
                    "surfaces": 10,
                    "max_skill_words": 999999,
                    "behavior_references": 4,
                    "cross_skill_loads": 0,
                    "dependency_cycles": 0,
                }
            },
        }
        self.assertEqual(compactness_failures(result), [])

    def test_v4_skill_and_reference_inventory_rejects_legacy_counts(self) -> None:
        result = {
            "enforced": {key: dict(value) for key, value in COMPACTNESS_LIMITS.items()},
            "telemetry": {
                "skills": {
                    "surfaces": 9,
                    "max_skill_words": 1,
                    "behavior_references": 0,
                    "cross_skill_loads": 0,
                    "dependency_cycles": 0,
                }
            },
        }
        self.assertEqual(
            compactness_failures(result),
            [
                "canonical skill inventory must contain 10 skills: 9",
                "canonical reference inventory must contain 4 references: 0",
            ],
        )

    def test_real_loading_surfaces_include_project_memory_and_repository_context(self) -> None:
        self.assertTrue(
            {
                "project_instruction_block",
                "repository_instructions",
                "runtime_memory_index",
                "runtime_memory_readme",
                "worst_static_root_path",
                "worst_static_leaf_path",
                "worst_repository_root_path",
            }.issubset(COMPACTNESS_LIMITS)
        )

    def test_runtime_volume_budgets_have_one_owner(self) -> None:
        root = Path(__file__).resolve().parents[2]
        validation = "\n".join(
            (root / path).read_text(encoding="utf-8")
            for path in (
                "scripts/validation/common.sh",
                "scripts/validation/contracts.sh",
                "scripts/validation/integration.sh",
            )
        )
        self.assertNotRegex(validation, r"(?m)^\s*(?:line_count_max|word_count_max)\s")
        self.assertIn("fenced_block_line_count_max", validation)


if __name__ == "__main__":
    unittest.main()
