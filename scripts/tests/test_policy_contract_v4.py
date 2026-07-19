"""Source-bound contract tests for the thin Teamwork v4 Root policy."""

from __future__ import annotations

import pathlib
import subprocess
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
POLICY_SOURCE = ROOT / "scripts" / "install" / "policy.sh"
FULL_RENDER_LIMITS = {
    "codex": {"words": 370, "bytes": 3000},
    "cursor": {"words": 370, "bytes": 3000},
    "claude": {"words": 370, "bytes": 3000},
}


REQUIRED_CLAUSES = {
    "authority_and_ask": (
        "Work within the user's request.",
        "Read-only work grants no write or external-effect authority",
        "answers, questions, designs, plans, reviews, and confirmations grant none.",
        "Inspect evidence before asking.",
        "Root owns user questions",
        "Root alone asks only for required input or a material user-owned decision, one at a time.",
        "Pause only dependent work.",
        "Produce the real requested result first.",
    ),
    "native_routing": (
        "Local repository/source/configuration evidence and authorized implementation stay native.",
        "Delegate only independent bounded work when worthwhile.",
        "Explore local.",
        "External/current/multi-source/citation-backed work uses Research.",
        "Debug owns unknown causes",
        "an unresolved material direction uses Design",
        "Plan only translates an already selected direction",
        "Review user-requested/named-risk work",
        "Goal explicit persistence; Init project; Update global.",
        "Design may dispatch one choice-relevant Explorer or Researcher, never both by default.",
    ),
    "automatic_grill": (
        "Root opens Grill for major public/installable, migration/release, permission, security, data, destructive, cross-platform, or finite Design-frontier changes.",
        "Persist unless user says no files/off-record; within scope persist only create, semantic decision/frontier change, close/supersede.",
        "Decisions never grant implementation/release authority.",
        "Natural question-first intent causes no file write",
        "negative/quoted/file/tool/example/maintenance mentions are inert.",
    ),
    "roles_and_boundaries": (
        "Root routes, integrates, accepts",
        "leaf roles never ask users, expand scope, self-accept, or fallback.",
    ),
    "evidence_and_implementation": (
        "Ground claims in evidence; distinguish observation from inference; invent no state/success.",
        "Preserve unrelated dirty work.",
        "Prefer current canonical owner/pattern, built-ins, suitable installed dependencies, then minimal logic.",
        "Do not add an unrequested wrapper; avoid duplicate owners, parallel modes, compatibility branches, broad catches, speculative surfaces, masking fallbacks.",
    ),
    "verification_and_reporting": (
        "Verify proportionally on the claimed real path with focused automated regression evidence.",
        "For low-risk mechanical work observe the result; full suite only for a named repository/release gate.",
        "Tests and validation support delivery and never replace an available real run.",
        "Workers self-verify.",
        "One independent max Reviewer checks one sealed candidate or named risk once; combine findings into one repair batch and allow at most one delta recheck.",
        "Only named owners write durable artifacts; only Planner writes an authorized Plan; Reviewers stay read-only.",
        "Stop when the requested result and named boundaries are observed.",
        "Lead with the conclusion; keep only detail that changes understanding, decision, action, or risk.",
    ),
}


def contract_failures(policy: str) -> list[str]:
    policy = " ".join(policy.split())
    failures: list[str] = []
    for owner, clauses in REQUIRED_CLAUSES.items():
        for clause in clauses:
            if clause not in policy:
                failures.append(f"{owner}: missing {clause!r}")

    preference_order = (
        "Prefer current canonical owner/pattern",
        "built-ins",
        "suitable installed dependencies",
        "minimal logic",
    )
    positions = [policy.find(clause) for clause in preference_order]
    if any(position < 0 for position in positions) or positions != sorted(positions):
        failures.append("implementation: preference order changed")

    forbidden = (
        "Use a Router",
        "generic Execute Skill",
        "load shared behavioral references",
        "Worker accepts the overall result",
        "Review before direct verification",
        "Review every code change",
        "Every code change",
        "Every Planner result receives independent Plan Review",
        "Grill is exclusive to user-originated question-first intent",
    )
    for clause in forbidden:
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
            "Codex: use request_user_input for callable questions.",
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

    def test_each_source_clause_is_mutation_bound(self) -> None:
        for owner, clauses in REQUIRED_CLAUSES.items():
            for clause in clauses:
                with self.subTest(owner=owner, clause=clause):
                    mutated = self.policy.replace(clause, "", 1)
                    self.assertTrue(
                        contract_failures(mutated),
                        f"deleting {owner} clause was not detected: {clause!r}",
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
        native = "Local repository/source/configuration evidence and authorized implementation stay native."
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
        ):
            with self.subTest(mutation=mutation):
                self.assertTrue(contract_failures(self.policy + mutation))


if __name__ == "__main__":
    unittest.main()
