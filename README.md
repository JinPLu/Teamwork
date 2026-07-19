<h1 align="center">Teamwork</h1>

<p align="center">
  让 Codex、Cursor 和 Claude Code 在需要时做好外部调研、设计、排错、计划与验收，不给日常工作加一套额外流程。
</p>

<p align="center">
  <a href="https://github.com/JinPLu/Teamwork/releases"><img src="https://img.shields.io/github/v/release/JinPLu/Teamwork?display_name=tag&amp;sort=semver" alt="最新 Release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-2563EB" alt="MIT License"></a>
  <img src="https://img.shields.io/badge/platforms-Codex%20%C2%B7%20Cursor%20%C2%B7%20Claude%20Code-0F766E" alt="支持 Codex、Cursor 和 Claude Code">
</p>

[English](README.en.md) · [更新日志](CHANGELOG.md) · [参与贡献](CONTRIBUTING.md) · [MIT License](LICENSE)

---

## Teamwork 能帮你做什么

Teamwork 是一组可安装到 Codex、Cursor 和 Claude Code 的 Skills。当前版本有 10 个公开 Skills、3 份只由所属 Skill 使用的进阶参考，以及 8 个宿主 agent 角色；它只为真正需要专门方法的任务提供清晰边界：外部多来源调研、本地证据查找、重要方案设计、未知原因排错、可执行计划、独立复查和长时间收敛。

本地代码、配置、测试、日志和运行现象的查证，本来就是 agent 的基本能力；范围清楚且已授权的实现也直接由宿主完成。因此 v4 不再提供通用 Execute skill，也不再用一个 router skill 二次判断工作流向。你只需描述想要的结果；宿主仍负责工具、权限、Skill 选择和最终回复。

## 需要精确指定时，选择一种能力

| 你想做的事 | Skill | 何时用 |
| --- | --- | --- |
| 调研外部现状 | `$teamwork-research` | 查官方资料、论文、市场或时效性事实，并给出可追溯引用。 |
| 查找本地证据 | `$teamwork-explore` | 只读查代码、配置、测试、日志、历史、artifact 或运行状态，并给出一个可验证的本地结论。 |
| 设计重要方案 | `$teamwork-design` | 产品、架构、工作流程或公开契约仍有会改变结果的取舍。 |
| 定位未知故障 | `$teamwork-debug` | 真实失败的原因不明，需要复现、区分假设并验证修复。 |
| 把方向变成计划 | `$teamwork-plan` | 方向已定，需要有所属、依赖、直接验证与停止条件的执行步骤。 |
| 检查产出或结论 | `$teamwork-review` | 对计划、diff、artifact 或完成声明做独立、有证据的验收。 |
| 持续推进到可验证 | `$teamwork-goal` | 你明确要求“继续到通过”、“修到绿”或给出预算化目标。 |
| 先挑战你的决定 | `$grill-me` | 你显式要求被追问、质疑、保存或继续这次讨论。 |
| 初始化一个项目 | `$teamwork-init` | 设置或整理项目说明、Teamwork memory 入口和可用的 CodeGraph 上下文。 |
| 检查或刷新全局安装 | `$teamwork-update` | 更新 Teamwork 管理的 skills、agents、策略、路由和通知。 |

Research 只处理外部或时效性证据；Explore 只处理本地项目证据。Design 和 Plan 的分界也很简单：方案未定时用 Design，方向已定时用 Plan，只是实现一个清晰改动时两者都不需要。

Design 只在某个未决的本地约束会改变选择时调用 Explorer，只在某个明确的外部或时效性主张会改变选择时，才让 Research 用已脱敏的问题补充证据；不会默认同时跑两条证据轨。真正有取舍时会比较 2–3 个实质不同的方案；若证据只有一条安全路径，则记录 safe-path evidence 和排除理由，不虚构选项。它只做一次 challenge pass，并把真正由用户决定的事项限制在有限 frontier（通常不超过三个）。方向冻结后，受控的 Design transaction 生成一个持久 Design artifact；然后才可进入 Plan。独立 Plan Review 只在用户要求或命名的实质风险门需要时运行。受控写入不可用时会停止，不会手写替代 artifact；Design、Plan 或其批准都不授权实现。

方法致谢：v4 采用了 Superpowers 的 hard gate、options 和 specification self-check 思路；一次 challenge 与有限 decision frontier 是 Teamwork 针对本地协作方式做的调整，并非声称完整复刻 Superpowers 工作流。

## 快速开始

### Codex：Marketplace 插件（推荐）

```bash
codex plugin marketplace add JinPLu/Teamwork
codex plugin add teamwork-skill@teamwork
```

开启一个新的 Codex 任务，然后运行：

```text
$teamwork-update
```

Skills 会直接从插件缓存加载。首次完整启用时，`$teamwork-update` 会说明它准备配置的 Codex agents、路由、受管全局策略、通知和已验证旧文件清理，并在你确认后才执行。它不会创建 `~/.agents/skills` 副本，也不会覆盖归属不明的内容。

### Cursor、Claude Code 或 checkout 安装

```bash
git clone https://github.com/JinPLu/Teamwork.git
cd Teamwork
./install.sh all
./scripts/check-update.sh --readiness
```

也可只安装一个平台：

```bash
./install.sh codex
./install.sh cursor
./install.sh claude
```

Cursor 还需运行 `./install.sh cursor-policy-copy`，再把内容粘贴到 **Cursor Settings → Rules → User Rules**。完整说明见 [Codex](CODEX.md)、[Cursor](CURSOR.md) 和 [Claude Code](CLAUDE.md) 指南。

## 初始化项目

为指定仓库建立项目说明和工作记录入口：

```bash
./install.sh --project-root /path/to/project init-project
```

`init-project` 只修改所选项目：它设置 Teamwork 管理的项目说明、memory 入口、ignore 规则，并在 CodeGraph CLI 可用时初始化本地上下文。它不会刷新全局 skills、agents、策略、路由或通知，也不会把 Teamwork 副本安装进项目。全局更新请单独使用 `$teamwork-update` 或 `./install.sh all`。

## 讨论、实现、复查与持续目标

- 普通的“先问我”只会进行问答，不写文件。显式调用 `$grill-me`、保存、继续或记录会在已初始化且可写的项目中使用唯一的 `docs/teamwork/discussion/current.md`；独立构成重大变更的讨论（公开或可安装能力/角色、迁移或发布、权限、安全、数据、破坏性或跨平台边界）也会自动打开持久记录。同一范围只在创建、实质决定/frontier 变化及关闭/取代时落盘；状态未变就是 no-op。“不写文件”或 off-the-record 始终优先。
- Debug 先取得真实失败、复现和区分假设的证据；仅诊断时不修改。原请求已授权修复时，才会改动证据支持的真正 owner，并重跑同一失败路径。Research、Design、Plan 和 Review 默认只读；Plan 只把已选方向写成可执行步骤，Review 只给 `ACCEPT`、`REVISE` 或 `BLOCKED` 的独立证据结论。
- 清楚且已授权的实现按结果优先进行：先改 canonical owner、复用现有模式/内建能力/合适依赖，再写最小完整逻辑；每个 Worker 用与风险相称的聚焦测试和真实路径自证自己的切片。Root 集成并封定候选后，只有用户要求或命名的实质风险门需要时才做一次独立 max Review；发现项合成一个修复批次，每个候选最多再做一次 delta recheck。
- `$teamwork-goal` 只在你明确要求持续推进时启用。它会先保存目标、成功信号、范围、保护边界、预算和尝试记录；没有持久状态就不会假称能跨回合持续，只有真实成功信号和命名边界都通过才完成。
- 安装器只删除已确认由 Teamwork 生成的条目。不要整体删除 `.agents`、`.codex`、`.cursor` 或 `.claude`；同名内容归属不明或已被修改时，安装器会停止。
- 启用 Codex 通知后，请重启 Codex，在 `/hooks` 中只信任 Teamwork 的 `Stop` 和 `PermissionRequest`，不要使用 trust-all。
- `./scripts/check-update.sh --readiness` 只检查 Teamwork 管理的文件和配置，不能代替 Cursor User Rules、hook 信任等宿主手动步骤，也不保证自然语言每次都选中同一个 Skill。

## 更新

Codex Marketplace 升级：

```bash
codex plugin marketplace remove teamwork
codex plugin marketplace add JinPLu/Teamwork
codex plugin add teamwork-skill@teamwork
```

开启新任务并运行 `$teamwork-update`。checkout 安装升级：

```bash
git pull --ff-only
./install.sh all
./scripts/check-update.sh --readiness
```

从 v3.4.2 升级时，重新运行对应安装命令或 `$teamwork-update`，让安装器仅清理它能确认归属的旧 Router/Execute 和 legacy role 文件。这个识别只用于安全迁移，不是 v4 的兼容别名：v4 不提供 Router、Execute 或旧角色名称的 alias。

想收到新版本提醒，可在 [GitHub 仓库](https://github.com/JinPLu/Teamwork) 选择 **Watch → Custom → Releases**。

## 更多资料

- [更新日志](CHANGELOG.md)：各版本的用户可见变化、升级方式与限制。
- [Codex](CODEX.md)、[Cursor](CURSOR.md)、[Claude Code](CLAUDE.md)：各平台的配置和排错。
- [项目结构](docs/architecture.md)：源码、生成目录、依赖边界和稳定命令。
- [参与贡献](CONTRIBUTING.md)：修改与验证要求。
- [GitHub Issues](https://github.com/JinPLu/Teamwork/issues)：反馈问题或建议。
