"""Isolated installed-Codex canary orchestration and redacted finalization."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Sequence

from .semantic_review import SemanticReviewError, trajectory_sha256, validate_semantic_review


SCHEMA_VERSION = 1
RAW_NAME = "raw-trajectories.jsonl"
MANIFEST_NAME = "install-manifest.json"
SUMMARY_NAME = "summary.json"
REVIEWS_DIR = "reviews"
DEFAULT_RUBRIC = "evals/teamwork/rubrics/teamwork-live-semantic-v1.json"
USAGE_FIELDS = {
    "cached_input_tokens",
    "input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
    "total_tokens",
}


class LiveCanaryError(ValueError):
    """Raised when the installed live-canary contract cannot be satisfied."""


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    try:
        return _sha256_bytes(path.read_bytes())
    except OSError as exc:
        raise LiveCanaryError(f"cannot hash {path}: {exc}") from exc


def _read_json(path: Path, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise LiveCanaryError(f"cannot read {label} {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise LiveCanaryError(f"invalid JSON in {label} {path}: {exc}") from exc


def _write_json_exclusive(path: Path, value: Any, mode: int = 0o600) -> None:
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, sort_keys=True, indent=2)
            handle.write("\n")
    except OSError as exc:
        raise LiveCanaryError(f"cannot create {path}: {exc}") from exc


def _load_cases(paths: Sequence[Path]) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    ids: set[str] = set()
    for path in paths:
        value = _read_json(path, "case")
        if not isinstance(value, dict):
            raise LiveCanaryError(f"case {path} must be a JSON object")
        case_id = value.get("id")
        if not isinstance(case_id, str) or not case_id.strip():
            raise LiveCanaryError(f"case {path} must have a non-empty id")
        if case_id in ids:
            raise LiveCanaryError(f"duplicate case id: {case_id}")
        if value.get("sandbox") != "read-only":
            raise LiveCanaryError(f"case {case_id} must declare sandbox read-only")
        ids.add(case_id)
        cases.append(value)
    return cases


def _capture_marker(path: Path) -> tuple[bool, bytes | None, int | None]:
    if not path.exists():
        return False, None, None
    try:
        return True, path.read_bytes(), stat.S_IMODE(path.stat().st_mode)
    except OSError as exc:
        raise LiveCanaryError(f"cannot preserve repository profile marker {path}: {exc}") from exc


def _restore_marker(path: Path, state: tuple[bool, bytes | None, int | None]) -> None:
    existed, content, mode = state
    try:
        if existed:
            assert content is not None and mode is not None
            path.write_bytes(content)
            path.chmod(mode)
        else:
            path.unlink(missing_ok=True)
    except OSError as exc:
        raise LiveCanaryError(f"cannot restore repository profile marker {path}: {exc}") from exc


def _inventory(codex_home: Path) -> tuple[list[dict[str, Any]], str]:
    candidates: list[tuple[str, Path]] = []
    for label in ("skills", "agents"):
        root = codex_home / label
        if root.is_dir():
            candidates.extend(
                (path.relative_to(codex_home).as_posix(), path)
                for path in root.rglob("*")
                if path.is_file()
            )
    for label in ("AGENTS.md", "config.toml"):
        path = codex_home / label
        if path.is_file():
            candidates.append((label, path))
    entries = [
        {"path": relative, "size": path.stat().st_size, "sha256": _sha256_file(path)}
        for relative, path in sorted(candidates)
    ]
    required = {"skills/.teamwork-version", "skills/.teamwork-profile", "AGENTS.md", "config.toml"}
    present = {entry["path"] for entry in entries}
    missing = sorted(required - present)
    if missing:
        raise LiveCanaryError(f"installed Codex inventory is incomplete: {', '.join(missing)}")
    encoded = json.dumps(entries, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return entries, _sha256_bytes(encoded)


def _installed_marker(codex_home: Path, name: str) -> str:
    path = codex_home / "skills" / name
    try:
        value = path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise LiveCanaryError(f"cannot read installed marker {path}: {exc}") from exc
    if not value:
        raise LiveCanaryError(f"installed marker is empty: {path}")
    return value


def _load_trajectories(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise LiveCanaryError(f"cannot read raw trajectories {path}: {exc}") from exc
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise LiveCanaryError(f"invalid trajectory JSON on line {line_number}: {exc}") from exc
        if not isinstance(record, dict) or record.get("record_type") != "teamwork_live_trajectory":
            raise LiveCanaryError(f"trajectory line {line_number} has the wrong record type")
        records.append(record)
    if not records:
        raise LiveCanaryError("raw trajectory file is empty")
    run_ids = [record.get("run_id") for record in records]
    if not all(isinstance(value, str) and value for value in run_ids):
        raise LiveCanaryError("every trajectory must have a non-empty run_id")
    if len(run_ids) != len(set(run_ids)):
        raise LiveCanaryError("raw trajectories contain duplicate run_id values")
    return records


def _safe_environment(home: Path, codex_home: Path) -> dict[str, str]:
    """Build the complete child environment without forwarding ambient secrets."""

    return {
        "HOME": str(home),
        "CODEX_HOME": str(codex_home),
        "PATH": os.environ.get("PATH", os.defpath),
    }


def _verify_git_root(workdir: Path) -> None:
    env = {
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "PATH": os.environ.get("PATH", os.defpath),
    }
    try:
        completed = subprocess.run(
            ["git", "-C", str(workdir), "rev-parse", "--show-toplevel"],
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise LiveCanaryError(f"cannot verify --workdir as a Git root: {exc}") from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip() or f"git exited {completed.returncode}"
        raise LiveCanaryError(f"--workdir must be a real Git worktree root: {detail}")
    if not completed.stdout.strip():
        raise LiveCanaryError("Git verification returned an empty worktree root")
    try:
        root = Path(completed.stdout.strip()).resolve()
    except (OSError, RuntimeError) as exc:
        raise LiveCanaryError(f"cannot resolve verified Git root: {exc}") from exc
    if root != workdir:
        raise LiveCanaryError(
            f"--workdir must be the Git worktree root (git reported {root})"
        )


def _redacted_usage(value: Any) -> Any:
    """Retain only fixed-schema numeric token counters."""

    if isinstance(value, list):
        return [_redacted_usage(item) for item in value]
    if not isinstance(value, dict):
        return None
    return {
        key: item
        for key in sorted(USAGE_FIELDS)
        if isinstance((item := value.get(key)), (int, float))
        and not isinstance(item, bool)
    }


def _redacted_costs(value: Any) -> list[int | float | None] | None:
    if not isinstance(value, list):
        return None
    return [
        item if isinstance(item, (int, float)) and not isinstance(item, bool) else None
        for item in value
    ]


def _run_command(args: argparse.Namespace) -> int:
    workdir = args.workdir.expanduser().resolve()
    review_dir = args.review_dir.expanduser().resolve()
    cases = [path.expanduser().resolve() for path in args.cases]
    if not workdir.is_dir():
        raise LiveCanaryError(f"--workdir is not a directory: {workdir}")
    for field in ("model", "effort", "profile"):
        if not isinstance(getattr(args, field), str) or not getattr(args, field).strip():
            raise LiveCanaryError(f"--{field} must be non-empty")
    if args.repeats < 1 or args.timeout_seconds < 1 or args.max_trajectories < 1:
        raise LiveCanaryError("repeats, timeout-seconds, and max-trajectories must be positive")
    loaded_cases = _load_cases(cases)
    trajectory_count = len(loaded_cases) * args.repeats
    if trajectory_count > args.max_trajectories:
        raise LiveCanaryError(
            f"requested {trajectory_count} trajectories exceeds --max-trajectories {args.max_trajectories}"
        )
    auth_file = args.auth_file.expanduser().resolve() if args.auth_file else None
    if args.dry_run and auth_file is not None:
        raise LiveCanaryError("--auth-file is not allowed with --dry-run")
    if not args.dry_run and (auth_file is None or not auth_file.is_file()):
        raise LiveCanaryError("non-dry-run requires an existing --auth-file")
    _verify_git_root(workdir)
    try:
        review_dir.mkdir(mode=0o700, parents=False, exist_ok=False)
        review_dir.chmod(0o700)
        (review_dir / REVIEWS_DIR).mkdir(mode=0o700)
    except OSError as exc:
        raise LiveCanaryError(f"cannot create new review directory {review_dir}: {exc}") from exc

    marker = workdir / ".teamwork-profile"
    marker_state = _capture_marker(marker)
    temp_home = Path(tempfile.mkdtemp(prefix="teamwork-installed-canary-"))
    codex_home = temp_home / ".codex"
    raw_path = review_dir / RAW_NAME
    manifest_path = review_dir / MANIFEST_NAME
    result = 0
    primary_error: BaseException | None = None
    finalization_errors: list[str] = []
    try:
        codex_home.mkdir(mode=0o700)
        env = _safe_environment(temp_home, codex_home)
        if auth_file is not None:
            try:
                shutil.copyfile(auth_file, codex_home / "auth.json")
                (codex_home / "auth.json").chmod(0o600)
            except OSError as exc:
                raise LiveCanaryError(f"cannot copy isolated authentication: {exc}") from exc
        install_argv = [
            str(workdir / "install.sh"), "--copy", "--no-notifications",
            "--profile", args.profile, "codex",
        ]
        installed = subprocess.run(
            install_argv, cwd=workdir, env=env, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=args.timeout_seconds, check=False,
        )
        if installed.returncode != 0:
            raise LiveCanaryError(
                f"isolated Codex install failed with exit {installed.returncode}: {installed.stderr.strip()}"
            )
        entries, inventory_sha = _inventory(codex_home)
        package_version = _installed_marker(codex_home, ".teamwork-version")
        installed_profile = _installed_marker(codex_home, ".teamwork-profile")
        if installed_profile != args.profile:
            raise LiveCanaryError(
                f"installed profile {installed_profile!r} does not match requested profile {args.profile!r}"
            )
        runner = workdir / "scripts" / "run-teamwork-live-eval.py"
        runner_argv = [
            sys.executable, str(runner), "--arm", f"installed-{args.profile}",
            "--model", args.model, "--effort", args.effort,
            "--workdir", str(workdir), "--output", str(raw_path),
            "--cases", *[str(path) for path in cases],
            "--repeats", str(args.repeats),
            "--timeout-seconds", str(args.timeout_seconds),
        ]
        if args.dry_run:
            runner_argv.append("--dry-run")
        ran = subprocess.run(
            runner_argv, cwd=workdir, env=env, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=(args.timeout_seconds * trajectory_count) + 30, check=False,
        )
        if not raw_path.is_file():
            raise LiveCanaryError(
                f"trajectory runner failed before producing output (exit {ran.returncode}): {ran.stderr.strip()}"
            )
        try:
            records = _load_trajectories(raw_path)
        except LiveCanaryError as exc:
            detail = ran.stderr.strip()
            if ran.returncode != 0 and detail:
                raise LiveCanaryError(
                    f"trajectory runner exited {ran.returncode} before producing valid records: {detail}"
                ) from exc
            raise
        if len(records) != trajectory_count:
            raise LiveCanaryError(
                f"trajectory runner produced {len(records)} records; expected {trajectory_count}"
            )
        links = [
            {"run_id": record["run_id"], "trajectory_sha256": trajectory_sha256(record)}
            for record in records
        ]
        codex_versions = {
            config.get("codex_version")
            for record in records
            if isinstance((config := record.get("config_source")), dict)
            and isinstance(config.get("codex_version"), str)
            and config.get("codex_version").strip()
        }
        if not args.dry_run and len(codex_versions) != 1:
            raise LiveCanaryError(
                "live trajectories must report one consistent Codex CLI version"
            )
        codex_version = next(iter(codex_versions), None)
        availability_sources = [
            {"kind": "INSTALLED_FILE", "path": entry["path"], "sha256": entry["sha256"]}
            for entry in entries
            if entry["path"].endswith("/SKILL.md")
        ]
        config = next((entry for entry in entries if entry["path"] == "config.toml"), None)
        if config:
            availability_sources.append(
                {"kind": "CONFIG", "path": config["path"], "sha256": config["sha256"]}
            )
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "record_type": "teamwork_installed_canary_manifest",
            "package_version": package_version,
            "profile": args.profile,
            "host": {"codex_version": codex_version},
            "requested_model": args.model,
            "requested_effort": args.effort,
            "dry_run": args.dry_run,
            "trajectory_limit": args.max_trajectories,
            "inventory": entries,
            "inventory_sha256": inventory_sha,
            "trajectories": links,
            "activation_evidence": {
                "claim": "AVAILABILITY_ONLY",
                "sources": availability_sources,
            },
            "claim_limits": [
                "No automatic skill activation claim.",
                "No Cursor or Claude Code parity claim.",
            ],
        }
        _write_json_exclusive(manifest_path, manifest, mode=0o400)
        manifest_path.chmod(0o400)
        result = ran.returncode
    except BaseException as exc:
        primary_error = exc
    finally:
        try:
            shutil.rmtree(temp_home)
        except OSError as cleanup_exc:
            finalization_errors.append(
                f"cannot delete isolated temporary home {temp_home}: {cleanup_exc}"
            )
        try:
            _restore_marker(marker, marker_state)
        except BaseException as restore_exc:
            finalization_errors.append(str(restore_exc))
    if finalization_errors:
        details = "; ".join(finalization_errors)
        if primary_error is not None:
            raise LiveCanaryError(
                f"{primary_error}; finalization failures: {details}"
            ) from primary_error
        raise LiveCanaryError(f"finalization failures: {details}")
    if primary_error is not None:
        raise primary_error
    print(f"wrote {trajectory_count} installed canary trajectories and immutable manifest to {review_dir}")
    return result


def _review_files(review_dir: Path) -> dict[str, Path]:
    root = review_dir / REVIEWS_DIR
    if not root.is_dir():
        raise LiveCanaryError(f"review directory is missing: {root}")
    files = sorted(root.glob("*.json"))
    return {path.stem: path for path in files}


def _finalize_command(args: argparse.Namespace) -> int:
    review_dir = args.review_dir.expanduser().resolve()
    raw_path = review_dir / RAW_NAME
    manifest_path = review_dir / MANIFEST_NAME
    summary_path = review_dir / SUMMARY_NAME
    if summary_path.exists():
        raise LiveCanaryError(f"refusing to overwrite existing summary: {summary_path}")
    records = _load_trajectories(raw_path)
    manifest = _read_json(manifest_path, "manifest")
    rubric = _read_json(args.rubric.expanduser().resolve(), "rubric")
    if not isinstance(manifest, dict) or manifest.get("record_type") != "teamwork_installed_canary_manifest":
        raise LiveCanaryError("install manifest has the wrong record type")
    manifest_activation = manifest.get("activation_evidence")
    if not isinstance(manifest_activation, dict) or manifest_activation.get("claim") != "AVAILABILITY_ONLY":
        raise LiveCanaryError("install manifest exceeds availability-only activation evidence")
    manifest_activation_sources = {
        (source.get("kind"), source.get("path"), source.get("sha256"))
        for source in manifest_activation.get("sources", [])
        if isinstance(source, dict)
    }
    files = _review_files(review_dir)
    expected = {record["run_id"] for record in records}
    actual = set(files)
    if expected != actual:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        details = []
        if missing:
            details.append(f"missing: {', '.join(missing)}")
        if extra:
            details.append(f"extra: {', '.join(extra)}")
        raise LiveCanaryError(f"reviews must cover every trajectory exactly ({'; '.join(details)})")
    manifest_links = {
        item.get("run_id"): item.get("trajectory_sha256")
        for item in manifest.get("trajectories", [])
        if isinstance(item, dict)
    } if isinstance(manifest, dict) else {}
    manifest_sha = _sha256_file(manifest_path)
    results: list[dict[str, Any]] = []
    for record in records:
        run_id = record["run_id"]
        digest = trajectory_sha256(record)
        if manifest_links.get(run_id) != digest:
            raise LiveCanaryError(f"manifest trajectory hash mismatch for {run_id}")
        review = _read_json(files[run_id], "review")
        try:
            validate_semantic_review(review, record, rubric)
        except SemanticReviewError as exc:
            raise LiveCanaryError(f"invalid semantic review for {run_id}: {exc}") from exc
        activation = review.get("activation_evidence")
        if not isinstance(activation, dict) or activation.get("claim") != "AVAILABILITY_ONLY":
            raise LiveCanaryError(f"review for {run_id} exceeds availability-only activation evidence")
        review_activation_sources = {
            (source.get("kind"), source.get("path"), source.get("sha256"))
            for source in activation.get("sources", [])
            if isinstance(source, dict)
        }
        if not review_activation_sources.issubset(manifest_activation_sources):
            raise LiveCanaryError(
                f"review for {run_id} cites activation evidence absent from the install manifest"
            )
        results.append({
            "run_id": run_id,
            "case_id": record.get("case_id"),
            "statuses": {
                "trajectory": record.get("status"),
                "execution": record.get("execution_status"),
                "structural": record.get("structural_status"),
                "model_provenance": record.get("model_provenance_status"),
            },
            "model": {"requested": record.get("model"), "resolved": record.get("resolved_model")},
            "effort": record.get("effort"),
            "usage": _redacted_usage(record.get("usage")),
            "reported_costs": _redacted_costs(record.get("reported_costs")),
            "verdict": review.get("verdict"),
            "scores": [
                {"criterion_id": item.get("criterion_id"), "outcome": item.get("outcome"), "score": item.get("score")}
                for item in review.get("criteria", []) if isinstance(item, dict)
            ],
            "hashes": {
                "trajectory_sha256": digest,
                "review_sha256": _sha256_file(files[run_id]),
                "manifest_sha256": manifest_sha,
            },
            "activation_claim": "AVAILABILITY_ONLY",
        })
    summary = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "teamwork_installed_canary_summary",
        "package_version": manifest.get("package_version"),
        "profile": manifest.get("profile"),
        "host": {
            "codex_version": (
                manifest.get("host", {}).get("codex_version")
                if isinstance(manifest.get("host"), dict)
                else None
            )
        },
        "claim_limits": [
            "Availability evidence does not prove automatic skill activation.",
            "This Codex canary does not prove Cursor or Claude Code parity.",
        ],
        "results": results,
    }
    _write_json_exclusive(summary_path, summary)
    if args.delete_raw:
        try:
            raw_path.unlink()
        except OSError as exc:
            raise LiveCanaryError(f"summary validated but raw deletion failed: {exc}") from exc
    print(f"wrote validated redacted summary for {len(results)} trajectories to {summary_path}")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run or finalize the opt-in isolated installed-Codex Teamwork canary."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run", help="install into a temporary home and record trajectories")
    run.add_argument("--model", required=True)
    run.add_argument("--effort", required=True)
    run.add_argument("--profile", required=True)
    run.add_argument("--workdir", required=True, type=Path)
    run.add_argument("--cases", required=True, nargs="+", type=Path)
    run.add_argument("--repeats", required=True, type=int)
    run.add_argument("--timeout-seconds", required=True, type=int)
    run.add_argument("--max-trajectories", required=True, type=int)
    run.add_argument("--review-dir", required=True, type=Path)
    run.add_argument("--auth-file", type=Path)
    run.add_argument("--dry-run", action="store_true")
    finalize = subparsers.add_parser("finalize", help="validate exact external reviews and redact output")
    finalize.add_argument("--review-dir", required=True, type=Path)
    finalize.add_argument("--rubric", type=Path, default=Path(DEFAULT_RUBRIC))
    finalize.add_argument("--delete-raw", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "run":
        return _run_command(args)
    return _finalize_command(args)
