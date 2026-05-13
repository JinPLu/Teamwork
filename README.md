# Run-Analyze-Optimize Skill

Lightweight run/analyze/optimize workflow package for Claude Code, Codex, and
Cursor. The source of truth is the four skills under `skills/`; platform docs
only explain installation and runtime entrypoints.

## Why Use It

- Evidence-first: decisions must trace to files, diffs, logs, tests, artifacts,
  or command output.
- Role-separated: research, plan, execute, and review stay as distinct passes.
- Lightweight: no model registry, pricing cache, dispatch platform, or ledger.
- Runtime-aware: Codex uses native goals/subagents; Claude can use `/rao:*` plus
  a Stop hook for bounded continuation.

## Topology

```text
skills/run-analyze-optimize/SKILL.md  # router + mode: goal
skills/run-analyze-design/SKILL.md    # mode: research | mode: plan
skills/run-analyze-execute/SKILL.md   # accepted-plan execution
skills/run-analyze-review/SKILL.md    # mode: plan | mode: execution
```

`run-analyze-optimize` routes by user intent:

| Intent | Route |
|---|---|
| Research options, causes, or tradeoffs | `run-analyze-design` with `mode: research` |
| Turn a chosen direction into worker steps | `run-analyze-design` with `mode: plan` |
| Execute an accepted plan | `run-analyze-execute` |
| Review a plan | `run-analyze-review` with `mode: plan` |
| Review a diff, artifact, or execution result | `run-analyze-review` with `mode: execution` |
| Iterate to verified success or a blocker | `run-analyze-optimize` with `mode: goal` |

## Install

Claude skills:

```bash
./install.sh claude
```

Codex skills:

```bash
./install.sh codex
```

Cursor project rule:

```bash
./install.sh cursor /path/to/project
```

All entrypoints:

```bash
./install.sh all /path/to/cursor-project
```

The installer installs the current four skills and removes only known retired
symlinks that point back to this repository.

## Usage

Route a task through the workflow:

```text
run-analyze-optimize: research why pytest X fails, propose options, then write a plan
```

Execute an accepted plan:

```text
run-analyze-execute: implement the accepted plan with minimal edits and run the focused verification
```

Review a completed execution:

```text
run-analyze-review mode: execution: review this diff and verification evidence
```

Run a Claude goal with bounded continuation:

```text
/rao:goal fix pytest X, max 3 iterations, stop on no progress --max-iterations 3
```

## Codex runtime

Codex uses the same four skills as the stable entrypoint. Use native Codex
plans, goals, subagents, MCP, sandbox approvals, and `codex review` as described
in `CODEX.md`; do not use the Claude `/rao:*` Markdown goal runtime as the Codex
goal backend.

## Claude `/rao:*` runtime

Claude Code plugin installs can manage a project-local autonomous goal:

```text
/rao:goal <objective> [--max-iterations N] [--completion-promise TEXT]
/rao:status
/rao:pause
/rao:resume
/rao:stop
/rao:complete
/rao:clear
/rao:note <note>
```

State lives at:

```text
.claude/run-analyze-optimize-goals/
```

The `Stop hook` continues active goals until verified completion, max
iterations, user stop, or a hard blocker. The default completion promise is:

```text
<promise>RAO_GOAL_COMPLETE</promise>
```

Auto-completion requires both that exact promise and this structured completion
audit in the final assistant message:

```text
<completion_audit>
<requirements_mapping>map each requirement to direct evidence</requirements_mapping>
<verification_evidence>commands, artifacts, or inspected evidence</verification_evidence>
<review_verdict>pass</review_verdict>
<dissent>none or preserved dissent/residual risk</dissent>
</completion_audit>
```

`review_verdict` must be `pass` or `pass-with-notes`. A promise without the
audit is blocked unless max iterations have already been reached. `/rao:complete`
is a manual override and is logged as manual completion.

## Validate

```bash
./scripts/validate.sh
```

Validation checks skill topology and frontmatter, manifests, installer smoke,
Cursor rule size, Claude command/hook presence, Stop-hook completion gating,
and required thin-doc references.

## Publish

```bash
git remote add origin git@github.com:<owner>/run-analyze-optimize-skill.git
git push -u origin main
```

GitHub CLI:

```bash
gh repo create run-analyze-optimize-skill --public --source=. --remote=origin --push
```
