# Codex installed live protocol

Run only through `run-installed-codex-teamwork-live-eval.py` with a prepared
declared release case and explicit parent model and effort as invocation
configuration. `codex` must resolve to an absolute executable path and report
its version; both are retained on every trajectory. The runner uses
supported isolated authentication, installs into a disposable home, and gives
every case a fresh scenario. For the declared Codex release matrix, use a
600-second invocation deadline so the complete observed role path can return
its final answer; a timeout remains a blocking failed observation, never an
accepted result. The cost-first matrix uses a `gpt-5.6-terra`/`high` parent;
the installed role profiles select the child models and efforts.

Child cases require observed host-native role identity. Model and effort select
the invocation but are not inferred as child behavior or used as release-pass
evidence. The record binds the case's requested authority; Codex receives that
request through its sandbox argument. Missing observations, privacy leakage, or
missing direct evidence is `UNSUPPORTED` or `FAIL`, never an inferred pass.
For a manifest pair declared `conditional-exact-role`, only a missing required
Agent observation may be retained as expected `UNSUPPORTED`; required pairs
still need `PASS`, and authentication, route, command, scenario, or output
failures remain blockers.
Scenario cases retain the actual disposable candidate beside the trajectory.
The local gate requires a real final answer but does not score its wording,
length, or correctness except where a declared case directly validates its own
concrete outcome. Semantic acceptance requires an independent Reviewer to read
the answer and retained candidate.

## Publishable behavioral receipt

After the installed Codex runner has written its trajectory slices, run the
release-matrix verifier. Its `matrix-summary.json` is the single redacted
receipt suitable for manual publication: each slice names its relative
trajectory path, retained Codex version value or values, observation time
window, and every case outcome.
An `UNSUPPORTED` outcome is acceptable only when its case outcome says
`conditional-unsupported`; its retained classification is
`required-agent-not-observed`.

The verifier summarizes supplied installed-host trajectories; it does not run
Codex itself. Its `evidence_scope` is behavioral only and explicitly excludes
fresh-host execution, semantic acceptance, and release readiness. Static
validation does not produce a live-run claim: without retained installed
trajectory output, there is no matrix receipt to publish. Keep raw trajectories
and candidates private; the receipt omits their prompts, final answers,
authentication state, and candidate contents.
