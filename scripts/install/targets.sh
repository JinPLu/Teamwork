configure_user_notifications() {
  local platform="$1"
  local config dest
  [[ "$NOTIFICATIONS_ACTION" != "preserve" ]] || return 0

  case "$platform" in
    codex)
      config="$HOME/.codex/hooks.json"
      dest="$HOME/.codex/teamwork/notify.py"
      ;;
    claude)
      config="$HOME/.claude/settings.json"
      dest="$HOME/.claude/teamwork/notify.py"
      ;;
    *)
      echo "Unsupported notification platform: $platform" >&2
      exit 2
      ;;
  esac

  if [[ "$NOTIFICATIONS_ACTION" == "install" ]]; then
    install_agent_file "$ROOT/hooks/notify.py" "$dest"
    python3 "$ROOT/scripts/configure-notifications.py" install \
      --config "$config" --notifier "$dest"
    echo "Installed Teamwork $platform notifications: $config"
    if [[ "$platform" == "codex" ]]; then
      echo "Codex notification review required: open Codex CLI, run /hooks, and trust the Teamwork Stop and PermissionRequest hooks."
    fi
  else
    python3 "$ROOT/scripts/configure-notifications.py" remove \
      --config "$config" --notifier "$dest"
    rm -f "$dest"
    echo "Removed Teamwork $platform notifications from: $config"
  fi
}


configure_codex_routing() {
  if [[ "$CODEX_ROUTING_ACTION" == "preserve" ]]; then
    echo "Codex custom-agent routing: preserved (--no-codex-routing)"
    return 0
  fi
  if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 is required to configure Codex custom-agent routing." >&2
    return 1
  fi
  python3 "$ROOT/scripts/configure-codex-routing.py" --apply
}

install_codex() {
  preflight_teamwork_skill_root "$CODEX_USER_SKILLS_ROOT" "Codex user skill root"
  preflight_legacy_codex_skills "$(codex_home_path)/skills"
  preflight_owned_legacy_cleanup "$(codex_home_path)/skills"
  configure_codex_routing
  install_codex_skill_set
  install_codex_agent_set "$HOME/.codex/agents" "user"
  install_codex_global_policy
  configure_user_notifications codex
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
  configure_user_notifications claude
}

install_all() {
  install_codex
  install_cursor
  install_claude
}

init_project() {
  local base="${PROJECT_ROOT:-$PWD}"
  TEAMWORK_CODEX_ROUTING="$CODEX_ROUTING_ACTION" \
  TEAMWORK_NOTIFICATIONS_ACTION="$NOTIFICATIONS_ACTION" \
  "$ROOT/scripts/init-project.sh" \
    "--$INSTALL_MODE" \
    --profile "$CODEX_PROFILE" \
    --project-root "$base"
}

install_codex_agents_home() {
  configure_codex_routing
  install_codex_agent_set "$HOME/.codex/agents" "user"
}

install_cursor_agents_home() {
  install_cursor_agent_set "$HOME/.cursor/agents" "user Cursor"
}

install_claude_agents_home() {
  install_claude_agent_set "$HOME/.claude/agents" "user Claude Code"
}
