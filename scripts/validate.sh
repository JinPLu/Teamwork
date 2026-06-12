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

if git -C "$ROOT" ls-files 'docs/teamwork/plans/*' 'docs/teamwork/research/*' 'docs/teamwork/reports/*' 'docs/teamwork/workflows/*' | grep -q .; then
  fail "local workflow artifacts under docs/teamwork/{plans,research,reports,workflows}/ must not be tracked"
fi
grep_required '^docs/teamwork/plans/$' "$ROOT/.gitignore" ".gitignore must ignore local Teamwork plan artifacts"
grep_required '^docs/teamwork/research/$' "$ROOT/.gitignore" ".gitignore must ignore local Teamwork research artifacts"
grep_required '^docs/teamwork/reports/$' "$ROOT/.gitignore" ".gitignore must ignore local Teamwork report artifacts"
grep_required '^docs/teamwork/workflows/$' "$ROOT/.gitignore" ".gitignore must ignore local Teamwork workflow artifacts"

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

for reference in artifact-protocol goal-iteration dispatch-policy platform-dispatch-mapping workflow-orchestration subagent-prompt-contract subagent-packets subagent-routing workflow-contract codex-deep-collaboration plan-output review-checks project-init teamwork-index research-protocol role-workflows optional-skills designer-judge-workflow worker-workflow reviewer-workflow; do
  ref_file="$ROOT/skills/using-teamwork/references/$reference.md"
  [[ -f "$ref_file" ]] || fail "missing skills/using-teamwork/references/$reference.md"
  git_known_or_worktree_addition "skills/using-teamwork/references/$reference.md" \
    || fail "skills/using-teamwork/references/$reference.md is neither tracked nor a worktree addition"
done

for template in teamwork-index-template.json teamwork-index-readme-template.md teamwork-current-template.md; do
  template_file="$ROOT/skills/using-teamwork/references/$template"
  [[ -f "$template_file" ]] || fail "missing skills/using-teamwork/references/$template"
  git_known_or_worktree_addition "skills/using-teamwork/references/$template" \
    || fail "skills/using-teamwork/references/$template is neither tracked nor a worktree addition"
done

expected_reference_inventory="$(
  printf '%s\n' \
    artifact-protocol.md codex-deep-collaboration.md designer-judge-workflow.md \
    dispatch-policy.md goal-iteration.md optional-skills.md plan-output.md \
    platform-dispatch-mapping.md project-init.md research-protocol.md \
    reviewer-workflow.md review-checks.md role-workflows.md subagent-packets.md \
    subagent-prompt-contract.md subagent-routing.md teamwork-current-template.md \
    teamwork-index-readme-template.md teamwork-index-template.json \
    teamwork-index.md worker-workflow.md workflow-contract.md \
    workflow-orchestration.md | sort
)"
actual_reference_inventory="$(
  find "$ROOT/skills/using-teamwork/references" -maxdepth 1 -type f \
    -exec basename {} \; | sort
)"
[[ "$actual_reference_inventory" == "$expected_reference_inventory" ]] \
  || fail "using-teamwork references inventory drifted"

[[ -f "$ROOT/scripts/validate_teamwork_index.py" ]] || fail "missing scripts/validate_teamwork_index.py"
git_known_or_worktree_addition "scripts/validate_teamwork_index.py" \
  || fail "scripts/validate_teamwork_index.py is neither tracked nor a worktree addition"
python3 "$ROOT/scripts/validate_teamwork_index.py" \
  "$ROOT/skills/using-teamwork/references/teamwork-index-template.json" >/dev/null

grep_required 'Optional durable-memory fields' "$ROOT/skills/using-teamwork/references/subagent-packets.md" \
  "subagent-packets must keep Memory Delta as optional durable-memory output"
grep_required 'Memory Delta Candidate' "$ROOT/skills/using-teamwork/references/subagent-packets.md" \
  "subagent-packets must document optional Memory Delta Candidate"
grep_required 'Durable memory check' "$ROOT/skills/using-teamwork/references/review-checks.md" \
  "review-checks must include durable memory materiality checks"
grep_required 'Memory promotion check' "$ROOT/skills/using-teamwork/references/review-checks.md" \
  "review-checks must include memory promotion checks"
grep_required 'candidate memory' "$ROOT/skills/using-teamwork/references/review-checks.md" \
  "review-checks must keep external memory candidate-scoped"
grep_required 'Manual smoke evidence captures source' "$ROOT/skills/using-teamwork/references/review-checks.md" \
  "review-checks must include manual smoke evidence capture fields"
grep_required 'When delegated work may change durable project memory' "$ROOT/skills/using-teamwork/references/subagent-prompt-contract.md" \
  "subagent prompt contract must make Memory Delta Candidate conditional"
grep_required 'Lifecycle And Closure' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy must document subagent lifecycle closure"
grep_required 'Closure Instruction' "$ROOT/skills/using-teamwork/references/subagent-prompt-contract.md" \
  "subagent prompt contract must require explicit closure instructions"
grep_required 'Closure Evidence' "$ROOT/skills/using-teamwork/references/subagent-packets.md" \
  "subagent packets must record dispatch closure evidence"
grep_required 'delegated track may remain open' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy must prohibit open delegated tracks before final response"
grep_required 'Subagents are bounded tasks: return the required packet once, then stop' "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
  "workflow contract must define bounded subagent lifecycle"
grep_required '`abandoned-after-discovery`' "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
  "workflow contract must use canonical abandoned-after-discovery status"
grep_required 'dispatched -> returned ->' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy must define dispatch status transitions"
grep_required '`done_with_concerns`' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy must include all Worker terminal statuses"
grep_required 'Final status cannot remain `dispatched` or' "$ROOT/skills/using-teamwork/references/subagent-packets.md" \
  "subagent packets must forbid dispatched final dispatch status"
grep_required '`returned`.' "$ROOT/skills/using-teamwork/references/subagent-packets.md" \
  "subagent packets must forbid returned final dispatch status"
grep_required 'Protected Data Status' "$ROOT/skills/using-teamwork/references/subagent-packets.md" \
  "subagent packets must expose protected-data status for memory candidates"
grep_required 'Subagents propose memory candidates only' "$ROOT/skills/using-teamwork/references/subagent-packets.md" \
  "subagent packets must prevent subagents from promoting memory"
grep_required 'final status, closure evidence' "$ROOT/skills/using-teamwork/references/plan-output.md" \
  "plan output must include dispatch closure evidence"
grep_required 'No delegated track remains `dispatched` or `returned`' "$ROOT/skills/using-teamwork/references/review-checks.md" \
  "review checks must reject open delegated tracks"
grep_required 'closed dispatch log or continuity' "$ROOT/skills/teamwork-research/SKILL.md" \
  "research handoff must close delegated tracks"
grep_required 'Closure Evidence after integration' "$ROOT/skills/teamwork-execute/SKILL.md" \
  "execute skill must close Worker tracks after integration"
grep_required 'Reject open delegated tracks' "$ROOT/skills/teamwork-review/SKILL.md" \
  "review skill must reject open delegated tracks"
grep_required 'Verdict: accept | revise | blocked' "$ROOT/skills/teamwork-review/SKILL.md" \
  "review skill verdict enum must match Reviewer Verdict Packet"
grep_absent 'Verdict: pass | pass-with-notes' \
  "review skill must not use stale pass/pass-with-notes verdict enum" \
  "$ROOT/skills/teamwork-review/SKILL.md"
grep_required 'closes or' "$ROOT/skills/teamwork-goal/SKILL.md" \
  "goal loop must close or block delegated tracks before retry"

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
grep_required "explicit standing request" "$ROOT/CODEX.md" \
  "CODEX.md must include Codex standing subagent authorization snippet"
grep_required 'write_teamwork_codex_global_policy()' "$ROOT/install.sh" \
  "installer must define Teamwork Codex global policy writer"
grep_required '<!-- TEAMWORK_CODEX_GLOBAL_START -->' "$ROOT/install.sh" \
  "installer global policy writer must include managed start marker"
grep_required '<!-- TEAMWORK_CODEX_GLOBAL_END -->' "$ROOT/install.sh" \
  "installer global policy writer must include managed end marker"
grep_required 'explicit standing authorization and request' "$ROOT/install.sh" \
  "installer global policy must provide explicit Codex subagent authorization"
grep_required 'non-lightweight, independent, and worth the extra agent' "$ROOT/install.sh" \
  "installer global policy must preserve dispatch economics"
grep_required 'install_codex_global_policy' "$ROOT/install.sh" \
  "installer must call Codex global policy install from Codex target"
grep_required './install.sh --link codex' "$ROOT/README.md" \
  "README must document Codex link-mode development install"
grep_required './install.sh --link codex' "$ROOT/README.en.md" \
  "English README must document Codex link-mode development install"
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
line_count_max "$ROOT/skills/using-teamwork/references/dispatch-policy.md" 140 "dispatch policy reference should stay focused"
word_count_max "$ROOT/skills/using-teamwork/references/dispatch-policy.md" 800 "dispatch policy reference should stay focused"
line_count_max "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" 130 "platform dispatch mapping reference should stay focused"
word_count_max "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" 700 "platform dispatch mapping reference should stay focused"
line_count_max "$ROOT/skills/using-teamwork/references/workflow-orchestration.md" 80 "workflow orchestration reference should stay focused"
word_count_max "$ROOT/skills/using-teamwork/references/workflow-orchestration.md" 500 "workflow orchestration reference should stay focused"
line_count_max "$ROOT/skills/using-teamwork/references/subagent-prompt-contract.md" 80 "subagent prompt contract should stay focused"
word_count_max "$ROOT/skills/using-teamwork/references/subagent-prompt-contract.md" 500 "subagent prompt contract should stay focused"
line_count_max "$ROOT/skills/using-teamwork/references/subagent-packets.md" 150 "subagent packet reference should stay focused"
word_count_max "$ROOT/skills/using-teamwork/references/subagent-packets.md" 500 "subagent packet reference should stay focused"
line_count_max "$ROOT/skills/using-teamwork/references/research-protocol.md" 70 "research protocol reference should stay focused"
word_count_max "$ROOT/skills/using-teamwork/references/research-protocol.md" 450 "research protocol reference should stay focused"
line_count_max "$ROOT/skills/using-teamwork/references/role-workflows.md" 80 "role workflows reference should stay focused"
word_count_max "$ROOT/skills/using-teamwork/references/role-workflows.md" 500 "role workflows reference should stay focused"
line_count_max "$ROOT/skills/using-teamwork/references/optional-skills.md" 90 "optional skills reference should stay focused"
word_count_max "$ROOT/skills/using-teamwork/references/optional-skills.md" 600 "optional skills reference should stay focused"
line_count_max "$ROOT/skills/using-teamwork/references/designer-judge-workflow.md" 80 "designer/judge workflow reference should stay focused"
word_count_max "$ROOT/skills/using-teamwork/references/designer-judge-workflow.md" 550 "designer/judge workflow reference should stay focused"
line_count_max "$ROOT/skills/using-teamwork/references/worker-workflow.md" 80 "worker workflow reference should stay focused"
word_count_max "$ROOT/skills/using-teamwork/references/worker-workflow.md" 550 "worker workflow reference should stay focused"
line_count_max "$ROOT/skills/using-teamwork/references/reviewer-workflow.md" 80 "reviewer workflow reference should stay focused"
word_count_max "$ROOT/skills/using-teamwork/references/reviewer-workflow.md" 550 "reviewer workflow reference should stay focused"
line_count_max "$ROOT/skills/using-teamwork/references/subagent-routing.md" 25 "compatibility routing index should stay small"
word_count_max "$ROOT/skills/using-teamwork/references/subagent-routing.md" 120 "compatibility routing index should stay small"
line_count_max "$ROOT/skills/using-teamwork/references/project-init.md" 95 "project init reference should stay focused"
word_count_max "$ROOT/skills/using-teamwork/references/project-init.md" 650 "project init reference should stay focused"
line_count_max "$ROOT/skills/using-teamwork/references/teamwork-index.md" 100 "teamwork index reference should stay focused"
word_count_max "$ROOT/skills/using-teamwork/references/teamwork-index.md" 600 "teamwork index reference should stay focused"
for skill in "${SKILLS[@]}"; do
  fenced_block_line_count_max "$ROOT/skills/$skill/SKILL.md" 20 "$skill must not embed large fenced templates"
done

grep_required 'platform-native layer' "$ENTRYPOINT" \
  "entrypoint/router must define Teamwork as platform-native"
grep_required 'Platform Native Policy Map' "$ENTRYPOINT" \
  "entrypoint/router must document platform native policy map"
grep_required 'Goal Proposal' "$ENTRYPOINT" \
  "entrypoint/router must document goal proposal routing"
grep_required 'dispatch-policy.md' "$ENTRYPOINT" \
  "entrypoint/router must point to dispatch economics"
grep_required 'workflow-contract.md' "$ENTRYPOINT" \
  "entrypoint/router must point to shared workflow judgment"
grep_required 'Plans may' "$ENTRYPOINT" \
  "entrypoint/router must treat plans as routing guidance, not sole dispatch authorization"
grep_required 'Native fast path' "$ENTRYPOINT" \
  "entrypoint/router must define native fast path"
grep_required 'Progressive Reference Loading' "$ENTRYPOINT" \
  "entrypoint/router must define progressive reference loading"
grep_required 'Fast path first' "$ENTRYPOINT" \
  "entrypoint/router must prioritize fast path"
grep_required 'low-risk mechanical multi-file edits' "$ENTRYPOINT" \
  "entrypoint/router must allow low-risk mechanical multi-file native flow"
grep_required 'dispatch proactively when an independent track has clear evidence' "$ENTRYPOINT" \
  "entrypoint/router must make valuable independent dispatch the Codex-first default"
grep_required 'Subagent Tool Discovery Gate' "$ENTRYPOINT" \
  "entrypoint/router must require tool discovery before serial fallback"
grep_required 'If subagents are' "$ENTRYPOINT" \
  "entrypoint/router must respect platform subagent authorization"
grep_required 'Workflow Pattern Selection' "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
  "workflow contract must define workflow pattern selection"
for pattern in 'Native single-agent' 'Skill:' 'Router/subagent' 'Handoff:' 'Custom workflow'; do
  grep_required "$pattern" "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
    "workflow contract must define pattern choice: $pattern"
done
grep_required 'Platform Native Policy Map' "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
  "workflow contract must define platform native policy map"
grep_required 'Codex standing authorization' "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
  "workflow contract must distinguish Codex standing authorization from dispatch economics"
grep_required 'project/global instruction' "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
  "workflow contract must support loaded Codex standing authorization"
grep_required 'Use subagent dispatch when' "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
  "workflow contract must make dispatch conditional on authorization and economics"
grep_required 'dispatch is preferred' "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
  "workflow contract must prefer dispatch for valuable independent tracks"
grep_required 'Low-risk mechanical multi-file' "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
  "workflow contract must preserve native fast path for low-risk mechanical multi-file work"
grep_required 'permission profiles' "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
  "workflow contract must name Codex permission profiles"
grep_required 'codex doctor' "$ROOT/skills/using-teamwork/references/codex-deep-collaboration.md" \
  "Codex deep collaboration reference must include diagnostics"
grep_required 'Appshots' "$ROOT/skills/using-teamwork/references/codex-deep-collaboration.md" \
  "Codex deep collaboration reference must include visual evidence"
grep_required 'Proactive Custom Agents' "$ROOT/skills/using-teamwork/references/codex-deep-collaboration.md" \
  "Codex deep collaboration reference must define proactive custom agents"
grep_required 'routing guidance' "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
  "workflow contract must define plan routing as guidance"
grep_required 'not the only' "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
  "workflow contract must not make plans the only authorization model"
grep_required 'The execution stage' "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
  "workflow contract must require execution-stage split reevaluation"
grep_required 'starting any coding-agent task' "$ROOT/skills/using-teamwork/SKILL.md" \
  "using-teamwork description must be broad enough for automatic discovery"
grep_required 'discovery reads frontmatter' "$ROOT/skills/using-teamwork/SKILL.md" \
  "using-teamwork must explain broad discovery before route filtering"
grep_required 'platform goal handoff unless active goal state exists' "$ROOT/skills/using-teamwork/SKILL.md" \
  "using-teamwork must route goal work through platform goal handoff"
grep_required '"CURSOR"' "$ROOT/skills/using-teamwork/SKILL.md" \
  "using-teamwork must include CURSOR init trigger"
grep_required 'CURSOR.md' "$ROOT/skills/teamwork-init/SKILL.md" \
  "teamwork-init must inspect CURSOR.md"
grep_required 'AGENTS/CODEX/CURSOR/CLAUDE' "$ROOT/skills/teamwork-init/SKILL.md" \
  "teamwork-init description must mention AGENTS/CODEX/CURSOR/CLAUDE"
grep_required 'Codex bootstrap policy:' "$ROOT/skills/teamwork-init/SKILL.md" \
  "teamwork-init must report Codex bootstrap policy audit state"
grep_required 'app-personalization' "$ROOT/skills/teamwork-init/SKILL.md" \
  "teamwork-init must include Codex App Personalization bootstrap state"
grep_required 'Init Mode: global-default | performance-first | cost-first' "$ROOT/skills/teamwork-init/SKILL.md" \
  "teamwork-init must report selected init mode"
grep_required 'downshift only routine Explorer' "$ROOT/skills/teamwork-init/SKILL.md" \
  "teamwork-init cost-first mode must only downshift routine roles"
grep_required 'preserve Deep' "$ROOT/skills/teamwork-init/SKILL.md" \
  "teamwork-init cost-first mode must preserve deep xhigh triggers"
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
grep_required 'Explorer Result Packet once' "$ROOT/templates/claude-agents/explore.md" \
  "Claude explore agent must return exact Explorer packet once and stop"
grep_required 'Worker Completion Packet once' "$ROOT/templates/claude-agents/worker.md" \
  "Claude worker agent must return exact Worker packet once and stop"
grep_required 'Reviewer Verdict Packet once' "$ROOT/templates/claude-agents/code-reviewer.md" \
  "Claude reviewer agent must return exact Reviewer packet once and stop"
grep_required 'accept`, `revise`, or `blocked`' "$ROOT/templates/claude-agents/code-reviewer.md" \
  "Claude reviewer verdict enum must match Reviewer Verdict Packet"
for agent in teamwork-explorer teamwork-worker teamwork-designer teamwork-judge teamwork-reviewer teamwork-deep-judge teamwork-deep-reviewer; do
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
grep_required '^name = "teamwork_deep_judge"$' "$ROOT/templates/codex-agents/teamwork-deep-judge.toml" \
  "Codex deep judge agent must declare exact name"
grep_required '^name = "teamwork_deep_reviewer"$' "$ROOT/templates/codex-agents/teamwork-deep-reviewer.toml" \
  "Codex deep reviewer agent must declare exact name"
for agent in teamwork-explorer teamwork-worker teamwork-designer; do
  grep_required '^model = "gpt-5.5"$' "$ROOT/templates/codex-agents/$agent.toml" \
    "Codex agent must use performance-first pro model: $agent"
  grep_required '^model_reasoning_effort = "medium"$' "$ROOT/templates/codex-agents/$agent.toml" \
    "Codex routine agent must use medium reasoning: $agent"
done
for agent in teamwork-judge teamwork-reviewer; do
  grep_required '^model = "gpt-5.5"$' "$ROOT/templates/codex-agents/$agent.toml" \
    "Codex review agent must use frontier model: $agent"
  grep_required '^model_reasoning_effort = "high"$' "$ROOT/templates/codex-agents/$agent.toml" \
    "Codex review agent must use high reasoning: $agent"
done
for agent in teamwork-deep-judge teamwork-deep-reviewer; do
  grep_required '^model = "gpt-5.5"$' "$ROOT/templates/codex-agents/$agent.toml" \
    "Codex deep agent must use frontier model: $agent"
  grep_required '^model_reasoning_effort = "xhigh"$' "$ROOT/templates/codex-agents/$agent.toml" \
    "Codex deep agent must use xhigh reasoning: $agent"
done
grep_required 'Explorer Result Packet once' "$ROOT/templates/codex-agents/teamwork-explorer.toml" \
  "Codex explorer agent must return exact Explorer packet once and stop"
grep_required 'Decision Relevance' "$ROOT/templates/codex-agents/teamwork-explorer.toml" \
  "Codex explorer agent must include expanded Explorer packet fields"
grep_required 'Search Plan' "$ROOT/templates/codex-agents/teamwork-explorer.toml" \
  "Codex explorer agent must include research packet fields"
grep_required 'Artifact Pointer / Evidence Store' "$ROOT/templates/codex-agents/teamwork-explorer.toml" \
  "Codex explorer agent must carry artifact pointer for evidence overflow"
grep_required 'Source Census when broad' "$ROOT/templates/codex-agents/teamwork-explorer.toml" \
  "Codex explorer agent must include source census for broad research"
grep_required 'output/source/citation budget' "$ROOT/templates/codex-agents/teamwork-explorer.toml" \
  "Codex explorer agent must respect parent budget fields"
grep_required 'default max 8 each' "$ROOT/templates/codex-agents/teamwork-explorer.toml" \
  "Codex explorer agent must keep bounded broad-research caps"
grep_required 'Citation Ledger' "$ROOT/templates/claude-agents/explore.md" \
  "Claude explorer agent must include research packet fields"
grep_required 'Artifact Pointer / Evidence Store' "$ROOT/templates/claude-agents/explore.md" \
  "Claude explorer agent must carry artifact pointer for evidence overflow"
grep_required 'Source Census when broad' "$ROOT/templates/claude-agents/explore.md" \
  "Claude explorer agent must include source census for broad research"
grep_required 'output/source/citation budget' "$ROOT/templates/claude-agents/explore.md" \
  "Claude explorer agent must respect parent budget fields"
grep_required 'default max 8 each' "$ROOT/templates/claude-agents/explore.md" \
  "Claude explorer agent must keep bounded broad-research caps"
grep_required 'Designer Decision Packet once' "$ROOT/templates/codex-agents/teamwork-designer.toml" \
  "Codex designer agent must return exact Designer packet once and stop"
grep_required 'Decision Scope' "$ROOT/templates/codex-agents/teamwork-designer.toml" \
  "Codex designer agent must include expanded Designer packet fields"
grep_required 'Judge Plan Review Packet once' "$ROOT/templates/codex-agents/teamwork-judge.toml" \
  "Codex judge agent must return exact Judge packet once and stop"
grep_required 'accept, revise, or blocked' "$ROOT/templates/codex-agents/teamwork-judge.toml" \
  "Codex judge verdict enum must match Judge packet"
grep_required 'Stop Rule Adequacy' "$ROOT/templates/codex-agents/teamwork-judge.toml" \
  "Codex judge agent must include expanded Judge packet fields"
for agent in teamwork-judge teamwork-deep-judge; do
  for anchor in 'Requirements Mapping Adequacy' 'Assumption Safety' 'Protected Boundary Adequacy' 'Plan Completeness' 'Guardrails / Stop Conditions' 'Verdict Rationale'; do
    grep_required "$anchor" "$ROOT/templates/codex-agents/$agent.toml" \
      "Codex $agent must include expanded Judge field: $anchor"
  done
done
grep_required 'Worker Completion Packet once' "$ROOT/templates/codex-agents/teamwork-worker.toml" \
  "Codex worker agent must return exact Worker packet once and stop"
grep_required 'done, done_with_concerns, blocked, or needs_context' "$ROOT/templates/codex-agents/teamwork-worker.toml" \
  "Codex worker status enum must match Worker packet"
grep_required 'Protected Boundary Hits' "$ROOT/templates/codex-agents/teamwork-worker.toml" \
  "Codex worker agent must include expanded Worker packet fields"
grep_required 'Reviewer Verdict Packet once' "$ROOT/templates/codex-agents/teamwork-reviewer.toml" \
  "Codex reviewer agent must return exact Reviewer packet once and stop"
grep_required 'accept, revise, or blocked' "$ROOT/templates/codex-agents/teamwork-reviewer.toml" \
  "Codex reviewer verdict enum must match Reviewer packet"
grep_required 'Requirement Misses' "$ROOT/templates/codex-agents/teamwork-reviewer.toml" \
  "Codex reviewer agent must include expanded Reviewer packet fields"
for agent in teamwork-reviewer teamwork-deep-reviewer; do
  for anchor in 'Base/Head or Diff Source' 'Requirements / Evidence Map' 'Severity Crosswalk' 'Feedback / Thread Disposition' 'CI / Log Provenance' 'Re-review Status' 'Pushback / Dissent'; do
    grep_required "$anchor" "$ROOT/templates/codex-agents/$agent.toml" \
      "Codex $agent must include expanded Reviewer field: $anchor"
  done
done
for anchor in 'Role' 'Native Fields' 'Status' 'Plan Source' 'Owned Scope' 'Plan Step Mapping' 'Files Changed' 'Implemented' 'Mode' 'TDD Evidence' 'Failing Test / Repro Evidence' 'Root Cause Evidence' 'Hypothesis Tested' 'Verification Commands' 'Verification Result' 'Claim Supported By Evidence' 'Review Loop Status' 'Deviations' 'Protected Boundary Hits' 'Concerns / Blockers'; do
  grep_required "$anchor" "$ROOT/templates/claude-agents/worker.md" \
    "Claude worker agent must include canonical Worker field: $anchor"
done
for anchor in 'Role' 'Native Fields' 'Verdict' 'Review Target' 'Base/Head or Diff Source' 'Requirements / Evidence Map' 'Acceptance Mapping' 'Requirement Misses' 'Issues' 'Severity Crosswalk' 'Feedback / Thread Disposition' 'Verification Reviewed' 'CI / Log Provenance' 'Manual Smoke Evidence' 'Routing Conformance' 'Re-review Status' 'Pushback / Dissent' 'Residual Risk' 'Next Route'; do
  grep_required "$anchor" "$ROOT/templates/claude-agents/code-reviewer.md" \
    "Claude reviewer agent must include canonical Reviewer field: $anchor"
done
grep_required 'not a separate conceptual role' "$ROOT/templates/codex-agents/teamwork-deep-judge.toml" \
  "Codex deep judge must be documented as a severity profile"
grep_required 'not a separate conceptual role' "$ROOT/templates/codex-agents/teamwork-deep-reviewer.toml" \
  "Codex deep reviewer must be documented as a severity profile"
if [[ -d "$ROOT/.codex/agents" ]]; then
  for agent in teamwork-explorer teamwork-worker teamwork-designer teamwork-judge teamwork-reviewer teamwork-deep-judge teamwork-deep-reviewer; do
    generated="$ROOT/.codex/agents/$agent.toml"
    template="$ROOT/templates/codex-agents/$agent.toml"
    if [[ -e "$generated" ]]; then
      if [[ -L "$generated" ]]; then
        [[ "$(readlink "$generated")" == "$template" ]] \
          || fail "project Codex agent symlink drifted: $agent"
      else
        diff -q \
          <(sed '/^model = /d;/^model_reasoning_effort = /d' "$generated") \
          <(sed '/^model = /d;/^model_reasoning_effort = /d' "$template") >/dev/null \
          || fail "project Codex agent copy drifted from template: $agent"
      fi
    fi
  done
fi
if [[ -d "$ROOT/.claude/agents" ]]; then
  for agent in explore worker code-reviewer; do
    generated="$ROOT/.claude/agents/$agent.md"
    template="$ROOT/templates/claude-agents/$agent.md"
    if [[ -e "$generated" ]]; then
      if [[ -L "$generated" ]]; then
        [[ "$(readlink "$generated")" == "$template" ]] \
          || fail "project Claude agent symlink drifted: $agent"
      else
        cmp -s "$generated" "$template" \
          || fail "project Claude agent copy drifted from template: $agent"
      fi
    fi
  done
fi
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
grep_required 'plan-ready' "$ROOT/skills/teamwork-research/SKILL.md" \
  "research handoff must include plan-ready fields"
grep_required 'research-protocol.md' "$ROOT/skills/teamwork-research/SKILL.md" \
  "research skill must use research protocol"
grep_required 'source-audit' "$ROOT/skills/using-teamwork/references/research-protocol.md" \
  "research protocol must define source-audit mode"
grep_required 'Citation Ledger' "$ROOT/skills/using-teamwork/references/research-protocol.md" \
  "research protocol must require Citation Ledger"
grep_required 'public web search separate from private data' "$ROOT/skills/teamwork-research/SKILL.md" \
  "research skill must preserve public/private research safety staging"
grep_required 'Search Keys' "$ROOT/skills/teamwork-research/SKILL.md" \
  "research artifact template must include Search Keys"
grep_required 'Abstract' "$ROOT/skills/teamwork-research/SKILL.md" \
  "research artifact template must include Abstract"
grep_required 'Use the lightest planning form that preserves correctness' "$ROOT/skills/teamwork-plan/SKILL.md" \
  "plan skill must support lightweight and durable planning tiers"
grep_required 'non-trivial implement/fix/add/change' "$ROOT/skills/teamwork-plan/SKILL.md" \
  "plan skill description must cover only non-trivial implementation verbs"
grep_required 'Plan-as-you-go' "$ROOT/skills/teamwork-plan/SKILL.md" \
  "plan skill must support plan-as-you-go"
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
grep_required 'Run the Parallelization Gate before implementation steps when work is' "$ROOT/skills/teamwork-plan/SKILL.md" \
  "plan skill must evaluate split before implementation steps when material"
grep_required '`Dispatch Guidance: none` requires a continuity rationale only when' "$ROOT/skills/teamwork-plan/SKILL.md" \
  "plan skill must require rationale for material serial continuity"
grep_required 'Abstract' "$ROOT/skills/using-teamwork/references/plan-output.md" \
  "plan output reference must include Abstract"
grep_required 'Durable Plan Sections' "$ROOT/skills/using-teamwork/references/plan-output.md" \
  "plan output reference must include durable plan sections"
grep_required 'Platform native dispatch fields are derived at dispatch time from the' "$ROOT/skills/teamwork-plan/SKILL.md" \
  "plan skill must derive native dispatch fields at dispatch time"
grep_required 'designer-judge-workflow.md' "$ROOT/skills/teamwork-plan/SKILL.md" \
  "plan skill must use designer/judge workflow detail"
grep_required 'option matrix' "$ROOT/skills/teamwork-plan/SKILL.md" \
  "plan skill must require Designer option matrix workflow"
grep_required 'Designer Decision' "$ROOT/skills/using-teamwork/references/plan-output.md" \
  "plan output must include optional Designer Decision section"
grep_required 'Judge Plan Review' "$ROOT/skills/using-teamwork/references/plan-output.md" \
  "plan output must include optional Judge Plan Review section"
for role in Explorer Designer Judge Worker Reviewer; do
  grep_required "$role" "$ROOT/skills/using-teamwork/references/role-workflows.md" \
    "role workflows must cover $role"
done
for anchor in 'Research Protocol' 'Planning Synthesis' 'Staged Execution' 'TDD Gate' 'Debugging Gate' 'Verification Before Claims' 'Review Request' 'Review Reception'; do
  grep_required "$anchor" "$ROOT/skills/using-teamwork/references/role-workflows.md" \
    "role workflows must map Teamwork workflow contract: $anchor"
done
for anchor in 'Design Synthesis' 'Parallel Dispatch' 'Skill Authoring'; do
  grep_required "$anchor" "$ROOT/skills/using-teamwork/references/role-workflows.md" \
    "role workflows must map Designer/Judge workflow contract: $anchor"
done
for anchor in 'Option Matrix' 'Plan Decomposition Notes' 'Acceptance Implications' 'Requirements Mapping Adequacy' 'Guardrails / Stop Conditions' 'Acceptance Gap'; do
  grep_required "$anchor" "$ROOT/skills/using-teamwork/references/subagent-packets.md" \
    "subagent packets must include Designer/Judge field: $anchor"
done
for anchor in 'Plan Step Mapping' 'TDD Evidence' 'Root Cause Evidence' 'Verification Commands' 'Claim Supported By Evidence' 'Review Loop Status'; do
  grep_required "$anchor" "$ROOT/skills/using-teamwork/references/subagent-packets.md" \
    "subagent packets must include Worker field: $anchor"
done
for anchor in 'Requirements / Evidence Map' 'Severity Crosswalk' 'Feedback / Thread Disposition' 'CI / Log Provenance' 'Re-review Status' 'Pushback / Dissent'; do
  grep_required "$anchor" "$ROOT/skills/using-teamwork/references/subagent-packets.md" \
    "subagent packets must include Reviewer field: $anchor"
done
grep_required 'worker-workflow.md' "$ROOT/skills/teamwork-execute/SKILL.md" \
  "execute skill must use Worker workflow detail"
grep_required 'exit condition' "$ROOT/skills/teamwork-execute/SKILL.md" \
  "execute skill must require Worker run-loop exit"
grep_required 'reviewer-workflow.md' "$ROOT/skills/teamwork-review/SKILL.md" \
  "review skill must use Reviewer workflow detail"
grep_required 'Requirements / Evidence Map' "$ROOT/skills/teamwork-review/SKILL.md" \
  "review skill verdict format must include evidence map"
grep_required 'Re-review after `revise`' "$ROOT/skills/using-teamwork/references/reviewer-workflow.md" \
  "reviewer workflow must define re-review loop"
grep_required 'TDD Gate' "$ROOT/skills/using-teamwork/references/worker-workflow.md" \
  "worker workflow must define TDD gate"
grep_required 'Debugging Gate' "$ROOT/skills/using-teamwork/references/worker-workflow.md" \
  "worker workflow must define debugging gate"
grep_required 'expected output, guardrails, retry/stop conditions' "$ROOT/skills/using-teamwork/references/designer-judge-workflow.md" \
  "designer/judge workflow must define guardrail and stop condition checks"
for skill in teamwork-plan teamwork-execute teamwork-review; do
  grep_required 'role-workflows.md' "$ROOT/skills/$skill/SKILL.md" \
    "$skill must reference role workflows"
done
grep_required 'optional-skills.md' "$ROOT/skills/teamwork-research/SKILL.md" \
  "research skill must reference optional skill gate"
grep_required 'optional-skills.md' "$ROOT/skills/teamwork-plan/SKILL.md" \
  "plan skill must reference optional skill gate"
grep_required 'optional-skills.md' "$ROOT/skills/teamwork-execute/SKILL.md" \
  "execute skill must reference optional skill gate"
grep_required 'optional-skills.md' "$ROOT/skills/teamwork-review/SKILL.md" \
  "review skill must reference optional skill gate"
for anchor in 'plugin-first' 'No duplicate install' 'credential' 'write risk' 'smoke test' 'broad community' 'Candidate Record'; do
  grep_required "$anchor" "$ROOT/skills/using-teamwork/references/optional-skills.md" \
    "optional skills must document gate anchor: $anchor"
done
grep_required 'Skill = reusable workflow or expertise; plugin = installable distribution unit' "$ROOT/skills/using-teamwork/references/optional-skills.md" \
  "optional skills must distinguish skill workflow from plugin distribution"
grep_required 'licenses may differ per skill directory' "$ROOT/skills/using-teamwork/references/optional-skills.md" \
  "optional skills must require per-skill license awareness"
python3 - "$ROOT/skills/using-teamwork/references/optional-skills.md" <<'PY'
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text()
required = [
    "Source/License",
    "Role Fit",
    "Trigger",
    "Credentials",
    "Write Risk",
    "Smoke Test",
    "Decision",
]
missing = [name for name in required if name not in text]
if missing:
    raise SystemExit(f"FAIL: optional-skills.md candidate record missing fields: {', '.join(missing)}")
volatile = ["gh-fix-ci", "gh-address-comments", "playwright-interactive", "security-threat-model"]
leaked = [name for name in volatile if name in text]
if leaked:
    raise SystemExit(f"FAIL: optional-skills.md must not keep static external skill inventory: {', '.join(leaked)}")
PY
grep_absent 'Official assumptions refreshed' \
  "runtime references must not contain dated official-assumption refresh claims" \
  "$ROOT/skills/using-teamwork/references"
grep_required 'codex review' "$ROOT/skills/teamwork-review/SKILL.md" \
  "review skill must mention codex review as evidence"
grep_required 'Routing conformance' "$ROOT/skills/teamwork-review/SKILL.md" \
  "review skill must check routing conformance"
grep_required 'missing Parallelization Gate' "$ROOT/skills/teamwork-review/SKILL.md" \
  "review skill must reject plans without the parallelization gate"
grep_required 'Execution Review' "$ROOT/skills/using-teamwork/references/review-checks.md" \
  "review checks reference must include execution review"
grep_required 'Re-review after `revise` records prior verdict' "$ROOT/skills/using-teamwork/references/review-checks.md" \
  "review checks must require re-review closure evidence"
grep_required 'CI review records failing check/log provenance' "$ROOT/skills/using-teamwork/references/review-checks.md" \
  "review checks must require CI provenance when relevant"
grep_required 'sandbox' "$ROOT/skills/teamwork-execute/SKILL.md" \
  "execute skill must document sandbox approvals"
grep_required 'accepted, approved, resumed' "$ROOT/skills/teamwork-execute/SKILL.md" \
  "execute skill must auto-route accepted or resumed plans"
grep_required 'go ahead, proceed, do it' "$ROOT/skills/teamwork-execute/SKILL.md" \
  "execute skill description must cover natural continuation verbs"
grep_required 'parallel Worker' "$ROOT/skills/teamwork-execute/SKILL.md" \
  "execute skill must prefer parallel Worker subagents for independent tracks"
grep_required 'Automatic Stage Selection' "$ROOT/skills/using-teamwork/SKILL.md" \
  "using-teamwork must define automatic natural-language stage selection"
grep_required 'Do not wait for named skills' "$ROOT/skills/using-teamwork/SKILL.md" \
  "using-teamwork must not require manual skill invocation"
grep_required 'check/validate completed work' "$ROOT/skills/using-teamwork/SKILL.md" \
  "using-teamwork must not route bare check/validate to review ceremony"
grep_required 'simple checks stay native' "$ROOT/skills/using-teamwork/SKILL.md" \
  "using-teamwork must keep simple checks lightweight"
grep_required 'budgeted convergence' "$ROOT/skills/using-teamwork/SKILL.md" \
  "using-teamwork must not route bare budget mentions to goal mode"
grep_required 'teamwork-update' "$ROOT/skills/using-teamwork/SKILL.md" \
  "using-teamwork must route package update work"
grep_required 'teamwork-init' "$ROOT/skills/using-teamwork/SKILL.md" \
  "using-teamwork must route project initialization work"
grep_required 'Project Rule Layering' "$ROOT/skills/using-teamwork/references/project-init.md" \
  "project init reference must define project rule layering"
grep_required 'CodeGraph' "$ROOT/skills/using-teamwork/references/project-init.md" \
  "project init reference must define CodeGraph policy"
for row in 'Core Teamwork workflow' 'Platform profile' 'Project instruction layer' 'Artifact memory' 'CodeGraph policy' 'Subagent policy/install state' 'Teamwork role workflow contracts' 'Validation' 'Optional docs graph' 'Optional external memory' 'Blockers'; do
  grep_required "$row" "$ROOT/skills/using-teamwork/references/project-init.md" \
    "project init full-feature matrix missing row: $row"
done
for status in enabled missing blocked optional deferred; do
  grep_required "$status" "$ROOT/skills/using-teamwork/references/project-init.md" \
    "project init full-feature matrix missing status: $status"
done
grep_required 'Full Feature Init' "$ROOT/skills/teamwork-init/SKILL.md" \
  "teamwork-init must expose full-feature init behavior"
grep_required 'Capability Matrix' "$ROOT/skills/teamwork-init/SKILL.md" \
  "teamwork-init must return a capability matrix for full-feature requests"
grep_required 'External memory/docs graph rows stay' "$ROOT/skills/teamwork-init/SKILL.md" \
  "teamwork-init must keep external memory/docs graph opt-in"
grep_required 'Memory And Docs Graph Candidates' "$ROOT/skills/using-teamwork/references/optional-skills.md" \
  "optional skills must cover memory/docs graph candidate gates"
grep_required 'Canonical Boundary' "$ROOT/skills/using-teamwork/references/optional-skills.md" \
  "optional memory/docs graph gates must state candidate boundary"
grep_required 'External Memory Promotion Gate' "$ROOT/skills/using-teamwork/references/artifact-protocol.md" \
  "artifact protocol must define external memory promotion gate"
grep_required 'memory candidate' "$ROOT/skills/using-teamwork/references/artifact-protocol.md" \
  "artifact protocol must keep external recall as memory candidate context"
grep_required 'use CodeGraph before Explorer fanout' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy must use CodeGraph before Explorer fanout for structural code"
grep_required 'vendor-specific memory backend' "$ROOT/skills/using-teamwork/references/teamwork-index.md" \
  "teamwork index contract must avoid vendor-specific memory backends"
grep_required 'docs/teamwork' "$ROOT/skills/using-teamwork/references/project-init.md" \
  "project init reference must define Teamwork artifact placement"
grep_required 'runtime memory entrypoint' "$ROOT/skills/using-teamwork/references/project-init.md" \
  "project init reference must point project instructions to Teamwork runtime README"
grep_required 'context-cache' "$ROOT/skills/using-teamwork/references/project-init.md" \
  "project init reference must define context-cache policy"
grep_required 'current task progress' "$ROOT/skills/teamwork-init/SKILL.md" \
  "teamwork-init must forbid current task progress in instructions"
grep_required 'short `AGENTS.md` or README pointer' "$ROOT/skills/teamwork-init/SKILL.md" \
  "teamwork-init must add short project instruction pointer to Teamwork runtime README"
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
grep_required 'end-user package refresh' "$ROOT/skills/teamwork-update/SKILL.md" \
  "update skill must treat Teamwork updates as user-facing package refresh"
grep_required './install.sh all' "$ROOT/skills/teamwork-update/SKILL.md" \
  "update skill must refresh all installed Teamwork surfaces"
grep_required './install.sh project' "$ROOT/skills/teamwork-update/SKILL.md" \
  "update skill must cover project-local install surface refresh"
grep_required 'GitHub remote' "$ROOT/skills/teamwork-update/SKILL.md" \
  "update skill must check GitHub remote for publication updates"
grep_required 'tag/release' "$ROOT/skills/teamwork-update/SKILL.md" \
  "update skill must cover tag/release publication checks"

for term in observed inferred claimed; do
  grep_required "$term" "$ENTRYPOINT" "entrypoint/router must mention $term evidence"
  grep_required "$term" "$ROOT/skills/teamwork-research/SKILL.md" "research skill must mention $term evidence"
  grep_required "$term" "$ROOT/skills/teamwork-plan/SKILL.md" "plan skill must mention $term evidence"
  grep_required "$term" "$ROOT/skills/teamwork-review/SKILL.md" "review skill must mention $term evidence"
done

grep_required 'Explorer -> `agent_type:"teamwork_explorer"`' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "dispatch policy reference must map Explorer to Codex custom agent"
grep_required '`agent_type:"teamwork_worker"`' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "dispatch policy reference must map Worker to Codex custom agent"
grep_required '`agent_type:"teamwork_designer"`' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "dispatch policy reference must map Designer to Codex custom agent"
grep_required '`agent_type:"teamwork_judge"`' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "dispatch policy reference must map Judge to Codex custom agent"
grep_required '`agent_type:"teamwork_reviewer"`' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "dispatch policy reference must map Reviewer to Codex custom agent"
grep_required 'Fallback when custom agents are unavailable' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "dispatch policy reference must define Codex built-in fallback mapping"
grep_required '`fast` -> `reasoning_effort:"low"`' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "dispatch policy reference must map fast tier"
grep_required '`standard` -> `reasoning_effort:"medium"`' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "dispatch policy reference must map standard tier"
grep_required '`high reasoning` -> `reasoning_effort:"high"`' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "dispatch policy reference must map high reasoning tier"
grep_required '`deep reasoning` -> `reasoning_effort:"xhigh"`' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "dispatch policy reference must map deep reasoning tier"
grep_required 'Do not combine' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "dispatch policy reference must reject invalid full-history routing"
grep_required 'Codex role dispatch' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "Codex role dispatch must pin role-profile models by default"
grep_required 'Role Profiles' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy reference must define role profiles"
grep_required '`performance-first` uses' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy must define performance-first role profile behavior"
grep_required 'model class `balanced` by default' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "Explorer profile must preserve stable class policy"
grep_required 'Judge: model class `frontier`, reasoning `high`' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "Judge/Reviewer profiles must require high reasoning class"
grep_required 'Reviewer: model class `frontier`, reasoning `high`' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "Reviewer profile must require high reasoning class"
grep_required 'Codex Model Mapping' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "dispatch policy reference must define Codex model mapping"
grep_required 'Codex Native Field Presets' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "dispatch policy reference must define explicit Codex native field presets"
grep_required '`performance-first`: install-time default for Pro/20x Codex workflows' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "model mapping must define performance-first Codex profile"
grep_required '`cheap-fast` -> `gpt-5.4-mini`' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "cost-first model mapping must define cheap-fast model"
grep_required 'opt-in only for trivial read-only' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "cheap-fast model must be opt-in, not a default"
grep_required '`balanced` and' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "model mapping must define cost-first balanced/coding models"
grep_required '`frontier` -> `gpt-5.5`' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "model mapping must define frontier pro model"
grep_required 'Codex role dispatch: `agent_type`, `model`, `reasoning_effort`' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "Codex mapping must define role dispatch native fields"
grep_required 'full-history fork: `fork_context:true` only' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "Codex mapping must define fork_context-only full-history shape"
grep_required 'Explorer default: `agent_type:"explorer"`, `model:"gpt-5.5"`' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "Codex Explorer preset must pin pro model"
grep_required 'Worker default: `agent_type:"worker"`, `model:"gpt-5.5"`' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "Codex Worker preset must pin pro model"
grep_required 'agent_type:"teamwork_deep_judge"' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "Codex mapping must define explicit deep judge custom agent"
grep_required 'agent_type:"teamwork_deep_reviewer"' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "Codex mapping must define explicit deep reviewer custom agent"
grep_absent 'gpt-5.3-codex' \
  "Codex custom-agent model mapping must not use removed gpt-5.3-codex slug" \
  "$ROOT/templates/codex-agents" "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" "$ROOT/CODEX.md"
grep_absent 'gpt-5.5-pro' \
  "Codex custom-agent model mapping must not use unsupported gpt-5.5-pro slug" \
  "$ROOT/templates/codex-agents" "$ROOT/skills" "$ROOT/CODEX.md" "$ROOT/README.md" "$ROOT/README.en.md" "$ROOT/install.sh"
grep_absent 'max-quality\|max quality\|--max-quality' \
  "Teamwork must not add a max-quality profile" \
  "$ROOT/templates/codex-agents" "$ROOT/skills" "$ROOT/CODEX.md" "$ROOT/README.md" "$ROOT/README.en.md" "$ROOT/install.sh"
grep_absent '^model_reasoning_effort = "xhigh"$' \
  "Only deep Codex agents may use xhigh" \
  "$ROOT/templates/codex-agents/teamwork-explorer.toml" \
  "$ROOT/templates/codex-agents/teamwork-worker.toml" \
  "$ROOT/templates/codex-agents/teamwork-designer.toml" \
  "$ROOT/templates/codex-agents/teamwork-judge.toml" \
  "$ROOT/templates/codex-agents/teamwork-reviewer.toml"
grep_required 'Judge default: `agent_type:"default"`, `model:"gpt-5.5"`' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "Codex Judge preset must pin pro model"
grep_required 'Deep Judge/Reviewer default' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "Codex mapping must define deep xhigh fallback"
grep_required 'triggers still use `gpt-5.5` with xhigh reasoning' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "cost-first mapping must preserve deep xhigh triggers"
grep_required 'five conceptual roles' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy must define five-role taxonomy"
grep_required 'Codex Native Field Presets' "$ROOT/skills/using-teamwork/references/subagent-prompt-contract.md" \
  "subagent prompt contract must require Codex native field presets"
grep_required 'Platform Dispatch Fields' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "dispatch policy reference must define platform dispatch fields"
grep_required 'Cursor Mapping' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "dispatch policy reference must define Cursor mapping"
grep_required 'Explorer -> `subagent_type:"explore"`' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "Cursor mapping must map Explorer to explore"
grep_required 'Reviewer -> `subagent_type:"code-reviewer"`' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "Cursor mapping must map Reviewer to code-reviewer"
grep_required 'For `generalPurpose`, the prompt contract must carry role, packet, and' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "Cursor generalPurpose fallback must rely on full prompt contract for closure"
grep_required 'Cursor Model Mapping' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "dispatch policy reference must define Cursor model mapping"
grep_required '`cheap-fast` -> `composer-2.5-fast`' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "Cursor model mapping must define cheap-fast model"
grep_required '`balanced` -> `gpt-5.5-medium` when listed' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "Cursor model mapping must define balanced model"
grep_required '`coding` -> `gpt-5.5-medium` when listed' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "Cursor model mapping must define coding model"
grep_required '`frontier` -> `claude-opus-4-7-thinking-high`' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "Cursor model mapping must define frontier model"
grep_required 'Cursor Task Parameters' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "dispatch policy reference must define Cursor Task parameters"
grep_required 'Claude Code Mapping' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "dispatch policy reference must define Claude Code mapping"
grep_required 'Claude Code Task Parameters' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "dispatch policy reference must define Claude Code Task parameters"
grep_required 'For `general-purpose`, the prompt contract must carry role, packet, and' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "Claude general-purpose fallback must rely on full prompt contract for closure"
grep_required 'Claude Code Model Mapping' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "dispatch policy reference must define Claude Code model mapping"
grep_required '`cheap-fast` -> `claude-haiku`' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "Claude Code model mapping must define cheap-fast model"
grep_required '`frontier` -> `claude-opus`' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "Claude Code model mapping must define frontier model"
grep_required 'readonly: true' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "Cursor Task parameters must define readonly default"
grep_required 'run_in_background: true' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "Cursor Task parameters must define background dispatch"
grep_required 'best-of-n-runner' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "Cursor Task parameters must define best-of-n-runner"
grep_required 'resume: "self"' "$ROOT/skills/using-teamwork/references/platform-dispatch-mapping.md" \
  "Cursor Task parameters must define self resume"
grep_required 'code-reviewer' "$ROOT/skills/teamwork-review/SKILL.md" \
  "review skill must mention Cursor code-reviewer evidence"
grep_required 'platform native fields per platform-dispatch-mapping.md' "$ROOT/skills/using-teamwork/references/subagent-prompt-contract.md" \
  "subagent prompt contract must use platform-neutral role templates"
grep_required 'missing required env/path/command/model' "$ROOT/skills/using-teamwork/references/subagent-prompt-contract.md" \
  "subagent prompt contract must escalate missing required values"
grep_required 'resume:"self"' "$ROOT/skills/using-teamwork/references/subagent-prompt-contract.md" \
  "subagent prompt contract must define Cursor full-history fork"
grep_required 'Do not invent fallback defaults' "$ROOT/templates/codex-agents/teamwork-worker.toml" \
  "Codex Worker agent must block on missing required values"
grep_required 'silent fallback defaults' "$ROOT/templates/codex-agents/teamwork-reviewer.toml" \
  "Codex Reviewer agent must flag silent fallback defaults"
grep_required 'Clarification Relevance' "$ROOT/templates/codex-agents/teamwork-explorer.toml" \
  "Codex Explorer agent must report clarification relevance"
grep_required 'Clarification Gap' "$ROOT/templates/codex-agents/teamwork-judge.toml" \
  "Codex Judge agent must report clarification gaps"
grep_required 'Clarification Gap' "$ROOT/templates/codex-agents/teamwork-deep-judge.toml" \
  "Codex Deep Judge agent must report clarification gaps"
grep_required 'Open Questions' "$ROOT/templates/codex-agents/teamwork-worker.toml" \
  "Codex Worker agent must report open questions"
grep_required 'Clarification Gap' "$ROOT/templates/codex-agents/teamwork-reviewer.toml" \
  "Codex Reviewer agent must report clarification gaps"
grep_required 'Clarification Gap' "$ROOT/templates/codex-agents/teamwork-deep-reviewer.toml" \
  "Codex Deep Reviewer agent must report clarification gaps"
grep_required 'clarification relevance' "$ROOT/templates/claude-agents/explore.md" \
  "Claude Explorer agent must report clarification relevance"
grep_required 'Open Questions' "$ROOT/templates/claude-agents/worker.md" \
  "Claude Worker agent must report open questions"
grep_required 'Clarification Gap' "$ROOT/templates/claude-agents/code-reviewer.md" \
  "Claude Reviewer agent must report clarification gaps"
grep_required 'Do not use `cheap-fast` for normal Pro/20x Codex workflows' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy must forbid cheap-fast for Judge and Reviewer"
grep_required 'routing guidance' "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
  "workflow contract must treat plan routing as guidance"
grep_required 'Rule Placement' "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
  "workflow contract must define rule placement"
grep_required 'No Silent Defaults' "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
  "workflow contract must keep no-silent-defaults canonical"
grep_required 'Missing required values are blockers' "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
  "workflow contract must fail fast on missing required values"
grep_required 'Before planning or executing' "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
  "workflow contract must require clarification before plan or execution"
grep_required 'Gate outcomes are `pass`, `assumptions-stated`, `ask`, and' "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
  "workflow contract must define clarification gate outcomes"
grep_required 'unclear human goal/scope/acceptance asks first' "$ENTRYPOINT" \
  "entrypoint/router must ask before planning unclear human goals"
grep_required 'Resolve decision-critical human requirement gaps' "$ROOT/skills/teamwork-plan/SKILL.md" \
  "planning must clarify decision-critical human requirement gaps"
grep_required 'Clarification Gate: pass | assumptions-stated | blocked-for-clarification' "$ROOT/skills/using-teamwork/references/plan-output.md" \
  "plan output must expose clarification gate state"
grep_required 'Accepted plan resolves decision-critical user needs' "$ROOT/skills/teamwork-execute/SKILL.md" \
  "execution must require clarified user needs in the accepted plan"
grep_required 'Goal Proposal` with `Clarification Gate:' "$ROOT/skills/teamwork-goal/SKILL.md" \
  "goal proposal must expose clarification gate state"
grep_required 'unanswered human requirements could change' "$ROOT/skills/using-teamwork/references/review-checks.md" \
  "review must reject plans with decision-critical unanswered human requirements"
grep_required 'Subagents report questions; the orchestrator asks' "$ROOT/skills/using-teamwork/references/subagent-prompt-contract.md" \
  "subagents must not own user clarification"
grep_required 'Clarification Gap' "$ROOT/skills/using-teamwork/references/subagent-packets.md" \
  "subagent packets must carry clarification gaps"
grep_required 'codex-policy' "$ROOT/skills/using-teamwork/references/project-init.md" \
  "project init reference must document Codex policy rendering"
grep_required 'required environment variables' "$ROOT/skills/using-teamwork/references/project-init.md" \
  "project init reference must store required local values in project rules"
grep_absent 'verified-but-unreviewed' \
  "Teamwork must use canonical unreviewed status" \
  "$ROOT/skills" "$ROOT/CODEX.md" "$ROOT/CURSOR.md" "$ROOT/CLAUDE.md" "$ROOT/README.md" "$ROOT/README.en.md"
grep_required 'evaluate the split before implementation steps' "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
  "workflow contract must require split evaluation before implementation steps"
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
grep_required 'parallel subagents when independent tracks have clear evidence' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy must use parallel subagents when independent value justifies it"
grep_required 'Workflow-class' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy must include workflow-class escalation"
grep_required 'phase plan' "$ROOT/skills/using-teamwork/references/workflow-orchestration.md" \
  "workflow orchestration must require phase plan"
grep_required 'Cross-check' "$ROOT/skills/using-teamwork/references/workflow-orchestration.md" \
  "workflow orchestration must require cross-checking"
grep_required 'Claude Code' "$ROOT/skills/using-teamwork/references/workflow-orchestration.md" \
  "workflow orchestration must define Claude Code mapping"
grep_required 'Codex' "$ROOT/skills/using-teamwork/references/workflow-orchestration.md" \
  "workflow orchestration must define Codex mapping"
grep_required 'When the active platform or loaded instructions authorize subagents' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy must respect platform-specific subagent authorization gates"
grep_required 'Codex, a project or global standing' "$ROOT/skills/using-teamwork/references/dispatch-policy.md" \
  "dispatch policy must document Codex standing authorization"
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
grep_required 'Native Fields: fields from `platform-dispatch-mapping.md`' "$ROOT/skills/using-teamwork/references/subagent-prompt-contract.md" \
  "subagent prompt contract must require native fields"
grep_required 'full-history fork (`fork_context:true`, inherited model, no' "$ROOT/skills/using-teamwork/references/subagent-prompt-contract.md" \
  "subagent prompt contract must define Codex fork_context alternative"
grep_required 'Cursor uses `subagent_type`, `model` or' "$ROOT/skills/using-teamwork/references/subagent-prompt-contract.md" \
  "subagent prompt contract must document Cursor native fields"
grep_required 'Never imply a stronger model' "$ROOT/skills/using-teamwork/references/subagent-prompt-contract.md" \
  "subagent prompt contract must prevent misleading model claims"
grep_required 'Context Strategy: one value from `Context Strategies`' "$ROOT/skills/using-teamwork/references/subagent-prompt-contract.md" \
  "subagent prompt contract must require context strategy"
grep_required 'Required Output Schema: packet from `subagent-packets.md`' "$ROOT/skills/using-teamwork/references/subagent-prompt-contract.md" \
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
grep_required 'Search Plan; Queries Tried; Source Classes; Source Census when broad; Sources Used; Sources Rejected; Contradictions; Coverage Gaps; Citation Ledger' "$ROOT/skills/using-teamwork/references/subagent-packets.md" \
  "Explorer packet must define web/deep research fields"
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
grep_required 'Artifact Pointer / Evidence Store' "$ROOT/skills/using-teamwork/references/subagent-packets.md" \
  "Explorer packet must carry artifact pointer for evidence overflow"
grep_required 'default max 8 each' "$ROOT/skills/using-teamwork/references/subagent-packets.md" \
  "Explorer packet must keep bounded broad-research caps"
grep_required 'output/source/citation budget' "$ROOT/skills/using-teamwork/references/subagent-prompt-contract.md" \
  "Explorer prompt contract must carry budget fields"
grep_required 'source census' "$ROOT/skills/using-teamwork/references/research-protocol.md" \
  "research protocol must stage broad research through source census"
grep_required 'artifact pointer' "$ROOT/skills/using-teamwork/references/research-protocol.md" \
  "research protocol must route overflow to artifact pointers"
grep_required 'budgeted packets' "$ROOT/README.en.md" \
  "English README must describe budgeted Explorer packets"
grep_required 'capped Explorer packets' "$ROOT/README.en.md" \
  "English README must mention capped Explorer packets"
grep_required 'artifact-backed evidence ledgers' "$ROOT/README.en.md" \
  "English README must mention artifact-backed evidence ledgers"
grep_required 'citation ledgers go into artifacts' "$ROOT/README.en.md" \
  "English README must describe broad-research artifact overflow"
grep_required 'Treat compaction as continuity support, not audit evidence' "$ROOT/README.en.md" \
  "English README must keep compaction as continuity support"
for doc in CURSOR.md CLAUDE.md; do
  grep_required 'source census' "$ROOT/$doc" \
    "$doc must mention source census for broad research"
  grep_required 'capped Explorer packets' "$ROOT/$doc" \
    "$doc must mention capped Explorer packets"
  grep_required 'artifact-backed evidence ledgers' "$ROOT/$doc" \
    "$doc must mention artifact-backed evidence ledgers"
done
grep_required 'Treat compaction as continuity support, not audit evidence' "$ROOT/CURSOR.md" \
  "Cursor runtime summary must keep compaction as continuity support"
grep_required 'Treat compaction as continuity support, not audit evidence' "$ROOT/CLAUDE.md" \
  "Claude runtime summary must keep compaction as continuity support"
grep_required 'invalid platform dispatch fields' "$ROOT/skills/using-teamwork/references/review-checks.md" \
  "review checks must validate platform dispatch fields"
grep_required 'Codex/Cursor/Claude Code mapping' "$ROOT/skills/using-teamwork/references/subagent-routing.md" \
  "compatibility routing index must mention Codex/Cursor/Claude Code mapping"
grep_required 'dispatch-policy.md' "$ROOT/skills/using-teamwork/references/subagent-routing.md" \
  "compatibility routing index must point to dispatch policy"
grep_required 'platform-dispatch-mapping.md' "$ROOT/skills/using-teamwork/references/subagent-routing.md" \
  "compatibility routing index must point to platform dispatch mapping"
grep_required 'workflow-orchestration.md' "$ROOT/skills/using-teamwork/references/subagent-routing.md" \
  "compatibility routing index must point to workflow orchestration"
grep_required 'subagent-prompt-contract.md' "$ROOT/skills/using-teamwork/references/subagent-routing.md" \
  "compatibility routing index must point to prompt contract"
grep_required 'subagent-packets.md' "$ROOT/skills/using-teamwork/references/subagent-routing.md" \
  "compatibility routing index must point to packet schemas"
grep_required 'Use parallel Explorer subagents for 2+ independent tracks' "$ROOT/skills/teamwork-research/SKILL.md" \
  "research skill must dispatch valuable independent Explorer tracks"
grep_required 'and subagents are' "$ROOT/skills/teamwork-research/SKILL.md" \
  "research skill must respect subagent authorization"
grep_required 'Research Context Budget Gate' "$ROOT/skills/teamwork-research/SKILL.md" \
  "research skill must define context budget gate"
grep_required 'source census before deep reads' "$ROOT/skills/teamwork-research/SKILL.md" \
  "research skill must require source census for broad research"
grep_required 'Guidance only when dispatch matters' "$ROOT/skills/teamwork-plan/SKILL.md" \
  "plan skill must support conditional lightweight dispatch guidance"
grep_required 'subagents are authorized' "$ROOT/skills/teamwork-plan/SKILL.md" \
  "plan skill must respect subagent authorization"
grep_required 'Dispatch parallel Worker subagents when' "$ROOT/skills/teamwork-execute/SKILL.md" \
  "execute skill must dispatch independent Worker tracks when economics justify it"
grep_required 'when subagents' "$ROOT/skills/teamwork-execute/SKILL.md" \
  "execute skill must respect subagent authorization"
grep_required 'active.current' "$ROOT/skills/teamwork-execute/SKILL.md" \
  "execute skill must read active Teamwork memory before artifact-backed edits"
grep_required 'Artifact Retrieval disposition' "$ROOT/skills/teamwork-execute/SKILL.md" \
  "execute skill must record artifact retrieval disposition"
grep_required 'dispatching more than 3 Workers' "$ROOT/skills/teamwork-execute/SKILL.md" \
  "execute skill must require >3 Worker integration plan"
grep_required 'Default to fresh-context Reviewer subagents' "$ROOT/skills/teamwork-review/SKILL.md" \
  "review skill must default to fresh-context reviewer subagents for required acceptance"
grep_required 'subagents are authorized' "$ROOT/skills/teamwork-review/SKILL.md" \
  "review skill must respect subagent authorization"
grep_required 'active.current' "$ROOT/skills/teamwork-review/SKILL.md" \
  "review skill must read active Teamwork memory before durable verdicts"
grep_required 'Artifact Retrieval: none | index | reuse | update | new' "$ROOT/skills/teamwork-review/SKILL.md" \
  "review verdict must include artifact retrieval disposition"
grep_required 'Dispatch Guidance:' "$ROOT/skills/using-teamwork/references/plan-output.md" \
  "lightweight plan template must include dispatch guidance"
grep_required 'Explorer/Designer/Judge/Worker/Reviewer' "$ROOT/skills/using-teamwork/references/plan-output.md" \
  "dispatch guidance must support all Teamwork subagent roles"
grep_required 'Deep Judge/Reviewer severity' "$ROOT/skills/using-teamwork/references/plan-output.md" \
  "dispatch guidance must record deep review severity when warranted"
grep_required 'Subagent Prompt Packets' "$ROOT/skills/using-teamwork/references/plan-output.md" \
  "plan output reference must include subagent prompt packets"
grep_required 'Actual Dispatch Log' "$ROOT/skills/using-teamwork/references/plan-output.md" \
  "plan output reference must include actual dispatch log"
grep_required 'include none with rationale only when material dispatch is skipped' "$ROOT/skills/using-teamwork/references/plan-output.md" \
  "plan output reference must require rationale for material serial continuity"
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
grep_required 'selected-source table' "$ROOT/skills/using-teamwork/references/artifact-protocol.md" \
  "artifact protocol must own broad-research evidence tables"
grep_required 'packet/source budget' "$ROOT/skills/using-teamwork/references/workflow-orchestration.md" \
  "workflow orchestration must carry research packet/source budget"

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
while IFS= read -r ref_file; do
  reference="$(basename "$ref_file")"
  printf '%s\n' "retired $reference" > "$retired_teamwork_dir/references/$reference"
done < <(find "$ROOT/skills/using-teamwork/references" -maxdepth 1 -type f | sort)
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
for agent in teamwork-explorer teamwork-worker teamwork-designer teamwork-judge teamwork-reviewer teamwork-deep-judge teamwork-deep-reviewer; do
  [[ -f "$tmp/home/.codex/agents/$agent.toml" ]] \
    || fail "Codex install must copy Codex agent $agent"
  [[ ! -L "$tmp/home/.codex/agents/$agent.toml" ]] \
    || fail "default Codex install must copy Codex agent $agent"
done
for agent in teamwork-explorer teamwork-worker teamwork-designer; do
  grep_required '^model_reasoning_effort = "medium"$' "$tmp/home/.codex/agents/$agent.toml" \
    "Codex install must render medium reasoning for $agent"
done
for agent in teamwork-judge teamwork-reviewer; do
  grep_required '^model_reasoning_effort = "high"$' "$tmp/home/.codex/agents/$agent.toml" \
    "Codex install must render high reasoning for $agent"
done
for agent in teamwork-deep-judge teamwork-deep-reviewer; do
  grep_required '^model_reasoning_effort = "xhigh"$' "$tmp/home/.codex/agents/$agent.toml" \
    "Codex install must render xhigh reasoning for $agent"
done
grep_required '<!-- TEAMWORK_CODEX_GLOBAL_START -->' "$tmp/home/.codex/AGENTS.md" \
  "Codex install must create Teamwork global AGENTS block"
grep_required 'Teamwork Codex Global Policy' "$tmp/home/.codex/AGENTS.md" \
  "Codex install must write Teamwork global policy heading"
grep_required 'Agent efficiency comes first' "$tmp/home/.codex/AGENTS.md" \
  "Codex global policy must prioritize agent efficiency"
grep_required 'Codex model profile: default is performance-first' "$tmp/home/.codex/AGENTS.md" \
  "Codex global policy must record performance-first profile"
grep_required 'Bootstrap safety:' "$tmp/home/.codex/AGENTS.md" \
  "Codex global policy must include bootstrap fail-fast safety"
grep_required 'Remote execution:' "$tmp/home/.codex/AGENTS.md" \
  "Codex global policy must include remote execution default"
grep_required 'do not invent missing execution targets' "$tmp/home/.codex/AGENTS.md" \
  "Codex global policy must forbid invented remote targets"

agents_preserve_home="$tmp/home-agents-preserve"
mkdir -p "$agents_preserve_home/.codex"
cat > "$agents_preserve_home/.codex/AGENTS.md" <<'AGENTS'
Personal rule before.

<!-- TEAMWORK_CODEX_GLOBAL_START -->
old managed content
<!-- TEAMWORK_CODEX_GLOBAL_END -->

No user needs to specify sub-agents for distribution; default assignment is used.

All code runs on a remote server; the local environment only supports basic testing and syntax checking.

<!-- CODEGRAPH_START -->
Keep CodeGraph instructions.
<!-- CODEGRAPH_END -->
AGENTS
HOME="$agents_preserve_home" "$ROOT/install.sh" codex >/dev/null
grep_required 'Personal rule before.' "$agents_preserve_home/.codex/AGENTS.md" \
  "Codex global policy install must preserve user content"
grep_required '<!-- CODEGRAPH_START -->' "$agents_preserve_home/.codex/AGENTS.md" \
  "Codex global policy install must preserve CodeGraph block"
grep_required 'Agent efficiency comes first' "$agents_preserve_home/.codex/AGENTS.md" \
  "Codex global policy install must replace managed block"
grep_required 'Bootstrap safety:' "$agents_preserve_home/.codex/AGENTS.md" \
  "Codex global policy install must include bootstrap fail-fast safety"
grep_absent 'old managed content' \
  "Codex global policy install must replace old managed content" \
  "$agents_preserve_home/.codex/AGENTS.md"
grep_absent 'No user needs to specify sub-agents' \
  "Codex global policy install must remove retired subagent sentence" \
  "$agents_preserve_home/.codex/AGENTS.md"
grep_absent 'All code runs on a remote server' \
  "Codex global policy install must migrate retired remote sentence" \
  "$agents_preserve_home/.codex/AGENTS.md"

codex_policy_out="$tmp/codex-policy.out"
HOME="$tmp/home-codex-policy" "$ROOT/install.sh" codex-policy > "$codex_policy_out"
grep_required '<!-- TEAMWORK_CODEX_GLOBAL_START -->' "$codex_policy_out" \
  "codex-policy target must print Teamwork global policy start marker"
grep_required 'Codex model profile: default is performance-first' "$codex_policy_out" \
  "codex-policy target must render performance-first profile"
grep_required 'Bootstrap safety:' "$codex_policy_out" \
  "codex-policy target must print bootstrap fail-fast safety"
[[ ! -e "$tmp/home-codex-policy/.codex/AGENTS.md" ]] \
  || fail "codex-policy target must not write global AGENTS policy"

HOME="$tmp/home-codex-agents" "$ROOT/install.sh" codex-agents >/dev/null
for agent in teamwork-explorer teamwork-worker teamwork-designer teamwork-judge teamwork-reviewer teamwork-deep-judge teamwork-deep-reviewer; do
  [[ -f "$tmp/home-codex-agents/.codex/agents/$agent.toml" ]] \
    || fail "Codex agent install missing $agent"
  [[ ! -L "$tmp/home-codex-agents/.codex/agents/$agent.toml" ]] \
    || fail "default Codex agent install must copy $agent"
done
for agent in teamwork-explorer teamwork-worker teamwork-designer; do
  grep_required '^model = "gpt-5.5"$' "$tmp/home-codex-agents/.codex/agents/$agent.toml" \
    "default Codex agent install must render performance model for $agent"
  grep_required '^model_reasoning_effort = "medium"$' "$tmp/home-codex-agents/.codex/agents/$agent.toml" \
    "default Codex agent install must render medium reasoning for $agent"
done
for agent in teamwork-judge teamwork-reviewer; do
  grep_required '^model = "gpt-5.5"$' "$tmp/home-codex-agents/.codex/agents/$agent.toml" \
    "default Codex agent install must render frontier model for $agent"
  grep_required '^model_reasoning_effort = "high"$' "$tmp/home-codex-agents/.codex/agents/$agent.toml" \
    "default Codex agent install must render high reasoning for $agent"
done
for agent in teamwork-deep-judge teamwork-deep-reviewer; do
  grep_required '^model = "gpt-5.5"$' "$tmp/home-codex-agents/.codex/agents/$agent.toml" \
    "default Codex agent install must render frontier model for $agent"
  grep_required '^model_reasoning_effort = "xhigh"$' "$tmp/home-codex-agents/.codex/agents/$agent.toml" \
    "default Codex agent install must render xhigh reasoning for $agent"
done
[[ ! -e "$tmp/home-codex-agents/.codex/AGENTS.md" ]] \
  || fail "codex-agents target must not write global AGENTS policy"

HOME="$tmp/home-codex-agents-cost" "$ROOT/install.sh" --profile cost-first codex-agents >/dev/null
for agent in teamwork-explorer teamwork-worker teamwork-designer; do
  grep_required '^model = "gpt-5.4"$' "$tmp/home-codex-agents-cost/.codex/agents/$agent.toml" \
    "cost-first Codex agent install must downshift $agent"
  grep_required '^model_reasoning_effort = "medium"$' "$tmp/home-codex-agents-cost/.codex/agents/$agent.toml" \
    "cost-first Codex agent install must use medium reasoning for $agent"
done
for agent in teamwork-judge teamwork-reviewer; do
  grep_required '^model = "gpt-5.5"$' "$tmp/home-codex-agents-cost/.codex/agents/$agent.toml" \
    "cost-first Codex agent install must keep frontier model for $agent"
  grep_required '^model_reasoning_effort = "high"$' "$tmp/home-codex-agents-cost/.codex/agents/$agent.toml" \
    "cost-first Codex agent install must keep high reasoning for $agent"
done
for agent in teamwork-deep-judge teamwork-deep-reviewer; do
  grep_required '^model = "gpt-5.5"$' "$tmp/home-codex-agents-cost/.codex/agents/$agent.toml" \
    "cost-first Codex agent install must keep frontier model for $agent"
  grep_required '^model_reasoning_effort = "xhigh"$' "$tmp/home-codex-agents-cost/.codex/agents/$agent.toml" \
    "cost-first Codex agent install must keep xhigh reasoning for $agent"
done

HOME="$tmp/home-codex-cost" "$ROOT/install.sh" --profile cost-first codex >/dev/null
grep_required 'Codex model profile: default is cost-first' "$tmp/home-codex-cost/.codex/AGENTS.md" \
  "Codex global policy must record cost-first profile"

HOME="$tmp/home-codex-policy-cost" "$ROOT/install.sh" --profile cost-first codex-policy > "$tmp/codex-policy-cost.out"
grep_required 'Codex model profile: default is cost-first' "$tmp/codex-policy-cost.out" \
  "codex-policy target must render cost-first profile"
[[ ! -e "$tmp/home-codex-policy-cost/.codex/AGENTS.md" ]] \
  || fail "cost-first codex-policy target must not write global AGENTS policy"

HOME="$tmp/home-invalid-profile" "$ROOT/install.sh" --profile invalid codex >/dev/null 2>&1 \
  && fail "installer must reject unsupported Codex profiles"

HOME="$tmp/home-codex-agents-link" "$ROOT/install.sh" --link codex-agents >/dev/null
for agent in teamwork-explorer teamwork-worker teamwork-designer teamwork-judge teamwork-reviewer teamwork-deep-judge teamwork-deep-reviewer; do
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
for agent in teamwork-explorer teamwork-worker teamwork-designer teamwork-judge teamwork-reviewer teamwork-deep-judge teamwork-deep-reviewer; do
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
for agent in teamwork-explorer teamwork-worker teamwork-designer teamwork-judge teamwork-reviewer teamwork-deep-judge teamwork-deep-reviewer; do
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
