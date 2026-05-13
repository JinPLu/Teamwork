#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROUTER="$ROOT/skills/teamwork/SKILL.md"
SKILLS=(
  using-teamwork
  teamwork
  teamwork-design
  teamwork-execute
  teamwork-review
)
RETIRED_SKILLS=(
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

for subskill in teamwork-design teamwork-execute teamwork-review; do
  grep -q "skills/$subskill/SKILL.md" "$ROUTER" || fail "router does not reference skills/$subskill/SKILL.md"
done

grep -q 'mode: goal' "$ROUTER" || fail "router must own mode: goal"
grep -q 'mode: research' "$ROOT/skills/teamwork-design/SKILL.md" || fail "design skill missing mode: research"
grep -q 'mode: plan' "$ROOT/skills/teamwork-design/SKILL.md" || fail "design skill missing mode: plan"
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
    "./skills/teamwork-design",
    "./skills/teamwork-execute",
    "./skills/teamwork-review",
]
retired = {
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
[[ -d "$ROOT/commands/rao" ]] || fail "missing /rao command directory"
for command in goal status pause resume stop complete clear note help; do
  [[ -f "$ROOT/commands/rao/$command.md" ]] || fail "missing /rao:$command command"
done
grep -q 'hook-stop' "$ROOT/hooks/hooks.json" || fail "hooks must include Stop continuation"
grep -q 'raoctl.py' "$ROOT/hooks/hooks.json" || fail "hooks must invoke raoctl.py"
grep -q '/rao:goal' "$ROOT/README.md" || fail "README must document /rao:goal"
grep -q 'Stop hook' "$ROOT/README.md" || fail "README must document Stop hook behavior"
grep -q '.claude/teamwork-goals' "$ROOT/README.md" || fail "README must document goal state path"
grep -q 'RAO_GOAL_COMPLETE' "$ROOT/README.md" || fail "README must document completion promise"
grep -q 'Codex Native Integration' "$ROUTER" || fail "router must document Codex native integration"
grep -q 'native Codex goals' "$ROOT/CODEX.md" || fail "CODEX.md must document native Codex goals"
grep -q 'Codex Runtime Mapping' "$ROOT/CODEX.md" || fail "CODEX.md must document Codex runtime mapping"
grep -q 'Codex runtime' "$ROOT/README.md" || fail "README must document Codex runtime"
grep -q 'durable Markdown plan artifact' "$ROUTER" || fail "router must define durable Markdown plan artifacts"
grep -q 'transient UI-only checklist' "$ROUTER" || fail "router must mark update_plan as transient UI-only"
grep -q 'Teamwork planning pass must create or update one before execution' "$ROUTER" \
  || fail "router must require all plans to be durable artifacts"
grep -q 'docs/teamwork/plans/YYYY-MM-DD-<slug>.md' "$ROOT/skills/teamwork-design/SKILL.md" \
  || fail "design skill must define the durable plan path"
grep -q 'All plans must be written to a durable Markdown plan artifact' "$ROOT/skills/teamwork-design/SKILL.md" \
  || fail "design skill must require all plans to be durable artifacts"
! grep -q 'chat-visible plan is enough' "$ROOT/skills/teamwork-design/SKILL.md" \
  || fail "design skill must not allow chat-only lightweight plans"
grep -q 'Requirements Mapping' "$ROOT/skills/teamwork-design/SKILL.md" \
  || fail "design skill must require requirements mapping in plan artifacts"
grep -q 'Expected Results' "$ROOT/skills/teamwork-design/SKILL.md" \
  || fail "design skill must require expected verification results"
grep -q 'must return `revise` or `blocked`' "$ROOT/skills/teamwork-review/SKILL.md" \
  || fail "review skill must hard-fail missing or weak plan artifacts"
grep -q 'every plan has a Markdown plan artifact path' "$ROOT/skills/teamwork-review/SKILL.md" \
  || fail "review skill must require artifacts for every plan"
grep -q 'requirements-to-evidence mapping' "$ROOT/skills/teamwork-review/SKILL.md" \
  || fail "review skill must check requirements-to-evidence mapping"
grep -q 'docs/teamwork/plans/YYYY-MM-DD-<slug>.md' "$ROOT/README.md" \
  || fail "README must document durable plan artifact path"
grep -q 'durable Markdown plan artifacts' "$ROOT/CODEX.md" \
  || fail "CODEX.md must document durable Markdown plan artifacts"
grep -q 'For every Teamwork planning pass' "$ROOT/CODEX.md" \
  || fail "CODEX.md must require all plans to be durable artifacts"
grep -q 'It is not Codex' "$ROOT/CODEX.md" \
  || fail "CODEX.md must distinguish plan artifacts from Codex goal state"
grep -q 'goal state and not Claude `.claude/teamwork-goals/` runtime state' "$ROOT/CODEX.md" \
  || fail "CODEX.md must distinguish plan artifacts from Claude goal runtime"
grep -q 'codex review' "$ROOT/skills/teamwork-review/SKILL.md" || fail "review skill must mention codex review"
grep -q 'sandbox' "$ROOT/skills/teamwork-execute/SKILL.md" || fail "execute skill must document sandbox approvals"
grep -q 'Subagent Routing Policy' "$ROUTER" || fail "router must define subagent routing policy"
grep -q 'Designer' "$ROUTER" || fail "router must define Designer subagent role"
grep -q 'model tier' "$ROUTER" || fail "router must document model tier routing"
grep -q '`fast`' "$ROUTER" || fail "router must document fast routing tier"
grep -q '`standard`' "$ROUTER" || fail "router must document standard routing tier"
grep -q 'high reasoning' "$ROUTER" || fail "router must document high reasoning routing tier"
grep -q 'Subagent Routing' "$ROOT/skills/teamwork-design/SKILL.md" || fail "design skill must document subagent routing"
grep -q 'model tier' "$ROOT/skills/teamwork-design/SKILL.md" || fail "design skill must require model tier in subagent routing"
grep -q 'Workers execute the accepted plan' "$ROOT/skills/teamwork-execute/SKILL.md" \
  || fail "execute skill must keep Worker execution boundary"
grep -q 'do not reopen product behavior' "$ROOT/skills/teamwork-execute/SKILL.md" \
  || fail "execute skill must block design reopening during execution"
grep -q 'Routing conformance' "$ROOT/skills/teamwork-review/SKILL.md" \
  || fail "review skill must check routing conformance"
grep -q 'underpowered tier' "$ROOT/skills/teamwork-review/SKILL.md" \
  || fail "review skill must block underpowered high-risk routing"
grep -q 'review_verdict: <pass | pass-with-notes>' "$ROUTER" \
  || fail "goal completion audit must only allow passing review verdicts"
! grep -q 'review_verdict: <pass | pass-with-notes | revise | blocked>' "$ROUTER" \
  || fail "goal completion audit must not list non-passing review verdicts"
grep -q 'MCP' "$ROOT/CODEX.md" || fail "CODEX.md must document MCP/network fallback"
grep -q 'Evidence Interpretation Contract' "$ROUTER" || fail "router must define evidence interpretation contract"
grep -q 'Evidence Interpretation Contract' "$ROOT/skills/teamwork-design/SKILL.md" || fail "design skill must define evidence interpretation contract"
grep -q 'Context & Cost Discipline' "$ROUTER" || fail "router must define context and cost discipline"
grep -q 'Context & Cost Discipline' "$ROOT/skills/teamwork-design/SKILL.md" || fail "design skill must define context and cost discipline"
grep -q 'Subagent Collaboration Model' "$ROUTER" || fail "router must define subagent collaboration model"
for term in observed inferred claimed; do
  grep -q "$term" "$ROUTER" || fail "router must mention $term evidence"
  grep -q "$term" "$ROOT/skills/teamwork-design/SKILL.md" || fail "design skill must mention $term evidence"
  grep -q "$term" "$ROOT/skills/teamwork-review/SKILL.md" || fail "review skill must mention $term evidence"
done
grep -q 'at most 3 parallel' "$ROUTER" || fail "router must limit default parallel subagents"
grep -q '<completion_audit>' "$ROUTER" || fail "router must document completion audit format"
grep -q '<completion_audit>' "$ROOT/README.md" || fail "README must document completion audit format"
grep -q 'completion_audit_detected' "$ROOT/bin/raoctl.py" || fail "runtime must gate completion on audit detection"
grep -q 'PASSING_REVIEW_VERDICTS' "$ROOT/bin/raoctl.py" || fail "runtime must parse passing review verdicts"
grep -q 'manual /rao:complete override' "$ROOT/bin/raoctl.py" || fail "runtime must mark manual completion override"
grep -q 'Narrative-mislead risk' "$ROOT/skills/teamwork-review/SKILL.md" || fail "review skill must check narrative-mislead risk"
grep -q 'Treat executor summaries' "$ROOT/skills/teamwork-review/SKILL.md" || fail "review skill must treat summaries as evidence only"

tmp_runtime="$(mktemp -d)"
first_stop="$tmp_runtime/first-stop.json"
promise_only_stop="$tmp_runtime/promise-only-stop.json"
missing_requirements_stop="$tmp_runtime/missing-requirements-stop.json"
missing_verification_stop="$tmp_runtime/missing-verification-stop.json"
missing_dissent_stop="$tmp_runtime/missing-dissent-stop.json"
invalid_review_stop="$tmp_runtime/invalid-review-stop.json"
uppercase_review_stop="$tmp_runtime/uppercase-review-stop.json"
complete_stop="$tmp_runtime/complete-stop.json"
pass_with_notes_stop="$tmp_runtime/pass-with-notes-stop.json"
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
valid_audit='<completion_audit>
<requirements_mapping>objective mapped to focused validation evidence</requirements_mapping>
<verification_evidence>focused smoke command passed</verification_evidence>
<review_verdict>pass</review_verdict>
<dissent>none</dissent>
</completion_audit>'
missing_verification_audit='<completion_audit>
<requirements_mapping>objective mapped to focused validation evidence</requirements_mapping>
<review_verdict>pass</review_verdict>
<dissent>none</dissent>
</completion_audit>'
missing_requirements_audit='<completion_audit>
<verification_evidence>focused smoke command passed</verification_evidence>
<review_verdict>pass</review_verdict>
<dissent>none</dissent>
</completion_audit>'
missing_dissent_audit='<completion_audit>
<requirements_mapping>objective mapped to focused validation evidence</requirements_mapping>
<verification_evidence>focused smoke command passed</verification_evidence>
<review_verdict>pass</review_verdict>
</completion_audit>'
invalid_review_audit='<completion_audit>
<requirements_mapping>objective mapped to focused validation evidence</requirements_mapping>
<verification_evidence>focused smoke command passed</verification_evidence>
<review_verdict>revise</review_verdict>
<dissent>none</dissent>
</completion_audit>'
uppercase_review_audit='<completion_audit>
<requirements_mapping>objective mapped to focused validation evidence</requirements_mapping>
<verification_evidence>focused smoke command passed</verification_evidence>
<review_verdict>PASS</review_verdict>
<dissent>none</dissent>
</completion_audit>'
pass_with_notes_audit='<completion_audit>
<requirements_mapping>objective mapped to focused validation evidence</requirements_mapping>
<verification_evidence>focused smoke command passed</verification_evidence>
<review_verdict>pass-with-notes</review_verdict>
<dissent>residual risk noted</dissent>
</completion_audit>'
python3 "$ROOT/bin/raoctl.py" goal --session-id s1 --max-iterations 2 --completion-promise RAO_GOAL_COMPLETE 'verify runtime continuation' --cwd "$tmp_runtime" >/dev/null
hook_json "$tmp_runtime" "not done" | python3 "$ROOT/bin/raoctl.py" hook-stop > "$first_stop"
grep -q '"decision":"block"' "$first_stop" || fail "hook-stop must block incomplete active goals"
python3 "$ROOT/bin/raoctl.py" goal --session-id s1 --max-iterations 3 --completion-promise RAO_GOAL_COMPLETE 'verify promise-only block' --cwd "$tmp_runtime" >/dev/null
hook_json "$tmp_runtime" "<promise>RAO_GOAL_COMPLETE</promise>" | python3 "$ROOT/bin/raoctl.py" hook-stop > "$promise_only_stop"
grep -q '"decision":"block"' "$promise_only_stop" || fail "hook-stop must block completion promise without audit"
python3 "$ROOT/bin/raoctl.py" goal --session-id s1 --max-iterations 3 --completion-promise RAO_GOAL_COMPLETE 'verify missing audit verification block' --cwd "$tmp_runtime" >/dev/null
hook_json "$tmp_runtime" "<promise>RAO_GOAL_COMPLETE</promise>
$missing_verification_audit" | python3 "$ROOT/bin/raoctl.py" hook-stop > "$missing_verification_stop"
grep -q '"decision":"block"' "$missing_verification_stop" || fail "hook-stop must block audit missing verification evidence"
python3 "$ROOT/bin/raoctl.py" goal --session-id s1 --max-iterations 3 --completion-promise RAO_GOAL_COMPLETE 'verify missing audit requirements block' --cwd "$tmp_runtime" >/dev/null
hook_json "$tmp_runtime" "<promise>RAO_GOAL_COMPLETE</promise>
$missing_requirements_audit" | python3 "$ROOT/bin/raoctl.py" hook-stop > "$missing_requirements_stop"
grep -q '"decision":"block"' "$missing_requirements_stop" || fail "hook-stop must block audit missing requirements mapping"
python3 "$ROOT/bin/raoctl.py" goal --session-id s1 --max-iterations 3 --completion-promise RAO_GOAL_COMPLETE 'verify missing audit dissent block' --cwd "$tmp_runtime" >/dev/null
hook_json "$tmp_runtime" "<promise>RAO_GOAL_COMPLETE</promise>
$missing_dissent_audit" | python3 "$ROOT/bin/raoctl.py" hook-stop > "$missing_dissent_stop"
grep -q '"decision":"block"' "$missing_dissent_stop" || fail "hook-stop must block audit missing dissent"
python3 "$ROOT/bin/raoctl.py" goal --session-id s1 --max-iterations 3 --completion-promise RAO_GOAL_COMPLETE 'verify invalid review block' --cwd "$tmp_runtime" >/dev/null
hook_json "$tmp_runtime" "<promise>RAO_GOAL_COMPLETE</promise>
$invalid_review_audit" | python3 "$ROOT/bin/raoctl.py" hook-stop > "$invalid_review_stop"
grep -q '"decision":"block"' "$invalid_review_stop" || fail "hook-stop must block audit without passing review verdict"
python3 "$ROOT/bin/raoctl.py" goal --session-id s1 --max-iterations 3 --completion-promise RAO_GOAL_COMPLETE 'verify uppercase review block' --cwd "$tmp_runtime" >/dev/null
hook_json "$tmp_runtime" "<promise>RAO_GOAL_COMPLETE</promise>
$uppercase_review_audit" | python3 "$ROOT/bin/raoctl.py" hook-stop > "$uppercase_review_stop"
grep -q '"decision":"block"' "$uppercase_review_stop" || fail "hook-stop must require exact lowercase review verdict"
python3 "$ROOT/bin/raoctl.py" goal --session-id s1 --max-iterations 3 --completion-promise RAO_GOAL_COMPLETE 'verify audited completion' --cwd "$tmp_runtime" >/dev/null
hook_json "$tmp_runtime" "<promise>RAO_GOAL_COMPLETE</promise>
$valid_audit" | python3 "$ROOT/bin/raoctl.py" hook-stop > "$complete_stop"
[[ ! -s "$complete_stop" ]] || fail "hook-stop must allow audited completion promise to stop"
python3 "$ROOT/bin/raoctl.py" status --session-id s1 --cwd "$tmp_runtime" | grep -q '^Status: complete$' \
  || fail "hook-stop must mark audited completion complete"
python3 "$ROOT/bin/raoctl.py" goal --session-id s1 --max-iterations 3 --completion-promise RAO_GOAL_COMPLETE 'verify pass-with-notes audited completion' --cwd "$tmp_runtime" >/dev/null
hook_json "$tmp_runtime" "<promise>RAO_GOAL_COMPLETE</promise>
$pass_with_notes_audit" | python3 "$ROOT/bin/raoctl.py" hook-stop > "$pass_with_notes_stop"
[[ ! -s "$pass_with_notes_stop" ]] || fail "hook-stop must allow pass-with-notes audited completion"
python3 "$ROOT/bin/raoctl.py" goal --session-id s1 --max-iterations 1 --completion-promise RAO_GOAL_COMPLETE 'verify max iteration stop' --cwd "$tmp_runtime" >/dev/null
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
