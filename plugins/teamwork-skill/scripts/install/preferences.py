#!/usr/bin/env python3
"""Read and atomically update Teamwork's global install preferences."""

from __future__ import annotations

import argparse
import json
import os
import stat
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 2
OWNER = "teamwork"
PROFILES = {"performance-first", "cost-first"}
PROFILE_SOURCES = {
    "cli",
    "env",
    "recorded",
    "baseline",
}
CAPABILITY_SOURCES = {
    "cli",
    "env",
    "recorded",
    "observed-ready",
    "baseline",
    "new-capability-default",
}
CAPABILITIES = ("codegraph", "gpu_broker")
DESIRED_VALUES = {"enabled", "disabled"}
OBSERVED_STATES = {"ready", "missing", "stale", "unknown", "failed", "not-checked"}
RECEIPT_ACTIONS = {"none", "refresh", "skip", "preflight"}
RECEIPT_STATUSES = {"not-run", "ready", "disabled", "failed"}


class PreferenceError(RuntimeError):
    pass


class ObsoletePreferenceError(PreferenceError):
    """A Teamwork-owned pre-7 receipt that must not influence current settings."""

    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def preference_path() -> Path:
    raw_root = os.environ.get("XDG_STATE_HOME")
    state_root = Path(raw_root).expanduser() if raw_root else Path.home() / ".local" / "state"
    return state_root / "teamwork" / "install-preferences.json"


def require_timestamp(value: Any, label: str, *, nullable: bool = False) -> None:
    if nullable and value is None:
        return
    if not isinstance(value, str) or not value.endswith("Z"):
        raise PreferenceError(f"{label} must be an RFC3339 UTC timestamp")
    try:
        datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise PreferenceError(f"{label} must be an RFC3339 UTC timestamp") from exc


def require_exact_keys(value: Any, expected: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != expected:
        raise PreferenceError(f"{label} must contain exactly {sorted(expected)}")
    return value


def validate_state(value: Any) -> dict[str, Any]:
    state = require_exact_keys(
        value,
        {"schema_version", "owner", "updated_at", "desired", "observed", "receipts"},
        "preference document",
    )
    if state["schema_version"] != SCHEMA_VERSION or state["owner"] != OWNER:
        raise PreferenceError(
            f"preference document is not an owned Teamwork schema-v{SCHEMA_VERSION} receipt"
        )
    require_timestamp(state["updated_at"], "updated_at")

    desired = require_exact_keys(
        state["desired"], {"profile", *CAPABILITIES}, "desired"
    )
    profile = require_exact_keys(
        desired["profile"], {"value", "source", "updated_at"}, "desired.profile"
    )
    if profile["value"] not in PROFILES or profile["source"] not in PROFILE_SOURCES:
        raise PreferenceError("desired.profile contains an unsupported value or source")
    require_timestamp(profile["updated_at"], "desired.profile.updated_at")

    for capability in CAPABILITIES:
        entry = require_exact_keys(
            desired[capability], {"value", "source", "updated_at"}, f"desired.{capability}"
        )
        if entry["value"] not in DESIRED_VALUES or entry["source"] not in CAPABILITY_SOURCES:
            raise PreferenceError(f"desired.{capability} contains an unsupported value or source")
        require_timestamp(entry["updated_at"], f"desired.{capability}.updated_at")

    observed = require_exact_keys(state["observed"], set(CAPABILITIES), "observed")
    receipts = require_exact_keys(state["receipts"], set(CAPABILITIES), "receipts")
    for capability in CAPABILITIES:
        observation = require_exact_keys(
            observed[capability],
            {"state", "version", "detail", "checked_at"},
            f"observed.{capability}",
        )
        if observation["state"] not in OBSERVED_STATES:
            raise PreferenceError(f"observed.{capability}.state is unsupported")
        if observation["version"] is not None and not isinstance(observation["version"], str):
            raise PreferenceError(f"observed.{capability}.version must be a string or null")
        if observation["detail"] is not None and not isinstance(observation["detail"], str):
            raise PreferenceError(f"observed.{capability}.detail must be a string or null")
        require_timestamp(
            observation["checked_at"], f"observed.{capability}.checked_at", nullable=True
        )

        receipt = require_exact_keys(
            receipts[capability],
            {"last_action", "status", "detail", "updated_at"},
            f"receipts.{capability}",
        )
        if receipt["last_action"] not in RECEIPT_ACTIONS:
            raise PreferenceError(f"receipts.{capability}.last_action is unsupported")
        if receipt["status"] not in RECEIPT_STATUSES:
            raise PreferenceError(f"receipts.{capability}.status is unsupported")
        if receipt["detail"] is not None and not isinstance(receipt["detail"], str):
            raise PreferenceError(f"receipts.{capability}.detail must be a string or null")
        require_timestamp(
            receipt["updated_at"], f"receipts.{capability}.updated_at", nullable=True
        )
    return state


def ensure_safe_parent(path: Path, *, create: bool) -> None:
    parent = path.parent
    if parent.is_symlink():
        raise PreferenceError(f"refusing Teamwork preference directory symlink: {parent}")
    if parent.exists() and not parent.is_dir():
        raise PreferenceError(f"Teamwork preference parent is not a directory: {parent}")
    if create and not parent.exists():
        parent.mkdir(parents=True, mode=0o700)
        if parent.is_symlink() or not parent.is_dir():
            raise PreferenceError(f"Teamwork preference directory is unsafe: {parent}")


def load_state(path: Path) -> dict[str, Any] | None:
    ensure_safe_parent(path, create=False)
    if path.is_symlink():
        raise PreferenceError(f"refusing Teamwork preference symlink: {path}")
    if not path.exists():
        return None
    info = path.stat()
    if not stat.S_ISREG(info.st_mode):
        raise PreferenceError(f"Teamwork preference path is not a regular file: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PreferenceError(f"cannot read valid Teamwork preferences at {path}: {exc}") from exc
    if (
        isinstance(value, dict)
        and value.get("owner") == OWNER
        and value.get("schema_version") == 1
    ):
        raise ObsoletePreferenceError(
            "Teamwork schema-v1 preferences are obsolete and are not reused by Teamwork 7"
        )
    return validate_state(value)


def atomic_write(path: Path, state: dict[str, Any]) -> None:
    validate_state(state)
    ensure_safe_parent(path, create=True)
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise PreferenceError(f"refusing unsafe Teamwork preference path: {path}")
    fd, raw_temporary = tempfile.mkstemp(prefix=f".{path.name}.teamwork-", dir=path.parent)
    temporary = Path(raw_temporary)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(state, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        if path.is_symlink() or (path.exists() and not path.is_file()):
            raise PreferenceError(f"Teamwork preference path changed while writing: {path}")
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        temporary.unlink(missing_ok=True)


def default_observation() -> dict[str, Any]:
    return {"state": "not-checked", "version": None, "detail": None, "checked_at": None}


def default_receipt(value: str, timestamp: str) -> dict[str, Any]:
    if value == "disabled":
        return {
            "last_action": "skip",
            "status": "disabled",
            "detail": "disabled by preference",
            "updated_at": timestamp,
        }
    return {"last_action": "none", "status": "not-run", "detail": None, "updated_at": None}


def new_state(
    *,
    profile: str,
    profile_source: str,
    codegraph: str,
    codegraph_source: str,
    gpu_broker: str,
    gpu_broker_source: str,
) -> dict[str, Any]:
    timestamp = utc_now()
    return {
        "schema_version": SCHEMA_VERSION,
        "owner": OWNER,
        "updated_at": timestamp,
        "desired": {
            "profile": {"value": profile, "source": profile_source, "updated_at": timestamp},
            "codegraph": {
                "value": codegraph,
                "source": codegraph_source,
                "updated_at": timestamp,
            },
            "gpu_broker": {
                "value": gpu_broker,
                "source": gpu_broker_source,
                "updated_at": timestamp,
            },
        },
        "observed": {capability: default_observation() for capability in CAPABILITIES},
        "receipts": {
            "codegraph": default_receipt(codegraph, timestamp),
            "gpu_broker": default_receipt(gpu_broker, timestamp),
        },
    }


def resolve(args: argparse.Namespace) -> int:
    path = preference_path()
    original_status = "missing"
    try:
        state = load_state(path)
    except ObsoletePreferenceError:
        # Teamwork 7 deliberately does not translate pre-7 preference values.
        # A recorded resolve replaces only this Teamwork-owned receipt with
        # explicit current choices (or the documented current baseline).
        state = None
        original_status = "obsolete"
    except PreferenceError as exc:
        print(f"Teamwork install preferences refused: {exc}", file=sys.stderr)
        return 1

    changed = state is None
    if state is None:
        profile = args.profile or "performance-first"
        profile_source = args.profile_source or "baseline"
        codegraph = args.codegraph or "disabled"
        codegraph_source = args.codegraph_source or "baseline"
        gpu_broker = args.gpu_broker or "disabled"
        gpu_broker_source = args.gpu_broker_source or "baseline"
        state = new_state(
            profile=profile,
            profile_source=profile_source,
            codegraph=codegraph,
            codegraph_source=codegraph_source,
            gpu_broker=gpu_broker,
            gpu_broker_source=gpu_broker_source,
        )
    else:
        original_status = "valid"
        overrides = {
            "profile": (args.profile, args.profile_source),
            "codegraph": (args.codegraph, args.codegraph_source),
            "gpu_broker": (args.gpu_broker, args.gpu_broker_source),
        }
        for field, (value, source) in overrides.items():
            if value is None:
                continue
            entry = state["desired"][field]
            if entry["value"] == value and entry["source"] == source:
                continue
            timestamp = utc_now()
            entry.update({"value": value, "source": source, "updated_at": timestamp})
            state["updated_at"] = timestamp
            if field in CAPABILITIES:
                state["receipts"][field] = default_receipt(value, timestamp)
            changed = True

    if args.record and changed:
        try:
            atomic_write(path, state)
        except (OSError, PreferenceError) as exc:
            print(f"Teamwork install preferences refused: {exc}", file=sys.stderr)
            return 1

    print(
        "\t".join(
            (
                state["desired"]["profile"]["value"],
                state["desired"]["codegraph"]["value"],
                state["desired"]["gpu_broker"]["value"],
                "valid" if args.record else original_status,
            )
        )
    )
    return 0


def status(args: argparse.Namespace) -> int:
    path = preference_path()
    try:
        state = load_state(path)
    except ObsoletePreferenceError as exc:
        if args.field == "json":
            print(
                json.dumps(
                    {"status": "obsolete", "detail": str(exc), "path": str(path)},
                    sort_keys=True,
                )
            )
        else:
            print("obsolete")
        return 0
    except PreferenceError as exc:
        if args.field == "json":
            print(json.dumps({"status": "invalid", "detail": str(exc)}, sort_keys=True))
        else:
            print("invalid")
        return 0
    if state is None:
        if args.field == "json":
            print(json.dumps({"status": "missing", "path": str(path)}, sort_keys=True))
        else:
            print("missing")
        return 0
    if args.field == "json":
        print(json.dumps({"status": "valid", "path": str(path), "state": state}, sort_keys=True))
    elif args.field == "status":
        print("valid")
    elif args.field == "profile":
        print(state["desired"]["profile"]["value"])
    else:
        print(state["desired"][args.field.replace("-", "_")]["value"])
    return 0


def record_capability(args: argparse.Namespace) -> int:
    path = preference_path()
    try:
        state = load_state(path)
        if state is None:
            raise PreferenceError("cannot record capability result before preferences are resolved")
        timestamp = utc_now()
        state["updated_at"] = timestamp
        state["observed"][args.capability] = {
            "state": args.observed,
            "version": args.version,
            "detail": args.detail,
            "checked_at": timestamp,
        }
        state["receipts"][args.capability] = {
            "last_action": args.action,
            "status": args.receipt_status,
            "detail": args.detail,
            "updated_at": timestamp,
        }
        atomic_write(path, state)
    except (OSError, PreferenceError) as exc:
        print(f"Teamwork install preferences refused: {exc}", file=sys.stderr)
        return 1
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    subparsers = result.add_subparsers(dest="command", required=True)

    resolve_parser = subparsers.add_parser("resolve")
    resolve_parser.add_argument("--profile", choices=sorted(PROFILES))
    resolve_parser.add_argument("--profile-source", choices=("cli", "env"))
    resolve_parser.add_argument("--codegraph", choices=sorted(DESIRED_VALUES))
    resolve_parser.add_argument("--codegraph-source", choices=("cli", "env"))
    resolve_parser.add_argument("--gpu-broker", choices=sorted(DESIRED_VALUES))
    resolve_parser.add_argument("--gpu-broker-source", choices=("cli", "env"))
    resolve_parser.add_argument("--record", action="store_true")

    status_parser = subparsers.add_parser("status")
    status_parser.add_argument(
        "--field",
        choices=("json", "status", "profile", "codegraph", "gpu-broker"),
        default="json",
    )

    record_parser = subparsers.add_parser("record-capability")
    record_parser.add_argument("--capability", choices=CAPABILITIES, required=True)
    record_parser.add_argument("--observed", choices=sorted(OBSERVED_STATES), required=True)
    record_parser.add_argument("--version")
    record_parser.add_argument("--detail")
    record_parser.add_argument("--action", choices=sorted(RECEIPT_ACTIONS), required=True)
    record_parser.add_argument(
        "--receipt-status", choices=sorted(RECEIPT_STATUSES), required=True
    )
    return result


def main() -> int:
    args = parser().parse_args()
    if args.command == "resolve":
        for value, source, label in (
            (args.profile, args.profile_source, "profile"),
            (args.codegraph, args.codegraph_source, "codegraph"),
            (args.gpu_broker, args.gpu_broker_source, "gpu-broker"),
        ):
            if (value is None) != (source is None):
                raise SystemExit(f"{label} value and source must be provided together")
        return resolve(args)
    if args.command == "status":
        return status(args)
    return record_capability(args)


if __name__ == "__main__":
    raise SystemExit(main())
