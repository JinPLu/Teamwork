# Teamwork

Teamwork 是一组给 Codex 使用的轻量协作 Skills。它只有一个默认原则：
**清楚、已授权的工作直接做；只有请求确实匹配时才加载专项方法。**

它不再维护 Router、固定阶段链、Case、项目文档 schema、Writer、全局
readiness 门或版本前置检查。

## 实际工作流

```text
用户请求
  → Root 判断是否需要专项 Skill
  → 可选：把独立、边界清楚的子任务交给 subagent
  → Root 汇总并完成被授权的工作
  → 对真实结果做相称验证
```

subagent 交接只需要五项：

1. 目标；
2. 负责范围；
3. 已确定的用户约束；
4. 当前证据；
5. 期望返回。

Agent 不可用不会触发 Update，也不会阻塞原本可以直接完成的工作。只有用户明确
要求“独立审查”而宿主无法提供独立上下文时，Root 才需要如实说明审查并不独立。

## Skills

| 请求 | Skill | 作用 |
|---|---|---|
| 一起讨论、比较方向 | `$teamwork-collaborate` | 形成选项、权衡和决定 |
| 深度外部调查 | `$teamwork-research` | 多来源、逐主张证据综合 |
| 未知原因的故障 | `$teamwork-debug` | 先定位原因，再按授权修复 |
| 已选方向的执行计划 | `$teamwork-plan` | 产出可执行任务和验证关系 |
| 稳定候选的复查 | `$teamwork-review` | 按需求与直接证据给出结论 |
| 持续做到成功信号出现 | `$teamwork-goal` | 为原任务增加持续推进 |
| 添加项目 Teamwork 指令 | `$teamwork-init` | 只维护一个简短 AGENTS.md block |
| 检查或刷新全局安装 | `$teamwork-update` | 默认只处理 Codex 安装面 |

普通代码修改、文件阅读、单页查询、已知原因的小修复都不需要先调用 Teamwork Skill。

## Agent 行为

Teamwork 保留七个可选内部角色：Researcher、Explorer、Debugger、Challenger、
Planner、Reviewer、Worker。

- Root 始终负责用户沟通、集成和最终结果。
- Agent 只处理 brief 中的范围。
- 子任务失败只影响该子任务；Root 可以采用其他可用工具继续。
- Reviewer 只读且不修复自己的发现；其他角色不需要制造额外记录。

## 安装

Codex Marketplace 是默认安装方式：

```text
codex plugin marketplace add JinPLu/Teamwork
codex plugin add teamwork-skill@teamwork
```

然后在新任务中运行 `$teamwork-update`。Checkout 开发安装可查看：

```bash
./install.sh --help
```

`update` 默认只刷新 Codex。Cursor 和 Claude Code 是显式选择的兼容开发目标，
不会参与 Codex readiness 或阻塞普通工作。

## 项目初始化

```bash
./install.sh --project-root /absolute/project/path init-project
```

这个命令只在 `AGENTS.md` 中添加或刷新一个小的 managed block。它是幂等的，
不会创建 `docs/teamwork`、Case、索引、schema、迁移状态或其他运行时文件。

## 验证

```bash
./scripts/validate.sh
```

默认命令只做快速核心 smoke：语法、Skill 元数据、Codex profiles、项目初始化、
readiness 非阻塞行为和生成插件同步。显式发布准备才运行：

```bash
./scripts/validate.sh --release
```

安装状态也可以单独查看：

```bash
./scripts/check-update.sh --readiness
```

它只返回诊断信息，退出成功，不会授权或阻止其他任务。

## 开发原则

- `skills/` 是行为真源。
- `templates/*-agents/` 是可选角色 profile。
- `policy/teamwork-global.md` 是最小全局原则。
- `plugins/teamwork-skill/` 是生成包，修改 canonical 后重新生成。
- 未知或用户拥有的安装文件不会被覆盖。
- 全局授权与机制规则只维护在 `policy/teamwork-global.md`。

许可证：[MIT](LICENSE)
