#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODEX_HOME_DIR="${CODEX_HOME:-$HOME/.codex}"
READINESS=0

usage() {
  cat <<'USAGE'
Usage: ./scripts/check-update.sh [--readiness] [--no-fetch]

Report the local Codex Teamwork installation. The command is diagnostic: stale
or missing optional surfaces are reported as partial state and never become a
prerequisite for another workflow.
USAGE
}

while (($#)); do
  case "$1" in
    --readiness) READINESS=1 ;;
    --no-fetch) : ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage; exit 2 ;;
  esac
  shift
done

mapfile_compat() {
  local directory="$1" pattern="$2"
  find "$directory" -maxdepth 1 -type f -name "$pattern" -exec basename {} \; 2>/dev/null | sort
}

expected_agents="$(mapfile_compat "$ROOT/templates/codex-agents" 'teamwork-*.toml')"
missing_agents=()
while IFS= read -r agent; do
  [[ -n "$agent" ]] || continue
  [[ -f "$CODEX_HOME_DIR/agents/$agent" ]] || missing_agents+=("$agent")
done <<<"$expected_agents"

policy=missing
if [[ -f "$CODEX_HOME_DIR/AGENTS.md" ]] \
    && grep -q '<!-- TEAMWORK_CODEX_GLOBAL_START -->' "$CODEX_HOME_DIR/AGENTS.md" \
    && grep -q '<!-- TEAMWORK_CODEX_GLOBAL_END -->' "$CODEX_HOME_DIR/AGENTS.md"; then
  policy=present
fi

routing=unconfigured
if python3 "$ROOT/scripts/configure-codex-routing.py" \
    --check --config "$CODEX_HOME_DIR/config.toml" >/dev/null 2>&1; then
  routing=configured
fi

skills=missing
if [[ -d "$HOME/.agents/skills/teamwork-collaborate" ]]; then
  skills=user
fi

source_state="$(python3 "$ROOT/scripts/write-source-pointer.py" status --home "$HOME")"

state=ready
if ((${#missing_agents[@]})) || [[ "$policy" != present ]] || [[ "$routing" != configured ]] || [[ "$skills" == missing ]]; then
  state=partial
fi

missing="$(IFS=,; echo "${missing_agents[*]-}")"
if ((READINESS)); then
  echo "INSTALL_STATE=$state"
  echo "INSTALL_SCOPE=codex"
  echo "SKILLS=$skills"
  echo "SOURCE=$source_state"
  echo "AGENTS=$([[ -z "$missing" ]] && echo present || echo partial)"
  echo "MISSING_AGENTS=$missing"
  echo "POLICY=$policy"
  echo "ROUTING=$routing"
  echo "BLOCKS_OTHER_WORK=no"
else
  echo "Teamwork Codex install: $state"
  echo "Skills: $skills"
  echo "Source pointer: $source_state"
  echo "Agents: $([[ -z "$missing" ]] && echo present || echo "missing $missing")"
  echo "Policy: $policy"
  echo "Routing: $routing"
  echo "This report is informational and does not block native work."
fi

exit 0
