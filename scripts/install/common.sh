INSTALL_MODE="${TEAMWORK_INSTALL_MODE:-copy}"
CODEX_PROFILE="${TEAMWORK_CODEX_PROFILE:-performance-first}"
NOTIFICATIONS_ACTION="${TEAMWORK_NOTIFICATIONS_ACTION:-preserve}"
CODEX_ROUTING_ACTION="${TEAMWORK_CODEX_ROUTING:-configure}"
PKG_VERSION="unknown"
if [[ -f "$ROOT/VERSION" ]]; then
  PKG_VERSION="$(tr -d '[:space:]' < "$ROOT/VERSION")"
fi
SKILLS=(
  using-teamwork
  grill-me
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
  ./install.sh [--copy|--link] [--notifications|--no-notifications] [--codex-routing|--no-codex-routing] [--profile performance-first|cost-first|gpt56-role|gpt56-high|gpt56-xhigh|gpt55-high|gpt55-xhigh] \
    [--project-root PATH] \
    codex|cursor|claude|all|init-project|codex-agents|cursor-agents|claude-agents|codex-policy|cursor-policy|cursor-policy-copy|claude-policy

Targets:
  codex          Install skills, Codex agents, and Teamwork global policy (default target)
  cursor         Install skills, Cursor agents, and print cursor-policy guidance
  claude         Install skills, Claude agents, and Teamwork Claude global policy
  all            Install skills, all platform agents, and Codex + Claude global policy
  init-project   Refresh global skills, agents, and policies, then initialize
                 AGENTS.md, docs/teamwork/, .gitignore entries, and CodeGraph
                 for one project (use --project-root for another repo)
  codex-agents   Install Teamwork Codex custom agents to ~/.codex/agents
                 and configure their user-level routing unless opted out
  cursor-agents  Install Teamwork Cursor subagents to ~/.cursor/agents
  claude-agents  Install Teamwork Claude subagents to ~/.claude/agents
  codex-policy   Print the Teamwork Codex global policy block for App Personalization
  cursor-policy  Print the Teamwork Cursor global policy block for User Rules paste
  cursor-policy-copy
                 Copy the Teamwork Cursor global policy block to the clipboard
  claude-policy  Print the Teamwork Claude global policy block for manual review

Default mode is --copy. Use --link for local development when installs should
track this checkout.
`--project-root` is valid only with `init-project`.

Full installs (`all` and `init-project`) install ready/permission sounds for
user-level Codex and Claude Code by default. Direct platform installs leave
notifications unchanged unless --notifications or --no-notifications is used.
--no-notifications removes only Teamwork-owned handlers. Cursor notification
installs are intentionally unsupported until their local hook contracts are
live-verified.

User-level Codex installs configure ~/.codex/config.toml so the runtime can
select installed Teamwork agent roles and run one main thread plus up to eight
subagents. Use --no-codex-routing only when another owner manages that routing
contract; init-project refreshes the user-level routing before project setup.

Profile defaults to performance-first on all platforms. For Codex it uses a
GPT-5.6 role split: Terra medium for Explorer; Sol medium for Worker; Sol high
for Designer, Judge, and Reviewer; Sol max for Deep Judge/Reviewer. gpt56-role
is a compatibility alias for the same Codex mapping. cost-first uses Luna for
routine reading/design, Terra for implementation, and Sol for review. Use
gpt56-high or gpt56-xhigh to pin every Codex agent to Sol; legacy gpt55-high and
gpt55-xhigh names remain compatibility aliases and no longer emit GPT-5.5.
Non-Codex platforms keep current native model families for the same profiles.
USAGE
}


validate_codex_profile() {
  case "$CODEX_PROFILE" in
    performance-first|cost-first|gpt56-role|gpt56-high|gpt56-xhigh|gpt55-high|gpt55-xhigh)
      ;;
    *)
      echo "Unknown profile: $CODEX_PROFILE" >&2
      usage
      exit 2
      ;;
  esac
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
