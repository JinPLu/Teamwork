#!/usr/bin/env python3
"""Run candidate-isolated Teamwork v4 trajectories through Cursor."""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from teamwork_tooling.evaluation.host_cli import main  # noqa: E402
from teamwork_tooling.evaluation.host_matrix import HostMatrixError  # noqa: E402

if __name__ == "__main__":
    try:
        raise SystemExit(main("cursor"))
    except HostMatrixError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
