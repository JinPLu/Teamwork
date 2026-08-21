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
  local main_model main_effort
  if [[ "$CODEX_ROUTING_ACTION" == "preserve" ]]; then
    echo "Codex custom-agent routing: preserved (--no-codex-routing)"
    return 0
  fi
  if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 is required to configure Codex custom-agent routing." >&2
    return 1
  fi
  read -r main_model main_effort < <(codex_default_profile_values)
  python3 "$ROOT/scripts/configure-codex-routing.py" \
    --apply \
    --default-model "$main_model" \
    --default-effort "$main_effort" \
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
  local config main_model main_effort
  config="$(codex_home_path)/config.toml"
  if [[ "$CODEX_ROUTING_ACTION" == "preserve" ]]; then
    if ! python3 "$ROOT/scripts/configure-codex-routing.py" --check --config "$config" >/dev/null 2>&1; then
      echo "Codex static routing is not configured; --no-codex-routing cannot preserve a missing or disabled multi_agent feature." >&2
      return 1
    fi
    return 0
  fi
  read -r main_model main_effort < <(codex_default_profile_values)
  python3 "$ROOT/scripts/configure-codex-routing.py" \
    --dry-run \
    --default-model "$main_model" \
    --default-effort "$main_effort" \
    --config "$config" >/dev/null
}

install_codex() {
  local skill_root="$CODEX_USER_SKILLS_ROOT"
  local agent_root="$(codex_home_path)/agents"
  local main_model main_effort
  remove_legacy_plugin_activation
  preflight_teamwork_skill_root "$CODEX_USER_SKILLS_ROOT" "Codex user skill root"
  preflight_legacy_codex_skills "$(codex_home_path)/skills"
  preflight_owned_legacy_cleanup "$(codex_home_path)/skills"
  preflight_codex_agent_set "$agent_root"
  preflight_codex_global_policy
  preflight_codex_notifications
  if [[ "$CODEX_ROUTING_ACTION" == "configure" ]]; then
    read -r main_model main_effort < <(codex_default_profile_values)
    python3 "$ROOT/scripts/configure-codex-routing.py" \
      --dry-run \
      --default-model "$main_model" \
      --default-effort "$main_effort" \
      --config "$(codex_home_path)/config.toml" >/dev/null
  fi
  configure_codex_routing
  install_codex_skill_set
  install_codex_agent_set "$agent_root" "user"
  echo "Codex static skills/agents: installed"
  install_codex_global_policy
  configure_user_notifications codex
  write_source_pointer --host codex
}

install_cursor() {
  local skill_root="$HOME/.cursor/skills"
  local agent_root="$HOME/.cursor/agents"
  local claude_skill_root="$HOME/.claude/skills"
  preflight_teamwork_skill_root "$skill_root" "Cursor skill root"
  preflight_agent_destination "$agent_root" md Cursor "${CURSOR_AGENTS[@]}"
  install_skill_set "$skill_root" "Cursor" "$CURSOR_SKILL_PROFILE_TOKEN" "cursor"
  install_cursor_agent_set "$agent_root" "user Cursor"
  echo "Cursor static skills/agents: installed"
  if teamwork_skill_root_has_markers "$claude_skill_root"; then
    install_skill_set "$claude_skill_root" "Claude Code" "$CLAUDE_SKILL_PROFILE_TOKEN" "claude"
    echo "Both Teamwork skill roots were refreshed; when both exist, which copy wins is not guaranteed."
  fi
  echo "Cursor global policy activation: separate; this installer cannot reach Cursor's user-rule store."
  echo "Exact action: run ./install.sh cursor-policy, then have a Cursor Agent add or update that block as one user rule and confirm it with a rule list readback."
  write_source_pointer --host cursor
}

install_claude() {
  local skill_root="$HOME/.claude/skills"
  local agent_root="$HOME/.claude/agents"
  preflight_teamwork_skill_root "$skill_root" "Claude Code skill root"
  preflight_agent_destination "$agent_root" md "Claude Code" "${CLAUDE_AGENTS[@]}"
  preflight_claude_global_policy
  preflight_user_notifications claude
  install_skill_set "$skill_root" "Claude Code" "$CLAUDE_SKILL_PROFILE_TOKEN" "claude"
  install_claude_agent_set "$agent_root" "user Claude Code"
  echo "Claude static skills/agents: installed"
  install_claude_global_policy
  configure_user_notifications claude
  write_source_pointer --host claude
}

install_all() {
  local codex_skill_root="$CODEX_USER_SKILLS_ROOT"
  local codex_agent_root="$(codex_home_path)/agents"
  local cursor_skill_root="$HOME/.cursor/skills"
  local cursor_agent_root="$HOME/.cursor/agents"
  local claude_skill_root="$HOME/.claude/skills"
  local claude_agent_root="$HOME/.claude/agents"
  local main_model main_effort
  remove_legacy_plugin_activation
  preflight_teamwork_skill_root "$CODEX_USER_SKILLS_ROOT" "Codex user skill root"
  preflight_legacy_codex_skills "$(codex_home_path)/skills"
  preflight_owned_legacy_cleanup "$(codex_home_path)/skills"
  preflight_teamwork_skill_root "$HOME/.cursor/skills" "Cursor skill root"
  preflight_teamwork_skill_root "$HOME/.claude/skills" "Claude Code skill root"
  preflight_codex_agent_set "$codex_agent_root"
  preflight_agent_destination "$cursor_agent_root" md Cursor "${CURSOR_AGENTS[@]}"
  preflight_agent_destination "$claude_agent_root" md "Claude Code" "${CLAUDE_AGENTS[@]}"
  preflight_codex_global_policy
  preflight_claude_global_policy
  preflight_codex_notifications
  preflight_user_notifications claude
  if [[ "$CODEX_ROUTING_ACTION" == "configure" ]]; then
    read -r main_model main_effort < <(codex_default_profile_values)
    python3 "$ROOT/scripts/configure-codex-routing.py" \
      --dry-run \
      --default-model "$main_model" \
      --default-effort "$main_effort" \
      --config "$(codex_home_path)/config.toml" >/dev/null
  fi
  configure_codex_routing
  install_codex_skill_set
  install_codex_agent_set "$codex_agent_root" "user"
  echo "Codex static skills/agents: installed"
  install_codex_global_policy
  configure_user_notifications codex
  install_skill_set "$cursor_skill_root" "Cursor" "$CURSOR_SKILL_PROFILE_TOKEN" "cursor"
  install_cursor_agent_set "$cursor_agent_root" "user Cursor"
  echo "Cursor static skills/agents: installed"
  echo "Cursor global policy activation: separate; this installer cannot reach Cursor's user-rule store."
  echo "Exact action: run ./install.sh cursor-policy, then have a Cursor Agent add or update that block as one user rule and confirm it with a rule list readback."
  install_skill_set "$claude_skill_root" "Claude Code" "$CLAUDE_SKILL_PROFILE_TOKEN" "claude"
  install_claude_agent_set "$claude_agent_root" "user Claude Code"
  echo "Claude static skills/agents: installed"
  install_claude_global_policy
  configure_user_notifications claude
  write_source_pointer --host codex --host cursor --host claude
}

install_update() {
  install_codex
}

init_project() {
  local base="${PROJECT_ROOT:-$PWD}"
  TEAMWORK_CODEX_ROUTING="$CODEX_ROUTING_ACTION" \
  TEAMWORK_NOTIFICATIONS_ACTION="$NOTIFICATIONS_ACTION" \
  "$ROOT/scripts/init-project.sh" \
    --project-root "$base"
  write_source_pointer
}

install_codex_agents_home() {
  local agent_root="$(codex_home_path)/agents"
  preflight_codex_agent_set "$agent_root"
  configure_codex_routing
  install_codex_agent_set "$agent_root" "user"
  write_source_pointer --host codex
}

install_cursor_agents_home() {
  local agent_root="$HOME/.cursor/agents"
  preflight_agent_destination "$agent_root" md Cursor "${CURSOR_AGENTS[@]}"
  install_cursor_agent_set "$agent_root" "user Cursor"
  write_source_pointer --host cursor
}

install_claude_agents_home() {
  local agent_root="$HOME/.claude/agents"
  preflight_agent_destination "$agent_root" md "Claude Code" "${CLAUDE_AGENTS[@]}"
  install_claude_agent_set "$agent_root" "user Claude Code"
  write_source_pointer --host claude
}
