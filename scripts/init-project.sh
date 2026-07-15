#!/usr/bin/env bash
set -euo pipefail

TEAMWORK_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ORIGINAL_ARGS=("$@")
CALLER_PWD="$PWD"
PROJECT_ROOT_INPUT="$PWD"
PROJECT_ROOT=""
INSTALL_MODE_FLAG=""
PROFILE_VALUE=""
RUN_CODEGRAPH="${TEAMWORK_INIT_CODEGRAPH:-1}"
COPY_CURSOR_POLICY="${TEAMWORK_INIT_CURSOR_POLICY_COPY:-1}"
NOTIFICATIONS_ACTION="${TEAMWORK_NOTIFICATIONS_ACTION:-preserve}"
GLOBAL_INSTALL_RC=0
unset TEAMWORK_NOTIFICATIONS_ACTION

usage() {
  cat <<'USAGE'
Usage:
  ./scripts/init-project.sh [--project-root PATH] [--copy|--link] [--profile performance-first|cost-first|gpt56-role|gpt56-high|gpt56-xhigh|gpt55-high|gpt55-xhigh] [--no-codegraph] [--no-cursor-policy-copy]

Initializes a project with full Teamwork defaults:
  - global Codex/Cursor/Claude skills, agents, and managed policies
  - Codex custom-agent routing
  - user-level Codex and Claude Code notifications (use --no-notifications on
    the install.sh init-project entrypoint to opt out)
  - AGENTS.md Teamwork managed block
  - docs/teamwork/ runtime memory entrypoint
  - .gitignore entries for local Teamwork state
  - CodeGraph index when the codegraph CLI is available
  - Cursor User Rules block copied to clipboard when clipboard tooling exists

Safety boundary: the project-root path and each existing caller-path ancestor
must be real directories; symlink components are refused before any write.
USAGE
}

require_python() {
  if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 is required to write Teamwork project init files." >&2
    exit 1
  fi
}

preflight_project_root_input() {
  require_python
  TEAMWORK_PROJECT_ROOT_INPUT="$PROJECT_ROOT_INPUT" \
  TEAMWORK_CALLER_PWD="$CALLER_PWD" \
  python3 <<'PY'
import os
import stat
from pathlib import Path

raw = os.environ["TEAMWORK_PROJECT_ROOT_INPUT"]
caller_pwd = os.environ["TEAMWORK_CALLER_PWD"]
if not raw:
    raise SystemExit("Teamwork project root must not be empty")
if not os.path.isabs(caller_pwd):
    raise SystemExit(f"Teamwork caller PWD must be absolute: {caller_pwd}")

parts = []
if not os.path.isabs(raw):
    parts.extend(caller_pwd.split("/"))
parts.extend(raw.split("/"))
current = Path("/")
for part in parts:
    if part in ("", "."):
        continue
    if part == "..":
        current = current.parent
        continue
    candidate = current / part
    try:
        mode = candidate.lstat().st_mode
    except FileNotFoundError:
        raise SystemExit(f"Teamwork project-root component does not exist: {candidate}")
    if stat.S_ISLNK(mode):
        raise SystemExit(f"refusing symlinked Teamwork project-root component: {candidate}")
    if not stat.S_ISDIR(mode):
        raise SystemExit(f"expected Teamwork project-root directory component: {candidate}")
    current = candidate
PY
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project-root)
      [[ $# -ge 2 ]] || { echo "--project-root requires a path." >&2; exit 2; }
      PROJECT_ROOT_INPUT="$2"
      shift 2
      ;;
    --copy|--link)
      INSTALL_MODE_FLAG="$1"
      shift
      ;;
    --profile)
      [[ $# -ge 2 ]] || { echo "--profile requires a value." >&2; exit 2; }
      PROFILE_VALUE="$2"
      shift 2
      ;;
    --no-codegraph)
      RUN_CODEGRAPH=0
      shift
      ;;
    --project-only)
      echo "--project-only was removed: use ./install.sh --project-root <path> init-project, which always refreshes global Teamwork surfaces." >&2
      usage
      exit 2
      ;;
    --no-cursor-policy-copy)
      COPY_CURSOR_POLICY=0
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

preflight_project_root_input
PROJECT_ROOT="$(cd "$PROJECT_ROOT_INPUT" && pwd -P)"

guard_environment_present() {
  [[ -n "${TEAMWORK_DISCUSSION_GUARD_ROOT_FD:-}" \
    || -n "${TEAMWORK_DISCUSSION_GUARD_DOCS_FD:-}" \
    || -n "${TEAMWORK_DISCUSSION_GUARD_TEAMWORK_FD:-}" \
    || -n "${TEAMWORK_DISCUSSION_GUARD_LOCK_FD:-}" \
    || -n "${TEAMWORK_DISCUSSION_GUARD_TOKEN:-}" ]]
}

verify_inherited_guard_lock_owner() {
  TEAMWORK_PROJECT_ROOT="$PROJECT_ROOT" python3 <<'PY'
import fcntl
import os

names = (
    "TEAMWORK_DISCUSSION_GUARD_ROOT_FD",
    "TEAMWORK_DISCUSSION_GUARD_DOCS_FD",
    "TEAMWORK_DISCUSSION_GUARD_TEAMWORK_FD",
    "TEAMWORK_DISCUSSION_GUARD_LOCK_FD",
    "TEAMWORK_DISCUSSION_GUARD_TOKEN",
)
if any(not os.environ.get(name) for name in names):
    raise SystemExit("incomplete inherited discussion transaction guard")
try:
    lock_fd = int(os.environ["TEAMWORK_DISCUSSION_GUARD_LOCK_FD"])
except ValueError:
    raise SystemExit("invalid inherited discussion transaction guard: lock file descriptor is malformed")
try:
    fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
except OSError as exc:
    raise SystemExit(
        "invalid inherited discussion transaction guard: "
        f"lock descriptor does not own the discussion lock: {exc}"
    )
PY
}

enter_discussion_transaction_guard() {
  if guard_environment_present; then
    verify_inherited_guard_lock_owner
    return
  fi
  export TEAMWORK_NOTIFICATIONS_ACTION="$NOTIFICATIONS_ACTION"
  exec "$TEAMWORK_ROOT/skills/using-teamwork/scripts/discussion-transaction.py" \
    guard --allow-init-recovery --project-root "$PROJECT_ROOT" -- \
    "$TEAMWORK_ROOT/scripts/init-project.sh" "${ORIGINAL_ARGS[@]}"
}

project_files() {
  TEAMWORK_PROJECT_ROOT="$PROJECT_ROOT" \
    python3 "$TEAMWORK_ROOT/scripts/init-project-files.py" "$@"
}

install_global_surfaces() {
  local args=()
  [[ -n "$INSTALL_MODE_FLAG" ]] && args+=("$INSTALL_MODE_FLAG")
  [[ -n "$PROFILE_VALUE" ]] && args+=(--profile "$PROFILE_VALUE")
  args+=(all)
  TEAMWORK_NOTIFICATIONS_ACTION="$NOTIFICATIONS_ACTION" \
    "$TEAMWORK_ROOT/install.sh" "${args[@]}"
}

init_codegraph() {
  if (( RUN_CODEGRAPH == 0 )); then
    echo "CodeGraph: skipped (--no-codegraph)"
    return 0
  fi
  if [[ -d "$PROJECT_ROOT/.codegraph" ]]; then
    echo "CodeGraph: already initialized"
    return 0
  fi
  if ! command -v codegraph >/dev/null 2>&1; then
    echo "CodeGraph: skipped (codegraph CLI not found)"
    return 0
  fi
  if project_files codegraph -- codegraph init -i; then
    echo "CodeGraph: initialized"
  else
    echo "CodeGraph: init failed; continuing with project files in place"
  fi
}

copy_cursor_policy() {
  if (( COPY_CURSOR_POLICY == 0 )); then
    echo "Cursor User Rules: clipboard copy skipped (--no-cursor-policy-copy)"
    return 0
  fi
  if command -v pbcopy >/dev/null 2>&1 \
    || command -v wl-copy >/dev/null 2>&1 \
    || command -v xclip >/dev/null 2>&1 \
    || command -v xsel >/dev/null 2>&1 \
    || command -v clip.exe >/dev/null 2>&1; then
    if [[ -n "$PROFILE_VALUE" ]]; then
      "$TEAMWORK_ROOT/install.sh" --profile "$PROFILE_VALUE" cursor-policy-copy \
        || echo "Cursor User Rules: clipboard copy failed; run ./install.sh cursor-policy-copy manually"
    else
      "$TEAMWORK_ROOT/install.sh" cursor-policy-copy \
        || echo "Cursor User Rules: clipboard copy failed; run ./install.sh cursor-policy-copy manually"
    fi
  else
    echo "Cursor User Rules: clipboard tool not found; run ./install.sh cursor-policy-copy manually"
  fi
}

enter_discussion_transaction_guard
project_files preflight
project_files migrate
if install_global_surfaces; then
  :
else
  GLOBAL_INSTALL_RC=$?
  echo "Global Teamwork surfaces: failed; continuing with project context setup" >&2
fi
init_codegraph
project_files write-context
if project_files validate; then
  echo "Teamwork memory: index valid"
else
  echo "Teamwork memory: index invalid; inspect $PROJECT_ROOT/docs/teamwork/index.json" >&2
  exit 1
fi
copy_cursor_policy

if (( GLOBAL_INSTALL_RC != 0 )); then
  echo "Teamwork project context initialized; global setup still requires repair" >&2
  exit "$GLOBAL_INSTALL_RC"
fi

echo "Teamwork project init complete: $PROJECT_ROOT"
