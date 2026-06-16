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

# --- Skill frontmatter ---
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

# --- Reference inventory ---
for reference in artifact-protocol goal-iteration optional-skills plan-output project-init research-protocol review-checks role-playbook subagent-contract subagent-dispatch workflow-contract workflow-orchestration; do
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
    artifact-protocol.md goal-iteration.md optional-skills.md plan-output.md \
    project-init.md research-protocol.md review-checks.md role-playbook.md \
    subagent-contract.md subagent-dispatch.md teamwork-current-template.md \
    teamwork-index-readme-template.md teamwork-index-template.json \
    workflow-contract.md workflow-orchestration.md | sort
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
grep_required 'teamwork-init' "$ROOT/README.md" "README must document teamwork-init"
grep_required 'VERSION' "$ROOT/README.md" "README must document package version source"
grep_required '\[English\](README.en.md)' "$ROOT/README.md" "default README must link to English README"
grep_required 'docs/teamwork/research/YYYY-MM-DD-<slug>.md' "$ROOT/README.md" "README must document research artifact path"
grep_required 'docs/teamwork/plans/YYYY-MM-DD-<slug>.md' "$ROOT/README.md" "README must document plan artifact path"
grep_required 'docs/teamwork/reports/YYYY-MM-DD-<slug>.md' "$ROOT/README.md" "README must document report artifact path"
grep_required './install.sh --link codex' "$ROOT/README.md" "README must document Codex link-mode development install"
[[ -f "$ROOT/README.en.md" ]] || fail "missing English README"
git -C "$ROOT" ls-files --error-unmatch "README.en.md" >/dev/null 2>&1 || fail "README.en.md must be tracked by git"
grep_required '\[中文\](README.md)' "$ROOT/README.en.md" "English README must link to default Chinese README"
grep_required 'Codex + Cursor + Claude Code' "$ROOT/README.en.md" "English README must state Codex + Cursor + Claude Code positioning"
grep_required 'teamwork-update' "$ROOT/README.en.md" "English README must document teamwork-update"
grep_required 'VERSION' "$ROOT/README.en.md" "English README must document package version source"
grep_required './install.sh --link codex' "$ROOT/README.en.md" "English README must document Codex link-mode development install"
grep_required 'Codex + Cursor + Claude Code skill package' "$ROOT/AGENTS.md" "AGENTS.md must describe the package"
grep_required 'teamwork-update' "$ROOT/AGENTS.md" "AGENTS.md must document update skill ownership"
grep_required 'teamwork-init' "$ROOT/AGENTS.md" "AGENTS.md must document init skill ownership"
grep_required 'Codex native capabilities' "$ROOT/CODEX.md" "CODEX.md must document native Codex capability policy"
grep_required 'Codex runtime profile' "$ROOT/CODEX.md" "CODEX.md must identify itself as the Codex runtime profile"
grep_required 'VERSION' "$ROOT/CODEX.md" "CODEX.md must document package version source"
grep_required 'teamwork-init' "$ROOT/CODEX.md" "CODEX.md must document teamwork-init"
grep_required 'subagent-dispatch.md' "$ROOT/CODEX.md" "CODEX.md must point to subagent dispatch reference"
grep_required 'Task' "$ROOT/CURSOR.md" "CURSOR.md must document Cursor Task subagent policy"
grep_required 'Goal Mode' "$ROOT/CURSOR.md" "CURSOR.md must document Cursor goal mode"
grep_required 'subagent-dispatch.md' "$ROOT/CURSOR.md" "CURSOR.md must point to subagent dispatch reference"
grep_required 'Claude Code native capabilities' "$ROOT/CLAUDE.md" "CLAUDE.md must document native Claude Code capability policy"
grep_required 'Task' "$ROOT/CLAUDE.md" "CLAUDE.md must document Claude Code Task subagent policy"
grep_required 'subagent-dispatch.md' "$ROOT/CLAUDE.md" "CLAUDE.md must point to subagent dispatch reference"
grep_required 'rolling report' "$ROOT/CLAUDE.md" "CLAUDE.md must document Claude Code goal rolling report"
grep_required 'VERSION' "$ROOT/CLAUDE.md" "CLAUDE.md must document package version source"

# --- Installer global policy ---
grep_required 'write_teamwork_codex_global_policy()' "$ROOT/install.sh" "installer must define Teamwork Codex global policy writer"
grep_required '<!-- TEAMWORK_CODEX_GLOBAL_START -->' "$ROOT/install.sh" "installer global policy writer must include managed start marker"
grep_required '<!-- TEAMWORK_CODEX_GLOBAL_END -->' "$ROOT/install.sh" "installer global policy writer must include managed end marker"
grep_required 'install_codex_global_policy' "$ROOT/install.sh" "installer must call Codex global policy install from Codex target"

# --- Budgets ---
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
line_count_max "$ROOT/skills/using-teamwork/references/workflow-contract.md" 150 "workflow contract reference should stay focused"
word_count_max "$ROOT/skills/using-teamwork/references/workflow-contract.md" 950 "workflow contract reference should stay focused"
line_count_max "$ROOT/skills/using-teamwork/references/subagent-dispatch.md" 130 "subagent dispatch reference should stay focused"
word_count_max "$ROOT/skills/using-teamwork/references/subagent-dispatch.md" 900 "subagent dispatch reference should stay focused"
line_count_max "$ROOT/skills/using-teamwork/references/subagent-contract.md" 145 "subagent contract reference should stay focused"
word_count_max "$ROOT/skills/using-teamwork/references/subagent-contract.md" 600 "subagent contract reference should stay focused"
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
line_count_max "$ROOT/skills/using-teamwork/references/project-init.md" 80 "project init reference should stay focused"
word_count_max "$ROOT/skills/using-teamwork/references/project-init.md" 600 "project init reference should stay focused"
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
grep_required 'references/subagent-dispatch.md' "$ENTRYPOINT" "using-teamwork must reference subagent dispatch"
for skill in teamwork-init teamwork-goal teamwork-research teamwork-plan teamwork-execute teamwork-review; do
  grep_absent '`references/' "$skill must not use sibling-local reference paths" "$ROOT/skills/$skill/SKILL.md"
  grep_absent '^- `references/' "$skill must not list sibling-local reference paths" "$ROOT/skills/$skill/SKILL.md"
  grep_required 'skills/using-teamwork/references/workflow-contract.md' "$ROOT/skills/$skill/SKILL.md" "$skill must reference shared workflow contract"
done

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
grep_required 'frontier' "$ROOT/skills/using-teamwork/references/subagent-dispatch.md" "subagent dispatch must document model classes"

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
grep_required 'Goal Proposal' "$ROOT/skills/using-teamwork/references/goal-iteration.md" "goal iteration must define Goal Proposal"
grep_required 'Research + Plan Adequacy Gate' "$ROOT/skills/using-teamwork/references/goal-iteration.md" "goal iteration must define adequacy gate"
grep_required 'final status, closure evidence' "$ROOT/skills/using-teamwork/references/plan-output.md" "plan output must include dispatch closure evidence"
grep_required 'Durable memory check' "$ROOT/skills/using-teamwork/references/review-checks.md" "review checks must include durable memory materiality checks"
grep_required 'Memory promotion check' "$ROOT/skills/using-teamwork/references/review-checks.md" "review checks must include memory promotion checks"
grep_required 'candidate memory' "$ROOT/skills/using-teamwork/references/review-checks.md" "review checks must keep external memory candidate-scoped"
grep_required 'Manual smoke evidence captures source' "$ROOT/skills/using-teamwork/references/review-checks.md" "review checks must include manual smoke evidence fields"
grep_required 'No delegated track remains dispatched or returned' "$ROOT/skills/using-teamwork/references/review-checks.md" "review checks must reject open delegated tracks"

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
