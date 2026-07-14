#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=scripts/install/common.sh
source "$ROOT/scripts/install/common.sh"
# shellcheck source=scripts/install/policy.sh
source "$ROOT/scripts/install/policy.sh"
# shellcheck source=scripts/install/profiles.sh
source "$ROOT/scripts/install/profiles.sh"
# shellcheck source=scripts/install/targets.sh
source "$ROOT/scripts/install/targets.sh"

TARGET=""
PROJECT_ROOT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --copy)
      INSTALL_MODE="copy"
      shift
      ;;
    --link)
      INSTALL_MODE="link"
      shift
      ;;
    --notifications)
      NOTIFICATIONS_ACTION="install"
      shift
      ;;
    --no-notifications)
      NOTIFICATIONS_ACTION="remove"
      shift
      ;;
    --codex-routing)
      CODEX_ROUTING_ACTION="configure"
      shift
      ;;
    --no-codex-routing)
      CODEX_ROUTING_ACTION="preserve"
      shift
      ;;
    --project-root)
      [[ $# -ge 2 ]] || { echo "--project-root requires a path." >&2; usage; exit 2; }
      PROJECT_ROOT="$(cd "$2" && pwd)"
      shift 2
      ;;
    --profile)
      [[ $# -ge 2 ]] || { echo "--profile requires a value." >&2; usage; exit 2; }
      CODEX_PROFILE="$2"
      shift 2
      ;;
    --performance-first)
      CODEX_PROFILE="performance-first"
      shift
      ;;
    --cost-first)
      CODEX_PROFILE="cost-first"
      shift
      ;;
    codex|cursor|claude|all|project|init-project|project-codex-agents|codex-agents|cursor-agents|claude-agents|codex-policy|cursor-policy|cursor-policy-copy|claude-policy)
      if [[ -n "$TARGET" ]]; then
        echo "Specify only one install target." >&2
        usage
        exit 2
      fi
      TARGET="$1"
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

validate_codex_profile

case "$NOTIFICATIONS_ACTION" in
  preserve|install|remove)
    ;;
  *)
    echo "TEAMWORK_NOTIFICATIONS_ACTION must be preserve, install, or remove." >&2
    exit 2
    ;;
esac

case "${TARGET:-codex}" in
  all|init-project)
    if [[ "$NOTIFICATIONS_ACTION" == "preserve" ]]; then
      NOTIFICATIONS_ACTION="install"
    fi
    ;;
esac

case "$CODEX_ROUTING_ACTION" in
  configure|preserve)
    ;;
  *)
    echo "TEAMWORK_CODEX_ROUTING must be configure or preserve." >&2
    exit 2
    ;;
esac

if [[ "$NOTIFICATIONS_ACTION" != "preserve" ]]; then
  case "${TARGET:-codex}" in
    codex|claude|all|init-project)
      ;;
    *)
      echo "Notification flags are supported only with codex, claude, all, or init-project targets." >&2
      usage
      exit 2
      ;;
  esac
fi

if [[ -n "$PROJECT_ROOT" && "${TARGET:-codex}" != "project" && "${TARGET:-codex}" != "init-project" && "${TARGET:-codex}" != "project-codex-agents" ]]; then
  echo "--project-root is valid only with the project, project-codex-agents, and init-project targets." >&2
  usage
  exit 2
fi

case "${TARGET:-codex}" in
  codex-policy|cursor-policy|cursor-policy-copy|claude-policy)
    ;;
  *)
    printf '%s\n' "$CODEX_PROFILE" > "$ROOT/.teamwork-profile"
    ;;
esac

case "${TARGET:-codex}" in
  codex)
    install_codex
    ;;
  cursor)
    install_cursor
    ;;
  claude)
    install_claude
    ;;
  all)
    install_all
    ;;
  project)
    install_project
    ;;
  project-codex-agents)
    install_codex_agent_set "${PROJECT_ROOT:-$ROOT}/.codex/agents" "project"
    ;;
  init-project)
    init_project
    ;;
  codex-agents)
    install_codex_agents_home
    ;;
  cursor-agents)
    install_cursor_agents_home
    ;;
  claude-agents)
    install_claude_agents_home
    ;;
  codex-policy)
    write_teamwork_codex_global_policy
    ;;
  cursor-policy)
    write_teamwork_cursor_global_policy
    ;;
  cursor-policy-copy)
    copy_teamwork_cursor_global_policy
    ;;
  claude-policy)
    write_teamwork_claude_global_policy
    ;;
  *)
    usage
    exit 2
    ;;
esac
