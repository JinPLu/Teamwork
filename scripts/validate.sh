#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENTRYPOINT="$ROOT/skills/using-teamwork/SKILL.md"
SKILLS=(
  using-teamwork
  teamwork-init
  teamwork-goal
  teamwork-research
  teamwork-plan
  teamwork-execute
  teamwork-review
  teamwork-update
)
RETIRED_SKILLS=(
  teamwork
  teamwork-design
  run-analyze-optimize
  run-analyze-design
  run-analyze-execute
  run-analyze-review
  run-analyze-research
  run-analyze-plan
  run-analyze-goal
  run-analyze-plan-review
  run-analyze-execution-review
)

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

grep_required() {
  local pattern="$1"
  local file="$2"
  local message="$3"
  grep -q "$pattern" "$file" || fail "$message"
}

grep_absent() {
  local pattern="$1"
  local message="$2"
  shift 2
  if grep -R -q "$pattern" "$@"; then
    fail "$message"
  fi
}

line_count_max() {
  local file="$1"
  local max="$2"
  local message="$3"
  local count
  count="$(wc -l < "$file" | tr -d ' ')"
  [[ "$count" -le "$max" ]] || fail "$message ($count > $max)"
}

word_count_max() {
  local file="$1"
  local max="$2"
  local message="$3"
  local count
  count="$(wc -w < "$file" | tr -d ' ')"
  [[ "$count" -le "$max" ]] || fail "$message ($count > $max)"
}

fenced_block_line_count_max() {
  local file="$1"
  local max="$2"
  local message="$3"
  awk -v max="$max" -v message="$message" '
    /^```/ {
      if (in_block && count > max) {
        printf "FAIL: %s in %s (%d > %d)\n", message, FILENAME, count, max > "/dev/stderr"
        exit 1
      }
      in_block = !in_block
      count = 0
      next
    }
    in_block { count++ }
    END {
      if (in_block && count > max) {
        printf "FAIL: %s in %s (%d > %d)\n", message, FILENAME, count, max > "/dev/stderr"
        exit 1
      }
    }
  ' "$file" || exit 1
}

git_known_or_worktree_addition() {
  local path="$1"
  git -C "$ROOT" ls-files --error-unmatch "$path" >/dev/null 2>&1 && return 0
  git -C "$ROOT" status --short -- "$path" | grep -Eq '^\?\? ' && return 0
  return 1
}

expected_skill_dirs="$(printf '%s\n' "${SKILLS[@]}" | sort)"
actual_skill_dirs="$(find "$ROOT/skills" -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | sort)"
[[ "$actual_skill_dirs" == "$expected_skill_dirs" ]] || fail "skills/ must contain exactly: ${SKILLS[*]}"

for retired in "${RETIRED_SKILLS[@]}"; do
  [[ ! -d "$ROOT/skills/$retired" ]] || fail "retired skill directory still exists: skills/$retired"
done

for removed in "commands" "hooks" "bin/raoctl.py"; do
  [[ ! -e "$ROOT/$removed" ]] || fail "removed runtime surface still exists: $removed"
done
if git -C "$ROOT" ls-files '.cursor' 2>/dev/null | grep -q .; then
  fail ".cursor/ must not be tracked; use ./install.sh project for local project skills"
fi
if git -C "$ROOT" ls-files '.codex' 2>/dev/null | grep -q .; then
  fail ".codex/ must not be tracked; use ./install.sh project for local project agents"
fi
grep_required '^\.codex/$' "$ROOT/.gitignore" ".gitignore must ignore local .codex/ install output"
grep_required '^\.cursor/$' "$ROOT/.gitignore" ".gitignore must ignore local .cursor/ install output"
grep_required '^\.claude/$' "$ROOT/.gitignore" ".gitignore must ignore local .claude/ install output"

[[ -f "$ROOT/CURSOR.md" ]] || fail "missing CURSOR.md"
[[ -f "$ROOT/CLAUDE.md" ]] || fail "missing CLAUDE.md"

[[ -f "$ROOT/VERSION" ]] || fail "missing VERSION"
git_known_or_worktree_addition "VERSION" || fail "VERSION is neither tracked nor a worktree addition"
grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+$' "$ROOT/VERSION" || fail "VERSION must be plain semver"

if git -C "$ROOT" ls-files 'docs/teamwork/plans/*' 'docs/teamwork/research/*' 'docs/teamwork/reports/*' 'docs/superpowers/*' | grep -q .; then
  fail "local workflow artifacts under docs/teamwork/{plans,research,reports}/ or docs/superpowers/ must not be tracked"
fi
grep_required '^docs/teamwork/plans/$' "$ROOT/.gitignore" ".gitignore must ignore local Teamwork plan artifacts"
grep_required '^docs/teamwork/research/$' "$ROOT/.gitignore" ".gitignore must ignore local Teamwork research artifacts"
grep_required '^docs/teamwork/reports/$' "$ROOT/.gitignore" ".gitignore must ignore local Teamwork report artifacts"

for skill in "${SKILLS[@]}"; do
  file="$ROOT/skills/$skill/SKILL.md"
  [[ -f "$file" ]] || fail "missing skills/$skill/SKILL.md"
  git_known_or_worktree_addition "skills/$skill/SKILL.md" \
    || fail "skills/$skill/SKILL.md is neither tracked nor a worktree addition"
  head -n 1 "$file" | grep -qx -- "---" || fail "$skill SKILL.md must start with YAML frontmatter"
  grep_required "^name: $skill$" "$file" "$skill missing matching skill name"
  grep -Eq '^description: Use when .+' "$file" || fail "$skill description must start with: Use when"
  ! grep -q '^disable-model-invocation:' "$file" || fail "$skill uses unsupported metadata"
  ! grep -q '^```skill' "$file" || fail "$skill SKILL.md must not be wrapped in a skill fence"

  keys="$(
    sed -n '2,/^---$/p' "$file" \
      | sed '$d' \
      | sed -n 's/^\([A-Za-z0-9_-]\+\):.*/\1/p'
  )"
  for key in $keys; do
    [[ "$key" == "name" || "$key" == "description" ]] || fail "$skill frontmatter has unsupported key: $key"
  done
done

for subskill in teamwork-init teamwork-goal teamwork-research teamwork-plan teamwork-execute teamwork-review teamwork-update; do
  grep_required "skills/$subskill/SKILL.md" "$ENTRYPOINT" "entrypoint/router does not reference skills/$subskill/SKILL.md"
done

for reference in artifact-protocol goal-iteration dispatch-policy subagent-prompt-contract subagent-packets subagent-routing workflow-contract plan-output review-checks project-init; do
  ref_file="$ROOT/skills/using-teamwork/references/$reference.md"
  [[ -f "$ref_file" ]] || fail "missing skills/using-teamwork/references/$reference.md"
  git_known_or_worktree_addition "skills/using-teamwork/references/$reference.md" \
    || fail "skills/using-teamwork/references/$reference.md is neither tracked nor a worktree addition"
done

grep_required 'references/workflow-contract.md' "$ROOT/skills/using-teamwork/SKILL.md" \
  "using-teamwork must reference shared workflow contract"
for skill in teamwork-init teamwork-goal teamwork-research teamwork-plan teamwork-execute teamwork-review; do
  grep_absent '`references/' \
    "$skill must not use sibling-local reference paths" \
    "$ROOT/skills/$skill/SKILL.md"
  grep_absent '^- `references/' \
    "$skill must not list sibling-local reference paths" \
    "$ROOT/skills/$skill/SKILL.md"
  grep_required 'skills/using-teamwork/references/workflow-contract.md' "$ROOT/skills/$skill/SKILL.md" \
    "$skill must reference shared workflow contract"
done

for skill in using-teamwork teamwork-init teamwork-goal teamwork-research teamwork-plan teamwork-execute teamwork-review; do
  grep_required 'references/workflow-contract.md' "$ROOT/skills/$skill/SKILL.md" \
    "$skill must reference shared workflow contract"
done

[[ -f "$ROOT/.codex-plugin/plugin.json" ]] || fail "missing Codex plugin manifest"
[[ -f "$ROOT/.claude-plugin/plugin.json" ]] || fail "missing Claude Code plugin manifest"
python3 -m json.tool "$ROOT/.codex-plugin/plugin.json" >/dev/null
python3 -m json.tool "$ROOT/.claude-plugin/plugin.json" >/dev/null
python3 - "$ROOT" <<'PY'
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
codex = json.loads((root / ".codex-plugin/plugin.json").read_text())
claude = json.loads((root / ".claude-plugin/plugin.json").read_text())
version = (root / "VERSION").read_text().strip()
if codex.get("skills") != "./skills/":
    raise SystemExit("FAIL: Codex manifest skills must remain ./skills/")
if "Codex" not in codex.get("description", ""):
    raise SystemExit("FAIL: Codex manifest description must mention Codex")
if codex.get("version") != version:
    raise SystemExit("FAIL: Codex manifest version must match VERSION")
if claude.get("skills") != "./skills/":
    raise SystemExit("FAIL: Claude manifest skills must remain ./skills/")
if "Claude Code" not in claude.get("description", ""):
    raise SystemExit("FAIL: Claude manifest description must mention Claude Code")
if claude.get("version") != version:
    raise SystemExit("FAIL: Claude manifest version must match VERSION")
PY

grep_required 'Codex + Cursor + Claude Code' "$ROOT/README.md" "README must state Codex + Cursor + Claude Code positioning"
grep_required 'native capabilities' "$ROOT/README.md" \
  "README must explain native platform augmentation"
grep_required 'Goal Text' "$ROOT/README.md" \
  "README must document goal text handoff"
grep_required 'teamwork-update' "$ROOT/README.md" \
  "README must document teamwork-update"
grep_required 'teamwork-init' "$ROOT/README.md" \
  "README must document teamwork-init"
grep_required 'VERSION' "$ROOT/README.md" \
  "README must document package version source"
grep_required '\[English\](README.en.md)' "$ROOT/README.md" \
  "default README must link to English README"
grep_required 'docs/teamwork/research/YYYY-MM-DD-<slug>.md' "$ROOT/README.md" \
  "README must document research artifact path"
grep_required 'docs/teamwork/plans/YYYY-MM-DD-<slug>.md' "$ROOT/README.md" \
  "README must document plan artifact path"
grep_required 'docs/teamwork/reports/YYYY-MM-DD-<slug>.md' "$ROOT/README.md" \
  "README must document report artifact path"
[[ -f "$ROOT/README.en.md" ]] || fail "missing English README"
git -C "$ROOT" ls-files --error-unmatch "README.en.md" >/dev/null 2>&1 \
  || fail "README.en.md must be tracked by git"
grep_required '\[中文\](README.md)' "$ROOT/README.en.md" \
  "English README must link to default Chinese README"
grep_required 'Codex + Cursor + Claude Code' "$ROOT/README.en.md" "English README must state Codex + Cursor + Claude Code positioning"
grep_required 'native capabilities are the execution substrate' "$ROOT/README.en.md" \
  "English README must explain native platform augmentation"
grep_required 'teamwork-update' "$ROOT/README.en.md" \
  "English README must document teamwork-update"
grep_required 'teamwork-init' "$ROOT/README.en.md" \
  "English README must document teamwork-init"
grep_required 'VERSION' "$ROOT/README.en.md" \
  "English README must document package version source"
grep_required 'Codex + Cursor + Claude Code skill package' "$ROOT/AGENTS.md" \
  "AGENTS.md must describe the Codex + Cursor + Claude Code package"
grep_required 'teamwork-update' "$ROOT/AGENTS.md" \
  "AGENTS.md must document update skill ownership"
grep_required 'teamwork-init' "$ROOT/AGENTS.md" \
  "AGENTS.md must document init skill ownership"
grep_required 'Codex native capabilities' "$ROOT/CODEX.md" \
  "CODEX.md must document native Codex capability policy"
grep_required 'Codex runtime profile' "$ROOT/CODEX.md" \
  "CODEX.md must identify itself as the Codex runtime profile"
grep_required 'Task' "$ROOT/CURSOR.md" \
  "CURSOR.md must document Cursor Task subagent policy"
grep_required 'Goal Mode' "$ROOT/CURSOR.md" \
  "CURSOR.md must document Cursor goal mode"
grep_required 'dispatch-policy.md' "$ROOT/CURSOR.md" \
  "CURSOR.md must point to dispatch policy"
grep_required 'Claude Code native capabilities' "$ROOT/CLAUDE.md" \
  "CLAUDE.md must document native Claude Code capability policy"
grep_required 'Claude Code runtime profile' "$ROOT/CLAUDE.md" \
  "CLAUDE.md must identify itself as the Claude Code runtime profile"
grep_required 'Task' "$ROOT/CLAUDE.md" \
  "CLAUDE.md must document Claude Code Task subagent policy"
grep_required 'dispatch-policy.md' "$ROOT/CLAUDE.md" \
  "CLAUDE.md must point to dispatch policy"
grep_required 'rolling report' "$ROOT/CLAUDE.md" \
  "CLAUDE.md must document Claude Code goal rolling report"
grep_required 'VERSION' "$ROOT/CLAUDE.md" \
  "CLAUDE.md must document package version source"
grep_required 'teamwork-init' "$ROOT/CLAUDE.md" \
  "CLAUDE.md must document teamwork-init"
grep_required 'VERSION' "$ROOT/CODEX.md" \
  "CODEX.md must document package version source"
grep_required 'teamwork-init' "$ROOT/CODEX.md" \
  "CODEX.md must document teamwork-init"
[[ "$(wc -l < "$ROOT/README.md")" -le 195 ]] || fail "README should stay concise"
[[ "$(wc -l < "$ROOT/README.en.md")" -le 200 ]] || fail "English README should stay concise"
line_count_max "$ROOT/skills/using-teamwork/SKILL.md" 80 "using-teamwork should stay concise"
word_count_max "$ROOT/skills/using-teamwork/SKILL.md" 450 "using-teamwork should stay concise"
line_count_max "$ROOT/skills/teamwork-init/SKILL.md" 100 "teamwork-init should stay concise"
word_count_max "$ROOT/skills/teamwork-init/SKILL.md" 600 "teamwork-init should stay concise"
line_count_max "$ROOT/skills/teamwork-plan/SKILL.md" 120 "teamwork-plan should stay concise"
word_count_max "$ROOT/skills/teamwork-plan/SKILL.md" 650 "teamwork-plan should stay concise"
line_count_max "$ROOT/skills/teamwork-goal/SKILL.md" 130 "teamwork-goal should stay concise"
word_count_max "$ROOT/skills/teamwork-goal/SKILL.md" 700 "teamwork-goal should stay concise"
line_count_max "$ROOT/skills/teamwork-review/SKILL.md" 100 "teamwork-review should stay concise"
word_count_max "$ROOT/skills/teamwork-review/SKILL.md" 550 "teamwork-review should stay concise"
line_count_max "$ROOT/skills/teamwork-research/SKILL.md" 120 "teamwork-research should stay concise"
word_count_max "$ROOT/skills/teamwork-research/SKILL.md" 650 "teamwork-research should stay concise"
line_count_max "$ROOT/skills/teamwork-execute/SKILL.md" 120 "teamwork-execute should stay concise"
word_count_max "$ROOT/skills/teamwork-execute/SKILL.md" 650 "teamwork-execute should stay concise"
line_count_max "$ROOT/skills/teamwork-update/SKILL.md" 80 "teamwork-update should stay concise"
word_count_max "$ROOT/skills/teamwork-update/SKILL.md" 400 "teamwork-update should stay concise"
line_count_max "$ROOT/skills/using-teamwork/references/dispatch-policy.md" 225 "dispatch policy reference should stay focused"
word_count_max "$ROOT/skills/using-teamwork/references/dispatch-policy.md" 1400 "dispatch policy reference should stay focused"
line_count_max "$ROOT/skills/using-teamwork/references/subagent-prompt-contract.md" 80 "subagent prompt contract should stay focused"
word_count_max "$ROOT/skills/using-teamwork/references/subagent-prompt-contract.md" 500 "subagent prompt contract should stay focused"
line_count_max "$ROOT/skills/using-teamwork/references/subagent-packets.md" 110 "subagent packet reference should stay focused"
word_count_max "$ROOT/skills/using-teamwork/references/subagent-packets.md" 350 "subagent packet reference should stay focused"
line_count_max "$ROOT/skills/using-teamwork/references/subagent-routing.md" 25 "compatibility routing index should stay small"
word_count_max "$ROOT/skills/using-teamwork/references/subagent-routing.md" 120 "compatibility routing index should stay small"
line_count_max "$ROOT/skills/using-teamwork/references/project-init.md" 95 "project init reference should stay focused"
word_count_max "$ROOT/skills/using-teamwork/references/project-init.md" 650 "project init reference should stay focused"
for skill in "${SKILLS[@]}"; do
  fenced_block_line_count_max "$ROOT/skills/$skill/SKILL.md" 20 "$skill must not embed large fenced templates"
done

grep_required 'platform-native augmentation layer' "$ENTRYPOINT" \
  "entrypoint/router must define Teamwork as platform-native augmentation"
grep_required 'Platform Native Policy Map' "$ENTRYPOINT" \
  "entrypoint/router must document platform native policy map"
grep_required 'Goal Proposal' "$ENTRYPOINT" \
  "entrypoint/router must document goal proposal routing"
grep_required 'Stage-Routed Proactive Dispatch' "$ENTRYPOINT" \
  "entrypoint/router must use stage-routed proactive dispatch authorization"
grep_required 'Evidence Interpretation Contract' "$ENTRYPOINT" \
  "entrypoint/router must define evidence interpretation contract"
grep_required 'Context & Cost Discipline' "$ENTRYPOINT" \
  "entrypoint/router must define context and cost discipline"
grep_required 'Subagent Collaboration Model' "$ENTRYPOINT" \
  "entrypoint/router must define subagent collaboration model"
grep_required 'Dispatch Economics' "$ENTRYPOINT" \
  "entrypoint/router must point to dispatch economics"
grep_required 'Plans may' "$ENTRYPOINT" \
  "entrypoint/router must treat plans as routing guidance, not sole dispatch authorization"
grep_required 'Teamwork orchestration is' "$ENTRYPOINT" \
  "entrypoint/router must make Teamwork orchestration the default for non-lightweight coding work"
grep_required 'Subagent Tool Discovery Gate' "$ENTRYPOINT" \
  "entrypoint/router must require tool discovery before serial fallback"
grep_required 'does not need to ask to "fan out subagents"' "$ENTRYPOINT" \
  "entrypoint/router must not require explicit fan-out wording from the user"
grep_required 'Workflow Pattern Selection' "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
  "workflow contract must define workflow pattern selection"
grep_required 'Platform Native Policy Map' "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
  "workflow contract must define platform native policy map"
grep_required 'Subagent authorization is Stage-Routed Proactive Dispatch' "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
  "workflow contract must define stage-routed proactive dispatch authorization"
grep_required 'does not need to request "fan out subagents"' "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
  "workflow contract must not require explicit user fan-out requests"
grep_required 'standing authorization' "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
  "workflow contract must treat Teamwork activation as standing dispatch authorization"
grep_required 'dispatch is the expected path' "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
  "workflow contract must make dispatch expected for independent non-lightweight tracks"
grep_required 'routing guidance' "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
  "workflow contract must define plan routing as guidance"
grep_required 'not the only' "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
  "workflow contract must not make plans the only authorization model"
grep_required 'execution stage must re-evaluate' "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
  "workflow contract must require execution-stage split reevaluation"
grep_required 'starting any coding-agent task' "$ROOT/skills/using-teamwork/SKILL.md" \
  "using-teamwork description must be broad enough for automatic discovery"
grep_required 'discovery reads frontmatter before' "$ROOT/skills/using-teamwork/SKILL.md" \
  "using-teamwork must explain broad discovery before route filtering"
grep_required 'platform goal handoff unless an active goal surface exists' "$ROOT/skills/using-teamwork/SKILL.md" \
  "using-teamwork must route goal work through platform goal handoff"
grep_required '"CURSOR"' "$ROOT/skills/using-teamwork/SKILL.md" \
  "using-teamwork must include CURSOR init trigger"
grep_required 'CURSOR.md' "$ROOT/skills/teamwork-init/SKILL.md" \
  "teamwork-init must inspect CURSOR.md"
grep_required 'AGENTS/CODEX/CURSOR/CLAUDE' "$ROOT/skills/teamwork-init/SKILL.md" \
  "teamwork-init description must mention AGENTS/CODEX/CURSOR/CLAUDE"
for agent in explore worker code-reviewer; do
  [[ -f "$ROOT/templates/claude-agents/$agent.md" ]] \
    || fail "missing templates/claude-agents/$agent.md"
  grep_required "^name: $agent$" "$ROOT/templates/claude-agents/$agent.md" \
    "Claude agent template must declare name: $agent"
done
grep_required '^model: sonnet$' "$ROOT/templates/claude-agents/explore.md" \
  "Claude explore agent must use balanced model tier"
grep_required '^model: sonnet$' "$ROOT/templates/claude-agents/worker.md" \
  "Claude worker agent must use coding/balanced model tier"
grep_required '^model: opus$' "$ROOT/templates/claude-agents/code-reviewer.md" \
  "Claude reviewer agent must use frontier model tier"
for agent in teamwork-explorer teamwork-worker teamwork-designer teamwork-judge teamwork-reviewer; do
  [[ -f "$ROOT/templates/codex-agents/$agent.toml" ]] \
    || fail "missing templates/codex-agents/$agent.toml"
  grep_required '^description = ' "$ROOT/templates/codex-agents/$agent.toml" \
    "Codex agent template must declare description: $agent"
  grep_required '^developer_instructions = """' "$ROOT/templates/codex-agents/$agent.toml" \
    "Codex agent template must declare developer_instructions: $agent"
done
grep_required '^name = "teamwork_explorer"$' "$ROOT/templates/codex-agents/teamwork-explorer.toml" \
  "Codex explorer agent must declare exact name"
grep_required '^name = "teamwork_worker"$' "$ROOT/templates/codex-agents/teamwork-worker.toml" \
  "Codex worker agent must declare exact name"
grep_required '^name = "teamwork_designer"$' "$ROOT/templates/codex-agents/teamwork-designer.toml" \
  "Codex designer agent must declare exact name"
grep_required '^name = "teamwork_judge"$' "$ROOT/templates/codex-agents/teamwork-judge.toml" \
  "Codex judge agent must declare exact name"
grep_required '^name = "teamwork_reviewer"$' "$ROOT/templates/codex-agents/teamwork-reviewer.toml" \
  "Codex reviewer agent must declare exact name"
grep_required '^model = "gpt-5.4"$' "$ROOT/templates/codex-agents/teamwork-explorer.toml" \
  "Codex explorer agent must use balanced model tier"
grep_required '^model = "gpt-5.3-codex"$' "$ROOT/templates/codex-agents/teamwork-worker.toml" \
  "Codex worker agent must use coding model tier"
grep_required '^model = "gpt-5.4"$' "$ROOT/templates/codex-agents/teamwork-designer.toml" \
  "Codex designer agent must use balanced model tier"
grep_required '^model = "gpt-5.5"$' "$ROOT/templates/codex-agents/teamwork-judge.toml" \
  "Codex judge agent must use frontier model tier"
grep_required '^model = "gpt-5.5"$' "$ROOT/templates/codex-agents/teamwork-reviewer.toml" \
  "Codex reviewer agent must use frontier model tier"
grep -q 'all)' "$ROOT/install.sh" || fail "install.sh must support all target"
grep -q 'project)' "$ROOT/install.sh" || fail "install.sh must support project target"
grep -q 'codex-agents)' "$ROOT/install.sh" || fail "install.sh must support codex-agents target"
grep -q 'claude-agents)' "$ROOT/install.sh" || fail "install.sh must support claude-agents target"
grep_required 'platform native boundaries' "$ROOT/skills/teamwork-init/SKILL.md" \
  "teamwork-init must reference platform native boundaries"
grep_required 'Visible progress tools' "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
  "workflow contract must define platform-neutral progress anchors"
grep_required 'Platform Goal Surface:' "$ROOT/skills/using-teamwork/references/goal-iteration.md" \
  "goal iteration reference must define platform goal surface output"
grep_required 'Goal Text:' "$ROOT/skills/using-teamwork/references/goal-iteration.md" \
  "goal iteration reference must define Goal Text in proposal"
grep_required 'before platform goal handoff' "$ROOT/skills/using-teamwork/references/goal-iteration.md" \
  "goal iteration reference must require platform goal handoff"
grep_required 'Research + Plan Adequacy Gate' "$ROOT/skills/teamwork-goal/SKILL.md" \
  "goal skill must define failure iteration gate"

grep_required 'Goal Proposal Before Platform Goal Handoff' "$ROOT/skills/teamwork-goal/SKILL.md" \
  "goal skill must require goal proposal before platform goal handoff"
grep_required 'Platform goal surface is the source of truth' "$ROOT/skills/teamwork-goal/SKILL.md" \
  "goal skill must define platform goal surface"
grep_required 'Goal Text goes into the platform goal surface' "$ROOT/skills/teamwork-goal/SKILL.md" \
  "goal skill must hand approved goal text to the platform goal surface"
grep_required 'create_goal' "$ROOT/skills/teamwork-goal/SKILL.md" \
  "goal skill must preserve Codex create_goal handoff"
grep_required 'rolling report' "$ROOT/skills/teamwork-goal/SKILL.md" \
  "goal skill must preserve Cursor rolling-report handoff"

grep_required 'Research Artifact Requirement' "$ROOT/skills/teamwork-research/SKILL.md" \
  "research skill must require reusable research artifacts"
grep_required 'Search existing research artifacts' "$ROOT/skills/teamwork-research/SKILL.md" \
  "research skill must reuse existing research artifacts"
grep_required 'Research Refresh Triggers' "$ROOT/skills/teamwork-research/SKILL.md" \
  "research skill must define refresh triggers"
grep_required 'Search Keys' "$ROOT/skills/teamwork-research/SKILL.md" \
  "research artifact template must include Search Keys"
grep_required 'Abstract' "$ROOT/skills/teamwork-research/SKILL.md" \
  "research artifact template must include Abstract"
grep_required 'Use the lightest planning form that preserves correctness' "$ROOT/skills/teamwork-plan/SKILL.md" \
  "plan skill must support lightweight and durable planning tiers"
grep_required 'implement, fix, add, change' "$ROOT/skills/teamwork-plan/SKILL.md" \
  "plan skill description must cover natural implementation verbs"
grep_required 'non-trivial implementation when no accepted plan' "$ROOT/skills/teamwork-plan/SKILL.md" \
  "plan skill must auto-route non-trivial implementation before edits"
grep_required 'Goal-mode durable plans' "$ROOT/skills/teamwork-plan/SKILL.md" \
  "plan skill must define Codex goal durable plans"
grep_required 'Requirements Mapping' "$ROOT/skills/teamwork-plan/SKILL.md" \
  "plan skill must require requirements mapping"
grep_required 'Search Keys' "$ROOT/skills/teamwork-plan/SKILL.md" \
  "plan skill must reference artifact header details"
grep_required 'Parallelization Gate' "$ROOT/skills/teamwork-plan/SKILL.md" \
  "plan skill must define the parallelization gate"
grep_required 'split before implementation steps' "$ROOT/skills/teamwork-plan/SKILL.md" \
  "plan skill must split before implementation steps"
grep_required '`Dispatch Guidance: none` requires a continuity rationale' "$ROOT/skills/teamwork-plan/SKILL.md" \
  "plan skill must require rationale for serial continuity"
grep_required 'Abstract' "$ROOT/skills/using-teamwork/references/plan-output.md" \
  "plan output reference must include Abstract"
grep_required 'Durable Plan Sections' "$ROOT/skills/using-teamwork/references/plan-output.md" \
  "plan output reference must include durable plan sections"
grep_required 'Platform native dispatch fields are derived at dispatch time from the' "$ROOT/skills/teamwork-plan/SKILL.md" \
  "plan skill must derive native dispatch fields at dispatch time"
grep_required 'codex review' "$ROOT/skills/teamwork-review/SKILL.md" \
  "review skill must mention codex review as evidence"
grep_required 'Routing conformance' "$ROOT/skills/teamwork-review/SKILL.md" \
  "review skill must check routing conformance"
grep_required 'missing Parallelization Gate' "$ROOT/skills/teamwork-review/SKILL.md" \
  "review skill must reject plans without the parallelization gate"
grep_required 'Execution Review' "$ROOT/skills/using-teamwork/references/review-checks.md" \
  "review checks reference must include execution review"
grep_required 'sandbox' "$ROOT/skills/teamwork-execute/SKILL.md" \
  "execute skill must document sandbox approvals"
grep_required 'accepted, approved, resumed' "$ROOT/skills/teamwork-execute/SKILL.md" \
  "execute skill must auto-route accepted or resumed plans"
grep_required 'go ahead, proceed, do it' "$ROOT/skills/teamwork-execute/SKILL.md" \
  "execute skill description must cover natural continuation verbs"
grep_required 'parallel Worker' "$ROOT/skills/teamwork-execute/SKILL.md" \
  "execute skill must prefer parallel Worker subagents when useful"
grep_required 'Automatic Stage Selection' "$ROOT/skills/using-teamwork/SKILL.md" \
  "using-teamwork must define automatic natural-language stage selection"
grep_required 'Do not wait for the user to name a Teamwork skill' "$ROOT/skills/using-teamwork/SKILL.md" \
  "using-teamwork must not require manual skill invocation"
grep_required 'teamwork-update' "$ROOT/skills/using-teamwork/SKILL.md" \
  "using-teamwork must route package update work"
grep_required 'teamwork-init' "$ROOT/skills/using-teamwork/SKILL.md" \
  "using-teamwork must route project initialization work"
grep_required 'Project Rule Layering' "$ROOT/skills/using-teamwork/references/project-init.md" \
  "project init reference must define project rule layering"
grep_required 'CodeGraph' "$ROOT/skills/using-teamwork/references/project-init.md" \
  "project init reference must define CodeGraph policy"
grep_required 'docs/teamwork' "$ROOT/skills/using-teamwork/references/project-init.md" \
  "project init reference must define Teamwork artifact placement"
grep_required 'context-cache' "$ROOT/skills/using-teamwork/references/project-init.md" \
  "project init reference must define context-cache policy"
grep_required 'current task progress' "$ROOT/skills/teamwork-init/SKILL.md" \
  "teamwork-init must forbid current task progress in instructions"
grep_required 'project-init.md' "$ROOT/skills/teamwork-init/SKILL.md" \
  "teamwork-init must link project init reference"
grep_required 'VERSION is the package version source of truth' "$ROOT/skills/teamwork-update/SKILL.md" \
  "update skill must define VERSION as source of truth"
grep_required '.codex-plugin/plugin.json' "$ROOT/skills/teamwork-update/SKILL.md" \
  "update skill must synchronize plugin manifest"
grep_required 'semantic versioning' "$ROOT/skills/teamwork-update/SKILL.md" \
  "update skill must define semver policy"
grep_required 'Skill frontmatter must stay limited to `name` and `description`' "$ROOT/skills/teamwork-update/SKILL.md" \
  "update skill must preserve skill frontmatter contract"

for term in observed inferred claimed; do
  grep_required "$term" "$ENTRYPOINT" "entrypoint/router must mention $term evidence"
  grep_required "$term" "$ROOT/skills/teamwork-research/SKILL.md" "research skill must mention $term evidence"
  grep_required "$term" "$ROOT/skills/teamwork-plan/SKILL.md" "plan skill must mention $term evidence"
  grep_required "$term" "$ROOT/skills/teamwork-review/SKILL.md" "review skill must mention $term evidence"
done

grep_required 'Explorer -> `agent_type:"teamwork_explorer"`' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy reference must map Explorer to Codex custom agent"
grep_required '`agent_type:"teamwork_worker"`' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy reference must map Worker to Codex custom agent"
grep_required '`agent_type:"teamwork_designer"`' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy reference must map Designer to Codex custom agent"
grep_required '`agent_type:"teamwork_judge"`' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy reference must map Judge to Codex custom agent"
grep_required '`agent_type:"teamwork_reviewer"`' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy reference must map Reviewer to Codex custom agent"
grep_required 'Fallback when custom agents are unavailable' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy reference must define Codex built-in fallback mapping"
grep_required '`fast` -> `reasoning_effort:"low"`' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy reference must map fast tier"
grep_required '`standard` -> `reasoning_effort:"medium"`' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy reference must map standard tier"
grep_required '`high reasoning` -> `reasoning_effort:"high"`' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy reference must map high reasoning tier"
grep_required 'Do not combine' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy reference must reject invalid full-history routing"
grep_required 'Codex role dispatch, set an explicit Role Profile model' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "Codex role dispatch must pin role-profile models by default"
grep_required 'Role Profiles' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy reference must define role profiles"
grep_required 'model class `balanced` by default' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "Explorer profile must avoid weak default models"
grep_required 'reasoning `high`' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "Judge/Reviewer profiles must require high reasoning class"
grep_required 'Codex Model Mapping' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy reference must define Codex model mapping"
grep_required 'Codex Native Field Presets' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy reference must define explicit Codex native field presets"
grep_required '`cheap-fast` -> `gpt-5.4-mini`' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "model mapping must define cheap-fast model"
grep_required 'opt-in only for trivial read-only' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "cheap-fast model must be opt-in, not a default"
grep_required '`balanced` -> `gpt-5.4`' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "model mapping must define balanced model"
grep_required '`coding` -> `gpt-5.3-codex`' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "model mapping must define coding model"
grep_required '`frontier` -> `gpt-5.5`' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "model mapping must define frontier model"
grep_required 'Explorer default: `agent_type:"explorer"`, `model:"gpt-5.4"`' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "Codex Explorer preset must pin balanced model"
grep_required 'Worker default: `agent_type:"worker"`, `model:"gpt-5.3-codex"`' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "Codex Worker preset must pin coding model"
grep_required 'Judge default: `agent_type:"default"`, `model:"gpt-5.5"`' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "Codex Judge preset must pin frontier model"
grep_required 'Codex Native Field Presets' "$ROOT/skills/using-teamwork/references/subagent-prompt-contract.md" \
  "subagent prompt contract must require Codex native field presets"
grep_required 'Platform Dispatch Fields' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy reference must define platform dispatch fields"
grep_required 'Cursor Mapping' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy reference must define Cursor mapping"
grep_required 'Explorer -> `subagent_type:"explore"`' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "Cursor mapping must map Explorer to explore"
grep_required 'Reviewer -> `subagent_type:"code-reviewer"`' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "Cursor mapping must map Reviewer to code-reviewer"
grep_required 'Cursor Model Mapping' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy reference must define Cursor model mapping"
grep_required '`cheap-fast` -> `composer-2.5-fast`' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "Cursor model mapping must define cheap-fast model"
grep_required '`balanced` -> `gpt-5.5-medium` when listed' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "Cursor model mapping must define balanced model"
grep_required '`coding` -> `gpt-5.5-medium` when listed' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "Cursor model mapping must define coding model"
grep_required '`frontier` -> `claude-opus-4-7-thinking-high`' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "Cursor model mapping must define frontier model"
grep_required 'Cursor Task Parameters' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy reference must define Cursor Task parameters"
grep_required 'Claude Code Mapping' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy reference must define Claude Code mapping"
grep_required 'Claude Code Task Parameters' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy reference must define Claude Code Task parameters"
grep_required 'Claude Code Model Mapping' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy reference must define Claude Code model mapping"
grep_required '`cheap-fast` -> `claude-haiku`' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "Claude Code model mapping must define cheap-fast model"
grep_required '`frontier` -> `claude-opus`' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "Claude Code model mapping must define frontier model"
grep_required 'readonly: true' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "Cursor Task parameters must define readonly default"
grep_required 'run_in_background: true' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "Cursor Task parameters must define background dispatch"
grep_required 'best-of-n-runner' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "Cursor Task parameters must define best-of-n-runner"
grep_required 'resume: "self"' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "Cursor Task parameters must define self resume"
grep_required 'code-reviewer' "$ROOT/skills/teamwork-review/SKILL.md" \
  "review skill must mention Cursor code-reviewer evidence"
grep_required 'platform native fields per dispatch-policy.md' "$ROOT/skills/using-teamwork/references/subagent-prompt-contract.md" \
  "subagent prompt contract must use platform-neutral role templates"
grep_required 'resume:"self"' "$ROOT/skills/using-teamwork/references/subagent-prompt-contract.md" \
  "subagent prompt contract must define Cursor full-history fork"
grep_required 'Do not use `cheap-fast` for normal Pro/20x Codex workflows' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy must forbid cheap-fast for Judge and Reviewer"
grep_required 'routing guidance, not the only' "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
  "workflow contract must treat plan routing as guidance"
grep_required 'split before implementation steps' "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
  "workflow contract must require split before implementation steps"
grep_required 'Explorer/Reviewer: default max 3' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy reference must cap Explorer/Reviewer"
grep_required 'Worker: no fixed numeric cap' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy reference must not hard-cap Workers"
grep_required 'Before dispatching more than 3 Workers' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy reference must require >3 Worker rationale"
grep_required 'ownership map' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy reference must require Worker ownership map"
grep_required 'batch or worktree isolation' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy reference must define Worker batching or worktree isolation"
grep_required 'local execution is cheaper or safer' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy reference must preserve local execution escape hatch"
grep_required 'Evaluate the split before implementation steps' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy reference must place split before implementation steps"
grep_required 'Stage-Routed Proactive Dispatch' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy reference must define stage-routed proactive dispatch"
grep_required 'parallel subagents are the default execution substrate' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy must default independent non-lightweight work to parallel subagents"
grep_required 'standing authorization' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy must define Teamwork activation as standing dispatch authorization"
grep_required 'Do not wait for the user to say' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy must not require explicit user fan-out requests"
grep_required 'Do not wait' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy reference must not wait for pre-authorization"
grep_required 'explicitly name every track' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy reference must not require proposal or plan pre-authorization for every track"
grep_required 'Context Strategies' "$ROOT/skills/using-teamwork/references/subagent-prompt-contract.md" \
  "subagent prompt contract must define context strategies"
grep_required 'condensed-evidence-only' "$ROOT/skills/using-teamwork/references/subagent-prompt-contract.md" \
  "subagent prompt contract must define condensed evidence context strategy"
grep_required 'fresh-context-review' "$ROOT/skills/using-teamwork/references/subagent-prompt-contract.md" \
  "subagent prompt contract must define fresh context review strategy"
grep_required 'owned-files-only' "$ROOT/skills/using-teamwork/references/subagent-prompt-contract.md" \
  "subagent prompt contract must define owned files context strategy"
grep_required 'artifact-backed' "$ROOT/skills/using-teamwork/references/subagent-prompt-contract.md" \
  "subagent prompt contract must define artifact backed context strategy"
grep_required 'explicit-non-inheriting-dispatch' "$ROOT/skills/using-teamwork/references/subagent-prompt-contract.md" \
  "subagent prompt contract must define explicit non-inheriting dispatch strategy"
grep_required 'Subagent Prompt Contract' "$ROOT/skills/using-teamwork/references/subagent-prompt-contract.md" \
  "subagent prompt contract must define subagent prompt contract"
grep_required 'Conceptual Role: Explorer, Designer, Judge, Worker, or Reviewer' "$ROOT/skills/using-teamwork/references/subagent-prompt-contract.md" \
  "subagent prompt contract must require conceptual role"
grep_required 'Native Fields: platform dispatch fields from `dispatch-policy.md`' "$ROOT/skills/using-teamwork/references/subagent-prompt-contract.md" \
  "subagent prompt contract must require native fields"
grep_required 'on Cursor `subagent_type`, `model` or `model: inherited`' "$ROOT/skills/using-teamwork/references/subagent-prompt-contract.md" \
  "subagent prompt contract must document Cursor native fields"
grep_required 'Never imply a stronger model' "$ROOT/skills/using-teamwork/references/subagent-prompt-contract.md" \
  "subagent prompt contract must prevent misleading model claims"
grep_required 'Context Strategy: one value from `Context Strategies`' "$ROOT/skills/using-teamwork/references/subagent-prompt-contract.md" \
  "subagent prompt contract must require context strategy"
grep_required 'Required Output Schema: matching packet from `subagent-packets.md`' "$ROOT/skills/using-teamwork/references/subagent-prompt-contract.md" \
  "subagent prompt contract must require output schema"
grep_required 'Role Templates' "$ROOT/skills/using-teamwork/references/subagent-prompt-contract.md" \
  "subagent prompt contract must define role prompt templates"
grep_required 'Explorer:' "$ROOT/skills/using-teamwork/references/subagent-prompt-contract.md" \
  "subagent prompt contract must include Explorer prompt template"
grep_required 'Designer:' "$ROOT/skills/using-teamwork/references/subagent-prompt-contract.md" \
  "subagent prompt contract must include Designer prompt template"
grep_required 'Judge:' "$ROOT/skills/using-teamwork/references/subagent-prompt-contract.md" \
  "subagent prompt contract must include Judge prompt template"
grep_required 'Worker:' "$ROOT/skills/using-teamwork/references/subagent-prompt-contract.md" \
  "subagent prompt contract must include Worker prompt template"
grep_required 'Reviewer:' "$ROOT/skills/using-teamwork/references/subagent-prompt-contract.md" \
  "subagent prompt contract must include Reviewer prompt template"
grep_required 'Result Packets' "$ROOT/skills/using-teamwork/references/subagent-packets.md" \
  "subagent packets reference must define packet shapes"
grep_required 'Explorer Result Packet' "$ROOT/skills/using-teamwork/references/subagent-packets.md" \
  "subagent packets reference must define Explorer result packet"
grep_required 'Native Fields:' "$ROOT/skills/using-teamwork/references/subagent-packets.md" \
  "subagent packets must record native fields"
grep_required 'Designer Decision Packet' "$ROOT/skills/using-teamwork/references/subagent-packets.md" \
  "subagent packets reference must define Designer decision packet"
grep_required 'Judge Plan Review Packet' "$ROOT/skills/using-teamwork/references/subagent-packets.md" \
  "subagent packets reference must define Judge plan review packet"
grep_required 'Worker Completion Packet' "$ROOT/skills/using-teamwork/references/subagent-packets.md" \
  "subagent packets reference must define Worker completion packet"
grep_required 'Reviewer Verdict Packet' "$ROOT/skills/using-teamwork/references/subagent-packets.md" \
  "subagent packets reference must define Reviewer verdict packet"
grep_required 'Actual Dispatch Log' "$ROOT/skills/using-teamwork/references/subagent-packets.md" \
  "subagent packets reference must define actual dispatch log"
grep_required 'Prompt Packet:' "$ROOT/skills/using-teamwork/references/subagent-packets.md" \
  "actual dispatch log must record prompt packet"
grep_required 'Returned Packet:' "$ROOT/skills/using-teamwork/references/subagent-packets.md" \
  "actual dispatch log must record returned packet"
grep_required 'invalid platform dispatch fields' "$ROOT/skills/using-teamwork/references/review-checks.md" \
  "review checks must validate platform dispatch fields"
grep_required 'Codex/Cursor/Claude Code mapping' "$ROOT/skills/using-teamwork/references/subagent-routing.md" \
  "compatibility routing index must mention Codex/Cursor/Claude Code mapping"
grep_required 'dispatch-policy.md' "$ROOT/skills/using-teamwork/references/subagent-routing.md" \
  "compatibility routing index must point to dispatch policy"
grep_required 'subagent-prompt-contract.md' "$ROOT/skills/using-teamwork/references/subagent-routing.md" \
  "compatibility routing index must point to prompt contract"
grep_required 'subagent-packets.md' "$ROOT/skills/using-teamwork/references/subagent-routing.md" \
  "compatibility routing index must point to packet schemas"
grep_required 'Default to parallel Explorer subagents' "$ROOT/skills/teamwork-research/SKILL.md" \
  "research skill must default-dispatch independent Explorer tracks"
grep_required 'does not need to request subagents' "$ROOT/skills/teamwork-research/SKILL.md" \
  "research skill must not require explicit user subagent requests"
grep_required 'lightweight `Dispatch Guidance:`' "$ROOT/skills/teamwork-plan/SKILL.md" \
  "plan skill must support lightweight dispatch guidance"
grep_required 'Do not wait for the user to request subagents' "$ROOT/skills/teamwork-plan/SKILL.md" \
  "plan skill must not require explicit user subagent requests"
grep_required 'dispatch parallel Worker subagents by default' "$ROOT/skills/teamwork-execute/SKILL.md" \
  "execute skill must default-dispatch independent Worker tracks"
grep_required 'even if the user did not request subagents' "$ROOT/skills/teamwork-execute/SKILL.md" \
  "execute skill must not require explicit user subagent requests"
grep_required 'Before dispatching more than 3 Workers' "$ROOT/skills/teamwork-execute/SKILL.md" \
  "execute skill must require >3 Worker integration plan"
grep_required 'Default to fresh-context Reviewer subagents' "$ROOT/skills/teamwork-review/SKILL.md" \
  "review skill must default to fresh-context reviewer subagents for non-trivial execution"
grep_required 'without waiting for the user to request subagents' "$ROOT/skills/teamwork-review/SKILL.md" \
  "review skill must not require explicit user subagent requests"
grep_required 'Dispatch Guidance:' "$ROOT/skills/using-teamwork/references/plan-output.md" \
  "lightweight plan template must include dispatch guidance"
grep_required 'Explorer/Designer/Judge/Worker/Reviewer' "$ROOT/skills/using-teamwork/references/plan-output.md" \
  "dispatch guidance must support all Teamwork subagent roles"
grep_required 'Subagent Prompt Packets' "$ROOT/skills/using-teamwork/references/plan-output.md" \
  "plan output reference must include subagent prompt packets"
grep_required 'Actual Dispatch Log' "$ROOT/skills/using-teamwork/references/plan-output.md" \
  "plan output reference must include actual dispatch log"
grep_required '`Dispatch Guidance: none` requires rationale' "$ROOT/skills/using-teamwork/references/plan-output.md" \
  "plan output reference must require rationale for serial continuity"
grep_required 'the plan is not the only authorization source' "$ROOT/skills/using-teamwork/references/plan-output.md" \
  "plan output reference must not make plans the only dispatch authorization"
grep_absent 'Proposal/Plan Routed' \
  "retired proposal/plan-routed authorization must not appear in skills or docs" \
  "$ROOT/skills" "$ROOT/README.md" "$ROOT/README.en.md" "$ROOT/CODEX.md"
grep_required 'Parallelization Gate appears before steps' "$ROOT/skills/using-teamwork/references/review-checks.md" \
  "review checks must enforce routing before steps"
grep_required 'serializes' "$ROOT/skills/using-teamwork/references/review-checks.md" \
  "review checks must reject serializing independent tracks without rationale"
grep_required 'Research + Plan Adequacy Gate' "$ROOT/skills/using-teamwork/references/goal-iteration.md" \
  "goal iteration reference must define failure gate"
grep_required 'Research Reuse' "$ROOT/skills/using-teamwork/references/goal-iteration.md" \
  "goal iteration reference must include research reuse in rolling report"
grep_required 'Search Keys' "$ROOT/skills/using-teamwork/references/goal-iteration.md" \
  "report template must include Search Keys"
grep_required 'Abstract' "$ROOT/skills/using-teamwork/references/goal-iteration.md" \
  "report template must include Abstract"
grep_required 'Retrieval Header' "$ROOT/skills/using-teamwork/references/artifact-protocol.md" \
  "artifact protocol must define Retrieval Header"
grep_required 'docs/teamwork/{research,plans,reports}/' "$ROOT/skills/using-teamwork/references/artifact-protocol.md" \
  "artifact retrieval must cover research, plans, and reports"
grep_required 'Search Keys' "$ROOT/skills/using-teamwork/references/artifact-protocol.md" \
  "artifact protocol must define Search Keys"
grep_required 'Abstract' "$ROOT/skills/using-teamwork/references/artifact-protocol.md" \
  "artifact protocol must define Abstract"

if git -C "$ROOT" grep -n -E 'raoctl|RAO|Stop hook|/rao:|/teamwork:' \
  -- ':!scripts/validate.sh' >/tmp/teamwork-retired-grep.$$; then
  cat /tmp/teamwork-retired-grep.$$ >&2
  rm -f /tmp/teamwork-retired-grep.$$
  fail "retired multi-runtime references remain outside validation"
fi
rm -f /tmp/teamwork-retired-grep.$$

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
retired_teamwork_dir="$tmp/home/.codex/skills/teamwork"
mkdir -p "$retired_teamwork_dir/references"
printf '%s\n' '---' 'name: teamwork' 'description: Use when selecting a Teamwork stage.' '---' > "$retired_teamwork_dir/SKILL.md"
for reference in artifact-protocol goal-iteration dispatch-policy subagent-prompt-contract subagent-packets subagent-routing workflow-contract plan-output review-checks project-init; do
  printf '%s\n' "retired $reference" > "$retired_teamwork_dir/references/$reference.md"
done
HOME="$tmp/home" "$ROOT/install.sh" >/dev/null
[[ ! -e "$retired_teamwork_dir" ]] || fail "Codex install must remove old copied teamwork skill"
for skill in "${SKILLS[@]}"; do
  [[ -f "$tmp/home/.codex/skills/$skill/SKILL.md" ]] || fail "Codex install missing $skill"
  [[ ! -L "$tmp/home/.codex/skills/$skill/SKILL.md" ]] || fail "default install must copy $skill"
  grep_required "^name: $skill$" "$tmp/home/.codex/skills/$skill/SKILL.md" \
    "installed skill has wrong name: $skill"
done
[[ -f "$tmp/home/.codex/skills/using-teamwork/references/workflow-contract.md" ]] \
  || fail "Codex install must copy using-teamwork references"

HOME="$tmp/home-codex-agents" "$ROOT/install.sh" codex-agents >/dev/null
for agent in teamwork-explorer teamwork-worker teamwork-designer teamwork-judge teamwork-reviewer; do
  [[ -f "$tmp/home-codex-agents/.codex/agents/$agent.toml" ]] \
    || fail "Codex agent install missing $agent"
  [[ ! -L "$tmp/home-codex-agents/.codex/agents/$agent.toml" ]] \
    || fail "default Codex agent install must copy $agent"
done

HOME="$tmp/home-codex-agents-link" "$ROOT/install.sh" --link codex-agents >/dev/null
for agent in teamwork-explorer teamwork-worker teamwork-designer teamwork-judge teamwork-reviewer; do
  [[ -L "$tmp/home-codex-agents-link/.codex/agents/$agent.toml" ]] \
    || fail "Codex agent link install must symlink $agent"
done

unknown_teamwork_dir="$tmp/home-unknown/.codex/skills/teamwork"
mkdir -p "$unknown_teamwork_dir/references"
printf '%s\n' '---' 'name: teamwork' 'description: Use when selecting a Teamwork stage.' '---' > "$unknown_teamwork_dir/SKILL.md"
printf '%s\n' "keep me" > "$unknown_teamwork_dir/notes.md"
HOME="$tmp/home-unknown" "$ROOT/install.sh" >/dev/null
[[ -f "$unknown_teamwork_dir/notes.md" ]] \
  || fail "Codex install must preserve unknown files in retired teamwork directory"

HOME="$tmp/home-link" "$ROOT/install.sh" --link codex >/dev/null
for skill in "${SKILLS[@]}"; do
  [[ -L "$tmp/home-link/.codex/skills/$skill" ]] || fail "link install must symlink $skill directory"
done

HOME="$tmp/home-cursor" "$ROOT/install.sh" cursor >/dev/null
for skill in "${SKILLS[@]}"; do
  [[ -f "$tmp/home-cursor/.cursor/skills/$skill/SKILL.md" ]] || fail "Cursor install missing $skill"
  [[ ! -L "$tmp/home-cursor/.cursor/skills/$skill/SKILL.md" ]] || fail "default Cursor install must copy $skill"
done

HOME="$tmp/home-claude" "$ROOT/install.sh" claude >/dev/null
for skill in "${SKILLS[@]}"; do
  [[ -f "$tmp/home-claude/.claude/skills/$skill/SKILL.md" ]] || fail "Claude Code install missing $skill"
  [[ ! -L "$tmp/home-claude/.claude/skills/$skill/SKILL.md" ]] || fail "default Claude Code install must copy $skill"
done
[[ -f "$tmp/home-claude/.claude/skills/using-teamwork/references/workflow-contract.md" ]] \
  || fail "Claude Code install must copy using-teamwork references"

HOME="$tmp/home-claude-link" "$ROOT/install.sh" --link claude >/dev/null
for skill in "${SKILLS[@]}"; do
  [[ -L "$tmp/home-claude-link/.claude/skills/$skill" ]] || fail "Claude Code link install must symlink $skill directory"
done

HOME="$tmp/home-invalid" "$ROOT/install.sh" gemini >/dev/null 2>&1 && fail "installer must reject unsupported targets"

HOME="$tmp/home-all" "$ROOT/install.sh" --link all >/dev/null
for skill in "${SKILLS[@]}"; do
  [[ -L "$tmp/home-all/.codex/skills/$skill" ]] || fail "all install must link Codex skill $skill"
  [[ -L "$tmp/home-all/.cursor/skills/$skill" ]] || fail "all install must link Cursor skill $skill"
  [[ -L "$tmp/home-all/.claude/skills/$skill" ]] || fail "all install must link Claude skill $skill"
done
for agent in teamwork-explorer teamwork-worker teamwork-designer teamwork-judge teamwork-reviewer; do
  [[ -L "$tmp/home-all/.codex/agents/$agent.toml" ]] || fail "all install must link Codex agent $agent"
done
for agent in explore worker code-reviewer; do
  [[ -L "$tmp/home-all/.claude/agents/$agent.md" ]] || fail "all install must link Claude agent $agent"
done
[[ ! -e "$tmp/home-all/.claude/skills/teamwork" ]] || fail "all install must remove retired teamwork skill"

old_root="$ROOT"
ROOT="$tmp/project-repo"
mkdir -p "$ROOT/skills" "$ROOT/templates/claude-agents" "$ROOT/templates/codex-agents"
cp -R "$old_root/skills/." "$ROOT/skills/"
cp -R "$old_root/templates/claude-agents/." "$ROOT/templates/claude-agents/"
cp -R "$old_root/templates/codex-agents/." "$ROOT/templates/codex-agents/"
cp "$old_root/install.sh" "$ROOT/install.sh"
HOME="$tmp/home-project" ROOT="$ROOT" "$ROOT/install.sh" --link project >/dev/null
for skill in "${SKILLS[@]}"; do
  [[ -L "$ROOT/.cursor/skills/$skill" ]] || fail "project install must link Cursor skill $skill"
done
for agent in teamwork-explorer teamwork-worker teamwork-designer teamwork-judge teamwork-reviewer; do
  [[ -L "$ROOT/.codex/agents/$agent.toml" ]] || fail "project install must link Codex agent $agent"
done
for agent in explore worker code-reviewer; do
  [[ -L "$ROOT/.claude/agents/$agent.md" ]] || fail "project install must link Claude agent $agent"
done
ROOT="$old_root"

HOME="$tmp/home-agents" "$ROOT/install.sh" --link claude-agents >/dev/null
for agent in explore worker code-reviewer; do
  [[ -L "$tmp/home-agents/.claude/agents/$agent.md" ]] \
    || fail "claude-agents install must link $agent.md"
done

echo "OK: Teamwork skill package validates"
