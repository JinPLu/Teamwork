# Teamwork

Teamwork 是给 Claude Code、Codex 和 Cursor 共用的一组工作流 skills。它不是替代原生 coding agent 的框架，而是在任务需要证据、计划、分工、复查或自主收敛时，把这些步骤变成明确、可验证、可交接的流程。

最重要的判断：

- 简单、低风险、单步任务继续走 native flow。
- 需要读文件、日志、diff、外部信息后才能判断方向时，先走 research。
- 多步骤、含糊、高风险、跨 agent、跨轮次或 goal mode，必须把范围、证据、验证和停止条件说清楚。
- 执行者不能自宣完成；完成要靠验证结果和 review 证据。

## Quick Start

安装到 Codex：

```bash
git clone https://github.com/JinPLu/Teamwork.git
cd Teamwork
./install.sh codex
```

其他安装方式：

```bash
./install.sh claude
./install.sh cursor /path/to/project
./install.sh all /path/to/cursor-project
./install.sh --link codex
./install.sh --link claude
```

验证仓库：

```bash
./scripts/validate.sh
```

Claude Code 中启动一个有界自主目标：

```text
/teamwork:goal 修复 pytest X，最多 3 轮，无进展就停 --max-iterations 3
/teamwork:plan docs/teamwork/plans/2026-05-14-fix-pytest-x.md
```

`/rao:goal` 等 `/rao:*` 命令仍是兼容别名。

## Skill Map

当前只有七个 active skills，职责按阶段拆开：

| Skill | 什么时候用 | 主要产物 |
|---|---|---|
| `using-teamwork` | 普通 coding / debugging / research / review 请求开始时，先判断是否需要升级到 Teamwork | native flow 或具体 Teamwork stage |
| `teamwork` | 公共 router；定义证据规则、activation tiers、subagent 角色、Codex dispatch mapping | 路由决策和共享行为契约 |
| `teamwork-research` | 需要收集证据、比较方案、排查原因、刷新旧假设 | `docs/teamwork/research/YYYY-MM-DD-<slug>.md` |
| `teamwork-plan` | 把已选方向变成可执行计划，或任务多步/有风险/用户要求计划 | lightweight checklist 或 durable plan |
| `teamwork-execute` | 执行已接受计划 | 最小必要改动和 focused verification |
| `teamwork-review` | 审计划或审执行结果 | `mode: plan` 或 `mode: execution` verdict |
| `teamwork-goal` | 用户要求持续迭代直到通过、预算耗尽或明确 blocker | durable plan anchor、checkpoint、completion audit |

不要把七个 skill 看成每次都要跑一遍。它们是按需要调用的阶段：能 native 解决就 native；只有 Teamwork 能提升正确性时才升级。

## Workflow

常见完整链路是：

```text
research -> plan -> plan review -> execute -> execution review -> accept / iterate / block
```

但这是高风险或 artifact-backed 任务的形态，不是所有任务的最低门槛。

| 任务形态 | 推荐流程 |
|---|---|
| 简单、明确、低风险 | native flow；必要时用简短 checklist |
| 需要证据或方案比较 | `teamwork-research`，然后再决定是否 plan |
| 多步骤但边界清楚 | `teamwork-plan` 的 lightweight plan，执行后 focused verification 和 review pass |
| 高风险、跨 agent、跨轮次、含糊或显式要求仓库计划 | durable plan artifact + plan review + bounded execution + execution review |
| 自主续跑到目标达成 | `teamwork-goal`，必须有 durable plan anchor、checkpoint 和 completion audit |

## Artifacts

Teamwork 的持久产物是普通 Markdown 文件，方便 Claude Code、Codex、Cursor 共用。

Research artifact：

```text
docs/teamwork/research/YYYY-MM-DD-<slug>.md
```

Durable plan artifact：

```text
docs/teamwork/plans/YYYY-MM-DD-<slug>.md
```

`teamwork-plan` 使用最轻但足够正确的计划形式。轻量、低风险、单 agent 的 bounded work 可以只用 chat/native checklist；跨 agent、跨轮次、高风险、含糊、public/shared behavior 变化、显式 repository plan、以及所有 goal mode，都使用 durable Markdown plan artifact。

Plan artifact 应覆盖目标、需求到证据的映射、已读证据、范围边界、实施步骤、验证命令、预期结果、风险、停止条件、worker handoff 和 review handoff。它不是 Codex goal state，也不是 Claude `.claude/teamwork-goals/` runtime state。

重要证据要区分：

- `observed`: 直接读到的源码、diff、配置、日志、命令输出、测试结果或 artifact。
- `inferred`: 从 observed evidence 推出的结论。
- `claimed`: README、文件名、注释、历史说明、工具摘要或用户叙述里的说法，尚未被直接证据确认。

## Subagents

Subagents 是加速独立取证、隔离执行、fresh-context review 的工具，不是仪式。主 agent 负责拆解、综合、冲突解决、验证和最终接受。

Teamwork 的概念角色：

| Role | 用途 |
|---|---|
| Explorer | 独立读文件、日志、测试、artifact，返回压缩证据 |
| Designer | 处理含糊需求、架构取舍、跨模块方案 |
| Judge | 执行前审计划 |
| Worker | 按已接受计划实现，必须有明确文件或职责边界 |
| Reviewer | 执行后审 diff、验证证据、回归风险和残留分歧 |

模型层级用能力描述，不写死模型 ID：`fast` 用于低风险证据和机械改动，`standard` 用于中等综合或多文件执行，`high reasoning` 用于设计、Judge、最终 review、安全或回归边界。

## Codex Runtime

Codex runtime 使用原生能力，不模拟一套额外调度系统：

- `update_plan` 只是 transient UI-only checklist，不是 durable execution 或 review artifact。
- native Codex goals 只用于用户明确要求自主收敛，或已有 active goal 的情况。
- Codex subagents 只用于独立 Explorer、Designer、Judge、Worker、Reviewer track。
- `codex review --uncommitted`、`--base` 或 `--commit` 可以作为审查证据，但不能自动代表通过。
- sandbox 或网络限制阻塞必要命令时，按 Codex 权限模型请求窄范围 escalation。

Codex dispatch details are derived from the router mapping in `skills/teamwork/SKILL.md`. Ordinary plans should record conceptual role, scope, tier, context strategy, order, and why; include native Codex fields only when a non-default native override is itself part of the decision.

## Claude Runtime

Claude Code 插件提供 `/teamwork:*` 命令；`/rao:*` 保留为兼容前缀，状态文件存放在：

```text
.claude/teamwork-goals/
```

核心命令：

```text
/teamwork:goal <objective> [--max-iterations N] [--completion-promise TEXT]
/teamwork:plan <docs/teamwork/plans/...md>
/teamwork:checkpoint --plan-review-verdict <pass|pass-with-notes|revise|blocked> --execution-review-verdict <pass|pass-with-notes|revise|blocked> --verification-command <command> --verification-result <pass|fail> --evidence-delta <progress|no-progress>
```

其他命令包括 `/teamwork:status`、`pause`、`resume`、`stop`、`complete`、`clear` 和 `note`。Stop hook 会在 goal 未完成且未达到最大轮数时阻止停止，并注入下一轮 continuation prompt。连续两次 `--evidence-delta no-progress` 会停止 goal。默认 completion promise 是 `RAO_GOAL_COMPLETE`。

自动完成必须同时包含 promise 和结构化 audit；只出现 promise 不会被视为 verified completion。

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

`plan_review_verdict` 和 `execution_review_verdict` 只能是 `pass` 或 `pass-with-notes`。`/teamwork:complete` 和 `/rao:complete` 是人工 override，不等同于自动验证通过。

## Cursor

Cursor 只安装薄规则入口 `.cursor/rules/teamwork.mdc`，指向同一组 Teamwork skills，不复制完整 Claude runtime。

当修改 workflow 行为时，优先更新对应 `skills/*/SKILL.md`。README 只负责帮助读者快速理解当前 skill 体系和入口，不复制完整 skill body。
