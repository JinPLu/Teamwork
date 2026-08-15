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

    def _persistence_section(self, skill_text: str) -> str:
        marker = "## Persistence"
        start = skill_text.find(marker)
        self.assertGreaterEqual(start, 0, "missing Persistence section")
        rest = skill_text[start + len(marker) :]
        nxt = rest.find("\n## ")
        return rest if nxt < 0 else rest[:nxt]

    def test_collaborate_description_requires_unclear_intent_not_one_detail(self) -> None:
        description = self._frontmatter_description(self._skill_text("teamwork-collaborate"))
        self.assertIn("unclear intent", description)
        self.assertIn("guided clarification", description)
        self.assertIn("do not use for clear execution or a single discoverable detail", description)

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
            ROOT / "templates/cursor-agents/debugger.md",
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

    def test_each_skill_persistence_section_retains_writer_grant_fields(self) -> None:
        grant_fields = (
            "document kind and path",
            "identity",
            "authoritative",
            "owner-certified semantic delta",
            "read-only context",
            "expected base",
        )
        topology = json.loads((ROOT / "config/teamwork-topology.json").read_text(encoding="utf-8"))
        skills = [row["name"] for row in topology["public_skills"]]
        self.assertEqual(len(skills), 8)
        for name in skills:
            with self.subTest(skill=name):
                section = self._folded(self._persistence_section(self._skill_text(name)))
                for field in grant_fields:
                    self.assertIn(field, section, field)

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
        module.validate_topology_layout(ROOT)

        with tempfile.TemporaryDirectory() as raw:
            isolated = Path(raw)
            (isolated / "config").mkdir()
            (isolated / "skills/demo").mkdir(parents=True)
            (isolated / "templates/codex-agents").mkdir(parents=True)
            (isolated / "skills/demo/SKILL.md").write_text("# demo\n", encoding="utf-8")
            (isolated / "templates/codex-agents/teamwork-explorer.toml").write_text(
                "name = \"teamwork_explorer\"\n",
                encoding="utf-8",
            )
            (isolated / "config/teamwork-topology.json").write_text(
                json.dumps(
                    {
                        "public_skills": [
                            {"name": "demo", "path": "skills/demo/SKILL.md"}
                        ],
                        "agents": [
                            {
                                "name": "explorer",
                                "templates": {
                                    "codex": "templates/codex-agents/teamwork-explorer.toml",
                                },
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            module.validate_topology_layout(isolated)

        live = subprocess.run(
            [sys.executable, str(ROOT / "scripts/plugin-runtime-root.py")],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(live.returncode, 0, live.stderr)
        self.assertEqual(live.stdout.strip(), str(ROOT))


if __name__ == "__main__":
    unittest.main()
