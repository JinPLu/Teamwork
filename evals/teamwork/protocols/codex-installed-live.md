# Codex installed live protocol

Run only through `run-installed-codex-teamwork-live-eval.py` with a prepared
declared release case and explicit parent model and effort as invocation
configuration. `codex` must resolve to an absolute executable path and report
its version; both are retained on every trajectory. The runner uses
supported isolated authentication, installs into a disposable home, and gives
every case a fresh scenario.

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
