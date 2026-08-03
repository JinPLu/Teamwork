"""Source-bound contract tests for the thin Teamwork v4 Root policy."""

from __future__ import annotations

import pathlib
import subprocess
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
POLICY_SOURCE = ROOT / "scripts" / "install" / "policy.sh"
ROLE_TEMPLATE_DIRECTORIES = {
    "codex-agents": (
        "teamwork-researcher.toml",
        "teamwork-explorer.toml",
        "teamwork-debugger.toml",
        "teamwork-designer.toml",
        "teamwork-planner.toml",
        "teamwork-worker.toml",
        "teamwork-writer.toml",
        "teamwork-plan-reviewer.toml",
        "teamwork-reviewer.toml",
    ),
    "cursor-agents": (
        "researcher.md",
        "explorer.md",
        "debugger.md",
        "designer.md",
        "planner.md",
        "worker.md",
        "writer.md",
        "plan-reviewer.md",
        "reviewer.md",
    ),
    "claude-agents": (
        "researcher.md",
        "explorer.md",
        "debugger.md",
        "designer.md",
        "planner.md",
        "worker.md",
        "writer.md",
        "plan-reviewer.md",
        "reviewer.md",
    ),
}
WRITER_TEMPLATES = {
    "codex-agents": "teamwork-writer.toml",
    "cursor-agents": "writer.md",
    "claude-agents": "writer.md",
}
FULL_RENDER_LIMITS = {
    "codex": {"words": 220, "bytes": 2600},
    "cursor": {"words": 220, "bytes": 2600},
    "claude": {"words": 220, "bytes": 2600},
}


REQUIRED_CONCEPTS = {
    "authority_and_effect_boundary": (
        "Work within the request",
        "Read-only",
        "no write/effect authority",
        "No-files/off-record/read-only/no-writes",
        "override effects",
        "Inspect before asking",
        "discoverable/safe/reversible -> act",
        "one missing user value",
        "Root alone asks",
        "one bounded decision batch",
        "then resume",
        "unformed intent/preference -> Collaborate",
        "Result first; clear/stable/relevant",
        "report unsaved/blocked",
    ),
    "native_fast_path_and_routing": (
        "Native fast path",
        "tiny reads/explanations/commands/integration/authorized implementation",
        "Research->Researcher",
        "Explore->Explorer",
        "Debug->Debugger",
        "Plan->Planner",
        "Review->Reviewer",
        "Plan Review->Plan Reviewer",
        "Init/Update->Explorer then Worker",
        "Collaborate/Goal Root-owned",
    ),
    "unavailable_role_blocks": (
        "Unavailable role/isolation",
        "capability-blocked",
        "no role/method fallback",
    ),
    "collaborate_and_leaf_boundary": (
        "Discuss/brainstorm/stress-test activates Collaborate",
        "dialogue|brainstorm",
        "synthesis/tension/options+recommendation",
        "Ask only if useful",
        "open prose",
        "host-native 2-3 finite choices",
        "Challenge moves",
        "Adversarial is challenge, not mode",
        "question-first",
        "Leaves return exact gap/reclassification",
        "never ask/activate/expand/self-accept",
        "One asker/owner/gap",
        "no repeats",
    ),
    "case_v2_writer_transaction": (
        "Writable initialized projects",
        "default-save substantive case-v2 workflow checkpoints/results",
        "frozen Writer packet+transaction+readback",
        "Only tiny-native/check-only/one-shot work is unsaved",
        "Legacy-v1 read-only",
        "no artifact/collaborate/goal/manual/report/ memory write fallback",
        "Missing memory/Writer/authority/consumer/route",
        "deliver core result",
        "report unsaved/blocked",
        "Code-coupled text stays implementer-owned",
    ),
    "evidence_implementation_and_verification": (
        "Ground claims",
        "separate observation/inference",
        "invent no success",
        "preserve dirty work",
        "Prefer canonical owner/pattern",
        "built-ins/dependencies",
        "minimal logic",
        "Verify real path",
        "focused evidence",
        "tests never replace it",
        "Reviewers read-only",
        "one sealed review",
        "repair-batch/delta-recheck",
        "requested/risk gates",
        "Stop when result/boundaries are observed",
    ),
}


FORBIDDEN_CONCEPTS = (
    "Use a Router",
    "generic Execute Skill",
    "load shared behavioral references",
    "Worker accepts the overall result",
    "Review before direct verification",
    "Review every code change",
    "Every code change",
    "Every Planner result receives independent Plan Review",
    "Grill is exclusive to user-originated question-first intent",
    "finite Design frontier",
    "every material user decision",
    "Risk automatically activates adversarial Design",
    "Complexity automatically activates adversarial Design",
    "adversarial mode",
    "Root may perform named-method fallback",
    "legacy-v1 artifact/collaborate/goal may write fallback",
)


def contract_failures(policy: str) -> list[str]:
    policy = " ".join(policy.split())
    failures: list[str] = []
    if "Do Do not" in policy:
        failures.append("implementation: duplicated Do before wrapper boundary")
    for owner, concepts in REQUIRED_CONCEPTS.items():
        for concept in concepts:
            if concept not in policy:
                failures.append(f"{owner}: missing concept {concept!r}")

    preference_order = (
        "Prefer canonical owner/pattern",
        "built-ins/dependencies",
        "minimal logic",
    )
    positions = [policy.find(clause) for clause in preference_order]
    if any(position < 0 for position in positions) or positions != sorted(positions):
        failures.append("implementation: preference order changed")

    for clause in FORBIDDEN_CONCEPTS:
        if clause in policy:
            failures.append(f"forbidden v4 behavior: {clause!r}")
    return failures


class PolicyContractV4Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        def render(function: str) -> str:
            result = subprocess.run(
                [
                    "bash",
                    "-c",
                    f'source "$1"; {function}',
                    "policy-contract-v4",
                    str(POLICY_SOURCE),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            return result.stdout

        cls.policy = " ".join(render("write_teamwork_global_policy_body").split())
        def render_install(platform: str) -> str:
            result = subprocess.run(
                [str(ROOT / "install.sh"), f"{platform}-policy"],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            return result.stdout

        cls.raw_platforms = {
            platform: render_install(platform)
            for platform in FULL_RENDER_LIMITS
        }
        cls.platforms = {
            platform: " ".join(rendered.split())
            for platform, rendered in cls.raw_platforms.items()
        }

    def test_rendered_policy_satisfies_v4_contract(self) -> None:
        self.assertEqual(contract_failures(self.policy), [])

    def test_each_host_rendering_keeps_the_contract_and_codex_question_surface(self) -> None:
        for platform, rendered in self.platforms.items():
            with self.subTest(platform=platform):
                self.assertEqual(contract_failures(rendered), [])
        self.assertIn(
            "Codex: bounded choices request_user_input; open prose.",
            self.platforms["codex"],
        )
        self.assertNotIn("request_user_input", self.platforms["cursor"])
        self.assertNotIn("request_user_input", self.platforms["claude"])

    def test_each_full_host_rendering_enforces_exact_word_and_byte_limits(self) -> None:
        for platform, rendered in self.raw_platforms.items():
            with self.subTest(platform=platform):
                measured = {
                    "words": len(rendered.split()),
                    "bytes": len(rendered.encode("utf-8")),
                }
                for metric, limit in FULL_RENDER_LIMITS[platform].items():
                    self.assertLessEqual(
                        measured[metric],
                        limit,
                        f"{platform} full rendered policy exceeds {metric}: "
                        f"{measured[metric]} > {limit}",
                    )

    def test_each_source_concept_is_mutation_bound(self) -> None:
        for owner, concepts in REQUIRED_CONCEPTS.items():
            for concept in concepts:
                with self.subTest(owner=owner, concept=concept):
                    mutated = self.policy.replace(concept, "")
                    self.assertTrue(
                        contract_failures(mutated),
                        f"deleting {owner} concept was not detected: {concept!r}",
                    )

    def test_preference_order_inversion_is_detected(self) -> None:
        canonical = "Prefer canonical owner/pattern"
        minimal = "minimal logic"
        mutated = self.policy.replace(canonical, "ORDER_SENTINEL", 1)
        mutated = mutated.replace(minimal, canonical, 1)
        mutated = mutated.replace("ORDER_SENTINEL", minimal, 1)
        self.assertIn(
            "implementation: preference order changed",
            contract_failures(mutated),
        )

    def test_clear_simple_work_cannot_be_rerouted_to_a_worker(self) -> None:
        native = "Native fast path: tiny reads/explanations/commands/integration/authorized implementation."
        mutated = self.policy.replace(
            native,
            "A Worker owns every clear authorized implementation.",
            1,
        )
        self.assertNotEqual(self.policy, mutated)
        self.assertTrue(contract_failures(mutated))

    def test_forbidden_router_execute_and_self_acceptance_mutations_fail(self) -> None:
        for mutation in (
            " Use a Router.",
            " Add a generic Execute Skill.",
            " Skills load shared behavioral references.",
            " Worker accepts the overall result.",
            " Review before direct verification.",
            " Grill is exclusive to user-originated question-first intent.",
            " Root may perform named-method fallback.",
            " legacy-v1 artifact/collaborate/goal may write fallback.",
        ):
            with self.subTest(mutation=mutation):
                self.assertTrue(contract_failures(self.policy + mutation))

    def test_internal_role_inventory_stays_exactly_nine_per_host(self) -> None:
        for directory, expected_names in ROLE_TEMPLATE_DIRECTORIES.items():
            with self.subTest(directory=directory):
                actual_names = {
                    path.name
                    for path in (ROOT / "templates" / directory).iterdir()
                    if path.is_file()
                }
                self.assertEqual(set(expected_names), actual_names)

    def test_writer_templates_enforce_frozen_packet_controls(self) -> None:
        required = (
            "frozen bounded writing brief, byte/semantic-controlled",
            "requested clauses",
            "Do not paraphrase controlled text",
            "resolve contradictions",
            "delete requested clauses",
            "read back and compare against byte/semantic packet obligations",
            "blocked without writing and unsaved",
            "cannot preserve requested clauses",
            "return blocked/unsaved to Root/Planner on conflict or readback mismatch",
            "case-v2 only",
            "case-schema <operation> -> case-apply/readback",
            "legacy-v1 artifacts/collaborate/goal are read-only migration inputs, no write route",
            "Do not self-accept",
        )
        for directory, filename in WRITER_TEMPLATES.items():
            with self.subTest(template=f"{directory}/{filename}"):
                text = " ".join(
                    (ROOT / "templates" / directory / filename)
                    .read_text(encoding="utf-8")
                    .split()
                )
                for phrase in required:
                    self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
