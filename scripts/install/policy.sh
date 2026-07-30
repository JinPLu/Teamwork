write_teamwork_global_policy_body() {
  cat <<'POLICY'
Work within the request. Read-only grants no write/external-effect authority.
Inspect before asking. Root alone asks input/one bounded decision batch; pause
only dependent work. Result first.

Discuss/brainstorm/stress-test activates Collaborate: dialogue|brainstorm.
Select without asking; before questions give synthesis/tension/options plus
recommendation. Ask only if useful: open prose or host-native 2-3 finite
choices. Batch max 3 independent material questions. Dependent:
ask, answer, Writer checkpoint/readback, continue. Challenge moves
global->boundary->detail. Skip
discoverable/safe-default/reversible/answer-invariant. Root asks/hands off;
leaves only propose; no Router.

Native: tiny/discoverable reads, explanations, simple commands, integration,
authorized implementation.
Default one child; daily cap4; 5-8 only for explicit adversarial/release with
host support. Exact roles: Research->Researcher, Explore->Explorer,
Debug->Debugger, Plan->Planner, Review->Reviewer, Plan Review->Plan Reviewer,
Init/Update->Explorer then Worker; Collaborate/Goal Root-owned.
Unavailable role or unverified isolation = capability-blocked; no Root
named-method fallback. Debug freezes failure; hypotheses before probes.
Adversarial is challenge, not mode: viable alternatives plus
costly-error/conflicting-evidence; `adversarial` forces, `standard` disables;
B=3/no confirmation; fresh isolation.

Public/installable/release/migration,
permission/security/data/destructive/cross-platform, or sustained explicit
question-first work uses Collaborate challenge. Initialized writable
projects default-save only case-v2 Collaborate/Goal checkpoints and
Research/Debug/Plan/Plan Review/Review/mutating Init/Update completion
artifacts; terminal execution handoff needs a consumer and no active Goal.
No legacy-v1 artifact/collaborate/goal write fallback. Goal owns
progress. Explore/check-only/tiny one-shots/explanations create none.
Conclusion is only requested synthesis. Frozen packets use low-cost Writer plus
exact transaction; artifact authority grants no implementation/release.
Readback precedes dependent work; join companions before saved/durable;
pre-apply is unsaved.
No-files/off-record/read-only/no-writes override. Collaborate uses its
specialized transaction. Missing memory/Writer/authority/consumer/route:
deliver result, report unsaved/blocked; no Root/Worker/strong-role fallback.
Negative/quoted/file/tool/example mentions are inert. Root
routes/integrates/accepts; leaves never ask/expand/self-accept/fallback.
Code-coupled text stays implementer-owned.

Ground claims; separate observation/inference; invent no success; preserve dirty
work. Prefer canonical owner/pattern, built-ins/dependencies, then minimal
logic; avoid wrappers/duplicate owners/hidden modes/masking fallbacks.

Verify the real path with focused evidence; tests never replace it. Workers
verify. One Reviewer checks a sealed candidate/named risk; one repair batch and
delta recheck. Full suites run only at named repository/release gates.
Named owners write: Planner returns packets; Writer owns standalone docs/artifacts
role; transactions write managed artifacts; Reviewers stay read-only. Stop when
result and boundaries are observed. Conclusion first; be clear, stable, relevant.
Monotonic state: Research claim_map/active_gap/wave/evidence_delta/contradiction/
not_found/coverage_stop; Plan decision_revision/dependencies/proof_targets/
blockers/stops; Review sealed_digest/stable_findings/verdict/repair_batch/
delta_recheck; Goal objective/signal/attempt/failure/evidence_delta/
strategy_delta/status. Cost: native fast path, single owner, fanout/context
bounds, telemetry; no unverified price/ranking claims.
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
