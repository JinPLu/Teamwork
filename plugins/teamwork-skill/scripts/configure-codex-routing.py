#!/usr/bin/env python3
"""Configure or check Teamwork's static Codex custom-agent setup."""

from __future__ import annotations

import argparse
import pathlib

from codex_routing_config import RoutingConfigError
from codex_routing_config import RoutingReport
from codex_routing_config import apply_config
from codex_routing_config import inspect_config
from codex_routing_config import print_report
from codex_routing_config import preview_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Safely configure or inspect the stable Codex multi-agent feature "
            "used with installed Teamwork custom-agent profiles. This static "
            "Agent availability is reported separately from workflow success."
        )
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--apply",
        action="store_true",
        help="atomically migrate config.toml to the Teamwork routing contract",
    )
    mode.add_argument(
        "--check",
        action="store_true",
        help="check static routing configuration without changing config (default)",
    )
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="validate the exact routing migration without changing config",
    )
    parser.add_argument(
        "--config",
        type=pathlib.Path,
        default=pathlib.Path.home() / ".codex" / "config.toml",
        help="Codex config path (default: ~/.codex/config.toml)",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.apply:
            report = apply_config(args.config)
        elif args.dry_run:
            report = preview_config(args.config)
        else:
            report = inspect_config(args.config)
    except RoutingConfigError as exc:
        report = RoutingReport(
            status="invalid",
            config_path=str(args.config.expanduser()),
            ready=False,
            issues=[str(exc)],
            experimental_multi_agent_v2="unknown",
        )
        print_report(report, args.json)
        return 1
    print_report(report, args.json)
    return 0 if report.ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
