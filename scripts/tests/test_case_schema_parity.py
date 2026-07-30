from __future__ import annotations

import hashlib
import json
import os
import runpy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TRANSACTION = ROOT / "scripts/discussion-transaction.py"
VALIDATOR = ROOT / "scripts/validate_teamwork_index.py"
CONTRACT = runpy.run_path(str(TRANSACTION), run_name="teamwork_case_schema_parity_contract")


def length_framed_hash(*parts: bytes) -> str:
    digest = hashlib.sha256()
    for part in parts:
        digest.update(len(part).to_bytes(8, "big"))
        digest.update(part)
    return digest.hexdigest()


class CaseSchemaParityTests(unittest.TestCase):
    def setUp(self) -> None:
        (ROOT / "tmp").mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=ROOT / "tmp")
        self.project = Path(self.temporary.name) / "project"
        self.memory = self.project / "docs/teamwork"
        self.memory.mkdir(parents=True)
        (self.memory / "index.json").write_text(
            CONTRACT["serialize_case_index"](CONTRACT["empty_case_index"]("Teamwork")),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def transaction(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(TRANSACTION), *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            env=os.environ.copy(),
        )

    def validator(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(VALIDATOR), str(self.memory / "index.json")],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def inspect(self) -> dict[str, object]:
        result = self.transaction("case-inspect", "--project-root", str(self.project))
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def apply(self, request: dict[str, object]) -> dict[str, object]:
        result = self.transaction("case-apply", "--project-root", str(self.project), "--request-json", json.dumps(request))
        self.assertEqual(result.returncode, 0, result.stderr)
        validated = self.validator()
        self.assertEqual(validated.returncode, 0, validated.stderr)
        return json.loads(result.stdout)

    def request(self, operation: str, case: dict[str, object] | None = None, **extra: object) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": 2,
            "operation": operation,
            "expected_revision": self.inspect()["revision"],
            "updated_at": extra.pop("updated_at", "2026-07-30T00:00:00+00:00"),
        }
        if case is not None:
            payload["case_id"] = case["case_id"]
            payload["expected_manifest_revision"] = case["manifest_revision"]
        payload.update(extra)
        return payload

    def test_transaction_produced_index_and_manifest_validate_at_each_phase(self) -> None:
        created = self.apply(
            self.request(
                "create",
                case_seed="44" * 32,
                title="Persistent documentation parity",
                task_key="persistent-docs",
                aliases=["persistent-docs"],
                initial_phase="collaborating",
            )
        )
        collecting = self.apply(self.request("update", created, phase="collecting", updated_at="2026-07-30T00:10:00+00:00"))
        planned = self.apply(self.request("update", collecting, phase="planned", updated_at="2026-07-30T00:20:00+00:00"))
        executing = self.apply(
            self.request(
                "plan-upsert",
                planned,
                updated_at="2026-07-30T00:30:00+00:00",
                source_digest="1" * 64,
                body="## Plan\n\n- Persist through the case bundle.",
            )
        )
        with_goal = self.apply(
            self.request(
                "goal-acquire",
                executing,
                updated_at="2026-07-30T00:40:00+00:00",
                source_digest="2" * 64,
                body="## Goal\n\n- Hold the active claim.",
                claim_seed="55" * 32,
                owner="Goal",
            )
        )
        result = self.apply(
            self.request(
                "result-add",
                with_goal,
                updated_at="2026-07-30T00:50:00+00:00",
                source_digest="3" * 64,
                body="## Result\n\n- Terminal artifact.",
            )
        )
        closed = self.apply(
            self.request(
                "close",
                result,
                updated_at="2026-07-30T01:00:00+00:00",
                closed_at="2026-07-30T01:00:00+00:00",
            )
        )
        index = json.loads((self.memory / "index.json").read_text(encoding="utf-8"))
        self.assertEqual(index["active_cases"], [])
        self.assertEqual(index["recent_cases"][0]["case_id"], closed["case_id"])
        self.assertRegex(index["recent_cases"][0]["result_artifact_id"], r"^a-[0-9a-f]{64}$")

    def test_negative_shapes_are_rejected_identically_by_contract_and_validator(self) -> None:
        created = self.apply(
            self.request(
                "create",
                case_seed="66" * 32,
                title="Negative parity",
                task_key="negative-parity",
                aliases=["negative-parity"],
                initial_phase="collecting",
            )
        )
        index_path = self.memory / "index.json"
        original = json.loads(index_path.read_text(encoding="utf-8"))
        cases = {
            "unknown-root": lambda data: data.update({"entries": []}),
            "claim-head-list": lambda data: data.update({"claim_heads": []}),
            "alias-dangling": lambda data: data["aliases"]["negative-parity"].update({"target_id": "c-" + "9" * 64}),
        }
        for name, mutate in cases.items():
            with self.subTest(name=name):
                data = json.loads(json.dumps(original))
                mutate(data)
                with self.assertRaises(CONTRACT["TransactionError"]):
                    CONTRACT["validate_case_index"](data)
                index_path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                result = self.validator()
                self.assertNotEqual(result.returncode, 0)
        manifest_path = self.project / created["manifest_path"]
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["extra"] = True
        manifest_path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")
        index_path.write_text(json.dumps(original, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        result = self.validator()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("case manifest top-level fields", result.stderr)

    def test_seeded_id_golden_vectors_use_exact_domains(self) -> None:
        seed = "aa" * 32
        seed_bytes = bytes.fromhex(seed)
        self.assertEqual(CONTRACT["case_id_from_seed"](seed), "c-" + length_framed_hash(b"teamwork-case-id-v1", seed_bytes))
        self.assertEqual(CONTRACT["claim_id_from_seed"](seed), "cl-" + length_framed_hash(b"teamwork-claim-id-v1", seed_bytes))
        self.assertEqual(CONTRACT["migration_id_from_seed"](seed), "m-" + length_framed_hash(b"teamwork-migration-id-v1", seed_bytes))

    def test_transaction_normalizes_utc_to_validator_canonical_z(self) -> None:
        created = self.apply(
            self.request(
                "create",
                updated_at="2026-07-30T00:00:00+00:00",
                case_seed="77" * 32,
                title="UTC parity",
                task_key="utc-parity",
                aliases=["utc-parity"],
                initial_phase="collecting",
            )
        )
        manifest = json.loads((self.project / created["manifest_path"]).read_text(encoding="utf-8"))
        self.assertEqual(manifest["created_at"], "2026-07-30T00:00:00Z")
        validated = self.validator()
        self.assertEqual(validated.returncode, 0, validated.stderr)

    def test_transaction_rejects_non_kebab_task_keys_before_validator(self) -> None:
        request = self.request(
            "create",
            case_seed="88" * 32,
            title="Task key parity",
            task_key="bad:key",
            aliases=[],
            initial_phase="collecting",
        )
        result = self.transaction("case-apply", "--project-root", str(self.project), "--request-json", json.dumps(request))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("task_key", json.loads(result.stderr)["message"])


if __name__ == "__main__":
    unittest.main()
