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

from grill_contract import active_output_violation, close_basis


SCHEMA_VERSION = 2
CASE_CATEGORIES = {
    "grill",
    "lightweight",
    "missing-required-state",
    "research",
    "review-goal-sentinel",
}
SANDBOXES = {"read-only", "workspace-write"}
EFFORTS = {"none", "low", "medium", "high", "xhigh", "max"}
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
        "sandbox",
        "expected_signals",
        "forbidden_signals",
        "pilot_only",
    }
    allowed = required | {"prompt", "prompts"}
    missing = sorted(required - set(data))
    unknown = sorted(set(data) - allowed)
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
    if ("prompt" in data) == ("prompts" in data):
        raise LiveEvalError(f"{path}: provide exactly one of prompt or prompts")
    prompts = (
        [require_nonempty_string(data["prompt"], "prompt", path)]
        if "prompt" in data
        else require_string_list(data["prompts"], "prompts", path)
    )
    sandbox = require_nonempty_string(data["sandbox"], "sandbox", path)
    if sandbox not in SANDBOXES:
        raise LiveEvalError(f"{path}: sandbox must be one of {sorted(SANDBOXES)}")
    require_string_list(data["expected_signals"], "expected_signals", path)
    require_string_list(data["forbidden_signals"], "forbidden_signals", path)
    if data["pilot_only"] is not True:
        raise LiveEvalError(f"{path}: pilot_only must be true")
    data["prompt"] = prompts[0]
    data["prompts"] = prompts
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


def find_reported_cost(value: Any) -> int | float | None:
    if isinstance(value, dict):
        for key in ("reported_cost", "cost_usd", "total_cost", "cost"):
            candidate = value.get(key)
            if isinstance(candidate, (int, float)) and not isinstance(candidate, bool):
                return candidate
        for child in value.values():
            found = find_reported_cost(child)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = find_reported_cost(child)
            if found is not None:
                return found
    return None


def parse_events(
    stdout: str,
) -> tuple[list[Any], list[str], str | None, dict[str, Any] | None, str | None, str | None]:
    events: list[Any] = []
    warnings: list[str] = []
    final_output: str | None = None
    usage: dict[str, Any] | None = None
    session_id: str | None = None
    resolved_model: str | None = None
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
        if isinstance(event, dict):
            if event.get("type") in {"thread.started", "thread.resumed"}:
                candidate = event.get("thread_id") or event.get("session_id")
                if isinstance(candidate, str) and candidate.strip():
                    session_id = candidate
                model = event.get("model")
                if isinstance(model, str) and model.strip():
                    resolved_model = model
            if event.get("type") == "item.completed":
                item = event.get("item")
                if isinstance(item, dict) and item.get("type") == "agent_message":
                    text = item.get("text")
                    if isinstance(text, str):
                        final_output = text
    return events, warnings, final_output, usage, session_id, resolved_model


def grill_state(output: str | None) -> str:
    lowered = (output or "").lower()
    active = "grill status: active" in lowered
    closed = "grill status: closed" in lowered
    if active and closed:
        return "invalid"
    if active:
        return "active"
    if closed:
        return "closed"
    return "none"


def assess_grill_behavior(turns: list[dict[str, Any]], *, dry_run: bool) -> tuple[str, list[str]]:
    if dry_run:
        return "not_run", []
    violations: list[str] = []
    if not turns:
        return "failed", ["grill trajectory is empty"]

    closed_seen = False
    active_count = 0
    for index, turn in enumerate(turns, start=1):
        output = turn.get("final_output") or ""
        lowered = output.lower()
        state = turn.get("grill_state")
        is_last = index == len(turns)
        expected_state = "closed" if is_last else "active"
        if state != expected_state:
            violations.append(f"turn {index} must be {expected_state}, got {state}")
        output_violation = active_output_violation(output)
        if output_violation:
            violations.append(f"turn {index} {output_violation}")
        if state == "active":
            active_count += 1
            if closed_seen:
                violations.append(f"turn {index} reactivated after close")
            if lowered.count("grill status: active") != 1:
                violations.append(f"turn {index} must contain exactly one active marker")
            if lowered.count("question:") != 1 or output.count("?") != 1:
                violations.append(f"turn {index} must ask exactly one labeled question")
            for field in ("recommended:", "alternatives:"):
                if lowered.count(field) != 1:
                    violations.append(f"turn {index} must contain exactly one {field[:-1]} field")
            if re.search(r"\b(?:i|we)\s+(?:edited|changed|implemented|created|wrote|dispatched|started)\b", lowered):
                violations.append(f"turn {index} claims enactment while grill is active")
        elif state == "closed":
            closed_seen = True
            if not close_basis(turn.get("prompt") or "", output):
                violations.append(f"turn {index} lacks a valid user or exhausted close basis")

        if not is_last:
            serialized = json.dumps(turn.get("raw_events", []), ensure_ascii=False).lower()
            if any(token in serialized for token in ('"type": "file_change"', "spawn_agent", "create_goal", "apply_patch")):
                violations.append(f"turn {index} contains a forbidden mutation, goal, or subagent event")
    if active_count > 3:
        violations.append("grill trajectory exceeds the three-question hard cap")
    return ("passed" if not violations else "failed"), violations


def validate_record(record: dict[str, Any]) -> None:
    required = {
        "schema_version", "record_type", "timestamp_utc", "pilot_only", "status",
        "arm", "model", "effort", "case_id", "run_id", "repeat_index",
        "case_source", "category", "prompt", "prompts", "expected_signals",
        "forbidden_signals", "sandbox", "workdir", "repo_sha", "skill_tree_sha256",
        "runner_sha256", "worktree", "treatment", "argv", "argv_shell",
        "config_source", "session_id", "turns", "grill_states", "raw_events",
        "raw_stdout", "raw_stderr", "final_output", "usage", "reported_costs",
        "elapsed_seconds", "exit_code", "warnings", "execution_status",
        "behavioral_status", "behavior_violations", "resolved_model",
        "model_provenance_status",
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
    if not isinstance(record["prompts"], list) or not record["prompts"]:
        raise LiveEvalError("output record prompts must be a non-empty list")
    if not isinstance(record["turns"], list) or not record["turns"]:
        raise LiveEvalError("output record turns must be a non-empty list")
    if len(record["turns"]) > len(record["prompts"]):
        raise LiveEvalError("output record has more turns than prompts")
    if record["status"] in {"dry_run", "completed"} and len(record["turns"]) != len(record["prompts"]):
        raise LiveEvalError("successful output record must include every prompt turn")
    if len(record["prompts"]) > 1 and record["status"] == "completed":
        require_nonempty_string(record["session_id"], "session_id", Path("output"))
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
    if record["behavioral_status"] not in {"not_applicable", "not_run", "passed", "failed"}:
        raise LiveEvalError("output record has an invalid behavioral_status")
    if not isinstance(record["behavior_violations"], list):
        raise LiveEvalError("output record behavior_violations must be a list")
    if record["model_provenance_status"] not in {"not_run", "verified", "unverified", "mismatch"}:
        raise LiveEvalError("output record has an invalid model_provenance_status")


def make_start_argv(args: argparse.Namespace, case: dict[str, Any]) -> list[str]:
    argv = [args.codex_bin, "exec"]
    if len(case["prompts"]) == 1:
        argv.append("--ephemeral")
    argv.extend([
        "--json", "--color", "never", "--model", args.model,
        "-c", f'model_reasoning_effort="{args.effort}"',
        "--sandbox", case["sandbox"], "--cd", str(args.workdir), "-",
    ])
    return argv


def make_resume_argv(args: argparse.Namespace, session_id: str) -> list[str]:
    return [
        args.codex_bin, "exec", "resume", "--json", "--model", args.model,
        "-c", f'model_reasoning_effort="{args.effort}"', session_id, "-",
    ]


def run_turn(
    args: argparse.Namespace,
    argv: list[str],
    prompt: str,
    turn_index: int,
) -> dict[str, Any]:
    started = time.monotonic()
    raw_stdout = ""
    raw_stderr = ""
    exit_code: int | None = None
    status = "dry_run"
    warnings: list[str] = []
    if not args.dry_run:
        try:
            completed = subprocess.run(
                argv,
                input=prompt,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=args.timeout_seconds,
                check=False,
                cwd=args.workdir,
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

    events, parse_warnings, final_output, usage, event_session_id, resolved_model = parse_events(raw_stdout)
    warnings.extend(parse_warnings)
    if raw_stderr.strip():
        warnings.append("codex exec wrote to stderr; inspect raw_stderr")
    if status == "completed" and final_output is None:
        status = "failed"
        warnings.append("zero-exit run did not contain an agent_message event")
    return {
        "turn_index": turn_index,
        "prompt": prompt,
        "status": status,
        "argv": argv,
        "argv_shell": shlex.join(argv),
        "session_id": event_session_id,
        "resolved_model": resolved_model,
        "raw_events": events,
        "raw_stdout": raw_stdout,
        "raw_stderr": raw_stderr,
        "final_output": final_output,
        "grill_state": grill_state(final_output),
        "usage": usage,
        "reported_cost": find_reported_cost(events),
        "elapsed_seconds": round(time.monotonic() - started, 6),
        "exit_code": exit_code,
        "warnings": warnings,
    }


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
    run_id = f"{args.arm}-{case['id']}-r{repeat_index}"
    started = time.monotonic()
    session_id: str | None = None
    turns: list[dict[str, Any]] = []
    warnings = list(provenance_warnings)

    for turn_index, prompt in enumerate(case["prompts"], start=1):
        if turn_index == 1:
            argv = make_start_argv(args, case)
        else:
            resume_id = session_id or "<session-id>"
            argv = make_resume_argv(args, resume_id)
        turn = run_turn(args, argv, prompt, turn_index)
        turns.append(turn)
        warnings.extend(f"turn {turn_index}: {item}" for item in turn["warnings"])
        if turn_index == 1 and len(case["prompts"]) > 1 and not args.dry_run:
            session_id = turn["session_id"]
            if not session_id:
                turn["status"] = "failed"
                warnings.append("turn 1 did not return a session id; resume was not attempted")
                break
        elif turn_index > 1 and turn["session_id"] and turn["session_id"] != session_id:
            turn["status"] = "failed"
            warnings.append(f"turn {turn_index} returned a different session id")
            break
        if turn["status"] not in {"completed", "dry_run"}:
            break

    statuses = [turn["status"] for turn in turns]
    if args.dry_run:
        status = "dry_run"
    elif "unavailable" in statuses:
        status = "unavailable"
    elif len(turns) == len(case["prompts"]) and all(item == "completed" for item in statuses):
        status = "completed"
    else:
        status = "failed"

    execution_status = status
    if case["category"] == "grill":
        behavioral_status, behavior_violations = assess_grill_behavior(turns, dry_run=args.dry_run)
    else:
        behavioral_status, behavior_violations = ("not_run", []) if args.dry_run else ("not_applicable", [])
    resolved_models = {turn["resolved_model"] for turn in turns if turn["resolved_model"]}
    if args.dry_run:
        resolved_model = None
        model_provenance_status = "not_run"
    elif not resolved_models:
        resolved_model = None
        model_provenance_status = "unverified"
    elif len(resolved_models) == 1:
        resolved_model = next(iter(resolved_models))
        model_provenance_status = "verified" if resolved_model == args.model else "mismatch"
    else:
        resolved_model = None
        model_provenance_status = "mismatch"

    if not args.dry_run and behavioral_status == "failed":
        status = "failed"
    if not args.dry_run and model_provenance_status in {"unverified", "mismatch"}:
        status = "unavailable" if execution_status == "completed" else status
        warnings.append("runtime did not verify the exact requested model slug")

    first_turn = turns[0]
    last_turn = turns[-1]
    record = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "teamwork_live_trajectory",
        "timestamp_utc": utc_now(),
        "pilot_only": True,
        "status": status,
        "execution_status": execution_status,
        "behavioral_status": behavioral_status,
        "behavior_violations": behavior_violations,
        "arm": args.arm,
        "model": args.model,
        "resolved_model": resolved_model,
        "model_provenance_status": model_provenance_status,
        "effort": args.effort,
        "case_id": case["id"],
        "run_id": run_id,
        "repeat_index": repeat_index,
        "case_source": str(case_path.resolve()),
        "category": case["category"],
        "prompt": case["prompt"],
        "prompts": case["prompts"],
        "expected_signals": case["expected_signals"],
        "forbidden_signals": case["forbidden_signals"],
        "sandbox": case["sandbox"],
        "workdir": str(args.workdir),
        "repo_sha": repo_sha,
        "skill_tree_sha256": skill_sha,
        "runner_sha256": runner_sha,
        "worktree": worktree,
        "treatment": {"arm": args.arm, "skill_tree_sha256": skill_sha},
        "argv": first_turn["argv"],
        "argv_shell": first_turn["argv_shell"],
        "config_source": {
            "runner": str(Path(__file__).resolve()),
            "runner_cli": list(sys.argv),
            "case_file": str(case_path.resolve()),
            "codex_version": codex_version,
            "base_config_files": config_files(args.workdir),
            "model_source": "--model",
            "effort_source": "--effort -> codex -c model_reasoning_effort",
            "sandbox_source": "case.sandbox",
            "continuation": "codex exec resume <session-id> --json",
            "fallback_policy": "none",
        },
        "session_id": session_id,
        "turns": turns,
        "grill_states": [turn["grill_state"] for turn in turns],
        "raw_events": [event for turn in turns for event in turn["raw_events"]],
        "raw_stdout": "\n".join(turn["raw_stdout"] for turn in turns),
        "raw_stderr": "\n".join(turn["raw_stderr"] for turn in turns),
        "final_output": last_turn["final_output"],
        "usage": [turn["usage"] for turn in turns],
        "reported_costs": [turn["reported_cost"] for turn in turns],
        "elapsed_seconds": round(time.monotonic() - started, 6),
        "exit_code": last_turn["exit_code"],
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
