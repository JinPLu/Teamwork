configure_user_notifications() {
  local platform="$1"
  local config dest
  [[ "$NOTIFICATIONS_ACTION" != "preserve" ]] || return 0

  case "$platform" in
    codex)
      config="$(codex_home_path)/hooks.json"
      dest="$(codex_home_path)/teamwork/notify.py"
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
  python3 "$ROOT/scripts/configure-codex-routing.py" \
    --apply \
    --config "$(codex_home_path)/config.toml"
}

preflight_codex_notifications() {
  local config dest
  [[ "$NOTIFICATIONS_ACTION" != "preserve" ]] || return 0
  config="$(codex_home_path)/hooks.json"
  dest="$(codex_home_path)/teamwork/notify.py"
  if ! python3 "$ROOT/scripts/configure-notifications.py" status \
    --config "$config" --notifier "$dest" >/dev/null 2>&1; then
    echo "Codex notification configuration is not safe to update: $config" >&2
    return 1
  fi
  if [[ -e "$dest" && ! -f "$dest" ]]; then
    echo "Codex notification runtime is not a regular file: $dest" >&2
    return 1
  fi
}

preflight_codex_routing() {
  local config
  config="$(codex_home_path)/config.toml"
  if [[ "$CODEX_ROUTING_ACTION" == "preserve" ]]; then
    if ! python3 "$ROOT/scripts/configure-codex-routing.py" --check --config "$config" >/dev/null 2>&1; then
      echo "Codex routing is not ready; plugin activation cannot preserve a missing or drifting routing contract." >&2
      return 1
    fi
    return 0
  fi
  python3 "$ROOT/scripts/configure-codex-routing.py" --dry-run --config "$config" >/dev/null
}

preflight_plugin_codex_bootstrap() {
  local code_home legacy_root
  code_home="$(codex_home_path)"
  legacy_root="$code_home/skills"

  preflight_plugin_runtime
  preflight_teamwork_skill_root "$CODEX_USER_SKILLS_ROOT" "Legacy Codex user skill root"
  preflight_owned_legacy_cleanup "$CODEX_USER_SKILLS_ROOT"
  if [[ "$legacy_root" != "$CODEX_USER_SKILLS_ROOT" ]]; then
    preflight_legacy_codex_skills "$legacy_root"
    preflight_owned_legacy_cleanup "$legacy_root"
  fi
  preflight_codex_agent_set "$code_home/agents"
  preflight_codex_global_policy
  preflight_codex_routing
  preflight_codex_notifications
}

plugin_notification_setting() {
  case "$NOTIFICATIONS_ACTION" in
    install)
      printf '%s\n' "enabled"
      ;;
    remove)
      printf '%s\n' "disabled"
      ;;
    *)
      echo "plugin-codex-bootstrap requires an explicit notification setting." >&2
      return 1
      ;;
  esac
}

remove_plugin_legacy_skill_copies() {
  local code_home legacy_root
  code_home="$(codex_home_path)"
  legacy_root="$code_home/skills"
  remove_owned_legacy_codex_skills "$CODEX_USER_SKILLS_ROOT"
  if [[ "$legacy_root" != "$CODEX_USER_SKILLS_ROOT" ]]; then
    remove_owned_legacy_codex_skills "$legacy_root"
  fi
}

write_plugin_activation() {
  local notifications
  notifications="$(plugin_notification_setting)"
  python3 "$ROOT/scripts/plugin-activation.py" write \
    --path "$(codex_plugin_activation_path)" \
    --version "$PKG_VERSION" \
    --profile "$CODEX_PROFILE" \
    --notifications "$notifications" >/dev/null
  echo "Activated Teamwork Codex plugin: $(codex_plugin_activation_path)"
}

install_codex() {
  if plugin_activation_is_present; then
    echo "Teamwork Codex plugin activation is present. Legacy ./install.sh codex will not copy duplicate skills; start a new Codex task and run \$teamwork-update instead." >&2
    return 1
  fi
  preflight_teamwork_skill_root "$CODEX_USER_SKILLS_ROOT" "Codex user skill root"
  preflight_legacy_codex_skills "$(codex_home_path)/skills"
  preflight_owned_legacy_cleanup "$(codex_home_path)/skills"
  configure_codex_routing
  install_codex_skill_set
  install_codex_agent_set "$(codex_home_path)/agents" "user"
  install_codex_global_policy
  configure_user_notifications codex
}

install_plugin_codex_bootstrap() {
  local code_home
  code_home="$(codex_home_path)"
  preflight_plugin_codex_bootstrap
  configure_codex_routing
  install_codex_agent_set "$code_home/agents" "plugin"
  install_codex_global_policy
  configure_user_notifications codex
  remove_plugin_legacy_skill_copies
  write_plugin_activation
  echo "Teamwork full Codex setup is ready. Restart Codex; if notifications are enabled, run /hooks and trust only Teamwork Stop and PermissionRequest."
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

init_plugin_project() {
  local base="${PROJECT_ROOT:-$PWD}"
  TEAMWORK_PLUGIN_RUNTIME=1 \
  TEAMWORK_CODEX_ROUTING="$CODEX_ROUTING_ACTION" \
  TEAMWORK_NOTIFICATIONS_ACTION="$NOTIFICATIONS_ACTION" \
  "$ROOT/scripts/init-project.sh" \
    "--$INSTALL_MODE" \
    --profile "$CODEX_PROFILE" \
    --project-root "$base"
}

install_codex_agents_home() {
  configure_codex_routing
  install_codex_agent_set "$(codex_home_path)/agents" "user"
}

install_cursor_agents_home() {
  install_cursor_agent_set "$HOME/.cursor/agents" "user Cursor"
}

install_claude_agents_home() {
  install_claude_agent_set "$HOME/.claude/agents" "user Claude Code"
}
