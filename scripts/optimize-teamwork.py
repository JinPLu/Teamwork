#!/usr/bin/env python3
"""Small offline SkillOpt-Lite utilities for Teamwork maintenance."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from math import isfinite
from pathlib import Path
from typing import Any


SAMPLE_ROOT = Path(".skillopt") / "samples"
HISTORY_DIR = Path(".skillopt") / "history"
EVAL_RUN_DIR = Path(".skillopt") / "_eval_run"
CORE_RESULT_FIELDS = ("id", "input", "expected", "output")
FRONTMATTER_FIELDS = (
    "id",
    "case_id",
    "status",
    "score",
    "split",
    "source",
    "platform",
    "target",
    "timestamp",
    "run_id",
    "tags",
)


class OptimizeError(Exception):
    pass


def write_json(data: dict[str, Any]) -> None:
    print(json.dumps(data, sort_keys=True))


def ensure_workspace(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    for directory in (
        SAMPLE_ROOT / "failed",
        SAMPLE_ROOT / "passed",
        HISTORY_DIR,
        EVAL_RUN_DIR,
    ):
        (path / directory).mkdir(parents=True, exist_ok=True)


def cmd_init_workspace(args: argparse.Namespace) -> None:
    workspace = args.workspace.resolve()
    skill = args.skill.resolve()
    if not skill.is_file():
        raise OptimizeError(f"skill does not exist: {skill}")
    ensure_workspace(workspace)
    skill_copy = workspace / "skill.md"
    shutil.copyfile(skill, skill_copy)
    shutil.copyfile(skill, workspace / HISTORY_DIR / "initial.skill.md")
    write_json(
        {
            "action": "init-workspace",
            "workspace": str(workspace),
            "skill": str(skill),
            "skill_copy": str(skill_copy),
        }
    )


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise OptimizeError(f"results file does not exist: {path}")
    rows: list[dict[str, Any]] = []
    for index, line in enumerate(path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise OptimizeError(f"{path}:{index}: invalid JSONL: {exc}") from exc
        if not isinstance(row, dict):
            raise OptimizeError(f"{path}:{index}: row must be a JSON object")
        missing = [field for field in CORE_RESULT_FIELDS if field not in row]
        if missing:
            raise OptimizeError(f"{path}:{index}: missing fields: {', '.join(missing)}")
        rows.append(row)
    return rows


def sample_status(row: dict[str, Any]) -> str:
    raw_status = row.get("status")
    if raw_status in {"failed", "passed", "partial"}:
        return raw_status
    if "passed" in row:
        return "passed" if bool(row["passed"]) else "failed"
    score = row.get("score", row.get("hard"))
    if isinstance(score, (int, float)):
        return "passed" if float(score) >= 1.0 else "failed"
    raise OptimizeError(f"row {row['id']!r}: status, passed, score, or hard is required")


def sample_score(row: dict[str, Any]) -> float | int | str:
    score = row.get("score", row.get("hard", row.get("soft")))
    if isinstance(score, (int, float)):
        return score
    if score is None:
        return "not_applicable"
    return str(score)


def numeric_score(row: dict[str, Any], field: str) -> float:
    score = row.get(field)
    if isinstance(score, bool) or not isinstance(score, (int, float)):
        raise OptimizeError(f"row {row['id']!r}: numeric {field!r} is required")
    value = float(score)
    if not isfinite(value):
        raise OptimizeError(f"row {row['id']!r}: {field!r} must be finite")
    return value


def slug(value: Any) -> str:
    text = re.sub(r"[^a-zA-Z0-9._-]+", "-", str(value).strip()).strip("-")
    return text or "sample"


def yaml_value(value: Any) -> str:
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return json.dumps(value, ensure_ascii=True)
    return json.dumps(str(value), ensure_ascii=True)


def markdown_section(title: str, value: Any) -> str:
    if isinstance(value, (dict, list)):
        body = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True)
    else:
        body = str(value)
    return f"## {title}\n{body.strip()}\n"


def sample_markdown(row: dict[str, Any], status: str) -> str:
    frontmatter = {
        "id": row["id"],
        "status": status,
        "score": sample_score(row),
    }
    for field in FRONTMATTER_FIELDS:
        if field == "status":
            continue
        if field in row:
            frontmatter[field] = row[field]

    lines = ["---"]
    for key in FRONTMATTER_FIELDS:
        if key in frontmatter:
            lines.append(f"{key}: {yaml_value(frontmatter[key])}")
    lines.extend(["---", "", f"# Sample {row['id']} - {status.upper()}", ""])
    lines.append(markdown_section("Input", row["input"]))
    lines.append(markdown_section("Expected", row["expected"]))
    lines.append(markdown_section("Assistant output", row["output"]))
    if "trace" in row:
        lines.extend(
            [
                "## Trace",
                "<details>",
                "<summary>Trace</summary>",
                "",
                str(row["trace"]).strip(),
                "",
                "</details>",
                "",
            ]
        )
    notes = row.get("fail_reason", row.get("notes", "not_applicable"))
    lines.append(markdown_section("Notes", f"`fail_reason`: {notes}"))
    return "\n".join(lines).rstrip() + "\n"


def cmd_export_samples(args: argparse.Namespace) -> None:
    if args.env != "teamwork":
        raise OptimizeError("only --env teamwork is supported")
    if args.limit is not None and args.limit < 0:
        raise OptimizeError("--limit must be >= 0")
    workspace = args.workspace.resolve()
    ensure_workspace(workspace)
    rows = load_jsonl(args.results.resolve())
    if args.limit is not None:
        rows = rows[: args.limit]

    counts = {"failed": 0, "passed": 0, "partial": 0}
    written: list[str] = []
    for row in rows:
        status = sample_status(row)
        bucket = "passed" if status == "passed" else "failed"
        path = workspace / SAMPLE_ROOT / bucket / f"{slug(row['id'])}.md"
        path.write_text(sample_markdown(row, status))
        counts[status] += 1
        written.append(str(path))

    write_json(
        {
            "action": "export-samples",
            "workspace": str(workspace),
            "results": str(args.results.resolve()),
            "written": written,
            "counts": counts,
        }
    )


def cmd_score_results(args: argparse.Namespace) -> None:
    results = args.results.resolve()
    rows = load_jsonl(results)
    if not rows:
        raise OptimizeError("results file has no rows")

    counts = {"failed": 0, "passed": 0, "partial": 0}
    scores: list[float] = []
    for row in rows:
        counts[sample_status(row)] += 1
        scores.append(numeric_score(row, args.score_field))

    write_json(
        {
            "action": "score-results",
            "results": str(results),
            "count": len(rows),
            "passed": counts["passed"],
            "failed": counts["failed"],
            "partial": counts["partial"],
            "mean_score": sum(scores) / len(scores),
            "score_field": args.score_field,
        }
    )


def cmd_gate(args: argparse.Namespace) -> None:
    candidate = args.candidate_score
    current = args.current_score
    best = args.best_score
    dead_band = args.dead_band
    if not all(isfinite(score) for score in (candidate, current, best, dead_band)):
        raise OptimizeError("scores and --dead-band must be finite")
    if dead_band < 0:
        raise OptimizeError("--dead-band must be >= 0")

    if candidate > current + dead_band:
        action = "accept_new_best" if candidate > best + dead_band else "accept"
    elif abs(candidate - current) <= dead_band:
        action = "flat"
    else:
        action = "reject"

    write_json(
        {
            "action": action,
            "candidate_score": candidate,
            "current_score": current,
            "best_score": best,
            "dead_band": dead_band,
            "delta_current": candidate - current,
            "delta_best": candidate - best,
        }
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Offline Teamwork SkillOpt-Lite workspace, sample, and gate utilities."
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    init = subcommands.add_parser("init-workspace", help="Create a SkillOpt-Lite workspace.")
    init.add_argument("--workspace", required=True, type=Path)
    init.add_argument("--skill", required=True, type=Path)
    init.set_defaults(func=cmd_init_workspace)

    export = subcommands.add_parser("export-samples", help="Export JSONL results to markdown samples.")
    export.add_argument("--results", required=True, type=Path)
    export.add_argument("--workspace", required=True, type=Path)
    export.add_argument("--env", required=True, choices=("teamwork",))
    export.add_argument("--limit", type=int)
    export.set_defaults(func=cmd_export_samples)

    score = subcommands.add_parser("score-results", help="Summarize JSONL result scores.")
    score.add_argument("--results", required=True, type=Path)
    score.add_argument("--score-field", choices=("score", "hard", "soft"), default="score")
    score.set_defaults(func=cmd_score_results)

    gate = subcommands.add_parser("gate", help="Decide whether candidate score should pass the gate.")
    gate.add_argument("--candidate-score", required=True, type=float)
    gate.add_argument("--current-score", required=True, type=float)
    gate.add_argument("--best-score", required=True, type=float)
    gate.add_argument("--dead-band", type=float, default=0.0)
    gate.set_defaults(func=cmd_gate)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except OptimizeError as exc:
        parser.exit(2, f"error: {exc}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
