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

preflight_user_notifications() {
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
      return 1
      ;;
  esac
  if ! python3 "$ROOT/scripts/configure-notifications.py" status \
    --config "$config" --notifier "$dest" >/dev/null 2>&1; then
    echo "$platform notification configuration is not safe to update: $config" >&2
    return 1
  fi
  if [[ -e "$dest" && ! -f "$dest" ]]; then
    echo "$platform notification runtime is not a regular file: $dest" >&2
    return 1
  fi
}

preflight_codex_notifications() {
  preflight_user_notifications codex
}

preflight_claude_global_policy() {
  local dest_dir="$HOME/.claude"
  local dest="$dest_dir/CLAUDE.md"
  local parent
  parent="$(dirname "$dest_dir")"

  while [[ ! -e "$parent" && "$parent" != "/" ]]; do
    parent="$(dirname "$parent")"
  done

  if [[ -e "$dest_dir" && ! -d "$dest_dir" ]]; then
    echo "Claude home is not a directory: $dest_dir" >&2
    return 1
  fi
  if [[ -e "$dest" && ! -f "$dest" ]]; then
    echo "Claude global policy path is not a regular file: $dest" >&2
    return 1
  fi
  if [[ -f "$dest" && ( ! -r "$dest" || ! -w "$dest" ) ]]; then
    echo "Claude global policy is not readable and writable: $dest" >&2
    return 1
  fi
  if [[ -d "$dest_dir" && ( ! -w "$dest_dir" || ! -x "$dest_dir" ) ]]; then
    echo "Claude home is not writable: $dest_dir" >&2
    return 1
  fi
  if [[ ! -e "$dest_dir" && ( ! -d "$parent" || ! -w "$parent" || ! -x "$parent" ) ]]; then
    echo "Claude home ancestor is not writable: $parent" >&2
    return 1
  fi
}

preflight_codex_routing() {
  local config
  config="$(codex_home_path)/config.toml"
  if [[ "$CODEX_ROUTING_ACTION" == "preserve" ]]; then
    if ! python3 "$ROOT/scripts/configure-codex-routing.py" --check --config "$config" >/dev/null 2>&1; then
      echo "Codex routing is not ready; plugin activation cannot preserve a missing or disabled multi_agent feature." >&2
      return 1
    fi
    return 0
  fi
  python3 "$ROOT/scripts/configure-codex-routing.py" --dry-run --config "$config" >/dev/null
}

preflight_plugin_codex_bootstrap() {
  local code_home legacy_root activation_profile="" skill_profile=""
  code_home="$(codex_home_path)"
  legacy_root="$code_home/skills"

  preflight_plugin_runtime
  if plugin_activation_is_present \
    && [[ "$(plugin_activation_version)" == "3.4.2" ]]; then
    activation_profile="$(plugin_activation_profile)"
    PLUGIN_V342_AGENT_PROFILE="$activation_profile"
  fi
  preflight_teamwork_skill_root "$CODEX_USER_SKILLS_ROOT" "Legacy Codex user skill root"
  preflight_owned_legacy_cleanup "$CODEX_USER_SKILLS_ROOT"
  if [[ "$legacy_root" != "$CODEX_USER_SKILLS_ROOT" ]]; then
    preflight_legacy_codex_skills "$legacy_root"
    preflight_owned_legacy_cleanup "$legacy_root"
  fi
  if [[ -f "$CODEX_USER_SKILLS_ROOT/.teamwork-version" ]] \
    && [[ "$(tr -d '[:space:]' < "$CODEX_USER_SKILLS_ROOT/.teamwork-version")" == "3.4.2" ]]; then
    PLUGIN_V342_SKILL_ROOT="$CODEX_USER_SKILLS_ROOT"
  elif [[ -f "$legacy_root/.teamwork-version" ]] \
    && [[ "$(tr -d '[:space:]' < "$legacy_root/.teamwork-version")" == "3.4.2" ]]; then
    PLUGIN_V342_SKILL_ROOT="$legacy_root"
  fi
  if [[ -n "$PLUGIN_V342_SKILL_ROOT" ]]; then
    skill_profile="$(v342_agent_profile "$PLUGIN_V342_SKILL_ROOT")"
    if [[ -n "$activation_profile" && "$activation_profile" != "$skill_profile" ]]; then
      echo "The v3.4.2 plugin activation profile does not match the legacy Skill profile; refusing to migrate either installation." >&2
      return 1
    fi
    PLUGIN_V342_AGENT_PROFILE="$skill_profile"
    preflight_v342_agent_set codex "$code_home/agents" "$PLUGIN_V342_SKILL_ROOT"
    preflight_v342_managed_policy codex "$code_home/AGENTS.md" "$PLUGIN_V342_SKILL_ROOT"
  elif [[ -n "$PLUGIN_V342_AGENT_PROFILE" ]]; then
    preflight_v342_agent_profile codex "$code_home/agents" "$PLUGIN_V342_AGENT_PROFILE"
    preflight_v342_managed_policy_file codex "$code_home/AGENTS.md"
  fi
  if [[ "$V342_CODEX_AGENTS_PREFLIGHTED" == "1" ]]; then
    preflight_codex_agent_set "$code_home/agents" "$PLUGIN_V342_AGENT_PROFILE"
  else
    preflight_codex_agent_set "$code_home/agents"
  fi
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
    remove_legacy_codex_router_copy "$legacy_root"
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
  local skill_root="$CODEX_USER_SKILLS_ROOT"
  local agent_root="$(codex_home_path)/agents"
  if plugin_activation_is_present; then
    echo "Teamwork Codex plugin activation is present. Legacy ./install.sh codex will not copy duplicate skills; start a new Codex task and run \$teamwork-update instead." >&2
    return 1
  fi
  preflight_teamwork_skill_root "$CODEX_USER_SKILLS_ROOT" "Codex user skill root"
  preflight_legacy_codex_skills "$(codex_home_path)/skills"
  preflight_owned_legacy_cleanup "$(codex_home_path)/skills"
  preflight_v342_agent_set codex "$agent_root" "$skill_root"
  preflight_v342_managed_policy codex "$(codex_home_path)/AGENTS.md" "$skill_root"
  if [[ "$V342_CODEX_AGENTS_PREFLIGHTED" == "1" ]]; then
    preflight_codex_agent_set "$agent_root" "$(v342_agent_profile "$skill_root")"
  else
    preflight_codex_agent_set "$agent_root"
  fi
  preflight_codex_global_policy
  preflight_codex_notifications
  if [[ "$CODEX_ROUTING_ACTION" == "configure" ]]; then
    python3 "$ROOT/scripts/configure-codex-routing.py" \
      --dry-run --config "$(codex_home_path)/config.toml" >/dev/null
  fi
  remove_v342_agent_set codex "$agent_root" "$skill_root"
  configure_codex_routing
  install_codex_skill_set
  install_codex_agent_set "$agent_root" "user"
  install_codex_global_policy
  configure_user_notifications codex
}

install_plugin_codex_bootstrap() {
  local code_home
  code_home="$(codex_home_path)"
  preflight_plugin_codex_bootstrap
  preflight_legacy_codex_skills "$code_home/skills"
  if [[ -n "$PLUGIN_V342_SKILL_ROOT" ]]; then
    remove_v342_agent_set codex "$code_home/agents" "$PLUGIN_V342_SKILL_ROOT"
  elif [[ -n "$PLUGIN_V342_AGENT_PROFILE" ]]; then
    remove_v342_agent_profile codex "$code_home/agents" "$PLUGIN_V342_AGENT_PROFILE"
  fi
  configure_codex_routing
  install_codex_agent_set "$code_home/agents" "plugin"
  install_codex_global_policy
  configure_user_notifications codex
  remove_plugin_legacy_skill_copies
  write_plugin_activation
  echo "Teamwork full Codex setup is ready. Restart Codex; if notifications are enabled, run /hooks and trust only Teamwork Stop and PermissionRequest."
}

configure_cursor_mcp_install() {
  if [[ "$CURSOR_MCP_ACTION" == "skip" ]]; then
    echo "Cursor MCP: skipped (--no-mcp)"
    return 0
  fi
  python3 "$ROOT/scripts/install/configure_cursor_mcp.py" --apply
  echo "Cursor MCP: registered codegraph and gpu-broker in ~/.cursor/mcp.json"
  echo "Enable them in Cursor Settings -> MCP if prompted."
}

install_cursor_mcp_home() {
  configure_cursor_mcp_install
}

install_cursor() {
  local skill_root="$HOME/.cursor/skills"
  local agent_root="$HOME/.cursor/agents"
  preflight_teamwork_skill_root "$skill_root" "Cursor skill root"
  preflight_v342_agent_set cursor "$agent_root" "$skill_root"
  preflight_agent_destination "$agent_root" md Cursor "${CURSOR_AGENTS[@]}"
  remove_v342_agent_set cursor "$agent_root" "$skill_root"
  install_skill_set "$skill_root" "Cursor"
  install_cursor_agent_set "$agent_root" "user Cursor"
  configure_cursor_mcp_install
  echo "Cursor User Rules: run ./install.sh cursor-policy-copy (or cursor-policy) and paste into Cursor Settings -> Rules -> User Rules."
}

install_claude() {
  local skill_root="$HOME/.claude/skills"
  local agent_root="$HOME/.claude/agents"
  preflight_teamwork_skill_root "$skill_root" "Claude Code skill root"
  preflight_v342_agent_set claude "$agent_root" "$skill_root"
  preflight_agent_destination "$agent_root" md "Claude Code" "${CLAUDE_AGENTS[@]}"
  preflight_v342_managed_policy claude "$HOME/.claude/CLAUDE.md" "$skill_root"
  preflight_claude_global_policy
  preflight_user_notifications claude
  remove_v342_agent_set claude "$agent_root" "$skill_root"
  install_skill_set "$skill_root" "Claude Code"
  install_claude_agent_set "$agent_root" "user Claude Code"
  install_claude_global_policy
  configure_user_notifications claude
}

install_all() {
  local codex_skill_root="$CODEX_USER_SKILLS_ROOT"
  local codex_agent_root="$(codex_home_path)/agents"
  local cursor_skill_root="$HOME/.cursor/skills"
  local cursor_agent_root="$HOME/.cursor/agents"
  local claude_skill_root="$HOME/.claude/skills"
  local claude_agent_root="$HOME/.claude/agents"
  if plugin_activation_is_present; then
    echo "Teamwork Codex plugin activation is present. Legacy ./install.sh all will not copy duplicate skills; start a new Codex task and run \$teamwork-update instead." >&2
    return 1
  fi
  preflight_teamwork_skill_root "$CODEX_USER_SKILLS_ROOT" "Codex user skill root"
  preflight_legacy_codex_skills "$(codex_home_path)/skills"
  preflight_owned_legacy_cleanup "$(codex_home_path)/skills"
  preflight_teamwork_skill_root "$HOME/.cursor/skills" "Cursor skill root"
  preflight_teamwork_skill_root "$HOME/.claude/skills" "Claude Code skill root"
  preflight_v342_agent_set codex "$codex_agent_root" "$codex_skill_root"
  preflight_v342_agent_set cursor "$cursor_agent_root" "$cursor_skill_root"
  preflight_v342_agent_set claude "$claude_agent_root" "$claude_skill_root"
  preflight_v342_managed_policy codex "$(codex_home_path)/AGENTS.md" "$codex_skill_root"
  preflight_v342_managed_policy claude "$HOME/.claude/CLAUDE.md" "$claude_skill_root"
  if [[ "$V342_CODEX_AGENTS_PREFLIGHTED" == "1" ]]; then
    preflight_codex_agent_set "$codex_agent_root" "$(v342_agent_profile "$codex_skill_root")"
  else
    preflight_codex_agent_set "$codex_agent_root"
  fi
  preflight_agent_destination "$cursor_agent_root" md Cursor "${CURSOR_AGENTS[@]}"
  preflight_agent_destination "$claude_agent_root" md "Claude Code" "${CLAUDE_AGENTS[@]}"
  preflight_codex_global_policy
  preflight_claude_global_policy
  preflight_codex_notifications
  preflight_user_notifications claude
  if [[ "$CODEX_ROUTING_ACTION" == "configure" ]]; then
    python3 "$ROOT/scripts/configure-codex-routing.py" \
      --dry-run --config "$(codex_home_path)/config.toml" >/dev/null
  fi

  remove_v342_agent_set codex "$codex_agent_root" "$codex_skill_root"
  remove_v342_agent_set cursor "$cursor_agent_root" "$cursor_skill_root"
  remove_v342_agent_set claude "$claude_agent_root" "$claude_skill_root"
  configure_codex_routing
  install_codex_skill_set
  install_codex_agent_set "$codex_agent_root" "user"
  install_codex_global_policy
  configure_user_notifications codex
  install_skill_set "$cursor_skill_root" "Cursor"
  install_cursor_agent_set "$cursor_agent_root" "user Cursor"
  configure_cursor_mcp_install
  echo "Cursor User Rules: run ./install.sh cursor-policy-copy (or cursor-policy) and paste into Cursor Settings -> Rules -> User Rules."
  install_skill_set "$claude_skill_root" "Claude Code"
  install_claude_agent_set "$claude_agent_root" "user Claude Code"
  install_claude_global_policy
  configure_user_notifications claude
}

init_project() {
  local base="${PROJECT_ROOT:-$PWD}"
  TEAMWORK_CODEX_ROUTING="$CODEX_ROUTING_ACTION" \
  TEAMWORK_NOTIFICATIONS_ACTION="$NOTIFICATIONS_ACTION" \
  TEAMWORK_INIT_CURSOR_MCP="${TEAMWORK_INIT_CURSOR_MCP:-0}" \
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
  local skill_root="$CODEX_USER_SKILLS_ROOT"
  local agent_root="$(codex_home_path)/agents"
  preflight_v342_agent_set codex "$agent_root" "$skill_root"
  if [[ "$V342_CODEX_AGENTS_PREFLIGHTED" != "1" ]]; then
    preflight_codex_agent_set "$agent_root"
  fi
  remove_v342_agent_set codex "$agent_root" "$skill_root"
  configure_codex_routing
  install_codex_agent_set "$agent_root" "user"
}

install_cursor_agents_home() {
  local skill_root="$HOME/.cursor/skills"
  local agent_root="$HOME/.cursor/agents"
  preflight_v342_agent_set cursor "$agent_root" "$skill_root"
  preflight_agent_destination "$agent_root" md Cursor "${CURSOR_AGENTS[@]}"
  remove_v342_agent_set cursor "$agent_root" "$skill_root"
  install_cursor_agent_set "$agent_root" "user Cursor"
}

install_claude_agents_home() {
  local skill_root="$HOME/.claude/skills"
  local agent_root="$HOME/.claude/agents"
  preflight_v342_agent_set claude "$agent_root" "$skill_root"
  preflight_agent_destination "$agent_root" md "Claude Code" "${CLAUDE_AGENTS[@]}"
  remove_v342_agent_set claude "$agent_root" "$skill_root"
  install_claude_agent_set "$agent_root" "user Claude Code"
}
