#!/usr/bin/env bash

SKILLS=()
while IFS= read -r skill; do
  SKILLS+=("$skill")
done < <(
  find "$ROOT/skills" -mindepth 2 -maxdepth 2 -type f -name SKILL.md \
    -exec dirname {} \; | xargs -n1 basename | sort
)
CANONICAL_SKILL_COUNT=10
RETIRED_SKILLS=(
  teamwork
  using-teamwork
  teamwork-execute
  run-analyze-optimize
  run-analyze-design
  run-analyze-execute
  run-analyze-review
  run-analyze-research
  run-analyze-plan
  run-analyze-goal
  run-analyze-plan-review
  run-analyze-execution-review
)
CLEANUP_PATHS=()

cleanup() {
  if ((${#CLEANUP_PATHS[@]})); then
    rm -rf "${CLEANUP_PATHS[@]}"
  fi
}
trap cleanup EXIT

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

case "${TEAMWORK_VALIDATION_MODE:-fast}" in
  fast|full)
    ;;
  *)
    fail "TEAMWORK_VALIDATION_MODE must be fast or full"
    ;;
esac

is_full_validation() {
  [[ "${TEAMWORK_VALIDATION_MODE:-fast}" == "full" ]]
}

validation_note() {
  printf 'SKIP: %s\n' "$*" >&2
}

grep_required() {
  local pattern="$1"
  local file="$2"
  local message="$3"
  grep -q "$pattern" "$file" || fail "$message"
}

grep_required_ci() {
  local pattern="$1"
  local file="$2"
  local message="$3"
  grep -qi "$pattern" "$file" || fail "$message"
}

normalized_required() {
  local pattern="$1"
  local file="$2"
  local message="$3"
  local text
  text="$(tr '\n' ' ' < "$file")"
  [[ "$text" == *"$pattern"* ]] || fail "$message"
}

grep_absent() {
  local pattern="$1"
  local message="$2"
  shift 2
  if grep -R -q "$pattern" "$@"; then
    fail "$message"
  fi
}

line_count_max() {
  local file="$1"
  local max="$2"
  local message="$3"
  local count
  count="$(wc -l < "$file" | tr -d ' ')"
  [[ "$count" -le "$max" ]] || fail "$message ($count > $max)"
}

word_count_max() {
  local file="$1"
  local max="$2"
  local message="$3"
  local count
  count="$(wc -w < "$file" | tr -d ' ')"
  [[ "$count" -le "$max" ]] || fail "$message ($count > $max)"
}

fenced_block_line_count_max() {
  local file="$1"
  local max="$2"
  local message="$3"
  awk -v max="$max" -v message="$message" '
    /^```/ {
      if (in_block && count > max) {
        printf "FAIL: %s in %s (%d > %d)\n", message, FILENAME, count, max > "/dev/stderr"
        exit 1
      }
      in_block = !in_block
      count = 0
      next
    }
    in_block { count++ }
    END {
      if (in_block && count > max) {
        printf "FAIL: %s in %s (%d > %d)\n", message, FILENAME, count, max > "/dev/stderr"
        exit 1
      }
    }
  ' "$file" || exit 1
}

check_lean_policy() {
  local file="$1"
  local _profile="$2"
  local label="$3"
  local policy_words policy_text
  policy_words="$(awk '
    /<!-- TEAMWORK_(CODEX|CURSOR|CLAUDE)_GLOBAL_START -->/ { inside = 1; next }
    /<!-- TEAMWORK_(CODEX|CURSOR|CLAUDE)_GLOBAL_END -->/ { inside = 0; next }
    inside { print }
  ' "$file" | wc -w | tr -d ' ')"
  [[ "$policy_words" -le 340 ]] \
    || fail "$label must remain a compact always-loaded policy ($policy_words > 340)"
  policy_text="$(tr '\n' ' ' < "$file")"
  for contract in \
    "request scope::work within the user.?s request" \
    "read-only authority::read.only.{0,100}(authority|effect)" \
    "inspect before asking::inspect.{0,50}(before|prior to).{0,30}ask" \
    "one user-owned question::ask.{0,100}(required input|user.owned decision).{0,100}one at a time" \
    "dependent work only::pause only dependent work" \
    "local-native boundary::local.{0,120}(repository|source|configuration).{0,120}native" \
    "external Research boundary::external.{0,100}(current|multi.source|citation).{0,100}research" \
    "Design ownership::unresolved material direction.{0,60}design" \
    "Plan ownership::plan only translates an already selected direction" \
    "natural Grill no-write::natural question.first intent.{0,80}no file write" \
    "evidence discipline::distinguish observation from inference" \
    "real-path verification::verify.{0,80}real path" \
    "support checks not delivery::tests.{0,100}validation.{0,100}(never replace|support delivery)" \
    "economic delegation::delegate only independent.{0,40}worthwhile" \
    "root question ownership::root owns user questions" \
    "conclusion-first replies::lead with the conclusion" \
    "relevance gate::detail that changes understanding.{0,80}decision.{0,80}risk"; do
    contract_label="${contract%%::*}"
    pattern="${contract#*::}"
    printf '%s\n' "$policy_text" | grep -Eqi "$pattern" \
      || fail "$label must preserve $contract_label"
  done
  if [[ "$label" == *Cursor* || "$label" == *Claude* ]]; then
    ! grep -Eq 'request_user_input|Codex CLI|Codex native|every material user decision|grill ceremony|text choice card' "$file" \
      || fail "$label must not contain Codex-native adapter wording"
  fi
}

git_known_package_file() {
  local path="$1"
  if ! is_full_validation; then
    [[ -e "$ROOT/$path" ]]
    return
  fi
  git -C "$ROOT" ls-files --error-unmatch "$path" >/dev/null 2>&1 && return 0
  return 1
}

run_python_unit_tests() {
  local tests=()
  local test_path module

  if is_full_validation; then
    while IFS= read -r test_path; do
      tests+=("${test_path#"$ROOT"/}")
    done < <(find "$ROOT/scripts/tests" -maxdepth 1 -type f -name 'test_*.py' | sort)
  else
    tests=(
      scripts/tests/test_active_artifact_currentness.py
      scripts/tests/test_discussion_index_safety.py
      scripts/tests/test_evaluation_contract_v4.py
      scripts/tests/test_instruction_footprint.py
      scripts/tests/test_pairwise_comparison.py
      scripts/tests/test_policy_contract_v4.py
      scripts/tests/test_privacy_scan.py
      scripts/tests/test_semantic_review.py
      scripts/tests/test_skill_topology_v4.py
    )
  fi

  for test_path in "${tests[@]}"; do
    [[ -f "$ROOT/$test_path" ]] || fail "missing $test_path"
    module="${test_path%.py}"
    module="${module//\//.}"
    PYTHONPATH="$ROOT/scripts" PYTHONDONTWRITEBYTECODE=1 \
      python3 -m unittest "$module" >/dev/null
  done
}

compile_python_files() {
  local compile_tmp
  compile_tmp="$(mktemp -d)"
  CLEANUP_PATHS+=("$compile_tmp")
  python3 - "$compile_tmp" "$@" <<'PY'
import pathlib
import py_compile
import sys

target_dir = pathlib.Path(sys.argv[1])
for index, source in enumerate(sys.argv[2:]):
    py_compile.compile(
        source,
        cfile=str(target_dir / f"{index}.pyc"),
        doraise=True,
    )
PY
}

check_markdown_local_images() {
  local file="$1"
  python3 - "$ROOT" "$file" <<'PY'
import pathlib
import re
import subprocess
import sys
from urllib.parse import unquote

root = pathlib.Path(sys.argv[1]).resolve()
file = pathlib.Path(sys.argv[2]).resolve()
text = file.read_text()

for raw_target in re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text):
    target = raw_target.strip()
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target):
        continue
    if target.startswith("#"):
        continue
    if target.startswith("<") and ">" in target:
        target = target[1:target.index(">")]
    else:
        target = target.split()[0]
    target = unquote(target)
    asset = (file.parent / target).resolve()
    try:
        rel = asset.relative_to(root)
    except ValueError as exc:
        raise SystemExit(f"FAIL: {file.relative_to(root)} image points outside package: {raw_target}") from exc
    if not asset.is_file():
        raise SystemExit(f"FAIL: {file.relative_to(root)} image missing: {rel}")
    known = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--error-unmatch", str(rel)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if known.returncode != 0:
        raise SystemExit(
            f"FAIL: {file.relative_to(root)} image is absent from the active validation index: {rel}"
        )
PY
}
