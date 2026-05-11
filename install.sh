#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_SRC="$ROOT/skills/run-analyze-optimize/SKILL.md"

usage() {
  cat <<'USAGE'
Usage:
  ./install.sh claude
  ./install.sh codex
  ./install.sh cursor /path/to/project
  ./install.sh all /path/to/cursor-project

Installs by symlink where supported so skills/run-analyze-optimize/SKILL.md
remains the single source of truth.
USAGE
}

install_claude() {
  local dest="$HOME/.claude/skills/run-analyze-optimize"
  mkdir -p "$dest"
  ln -sf "$SKILL_SRC" "$dest/SKILL.md"
  echo "Installed Claude Code skill: $dest/SKILL.md"
}

install_codex() {
  local dest="$HOME/.codex/skills/run-analyze-optimize"
  mkdir -p "$dest"
  ln -sf "$SKILL_SRC" "$dest/SKILL.md"
  echo "Installed Codex skill: $dest/SKILL.md"
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
