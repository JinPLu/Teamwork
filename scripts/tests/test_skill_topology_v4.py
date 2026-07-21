from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILLS = ROOT / "skills"

EXPECTED_SKILLS = {
    "grill-me",
    "teamwork-explore",
    "teamwork-research",
    "teamwork-debug",
    "teamwork-design",
    "teamwork-plan",
    "teamwork-review",
    "teamwork-goal",
    "teamwork-init",
    "teamwork-update",
}

EXPECTED_REFERENCES = {
    "teamwork-research": "deep-research.md",
    "teamwork-debug": "runtime-diagnosis.md",
    "teamwork-design": "adversarial-search.md",
    "teamwork-review": "strict-review.md",
}

GRILL_DIRECT_WRITE_TARGETS = {
    "discussion artifact",
    "Markdown",
    "Mermaid diagram",
    "decision map",
    "index",
    "current anchor",
    "README",
    "archive",
}

GRILL_LIFECYCLES = {"create", "update", "close", "replace", "supersede"}

INIT_PROMOTION_GATES = {
    "currentness",
    "scope",
    "direct evidence",
    "privacy/protected-data review",
    "Root authority",
}

DIRECT_WRITE_PERMISSION = re.compile(
    r"(?:\bGrill\b[^.]*\b(?:may|can|allowed|permission|exception|fallback)\b"
    r"[^.]*\b(?:write|rewrite)\b|\bdirect[- ]write\b[^.]*"
    r"\b(?:permission|exception|fallback|may|can|allowed)\b[^.]*"
    r"\b(?:write|rewrite|permit|allow)\b)",
    re.IGNORECASE,
)
APPLY_WITHOUT_REVISION_PERMISSION = re.compile(
    r"(?:\bapply\b[^.]*\b(?:may|can|allowed|permits?|optional)\b"
    r"[^.]*\b(?:without|omit|skip|bypass|expected[_ ]revision)\b|"
    r"\b(?:without|omit|skip|bypass)\b[^.]*\bexpected[_ ]revision\b"
    r"[^.]*\bapply\b[^.]*\b(?:may|can|allowed|permits?|optional)\b|"
    r"\bexpected[_ ]revision\b[^.]*\b(?:may|can|allowed|permits?|optional)\b"
    r"[^.]*\bapply\b)",
    re.IGNORECASE,
)
PERMISSIVE_PROMOTION = re.compile(
    r"(?:\b(?:logged|partial|permissive)\b[^.]*"
    r"\b(?:may|can|allowed|sufficient|permits?|allows?)\b[^.]*\bpromot\w*\b|"
    r"\bpromot\w*\b[^.]*\b(?:with|after|despite|from)\b[^.]*"
    r"\b(?:logged|partial|permissive)\b)",
    re.IGNORECASE,
)
HAND_AUTHORED_DESIGN_PERMISSION = re.compile(
    r"\b(?:Design|Designer)\b[^.]*\b(?:may|can|allowed|exception|fallback)\b"
    r"[^.]*\b(?:hand[- ]author|write|edit)\b[^.]*"
    r"\b(?:Markdown|artifact|map|fallback)\b",
    re.IGNORECASE,
)
PERMISSION_OR_WAIVER = re.compile(
    r"\b(?:may|can|allowed|allows?|permission|exception|waiv\w*|override|"
    r"fallback|emergency|optional|skip\w*|bypass\w*|proceed)\b",
    re.IGNORECASE,
)
EXPLICIT_PROHIBITION = re.compile(
    r"\b(?:no|never|not|cannot|must not|do not|does not|prohibit\w*|forbid\w*)\b",
    re.IGNORECASE,
)


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


class SkillTopologyV4Test(unittest.TestCase):
    def assert_in_order(self, text: str, *phrases: str) -> None:
        cursor = -1
        for phrase in phrases:
            position = text.find(phrase, cursor + 1)
            self.assertNotEqual(-1, position, f"missing ordered contract: {phrase!r}")
            self.assertGreater(position, cursor, f"out-of-order contract: {phrase!r}")
            cursor = position

    def assert_exact_pipe_contract(
        self, text: str, label: str, expected_items: set[str]
    ) -> None:
        match = re.search(rf"{re.escape(label)}: (?P<items>[^.]+)\.", text)
        self.assertIsNotNone(match, f"missing structured contract: {label}")
        assert match is not None
        actual_items = {item.strip() for item in match.group("items").split("|")}
        self.assertEqual(expected_items, actual_items, label)

    def delete_pipe_contract_item(self, text: str, label: str, item: str) -> str:
        match = re.search(rf"{re.escape(label)}: (?P<items>[^.]+)\.", text)
        self.assertIsNotNone(match, f"missing structured contract: {label}")
        assert match is not None
        items = [entry.strip() for entry in match.group("items").split("|")]
        self.assertIn(item, items, f"missing mutation target: {item}")
        items.remove(item)
        replacement = f"{label}: {' | '.join(items)}."
        return text[: match.start()] + replacement + text[match.end() :]

    def assert_no_protected_waiver(
        self, text: str, protected_terms: set[str], boundary: str
    ) -> None:
        """Reject additive permissions that weaken a protected state boundary."""
        for sentence in re.split(r"(?<=[.!?])\s+", text):
            mentions_boundary = any(
                term.casefold() in sentence.casefold() for term in protected_terms
            )
            if not mentions_boundary or not PERMISSION_OR_WAIVER.search(sentence):
                continue
            if EXPLICIT_PROHIBITION.search(sentence):
                continue
            self.fail(f"{boundary} has an additive permission or waiver: {sentence!r}")

    def assert_skill_contract(self, skill: str, text: str) -> None:
        """Assert behavior relationships, not merely skill-file vocabulary."""
        text = " ".join(text.split())
        if skill == "grill-me":
            self.assertIn("one finite frontier for the scope", text)
            self.assertIn("Publish the global decision map before details", text)
            self.assertIn("Ask one bounded independent batch at a time", text)
            self.assertIn("Dependent questions are serial", text)
            self.assertIn("why it is critical", text)
            self.assertIn("observable condition that closes it", text)
            self.assertIn("semantic decision or frontier change", text)
            self.assertIn("An unchanged state is a no-op", text)
            self.assertIn(
                "Every persisted create, update, close, replace, or supersede mutation uses this public transaction",
                text,
            )
            route = re.search(
                r"1\. Run `discussion-transaction\.py inspect --project-root <project>`"
                r"(?P<inspect>.*?)2\. Run `discussion-transaction\.py schema "
                r"<create\|update\|close\|replace\|supersede>`(?P<schema>.*?)3\. Run "
                r"`discussion-transaction\.py apply --project-root <project> "
                r"--request <file>`(?P<apply>.*?)`apply` is the sole discussion writer\.",
                text,
            )
            self.assertIsNotNone(route, "Grill must use inspect → schema → apply")
            assert route is not None
            self.assertIn("returned active state and opaque revision", route.group("inspect"))
            self.assertIn("`expected_revision` field", route.group("schema"))
            self.assertIn("same expected revision", route.group("apply"))
            self.assertIn("`apply` is the sole discussion writer.", text)
            self.assert_exact_pipe_contract(
                text,
                "Direct-write prohibition (never write or rewrite)",
                GRILL_DIRECT_WRITE_TARGETS,
            )
            self.assertIn("CAS rejection of stale state", text)
            self.assertIn("atomic", text)
            self.assertIn("Mermaid route plus plain-text fallback", text)
            self.assertIn("`INDETERMINATE` result pauses", text)
            self.assertNotIn("```markdown", text)
            self.assertNotRegex(text, DIRECT_WRITE_PERMISSION)
            self.assertNotRegex(text, APPLY_WITHOUT_REVISION_PERMISSION)
            self.assert_no_protected_waiver(
                text, {"expected_revision", "expected revision"}, "expected revision"
            )
            self.assert_no_protected_waiver(
                text, GRILL_DIRECT_WRITE_TARGETS, "direct-write authority"
            )
            return
        if skill == "teamwork-explore":
            self.assertIn("local-only and read-only", text)
            self.assertIn("healthy CodeGraph first", text)
            self.assertIn("Separate observation from inference", text)
            self.assertIn("does not browse the web", text)
            return
        if skill == "teamwork-research":
            self.assertIn("external-only", text)
            self.assertIn("Before any Research method step", text)
            self.assertIn("Root's first role action", text)
            self.assertIn('`agent_type="teamwork_researcher"`', text)
            self.assertIn("Root MUST NOT browse", text)
            self.assertIn("MUST NOT call `wait_agent`", text)
            self.assertIn("non-empty live agent id", text)
            self.assertIn("wait without a live agent is STOP", text)
            self.assertIn("After the primary Researcher handoff", text)
            self.assert_in_order(text, "`lookup`", "`research`", "`deep`")
            self.assertIn("Source count is not claim coverage", text)
            self.assertIn("only for `deep`", text)
            return
        if skill == "teamwork-debug":
            self.assert_in_order(text, "`observe`", "`instrument`", "`fix`")
            self.assertIn("immutable authority", text)
            self.assertIn("Never infer or upgrade authority", text)
            return
        if skill == "teamwork-design":
            self.assertIn("only when an unresolved local constraint", text)
            self.assertIn("only for a named external or current claim", text)
            self.assertIn("Do not run both evidence tracks by default", text)
            self.assertIn(
                "After the initial evidence wave, select once before Designer critic/auditor dispatch",
                text,
            )
            self.assert_in_order(
                text,
                "## Establish The Decision",
                "## Select The Search Strategy",
                "## Resolve Trade-offs",
            )
            self.assertIn("`standard` keeps the default", text)
            self.assertIn("`adversarial` forces", text)
            self.assertIn("at least two viable directions", text)
            self.assertIn("costly or irreversible error or conflicting evidence", text)
            self.assertIn(
                "Risk, complexity, or brainstorm labels alone do not qualify",
                text,
            )
            self.assertIn("State the strategy and reason without confirmation", text)
            self.assertIn("load and follow `references/adversarial-search.md`", text)
            self.assertIn("exactly one challenge pass", text)
            self.assertIn(
                "In the default strategy, after recommending, perform exactly one challenge pass",
                text,
            )
            self.assertIn("at most one targeted delta", text)
            self.assertIn("Publish the global map before details", text)
            self.assertIn("Ask one bounded independent batch", text)
            self.assertIn("Dependent choices are serial", text)
            self.assertIn("why the answer is critical", text)
            self.assertIn("two consecutive rounds", text)
            self.assertIn("is not durable or Plan-ready", text)
            self.assertIn("explicitly accepts the direction and authorizes saving it", text)
            self.assertIn(
                "A Plan-ready handoff request counts only when it explicitly accepts that direction and authorizes the save",
                text,
            )
            self.assertIn("Freeze one durable Design", text)
            self.assertIn("structured Design state", text)
            self.assertIn("distinct critic and auditor identities", text)
            self.assertIn("never store raw agent transcripts", text)
            durable_route = re.search(
                r"The package-level Design transaction is the sole durable Design writer\."
                r" Every durable Design lifecycle uses this public route, in order: "
                r"1\. Run `discussion-transaction\.py design-inspect --project-root <project>`"
                r"(?P<inspect>.*?)2\. Run `discussion-transaction\.py design-schema "
                r"<create\|update\|supersede>`(?P<schema>.*?)3\. Run "
                r"`discussion-transaction\.py design-apply --project-root <project>`"
                r"(?P<apply>.*?)`design-render` and `design-validate` are read-only helpers only",
                text,
            )
            self.assertIsNotNone(durable_route, "Design must use inspect → schema → apply")
            assert durable_route is not None
            self.assertIn("active state and returned revision", durable_route.group("inspect"))
            self.assertIn("`expected_revision` from inspect", durable_route.group("schema"))
            self.assertIn("structured state", durable_route.group("schema"))
            self.assertIn("`state.slug` and `state.updated`", durable_route.group("schema"))
            self.assertIn("`--request <file>` or `--request-json <json>`", durable_route.group("apply"))
            self.assertIn("atomically renders, validates, and writes", durable_route.group("apply"))
            self.assertIn("artifact plus `active.design`", durable_route.group("apply"))
            self.assertIn("path, revision, and changed paths", durable_route.group("apply"))
            self.assertIn("Never hand-author, redirect renderer output into, or directly edit", text)
            self.assertNotRegex(text, HAND_AUTHORED_DESIGN_PERMISSION)
            self.assert_no_protected_waiver(
                text,
                {
                    "expected_revision",
                    "expected revision",
                    "design-apply",
                    "active.design",
                    "Design Markdown",
                    "route map",
                    "text fallback",
                },
                "controlled Design ownership",
            )
            return
        if skill == "teamwork-plan":
            self.assertIn("only when the user requests it or a named material risk gate requires it", text)
            self.assertIn("require the controlled durable Design path and revision", text)
            self.assertIn("A conversational Design recommendation", text)
            self.assertIn("is not Plan-ready", text)
            self.assertIn("stable `PR-*`", text)
            self.assertIn("reviewed Plan cannot pass with placeholders", text)
            return
        if skill == "teamwork-review":
            self.assertIn("sealed integrated candidate", text)
            self.assertIn("one independent initial pass", text)
            self.assertIn("one repair batch", text)
            self.assertIn("at most one bounded delta recheck per candidate", text)
            self.assertIn("Do not review each Worker slice", text)
            self.assert_in_order(text, "Check correctness first", "Then inspect only the changed scope")
            self.assertIn("stable `R-*`", text)
            self.assertIn("purely pre-existing debt", text)
            return
        if skill == "teamwork-goal":
            self.assertIn("durable Goal state at entry", text)
            self.assertIn("single current unmet claim", text)
            self.assertIn("strategy delta", text)
            return
        if skill == "teamwork-init":
            self.assertIn("only for an explicit full bootstrap", text)
            self.assertIn("must not manufacture that broad matrix", text)
            self.assertIn("candidate-only context", text)
            self.assertIn("never as project or Teamwork truth", text)
            self.assert_exact_pipe_contract(
                text,
                "Candidate-promotion gates (all must pass)",
                INIT_PROMOTION_GATES,
            )
            self.assertIn("until those five gates pass", text)
            self.assertIn(
                "A logged, partial, or permissive gate result is not promotion", text
            )
            self.assertNotRegex(text, PERMISSIVE_PROMOTION)
            self.assert_no_protected_waiver(
                text, INIT_PROMOTION_GATES, "candidate-promotion gates"
            )
            return
        if skill == "teamwork-update":
            self.assertIn("global installation surfaces only", text)
            self.assertIn("Dispatch Explorer", text)
            self.assertIn("Dispatch Worker", text)
            self.assertIn("privileged surfaces remain with Root", text)
            return
        self.fail(f"missing contract validator for {skill}")

    def assert_advanced_reference_contract(
        self, skill: str, reference: str, text: str
    ) -> None:
        text = " ".join(text.split())
        if (skill, reference) == ("teamwork-research", "deep-research.md"):
            self.assert_in_order(
                text,
                "research brief",
                "source census",
                "claim ledger",
                "contradictions",
                "coverage audit",
                "stop basis",
            )
            self.assertIn("Never average conflicting sources", text)
            return
        if (skill, reference) == ("teamwork-debug", "runtime-diagnosis.md"):
            self.assertIn("fixed dispatch authority", text)
            self.assertIn("human-only", text)
            self.assert_in_order(
                text, "Remove every temporary", "original failure path"
            )
            return
        if (skill, reference) == ("teamwork-design", "adversarial-search.md"):
            self.assertIn("selects it automatically or an explicit adversarial override", text)
            self.assertIn("Accept a user override only when `2 <= B <= 5`", text)
            self.assertIn("reject an out-of-range override", text)
            self.assertIn("`B = 3`", text)
            self.assertIn("do not request confirmation", text)
            self.assertIn(
                "maximum adversarial critic/auditor cost is `2B + 2` fresh dispatches",
                text,
            )
            self.assertIn("add it to the total envelope", text)
            self.assertIn(
                "Every actual hypothesis gets exactly two fresh Designer critics", text
            )
            self.assertIn(
                "Exclude a material cell without a trial only when named direct evidence proves",
                text,
            )
            self.assertIn("more non-excluded material cells than `B`", text)
            self.assertIn("do not merge, demote, or silently skip cells", text)
            self.assertIn("A materially revised hypothesis is a new trial", text)
            self.assertIn("Launch exactly two final Designer auditors", text)
            self.assertIn(
                "Converge only when both final auditors return `PASS`", text
            )
            self.assertIn("final unit of `B` is valid closure", text)
            self.assertIn(
                "`budget-exhausted` applies only when another trial or audit repair is still required",
                text,
            )
            self.assert_exact_pipe_contract(
                text,
                "Adversarial failure states",
                {
                    "budget-exhausted",
                    "audit-failed",
                    "freshness-unproven",
                    "capability-blocked",
                    "interrupted",
                },
            )
            self.assertIn("never store raw agent transcripts", text)
            return
        if (skill, reference) == ("teamwork-review", "strict-review.md"):
            self.assert_in_order(text, "correctness first", "changed-scope cohesion")
            self.assertIn("stable `R-*`", text)
            self.assertIn("read-only", text)
            return
        self.fail(f"missing advanced-reference validator for {skill}/{reference}")

    def test_exact_flat_skill_inventory(self) -> None:
        actual = {path.name for path in SKILLS.iterdir() if path.is_dir()}
        self.assertEqual(EXPECTED_SKILLS, actual)

        expected_files = {SKILLS / name / "SKILL.md" for name in EXPECTED_SKILLS}
        expected_files.update(
            SKILLS / skill / "references" / reference
            for skill, reference in EXPECTED_REFERENCES.items()
        )
        actual_files = {path for path in SKILLS.rglob("*") if path.is_file()}
        self.assertEqual(expected_files, actual_files)

        expected_directories = {SKILLS / name for name in EXPECTED_SKILLS}
        expected_directories.update(
            SKILLS / skill / "references" for skill in EXPECTED_REFERENCES
        )
        actual_directories = {path for path in SKILLS.rglob("*") if path.is_dir()}
        self.assertEqual(expected_directories, actual_directories)

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
            expected = (
                {EXPECTED_REFERENCES[skill]} if skill in EXPECTED_REFERENCES else set()
            )
            self.assertEqual(expected, references, path)

        for skill, reference in EXPECTED_REFERENCES.items():
            path = SKILLS / skill / "references" / reference
            text = path.read_text(encoding="utf-8")
            self.assertNotRegex(text, r"references/[a-z0-9-]+\.md", path)
            for other_skill in EXPECTED_SKILLS - {skill}:
                self.assertNotIn(other_skill, text, path)

    def test_no_skill_invokes_another_or_restores_retired_aliases(self) -> None:
        retired = {"using-teamwork", "teamwork-execute"}
        for skill in EXPECTED_SKILLS:
            path = SKILLS / skill / "SKILL.md"
            _, body = parse_frontmatter(path)
            for other_skill in EXPECTED_SKILLS - {skill}:
                self.assertNotIn(other_skill, body, path)
            for alias in retired:
                self.assertNotIn(alias, body, path)

    def test_required_behavior_is_owned_by_the_right_skill(self) -> None:
        for skill in EXPECTED_SKILLS:
            text = (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")
            with self.subTest(skill=skill):
                self.assert_skill_contract(skill, text)

    def test_contract_inversions_and_deletions_are_rejected(self) -> None:
        """Guard the owner contracts against a plausible weakening, not just absence."""
        mutations = {
            "teamwork-explore": [("local-only and read-only", "local or external and writable")],
            "teamwork-research": [
                ("external-only", "local-only"),
                ("Root's first role action", "Root may answer directly"),
                ("Root MUST NOT browse", "Root may browse"),
                ("MUST NOT call `wait_agent`", "may call `wait_agent`"),
            ],
            "teamwork-debug": [("Never infer or upgrade authority", "May infer or upgrade authority")],
            "teamwork-design": [
                (
                    "In the default strategy, after recommending, perform exactly one challenge pass",
                    "In every strategy, perform unlimited challenge passes",
                ),
                ("Ask one bounded independent batch", "Ask every open item together"),
                ("at least two viable directions", "any single direction"),
                (
                    "After the initial evidence wave, select once before Designer critic/auditor dispatch",
                    "Select before the initial evidence wave",
                ),
                (
                    "State the strategy and reason without confirmation",
                    "Ask for strategy confirmation",
                ),
                (
                    "A Plan-ready handoff request counts only when it explicitly accepts that direction and authorizes the save",
                    "A Plan-ready handoff request bypasses acceptance and save authority",
                ),
            ],
            "teamwork-plan": [
                (
                    "only when the user requests it or a named material risk gate requires it",
                    "for every Plan",
                ),
                (
                    "A conversational Design recommendation",
                    "Any conversational Design recommendation",
                ),
            ],
            "teamwork-review": [("Check correctness first", "Check deslop first")],
            "teamwork-goal": [("durable Goal state at entry", "optional Goal state after attempts")],
            "teamwork-update": [("global installation surfaces only", "project-local surfaces too")],
        }
        for skill, changes in mutations.items():
            original = " ".join(
                (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8").split()
            )
            for before, after in changes:
                with self.subTest(skill=skill, before=before):
                    mutated = original.replace(before, after, 1)
                    self.assertNotEqual(original, mutated, "mutation fixture must apply")
                    with self.assertRaises(AssertionError):
                        self.assert_skill_contract(skill, mutated)

    def test_design_adversarial_reference_inversions_are_rejected(self) -> None:
        skill = "teamwork-design"
        reference = "adversarial-search.md"
        original = " ".join(
            (SKILLS / skill / "references" / reference)
            .read_text(encoding="utf-8")
            .split()
        )
        for before, after in (
            (
                "selects it automatically or an explicit adversarial override",
                "runs only after explicit adversarial wording",
            ),
            ("reject an out-of-range override", "accept any override"),
            ("do not request confirmation", "request confirmation"),
            ("exactly two fresh Designer critics", "one reused Designer critic"),
            (
                "Exclude a material cell without a trial only when named direct evidence proves",
                "Exclude any material cell without a trial when Root prefers",
            ),
            ("both final auditors return `PASS`", "one final auditor returns `PASS`"),
            ("final unit of `B` is valid closure", "final unit of `B` always fails"),
        ):
            with self.subTest(before=before):
                mutated = original.replace(before, after, 1)
                self.assertNotEqual(original, mutated, "mutation fixture must apply")
                with self.assertRaises(AssertionError):
                    self.assert_advanced_reference_contract(skill, reference, mutated)

    def test_grill_transaction_deletions_and_inversions_are_rejected(self) -> None:
        original = " ".join((SKILLS / "grill-me" / "SKILL.md").read_text(encoding="utf-8").split())
        for required_fragment in (
            "opaque revision",
            "`expected_revision` field",
            "same expected revision",
        ):
            with self.subTest(deleted=required_fragment):
                mutated = original.replace(required_fragment, "", 1)
                self.assertNotEqual(original, mutated, "mutation fixture must apply")
                with self.assertRaises(AssertionError):
                    self.assert_skill_contract("grill-me", mutated)

        mandate = "Every persisted create, update, close, replace, or supersede mutation uses this public transaction"
        schema = "schema <create|update|close|replace|supersede>"
        for lifecycle in GRILL_LIFECYCLES:
            with self.subTest(deleted_lifecycle=lifecycle):
                shortened_mandate = mandate.replace(
                    f", {lifecycle}", "", 1
                ).replace(f"{lifecycle}, ", "", 1).replace(f"or {lifecycle}", "")
                shortened_schema = schema.replace(
                    f"|{lifecycle}", "", 1
                ).replace(f"{lifecycle}|", "", 1)
                mutated = original.replace(mandate, shortened_mandate, 1).replace(
                    schema, shortened_schema, 1
                )
                self.assertNotEqual(original, mutated, "mutation fixture must apply")
                with self.assertRaises(AssertionError):
                    self.assert_skill_contract("grill-me", mutated)

        for target in GRILL_DIRECT_WRITE_TARGETS:
            with self.subTest(deleted_direct_write_target=target):
                mutated = self.delete_pipe_contract_item(
                    original,
                    "Direct-write prohibition (never write or rewrite)",
                    target,
                )
                with self.assertRaises(AssertionError):
                    self.assert_skill_contract("grill-me", mutated)

        for before, after in (
            ("`apply` is the sole discussion writer.", "`apply` is an optional writer."),
            (
                "Direct-write prohibition (never write or rewrite)",
                "Direct-write permission (may write or rewrite)",
            ),
            ("CAS rejection of stale state", "best-effort stale state"),
            ("locking and atomic commit/readback", "locking and best-effort commit/readback"),
            ("Mermaid route plus plain-text fallback", "independent diagram renderers"),
        ):
            with self.subTest(inverted=before):
                mutated = original.replace(before, after, 1)
                self.assertNotEqual(original, mutated, "mutation fixture must apply")
                with self.assertRaises(AssertionError):
                    self.assert_skill_contract("grill-me", mutated)

    def test_init_promotion_gate_deletions_and_inversions_are_rejected(self) -> None:
        original = " ".join((SKILLS / "teamwork-init" / "SKILL.md").read_text(encoding="utf-8").split())
        for gate in INIT_PROMOTION_GATES:
            with self.subTest(deleted_gate=gate):
                mutated = self.delete_pipe_contract_item(
                    original,
                    "Candidate-promotion gates (all must pass)",
                    gate,
                )
                with self.assertRaises(AssertionError):
                    self.assert_skill_contract("teamwork-init", mutated)

        for before, after in (
            ("Candidate-promotion gates (all must pass)", "Candidate-promotion gates (logged gates may pass)"),
            ("until those five gates pass", "when any logged gate passes"),
            (
                "A logged, partial, or permissive gate result is not promotion",
                "A logged, partial, or permissive gate result is promotion",
            ),
        ):
            with self.subTest(inverted=before):
                mutated = original.replace(before, after, 1)
                self.assertNotEqual(original, mutated, "mutation fixture must apply")
                with self.assertRaises(AssertionError):
                    self.assert_skill_contract("teamwork-init", mutated)

    def test_additive_permission_and_exception_escape_hatches_are_rejected(self) -> None:
        grill = " ".join((SKILLS / "grill-me" / "SKILL.md").read_text(encoding="utf-8").split())
        for target in GRILL_DIRECT_WRITE_TARGETS:
            with self.subTest(added_direct_write_permission=target):
                mutated = f"{grill} Exception: Grill may directly write {target}."
                with self.assertRaises(AssertionError):
                    self.assert_skill_contract("grill-me", mutated)
                generic = f"{grill} Direct-write exception permits rewrite of {target}."
                with self.assertRaises(AssertionError):
                    self.assert_skill_contract("grill-me", generic)
        for exception in (
            "Exception: apply may proceed without expected_revision.",
            "Emergency fallback: without expected revision, apply can proceed.",
            "The expected_revision is optional before apply.",
        ):
            with self.subTest(added_apply_escape=exception):
                mutated = f"{grill} {exception}"
                with self.assertRaises(AssertionError):
                    self.assert_skill_contract("grill-me", mutated)
        for lifecycle in GRILL_LIFECYCLES:
            exception = f"Exception: {lifecycle} may proceed without expected_revision."
            with self.subTest(added_lifecycle_revision_escape=exception):
                mutated = f"{grill} {exception}"
                with self.assertRaises(AssertionError):
                    self.assert_skill_contract("grill-me", mutated)
            direct_write = (
                f"Exception: {lifecycle} may directly write the discussion artifact."
            )
            with self.subTest(added_lifecycle_direct_write_escape=direct_write):
                mutated = f"{grill} {direct_write}"
                with self.assertRaises(AssertionError):
                    self.assert_skill_contract("grill-me", mutated)

        init = " ".join((SKILLS / "teamwork-init" / "SKILL.md").read_text(encoding="utf-8").split())
        for exception in (
            "Exception: logged evidence may promote candidate material.",
            "Partial gate results are sufficient to promote docs-graph output.",
            "Permissive gate fallback permits promotion of external-memory output.",
            "Candidate material may be promoted after a logged gate.",
        ):
            with self.subTest(added_promotion_escape=exception):
                mutated = f"{init} {exception}"
                with self.assertRaises(AssertionError):
                    self.assert_skill_contract("teamwork-init", mutated)

    def test_generalized_protected_contract_waivers_are_rejected(self) -> None:
        design = " ".join(
            (SKILLS / "teamwork-design" / "SKILL.md").read_text(encoding="utf-8").split()
        )
        for exception in (
            "Exception: design-apply may proceed without expected_revision.",
            "Emergency waiver: expected revision is optional for design-apply.",
            "Root can bypass expected_revision before controlled Design apply.",
            "Exception: Design may directly write active.design.",
            "Fallback permission allows direct update of active.design.",
            "Emergency override: design-apply may be replaced by a manual artifact write.",
        ):
            with self.subTest(design_waiver=exception):
                mutated = f"{design} {exception}"
                with self.assertRaises(AssertionError):
                    self.assert_skill_contract("teamwork-design", mutated)

        init = " ".join(
            (SKILLS / "teamwork-init" / "SKILL.md").read_text(encoding="utf-8").split()
        )
        for gate in INIT_PROMOTION_GATES:
            for exception in (
                f"Exception: Root may promote candidate material without {gate}.",
                f"Waiver: {gate} can be skipped during candidate promotion.",
            ):
                with self.subTest(gate=gate, promotion_waiver=exception):
                    mutated = f"{init} {exception}"
                    with self.assertRaises(AssertionError):
                        self.assert_skill_contract("teamwork-init", mutated)

    def test_design_controlled_route_deletions_and_manual_write_escapes_are_rejected(self) -> None:
        original = " ".join((SKILLS / "teamwork-design" / "SKILL.md").read_text(encoding="utf-8").split())
        for required_fragment in (
            "structured Design state",
            "Design transaction is the sole durable Design writer",
            "design-inspect --project-root <project>",
            "design-schema <create|update|supersede>",
            "`expected_revision` from inspect",
            "`state.slug` and `state.updated`",
            "design-apply --project-root <project>",
            "`--request <file>` or `--request-json <json>`",
            "atomically renders, validates, and writes",
            "artifact plus `active.design`",
            "path, revision, and changed paths",
            "`design-render` and `design-validate` are read-only helpers only",
        ):
            with self.subTest(deleted=required_fragment):
                mutated = original.replace(required_fragment, "", 1)
                self.assertNotEqual(original, mutated, "mutation fixture must apply")
                with self.assertRaises(AssertionError):
                    self.assert_skill_contract("teamwork-design", mutated)

        for exception in (
            "Exception: Designer may hand-author Design Markdown.",
            "Fallback: Design can directly write the artifact map.",
            "Recovery path: Design is allowed to edit its text fallback.",
        ):
            with self.subTest(added_manual_design_write=exception):
                mutated = f"{original} {exception}"
                with self.assertRaises(AssertionError):
                    self.assert_skill_contract("teamwork-design", mutated)

    def test_advanced_references_preserve_their_named_contracts(self) -> None:
        for skill, reference in (
            ("teamwork-research", "deep-research.md"),
            ("teamwork-debug", "runtime-diagnosis.md"),
            ("teamwork-design", "adversarial-search.md"),
            ("teamwork-review", "strict-review.md"),
        ):
            text = (SKILLS / skill / "references" / reference).read_text(
                encoding="utf-8"
            )
            with self.subTest(skill=skill, reference=reference):
                self.assert_advanced_reference_contract(skill, reference, text)

    def test_advanced_reference_deletions_are_rejected(self) -> None:
        contracts = {
            ("teamwork-research", "deep-research.md"): "claim ledger",
            ("teamwork-debug", "runtime-diagnosis.md"): "Remove every temporary",
            ("teamwork-design", "adversarial-search.md"): "exactly two fresh Designer critics",
            ("teamwork-review", "strict-review.md"): "correctness first",
        }
        for (skill, reference), phrase in contracts.items():
            path = SKILLS / skill / "references" / reference
            original = " ".join(path.read_text(encoding="utf-8").split())
            mutated = original.replace(phrase, "", 1)
            self.assertNotEqual(original, mutated, "mutation fixture must apply")
            with self.subTest(skill=skill, reference=reference):
                with self.assertRaises(AssertionError):
                    self.assert_advanced_reference_contract(skill, reference, mutated)


if __name__ == "__main__":
    unittest.main()
