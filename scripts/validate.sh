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

expected_skill_dirs="$(printf '%s\n' "${SKILLS[@]}" | sort)"
actual_skill_dirs="$(find "$ROOT/skills" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort)"
[[ "$actual_skill_dirs" == "$expected_skill_dirs" ]] || fail "skills/ must contain exactly: ${SKILLS[*]}"

if git -C "$ROOT" ls-files 'docs/teamwork/plans/*' 'docs/teamwork/research/*' 'docs/teamwork/reports/*' 'docs/superpowers/*' | grep -q .; then
  fail "local workflow artifacts under docs/teamwork/{plans,research,reports}/ or docs/superpowers/ must not be tracked"
fi
grep -q '^docs/teamwork/plans/$' "$ROOT/.gitignore" \
  || fail ".gitignore must ignore local Teamwork plan artifacts"
grep -q '^docs/teamwork/research/$' "$ROOT/.gitignore" \
  || fail ".gitignore must ignore local Teamwork research artifacts"
grep -q '^docs/teamwork/reports/$' "$ROOT/.gitignore" \
  || fail ".gitignore must ignore local Teamwork report artifacts"
grep -q '^docs/superpowers/$' "$ROOT/.gitignore" \
  || fail ".gitignore must ignore local superpowers artifacts"

for retired in "${RETIRED_SKILLS[@]}"; do
  [[ ! -d "$ROOT/skills/$retired" ]] || fail "retired skill directory still exists: skills/$retired"
done

for skill in "${SKILLS[@]}"; do
  file="$ROOT/skills/$skill/SKILL.md"
  [[ -f "$file" ]] || fail "missing skills/$skill/SKILL.md"
  git -C "$ROOT" ls-files --error-unmatch "skills/$skill/SKILL.md" >/dev/null 2>&1 \
    || fail "skills/$skill/SKILL.md is not tracked by git"
  head -n 1 "$file" | grep -qx -- "---" || fail "$skill SKILL.md must start with YAML frontmatter"
  grep -q "^name: $skill$" "$file" || fail "$skill missing matching skill name"
  grep -Eq '^description: Use when .+' "$file" || fail "$skill description must start with: Use when"
  ! grep -q '^disable-model-invocation:' "$file" || fail "$skill uses unsupported disable-model-invocation metadata"
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
  grep -q "skills/$subskill/SKILL.md" "$ROUTER" || fail "router does not reference skills/$subskill/SKILL.md"
done

grep -q 'teamwork-goal' "$ROUTER" || fail "router must route goal requests to teamwork-goal"
! grep -q 'Do not create separate research, plan, or goal subskills' "$ROUTER" \
  || fail "router must not forbid the dedicated goal subskill"
grep -q 'mode: goal' "$ROOT/skills/teamwork-goal/SKILL.md" || fail "goal skill missing mode: goal"
grep -q 'Research Artifact Requirement' "$ROOT/skills/teamwork-research/SKILL.md" || fail "research skill must require research artifacts"
grep -q 'when findings will be reused' "$ROOT/skills/teamwork-research/SKILL.md" || fail "research artifacts must be targeted to reusable findings"
grep -q 'Research Refresh Triggers' "$ROOT/skills/teamwork-research/SKILL.md" || fail "research skill must define refresh triggers"
grep -q 'docs/teamwork/research/YYYY-MM-DD-<slug>.md' "$ROOT/skills/teamwork-research/SKILL.md" || fail "research skill must define research artifact path"
grep -q 'Use the lightest planning form that preserves correctness' "$ROOT/skills/teamwork-plan/SKILL.md" || fail "plan skill must support lightweight and durable planning tiers"
grep -q 'docs/teamwork/plans/YYYY-MM-DD-<slug>.md' "$ROOT/skills/teamwork-plan/SKILL.md" || fail "plan skill must define durable plan path"
grep -q 'mode: plan' "$ROOT/skills/teamwork-review/SKILL.md" || fail "review skill missing mode: plan"
grep -q 'mode: execution' "$ROOT/skills/teamwork-review/SKILL.md" || fail "review skill missing mode: execution"

[[ -f "$ROOT/.claude-plugin/plugin.json" ]] || fail "missing Claude plugin manifest"
[[ -f "$ROOT/.codex-plugin/plugin.json" ]] || fail "missing Codex plugin manifest"
[[ -f "$ROOT/.cursor/rules/teamwork.mdc" ]] || fail "missing Cursor rule"

python3 -m json.tool "$ROOT/.claude-plugin/plugin.json" >/dev/null
python3 -m json.tool "$ROOT/.claude-plugin/marketplace.json" >/dev/null
python3 -m json.tool "$ROOT/.codex-plugin/plugin.json" >/dev/null

python3 - "$ROOT" <<'PY'
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
expected = [
    "./skills/using-teamwork",
    "./skills/teamwork",
    "./skills/teamwork-goal",
    "./skills/teamwork-research",
    "./skills/teamwork-plan",
    "./skills/teamwork-execute",
    "./skills/teamwork-review",
]
retired = {
    "./skills/teamwork-design",
    "./skills/run-analyze-optimize",
    "./skills/run-analyze-design",
    "./skills/run-analyze-execute",
    "./skills/run-analyze-review",
    "./skills/run-analyze-research",
    "./skills/run-analyze-plan",
    "./skills/run-analyze-goal",
}

claude = json.loads((root / ".claude-plugin/plugin.json").read_text())
if claude.get("skills") != expected:
    raise SystemExit("FAIL: Claude manifest skills must list the current skill directories")
if retired.intersection(claude.get("skills", [])):
    raise SystemExit("FAIL: Claude manifest still lists retired skills")

codex = json.loads((root / ".codex-plugin/plugin.json").read_text())
if codex.get("skills") != "./skills/":
    raise SystemExit("FAIL: Codex manifest skills must remain ./skills/")
PY

[[ -f "$ROOT/bin/raoctl.py" ]] || fail "missing Teamwork runtime controller"
[[ -f "$ROOT/hooks/hooks.json" ]] || fail "missing Claude hook definitions"
[[ -f "$ROOT/AGENTS.md" ]] || fail "missing AGENTS.md repository guidance"
grep -q 'This repository packages the Teamwork workflow' "$ROOT/AGENTS.md" \
  || fail "AGENTS.md must describe the Teamwork package"
grep -q 'commands/teamwork/\*.md' "$ROOT/AGENTS.md" \
  || fail "AGENTS.md must document /teamwork command files"
grep -q 'seven Teamwork skills' "$ROOT/AGENTS.md" \
  || fail "AGENTS.md must document the current skill count"
! grep -q 'packages the run-analyze-optimize workflow' "$ROOT/AGENTS.md" \
  || fail "AGENTS.md must not describe run-analyze-optimize as the active package"
[[ -d "$ROOT/commands/teamwork" ]] || fail "missing /teamwork command directory"
for command in goal status pause resume stop complete clear note help plan checkpoint; do
  [[ -f "$ROOT/commands/teamwork/$command.md" ]] || fail "missing /teamwork:$command command"
done
[[ -d "$ROOT/commands/rao" ]] || fail "missing /rao command directory"
for command in goal status pause resume stop complete clear note help plan checkpoint; do
  [[ -f "$ROOT/commands/rao/$command.md" ]] || fail "missing /rao:$command command"
done
grep -q 'hook-stop' "$ROOT/hooks/hooks.json" || fail "hooks must include Stop continuation"
grep -q 'raoctl.py' "$ROOT/hooks/hooks.json" || fail "hooks must invoke raoctl.py"
grep -q '/teamwork:goal' "$ROOT/README.md" || fail "README must document /teamwork:goal"
grep -q '/rao:goal' "$ROOT/README.md" || fail "README must document /rao:goal compatibility"
grep -q 'Stop hook' "$ROOT/README.md" || fail "README must document Stop hook behavior"
grep -q '.claude/teamwork-goals' "$ROOT/README.md" || fail "README must document goal state path"
grep -q 'RAO_GOAL_COMPLETE' "$ROOT/README.md" || fail "README must document completion promise"
grep -q 'docs/teamwork/reports/YYYY-MM-DD-<slug>.md' "$ROOT/README.md" \
  || fail "README must document report artifact path"
grep -q 'Codex Native Integration' "$ROUTER" || fail "router must document Codex native integration"
grep -q 'native Codex goals' "$ROOT/CODEX.md" || fail "CODEX.md must document native Codex goals"
grep -q 'Codex Runtime Mapping' "$ROOT/CODEX.md" || fail "CODEX.md must document Codex runtime mapping"
grep -q 'Codex runtime' "$ROOT/README.md" || fail "README must document Codex runtime"
grep -q 'durable Markdown plan artifact' "$ROUTER" || fail "router must define durable Markdown plan artifacts"
grep -q 'Progress Anchors And Artifacts' "$ROUTER" || fail "router must define progress anchors and artifacts"
grep -q 'docs/teamwork/reports/YYYY-MM-DD-<slug>.md' "$ROUTER" \
  || fail "router must define report artifact path"
grep -q 'transient UI-only checklist' "$ROUTER" || fail "router must mark update_plan as transient UI-only"
grep -q 'native flow remains the default for simple Claude Code tasks' "$ROUTER" \
  || fail "router must preserve native Claude Code flow for simple tasks"
grep -q 'automatic subagent delegation' "$ROOT/skills/teamwork/SKILL.md" \
  || fail "router must authorize automatic subagent delegation on non-lightweight tracks"
grep -q 'extra "fan out" confirmation' "$ROOT/skills/teamwork/SKILL.md" \
  || fail "router must not require explicit fan-out confirmation"
grep -q 'automatic subagent delegation' "$ROOT/skills/using-teamwork/SKILL.md" \
  || fail "entry skill must authorize automatic subagent delegation"
grep -q 'Teamwork 激活后，视为用户已授权对独立的非轻量轨道自动分配 subagent' "$ROOT/README.md" \
  || fail "README must document automatic delegation"
grep -q 'automatic subagent delegation' "$ROOT/CODEX.md" \
  || fail "CODEX.md must document automatic delegation"
grep -q 'standing authorization for automatic subagent delegation' "$ROOT/AGENTS.md" \
  || fail "AGENTS.md must document automatic delegation"
grep -q 'standing authorization for automatic subagent delegation' "$ROOT/CLAUDE.md" \
  || fail "CLAUDE.md must document automatic delegation"
grep -q 'docs/teamwork/plans/YYYY-MM-DD-<slug>.md' "$ROOT/skills/teamwork-plan/SKILL.md" \
  || fail "plan skill must define the durable plan path"
grep -q 'Use the lightest planning form that preserves correctness' "$ROOT/skills/teamwork-plan/SKILL.md" \
  || fail "plan skill must support lightweight and durable planning tiers"
grep -q 'Lightweight plan' "$ROOT/skills/teamwork-plan/SKILL.md" \
  || fail "plan skill must define lightweight planning"
grep -q 'Durable artifact plan' "$ROOT/skills/teamwork-plan/SKILL.md" \
  || fail "plan skill must define durable artifact planning"
grep -q 'Requirements Mapping' "$ROOT/skills/teamwork-plan/SKILL.md" \
  || fail "plan skill must require requirements mapping in plan artifacts"
grep -q '^Goal:$' "$ROOT/skills/teamwork-plan/SKILL.md" \
  || fail "plan output template must include a Goal section"
grep -q 'Expected Results' "$ROOT/skills/teamwork-plan/SKILL.md" \
  || fail "plan skill must require expected verification results"
grep -q 'compact execution memo' "$ROOT/skills/teamwork-plan/SKILL.md" \
  || fail "plan skill must support compact execution memos"
grep -q 'must return `revise` or `blocked`' "$ROOT/skills/teamwork-review/SKILL.md" \
  || fail "review skill must hard-fail weak durable-required plans"
grep -q 'For durable-required work' "$ROOT/skills/teamwork-review/SKILL.md" \
  || fail "review skill must distinguish lightweight and durable plan gates"
grep -q 'requirements-to-evidence mapping' "$ROOT/skills/teamwork-review/SKILL.md" \
  || fail "review skill must check requirements-to-evidence mapping"
grep -q 'docs/teamwork/plans/YYYY-MM-DD-<slug>.md' "$ROOT/README.md" \
  || fail "README must document durable plan artifact path"
grep -q 'durable Markdown plan artifacts' "$ROOT/CODEX.md" \
  || fail "CODEX.md must document durable Markdown plan artifacts"
grep -q 'Use durable Markdown plan artifacts for cross-agent execution' "$ROOT/CODEX.md" \
  || fail "CODEX.md must require durable artifacts for cross-agent/high-risk work"
grep -q 'docs/teamwork/reports/YYYY-MM-DD-<slug>.md' "$ROOT/CODEX.md" \
  || fail "CODEX.md must document report artifact path"
grep -q 'Small, low-risk edits may use a' "$ROOT/CODEX.md" \
  || fail "CODEX.md must allow lightweight planning for bounded low-risk work"
grep -q 'It is not Codex' "$ROOT/CODEX.md" \
  || fail "CODEX.md must distinguish plan artifacts from Codex goal state"
grep -q 'goal state and not Claude `.claude/teamwork-goals/` runtime state' "$ROOT/CODEX.md" \
  || fail "CODEX.md must distinguish plan artifacts from Claude goal runtime"
grep -q 'codex review' "$ROOT/skills/teamwork-review/SKILL.md" || fail "review skill must mention codex review"
grep -q 'sandbox' "$ROOT/skills/teamwork-execute/SKILL.md" || fail "execute skill must document sandbox approvals"
grep -q 'durable Markdown plan artifact path' "$ROOT/skills/teamwork-execute/SKILL.md" \
  || fail "execute skill must require a durable plan artifact path"
grep -q 'active_plan_artifact' "$ROOT/skills/teamwork-goal/SKILL.md" \
  || fail "goal skill must document active_plan_artifact"
grep -q '<plan_artifact>' "$ROOT/skills/teamwork-goal/SKILL.md" \
  || fail "goal skill must document plan_artifact completion audit field"
grep -q 'Subagent Routing Policy' "$ROUTER" || fail "router must define subagent routing policy"
grep -q 'Codex Dispatch Mapping' "$ROUTER" || fail "router must define Codex dispatch mapping"
grep -q 'Designer' "$ROUTER" || fail "router must define Designer subagent role"
grep -q 'model tier' "$ROUTER" || fail "router must document model tier routing"
grep -q '`fast`' "$ROUTER" || fail "router must document fast routing tier"
grep -q '`standard`' "$ROUTER" || fail "router must document standard routing tier"
grep -q 'high reasoning' "$ROUTER" || fail "router must document high reasoning routing tier"
grep -q '`fast` -> `reasoning_effort:"low"`' "$ROUTER" \
  || fail "router must map fast tier to low Codex reasoning effort"
grep -q '`standard` -> `reasoning_effort:"medium"`' "$ROUTER" \
  || fail "router must map standard tier to medium Codex reasoning effort"
grep -q '`high reasoning` -> `reasoning_effort:"high"`' "$ROUTER" \
  || fail "router must map high reasoning tier to high Codex reasoning effort"
grep -q 'reasoning_effort:"xhigh"' "$ROUTER" \
  || fail "router must document xhigh only for explicitly high-risk final gates"
grep -q 'Explorer -> `agent_type:"explorer"`' "$ROUTER" \
  || fail "router must map Explorer to Codex explorer agent type"
grep -q 'Worker -> `agent_type:"worker"`' "$ROUTER" \
  || fail "router must map Worker to Codex worker agent type"
grep -q 'Designer -> `agent_type:"default"`' "$ROUTER" \
  || fail "router must map Designer to Codex default agent type"
grep -q 'Judge -> `agent_type:"default"`' "$ROUTER" \
  || fail "router must map Judge to Codex default agent type"
grep -q 'Reviewer -> `agent_type:"default"`' "$ROUTER" \
  || fail "router must map Reviewer to Codex default agent type"
grep -q 'Full-history fork inheritance' "$ROUTER" \
  || fail "router must document fork_context:true inheritance"
grep -q 'use `fork_context:false` or omit `fork_context`' "$ROUTER" \
  || fail "router must document fork_context:false explicit routing"
grep -q 'Omit `agent_type`, `model`, and' "$ROUTER" \
  || fail "router must require omitting override fields on full-history forks"
grep -q 'Subagent Routing' "$ROOT/skills/teamwork-plan/SKILL.md" || fail "plan skill must document subagent routing"
grep -q 'if subagents are used' "$ROOT/skills/teamwork-plan/SKILL.md" \
  || fail "plan skill must make subagent routing conditional"
grep -q 'model tier' "$ROOT/skills/teamwork-plan/SKILL.md" || fail "plan skill must require model tier in subagent routing"
grep -q 'context strategy' "$ROOT/skills/teamwork-plan/SKILL.md" \
  || fail "plan skill must require context strategy in subagent routing"
grep -q 'Codex native dispatch fields are derived at dispatch time from the router' "$ROOT/skills/teamwork-plan/SKILL.md" \
  || fail "plan skill must derive native Codex fields at dispatch time"
if grep -q 'Codex `agent_type`' "$ROOT/skills/teamwork-plan/SKILL.md"; then
  fail "plan skill must not require Codex agent_type in ordinary routing entries"
fi
if grep -q '`fork_context`:' "$ROOT/skills/teamwork-plan/SKILL.md"; then
  fail "plan skill must not require fork_context in ordinary routing entries"
fi
if grep -q '`reasoning_effort`:' "$ROOT/skills/teamwork-plan/SKILL.md"; then
  fail "plan skill must not require reasoning_effort in ordinary routing entries"
fi
if grep -q 'xhigh' "$ROOT/skills/teamwork-plan/SKILL.md"; then
  fail "plan skill must not list xhigh as a normal plan-template option"
fi
grep -q 'Workers execute the accepted plan' "$ROOT/skills/teamwork-execute/SKILL.md" \
  || fail "execute skill must keep Worker execution boundary"
grep -q 'disjoint file ownership' "$ROOT/skills/teamwork-execute/SKILL.md" \
  || fail "execute skill must require disjoint Worker ownership"
grep -q 'do not reopen product behavior' "$ROOT/skills/teamwork-execute/SKILL.md" \
  || fail "execute skill must block design reopening during execution"
grep -q 'Do not combine `fork_context:true` with `agent_type`, `model`, or' "$ROOT/skills/teamwork-execute/SKILL.md" \
  || fail "execute skill must reject full-history fork plus override fields"
grep -q 'Do not use nonexistent Codex agent types' "$ROOT/skills/teamwork-execute/SKILL.md" \
  || fail "execute skill must reject nonexistent Codex agent types"
grep -q 'Routing conformance' "$ROOT/skills/teamwork-review/SKILL.md" \
  || fail "review skill must check routing conformance"
grep -q 'fresh-context review' "$ROOT/skills/teamwork-review/SKILL.md" \
  || fail "review skill must prefer fresh-context review for non-trivial execution"
grep -q 'If subagents are used' "$ROOT/skills/teamwork-review/SKILL.md" \
  || fail "review skill must review subagent routing only when used"
grep -q 'low-capability tier' "$ROOT/skills/teamwork-review/SKILL.md" \
  || fail "review skill must block underpowered high-risk routing"
grep -q 'explicitly includes native dispatch fields and combines' "$ROOT/skills/teamwork-review/SKILL.md" \
  || fail "review skill must inspect explicit native dispatch fields"
grep -q '`fork_context:true` with `agent_type`, `model`, or' "$ROOT/skills/teamwork-review/SKILL.md" \
  || fail "review skill must reject full-history fork plus override fields"
grep -q 'nonexistent native agent types' "$ROOT/skills/teamwork-review/SKILL.md" \
  || fail "review skill must reject nonexistent Codex agent types"
grep -q 'Derive native Codex fields' "$ROOT/CODEX.md" \
  || fail "CODEX.md must document native Codex field derivation"
grep -q 'skills/teamwork/SKILL.md' "$ROOT/CODEX.md" \
  || fail "CODEX.md must point to router for native Codex dispatch mapping"
grep -q 'Ordinary plans should record conceptual role, scope' "$ROOT/README.md" \
  || fail "README must keep Codex dispatch guidance concise and conceptual"
if grep -R -E 'agent_type:"(judge|reviewer|designer)"|agent_type: "(judge|reviewer|designer)"' \
  "$ROOT/skills" "$ROOT/CODEX.md" "$ROOT/README.md" >/dev/null; then
  fail "Codex docs must not use nonexistent judge/reviewer/designer agent_type values"
fi
if grep -R -i -E 'full-history fork (with|plus) overrides is valid|fork_context:true .*overrides are valid' \
  "$ROOT/skills" "$ROOT/CODEX.md" "$ROOT/README.md" >/dev/null; then
  fail "Codex docs must not endorse full-history fork plus override routing"
fi
grep -q 'plan_review_verdict: <pass | pass-with-notes>' "$ROOT/skills/teamwork-goal/SKILL.md" \
  || fail "goal completion audit must only allow passing plan review verdicts"
grep -q 'execution_review_verdict: <pass | pass-with-notes>' "$ROOT/skills/teamwork-goal/SKILL.md" \
  || fail "goal completion audit must only allow passing execution review verdicts"
! grep -q 'review_verdict: <pass | pass-with-notes | revise | blocked>' "$ROOT/skills/teamwork-goal/SKILL.md" \
  || fail "goal completion audit must not list non-passing review verdicts"
grep -q 'MCP' "$ROOT/CODEX.md" || fail "CODEX.md must document MCP/network fallback"
grep -q 'Evidence Interpretation Contract' "$ROUTER" || fail "router must define evidence interpretation contract"
grep -q 'Evidence Interpretation Contract' "$ROOT/skills/teamwork-research/SKILL.md" || fail "research skill must define evidence interpretation contract"
grep -q 'Evidence Interpretation Contract' "$ROOT/skills/teamwork-plan/SKILL.md" || fail "plan skill must define evidence interpretation contract"
grep -q 'Context & Cost Discipline' "$ROUTER" || fail "router must define context and cost discipline"
grep -q 'Context & Cost Discipline' "$ROOT/skills/teamwork-research/SKILL.md" || fail "research skill must define context and cost discipline"
grep -q 'Context & Cost Discipline' "$ROOT/skills/teamwork-plan/SKILL.md" || fail "plan skill must define context and cost discipline"
grep -q 'external calibration' "$ROOT/skills/teamwork-research/SKILL.md" \
  || fail "research skill must require external calibration"
grep -q 'Search existing research artifacts' "$ROOT/skills/teamwork-research/SKILL.md" \
  || fail "research skill must reuse existing research artifacts"
grep -q 'no evidence delta' "$ROOT/skills/teamwork-research/SKILL.md" \
  || fail "research skill must break local no-progress loops"
grep -q 'Research calibration' "$ROOT/README.md" \
  || fail "README must document research calibration"
grep -q 'Research calibration' "$ROOT/CODEX.md" \
  || fail "CODEX.md must document research calibration"
grep -q 'Subagent Collaboration Model' "$ROUTER" || fail "router must define subagent collaboration model"
grep -q 'separable evidence questions' "$ROOT/skills/teamwork-research/SKILL.md" \
  || fail "research skill must prefer parallel Explorer tracks when separable"
for term in observed inferred claimed; do
  grep -q "$term" "$ROUTER" || fail "router must mention $term evidence"
  grep -q "$term" "$ROOT/skills/teamwork-research/SKILL.md" || fail "research skill must mention $term evidence"
  grep -q "$term" "$ROOT/skills/teamwork-plan/SKILL.md" || fail "plan skill must mention $term evidence"
  grep -q "$term" "$ROOT/skills/teamwork-review/SKILL.md" || fail "review skill must mention $term evidence"
done
grep -q 'at most 3 parallel' "$ROUTER" || fail "router must limit default parallel subagents"
grep -q '<completion_audit>' "$ROOT/skills/teamwork-goal/SKILL.md" || fail "goal skill must document completion audit format"
grep -q '<completion_audit>' "$ROOT/README.md" || fail "README must document completion audit format"
grep -q 'completion_audit_detected' "$ROOT/bin/raoctl.py" || fail "runtime must gate completion on audit detection"
grep -q 'active_plan_artifact' "$ROOT/bin/raoctl.py" || fail "runtime must store active_plan_artifact"
grep -q 'active_plan_artifact_sha256' "$ROOT/bin/raoctl.py" || fail "runtime must store active_plan_artifact_sha256"
grep -q 'COMPACT_PLAN_REQUIRED_SECTIONS' "$ROOT/bin/raoctl.py" || fail "runtime must accept compact execution memos"
grep -q 'command_plan' "$ROOT/bin/raoctl.py" || fail "runtime must expose a plan command"
grep -q 'command_checkpoint' "$ROOT/bin/raoctl.py" || fail "runtime must expose a checkpoint command"
grep -q 'PASSING_REVIEW_VERDICTS' "$ROOT/bin/raoctl.py" || fail "runtime must parse passing review verdicts"
grep -q 'manual /rao:complete override' "$ROOT/bin/raoctl.py" || fail "runtime must mark manual completion override"
grep -q 'Narrative-mislead risk' "$ROOT/skills/teamwork-review/SKILL.md" || fail "review skill must check narrative-mislead risk"
grep -q 'Treat executor summaries' "$ROOT/skills/teamwork-review/SKILL.md" || fail "review skill must treat summaries as evidence only"
! grep -q 'teamwork-design` mode: plan' "$ROOT/bin/raoctl.py" \
  || fail "runtime continuation prompt must not mention retired teamwork-design skill"

tmp_runtime="$(mktemp -d)"
first_stop="$tmp_runtime/first-stop.json"
promise_only_stop="$tmp_runtime/promise-only-stop.json"
missing_requirements_stop="$tmp_runtime/missing-requirements-stop.json"
missing_verification_stop="$tmp_runtime/missing-verification-stop.json"
missing_dissent_stop="$tmp_runtime/missing-dissent-stop.json"
missing_plan_stop="$tmp_runtime/missing-plan-stop.json"
missing_sha_stop="$tmp_runtime/missing-sha-stop.json"
wrong_plan_stop="$tmp_runtime/wrong-plan-stop.json"
wrong_sha_stop="$tmp_runtime/wrong-sha-stop.json"
hash_mismatch_stop="$tmp_runtime/hash-mismatch-stop.json"
missing_checkpoint_stop="$tmp_runtime/missing-checkpoint-stop.json"
verification_fail_stop="$tmp_runtime/verification-fail-stop.json"
review_revise_stop="$tmp_runtime/review-revise-stop.json"
invalid_review_stop="$tmp_runtime/invalid-review-stop.json"
uppercase_review_stop="$tmp_runtime/uppercase-review-stop.json"
complete_stop="$tmp_runtime/complete-stop.json"
pass_with_notes_stop="$tmp_runtime/pass-with-notes-stop.json"
no_progress_stop="$tmp_runtime/no-progress-stop.json"
max_stop="$tmp_runtime/max-stop.json"
hook_json() {
  local cwd="$1"
  local message="$2"
  python3 - "$cwd" "$message" <<'PY'
import json
import sys

print(json.dumps({"session_id": "s1", "cwd": sys.argv[1], "last_assistant_message": sys.argv[2]}, separators=(",", ":")))
PY
}
write_valid_plan() {
  local path="$1"
  python3 - "$path" <<'PY'
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("""# Runtime Smoke Plan

## Goal

Validate the runtime smoke path.

## Requirements Mapping

- Runtime smoke requirement maps to focused validation evidence.

## Evidence Read

- Observed runtime smoke fixture.

## Scope

- Validate the smoke fixture only.

## Implementation Steps

1. Record the plan.
2. Record checkpoint evidence.

## Verification

- Command: runtime smoke command.
- Expected Results: command exits with status 0.

## Risks

- Smoke fixture may drift.

## Stop Rules

- Stop on failed smoke evidence.

## Worker Handoff

Worker executes the smoke fixture only.

## Review Handoff

Reviewer checks runtime smoke evidence.

## Subagent Routing

- Worker: main agent | scope: smoke fixture | tier: standard | context: local | order: serial | why: compact.
""", encoding="utf-8")
PY
}
write_compact_plan() {
  local path="$1"
  python3 - "$path" <<'PY'
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text("""# Runtime Compact Memo

## Goal

Validate the compact execution memo path.

## Scope

- Validate compact plan linting only.

## Implementation Steps

1. Record the compact memo.

## Verification

- Command: runtime compact smoke command.
- Expected Results: command exits with status 0.

## Stop Rules

- Stop on failed smoke evidence.

## Worker Handoff

Worker executes the compact fixture only.

## Review Handoff

Reviewer checks compact smoke evidence.
""", encoding="utf-8")
PY
}
plan_sha() {
  python3 - "$1" <<'PY'
import hashlib
import pathlib
import sys

print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())
PY
}
record_checkpoint() {
  python3 "$ROOT/bin/raoctl.py" checkpoint --session-id s1 --cwd "$1" \
    --plan-review-verdict "${2:-pass}" \
    --execution-review-verdict "${3:-pass}" \
    --verification-command "runtime smoke command" \
    --verification-result "${4:-pass}" \
    --evidence-delta "${5:-progress}" >/dev/null
}
audit_block() {
  local sha="$1"
  local plan_review="${2:-pass}"
  local execution_review="${3:-pass}"
  cat <<EOF
<completion_audit>
<plan_artifact>docs/teamwork/plans/runtime-smoke.md</plan_artifact>
<plan_artifact_sha256>$sha</plan_artifact_sha256>
<plan_review_verdict>$plan_review</plan_review_verdict>
<execution_review_verdict>$execution_review</execution_review_verdict>
<requirements_mapping>objective mapped to focused validation evidence</requirements_mapping>
<verification_evidence>focused smoke command passed</verification_evidence>
<dissent>none</dissent>
</completion_audit>
EOF
}
missing_verification_audit='<completion_audit>
<plan_artifact>docs/teamwork/plans/runtime-smoke.md</plan_artifact>
<plan_artifact_sha256>missing</plan_artifact_sha256>
<plan_review_verdict>pass</plan_review_verdict>
<execution_review_verdict>pass</execution_review_verdict>
<requirements_mapping>objective mapped to focused validation evidence</requirements_mapping>
<dissent>none</dissent>
</completion_audit>'
missing_requirements_audit='<completion_audit>
<plan_artifact>docs/teamwork/plans/runtime-smoke.md</plan_artifact>
<plan_artifact_sha256>missing</plan_artifact_sha256>
<plan_review_verdict>pass</plan_review_verdict>
<execution_review_verdict>pass</execution_review_verdict>
<verification_evidence>focused smoke command passed</verification_evidence>
<dissent>none</dissent>
</completion_audit>'
missing_dissent_audit='<completion_audit>
<plan_artifact>docs/teamwork/plans/runtime-smoke.md</plan_artifact>
<plan_artifact_sha256>missing</plan_artifact_sha256>
<plan_review_verdict>pass</plan_review_verdict>
<execution_review_verdict>pass</execution_review_verdict>
<requirements_mapping>objective mapped to focused validation evidence</requirements_mapping>
<verification_evidence>focused smoke command passed</verification_evidence>
</completion_audit>'
missing_plan_audit='<completion_audit>
<plan_artifact_sha256>missing</plan_artifact_sha256>
<plan_review_verdict>pass</plan_review_verdict>
<execution_review_verdict>pass</execution_review_verdict>
<requirements_mapping>objective mapped to focused validation evidence</requirements_mapping>
<verification_evidence>focused smoke command passed</verification_evidence>
<dissent>none</dissent>
</completion_audit>'
missing_sha_audit='<completion_audit>
<plan_artifact>docs/teamwork/plans/runtime-smoke.md</plan_artifact>
<plan_review_verdict>pass</plan_review_verdict>
<execution_review_verdict>pass</execution_review_verdict>
<requirements_mapping>objective mapped to focused validation evidence</requirements_mapping>
<verification_evidence>focused smoke command passed</verification_evidence>
<dissent>none</dissent>
</completion_audit>'
wrong_plan_audit='<completion_audit>
<plan_artifact>docs/teamwork/plans/wrong.md</plan_artifact>
<plan_artifact_sha256>missing</plan_artifact_sha256>
<plan_review_verdict>pass</plan_review_verdict>
<execution_review_verdict>pass</execution_review_verdict>
<requirements_mapping>objective mapped to focused validation evidence</requirements_mapping>
<verification_evidence>focused smoke command passed</verification_evidence>
<dissent>none</dissent>
</completion_audit>'
invalid_review_audit='<completion_audit>
<plan_artifact>docs/teamwork/plans/runtime-smoke.md</plan_artifact>
<plan_artifact_sha256>missing</plan_artifact_sha256>
<plan_review_verdict>revise</plan_review_verdict>
<execution_review_verdict>pass</execution_review_verdict>
<requirements_mapping>objective mapped to focused validation evidence</requirements_mapping>
<verification_evidence>focused smoke command passed</verification_evidence>
<dissent>none</dissent>
</completion_audit>'
uppercase_review_audit='<completion_audit>
<plan_artifact>docs/teamwork/plans/runtime-smoke.md</plan_artifact>
<plan_artifact_sha256>missing</plan_artifact_sha256>
<plan_review_verdict>PASS</plan_review_verdict>
<execution_review_verdict>pass</execution_review_verdict>
<requirements_mapping>objective mapped to focused validation evidence</requirements_mapping>
<verification_evidence>focused smoke command passed</verification_evidence>
<dissent>none</dissent>
</completion_audit>'
python3 "$ROOT/bin/raoctl.py" goal --session-id s1 --max-iterations 2 --completion-promise RAO_GOAL_COMPLETE 'verify runtime continuation' --cwd "$tmp_runtime" >/dev/null
mkdir -p "$tmp_runtime/docs/teamwork/plans"
write_valid_plan "$tmp_runtime/docs/teamwork/plans/runtime-smoke.md"
write_compact_plan "$tmp_runtime/docs/teamwork/plans/compact-smoke.md"
printf '# Weak plan\n\n## Goal\n\nTBD\n' > "$tmp_runtime/docs/teamwork/plans/weak.md"
printf '# Wrong path plan\n' > "$tmp_runtime/runtime-smoke.md"
! python3 "$ROOT/bin/raoctl.py" plan --session-id s1 --cwd "$tmp_runtime" docs/teamwork/plans/missing.md >/dev/null 2>&1 \
  || fail "plan command must reject missing plan artifacts"
! python3 "$ROOT/bin/raoctl.py" plan --session-id s1 --cwd "$tmp_runtime" runtime-smoke.md >/dev/null 2>&1 \
  || fail "plan command must reject non docs/teamwork/plans artifacts"
! python3 "$ROOT/bin/raoctl.py" plan --session-id s1 --cwd "$tmp_runtime" "$ROOT/README.md" >/dev/null 2>&1 \
  || fail "plan command must reject project-external artifacts"
! python3 "$ROOT/bin/raoctl.py" plan --session-id s1 --cwd "$tmp_runtime" docs/teamwork/plans/weak.md >/dev/null 2>&1 \
  || fail "plan command must reject weak plan artifacts"
python3 "$ROOT/bin/raoctl.py" plan --session-id s1 --cwd "$tmp_runtime" docs/teamwork/plans/compact-smoke.md >/dev/null \
  || fail "plan command must accept compact execution memo artifacts"
python3 "$ROOT/bin/raoctl.py" plan --session-id s1 --cwd "$tmp_runtime" docs/teamwork/plans/runtime-smoke.md >/dev/null
smoke_sha="$(plan_sha "$tmp_runtime/docs/teamwork/plans/runtime-smoke.md")"
python3 "$ROOT/bin/raoctl.py" status --session-id s1 --cwd "$tmp_runtime" | grep -q '^Active plan artifact: docs/teamwork/plans/runtime-smoke.md$' \
  || fail "status must print active plan artifact"
python3 "$ROOT/bin/raoctl.py" status --session-id s1 --cwd "$tmp_runtime" | grep -Eq '^Active plan artifact SHA-256: [0-9a-f]{64}$' \
  || fail "status must print active plan artifact SHA-256"
hook_json "$tmp_runtime" "not done" | python3 "$ROOT/bin/raoctl.py" hook-stop > "$first_stop"
grep -q '"decision":"block"' "$first_stop" || fail "hook-stop must block incomplete active goals"
grep -q 'teamwork-goal' "$first_stop" || fail "continuation prompt must name teamwork-goal"
grep -q 'docs/teamwork/plans/runtime-smoke.md' "$first_stop" || fail "continuation prompt must include active plan artifact"
python3 "$ROOT/bin/raoctl.py" goal --session-id s1 --max-iterations 3 --completion-promise RAO_GOAL_COMPLETE 'verify hash mismatch stop' --cwd "$tmp_runtime" >/dev/null
python3 "$ROOT/bin/raoctl.py" plan --session-id s1 --cwd "$tmp_runtime" docs/teamwork/plans/runtime-smoke.md >/dev/null
printf '\nchanged\n' >> "$tmp_runtime/docs/teamwork/plans/runtime-smoke.md"
hook_json "$tmp_runtime" "not done" | python3 "$ROOT/bin/raoctl.py" hook-stop > "$hash_mismatch_stop"
[[ ! -s "$hash_mismatch_stop" ]] || fail "hook-stop must not continue after plan hash mismatch"
python3 "$ROOT/bin/raoctl.py" status --session-id s1 --cwd "$tmp_runtime" | grep -q '^Status: stopped$' \
  || fail "hook-stop must mark plan hash mismatch stopped"
write_valid_plan "$tmp_runtime/docs/teamwork/plans/runtime-smoke.md"
smoke_sha="$(plan_sha "$tmp_runtime/docs/teamwork/plans/runtime-smoke.md")"
python3 "$ROOT/bin/raoctl.py" goal --session-id s1 --max-iterations 3 --completion-promise RAO_GOAL_COMPLETE 'verify promise-only block' --cwd "$tmp_runtime" >/dev/null
python3 "$ROOT/bin/raoctl.py" plan --session-id s1 --cwd "$tmp_runtime" docs/teamwork/plans/runtime-smoke.md >/dev/null
hook_json "$tmp_runtime" "<promise>RAO_GOAL_COMPLETE</promise>" | python3 "$ROOT/bin/raoctl.py" hook-stop > "$promise_only_stop"
grep -q '"decision":"block"' "$promise_only_stop" || fail "hook-stop must block completion promise without audit"
python3 "$ROOT/bin/raoctl.py" goal --session-id s1 --max-iterations 3 --completion-promise RAO_GOAL_COMPLETE 'verify missing audit verification block' --cwd "$tmp_runtime" >/dev/null
python3 "$ROOT/bin/raoctl.py" plan --session-id s1 --cwd "$tmp_runtime" docs/teamwork/plans/runtime-smoke.md >/dev/null
hook_json "$tmp_runtime" "<promise>RAO_GOAL_COMPLETE</promise>
$missing_verification_audit" | python3 "$ROOT/bin/raoctl.py" hook-stop > "$missing_verification_stop"
grep -q '"decision":"block"' "$missing_verification_stop" || fail "hook-stop must block audit missing verification evidence"
python3 "$ROOT/bin/raoctl.py" goal --session-id s1 --max-iterations 3 --completion-promise RAO_GOAL_COMPLETE 'verify missing audit requirements block' --cwd "$tmp_runtime" >/dev/null
python3 "$ROOT/bin/raoctl.py" plan --session-id s1 --cwd "$tmp_runtime" docs/teamwork/plans/runtime-smoke.md >/dev/null
hook_json "$tmp_runtime" "<promise>RAO_GOAL_COMPLETE</promise>
$missing_requirements_audit" | python3 "$ROOT/bin/raoctl.py" hook-stop > "$missing_requirements_stop"
grep -q '"decision":"block"' "$missing_requirements_stop" || fail "hook-stop must block audit missing requirements mapping"
python3 "$ROOT/bin/raoctl.py" goal --session-id s1 --max-iterations 3 --completion-promise RAO_GOAL_COMPLETE 'verify missing audit dissent block' --cwd "$tmp_runtime" >/dev/null
python3 "$ROOT/bin/raoctl.py" plan --session-id s1 --cwd "$tmp_runtime" docs/teamwork/plans/runtime-smoke.md >/dev/null
hook_json "$tmp_runtime" "<promise>RAO_GOAL_COMPLETE</promise>
$missing_dissent_audit" | python3 "$ROOT/bin/raoctl.py" hook-stop > "$missing_dissent_stop"
grep -q '"decision":"block"' "$missing_dissent_stop" || fail "hook-stop must block audit missing dissent"
python3 "$ROOT/bin/raoctl.py" goal --session-id s1 --max-iterations 3 --completion-promise RAO_GOAL_COMPLETE 'verify missing audit plan block' --cwd "$tmp_runtime" >/dev/null
python3 "$ROOT/bin/raoctl.py" plan --session-id s1 --cwd "$tmp_runtime" docs/teamwork/plans/runtime-smoke.md >/dev/null
hook_json "$tmp_runtime" "<promise>RAO_GOAL_COMPLETE</promise>
$missing_plan_audit" | python3 "$ROOT/bin/raoctl.py" hook-stop > "$missing_plan_stop"
grep -q '"decision":"block"' "$missing_plan_stop" || fail "hook-stop must block audit missing plan artifact"
python3 "$ROOT/bin/raoctl.py" goal --session-id s1 --max-iterations 3 --completion-promise RAO_GOAL_COMPLETE 'verify missing audit sha block' --cwd "$tmp_runtime" >/dev/null
python3 "$ROOT/bin/raoctl.py" plan --session-id s1 --cwd "$tmp_runtime" docs/teamwork/plans/runtime-smoke.md >/dev/null
hook_json "$tmp_runtime" "<promise>RAO_GOAL_COMPLETE</promise>
$missing_sha_audit" | python3 "$ROOT/bin/raoctl.py" hook-stop > "$missing_sha_stop"
grep -q '"decision":"block"' "$missing_sha_stop" || fail "hook-stop must block audit missing plan artifact SHA"
python3 "$ROOT/bin/raoctl.py" goal --session-id s1 --max-iterations 3 --completion-promise RAO_GOAL_COMPLETE 'verify wrong audit plan block' --cwd "$tmp_runtime" >/dev/null
python3 "$ROOT/bin/raoctl.py" plan --session-id s1 --cwd "$tmp_runtime" docs/teamwork/plans/runtime-smoke.md >/dev/null
hook_json "$tmp_runtime" "<promise>RAO_GOAL_COMPLETE</promise>
$wrong_plan_audit" | python3 "$ROOT/bin/raoctl.py" hook-stop > "$wrong_plan_stop"
grep -q '"decision":"block"' "$wrong_plan_stop" || fail "hook-stop must block audit with wrong plan artifact"
python3 "$ROOT/bin/raoctl.py" goal --session-id s1 --max-iterations 3 --completion-promise RAO_GOAL_COMPLETE 'verify wrong audit sha block' --cwd "$tmp_runtime" >/dev/null
python3 "$ROOT/bin/raoctl.py" plan --session-id s1 --cwd "$tmp_runtime" docs/teamwork/plans/runtime-smoke.md >/dev/null
wrong_sha_audit="$(audit_block 0000000000000000000000000000000000000000000000000000000000000000)"
hook_json "$tmp_runtime" "<promise>RAO_GOAL_COMPLETE</promise>
$wrong_sha_audit" | python3 "$ROOT/bin/raoctl.py" hook-stop > "$wrong_sha_stop"
grep -q '"decision":"block"' "$wrong_sha_stop" || fail "hook-stop must block audit with wrong plan artifact SHA"
python3 "$ROOT/bin/raoctl.py" goal --session-id s1 --max-iterations 3 --completion-promise RAO_GOAL_COMPLETE 'verify invalid review block' --cwd "$tmp_runtime" >/dev/null
python3 "$ROOT/bin/raoctl.py" plan --session-id s1 --cwd "$tmp_runtime" docs/teamwork/plans/runtime-smoke.md >/dev/null
hook_json "$tmp_runtime" "<promise>RAO_GOAL_COMPLETE</promise>
$invalid_review_audit" | python3 "$ROOT/bin/raoctl.py" hook-stop > "$invalid_review_stop"
grep -q '"decision":"block"' "$invalid_review_stop" || fail "hook-stop must block audit without passing review verdict"
python3 "$ROOT/bin/raoctl.py" goal --session-id s1 --max-iterations 3 --completion-promise RAO_GOAL_COMPLETE 'verify uppercase review block' --cwd "$tmp_runtime" >/dev/null
python3 "$ROOT/bin/raoctl.py" plan --session-id s1 --cwd "$tmp_runtime" docs/teamwork/plans/runtime-smoke.md >/dev/null
hook_json "$tmp_runtime" "<promise>RAO_GOAL_COMPLETE</promise>
$uppercase_review_audit" | python3 "$ROOT/bin/raoctl.py" hook-stop > "$uppercase_review_stop"
grep -q '"decision":"block"' "$uppercase_review_stop" || fail "hook-stop must require exact lowercase review verdict"
python3 "$ROOT/bin/raoctl.py" goal --session-id s1 --max-iterations 3 --completion-promise RAO_GOAL_COMPLETE 'verify missing checkpoint block' --cwd "$tmp_runtime" >/dev/null
python3 "$ROOT/bin/raoctl.py" plan --session-id s1 --cwd "$tmp_runtime" docs/teamwork/plans/runtime-smoke.md >/dev/null
valid_audit="$(audit_block "$smoke_sha")"
hook_json "$tmp_runtime" "<promise>RAO_GOAL_COMPLETE</promise>
$valid_audit" | python3 "$ROOT/bin/raoctl.py" hook-stop > "$missing_checkpoint_stop"
grep -q '"decision":"block"' "$missing_checkpoint_stop" || fail "hook-stop must block audited completion without checkpoint"
python3 "$ROOT/bin/raoctl.py" goal --session-id s1 --max-iterations 3 --completion-promise RAO_GOAL_COMPLETE 'verify verification fail block' --cwd "$tmp_runtime" >/dev/null
python3 "$ROOT/bin/raoctl.py" plan --session-id s1 --cwd "$tmp_runtime" docs/teamwork/plans/runtime-smoke.md >/dev/null
record_checkpoint "$tmp_runtime" pass pass fail progress
hook_json "$tmp_runtime" "<promise>RAO_GOAL_COMPLETE</promise>
$valid_audit" | python3 "$ROOT/bin/raoctl.py" hook-stop > "$verification_fail_stop"
grep -q '"decision":"block"' "$verification_fail_stop" || fail "hook-stop must block checkpoint with failed verification"
python3 "$ROOT/bin/raoctl.py" goal --session-id s1 --max-iterations 3 --completion-promise RAO_GOAL_COMPLETE 'verify review revise block' --cwd "$tmp_runtime" >/dev/null
python3 "$ROOT/bin/raoctl.py" plan --session-id s1 --cwd "$tmp_runtime" docs/teamwork/plans/runtime-smoke.md >/dev/null
record_checkpoint "$tmp_runtime" revise pass pass progress
revise_audit="$(audit_block "$smoke_sha" revise pass)"
hook_json "$tmp_runtime" "<promise>RAO_GOAL_COMPLETE</promise>
$revise_audit" | python3 "$ROOT/bin/raoctl.py" hook-stop > "$review_revise_stop"
grep -q '"decision":"block"' "$review_revise_stop" || fail "hook-stop must block checkpoint with revise review verdict"
python3 "$ROOT/bin/raoctl.py" goal --session-id s1 --max-iterations 3 --completion-promise RAO_GOAL_COMPLETE 'verify audited completion' --cwd "$tmp_runtime" >/dev/null
python3 "$ROOT/bin/raoctl.py" plan --session-id s1 --cwd "$tmp_runtime" docs/teamwork/plans/runtime-smoke.md >/dev/null
python3 "$ROOT/bin/raoctl.py" checkpoint-raw --session-id s1 --cwd "$tmp_runtime" >/dev/null <<'CHECKPOINT_RAW_ARGS'
--plan-review-verdict pass --execution-review-verdict pass --verification-command "runtime smoke command && echo ok" --verification-result pass --evidence-delta progress
CHECKPOINT_RAW_ARGS
python3 "$ROOT/bin/raoctl.py" status --session-id s1 --cwd "$tmp_runtime" | grep -q '^Verification command: runtime smoke command && echo ok$' \
  || fail "checkpoint-raw must preserve shell-like verification command text"
hook_json "$tmp_runtime" "<promise>RAO_GOAL_COMPLETE</promise>
$valid_audit" | python3 "$ROOT/bin/raoctl.py" hook-stop > "$complete_stop"
[[ ! -s "$complete_stop" ]] || fail "hook-stop must allow audited completion promise to stop"
python3 "$ROOT/bin/raoctl.py" status --session-id s1 --cwd "$tmp_runtime" | grep -q '^Status: complete$' \
  || fail "hook-stop must mark audited completion complete"
python3 "$ROOT/bin/raoctl.py" goal --session-id s1 --max-iterations 3 --completion-promise RAO_GOAL_COMPLETE 'verify pass-with-notes audited completion' --cwd "$tmp_runtime" >/dev/null
python3 "$ROOT/bin/raoctl.py" plan --session-id s1 --cwd "$tmp_runtime" docs/teamwork/plans/runtime-smoke.md >/dev/null
record_checkpoint "$tmp_runtime" pass-with-notes pass-with-notes pass progress
pass_with_notes_audit="$(audit_block "$smoke_sha" pass-with-notes pass-with-notes)"
hook_json "$tmp_runtime" "<promise>RAO_GOAL_COMPLETE</promise>
$pass_with_notes_audit" | python3 "$ROOT/bin/raoctl.py" hook-stop > "$pass_with_notes_stop"
[[ ! -s "$pass_with_notes_stop" ]] || fail "hook-stop must allow pass-with-notes audited completion"
python3 "$ROOT/bin/raoctl.py" goal --session-id s1 --max-iterations 3 --completion-promise RAO_GOAL_COMPLETE 'verify no progress stop' --cwd "$tmp_runtime" >/dev/null
python3 "$ROOT/bin/raoctl.py" plan --session-id s1 --cwd "$tmp_runtime" docs/teamwork/plans/runtime-smoke.md >/dev/null
record_checkpoint "$tmp_runtime" pass pass pass no-progress
python3 "$ROOT/bin/raoctl.py" checkpoint --session-id s1 --cwd "$tmp_runtime" \
  --plan-review-verdict pass \
  --execution-review-verdict pass \
  --verification-command "runtime smoke command" \
  --verification-result pass \
  --evidence-delta no-progress > "$no_progress_stop"
grep -q 'Goal stopped after 2 consecutive no-progress checkpoints' "$no_progress_stop" \
  || fail "checkpoint must report no-progress stop"
python3 "$ROOT/bin/raoctl.py" status --session-id s1 --cwd "$tmp_runtime" | grep -q '^Status: stopped$' \
  || fail "checkpoint must mark no-progress stop stopped"
python3 "$ROOT/bin/raoctl.py" goal --session-id s1 --max-iterations 3 --completion-promise RAO_GOAL_COMPLETE 'verify manual override status' --cwd "$tmp_runtime" >/dev/null
python3 "$ROOT/bin/raoctl.py" complete --session-id s1 --cwd "$tmp_runtime" >/dev/null
python3 "$ROOT/bin/raoctl.py" status --session-id s1 --cwd "$tmp_runtime" | grep -q '^Manual completion: not automatically verified$' \
  || fail "status must show manual completion is not automatically verified"
python3 "$ROOT/bin/raoctl.py" goal --session-id s1 --max-iterations 1 --completion-promise RAO_GOAL_COMPLETE 'verify max iteration stop' --cwd "$tmp_runtime" >/dev/null
python3 "$ROOT/bin/raoctl.py" plan --session-id s1 --cwd "$tmp_runtime" docs/teamwork/plans/runtime-smoke.md >/dev/null
hook_json "$tmp_runtime" "still not done" | python3 "$ROOT/bin/raoctl.py" hook-stop > "$max_stop"
[[ ! -s "$max_stop" ]] || fail "hook-stop must allow stop at max iterations"
python3 "$ROOT/bin/raoctl.py" status --session-id s1 --cwd "$tmp_runtime" | grep -q '^Status: stopped$' \
  || fail "hook-stop must mark max-iteration stop stopped"
rm -rf "$tmp_runtime"

tmp_legacy="$(mktemp -d)"
mkdir -p "$tmp_legacy/.claude/run-analyze-optimize-goals"
python3 - "$tmp_legacy/.claude/run-analyze-optimize-goals/s1.goal.md" <<'PY'
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
path.write_text("""---
status: "active"
session_id: "s1"
objective: "verify legacy state migration"
iteration: 1
max_iterations: 2
completion_promise: "RAO_GOAL_COMPLETE"
created_at: "2026-05-13T00:00:00Z"
last_hook_event: "goal_created"
---

# Objective

verify legacy state migration

# Notes

# Iteration Log

- 2026-05-13T00:00:00Z: Legacy goal created.
""", encoding="utf-8")
PY
hook_json "$tmp_legacy" "legacy not done" | python3 "$ROOT/bin/raoctl.py" hook-stop > "$tmp_legacy/legacy-stop.json"
grep -q '"decision":"block"' "$tmp_legacy/legacy-stop.json" || fail "hook-stop must block migrated legacy active goals"
[[ -f "$tmp_legacy/.claude/teamwork-goals/s1.goal.md" ]] || fail "legacy state must migrate to .claude/teamwork-goals"
[[ ! -e "$tmp_legacy/.claude/run-analyze-optimize-goals/s1.goal.md" ]] || fail "legacy state file must be removed after migration"
rm -rf "$tmp_legacy"

for skill in "${SKILLS[@]}"; do
  grep -q "$skill" "$ROOT/.cursor/rules/teamwork.mdc" || fail "Cursor rule does not mention $skill"
  grep -q "$skill" "$ROOT/install.sh" || fail "install.sh does not install $skill"
  grep -q "$skill" "$ROOT/README.md" || fail "README.md does not mention $skill"
done

for retired in "${RETIRED_SKILLS[@]}"; do
  ! grep -q "$retired" "$ROOT/.cursor/rules/teamwork.mdc" || fail "Cursor rule mentions retired skill $retired"
  ! grep -q "$retired" "$ROOT/README.md" || fail "README.md mentions retired skill $retired"
done

cursor_lines="$(wc -l < "$ROOT/.cursor/rules/teamwork.mdc")"
[[ "$cursor_lines" -le 120 ]] || fail "Cursor rule is too long to be a thin summary"
readme_lines="$(wc -l < "$ROOT/README.md")"
[[ "$readme_lines" -le 180 ]] || fail "README is too long to remain an entrypoint summary"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

HOME="$tmp/claude-home" "$ROOT/install.sh" claude >/dev/null
HOME="$tmp/codex-home" "$ROOT/install.sh" codex >/dev/null
mkdir -p "$tmp/cursor-project"
mkdir -p "$tmp/cursor-project/.cursor/rules"
ln -sf "$ROOT/.cursor/rules/run-analyze-optimize.mdc" "$tmp/cursor-project/.cursor/rules/run-analyze-optimize.mdc"
HOME="$tmp/cursor-home" "$ROOT/install.sh" cursor "$tmp/cursor-project" >/dev/null

for skill in "${SKILLS[@]}"; do
  [[ -f "$tmp/claude-home/.claude/skills/$skill/SKILL.md" && \
     ! -L "$tmp/claude-home/.claude/skills/$skill/SKILL.md" ]] \
    || fail "Claude default install must copy $skill"
  [[ -f "$tmp/codex-home/.codex/skills/$skill/SKILL.md" && \
     ! -L "$tmp/codex-home/.codex/skills/$skill/SKILL.md" ]] \
    || fail "Codex default install must copy $skill"
  grep -q "^name: $skill$" "$tmp/claude-home/.claude/skills/$skill/SKILL.md" \
    || fail "Claude copied skill has wrong name: $skill"
  grep -q "^name: $skill$" "$tmp/codex-home/.codex/skills/$skill/SKILL.md" \
    || fail "Codex copied skill has wrong name: $skill"
done
[[ -f "$tmp/cursor-project/.cursor/rules/teamwork.mdc" && \
   ! -L "$tmp/cursor-project/.cursor/rules/teamwork.mdc" ]] \
  || fail "Cursor default install must copy rule"
[[ ! -e "$tmp/cursor-project/.cursor/rules/run-analyze-optimize.mdc" && \
   ! -L "$tmp/cursor-project/.cursor/rules/run-analyze-optimize.mdc" ]] \
  || fail "Cursor install did not clean retired rule symlink"

HOME="$tmp/link-home" "$ROOT/install.sh" --link codex >/dev/null
for skill in "${SKILLS[@]}"; do
  [[ -L "$tmp/link-home/.codex/skills/$skill/SKILL.md" ]] \
    || fail "--link install must symlink $skill"
done

for retired in "${RETIRED_SKILLS[@]}"; do
  mkdir -p "$tmp/migration-home/.codex/skills/$retired"
  ln -sf "$ROOT/skills/$retired/SKILL.md" "$tmp/migration-home/.codex/skills/$retired/SKILL.md"
done
HOME="$tmp/migration-home" "$ROOT/install.sh" codex >/dev/null
for retired in "${RETIRED_SKILLS[@]}"; do
  [[ ! -e "$tmp/migration-home/.codex/skills/$retired/SKILL.md" && \
     ! -L "$tmp/migration-home/.codex/skills/$retired/SKILL.md" ]] \
    || fail "install did not clean retired symlink: $retired"
done

for retired in "${RETIRED_SKILLS[@]}"; do
  mkdir -p "$tmp/copy-migration-home/.codex/skills/$retired"
  printf -- "---\nname: %s\ndescription: Use when retired.\n---\n" "$retired" \
    > "$tmp/copy-migration-home/.codex/skills/$retired/SKILL.md"
done
HOME="$tmp/copy-migration-home" "$ROOT/install.sh" codex >/dev/null
for retired in "${RETIRED_SKILLS[@]}"; do
  [[ ! -e "$tmp/copy-migration-home/.codex/skills/$retired/SKILL.md" && \
     ! -L "$tmp/copy-migration-home/.codex/skills/$retired/SKILL.md" ]] \
    || fail "install did not clean retired copied skill: $retired"
done

echo "OK: Teamwork skill package validates"
