#!/usr/bin/env bash

# User-facing documentation is validated by outcomes and boundaries, not by
# preserving one historical sentence.
semantic_doc_required() {
  local pattern="$1"
  local file="$2"
  local message="$3"
  tr '\n' ' ' < "$file" | grep -Eqi "$pattern" || fail "$message"
}

for document in README.md README.en.md CODEX.md CURSOR.md CLAUDE.md CHANGELOG.md CHANGELOG.en.md; do
  [[ -f "$ROOT/$document" ]] || fail "missing $document"
  git_known_package_file "$document" \
    || fail "$document is absent from the active validation index"
done

for readme in README.md README.en.md; do
  semantic_doc_required 'Codex.{0,80}Cursor.{0,80}Claude Code' "$ROOT/$readme" \
    "$readme must name all supported hosts"
  semantic_doc_required '(external|outside|外部).{0,80}(research|调研)' "$ROOT/$readme" \
    "$readme must explain external Research"
  semantic_doc_required '(Design.{0,120}Plan|设计.{0,120}计划)' "$ROOT/$readme" \
    "$readme must distinguish Design from Plan"
  semantic_doc_required 'docs/teamwork/discussion/current\.md' "$ROOT/$readme" \
    "$readme must explain the one-file Grill record"
  semantic_doc_required '\./install\.sh all' "$ROOT/$readme" \
    "$readme must show the complete checkout refresh"
  semantic_doc_required 'check-update\.sh --readiness' "$ROOT/$readme" \
    "$readme must show the readiness check"
  check_markdown_local_images "$ROOT/$readme"
done

for guide in CODEX.md CURSOR.md CLAUDE.md; do
  semantic_doc_required '(external|current).{0,80}(research|sources)' "$ROOT/$guide" \
    "$guide must explain external Research"
  semantic_doc_required 'Design.{0,120}(selected|Plan)' "$ROOT/$guide" \
    "$guide must explain the Design/Plan boundary"
  semantic_doc_required '(local|repository).{0,100}(native|natively)' "$ROOT/$guide" \
    "$guide must keep local evidence native"
  semantic_doc_required '(permissions|permission)' "$ROOT/$guide" \
    "$guide must preserve host permission ownership"
  semantic_doc_required 'init-project' "$ROOT/$guide" \
    "$guide must document project initialization"
  semantic_doc_required 'check-update\.sh --readiness' "$ROOT/$guide" \
    "$guide must document readiness"
done

current_version="$(tr -d '[:space:]' < "$ROOT/VERSION")"
[[ "$current_version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || fail "VERSION must be semver"
grep_required "## $current_version -" "$ROOT/CHANGELOG.md" \
  "Chinese changelog must document current VERSION"
grep_required "## $current_version -" "$ROOT/CHANGELOG.en.md" \
  "English changelog must document current VERSION"
semantic_doc_required 'One release unit.*(VERSION|version).*tag.*GitHub Release' \
  "$ROOT/AGENTS.md" "AGENTS.md must own an atomic maintainer release"
semantic_doc_required '(Write changelogs for users|面向用户)' "$ROOT/AGENTS.md" \
  "AGENTS.md must keep changelogs audience-first"
semantic_doc_required '(short, natural summary sentence|一句简短自然的总结)' "$ROOT/AGENTS.md" \
  "AGENTS.md must keep changelogs concise"
line_count_max "$ROOT/AGENTS.md" 70 "AGENTS.md must remain compact"
word_count_max "$ROOT/AGENTS.md" 600 "AGENTS.md must remain compact"

# The always-loaded policy owns the small amount of behavior that native agent
# work needs after removing the router/reference graph.
for writer in \
  write_teamwork_global_policy_body \
  write_teamwork_codex_global_policy \
  write_teamwork_cursor_global_policy \
  write_teamwork_claude_global_policy; do
  grep_required "$writer()" "$ROOT/scripts/install/policy.sh" \
    "installer policy must define $writer"
done
for platform in CODEX CURSOR CLAUDE; do
  grep_required "<!-- TEAMWORK_${platform}_GLOBAL_START -->" "$ROOT/scripts/install/policy.sh" \
    "installer policy must include the $platform managed marker"
done

policy_tmp="$(mktemp -d)"
CLEANUP_PATHS+=("$policy_tmp")
for platform in codex cursor claude; do
  "$ROOT/install.sh" "$platform-policy" > "$policy_tmp/$platform.md"
  check_lean_policy "$policy_tmp/$platform.md" "$platform" "$platform global policy"
done
grep_required 'request_user_input' "$policy_tmp/codex.md" \
  "Codex adapter must use request_user_input when callable"
grep_absent 'request_user_input' "host-neutral policies must not name Codex input tools" \
  "$policy_tmp/cursor.md" "$policy_tmp/claude.md"

# Every public behavior owner is self-contained and reasonably focused. The
# semantic validator checks capability boundaries without freezing prose.
for skill in "${SKILLS[@]}"; do
  skill_file="$ROOT/skills/$skill/SKILL.md"
  line_count_max "$skill_file" 180 "$skill should remain focused"
  word_count_max "$skill_file" 900 "$skill should remain focused"
  fenced_block_line_count_max "$skill_file" 20 "$skill must not embed a large template"
done
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$ROOT/scripts" python3 - <<'PY'
from teamwork_tooling.evaluation.sources import validate_semantic_sources
validate_semantic_sources()
PY

grep_absent 'skills/[a-z0-9-]\+/SKILL\.md' \
  "SKILL.md files must not load another Teamwork skill" \
  "$ROOT/skills"
grep_absent 'using-teamwork\|teamwork-execute' \
  "removed router and generic Execute skill must not remain in active skill sources" \
  "$ROOT/skills"

# Host interaction features remain host-owned.
grep_absent 'default_mode_request_user_input\|codex-native-questions\|configure-codex-native-questions\|code_mode_only' \
  "Teamwork must not install or emulate a host interaction feature" \
  "$ROOT/install.sh" "$ROOT/scripts/install" "$ROOT/scripts/check-update.sh" "$ROOT/scripts/init-project.sh" \
  "$ROOT/skills"

# Codex routing profiles still need structural validation, including collision
# rejection, but the skill package no longer depends on a role-playbook file.
[[ -f "$ROOT/scripts/check-codex-routing.py" ]] || fail "missing scripts/check-codex-routing.py"
compile_python_files "$ROOT/scripts/check-codex-routing.py"
python3 "$ROOT/scripts/check-codex-routing.py" \
  --agents-dir "$ROOT/templates/codex-agents" --profiles-only >/dev/null

codex_profile_tmp="$(mktemp -d)"
CLEANUP_PATHS+=("$codex_profile_tmp")
cp "$ROOT"/templates/codex-agents/*.toml "$codex_profile_tmp/"
python3 - "$codex_profile_tmp/other-agent.toml" <<'PY'
import pathlib
import sys

pathlib.Path(sys.argv[1]).write_text(
    'name = "other_agent"\nnickname_candidates = ["Atlas"]\n',
    encoding="utf-8",
)
PY
if python3 "$ROOT/scripts/check-codex-routing.py" \
  --agents-dir "$codex_profile_tmp" --profiles-only >/dev/null 2>&1; then
  fail "Codex profile validation must reject duplicate nicknames"
fi
