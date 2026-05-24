#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_MODE="${TEAMWORK_INSTALL_MODE:-copy}"
DEST_ROOT="$HOME/.codex/skills"
SKILLS=(
  using-teamwork
  teamwork
  teamwork-goal
  teamwork-research
  teamwork-plan
  teamwork-execute
  teamwork-review
)
RETIRED_SKILLS=(
  teamwork-design
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
  ./install.sh [--copy|--link] [codex]

Installs the seven Teamwork skills into ~/.codex/skills.

Default mode is --copy, which installs standalone skill files. Use --link for
local development when installed skills should track this checkout.
USAGE
}

remove_retired_skill() {
  local retired="$1"
  local dest="$DEST_ROOT/$retired"
  local link="$dest/SKILL.md"
  local raw_target resolved entry_count

  if [[ -L "$dest" ]]; then
    raw_target="$(readlink "$dest" 2>/dev/null || true)"
    resolved="$(readlink -f "$dest" 2>/dev/null || true)"
    if [[ "$raw_target" == */skills/"$retired" || "$resolved" == */skills/"$retired" ]]; then
      rm -f "$dest"
    fi
    return 0
  fi

  [[ -e "$link" || -L "$link" ]] || return 0

  if [[ -L "$link" ]]; then
    raw_target="$(readlink "$link" 2>/dev/null || true)"
    resolved="$(readlink -f "$link" 2>/dev/null || true)"
    if [[ "$raw_target" == */skills/"$retired"/SKILL.md || "$resolved" == */skills/"$retired"/SKILL.md ]]; then
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

install_skill_dir() {
  local source="$1"
  local dest="$2"

  rm -rf "$dest"
  mkdir -p "$(dirname "$dest")"
  case "$INSTALL_MODE" in
    copy)
      cp -R "$source" "$dest"
      ;;
    link)
      ln -sfn "$source" "$dest"
      ;;
    *)
      echo "Unknown install mode: $INSTALL_MODE" >&2
      usage
      exit 2
      ;;
  esac
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

case "${1:-codex}" in
  ""|codex)
    ;;
  *)
    usage
    exit 2
    ;;
esac

mkdir -p "$DEST_ROOT"
for retired in "${RETIRED_SKILLS[@]}"; do
  remove_retired_skill "$retired"
done

for skill in "${SKILLS[@]}"; do
  install_skill_dir "$ROOT/skills/$skill" "$DEST_ROOT/$skill"
done

echo "Installed Codex skills under: $DEST_ROOT ($INSTALL_MODE)"
