# Run-Analyze-Optimize Skill

> Agent-roundtable-lite 的 run/analyze/optimize skill pack：一个 router
> 负责分流，五个 subskill 分别处理调研、计划、执行、审查、无人值守收敛。
> 保留 roundtable 式证据优先、角色分离、多视角审查和 dissent，但不搬运
> model registry、pricing cache、thread ledger、dispatch scripts 等完整基建。

支持三种入口：

- Claude Code skills / plugin
- Codex skills / plugin
- Cursor project rule

Router:

```text
skills/run-analyze-optimize/SKILL.md
```

Subskills:

```text
skills/run-analyze-research/SKILL.md
skills/run-analyze-plan/SKILL.md
skills/run-analyze-execute/SKILL.md
skills/run-analyze-review/SKILL.md
skills/run-analyze-goal/SKILL.md
```

`run-analyze-review` 故意不拆成两个 skill。它有两个显式模式：

- `mode: plan` - 执行前审计划。
- `mode: execution` - 执行后审 diff、产物、测试和验收条件。

## 你想... -> 输入

> `run-analyze-optimize:` 等价于“调用 router，让它按意图选择 subskill”。

| 场景 | 输入 | 路由 |
|---|---|---|
| **调研讨论** | `run-analyze-optimize: 调研 X 的可行方案，保留分歧` | `run-analyze-research` -> options / dissent / recommendation |
| **制定计划** | `把方案 B 写成可执行修改计划，列 scope、风险、验证` | `run-analyze-plan` -> implementation plan |
| **审计划** | `review this plan before execution` | `run-analyze-review` with `mode: plan` |
| **执行已接受计划** | `按这个 plan 执行，只做最小必要改动` | `run-analyze-execute` |
| **审执行结果** | `review this diff/result and verification` | `run-analyze-review` with `mode: execution` |
| **无人值守迭代到收敛** | `最多 3 轮，直到 pytest X 通过；无进展就停` | `run-analyze-goal` |
| **修生成 pipeline** | `直到 artifacts/ 有 N 条合法记录，保持 schema 不变` | `run-analyze-goal` |

## 主流程展开

```text
你输  run-analyze-optimize: 调研怎么修 pytest X，给 2-3 个方案
      -> run-analyze-research
      -> 读日志 / 测试 / 源码，输出 options + dissent + recommendation

你输  把推荐方案写成可执行计划
      -> run-analyze-plan
      -> 输出 scope / sacred boundary / steps / verification / risk

你输  审这个 plan
      -> run-analyze-review mode: plan
      -> 检查 scope、假设、可行性、验证设计、风险

你输  按已接受 plan 执行
      -> run-analyze-execute
      -> 最小改动 + focused verification，不自称完成

你输  审执行结果
      -> run-analyze-review mode: execution
      -> reviewer 直接读 diff、测试、产物，给 verdict + dissent
```

如果你希望一条命令跑完整闭环：

```text
run-analyze-optimize: 跑 pytest workplace/eval/tests，最多 3 轮，修到通过；
不要改公共 schema；每轮必须先计划、后执行、再审执行结果。
```

Router 会走：

```text
research/discuss if needed
  -> plan
  -> review plan
  -> execute
  -> review execution
  -> accept / continue / re-plan / block
```

## 子 Skill 速查

| Skill | 什么时候用 | 产物 |
|---|---|---|
| `run-analyze-optimize` | 入口不确定，想让 router 分流 | route + reason |
| `run-analyze-research` | 原因不明、方案未定、需要多视角讨论 | evidence、options、dissent、recommendation |
| `run-analyze-plan` | 方向已选，需要 worker 可执行计划 | scope、steps、verification、risk、handoff |
| `run-analyze-execute` | plan 已接受，要实现 | changed files、verification、deviations、blockers |
| `run-analyze-review` | 审计划或审执行结果 | verdict: pass / revise / blocked |
| `run-analyze-goal` | 给目标和预算，让它自动收敛 | iterations、verification、review、conclusion |

## 规则边界

- **证据优先**：先读日志、测试、产物、diff、源码，再诊断。
- **Karpathy guardrails**：假设明确、简单优先、外科手术式改动、目标驱动验证。
- **角色分离**：research / plan / execute / review 是独立 pass；必要时可用 subagent。
- **reviewer 不信 summary**：审查者必须直接读 evidence。
- **保留 dissent**：少数意见不抹平，最终 verdict 要写 residual risk。
- **executor 不自宣完成**：完成必须通过 `mode: execution` review。
- **停止条件明确**：verified success、budget exhausted、no-progress、blocker、sacred-boundary conflict。

## 一次性安装

### Claude Code

```bash
./install.sh claude
```

等价手动安装：

```bash
for skill in \
  run-analyze-optimize \
  run-analyze-research \
  run-analyze-plan \
  run-analyze-execute \
  run-analyze-review \
  run-analyze-goal; do
  mkdir -p "$HOME/.claude/skills/$skill"
  ln -sf "$(pwd)/skills/$skill/SKILL.md" \
    "$HOME/.claude/skills/$skill/SKILL.md"
done
```

Plugin metadata:

```text
.claude-plugin/plugin.json
```

### Codex

```bash
./install.sh codex
```

等价手动安装：

```bash
for skill in \
  run-analyze-optimize \
  run-analyze-research \
  run-analyze-plan \
  run-analyze-execute \
  run-analyze-review \
  run-analyze-goal; do
  mkdir -p "$HOME/.codex/skills/$skill"
  ln -sf "$(pwd)/skills/$skill/SKILL.md" \
    "$HOME/.codex/skills/$skill/SKILL.md"
done
```

Codex manifest 保持目录入口，避免 schema 风险：

```json
"skills": "./skills/"
```

### Cursor

```bash
./install.sh cursor /path/to/project
```

Cursor 不直接消费 Claude/Codex skill 目录，所以这里只安装 thin rule：

```text
.cursor/rules/run-analyze-optimize.mdc
```

## 验证

```bash
./scripts/validate.sh
```

验证内容：

- `skills/` 只包含这六个 skill 目录；
- 每个 `SKILL.md` 都有匹配 frontmatter；
- router 引用所有 subskill path；
- `run-analyze-review` 同时包含 `mode: plan` 和 `mode: execution`；
- 不存在拆分版 plan-review / execution-review skill；
- Claude manifest 列出全部 skill；
- Codex manifest 保持 `"skills": "./skills/"`；
- Cursor rule 存在、足够薄，并列出所有 skill 名。

## 发布到 GitHub

```bash
git remote add origin git@github.com:<owner>/run-analyze-optimize-skill.git
git push -u origin main
```

GitHub CLI:

```bash
gh repo create run-analyze-optimize-skill --public --source=. --remote=origin --push
```

## 不适合

- 没有可验证目标的“帮我优化一下”；
- 纯审美 / 文案口味判断；
- 大架构方向完全未定但又要求直接执行；
- 需要完整 agent-roundtable 的跨厂商 dispatch、成本估算、thread ledger、pricing cache。

一句话：它是一个轻量、可安装、可验证的 Roundtable-style run/analyze/optimize workflow，不是完整多 agent 平台。
