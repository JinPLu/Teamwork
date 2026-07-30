<p align="center">
  <img src="assets/teamwork-readme-teaser-v5.png" alt="Teamwork README teaser：普通工作走宿主原生路径，需要专门方法时调用 9 个 Teamwork skills 和 9 个可选 agent 角色" width="760">
</p>

<h1 align="center">Teamwork</h1>

<p align="center">
  <strong>给 Codex、Cursor 和 Claude Code 的聚焦协作技能包。</strong><br>
  Teamwork 不接管普通本地工作：清楚的查代码、改文件和验证继续走宿主原生路径。它在任务需要专门方法时接上 9 个可点名能力，处理协作收敛、外部调研、本地证据、未知失败排查、计划、只读复查、持久目标、项目初始化和全局更新。
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

Teamwork 是一套按需调用的协作方法，而不是一个接管宿主的总控层。v5 会更积极地识别讨论、方案收敛和可复用中间结果：自然讨论、一起想、brainstorm、grill、压力测试、行动前先提问，或产品/架构/API 方向还没定，都会进入 Collaborate，并从目标和证据自选 `dialogue`、`brainstorm` 或 `grill`；清楚、已授权的本地实现仍由 Codex、Cursor 或 Claude Code 直接完成。

| 层次 | 负责什么 |
| --- | --- |
| 宿主原生路径 | 读本地代码、配置、测试、日志和 artifact；完成清楚授权的修改；运行真实验证。 |
| 9 个公开 Skills | 给协作收敛、调研、证据、排错、计划、复查、持久目标、项目初始化和全局更新提供明确方法。 |
| 9 个可选 agent 角色 | 在 Codex、Cursor、Claude Code setup 中承担 Researcher、Explorer、Debugger、Designer、Planner、Worker、Writer、Plan Reviewer 和 Reviewer；主任务仍负责范围、集成和最终回复。 |

## 🗃️ 文档与持久化

已初始化且可写的项目进入命名 Teamwork workflow 后，默认会把可复用的中间检查点和完成结果写成对应 artifact，并登记到 `docs/teamwork/index.json`；明确 `no files`、off-record、read-only/no-write 会覆盖这个默认。一次性说明、随口事实问题和很小的 native work 不会强制造文档；但持续讨论已经形成实质综合且仍有未决问题时，会默认保存一份语义检查点。

Teamwork 5.1 对新初始化的项目启用 v2 case bundle。一个 case 成为持久文档单元，集中承接 live collaboration、已接受决定、计划、证据、复查、Goal 状态和结果，路径位于 `docs/teamwork/cases/c-<64hex>/`。已有项目在明确授权单向 cutover 前继续走 legacy-v1 路由；安装或更新 Teamwork 本身不会迁移、改写或删除项目文档。

Writer 只根据 Root 或强角色给出的 frozen bounded packet 成文：可起草、整理、摘要、翻译和润色独立文档或 runtime artifact，但不能研究、发明、转述或改变冻结事实、引用、决策、权限、状态、验收结论，也不能自验收；内容缺口必须失败关闭并报告未保存。代码耦合的注释、docstring、测试、schema、manifest、机器配置和配置内说明仍归写代码的 Worker 或对应实现所有者。

持久化先读 `docs/teamwork/index.json` 决定 schema：v2 项目中 Collaborate、Research、Debug、Plan、Plan Review、Review、Goal、会产生变更的 Init/Update，以及满足条件的终态执行交接都写入 case transaction / case artifact；legacy-v1 项目中 Collaborate 和 Goal 继续使用各自专用事务，Research、Debug、Plan、Plan Review、Review、会产生变更的 Init/Update 与终态执行交接继续使用既有 generic artifact transaction。Writer 只根据冻结内容调用事务，事务才是实际文件写入者。Explore 不独立造报告，证据并入消费它的 artifact 或答复。

| 工作流 | 默认是否落盘 | 主要产物 | 之后怎么消费 |
| --- | --- | --- | --- |
| 一次性说明、随口事实问题或很小的 native work | 否 | 无强制 artifact | 只按当前对话和宿主原生上下文继续。 |
| Collaborate | 达到“持续协作 + 实质综合/候选空间/决策地图 + 未决问题或未接受方向”即默认落盘 | v2 case live collaborate/decision；legacy-v1 受控 Collaborate | 恢复同一协作；v2 从 case manifest 继续，legacy-v1 从 current record 继续；被接受后成为 Plan 的唯一公共入口。旧 Discussion/Design 只作为只读迁移输入。 |
| Research | 是 | v2 case evidence；legacy-v1 research artifact | 作为 Collaborate、Plan、Review、文档或最终答复的引用证据。 |
| 方案收敛 | 由 Collaborate 承接 | Collaborate 中的 `pending`、`accepted` 或 `blocked` acceptance | 只有 accepted Collaborate 能进入 Plan；内部 Designer 只读参与方向选择、挑战或收敛审计。 |
| Plan | 是 | v2 case plan；legacy-v1 canonical plan | Worker/Root 按 owner、路径、验证和停止条件执行。 |
| Debug | 是 | v2 case evidence/result；legacy-v1 diagnosis/report | Worker 或 Root 用根因、修复边界和同路径验证继续。 |
| Plan Review / Review | 是，落盘不代表验收 | v2 case review/delta；legacy-v1 review | Root 用证据结论决定修复、重做计划或收口。 |
| Goal | 是 | 既有 entry/attempt/status | 后续回合按目标、预算、成功信号和阻塞状态续跑；Goal 激活期间不再重复创建 execution artifact。 |
| Native / Worker 执行 | 仅在有明确下游消费者、终态交接且没有 active Goal 时 | execution | 把已完成结果交给指定的 Plan、Review、发布或其他真实消费者。 |
| mutating Init / Update | 是 | receipt | 后续 readiness、排错和用户复核使用。 |
| Explore | 否 | 不独立造报告 | 本地证据并入消费它的 Collaborate、Plan、Debug、Review、Goal 或答复。 |

Collaborate 只能写到专用 collaborate 路由，不能拿普通 report、conclusion、旧 Discussion 或旧 Design 代替；execution 也不能拿 conclusion 代替。只有用户确实要求一份独立综合文档时，才使用 conclusion。

cutover 期间，旧文档只作为迁移输入，之后作为 cold archive 来源。cold archive 只保存字节和 POSIX mode，不是物理备份；Teamwork 不会自动删除冷归档对象。

| 你遇到的情况 | 推荐用法 |
| --- | --- |
| 本地改动已经清楚 | 直接描述目标，不需要点名 Teamwork。 |
| 需要当前外部事实、官方资料、论文或引用 | 用 `$teamwork-research`。 |
| 需要只读梳理本地代码、配置、日志、测试、历史或 artifact | 用 `$teamwork-explore`。 |
| 想一起讨论、brainstorm、逐步收敛，或希望行动前先被提问/压力测试 | 直接描述意图或用 `$teamwork-collaborate`；它会自选 dialogue、brainstorm 或 grill。 |
| 产品、架构、流程或 API 方向还没选定，需要形成可接受方向 | 直接描述问题或用 `$teamwork-collaborate`；必要时会调用内部只读 Designer 做普通挑战或对抗搜索。 |
| 失败原因未知，不能安全下手修 | 用 `$teamwork-debug`。 |
| 受控 Collaborate 已是 `accepted`，需要拆成可执行步骤 | 用 `$teamwork-plan`。 |
| 计划、diff、artifact 或完成声明需要独立验收 | 用 `$teamwork-review`。 |
| 你明确要求持续修到通过、修到绿或预算化目标 | 用 `$teamwork-goal`。 |
| 要初始化一个项目或刷新全局安装 | 分别用 `$teamwork-init` 和 `$teamwork-update`。 |

## 🛡️ 它守住什么边界

| 你不想要 | Teamwork 的做法 |
| --- | --- |
| 🔁 一直测试、一直复查，却不交付 | 先拿真实结果；测试和 review 只服务于改动路径或明确风险门。 |
| 🧱 小事也被套复杂流程 | 简单问答、小修改、清楚实现直接做，不强制走 Teamwork。 |
| 🕳️ 凭空补路径、端口、模型或状态 | 先看项目、日志、配置、官方资料和实际输出。 |
| ❓ 问一堆无关问题 | 先给综合、候选空间或建议；开放问题用文字，只在确有 2–3 个互斥选项时调用宿主原生选择界面。有依赖的问题分轮问。 |
| 🧑‍⚖️ review 替代执行 | Review 默认只读，只给有证据的 `ACCEPT` / `REVISE` / `BLOCKED`。 |

---

## 🧩 9 个能力，按需要点名

平时直接描述目标即可；需要精确控制工作方式时，再显式调用 Skill。

| 能力 | 用在什么时候 |
| --- | --- |
| 🔎 `$teamwork-research` | 查外部现状、官方资料、论文、市场信息或需要引用的事实。 |
| 🗂️ `$teamwork-explore` | 只读查看本地代码、配置、日志、测试、历史或 artifact，给出证据结论。 |
| 💬 `$teamwork-collaborate` | 一起讨论、brainstorm、grill/压力测试、行动前先问，或让未定方案收敛成可接受方向；自动选择 dialogue、brainstorm 或 grill，并在达到语义门槛时保存检查点。 |
| 🐞 `$teamwork-debug` | 失败原因未知，需要复现、区分假设，再确认修复。 |
| 📝 `$teamwork-plan` | 方向已定，需要拆成 owner、依赖、验收和停止条件清楚的步骤。 |
| ✅ `$teamwork-review` | 检查计划、diff、artifact 或完成声明是否真的成立。 |
| 🎯 `$teamwork-goal` | 你明确要求“继续到通过”“修到绿”或给出预算化目标。 |
| 🧰 `$teamwork-init` | 为一个仓库设置项目说明、Teamwork memory 入口和可用 CodeGraph 上下文。 |
| 🔄 `$teamwork-update` | 检查或刷新全局 Teamwork skills、agents、策略、路由和通知。 |

示例：

```text
用 $teamwork-research 查官方资料和关键论文，给出可追溯建议。
用 $teamwork-collaborate 和我一起 brainstorm 一个更低维护成本的 onboarding 流程。
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

| Profile | 高频执行角色 | 文档 Writer | Collaborate / 计划复查 | 最终复查 |
| --- | --- | --- | --- | --- |
| `performance-first` | `gpt-5.5` / `high` | `gpt-5.5` / `low` | `gpt-5.6-sol` / `high` | `gpt-5.6-sol` / `max` |
| `cost-first` | `gpt-5.5` / `medium` | `gpt-5.5` / `low` | Designer 为 `gpt-5.6-sol` / `medium`；Plan Reviewer 为 `gpt-5.6-sol` / `high` | `gpt-5.6-sol` / `high` |

这个分配把常见的证据查找、排错、计划和实现交给更快的执行模型，把独立文档表达交给简单 Writer，把重大取舍和独立验收留给更保守的 reviewer 模型。Writer 可以组织、摘要、翻译和润色表达，但不能研究、发明事实、转述或改变冻结的引用/决策/权限/状态/验收结论或自验收。

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

- Research、Collaborate、Plan、排错诊断和 Review 不授权修改候选代码或产生外部效果；命名 workflow 的可复用结果仍按上面的矩阵默认持久化，接受 Plan 也不等于授权执行。
- Collaborate 只在至少两个可行方向仍成立，且错误代价高、难以逆转或证据冲突使一次普通挑战不足时，才通过内部只读 Designer 自动升级到 adversarial；只写“高风险”“复杂”不会触发。模型说明选择理由并直接使用默认 `B=3`，无需再次确认；`adversarial` / `standard` 可强制覆盖。每个实际假设使用两名全新批评者，最后两名全新审计者必须同时通过；Collaborate v1 始终显式记录 `acceptance: pending`、`accepted` 或 `blocked`。隔离或收敛不可证明时只能保持 `pending` 或记为 `blocked`，不能成为 Plan-ready；落盘不等于接受，只有 `accepted` 才能进入 Plan。
- 自然讨论、一起想、brainstorm、grill、压力测试或“行动前先问我”会更积极地触发 Collaborate；它先给有用综合、候选空间、决策地图或临时建议，再按问题形态提问。grill 严格按 global → boundary → detail 推进，每批最多提出三个彼此独立的决定，依赖决定分轮处理；每个已回答批次只形成一次完整语义更新。开放问题保留为文字，只有真实有限的 2–3 个互斥选择才使用 Codex 原生询问界面；宿主必须实际暴露 `request_user_input`。达到持续协作语义门槛后，默认先读 `docs/teamwork/index.json` 决定 schema：v2 通过 Writer 和 case transaction 更新所选 case 的 `live/collaborate.md`，只有 legacy-v1 继续通过 Collaborate transaction 维护 `docs/teamwork/collaborate/current.md`；若宿主未提供 Writer、路由或 readback，必须明确报告未保存，禁止 Root 伪装成已落盘。记录不保存逐字对话，也不复制成 report/conclusion 或旧 Discussion/Design；`no files`、off-record、read-only/no-write 始终优先。
- 安装器只删除能证明由 Teamwork 生成的条目。不要整体删除 `.agents`、`.codex`、`.cursor` 或 `.claude`。
- 启用 Codex 通知后，请重启 Codex，在 `/hooks` 中只信任 Teamwork 的 `Stop` 和 `PermissionRequest`，不要使用 trust-all。
- `./scripts/check-update.sh --readiness` 只检查 Teamwork 受管文件和配置；它不能代替 Cursor User Rules、hook 信任等宿主手动步骤。
- v5 移除了公开 `$grill-me`、`$teamwork-discuss` 和 `$teamwork-design` 名称，由 `$teamwork-collaborate` 统一承接三种协作模式与可接受方向收敛；Router、Execute 和 legacy role alias 也仍不存在。升级只清理 Teamwork 能用精确内容证明归属的旧 Grill/Discuss/Design/Router/Execute 文件；改过或无所有权标记的副本会被保留并阻止自动替换，不会创建别名。
- v5.1 保持 legacy-v1 项目 memory 兼容，同时让新项目使用 v2 case bundle。cutover 是单独、明确授权、单向的操作；update/install 本身不得改写现有 `docs/teamwork` 文档。

---

## 📚 继续了解

- [更新日志](CHANGELOG.md)：各版本的用户可见变化与升级说明。
- [Codex](CODEX.md)、[Cursor](CURSOR.md)、[Claude Code](CLAUDE.md)：各平台完整配置和排错。
- [项目结构](docs/architecture.md)：源码、生成目录、依赖边界和稳定命令。
- [参与贡献](CONTRIBUTING.md)：修改范围和验证要求。
- [GitHub Issues](https://github.com/JinPLu/Teamwork/issues)：反馈问题或建议。
