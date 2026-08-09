#!/usr/bin/env bash
set -euo pipefail

TEAMWORK_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_ROOT_INPUT="$PWD"
PROJECT_ROOT=""
FULL_BOOTSTRAP=0

usage() {
  cat <<'USAGE'
Usage:
  ./scripts/init-project.sh [--project-root PATH] [--full-bootstrap]

Initialize minimal project-local Teamwork context:
  - an empty schema-v4 index at docs/teamwork/index.json
  - the managed Teamwork block in AGENTS.md
  - local Teamwork ignore rules

Typed directories and documents are created later by Writer when material
reusable output first appears. Init never migrates older Teamwork formats.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project-root)
      [[ $# -ge 2 ]] || { echo "--project-root requires a path." >&2; exit 2; }
      PROJECT_ROOT_INPUT="$2"
      shift 2
      ;;
    --full-bootstrap)
      FULL_BOOTSTRAP=1
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

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required to initialize Teamwork project files." >&2
  exit 1
fi

project_files() {
  python3 "$TEAMWORK_ROOT/scripts/init-project-files.py" \
    --project-root "$PROJECT_ROOT_INPUT" "$@"
}

PROJECT_ROOT="$(project_files print-root)"
project_files preflight

write_args=(initialize)
if (( FULL_BOOTSTRAP == 1 )); then
  write_args+=(--full-bootstrap)
fi
project_files "${write_args[@]}"
project_files validate

echo "Teamwork project init complete: $PROJECT_ROOT"
