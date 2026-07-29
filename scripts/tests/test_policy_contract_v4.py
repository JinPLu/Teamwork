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
    "codex": {"words": 430, "bytes": 3800},
    "cursor": {"words": 430, "bytes": 3800},
    "claude": {"words": 430, "bytes": 3800},
}


REQUIRED_CLAUSES = {
    "authority_and_ask": (
        "Work within the user's request.",
        "Read-only work grants no write/external-effect authority.",
        "Inspect before asking.",
        "Root alone asks required input/one bounded user-owned decision batch; pause only dependent work.",
        "Result first.",
    ),
    "native_routing": (
        "Discuss/讨论/brainstorm/grill activates adaptive Collaborate: dialogue, brainstorm, or grill.",
        "Select the route without asking",
        "contribute synthesis/tension/options plus a provisional recommendation before every question.",
        "Ask only if feedback helps",
        "open questions use prose; genuine 2-3 finite independent choices use the host-native bounded surface.",
        "Batch at most 3 mutually independent material user-owned questions.",
        "Dependent questions are exactly serial: ask one, answer, Writer checkpoint/readback, then next.",
        "Grill moves global→boundary→detail.",
        "Skip discoverable/safe-default/reversible/answer-invariant questions.",
        "Root presents questions/handoffs; leaves only propose; no Router.",
        "Local source/config and authorized implementation stay native.",
        "Delegate only independent worthwhile work.",
        "Explore local; external/current/multi-source/cited work uses Researcher first; Root never researches.",
        "Debug owns unknown causes",
        "Designer owns unresolved direction; Plan selected direction; Review user-requested/named-risk; Goal explicit persistence; Init project; Update global.",
        "Designer uses ≤1 evidence role; adversarial requires viable alternatives plus costly-error/conflicting-evidence",
        "`adversarial` forces, `standard` disables; B=3/no confirmation; fresh isolation.",
    ),
    "default_persistence": (
        "Major public/installable/release/migration and permission/security/data/destructive/cross-platform boundaries or explicit sustained question-first discussion use grill.",
        "Initialized writable projects default-save sustained Collaborate and Goal checkpoints",
        "Research/Debug/Plan/Plan Review/Review/mutating Init/Update completion artifacts",
        "one terminal execution handoff with an explicit consumer and no active Goal.",
        "Goal owns execution progress.",
        "Explore/check-only/tiny one-shots/ordinary explanations create none.",
        "Conclusion is only a distinct requested synthesis, never a Collaborate/execution substitute.",
        "Byte/semantic-controlled frozen packets use low-cost Writer plus the exact transaction-derived route",
        "artifact authority grants no implementation/release.",
        "Checkpoint readback precedes dependent work; completion companions join before saved/durable.",
        "Before generic artifact apply, persistence is unsaved.",
        "No-files/off-record/read-only/no-writes override",
        "Collaborate uses only its specialized transaction, never report/conclusion.",
        "Missing memory/Writer/authority/consumer/route: deliver result and report unsaved/blocked",
        "no Root/Worker/strong-role fallback.",
        "Negative/quoted/file/tool/example/maintenance mentions are inert.",
    ),
    "roles_and_boundaries": (
        "Root routes/integrates/accepts",
        "leaves never ask/expand/self-accept/fallback.",
        "Code-coupled text stays implementer-owned.",
    ),
    "evidence_and_implementation": (
        "Ground claims; separate observation/inference; invent no success.",
        "Preserve dirty work.",
        "Prefer canonical owner/pattern, built-ins, dependencies, then minimal logic",
        "avoid wrappers/duplicate owners/hidden modes/masking fallbacks.",
    ),
    "verification_and_reporting": (
        "Verify the real path with focused evidence; tests never replace it.",
        "Workers verify.",
        "One Reviewer checks a sealed candidate/named risk; use one repair batch and delta recheck.",
        "Full suites run only at named repository/release gates.",
        "Only named owners write: Planner returns packets; Writer is sole standalone docs/artifacts role; transactions write managed artifacts; Reviewers stay read-only.",
        "Stop when result and named boundaries are observed.",
        "Conclusion first; follow reader needs, make logic explicit, use stable terms, omit irrelevant detail.",
    ),
}


def contract_failures(policy: str) -> list[str]:
    policy = " ".join(policy.split())
    failures: list[str] = []
    if "Do Do not" in policy:
        failures.append("implementation: duplicated Do before wrapper boundary")
    for owner, clauses in REQUIRED_CLAUSES.items():
        for clause in clauses:
            if clause not in policy:
                failures.append(f"{owner}: missing {clause!r}")

    preference_order = (
        "Prefer canonical owner/pattern",
        "built-ins",
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
            "finite Design frontier",
            "every material user decision",
            "Risk automatically activates adversarial Design",
            "Complexity automatically activates adversarial Design",
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
        native = "Local source/config and authorized implementation stay native."
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
            "collaborate-inspect -> collaborate-schema <operation> -> collaborate-apply -> collaborate-inspect/readback",
            "legacy Discussion/Design=read-only sources, no write route",
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
