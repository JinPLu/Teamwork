write_teamwork_global_policy_body() {
  cat <<'POLICY'
Work within the request. Read-only: no write/effect authority.
No-files/off-record/read-only/no-writes override effects. Inspect before asking:
discoverable/safe/reversible -> act; one missing user value -> Root alone asks
one bounded decision batch, then resume; unformed intent/preference -> Collaborate.
Pause only dependent work.
Result first; clear/stable/relevant; report unsaved/blocked.

Native fast path: tiny reads/explanations/commands/integration/authorized implementation.
Named workflows: Research->Researcher,
Explore->Explorer, Debug->Debugger, Plan->Planner, Review->Reviewer,
Plan Review->Plan Reviewer, Init/Update->Explorer then Worker;
Collaborate/Goal Root-owned. Unavailable role/isolation = capability-blocked;
no role/method fallback. Default one child; daily cap4; 5-8 only explicit
adversarial/release with host-support.

Discuss/brainstorm/stress-test activates Collaborate: dialogue|brainstorm.
Contribute synthesis/tension/options+recommendation first. Ask only
if useful: open prose or host-native 2-3 finite choices. Challenge moves
global->boundary->detail. Adversarial is challenge, not mode. Public/release/
migration/security/destructive/cross-platform or question-first
activates Collaborate. Leaves return exact gap/reclassification; never
ask/activate/expand/self-accept. One asker/owner/gap; no repeats.

Writable initialized projects default-save substantive case-v2 workflow
checkpoints/results via frozen Writer packet+transaction+readback, plus qualifying
execution. Only tiny-native/check-only/one-shot work is unsaved.
Legacy-v1 read-only; no
artifact/collaborate/goal/manual/report/
memory write fallback. Missing memory/Writer/authority/consumer/route:
deliver core result, report unsaved/blocked. Code-coupled text stays
implementer-owned.

Ground claims, separate observation/inference, invent no success, preserve dirty
work. Prefer canonical owner/pattern+built-ins/dependencies+minimal logic.
Verify real path/focused evidence; tests never replace it. Reviewers
read-only; one sealed review + repair-batch/delta-recheck at requested/risk gates.
Stop when result/boundaries are observed.
POLICY
}

write_teamwork_codex_global_policy() {
  cat <<'POLICY'
<!-- TEAMWORK_CODEX_GLOBAL_START -->
## Teamwork Codex Global Policy
POLICY
  write_teamwork_global_policy_body
  cat <<'POLICY'
Codex: bounded choices request_user_input; open prose.
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
