#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path


DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
KINDS = {"result", "progress", "design", "decision", "plan", "report", "research", "runbook"}
STATUSES = {"active", "historical", "superseded", "blocked", "candidate", "accepted"}
CURRENTNESS = {"current", "stale", "historical", "candidate"}
AUTHORITIES = {"canonical", "active-summary", "supporting", "candidate", "historical", "superseded"}


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
    require(DATE_RE.match(str(entry["updated"])) is not None, f"entries[{idx}].updated must be YYYY-MM-DD")


def validate_index(index: dict) -> None:
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
    require(isinstance(budgets.get("default_max_files"), int), "budgets.default_max_files must be integer")
    require(1 <= budgets["default_max_files"] <= 10, "budgets.default_max_files must be between 1 and 10")
    require(isinstance(budgets.get("default_max_artifact_bodies"), int), "budgets.default_max_artifact_bodies must be integer")
    require(0 <= budgets["default_max_artifact_bodies"] <= 5, "budgets.default_max_artifact_bodies must be between 0 and 5")
    require(isinstance(budgets.get("header_first"), bool), "budgets.header_first must be boolean")
    require(budgets["header_first"] is True, "budgets.header_first must be true for templates")

    active = index["active"]
    require(isinstance(active, dict), "active must be object")
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

    profiles = index["profiles"]
    require(isinstance(profiles, dict) and len(profiles) > 0, "profiles must be non-empty object")

    pending = index.get("pending", [])
    require(isinstance(pending, list), "pending must be list when present")
    require(len(pending) <= 5, "pending cap exceeded: max 5")


def validate_templates(root: Path) -> None:
    readme_path = root / "skills/using-teamwork/references/teamwork-index-readme-template.md"
    current_path = root / "skills/using-teamwork/references/teamwork-current-template.md"
    index_doc_path = root / "skills/using-teamwork/references/teamwork-index.md"

    readme = read_text(readme_path)
    current = read_text(current_path)
    index_doc = read_text(index_doc_path)

    require(line_count(readme) <= 120, "teamwork-index-readme-template.md exceeds 120 lines")
    require(word_count(readme) <= 1200, "teamwork-index-readme-template.md exceeds 1200 words")

    require(line_count(current) <= 120, "teamwork-current-template.md exceeds 120 lines")
    require(word_count(current) <= 700, "teamwork-current-template.md exceeds 700 words")

    required_readme_phrases = ["broad scan", "stage", "Memory Delta", "index.json"]
    for phrase in required_readme_phrases:
        require(phrase.lower() in readme.lower(), f"README template missing required language: {phrase}")

    required_index_doc_phrases = ["pending", "active", "topic + kind", "stage", "broad-scan"]
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
        validate_index(data)
        validate_templates(root)
    except (ValidationError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print("PASS: Teamwork index contract/template validation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
