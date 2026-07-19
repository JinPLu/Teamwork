#!/usr/bin/env bash

# --- Package layout ---
for validation_module in common package contracts integration; do
  module_path="scripts/validation/$validation_module.sh"
  [[ -f "$ROOT/$module_path" ]] || fail "missing $module_path"
  git_known_package_file "$module_path" \
    || fail "$module_path is absent from the active validation index"
done

for install_module in common policy profiles targets; do
  module_path="scripts/install/$install_module.sh"
  [[ -f "$ROOT/$module_path" ]] || fail "missing $module_path"
  git_known_package_file "$module_path" \
    || fail "$module_path is absent from the active validation index"
done

[[ -f "$ROOT/docs/architecture.md" ]] || fail "missing docs/architecture.md"
git_known_package_file "docs/architecture.md" \
  || fail "docs/architecture.md is absent from the active validation index"
grep_required_ci '## Canonical tree' "$ROOT/docs/architecture.md" \
  "architecture contract must define the canonical tree"
grep_required_ci '## Dependency direction' "$ROOT/docs/architecture.md" \
  "architecture contract must define dependency direction"
grep_required_ci '## Change owners' "$ROOT/docs/architecture.md" \
  "architecture contract must define change ownership"

while IFS= read -r tooling_file; do
  rel="${tooling_file#"$ROOT"/}"
  git_known_package_file "$rel" \
    || fail "$rel is absent from the active validation index"
done < <(
  find "$ROOT/scripts/teamwork_tooling" "$ROOT/scripts/tests" -type f -name '*.py' | sort
)

if ! PYTHONDONTWRITEBYTECODE=1 python3 "$ROOT/scripts/teamwork_tooling/privacy_scan.py" "$ROOT"; then
  fail "tracked privacy scan found blocked values"
fi
if ! PYTHONDONTWRITEBYTECODE=1 python3 "$ROOT/scripts/teamwork_tooling/instruction_footprint.py"; then
  fail "always-loaded policy and union runtime instruction footprint exceed compactness limits"
fi

actual_skill_dirs="$(find "$ROOT/skills" -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | sort)"
[[ "$(printf '%s\n' "${SKILLS[@]}")" == "$actual_skill_dirs" ]] \
  || fail "every top-level skills/ directory must contain one SKILL.md"
[[ "${#SKILLS[@]}" -eq "$CANONICAL_SKILL_COUNT" ]] \
  || fail "canonical skills/ inventory must discover exactly $CANONICAL_SKILL_COUNT skills"

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
git_known_package_file "CHANGELOG.md" || fail "CHANGELOG.md is absent from the active validation index"
git_known_package_file "CHANGELOG.en.md" || fail "CHANGELOG.en.md is absent from the active validation index"

[[ -f "$ROOT/VERSION" ]] || fail "missing VERSION"
git_known_package_file "VERSION" || fail "VERSION is absent from the active validation index"
grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+$' "$ROOT/VERSION" || fail "VERSION must be plain semver"

if git -C "$ROOT" ls-files 'docs/teamwork/design/*' 'docs/teamwork/discussion/*' 'docs/teamwork/plans/*' 'docs/teamwork/research/*' 'docs/teamwork/reports/*' 'docs/teamwork/workflows/*' | grep -q .; then
  fail "local workflow artifacts under docs/teamwork/{design,discussion,plans,research,reports,workflows}/ must not be tracked"
fi
grep_required '^docs/teamwork/design/$' "$ROOT/.gitignore" ".gitignore must ignore local Teamwork design artifacts"
git -C "$ROOT" check-ignore -q docs/teamwork/design/validation-probe.md \
  || fail ".gitignore must match untracked Teamwork design artifacts"
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
    || fail "skills/$skill/SKILL.md is absent from the active validation index"
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

# --- Skill topology and package runtime ---
expected_reference_inventory="$(printf '%s\n' \
  'skills/teamwork-debug/references/runtime-diagnosis.md' \
  'skills/teamwork-research/references/deep-research.md' \
  'skills/teamwork-review/references/strict-review.md' | sort)"
actual_reference_inventory="$(find "$ROOT/skills" -type f -path '*/references/*' \
  | sed "s#^$ROOT/##" | sort)"
[[ "$actual_reference_inventory" == "$expected_reference_inventory" ]] \
  || fail "skills must contain exactly the three public reference files"
if find "$ROOT/skills" -mindepth 2 -type d -name scripts \
  -exec sh -c 'find "$1" -type f -print -quit' _ {} \; | grep -q .; then
  fail "skills must not contain skill-local scripts"
fi
if grep -REq 'skills/[a-z0-9-]+/SKILL\.md' "$ROOT/skills"; then
  fail "a SKILL.md must not load another Teamwork skill"
fi

plugin_runtime_locator="scripts/plugin-runtime-root.py"
[[ -f "$ROOT/$plugin_runtime_locator" ]] \
  || fail "missing $plugin_runtime_locator"
git_known_package_file "$plugin_runtime_locator" \
  || fail "$plugin_runtime_locator is absent from the active validation index"
[[ -x "$ROOT/$plugin_runtime_locator" ]] \
  || fail "$plugin_runtime_locator must be executable"
python3 - "$ROOT/$plugin_runtime_locator" <<'PY'
import pathlib
import py_compile
import sys
import tempfile

with tempfile.TemporaryDirectory() as directory:
    for source in sys.argv[1:]:
        py_compile.compile(
            source,
            cfile=str(pathlib.Path(directory) / (pathlib.Path(source).stem + ".pyc")),
            doraise=True,
        )
PY

# --- Eval harness inventory ---
[[ -f "$ROOT/evals/teamwork/README.md" ]] || fail "missing evals/teamwork/README.md"
git_known_package_file "evals/teamwork/README.md" \
  || fail "evals/teamwork/README.md is absent from the active validation index"
for eval_dir in cases live-cases rubrics ledgers; do
  [[ -d "$ROOT/evals/teamwork/$eval_dir" ]] || fail "missing evals/teamwork/$eval_dir/"
done
while IFS= read -r eval_file; do
  rel="${eval_file#"$ROOT"/}"
  git_known_package_file "$rel" \
    || fail "$rel is absent from the active validation index"
done < <(find "$ROOT/evals/teamwork/cases" "$ROOT/evals/teamwork/live-cases" "$ROOT/evals/teamwork/rubrics" "$ROOT/evals/teamwork/ledgers" -type f | sort)
[[ -f "$ROOT/scripts/eval-teamwork.py" ]] || fail "missing scripts/eval-teamwork.py"
git_known_package_file "scripts/eval-teamwork.py" \
  || fail "scripts/eval-teamwork.py is absent from the active validation index"
python3 "$ROOT/scripts/eval-teamwork.py" --split dev >/dev/null
python3 "$ROOT/scripts/eval-teamwork.py" --split release >/dev/null
[[ -x "$ROOT/scripts/run-teamwork-live-eval.py" ]] || fail "live eval runner must be executable"
git_known_package_file "scripts/run-teamwork-live-eval.py" \
  || fail "scripts/run-teamwork-live-eval.py is absent from the active validation index"
[[ -x "$ROOT/scripts/run-installed-teamwork-live-eval.py" ]] \
  || fail "installed live canary runner must be executable"
git_known_package_file "scripts/run-installed-teamwork-live-eval.py" \
  || fail "scripts/run-installed-teamwork-live-eval.py is absent from the active validation index"
[[ -f "$ROOT/scripts/test_live_eval_runner.py" ]] || fail "missing live eval runner tests"
git_known_package_file "scripts/test_live_eval_runner.py" \
  || fail "scripts/test_live_eval_runner.py is absent from the active validation index"
[[ -f "$ROOT/scripts/test_eval_teamwork_mutations.py" ]] || fail "missing grill contract mutation tests"
git_known_package_file "scripts/test_eval_teamwork_mutations.py" \
  || fail "scripts/test_eval_teamwork_mutations.py is absent from the active validation index"
[[ -f "$ROOT/scripts/grill_contract.py" ]] || fail "missing shared grill contract checks"
git_known_package_file "scripts/grill_contract.py" \
  || fail "scripts/grill_contract.py is absent from the active validation index"
[[ -f "$ROOT/scripts/codex_routing_config.py" ]] || fail "missing Codex routing config module"
[[ -f "$ROOT/scripts/configure-codex-routing.py" ]] || fail "missing Codex routing config CLI"
[[ -f "$ROOT/scripts/test_codex_routing_config.py" ]] || fail "missing Codex routing config tests"
[[ -x "$ROOT/scripts/codex_app_server_user_input.py" ]] || fail "missing Codex app-server user-input harness"
[[ -f "$ROOT/scripts/test_codex_app_server_user_input.py" ]] || fail "missing Codex app-server user-input tests"
compile_python_files "$ROOT/scripts/grill_contract.py" "$ROOT/scripts/run-teamwork-live-eval.py" \
  "$ROOT/scripts/run-installed-teamwork-live-eval.py" "$ROOT/scripts/test_live_eval_runner.py" \
  "$ROOT/scripts/test_eval_teamwork_mutations.py" "$ROOT/scripts/codex_routing_config.py" \
  "$ROOT/scripts/configure-codex-routing.py" "$ROOT/scripts/test_codex_routing_config.py" \
  "$ROOT/scripts/codex_app_server_user_input.py" "$ROOT/scripts/test_codex_app_server_user_input.py"
if is_full_validation; then
  PYTHONDONTWRITEBYTECODE=1 python3 "$ROOT/scripts/test_live_eval_runner.py" >/dev/null
else
  validation_note "live eval runner unit tests are release-only"
fi
if is_full_validation; then
  PYTHONDONTWRITEBYTECODE=1 python3 "$ROOT/scripts/test_eval_teamwork_mutations.py" >/dev/null
else
  validation_note "eval mutation tests are release-only"
fi
PYTHONDONTWRITEBYTECODE=1 python3 "$ROOT/scripts/test_codex_routing_config.py" >/dev/null
if is_full_validation; then
  PYTHONDONTWRITEBYTECODE=1 python3 "$ROOT/scripts/test_codex_app_server_user_input.py" >/dev/null
else
  validation_note "Codex app-server user-input tests are release-only"
fi
run_python_unit_tests
[[ ! -e "$ROOT/scripts/teamwork_contract.py" && ! -e "$ROOT/scripts/test_teamwork_contract.py" ]] \
  || fail "retired Task Contract validator must remain absent"
[[ ! -e "$ROOT/scripts/teamwork_findings.py" && ! -e "$ROOT/scripts/test_teamwork_findings.py" ]] \
  || fail "retired Finding-state validator must remain absent"
[[ "$(find "$ROOT/evals/teamwork/cases" -maxdepth 1 -type f -name '*.dev.v4.json' | wc -l | tr -d ' ')" -ge 30 ]] \
  || fail "v4 dev eval must retain broad bilingual behavior coverage"
[[ "$(find "$ROOT/evals/teamwork/cases" -maxdepth 1 -type f -name '*.release.v4.json' | wc -l | tr -d ' ')" -ge 3 ]] \
  || fail "v4 release eval must cover Research, Design, and Grill boundaries"
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
if is_full_validation; then
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
  python3 "$ROOT/scripts/run-installed-teamwork-live-eval.py" run \
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
else
  validation_note "live eval dry-runs are release-only"
fi
[[ -f "$ROOT/scripts/optimize-teamwork.py" ]] || fail "missing scripts/optimize-teamwork.py"
git_known_package_file "scripts/optimize-teamwork.py" \
  || fail "scripts/optimize-teamwork.py is absent from the active validation index"
python3 "$ROOT/scripts/optimize-teamwork.py" --help >/dev/null
if is_full_validation; then
  opt_tmp="$(mktemp -d)"
  CLEANUP_PATHS+=("$opt_tmp")
  printf '%s\n' \
    '{"id":"case-failed","status":"failed","score":0,"input":"Fix typo","expected":"direct edit","output":"planned too much","fail_reason":"over-routing"}' \
    '{"id":"case-passed","passed":true,"score":1,"input":"Review release","expected":"release eval","output":"asked for eval"}' \
    > "$opt_tmp/results.jsonl"
  python3 "$ROOT/scripts/optimize-teamwork.py" init-workspace \
    --workspace "$opt_tmp/workspace" --skill "$ROOT/skills/teamwork-design/SKILL.md" >/dev/null
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
    '{"date":"2026-07-08","candidate_id":"optimizer-smoke-valid","kind":"skillopt-lite","provider":"offline","model":"deterministic-smoke","model_config":"offline-smoke","prompt_or_template":"skills/teamwork-design/SKILL.md","owned_files":["skills/teamwork-review/SKILL.md"],"denylist":["evals/teamwork/cases/*.json"],"baseline":"evals/teamwork/README.md","treatment":"scripts/optimize-teamwork.py","gate_decision":"reject","rollback":"evals/teamwork/README.md","validation":["scripts/validate.sh"],"release_audit":"validate smoke only","reviewer":"validate.sh","decision":"rejected"}' \
    > "$opt_ledger_tmp/valid.jsonl"
  python3 "$ROOT/scripts/eval-teamwork.py" --optimizer-ledger "$opt_ledger_tmp/valid.jsonl" >/dev/null
  printf '%s\n' \
    '{"date":"2026-07-08","candidate_id":"optimizer-smoke-invalid","kind":"skillopt-lite","provider":"offline","model":"deterministic-smoke","model_config":"offline-smoke","prompt_or_template":"not_applicable","owned_files":["skills/teamwork-review/SKILL.md"],"denylist":["evals/teamwork/cases/*.json"],"baseline":"evals/teamwork/README.md","treatment":"scripts/optimize-teamwork.py","gate_decision":"reject","rollback":"evals/teamwork/README.md","validation":["scripts/validate.sh"],"release_audit":"validate smoke only","reviewer":"validate.sh","decision":"rejected"}' \
    > "$opt_ledger_tmp/invalid.jsonl"
  if python3 "$ROOT/scripts/eval-teamwork.py" --optimizer-ledger "$opt_ledger_tmp/invalid.jsonl" >/dev/null 2>&1; then
    fail "optimizer ledger smoke accepted placeholder evidence"
  fi
else
  validation_note "optimizer workspace smoke is release-only"
fi

[[ -f "$ROOT/scripts/validate_teamwork_index.py" ]] || fail "missing scripts/validate_teamwork_index.py"
git_known_package_file "scripts/validate_teamwork_index.py" \
  || fail "scripts/validate_teamwork_index.py is absent from the active validation index"
python3 "$ROOT/scripts/validate_teamwork_index.py" \
  "$ROOT/templates/teamwork-memory/index.json" >/dev/null
index_pointer_tmp="$(mktemp -d "${TMPDIR:-/tmp}/teamwork-index-pointer.XXXXXX")"
CLEANUP_PATHS+=("$index_pointer_tmp")

sed 's#"current": "docs/teamwork/current.md"#"current": "docs/teamwork/missing.md"#' \
  "$ROOT/templates/teamwork-memory/index.json" \
  > "$index_pointer_tmp/missing-pointer.json"
if python3 "$ROOT/scripts/validate_teamwork_index.py" \
  "$index_pointer_tmp/missing-pointer.json" >/dev/null 2>&1; then
  fail "Teamwork index validator accepted an active pointer without a matching entry"
fi
sed 's/"status": "active"/"status": "candidate"/' \
  "$ROOT/templates/teamwork-memory/index.json" \
  > "$index_pointer_tmp/candidate-pointer.json"
if python3 "$ROOT/scripts/validate_teamwork_index.py" \
  "$index_pointer_tmp/candidate-pointer.json" >/dev/null 2>&1; then
  fail "Teamwork index validator accepted a candidate entry as active truth"
fi
if [[ "${TEAMWORK_VALIDATE_LOCAL_MEMORY:-0}" == "1" && -f "$ROOT/docs/teamwork/index.json" ]]; then
  python3 "$ROOT/scripts/validate_teamwork_index.py" "$ROOT/docs/teamwork/index.json" >/dev/null
elif [[ -f "$ROOT/docs/teamwork/index.json" ]]; then
  validation_note "local Teamwork memory index validation is opt-in"
fi

# --- Plugin manifests ---
[[ -f "$ROOT/.codex-plugin/plugin.json" ]] || fail "missing Codex plugin manifest"
[[ -f "$ROOT/.claude-plugin/plugin.json" ]] || fail "missing Claude Code plugin manifest"
for plugin_file in scripts/build-codex-plugin.py scripts/plugin-activation.py .agents/plugins/marketplace.json; do
  [[ -f "$ROOT/$plugin_file" ]] || fail "missing $plugin_file"
  git_known_package_file "$plugin_file" \
    || fail "$plugin_file is absent from the active validation index"
done
[[ -x "$ROOT/scripts/build-codex-plugin.py" ]] || fail "build-codex-plugin.py must be executable"
[[ -x "$ROOT/scripts/plugin-activation.py" ]] || fail "plugin-activation.py must be executable"
compile_python_files "$ROOT/scripts/build-codex-plugin.py" "$ROOT/scripts/plugin-activation.py"
python3 "$ROOT/scripts/build-codex-plugin.py" --check \
  || fail "tracked Codex Marketplace bundle must match canonical inputs"
python3 -m json.tool "$ROOT/.codex-plugin/plugin.json" >/dev/null
python3 -m json.tool "$ROOT/.claude-plugin/plugin.json" >/dev/null
python3 - "$ROOT" <<'PY'
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
codex = json.loads((root / ".codex-plugin/plugin.json").read_text())
claude = json.loads((root / ".claude-plugin/plugin.json").read_text())
bundle = root / "plugins/teamwork-skill"
bundle_manifest = json.loads((bundle / ".codex-plugin/plugin.json").read_text())
marketplace = json.loads((root / ".agents/plugins/marketplace.json").read_text())
version = (root / "VERSION").read_text().strip()
if codex.get("skills") != "./skills/":
    raise SystemExit("FAIL: Codex manifest skills must remain ./skills/")
if "Codex" not in codex.get("description", ""):
    raise SystemExit("FAIL: Codex manifest description must mention Codex")
if codex.get("version") != version:
    raise SystemExit("FAIL: Codex manifest version must match VERSION")
if codex.get("interface", {}).get("defaultPrompt") is None or len(codex["interface"]["defaultPrompt"]) != 3:
    raise SystemExit("FAIL: Codex manifest must expose exactly three default prompts")
if any(not isinstance(prompt, str) or len(prompt) > 128 for prompt in codex["interface"]["defaultPrompt"]):
    raise SystemExit("FAIL: Codex default prompts must be strings of at most 128 characters")
if bundle_manifest != codex:
    raise SystemExit("FAIL: Marketplace bundle manifest must match the canonical Codex manifest")
if "hooks" in bundle_manifest:
    raise SystemExit("FAIL: Marketplace bundle manifest must not declare hooks")
expected_marketplace = {
    "name": "teamwork",
    "interface": {"displayName": "Teamwork"},
    "plugins": [{
        "name": "teamwork-skill",
        "source": {"source": "local", "path": "./plugins/teamwork-skill"},
        "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
        "category": "Productivity",
    }],
}
if marketplace != expected_marketplace:
    raise SystemExit("FAIL: Marketplace manifest drifted from the Teamwork contract")
expected_skills = {
    path.name for path in (root / "skills").iterdir()
    if path.is_dir() and (path / "SKILL.md").is_file()
}
if len(expected_skills) != 10:
    raise SystemExit("FAIL: canonical source inventory must discover exactly ten skills")
actual_skills = {path.name for path in (bundle / "skills").iterdir() if path.is_dir()}
if actual_skills != expected_skills:
    raise SystemExit("FAIL: Marketplace bundle skill inventory must match canonical source")
expected_references = {
    "teamwork-debug/references/runtime-diagnosis.md",
    "teamwork-research/references/deep-research.md",
    "teamwork-review/references/strict-review.md",
}
source_references = {
    path.relative_to(root / "skills").as_posix()
    for path in (root / "skills").rglob("*")
    if path.is_file() and path.parent.name == "references"
}
bundle_references = {
    path.relative_to(bundle / "skills").as_posix()
    for path in (bundle / "skills").rglob("*")
    if path.is_file() and path.parent.name == "references"
}
if source_references != expected_references or bundle_references != expected_references:
    raise SystemExit("FAIL: source and Marketplace bundle must contain exactly three public references")
expected_roles = {
    "codex-agents": {
        "teamwork-debugger.toml", "teamwork-designer.toml", "teamwork-explorer.toml",
        "teamwork-plan-reviewer.toml", "teamwork-planner.toml", "teamwork-researcher.toml",
        "teamwork-reviewer.toml", "teamwork-worker.toml",
    },
    "cursor-agents": {
        "debugger.md", "designer.md", "explorer.md", "plan-reviewer.md", "planner.md",
        "researcher.md", "reviewer.md", "worker.md",
    },
    "claude-agents": {
        "debugger.md", "designer.md", "explorer.md", "plan-reviewer.md", "planner.md",
        "researcher.md", "reviewer.md", "worker.md",
    },
}
for directory, expected in expected_roles.items():
    source_roles = {path.name for path in (root / "templates" / directory).iterdir() if path.is_file()}
    bundle_roles = {path.name for path in (bundle / "templates" / directory).iterdir() if path.is_file()}
    if source_roles != expected or bundle_roles != expected:
        raise SystemExit(f"FAIL: source and Marketplace bundle must contain exactly eight {directory} roles")
required_runtime = {
    "install.sh",
    "scripts/check-update.sh",
    "scripts/configure-codex-routing.py",
    "scripts/configure-notifications.py",
    "scripts/init-project.sh",
    "scripts/init-project-files.py",
    "scripts/discussion-transaction.py",
    "scripts/plugin-activation.py",
    "templates/codex-agents/teamwork-worker.toml",
    "templates/cursor-agents/worker.md",
    "templates/claude-agents/worker.md",
    "hooks/notify.py",
    "scripts/plugin-runtime-root.py",
    "scripts/tests/fixtures/v3.4.2-owned-surfaces.json",
    "templates/teamwork-memory/index.json",
    "templates/teamwork-memory/teamwork-design-template.md",
    "evals/teamwork/ledgers/v4-capability-migration.jsonl",
}
for rel in required_runtime:
    if not (bundle / rel).is_file():
        raise SystemExit(f"FAIL: Marketplace bundle is missing runtime input: {rel}")
if (bundle / "hooks/hooks.json").exists():
    raise SystemExit("FAIL: Marketplace bundle must not expose plugin-bundled hooks")
if (bundle / ".claude-plugin").exists():
    raise SystemExit("FAIL: Marketplace bundle must copy only the Codex plugin manifest")
if (bundle / ".teamwork-plugin-runtime").read_text() != "TEAMWORK_CODEX_PLUGIN_RUNTIME=1\n":
    raise SystemExit("FAIL: Marketplace bundle runtime marker is invalid")
if claude.get("skills") != "./skills/":
    raise SystemExit("FAIL: Claude manifest skills must remain ./skills/")
if "Claude Code" not in claude.get("description", ""):
    raise SystemExit("FAIL: Claude manifest description must mention Claude Code")
if claude.get("version") != version:
    raise SystemExit("FAIL: Claude manifest version must match VERSION")
claude_prompts = claude.get("interface", {}).get("defaultPrompt")
if not isinstance(claude_prompts, list) or len(claude_prompts) != 3 or any(
    not isinstance(prompt, str) or len(prompt) > 128 for prompt in claude_prompts
):
    raise SystemExit("FAIL: Claude default prompts must be three strings of at most 128 characters")
PY
while IFS= read -r bundle_file; do
  rel="${bundle_file#"$ROOT"/}"
  git_known_package_file "$rel" \
    || fail "$rel is absent from the active validation index"
done < <(find "$ROOT/plugins/teamwork-skill" -type f -o -type l | sort)

# --- Notification hooks and private session audit ---
for hook_file in hooks/hooks.json hooks/notify.py scripts/configure-notifications.py scripts/test_notify_hook.py scripts/audit-codex-sessions.py; do
  [[ -f "$ROOT/$hook_file" ]] || fail "missing $hook_file"
  git_known_package_file "$hook_file" \
    || fail "$hook_file is absent from the active validation index"
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
compile_python_files \
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
