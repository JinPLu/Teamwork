# 更新日志

[English](CHANGELOG.en.md)

这份 changelog 按“用户升级后会感受到什么”来写，而不是只罗列文件改动。
版本边界以 `VERSION` 和插件 manifest 的更新为准；当前仓库没有 git release tag。

## 2.11.1 - 2026-07-08

这版重点是：**补实 question-first / grill-me 和轻量直做之间的优先级边界。**

- 轻量任务仍默认直接做，但 `using-teamwork` 和 routing policy 现在明确写出：显式
  `grill-me` / question-first 会先于轻量 fast path 生效。
- 新增“简单任务 + 显式 grill-me”的 eval fixture，防止一行 typo 这类任务绕过
  question-first override。
- 轻量控制样本的验证更严格：现在会拒绝额外问题、grill ceremony、subagent dispatch
  和 durable plan，而不是只看少量关键词。
- Init/update skill 增加 active grill/question-first 的维护入口保护，避免在安装或发版任务中继续改动。

## 2.11.0 - 2026-07-08

这版重点是：**question-first / grill-me 变成跨阶段交互协议，并且安装面漂移检查更可信。**

- 复杂、不确定或非轻量任务现在会在计划/执行前先问会改变结果的决策/风险问题；显式
  `grill-me` / question-first 会先检查可发现事实，只问一个带推荐答案的问题，然后停止等待确认或退出。
- Research、debug、plan、execute、review、goal、init、update，以及 Codex/Cursor/Claude
  的 Explorer、Designer、Judge、Worker、Reviewer 模板都同步了 question-first override guard。
- 新增 question-first eval fixtures 和三平台静态样本，覆盖显式 grill、普通复杂不确定任务、轻量任务不过度拷问三类场景；文档明确这些是离线 fixture/static-sample gate，不声称证明 live model 行为。
- `check-update.sh` 现在按 installer profile 渲染 expected agent 文件并逐文件比较，readiness 和普通 report 都能发现 global/project agent 内容漂移。
- 更新/初始化命令修正为可直接运行：project-local 刷新使用 `--project-root`，profile 示例带 `<profile> <target>`，policy 输出目标不再改写 checkout 的 `.teamwork-profile`。
- 新增 `gpt55-high` profile，可把 Codex Teamwork subagents 固定到 gpt-5.5 high reasoning。

## 2.10.0 - 2026-07-08

这版重点是：**Teamwork 有了可复用的 SkillOpt-Lite/HarnessOpt-Lite 候选闭环底座。**

- 新增 `scripts/optimize-teamwork.py`：可以初始化优化工作区、把结果 JSONL 导出成
  file-native markdown samples、汇总分数，并用 deterministic gate 判断候选是否接受。
- `scripts/eval-teamwork.py` 新增可选的 `optimizer-candidates.jsonl` schema 和
  `--optimizer-ledger` 独立校验入口；真实候选必须包含 provider/model/config、baseline/treatment、
  rollback、validation、reviewer 等证据，不能用 `not_applicable` 占位。
- `scripts/validate.sh` 现在覆盖 optimizer helper、有效/无效候选 ledger、score 和 gate smoke，
  同时保持临时文件清理干净。
- Review/update/eval gate 规则明确：只有具备 trajectory samples、同案 baseline/treatment、
  gate、rollback、ledger、release audit 和 fresh review 时，才可以声称实际
  SkillOpt-Lite/HarnessOpt-Lite 参与。
- 这版提供可验证的优化管线底座；尚不把 scaffold 本身声明为一次真实 optimizer pilot。

## 2.9.0 - 2026-07-08

这版重点是：**Teamwork 开始用 file-native harness 约束和优化自己的 skill 行为。**

- 新增 `evals/teamwork/`：用 tracked cases、rubrics 和 ledgers 保存可复用的行为期望，
  覆盖轻量任务不过度流程化、复杂编码、debug、research、review、goal、release gate 和跨平台范围。
- 新增 `scripts/eval-teamwork.py`：离线、无模型依赖地校验 eval fixture、dev/release split、
  target surface、rubric 和 ledger schema。
- `scripts/validate.sh` 现在会检查 eval harness inventory，并运行 dev split，避免 skill/harness
  资产漂移。
- 新增 `eval-gate.md`，明确 eval 是维护证据而不是新的 runtime stage；普通轻量任务不会被强制跑 eval。
- `teamwork-review` 和 `teamwork-update` 现在要求 package behavior / release 变更引用 eval、ledger
  和非空 release split 证据，避免只靠主观感觉接受 skill 改动。

## 2.8.1 - 2026-07-08

这版重点是：**grill mode 和代码维护规则真的进入所有关键执行入口。**

- `grill me` 现在会暂停 research synthesis、design selection、goal handoff、
  edit 和 planning/design/execution agent dispatch，而不只是暂停 plan/implementation。
- Research、plan、goal、review、Designer、Judge、Worker、Reviewer 的规则同步了
  Shared Understanding Packet 前置锁，避免还没确认就开始综合、选方案或派工。
- 代码维护规则改成每条 code write path 的前置条件：先理解 owner、control flow、
  tests/config 和 invariants，再修改当前路径；Reviewer 对每个 code diff 都检查这条基线。
- `check-update.sh` 和 validation 现在会检查 policy 与 agent 内容锚点，能发现 installed
  global/project surfaces 仍是旧规则的情况。
- Codex、Cursor、Claude Code 的全局策略、agent 模板和 project-local 安装面都同步了这套规则。

## 2.8.0 - 2026-07-08

这版重点是：**显式要求“先拷问我”时，Teamwork 会真的先问清楚。**

- 新增 explicit grill/question-first 协议：当用户说 grill me、先问清楚、challenge assumptions
  或 ask before acting 时，Teamwork 必须先提出至少一个决策/风险问题并给出推荐答案。
- grill mode 会暂停 plan、implementation、goal start 和 Worker dispatch，直到用户确认
  Shared Understanding Packet，或明确退出 grill mode。
- plan、execute、goal、review 和 debug 阶段同步了新约束，避免一边说要问清楚、一边直接开始做。
- `check-update.sh` 现在检查 installed skill file content drift，并覆盖 project-local skill 内容漂移；
  validation 增加了对应 regression，避免安装面只看版本号却漏掉 skill 内容未刷新。
- 安装的 Codex、Cursor、Claude Code 全局策略同步了 grill mode 和更精简的 dispatch 边界。

## 2.7.1 - 2026-07-07

这版重点是：**写代码、改代码和复查代码时更偏向精简、清晰、可维护。**

- 执行和 review 明确要求先理解现有 owner、control flow、tests/config 和 invariants，
  再修改或验收代码。
- Worker 和 Reviewer 会更直接地反对无证据的分支、mode、wrapper、fallback 堆叠，
  以及猜默认值、防御式掩盖缺失状态的改法。
- Codex、Cursor、Claude Code 的全局策略同步了 code maintenance 规则：优先改/删现有路径，
  只有 accepted behavior 有证据要求时才新增分支或 fallback，缺状态时 fail fast。

## 2.7.0 - 2026-07-01

这版重点是：**Codex 可以显式拉满推理强度，同时减少抢答和表演式进度。**

- 新增 `gpt55-xhigh` profile：需要质量优先时，可以把所有 Teamwork Codex subagents
  渲染为 `gpt-5.5` + `xhigh` reasoning；Cursor 和 Claude Code 继续保留各自的
  performance-first 原生模型层级。
- 新增 `project-codex-agents` 安装目标，用于只刷新项目级 `.codex/agents`，避免为了
  Codex subagent profile 调整而改动 Cursor 或 Claude Code 项目面。
- Codex 全局策略新增 think-first reasoning discipline：非轻量或证据敏感任务不能为了快速可见输出牺牲读源、
  解释校验和验证；可选进度汇报应压缩，只保留决策、阻塞和验证相关信息。
- 共享 workflow contract 将“少叙述”收敛为可审计规则：routine route 不需要 gate label，
  但重要 dispatch、review 和 skipped action 仍必须保留审计线索。
- README、CODEX、init guidance、dispatch reference 和 validation 同步覆盖新 profile、
  项目级 Codex agent 安装目标和 reasoning/commentary policy。

## 2.6.0 - 2026-06-23

这版重点是：**规则更硬，调研更会发散，文档更像开源产品说明。**

- 调研不会再只围着用户给的一篇文章、论文、URL、仓库或报告转。Teamwork 会把它当作
  seed source，继续扩展到 primary source、相邻来源、反例和仍未覆盖的问题。
- 设计/方案阶段更像科研助理：先看证据覆盖、反例、来源质量和未解问题，再给方向或计划。
- 规则更能防止“假成功”：缺 env、路径、端口、模型名、超参数、credential、配置或不变量时，
  agent 不能随手给默认值或 fallback 把缺失状态伪装成可用。
- strict review / deslop 更实用：review 会更明确地抓 AI 冗余、异常防御性分支、宽泛
  catch、静默默认值、fallback masking 和可维护性退化。
- README、CODEX、CURSOR、CLAUDE 和 changelog 改成用户视角，先说明为什么用、何时用、
  能得到什么，再把平台细节留给高级参考。
- Codex、Cursor、Claude Code 的全局策略同步了同一套安全底线，升级后不同平台的行为更一致。

## 2.5.0 - 2026-06-22

这版重点是：**长任务失败后不会盲目重试。**

- goal mode 记录每次尝试的目标、假设、验证结果、失败类别和下一步，方便跨回合继续推进。
- 失败后会先做 Replay Preflight 和 plan adequacy 检查，判断是信息不足、计划过期、范围错了，
  还是执行偏离，而不是直接重复上一轮修法。
- 项目初始化更完整：新增 `scripts/init-project.sh`，改善项目级 artifacts、默认结构和安装行为。

## 2.4.1 - 2026-06-21

这版重点是：**Cursor 用户更容易安装全局规则。**

- 新增 `./install.sh cursor-policy-copy`，可以把 Cursor User Rules 策略直接复制到剪贴板。
- 文档和 readiness 检查明确提示：Cursor 的 User Rules 仍需要用户手动粘贴。

## 2.4.0 - 2026-06-21

这版重点是：**你可以更自然地说需求，Teamwork 更会自己路由。**

- 普通自然语言请求更稳定地映射到研究、诊断、计划、执行、复查、长期目标、初始化或更新。
- 小事更容易直接走 native fast path，大事才加载对应 stage 和 references。

## 2.3.0 - 2026-06-21

这版重点是：**遇到 bug 先诊断，不再先猜修法。**

- 新增 `teamwork-debug` 阶段，用于在修复前收集日志、复现、假设和 runtime evidence。
- 新增 debug、verification 和 review lenses，帮助区分“真的根因”“只是现象”和“验证不够”。
- 执行和 review 增加 debug cleanup 规则，避免临时日志、探针和修复残留变成新技术债。
- 修复 `scripts/check-update.sh` 的 upstream remote 检测。

## 2.2.0 - 2026-06-16

这版重点是：**安装和更新更可检查。**

- 新增 `scripts/check-update.sh`，用于检查本地 skills、agents、policy 和项目安装是否过期。
- 增加 installed-version markers、`--project-root` 和更完整的项目级安装支持。
- Codex、Cursor、Claude Code 的 agents、policy blocks、manifests、docs 和 validation 更一致。

## 2.0.0 - 2026-06-16

这版重点是：**Teamwork 更少打断用户，更会自己推进。**

- 收敛到 act-by-default routing：明确的任务直接做，只在真实 blocker 或核心决策上提问。
- 把分散的 subagent 规则合并成更聚焦的 dispatch、contract 和 role playbook references。
- 大幅精简 validation，但保留 package layout、manifest、skill、memory、platform 和 install-smoke 检查。

## 1.11.0 - 1.15.0 - 2026-06-11 to 2026-06-16

这几版重点是：**skills 更按需加载，深调研更省上下文。**

- `teamwork-update` 能更完整地刷新 package，并扩大 validation 覆盖。
- skills 改成按需加载：只有任务需要时才加载更细规则。
- Explorer 和 deep research packets 引入 research context budget，调研可以广泛找，但只把有用证据带回主线程。
- 新增 optional docs MCP policy，用于查询当前 library/API 文档。

## 1.5.0 - 1.10.0 - 2026-06-05

这几版重点是：**把 Teamwork 从“流程提示词”变成能记忆、能验收的协作系统。**

- 强化 durable memory、clarification gates、evidence-first fallback positioning 和 role fan-out guidance。
- 新增 full-feature memory / init gates，以及 external-memory promotion 防护。
- 引入 fail-fast no-defaults guidance，同时逐步精简 workflow overhead。

## 1.2.0 - 1.4.1 - 2026-06-04 to 2026-06-05

这几版重点是：**不同成本/性能偏好的用户可以选 profile。**

- 新增 install-time Codex model profiles：`performance-first` 和 `cost-first`。
- 优化 Codex custom agent 的默认模型，并强化 Explorer、Designer、Worker 等 role workflows。

## 1.0.0 - 1.1.2 - 2026-06-01 to 2026-06-04

这几版重点是：**建立 Teamwork 的协作骨架。**

- 细化协作编排和阶段职责。
- 新增 delegated-track lifecycle closure contracts，让 subagents 有明确交付和关闭条件。
- 更新 Codex Worker model mapping。
- 新增 runtime README pointer guidance。

## 0.14.0 - 2026-06-01

这版重点是：**Codex 的 Teamwork 授权可以全局复用。**

- 在 `~/.codex/AGENTS.md` 中安装 Teamwork 管理的全局策略块。
- 用户不需要每个项目都重复说明“可以使用 subagents”。

## 0.13.0 - 2026-05-31

这版重点是：**收紧 Codex subagent 授权规则。**

- 更新 Codex subagent authorization policy，让并行 agent 的使用边界更清楚。

## 0.12.0 - 2026-05-28

这版重点是：**Claude Code 成为一等平台。**

- 增加 Claude Code parity，包括 Claude plugin metadata、`CLAUDE.md`、Claude install targets
  和 Claude agent templates。
- 扩展 validation，覆盖 Claude manifests、skill installs 和 agent templates。

## 0.11.0 - 2026-05-27

这版重点是：**Cursor 成为一等平台。**

- 增加 Cursor platform parity，包括 `CURSOR.md`、Cursor install support、Cursor Task subagent
  mapping 和 Cursor goal-mode 文档。
- 文档从 Codex-only 行为改成 platform-native capabilities 叙事。

## 0.10.0 - 2026-05-27

这版重点是：**不能过早说 subagents 不可用，也不能把自查当验收。**

- 新增 dispatch discovery gates，要求先发现可用 subagent 能力，再判断是否能分派。
- non-lightweight acceptance paths 要求显式 dispatch exception 和 fresh-review labeling。

## 0.9.0 - 2026-05-27

这版重点是：**Teamwork 第一次成为带版本的 workflow package。**

- 发布第一个带版本号的 Teamwork workflow-gates package。
- 通过 `teamwork-init` 和 project-init references 增加 project initialization workflow。
- 将职责拆成 research、planning、execution、review、goal iteration、init、update 和 auto-routing。
- 增加 evidence-first gates、durable artifacts、review-oriented acceptance 和 automatic subagent routing。

## Pre-0.9.0 - 2026-05-12 to 2026-05-26

这段历史重点是：**从单个优化 skill 演进为 Teamwork。**

- 最初从单一优化流程起步。
- 逐步拆出 research、plan、execute、goal 和 review router subskills。
- 增加 goal runtime commands、evidence gates、durable plan artifacts 和 Codex auto-routing。
- 重命名为 Teamwork，并在后续多平台支持前先收敛为 Codex-first skill package。
