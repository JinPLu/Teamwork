# Teamwork

Teamwork 是一个面向 Claude Code、Codex 和 Cursor 的轻量 agent 协作工作流。
它把一次性长上下文执行拆成清晰阶段：调研、计划、执行、复查和验收。

核心原则：

- 主 agent 负责范围、调度、综合、验证和最终判断。
- subagents 负责独立调研、明确范围的执行、fresh-context review 和证据回传。
- 重要结论必须区分 `observed`、`inferred`、`claimed`。
- 执行者不能自宣完成；完成前必须有验证和 review。

## Quick Start

安装：

```bash
git clone https://github.com/JinPLu/Teamwork.git
cd Teamwork
./install.sh codex
```

其他平台：

```bash
./install.sh claude
./install.sh cursor /path/to/project
./install.sh all /path/to/cursor-project
```

开发本仓库时如果希望已安装 skill 直接跟随本地修改，可用 symlink 模式：

```bash
./install.sh --link codex
./install.sh --link claude
```

常用调用：

```text
using-teamwork: 自动判断普通 Codex coding / research / review 请求是否需要 Teamwork
teamwork: 调研 pytest X 为什么失败，给出方案，然后写成执行计划
teamwork-goal: 自主续跑到验证通过、预算耗尽或明确 blocker
teamwork-execute: 按已接受计划实现，只做必要改动并运行 focused verification
teamwork-review mode: execution: 审查这个 diff 和验证证据
```

Claude 中启动有界续跑目标：

```text
/teamwork:goal 修复 pytest X，最多 3 轮，无进展就停 --max-iterations 3
/teamwork:plan docs/teamwork/plans/2026-05-14-fix-pytest-x.md
```

验证仓库：

```bash
./scripts/validate.sh
```

## Workflow

```text
research -> plan -> plan review -> execute -> execution review -> accept / iterate / block
```

| 场景 | Skill |
|---|---|
| 普通 Codex coding / research / review 请求的自动入口 | `using-teamwork` |
| 自动路由 | `teamwork` |
| 目标续跑、自主收敛 | `teamwork-goal` |
| 调研方案、写执行计划 | `teamwork-design` |
| 执行已接受计划 | `teamwork-execute` |
| 审计划、审 diff / artifact / 验证结果 | `teamwork-review` |

`using-teamwork` 是轻量入口，用于让 Codex 在普通 coding / research / review 请求开始时先做 Teamwork 路由判断。`teamwork` 是 router。它按用户意图进入 research、plan、execute、review，目标续跑路由到 `teamwork-goal`。
默认优先本地文件、diff、日志、测试和 artifact；只有外部约束确实需要时才用 MCP 或
网络信息。

## Subagent Routing

Teamwork 按角色和能力层级路由 subagents，而不是写死模型 ID：`Explorer` 收集证据，
`Designer` 处理需求含糊、架构和跨模块设计，`Judge` 审计划，`Worker` 执行已接受
范围，`Reviewer` 做最终复查。`fast` 适合低风险证据和机械改动，`standard` 适合
多文件执行或中等综合，`high reasoning` 用于设计、Judge、最终 review 和安全 /
回归边界。

Codex dispatch details are derived from the router mapping in
`skills/teamwork/SKILL.md`. Ordinary plans should record conceptual role, scope,
tier, context strategy, order, and why; include native Codex fields only when a
non-default native override is itself part of the decision.

## Plan Artifacts

Codex 的 native plan / `update_plan` 只是可见进度状态，不是持久执行依据。

所有 `teamwork-design mode: plan` 都必须写入 durable Markdown plan artifact，
包括轻量改动、低风险改动和单文件改动：

```text
docs/teamwork/plans/YYYY-MM-DD-<slug>.md
```

计划文件应覆盖目标、需求映射、已读证据、范围边界、实施步骤、验证命令、预期结果、
风险、停止条件、worker handoff 和 review handoff。

这个 Markdown artifact 是普通仓库文件，可被 Cursor、Claude Code 和 Codex 共同
编辑、执行和 review；它不是 Codex goal，也不是 Claude `.claude/teamwork-goals/`
runtime 状态。

Goal 续跑必须记录当前计划锚点。Claude runtime 使用 `/teamwork:plan <path>`
把 `active_plan_artifact` 和 `active_plan_artifact_sha256` 写入
`.claude/teamwork-goals/`；后续 continuation、Worker、Reviewer 和 completion
audit 都对照这同一个 Markdown plan artifact。

## Platform Notes

**Codex runtime**

- 使用 native plan / `update_plan` 展示进度。
- 只有用户明确要求自主收敛或已有 active goal 时才用 native Codex goal。
- 使用 Codex subagents 承担独立 Explorer、Designer、Judge、Worker、Reviewer track。
- `codex review` 可以作为审查证据，但不能自动代表通过。

**Claude `/teamwork:*` runtime**

- `/teamwork:*` 是 Teamwork 的主 Claude 命令前缀。
- `/rao:*` 保留为兼容命令前缀，例如 `/rao:goal` 等价于
  `/teamwork:goal`。
- goal 状态文件在 `.claude/teamwork-goals/`。
- `Stop hook` 会在 goal 未完成且未达到最大轮数时阻止停止，并注入下一轮 continuation
  prompt。
- `/teamwork:checkpoint` 记录 plan review、execution review、verification
  result 和 evidence delta。自动完成必须使用当前 plan SHA 的 checkpoint。
- 连续两次 `--evidence-delta no-progress` 会停止 goal。
- 默认 completion promise 是 `<promise>RAO_GOAL_COMPLETE</promise>`。

自动完成必须同时包含 promise 和结构化 audit：

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

`plan_review_verdict` 和 `execution_review_verdict` 只能是 `pass` 或
`pass-with-notes`，`plan_artifact` 和 `plan_artifact_sha256` 必须匹配 runtime
记录的 active plan。`/teamwork:complete` 和 `/rao:complete` 是人工 override，
status 会显示 manual completion is not automatically verified。

**Cursor**

Cursor 只安装薄规则入口，指向同一组 Teamwork skills，不复制完整 runtime。

## Repository

核心文件：

```text
skills/using-teamwork/SKILL.md
skills/teamwork/SKILL.md
skills/teamwork-goal/SKILL.md
skills/teamwork-design/SKILL.md
skills/teamwork-execute/SKILL.md
skills/teamwork-review/SKILL.md
commands/teamwork/*.md
commands/rao/*.md
hooks/hooks.json
bin/raoctl.py
```

`./scripts/validate.sh` 会检查 skill 拓扑、frontmatter、manifest、临时安装 smoke、
Cursor rule 长度、Claude command / hook 存在性、持久计划说明和 Stop-hook
completion gate。
