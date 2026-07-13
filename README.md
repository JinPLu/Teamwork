# Teamwork

[English](README.en.md) · [更新日志](CHANGELOG.md) · [参与贡献](CONTRIBUTING.md) · [MIT License](LICENSE)

**让 Codex、Cursor 和 Claude Code 在复杂科研/工程任务中先找证据、再行动，并用可检查的结果收尾。**

Teamwork 是一个 **Codex-first 的 Codex + Cursor + Claude Code skill package**。它不替代 shell、MCP、浏览器、权限或测试工具，而是在这些原生能力之上补上任务路由、证据约束、可控分工、跨回合记忆和验收闭环。

![Teamwork 工作流](assets/teamwork-workflow-gpt-image-2.png)

## 它解决什么

| 常见问题 | Teamwork 的处理方式 |
|---|---|
| 调研停在一个来源 | 从 seed source 扩展到 primary source、相邻证据和必要的反例 |
| 研究、实现、复盘混成一条长聊天 | 按风险路由到 research、debug、plan、execute、review 或 goal |
| 多个 subagents 各说各话 | 只拆独立任务，主 agent 负责范围、集成和最终验证 |
| 缺路径、端口、模型或配置时随手兜底 | 必需值只能来自用户、项目、源码、配置、测试或已接受计划 |
| “已完成”没有证据 | 用来源、日志、测试、diff、artifact 或 fresh review 支撑结论 |

小问题仍走平台原生 fast path；Teamwork 只在额外流程能提高正确性、连续性或可验收性时介入。

## 快速开始

准备条件：已安装并能正常使用 Codex、Cursor 或 Claude Code 中的至少一个；本仓库的安装入口使用 Bash。

以 Codex 为例：

```bash
git clone https://github.com/JinPLu/Teamwork.git
cd Teamwork
./install.sh codex
./scripts/check-update.sh --no-fetch
```

安装后直接用自然语言描述目标，不需要记 workflow 名称：

```text
先调研这个领域、关键论文和现有代码，再给我一个可执行方案。
定位这个 CI 失败的根因，先用日志和复现证据确认，再修复。
按已接受的计划执行并验证；失败要记录原因，直到通过或遇到真实 blocker。
严格 review 这次产出，重点检查假成功、防御性 fallback 和 AI 冗余。
grill me：只挑战会改变结果的关键决策；没有实质问题就停止，不要问语言或文件数量。
```

## 选择安装方式

| 平台 | 命令 | 安装结果 |
|---|---|---|
| Codex | `./install.sh codex` | `~/.codex/skills/`、`~/.codex/agents/`、`~/.codex/AGENTS.md` 标记块，以及 `~/.codex/config.toml` 中有限的角色路由键 |
| Cursor | `./install.sh cursor` | `~/.cursor/skills/`、`~/.cursor/agents/`；按终端提示复制 User Rules |
| Claude Code | `./install.sh claude` | `~/.claude/skills/`、`~/.claude/agents/`，以及 `~/.claude/CLAUDE.md` 中的 Teamwork 标记块 |
| 三个平台 | `./install.sh all` | 安装以上全部用户级入口 |

默认使用 `--copy` 和 `performance-first` profile；Codex 使用 GPT-5.6 Terra/Sol，Cursor 和 Claude Code 使用各自当前原生模型。`cost-first` 也已迁移到当前低成本模型；旧 `gpt55-*` 名称仅作兼容，不再调用 GPT-5.5。高级选项以帮助输出为准：

```bash
./install.sh --help
./install.sh --profile cost-first codex
./install.sh --notifications --profile cost-first codex
```

`--notifications` 为用户级 Codex/Claude Code 安装主任务完成音和权限请求音；
subagent 默认静音，普通安装不会改变现有通知配置。用 `--no-notifications`
只移除 Teamwork 自己的 handler。Codex plugin 用户需在 `/hooks` 明确信任；
Cursor 本地 hook 尚未 live-verified，因此不伪装成已支持。

用户级 Codex 安装会原子迁移 custom-agent 路由，使 fresh subagent 能通过
`agent_type` 使用各角色自己的 model/effort，并将 root-inclusive 总线程上限
设为 9（1 个主线程 + 最多 8 个 subagent）；修改后需重启 Codex。仅当该配置
由其他系统管理时使用 `--no-codex-routing`；项目级安装不会修改用户配置。

原生提问能力由当前宿主提供，不属于 Teamwork 安装状态。运行时有
`request_user_input` 就直接使用；没有时回退为简洁文本。Teamwork 不会为了提问
修改用户配置、切换模式或启用实验特性。

项目级安装与完整初始化：

```bash
./install.sh --project-root /path/to/project project
./install.sh --project-root /path/to/project init-project
```

`project` 安装项目级 skills/agents；`init-project` 还会配置项目规则、`docs/teamwork/` 记忆入口和可用的 CodeGraph。维护本仓库时可使用 `./install.sh --link codex`，让已安装内容跟随 checkout 更新。

安装器只管理 Teamwork 专属目录、agent 文件、带边界标记的全局 policy 块和有限的 Codex 路由键；平台自己的权限、MCP、浏览器和测试配置仍由平台及用户控制。平台细节见 [Codex](CODEX.md)、[Cursor](CURSOR.md) 和 [Claude Code](CLAUDE.md) 文档。

## 什么时候使用

适合：

- 论文/领域调研、API 或库选型、竞品与历史决策查证；
- 需要证据链的方案比较、实验设计和工程实现；
- 可复现故障、flaky 测试、CI、崩溃或 UI 症状诊断；
- 值得分成独立轨道的 subagent 调研、实现或复查；
- 跨回合推进，或持续迭代直到测试通过、目标达成或确认 blocker。

不必使用：一句话事实、明显的小编辑、局部语法问题，或分工成本高于收益的强耦合任务。敏感、破坏性、付费或公开操作仍遵守平台权限和用户确认。

## 工作方式

`using-teamwork` 是轻量路由入口，按当前任务需要加载专用 skill：

| Skill | 负责什么 |
|---|---|
| `grill-me` | 先质疑、查证并分类未知，只把真正属于用户的结果性决策交给原生/结构化问答 |
| `teamwork-research` | 查证来源、外部约束、方案空间和 repro surface |
| `teamwork-debug` | 用复现、日志、假设和 instrumentation 确认根因 |
| `teamwork-plan` | 深度接管 Codex Plan mode 的证据、关键值来源、范围、阶段、验收和停止条件 |
| `teamwork-execute` | 在已接受范围内实现并验证 |
| `teamwork-review` | 检查 diff、证据、质量和完成声明 |
| `teamwork-goal` | 对明确目标持续迭代，直到完成或真正受阻 |

`grill-me` 是交互 skill，不是 Teamwork stage。用户明确要求先提问、挑战或 grill 时会激活；存在实质决策或风险的非简单 Plan 也会自动进入 evidence-first Grill，并在最终计划前确认 Decision Summary。普通澄清仍走平台原生路径，明确拒绝访谈时不追问，引用、文件、工具、示例或维护文本也不会触发。它先查清可发现事实，再由 agent 承担安全可逆的实现选择，只询问仍会实质改变公开行为、兼容性、验收、成本、风险或不可逆操作的用户决策。默认一次问一个；不凑数、不重复已回答的问题。宿主提供 `request_user_input` 时直接使用，否则简洁文本降级。结束 grill 或确认计划都不授权执行。

`teamwork-init` 负责项目接入，`teamwork-update` 负责安装刷新和 release hygiene。

在 Codex Plan mode 中，原生模式负责提问 UI 和最终 plan item，`teamwork-plan` 负责同一条计划链的质量门：先查当前 owner、配置、测试和事实源，再只询问真正属于用户的关键决策；回答后重新对齐证据，并把每项需求映射到有 owner、输入、产物、依赖、验证和停止条件的阶段。所有执行关键数值必须来自用户、仓库或可解释推导，未解决值保持显式，不因计划写得很长就视为充分。

对非简单 Plan（判断标准是存在实质决策或风险，而不是文件数量），除非用户明确拒绝，否则先进行 evidence-first Grill；在最终 Plan 前确认一份简洁的 Decision Summary，列出实质选择、假设和未解决项。简单或机械 Plan 可直接进行。确认只接受计划，不授权实施。

跨平台的 Judge/Reviewer 都以稳定 ID 记录并绑定已接受的 Contract 与 AC：只有阻塞 Contract/AC 的问题才是 `BLOCKER`，其他工作标为 `FOLLOW-UP` 或 `SUGGESTION`。只有运行时确实支持同一 agent resume 才做 delta recheck；否则传递稳定 finding ledger 或 packet。进度更新保持稀疏，只报告实质状态变化。

只有跨回合复用确有价值时，才写入固定位置：

```text
docs/teamwork/research/YYYY-MM-DD-<slug>.md
docs/teamwork/plans/YYYY-MM-DD-<slug>.md
docs/teamwork/reports/YYYY-MM-DD-<slug>.md
```

## 更新与验证

更新 checkout 后，重新执行原安装目标，再检查安装面是否一致：

```bash
git pull --ff-only
./install.sh codex
./scripts/check-update.sh --no-fetch
```

如需同时检查某个项目的本地安装：

```bash
./scripts/check-update.sh --project /path/to/project
```

包版本以 [`VERSION`](VERSION) 为准，并与 plugin manifests 保持一致。仓库开发和发版前运行：

```bash
./scripts/validate.sh
python3 scripts/check-codex-routing.py
python3 scripts/eval-teamwork.py --split dev
python3 scripts/run-teamwork-live-eval.py --help
python3 scripts/audit-codex-sessions.py --help
```

`check-codex-routing.py` 只读检查 Teamwork agent 合同、路由配置、当前 bundled
catalog 中的 model/effort 支持和 prompt 装载；它不会调用模型或修改 catalog。
Codex 升级后仍需用 fresh schema/live spawn 验证真实 selector。

## 文档导航

- [CODEX.md](CODEX.md)：Codex 安装、项目设置、subagents、Goal Mode 与模型 profile。
- [CURSOR.md](CURSOR.md)：Cursor 安装、User Rules、Task subagents 与 goal 记录。
- [CLAUDE.md](CLAUDE.md)：Claude Code 安装、Task subagents 与 goal 记录。
- [CHANGELOG.md](CHANGELOG.md)：面向用户的版本变化。
- [CONTRIBUTING.md](CONTRIBUTING.md)：问题反馈、修改范围和验证要求。
- [`skills/*/SKILL.md`](skills/)：各 workflow skill 的行为定义。

问题与建议请提交到 [GitHub Issues](https://github.com/JinPLu/Teamwork/issues)。
