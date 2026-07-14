from __future__ import annotations

import contextlib
import io
import subprocess
import tempfile
import unittest
from pathlib import Path

from teamwork_tooling.privacy_scan import Finding, main, scan_repository


class PrivacyScanTests(unittest.TestCase):
    def make_repo(self, files: dict[str, bytes | str]) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        for relative, content in files.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(content, bytes):
                path.write_bytes(content)
            else:
                path.write_text(content, encoding="utf-8")
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        return root

    def test_reports_sensitive_tracked_text_by_path_line_and_class(self) -> None:
        root = self.make_repo(
            {
                "notes.txt": (
                    "home=/Users/" + "alice/project\n"
                    "session_id=019f57bb-62a2-7912-" + "bad9-8971a9fd2d2d\n"
                    "mail=person@" + "corp.example\n"
                    "host=build.private." + "local\n"
                    "address=192.168." + "4.20\n"
                    "token=ghp_" + "abcdefghijklmnopqrstuvwxyz123456\n"
                    "-----BEGIN " + "PRIVATE KEY-----\n"
                )
            }
        )

        self.assertEqual(
            scan_repository(root),
            [
                Finding("notes.txt", 1, "named-home-path"),
                Finding("notes.txt", 2, "contextual-codex-id"),
                Finding("notes.txt", 3, "non-allowlisted-email"),
                Finding("notes.txt", 4, "local-domain"),
                Finding("notes.txt", 5, "private-or-link-local-ip"),
                Finding("notes.txt", 6, "token-prefix"),
                Finding("notes.txt", 7, "pem-private-key-header"),
            ],
        )

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = main([str(root)])
        self.assertEqual(status, 1)
        self.assertEqual(
            output.getvalue().splitlines(),
            [
                "notes.txt:1:named-home-path",
                "notes.txt:2:contextual-codex-id",
                "notes.txt:3:non-allowlisted-email",
                "notes.txt:4:local-domain",
                "notes.txt:5:private-or-link-local-ip",
                "notes.txt:6:token-prefix",
                "notes.txt:7:pem-private-key-header",
            ],
        )
        self.assertNotIn("alice", output.getvalue())
        self.assertNotIn("ghp_", output.getvalue())

    def test_allows_portable_public_and_explicitly_synthetic_values(self) -> None:
        root = self.make_repo(
            {
                "public.txt": (
                    "JinPLu https://github.com/JinPlu\n"
                    "git@github.com:JinPlu/Teamwork.git\n"
                    "origin=git@github.com:OpenAI/example.git\n"
                    "remote=${REMOTE:-git@github.com:OpenAI/example.git}\n"
                    "model=gpt-5.6-sol api=responses.create\n"
                    "mail=fixture@example.invalid\n"
                    "root=/tmp/teamwork and /Users/<user>/Teamwork\n"
                    "documentation=203.0.113.10\n"
                ),
                "fixture.txt": 'audit_root_id="11111111-1111-4111-8111-111111111111"\n',
            }
        )
        self.assertEqual(scan_repository(root), [])

    def test_rejects_github_lookalike_and_bare_uuid(self) -> None:
        root = self.make_repo(
            {
                "bypass.txt": (
                    "owner@" + "github.com:\n"
                    "notgit@" + "github.com:private\n"
                    "origin=notgit@" + "github.com:private\n"
                    "git@" + "github.com-private:repo\n"
                    "git@" + "github.com/owner/repo.git\n"
                    "@git@" + "github.com:repo\n"
                    '"id": "019f57bb-62a2-7912-' + 'bad9-8971a9fd2d2d"\n'
                )
            }
        )
        self.assertEqual(
            scan_repository(root),
            [
                Finding("bypass.txt", 1, "non-allowlisted-email"),
                Finding("bypass.txt", 2, "non-allowlisted-email"),
                Finding("bypass.txt", 3, "non-allowlisted-email"),
                Finding("bypass.txt", 4, "non-allowlisted-email"),
                Finding("bypass.txt", 5, "non-allowlisted-email"),
                Finding("bypass.txt", 6, "non-allowlisted-email"),
                Finding("bypass.txt", 7, "contextual-codex-id"),
            ],
        )

    def test_skips_binary_files_even_when_bytes_resemble_secrets(self) -> None:
        root = self.make_repo(
            {"asset.bin": b"\x00/Users/alice\nghp_abcdefghijklmnopqrstuvwxyz123456"}
        )
        self.assertEqual(scan_repository(root), [])

    def test_reports_force_added_ignored_tracked_paths(self) -> None:
        root = self.make_repo({".gitignore": "docs/teamwork/reports/\n"})
        artifact = root / "docs/teamwork/reports/private.json"
        artifact.parent.mkdir(parents=True)
        artifact.write_text("{}\n", encoding="utf-8")
        subprocess.run(
            ["git", "-C", str(root), "add", "-f", artifact.relative_to(root)],
            check=True,
        )

        self.assertEqual(
            scan_repository(root),
            [
                Finding(
                    "docs/teamwork/reports/private.json",
                    1,
                    "force-added-ignored-runtime-artifact",
                )
            ],
        )


if __name__ == "__main__":
    unittest.main()
