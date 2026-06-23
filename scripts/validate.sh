#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENTRYPOINT="$ROOT/skills/using-teamwork/SKILL.md"
SKILLS=(
  using-teamwork
  teamwork-debug
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

git_known_package_file() {
  local path="$1"
  git -C "$ROOT" ls-files --error-unmatch "$path" >/dev/null 2>&1 && return 0
  return 1
}

# --- Package layout ---
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
[[ -f "$ROOT/CHANGELOG.md" ]] || fail "missing CHANGELOG.md"
git_known_package_file "CHANGELOG.md" || fail "CHANGELOG.md is not known to git; use git add -N before release validation"

[[ -f "$ROOT/VERSION" ]] || fail "missing VERSION"
git_known_package_file "VERSION" || fail "VERSION is not known to git; use git add -N before release validation"
grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+$' "$ROOT/VERSION" || fail "VERSION must be plain semver"

if git -C "$ROOT" ls-files 'docs/teamwork/plans/*' 'docs/teamwork/research/*' 'docs/teamwork/reports/*' 'docs/teamwork/workflows/*' | grep -q .; then
  fail "local workflow artifacts under docs/teamwork/{plans,research,reports,workflows}/ must not be tracked"
fi
grep_required '^docs/teamwork/plans/$' "$ROOT/.gitignore" ".gitignore must ignore local Teamwork plan artifacts"
grep_required '^docs/teamwork/research/$' "$ROOT/.gitignore" ".gitignore must ignore local Teamwork research artifacts"
grep_required '^docs/teamwork/reports/$' "$ROOT/.gitignore" ".gitignore must ignore local Teamwork report artifacts"
grep_required '^docs/teamwork/workflows/$' "$ROOT/.gitignore" ".gitignore must ignore local Teamwork workflow artifacts"

# --- Skill frontmatter ---
for skill in "${SKILLS[@]}"; do
  file="$ROOT/skills/$skill/SKILL.md"
  [[ -f "$file" ]] || fail "missing skills/$skill/SKILL.md"
  git_known_package_file "skills/$skill/SKILL.md" \
    || fail "skills/$skill/SKILL.md is not known to git; use git add -N before release validation"
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

for subskill in teamwork-debug teamwork-init teamwork-goal teamwork-research teamwork-plan teamwork-execute teamwork-review teamwork-update; do
  grep_required "skills/$subskill/SKILL.md" "$ENTRYPOINT" "entrypoint/router does not reference skills/$subskill/SKILL.md"
done

# --- Reference inventory ---
for reference in artifact-protocol debug-mode goal-iteration optional-skills plan-output project-init research-protocol review-checks review-lenses role-playbook routing-policy subagent-contract subagent-dispatch verification-patterns workflow-contract workflow-orchestration; do
  ref_file="$ROOT/skills/using-teamwork/references/$reference.md"
  [[ -f "$ref_file" ]] || fail "missing skills/using-teamwork/references/$reference.md"
  git_known_package_file "skills/using-teamwork/references/$reference.md" \
    || fail "skills/using-teamwork/references/$reference.md is not known to git; use git add -N before release validation"
done

for template in teamwork-index-template.json teamwork-index-readme-template.md teamwork-current-template.md; do
  template_file="$ROOT/skills/using-teamwork/references/$template"
  [[ -f "$template_file" ]] || fail "missing skills/using-teamwork/references/$template"
  git_known_package_file "skills/using-teamwork/references/$template" \
    || fail "skills/using-teamwork/references/$template is not known to git; use git add -N before release validation"
done

expected_reference_inventory="$(
  printf '%s\n' \
    artifact-protocol.md check-update.md debug-mode.md goal-iteration.md optional-skills.md plan-output.md \
    project-init.md research-protocol.md review-checks.md review-lenses.md role-playbook.md routing-policy.md \
    subagent-contract.md subagent-dispatch.md teamwork-current-template.md \
    teamwork-index-readme-template.md teamwork-index-template.json \
    verification-patterns.md workflow-contract.md workflow-orchestration.md | sort
)"
actual_reference_inventory="$(
  find "$ROOT/skills/using-teamwork/references" -maxdepth 1 -type f \
    -exec basename {} \; | sort
)"
[[ "$actual_reference_inventory" == "$expected_reference_inventory" ]] \
  || fail "using-teamwork references inventory drifted"

[[ -f "$ROOT/scripts/validate_teamwork_index.py" ]] || fail "missing scripts/validate_teamwork_index.py"
git_known_package_file "scripts/validate_teamwork_index.py" \
  || fail "scripts/validate_teamwork_index.py is not known to git; use git add -N before release validation"
python3 "$ROOT/scripts/validate_teamwork_index.py" \
  "$ROOT/skills/using-teamwork/references/teamwork-index-template.json" >/dev/null
if [[ -f "$ROOT/docs/teamwork/index.json" ]]; then
  python3 "$ROOT/scripts/validate_teamwork_index.py" "$ROOT/docs/teamwork/index.json" >/dev/null
fi

# --- Plugin manifests ---
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

# --- Top-level docs ---
grep_required 'Codex + Cursor + Claude Code' "$ROOT/README.md" "README must state Codex + Cursor + Claude Code positioning"
grep_required 'teamwork-update' "$ROOT/README.md" "README must document teamwork-update"
grep_required 'check-update.sh' "$ROOT/README.md" "README must document check-update script"
grep_required 'teamwork-init' "$ROOT/README.md" "README must document teamwork-init"
grep_required 'VERSION' "$ROOT/README.md" "README must document package version source"
grep_required '\[English\](README.en.md)' "$ROOT/README.md" "default README must link to English README"
grep_required 'docs/teamwork/research/YYYY-MM-DD-<slug>.md' "$ROOT/README.md" "README must document research artifact path"
grep_required 'docs/teamwork/plans/YYYY-MM-DD-<slug>.md' "$ROOT/README.md" "README must document plan artifact path"
grep_required 'docs/teamwork/reports/YYYY-MM-DD-<slug>.md' "$ROOT/README.md" "README must document report artifact path"
grep_required './install.sh --link codex' "$ROOT/README.md" "README must document Codex link-mode development install"
grep_required '^# Changelog' "$ROOT/CHANGELOG.md" "CHANGELOG must have a top-level heading"
grep_required "## $(tr -d '[:space:]' < "$ROOT/VERSION") -" "$ROOT/CHANGELOG.md" "CHANGELOG must document current VERSION"
[[ -f "$ROOT/README.en.md" ]] || fail "missing English README"
git -C "$ROOT" ls-files --error-unmatch "README.en.md" >/dev/null 2>&1 || fail "README.en.md must be tracked by git"
grep_required '\[中文\](README.md)' "$ROOT/README.en.md" "English README must link to default Chinese README"
grep_required 'Codex + Cursor + Claude Code' "$ROOT/README.en.md" "English README must state Codex + Cursor + Claude Code positioning"
grep_required 'teamwork-update' "$ROOT/README.en.md" "English README must document teamwork-update"
grep_required 'check-update.sh' "$ROOT/README.en.md" "English README must document check-update script"
grep_required 'VERSION' "$ROOT/README.en.md" "English README must document package version source"
grep_required './install.sh --link codex' "$ROOT/README.en.md" "English README must document Codex link-mode development install"
grep_required 'Codex + Cursor + Claude Code skill package' "$ROOT/AGENTS.md" "AGENTS.md must describe the package"
grep_required 'teamwork-update' "$ROOT/AGENTS.md" "AGENTS.md must document update skill ownership"
grep_required 'check-update.sh' "$ROOT/AGENTS.md" "AGENTS.md must document check-update script"
grep_required 'teamwork-init' "$ROOT/AGENTS.md" "AGENTS.md must document init skill ownership"
grep_required 'Codex native capabilities' "$ROOT/CODEX.md" "CODEX.md must document native Codex capability policy"
grep_required 'Codex runtime profile' "$ROOT/CODEX.md" "CODEX.md must identify itself as the Codex runtime profile"
grep_required 'VERSION' "$ROOT/CODEX.md" "CODEX.md must document package version source"
grep_required 'teamwork-init' "$ROOT/CODEX.md" "CODEX.md must document teamwork-init"
grep_required 'subagent-dispatch.md' "$ROOT/CODEX.md" "CODEX.md must point to subagent dispatch reference"
grep_required 'Task' "$ROOT/CURSOR.md" "CURSOR.md must document Cursor Task subagent policy"
grep_required 'Goal Mode' "$ROOT/CURSOR.md" "CURSOR.md must document Cursor goal mode"
grep_required 'subagent-dispatch.md' "$ROOT/CURSOR.md" "CURSOR.md must point to subagent dispatch reference"
grep_required '~/.cursor/agents/' "$ROOT/CURSOR.md" "CURSOR.md must document Cursor custom agents"
grep_required 'cursor-policy' "$ROOT/CURSOR.md" "CURSOR.md must document cursor-policy target"
grep_required 'Claude Code native capabilities' "$ROOT/CLAUDE.md" "CLAUDE.md must document native Claude Code capability policy"
grep_required 'Task' "$ROOT/CLAUDE.md" "CLAUDE.md must document Claude Code Task subagent policy"
grep_required 'subagent-dispatch.md' "$ROOT/CLAUDE.md" "CLAUDE.md must point to subagent dispatch reference"
grep_required 'rolling report' "$ROOT/CLAUDE.md" "CLAUDE.md must document Claude Code goal rolling report"
grep_required 'VERSION' "$ROOT/CLAUDE.md" "CLAUDE.md must document package version source"
grep_required '~/.claude/CLAUDE.md' "$ROOT/CLAUDE.md" "CLAUDE.md must document Claude global policy"
grep_required 'claude-policy' "$ROOT/CLAUDE.md" "CLAUDE.md must document claude-policy target"
grep_required 'deep-judge' "$ROOT/CLAUDE.md" "CLAUDE.md must document Deep Judge agent"

# --- Installer global policy ---
grep_required 'write_teamwork_codex_global_policy()' "$ROOT/install.sh" "installer must define Teamwork Codex global policy writer"
grep_required 'write_teamwork_claude_global_policy()' "$ROOT/install.sh" "installer must define Teamwork Claude global policy writer"
grep_required 'write_teamwork_cursor_global_policy()' "$ROOT/install.sh" "installer must define Teamwork Cursor global policy writer"
grep_required '<!-- TEAMWORK_CODEX_GLOBAL_START -->' "$ROOT/install.sh" "installer global policy writer must include managed start marker"
grep_required '<!-- TEAMWORK_CLAUDE_GLOBAL_START -->' "$ROOT/install.sh" "installer Claude global policy writer must include managed start marker"
grep_required '<!-- TEAMWORK_CURSOR_GLOBAL_START -->' "$ROOT/install.sh" "installer Cursor global policy writer must include managed start marker"
grep_required 'install_codex_global_policy' "$ROOT/install.sh" "installer must call Codex global policy install from Codex target"
grep_required 'install_claude_global_policy' "$ROOT/install.sh" "installer must call Claude global policy install from Claude target"
grep_required 'install_cursor_agent_set' "$ROOT/install.sh" "installer must define Cursor agent install set"
grep_required 'cursor-agents' "$ROOT/install.sh" "installer must support cursor-agents target"
grep_required 'cursor-policy' "$ROOT/install.sh" "installer must support cursor-policy target"
grep_required 'cursor-policy-copy' "$ROOT/install.sh" "installer must support cursor-policy-copy target"
grep_required 'claude-policy' "$ROOT/install.sh" "installer must support claude-policy target"

# --- Budgets ---
[[ "$(wc -l < "$ROOT/README.md")" -le 195 ]] || fail "README should stay concise"
[[ "$(wc -l < "$ROOT/README.en.md")" -le 200 ]] || fail "English README should stay concise"
line_count_max "$ROOT/skills/using-teamwork/SKILL.md" 80 "using-teamwork should stay concise"
word_count_max "$ROOT/skills/using-teamwork/SKILL.md" 450 "using-teamwork should stay concise"
line_count_max "$ROOT/skills/teamwork-init/SKILL.md" 95 "teamwork-init should stay concise"
word_count_max "$ROOT/skills/teamwork-init/SKILL.md" 650 "teamwork-init should stay concise"
line_count_max "$ROOT/skills/teamwork-debug/SKILL.md" 85 "teamwork-debug should stay concise"
word_count_max "$ROOT/skills/teamwork-debug/SKILL.md" 560 "teamwork-debug should stay concise"
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
line_count_max "$ROOT/skills/teamwork-update/SKILL.md" 70 "teamwork-update should stay concise"
word_count_max "$ROOT/skills/teamwork-update/SKILL.md" 450 "teamwork-update should stay concise"
line_count_max "$ROOT/skills/using-teamwork/references/workflow-contract.md" 150 "workflow contract reference should stay focused"
word_count_max "$ROOT/skills/using-teamwork/references/workflow-contract.md" 950 "workflow contract reference should stay focused"
line_count_max "$ROOT/skills/using-teamwork/references/subagent-dispatch.md" 150 "subagent dispatch reference should stay focused"
word_count_max "$ROOT/skills/using-teamwork/references/subagent-dispatch.md" 1050 "subagent dispatch reference should stay focused"
line_count_max "$ROOT/skills/using-teamwork/references/subagent-contract.md" 145 "subagent contract reference should stay focused"
word_count_max "$ROOT/skills/using-teamwork/references/subagent-contract.md" 600 "subagent contract reference should stay focused"
line_count_max "$ROOT/skills/using-teamwork/references/debug-mode.md" 85 "debug mode reference should stay focused"
word_count_max "$ROOT/skills/using-teamwork/references/debug-mode.md" 520 "debug mode reference should stay focused"
line_count_max "$ROOT/skills/using-teamwork/references/verification-patterns.md" 80 "verification patterns reference should stay focused"
word_count_max "$ROOT/skills/using-teamwork/references/verification-patterns.md" 560 "verification patterns reference should stay focused"
line_count_max "$ROOT/skills/using-teamwork/references/review-lenses.md" 85 "review lenses reference should stay focused"
word_count_max "$ROOT/skills/using-teamwork/references/review-lenses.md" 620 "review lenses reference should stay focused"
line_count_max "$ROOT/skills/using-teamwork/references/routing-policy.md" 70 "routing policy reference should stay focused"
word_count_max "$ROOT/skills/using-teamwork/references/routing-policy.md" 520 "routing policy reference should stay focused"
line_count_max "$ROOT/skills/using-teamwork/references/role-playbook.md" 100 "role playbook reference should stay focused"
word_count_max "$ROOT/skills/using-teamwork/references/role-playbook.md" 650 "role playbook reference should stay focused"
line_count_max "$ROOT/skills/using-teamwork/references/artifact-protocol.md" 120 "artifact protocol reference should stay focused"
word_count_max "$ROOT/skills/using-teamwork/references/artifact-protocol.md" 780 "artifact protocol reference should stay focused"
line_count_max "$ROOT/skills/using-teamwork/references/goal-iteration.md" 90 "goal iteration reference should stay focused"
word_count_max "$ROOT/skills/using-teamwork/references/goal-iteration.md" 520 "goal iteration reference should stay focused"
line_count_max "$ROOT/skills/using-teamwork/references/plan-output.md" 90 "plan output reference should stay focused"
word_count_max "$ROOT/skills/using-teamwork/references/plan-output.md" 460 "plan output reference should stay focused"
line_count_max "$ROOT/skills/using-teamwork/references/review-checks.md" 60 "review checks reference should stay focused"
word_count_max "$ROOT/skills/using-teamwork/references/review-checks.md" 460 "review checks reference should stay focused"
line_count_max "$ROOT/skills/using-teamwork/references/project-init.md" 85 "project init reference should stay focused"
word_count_max "$ROOT/skills/using-teamwork/references/project-init.md" 650 "project init reference should stay focused"
line_count_max "$ROOT/skills/using-teamwork/references/check-update.md" 70 "check update reference should stay focused"
word_count_max "$ROOT/skills/using-teamwork/references/check-update.md" 500 "check update reference should stay focused"
line_count_max "$ROOT/skills/using-teamwork/references/research-protocol.md" 60 "research protocol reference should stay focused"
word_count_max "$ROOT/skills/using-teamwork/references/research-protocol.md" 430 "research protocol reference should stay focused"
line_count_max "$ROOT/skills/using-teamwork/references/optional-skills.md" 60 "optional skills reference should stay focused"
word_count_max "$ROOT/skills/using-teamwork/references/optional-skills.md" 430 "optional skills reference should stay focused"
line_count_max "$ROOT/skills/using-teamwork/references/workflow-orchestration.md" 70 "workflow orchestration reference should stay focused"
word_count_max "$ROOT/skills/using-teamwork/references/workflow-orchestration.md" 450 "workflow orchestration reference should stay focused"
for skill in "${SKILLS[@]}"; do
  fenced_block_line_count_max "$ROOT/skills/$skill/SKILL.md" 20 "$skill must not embed large fenced templates"
done

# --- Router + stage anchors ---
grep_required 'references/workflow-contract.md' "$ENTRYPOINT" "using-teamwork must reference shared workflow contract"
grep_required 'routing-policy.md' "$ENTRYPOINT" "using-teamwork must reference routing policy for ambiguous intent"
grep_required 'references/subagent-dispatch.md' "$ENTRYPOINT" "using-teamwork must reference subagent dispatch"
for skill in teamwork-debug teamwork-init teamwork-goal teamwork-research teamwork-plan teamwork-execute teamwork-review; do
  grep_absent '`references/' "$skill must not use sibling-local reference paths" "$ROOT/skills/$skill/SKILL.md"
  grep_absent '^- `references/' "$skill must not list sibling-local reference paths" "$ROOT/skills/$skill/SKILL.md"
  grep_required 'skills/using-teamwork/references/workflow-contract.md' "$ROOT/skills/$skill/SKILL.md" "$skill must reference shared workflow contract"
done
grep_required 'Debug' "$ENTRYPOINT" "using-teamwork router must name the Debug stage"
grep_required 'skills/teamwork-debug/SKILL.md' "$ENTRYPOINT" "using-teamwork router must reference teamwork-debug"
grep_required 'skills/using-teamwork/references/workflow-contract.md' "$ROOT/skills/teamwork-debug/SKILL.md" "teamwork-debug must reference shared workflow contract"
grep_required 'debug-mode.md' "$ROOT/skills/teamwork-debug/SKILL.md" "teamwork-debug must reference the shared debug protocol"
grep_required 'verification-patterns.md' "$ROOT/skills/teamwork-debug/SKILL.md" "teamwork-debug must reference verification patterns"
grep_required 'verification-patterns.md' "$ROOT/skills/teamwork-plan/SKILL.md" "teamwork-plan must reference verification patterns"
grep_required 'verification-patterns.md' "$ROOT/skills/teamwork-execute/SKILL.md" "teamwork-execute must reference verification patterns"
grep_required 'verification-patterns.md' "$ROOT/skills/teamwork-review/SKILL.md" "teamwork-review must reference verification patterns"
grep_required 'review-lenses.md' "$ROOT/skills/teamwork-review/SKILL.md" "teamwork-review must reference review lenses"
grep_required 'repro-surface framing' "$ROOT/skills/teamwork-research/SKILL.md" "research trigger must stop before runtime diagnosis"
grep_required 'one bounded micro-debug pass' "$ROOT/skills/teamwork-execute/SKILL.md" "execute must bound local micro-debugging"
for anchor in Repro Hypotheses Instrumentation 'Runtime Evidence' Cleanup; do
  grep_required "$anchor" "$ROOT/skills/using-teamwork/references/debug-mode.md" "debug-mode must lock $anchor"
done
grep_required 'Wrong-surface or inconclusive checks are not a pass' "$ROOT/skills/using-teamwork/references/debug-mode.md" "debug-mode must preserve same-surface verification"
for anchor in 'Verification Strength' 'Baseline / Treatment' 'VERIFIED' 'NOT VERIFIED' 'INCONCLUSIVE'; do
  grep_required "$anchor" "$ROOT/skills/using-teamwork/references/verification-patterns.md" "verification patterns must lock $anchor"
done
for anchor in Deslop 'Strict Maintainability' 'Reviewer Comprehension' 'Multi-Lens Review'; do
  grep_required "$anchor" "$ROOT/skills/using-teamwork/references/review-lenses.md" "review lenses must lock $anchor"
done
grep_required 'No silent defaults or invariant-masking fallback' "$ROOT/skills/using-teamwork/references/workflow-contract.md" "workflow contract must define invariant-masking fallback"
grep_required 'Required Values / Invariants' "$ROOT/skills/using-teamwork/references/plan-output.md" "plan output must lock required values and invariants"
grep_required 'Fail fast rather than invent fallback behavior' "$ROOT/skills/teamwork-execute/SKILL.md" "execute must fail fast instead of masking invariants"
grep_required 'Allowed Fail-Fast Checks' "$ROOT/skills/using-teamwork/references/review-lenses.md" "review lenses must distinguish fail-fast from defensive masking"
grep_required 'fallback masking' "$ROOT/skills/using-teamwork/references/review-checks.md" "review checks must catch fallback masking"
grep_absent 'teamwork-quality' "Teamwork must not add a separate quality stage" "$ROOT/skills" "$ROOT/CODEX.md" "$ROOT/CURSOR.md" "$ROOT/CLAUDE.md" "$ROOT/install.sh"
grep_absent 'teamwork-deslop' "Teamwork must not add a separate deslop stage" "$ROOT/skills" "$ROOT/CODEX.md" "$ROOT/CURSOR.md" "$ROOT/CLAUDE.md" "$ROOT/install.sh"
for anchor in 'Natural Signals' 'Tie-Breakers' 'User does not need to say' 'Symptom with unknown cause'; do
  grep_required "$anchor" "$ROOT/skills/using-teamwork/references/routing-policy.md" "routing policy must lock $anchor"
done
grep_absent 'Stage: teamwork-debug' "subagent contract must not define stage-local Debug output" "$ROOT/skills/using-teamwork/references/subagent-contract.md"
grep_absent 'Debug Findings Output' "subagent contract must not define stage-local Debug output" "$ROOT/skills/using-teamwork/references/subagent-contract.md"

grep_required 'check-update.md' "$ROOT/skills/teamwork-init/SKILL.md" "teamwork-init must reference check-update"
grep_required 'check-update.md' "$ROOT/skills/teamwork-update/SKILL.md" "teamwork-update must reference check-update"
grep_required 'check-update.sh' "$ROOT/skills/teamwork-update/SKILL.md" "teamwork-update must reference check-update script"
[[ -x "$ROOT/scripts/check-update.sh" ]] || fail "check-update script must be executable"
grep_required 'Verdict: accept | revise | blocked' "$ROOT/skills/teamwork-review/SKILL.md" "review skill verdict enum must match Reviewer Verdict Packet"
grep_absent 'Verdict: pass | pass-with-notes' "review skill must not use stale verdict enum" "$ROOT/skills/teamwork-review/SKILL.md"
grep_required 'Reject open delegated tracks' "$ROOT/skills/teamwork-review/SKILL.md" "review skill must reject open delegated tracks"
grep_required 'closed dispatch log or continuity' "$ROOT/skills/teamwork-research/SKILL.md" "research handoff must close delegated tracks"
grep_required 'Closure Evidence after integration' "$ROOT/skills/teamwork-execute/SKILL.md" "execute skill must close Worker tracks after integration"
grep_required 'closes or' "$ROOT/skills/teamwork-goal/SKILL.md" "goal loop must close or block delegated tracks before retry"

# --- Shared contract anchors ---
grep_required 'returns one packet, then stop' "$ROOT/skills/using-teamwork/references/workflow-contract.md" "workflow contract must define bounded subagent lifecycle"
grep_required 'abandoned-after-discovery' "$ROOT/skills/using-teamwork/references/workflow-contract.md" "workflow contract must use canonical abandoned-after-discovery status"

# --- Subagent dispatch anchors ---
grep_required 'When To Dispatch' "$ROOT/skills/using-teamwork/references/subagent-dispatch.md" "subagent dispatch must document when to dispatch"
grep_required 'returns one packet, then stop' "$ROOT/skills/using-teamwork/references/subagent-dispatch.md" "subagent dispatch must define bounded lifecycle"
grep_required 'abandoned-after-discovery' "$ROOT/skills/using-teamwork/references/subagent-dispatch.md" "subagent dispatch must use canonical closure status"
grep_required 'agent_type' "$ROOT/skills/using-teamwork/references/subagent-dispatch.md" "subagent dispatch must map Codex fields"
grep_required 'subagent_type' "$ROOT/skills/using-teamwork/references/subagent-dispatch.md" "subagent dispatch must map Cursor fields"
grep_required 'Custom agent' "$ROOT/skills/using-teamwork/references/subagent-dispatch.md" "subagent dispatch must map Cursor custom agents"
grep_required 'effort' "$ROOT/skills/using-teamwork/references/subagent-dispatch.md" "subagent dispatch must document Claude effort"

# --- Subagent contract anchors ---
grep_required 'Worker Completion Packet' "$ROOT/skills/using-teamwork/references/subagent-contract.md" "subagent contract must define Worker packet"
grep_required 'Reviewer Verdict Packet' "$ROOT/skills/using-teamwork/references/subagent-contract.md" "subagent contract must define Reviewer packet"
grep_required 'Verdict: accept | revise | blocked' "$ROOT/skills/using-teamwork/references/subagent-contract.md" "subagent contract verdict enum"
grep_required 'Status: done | done_with_concerns | blocked | needs_context' "$ROOT/skills/using-teamwork/references/subagent-contract.md" "subagent contract worker status enum"
grep_required 'Closure Evidence' "$ROOT/skills/using-teamwork/references/subagent-contract.md" "subagent contract must record dispatch closure evidence"
grep_required 'dispatched -> returned -> closed' "$ROOT/skills/using-teamwork/references/subagent-contract.md" "subagent contract must define dispatch transitions"
grep_required 'Final status cannot remain' "$ROOT/skills/using-teamwork/references/subagent-contract.md" "subagent contract must forbid open final dispatch status"
grep_required 'Memory Delta Candidate' "$ROOT/skills/using-teamwork/references/subagent-contract.md" "subagent contract must document optional Memory Delta Candidate"
grep_required 'Subagents propose memory candidates only' "$ROOT/skills/using-teamwork/references/subagent-contract.md" "subagent contract must prevent subagents from promoting memory"

# --- Role playbook anchors ---
for role in Explorer Designer Judge Worker Reviewer; do
  grep_required "## $role" "$ROOT/skills/using-teamwork/references/role-playbook.md" "role playbook must define $role"
done
grep_required 'research-protocol.md' "$ROOT/skills/using-teamwork/references/role-playbook.md" "role playbook Explorer must point to research protocol"

# --- Memory + review anchors ---
grep_required 'Memory Delta' "$ROOT/skills/using-teamwork/references/artifact-protocol.md" "artifact protocol must define Memory Delta"
grep_required 'Search Keys' "$ROOT/skills/using-teamwork/references/artifact-protocol.md" "artifact protocol must define Search Keys"
grep_required 'docs/teamwork/index.json' "$ROOT/skills/using-teamwork/references/artifact-protocol.md" "artifact protocol must document index routing"
grep_required 'schema_version' "$ROOT/skills/using-teamwork/references/artifact-protocol.md" "artifact protocol must document index schema"
grep_required 'active.goal' "$ROOT/skills/using-teamwork/references/artifact-protocol.md" "artifact protocol must document active.goal"
grep_required 'active.report' "$ROOT/skills/using-teamwork/references/artifact-protocol.md" "artifact protocol must document active.report"
grep_required 'Structured Bodies' "$ROOT/skills/using-teamwork/references/artifact-protocol.md" "artifact protocol must require structured artifact bodies"
grep_required 'Research artifacts should' "$ROOT/skills/using-teamwork/references/artifact-protocol.md" "artifact protocol must require research matrices"
grep_required 'Report artifacts should' "$ROOT/skills/using-teamwork/references/artifact-protocol.md" "artifact protocol must require report tables"
grep_required 'Seed Expansion' "$ROOT/skills/teamwork-research/SKILL.md" "research skill must require seeded-source expansion"
grep_required 'Seed Expansion' "$ROOT/skills/using-teamwork/references/research-protocol.md" "research protocol must define Seed Expansion"
grep_required 'Coverage Audit' "$ROOT/skills/using-teamwork/references/subagent-contract.md" "Explorer packet must carry coverage audit"
grep_required 'broad/seeded research' "$ROOT/skills/using-teamwork/references/review-checks.md" "review checks must catch shallow seeded research"
grep_required 'Evidence Matrix' "$ROOT/skills/using-teamwork/references/research-protocol.md" "research protocol must require evidence matrix"
grep_required 'Option Matrix' "$ROOT/skills/using-teamwork/references/research-protocol.md" "research protocol must require option matrix"
grep_required 'Goal Proposal' "$ROOT/skills/using-teamwork/references/goal-iteration.md" "goal iteration must define Goal Proposal"
grep_required 'Research + Plan Adequacy Gate' "$ROOT/skills/using-teamwork/references/goal-iteration.md" "goal iteration must define adequacy gate"
grep_required 'Goal Invariants' "$ROOT/skills/using-teamwork/references/goal-iteration.md" "goal iteration must preserve Goal Invariants"
grep_required 'Replay Preflight' "$ROOT/skills/using-teamwork/references/goal-iteration.md" "goal iteration must require Replay Preflight"
grep_required 'Attempt Record' "$ROOT/skills/using-teamwork/references/goal-iteration.md" "goal iteration must require Attempt Record"
grep_required 'Failure Reflection' "$ROOT/skills/using-teamwork/references/goal-iteration.md" "goal iteration must require Failure Reflection"
grep_required 'Mermaid for' "$ROOT/skills/using-teamwork/references/goal-iteration.md" "goal iteration reports must use diagrams when branching"
grep_required 'reject` is not a lifecycle verdict' "$ROOT/skills/using-teamwork/references/goal-iteration.md" "goal iteration must forbid reject as lifecycle verdict"
grep_required 'final status, closure evidence' "$ROOT/skills/using-teamwork/references/plan-output.md" "plan output must include dispatch closure evidence"
grep_required 'Goal Anchor' "$ROOT/skills/using-teamwork/references/plan-output.md" "plan output must include Goal Anchor"
grep_required 'Durable memory check' "$ROOT/skills/using-teamwork/references/review-checks.md" "review checks must include durable memory materiality checks"
grep_required 'Memory promotion check' "$ROOT/skills/using-teamwork/references/review-checks.md" "review checks must include memory promotion checks"
grep_required 'candidate memory' "$ROOT/skills/using-teamwork/references/review-checks.md" "review checks must keep external memory candidate-scoped"
grep_required 'Manual smoke evidence captures source' "$ROOT/skills/using-teamwork/references/review-checks.md" "review checks must include manual smoke evidence fields"
grep_required 'No delegated track remains dispatched or returned' "$ROOT/skills/using-teamwork/references/review-checks.md" "review checks must reject open delegated tracks"
grep_required 'Drift Verdict' "$ROOT/skills/using-teamwork/references/review-checks.md" "review checks must require goal drift verdict"
grep_required 'Retry Verdict' "$ROOT/skills/using-teamwork/references/review-checks.md" "review checks must require goal retry verdict"
grep_required 'Goal Anchor' "$ROOT/skills/using-teamwork/references/subagent-contract.md" "subagent contract must define Goal Anchor"
grep_required 'Drift Verdict' "$ROOT/skills/using-teamwork/references/subagent-contract.md" "subagent contract must define Drift Verdict"
grep_required 'Retry Verdict' "$ROOT/skills/using-teamwork/references/subagent-contract.md" "subagent contract must define Retry Verdict"
grep_required 'reject` is not a lifecycle verdict' "$ROOT/skills/using-teamwork/references/subagent-contract.md" "subagent contract must forbid reject as lifecycle verdict"

python3 - "$ROOT" <<'PY'
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1])
allowed = {"accept", "revise", "blocked"}
bad_packet = "Role: Reviewer\nVerdict: reject\n"
ok_packet = "Role: Reviewer\nVerdict: revise\n"
bad_match = re.search(r"^Verdict:\s*(\w+)\b", bad_packet, re.M)
ok_match = re.search(r"^Verdict:\s*(\w+)\b", ok_packet, re.M)
if not bad_match or bad_match.group(1) in allowed:
    raise SystemExit("FAIL: goal continuity smoke must catch reject lifecycle verdict")
if not ok_match or ok_match.group(1) not in allowed:
    raise SystemExit("FAIL: goal continuity smoke must allow revise lifecycle verdict")

required = {
    "skills/using-teamwork/references/goal-iteration.md": [
        "Goal Invariants", "Replay Preflight", "Attempt Record", "Failure Reflection", "Do Not Repeat"
    ],
    "skills/using-teamwork/references/plan-output.md": [
        "Goal Anchor", "Drift Verdict", "Retry Verdict", "Replay Preflight"
    ],
    "skills/using-teamwork/references/subagent-contract.md": [
        "Goal Anchor", "Prior Attempts Reviewed", "Drift Verdict", "Retry Verdict"
    ],
}
for rel, phrases in required.items():
    text = (root / rel).read_text()
    missing = [phrase for phrase in phrases if phrase not in text]
    if missing:
        raise SystemExit(f"FAIL: {rel} missing goal continuity anchors: {', '.join(missing)}")

for rel in [
    "skills/teamwork-review/SKILL.md",
    "skills/using-teamwork/references/subagent-contract.md",
]:
    text = (root / rel).read_text()
    if re.search(r"^Verdict:\s*reject\b", text, re.M):
        raise SystemExit(f"FAIL: {rel} defines reject as a lifecycle verdict")

def goal_retry_errors(text):
    failed = re.search(r"^Attempt Result:\s*(failed|partial|blocked|no-progress)\b", text, re.M)
    if not failed:
        return []
    required_fields = [
        "Goal Invariants",
        "Attempt Record",
        "Failure Reflection",
        "Replay Preflight",
        "Do Not Repeat",
        "Strategy Delta",
    ]
    errors = [field for field in required_fields if not re.search(rf"^{re.escape(field)}:", text, re.M)]
    invariants = re.search(r"^Goal Invariants:\s*(.+)$", text, re.M)
    invariant_text = invariants.group(1) if invariants else ""
    for term in ["不要过严过滤", "数据飞轮"]:
        if term in text and term not in invariant_text:
            errors.append(f"Goal Invariants missing {term}")
    return errors

bad_storyboard = """Goal Text: 端到端视频生成一致性诊断与优化
User Constraint: 不要过严过滤
Data Flywheel: 数据飞轮
Attempt Result: failed
Next Plan: reclassify cases
"""
if not goal_retry_errors(bad_storyboard):
    raise SystemExit("FAIL: goal continuity smoke must fail missing invariants/replay fields")

good_storyboard = """Goal Text: 端到端视频生成一致性诊断与优化
Goal Invariants: 端到端视频生成一致性诊断与优化; 不要过严过滤; 数据飞轮; remaining cases clean
Attempt Result: failed
Attempt Record: v20 kept weak cases but reject mixed unreviewed, ablation-only, readability-unchecked buckets
Failure Reflection: over-strict bucket semantics hid usable data; evidence delta from v5/v6/v8/v9/v20 reviewed
Replay Preflight: active goal/report and prior attempts reviewed
Do Not Repeat: use reject as catch-all lifecycle verdict or data bucket
Strategy Delta: split lifecycle verdict from data buckets and preserve weak/review candidates
"""
good_errors = goal_retry_errors(good_storyboard)
if good_errors:
    raise SystemExit(f"FAIL: goal continuity smoke rejected valid Storyboard fixture: {', '.join(good_errors)}")
PY

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
[[ "$(tr -d '[:space:]' < "$tmp/home/.codex/skills/.teamwork-version")" == "$(tr -d '[:space:]' < "$ROOT/VERSION")" ]] \
  || fail "Codex install must write .teamwork-version matching VERSION"
[[ -f "$tmp/home/.codex/skills/.teamwork-profile" ]] \
  || fail "Codex install must write .teamwork-profile"
HOME="$tmp/home" "$ROOT/scripts/check-update.sh" --readiness --no-fetch >/dev/null \
  || fail "check-update readiness must succeed after fresh install"
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
grep_required 'Act by default:' "$tmp/home/.codex/AGENTS.md" \
  "Codex global policy must prioritize acting by default"
grep_required 'Ask only when it matters:' "$tmp/home/.codex/AGENTS.md" \
  "Codex global policy must scope asking to core decisions"
grep_required 'Codex model profile: default is performance-first' "$tmp/home/.codex/AGENTS.md" \
  "Codex global policy must record performance-first profile"
grep_required 'Bootstrap safety:' "$tmp/home/.codex/AGENTS.md" \
  "Codex global policy must include bootstrap no-silent-defaults safety"
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
grep_required 'Act by default:' "$agents_preserve_home/.codex/AGENTS.md" \
  "Codex global policy install must replace managed block"
grep_required 'Ask only when it matters:' "$agents_preserve_home/.codex/AGENTS.md" \
  "Codex global policy install must scope asking to core decisions"
grep_required 'Bootstrap safety:' "$agents_preserve_home/.codex/AGENTS.md" \
  "Codex global policy install must include bootstrap no-silent-defaults safety"
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
  "codex-policy target must print bootstrap no-silent-defaults safety"
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
for agent in explore worker designer judge code-reviewer deep-judge deep-reviewer; do
  [[ -f "$tmp/home-cursor/.cursor/agents/$agent.md" ]] \
    || fail "Cursor install must copy Cursor agent $agent"
  [[ ! -L "$tmp/home-cursor/.cursor/agents/$agent.md" ]] \
    || fail "default Cursor install must copy Cursor agent $agent"
done
for agent in explore designer; do
  grep_required '^model: claude-sonnet-4-6$' "$tmp/home-cursor/.cursor/agents/$agent.md" \
    "Cursor install must render sonnet 4.6 model for $agent"
done
grep_required '^model: composer-2.5-fast$' "$tmp/home-cursor/.cursor/agents/worker.md" \
  "Cursor install must render composer 2.5 model for worker"
for agent in judge code-reviewer deep-judge deep-reviewer; do
  grep_required '^model: claude-opus-4-8-thinking-high$' "$tmp/home-cursor/.cursor/agents/$agent.md" \
    "Cursor install must render opus 4.8 model for $agent"
done

HOME="$tmp/home-cursor-agents" "$ROOT/install.sh" cursor-agents >/dev/null
for agent in explore worker designer judge code-reviewer deep-judge deep-reviewer; do
  [[ -f "$tmp/home-cursor-agents/.cursor/agents/$agent.md" ]] \
    || fail "Cursor agent install missing $agent"
done
[[ ! -e "$tmp/home-cursor-agents/.cursor/skills" ]] \
  || fail "cursor-agents target must not write Cursor skills"

HOME="$tmp/home-cursor-cost" "$ROOT/install.sh" --profile cost-first cursor-agents >/dev/null
for agent in explore designer worker; do
  grep_required '^model: composer-2.5-fast$' "$tmp/home-cursor-cost/.cursor/agents/$agent.md" \
    "cost-first Cursor agent install must downshift $agent"
done
for agent in judge code-reviewer deep-judge deep-reviewer; do
  grep_required '^model: claude-opus-4-8-thinking-high$' "$tmp/home-cursor-cost/.cursor/agents/$agent.md" \
    "cost-first Cursor agent install must keep opus 4.8 model for $agent"
done

cursor_policy_out="$tmp/cursor-policy.out"
HOME="$tmp/home-cursor-policy" "$ROOT/install.sh" cursor-policy > "$cursor_policy_out"
grep_required '<!-- TEAMWORK_CURSOR_GLOBAL_START -->' "$cursor_policy_out" \
  "cursor-policy target must print Teamwork global policy start marker"
grep_required 'Cursor model profile: default is performance-first' "$cursor_policy_out" \
  "cursor-policy target must render performance-first profile"
[[ ! -e "$tmp/home-cursor-policy/.cursor" ]] \
  || fail "cursor-policy target must not write Cursor home files"

mkdir -p "$tmp/bin"
cat > "$tmp/bin/pbcopy" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
cat > "$TEAMWORK_TEST_CLIPBOARD"
SH
chmod +x "$tmp/bin/pbcopy"
cursor_policy_copy_out="$tmp/cursor-policy-copy.out"
TEAMWORK_TEST_CLIPBOARD="$tmp/cursor-policy-copy.clipboard" \
  HOME="$tmp/home-cursor-policy-copy" \
  PATH="$tmp/bin:$PATH" \
  "$ROOT/install.sh" cursor-policy-copy > "$cursor_policy_copy_out"
grep_required '<!-- TEAMWORK_CURSOR_GLOBAL_START -->' "$tmp/cursor-policy-copy.clipboard" \
  "cursor-policy-copy target must copy Teamwork global policy start marker"
grep_required 'Copied Teamwork Cursor global policy to clipboard.' "$cursor_policy_copy_out" \
  "cursor-policy-copy target must report clipboard copy"
[[ ! -e "$tmp/home-cursor-policy-copy/.cursor" ]] \
  || fail "cursor-policy-copy target must not write Cursor home files"

HOME="$tmp/home-claude" "$ROOT/install.sh" claude >/dev/null
for skill in "${SKILLS[@]}"; do
  [[ -f "$tmp/home-claude/.claude/skills/$skill/SKILL.md" ]] || fail "Claude Code install missing $skill"
  [[ ! -L "$tmp/home-claude/.claude/skills/$skill/SKILL.md" ]] || fail "default Claude Code install must copy $skill"
done
[[ -f "$tmp/home-claude/.claude/skills/using-teamwork/references/workflow-contract.md" ]] \
  || fail "Claude Code install must copy using-teamwork references"
for agent in explore worker designer judge code-reviewer deep-judge deep-reviewer; do
  [[ -f "$tmp/home-claude/.claude/agents/$agent.md" ]] \
    || fail "Claude Code install must copy Claude agent $agent"
  [[ ! -L "$tmp/home-claude/.claude/agents/$agent.md" ]] \
    || fail "default Claude Code install must copy Claude agent $agent"
done
for agent in explore designer worker; do
  grep_required '^model: sonnet$' "$tmp/home-claude/.claude/agents/$agent.md" \
    "Claude install must render sonnet model for $agent"
  grep_required '^effort: medium$' "$tmp/home-claude/.claude/agents/$agent.md" \
    "Claude install must render medium effort for $agent"
done
for agent in judge code-reviewer; do
  grep_required '^model: opus$' "$tmp/home-claude/.claude/agents/$agent.md" \
    "Claude install must render opus model for $agent"
  grep_required '^effort: high$' "$tmp/home-claude/.claude/agents/$agent.md" \
    "Claude install must render high effort for $agent"
done
for agent in deep-judge deep-reviewer; do
  grep_required '^model: opus$' "$tmp/home-claude/.claude/agents/$agent.md" \
    "Claude install must render opus model for $agent"
  grep_required '^effort: xhigh$' "$tmp/home-claude/.claude/agents/$agent.md" \
    "Claude install must render xhigh effort for $agent"
done
grep_required '<!-- TEAMWORK_CLAUDE_GLOBAL_START -->' "$tmp/home-claude/.claude/CLAUDE.md" \
  "Claude install must create Teamwork global CLAUDE block"
grep_required 'Claude model profile: default is performance-first' "$tmp/home-claude/.claude/CLAUDE.md" \
  "Claude global policy must record performance-first profile"
grep_required 'Bootstrap safety:' "$tmp/home-claude/.claude/CLAUDE.md" \
  "Claude global policy must include bootstrap no-silent-defaults safety"

claude_policy_out="$tmp/claude-policy.out"
HOME="$tmp/home-claude-policy" "$ROOT/install.sh" claude-policy > "$claude_policy_out"
grep_required '<!-- TEAMWORK_CLAUDE_GLOBAL_START -->' "$claude_policy_out" \
  "claude-policy target must print Teamwork global policy start marker"
grep_required 'Claude model profile: default is performance-first' "$claude_policy_out" \
  "claude-policy target must render performance-first profile"
[[ ! -e "$tmp/home-claude-policy/.claude/CLAUDE.md" ]] \
  || fail "claude-policy target must not write global CLAUDE policy"

HOME="$tmp/home-claude-cost" "$ROOT/install.sh" --profile cost-first claude-agents >/dev/null
for agent in explore designer worker; do
  grep_required '^model: haiku$' "$tmp/home-claude-cost/.claude/agents/$agent.md" \
    "cost-first Claude agent install must downshift $agent"
done
for agent in judge code-reviewer deep-judge deep-reviewer; do
  grep_required '^model: opus$' "$tmp/home-claude-cost/.claude/agents/$agent.md" \
    "cost-first Claude agent install must keep opus model for $agent"
done

claude_preserve_home="$tmp/home-claude-preserve"
mkdir -p "$claude_preserve_home/.claude"
cat > "$claude_preserve_home/.claude/CLAUDE.md" <<'CLAUDE'
Personal rule before.

<!-- TEAMWORK_CLAUDE_GLOBAL_START -->
old managed content
<!-- TEAMWORK_CLAUDE_GLOBAL_END -->

<!-- CODEGRAPH_START -->
Keep CodeGraph instructions.
<!-- CODEGRAPH_END -->
CLAUDE
HOME="$claude_preserve_home" "$ROOT/install.sh" claude >/dev/null
grep_required 'Personal rule before.' "$claude_preserve_home/.claude/CLAUDE.md" \
  "Claude global policy install must preserve user content"
grep_required '<!-- CODEGRAPH_START -->' "$claude_preserve_home/.claude/CLAUDE.md" \
  "Claude global policy install must preserve CodeGraph block"
grep_required 'Bootstrap safety:' "$claude_preserve_home/.claude/CLAUDE.md" \
  "Claude global policy install must replace managed block"
grep_absent 'old managed content' \
  "Claude global policy install must replace old managed content" \
  "$claude_preserve_home/.claude/CLAUDE.md"

HOME="$tmp/home-claude-link" "$ROOT/install.sh" --link claude >/dev/null
for skill in "${SKILLS[@]}"; do
  [[ -L "$tmp/home-claude-link/.claude/skills/$skill" ]] || fail "Claude Code link install must symlink $skill directory"
done

HOME="$tmp/home-claude-agents-link" "$ROOT/install.sh" --link claude-agents >/dev/null
for agent in explore worker designer judge code-reviewer deep-judge deep-reviewer; do
  [[ -L "$tmp/home-claude-agents-link/.claude/agents/$agent.md" ]] \
    || fail "Claude agent link install must symlink $agent.md"
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
for agent in explore worker code-reviewer designer judge deep-judge deep-reviewer; do
  [[ -L "$tmp/home-all/.claude/agents/$agent.md" ]] || fail "all install must link Claude agent $agent"
done
for agent in explore worker designer judge code-reviewer deep-judge deep-reviewer; do
  [[ -L "$tmp/home-all/.cursor/agents/$agent.md" ]] || fail "all install must link Cursor agent $agent"
done
[[ ! -e "$tmp/home-all/.claude/skills/teamwork" ]] || fail "all install must remove retired teamwork skill"
grep_required '<!-- TEAMWORK_CLAUDE_GLOBAL_START -->' "$tmp/home-all/.claude/CLAUDE.md" \
  "all install must write Claude global policy"

old_root="$ROOT"
ROOT="$tmp/project-repo"
mkdir -p "$ROOT/skills" "$ROOT/templates/claude-agents" "$ROOT/templates/codex-agents" "$ROOT/templates/cursor-agents"
cp -R "$old_root/skills/." "$ROOT/skills/"
cp -R "$old_root/templates/claude-agents/." "$ROOT/templates/claude-agents/"
cp -R "$old_root/templates/codex-agents/." "$ROOT/templates/codex-agents/"
cp -R "$old_root/templates/cursor-agents/." "$ROOT/templates/cursor-agents/"
cp "$old_root/install.sh" "$ROOT/install.sh"
HOME="$tmp/home-project" ROOT="$ROOT" "$ROOT/install.sh" --link project >/dev/null
for skill in "${SKILLS[@]}"; do
  [[ -L "$ROOT/.cursor/skills/$skill" ]] || fail "project install must link Cursor skill $skill"
done
for agent in teamwork-explorer teamwork-worker teamwork-designer teamwork-judge teamwork-reviewer teamwork-deep-judge teamwork-deep-reviewer; do
  [[ -L "$ROOT/.codex/agents/$agent.toml" ]] || fail "project install must link Codex agent $agent"
done
for agent in explore worker designer judge code-reviewer deep-judge deep-reviewer; do
  [[ -L "$ROOT/.cursor/agents/$agent.md" ]] || fail "project install must link Cursor agent $agent"
done
for agent in explore worker designer judge code-reviewer deep-judge deep-reviewer; do
  [[ -L "$ROOT/.claude/agents/$agent.md" ]] || fail "project install must link Claude agent $agent"
done
ROOT="$old_root"

init_root="$tmp/init-project"
mkdir -p "$init_root"
printf '# Init Smoke\n' > "$init_root/README.md"
HOME="$tmp/home-init-project" \
  TEAMWORK_INIT_CODEGRAPH=0 \
  TEAMWORK_INIT_CURSOR_POLICY_COPY=0 \
  "$ROOT/install.sh" --copy --project-root "$init_root" init-project >/dev/null
grep_required '<!-- TEAMWORK_PROJECT_START -->' "$init_root/AGENTS.md" \
  "init-project must write managed AGENTS.md block"
grep_required 'docs/teamwork/README.md' "$init_root/AGENTS.md" \
  "init-project AGENTS.md block must point to Teamwork memory"
grep_required '# TEAMWORK_LOCAL_START' "$init_root/.gitignore" \
  "init-project must write local .gitignore block"
python3 "$ROOT/scripts/validate_teamwork_index.py" "$init_root/docs/teamwork/index.json" >/dev/null
[[ -f "$init_root/docs/teamwork/current.md" ]] || fail "init-project must write current.md"
[[ -d "$tmp/home-init-project/.codex/skills/using-teamwork" ]] || fail "init-project must install global Codex skills by default"
[[ -f "$tmp/home-init-project/.codex/AGENTS.md" ]] || fail "init-project must install global Codex policy by default"
[[ -d "$tmp/home-init-project/.cursor/skills/using-teamwork" ]] || fail "init-project must install global Cursor skills by default"
[[ -f "$tmp/home-init-project/.cursor/agents/worker.md" ]] || fail "init-project must install global Cursor agents by default"
[[ -f "$tmp/home-init-project/.claude/CLAUDE.md" ]] || fail "init-project must install global Claude policy by default"
[[ -f "$tmp/home-init-project/.claude/agents/worker.md" ]] || fail "init-project must install global Claude agents by default"
[[ -d "$init_root/.cursor/skills/using-teamwork" ]] || fail "init-project must install project skills"
[[ -f "$init_root/.codex/agents/teamwork-worker.toml" ]] || fail "init-project must install Codex agents"
[[ -f "$init_root/.cursor/agents/worker.md" ]] || fail "init-project must install project Cursor agents"
[[ -f "$init_root/.claude/agents/worker.md" ]] || fail "init-project must install project Claude agents"

invalid_root="$tmp/init-project-invalid-index"
mkdir -p "$invalid_root/docs/teamwork"
printf '# Invalid Index Smoke\n' > "$invalid_root/README.md"
printf '{"bad": true}\n' > "$invalid_root/docs/teamwork/index.json"
invalid_output="$(
  HOME="$tmp/home-init-project-invalid" \
    TEAMWORK_INIT_CODEGRAPH=0 \
    TEAMWORK_INIT_CURSOR_POLICY_COPY=0 \
    "$ROOT/scripts/init-project.sh" --project-root "$invalid_root" --project-only --copy 2>&1
)"
printf '%s\n' "$invalid_output" | grep -q 'Teamwork memory: index invalid' \
  || fail "init-project must report invalid existing Teamwork memory index"

HOME="$tmp/home-agents" "$ROOT/install.sh" --link claude-agents >/dev/null
for agent in explore worker designer judge code-reviewer deep-judge deep-reviewer; do
  [[ -L "$tmp/home-agents/.claude/agents/$agent.md" ]] \
    || fail "claude-agents install must link $agent.md"
done

HOME="$tmp/home-cursor-agents-link" "$ROOT/install.sh" --link cursor-agents >/dev/null
for agent in explore worker designer judge code-reviewer deep-judge deep-reviewer; do
  [[ -L "$tmp/home-cursor-agents-link/.cursor/agents/$agent.md" ]] \
    || fail "cursor-agents link install must symlink $agent.md"
done

echo "OK: Teamwork skill package validates"
