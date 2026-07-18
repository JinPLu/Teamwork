#!/usr/bin/env bash

# --- Public documentation ---
# Keep these checks about outcomes and user actions. Internal implementation
# details belong with their owners, not in the platform guides.
grep_required 'Codex、Cursor 和 Claude Code' "$ROOT/README.md" "README must name all supported platforms"
grep_required '共享 skill package' "$ROOT/README.md" "README must describe the shared package"
grep_required '各宿主仍负责发现 skill、调用原生工具、执行权限策略和产生实际回复' "$ROOT/README.md" \
  "README must preserve the host-owned runtime boundary"
grep_required '默认的完整全局刷新使用 `./install.sh all`' "$ROOT/README.md" \
  "README must make the full global refresh explicit"
grep_required 'check-update.sh --readiness' "$ROOT/README.md" "README must show the global readiness check"
grep_required '不会把 Teamwork skills 或 agents 安装到该仓库中' "$ROOT/README.md" \
  "README must keep init-project limited to project context"
grep_required '先给出结论或它代表的含义' "$ROOT/README.md" \
  "README must promise an audience-first response"
grep_required '技术细节只在确有帮助或你要求时展开' "$ROOT/README.md" \
  "README must relevance-gate technical detail"
grep_required '用户明确要求先提问或挑战时，可保存一份包含目标、已定选择、未决问题、关键证据和继续点的紧凑摘要' "$ROOT/README.md" \
  "README must describe authorized durable continuity"
grep_required '普通 Plan 不会自动进入 Grill 或写入讨论文档' "$ROOT/README.md" \
  "README must keep ordinary Plan out of Grill"
grep_required '只删除已确认由 Teamwork 生成的条目' "$ROOT/README.md" \
  "README must require safe legacy cleanup"
grep_required '绝不要整体删除 `.agents`、`.codex`、`.cursor` 或 `.claude`' "$ROOT/README.md" \
  "README must protect unrelated legacy directories"
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
grep_required 'one shared skill package adapted to Codex, Cursor, and Claude Code' "$ROOT/README.en.md" \
  "English README must describe the shared package"
grep_required 'Each host still owns skill discovery, native tool calls, permission policy, and the responses produced at runtime' "$ROOT/README.en.md" \
  "English README must preserve the host-owned runtime boundary"
grep_required 'The default full global refresh is `./install.sh all`' "$ROOT/README.en.md" \
  "English README must make the full global refresh explicit"
grep_required 'check-update.sh --readiness' "$ROOT/README.en.md" "English README must show the global readiness check"
grep_required 'it does not install Teamwork skills or agents into the repository' "$ROOT/README.en.md" \
  "English README must keep init-project limited to project context"
grep_required 'starts with the conclusion or what it means' "$ROOT/README.en.md" \
  "English README must promise an audience-first response"
grep_required 'Technical detail appears when it is useful or requested' "$ROOT/README.en.md" \
  "English README must relevance-gate technical detail"
grep_required 'an explicit request to be questioned or challenged may save one compact summary of the goal, settled choices, open question, key evidence, and continue point' "$ROOT/README.en.md" \
  "English README must describe authorized durable continuity"
grep_required 'An ordinary Plan does not automatically enter Grill or write a discussion record' "$ROOT/README.en.md" \
  "English README must keep ordinary Plan out of Grill"
grep_required 'Delete only entries you have confirmed Teamwork generated' "$ROOT/README.en.md" \
  "English README must require safe legacy cleanup"
grep_required 'never the whole `.agents`, `.codex`, `.cursor`, or `.claude` directory' "$ROOT/README.en.md" \
  "English README must protect unrelated legacy directories"
grep_required '\[Codex guide\](CODEX.md)' "$ROOT/README.en.md" "English README must link to the detailed Codex guide"
grep_required '\[Cursor guide\](CURSOR.md)' "$ROOT/README.en.md" "English README must link to the detailed Cursor guide"
grep_required '\[Claude Code guide\](CLAUDE.md)' "$ROOT/README.en.md" "English README must link to the detailed Claude Code guide"
check_markdown_local_images "$ROOT/README.en.md"
grep_required 'Codex + Cursor + Claude Code skill package' "$ROOT/AGENTS.md" "AGENTS.md must describe the package"
grep_required 'teamwork-update' "$ROOT/AGENTS.md" "AGENTS.md must document update skill ownership"
grep_required 'check-update.sh' "$ROOT/AGENTS.md" "AGENTS.md must document check-update script"
grep_required 'teamwork-init' "$ROOT/AGENTS.md" "AGENTS.md must document init skill ownership"
for retrieval_surface in \
  "$ROOT/AGENTS.md" \
  "$ROOT/scripts/init-project-files.py" \
  "$ROOT/skills/using-teamwork/references/teamwork-index-readme-template.md"; do
  grep_required 'For Grill/discussion continuation, load `grill-me`' "$retrieval_surface" \
    "$retrieval_surface must load grill-me before discussion continuation"
  grep_required 'run `inspect` from the project root' "$retrieval_surface" \
    "$retrieval_surface must route discussion reads through helper inspect"
  normalized_required 'sole discussion read path' "$retrieval_surface" \
    "$retrieval_surface must keep helper inspect as the sole discussion read path"
  normalized_required 'do not directly read `index.json`' "$retrieval_surface" \
    "$retrieval_surface must forbid direct canonical-memory reads during discussion continuation"
done
grep_absent 'Follow `active.current`, then `active.discussion`\|read the active discussion before continuing dependent work' \
  "project retrieval instructions must not direct-read active discussion state" \
  "$ROOT/AGENTS.md" \
  "$ROOT/skills/using-teamwork/references/teamwork-index-readme-template.md"
# Every platform guide carries the shared public promise. This protects the
# user-facing contract without making a guide narrate versioning, routing,
# host goal modes, or maintainer test implementation.
for guide in CODEX.md CURSOR.md CLAUDE.md; do
  guide_path="$ROOT/$guide"
  grep_required '\./install\.sh all' "$guide_path" "$guide must document the full global refresh command"
  grep_required 'default full global refresh' "$guide_path" "$guide must make that refresh global"
  grep_required 'init-project' "$guide_path" "$guide must document project-context setup"
  normalized_required 'It does not install Teamwork skills or agents into the repository' "$guide_path" \
    "$guide must keep init-project from creating local package copies"
  grep_required 'Replies lead with the conclusion or what it means' "$guide_path" \
    "$guide must lead with the conclusion or meaning"
  normalized_required 'technical detail when it helps or when you ask' "$guide_path" \
    "$guide must relevance-gate technical detail"
  normalized_required 'rather than narrating internal workflow labels or version details' "$guide_path" \
    "$guide must not make internal process narration the response"
  grep_required 'one compact summary of the goal' "$guide_path" "$guide must offer compact durable continuity when useful"
  normalized_required 'Ordinary requests do not need one' "$guide_path" \
    "$guide must keep durable continuity optional"
  grep_required 'teamwork-init' "$guide_path" "$guide must point users to project-context setup"
  grep_required 'teamwork-update' "$guide_path" "$guide must point users to global refresh guidance"
  grep_required 'check-update.sh --readiness' "$guide_path" "$guide must document the global readiness check"
  grep_required 'grill-me' "$guide_path" "$guide must document explicit grill-me invocation"
done

# Keep platform-specific details only where they change a user's setup or use.
grep_required 'Codex native capabilities' "$ROOT/CODEX.md" "CODEX.md must identify the native execution layer"
grep_required '~/.agents/skills' "$ROOT/CODEX.md" \
  "CODEX.md must document the supported Codex user-skill location"
grep_required 'Restart Codex after a routing change' "$ROOT/CODEX.md" "CODEX.md must preserve the required restart"
grep_required '/hooks' "$ROOT/CODEX.md" "CODEX.md must explain the user-owned hook trust step"
grep_required 'Cursor `Task` subagents' "$ROOT/CURSOR.md" "CURSOR.md must document its native subagent option"
grep_required 'cursor-policy-copy' "$ROOT/CURSOR.md" "CURSOR.md must document the manual User Rules setup"
grep_required 'Claude Code native capabilities' "$ROOT/CLAUDE.md" "CLAUDE.md must identify the native execution layer"
grep_required 'Claude Code `Task` subagents' "$ROOT/CLAUDE.md" "CLAUDE.md must document its native subagent option"
grep_required 'claude-policy' "$ROOT/CLAUDE.md" "CLAUDE.md must document global-policy review"

# --- Maintainer eval docs ---
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
grep_required 'CODEX_USER_SKILLS_ROOT="\$HOME/\.agents/skills"' "$ROOT/scripts/install/common.sh" \
  "Codex skills must use the supported user skill root"
grep_required 'preflight_legacy_codex_skills' "$ROOT/scripts/install/common.sh" \
  "Codex skill migration must fail closed before legacy cleanup"
grep_absent 'install_skill_set "\$HOME/\.codex/skills"' \
  "Codex installer must not create a second legacy skill root" \
  "$ROOT/scripts/install/targets.sh"
grep_required 'no-codex-routing' "$ROOT/install.sh" "installer must expose a Codex routing opt-out"
grep_absent 'configure_codex_native_questions\|codex-native-questions\|default_mode_request_user_input\|code_mode_only' \
  "installer must not own or mutate the host native-input capability" \
  "$ROOT/install.sh" "$ROOT/scripts/install"
grep_required 'one main thread plus up to eight' "$ROOT/scripts/install/common.sh" \
  "installer help must document the root-inclusive thread limit"
grep_required 'codex_routing_status' "$ROOT/scripts/check-update.sh" "check-update must inspect Codex routing"
grep_required 'MANAGED_INSTALL_READY=' "$ROOT/scripts/check-update.sh" \
  "readiness must retain a managed-install-only signal"
grep_required 'HOST_ACTIVATION=manual-action-required' "$ROOT/scripts/check-update.sh" \
  "readiness must not turn static install checks into a live activation claim"
grep_required 'MANUAL_ACTIONS=' "$ROOT/scripts/check-update.sh" \
  "readiness must list remaining host-owned actions"
grep_required 'latest_remote_tag_version' "$ROOT/scripts/check-update.sh" \
  "check-update must inspect the latest remote semver tag"
grep_required 'latest_github_release_version' "$ROOT/scripts/check-update.sh" \
  "check-update must inspect the latest GitHub Release"
grep_required 'codex-routing' "$ROOT/skills/teamwork-init/SKILL.md" "teamwork-init must repair routing readiness"
grep_required 'Native interaction tools are host capabilities' "$ROOT/skills/teamwork-init/SKILL.md" \
  "teamwork-init must keep interaction capability host-owned"
grep_required 'Native interaction tools remain host-owned' "$ROOT/skills/teamwork-update/SKILL.md" \
  "teamwork-update must keep interaction capability runtime-owned"
for refresh_contract in \
  'Refresh global user installations only' \
  'check-update.sh --readiness' \
  'global-only' \
  'skills, agents, managed policy, and routing' \
  'Project initialization and project-context' \
  'belong to `teamwork-init`' \
  'INSTALL_READY=yes' \
  'Never edit `VERSION`'; do
  grep_required "$refresh_contract" "$ROOT/skills/teamwork-update/SKILL.md" \
    "teamwork-update missing user-refresh contract: $refresh_contract"
done
grep_required 'Project-local install targets were removed' "$ROOT/install.sh" \
  "installer must reject the removed project-local package targets"
grep_required 'project-root is valid only with the init-project or plugin-init-project target' "$ROOT/install.sh" \
  "installer must reserve --project-root for checkout or Marketplace project-context setup"
grep_required 'project-only was removed' "$ROOT/scripts/init-project.sh" \
  "init-project must reject the removed project-only path"
grep_required 'project was removed' "$ROOT/scripts/check-update.sh" \
  "check-update must reject the removed project-local freshness route"
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
  normalized_required "$release_contract" "$ROOT/AGENTS.md" \
    "AGENTS.md missing atomic maintainer release contract: $release_contract"
done
for changelog_contract in 'Write changelogs for users, not maintainers' 'Before -> After' 'exact upgrade action or that no action is needed' 'reads like an engineering report is not release-ready'; do
  grep_required "$changelog_contract" "$ROOT/AGENTS.md" \
    "AGENTS.md missing user-facing changelog contract: $changelog_contract"
done
grep_required 'direct mainline release' "$ROOT/AGENTS.md" \
  "project Git policy must preserve the direct mainline release default"
normalized_required 'Create a branch or pull request only when the user explicitly requests it or repository protection requires it' "$ROOT/AGENTS.md" \
  "project Git policy must keep branch creation user- or protection-owned"
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
line_count_max "$ROOT/skills/grill-me/SKILL.md" 50 "grill-me should stay concise"
word_count_max "$ROOT/skills/grill-me/SKILL.md" 380 "grill-me should stay concise"
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
word_count_max "$ROOT/skills/using-teamwork/references/workflow-contract.md" 1050 "workflow contract reference should stay focused"
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
line_count_max "$ROOT/skills/using-teamwork/references/artifact-protocol.md" 100 "artifact protocol reference should stay focused"
word_count_max "$ROOT/skills/using-teamwork/references/artifact-protocol.md" 700 "artifact protocol reference should stay focused"
line_count_max "$ROOT/skills/using-teamwork/references/goal-iteration.md" 90 "goal iteration reference should stay focused"
word_count_max "$ROOT/skills/using-teamwork/references/goal-iteration.md" 520 "goal iteration reference should stay focused"
line_count_max "$ROOT/skills/using-teamwork/references/plan-output.md" 90 "plan output reference should stay focused"
word_count_max "$ROOT/skills/using-teamwork/references/plan-output.md" 500 "plan output reference should stay focused"
line_count_max "$ROOT/skills/using-teamwork/references/review-checks.md" 60 "review checks reference should stay focused"
word_count_max "$ROOT/skills/using-teamwork/references/review-checks.md" 460 "review checks reference should stay focused"
line_count_max "$ROOT/skills/using-teamwork/references/project-init.md" 85 "project init reference should stay focused"
word_count_max "$ROOT/skills/using-teamwork/references/project-init.md" 650 "project init reference should stay focused"
grep_required 'durable marker blocks protocol reads and writes' \
  "$ROOT/skills/using-teamwork/references/project-init.md" \
  "project init must document hard-interruption recovery instead of instant multi-file atomicity"
line_count_max "$ROOT/skills/using-teamwork/references/check-update.md" 80 "check update reference should stay focused"
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
grep_absent 'nature-writing\|nature-polishing' \
  "reader dialogue policy must stay native to Teamwork, not depend on external academic-writing skills" \
  "$ROOT/skills/using-teamwork" "$ROOT/skills/grill-me" "$ROOT/scripts/install/policy.sh" \
  "$ROOT/scripts/teamwork_tooling/evaluation" "$ROOT/evals/teamwork/cases"
grep_absent 'grill-mode.md' "retired grill-mode reference must be removed" "$ROOT/skills" "$ROOT/templates"
normalized_required 'authorized change/build work stays native or goes straight to Execute' "$ENTRYPOINT" "router must preserve the native fast path"
for intent in 'asks to be challenged, grilled, or questioned before action' 'ask me first' '先问我' 'continues that discussion'; do
  grep_required "$intent" "$ROOT/skills/grill-me/SKILL.md" \
    "grill-me description must expose semantic activation intent: $intent"
done
grep_required 'quoted, file, tool, example, or maintenance mentions are inert' "$ROOT/skills/grill-me/SKILL.md" \
  "grill-me must keep non-user marker text inert"
grep_required 'explicit negative intent wins' "$ROOT/skills/grill-me/SKILL.md" \
  "grill-me must honor explicit negative signals"
for contract in 'Ask Gate' 'discoverable evidence' 'safe, reversible, implementation-level details' 'one decision at a time' "host's native interaction surface" 'clarification do not activate Grill' 'does not grant implementation authority'; do
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
for contract in '## Ask Gate' 'uniquely supplies required input' 'required input' 'material decision' 'Own safe reversible details' 'pause only the dependent branch' 'Independent read-only work may continue' 'Root alone asks' 'Question Candidates' 'host owns UI' 'Teamwork never emulates host capabilities'; do
  grep_required "$contract" "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
    "workflow contract must preserve the shared ask boundary: $contract"
done
grep_required 'Do not invent required state' "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
  "workflow contract must preserve bootstrap safety"
grep_required 'Produce the real result first' "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
  "workflow contract must prioritize delivery"
grep_required 'do not replace it with a proxy check' "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
  "workflow contract must prefer an available real path"
grep_required 'stop; do not add another test, review, report, branch, or PR' "$ROOT/skills/using-teamwork/references/workflow-contract.md" \
  "workflow contract must stop after the requested result"
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
grep_required 'Gather only evidence that distinguishes the next possible fix' "$ROOT/skills/teamwork-debug/SKILL.md" \
  "debug must stay bounded to the next safe fix"
grep_required 'Codex is in Plan mode' "$ROOT/skills/teamwork-plan/SKILL.md" \
  "teamwork-plan metadata must trigger in Codex Plan mode"
grep_required 'native bridge and readiness gate' "$ROOT/skills/teamwork-plan/SKILL.md" \
  "teamwork-plan must bind Codex Plan mode to the Teamwork quality gate"
grep_required 'shortest authorized path' "$ROOT/skills/teamwork-execute/SKILL.md" "execute must preserve direct implementation"
normalized_required 'Never substitute plan/mock/static success for an available real path' "$ROOT/skills/teamwork-execute/SKILL.md" \
  "execute must not replace delivery with proxy checks"
grep_required 'eval-gate.md.*only when that gate applies' "$ROOT/skills/teamwork-review/SKILL.md" \
  "review must condition package eval policy"
normalized_required 'Do not invent a fixed iteration budget' "$ROOT/skills/teamwork-goal/SKILL.md" \
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
for anchor in 'Codex Plan Mode Bridge' 'shared Ask Gate' 'request_user_input' 'execution-critical value' 'Readiness Gate'; do
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
