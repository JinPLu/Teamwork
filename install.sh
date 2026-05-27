#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_MODE="${TEAMWORK_INSTALL_MODE:-copy}"
SKILLS=(
  using-teamwork
  teamwork-init
  teamwork-goal
  teamwork-research
  teamwork-plan
  teamwork-execute
  teamwork-review
  teamwork-update
)
RETIRED_SKILLS=(
  teamwork
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
CLAUDE_AGENTS=(
  explore
  worker
  code-reviewer
)

usage() {
  cat <<'USAGE'
Usage:
  ./install.sh [--copy|--link] codex|cursor|claude|all|project|claude-agents

Targets:
  codex          Install skills to ~/.codex/skills (default target)
  cursor         Install skills to ~/.cursor/skills
  claude         Install skills to ~/.claude/skills
  all            Install skills to codex, cursor, and claude home directories
  project        Install skills to <repo>/.cursor/skills and agents to <repo>/.claude/agents
  claude-agents  Install Teamwork Claude subagents to ~/.claude/agents

Default mode is --copy. Use --link for local development when installs should
track this checkout.
USAGE
}

retired_copy_is_plugin_owned() {
  local retired="$1"
  local dest="$2"
  local entry rel

  while IFS= read -r -d '' entry; do
    rel="${entry#$dest/}"
    case "$rel" in
      SKILL.md)
        ;;
      references|references/artifact-protocol.md|references/goal-iteration.md|references/dispatch-policy.md|references/subagent-prompt-contract.md|references/subagent-packets.md|references/subagent-routing.md|references/workflow-contract.md|references/plan-output.md|references/review-checks.md|references/project-init.md)
        [[ "$retired" == "teamwork" ]] || return 1
        ;;
      *)
        return 1
        ;;
    esac
  done < <(find "$dest" -mindepth 1 -print0)

  return 0
}

remove_retired_skill() {
  local dest_root="$1"
  local retired="$2"
  local dest="$dest_root/$retired"
  local link="$dest/SKILL.md"
  local raw_target resolved

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
  if retired_copy_is_plugin_owned "$retired" "$dest"; then
    rm -rf "$dest"
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

install_agent_file() {
  local source="$1"
  local dest="$2"

  rm -f "$dest"
  mkdir -p "$(dirname "$dest")"
  case "$INSTALL_MODE" in
    copy)
      cp "$source" "$dest"
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

install_skill_set() {
  local dest_root="$1"
  local label="$2"
  local skill

  mkdir -p "$dest_root"
  for retired in "${RETIRED_SKILLS[@]}"; do
    remove_retired_skill "$dest_root" "$retired"
  done

  for skill in "${SKILLS[@]}"; do
    install_skill_dir "$ROOT/skills/$skill" "$dest_root/$skill"
  done

  echo "Installed $label skills under: $dest_root ($INSTALL_MODE)"
}

install_claude_agent_set() {
  local dest_root="$1"
  local label="$2"
  local agent

  mkdir -p "$dest_root"
  for agent in "${CLAUDE_AGENTS[@]}"; do
    install_agent_file \
      "$ROOT/templates/claude-agents/$agent.md" \
      "$dest_root/$agent.md"
  done

  echo "Installed $label Claude agents under: $dest_root ($INSTALL_MODE)"
}

install_codex() {
  install_skill_set "$HOME/.codex/skills" "Codex"
}

install_cursor() {
  install_skill_set "$HOME/.cursor/skills" "Cursor"
}

install_claude() {
  install_skill_set "$HOME/.claude/skills" "Claude Code"
}

install_all() {
  install_codex
  install_cursor
  install_claude
}

install_project() {
  install_skill_set "$ROOT/.cursor/skills" "project Cursor"
  install_claude_agent_set "$ROOT/.claude/agents" "project Claude Code"
}

install_claude_agents_home() {
  install_claude_agent_set "$HOME/.claude/agents" "user Claude Code"
}

TARGET=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --copy)
      INSTALL_MODE="copy"
      shift
      ;;
    --link)
      INSTALL_MODE="link"
      shift
      ;;
    codex|cursor|claude|all|project|claude-agents)
      if [[ -n "$TARGET" ]]; then
        echo "Specify only one install target." >&2
        usage
        exit 2
      fi
      TARGET="$1"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

case "${TARGET:-codex}" in
  codex)
    install_codex
    ;;
  cursor)
    install_cursor
    ;;
  claude)
    install_claude
    ;;
  all)
    install_all
    ;;
  project)
    install_project
    ;;
  claude-agents)
    install_claude_agents_home
    ;;
  *)
    usage
    exit 2
    ;;
esac
