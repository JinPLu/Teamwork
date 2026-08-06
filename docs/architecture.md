# Teamwork Architecture

Teamwork separates model-facing behavior from implementation infrastructure so ordinary work stays fast and specialized methods remain understandable.

## Model-facing layers

### 1. Global principles

`policy/teamwork-global.md` is the sole readable owner of five durable
principles. Installers only render host-specific wrappers:

1. Keep clear work native.
2. Distinguish observation, inference, unknowns, and completed work.
3. Calibrate verification to the credible risk and the claim being made;
   prefer direct outcome evidence.
4. Admit a defensive control only when an observed failure, explicit contract,
   or boundary created by the current authorized action supports it, and only
   when it changes the action, stop condition, or conclusion. Use the smallest
   sufficient control, and do not autonomously introduce hashes, digests,
   checksums, or content fingerprints.
5. Route to a named Skill only when its public trigger and host route match.

Host and tool permissions remain authoritative. Importance, complexity, and
subjective risk do not activate a Teamwork workflow. Teamwork's own source,
formats, protocols, and validation use no hash, digest, checksum, or content-
fingerprint machinery.

### 2. Routing

`SKILL.md` descriptions are the semantic routing source. `agents/openai.yaml` is UI metadata, not a second behavior contract.

The selected public methods are Collaborate, Research, Debug, Plan, Review, Goal, Init, and Update. Their number is not an architectural invariant. Local evidence routes internally to Explorer. Strict adversarial work routes to Challenger.

### 3. Skill methods

Each Skill is self-contained and uses progressive disclosure:

- metadata contains the trigger and exclusion boundary;
- `SKILL.md` contains the concise core method;
- one-level references contain only complex optional protocols.

There is no public router, generic Execute Skill, cross-Skill behavior loading, fixed dispatch count, or workflow-wide transaction ceremony.

### 4. Agent responsibilities

Researcher, Explorer, Debugger, Challenger, Planner, Reviewer, Worker, and Writer have narrow responsibilities. Root owns Collaborate, Goal, and user dialogue. Reviewer covers both execution and plan review. Worker preserves unrelated work. Writer maintains documents without changing facts, decisions, authority, or completion.

A required Agent is active only when the host selects that installed role.
Naming a task after the role, or repeating a purported result in Root's own
text, is not Agent activation. On a Codex surface that exposes it, the policy
adapter selects named roles through `spawn_agent.agent_type` and a
self-contained or bounded-history assignment; a full-history fork inherits
Root's role. Static profiles and `features.multi_agent` configuration establish
only installed state. A live child-start observation proves exact activation;
without it, the Agent-dependent path is unsupported or failed. Teamwork does
not create, delete, or enable the user's under-development host feature to
change that result. Cursor and Claude Code adapters may keep native named Agent
selectors for compatibility and development, but Teamwork 7.1 does not treat
them as supported, release-qualified, or release-blocking surfaces.

## Typed project documents

Writer is the sole ordinary semantic writer. It creates a document only when
material reusable content first appears, updates it on a material semantic
change, and finalizes it at the owning stage boundary. The six types are:

- `discussions/` for decisions, options, trade-offs, and settled choices;
- `research/` for full Deep Research evidence and conclusions;
- `debug/` for failure boundaries, causal evidence, fixes, and verification;
- `plans/` for selected-direction executable plans;
- `reviews/` for candidate evidence, findings, and verdicts;
- `reports/` for Goal, Init, Update, and reusable execution outcomes.

`docs/teamwork/index.json` groups one or more typed paths under a human-readable
task key with a title, one-sentence summary, search terms, lifecycle status, and
document statuses. It does not copy document content or create a second identity
system. Explorer has no standalone document; its evidence goes to the consumer.

Skills state what each document must communicate. Same-scope editorial or link
corrections may update a final document in place; materially new semantic scope
creates a new same-type document and preserves the earlier conclusion.

## Storage and migration

Schema v4 storage is deliberately small: normalized typed paths, index schema
validation, task/document registration, discovery, and lifecycle updates. It
does not summarize prose and contains no cases, manifests, artifacts, claims,
lineage, content identities, hashes, digests, or sealed evidence.

Normal readers accept only schema v4. Older project records enter through the
explicit Update path, never through runtime compatibility branches. Writer
reorganizes every source record by meaning, scripts handle bounded mechanics,
and an independent Reviewer reads the actual migrated corpus. With an exact
project root, Update migrates every Teamwork document before normal work
resumes; without one it reports migration as pending.

Teamwork does not replace retired hash machinery with byte comparison,
fingerprints, opaque IDs, or another sealing layer.

## Canonical and generated surfaces

- `skills/` owns Skill behavior.
- `templates/*-agents/` owns host agent templates.
- `policy/teamwork-global.md` owns the global policy;
  `scripts/install/policy.sh` transports it to hosts.
- `config/teamwork-topology.json` owns the current mechanical inventory and retired names, not behavior.
- `scripts/build-codex-plugin.py` generates `plugins/teamwork-skill/`.

Generated plugin files are never edited directly.

## Evidence lanes

Keep claims scoped to their evidence:

1. **Structural evidence** validates topology, schema, generated synchronization,
   version, and file layout. It proves structure only.
2. **Behavioral evidence** observes the installed, changed or reasserted public
   behavior on the relevant Codex path. The trajectory binds the case's
   requested authority and retains any disposable scenario candidate outside
   the scenario lifetime; model and effort are invocation choices, not inferred
   behavior claims. Cursor and Claude Code adapter observations are
   compatibility/development evidence only.
3. **Semantic evidence** comes from an independent Reviewer reading the actual
   output or artifact against outcome-based criteria.

The live Codex evidence manifest declares each case as required or
`conditional-exact-role`. Required cases must pass. A conditional case may
retain a precisely classified missing-role `UNSUPPORTED` observation without
turning it into success, claiming that capability, or claiming that all
conditional cases passed; missing declarations and other failures remain
blockers.

A dry run proves only configuration and command shape. The local host gate
checks evidence presence and consistency without scoring answer length or
wording. Tests and structural checks never stand in for semantic correctness.
Missing required observed or review evidence stays missing instead of being
rewritten as success.
