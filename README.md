# Run-Analyze-Optimize Skill

> Agent-roundtable-lite 的 run / analyze / optimize skill pack。
> 当前版本把过细的 subskills 收敛成 4 个安装入口：一个 router / goal
> controller，三个阶段 skill。保留 roundtable 式证据优先、角色分离、多视角审查
> 和 dissent，但不搬运 model registry、pricing cache、thread ledger、dispatch
> scripts 等完整基建。

支持三种入口：

- Claude Code skills / plugin
- Codex skills / plugin
- Cursor project rule

## 当前 Skill 拓扑

```text
skills/run-analyze-optimize/SKILL.md  # router + autonomous goal mode
skills/run-analyze-design/SKILL.md    # mode: research | mode: plan
skills/run-analyze-execute/SKILL.md   # accepted-plan execution
skills/run-analyze-review/SKILL.md    # mode: plan | mode: execution
```

为什么这样拆：

- `run-analyze-optimize` 是唯一公共入口，也承载无人值守 goal controller。
- `run-analyze-design` 合并调研和计划，但用显式 mode 保持边界。
- `run-analyze-execute` 只执行已接受计划，不自宣完成。
- `run-analyze-review` 仍然是一个 review skill，用两个 mode 区分审计划和审执行结果。

## 你想... -> 输入

> `run-analyze-optimize:` 等价于“调用 router，让它按意图选择 mode / skill”。

| 场景 | 输入 | 路由 |
|---|---|---|
| **调研讨论** | `run-analyze-optimize: 调研 X 的可行方案，保留分歧` | `run-analyze-design` with `mode: research` |
| **制定计划** | `把方案 B 写成可执行修改计划，列 scope、风险、验证` | `run-analyze-design` with `mode: plan` |
| **审计划** | `review this plan before execution` | `run-analyze-review` with `mode: plan` |
| **执行已接受计划** | `按这个 plan 执行，只做最小必要改动` | `run-analyze-execute` |
| **审执行结果** | `review this diff/result and verification` | `run-analyze-review` with `mode: execution` |
| **无人值守迭代到收敛** | `最多 3 轮，直到 pytest X 通过；无进展就停` | `run-analyze-optimize` with `mode: goal` |

## 主流程展开

分阶段使用：

```text
你输  run-analyze-optimize: 调研怎么修 pytest X，给 2-3 个方案
      -> run-analyze-design mode: research
      -> 读日志 / 测试 / 源码，输出 options + dissent + recommendation

你输  把推荐方案写成可执行计划
      -> run-analyze-design mode: plan
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

一条命令跑完整闭环：

```text
run-analyze-optimize: 跑 pytest workplace/eval/tests，最多 3 轮，修到通过；
不要改公共 schema；每轮必须先计划、后执行、再审执行结果。
```

Router 的 `mode: goal` 会走：

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
| `run-analyze-optimize` | 入口不确定，或要无人值守迭代到可验证目标 | route / goal iterations / conclusion |
| `run-analyze-design` | 执行前的调研或计划 | options / dissent / implementation plan |
| `run-analyze-execute` | plan 已接受，要实现 | changed files / verification / deviations |
| `run-analyze-review` | 审计划或审执行结果 | verdict: pass / revise / blocked |

## 规则边界

- **证据优先**：先读日志、测试、产物、diff、源码，再诊断。
- **Karpathy guardrails**：假设明确、简单优先、外科手术式改动、目标驱动验证。
- **角色分离**：research / plan / execute / review 是独立 pass；必要时可用 subagent。
- **reviewer 不信 summary**：审查者必须直接读 evidence。
- **保留 dissent**：少数意见不抹平，最终 verdict 要写 residual risk。
- **executor 不自宣完成**：完成必须通过 `mode: execution` review。
- **停止条件明确**：verified success、budget exhausted、no-progress、blocker、sacred-boundary conflict。

## 安装

Claude Code:

```bash
./install.sh claude
```

Codex:

```bash
./install.sh codex
```

Cursor project rule:

```bash
./install.sh cursor /path/to/project
```

全部安装：

```bash
./install.sh all /path/to/cursor-project
```

安装脚本会安装当前 4 个 skill，并安全清理旧版本留下的已知 retired symlink：
只有当旧 `SKILL.md` symlink 指回本仓库时才会删除，不会碰用户自建目录。

Codex manifest 保持目录入口，避免 schema 风险：

```json
"skills": "./skills/"
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

- `skills/` 只包含当前 4 个 skill 目录；
- 每个 `SKILL.md` frontmatter 只有 `name` 和 `description`；
- description 使用 `Use when...` 触发式写法；
- router 引用当前 subskill path，并包含 `mode: goal`；
- `run-analyze-design` 同时包含 `mode: research` 和 `mode: plan`；
- `run-analyze-review` 同时包含 `mode: plan` 和 `mode: execution`；
- Claude manifest、Codex manifest、Cursor rule、install script 与当前拓扑一致；
- 临时 HOME 下的 Claude / Codex / Cursor 安装 smoke 通过。

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
