CODEGRAPH_PACKAGE="${TEAMWORK_CODEGRAPH_PACKAGE:-@colbymchenry/codegraph}"
CODEGRAPH_VERSION="${TEAMWORK_CODEGRAPH_VERSION:-1.5.0}"
GPU_BROKER_URL="${TEAMWORK_GPU_BROKER_URL:-http://127.0.0.1:8787}"
PREFERENCES_HELPER="$ROOT/scripts/install/preferences.py"
MANAGED_DEPENDENCIES_ACTION="${TEAMWORK_MANAGED_DEPENDENCIES:-}"
MANAGED_DEPENDENCIES_SOURCE=""
MANAGED_CODEGRAPH_ACTION="${TEAMWORK_MANAGED_CODEGRAPH:-}"
MANAGED_CODEGRAPH_SOURCE=""
MANAGED_GPU_BROKER_ACTION="${TEAMWORK_MANAGED_GPU_BROKER:-}"
MANAGED_GPU_BROKER_SOURCE=""
PREFERENCES_STATUS="missing"
MANAGED_DEPENDENCIES_REFRESHED=0

if [[ -n "$MANAGED_DEPENDENCIES_ACTION" ]]; then
  MANAGED_DEPENDENCIES_SOURCE="env"
fi
if [[ -n "$MANAGED_CODEGRAPH_ACTION" ]]; then
  MANAGED_CODEGRAPH_SOURCE="env"
fi
if [[ -n "$MANAGED_GPU_BROKER_ACTION" ]]; then
  MANAGED_GPU_BROKER_SOURCE="env"
fi

managed_dependencies_enabled() {
  managed_codegraph_enabled || managed_gpu_broker_enabled
}

managed_codegraph_enabled() {
  [[ "$MANAGED_CODEGRAPH_ACTION" == "enabled" ]]
}

managed_gpu_broker_enabled() {
  [[ "$MANAGED_GPU_BROKER_ACTION" == "enabled" ]]
}

validate_managed_dependencies_action() {
  local value
  if [[ -n "$MANAGED_DEPENDENCIES_ACTION" ]]; then
    case "$MANAGED_DEPENDENCIES_ACTION" in
      apply|skip|mixed) ;;
      *)
        echo "TEAMWORK_MANAGED_DEPENDENCIES must be apply or skip." >&2
        return 1
        ;;
    esac
  fi
  for value in "$MANAGED_CODEGRAPH_ACTION" "$MANAGED_GPU_BROKER_ACTION"; do
    case "$value" in
      enabled|disabled) ;;
      *)
        echo "Managed CodeGraph and GPU Broker preferences must be enabled or disabled." >&2
        return 1
        ;;
    esac
  done
}

capability_override() {
  local capability="$1" specific_value specific_source aggregate_value="" aggregate_source=""
  case "$capability" in
    codegraph)
      specific_value="$MANAGED_CODEGRAPH_ACTION"
      specific_source="$MANAGED_CODEGRAPH_SOURCE"
      ;;
    gpu_broker)
      specific_value="$MANAGED_GPU_BROKER_ACTION"
      specific_source="$MANAGED_GPU_BROKER_SOURCE"
      ;;
    *)
      return 2
      ;;
  esac
  if [[ -n "$specific_source" ]]; then
    printf '%s %s\n' "$specific_value" "$specific_source"
    return 0
  fi
  if [[ -n "$MANAGED_DEPENDENCIES_SOURCE" ]]; then
    case "$MANAGED_DEPENDENCIES_ACTION" in
      apply) aggregate_value="enabled" ;;
      skip) aggregate_value="disabled" ;;
      *)
        echo "TEAMWORK_MANAGED_DEPENDENCIES must be apply or skip." >&2
        return 1
        ;;
    esac
    aggregate_source="$MANAGED_DEPENDENCIES_SOURCE"
    printf '%s %s\n' "$aggregate_value" "$aggregate_source"
  fi
}

validate_preference_overrides() {
  local value source
  for value in "$MANAGED_CODEGRAPH_ACTION" "$MANAGED_GPU_BROKER_ACTION"; do
    case "$value" in
      ""|enabled|disabled) ;;
      *)
        echo "TEAMWORK_MANAGED_CODEGRAPH and TEAMWORK_MANAGED_GPU_BROKER must be enabled or disabled." >&2
        return 1
        ;;
    esac
  done
  if [[ -n "$MANAGED_DEPENDENCIES_SOURCE" ]]; then
    case "$MANAGED_DEPENDENCIES_ACTION" in
      apply|skip) ;;
      *)
        echo "TEAMWORK_MANAGED_DEPENDENCIES must be apply or skip." >&2
        return 1
        ;;
    esac
  fi
  for source in "$MANAGED_CODEGRAPH_SOURCE" "$MANAGED_GPU_BROKER_SOURCE"; do
    case "$source" in
      ""|cli|env) ;;
      *) return 1 ;;
    esac
  done
}

validate_managed_dependency_target() {
  local target="$1"
  case "$target" in
    codex|all|update|plugin-codex-bootstrap)
      return 0
      ;;
  esac
  if [[ -n "$MANAGED_DEPENDENCIES_SOURCE" \
    || -n "$MANAGED_CODEGRAPH_SOURCE" \
    || -n "$MANAGED_GPU_BROKER_SOURCE" ]]; then
    echo "Managed capability options are supported only with codex, all, update, or plugin-codex-bootstrap targets; '$target' does not manage dependency lifecycles." >&2
    return 1
  fi
}

managed_dependency_lifecycle_target() {
  case "$1" in
    codex|all|update|plugin-codex-bootstrap)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

explicit_capability_choice_is_present() {
  local capability="$1" source
  case "$capability" in
    codegraph)
      source="$MANAGED_CODEGRAPH_SOURCE"
      ;;
    gpu_broker)
      source="$MANAGED_GPU_BROKER_SOURCE"
      ;;
    *)
      return 2
      ;;
  esac
  [[ -n "$source" || -n "$MANAGED_DEPENDENCIES_SOURCE" ]]
}

require_explicit_lifecycle_preferences() {
  local target="$1"
  local missing=() missing_text
  managed_dependency_lifecycle_target "$target" || return 0
  [[ "$PREFERENCES_STATUS" == "missing" ]] || return 0

  [[ -n "$CODEX_PROFILE_SOURCE" ]] || missing+=("profile (--profile performance-first|cost-first)")
  explicit_capability_choice_is_present codegraph \
    || missing+=("CodeGraph (--managed-codegraph|--no-managed-codegraph)")
  explicit_capability_choice_is_present gpu_broker \
    || missing+=("GPU Broker (--managed-gpu-broker|--no-managed-gpu-broker)")

  if ((${#missing[@]} > 0)); then
    missing_text="${missing[0]}"
    for value in "${missing[@]:1}"; do
      missing_text="$missing_text, $value"
    done
    printf 'Missing Teamwork install preferences; %s requires explicit %s before writing global install state.\n' \
      "$target" "$missing_text" >&2
    printf 'For the explicit baseline, use: --profile performance-first --no-managed-codegraph --no-managed-gpu-broker.\n' >&2
    return 2
  fi
}

resolve_install_preferences() {
  local record="$1" result profile codegraph gpu_broker status value source
  local args=(resolve)
  validate_preference_overrides
  if [[ -n "$CODEX_PROFILE_SOURCE" ]]; then
    args+=(--profile "$CODEX_PROFILE" --profile-source "$CODEX_PROFILE_SOURCE")
  fi
  if read -r value source < <(capability_override codegraph) && [[ -n "${value:-}" ]]; then
    args+=(--codegraph "$value" --codegraph-source "$source")
  fi
  if read -r value source < <(capability_override gpu_broker) && [[ -n "${value:-}" ]]; then
    args+=(--gpu-broker "$value" --gpu-broker-source "$source")
  fi
  if [[ "$record" == "record" ]]; then
    args+=(--record)
  fi
  result="$(python3 "$PREFERENCES_HELPER" "${args[@]}")"
  IFS=$'\t' read -r profile codegraph gpu_broker status <<< "$result"
  CODEX_PROFILE="$profile"
  MANAGED_CODEGRAPH_ACTION="$codegraph"
  MANAGED_GPU_BROKER_ACTION="$gpu_broker"
  PREFERENCES_STATUS="$status"
  if [[ "$codegraph" == "enabled" && "$gpu_broker" == "enabled" ]]; then
    MANAGED_DEPENDENCIES_ACTION="apply"
  elif [[ "$codegraph" == "disabled" && "$gpu_broker" == "disabled" ]]; then
    MANAGED_DEPENDENCIES_ACTION="skip"
  else
    MANAGED_DEPENDENCIES_ACTION="mixed"
  fi
  validate_managed_dependencies_action
}

persist_install_preferences() {
  resolve_install_preferences record
}

persist_install_preferences_if_recorded() {
  if [[ "$PREFERENCES_STATUS" == "valid" ]]; then
    persist_install_preferences
  fi
}

preference_document_status() {
  python3 "$PREFERENCES_HELPER" status --field status
}

record_capability_result() {
  local capability="$1" observed="$2" action="$3" receipt_status="$4" detail="${5:-}" version="${6:-}"
  local args=(record-capability --capability "$capability" --observed "$observed" --action "$action" --receipt-status "$receipt_status")
  [[ -n "$detail" ]] && args+=(--detail "$detail")
  [[ -n "$version" ]] && args+=(--version "$version")
  python3 "$PREFERENCES_HELPER" "${args[@]}"
}

record_capability_failure() {
  local capability="$1" detail="$2"
  record_capability_result "$capability" failed preflight failed "$detail"
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
  local codegraph_preference gpu_preference
  codegraph_preference="$(managed_capability_preference codegraph)"
  gpu_preference="$(managed_capability_preference gpu_broker)"
  if [[ "$codegraph_preference" == "invalid" || "$gpu_preference" == "invalid" ]]; then
    echo "invalid"
    return 0
  fi
  if [[ "$codegraph_preference" != "enabled" && "$gpu_preference" != "enabled" ]]; then
    echo "skipped"
    return 0
  fi
  if [[ "$codegraph_preference" == "enabled" && "$(codegraph_readiness)" != "ready" ]]; then
    echo "not-ready"
    return 0
  fi
  if [[ "$gpu_preference" == "enabled" ]] \
    && { [[ "$(gpu_broker_source_status)" != "available" ]] \
      || [[ "$(gpu_broker_tool_status)" != "available" ]] \
      || [[ "$(gpu_broker_daemon_status)" != "ready" ]] \
      || [[ "$(gpu_broker_live_status)" != "ready" ]] \
      || [[ "$(gpu_broker_ready_status)" != "ready" ]]; }; then
    echo "not-ready"
    return 0
  fi
  echo "ready"
}

managed_capability_preference() {
  local capability="$1" specific_value specific_source field
  case "$capability" in
    codegraph)
      specific_value="$MANAGED_CODEGRAPH_ACTION"
      specific_source="$MANAGED_CODEGRAPH_SOURCE"
      field="codegraph"
      ;;
    gpu_broker)
      specific_value="$MANAGED_GPU_BROKER_ACTION"
      specific_source="$MANAGED_GPU_BROKER_SOURCE"
      field="gpu-broker"
      ;;
    *)
      echo "invalid"
      return 0
      ;;
  esac
  if [[ "$specific_value" == "enabled" || "$specific_value" == "disabled" ]]; then
    printf '%s\n' "$specific_value"
    return 0
  fi
  if [[ -n "$specific_source" ]]; then
    echo "invalid"
    return 0
  fi
  case "$MANAGED_DEPENDENCIES_ACTION" in
    apply) echo "enabled"; return 0 ;;
    skip) echo "disabled"; return 0 ;;
  esac
  python3 "$PREFERENCES_HELPER" status --field "$field"
}

full_capability_ready() {
  [[ "$(managed_capability_preference codegraph)" == "enabled" ]] \
    && [[ "$(managed_capability_preference gpu_broker)" == "enabled" ]] \
    && [[ "$(managed_dependencies_status)" == "ready" ]]
}

preflight_managed_dependencies() {
  local source
  validate_managed_dependencies_action
  if ! managed_dependencies_enabled; then
    return 0
  fi
  if managed_codegraph_enabled && ! command -v npm >/dev/null 2>&1; then
    record_capability_failure codegraph "npm is required to refresh managed CodeGraph" || true
    echo "npm is required to refresh managed CodeGraph $CODEGRAPH_PACKAGE@$CODEGRAPH_VERSION." >&2
    return 1
  fi
  if ! managed_gpu_broker_enabled; then
    return 0
  fi
  if ! command -v python3 >/dev/null 2>&1; then
    record_capability_failure gpu_broker "python3 is required to verify managed GPU Broker" || true
    echo "python3 is required to verify managed GPU Broker health." >&2
    return 1
  fi
  if ! command -v uv >/dev/null 2>&1; then
    record_capability_failure gpu_broker "uv is required to install managed GPU Broker" || true
    echo "uv is required to install the managed GPU Broker companion." >&2
    return 1
  fi
  source="$(gpu_broker_source)"
  if [[ -z "$source" || ! -d "$source" ]]; then
    record_capability_failure gpu_broker "GPU Broker companion source is unavailable" || true
    echo "GPU Broker companion source is unavailable. Set TEAMWORK_GPU_BROKER_SOURCE to its local checkout." >&2
    return 1
  fi
  if [[ ! -f "$source/pyproject.toml" ]]; then
    record_capability_failure gpu_broker "GPU Broker companion source is not a Python project" || true
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
    echo "Managed capabilities: skipped by recorded preference"
    MANAGED_DEPENDENCIES_REFRESHED=1
    return 0
  fi
  preflight_managed_dependencies
  if managed_codegraph_enabled; then
    echo "Managed CodeGraph: refreshing $CODEGRAPH_VERSION"
    if refresh_codegraph_dependency; then
      record_capability_result codegraph ready refresh ready "CodeGraph reached the pinned version" "$CODEGRAPH_VERSION"
    else
      record_capability_result codegraph failed refresh failed "CodeGraph refresh did not reach the pinned version" || true
      return 1
    fi
  fi
  if managed_gpu_broker_enabled; then
    echo "Managed GPU Broker: refreshing local companion"
    if refresh_gpu_broker_dependency; then
      record_capability_result gpu_broker ready refresh ready "GPU Broker daemon/live/ready checks passed"
    else
      record_capability_result gpu_broker failed refresh failed "GPU Broker refresh did not become ready" || true
      return 1
    fi
  fi
  MANAGED_DEPENDENCIES_REFRESHED=1
}
