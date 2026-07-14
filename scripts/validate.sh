#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENTRYPOINT="$ROOT/skills/using-teamwork/SKILL.md"
SKILLS=(
  using-teamwork
  grill-me
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
  local policy_words
  policy_words="$(awk '
    /<!-- TEAMWORK_(CODEX|CURSOR|CLAUDE)_GLOBAL_START -->/ { inside = 1 }
    inside { print }
    /<!-- TEAMWORK_(CODEX|CURSOR|CLAUDE)_GLOBAL_END -->/ { inside = 0 }
  ' "$file" | wc -w | tr -d ' ')"
  [[ "$policy_words" -le 190 ]] \
    || fail "$label must remain a guard-only global policy ($policy_words > 190)"
  grep_required "Work within the user's request" "$file" "$label must preserve request scope"
  grep_required 'routine reversible choices' "$file" "$label must permit routine reversible choices"
  grep_required 'Route explicit grill/question-first' "$file" \
    "$label must route explicit grill intent"
  grep_required 'Never invent or hide gaps' "$file" "$label must preserve required-state safety"
  grep_required 'Ask only when the user must supply' "$file" "$label must preserve the shared ask boundary"
  grep_required 'Pause only dependent work' "$file" "$label must scope unresolved-question blocking"
  grep_required 'Delegate only worthwhile independent scope' "$file" \
    "$label must keep delegation economic"
  grep_required 'agents own models; active profile' "$file" \
    "$label must keep model mappings out of global policy"
  grep_required "active profile: ${profile}\. Use project-local init" "$file" "$label must record active profile $profile"
  if [[ "$label" == *Cursor* || "$label" == *Claude* ]]; then
    ! grep -Eq 'request_user_input|Codex CLI|Codex native|every material user decision|grill ceremony|text choice card' "$file" \
      || fail "$label must not contain Codex-native adapter wording"
  fi
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

for removed in "commands" "bin/raoctl.py"; do
  [[ ! -e "$ROOT/$removed" ]] || fail "removed runtime surface still exists: $removed"
done
expected_hook_inventory="$(printf '%s\n' hooks.json notify.py | sort)"
actual_hook_inventory="$(find "$ROOT/hooks" -maxdepth 1 -type f -exec basename {} \; | sort)"
[[ "$actual_hook_inventory" == "$expected_hook_inventory" ]] \
  || fail "hooks/ must contain only the notification contract: hooks.json notify.py"
if git -C "$ROOT" ls-files '.cursor' 2>/dev/null | grep -q .; then
  fail ".cursor/ must not be tracked; use ./install.sh project for local project skills"
fi
if git -C "$ROOT" ls-files '.agents' 2>/dev/null | grep -q .; then
  fail ".agents/ must not be tracked; use ./install.sh project for local Codex project skills"
fi
if git -C "$ROOT" ls-files '.codex' 2>/dev/null | grep -q .; then
  fail ".codex/ must not be tracked; use ./install.sh project for local project agents"
fi
grep_required '^\.agents/$' "$ROOT/.gitignore" ".gitignore must ignore local .agents/ install output"
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
for reference in artifact-protocol check-update debug-mode eval-gate goal-iteration optional-skills plan-output project-init research-protocol review-checks review-lenses role-playbook routing-policy subagent-contract subagent-dispatch verification-patterns workflow-contract workflow-orchestration; do
  ref_file="$ROOT/skills/using-teamwork/references/$reference.md"
  [[ -f "$ref_file" ]] || fail "missing skills/using-teamwork/references/$reference.md"
  git_known_package_file "skills/using-teamwork/references/$reference.md" \
    || fail "skills/using-teamwork/references/$reference.md is not known to git; use git add -N before release validation"
done

[[ ! -d "$ROOT/skills/grill-me/references" ]] \
  || [[ -z "$(find "$ROOT/skills/grill-me/references" -type f -print -quit)" ]] \
  || fail "grill-me must keep its complete semantic contract in the lean SKILL.md"

for template in teamwork-index-template.json teamwork-index-readme-template.md teamwork-current-template.md; do
  template_file="$ROOT/skills/using-teamwork/references/$template"
  [[ -f "$template_file" ]] || fail "missing skills/using-teamwork/references/$template"
  git_known_package_file "skills/using-teamwork/references/$template" \
    || fail "skills/using-teamwork/references/$template is not known to git; use git add -N before release validation"
done

expected_reference_inventory="$(
  printf '%s\n' \
    artifact-protocol.md check-update.md debug-mode.md eval-gate.md goal-iteration.md optional-skills.md plan-output.md \
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
for case_id in complex-autonomy-control ordinary-material-clarification-control question-first-explicit-grill question-first-explicit-lightweight-grill question-first-complex-uncertainty question-first-lightweight-control grill-question-value-stop grill-zero-question-low-value grill-language-ownership-contrast grill-rename-ownership-contrast grill-boundary-ownership-contrast grill-observable-preference-contrast grill-threshold-evidence-contrast grill-reversibility-ownership-contrast; do
  [[ -f "$ROOT/evals/teamwork/cases/$case_id.dev.json" ]] \
    || fail "missing question-first eval case: $case_id"
  grep_required "\"case_id\":\"$case_id\"" "$ROOT/evals/teamwork/outputs/question-first/dev.jsonl" \
    "question-first eval outputs must include $case_id"
done
grep_required '"platforms":\["codex","cursor","claude"\]' "$ROOT/evals/teamwork/outputs/question-first/dev.jsonl" \
  "question-first fixtures must declare their static cross-platform contract"
grep_required 'skills/ and install.sh inventories' "$ROOT/evals/teamwork/outputs/question-first/dev.jsonl" \
  "fact-lookup grill fixture must cite bounded evidence before asking"
[[ -f "$ROOT/scripts/eval-teamwork.py" ]] || fail "missing scripts/eval-teamwork.py"
git_known_package_file "scripts/eval-teamwork.py" \
  || fail "scripts/eval-teamwork.py is not known to git; use git add -N before release validation"
python3 "$ROOT/scripts/eval-teamwork.py" --split dev >/dev/null
[[ -x "$ROOT/scripts/run-teamwork-live-eval.py" ]] || fail "live eval runner must be executable"
git_known_package_file "scripts/run-teamwork-live-eval.py" \
  || fail "scripts/run-teamwork-live-eval.py is not known to git; use git add -N before release validation"
[[ -f "$ROOT/scripts/test_live_eval_runner.py" ]] || fail "missing live eval runner tests"
git_known_package_file "scripts/test_live_eval_runner.py" \
  || fail "scripts/test_live_eval_runner.py is not known to git; use git add -N before release validation"
[[ -f "$ROOT/scripts/test_eval_teamwork_mutations.py" ]] || fail "missing grill contract mutation tests"
git_known_package_file "scripts/test_eval_teamwork_mutations.py" \
  || fail "scripts/test_eval_teamwork_mutations.py is not known to git; use git add -N before release validation"
[[ -f "$ROOT/scripts/grill_contract.py" ]] || fail "missing shared grill contract checks"
git_known_package_file "scripts/grill_contract.py" \
  || fail "scripts/grill_contract.py is not known to git; use git add -N before release validation"
[[ -f "$ROOT/scripts/codex_routing_config.py" ]] || fail "missing Codex routing config module"
[[ -f "$ROOT/scripts/configure-codex-routing.py" ]] || fail "missing Codex routing config CLI"
[[ -f "$ROOT/scripts/test_codex_routing_config.py" ]] || fail "missing Codex routing config tests"
[[ -x "$ROOT/scripts/codex_app_server_user_input.py" ]] || fail "missing Codex app-server user-input harness"
[[ -f "$ROOT/scripts/test_codex_app_server_user_input.py" ]] || fail "missing Codex app-server user-input tests"
python3 -m py_compile "$ROOT/scripts/grill_contract.py" "$ROOT/scripts/run-teamwork-live-eval.py" "$ROOT/scripts/test_live_eval_runner.py" \
  "$ROOT/scripts/test_eval_teamwork_mutations.py" "$ROOT/scripts/codex_routing_config.py" \
  "$ROOT/scripts/configure-codex-routing.py" "$ROOT/scripts/test_codex_routing_config.py" \
  "$ROOT/scripts/codex_app_server_user_input.py" "$ROOT/scripts/test_codex_app_server_user_input.py"
PYTHONDONTWRITEBYTECODE=1 python3 "$ROOT/scripts/test_live_eval_runner.py" >/dev/null
PYTHONDONTWRITEBYTECODE=1 python3 "$ROOT/scripts/test_eval_teamwork_mutations.py" >/dev/null
PYTHONDONTWRITEBYTECODE=1 python3 "$ROOT/scripts/test_codex_routing_config.py" >/dev/null
PYTHONDONTWRITEBYTECODE=1 python3 "$ROOT/scripts/test_codex_app_server_user_input.py" >/dev/null
grep_required 'one class: `BLOCKER`, `FOLLOW-UP`, or `SUGGESTION`' \
  "$ROOT/skills/teamwork-review/SKILL.md" \
  "review taxonomy must remain BLOCKER, FOLLOW-UP, or SUGGESTION"
grep_required '`BLOCKER | FOLLOW-UP | SUGGESTION` findings' \
  "$ROOT/skills/using-teamwork/references/role-playbook.md" \
  "role playbook taxonomy must remain BLOCKER | FOLLOW-UP | SUGGESTION"
grep_absent '`blocker | major | minor`' \
  "role playbook must not restore blocker | major | minor taxonomy" \
  "$ROOT/skills/using-teamwork/references/role-playbook.md"
grep_required 'Use Codex native goal state only when the user explicitly requests Goal mode or' \
  "$ROOT/skills/teamwork-goal/SKILL.md" \
  "native goal state must require explicit user request or accepted Goal Proposal"
grep_required 'accepts a Goal Proposal' "$ROOT/skills/teamwork-goal/SKILL.md" \
  "native goal state must accept an approved Goal Proposal"
grep_absent 'native goal state.*when available' \
  "native goal state must not activate merely when available" \
  "$ROOT/skills/teamwork-goal/SKILL.md"
[[ ! -e "$ROOT/scripts/teamwork_contract.py" && ! -e "$ROOT/scripts/test_teamwork_contract.py" ]] \
  || fail "retired Task Contract validator must remain absent"
[[ ! -e "$ROOT/scripts/teamwork_findings.py" && ! -e "$ROOT/scripts/test_teamwork_findings.py" ]] \
  || fail "retired Finding-state validator must remain absent"
for case_id in \
  ask-native-simple-control ask-discoverable-fact-control \
  ask-required-input-research ask-required-observation-debug \
  ask-required-input-execute ask-required-observation-review ask-required-input-goal \
  plan-ask-readiness review-bounded-recheck goal-dependent-branch-retry \
  ask-confirmation-authority ask-subagent-root-ownership \
  ask-independent-readonly-progress ask-text-fallback; do
  [[ -f "$ROOT/evals/teamwork/cases/$case_id.dev.json" ]] \
    || fail "missing ask-predicate eval case: $case_id"
done
while IFS= read -r active_source; do
  if grep -Eiq 'Task Contract|Contract version|Finding-state|Finding state|FINDING_STATUSES|base_review_id|corrective delta review|Replay Preflight|Stage Entry Card|truth identity|frozen card|scope delta gate' "$active_source"; then
    fail "retired workflow lifecycle term remains in ${active_source#"$ROOT"/}"
  fi
done < <(
  find "$ROOT/skills" "$ROOT/templates" "$ROOT/evals/teamwork/cases" "$ROOT/evals/teamwork/rubrics" \
    -type f ! -name '*.pyc' ! -path '*/__pycache__/*' | sort
)
grep_absent 'parse_close_packet\|expected_question_ids\|expected_close\|blocked_route\|pilot_only\|activation_evidence' \
  "active grill eval code must not restore the retired lifecycle or native-promotion schema" \
  "$ROOT/scripts/run-teamwork-live-eval.py" "$ROOT/scripts/codex_app_server_user_input.py"
grep_required '"category": "grill"' "$ROOT/evals/teamwork/live-cases/grill-multiturn-pilot.json" \
  "live evals must include a grill category"
live_eval_tmp="$(mktemp -d)"
CLEANUP_PATHS+=("$live_eval_tmp")
python3 "$ROOT/scripts/run-teamwork-live-eval.py" \
  --arm validate-dry-run \
  --model gpt-5.6-sol \
  --effort max \
  --workdir "$ROOT" \
  --output "$live_eval_tmp/output.jsonl" \
  --cases \
    "$ROOT/evals/teamwork/live-cases/lightweight-pilot.json" \
    "$ROOT/evals/teamwork/live-cases/grill-multiturn-pilot.json" \
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
index_pointer_tmp="$(mktemp -d "${TMPDIR:-/tmp}/teamwork-index-pointer.XXXXXX")"
CLEANUP_PATHS+=("$index_pointer_tmp")
sed 's#"current": "docs/teamwork/current.md"#"current": "docs/teamwork/missing.md"#' \
  "$ROOT/skills/using-teamwork/references/teamwork-index-template.json" \
  > "$index_pointer_tmp/missing-pointer.json"
if python3 "$ROOT/scripts/validate_teamwork_index.py" \
  "$index_pointer_tmp/missing-pointer.json" >/dev/null 2>&1; then
  fail "Teamwork index validator accepted an active pointer without a matching entry"
fi
sed 's/"status": "active"/"status": "candidate"/' \
  "$ROOT/skills/using-teamwork/references/teamwork-index-template.json" \
  > "$index_pointer_tmp/candidate-pointer.json"
if python3 "$ROOT/scripts/validate_teamwork_index.py" \
  "$index_pointer_tmp/candidate-pointer.json" >/dev/null 2>&1; then
  fail "Teamwork index validator accepted a candidate entry as active truth"
fi
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

# --- Notification hooks and private session audit ---
for hook_file in hooks/hooks.json hooks/notify.py scripts/configure-notifications.py scripts/test_notify_hook.py scripts/audit-codex-sessions.py; do
  [[ -f "$ROOT/$hook_file" ]] || fail "missing $hook_file"
  git_known_package_file "$hook_file" \
    || fail "$hook_file is not known to git; use git add -N before release validation"
done
python3 -m json.tool "$ROOT/hooks/hooks.json" >/dev/null
python3 - "$ROOT" <<'PY'
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
data = json.loads((root / "hooks/hooks.json").read_text())
hooks = data.get("hooks")
if set(hooks or {}) != {"Stop", "PermissionRequest"}:
    raise SystemExit("FAIL: hooks.json must contain only Stop and PermissionRequest")
for event, groups in hooks.items():
    if len(groups) != 1 or set(groups[0]) != {"hooks"}:
        raise SystemExit(f"FAIL: {event} must have one minimal matcher-free group")
    handlers = groups[0]["hooks"]
    if len(handlers) != 1 or handlers[0].get("type") != "command":
        raise SystemExit(f"FAIL: {event} must have one command handler")
    command = handlers[0].get("command", "")
    if "hooks/notify.py" not in command:
        raise SystemExit(f"FAIL: {event} must call hooks/notify.py")
    if any(field in handlers[0] for field in ("decision", "continue", "reason", "prompt")):
        raise SystemExit(f"FAIL: {event} hook must not control workflow")
PY
PYTHONDONTWRITEBYTECODE=1 python3 "$ROOT/scripts/test_notify_hook.py" >/dev/null
python3 -m py_compile \
  "$ROOT/hooks/notify.py" \
  "$ROOT/scripts/configure-notifications.py" \
  "$ROOT/scripts/audit-codex-sessions.py" \
  "$ROOT/scripts/test_notify_hook.py"

audit_tmp="$(mktemp -d)"
CLEANUP_PATHS+=("$audit_tmp")
audit_root_id="11111111-1111-4111-8111-111111111111"
audit_child_id="22222222-2222-4222-8222-222222222222"
printf '%s\n' \
  "{\"type\":\"session_meta\",\"payload\":{\"id\":\"$audit_root_id\",\"timestamp\":\"2026-07-13T00:00:00Z\",\"thread_source\":\"user\"}}" \
  '{"type":"turn_context","payload":{"model":"gpt-5.6-sol","effort":"high"}}' \
  '{"type":"response_item","payload":{"type":"function_call","name":"spawn_agent","arguments":"{\"task_name\":\"worker\",\"fork_turns\":\"none\",\"message\":\"redacted fixture\"}"}}' \
  "{\"type\":\"event_msg\",\"payload\":{\"type\":\"sub_agent_activity\",\"kind\":\"started\",\"agent_thread_id\":\"$audit_child_id\",\"agent_path\":\"/root/worker\"}}" \
  '{"type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":100,"cached_input_tokens":80,"output_tokens":10,"reasoning_output_tokens":2,"total_tokens":110},"model_context_window":1000}}}' \
  > "$audit_tmp/rollout-$audit_root_id.jsonl"
printf '%s\n' \
  "{\"type\":\"session_meta\",\"payload\":{\"id\":\"$audit_child_id\",\"parent_thread_id\":\"$audit_root_id\",\"thread_source\":\"subagent\",\"source\":{\"subagent\":{\"thread_spawn\":{\"parent_thread_id\":\"$audit_root_id\",\"agent_path\":\"/root/worker\",\"agent_role\":null}}}}}" \
  '{"type":"turn_context","payload":{"model":"gpt-5.6-sol","effort":"high"}}' \
  '{"type":"event_msg","payload":{"type":"token_count","info":{"total_token_usage":{"input_tokens":50,"cached_input_tokens":40,"output_tokens":5,"reasoning_output_tokens":1,"total_tokens":55},"model_context_window":1000}}}' \
  > "$audit_tmp/rollout-$audit_child_id.jsonl"
python3 "$ROOT/scripts/audit-codex-sessions.py" \
  --sessions-root "$audit_tmp" \
  --profile "$audit_root_id=performance-first" \
  --json "$audit_root_id" > "$audit_tmp/report.json"
python3 - "$audit_tmp/report.json" <<'PY'
import json
import pathlib
import sys

report = json.loads(pathlib.Path(sys.argv[1]).read_text())["reports"][0]
assert report["profile_at_session_time"]["value"] == "performance-first"
assert report["root"]["fork_modes"] == {"none": 1}
assert len(report["direct_children"]) == 1
assert report["direct_children"][0]["model_attribution"] == "generic-or-parent-inherited"
assert report["aggregate"]["operational_token_telemetry"]["total_tokens"] == 165
PY

# --- Top-level docs ---
grep_required 'Codex、Cursor 和 Claude Code' "$ROOT/README.md" "README must name all supported platforms"
grep_required 'Codex-first' "$ROOT/README.md" "README must state Codex-first positioning"
grep_required 'check-update.sh' "$ROOT/README.md" "README must document check-update script"
grep_required '\[English\](README.en.md)' "$ROOT/README.md" "default README must link to English README"
grep_required '\[Codex\](CODEX.md)' "$ROOT/README.md" "README must link to the detailed Codex guide"
grep_required '\[Cursor\](CURSOR.md)' "$ROOT/README.md" "README must link to the detailed Cursor guide"
grep_required '\[Claude Code\](CLAUDE.md)' "$ROOT/README.md" "README must link to the detailed Claude Code guide"
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
grep_required 'Codex, Cursor, and Claude Code' "$ROOT/README.en.md" "English README must name all supported platforms"
grep_required 'Codex-first skill package' "$ROOT/README.en.md" "English README must state Codex-first positioning"
grep_required 'check-update.sh' "$ROOT/README.en.md" "English README must document check-update script"
grep_required '\[Codex guide\](CODEX.md)' "$ROOT/README.en.md" "English README must link to the detailed Codex guide"
grep_required '\[Cursor guide\](CURSOR.md)' "$ROOT/README.en.md" "English README must link to the detailed Cursor guide"
grep_required '\[Claude Code guide\](CLAUDE.md)' "$ROOT/README.en.md" "English README must link to the detailed Claude Code guide"
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
grep_required 'check-codex-routing.py' "$ROOT/CODEX.md" \
  "CODEX.md must document Codex routing readiness"
grep_required 'non-reserved `teamwork` namespace' "$ROOT/CODEX.md" \
  "CODEX.md must document the custom-agent routing namespace"
grep_required 'up to eight subagents' "$ROOT/CODEX.md" \
  "CODEX.md must document the Codex subagent limit"
grep_required 'grill-me' "$ROOT/CODEX.md" "CODEX.md must document explicit grill-me invocation"
grep_required 'test_live_eval_runner.py' "$ROOT/CODEX.md" "CODEX.md must document the offline live-runner test"
grep_required 'Task' "$ROOT/CURSOR.md" "CURSOR.md must document Cursor Task subagent policy"
grep_required 'Goal Mode' "$ROOT/CURSOR.md" "CURSOR.md must document Cursor goal mode"
grep_required 'subagent-dispatch.md' "$ROOT/CURSOR.md" "CURSOR.md must point to subagent dispatch reference"
grep_required '~/.cursor/agents/' "$ROOT/CURSOR.md" "CURSOR.md must document Cursor custom agents"
grep_required 'cursor-policy' "$ROOT/CURSOR.md" "CURSOR.md must document cursor-policy target"
grep_required 'grill-me' "$ROOT/CURSOR.md" "CURSOR.md must document grill-me"
grep_required 'Claude Code native capabilities' "$ROOT/CLAUDE.md" "CLAUDE.md must document native Claude Code capability policy"
grep_required 'Task' "$ROOT/CLAUDE.md" "CLAUDE.md must document Claude Code Task subagent policy"
grep_required 'subagent-dispatch.md' "$ROOT/CLAUDE.md" "CLAUDE.md must point to subagent dispatch reference"
grep_required 'rolling report' "$ROOT/CLAUDE.md" "CLAUDE.md must document Claude Code goal rolling report"
grep_required 'VERSION' "$ROOT/CLAUDE.md" "CLAUDE.md must document package version source"
grep_required '~/.claude/CLAUDE.md' "$ROOT/CLAUDE.md" "CLAUDE.md must document Claude global policy"
grep_required 'claude-policy' "$ROOT/CLAUDE.md" "CLAUDE.md must document claude-policy target"
grep_required 'deep-judge' "$ROOT/CLAUDE.md" "CLAUDE.md must document Deep Judge agent"
grep_required 'grill-me' "$ROOT/CLAUDE.md" "CLAUDE.md must document grill-me"
grep_required 'codex exec resume' "$ROOT/evals/teamwork/README.md" \
  "eval README must document persistent multi-turn Codex resume semantics"
grep_required 'test_live_eval_runner.py' "$ROOT/evals/teamwork/README.md" \
  "eval README must document the offline live-runner test"

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
grep_required 'configure_codex_routing' "$ROOT/install.sh" "installer must configure user-level Codex routing"
grep_required 'no-codex-routing' "$ROOT/install.sh" "installer must expose a Codex routing opt-out"
grep_absent 'configure_codex_native_questions\|codex-native-questions\|default_mode_request_user_input\|code_mode_only' \
  "installer must not own or mutate the host native-input capability" "$ROOT/install.sh"
grep_required 'one main thread plus up to eight' "$ROOT/install.sh" \
  "installer help must document the root-inclusive thread limit"
grep_required 'codex_routing_status' "$ROOT/scripts/check-update.sh" "check-update must inspect Codex routing"
grep_required 'latest_remote_tag_version' "$ROOT/scripts/check-update.sh" \
  "check-update must inspect the latest remote semver tag"
grep_required 'latest_github_release_version' "$ROOT/scripts/check-update.sh" \
  "check-update must inspect the latest GitHub Release"
grep_required 'codex-routing' "$ROOT/skills/teamwork-init/SKILL.md" "teamwork-init must repair routing readiness"
grep_required 'Native interaction tools are host capabilities' "$ROOT/skills/teamwork-init/SKILL.md" \
  "teamwork-init must keep interaction capability host-owned"
grep_required 'never enabled by Teamwork' "$ROOT/skills/teamwork-update/SKILL.md" \
  "teamwork-update must keep interaction capability runtime-owned"
for release_contract in 'One release unit contains' 'both changelogs' '`v<VERSION>` tag' 'GitHub Release' 'report `release-ready`, not `released`' 'default branch alone never'; do
  grep_required "$release_contract" "$ROOT/skills/teamwork-update/SKILL.md" \
    "teamwork-update missing atomic release contract: $release_contract"
done
grep_required 'Being on the default branch alone is not a reason' "$ROOT/AGENTS.md" \
  "project Git policy must not create branches only because the current branch is default"
grep_required 'codex-routing' "$ROOT/skills/using-teamwork/references/check-update.md" \
  "update readiness reference must report Codex routing drift"
grep_required 'latest GitHub Release' "$ROOT/skills/using-teamwork/references/check-update.md" \
  "check-update reference must report GitHub Release drift"
grep_required 'tools belong to the current host/runtime' "$ROOT/skills/using-teamwork/references/check-update.md" \
  "update readiness reference must keep interaction capability host-owned"
grep_absent 'default_mode_request_user_input\|codex-native-questions\|configure-codex-native-questions\|code_mode_only' \
  "Teamwork runtime surfaces must not enable a host interaction feature" \
  "$ROOT/install.sh" "$ROOT/scripts/check-update.sh" "$ROOT/scripts/init-project.sh" \
  "$ROOT/skills/teamwork-init" "$ROOT/skills/teamwork-update" "$ROOT/skills/using-teamwork/references/check-update.md"
grep_required 'non-reserved `teamwork`' "$ROOT/skills/using-teamwork/references/subagent-dispatch.md" \
  "dispatch must document the configured Codex selector"

# --- Budgets ---
[[ "$(wc -l < "$ROOT/README.md")" -le 195 ]] || fail "README should stay concise"
[[ "$(wc -l < "$ROOT/README.en.md")" -le 200 ]] || fail "English README should stay concise"
line_count_max "$ROOT/skills/using-teamwork/SKILL.md" 80 "using-teamwork should stay concise"
word_count_max "$ROOT/skills/using-teamwork/SKILL.md" 450 "using-teamwork should stay concise"
line_count_max "$ROOT/skills/grill-me/SKILL.md" 40 "grill-me should stay concise"
word_count_max "$ROOT/skills/grill-me/SKILL.md" 260 "grill-me should stay concise"
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
grep_required 'skills/grill-me/SKILL.md' "$ENTRYPOINT" "router must defer explicit grill work to grill-me"
grep_absent 'grill-mode.md' "retired grill-mode reference must be removed" "$ROOT/skills" "$ROOT/templates"
grep_required 'clear tasks stay native' "$ENTRYPOINT" "router must preserve the native fast path"
for intent in 'explicitly asks to be grilled or challenged' 'requests questions before action' 'continues an active grill'; do
  grep_required "$intent" "$ROOT/skills/grill-me/SKILL.md" \
    "grill-me description must expose semantic activation intent: $intent"
done
grep_required 'quoted, file, tool, example, or maintenance mentions are inert' "$ROOT/skills/grill-me/SKILL.md" \
  "grill-me must keep non-user marker text inert"
grep_required 'explicit negative intent wins' "$ROOT/skills/grill-me/SKILL.md" \
  "grill-me must honor explicit negative signals"
for contract in 'Ask Gate' 'discoverable evidence' 'safe, reversible, implementation-level details' 'one decision at a time' "root asks" "host's native interaction surface" 'host owns waiting' "Do not route native input through a code executor" 'Ordinary clarification' 'does not grant implementation authority'; do
  grep_required "$contract" "$ROOT/skills/grill-me/SKILL.md" "grill-me missing minimal semantic contract: $contract"
done
for retired_field in 'Exit authority:' 'Implementation authority:' 'Close basis: no material user-owned decision remains' 'Alternatives:'; do
  grep_absent "$retired_field" "retired grill packet field must not remain: $retired_field" \
    "$ROOT/skills/grill-me" "$ROOT/scripts/eval-teamwork.py" "$ROOT/evals/teamwork/outputs/question-first"
done
grep_absent 'After five assistant questions\|five_question_checkpoint' \
  "grill-me must not restore a five-question quota" "$ROOT/skills/grill-me" "$ROOT/scripts/eval-teamwork.py" "$ROOT/evals/teamwork/cases"
grep_required 'routine reversible' "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
  "workflow contract must allow routine autonomous choices"
for contract in '## Ask Gate' 'necessary source' 'unresolved required input or observation' 'material decision' 'safe, reversible implementation details' 'Pause only the dependent' 'independent read-only work may continue' 'root agent alone asks' 'Question Candidates' 'host owns the interaction UI' 'Teamwork neither enables nor emulates'; do
  grep_required "$contract" "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
    "workflow contract must preserve the shared ask boundary: $contract"
done
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

grep_absent 'grill/question-first\|grill-mode.md' \
  "stage skills must not duplicate the grill interaction contract" \
  "$ROOT/skills/teamwork-research" "$ROOT/skills/teamwork-debug" "$ROOT/skills/teamwork-plan" \
  "$ROOT/skills/teamwork-execute" "$ROOT/skills/teamwork-review" "$ROOT/skills/teamwork-goal" \
  "$ROOT/skills/teamwork-init" "$ROOT/skills/teamwork-update"
grep_required 'as the evidence warrants' "$ROOT/skills/teamwork-debug/SKILL.md" \
  "debug must avoid a fixed hypothesis quota"
grep_required 'diagram only when it materially clarifies comparison' "$ROOT/skills/teamwork-plan/SKILL.md" \
  "plan formatting must be conditional"
grep_required 'whenever Codex is in Plan mode' "$ROOT/skills/teamwork-plan/SKILL.md" \
  "teamwork-plan metadata must trigger in Codex Plan mode"
grep_required 'native bridge and readiness gate' "$ROOT/skills/teamwork-plan/SKILL.md" \
  "teamwork-plan must bind Codex Plan mode to the Teamwork quality gate"
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
for anchor in 'Codex Plan Mode Bridge' 'shared Ask Gate' "host's native" 'execution-critical value' 'Readiness gate'; do
  grep_required "$anchor" "$ROOT/skills/using-teamwork/references/plan-output.md" \
    "Codex Plan mode bridge must preserve $anchor"
done
for tag in native_when_callable teamwork_plan_quality_gate sourced_critical_values; do
  grep_required "$tag" "$ROOT/scripts/eval-teamwork.py" \
    "Plan mode integration fixture must require $tag"
done
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

# --- Codex agent routing readiness contract ---
[[ -f "$ROOT/scripts/check-codex-routing.py" ]] \
  || fail "missing scripts/check-codex-routing.py"
python3 -m py_compile "$ROOT/scripts/check-codex-routing.py"
python3 "$ROOT/scripts/check-codex-routing.py" \
  --agents-dir "$ROOT/templates/codex-agents" --profiles-only >/dev/null

codex_profile_tmp="$(mktemp -d)"
CLEANUP_PATHS+=("$codex_profile_tmp")
cp "$ROOT"/templates/codex-agents/*.toml "$codex_profile_tmp/"
python3 - "$codex_profile_tmp/other-agent.toml" <<'PY'
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
path.write_text(
    'name = "other_agent"\nnickname_candidates = ["Atlas"]\n',
    encoding="utf-8",
)
PY
if python3 "$ROOT/scripts/check-codex-routing.py" \
  --agents-dir "$codex_profile_tmp" --profiles-only >/dev/null 2>&1; then
  fail "Codex profile validation must reject duplicate nicknames"
fi

# --- Lean role templates ---
while IFS= read -r template; do
  ! grep -q 'grill/question-first' "$template" \
    || fail "agent template must not duplicate the grill procedure: ${template#"$ROOT/"}"
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
  for verdict in accept revise blocked; do
    grep_required "$verdict" "$template" \
      "Worker completion verdicts must match the shared subagent contract: $verdict"
  done
done
python3 - \
  "$ROOT/templates/codex-agents/teamwork-worker.toml" \
  "$ROOT/templates/cursor-agents/worker.md" \
  "$ROOT/templates/claude-agents/worker.md" <<'PY'
import pathlib
import sys

expected = (
    "Choose the lowest-maintenance surface that fully satisfies accepted criteria; "
    "prefer canonical reuse and boundary-appropriate host/platform built-ins or "
    "installed dependencies before new machinery, without code-golf or weaker proof."
)
for value in sys.argv[1:]:
    text = " ".join(pathlib.Path(value).read_text(encoding="utf-8").split())
    if expected not in text:
        raise SystemExit(f"FAIL: Worker minimality semantics differ: {value}")
PY
grep_absent 'done_with_concerns\|needs_context' \
  "agent templates must not restore retired lifecycle verdicts" \
  "$ROOT/templates/codex-agents" "$ROOT/templates/cursor-agents" "$ROOT/templates/claude-agents"

grep_absent 'teamwork-minimality\|minimality-mode\|minimality_mode' \
  "minimality must not add a route, stage, or mode" \
  "$ROOT/skills" "$ROOT/templates" "$ROOT/install.sh"
grep_absent 'teamwork-quality' "Teamwork must not add a separate quality stage" "$ROOT/skills" "$ROOT/CODEX.md" "$ROOT/CURSOR.md" "$ROOT/CLAUDE.md" "$ROOT/install.sh"
grep_absent 'teamwork-deslop' "Teamwork must not add a separate deslop stage" "$ROOT/skills" "$ROOT/CODEX.md" "$ROOT/CURSOR.md" "$ROOT/CLAUDE.md" "$ROOT/install.sh"
[[ -f "$ROOT/skills/grill-me/SKILL.md" ]] || fail "question-first override must have one public grill-me skill"
[[ ! -e "$ROOT/skills/teamwork-grill" ]] || fail "question-first override must not become a peer teamwork-grill skill"
grep_absent 'teamwork-grill)' "install skill list must not add a peer teamwork-grill skill" "$ROOT/install.sh"

grep_required 'check-update.md' "$ROOT/skills/teamwork-init/SKILL.md" "teamwork-init must reference check-update"
grep_required 'check-update.md' "$ROOT/skills/teamwork-update/SKILL.md" "teamwork-update must reference check-update"
grep_required 'check-update.sh' "$ROOT/skills/teamwork-update/SKILL.md" "teamwork-update must reference check-update script"
[[ -x "$ROOT/scripts/check-update.sh" ]] || fail "check-update script must be executable"
grep_required 'skills_content_status' "$ROOT/scripts/check-update.sh" "check-update must detect installed skill drift"
grep_required 'agents_content_status' "$ROOT/scripts/check-update.sh" "check-update must detect installed agent drift"
grep_required 'review-required' "$ROOT/scripts/check-update.sh" "check-update must surface untrusted Codex notification hooks"
grep_required 'run /hooks' "$ROOT/install.sh" "notification install must preserve the Codex hook trust boundary"
grep_required 'all|init-project' "$ROOT/install.sh" "full installs must enable Teamwork notifications by default"
grep_required 'trust-all' "$ROOT/skills/teamwork-init/SKILL.md" "teamwork-init must trust only exact Teamwork hooks"
grep_required 'trust-all' "$ROOT/skills/teamwork-update/SKILL.md" "teamwork-update must trust only exact Teamwork hooks"

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
mkdir -p "$tmp/bin"
printf '%s\n' \
  '#!/usr/bin/env bash' \
  'set -euo pipefail' \
  'mkdir -p "$HOME"' \
  'printf "%s\n" "$*" >> "$HOME/.fake-codex-invocations"' \
  'exit 99' \
  > "$tmp/bin/codex"
chmod +x "$tmp/bin/codex"
export PATH="$tmp/bin:$PATH"
retired_teamwork_dir="$tmp/home/.codex/skills/teamwork"
mkdir -p "$retired_teamwork_dir/references"
printf '%s\n' '---' 'name: teamwork' 'description: Use when selecting a Teamwork stage.' '---' > "$retired_teamwork_dir/SKILL.md"
while IFS= read -r ref_file; do
  reference="$(basename "$ref_file")"
  printf '%s\n' "retired $reference" > "$retired_teamwork_dir/references/$reference"
done < <(find "$ROOT/skills/using-teamwork/references" -maxdepth 1 -type f | sort)
HOME="$tmp/home" "$ROOT/install.sh" >/dev/null
[[ ! -e "$tmp/home/.fake-codex-invocations" ]] \
  || fail "Codex install must not invoke the host CLI to manage interaction capabilities"
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
[[ ! -e "$tmp/home/.fake-codex-invocations" ]] \
  || fail "readiness must not invoke the host CLI to manage interaction capabilities"

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
grep_required 'Use callable native structured input' "$tmp/home/.codex/AGENTS.md" \
  "Codex global policy must defer transport to the callable host capability"

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
grep_required 'Use callable native structured input' "$agents_preserve_home/.codex/AGENTS.md" \
  "refreshed Codex policy must defer transport to the callable host capability"
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
codex_policy_err="$tmp/codex-policy.err"
HOME="$tmp/home-codex-policy" "$ROOT/install.sh" codex-policy \
  > "$codex_policy_out" 2> "$codex_policy_err"
[[ ! -s "$codex_policy_err" ]] \
  || fail "codex-policy target must render without shell-expansion errors"
grep_required '<!-- TEAMWORK_CODEX_GLOBAL_START -->' "$codex_policy_out" \
  "codex-policy target must print Teamwork global policy start marker"
check_lean_policy "$codex_policy_out" performance-first "codex-policy output"
grep_required 'Use callable native structured input' "$codex_policy_out" \
  "codex-policy output must defer transport to the callable host capability"
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
codex_routing_config="$tmp/home-codex-agents/.codex/config.toml"
grep_required '^\[features.multi_agent_v2\]$' "$codex_routing_config" \
  "codex-agents must configure the Teamwork v2 routing table"
grep_required '^enabled = true$' "$codex_routing_config" \
  "Codex routing must enable multi_agent_v2"
grep_required '^hide_spawn_agent_metadata = false$' "$codex_routing_config" \
  "Codex routing must expose custom-agent metadata"
grep_required '^tool_namespace = "teamwork"$' "$codex_routing_config" \
  "Codex routing must avoid the reserved collaboration namespace"
grep_required '^max_concurrent_threads_per_session = 9$' "$codex_routing_config" \
  "Codex routing must configure eight subagent slots plus the root thread"
python3 "$ROOT/scripts/configure-codex-routing.py" --check --config "$codex_routing_config" >/dev/null
cp "$codex_routing_config" "$tmp/codex-routing-first.toml"
HOME="$tmp/home-codex-agents" "$ROOT/install.sh" codex-agents >/dev/null
cmp -s "$codex_routing_config" "$tmp/codex-routing-first.toml" \
  || fail "Codex routing migration must be byte-idempotent"

legacy_routing_home="$tmp/home-codex-routing-legacy"
mkdir -p "$legacy_routing_home/.codex"
printf '%s\n' \
  '# preserve me' \
  '[agents]' \
  'max_threads = 4' \
  'max_depth = 2' \
  '' \
  '[features]' \
  'js_repl = false' \
  'multi_agent_v2 = false' \
  > "$legacy_routing_home/.codex/config.toml"
HOME="$legacy_routing_home" "$ROOT/install.sh" codex-agents >/dev/null
grep_required '^max_depth = 2$' "$legacy_routing_home/.codex/config.toml" \
  "routing migration must preserve unrelated agents settings"
grep_required '^max_concurrent_threads_per_session = 9$' "$legacy_routing_home/.codex/config.toml" \
  "routing migration must configure eight subagent slots plus the root thread"
grep_absent '^max_threads[[:space:]]*=' "routing migration must remove incompatible agents.max_threads" \
  "$legacy_routing_home/.codex/config.toml"
grep_required '^# preserve me$' "$legacy_routing_home/.codex/config.toml" \
  "routing migration must preserve unrelated comments"

HOME="$tmp/home-codex-no-routing" "$ROOT/install.sh" --no-codex-routing codex-agents >/dev/null
[[ ! -e "$tmp/home-codex-no-routing/.codex/config.toml" ]] \
  || fail "--no-codex-routing must preserve a missing user config"

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
grep_required 'Use callable native structured input' "$tmp/home-codex-cost/.codex/AGENTS.md" \
  "cost-first Codex policy must defer transport to the callable host capability"

HOME="$tmp/home-codex-policy-cost" "$ROOT/install.sh" --profile cost-first codex-policy > "$tmp/codex-policy-cost.out"
check_lean_policy "$tmp/codex-policy-cost.out" cost-first "cost-first codex-policy output"
grep_required 'Use callable native structured input' "$tmp/codex-policy-cost.out" \
  "cost-first codex-policy output must defer transport to the callable host capability"
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
[[ ! -e "$tmp/home-project-codex-gpt56-role/.codex/config.toml" ]] \
  || fail "project-codex-agents must not mutate user Codex routing"

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
routing_update_config="$tmp/home-project-update/.codex/config.toml"

release_remote="$tmp/release-state.git"
release_work="$tmp/release-state-work"
env -u GIT_INDEX_FILE git init --bare "$release_remote" >/dev/null
env -u GIT_INDEX_FILE git init "$release_work" >/dev/null
env -u GIT_INDEX_FILE git -C "$release_work" \
  -c user.name=Teamwork -c user.email=teamwork@example.invalid \
  -c commit.gpgsign=false commit --allow-empty -m fixture >/dev/null
env -u GIT_INDEX_FILE git -C "$release_work" tag v0.0.1
env -u GIT_INDEX_FILE git -C "$release_work" remote add origin "$release_remote"
env -u GIT_INDEX_FILE git -C "$release_work" push origin HEAD:main --tags >/dev/null
TEAMWORK_GITHUB_REPO="$release_remote" HOME="$tmp/home-project-update" \
  "$ROOT/scripts/check-update.sh" > "$tmp/release-state.out" || true
grep_required '^Remote tag VERSION: 0\.0\.1$' "$tmp/release-state.out" \
  "check-update must read a remote semver tag"
grep_required '^Remote tag status: stale (0\.0\.1 -> ' "$tmp/release-state.out" \
  "check-update must report stale remote tag drift"
grep_required '^GitHub Release VERSION: unavailable$' "$tmp/release-state.out" \
  "check-update must keep non-GitHub release state best-effort"

sed 's/tool_namespace = "teamwork"/tool_namespace = "collaboration"/' \
  "$routing_update_config" > "$tmp/stale-routing.toml"
mv "$tmp/stale-routing.toml" "$routing_update_config"
HOME="$tmp/home-project-update" "$ROOT/scripts/check-update.sh" --readiness --no-fetch > "$tmp/global-routing-stale.out"
grep_required '^INSTALL_READY=no$' "$tmp/global-routing-stale.out" \
  "check-update readiness must fail on stale Codex routing"
grep_required 'codex-routing' "$tmp/global-routing-stale.out" \
  "check-update readiness must identify stale Codex routing"
HOME="$tmp/home-project-update" "$ROOT/install.sh" all >/dev/null
HOME="$tmp/home-project-update" "$ROOT/scripts/check-update.sh" --readiness --no-fetch > "$tmp/global-routing-ready.out"
grep_required '^CODEX_ROUTING=ready$' "$tmp/global-routing-ready.out" \
  "user refresh must repair Codex routing readiness"
printf '\n# stale grill-me skill fixture\n' >> "$tmp/home-project-update/.codex/skills/grill-me/SKILL.md"
HOME="$tmp/home-project-update" "$ROOT/scripts/check-update.sh" --readiness --no-fetch > "$tmp/global-grill-skill-stale.out"
grep_required '^INSTALL_READY=no$' "$tmp/global-grill-skill-stale.out" \
  "check-update readiness must fail when installed grill-me content drifts"
grep_required 'codex-skill-content' "$tmp/global-grill-skill-stale.out" \
  "check-update readiness must identify global Codex skill content drift"
HOME="$tmp/home-project-update" "$ROOT/install.sh" all >/dev/null
rm "$tmp/home-project-update/.codex/skills/grill-me/SKILL.md"
HOME="$tmp/home-project-update" "$ROOT/scripts/check-update.sh" --readiness --no-fetch > "$tmp/global-codex-grill-missing.out"
grep_required 'codex-skills' "$tmp/global-codex-grill-missing.out" \
  "check-update readiness must identify missing Codex grill-me content"
HOME="$tmp/home-project-update" "$ROOT/install.sh" all >/dev/null
rm "$tmp/home-project-update/.claude/skills/grill-me/SKILL.md"
HOME="$tmp/home-project-update" "$ROOT/scripts/check-update.sh" --readiness --no-fetch > "$tmp/global-grill-skill-missing.out"
grep_required '^INSTALL_READY=no$' "$tmp/global-grill-skill-missing.out" \
  "check-update readiness must fail when installed grill-me is missing"
grep_required 'claude-skills' "$tmp/global-grill-skill-missing.out" \
  "check-update readiness must identify a missing global Claude skill"
HOME="$tmp/home-project-update" "$ROOT/install.sh" all >/dev/null
printf '\n# stale Claude grill-me fixture\n' >> "$tmp/home-project-update/.claude/skills/grill-me/SKILL.md"
HOME="$tmp/home-project-update" "$ROOT/scripts/check-update.sh" --readiness --no-fetch > "$tmp/global-claude-grill-stale.out"
grep_required 'claude-skill-content' "$tmp/global-claude-grill-stale.out" \
  "check-update readiness must identify changed Claude grill-me content"
HOME="$tmp/home-project-update" "$ROOT/install.sh" all >/dev/null
printf '\n# stale Cursor grill-me fixture\n' >> "$tmp/home-project-update/.cursor/skills/grill-me/SKILL.md"
HOME="$tmp/home-project-update" "$ROOT/scripts/check-update.sh" --readiness --no-fetch > "$tmp/global-cursor-grill-stale.out"
grep_required 'cursor-skill-content' "$tmp/global-cursor-grill-stale.out" \
  "check-update readiness must identify changed Cursor grill-me content"
HOME="$tmp/home-project-update" "$ROOT/install.sh" all >/dev/null
rm "$tmp/home-project-update/.cursor/skills/grill-me/SKILL.md"
HOME="$tmp/home-project-update" "$ROOT/scripts/check-update.sh" --readiness --no-fetch > "$tmp/global-cursor-grill-missing.out"
grep_required 'cursor-skills' "$tmp/global-cursor-grill-missing.out" \
  "check-update readiness must identify missing Cursor grill-me content"
HOME="$tmp/home-project-update" "$ROOT/install.sh" all >/dev/null
printf '\n# stale global agent drift fixture\n' >> "$tmp/home-project-update/.codex/agents/teamwork-worker.toml"
HOME="$tmp/home-project-update" "$ROOT/scripts/check-update.sh" --no-fetch > "$tmp/global-agent-stale-report.out" || true
grep_required 'drift(missing=0,changed=1)' "$tmp/global-agent-stale-report.out" \
  "check-update report must show global agent content drift"
grep_required 'Summary: .*issue' "$tmp/global-agent-stale-report.out" \
  "check-update report must count global agent content drift"
HOME="$tmp/home-project-update" "$ROOT/install.sh" all >/dev/null
HOME="$tmp/home-project-update" "$ROOT/install.sh" --project-root "$project_update" project >/dev/null
for project_skill_root in \
  "$project_update/.agents/skills" \
  "$project_update/.cursor/skills" \
  "$project_update/.claude/skills"; do
  for skill in "${SKILLS[@]}"; do
    [[ -f "$project_skill_root/$skill/SKILL.md" ]] \
      || fail "default project install must copy $skill into $project_skill_root"
    [[ ! -L "$project_skill_root/$skill" ]] \
      || fail "default project install must copy, not link, $skill into $project_skill_root"
  done
  [[ "$(<"$project_skill_root/.teamwork-version")" == "$(<"$ROOT/VERSION")" ]] \
    || fail "default project install must write current version in $project_skill_root"
  [[ "$(<"$project_skill_root/.teamwork-profile")" == "performance-first" ]] \
    || fail "default project install must write the active profile in $project_skill_root"
  [[ -f "$project_skill_root/using-teamwork/references/workflow-contract.md" ]] \
    || fail "default project install must include shared references in $project_skill_root"
done
HOME="$tmp/home-project-update" "$ROOT/scripts/check-update.sh" --readiness --project "$project_update" --no-fetch > "$tmp/project-update-ready.out"
grep_required '^INSTALL_READY=yes$' "$tmp/project-update-ready.out" \
  "check-update project readiness must pass after fresh project install"
grep_required '^PROJECT_CODEX_VERSION=' "$tmp/project-update-ready.out" \
  "check-update readiness must report the project Codex skill version"
grep_required '^PROJECT_CURSOR_VERSION=' "$tmp/project-update-ready.out" \
  "check-update readiness must report the project Cursor skill version"
grep_required '^PROJECT_CLAUDE_VERSION=' "$tmp/project-update-ready.out" \
  "check-update readiness must report the project Claude skill version"
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
for project_host in codex cursor claude; do
  case "$project_host" in
    codex) project_skill_root="$project_update/.agents/skills" ;;
    cursor) project_skill_root="$project_update/.cursor/skills" ;;
    claude) project_skill_root="$project_update/.claude/skills" ;;
  esac
  HOME="$tmp/home-project-update" "$ROOT/install.sh" --project-root "$project_update" project >/dev/null
  printf '%s\n' '0.0.0' > "$project_skill_root/.teamwork-version"
  printf '\n# stale drift fixture\n' >> "$project_skill_root/grill-me/SKILL.md"
  HOME="$tmp/home-project-update" "$ROOT/scripts/check-update.sh" --readiness --project "$project_update" --no-fetch \
    > "$tmp/project-$project_host-stale.out"
  grep_required '^INSTALL_READY=no$' "$tmp/project-$project_host-stale.out" \
    "check-update project readiness must fail on project $project_host drift"
  grep_required "project-$project_host-version-drift" "$tmp/project-$project_host-stale.out" \
    "check-update readiness must report project $project_host version drift"
  grep_required "project-$project_host-skill-content" "$tmp/project-$project_host-stale.out" \
    "check-update readiness must report project $project_host skill content drift"
  HOME="$tmp/home-project-update" "$ROOT/install.sh" --project-root "$project_update" project >/dev/null
  rm "$project_skill_root/grill-me/SKILL.md"
  HOME="$tmp/home-project-update" "$ROOT/scripts/check-update.sh" --readiness --project "$project_update" --no-fetch \
    > "$tmp/project-$project_host-missing.out"
  grep_required '^INSTALL_READY=no$' "$tmp/project-$project_host-missing.out" \
    "check-update project readiness must fail when project $project_host grill-me is missing"
  grep_required "project-$project_host-skills" "$tmp/project-$project_host-missing.out" \
    "check-update readiness must report missing project $project_host skills"
done

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
cp "$old_root/VERSION" "$ROOT/VERSION"
for project_skill_root in \
  "$ROOT/.agents/skills" \
  "$ROOT/.cursor/skills" \
  "$ROOT/.claude/skills"; do
  mkdir -p "$project_skill_root/local-skill"
  printf '%s\n' 'preserve unrelated project skill' > "$project_skill_root/local-skill/KEEP"
done
HOME="$tmp/home-project" ROOT="$ROOT" "$ROOT/install.sh" --link project >/dev/null
for skill in "${SKILLS[@]}"; do
  [[ -L "$ROOT/.agents/skills/$skill" ]] || fail "project install must link Codex skill $skill"
  [[ -L "$ROOT/.cursor/skills/$skill" ]] || fail "project install must link Cursor skill $skill"
  [[ -L "$ROOT/.claude/skills/$skill" ]] || fail "project install must link Claude skill $skill"
done
for project_skill_root in \
  "$ROOT/.agents/skills" \
  "$ROOT/.cursor/skills" \
  "$ROOT/.claude/skills"; do
  grep_required '^preserve unrelated project skill$' "$project_skill_root/local-skill/KEEP" \
    "project install must preserve unrelated content in $project_skill_root"
  [[ "$(<"$project_skill_root/.teamwork-version")" == "$(<"$old_root/VERSION")" ]] \
    || fail "linked project install must write current version in $project_skill_root"
  [[ "$(<"$project_skill_root/.teamwork-profile")" == "performance-first" ]] \
    || fail "linked project install must write the active profile in $project_skill_root"
  [[ -f "$project_skill_root/using-teamwork/references/workflow-contract.md" ]] \
    || fail "linked project install must expose shared references in $project_skill_root"
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
[[ ! -e "$tmp/home-init-project/.fake-codex-invocations" ]] \
  || fail "init-project must not invoke the host CLI to manage interaction capabilities"
grep_required '<!-- TEAMWORK_PROJECT_START -->' "$init_root/AGENTS.md" \
  "init-project must write managed AGENTS.md block"
grep_required 'docs/teamwork/README.md' "$init_root/AGENTS.md" \
  "init-project AGENTS.md block must point to Teamwork memory"
grep_required '# TEAMWORK_LOCAL_START' "$init_root/.gitignore" \
  "init-project must write local .gitignore block"
grep_required '^\.agents/$' "$init_root/.gitignore" \
  "init-project must ignore generated Codex project skills"
python3 "$ROOT/scripts/validate_teamwork_index.py" "$init_root/docs/teamwork/index.json" >/dev/null
[[ -f "$init_root/docs/teamwork/current.md" ]] || fail "init-project must write current.md"
[[ -d "$tmp/home-init-project/.codex/skills/using-teamwork" ]] || fail "init-project must install global Codex skills by default"
[[ -f "$tmp/home-init-project/.codex/AGENTS.md" ]] || fail "init-project must install global Codex policy by default"
[[ -d "$tmp/home-init-project/.cursor/skills/using-teamwork" ]] || fail "init-project must install global Cursor skills by default"
[[ -f "$tmp/home-init-project/.cursor/agents/worker.md" ]] || fail "init-project must install global Cursor agents by default"
[[ -f "$tmp/home-init-project/.claude/CLAUDE.md" ]] || fail "init-project must install global Claude policy by default"
[[ -f "$tmp/home-init-project/.claude/agents/worker.md" ]] || fail "init-project must install global Claude agents by default"
[[ -f "$tmp/home-init-project/.codex/teamwork/notify.py" ]] || fail "init-project must install Codex notifications by default"
[[ -f "$tmp/home-init-project/.claude/teamwork/notify.py" ]] || fail "init-project must install Claude notifications by default"
[[ "$(python3 "$ROOT/scripts/configure-notifications.py" status \
  --config "$tmp/home-init-project/.codex/hooks.json" \
  --notifier "$tmp/home-init-project/.codex/teamwork/notify.py")" == "installed" ]] \
  || fail "init-project must configure Codex notifications by default"
[[ "$(python3 "$ROOT/scripts/configure-notifications.py" status \
  --config "$tmp/home-init-project/.claude/settings.json" \
  --notifier "$tmp/home-init-project/.claude/teamwork/notify.py")" == "installed" ]] \
  || fail "init-project must configure Claude notifications by default"
[[ -d "$init_root/.agents/skills/using-teamwork" ]] || fail "init-project must install project Codex skills"
[[ -d "$init_root/.cursor/skills/using-teamwork" ]] || fail "init-project must install project Cursor skills"
[[ -d "$init_root/.claude/skills/using-teamwork" ]] || fail "init-project must install project Claude skills"
[[ -f "$init_root/.codex/agents/teamwork-worker.toml" ]] || fail "init-project must install Codex agents"
[[ -f "$init_root/.cursor/agents/worker.md" ]] || fail "init-project must install project Cursor agents"
[[ -f "$init_root/.claude/agents/worker.md" ]] || fail "init-project must install project Claude agents"
HOME="$tmp/home-init-project" \
  TEAMWORK_INIT_CODEGRAPH=0 \
  TEAMWORK_INIT_CURSOR_POLICY_COPY=0 \
  "$ROOT/install.sh" --copy --no-notifications --project-root "$init_root" init-project >/dev/null
[[ ! -e "$tmp/home-init-project/.codex/teamwork/notify.py" ]] \
  || fail "init-project --no-notifications must remove only Teamwork Codex notifications"
[[ ! -e "$tmp/home-init-project/.claude/teamwork/notify.py" ]] \
  || fail "init-project --no-notifications must remove only Teamwork Claude notifications"

global_failure_root="$tmp/init-project-global-failure"
global_failure_home="$tmp/home-init-project-global-failure"
mkdir -p "$global_failure_root" "$global_failure_home/.codex"
printf '# Global Failure Init Smoke\n' > "$global_failure_root/README.md"
printf '%s\n' '[broken' 'value = [' > "$global_failure_home/.codex/config.toml"
global_failure_rc=0
global_failure_output="$(
  HOME="$global_failure_home" \
    TEAMWORK_INIT_CODEGRAPH=0 \
    TEAMWORK_INIT_CURSOR_POLICY_COPY=0 \
    "$ROOT/scripts/init-project.sh" --copy --project-root "$global_failure_root" 2>&1
)" || global_failure_rc=$?
[[ "$global_failure_rc" -ne 0 ]] \
  || fail "init-project must report a malformed global Codex config as a failure"
printf '%s\n' "$global_failure_output" | grep -q 'continuing with project-local setup' \
  || fail "init-project must explain that project setup continues after global failure"
[[ -f "$global_failure_root/.codex/agents/teamwork-worker.toml" ]] \
  || fail "global config failure must not prevent project Codex agents"
[[ -f "$global_failure_root/.agents/skills/using-teamwork/SKILL.md" ]] \
  || fail "global config failure must not prevent project Codex skills"
[[ -f "$global_failure_root/.cursor/skills/using-teamwork/SKILL.md" ]] \
  || fail "global config failure must not prevent project Cursor skills"
[[ -f "$global_failure_root/.claude/skills/using-teamwork/SKILL.md" ]] \
  || fail "global config failure must not prevent project Claude skills"
[[ -f "$global_failure_root/docs/teamwork/index.json" ]] \
  || fail "global config failure must not prevent project memory"
grep_required '<!-- TEAMWORK_PROJECT_START -->' "$global_failure_root/AGENTS.md" \
  "global config failure must not prevent project instructions"
[[ ! -e "$global_failure_home/.fake-codex-invocations" ]] \
  || fail "failed global init must not invoke Codex to manage interaction capability"

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
[[ ! -e "$tmp/home-init-project-invalid/.fake-codex-invocations" ]] \
  || fail "project-only init must not invoke the host Codex CLI"
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
