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
    "codex": {"words": 430, "bytes": 4100},
    "cursor": {"words": 430, "bytes": 4100},
    "claude": {"words": 430, "bytes": 4100},
}


REQUIRED_CLAUSES = {
    "authority_and_ask": (
        "Work within the request.",
        "Read-only grants no write/external-effect authority.",
        "Inspect before asking.",
        "Root alone asks input/one bounded decision batch; pause only dependent work.",
        "Result first.",
    ),
    "native_routing": (
        "Discuss/brainstorm/stress-test activates Collaborate: dialogue|brainstorm.",
        "Select without asking",
        "before questions give synthesis/tension/options plus recommendation.",
        "Ask only if useful",
        "open prose or host-native 2-3 finite choices.",
        "Batch max 3 independent material questions.",
        "Dependent: ask, answer, Writer checkpoint/readback, continue.",
        "Challenge moves global->boundary->detail.",
        "Skip discoverable/safe-default/reversible/answer-invariant.",
        "Root asks/hands off; leaves only propose; no Router.",
        "Native: tiny/discoverable reads, explanations, simple commands, integration, authorized implementation.",
        "Default one child; daily cap4; 5-8 only for explicit adversarial/release with host support.",
        "Exact roles: Research->Researcher, Explore->Explorer, Debug->Debugger, Plan->Planner, Review->Reviewer, Plan Review->Plan Reviewer, Init/Update->Explorer then Worker; Collaborate/Goal Root-owned.",
        "Unavailable role or unverified isolation = capability-blocked; no Root named-method fallback.",
        "Debug freezes failure; hypotheses before probes.",
        "Adversarial is challenge, not mode: viable alternatives plus costly-error/conflicting-evidence",
        "`adversarial` forces, `standard` disables; B=3/no confirmation; fresh isolation.",
    ),
    "default_persistence": (
        "Public/installable/release/migration, permission/security/data/destructive/cross-platform, or sustained explicit question-first work uses Collaborate challenge.",
        "Initialized writable projects default-save only case-v2 Collaborate/Goal checkpoints",
        "Research/Debug/Plan/Plan Review/Review/mutating Init/Update completion artifacts",
        "terminal execution handoff needs a consumer and no active Goal.",
        "No legacy-v1 artifact/collaborate/goal write fallback.",
        "Goal owns progress.",
        "Explore/check-only/tiny one-shots/explanations create none.",
        "Conclusion is only requested synthesis.",
        "Frozen packets use low-cost Writer plus exact transaction",
        "artifact authority grants no implementation/release.",
        "Readback precedes dependent work; join companions before saved/durable; pre-apply is unsaved.",
        "No-files/off-record/read-only/no-writes override.",
        "Collaborate uses its specialized transaction.",
        "Missing memory/Writer/authority/consumer/route: deliver result, report unsaved/blocked",
        "no Root/Worker/strong-role fallback.",
        "Negative/quoted/file/tool/example mentions are inert.",
    ),
    "roles_and_boundaries": (
        "Root routes/integrates/accepts",
        "leaves never ask/expand/self-accept/fallback.",
        "Code-coupled text stays implementer-owned.",
    ),
    "evidence_and_implementation": (
        "Ground claims; separate observation/inference; invent no success; preserve dirty work.",
        "Prefer canonical owner/pattern, built-ins/dependencies, then minimal logic",
        "avoid wrappers/duplicate owners/hidden modes/masking fallbacks.",
    ),
    "verification_and_reporting": (
        "Verify the real path with focused evidence; tests never replace it.",
        "Workers verify.",
        "One Reviewer checks a sealed candidate/named risk; one repair batch and delta recheck.",
        "Full suites run only at named repository/release gates.",
        "Named owners write: Planner returns packets; Writer owns standalone docs/artifacts role; transactions write managed artifacts; Reviewers stay read-only.",
        "Stop when result and boundaries are observed.",
        "Conclusion first; be clear, stable, relevant.",
        "Monotonic state: Research claim_map/active_gap/wave/evidence_delta/contradiction/",
        "Plan decision_revision/dependencies/proof_targets/",
        "Review sealed_digest/stable_findings/verdict/repair_batch/",
        "Goal objective/signal/attempt/failure/evidence_delta/",
        "Cost: native fast path, single owner, fanout/context bounds, telemetry; no unverified price/ranking claims.",
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
            "adversarial mode",
            "Root may perform named-method fallback",
            "legacy-v1 artifact/collaborate/goal may write fallback",
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
        native = "Native: tiny/discoverable reads, explanations, simple commands, integration, authorized implementation."
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
