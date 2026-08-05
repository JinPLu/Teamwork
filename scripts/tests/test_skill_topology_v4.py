from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from teamwork_tooling.evaluation.contracts import EvalError  # noqa: E402
from teamwork_tooling.evaluation.sources import (  # noqa: E402
    discover_skill_inventory,
    validate_retired_reference,
    validate_role_template_sources,
    validate_skill_topology,
)
from teamwork_tooling.topology import (  # noqa: E402
    agent_template_paths,
    host_role_paths,
    load_topology,
    owned_references,
    public_skill_paths,
)


class SkillTopologyManifestTests(unittest.TestCase):
    def test_manifest_drives_skill_inventory_without_count_contract(self) -> None:
        expected = set(public_skill_paths(ROOT))
        self.assertEqual(expected, set(discover_skill_inventory(ROOT)))
        self.assertNotIn("teamwork-explore", expected)
        self.assertIn("explorer", agent_template_paths(ROOT))
        self.assertNotIn("CANONICAL_SKILL_COUNT", (ROOT / "scripts/teamwork_tooling/evaluation/contracts.py").read_text())

    def test_agent_renames_and_host_paths_are_manifest_owned(self) -> None:
        topology = load_topology(ROOT)
        agents = set(agent_template_paths(ROOT))
        self.assertIn("challenger", agents)
        self.assertIn("reviewer", agents)
        self.assertNotIn("designer", agents)
        self.assertNotIn("plan-reviewer", agents)
        self.assertEqual("challenger", topology["retired"]["agents"]["designer"])
        self.assertEqual("reviewer", topology["retired"]["agents"]["plan-reviewer"])
        for host, mapping in host_role_paths(ROOT).items():
            self.assertEqual(agents, set(mapping), host)

    def test_references_are_owned_by_manifest_not_a_fixed_number(self) -> None:
        observed = {
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / "skills").glob("*/references/**/*")
            if path.is_file()
        }
        self.assertEqual(set(owned_references(ROOT)), observed)
        self.assertNotIn(
            "skills/teamwork-collaborate/references/collaboration-layers.md",
            observed,
        )

    def test_topology_and_role_surfaces_validate(self) -> None:
        validate_skill_topology(ROOT)
        validate_role_template_sources(ROOT)

    def test_inventory_mismatch_reports_names_not_an_abstract_count(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "config").mkdir()
            topology = json.loads((ROOT / "config/teamwork-topology.json").read_text())
            (root / "config/teamwork-topology.json").write_text(json.dumps(topology))
            for name in public_skill_paths(ROOT):
                target = root / "skills" / name
                target.mkdir(parents=True)
                (target / "SKILL.md").write_text(
                    f"---\nname: {name}\ndescription: Use when testing.\n---\n"
                )
            extra = root / "skills/teamwork-router"
            extra.mkdir()
            (extra / "SKILL.md").write_text(
                "---\nname: teamwork-router\ndescription: Use when routing.\n---\n"
            )
            with self.assertRaisesRegex(EvalError, "differs from topology manifest"):
                validate_skill_topology(root)

    def test_retired_name_paths_are_categorized(self) -> None:
        self.assertEqual(
            "history",
            validate_retired_reference("evals/teamwork/ledgers/retired-teamwork-explore.jsonl"),
        )
        with self.assertRaisesRegex(EvalError, "outside a categorized"):
            validate_retired_reference("evals/teamwork/cases/negative-teamwork-explore.json")
        with self.assertRaisesRegex(EvalError, "outside a categorized"):
            validate_retired_reference("skills/teamwork-collaborate/SKILL.md")


if __name__ == "__main__":
    unittest.main()
