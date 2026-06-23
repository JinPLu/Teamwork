# Teamwork

[English](README.en.md)

**给个人科研/工程任务加一层协作系统：深调研、会分工、能写代码、可复盘、可验收。**

Teamwork 是一个 **Codex-first 的 Codex + Cursor + Claude Code skill package**。
它把 Codex、Cursor 和 Claude Code 从一次性聊天助手，变成围绕你长期项目工作的个性化科研协作 agent。
它不替代编辑器、shell、MCP、浏览器、权限或测试工具；这些 native capabilities 仍然负责执行。
Teamwork 解决的是更上层的问题：复杂任务怎样先查证、怎样分工、怎样保留上下文、怎样证明真的完成。

Coding 是最重要的落地场景之一，但 Teamwork 的 research、planning、review 和 memory
不是 coding 专属。它同样适合论文/领域调研、方案比较、实验设计、资料复盘、长期项目推进。

![Teamwork 工作流说明图](assets/teamwork-workflow-gpt-image-2.png)

## 为什么需要

个人科研和工程协作的瓶颈通常不是“模型不会回答”，而是：

- 调研太浅：看一篇文章、一个 README 或一个搜索结果就开始总结，不会主动扩展到相邻来源和反例。
- 主线漂移：研究、设计、实现、实验和复盘混在一条长聊天里。
- 分工失控：几个 subagents 并行后没人负责集成，结论互相打架。
- 假成功太多：缺 env、路径、端口、模型名、超参数、数据来源时随手给默认值继续跑。
- 长任务失忆：调研、计划、失败尝试和验收证据散在聊天里。
- 完成不可验收：最后只剩一句“我完成了”，没有来源、实验、测试、日志、diff、artifact 或 fresh review 支撑。

Teamwork 把这些风险变成工作流约束：先查证，再计划；值得并行时才 fan out；
必需值缺失就问、查证或 block；非轻量结果必须有验证证据。

## 核心优势

| 用户遇到的问题 | 普通 agent / 简单 subagents | Teamwork |
|---|---|---|
| 调研不够深 | 停在用户给的 seed source | 从 seed source 扩到 source census、primary source、neighbor source、反例和空白问题 |
| 分工不可控 | 多个聊天各说各话 | 只有独立轨道才 fan out；Explorer、Designer、Judge、Worker、Reviewer 输出 packet，由主 agent 集成 |
| 证据不扎实 | 把标题、summary、文件名、`latest`、`v2` 当事实 | 关键结论映射到论文、文档、源码、配置、日志、测试、diff、artifact 或 primary source |
| 缺值被兜底 | 防御性 fallback 把缺失状态伪装成成功 | 必需值必须来自用户、项目文件、源码、测试或已接受计划；否则问、查或停 |
| 失败反复猜 | 失败后换个猜法继续试 | 记录假设、验证、失败类别和下一步，必要时回到 research + plan adequacy |
| 完成不可验收 | 模型自述完成 | 执行给验证证据；重要结果进入 review 或 goal loop |

一句话：Teamwork 不是让 agent 更会写“流程文档”，而是让大任务的证据、分工、记忆和验收都可检查。

## 什么时候值得用

如果任务会跨论文/网页/代码/数据/回合/工具，或者你已经遇到 agent 反复猜、反复修、反复说完成，Teamwork 值得装。

适合：

- 先调研领域、paper、API、库、竞品、历史决策或项目资料，再制定方案。
- 做科研/工程方向比较、实验设计、证据整理、长期项目推进。
- coding、debug 可复现故障、flaky 测试、CI 失败、崩溃或 UI 症状，并证明根因。
- fan out subagents 做调研、设计、实现或复查，但需要主线集成。
- strict review、deslop、AI 冗余输出清理、代码质量/PR/CI 复查。
- 持续迭代直到测试通过、目标达成、预算耗尽或遇到真实 blocker。

不必用：

- 一句话事实、小的明显编辑、局部语法问题。
- 强耦合临界路径，subagent 上下文成本高于收益。
- 敏感、破坏性或必须人工确认后才能继续的操作。

## 怎么使用

继续用自然语言提需求，不需要学习内部 stage 名：

```text
先调研这个领域、关键论文和现有代码，再给我一个方案。
fan out subagents 比较几个方向，最后推荐一个可执行计划。
按计划执行；失败要记录原因和证据，直到测试通过。
严格 review 这次产出，重点看假成功、防御性 fallback 和 AI 冗余。
```

`using-teamwork` 会判断是直接走 native fast path，还是进入 research、debug、plan、execute、review、goal、init 或 update。
小事直接做；复杂任务才加载更多规则、subagents 和 artifacts。

## 快速安装

Codex 默认安装：

```bash
./install.sh              # 等同于 ./install.sh codex
./install.sh codex --profile cost-first
```

其他平台：

```bash
./install.sh cursor|claude|all
./install.sh cursor-agents|claude-agents
./install.sh cursor-policy-copy|cursor-policy|claude-policy
```

项目级安装和本地开发：

```bash
./install.sh project
./install.sh --project-root /path/to/project init-project
./install.sh --link codex
```

`teamwork-init` 负责项目规则、AGENTS/CODEX/CURSOR/CLAUDE、`docs/teamwork/` 和 CodeGraph 初始化。
`teamwork-update` 与 `./scripts/check-update.sh` 负责刷新 skills/agents/policy、检查安装面和版本漂移。

## 工作方式

Teamwork 的内部 skills 只在需要时触发：

| 能力 | 什么时候触发 |
|---|---|
| `teamwork-research` | 来源、证据、方案、外部约束或 repro surface 不清楚 |
| `teamwork-debug` | 有日志、CI、崩溃、flaky、UI 症状，需要 runtime evidence |
| `teamwork-plan` | 需要边界、验收、dispatch guidance 或 stop rules |
| `teamwork-execute` | 执行已接受计划、清单、范围或已知根因修复 |
| `teamwork-review` | fresh review、strict quality、deslop、PR/CI 或完成验收 |
| `teamwork-goal` | keep going、until green/done、预算内持续迭代 |

需要跨回合保留时，artifacts 固定写到：

```text
docs/teamwork/research/YYYY-MM-DD-<slug>.md
docs/teamwork/plans/YYYY-MM-DD-<slug>.md
docs/teamwork/reports/YYYY-MM-DD-<slug>.md
```

## 版本与验证

`VERSION` 与 plugin manifest 保持一致。刷新安装面或做 release 前：

```bash
./scripts/check-update.sh --project /path/to/project
./scripts/validate.sh
```

## 深入阅读

- [CODEX.md](CODEX.md)：Codex runtime profile、Goal Text、custom-agent 映射。
- [CURSOR.md](CURSOR.md)：Cursor adapter。
- [CLAUDE.md](CLAUDE.md)：Claude Code adapter。
- `skills/*/SKILL.md`：各 workflow skill 的行为定义。
- `skills/using-teamwork/references/`：dispatch、packet、artifact、review、goal 细节。
