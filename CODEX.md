# Codex

Codex is Teamwork's supported runtime. Install from Marketplace, then run
`$teamwork-update` in a new task when you want to refresh the installation.

Clear work stays native. A Skill is selected only by its trigger. Specialized
Agents are optional bounded helpers; their availability, installed version, or
static routing state does not gate native work.

The eight optional roles are Researcher, Explorer, Debugger, Challenger,
Planner, Reviewer, Worker, and Writer.
<!-- BEGIN GENERATED: host-counts -->
Claude Code installs 7 roles and omits Explorer because that host already provides Explore. Cursor installs 6 roles and omits Explorer and Debugger, and does not install the Debug or Goal Skills; unknown-cause diagnosis uses host Debug. Codex retains the Explorer role, plus Debug, Goal, and Debugger.
<!-- END GENERATED: host-counts -->
Root sends a five-part brief: objective,
scope, settled constraints, evidence, and requested return. Root owns
integration, user dialogue, and confirmation of what enters the mainline.

Writer is a helper role, not a Skill. Explicit Skill invocation remains
`$name`. Native Plan proposals are candidates until the user approves them.
Native questions collect input and do not by themselves create a document.
After the user accepts a reusable result, apply the matching Persistence
contract under
<!-- BEGIN GENERATED: kind-root -->
`docs/teamwork/<kind>/`
<!-- END GENERATED: kind-root -->
, then continue with native execution approval.

Project setup adds only one managed block to `AGENTS.md`:

```bash
./install.sh --project-root /absolute/project/path init-project
```

Check installation state without creating a workflow gate:

```bash
./scripts/check-update.sh --readiness
```

Run the fast local smoke suite with `./scripts/validate.sh`; use `--release`
only during explicit release preparation.
