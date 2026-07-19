codex_agent_performance_values() {
  local agent="$1"
  case "$agent" in
    teamwork-researcher|teamwork-explorer|teamwork-debugger|teamwork-planner|teamwork-worker)
      printf '%s %s\n' "gpt-5.5" "high"
      ;;
    teamwork-designer|teamwork-plan-reviewer)
      printf '%s %s\n' "gpt-5.6-sol" "high"
      ;;
    teamwork-reviewer)
      printf '%s %s\n' "gpt-5.6-sol" "max"
      ;;
    *)
      echo "Unsupported Codex role: $agent" >&2
      return 1
      ;;
  esac
}

codex_agent_profile_values() {
  local agent="$1"
  case "$CODEX_PROFILE:$agent" in
    performance-first:*)
      codex_agent_performance_values "$agent"
      ;;
    cost-first:teamwork-researcher|cost-first:teamwork-explorer|cost-first:teamwork-debugger|cost-first:teamwork-planner|cost-first:teamwork-worker)
      printf '%s %s\n' "gpt-5.5" "medium"
      ;;
    cost-first:teamwork-designer)
      printf '%s %s\n' "gpt-5.6-sol" "medium"
      ;;
    cost-first:teamwork-plan-reviewer|cost-first:teamwork-reviewer)
      printf '%s %s\n' "gpt-5.6-sol" "high"
      ;;
    *)
      echo "Unsupported Codex role/profile mapping: $CODEX_PROFILE:$agent" >&2
      return 1
      ;;
  esac
}

claude_agent_profile_values() {
  local agent="$1"
  case "$CODEX_PROFILE:$agent" in
    performance-first:researcher|performance-first:explorer|performance-first:worker)
      printf '%s %s\n' "sonnet" "medium"
      ;;
    cost-first:researcher|cost-first:explorer|cost-first:worker)
      printf '%s %s\n' "haiku" "medium"
      ;;
    performance-first:debugger|performance-first:designer|performance-first:planner|cost-first:debugger|cost-first:designer|cost-first:planner)
      printf '%s %s\n' "opus" "high"
      ;;
    performance-first:plan-reviewer|performance-first:reviewer|cost-first:plan-reviewer|cost-first:reviewer)
      printf '%s %s\n' "opus" "max"
      ;;
    *)
      echo "Unsupported Claude role/profile mapping: $CODEX_PROFILE:$agent" >&2
      return 1
      ;;
  esac
}

cursor_agent_profile_values() {
  local agent="$1"
  case "$CODEX_PROFILE:$agent" in
    cost-first:researcher|cost-first:explorer|cost-first:worker)
      printf '%s\n' "composer-2.5"
      ;;
    performance-first:worker)
      printf '%s\n' "composer-2.5-fast"
      ;;
    performance-first:researcher|performance-first:explorer)
      printf '%s\n' "claude-sonnet-4-6"
      ;;
    performance-first:debugger|performance-first:designer|performance-first:planner|performance-first:plan-reviewer|performance-first:reviewer|cost-first:debugger|cost-first:designer|cost-first:planner|cost-first:plan-reviewer|cost-first:reviewer)
      printf '%s\n' "claude-opus-4-8-thinking-high"
      ;;
    *)
      echo "Unsupported Cursor role/profile mapping: $CODEX_PROFILE:$agent" >&2
      return 1
      ;;
  esac
}

require_single_profile_field() {
  local path="$1"
  local pattern="$2"
  local label="$3"
  local count

  count="$(grep -Ec "$pattern" "$path" || true)"
  if [[ "$count" != "1" ]]; then
    echo "Invalid $label profile field in $path" >&2
    return 1
  fi
}

install_codex_agent_file() {
  local source="$1"
  local dest="$2"
  local agent="$3"
  local model effort template_model template_effort tmp expected_name

  read -r model effort < <(codex_agent_profile_values "$agent")
  read -r template_model template_effort < <(codex_agent_performance_values "$agent")
  expected_name="${agent//-/_}"
  require_single_profile_field "$source" '^name = "teamwork_[a-z_]+"$' "Codex name"
  require_single_profile_field "$source" '^model = "[^"]+"$' "Codex model"
  require_single_profile_field "$source" '^model_reasoning_effort = "(medium|high|max)"$' "Codex effort"
  require_single_profile_field "$source" '^sandbox_mode = "(read-only|workspace-write)"$' "Codex sandbox"
  grep -Fqx "name = \"$expected_name\"" "$source" || {
    echo "Codex profile identity does not match $agent: $source" >&2
    return 1
  }
  grep -Fqx "model = \"$template_model\"" "$source" \
    && grep -Fqx "model_reasoning_effort = \"$template_effort\"" "$source" || {
      echo "Codex source template does not match canonical performance mapping: $agent" >&2
      return 1
    }
  rm -f "$dest"
  mkdir -p "$(dirname "$dest")"

  if [[ "$INSTALL_MODE" == "link" && "$CODEX_PROFILE" == "performance-first" ]]; then
    grep -Fqx "model = \"$model\"" "$source"
    grep -Fqx "model_reasoning_effort = \"$effort\"" "$source"
    ln -sfn "$source" "$dest"
    return 0
  fi

  tmp="$(mktemp)"
  sed \
    -e "s/^model = .*/model = \"$model\"/" \
    -e "s/^model_reasoning_effort = .*/model_reasoning_effort = \"$effort\"/" \
    "$source" > "$tmp"
  if ! grep -Fqx "model = \"$model\"" "$tmp" \
      || ! grep -Fqx "model_reasoning_effort = \"$effort\"" "$tmp"; then
    rm -f "$tmp"
    echo "Failed to render Codex role/profile mapping: $CODEX_PROFILE:$agent" >&2
    return 1
  fi
  mv "$tmp" "$dest"
}

install_claude_agent_file() {
  local source="$1"
  local dest="$2"
  local agent="$3"
  local model effort tmp

  read -r model effort < <(claude_agent_profile_values "$agent")
  require_single_profile_field "$source" '^name: [a-z-]+$' "Claude name"
  require_single_profile_field "$source" '^tools: .+$' "Claude tools"
  require_single_profile_field "$source" '^model: (haiku|sonnet|opus)$' "Claude model"
  require_single_profile_field "$source" '^effort: (medium|high|max)$' "Claude effort"
  grep -Fqx "name: $agent" "$source" || {
    echo "Claude profile identity does not match $agent: $source" >&2
    return 1
  }
  rm -f "$dest"
  mkdir -p "$(dirname "$dest")"

  if [[ "$INSTALL_MODE" == "link" && "$CODEX_PROFILE" == "performance-first" ]]; then
    grep -Fqx "model: $model" "$source"
    grep -Fqx "effort: $effort" "$source"
    ln -sfn "$source" "$dest"
    return 0
  fi

  tmp="$(mktemp)"
  sed \
    -e "s/^model: .*/model: $model/" \
    -e "s/^effort: .*/effort: $effort/" \
    "$source" > "$tmp"
  if ! grep -Fqx "model: $model" "$tmp" || ! grep -Fqx "effort: $effort" "$tmp"; then
    rm -f "$tmp"
    echo "Failed to render Claude role/profile mapping: $CODEX_PROFILE:$agent" >&2
    return 1
  fi
  mv "$tmp" "$dest"
}

install_cursor_agent_file() {
  local source="$1"
  local dest="$2"
  local agent="$3"
  local model tmp

  read -r model < <(cursor_agent_profile_values "$agent")
  require_single_profile_field "$source" '^name: [a-z-]+$' "Cursor name"
  require_single_profile_field "$source" '^model: [a-z0-9.-]+$' "Cursor model"
  require_single_profile_field "$source" '^readonly: (true|false)$' "Cursor readonly"
  grep -Fqx "name: $agent" "$source" || {
    echo "Cursor profile identity does not match $agent: $source" >&2
    return 1
  }
  rm -f "$dest"
  mkdir -p "$(dirname "$dest")"

  if [[ "$INSTALL_MODE" == "link" && "$CODEX_PROFILE" == "performance-first" ]]; then
    grep -Fqx "model: $model" "$source"
    ln -sfn "$source" "$dest"
    return 0
  fi

  tmp="$(mktemp)"
  sed -e "s/^model: .*/model: $model/" "$source" > "$tmp"
  if ! grep -Fqx "model: $model" "$tmp"; then
    rm -f "$tmp"
    echo "Failed to render Cursor role/profile mapping: $CODEX_PROFILE:$agent" >&2
    return 1
  fi
  mv "$tmp" "$dest"
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

teamwork_codex_agent_file_is_recognized() {
  local path="$1"
  local agent="$2"
  local expected_name
  expected_name="${agent//-/_}"
  [[ -f "$path" ]] \
    && grep -q "^name = \"$expected_name\"$" "$path" \
    && grep -q 'Do not spawn or delegate\.' "$path"
}

teamwork_markdown_agent_file_is_recognized() {
  local path="$1"
  local agent="$2"
  [[ -f "$path" ]] \
    && grep -Fqx "name: $agent" "$path" \
    && grep -Eq '^You are the Teamwork .+ leaf role\.$' "$path" \
    && grep -Fq 'Do not spawn or delegate.' "$path"
}

preflight_codex_agent_set() {
  local dest_root="$1"
  local v342_profile="${2:-}"
  local v342_names=""
  local agent dest

  if [[ -n "$v342_profile" ]]; then
    v342_names="$(v342_agent_names codex "$v342_profile")"
  fi

  if [[ -e "$dest_root" && ! -d "$dest_root" ]]; then
    echo "Codex agents path is not a directory: $dest_root" >&2
    return 1
  fi
  if [[ -d "$dest_root" && ( ! -w "$dest_root" || ! -x "$dest_root" ) ]]; then
    echo "Codex agents path is not writable: $dest_root" >&2
    return 1
  fi
  for agent in "${CODEX_AGENTS[@]}"; do
    dest="$dest_root/$agent.toml"
    if [[ -e "$dest" || -L "$dest" ]]; then
      if [[ -n "$v342_names" ]] && grep -Fqx "$agent.toml" <<< "$v342_names"; then
        if [[ ! -f "$dest" || ! -w "$dest" ]]; then
          echo "Codex agent $dest is not writable." >&2
          return 1
        fi
        continue
      fi
      if ! teamwork_codex_agent_file_is_recognized "$dest" "$agent"; then
        echo "Codex agent $dest is not a recognized Teamwork-owned profile; refusing to replace it." >&2
        return 1
      fi
      if [[ ! -w "$dest" ]]; then
        echo "Codex agent $dest is not writable." >&2
        return 1
      fi
    fi
  done
}
