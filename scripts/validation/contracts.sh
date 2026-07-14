#!/usr/bin/env bash

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
current_version="$(tr -d '[:space:]' < "$ROOT/VERSION")"
grep_required "## $current_version -" "$ROOT/CHANGELOG.md" "CHANGELOG must document current VERSION"
current_changelog_cn="$(awk -v prefix="## $current_version -" '
  /^## / { if (capture) exit; capture = index($0, prefix) == 1 }
  capture { print }
' "$ROOT/CHANGELOG.md")"
[[ "$current_changelog_cn" == *"升级方式："* || "$current_changelog_cn" == *"无需操作"* ]] \
  || fail "current Chinese changelog must state the user action or that no action is needed"
grep_required '^# Changelog' "$ROOT/CHANGELOG.en.md" "English CHANGELOG must have a top-level heading"
grep_required '\[中文\](CHANGELOG.md)' "$ROOT/CHANGELOG.en.md" "English CHANGELOG must link to default Chinese CHANGELOG"
grep_required "## $current_version -" "$ROOT/CHANGELOG.en.md" "English CHANGELOG must document current VERSION"
current_changelog_en="$(awk -v prefix="## $current_version -" '
  /^## / { if (capture) exit; capture = index($0, prefix) == 1 }
  capture { print }
' "$ROOT/CHANGELOG.en.md")"
[[ "$current_changelog_en" == *"To upgrade:"* || "$current_changelog_en" == *"No action is required"* ]] \
  || fail "current English changelog must state the user action or that no action is needed"
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
grep_required 'write_teamwork_codex_global_policy()' "$ROOT/scripts/install/policy.sh" "installer must define Teamwork Codex global policy writer"
grep_required 'write_teamwork_claude_global_policy()' "$ROOT/scripts/install/policy.sh" "installer must define Teamwork Claude global policy writer"
grep_required 'write_teamwork_cursor_global_policy()' "$ROOT/scripts/install/policy.sh" "installer must define Teamwork Cursor global policy writer"
grep_required '<!-- TEAMWORK_CODEX_GLOBAL_START -->' "$ROOT/scripts/install/policy.sh" "installer global policy writer must include managed start marker"
grep_required '<!-- TEAMWORK_CLAUDE_GLOBAL_START -->' "$ROOT/scripts/install/policy.sh" "installer Claude global policy writer must include managed start marker"
grep_required '<!-- TEAMWORK_CURSOR_GLOBAL_START -->' "$ROOT/scripts/install/policy.sh" "installer Cursor global policy writer must include managed start marker"
grep_required 'install_codex_global_policy' "$ROOT/scripts/install/targets.sh" "installer must call Codex global policy install from Codex target"
grep_required 'install_claude_global_policy' "$ROOT/scripts/install/targets.sh" "installer must call Claude global policy install from Claude target"
grep_required 'install_cursor_agent_set' "$ROOT/scripts/install/profiles.sh" "installer must define Cursor agent install set"
grep_required 'cursor-agents' "$ROOT/install.sh" "installer must support cursor-agents target"
grep_required 'cursor-policy' "$ROOT/install.sh" "installer must support cursor-policy target"
grep_required 'cursor-policy-copy' "$ROOT/install.sh" "installer must support cursor-policy-copy target"
grep_required 'claude-policy' "$ROOT/install.sh" "installer must support claude-policy target"
grep_required 'configure_codex_routing' "$ROOT/scripts/install/targets.sh" "installer must configure user-level Codex routing"
grep_required 'no-codex-routing' "$ROOT/install.sh" "installer must expose a Codex routing opt-out"
grep_absent 'configure_codex_native_questions\|codex-native-questions\|default_mode_request_user_input\|code_mode_only' \
  "installer must not own or mutate the host native-input capability" \
  "$ROOT/install.sh" "$ROOT/scripts/install"
grep_required 'one main thread plus up to eight' "$ROOT/scripts/install/common.sh" \
  "installer help must document the root-inclusive thread limit"
grep_required 'codex_routing_status' "$ROOT/scripts/check-update.sh" "check-update must inspect Codex routing"
grep_required 'latest_remote_tag_version' "$ROOT/scripts/check-update.sh" \
  "check-update must inspect the latest remote semver tag"
grep_required 'latest_github_release_version' "$ROOT/scripts/check-update.sh" \
  "check-update must inspect the latest GitHub Release"
grep_required 'codex-routing' "$ROOT/skills/teamwork-init/SKILL.md" "teamwork-init must repair routing readiness"
grep_required 'Native interaction tools are host capabilities' "$ROOT/skills/teamwork-init/SKILL.md" \
  "teamwork-init must keep interaction capability host-owned"
grep_required 'Native interaction tools remain host-owned' "$ROOT/skills/teamwork-update/SKILL.md" \
  "teamwork-update must keep interaction capability runtime-owned"
for refresh_contract in 'Refresh user installations only' 'check-update.sh --readiness' 'applicable project surfaces' 'INSTALL_READY=yes' 'Never edit `VERSION`'; do
  grep_required "$refresh_contract" "$ROOT/skills/teamwork-update/SKILL.md" \
    "teamwork-update missing user-refresh contract: $refresh_contract"
done
grep_absent '## Maintainer Release\|## Release Unit\|v<VERSION>' \
  "installed teamwork-update must not own maintainer release policy" \
  "$ROOT/skills/teamwork-update"
[[ ! -e "$ROOT/skills/using-teamwork/references/changelog-guide.md" ]] \
  || fail "maintainer changelog guidance must live only in root AGENTS.md"
grep_absent 'One release unit contains\|complete release unit\|Write changelogs for users, not maintainers\|Until the tag and GitHub Release exist' \
  "maintainer release policy must not be duplicated outside root AGENTS.md" \
  "$ROOT/skills/teamwork-update/SKILL.md" "$ROOT/skills/using-teamwork/SKILL.md" \
  "$ROOT/skills/using-teamwork/references/check-update.md" "$ROOT/CODEX.md"
for release_contract in 'One release unit contains' 'both changelogs' '`v<VERSION>` tag' 'GitHub Release' 'report `release-ready`, not `released`'; do
  grep_required "$release_contract" "$ROOT/AGENTS.md" \
    "AGENTS.md missing atomic maintainer release contract: $release_contract"
done
for changelog_contract in 'Write changelogs for users, not maintainers' 'Before -> After' 'exact upgrade action or that no action is needed' 'reads like an engineering report is not release-ready'; do
  grep_required "$changelog_contract" "$ROOT/AGENTS.md" \
    "AGENTS.md missing user-facing changelog contract: $changelog_contract"
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
  "$ROOT/install.sh" "$ROOT/scripts/install" "$ROOT/scripts/check-update.sh" "$ROOT/scripts/init-project.sh" \
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
for contract in 'Ask Gate' 'discoverable evidence' 'safe, reversible, implementation-level details' 'one decision at a time' "host's native interaction surface" 'Ordinary clarification' 'does not grant implementation authority'; do
  grep_required "$contract" "$ROOT/skills/grill-me/SKILL.md" "grill-me missing minimal semantic contract: $contract"
done
for retired_field in 'Exit authority:' 'Implementation authority:' 'Close basis: no material user-owned decision remains' 'Alternatives:'; do
  grep_absent "$retired_field" "retired grill packet field must not remain: $retired_field" \
    "$ROOT/skills/grill-me" "$ROOT/scripts/eval-teamwork.py" \
    "$ROOT/scripts/teamwork_tooling/evaluation" "$ROOT/evals/teamwork/outputs/question-first"
done
grep_absent 'After five assistant questions\|five_question_checkpoint' \
  "grill-me must not restore a five-question quota" "$ROOT/skills/grill-me" \
  "$ROOT/scripts/eval-teamwork.py" "$ROOT/scripts/teamwork_tooling/evaluation" \
  "$ROOT/evals/teamwork/cases"
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
  grep_required "$tag" "$ROOT/scripts/teamwork_tooling/evaluation/contracts.py" \
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
grep_required 'exceeds coordination cost' "$ROOT/skills/using-teamwork/references/subagent-dispatch.md" \
  "Worker waves must be bounded by economics"
grep_absent 'first wave to at most two\|two-agent first wave' \
  "Worker waves must not restore a fixed quota" \
  "$ROOT/skills/using-teamwork/references/subagent-dispatch.md"

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
