# Teamwork

[English](README.en.md)

![Teamwork workflow banner](assets/teamwork-hero.png)

Teamwork 是一个 **Codex + Cursor + Claude Code skill package**。各平台 native capabilities 是 execution substrate：Codex 侧有原生 goal、`update_plan`、`spawn_agent`；Cursor 侧有 `Task` subagents、MCP、browser 和 permissions；Claude Code 侧有 `Task` subagents（用户自定义于 `~/.claude/agents/`）、TodoWrite、MCP 和 permissions。Teamwork 只补上一层协作策略，让复杂 coding-agent 工作更可靠：证据优先、可复用 artifacts、stage-routed proactive dispatch、经过 review 的执行，以及不会过早停止的 goal iteration。

Teamwork 激活后，主 agent 默认承担 orchestrator 角色：保留简单任务的平台 native flow；对 research、plan、execute、review、goal 中的非轻量工作，主动评估是否分发 subagents，而不是等待用户或 plan 授权。

## 核心优势

| 优势 | Teamwork 增加什么 |
|---|---|
| 证据优先 | 关键结论必须来自源码、diff、日志、测试、artifacts 或 primary external sources。文件名、README、注释、历史摘要和 `latest` 标签都先视为 claim；`implement/fix` 在 root/source/API/failure/evidence/risk 不清时先 research。 |
| 更好的 platform goals | 不清晰的自主任务先生成聊天窗口里的 `Goal Proposal`。用户确认后，Codex 用 Goal Text 调用 `create_goal`；Cursor 和 Claude Code 用 rolling report 作 durable goal state 并在 chat 中自驱动 controller loop。失败尝试会回到 research + plan adequacy，而不是过早 block。 |
| Artifact memory | `research/`、`plans/`、`reports/` 保存可复用证据、执行 memo、滚动尝试、验证、review 和 routing 决策，避免重复调查或把聊天上下文撑大。 |
| 检索头 | Durable artifacts 以 type、status、updated date、search keys、abstract 和 linked artifacts 开头，方便未来 agent 先定位正确记忆，再做全文搜索。 |
| Stage-routed dispatch | Teamwork 激活后采用 subagent-first orchestration。Research / plan / execute / review / goal 阶段会对非轻量工作主动评估 Explorer、Designer、Judge、Worker 或 Reviewer 分发。Codex 用 `spawn_agent`；Cursor 和 Claude Code 用 `Task`。若 Codex 上 `spawn_agent` 未激活但 `tool_search` 可用，必须先发现工具再说不可用。非轻量验收需要 fresh Reviewer，self-review 不算 acceptance。 |

## Skill Map

`using-teamwork` 是自动入口和 lean router。Stage skills 保持轻量，只加载当前阶段需要的 reference；subagent 细节按 progressive disclosure 拆分到 focused references，而不是集中在一个大 `subagent-routing` reference 中。

| 用户意图 | Skill | 输出 |
|---|---|---|
| 初始化或瘦身项目 agent 规则 | `teamwork-init` | 项目规则分层、MCP/CodeGraph 边界、appendix 和 artifact 接入方案 |
| 调查原因、比较方案、刷新过期假设 | `teamwork-research` | 直接证据、外部校准，以及必要时的 reusable research artifact |
| 规划或准备非平凡改动 | `teamwork-plan` | 轻量 checklist 或 durable execution memo |
| 执行已接受、批准、继续或恢复的计划 | `teamwork-execute` | 最小范围改动和 focused verification |
| 审查计划、diff、artifact 或结果 | `teamwork-review` | 基于证据的 verdict，保留 dissent 和 required fixes |
| 更新版本、发布元数据或 skill 拓扑 | `teamwork-update` | 同步 `VERSION`、manifest、文档、安装和验证 |
| 持续迭代直到达到可验证目标 | `teamwork-goal` | Goal Proposal、native goal handoff、iteration loop，以及必要时的 rolling report |

Subagent references 按职责拆分：`dispatch-policy` 说明何时分发、cap/economics、Codex/Cursor dispatch field，以及 role-specific model class；`subagent-prompt-contract` 说明 prompt 结构和 `Native Fields`；`subagent-packets` 说明 Worker / Reviewer handoff packet。Plan 里的 `Dispatch Guidance:` 是建议；实际 dispatch 仍由当前 stage 按 stage-routed proactive dispatch 决定。

## Platform Native Policy Map

| 平台能力 | Teamwork 策略 |
|---|---|
| Codex goal | 自主目标和生命周期的 source of truth。Teamwork 在 `create_goal` 前设计 goal、证据、scope、retry policy 和 acceptance checks。 |
| Cursor goal | 无原生 goal state 时，goal-mode 用 chat iteration + durable report；不强制 `create_goal`。 |
| Claude Code goal | 同 Cursor：无原生 goal state；goal-mode 用 chat iteration + rolling report。 |
| `update_plan` / TodoWrite | 只表示可见进度。它不是 durable execution spec、review target 或 completion proof。 |
| Subagents | Stage-routed proactive dispatch。Teamwork 激活后主 agent 是 orchestrator；research、plan、execute、review、goal 的非轻量工作主动评估并分发 subagents。Codex 用 `spawn_agent`；Cursor 和 Claude Code 用 `Task`（Claude Code 的 `subagent_type` 指向 `~/.claude/agents/` 里的用户自定义 agent，未配置时回落到 `general-purpose`）。Plan 中的 `Dispatch Guidance:` 或 `Subagent Routing` 是建议，不是唯一授权。若 Codex 上 `spawn_agent` 不在 active tools 里但 `tool_search` 可用，必须先发现工具。跳过 required dispatch 必须写 `Dispatch Exception:`。Explorer/Reviewer 默认 3；Worker 无固定 cap。非轻量 review 只有 subagent discovery 失败或用户禁用时才能跳过 fresh Reviewer，且必须标 `unreviewed`。Model policy 优先少而强：Codex bounded subagents 默认显式 pin Role Profile model；Explorer 默认 `balanced`，Judge/Reviewer 默认 `frontier`，Worker 默认 `coding` 并按风险升级 `frontier`；`cheap-fast` 只用于显式低延迟/额度压力的轻量只读任务。 |
| Review | 平台 review 输出可以作为证据，但完成判断仍必须映射到 requirements、diff、tests、artifacts 和 acceptance criteria。 |
| Sandbox/permissions | 使用各平台原生 approval 和 sandbox/permission model。Teamwork 只要求 boundaries 和 risks 明确。 |
| Automations/heartbeat | Codex 使用原生 automation 或 thread heartbeat。不要把 schedule 写进 Teamwork artifacts。 |
| MCP/plugins | 优先使用平台原生 tools 和 connectors。若 source limits 影响决策，需要记录限制。 |
| Project instructions | `teamwork-init` 负责初始化或瘦身 `AGENTS.md`、`CODEX.md`、`CURSOR.md`、`CLAUDE.md`，把可复用流程迁移到 Teamwork，把项目事实留在项目内。 |

包版本以 `VERSION` 为 source of truth，并且必须和 `.codex-plugin/plugin.json`、`.claude-plugin/plugin.json` 中的 `version` 保持一致。版本、发布元数据或 skill surface 更新走 `teamwork-update`。

## Goal Proposal

对不清晰的自主任务，Teamwork 会先在聊天里返回这个结构，再进行 platform goal handoff：

```text
Goal Proposal:
- Objective: <one-sentence target>
- Done Evidence: <commands, files, artifacts, or observable acceptance checks>
- Scope: <allowed files, behavior, or systems>
- Non-goals: <explicit exclusions>
- Constraints: <permissions, compatibility, cost/time, sacred boundaries>
- Iteration Budget: <default 3 if unspecified, or user-specified>
- Retry Policy: <failed verification returns to research + plan adequacy>
- Artifacts: <none | suggested research/plan/report paths and why>
- Subagent Routing: <suggested tracks to split, or why main-agent continuity is better>
- Goal Text: <concise target for platform goal handoff>
```

这个 proposal 是人工 review gate。Codex 将 Goal Text 写入 `create_goal`；Cursor 将 Goal Text 写入 rolling report 的 Abstract 并启动 controller loop。

## Artifacts

Artifacts 是证据记忆，不替代 platform goal surface。只有当它们能减少重复工作，或需要锚定 cross-turn、cross-agent、high-risk、ambiguous、public/shared、explicitly planned、goal-mode 工作时才创建。

```text
docs/teamwork/research/YYYY-MM-DD-<slug>.md
docs/teamwork/plans/YYYY-MM-DD-<slug>.md
docs/teamwork/reports/YYYY-MM-DD-<slug>.md
```

| 目录 | 角色 | Review 问题 |
|---|---|---|
| `research/` | 可复用调查和外部校准 | 读了什么证据？哪些 finding 是 observed / inferred / claimed？ |
| `plans/` | 执行 memo 和 review source of truth | goal、scope、steps、verification、risks、handoffs、routing 建议是否清楚？ |
| `reports/` | Goal rolling memory 和 durable conclusions | 尝试了什么、验证了什么、审查了什么、复用了什么、实际如何 dispatch？ |

每个 durable artifact 都以 `Artifact Type`、`Status`、`Last Updated`、`Search Keys`、`Abstract` 和 `Linked Artifacts` 开头。`Abstract` 只帮助检索；完成判断仍然需要 commands、diffs、tests、artifacts 或 inspected behavior 等直接证据。

这些目录默认被 gitignore，除非用户明确要求发布某个具体 artifact。

## 安装

三端一次装好（推荐首次或升级后执行）：

```bash
./install.sh all
./install.sh codex-agents
./install.sh claude-agents
```

按平台单独安装：

```bash
./install.sh codex    # 默认目标
./install.sh cursor
./install.sh claude
./install.sh codex-agents
```

在**当前仓库**启用项目级 Cursor skills、Codex agents 与 Claude agents（写入已 gitignore 的 `.cursor/skills/`、`.codex/agents/`、`.claude/agents/`）：

```bash
./install.sh project
```

Claude Code 的 Teamwork 子代理模板（`explore`、`worker`、`code-reviewer`）：

```bash
./install.sh claude-agents   # ~/.claude/agents/
```

本地开发时用 symlink 跟踪本仓库：

```bash
./install.sh --link all
./install.sh --link project
```

**Cursor 注意**：会话应优先使用 `~/.cursor/skills/` 或项目 `.cursor/skills/`。若同时存在旧的 `~/.claude/skills/using-teamwork` 或已退役的 `teamwork` skill，可能抢路由；用 `./install.sh all` 刷新并删除退役副本。

验证仓库：

```bash
./scripts/validate.sh
```

行为定义在 `skills/*/SKILL.md`；`README.md`、`CODEX.md`、`CURSOR.md` 和 `CLAUDE.md` 只是简洁的运行时说明。
