#!/usr/bin/env bash
set -euo pipefail

TEAMWORK_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_ROOT_INPUT="$PWD"
PROJECT_ROOT=""
RUN_CODEGRAPH="${TEAMWORK_INIT_CODEGRAPH:-0}"
FULL_BOOTSTRAP=0

usage() {
  cat <<'USAGE'
Usage:
  ./scripts/init-project.sh [--project-root PATH] [--codegraph|--no-codegraph] [--full-bootstrap]

Initialize only project-local Teamwork context:
  - the managed Teamwork block in AGENTS.md
  - ordinary durable memory under docs/teamwork/
  - local Teamwork ignore rules
  - a CodeGraph index only after explicit --codegraph consent

This command does not install or refresh global skills, agents, policies,
notifications, or clipboard content. The legacy --copy, --link, --profile,
--project-only, and --no-cursor-policy-copy options are accepted as no-op
compatibility inputs for older install entrypoints.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project-root)
      [[ $# -ge 2 ]] || { echo "--project-root requires a path." >&2; exit 2; }
      PROJECT_ROOT_INPUT="$2"
      shift 2
      ;;
    --no-codegraph)
      RUN_CODEGRAPH=0
      shift
      ;;
    --codegraph)
      RUN_CODEGRAPH=1
      shift
      ;;
    --full-bootstrap)
      FULL_BOOTSTRAP=1
      shift
      ;;
    --copy|--link|--project-only|--no-cursor-policy-copy)
      shift
      ;;
    --profile)
      [[ $# -ge 2 ]] || { echo "--profile requires a value." >&2; exit 2; }
      shift 2
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

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required to initialize Teamwork project files." >&2
  exit 1
fi

project_files() {
  python3 "$TEAMWORK_ROOT/scripts/init-project-files.py" \
    --project-root "$PROJECT_ROOT_INPUT" "$@"
}

project_files preflight
PROJECT_ROOT="$(project_files print-root)"

if (( RUN_CODEGRAPH == 0 )); then
  echo "CodeGraph: skipped (explicit consent not given)"
elif [[ -d "$PROJECT_ROOT/.codegraph" ]]; then
  echo "CodeGraph: already initialized"
elif ! command -v codegraph >/dev/null 2>&1; then
  echo "CodeGraph: skipped (codegraph CLI not found)"
elif project_files codegraph -- codegraph init -i; then
  echo "CodeGraph: initialized"
else
  echo "CodeGraph: init failed; continuing with project files in place" >&2
fi

if (( FULL_BOOTSTRAP == 1 )); then
  project_files write-context --full-bootstrap
else
  project_files write-context
fi
project_files validate

echo "Teamwork project init complete: $PROJECT_ROOT"
