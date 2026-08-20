from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[2]


class CoreFlowTests(unittest.TestCase):
    def test_writer_and_plain_markdown_document_templates_are_complete(self) -> None:
        topology = json.loads((ROOT / "config/teamwork-topology.json").read_text(encoding="utf-8"))
        agents = {row["name"]: row["templates"] for row in topology["agents"]}
        self.assertEqual(
            agents["writer"],
            {
                "codex": "templates/codex-agents/teamwork-writer.toml",
                "cursor": "templates/cursor-agents/writer.md",
                "claude": "templates/claude-agents/writer.md",
            },
        )
        writer = (ROOT / agents["writer"]["codex"]).read_text(encoding="utf-8")
        self.assertIn('model = "gpt-5.6-luna"', writer)
        self.assertIn('model_reasoning_effort = "high"', writer)
        self.assertIn('service_tier = "default"', writer)
        self.assertIn('sandbox_mode = "workspace-write"', writer)

        documents = {row["name"]: row["path"] for row in topology["document_templates"]}
        self.assertEqual(
            set(documents),
            {"discussion", "research", "debug", "plan", "review", "report"},
        )
        for path in documents.values():
            template = (ROOT / path).read_text(encoding="utf-8")
            self.assertTrue(template.startswith("# "), path)
            self.assertIn("## History", template, path)
            self.assertIn("Append only", template, path)

    def test_writer_document_resources_resolve_after_copy_install(self) -> None:
        expected = {
            "teamwork-collaborate": "references/discussion.md",
            "teamwork-research": "references/research.md",
            "teamwork-debug": "references/debug.md",
            "teamwork-plan": "references/plan.md",
            "teamwork-review": "references/review.md",
            "teamwork-goal": "references/report.md",
            "teamwork-init": "references/report.md",
            "teamwork-update": "references/report.md",
        }
        with tempfile.TemporaryDirectory() as raw:
            env = os.environ.copy()
            env["HOME"] = raw
            env["CODEX_HOME"] = str(Path(raw) / ".codex")
            result = subprocess.run(
                [
                    str(ROOT / "install.sh"),
                    "--copy",
                    "--no-notifications",
                    "--no-codex-routing",
                    "codex",
                ],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            installed = Path(raw) / ".agents/skills"
            for skill, reference in expected.items():
                skill_root = installed / skill
                skill_text = (skill_root / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn(f"`{reference}`", skill_text)
                self.assertTrue((skill_root / reference).is_file(), f"{skill}/{reference}")

            collaborate_root = installed / "teamwork-collaborate"
            self.assertIn("`references/experiment.md`", (collaborate_root / "SKILL.md").read_text(encoding="utf-8"))
            self.assertTrue((collaborate_root / "references/experiment.md").is_file())

            report_texts = {
                (installed / skill / "references/report.md").read_text(encoding="utf-8")
                for skill in ("teamwork-goal", "teamwork-init", "teamwork-update")
            }
            self.assertEqual(len(report_texts), 1)

    def test_codex_agent_profiles_render_the_expected_role_tradeoffs(self) -> None:
        main_threads = {
            "performance-first": ("gpt-5.6-terra", "xhigh"),
            "cost-first": ("gpt-5.6-luna", "high"),
        }
        expected = {
            "performance-first": {
                "challenger": ("gpt-5.6-sol", "high"),
                "debugger": ("gpt-5.6-sol", "xhigh"),
                "explorer": ("gpt-5.6-terra", "high"),
                "planner": ("gpt-5.6-terra", "xhigh"),
                "researcher": ("gpt-5.6-terra", "xhigh"),
                "reviewer": ("gpt-5.6-sol", "xhigh"),
                "worker": ("gpt-5.6-sol", "medium"),
                "writer": ("gpt-5.6-luna", "high"),
            },
            "cost-first": {
                "challenger": ("gpt-5.6-luna", "high"),
                "debugger": ("gpt-5.6-luna", "xhigh"),
                "explorer": ("gpt-5.6-luna", "high"),
                "planner": ("gpt-5.6-luna", "xhigh"),
                "researcher": ("gpt-5.6-luna", "xhigh"),
                "reviewer": ("gpt-5.6-luna", "xhigh"),
                "worker": ("gpt-5.6-luna", "high"),
                "writer": ("gpt-5.6-luna", "high"),
            },
        }
        for profile, roles in expected.items():
            with self.subTest(profile=profile), tempfile.TemporaryDirectory() as raw:
                env = os.environ.copy()
                env["HOME"] = raw
                env["CODEX_HOME"] = str(Path(raw) / ".codex")
                result = subprocess.run(
                    [
                        str(ROOT / "install.sh"),
                        "--copy",
                        "--profile",
                        profile,
                        "codex-agents",
                    ],
                    env=env,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                main_config = tomllib.loads(
                    (Path(raw) / ".codex/config.toml").read_text(encoding="utf-8")
                )
                self.assertEqual(main_config["model"], main_threads[profile][0])
                self.assertEqual(
                    main_config["model_reasoning_effort"], main_threads[profile][1]
                )
                for role, (model, effort) in roles.items():
                    path = Path(raw) / ".codex/agents" / f"teamwork-{role}.toml"
                    rendered = tomllib.loads(path.read_text(encoding="utf-8"))
                    self.assertEqual(rendered["model"], model, path)
                    self.assertEqual(rendered["model_reasoning_effort"], effort, path)

    def test_codex_profile_config_migration_preserves_user_settings(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            config = Path(raw) / "config.toml"
            config.write_text(
                "#:schema https://developers.openai.com/codex/config-schema.json\n"
                'model = "gpt-5.6-luna" # existing default\n'
                'model_reasoning_effort = "max"\n'
                'personality = "friendly"\n'
                "\n"
                "[features]\n"
                "multi_agent_v2 = true\n"
                "\n"
                "[mcp_servers.example]\n"
                'command = "example"\n',
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/configure-codex-routing.py"),
                    "--apply",
                    "--default-model",
                    "gpt-5.6-terra",
                    "--default-effort",
                    "xhigh",
                    "--config",
                    str(config),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("CHANGES=set model; set model_reasoning_effort; add features.multi_agent", result.stdout)
            config_text = config.read_text(encoding="utf-8")
            rendered = tomllib.loads(config_text)
            self.assertEqual(rendered["model"], "gpt-5.6-terra")
            self.assertEqual(rendered["model_reasoning_effort"], "xhigh")
            self.assertEqual(rendered["personality"], "friendly")
            self.assertTrue(rendered["features"]["multi_agent"])
            self.assertTrue(rendered["features"]["multi_agent_v2"])
            self.assertEqual(rendered["mcp_servers"]["example"]["command"], "example")
            self.assertIn('# existing default', config_text)

    def test_schema_index_and_migration_runtime_remain_absent(self) -> None:
        retired = (
            "scripts/migrate-teamwork-documents.py",
            "scripts/teamwork_index_v4.py",
            "scripts/teamwork-documents-schema.json",
        )
        for path in retired:
            self.assertFalse((ROOT / path).exists(), path)

    def test_project_init_is_idempotent_and_stateless(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            project = Path(raw)
            command = [
                sys.executable,
                str(ROOT / "scripts/init-project-files.py"),
                "--project-root",
                str(project),
                "initialize",
            ]
            subprocess.run(command, check=True)
            subprocess.run(command, check=True)
            agents = (project / "AGENTS.md").read_text(encoding="utf-8")
            self.assertEqual(agents.count("<!-- TEAMWORK_PROJECT_START -->"), 1)
            self.assertIn("no required project-local workflow or state", agents)
            self.assertFalse((project / "docs/teamwork").exists())

    def test_readiness_is_informational(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            env = os.environ.copy()
            env["HOME"] = raw
            env["CODEX_HOME"] = str(Path(raw) / ".codex")
            result = subprocess.run(
                [str(ROOT / "scripts/check-update.sh"), "--readiness"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("INSTALL_STATE=partial", result.stdout)
            self.assertIn("BLOCKS_OTHER_WORK=no", result.stdout)

    def _skill_text(self, name: str) -> str:
        return (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")

    @staticmethod
    def _folded(text: str) -> str:
        return " ".join(text.split())

    def _frontmatter_description(self, skill_text: str) -> str:
        self.assertTrue(skill_text.startswith("---\n"), skill_text[:40])
        end = skill_text.find("\n---\n", 4)
        self.assertGreater(end, 0)
        block = skill_text[4:end]
        prefix = "description: "
        for line in block.splitlines():
            if line.startswith(prefix):
                return line[len(prefix) :]
        self.fail("missing description frontmatter")

    def _section_after(self, skill_text: str, marker: str) -> str:
        start = skill_text.find(marker)
        self.assertGreaterEqual(start, 0, f"missing {marker} section")
        rest = skill_text[start + len(marker) :]
        nxt = rest.find("\n## ")
        return rest if nxt < 0 else rest[:nxt]

    def _method_section(self, skill_text: str) -> str:
        return self._section_after(skill_text, "## Method")

    def _persistence_section(self, skill_text: str) -> str:
        return self._section_after(skill_text, "## Persistence")

    def test_collaborate_description_requires_unclear_intent_not_one_detail(self) -> None:
        description = self._frontmatter_description(self._skill_text("teamwork-collaborate"))
        self.assertIn("unclear intent", description)
        self.assertIn("guided clarification", description)
        self.assertIn("do not use for clear execution or a single discoverable detail", description)

    def test_collaborate_keeps_recorded_locks_and_separates_quotes(self) -> None:
        skill = self._folded(self._skill_text("teamwork-collaborate"))
        self.assertIn(
            "Recorded rejections and decisions are the mainline; research or a "
            "subagent return must not restate them as a new question.",
            skill,
        )
        self.assertIn(
            "Keep user quotes separate from the working understanding.",
            skill,
        )
        self.assertIn(
            "The next turn on the same subject reads the discussion document's "
            "current synthesis first when that document exists.",
            skill,
        )
        self.assertIn(
            "Session recall may be used on the next turn only after a write is "
            "observed unavailable or failed",
            skill,
        )
        self.assertIn("marked as not persisted", skill)
        self.assertIn(
            "A missing document is not a license to skip a fired checkpoint write",
            skill,
        )
        self.assertNotIn(
            "If the document is missing, session recall may be used",
            skill,
        )
        self.assertIn("Start from facts, constraints, and the goal", skill)
        self.assertIn("three axes", skill)
        self.assertIn("Lead with the claim", skill)
        self.assertIn("same final goal plus the same subject", skill)
        self.assertIn("name the document you read", skill)
        raw = self._skill_text("teamwork-collaborate")
        self.assertNotIn("\n### ", raw)
        method = self._folded(self._method_section(raw))
        self.assertIn("references/experiment.md", method)
        self.assertIn("Otherwise skip Experiment", method)
        experiment = (
            ROOT / "skills/teamwork-collaborate/references/experiment.md"
        ).read_text(encoding="utf-8")
        self.assertIn("condition-gated", experiment)
        self.assertIn("Main table", experiment)
        self.assertIn("Appendix hygiene", experiment)
        self.assertIn("Exploratory probe", experiment)
        self.assertNotIn("Encourage practice", experiment)
        template = (
            ROOT / "skills/teamwork-collaborate/references/discussion.md"
        ).read_text(encoding="utf-8")
        self.assertIn("## User quotes", template)
        self.assertIn("## Working understanding", template)
        self.assertIn("## Experiment slot", template)
        self.assertIn("Used only when the Experiment step fired", template)
        self.assertIn(
            "user's original wording, especially recorded rejections and decisions",
            template,
        )
        self.assertIn("do not write this as the user's wording", template)

    def test_debug_freezes_observe_instrument_fix_and_runtime_log_first(self) -> None:
        skill = self._folded(self._skill_text("teamwork-debug"))
        self.assertIn("freeze observe, instrument, and fix permission", skill)
        self.assertIn(
            "For a runtime unknown, use structured logging first when it is that discriminator",
            skill,
        )
        self.assertIn("keep non-runtime or already-isolated failures probe-minimal", skill)
        templates = (
            ROOT / "templates/codex-agents/teamwork-debugger.toml",
            ROOT / "templates/claude-agents/debugger.md",
        )
        for path in templates:
            text = self._folded(path.read_text(encoding="utf-8"))
            self.assertRegex(text, r"observe.{0,40}instrument.{0,40}fix", path.name)
            self.assertIn("structured logging first", text, path.name)
            self.assertIn("runtime unknown", text, path.name)
            self.assertIn("must not expand repair authority", text, path.name)

    def test_goal_mentions_invariants_and_attempt_record(self) -> None:
        skill = self._folded(self._skill_text("teamwork-goal"))
        self.assertIn("Invariants", skill)
        self.assertIn("Attempt Record", skill)

    def test_review_marks_missing_evidence_unknown_and_names_protected_boundary(self) -> None:
        skill = self._skill_text("teamwork-review")
        self.assertIn("missing evidence is `unknown`", skill)
        self.assertIn("protected boundary", skill)

    def test_init_and_update_report_observed_noop(self) -> None:
        for name in ("teamwork-init", "teamwork-update"):
            with self.subTest(skill=name):
                skill = self._skill_text(name)
                self.assertIn("observed no-op", skill)
                persistence = self._folded(self._persistence_section(skill))
                self.assertIn("Persistence is optional", persistence)
                self.assertIn("same response cycle", persistence)
                self.assertIn("Root owns document delivery", persistence)
                self.assertIn("does not delay the current checkpoint write", persistence)
                self.assertIn("Root may write the same template", persistence)
                self.assertNotIn("Prefer Writer", persistence)
                self.assertNotIn("Root fallback", persistence)

    def test_each_skill_persistence_section_retains_path_and_identity(self) -> None:
        mandatory = (
            "teamwork-collaborate",
            "teamwork-research",
            "teamwork-debug",
            "teamwork-plan",
            "teamwork-review",
            "teamwork-goal",
        )
        for name in mandatory:
            with self.subTest(skill=name):
                skill = self._skill_text(name)
                section = self._folded(self._persistence_section(skill))
                self.assertIn("docs/teamwork/", section)
                self.assertIn("<YYYY-MM-DD>-<slug>.md", section)
                self.assertIn("references/", section)
                self.assertIn("Same identity means", section)
                self.assertIn("reuse that path", section)
                self.assertIn("name the document you read", section)
                self.assertIn("A different subject gets a new path", section)
                self.assertIn("Checkpoints:", section)
                self.assertIn("same response cycle", section)
                self.assertIn("separate stable identities", section)
                self.assertNotIn("no-write", section)
                self.assertNotIn("Root fallback", section)
                self.assertNotIn("unavailable or returns a no-write", section)
                self.assertNotIn("helper role with its own writing contract", section)
                self.assertNotIn("Root writes the same template", section)
                self.assertNotIn("silently skipping", section.lower())
                self.assertNotIn("Skill violation", skill)
                self.assertNotIn("before closeout", skill)
                self.assertNotIn("expected base", skill)
                self.assertNotIn("owner-certified semantic delta", skill)
                self.assertNotIn("Do not write the checkpoint document yourself", section)

    def test_skill_methods_return_results_without_checkpoint_gate(self) -> None:
        mandatory = (
            "teamwork-collaborate",
            "teamwork-research",
            "teamwork-debug",
            "teamwork-plan",
            "teamwork-review",
            "teamwork-goal",
        )
        for name in mandatory:
            with self.subTest(skill=name):
                skill = self._skill_text(name)
                method = self._folded(self._method_section(skill))
                persistence = self._folded(self._persistence_section(skill))
                self.assertNotIn("before closeout", method)
                self.assertNotIn("host plan or question UI does not complete", method)
                self.assertNotIn("unavailable or returns a no-write", method)
                self.assertNotIn("Root writes the same template", method)
                self.assertNotIn("Root fallback", method)
                self.assertNotIn("prefer Writer", method.lower())
                self.assertNotIn("silently skipping", persistence.lower())
                self.assertNotIn("Do not write the checkpoint document yourself", skill)
                self.assertNotIn("CreatePlan", skill)
                self.assertNotIn("AskQuestion", skill)
                self.assertNotIn("AskUserQuestion", skill)
                self.assertNotIn("subagent_type: writer", skill)
                self.assertNotIn(".cursor/plans", skill)

        for name in ("teamwork-init", "teamwork-update"):
            with self.subTest(skill=name):
                skill = self._skill_text(name)
                method = self._folded(self._method_section(skill))
                persistence = self._folded(self._persistence_section(skill))
                self.assertNotIn("wake Writer before closing out", method)
                self.assertIn("Persistence is optional", persistence)
                self.assertNotIn("Do not write the checkpoint document yourself", skill)
                self.assertNotIn("CreatePlan", skill)
                self.assertNotIn("AskQuestion", skill)

        collaborate_skill = self._skill_text("teamwork-collaborate")
        collaborate = self._folded(self._method_section(collaborate_skill))
        persistence = self._folded(self._persistence_section(collaborate_skill))
        self.assertIn("next authorized action", collaborate)
        self.assertIn("do not open a new evidence gate", collaborate)
        self.assertIn("references/experiment.md", collaborate)
        self.assertIn("Otherwise skip Experiment", collaborate)
        self.assertNotIn("\n### ", collaborate_skill)
        self.assertIn("decision, recommendation, or unresolved question batch", persistence)
        self.assertIn("An ordinary next action by itself does not write a document", persistence)

        plan = self._folded(self._persistence_section(self._skill_text("teamwork-plan")))
        self.assertIn("direction and scope are accepted", plan)
        self.assertIn("executable plan is first settled", plan)
        self.assertIn("material replan", plan)
        self.assertNotIn("Acceptance, Parallel, and Presentation", plan)

    def test_policy_and_cursor_adapter_name_host_surfaces(self) -> None:
        policy = self._folded((ROOT / "policy/teamwork-global.md").read_text(encoding="utf-8"))
        cursor = self._folded((ROOT / "CURSOR.md").read_text(encoding="utf-8"))
        claude = self._folded((ROOT / "CLAUDE.md").read_text(encoding="utf-8"))
        self.assertIn("Host interaction surfaces do not replace", policy)
        self.assertIn("host plan UI", policy)
        self.assertIn("question UI", policy)
        self.assertIn("does not complete a Skill checkpoint", policy)
        self.assertIn("Root owns document delivery", policy)
        self.assertIn("same response cycle", policy)
        self.assertIn("does not delay the current checkpoint write", policy)
        self.assertIn("current environment cannot write", policy)
        self.assertIn("document was not delivered", policy)
        self.assertIn("unavailable, returns a no-write", policy)
        self.assertIn("Root writes the same Skill template", policy)
        self.assertNotIn("Prefer Writer", policy)
        self.assertNotIn("Root fallback", policy)
        self.assertIn("Trigger hints", policy)
        self.assertIn("Collaborate", policy)
        self.assertIn("Debug", policy)
        self.assertIn("Goal", policy)
        self.assertIn("Review", policy)
        self.assertNotIn("CreatePlan", policy)
        self.assertNotIn("AskQuestion", policy)
        self.assertIn("CreatePlan is not Writer", cursor)
        self.assertIn("AskQuestion", cursor)
        self.assertIn("subagent_type: writer", cursor)
        self.assertIn("teamwork-writer", cursor)
        self.assertIn("~/.claude/skills/", cursor)
        self.assertIn("not guaranteed", cursor)
        self.assertIn("keep both in sync", cursor)
        self.assertIn("/name", cursor)
        self.assertIn("$name", cursor)
        self.assertIn("Root owns document delivery", cursor)
        self.assertIn("does not delay the current checkpoint write", cursor)
        self.assertNotIn("Prefer Writer", cursor)
        self.assertNotIn("Root fallback", cursor)
        self.assertIn("Privacy Mode (Legacy)", cursor)
        self.assertIn("agent refresh is not a usable path", cursor)
        self.assertIn("global policy block is not injected", cursor)
        self.assertIn("self-sufficient", cursor)
        self.assertIn("User Rule paste is optional", cursor)
        self.assertIn("Batching a stage's questions through AskQuestion", cursor)
        self.assertIn("Cursor installs 6 roles", cursor)
        self.assertIn("does not install the Debug or Goal Skills", cursor)
        self.assertIn("Explorer and Debugger are intentionally omitted", cursor)
        self.assertIn("reviewer, planner, challenger, and worker use high", cursor)
        self.assertNotIn("xhigh", cursor)
        self.assertNotIn("debugger and reviewer", cursor)
        self.assertIn("AskUserQuestion", claude)
        self.assertIn("host Plan", claude)
        self.assertIn("do not persist", claude)
        self.assertIn("Task/Agent helper role", claude)
        self.assertIn("/name", claude)
        self.assertIn("$name", claude)
        self.assertIn("Root owns document delivery", claude)
        self.assertIn("does not delay the current checkpoint write", claude)
        self.assertIn("not guaranteed", claude)
        self.assertNotIn("Prefer Writer", claude)
        self.assertNotIn("Root fallback", claude)
        self.assertIn("Debugger stays", claude)
        self.assertIn("still installs Debug, Goal, and Debugger", claude)

    def test_cursor_agents_pin_grok_fast_by_role(self) -> None:
        expected = {
            "researcher": "model: kimi-k3[effort=high]",
            "planner": "model: grok-4.6[effort=high,fast=true]",
            "reviewer": "model: grok-4.6[effort=high,fast=true]",
            "challenger": "model: grok-4.6[effort=high,fast=true]",
            "worker": "model: grok-4.6[effort=high,fast=true]",
            "writer": "model: grok-4.6[effort=medium,fast=true]",
        }
        leftover = (
            "---\n"
            "name: debugger\n"
            "description: leftover Teamwork debugger\n"
            "readonly: false\n"
            "---\n\n"
            "You are the Teamwork Debugger.\n"
        )
        with tempfile.TemporaryDirectory() as raw:
            env = os.environ.copy()
            env["HOME"] = raw
            agent_root = Path(raw) / ".cursor/agents"
            agent_root.mkdir(parents=True)
            (agent_root / "debugger.md").write_text(leftover, encoding="utf-8")
            result = subprocess.run(
                [str(ROOT / "install.sh"), "--copy", "cursor-agents"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("pinned role models + effort", result.stdout)
            self.assertFalse((agent_root / "debugger.md").exists())
            for role, model_line in expected.items():
                path = Path(raw) / ".cursor/agents" / f"{role}.md"
                lines = [
                    line
                    for line in path.read_text(encoding="utf-8").splitlines()
                    if line.startswith("model:")
                ]
                self.assertEqual(lines, [model_line], path)

    def test_install_cursor_refreshes_existing_claude_skill_root(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            claude_root = home / ".claude/skills"
            claude_root.mkdir(parents=True)
            (claude_root / ".teamwork-version").write_text("0.0.0\n", encoding="utf-8")
            (claude_root / ".teamwork-profile").write_text("performance-first\n", encoding="utf-8")
            cursor_root = home / ".cursor/skills"
            cursor_root.mkdir(parents=True)
            (cursor_root / ".teamwork-version").write_text("0.0.0\n", encoding="utf-8")
            (cursor_root / ".teamwork-profile").write_text("inherit\n", encoding="utf-8")
            for name in ("teamwork-debug", "teamwork-goal"):
                leftover = cursor_root / name
                leftover.mkdir()
                (leftover / "SKILL.md").write_text(
                    f"---\nname: {name}\ndescription: leftover\n---\n\nTeamwork leftover.\n",
                    encoding="utf-8",
                )
            env = os.environ.copy()
            env["HOME"] = raw
            result = subprocess.run(
                [str(ROOT / "install.sh"), "--copy", "cursor"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            cursor_plan = home / ".cursor/skills/teamwork-plan/SKILL.md"
            claude_plan = claude_root / "teamwork-plan/SKILL.md"
            self.assertTrue(cursor_plan.is_file(), cursor_plan)
            self.assertTrue(claude_plan.is_file(), claude_plan)
            self.assertIn("docs/teamwork/plans/", claude_plan.read_text(encoding="utf-8"))
            for name in ("teamwork-debug", "teamwork-goal"):
                self.assertFalse((cursor_root / name).exists(), name)
                claude_skill = claude_root / name / "SKILL.md"
                self.assertTrue(claude_skill.is_file(), claude_skill)
            self.assertFalse((home / ".claude/agents").exists())
            self.assertFalse((home / ".claude/CLAUDE.md").exists())
            self.assertIn(
                "Both Teamwork skill roots were refreshed; when both exist, which copy wins is not guaranteed.",
                result.stdout,
            )

    def test_plugin_runtime_root_accepts_explorer_without_cursor(self) -> None:
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "plugin_runtime_root",
            ROOT / "scripts/plugin-runtime-root.py",
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        topology = json.loads((ROOT / "config/teamwork-topology.json").read_text(encoding="utf-8"))
        explorer = next(row for row in topology["agents"] if row["name"] == "explorer")
        self.assertEqual(
            set(explorer["templates"]),
            {"codex"},
        )
        debugger = next(row for row in topology["agents"] if row["name"] == "debugger")
        self.assertEqual(
            set(debugger["templates"]),
            {"codex", "claude"},
        )
        self.assertNotIn("cursor", debugger["templates"])
        for name in ("teamwork-debug", "teamwork-goal"):
            skill = next(row for row in topology["public_skills"] if row["name"] == name)
            self.assertEqual(set(skill["hosts"]), {"codex", "claude"})
            self.assertNotIn("cursor", skill["hosts"])
        module.validate_topology_layout(ROOT)

        with tempfile.TemporaryDirectory() as raw:
            isolated = Path(raw)
            (isolated / "config").mkdir()
            (isolated / "skills/demo").mkdir(parents=True)
            (isolated / "templates/codex-agents").mkdir(parents=True)
            (isolated / "templates/claude-agents").mkdir(parents=True)
            (isolated / "skills/demo/SKILL.md").write_text("# demo\n", encoding="utf-8")
            (isolated / "templates/codex-agents/teamwork-explorer.toml").write_text(
                "name = \"teamwork_explorer\"\n",
                encoding="utf-8",
            )
            (isolated / "templates/codex-agents/teamwork-debugger.toml").write_text(
                "name = \"teamwork_debugger\"\n",
                encoding="utf-8",
            )
            (isolated / "templates/claude-agents/debugger.md").write_text(
                "name: debugger\n",
                encoding="utf-8",
            )
            (isolated / "config/teamwork-topology.json").write_text(
                json.dumps(
                    {
                        "public_skills": [
                            {
                                "name": "demo",
                                "path": "skills/demo/SKILL.md",
                                "hosts": ["codex", "claude"],
                            }
                        ],
                        "agents": [
                            {
                                "name": "explorer",
                                "templates": {
                                    "codex": "templates/codex-agents/teamwork-explorer.toml",
                                },
                            },
                            {
                                "name": "debugger",
                                "templates": {
                                    "codex": "templates/codex-agents/teamwork-debugger.toml",
                                    "claude": "templates/claude-agents/debugger.md",
                                },
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            module.validate_topology_layout(isolated)

            invalid = json.loads((isolated / "config/teamwork-topology.json").read_text(encoding="utf-8"))
            invalid["public_skills"][0]["hosts"] = []
            (isolated / "config/teamwork-topology.json").write_text(
                json.dumps(invalid),
                encoding="utf-8",
            )
            with self.assertRaises(SystemExit):
                module.validate_topology_layout(isolated)

            invalid["public_skills"][0]["hosts"] = ["vim"]
            (isolated / "config/teamwork-topology.json").write_text(
                json.dumps(invalid),
                encoding="utf-8",
            )
            with self.assertRaises(SystemExit):
                module.validate_topology_layout(isolated)

        live = subprocess.run(
            [sys.executable, str(ROOT / "scripts/plugin-runtime-root.py")],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(live.returncode, 0, live.stderr)
        self.assertEqual(live.stdout.strip(), str(ROOT))

    def test_topology_skills_host_filter_omits_cursor_debug_goal(self) -> None:
        query = ROOT / "scripts/teamwork_tooling/topology.py"
        all_skills = subprocess.run(
            [sys.executable, str(query), "skills"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(all_skills.returncode, 0, all_skills.stderr)
        all_names = all_skills.stdout.split()
        self.assertEqual(len(all_names), 8)
        self.assertIn("teamwork-debug", all_names)
        self.assertIn("teamwork-goal", all_names)

        cursor = subprocess.run(
            [sys.executable, str(query), "skills", "--host", "cursor"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(cursor.returncode, 0, cursor.stderr)
        cursor_names = cursor.stdout.split()
        self.assertEqual(len(cursor_names), 6)
        self.assertNotIn("teamwork-debug", cursor_names)
        self.assertNotIn("teamwork-goal", cursor_names)

        for host in ("claude", "codex"):
            result = subprocess.run(
                [sys.executable, str(query), "skills", "--host", host],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            names = result.stdout.split()
            self.assertEqual(len(names), 8, host)
            self.assertIn("teamwork-debug", names)
            self.assertIn("teamwork-goal", names)

        cursor_roles = subprocess.run(
            [sys.executable, str(query), "agent-templates", "--host", "cursor", "--field", "name"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(cursor_roles.returncode, 0, cursor_roles.stderr)
        role_names = cursor_roles.stdout.split()
        self.assertEqual(len(role_names), 6)
        self.assertNotIn("debugger", role_names)
        self.assertNotIn("explorer", role_names)

    def test_cursor_policy_declares_omit_debug_goal_debugger(self) -> None:
        result = subprocess.run(
            [str(ROOT / "install.sh"), "cursor-policy"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        folded = self._folded(result.stdout)
        self.assertIn("does not install the Debug or Goal Skills or the Debugger role", folded)
        self.assertIn("Do not load them", folded)
        self.assertIn("use the host Debug mode", folded)
        self.assertNotIn("CreatePlan", (ROOT / "policy/teamwork-global.md").read_text(encoding="utf-8"))

    def test_policy_owns_outcome_and_persistence_contract(self) -> None:
        policy = self._folded((ROOT / "policy/teamwork-global.md").read_text(encoding="utf-8"))
        self.assertIn("The active method succeeds on its user-facing result", policy)
        self.assertIn("never certify or substitute", policy)
        self.assertIn("Before a direction is frozen", policy)
        self.assertIn("would change the goal, direction, acceptance, or irreversible spend", policy)
        self.assertIn("After the user authorizes a settled direction, advance that result", policy)
        self.assertIn("Execution eligibility", policy)
        self.assertIn("Claim eligibility", policy)
        self.assertIn("does not by itself forbid a safe, authorized attempt", policy)
        self.assertIn("do not invent vetoes", policy)
        self.assertIn("after the method's user-facing result already exists", policy)
        self.assertIn("same response cycle", policy)
        self.assertIn("Root owns document delivery", policy)
        self.assertIn("does not delay the current checkpoint write", policy)
        self.assertIn("current environment cannot write", policy)
        self.assertIn("document was not delivered", policy)
        self.assertIn("first todo after an execution request", policy)
        self.assertNotIn("silently skipping a fired checkpoint", policy.lower())
        self.assertNotIn("before closeout", policy.lower())
        self.assertNotIn("Prefer Writer", policy)
        self.assertNotIn("Root fallback", policy)

        architecture = self._folded((ROOT / "docs/architecture.md").read_text(encoding="utf-8"))
        self.assertIn("does not certify or substitute for that result", architecture)
        self.assertIn("policy/teamwork-global.md` is the sole owner", architecture)
        self.assertIn("Claude Code installs 7 roles", architecture)
        self.assertIn("Cursor installs 6 roles", architecture)

        for name in (
            "teamwork-collaborate",
            "teamwork-research",
            "teamwork-debug",
            "teamwork-plan",
            "teamwork-review",
            "teamwork-goal",
        ):
            with self.subTest(skill=name):
                skill = self._folded(self._skill_text(name))
                self.assertNotIn("Execution eligibility is permission", skill)
                self.assertNotIn("first todo after an execution request", skill)
                self.assertNotIn("silently skipping a fired checkpoint", skill.lower())

    def test_method_skill_persistence_requires_timely_write_and_identity_split(
        self,
    ) -> None:
        for name in (
            "teamwork-collaborate",
            "teamwork-research",
            "teamwork-debug",
            "teamwork-plan",
            "teamwork-review",
            "teamwork-goal",
        ):
            with self.subTest(skill=name):
                section = self._folded(self._persistence_section(self._skill_text(name)))
                self.assertIn("When a listed checkpoint fires", section)
                self.assertIn("same response cycle", section)
                self.assertIn(
                    "If separate stable identities each cross a checkpoint",
                    section,
                )
                self.assertIn("write each to its own path", section)
                self.assertNotIn("Prefer Writer", section)
                method = self._folded(self._method_section(self._skill_text(name)))
                self.assertNotIn("same response cycle", method)
                self.assertNotIn("write the document", method.lower())

    def test_init_update_persist_only_after_optional_checkpoint(self) -> None:
        for name in ("teamwork-init", "teamwork-update"):
            with self.subTest(skill=name):
                persistence = self._folded(
                    self._persistence_section(self._skill_text(name))
                )
                self.assertIn("Persistence is optional", persistence)
                self.assertIn("When that optional checkpoint fires", persistence)
                self.assertIn("same response cycle", persistence)
                self.assertIn("Root owns document delivery", persistence)
                self.assertIn("does not delay the current checkpoint write", persistence)
                method = self._folded(self._method_section(self._skill_text(name)))
                self.assertNotIn("same response cycle", method)

    def test_collaborate_session_recall_only_after_observed_write_failure(
        self,
    ) -> None:
        skill = self._folded(self._skill_text("teamwork-collaborate"))
        persistence = self._folded(
            self._persistence_section(self._skill_text("teamwork-collaborate"))
        )
        self.assertIn(
            "Session recall may be used on the next turn only after a write is "
            "observed unavailable or failed",
            skill,
        )
        self.assertIn(
            "A missing document is not a license to skip a fired checkpoint write",
            persistence,
        )
        self.assertNotIn(
            "If the document is missing, session recall may be used",
            skill,
        )

    def test_skills_and_core_policy_omit_host_mode_tool_names(self) -> None:
        forbidden = (
            "CreatePlan",
            "AskQuestion",
            "AskUserQuestion",
            "plan mode",
            ".cursor/plans",
        )
        products = ("Cursor", "Claude", "Codex")
        policy = (ROOT / "policy/teamwork-global.md").read_text(encoding="utf-8")
        for name in forbidden + products:
            self.assertNotIn(name, policy, name)
        for skill_name in (
            "teamwork-collaborate",
            "teamwork-research",
            "teamwork-debug",
            "teamwork-plan",
            "teamwork-review",
            "teamwork-goal",
            "teamwork-init",
            "teamwork-update",
        ):
            persistence = self._persistence_section(self._skill_text(skill_name))
            for name in forbidden + products:
                self.assertNotIn(name, persistence, f"{skill_name}:{name}")

    def test_collaborate_rebuilds_decision_surface_then_advances(self) -> None:
        method = self._folded(self._method_section(self._skill_text("teamwork-collaborate")))
        self.assertIn("Rebuild the full decision surface first", method)
        self.assertIn("unknowns that would change the goal, direction, or acceptance", method)
        self.assertIn("Resolve discoverable facts directly", method)
        self.assertIn("Recommend a direction when the evidence distinguishes one", method)
        self.assertIn("discussion ends at that real action", method)
        self.assertIn("do not open a new evidence gate", method)
        self.assertNotIn("main deliverable", method.lower())

    def test_plan_returns_gap_and_requires_first_real_step(self) -> None:
        plan = self._folded(self._skill_text("teamwork-plan"))
        self.assertIn("full set of goals", plan)
        self.assertIn("return that gap instead of a partial plan", plan)
        self.assertIn(
            "The first executable step must change the target artifact or remove an observed mechanical blocker",
            plan,
        )
        self.assertIn("The critical path holds only actions that produce the result", plan)
        self.assertIn("not prerequisites just because they help explain", plan)
        self.assertIn("Default to a local patch", plan)
        self.assertIn("Do not open a new plan because of added acceptance checks", plan)
        self.assertNotIn("Classify new feedback", plan)
        self.assertNotIn("Impact log", plan)
        self.assertNotIn("main-deliverable", plan)

        plan_template = (ROOT / "skills/teamwork-plan/references/plan.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("## Current execution plan", plan_template)
        self.assertNotIn("## Impact log", plan_template)

        for path in (
            ROOT / "templates/codex-agents/teamwork-planner.toml",
            ROOT / "templates/cursor-agents/planner.md",
            ROOT / "templates/claude-agents/planner.md",
        ):
            text = self._folded(path.read_text(encoding="utf-8"))
            with self.subTest(planner=path.name):
                self.assertIn("return that gap instead of a partial plan", text)
                self.assertIn("first executable step must change the target artifact", text)
                self.assertIn("default to a local patch", text.lower())

    def test_research_names_decision_and_feeds_matching_section(self) -> None:
        research = self._folded(self._skill_text("teamwork-research"))
        self.assertIn("Name the decision this investigation serves", research)
        self.assertIn("Stop when the evidence distinguishes the served direction", research)
        self.assertIn("feed the matching discussion or plan section", research)
        self.assertIn("they do not rewrite the whole case", research)
        self.assertNotIn("main deliverable", research.lower())

    def test_experiment_slots_constrain_claim_and_scale(self) -> None:
        experiment = (
            ROOT / "skills/teamwork-collaborate/references/experiment.md"
        ).read_text(encoding="utf-8")
        folded = self._folded(experiment)
        self.assertIn("The slot decides what may be claimed and whether scale-up is worth it", folded)
        self.assertIn(
            "does not decide whether the first authorized, in-budget real attempt may run",
            folded,
        )
        self.assertIn("stop the matching claim or scale-up", folded)
        self.assertIn("do not stop the whole project", folded)
        self.assertIn(
            "do not stop an authorized, in-budget first outcome-bearing attempt",
            folded,
        )
        self.assertNotIn("Unfrozen mechanism work stays out of training", experiment)
        self.assertNotIn("until agreed gates pass", experiment)
        self.assertNotIn("a gate, not a contribution", experiment)

        collaborate = self._folded(self._skill_text("teamwork-collaborate"))
        self.assertIn("Practice first forbids claiming an unobserved result", collaborate)
        self.assertIn("does not require proxy experiments", collaborate)

    def test_debug_goal_review_keep_v76_method_contracts(self) -> None:
        debug = self._folded(self._skill_text("teamwork-debug"))
        self.assertIn("Do not guess a fix", debug)
        self.assertIn("same failing path", debug)
        self.assertIn("freeze observe, instrument, and fix permission", debug)
        self.assertIn("Reproduce or directly inspect the failure", debug)
        self.assertNotIn("main deliverable", debug.lower())
        self.assertNotIn("outcome-bearing", debug)

        goal = self._folded(self._skill_text("teamwork-goal"))
        self.assertIn("success signal is the directly observable result", goal)
        self.assertIn("Invariants", goal)
        self.assertIn("Attempt Record", goal)
        self.assertNotIn("main deliverable", goal.lower())
        self.assertNotIn("outcome-bearing", goal)

        review = self._skill_text("teamwork-review")
        folded_review = self._folded(review)
        self.assertIn("missing evidence is `unknown`", review)
        self.assertIn("`ACCEPT`, `REVISE`, or `BLOCKED`", review)
        self.assertIn("protected boundary", review)
        self.assertNotIn("main deliverable", folded_review.lower())
        self.assertNotIn("outcome-bearing", folded_review)

    BASELINE_V76 = "82459cc3dec6ff8872a33be6fe2e11c6a1e5997c"

    def _git_show(self, rev: str, rel: str) -> str:
        result = subprocess.run(
            ["git", "show", f"{rev}:{rel}"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        return result.stdout

    def _replay_first_todo(self, texts: dict[str, str], candidates: tuple[str, ...], kind: str) -> str:
        policy = self._folded(texts["policy"])
        plan = self._folded(texts["plan"])
        debug = self._folded(texts["debug"])
        review = self._folded(texts["review"])
        collaborate = self._folded(texts["collaborate"])
        experiment = self._folded(texts["experiment"])

        persist = {
            "persist checkpoint",
            "wake Writer",
            "write docs/teamwork first",
        }
        evidence = {
            "bake-off / metric dry-run",
            "design document",
            "audit",
            "benchmark harness",
        }
        new_or_rewrite = {
            "Write new plan slug",
            "full rewrite of plan.md",
            "full rewrite",
        }
        forbidden: set[str] = set()
        if "Rebuild the full decision surface first" in collaborate and kind == "scope":
            forbidden |= {
                "write a plan from the last message only",
                "start bake-off / metric dry-run",
                "implement immediately",
                "design document",
            }
        if "Resolve discoverable facts directly" in collaborate and kind == "scope":
            forbidden.add("design document")
        if "after the method's user-facing result already exists" in policy and kind == "scope":
            forbidden |= persist
        if "return that gap instead of a partial plan" in plan and kind == "plan-gap":
            forbidden.add("write a partial plan assuming the gap")
        if "first todo after an execution request" in policy and kind in {
            "execution",
            "plan-edit",
        }:
            forbidden |= persist
        if "not prerequisites just because they help explain" in plan and kind == "execution":
            forbidden |= evidence
        if "does not require proxy experiments" in collaborate and kind == "execution":
            forbidden.add("bake-off / metric dry-run")
        if "do not open a new evidence gate" in collaborate and kind == "execution":
            forbidden.add("reopen execution with a new evidence gate")
        if "Unfrozen mechanism work stays out of training" in experiment and kind == "execution":
            forbidden.add("start training or mechanical prep")
        if "Default to a local patch" in plan and kind == "plan-edit":
            forbidden |= new_or_rewrite
        if "Do not open a new plan because of added acceptance checks" in plan and kind == "plan-edit":
            forbidden.add("Write new plan slug")
        if "Rearrange the whole plan only when the user changes the goal or direction" in plan and kind == "plan-edit":
            forbidden.add("reopen direction")
        if "Do not guess a fix" in debug and kind == "debug":
            forbidden.add("guess a fix")
        if "missing evidence is `unknown`" in review and kind == "review-missing-evidence":
            forbidden.add("ACCEPT")
        if "before closeout" in collaborate.lower() and kind == "execution":
            forbidden.add("start training or mechanical prep")
            forbidden.add("implement or report mechanical blocker")

        remaining = [item for item in candidates if item not in forbidden]
        if not remaining:
            return "blocked"
        return remaining[0]

    def _replay_corpus(self) -> tuple[tuple[str, str, tuple[str, ...], str], ...]:
        return (
            (
                "ml_intake",
                "scope",
                (
                    "write a plan from the last message only",
                    "start bake-off / metric dry-run",
                    "persist checkpoint",
                    "rebuild full decision surface: probe vs paper vs complete goal",
                ),
                "rebuild full decision surface: probe vs paper vs complete goal",
            ),
            (
                "ml_build",
                "execution",
                (
                    "persist checkpoint",
                    "bake-off / metric dry-run",
                    "reopen execution with a new evidence gate",
                    "start training or mechanical prep",
                ),
                "start training or mechanical prep",
            ),
            (
                "ml_add_public_metric",
                "plan-edit",
                (
                    "Write new plan slug",
                    "full rewrite of plan.md",
                    "local patch same plan",
                ),
                "local patch same plan",
            ),
            (
                "ml_scale_1_2_gpu",
                "plan-edit",
                (
                    "Write new plan slug",
                    "full rewrite",
                    "reopen direction",
                    "local patch: 1-2 GPU constraint, keep unaffected goals",
                ),
                "local patch: 1-2 GPU constraint, keep unaffected goals",
            ),
            (
                "software_intake",
                "scope",
                (
                    "write a plan from the last message only",
                    "design document",
                    "implement immediately",
                    "resolve API/scope-changing facts",
                ),
                "resolve API/scope-changing facts",
            ),
            (
                "software_build",
                "execution",
                (
                    "persist checkpoint",
                    "design document",
                    "audit",
                    "benchmark harness",
                    "implement or report mechanical blocker",
                ),
                "implement or report mechanical blocker",
            ),
            (
                "plan_direction_gap",
                "plan-gap",
                (
                    "write a partial plan assuming the gap",
                    "return the direction-changing gap",
                ),
                "return the direction-changing gap",
            ),
            (
                "debug_unknown",
                "debug",
                ("guess a fix", "locate the cause"),
                "locate the cause",
            ),
            (
                "review_missing_runtime",
                "review-missing-evidence",
                ("ACCEPT", "unknown / not ACCEPT"),
                "unknown / not ACCEPT",
            ),
        )

    def _live_texts(self) -> dict[str, str]:
        return {
            "policy": (ROOT / "policy/teamwork-global.md").read_text(encoding="utf-8"),
            "plan": self._skill_text("teamwork-plan"),
            "debug": self._skill_text("teamwork-debug"),
            "review": self._skill_text("teamwork-review"),
            "collaborate": self._skill_text("teamwork-collaborate"),
            "experiment": (
                ROOT / "skills/teamwork-collaborate/references/experiment.md"
            ).read_text(encoding="utf-8"),
        }

    def _v76_texts(self) -> dict[str, str]:
        return {
            "policy": self._git_show(self.BASELINE_V76, "policy/teamwork-global.md"),
            "plan": self._git_show(self.BASELINE_V76, "skills/teamwork-plan/SKILL.md"),
            "debug": self._git_show(self.BASELINE_V76, "skills/teamwork-debug/SKILL.md"),
            "review": self._git_show(self.BASELINE_V76, "skills/teamwork-review/SKILL.md"),
            "collaborate": self._git_show(
                self.BASELINE_V76, "skills/teamwork-collaborate/SKILL.md"
            ),
            "experiment": self._git_show(
                self.BASELINE_V76,
                "skills/teamwork-collaborate/references/experiment.md",
            ),
        }

    def test_behavioral_replay_orders_scope_then_real_action(self) -> None:
        texts = self._live_texts()
        for name, kind, candidates, expected in self._replay_corpus():
            with self.subTest(scenario=name):
                first = self._replay_first_todo(texts, candidates, kind)
                self.assertEqual(first, expected)
                self.assertNotEqual(first, "persist checkpoint")
                self.assertNotEqual(first, "Write new plan slug")
                self.assertNotEqual(first, "guess a fix")
                self.assertNotEqual(first, "ACCEPT")

    def test_ab_replay_improves_scope_and_advance_versus_v76(self) -> None:
        live = self._live_texts()
        baseline = self._v76_texts()
        scope_kinds = {"scope", "plan-gap"}
        advance_kinds = {"execution", "plan-edit"}
        live_scope_hits = 0
        base_scope_hits = 0
        live_advance_hits = 0
        base_advance_hits = 0
        rows = []
        for name, kind, candidates, expected in self._replay_corpus():
            live_first = self._replay_first_todo(live, candidates, kind)
            base_first = self._replay_first_todo(baseline, candidates, kind)
            rows.append((name, kind, base_first, live_first, expected))
            self.assertEqual(live_first, expected, name)
            if kind in scope_kinds:
                live_scope_hits += int(live_first == expected)
                base_scope_hits += int(base_first == expected)
            if kind in advance_kinds:
                live_advance_hits += int(live_first == expected)
                base_advance_hits += int(base_first == expected)
            if kind in {"debug", "review-missing-evidence"}:
                self.assertEqual(live_first, base_first)
        report = "\n".join(
            f"{name} [{kind}]: v7.6={base} -> candidate={live_first} (want {expected})"
            for name, kind, base, live_first, expected in rows
        )
        print("\nA/B replay vs v7.6.0:\n" + report)
        self.assertGreater(live_scope_hits, base_scope_hits, report)
        self.assertGreater(live_advance_hits, base_advance_hits, report)


if __name__ == "__main__":
    unittest.main()

