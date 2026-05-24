# Teamwork

[English](README.en.md)

![Teamwork workflow banner](assets/teamwork-hero.png)

Teamwork 是一个 **Codex-only skill package**。Codex native capabilities are the execution substrate：原生 goal、`update_plan`、subagents、review、sandbox approvals、automations、MCP 和 plugins 仍然负责实际执行。Teamwork 只补上一层协作策略，让复杂 coding-agent 工作更可靠：证据优先、可复用 artifacts、明确的 subagent routing、经过 review 的执行，以及不会过早停止的 goal iteration。

简单任务继续走 Codex native flow。只有当证据、规划、审查、委派或自主收敛能明显提升正确性时，才启用 Teamwork。

## 核心优势

| 优势 | Teamwork 增加什么 |
|---|---|
| 证据优先 | 关键结论必须来自源码、diff、日志、测试、artifacts 或 primary external sources。文件名、README、注释、历史摘要和 `latest` 标签都先视为 claim，直到被直接证据确认。 |
| 更好的原生 goals | 不清晰的自主任务先生成聊天窗口里的 `Goal Proposal`。用户确认后，用其中的 `Native Codex Goal Text` 创建 Codex 原生 goal。失败尝试会回到 research + plan adequacy，而不是过早 block。 |
| Artifact memory | `research/`、`plans/`、`reports/` 保存可复用证据、执行 memo、滚动尝试、验证、review 和 routing 决策，避免重复调查或把聊天上下文撑大。 |
| 检索头 | Durable artifacts 以 type、status、updated date、search keys、abstract 和 linked artifacts 开头，方便未来 agent 先定位正确记忆，再做全文搜索。 |
| Subagent routing | 轻量计划可用 `Dispatch:`，durable plans 用 `Subagent Routing`。Explorer/Reviewer 默认最多 3 个；Worker 按 ownership、integration cost 和 verification 扩展。 |

## Skill Map

`using-teamwork` 是自动入口和 router。

| 用户意图 | Skill | 输出 |
|---|---|---|
| 调查原因、比较方案、刷新过期假设 | `teamwork-research` | 直接证据、外部校准，以及必要时的 reusable research artifact |
| 规划或准备非平凡改动 | `teamwork-plan` | 轻量 checklist 或 durable execution memo |
| 执行已接受、批准、继续或恢复的计划 | `teamwork-execute` | 最小范围改动和 focused verification |
| 审查计划、diff、artifact 或结果 | `teamwork-review` | 基于证据的 verdict，保留 dissent 和 required fixes |
| 更新版本、发布元数据或 skill 拓扑 | `teamwork-update` | 同步 `VERSION`、manifest、文档、安装和验证 |
| 持续迭代直到达到可验证目标 | `teamwork-goal` | Goal Proposal、native goal handoff、iteration loop，以及必要时的 rolling report |

## Codex Native Policy Map

| Codex 能力 | Teamwork 策略 |
|---|---|
| Native goal | 自主目标和生命周期的 source of truth。Teamwork 在 `create_goal` 前设计 goal、证据、scope、retry policy 和 acceptance checks。 |
| `update_plan` | 只表示可见进度。它不是 durable execution spec、review target 或 completion proof。 |
| Subagents | 由用户请求、已接受的 Goal Proposal、lightweight `Dispatch:` 或 durable `Subagent Routing` 授权。Explorer/Reviewer 默认 3；Worker 无固定 cap，但 >3 需说明 ownership、integration 和 verification。 |
| Review | Codex review 输出可以作为证据，但完成判断仍必须映射到 requirements、diff、tests、artifacts 和 acceptance criteria。 |
| Sandbox/permissions | 使用 Codex 原生 approval 和 sandbox model。Teamwork 只要求 boundaries 和 risks 明确。 |
| Automations/heartbeat | 使用 Codex 原生 automation 或 thread heartbeat 处理 recurring checks 或 later continuation。不要把 schedule 写进 Teamwork artifacts。 |
| MCP/plugins | 优先使用 Codex 原生 tools 和 connectors。若 source limits 影响决策，需要记录限制。 |

包版本以 `VERSION` 为 source of truth，并且必须和 `.codex-plugin/plugin.json` 中的 `version` 保持一致。版本、发布元数据或 skill surface 更新走 `teamwork-update`。

## Goal Proposal

对不清晰的自主任务，Teamwork 会先在聊天里返回这个结构，再创建 Codex 原生 goal：

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
- Subagent Routing: <tracks to split, or why main-agent continuity is better>
- Native Codex Goal Text: <concise text prepared for create_goal>
```

这个 proposal 是人工 review gate。被批准的 `Native Codex Goal Text` 才会写入 Codex 原生 goal state。

## Artifacts

Artifacts 是证据记忆，不替代 Codex 原生 goal state。只有当它们能减少重复工作，或需要锚定 cross-turn、cross-agent、high-risk、ambiguous、public/shared、explicitly planned、goal-mode 工作时才创建。

```text
docs/teamwork/research/YYYY-MM-DD-<slug>.md
docs/teamwork/plans/YYYY-MM-DD-<slug>.md
docs/teamwork/reports/YYYY-MM-DD-<slug>.md
```

| 目录 | 角色 | Review 问题 |
|---|---|---|
| `research/` | 可复用调查和外部校准 | 读了什么证据？哪些 finding 是 observed / inferred / claimed？ |
| `plans/` | 执行 memo 和 review source of truth | goal、scope、steps、verification、risks、handoffs、routing 是否清楚？ |
| `reports/` | Goal rolling memory 和 durable conclusions | 尝试了什么、验证了什么、审查了什么、复用了什么、如何 routing？ |

每个 durable artifact 都以 `Artifact Type`、`Status`、`Last Updated`、`Search Keys`、`Abstract` 和 `Linked Artifacts` 开头。`Abstract` 只帮助检索；完成判断仍然需要 commands、diffs、tests、artifacts 或 inspected behavior 等直接证据。

这些目录默认被 gitignore，除非用户明确要求发布某个具体 artifact。

## 安装

```bash
./install.sh
```

显式写法等价：

```bash
./install.sh codex
```

本地开发时使用 symlink：

```bash
./install.sh --link
```

验证仓库：

```bash
./scripts/validate.sh
```

行为定义在 `skills/*/SKILL.md`；`README.md` 和 `CODEX.md` 只是简洁的运行时说明。
