# Codex

Codex is Teamwork's supported runtime. Install from Marketplace, then run
`$teamwork-update` in a new task when you want to refresh the installation.

Clear work stays native. A Skill is selected only by its trigger. Specialized
Agents are optional bounded helpers; their availability, installed version, or
static routing state does not gate native work.

The eight optional roles are Researcher, Explorer, Debugger, Challenger,
Planner, Reviewer, Worker, and Writer. Root sends a five-part brief: objective,
scope, settled constraints, evidence, and requested return. Root owns
integration, user dialogue, and confirmation of what enters the mainline.

Writer is a low-cost, non-blocking recorder. A method owner certifies the
semantic delta; Writer expresses that delta in plain Markdown without changing
facts, decisions, authority, or completion. One Writer may be reused across
Skills, but that reuse shares only the Agent lifecycle: each Skill retains
ownership of its own meaning. Writer failure is reported and never blocks the
main work; if the document itself was explicitly requested, only that delivery
remains incomplete.

Reusable content has six document semantics under `docs/teamwork/`: Discussion
records choices and trade-offs; Research records external evidence and
synthesis; Debug records failure boundaries, causal reasoning, repair, and
verification; Plan records executable steps for a selected direction; Review
records candidate evidence, findings, and verdict; Report records reusable
status and outcomes. Each plain Markdown document maintains a current synthesis
plus chronological history at Skill-defined semantic checkpoints, using
`<YYYY-MM-DD>-<slug>.md` and reusing the path for the same stable identity.
These documents require no Case, schema, JSON index, migration, or readiness
gate.

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
