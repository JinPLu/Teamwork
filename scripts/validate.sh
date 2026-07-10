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
CLEANUP_PATHS=()

cleanup() {
  if ((${#CLEANUP_PATHS[@]})); then
    rm -rf "${CLEANUP_PATHS[@]}"
  fi
}
trap cleanup EXIT

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

check_lean_policy() {
  local file="$1"
  local profile="$2"
  local label="$3"
  grep_required "Act by default within the user's request" "$file" "$label must preserve act-by-default"
  grep_required 'Make routine,' "$file" "$label must permit routine reversible choices"
  grep_required 'Grill/question-first behavior activates only when explicitly requested' "$file" \
    "$label must keep grill mode explicit"
  grep_required 'Do not invent them' "$file" "$label must preserve required-state safety"
  grep_required 'evidence, time, or context-isolation value exceeds' "$file" \
    "$label must keep delegation economic"
  grep_required 'Installed agent files own model mappings; active profile:' "$file" \
    "$label must keep model mappings out of global policy"
  grep_required "^${profile}\. Use project-local" "$file" "$label must record active profile $profile"
}

git_known_package_file() {
  local path="$1"
  git -C "$ROOT" ls-files --error-unmatch "$path" >/dev/null 2>&1 && return 0
  return 1
}

check_markdown_local_images() {
  local file="$1"
  python3 - "$ROOT" "$file" <<'PY'
import pathlib
import re
import subprocess
import sys
from urllib.parse import unquote

root = pathlib.Path(sys.argv[1]).resolve()
file = pathlib.Path(sys.argv[2]).resolve()
text = file.read_text()

for raw_target in re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text):
    target = raw_target.strip()
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target):
        continue
    if target.startswith("#"):
        continue
    if target.startswith("<") and ">" in target:
        target = target[1:target.index(">")]
    else:
        target = target.split()[0]
    target = unquote(target)
    asset = (file.parent / target).resolve()
    try:
        rel = asset.relative_to(root)
    except ValueError as exc:
        raise SystemExit(f"FAIL: {file.relative_to(root)} image points outside package: {raw_target}") from exc
    if not asset.is_file():
        raise SystemExit(f"FAIL: {file.relative_to(root)} image missing: {rel}")
    known = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--error-unmatch", str(rel)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if known.returncode != 0:
        raise SystemExit(
            f"FAIL: {file.relative_to(root)} image is not known to git: {rel}; use git add -N before release validation"
        )
PY
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
[[ -f "$ROOT/CHANGELOG.en.md" ]] || fail "missing CHANGELOG.en.md"
git_known_package_file "CHANGELOG.md" || fail "CHANGELOG.md is not known to git; use git add -N before release validation"
git_known_package_file "CHANGELOG.en.md" || fail "CHANGELOG.en.md is not known to git; use git add -N before release validation"

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
for reference in artifact-protocol check-update debug-mode eval-gate goal-iteration grill-mode optional-skills plan-output project-init research-protocol review-checks review-lenses role-playbook routing-policy subagent-contract subagent-dispatch verification-patterns workflow-contract workflow-orchestration; do
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
    artifact-protocol.md check-update.md debug-mode.md eval-gate.md goal-iteration.md grill-mode.md optional-skills.md plan-output.md \
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

# --- Eval harness inventory ---
[[ -f "$ROOT/evals/teamwork/README.md" ]] || fail "missing evals/teamwork/README.md"
git_known_package_file "evals/teamwork/README.md" \
  || fail "evals/teamwork/README.md is not known to git; use git add -N before release validation"
for eval_dir in cases live-cases rubrics ledgers outputs; do
  [[ -d "$ROOT/evals/teamwork/$eval_dir" ]] || fail "missing evals/teamwork/$eval_dir/"
done
while IFS= read -r eval_file; do
  rel="${eval_file#"$ROOT"/}"
  git_known_package_file "$rel" \
    || fail "$rel is not known to git; use git add -N before release validation"
done < <(find "$ROOT/evals/teamwork/cases" "$ROOT/evals/teamwork/live-cases" "$ROOT/evals/teamwork/rubrics" "$ROOT/evals/teamwork/ledgers" "$ROOT/evals/teamwork/outputs" -type f | sort)
[[ -f "$ROOT/evals/teamwork/outputs/question-first/dev.jsonl" ]] \
  || fail "missing question-first eval output samples"
for case_id in complex-autonomy-control question-first-explicit-grill question-first-explicit-lightweight-grill question-first-complex-uncertainty question-first-lightweight-control; do
  [[ -f "$ROOT/evals/teamwork/cases/$case_id.dev.json" ]] \
    || fail "missing question-first eval case: $case_id"
  grep_required "\"case_id\":\"$case_id\"" "$ROOT/evals/teamwork/outputs/question-first/dev.jsonl" \
    "question-first eval outputs must include $case_id"
done
for platform in codex cursor claude; do
  grep_required "\"platform\":\"$platform\"" "$ROOT/evals/teamwork/outputs/question-first/dev.jsonl" \
    "question-first eval outputs must include $platform samples"
done
grep_required 'Facts checked:' "$ROOT/evals/teamwork/outputs/question-first/dev.jsonl" \
  "explicit grill output samples must cite facts checked before asking"
[[ -f "$ROOT/scripts/eval-teamwork.py" ]] || fail "missing scripts/eval-teamwork.py"
git_known_package_file "scripts/eval-teamwork.py" \
  || fail "scripts/eval-teamwork.py is not known to git; use git add -N before release validation"
python3 "$ROOT/scripts/eval-teamwork.py" --split dev >/dev/null
[[ -x "$ROOT/scripts/run-teamwork-live-eval.py" ]] || fail "live eval runner must be executable"
git_known_package_file "scripts/run-teamwork-live-eval.py" \
  || fail "scripts/run-teamwork-live-eval.py is not known to git; use git add -N before release validation"
python3 -m py_compile "$ROOT/scripts/run-teamwork-live-eval.py"
live_eval_tmp="$(mktemp -d)"
CLEANUP_PATHS+=("$live_eval_tmp")
python3 "$ROOT/scripts/run-teamwork-live-eval.py" \
  --arm validate-dry-run \
  --model gpt-5.6-sol \
  --effort max \
  --workdir "$ROOT" \
  --output "$live_eval_tmp/output.jsonl" \
  --cases "$ROOT/evals/teamwork/live-cases/lightweight-pilot.json" \
  --repeats 1 \
  --timeout-seconds 60 \
  --dry-run >/dev/null
[[ -f "$ROOT/scripts/optimize-teamwork.py" ]] || fail "missing scripts/optimize-teamwork.py"
git_known_package_file "scripts/optimize-teamwork.py" \
  || fail "scripts/optimize-teamwork.py is not known to git; use git add -N before release validation"
python3 "$ROOT/scripts/optimize-teamwork.py" --help >/dev/null
opt_tmp="$(mktemp -d)"
CLEANUP_PATHS+=("$opt_tmp")
printf '%s\n' \
  '{"id":"case-failed","status":"failed","score":0,"input":"Fix typo","expected":"direct edit","output":"planned too much","fail_reason":"over-routing"}' \
  '{"id":"case-passed","passed":true,"score":1,"input":"Review release","expected":"release eval","output":"asked for eval"}' \
  > "$opt_tmp/results.jsonl"
python3 "$ROOT/scripts/optimize-teamwork.py" init-workspace \
  --workspace "$opt_tmp/workspace" --skill "$ROOT/skills/using-teamwork/SKILL.md" >/dev/null
python3 "$ROOT/scripts/optimize-teamwork.py" export-samples \
  --results "$opt_tmp/results.jsonl" --workspace "$opt_tmp/workspace" --env teamwork >/dev/null
[[ -f "$opt_tmp/workspace/.skillopt/samples/failed/case-failed.md" ]] \
  || fail "optimizer smoke did not write failed sample"
python3 "$ROOT/scripts/optimize-teamwork.py" score-results \
  --results "$opt_tmp/results.jsonl" \
  | grep -q '"mean_score": 0.5' \
  || fail "optimizer smoke score did not compute expected mean"
python3 "$ROOT/scripts/optimize-teamwork.py" gate \
  --candidate-score 0.92 --current-score 0.80 --best-score 0.90 --dead-band 0.01 \
  | grep -q '"action": "accept_new_best"' \
  || fail "optimizer smoke gate did not accept new best"
opt_ledger_tmp="$(mktemp -d)"
CLEANUP_PATHS+=("$opt_ledger_tmp")
printf '%s\n' \
  '{"date":"2026-07-08","candidate_id":"optimizer-smoke-valid","kind":"skillopt-lite","provider":"offline","model":"deterministic-smoke","model_config":"offline-smoke","prompt_or_template":"skills/using-teamwork/SKILL.md","owned_files":["skills/teamwork-review/SKILL.md"],"denylist":["evals/teamwork/cases/*.json"],"baseline":"evals/teamwork/README.md","treatment":"scripts/optimize-teamwork.py","gate_decision":"reject","rollback":"evals/teamwork/README.md","validation":["scripts/validate.sh"],"release_audit":"validate smoke only","reviewer":"validate.sh","decision":"rejected"}' \
  > "$opt_ledger_tmp/valid.jsonl"
python3 "$ROOT/scripts/eval-teamwork.py" --optimizer-ledger "$opt_ledger_tmp/valid.jsonl" >/dev/null
printf '%s\n' \
  '{"date":"2026-07-08","candidate_id":"optimizer-smoke-invalid","kind":"skillopt-lite","provider":"offline","model":"deterministic-smoke","model_config":"offline-smoke","prompt_or_template":"not_applicable","owned_files":["skills/teamwork-review/SKILL.md"],"denylist":["evals/teamwork/cases/*.json"],"baseline":"evals/teamwork/README.md","treatment":"scripts/optimize-teamwork.py","gate_decision":"reject","rollback":"evals/teamwork/README.md","validation":["scripts/validate.sh"],"release_audit":"validate smoke only","reviewer":"validate.sh","decision":"rejected"}' \
  > "$opt_ledger_tmp/invalid.jsonl"
if python3 "$ROOT/scripts/eval-teamwork.py" --optimizer-ledger "$opt_ledger_tmp/invalid.jsonl" >/dev/null 2>&1; then
  fail "optimizer ledger smoke accepted placeholder evidence"
fi

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
check_markdown_local_images "$ROOT/README.md"
grep_required '^# 更新日志' "$ROOT/CHANGELOG.md" "CHANGELOG must have a Chinese top-level heading"
grep_required '\[English\](CHANGELOG.en.md)' "$ROOT/CHANGELOG.md" "default CHANGELOG must link to English CHANGELOG"
grep_required "## $(tr -d '[:space:]' < "$ROOT/VERSION") -" "$ROOT/CHANGELOG.md" "CHANGELOG must document current VERSION"
grep_required '^# Changelog' "$ROOT/CHANGELOG.en.md" "English CHANGELOG must have a top-level heading"
grep_required '\[中文\](CHANGELOG.md)' "$ROOT/CHANGELOG.en.md" "English CHANGELOG must link to default Chinese CHANGELOG"
grep_required "## $(tr -d '[:space:]' < "$ROOT/VERSION") -" "$ROOT/CHANGELOG.en.md" "English CHANGELOG must document current VERSION"
[[ -f "$ROOT/README.en.md" ]] || fail "missing English README"
git -C "$ROOT" ls-files --error-unmatch "README.en.md" >/dev/null 2>&1 || fail "README.en.md must be tracked by git"
grep_required '\[中文\](README.md)' "$ROOT/README.en.md" "English README must link to default Chinese README"
grep_required 'Codex + Cursor + Claude Code' "$ROOT/README.en.md" "English README must state Codex + Cursor + Claude Code positioning"
grep_required 'teamwork-update' "$ROOT/README.en.md" "English README must document teamwork-update"
grep_required 'check-update.sh' "$ROOT/README.en.md" "English README must document check-update script"
grep_required 'VERSION' "$ROOT/README.en.md" "English README must document package version source"
grep_required './install.sh --link codex' "$ROOT/README.en.md" "English README must document Codex link-mode development install"
check_markdown_local_images "$ROOT/README.en.md"
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
line_count_max "$ROOT/skills/using-teamwork/references/eval-gate.md" 75 "eval gate reference should stay focused"
word_count_max "$ROOT/skills/using-teamwork/references/eval-gate.md" 450 "eval gate reference should stay focused"
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
line_count_max "$ROOT/skills/using-teamwork/references/grill-mode.md" 70 "grill mode reference should stay focused"
word_count_max "$ROOT/skills/using-teamwork/references/grill-mode.md" 430 "grill mode reference should stay focused"
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

# --- Lean runtime contracts ---
grep_required 'references/workflow-contract.md' "$ENTRYPOINT" "router must reference the shared workflow contract"
grep_required 'routing-policy.md' "$ENTRYPOINT" "router must load routing policy only for unclear routes"
grep_required 'grill-mode.md' "$ENTRYPOINT" "router must keep explicit grill mode discoverable"
grep_required 'clear tasks stay native' "$ENTRYPOINT" "router must preserve the native fast path"
grep_required 'Only an explicit grill/question-first request' "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
  "workflow contract must not infer grill mode from complexity"
grep_required 'routine reversible' "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
  "workflow contract must allow routine autonomous choices"
grep_required 'Do not invent required state' "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
  "workflow contract must preserve bootstrap safety"
grep_required 'Fresh review is required only for the high-risk row' "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
  "workflow contract must risk-gate fresh review"

for skill in teamwork-research teamwork-debug teamwork-plan teamwork-execute teamwork-review teamwork-goal; do
  file="$ROOT/skills/$skill/SKILL.md"
  for heading in '## Outcome' '## Enter When' '## Do And Boundaries' '## Done When' '## Escalate' '## Conditional Protocols'; do
    grep_required "$heading" "$file" "$skill must use the compact stage-card contract"
  done
  grep_required 'skills/using-teamwork/references/' "$file" "$skill must resolve shared reference paths"
  word_count_max "$file" 340 "$skill stage card should remain lean"
done

grep_required 'only for explicit' "$ROOT/skills/teamwork-research/SKILL.md" "research must condition grill mode"
grep_required 'as the evidence warrants' "$ROOT/skills/teamwork-debug/SKILL.md" \
  "debug must avoid a fixed hypothesis quota"
grep_required 'table or diagram only when it materially clarifies' "$ROOT/skills/teamwork-plan/SKILL.md" \
  "plan formatting must be conditional"
grep_required 'smallest direct change' "$ROOT/skills/teamwork-execute/SKILL.md" "execute must preserve direct implementation"
grep_required 'eval-gate.md.*only when that gate applies' "$ROOT/skills/teamwork-review/SKILL.md" \
  "review must condition package eval policy"
grep_required 'Do not invent a fixed iteration budget' "$ROOT/skills/teamwork-goal/SKILL.md" \
  "goal must not invent a numeric budget"

for anchor in Repro Hypotheses Instrumentation 'Runtime Evidence' Cleanup; do
  grep_required "$anchor" "$ROOT/skills/using-teamwork/references/debug-mode.md" "debug protocol must preserve $anchor"
done
for anchor in 'Verification Strength' 'VERIFIED' 'NOT VERIFIED' 'INCONCLUSIVE'; do
  grep_required "$anchor" "$ROOT/skills/using-teamwork/references/verification-patterns.md" \
    "verification protocol must preserve $anchor"
done
grep_required 'Source counts and packet sizes are heuristics, not gates' \
  "$ROOT/skills/using-teamwork/references/research-protocol.md" "research depth must be adaptive"
grep_required 'only when breadth makes' "$ROOT/skills/using-teamwork/references/research-protocol.md" \
  "research matrices must be conditional"
grep_required 'not an acceptance' \
  "$ROOT/skills/using-teamwork/references/plan-output.md" "plan format must remain flexible"
grep_required 'External calibration alone is not a write trigger' \
  "$ROOT/skills/using-teamwork/references/artifact-protocol.md" "artifact creation must be materiality-gated"
grep_required 'Goal Invariants' "$ROOT/skills/using-teamwork/references/goal-iteration.md" \
  "goal protocol must preserve goal invariants"
grep_required 'strategy delta' "$ROOT/skills/using-teamwork/references/goal-iteration.md" \
  "goal retries must change strategy after failed evidence"
grep_required 'no-progress stop' "$ROOT/skills/using-teamwork/references/goal-iteration.md" \
  "goal protocol must bound unbudgeted retries"

for role in Explorer Designer Judge Worker Reviewer; do
  grep_required "## $role" "$ROOT/skills/using-teamwork/references/role-playbook.md" "role playbook must define $role"
done
grep_required 'existing path' "$ROOT/skills/using-teamwork/references/role-playbook.md" \
  "Worker must prefer the existing owner"
grep_required 'Same-context verification is sufficient elsewhere' "$ROOT/skills/using-teamwork/references/role-playbook.md" \
  "Reviewer must not require fresh context universally"

grep_required '## Prompt' "$ROOT/skills/using-teamwork/references/subagent-contract.md" \
  "subagent contract must define a compact base prompt"
grep_required '## Base Result' "$ROOT/skills/using-teamwork/references/subagent-contract.md" \
  "subagent contract must define a compact base result"
grep_required 'accept | revise | blocked' "$ROOT/skills/using-teamwork/references/subagent-contract.md" \
  "Reviewer verdict enum must remain stable"
grep_required 'only when they' "$ROOT/skills/using-teamwork/references/subagent-contract.md" \
  "subagent packets must remain conditional"
for anchor in agent_type subagent_type 'Custom agent' effort 'gpt-5.6-sol.*max'; do
  grep_required "$anchor" "$ROOT/skills/using-teamwork/references/subagent-dispatch.md" \
    "subagent dispatch must preserve platform/profile anchor: $anchor"
done
grep_required 'no fixed prompt-level cap' "$ROOT/skills/using-teamwork/references/subagent-dispatch.md" \
  "Worker waves must be bounded by economics rather than a fixed quota"

# --- Lean role templates ---
while IFS= read -r template; do
  [[ "$(grep -c 'grill/question-first' "$template")" -eq 1 ]] \
    || fail "agent template must contain exactly one grill guard: ${template#"$ROOT/"}"
  word_count_max "$template" 260 "agent template should remain lean: ${template#"$ROOT/"}"
done < <(find "$ROOT/templates/codex-agents" "$ROOT/templates/cursor-agents" "$ROOT/templates/claude-agents" -type f | sort)
grep_absent 'Shared Understanding Packet\|Native Fields\|Option Matrix' \
  "agent templates must not restore fixed packet ceremony" \
  "$ROOT/templates/codex-agents" "$ROOT/templates/cursor-agents" "$ROOT/templates/claude-agents"
for template in \
  "$ROOT/templates/codex-agents/teamwork-explorer.toml" \
  "$ROOT/templates/cursor-agents/explore.md" \
  "$ROOT/templates/claude-agents/explore.md"; do
  grep_required 'full source census' "$template" "Explorer must mention the optional census"
  grep_required 'deep research' "$template" "Explorer source census must be conditional"
done
for template in \
  "$ROOT/templates/codex-agents/teamwork-designer.toml" \
  "$ROOT/templates/cursor-agents/designer.md" \
  "$ROOT/templates/claude-agents/designer.md"; do
  grep_required 'genuine alternatives' "$template" "Designer alternatives must reflect real tradeoffs"
done
for template in \
  "$ROOT/templates/codex-agents/teamwork-worker.toml" \
  "$ROOT/templates/cursor-agents/worker.md" \
  "$ROOT/templates/claude-agents/worker.md"; do
  grep_required 'Use TDD when a focused test' "$template" "Worker TDD must be conditional"
done

grep_absent 'teamwork-quality' "Teamwork must not add a separate quality stage" "$ROOT/skills" "$ROOT/CODEX.md" "$ROOT/CURSOR.md" "$ROOT/CLAUDE.md" "$ROOT/install.sh"
grep_absent 'teamwork-deslop' "Teamwork must not add a separate deslop stage" "$ROOT/skills" "$ROOT/CODEX.md" "$ROOT/CURSOR.md" "$ROOT/CLAUDE.md" "$ROOT/install.sh"
[[ ! -e "$ROOT/skills/teamwork-grill" ]] || fail "question-first override must not become a peer teamwork-grill skill"
grep_absent 'teamwork-grill)' "install skill list must not add a peer teamwork-grill skill" "$ROOT/install.sh"

grep_required 'check-update.md' "$ROOT/skills/teamwork-init/SKILL.md" "teamwork-init must reference check-update"
grep_required 'check-update.md' "$ROOT/skills/teamwork-update/SKILL.md" "teamwork-update must reference check-update"
grep_required 'check-update.sh' "$ROOT/skills/teamwork-update/SKILL.md" "teamwork-update must reference check-update script"
[[ -x "$ROOT/scripts/check-update.sh" ]] || fail "check-update script must be executable"
grep_required 'skills_content_status' "$ROOT/scripts/check-update.sh" "check-update must detect installed skill drift"
grep_required 'agents_content_status' "$ROOT/scripts/check-update.sh" "check-update must detect installed agent drift"

if git -C "$ROOT" grep -n -E 'raoctl|RAO|Stop hook|/rao:|/teamwork:' \
  -- ':!scripts/validate.sh' >/tmp/teamwork-retired-grep.$$; then
  cat /tmp/teamwork-retired-grep.$$ >&2
  rm -f /tmp/teamwork-retired-grep.$$
  fail "retired multi-runtime references remain outside validation"
fi
rm -f /tmp/teamwork-retired-grep.$$

tmp="$(mktemp -d)"
original_profile_marker="$ROOT/.teamwork-profile"
original_profile_exists=0
original_profile=""
if [[ -f "$original_profile_marker" ]]; then
  original_profile_exists=1
  original_profile="$(cat "$original_profile_marker")"
fi
restore_validate_state() {
  rm -rf "$tmp"
  if (( original_profile_exists )); then
    printf '%s\n' "$original_profile" > "$original_profile_marker"
  else
    rm -f "$original_profile_marker"
  fi
}
trap restore_validate_state EXIT
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
for agent in teamwork-explorer teamwork-worker; do
  grep_required '^model_reasoning_effort = "medium"$' "$tmp/home/.codex/agents/$agent.toml" \
    "Codex install must render medium reasoning for $agent"
done
for agent in teamwork-designer teamwork-judge teamwork-reviewer; do
  grep_required '^model_reasoning_effort = "high"$' "$tmp/home/.codex/agents/$agent.toml" \
    "Codex install must render high reasoning for $agent"
done
for agent in teamwork-deep-judge teamwork-deep-reviewer; do
  grep_required '^model_reasoning_effort = "max"$' "$tmp/home/.codex/agents/$agent.toml" \
    "Codex install must render max reasoning for $agent"
done
grep_required '<!-- TEAMWORK_CODEX_GLOBAL_START -->' "$tmp/home/.codex/AGENTS.md" \
  "Codex install must create Teamwork global AGENTS block"
grep_required 'Teamwork Codex Global Policy' "$tmp/home/.codex/AGENTS.md" \
  "Codex install must write Teamwork global policy heading"
check_lean_policy "$tmp/home/.codex/AGENTS.md" performance-first "Codex global policy"

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
check_lean_policy "$agents_preserve_home/.codex/AGENTS.md" performance-first \
  "refreshed Codex global policy"
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
check_lean_policy "$codex_policy_out" performance-first "codex-policy output"
[[ ! -e "$tmp/home-codex-policy/.codex/AGENTS.md" ]] \
  || fail "codex-policy target must not write global AGENTS policy"

HOME="$tmp/home-codex-agents" "$ROOT/install.sh" codex-agents >/dev/null
for agent in teamwork-explorer teamwork-worker teamwork-designer teamwork-judge teamwork-reviewer teamwork-deep-judge teamwork-deep-reviewer; do
  [[ -f "$tmp/home-codex-agents/.codex/agents/$agent.toml" ]] \
    || fail "Codex agent install missing $agent"
  [[ ! -L "$tmp/home-codex-agents/.codex/agents/$agent.toml" ]] \
    || fail "default Codex agent install must copy $agent"
done
grep_required '^model = "gpt-5.6-terra"$' "$tmp/home-codex-agents/.codex/agents/teamwork-explorer.toml" \
  "default Codex Explorer must use gpt-5.6-terra"
grep_required '^model_reasoning_effort = "medium"$' "$tmp/home-codex-agents/.codex/agents/teamwork-explorer.toml" \
  "default Codex Explorer must use medium reasoning"
grep_required '^model = "gpt-5.6-sol"$' "$tmp/home-codex-agents/.codex/agents/teamwork-worker.toml" \
  "default Codex Worker must use gpt-5.6-sol"
grep_required '^model_reasoning_effort = "medium"$' "$tmp/home-codex-agents/.codex/agents/teamwork-worker.toml" \
  "default Codex Worker must use medium reasoning"
for agent in teamwork-designer teamwork-judge teamwork-reviewer; do
  grep_required '^model = "gpt-5.6-sol"$' "$tmp/home-codex-agents/.codex/agents/$agent.toml" \
    "default Codex agent install must render gpt-5.6-sol for $agent"
  grep_required '^model_reasoning_effort = "high"$' "$tmp/home-codex-agents/.codex/agents/$agent.toml" \
    "default Codex agent install must render high reasoning for $agent"
done
for agent in teamwork-deep-judge teamwork-deep-reviewer; do
  grep_required '^model = "gpt-5.6-sol"$' "$tmp/home-codex-agents/.codex/agents/$agent.toml" \
    "default Codex agent install must render gpt-5.6-sol for $agent"
  grep_required '^model_reasoning_effort = "max"$' "$tmp/home-codex-agents/.codex/agents/$agent.toml" \
    "default Codex agent install must render max reasoning for $agent"
done
[[ ! -e "$tmp/home-codex-agents/.codex/AGENTS.md" ]] \
  || fail "codex-agents target must not write global AGENTS policy"

HOME="$tmp/home-codex-agents-cost" "$ROOT/install.sh" --profile cost-first codex-agents >/dev/null
for agent in teamwork-explorer teamwork-designer; do
  grep_required '^model = "gpt-5.6-luna"$' "$tmp/home-codex-agents-cost/.codex/agents/$agent.toml" \
    "cost-first Codex agent install must use Luna for $agent"
  grep_required '^model_reasoning_effort = "medium"$' "$tmp/home-codex-agents-cost/.codex/agents/$agent.toml" \
    "cost-first Codex agent install must use medium reasoning for $agent"
done
grep_required '^model = "gpt-5.6-terra"$' "$tmp/home-codex-agents-cost/.codex/agents/teamwork-worker.toml" \
  "cost-first Codex Worker must use Terra"
grep_required '^model_reasoning_effort = "medium"$' "$tmp/home-codex-agents-cost/.codex/agents/teamwork-worker.toml" \
  "cost-first Codex Worker must use medium reasoning"
for agent in teamwork-judge teamwork-reviewer; do
  grep_required '^model = "gpt-5.6-sol"$' "$tmp/home-codex-agents-cost/.codex/agents/$agent.toml" \
    "cost-first Codex agent install must use Sol for $agent"
  grep_required '^model_reasoning_effort = "high"$' "$tmp/home-codex-agents-cost/.codex/agents/$agent.toml" \
    "cost-first Codex agent install must keep high reasoning for $agent"
done
for agent in teamwork-deep-judge teamwork-deep-reviewer; do
  grep_required '^model = "gpt-5.6-sol"$' "$tmp/home-codex-agents-cost/.codex/agents/$agent.toml" \
    "cost-first Codex agent install must use Sol for $agent"
  grep_required '^model_reasoning_effort = "max"$' "$tmp/home-codex-agents-cost/.codex/agents/$agent.toml" \
    "cost-first Codex agent install must use max reasoning for $agent"
done

HOME="$tmp/home-codex-cost" "$ROOT/install.sh" --profile cost-first codex >/dev/null
check_lean_policy "$tmp/home-codex-cost/.codex/AGENTS.md" cost-first "cost-first Codex policy"

HOME="$tmp/home-codex-policy-cost" "$ROOT/install.sh" --profile cost-first codex-policy > "$tmp/codex-policy-cost.out"
check_lean_policy "$tmp/codex-policy-cost.out" cost-first "cost-first codex-policy output"
[[ ! -e "$tmp/home-codex-policy-cost/.codex/AGENTS.md" ]] \
  || fail "cost-first codex-policy target must not write global AGENTS policy"

HOME="$tmp/home-codex-agents-gpt56-role" "$ROOT/install.sh" --profile gpt56-role codex-agents >/dev/null
grep_required '^model = "gpt-5.6-terra"$' "$tmp/home-codex-agents-gpt56-role/.codex/agents/teamwork-explorer.toml" \
  "gpt56-role Explorer must use gpt-5.6-terra"
grep_required '^model_reasoning_effort = "medium"$' "$tmp/home-codex-agents-gpt56-role/.codex/agents/teamwork-explorer.toml" \
  "gpt56-role Explorer must use medium reasoning"
grep_required '^model = "gpt-5.6-sol"$' "$tmp/home-codex-agents-gpt56-role/.codex/agents/teamwork-worker.toml" \
  "gpt56-role Worker must use gpt-5.6-sol"
grep_required '^model_reasoning_effort = "medium"$' "$tmp/home-codex-agents-gpt56-role/.codex/agents/teamwork-worker.toml" \
  "gpt56-role Worker must use medium reasoning"
for agent in teamwork-designer teamwork-judge teamwork-reviewer; do
  grep_required '^model = "gpt-5.6-sol"$' "$tmp/home-codex-agents-gpt56-role/.codex/agents/$agent.toml" \
    "gpt56-role must render gpt-5.6-sol for $agent"
  grep_required '^model_reasoning_effort = "high"$' "$tmp/home-codex-agents-gpt56-role/.codex/agents/$agent.toml" \
    "gpt56-role must render high reasoning for $agent"
done
for agent in teamwork-deep-judge teamwork-deep-reviewer; do
  grep_required '^model = "gpt-5.6-sol"$' "$tmp/home-codex-agents-gpt56-role/.codex/agents/$agent.toml" \
    "gpt56-role must render gpt-5.6-sol for $agent"
  grep_required '^model_reasoning_effort = "max"$' "$tmp/home-codex-agents-gpt56-role/.codex/agents/$agent.toml" \
    "gpt56-role must render max reasoning for $agent"
done

HOME="$tmp/home-codex-gpt56-role" "$ROOT/install.sh" --profile gpt56-role codex >/dev/null
check_lean_policy "$tmp/home-codex-gpt56-role/.codex/AGENTS.md" gpt56-role "gpt56-role Codex policy"
grep_absent 'gpt-5.6-terra medium for Explorer' \
  "global policy must defer exact GPT-5.6 mappings to agent files" \
  "$tmp/home-codex-gpt56-role/.codex/AGENTS.md"

HOME="$tmp/home-codex-policy-gpt56-role" "$ROOT/install.sh" --profile gpt56-role codex-policy > "$tmp/codex-policy-gpt56-role.out"
check_lean_policy "$tmp/codex-policy-gpt56-role.out" gpt56-role "gpt56-role codex-policy output"
[[ ! -e "$tmp/home-codex-policy-gpt56-role/.codex/AGENTS.md" ]] \
  || fail "gpt56-role codex-policy target must not write global AGENTS policy"

project_codex_gpt56_role="$tmp/project-codex-gpt56-role"
mkdir -p "$project_codex_gpt56_role"
HOME="$tmp/home-project-codex-gpt56-role" "$ROOT/install.sh" --profile gpt56-role --project-root "$project_codex_gpt56_role" project-codex-agents >/dev/null
grep_required '^model = "gpt-5.6-terra"$' "$project_codex_gpt56_role/.codex/agents/teamwork-explorer.toml" \
  "project-codex-agents must render gpt-5.6-terra for Explorer"
grep_required '^model = "gpt-5.6-sol"$' "$project_codex_gpt56_role/.codex/agents/teamwork-worker.toml" \
  "project-codex-agents must render gpt-5.6-sol for Worker"
grep_required '^model_reasoning_effort = "max"$' "$project_codex_gpt56_role/.codex/agents/teamwork-deep-reviewer.toml" \
  "project-codex-agents must render max for Deep Reviewer"
[[ ! -e "$project_codex_gpt56_role/.cursor" ]] \
  || fail "project-codex-agents must not write Cursor project agents"
[[ ! -e "$project_codex_gpt56_role/.claude" ]] \
  || fail "project-codex-agents must not write Claude project agents"

HOME="$tmp/home-cursor-gpt56-role" "$ROOT/install.sh" --profile gpt56-role cursor-agents >/dev/null
for agent in explore designer; do
  grep_required '^model: claude-sonnet-4-6$' "$tmp/home-cursor-gpt56-role/.cursor/agents/$agent.md" \
    "gpt56-role must preserve Cursor performance model for $agent"
done
grep_required '^model: composer-2.5-fast$' "$tmp/home-cursor-gpt56-role/.cursor/agents/worker.md" \
  "gpt56-role must preserve Cursor performance model for Worker"
for agent in judge code-reviewer deep-judge deep-reviewer; do
  grep_required '^model: claude-opus-4-8-thinking-high$' "$tmp/home-cursor-gpt56-role/.cursor/agents/$agent.md" \
    "gpt56-role must preserve Cursor review model for $agent"
done

HOME="$tmp/home-claude-gpt56-role" "$ROOT/install.sh" --profile gpt56-role claude-agents >/dev/null
for agent in explore designer worker; do
  grep_required '^model: sonnet$' "$tmp/home-claude-gpt56-role/.claude/agents/$agent.md" \
    "gpt56-role must preserve Claude performance model for $agent"
  grep_required '^effort: medium$' "$tmp/home-claude-gpt56-role/.claude/agents/$agent.md" \
    "gpt56-role must preserve Claude medium effort for $agent"
done
for agent in judge code-reviewer; do
  grep_required '^model: opus$' "$tmp/home-claude-gpt56-role/.claude/agents/$agent.md" \
    "gpt56-role must preserve Claude review model for $agent"
  grep_required '^effort: high$' "$tmp/home-claude-gpt56-role/.claude/agents/$agent.md" \
    "gpt56-role must preserve Claude high effort for $agent"
done
for agent in deep-judge deep-reviewer; do
  grep_required '^model: opus$' "$tmp/home-claude-gpt56-role/.claude/agents/$agent.md" \
    "gpt56-role must preserve Claude deep model for $agent"
  grep_required '^effort: max$' "$tmp/home-claude-gpt56-role/.claude/agents/$agent.md" \
    "gpt56-role must use Claude max effort for $agent"
done

for profile in gpt56-high gpt56-xhigh gpt55-high gpt55-xhigh; do
  profile_home="$tmp/home-cross-platform-$profile"
  HOME="$profile_home" "$ROOT/install.sh" --profile "$profile" all >/dev/null
  for agent in explore designer; do
    grep_required '^model: claude-sonnet-4-6$' "$profile_home/.cursor/agents/$agent.md" \
      "$profile must keep the current Cursor model for $agent"
  done
  grep_required '^model: composer-2.5-fast$' "$profile_home/.cursor/agents/worker.md" \
    "$profile must keep the current Cursor model for Worker"
  for agent in judge code-reviewer deep-judge deep-reviewer; do
    grep_required '^model: claude-opus-4-8-thinking-high$' "$profile_home/.cursor/agents/$agent.md" \
      "$profile must keep the current Cursor review model for $agent"
  done
  for agent in explore designer worker; do
    grep_required '^model: sonnet$' "$profile_home/.claude/agents/$agent.md" \
      "$profile must keep the current Claude routine model for $agent"
  done
  for agent in judge code-reviewer deep-judge deep-reviewer; do
    grep_required '^model: opus$' "$profile_home/.claude/agents/$agent.md" \
      "$profile must keep the current Claude review model for $agent"
  done
  if [[ "$profile" == *xhigh ]]; then
    expected_deep_effort="xhigh"
  else
    expected_deep_effort="max"
  fi
  for agent in deep-judge deep-reviewer; do
    grep_required "^effort: $expected_deep_effort$" "$profile_home/.claude/agents/$agent.md" \
      "$profile must render $expected_deep_effort for Claude $agent"
  done
done

HOME="$tmp/home-codex-agents-high" "$ROOT/install.sh" --profile gpt55-high codex-agents >/dev/null
for agent in teamwork-explorer teamwork-worker teamwork-designer teamwork-judge teamwork-reviewer teamwork-deep-judge teamwork-deep-reviewer; do
  grep_required '^model = "gpt-5.6-sol"$' "$tmp/home-codex-agents-high/.codex/agents/$agent.toml" \
    "legacy gpt55-high alias must render gpt-5.6-sol for $agent"
  grep_required '^model_reasoning_effort = "high"$' "$tmp/home-codex-agents-high/.codex/agents/$agent.toml" \
    "gpt55-high Codex agent install must render high reasoning for $agent"
done
HOME="$tmp/home-codex-agents-gpt56-high" "$ROOT/install.sh" --profile gpt56-high codex-agents >/dev/null
for agent in teamwork-explorer teamwork-worker teamwork-designer teamwork-judge teamwork-reviewer teamwork-deep-judge teamwork-deep-reviewer; do
  cmp -s "$tmp/home-codex-agents-gpt56-high/.codex/agents/$agent.toml" \
    "$tmp/home-codex-agents-high/.codex/agents/$agent.toml" \
    || fail "gpt55-high compatibility alias must match gpt56-high for $agent"
done

HOME="$tmp/home-codex-high" "$ROOT/install.sh" --profile gpt55-high codex >/dev/null
check_lean_policy "$tmp/home-codex-high/.codex/AGENTS.md" gpt55-high "gpt55-high Codex policy"

HOME="$tmp/home-codex-policy-high" "$ROOT/install.sh" --profile gpt55-high codex-policy > "$tmp/codex-policy-high.out"
check_lean_policy "$tmp/codex-policy-high.out" gpt55-high "gpt55-high codex-policy output"
[[ ! -e "$tmp/home-codex-policy-high/.codex/AGENTS.md" ]] \
  || fail "gpt55-high codex-policy target must not write global AGENTS policy"

project_codex_high="$tmp/project-codex-high"
mkdir -p "$project_codex_high"
HOME="$tmp/home-project-codex-high" "$ROOT/install.sh" --profile gpt55-high --project-root "$project_codex_high" project-codex-agents >/dev/null
for agent in teamwork-explorer teamwork-worker teamwork-designer teamwork-judge teamwork-reviewer teamwork-deep-judge teamwork-deep-reviewer; do
  grep_required '^model = "gpt-5.6-sol"$' "$project_codex_high/.codex/agents/$agent.toml" \
    "legacy gpt55-high project alias must render gpt-5.6-sol for $agent"
  grep_required '^model_reasoning_effort = "high"$' "$project_codex_high/.codex/agents/$agent.toml" \
    "project-codex-agents must render high reasoning for $agent"
done
[[ ! -e "$project_codex_high/.cursor" ]] \
  || fail "project-codex-agents target must not write Cursor project agents"
[[ ! -e "$project_codex_high/.claude" ]] \
  || fail "project-codex-agents target must not write Claude project agents"

HOME="$tmp/home-codex-agents-xhigh" "$ROOT/install.sh" --profile gpt55-xhigh codex-agents >/dev/null
for agent in teamwork-explorer teamwork-worker teamwork-designer teamwork-judge teamwork-reviewer teamwork-deep-judge teamwork-deep-reviewer; do
  grep_required '^model = "gpt-5.6-sol"$' "$tmp/home-codex-agents-xhigh/.codex/agents/$agent.toml" \
    "legacy gpt55-xhigh alias must render gpt-5.6-sol for $agent"
  grep_required '^model_reasoning_effort = "xhigh"$' "$tmp/home-codex-agents-xhigh/.codex/agents/$agent.toml" \
    "gpt55-xhigh Codex agent install must render xhigh reasoning for $agent"
done
HOME="$tmp/home-codex-agents-gpt56-xhigh" "$ROOT/install.sh" --profile gpt56-xhigh codex-agents >/dev/null
for agent in teamwork-explorer teamwork-worker teamwork-designer teamwork-judge teamwork-reviewer teamwork-deep-judge teamwork-deep-reviewer; do
  cmp -s "$tmp/home-codex-agents-gpt56-xhigh/.codex/agents/$agent.toml" \
    "$tmp/home-codex-agents-xhigh/.codex/agents/$agent.toml" \
    || fail "gpt55-xhigh compatibility alias must match gpt56-xhigh for $agent"
done

HOME="$tmp/home-codex-xhigh" "$ROOT/install.sh" --profile gpt55-xhigh codex >/dev/null
check_lean_policy "$tmp/home-codex-xhigh/.codex/AGENTS.md" gpt55-xhigh "gpt55-xhigh Codex policy"

HOME="$tmp/home-codex-policy-xhigh" "$ROOT/install.sh" --profile gpt55-xhigh codex-policy > "$tmp/codex-policy-xhigh.out"
check_lean_policy "$tmp/codex-policy-xhigh.out" gpt55-xhigh "gpt55-xhigh codex-policy output"
[[ ! -e "$tmp/home-codex-policy-xhigh/.codex/AGENTS.md" ]] \
  || fail "gpt55-xhigh codex-policy target must not write global AGENTS policy"

project_codex_xhigh="$tmp/project-codex-xhigh"
mkdir -p "$project_codex_xhigh"
HOME="$tmp/home-project-codex-xhigh" "$ROOT/install.sh" --profile gpt55-xhigh --project-root "$project_codex_xhigh" project-codex-agents >/dev/null
for agent in teamwork-explorer teamwork-worker teamwork-designer teamwork-judge teamwork-reviewer teamwork-deep-judge teamwork-deep-reviewer; do
  grep_required '^model = "gpt-5.6-sol"$' "$project_codex_xhigh/.codex/agents/$agent.toml" \
    "legacy gpt55-xhigh project alias must render gpt-5.6-sol for $agent"
  grep_required '^model_reasoning_effort = "xhigh"$' "$project_codex_xhigh/.codex/agents/$agent.toml" \
    "project-codex-agents must render xhigh reasoning for $agent"
done
[[ ! -e "$project_codex_xhigh/.cursor" ]] \
  || fail "project-codex-agents target must not write Cursor project agents"
[[ ! -e "$project_codex_xhigh/.claude" ]] \
  || fail "project-codex-agents target must not write Claude project agents"

project_update="$tmp/project-update"
mkdir -p "$project_update"
HOME="$tmp/home-project-update" "$ROOT/install.sh" all >/dev/null
printf '\n# stale global agent drift fixture\n' >> "$tmp/home-project-update/.codex/agents/teamwork-worker.toml"
HOME="$tmp/home-project-update" "$ROOT/scripts/check-update.sh" --no-fetch > "$tmp/global-agent-stale-report.out" || true
grep_required 'drift(missing=0,changed=1)' "$tmp/global-agent-stale-report.out" \
  "check-update report must show global agent content drift"
grep_required 'Summary: .*issue' "$tmp/global-agent-stale-report.out" \
  "check-update report must count global agent content drift"
HOME="$tmp/home-project-update" "$ROOT/install.sh" all >/dev/null
HOME="$tmp/home-project-update" "$ROOT/install.sh" --project-root "$project_update" project >/dev/null
HOME="$tmp/home-project-update" "$ROOT/scripts/check-update.sh" --readiness --project "$project_update" --no-fetch > "$tmp/project-update-ready.out"
grep_required '^INSTALL_READY=yes$' "$tmp/project-update-ready.out" \
  "check-update project readiness must pass after fresh project install"
printf '\n# stale agent drift fixture\n' >> "$project_update/.codex/agents/teamwork-worker.toml"
HOME="$tmp/home-project-update" "$ROOT/scripts/check-update.sh" --project "$project_update" --no-fetch > "$tmp/project-update-agent-stale-report.out" || true
grep_required 'project codex agent content: drift(missing=0,changed=1)' "$tmp/project-update-agent-stale-report.out" \
  "check-update report must show project agent content drift"
HOME="$tmp/home-project-update" "$ROOT/scripts/check-update.sh" --readiness --project "$project_update" --no-fetch > "$tmp/project-update-agent-stale.out"
grep_required '^INSTALL_READY=no$' "$tmp/project-update-agent-stale.out" \
  "check-update project readiness must fail on project agent drift"
grep_required 'project-codex-agent-content' "$tmp/project-update-agent-stale.out" \
  "check-update readiness must report project agent content drift"
HOME="$tmp/home-project-update" "$ROOT/install.sh" --project-root "$project_update" project >/dev/null
printf '%s\n' '0.0.0' > "$project_update/.cursor/skills/.teamwork-version"
printf '\n# stale drift fixture\n' >> "$project_update/.cursor/skills/using-teamwork/SKILL.md"
HOME="$tmp/home-project-update" "$ROOT/scripts/check-update.sh" --readiness --project "$project_update" --no-fetch > "$tmp/project-update-stale.out"
grep_required '^INSTALL_READY=no$' "$tmp/project-update-stale.out" \
  "check-update project readiness must fail on project drift"
grep_required 'project-version-drift' "$tmp/project-update-stale.out" \
  "check-update readiness must report project version drift"
grep_required 'project-skill-content' "$tmp/project-update-stale.out" \
  "check-update readiness must report project skill content drift"

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
  grep_required '^model: composer-2.5$' "$tmp/home-cursor-cost/.cursor/agents/$agent.md" \
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
check_lean_policy "$cursor_policy_out" performance-first "cursor-policy output"
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
check_lean_policy "$tmp/cursor-policy-copy.clipboard" performance-first \
  "cursor-policy clipboard output"
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
  grep_required '^effort: max$' "$tmp/home-claude/.claude/agents/$agent.md" \
    "Claude install must render max effort for $agent"
done
grep_required '<!-- TEAMWORK_CLAUDE_GLOBAL_START -->' "$tmp/home-claude/.claude/CLAUDE.md" \
  "Claude install must create Teamwork global CLAUDE block"
check_lean_policy "$tmp/home-claude/.claude/CLAUDE.md" performance-first "Claude global policy"

claude_policy_out="$tmp/claude-policy.out"
HOME="$tmp/home-claude-policy" "$ROOT/install.sh" claude-policy > "$claude_policy_out"
grep_required '<!-- TEAMWORK_CLAUDE_GLOBAL_START -->' "$claude_policy_out" \
  "claude-policy target must print Teamwork global policy start marker"
check_lean_policy "$claude_policy_out" performance-first "claude-policy output"
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
for agent in deep-judge deep-reviewer; do
  grep_required '^effort: max$' "$tmp/home-claude-cost/.claude/agents/$agent.md" \
    "cost-first Claude agent install must use max effort for $agent"
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
check_lean_policy "$claude_preserve_home/.claude/CLAUDE.md" performance-first \
  "refreshed Claude global policy"
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
