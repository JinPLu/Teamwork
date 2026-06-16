#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GITHUB_REPO="${TEAMWORK_GITHUB_REPO:-https://github.com/JinPLu/Teamwork}"
READINESS=0
PROJECT_ROOT=""
FETCH_UPSTREAM=1

SKILLS=(
  using-teamwork
  teamwork-init
  teamwork-goal
  teamwork-research
  teamwork-plan
  teamwork-execute
  teamwork-review
  teamwork-update
)
CODEX_AGENTS=(
  teamwork-explorer
  teamwork-worker
  teamwork-designer
  teamwork-judge
  teamwork-reviewer
  teamwork-deep-judge
  teamwork-deep-reviewer
)
CURSOR_AGENTS=(
  explore
  worker
  designer
  judge
  code-reviewer
  deep-judge
  deep-reviewer
)
CLAUDE_AGENTS=(
  explore
  worker
  designer
  judge
  code-reviewer
  deep-judge
  deep-reviewer
)

ISSUES=0

usage() {
  cat <<'USAGE'
Usage:
  ./scripts/check-update.sh [--readiness] [--project PATH] [--no-fetch]

Report Teamwork install freshness: package version, global/project surfaces,
bootstrap policy, agent inventory, and best-effort upstream/model drift.

Options:
  --readiness     Compact machine-friendly output for teamwork-init gate
  --project PATH  Also check project-local .cursor/.codex/.claude installs
  --no-fetch      Skip git fetch / remote tag lookup
USAGE
}

semver_lt() {
  local a="$1" b="$2"
  [[ "$(printf '%s\n%s\n' "$a" "$b" | sort -V | head -n1)" == "$a" && "$a" != "$b" ]]
}

read_installed_version() {
  local dest_root="$1"
  local marker="$dest_root/.teamwork-version"
  if [[ -f "$marker" ]]; then
    tr -d '[:space:]' < "$marker"
    return 0
  fi
  if [[ -d "$dest_root/using-teamwork" ]]; then
    echo "unknown"
    return 0
  fi
  echo "missing"
}

read_installed_profile() {
  local dest_root="$1"
  local marker="$dest_root/.teamwork-profile"
  if [[ -f "$marker" ]]; then
    tr -d '[:space:]' < "$marker"
  else
    echo "unknown"
  fi
}

skills_status() {
  local dest_root="$1"
  local skill missing=0
  [[ -d "$dest_root" ]] || { echo "missing"; return 0; }
  for skill in "${SKILLS[@]}"; do
    [[ -e "$dest_root/$skill/SKILL.md" ]] || missing=$((missing + 1))
  done
  if (( missing == 0 )); then
    echo "ok"
  elif (( missing == ${#SKILLS[@]} )); then
    echo "missing"
  else
    echo "partial($missing/${#SKILLS[@]})"
  fi
}

agents_status() {
  local dest_root="$1"
  local ext="$2"
  shift 2
  local agents=("$@")
  local agent missing=0
  [[ -d "$dest_root" ]] || { echo "missing"; return 0; }
  for agent in "${agents[@]}"; do
    [[ -e "$dest_root/$agent.$ext" ]] || missing=$((missing + 1))
  done
  if (( missing == 0 )); then
    echo "ok"
  elif (( missing == ${#agents[@]} )); then
    echo "missing"
  else
    echo "partial($missing/${#agents[@]})"
  fi
}

policy_status() {
  local platform="$1"
  case "$platform" in
    codex)
      if [[ -f "$HOME/.codex/AGENTS.md" ]] && grep -q 'TEAMWORK_CODEX_GLOBAL_START' "$HOME/.codex/AGENTS.md"; then
        echo "ok"
      else
        echo "missing"
      fi
      ;;
    claude)
      if [[ -f "$HOME/.claude/CLAUDE.md" ]] && grep -q 'TEAMWORK_CLAUDE_GLOBAL_START' "$HOME/.claude/CLAUDE.md"; then
        echo "ok"
      else
        echo "missing"
      fi
      ;;
    cursor)
      echo "manual"
      ;;
  esac
}

version_drift() {
  local installed="$1" source="$2"
  case "$installed" in
    missing|unknown)
      echo "unknown"
      ;;
    *)
      if semver_lt "$installed" "$source"; then
        echo "stale($installed->$source)"
      elif [[ "$installed" == "$source" ]]; then
        echo "current"
      else
        echo "ahead($installed)"
      fi
      ;;
  esac
}

note_issue() {
  ISSUES=$((ISSUES + 1))
}

cursor_model_sample() {
  local agent_file="$HOME/.cursor/agents/explore.md"
  [[ -f "$agent_file" ]] || { echo "missing"; return 0; }
  sed -n 's/^model: //p' "$agent_file" | head -n1
}

source_profile() {
  tr -d '[:space:]' < "$ROOT/.teamwork-profile" 2>/dev/null || echo "performance-first"
}

upstream_version() {
  local remote_version=""
  if (( FETCH_UPSTREAM )) && git -C "$ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git -C "$ROOT" fetch origin --quiet 2>/dev/null || true
    remote_version="$(git -C "$ROOT" show "origin/HEAD:VERSION" 2>/dev/null \
      || git -C "$ROOT" show "origin/main:VERSION" 2>/dev/null \
      || true)"
  fi
  if [[ -z "$remote_version" ]] && (( FETCH_UPSTREAM )) && command -v curl >/dev/null 2>&1; then
    remote_version="$(curl -fsSL "${GITHUB_REPO}/raw/main/VERSION" 2>/dev/null || true)"
  fi
  if [[ -z "$remote_version" ]] && (( FETCH_UPSTREAM )) && command -v git >/dev/null 2>&1; then
    local latest_tag
    latest_tag="$(git ls-remote --tags "${GITHUB_REPO}.git" 2>/dev/null \
      | awk -F/ '{print $NF}' | grep -E '^v?[0-9]+\.[0-9]+\.[0-9]+$' \
      | sed 's/^v//' | sort -V | tail -n1 || true)"
    remote_version="$latest_tag"
  fi
  echo "$remote_version"
}

git_local_state() {
  if ! git -C "$ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "not-a-git-checkout"
    return 0
  fi
  local behind=0
  if git -C "$ROOT" rev-parse '@{u}' >/dev/null 2>&1; then
    behind="$(git -C "$ROOT" rev-list --count HEAD.."@{u}" 2>/dev/null || echo 0)"
    if [[ "$behind" != "0" ]]; then
      echo "behind-upstream($behind)"
      note_issue
      return 0
    fi
  fi
  echo "synced"
}

print_readiness() {
  local source_version profile codex_v cursor_v claude_v
  source_version="$(tr -d '[:space:]' < "$ROOT/VERSION")"
  profile="$(source_profile)"
  codex_v="$(read_installed_version "$HOME/.codex/skills")"
  cursor_v="$(read_installed_version "$HOME/.cursor/skills")"
  claude_v="$(read_installed_version "$HOME/.claude/skills")"

  local ready=yes
  local missing=()

  [[ "$(skills_status "$HOME/.codex/skills")" == "ok" ]] || { ready=no; missing+=("codex-skills"); }
  [[ "$(skills_status "$HOME/.cursor/skills")" == "ok" ]] || { ready=no; missing+=("cursor-skills"); }
  [[ "$(skills_status "$HOME/.claude/skills")" == "ok" ]] || { ready=no; missing+=("claude-skills"); }
  [[ "$(agents_status "$HOME/.codex/agents" toml "${CODEX_AGENTS[@]}")" == "ok" ]] || { ready=no; missing+=("codex-agents"); }
  [[ "$(agents_status "$HOME/.cursor/agents" md "${CURSOR_AGENTS[@]}")" == "ok" ]] || { ready=no; missing+=("cursor-agents"); }
  [[ "$(agents_status "$HOME/.claude/agents" md "${CLAUDE_AGENTS[@]}")" == "ok" ]] || { ready=no; missing+=("claude-agents"); }
  [[ "$(policy_status codex)" == "ok" ]] || { ready=no; missing+=("codex-policy"); }
  [[ "$(policy_status claude)" == "ok" ]] || { ready=no; missing+=("claude-policy"); }
  missing+=("cursor-policy-manual")

  if [[ -n "$PROJECT_ROOT" ]]; then
    [[ "$(skills_status "$PROJECT_ROOT/.cursor/skills")" == "ok" ]] || { ready=no; missing+=("project-skills"); }
    [[ "$(agents_status "$PROJECT_ROOT/.cursor/agents" md "${CURSOR_AGENTS[@]}")" == "ok" ]] || { ready=no; missing+=("project-cursor-agents"); }
  fi

  for v in "$codex_v" "$cursor_v" "$claude_v"; do
    if [[ "$v" != "missing" && "$v" != "unknown" ]] && semver_lt "$v" "$source_version"; then
      ready=no
      missing+=("version-drift")
      break
    fi
  done

  echo "INSTALL_READY=$ready"
  echo "SOURCE_VERSION=$source_version"
  echo "PROFILE=$profile"
  echo "CODEX_VERSION=$codex_v"
  echo "CURSOR_VERSION=$cursor_v"
  echo "CLAUDE_VERSION=$claude_v"
  echo "MISSING=$(IFS=,; echo "${missing[*]-}")"
  echo "NEXT=cd \"$ROOT\" && ./install.sh all --profile $profile${PROJECT_ROOT:+ && ./install.sh --project-root \"$PROJECT_ROOT\" project}"
  echo "CURSOR_POLICY=./install.sh cursor-policy"
}

print_report() {
  local source_version upstream profile
  source_version="$(tr -d '[:space:]' < "$ROOT/VERSION")"
  upstream="$(upstream_version)"
  profile="$(source_profile)"

  echo "=== Teamwork Update Report ==="
  echo "Checkout: $ROOT"
  echo "Source VERSION: $source_version"
  echo "Install profile (checkout): $profile"
  echo "Git state: $(git_local_state)"
  if [[ -n "$upstream" ]]; then
    echo "Upstream VERSION: $upstream"
    if semver_lt "$source_version" "$upstream"; then
      echo "Checkout status: stale ($source_version -> $upstream)"
      note_issue
    elif [[ "$source_version" == "$upstream" ]]; then
      echo "Checkout status: current"
    else
      echo "Checkout status: ahead ($source_version)"
    fi
  else
    echo "Upstream VERSION: unavailable"
  fi
  echo

  printf '%-8s %-8s %-8s %-8s %-18s %-12s\n' "Platform" "Skills" "Agents" "Policy" "InstalledVersion" "Profile"
  local platform dest_skills dest_agents ext agents_ref
  for platform in codex cursor claude; do
    case "$platform" in
      codex)
        dest_skills="$HOME/.codex/skills"
        dest_agents="$HOME/.codex/agents"
        ext="toml"
        agents_ref=("${CODEX_AGENTS[@]}")
        ;;
      cursor)
        dest_skills="$HOME/.cursor/skills"
        dest_agents="$HOME/.cursor/agents"
        ext="md"
        agents_ref=("${CURSOR_AGENTS[@]}")
        ;;
      claude)
        dest_skills="$HOME/.claude/skills"
        dest_agents="$HOME/.claude/agents"
        ext="md"
        agents_ref=("${CLAUDE_AGENTS[@]}")
        ;;
    esac
    local installed_v skills_s agents_s policy_s drift_s prof_s
    installed_v="$(read_installed_version "$dest_skills")"
    skills_s="$(skills_status "$dest_skills")"
    agents_s="$(agents_status "$dest_agents" "$ext" "${agents_ref[@]}")"
    policy_s="$(policy_status "$platform")"
    drift_s="$(version_drift "$installed_v" "$source_version")"
    prof_s="$(read_installed_profile "$dest_skills")"
    [[ "$skills_s" == "ok" && "$agents_s" == "ok" && "$drift_s" == "current" ]] || note_issue
    [[ "$policy_s" == "missing" ]] && note_issue
    printf '%-8s %-8s %-8s %-8s %-18s %-12s\n' \
      "$platform" "$skills_s" "$agents_s" "$policy_s" "$drift_s" "$prof_s"
  done
  echo

  echo "--- Bootstrap manual checks ---"
  echo "Cursor User Rules: paste ./install.sh cursor-policy (cannot auto-verify)"
  echo

  echo "--- Model mapping (best-effort) ---"
  echo "Cursor explore model: $(cursor_model_sample)"
  echo "Expected cost-first routine: composer-2.5-fast"
  echo "Expected performance-first explore: claude-sonnet-4-6"
  echo

  if [[ -n "$PROJECT_ROOT" ]]; then
    echo "--- Project ($PROJECT_ROOT) ---"
    local p_skills p_cursor_agents p_codex_agents p_claude_agents p_v
    p_skills="$(skills_status "$PROJECT_ROOT/.cursor/skills")"
    p_cursor_agents="$(agents_status "$PROJECT_ROOT/.cursor/agents" md "${CURSOR_AGENTS[@]}")"
    p_codex_agents="$(agents_status "$PROJECT_ROOT/.codex/agents" toml "${CODEX_AGENTS[@]}")"
    p_claude_agents="$(agents_status "$PROJECT_ROOT/.claude/agents" md "${CLAUDE_AGENTS[@]}")"
    p_v="$(read_installed_version "$PROJECT_ROOT/.cursor/skills")"
    echo "project skills: $p_skills ($p_v)"
    echo "project cursor agents: $p_cursor_agents"
    echo "project codex agents: $p_codex_agents"
    echo "project claude agents: $p_claude_agents"
    [[ "$p_skills" != "ok" || "$p_cursor_agents" != "ok" ]] && note_issue
    if [[ -f "$PROJECT_ROOT/docs/teamwork/index.json" ]]; then
      echo "docs/teamwork/index.json: present"
    else
      echo "docs/teamwork/index.json: missing (optional until memory enabled)"
    fi
    echo
  fi

  echo "--- Optional substrates ---"
  if [[ -d "$HOME/.cursor/projects" ]] && find "$HOME/.cursor/projects" -path '*/mcps/user-codegraph/tools/*.json' -print -quit 2>/dev/null | grep -q .; then
    echo "CodeGraph MCP: configured"
  else
    echo "CodeGraph MCP: not detected (optional)"
  fi
  echo

  echo "--- Recommended actions ---"
  if [[ -n "$upstream" ]] && semver_lt "$source_version" "$upstream"; then
    echo "1. cd \"$ROOT\" && git pull"
  fi
  echo "2. cd \"$ROOT\" && ./install.sh all --profile $profile"
  if [[ -n "$PROJECT_ROOT" ]]; then
    echo "3. cd \"$ROOT\" && ./install.sh project"
  fi
  echo "4. ./install.sh cursor-policy  # paste into Cursor User Rules"
  echo "5. ./scripts/validate.sh       # maintainer or post-release sanity"
  echo

  if (( ISSUES > 0 )); then
    echo "Summary: $ISSUES issue(s) need attention."
  else
    echo "Summary: installed surfaces look current."
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --readiness)
      READINESS=1
      shift
      ;;
    --project)
      [[ $# -ge 2 ]] || { echo "--project requires a path." >&2; exit 2; }
      PROJECT_ROOT="$(cd "$2" && pwd)"
      shift 2
      ;;
    --no-fetch)
      FETCH_UPSTREAM=0
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

if (( READINESS )); then
  print_readiness
else
  print_report
fi

exit $(( ISSUES > 0 ? 1 : 0 ))
