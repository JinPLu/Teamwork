#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE=fast
if [[ "${1:-}" == "--release" || "${1:-}" == "--full" ]]; then
  MODE=release
elif [[ -n "${1:-}" && "${1:-}" != "--fast" ]]; then
  echo "Usage: ./scripts/validate.sh [--fast|--release]" >&2
  exit 2
fi

bash -n "$ROOT/install.sh" "$ROOT/scripts/check-update.sh" \
  "$ROOT/scripts/init-project.sh" "$ROOT/scripts/install/"*.sh

python3 -m json.tool "$ROOT/config/teamwork-topology.json" >/dev/null
python3 -m json.tool "$ROOT/.codex-plugin/plugin.json" >/dev/null
python3 -m json.tool "$ROOT/.claude-plugin/plugin.json" >/dev/null
python3 -m json.tool "$ROOT/hooks/hooks.json" >/dev/null

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest scripts.tests.test_core_flow
PYTHONDONTWRITEBYTECODE=1 python3 "$ROOT/scripts/check-codex-routing.py" \
  --agents-dir "$ROOT/templates/codex-agents" --profiles-only >/dev/null
PYTHONDONTWRITEBYTECODE=1 python3 "$ROOT/scripts/build-codex-plugin.py" --check

if [[ "$MODE" == release ]]; then
  python3 - "$ROOT" <<'PY'
import json
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1])
version = (root / "VERSION").read_text(encoding="utf-8").strip()
if not re.fullmatch(r"\d+\.\d+\.\d+", version):
    raise SystemExit("VERSION must be semver for release")
for relative in (".codex-plugin/plugin.json", ".claude-plugin/plugin.json"):
    manifest = json.loads((root / relative).read_text(encoding="utf-8"))
    if manifest.get("version") != version:
        raise SystemExit(f"{relative} version does not match VERSION")
PY
fi

echo "OK: Teamwork validation ($MODE)"
