#!/usr/bin/env bash

# Public documentation receives only structural checks here. Semantic quality
# belongs to an independent Reviewer reading the actual documents.
for document in README.md README.en.md CODEX.md CURSOR.md CLAUDE.md CONTRIBUTING.md CHANGELOG.md CHANGELOG.en.md; do
  [[ -f "$ROOT/$document" ]] || fail "missing $document"
  git_known_package_file "$document" \
    || fail "$document is absent from the active validation index"
done
check_markdown_local_images "$ROOT/README.md"
check_markdown_local_images "$ROOT/README.en.md"

current_version="$(tr -d '[:space:]' < "$ROOT/VERSION")"
[[ "$current_version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || fail "VERSION must be semver"
grep_required "## $current_version -" "$ROOT/CHANGELOG.md" \
  "Chinese changelog must document current VERSION"
grep_required "## $current_version -" "$ROOT/CHANGELOG.en.md" \
  "English changelog must document current VERSION"
python3 - "$ROOT" "$current_version" <<'PY'
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1])
current_version = sys.argv[2]


def release_labels(name: str) -> list[str]:
    text = (root / name).read_text(encoding="utf-8")
    labels = re.findall(r"^## (?P<label>[^\n]+)$", text, flags=re.MULTILINE)
    if not labels:
        raise SystemExit(f"FAIL: {name} has no release sections")
    return labels


labels = {name: release_labels(name) for name in ("CHANGELOG.md", "CHANGELOG.en.md")}
if labels["CHANGELOG.md"] != labels["CHANGELOG.en.md"]:
    raise SystemExit("FAIL: bilingual changelogs must keep identical release order")
if not labels["CHANGELOG.md"][0].startswith(f"{current_version} - "):
    raise SystemExit("FAIL: current VERSION must be the first bilingual changelog section")
PY

# instruction_footprint.py is the sole owner of word and byte budgets. This file
# keeps semantic and structural contracts without imposing a second, lower cap.
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
grep_required 'spawn_agent.agent_type' "$policy_tmp/codex.md" \
  "Codex adapter must select required Teamwork Agent roles explicitly"
grep_required 'teamwork_debugger' "$policy_tmp/codex.md" \
  "Codex adapter must expose exact installed Teamwork role IDs"
grep_required 'fork_turns' "$policy_tmp/codex.md" \
  "Codex adapter must describe compatible named-role context forking"
grep_absent 'request_user_input' "host-neutral policies must not name Codex input tools" \
  "$policy_tmp/cursor.md" "$policy_tmp/claude.md"

# Every public behavior owner is self-contained and reasonably focused. The
# semantic validator checks capability boundaries without freezing prose.
for skill in "${SKILLS[@]}"; do
  skill_file="$ROOT/skills/$skill/SKILL.md"
  fenced_block_line_count_max "$skill_file" 20 "$skill must not embed a large template"
done
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$ROOT/scripts" python3 - <<'PY'
from teamwork_tooling.evaluation.sources import validate_semantic_sources
validate_semantic_sources()
PY

grep_absent 'skills/[a-z0-9-]\+/SKILL\.md' \
  "SKILL.md files must not load another Teamwork skill" \
  "$ROOT/skills"
grep_absent 'grill-me\|teamwork-discuss\|teamwork-design\|using-teamwork\|teamwork-execute' \
  "retired public skill sources must not remain active" \
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
