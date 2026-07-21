"""Semantic and topology checks for the compact Teamwork skill set."""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Mapping

from .contracts import (
    CANONICAL_ROLES,
    CANONICAL_SKILL_COUNT,
    DESIGN_ADVERSARIAL_REFERENCE_PATH,
    EvalError,
    RETIRED_SKILLS,
    ROLE_TEMPLATE_PATHS,
    ROOT,
)


DESIGN_ADVERSARIAL_REFERENCE_CONCEPTS = (
    ("bounded trial budget", (r"Accept `2 <= B <= 5`",)),
    ("bounded dispatch cost", (r"`2B \+ 2` fresh dispatches",)),
    (
        "two fresh critics per hypothesis",
        (r"Every actual hypothesis gets exactly\s+two fresh Designer critics",),
    ),
    (
        "material revision consumes a new trial",
        (r"A materially revised hypothesis is a new trial",),
    ),
    (
        "two fresh final auditors",
        (r"Launch exactly two final Designer auditors",),
    ),
    (
        "dual pass closure",
        (r"Converge only when both final auditors return `PASS`",),
    ),
    (
        "full-budget closure remains valid",
        (r"final unit of `B` is valid closure",),
    ),
    (
        "budget exhaustion needs unfinished work",
        (r"`budget-exhausted` applies only when another trial\s+or audit repair is still required",),
    ),
    (
        "failure-closed states",
        (
            r"budget-exhausted\s*\|\s*audit-failed\s*\|\s*freshness-unproven\s*\|\s*capability-blocked\s*\|\s*interrupted",
        ),
    ),
)


def normalize_semantic_text(text: str) -> str:
    return " ".join(text.split()).casefold()


def discover_skill_inventory(root: Path = ROOT) -> dict[str, Path]:
    """Discover canonical skills from the public filesystem surface."""

    skill_root = root / "skills"
    if not skill_root.is_dir():
        raise EvalError("skills/ is missing")
    inventory: dict[str, Path] = {}
    for directory in sorted(path for path in skill_root.iterdir() if path.is_dir()):
        skill_file = directory / "SKILL.md"
        if not skill_file.is_file():
            raise EvalError(f"skills/{directory.name}: top-level skill directory lacks SKILL.md")
        inventory[directory.name] = skill_file
    return inventory


def parse_frontmatter(source: str, path: str) -> tuple[str, str]:
    match = re.match(r"\A---\n(.*?)\n---(?:\n|\Z)", source, re.DOTALL)
    if not match:
        raise EvalError(f"{path}: missing YAML frontmatter")
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            raise EvalError(f"{path}: malformed frontmatter line: {line}")
        key, value = line.split(":", 1)
        if key in fields:
            raise EvalError(f"{path}: duplicate frontmatter key: {key}")
        fields[key] = value.strip()
    if set(fields) != {"name", "description"}:
        raise EvalError(f"{path}: frontmatter must contain only name and description")
    if not fields["description"].startswith("Use when "):
        raise EvalError(f"{path}: description must start with 'Use when '")
    return fields["name"], fields["description"]


def _require_concept(path: str, text: str, label: str, patterns: Iterable[str]) -> None:
    if not any(re.search(pattern, text, re.IGNORECASE | re.DOTALL) for pattern in patterns):
        raise EvalError(f"{path}: missing behavioral concept: {label}")


def _forbid_concept(path: str, text: str, label: str, patterns: Iterable[str]) -> None:
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE | re.DOTALL):
            raise EvalError(f"{path}: forbidden behavioral overlap: {label}")


SKILL_CONCEPTS: dict[str, tuple[tuple[str, tuple[str, ...]], ...]] = {
    "teamwork-explore": (
        ("local-only evidence", (r"local.{0,100}(?:repository|source|config|test|log|runtime|artifact)", r"本地.{0,100}(?:仓库|源码|配置|测试|日志|运行|产物)")),
        ("read-only boundary", (r"read[- ]only", r"只读")),
        ("no external research", (r"(?:do not|never|no).{0,50}(?:browse|external|web|research)", r"不.{0,40}(?:外部|联网|浏览|调研)")),
    ),
    "teamwork-research": (
        ("external lookup trigger", (r"\bexternal\b", r"\bweb\b", r"外部(?:调研|资料|来源)")),
        ("current or multi-source evidence", (r"current.{0,80}(?:source|fact)", r"multi[- ]source", r"(?:时效|当前).{0,40}(?:来源|事实)", r"多来源")),
        ("citations", (r"\bcitations?\b", r"\bcite\b", r"引用|链接")),
        ("local evidence stays native", (r"do not use for local repository/source/config/test/log/runtime/artifact inspection", r"external[- ]only.{0,100}do not inspect private local", r"(?:本地|代码库).{0,100}(?:原生|无需.*research|不.*research)")),
        ("read-only boundary", (r"read[- ]only", r"does not authorize.{0,80}(?:edit|write)", r"只读|不授权.{0,40}(?:修改|写入)")),
        ("privacy boundary", (r"(?:secret|credential|sensitive|private).{0,100}(?:query|disclos|source)", r"(?:秘密|凭据|敏感|私密).{0,100}(?:查询|披露|来源)")),
    ),
    "teamwork-design": (
        ("unresolved material choice trigger", (r"unresolved.{0,100}(?:product|architecture|workflow|contract|choice|tradeoff)", r"(?:material.{0,100}trade[- ]off|direction).{0,100}not (?:yet )?settled", r"未解决.{0,100}(?:产品|架构|工作流|契约|选择|取舍)")),
        ("local constraints first", (r"local.{0,80}(?:constraint|evidence|context).{0,80}(?:first|before)", r"先.{0,80}(?:本地|约束|证据|上下文)")),
        ("genuine alternatives only", (r"(?:2|two).{0,20}(?:3|three).{0,100}(?:genuine|real|meaningful).{0,40}(?:tradeoff|alternative)", r"(?:2|两).{0,20}(?:3|三).{0,100}(?:真实|实质).{0,40}(?:取舍|方案)")),
        ("recommendation before question", (r"recommend.{0,120}(?:before|then).{0,80}(?:ask|question)", r"先.{0,50}推荐.{0,80}(?:再|然后).{0,30}问")),
        ("bounded independent batch", (r"one bounded independent batch", r"one to three current choices", r"bounded.{0,80}independent.{0,80}batch")),
        ("dependency serialization", (r"dependent choices are serial", r"cannot change each other's.{0,120}(?:prompt|options|recommendation|closure signal)")),
        ("question criticality", (r"why the answer is critical", r"what it blocks", r"observable closing condition")),
        ("read-only and no implementation", (r"Design does not implement", r"(?:不实施|不实现).{0,180}(?:仅|只).{0,30}(?:artifact|文件)")),
        ("managed Design transaction", (r"design-inspect.{0,500}design-schema.{0,500}design-apply", r"expected_revision.{0,500}design-apply")),
        ("Plan boundary", (r"(?:selected|settled|chosen) direction.{0,160}\bplan\b", r"(?:Design is frozen|Freeze one durable Design).{0,300}Planner", r"controlled route returns.{0,180}Planner.{0,120}\bPlan\b", r"clear enough.{0,100}(?:execution )?plan", r"(?:已选|已确定|已收敛).{0,80}(?:方向|方案).{0,80}(?:plan|计划)")),
    ),
    "teamwork-plan": (
        ("selected direction prerequisite", (r"(?:selected|settled|chosen) direction", r"(?:已选|已确定|已收敛).{0,50}(?:方向|方案)")),
        ("owned ordered actions", (r"owned.{0,40}(?:ordered|sequence).{0,40}actions", r"ordered work units.{0,160}(?:owner|target surface)", r"(?:负责人|归属).{0,50}(?:顺序|有序).{0,40}(?:行动|步骤)")),
        ("dependencies and direct proof", (r"dependenc.{0,100}(?:direct|real).{0,40}(?:proof|verification|check)", r"依赖.{0,100}(?:直接|真实).{0,30}(?:证明|验证)")),
        ("stop or replan conditions", (r"(?:stop|replan).{0,40}conditions?", r"(?:停止|重新规划|重做计划).{0,40}条件")),
        ("no redesign or implementation", (r"Do not redesign or implement", r"(?:do not|never|no).{0,40}(?:compare options|redesign).{0,100}(?:do not|never|no).{0,30}implement", r"不.{0,30}(?:比较方案|重新设计).{0,100}不.{0,20}(?:实施|实现)")),
    ),
    "grill-me": (
        ("natural question-first trigger", (r"ask me first", r"questioned before action", r"先问我|先问清楚")),
        ("ordinary activation is no-write", (r"Natural\s+question-first\s+requests\s+remain\s+conversation-only\s+unless\s+they\s+are\s+independently\s+major", r"自然语言.{0,100}(?:不写|不授权.{0,30}写)")),
        ("major change auto-transaction", (r"Major-change Grill automatically records its state", r"major.{0,120}automatic.{0,120}(?:record|transaction)")),
        ("explicit save persistence", (r"Explicit \$grill-me, save, record, or resume requests also authorize the record", r"\$grill-me.{0,120}(?:save|resume|record)")),
        ("transaction-owned writer", (r"discussion-transaction\.py\s+inspect.{0,500}\bschema\b.{0,500}\bapply\b", r"apply is the sole discussion writer")),
        ("initialized writable prerequisite", (r"(?:initialized|initialised).{0,80}writable", r"已初始化.{0,60}可写")),
        ("no-files override", (r"no files.{0,180}(?:overrides?|wins|no write)", r"(?:不要文件|不落盘|no files).{0,120}(?:优先|不写|覆盖)")),
        ("global decision map", (r"global decision map", r"current critical path", r"goal.{0,40}boundary.{0,40}detail")),
        ("bounded independent batch", (r"one bounded independent batch", r"one to three current.{0,40}material questions", r"bounded.{0,80}independent.{0,80}batch")),
        ("dependency serialization", (r"dependent questions are serial", r"neither answer can change the other's.{0,120}(?:prompt|options|recommendation|closure signal)")),
        ("question criticality", (r"why it is critical", r"what it blocks", r"observable condition that closes")),
        ("recommendation before question", (r"recommend.{0,100}(?:before|then).{0,80}(?:question|batch)", r"先.{0,40}推荐.{0,80}(?:问题|决定|批次)")),
        ("no implementation authority", (r"(?:never|does not|no).{0,40}(?:implement|implementation authority)", r"不.{0,30}(?:实施|实现|授权实现)")),
    ),
    "teamwork-debug": (
        ("actual failure first", (r"actual.{0,40}(?:failure|failing)", r"真实.{0,30}(?:失败|报错)")),
        ("discriminating hypothesis", (r"discriminat.{0,80}(?:hypothes|evidence)", r"hypotheses.{0,120}(?:distinguish|smallest observation)", r"区分.{0,50}(?:假设|证据)")),
        ("authorized narrow fix", (r"authoriz.{0,60}(?:narrow|minimal).{0,30}fix", r"已授权.{0,50}(?:窄|最小).{0,20}修复")),
        ("same-path rerun", (r"rerun.{0,40}(?:same|failing).{0,20}path", r"重跑.{0,40}(?:同一|失败).{0,20}路径")),
    ),
    "teamwork-review": (
        ("read-only review", (r"read[- ]only", r"只读")),
        ("evidence-backed verdict", (r"evidence[- ](?:backed|based).{0,40}(?:verdict|finding|conclusion|`accept`)", r"证据.{0,30}(?:结论|发现|判断)")),
        ("acceptance boundary", (r"acceptance.{0,60}(?:criteria|evidence|boundary)", r"验收.{0,40}(?:标准|证据|边界)")),
    ),
    "teamwork-goal": (
        ("explicit modifier", (r"explicit.{0,80}(?:goal|keep working|terminal)", r"明确.{0,60}(?:目标|持续工作|终止条件)")),
        ("preserve scope", (r"preserv.{0,40}(?:scope|invariant)", r"保持.{0,40}(?:范围|不变量)")),
        ("strategy delta", (r"strategy delta", r"策略变化|改变策略")),
        ("real success signal", (r"real.{0,40}success signal", r"真实.{0,30}成功信号")),
    ),
    "teamwork-init": (
        ("project-only ownership", (r"project.{0,80}(?:only|scope|context)", r"仅.{0,30}项目|项目.{0,50}(?:范围|上下文)")),
        ("no global refresh", (r"(?:do not|never|no).{0,50}global.{0,30}(?:refresh|install|update)", r"不.{0,30}(?:全局刷新|全局安装|全局更新)")),
    ),
    "teamwork-update": (
        ("global-only ownership", (r"global.{0,60}(?:only|installation|refresh)", r"仅.{0,30}全局|全局.{0,40}(?:安装|刷新)")),
        ("no project initialization", (r"(?:do not|never|no).{0,60}project.{0,30}(?:init|context)", r"不.{0,30}(?:项目初始化|项目上下文)")),
    ),
}


def validate_skill_source_contract(skill: str, source_text: str) -> None:
    path = f"skills/{skill}/SKILL.md"
    name, _description = parse_frontmatter(source_text, path)
    if name != skill:
        raise EvalError(f"{path}: frontmatter name must match directory")
    concepts = SKILL_CONCEPTS.get(skill)
    if concepts is None:
        raise EvalError(f"{path}: no capability contract registered")
    for label, patterns in concepts:
        _require_concept(path, source_text, label, patterns)

    if skill == "teamwork-research":
        _forbid_concept(
            path,
            source_text,
            "local repository inspection activates Research",
            (r"(?:enter|activate|use).{0,50}research.{0,100}(?:local|repository|code|log|config|test)",),
        )
    elif skill == "teamwork-plan":
        _forbid_concept(
            path,
            source_text,
            "Plan owns option discovery",
            (r"(?<!do not )(?<!never )\b(?:generate|brainstorm|compare).{0,60}(?:alternatives|options)",),
        )


def validate_design_adversarial_reference_contract(source_text: str) -> None:
    path = DESIGN_ADVERSARIAL_REFERENCE_PATH
    for label, patterns in DESIGN_ADVERSARIAL_REFERENCE_CONCEPTS:
        _require_concept(path, source_text, label, patterns)


def dependency_cycles(edges: Mapping[str, Iterable[str]]) -> list[list[str]]:
    """Return cycles in a small directed dependency graph."""

    visiting: list[str] = []
    active: set[str] = set()
    visited: set[str] = set()
    cycles: list[list[str]] = []

    def visit(node: str) -> None:
        if node in active:
            start = visiting.index(node)
            cycles.append(visiting[start:] + [node])
            return
        if node in visited:
            return
        active.add(node)
        visiting.append(node)
        for target in edges.get(node, ()):
            visit(target)
        visiting.pop()
        active.remove(node)
        visited.add(node)

    for node in sorted(edges):
        visit(node)
    return cycles


def validate_skill_topology(root: Path = ROOT) -> dict[str, object]:
    inventory = discover_skill_inventory(root)
    names = set(inventory)
    if len(names) != CANONICAL_SKILL_COUNT:
        raise EvalError(
            f"skills/: canonical inventory must contain {CANONICAL_SKILL_COUNT} skills; "
            f"discovered {len(names)}"
        )
    remaining_retired = sorted(names & RETIRED_SKILLS)
    if remaining_retired:
        raise EvalError(f"skills/: retired skill remains: {', '.join(remaining_retired)}")
    for required in SKILL_CONCEPTS:
        if required not in names:
            raise EvalError(f"skills/: missing capability owner: {required}")

    behavior_refs = sorted(
        path.relative_to(root).as_posix()
        for path in (root / "skills").glob("*/references/**/*")
        if path.is_file()
    )
    allowed_refs = {
        "skills/teamwork-research/references/deep-research.md",
        "skills/teamwork-debug/references/runtime-diagnosis.md",
        "skills/teamwork-design/references/adversarial-search.md",
        "skills/teamwork-review/references/strict-review.md",
    }
    unexpected_refs = sorted(set(behavior_refs) - allowed_refs)
    if unexpected_refs:
        raise EvalError(
            "skills/: only the four named one-level advanced references are allowed: "
            + ", ".join(unexpected_refs)
        )
    skill_scripts = sorted(
        path.relative_to(root).as_posix()
        for path in (root / "skills").glob("*/scripts/**/*")
        if path.is_file()
    )
    if skill_scripts:
        raise EvalError(
            "skills/: skill-local behavioral scripts are not allowed: "
            + ", ".join(skill_scripts)
        )

    edges: dict[str, set[str]] = defaultdict(set)
    cross_loads: list[str] = []
    path_re = re.compile(r"skills/([a-z0-9-]+)/SKILL\.md")
    for owner, path in inventory.items():
        source = path.read_text(encoding="utf-8")
        parse_frontmatter(source, f"skills/{owner}/SKILL.md")
        for target in path_re.findall(source):
            edges[owner].add(target)
            if target != owner:
                cross_loads.append(f"{owner}->{target}")
        for referenced in re.findall(r"skills/([a-z0-9-]+)/references/[a-z0-9-]+\.md", source):
            if referenced != owner:
                cross_loads.append(f"{owner}->{referenced}-reference")
    if cross_loads:
        raise EvalError(
            "skills/: a SKILL.md must not load another Teamwork skill: "
            + ", ".join(sorted(cross_loads))
        )
    cycles = dependency_cycles(edges)
    if cycles:
        rendered = " ; ".join(" -> ".join(cycle) for cycle in cycles)
        raise EvalError(f"skills/: skill dependency cycle: {rendered}")

    return {
        "skills": sorted(names),
        "count": len(names),
        "behavior_references": behavior_refs,
        "cross_skill_loads": cross_loads,
        "cycles": cycles,
    }


def validate_role_template_sources(root: Path = ROOT) -> None:
    """Validate exact eight-role target semantics on every rendered host."""

    for host, mapping in ROLE_TEMPLATE_PATHS.items():
        expected = set(mapping.values())
        directory = root / f"templates/{host}-agents"
        observed = {
            path.relative_to(root).as_posix()
            for path in directory.iterdir()
            if path.is_file()
        }
        if observed != expected:
            raise EvalError(
                f"templates/{host}-agents/: expected exact eight-role inventory; "
                f"missing={sorted(expected - observed)}, extra={sorted(observed - expected)}"
            )
        for role in CANONICAL_ROLES:
            source_path = mapping[role]
            source = (root / source_path).read_text(encoding="utf-8")
            normalized = normalize_semantic_text(source).replace("_", "-")
            declared = f'name = "teamwork-{role}"' if host == "codex" else f"name: {role}"
            if declared not in normalized:
                raise EvalError(f"{source_path}: role identity does not match {role}")
            for label in (
                "mission:", "owned scope:", "input:", "output:", "verify:",
                "stop:", "tool boundary:", "write authority:", "acceptance limitation:",
            ):
                if label not in normalized:
                    raise EvalError(f"{source_path}: missing role target field {label}")
            for prohibition in ("do not spawn", "do not interact with the user", "do not expand scope", "do not self-accept"):
                if prohibition not in normalized:
                    raise EvalError(f"{source_path}: missing leaf-role boundary {prohibition}")
            if role in {"designer", "plan-reviewer", "reviewer"} and "write authority: none" not in normalized:
                raise EvalError(f"{source_path}: {role} must be strictly read-only")
            if role == "planner" and "single" not in normalized:
                raise EvalError(f"{source_path}: Planner lacks single-Plan-path authority")
            if role == "debugger" and "immutable" not in normalized:
                raise EvalError(f"{source_path}: Debugger lacks immutable dispatch authority")
            if role == "researcher" and not all(term in normalized for term in ("sanitized", "private", "read-only")):
                raise EvalError(f"{source_path}: Researcher lacks privacy/read-only semantics")
            if role == "explorer" and not any(term in normalized for term in ("do not browse", "never browse")):
                raise EvalError(f"{source_path}: Explorer lacks local-only semantics")


def validate_semantic_sources(root: Path = ROOT) -> None:
    topology = validate_skill_topology(root)
    for skill in topology["skills"]:
        path = root / "skills" / skill / "SKILL.md"
        validate_skill_source_contract(skill, path.read_text(encoding="utf-8"))
    validate_role_template_sources(root)
