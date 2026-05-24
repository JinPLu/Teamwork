# Teamwork

![Teamwork workflow banner](assets/teamwork-hero.png)

Teamwork 是一组给 Claude Code、Codex 和 Cursor 用的 workflow skills。它不替代 coding agent；它让 agent 在容易跑偏的任务里按证据、计划、执行边界、验证和复查推进。

一句话：**先弄清楚，再动手；执行有边界，完成要有证据。**

## Why

Coding agent 常见的问题不是不会写代码，而是太快进入错误方向：

- 没读代码、diff、日志、测试，就先假设原因。
- 在本地反复试错，没查外部资料、论文、issue 或官方文档校准方向。
- 把“小改动”做成隐性重构。
- 调研、计划、实现、复查混在一起，执行者自己宣布完成。
- 多 agent 并行时没有所有权，互相覆盖或重复工作。

Teamwork 的目标是把这些风险变成明确的 workflow gate。

## Core Ideas

| Idea | Meaning |
|---|---|
| Evidence first | 重要判断先读直接证据，并区分 `observed`、`inferred`、`claimed`。 |
| Research calibration | Research 先理解本地真实主线，再用外部主源校准方向，避免本地反复试错。 |
| Progress anchor | 主线程锚定目标、执行备忘录、验证和复查结果，而不是维护长流水账。 |
| Targeted artifacts | `research/` 存可复用调研，`plans/` 存执行备忘录，`reports/` 存任务结论。 |
| Plan before edits | 代码修改前先有计划；非轻量、高风险、跨模块或含糊任务先 review plan。 |
| Bounded execution | Worker 只做计划内改动；发现需求、架构或外部证据缺口就停回 research/plan。 |
| Review before done | 完成必须有验证和复查；工具输出、总结、文件名或 README 说法都不是最终 verdict。 |

## How You Trigger It

你不需要记 skill 名。按人话说即可：

| You say | Teamwork does |
|---|---|
| “研究这个失败原因” / “看看有什么方案” | `teamwork-research`: 本地取证、外部校准、写 research artifact。 |
| “先给计划” / “这个改动怎么做” | `teamwork-plan`: 把方向变成可执行计划和验证标准。 |
| “执行这个计划” | `teamwork-execute`: 按计划最小改动，先跑 focused verification。 |
| “review 这个计划 / diff / 结果” | `teamwork-review`: 独立检查范围、证据、验证和回归风险。 |
| “跑到通过为止” / “继续迭代直到收敛” | `teamwork-goal`: 预算内自主迭代到验证通过、无进展或 blocker。 |

普通、明确、低风险的一步任务继续走 native flow。Teamwork 只在证据、计划、复查、并行或收敛能提升正确性时介入。

Skill entrypoints: `using-teamwork`, `teamwork`, `teamwork-research`, `teamwork-plan`, `teamwork-execute`, `teamwork-review`, `teamwork-goal`.

## Codex runtime

Teamwork 在 Codex 里是 **Codex-native, not hook-emulated**：

- `update_plan` 只是临时进度条，不是 durable plan。
- Codex subagents 用来做独立 Explorer、Worker 或 fresh-context review；非轻量任务先拆独立轨道，主线程继续做不重叠工作。
- Teamwork 激活后，视为用户已授权对独立的非轻量轨道自动分配 subagent；不需要等用户额外说 “fan out”。
- Native Codex goals 只在你明确要求自主收敛或已有 active goal 时使用。
- Sandbox、网络和权限按 Codex approval 模型走，不绕过。
- Durable artifacts 是跨 turn、跨 agent 的事实锚点，不是 Codex goal state。

Ordinary plans should record conceptual role, scope, tier, context strategy, order, and why; native Codex fields are derived from `skills/teamwork/SKILL.md` only when dispatching.

## Typical Flows

**Small edit**

```text
brief plan -> user approval -> execute -> focused check -> self-review
```

**Non-trivial bug or prompt/model work**

```text
research local mainline -> external calibration -> research artifact -> plan -> execute -> review
```

**Cross-agent or high-risk work**

```text
research artifact -> durable plan -> plan review -> scoped worker -> verification -> execution review
```

**Goal mode**

```text
retrieve memory -> research/plan -> review -> execute -> verify -> review -> report row -> accept / revise plan / block
```

Default budget is 3 iterations. Failed verification refreshes research and checks whether the plan was under-informed, stale, wrong-scope, or over-strict before retry; repeated no-progress stops the run.

## Artifacts

Research artifacts:

```text
docs/teamwork/research/YYYY-MM-DD-<slug>.md
```

Durable plan artifacts:

```text
docs/teamwork/plans/YYYY-MM-DD-<slug>.md
```

Final reports:

```text
docs/teamwork/reports/YYYY-MM-DD-<slug>.md
```

Research artifacts are reusable investigation memory: use full-text search over old research first, update or cite still-relevant files, and record local evidence, external sources, recommendation, dissent, and refresh triggers.

Plan artifacts are execution memos: name scope boundaries, list executable steps, define focused verification and expected results, and include worker/reviewer handoffs. Larger plans may also map requirements to evidence, risks, and subagent routing.

Reports are conclusions plus goal rolling memory. Goal mode keeps one Markdown table report per goal; ordinary tasks write reports only for non-trivial, reusable summaries.

These artifacts are ignored by default, together with `docs/superpowers/`. Force-add only when a specific artifact is intentionally part of a PR.

## Platform Notes

Codex uses native plan/subagent/goal/sandbox capabilities. It does not run the Claude Stop hook.

Claude Code uses `/teamwork:*`; `/rao:*` remains as a compatibility prefix, so `/rao:goal` still works. Claude goal state is project-local under:

```text
.claude/teamwork-goals/
```

Claude bounded goal example:

```text
/teamwork:goal 修复 pytest X，最多 3 轮，无进展就停 --max-iterations 3
/teamwork:plan docs/teamwork/plans/2026-05-14-fix-pytest-x.md
/teamwork:checkpoint --plan-review-verdict pass --execution-review-verdict pass --verification-command "pytest X" --verification-result pass --evidence-delta progress
```

Claude Stop hook continues an unfinished goal until completion, max iterations, pause/stop, blocker, or repeated no-progress. The default completion promise is `RAO_GOAL_COMPLETE`.

Automatic Claude completion requires the promise and a structured audit:

```text
<completion_audit>
<plan_artifact>docs/teamwork/plans/YYYY-MM-DD-slug.md</plan_artifact>
<plan_artifact_sha256>recorded sha256</plan_artifact_sha256>
<plan_review_verdict>pass</plan_review_verdict>
<execution_review_verdict>pass</execution_review_verdict>
<requirements_mapping>map requirements to direct evidence</requirements_mapping>
<verification_evidence>commands, artifacts, or inspected evidence</verification_evidence>
<dissent>none or preserved dissent/residual risk</dissent>
</completion_audit>
```

`/teamwork:complete` and `/rao:complete` are manual overrides, not automatically verified completion.

Cursor installs one thin rule at `.cursor/rules/teamwork.mdc` and points back to the same skill files.

## Install

```bash
./install.sh codex
./install.sh claude
./install.sh cursor /path/to/project
./install.sh all /path/to/project
```

Validate this repo:

```bash
./scripts/validate.sh
```

Behavior lives in `skills/*/SKILL.md`; platform docs summarize instead of duplicating the full skill bodies.
