#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_MODE="${TEAMWORK_INSTALL_MODE:-copy}"
SKILLS=(
  teamwork
  teamwork-design
  teamwork-execute
  teamwork-review
)
RETIRED_SKILLS=(
  run-analyze-optimize
  run-analyze-design
  run-analyze-execute
  run-analyze-review
  run-analyze-research
  run-analyze-plan
  run-analyze-goal
  run-analyze-plan-review
  run-analyze-execution-review
)

usage() {
  cat <<'USAGE'
Usage:
  ./install.sh [--copy|--link] claude
  ./install.sh [--copy|--link] codex
  ./install.sh [--copy|--link] cursor /path/to/project
  ./install.sh [--copy|--link] all /path/to/cursor-project

Default mode is --copy, which installs standalone files so the skills keep
working if this repository moves or is deleted. Use --link for local
development when you want installed skills to track edits in this checkout.

Claude Code plugin installs should use the checked-in plugin manifest for
commands and hooks; this script does not modify global settings.
USAGE
}

remove_retired_skill() {
  local root="$1"
  local retired="$2"
  local dest="$root/$retired"
  local link="$dest/SKILL.md"
  local raw_target resolved entry_count

  [[ -e "$link" || -L "$link" ]] || return 0

  if [[ -L "$link" ]]; then
    raw_target="$(readlink "$link" 2>/dev/null || true)"
    resolved="$(readlink -f "$link" 2>/dev/null || true)"
    if [[ "$raw_target" == */skills/"$retired"/SKILL.md || \
          "$resolved" == */skills/"$retired"/SKILL.md ]]; then
      rm -f "$link"
      rmdir "$dest" 2>/dev/null || true
    fi
    return 0
  fi

  [[ -f "$link" ]] || return 0
  grep -q "^name: $retired$" "$link" || return 0
  entry_count="$(find "$dest" -mindepth 1 -maxdepth 1 | wc -l | tr -d ' ')"
  if [[ "$entry_count" == "1" ]]; then
    rm -f "$link"
    rmdir "$dest" 2>/dev/null || true
  fi
}

install_file() {
  local source="$1"
  local dest="$2"

  mkdir -p "$(dirname "$dest")"
  rm -f "$dest"
  case "$INSTALL_MODE" in
    copy)
      cp "$source" "$dest"
      ;;
    link)
      ln -sf "$source" "$dest"
      ;;
    *)
      echo "Unknown install mode: $INSTALL_MODE" >&2
      usage
      exit 2
      ;;
  esac
}

install_skill_set() {
  local root="$1"
  local label="$2"
  local skill dest retired

  mkdir -p "$root"
  for retired in "${RETIRED_SKILLS[@]}"; do
    remove_retired_skill "$root" "$retired"
  done

  for skill in "${SKILLS[@]}"; do
    dest="$root/$skill"
    install_file "$ROOT/skills/$skill/SKILL.md" "$dest/SKILL.md"
  done
  echo "Installed $label skills under: $root ($INSTALL_MODE)"
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
  if [[ -L "$rules/run-analyze-optimize.mdc" ]]; then
    local raw_target resolved
    raw_target="$(readlink "$rules/run-analyze-optimize.mdc" 2>/dev/null || true)"
    resolved="$(readlink -f "$rules/run-analyze-optimize.mdc" 2>/dev/null || true)"
    if [[ "$raw_target" == "$ROOT/.cursor/rules/run-analyze-optimize.mdc" || \
          "$resolved" == "$ROOT/.cursor/rules/run-analyze-optimize.mdc" ]]; then
      rm -f "$rules/run-analyze-optimize.mdc"
    fi
  elif [[ -f "$rules/run-analyze-optimize.mdc" ]] && \
       grep -q 'run-analyze-optimize\|Run-Analyze-Optimize' "$rules/run-analyze-optimize.mdc"; then
    rm -f "$rules/run-analyze-optimize.mdc"
  fi
  install_file "$ROOT/.cursor/rules/teamwork.mdc" "$rules/teamwork.mdc"
  echo "Installed Cursor rule: $rules/teamwork.mdc ($INSTALL_MODE)"
}

case "${1:-}" in
  --copy)
    INSTALL_MODE="copy"
    shift
    ;;
  --link)
    INSTALL_MODE="link"
    shift
    ;;
esac

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
