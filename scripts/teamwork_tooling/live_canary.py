"""Isolated installed-Codex canary orchestration and redacted finalization."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

from .semantic_review import (
    SemanticReviewError,
    trajectory_sha256,
    validate_pairwise_review,
    validate_semantic_review,
)


SCHEMA_VERSION = 1
RAW_NAME = "raw-trajectories.jsonl"
MANIFEST_NAME = "install-manifest.json"
SUMMARY_NAME = "summary.json"
REVIEWS_DIR = "reviews"
DEFAULT_RUBRIC = "evals/teamwork/rubrics/teamwork-live-semantic-v1.json"
DEFAULT_PAIRWISE_RUBRIC = "evals/teamwork/rubrics/teamwork-pairwise-v1.json"
PAIRWISE_CONTROLLER_NAME = "pairwise-controller-v1.json"
PAIRWISE_RESULT_NAME = "pairwise-comparison-v1.json"
PAIRWISE_INPUTS_DIR = "reviewer-inputs"
PAIRWISE_REVIEWS_DIR = "pairwise-reviews"
FROZEN_GOLD_CASES = {
    "human-outcome-community-research-gold",
    "human-outcome-exact-action-gold",
    "human-outcome-uncertain-diagnosis-gold",
    "human-outcome-review-findings-gold",
}
FROZEN_CONTROL_CASES = {
    "direct-artifact-only-control",
    "quoted-workflow-terms-control",
    "expert-precision-control",
}
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


def _inventory(codex_home: Path, skills_root: Path) -> tuple[list[dict[str, Any]], str]:
    candidates: list[tuple[str, Path]] = []
    if skills_root.is_dir():
        candidates.extend(
            (f"user-skills/{path.relative_to(skills_root).as_posix()}", path)
            for path in skills_root.rglob("*")
            if path.is_file()
        )
    for label in ("agents",):
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
    required = {
        "user-skills/.teamwork-version",
        "user-skills/.teamwork-profile",
        "AGENTS.md",
        "config.toml",
    }
    present = {entry["path"] for entry in entries}
    missing = sorted(required - present)
    if missing:
        raise LiveCanaryError(f"installed Codex inventory is incomplete: {', '.join(missing)}")
    encoded = json.dumps(entries, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return entries, _sha256_bytes(encoded)


def _installed_marker(skills_root: Path, name: str) -> str:
    path = skills_root / name
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


def _prompt_sha256(record: Mapping[str, Any]) -> str:
    """Bind retained evidence to prompts without retaining prompt prose."""

    turns = record.get("turns")
    prompts = [turn.get("prompt") for turn in turns if isinstance(turn, dict)] if isinstance(turns, list) else []
    encoded = json.dumps(prompts, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return _sha256_bytes(encoded)


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
    for field in ("arm", "model", "effort", "profile"):
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
        skills_root = temp_home / ".agents" / "skills"
        entries, inventory_sha = _inventory(codex_home, skills_root)
        package_version = _installed_marker(skills_root, ".teamwork-version")
        installed_profile = _installed_marker(skills_root, ".teamwork-profile")
        if installed_profile != args.profile:
            raise LiveCanaryError(
                f"installed profile {installed_profile!r} does not match requested profile {args.profile!r}"
            )
        runner = workdir / "scripts" / "run-teamwork-live-eval.py"
        runner_argv = [
            sys.executable, str(runner), "--arm", args.arm,
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
            "arm": args.arm,
            "host": {"codex_version": codex_version},
            "requested_model": args.model,
            "requested_effort": args.effort,
            "repeats": args.repeats,
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
                "prompt_sha256": _prompt_sha256(record),
            },
            "provenance": {
                "package_version": manifest.get("package_version"),
                "evidence_lane": "LIVE",
                "host": "codex",
                "model": record.get("resolved_model") or record.get("model"),
                "config_sha256": manifest_sha,
                "prompt_sha256": _prompt_sha256(record),
                "repeats": manifest.get("repeats"),
                "trajectory_sha256": digest,
                "review_sha256": _sha256_file(files[run_id]),
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


def _arm_specs(raw_specs: Sequence[str]) -> list[tuple[str, Path]]:
    if len(raw_specs) != 2:
        raise LiveCanaryError("compare requires exactly two --arm OPAQUE=CANARY_DIR values")
    result: list[tuple[str, Path]] = []
    for raw in raw_specs:
        arm_id, separator, directory = raw.partition("=")
        if not separator or not arm_id.strip() or not directory.strip():
            raise LiveCanaryError("each compare --arm must be OPAQUE=CANARY_DIR")
        result.append((arm_id.strip(), Path(directory).expanduser().resolve()))
    if result[0][0] == result[1][0]:
        raise LiveCanaryError("compare arm IDs must be distinct")
    return result


def _comparison_sources(raw_specs: Sequence[str]) -> tuple[list[tuple[str, Path]], dict[str, dict[tuple[str, int], dict[str, Any]]], dict[str, str]]:
    arms = _arm_specs(raw_specs)
    records_by_arm: dict[str, dict[tuple[str, int], dict[str, Any]]] = {}
    manifest_hashes: dict[str, str] = {}
    expected_cases = FROZEN_GOLD_CASES | FROZEN_CONTROL_CASES
    expected_keys: set[tuple[str, int]] | None = None
    for arm_id, directory in arms:
        records = _load_trajectories(directory / RAW_NAME)
        manifest_path = directory / MANIFEST_NAME
        manifest = _read_json(manifest_path, "comparison source manifest")
        if not isinstance(manifest, dict) or manifest.get("record_type") != "teamwork_installed_canary_manifest":
            raise LiveCanaryError(f"comparison source {directory} has the wrong manifest record type")
        manifest_links = {
            item.get("run_id"): item.get("trajectory_sha256")
            for item in manifest.get("trajectories", [])
            if isinstance(item, dict)
        }
        keyed: dict[tuple[str, int], dict[str, Any]] = {}
        for record in records:
            case_id = record.get("case_id")
            repeat_index = record.get("repeat_index")
            if not isinstance(case_id, str) or not isinstance(repeat_index, int) or isinstance(repeat_index, bool) or repeat_index < 1:
                raise LiveCanaryError("comparison source has invalid case_id or repeat_index")
            key = (case_id, repeat_index)
            if key in keyed:
                raise LiveCanaryError(f"comparison source has duplicate case/repeat: {case_id}/{repeat_index}")
            digest = trajectory_sha256(record)
            if manifest_links.get(record.get("run_id")) != digest:
                raise LiveCanaryError(f"comparison source trajectory hash mismatch for {record.get('run_id')}")
            hard_status = (
                record.get("status"), record.get("execution_status"),
                record.get("structural_status"), record.get("model_provenance_status"),
            )
            if hard_status != ("completed", "completed", "passed", "verified"):
                raise LiveCanaryError(f"comparison source hard-gate fail for {case_id}/{repeat_index}: {hard_status}")
            keyed[key] = record
        keys = set(keyed)
        if {case_id for case_id, _ in keys} != expected_cases:
            raise LiveCanaryError("comparison sources must contain exactly the frozen gold and control case IDs")
        repeats_by_case = {
            case_id: {repeat for current_case, repeat in keys if current_case == case_id}
            for case_id in expected_cases
        }
        if len({tuple(sorted(value)) for value in repeats_by_case.values()}) != 1:
            raise LiveCanaryError("comparison source repeat indexes must match for every frozen case")
        if expected_keys is not None and keys != expected_keys:
            raise LiveCanaryError("comparison sources do not have the same exact case/repeat manifest")
        expected_keys = keys
        records_by_arm[arm_id] = keyed
        manifest_hashes[arm_id] = _sha256_file(manifest_path)
    return arms, records_by_arm, manifest_hashes


def _installed_inventory_bytes(directory: Path) -> int:
    manifest = _read_json(directory / MANIFEST_NAME, "comparison source manifest")
    inventory = manifest.get("inventory") if isinstance(manifest, dict) else None
    if not isinstance(inventory, list) or not inventory:
        raise LiveCanaryError("comparison source manifest lacks installed inventory")
    total = 0
    for entry in inventory:
        if not isinstance(entry, dict):
            raise LiveCanaryError("comparison source inventory entry must be an object")
        size = entry.get("size")
        digest = entry.get("sha256")
        path = entry.get("path")
        if (
            not isinstance(path, str)
            or not path
            or not isinstance(size, int)
            or isinstance(size, bool)
            or size < 0
            or not isinstance(digest, str)
            or not re.fullmatch(r"[0-9a-f]{64}", digest)
        ):
            raise LiveCanaryError("comparison source inventory entry has invalid path, size, or hash")
        total += size
    return total


def _neutral_side(record: Mapping[str, Any]) -> dict[str, Any]:
    turns = record.get("turns") if isinstance(record.get("turns"), list) else []
    return {
        "trajectory_sha256": trajectory_sha256(record),
        "response": record.get("final_output"),
        "turn_responses": [turn.get("final_output") for turn in turns if isinstance(turn, dict)],
    }


def _reviewer_packet(
    controller: Mapping[str, Any],
    reviewer: str,
    rubric_id: str,
    schedule_rows: Sequence[Mapping[str, Any]],
    records_by_arm: Mapping[str, Mapping[tuple[str, int], Mapping[str, Any]]],
) -> dict[str, Any]:
    pairs: list[dict[str, Any]] = []
    for row in schedule_rows:
        if row.get("reviewer_id") != reviewer:
            continue
        key = (row.get("case_id"), row.get("repeat_index"))
        left_record = records_by_arm[row["left_arm_id"]][key]
        right_record = records_by_arm[row["right_arm_id"]][key]
        pairs.append({
            "pair_id": row["pair_id"],
            "case_id": row["case_id"],
            "repeat_index": row["repeat_index"],
            "left_trajectory_sha256": trajectory_sha256(left_record),
            "right_trajectory_sha256": trajectory_sha256(right_record),
            "left": _neutral_side(left_record),
            "right": _neutral_side(right_record),
            "required_evidence": {
                "category": left_record.get("category"),
                "unscored_annotations": left_record.get("unscored_annotations"),
            },
        })
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "teamwork_pairwise_reviewer_input",
        "comparison_id": controller.get("comparison_id"),
        "reviewer_id": reviewer,
        "rubric_id": rubric_id,
        "pairs": pairs,
    }


def _compare_prepare(args: argparse.Namespace) -> int:
    review_dir = args.review_dir.expanduser().resolve()
    arms, records_by_arm, manifest_hashes = _comparison_sources(args.arm)
    if len(args.reviewer_id) != 2 or len(set(args.reviewer_id)) != 2 or any(not item.strip() for item in args.reviewer_id):
        raise LiveCanaryError("compare prepare requires exactly two distinct non-empty --reviewer-id values")
    rubric_path = args.rubric.expanduser().resolve()
    rubric = _read_json(rubric_path, "pairwise rubric")
    rubric_id = rubric.get("id") if isinstance(rubric, dict) else None
    if not isinstance(rubric_id, str) or not rubric_id:
        raise LiveCanaryError("pairwise rubric must have a non-empty id")
    try:
        review_dir.mkdir(mode=0o700, parents=False, exist_ok=False)
        (review_dir / PAIRWISE_INPUTS_DIR).mkdir(mode=0o700)
        (review_dir / PAIRWISE_REVIEWS_DIR).mkdir(mode=0o700)
    except OSError as exc:
        raise LiveCanaryError(f"cannot create comparison review directory {review_dir}: {exc}") from exc
    rng = random.Random(args.seed)
    arm_ids = [item[0] for item in arms]
    schedule: list[dict[str, Any]] = []
    packets = {
        reviewer: {
            "schema_version": SCHEMA_VERSION,
            "record_type": "teamwork_pairwise_reviewer_input",
            "comparison_id": args.comparison_id,
            "reviewer_id": reviewer,
            "rubric_id": rubric_id,
            "pairs": [],
        }
        for reviewer in args.reviewer_id
    }
    keys = sorted(records_by_arm[arm_ids[0]])
    for pair_number, (case_id, repeat_index) in enumerate(keys, start=1):
        first_left = rng.randrange(2)
        pair_id = f"pair-{pair_number:04d}"
        for reviewer_index, reviewer in enumerate(args.reviewer_id):
            left_index = first_left if reviewer_index == 0 else 1 - first_left
            left_arm = arm_ids[left_index]
            right_arm = arm_ids[1 - left_index]
            left_record = records_by_arm[left_arm][(case_id, repeat_index)]
            right_record = records_by_arm[right_arm][(case_id, repeat_index)]
            schedule.append({
                "pair_id": pair_id, "reviewer_id": reviewer,
                "case_id": case_id, "repeat_index": repeat_index,
                "left_arm_id": left_arm, "right_arm_id": right_arm,
                "left_trajectory_sha256": trajectory_sha256(left_record),
                "right_trajectory_sha256": trajectory_sha256(right_record),
            })
            packets[reviewer]["pairs"].append({
                "pair_id": pair_id, "case_id": case_id, "repeat_index": repeat_index,
                "left_trajectory_sha256": trajectory_sha256(left_record),
                "right_trajectory_sha256": trajectory_sha256(right_record),
                "left": _neutral_side(left_record), "right": _neutral_side(right_record),
                "required_evidence": {
                    "category": left_record.get("category"),
                    "unscored_annotations": left_record.get("unscored_annotations"),
                },
            })
    controller = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "teamwork_pairwise_controller",
        "comparison_id": args.comparison_id,
        "transition": args.transition,
        "stage": args.stage,
        "rubric_id": rubric_id,
        "rubric_sha256": _sha256_file(rubric_path),
        "seed": args.seed,
        "reviewers": list(args.reviewer_id),
        "arm_mapping": [
            {"arm_id": arm_id, "canary_dir": str(directory), "manifest_sha256": manifest_hashes[arm_id]}
            for arm_id, directory in arms
        ],
        "schedule": schedule,
    }
    _write_json_exclusive(review_dir / PAIRWISE_CONTROLLER_NAME, controller)
    for reviewer, packet in packets.items():
        _write_json_exclusive(review_dir / PAIRWISE_INPUTS_DIR / f"{reviewer}.json", packet)
    print(f"wrote balanced blind comparison packets for {len(keys)} matched pairs to {review_dir}")
    return 0


def _normalized_outcome(outcome: str, schedule: Mapping[str, Any]) -> str:
    if outcome == "TIE":
        return "TIE"
    return schedule["left_arm_id"] if outcome == "LEFT_BETTER" else schedule["right_arm_id"]


def _compare_finalize(args: argparse.Namespace) -> int:
    review_dir = args.review_dir.expanduser().resolve()
    result_path = review_dir / PAIRWISE_RESULT_NAME
    if result_path.exists():
        raise LiveCanaryError(f"refusing to overwrite existing comparison result: {result_path}")
    controller = _read_json(review_dir / PAIRWISE_CONTROLLER_NAME, "pairwise controller")
    if not isinstance(controller, dict) or controller.get("record_type") != "teamwork_pairwise_controller":
        raise LiveCanaryError("pairwise controller has the wrong record type")
    arms, records_by_arm, manifest_hashes = _comparison_sources(args.arm)
    arm_ids = [item[0] for item in arms]
    mapping = controller.get("arm_mapping")
    expected_mapping = [
        {"arm_id": arm_id, "canary_dir": str(directory), "manifest_sha256": manifest_hashes[arm_id]}
        for arm_id, directory in arms
    ]
    if mapping != expected_mapping:
        raise LiveCanaryError("compare arm mapping or source manifest hash changed since prepare")
    rubric_path = args.rubric.expanduser().resolve()
    rubric = _read_json(rubric_path, "pairwise rubric")
    if controller.get("rubric_sha256") != _sha256_file(rubric_path):
        raise LiveCanaryError("pairwise rubric changed since prepare")
    reviewers = controller.get("reviewers")
    if not isinstance(reviewers, list) or len(reviewers) != 2 or len(set(reviewers)) != 2:
        raise LiveCanaryError("pairwise controller must bind two distinct reviewer IDs")
    schedule_rows = controller.get("schedule")
    if not isinstance(schedule_rows, list) or not schedule_rows:
        raise LiveCanaryError("pairwise controller schedule is missing")
    schedule: dict[tuple[str, str], Mapping[str, Any]] = {}
    order_counts = {arm_id: 0 for arm_id in arm_ids}
    for row in schedule_rows:
        if not isinstance(row, dict):
            raise LiveCanaryError("pairwise schedule row must be an object")
        key = (row.get("reviewer_id"), row.get("pair_id"))
        if key in schedule:
            raise LiveCanaryError(f"duplicate pairwise schedule row: {key}")
        schedule[key] = row
        if row.get("left_arm_id") not in order_counts or row.get("right_arm_id") not in order_counts:
            raise LiveCanaryError("pairwise schedule contains an unmatched arm")
        order_counts[row["left_arm_id"]] += 1
        source = records_by_arm[row["left_arm_id"]].get((row.get("case_id"), row.get("repeat_index")))
        other = records_by_arm[row["right_arm_id"]].get((row.get("case_id"), row.get("repeat_index")))
        if source is None or other is None:
            raise LiveCanaryError("pairwise schedule contains an unmatched case/repeat")
        if trajectory_sha256(source) != row.get("left_trajectory_sha256") or trajectory_sha256(other) != row.get("right_trajectory_sha256"):
            raise LiveCanaryError("pairwise schedule trajectory hash mismatch")
    if len(set(order_counts.values())) != 1:
        raise LiveCanaryError("pairwise left/right order is unbalanced")
    secrets = set(arm_ids)
    for _, directory in arms:
        secrets.update({str(directory), directory.name})
    normalized: dict[str, list[str]] = {}
    review_hashes: dict[str, str] = {}
    for reviewer in reviewers:
        payload_path = review_dir / PAIRWISE_INPUTS_DIR / f"{reviewer}.json"
        review_path = review_dir / PAIRWISE_REVIEWS_DIR / f"{reviewer}.json"
        payload = _read_json(payload_path, "reviewer input")
        expected_payload = _reviewer_packet(
            controller, reviewer, rubric.get("id"), schedule_rows, records_by_arm
        )
        if payload != expected_payload:
            raise LiveCanaryError(
                f"reviewer input for {reviewer} changed since prepare or no longer matches source evidence"
            )
        review = _read_json(review_path, "pairwise review")
        try:
            validate_pairwise_review(review, payload, rubric, secrets)
        except SemanticReviewError as exc:
            raise LiveCanaryError(f"invalid pairwise review for {reviewer}: {exc}") from exc
        for judgment in review["judgments"]:
            key = (reviewer, judgment["pair_id"])
            row = schedule.get(key)
            if row is None:
                raise LiveCanaryError(f"unmatched pairwise judgment: {key}")
            normalized.setdefault(judgment["pair_id"], []).append(_normalized_outcome(judgment["outcome"], row))
        review_hashes[reviewer] = _sha256_file(review_path)
    decisions: list[dict[str, Any]] = []
    for pair_id, outcomes in sorted(normalized.items()):
        if len(outcomes) != 2 or outcomes[0] != outcomes[1]:
            raise LiveCanaryError(f"pairwise reviewer disagreement for {pair_id}")
        sample = next(row for row in schedule_rows if row["pair_id"] == pair_id)
        decisions.append({
            "pair_id": pair_id, "case_id": sample["case_id"],
            "repeat_index": sample["repeat_index"], "outcome": outcomes[0],
        })
    expected_pair_ids = {row["pair_id"] for row in schedule_rows}
    if set(normalized) != expected_pair_ids:
        raise LiveCanaryError("pairwise reviews do not completely cover the schedule")
    incumbent, candidate = arm_ids
    outcomes = [item["outcome"] for item in decisions]
    selection: str | None = None
    reason: str
    footprint_evidence: Any = None
    if controller.get("transition") == "a-to-b":
        if any(item == incumbent for item in outcomes):
            selection, reason = incumbent, "candidate was unanimously worse on at least one matched pair"
        elif any(item == candidate for item in outcomes):
            selection, reason = candidate, "candidate was unanimously tie-or-better on every pair and better on at least one"
        else:
            if args.smaller_footprint_evidence:
                supplied = _read_json(args.smaller_footprint_evidence.expanduser().resolve(), "smaller-footprint evidence")
                required = {
                    "record_type", "metric", "candidate_arm_id", "incumbent_arm_id",
                    "candidate_manifest_sha256", "incumbent_manifest_sha256",
                }
                if not isinstance(supplied, dict) or set(supplied) != required:
                    raise LiveCanaryError("smaller-footprint evidence has the wrong schema")
                if supplied.get("record_type") != "teamwork-pairwise-footprint-v1" or supplied.get("metric") != "installed_inventory_bytes":
                    raise LiveCanaryError("smaller-footprint evidence must use the verified installed_inventory_bytes metric")
                if supplied.get("candidate_arm_id") != candidate or supplied.get("incumbent_arm_id") != incumbent:
                    raise LiveCanaryError("smaller-footprint evidence must bind both opaque arms")
                if (
                    supplied.get("candidate_manifest_sha256") != manifest_hashes[candidate]
                    or supplied.get("incumbent_manifest_sha256") != manifest_hashes[incumbent]
                ):
                    raise LiveCanaryError("smaller-footprint evidence manifest hash mismatch")
                directories = dict(arms)
                candidate_value = _installed_inventory_bytes(directories[candidate])
                incumbent_value = _installed_inventory_bytes(directories[incumbent])
                if candidate_value >= incumbent_value:
                    raise LiveCanaryError("candidate installed inventory is not strictly smaller")
                footprint_evidence = {
                    **supplied,
                    "candidate_value": candidate_value,
                    "incumbent_value": incumbent_value,
                }
                selection, reason = candidate, "all pairs tied and controller supplied candidate smaller-footprint evidence"
            else:
                reason = "all pairs tied without smaller-footprint evidence"
    elif controller.get("transition") == "b-to-c":
        gold = [item for item in decisions if item["case_id"] in FROZEN_GOLD_CASES]
        controls = [item for item in decisions if item["case_id"] in FROZEN_CONTROL_CASES]
        if any(item["outcome"] == incumbent for item in decisions):
            selection, reason = incumbent, "candidate was unanimously worse on a frozen gold or control"
        elif gold and controls and all(
            any(item["case_id"] == case_id and item["outcome"] == candidate for item in gold)
            for case_id in FROZEN_GOLD_CASES
        ):
            selection, reason = candidate, "candidate was tie-or-better throughout and better on every frozen gold case"
        else:
            reason = "candidate did not improve every frozen gold case"
    else:
        raise LiveCanaryError("pairwise controller has an unknown transition")
    result = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "pairwise-comparison-v1",
        "comparison_id": controller.get("comparison_id"),
        "stage": controller.get("stage"),
        "transition": controller.get("transition"),
        "arm_mapping": mapping,
        "schedule": schedule_rows,
        "reviewer_ids": reviewers,
        "review_sha256": review_hashes,
        "matched_results": decisions,
        "selection": selection,
        "status": "SELECTED" if selection else "INCONCLUSIVE",
        "reason": reason,
        "smaller_footprint_evidence": footprint_evidence,
        "claim_limits": [
            "Development selection does not replace held-out release confirmation.",
            "Held-out release confirmation must not be used to retune the candidate.",
        ],
    }
    _write_json_exclusive(result_path, result)
    print(f"wrote private pairwise comparison result to {result_path}: {result['status']}")
    return 0 if selection else 2


def _compare_command(args: argparse.Namespace) -> int:
    if args.compare_phase == "prepare":
        return _compare_prepare(args)
    return _compare_finalize(args)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run or finalize the opt-in isolated installed-Codex Teamwork canary."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run", help="install into a temporary home and record trajectories")
    run.add_argument("--arm", default=None, help="opaque experiment arm label (defaults to installed-PROFILE)")
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
    compare = subparsers.add_parser("compare", help="prepare or finalize a private blind pairwise comparison")
    compare_phases = compare.add_subparsers(dest="compare_phase", required=True)
    prepare = compare_phases.add_parser("prepare", help="write balanced neutral reviewer packets")
    prepare.add_argument("--review-dir", required=True, type=Path)
    prepare.add_argument("--arm", required=True, action="append")
    prepare.add_argument("--comparison-id", required=True)
    prepare.add_argument("--reviewer-id", required=True, action="append")
    prepare.add_argument("--seed", required=True, type=int)
    prepare.add_argument("--transition", required=True, choices=("a-to-b", "b-to-c"))
    prepare.add_argument("--stage", required=True, choices=("dev", "release"))
    prepare.add_argument("--rubric", type=Path, default=Path(DEFAULT_PAIRWISE_RUBRIC))
    finish = compare_phases.add_parser("finalize", help="validate two reviews and select deterministically")
    finish.add_argument("--review-dir", required=True, type=Path)
    finish.add_argument("--arm", required=True, action="append")
    finish.add_argument("--rubric", type=Path, default=Path(DEFAULT_PAIRWISE_RUBRIC))
    finish.add_argument("--smaller-footprint-evidence", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "run":
        if args.arm is None:
            args.arm = f"installed-{args.profile}"
        return _run_command(args)
    if args.command == "finalize":
        return _finalize_command(args)
    return _compare_command(args)
