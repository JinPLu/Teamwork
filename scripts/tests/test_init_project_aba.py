import os
import selectors
import subprocess
import tempfile
import threading
import time
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INIT = ROOT / "scripts/init-project.sh"
TEMPLATE = ROOT / "skills/using-teamwork/references/teamwork-index-template.json"
READY = "TEAMWORK_TEST_CODEGRAPH_READY"
DEADLINE_SECONDS = 10.0


class InitProjectAbaRegressionTests(unittest.TestCase):
    def make_fake_codegraph(self, base: Path) -> Path:
        bin_dir = base / "bin"
        bin_dir.mkdir()
        codegraph = bin_dir / "codegraph"
        codegraph.write_text(
            f"""#!/bin/sh
printf '%s\\n' '{READY}'
IFS= read -r command
if [ "$command" != GO ]; then
  printf '%s\\n' "expected GO, got: $command" >&2
  exit 97
fi
exit 0
""",
            encoding="utf-8",
        )
        codegraph.chmod(0o755)
        return bin_dir

    def start_init(self, project: Path, home: Path, bin_dir: Path) -> subprocess.Popen[str]:
        env = os.environ.copy()
        env.update(
            {
                "HOME": str(home),
                "PATH": f"{bin_dir}{os.pathsep}{env['PATH']}",
                "TEAMWORK_INIT_CODEGRAPH": "1",
                "TEAMWORK_INIT_CURSOR_POLICY_COPY": "0",
            }
        )
        return subprocess.Popen(
            [
                str(INIT),
                "--copy",
                "--no-cursor-policy-copy",
                "--project-root",
                str(project),
            ],
            cwd=ROOT,
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

    def wait_for_ready(self, process: subprocess.Popen[str], deadline: float) -> str:
        assert process.stdout is not None
        lines: list[str] = []
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    self.fail(
                        f"init did not reach fake codegraph within {DEADLINE_SECONDS:g}s; "
                        f"output so far:\n{''.join(lines)}"
                    )
                events = selector.select(remaining)
                if not events:
                    continue
                line = process.stdout.readline()
                if line:
                    lines.append(line)
                    if line.rstrip("\r\n") == READY:
                        return "".join(lines)
                    continue
                returncode = process.poll()
                if returncode is not None:
                    self.fail(
                        f"init exited with {returncode} before fake codegraph READY; "
                        f"output:\n{''.join(lines)}"
                    )

    def send_go(self, process: subprocess.Popen[str]) -> None:
        assert process.stdin is not None
        process.stdin.write("GO\n")
        process.stdin.flush()

    def finish(
        self,
        process: subprocess.Popen[str],
        deadline: float,
        prefix: str,
    ) -> tuple[int, str]:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            self.fail(f"init exceeded the {DEADLINE_SECONDS:g}s test deadline")
        try:
            tail, _ = process.communicate(timeout=remaining)
        except subprocess.TimeoutExpired:
            process.kill()
            tail, _ = process.communicate()
            self.fail(
                f"init exceeded the {DEADLINE_SECONDS:g}s test deadline; "
                f"output:\n{prefix}{tail}"
            )
        return process.returncode, prefix + tail

    def stop_process(self, process: subprocess.Popen[str]) -> None:
        if process.poll() is None:
            process.kill()
            process.communicate()

    def filesystem_state(self, root: Path) -> dict[str, tuple[object, ...]]:
        state: dict[str, tuple[object, ...]] = {}
        for path in sorted((root, *root.rglob("*")), key=lambda item: str(item)):
            relative = "." if path == root else path.relative_to(root).as_posix()
            mode = path.lstat().st_mode
            if path.is_symlink():
                state[relative] = ("symlink", mode, os.readlink(path))
            elif path.is_file():
                state[relative] = ("file", mode, path.read_bytes())
            elif path.is_dir():
                state[relative] = ("directory", mode)
            else:
                state[relative] = ("other", mode)
        return state

    def test_existing_teamwork_directory_aba_does_not_redirect_runtime_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            project = base / "project"
            docs = project / "docs"
            memory = docs / "teamwork"
            original = docs / "teamwork-original"
            transient_saved = docs / "teamwork-transient"
            home = base / "home"
            memory.mkdir(parents=True)
            home.mkdir()
            (memory / "index.json").write_bytes(TEMPLATE.read_bytes())
            (memory / "current.md").write_bytes(
                b"# Existing current\n\n- Active discussion: none.\n"
            )
            (memory / "README.md").write_bytes(
                b"# Existing runtime README\n\n- Active discussion route: none\n"
            )
            (memory / "retained-sentinel.txt").write_bytes(b"retained directory\n")

            runtime_names = ("index.json", "current.md", "README.md")
            runtime_before = {
                name: (
                    (memory / name).read_bytes(),
                    (memory / name).stat().st_dev,
                    (memory / name).stat().st_ino,
                )
                for name in runtime_names
            }
            memory_identity = (memory.stat().st_dev, memory.stat().st_ino)
            bin_dir = self.make_fake_codegraph(base)
            process = self.start_init(project, home, bin_dir)
            deadline = time.monotonic() + DEADLINE_SECONDS
            stop_observer = threading.Event()
            observer_result: list[str] = []
            observer_error: list[BaseException] = []
            observer: threading.Thread | None = None

            try:
                prefix = self.wait_for_ready(process, deadline)
                memory.rename(original)
                memory.mkdir()

                def observe_and_restore() -> None:
                    try:
                        while time.monotonic() < deadline:
                            if (memory / "index.json").exists():
                                observer_result.append("redirected")
                                break
                            if (project / "AGENTS.md").exists():
                                observer_result.append("retained")
                                break
                            returncode = process.poll()
                            if returncode is not None:
                                raise AssertionError(
                                    f"init exited with {returncode} before a deterministic restore signal"
                                )
                            if stop_observer.wait(0.01):
                                return
                        else:
                            raise AssertionError("no restore signal before the 10s deadline")
                        memory.rename(transient_saved)
                        original.rename(memory)
                    except BaseException as exc:
                        observer_error.append(exc)

                observer = threading.Thread(target=observe_and_restore, daemon=True)
                observer.start()
                self.send_go(process)
                returncode, output = self.finish(process, deadline, prefix)
                observer.join(max(0.0, deadline - time.monotonic()))

                self.assertFalse(observer.is_alive(), "restore observer did not terminate")
                self.assertFalse(observer_error, observer_error[0] if observer_error else None)
                self.assertEqual(returncode, 0, output)
                self.assertEqual(observer_result, ["retained"], output)
                self.assertEqual((memory.stat().st_dev, memory.stat().st_ino), memory_identity)
                self.assertEqual(
                    (memory / "retained-sentinel.txt").read_bytes(),
                    b"retained directory\n",
                )
                for name, (expected_bytes, expected_device, expected_inode) in runtime_before.items():
                    path = memory / name
                    self.assertEqual(path.read_bytes(), expected_bytes, name)
                    self.assertEqual((path.stat().st_dev, path.stat().st_ino), (expected_device, expected_inode))
                    self.assertFalse((transient_saved / name).exists(), name)
                self.assertTrue((project / "AGENTS.md").is_file())
            finally:
                stop_observer.set()
                self.stop_process(process)
                if observer is not None:
                    observer.join(1.0)
                if original.exists() and memory.exists() and not transient_saved.exists():
                    memory.rename(transient_saved)
                    original.rename(memory)

    def test_marker_created_at_codegraph_pause_blocks_all_later_project_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            project = base / "project"
            home = base / "home"
            project.mkdir()
            home.mkdir()
            bin_dir = self.make_fake_codegraph(base)
            process = self.start_init(project, home, bin_dir)
            deadline = time.monotonic() + DEADLINE_SECONDS

            try:
                prefix = self.wait_for_ready(process, deadline)
                memory = project / "docs/teamwork"
                memory.mkdir(parents=True, exist_ok=True)
                for path in (
                    memory / "index.json",
                    memory / "current.md",
                    memory / "README.md",
                    project / "AGENTS.md",
                    project / ".gitignore",
                ):
                    self.assertFalse(path.exists(), f"unexpected pre-marker write: {path}")
                home_at_marker = self.filesystem_state(home)
                marker = memory / ".discussion-transaction.json"
                marker.write_text(
                    '{"operation":"update","phase":"commit"}\n',
                    encoding="utf-8",
                )

                self.send_go(process)
                returncode, output = self.finish(process, deadline, prefix)

                self.assertNotEqual(returncode, 0, output)
                self.assertIn("unfinished discussion transaction marker", output)
                self.assertEqual(self.filesystem_state(home), home_at_marker)
                self.assertEqual(
                    marker.read_bytes(),
                    b'{"operation":"update","phase":"commit"}\n',
                )
                for path in (
                    memory / "index.json",
                    memory / "current.md",
                    memory / "README.md",
                    project / "AGENTS.md",
                    project / ".gitignore",
                ):
                    self.assertFalse(path.exists(), f"write occurred after marker: {path}")
            finally:
                self.stop_process(process)


if __name__ == "__main__":
    unittest.main()
