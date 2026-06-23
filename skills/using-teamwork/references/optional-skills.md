# Optional Skills

External skills are tool substrates, not Teamwork roles. Ask before installing,
configuring, granting credentials, or using a write-capable inactive skill.
Already-available read-only lookup tools may be used when their data boundary
fits the task.

## Install Flow

1. **Ask**: confirm user intent, expected capability, and approval to install,
   configure, grant credentials, or run write-capable actions.
2. **Check duplicates**: prefer an active plugin or built-in tool over a new local skill.
3. **Verify**: source/license or trust note, trigger scope, credential needs, write risk.
4. **Smoke test**: run a read-only probe or minimal invocation before relying on the skill.
5. **Record decision**: `use plugin`, `install`, `adapt`, `defer`, or `reject` with reason.

Reject broad community packs, write-capable automation loops, or unclear licenses until a per-skill audit passes. Document `deferred` when credentials or smoke test are unavailable; do not install speculatively.

## Candidate Record

For each candidate record: Source/License · Capability and Role Fit · No duplicate check · Credentials and privacy boundary · Write Risk · Smoke Test result · Decision.

Do not maintain a static external-skill inventory in runtime instructions.

## Memory and Docs Graph Skills

For memory integration or docs graph tools, also record:

- Canonical Boundary: recall/search/graph output is candidate context, not Teamwork truth.
- Data Scope: repository-only, personal, team, or external docs.
- Promotion Gate: evidence path, currentness, protected-data check, and Memory Delta owner.
- Smoke Test: read-only search/status/API probe before writes or MCP registration.

Decision stays `defer` or `adapt` when schema, credentials, privacy, or write-risk evidence is incomplete.

## Docs MCP (Context7-class)

Use CodeGraph for local code structure; use the docs MCP for current external library, framework, SDK, or API documentation. Treat as optional docs graph candidate, not a Teamwork dependency.

Send only sanitized library names, IDs, versions, and topic queries. Never send
private source, prompts, customer data, or proprietary details. Read-only lookup
is allowed when already available; MCP/plugin installation, API key setup, or
repository config changes require explicit user approval.

Smoke test: resolve a public library and retrieve a small result before relying on it.
