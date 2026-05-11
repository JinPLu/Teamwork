#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL="$ROOT/skills/run-analyze-optimize/SKILL.md"

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

[[ -f "$SKILL" ]] || fail "missing canonical SKILL.md"
head -n 1 "$SKILL" | grep -qx -- "---" || fail "SKILL.md must start with YAML frontmatter"
! grep -q '^```skill' "$SKILL" || fail "SKILL.md must not be wrapped in a skill fence"
grep -q '^name: run-analyze-optimize$' "$SKILL" || fail "missing skill name"
grep -q '^description:' "$SKILL" || fail "missing skill description"

[[ -f "$ROOT/.claude-plugin/plugin.json" ]] || fail "missing Claude plugin manifest"
[[ -f "$ROOT/.codex-plugin/plugin.json" ]] || fail "missing Codex plugin manifest"
[[ -f "$ROOT/.cursor/rules/run-analyze-optimize.mdc" ]] || fail "missing Cursor rule"

python3 -m json.tool "$ROOT/.claude-plugin/plugin.json" >/dev/null
python3 -m json.tool "$ROOT/.claude-plugin/marketplace.json" >/dev/null
python3 -m json.tool "$ROOT/.codex-plugin/plugin.json" >/dev/null

echo "OK: run-analyze-optimize skill package validates"
