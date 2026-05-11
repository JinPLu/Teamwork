# Run-Analyze-Optimize Skill

> 轻量自迭代 agent skill：给一个命令 / 目标，自动运行、读证据、诊断根因、做最小修改、复跑验证、独立 review，直到成功或明确阻塞。

支持三方安装：

- Claude Code skill / plugin
- Codex skill / plugin
- Cursor project rule

Canonical skill 只维护一份：

```text
skills/run-analyze-optimize/SKILL.md
```

Cursor、Codex、Claude Code 的入口都指向或引用这一份内容，避免三份 `SKILL.md` 分叉。

## 你想... -> 输入

| 场景 | 输入 | 链路 |
|---|---|---|
| **修 failing test** | `run-analyze-optimize: 跑 pytest X，直到通过` | run -> diagnose -> plan -> patch -> verify -> review |
| **修生成 pipeline** | `直到 artifacts/ 有 N 条合法记录` | monitor logs -> check artifacts -> fix producer -> rerun |
| **迭代 prompt/parser/schema** | `保持 schema 不变，只优化 prompt/校验/重试` | protect boundary -> root cause -> minimal implementation change |
| **长命令自动收敛** | `最多 3 轮，无进展就停` | budgeted loop -> evidence delta check -> stop/continue |
| **高风险修改** | `用强模型做最终 review，便宜模型做 dissent` | worker -> independent reviewer -> preserve dissent |

## 核心流程

```text
初始化边界
  -> 跑命令
  -> 读日志 / 测试 / 产物
  -> 诊断根因
  -> 写最小修改计划
  -> worker 执行
  -> 复跑验证
  -> reviewer 独立审查
  -> 成功 / 继续 / 阻塞 / 预算耗尽
```

## 设计原则

- **Karpathy guardrails**：先想清楚、简单优先、外科手术式修改、目标驱动验证。
- **Roundtable-lite**：角色分离、证据优先、独立 review、保留 dissent、预算停止。
- **不搬运完整 roundtable 基建**：不依赖 `models.json`、thread ledger、pricing cache、dispatch confirmation。
- **单一 source of truth**：只维护 `skills/run-analyze-optimize/SKILL.md`。

## 安装

### Claude Code

个人全局安装：

```bash
./install.sh claude
```

等价手动安装：

```bash
mkdir -p ~/.claude/skills/run-analyze-optimize
ln -sf "$(pwd)/skills/run-analyze-optimize/SKILL.md" \
  ~/.claude/skills/run-analyze-optimize/SKILL.md
```

Claude Code plugin manifest:

```text
.claude-plugin/plugin.json
```

### Codex

个人全局安装：

```bash
./install.sh codex
```

等价手动安装：

```bash
mkdir -p ~/.codex/skills/run-analyze-optimize
ln -sf "$(pwd)/skills/run-analyze-optimize/SKILL.md" \
  ~/.codex/skills/run-analyze-optimize/SKILL.md
```

Codex plugin manifest:

```text
.codex-plugin/plugin.json
```

### Cursor

项目级安装：

```bash
./install.sh cursor /path/to/project
```

等价手动安装：

```bash
mkdir -p /path/to/project/.cursor/rules
ln -sf "$(pwd)/.cursor/rules/run-analyze-optimize.mdc" \
  /path/to/project/.cursor/rules/run-analyze-optimize.mdc
```

Cursor 不直接读取 Claude/Codex skill 目录，所以这里提供一个 thin project rule。规则文本会指向 canonical skill，并总结必要流程。

## 验证

```bash
./scripts/validate.sh
```

验证内容：

- canonical `SKILL.md` frontmatter 可识别
- 没有顶层 ```skill fence
- Claude/Codex manifests 存在
- Cursor rule 存在

## 发布到 GitHub

如果你有 GitHub CLI：

```bash
gh repo create run-analyze-optimize-skill --public --source=. --remote=origin --push
```

如果没有 `gh`：

```bash
git remote add origin git@github.com:<owner>/run-analyze-optimize-skill.git
git push -u origin main
```

## 不适合

- 开放式产品设计
- 没有可验证目标的“帮我优化一下”
- 大架构方向未定
- 需要人类偏好判断的文案 / UI 决策

一句话：**它是一个能自己跑到证据闭环的轻量 Roundtable，不是一个复杂多 agent 平台。**
