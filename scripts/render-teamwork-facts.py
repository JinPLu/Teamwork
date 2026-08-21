#!/usr/bin/env python3
"""Fill <!-- BEGIN GENERATED --> blocks from config/teamwork-facts.yaml."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from teamwork_tooling.simple_yaml import load_simple_yaml  # noqa: E402

FACTS_REL = Path("config/teamwork-facts.yaml")
BEGIN = "<!-- BEGIN GENERATED: {name} -->"
END = "<!-- END GENERATED: {name} -->"
BLOCK_RE = re.compile(
    r"<!-- BEGIN GENERATED: ([a-z0-9-]+) -->\n.*?<!-- END GENERATED: \1 -->",
    re.DOTALL,
)

TARGETS = (
    Path("README.md"),
    Path("README.en.md"),
    Path("CURSOR.md"),
    Path("CLAUDE.md"),
    Path("CODEX.md"),
    Path("docs/architecture.md"),
)


def facts_path(root: Path) -> Path:
    return root / FACTS_REL


def load_facts(root: Path) -> dict:
    return load_simple_yaml(facts_path(root))


def _kinds(facts: dict) -> list[str]:
    kinds = facts["kinds"]
    if not isinstance(kinds, list) or not kinds:
        raise SystemExit("facts.yaml kinds must be a non-empty list")
    return [str(item) for item in kinds]


def render_blocks(facts: dict) -> dict[str, str]:
    kinds = _kinds(facts)
    meanings = facts["kind_meanings"]
    hosts = facts["hosts"]
    checkpoint = facts["checkpoint_path"]
    kind_root = facts["kind_root"]
    cursor_skills = ", ".join(f"`{name}`" for name in facts["cursor_skills"])

    meaning_lines = ["The seven meanings are:", ""]
    for index, kind in enumerate(kinds):
        row = meanings[kind]
        suffix = ";" if index < len(kinds) - 1 else "."
        meaning_lines.append(
            f"- {row['label']} (`{kind}/`): {row['meaning']}{suffix}"
        )
    kind_meanings = "\n".join(meaning_lines)

    table_zh_rows = ["| 文档 | 它记录什么 |", "| --- | --- |"]
    table_en_rows = ["| Document | What it records |", "| --- | --- |"]
    for kind in kinds:
        row = meanings[kind]
        table_zh_rows.append(f"| {row['emoji']} {row['label']} | {row['meaning_zh']} |")
        table_en_rows.append(
            f"| {row['emoji']} {row['label']} | {row['meaning'][0].upper() + row['meaning'][1:]}. |"
        )

    host_counts = (
        f"Claude Code installs {hosts['claude']['roles']} roles and omits Explorer "
        "because that host already provides Explore. Cursor installs "
        f"{hosts['cursor']['roles']} roles and omits Explorer and Debugger, and "
        "does not install the Debug or Goal Skills; unknown-cause diagnosis uses "
        "host Debug. Codex retains the Explorer role, plus Debug, Goal, and "
        "Debugger."
    )
    host_counts_zh = (
        f"Claude Code 安装 {hosts['claude']['roles']} 个角色并使用宿主自带 Explore；"
        f"Cursor 安装 {hosts['cursor']['roles']} 个角色（省略 Explorer 与 Debugger），"
        "且不安装 Debug / Goal Skill，未知原因诊断使用宿主 Debug；"
        "Codex 仍保留 Explorer，以及 Debug、Goal 和 Debugger。"
    )
    host_counts_en = (
        f"Claude Code installs {hosts['claude']['roles']} roles and uses the host's "
        "built-in Explore. Cursor installs "
        f"{hosts['cursor']['roles']} roles (omitting Explorer and Debugger) and "
        "does not install the Debug or Goal Skills; unknown-cause diagnosis uses "
        "host Debug. Codex keeps Explorer, plus Debug, Goal, and Debugger."
    )
    persistence_zh = (
        "当原生交互或专项方法到达可复用语义结果、且你已经接受该结果时，Root 在同一"
        f"响应周期把纯 Markdown 写入 `{kind_root}`；进入 mode 或调用宿主界面本身不会"
        "落盘，也不必先点名 Skill。Writer 只在不耽误写入时帮忙。每份文档同时保留一份"
        "**当前综合**和按时间追加的**历史**，既方便快速阅读，也不会抹掉结论如何变化。"
        f"默认路径为 `{checkpoint}`，同一稳定身份复用已有路径。\n\n"
        + "\n".join(table_zh_rows)
    )
    persistence_en = (
        "When a native interaction or focused method reaches a reusable semantic "
        f"result and you accept that result, Root writes plain Markdown under `{kind_root}` "
        "in the same response cycle. Entering a mode or invoking a host surface is not "
        "itself a write, and you do not need to name a Skill first. Writer helps only "
        "when that does not delay the write. Each document carries both a **current "
        "synthesis** and an append-only **chronological history**, so it is quick to "
        "read without hiding how the conclusion changed. Default paths are "
        f"`{checkpoint}`; reuse the path for the same stable identity.\n\n"
        + "\n".join(table_en_rows)
    )
    cursor_skills_block = (
        f"The adapter exposes {hosts['cursor']['skills']} focused Skills "
        f"({cursor_skills}) and {hosts['cursor']['roles']} optional helper roles: "
        "Researcher, Challenger, Planner, Reviewer, Worker, and Writer. "
        f"Cursor installs {hosts['cursor']['roles']} roles; Explorer and Debugger "
        "are intentionally omitted."
    )
    return {
        "kind-meanings": kind_meanings,
        "host-counts": host_counts,
        "host-counts-zh": host_counts_zh,
        "host-counts-en": host_counts_en,
        "persistence-zh": persistence_zh,
        "persistence-en": persistence_en,
        "cursor-skills": cursor_skills_block,
        "kind-root": f"`{kind_root}`",
        "checkpoint-path": f"`{checkpoint}`",
    }


def replace_blocks(text: str, blocks: dict[str, str], rel: Path) -> str:
    names = BLOCK_RE.findall(text)
    if not names:
        return text

    def repl(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in blocks:
            raise SystemExit(f"unknown generated block {name!r} in {rel}")
        return f"{BEGIN.format(name=name)}\n{blocks[name]}\n{END.format(name=name)}"

    updated = BLOCK_RE.sub(repl, text)
    missing = [name for name in names if name not in blocks]
    if missing:
        raise SystemExit(f"unknown generated blocks in {rel}: {missing}")
    return updated


def iter_targets(root: Path) -> list[Path]:
    return [root / rel for rel in TARGETS]


def apply(root: Path, check: bool) -> int:
    blocks = render_blocks(load_facts(root))
    dirty: list[str] = []
    for path in iter_targets(root):
        before = path.read_text(encoding="utf-8")
        after = replace_blocks(before, blocks, path.relative_to(root))
        if after != before:
            dirty.append(path.relative_to(root).as_posix())
            if not check:
                path.write_text(after, encoding="utf-8")
    if check and dirty:
        print("stale generated docs:", ", ".join(dirty), file=sys.stderr)
        return 1
    if not check and dirty:
        print("updated:", ", ".join(dirty))
    else:
        print("OK: generated docs facts")
    return 0


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--root", type=Path, default=ROOT)
    result.add_argument(
        "--check",
        action="store_true",
        help="fail when tracked files differ from rendered facts",
    )
    return result


def main() -> int:
    arguments = parser().parse_args()
    root = arguments.root.resolve()
    try:
        return apply(root, arguments.check)
    except (OSError, ValueError, KeyError) as exc:
        print(f"render-teamwork-facts failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
