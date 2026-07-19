# Claude Code installed-v4 live protocol

Run only through `run-installed-claude-teamwork-live-eval.py` with a prepared
candidate manifest. `claude` must resolve and report its version. The user uses the
supported authentication flow; the runner never copies credentials. It installs
into a disposable home and gives every case a fresh isolated scenario.

Capture `SubagentStart`/`SubagentStop` identity and transcript evidence when the
host exposes it. Missing binary/authentication, unavailable hook or transcript
evidence, unobservable actual model/effort/tool authority, privacy leakage, or no
changed scenario artifact/non-agent trace is `UNSUPPORTED` or `FAIL`, never a
prompt-derived pass.
