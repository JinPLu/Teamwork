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
    project|project-codex-agents)
      echo "Project-local install targets were removed. Use ./install.sh --project-root <path> init-project to set up only that project's context; refresh global Teamwork surfaces separately." >&2
      usage
      exit 2
      ;;
    codex|cursor|claude|all|init-project|plugin-codex-bootstrap|plugin-init-project|codex-agents|cursor-agents|claude-agents|codex-policy|cursor-policy|cursor-policy-copy|claude-policy)
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

case "${TARGET:-codex}" in
  plugin-codex-bootstrap|plugin-init-project)
    if [[ "$INSTALL_MODE" != "copy" ]]; then
      echo "Marketplace bootstrap targets require --copy so user-level Codex resources remain stable after a plugin cache update." >&2
      exit 2
    fi
    ;;
esac

case "$NOTIFICATIONS_ACTION" in
  preserve|install|remove)
    ;;
  *)
    echo "TEAMWORK_NOTIFICATIONS_ACTION must be preserve, install, or remove." >&2
    exit 2
    ;;
esac

case "${TARGET:-codex}" in
  all|plugin-codex-bootstrap)
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
    codex|claude|all|init-project|plugin-codex-bootstrap|plugin-init-project)
      ;;
    *)
      echo "Notification flags are supported only with codex, claude, all, or init-project targets." >&2
      usage
      exit 2
      ;;
  esac
fi

if [[ -n "$PROJECT_ROOT" && "${TARGET:-codex}" != "init-project" && "${TARGET:-codex}" != "plugin-init-project" ]]; then
  echo "--project-root is valid only with the init-project or plugin-init-project target." >&2
  usage
  exit 2
fi

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
  init-project)
    init_project
    ;;
  plugin-codex-bootstrap)
    install_plugin_codex_bootstrap
    ;;
  plugin-init-project)
    init_plugin_project
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
