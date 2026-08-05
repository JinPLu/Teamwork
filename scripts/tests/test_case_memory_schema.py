from __future__ import annotations

import json
import runpy
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "scripts/discussion-transaction.py"
CONTRACT = runpy.run_path(str(CLI), run_name="teamwork_case_schema_contract")


class CaseMemorySchemaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.project = Path(self.temporary.name) / "project"
        self.memory = self.project / "docs/teamwork"
        self.memory.mkdir(parents=True)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_index(self, value: dict[str, object]) -> None:
        (self.memory / "index.json").write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def manifest(self, case_id: str, *, status: str = "collaborating") -> dict[str, object]:
        return {
            "schema_version": 2,
            "case_id": case_id,
            "case_seed_b64": "AgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgI=",
            "created_at": "2026-07-30T00:00:00+00:00",
            "closed_at": None,
            "status": status,
            "claims": {},
            "artifacts": {},
            "history": [],
            "references": [],
            "runtime": {
                "active_route": CONTRACT["case_manifest_path"](case_id),
                "state_revision": "0" * 64,
            },
            "migration_sources": [],
            "document": None,
        }

    def test_empty_case_index_has_exact_v3_shape_and_revision(self) -> None:
        index = CONTRACT["empty_case_index"]("Teamwork")
        self.assertEqual(
            set(index),
            {"schema_version", "project", "active_cases", "claim_heads", "aliases", "recent_cases", "migration"},
        )
        self.assertEqual(index["schema_version"], 3)
        text = CONTRACT["serialize_case_index"](index)
        self.assertIn('"active_cases": []', text)

    def test_schema_detection_rejects_hybrid_v1_v2_index(self) -> None:
        index = CONTRACT["empty_case_index"]("Teamwork")
        index["entries"] = []
        index["active"] = {}
        index["last_updated"] = "2026-07-30"
        self.write_index(index)
        with self.assertRaisesRegex(CONTRACT["TransactionError"], "hybrid"):
            CONTRACT["detect_teamwork_memory_schema"](self.project)

    def test_manifest_rejects_unknown_fields_duplicate_ids_and_bad_paths(self) -> None:
        case_id = CONTRACT["case_id_from_seed"]("01" * 32)
        artifact_id = "a-" + "1" * 64
        manifest = self.manifest(case_id)
        manifest["artifacts"] = {
            artifact_id: {
                "role": "plan",
                "subtype": "plan",
                "path": "docs/teamwork/legacy/plan.md",
                "envelope_digest": "2" * 64,
                "byte_digest": "3" * 64,
                "created_at": "2026-07-30T00:00:00+00:00",
                "immutable": True,
                "consumer": "teamwork",
                "source_revision": "4" * 64,
            }
        }
        with self.assertRaisesRegex(CONTRACT["TransactionError"], "inside its case"):
            CONTRACT["validate_case_manifest"](manifest)
        manifest["artifacts"] = []
        manifest["extra"] = True
        with self.assertRaisesRegex(CONTRACT["TransactionError"], "schema_version"):
            CONTRACT["validate_case_manifest"](manifest)

    def test_case_ids_and_artifact_paths_are_deterministic_full_hashes(self) -> None:
        seed = "aa" * 32
        case_id = CONTRACT["case_id_from_seed"](seed)
        self.assertRegex(case_id, r"^c-[0-9a-f]{64}$")
        self.assertRegex(CONTRACT["claim_id_from_seed"](seed), r"^cl-[0-9a-f]{64}$")
        self.assertRegex(CONTRACT["migration_id_from_seed"](seed), r"^m-[0-9a-f]{64}$")
        self.assertEqual(case_id, CONTRACT["case_id_from_seed"](seed))
        artifact_id = CONTRACT["artifact_id_for_case"](
            "plan",
            {
                "role": "plan",
                "subtype": "plan",
                "case_id": case_id,
                "claim_ids": [],
                "consumer": "teamwork",
                "source_revision": "0" * 64,
                "immutable": True,
            },
            "body\n",
        )
        self.assertRegex(artifact_id, r"^a-[0-9a-f]{64}$")
        self.assertEqual(
            CONTRACT["derive_case_artifact_path"](case_id, "plan", artifact_id),
            f"docs/teamwork/cases/{case_id}/live.md",
        )
        with self.assertRaisesRegex(CONTRACT["TransactionError"], "history artifacts"):
            CONTRACT["derive_case_artifact_path"](case_id, "history-plan", artifact_id)
        self.assertEqual(
            CONTRACT["derive_case_source_artifact_path"](case_id, "history-plan", artifact_id),
            f"docs/teamwork/cases/{case_id}/history/plan/{artifact_id}.md",
        )

    def test_collecting_is_valid_active_collection_phase(self) -> None:
        case_id = CONTRACT["case_id_from_seed"]("02" * 32)
        manifest = self.manifest(case_id, status="collecting")
        revision = CONTRACT["case_manifest_revision"](manifest)
        index = CONTRACT["empty_case_index"]("Teamwork")
        index["active_cases"].append(
            {
                "case_id": case_id,
                "manifest_path": CONTRACT["case_manifest_path"](case_id),
                "manifest_revision": revision,
                "phase": "collecting",
                "task_key": "collect-evidence",
            }
        )
        self.assertEqual(CONTRACT["validate_case_manifest"](manifest)["status"], "collecting")
        self.assertEqual(CONTRACT["validate_case_index"](index)["active_cases"][0]["phase"], "collecting")


if __name__ == "__main__":
    unittest.main()
