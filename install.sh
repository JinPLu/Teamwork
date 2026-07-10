#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_MODE="${TEAMWORK_INSTALL_MODE:-copy}"
CODEX_PROFILE="${TEAMWORK_CODEX_PROFILE:-performance-first}"
PKG_VERSION="unknown"
if [[ -f "$ROOT/VERSION" ]]; then
  PKG_VERSION="$(tr -d '[:space:]' < "$ROOT/VERSION")"
fi
SKILLS=(
  using-teamwork
  teamwork-debug
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
  designer
  judge
  code-reviewer
  deep-judge
  deep-reviewer
)
CURSOR_AGENTS=(
  explore
  worker
  designer
  judge
  code-reviewer
  deep-judge
  deep-reviewer
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
  ./install.sh [--copy|--link] [--profile performance-first|cost-first|gpt56-role|gpt55-high|gpt55-xhigh] \
    [--project-root PATH] \
    codex|cursor|claude|all|project|init-project|project-codex-agents|codex-agents|cursor-agents|claude-agents|codex-policy|cursor-policy|cursor-policy-copy|claude-policy

Targets:
  codex          Install skills, Codex agents, and Teamwork global policy (default target)
  cursor         Install skills, Cursor agents, and print cursor-policy guidance
  claude         Install skills, Claude agents, and Teamwork Claude global policy
  all            Install skills, all platform agents, and Codex + Claude global policy
  project        Install project skills/agents under .cursor/, .codex/, and .claude/
                 (default: this checkout; use --project-root for another repo)
  init-project   Full project init: global/project skills and agents, AGENTS.md,
                 docs/teamwork/, .gitignore entries, and CodeGraph when available
  project-codex-agents
                 Install only project-local Teamwork Codex agents under .codex/
  codex-agents   Install Teamwork Codex custom agents to ~/.codex/agents
  cursor-agents  Install Teamwork Cursor subagents to ~/.cursor/agents
  claude-agents  Install Teamwork Claude subagents to ~/.claude/agents
  codex-policy   Print the Teamwork Codex global policy block for App Personalization
  cursor-policy  Print the Teamwork Cursor global policy block for User Rules paste
  cursor-policy-copy
                 Copy the Teamwork Cursor global policy block to the clipboard
  claude-policy  Print the Teamwork Claude global policy block for manual review

Default mode is --copy. Use --link for local development when installs should
track this checkout.

Profile defaults to performance-first on all platforms. Use cost-first to
downshift routine Explorer, Designer, and Worker roles. Judge, Reviewer, and
Deep variants stay on frontier tiers. Use gpt56-role for a GPT-5.6 Codex split:
Terra medium for Explorer; Sol medium for Worker; Sol high for Designer, Judge,
and Reviewer; Sol max for Deep Judge/Reviewer. Use gpt55-high or gpt55-xhigh to
force every Codex Teamwork agent to gpt-5.5 with high or xhigh reasoning.
The gpt56-role profile keeps non-Codex platforms on native performance-first
model tiers; legacy gpt55 profiles keep their existing adapter behavior.
USAGE
}

write_teamwork_codex_global_policy() {
  cat <<POLICY
<!-- TEAMWORK_CODEX_GLOBAL_START -->
## Teamwork Codex Global Policy

Act by default within the user's request. Answer, research, diagnose, plan, and
review are read-only unless the user also authorizes a change. Make routine,
reversible choices yourself; ask only when a remaining user decision could
materially change scope, acceptance, public behavior, risk, or an irreversible
action. Grill/question-first behavior activates only when explicitly requested.

Required runtime values and invariants must come from the user, project
instructions, source/config, tests, or an accepted plan. Do not invent them or
hide their absence behind a fallback; inspect first, then ask or block.

Keep changes inside the accepted scope. Get confirmation before destructive,
credential-sensitive, paid, public, or external-system actions not already
authorized. Match evidence and verification to risk, and do not claim behavior
or completion beyond what the checks demonstrate.

Delegation within the accepted scope is authorized, but use it only for
independent work whose evidence, time, or context-isolation value exceeds
coordination cost. The main agent owns integration and final verification.
Installed agent files own model mappings; active profile:
${CODEX_PROFILE}. Use project-local Teamwork init only for explicit overrides.
<!-- TEAMWORK_CODEX_GLOBAL_END -->
POLICY
}

write_teamwork_claude_global_policy() {
  cat <<POLICY
<!-- TEAMWORK_CLAUDE_GLOBAL_START -->
## Teamwork Claude Code Global Policy

Act by default within the user's request. Answer, research, diagnose, plan, and
review are read-only unless the user also authorizes a change. Make routine,
reversible choices yourself; ask only when a remaining user decision could
materially change scope, acceptance, public behavior, risk, or an irreversible
action. Grill/question-first behavior activates only when explicitly requested.

Required runtime values and invariants must come from the user, project
instructions, source/config, tests, or an accepted plan. Do not invent them or
hide their absence behind a fallback; inspect first, then ask or block.

Keep changes inside the accepted scope. Get confirmation before destructive,
credential-sensitive, paid, public, or external-system actions not already
authorized. Match evidence and verification to risk, and do not claim behavior
or completion beyond what the checks demonstrate.

Delegation within the accepted scope is authorized, but use it only for
independent work whose evidence, time, or context-isolation value exceeds
coordination cost. The main agent owns integration and final verification.
Installed agent files own model mappings; active profile:
${CODEX_PROFILE}. Use project-local Teamwork init only for explicit overrides.
<!-- TEAMWORK_CLAUDE_GLOBAL_END -->
POLICY
}

write_teamwork_cursor_global_policy() {
  cat <<POLICY
<!-- TEAMWORK_CURSOR_GLOBAL_START -->
## Teamwork Cursor Global Policy

Paste this block into Cursor Settings → Rules → User Rules.

Act by default within the user's request. Answer, research, diagnose, plan, and
review are read-only unless the user also authorizes a change. Make routine,
reversible choices yourself; ask only when a remaining user decision could
materially change scope, acceptance, public behavior, risk, or an irreversible
action. Grill/question-first behavior activates only when explicitly requested.

Required runtime values and invariants must come from the user, project
instructions, source/config, tests, or an accepted plan. Do not invent them or
hide their absence behind a fallback; inspect first, then ask or block.

Keep changes inside the accepted scope. Get confirmation before destructive,
credential-sensitive, paid, public, or external-system actions not already
authorized. Match evidence and verification to risk, and do not claim behavior
or completion beyond what the checks demonstrate.

Delegation within the accepted scope is authorized, but use it only for
independent work whose evidence, time, or context-isolation value exceeds
coordination cost. The main agent owns integration and final verification.
Installed agent files own model mappings; active profile:
${CODEX_PROFILE}. Use project-local Teamwork init only for explicit overrides.
<!-- TEAMWORK_CURSOR_GLOBAL_END -->
POLICY
}

copy_teamwork_cursor_global_policy() {
  local tmp
  tmp="$(mktemp)"
  write_teamwork_cursor_global_policy > "$tmp"

  if command -v pbcopy >/dev/null 2>&1; then
    pbcopy < "$tmp"
  elif command -v wl-copy >/dev/null 2>&1; then
    wl-copy < "$tmp"
  elif command -v xclip >/dev/null 2>&1; then
    xclip -selection clipboard < "$tmp"
  elif command -v xsel >/dev/null 2>&1; then
    xsel --clipboard --input < "$tmp"
  elif command -v clip.exe >/dev/null 2>&1; then
    clip.exe < "$tmp"
  else
    cat "$tmp"
    rm -f "$tmp"
    echo "No supported clipboard command found; printed policy block instead." >&2
    echo "Paste it into Cursor Settings -> Rules -> User Rules." >&2
    exit 1
  fi

  rm -f "$tmp"
  echo "Copied Teamwork Cursor global policy to clipboard."
  echo "Paste it into Cursor Settings -> Rules -> User Rules."
}

validate_codex_profile() {
  case "$CODEX_PROFILE" in
    performance-first|cost-first|gpt56-role|gpt55-high|gpt55-xhigh)
      ;;
    *)
      echo "Unknown profile: $CODEX_PROFILE" >&2
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

install_claude_global_policy() {
  local dest_dir="$HOME/.claude"
  local dest="$dest_dir/CLAUDE.md"
  local tmp

  mkdir -p "$dest_dir"
  tmp="$(mktemp)"

  if [[ -f "$dest" ]]; then
    awk '
      /<!-- TEAMWORK_CLAUDE_GLOBAL_START -->/ { skip = 1; next }
      /<!-- TEAMWORK_CLAUDE_GLOBAL_END -->/ { skip = 0; next }
      skip { next }
      { print }
    ' "$dest" > "$tmp"
  fi

  if [[ -s "$tmp" ]]; then
    printf '\n' >> "$tmp"
  fi
  write_teamwork_claude_global_policy >> "$tmp"
  mv "$tmp" "$dest"
  echo "Installed Teamwork Claude global policy under: $dest"
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
    gpt56-role:teamwork-explorer)
      printf '%s %s\n' "gpt-5.6-terra" "medium"
      ;;
    gpt56-role:teamwork-worker)
      printf '%s %s\n' "gpt-5.6-sol" "medium"
      ;;
    gpt56-role:teamwork-designer|gpt56-role:teamwork-judge|gpt56-role:teamwork-reviewer)
      printf '%s %s\n' "gpt-5.6-sol" "high"
      ;;
    gpt56-role:teamwork-deep-judge|gpt56-role:teamwork-deep-reviewer)
      printf '%s %s\n' "gpt-5.6-sol" "max"
      ;;
    gpt55-xhigh:*)
      printf '%s %s\n' "gpt-5.5" "xhigh"
      ;;
    gpt55-high:*)
      printf '%s %s\n' "gpt-5.5" "high"
      ;;
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

claude_agent_profile_values() {
  local agent="$1"
  case "$CODEX_PROFILE:$agent" in
    gpt56-role:explore|gpt56-role:designer|gpt56-role:worker|gpt55-xhigh:explore|gpt55-xhigh:designer|gpt55-xhigh:worker)
      printf '%s %s\n' "sonnet" "medium"
      ;;
    cost-first:explore|cost-first:designer|cost-first:worker)
      printf '%s %s\n' "haiku" "medium"
      ;;
    *:deep-judge|*:deep-reviewer)
      printf '%s %s\n' "opus" "xhigh"
      ;;
    *:explore|*:designer|*:worker)
      printf '%s %s\n' "sonnet" "medium"
      ;;
    *)
      printf '%s %s\n' "opus" "high"
      ;;
  esac
}

cursor_agent_profile_values() {
  local agent="$1"
  case "$CODEX_PROFILE:$agent" in
    gpt56-role:worker|gpt55-xhigh:worker)
      printf '%s\n' "composer-2.5-fast"
      ;;
    gpt56-role:explore|gpt56-role:designer|gpt55-xhigh:explore|gpt55-xhigh:designer)
      printf '%s\n' "claude-sonnet-4-6"
      ;;
    cost-first:explore|cost-first:designer|cost-first:worker)
      printf '%s\n' "composer-2.5-fast"
      ;;
    performance-first:worker)
      printf '%s\n' "composer-2.5-fast"
      ;;
    performance-first:explore|performance-first:designer)
      printf '%s\n' "claude-sonnet-4-6"
      ;;
    *:judge|*:code-reviewer|*:deep-judge|*:deep-reviewer)
      printf '%s\n' "claude-opus-4-8-thinking-high"
      ;;
    *)
      printf '%s\n' "claude-sonnet-4-6"
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

install_claude_agent_file() {
  local source="$1"
  local dest="$2"
  local agent="$3"
  local model effort tmp

  read -r model effort < <(claude_agent_profile_values "$agent")
  rm -f "$dest"
  mkdir -p "$(dirname "$dest")"

  if [[ "$INSTALL_MODE" == "link" && "$CODEX_PROFILE" == "performance-first" ]]; then
    ln -sfn "$source" "$dest"
    return 0
  fi

  tmp="$(mktemp)"
  sed \
    -e "s/^model: .*/model: $model/" \
    -e "s/^effort: .*/effort: $effort/" \
    "$source" > "$tmp"
  mv "$tmp" "$dest"
}

install_cursor_agent_file() {
  local source="$1"
  local dest="$2"
  local agent="$3"
  local model tmp

  read -r model < <(cursor_agent_profile_values "$agent")
  rm -f "$dest"
  mkdir -p "$(dirname "$dest")"

  if [[ "$INSTALL_MODE" == "link" && "$CODEX_PROFILE" == "performance-first" ]]; then
    ln -sfn "$source" "$dest"
    return 0
  fi

  tmp="$(mktemp)"
  sed -e "s/^model: .*/model: $model/" "$source" > "$tmp"
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

  printf '%s\n' "$PKG_VERSION" > "$dest_root/.teamwork-version"
  printf '%s\n' "$CODEX_PROFILE" > "$dest_root/.teamwork-profile"

  echo "Installed $label skills under: $dest_root ($INSTALL_MODE)"
}

install_claude_agent_set() {
  local dest_root="$1"
  local label="$2"
  local agent

  mkdir -p "$dest_root"
  for agent in "${CLAUDE_AGENTS[@]}"; do
    install_claude_agent_file \
      "$ROOT/templates/claude-agents/$agent.md" \
      "$dest_root/$agent.md" \
      "$agent"
  done

  echo "Installed $label Claude agents under: $dest_root ($INSTALL_MODE, $CODEX_PROFILE)"
}

install_cursor_agent_set() {
  local dest_root="$1"
  local label="$2"
  local agent

  mkdir -p "$dest_root"
  for agent in "${CURSOR_AGENTS[@]}"; do
    install_cursor_agent_file \
      "$ROOT/templates/cursor-agents/$agent.md" \
      "$dest_root/$agent.md" \
      "$agent"
  done

  echo "Installed $label Cursor agents under: $dest_root ($INSTALL_MODE, $CODEX_PROFILE)"
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
  install_cursor_agent_set "$HOME/.cursor/agents" "user Cursor"
  echo "Cursor User Rules: run ./install.sh cursor-policy-copy (or cursor-policy) and paste into Cursor Settings -> Rules -> User Rules."
}

install_claude() {
  install_skill_set "$HOME/.claude/skills" "Claude Code"
  install_claude_agent_set "$HOME/.claude/agents" "user Claude Code"
  install_claude_global_policy
}

install_all() {
  install_codex
  install_cursor
  install_claude
}

install_project() {
  local base="${PROJECT_ROOT:-$ROOT}"
  install_skill_set "$base/.cursor/skills" "project Cursor"
  install_codex_agent_set "$base/.codex/agents" "project"
  install_cursor_agent_set "$base/.cursor/agents" "project Cursor"
  install_claude_agent_set "$base/.claude/agents" "project Claude Code"
}

init_project() {
  local base="${PROJECT_ROOT:-$PWD}"
  "$ROOT/scripts/init-project.sh" \
    "--$INSTALL_MODE" \
    --profile "$CODEX_PROFILE" \
    --project-root "$base"
}

install_codex_agents_home() {
  install_codex_agent_set "$HOME/.codex/agents" "user"
}

install_cursor_agents_home() {
  install_cursor_agent_set "$HOME/.cursor/agents" "user Cursor"
}

install_claude_agents_home() {
  install_claude_agent_set "$HOME/.claude/agents" "user Claude Code"
}

TARGET=""
PROJECT_ROOT=""

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
    --project-root)
      [[ $# -ge 2 ]] || { echo "--project-root requires a path." >&2; usage; exit 2; }
      PROJECT_ROOT="$(cd "$2" && pwd)"
      shift 2
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
    codex|cursor|claude|all|project|init-project|project-codex-agents|codex-agents|cursor-agents|claude-agents|codex-policy|cursor-policy|cursor-policy-copy|claude-policy)
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

if [[ -n "$PROJECT_ROOT" && "${TARGET:-codex}" != "project" && "${TARGET:-codex}" != "init-project" && "${TARGET:-codex}" != "project-codex-agents" ]]; then
  echo "--project-root is valid only with the project, project-codex-agents, and init-project targets." >&2
  usage
  exit 2
fi

case "${TARGET:-codex}" in
  codex-policy|cursor-policy|cursor-policy-copy|claude-policy)
    ;;
  *)
    printf '%s\n' "$CODEX_PROFILE" > "$ROOT/.teamwork-profile"
    ;;
esac

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
  project-codex-agents)
    install_codex_agent_set "${PROJECT_ROOT:-$ROOT}/.codex/agents" "project"
    ;;
  init-project)
    init_project
    ;;
  codex-agents)
    install_codex_agents_home
    ;;
  cursor-agents)
    install_cursor_agents_home
    ;;
  claude-agents)
    install_claude_agents_home
    ;;
  codex-policy)
    write_teamwork_codex_global_policy
    ;;
  cursor-policy)
    write_teamwork_cursor_global_policy
    ;;
  cursor-policy-copy)
    copy_teamwork_cursor_global_policy
    ;;
  claude-policy)
    write_teamwork_claude_global_policy
    ;;
  *)
    usage
    exit 2
    ;;
esac
