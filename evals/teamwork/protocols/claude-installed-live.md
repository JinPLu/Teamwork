# Claude Code installed live protocol

Run only through `run-installed-claude-teamwork-live-eval.py` with a prepared
declared release case. `claude` must resolve and report its version. The user uses the
supported authentication flow; the runner never copies credentials. It installs
into a disposable home and gives every case a fresh isolated scenario.

Capture `SubagentStart`/`SubagentStop` identity and transcript evidence when the
host exposes it. The record binds the case's requested authority and Claude
receives it through its permission mode. Model and effort are host execution
choices, not release-pass evidence. Missing binary/authentication, unavailable
hook or transcript evidence, privacy leakage, or missing retained scenario or
final-answer evidence is `UNSUPPORTED` or `FAIL`, never a prompt-derived pass.
The local gate does not score wording or length; semantic acceptance requires
an independent Reviewer to read the answer and retained candidate.
