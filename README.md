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
teamwork: 调研 pytest X 为什么失败，给出方案，然后写成执行计划
teamwork-execute: 按已接受计划实现，只做必要改动并运行 focused verification
teamwork-review mode: execution: 审查这个 diff 和验证证据
```

Claude 中启动有界续跑目标：

```text
/rao:goal 修复 pytest X，最多 3 轮，无进展就停 --max-iterations 3
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
| 自动路由、目标续跑 | `teamwork` |
| 调研方案、写执行计划 | `teamwork-design` |
| 执行已接受计划 | `teamwork-execute` |
| 审计划、审 diff / artifact / 验证结果 | `teamwork-review` |

`teamwork` 是 router。它按用户意图进入 research、plan、execute、review 或 goal mode。
默认优先本地文件、diff、日志、测试和 artifact；只有外部约束确实需要时才用 MCP 或
网络信息。

## Subagent Routing

Teamwork 按角色和能力层级路由 subagents，而不是写死模型 ID：`Explorer` 收集证据，
`Designer` 处理需求含糊、架构和跨模块设计，`Judge` 审计划，`Worker` 执行已接受
范围，`Reviewer` 做最终复查。`fast` 适合低风险证据和机械改动，`standard` 适合
多文件执行或中等综合，`high reasoning` 用于设计、Judge、最终 review 和安全 /
回归边界。

## Plan Artifacts

Codex 的 native plan / `update_plan` 只是可见进度状态，不是持久执行依据。

轻量改动可以使用聊天计划，但仍要有明确验证和最终 review。非小改默认写入 durable
Markdown plan artifact：

```text
docs/teamwork/plans/YYYY-MM-DD-<slug>.md
```

计划文件应覆盖目标、需求映射、已读证据、范围边界、实施步骤、验证命令、预期结果、
风险、停止条件、worker handoff 和 review handoff。

这个 Markdown artifact 是普通仓库文件，可被 Cursor、Claude Code 和 Codex 共同
编辑、执行和 review；它不是 Codex goal，也不是 Claude `.claude/teamwork-goals/`
runtime 状态。

## Platform Notes

**Codex runtime**

- 使用 native plan / `update_plan` 展示进度。
- 只有用户明确要求自主收敛或已有 active goal 时才用 native Codex goal。
- 使用 Codex subagents 承担独立 Explorer、Designer、Judge、Worker、Reviewer track。
- `codex review` 可以作为审查证据，但不能自动代表通过。

**Claude `/rao:*` runtime**

- `/rao:*` 是 Teamwork 保留的 Claude 兼容命令前缀。
- goal 状态文件在 `.claude/teamwork-goals/`。
- `Stop hook` 会在 goal 未完成且未达到最大轮数时阻止停止，并注入下一轮 continuation
  prompt。
- 默认 completion promise 是 `<promise>RAO_GOAL_COMPLETE</promise>`。

自动完成必须同时包含 promise 和结构化 audit：

```text
<completion_audit>
<requirements_mapping>map requirements to direct evidence</requirements_mapping>
<verification_evidence>commands, artifacts, or inspected evidence</verification_evidence>
<review_verdict>pass</review_verdict>
<dissent>none or preserved dissent/residual risk</dissent>
</completion_audit>
```

`review_verdict` 只能是 `pass` 或 `pass-with-notes`。`/rao:complete` 是人工 override，
会记录为 manual completion。

**Cursor**

Cursor 只安装薄规则入口，指向同一组 Teamwork skills，不复制完整 runtime。

## Repository

核心文件：

```text
skills/teamwork/SKILL.md
skills/teamwork-design/SKILL.md
skills/teamwork-execute/SKILL.md
skills/teamwork-review/SKILL.md
commands/rao/*.md
hooks/hooks.json
bin/raoctl.py
```

`./scripts/validate.sh` 会检查 skill 拓扑、frontmatter、manifest、临时安装 smoke、
Cursor rule 长度、Claude command / hook 存在性、持久计划说明和 Stop-hook
completion gate。
