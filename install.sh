#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_MODE="${TEAMWORK_INSTALL_MODE:-copy}"
CODEX_PROFILE="${TEAMWORK_CODEX_PROFILE:-performance-first}"
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
CODEX_AGENTS=(
  teamwork-explorer
  teamwork-worker
  teamwork-designer
  teamwork-judge
  teamwork-reviewer
  teamwork-deep-judge
  teamwork-deep-reviewer
)

usage() {
  cat <<'USAGE'
Usage:
  ./install.sh [--copy|--link] [--profile performance-first|cost-first] codex|cursor|claude|all|project|codex-agents|claude-agents|codex-policy

Targets:
  codex          Install skills, Codex agents, and Teamwork global policy (default target)
  cursor         Install skills to ~/.cursor/skills
  claude         Install skills to ~/.claude/skills
  all            Install skills, Codex agents, Claude agents, and Codex global policy
  project        Install skills to <repo>/.cursor/skills and agents to <repo>/.codex/agents and <repo>/.claude/agents
  codex-agents   Install Teamwork Codex custom agents to ~/.codex/agents
  claude-agents  Install Teamwork Claude subagents to ~/.claude/agents
  codex-policy   Print the Teamwork Codex global policy block for App Personalization

Default mode is --copy. Use --link for local development when installs should
track this checkout.

Codex profile defaults to performance-first. Use cost-first to downshift
Explorer, Designer, and Worker. Deep Judge/Reviewer stay xhigh.
USAGE
}

write_teamwork_codex_global_policy() {
  cat <<POLICY
<!-- TEAMWORK_CODEX_GLOBAL_START -->
## Teamwork Codex Global Policy

Subagents: this is the user's explicit standing authorization and request to
use sub-agents, delegation, and parallel agent work only when Teamwork dispatch
policy says the task is non-lightweight, independent, and worth the extra agent
cost.
Act by default: make ordinary decisions yourself — tool/MCP choice, naming,
formatting, safe reversible defaults, and equivalent approaches. Keep work local
for quick answers, tiny edits, one CodeGraph-answerable structural question,
tight critical-path work, overlapping write ownership, destructive or
credential-sensitive actions, or higher subagent context cost than benefit.

Ask only when it matters: ask one short question when you hit a real obstacle,
lack information you cannot obtain, or face a core decision you cannot resolve —
scope, acceptance, constraints, public behavior, contracts, architecture, or an
irreversible or destructive action. Do not interrupt for routine tool, MCP, or
approach choices. Missing required human input is a question first, a blocker
only when it cannot be obtained.

Codex model profile: default is ${CODEX_PROFILE}. performance-first uses
role-optimized gpt-5.5 agents: routine Explorer, Designer, and Worker use
medium; Judge and Reviewer use high; Deep Judge/Reviewer use xhigh. cost-first
downshifts routine Explorer, Designer, and Worker to gpt-5.4 medium.
Use project-local Teamwork init mode only for explicit overrides.

Bootstrap safety: required environment variables, paths, commands, ports, model
names, hyperparameters, credentials, configs, and execution modes must be
explicit in user input, project instructions, source/config, or an accepted
plan. Ask once when the user can supply a missing required value; treat it as
blocked only when it cannot be safely obtained, requires unavailable
credentials/resources, or the user declines. Report what was checked instead of
inventing fallbacks.

Remote execution: assume substantial code execution runs on the configured
remote server when project instructions or server inventory identify one. The
local environment is for editing, inspection, basic tests, syntax checks, and
lightweight validation. Before remote jobs, verify host, repository path,
branch, and command scope; do not invent missing execution targets.
<!-- TEAMWORK_CODEX_GLOBAL_END -->
POLICY
}

validate_codex_profile() {
  case "$CODEX_PROFILE" in
    performance-first|cost-first)
      ;;
    *)
      echo "Unknown Codex profile: $CODEX_PROFILE" >&2
      usage
      exit 2
      ;;
  esac
}

install_codex_global_policy() {
  local dest_dir="$HOME/.codex"
  local dest="$dest_dir/AGENTS.md"
  local tmp

  mkdir -p "$dest_dir"
  tmp="$(mktemp)"

  if [[ -f "$dest" ]]; then
    awk '
      /<!-- TEAMWORK_CODEX_GLOBAL_START -->/ { skip = 1; next }
      /<!-- TEAMWORK_CODEX_GLOBAL_END -->/ { skip = 0; next }
      skip { next }
      $0 == "No user needs to specify sub-agents for distribution; default assignment is used." { next }
      $0 == "All code runs on a remote server; the local environment only supports basic testing and syntax checking." { next }
      { print }
    ' "$dest" > "$tmp"
  fi

  if [[ -s "$tmp" ]]; then
    printf '\n' >> "$tmp"
  fi
  write_teamwork_codex_global_policy >> "$tmp"
  mv "$tmp" "$dest"
  echo "Installed Teamwork Codex global policy under: $dest"
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
      references)
        [[ "$retired" == "teamwork" ]] || return 1
        ;;
      references/*)
        [[ "$retired" == "teamwork" ]] || return 1
        [[ -f "$ROOT/skills/using-teamwork/$rel" ]] || return 1
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

codex_agent_profile_values() {
  local agent="$1"
  case "$CODEX_PROFILE:$agent" in
    cost-first:teamwork-explorer|cost-first:teamwork-designer|cost-first:teamwork-worker)
      printf '%s %s\n' "gpt-5.4" "medium"
      ;;
    *:teamwork-deep-judge|*:teamwork-deep-reviewer)
      printf '%s %s\n' "gpt-5.5" "xhigh"
      ;;
    *:teamwork-explorer|*:teamwork-designer|*:teamwork-worker)
      printf '%s %s\n' "gpt-5.5" "medium"
      ;;
    *)
      printf '%s %s\n' "gpt-5.5" "high"
      ;;
  esac
}

install_codex_agent_file() {
  local source="$1"
  local dest="$2"
  local agent="$3"
  local model effort tmp

  read -r model effort < <(codex_agent_profile_values "$agent")
  rm -f "$dest"
  mkdir -p "$(dirname "$dest")"

  if [[ "$INSTALL_MODE" == "link" && "$CODEX_PROFILE" == "performance-first" ]]; then
    ln -sfn "$source" "$dest"
    return 0
  fi

  tmp="$(mktemp)"
  sed \
    -e "s/^model = .*/model = \"$model\"/" \
    -e "s/^model_reasoning_effort = .*/model_reasoning_effort = \"$effort\"/" \
    "$source" > "$tmp"
  mv "$tmp" "$dest"
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

install_codex_agent_set() {
  local dest_root="$1"
  local label="$2"
  local agent

  mkdir -p "$dest_root"
  for agent in "${CODEX_AGENTS[@]}"; do
    install_codex_agent_file \
      "$ROOT/templates/codex-agents/$agent.toml" \
      "$dest_root/$agent.toml" \
      "$agent"
  done

  echo "Installed $label Codex agents under: $dest_root ($INSTALL_MODE, $CODEX_PROFILE)"
}

install_codex() {
  install_skill_set "$HOME/.codex/skills" "Codex"
  install_codex_agent_set "$HOME/.codex/agents" "user"
  install_codex_global_policy
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
  install_claude_agents_home
}

install_project() {
  install_skill_set "$ROOT/.cursor/skills" "project Cursor"
  install_codex_agent_set "$ROOT/.codex/agents" "project"
  install_claude_agent_set "$ROOT/.claude/agents" "project Claude Code"
}

install_codex_agents_home() {
  install_codex_agent_set "$HOME/.codex/agents" "user"
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
    --profile)
      [[ $# -ge 2 ]] || { echo "--profile requires a value." >&2; usage; exit 2; }
      CODEX_PROFILE="$2"
      shift 2
      ;;
    --performance-first)
      CODEX_PROFILE="performance-first"
      shift
      ;;
    --cost-first)
      CODEX_PROFILE="cost-first"
      shift
      ;;
    codex|cursor|claude|all|project|codex-agents|claude-agents|codex-policy)
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

validate_codex_profile

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
  codex-agents)
    install_codex_agents_home
    ;;
  claude-agents)
    install_claude_agents_home
    ;;
  codex-policy)
    write_teamwork_codex_global_policy
    ;;
  *)
    usage
    exit 2
    ;;
esac
