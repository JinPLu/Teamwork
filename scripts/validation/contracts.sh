#!/usr/bin/env bash

# User-facing documentation is validated by outcomes and boundaries, not by
# preserving one historical sentence.
semantic_doc_required() {
  local pattern="$1"
  local file="$2"
  local message="$3"
  tr '\n' ' ' < "$file" | grep -Eqi "$pattern" || fail "$message"
}

for document in README.md README.en.md CODEX.md CURSOR.md CLAUDE.md CONTRIBUTING.md CHANGELOG.md CHANGELOG.en.md; do
  [[ -f "$ROOT/$document" ]] || fail "missing $document"
  git_known_package_file "$document" \
    || fail "$document is absent from the active validation index"
done

semantic_doc_required 'Changelog style.{0,180}4\.2/4\.3.{0,180}one to four.{0,80}bold-led' \
  "$ROOT/CONTRIBUTING.md" "CONTRIBUTING.md must document the durable changelog shape"
semantic_doc_required 'small.{0,100}(do not|never).{0,40}(pad|padding)' \
  "$ROOT/CONTRIBUTING.md" "CONTRIBUTING.md must forbid padding small releases"
semantic_doc_required 'Chinese.{0,120}English.{0,160}(order|point count).{0,160}equivalent' \
  "$ROOT/CONTRIBUTING.md" "CONTRIBUTING.md must require bilingual changelog equivalence"
semantic_doc_required 'user outcome.{0,120}maintainer.{0,160}(internal|implementation)' \
  "$ROOT/CONTRIBUTING.md" "CONTRIBUTING.md must keep changelogs user-facing"

grep_absent 'instruction_footprint\.py|365/975/260|runtime volume owner|line-count shadow|frozen bounded brief|runtime artifacts?|implementation owner|specialized transactions?|generic transactions?|专用事务|通用事务|强角色' \
  "changelogs must omit maintainer-only compactness implementation" \
  "$ROOT/CHANGELOG.md" "$ROOT/CHANGELOG.en.md"

for readme in README.md README.en.md; do
  semantic_doc_required 'Codex.{0,80}Cursor.{0,80}Claude Code' "$ROOT/$readme" \
    "$readme must name all supported hosts"
  semantic_doc_required '(external|outside|外部).{0,80}(research|调研)' "$ROOT/$readme" \
    "$readme must explain external Research"
  semantic_doc_required '(Design.{0,120}Plan|设计.{0,120}计划)' "$ROOT/$readme" \
    "$readme must distinguish Design from Plan"
  semantic_doc_required 'docs/teamwork/discussion/current\.md' "$ROOT/$readme" \
    "$readme must explain the one-file Grill record"
  semantic_doc_required '\./install\.sh all' "$ROOT/$readme" \
    "$readme must show the complete checkout refresh"
  semantic_doc_required 'check-update\.sh --readiness' "$ROOT/$readme" \
    "$readme must show the readiness check"
  check_markdown_local_images "$ROOT/$readme"
done

for guide in CODEX.md CURSOR.md CLAUDE.md; do
  semantic_doc_required '(external|current).{0,80}(research|sources)' "$ROOT/$guide" \
    "$guide must explain external Research"
  semantic_doc_required 'Design.{0,120}(selected|Plan)' "$ROOT/$guide" \
    "$guide must explain the Design/Plan boundary"
  semantic_doc_required '(local|repository).{0,100}(native|natively)' "$ROOT/$guide" \
    "$guide must keep local evidence native"
  semantic_doc_required '(permissions|permission)' "$ROOT/$guide" \
    "$guide must preserve host permission ownership"
  semantic_doc_required 'init-project' "$ROOT/$guide" \
    "$guide must document project initialization"
  semantic_doc_required 'check-update\.sh --readiness' "$ROOT/$guide" \
    "$guide must document readiness"
done

current_version="$(tr -d '[:space:]' < "$ROOT/VERSION")"
[[ "$current_version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || fail "VERSION must be semver"
grep_required "## $current_version -" "$ROOT/CHANGELOG.md" \
  "Chinese changelog must document current VERSION"
grep_required "## $current_version -" "$ROOT/CHANGELOG.en.md" \
  "English changelog must document current VERSION"
python3 - "$ROOT" "$current_version" <<'PY'
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1])
current_version = sys.argv[2]


def sections(name: str) -> list[tuple[str, str]]:
    text = (root / name).read_text(encoding="utf-8")
    headings = list(re.finditer(r"^## (?P<label>[^\n]+)\n", text, flags=re.MULTILINE))
    if not headings:
        raise SystemExit(f"FAIL: {name} has no release sections")
    return [
        (
            match.group("label"),
            text[match.end() : headings[index + 1].start() if index + 1 < len(headings) else len(text)],
        )
        for index, match in enumerate(headings)
    ]


documents = {name: sections(name) for name in ("CHANGELOG.md", "CHANGELOG.en.md")}
labels = {name: [label for label, _body in values] for name, values in documents.items()}
if labels["CHANGELOG.md"] != labels["CHANGELOG.en.md"]:
    raise SystemExit("FAIL: bilingual changelogs must keep identical release order")

for index, label in enumerate(labels["CHANGELOG.md"]):
    bodies = {name: documents[name][index][1] for name in documents}
    shapes: dict[str, tuple[int, bool, bool]] = {}
    for name, body in bodies.items():
        summaries = re.findall(r"^\*\*\S.*\*\*$", body, flags=re.MULTILINE)
        bullets = re.findall(r"^- .+$", body, flags=re.MULTILINE)
        headed_bullets = re.findall(r"^- \*\*[^*\n]+\*\* \S.*$", body, flags=re.MULTILINE)
        if len(summaries) != 1:
            raise SystemExit(f"FAIL: {name} {label} needs one bold summary")
        if not 1 <= len(bullets) <= 4:
            raise SystemExit(f"FAIL: {name} {label} needs one to four changelog points")
        if len(headed_bullets) != len(bullets):
            raise SystemExit(f"FAIL: {name} {label} needs a bold heading on every point")
        action = re.search(r"^(?:升级操作|Upgrade action)[:：]", body, flags=re.MULTILINE) is not None
        limit = re.search(r"^(?:重要限制|Important limit)[:：]", body, flags=re.MULTILINE) is not None
        if re.search(
            r"^(?:升级时|To upgrade|兼容边界|Compatibility boundary)[:：]",
            body,
            flags=re.MULTILINE,
        ):
            raise SystemExit(f"FAIL: {name} {label} uses a noncanonical action or limit label")
        shapes[name] = (len(bullets), action, limit)

    if shapes["CHANGELOG.md"] != shapes["CHANGELOG.en.md"]:
        raise SystemExit(f"FAIL: bilingual changelog shape differs for {label}")

    if label.startswith(f"{current_version} - "):
        points, action, limit = shapes["CHANGELOG.md"]
        if points != 4 or not action or not limit:
            raise SystemExit(
                f"FAIL: current release {label} needs four points, an upgrade action, and an important limit"
            )
PY
semantic_doc_required 'One release unit.*(VERSION|version).*tag.*GitHub Release' \
  "$ROOT/AGENTS.md" "AGENTS.md must own an atomic maintainer release"
semantic_doc_required '(Write changelogs for users|面向用户)' "$ROOT/AGENTS.md" \
  "AGENTS.md must keep changelogs audience-first"
semantic_doc_required '(short, natural summary sentence|一句简短自然的总结)' "$ROOT/AGENTS.md" \
  "AGENTS.md must keep changelogs concise"
semantic_doc_required 'Every release.{0,100}4\.2/4\.3-style.{0,180}one[[:space:]]+to[[:space:]]+four[[:space:]]+concise.{0,80}bold-led points' "$ROOT/AGENTS.md" \
  "AGENTS.md must keep every changelog in the 4.2/4.3 shape"
semantic_doc_required 'substantive.{0,60}normally use four' "$ROOT/AGENTS.md" \
  "AGENTS.md must keep four points for substantive releases"
semantic_doc_required 'Upgrade[[:space:]]+action.{0,80}Important[[:space:]]+limit.{0,100}only when' "$ROOT/AGENTS.md" \
  "AGENTS.md must preserve the 4.2/4.3 action and limit paragraphs"
semantic_doc_required 'user outcome.{0,100}maintainer-only.{0,180}internal scripts.{0,100}numeric thresholds.{0,100}test counts' "$ROOT/AGENTS.md" \
  "AGENTS.md must keep changelogs user-facing"

# instruction_footprint.py is the sole owner of word and byte budgets. This file
# keeps semantic and structural contracts without imposing a second, lower cap.
for writer in \
  write_teamwork_global_policy_body \
  write_teamwork_codex_global_policy \
  write_teamwork_cursor_global_policy \
  write_teamwork_claude_global_policy; do
  grep_required "$writer()" "$ROOT/scripts/install/policy.sh" \
    "installer policy must define $writer"
done
for platform in CODEX CURSOR CLAUDE; do
  grep_required "<!-- TEAMWORK_${platform}_GLOBAL_START -->" "$ROOT/scripts/install/policy.sh" \
    "installer policy must include the $platform managed marker"
done

policy_tmp="$(mktemp -d)"
CLEANUP_PATHS+=("$policy_tmp")
for platform in codex cursor claude; do
  "$ROOT/install.sh" "$platform-policy" > "$policy_tmp/$platform.md"
  check_lean_policy "$policy_tmp/$platform.md" "$platform" "$platform global policy"
done
grep_required 'request_user_input' "$policy_tmp/codex.md" \
  "Codex adapter must use request_user_input when callable"
grep_absent 'request_user_input' "host-neutral policies must not name Codex input tools" \
  "$policy_tmp/cursor.md" "$policy_tmp/claude.md"

# Every public behavior owner is self-contained and reasonably focused. The
# semantic validator checks capability boundaries without freezing prose.
for skill in "${SKILLS[@]}"; do
  skill_file="$ROOT/skills/$skill/SKILL.md"
  fenced_block_line_count_max "$skill_file" 20 "$skill must not embed a large template"
done
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$ROOT/scripts" python3 - <<'PY'
from teamwork_tooling.evaluation.sources import validate_semantic_sources
validate_semantic_sources()
PY

grep_absent 'skills/[a-z0-9-]\+/SKILL\.md' \
  "SKILL.md files must not load another Teamwork skill" \
  "$ROOT/skills"
grep_absent 'using-teamwork\|teamwork-execute' \
  "removed router and generic Execute skill must not remain in active skill sources" \
  "$ROOT/skills"

# Host interaction features remain host-owned.
grep_absent 'default_mode_request_user_input\|codex-native-questions\|configure-codex-native-questions\|code_mode_only' \
  "Teamwork must not install or emulate a host interaction feature" \
  "$ROOT/install.sh" "$ROOT/scripts/install" "$ROOT/scripts/check-update.sh" "$ROOT/scripts/init-project.sh" \
  "$ROOT/skills"

# Codex routing profiles still need structural validation, including collision
# rejection, but the skill package no longer depends on a role-playbook file.
[[ -f "$ROOT/scripts/check-codex-routing.py" ]] || fail "missing scripts/check-codex-routing.py"
compile_python_files "$ROOT/scripts/check-codex-routing.py"
python3 "$ROOT/scripts/check-codex-routing.py" \
  --agents-dir "$ROOT/templates/codex-agents" --profiles-only >/dev/null

codex_profile_tmp="$(mktemp -d)"
CLEANUP_PATHS+=("$codex_profile_tmp")
cp "$ROOT"/templates/codex-agents/*.toml "$codex_profile_tmp/"
python3 - "$codex_profile_tmp/other-agent.toml" <<'PY'
import pathlib
import sys

pathlib.Path(sys.argv[1]).write_text(
    'name = "other_agent"\nnickname_candidates = ["Atlas"]\n',
    encoding="utf-8",
)
PY
if python3 "$ROOT/scripts/check-codex-routing.py" \
  --agents-dir "$codex_profile_tmp" --profiles-only >/dev/null 2>&1; then
  fail "Codex profile validation must reject duplicate nicknames"
fi
