# Teamwork

[English](README.en.md) · [更新日志](CHANGELOG.md) · [参与贡献](CONTRIBUTING.md) · [MIT License](LICENSE)

**让 Codex、Cursor 和 Claude Code 先把真实结果做出来，只在能推进结果或保护明确边界时调研、测试和复查。**

Teamwork 是一套适配 Codex、Cursor 和 Claude Code 的共享 skill package；各宿主仍负责发现 skill、调用原生工具、执行权限策略和产生实际回复。安装后，通常只需照常用自然语言描述目标。明确、已授权的 change/build 会直接进入最短真实路径；计划、测试、验证和 review 只是辅助，不能代替可用的真实运行，结果完成后就停止。宿主仍会依据请求和 skill 描述选择调研、排错、计划、执行或验收；这种选择属于模型行为，并非确定性的自动路由。面对需要解释的讨论，Teamwork 要求先给出结论或它代表的含义，再把观察到的事实、这些事实说明什么，以及会改变决定的边界连成一段短论证。技术细节只在确有帮助或你要求时展开，不会拿内部流程、版本或标签当作回答主体。

![Teamwork 工作流](assets/teamwork-workflow-gpt-image-2.png)

## 你会得到什么

- **基于证据的调研：** 从原始来源、项目文件和实际配置中找证据，不凭空补路径、端口、模型或参数。
- **真实结果优先：** 范围、验收标准和执行权限已明确时即可直接修改、生成或运行，accepted plan 不是前提也不会补足权限；只有新证据改变已接受的范围或标准才重回 Plan。只检查改动路径或明确高风险边界，结果出现后立即停止；独立复查仅在用户或已接受风险门槛要求时进行。
- **只问必要问题：** 先自行检查可发现的事实，只把会改变结果、范围、验收或权限的决定交给你。
- **有边界的协作：** 只在任务适合拆分时使用 subagent，主 agent 负责范围和集成，不重放已经完成的工作。
- **真实路径决定完成：** 优先看实际产物、命令或运行是否成功；plan、mock、静态检查和代理测试不能把尚未运行的目标说成完成。
- **可恢复的讨论：** 仓库已经初始化、用户已授权写入、运行时也确实可写，并且用户明确要求先提问或挑战时，可保存一份包含目标、已定选择、未决问题、关键证据和继续点的紧凑摘要，供后续任务继续。显式保存/稍后恢复、临近交接或压缩、已定结论仍有明确未决比较，或至少三条真实分支中的任一条件即可使记录有用；短讨论既不触发也不否决记录。普通 Plan 不会自动进入 Grill 或写入讨论文档。

适合文献与领域调研、技术选型、复杂方案、可复现故障、CI、跨文件实现、严格 review，以及“持续推进直到通过”的任务。一句话事实和明显的小编辑不会被强行套流程。

## 快速开始

需要先安装并能正常使用 Codex、Cursor 或 Claude Code 中的至少一个。对 Codex，推荐使用 Marketplace 插件：添加固定的 3.4.0 Marketplace、安装插件、开启新任务，再显式启用完整 Codex 集成：

```bash
codex plugin marketplace add JinPLu/Teamwork@v3.4.0
codex plugin add teamwork-skill@teamwork
```

在新任务中调用 `$teamwork-update`。它会先说明将配置的 agents、路由、受管全局策略、通知选择，以及已验证的旧 Skill 清理；确认这一次启用即可。安装插件后 10 个 Teamwork Skill 立即可用，而用户级 Codex 配置仍由你显式决定。

Cursor、Claude Code 或兼容期内的 checkout 工作流仍可使用完整全局安装：

```bash
git clone https://github.com/JinPLu/Teamwork.git
cd Teamwork
./install.sh all
./scripts/check-update.sh --readiness
```

安装后通常可以直接描述想要的结果。自然语言用于表达意图；如果必须指定某项能力，可显式调用宿主支持的 skill：

```text
调研这个领域、关键论文和现有代码，再给我一个可执行方案。
定位这个 CI 失败的根因，用日志和复现证据确认后修复。
直接实现并尽早运行最短真实路径；只修第一个真实 blocker，成功后停止。
严格 review 这次产出，重点检查假成功、防御性 fallback 和 AI 冗余。
grill me：只挑战会改变结果的关键决定，没有实质问题就停止。
```

## 安装

| 目标 | 命令 |
|---|---|
| Codex（推荐） | `codex plugin marketplace add JinPLu/Teamwork@v3.4.0` → `codex plugin add teamwork-skill@teamwork` → 新任务调用 `$teamwork-update` |
| Codex checkout（3.4.x 兼容） | `./install.sh codex` |
| Cursor | `./install.sh cursor` |
| Claude Code | `./install.sh claude` |
| 全部平台 | `./install.sh all` |

Marketplace 安装不依赖 checkout 即可提供全部 10 个 Skill。它的首次显式启用只配置 Codex agents、路由、受管全局策略与可选通知，绝不创建 `~/.agents/skills` 副本。之后可通过 `teamwork-init` 使用插件内的 Codex-only 项目初始化。Cursor 与 Claude Code 继续使用仓库安装器。`./install.sh codex` 在 3.4.x 兼容期内保留；若已存在插件 activation 标记，它会安全停止而不会复制同名 Skill。

checkout 全局命令让 Teamwork skills 和 agents 对当前用户可用，不会自动修改每个项目。默认的完整全局刷新使用 `./install.sh all`。需要为某个仓库建立 Teamwork 项目上下文时，使用 `teamwork-init`，或用下面的 `init-project` 命令明确指定项目路径。

默认安装使用 `performance-first` profile。查看所有目标和选项：

```bash
./install.sh --help
```

常用选项：

```bash
./install.sh --profile cost-first codex
./install.sh --notifications codex
./install.sh --project-root /path/to/project init-project
```

- `--profile cost-first`：优先使用当前低成本模型。
- `--notifications`：为直接平台安装添加主任务完成音和权限请求音；subagent 保持静音。完整的 `all`/`init-project` 安装默认启用，可用 `--no-notifications` 退出。Codex 安装后需在 CLI 运行 `/hooks`，逐项审核并信任两项 Teamwork hook。
- `init-project`：为指定仓库建立 Teamwork 项目上下文，包括项目说明，以及可用时的工作记录入口和 CodeGraph；同时刷新当前用户的全局 skills、agents 和默认规则。它不会把 Teamwork skills 或 agents 安装到该仓库中。

迁移提示：已有的项目级 Teamwork 副本不再支持或刷新。只删除已确认由 Teamwork 生成的条目，绝不要整体删除 `.agents`、`.codex`、`.cursor` 或 `.claude`；然后运行 `./install.sh all`。

Codex 用户级安装更新角色路由后需要重启 Codex；它的 hooks 仍需用户在 CLI 中逐项信任。Marketplace 包刻意不在 manifest 中声明 hooks：若启用通知，仍须在 `/hooks` 单独信任稳定的 Teamwork `Stop` 与 `PermissionRequest` handler。Cursor User Rules 仍需手动复制粘贴，安装器无法验证是否已完成。安装器只管理 Teamwork 自己的目录、规则块和有限配置；不会接管平台权限、MCP、浏览器、测试设置或宿主的实际模型行为。平台细节见 [Codex](CODEX.md)、[Cursor](CURSOR.md) 和 [Claude Code](CLAUDE.md)。

`./scripts/check-update.sh --readiness` 检查的是 Teamwork 管理的文件和配置是否新鲜、齐全；它不证明 Cursor 的手动 User Rules、Codex 的 hook 信任步骤已经完成，也不证明某次自然语言请求一定会激活特定 skill。

## 更新

已安装的 Codex 插件请先升级 Marketplace、重新安装插件，再开启新任务调用 `$teamwork-update` 刷新其仅限 Codex 的受管表面：

```bash
codex plugin marketplace upgrade teamwork
codex plugin add teamwork-skill@teamwork
```

checkout 工作流则先更新仓库，再使用完整全局安装刷新当前用户的 Teamwork，并检查安装状态：

```bash
git pull --ff-only
./install.sh all
./scripts/check-update.sh --readiness
```

在助手会话中，也可以使用 `teamwork-update` 检查并指导这次全局刷新；项目上下文则由 `teamwork-init` 处理。

## 更多信息

- [更新日志](CHANGELOG.md)：每个版本中用户能感受到的变化。
- [Codex 指南](CODEX.md)、[Cursor 指南](CURSOR.md)、[Claude Code 指南](CLAUDE.md)：平台安装与高级用法。
- [项目结构](docs/architecture.md)：canonical source、生成目录、稳定命令和变更 owner。
- [参与贡献](CONTRIBUTING.md)：修改范围和验证要求。
- [GitHub Issues](https://github.com/JinPLu/Teamwork/issues)：问题反馈与建议。
