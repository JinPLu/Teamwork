from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILLS = ROOT / "skills"

EXPECTED_SKILLS = {
    "teamwork-collaborate",
    "teamwork-debug",
    "teamwork-explore",
    "teamwork-goal",
    "teamwork-init",
    "teamwork-plan",
    "teamwork-research",
    "teamwork-review",
    "teamwork-update",
}

EXPECTED_REFERENCES = {
    "teamwork-collaborate": {"adversarial-search.md", "collaboration-layers.md"},
    "teamwork-debug": {"runtime-diagnosis.md"},
    "teamwork-research": {"deep-research.md"},
    "teamwork-review": {"strict-review.md"},
}

EXPECTED_AGENT_METADATA = {
    "teamwork-collaborate": "agents/openai.yaml",
}

RETIRED_PUBLIC_SKILLS = {
    "grill-me",
    "teamwork-discuss",
    "teamwork-design",
    "teamwork",
    "using-teamwork",
    "teamwork-execute",
}

NEGATIVE_ARTIFACT_OVERRIDES = {
    "`no files`",
    "`off-record`",
    "`read-only`",
    "`no writes`",
}


def parse_frontmatter(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise AssertionError(f"{path} does not start with frontmatter")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise AssertionError(f"{path} has unterminated frontmatter") from exc
    metadata: dict[str, str] = {}
    for line in lines[1:end]:
        key, separator, value = line.partition(":")
        if not separator:
            raise AssertionError(f"invalid frontmatter line in {path}: {line!r}")
        metadata[key.strip()] = value.strip()
    return metadata, "\n".join(lines[end + 1 :])


def normalized(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


class SkillTopologyV4Test(unittest.TestCase):
    def assert_in_order(self, text: str, *phrases: str) -> None:
        cursor = -1
        for phrase in phrases:
            position = text.find(phrase, cursor + 1)
            self.assertNotEqual(-1, position, f"missing ordered contract: {phrase!r}")
            self.assertGreater(position, cursor, f"out-of-order contract: {phrase!r}")
            cursor = position

    def assert_has_fragments(self, text: str, fragments: tuple[str, ...]) -> None:
        for fragment in fragments:
            self.assertIn(fragment, text)

    def assert_skill_contract(self, skill: str, text: str) -> None:
        text = " ".join(text.split())
        if skill == "teamwork-collaborate":
            self.assert_has_fragments(
                text,
                (
                    "wants to discuss, design, plan, brainstorm, compare options, or think something through",
                    "material choice belongs to the user",
                    "intent is unclear and needs guided clarification",
                    "brief intent check",
                    "do not force a question",
                    "synthesis, useful options, and a recommendation before asking",
                    "host-native Ask Question",
                    "Do not impose a total question or round limit",
                    "Ask independent questions together",
                    "Ask dependent questions after the earlier answer",
                    "wait before continuing dependent work",
                    "L1 — Understand Intent",
                    "L2 — Explore Together",
                    "L3 — Challenge and Converge",
                    "Move between layers",
                    "Do not use layer number as a question, turn, or agent budget",
                    "Research and Explore gather evidence, then return it to the same discussion",
                    "Execute the real method or report it unavailable",
                    "Dispatch Writer at the first substantive synthesis",
                    "overall picture; decided; open discussion and evidence; current recommendation and next step",
                    "Save meaning, not a transcript",
                ),
            )
            self.assertNotIn("Public/release/migration/security/destructive/cross-platform", text)
            self.assertNotIn("A native bounded batch contains at most three questions", text)
            return
        if skill == "teamwork-plan":
            self.assert_has_fragments(
                text,
                (
                    "accepted Collaborate decision",
                    "Do not redesign or implement",
                    "controlled case-v2 Collaborate readback",
                    "case-v2",
                    "case-inspect",
                    "selected case manifest",
                    "accepted decision artifact",
                    "manifest revision",
                    "Legacy-v1",
                    "decision revision",
                    "digests",
                    "acceptance evidence",
                    "Legacy-v1, pending, or blocked Collaborate records are durable/migration inputs but never Plan-ready",
                    "Legacy Design, Discussion",
                    "not Plan-ready",
                    "Maintain visible monotonic Plan state",
                    "No Planner, Root, or Worker fallback writes it",
                ),
            )
            self.assertNotIn("design-inspect", text)
            self.assertNotIn("active.design", text)
            return
        if skill == "teamwork-research":
            self.assert_has_fragments(
                text,
                ("external-only", "Root MUST NOT browse", "MUST NOT call `wait_agent`", "read-only"),
            )
            return
        if skill == "teamwork-explore":
            self.assert_has_fragments(
                text,
                ("local-only and read-only", "healthy CodeGraph first", "does not browse the web"),
            )
            return
        if skill == "teamwork-debug":
            self.assert_has_fragments(
                text,
                (
                    "`observe`",
                    "`instrument`",
                    "`fix`",
                    "Never infer or upgrade authority",
                    "Freeze The Failure",
                    "Hypothesis Gate",
                    "rank three to five plausible hypotheses",
                    "one active discriminating experiment at a time",
                    "Runtime Log-First",
                    "event-flow",
                    "temporary structured log",
                    "Skip code instrumentation only when existing evidence already decides",
                    "`new-failure-split`",
                    "Do not invoke Reviewer",
                ),
            )
            causal_loop = text.split("## Causal Loop", 1)[1]
            self.assert_in_order(
                causal_loop,
                "Capture the actual failing",
                "Apply the Hypothesis Gate",
                "Trace from the failing boundary",
            )
            return
        if skill == "teamwork-review":
            self.assert_has_fragments(
                text,
                ("sealed integrated candidate", "one independent initial pass", "Reviewer always stays read-only"),
            )
            return
        if skill == "teamwork-goal":
            self.assert_has_fragments(
                text,
                (
                    "durable Goal state at entry",
                    "case-v2 Goal transaction route",
                    "case-inspect",
                    "case-schema <goal-acquire|goal-update|goal-transfer|goal-close>",
                    "case-apply",
                    "Maintain visible monotonic Goal state",
                ),
            )
            return
        if skill == "teamwork-init":
            self.assert_has_fragments(
                text,
                (
                    "project-local",
                    "capability-blocked",
                    "migrate --project-root <exact-project-root>",
                    "resume --project-root <exact-project-root>",
                    "case-v2",
                    "never asks for the global performance/cost profile",
                    "never installs or configures GPU Broker",
                    "--codegraph` or `--no-codegraph",
                ),
            )
            return
        if skill == "teamwork-update":
            self.assert_has_fragments(
                text,
                (
                    "global",
                    "check-update.sh",
                    "capability-blocked",
                    "migrate --project-root <exact-project-root>",
                    "resume --project-root <exact-project-root>",
                    "case-v2",
                    "performance-first|cost-first",
                    "--managed-codegraph|--no-managed-codegraph",
                    "--managed-gpu-broker|--no-managed-gpu-broker",
                    "BASELINE_READY=yes",
                    "FULL_CAPABILITY_READY=yes",
                ),
            )
            return
        self.fail(f"missing contract validator for {skill}")

    def assert_advanced_reference_contract(self, skill: str, reference: str, text: str) -> None:
        text = " ".join(text.split())
        if (skill, reference) == ("teamwork-collaborate", "adversarial-search.md"):
            self.assert_has_fragments(
                text,
                (
                    "Collaborate selects it automatically or an explicit adversarial override",
                    "Accept a user override only when `2 <= B <= 3`",
                    "reject an out-of-range override",
                    "`B = 3`",
                    "do not request confirmation",
                    "maximum adversarial critic/auditor cost is `2B + 2` fresh dispatches",
                    "capped at eight total children",
                    "Every actual hypothesis gets exactly two fresh internal Designer critics",
                    "Launch exactly two final internal Designer auditors",
                    "Converge only when both final auditors return `PASS`",
                    "budget-exhausted",
                    "Never store raw agent transcripts",
                ),
            )
            return
        if (skill, reference) == ("teamwork-collaborate", "collaboration-layers.md"):
            self.assert_has_fragments(
                text,
                (
                    "Intent ambiguity",
                    "Knowledge-space ambiguity",
                    "Ask directly when",
                    "Map first when",
                    "host-native Ask Question",
                    "transport limit",
                    "Overall outcome",
                    "Boundaries and criteria",
                    "Directions and evidence",
                    "Broad research direction",
                    "Dependent decisions",
                    "Adversarial convergence",
                ),
            )
            return
        if (skill, reference) == ("teamwork-research", "deep-research.md"):
            self.assert_in_order(text, "research brief", "source census", "claim ledger", "contradictions")
            return
        if (skill, reference) == ("teamwork-debug", "runtime-diagnosis.md"):
            self.assert_has_fragments(
                text,
                (
                    "fixed dispatch authority",
                    "Runtime Log-First",
                    "event-flow",
                    "temporary structured log",
                    "human-only",
                    "Remove every temporary",
                ),
            )
            return
        if (skill, reference) == ("teamwork-review", "strict-review.md"):
            self.assert_has_fragments(text, ("correctness first", "stable `R-*`", "read-only"))
            return
        self.fail(f"missing advanced-reference validator for {skill}/{reference}")

    def test_exact_flat_skill_inventory(self) -> None:
        actual = {path.name for path in SKILLS.iterdir() if path.is_dir()}
        self.assertEqual(EXPECTED_SKILLS, actual)
        self.assertTrue(RETIRED_PUBLIC_SKILLS.isdisjoint(actual))

        expected_files = {SKILLS / name / "SKILL.md" for name in EXPECTED_SKILLS}
        expected_files.update(
            SKILLS / skill / "references" / reference
            for skill, references in EXPECTED_REFERENCES.items()
            for reference in references
        )
        expected_files.update(
            SKILLS / skill / relative
            for skill, relative in EXPECTED_AGENT_METADATA.items()
        )
        actual_files = {path for path in SKILLS.rglob("*") if path.is_file()}
        self.assertEqual(expected_files, actual_files)

    def test_frontmatter_is_minimal_and_matches_directory(self) -> None:
        for skill in EXPECTED_SKILLS:
            path = SKILLS / skill / "SKILL.md"
            metadata, _ = parse_frontmatter(path)
            self.assertEqual({"name", "description"}, set(metadata), path)
            self.assertEqual(skill, metadata["name"], path)
            self.assertTrue(metadata["description"].startswith("Use when"), path)

    def test_only_advanced_owners_load_their_own_references(self) -> None:
        for skill in EXPECTED_SKILLS:
            path = SKILLS / skill / "SKILL.md"
            text = path.read_text(encoding="utf-8")
            references = set(re.findall(r"references/([a-z0-9-]+\.md)", text))
            expected = EXPECTED_REFERENCES.get(skill, set())
            self.assertEqual(expected, references, path)

        for skill, references in EXPECTED_REFERENCES.items():
            for reference in references:
                path = SKILLS / skill / "references" / reference
                text = path.read_text(encoding="utf-8")
                self.assertNotRegex(text, r"references/[a-z0-9-]+\.md", path)
                for other_skill in EXPECTED_SKILLS - {skill}:
                    self.assertNotIn(other_skill, text, path)

    def test_collaborate_openai_metadata_matches_skill(self) -> None:
        path = SKILLS / "teamwork-collaborate" / "agents" / "openai.yaml"
        text = path.read_text(encoding="utf-8")
        self.assertIn('display_name: "Teamwork Collaborate"', text)
        match = re.search(r'short_description: "([^"]+)"', text)
        self.assertIsNotNone(match)
        self.assertTrue(25 <= len(match.group(1)) <= 64)
        self.assertIn('$teamwork-collaborate', text)

    def test_no_skill_invokes_another_or_restores_retired_aliases(self) -> None:
        for skill in EXPECTED_SKILLS:
            _, body = parse_frontmatter(SKILLS / skill / "SKILL.md")
            for other_skill in EXPECTED_SKILLS - {skill}:
                self.assertNotIn(other_skill, body)
            for retired in RETIRED_PUBLIC_SKILLS:
                self.assertNotIn(f"skills/{retired}/SKILL.md", body)

    def test_required_behavior_is_owned_by_the_right_skill(self) -> None:
        for skill in EXPECTED_SKILLS:
            with self.subTest(skill=skill):
                self.assert_skill_contract(skill, (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8"))

    def test_request_readiness_has_one_root_asker_and_explicit_leaf_handoffs(self) -> None:
        skill_fragments = {
            "teamwork-collaborate": ("host-native Ask Question", "Never decide a material user-owned choice"),
            "teamwork-research": ("Researcher never asks", "reclassification signal"),
            "teamwork-explore": ("Explorer never asks", "reclassification signal"),
            "teamwork-debug": ("A leaf never asks directly", "reclassification signal"),
            "teamwork-plan": ("Planner never asks users", "reclassification signal"),
            "teamwork-review": ("Reviewer and Plan Reviewer never ask", "reclassification signal"),
            "teamwork-goal": ("Root alone asks once", "reclassified to Collaborate"),
            "teamwork-init": ("Explorer and Worker never ask", "resumes the same Init workflow"),
            "teamwork-update": ("Explorer and Worker never ask", "resumes the same Update workflow"),
        }
        for skill, fragments in skill_fragments.items():
            with self.subTest(skill=skill):
                text = normalized(SKILLS / skill / "SKILL.md")
                self.assert_has_fragments(text, fragments)

        readiness_roles = {
            "researcher", "explorer", "debugger", "planner", "worker",
            "reviewer", "plan-reviewer",
        }
        for host, directory, suffix, prefix in (
            ("codex", ROOT / "templates/codex-agents", ".toml", "teamwork-"),
            ("cursor", ROOT / "templates/cursor-agents", ".md", ""),
            ("claude", ROOT / "templates/claude-agents", ".md", ""),
        ):
            for role in readiness_roles:
                with self.subTest(host=host, role=role):
                    text = normalized(directory / f"{prefix}{role}{suffix}")
                    self.assertIn("Readiness: never ask", text)
                    self.assertIn("reclassification signal to Root", text)
            for role in ("designer", "writer"):
                with self.subTest(host=host, role=role):
                    text = normalized(directory / f"{prefix}{role}{suffix}")
                    self.assertNotIn("Readiness:", text)

    def test_case_v2_writer_routes_are_explicit_and_legacy_routes_are_migration_only(self) -> None:
        contracts = {
            "teamwork-research": ("case-inspect", "case-schema <research-add>", "case-apply"),
            "teamwork-explore": ("case-inspect", "case-schema <evidence-add>", "case-apply"),
            "teamwork-debug": ("case-inspect", "case-schema <debug-add>", "case-apply"),
            "teamwork-plan": ("case-inspect", "case-schema <plan-upsert>", "case-apply"),
            "teamwork-review": ("case-inspect", "case-schema <review-add|code-review-add|plan-review-add>", "case-apply"),
            "teamwork-goal": ("case-inspect", "case-schema <goal-acquire|goal-update|goal-transfer|goal-close>", "case-apply"),
            "teamwork-init": ("case-inspect", "case-schema <init-result>", "case-apply"),
            "teamwork-update": ("case-inspect", "case-schema <update-result>", "case-apply"),
        }
        for skill, route in contracts.items():
            with self.subTest(skill=skill):
                text = " ".join((SKILLS / skill / "SKILL.md").read_text(encoding="utf-8").split())
                for fragment in (
                    *route,
                    "case_id",
                    "alias",
                    "frozen seed/task_key",
                    "fails closed before any write",
                ):
                    self.assertIn(fragment, text)
                self.assertNotIn("artifact-inspect -> artifact-schema <create|update|supersede> -> artifact-apply", text)
                self.assertNotIn("collaborate-inspect -> collaborate-schema", text)
                self.assertNotIn("goal-inspect --project-root <project>", text)

        collaborate = " ".join((SKILLS / "teamwork-collaborate" / "SKILL.md").read_text(encoding="utf-8").split())
        self.assertIn("Dispatch Writer at the first substantive synthesis", collaborate)
        self.assertIn("Never write the checkpoint directly", collaborate)
        self.assertNotIn("case-schema", collaborate)

        goal = " ".join((SKILLS / "teamwork-goal" / "SKILL.md").read_text(encoding="utf-8").split())
        review = " ".join((SKILLS / "teamwork-review" / "SKILL.md").read_text(encoding="utf-8").split())
        self.assertIn("initial_phase=executing", goal)
        self.assertIn("reads back its revisions", goal)
        self.assertIn("initial_phase=executing", review)
        self.assertIn("initial_phase=planned", review)
        self.assertIn("reads back the create revisions", review)

    def test_plan_readiness_schema_first_segments(self) -> None:
        text = normalized(SKILLS / "teamwork-plan" / "SKILL.md")
        v2_segment = text.split("In case-v2", 1)[1].split("Legacy-v1", 1)[0]
        self.assertIn("case-inspect", v2_segment)
        self.assertIn("selected case manifest", v2_segment)
        self.assertIn("accepted decision artifact", v2_segment)
        self.assertIn("manifest revision", v2_segment)
        self.assertNotIn("docs/teamwork/collaborate/current.md", v2_segment)
        self.assertNotIn("collaborate-inspect", v2_segment)
        self.assertIn("Legacy-v1, pending, or blocked Collaborate records are durable/migration inputs but never Plan-ready", text)
        self.assertNotIn("active.path == docs/teamwork/collaborate/current.md", text)

    def test_public_docs_describe_case_v2_only_routes_and_migration_inputs(self) -> None:
        stale_generic = (
            "Research, Debug, Plan, Plan Review, Review, mutating Init/Update, "
            "and qualifying terminal execution handoffs use the generic artifact transaction. Writer calls"
        )
        for relative in ("README.md", "README.en.md", "docs/architecture.md"):
            with self.subTest(path=relative):
                text = normalized(ROOT / relative)
                self.assertIn("v2", text)
                self.assertIn("case", text)
                self.assertIn("legacy-v1", text)
                self.assertTrue(
                    "migration input" in text or "迁移输入" in text,
                    relative,
                )
                self.assertNotIn("generic artifact transaction", text)
                self.assertNotIn(stale_generic, text)

    def test_collaborate_and_plan_gate_inversions_are_rejected(self) -> None:
        mutations = {
            "teamwork-collaborate": (
                ("do not force a question", "force a question"),
                ("Do not impose a total question or round limit", "Impose a total question and round limit"),
                ("Ask independent questions together", "Ask independent questions one at a time"),
                ("Ask dependent questions after the earlier answer", "Ask dependent questions in the same batch"),
                ("Move between layers as the discussion changes", "Move through layers once in fixed order"),
                ("Execute the real method or report it unavailable", "Describe the method without executing it"),
                ("Save meaning, not a transcript", "Save the transcript"),
            ),
            "teamwork-plan": (
                ("accepted Collaborate decision", "accepted Design decision"),
                ("controlled case-v2 Collaborate readback", "uncontrolled Collaborate summary"),
                ("Legacy-v1, pending, or blocked Collaborate records are durable/migration inputs but never Plan-ready", "Pending or blocked Collaborate records may be Plan-ready"),
                ("Legacy Design, Discussion", "Current Design, Discussion"),
            ),
        }
        for skill, changes in mutations.items():
            original = normalized(SKILLS / skill / "SKILL.md")
            for before, after in changes:
                with self.subTest(skill=skill, before=before):
                    mutated = original.replace(before, after, 1)
                    self.assertNotEqual(original, mutated, "mutation fixture must apply")
                    with self.assertRaises(AssertionError):
                        self.assert_skill_contract(skill, mutated)

    def test_collaborate_adversarial_reference_inversions_are_rejected(self) -> None:
        original = normalized(SKILLS / "teamwork-collaborate" / "references" / "adversarial-search.md")
        for before, after in (
            ("Collaborate selects it automatically or an explicit adversarial override", "runs only after explicit adversarial wording"),
            ("reject an out-of-range override", "accept any override"),
            ("do not request confirmation", "request confirmation"),
            ("exactly two fresh internal Designer critics", "one reused Designer critic"),
            ("both final auditors return `PASS`", "one final auditor returns `PASS`"),
        ):
            with self.subTest(before=before):
                mutated = original.replace(before, after, 1)
                self.assertNotEqual(original, mutated, "mutation fixture must apply")
                with self.assertRaises(AssertionError):
                    self.assert_advanced_reference_contract("teamwork-collaborate", "adversarial-search.md", mutated)

    def test_advanced_references_preserve_their_named_contracts(self) -> None:
        for skill, references in EXPECTED_REFERENCES.items():
            for reference in references:
                with self.subTest(skill=skill, reference=reference):
                    self.assert_advanced_reference_contract(
                        skill,
                        reference,
                        (SKILLS / skill / "references" / reference).read_text(encoding="utf-8"),
                    )


if __name__ == "__main__":
    unittest.main()
