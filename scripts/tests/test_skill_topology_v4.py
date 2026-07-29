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
    "teamwork-collaborate": "adversarial-search.md",
    "teamwork-debug": "runtime-diagnosis.md",
    "teamwork-research": "deep-research.md",
    "teamwork-review": "strict-review.md",
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
                    "only public Teamwork skill for natural dialogue, brainstorming",
                    "replaces the retired public Discuss, Design, and Grill skill sources",
                    "without aliases or compatibility public surfaces",
                    "do not ask the user to name it",
                    "Before every question",
                    "provisional recommendation",
                    "A native bounded batch contains at most three questions",
                    "Dependent questions are serial",
                    "global -> boundary -> detail",
                    "why the answer is critical",
                    "what it blocks",
                    "observable closing condition",
                    "at least two viable directions remain",
                    "costly or irreversible error or conflicting evidence",
                    "Acceptance requires closure evidence",
                    "`recommendation` is nonempty",
                    "`acceptance_evidence` is nonempty",
                    "sustained semantic Collaborate state defaults to a managed Collaborate checkpoint",
                    "Writer calls only the controlled transaction route",
                    "`discussion-transaction.py collaborate-inspect --project-root <project>`",
                    "`discussion-transaction.py collaborate-schema <create|update|accept|block|close|supersede>`",
                    "`discussion-transaction.py collaborate-apply --project-root <project> --request <file>`",
                    "`docs/teamwork/collaborate/current.md`",
                    "`active.collaborate`",
                    "Legacy Discussion and Design artifacts are read-only migration inputs only",
                    "Legacy write lifecycle commands are retired",
                    "Plan Gate",
                    "Collaborate-scoped revision",
                    "semantic digest",
                    "lineage digest",
                    "Pending or blocked Collaborate records are durable but not Plan-ready",
                    "authorize file changes outside its checkpoint",
                ),
            )
            self.assert_in_order(
                text,
                "discussion-transaction.py collaborate-inspect --project-root <project>",
                "discussion-transaction.py collaborate-schema <create|update|accept|block|close|supersede>",
                "discussion-transaction.py collaborate-apply --project-root <project> --request <file>",
            )
            for override in NEGATIVE_ARTIFACT_OVERRIDES:
                self.assertIn(override, text)
            self.assertNotIn("discussion-transaction.py schema <create|update|close|replace|supersede>", text)
            self.assertNotIn("discussion-transaction.py design-apply", text)
            return
        if skill == "teamwork-plan":
            self.assert_has_fragments(
                text,
                (
                    "accepted Collaborate decision",
                    "Do not redesign or implement",
                    "discussion-transaction.py collaborate-inspect --project-root <project>",
                    "active.path == docs/teamwork/collaborate/current.md",
                    "active.acceptance == accepted",
                    "semantic digest",
                    "lineage digest",
                    "Pending or blocked Collaborate records are durable but never Plan-ready",
                    "Legacy Design, Discussion",
                    "not Plan-ready",
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
                ("`observe`", "`instrument`", "`fix`", "Never infer or upgrade authority"),
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
                ("durable Goal state at entry", "goal-inspect", "goal-schema", "goal-apply"),
            )
            return
        if skill == "teamwork-init":
            self.assert_has_fragments(
                text,
                ("only for an explicit full bootstrap", "Candidate-promotion gates (all must pass)", "project"),
            )
            return
        if skill == "teamwork-update":
            self.assert_has_fragments(
                text,
                ("global installation surfaces only", "check-update.sh", "global"),
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
                    "Accept a user override only when `2 <= B <= 5`",
                    "reject an out-of-range override",
                    "`B = 3`",
                    "do not request confirmation",
                    "maximum adversarial critic/auditor cost is `2B + 2` fresh dispatches",
                    "Every actual hypothesis gets exactly two fresh internal Designer critics",
                    "Launch exactly two final internal Designer auditors",
                    "Converge only when both final auditors return `PASS`",
                    "budget-exhausted",
                    "Never store raw agent transcripts",
                ),
            )
            return
        if (skill, reference) == ("teamwork-research", "deep-research.md"):
            self.assert_in_order(text, "research brief", "source census", "claim ledger", "contradictions")
            return
        if (skill, reference) == ("teamwork-debug", "runtime-diagnosis.md"):
            self.assert_has_fragments(text, ("fixed dispatch authority", "human-only", "Remove every temporary"))
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
            for skill, reference in EXPECTED_REFERENCES.items()
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

    def test_only_advanced_owners_load_their_one_reference(self) -> None:
        for skill in EXPECTED_SKILLS:
            path = SKILLS / skill / "SKILL.md"
            text = path.read_text(encoding="utf-8")
            references = set(re.findall(r"references/([a-z0-9-]+\.md)", text))
            expected = {EXPECTED_REFERENCES[skill]} if skill in EXPECTED_REFERENCES else set()
            self.assertEqual(expected, references, path)

        for skill, reference in EXPECTED_REFERENCES.items():
            path = SKILLS / skill / "references" / reference
            text = path.read_text(encoding="utf-8")
            self.assertNotRegex(text, r"references/[a-z0-9-]+\.md", path)
            for other_skill in EXPECTED_SKILLS - {skill}:
                self.assertNotIn(other_skill, text, path)

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

    def test_collaborate_and_plan_gate_inversions_are_rejected(self) -> None:
        mutations = {
            "teamwork-collaborate": (
                ("do not ask the user to name it", "ask the user to name it"),
                ("A native bounded batch contains at most three questions", "A native bounded batch contains any number of questions"),
                ("Dependent questions are serial", "Dependent questions may be batched"),
                ("Acceptance requires closure evidence", "Acceptance does not require closure evidence"),
                ("Writer calls only the controlled transaction route", "Writer may use any route"),
            ),
            "teamwork-plan": (
                ("accepted Collaborate decision", "accepted Design decision"),
                ("active.acceptance == accepted", "active.acceptance != blocked"),
                ("Pending or blocked Collaborate records are durable but never Plan-ready", "Pending or blocked Collaborate records may be Plan-ready"),
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
        for skill, reference in EXPECTED_REFERENCES.items():
            with self.subTest(skill=skill, reference=reference):
                self.assert_advanced_reference_contract(
                    skill,
                    reference,
                    (SKILLS / skill / "references" / reference).read_text(encoding="utf-8"),
                )


if __name__ == "__main__":
    unittest.main()
