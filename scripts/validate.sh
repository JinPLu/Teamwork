#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

TEAMWORK_VALIDATION_MODE="${TEAMWORK_VALIDATION_MODE:-fast}"
while (($#)); do
  case "$1" in
    --fast)
      TEAMWORK_VALIDATION_MODE="fast"
      ;;
    --full|--release)
      TEAMWORK_VALIDATION_MODE="full"
      ;;
    -h|--help)
      printf '%s\n' \
        "Usage: scripts/validate.sh [--fast|--full]" \
        "" \
        "  --fast   Run the default local validation set." \
        "  --full   Run release-grade validation, including install integration." \
        "" \
        "Default: --fast"
      exit 0
      ;;
    *)
      echo "FAIL: unsupported validate option: $1" >&2
      exit 2
      ;;
  esac
  shift
done
export TEAMWORK_VALIDATION_MODE
export PYTHONDONTWRITEBYTECODE=1

source "$ROOT/scripts/validation/common.sh"
source "$ROOT/scripts/validation/package.sh"
source "$ROOT/scripts/validation/contracts.sh"

if is_full_validation; then
  source "$ROOT/scripts/validation/integration.sh"
else
  echo "SKIP: install integration and release-only tests (run ./scripts/validate.sh --full)"
fi

echo "OK: Teamwork skill package validates ($TEAMWORK_VALIDATION_MODE)"
