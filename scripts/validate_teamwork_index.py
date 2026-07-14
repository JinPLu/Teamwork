#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path, PurePosixPath


DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
KINDS = {"result", "progress", "design", "decision", "discussion", "plan", "report", "research", "runbook"}
STATUSES = {"active", "historical", "superseded", "blocked", "candidate", "accepted"}
CURRENTNESS = {"current", "stale", "historical", "candidate"}
AUTHORITIES = {"canonical", "active-summary", "supporting", "candidate", "historical", "superseded"}
ACTIVE_STATUSES = {"active", "accepted"}
ACTIVE_AUTHORITIES = {"canonical", "active-summary", "supporting"}
ACTIVE_POINTER_KEYS = ("current", "design", "plan", "progress", "goal", "report", "discussion")


class ValidationError(Exception):
    pass


def fail(msg: str) -> None:
    raise ValidationError(msg)


def require(cond: bool, msg: str) -> None:
    if not cond:
        fail(msg)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"missing file: {path}")


def line_count(text: str) -> int:
    return len(text.splitlines())


def word_count(text: str) -> int:
    return len(text.split())


def validate_entry(entry: dict, idx: int) -> None:
    required = [
        "topic",
        "kind",
        "title",
        "status",
        "currentness",
        "authority",
        "path",
        "updated",
        "summary",
    ]
    for key in required:
        require(key in entry, f"entries[{idx}] missing required key: {key}")
    require(isinstance(entry["topic"], str) and entry["topic"], f"entries[{idx}].topic must be non-empty string")
    require(isinstance(entry["kind"], str) and entry["kind"], f"entries[{idx}].kind must be non-empty string")
    require(isinstance(entry["status"], str) and entry["status"], f"entries[{idx}].status must be non-empty string")
    require(entry["kind"] in KINDS, f"entries[{idx}].kind has unknown value: {entry['kind']}")
    require(entry["status"] in STATUSES, f"entries[{idx}].status has unknown value: {entry['status']}")
    require(entry["currentness"] in CURRENTNESS, f"entries[{idx}].currentness has unknown value: {entry['currentness']}")
    require(entry["authority"] in AUTHORITIES, f"entries[{idx}].authority has unknown value: {entry['authority']}")
    for key in ["title", "path", "summary"]:
        require(isinstance(entry[key], str) and entry[key], f"entries[{idx}].{key} must be non-empty string")
    require(DATE_RE.match(str(entry["updated"])) is not None, f"entries[{idx}].updated must be YYYY-MM-DD")


def real_project_root(index_path: Path) -> Path | None:
    if (
        index_path.name == "index.json"
        and index_path.parent.name == "teamwork"
        and index_path.parent.parent.name == "docs"
    ):
        return index_path.parent.parent.parent
    return None


def validate_active_pointers(active: dict, entries: list[dict], index_path: Path) -> None:
    entries_by_path: dict[str, list[dict]] = {}
    for entry in entries:
        entries_by_path.setdefault(entry["path"], []).append(entry)

    pointers: list[tuple[str, str]] = []
    for key in ACTIVE_POINTER_KEYS:
        value = active.get(key)
        if value is not None:
            pointers.append((f"active.{key}", value))

    results = active.get("results", [])
    seen_results: set[str] = set()
    for idx, value in enumerate(results):
        require(isinstance(value, str) and value, f"active.results[{idx}] must be non-empty string")
        require(value not in seen_results, f"active.results contains duplicate path: {value}")
        seen_results.add(value)
        pointers.append((f"active.results[{idx}]", value))

    for label, path in pointers:
        matches = entries_by_path.get(path, [])
        require(matches, f"{label} has no matching entries.path: {path}")
        eligible = [
            entry
            for entry in matches
            if entry["status"] in ACTIVE_STATUSES
            and entry["currentness"] == "current"
            and entry["authority"] in ACTIVE_AUTHORITIES
        ]
        require(
            eligible,
            f"{label} must resolve to a current accepted/active entry with non-candidate authority: {path}",
        )

        if label == "active.discussion":
            discussion_path = PurePosixPath(path)
            require(
                not discussion_path.is_absolute()
                and discussion_path.as_posix() == path
                and len(discussion_path.parts) > 3
                and discussion_path.parts[:3] == ("docs", "teamwork", "discussion")
                and ".." not in discussion_path.parts,
                "active.discussion path must be under docs/teamwork/discussion/",
            )
            require(
                any(entry["kind"] == "discussion" for entry in eligible),
                "active.discussion must resolve to an entry with kind discussion",
            )
            require(
                any(entry["authority"] == "supporting" for entry in eligible if entry["kind"] == "discussion"),
                "active.discussion must resolve to a discussion entry with supporting authority",
            )
            project_root = real_project_root(index_path)
            if project_root is not None:
                require(
                    (project_root / discussion_path).is_file(),
                    f"active.discussion artifact does not exist: {path}",
                )


def validate_index(index: dict, index_path: Path) -> None:
    required_top = [
        "schema_version",
        "last_updated",
        "project",
        "source_of_truth_order",
        "ignore_globs",
        "budgets",
        "active",
        "entries",
        "profiles",
    ]
    for key in required_top:
        require(key in index, f"missing top-level key: {key}")

    require(index["schema_version"] == 1, "schema_version must be 1")
    require(DATE_RE.match(str(index["last_updated"])) is not None, "last_updated must be YYYY-MM-DD")

    project = index["project"]
    require(isinstance(project, dict), "project must be object")
    for key in ["name", "root", "description"]:
        require(key in project, f"project missing key: {key}")
        require(isinstance(project[key], str) and project[key], f"project.{key} must be non-empty string")

    sto = index["source_of_truth_order"]
    require(isinstance(sto, list) and len(sto) > 0, "source_of_truth_order must be non-empty list")

    ignores = index["ignore_globs"]
    require(isinstance(ignores, list), "ignore_globs must be list")
    require(".planning/**" in ignores, "ignore_globs must include .planning/**")

    budgets = index["budgets"]
    require(isinstance(budgets, dict), "budgets must be object")
    header_only_keys = {"header_first"}
    legacy_keys = {"default_max_files", "default_max_artifact_bodies", "header_first"}
    require(
        set(budgets) in (header_only_keys, legacy_keys),
        "budgets must be exactly header-first or the complete legacy numeric form",
    )
    require(budgets.get("header_first") is True, "budgets.header_first must be true")
    if set(budgets) == legacy_keys:
        max_files = budgets["default_max_files"]
        max_bodies = budgets["default_max_artifact_bodies"]
        require(
            isinstance(max_files, int) and not isinstance(max_files, bool),
            "budgets.default_max_files must be integer",
        )
        require(1 <= max_files <= 10, "budgets.default_max_files must be between 1 and 10")
        require(
            isinstance(max_bodies, int) and not isinstance(max_bodies, bool),
            "budgets.default_max_artifact_bodies must be integer",
        )
        require(0 <= max_bodies <= 5, "budgets.default_max_artifact_bodies must be between 0 and 5")

    active = index["active"]
    require(isinstance(active, dict), "active must be object")
    for key in ACTIVE_POINTER_KEYS:
        if key in active:
            value = active[key]
            require(value is None or (isinstance(value, str) and value), f"active.{key} must be null or non-empty string when present")
    if "results" in active:
        require(isinstance(active["results"], list), "active.results must be list when present")

    entries = index["entries"]
    require(isinstance(entries, list) and len(entries) > 0, "entries must be non-empty list")
    active_unique = set()
    for i, entry in enumerate(entries):
        require(isinstance(entry, dict), f"entries[{i}] must be object")
        validate_entry(entry, i)
        if entry.get("status") == "active":
            key = (entry.get("topic"), entry.get("kind"))
            require(key not in active_unique, f"duplicate active entry for topic+kind: {key[0]}::{key[1]}")
            active_unique.add(key)

    validate_active_pointers(active, entries, index_path)

    profiles = index["profiles"]
    require(isinstance(profiles, dict) and len(profiles) > 0, "profiles must be non-empty object")

    pending = index.get("pending", [])
    require(isinstance(pending, list), "pending must be list when present")
    require(len(pending) <= 5, "pending cap exceeded: max 5")


def validate_templates(root: Path) -> None:
    readme_path = root / "skills/using-teamwork/references/teamwork-index-readme-template.md"
    current_path = root / "skills/using-teamwork/references/teamwork-current-template.md"
    index_doc_path = root / "skills/using-teamwork/references/artifact-protocol.md"

    readme = read_text(readme_path)
    current = read_text(current_path)
    index_doc = read_text(index_doc_path)

    require(line_count(readme) <= 120, "teamwork-index-readme-template.md exceeds 120 lines")
    require(word_count(readme) <= 1200, "teamwork-index-readme-template.md exceeds 1200 words")

    require(line_count(current) <= 120, "teamwork-current-template.md exceeds 120 lines")
    require(word_count(current) <= 700, "teamwork-current-template.md exceeds 700 words")

    required_readme_phrases = [
        "broad scan",
        "stage",
        "compatibility retrieval hints",
        "not execution limits",
        "index.json",
        "Project instructions may point here",
    ]
    for phrase in required_readme_phrases:
        require(phrase.lower() in readme.lower(), f"README template missing required language: {phrase}")

    required_index_doc_phrases = [
        "schema_version",
        "active pointers",
        "candidate",
        "memory delta",
        "external calibration alone is not a write trigger",
    ]
    for phrase in required_index_doc_phrases:
        require(phrase.lower() in index_doc.lower(), f"index contract missing required language: {phrase}")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python3 scripts/validate_teamwork_index.py <index-template.json>", file=sys.stderr)
        return 2

    template_path = Path(sys.argv[1]).resolve()
    root = Path(__file__).resolve().parents[1]

    try:
        raw = read_text(template_path)
        data = json.loads(raw)
        validate_index(data, template_path)
        validate_templates(root)
    except (ValidationError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print("PASS: Teamwork index contract/template validation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
