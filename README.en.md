<p align="center">
  <img src="assets/teamwork-readme-teaser-v7.png" alt="Teamwork: clear tasks stay direct, eight focused Skills join when a method is needed, and eight Agent roles help reach a verified result" width="860">
</p>

<h1 align="center">Teamwork</h1>

<p align="center">
  <strong>Let AI work directly when it should, and bring in a method only when the task needs one.</strong><br>
  AI/human collaboration Skills for Codex, with less ceremony, clearer boundaries, and more credible results.
</p>

<p align="center">
  <a href="https://github.com/JinPLu/Teamwork/releases"><img src="https://img.shields.io/github/v/release/JinPLu/Teamwork?display_name=tag&amp;sort=semver" alt="Latest release"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-2563EB" alt="MIT License"></a>
  <img src="https://img.shields.io/badge/supported-Codex-0F766E" alt="Officially supports Codex">
</p>

<p align="center">
  <a href="README.md">中文</a> ·
  <a href="CHANGELOG.en.md">Changelog</a> ·
  <a href="CODEX.md">Codex</a> ·
  <a href="CURSOR.md">Cursor</a> ·
  <a href="CLAUDE.md">Claude Code</a> ·
  <a href="docs/architecture.md">Architecture</a>
</p>

---

> [!TIP]
> **You do not need to memorize eight Skills.** Describe the outcome directly most of the time. Name a `$teamwork-*` Skill only when you want precise control over discussion, research, debugging, planning, or review.

## 🚀 Start in one minute

### Codex: use the Marketplace plugin

```bash
codex plugin marketplace add JinPLu/Teamwork
codex plugin add teamwork-skill@teamwork
```

Start a new Codex task and run:

```text
$teamwork-update
```

The first setup lets you choose `performance-first` or `cost-first`, then decide independently whether to enable managed CodeGraph and the local GPU Broker. Codex installs and reads back its Skills, Agents, routing, and managed global-policy block regardless of those optional capabilities.

Now ask for the result directly:

```text
Implement this validation change, verify the real affected path, and stop when it works.
```

When the outcome and boundary are clear, Teamwork does not manufacture a workflow first. If you want to shape the direction together, try:

```text
Use $teamwork-collaborate to compare three onboarding directions with me. Recommend first, then ask only what could change the choice.
```

To create current-format project instructions and Teamwork documents in a new repository:

```text
Use $teamwork-init to initialize this project.
```

<details>
<summary><strong>Compatibility adapters and development checkout</strong></summary>

Teamwork 7.1 officially supports and release-qualifies Codex only; release blocking applies only to Codex evidence. The Cursor and Claude Code source adapters remain for compatibility maintenance and local development; they are not release-qualified platforms and are not recommended as normal supported install paths.

```bash
git clone https://github.com/JinPLu/Teamwork.git
cd Teamwork
./install.sh codex
./scripts/check-update.sh --readiness
```

When maintaining a compatibility adapter, install that development target directly:

```bash
./install.sh cursor
./install.sh claude
./install.sh codex   # development or manual Codex setup only
```

Choose the lower-cost profile for a Codex development install with:

```bash
./install.sh codex --profile cost-first
```

The Cursor compatibility adapter also needs `./install.sh cursor-policy-copy`, followed by a review and paste of the same global policy into **Cursor Settings → Rules → User Rules**. Teamwork cannot observe that setting, so Cursor readiness honestly remains `manual action required` / partial. See the [Cursor guide](CURSOR.md) and [Claude Code guide](CLAUDE.md) for adapter details.

Codex static installation checks prove only that Agent profiles and the stable `multi_agent` configuration are present; they do not prove exact named-Agent activation. An Agent-dependent path must observe that role in a live run. The stable Codex CLI 0.144 path retains `UNSUPPORTED` when it cannot provide that evidence instead of pretending to pass. Teamwork does not create, delete, or enable the user's under-development `multi_agent_v2` setting.

</details>

## 🧭 Use what is missing now

| What you are missing | Use | What it solves |
| --- | --- | --- |
| An acceptable direction | 💬 `$teamwork-collaborate` | Discuss, co-design, compare, brainstorm, or help unformed intent and preferences become clear. |
| Deep external or current evidence | 🔎 `$teamwork-research` | Research across official documentation, papers, or other reliable sources, reconcile conflicts, and return traceable conclusions. |
| The cause of a real failure | 🐞 `$teamwork-debug` | Start from the observed failure, discriminate among hypotheses, confirm the cause, and repair the same path only when already authorized. |
| Executable steps | 📝 `$teamwork-plan` | Turn a clear direction into owned steps with dependencies, verification, and stop conditions. |
| Independent judgment | ✅ `$teamwork-review` | Review stable code, documents, plans, artifacts, or claims, with findings before the verdict. |
| Persistent progress | 🎯 `$teamwork-goal` | Only when explicitly requested, continue until a real success signal passes or a genuine blocker appears. |
| Fresh current-format project context | 🧰 `$teamwork-init` | Create fresh Teamwork context and an empty schema-v4 index under one exact project root; use Update for installed-state repair or older-document migration. |
| Global refresh or old-document migration | 🔄 `$teamwork-update` | Refresh global Teamwork and, with an exact project root, migrate every older Teamwork document in that project. |

Local code, configuration, logs, tests, and history are gathered read-only by the internal Explorer Agent, not by a public Explore Skill. Routine web lookup stays native. Research is for external questions that genuinely need multi-source synthesis.

## 🛣️ The four most common paths

### 1. The outcome and change are clear

```text
Change the login timeout logic directly. Verify only the related tests and real login path.
```

**Path:** native host inspection → edit → verification.

No Router, Execute, or Agent dispatch is required first.

### 2. The direction is still open

```text
Use $teamwork-collaborate to compare synchronous, queued, and hybrid API designs and help me converge on an acceptable direction.
```

**Path:** Collaborate → user accepts a direction → Plan when useful → separately authorized implementation.

Discussion, planning, and acceptance do not authorize code changes by themselves.

### 3. There is a failure, but the cause is unknown

```text
Use $teamwork-debug to reproduce this CI failure, confirm the cause, repair it, and rerun the same path.
```

**Path:** Debug diagnosis → narrow repair → same-path verification.

If the cause and narrow repair are already clear, fix it directly instead.

### 4. A decision depends on external facts

```text
Use $teamwork-research to read official documentation and recent changes, then give me a sourced recommendation.
```

**Path:** Research → sourced conclusion; return to Collaborate only when a real user choice remains.

Review is an optional independent acceptance gate. An ordinary release uses one independent semantic Reviewer; Strict Review appears only when the current change actually crosses permission or security, irreversible user data, persistent-data migration, or a changed public compatibility contract. Goal is an explicitly requested persistence wrapper. Neither belongs in every task by default.

## 📋 Copy-ready prompts

```text
# Think together
Use $teamwork-collaborate to brainstorm a lower-maintenance release flow with me. Synthesize the current state and real options first, then ask the most useful question.

# Research deeply
Use $teamwork-research to read only official sources and key papers, compare the options, and provide traceable citations.

# Inspect local evidence read-only
Do not edit yet. Map the authentication flow, related configuration, and tests, then tell me the real change boundary.

# Diagnose a failure
Use $teamwork-debug to reproduce this error, discriminate among the likely causes, then fix and verify the same path once confirmed.

# Write a plan
Use $teamwork-plan to turn the selected migration direction into owned steps with dependencies, acceptance criteria, and stop conditions. Do not execute it.

# Review independently
Use $teamwork-review to check this diff against the requirements, focusing on false success, missed paths, and stale documentation.

# Persist to completion
Use $teamwork-goal to keep fixing until the named check passes. Stop only for a genuine blocker.
```

## 🧩 What Skills, Agents, and the host each own

| Layer | Responsibility | Do you operate it directly? |
| --- | --- | --- |
| ⚡ Native host path | Clear explanations, lookup, local inspection, edits, and verification. | Yes. Describe the outcome. |
| 🧭 Eight public Skills | A focused method with a clear trigger and boundary. | Optional. Name one when exact selection matters. |
| 🤝 Eight internal Agent roles | Researcher, Explorer, Debugger, Challenger, Planner, Reviewer, Worker, and Writer. | Usually no. Root owns dispatch, integration, and user dialogue. |

Challenger is only for an explicit strict adversarial challenge. Reviewer covers both implementation and plan review. Teamwork defines no fixed Agent count or daily dispatch cap, and importance, complexity, or risk alone does not activate a workflow.

## 🗃️ Put reusable content where it belongs

When a task produces reusable content, Writer maintains six typed documents instead of compressing every stage into one live document:

| Content | Directory | What it preserves |
| --- | --- | --- |
| Discussion and decisions | 💬 `discussions/` | Options, trade-offs, settled choices, and the next meaningful question batch |
| Deep research | 🔎 `research/` | Conclusions, source census, claim evidence, contradictions, coverage audit, and stop basis |
| Debugging | 🐞 `debug/` | Failure boundary, causal evidence, fix, and same-path verification |
| Planning | 📝 `plans/` | Selected direction, owners, dependencies, verification, and stop conditions |
| Review | ✅ `reviews/` | Actual candidate, direct evidence, findings, and semantic verdict |
| Results | 📌 `reports/` | Goal, Init, Update, and reusable execution outcomes |

`docs/teamwork/index.json` groups several documents under one readable task key. Writer writes only when reusable content first appears or its meaning materially changes. A finalized document can receive same-scope prose or link corrections in place; a new decision, failure, or candidate creates another document of the same type. Explorer evidence goes to its consumer instead of creating a side record.

Codex and its permissions still control files, tools, credentials, and external effects. Cursor and Claude Code compatibility adapters remain governed by their hosts. Teamwork creates no second authorization system. Discussing or accepting a plan does not authorize execution.

> [!IMPORTANT]
> **Teamwork 7.1 keeps no normal-runtime compatibility for older document formats.** Update is the only older-document migration path. With an exact project root, Writer reorganizes every older Teamwork document by meaning, scripts handle only mechanics, and an independent Reviewer reads the actual migrated result. After acceptance, normal runtime uses only schema v4 and has no legacy reader. Valid Teamwork 7 install preferences remain reusable; the incompatible change here is the project-document format.

Use the CLI to refresh the global install and inventory whether one project
needs semantic migration:

```bash
./install.sh --project-root /path/to/project update
```

The CLI does not replace Writer's semantic work. When it finds an older format,
it leaves the project unchanged, reports the inventory, and asks you to run
`$teamwork-update` in a host so Writer can transform the corpus and Reviewer can
read the actual result before cutover. Without an exact project root, the CLI
completes the global refresh and reports `project migration pending`.

## 🔄 Updates

Codex plugin:

```bash
codex plugin marketplace remove teamwork
codex plugin marketplace add JinPLu/Teamwork
codex plugin add teamwork-skill@teamwork
```

Then start a new task and run `$teamwork-update`.

Checkout:

```bash
git pull --ff-only
./install.sh codex
./scripts/check-update.sh --readiness
```

To receive new-version notifications, choose **Watch → Custom → Releases** on [JinPLu/Teamwork](https://github.com/JinPLu/Teamwork).

## 📚 Keep exploring

- [Changelog](CHANGELOG.en.md): user-visible changes and upgrade notes.
- [Codex](CODEX.md): officially supported setup and troubleshooting.
- [Cursor](CURSOR.md) and [Claude Code](CLAUDE.md): retained compatibility/development adapter notes.
- [Architecture](docs/architecture.md): four model-facing layers, canonical owners, storage, and release evidence.
- [Contributing](CONTRIBUTING.md): change conventions and validation commands.
- [GitHub Issues](https://github.com/JinPLu/Teamwork/issues): report a problem or suggest an improvement.
