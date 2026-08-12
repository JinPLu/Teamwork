# Codex

Codex is Teamwork's supported runtime. Install from Marketplace, then run
`$teamwork-update` in a new task when you want to refresh the installation.

Clear work stays native. A Skill is selected only by its trigger. Specialized
Agents are optional bounded helpers; their availability, installed version, or
static routing state does not gate native work.

The seven optional roles are Researcher, Explorer, Debugger, Challenger,
Planner, Reviewer, and Worker. Root sends a five-part brief: objective, scope,
settled constraints, evidence, and requested return. Root owns integration and
user dialogue.

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
