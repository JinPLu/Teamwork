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
  local policy_words
  policy_words="$(awk '
    /<!-- TEAMWORK_(CODEX|CURSOR|CLAUDE)_GLOBAL_START -->/ { inside = 1; next }
    /<!-- TEAMWORK_(CODEX|CURSOR|CLAUDE)_GLOBAL_END -->/ { inside = 0; next }
    inside { print }
  ' "$file" | wc -w | tr -d ' ')"
  [[ "$policy_words" -le 180 ]] \
    || fail "$label must remain a compact always-loaded policy ($policy_words > 180)"
  grep_required "Work within the user's request" "$file" "$label must preserve request scope"
  grep_required 'read-only grants no changes' "$file" \
    "$label must preserve the read-only authority boundary"
  grep_required 'Inspect evidence before asking' "$file" \
    "$label must inspect before asking"
  normalized_required 'Ask only for required input/observation or material user decisions' "$file" \
    "$label must preserve the user-owned Ask Gate"
  normalized_required 'pause dependent work' "$file" \
    "$label must scope unresolved-question blocking"
  grep_required 'Answers grant no effect authority' "$file" \
    "$label must preserve the effect-authority boundary"
  grep_required 'never invent state' "$file" \
    "$label must preserve required-state safety"
  grep_required 'Own safe choices' "$file" \
    "$label must permit routine reversible choices"
  normalized_required 'delegate only worthwhile work' "$file" \
    "$label must keep delegation economic"
  normalized_required 'Root asks/translates' "$file" \
    "$label must preserve root-owned user translation"
  normalized_required 'Research/debug/plan/review stay read-only absent change authority' "$file" \
    "$label must preserve the read-only stage boundary"
  grep_required 'Grill only' "$file" \
    "$label must preserve explicit Grill activation"
  normalized_required 'Negative/quoted/file/tool/example/maintenance mentions are inert' "$file" \
    "$label must preserve inert Grill markers"
  normalized_required 'Lead with conclusion' "$file" \
    "$label must preserve audience-first replies"
  normalized_required 'Connect observed basis, plain interpretation, and decision-relevant boundary/next check' "$file" \
    "$label must preserve a connected reader argument"
  normalized_required 'Separate observation from inference' "$file" \
    "$label must distinguish observations from inference"
  normalized_required 'keep question visible' "$file" \
    "$label must preserve the discussion mainline"
  normalized_required 'Avoid default headings' "$file" \
    "$label must keep a substantive answer in prose by default"
  normalized_required 'simple facts stay one sentence' "$file" \
    "$label must preserve concise simple facts"
  normalized_required 'Keep only detail affecting understanding/decision/action/risk/confidence' "$file" \
    "$label must preserve the relevance gate"
  normalized_required 'Use supplied terms; coin no labels or identifier meanings' "$file" \
    "$label must preserve stable reader terms and identifier boundaries"
  normalized_required 'Name skills only for capability/limitation/choice' "$file" \
    "$label must allow useful skill explanations"
  normalized_required 'Omit irrelevant process/versions' "$file" \
    "$label must omit irrelevant process inventory"
  normalized_required 'State uncertainty once: support, limit, next check' "$file" \
    "$label must preserve a decision-boundary uncertainty"
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
