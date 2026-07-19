# Cursor installed-v4 live protocol

Run only through `run-installed-cursor-teamwork-live-eval.py` with a prepared
candidate manifest. `cursor-agent` must resolve and report its version. The user
authenticates through Cursor's supported flow; the runner never copies credentials.
It installs into a disposable home and gives every case a fresh isolated scenario.

Missing binary or authentication, unsupported custom-agent identity, unobservable
actual model/effort/tool/authority, privacy leakage, or a missing changed scenario
artifact/non-agent tool trace is a typed `UNSUPPORTED` or `FAIL`. It blocks that
slice and is never inferred from template or prompt text.
