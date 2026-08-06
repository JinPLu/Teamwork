# Cursor installed live protocol

Run only through `run-installed-cursor-teamwork-live-eval.py` with a prepared
declared release case. `cursor-agent` must resolve and report its version. The user
authenticates through Cursor's supported flow; the runner never copies credentials.
It installs into a disposable home and gives every case a fresh isolated scenario.

The record binds the case's requested authority. Read-only cases use Cursor's
read-only mode and all cases request its sandbox; neither the Agent templates
nor prompt text are treated as proof of enforcement. Model and effort are host
execution choices, not release-pass evidence. Missing binary or authentication,
unsupported custom-agent identity, privacy leakage, or missing retained
scenario/final-answer evidence is a typed `UNSUPPORTED` or `FAIL`. The local
gate does not score answer wording or length. Semantic acceptance requires an
independent Reviewer to read the answer and retained candidate.
