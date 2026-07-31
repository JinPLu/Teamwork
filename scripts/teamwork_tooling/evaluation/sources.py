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
    (
        "automatic or explicit selection",
        (r"selects it automatically or an\s+explicit adversarial override",),
    ),
    ("bounded trial budget", (r"Accept a user override\s+only when `2 <= B <= 3`",)),
    ("invalid budget rejected", (r"reject an out-of-range override",)),
    ("automatic default budget", (r"If omitted, set\s+`B = 3`",)),
    ("no confirmation round", (r"do\s+not\s+request\s+confirmation",)),
    ("bounded dispatch cost", (r"2B \+ 2.{0,40}fresh\s+dispatches.{0,160}capped at eight total\s+children",)),
    (
        "two fresh critics per hypothesis",
        (r"Every actual hypothesis gets exactly\s+two fresh (?:internal )?Designer critics",),
    ),
    (
        "material revision consumes a new trial",
        (r"A materially revised hypothesis is a new trial",),
    ),
    (
        "two fresh final auditors",
        (r"Launch exactly two final (?:internal )?Designer\s+auditors",),
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
        (r"`budget-exhausted`\s+applies\s+only\s+when another trial\s+or audit repair is still required",),
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
        ("exact researcher dispatch", (r"Research\s*->\s*Researcher", r"first action after preparing.*brief MUST be Researcher dispatch")),
        ("capability blocked no fallback", (r"capability-blocked.{0,100}no named-method fallback", r"Root has no named-method fallback")),
        ("default one child cap4", (r"Default to one Researcher", r"daily work stays within cap4")),
        ("explicit five to eight only", (r"five to eight.{0,120}explicit adversarial/release", r"5-8.{0,120}explicit adversarial/release")),
        ("bounded sanitized packet", (r"bounded sanitized packet",)),
        ("external lookup trigger", (r"\bexternal\b", r"\bweb\b", r"外部(?:调研|资料|来源)")),
        ("current or multi-source evidence", (r"current.{0,80}(?:source|fact)", r"multi[- ]source", r"(?:时效|当前).{0,40}(?:来源|事实)", r"多来源")),
        ("direct support", (r"direct support", r"直接支持")),
        ("citations", (r"\bcitations?\b", r"\bcite\b", r"引用|链接")),
        ("claim ledger fields", (r"claim_map.{0,80}active_gap.{0,80}wave.{0,80}evidence_delta",)),
        ("conflict coverage stop", (r"contradiction.{0,80}not_found.{0,80}coverage_stop",)),
        ("lookup lightweight control", (r"`lookup`.{0,120}one canonical or official source",)),
        ("local evidence stays native", (r"do not use for local repository/source/config/test/log/runtime/artifact inspection", r"external[- ]only.{0,100}do not inspect private local", r"(?:本地|代码库).{0,100}(?:原生|无需.*research|不.*research)")),
        ("read-only boundary", (r"read[- ]only", r"does not authorize.{0,80}(?:edit|write)", r"只读|不授权.{0,40}(?:修改|写入)")),
        ("privacy boundary", (r"(?:secret|credential|sensitive|private).{0,100}(?:query|disclos|source)", r"(?:秘密|凭据|敏感|私密).{0,100}(?:查询|披露|来源)")),
    ),
    "teamwork-plan": (
        ("selected direction prerequisite", (r"(?:selected|settled|chosen) direction", r"(?:已选|已确定|已收敛).{0,50}(?:方向|方案)")),
        ("owned ordered actions", (r"owned.{0,40}(?:ordered|sequence).{0,40}actions", r"ordered work units.{0,160}(?:owner|target surface)", r"(?:负责人|归属).{0,50}(?:顺序|有序).{0,40}(?:行动|步骤)")),
        ("dependencies and direct proof", (r"dependenc.{0,100}(?:direct|real).{0,40}(?:proof|verification|check)", r"依赖.{0,100}(?:直接|真实).{0,30}(?:证明|验证)")),
        ("proof targets", (r"proof targets",)),
        ("capability blocked no fallback", (r"capability-blocked", r"fails closed before any write")),
        ("case-v2 plan packet", (r"case-v2 Plan", r"case-inspect.{0,120}case-schema")),
        ("accepted Collaborate transaction gate", (r"case-v2 Collaborate readback", r"pending, or blocked Collaborate records.{0,80}never\s+Plan-ready")),
        ("stop or replan conditions", (r"(?:stop|replan).{0,40}conditions?", r"(?:停止|重新规划|重做计划).{0,40}条件")),
        ("no redesign or implementation", (r"Do not redesign or\s+implement", r"(?:do not|never|no).{0,40}(?:compare options|redesign).{0,120}(?:do not|never|no).{0,30}implement", r"不.{0,30}(?:比较方案|重新设计).{0,100}不.{0,20}(?:实施|实现)")),
    ),
    "teamwork-collaborate": (
        ("natural collaboration trigger", (r"only public Teamwork\s+skill for natural dialogue, brainstorming, sustained questioning",)),
        ("dialogue brainstorm only", (r"`dialogue`.{0,160}`brainstorm`", r"not a third runtime mode")),
        ("challenge not mode", (r"Stress-testing is a challenge method inside dialogue or brainstorm,\s+not a third runtime mode",)),
        ("adversarial not mode", (r"method replaces only the challenge method", r"does not create a public Design workflow")),
        ("capability blocked no fallback", (r"capability-blocked.{0,100}Root must not perform a named-method fallback",)),
        ("case-v2 only", (r"managed case-v2 Collaborate checkpoint", r"legacy-v1.{0,120}fails closed")),
        ("unresolved material choice trigger", (r"decision convergence", r"meaningful alternatives", r"material frontier")),
        ("genuine alternatives only", (r"(?:two|2).{0,20}(?:three|3).{0,100}(?:meaningful|mutually exclusive|genuine).{0,60}(?:alternatives|options|choices)",)),
        ("recommendation before question", (r"before every question.{0,120}provisional recommendation", r"recommendation.{0,120}before.{0,80}(?:question|asking)")),
        ("bounded independent batch", (r"native bounded batch contains at most three questions", r"batch.{0,100}mutually independent")),
        ("dependency serialization", (r"dependent questions are serial", r"never\s+batch dependent questions")),
        ("question criticality", (r"why the answer is critical", r"what it blocks", r"observable\s+closing condition")),
        ("automatic adversarial gate", (r"at least two viable directions remain.{0,160}(?:costly|irreversible).*conflicting evidence",)),
        ("strategy overrides", (r"explicitly requests adversarial search",)),
        ("adaptive checkpoint threshold", (r"sustained semantic Collaborate state.{0,120}managed case-v2 Collaborate checkpoint", r"first substantive.{0,120}(?:dialogue|brainstorm).{0,120}defaults to a managed case-v2")),
        ("transaction-owned writer", (r"case-inspect.{0,240}case-schema.{0,240}case-apply", r"Writer calls\s+only the controlled transaction route")),
        ("initialized writable prerequisite", (r"(?:initialized|initialised).{0,80}writable", r"已初始化.{0,60}可写")),
        ("no-files override", (r"no files.{0,180}(?:overrides?|wins|no write)", r"(?:不要文件|不落盘|no files).{0,120}(?:优先|不写|覆盖)")),
        ("global decision map", (r"global decision map", r"whole decision map", r"current critical path", r"goal.{0,40}boundary.{0,40}detail")),
        ("global-to-detail order", (r"global\s*->\s*boundary\s*->\s*detail", r"whole decision map.{0,120}current batch")),
        ("one update per answered batch", (r"ask the question, wait for the answer, dispatch\s+Writer checkpoint",)),
        ("Collaborate acceptance state", (r"Acceptance requires closure evidence", r"active\.acceptance\s+==\s+accepted")),
        ("Plan boundary", (r"settled direction becomes Plan-ready only through an accepted\s+Collaborate state", r"Planner may proceed.{0,180}accepted readback")),
        ("no implementation authority", (r"authorize no implementation", r"(?:never|does not|no).{0,60}(?:implement|implementation authority)", r"不.{0,30}(?:实施|实现|授权实现)")),
    ),
    "teamwork-debug": (
        ("actual failure first", (r"actual.{0,40}(?:failure|failing)", r"真实.{0,30}(?:失败|报错)")),
        ("frozen failure signature", (r"freeze.{0,80}failure signature", r"frozen failure signature")),
        ("ranked hypothesis ledger", (r"rank.{0,40}(?:three to five|3-5).{0,80}hypotheses", r"ranked hypotheses")),
        ("hypothesis before probes", (r"hypotheses before broad.{0,100}(?:inspection|instrumentation|probe)", r"hypothes.{0,80}precede probes")),
        ("prediction and falsifier mapping", (r"observation predicted if it is true.{0,160}observation that would falsify", r"predictions.{0,80}falsifiers")),
        ("one discriminating experiment", (r"one active discriminating experiment at a time", r"one discriminating experiment at a time")),
        ("runtime log-first experiment", (r"Runtime Log-First", r"runtime.{0,120}temporary structured log", r"structured log.{0,160}E-\*")),
        ("instrumentation skip rationale", (r"Skip code instrumentation only when existing evidence already decides", r"skip rationale.{0,120}hypotheses it distinguishes")),
        ("discriminating hypothesis", (r"discriminat.{0,80}(?:hypothes|evidence)", r"hypotheses.{0,120}(?:distinguish|smallest observation)", r"区分.{0,50}(?:假设|证据)")),
        ("rejected hypotheses", (r"rejected hypotheses", r"supported.{0,80}weakened.{0,80}rejected")),
        ("authorized narrow fix", (r"authoriz.{0,60}(?:narrow|minimal).{0,30}fix", r"已授权.{0,50}(?:窄|最小).{0,20}修复")),
        ("same-path rerun", (r"rerun.{0,40}(?:same|failing).{0,20}path", r"重跑.{0,40}(?:同一|失败).{0,20}路径")),
        ("new failure split", (r"new-failure-split", r"materially different failure signature.{0,80}separate")),
        ("no review before cause", (r"Do not\s+invoke Reviewer", r"no Review.{0,80}cause.*unknown")),
    ),
    "teamwork-review": (
        ("read-only review", (r"read[- ]only", r"只读")),
        ("evidence-backed verdict", (r"evidence[- ](?:backed|based).{0,40}(?:verdict|finding|conclusion|`accept`)", r"证据.{0,30}(?:结论|发现|判断)")),
        ("acceptance boundary", (r"acceptance.{0,60}(?:criteria|evidence|boundary)", r"验收.{0,40}(?:标准|证据|边界)")),
        ("unsupported claim handling", (r"unsupported", r"unverified")),
        ("one repair batch", (r"one repair batch",)),
        ("one delta recheck", (r"one bounded delta recheck", r"at most one.{0,80}delta recheck")),
        ("case-v2 review artifact", (r"case-v2 review artifact",)),
    ),
    "teamwork-goal": (
        ("explicit modifier", (r"explicit.{0,80}(?:goal|keep working|terminal)", r"明确.{0,60}(?:目标|持续工作|终止条件)")),
        ("preserve scope", (r"preserv.{0,40}(?:scope|invariant)", r"保持.{0,40}(?:范围|不变量)")),
        ("strategy delta", (r"strategy delta", r"策略变化|改变策略")),
        ("real success signal", (r"real.{0,40}success signal", r"真实.{0,30}成功信号")),
        ("failure evidence status fields", (r"failure.{0,120}evidence_delta.{0,120}strategy_delta.{0,120}status", r"objective.{0,120}signal.{0,120}attempt")),
        ("case-v2 goal artifact", (r"case-v2 Goal",)),
    ),
    "teamwork-init": (
        ("project-only ownership", (r"project.{0,80}(?:only|scope|context)", r"仅.{0,30}项目|项目.{0,50}(?:范围|上下文)")),
        ("no global refresh", (r"(?:do not|never|no).{0,50}global.{0,30}(?:refresh|install|update)", r"不.{0,30}(?:全局刷新|全局安装|全局更新)")),
        ("exact-root migrate resume", (r"migrate --project-root <exact-project-root>.*resume --project-root <exact-project-root>",)),
        ("migration capability blocked", (r"capability-blocked",)),
    ),
    "teamwork-update": (
        ("global-only ownership", (r"global.{0,60}(?:only|installation|refresh)", r"仅.{0,30}全局|全局.{0,40}(?:安装|刷新)")),
        ("no project initialization", (r"(?:do not|never|no).{0,60}project.{0,30}(?:init|context)", r"不.{0,30}(?:项目初始化|项目上下文)")),
        ("exact-root migrate resume", (r"migrate --project-root <exact-project-root>.*resume --project-root <exact-project-root>",)),
        ("migration capability blocked", (r"capability-blocked",)),
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
        normalized_source = " ".join(source_text.split())
        _forbid_concept(
            path,
            normalized_source,
            "Plan owns option discovery",
            (
                r"(?<!do not )(?<!never )(?<!do not compare options or )"
                r"\b(?:generate|brainstorm|compare).{0,60}(?:alternatives|options)",
            ),
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
        "skills/teamwork-collaborate/references/adversarial-search.md",
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
    """Validate exact nine-role target semantics on every rendered host."""

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
                f"templates/{host}-agents/: expected exact nine-role inventory; "
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
            if role == "planner" and "execution-ready plan packet" not in normalized:
                raise EvalError(f"{source_path}: Planner lacks packet-only Plan authority")
            if role == "designer":
                for term in (
                    "governing criteria",
                    "direct evidence",
                    "assumption/disconfirming-evidence challenge",
                ):
                    if term not in normalized:
                        raise EvalError(f"{source_path}: Designer lacks {term} boundary")
            if role != "writer" and "bounded writing brief" not in normalized:
                raise EvalError(f"{source_path}: missing Writer handoff boundary")
            if role == "writer":
                for term in (
                    "standalone document",
                    "bounded writing brief",
                    "facts/sources/citations/decisions/authority/status/acceptance",
                    "managed artifacts only through their exact case-v2 specialized transaction",
                    "case-schema <operation> -> case-apply/readback",
                    "case-inspect first",
                    "legacy-v1 artifacts/collaborate/goal are read-only migration inputs, no write route",
                    "accept transaction-derived destination",
                    "execution=`workflow=execution`",
                    "no active goal",
                    "required transaction gate",
                    "registration",
                    "blocked without writing",
                    "do not research",
                    "do not fallback",
                    "code-coupled",
                ):
                    if term not in normalized:
                        raise EvalError(f"{source_path}: Writer lacks {term} boundary")
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
