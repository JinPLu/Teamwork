CODEGRAPH_PACKAGE="${TEAMWORK_CODEGRAPH_PACKAGE:-@colbymchenry/codegraph}"
CODEGRAPH_VERSION="${TEAMWORK_CODEGRAPH_VERSION:-1.5.0}"
GPU_BROKER_URL="${TEAMWORK_GPU_BROKER_URL:-http://127.0.0.1:8787}"
MANAGED_DEPENDENCIES_ACTION="${TEAMWORK_MANAGED_DEPENDENCIES:-apply}"

managed_dependencies_enabled() {
  [[ "$MANAGED_DEPENDENCIES_ACTION" == "apply" ]]
}

validate_managed_dependencies_action() {
  case "$MANAGED_DEPENDENCIES_ACTION" in
    apply|skip)
      ;;
    *)
      echo "TEAMWORK_MANAGED_DEPENDENCIES must be apply or skip." >&2
      return 1
      ;;
  esac
}

gpu_broker_source() {
  local sibling receipt
  if [[ -n "${TEAMWORK_GPU_BROKER_SOURCE:-}" ]]; then
    printf '%s\n' "$TEAMWORK_GPU_BROKER_SOURCE"
    return 0
  fi

  sibling="$(cd "$ROOT/.." && pwd)/gpu-broker"
  if [[ -d "$sibling" ]]; then
    printf '%s\n' "$sibling"
    return 0
  fi

  receipt="$HOME/.local/share/uv/tools/gpu-broker/uv-receipt.toml"
  if [[ -f "$receipt" ]] && command -v python3 >/dev/null 2>&1; then
    python3 - "$receipt" <<'PY'
import pathlib
import sys

try:
    import tomllib
    payload = tomllib.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
except (OSError, ValueError, ModuleNotFoundError):
    raise SystemExit(0)

def visit(value):
    if isinstance(value, dict):
        if value.get("name") == "gpu-broker":
            directory = value.get("directory")
            if isinstance(directory, str) and directory:
                print(directory)
                raise SystemExit(0)
        for child in value.values():
            visit(child)
    elif isinstance(value, list):
        for child in value:
            visit(child)

visit(payload)
PY
  fi
}

codegraph_version() {
  local output
  if ! command -v codegraph >/dev/null 2>&1; then
    echo "missing"
    return 0
  fi
  output="$(codegraph --version 2>/dev/null || codegraph version 2>/dev/null || true)"
  if [[ -z "$output" ]]; then
    echo "unknown"
    return 0
  fi
  printf '%s\n' "$output" | sed -n -E 's/.*([0-9]+\.[0-9]+\.[0-9]+).*/\1/p' | head -n1
}

codegraph_readiness() {
  local version
  version="$(codegraph_version)"
  if [[ "$version" == "$CODEGRAPH_VERSION" ]]; then
    echo "ready"
  elif [[ "$version" == "missing" ]]; then
    echo "missing"
  elif [[ -z "$version" || "$version" == "unknown" ]]; then
    echo "unknown"
  else
    echo "stale($version->$CODEGRAPH_VERSION)"
  fi
}

gpu_broker_source_status() {
  local source
  source="$(gpu_broker_source)"
  if [[ -z "$source" || ! -d "$source" ]]; then
    echo "missing"
  else
    echo "available"
  fi
}

gpu_broker_tool_status() {
  command -v gpu-broker >/dev/null 2>&1 && echo "available" || echo "missing"
}

gpu_broker_daemon_status() {
  if command -v gpu-broker >/dev/null 2>&1 \
    && gpu-broker daemon status --json >/dev/null 2>&1; then
    echo "ready"
  else
    echo "unavailable"
  fi
}

gpu_broker_health_status() {
  local endpoint="$1" expected="$2"
  if ! command -v python3 >/dev/null 2>&1; then
    echo "unavailable"
    return 0
  fi
  python3 - "$GPU_BROKER_URL/health/$endpoint" "$expected" <<'PY' 2>/dev/null || echo "unavailable"
import json
import sys
from urllib.request import urlopen

url, expected = sys.argv[1:]
try:
    with urlopen(url, timeout=3) as response:
        payload = json.load(response)
except Exception:
    print("unavailable")
    raise SystemExit(0)
print("ready" if payload.get("status") == expected else "invalid")
PY
}

gpu_broker_live_status() {
  gpu_broker_health_status live live
}

gpu_broker_ready_status() {
  gpu_broker_health_status ready ready
}

managed_dependencies_status() {
  if ! managed_dependencies_enabled; then
    echo "skipped"
    return 0
  fi
  if [[ "$(codegraph_readiness)" == "ready" ]] \
    && [[ "$(gpu_broker_source_status)" == "available" ]] \
    && [[ "$(gpu_broker_tool_status)" == "available" ]] \
    && [[ "$(gpu_broker_daemon_status)" == "ready" ]] \
    && [[ "$(gpu_broker_live_status)" == "ready" ]] \
    && [[ "$(gpu_broker_ready_status)" == "ready" ]]; then
    echo "ready"
  else
    echo "not-ready"
  fi
}

preflight_managed_dependencies() {
  local source
  validate_managed_dependencies_action
  if ! managed_dependencies_enabled; then
    return 0
  fi
  if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 is required to verify managed GPU Broker health." >&2
    return 1
  fi
  if ! command -v npm >/dev/null 2>&1; then
    echo "npm is required to refresh managed CodeGraph $CODEGRAPH_PACKAGE@$CODEGRAPH_VERSION." >&2
    return 1
  fi
  if ! command -v uv >/dev/null 2>&1; then
    echo "uv is required to install the managed GPU Broker companion." >&2
    return 1
  fi
  source="$(gpu_broker_source)"
  if [[ -z "$source" || ! -d "$source" ]]; then
    echo "GPU Broker companion source is unavailable. Set TEAMWORK_GPU_BROKER_SOURCE to its local checkout." >&2
    return 1
  fi
  if [[ ! -f "$source/pyproject.toml" ]]; then
    echo "GPU Broker companion source is not a Python project: $source" >&2
    return 1
  fi
}

refresh_codegraph_dependency() {
  local effective_codegraph
  effective_codegraph="$(command -v codegraph 2>/dev/null || true)"
  if [[ "$effective_codegraph" == "$HOME/.local/bin/codegraph" ]]; then
    npm install --global --force --prefix "$HOME/.local" \
      "$CODEGRAPH_PACKAGE@$CODEGRAPH_VERSION"
  else
    npm install --global "$CODEGRAPH_PACKAGE@$CODEGRAPH_VERSION"
  fi
  if [[ "$(codegraph_readiness)" != "ready" ]]; then
    echo "CodeGraph did not reach the required version $CODEGRAPH_VERSION." >&2
    return 1
  fi
}

refresh_gpu_broker_dependency() {
  local source
  source="$(gpu_broker_source)"
  uv tool install --force "$source"
  gpu-broker daemon install --source-root "$source"
  if [[ "$(gpu_broker_daemon_status)" != "ready" ]] \
    || [[ "$(gpu_broker_live_status)" != "ready" ]] \
    || [[ "$(gpu_broker_ready_status)" != "ready" ]]; then
    echo "GPU Broker did not become daemon/live/ready after refresh." >&2
    return 1
  fi
}

refresh_managed_dependencies() {
  if ! managed_dependencies_enabled; then
    echo "Managed dependencies: skipped (--no-dependencies)"
    return 0
  fi
  preflight_managed_dependencies
  echo "Managed dependencies: CodeGraph $CODEGRAPH_VERSION and local GPU Broker companion"
  refresh_codegraph_dependency
  refresh_gpu_broker_dependency
}
