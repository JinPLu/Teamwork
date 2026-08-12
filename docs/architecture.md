# Teamwork Architecture

Teamwork is a small collection of optional methods around native work.

## Runtime flow

1. Root reads the user's request and the repository instructions.
2. Clear authorized work stays native.
3. A named Skill is loaded only when its public trigger matches.
4. Root may delegate a bounded, independent subtask when doing so is useful.
5. Root integrates the result, performs the authorized work, and verifies the
   outcome in proportion to the claim.

There is no router, mandatory stage chain, readiness preflight, document schema,
case lifecycle, or automatic Update detour.

## Agent handoff

Every handoff uses the same five fields:

- objective;
- owned scope;
- settled user constraints;
- available evidence;
- requested return.

Researcher, Explorer, Debugger, Challenger, Planner, Reviewer, and Worker are
focused helpers. They do not own the user dialogue. Missing
agents do not block native work. When the user specifically requires an
independent review and no independent context is available, Root labels the
review non-independent instead of pretending otherwise.

## Sources and installation

- `skills/` owns behavior.
- `templates/*-agents/` owns optional host agent profiles.
- `policy/teamwork-global.md` is the sole owner of universal authorization and
  mechanism rules.
- `scripts/install/` owns installation mechanics.
- `plugins/teamwork-skill/` is generated from canonical sources.

The default install and Update path is Codex-only. Cursor and Claude Code remain
explicit compatibility targets.

## Verification

The default validation command checks syntax, Skill metadata, Codex profiles,
project initialization, and bundle synchronization. Release-only version and
packaging checks run only with `--release`. Tests and markers never substitute
for reading the actual result.
