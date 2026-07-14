#!/usr/bin/env python3
"""Run and finalize the opt-in installed-Codex Teamwork semantic canary."""

from __future__ import annotations

import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from teamwork_tooling.live_canary import LiveCanaryError, main  # noqa: E402


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except LiveCanaryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
