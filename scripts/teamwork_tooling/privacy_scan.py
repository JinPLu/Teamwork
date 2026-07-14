from __future__ import annotations

import argparse
import ipaddress
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


@dataclass(frozen=True, order=True)
class Finding:
    path: str
    line: int
    value_class: str


@dataclass(frozen=True)
class ValueAllowlist:
    value_class: str
    pattern: re.Pattern[str]
    rationale: str


VALUE_ALLOWLISTS = (
    ValueAllowlist(
        "contextual-codex-id",
        re.compile(
            r"^(?:11111111-1111-4111-8111-111111111111|"
            r"22222222-2222-4222-8222-222222222222)$"
        ),
        "These two deterministic UUIDs identify the synthetic session-audit fixture.",
    ),
    ValueAllowlist(
        "non-allowlisted-email",
        re.compile(r"^[^@\s]+@example\.invalid$", re.IGNORECASE),
        "example.invalid is the repository's reserved synthetic email domain.",
    ),
    ValueAllowlist(
        "private-or-link-local-ip",
        re.compile(r"^(?:192\.0\.2\.|198\.51\.100\.|203\.0\.113\.)\d+$"),
        "RFC 5737 documentation networks are explicitly synthetic fixtures.",
    ),
)

NAMED_HOME_RE = re.compile(
    r"(?<![A-Za-z0-9_}$])(?:/Users/[A-Za-z0-9._-]+|/home/[A-Za-z0-9._-]+|"
    r"[A-Za-z]:\\Users\\[A-Za-z0-9._-]+)"
)
UUID_RE = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)
PREFIXED_CODEX_ID_RE = re.compile(
    r"\b(?:call|thread|session|sess|turn)_[A-Za-z0-9_-]{12,}\b", re.IGNORECASE
)
EMAIL_RE = re.compile(r"\b[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
GITHUB_SSH_TRANSPORT_RE = re.compile(
    r"(?:^|[\s=:{(\[\"']|:-)(git@github\.com)(?=:)", re.IGNORECASE
)
LOCAL_DOMAIN_RE = re.compile(
    r"\b(?:[A-Za-z0-9-]+\.)+(?:local|internal|lan|localhost)\b", re.IGNORECASE
)
IP_RE = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")
TOKEN_RE = re.compile(
    r"\b(?:AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|"
    r"glpat-[A-Za-z0-9_-]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|npm_[A-Za-z0-9]{20,}|"
    r"pypi-[A-Za-z0-9_-]{20,}|hf_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,})\b"
)
PEM_RE = re.compile(r"-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----")


def _git_paths(root: Path, *args: str) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(root), *args, "-z"],
        check=True,
        stdout=subprocess.PIPE,
    )
    return [os.fsdecode(item) for item in result.stdout.split(b"\0") if item]


def _value_allowed(value: str, value_class: str) -> bool:
    return any(
        rule.value_class == value_class and rule.pattern.fullmatch(value)
        for rule in VALUE_ALLOWLISTS
    )


def _matches(line: str) -> Iterable[tuple[str, str]]:
    for match in NAMED_HOME_RE.finditer(line):
        yield "named-home-path", match.group(0)

    for match in UUID_RE.finditer(line):
        yield "contextual-codex-id", match.group(0)
    for match in PREFIXED_CODEX_ID_RE.finditer(line):
        yield "contextual-codex-id", match.group(0)

    email_line = list(line)
    for transport in GITHUB_SSH_TRANSPORT_RE.finditer(line):
        start, end = transport.span(1)
        email_line[start:end] = " " * (end - start)
    for match in EMAIL_RE.finditer("".join(email_line)):
        yield "non-allowlisted-email", match.group(0)
    for match in LOCAL_DOMAIN_RE.finditer(line):
        yield "local-domain", match.group(0)

    for match in IP_RE.finditer(line):
        value = match.group(0)
        try:
            address = ipaddress.ip_address(value)
        except ValueError:
            continue
        if address.is_private or address.is_link_local:
            yield "private-or-link-local-ip", value

    for match in TOKEN_RE.finditer(line):
        yield "token-prefix", match.group(0)
    for match in PEM_RE.finditer(line):
        yield "pem-private-key-header", match.group(0)


def scan_repository(root: Path) -> list[Finding]:
    root = root.resolve()
    findings: set[Finding] = set()

    for path in _git_paths(root, "ls-files"):
        tracked_path = root / path
        if tracked_path.is_symlink():
            data = os.fsencode(os.readlink(tracked_path))
        else:
            data = tracked_path.read_bytes()
        if b"\0" in data:
            continue
        text = data.decode("utf-8", errors="replace")
        for line_number, line in enumerate(text.splitlines(), start=1):
            for value_class, value in _matches(line):
                if _value_allowed(value, value_class):
                    continue
                findings.add(Finding(path, line_number, value_class))

    for path in _git_paths(root, "ls-files", "-ci", "--exclude-standard"):
        findings.add(Finding(path, 1, "force-added-ignored-runtime-artifact"))

    return sorted(findings)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scan tracked repository text for non-portable or private values."
    )
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args(argv)
    findings = scan_repository(Path(args.root))
    for finding in findings:
        print(f"{finding.path}:{finding.line}:{finding.value_class}")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
