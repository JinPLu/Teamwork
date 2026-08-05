from __future__ import annotations

import json
import hashlib
import runpy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "scripts/validate_teamwork_index.py"
FILES = ROOT / "scripts/init-project-files.py"
TRANSACTION = ROOT / "scripts/discussion-transaction.py"
CONTRACT = runpy.run_path(str(TRANSACTION), run_name="teamwork_index_v2_contract")

CASE_ID = "c-" + "a" * 64
ARTIFACT_ID = "a-" + "c" * 64
CLAIM_ID = "cl-" + "e" * 64
LIVE_TEXT = f"""Teamwork Live Document: 1
Case ID: {CASE_ID}
Purpose: discussion
Status: active
Generation: 1
Last Updated: 2026-07-30T00:00:00Z
Needs Resolution: no

# Case bundle
<!-- TEAMWORK:SECTION Purpose State -->
## Purpose State

Current collaboration state.
<!-- /TEAMWORK:SECTION -->
"""
ARTIFACT_DIGEST = hashlib.sha256(LIVE_TEXT.encode("utf-8")).hexdigest()


class TeamworkV2IndexTests(unittest.TestCase):
    def setUp(self) -> None:
        (ROOT / "tmp").mkdir(exist_ok=True)

    def run_validator(self, path: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(VALIDATOR), str(path)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    @staticmethod
    def manifest() -> dict[str, object]:
        return {
            "schema_version": 2,
            "case_id": CASE_ID,
            "case_seed_b64": "AQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQE=",
            "created_at": "2026-07-30T00:00:00Z",
            "closed_at": None,
            "status": "collaborating",
            "claims": {
                CLAIM_ID: {
                    "descriptor_version": 1,
                    "descriptor_digest": "b" * 64,
                    "status": "active",
                    "acquired_at": "2026-07-30T00:00:00Z",
                    "released_at": None,
                    "head_artifact_id": ARTIFACT_ID,
                    "head_digest": ARTIFACT_DIGEST,
                }
            },
            "artifacts": {
                ARTIFACT_ID: {
                    "role": "collaborate",
                    "subtype": "collaborate",
                    "path": f"docs/teamwork/cases/{CASE_ID}/live.md",
                    "envelope_digest": "f" * 64,
                    "byte_digest": ARTIFACT_DIGEST,
                    "created_at": "2026-07-30T00:00:00Z",
                    "immutable": True,
                    "consumer": "teamwork",
                    "source_revision": "9" * 64,
                }
            },
            "history": [],
            "references": [],
            "runtime": {
                "active_route": f"docs/teamwork/cases/{CASE_ID}/live.md",
                "state_revision": "8" * 64,
            },
            "migration_sources": [],
            "document": {
                "path": f"docs/teamwork/cases/{CASE_ID}/live.md",
                "generation": 1,
                "byte_digest": ARTIFACT_DIGEST,
                "updated_at": "2026-07-30T00:00:00Z",
                "title": "Case bundle",
                "purpose": "discussion",
                "status": "active",
                "needs_resolution": False,
                "latest_artifact_id": ARTIFACT_ID,
                "source_artifact_ids": [ARTIFACT_ID],
            },
        }

    @staticmethod
    def index() -> dict[str, object]:
        revision = CONTRACT["case_manifest_revision"](TeamworkV2IndexTests.manifest())
        return {
            "schema_version": 3,
            "project": {
                "name": "Fixture",
                "root": ".",
                "description": "Local Teamwork case-bundle index for this project.",
            },
            "active_cases": [
                {
                    "case_id": CASE_ID,
                    "manifest_path": f"docs/teamwork/cases/{CASE_ID}/manifest.json",
                    "manifest_revision": revision,
                    "phase": "collaborating",
                    "task_key": "case-bundle",
                }
            ],
            "claim_heads": {
                CLAIM_ID: {
                    "case_id": CASE_ID,
                    "artifact_id": ARTIFACT_ID,
                    "artifact_digest": ARTIFACT_DIGEST,
                    "claim_revision": revision,
                    "status": "active",
                }
            },
            "aliases": {
                "case-bundle": {
                    "target_type": "case",
                    "target_id": CASE_ID,
                    "manifest_path": f"docs/teamwork/cases/{CASE_ID}/manifest.json",
                    "manifest_revision": revision,
                }
            },
            "recent_cases": [],
            "migration": None,
        }

    def test_template_is_valid_v2_index_only(self) -> None:
        result = self.run_validator(ROOT / "templates/teamwork-memory/index.json")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_project_index_reads_and_validates_active_case_manifest(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "tmp") as temporary:
            project = Path(temporary) / "project"
            manifest_path = project / f"docs/teamwork/cases/{CASE_ID}/manifest.json"
            manifest_path.parent.mkdir(parents=True)
            manifest_path.write_text(json.dumps(self.manifest(), indent=2) + "\n", encoding="utf-8")
            (manifest_path.parent / "live.md").write_text(LIVE_TEXT, encoding="utf-8")
            index_path = project / "docs/teamwork/index.json"
            index_path.write_text(json.dumps(self.index(), indent=2) + "\n", encoding="utf-8")

            result = self.run_validator(index_path)

            self.assertEqual(result.returncode, 0, result.stderr)

    def test_v2_index_rejects_unknown_top_level_alias_cap_and_recent_overlap(self) -> None:
        cases = {
            "unknown": (lambda data: data.update({"entries": []}), "top-level fields"),
            "alias-cap": (
                lambda data: data.update({"aliases": {f"alias-{i}": {
                    "target_type": "case",
                    "target_id": CASE_ID,
                    "manifest_path": f"docs/teamwork/cases/{CASE_ID}/manifest.json",
                    "manifest_revision": CONTRACT["case_manifest_revision"](TeamworkV2IndexTests.manifest()),
                } for i in range(257)}}),
                "aliases exceeds 256",
            ),
            "recent-overlap": (
                lambda data: data.update(
                    {
                        "recent_cases": [
                            {
                                "case_id": CASE_ID,
                                "manifest_path": f"docs/teamwork/cases/{CASE_ID}/manifest.json",
                                "closed_at": "2026-07-30T00:00:00Z",
                                "result_artifact_id": ARTIFACT_ID,
                                "result_digest": ARTIFACT_DIGEST,
                            }
                        ]
                    }
                ),
                "recent_cases must not duplicate active cases",
            ),
        }
        for name, (mutate, message) in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory(dir=ROOT / "tmp") as temporary:
                path = Path(temporary) / "index.json"
                data = self.index()
                mutate(data)
                path.write_text(json.dumps(data) + "\n", encoding="utf-8")

                result = self.run_validator(path)

                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, result.stderr)

    def test_case_manifest_rejects_out_of_case_artifact_paths(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "tmp") as temporary:
            path = Path(temporary) / "project" / f"docs/teamwork/cases/{CASE_ID}/manifest.json"
            path.parent.mkdir(parents=True)
            data = self.manifest()
            artifacts = data["artifacts"]
            assert isinstance(artifacts, dict)
            artifact = artifacts[ARTIFACT_ID]
            assert isinstance(artifact, dict)
            artifact["path"] = "docs/teamwork/cases/c-" + "f" * 64 + "/live.md"
            path.write_text(json.dumps(data) + "\n", encoding="utf-8")

            result = self.run_validator(path)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn(f"docs/teamwork/cases/{CASE_ID}/", result.stderr)

    def test_v2_hybrid_with_legacy_anchors_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / "tmp") as temporary:
            project = Path(temporary) / "project"
            memory = project / "docs/teamwork"
            memory.mkdir(parents=True)
            (memory / "index.json").write_text(json.dumps(self.index()) + "\n", encoding="utf-8")
            (memory / "current.md").write_text("# legacy anchor\n", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(FILES), "--project-root", str(project), "validate"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("hybrid case memory initialization", result.stderr)


if __name__ == "__main__":
    unittest.main()
