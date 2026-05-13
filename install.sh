#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
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

usage() {
  cat <<'USAGE'
Usage:
  ./install.sh claude
  ./install.sh codex
  ./install.sh cursor /path/to/project
  ./install.sh all /path/to/cursor-project

Installs by symlink where supported so each skills/*/SKILL.md remains the
source of truth. Claude Code plugin installs should use the checked-in plugin
manifest for commands and hooks; this script does not modify global settings.
USAGE
}

install_skill_set() {
  local root="$1"
  local label="$2"
  local skill dest retired link raw_target resolved

  mkdir -p "$root"
  for retired in "${RETIRED_SKILLS[@]}"; do
    dest="$root/$retired"
    link="$dest/SKILL.md"
    if [[ -L "$link" ]]; then
      raw_target="$(readlink "$link" 2>/dev/null || true)"
      resolved="$(readlink -f "$link" 2>/dev/null || true)"
      if [[ "$raw_target" == "$ROOT/skills/$retired/SKILL.md" || \
            "$resolved" == "$ROOT/skills/$retired/SKILL.md" ]]; then
        rm -f "$link"
        rmdir "$dest" 2>/dev/null || true
      fi
    fi
  done

  for skill in "${SKILLS[@]}"; do
    dest="$root/$skill"
    mkdir -p "$dest"
    ln -sf "$ROOT/skills/$skill/SKILL.md" "$dest/SKILL.md"
  done
  echo "Installed $label skills under: $root"
}

install_claude() {
  install_skill_set "$HOME/.claude/skills" "Claude Code"
}

install_codex() {
  install_skill_set "$HOME/.codex/skills" "Codex"
}

install_cursor() {
  local project="${1:-}"
  if [[ -z "$project" ]]; then
    echo "Cursor install requires a project path." >&2
    usage
    exit 2
  fi

  local rules="$project/.cursor/rules"
  mkdir -p "$rules"
  ln -sf "$ROOT/.cursor/rules/run-analyze-optimize.mdc" \
    "$rules/run-analyze-optimize.mdc"
  echo "Installed Cursor rule: $rules/run-analyze-optimize.mdc"
}

case "${1:-}" in
  claude)
    install_claude
    ;;
  codex)
    install_codex
    ;;
  cursor)
    install_cursor "${2:-}"
    ;;
  all)
    install_claude
    install_codex
    install_cursor "${2:-}"
    ;;
  *)
    usage
    exit 2
    ;;
esac
