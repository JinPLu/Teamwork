#!/usr/bin/env bash

# --- Lean role templates ---
while IFS= read -r template; do
  ! grep -q 'grill/question-first' "$template" \
    || fail "agent template must not duplicate the grill procedure: ${template#"$ROOT/"}"
  word_count_max "$template" 260 "agent template should remain lean: ${template#"$ROOT/"}"
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
    "explorer": [
        root / "templates/codex-agents/teamwork-explorer.toml",
        root / "templates/cursor-agents/explore.md",
        root / "templates/claude-agents/explore.md",
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
    "reviewer": [
        root / "templates/codex-agents/teamwork-reviewer.toml",
        root / "templates/cursor-agents/code-reviewer.md",
        root / "templates/claude-agents/code-reviewer.md",
    ],
    "deep-reviewer": [
        root / "templates/codex-agents/teamwork-deep-reviewer.toml",
        root / "templates/cursor-agents/deep-reviewer.md",
        root / "templates/claude-agents/deep-reviewer.md",
    ],
}
required = {
    "explorer": ("tools proportional", "full source census"),
    "designer": ("inspect relevant material within the delegated scope", "genuine alternatives"),
    "worker": ("bounded evidence sufficient to classify", "route unknown causes to diagnosis"),
    "reviewer": ("stable id", "blocker", "follow-up", "suggestion", "prior fixes", "regression risk proportional", "fresh review"),
    "deep-reviewer": ("stable id", "blocker", "follow-up", "suggestion", "prior fixes", "proportional regression risk", "fresh review"),
}
for role, paths in roles.items():
    for path in paths:
        text = " ".join(path.read_text(encoding="utf-8").split()).lower()
        for phrase in required[role]:
            if phrase not in text:
                raise SystemExit(f"FAIL: {role} parity missing {phrase!r}: {path}")
PY
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
  "$ROOT/skills" "$ROOT/templates" "$ROOT/install.sh" "$ROOT/scripts/install"
grep_absent 'teamwork-quality' "Teamwork must not add a separate quality stage" "$ROOT/skills" "$ROOT/CODEX.md" "$ROOT/CURSOR.md" "$ROOT/CLAUDE.md" "$ROOT/install.sh" "$ROOT/scripts/install"
grep_absent 'teamwork-deslop' "Teamwork must not add a separate deslop stage" "$ROOT/skills" "$ROOT/CODEX.md" "$ROOT/CURSOR.md" "$ROOT/CLAUDE.md" "$ROOT/install.sh" "$ROOT/scripts/install"
[[ -f "$ROOT/skills/grill-me/SKILL.md" ]] || fail "question-first override must have one public grill-me skill"
[[ ! -e "$ROOT/skills/teamwork-grill" ]] || fail "question-first override must not become a peer teamwork-grill skill"
grep_absent 'teamwork-grill)' "install skill list must not add a peer teamwork-grill skill" "$ROOT/install.sh" "$ROOT/scripts/install"

grep_required 'check-update.md' "$ROOT/skills/teamwork-init/SKILL.md" "teamwork-init must reference check-update"
grep_required 'check-update.md' "$ROOT/skills/teamwork-update/SKILL.md" "teamwork-update must reference check-update"
grep_required 'check-update.sh' "$ROOT/skills/teamwork-update/SKILL.md" "teamwork-update must reference check-update script"
[[ -x "$ROOT/scripts/check-update.sh" ]] || fail "check-update script must be executable"
grep_required 'skills_content_status' "$ROOT/scripts/check-update.sh" "check-update must detect installed skill drift"
grep_required 'agents_content_status' "$ROOT/scripts/check-update.sh" "check-update must detect installed agent drift"
grep_required 'review-required' "$ROOT/scripts/check-update.sh" "check-update must surface untrusted Codex notification hooks"
grep_required 'run /hooks' "$ROOT/scripts/install/targets.sh" "notification install must preserve the Codex hook trust boundary"
grep_required 'all|init-project' "$ROOT/install.sh" "full installs must enable Teamwork notifications by default"
grep_required 'trust-all' "$ROOT/skills/teamwork-init/SKILL.md" "teamwork-init must trust only exact Teamwork hooks"
grep_required 'trust-all' "$ROOT/skills/teamwork-update/SKILL.md" "teamwork-update must trust only exact Teamwork hooks"

if git -C "$ROOT" grep -n -E 'raoctl|RAO|Stop hook|/rao:|/teamwork:' \
  -- ':!scripts/validate.sh' ':!scripts/validation/**' >/tmp/teamwork-retired-grep.$$; then
  cat /tmp/teamwork-retired-grep.$$ >&2
  rm -f /tmp/teamwork-retired-grep.$$
  fail "retired multi-runtime references remain outside validation"
fi
rm -f /tmp/teamwork-retired-grep.$$

tmp="$(cd "$(mktemp -d)" && pwd -P)"
discussion_transaction_source="$ROOT/skills/using-teamwork/scripts/discussion-transaction.py"

check_discussion_transaction_copy() {
  local installed="$1"
  local platform="$2"
  [[ -f "$installed" ]] || fail "$platform install must copy discussion-transaction.py"
  [[ ! -L "$installed" ]] || fail "$platform default install must copy discussion-transaction.py"
  [[ -x "$installed" ]] || fail "$platform installed discussion-transaction.py must be executable"
  cmp -s "$discussion_transaction_source" "$installed" \
    || fail "$platform installed discussion-transaction.py must match source byte-for-byte"
}

check_using_teamwork_link() {
  local installed="$1"
  local platform="$2"
  [[ -L "$installed" ]] || fail "$platform link install must symlink the using-teamwork skill directory"
  [[ "$(cd "$installed" && pwd -P)" == "$(cd "$ROOT/skills/using-teamwork" && pwd -P)" ]] \
    || fail "$platform using-teamwork skill link must resolve to source"
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
codex_discussion_transaction="$tmp/home/.codex/skills/using-teamwork/scripts/discussion-transaction.py"
check_discussion_transaction_copy \
  "$codex_discussion_transaction" \
  "Codex"
discussion_inspect_empty="$tmp/discussion-inspect-empty"
mkdir -p "$discussion_inspect_empty"
discussion_inspect_output="$(
  "$codex_discussion_transaction" inspect --project-root "$discussion_inspect_empty"
)"
python3 - "$discussion_inspect_output" <<'PY'
import json
import sys

result = json.loads(sys.argv[1])
if result.get("initialized") is not False or result.get("active", object()) is not None:
    raise SystemExit("FAIL: installed helper must report an empty safe project as uninitialized")
if "revision" in result:
    raise SystemExit("FAIL: an uninitialized project must not expose a discussion revision")
PY

discussion_inspect_partial="$tmp/discussion-inspect-partial"
mkdir -p "$discussion_inspect_partial/docs/teamwork"
printf '{}\n' > "$discussion_inspect_partial/docs/teamwork/index.json"
if "$codex_discussion_transaction" inspect \
  --project-root "$discussion_inspect_partial" >/dev/null 2>&1; then
  fail "installed helper must fail closed on partially initialized Teamwork memory"
fi

discussion_inspect_unsafe="$tmp/discussion-inspect-unsafe"
mkdir -p "$discussion_inspect_unsafe" "$tmp/discussion-inspect-unsafe-target"
ln -s "$tmp/discussion-inspect-unsafe-target" "$discussion_inspect_unsafe/docs"
if "$codex_discussion_transaction" inspect \
  --project-root "$discussion_inspect_unsafe" >/dev/null 2>&1; then
  fail "installed helper must fail closed on an unsafe Teamwork memory node"
fi
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
HOME="$tmp/home-project-update" "$ROOT/scripts/check-update.sh" --readiness --no-fetch > "$tmp/global-routing-stale.out" || true
grep_required '^INSTALL_READY=no$' "$tmp/global-routing-stale.out" \
  "check-update readiness must fail on stale Codex routing"
grep_required 'codex-routing' "$tmp/global-routing-stale.out" \
  "check-update readiness must identify stale Codex routing"
HOME="$tmp/home-project-update" "$ROOT/install.sh" all >/dev/null
HOME="$tmp/home-project-update" "$ROOT/scripts/check-update.sh" --readiness --no-fetch > "$tmp/global-routing-ready.out"
grep_required '^CODEX_ROUTING=ready$' "$tmp/global-routing-ready.out" \
  "user refresh must repair Codex routing readiness"
printf '\n# stale grill-me skill fixture\n' >> "$tmp/home-project-update/.codex/skills/grill-me/SKILL.md"
HOME="$tmp/home-project-update" "$ROOT/scripts/check-update.sh" --readiness --no-fetch > "$tmp/global-grill-skill-stale.out" || true
grep_required '^INSTALL_READY=no$' "$tmp/global-grill-skill-stale.out" \
  "check-update readiness must fail when installed grill-me content drifts"
grep_required 'codex-skill-content' "$tmp/global-grill-skill-stale.out" \
  "check-update readiness must identify global Codex skill content drift"
HOME="$tmp/home-project-update" "$ROOT/install.sh" all >/dev/null
rm "$tmp/home-project-update/.codex/skills/grill-me/SKILL.md"
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
grep_required 'drift(missing=0,changed=1)' "$tmp/global-agent-stale-report.out" \
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
check_using_teamwork_link "$tmp/home-link/.codex/skills/using-teamwork" "Codex"

HOME="$tmp/home-cursor" "$ROOT/install.sh" cursor >/dev/null
for skill in "${SKILLS[@]}"; do
  [[ -f "$tmp/home-cursor/.cursor/skills/$skill/SKILL.md" ]] || fail "Cursor install missing $skill"
  [[ ! -L "$tmp/home-cursor/.cursor/skills/$skill/SKILL.md" ]] || fail "default Cursor install must copy $skill"
done
check_discussion_transaction_copy \
  "$tmp/home-cursor/.cursor/skills/using-teamwork/scripts/discussion-transaction.py" \
  "Cursor"
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
check_discussion_transaction_copy \
  "$tmp/home-claude/.claude/skills/using-teamwork/scripts/discussion-transaction.py" \
  "Claude Code"
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
check_using_teamwork_link "$tmp/home-claude-link/.claude/skills/using-teamwork" "Claude Code"

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
check_using_teamwork_link "$tmp/home-all/.codex/skills/using-teamwork" "Codex all"
check_using_teamwork_link "$tmp/home-all/.cursor/skills/using-teamwork" "Cursor all"
check_using_teamwork_link "$tmp/home-all/.claude/skills/using-teamwork" "Claude Code all"
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
for removed_ignore in '^\.agents/$' '^\.codex/$' '^\.cursor/$' '^\.claude/$'; do
  ! grep -Eq "$removed_ignore" "$init_root/.gitignore" \
    || fail "init-project must not add a project-local Teamwork package ignore: $removed_ignore"
done
python3 "$ROOT/scripts/validate_teamwork_index.py" "$init_root/docs/teamwork/index.json" >/dev/null
[[ -f "$init_root/docs/teamwork/current.md" ]] || fail "init-project must write current.md"
[[ ! -e "$init_root/docs/teamwork/discussion" ]] \
  || fail "init-project must not create an empty or fake discussion artifact directory"
python3 - "$init_root/docs/teamwork/index.json" "$init_root/docs/teamwork/discussion/$(date +%F)-preserved-discussion.md" <<'PY'
import json
import pathlib
import sys

index_path = pathlib.Path(sys.argv[1])
artifact_path = pathlib.Path(sys.argv[2])
artifact_path.parent.mkdir(parents=True, exist_ok=True)
index = json.loads(index_path.read_text(encoding="utf-8"))
project_root = index_path.parents[2]
relative_artifact = artifact_path.relative_to(project_root).as_posix()
index["active"]["discussion"] = relative_artifact
index["entries"].append({
    "topic": "preserved-discussion",
    "kind": "discussion",
    "title": "Preserved discussion",
    "status": "active",
    "currentness": "current",
    "authority": "supporting",
    "path": relative_artifact,
    "updated": index["last_updated"],
    "summary": "Existing discussion pointer preserved across init reruns.",
})
index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
current_path = index_path.parent / "current.md"
current = current_path.read_text(encoding="utf-8")
current = current.replace(
    "- Active discussion: none.",
    f"- Active discussion: {relative_artifact}.",
)
if relative_artifact not in current:
    raise SystemExit("FAIL: initialized current.md did not expose the discussion anchor")
current_path.write_text(current, encoding="utf-8")

readme_path = index_path.parent / "README.md"
readme = readme_path.read_text(encoding="utf-8")
readme = readme.replace(
    "- Active discussion route: none",
    f"- Active discussion route: {relative_artifact}",
)
if relative_artifact not in readme:
    raise SystemExit("FAIL: initialized runtime README did not expose the discussion anchor")
readme_path.write_text(readme, encoding="utf-8")

artifact_path.write_text(f"""Artifact Type: discussion
Status: active
Authority: supporting
Last Updated: {index["last_updated"]}
Search Keys: preserved discussion, init rerun
Abstract: Preserve the active supporting route across project initialization.
Linked Artifacts: none
Superseded By: none

# Preserve the discussion route across initialization

## Goal

Preserve a material decision route across an initialization rerun so later work
does not lose continuity.

## Settled

- Retain the existing supporting route; recreating it from a raw transcript was
  rejected because the saved artifact already carries the needed context.

## Still open

- Whether later evidence changes the active route.

## Key evidence

- The active pointer and both runtime anchors identify the same artifact,
  establishing the route that the rerun must preserve.

## Continue here

Continue from the next decision-relevant evidence and update the artifact only
if that evidence changes the route.
""", encoding="utf-8")
PY
cp "$init_root/docs/teamwork/index.json" "$index_pointer_tmp/init-index-before-rerun.json"
cp "$init_root/docs/teamwork/current.md" "$index_pointer_tmp/init-current-before-rerun.md"
cp "$init_root/docs/teamwork/README.md" "$index_pointer_tmp/init-readme-before-rerun.md"
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
HOME="$tmp/home-init-project" \
  TEAMWORK_INIT_CODEGRAPH=0 \
  TEAMWORK_INIT_CURSOR_POLICY_COPY=0 \
  "$ROOT/install.sh" --copy --no-notifications --project-root "$init_root" init-project >/dev/null
cmp -s "$index_pointer_tmp/init-index-before-rerun.json" "$init_root/docs/teamwork/index.json" \
  || fail "init-project rerun must preserve the existing index and active discussion pointer"
cmp -s "$index_pointer_tmp/init-current-before-rerun.md" "$init_root/docs/teamwork/current.md" \
  || fail "init-project rerun must preserve existing current.md"
cmp -s "$index_pointer_tmp/init-readme-before-rerun.md" "$init_root/docs/teamwork/README.md" \
  || fail "init-project rerun must preserve the existing runtime README"
python3 "$ROOT/scripts/validate_teamwork_index.py" "$init_root/docs/teamwork/index.json" >/dev/null
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
printf '%s\n' "$global_failure_output" | grep -q 'continuing with project context setup' \
  || fail "init-project must explain that project context setup continues after global failure"
[[ -f "$global_failure_root/docs/teamwork/index.json" ]] \
  || fail "global config failure must not prevent project memory"
grep_required '<!-- TEAMWORK_PROJECT_START -->' "$global_failure_root/AGENTS.md" \
  "global config failure must not prevent project instructions"
for removed_local_surface in \
  "$global_failure_root/.agents" \
  "$global_failure_root/.codex/agents" \
  "$global_failure_root/.cursor/skills" \
  "$global_failure_root/.claude/skills"; do
  [[ ! -e "$removed_local_surface" ]] \
    || fail "global-failure init must not create project-local package surface $removed_local_surface"
done
[[ ! -e "$global_failure_home/.fake-codex-invocations" ]] \
  || fail "failed global init must not invoke Codex to manage interaction capability"

invalid_root="$tmp/init-project-invalid-index"
mkdir -p "$invalid_root/docs/teamwork"
printf '# Invalid Index Smoke\n' > "$invalid_root/README.md"
printf '{"bad": true}\n' > "$invalid_root/docs/teamwork/index.json"
cp "$invalid_root/docs/teamwork/index.json" "$index_pointer_tmp/invalid-index-before.json"
invalid_rc=0
invalid_output="$(
  HOME="$tmp/home-init-project-invalid" \
    TEAMWORK_INIT_CODEGRAPH=0 \
    TEAMWORK_INIT_CURSOR_POLICY_COPY=0 \
    "$ROOT/scripts/init-project.sh" --project-root "$invalid_root" --copy 2>&1
)" || invalid_rc=$?
[[ "$invalid_rc" -ne 0 ]] \
  || fail "init-project must fail closed on an invalid existing Teamwork memory index"
printf '%s\n' "$invalid_output" | grep -q 'Teamwork project init refused' \
  || fail "init-project must explain why invalid existing Teamwork memory was refused"
cmp -s "$index_pointer_tmp/invalid-index-before.json" "$invalid_root/docs/teamwork/index.json" \
  || fail "invalid existing Teamwork memory must remain byte-for-byte unchanged"
[[ ! -e "$invalid_root/AGENTS.md" && ! -e "$invalid_root/.gitignore" ]] \
  || fail "invalid existing Teamwork memory must fail before project output writes"
[[ ! -e "$tmp/home-init-project-invalid" ]] \
  || fail "invalid existing Teamwork memory must fail before global install writes"
[[ ! -e "$tmp/home-init-project-invalid/.fake-codex-invocations" ]] \
  || fail "init-project must not invoke the host Codex CLI to manage interaction capabilities"
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
