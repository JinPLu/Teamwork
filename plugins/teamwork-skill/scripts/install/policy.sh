write_teamwork_global_policy_body() {
  cat <<'POLICY'
Work within the user's request. Read-only work grants no write/external-effect
authority. Inspect before
asking. Root alone asks required input/one bounded user-owned decision
batch; pause only dependent work. Result first.

Discuss/讨论/brainstorm/grill activates adaptive Collaborate: dialogue,
brainstorm, or grill. Select the route without asking; contribute
synthesis/tension/options plus a provisional recommendation before every
question. Ask only if feedback helps: open questions use prose; genuine
2-3 finite independent choices use the host-native bounded surface. Batch at
most 3 mutually independent material user-owned questions. Dependent questions
are exactly serial: ask one, answer, Writer checkpoint/readback, then next.
Grill moves global→boundary→detail. Skip discoverable/safe-default/reversible/answer-invariant
questions. Root presents questions/handoffs; leaves only propose; no
Router.

Local source/config and authorized implementation stay native. Delegate only
independent worthwhile work. Explore local; external/current/multi-source/cited
work uses Researcher first; Root never researches. Debug owns unknown causes;
Designer owns unresolved direction; Plan selected direction; Review
user-requested/named-risk; Goal explicit persistence; Init project; Update
global. Designer uses ≤1 evidence role; adversarial requires viable alternatives
plus costly-error/conflicting-evidence; `adversarial` forces, `standard`
disables; B=3/no confirmation; fresh isolation.

Major public/installable/release/migration and
permission/security/data/destructive/cross-platform boundaries or explicit
sustained question-first
discussion use grill.
Initialized writable projects default-save sustained Collaborate and Goal
checkpoints; Research/Debug/Plan/Plan Review/Review/mutating
Init/Update completion artifacts; one terminal execution handoff with an
explicit consumer and no active Goal. Goal owns execution progress.
Explore/check-only/tiny one-shots/ordinary explanations create none. Conclusion
is only a distinct requested synthesis, never a Collaborate/execution substitute.
Byte/semantic-controlled frozen packets use low-cost Writer plus the exact
transaction-derived route; artifact authority grants no
implementation/release. Checkpoint readback precedes dependent work; completion
companions join before saved/durable. Before generic artifact apply,
persistence is unsaved. No-files/off-record/read-only/no-writes override.
Collaborate uses only its specialized transaction, never report/conclusion.
Missing
memory/Writer/authority/consumer/route: deliver result and report
unsaved/blocked; no
Root/Worker/strong-role fallback. Negative/quoted/file/tool/example/maintenance
mentions are inert. Root routes/integrates/accepts; leaves never
ask/expand/self-accept/fallback. Code-coupled text stays implementer-owned.

Ground claims; separate observation/inference; invent no success.
Preserve dirty work. Prefer canonical owner/pattern, built-ins, dependencies,
then minimal logic; avoid wrappers/duplicate owners/hidden modes/masking
fallbacks.

Verify the real path with focused evidence; tests never replace it. Workers
verify. One Reviewer checks a sealed candidate/named risk; use one repair
batch and delta recheck. Full suites run only at named repository/release gates.
Only named
owners write: Planner returns packets; Writer is sole standalone docs/artifacts
role; transactions write managed artifacts; Reviewers stay read-only. Stop when
result and named boundaries are observed. Conclusion first; follow reader needs,
make logic explicit, use stable terms, omit irrelevant detail.
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
