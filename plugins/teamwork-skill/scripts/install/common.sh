INSTALL_MODE="${TEAMWORK_INSTALL_MODE:-copy}"
CODEX_PROFILE="${TEAMWORK_CODEX_PROFILE:-performance-first}"
NOTIFICATIONS_ACTION="${TEAMWORK_NOTIFICATIONS_ACTION:-preserve}"
CODEX_ROUTING_ACTION="${TEAMWORK_CODEX_ROUTING:-configure}"
CODEX_USER_SKILLS_ROOT="$HOME/.agents/skills"
PKG_VERSION="unknown"
if [[ -f "$ROOT/VERSION" ]]; then
  PKG_VERSION="$(tr -d '[:space:]' < "$ROOT/VERSION")"
fi
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
RETIRED_SKILLS=(
  teamwork
  teamwork-design
  run-analyze-optimize
  run-analyze-design
  run-analyze-execute
  run-analyze-review
  run-analyze-research
  run-analyze-plan
  run-analyze-goal
  run-analyze-plan-review
  run-analyze-execution-review
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
CURSOR_AGENTS=(
  explore
  worker
  designer
  judge
  code-reviewer
  deep-judge
  deep-reviewer
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

usage() {
  cat <<'USAGE'
Usage:
  ./install.sh [--copy|--link] [--notifications|--no-notifications] [--codex-routing|--no-codex-routing] [--profile performance-first|cost-first|gpt56-role|gpt56-high|gpt56-xhigh|gpt55-high|gpt55-xhigh] \
    [--project-root PATH] \
    codex|cursor|claude|all|init-project|plugin-codex-bootstrap|plugin-init-project|codex-agents|cursor-agents|claude-agents|codex-policy|cursor-policy|cursor-policy-copy|claude-policy

Targets:
  codex          Install skills, Codex agents, and Teamwork global policy (default target)
  cursor         Install skills, Cursor agents, and print cursor-policy guidance
  claude         Install skills, Claude agents, and Teamwork Claude global policy
  all            Install skills, all platform agents, and Codex + Claude global policy
  init-project   Refresh global skills, agents, and policies, then initialize
                 AGENTS.md, docs/teamwork/, .gitignore entries, and CodeGraph
                 for one project (use --project-root for another repo)
  plugin-codex-bootstrap
                 Marketplace-internal Codex-only activation: install agents,
                 routing, managed policy, and optional notifications without
                 copying skills to ~/.agents/skills
  plugin-init-project
                 Marketplace-internal Codex-only activation plus project
                 context setup (use --project-root for another repo)
  codex-agents   Install Teamwork Codex custom agents to ~/.codex/agents
                 and configure their user-level routing unless opted out
  cursor-agents  Install Teamwork Cursor subagents to ~/.cursor/agents
  claude-agents  Install Teamwork Claude subagents to ~/.claude/agents
  codex-policy   Print the Teamwork Codex global policy block for App Personalization
  cursor-policy  Print the Teamwork Cursor global policy block for User Rules paste
  cursor-policy-copy
                 Copy the Teamwork Cursor global policy block to the clipboard
  claude-policy  Print the Teamwork Claude global policy block for manual review

Default mode is --copy. Use --link for local development when installs should
track this checkout.
`--project-root` is valid only with `init-project` or `plugin-init-project`.

Full installs (`all` and `init-project`) install ready/permission sounds for
user-level Codex and Claude Code by default. Direct platform installs leave
notifications unchanged unless --notifications or --no-notifications is used.
Marketplace bootstrap targets install Codex notifications by default; use
--no-notifications to opt out.
--no-notifications removes only Teamwork-owned handlers. Cursor notification
installs are intentionally unsupported until their local hook contracts are
live-verified.

User-level Codex installs configure ~/.codex/config.toml so the runtime can
select installed Teamwork agent roles and run one main thread plus up to eight
subagents. Use --no-codex-routing only when another owner manages that routing
contract; init-project refreshes the user-level routing before project setup.

Profile defaults to performance-first on all platforms. For Codex it uses a
GPT-5.6 role split: Terra medium for Explorer; Sol medium for Worker; Sol high
for Designer, Judge, and Reviewer; Sol max for Deep Judge/Reviewer. gpt56-role
is a compatibility alias for the same Codex mapping. cost-first uses Luna for
routine reading/design, Terra for implementation, and Sol for review. Use
gpt56-high or gpt56-xhigh to pin every Codex agent to Sol; legacy gpt55-high and
gpt55-xhigh names remain compatibility aliases and no longer emit GPT-5.5.
Non-Codex platforms keep current native model families for the same profiles.
USAGE
}


validate_codex_profile() {
  case "$CODEX_PROFILE" in
    performance-first|cost-first|gpt56-role|gpt56-high|gpt56-xhigh|gpt55-high|gpt55-xhigh)
      ;;
    *)
      echo "Unknown profile: $CODEX_PROFILE" >&2
      usage
      exit 2
      ;;
  esac
}


retired_copy_is_plugin_owned() {
  local retired="$1"
  local dest="$2"
  local entry rel

  while IFS= read -r -d '' entry; do
    rel="${entry#$dest/}"
    case "$rel" in
      SKILL.md)
        ;;
      references)
        [[ "$retired" == "teamwork" ]] || return 1
        ;;
      references/*)
        [[ "$retired" == "teamwork" ]] || return 1
        [[ -f "$ROOT/skills/using-teamwork/$rel" ]] || return 1
        ;;
	      *)
	        return 1
	        ;;
    esac
  done < <(find "$dest" -mindepth 1 -print0)

  return 0
}

remove_retired_skill() {
  local dest_root="$1"
  local retired="$2"
  local dest="$dest_root/$retired"
  local link="$dest/SKILL.md"
  local raw_target resolved

  if [[ -L "$dest" ]]; then
    raw_target="$(readlink "$dest" 2>/dev/null || true)"
    resolved="$(readlink -f "$dest" 2>/dev/null || true)"
    if [[ "$raw_target" == */skills/"$retired" || "$resolved" == */skills/"$retired" ]]; then
      rm -f "$dest"
    fi
    return 0
  fi

  [[ -e "$link" || -L "$link" ]] || return 0

  if [[ -L "$link" ]]; then
    raw_target="$(readlink "$link" 2>/dev/null || true)"
    resolved="$(readlink -f "$link" 2>/dev/null || true)"
    if [[ "$raw_target" == */skills/"$retired"/SKILL.md || "$resolved" == */skills/"$retired"/SKILL.md ]]; then
      rm -f "$link"
      rmdir "$dest" 2>/dev/null || true
    fi
    return 0
  fi

  [[ -f "$link" ]] || return 0
  grep -q "^name: $retired$" "$link" || return 0
  if retired_copy_is_plugin_owned "$retired" "$dest"; then
    rm -rf "$dest"
  fi
}

install_skill_dir() {
  local source="$1"
  local dest="$2"

  rm -rf "$dest"
  mkdir -p "$(dirname "$dest")"
  case "$INSTALL_MODE" in
    copy)
      cp -R "$source" "$dest"
      ;;
    link)
      ln -sfn "$source" "$dest"
      ;;
    *)
      echo "Unknown install mode: $INSTALL_MODE" >&2
      usage
      exit 2
      ;;
  esac
}

install_agent_file() {
  local source="$1"
  local dest="$2"

  rm -f "$dest"
  mkdir -p "$(dirname "$dest")"
  case "$INSTALL_MODE" in
    copy)
      cp "$source" "$dest"
      ;;
    link)
      ln -sfn "$source" "$dest"
      ;;
    *)
      echo "Unknown install mode: $INSTALL_MODE" >&2
      usage
      exit 2
      ;;
  esac
}


install_skill_set() {
  local dest_root="$1"
  local label="$2"
  local skill

  mkdir -p "$dest_root"
  for retired in "${RETIRED_SKILLS[@]}"; do
    remove_retired_skill "$dest_root" "$retired"
  done

  for skill in "${SKILLS[@]}"; do
    install_skill_dir "$ROOT/skills/$skill" "$dest_root/$skill"
  done

  printf '%s\n' "$PKG_VERSION" > "$dest_root/.teamwork-version"
  printf '%s\n' "$CODEX_PROFILE" > "$dest_root/.teamwork-profile"

  echo "Installed $label skills under: $dest_root ($INSTALL_MODE)"
}

codex_home_path() {
  printf '%s\n' "${CODEX_HOME:-$HOME/.codex}"
}

codex_plugin_activation_path() {
  printf '%s/teamwork/plugin-activation.json\n' "$(codex_home_path)"
}

teamwork_plugin_runtime_is_valid() {
  [[ -f "$ROOT/.teamwork-plugin-runtime" ]] \
    && [[ "$(cat "$ROOT/.teamwork-plugin-runtime")" == "TEAMWORK_CODEX_PLUGIN_RUNTIME=1" ]] \
    && [[ -f "$ROOT/.codex-plugin/plugin.json" ]] \
    && grep -q '"name": "teamwork-skill"' "$ROOT/.codex-plugin/plugin.json"
}

plugin_activation_status() {
  local output
  if output="$(python3 "$ROOT/scripts/plugin-activation.py" status \
    --path "$(codex_plugin_activation_path)" \
    --version "$PKG_VERSION" 2>/dev/null)"; then
    printf '%s\n' "$output"
  else
    printf '%s\n' "invalid"
  fi
}

plugin_activation_is_present() {
  [[ -e "$(codex_plugin_activation_path)" || -L "$(codex_plugin_activation_path)" ]]
}

plugin_activation_profile() {
  local path
  path="$(codex_plugin_activation_path)"
  python3 - "$path" <<'PY'
import json
import pathlib
import sys

try:
    value = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError):
    raise SystemExit(1)
profile = value.get("profile")
if not isinstance(profile, str):
    raise SystemExit(1)
print(profile)
PY
}

plugin_activation_notification_setting() {
  local path
  path="$(codex_plugin_activation_path)"
  python3 - "$path" <<'PY'
import json
import pathlib
import sys

try:
    value = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError):
    raise SystemExit(1)
notifications = value.get("notifications")
if not isinstance(notifications, str):
    raise SystemExit(1)
print(notifications)
PY
}

preflight_plugin_runtime() {
  if ! teamwork_plugin_runtime_is_valid; then
    echo "plugin-codex-bootstrap must run from the Teamwork Marketplace runtime." >&2
    return 1
  fi
  if [[ ! -x "$ROOT/scripts/plugin-activation.py" ]]; then
    echo "Teamwork Marketplace runtime is missing the activation writer." >&2
    return 1
  fi
  if [[ -e "$(codex_plugin_activation_path)" || -L "$(codex_plugin_activation_path)" ]]; then
    if [[ "$(plugin_activation_status)" == "invalid" ]]; then
      echo "Teamwork plugin activation marker is invalid or owned by another installation; refusing to overwrite it." >&2
      return 1
    fi
  fi
}

teamwork_skill_entry_is_named() {
  local root="$1"
  local skill="$2"
  local entry="$root/$skill"
  local skill_file="$entry/SKILL.md"
  [[ -f "$skill_file" ]] || return 1
  grep -q "^name: $skill$" "$skill_file"
}

teamwork_skill_entry_identity_is_safe() {
  local root="$1"
  local skill="$2"
  local entry="$root/$skill"
  local skill_file="$entry/SKILL.md"

  if [[ -L "$entry" ]]; then
    teamwork_skill_entry_is_named "$root" "$skill"
    return
  fi
  [[ -d "$entry" ]] || return 1
  [[ ! -e "$skill_file" ]] || teamwork_skill_entry_is_named "$root" "$skill"
}

teamwork_skill_entry_has_known_inventory() {
  local root="$1"
  local skill="$2"
  local entry="$root/$skill"
  local source="$ROOT/skills/$skill"
  local item rel

  if [[ -L "$entry" ]]; then
    teamwork_skill_entry_is_named "$root" "$skill"
    return
  fi
  [[ -d "$entry" ]] || return 1
  while IFS= read -r -d '' item; do
    rel="${item#$entry/}"
    if [[ ! -e "$source/$rel" && ! -L "$source/$rel" ]]; then
      return 1
    fi
  done < <(find "$entry" -mindepth 1 -print0)
}

preflight_teamwork_skill_root() {
  local root="$1"
  local label="$2"
  local marker="$root/.teamwork-version"
  local profile_marker="$root/.teamwork-profile"
  local skill found=0

  for skill in "${SKILLS[@]}"; do
    if [[ -e "$root/$skill" || -L "$root/$skill" ]]; then
      found=1
      if [[ ! -f "$marker" || ! -f "$profile_marker" ]]; then
        echo "$label contains $skill without Teamwork ownership markers; refusing to replace it." >&2
        return 1
      fi
      if ! teamwork_skill_entry_identity_is_safe "$root" "$skill"; then
        echo "$label contains an unrecognized $skill entry; refusing to replace it." >&2
        return 1
      fi
      if ! teamwork_skill_entry_has_known_inventory "$root" "$skill"; then
        echo "$label contains unknown files in $skill; refusing to replace it." >&2
        return 1
      fi
    fi
  done

  if (( found == 0 )) && [[ -e "$marker" || -e "$profile_marker" ]]; then
    if [[ ! -f "$marker" || ! -f "$profile_marker" ]]; then
      echo "$label has incomplete Teamwork ownership markers; refusing to modify it." >&2
      return 1
    fi
  fi
}

preflight_legacy_codex_skills() {
  local legacy_root="$1"
  local marker="$legacy_root/.teamwork-version"
  local profile_marker="$legacy_root/.teamwork-profile"
  local skill found=0

  [[ -d "$legacy_root" ]] || return 0
  for skill in "${SKILLS[@]}"; do
    if [[ -e "$legacy_root/$skill" || -L "$legacy_root/$skill" ]]; then
      found=1
      if [[ ! -f "$marker" || ! -f "$profile_marker" ]]; then
        echo "Legacy Codex skills contain $skill without Teamwork ownership markers; refusing migration." >&2
        return 1
      fi
      if ! teamwork_skill_entry_identity_is_safe "$legacy_root" "$skill"; then
        echo "Legacy Codex skills contain an unrecognized $skill entry; refusing migration." >&2
        return 1
      fi
      if ! teamwork_skill_entry_has_known_inventory "$legacy_root" "$skill"; then
        echo "Legacy Codex skills contain unknown files in $skill; refusing migration." >&2
        return 1
      fi
    fi
  done
  if (( found == 0 )) && [[ -e "$marker" || -e "$profile_marker" ]]; then
    if [[ ! -f "$marker" || ! -f "$profile_marker" ]]; then
      echo "Legacy Codex skills have incomplete Teamwork ownership markers; refusing migration." >&2
      return 1
    fi
  fi
}

preflight_owned_legacy_cleanup() {
  local legacy_root="$1"
  local skill entry dir
  local found=0

  [[ -d "$legacy_root" ]] || return 0
  for skill in "${SKILLS[@]}"; do
    entry="$legacy_root/$skill"
    if [[ -e "$entry" || -L "$entry" ]]; then
      found=1
      if [[ -d "$entry" && ! -L "$entry" ]]; then
        while IFS= read -r -d '' dir; do
          if [[ ! -w "$dir" || ! -x "$dir" ]]; then
            echo "Legacy Codex skill cleanup is not writable at $dir; refusing migration before installing the new root." >&2
            return 1
          fi
        done < <(find "$entry" -type d -print0)
      fi
    fi
  done

  if (( found == 1 )) || [[ -e "$legacy_root/.teamwork-version" || -e "$legacy_root/.teamwork-profile" ]]; then
    if [[ ! -w "$legacy_root" || ! -x "$legacy_root" ]]; then
      echo "Legacy Codex skill cleanup is not writable at $legacy_root; refusing migration before installing the new root." >&2
      return 1
    fi
  fi
}

remove_owned_legacy_codex_skills() {
  local legacy_root="$1"
  local skill retired
  [[ -d "$legacy_root" ]] || return 0

  for skill in "${SKILLS[@]}"; do
    if [[ -e "$legacy_root/$skill" || -L "$legacy_root/$skill" ]]; then
      rm -rf "$legacy_root/$skill"
    fi
  done
  for retired in "${RETIRED_SKILLS[@]}"; do
    remove_retired_skill "$legacy_root" "$retired"
  done
  rm -f "$legacy_root/.teamwork-version" "$legacy_root/.teamwork-profile"
  rmdir "$legacy_root" 2>/dev/null || true
}

install_codex_skill_set() {
  local dest_root="$CODEX_USER_SKILLS_ROOT"
  local legacy_root="$(codex_home_path)/skills"

  preflight_teamwork_skill_root "$dest_root" "Codex user skill root"
  if [[ "$legacy_root" != "$dest_root" ]]; then
    preflight_legacy_codex_skills "$legacy_root"
    preflight_owned_legacy_cleanup "$legacy_root"
  fi
  install_skill_set "$dest_root" "Codex"
  if [[ "$legacy_root" != "$dest_root" ]]; then
    remove_owned_legacy_codex_skills "$legacy_root"
  fi
}
