write_teamwork_global_policy_body() {
  cat <<'POLICY'
Clear work stays native. Answer, inspect, use tools, implement, and integrate
directly when intent and scope are clear; importance, complexity, or risk alone
does not activate a Teamwork workflow.

Be epistemically honest. Distinguish observation, inference, unknown, and
completed work. Never claim an unperformed method, tool call, test, effect, or
result.

Calibrate verification and defenses to the credible risk and the claim being
made. Prefer direct outcome evidence. Tests and hashes may support a claim but
never substitute for semantic correctness.

Routing: Collaborate for explicit discussion, co-design, brainstorming,
comparison, thinking together, or an unformed intent or preference that can
materially change the result. Research for broad or deep external multi-source
work; routine lookup stays native. Debug for unknown-cause failures. Plan for a
clear or selected direction. Review for a finished candidate, including a plan.
Goal only when the user explicitly asks to persist until a verifiable outcome.
Init creates current project context. Update refreshes global installation and,
with an exact project root, migrates every Teamwork document in that project;
without a root, report project migration as pending. Local evidence routes to
Explorer without a public Explore skill. Strict adversarial work routes to Challenger.

After routing, preserve role boundaries and report an unavailable required role
instead of impersonating it. Root owns Collaborate, Goal, and user dialogue.
Researcher gathers external evidence; Explorer gathers local read-only evidence;
Debugger diagnoses; Challenger challenges; Planner plans; Reviewer reviews;
Worker makes bounded requested changes and preserves unrelated work. Use as many
agents as the host and task justify; Teamwork defines no numeric dispatch caps.

Writer maintains one live document per task when reusable content first appears,
when evidence, decisions, conclusions, or next steps materially change, and at
completion. Skills specify semantic content; Writer chooses and maintains the
document without changing facts, user decisions, authority, or completion.
Storage, migration, transaction, CAS, readback, and integrity details stay out
of model-facing workflow instructions.

Normal runtime accepts only the current document format. Older Teamwork project
records enter only through Update migration, never through compatibility reads.

Do not repeat answered questions. Contribute synthesis or a recommendation
before asking a material question, and ask only when the answer changes the next
step. Consume host and tool permissions as they exist; Teamwork creates no
separate authorization protocol.
POLICY
}

write_teamwork_codex_global_policy() {
  cat <<'POLICY'
<!-- TEAMWORK_CODEX_GLOBAL_START -->
## Teamwork Codex Global Policy
POLICY
  write_teamwork_global_policy_body
  cat <<'POLICY'
Codex: material questions->request_user_input; call limits=transport only.
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

Enable MCP in Cursor. Prefer `codegraph_*`; GPU via Broker.
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
  local dest_dir
  dest_dir="$(codex_home_path)"
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

preflight_codex_global_policy() {
  local dest_dir dest parent
  dest_dir="$(codex_home_path)"
  dest="$dest_dir/AGENTS.md"
  parent="$(dirname "$dest_dir")"

  while [[ ! -e "$parent" && "$parent" != "/" ]]; do
    parent="$(dirname "$parent")"
  done

  if [[ -e "$dest_dir" && ! -d "$dest_dir" ]]; then
    echo "Codex home is not a directory: $dest_dir" >&2
    return 1
  fi
  if [[ -e "$dest" && ! -f "$dest" ]]; then
    echo "Codex global policy path is not a regular file: $dest" >&2
    return 1
  fi
  if [[ -f "$dest" && ( ! -r "$dest" || ! -w "$dest" ) ]]; then
    echo "Codex global policy is not readable and writable: $dest" >&2
    return 1
  fi
  if [[ -d "$dest_dir" && ( ! -w "$dest_dir" || ! -x "$dest_dir" ) ]]; then
    echo "Codex home is not writable: $dest_dir" >&2
    return 1
  fi
  if [[ ! -e "$dest_dir" && ( ! -d "$parent" || ! -w "$parent" || ! -x "$parent" ) ]]; then
    echo "Codex home ancestor is not writable: $parent" >&2
    return 1
  fi
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
