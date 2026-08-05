"""Semantic contracts for Teamwork's lean managed policy."""

from __future__ import annotations

import pathlib
import subprocess
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
POLICY = ROOT / "scripts/install/policy.sh"

PRINCIPLES = (
    "Clear work stays native",
    "Be epistemically honest",
    "Calibrate verification and defenses",
)

ROUTING = (
    "Collaborate for explicit discussion",
    "Research for broad or deep external multi-source work",
    "Debug for unknown-cause failures",
    "Plan for a clear or selected direction",
    "Review for a finished candidate, including a plan",
    "Goal only when the user explicitly asks",
    "Local evidence routes to Explorer without a public Explore skill",
    "Strict adversarial work routes to Challenger",
)

FORBIDDEN = (
    "Plan Reviewer",
    "Designer",
    "Default-child",
    "daily cap",
    "L1=intent",
    "case-v2 workflow",
    "Writer packet+transaction",
    "sealed review",
)


def contract_failures(policy: str) -> list[str]:
    failures = [f"missing: {phrase}" for phrase in (*PRINCIPLES, *ROUTING) if phrase not in policy]
    failures.extend(f"retired: {phrase}" for phrase in FORBIDDEN if phrase in policy)
    return failures


def render(function: str) -> str:
    output = subprocess.run(
        ["bash", "-c", f'source "$1"; {function}', "policy-test", str(POLICY)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return " ".join(output.split())


class LeanPolicyTests(unittest.TestCase):
    def test_policy_preserves_three_principles_and_semantic_routes(self) -> None:
        policy = render("write_teamwork_global_policy_body")
        self.assertEqual(contract_failures(policy), [])

    def test_policy_keeps_infrastructure_out_of_model_workflows(self) -> None:
        policy = render("write_teamwork_global_policy_body")
        self.assertIn("Storage, migration, transaction, CAS, readback, and integrity details stay out", policy)
        self.assertIn("Teamwork creates no separate authorization protocol", policy)
        self.assertIn("Teamwork defines no numeric dispatch caps", policy)

    def test_each_principle_is_mutation_bound(self) -> None:
        policy = render("write_teamwork_global_policy_body")
        for phrase in PRINCIPLES:
            with self.subTest(phrase=phrase):
                self.assertTrue(contract_failures(policy.replace(phrase, "")))

    def test_host_adapters_share_policy_and_only_codex_names_its_question_tool(self) -> None:
        rendered = {
            host: render(f"write_teamwork_{host}_global_policy")
            for host in ("codex", "cursor", "claude")
        }
        for host, policy in rendered.items():
            with self.subTest(host=host):
                for phrase in PRINCIPLES:
                    self.assertIn(phrase, policy)
        self.assertIn("request_user_input", rendered["codex"])
        self.assertNotIn("request_user_input", rendered["cursor"])
        self.assertNotIn("request_user_input", rendered["claude"])


if __name__ == "__main__":
    unittest.main()
