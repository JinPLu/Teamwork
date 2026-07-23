#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=install/policy.sh
source "$ROOT/scripts/install/policy.sh"
# shellcheck source=install/profiles.sh
source "$ROOT/scripts/install/profiles.sh"
GITHUB_REPO="${TEAMWORK_GITHUB_REPO:-https://github.com/JinPLu/Teamwork}"
READINESS=0
FETCH_UPSTREAM=1
PLUGIN_MODE=0
CODEX_HOME_DIR="${CODEX_HOME:-$HOME/.codex}"
PLUGIN_ACTIVATION_PATH="$CODEX_HOME_DIR/teamwork/plugin-activation.json"
STATUS_PROFILE_OVERRIDE=""

SKILLS=(
  grill-me
  teamwork-debug
  teamwork-design
  teamwork-explore
  teamwork-init
  teamwork-goal
  teamwork-research
  teamwork-plan
  teamwork-review
  teamwork-update
)
RETIRED_SKILLS=(
  using-teamwork
  teamwork-execute
)
CODEX_AGENTS=(
  teamwork-researcher
  teamwork-explorer
  teamwork-debugger
  teamwork-designer
  teamwork-planner
  teamwork-worker
  teamwork-writer
  teamwork-plan-reviewer
  teamwork-reviewer
)
CURSOR_AGENTS=(
  researcher
  explorer
  debugger
  designer
  planner
  worker
  writer
  plan-reviewer
  reviewer
)
CLAUDE_AGENTS=(
  researcher
  explorer
  debugger
  designer
  planner
  worker
  writer
  plan-reviewer
  reviewer
)

ISSUES=0

usage() {
  cat <<'USAGE'
Usage:
  ./scripts/check-update.sh [--plugin] [--readiness] [--no-fetch]

Report Teamwork install freshness: package version, global surfaces, bootstrap
policy, agent inventory, and best-effort upstream, remote-tag, GitHub-Release,
and model drift.

Options:
  --plugin        Check the installed Codex Marketplace plugin surface only
  --readiness     Compact machine-friendly global installation freshness output
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
  local skill
  if [[ -f "$marker" ]]; then
    tr -d '[:space:]' < "$marker"
    return 0
  fi
  for skill in "${SKILLS[@]}" "${RETIRED_SKILLS[@]}"; do
    if [[ -e "$dest_root/$skill" || -L "$dest_root/$skill" ]]; then
      echo "unknown"
      return 0
    fi
  done
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
      config="$CODEX_HOME_DIR/hooks.json"
      notifier="$CODEX_HOME_DIR/teamwork/notify.py"
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
  if output="$(python3 "$ROOT/scripts/configure-codex-routing.py" \
    --check --config "$CODEX_HOME_DIR/config.toml" 2>/dev/null)"; then
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
  local skill source_file dest_item rel drift=0 missing=0 extra=0
  [[ -d "$dest_root" ]] || { echo "missing"; return 0; }
  for skill in "${SKILLS[@]}"; do
    while IFS= read -r -d '' source_file; do
      rel="${source_file#$ROOT/skills/}"
      if [[ ! -f "$dest_root/$rel" ]]; then
        missing=$((missing + 1))
      elif ! cmp -s "$source_file" "$dest_root/$rel"; then
        drift=$((drift + 1))
      fi
    done < <(find "$ROOT/skills/$skill" -type f -print0)

    if [[ -d "$dest_root/$skill" && ! -L "$dest_root/$skill" ]]; then
      while IFS= read -r -d '' dest_item; do
        rel="${dest_item#$dest_root/}"
        if [[ ! -e "$ROOT/skills/$rel" && ! -L "$ROOT/skills/$rel" ]]; then
          extra=$((extra + 1))
        fi
      done < <(find "$dest_root/$skill" -mindepth 1 -print0)
    fi
  done
  for skill in "${RETIRED_SKILLS[@]}"; do
    if [[ -e "$dest_root/$skill" || -L "$dest_root/$skill" ]]; then
      extra=$((extra + 1))
    fi
  done

  if (( missing == 0 && drift == 0 && extra == 0 )); then
    echo "current"
  else
    echo "drift(missing=$missing,changed=$drift,extra=$extra)"
  fi
}

legacy_codex_skills_status() {
  local legacy_root="$CODEX_HOME_DIR/skills"
  local skill
  [[ -d "$legacy_root" ]] || { echo "clear"; return 0; }
  for skill in "${SKILLS[@]}" "${RETIRED_SKILLS[@]}"; do
    if [[ -e "$legacy_root/$skill" || -L "$legacy_root/$skill" ]]; then
      echo "duplicate"
      return 0
    fi
  done
  echo "clear"
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
  local agent source expected tmp missing=0 drift=0 extra=0
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
  while IFS= read -r agent; do
    if [[ -n "$agent" && ( -e "$dest_root/$agent.$ext" || -L "$dest_root/$agent.$ext" ) ]]; then
      extra=$((extra + 1))
    fi
  done < <(python3 - "$ROOT/scripts/tests/fixtures/v3.4.2-owned-surfaces.json" "$platform" "${agents[@]}" <<'PY'
import json
import pathlib
import sys

fixture = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
platform = sys.argv[2]
active = set(sys.argv[3:])
prefix = f"managed://installed-agent/{platform}/"
old = set()
for row in fixture.get("deterministic_surfaces", []):
    path = row.get("path", "")
    if row.get("surface_class") != "profile-rendered-agent" or not path.startswith(prefix):
        continue
    old.add(path.rsplit("/", 1)[-1].rsplit(".", 1)[0])
for name in sorted(old - active):
    print(name)
PY
  )
  rm -rf "$tmp"
  if (( missing == 0 && drift == 0 && extra == 0 )); then
    echo "current"
  else
    echo "drift(missing=$missing,changed=$drift,extra=$extra)"
  fi
}

render_codex_agent_expected() {
  local source="$1" expected="$2" agent="$3" model effort
  read -r model effort < <(CODEX_PROFILE="$(source_profile)" codex_agent_profile_values "$agent")
  sed \
    -e "s/^model = .*/model = \"$model\"/" \
    -e "s/^model_reasoning_effort = .*/model_reasoning_effort = \"$effort\"/" \
    "$source" > "$expected"
}

render_claude_agent_expected() {
  local source="$1" expected="$2" agent="$3" model effort
  read -r model effort < <(CODEX_PROFILE="$(source_profile)" claude_agent_profile_values "$agent")
  sed \
    -e "s/^model: .*/model: $model/" \
    -e "s/^effort: .*/effort: $effort/" \
    "$source" > "$expected"
}

render_cursor_agent_expected() {
  local source="$1" expected="$2" agent="$3" model
  read -r model < <(CODEX_PROFILE="$(source_profile)" cursor_agent_profile_values "$agent")
  sed -e "s/^model: .*/model: $model/" "$source" > "$expected"
}

policy_status() {
  local platform="$1"
  local file start_marker end_marker expected actual
  case "$platform" in
    codex)
      file="$CODEX_HOME_DIR/AGENTS.md"
      start_marker="<!-- TEAMWORK_CODEX_GLOBAL_START -->"
      end_marker="<!-- TEAMWORK_CODEX_GLOBAL_END -->"
      expected="$(write_teamwork_codex_global_policy)"
      ;;
    claude)
      file="$HOME/.claude/CLAUDE.md"
      start_marker="<!-- TEAMWORK_CLAUDE_GLOBAL_START -->"
      end_marker="<!-- TEAMWORK_CLAUDE_GLOBAL_END -->"
      expected="$(write_teamwork_claude_global_policy)"
      ;;
    cursor)
      echo "manual"
      return 0
      ;;
  esac

  [[ -f "$file" ]] || { echo "missing"; return 0; }
  actual="$(awk -v start="$start_marker" -v end="$end_marker" '
    $0 == start { capture = 1 }
    capture { print }
    $0 == end { capture = 0 }
  ' "$file")"

  if [[ "$actual" == "$expected" ]]; then
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
  local agent_file="$HOME/.cursor/agents/explorer.md"
  [[ -f "$agent_file" ]] || { echo "missing"; return 0; }
  sed -n 's/^model: //p' "$agent_file" | head -n1
}

installed_profile_marker_status() {
  local profiles=() root value first
  for root in "$HOME/.agents/skills" "$HOME/.cursor/skills" "$HOME/.claude/skills"; do
    if [[ -f "$root/.teamwork-profile" ]]; then
      value="$(tr -d '[:space:]' < "$root/.teamwork-profile")"
      profiles+=("$value")
    fi
  done
  if (( ${#profiles[@]} == 0 )); then
    echo "missing"
    return 0
  fi
  first="${profiles[0]}"
  for value in "${profiles[@]}"; do
    if [[ "$value" != "$first" ]]; then
      echo "mixed"
      return 0
    fi
  done
  echo "$first"
}

source_profile() {
  local profile
  if [[ -n "$STATUS_PROFILE_OVERRIDE" ]]; then
    printf '%s\n' "$STATUS_PROFILE_OVERRIDE"
    return 0
  fi
  profile="$(installed_profile_marker_status)"
  if [[ "$profile" == "missing" ]]; then
    echo "performance-first"
    return 0
  fi
  echo "$profile"
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
    git@github.com:*) slug="${slug#*:}" ;;
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

plugin_marker_status() {
  local output
  if output="$(python3 "$ROOT/scripts/plugin-activation.py" status \
    --path "$PLUGIN_ACTIVATION_PATH" \
    --version "$(tr -d '[:space:]' < "$ROOT/VERSION")" 2>/dev/null)"; then
    printf '%s\n' "$output"
  else
    printf '%s\n' "invalid"
  fi
}

plugin_marker_field() {
  local field="$1"
  python3 - "$PLUGIN_ACTIVATION_PATH" "$field" <<'PY'
import json
import pathlib
import sys

try:
    value = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError):
    raise SystemExit(1)
result = value.get(sys.argv[2])
if not isinstance(result, str):
    raise SystemExit(1)
print(result)
PY
}

plugin_catalog_status() {
  local raw
  if ! command -v codex >/dev/null 2>&1; then
    echo "unavailable"
    return 0
  fi
  if ! raw="$(codex plugin list --json 2>/dev/null)"; then
    echo "unavailable"
    return 0
  fi
  TEAMWORK_PLUGIN_LIST_JSON="$raw" python3 - <<'PY'
import json
import os

try:
    data = json.loads(os.environ["TEAMWORK_PLUGIN_LIST_JSON"])
except json.JSONDecodeError:
    print("invalid")
    raise SystemExit()

rows = []
def visit(value):
    if isinstance(value, dict):
        if value.get("name") == "teamwork-skill":
            rows.append(value)
        for child in value.values():
            visit(child)
    elif isinstance(value, list):
        for child in value:
            visit(child)
visit(data)

def marketplace_name(row):
    value = row.get("marketplace")
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("name", "id"):
            if isinstance(value.get(key), str):
                return value[key]
    for key in ("marketplace_name", "marketplaceName"):
        if isinstance(row.get(key), str):
            return row[key]
    return ""

target = [row for row in rows if marketplace_name(row) == "teamwork"]
if not target:
    print("missing" if not rows else "wrong-marketplace")
elif any(row.get("enabled") is False for row in target):
    print("disabled")
else:
    print("enabled")
PY
}

plugin_cache_status() {
  local version cache_root
  version="$(tr -d '[:space:]' < "$ROOT/VERSION")"
  cache_root="$CODEX_HOME_DIR/plugins/cache/teamwork/teamwork-skill"
  python3 - "$cache_root" "$version" <<'PY'
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
version = sys.argv[2]
if not root.is_dir():
    print("missing")
    raise SystemExit()
records = []
for candidate in sorted(root.iterdir()):
    manifest = candidate / ".codex-plugin/plugin.json"
    try:
        value = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        continue
    if value.get("name") == "teamwork-skill":
        records.append((candidate.name, value.get("version")))
if not records:
    print("invalid")
elif any(found_version == version for _, found_version in records):
    print("current(" + ",".join(name for name, found_version in records if found_version == version) + ")")
else:
    print("stale(" + ",".join(f"{name}:{found_version}" for name, found_version in records) + ")")
PY
}

plugin_legacy_skill_status() {
  local root skill
  for root in "$HOME/.agents/skills" "$CODEX_HOME_DIR/skills"; do
    [[ -d "$root" ]] || continue
    for skill in "${SKILLS[@]}" "${RETIRED_SKILLS[@]}"; do
      if [[ -e "$root/$skill" || -L "$root/$skill" ]]; then
        echo "duplicate"
        return 0
      fi
    done
  done
  echo "clear"
}

plugin_notification_is_ready() {
  local expected="$1"
  local actual="$2"
  case "$expected:$actual" in
    disabled:disabled)
      return 0
      ;;
    enabled:installed|enabled:review-required|enabled:runtime-unverified)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

print_plugin_readiness() {
  local source_version marker profile notifications catalog cache legacy agents agent_content routing policy notification
  source_version="$(tr -d '[:space:]' < "$ROOT/VERSION")"
  marker="$(plugin_marker_status)"
  profile="$(plugin_marker_field profile 2>/dev/null || echo "unknown")"
  notifications="$(plugin_marker_field notifications 2>/dev/null || echo "unknown")"
  STATUS_PROFILE_OVERRIDE="$profile"
  catalog="$(plugin_catalog_status)"
  cache="$(plugin_cache_status)"
  legacy="$(plugin_legacy_skill_status)"
  agents="$(agents_status "$CODEX_HOME_DIR/agents" toml "${CODEX_AGENTS[@]}")"
  agent_content="$(agents_content_status "$CODEX_HOME_DIR/agents" toml codex "${CODEX_AGENTS[@]}")"
  routing="$(codex_routing_status)"
  policy="$(policy_status codex)"
  notification="$(notification_status codex)"

  local ready=yes
  local missing=()

  [[ "$catalog" == "enabled" ]] || { ready=no; missing+=("plugin-catalog"); }
  [[ "$cache" == current* ]] || { ready=no; missing+=("plugin-cache"); }
  [[ "$marker" == "current" ]] || { ready=no; missing+=("plugin-activation"); }
  [[ "$legacy" == "clear" ]] || { ready=no; missing+=("legacy-skill-copies"); }
  [[ "$agents" == "ok" ]] || { ready=no; missing+=("codex-agents"); }
  [[ "$agent_content" == "current" ]] || { ready=no; missing+=("codex-agent-content"); }
  [[ "$routing" == "ready" ]] || { ready=no; missing+=("codex-routing"); }
  [[ "$policy" == "ok" ]] || { ready=no; missing+=("codex-policy"); }
  if ! plugin_notification_is_ready "$notifications" "$notification"; then
    ready=no
    missing+=("codex-notifications")
  fi

  local manual_actions=("restart-codex")
  if [[ "$notifications" == "enabled" && "$notification" == "review-required" ]]; then
    manual_actions+=("codex-hook-trust")
  elif [[ "$notifications" == "enabled" && "$notification" == "runtime-unverified" ]]; then
    manual_actions+=("codex-hook-inspection")
  fi

  echo "INSTALL_READY=$ready"
  echo "MANAGED_INSTALL_READY=$ready"
  echo "SOURCE_VERSION=$source_version"
  echo "PLUGIN_CATALOG=$catalog"
  echo "PLUGIN_CACHE=$cache"
  echo "PLUGIN_ACTIVATION=$marker"
  echo "PROFILE=$profile"
  echo "CODEX_LEGACY_SKILLS=$legacy"
  echo "CODEX_AGENTS=$agents"
  echo "CODEX_AGENT_CONTENT=$agent_content"
  echo "CODEX_ROUTING=$routing"
  echo "CODEX_POLICY=$policy"
  echo "CODEX_NOTIFICATIONS=$notification"
  echo "MISSING=$(IFS=,; echo "${missing[*]-}")"
  echo "HOST_ACTIVATION=manual-action-required"
  echo "MANUAL_ACTIONS=$(IFS=,; echo "${manual_actions[*]}")"
  if [[ "$catalog" != "enabled" || "$cache" != current* ]]; then
    echo "NEXT=codex plugin marketplace remove teamwork && codex plugin marketplace add JinPLu/Teamwork && codex plugin add teamwork-skill@teamwork && # start a new Codex task and run \$teamwork-update"
  else
    echo "NEXT=# start a new Codex task and run \$teamwork-update to enable or refresh full Teamwork"
  fi
  [[ "$ready" == "yes" ]]
}

print_plugin_report() {
  local readiness_rc=0
  echo "=== Teamwork Codex Marketplace Plugin Report ==="
  echo "Runtime: $ROOT"
  echo "Codex home: $CODEX_HOME_DIR"
  echo
  print_plugin_readiness || readiness_rc=$?
  echo
  echo "Marketplace updates: remove teamwork, add JinPLu/Teamwork without a pinned tag, then reinstall teamwork-skill@teamwork."
  echo "Activation: begin a new Codex task and run \$teamwork-update; first activation requires explicit approval."
  echo "Host action: restart Codex. When notifications are enabled, inspect /hooks and trust only Teamwork Stop and PermissionRequest."
  if (( readiness_rc != 0 )); then
    note_issue
  fi
}

print_readiness() {
  local source_version profile codex_v cursor_v claude_v codex_notifications
  source_version="$(tr -d '[:space:]' < "$ROOT/VERSION")"
  profile="$(source_profile)"
  codex_v="$(read_installed_version "$HOME/.agents/skills")"
  cursor_v="$(read_installed_version "$HOME/.cursor/skills")"
  claude_v="$(read_installed_version "$HOME/.claude/skills")"

  local ready=yes
  local missing=()

  case "$profile" in
    performance-first|cost-first)
      ;;
    *)
      ready=no
      missing+=("profile")
      ;;
  esac

  [[ "$(skills_status "$HOME/.agents/skills")" == "ok" ]] || { ready=no; missing+=("codex-skills"); }
  [[ "$(skills_status "$HOME/.cursor/skills")" == "ok" ]] || { ready=no; missing+=("cursor-skills"); }
  [[ "$(skills_status "$HOME/.claude/skills")" == "ok" ]] || { ready=no; missing+=("claude-skills"); }
  [[ "$(skills_content_status "$HOME/.agents/skills")" == "current" ]] || { ready=no; missing+=("codex-skill-content"); }
  [[ "$(legacy_codex_skills_status)" == "clear" ]] || { ready=no; missing+=("codex-legacy-skills"); }
  [[ "$(skills_content_status "$HOME/.cursor/skills")" == "current" ]] || { ready=no; missing+=("cursor-skill-content"); }
  [[ "$(skills_content_status "$HOME/.claude/skills")" == "current" ]] || { ready=no; missing+=("claude-skill-content"); }
  [[ "$(agents_status "$CODEX_HOME_DIR/agents" toml "${CODEX_AGENTS[@]}")" == "ok" ]] || { ready=no; missing+=("codex-agents"); }
  [[ "$(agents_status "$HOME/.cursor/agents" md "${CURSOR_AGENTS[@]}")" == "ok" ]] || { ready=no; missing+=("cursor-agents"); }
  [[ "$(agents_status "$HOME/.claude/agents" md "${CLAUDE_AGENTS[@]}")" == "ok" ]] || { ready=no; missing+=("claude-agents"); }
  [[ "$(agents_content_status "$CODEX_HOME_DIR/agents" toml codex "${CODEX_AGENTS[@]}")" == "current" ]] || { ready=no; missing+=("codex-agent-content"); }
  [[ "$(agents_content_status "$HOME/.cursor/agents" md cursor "${CURSOR_AGENTS[@]}")" == "current" ]] || { ready=no; missing+=("cursor-agent-content"); }
  [[ "$(agents_content_status "$HOME/.claude/agents" md claude "${CLAUDE_AGENTS[@]}")" == "current" ]] || { ready=no; missing+=("claude-agent-content"); }
  [[ "$(codex_routing_status)" == "ready" ]] || { ready=no; missing+=("codex-routing"); }
  [[ "$(policy_status codex)" == "ok" ]] || { ready=no; missing+=("codex-policy"); }
  [[ "$(policy_status claude)" == "ok" ]] || { ready=no; missing+=("claude-policy"); }
  missing+=("cursor-policy-manual")

  for v in "$codex_v" "$cursor_v" "$claude_v"; do
    if [[ "$v" != "missing" && "$v" != "unknown" ]] && semver_lt "$v" "$source_version"; then
      ready=no
      missing+=("version-drift")
      break
    fi
  done

  codex_notifications="$(notification_status codex)"
  local manual_actions=("cursor-policy-paste")
  if [[ "$codex_notifications" == "review-required" ]]; then
    manual_actions+=("codex-hook-trust")
  fi

  echo "INSTALL_READY=$ready"
  echo "MANAGED_INSTALL_READY=$ready"
  echo "SOURCE_VERSION=$source_version"
  echo "PROFILE=$profile"
  echo "CODEX_VERSION=$codex_v"
  echo "CURSOR_VERSION=$cursor_v"
  echo "CLAUDE_VERSION=$claude_v"
  echo "CODEX_NOTIFICATIONS=$codex_notifications"
  echo "CODEX_ROUTING=$(codex_routing_status)"
  echo "CLAUDE_NOTIFICATIONS=$(notification_status claude)"
  echo "CURSOR_NOTIFICATIONS=$(notification_status cursor)"
  echo "MISSING=$(IFS=,; echo "${missing[*]-}")"
  echo "HOST_ACTIVATION=manual-action-required"
  echo "MANUAL_ACTIONS=$(IFS=,; echo "${manual_actions[*]}")"
  echo "CURSOR_POLICY_MANUAL=run ./install.sh cursor-policy-copy, then paste into Cursor Settings -> Rules -> User Rules"
  echo "NEXT=cd \"$ROOT\" && ./install.sh all --profile $profile"
  echo "CURSOR_POLICY=./install.sh cursor-policy-copy"
  [[ "$ready" == "yes" ]]
}

print_report() {
  local source_version upstream profile profile_markers remote_tag github_release action
  source_version="$(tr -d '[:space:]' < "$ROOT/VERSION")"
  upstream="$(upstream_version)"
  profile="$(source_profile)"
  profile_markers="$(installed_profile_marker_status)"
  remote_tag="$(latest_remote_tag_version)"
  github_release="$(latest_github_release_version)"

  echo "=== Teamwork Update Report ==="
  echo "Checkout: $ROOT"
  echo "Source VERSION: $source_version"
  echo "Installed profile markers (derived): $profile_markers"
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
        dest_skills="$HOME/.agents/skills"
        dest_agents="$CODEX_HOME_DIR/agents"
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
  local legacy_codex_skills_s
  legacy_codex_skills_s="$(legacy_codex_skills_status)"
  echo "legacy skill root: $legacy_codex_skills_s"
  [[ "$legacy_codex_skills_s" == "clear" ]] || note_issue
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
  echo "Cursor explorer model: $(cursor_model_sample)"
  echo "Expected performance-first Codex: Researcher/Explorer/Debugger/Planner/Worker=GPT-5.5/high, Writer=GPT-5.5/low, Designer/Plan Reviewer=Sol/high, Reviewer=Sol/max"
  echo "Expected cost-first Codex: Researcher/Explorer/Debugger/Planner/Worker=GPT-5.5/medium, Writer=GPT-5.5/low, Designer=Sol/medium, Plan Reviewer/Reviewer=Sol/high"
  echo "Expected cost-first Cursor: Researcher/Explorer=gemini-3.5-flash, Debugger/Designer/Plan Reviewer=gpt-5.6-terra-medium, Planner=gpt-5.6-luna-medium, Worker/Writer=composer-2.5-fast, Reviewer=claude-opus-4-8-thinking-high"
  echo "Expected performance-first Cursor: Researcher=gpt-5.6-terra-medium, Explorer=gemini-3.5-flash, Debugger/Plan Reviewer=claude-opus-4-8-thinking-high, Designer=gpt-5.6-sol-medium, Planner=gpt-5.6-terra-medium, Worker/Writer=composer-2.5-fast, Reviewer=claude-fable-5-thinking-high"
  echo

  echo "--- Optional substrates ---"
  if [[ -d "$HOME/.cursor/projects" ]] && find "$HOME/.cursor/projects" -path '*/mcps/user-codegraph/tools/*.json' -print -quit 2>/dev/null | grep -q .; then
    echo "CodeGraph MCP: configured"
  else
    echo "CodeGraph MCP: not detected (optional)"
  fi
  echo

  echo "--- Recommended actions ---"
  action=1
  if [[ -n "$upstream" ]] && semver_lt "$source_version" "$upstream"; then
    echo "$action. cd \"$ROOT\" && git pull"
    ((action += 1))
  fi
  echo "$action. cd \"$ROOT\" && ./install.sh all --profile $profile"
  ((action += 1))
  echo "$action. Restart Codex after routing changes"
  if [[ "$codex_notification_s" == "review-required" ]]; then
    echo "${action}a. Open Codex CLI, run /hooks, and trust the Teamwork Stop and PermissionRequest hooks"
  elif [[ "$codex_notification_s" == "runtime-unverified" ]]; then
    echo "${action}a. Open Codex CLI and run /hooks to inspect Teamwork notification hook status"
  fi
  ((action += 1))
  echo "$action. ./install.sh cursor-policy-copy  # copy, then paste into Cursor User Rules"
  ((action += 1))
  echo "$action. ./scripts/validate.sh       # maintainer or post-release sanity"
  if [[ -n "$remote_tag" && "$remote_tag" != "$source_version" ]] \
    || [[ -n "$github_release" && "$github_release" != "$source_version" ]]; then
    ((action += 1))
    echo "$action. Maintainer release: publish v$source_version and its GitHub Release after approval"
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
    --plugin)
      PLUGIN_MODE=1
      FETCH_UPSTREAM=0
      shift
      ;;
    --project)
      echo "--project was removed: use ./install.sh all to refresh Teamwork's global skills and agents." >&2
      usage
      exit 2
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

if (( PLUGIN_MODE == 0 )) && [[ -e "$PLUGIN_ACTIVATION_PATH" || -L "$PLUGIN_ACTIVATION_PATH" ]]; then
  PLUGIN_MODE=1
  FETCH_UPSTREAM=0
fi

if (( PLUGIN_MODE )); then
  if (( READINESS )); then
    print_plugin_readiness
  else
    print_plugin_report
  fi
elif (( READINESS )); then
  print_readiness
else
  print_report
fi

exit $(( ISSUES > 0 ? 1 : 0 ))
