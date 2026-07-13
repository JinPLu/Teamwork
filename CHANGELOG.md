# 更新日志

[English](CHANGELOG.en.md)

这里只记录用户能感受到的变化；实现细节见 Git 提交或 Pull Request。

## 2.18.0 - 2026-07-13

**提问更贴近实际工作，不再为维持流程状态而增加额外负担。**

- **所有阶段共用一条提问边界。** Research、Debug、Plan、Execute、Review 和 Goal 都会先检查仓库、配置和已有证据；只有缺少必须由你提供的输入、观察，或结果会因你的决定而显著变化时才提问。普通澄清不需要切换到 `grill-me`。
- **只暂停真正依赖答案的工作。** 一个分支等待确认时，独立的只读调查仍可继续，避免一个问题冻结整个任务。
- **subagent 不再各自打断你。** subagent 只向 root 返回 Question Candidate，由 root 重新核对、合并重复问题并统一询问。
- **删除 Task Contract 状态机。** 2.17 引入的版本号、refreeze、Stage Entry Card 及两个 JSON 生命周期校验器被移除，改用轻量 Working Facts 保存目标、范围、验收、权限、阻塞和停止条件。
- **Review 和 Goal 继续保持收敛约束。** Review 仍使用稳定 finding ID、`BLOCKER | FOLLOW-UP | SUGGESTION` 和最多一次受限复查；Goal 仍只重试受影响分支，并且只有用户明确请求或接受 Goal Proposal 后才进入 Codex 原生 Goal 状态。
- **发布状态更完整。** 维护者更新现在会同时核对版本、双语更新日志、安装面、远端标签和 GitHub Release；缺少标签或 Release 时只报告 `release-ready`，不会误称已发布。

离线评测覆盖三平台的共享规则和安装兼容性；有限的 Codex 实测支持跨阶段提问与权限保持，但不宣称已经证明所有阶段、自然问题去重或 Cursor/Claude 的完整运行时行为。

## 2.17.0 - 2026-07-13

**直接解决“一个方案反复审很多轮、跑几个小时仍不收敛”的体验问题。**

- **重要决定更早一次对齐。** 非简单 Plan 会先检查仓库和配置，再每次只问一个真正需要你决定的问题，并给出推荐。最终方案前会展示一份简短的 Decision Summary，减少做到一半才发现方向理解错了。
- **Review 不再无限重开。** 需要独立验收的任务最多做一次完整审查；修复后由同一个 Reviewer 做一次增量复查，只检查原问题、已声明修复和修复引入的回归，不再从头扫描并不断产生新一轮意见。简单任务仍可直接自验。
- **没有阻断问题就明确结束。** 只有违反已确认验收条件、破坏保护边界、引入回归或缺少必要验证才能成为 `BLOCKER`。偏好、顺手优化和范围外建议会保留，但不能让任务一直卡着不过。
- **修一个问题不再从 Plan 全流程重来。** 已知修复直接回 Execute，原因不明才回 Debug；只有你接受了范围变化才重新 Plan。验证失败时只重跑受影响阶段。
- **执行过程中不再悄悄换目标。** 进入非简单、多阶段 Teamwork 流程的任务会让 Plan、Execute、Review 和 Goal 共用同一份版本化 Task Contract 与稳定验收条件；任何范围变化都必须显式说明并升级版本。简单任务不需要创建这套契约。
- **对话更安静。** 进度更新只报告新决定、阻塞、验证结果和完成状态，不再重复复述计划或反复宣布正在复查。

Plan 和 Review 没有被删除，Codex 的角色模型档位也没有降低。本版本优化的是重复流程、返工和收敛速度；不承诺消除 GPT-5.6 Sol/high 自身的单次响应延迟。相较 2.16，本版取消固定“零到三个问题”和 active/closed 状态仪式，改为只在有价值时提问；下面的 2.16 条目保留的是当时的历史行为。

## 2.16.0 - 2026-07-13

**新增可发现的 `grill-me` 交互，并修复 Codex subagent 的角色模型路由。**

- `grill-me` 现在是独立 skill：只询问零到三个真正影响结果、且必须由用户决定的问题；语言、文件数量、命名和内部布局等可逆细节不会被拿来凑问题。
- 多轮 grill 会保留明确的 active/closed 状态，用户要求停止、继续执行、委托判断或切换任务时才按对应权限退出；问题耗尽不会自动授权实施。
- Codex 安装、初始化和更新会原子迁移 custom-agent 路由，让 Explorer、Worker、Reviewer 等角色使用各自配置的 model/effort，而不是继承主线程的高推理档位。
- Codex 会话上限调整为 9 个线程，即一个主线程加最多 8 个 subagent；项目级安装仍不会修改用户全局配置，并保留显式 opt-out。
- Codex 0.144.0 已实测 8 个同时存活的 Explorer 使用 Terra/medium，fresh Reviewer 使用 Sol/high。重启 Codex 后新任务才会读取新的路由配置；跨平台 grill 行为仍以静态与离线验证为主。

## 2.15.0 - 2026-07-13

**长任务更不容易跑偏，并可在完成或等待确认时播放提示音。**

- 减少重复协作；用户纠正后，过时任务会停止生效。
- 不再把局部完成或未验证结果误报为整个任务完成。
- Codex 可选提示音只提醒主任务，后台任务保持静音。
- 新增只读诊断工具，排查 agent 配置和异常长任务时不会输出对话正文。
- 提示音已在 macOS 验证；Claude Code 尚未实测，Cursor 暂不支持。

## 2.14.0 - 2026-07-11

这版重点是：**刷新全部平台、全部 profile 的 subagent 模型映射。**

- Codex 的 `performance-first` 使用 GPT-5.6 Terra/Sol；`cost-first` 使用
  Luna/Terra/Sol；新增全 Sol 的 `gpt56-high` 和 `gpt56-xhigh`。
- `gpt56-role`、`gpt55-high`、`gpt55-xhigh` 继续作为兼容名称，但所有
  Codex profile 都不再调用 GPT-5.5。
- Cursor 使用当前 Composer 2.5、Sonnet 4.6 和 Opus 4.8 原生映射，其中
  `cost-first` 改用非 Fast Composer 2.5；Claude Code 使用当前
  `haiku`/`sonnet`/`opus` aliases，Deep 档提升到 `max`。
- installer、source templates、drift checker、三平台文档、项目初始化说明
  和 validation 同步更新，copy/link 与全局/项目安装保持一致。

## 2.13.0 - 2026-07-10

这版重点是：**复杂任务保留质量，简单任务少背流程。**

- 信息充分的任务会直接推进，不再为了遵循模板强制列假设、画表格、创建长期记录或启动独立复查。
- 只有真正影响结果、且必须由用户决定的问题才会打断你；测试先行、方案对比、长期记忆和 fresh review 都改为按风险触发。
- 三个平台的核心协作说明明显缩短，减少模型反复阅读和复述流程的上下文开销。
- Codex 新增按角色分层的 `gpt56-role`：Explorer 使用 Terra/medium，Worker 使用 Sol/medium，设计与验收使用 Sol/high，少数深度验收使用 Sol/max，避免所有工作都继承同一高推理档位。
- 显式固定模型或推理档位时，如果运行时不支持会直接失败并说明原因，不会悄悄换模型或降低档位。

`2.12.0` 没有独立发布；这组角色分层能力随 `2.13.0` 一起进入正式版本。

## 2.11.1 - 2026-07-08

这版重点是：**小任务默认直接做，但你明确要求“先问我”时不会被忽略。**

- 一行修复等轻量任务仍会直接完成，不自动增加问题、subagent 或长期计划。
- 如果你明确要求 `grill-me`、先讨论或先挑战假设，即使任务很小也会先遵从这个要求。
- 安装和更新不会在尚未回答的关键问题上继续改动，避免维护动作绕过你的确认。
- 新增轻量任务回归样例，防止后续版本重新变得爱提问、爱规划或过度分派。

## 2.11.0 - 2026-07-08

这版重点是：**真正影响结果的问题会先确认，本地安装是否过期也更容易发现。**

- 面对复杂或不确定任务，Teamwork 会先检查仓库和配置，只把仍需用户决定的问题带回来，并同时给出推荐。
- Research、Debug、Plan、Execute、Review 和 Goal 使用一致的确认边界，避免某个阶段说要等确认，另一个阶段却继续执行。
- 简单任务有专门的控制样例，防止普通请求被无意义地“拷问”。这些离线检查不冒充真实平台行为证明。
- `check-update.sh` 能发现全局和项目级 skills/agents 的内容漂移，而不再只比较版本号。
- 项目级更新命令和 profile 示例改成可直接复制执行；新增可将 Codex subagents 固定到 GPT-5.5/high 的 `gpt55-high` 选项。

## 2.10.0 - 2026-07-08

这版重点是：**Teamwork 的提示词优化开始要求可重复比较，而不是凭感觉改。**

- 维护者可以让旧版和候选版运行同一组任务，比较结果后再决定是否接受。
- 每次候选都必须记录模型、配置、验证结果、回滚方法和独立复查，不能只展示最好的一次输出。
- 接受与拒绝的候选都会留下记录，避免过一段时间重新尝试已经证明无效的方向。
- 这套优化工具只用于维护 Teamwork，不会给普通用户任务增加一个新的运行阶段。
- 本版本提供的是可验证的优化基础设施，不代表 Teamwork 已经自动完成了一轮真实优化。

## 2.9.0 - 2026-07-08

这版重点是：**Teamwork 自身的行为升级开始有可复用的回归检查。**

- 新增样例覆盖“小任务不过度流程化”、复杂编码、调试、调研、复查、长期目标和跨平台边界。
- 这些检查完全离线运行，不调用模型，因此维护者可以快速发现规则或安装资产被意外改坏。
- 发布行为变化前必须同时提供开发样例、发布审计和接受/拒绝记录，减少“看起来不错就上线”。
- 评测只约束 Teamwork 的维护过程，不会成为普通用户任务里的新阶段。
- 离线检查只能证明规则和样例一致，不会被描述成 Codex、Cursor 或 Claude 的真实运行效果。

## 2.8.1 - 2026-07-08

这版重点是：**“先讨论再动手”和代码质量规则真正覆盖到执行过程。**

- 当你要求先讨论时，依赖该决定的分析结论、方案选择、编辑和分派都会等待确认，而不只是暂停写代码。
- 修改代码前会先确认现有负责人、调用流程、测试和配置，减少在错误位置添加第二套实现。
- Reviewer 会检查无证据的分支、默认值和 fallback，避免一次修复带来更多难维护路径。
- 更新检查能发现本地仍在使用旧 skill、agent 或全局策略的情况。
- Codex、Cursor 和 Claude Code 使用一致的确认与代码维护边界。

## 2.8.0 - 2026-07-08

这版重点是：**你明确要求“先问清楚”时，Teamwork 会真的先停下来讨论。**

- 当你说 grill me、先问清楚或 challenge assumptions 时，Teamwork 会先提出至少一个影响结果的问题，并给出推荐答案。
- 在你确认或明确退出前，不会开始 Plan、实现、长期 Goal 或 Worker 分派。
- Debug、Plan、Execute、Review 和 Goal 使用同一条暂停规则，避免一边承诺先讨论、一边后台继续执行。
- 更新检查开始比较已安装 skill 的实际内容，能发现“版本号相同但规则仍是旧的”情况。
- Codex、Cursor 和 Claude Code 的全局安装面同步了这套交互边界。

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
