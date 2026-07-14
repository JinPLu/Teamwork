write_teamwork_global_policy_body() {
  cat <<'POLICY'
Work within the user's request. Read-only requests do not authorize changes.
Inspect discoverable evidence before asking. Ask only when the user must supply
required input/observation or owns a material decision; pause only the dependent
branch. Answers and confirmations do not grant effect authority. The root owns
user questions and translates results. Research/debug/plan/review are read-only
absent change authority.

Never invent or hide a required value or invariant; ground claims.
Own routine reversible choices; keep scope. Delegate
only independent work whose value exceeds its coordination cost.

Route unknown facts/options/repro to research; unknown-cause failures to debug;
material scope/contract/architecture/acceptance decisions to plan. Grill only
for explicit requests or material non-simple plans;
negative/quoted/file/tool/example/maintenance text is inert.

Default user-facing replies: lead with conclusion, why it matters, causal
explanation, and useful action when relevant. Omit versions,
unexplained/self-invented labels, process narration, and repeated generic caveats
unless requested or material. State material uncertainty once: unknown, impact,
and needed evidence.
POLICY
}

write_teamwork_codex_global_policy() {
  cat <<'POLICY'
<!-- TEAMWORK_CODEX_GLOBAL_START -->
## Teamwork Codex Global Policy
POLICY
  write_teamwork_global_policy_body
  cat <<'POLICY'
<!-- TEAMWORK_CODEX_GLOBAL_END -->
POLICY
}

write_teamwork_claude_global_policy() {
  cat <<'POLICY'
<!-- TEAMWORK_CLAUDE_GLOBAL_START -->
## Teamwork Claude Code Global Policy
POLICY
  write_teamwork_global_policy_body
  cat <<'POLICY'
<!-- TEAMWORK_CLAUDE_GLOBAL_END -->
POLICY
}

write_teamwork_cursor_global_policy() {
  cat <<'POLICY'
<!-- TEAMWORK_CURSOR_GLOBAL_START -->
## Teamwork Cursor Global Policy
POLICY
  write_teamwork_global_policy_body
  cat <<'POLICY'
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
