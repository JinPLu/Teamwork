codex_agent_profile_values() {
  local agent="$1"
  case "$CODEX_PROFILE:$agent" in
    performance-first:teamwork-explorer|gpt56-role:teamwork-explorer)
      printf '%s %s\n' "gpt-5.6-terra" "medium"
      ;;
    performance-first:teamwork-worker|gpt56-role:teamwork-worker)
      printf '%s %s\n' "gpt-5.6-sol" "medium"
      ;;
    performance-first:teamwork-designer|performance-first:teamwork-judge|performance-first:teamwork-reviewer|gpt56-role:teamwork-designer|gpt56-role:teamwork-judge|gpt56-role:teamwork-reviewer)
      printf '%s %s\n' "gpt-5.6-sol" "high"
      ;;
    performance-first:teamwork-deep-judge|performance-first:teamwork-deep-reviewer|gpt56-role:teamwork-deep-judge|gpt56-role:teamwork-deep-reviewer)
      printf '%s %s\n' "gpt-5.6-sol" "max"
      ;;
    gpt56-xhigh:*|gpt55-xhigh:*)
      printf '%s %s\n' "gpt-5.6-sol" "xhigh"
      ;;
    gpt56-high:*|gpt55-high:*)
      printf '%s %s\n' "gpt-5.6-sol" "high"
      ;;
    cost-first:teamwork-explorer|cost-first:teamwork-designer)
      printf '%s %s\n' "gpt-5.6-luna" "medium"
      ;;
    cost-first:teamwork-worker)
      printf '%s %s\n' "gpt-5.6-terra" "medium"
      ;;
    cost-first:teamwork-judge|cost-first:teamwork-reviewer)
      printf '%s %s\n' "gpt-5.6-sol" "high"
      ;;
    cost-first:teamwork-deep-judge|cost-first:teamwork-deep-reviewer)
      printf '%s %s\n' "gpt-5.6-sol" "max"
      ;;
    *)
      printf '%s %s\n' "gpt-5.6-sol" "high"
      ;;
  esac
}

claude_agent_profile_values() {
  local agent="$1"
  case "$CODEX_PROFILE:$agent" in
    gpt56-role:explore|gpt56-role:designer|gpt56-role:worker|gpt56-high:explore|gpt56-high:designer|gpt56-high:worker|gpt56-xhigh:explore|gpt56-xhigh:designer|gpt56-xhigh:worker|gpt55-high:explore|gpt55-high:designer|gpt55-high:worker|gpt55-xhigh:explore|gpt55-xhigh:designer|gpt55-xhigh:worker)
      printf '%s %s\n' "sonnet" "medium"
      ;;
    cost-first:explore|cost-first:designer|cost-first:worker)
      printf '%s %s\n' "haiku" "medium"
      ;;
    gpt56-xhigh:deep-judge|gpt56-xhigh:deep-reviewer|gpt55-xhigh:deep-judge|gpt55-xhigh:deep-reviewer)
      printf '%s %s\n' "opus" "xhigh"
      ;;
    *:deep-judge|*:deep-reviewer)
      printf '%s %s\n' "opus" "max"
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
    cost-first:explore|cost-first:designer|cost-first:worker)
      printf '%s\n' "composer-2.5"
      ;;
    *:worker)
      printf '%s\n' "composer-2.5-fast"
      ;;
    *:explore|*:designer)
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
