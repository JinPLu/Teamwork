#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENTRYPOINT="$ROOT/skills/using-teamwork/SKILL.md"
SKILLS=(
  using-teamwork
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

for removed in ".claude-plugin" ".cursor" "commands" "hooks" "bin/raoctl.py" "CLAUDE.md" "CURSOR.md"; do
  [[ ! -e "$ROOT/$removed" ]] || fail "removed runtime surface still exists: $removed"
done

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

for subskill in teamwork-goal teamwork-research teamwork-plan teamwork-execute teamwork-review teamwork-update; do
  grep_required "skills/$subskill/SKILL.md" "$ENTRYPOINT" "entrypoint/router does not reference skills/$subskill/SKILL.md"
done

for reference in artifact-protocol goal-iteration subagent-routing workflow-contract plan-output review-checks; do
  ref_file="$ROOT/skills/using-teamwork/references/$reference.md"
  [[ -f "$ref_file" ]] || fail "missing skills/using-teamwork/references/$reference.md"
  git_known_or_worktree_addition "skills/using-teamwork/references/$reference.md" \
    || fail "skills/using-teamwork/references/$reference.md is neither tracked nor a worktree addition"
done

for skill in using-teamwork teamwork-goal teamwork-research teamwork-plan teamwork-execute teamwork-review; do
  grep_required 'skills/using-teamwork/references/workflow-contract.md' "$ROOT/skills/$skill/SKILL.md" \
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
version = (root / "VERSION").read_text().strip()
if codex.get("skills") != "./skills/":
    raise SystemExit("FAIL: Codex manifest skills must remain ./skills/")
if "Codex" not in codex.get("description", ""):
    raise SystemExit("FAIL: Codex manifest description must be Codex-specific")
if codex.get("version") != version:
    raise SystemExit("FAIL: Codex manifest version must match VERSION")
PY

grep_required 'Codex-only' "$ROOT/README.md" "README must state Codex-only positioning"
grep_required 'Codex native capabilities are the execution substrate' "$ROOT/README.md" \
  "README must explain native Codex augmentation"
grep_required 'Native Codex Goal Text' "$ROOT/README.md" \
  "README must document native goal text handoff"
grep_required 'teamwork-update' "$ROOT/README.md" \
  "README must document teamwork-update"
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
grep_required 'Codex-only' "$ROOT/README.en.md" "English README must state Codex-only positioning"
grep_required 'Codex native capabilities are the execution substrate' "$ROOT/README.en.md" \
  "English README must explain native Codex augmentation"
grep_required 'teamwork-update' "$ROOT/README.en.md" \
  "English README must document teamwork-update"
grep_required 'VERSION' "$ROOT/README.en.md" \
  "English README must document package version source"
grep_required 'Codex-only skill package' "$ROOT/AGENTS.md" \
  "AGENTS.md must describe the Codex-only package"
grep_required 'teamwork-update' "$ROOT/AGENTS.md" \
  "AGENTS.md must document update skill ownership"
grep_required 'Codex native capabilities' "$ROOT/CODEX.md" \
  "CODEX.md must document native Codex capability policy"
grep_required 'VERSION' "$ROOT/CODEX.md" \
  "CODEX.md must document package version source"
[[ "$(wc -l < "$ROOT/README.md")" -le 170 ]] || fail "README should stay concise"
[[ "$(wc -l < "$ROOT/README.en.md")" -le 175 ]] || fail "English README should stay concise"
line_count_max "$ROOT/skills/using-teamwork/SKILL.md" 80 "using-teamwork should stay concise"
word_count_max "$ROOT/skills/using-teamwork/SKILL.md" 450 "using-teamwork should stay concise"
line_count_max "$ROOT/skills/teamwork-plan/SKILL.md" 120 "teamwork-plan should stay concise"
word_count_max "$ROOT/skills/teamwork-plan/SKILL.md" 650 "teamwork-plan should stay concise"
line_count_max "$ROOT/skills/teamwork-goal/SKILL.md" 120 "teamwork-goal should stay concise"
word_count_max "$ROOT/skills/teamwork-goal/SKILL.md" 650 "teamwork-goal should stay concise"
line_count_max "$ROOT/skills/teamwork-review/SKILL.md" 100 "teamwork-review should stay concise"
word_count_max "$ROOT/skills/teamwork-review/SKILL.md" 550 "teamwork-review should stay concise"
line_count_max "$ROOT/skills/teamwork-research/SKILL.md" 120 "teamwork-research should stay concise"
word_count_max "$ROOT/skills/teamwork-research/SKILL.md" 650 "teamwork-research should stay concise"
line_count_max "$ROOT/skills/teamwork-execute/SKILL.md" 120 "teamwork-execute should stay concise"
word_count_max "$ROOT/skills/teamwork-execute/SKILL.md" 650 "teamwork-execute should stay concise"
line_count_max "$ROOT/skills/teamwork-update/SKILL.md" 80 "teamwork-update should stay concise"
word_count_max "$ROOT/skills/teamwork-update/SKILL.md" 400 "teamwork-update should stay concise"
for skill in "${SKILLS[@]}"; do
  fenced_block_line_count_max "$ROOT/skills/$skill/SKILL.md" 20 "$skill must not embed large fenced templates"
done

grep_required 'Codex-native augmentation layer' "$ENTRYPOINT" \
  "entrypoint/router must define Teamwork as Codex-native augmentation"
grep_required 'Codex Native Policy Map' "$ENTRYPOINT" \
  "entrypoint/router must document Codex native policy map"
grep_required 'Goal Proposal' "$ENTRYPOINT" \
  "entrypoint/router must document goal proposal routing"
grep_required 'Proposal/Plan Routed' "$ENTRYPOINT" \
  "entrypoint/router must use proposal/plan routed subagent authorization"
grep_required 'Evidence Interpretation Contract' "$ENTRYPOINT" \
  "entrypoint/router must define evidence interpretation contract"
grep_required 'Context & Cost Discipline' "$ENTRYPOINT" \
  "entrypoint/router must define context and cost discipline"
grep_required 'Subagent Collaboration Model' "$ENTRYPOINT" \
  "entrypoint/router must define subagent collaboration model"
grep_required 'Dispatch Economics' "$ENTRYPOINT" \
  "entrypoint/router must point to dispatch economics"
grep_required 'Workflow Pattern Selection' "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
  "workflow contract must define workflow pattern selection"
grep_required 'Codex Native Policy Map' "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
  "workflow contract must define Codex native policy map"
grep_required 'starting any coding-agent task' "$ROOT/skills/using-teamwork/SKILL.md" \
  "using-teamwork description must be broad enough for automatic discovery"
grep_required 'discovery reads frontmatter before' "$ROOT/skills/using-teamwork/SKILL.md" \
  "using-teamwork must explain broad discovery before route filtering"

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
grep_required 'Abstract' "$ROOT/skills/using-teamwork/references/plan-output.md" \
  "plan output reference must include Abstract"
grep_required 'Durable Plan Sections' "$ROOT/skills/using-teamwork/references/plan-output.md" \
  "plan output reference must include durable plan sections"
grep_required 'Codex native dispatch fields are derived at dispatch time from the' "$ROOT/skills/teamwork-plan/SKILL.md" \
  "plan skill must derive native dispatch fields at dispatch time"
grep_required 'codex review' "$ROOT/skills/teamwork-review/SKILL.md" \
  "review skill must mention codex review as evidence"
grep_required 'Routing conformance' "$ROOT/skills/teamwork-review/SKILL.md" \
  "review skill must check routing conformance"
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

grep_required 'Explorer -> `agent_type:"explorer"`' "$ROOT/skills/using-teamwork/references/subagent-routing.md" \
  "subagent routing reference must map Explorer to Codex explorer"
grep_required 'Worker -> `agent_type:"worker"`' "$ROOT/skills/using-teamwork/references/subagent-routing.md" \
  "subagent routing reference must map Worker to Codex worker"
grep_required 'Designer, Judge, Reviewer -> `agent_type:"default"`' "$ROOT/skills/using-teamwork/references/subagent-routing.md" \
  "subagent routing reference must map review roles to Codex default"
grep_required '`fast` -> `reasoning_effort:"low"`' "$ROOT/skills/using-teamwork/references/subagent-routing.md" \
  "subagent routing reference must map fast tier"
grep_required '`standard` -> `reasoning_effort:"medium"`' "$ROOT/skills/using-teamwork/references/subagent-routing.md" \
  "subagent routing reference must map standard tier"
grep_required '`high reasoning` -> `reasoning_effort:"high"`' "$ROOT/skills/using-teamwork/references/subagent-routing.md" \
  "subagent routing reference must map high reasoning tier"
grep_required 'Do not combine' "$ROOT/skills/using-teamwork/references/subagent-routing.md" \
  "subagent routing reference must reject invalid full-history routing"
grep_required 'accepted lightweight plan with a Dispatch line' "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
  "workflow contract must authorize lightweight Dispatch"
grep_required 'Explorer/Reviewer: default max 3' "$ROOT/skills/using-teamwork/references/subagent-routing.md" \
  "subagent routing reference must cap Explorer/Reviewer"
grep_required 'Worker: no fixed numeric cap' "$ROOT/skills/using-teamwork/references/subagent-routing.md" \
  "subagent routing reference must not hard-cap Workers"
grep_required 'Before dispatching more than 3 Workers' "$ROOT/skills/using-teamwork/references/subagent-routing.md" \
  "subagent routing reference must require >3 Worker rationale"
grep_required 'ownership map' "$ROOT/skills/using-teamwork/references/subagent-routing.md" \
  "subagent routing reference must require Worker ownership map"
grep_required 'batch or worktree isolation' "$ROOT/skills/using-teamwork/references/subagent-routing.md" \
  "subagent routing reference must define Worker batching or worktree isolation"
grep_required 'local execution is cheaper or safer' "$ROOT/skills/using-teamwork/references/subagent-routing.md" \
  "subagent routing reference must preserve local execution escape hatch"
grep_required 'Default to parallel Explorer subagents' "$ROOT/skills/teamwork-research/SKILL.md" \
  "research skill must default-dispatch independent Explorer tracks"
grep_required 'lightweight `Dispatch:`' "$ROOT/skills/teamwork-plan/SKILL.md" \
  "plan skill must support lightweight Dispatch"
grep_required 'dispatch parallel Worker subagents by default' "$ROOT/skills/teamwork-execute/SKILL.md" \
  "execute skill must default-dispatch independent Worker tracks"
grep_required 'Before dispatching more than 3 Workers' "$ROOT/skills/teamwork-execute/SKILL.md" \
  "execute skill must require >3 Worker integration plan"
grep_required 'Default to fresh-context review' "$ROOT/skills/teamwork-review/SKILL.md" \
  "review skill must default to fresh-context review for non-trivial execution"
grep_required 'Dispatch: none | Explorer/Worker/Reviewer tracks, ownership, cap/batch reason' "$ROOT/skills/using-teamwork/references/plan-output.md" \
  "lightweight plan template must include Dispatch line"
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

if git -C "$ROOT" grep -n -E 'Claude|Cursor|raoctl|RAO|Stop hook|/rao:|/teamwork:|\.claude|\.cursor|claude-plugin' \
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
for reference in artifact-protocol goal-iteration subagent-routing workflow-contract plan-output review-checks; do
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

HOME="$tmp/home-invalid" "$ROOT/install.sh" cursor >/dev/null 2>&1 && fail "installer must reject non-Codex targets"

echo "OK: Codex-only Teamwork skill package validates"
