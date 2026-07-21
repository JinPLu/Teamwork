"""CLI shared by installed-v4 host adapters."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from .host_matrix import CODEX_ROOT_ARMS, run_host_matrix


def parser_for(host: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=f"Run isolated Teamwork v4 trajectories through {host}.")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    binary_flag = {"codex": "--codex-bin", "cursor": "--cursor-agent-bin", "claude": "--claude-bin"}[host]
    run.add_argument(binary_flag, default={"codex": "codex", "cursor": "cursor-agent", "claude": "claude"}[host], dest="binary")
    run.add_argument("--profile", required=True, choices=("performance-first", "cost-first"))
    run.add_argument("--project-root", required=True, type=Path)
    run.add_argument("--candidate-manifest", required=True, type=Path)
    run.add_argument("--case-manifest", required=True, type=Path)
    run.add_argument("--output", required=True, type=Path)
    run.add_argument("--repeats", required=True, type=int)
    run.add_argument("--timeout-seconds", required=True, type=int)
    run.add_argument("--only-cases", nargs="+")
    if host == "codex":
        run.add_argument("--arm", required=True, choices=tuple(CODEX_ROOT_ARMS))
        # Root model/effort select only the parent Codex invocation. Child role
        # evidence still has to bind to the candidate's profile-rendered map.
        run.add_argument("--model", required=True)
        run.add_argument("--effort", required=True)
        run.add_argument("--max-trajectories", required=True, type=int)
    return parser


def main(host: str, argv: Sequence[str] | None = None) -> int:
    args = parser_for(host).parse_args(argv)
    return run_host_matrix(
        host=host, binary=args.binary, profile=args.profile,
        # Preserve raw paths: the candidate runner validates them lexically and
        # rejects links before it ever reads a candidate input.
        project_root=args.project_root,
        candidate_manifest=args.candidate_manifest,
        case_manifest=args.case_manifest, output=args.output,
        repeats=args.repeats, timeout_seconds=args.timeout_seconds, extra={},
        only_cases=set(args.only_cases) if args.only_cases else None,
        max_trajectories=getattr(args, "max_trajectories", None),
        arm=getattr(args, "arm", None),
        parent_model=getattr(args, "model", None),
        parent_effort=getattr(args, "effort", None),
    )
