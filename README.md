# Teamwork

Teamwork 是 Claude Code、Codex 和 Cursor 共用的一组 workflow skills。它不替代原生 coding agent；它给容易失控的任务加上证据、计划、执行边界、复查和自主收敛规则。

## The Problem

Coding agent 最常见的问题不是不会写代码，而是太快进入错误方向：

- 还没读文件、diff、日志或测试，就先假设原因。
- 把“看起来简单”的改动做成隐性架构变化。
- 调研、计划、实现、复查混在同一个上下文里，执行者自己宣布完成。
- 多 agent 并行时没有明确所有权，最后互相覆盖或重复工作。
- 运行中的 plan、research、goal state 被提交到 GitHub，污染仓库。

Teamwork 的目标是让 agent 慢在关键点、快在可并行的地方。

## The Solution

| Rule | What It Means |
|---|---|
| Native first | 简单、低风险、单步任务继续走 native flow。 |
| Evidence first | 重要判断先读直接证据；把证据标成 `observed`、`inferred`、`claimed`。 |
| Plan before edits | 代码修改前给出精确计划；非轻量、高影响、跨模块、用户可见或含糊变更要先 plan review / Judge。 |
| Bounded execution | Worker 只做计划内必要改动，不重新打开产品行为、架构或需求设计。 |
| Verify before done | 先跑 focused checks；共享或公开行为受影响时再扩大验证。 |
| Review before accept | 执行者不能自宣完成；轻量路径也要有清晰 review pass。 |
| Parallel with ownership | 调试、实验分析和代码逻辑分析要先拆调查轨道；独立时并行取证，主 agent 负责综合和解决分歧。 |
| Keep artifacts local | `docs/teamwork/plans/`、`docs/teamwork/research/` 和 `docs/superpowers/` 默认不进 GitHub。 |

## Skill Map

当前 active skills 只有七个：

| Skill | Owns |
|---|---|
| `using-teamwork` | 普通 coding / debugging / research / review 请求的入口判断。 |
| `teamwork` | 公共 router；定义 evidence、artifact、subagent、Codex dispatch 和 routing rules。 |
| `teamwork-research` | 取证、原因分析、方案比较、外部资料刷新和 research artifact。 |
| `teamwork-plan` | 把已选方向变成 lightweight checklist 或 durable plan。 |
| `teamwork-execute` | 按已接受计划做最小实现并运行 focused verification。 |
| `teamwork-review` | `mode: plan` 审计划；`mode: execution` 审 diff、验证证据和回归风险。 |
| `teamwork-goal` | 自主迭代到验证通过、预算耗尽或明确 blocker。 |

完整链路通常是：

```text
research -> plan -> plan review -> execute -> execution review -> accept / iterate / block
```

这不是所有任务的最低门槛。能 native 解决就 native；只有 Teamwork 能提升正确性时才升级。

## When To Escalate

| Situation | Use |
|---|---|
| 单步、明确、低风险 | native flow；必要时一个短 checklist |
| 需要读文件、日志、diff、测试或外部信息后才能判断 | `teamwork-research` |
| 多步骤、含糊、用户要求计划、错误第一步代价高 | `teamwork-plan` |
| 已有接受的计划需要执行 | `teamwork-execute` |
| 需要审计划、diff、artifact、测试结果或完成声明 | `teamwork-review` |
| 用户要求“run until it passes / keep going / iterate until done” | `teamwork-goal` |

## Install

```bash
git clone https://github.com/JinPLu/Teamwork.git
cd Teamwork
./install.sh codex
```

Other installs:

```bash
./install.sh claude
./install.sh cursor /path/to/project
./install.sh all /path/to/cursor-project
./install.sh --link codex
./install.sh --link claude
```

Validate this repo:

```bash
./scripts/validate.sh
```

## Artifacts

Durable plans use:

```text
docs/teamwork/plans/YYYY-MM-DD-<slug>.md
```

Research artifacts use:

```text
docs/teamwork/research/YYYY-MM-DD-<slug>.md
```

These are local workflow artifacts and are ignored by default, together with `docs/superpowers/`. Force-add only when a specific artifact is intentionally part of a PR.

Plan artifacts should map requirements to evidence, name scope boundaries, list exact implementation steps, define focused verification and expected results, and include worker/reviewer handoffs. They are not Codex goal state and not Claude `.claude/teamwork-goals/` runtime state.

## Subagents

Use subagents only when independent context, parallel evidence collection, isolated execution, or fresh review actually helps.

| Role | Use |
|---|---|
| Explorer | Independent evidence collection. |
| Designer | Ambiguous requirements, architecture, cross-module design. |
| Judge | Fresh-context plan review before execution. |
| Worker | Accepted implementation scope with exact file ownership. |
| Reviewer | Final diff, artifact, verification, and regression review. |

Tiers are capability labels, not fixed model IDs: `fast`, `standard`, `high reasoning`. Default fan-out is at most 3 parallel research/review agents unless the user gives a larger budget.

## Codex runtime

- `update_plan` is transient UI state, not a durable execution or review artifact.
- Native Codex goals are only for explicit autonomous convergence or an existing active goal.
- Codex subagents map Teamwork roles onto native agent types at dispatch time.
- `codex review --uncommitted`, `--base`, or `--commit` can be review evidence, never automatic approval.
- Sandbox or network blocks should use narrow escalation; do not bypass approvals.

Codex dispatch details are derived from `skills/teamwork/SKILL.md`. Ordinary plans should record conceptual role, scope, tier, context strategy, order, and why; include native Codex fields only when a non-default native override is itself part of the decision.

## Claude Runtime

Claude Code uses `/teamwork:*`; `/rao:*` is a compatibility prefix, so `/rao:goal` still works. Goal state is project-local under:

```text
.claude/teamwork-goals/
```

Start a bounded goal:

```text
/teamwork:goal 修复 pytest X，最多 3 轮，无进展就停 --max-iterations 3
/teamwork:plan docs/teamwork/plans/2026-05-14-fix-pytest-x.md
/teamwork:checkpoint --plan-review-verdict pass --execution-review-verdict pass --verification-command "pytest X" --verification-result pass --evidence-delta progress
```

Stop hook continues an unfinished goal until completion, max iterations, pause/stop, blocker, or repeated no-progress. The default completion promise is `RAO_GOAL_COMPLETE`.

Automatic completion requires both the promise and a structured audit:

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

## Cursor

Cursor installs one thin rule at `.cursor/rules/teamwork.mdc` and points back to the same skill files.

## Development

Behavior lives in `skills/*/SKILL.md`; platform docs should summarize, not duplicate full skill bodies. `scripts/validate.sh` checks skill topology, manifests, hooks, runtime smoke behavior, README constraints, and ignored local artifact policy.
