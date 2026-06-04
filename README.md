# Teamwork

[English](README.en.md)

Teamwork 是一个 **Codex-first 的 Codex + Cursor + Claude Code skill package**：
给 coding agents 加一层可验证的协作协议。各平台的 native capabilities 仍然
负责编辑、shell、MCP、权限、浏览器和验证；Teamwork 负责分阶段、派角色、
收证据、做 fresh review、保存可复用记忆，并把目标推进到可验证结果或真实
blocker。

![Teamwork workflow banner](assets/teamwork-hero.png)

## 为什么用 Teamwork

- 非轻量任务不再靠单个 agent 猜到底：Teamwork 会按阶段拆成 evidence、design、
  plan、execute、review、goal。
- 重要结论要落到源码、diff、日志、测试、artifact 或 primary source；名字和
  summary 只是 claim。
- Subagents 是有边界的 packet producer：返回一次结果，由主 agent 负责整合、
  关闭 dispatch track、验证和最终交付。
- Goal loop 会持续迭代到目标达成、预算耗尽、无进展阈值触发，或遇到真实 blocker。
- Durable artifacts 和可选 index/current memory 减少跨回合重复调查。

## 核心能力

| 能力 | Teamwork 做什么 |
|---|---|
| Evidence first | 把关键 claim 映射到直接证据，区分 `observed` / `inferred` / `claimed`。 |
| Stage router | `using-teamwork` 自动分流 `teamwork-init`、research、plan、execute、review、update、goal。 |
| Role workflow | Explorer 查证据，Designer 做取舍，Judge 审计划，Worker 执行切片，Reviewer fresh review。 |
| Proactive dispatch | 授权后，对非轻量且独立的工作默认派发角色；跳过需要 `Dispatch Exception`。 |
| Packet contracts | 每个角色交付固定 packet，记录 scope、证据、验证、风险、closure。 |
| Goal convergence | Codex 用 native goal 和 Goal Text；Cursor/Claude Code 用 rolling report。 |
| Artifact memory | research / plans / reports 保存可复用证据、计划、结论和失败尝试。 |
| Validation | `./scripts/validate.sh` 锁定 skill topology、manifests、packet 字段、模板和文档契约。 |

## 工作流与角色

常见路径：

```text
research -> design/plan -> execute -> verify -> review -> report or goal update
```

| 角色 | 职责 | 输出 |
|---|---|---|
| Explorer | 查证据、刷新假设、做 web/deep research 或 source audit | Evidence packet |
| Designer | 比较方案、明确约束和成功标准、给出推荐方向 | Decision packet |
| Judge | 执行前审计划是否有证据、边界、guardrails 和验收缺口 | `accept` / `revise` / `blocked` |
| Worker | 在已接受范围内实现，记录 TDD、root cause 和验证证据 | Completion packet |
| Reviewer | fresh-context 审查 diff、测试、artifact、PR/CI 证据 | Verdict packet |

Deep Judge / Deep Reviewer 只是高风险复查档位，用于 failed goal、security、
destructive risk、public contract 或 release acceptance。

## 适合 / 不适合

适合：

- 需要把调查、规划、执行、验证、review 串起来的 coding-agent 工作。
- 需要 Codex subagents 主动分担探索、实现、复查、调研，而不是用户每步手推。
- 需要跨回合保存证据、计划、结果或失败尝试的任务。
- 需要持续迭代直到可验证目标达成的目标型工作。

不适合：一句话事实、很小的明显编辑、敏感/破坏性操作、强耦合临界路径，或
subagent 上下文成本高于收益的任务。

## 安装

Codex-first 默认安装：

```bash
./install.sh              # 等同于 ./install.sh codex
./install.sh codex --profile cost-first
```

Adapter 和全平台安装：

```bash
./install.sh cursor
./install.sh claude          # 仅 Claude Code skills
./install.sh claude-agents   # 仅 Claude Code agents
./install.sh all             # 三端 skills + Codex/Claude agents
```

项目级安装写入已 gitignore 的 `.cursor/skills/`、`.codex/agents/`、
`.claude/agents/`：

```bash
./install.sh project
```

本地开发使用 symlink：

```bash
./install.sh --link codex
./install.sh --link all
./install.sh --link project
```

Codex 安装默认 `performance-first`。它生成角色优化的 Codex agents；`cost-first`
只下调常规 Explorer / Designer / Worker，高风险 Judge / Reviewer 仍保留强模型档位。

## 平台定位

Codex 是 reference runtime：native goals 是自治控制面，`teamwork_*` custom
agents 是非轻量工作的主要协作网络。`./install.sh codex` 默认写入全局
`~/.codex/AGENTS.md` standing authorization；安装后，用户不需要每次重复
"use subagents"。未安装或项目 opt-out 时，Codex 仍需要用户 prompt 或已加载
全局/项目规则授权后才会调用 `spawn_agent`。

Cursor 和 Claude Code 是 adapter：复用同一套 Teamwork 协议，但继续使用各自
native capabilities。Cursor 侧使用 Task subagents；Claude Code skills 由
`./install.sh claude` 安装，`explore`、`worker`、`code-reviewer` agents 由
`./install.sh claude-agents`、`all` 或 `project` 安装，并用 rolling report 承载
goal mode。

## 记忆与版本

Teamwork artifacts：

```text
docs/teamwork/research/YYYY-MM-DD-<slug>.md
docs/teamwork/plans/YYYY-MM-DD-<slug>.md
docs/teamwork/reports/YYYY-MM-DD-<slug>.md
```

`VERSION` 是包版本 source of truth，必须和 `.codex-plugin/plugin.json`、
`.claude-plugin/plugin.json` 保持一致；版本、manifest、release surface 更新走
`teamwork-update`。

## 深入阅读

- [CODEX.md](CODEX.md)：Codex runtime profile、Goal Text、custom-agent 映射。
- [CURSOR.md](CURSOR.md)：Cursor adapter。
- [CLAUDE.md](CLAUDE.md)：Claude Code adapter。
- `skills/*/SKILL.md`：阶段 skill 行为定义。
- `skills/using-teamwork/references/`：dispatch、packet、artifact、review、goal 细节。

验证仓库：

```bash
./scripts/validate.sh
```
