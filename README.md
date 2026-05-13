# Teamwork

一个面向 Claude Code、Codex 和 Cursor 的轻量 agent 协作工作流。它让主 agent
负责拆分、调度和验收，让 subagents 负责并行调研、执行、复查和证据回传，避免
上下文过长、局部自证和草率宣称完成。

## 优势

- 协作优先：调研、计划、执行、复查、验收都围绕合理使用 subagents 设计。
- 证据优先：subagent 返回 condensed evidence、confidence、dissent，而不是长日志。
- 角色分离：main agent 负责综合判断，worker/reviewer 不能自宣完成。
- 轻量可装：不引入 model registry、pricing cache、dispatch 平台或 thread ledger。
- 运行时适配：Codex 使用原生 goal / subagent；Claude 可用 `/rao:*` 和 Stop hook 续跑。

## 拓扑

```text
skills/teamwork/SKILL.md  # router + mode: goal
skills/teamwork-design/SKILL.md    # mode: research | mode: plan
skills/teamwork-execute/SKILL.md   # accepted-plan execution
skills/teamwork-review/SKILL.md    # mode: plan | mode: execution
```

`teamwork` 会按意图路由：

| 你要做什么 | 路由 |
|---|---|
| 调研方案、原因或取舍 | `teamwork-design` with `mode: research` |
| 把选定方向写成执行计划 | `teamwork-design` with `mode: plan` |
| 执行已接受计划 | `teamwork-execute` |
| 审计划 | `teamwork-review` with `mode: plan` |
| 审 diff、产物或执行结果 | `teamwork-review` with `mode: execution` |
| 迭代到验证通过或明确阻塞 | `teamwork` with `mode: goal` |

## 安装

Claude skills:

```bash
./install.sh claude
```

Codex skills:

```bash
./install.sh codex
```

Cursor project rule:

```bash
./install.sh cursor /path/to/project
```

全部入口：

```bash
./install.sh all /path/to/cursor-project
```

安装脚本会安装当前四个 skill，并清理指回本仓库的旧版 symlink。

## 用法

让 router 自动选择阶段：

```text
teamwork: 调研 pytest X 为什么失败，给出方案，然后写成执行计划
```

执行已接受计划：

```text
teamwork-execute: 按已接受计划实现，只做必要改动并运行 focused verification
```

审查执行结果：

```text
teamwork-review mode: execution: 审查这个 diff 和验证证据
```

Claude 中启动有界续跑目标：

```text
/rao:goal 修复 pytest X，最多 3 轮，无进展就停 --max-iterations 3
```

## Codex runtime

Codex 使用同一组四个 skill。主 agent 负责拆分任务、调度 subagent、综合冲突和
最终验收；subagent 用于独立 research、judge、worker、review track。需要可见计划
时用原生 plan；只有用户明确要求自主收敛或已有 active goal 时才用原生 Codex goal。
真实 git diff 可把 `codex review` 作为审查证据，但不能当作自动通过。

不要把 Claude 的 `.claude/teamwork-goals/` Markdown goal runtime 当作
Codex 后端。

## Claude `/rao:*` runtime

Claude Code plugin 可管理项目本地 goal。`/rao:*` 是 Teamwork 保留的兼容命令前缀：

```text
/rao:goal <objective> [--max-iterations N] [--completion-promise TEXT]
/rao:status
/rao:pause
/rao:resume
/rao:stop
/rao:complete
/rao:clear
/rao:note <note>
```

状态文件位置：

```text
.claude/teamwork-goals/
```

`Stop hook` 会在 goal 未完成且未达到轮数上限时阻止停止，并把 continuation prompt
注入下一轮。默认 completion promise 是：

```text
<promise>RAO_GOAL_COMPLETE</promise>
```

自动完成必须同时包含精确 promise 和结构化 completion audit：

```text
<completion_audit>
<requirements_mapping>map each requirement to direct evidence</requirements_mapping>
<verification_evidence>commands, artifacts, or inspected evidence</verification_evidence>
<review_verdict>pass</review_verdict>
<dissent>none or preserved dissent/residual risk</dissent>
</completion_audit>
```

`review_verdict` 只能是 `pass` 或 `pass-with-notes`。只有 promise、没有 audit 时不会
自动 complete，除非已经达到最大轮数。`/rao:complete` 是人工 override，并会记录为
manual completion。

## 验证

```bash
./scripts/validate.sh
```

验证内容包括 skill 拓扑、frontmatter、manifest、临时安装 smoke、Cursor rule 长度、
Claude command / hook 存在性、Stop-hook completion gate，以及 thin-doc 必要引用。

## 发布

```bash
git remote add origin https://github.com/JinPLu/Teamwork.git
git push -u origin main
```

GitHub CLI:

```bash
gh repo create JinPLu/Teamwork --public --source=. --remote=origin --push
```
