# Teamwork

Teamwork 是一个面向 Claude Code、Codex 和 Cursor 的轻量 agent 协作工作流。
它把“一个 agent 从头做到尾”改成“主 agent 统筹，subagents 分工”：主 agent
负责拆分、调度、综合和验收；subagents 负责独立调研、范围明确的执行、fresh-context
复查和证据回传。

它主要解决四类问题：

- 上下文过长：把独立调研、执行和复查分给 subagents，主 agent 只保留结论和证据。
- 局部自证：执行者不能自宣完成，必须经过独立 review 和验证证据。
- 叙述误导：文件名、版本号、注释、README、历史说明都只是 claim，需要源码、diff、
  测试、日志或 artifact 交叉验证。
- 自动循环失控：goal mode 有预算、Stop hook、completion audit 和明确阻塞条件。

## 核心优势

- Subagent-first：调研、计划、执行、复查、验收都围绕合理使用 subagents 设计。
- Evidence-first：重要结论区分 `observed`、`inferred`、`claimed`。
- Review-gated：完成声明必须映射需求、验证证据、review verdict 和 dissent。
- 轻量：不引入 model registry、pricing cache、dispatch 平台或 thread ledger。
- 兼容：Codex 用原生 plan / goal / subagent；Claude 保留 `/rao:*` runtime。

## 工作流

```text
research -> plan -> plan review -> execute -> execution review -> accept / iterate / block
```

| 场景 | 使用 |
|---|---|
| 自动路由、目标续跑 | `teamwork` |
| 调研方案、写执行计划 | `teamwork-design` |
| 执行已接受计划 | `teamwork-execute` |
| 审计划、审 diff / artifact / 验证结果 | `teamwork-review` |

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

## 安装

普通用户从 GitHub clone 后直接复制安装：

```bash
git clone https://github.com/JinPLu/Teamwork.git
cd Teamwork
```

```bash
./install.sh claude
./install.sh codex
./install.sh cursor /path/to/project
./install.sh all /path/to/cursor-project
```

默认是复制安装，安装后的 skill 不依赖这个仓库路径。开发本仓库时如果希望本地修改
立即反映到已安装 skill，可以显式使用 symlink 模式：

```bash
./install.sh --link codex
./install.sh --link claude
```

安装脚本会安装四个 skill，并清理旧 `run-analyze-*` 安装。

## Codex runtime

Codex 使用同一组 skill，但不使用 Claude 的 Markdown goal 后端。需要可见计划时用
原生 plan；只有用户明确要求自主收敛或已有 active goal 时才用原生 Codex goal。
subagents 用于独立 research、judge、worker、review track；`codex review` 可以作为
审查证据，但不能自动代表通过。

## Claude `/rao:*` runtime

`/rao:*` 是 Teamwork 保留的 Claude 兼容命令前缀。状态文件在：

```text
.claude/teamwork-goals/
```

`Stop hook` 会在 goal 未完成且未达到最大轮数时阻止停止，并注入下一轮 continuation
prompt。默认 completion promise 是：

```text
<promise>RAO_GOAL_COMPLETE</promise>
```

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

## 验证

```bash
./scripts/validate.sh
```

验证覆盖 skill 拓扑、frontmatter、manifest、临时安装 smoke、Cursor rule 长度、
Claude command / hook 存在性，以及 Stop-hook completion gate。
