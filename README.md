<p align="center">
  <img src="assets/teamwork-workflow-gpt-image-2.png" alt="Teamwork 工作流：简单任务直接交付，复杂任务先找证据、行动、验证" width="760">
</p>

<h1 align="center">Teamwork</h1>

<p align="center">
  <strong>复杂任务需要协作，但不需要流程表演。</strong><br>
  Teamwork 给 Codex、Cursor 和 Claude Code 一组更稳的协作方法：该直接做就直接做；该调研、排错、设计、复查或持续推进时，再把正确的能力接上。
</p>

<p align="center">
  <a href="https://github.com/JinPLu/Teamwork/releases"><img src="https://img.shields.io/github/v/release/JinPLu/Teamwork?display_name=tag&amp;sort=semver" alt="最新 Release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-2563EB" alt="MIT License"></a>
  <img src="https://img.shields.io/badge/platforms-Codex%20%C2%B7%20Cursor%20%C2%B7%20Claude%20Code-0F766E" alt="支持 Codex、Cursor 和 Claude Code">
</p>

<p align="center">
  <a href="README.en.md">English</a> ·
  <a href="CHANGELOG.md">更新日志</a> ·
  <a href="CODEX.md">Codex 指南</a> ·
  <a href="CURSOR.md">Cursor 指南</a> ·
  <a href="CLAUDE.md">Claude Code 指南</a>
</p>

---

## ✨ 它帮你避免什么

Teamwork 不是另一个总控 router，也不是“先写计划、再反复 review、再测到没完”的流程包。v4 已经移除了旧的 Router / Execute：清楚、已授权的本地实现继续走宿主原生路径；只有任务真的需要专门方法时，才点亮对应 Skill。

| 你不想要 | Teamwork 的做法 |
| --- | --- |
| 🔁 一直测试、一直复查，却不交付 | 先拿真实结果；测试和 review 只服务于改动路径或明确风险门。 |
| 🧱 小事也被套复杂流程 | 简单问答、小修改、清楚实现直接做，不强制走 Teamwork。 |
| 🕳️ 凭空补路径、端口、模型或状态 | 先看项目、日志、配置、官方资料和实际输出。 |
| ❓ 问一堆无关问题 | 只问会改变结果、范围、验收或权限的决定。 |
| 🧑‍⚖️ review 替代执行 | Review 默认只读，只给有证据的 `ACCEPT` / `REVISE` / `BLOCKED`。 |

---

## 🧩 10 个能力，按需要点名

平时直接描述目标即可；需要精确控制工作方式时，再显式调用 Skill。

| 能力 | 用在什么时候 |
| --- | --- |
| 🔎 `$teamwork-research` | 查外部现状、官方资料、论文、市场信息或需要引用的事实。 |
| 🗂️ `$teamwork-explore` | 只读查看本地代码、配置、日志、测试、历史或 artifact，给出证据结论。 |
| 🧭 `$teamwork-design` | 方案、架构、产品或流程还有会改变结果的真实取舍。 |
| 🐞 `$teamwork-debug` | 失败原因未知，需要复现、区分假设，再确认修复。 |
| 📝 `$teamwork-plan` | 方向已定，需要拆成 owner、依赖、验收和停止条件清楚的步骤。 |
| ✅ `$teamwork-review` | 检查计划、diff、artifact 或完成声明是否真的成立。 |
| 🎯 `$teamwork-goal` | 你明确要求“继续到通过”“修到绿”或给出预算化目标。 |
| 🔥 `$grill-me` | 你希望先被追问、挑战关键决定，或保存/继续这次讨论。 |
| 🧰 `$teamwork-init` | 为一个仓库设置项目说明、Teamwork memory 入口和可用 CodeGraph 上下文。 |
| 🔄 `$teamwork-update` | 检查或刷新全局 Teamwork skills、agents、策略、路由和通知。 |

示例：

```text
用 $teamwork-research 查官方资料和关键论文，给出可追溯建议。
用 $teamwork-debug 复现这个 CI 失败，确认根因后修复同一路径。
直接实现这个改动；只验证受影响路径，成功后停止。
用 $teamwork-review 检查这次 release 是否还有假成功或旧叙述。
用 $teamwork-goal 继续修到指定检查通过，遇到真实阻塞再停。
```

---

## 🚀 快速开始

### 🤖 Codex 默认：Marketplace plugin

```bash
codex plugin marketplace add JinPLu/Teamwork
codex plugin add teamwork-skill@teamwork
```

开启一个新的 Codex 任务，然后运行：

```text
$teamwork-update
```

`$teamwork-update` 会先说明它准备配置的 Codex agents、路由、受管全局策略、通知和旧文件清理，等你确认后才执行。Skills 直接从插件缓存加载，不会复制到 `~/.agents/skills`，也不会覆盖归属不明的内容。

### 🖥️ Cursor、Claude Code 或开发 checkout

```bash
git clone https://github.com/JinPLu/Teamwork.git
cd Teamwork
./install.sh all
./scripts/check-update.sh --readiness
```

也可以只安装一个平台：

```bash
./install.sh cursor
./install.sh claude
./install.sh codex   # 仅用于开发或手动 Codex setup；普通 Codex 用户默认走 plugin
```

Cursor 还需要运行 `./install.sh cursor-policy-copy`，再把内容粘贴到 **Cursor Settings → Rules → User Rules**。

---

## 🧠 Codex agents 与 profile

完整 Codex setup 会安装 8 个自定义 agent：Researcher、Explorer、Debugger、Designer、Planner、Worker、Plan Reviewer 和 Reviewer。它们只在拆分上下文或独立验收真的有价值时使用；主任务仍负责范围、集成和最终回复。

| Profile | 高频执行角色 | 设计 / 计划复查 | 最终复查 |
| --- | --- | --- | --- |
| `performance-first` | `gpt-5.5` / `high` | `gpt-5.6-sol` / `high` | `gpt-5.6-sol` / `max` |
| `cost-first` | `gpt-5.5` / `medium` | Designer 为 `gpt-5.6-sol` / `medium`；Plan Reviewer 为 `gpt-5.6-sol` / `high` | `gpt-5.6-sol` / `high` |

这个分配把常见的证据查找、排错、计划和实现交给更快的执行模型，把重大取舍和独立验收留给更保守的 reviewer 模型。

---

## 🔄 更新

Codex plugin 更新：

```bash
codex plugin marketplace remove teamwork
codex plugin marketplace add JinPLu/Teamwork
codex plugin add teamwork-skill@teamwork
```

然后开启新任务并运行 `$teamwork-update`。

Checkout 更新：

```bash
git pull --ff-only
./install.sh all
./scripts/check-update.sh --readiness
```

想收到新版本提醒，可以在 [JinPLu/Teamwork](https://github.com/JinPLu/Teamwork) 选择 **Watch → Custom → Releases**。提醒不会自动升级本地插件或配置。

---

## 🛡️ 安全边界

- 回答、调研、设计、计划、排错诊断和 review 默认只读；接受计划不等于授权执行。
- 安装器只删除能证明由 Teamwork 生成的条目。不要整体删除 `.agents`、`.codex`、`.cursor` 或 `.claude`。
- 启用 Codex 通知后，请重启 Codex，在 `/hooks` 中只信任 Teamwork 的 `Stop` 和 `PermissionRequest`，不要使用 trust-all。
- `./scripts/check-update.sh --readiness` 只检查 Teamwork 受管文件和配置；它不能代替 Cursor User Rules、hook 信任等宿主手动步骤。
- v4 没有旧 Router、Execute 或 legacy role alias；迁移只清理 Teamwork 能确认归属的旧文件。

---

## 📚 继续了解

- [更新日志](CHANGELOG.md)：各版本的用户可见变化与升级说明。
- [Codex](CODEX.md)、[Cursor](CURSOR.md)、[Claude Code](CLAUDE.md)：各平台完整配置和排错。
- [项目结构](docs/architecture.md)：源码、生成目录、依赖边界和稳定命令。
- [参与贡献](CONTRIBUTING.md)：修改范围和验证要求。
- [GitHub Issues](https://github.com/JinPLu/Teamwork/issues)：反馈问题或建议。
