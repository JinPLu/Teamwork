# 更新日志

[English](CHANGELOG.en.md)

Teamwork 的重要变更记录，按 git 历史整理。日期使用提交日期。版本边界以
`VERSION` 和插件 manifest 的更新为准；当前仓库没有 git release tag。

## 2.6.0 - 2026-06-23

- 强化 broad / seeded research：用户提供的文章、论文、URL、仓库或报告会被
  视为研究种子，而不是研究边界。
- 将 AI 代码质量规则统一为“禁止静默默认值或掩盖不变量的 fallback”，并贯穿
  workflow、plan、execute、debug、review 和 subagent contract。
- 明确 routine 可逆默认值仍然允许，但代码/运行时默认值和 fallback 不能隐藏
  缺失的必需值或不变量。
- 扩展 review lenses 和 validation anchors，覆盖 bounded deslop、strict
  maintainability、fail-fast checks，并防止新增 `teamwork-quality` 或
  `teamwork-deslop` 阶段。
- 在 Codex、Cursor、Claude Code 和 installer 生成的全局策略中同步新的
  bootstrap safety 规则。

## 2.5.0 - 2026-06-22

- 强化 goal continuity workflow，补足 Goal Anchor、Replay Preflight、Drift
  Verdict、Retry Verdict 和 attempt record 的要求。
- 扩展 goal artifacts、Teamwork index templates 和 lifecycle verdict 的验证覆盖。
- 新增 `scripts/init-project.sh`，改进 project initialization 默认值、artifact
  结构和项目级安装行为。

## 2.4.1 - 2026-06-21

- 新增 `./install.sh cursor-policy-copy`，用于把 Cursor User Rules 策略文本复制
  到剪贴板。
- 更新 Cursor install、init、check-update 和 validation 文档，明确 Cursor User
  Rules 仍需要手动粘贴。

## 2.4.0 - 2026-06-21

- 新增 `routing-policy.md`，提供更智能的 stage routing。
- 调整 router 和 stage 描述，覆盖 native、research、debug、plan、execute、
  review、goal、init 和 update 工作流。

## 2.3.0 - 2026-06-21

- 新增 `teamwork-debug` 阶段，用于在 speculative fix 前先做 runtime diagnosis。
- 新增 `debug-mode.md`、`verification-patterns.md` 和 `review-lenses.md`，覆盖
  repro evidence、proof strength、strict maintainability 和 deslop review。
- 围绕 debug evidence 和 cleanup 扩展 plan、execute、review、worker 和 agent
  templates。
- 修复 `scripts/check-update.sh` 的 upstream remote 检测。

## 2.2.0 - 2026-06-16

- 新增 `scripts/check-update.sh`，用于安装新鲜度和 readiness 检查。
- 新增 installed-version markers、`--project-root` 和更完整的项目级安装支持。
- 扩展 Codex、Cursor、Claude Code 的 agents、policy blocks、manifests、docs
  和 validation，提升多平台一致性。

## 2.0.0 - 2026-06-16

- 将 Teamwork 收敛到 act-by-default routing：明确任务直接推进，只在真正的
  blocker 或核心决策上提问。
- 用聚焦的 dispatch、contract 和 role playbook references 取代分散的
  subagent references。
- 精简 validation，同时保留 package layout、manifest、skill、memory、platform
  和 install-smoke 检查。

## 1.11.0 - 1.15.0 - 2026-06-11 to 2026-06-16

- 扩展 `teamwork-update` 的 package refresh 行为和 validation 覆盖。
- 让 skills 更 progressive，只在需要时加载聚焦 reference。
- 新增 Explorer 和 deep research packets 的 research context budget 规则。
- 新增 optional docs MCP policy，用于查询当前 library/API 文档。
- 在 2.0 consolidation 前细化 question-first routing。

## 1.5.0 - 1.10.0 - 2026-06-05

- 强化 durable memory policy、clarification gates、evidence-first fallback
  positioning、rule placement 和 role fan-out guidance。
- 新增 full-feature memory / init gates，以及 external-memory promotion 防护。
- 新增 fail-fast no-defaults guidance，并在保留 reviewability 的同时精简
  workflow overhead。

## 1.2.0 - 1.4.1 - 2026-06-04 to 2026-06-05

- 新增 install-time Codex model profiles，支持 `performance-first` 和
  `cost-first` 模式。
- 优化 Codex custom agent 的默认模型，并强化 role workflows。

## 1.0.0 - 1.1.2 - 2026-06-01 to 2026-06-04

- 细化 Teamwork orchestration 和 workflow reference 结构。
- 新增 delegated-track lifecycle closure contracts。
- 更新 Codex Worker model mapping。
- 新增 runtime README pointer guidance。

## 0.14.0 - 2026-06-01

- 在 `~/.codex/AGENTS.md` 中安装 Teamwork 管理的全局策略块。
- 让 Codex standing subagent authorization 可以跨项目复用。

## 0.13.0 - 2026-05-31

- 更新 Codex subagent authorization policy。

## 0.12.0 - 2026-05-28

- 增加 Claude Code parity，包括 Claude plugin metadata、`CLAUDE.md`、Claude
  install targets 和 Claude agent templates。
- 扩展 validation，覆盖 Claude manifests、skill installs 和 agent templates。

## 0.11.0 - 2026-05-27

- 增加 Cursor platform parity，包括 `CURSOR.md`、Cursor install support、Cursor
  Task subagent mapping 和 Cursor goal-mode 文档。
- 将文档从 Codex-only 行为重塑为 platform-native capabilities 叙事。

## 0.10.0 - 2026-05-27

- 新增 dispatch discovery gates，避免过早宣称 subagents 不可用。
- 对 non-lightweight acceptance paths 要求显式 dispatch exception 和
  fresh-review labeling。

## 0.9.0 - 2026-05-27

- 发布第一个带版本号的 Teamwork workflow-gates package。
- 通过 `teamwork-init` 和 project-init references 增加 project initialization
  workflow 支持。
- 建立 Codex-only Teamwork package 和 versioned metadata。
- 将 workflow 职责拆分为 research、planning、execution、review、goal
  iteration、init、update 和 auto-routing 等聚焦 skills。
- 增加 evidence-first goal/runtime gates、durable artifacts 和 review-oriented
  acceptance behavior。
- 增加并细化 automatic subagent routing，包括 independent-track dispatch、
  packet contracts 和 model-aware routing。

## Pre-0.9.0 - 2026-05-12 to 2026-05-26

- 最初作为 `run-analyze-optimize` skill package 创建。
- 将原始 package 重构为 research、plan、execute、goal 和 review router
  subskills。
- 增加 goal runtime commands、evidence gates、durable plan artifacts 和 Codex
  auto-routing。
- 将 package 重命名为 Teamwork，并在后续多平台支持前先收敛为 Codex-first
  skill package。
