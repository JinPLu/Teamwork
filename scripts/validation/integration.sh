#!/usr/bin/env bash

REAL_CODEX="${TEAMWORK_REAL_CODEX:-$(command -v codex 2>/dev/null || true)}"
if [[ -n "$REAL_CODEX" && ! -x "$REAL_CODEX" ]]; then
  REAL_CODEX=""
fi
CODEX_AGENTS=(
  teamwork-researcher
  teamwork-explorer
  teamwork-debugger
  teamwork-designer
  teamwork-planner
  teamwork-worker
  teamwork-writer
  teamwork-plan-reviewer
  teamwork-reviewer
)
CURSOR_AGENTS=(
  researcher
  explorer
  debugger
  designer
  planner
  worker
  writer
  plan-reviewer
  reviewer
)
CLAUDE_AGENTS=(
  researcher
  explorer
  debugger
  designer
  planner
  worker
  writer
  plan-reviewer
  reviewer
)

# Candidate validation intentionally inherits the caller's Git index/worktree.
# The release-state fixture is a different repository, so run only those Git
# commands in a clean environment rather than accidentally pointing them at the
# candidate repository.
isolated_git() {
  env -i PATH="$PATH" HOME="${HOME:-/tmp}" TMPDIR="${TMPDIR:-/tmp}" git "$@"
}

V342_SKILL_INVENTORY_FIXTURE="scripts/tests/fixtures/v3.4.2-skill-inventory.json"
[[ -f "$ROOT/$V342_SKILL_INVENTORY_FIXTURE" ]] \
  || fail "missing frozen v3.4.2 skill inventory fixture"
git_known_package_file "$V342_SKILL_INVENTORY_FIXTURE" \
  || fail "$V342_SKILL_INVENTORY_FIXTURE is absent from the active validation index"

# --- Exact v4 role templates ---
while IFS= read -r template; do
  ! grep -q 'grill/question-first' "$template" \
    || fail "agent template must not duplicate the grill procedure: ${template#"$ROOT/"}"
done < <(find "$ROOT/templates/codex-agents" "$ROOT/templates/cursor-agents" "$ROOT/templates/claude-agents" -type f | sort)
grep_absent 'Shared Understanding Packet\|Native Fields\|Option Matrix\|Worker Completion Packet\|Question Candidate' \
  "agent templates must not restore fixed packet ceremony" \
  "$ROOT/templates/codex-agents" "$ROOT/templates/cursor-agents" "$ROOT/templates/claude-agents"
grep_absent 'only lightweight commands\|Inspect additional material only\|attempt only a bounded' \
  "agent templates must not impose capability-harming universal caps" \
  "$ROOT/templates/codex-agents" "$ROOT/templates/cursor-agents" "$ROOT/templates/claude-agents"
python3 - "$ROOT" <<'PY'
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
roles = {
    "researcher": [
        root / "templates/codex-agents/teamwork-researcher.toml",
        root / "templates/cursor-agents/researcher.md",
        root / "templates/claude-agents/researcher.md",
    ],
    "explorer": [
        root / "templates/codex-agents/teamwork-explorer.toml",
        root / "templates/cursor-agents/explorer.md",
        root / "templates/claude-agents/explorer.md",
    ],
    "debugger": [
        root / "templates/codex-agents/teamwork-debugger.toml",
        root / "templates/cursor-agents/debugger.md",
        root / "templates/claude-agents/debugger.md",
    ],
    "designer": [
        root / "templates/codex-agents/teamwork-designer.toml",
        root / "templates/cursor-agents/designer.md",
        root / "templates/claude-agents/designer.md",
    ],
    "worker": [
        root / "templates/codex-agents/teamwork-worker.toml",
        root / "templates/cursor-agents/worker.md",
        root / "templates/claude-agents/worker.md",
    ],
    "writer": [
        root / "templates/codex-agents/teamwork-writer.toml",
        root / "templates/cursor-agents/writer.md",
        root / "templates/claude-agents/writer.md",
    ],
    "planner": [
        root / "templates/codex-agents/teamwork-planner.toml",
        root / "templates/cursor-agents/planner.md",
        root / "templates/claude-agents/planner.md",
    ],
    "plan-reviewer": [
        root / "templates/codex-agents/teamwork-plan-reviewer.toml",
        root / "templates/cursor-agents/plan-reviewer.md",
        root / "templates/claude-agents/plan-reviewer.md",
    ],
    "reviewer": [
        root / "templates/codex-agents/teamwork-reviewer.toml",
        root / "templates/cursor-agents/reviewer.md",
        root / "templates/claude-agents/reviewer.md",
    ],
}
required = {
    "researcher": ("sanitized brief", ("citations", "cited support")),
    "explorer": ("local evidence question", "codegraph"),
    "debugger": ("unknown failure", "immutable"),
    "designer": ("genuine alternatives", "strictly read-only"),
    "worker": ("exact writable paths", "proportional"),
    "writer": (
        "standalone document",
        "bounded writing brief",
        "facts/sources/citations/decisions/authority/status/acceptance",
        "default terminal workflow artifacts",
        "artifact-inspect -> artifact-schema <create|update|supersede> -> artifact-apply",
        "transaction-derived destination",
        "required transaction gate",
        "registration",
        "blocked without writing",
    ),
    "planner": ("selected direction", "execution-ready plan"),
    "plan-reviewer": ("accept", "revise", "blocked"),
    "reviewer": ("accept", "revise", "blocked"),
}
for role, paths in roles.items():
    if len(paths) != 3:
        raise SystemExit(f"FAIL: {role} must have exactly one template per host")
    for path in paths:
        if not path.is_file():
            raise SystemExit(f"FAIL: missing {role} template: {path}")
        text = " ".join(path.read_text(encoding="utf-8").split()).lower()
        for expectation in required[role]:
            alternatives = (expectation,) if isinstance(expectation, str) else expectation
            if not any(phrase in text for phrase in alternatives):
                raise SystemExit(
                    f"FAIL: {role} parity missing one of {alternatives!r}: {path}"
                )
if set(roles) != {
    "researcher", "explorer", "debugger", "designer", "planner", "worker", "writer", "plan-reviewer", "reviewer"
}:
    raise SystemExit("FAIL: role validation must name exactly the nine v4 roles")
PY
grep_absent 'done_with_concerns\|needs_context' \
  "agent templates must not restore retired lifecycle verdicts" \
  "$ROOT/templates/codex-agents" "$ROOT/templates/cursor-agents" "$ROOT/templates/claude-agents"

grep_absent 'teamwork-minimality\|minimality-mode\|minimality_mode' \
  "minimality must not add a route, stage, or mode" \
  "$ROOT/skills" "$ROOT/templates" "$ROOT/install.sh" "$ROOT/scripts/install"
grep_absent 'teamwork-quality' "Teamwork must not add a separate quality stage" "$ROOT/skills" "$ROOT/CODEX.md" "$ROOT/CURSOR.md" "$ROOT/CLAUDE.md" "$ROOT/install.sh" "$ROOT/scripts/install"
grep_absent 'teamwork-deslop' "Teamwork must not add a separate deslop stage" "$ROOT/skills" "$ROOT/CODEX.md" "$ROOT/CURSOR.md" "$ROOT/CLAUDE.md" "$ROOT/install.sh" "$ROOT/scripts/install"
[[ -f "$ROOT/skills/grill-me/SKILL.md" ]] || fail "question-first override must have one public grill-me skill"
[[ ! -e "$ROOT/skills/teamwork-grill" ]] || fail "question-first override must not become a peer teamwork-grill skill"
grep_absent 'teamwork-grill)' "install skill list must not add a peer teamwork-grill skill" "$ROOT/install.sh" "$ROOT/scripts/install"

grep_required 'owns only the named project' "$ROOT/skills/teamwork-init/SKILL.md" \
  "teamwork-init must stay project-local"
grep_absent 'check-update.sh' \
  "teamwork-init must not absorb global install freshness" \
  "$ROOT/skills/teamwork-init"
grep_required 'check-update.sh' "$ROOT/skills/teamwork-update/SKILL.md" "teamwork-update must reference check-update script"
[[ -x "$ROOT/scripts/check-update.sh" ]] || fail "check-update script must be executable"
grep_required 'skills_content_status' "$ROOT/scripts/check-update.sh" "check-update must detect installed skill drift"
grep_required 'agents_content_status' "$ROOT/scripts/check-update.sh" "check-update must detect installed agent drift"
grep_required 'review-required' "$ROOT/scripts/check-update.sh" "check-update must surface untrusted Codex notification hooks"
grep_required 'run /hooks' "$ROOT/scripts/install/targets.sh" "notification install must preserve the Codex hook trust boundary"
grep_required 'all' "$ROOT/install.sh" "full global installs must remain available"
grep_required 'project-local' "$ROOT/scripts/init-project.sh" \
  "init-project must declare its project-local boundary"
grep_absent 'install_global_surfaces\|configure-notifications' \
  "init-project must not refresh global installs, policy, or notifications" \
  "$ROOT/scripts/init-project.sh"
grep_absent 'init-project refreshes the user-level routing\|init-project to refresh global Teamwork surfaces\|teamwork-init gate' \
  "installer help must not claim that project init mutates global state" \
  "$ROOT/install.sh" "$ROOT/scripts/install/common.sh" "$ROOT/scripts/check-update.sh"
grep_required 'trust-all' "$ROOT/skills/teamwork-update/SKILL.md" "teamwork-update must trust only exact Teamwork hooks"

if git -C "$ROOT" grep -n -E 'raoctl|RAO|Stop hook|/rao:|/teamwork:' \
  -- ':!scripts/validate.sh' ':!scripts/validation/**' >/tmp/teamwork-retired-grep.$$; then
  cat /tmp/teamwork-retired-grep.$$ >&2
  rm -f /tmp/teamwork-retired-grep.$$
  fail "retired multi-runtime references remain outside validation"
fi
rm -f /tmp/teamwork-retired-grep.$$

tmp="$(cd "$(mktemp -d)" && pwd -P)"
check_skill_link() {
  local installed="$1"
  local skill="$2"
  local platform="$3"
  [[ -L "$installed" ]] || fail "$platform link install must symlink the $skill skill directory"
  [[ "$(cd "$installed" && pwd -P)" == "$(cd "$ROOT/skills/$skill" && pwd -P)" ]] \
    || fail "$platform $skill skill link must resolve to source"
}

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
unproven_teamwork_dir="$tmp/home/.codex/skills/teamwork"
mkdir -p "$unproven_teamwork_dir/references"
printf '%s\n' '---' 'name: teamwork' 'description: Use when selecting a Teamwork stage.' '---' > "$unproven_teamwork_dir/SKILL.md"
while IFS= read -r ref_file; do
  printf '%s\n' "retired $ref_file" > "$unproven_teamwork_dir/references/$ref_file"
done < <(python3 - "$ROOT/$V342_SKILL_INVENTORY_FIXTURE" <<'PY'
import json
import pathlib
import sys

fixture = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
prefix = "skills/using-teamwork/references/"
for value in fixture["files"]:
    if value.startswith(prefix):
        print(pathlib.PurePosixPath(value).name)
PY
)
HOME="$tmp/home" "$ROOT/install.sh" >/dev/null
[[ ! -e "$tmp/home/.fake-codex-invocations" ]] \
  || fail "Codex install must not invoke the host CLI to manage interaction capabilities"
[[ -e "$unproven_teamwork_dir" ]] \
  || fail "Codex install must preserve a generic teamwork skill unless exact Teamwork ownership is proven"
grep_required '^description: Use when selecting a Teamwork stage\.$' "$unproven_teamwork_dir/SKILL.md" \
  "Codex install must preserve unproven generic teamwork skill content"
for skill in "${SKILLS[@]}"; do
  [[ -f "$tmp/home/.agents/skills/$skill/SKILL.md" ]] || fail "Codex install missing $skill"
  [[ ! -L "$tmp/home/.agents/skills/$skill/SKILL.md" ]] || fail "default install must copy $skill"
  grep_required "^name: $skill$" "$tmp/home/.agents/skills/$skill/SKILL.md" \
    "installed skill has wrong name: $skill"
done
[[ "$(tr -d '[:space:]' < "$tmp/home/.agents/skills/.teamwork-version")" == "$(tr -d '[:space:]' < "$ROOT/VERSION")" ]] \
  || fail "Codex install must write .teamwork-version matching VERSION"
[[ -f "$tmp/home/.agents/skills/.teamwork-profile" ]] \
  || fail "Codex install must write .teamwork-profile"
if HOME="$tmp/home" "$ROOT/scripts/check-update.sh" --readiness --no-fetch \
  > "$tmp/fresh-readiness.out"; then
  fail "single-platform install must not claim complete three-platform readiness"
fi
grep_required '^INSTALL_READY=no$' "$tmp/fresh-readiness.out" \
  "single-platform readiness must remain incomplete"
grep_required '^MISSING=.*cursor-skills.*claude-skills' "$tmp/fresh-readiness.out" \
  "single-platform readiness must name the missing platform skills"
grep_absent 'codex-skill-content' \
  "fresh Codex skill content must not be reported stale" \
  "$tmp/fresh-readiness.out"
grep_required '^MANAGED_INSTALL_READY=' "$tmp/fresh-readiness.out" \
  "readiness must distinguish managed install state"
grep_required '^HOST_ACTIVATION=manual-action-required$' "$tmp/fresh-readiness.out" \
  "readiness must expose remaining host-owned manual activation"
grep_required '^MANUAL_ACTIONS=.*cursor-policy-paste' "$tmp/fresh-readiness.out" \
  "readiness must name the remaining Cursor policy action"
grep_absent '^HOST_ACTIVATION=ready$' \
  "static install readiness must not claim live host activation" \
  "$tmp/fresh-readiness.out"
[[ ! -e "$tmp/home/.fake-codex-invocations" ]] \
  || fail "readiness must not invoke the host CLI to manage interaction capabilities"

legacy_codex_home="$tmp/home-codex-legacy-skills"
legacy_codex_root="$legacy_codex_home/.codex/skills"
mkdir -p "$legacy_codex_root"
for skill in "${SKILLS[@]}"; do
  cp -R "$ROOT/skills/$skill" "$legacy_codex_root/$skill"
done
printf '%s\n' "$(tr -d '[:space:]' < "$ROOT/VERSION")" > "$legacy_codex_root/.teamwork-version"
printf '%s\n' performance-first > "$legacy_codex_root/.teamwork-profile"
printf '%s\n' 'preserve unrelated skill root content' > "$legacy_codex_root/unrelated.txt"
HOME="$legacy_codex_home" "$ROOT/install.sh" codex >/dev/null
for skill in "${SKILLS[@]}"; do
  [[ -f "$legacy_codex_home/.agents/skills/$skill/SKILL.md" ]] \
    || fail "Codex install must migrate $skill to the supported user skill root"
  [[ ! -e "$legacy_codex_root/$skill" ]] \
    || fail "Codex install must remove its owned legacy duplicate for $skill"
done
[[ -f "$legacy_codex_root/unrelated.txt" ]] \
  || fail "Codex legacy migration must preserve unrelated root content"
[[ ! -e "$legacy_codex_root/.teamwork-version" && ! -e "$legacy_codex_root/.teamwork-profile" ]] \
  || fail "Codex legacy migration must remove obsolete Teamwork ownership markers"

readonly_legacy_home="$tmp/home-codex-readonly-legacy"
readonly_legacy_root="$readonly_legacy_home/.codex/skills"
mkdir -p "$readonly_legacy_root"
cp -R "$ROOT/skills/grill-me" "$readonly_legacy_root/grill-me"
printf '%s\n' current > "$readonly_legacy_root/.teamwork-version"
printf '%s\n' performance-first > "$readonly_legacy_root/.teamwork-profile"
chmod a-w "$readonly_legacy_root"
readonly_legacy_rc=0
HOME="$readonly_legacy_home" "$ROOT/install.sh" --no-notifications codex >/dev/null 2>&1 \
  || readonly_legacy_rc=$?
chmod u+w "$readonly_legacy_root"
if [[ "$readonly_legacy_rc" -eq 0 ]]; then
  fail "Codex install must reject a legacy root that cannot be cleaned"
fi
[[ -f "$readonly_legacy_root/grill-me/SKILL.md" ]] \
  || fail "failed legacy cleanup preflight must preserve the legacy skill"
[[ ! -e "$readonly_legacy_home/.agents/skills/grill-me" ]] \
  || fail "failed legacy cleanup preflight must not create a duplicate new-root skill"
[[ ! -e "$readonly_legacy_home/.codex/config.toml" ]] \
  || fail "legacy cleanup preflight must fail before routing mutation"

custom_codex_home="$tmp/home-codex-custom-root"
custom_codex_runtime="$tmp/custom-codex-runtime"
mkdir -p "$custom_codex_runtime/skills"
cp -R "$ROOT/skills/grill-me" "$custom_codex_runtime/skills/grill-me"
printf '%s\n' current > "$custom_codex_runtime/skills/.teamwork-version"
printf '%s\n' performance-first > "$custom_codex_runtime/skills/.teamwork-profile"
HOME="$custom_codex_home" CODEX_HOME="$custom_codex_runtime" \
  "$ROOT/install.sh" codex >/dev/null
[[ -f "$custom_codex_home/.agents/skills/grill-me/SKILL.md" ]] \
  || fail "Codex install must keep the supported skill root independent of CODEX_HOME"
[[ ! -e "$custom_codex_runtime/skills/grill-me" ]] \
  || fail "Codex install must migrate an owned legacy CODEX_HOME skill"

unknown_legacy_home="$tmp/home-codex-unknown-legacy"
mkdir -p "$unknown_legacy_home/.codex/skills"
cp -R "$ROOT/skills/grill-me" "$unknown_legacy_home/.codex/skills/grill-me"
if HOME="$unknown_legacy_home" "$ROOT/install.sh" codex >/dev/null 2>&1; then
  fail "Codex install must reject an unmarked legacy same-name skill"
fi
[[ -f "$unknown_legacy_home/.codex/skills/grill-me/SKILL.md" ]] \
  || fail "rejected legacy migration must preserve the existing skill"
[[ ! -e "$unknown_legacy_home/.agents/skills/grill-me" ]] \
  || fail "rejected legacy migration must not create a duplicate skill"
[[ ! -e "$unknown_legacy_home/.codex/config.toml" ]] \
  || fail "legacy migration preflight must fail before routing mutation"

unknown_inventory_home="$tmp/home-codex-unknown-inventory"
mkdir -p "$unknown_inventory_home/.codex/skills"
cp -R "$ROOT/skills/grill-me" "$unknown_inventory_home/.codex/skills/grill-me"
printf '%s\n' current > "$unknown_inventory_home/.codex/skills/.teamwork-version"
printf '%s\n' performance-first > "$unknown_inventory_home/.codex/skills/.teamwork-profile"
printf '%s\n' 'user file' > "$unknown_inventory_home/.codex/skills/grill-me/notes.md"
if HOME="$unknown_inventory_home" "$ROOT/install.sh" codex >/dev/null 2>&1; then
  fail "Codex install must reject unknown files inside a legacy Teamwork skill"
fi
[[ -f "$unknown_inventory_home/.codex/skills/grill-me/notes.md" ]] \
  || fail "rejected unknown legacy inventory must remain untouched"

unknown_destination_home="$tmp/home-codex-unknown-destination"
mkdir -p "$unknown_destination_home/.agents/skills"
cp -R "$ROOT/skills/grill-me" "$unknown_destination_home/.agents/skills/grill-me"
if HOME="$unknown_destination_home" "$ROOT/install.sh" codex >/dev/null 2>&1; then
  fail "Codex install must reject an unmarked same-name skill at the supported root"
fi
[[ -f "$unknown_destination_home/.agents/skills/grill-me/SKILL.md" ]] \
  || fail "rejected supported-root collision must remain untouched"
[[ ! -e "$unknown_destination_home/.codex/config.toml" ]] \
  || fail "supported-root preflight must fail before routing mutation"

for agent in "${CODEX_AGENTS[@]}"; do
  [[ -f "$tmp/home/.codex/agents/$agent.toml" ]] \
    || fail "Codex install must copy Codex agent $agent"
  [[ ! -L "$tmp/home/.codex/agents/$agent.toml" ]] \
    || fail "default Codex install must copy Codex agent $agent"
done
for agent in teamwork-researcher teamwork-explorer teamwork-debugger teamwork-designer teamwork-planner teamwork-worker teamwork-plan-reviewer; do
  grep_required '^model_reasoning_effort = "high"$' "$tmp/home/.codex/agents/$agent.toml" \
    "Codex install must render high reasoning for $agent"
done
grep_required '^model_reasoning_effort = "low"$' "$tmp/home/.codex/agents/teamwork-writer.toml" \
  "Codex install must render low reasoning for teamwork-writer"
for agent in teamwork-reviewer; do
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
codex_policy_err="$tmp/codex-policy.err"
HOME="$tmp/home-codex-policy" "$ROOT/install.sh" codex-policy \
  > "$codex_policy_out" 2> "$codex_policy_err"
[[ ! -s "$codex_policy_err" ]] \
  || fail "codex-policy target must render without shell-expansion errors"
grep_required '<!-- TEAMWORK_CODEX_GLOBAL_START -->' "$codex_policy_out" \
  "codex-policy target must print Teamwork global policy start marker"
check_lean_policy "$codex_policy_out" performance-first "codex-policy output"
[[ ! -e "$tmp/home-codex-policy/.codex/AGENTS.md" ]] \
  || fail "codex-policy target must not write global AGENTS policy"

HOME="$tmp/home-codex-agents" "$ROOT/install.sh" codex-agents >/dev/null
for agent in "${CODEX_AGENTS[@]}"; do
  [[ -f "$tmp/home-codex-agents/.codex/agents/$agent.toml" ]] \
    || fail "Codex agent install missing $agent"
  [[ ! -L "$tmp/home-codex-agents/.codex/agents/$agent.toml" ]] \
    || fail "default Codex agent install must copy $agent"
done
for agent in teamwork-researcher teamwork-explorer teamwork-debugger teamwork-planner teamwork-worker; do
  grep_required '^model = "gpt-5.5"$' "$tmp/home-codex-agents/.codex/agents/$agent.toml" \
    "default Codex execution-path agent must use gpt-5.5 for $agent"
  grep_required '^model_reasoning_effort = "high"$' "$tmp/home-codex-agents/.codex/agents/$agent.toml" \
    "default Codex execution-path agent must use high reasoning for $agent"
done
grep_required '^model = "gpt-5.5"$' "$tmp/home-codex-agents/.codex/agents/teamwork-writer.toml" \
  "default Codex writer install must use gpt-5.5"
grep_required '^model_reasoning_effort = "low"$' "$tmp/home-codex-agents/.codex/agents/teamwork-writer.toml" \
  "default Codex writer install must use low reasoning"
for agent in teamwork-designer teamwork-plan-reviewer; do
  grep_required '^model = "gpt-5.6-sol"$' "$tmp/home-codex-agents/.codex/agents/$agent.toml" \
    "default Codex agent install must render gpt-5.6-sol for $agent"
  grep_required '^model_reasoning_effort = "high"$' "$tmp/home-codex-agents/.codex/agents/$agent.toml" \
    "default Codex agent install must render high reasoning for $agent"
done
for agent in teamwork-reviewer; do
  grep_required '^model = "gpt-5.6-sol"$' "$tmp/home-codex-agents/.codex/agents/$agent.toml" \
    "default Codex reviewer install must render gpt-5.6-sol for $agent"
  grep_required '^model_reasoning_effort = "max"$' "$tmp/home-codex-agents/.codex/agents/$agent.toml" \
    "default Codex reviewer install must render max reasoning for $agent"
done
[[ ! -e "$tmp/home-codex-agents/.codex/AGENTS.md" ]] \
  || fail "codex-agents target must not write global AGENTS policy"
codex_routing_config="$tmp/home-codex-agents/.codex/config.toml"
grep_required '^\[features\]$' "$codex_routing_config" \
  "codex-agents must configure the stable Codex feature table"
grep_required '^multi_agent = true$' "$codex_routing_config" \
  "Codex routing must enable the stable multi_agent feature"
grep_absent 'multi_agent_v2' \
  "Codex routing must remove the legacy multi_agent_v2 contract" \
  "$codex_routing_config"
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
grep_required '^max_threads = 4$' "$legacy_routing_home/.codex/config.toml" \
  "routing migration must preserve stable Codex agents.max_threads"
grep_required '^multi_agent = true$' "$legacy_routing_home/.codex/config.toml" \
  "routing migration must configure the stable multi_agent feature"
grep_absent 'multi_agent_v2' "routing migration must remove legacy multi_agent_v2" \
  "$legacy_routing_home/.codex/config.toml"
grep_required '^# preserve me$' "$legacy_routing_home/.codex/config.toml" \
  "routing migration must preserve unrelated comments"

HOME="$tmp/home-codex-no-routing" "$ROOT/install.sh" --no-codex-routing codex-agents >/dev/null
[[ ! -e "$tmp/home-codex-no-routing/.codex/config.toml" ]] \
  || fail "--no-codex-routing must preserve a missing user config"

HOME="$tmp/home-codex-agents-cost" "$ROOT/install.sh" --profile cost-first codex-agents >/dev/null
for agent in teamwork-researcher teamwork-explorer teamwork-debugger teamwork-planner teamwork-worker; do
  grep_required '^model = "gpt-5.5"$' "$tmp/home-codex-agents-cost/.codex/agents/$agent.toml" \
    "cost-first Codex agent install must use gpt-5.5 for $agent"
  grep_required '^model_reasoning_effort = "medium"$' "$tmp/home-codex-agents-cost/.codex/agents/$agent.toml" \
    "cost-first Codex agent install must use medium reasoning for $agent"
done
grep_required '^model = "gpt-5.5"$' "$tmp/home-codex-agents-cost/.codex/agents/teamwork-writer.toml" \
  "cost-first Codex writer install must use gpt-5.5"
grep_required '^model_reasoning_effort = "low"$' "$tmp/home-codex-agents-cost/.codex/agents/teamwork-writer.toml" \
  "cost-first Codex writer install must use low reasoning"
for agent in teamwork-designer; do
  grep_required '^model = "gpt-5.6-sol"$' "$tmp/home-codex-agents-cost/.codex/agents/$agent.toml" \
    "cost-first Codex agent install must use Sol for $agent"
  grep_required '^model_reasoning_effort = "medium"$' "$tmp/home-codex-agents-cost/.codex/agents/$agent.toml" \
    "cost-first Codex agent install must use medium reasoning for $agent"
done
for agent in teamwork-plan-reviewer teamwork-reviewer; do
  grep_required '^model = "gpt-5.6-sol"$' "$tmp/home-codex-agents-cost/.codex/agents/$agent.toml" \
    "cost-first Codex agent install must use Sol for $agent"
  grep_required '^model_reasoning_effort = "high"$' "$tmp/home-codex-agents-cost/.codex/agents/$agent.toml" \
    "cost-first Codex reviewer install must use high reasoning for $agent"
done

HOME="$tmp/home-codex-cost" "$ROOT/install.sh" --profile cost-first codex >/dev/null
check_lean_policy "$tmp/home-codex-cost/.codex/AGENTS.md" cost-first "cost-first Codex policy"

HOME="$tmp/home-codex-policy-cost" "$ROOT/install.sh" --profile cost-first codex-policy > "$tmp/codex-policy-cost.out"
check_lean_policy "$tmp/codex-policy-cost.out" cost-first "cost-first codex-policy output"
[[ ! -e "$tmp/home-codex-policy-cost/.codex/AGENTS.md" ]] \
  || fail "cost-first codex-policy target must not write global AGENTS policy"

removed_project_root="$tmp/removed-project-routes"
mkdir -p "$removed_project_root"
for removed_target in project project-codex-agents; do
  removed_route_rc=0
  removed_route_output="$(
    HOME="$tmp/home-removed-$removed_target" "$ROOT/install.sh" \
      --project-root "$removed_project_root" "$removed_target" 2>&1
  )" || removed_route_rc=$?
  [[ "$removed_route_rc" -eq 2 ]] \
    || fail "$removed_target must be rejected as a removed public route"
  printf '%s\n' "$removed_route_output" | grep -q 'Project-local install targets were removed' \
    || fail "$removed_target rejection must explain the replacement workflow"
done
for removed_path in \
  "$removed_project_root/.agents" \
  "$removed_project_root/.codex/agents" \
  "$removed_project_root/.cursor/skills" \
  "$removed_project_root/.claude/skills"; do
  [[ ! -e "$removed_path" ]] \
    || fail "removed project install routes must not create $removed_path"
done

project_update="$tmp/project-update"
mkdir -p "$project_update"
HOME="$tmp/home-project-update" "$ROOT/install.sh" all >/dev/null
routing_update_config="$tmp/home-project-update/.codex/config.toml"

release_remote="$tmp/release-state.git"
release_work="$tmp/release-state-work"
isolated_git init --bare "$release_remote" >/dev/null
isolated_git init "$release_work" >/dev/null
isolated_git -C "$release_work" \
  -c user.name=Teamwork -c user.email=teamwork@example.invalid \
  -c commit.gpgsign=false commit --allow-empty -m fixture >/dev/null
isolated_git -C "$release_work" tag v0.0.1
isolated_git -C "$release_work" remote add origin "$release_remote"
isolated_git -C "$release_work" push origin HEAD:main --tags >/dev/null
TEAMWORK_GITHUB_REPO="$release_remote" HOME="$tmp/home-project-update" \
  "$ROOT/scripts/check-update.sh" > "$tmp/release-state.out" || true
grep_required '^Remote tag VERSION: 0\.0\.1$' "$tmp/release-state.out" \
  "check-update must read a remote semver tag"
grep_required '^Remote tag status: stale (0\.0\.1 -> ' "$tmp/release-state.out" \
  "check-update must report stale remote tag drift"
grep_required '^GitHub Release VERSION: unavailable$' "$tmp/release-state.out" \
  "check-update must keep non-GitHub release state best-effort"

sed 's/multi_agent = true/multi_agent = false/' \
  "$routing_update_config" > "$tmp/stale-routing.toml"
mv "$tmp/stale-routing.toml" "$routing_update_config"
HOME="$tmp/home-project-update" "$ROOT/scripts/check-update.sh" --readiness --no-fetch > "$tmp/global-routing-stale.out" || true
grep_required '^INSTALL_READY=no$' "$tmp/global-routing-stale.out" \
  "check-update readiness must fail on stale Codex routing"
grep_required 'codex-routing' "$tmp/global-routing-stale.out" \
  "check-update readiness must identify stale Codex routing"
HOME="$tmp/home-project-update" "$ROOT/install.sh" all >/dev/null
HOME="$tmp/home-project-update" "$ROOT/scripts/check-update.sh" --readiness --no-fetch > "$tmp/global-routing-ready.out"
grep_required '^CODEX_ROUTING=ready$' "$tmp/global-routing-ready.out" \
  "user refresh must repair Codex routing readiness"
printf '\n# stale grill-me skill fixture\n' >> "$tmp/home-project-update/.agents/skills/grill-me/SKILL.md"
HOME="$tmp/home-project-update" "$ROOT/scripts/check-update.sh" --readiness --no-fetch > "$tmp/global-grill-skill-stale.out" || true
grep_required '^INSTALL_READY=no$' "$tmp/global-grill-skill-stale.out" \
  "check-update readiness must fail when installed grill-me content drifts"
grep_required 'codex-skill-content' "$tmp/global-grill-skill-stale.out" \
  "check-update readiness must identify global Codex skill content drift"
HOME="$tmp/home-project-update" "$ROOT/install.sh" all >/dev/null
rm "$tmp/home-project-update/.agents/skills/grill-me/SKILL.md"
HOME="$tmp/home-project-update" "$ROOT/scripts/check-update.sh" --readiness --no-fetch > "$tmp/global-codex-grill-missing.out" || true
grep_required 'codex-skills' "$tmp/global-codex-grill-missing.out" \
  "check-update readiness must identify missing Codex grill-me content"
HOME="$tmp/home-project-update" "$ROOT/install.sh" all >/dev/null
rm "$tmp/home-project-update/.claude/skills/grill-me/SKILL.md"
HOME="$tmp/home-project-update" "$ROOT/scripts/check-update.sh" --readiness --no-fetch > "$tmp/global-grill-skill-missing.out" || true
grep_required '^INSTALL_READY=no$' "$tmp/global-grill-skill-missing.out" \
  "check-update readiness must fail when installed grill-me is missing"
grep_required 'claude-skills' "$tmp/global-grill-skill-missing.out" \
  "check-update readiness must identify a missing global Claude skill"
HOME="$tmp/home-project-update" "$ROOT/install.sh" all >/dev/null
printf '\n# stale Claude grill-me fixture\n' >> "$tmp/home-project-update/.claude/skills/grill-me/SKILL.md"
HOME="$tmp/home-project-update" "$ROOT/scripts/check-update.sh" --readiness --no-fetch > "$tmp/global-claude-grill-stale.out" || true
grep_required 'claude-skill-content' "$tmp/global-claude-grill-stale.out" \
  "check-update readiness must identify changed Claude grill-me content"
HOME="$tmp/home-project-update" "$ROOT/install.sh" all >/dev/null
printf '\n# stale Cursor grill-me fixture\n' >> "$tmp/home-project-update/.cursor/skills/grill-me/SKILL.md"
HOME="$tmp/home-project-update" "$ROOT/scripts/check-update.sh" --readiness --no-fetch > "$tmp/global-cursor-grill-stale.out" || true
grep_required 'cursor-skill-content' "$tmp/global-cursor-grill-stale.out" \
  "check-update readiness must identify changed Cursor grill-me content"
HOME="$tmp/home-project-update" "$ROOT/install.sh" all >/dev/null
rm "$tmp/home-project-update/.cursor/skills/grill-me/SKILL.md"
HOME="$tmp/home-project-update" "$ROOT/scripts/check-update.sh" --readiness --no-fetch > "$tmp/global-cursor-grill-missing.out" || true
grep_required 'cursor-skills' "$tmp/global-cursor-grill-missing.out" \
  "check-update readiness must identify missing Cursor grill-me content"
HOME="$tmp/home-project-update" "$ROOT/install.sh" all >/dev/null
printf '\n# stale global agent drift fixture\n' >> "$tmp/home-project-update/.codex/agents/teamwork-worker.toml"
HOME="$tmp/home-project-update" "$ROOT/scripts/check-update.sh" --no-fetch > "$tmp/global-agent-stale-report.out" || true
grep_required 'drift(missing=0,changed=1,extra=0)' "$tmp/global-agent-stale-report.out" \
  "check-update report must show global agent content drift"
grep_required 'Summary: .*issue' "$tmp/global-agent-stale-report.out" \
  "check-update report must count global agent content drift"
HOME="$tmp/home-project-update" "$ROOT/install.sh" all >/dev/null
HOME="$tmp/home-project-update" "$ROOT/scripts/check-update.sh" --readiness --no-fetch \
  > "$tmp/global-only-readiness.out"
grep_required '^INSTALL_READY=yes$' "$tmp/global-only-readiness.out" \
  "global readiness must pass after a fresh global install"
grep_required '^MISSING=cursor-policy-manual$' "$tmp/global-only-readiness.out" \
  "global readiness must recognize wrapped Codex and Claude policy text"
! grep -q '^PROJECT_' "$tmp/global-only-readiness.out" \
  || fail "global-only readiness must not report deleted project-local package surfaces"
removed_project_flag_rc=0
removed_project_flag_output="$(
  HOME="$tmp/home-project-update" "$ROOT/scripts/check-update.sh" \
    --readiness --project "$project_update" --no-fetch 2>&1
)" || removed_project_flag_rc=$?
[[ "$removed_project_flag_rc" -eq 2 ]] \
  || fail "check-update --project must be rejected after project-local package removal"
printf '%s\n' "$removed_project_flag_output" | grep -q -- '--project was removed' \
  || fail "check-update --project rejection must explain the removed surface"

HOME="$tmp/home-invalid-profile" "$ROOT/install.sh" --profile invalid codex >/dev/null 2>&1 \
  && fail "installer must reject unsupported Codex profiles"

HOME="$tmp/home-codex-agents-link" "$ROOT/install.sh" --link codex-agents >/dev/null
for agent in "${CODEX_AGENTS[@]}"; do
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
  [[ -L "$tmp/home-link/.agents/skills/$skill" ]] || fail "link install must symlink $skill directory"
done
check_skill_link "$tmp/home-link/.agents/skills/teamwork-design" "teamwork-design" "Codex"

HOME="$tmp/home-cursor" "$ROOT/install.sh" cursor >/dev/null
for skill in "${SKILLS[@]}"; do
  [[ -f "$tmp/home-cursor/.cursor/skills/$skill/SKILL.md" ]] || fail "Cursor install missing $skill"
  [[ ! -L "$tmp/home-cursor/.cursor/skills/$skill/SKILL.md" ]] || fail "default Cursor install must copy $skill"
done
for agent in "${CURSOR_AGENTS[@]}"; do
  [[ -f "$tmp/home-cursor/.cursor/agents/$agent.md" ]] \
    || fail "Cursor install must copy Cursor agent $agent"
  [[ ! -L "$tmp/home-cursor/.cursor/agents/$agent.md" ]] \
    || fail "default Cursor install must copy Cursor agent $agent"
done
grep_required '^model: gpt-5.6-terra-medium$' "$tmp/home-cursor/.cursor/agents/researcher.md" \
  "Cursor install must render terra medium model for researcher"
grep_required '^model: gemini-3.5-flash$' "$tmp/home-cursor/.cursor/agents/explorer.md" \
  "Cursor install must render gemini flash model for explorer"
grep_required '^model: composer-2.5-fast$' "$tmp/home-cursor/.cursor/agents/worker.md" \
  "Cursor install must render composer 2.5 model for worker"
grep_required '^model: composer-2.5-fast$' "$tmp/home-cursor/.cursor/agents/writer.md" \
  "Cursor install must render composer 2.5 model for writer"
grep_required '^model: claude-opus-4-8-thinking-high$' "$tmp/home-cursor/.cursor/agents/debugger.md" \
  "Cursor install must render opus 4.8 model for debugger"
grep_required '^model: gpt-5.6-sol-medium$' "$tmp/home-cursor/.cursor/agents/designer.md" \
  "Cursor install must render sol medium model for designer"
grep_required '^model: gpt-5.6-terra-medium$' "$tmp/home-cursor/.cursor/agents/planner.md" \
  "Cursor install must render terra medium model for planner"
grep_required '^model: claude-opus-4-8-thinking-high$' "$tmp/home-cursor/.cursor/agents/plan-reviewer.md" \
  "Cursor install must render opus 4.8 model for plan-reviewer"
grep_required '^model: claude-fable-5-thinking-high$' "$tmp/home-cursor/.cursor/agents/reviewer.md" \
  "Cursor install must render fable 5 model for reviewer"
[[ -f "$tmp/home-cursor/.cursor/mcp.json" ]] \
  || fail "Cursor install must write ~/.cursor/mcp.json"
[[ -f "$tmp/home-cursor/.cursor/.teamwork-mcp.json" ]] \
  || fail "Cursor install must write Teamwork MCP ownership sidecar"
python3 - "$tmp/home-cursor/.cursor/mcp.json" <<'PY'
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
servers = payload.get("mcpServers", {})
for name in ("codegraph", "gpu-broker"):
    if name not in servers:
        raise SystemExit(f"missing Teamwork MCP server: {name}")
if servers["codegraph"].get("command") != "codegraph":
    raise SystemExit("codegraph MCP command mismatch")
if servers["gpu-broker"].get("command") != "gpu-broker-mcp":
    raise SystemExit("gpu-broker MCP command mismatch")
PY

HOME="$tmp/home-cursor-no-mcp" "$ROOT/install.sh" --no-mcp cursor >/dev/null
[[ ! -e "$tmp/home-cursor-no-mcp/.cursor/mcp.json" ]] \
  || fail "--no-mcp cursor install must not write mcp.json"

mkdir -p "$tmp/home-cursor-preserve/.cursor"
printf '%s\n' '{"mcpServers":{"custom-server":{"command":"keep-me"}}}' \
  > "$tmp/home-cursor-preserve/.cursor/mcp.json"
HOME="$tmp/home-cursor-preserve" "$ROOT/install.sh" cursor-mcp >/dev/null
python3 - "$tmp/home-cursor-preserve/.cursor/mcp.json" <<'PY'
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
servers = payload.get("mcpServers", {})
if "custom-server" not in servers:
    raise SystemExit("cursor-mcp must preserve unrelated MCP servers")
for name in ("codegraph", "gpu-broker"):
    if name not in servers:
        raise SystemExit(f"missing Teamwork MCP server after preserve merge: {name}")
PY

HOME="$tmp/home-cursor-agents" "$ROOT/install.sh" cursor-agents >/dev/null
for agent in "${CURSOR_AGENTS[@]}"; do
  [[ -f "$tmp/home-cursor-agents/.cursor/agents/$agent.md" ]] \
    || fail "Cursor agent install missing $agent"
done
[[ ! -e "$tmp/home-cursor-agents/.cursor/skills" ]] \
  || fail "cursor-agents target must not write Cursor skills"

HOME="$tmp/home-cursor-cost" "$ROOT/install.sh" --profile cost-first cursor-agents >/dev/null
for agent in researcher explorer; do
  grep_required '^model: gemini-3.5-flash$' "$tmp/home-cursor-cost/.cursor/agents/$agent.md" \
    "cost-first Cursor agent install must downshift $agent"
done
grep_required '^model: composer-2.5-fast$' "$tmp/home-cursor-cost/.cursor/agents/worker.md" \
  "cost-first Cursor agent install must keep composer 2.5 model for worker"
grep_required '^model: composer-2.5-fast$' "$tmp/home-cursor-cost/.cursor/agents/writer.md" \
  "cost-first Cursor agent install must keep composer 2.5 model for writer"
grep_required '^model: gpt-5.6-terra-medium$' "$tmp/home-cursor-cost/.cursor/agents/debugger.md" \
  "cost-first Cursor agent install must downshift debugger"
grep_required '^model: gpt-5.6-terra-medium$' "$tmp/home-cursor-cost/.cursor/agents/designer.md" \
  "cost-first Cursor agent install must downshift designer"
grep_required '^model: gpt-5.6-luna-medium$' "$tmp/home-cursor-cost/.cursor/agents/planner.md" \
  "cost-first Cursor agent install must downshift planner"
grep_required '^model: gpt-5.6-terra-medium$' "$tmp/home-cursor-cost/.cursor/agents/plan-reviewer.md" \
  "cost-first Cursor agent install must downshift plan-reviewer"
grep_required '^model: claude-opus-4-8-thinking-high$' "$tmp/home-cursor-cost/.cursor/agents/reviewer.md" \
  "cost-first Cursor agent install must downshift reviewer"

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
for agent in "${CLAUDE_AGENTS[@]}"; do
  [[ -f "$tmp/home-claude/.claude/agents/$agent.md" ]] \
    || fail "Claude Code install must copy Claude agent $agent"
  [[ ! -L "$tmp/home-claude/.claude/agents/$agent.md" ]] \
    || fail "default Claude Code install must copy Claude agent $agent"
done
for agent in researcher explorer worker; do
  grep_required '^model: sonnet$' "$tmp/home-claude/.claude/agents/$agent.md" \
    "Claude install must render sonnet model for $agent"
  grep_required '^effort: medium$' "$tmp/home-claude/.claude/agents/$agent.md" \
    "Claude install must render medium effort for $agent"
done
grep_required '^model: haiku$' "$tmp/home-claude/.claude/agents/writer.md" \
  "Claude install must render haiku model for writer"
grep_required '^effort: medium$' "$tmp/home-claude/.claude/agents/writer.md" \
  "Claude install must render medium effort for writer"
for agent in debugger designer planner; do
  grep_required '^model: opus$' "$tmp/home-claude/.claude/agents/$agent.md" \
    "Claude install must render opus model for $agent"
  grep_required '^effort: high$' "$tmp/home-claude/.claude/agents/$agent.md" \
    "Claude install must render high effort for $agent"
done
for agent in plan-reviewer reviewer; do
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
for agent in researcher explorer worker; do
  grep_required '^model: haiku$' "$tmp/home-claude-cost/.claude/agents/$agent.md" \
    "cost-first Claude agent install must downshift $agent"
  grep_required '^effort: medium$' "$tmp/home-claude-cost/.claude/agents/$agent.md" \
    "cost-first Claude agent install must retain medium effort for $agent"
done
grep_required '^model: haiku$' "$tmp/home-claude-cost/.claude/agents/writer.md" \
  "cost-first Claude writer install must use haiku"
grep_required '^effort: medium$' "$tmp/home-claude-cost/.claude/agents/writer.md" \
  "cost-first Claude writer install must use medium effort"
for agent in debugger designer planner; do
  grep_required '^model: opus$' "$tmp/home-claude-cost/.claude/agents/$agent.md" \
    "cost-first Claude agent install must keep opus model for $agent"
  grep_required '^effort: high$' "$tmp/home-claude-cost/.claude/agents/$agent.md" \
    "cost-first Claude agent install must retain high effort for $agent"
done
for agent in plan-reviewer reviewer; do
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
check_skill_link "$tmp/home-claude-link/.claude/skills/teamwork-design" "teamwork-design" "Claude Code"

HOME="$tmp/home-claude-agents-link" "$ROOT/install.sh" --link claude-agents >/dev/null
for agent in "${CLAUDE_AGENTS[@]}"; do
  [[ -L "$tmp/home-claude-agents-link/.claude/agents/$agent.md" ]] \
    || fail "Claude agent link install must symlink $agent.md"
done

HOME="$tmp/home-invalid" "$ROOT/install.sh" gemini >/dev/null 2>&1 && fail "installer must reject unsupported targets"

HOME="$tmp/home-all" "$ROOT/install.sh" --link all >/dev/null
for skill in "${SKILLS[@]}"; do
  [[ -L "$tmp/home-all/.agents/skills/$skill" ]] || fail "all install must link Codex skill $skill"
  [[ -L "$tmp/home-all/.cursor/skills/$skill" ]] || fail "all install must link Cursor skill $skill"
  [[ -L "$tmp/home-all/.claude/skills/$skill" ]] || fail "all install must link Claude skill $skill"
done
check_skill_link "$tmp/home-all/.agents/skills/teamwork-design" "teamwork-design" "Codex all"
check_skill_link "$tmp/home-all/.cursor/skills/teamwork-design" "teamwork-design" "Cursor all"
check_skill_link "$tmp/home-all/.claude/skills/teamwork-design" "teamwork-design" "Claude Code all"
for agent in "${CODEX_AGENTS[@]}"; do
  [[ -L "$tmp/home-all/.codex/agents/$agent.toml" ]] || fail "all install must link Codex agent $agent"
done
for agent in "${CLAUDE_AGENTS[@]}"; do
  [[ -L "$tmp/home-all/.claude/agents/$agent.md" ]] || fail "all install must link Claude agent $agent"
done
for agent in "${CURSOR_AGENTS[@]}"; do
  [[ -L "$tmp/home-all/.cursor/agents/$agent.md" ]] || fail "all install must link Cursor agent $agent"
done
[[ -f "$tmp/home-all/.cursor/mcp.json" ]] \
  || fail "all install must write Cursor MCP config"
[[ ! -e "$tmp/home-all/.claude/skills/teamwork" ]] || fail "all install must remove retired teamwork skill"
grep_required '<!-- TEAMWORK_CLAUDE_GLOBAL_START -->' "$tmp/home-all/.claude/CLAUDE.md" \
  "all install must write Claude global policy"

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
grep_required '^docs/teamwork/discussion/$' "$init_root/.gitignore" \
  "init-project must ignore local discussion artifacts"
grep_required '^docs/teamwork/design/$' "$init_root/.gitignore" \
  "init-project must ignore local design artifacts"
[[ ! -e "$init_root/.cursor" ]] \
  || fail "default init-project must not create project .cursor surfaces"
for removed_ignore in '^\.agents/$' '^\.codex/$' '^\.cursor/$' '^\.claude/$'; do
  ! grep -Eq "$removed_ignore" "$init_root/.gitignore" \
    || fail "init-project must not add a project-local Teamwork package ignore: $removed_ignore"
done
python3 "$ROOT/scripts/validate_teamwork_index.py" "$init_root/docs/teamwork/index.json" >/dev/null
[[ -f "$init_root/docs/teamwork/current.md" ]] || fail "init-project must write current.md"
[[ ! -e "$init_root/docs/teamwork/discussion" ]] \
  || fail "init-project must not create an empty or fake discussion artifact directory"
discussion_file="$init_root/docs/teamwork/discussion/current.md"
mkdir -p "$(dirname "$discussion_file")"
printf '%s\n' \
  '# Saved Grill discussion' \
  '' \
  'This project-local file must survive init reruns without becoming an index anchor.' \
  > "$discussion_file"
init_snapshot="$tmp/init-project-snapshot"
mkdir -p "$init_snapshot"
cp "$init_root/docs/teamwork/index.json" "$init_snapshot/index.json"
cp "$init_root/docs/teamwork/current.md" "$init_snapshot/current.md"
cp "$init_root/docs/teamwork/README.md" "$init_snapshot/README.md"
cp "$discussion_file" "$init_snapshot/discussion-current.md"
for global_surface in \
  "$tmp/home-init-project/.agents" \
  "$tmp/home-init-project/.codex" \
  "$tmp/home-init-project/.cursor" \
  "$tmp/home-init-project/.claude"; do
  [[ ! -e "$global_surface" ]] \
    || fail "init-project must remain project-local and not create $global_surface"
done
for removed_local_surface in \
  "$init_root/.agents" \
  "$init_root/.codex/agents" \
  "$init_root/.cursor/skills" \
  "$init_root/.cursor/agents" \
  "$init_root/.claude/skills" \
  "$init_root/.claude/agents"; do
  [[ ! -e "$removed_local_surface" ]] \
    || fail "init-project must not create project-local Teamwork package surface $removed_local_surface"
done
init_mcp_root="$tmp/init-project-cursor-mcp"
mkdir -p "$init_mcp_root"
printf '# Init MCP Smoke\n' > "$init_mcp_root/README.md"
HOME="$tmp/home-init-project-cursor-mcp" \
  TEAMWORK_INIT_CODEGRAPH=0 \
  "$ROOT/install.sh" --copy --project-root "$init_mcp_root" --cursor-mcp init-project >/dev/null
[[ -f "$init_mcp_root/.cursor/rules/codegraph.mdc" ]] \
  || fail "init-project --cursor-mcp must write codegraph Cursor rule"
[[ -f "$init_mcp_root/.cursor/rules/gpu-broker.mdc" ]] \
  || fail "init-project --cursor-mcp must write gpu-broker Cursor rule"
[[ -f "$init_mcp_root/.cursor/mcp.json" ]] \
  || fail "init-project --cursor-mcp must write project .cursor/mcp.json"
python3 - "$init_mcp_root/.cursor/mcp.json" <<'PY'
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
servers = payload.get("mcpServers", {})
for name in ("codegraph", "gpu-broker"):
    if name not in servers:
        raise SystemExit(f"project init MCP config missing {name}")
PY
HOME="$tmp/home-init-project" \
  TEAMWORK_INIT_CODEGRAPH=0 \
  "$ROOT/install.sh" --project-root "$init_root" init-project >/dev/null
cmp -s "$init_snapshot/index.json" "$init_root/docs/teamwork/index.json" \
  || fail "init-project rerun must preserve the existing index"
cmp -s "$init_snapshot/current.md" "$init_root/docs/teamwork/current.md" \
  || fail "init-project rerun must preserve existing current.md"
cmp -s "$init_snapshot/README.md" "$init_root/docs/teamwork/README.md" \
  || fail "init-project rerun must preserve the existing runtime README"
cmp -s "$init_snapshot/discussion-current.md" "$discussion_file" \
  || fail "init-project rerun must preserve Grill's direct discussion file"
python3 "$ROOT/scripts/validate_teamwork_index.py" "$init_root/docs/teamwork/index.json" >/dev/null
for anchor in "$init_root/docs/teamwork/index.json" "$init_root/docs/teamwork/current.md" "$init_root/docs/teamwork/README.md"; do
  ! grep -q 'docs/teamwork/discussion' "$anchor" \
    || fail "ordinary Teamwork memory must not duplicate Grill's discussion pointer: $anchor"
done

global_isolation_root="$tmp/init-project-isolated"
global_isolation_home="$tmp/home-init-project-isolated"
mkdir -p "$global_isolation_root" "$global_isolation_home/.codex"
printf '# Global Isolation Init Smoke\n' > "$global_isolation_root/README.md"
printf '%s\n' '[broken' 'value = [' > "$global_isolation_home/.codex/config.toml"
cp "$global_isolation_home/.codex/config.toml" "$tmp/global-config-before.toml"
global_isolation_output="$(
  HOME="$global_isolation_home" \
    TEAMWORK_INIT_CODEGRAPH=0 \
    "$ROOT/scripts/init-project.sh" --project-root "$global_isolation_root" 2>&1
)" || fail "project-local init must ignore malformed global Codex configuration"
cmp -s "$tmp/global-config-before.toml" "$global_isolation_home/.codex/config.toml" \
  || fail "project-local init must not modify global Codex configuration"
[[ -f "$global_isolation_root/docs/teamwork/index.json" ]] \
  || fail "project-local init must create project memory independently of global state"
grep_required '<!-- TEAMWORK_PROJECT_START -->' "$global_isolation_root/AGENTS.md" \
  "project-local init must write project instructions independently of global state"
! printf '%s\n' "$global_isolation_output" | grep -Eq 'global (skills|agents|Codex|installation)' \
  || fail "project-local init must not report or inspect global installation state"
[[ ! -e "$global_isolation_home/.fake-codex-invocations" ]] \
  || fail "project-local init must not invoke Codex to manage interaction capability"

invalid_root="$tmp/init-project-invalid-index"
mkdir -p "$invalid_root/docs/teamwork"
printf '# Invalid Index Smoke\n' > "$invalid_root/README.md"
printf '{"bad": true}\n' > "$invalid_root/docs/teamwork/index.json"
invalid_index_snapshot="$tmp/invalid-index-before.json"
cp "$invalid_root/docs/teamwork/index.json" "$invalid_index_snapshot"
invalid_rc=0
invalid_output="$(
  HOME="$tmp/home-init-project-invalid" \
    TEAMWORK_INIT_CODEGRAPH=0 \
    TEAMWORK_INIT_CURSOR_POLICY_COPY=0 \
    "$ROOT/scripts/init-project.sh" --project-root "$invalid_root" 2>&1
)" || invalid_rc=$?
[[ "$invalid_rc" -ne 0 ]] \
  || fail "init-project must fail closed on an invalid existing Teamwork memory index"
printf '%s\n' "$invalid_output" | grep -q 'Teamwork project init refused' \
  || fail "init-project must explain why invalid existing Teamwork memory was refused"
cmp -s "$invalid_index_snapshot" "$invalid_root/docs/teamwork/index.json" \
  || fail "invalid existing Teamwork memory must remain byte-for-byte unchanged"
[[ ! -e "$invalid_root/AGENTS.md" && ! -e "$invalid_root/.gitignore" ]] \
  || fail "invalid existing Teamwork memory must fail before project output writes"
[[ ! -e "$tmp/home-init-project-invalid" ]] \
  || fail "invalid existing Teamwork memory must fail before global install writes"
[[ ! -e "$tmp/home-init-project-invalid/.fake-codex-invocations" ]] \
  || fail "init-project must not invoke the host Codex CLI to manage interaction capabilities"
HOME="$tmp/home-agents" "$ROOT/install.sh" --link claude-agents >/dev/null
for agent in "${CLAUDE_AGENTS[@]}"; do
  [[ -L "$tmp/home-agents/.claude/agents/$agent.md" ]] \
    || fail "claude-agents install must link $agent.md"
done

HOME="$tmp/home-cursor-agents-link" "$ROOT/install.sh" --link cursor-agents >/dev/null
for agent in "${CURSOR_AGENTS[@]}"; do
  [[ -L "$tmp/home-cursor-agents-link/.cursor/agents/$agent.md" ]] \
    || fail "cursor-agents link install must symlink $agent.md"
done

# --- Codex Marketplace cache and plugin bootstrap ---
if [[ -z "$REAL_CODEX" ]]; then
  [[ "${TEAMWORK_REQUIRE_MARKETPLACE_SMOKE:-0}" != "1" ]] \
    || fail "real Codex CLI is required for the Marketplace smoke"
  echo "SKIP: Codex Marketplace smoke (codex CLI unavailable)"
else
  marketplace_home="$tmp/home-marketplace"
  marketplace_codex_home="$tmp/codex-marketplace"
  # The real Codex CLI may materialize a local Marketplace source while it
  # installs it.  Exercise that behavior through an isolated copy so the
  # smoke test proves cache execution without ever mutating this checkout.
  marketplace_source="$tmp/marketplace-source"
  mkdir -p "$marketplace_home" "$marketplace_codex_home" \
    "$marketplace_source/.agents/plugins" "$marketplace_source/plugins"
  cp "$ROOT/.agents/plugins/marketplace.json" \
    "$marketplace_source/.agents/plugins/marketplace.json"
  cp -R "$ROOT/plugins/teamwork-skill" "$marketplace_source/plugins/teamwork-skill"
  HOME="$marketplace_home" CODEX_HOME="$marketplace_codex_home" \
    "$REAL_CODEX" plugin marketplace add "$marketplace_source" --json > "$tmp/marketplace-add.json"
  HOME="$marketplace_home" CODEX_HOME="$marketplace_codex_home" \
    "$REAL_CODEX" plugin add teamwork-skill@teamwork --json > "$tmp/plugin-add.json"
  [[ -d "$ROOT/plugins/teamwork-skill" ]] \
    || fail "Marketplace smoke must not mutate the release plugin bundle"
  cache_root="$marketplace_codex_home/plugins/cache/teamwork/teamwork-skill/$(tr -d '[:space:]' < "$ROOT/VERSION")"
  [[ -d "$cache_root" ]] || fail "Marketplace install must cache teamwork-skill by VERSION"
  [[ -f "$cache_root/.teamwork-plugin-runtime" ]] \
    || fail "Marketplace cache must preserve Teamwork runtime marker"
  [[ -f "$cache_root/scripts/plugin-activation.py" ]] \
    || fail "Marketplace cache must preserve plugin activation runtime"
  [[ ! -e "$cache_root/hooks/hooks.json" ]] \
    || fail "Marketplace cache must not expose plugin-bundled hooks"
  for skill in "${SKILLS[@]}"; do
    [[ -f "$cache_root/skills/$skill/SKILL.md" ]] \
      || fail "Marketplace cache must contain Teamwork skill $skill"
  done

  HOME="$marketplace_home" CODEX_HOME="$marketplace_codex_home" \
    "$cache_root/install.sh" plugin-codex-bootstrap >/dev/null
  [[ -f "$marketplace_codex_home/teamwork/plugin-activation.json" ]] \
    || fail "plugin bootstrap must write activation marker last"
  [[ -f "$marketplace_codex_home/teamwork/notify.py" ]] \
    || fail "plugin bootstrap must install stable Codex notifier"
  [[ "$(python3 "$cache_root/scripts/configure-notifications.py" status \
    --config "$marketplace_codex_home/hooks.json" \
    --notifier "$marketplace_codex_home/teamwork/notify.py")" == "installed" ]] \
    || fail "plugin bootstrap must configure Codex notifications by default"
  [[ ! -e "$marketplace_home/.agents/skills" ]] \
    || fail "plugin bootstrap must not create a user skill copy"
  for agent in "${CODEX_AGENTS[@]}"; do
    [[ -f "$marketplace_codex_home/agents/$agent.toml" ]] \
      || fail "plugin bootstrap must install Codex agent $agent"
  done
  grep_required '<!-- TEAMWORK_CODEX_GLOBAL_START -->' "$marketplace_codex_home/AGENTS.md" \
    "plugin bootstrap must install the Codex global policy"
  HOME="$marketplace_home" CODEX_HOME="$marketplace_codex_home" \
    "$cache_root/scripts/plugin-runtime-root.py" > "$tmp/plugin-runtime-root.out"
  [[ "$(cat "$tmp/plugin-runtime-root.out")" == "$(cd "$cache_root" && pwd -P)" ]] \
    || fail "plugin runtime locator must resolve the cache root"

  # A repeated bootstrap may render a different supported profile and remove
  # notifications without creating duplicate skills or hooks.
  HOME="$marketplace_home" CODEX_HOME="$marketplace_codex_home" \
    "$cache_root/install.sh" --profile cost-first --no-notifications plugin-codex-bootstrap >/dev/null
  grep_required '^model = "gpt-5.5"$' "$marketplace_codex_home/agents/teamwork-explorer.toml" \
    "plugin bootstrap must render the requested Codex profile"
  [[ ! -e "$marketplace_codex_home/teamwork/notify.py" ]] \
    || fail "plugin bootstrap --no-notifications must remove only its stable notifier"
  grep_required '"profile": "cost-first"' "$marketplace_codex_home/teamwork/plugin-activation.json" \
    "activation marker must record the selected profile"
  real_codex_dir="$(dirname "$REAL_CODEX")"
  PATH="$real_codex_dir:$PATH" HOME="$marketplace_home" CODEX_HOME="$marketplace_codex_home" \
    "$cache_root/scripts/check-update.sh" --plugin --readiness --no-fetch > "$tmp/plugin-readiness.out"
  grep_required '^MANAGED_INSTALL_READY=yes$' "$tmp/plugin-readiness.out" \
    "plugin readiness must verify the cached full Codex setup"
  grep_required '^PLUGIN_CATALOG=enabled$' "$tmp/plugin-readiness.out" \
    "plugin readiness must inspect codex plugin list JSON"
  grep_required '^PLUGIN_CACHE=current' "$tmp/plugin-readiness.out" \
    "plugin readiness must inspect cache version"
  grep_required '^CODEX_LEGACY_SKILLS=clear$' "$tmp/plugin-readiness.out" \
    "plugin readiness must reject duplicate legacy skills"

  # Simulate a Marketplace update waiting for the next task; bootstrap refreshes
  # the stale activation marker from the cache without copying skills.
  "$cache_root/scripts/plugin-activation.py" write \
    --path "$marketplace_codex_home/teamwork/plugin-activation.json" \
    --version 0.0.0 --profile cost-first --notifications disabled >/dev/null
  HOME="$marketplace_home" CODEX_HOME="$marketplace_codex_home" \
    "$cache_root/install.sh" --profile cost-first --no-notifications plugin-codex-bootstrap >/dev/null
  grep_required '"version": "'"$(tr -d '[:space:]' < "$ROOT/VERSION")"'"' \
    "$marketplace_codex_home/teamwork/plugin-activation.json" \
    "new-task plugin refresh must update a stale activation marker"
  if HOME="$marketplace_home" CODEX_HOME="$marketplace_codex_home" "$ROOT/install.sh" codex >/dev/null 2>&1; then
    fail "legacy Codex installer must stop when plugin activation is present"
  fi
  [[ ! -e "$marketplace_home/.agents/skills" ]] \
    || fail "legacy installer stop must not create duplicate skills"

  plugin_project="$tmp/plugin-init-project"
  mkdir -p "$plugin_project"
  printf '# Plugin Init Smoke\n' > "$plugin_project/README.md"
  plugin_project="$(cd "$plugin_project" && pwd -P)"
  HOME="$marketplace_home" CODEX_HOME="$marketplace_codex_home" \
    TEAMWORK_INIT_CODEGRAPH=0 TEAMWORK_INIT_CURSOR_POLICY_COPY=0 \
    "$cache_root/install.sh" --no-notifications --project-root "$plugin_project" plugin-init-project >/dev/null
  [[ -f "$plugin_project/docs/teamwork/index.json" ]] \
    || fail "plugin-init-project must create Teamwork project context"
  [[ ! -e "$marketplace_home/.cursor" && ! -e "$marketplace_home/.claude" ]] \
    || fail "plugin-init-project must not install non-Codex platform surfaces"

  unknown_plugin_home="$tmp/home-plugin-unknown-legacy"
  unknown_plugin_codex_home="$tmp/codex-plugin-unknown-legacy"
  mkdir -p "$unknown_plugin_home/.agents/skills/teamwork-update" "$unknown_plugin_codex_home"
  printf '%s\n' 'unowned content' > "$unknown_plugin_home/.agents/skills/teamwork-update/SKILL.md"
  if HOME="$unknown_plugin_home" CODEX_HOME="$unknown_plugin_codex_home" \
    "$cache_root/install.sh" --no-notifications plugin-codex-bootstrap >/dev/null 2>&1; then
    fail "plugin bootstrap must reject unknown same-name legacy skill content"
  fi
  [[ ! -e "$unknown_plugin_codex_home/config.toml" \
    && ! -e "$unknown_plugin_codex_home/teamwork/plugin-activation.json" ]] \
    || fail "unknown legacy skill protection must fail before Codex configuration writes"

  failed_plugin_home="$tmp/home-plugin-invalid-notifications"
  failed_plugin_codex_home="$tmp/codex-plugin-invalid-notifications"
  mkdir -p "$failed_plugin_home" "$failed_plugin_codex_home"
  printf '%s\n' '{broken-json' > "$failed_plugin_codex_home/hooks.json"
  if HOME="$failed_plugin_home" CODEX_HOME="$failed_plugin_codex_home" \
    "$cache_root/install.sh" plugin-codex-bootstrap >/dev/null 2>&1; then
    fail "plugin bootstrap must reject invalid notification config before mutation"
  fi
  [[ ! -e "$failed_plugin_codex_home/config.toml" \
    && ! -e "$failed_plugin_codex_home/agents" \
    && ! -e "$failed_plugin_codex_home/AGENTS.md" \
    && ! -e "$failed_plugin_codex_home/teamwork/plugin-activation.json" ]] \
    || fail "failed plugin bootstrap must not rewrite Codex managed configuration"

  migrated_plugin_home="$tmp/home-plugin-migration"
  migrated_plugin_codex_home="$tmp/codex-plugin-migration"
  mkdir -p "$migrated_plugin_home/.agents/skills" "$migrated_plugin_codex_home"
  for skill in "${SKILLS[@]}"; do
    cp -R "$cache_root/skills/$skill" "$migrated_plugin_home/.agents/skills/$skill"
  done
  printf '%s\n' "$(tr -d '[:space:]' < "$ROOT/VERSION")" > "$migrated_plugin_home/.agents/skills/.teamwork-version"
  printf '%s\n' performance-first > "$migrated_plugin_home/.agents/skills/.teamwork-profile"
  printf '%s\n' 'preserve unrelated content' > "$migrated_plugin_home/.agents/skills/unrelated.txt"
  HOME="$migrated_plugin_home" CODEX_HOME="$migrated_plugin_codex_home" \
    "$cache_root/install.sh" --no-notifications plugin-codex-bootstrap >/dev/null
  for skill in "${SKILLS[@]}"; do
    [[ ! -e "$migrated_plugin_home/.agents/skills/$skill" ]] \
      || fail "plugin migration must remove verified legacy skill $skill"
  done
  [[ -f "$migrated_plugin_home/.agents/skills/unrelated.txt" ]] \
    || fail "plugin migration must preserve unrelated user skill-root content"
  [[ ! -e "$migrated_plugin_home/.agents/skills/.teamwork-version" ]] \
    || fail "plugin migration must remove its ownership marker"
fi
