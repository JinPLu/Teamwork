#!/usr/bin/env python3
"""Configure or check Teamwork's Codex custom-agent routing contract."""

from __future__ import annotations

import argparse
import pathlib

from codex_routing_config import RoutingConfigError
from codex_routing_config import RoutingReport
from codex_routing_config import apply_config
from codex_routing_config import inspect_config
from codex_routing_config import print_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Safely configure or inspect the Codex multi-agent namespace used "
            "to select installed Teamwork custom agents."
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
        help="check routing readiness without changing config (default)",
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
        report = apply_config(args.config) if args.apply else inspect_config(args.config)
    except RoutingConfigError as exc:
        report = RoutingReport(
            status="invalid",
            config_path=str(args.config.expanduser()),
            ready=False,
            issues=[str(exc)],
        )
        print_report(report, args.json)
        return 1
    print_report(report, args.json)
    return 0 if report.ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
