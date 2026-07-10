#!/usr/bin/env python3
"""Run provenance-rich, maintainer-only Teamwork trajectories through Codex."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
CASE_CATEGORIES = {
    "lightweight",
    "missing-required-state",
    "research",
    "review-goal-sentinel",
}
SANDBOXES = {"read-only", "workspace-write"}
EFFORTS = {"low", "medium", "high", "max"}
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
UNAVAILABLE_RE = re.compile(
    r"(?:model[^\n]*(?:unavailable|not available|unsupported|not supported|invalid|not found|does not exist)|"
    r"(?:unavailable|unsupported|not supported|invalid)[^\n]*model|do not have access to model|"
    r"model_not_found|unsupported_model)",
    re.IGNORECASE,
)


class LiveEvalError(Exception):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def require_nonempty_string(value: Any, field: str, source: Path) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LiveEvalError(f"{source}: {field} must be a non-empty string")
    return value


def require_string_list(value: Any, field: str, source: Path) -> list[str]:
    if not isinstance(value, list) or not value:
        raise LiveEvalError(f"{source}: {field} must be a non-empty list")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise LiveEvalError(f"{source}: {field} must contain non-empty strings")
    return value


def load_case(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise LiveEvalError(f"cannot read case {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise LiveEvalError(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise LiveEvalError(f"{path}: case must be a JSON object")

    required = {
        "id",
        "category",
        "prompt",
        "sandbox",
        "expected_signals",
        "forbidden_signals",
        "pilot_only",
    }
    missing = sorted(required - set(data))
    unknown = sorted(set(data) - required)
    if missing:
        raise LiveEvalError(f"{path}: missing fields: {', '.join(missing)}")
    if unknown:
        raise LiveEvalError(f"{path}: unknown fields: {', '.join(unknown)}")

    case_id = require_nonempty_string(data["id"], "id", path)
    if not ID_RE.fullmatch(case_id):
        raise LiveEvalError(f"{path}: id must be kebab-case")
    category = require_nonempty_string(data["category"], "category", path)
    if category not in CASE_CATEGORIES:
        raise LiveEvalError(f"{path}: category must be one of {sorted(CASE_CATEGORIES)}")
    require_nonempty_string(data["prompt"], "prompt", path)
    sandbox = require_nonempty_string(data["sandbox"], "sandbox", path)
    if sandbox not in SANDBOXES:
        raise LiveEvalError(f"{path}: sandbox must be one of {sorted(SANDBOXES)}")
    require_string_list(data["expected_signals"], "expected_signals", path)
    require_string_list(data["forbidden_signals"], "forbidden_signals", path)
    if data["pilot_only"] is not True:
        raise LiveEvalError(f"{path}: pilot_only must be true")
    return data


def git_value(workdir: Path, *args: str) -> tuple[str | None, str | None]:
    try:
        completed = subprocess.run(
            ["git", "-C", str(workdir), *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, str(exc)
    value = completed.stdout.strip()
    if completed.returncode != 0 or not value:
        warning = completed.stderr.strip() or f"git {' '.join(args)} returned {completed.returncode}"
        return None, warning
    return value, None


def skill_tree_sha256(workdir: Path) -> tuple[str | None, str | None]:
    skill_root = workdir / "skills"
    if not skill_root.is_dir():
        return None, f"{skill_root} is unavailable"
    files = sorted(path for path in skill_root.rglob("*") if path.is_file())
    if not files:
        return None, f"{skill_root} contains no files"
    digest = hashlib.sha256()
    try:
        for path in files:
            digest.update(path.relative_to(workdir).as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
    except OSError as exc:
        return None, str(exc)
    return digest.hexdigest(), None


def worktree_provenance(workdir: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        status = subprocess.run(
            ["git", "-C", str(workdir), "status", "--porcelain=v1", "--untracked-files=all"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=20,
            check=False,
        )
        files = subprocess.run(
            ["git", "-C", str(workdir), "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, str(exc)
    if status.returncode != 0 or files.returncode != 0:
        error = status.stderr.strip() or files.stderr.decode(errors="replace").strip()
        return None, error or "git worktree provenance command failed"

    digest = hashlib.sha256()
    try:
        for raw_path in sorted(item for item in files.stdout.split(b"\0") if item):
            rel = raw_path.decode("utf-8", errors="surrogateescape")
            path = workdir / rel
            digest.update(raw_path)
            digest.update(b"\0")
            if path.is_file():
                digest.update(path.read_bytes())
            else:
                digest.update(b"<missing>")
            digest.update(b"\0")
    except OSError as exc:
        return None, str(exc)
    status_text = status.stdout.rstrip("\n")
    return {
        "dirty": bool(status_text),
        "status_porcelain": status_text,
        "visible_files_sha256": digest.hexdigest(),
    }, None


def file_sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
    except OSError:
        return None


def config_files(workdir: Path) -> list[dict[str, Any]]:
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()
    candidates = [codex_home / "config.toml", workdir / ".codex" / "config.toml"]
    return [
        {"path": str(path.resolve()), "exists": path.is_file(), "sha256": file_sha256(path)}
        for path in candidates
    ]


def find_usage(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        usage = value.get("usage")
        if isinstance(usage, dict):
            return usage
        for child in value.values():
            found = find_usage(child)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = find_usage(child)
            if found is not None:
                return found
    return None


def parse_events(stdout: str) -> tuple[list[Any], list[str], str | None, dict[str, Any] | None]:
    events: list[Any] = []
    warnings: list[str] = []
    final_output: str | None = None
    usage: dict[str, Any] | None = None
    for line_number, line in enumerate(stdout.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            events.append({"raw_line": line})
            warnings.append(f"stdout line {line_number} was not JSON")
            continue
        events.append(event)
        found_usage = find_usage(event)
        if found_usage is not None:
            usage = found_usage
        if isinstance(event, dict) and event.get("type") == "item.completed":
            item = event.get("item")
            if isinstance(item, dict) and item.get("type") == "agent_message":
                text = item.get("text")
                if isinstance(text, str):
                    final_output = text
    return events, warnings, final_output, usage


def validate_record(record: dict[str, Any]) -> None:
    required = {
        "schema_version", "record_type", "timestamp_utc", "pilot_only", "status",
        "arm", "model", "effort", "case_id", "run_id", "repeat_index",
        "case_source", "category", "prompt", "expected_signals", "forbidden_signals",
        "sandbox", "workdir", "repo_sha", "skill_tree_sha256", "runner_sha256",
        "worktree", "treatment", "argv", "argv_shell",
        "config_source", "raw_events", "raw_stdout", "raw_stderr", "final_output",
        "usage", "elapsed_seconds", "exit_code", "warnings",
    }
    missing = sorted(required - set(record))
    if missing:
        raise LiveEvalError(f"output record missing fields: {', '.join(missing)}")
    if record["schema_version"] != SCHEMA_VERSION:
        raise LiveEvalError("output record has the wrong schema_version")
    if record["record_type"] != "teamwork_live_trajectory":
        raise LiveEvalError("output record has the wrong record_type")
    if record["status"] not in {"dry_run", "completed", "failed", "unavailable"}:
        raise LiveEvalError("output record has an invalid status")
    if record["effort"] not in EFFORTS or record["sandbox"] not in SANDBOXES:
        raise LiveEvalError("output record has invalid effort or sandbox")
    if not isinstance(record["argv"], list) or not record["argv"]:
        raise LiveEvalError("output record argv must be a non-empty list")
    if not isinstance(record["raw_events"], list) or not isinstance(record["warnings"], list):
        raise LiveEvalError("output record raw_events and warnings must be lists")
    if not isinstance(record["worktree"], dict):
        raise LiveEvalError("output record worktree provenance must be an object")
    if not isinstance(record["worktree"].get("dirty"), bool):
        raise LiveEvalError("output record worktree.dirty must be boolean")
    require_nonempty_string(
        record["worktree"].get("visible_files_sha256"),
        "worktree.visible_files_sha256",
        Path("output"),
    )
    if not isinstance(record["treatment"], dict) or record["treatment"].get("arm") != record["arm"]:
        raise LiveEvalError("output record treatment must match the run arm")
    if not isinstance(record["runner_sha256"], str) or not record["runner_sha256"]:
        raise LiveEvalError("output record runner_sha256 must be non-empty")


def make_argv(args: argparse.Namespace, case: dict[str, Any]) -> list[str]:
    return [
        args.codex_bin,
        "exec",
        "--ephemeral",
        "--json",
        "--color",
        "never",
        "--model",
        args.model,
        "-c",
        f'model_reasoning_effort="{args.effort}"',
        "--sandbox",
        case["sandbox"],
        "--cd",
        str(args.workdir),
        "-",
    ]


def run_one(
    args: argparse.Namespace,
    case: dict[str, Any],
    case_path: Path,
    repeat_index: int,
    repo_sha: str | None,
    skill_sha: str | None,
    provenance_warnings: list[str],
    codex_version: str | None,
    runner_sha: str | None,
    worktree: dict[str, Any] | None,
) -> dict[str, Any]:
    argv = make_argv(args, case)
    run_id = f"{args.arm}-{case['id']}-r{repeat_index}"
    started = time.monotonic()
    raw_stdout = ""
    raw_stderr = ""
    exit_code: int | None = None
    status = "dry_run"
    warnings = list(provenance_warnings)

    if not args.dry_run:
        try:
            completed = subprocess.run(
                argv,
                input=case["prompt"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=args.timeout_seconds,
                check=False,
                env=os.environ.copy(),
            )
            raw_stdout = completed.stdout
            raw_stderr = completed.stderr
            exit_code = completed.returncode
            combined = f"{raw_stdout}\n{raw_stderr}"
            if completed.returncode == 0:
                status = "completed"
            elif UNAVAILABLE_RE.search(combined):
                status = "unavailable"
            else:
                status = "failed"
        except subprocess.TimeoutExpired as exc:
            raw_stdout = exc.stdout or ""
            raw_stderr = exc.stderr or ""
            if isinstance(raw_stdout, bytes):
                raw_stdout = raw_stdout.decode(errors="replace")
            if isinstance(raw_stderr, bytes):
                raw_stderr = raw_stderr.decode(errors="replace")
            status = "failed"
            warnings.append(f"codex exec timed out after {args.timeout_seconds} seconds")
        except OSError as exc:
            status = "failed"
            raw_stderr = str(exc)
            warnings.append("codex executable could not be started")

    events, parse_warnings, final_output, usage = parse_events(raw_stdout)
    warnings.extend(parse_warnings)
    if raw_stderr.strip():
        warnings.append("codex exec wrote to stderr; inspect raw_stderr")
    if status == "completed" and final_output is None:
        status = "failed"
        warnings.append("zero-exit run did not contain an agent_message event")

    record = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "teamwork_live_trajectory",
        "timestamp_utc": utc_now(),
        "pilot_only": True,
        "status": status,
        "arm": args.arm,
        "model": args.model,
        "effort": args.effort,
        "case_id": case["id"],
        "run_id": run_id,
        "repeat_index": repeat_index,
        "case_source": str(case_path.resolve()),
        "category": case["category"],
        "prompt": case["prompt"],
        "expected_signals": case["expected_signals"],
        "forbidden_signals": case["forbidden_signals"],
        "sandbox": case["sandbox"],
        "workdir": str(args.workdir),
        "repo_sha": repo_sha,
        "skill_tree_sha256": skill_sha,
        "runner_sha256": runner_sha,
        "worktree": worktree,
        "treatment": {"arm": args.arm, "skill_tree_sha256": skill_sha},
        "argv": argv,
        "argv_shell": shlex.join(argv),
        "config_source": {
            "runner": str(Path(__file__).resolve()),
            "runner_cli": list(sys.argv),
            "case_file": str(case_path.resolve()),
            "codex_version": codex_version,
            "base_config_files": config_files(args.workdir),
            "model_source": "--model",
            "effort_source": "--effort -> codex -c model_reasoning_effort",
            "sandbox_source": "case.sandbox",
            "fallback_policy": "none",
        },
        "raw_events": events,
        "raw_stdout": raw_stdout,
        "raw_stderr": raw_stderr,
        "final_output": final_output,
        "usage": usage,
        "elapsed_seconds": round(time.monotonic() - started, 6),
        "exit_code": exit_code,
        "warnings": warnings,
    }
    validate_record(record)
    return record


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run maintainer-only Codex live trajectories and write validated JSONL."
    )
    parser.add_argument("--arm", required=True, help="Experiment arm label, e.g. baseline or slim")
    parser.add_argument("--model", required=True, help="Exact Codex model; no fallback is attempted")
    parser.add_argument("--effort", required=True, choices=sorted(EFFORTS))
    parser.add_argument("--workdir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--cases", required=True, type=Path, nargs="+")
    parser.add_argument("--repeats", required=True, type=int)
    parser.add_argument("--timeout-seconds", required=True, type=int)
    parser.add_argument("--codex-bin", default="codex", help="Codex executable (default: codex)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate cases and write schema-valid planned records without invoking Codex",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.workdir = args.workdir.expanduser().resolve()
    args.output = args.output.expanduser().resolve()
    args.cases = [path.expanduser().resolve() for path in args.cases]
    if not args.arm.strip():
        raise LiveEvalError("--arm must be non-empty")
    if not args.model.strip():
        raise LiveEvalError("--model must be non-empty")
    if not args.workdir.is_dir():
        raise LiveEvalError(f"--workdir is not a directory: {args.workdir}")
    if args.repeats < 1:
        raise LiveEvalError("--repeats must be at least 1")
    if args.timeout_seconds < 1:
        raise LiveEvalError("--timeout-seconds must be at least 1")
    if args.output.exists():
        raise LiveEvalError(f"refusing to overwrite existing output: {args.output}")

    codex_version: str | None = None
    if not args.dry_run:
        resolved_codex = shutil.which(args.codex_bin)
        if resolved_codex is None:
            raise LiveEvalError(f"--codex-bin is not executable or not on PATH: {args.codex_bin}")
        args.codex_bin = str(Path(resolved_codex).resolve())
        version = subprocess.run(
            [args.codex_bin, "--version"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=20,
            check=False,
        )
        if version.returncode != 0:
            raise LiveEvalError(
                f"cannot read Codex version: {version.stderr.strip() or version.returncode}"
            )
        codex_version = version.stdout.strip()

    cases = [(path, load_case(path)) for path in args.cases]
    case_ids = [case["id"] for _, case in cases]
    if len(case_ids) != len(set(case_ids)):
        raise LiveEvalError("--cases contain duplicate case ids")

    provenance_warnings: list[str] = []
    repo_sha, repo_warning = git_value(args.workdir, "rev-parse", "HEAD")
    if repo_warning:
        provenance_warnings.append(f"repo SHA unavailable: {repo_warning}")
    skill_sha, skill_warning = skill_tree_sha256(args.workdir)
    if skill_warning:
        provenance_warnings.append(f"skill SHA unavailable: {skill_warning}")
    runner_sha = file_sha256(Path(__file__).resolve())
    if runner_sha is None:
        provenance_warnings.append("runner SHA unavailable")
    worktree, worktree_warning = worktree_provenance(args.workdir)
    if worktree_warning:
        provenance_warnings.append(f"worktree provenance unavailable: {worktree_warning}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    statuses: list[str] = []
    try:
        with args.output.open("x", encoding="utf-8") as output:
            for case_path, case in cases:
                for repeat_index in range(1, args.repeats + 1):
                    record = run_one(
                        args,
                        case,
                        case_path,
                        repeat_index,
                        repo_sha,
                        skill_sha,
                        provenance_warnings,
                        codex_version,
                        runner_sha,
                        worktree,
                    )
                    statuses.append(record["status"])
                    output.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
                    output.flush()
    except OSError as exc:
        raise LiveEvalError(f"cannot write output {args.output}: {exc}") from exc

    mode = "dry-run" if args.dry_run else "live"
    print(f"wrote {len(cases) * args.repeats} validated {mode} records to {args.output}")
    return 0 if args.dry_run or all(status == "completed" for status in statuses) else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except LiveEvalError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
