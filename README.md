<p align="center">
  <img src="assets/teamwork-readme-teaser-v5.png" alt="Teamwork README teaser：普通工作走宿主原生路径，需要专门方法时调用 10 个 Teamwork skills 和 9 个可选 agent 角色" width="760">
</p>

<h1 align="center">Teamwork</h1>

<p align="center">
  <strong>给 Codex、Cursor 和 Claude Code 的聚焦协作技能包。</strong><br>
  Teamwork 不接管普通本地工作：清楚的查代码、改文件和验证继续走宿主原生路径。它在任务需要专门方法时接上 10 个可点名能力，处理外部调研、本地证据、方案设计、未知失败排查、计划、只读复查、持久目标、项目初始化和全局更新。
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

## ✨ 它到底做什么

Teamwork 是一套按需调用的协作方法，而不是一个接管宿主的总控层。v4 已经移除旧的 Router / Execute：清楚、已授权的本地实现继续由 Codex、Cursor 或 Claude Code 直接完成；只有任务真的需要更强约束时，才进入对应 Skill。

| 层次 | 负责什么 |
| --- | --- |
| 宿主原生路径 | 读本地代码、配置、测试、日志和 artifact；完成清楚授权的修改；运行真实验证。 |
| 10 个公开 Skills | 给调研、证据、设计、排错、计划、复查、持久目标、讨论挑战、项目初始化和全局更新提供明确方法。 |
| 9 个可选 agent 角色 | 在 Codex、Cursor、Claude Code setup 中承担 Researcher、Explorer、Debugger、Designer、Planner、Worker、Writer、Plan Reviewer 和 Reviewer；主任务仍负责范围、集成和最终回复。 |

## 🗃️ 文档与持久化

已初始化且可写的项目进入命名 Teamwork workflow 后，默认会把可复用结果写成对应 artifact，并登记到 `docs/teamwork/index.json`；明确 `no files`、off-record、read-only/no-write 会覆盖这个默认。普通澄清或聊天、未进入 Teamwork workflow 的一次性 native work，以及清楚的代码实现请求，不会因为安装了 Teamwork 就强制生成额外 workflow artifact。

Writer 只根据 Root 或强角色给出的 frozen bounded brief 成文：可起草、改写、整理、摘要、翻译和润色独立文档或 runtime artifact，但不能研究、发明或改变事实、引用、决策、权限、状态、验收结论，也不能自验收。代码耦合的注释、docstring、测试、schema、manifest、机器配置和配置内说明仍归写代码的 Worker 或对应实现所有者。

Grill、Design 和 Goal 分别使用各自的专用事务；Research、Debug、Plan、Review 以及会产生变更的 Init/Update 使用 generic artifact transaction。Explore 不独立造报告，证据并入消费它的 artifact 或答复。

| 工作流 | 默认是否落盘 | 主要产物 | 之后怎么消费 |
| --- | --- | --- | --- |
| 普通澄清或聊天 / 一次性 native work | 否 | 无强制 artifact | 只按当前对话和宿主原生上下文继续。 |
| Grill | 是，除非 no files/off-record/read-only/no-write | 受控 discussion | 继续同一重大讨论、恢复 frontier/current_batch。 |
| Research | 是 | research | 作为 Design、Plan、Review、文档或最终答复的引用证据。 |
| Design | 是；落盘不代表接受 | 带 `pending`、`accepted` 或 `blocked` acceptance 的受控 design state | 只有 `accepted` 才能进入 Plan；`pending` / `blocked` 只保留为设计证据，旧 v1/v2 兼容按 `accepted` 读取。 |
| Plan | 是 | canonical plan | Worker/Root 按 owner、路径、验证和停止条件执行。 |
| Debug | 是 | diagnosis/report | Worker 或 Root 用根因、修复边界和同路径验证继续。 |
| Review | 是，落盘不代表验收 | verdict/conclusion | Root 用 `ACCEPT` / `REVISE` / `BLOCKED` 决定修复或收口。 |
| Goal | 是 | 既有 entry/attempt/status | 后续回合按目标、预算、成功信号和阻塞状态续跑。 |
| mutating Init / Update | 是 | receipt | 后续 readiness、排错和用户复核使用。 |
| Explore | 否 | 不独立造报告 | 本地证据并入消费它的 Design、Plan、Debug、Review、Goal 或答复。 |

| 你遇到的情况 | 推荐用法 |
| --- | --- |
| 本地改动已经清楚 | 直接描述目标，不需要点名 Teamwork。 |
| 需要当前外部事实、官方资料、论文或引用 | 用 `$teamwork-research`。 |
| 需要只读梳理本地代码、配置、日志、测试、历史或 artifact | 用 `$teamwork-explore`。 |
| 产品、架构、流程或 API 方向还没选定 | 直接描述问题；Teamwork Design 会自己选择普通挑战或对抗搜索。需要先被追问关键决定时用 `$grill-me`。 |
| 失败原因未知，不能安全下手修 | 用 `$teamwork-debug`。 |
| 受控 Design 已是 `accepted`，需要拆成可执行步骤 | 用 `$teamwork-plan`。 |
| 计划、diff、artifact 或完成声明需要独立验收 | 用 `$teamwork-review`。 |
| 你明确要求持续修到通过、修到绿或预算化目标 | 用 `$teamwork-goal`。 |
| 要初始化一个项目或刷新全局安装 | 分别用 `$teamwork-init` 和 `$teamwork-update`。 |

## 🛡️ 它守住什么边界

| 你不想要 | Teamwork 的做法 |
| --- | --- |
| 🔁 一直测试、一直复查，却不交付 | 先拿真实结果；测试和 review 只服务于改动路径或明确风险门。 |
| 🧱 小事也被套复杂流程 | 简单问答、小修改、清楚实现直接做，不强制走 Teamwork。 |
| 🕳️ 凭空补路径、端口、模型或状态 | 先看项目、日志、配置、官方资料和实际输出。 |
| ❓ 问一堆无关问题 | 先展示全局决策地图；只把彼此独立的关键决定放在同一批次，有依赖的问题分轮问。 |
| 🧑‍⚖️ review 替代执行 | Review 默认只读，只给有证据的 `ACCEPT` / `REVISE` / `BLOCKED`。 |

---

## 🧩 10 个能力，按需要点名

平时直接描述目标即可；需要精确控制工作方式时，再显式调用 Skill。

| 能力 | 用在什么时候 |
| --- | --- |
| 🔎 `$teamwork-research` | 查外部现状、官方资料、论文、市场信息或需要引用的事实。 |
| 🗂️ `$teamwork-explore` | 只读查看本地代码、配置、日志、测试、历史或 artifact，给出证据结论。 |
| 🧭 `$teamwork-design` | 方案、架构、产品或流程还有真实取舍；模型会自动选择普通挑战或预算化对抗搜索，`adversarial` / `standard` 可强制覆盖。 |
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
这个公开 API 可选同步、排队或混合；选错会让所有客户端付出昂贵迁移成本，而且延迟与可靠性证据互相冲突。请帮我决定。
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

完整 Codex setup 会安装 9 个自定义 agent：Researcher、Explorer、Debugger、Designer、Planner、Worker、Writer、Plan Reviewer 和 Reviewer。它们只在拆分上下文、独立文档书写或独立验收真的有价值时使用；主任务仍负责范围、集成和最终回复。Writer 使用简单模型，负责普通项目/产品文档、README/指南/架构/变更与发布说明，以及 Teamwork runtime artifacts；代码、代码注释、docstring、测试、schema、manifest、机器配置和配置内说明仍由实现角色维护。

| Profile | 高频执行角色 | 文档 Writer | 设计 / 计划复查 | 最终复查 |
| --- | --- | --- | --- | --- |
| `performance-first` | `gpt-5.5` / `high` | `gpt-5.5` / `low` | `gpt-5.6-sol` / `high` | `gpt-5.6-sol` / `max` |
| `cost-first` | `gpt-5.5` / `medium` | `gpt-5.5` / `low` | Designer 为 `gpt-5.6-sol` / `medium`；Plan Reviewer 为 `gpt-5.6-sol` / `high` | `gpt-5.6-sol` / `high` |

这个分配把常见的证据查找、排错、计划和实现交给更快的执行模型，把独立文档表达交给简单 Writer，把重大取舍和独立验收留给更保守的 reviewer 模型。Writer 可以组织、重写、摘要、翻译和润色表达，但不能研究、发明事实、改变引用/决策/权限/状态/验收结论或自验收。

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

- Research、Design、Plan、排错诊断和 Review 不授权修改候选代码或产生外部效果；命名 workflow 的可复用结果仍按上面的矩阵默认持久化，接受 Plan 也不等于授权执行。
- Design 只在至少两个可行方向仍成立，且错误代价高、难以逆转或证据冲突使一次普通挑战不足时自动升级到 adversarial；只写“高风险”“复杂”不会触发。模型说明选择理由并直接使用默认 `B=3`，无需再次确认；`adversarial` / `standard` 可强制覆盖。每个实际假设使用两名全新批评者，最后两名全新审计者必须同时通过；Design v3 始终显式记录 `acceptance: pending`、`accepted` 或 `blocked`。隔离或收敛不可证明时只能保持 `pending` 或记为 `blocked`，不能成为 Plan-ready；落盘不等于接受，只有 `accepted` 才能进入 Plan。
- 普通澄清不会触发 Grill，也不会落盘；点名或进入 Grill、继续已有 Grill，或独立重大边界触发 Grill 后，默认通过专用事务只更新 `docs/teamwork/discussion/current.md`，除非 `no files`、off-record、read-only/no-write 覆盖。新记录使用 `frontier` / `current_batch` 状态，不会复制到普通 memory。
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
