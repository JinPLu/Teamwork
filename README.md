<p align="center">
  <img src="assets/teamwork-workflow-gpt-image-2.png" alt="Teamwork 工作流" width="760">
</p>

<h1 align="center">Teamwork</h1>

<p align="center">
  让 Codex、Cursor 和 Claude Code 先交付真实结果；只在能推进结果或保护明确边界时加入调研、测试和复查。
</p>

<p align="center">
  <a href="https://github.com/JinPLu/Teamwork/releases"><img src="https://img.shields.io/github/v/release/JinPLu/Teamwork?display_name=tag&amp;sort=semver" alt="最新 Release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-2563EB" alt="MIT License"></a>
  <img src="https://img.shields.io/badge/platforms-Codex%20%C2%B7%20Cursor%20%C2%B7%20Claude%20Code-0F766E" alt="支持 Codex、Cursor 和 Claude Code">
</p>

[English](README.en.md) · [更新日志](CHANGELOG.md) · [参与贡献](CONTRIBUTING.md) · [MIT License](LICENSE)

---

## ✨ 它解决什么问题

Teamwork 是一套共享 skill package，适配 Codex、Cursor 和 Claude Code。它不接管宿主：各宿主仍负责发现 skill、调用原生工具、执行权限策略和产生实际回复。

你通常只要正常描述目标。范围、验收标准和执行权限明确时，Teamwork 会走最短真实路径；计划、测试、验证和 review 只是辅助，不能代替已经可运行的真实路径，结果完成后就停止。选择调研、排错、计划、执行或验收仍是模型行为，而不是确定性的自动路由。

| 🎯 关注点 | 你得到的行为 |
| --- | --- |
| **基于证据** | 用原始来源、项目文件和真实配置，不凭空补路径、端口、模型或参数。 |
| **真实结果优先** | Plan 不补足权限也不是执行前提；只验证改动路径或明确高风险边界。 |
| **必要时才提问** | 先检查可发现事实，只询问会改变结果、范围、验收或权限的决定。 |
| **有边界的协作** | 只在适合拆分时使用 subagent，主任务保留范围和集成责任。 |
| **可恢复的讨论** | 明确保存/恢复、临近交接、未决比较或真实分支足够多时，才保存有用的连续性。 |

> [!TIP]
> 一句话事实和明显的小编辑不会被强行套流程；复杂调研、技术选型、CI、跨文件实现、严格 review 和“持续推进直到通过”的任务更适合 Teamwork。

### 🧭 表达与连续性

面对需要解释的讨论，Teamwork 会先给出结论或它代表的含义，再连接观察到的事实、它们说明什么，以及会改变决定的边界。技术细节只在确有帮助或你要求时展开。

在已初始化、已获写入授权且运行时可写的仓库中，用户明确要求先提问或挑战时，可保存一份包含目标、已定选择、未决问题、关键证据和继续点的紧凑摘要；显式保存/恢复、临近交接、未决比较或足够多的真实分支也可能使它有用。普通 Plan 不会自动进入 Grill 或写入讨论文档。

---

## 🚀 最快开始

### Codex：Marketplace 插件（推荐）

```bash
codex plugin marketplace add JinPLu/Teamwork@v3.4.0
codex plugin add teamwork-skill@teamwork
```

然后开启一个新 Codex 任务并调用：

```text
$teamwork-update
```

安装插件后，全部 10 个 Teamwork Skill 会立即从插件缓存可用。

> [!IMPORTANT]
> 首次完整启用仍需你的明确确认。`$teamwork-update` 会先说明将要配置的 Codex agents、路由、受管全局策略、通知选择和已验证的旧 Skill 清理；它绝不会创建 `~/.agents/skills` 副本或覆盖无法确认归属的内容。

### Cursor、Claude Code 或 checkout 兼容路径

```bash
git clone https://github.com/JinPLu/Teamwork.git
cd Teamwork
./install.sh all
./scripts/check-update.sh --readiness
```

安装后直接描述想要的结果即可。需要精确指定能力时，再显式调用宿主支持的 Skill：

```text
调研这个领域、关键论文和现有代码，再给我一个可执行方案。
定位这个 CI 失败的根因，用日志和复现证据确认后修复。
直接实现并尽早运行最短真实路径；只修第一个真实 blocker，成功后停止。
严格 review 这次产出，重点检查假成功、防御性 fallback 和 AI 冗余。
grill me：只挑战会改变结果的关键决定，没有实质问题就停止。
```

---

## 🧩 选择安装方式

| 目标 | 推荐入口 | 后续动作 |
| --- | --- | --- |
| **Codex** | `codex plugin marketplace add JinPLu/Teamwork@v3.4.0` → `codex plugin add teamwork-skill@teamwork` | 新任务调用 `$teamwork-update` |
| **Codex checkout**（3.4.x 兼容） | `./install.sh codex` | 适用于本地开发或暂不迁移插件的用户 |
| **Cursor** | `./install.sh cursor` | 复制 Cursor User Rules |
| **Claude Code** | `./install.sh claude` | 使用受管全局策略 |
| **全部平台** | `./install.sh all` | 刷新三端的全局 Teamwork 表面 |

Marketplace 包是完整运行时：它不依赖用户保留 checkout，包含 10 个 Skill、Codex 专用安装与更新逻辑、agent 模板和通知资源。`teamwork-init` 可通过插件的 Codex-only 路径为一个指定仓库建立项目上下文；Cursor 和 Claude Code 继续使用仓库安装器。

### 常用 checkout 选项

```bash
./install.sh --help
./install.sh --profile cost-first codex
./install.sh --notifications codex
./install.sh --project-root /path/to/project init-project
```

- `--profile cost-first`：优先使用当前低成本模型。
- `--notifications`：为直接平台安装添加主任务完成和权限请求提示；完整的 `all` / `init-project` 安装默认启用，可用 `--no-notifications` 退出。
- `init-project`：为指定仓库建立项目说明、可用的工作记录入口和 CodeGraph 上下文，同时刷新当前用户的全局 Teamwork 表面；它不会把 Teamwork skills 或 agents 安装到该仓库中。

默认的完整全局刷新使用 `./install.sh all`。

---

## 🔄 更新与订阅提醒

### 更新已安装的 Codex 插件

```bash
codex plugin marketplace upgrade teamwork
codex plugin add teamwork-skill@teamwork
```

随后开启新任务并调用 `$teamwork-update`，让它检查并刷新仅限 Codex 的受管表面。

### 更新 checkout 工作流

```bash
git pull --ff-only
./install.sh all
./scripts/check-update.sh --readiness
```

### 🔔 不想自己记版本？订阅 GitHub Release

打开 [JinPLu/Teamwork](https://github.com/JinPLu/Teamwork)，选择 **Watch** → **Custom** → 勾选 **Releases**。GitHub 会在新 Release 发布时通过站内通知（以及你启用时的邮件）提醒你；它只提醒，不会自动升级本地插件或配置。[GitHub 官方通知说明](https://docs.github.com/en/subscriptions-and-notifications/get-started/configuring-notifications)

---

## 🛡️ 安全边界与迁移说明

> [!WARNING]
> 只删除已确认由 Teamwork 生成的条目，绝不要整体删除 `.agents`、`.codex`、`.cursor` 或 `.claude`。遇到同名但未知或改写过的内容，安装器会停止并要求人工确认。

- Marketplace 首次启用只配置 Codex agents、路由、受管策略和可选通知；不复制用户 Skill。
- 需要通知时，在 Codex 中重启后打开 `/hooks`，逐项信任 Teamwork 的 `Stop` 与 `PermissionRequest`，不要使用 trust-all。
- Cursor User Rules 仍需手动复制粘贴；安装器无法验证该宿主侧步骤。
- `./scripts/check-update.sh --readiness` 只证明 Teamwork 受管文件和配置已对齐，不证明某项手动宿主操作完成，也不保证一次自然语言请求必定选择某个 Skill。

---

## 📚 继续了解

- [更新日志](CHANGELOG.md)：每个版本中用户能感受到的变化。
- [Codex](CODEX.md)、[Cursor](CURSOR.md)、[Claude Code](CLAUDE.md)：平台安装与高级用法。
- [项目结构](docs/architecture.md)：canonical source、生成目录、稳定命令和变更 owner。
- [参与贡献](CONTRIBUTING.md)：修改范围和验证要求。
- [GitHub Issues](https://github.com/JinPLu/Teamwork/issues)：问题反馈与建议。
