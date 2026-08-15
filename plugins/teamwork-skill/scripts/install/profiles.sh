codex_agent_performance_values() {
  local agent="$1"
  case "$agent" in
    teamwork-explorer)
      printf '%s %s\n' "gpt-5.6-terra" "high"
      ;;
    teamwork-researcher|teamwork-planner)
      printf '%s %s\n' "gpt-5.6-terra" "xhigh"
      ;;
    teamwork-worker)
      printf '%s %s\n' "gpt-5.6-sol" "medium"
      ;;
    teamwork-writer)
      printf '%s %s\n' "gpt-5.6-luna" "high"
      ;;
    teamwork-debugger)
      printf '%s %s\n' "gpt-5.6-sol" "xhigh"
      ;;
    teamwork-challenger)
      printf '%s %s\n' "gpt-5.6-sol" "high"
      ;;
    teamwork-reviewer)
      printf '%s %s\n' "gpt-5.6-sol" "xhigh"
      ;;
    *)
      echo "Unsupported Codex role: $agent" >&2
      return 1
      ;;
  esac
}

codex_default_profile_values() {
  case "$CODEX_PROFILE" in
    performance-first)
      printf '%s %s\n' "gpt-5.6-terra" "xhigh"
      ;;
    cost-first)
      printf '%s %s\n' "gpt-5.6-luna" "high"
      ;;
    *)
      echo "Unsupported Codex main-thread profile: $CODEX_PROFILE" >&2
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
    cost-first:teamwork-researcher|cost-first:teamwork-debugger|cost-first:teamwork-planner|cost-first:teamwork-reviewer)
      printf '%s %s\n' "gpt-5.6-luna" "xhigh"
      ;;
    cost-first:teamwork-explorer|cost-first:teamwork-worker|cost-first:teamwork-writer|cost-first:teamwork-challenger)
      printf '%s %s\n' "gpt-5.6-luna" "high"
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
    performance-first:writer|cost-first:researcher|cost-first:explorer|cost-first:worker|cost-first:writer)
      printf '%s %s\n' "haiku" "medium"
      ;;
    performance-first:debugger|performance-first:challenger|performance-first:planner|cost-first:debugger|cost-first:challenger|cost-first:planner)
      printf '%s %s\n' "opus" "high"
      ;;
    performance-first:reviewer|cost-first:reviewer)
      printf '%s %s\n' "opus" "max"
      ;;
    *)
      echo "Unsupported Claude role/profile mapping: $CODEX_PROFILE:$agent" >&2
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
  require_single_profile_field "$source" '^model_reasoning_effort = "(low|medium|high|xhigh|max)"$' "Codex effort"
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

  require_single_profile_field "$source" '^name: [a-z-]+$' "Cursor name"
  require_single_profile_field "$source" '^readonly: (true|false)$' "Cursor readonly"
  grep -Fqx "name: $agent" "$source" || {
    echo "Cursor profile identity does not match $agent: $source" >&2
    return 1
  }
  # Omitting model uses Cursor's default (inherit / parent unless Task
  # overrides). A pinned slug would override that and can name a model the
  # host no longer offers.
  if grep -Eq '^model:' "$source"; then
    echo "Cursor profile must not pin a model: $source" >&2
    return 1
  fi
  install_agent_file "$source" "$dest"
}


install_claude_agent_set() {
  local dest_root="$1"
  local label="$2"
  local agent

  mkdir -p "$dest_root"
  remove_retired_agent_files claude "$dest_root" "${RETIRED_CLAUDE_AGENTS[@]}"
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
  remove_retired_agent_files cursor "$dest_root" "${RETIRED_CURSOR_AGENTS[@]}"
  for agent in "${CURSOR_AGENTS[@]}"; do
    install_cursor_agent_file \
      "$ROOT/templates/cursor-agents/$agent.md" \
      "$dest_root/$agent.md" \
      "$agent"
  done

  echo "Installed $label Cursor agents under: $dest_root ($INSTALL_MODE, inherit models)"
}

install_codex_agent_set() {
  local dest_root="$1"
  local label="$2"
  local agent

  mkdir -p "$dest_root"
  remove_retired_agent_files codex "$dest_root" "${RETIRED_CODEX_AGENTS[@]}"
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
    && grep -Eq 'You are (the )?Teamwork ' "$path"
}

teamwork_markdown_agent_file_is_recognized() {
  local path="$1"
  local agent="$2"
  [[ -f "$path" ]] \
    && grep -Fqx "name: $agent" "$path" \
    && grep -Eq '^You are (the )?Teamwork ' "$path"
}

remove_retired_agent_files() {
  local platform="$1"
  local root="$2"
  shift 2
  local agent extension path

  case "$platform" in
    codex) extension=toml ;;
    cursor|claude) extension=md ;;
    *) return 1 ;;
  esac

  for agent in "$@"; do
    path="$root/$agent.$extension"
    [[ -e "$path" || -L "$path" ]] || continue
    if [[ "$platform" == "codex" ]] && teamwork_codex_agent_file_is_recognized "$path" "$agent"; then
      rm -f "$path"
      echo "Removed retired Teamwork agent: $path"
    elif [[ "$platform" != "codex" ]] && teamwork_markdown_agent_file_is_recognized "$path" "$agent"; then
      rm -f "$path"
      echo "Removed retired Teamwork agent: $path"
    else
      echo "Preserved unrecognized retired agent file: $path" >&2
    fi
  done
}

preflight_codex_agent_set() {
  local dest_root="$1"
  local agent dest

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
