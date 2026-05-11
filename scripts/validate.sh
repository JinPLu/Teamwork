#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROUTER="$ROOT/skills/run-analyze-optimize/SKILL.md"
SKILLS=(
  run-analyze-optimize
  run-analyze-design
  run-analyze-execute
  run-analyze-review
)
RETIRED_SKILLS=(
  run-analyze-research
  run-analyze-plan
  run-analyze-goal
  run-analyze-plan-review
  run-analyze-execution-review
)

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

expected_skill_dirs="$(printf '%s\n' "${SKILLS[@]}" | sort)"
actual_skill_dirs="$(find "$ROOT/skills" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort)"
[[ "$actual_skill_dirs" == "$expected_skill_dirs" ]] || fail "skills/ must contain exactly: ${SKILLS[*]}"

for retired in "${RETIRED_SKILLS[@]}"; do
  [[ ! -d "$ROOT/skills/$retired" ]] || fail "retired skill directory still exists: skills/$retired"
done

for skill in "${SKILLS[@]}"; do
  file="$ROOT/skills/$skill/SKILL.md"
  [[ -f "$file" ]] || fail "missing skills/$skill/SKILL.md"
  git -C "$ROOT" ls-files --error-unmatch "skills/$skill/SKILL.md" >/dev/null 2>&1 \
    || fail "skills/$skill/SKILL.md is not tracked by git"
  head -n 1 "$file" | grep -qx -- "---" || fail "$skill SKILL.md must start with YAML frontmatter"
  grep -q "^name: $skill$" "$file" || fail "$skill missing matching skill name"
  grep -Eq '^description: Use when .+' "$file" || fail "$skill description must start with: Use when"
  ! grep -q '^disable-model-invocation:' "$file" || fail "$skill uses unsupported disable-model-invocation metadata"
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

for subskill in run-analyze-design run-analyze-execute run-analyze-review; do
  grep -q "skills/$subskill/SKILL.md" "$ROUTER" || fail "router does not reference skills/$subskill/SKILL.md"
done

grep -q 'mode: goal' "$ROUTER" || fail "router must own mode: goal"
grep -q 'mode: research' "$ROOT/skills/run-analyze-design/SKILL.md" || fail "design skill missing mode: research"
grep -q 'mode: plan' "$ROOT/skills/run-analyze-design/SKILL.md" || fail "design skill missing mode: plan"
grep -q 'mode: plan' "$ROOT/skills/run-analyze-review/SKILL.md" || fail "review skill missing mode: plan"
grep -q 'mode: execution' "$ROOT/skills/run-analyze-review/SKILL.md" || fail "review skill missing mode: execution"

[[ -f "$ROOT/.claude-plugin/plugin.json" ]] || fail "missing Claude plugin manifest"
[[ -f "$ROOT/.codex-plugin/plugin.json" ]] || fail "missing Codex plugin manifest"
[[ -f "$ROOT/.cursor/rules/run-analyze-optimize.mdc" ]] || fail "missing Cursor rule"

python3 -m json.tool "$ROOT/.claude-plugin/plugin.json" >/dev/null
python3 -m json.tool "$ROOT/.claude-plugin/marketplace.json" >/dev/null
python3 -m json.tool "$ROOT/.codex-plugin/plugin.json" >/dev/null

python3 - "$ROOT" <<'PY'
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
expected = [
    "./skills/run-analyze-optimize",
    "./skills/run-analyze-design",
    "./skills/run-analyze-execute",
    "./skills/run-analyze-review",
]
retired = {
    "./skills/run-analyze-research",
    "./skills/run-analyze-plan",
    "./skills/run-analyze-goal",
}

claude = json.loads((root / ".claude-plugin/plugin.json").read_text())
if claude.get("skills") != expected:
    raise SystemExit("FAIL: Claude manifest skills must list the current skill directories")
if retired.intersection(claude.get("skills", [])):
    raise SystemExit("FAIL: Claude manifest still lists retired skills")

codex = json.loads((root / ".codex-plugin/plugin.json").read_text())
if codex.get("skills") != "./skills/":
    raise SystemExit("FAIL: Codex manifest skills must remain ./skills/")
PY

for skill in "${SKILLS[@]}"; do
  grep -q "$skill" "$ROOT/.cursor/rules/run-analyze-optimize.mdc" || fail "Cursor rule does not mention $skill"
  grep -q "$skill" "$ROOT/install.sh" || fail "install.sh does not install $skill"
  grep -q "$skill" "$ROOT/README.md" || fail "README.md does not mention $skill"
done

for retired in "${RETIRED_SKILLS[@]}"; do
  ! grep -q "$retired" "$ROOT/.cursor/rules/run-analyze-optimize.mdc" || fail "Cursor rule mentions retired skill $retired"
  ! grep -q "$retired" "$ROOT/README.md" || fail "README.md mentions retired skill $retired"
done

cursor_lines="$(wc -l < "$ROOT/.cursor/rules/run-analyze-optimize.mdc")"
[[ "$cursor_lines" -le 120 ]] || fail "Cursor rule is too long to be a thin summary"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

HOME="$tmp/claude-home" "$ROOT/install.sh" claude >/dev/null
HOME="$tmp/codex-home" "$ROOT/install.sh" codex >/dev/null
mkdir -p "$tmp/cursor-project"
HOME="$tmp/cursor-home" "$ROOT/install.sh" cursor "$tmp/cursor-project" >/dev/null

for skill in "${SKILLS[@]}"; do
  [[ -L "$tmp/claude-home/.claude/skills/$skill/SKILL.md" ]] || fail "Claude install missing $skill"
  [[ -L "$tmp/codex-home/.codex/skills/$skill/SKILL.md" ]] || fail "Codex install missing $skill"
done
[[ -L "$tmp/cursor-project/.cursor/rules/run-analyze-optimize.mdc" ]] || fail "Cursor install missing rule"

for retired in "${RETIRED_SKILLS[@]}"; do
  mkdir -p "$tmp/migration-home/.codex/skills/$retired"
  ln -sf "$ROOT/skills/$retired/SKILL.md" "$tmp/migration-home/.codex/skills/$retired/SKILL.md"
done
HOME="$tmp/migration-home" "$ROOT/install.sh" codex >/dev/null
for retired in "${RETIRED_SKILLS[@]}"; do
  [[ ! -e "$tmp/migration-home/.codex/skills/$retired/SKILL.md" && \
     ! -L "$tmp/migration-home/.codex/skills/$retired/SKILL.md" ]] \
    || fail "install did not clean retired symlink: $retired"
done

echo "OK: run-analyze-optimize skill package validates"
