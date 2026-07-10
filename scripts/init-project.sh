#!/usr/bin/env bash
set -euo pipefail

TEAMWORK_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_ROOT="$PWD"
INSTALL_MODE_FLAG=""
PROFILE_VALUE=""
RUN_CODEGRAPH="${TEAMWORK_INIT_CODEGRAPH:-1}"
INSTALL_GLOBAL=1
COPY_CURSOR_POLICY="${TEAMWORK_INIT_CURSOR_POLICY_COPY:-1}"

usage() {
  cat <<'USAGE'
Usage:
  ./scripts/init-project.sh [--project-root PATH] [--copy|--link] [--profile performance-first|cost-first|gpt56-role|gpt56-high|gpt56-xhigh|gpt55-high|gpt55-xhigh] [--no-codegraph] [--project-only] [--no-cursor-policy-copy]

Initializes a project with full Teamwork defaults:
  - global Codex/Cursor/Claude skills, agents, and managed policies
  - project .cursor/.codex/.claude skills and agents
  - AGENTS.md Teamwork managed block
  - docs/teamwork/ runtime memory entrypoint
  - .gitignore entries for local Teamwork state
  - CodeGraph index when the codegraph CLI is available
  - Cursor User Rules block copied to clipboard when clipboard tooling exists
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project-root)
      [[ $# -ge 2 ]] || { echo "--project-root requires a path." >&2; exit 2; }
      PROJECT_ROOT="$(cd "$2" && pwd)"
      shift 2
      ;;
    --copy|--link)
      INSTALL_MODE_FLAG="$1"
      shift
      ;;
    --profile)
      [[ $# -ge 2 ]] || { echo "--profile requires a value." >&2; exit 2; }
      PROFILE_VALUE="$2"
      shift 2
      ;;
    --no-codegraph)
      RUN_CODEGRAPH=0
      shift
      ;;
    --project-only)
      INSTALL_GLOBAL=0
      shift
      ;;
    --no-cursor-policy-copy)
      COPY_CURSOR_POLICY=0
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

require_python() {
  if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 is required to write Teamwork project init files." >&2
    exit 1
  fi
}

install_global_surfaces() {
  if (( INSTALL_GLOBAL == 0 )); then
    echo "Global Teamwork surfaces: skipped (--project-only)"
    return 0
  fi
  if [[ -n "$INSTALL_MODE_FLAG" && -n "$PROFILE_VALUE" ]]; then
    "$TEAMWORK_ROOT/install.sh" "$INSTALL_MODE_FLAG" --profile "$PROFILE_VALUE" all
  elif [[ -n "$INSTALL_MODE_FLAG" ]]; then
    "$TEAMWORK_ROOT/install.sh" "$INSTALL_MODE_FLAG" all
  elif [[ -n "$PROFILE_VALUE" ]]; then
    "$TEAMWORK_ROOT/install.sh" --profile "$PROFILE_VALUE" all
  else
    "$TEAMWORK_ROOT/install.sh" all
  fi
}

install_project_surfaces() {
  if [[ -n "$INSTALL_MODE_FLAG" && -n "$PROFILE_VALUE" ]]; then
    "$TEAMWORK_ROOT/install.sh" "$INSTALL_MODE_FLAG" --profile "$PROFILE_VALUE" --project-root "$PROJECT_ROOT" project
  elif [[ -n "$INSTALL_MODE_FLAG" ]]; then
    "$TEAMWORK_ROOT/install.sh" "$INSTALL_MODE_FLAG" --project-root "$PROJECT_ROOT" project
  elif [[ -n "$PROFILE_VALUE" ]]; then
    "$TEAMWORK_ROOT/install.sh" --profile "$PROFILE_VALUE" --project-root "$PROJECT_ROOT" project
  else
    "$TEAMWORK_ROOT/install.sh" --project-root "$PROJECT_ROOT" project
  fi
}

write_project_files() {
  require_python
  TEAMWORK_PROJECT_ROOT="$PROJECT_ROOT" \
  TEAMWORK_TODAY="$(date +%F)" \
  python3 <<'PY'
import json
import os
import re
from pathlib import Path

root = Path(os.environ["TEAMWORK_PROJECT_ROOT"])
today = os.environ["TEAMWORK_TODAY"]
project_name = root.name or "Project"


def first_readme_heading() -> str:
    for name in ("README.md", "README.en.md", "readme.md"):
        path = root / name
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("# "):
                return line[2:].strip()
    return ""


project_description = first_readme_heading() or "Project-local Teamwork collaboration state."

docs = root / "docs" / "teamwork"
for directory in (docs, docs / "research", docs / "plans", docs / "reports", docs / "workflows"):
    directory.mkdir(parents=True, exist_ok=True)


def write_if_missing(path: Path, text: str) -> None:
    if not path.exists():
        path.write_text(text, encoding="utf-8")


readme = """# Teamwork Runtime Index README

## Purpose

This local runtime README is the entrypoint for Teamwork memory in this project.
Project instructions may point here, but should not inline this runtime narrative.

## Read Order

1. Read `docs/teamwork/index.json` first.
2. Follow `active` pointers before any broad scan.
3. Prefer headers before full artifact bodies.
4. Use stage-specific profiles from the index.

## Stage Notes

- `research`: read topic headers first, then selective bodies.
- `plan`: read active design/plan before adding or replacing plan state.
- `execute`: read active plan/progress before implementation updates.
- `review`: verify active claims against commands/logs/results.

## Memory Delta Reminder

At non-lightweight stage exit, report one disposition:
`none | current | plan | research | decision | supersede | compact | deferred`.

## Bounds

Keep this file concise and operational.
"""

current = f"""# Teamwork Current State

Last Updated: {today}

## Active Snapshot

- Current focus: Initial Teamwork project setup.
- Active plan/design: none.
- Progress summary: Teamwork runtime memory was initialized for this project.
- Latest result: Project instructions and local runtime surfaces are ready for use.
- Blockers: none recorded.
- Next action: Replace this digest when material project state changes.

## Verification Anchors

- Commands: discover from project files before changing behavior.
- Logs/Artifacts: none recorded.
- Result paths: `docs/teamwork/index.json`, `docs/teamwork/current.md`.

## Supersession

- Supersedes: none.
- Superseded by: none.

## Pending

- None.

## Notes

This is a compact digest, not a running log. Replace in place as state changes.
"""

index = {
    "schema_version": 1,
    "last_updated": today,
    "project": {
        "name": project_name,
        "root": ".",
        "description": project_description,
    },
    "source_of_truth_order": ["active", "linked", "header_search", "fulltext"],
    "ignore_globs": [".planning/**"],
    "budgets": {
        "default_max_files": 5,
        "default_max_artifact_bodies": 2,
        "header_first": True,
    },
    "active": {
        "current": "docs/teamwork/current.md",
        "design": None,
        "plan": None,
        "progress": None,
        "goal": None,
        "report": None,
        "results": [],
    },
    "entries": [
        {
            "topic": "project-initialization",
            "kind": "result",
            "title": "Teamwork project initialization",
            "status": "active",
            "currentness": "current",
            "authority": "active-summary",
            "path": "docs/teamwork/current.md",
            "applies_to": ["AGENTS.md", "docs/teamwork/"],
            "linked": [],
            "evidence_paths": ["docs/teamwork/current.md"],
            "supersedes": [],
            "search_keys": ["teamwork-init", "project-init", "initialization"],
            "updated": today,
            "summary": "Initial Teamwork runtime memory entry created by project init.",
        }
    ],
    "profiles": {
        "status": ["index", "current", "topic"],
        "implementation": ["index", "active_design_or_plan", "linked_research_headers"],
        "review": ["index", "active_design_or_plan", "active_progress", "verification"],
        "research": ["index", "topic_headers", "linked_artifacts"],
        "design": ["index", "accepted_decisions", "active_design_plan", "linked_research"],
    },
    "pending": [],
}

write_if_missing(docs / "README.md", readme)
write_if_missing(docs / "current.md", current)
write_if_missing(docs / "index.json", json.dumps(index, indent=2, ensure_ascii=False) + "\n")

agents_block = f"""<!-- TEAMWORK_PROJECT_START -->
## Teamwork Project Instructions

- Project identity: `{project_name}` - {project_description}
- Teamwork memory: read `docs/teamwork/index.json` first, then `docs/teamwork/README.md` when durable memory is relevant.
- CodeGraph: use `codegraph_*` tools for structural code questions when available. If `.codegraph/` is missing and the `codegraph` CLI is available, initialize with `codegraph init -i` from the project root.
- Docs MCP: use Context7/docs MCP for current external library, framework, SDK, or API docs when already available. Send only sanitized package names, versions, and topic queries; do not send private source.
- Keep volatile task progress, chat summaries, and experiment numbers out of `AGENTS.md`; use `docs/teamwork/current.md` or dated artifacts only when durable triggers apply.
- Required values, credentials, paths, ports, model names, hyperparameters, configs, and execution modes must come from project files, environment, or the user; do not invent fallbacks.
<!-- TEAMWORK_PROJECT_END -->
"""

gitignore_block = """# TEAMWORK_LOCAL_START
# Teamwork local runtime and project install surfaces
.codex/
.cursor/
.claude/
.teamwork-profile
.codegraph/
docs/teamwork/plans/
docs/teamwork/research/
docs/teamwork/reports/
docs/teamwork/workflows/
docs/teamwork/index.json
docs/teamwork/README.md
docs/teamwork/current.md
# TEAMWORK_LOCAL_END
"""


def replace_or_append(path: Path, start: str, end: str, block: str, prefix: str = "") -> None:
    original = path.read_text(encoding="utf-8", errors="replace") if path.exists() else prefix
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end) + r"\n?", re.S)
    if pattern.search(original):
        updated = pattern.sub(block, original)
    else:
        updated = original.rstrip() + "\n\n" + block
    path.write_text(updated.rstrip() + "\n", encoding="utf-8")


replace_or_append(
    root / "AGENTS.md",
    "<!-- TEAMWORK_PROJECT_START -->",
    "<!-- TEAMWORK_PROJECT_END -->",
    agents_block,
    "# Repository Guidelines\n",
)
replace_or_append(
    root / ".gitignore",
    "# TEAMWORK_LOCAL_START",
    "# TEAMWORK_LOCAL_END",
    gitignore_block,
)
PY
}

validate_teamwork_memory() {
  local index="$PROJECT_ROOT/docs/teamwork/index.json"
  if [[ ! -f "$index" ]]; then
    echo "Teamwork memory: index missing after init"
    return 0
  fi
  if python3 "$TEAMWORK_ROOT/scripts/validate_teamwork_index.py" "$index" >/dev/null 2>&1; then
    echo "Teamwork memory: index valid"
  else
    echo "Teamwork memory: index invalid; preserved existing file, inspect $index"
  fi
}

init_codegraph() {
  if (( RUN_CODEGRAPH == 0 )); then
    echo "CodeGraph: skipped (--no-codegraph)"
    return 0
  fi
  if [[ -d "$PROJECT_ROOT/.codegraph" ]]; then
    echo "CodeGraph: already initialized"
    return 0
  fi
  if ! command -v codegraph >/dev/null 2>&1; then
    echo "CodeGraph: skipped (codegraph CLI not found)"
    return 0
  fi
  if (cd "$PROJECT_ROOT" && codegraph init -i); then
    echo "CodeGraph: initialized"
  else
    echo "CodeGraph: init failed; continuing with project files in place"
  fi
}

detect_context7() {
  local file
  for file in \
    "$PROJECT_ROOT/.cursor/mcp.json" \
    "$PROJECT_ROOT/.mcp.json" \
    "$HOME/.codex/config.toml" \
    "$HOME/.cursor/mcp.json"; do
    if [[ -f "$file" ]] && grep -qi 'context7' "$file"; then
      echo "Context7/docs MCP: detected in $file"
      return 0
    fi
  done
  echo "Context7/docs MCP: not detected; recorded as optional read-only docs substrate"
}

copy_cursor_policy() {
  if (( COPY_CURSOR_POLICY == 0 )); then
    echo "Cursor User Rules: clipboard copy skipped (--no-cursor-policy-copy)"
    return 0
  fi
  if command -v pbcopy >/dev/null 2>&1 \
    || command -v wl-copy >/dev/null 2>&1 \
    || command -v xclip >/dev/null 2>&1 \
    || command -v xsel >/dev/null 2>&1 \
    || command -v clip.exe >/dev/null 2>&1; then
    if [[ -n "$PROFILE_VALUE" ]]; then
      "$TEAMWORK_ROOT/install.sh" --profile "$PROFILE_VALUE" cursor-policy-copy \
        || echo "Cursor User Rules: clipboard copy failed; run ./install.sh cursor-policy-copy manually"
    else
      "$TEAMWORK_ROOT/install.sh" cursor-policy-copy \
        || echo "Cursor User Rules: clipboard copy failed; run ./install.sh cursor-policy-copy manually"
    fi
  else
    echo "Cursor User Rules: clipboard tool not found; run ./install.sh cursor-policy-copy manually"
  fi
}

install_global_surfaces
install_project_surfaces
write_project_files
validate_teamwork_memory
init_codegraph
detect_context7
copy_cursor_policy

echo "Teamwork project init complete: $PROJECT_ROOT"
