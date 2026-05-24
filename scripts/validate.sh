#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROUTER="$ROOT/skills/teamwork/SKILL.md"
SKILLS=(
  using-teamwork
  teamwork
  teamwork-goal
  teamwork-research
  teamwork-plan
  teamwork-execute
  teamwork-review
)
RETIRED_SKILLS=(
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

expected_skill_dirs="$(printf '%s\n' "${SKILLS[@]}" | sort)"
actual_skill_dirs="$(find "$ROOT/skills" -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | sort)"
[[ "$actual_skill_dirs" == "$expected_skill_dirs" ]] || fail "skills/ must contain exactly: ${SKILLS[*]}"

for retired in "${RETIRED_SKILLS[@]}"; do
  [[ ! -d "$ROOT/skills/$retired" ]] || fail "retired skill directory still exists: skills/$retired"
done

for removed in ".claude-plugin" ".cursor" "commands" "hooks" "bin/raoctl.py" "CLAUDE.md" "CURSOR.md"; do
  [[ ! -e "$ROOT/$removed" ]] || fail "removed runtime surface still exists: $removed"
done

if git -C "$ROOT" ls-files 'docs/teamwork/plans/*' 'docs/teamwork/research/*' 'docs/teamwork/reports/*' 'docs/superpowers/*' | grep -q .; then
  fail "local workflow artifacts under docs/teamwork/{plans,research,reports}/ or docs/superpowers/ must not be tracked"
fi
grep_required '^docs/teamwork/plans/$' "$ROOT/.gitignore" ".gitignore must ignore local Teamwork plan artifacts"
grep_required '^docs/teamwork/research/$' "$ROOT/.gitignore" ".gitignore must ignore local Teamwork research artifacts"
grep_required '^docs/teamwork/reports/$' "$ROOT/.gitignore" ".gitignore must ignore local Teamwork report artifacts"

for skill in "${SKILLS[@]}"; do
  file="$ROOT/skills/$skill/SKILL.md"
  [[ -f "$file" ]] || fail "missing skills/$skill/SKILL.md"
  git -C "$ROOT" ls-files --error-unmatch "skills/$skill/SKILL.md" >/dev/null 2>&1 \
    || fail "skills/$skill/SKILL.md is not tracked by git"
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

for subskill in teamwork-goal teamwork-research teamwork-plan teamwork-execute teamwork-review; do
  grep_required "skills/$subskill/SKILL.md" "$ROUTER" "router does not reference skills/$subskill/SKILL.md"
done

for reference in artifact-protocol goal-iteration subagent-routing workflow-contract; do
  ref_file="$ROOT/skills/teamwork/references/$reference.md"
  [[ -f "$ref_file" ]] || fail "missing skills/teamwork/references/$reference.md"
  git -C "$ROOT" ls-files --error-unmatch "skills/teamwork/references/$reference.md" >/dev/null 2>&1 \
    || fail "skills/teamwork/references/$reference.md is not tracked by git"
done

for skill in teamwork teamwork-goal teamwork-research teamwork-plan teamwork-execute teamwork-review; do
  grep_required 'skills/teamwork/references/workflow-contract.md' "$ROOT/skills/$skill/SKILL.md" \
    "$skill must reference shared workflow contract"
done

[[ -f "$ROOT/.codex-plugin/plugin.json" ]] || fail "missing Codex plugin manifest"
python3 -m json.tool "$ROOT/.codex-plugin/plugin.json" >/dev/null
python3 - "$ROOT" <<'PY'
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
codex = json.loads((root / ".codex-plugin/plugin.json").read_text())
if codex.get("skills") != "./skills/":
    raise SystemExit("FAIL: Codex manifest skills must remain ./skills/")
if "Codex" not in codex.get("description", ""):
    raise SystemExit("FAIL: Codex manifest description must be Codex-specific")
PY

grep_required 'Codex-only' "$ROOT/README.md" "README must state Codex-only positioning"
grep_required 'Codex native capabilities are the execution substrate' "$ROOT/README.md" \
  "README must explain native Codex augmentation"
grep_required 'Native Codex Goal Text' "$ROOT/README.md" \
  "README must document native goal text handoff"
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
grep_required 'Codex-only' "$ROOT/README.en.md" "English README must state Codex-only positioning"
grep_required 'Codex native capabilities are the execution substrate' "$ROOT/README.en.md" \
  "English README must explain native Codex augmentation"
grep_required 'Codex-only skill package' "$ROOT/AGENTS.md" \
  "AGENTS.md must describe the Codex-only package"
grep_required 'Codex native capabilities' "$ROOT/CODEX.md" \
  "CODEX.md must document native Codex capability policy"
[[ "$(wc -l < "$ROOT/README.md")" -le 170 ]] || fail "README should stay concise"
[[ "$(wc -l < "$ROOT/README.en.md")" -le 175 ]] || fail "English README should stay concise"

grep_required 'Codex-native augmentation layer' "$ROUTER" \
  "router must define Teamwork as Codex-native augmentation"
grep_required 'Codex Native Policy Map' "$ROUTER" \
  "router must document Codex native policy map"
grep_required 'Goal Proposal' "$ROUTER" \
  "router must document goal proposal routing"
grep_required 'Proposal/Plan Routed' "$ROUTER" \
  "router must use proposal/plan routed subagent authorization"
grep_required 'Evidence Interpretation Contract' "$ROUTER" \
  "router must define evidence interpretation contract"
grep_required 'Context & Cost Discipline' "$ROUTER" \
  "router must define context and cost discipline"
grep_required 'Subagent Collaboration Model' "$ROUTER" \
  "router must define subagent collaboration model"
grep_required 'Default to at most' "$ROUTER" \
  "router must limit default parallel subagents"
grep_required 'Workflow Pattern Selection' "$ROOT/skills/teamwork/references/workflow-contract.md" \
  "workflow contract must define workflow pattern selection"

grep_required 'Goal Proposal Before Native Goal' "$ROOT/skills/teamwork-goal/SKILL.md" \
  "goal skill must require goal proposal before native goal creation"
grep_required 'Native Codex goal state is the source of truth' "$ROOT/skills/teamwork-goal/SKILL.md" \
  "goal skill must preserve native goal state"
grep_required 'Native Codex Goal Text' "$ROOT/skills/teamwork-goal/SKILL.md" \
  "goal proposal must include native goal text"
grep_required 'create_goal' "$ROOT/skills/teamwork-goal/SKILL.md" \
  "goal skill must hand approved goal text to native create_goal"
grep_required 'Research + Plan Adequacy Gate' "$ROOT/skills/teamwork-goal/SKILL.md" \
  "goal skill must define failure iteration gate"
grep_required 'rolling report' "$ROOT/skills/teamwork-goal/SKILL.md" \
  "goal skill must require rolling report when durable memory is needed"

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
grep_required 'Goal-mode durable plans' "$ROOT/skills/teamwork-plan/SKILL.md" \
  "plan skill must define Codex goal durable plans"
grep_required 'Requirements Mapping' "$ROOT/skills/teamwork-plan/SKILL.md" \
  "plan skill must require requirements mapping"
grep_required 'Search Keys' "$ROOT/skills/teamwork-plan/SKILL.md" \
  "plan artifact template must include Search Keys"
grep_required 'Abstract' "$ROOT/skills/teamwork-plan/SKILL.md" \
  "plan artifact template must include Abstract"
grep_required 'Codex native dispatch fields are derived at dispatch time from the router' "$ROOT/skills/teamwork-plan/SKILL.md" \
  "plan skill must derive native dispatch fields at dispatch time"
grep_required 'codex review' "$ROOT/skills/teamwork-review/SKILL.md" \
  "review skill must mention codex review as evidence"
grep_required 'Routing conformance' "$ROOT/skills/teamwork-review/SKILL.md" \
  "review skill must check routing conformance"
grep_required 'sandbox' "$ROOT/skills/teamwork-execute/SKILL.md" \
  "execute skill must document sandbox approvals"
grep_required 'parallel Worker' "$ROOT/skills/teamwork-execute/SKILL.md" \
  "execute skill must prefer parallel Worker subagents when useful"

for term in observed inferred claimed; do
  grep_required "$term" "$ROUTER" "router must mention $term evidence"
  grep_required "$term" "$ROOT/skills/teamwork-research/SKILL.md" "research skill must mention $term evidence"
  grep_required "$term" "$ROOT/skills/teamwork-plan/SKILL.md" "plan skill must mention $term evidence"
  grep_required "$term" "$ROOT/skills/teamwork-review/SKILL.md" "review skill must mention $term evidence"
done

grep_required 'Explorer -> `agent_type:"explorer"`' "$ROOT/skills/teamwork/references/subagent-routing.md" \
  "subagent routing reference must map Explorer to Codex explorer"
grep_required 'Worker -> `agent_type:"worker"`' "$ROOT/skills/teamwork/references/subagent-routing.md" \
  "subagent routing reference must map Worker to Codex worker"
grep_required 'Designer, Judge, Reviewer -> `agent_type:"default"`' "$ROOT/skills/teamwork/references/subagent-routing.md" \
  "subagent routing reference must map review roles to Codex default"
grep_required '`fast` -> `reasoning_effort:"low"`' "$ROOT/skills/teamwork/references/subagent-routing.md" \
  "subagent routing reference must map fast tier"
grep_required '`standard` -> `reasoning_effort:"medium"`' "$ROOT/skills/teamwork/references/subagent-routing.md" \
  "subagent routing reference must map standard tier"
grep_required '`high reasoning` -> `reasoning_effort:"high"`' "$ROOT/skills/teamwork/references/subagent-routing.md" \
  "subagent routing reference must map high reasoning tier"
grep_required 'Do not combine' "$ROOT/skills/teamwork/references/subagent-routing.md" \
  "subagent routing reference must reject invalid full-history routing"
grep_required 'Research + Plan Adequacy Gate' "$ROOT/skills/teamwork/references/goal-iteration.md" \
  "goal iteration reference must define failure gate"
grep_required 'Research Reuse' "$ROOT/skills/teamwork/references/goal-iteration.md" \
  "goal iteration reference must include research reuse in rolling report"
grep_required 'Search Keys' "$ROOT/skills/teamwork/references/goal-iteration.md" \
  "report template must include Search Keys"
grep_required 'Abstract' "$ROOT/skills/teamwork/references/goal-iteration.md" \
  "report template must include Abstract"
grep_required 'Retrieval Header' "$ROOT/skills/teamwork/references/artifact-protocol.md" \
  "artifact protocol must define Retrieval Header"
grep_required 'docs/teamwork/{research,plans,reports}/' "$ROOT/skills/teamwork/references/artifact-protocol.md" \
  "artifact retrieval must cover research, plans, and reports"
grep_required 'Search Keys' "$ROOT/skills/teamwork/references/artifact-protocol.md" \
  "artifact protocol must define Search Keys"
grep_required 'Abstract' "$ROOT/skills/teamwork/references/artifact-protocol.md" \
  "artifact protocol must define Abstract"

if git -C "$ROOT" grep -n -E 'Claude|Cursor|raoctl|RAO|Stop hook|/rao:|/teamwork:|\.claude|\.cursor|claude-plugin' \
  -- ':!scripts/validate.sh' >/tmp/teamwork-retired-grep.$$; then
  cat /tmp/teamwork-retired-grep.$$ >&2
  rm -f /tmp/teamwork-retired-grep.$$
  fail "retired multi-runtime references remain outside validation"
fi
rm -f /tmp/teamwork-retired-grep.$$

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
HOME="$tmp/home" "$ROOT/install.sh" >/dev/null
for skill in "${SKILLS[@]}"; do
  [[ -f "$tmp/home/.codex/skills/$skill/SKILL.md" ]] || fail "Codex install missing $skill"
  [[ ! -L "$tmp/home/.codex/skills/$skill/SKILL.md" ]] || fail "default install must copy $skill"
  grep_required "^name: $skill$" "$tmp/home/.codex/skills/$skill/SKILL.md" \
    "installed skill has wrong name: $skill"
done
[[ -f "$tmp/home/.codex/skills/teamwork/references/workflow-contract.md" ]] \
  || fail "Codex install must copy teamwork references"

HOME="$tmp/home-link" "$ROOT/install.sh" --link codex >/dev/null
for skill in "${SKILLS[@]}"; do
  [[ -L "$tmp/home-link/.codex/skills/$skill" ]] || fail "link install must symlink $skill directory"
done

HOME="$tmp/home-invalid" "$ROOT/install.sh" cursor >/dev/null 2>&1 && fail "installer must reject non-Codex targets"

echo "OK: Codex-only Teamwork skill package validates"
