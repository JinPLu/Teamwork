#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GITHUB_REPO="${TEAMWORK_GITHUB_REPO:-https://github.com/JinPLu/Teamwork}"
READINESS=0
PROJECT_ROOT=""
FETCH_UPSTREAM=1

SKILLS=(
  using-teamwork
  grill-me
  teamwork-debug
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
bootstrap policy, agent inventory, and best-effort upstream, remote-tag,
GitHub-Release, and model drift.

Options:
  --readiness     Compact machine-friendly output for teamwork-init gate
  --project PATH  Also check Codex .agents/skills, Cursor .cursor/skills,
                  Claude Code .claude/skills, and project-local agents
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

notification_status() {
  local platform="$1" config notifier base
  case "$platform" in
    codex)
      config="$HOME/.codex/hooks.json"
      notifier="$HOME/.codex/teamwork/notify.py"
      ;;
    claude)
      config="$HOME/.claude/settings.json"
      notifier="$HOME/.claude/teamwork/notify.py"
      ;;
    cursor)
      echo "unsupported"
      return 0
      ;;
    *)
      echo "unknown"
      return 0
      ;;
  esac
  if ! base="$(python3 "$ROOT/scripts/configure-notifications.py" status \
    --config "$config" --notifier "$notifier" 2>/dev/null)"; then
    echo "invalid"
    return 0
  fi
  if [[ "$platform" == "codex" && "$base" == "installed" ]]; then
    python3 "$ROOT/scripts/configure-notifications.py" status \
      --config "$config" --notifier "$notifier" \
      --codex-runtime --cwd "$ROOT" 2>/dev/null || echo "runtime-unverified"
    return 0
  fi
  echo "$base"
}

codex_routing_status() {
  local output status
  if ! command -v python3 >/dev/null 2>&1; then
    echo "unavailable"
    return 0
  fi
  if output="$(python3 "$ROOT/scripts/configure-codex-routing.py" --check 2>/dev/null)"; then
    echo "ready"
    return 0
  fi
  status="$(printf '%s\n' "$output" | sed -n 's/^CODEX_ROUTING=//p' | head -n1)"
  case "$status" in
    missing|drift|invalid)
      echo "$status"
      ;;
    *)
      echo "invalid"
      ;;
  esac
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

skills_content_status() {
  local dest_root="$1"
  local rel drift=0 missing=0
  [[ -d "$dest_root" ]] || { echo "missing"; return 0; }
  while IFS= read -r -d '' source_file; do
    rel="${source_file#$ROOT/skills/}"
    if [[ ! -f "$dest_root/$rel" ]]; then
      missing=$((missing + 1))
    elif ! cmp -s "$source_file" "$dest_root/$rel"; then
      drift=$((drift + 1))
    fi
  done < <(find "$ROOT/skills" -type f -print0)

  if (( missing == 0 && drift == 0 )); then
    echo "current"
  else
    echo "drift(missing=$missing,changed=$drift)"
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

agents_content_status() {
  local dest_root="$1"
  local ext="$2"
  local platform="$3"
  shift 3
  local agents=("$@")
  local agent source expected tmp missing=0 drift=0
  [[ -d "$dest_root" ]] || { echo "missing"; return 0; }
  tmp="$(mktemp -d)"
  for agent in "${agents[@]}"; do
    case "$platform" in
      codex)
        source="$ROOT/templates/codex-agents/$agent.toml"
        expected="$tmp/$agent.toml"
        render_codex_agent_expected "$source" "$expected" "$agent"
        ;;
      cursor)
        source="$ROOT/templates/cursor-agents/$agent.md"
        expected="$tmp/$agent.md"
        render_cursor_agent_expected "$source" "$expected" "$agent"
        ;;
      claude)
        source="$ROOT/templates/claude-agents/$agent.md"
        expected="$tmp/$agent.md"
        render_claude_agent_expected "$source" "$expected" "$agent"
        ;;
      *)
        rm -rf "$tmp"
        echo "unknown-platform"
        return 0
        ;;
    esac
    if [[ ! -f "$dest_root/$agent.$ext" ]]; then
      missing=$((missing + 1))
    elif ! cmp -s "$expected" "$dest_root/$agent.$ext"; then
      drift=$((drift + 1))
    fi
  done
  rm -rf "$tmp"
  if (( missing == 0 && drift == 0 )); then
    echo "current"
  else
    echo "drift(missing=$missing,changed=$drift)"
  fi
}

codex_agent_profile_values() {
  local agent="$1"
  case "$(source_profile):$agent" in
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
  case "$(source_profile):$agent" in
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
  case "$(source_profile):$agent" in
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

render_codex_agent_expected() {
  local source="$1" expected="$2" agent="$3" model effort
  read -r model effort < <(codex_agent_profile_values "$agent")
  sed \
    -e "s/^model = .*/model = \"$model\"/" \
    -e "s/^model_reasoning_effort = .*/model_reasoning_effort = \"$effort\"/" \
    "$source" > "$expected"
}

render_claude_agent_expected() {
  local source="$1" expected="$2" agent="$3" model effort
  read -r model effort < <(claude_agent_profile_values "$agent")
  sed \
    -e "s/^model: .*/model: $model/" \
    -e "s/^effort: .*/effort: $effort/" \
    "$source" > "$expected"
}

render_cursor_agent_expected() {
  local source="$1" expected="$2" agent="$3" model
  read -r model < <(cursor_agent_profile_values "$agent")
  sed -e "s/^model: .*/model: $model/" "$source" > "$expected"
}

policy_status() {
  local platform="$1"
  local file marker
  case "$platform" in
    codex)
      file="$HOME/.codex/AGENTS.md"
      marker="TEAMWORK_CODEX_GLOBAL_START"
      ;;
    claude)
      file="$HOME/.claude/CLAUDE.md"
      marker="TEAMWORK_CLAUDE_GLOBAL_START"
      ;;
    cursor)
      echo "manual"
      return 0
      ;;
  esac

  if [[ -f "$file" ]] \
    && grep -q "$marker" "$file" \
    && grep -q "Work within the user's request" "$file" \
    && grep -q 'routine reversible choices' "$file" \
    && grep -q 'Route explicit grill/question-first' "$file" \
    && grep -q 'Ask only when the user must supply' "$file" \
    && grep -q 'Pause only dependent work' "$file" \
    && grep -q 'Never invent or hide gaps' "$file" \
    && grep -q 'Delegate only worthwhile independent scope' "$file" \
    && grep -q 'agents own models; active profile' "$file"; then
    echo "ok"
  else
    echo "missing"
  fi
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
    local upstream_ref upstream_remote
    upstream_ref="$(git -C "$ROOT" rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)"
    if [[ -n "$upstream_ref" ]]; then
      upstream_remote="${upstream_ref%%/*}"
      git -C "$ROOT" fetch "$upstream_remote" --quiet 2>/dev/null || true
      remote_version="$(git -C "$ROOT" show "$upstream_ref:VERSION" 2>/dev/null || true)"
    fi
    if [[ -z "$remote_version" ]]; then
      git -C "$ROOT" fetch origin --quiet 2>/dev/null || true
      remote_version="$(git -C "$ROOT" show "origin/HEAD:VERSION" 2>/dev/null \
        || git -C "$ROOT" show "origin/main:VERSION" 2>/dev/null \
        || true)"
    fi
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

latest_remote_tag_version() {
  (( FETCH_UPSTREAM )) || { echo ""; return 0; }
  command -v git >/dev/null 2>&1 || { echo ""; return 0; }
  git ls-remote --tags "${GITHUB_REPO%.git}.git" 2>/dev/null \
    | awk -F/ '{print $NF}' \
    | grep -E '^v?[0-9]+\.[0-9]+\.[0-9]+$' \
    | sed 's/^v//' \
    | sort -V \
    | tail -n1 \
    || true
}

github_repo_slug() {
  local slug="$GITHUB_REPO"
  case "$slug" in
    https://github.com/*) slug="${slug#https://github.com/}" ;;
    http://github.com/*) slug="${slug#http://github.com/}" ;;
    git@github.com:*) slug="${slug#git@github.com:}" ;;
    *) return 0 ;;
  esac
  slug="${slug%.git}"
  slug="${slug%/}"
  [[ "$slug" == */* && "$slug" != */*/* ]] || return 0
  echo "$slug"
}

latest_github_release_version() {
  (( FETCH_UPSTREAM )) || { echo ""; return 0; }
  local slug tag=""
  slug="$(github_repo_slug)"
  [[ -n "$slug" ]] || { echo ""; return 0; }
  if command -v gh >/dev/null 2>&1; then
    tag="$(gh api "repos/$slug/releases/latest" --jq '.tag_name' 2>/dev/null || true)"
  fi
  if [[ -z "$tag" ]] && command -v curl >/dev/null 2>&1 && command -v python3 >/dev/null 2>&1; then
    tag="$(curl -fsSL "https://api.github.com/repos/$slug/releases/latest" 2>/dev/null \
      | python3 -c 'import json,sys; print(json.load(sys.stdin).get("tag_name", ""))' 2>/dev/null \
      || true)"
  fi
  printf '%s\n' "$tag" | sed -n -E 's/^v?([0-9]+\.[0-9]+\.[0-9]+)$/\1/p'
}

release_state() {
  local published="$1" source="$2"
  if semver_lt "$published" "$source"; then
    echo "stale ($published -> $source)"
  elif [[ "$published" == "$source" ]]; then
    echo "current"
  else
    echo "ahead ($published)"
  fi
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
  [[ "$(skills_content_status "$HOME/.codex/skills")" == "current" ]] || { ready=no; missing+=("codex-skill-content"); }
  [[ "$(skills_content_status "$HOME/.cursor/skills")" == "current" ]] || { ready=no; missing+=("cursor-skill-content"); }
  [[ "$(skills_content_status "$HOME/.claude/skills")" == "current" ]] || { ready=no; missing+=("claude-skill-content"); }
  [[ "$(agents_status "$HOME/.codex/agents" toml "${CODEX_AGENTS[@]}")" == "ok" ]] || { ready=no; missing+=("codex-agents"); }
  [[ "$(agents_status "$HOME/.cursor/agents" md "${CURSOR_AGENTS[@]}")" == "ok" ]] || { ready=no; missing+=("cursor-agents"); }
  [[ "$(agents_status "$HOME/.claude/agents" md "${CLAUDE_AGENTS[@]}")" == "ok" ]] || { ready=no; missing+=("claude-agents"); }
  [[ "$(agents_content_status "$HOME/.codex/agents" toml codex "${CODEX_AGENTS[@]}")" == "current" ]] || { ready=no; missing+=("codex-agent-content"); }
  [[ "$(agents_content_status "$HOME/.cursor/agents" md cursor "${CURSOR_AGENTS[@]}")" == "current" ]] || { ready=no; missing+=("cursor-agent-content"); }
  [[ "$(agents_content_status "$HOME/.claude/agents" md claude "${CLAUDE_AGENTS[@]}")" == "current" ]] || { ready=no; missing+=("claude-agent-content"); }
  [[ "$(codex_routing_status)" == "ready" ]] || { ready=no; missing+=("codex-routing"); }
  [[ "$(policy_status codex)" == "ok" ]] || { ready=no; missing+=("codex-policy"); }
  [[ "$(policy_status claude)" == "ok" ]] || { ready=no; missing+=("claude-policy"); }
  missing+=("cursor-policy-manual")

  if [[ -n "$PROJECT_ROOT" ]]; then
    local project_codex_v project_cursor_v project_claude_v
    project_codex_v="$(read_installed_version "$PROJECT_ROOT/.agents/skills")"
    project_cursor_v="$(read_installed_version "$PROJECT_ROOT/.cursor/skills")"
    project_claude_v="$(read_installed_version "$PROJECT_ROOT/.claude/skills")"
    [[ "$(skills_status "$PROJECT_ROOT/.agents/skills")" == "ok" ]] || { ready=no; missing+=("project-codex-skills"); }
    [[ "$(skills_status "$PROJECT_ROOT/.cursor/skills")" == "ok" ]] || { ready=no; missing+=("project-cursor-skills"); }
    [[ "$(skills_status "$PROJECT_ROOT/.claude/skills")" == "ok" ]] || { ready=no; missing+=("project-claude-skills"); }
    [[ "$(skills_content_status "$PROJECT_ROOT/.agents/skills")" == "current" ]] || { ready=no; missing+=("project-codex-skill-content"); }
    [[ "$(skills_content_status "$PROJECT_ROOT/.cursor/skills")" == "current" ]] || { ready=no; missing+=("project-cursor-skill-content"); }
    [[ "$(skills_content_status "$PROJECT_ROOT/.claude/skills")" == "current" ]] || { ready=no; missing+=("project-claude-skill-content"); }
    [[ "$(agents_status "$PROJECT_ROOT/.cursor/agents" md "${CURSOR_AGENTS[@]}")" == "ok" ]] || { ready=no; missing+=("project-cursor-agents"); }
    [[ "$(agents_status "$PROJECT_ROOT/.codex/agents" toml "${CODEX_AGENTS[@]}")" == "ok" ]] || { ready=no; missing+=("project-codex-agents"); }
    [[ "$(agents_status "$PROJECT_ROOT/.claude/agents" md "${CLAUDE_AGENTS[@]}")" == "ok" ]] || { ready=no; missing+=("project-claude-agents"); }
    [[ "$(agents_content_status "$PROJECT_ROOT/.codex/agents" toml codex "${CODEX_AGENTS[@]}")" == "current" ]] || { ready=no; missing+=("project-codex-agent-content"); }
    [[ "$(agents_content_status "$PROJECT_ROOT/.cursor/agents" md cursor "${CURSOR_AGENTS[@]}")" == "current" ]] || { ready=no; missing+=("project-cursor-agent-content"); }
    [[ "$(agents_content_status "$PROJECT_ROOT/.claude/agents" md claude "${CLAUDE_AGENTS[@]}")" == "current" ]] || { ready=no; missing+=("project-claude-agent-content"); }
    if [[ "$project_codex_v" != "missing" && "$project_codex_v" != "unknown" ]] && semver_lt "$project_codex_v" "$source_version"; then
      ready=no
      missing+=("project-codex-version-drift")
    fi
    if [[ "$project_cursor_v" != "missing" && "$project_cursor_v" != "unknown" ]] && semver_lt "$project_cursor_v" "$source_version"; then
      ready=no
      missing+=("project-cursor-version-drift")
    fi
    if [[ "$project_claude_v" != "missing" && "$project_claude_v" != "unknown" ]] && semver_lt "$project_claude_v" "$source_version"; then
      ready=no
      missing+=("project-claude-version-drift")
    fi
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
  if [[ -n "$PROJECT_ROOT" ]]; then
    echo "PROJECT_CODEX_VERSION=$project_codex_v"
    echo "PROJECT_CURSOR_VERSION=$project_cursor_v"
    echo "PROJECT_CLAUDE_VERSION=$project_claude_v"
  fi
  echo "CODEX_NOTIFICATIONS=$(notification_status codex)"
  echo "CODEX_ROUTING=$(codex_routing_status)"
  echo "CLAUDE_NOTIFICATIONS=$(notification_status claude)"
  echo "CURSOR_NOTIFICATIONS=$(notification_status cursor)"
  echo "MISSING=$(IFS=,; echo "${missing[*]-}")"
  echo "NEXT=cd \"$ROOT\" && ./install.sh all --profile $profile${PROJECT_ROOT:+ && ./install.sh --project-root \"$PROJECT_ROOT\" project}"
  echo "CURSOR_POLICY=./install.sh cursor-policy-copy"
}

print_report() {
  local source_version upstream profile remote_tag github_release
  source_version="$(tr -d '[:space:]' < "$ROOT/VERSION")"
  upstream="$(upstream_version)"
  profile="$(source_profile)"
  remote_tag="$(latest_remote_tag_version)"
  github_release="$(latest_github_release_version)"

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
  if [[ -n "$remote_tag" ]]; then
    echo "Remote tag VERSION: $remote_tag"
    echo "Remote tag status: $(release_state "$remote_tag" "$source_version")"
    [[ "$remote_tag" == "$source_version" ]] || note_issue
  else
    echo "Remote tag VERSION: unavailable"
  fi
  if [[ -n "$github_release" ]]; then
    echo "GitHub Release VERSION: $github_release"
    echo "GitHub Release status: $(release_state "$github_release" "$source_version")"
    [[ "$github_release" == "$source_version" ]] || note_issue
  else
    echo "GitHub Release VERSION: unavailable"
  fi
  echo

  printf '%-8s %-8s %-12s %-8s %-14s %-8s %-18s %-12s\n' "Platform" "Skills" "SkillContent" "Agents" "AgentContent" "Policy" "InstalledVersion" "Profile"
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
    local installed_v skills_s content_s agents_s agent_content_s policy_s drift_s prof_s
    installed_v="$(read_installed_version "$dest_skills")"
    skills_s="$(skills_status "$dest_skills")"
    content_s="$(skills_content_status "$dest_skills")"
    agents_s="$(agents_status "$dest_agents" "$ext" "${agents_ref[@]}")"
    agent_content_s="$(agents_content_status "$dest_agents" "$ext" "$platform" "${agents_ref[@]}")"
    policy_s="$(policy_status "$platform")"
    drift_s="$(version_drift "$installed_v" "$source_version")"
    prof_s="$(read_installed_profile "$dest_skills")"
    [[ "$skills_s" == "ok" && "$content_s" == "current" && "$agents_s" == "ok" && "$agent_content_s" == "current" && "$drift_s" == "current" ]] || note_issue
    [[ "$policy_s" == "missing" ]] && note_issue
    printf '%-8s %-8s %-12s %-8s %-14s %-8s %-18s %-12s\n' \
      "$platform" "$skills_s" "$content_s" "$agents_s" "$agent_content_s" "$policy_s" "$drift_s" "$prof_s"
  done
  echo

  echo "--- Codex custom-agent routing ---"
  local codex_routing_s
  codex_routing_s="$(codex_routing_status)"
  echo "config: $codex_routing_s"
  [[ "$codex_routing_s" == "ready" ]] || note_issue
  echo

  echo "--- Optional notifications ---"
  local notification_s codex_notification_s=""
  for platform in codex cursor claude; do
    notification_s="$(notification_status "$platform")"
    [[ "$platform" == "codex" ]] && codex_notification_s="$notification_s"
    echo "$platform: $notification_s"
    [[ "$notification_s" != "stale" && "$notification_s" != "duplicate" \
      && "$notification_s" != "invalid" && "$notification_s" != "review-required" \
      && "$notification_s" != "runtime-unverified" ]] || note_issue
  done
  echo

  echo "--- Bootstrap manual checks ---"
  echo "Cursor User Rules: run ./install.sh cursor-policy-copy, then paste in Cursor Settings -> Rules -> User Rules (cannot auto-verify)"
  echo

  echo "--- Model mapping (best-effort) ---"
  echo "Cursor explore model: $(cursor_model_sample)"
  echo "Expected performance-first Codex: Explorer=Terra/medium, Worker=Sol/medium, Designer/Judge/Reviewer=Sol/high, Deep=Sol/max"
  echo "Expected gpt56-role Codex: compatibility alias of performance-first"
  echo "Expected cost-first Cursor routine: composer-2.5"
  echo "Expected performance-first explore: claude-sonnet-4-6"
  echo

  if [[ -n "$PROJECT_ROOT" ]]; then
    echo "--- Project ($PROJECT_ROOT) ---"
    local p_codex_skills p_cursor_skills p_claude_skills p_codex_content p_cursor_content p_claude_content
    local p_cursor_agents p_codex_agents p_claude_agents p_cursor_agent_content p_codex_agent_content p_claude_agent_content
    local p_codex_v p_cursor_v p_claude_v p_codex_drift p_cursor_drift p_claude_drift
    p_codex_skills="$(skills_status "$PROJECT_ROOT/.agents/skills")"
    p_cursor_skills="$(skills_status "$PROJECT_ROOT/.cursor/skills")"
    p_claude_skills="$(skills_status "$PROJECT_ROOT/.claude/skills")"
    p_codex_content="$(skills_content_status "$PROJECT_ROOT/.agents/skills")"
    p_cursor_content="$(skills_content_status "$PROJECT_ROOT/.cursor/skills")"
    p_claude_content="$(skills_content_status "$PROJECT_ROOT/.claude/skills")"
    p_cursor_agents="$(agents_status "$PROJECT_ROOT/.cursor/agents" md "${CURSOR_AGENTS[@]}")"
    p_codex_agents="$(agents_status "$PROJECT_ROOT/.codex/agents" toml "${CODEX_AGENTS[@]}")"
    p_claude_agents="$(agents_status "$PROJECT_ROOT/.claude/agents" md "${CLAUDE_AGENTS[@]}")"
    p_cursor_agent_content="$(agents_content_status "$PROJECT_ROOT/.cursor/agents" md cursor "${CURSOR_AGENTS[@]}")"
    p_codex_agent_content="$(agents_content_status "$PROJECT_ROOT/.codex/agents" toml codex "${CODEX_AGENTS[@]}")"
    p_claude_agent_content="$(agents_content_status "$PROJECT_ROOT/.claude/agents" md claude "${CLAUDE_AGENTS[@]}")"
    p_codex_v="$(read_installed_version "$PROJECT_ROOT/.agents/skills")"
    p_cursor_v="$(read_installed_version "$PROJECT_ROOT/.cursor/skills")"
    p_claude_v="$(read_installed_version "$PROJECT_ROOT/.claude/skills")"
    p_codex_drift="$(version_drift "$p_codex_v" "$source_version")"
    p_cursor_drift="$(version_drift "$p_cursor_v" "$source_version")"
    p_claude_drift="$(version_drift "$p_claude_v" "$source_version")"
    echo "project codex skills: $p_codex_skills ($p_codex_drift)"
    echo "project codex skill content: $p_codex_content"
    echo "project cursor skills: $p_cursor_skills ($p_cursor_drift)"
    echo "project cursor skill content: $p_cursor_content"
    echo "project claude skills: $p_claude_skills ($p_claude_drift)"
    echo "project claude skill content: $p_claude_content"
    echo "project cursor agents: $p_cursor_agents"
    echo "project cursor agent content: $p_cursor_agent_content"
    echo "project codex agents: $p_codex_agents"
    echo "project codex agent content: $p_codex_agent_content"
    echo "project claude agents: $p_claude_agents"
    echo "project claude agent content: $p_claude_agent_content"
    [[ "$p_codex_skills" == "ok" && "$p_codex_content" == "current" && "$p_codex_drift" == "current" \
      && "$p_cursor_skills" == "ok" && "$p_cursor_content" == "current" && "$p_cursor_drift" == "current" \
      && "$p_claude_skills" == "ok" && "$p_claude_content" == "current" && "$p_claude_drift" == "current" \
      && "$p_cursor_agents" == "ok" && "$p_codex_agents" == "ok" && "$p_claude_agents" == "ok" \
      && "$p_cursor_agent_content" == "current" && "$p_codex_agent_content" == "current" && "$p_claude_agent_content" == "current" ]] || note_issue
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
    echo "3. cd \"$ROOT\" && ./install.sh --project-root \"$PROJECT_ROOT\" project"
  fi
  echo "4. Restart Codex after routing changes"
  if [[ "$codex_notification_s" == "review-required" ]]; then
    echo "4a. Open Codex CLI, run /hooks, and trust the Teamwork Stop and PermissionRequest hooks"
  elif [[ "$codex_notification_s" == "runtime-unverified" ]]; then
    echo "4a. Open Codex CLI and run /hooks to inspect Teamwork notification hook status"
  fi
  echo "5. ./install.sh cursor-policy-copy  # copy, then paste into Cursor User Rules"
  echo "6. ./scripts/validate.sh       # maintainer or post-release sanity"
  if [[ -n "$remote_tag" && "$remote_tag" != "$source_version" ]] \
    || [[ -n "$github_release" && "$github_release" != "$source_version" ]]; then
    echo "7. Maintainer release: publish v$source_version and its GitHub Release after approval"
  fi
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
