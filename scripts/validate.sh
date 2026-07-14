#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

source "$ROOT/scripts/validation/common.sh"
source "$ROOT/scripts/validation/package.sh"
source "$ROOT/scripts/validation/contracts.sh"
source "$ROOT/scripts/validation/integration.sh"

echo "OK: Teamwork skill package validates"
