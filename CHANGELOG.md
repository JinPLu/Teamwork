# 更新日志

[English](CHANGELOG.en.md)

这里只记录用户能感受到的变化；实现细节见 Git 提交或 Pull Request。

## 7.0.1 - 2026-08-06

**Teamwork 7.0.1 让现有 6.3 Codex 安装顺利升级，同时不放宽用户文件保护。**

- **官方旧 Writer 可以直接升级。** Update 会用发布资产的精确摘要识别 6.3.0 Writer profile，并替换为当前 7.0 版本。
- **同名用户文件仍不会被接管。** 只有字节完全匹配官方 6.3.0 资产的旧 Writer 才属于迁移范围；改动过的文件、symlink 与多硬链接继续安全停止。
- **真实升级路径已闭环。** 全局刷新与精确项目根迁移现在覆盖 6.3.0 → 7.0.1，并保持新偏好、agent inventory 与项目 case-v3 状态可验证。
- **旧偏好仍不会被静默复用。** 7.0.1 继续要求明确选择 profile、受管 CodeGraph 与受管 GPU Broker，再写入新的 7.0 preference receipt。

升级操作：更新到 7.0.1 后，重新对精确项目根运行 `$teamwork-update`。

重要限制：如果旧 Writer 与官方 6.3.0 资产不完全一致，Update 不会覆盖它；需要先确认该文件应保留、移走还是由用户显式替换。

## 7.0.0 - 2026-08-06

**Teamwork 7.0 让清晰任务保持直接，并把协作方法从流程仪式重构为简洁、按需加载的能力。**

- **全局规则更少、更可信。** 普通任务不再因为复杂、重要或有风险就自动进入 workflow；Teamwork 只要求如实表达证据，并让验证强度与真实风险和结论相匹配。
- **八个公共 Skill 各自拥有清楚边界。** Explore 改为内部只读 Agent，Designer 收敛为严格对抗专用 Challenger，Plan Reviewer 合并进 Reviewer；固定 Agent 数量、L1-L3 状态和通用 digest 仪式全部移除。
- **Writer 回到文档维护。** 每项任务只维护一份 live 文档，在可复用内容首次出现、实质改变和结束时更新；事务、恢复、迁移与完整性留在存储实现层，不再占用模型工作上下文。
- **发布证据改为语义优先。** topology 和 release matrix 由 manifest 驱动，测试与 hash 不再冒充内容正确性；三宿主安装后语义测试和 disposable-write 证据成为发布硬门。

升级操作：更新到 7.0.0 后，对精确项目根目录运行 `$teamwork-update`；它会刷新全局 surfaces，并把该项目中的全部 Teamwork 文档迁移到新格式。随后从新任务开始使用新的 Skills、Agents 与策略。

重要限制：7.0.0 不提供旧设置或旧数据的运行时兼容。旧项目文档只能作为 Update 的迁移输入；没有精确项目根目录时，Update 只刷新全局 surfaces 并报告项目迁移待执行。Codex 0.144 的 JSON 流尚不暴露完整的 child-start 身份、模型和 effort，Cursor 与 Claude 的 live 证据也要求各自 CLI 在隔离 HOME 中完成认证；这些情况下 Teamwork 会明确返回 `UNSUPPORTED` 或 `FAIL`，不会用模板或 prompt 代替实际证据。

## 6.3.0 - 2026-08-05

**Teamwork 6.3.0 让 Collaborate 更像同一场连续讨论：先判断、再提问，并把选择权清楚留给用户。**

- **触发条件回到真实意图。** Collaborate 只在用户明确要讨论、设计、计划、brainstorm、比较或一起想时、后续关键选择属于用户时，或意图不清需要引导澄清时启动；风险、安全、迁移、公开发布或复杂度本身不再单独触发。
- **L1-L3 是可来回移动的协作层。** 同一场讨论会按证据在 L1 Understand Intent、L2 Explore Together、L3 Challenge and Converge 之间调整；它们不是模式、skill、固定深度、轮数预算或必经阶段。
- **原生 Ask 只服务真正会改变下一步的选择。** Collaborate 会先综合、给选项和建议，再在必要时使用宿主原生提问；相互独立的问题可以合并，依赖问题必须等待前一个答案，整个 workflow 没有总问题数、批次数或轮数上限。
- **Writer 和旁路证据都回到同一讨论。** Writer 维护总体图景、已决定事项、开放讨论/证据、当前建议/下一步这四类语义记录，不写逐字稿；Research、Explore 和显式 brainstorming、adversarial、stress-test、subagent 方法会把结果带回同一场讨论，不能替用户拥有最终选择。

升级操作：更新到 6.3.0 后运行 `$teamwork-update`，然后新建一个任务，让新的 Collaborate 策略、skills 和 agents 全部加载。

重要限制：已经在运行的任务不会自动重载新策略；请从新任务开始验证 6.3.0 行为。Codex 单次 `request_user_input` 最多 3 个问题/选项只是宿主传输限制，不是 Teamwork 的 workflow 总上限。

## 6.2.3 - 2026-08-03

**Teamwork 6.2.3 让有实质内容的计划、讨论、调研、诊断、审查与执行结果默认可靠落盘。**

- **Writer 默认持久化覆盖完整 workflow。** 计划、Collaborate 更新、Research/Explore 证据、Debug 记录、Review 结论、Goal 进展、会产生变更的 Init/Update，以及有继续价值的执行检查点和结果，都会默认写入 case-v2 artifact。
- **Explore 不再丢失可复用的本地证据。** 有实质内容的代码、配置、日志和测试发现会通过 `evidence-add` 保存；很小的读取、检查型任务和一次性说明仍保持轻量，不制造文件。
- **Artifact 元数据不再被错误归类。** 每种写入操作都由 schema 固定到正确的 kind 与 `teamwork` consumer；Research、Explore、Debug 等记录保持原始语义，不匹配的覆盖请求会安全失败。
- **新建 Goal/Review 与三宿主 agent 边界完整闭环。** 新 case 会从合法阶段开始，所有创建与写入都经过事务回读；Codex、Cursor、Claude 共享同一套九角色边界，并继续只允许 Writer 执行 workflow 持久化。

升级操作：更新到 6.2.3 后运行 `$teamwork-update`，然后新建一个任务，让刷新后的策略、skills 和 agents 全部加载。

重要限制：默认持久化不是逐轮聊天日志；很小的 native/check-only 任务、一次性解释，以及明确要求 `no files`、`off-record`、`read-only` 或 `no writes` 的任务仍不会落盘。已有 case-v2 项目无需迁移。

## 6.2.2 - 2026-08-03

**Teamwork 6.2.2 完成 6.2 的安装、意图识别与 agent 投入三项整体交付。**

- **安装偏好和真实入口完整闭环。** 首次或缺少有效偏好记录时，完整全局安装/更新必须先获得 profile、CodeGraph 与 GPU Broker 的显式选择；已有有效记录才可无参数复用。
- **6.2 的意图识别优化继续有效。** Root 仍先检查可发现状态并采用安全默认值，只有真正缺少用户拥有的必需值或会改变结果的偏好时才提问，叶角色继续只返回精确缺口。
- **6.2 的 model/effort 优化继续有效。** `performance-first` 与 `cost-first` 的角色化投入矩阵保持不变，两个可选能力仍可独立选择，仅 CodeGraph、仅 GPU Broker 或全禁用组合都保留。
- **首次、checkout 与 Marketplace 边界已回归验证。** Marketplace runtime 首次无 activation marker 时会走 plugin bootstrap，不复制重复 Codex skills；checkout 加已有合法 activation marker 继续走 checkout-safe，checkout 无 marker 继续普通 checkout 安装。

升级操作：更新到 6.2.2 后重新运行 `$teamwork-update`；首次或偏好记录缺失时，显式 baseline 使用 `--profile performance-first --no-managed-codegraph --no-managed-gpu-broker`，或按需分别启用 CodeGraph/GPU Broker。

重要限制：shell 安装器保持非交互，不会在命令行内追问；缺少必需偏好时会停止并提示应由 Root/Skill 收集选择后重试。checkout 更新仍不会替换 Marketplace plugin cache。

## 6.2.1 - 2026-08-02

**Teamwork 6.2.1 修复了 checkout 更新与已有 Marketplace 激活状态并存时的错误路由。**

- **checkout 更新可以正常完成。** 从源码 checkout 运行 `$teamwork-update` 或 `./install.sh update` 时，即使本机已有 Codex Marketplace activation marker，也会走 checkout-safe 路径，不再误入仅允许 plugin runtime 的 bootstrap。
- **不会复制重复的 Codex skills。** checkout-safe 路径只刷新 Codex agents、routing、policy、notifications 与已确认的受管依赖，同时继续由 Marketplace plugin 提供 Codex skills。
- **Marketplace 边界保持严格。** `plugin-codex-bootstrap` 仍要求有效的 plugin runtime；checkout 不会重写 activation marker，非法或不属于 Teamwork 的 marker 仍会安全停止。
- **真实失败路径已有回归保护。** 新测试固定覆盖“checkout + 已有 activation marker”，并验证 profile、CodeGraph 与 GPU Broker 的显式偏好仍按非交互路径执行。

升级操作：更新到 6.2.1 后重新运行 `$teamwork-update`；checkout 用户可直接运行 `./install.sh update` 并传入或复用已记录的 profile、CodeGraph 与 GPU Broker 偏好。

重要限制：checkout 更新不会替换 Marketplace plugin cache 或重写其 activation marker；要更新 Marketplace 自带的 skills，仍需通过 Codex plugin marketplace 渠道安装 6.2.1，并在新任务中运行 `$teamwork-update`。

## 6.2.0 - 2026-08-02

**Teamwork 6.2 让安装选择、提问时机和 agent 投入更贴合真实任务。**

- **安装偏好一次说明、持续复用。** 首次启用或缺少有效记录时，Update 会明确收集 performance/cost profile，并分别确认是否受管 CodeGraph 与 GPU Broker；选择会保存，之后的非交互更新可直接复用，两个可选能力也会独立预检和刷新。
- **清楚请求不再被多余提问打断。** Root 会先检查可发现状态并采用安全可逆默认值；确实缺少一个用户拥有的必需值时只问一次并恢复同一 workflow；会实质改变结果的潜在偏好或未成形意图才进入 Collaborate，由它先给判断和建议再提问。
- **叶角色只报告缺口，不直接问用户。** Researcher、Explorer、Debugger、Planner、Worker、Reviewer 和 Plan Reviewer 在三个宿主上统一把精确缺口或重分类信号交回 Root，保证一个可见提问者、一个 active gap，并避免跨角色或阶段重复询问。
- **模型与 effort 按角色重新投入。** `performance-first` 把高质量推理集中到 Debug、Design、Plan 和 Review，同时让 Research、Explore 与 Worker 使用 Terra；`cost-first` 让 Explore 与 Worker 使用 Luna，并保留关键 Research 与 Review 的质量门槛。实时发布矩阵仍严格保持 13 个场景、104 条记录。

升级操作：通过现有 Marketplace 或 checkout 渠道更新到 6.2.0，然后运行 `$teamwork-update`；若已有有效安装偏好会直接复用，否则按一次提示选择 profile、CodeGraph 与 GPU Broker。

重要限制：受管 GPU Broker 仍需要可解析的本地 companion 来源；选择不受管只代表该可选能力不由 Teamwork 安装或刷新，不影响基础 skills、agents 与策略安装。模型名称和 effort 仅用于支持对应配置的宿主，不构成固定成本、延迟或质量保证。

## 6.1.3 - 2026-08-01

**Teamwork 6.1.3 确保更新的是当前实际调用的旧版 CodeGraph。**

- **实际命令得到更新。** 当旧 CodeGraph shim 位于用户本地 bin 目录时，`$teamwork-update` 现在会替换该有效命令而不是只安装一个未被调用的新副本。
- **替换范围精确。** 强制替换只作用于已确认的同名 CodeGraph shim；其他命令位置继续使用普通的 npm 全局安装路径。
- **旧环境可继续升级。** 旧版 CodeGraph 不再因 PATH 优先级而在全局更新的就绪检查中被误认为未更新。
- **安全顺序不变。** CodeGraph 未达到固定版本时，GPU Broker 与 Teamwork 全局配置仍不会刷新。

升级操作：通过你正在使用的 Marketplace 或 checkout 渠道更新到 6.1.3，然后运行 `$teamwork-update` 刷新全局配置。

重要限制：强制替换只适用于当前命令恰好是用户本地目录中的 CodeGraph shim；更新不会替换其他工具、升级 npm/uv、驱动、CUDA 或系统软件。

## 6.1.2 - 2026-08-01

**Teamwork 6.1.2 修复了旧版 CodeGraph 让全局更新过早停止的问题。**

- **旧版兼容。** 即使已安装的 CodeGraph 没有 `upgrade` 子命令，`$teamwork-update` 仍可继续完成受管更新。
- **安装方式统一。** Teamwork 现在固定通过 npm 安装受管的 CodeGraph 版本，使缺失与已安装的情况走同一可靠路径。
- **失败顺序可预期。** 如果 CodeGraph 安装失败，更新会在刷新 GPU Broker 或写入 Teamwork 全局配置前停止。
- **更新范围不扩张。** 本地 GPU Broker 继续仅从已解析的 companion 来源刷新，原有的 MCP 冲突保护保持不变。

升级操作：通过你正在使用的 Marketplace 或 checkout 渠道更新到 6.1.2，然后运行 `$teamwork-update` 刷新全局配置。

重要限制：该修复需要 npm 能安装 Teamwork 固定的 CodeGraph 版本；无法安装时会安全停止，不会尝试升级 npm、uv、驱动、CUDA 或其他无关工具。

## 6.1.1 - 2026-08-01

**Teamwork 更新现在会同步修复全局配置与所需的本地协作依赖。**

- **更新范围更完整。** `$teamwork-update` 默认刷新 Teamwork 的全局 skills、agents、路由、策略、通知和 Cursor MCP 配置。
- **依赖自动就绪。** CodeGraph 会更新到 Teamwork 固定的版本，缺失时自动安装；本地 GPU Broker companion 也会刷新并验证 daemon 与 health 状态。
- **配置冲突更安全。** 更新会保留不属于 Teamwork 的 MCP 条目；若发现同名但未托管且内容冲突的配置，会停止并说明原因。

升级操作：运行 `$teamwork-update`（checkout 用户运行 `./install.sh update`）以刷新全局安装；随后按提示重启宿主或完成 Cursor User Rules 粘贴。

重要限制：GPU Broker 只能从已解析的本地 companion 来源安装；找不到来源或所需运行时会安全失败。更新不会升级 Node、npm、uv、驱动、CUDA 或其他无关工具。

## 6.1.0 - 2026-07-31

**Teamwork 6.1 保留每个专门方法，同时让日常协作更轻、更少被流程打断。**

- **日常上下文更精简。** 全局规则只保留权限、路由和持久化边界；只有任务真正需要时才加载对应 Skill 的自包含方法，清楚的读取、解释、命令、实现与集成继续走 GPT 原生路径。
- **专门方法在真实工作中更可见。** 对获准插桩的运行时、异步、UI、事件流和数据流未知故障，Debug 现在默认使用最小结构化日志实验；Plan、Goal 与 Explore 也补强了各自边界的状态化证据场景。
- **文档持久化不再吞掉已完成结果。** 如果方法已产出结果，但 Writer、transaction 或 readback 随后失败，Teamwork 会返回该结果并明确标记为未保存；只有真正依赖持久连续性的下一步才等待 readback，也不会退回直接写文件。
- **发布门禁同时保护行为与余量。** 紧凑的语义合同替代了绑定长篇措辞的检查，为项目上下文留出明显余量，同时不改变现有 `performance-first` 或 `cost-first` 模型 profile。

升级操作：按现有 Codex、Cursor 或 Claude Code 渠道更新，并新建任务以加载精简后的全局规则和新 Skill。已有 v6 项目无需迁移；更旧且被明确选中的项目仍由 Init/Update 执行一次性迁移。

重要限制：更小的指令面会降低静态上下文压力，但 Teamwork 不承诺固定的延迟或价格下降。实际成本仍取决于模型、effort、任务和真正值得派发的 agent 数量；静态与有边界的轨迹证据也不代表所有宿主都具有完全等价的自动行为。

## 6.0.1 - 2026-07-31

**Teamwork 6.0.1 修正发布说明，让 v6 的研究依据、日常协作方式和成本控制更容易理解。**

- **研究依据进入发布说明。** 假设驱动调试、按证据缺口推进研究和独立复查等能力，现在明确对应 ReAct、Reflexion、CRITIC 等研究，以及 Cursor、Claude Code、Codex 和 Agent Skills 的实践，而不是只罗列内部机制。
- **日常协作边界更清楚。** 普通任务继续直接发挥 GPT 的原生能力；只有专门方法或独立视角能带来实质收益时才调用对应 agent，压力测试仍由 Collaborate 内的 challenge 方法承接。
- **投入策略被完整说明。** 默认采用一个聚焦 owner、受限上下文和受限并发，只在复杂度或风险需要时提高 effort；现有模型 profile 不变，也不把方向性运行观察写成固定价格或速度承诺。
- **升级边界不再含混。** 正常运行不保留旧配置回退；Init/Update 只在获得精确项目授权后一次性导入旧项目信息，安装新 Skill 本身不会静默迁移项目。

升级操作：运行中的 6.0.0 无需重新迁移项目或调整模型 profile；需要随安装包获取更正说明的用户，按现有渠道更新到 6.0.1。

重要限制：这是发布说明修复，不改变 6.0.0 的 Skill、调度、迁移协议或模型选择。外部论文、产品设计和 CodexRadar 只提供设计依据或方向性观察，不代表 Teamwork 测得了固定的速度提升、价格优势或模型排名。

## 6.0.0 - 2026-07-30

**Teamwork 6.0 强化了 Skill 思考和协作的方法，同时让日常任务继续走 GPT 原生的快速路径。**

- **调试、研究和复查开始沿证据推进。** Debug 会先建立可证伪假设再运行探针；Research 围绕证据缺口和矛盾逐步收敛；Review 保持独立批评，Goal 会记录失败证据并改变策略。这些设计吸收了 [ReAct](https://arxiv.org/abs/2210.03629)、[Reflexion](https://arxiv.org/abs/2303.11366)、[CRITIC](https://arxiv.org/abs/2305.11738)、Cursor Debug/Plan、Agent Skills 与 Claude Code/Codex subagent 的实践。
- **日常协作不会被 Skill 接管。** 普通读取、解释、简单命令和清楚授权的实现仍由 GPT 原生完成；只有需要专业方法、隔离上下文或独立判断时才启用对应 agent。压力测试也没有消失，而是作为 Collaborate 内部有边界的 challenge/adversarial 方法继续使用。
- **速度、质量和成本按任务权衡。** 默认只使用一个专注的专业 agent，并限制并行与上下文；只有复杂、高风险、明确对抗或发布任务才提高 effort 和并发。`performance-first` 与 `cost-first` 延续原有模型偏好，不根据易变的价格或排行榜自动改写路由。
- **旧项目一次迁移，之后不再双轨运行。** Teamwork 不保留旧版运行回退；Init/Update 会在用户指定的精确项目中读取旧信息、验证候选结果并安全导入新格式。迁移成功后，所有 workflow 只使用新的事项记录。

升级操作：把旧的 `$grill-me`、`$teamwork-discuss` 或 `$teamwork-design` 调用改为 `$teamwork-collaborate`。旧项目先更新 Teamwork，再在该项目中运行 Init/Update 完成一次性迁移；安装新版本本身不等于项目已经迁移。

重要限制：上述论文和产品设计支持的是方法选择，不是 Teamwork 自身的效果量测试。CodexRadar 只作为动态、方向性的运行观察；Teamwork 不承诺固定价格、延迟或模型排名，也没有在 v6 改写既有模型 profile。

## 5.1.0 - 2026-07-30

**Teamwork 5.1 修复工作流文档维护：新项目把持久文档收敛到 case bundle，同时不强制迁移已有项目。**

- **新项目使用 case bundle。** 新初始化的 Teamwork memory 以一个 case 承接 Collaborate、Plan、Research、Debug、Review、Goal 和执行结果，减少 `discussion/`、`plans/`、`research/`、`reports/` 等目录各自争抢所有权。
- **已有项目保持兼容。** 升级到 5.1.0 不会自动改写、迁移或删除现有 `docs/teamwork`；旧项目在明确 cutover 前继续使用 legacy-v1 路由。
- **Writer 更积极但仍受事务约束。** 命名工作流默认把可复查的中间状态和完成结果交给 Writer，经受控事务落盘；缺少 Writer、路由、权限或 readback 时必须报告未保存。
- **运行包可自检。** Marketplace runtime 带有 integrity manifest，用于发现混合、陈旧或被改动的包根；源码 checkout 和 runtime 包各自按自己的边界解析。

升级操作：Codex Marketplace 用户重新添加 `JinPLu/Teamwork`、安装 `teamwork-skill@teamwork`，并在新任务中运行 `$teamwork-update`；checkout 用户运行 `git pull --ff-only`、`./install.sh all` 和 `./scripts/check-update.sh --readiness`。升级本身不会执行项目文档迁移。

重要限制：从 legacy-v1 到 v2 case bundle 的 cutover 是单独的单向操作，需要在候选树验证和 cold archive restore drill 通过后再次明确授权。Cold archive 只保存字节和 POSIX mode，不是物理备份；Teamwork 不会自动删除旧文档或冷归档对象。

## 5.0.0 - 2026-07-29

**Teamwork 5 把讨论、压力测试和方案收敛统一到 Collaborate，让协作更容易启动，也更容易续上。**

- **一个公开入口承接协作。** `$teamwork-collaborate` 统一处理 dialogue、brainstorm、grill 和可接受方向收敛；公开 Skill 数量变为 9 个，`$grill-me`、`$teamwork-discuss` 和 `$teamwork-design` 不再作为公开名称或别名存在。
- **提问回到合适的交互形态。** Agent 先给综合、候选空间、决策地图或临时建议；grill 严格按 global → boundary → detail 推进，每批最多三个独立决定，依赖决定分轮处理。开放问题保留自然文字，只有真实有限的 2–3 个互斥选择才调用 Codex 原生选择界面。
- **Writer 默认留下可复查断点。** 持续协作形成实质状态且仍有未决问题或未接受方向时，会默认保存 Collaborate 检查点；Research、Debug、Plan、Plan Review、Review、会产生变更的 Init/Update 和有真实下游消费者的终态执行也会保存对应结果，active Goal 会接管执行进度并避免重复文档。
- **旧记录只作为迁移输入。** 新状态写入 `docs/teamwork/collaborate/current.md`；旧 Discussion/Design 只读导入，旧生命周期写入不再可用。记录不保存逐字对话，也不会用 report 或 conclusion 代替。

升级操作：把现有调用中的 `$grill-me`、`$teamwork-discuss` 或 `$teamwork-design` 改为 `$teamwork-collaborate`。Codex Marketplace 用户重新添加 `JinPLu/Teamwork`、安装 `teamwork-skill@teamwork`，并在新任务中运行 `$teamwork-update`；checkout 用户运行 `git pull --ff-only`、`./install.sh all` 和 `./scripts/check-update.sh --readiness`。

重要限制：协作模式、对抗搜索和落盘门槛仍依赖宿主模型的语义判断；原生选择界面要求宿主暴露 `request_user_input`，Writer 落盘要求宿主提供已安装的 Writer agent 与事务 readback。缺失能力时必须明确报告未保存，不能用文字选项或 Root 直写伪装成功；`no files`、off-record、read-only/no-write 始终优先。升级只会自动删除内容完全匹配的 Teamwork 旧 Grill/Discuss/Design/Router/Execute；改过或无所有权标记的副本会保留并阻止自动替换，需要用户先检查冲突。

## 4.6.0 - 2026-07-26

**Teamwork 现在会围绕读者真正需要理解和决定的内容组织回答与文档，同时保持原意不变。**

- **回答沿着读者的理解路径展开。** Root 先给结论，再明确关键逻辑、保持术语一致，并删去无助于理解的细节，让讨论更直接而不是只追求流畅措辞。
- **Writer 只改善呈现。** Writer 可以为了读者调整独立文档的顺序、措辞、衔接和重复，但必须保留既定事实、来源、引用、决定、权限、状态和验收结论。
- **无需选择写作模式。** 读者中心表达成为通用约束，不增加写作 Skill、模式或额外质量阶段，普通交流也不会被强制套用论文语气或固定结构。
- **三个宿主采用同一边界。** Codex、Cursor 和 Claude Code 使用一致的全局表达原则与 Writer 约束，代码相关文字仍由实现者负责。

升级操作：Codex Marketplace 用户重新添加 `JinPLu/Teamwork`、安装 `teamwork-skill@teamwork`，并在新任务中运行 `$teamwork-update`。checkout 用户运行 `git pull --ff-only`、`./install.sh all` 和 `./scripts/check-update.sh --readiness`。

重要限制：这些约束会改善信息顺序、逻辑显式性和术语一致性，但不能保证不同模型产生相同语气，也不会修复输入中缺失或错误的事实；Writer 必须保留或标明内容缺口，而不能自行补写。

## 4.5.0 - 2026-07-25

**Teamwork 现在会先参与讨论、再提出真正有价值的问题，并让各工作流的记录可靠共存。**

- **讨论先贡献再提问。** 当用户说“讨论”、`brainstorm` 或类似表达时，Root 会先给出综合、张力或候选空间；只有反馈确实能改善下一步时，才提出一个高信息量的开放或有限问题，清楚的执行请求仍直接完成。
- **Ask 成为原生交互能力。** 有限选择使用宿主的提问界面，开放讨论保持自然对话；Grill 专注重大影响或明确要求的持续盘问与压力测试，Design 处理非重大未决方向，各 Skill 只在自己的阶段请求必要反馈。
- **持久化跟随工作流生命周期。** Grill、Design 和 Goal 使用依赖后续工作的 checkpoint；Research、Debug、Plan、Review 和会产生变更的 Init/Update 在结果确定后保存 completion companion；Writer 只有在结果冻结后才启动，事务 readback 成功前不会声称已保存。
- **多份完成记录不再互相覆盖。** Debug、Review、Init 和 Update 的结果现在可以并存，已有记录会在下一次成功保存时安全兼容；普通 report 与 Plan 的原有所有权保持不变。

升级操作：Codex Marketplace 用户重新添加 `JinPLu/Teamwork`、安装 `teamwork-skill@teamwork`，并在新任务中运行 `$teamwork-update`。checkout 用户运行 `git pull --ff-only`、`./install.sh all` 和 `./scripts/check-update.sh --readiness`。

重要限制：讨论与 workflow 的语义选择仍由宿主模型判断，静态评测不能保证每次回答逐字一致；generic artifact 在成功开始 `artifact-apply` 前仍不具备持久化保证，中断时会明确报告未保存。

## 4.4.0 - 2026-07-23

**命名 Teamwork workflow 现在默认留下可复用结果，独立文档、Design 状态和指令边界也更清楚。**

- **默认持久化有完整矩阵。** 在已初始化且可写的项目中，Grill、Design、Goal、Research、Debug、Plan、Review 和会产生变更的 Init/Update 默认保存可复用结果；普通聊天、一次性 native work 和清楚的代码任务不强制额外文档，Explore 不独立造报告，`no files`、off-record、read-only/no-write 会覆盖默认。
- **独立文档交给 Writer。** 简单模型负责所有正常的独立文档与改写，包括起草、整理、摘要、翻译和润色；研究和决定仍由对应专业角色负责，代码相关文字由编码角色负责。
- **Design 状态对用户可见。** Design 可以保持 `pending`、被标为 `accepted` 或进入 `blocked`；保存不等于接受，只有 `accepted` 才能进入 Plan，已有 Design 记录继续兼容。
- **指令保持轻量而不丢边界。** Teamwork 的说明保持精简，但不会为了缩短文本而删掉决定、证据、权限或验收边界。

升级操作：Codex Marketplace 用户重新添加 `JinPLu/Teamwork`、安装 `teamwork-skill@teamwork`，并在新任务中运行 `$teamwork-update`。checkout 用户运行 `git pull --ff-only`、`./install.sh all` 和 `./scripts/check-update.sh --readiness`。

重要限制：默认落盘只在命名 workflow 已实际激活、项目已初始化且可写，并且 Teamwork 能安全保存时成立；`no files`、off-record、read-only/no-write 始终优先。落盘不授权实现或发布；条件不满足时仍先交付主结果，并明确报告未保存。

## 4.3.0 - 2026-07-21

**现在只需描述设计问题；Teamwork Design 会自己判断是否需要对抗搜索。**

- **从写命令变成看问题。** 以前只有明确写出 `$teamwork-design adversarial` 才会启动对抗搜索；现在只要真实设计取舍仍有至少两个可行方向，并且错误代价高、难以逆转或证据冲突让一次普通挑战不足，`teamwork-design` 就会自动升级。
- **不再追问预算。** 模型会先说明选择理由和 envelope，然后直接使用默认 `B=3`；无需再写策略名、预算或“不要进入 Plan/实现”。需要精确控制时，`adversarial` 仍可强制开启，`standard` 可明确关闭。
- **普通设计仍保持轻量。** 单纯出现“高风险”“复杂”或 `brainstorm` 字样不会触发额外 agent；没有满足自动门槛时仍只做一次 challenge。
- **安全边界没有放松。** 自动选择只授权只读 Design 搜索；fresh 隔离、双批评者、双最终审计和 durable Design / Plan / implementation 边界保持不变。

升级操作：Codex Marketplace 用户重新添加 `JinPLu/Teamwork`、安装 `teamwork-skill@teamwork`，并在新任务中运行 `$teamwork-update`。checkout 用户运行 `git pull --ff-only`、`./install.sh all` 和 `./scripts/check-update.sh --readiness`。

重要限制：自动选择依赖宿主模型对输入和证据的语义判断，不保证不同模型逐字一致；需要确定行为时使用 `adversarial` 或 `standard` 覆盖。

## 4.2.0 - 2026-07-21

**Teamwork Design 现在可以显式切换到预算化对抗搜索：普通设计仍保持轻量，需要更强压力测试时才使用多假设、独立双批评和双收敛审计。**

- **设计强度由你决定。** 以前 `$teamwork-design` 固定使用一次 challenge；现在默认行为不变，只有明确调用 `$teamwork-design adversarial` 才会进入对抗搜索。高风险、复杂度或裸 `brainstorm` 不会自动增加成本。
- **对抗搜索有可见上限。** 开始前会展示 goal、fitness、taxonomy 和假设试验预算；未指定时推荐 `budget=3`。每个实际假设交给两名全新独立批评者，实质修订消耗新的试验名额，最后两名全新审计者必须同时通过。
- **失败不会被包装成 Design。** 隔离不可证明、预算耗尽、审计分歧或中断都会明确返回 incomplete，不会静默降级、追加预算或生成 durable Design。
- **Design、Grill 和 Plan 的所有权不变。** 对抗搜索仍属于 `teamwork-design`，不新增第 11 个 skill 或新角色；聊天中的通过结论仍不是 Plan-ready，只有用户明确接受并授权受控保存后才产生 durable Design。

升级操作：Codex Marketplace 用户重新添加 `JinPLu/Teamwork`、安装 `teamwork-skill@teamwork`，然后在新任务运行 `$teamwork-update`；checkout 用户运行 `git pull --ff-only`、`./install.sh all` 和 `./scripts/check-update.sh --readiness`。

重要限制：本版会对无法证明 fresh 隔离的宿主失败关闭；静态验证或单宿主前向测试不等于 Codex、Cursor、Claude Code 的 live 行为完全等价。

## 4.1.0 - 2026-07-20

**Teamwork 4.1.0 让正式角色路由重新生效；Grill 和 Design 仍可批量处理独立问题，而跨宿主 live 派发尚未验证。**

- **正式角色路由恢复。** Research、Explore、Debug、Design、Plan、Worker 和 Review 再次使用宿主原生角色，清楚的本地工作仍走原生路径；Codex 保留用户已有的并发限制，跨宿主 live 派发仍待配额允许后确认。
- **相关决定可批量也可恢复。** Grill 先给全局决策地图，再提出最多三个彼此独立且带推荐、最大代价、关键性、阻塞对象、依赖和关闭信号的问题；Design 把独立决定同批、依赖决定分轮处理。一个回答批次只保存一次完整更新，旧讨论记录仍可读取；收敛图只显示路线、状态和依赖，完整理由与证据在图外正文出现一次。
- **Cursor setup 边界更明确。** Cursor 安装默认把 `codegraph` 和 `gpu-broker` 写入 `~/.cursor/mcp.json`，可用 `--no-mcp` 跳过且仍须在设置中启用 MCP；项目 init 只有在显式 `--cursor-mcp` 同意下才写 `.cursor/rules/` 和项目级 `.cursor/mcp.json`。`--readiness` 会提示 User Rules 的手动粘贴步骤，Research、Explore、Goal、Update 和 Design/Grill 的保存边界更清楚；CodeGraph MCP 不可用时回退到直接读文件，`gpu-broker` 规则只在可能涉及 GPU 的项目里加载。
- **Cursor profiles 按角色分配。** `performance-first` 与 `cost-first` 重新分配模型：Researcher 用 terra/flash，Explorer 用 flash，Debugger/Designer/Planner/Plan Reviewer/Reviewer 按角色在 opus、sol、terra、luna 与 fable 之间切换，Worker 保持 composer-2.5-fast。

## 4.0.0 - 2026-07-20

**Teamwork 变成一组更聚焦的能力，清楚的本地工作直接回到宿主执行。**

- **原生工作与普通讨论不再绕路。** 日常代码查证和已授权实现不再经过通用 Router/Execute，专门方法由 Research、Explore、Design、Debug、Plan、Review、Goal、Grill、Init 和 Update 这 10 个公开 Skills 处理；普通 question-first 留在对话里，只有显式保存、继续或独立构成重大变更的讨论才使用唯一 Grill 记录，并且只在实质决定、待决问题变化或关闭/取代时更新。
- **证据与 Design 各守边界。** Explore 只做本地项目证据，Research 只做外部或时效性证据；Design 只在真实取舍会改变结果时展开，并在进入 Plan 前冻结一个可追溯方向。
- **Worker 先自证再进入 Review。** Worker 完成所属切片并验证真实路径；主任务集成候选后，只有用户要求或命名的风险门才运行一次独立 Review，修复后最多做一次聚焦复查。
- **Codex 安装与 profiles 跟随角色。** Codex 默认使用 Marketplace 插件安装和更新，checkout 安装保留给 Cursor、Claude Code、本地开发或手动 Codex 配置；`performance-first` 让 Researcher、Explorer、Debugger、Planner 和 Worker 使用 `gpt-5.5/high`，Designer 和 Plan Reviewer 使用 `gpt-5.6-sol/high`，Reviewer 使用 `gpt-5.6-sol/max`。

升级操作：v3.4.2 用户重新运行适用安装命令或 `$teamwork-update`。Marketplace 用户需要移除并重新添加 `JinPLu/Teamwork`，再安装 `teamwork-skill@teamwork`，新开任务执行 `$teamwork-update`；checkout 用户运行 `git pull --ff-only`、`./install.sh all` 和 `./scripts/check-update.sh --readiness`。

重要限制：v4 没有旧 Router、Execute 或 legacy role alias；迁移只删除 Teamwork 能证明归属的旧文件，自然语言选择具体 Skill 仍由宿主模型决定。

## 3.4.2 - 2026-07-19

**公开文档变得更短，也更容易找到正确用法。**

- **文档先讲结果。** README、Codex、Cursor、Claude Code 指南和 Marketplace 说明都先讲用户能完成什么，再保留必要的使用边界。
- **更新可以继续前进。** Codex Marketplace 使用未固定版本的 `JinPLu/Teamwork`，后续 `$teamwork-update` 可以继续前进到新版本。
- **各指南表达一致。** 公开文档都围绕用户结果、操作边界和必要说明展开。

## 3.4.1 - 2026-07-19

**发布说明开始先讲用户真正能感受到的变化。**

- **条目先讲用户变化。** 发布条目先给总结，再用简短要点说明变化来源和使用影响。
- **运行行为不变。** 本版只调整文档写法，不改变 Teamwork 运行行为。

## 3.4.0 - 2026-07-18

**Codex 可以从 Marketplace 一步启用 Teamwork。**

- **Marketplace 一步启用。** 安装 `teamwork-skill@teamwork` 后，在新任务中运行 `$teamwork-update` 即可引导启用 agents、路由、策略和可选通知。
- **安装不越界。** Marketplace 安装不会静默改写配置、信任 hook 或创建额外的 skills 副本。
- **讨论可续，任务直达。** `grill-me` 可以保存明确要求继续的讨论；范围和权限清楚的普通任务直接完成。

## 3.3.0 - 2026-07-16

**完成结果优先，简单任务不再被流程拖慢。**

- **明确任务走最短路径。** 明确的修改或运行请求走最短真实路径，只核对当前 blocker、实际改动或指定的高风险边界，结果出现就停止。
- **自然语言触发合适能力。** “先问清楚”“查原因”“按现有方案继续”等自然语言请求可以进入对应的讨论、调研、诊断或执行能力。
- **讨论只在有续点时保存。** `grill-me` 只在明确要求先讨论且确有继续价值时保存记录；普通计划不创建讨论文件。
- **更新职责分开。** `teamwork-update` 负责全局刷新，`teamwork-init` 负责项目说明和上下文。

## 3.2.0 - 2026-07-16

**讨论更像自然交流，回来也更容易接着聊。**

- **回答连接结论与依据。** `using-teamwork` 会把结论、依据、通俗解释和真正影响决定的边界连起来说，观察与推断分开。
- **讨论记住续点。** `grill-me` 会记住已经谈定的结论和下一项待比较、测量或决定的问题。

## 3.1.1 - 2026-07-15

**这次不需要更新，Teamwork 的使用方式保持不变。**

- **只补发布记录。** 本版补齐 3.1.0 的发布记录，不改变任何 subskill 或运行行为。

## 3.1.0 - 2026-07-15

**长讨论中断后，回来还能从未决问题继续。**

- **讨论从断点继续。** `grill-me` 保存目标、已定选择、未决问题、关键依据和继续点，恢复时不重问已定事项。
- **回复与初始化更稳。** 普通回答先给结论和真正影响决定的事实，初始化中断会在项目锁内恢复或安全停止。

## 3.0.0 - 2026-07-15

**回复更直接，项目里也不再复制一整套 Teamwork。**

- **回复先给结论。** 普通回答先给结论、重要原因和下一步；长讨论在有权限时保存紧凑的路线和回放。
- **项目不再复制包。** `init-project` 只写项目说明、memory 和 CodeGraph 上下文，不再把 Teamwork 包复制进项目。

## 2.22.0 - 2026-07-15

**共同规则更集中，简单任务不再被重复流程拖慢。**

- **项目说明更轻更易迁移。** 项目得到精简、可迁移的说明和索引，不再承受重复规则。
- **公开包不带敏感内容。** 真实用户路径、会话标识、私有地址和凭证形态的内容不会进入公开包。

## 2.21.1 - 2026-07-15

**本版不改变安装与运行方式。**

- **无需用户操作。** 安装与运行行为保持不变，公开内容不包含原始私有数据。

## 2.21.0 - 2026-07-15

**长讨论经过压缩、暂停或交接后更容易恢复。**

- **讨论只保留必要状态。** 长讨论可以保存已接受方向、待决定问题和关键依据，记录不是逐轮 transcript，也不授予执行权限。
- **初始化与发布授权分开。** 初始化保护人类文档和自定义内容，更新安装内容不等于获准公开发布。

## 2.20.0 - 2026-07-14

**改动优先复用现有路径，减少无必要的包装和备用流程。**

- **改动复用既有路径。** 实现从已经负责该行为的路径开始，额外模式、包装、fallback 和依赖需要真实需求。
- **安装漂移可见。** 安装与更新检查会区分各平台 skills、agents 的缺失、过期和内容漂移。
- **过期记录不再生效。** 过期、未接受或不再适用的记录不会继续引导当前任务。

## 2.19.0 - 2026-07-13

**重要完成和权限请求提醒默认可用，而且只信任 Teamwork 自己的 hook。**

- **提醒按平台启用。** Codex 和 Claude Code 的完成音与权限请求音可随完整安装启用，单平台安装仍可选择。
- **Hook 信任状态可见。** readiness 检查区分 hook 已信任、待审核和无法核验，并分别处理 `Stop` 与 `PermissionRequest`。

## 2.18.0 - 2026-07-13

**Teamwork 会先查证，只在确实需要你决定时提问。**

- **只问必要决定。** 只有缺少必要输入、观察或实质决定时才提问；等待一个分支时，独立的只读调查仍可继续。
- **工作状态保持精简。** 工作只保留目标、范围、验收、权限、阻塞和停止条件等必要事实。
- **Review 与 Goal 有明确门槛。** 复查只让边界违反、回归或缺证据的问题阻断完成，Goal 只在明确要求或接受提议后启动。

## 2.17.0 - 2026-07-13

**重要方向会提前对齐，修复与复查更快收敛。**

- **一次只问一个决定。** 方案先查证，一次只问一个真正需要用户决定的问题，并给出推荐。
- **复查先完整后增量。** 复查先完整检查一次，修复后只增量检查原问题和新回归。
- **按原因回到正确路径。** 已知原因直接修，未知原因先诊断，范围变化才重新规划。

## 2.16.0 - 2026-07-13

**`grill-me` 成为独立 skill，只问真正影响结果的问题。**

- **问题只围绕用户决定。** 讨论只围绕用户必须决定的事项，不用可逆的语言、命名或内部布局凑问题。
- **Codex profile 控制子任务。** Codex 子任务按安装 profile 使用对应模型和推理强度，并支持最多九个并发线程。

## 2.15.0 - 2026-07-13

**你纠正方向后，旧任务会立即停下。**

- **过时方向立即停止。** 后台任务不会继续沿用过时方向，局部或未验证结果也不会被说成整体完成。
- **提醒只到主任务。** 可选提示音只提醒主任务，后台任务保持安静；只读诊断只显示 agent 设置和异常长任务，不输出对话正文。

## 2.14.0 - 2026-07-11

**Codex 的模型配置升级到 GPT-5.6，并提供更清晰的质量档位。**

- **Codex 提供四个质量档位。** `performance-first`、`cost-first`、`gpt56-high` 和 `gpt56-xhigh` 提供不同的模型与推理强度组合。
- **其他宿主保持原生映射。** Cursor 和 Claude Code 使用各自平台的原生模型映射，兼容 profile 名称继续可用。

## 2.13.0 - 2026-07-10

**信息够用时直接推进，不再为了模板增加仪式。**

- **额外流程按风险触发。** 假设清单、表格、长期记录、独立复查、测试先行和方案比较按风险与需要触发。
- **固定模型不可用时明确失败。** Codex 的 `gpt56-role` 按职责分配模型与推理强度，不可用时明确失败，不静默降级。

## 2.11.1 - 2026-07-08

**一行修复等小任务继续保持轻量。**

- **小任务不自动加流程。** 小任务不自动增加问题、子任务或长期计划；明确要求 `grill-me` 或先讨论时仍会暂停。
- **关键安装与更新决定会暂停。** 安装和更新遇到未回答的关键问题会停止等待。

## 2.11.0 - 2026-07-08

**复杂任务先查证，再把真正需要你决定的问题带回来。**

- **确认边界保持一致。** Research、Debug、Plan、Execute、Review 和 Goal 使用一致的确认边界。
- **更新比较版本与内容。** `check-update.sh` 会比较全局和项目安装的版本与实际内容。

## 2.10.0 - 2026-07-08

**Teamwork 的候选评估变得可比较，普通任务运行方式不变。**

- **日常使用保持不变。** 候选行为可以在采用前一致比较，不改变普通任务的运行方式。

## 2.9.0 - 2026-07-08

**发布前的保护开始覆盖完整工作边界。**

- **各类任务都有发布保护。** 简单任务、调试、调研、复查、Goal、安装和跨平台规则都会在采用前得到覆盖。

## 2.8.1 - 2026-07-08

**你要求先讨论时，所有依赖决定的动作都会真正暂停。**

- **依赖决定的动作会等待。** 分析、方向选择、编辑和分派都会等待确认。
- **改代码先找既有路径。** 改代码前先找到已经负责该行为的路径，复查会警惕无证据的分支、默认值和备用路径。
- **旧安装状态可发现。** 更新检查可以发现旧 skill、agent 或全局策略。

## 2.8.0 - 2026-07-08

**明确说“先问清楚”时，Teamwork 会先讨论，不会后台开工。**

- **讨论请求会真正触发。** “grill me”“先问清楚”或“challenge assumptions”会触发至少一个影响结果的问题和推荐。
- **执行等待确认。** 确认或退出前，不启动 Plan、实现、Goal 或 Worker 分派。
- **同版本漂移也可发现。** 更新检查会比较 skill 实际内容，即使版本号相同也能发现漂移。

## 2.7.1 - 2026-07-07

**改动前先找到真正负责行为的现有路径。**

- **既有路径与验证先明确。** 实施与验收先确认已有行为路径和验证方式，避免另造一套实现。
- **无证据复杂度被拒绝。** 三个平台都拒绝无证据增加分支、模式、包装、默认值或备用路径。

## 2.7.0 - 2026-07-01

**Codex 可以显式选择更高推理强度，同时减少仓促回答。**

- **Codex 可用 xhigh。** `gpt55-xhigh` 让 Codex 子任务使用 GPT-5.5 与 xhigh；Cursor 和 Claude Code 继续使用各自平台档位。
- **证据任务不再仓促。** 复杂任务更重视读源、解释、校验和验证，进度只保留决定、阻塞和验证信息。

## 2.6.0 - 2026-06-23

**调研不再停在第一份材料，缺少关键值也不会假装成功。**

- **Research 会继续查证。** Research 会继续寻找一手来源、相关来源、反例和未覆盖问题。
- **缺少关键值不猜。** 缺少路径、端口、模型、超参数、凭证、配置或不变量时，会询问、调查或停止。
- **Review 识别多余防御。** 复查会识别不必要的冗余、过度防御、静默默认值、隐藏 fallback 和回归。

## 2.5.0 - 2026-06-22

**长任务失败后先判断原因，不再盲目重跑。**

- **Goal 先分类失败。** Goal 保留尝试历史中的目标、假设、验证结果、失败类别和下一步，再区分证据不足、计划过期、范围错误或执行偏离。
- **项目初始化准备上下文。** 项目初始化开始准备项目记录与安装。

## 2.4.1 - 2026-06-21

**Cursor 全局规则可以一键复制到剪贴板。**

- **Cursor 规则可复制。** 新增 `./install.sh cursor-policy-copy`，readiness 检查会提醒手动粘贴 User Rules。

## 2.4.0 - 2026-06-21

**你可以直接用自然语言描述需求，由 Teamwork 选择处理方式。**

- **自然语言进入合适能力。** 普通请求更稳定地进入研究、诊断、计划、执行、复查、Goal、初始化或更新。
- **指导按需加载。** 简单任务保持接近原生的快速路径，大任务按需加载所需指导。

## 2.3.0 - 2026-06-21

**遇到 bug 先找根因，再决定怎么修。**

- **根因证据会完整收集。** 新增 `teamwork-debug`，收集复现步骤、日志、假设和运行证据，并区分根因、症状与证据不足；临时探针会清理。
- **Update remote 检测已修复。** `scripts/check-update.sh` 的 upstream remote 检测得到修复。

## 2.2.0 - 2026-06-16

**安装与更新状态开始可以直接检查。**

- **安装状态可见。** 新增 `scripts/check-update.sh`、已安装版本标记、`--project-root` 和更完整的项目级安装。
- **三平台内容与说明对齐。** 三个平台的安装内容与说明开始保持一致。

## 2.0.0 - 2026-06-16

**需求清楚时默认直接推进，只在真正阻塞时询问。**

- **行动优先。** Teamwork 从流程优先转为行动优先，确认与子任务规则聚焦于必要事项。
- **安装仍防止不完整内容。** 各平台安装继续避免使用不完整的包内容。

## 1.11.0 - 1.15.0 - 2026-06-11 to 2026-06-16

**Skills 开始按需加载，简单请求占用更少上下文。**

- **Skills 按需加载。** 简单请求占用更少上下文，深入调研只把有用证据带回主对话。
- **更新与时效查询增强。** 安装更新和当时最新库、API 文档查询逐步完善。

## 1.5.0 - 1.10.0 - 2026-06-05

**Teamwork 开始支持跨回合协作、更安全的决定边界和完成条件检查。**

- **持久上下文更安全。** 长期工作可跨回合保留重要上下文，外部 memory 导入更谨慎，澄清边界、多角色证据要求和项目初始化保护逐步加强。
- **缺少必需值时明确失败。** 必需值缺失时不猜默认值，同时保留可检查性并减少流程负担。

## 1.2.0 - 1.4.1 - 2026-06-04 to 2026-06-05

**Codex 安装开始提供成本与性能两种偏好。**

- **安装偏好控制子任务默认值。** `performance-first` 和 `cost-first` 会按所选偏好调整子任务默认配置。

## 1.0.0 - 1.1.2 - 2026-06-01 to 2026-06-04

**多角色协作骨架正式成形。**

- **职责与交接分开。** 研究、执行、验收等职责与子任务交接开始分开，复杂任务更容易完成收尾。

## 0.14.0 - 2026-06-01

**Codex 的 Teamwork 授权可以跨项目复用。**

- **授权可以跨项目复用。** Codex 的 Teamwork 授权只需全局安装一次，项目无需重复说明子任务权限。

## 0.13.0 - 2026-05-31

**Codex 并行子任务的授权边界更明确。**

- **并行分派边界更清楚。** 更新子任务授权策略，减少在未获授权的范围内分派并行任务的风险。

## 0.12.0 - 2026-05-28

**Claude Code 成为一等支持平台。**

- **Claude Code 支持完整落地。** 新增 Claude Code 安装、说明和角色支持。

## 0.11.0 - 2026-05-27

**Cursor 成为一等支持平台。**

- **Cursor 支持完整落地。** 新增 Cursor 安装、说明、子任务协作和长期任务支持，并按平台能力分别描述。

## 0.10.0 - 2026-05-27

**先检查子任务能力，再判断能否分派或独立验收。**

- **先查能力，再独立验收。** 不再过早断言子任务不可用；需要独立验收的结果必须来自全新上下文。

## 0.9.0 - 2026-05-27

**Teamwork 首次成为有版本、可安装的协作工作流包。**

- **可安装包的基础成形。** `teamwork-init` 带来项目初始化，调研、规划、执行、复查、Goal、初始化和更新开始各自聚焦，并加入自动路由、持久记录和基于证据的复查。

## Pre-0.9.0 - 2026-05-12 to 2026-05-26

**Teamwork 从一个优化 skill 逐步演变成多阶段协作系统。**

- **协作能力逐步拆分。** 调研、规划、执行、复查和长期 Goal 陆续成为独立能力，并逐步加入证据检查、持久计划与记录、Goal 命令和 Codex 路由。
