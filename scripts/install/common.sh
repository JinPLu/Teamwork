INSTALL_MODE="${TEAMWORK_INSTALL_MODE:-copy}"
CODEX_PROFILE="${TEAMWORK_CODEX_PROFILE:-performance-first}"
NOTIFICATIONS_ACTION="${TEAMWORK_NOTIFICATIONS_ACTION:-preserve}"
CODEX_ROUTING_ACTION="${TEAMWORK_CODEX_ROUTING:-configure}"
CURSOR_MCP_ACTION="${TEAMWORK_CURSOR_MCP_ACTION:-apply}"
CODEX_USER_SKILLS_ROOT="$HOME/.agents/skills"
PKG_VERSION="unknown"
if [[ -f "$ROOT/VERSION" ]]; then
  PKG_VERSION="$(tr -d '[:space:]' < "$ROOT/VERSION")"
fi
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
LEGACY_CODEX_ROUTER_SKILL="teamwork"
MIGRATION_RETIRED_SKILLS=(
  using-teamwork
  teamwork-execute
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

usage() {
  cat <<'USAGE'
Usage:
  ./install.sh [--copy|--link] [--notifications|--no-notifications] [--codex-routing|--no-codex-routing] [--no-mcp] [--profile performance-first|cost-first] \
    [--project-root PATH] \
    codex|cursor|claude|all|init-project|plugin-codex-bootstrap|plugin-init-project|codex-agents|cursor-agents|claude-agents|codex-policy|cursor-policy|cursor-policy-copy|claude-policy|cursor-mcp

Targets:
  codex          Install checkout-based Codex skills, agents, and policy
                 (script default target; Marketplace plugin is the default
                 Codex user install path)
  cursor         Install skills, Cursor agents, register MCP servers, and print cursor-policy guidance
  claude         Install skills, Claude agents, and Teamwork Claude global policy
  all            Install skills, all platform agents, and Codex + Claude global policy
  init-project   Initialize AGENTS.md, docs/teamwork/, ignore rules, and
                 CodeGraph context for one project without changing global
                 skills, agents, policies, routing, or notifications
  plugin-codex-bootstrap
                 Marketplace-internal Codex-only activation: install agents,
                 routing, managed policy, and optional notifications without
                 copying skills to ~/.agents/skills
  plugin-init-project
                 Marketplace-internal project context setup from the bundled
                 runtime (use --project-root for another repo)
  codex-agents   Install Teamwork Codex custom agents to ~/.codex/agents
                 and configure their user-level routing unless opted out
  cursor-agents  Install Teamwork Cursor subagents to ~/.cursor/agents
  cursor-mcp     Register Teamwork MCP servers in ~/.cursor/mcp.json
  claude-agents  Install Teamwork Claude subagents to ~/.claude/agents
  codex-policy   Print the Teamwork Codex global policy block for App Personalization
  cursor-policy  Print the Teamwork Cursor global policy block for User Rules paste
  cursor-policy-copy
                 Copy the Teamwork Cursor global policy block to the clipboard
  claude-policy  Print the Teamwork Claude global policy block for manual review

Default mode is --copy. For Codex users, install through the Marketplace plugin
by default. Use this checkout installer for Cursor, Claude Code, local
development, or manual Codex setups; use --link for local development when
installs should track this checkout.
`--project-root` is valid only with `init-project` or `plugin-init-project`.

The `all` install enables ready/permission sounds for user-level Codex and
Claude Code by default. Direct platform installs leave notifications unchanged
unless --notifications or --no-notifications is used. Marketplace bootstrap
installs Codex notifications by default; use --no-notifications to opt out.
Project init targets never change notifications; notification flags remain
accepted there as compatibility no-ops.
Cursor installs register codegraph and gpu-broker in ~/.cursor/mcp.json by
default. Use --no-mcp to skip MCP registration; enable new servers in Cursor
Settings -> MCP when prompted.
--no-notifications removes only Teamwork-owned handlers. Cursor notification
installs are intentionally unsupported until their local hook contracts are
live-verified.

User-level Codex installs configure ~/.codex/config.toml with the stable
multi_agent feature enabled so the runtime can select installed Teamwork agent
roles. Use --no-codex-routing only when another owner manages that feature.
Project init never changes user-level routing; run a Codex global install or
codex-agents separately when that surface needs refresh.

Profile defaults to performance-first on all platforms. On Codex, performance-first
uses GPT-5.5/high for Researcher, Explorer, Debugger, Planner, and Worker;
GPT-5.5/low for Writer; Sol/high for Designer and Plan Reviewer; and Sol/max for Reviewer. On Codex,
cost-first uses GPT-5.5/medium for Researcher, Explorer, Debugger, Planner, and
Worker; GPT-5.5/low for Writer; Sol/medium for Designer;
and Sol/high for Plan Reviewer and Reviewer. Cursor and Claude Code keep their existing profile mappings.
Writer is fixed to the simplest model in both profiles.
USAGE
}


validate_codex_profile() {
  case "$CODEX_PROFILE" in
    performance-first|cost-first)
      ;;
    *)
      echo "Unknown profile: $CODEX_PROFILE" >&2
      usage
      exit 2
      ;;
  esac
}


V342_OWNED_SURFACES="$ROOT/scripts/tests/fixtures/v3.4.2-owned-surfaces.json"
V342_CODEX_AGENTS_PREFLIGHTED=0
V342_CURSOR_AGENTS_PREFLIGHTED=0
V342_CLAUDE_AGENTS_PREFLIGHTED=0
V342_CODEX_AGENT_NAMES=""
V342_CURSOR_AGENT_NAMES=""
V342_CLAUDE_AGENT_NAMES=""
PLUGIN_V342_SKILL_ROOT=""
PLUGIN_V342_AGENT_PROFILE=""


preflight_v342_skill_root() {
  local root="$1"
  local label="$2"
  python3 - "$V342_OWNED_SURFACES" "$root" "$label" <<'PY'
import hashlib
import json
import pathlib
import stat
import sys

fixture_path = pathlib.Path(sys.argv[1])
root = pathlib.Path(sys.argv[2])
label = sys.argv[3]
try:
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError) as exc:
    print(f"Cannot load the frozen v3.4.2 ownership inventory: {exc}", file=sys.stderr)
    raise SystemExit(1)
if fixture.get("schema_version") != 1:
    print("Unsupported v3.4.2 ownership inventory schema.", file=sys.stderr)
    raise SystemExit(1)

expected = {}
for row in fixture.get("deterministic_surfaces", []):
    path = row.get("path", "")
    if path.startswith("skills/"):
        expected[path.removeprefix("skills/")] = row
if not expected:
    print("Frozen v3.4.2 ownership inventory has no Skill entries.", file=sys.stderr)
    raise SystemExit(1)

expected_skills = {pathlib.PurePosixPath(value).parts[0] for value in expected}
actual = {}
for skill in expected_skills:
    entry = root / skill
    if not entry.is_dir() or entry.is_symlink():
        print(f"{label} has a missing or non-directory v3.4.2 Skill: {skill}", file=sys.stderr)
        raise SystemExit(1)
    for path in entry.rglob("*"):
        rel = path.relative_to(root).as_posix()
        if path.is_dir() and not path.is_symlink():
            continue
        actual[rel] = path

unknown = sorted(set(actual) - set(expected))
missing = sorted(set(expected) - set(actual))
if unknown:
    print(f"{label} contains unknown v3.4.2 Skill content: {unknown[0]}", file=sys.stderr)
    raise SystemExit(1)
if missing:
    print(f"{label} is missing frozen v3.4.2 Skill content: {missing[0]}", file=sys.stderr)
    raise SystemExit(1)

for rel, row in expected.items():
    path = actual[rel]
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode):
        print(f"{label} has the wrong file type for {rel}", file=sys.stderr)
        raise SystemExit(1)
    mode = f"{stat.S_IMODE(info.st_mode):04o}"
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if mode != row.get("mode") or digest != row.get("sha256"):
        print(f"{label} has modified v3.4.2 Skill content: {rel}", file=sys.stderr)
        raise SystemExit(1)

for marker, expected_value in ((".teamwork-version", "3.4.2"), (".teamwork-profile", None)):
    path = root / marker
    try:
        info = path.lstat()
        value = path.read_text(encoding="utf-8").strip()
    except OSError:
        print(f"{label} is missing the v3.4.2 ownership marker {marker}", file=sys.stderr)
        raise SystemExit(1)
    if not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o644:
        print(f"{label} has an invalid v3.4.2 ownership marker {marker}", file=sys.stderr)
        raise SystemExit(1)
    if expected_value is not None and value != expected_value:
        print(f"{label} has an invalid v3.4.2 ownership marker {marker}", file=sys.stderr)
        raise SystemExit(1)
    known_profiles = {
        row.get("profile")
        for row in fixture.get("deterministic_surfaces", [])
        if row.get("surface_class") == "profile-rendered-agent"
    }
    if marker == ".teamwork-profile" and value not in known_profiles:
        print(f"{label} has an unsupported v3.4.2 profile: {value}", file=sys.stderr)
        raise SystemExit(1)
PY
}


v342_agent_profile() {
  local skill_root="$1"
  tr -d '[:space:]' < "$skill_root/.teamwork-profile"
}


v342_agent_flag_name() {
  case "$1" in
    codex) printf '%s\n' V342_CODEX_AGENTS_PREFLIGHTED ;;
    cursor) printf '%s\n' V342_CURSOR_AGENTS_PREFLIGHTED ;;
    claude) printf '%s\n' V342_CLAUDE_AGENTS_PREFLIGHTED ;;
    *) return 1 ;;
  esac
}


v342_agent_names_flag_name() {
  case "$1" in
    codex) printf '%s\n' V342_CODEX_AGENT_NAMES ;;
    cursor) printf '%s\n' V342_CURSOR_AGENT_NAMES ;;
    claude) printf '%s\n' V342_CLAUDE_AGENT_NAMES ;;
    *) return 1 ;;
  esac
}


v342_agent_names() {
  local platform="$1"
  local profile="$2"
  python3 - "$V342_OWNED_SURFACES" "$platform" "$profile" <<'PY'
import json
import pathlib
import sys

fixture = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
prefix = f"managed://installed-agent/{sys.argv[2]}/{sys.argv[3]}/"
for row in fixture.get("deterministic_surfaces", []):
    path = row.get("path", "")
    if row.get("surface_class") == "profile-rendered-agent" and path.startswith(prefix):
        print(path.removeprefix(prefix))
PY
}


preflight_v342_agent_set() {
  local platform="$1"
  local agent_root="$2"
  local skill_root="$3"
  local profile
  [[ -f "$skill_root/.teamwork-version" ]] || return 0
  [[ "$(tr -d '[:space:]' < "$skill_root/.teamwork-version")" == "3.4.2" ]] || return 0
  profile="$(v342_agent_profile "$skill_root")"

  preflight_v342_agent_profile "$platform" "$agent_root" "$profile"
}


preflight_v342_agent_profile() {
  local platform="$1"
  local agent_root="$2"
  local profile="$3"
  local flag names_flag

  python3 - "$V342_OWNED_SURFACES" "$platform" "$profile" "$agent_root" <<'PY'
import hashlib
import json
import pathlib
import stat
import sys

fixture_path = pathlib.Path(sys.argv[1])
platform, profile = sys.argv[2:4]
root = pathlib.Path(sys.argv[4])
try:
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError) as exc:
    print(f"Cannot load the frozen v3.4.2 ownership inventory: {exc}", file=sys.stderr)
    raise SystemExit(1)

prefix = f"managed://installed-agent/{platform}/{profile}/"
expected = {
    row["path"].removeprefix(prefix): row
    for row in fixture.get("deterministic_surfaces", [])
    if row.get("surface_class") == "profile-rendered-agent"
    and row.get("path", "").startswith(prefix)
}
if not expected:
    print(f"Frozen v3.4.2 inventory has no {platform}/{profile} agent profile.", file=sys.stderr)
    raise SystemExit(1)
for name, row in expected.items():
    path = root / name
    try:
        info = path.lstat()
    except OSError:
        print(f"Missing frozen v3.4.2 {platform} agent: {name}", file=sys.stderr)
        raise SystemExit(1)
    if not stat.S_ISREG(info.st_mode):
        print(f"Wrong file type for v3.4.2 {platform} agent: {name}", file=sys.stderr)
        raise SystemExit(1)
    mode = f"{stat.S_IMODE(info.st_mode):04o}"
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if mode != row.get("mode") or digest != row.get("sha256"):
        print(f"Modified v3.4.2 {platform} agent: {name}", file=sys.stderr)
        raise SystemExit(1)
PY

  flag="$(v342_agent_flag_name "$platform")"
  printf -v "$flag" '%s' 1
  names_flag="$(v342_agent_names_flag_name "$platform")"
  printf -v "$names_flag" '%s' "$(v342_agent_names "$platform" "$profile")"
}


remove_v342_agent_set() {
  local platform="$1"
  local agent_root="$2"
  local skill_root="$3"
  local flag profile
  flag="$(v342_agent_flag_name "$platform")"
  [[ "${!flag:-0}" == "1" ]] || return 0
  profile="$(v342_agent_profile "$skill_root")"
  remove_v342_agent_profile "$platform" "$agent_root" "$profile"
}


remove_v342_agent_profile() {
  local platform="$1"
  local agent_root="$2"
  local profile="$3"
  local flag names_flag agent
  flag="$(v342_agent_flag_name "$platform")"
  [[ "${!flag:-0}" == "1" ]] || return 0
  while IFS= read -r agent; do
    [[ -n "$agent" ]] && rm -f "$agent_root/$agent"
  done < <(v342_agent_names "$platform" "$profile")
  printf -v "$flag" '%s' 0
  names_flag="$(v342_agent_names_flag_name "$platform")"
  printf -v "$names_flag" '%s' ""
}


preflight_v342_managed_policy() {
  local platform="$1"
  local policy_file="$2"
  local skill_root="$3"
  [[ -f "$skill_root/.teamwork-version" ]] || return 0
  [[ "$(tr -d '[:space:]' < "$skill_root/.teamwork-version")" == "3.4.2" ]] || return 0

  preflight_v342_managed_policy_file "$platform" "$policy_file"
}


preflight_v342_managed_policy_file() {
  local platform="$1"
  local policy_file="$2"
  python3 - "$V342_OWNED_SURFACES" "$platform" "$policy_file" <<'PY'
import hashlib
import json
import pathlib
import stat
import sys

fixture = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
platform = sys.argv[2]
path = pathlib.Path(sys.argv[3])
try:
    info = path.lstat()
    lines = path.read_bytes().splitlines(keepends=True)
except OSError:
    print(f"Missing frozen v3.4.2 {platform} managed policy: {path}", file=sys.stderr)
    raise SystemExit(1)
if not stat.S_ISREG(info.st_mode):
    print(f"Wrong file type for v3.4.2 {platform} managed policy: {path}", file=sys.stderr)
    raise SystemExit(1)

upper = platform.upper()
start = f"<!-- TEAMWORK_{upper}_GLOBAL_START -->".encode()
end = f"<!-- TEAMWORK_{upper}_GLOBAL_END -->".encode()
starts = [index for index, line in enumerate(lines) if line.rstrip(b"\r\n") == start]
ends = [index for index, line in enumerate(lines) if line.rstrip(b"\r\n") == end]
if len(starts) != 1 or len(ends) != 1 or starts[0] >= ends[0]:
    print(f"Invalid v3.4.2 {platform} managed policy markers: {path}", file=sys.stderr)
    raise SystemExit(1)
block = b"".join(lines[starts[0] : ends[0] + 1])
expected = next(
    (
        row
        for row in fixture.get("deterministic_surfaces", [])
        if row.get("path") == f"managed://{platform}/global-policy"
    ),
    None,
)
if expected is None or hashlib.sha256(block).hexdigest() != expected.get("sha256"):
    print(f"Modified v3.4.2 {platform} managed policy: {path}", file=sys.stderr)
    raise SystemExit(1)
PY
}


preflight_agent_destination() {
  local root="$1"
  local extension="$2"
  local label="$3"
  shift 3
  local agent path platform names_flag preflighted_names=""
  case "$label" in
    Cursor) platform=cursor ;;
    "Claude Code") platform=claude ;;
    *) return 1 ;;
  esac
  names_flag="$(v342_agent_names_flag_name "$platform")"
  preflighted_names="${!names_flag:-}"
  if [[ -e "$root" && ! -d "$root" ]]; then
    echo "$label agent path is not a directory: $root" >&2
    return 1
  fi
  if [[ -d "$root" && ( ! -w "$root" || ! -x "$root" ) ]]; then
    echo "$label agent path is not writable: $root" >&2
    return 1
  fi
  for agent in "$@"; do
    path="$root/$agent.$extension"
    if [[ -e "$path" || -L "$path" ]]; then
      if [[ ! -f "$path" || ! -w "$path" ]]; then
        echo "$label agent is not a writable regular file: $path" >&2
        return 1
      fi
      if ! grep -Fqx "$agent.$extension" <<< "$preflighted_names" \
          && ! teamwork_markdown_agent_file_is_recognized "$path" "$agent"; then
        echo "$label agent $path is not a recognized Teamwork-owned profile; refusing to replace it." >&2
        return 1
      fi
    fi
  done
}


teamwork_skill_entry_has_known_inventory() {
  local root="$1"
  local skill="$2"
  local version="$3"
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
    [[ -e "$source/$rel" || -L "$source/$rel" ]] || return 1
  done < <(find "$entry" -mindepth 1 -print0)
}


retired_copy_is_plugin_owned() {
  local retired="$1"
  local dest="$2"
  local entry rel

  while IFS= read -r -d '' entry; do
    rel="${entry#$dest/}"
    [[ "$rel" == "SKILL.md" ]] || return 1
  done < <(find "$dest" -mindepth 1 -print0)

  return 0
}

remove_retired_skill() {
  local dest_root="$1"
  local retired="$2"
  local dest="$dest_root/$retired"
  local link="$dest/SKILL.md"
  local raw_target resolved

  if [[ -f "$dest_root/.teamwork-version" ]] \
    && [[ "$(tr -d '[:space:]' < "$dest_root/.teamwork-version")" == "3.4.2" ]]; then
    rm -rf "$dest"
    return 0
  fi

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

  preflight_teamwork_skill_root "$dest_root" "$label skill root"
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

plugin_activation_version() {
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
version = value.get("version")
if not isinstance(version, str):
    raise SystemExit(1)
print(version)
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

preflight_teamwork_skill_root() {
  local root="$1"
  local label="$2"
  local marker="$root/.teamwork-version"
  local profile_marker="$root/.teamwork-profile"
  local skill version="unknown" found=0

  if [[ -f "$marker" ]]; then
    version="$(tr -d '[:space:]' < "$marker")"
  fi

  if [[ "$version" == "3.4.2" ]]; then
    preflight_v342_skill_root "$root" "$label"
    return
  fi

  for skill in "${SKILLS[@]}" "${MIGRATION_RETIRED_SKILLS[@]}"; do
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
      if ! teamwork_skill_entry_has_known_inventory "$root" "$skill" "$version"; then
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
  preflight_teamwork_skill_root "$legacy_root" "Legacy Codex skills"
}

legacy_codex_router_copy_is_owned() {
  local legacy_root="$1"
  local entry="$legacy_root/$LEGACY_CODEX_ROUTER_SKILL"

  [[ -e "$entry" || -L "$entry" ]] || return 0
  [[ -d "$entry" && ! -L "$entry" ]] || return 1

  python3 - "$V342_OWNED_SURFACES" "$entry" <<'PY'
import hashlib
import json
import pathlib
import stat
import sys

try:
    fixture = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError):
    raise SystemExit(1)
entry = pathlib.Path(sys.argv[2])
prefix = "skills/using-teamwork/"
expected = {
    path.removeprefix(prefix): row
    for row in fixture.get("deterministic_surfaces", [])
    if (path := row.get("path", "")).startswith(prefix)
}
actual = {
    path.relative_to(entry).as_posix(): path
    for path in entry.rglob("*")
    if not path.is_dir() or path.is_symlink()
}
if not expected or set(actual) != set(expected):
    raise SystemExit(1)

# The legacy generic router was the v3.4.2 using-teamwork tree projected to
# `teamwork`, with only its frontmatter name changed. Freeze that projected
# SKILL.md digest alongside the source inventory digests.
projected_skill_sha256 = (
    "58fe3a16f7fe82ee788d08bd836efa33dc8785c79a8df2144a09718a71dcbeb1"
)
for relative, row in expected.items():
    path = actual[relative]
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode):
        raise SystemExit(1)
    expected_digest = (
        projected_skill_sha256 if relative == "SKILL.md" else row.get("sha256")
    )
    if (
        f"{stat.S_IMODE(info.st_mode):04o}" != row.get("mode")
        or hashlib.sha256(path.read_bytes()).hexdigest() != expected_digest
    ):
        raise SystemExit(1)
PY
}

preflight_owned_legacy_cleanup() {
  local legacy_root="$1"
  local skill entry dir
  local found=0

  [[ -d "$legacy_root" ]] || return 0
  for skill in "${SKILLS[@]}" "${MIGRATION_RETIRED_SKILLS[@]}" "$LEGACY_CODEX_ROUTER_SKILL"; do
    entry="$legacy_root/$skill"
    if [[ "$skill" == "$LEGACY_CODEX_ROUTER_SKILL" ]] \
      && ! legacy_codex_router_copy_is_owned "$legacy_root"; then
      continue
    fi
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

remove_legacy_codex_router_copy() {
  local legacy_root="$1"
  local entry="$legacy_root/$LEGACY_CODEX_ROUTER_SKILL"

  [[ -e "$entry" || -L "$entry" ]] || return 0
  legacy_codex_router_copy_is_owned "$legacy_root" || return 0
  rm -rf "$entry"
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
    remove_legacy_codex_router_copy "$legacy_root"
  fi
}
