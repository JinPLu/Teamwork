#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROUTER="$ROOT/skills/run-analyze-optimize/SKILL.md"
SKILLS=(
  run-analyze-optimize
  run-analyze-research
  run-analyze-plan
  run-analyze-execute
  run-analyze-review
  run-analyze-goal
)

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

expected_skill_dirs="$(printf '%s\n' "${SKILLS[@]}" | sort)"
actual_skill_dirs="$(find "$ROOT/skills" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort)"
[[ "$actual_skill_dirs" == "$expected_skill_dirs" ]] || fail "skills/ must contain exactly: ${SKILLS[*]}"

for skill in "${SKILLS[@]}"; do
  file="$ROOT/skills/$skill/SKILL.md"
  [[ -f "$file" ]] || fail "missing skills/$skill/SKILL.md"
  head -n 1 "$file" | grep -qx -- "---" || fail "$skill SKILL.md must start with YAML frontmatter"
  ! grep -q '^```skill' "$file" || fail "$skill SKILL.md must not be wrapped in a skill fence"
  grep -q "^name: $skill$" "$file" || fail "$skill missing matching skill name"
  grep -q '^description:' "$file" || fail "$skill missing skill description"
done

for subskill in run-analyze-research run-analyze-plan run-analyze-execute run-analyze-review run-analyze-goal; do
  grep -q "skills/$subskill/SKILL.md" "$ROUTER" || fail "router does not reference skills/$subskill/SKILL.md"
done

grep -q 'plan-review.*run-analyze-review' "$ROUTER" || fail "router must route plan-review intent to run-analyze-review"
grep -q 'execution-review.*run-analyze-review' "$ROUTER" || fail "router must route execution-review intent to run-analyze-review"
grep -q 'mode: plan' "$ROOT/skills/run-analyze-review/SKILL.md" || fail "review skill missing mode: plan"
grep -q 'mode: execution' "$ROOT/skills/run-analyze-review/SKILL.md" || fail "review skill missing mode: execution"
[[ ! -d "$ROOT/skills/run-analyze-plan-review" ]] || fail "do not split plan review into a separate subskill"
[[ ! -d "$ROOT/skills/run-analyze-execution-review" ]] || fail "do not split execution review into a separate subskill"

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
    "./skills/run-analyze-research",
    "./skills/run-analyze-plan",
    "./skills/run-analyze-execute",
    "./skills/run-analyze-review",
    "./skills/run-analyze-goal",
]

claude = json.loads((root / ".claude-plugin/plugin.json").read_text())
if claude.get("skills") != expected:
    raise SystemExit("FAIL: Claude manifest skills must list every skill directory")

codex = json.loads((root / ".codex-plugin/plugin.json").read_text())
if codex.get("skills") != "./skills/":
    raise SystemExit("FAIL: Codex manifest skills must remain ./skills/")
PY

for skill in "${SKILLS[@]}"; do
  grep -q "$skill" "$ROOT/.cursor/rules/run-analyze-optimize.mdc" || fail "Cursor rule does not mention $skill"
  grep -q "$skill" "$ROOT/install.sh" || fail "install.sh does not install $skill"
  grep -q "$skill" "$ROOT/README.md" || fail "README.md does not mention $skill"
done

cursor_lines="$(wc -l < "$ROOT/.cursor/rules/run-analyze-optimize.mdc")"
[[ "$cursor_lines" -le 120 ]] || fail "Cursor rule is too long to be a thin summary"

echo "OK: run-analyze-optimize skill package validates"
