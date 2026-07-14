#!/usr/bin/env bash

ENTRYPOINT="$ROOT/skills/using-teamwork/SKILL.md"
SKILLS=(
  using-teamwork
  grill-me
  teamwork-debug
  teamwork-init
  teamwork-goal
  teamwork-research
  teamwork-plan
  teamwork-execute
  teamwork-review
  teamwork-update
)
RETIRED_SKILLS=(
  teamwork
  teamwork-design
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

grep_required() {
  local pattern="$1"
  local file="$2"
  local message="$3"
  grep -q "$pattern" "$file" || fail "$message"
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
  local profile="$2"
  local label="$3"
  local policy_words
  policy_words="$(awk '
    /<!-- TEAMWORK_(CODEX|CURSOR|CLAUDE)_GLOBAL_START -->/ { inside = 1 }
    inside { print }
    /<!-- TEAMWORK_(CODEX|CURSOR|CLAUDE)_GLOBAL_END -->/ { inside = 0 }
  ' "$file" | wc -w | tr -d ' ')"
  [[ "$policy_words" -le 190 ]] \
    || fail "$label must remain a guard-only global policy ($policy_words > 190)"
  grep_required "Work within the user's request" "$file" "$label must preserve request scope"
  grep_required 'routine reversible choices' "$file" "$label must permit routine reversible choices"
  grep_required 'Route explicit grill/question-first' "$file" \
    "$label must route explicit grill intent"
  grep_required 'Never invent or hide gaps' "$file" "$label must preserve required-state safety"
  grep_required 'Ask only when the user must supply' "$file" "$label must preserve the shared ask boundary"
  grep_required 'Pause only dependent work' "$file" "$label must scope unresolved-question blocking"
  grep_required 'Delegate only worthwhile independent scope' "$file" \
    "$label must keep delegation economic"
  grep_required 'agents own models; active profile' "$file" \
    "$label must keep model mappings out of global policy"
  grep_required "active profile: ${profile}\. Use project-local init" "$file" "$label must record active profile $profile"
  if [[ "$label" == *Cursor* || "$label" == *Claude* ]]; then
    ! grep -Eq 'request_user_input|Codex CLI|Codex native|every material user decision|grill ceremony|text choice card' "$file" \
      || fail "$label must not contain Codex-native adapter wording"
  fi
}

git_known_package_file() {
  local path="$1"
  git -C "$ROOT" ls-files --error-unmatch "$path" >/dev/null 2>&1 && return 0
  return 1
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
            f"FAIL: {file.relative_to(root)} image is not known to git: {rel}; use git add -N before release validation"
        )
PY
}
