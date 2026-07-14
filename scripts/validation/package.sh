#!/usr/bin/env bash

# --- Package layout ---
for validation_module in common package contracts integration; do
  module_path="scripts/validation/$validation_module.sh"
  [[ -f "$ROOT/$module_path" ]] || fail "missing $module_path"
  git_known_package_file "$module_path" \
    || fail "$module_path is not known to git; use git add -N before release validation"
done

for install_module in common policy profiles targets; do
  module_path="scripts/install/$install_module.sh"
  [[ -f "$ROOT/$module_path" ]] || fail "missing $module_path"
  git_known_package_file "$module_path" \
    || fail "$module_path is not known to git; use git add -N before release validation"
done

[[ -f "$ROOT/docs/architecture.md" ]] || fail "missing docs/architecture.md"
git_known_package_file "docs/architecture.md" \
  || fail "docs/architecture.md is not known to git; use git add -N before release validation"
grep_required '## Canonical Tree' "$ROOT/docs/architecture.md" \
  "architecture contract must define the canonical tree"
grep_required '## Dependency Direction' "$ROOT/docs/architecture.md" \
  "architecture contract must define dependency direction"
grep_required '## Change Owners' "$ROOT/docs/architecture.md" \
  "architecture contract must define change ownership"

while IFS= read -r tooling_file; do
  rel="${tooling_file#"$ROOT"/}"
  git_known_package_file "$rel" \
    || fail "$rel is not known to git; use git add -N before release validation"
done < <(
  find "$ROOT/scripts/teamwork_tooling" "$ROOT/scripts/tests" -type f -name '*.py' | sort
)

if ! PYTHONDONTWRITEBYTECODE=1 python3 "$ROOT/scripts/teamwork_tooling/privacy_scan.py" "$ROOT"; then
  fail "tracked privacy scan found blocked values"
fi
if ! PYTHONDONTWRITEBYTECODE=1 python3 "$ROOT/scripts/teamwork_tooling/instruction_footprint.py"; then
  fail "always-loaded policy and union runtime instruction footprint exceed compactness limits"
fi

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
[[ -f "$ROOT/CURSOR.md" ]] || fail "missing CURSOR.md"
[[ -f "$ROOT/CLAUDE.md" ]] || fail "missing CLAUDE.md"
[[ -f "$ROOT/CHANGELOG.md" ]] || fail "missing CHANGELOG.md"
[[ -f "$ROOT/CHANGELOG.en.md" ]] || fail "missing CHANGELOG.en.md"
git_known_package_file "CHANGELOG.md" || fail "CHANGELOG.md is not known to git; use git add -N before release validation"
git_known_package_file "CHANGELOG.en.md" || fail "CHANGELOG.en.md is not known to git; use git add -N before release validation"

[[ -f "$ROOT/VERSION" ]] || fail "missing VERSION"
git_known_package_file "VERSION" || fail "VERSION is not known to git; use git add -N before release validation"
grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+$' "$ROOT/VERSION" || fail "VERSION must be plain semver"

if git -C "$ROOT" ls-files 'docs/teamwork/discussion/*' 'docs/teamwork/plans/*' 'docs/teamwork/research/*' 'docs/teamwork/reports/*' 'docs/teamwork/workflows/*' | grep -q .; then
  fail "local workflow artifacts under docs/teamwork/{discussion,plans,research,reports,workflows}/ must not be tracked"
fi
grep_required '^docs/teamwork/discussion/$' "$ROOT/.gitignore" ".gitignore must ignore local Teamwork discussion artifacts"
git -C "$ROOT" check-ignore -q docs/teamwork/discussion/validation-probe.md \
  || fail ".gitignore must match untracked Teamwork discussion artifacts"
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

for template in teamwork-index-template.json teamwork-index-readme-template.md teamwork-current-template.md teamwork-discussion-template.md; do
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
    teamwork-discussion-template.md \
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
[[ -x "$ROOT/scripts/run-installed-teamwork-live-eval.py" ]] \
  || fail "installed live canary runner must be executable"
git_known_package_file "scripts/run-installed-teamwork-live-eval.py" \
  || fail "scripts/run-installed-teamwork-live-eval.py is not known to git; use git add -N before release validation"
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
python3 -m py_compile "$ROOT/scripts/grill_contract.py" "$ROOT/scripts/run-teamwork-live-eval.py" \
  "$ROOT/scripts/run-installed-teamwork-live-eval.py" "$ROOT/scripts/test_live_eval_runner.py" \
  "$ROOT/scripts/test_eval_teamwork_mutations.py" "$ROOT/scripts/codex_routing_config.py" \
  "$ROOT/scripts/configure-codex-routing.py" "$ROOT/scripts/test_codex_routing_config.py" \
  "$ROOT/scripts/codex_app_server_user_input.py" "$ROOT/scripts/test_codex_app_server_user_input.py"
env -u GIT_INDEX_FILE PYTHONDONTWRITEBYTECODE=1 python3 "$ROOT/scripts/test_live_eval_runner.py" >/dev/null
env -u GIT_INDEX_FILE PYTHONDONTWRITEBYTECODE=1 python3 "$ROOT/scripts/test_eval_teamwork_mutations.py" >/dev/null
env -u GIT_INDEX_FILE PYTHONDONTWRITEBYTECODE=1 python3 "$ROOT/scripts/test_codex_routing_config.py" >/dev/null
env -u GIT_INDEX_FILE PYTHONDONTWRITEBYTECODE=1 python3 "$ROOT/scripts/test_codex_app_server_user_input.py" >/dev/null
(
  cd "$ROOT"
  env -u GIT_INDEX_FILE PYTHONPATH="$ROOT/scripts" PYTHONDONTWRITEBYTECODE=1 \
    python3 -m unittest discover -s scripts/tests -p 'test_*.py' >/dev/null
)
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
env -u GIT_INDEX_FILE python3 "$ROOT/scripts/run-teamwork-live-eval.py" \
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
env -u GIT_INDEX_FILE python3 "$ROOT/scripts/run-installed-teamwork-live-eval.py" run \
  --model gpt-5.6-sol \
  --effort max \
  --profile performance-first \
  --workdir "$ROOT" \
  --cases \
    "$ROOT/evals/teamwork/live-cases/lightweight-pilot.json" \
    "$ROOT/evals/teamwork/live-cases/grill-multiturn-pilot.json" \
  --repeats 1 \
  --timeout-seconds 60 \
  --max-trajectories 2 \
  --review-dir "$live_eval_tmp/installed" \
  --dry-run >/dev/null
python3 - "$live_eval_tmp/installed/install-manifest.json" <<'PY'
import json
import pathlib
import sys

manifest = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
if manifest.get("record_type") != "teamwork_installed_canary_manifest":
    raise SystemExit("FAIL: installed canary dry-run manifest has the wrong record type")
if manifest.get("dry_run") is not True or len(manifest.get("trajectories", [])) != 2:
    raise SystemExit("FAIL: installed canary dry-run manifest has the wrong trajectory contract")
if manifest.get("activation_evidence", {}).get("claim") != "AVAILABILITY_ONLY":
    raise SystemExit("FAIL: installed canary dry-run exceeded availability-only evidence")
PY
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
python3 - \
  "$ROOT/skills/using-teamwork/references/teamwork-index-template.json" \
  "$index_pointer_tmp" <<'PY'
import copy
import json
import pathlib
import sys

template_path = pathlib.Path(sys.argv[1])
output_dir = pathlib.Path(sys.argv[2])
template = json.loads(template_path.read_text(encoding="utf-8"))

old_index = copy.deepcopy(template)
old_index["active"].pop("discussion")
(output_dir / "old-v1.json").write_text(json.dumps(old_index) + "\n", encoding="utf-8")

discussion_path = "docs/teamwork/discussion/active.md"
discussion_entry = {
    "topic": "active-discussion",
    "kind": "discussion",
    "title": "Active discussion",
    "status": "accepted",
    "currentness": "current",
    "authority": "supporting",
    "path": discussion_path,
    "updated": "2026-06-01",
    "summary": "Accepted supporting discussion context.",
}

valid = copy.deepcopy(template)
valid["active"]["discussion"] = discussion_path
valid["entries"].append(discussion_entry)
(output_dir / "valid-discussion.json").write_text(json.dumps(valid) + "\n", encoding="utf-8")

variants = {
    "wrong-kind": ("kind", "report"),
    "wrong-path": ("path", "docs/teamwork/reports/active.md"),
    "wrong-status": ("status", "candidate"),
    "wrong-authority": ("authority", "canonical"),
}
for name, (field, value) in variants.items():
    invalid = copy.deepcopy(valid)
    invalid["entries"][-1][field] = value
    if field == "path":
        invalid["active"]["discussion"] = value
    (output_dir / f"{name}.json").write_text(json.dumps(invalid) + "\n", encoding="utf-8")

missing_entry = copy.deepcopy(valid)
missing_entry["entries"].pop()
(output_dir / "missing-entry.json").write_text(json.dumps(missing_entry) + "\n", encoding="utf-8")

for project_name, create_artifact in (("valid-project", True), ("missing-artifact", False)):
    project_root = output_dir / project_name
    index_path = project_root / "docs/teamwork/index.json"
    index_path.parent.mkdir(parents=True)
    index_path.write_text(json.dumps(valid) + "\n", encoding="utf-8")
    if create_artifact:
        artifact = project_root / discussion_path
        artifact.parent.mkdir(parents=True)
        artifact.write_text("# Active discussion\n", encoding="utf-8")
PY
python3 "$ROOT/scripts/validate_teamwork_index.py" "$index_pointer_tmp/old-v1.json" >/dev/null
python3 "$ROOT/scripts/validate_teamwork_index.py" "$index_pointer_tmp/valid-discussion.json" >/dev/null
python3 "$ROOT/scripts/validate_teamwork_index.py" \
  "$index_pointer_tmp/valid-project/docs/teamwork/index.json" >/dev/null
for invalid_discussion_index in wrong-kind wrong-path wrong-status wrong-authority missing-entry; do
  if python3 "$ROOT/scripts/validate_teamwork_index.py" \
    "$index_pointer_tmp/$invalid_discussion_index.json" >/dev/null 2>&1; then
    fail "Teamwork index validator accepted invalid active discussion invariant: $invalid_discussion_index"
  fi
done
if python3 "$ROOT/scripts/validate_teamwork_index.py" \
  "$index_pointer_tmp/missing-artifact/docs/teamwork/index.json" >/dev/null 2>&1; then
  fail "Teamwork index validator accepted a missing active discussion artifact"
fi
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
