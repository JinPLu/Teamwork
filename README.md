<p align="center">
  <img src="assets/teamwork-readme-teaser-v7.png" alt="Teamwork：清晰任务直接完成，需要方法时使用八个专门 Skills，并由八个 Agent 角色协作到可验证结果" width="860">
</p>

<h1 align="center">Teamwork</h1>

<p align="center">
  <strong>让 AI 在该直接做时直接做，在真正需要方法时再调用方法。</strong><br>
  面向 Codex、Cursor 和 Claude Code 的 AI/人类协作 Skills：更少仪式，更清楚的边界，更可信的结果。
</p>

<p align="center">
  <a href="https://github.com/JinPLu/Teamwork/releases"><img src="https://img.shields.io/github/v/release/JinPLu/Teamwork?display_name=tag&amp;sort=semver" alt="最新 Release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-2563EB" alt="MIT License"></a>
  <img src="https://img.shields.io/badge/platforms-Codex%20%C2%B7%20Cursor%20%C2%B7%20Claude%20Code-0F766E" alt="支持 Codex、Cursor 和 Claude Code">
</p>

<p align="center">
  <a href="README.en.md">English</a> ·
  <a href="CHANGELOG.md">更新日志</a> ·
  <a href="CODEX.md">Codex</a> ·
  <a href="CURSOR.md">Cursor</a> ·
  <a href="CLAUDE.md">Claude Code</a> ·
  <a href="docs/architecture.md">架构</a>
</p>

---

> [!TIP]
> **你不需要先背会八个 Skills。** 大多数时候，直接描述想要的结果。只有想精确选择讨论、调研、排错、计划或复查方法时，才点名 `$teamwork-*`。

## 🚀 一分钟开始

### Codex：推荐使用 Marketplace plugin

```bash
codex plugin marketplace add JinPLu/Teamwork
codex plugin add teamwork-skill@teamwork
```

开启一个新的 Codex 任务，运行：

```text
$teamwork-update
```

首次配置会让你选择 `performance-first` 或 `cost-first`，并分别决定是否启用受管 CodeGraph 与本地 GPU Broker。无论是否启用可选能力，Skills、Agents、路由和全局策略都会完整安装。

然后直接提出目标：

```text
实现这个校验改动，验证真实受影响路径，成功后停止。
```

目标和边界已经清楚时，Teamwork 不会先制造一个 workflow。想先一起判断方向，再这样说：

```text
用 $teamwork-collaborate 和我比较三个 onboarding 方向，先给建议，再问真正会改变选择的问题。
```

为一个新仓库创建当前格式的项目说明与 Teamwork 文档：

```text
用 $teamwork-init 初始化这个项目。
```

<details>
<summary><strong>Cursor、Claude Code 或开发 checkout</strong></summary>

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
./install.sh codex   # 仅用于开发或手动 Codex setup
```

使用较低成本配置：

```bash
./install.sh all --profile cost-first
```

Cursor 还需要运行 `./install.sh cursor-policy-copy`，再把内容粘贴到 **Cursor Settings → Rules → User Rules**。平台细节见 [Cursor 指南](CURSOR.md) 与 [Claude Code 指南](CLAUDE.md)。

</details>

## 🧭 当前缺什么，就用什么

| 你当前缺少 | 使用 | 它解决什么 |
| --- | --- | --- |
| 一个可接受的方向 | 💬 `$teamwork-collaborate` | 讨论、共创、比较、brainstorm，或帮助尚未形成的意图与偏好逐步清晰。 |
| 深入的外部或当前证据 | 🔎 `$teamwork-research` | 跨官方资料、论文或其他可靠来源调研，综合冲突证据并给出可追溯结论。 |
| 原因未知的失败 | 🐞 `$teamwork-debug` | 从真实失败出发，区分假设、确认根因，并只在已有权限时修复同一路径。 |
| 可执行的步骤 | 📝 `$teamwork-plan` | 把已经明确的方向转成 owner、依赖、验证和停止条件清楚的计划。 |
| 独立判断 | ✅ `$teamwork-review` | 审查稳定的代码、文档、计划、产物或结论，先给发现，再给 verdict。 |
| 持续推进到结果 | 🎯 `$teamwork-goal` | 仅在你明确要求时，持续工作到真实成功信号通过或出现真正阻塞。 |
| 当前格式的项目上下文 | 🧰 `$teamwork-init` | 初始化、审计、修复或瘦身一个明确项目根目录内的 Teamwork 配置。 |
| 全局刷新或旧文档迁移 | 🔄 `$teamwork-update` | 刷新全局 Teamwork；给出精确项目根目录时，一次性迁移其中全部旧 Teamwork 文档。 |

本地代码、配置、日志、测试和历史证据由内部 Explorer Agent 只读收集，不再暴露公共 Explore Skill。普通网页事实查询保持宿主原生；Research 只用于真正需要多源综合的外部问题。

## 🛣️ 四条最常用的路径

### 1. 目标与改法都清楚

```text
直接修改登录超时逻辑，只验证相关测试和真实登录路径。
```

**路径：** 宿主原生检查 → 修改 → 验证。

不需要 Router、Execute，也不需要先派发 Agent。

### 2. 方向还没有形成

```text
用 $teamwork-collaborate 比较同步、排队和混合三种 API 方案，帮我收敛到一个可接受方向。
```

**路径：** Collaborate → 用户接受方向 → 需要时进入 Plan → 再授权实现。

讨论、计划和接受方向本身都不授权修改代码。

### 3. 有失败，但原因未知

```text
用 $teamwork-debug 复现这个 CI 失败，确认根因后修复并重跑同一路径。
```

**路径：** Debug 诊断 → 窄修复 → 同路径验证。

如果根因和修复已经清楚，直接修，不必先走 Debug。

### 4. 决策依赖外部事实

```text
用 $teamwork-research 查官方文档和近期变更，给出带来源的建议。
```

**路径：** Research → 有来源的结论；只有仍存在真实选择时，才回到 Collaborate。

Review 是按需加入的独立验收门，Goal 是显式要求的持续推进器。两者都不是每个任务的默认步骤。

## 📋 可直接复制的提示词

```text
# 一起讨论
用 $teamwork-collaborate 和我 brainstorm 一个低维护成本的发布流程。先综合现状和真实选项，再问最有价值的问题。

# 深入调研
用 $teamwork-research 只查官方资料和关键论文，比较方案并给出可追溯引用。

# 只读检查本地证据
先别改文件。只读梳理认证流程、相关配置和测试，告诉我真正的修改边界。

# 排查失败
用 $teamwork-debug 复现这个错误，区分最可能的根因，确认后修复并验证同一路径。

# 做计划
用 $teamwork-plan 把已确定的迁移方向拆成 owner、依赖、验收条件和停止条件明确的步骤，不要执行。

# 独立复查
用 $teamwork-review 检查这个 diff 是否满足需求，重点寻找假成功、遗漏路径和过期文档。

# 持续到完成
用 $teamwork-goal 继续修到指定检查通过；只有遇到真实阻塞才停。
```

## 🧩 Skills、Agents 与宿主各自负责什么

| 层次 | 负责什么 | 你需要直接操作吗 |
| --- | --- | --- |
| ⚡ 宿主原生路径 | 完成清楚的解释、查询、本地检查、修改和验证。 | 是，直接描述结果。 |
| 🧭 八个公开 Skills | 在任务需要专门方法时，提供清楚的触发条件和工作方式。 | 可选；需要精确选择时点名。 |
| 🤝 八个内部 Agent 角色 | Researcher、Explorer、Debugger、Challenger、Planner、Reviewer、Worker、Writer。 | 通常不需要；Root 负责调度、集成与用户对话。 |

Challenger 只用于明确的严格对抗挑战。Reviewer 同时审查实现与计划。Teamwork 不规定固定 Agent 数量或每日派发上限，也不会因为任务重要、复杂或有风险就自动升级流程。

## 🗃️ 一项任务，一份 live document

当任务产生值得复用的内容时，Writer 为这项任务维护一份 live document：首次出现可复用内容时创建，证据、决定、结论或下一步实质变化时更新，任务结束时定稿。它不是逐轮 transcript，也不会把锁、事务、hash 或 readback 写进模型工作方法。

文件、工具、凭据与外部效果仍由 Codex、Cursor、Claude Code 及其权限控制。Teamwork 不建立第二套授权系统；讨论或接受计划也不等于授权执行。

> [!IMPORTANT]
> **Teamwork 7.0.0 不兼容旧设置或旧数据。** Update 是唯一旧格式迁移入口：给出精确项目根目录后，它迁移全部旧 Teamwork 文档；迁移验证完成后，正常运行只使用新格式，不保留旧 runtime reader。

刷新全局安装并迁移一个项目：

```bash
./install.sh --project-root /path/to/project update
```

没有精确项目根目录时，Update 只完成全局刷新，并明确报告 `project migration pending`。

## 🔄 更新

Codex plugin：

```bash
codex plugin marketplace remove teamwork
codex plugin marketplace add JinPLu/Teamwork
codex plugin add teamwork-skill@teamwork
```

然后开启新任务并运行 `$teamwork-update`。

Checkout：

```bash
git pull --ff-only
./install.sh all
./scripts/check-update.sh --readiness
```

想收到新版本提醒，可以在 [JinPLu/Teamwork](https://github.com/JinPLu/Teamwork) 选择 **Watch → Custom → Releases**。

## 📚 继续了解

- [更新日志](CHANGELOG.md)：用户可见变化和升级说明。
- [Codex](CODEX.md)、[Cursor](CURSOR.md)、[Claude Code](CLAUDE.md)：平台安装、配置与排错。
- [架构](docs/architecture.md)：四层模型、canonical owners、存储与发布证据。
- [参与贡献](CONTRIBUTING.md)：修改约定与验证命令。
- [GitHub Issues](https://github.com/JinPLu/Teamwork/issues)：反馈问题或建议。
