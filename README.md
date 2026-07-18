<p align="center">
  <img src="assets/teamwork-workflow-gpt-image-2.png" alt="Teamwork 工作流" width="760">
</p>

<h1 align="center">Teamwork</h1>

<p align="center">
  让 Codex、Cursor 和 Claude Code 更可靠地完成复杂的调研、排错、实现与验收。
</p>

<p align="center">
  <a href="https://github.com/JinPLu/Teamwork/releases"><img src="https://img.shields.io/github/v/release/JinPLu/Teamwork?display_name=tag&amp;sort=semver" alt="最新 Release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-2563EB" alt="MIT License"></a>
  <img src="https://img.shields.io/badge/platforms-Codex%20%C2%B7%20Cursor%20%C2%B7%20Claude%20Code-0F766E" alt="支持 Codex、Cursor 和 Claude Code">
</p>

[English](README.en.md) · [更新日志](CHANGELOG.md) · [参与贡献](CONTRIBUTING.md) · [MIT License](LICENSE)

---

## Teamwork 能帮你做什么

Teamwork 是一组可安装到 Codex、Cursor 和 Claude Code 的 Skills。你只需描述想要的结果；缺少必要事实时，它会先查项目和原始证据，在范围与权限明确时直接推进，只在真正影响结果时提问、计划或复查。

它特别适合：

- 调研技术、论文或现有代码，并给出有依据的建议；
- 从日志、复现和配置中定位未知故障；
- 在关键选择未定时比较方案并形成可执行计划；
- 实现跨文件改动，并验证真正受影响的路径；
- 严格检查“看似完成”、多余 fallback 和遗漏的边界；
- 持续推进任务，直到获得可验证结果或遇到真实阻塞。

简单问答和小修改仍走宿主的快速路径，不会被强行套流程。Teamwork 也不接管宿主：工具调用、权限确认、Skill 选择和最终回复仍由 Codex、Cursor 或 Claude Code 控制。

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

插件安装后，10 个 Teamwork Skills 已可从插件缓存使用。`$teamwork-update` 会先说明它准备配置的 agents、路由、受管全局策略、通知和旧 Skill 清理，再等待你的确认；它不会创建 `~/.agents/skills` 副本，也不会覆盖归属不明的内容。

### Cursor、Claude Code 或 checkout 安装

```bash
git clone https://github.com/JinPLu/Teamwork.git
cd Teamwork
./install.sh all
./scripts/check-update.sh --readiness
```

`all` 会安装三端所需的全局 Skills 和 agents，以及 Codex、Claude Code 的受管策略；Cursor User Rules 仍需手动粘贴。也可只安装一个平台：

```bash
./install.sh codex
./install.sh cursor
./install.sh claude
```

Cursor 还需运行 `./install.sh cursor-policy-copy`，再把内容粘贴到 **Cursor Settings → Rules → User Rules**。完整说明见 [Codex](CODEX.md)、[Cursor](CURSOR.md) 和 [Claude Code](CLAUDE.md) 指南。

## 直接描述目标，或点名一种能力

通常无需记 Skill 名称。需要精确指定工作方式时，可选择：

| 你想做的事 | Skill | 示例 |
| --- | --- | --- |
| 查清事实、来源或现状 | `$teamwork-research` | “调研这个领域的关键论文和现有实现，再给建议。” |
| 定位原因不明的失败 | `$teamwork-debug` | “用日志和复现证据确认这个 CI 失败的根因。” |
| 解决会改变结果的选择 | `$teamwork-plan` | “比较这两种迁移方案，确定验收标准和执行步骤。” |
| 执行已明确的改动 | `$teamwork-execute` | “实现这个改动，验证受影响路径，成功后停止。” |
| 检查计划、代码或结论 | `$teamwork-review` | “严格 review 这次产出，找出假成功和遗漏边界。” |
| 持续推进直到可验证 | `$teamwork-goal` | “继续修复直到检查通过；遇到真实阻塞再停。” |
| 先挑战你的关键决定 | `$grill-me` | “先问我：只挑战会改变结果的决定。” |
| 初始化一个项目 | `$teamwork-init` | “为这个仓库初始化 Teamwork 项目上下文。” |
| 检查和刷新 Codex 安装 | `$teamwork-update` | “检查 Teamwork 是否需要更新。” |

`$using-teamwork` 是轻量入口：当你不确定该选哪种能力时，让它按当前任务选择即可。选择仍是模型行为；自然语言请求不能保证每次都命中某个 Skill。

## 项目初始化与常用选项

为指定仓库建立项目说明和工作记录入口：

```bash
./install.sh --project-root /path/to/project init-project
```

这会同时刷新当前用户的全局 Teamwork 安装，但不会把 Skills 或 agents 复制进目标仓库。如果本机 CodeGraph CLI 可用且初始化成功，还会建立 CodeGraph 上下文。

```bash
./install.sh --help
./install.sh --profile cost-first codex
./install.sh --notifications codex
```

- `--profile cost-first`：优先使用当前的低成本模型配置。
- `--notifications`：为直接平台安装加入任务完成和权限请求提示；`all` 与 `init-project` 默认启用，可用 `--no-notifications` 退出。
- `--link`：本地开发时使用符号链接，让安装跟随 checkout。

## 更新

更新 Codex Marketplace 插件：

```bash
codex plugin marketplace remove teamwork
codex plugin marketplace add JinPLu/Teamwork
codex plugin add teamwork-skill@teamwork
```

然后开启新任务并运行 `$teamwork-update`。

更新 checkout 安装：

```bash
git pull --ff-only
./install.sh all
./scripts/check-update.sh --readiness
```

想收到新版本提醒，可在 [GitHub 仓库](https://github.com/JinPLu/Teamwork) 选择 **Watch → Custom → Releases**。提醒不会自动升级本地插件或配置。

## 权限与安全边界

- 回答、调研、排错、计划和 review 默认是只读的；只有你明确授权后，Teamwork 才会修改文件或外部状态。接受计划本身不等于授权执行。
- 在已初始化且可写的仓库中，明确要求“先问我”或 `grill me` 可保存一份紧凑的讨论继续点；如果不希望写入文件，请直接说明。普通计划不会自动创建这类记录。
- 安装器只删除已确认由 Teamwork 生成的条目。不要整体删除 `.agents`、`.codex`、`.cursor` 或 `.claude`；同名内容归属不明或已被修改时，安装器会停止并要求确认。
- 启用 Codex 通知后，请重启 Codex，在 `/hooks` 中只信任 Teamwork 的 `Stop` 和 `PermissionRequest`，不要使用 trust-all。
- `./scripts/check-update.sh --readiness` 只检查 Teamwork 管理的文件和配置，不证明 Cursor User Rules、hook 信任等手动宿主步骤已经完成。

## 更多资料

- [更新日志](CHANGELOG.md)：各版本的用户可见变化与升级说明。
- [Codex](CODEX.md)、[Cursor](CURSOR.md)、[Claude Code](CLAUDE.md)：各平台的完整配置和高级用法。
- [项目结构](docs/architecture.md)：源码、生成目录和稳定命令。
- [参与贡献](CONTRIBUTING.md)：修改与验证要求。
- [GitHub Issues](https://github.com/JinPLu/Teamwork/issues)：反馈问题或建议。
