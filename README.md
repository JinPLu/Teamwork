# Teamwork

[English](README.en.md)

**把 Codex 的 subagents 变成有分工、有记忆、有证据纪律、有验收闭环的工程团队。**

Teamwork 是一个 **Codex-first 的 Codex + Cursor + Claude Code skill package**。
它不替代 Codex、Cursor 或 Claude Code 的编辑、shell、MCP、浏览器、权限和验证能力；
这些 `native capabilities` 仍然是执行底座。Teamwork 做四件事：

1. 把非轻量任务 fan out 给定制角色 subagents，让复杂任务更经济、更高效、质量更稳。
2. 用调研和证据优先的规则提醒模型：别太自信，也别静默回退。
3. 维护讨论 / 调研、计划和报告记忆，避免长期任务遗忘，并强化 goal 执行能力。
4. 用验证、fresh review 和失败复盘形成验收闭环，不让“完成”只停留在模型自述。

![Teamwork workflow banner](assets/teamwork-hero.png)

## 核心价值

### 1. Fan out 角色化 subagents：更省、更快、更稳

普通多 agent 协作容易变成“多开几个聊天窗口”。Teamwork 做的是有边界的 fan out：
主 agent 先判断任务是否真的值得拆分，再把独立调研、方案、实现、复查轨道分发给有职责的工程角色：

- `Explorer` 查证据和外部约束，用有预算的 packet 回传；source census、长矩阵和引用台账进 artifact，不把原始上下文塞回主线程。
- `Designer` 做方案取舍，明确边界、成功标准和放弃的选项。
- `Judge` 在执行前审计划，找证据缺口、验收缺口和高风险假设。
- `Worker` 只负责自己的实现切片，按计划交付变更和验证证据。
- `Reviewer` 用 fresh context 审查 diff、测试、artifact、PR/CI 证据。

这样做的收益很直接：

| 收益 | 为什么 |
|---|---|
| 更经济 | 不把所有工作都塞给同一个长上下文强模型；按角色、风险和任务类型选择模型档位。 |
| 更高效 | 可以把互不阻塞的 evidence、design、worker、review 轨道并行 fan out；主 agent 只负责调度、整合和最终判断。 |
| 质量更好 | 每个 subagent 有固定输入、输出 packet 和关闭条件；重要结论要有证据；非轻量结果需要 fresh review。 |

### 2. 证据优先：模型别太自信，也别静默回退

Coding agent 最危险的失败方式不是“不知道”，而是“不知道但说得很肯定”。
另一个常见失败是需求、范围或验收没问清楚就开始计划 / 执行；做完也可能是错的。
缺环境、路径、超参数或执行模式时，模型也不能自己编默认值继续跑。
Teamwork 的规则会把名字、README、issue、summary、`latest`、`v2` 这类信息先当成 claim，
要求 agent 去找直接证据；缺少必要输入时，必须 fail fast，而不是静默回退。

- 重要结论要标成 `observed` / `inferred` / `claimed`。
- 关键决策要映射到源码、配置、日志、测试、diff、artifact 或 primary source。
- 需求、验收、根因、API 行为、环境 / 路径 / 超参数、provider 或外部约束不清楚时，先问清楚、research 或 fail fast。
- 计划和 review 会检查证据是否足够、假设是否安全、验收是否有缺口。

这不是为了增加仪式感，而是把模型的自信和“自动补默认值”的冲动压回到证据能支撑的范围内。

### 3. 任务记忆：让长任务不会反复失忆

复杂 coding-agent 任务通常不是一次完成的：先讨论，再调研，再计划，再执行，失败后还要复盘。
如果这些只留在聊天上下文里，几轮之后就会丢失。

Teamwork 用 artifacts 保存关键状态：

```text
docs/teamwork/research/YYYY-MM-DD-<slug>.md
docs/teamwork/plans/YYYY-MM-DD-<slug>.md
docs/teamwork/reports/YYYY-MM-DD-<slug>.md
```

- `research` 记录讨论 / 调研结论、证据、方案和仍然不确定的地方。
- `plans` 记录可执行范围、边界、验收标准、dispatch guidance 和 stop rules。
- `reports` 记录重要任务结论，或 goal-mode 下每轮尝试、验证结果、失败原因和下一步。

这让 `Goal Text` 不只是一个目标句子，而是能绑定证据、预算、停止条件和历史尝试的执行控制面。
失败后，Teamwork 会回到 research + plan adequacy，而不是重复上一轮猜测。

### 4. 验收闭环：完成要能被复查

Teamwork 把计划、执行、验证和 review 串成闭环。计划要写清 scope、verification、
stop rules；执行结束要说明改了什么、证据是什么、哪里没覆盖；review 要按 severity、
evidence、required action 给出结论。

对多项状态，Teamwork 鼓励用短表格交付：

| 场景 | 表格看什么 |
|---|---|
| 计划 | Step / Scope / Owner / Verification / Stop rule |
| 执行结果 | Requirement / Change / Evidence / Status |
| Review | Severity / Finding / Evidence / Required action |
| Goal 迭代 | Attempt / Hypothesis / Verification / Result / Next step |

表格不是为了好看，而是让人类能快速扫出范围、证据、风险和下一步。

## 装上以后 agent 行为怎么变

| 没有 Teamwork | 有 Teamwork |
|---|---|
| 主 agent 一边探索一边改 | `using-teamwork` 路由到 research、debug、plan、execute、review、goal 等阶段 |
| Subagents 没有稳定边界 | 独立轨道 fan out 给角色 subagents；每个角色有固定职责、输入、输出 packet 和关闭条件 |
| 模型把 summary 当事实 | 重要结论先标 `observed` / `inferred` / `claimed`，并映射到直接证据 |
| 做完就说完成 | 非轻量结果默认 fresh review；同上下文自查不能冒充验收 |
| 结论散在长段落里 | 计划、执行、review、goal 迭代用短表格汇总，方便人类复查 |
| 失败几轮后忘记历史 | report 记录尝试、验证、失败分类和下一轮决策 |
| 长任务靠用户反复提醒 | artifacts 和 goal loop 维持上下文、预算、stop rules 和验收证据 |

## 什么时候值得用

适合：

- 需要把非轻量 coding-agent 工作 fan out 给多个 subagents 分担调研、方案、实现或复查。
- 需要在成本、速度和质量之间做更清晰的角色分工。
- 需要降低模型过度自信，把关键结论压到可检查证据上。
- 需要跨回合保留讨论、调研、计划、报告、失败尝试和验收证据。
- 需要计划、执行结果和 review 便于人类快速复查。
- 需要持续迭代直到目标被验证、预算耗尽或遇到真实 blocker。

不适合：一句话事实、很小的明显编辑、敏感/破坏性操作、强耦合临界路径，
或 subagent 上下文成本高于收益的任务。

## 快速安装

Codex-first 默认安装：

```bash
./install.sh              # 等同于 ./install.sh codex
./install.sh codex --profile cost-first
```

安装到其他平台（同样支持 `performance-first` / `cost-first`）：

```bash
./install.sh cursor|claude|all
./install.sh cursor-agents|claude-agents
./install.sh cursor-policy-copy|cursor-policy|claude-policy
```

`./install.sh claude` 写入 `~/.claude/CLAUDE.md`；`./install.sh cursor-policy`
打印 Cursor User Rules block，`cursor-policy-copy` 复制到剪贴板后再粘贴。

本地开发或项目级安装：

```bash
./install.sh project         # 写入 gitignored .cursor/.codex/.claude
./install.sh --link codex
./install.sh --link all
./install.sh --link project
```

## Skills 怎么用

`using-teamwork` 是唯一宽入口：先走 native fast path，小事直接做；再从用户自然意图、证据状态和验收风险自动推断 research/debug/plan/execute/review/goal 等阶段。用户不需要说内部 stage 名。

| Skill | 什么时候用 | Teamwork 渐进能力 |
|---|---|---|
| `teamwork-research` | 来源、证据、方案、外部约束或 repro surface 不清楚 | Evidence / Research Framing |
| `teamwork-debug` | 可复现或大概率可复现的故障，需要假设、临时 instrumentation 和 runtime evidence 才能定根因 | Runtime Diagnosis / Root Cause Proof |
| `teamwork-plan` | 明确要求 plan/design，或非轻量实现需要边界和验收 | Design Synthesis / Planning Synthesis |
| `teamwork-execute` | 已接受的计划、清单、范围或已知根因修复需要实现 | Staged Execution / Verification Before Claims |
| `teamwork-review` | review、diff、完成验收、strict quality、deslop、PR walkthrough | Review Reception / Fresh Review |
| `teamwork-goal` | keep going、until green/done、预算内迭代 | Goal Recovery / Convergence |
| `teamwork-init` | AGENTS/CODEX/CURSOR/CLAUDE、项目规则瘦身、安装就绪检查 | Instruction Slimming |
| `teamwork-update` | 刷新安装面、检查版本漂移、release hygiene | Package Hygiene |

这些能力是 Teamwork 原生的渐进能力。`teamwork-debug` 是 stage，不是新角色；普通聊天不显示内部能力名，复杂任务才按需加载 routing policy、references、artifacts、packets 或 subagents。

## 平台定位

Codex 是 reference runtime：native goals 是自治控制面，`teamwork_*` custom
agents 是非轻量工作的主要协作网络。`./install.sh codex` 写入全局 bootstrap
policy；`./install.sh codex-policy` 打印同一 block 供 Codex App 个性化粘贴。
完整 workflow 规则留在 skills/references，项目文件只存本地事实和例外。

Cursor 和 Claude Code 同样是一等 runtime：7 个角色 agent、`./install.sh
--profile`、以及 bootstrap policy（Cursor 用 `cursor-policy-copy`，Claude 用
managed `~/.claude/CLAUDE.md`）。详见 [CURSOR.md](CURSOR.md) 和
[CLAUDE.md](CLAUDE.md)。

## 版本与验证

`VERSION` 与两个 plugin manifest 保持一致。用户刷新安装面：`teamwork-update`
（user refresh）或 `./scripts/check-update.sh`；项目 init 前也会跑 readiness
检查。release 走 maintainer 模式；本地项目安装用 `./install.sh project`。

```bash
./scripts/check-update.sh --project /path/to/project
./scripts/validate.sh
```

## 深入阅读

- [CODEX.md](CODEX.md)：Codex runtime profile、Goal Text、custom-agent 映射。
- [CURSOR.md](CURSOR.md)：Cursor adapter。
- [CLAUDE.md](CLAUDE.md)：Claude Code adapter。
- `skills/*/SKILL.md`：阶段 skill 行为定义。
- `skills/using-teamwork/references/`：dispatch、packet、artifact、review、goal 细节。
