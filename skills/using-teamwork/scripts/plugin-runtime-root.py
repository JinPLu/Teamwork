#!/usr/bin/env python3
"""Print the containing Teamwork Marketplace runtime root, if this is one."""

from __future__ import annotations

import json
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[3]
    marker = root / ".teamwork-plugin-runtime"
    manifest_path = root / ".codex-plugin" / "plugin.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"not a Teamwork plugin runtime: {exc}") from exc
    if (
        marker.read_text(encoding="utf-8") != "TEAMWORK_CODEX_PLUGIN_RUNTIME=1\n"
        or manifest.get("name") != "teamwork-skill"
        or not (root / "install.sh").is_file()
    ):
        raise SystemExit("not a Teamwork Marketplace runtime")
    print(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
