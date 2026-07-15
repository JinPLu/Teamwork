#!/usr/bin/env python3
import json
import os
import re
import stat
import sys
from datetime import date
from pathlib import Path, PurePosixPath


DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
KINDS = {"result", "progress", "design", "decision", "discussion", "plan", "report", "research", "runbook"}
STATUSES = {"active", "historical", "superseded", "blocked", "candidate", "accepted"}
CURRENTNESS = {"current", "stale", "historical", "candidate"}
AUTHORITIES = {"canonical", "active-summary", "supporting", "candidate", "historical", "superseded"}
ACTIVE_STATUSES = {"active", "accepted"}
ACTIVE_AUTHORITIES = {"canonical", "active-summary", "supporting"}
ACTIVE_POINTER_KEYS = ("current", "design", "plan", "progress", "goal", "report", "discussion")
CANONICAL_CURRENT_PATH = "docs/teamwork/current.md"
DISCUSSION_TRANSACTION_MARKER = ".discussion-transaction.json"
INIT_TRANSACTION_MARKER = ".teamwork-init-transaction.json"

DISCUSSION_ARTIFACT_TYPE = "discussion"
DISCUSSION_ARTIFACT_STATUSES = {"active", "accepted", "superseded"}
DISCUSSION_ENTRY_STATUSES = DISCUSSION_ARTIFACT_STATUSES
DISCUSSION_REQUIRED_HEADERS = (
    "Artifact Type",
    "Status",
    "Authority",
    "Last Updated",
    "Search Keys",
    "Abstract",
    "Linked Artifacts",
    "Superseded By",
)
DISCUSSION_REQUIRED_SECTIONS = (
    "Goal",
    "Settled",
    "Still open",
    "Key evidence",
    "Continue here",
)
DISCUSSION_PATH_RE = re.compile(
    r"^docs/teamwork/discussion/(\d{4}-\d{2}-\d{2})-([a-z0-9]+(?:-[a-z0-9]+)*)\.md$"
)
DISCUSSION_CURRENT_LINE_RE = re.compile(r"^- Active discussion:\s*(\S(?:.*\S)?)\s*$")
DISCUSSION_README_LINE_RE = re.compile(r"^- Active discussion route:\s*(\S(?:.*\S)?)\s*$")


class ValidationError(Exception):
    pass


def fail(msg: str) -> None:
    raise ValidationError(msg)


def require(cond: bool, msg: str) -> None:
    if not cond:
        fail(msg)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"missing file: {path}")


def _secure_open_flags(*, directory: bool) -> int:
    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory_flag = getattr(os, "O_DIRECTORY", None)
    if nofollow is None or (directory and directory_flag is None):
        fail("platform cannot safely open project files without following symlinks")
    flags = os.O_RDONLY | nofollow | getattr(os, "O_CLOEXEC", 0)
    if directory:
        assert directory_flag is not None
        flags |= directory_flag
    else:
        flags |= getattr(os, "O_NONBLOCK", 0)
    return flags


def _same_identity(opened: os.stat_result, expected: os.stat_result, *, directory: bool) -> bool:
    expected_type = stat.S_ISDIR if directory else stat.S_ISREG
    return (
        opened.st_dev == expected.st_dev
        and opened.st_ino == expected.st_ino
        and expected_type(expected.st_mode)
        and expected_type(opened.st_mode)
    )


def _open_absolute_directory(path: Path, label: str) -> int:
    """Open the project boundary itself without following a final symlink."""

    require(path.is_absolute(), f"{label} must be an absolute directory")
    flags = _secure_open_flags(directory=True)
    try:
        expected = os.lstat(path)
        if stat.S_ISLNK(expected.st_mode) or not stat.S_ISDIR(expected.st_mode):
            fail(f"{label} must be a non-symlink directory: {path}")
        current_fd = os.open(path, flags)
    except OSError as exc:
        fail(f"{label} must be a non-symlink directory: {path}: {exc}")
    opened = os.fstat(current_fd)
    if not _same_identity(opened, expected, directory=True):
        os.close(current_fd)
        fail(f"{label} changed identity while being opened: {path}")
    return current_fd


class SafeProjectReader:
    """Read canonical project files through retained, no-follow directory fds."""

    def __init__(self, project_root: Path):
        self.project_root = Path(os.path.abspath(os.fspath(project_root)))
        self.root_fd = _open_absolute_directory(self.project_root, "index input project root")
        self.root_stat = os.fstat(self.root_fd)
        self.docs_fd = -1
        self.memory_fd = -1
        try:
            self.docs_fd, self.docs_stat = self._open_child_directory(
                self.root_fd,
                "docs",
                "canonical docs directory",
            )
            self.memory_fd, self.memory_stat = self._open_child_directory(
                self.docs_fd,
                "teamwork",
                "canonical docs/teamwork directory",
            )
        except BaseException:
            self.close()
            raise

    def close(self) -> None:
        if self.memory_fd >= 0:
            os.close(self.memory_fd)
            self.memory_fd = -1
        if self.docs_fd >= 0:
            os.close(self.docs_fd)
            self.docs_fd = -1
        if self.root_fd >= 0:
            os.close(self.root_fd)
            self.root_fd = -1

    def _open_child_directory(
        self,
        parent_fd: int,
        name: str,
        label: str,
    ) -> tuple[int, os.stat_result]:
        flags = _secure_open_flags(directory=True)
        try:
            expected = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
            if stat.S_ISLNK(expected.st_mode) or not stat.S_ISDIR(expected.st_mode):
                fail(f"{label} must be a non-symlink directory")
            if expected.st_dev != self.root_stat.st_dev:
                fail(f"{label} crosses the project-root device")
            opened_fd = os.open(name, flags, dir_fd=parent_fd)
        except OSError as exc:
            fail(f"cannot safely open {label}: {exc}")
        opened = os.fstat(opened_fd)
        if (
            not _same_identity(opened, expected, directory=True)
            or opened.st_dev != self.root_stat.st_dev
        ):
            os.close(opened_fd)
            fail(f"{label} changed identity or device while being opened")
        return opened_fd, opened

    def _verify_namespace_identity(self) -> None:
        try:
            current_root = os.fstat(self.root_fd)
            current_docs = os.stat("docs", dir_fd=self.root_fd, follow_symlinks=False)
            current_memory = os.stat(
                "teamwork",
                dir_fd=self.docs_fd,
                follow_symlinks=False,
            )
        except OSError as exc:
            fail(f"canonical docs/teamwork namespace changed while reading: {exc}")
        require(
            _same_identity(current_root, self.root_stat, directory=True)
            and _same_identity(current_docs, self.docs_stat, directory=True)
            and _same_identity(current_memory, self.memory_stat, directory=True),
            "canonical docs/teamwork namespace changed identity while reading",
        )

    def require_no_pending_discussion_transaction(self) -> None:
        """Reject any transaction marker observed in the retained memory directory."""

        self._verify_namespace_identity()
        for marker in (DISCUSSION_TRANSACTION_MARKER, INIT_TRANSACTION_MARKER):
            try:
                os.stat(marker, dir_fd=self.memory_fd, follow_symlinks=False)
            except FileNotFoundError:
                continue
            except OSError as exc:
                fail(f"cannot determine Teamwork transaction state safely: {exc}")
            if marker == DISCUSSION_TRANSACTION_MARKER:
                fail(
                    "pending or indeterminate discussion transaction marker exists: "
                    f"docs/teamwork/{marker}"
                )
            fail(
                "pending or indeterminate Teamwork init transaction marker exists: "
                f"docs/teamwork/{marker}"
            )
        self._verify_namespace_identity()

    def read_text(
        self,
        relative_path: PurePosixPath,
        label: str,
        *,
        require_single_link: bool = True,
    ) -> str:
        require(
            not relative_path.is_absolute()
            and len(relative_path.parts) > 2
            and relative_path.parts[:2] == ("docs", "teamwork")
            and relative_path.as_posix() not in {"", "."}
            and "." not in relative_path.parts
            and ".." not in relative_path.parts,
            f"{label} path must remain lexically inside canonical docs/teamwork",
        )
        self._verify_namespace_identity()
        canonical_parts = relative_path.parts[2:]
        directory_flags = _secure_open_flags(directory=True)
        file_flags = _secure_open_flags(directory=False)
        directory_chain: list[tuple[int, str, int, os.stat_result]] = []
        file_fd = -1
        try:
            parent_fd = os.dup(self.memory_fd)
            for part in canonical_parts[:-1]:
                try:
                    expected = os.stat(part, dir_fd=parent_fd, follow_symlinks=False)
                    if stat.S_ISLNK(expected.st_mode) or not stat.S_ISDIR(expected.st_mode):
                        fail(
                            f"{label} must be a regular project file: "
                            f"{relative_path.as_posix()}"
                        )
                    if expected.st_dev != self.root_stat.st_dev:
                        fail(
                            f"{label} crosses the project-root device: "
                            f"{relative_path.as_posix()}"
                        )
                    child_fd = os.open(part, directory_flags, dir_fd=parent_fd)
                except OSError as exc:
                    fail(f"{label} must be a regular project file: {relative_path.as_posix()}: {exc}")
                opened = os.fstat(child_fd)
                if (
                    not _same_identity(opened, expected, directory=True)
                    or opened.st_dev != self.root_stat.st_dev
                ):
                    os.close(child_fd)
                    fail(f"{label} changed identity or device while being opened: {relative_path.as_posix()}")
                directory_chain.append((parent_fd, part, child_fd, opened))
                parent_fd = child_fd

            name = canonical_parts[-1]
            try:
                expected_file = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
                if stat.S_ISLNK(expected_file.st_mode) or not stat.S_ISREG(expected_file.st_mode):
                    fail(f"{label} must be a regular project file: {relative_path.as_posix()}")
                if expected_file.st_dev != self.root_stat.st_dev:
                    fail(f"{label} crosses the project-root device: {relative_path.as_posix()}")
                if require_single_link and expected_file.st_nlink != 1:
                    fail(f"{label} must have exactly one hard link: {relative_path.as_posix()}")
                file_fd = os.open(name, file_flags, dir_fd=parent_fd)
            except OSError as exc:
                fail(f"{label} must be a regular project file: {relative_path.as_posix()}: {exc}")
            opened_file = os.fstat(file_fd)
            if (
                not _same_identity(opened_file, expected_file, directory=False)
                or opened_file.st_dev != self.root_stat.st_dev
            ):
                fail(f"{label} changed identity or device while being opened: {relative_path.as_posix()}")
            if require_single_link and (expected_file.st_nlink != 1 or opened_file.st_nlink != 1):
                fail(f"{label} must have exactly one hard link: {relative_path.as_posix()}")

            chunks: list[bytes] = []
            while chunk := os.read(file_fd, 1024 * 1024):
                chunks.append(chunk)

            final_file = os.fstat(file_fd)
            try:
                current_file = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
            except OSError as exc:
                fail(f"{label} changed while being read: {relative_path.as_posix()}: {exc}")
            if (
                not _same_identity(final_file, opened_file, directory=False)
                or not _same_identity(current_file, opened_file, directory=False)
                or (require_single_link and final_file.st_nlink != 1)
            ):
                fail(f"{label} changed identity while being read: {relative_path.as_posix()}")

            for ancestor_fd, part, child_fd, opened in directory_chain:
                try:
                    current = os.stat(part, dir_fd=ancestor_fd, follow_symlinks=False)
                except OSError as exc:
                    fail(f"{label} ancestor changed while being read: {relative_path.as_posix()}: {exc}")
                if not _same_identity(current, opened, directory=True):
                    fail(f"{label} ancestor changed identity while being read: {relative_path.as_posix()}")
            self._verify_namespace_identity()
            try:
                return b"".join(chunks).decode("utf-8")
            except UnicodeDecodeError as exc:
                fail(f"{label} must be valid UTF-8: {relative_path.as_posix()}: {exc}")
        except OSError as exc:
            fail(f"cannot safely read {label}: {relative_path.as_posix()}: {exc}")
        finally:
            if file_fd >= 0:
                os.close(file_fd)
            if directory_chain:
                for ancestor_fd, _part, _child_fd, _opened in directory_chain:
                    os.close(ancestor_fd)
                os.close(directory_chain[-1][2])
            elif "parent_fd" in locals():
                os.close(parent_fd)


def line_count(text: str) -> int:
    return len(text.splitlines())


def word_count(text: str) -> int:
    return len(text.split())


def is_valid_iso_date(value: object) -> bool:
    if not isinstance(value, str) or DATE_RE.fullmatch(value) is None:
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def is_placeholder(value: str) -> bool:
    return not value.strip() or (value.strip().startswith("<") and value.strip().endswith(">"))


def discussion_headers(text: str) -> dict[str, list[str]]:
    """Return the metadata header before the document title.

    Discussion artifacts use a deliberately small, line-oriented header so the
    lifecycle validator can check a real saved artifact without treating the
    rest of the document as a machine-owned schema.
    """

    headers: dict[str, list[str]] = {}
    for line in text.splitlines():
        if line.startswith("#"):
            break
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        headers.setdefault(key.strip(), []).append(value.strip())
    return headers


def discussion_section(text: str, heading: str, *, required: bool = True) -> str | None:
    pattern = re.compile(
        rf"^## {re.escape(heading)}\s*$\n(?P<body>.*?)(?=^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    matches = list(pattern.finditer(text))
    if not matches:
        if required:
            fail(f"discussion artifact missing section: {heading}")
        return None
    require(
        len(matches) == 1,
        (
            f"discussion artifact section must appear exactly once: {heading}"
            if required
            else f"discussion artifact section must appear at most once: {heading}"
        ),
    )
    return matches[0].group("body").strip()


def is_none_section(value: str) -> bool:
    normalized = value.strip().lower()
    normalized = re.sub(r"^[\s>*+-]+", "", normalized)
    normalized = normalized.strip("`*_ .")
    return normalized in {"none", "n/a", "not applicable", "nothing"}


def validate_discussion_artifact_text(
    text: str,
    *,
    expected_status: str | None = None,
    expected_updated: str | None = None,
) -> None:
    """Validate the durable, human-readable shape of one discussion artifact.

    This intentionally checks recovery anchors rather than trying to judge the
    decision itself. Semantic quality remains a model-review concern; this
    validator proves that a saved artifact has deterministic recovery anchors
    and index linkage. Only a live continuation can demonstrate model recovery.
    """

    header_values = discussion_headers(text)
    headers: dict[str, str] = {}
    for key in DISCUSSION_REQUIRED_HEADERS:
        values = header_values.get(key, [])
        require(values, f"discussion artifact missing header: {key}")
        require(
            len(values) == 1,
            f"discussion artifact header must appear exactly once: {key}",
        )
        value = values[0]
        require(not is_placeholder(value), f"discussion artifact header is empty or placeholder: {key}")
        headers[key] = value

    require(
        headers["Artifact Type"] == DISCUSSION_ARTIFACT_TYPE,
        "discussion artifact Artifact Type must be discussion",
    )
    require(headers["Authority"] == "supporting", "discussion artifact Authority must be supporting")
    require(
        headers["Status"] in DISCUSSION_ARTIFACT_STATUSES,
        f"discussion artifact Status has unknown value: {headers['Status']}",
    )
    require(
        is_valid_iso_date(headers["Last Updated"]),
        "discussion artifact Last Updated must be a valid YYYY-MM-DD date",
    )
    superseded_by = headers["Superseded By"]
    if headers["Status"] == "active":
        require(
            is_none_section(superseded_by),
            "active discussion artifact Superseded By must be none",
        )
    if headers["Status"] == "superseded":
        require(
            not is_none_section(superseded_by),
            "superseded discussion artifact must name a successor or reason in Superseded By",
        )
    if expected_status is not None:
        require(
            headers["Status"] == expected_status,
            "discussion artifact Status must match its index entry",
        )
    if expected_updated is not None:
        require(
            headers["Last Updated"] == expected_updated,
            "discussion artifact Last Updated must match its index entry",
        )

    titles = re.findall(r"^# (?!#)(.+?)\s*$", text, re.MULTILINE)
    require(len(titles) == 1, "discussion artifact must have exactly one H1 title")
    title = titles[0].strip()
    require(not is_placeholder(title), "discussion artifact H1 title must be concrete")
    require(
        title.casefold() != "teamwork discussion",
        "discussion artifact H1 title must be specific, not Teamwork Discussion",
    )
    sections: dict[str, str] = {}
    for heading in DISCUSSION_REQUIRED_SECTIONS:
        section = discussion_section(text, heading)
        require(section is not None and not is_placeholder(section), f"discussion artifact section is empty or placeholder: {heading}")
        sections[heading] = section

    still_open = sections["Still open"]
    if headers["Status"] == "active":
        require(
            still_open is not None and not is_none_section(still_open),
            "active discussion artifact Still open must name an unresolved item",
        )
    else:
        require(
            still_open is not None and is_none_section(still_open),
            "closed discussion artifact Still open must explicitly be none",
        )

    decision_map = discussion_section(text, "Decision map", required=False)
    if decision_map is None:
        return
    mermaid = re.search(r"```mermaid\s*\n(?P<diagram>.*?)```", decision_map, re.DOTALL)
    require(mermaid is not None, "discussion artifact Decision map must contain Mermaid")
    diagram = mermaid.group("diagram")
    require(
        re.search(r"^\s*flowchart(?:\s+(?:TB|TD|BT|RL|LR))?\s*$", diagram, re.MULTILINE)
        is not None,
        "discussion artifact Decision map must be a flowchart",
    )
    require(
        re.search(r"^\s*[A-Za-z_][A-Za-z0-9_-]*\s*(?:\[|\(|\{)", diagram, re.MULTILINE)
        is not None,
        "discussion artifact Decision map must include a node",
    )


def normalized_discussion_anchor(value: str) -> str:
    value = value.strip()
    # A prose line may terminate a Markdown-formatted path with a sentence
    # period: `docs/.../discussion.md`. Remove that sentence punctuation before
    # unwrapping the inline-code delimiter so the initialized templates and
    # ordinary Markdown prose mean the same thing to the lifecycle check.
    if value.startswith("`") and value.endswith("`."):
        value = value[:-1]
    if value.startswith("`") and value.endswith("`"):
        value = value[1:-1].strip()
    # The initialized current digest uses "none." as a sentence, while a
    # discussion path naturally ends in .md. Trim only a final sentence period.
    if value == "none.":
        value = "none"
    elif value.endswith(".md."):
        value = value[:-1]
    return value


def runtime_discussion_anchor(
    text: str,
    display_path: str,
    pattern: re.Pattern[str],
    label: str,
) -> str:
    matches = [match.group(1) for line in text.splitlines() if (match := pattern.match(line))]
    require(len(matches) == 1, f"{display_path} must contain exactly one {label} anchor")
    value = normalized_discussion_anchor(matches[0])
    require(value == "none" or value, f"{display_path} {label} anchor must be a path or none")
    return value


def validate_entry(entry: dict, idx: int) -> None:
    required = [
        "topic",
        "kind",
        "title",
        "status",
        "currentness",
        "authority",
        "path",
        "updated",
        "summary",
    ]
    for key in required:
        require(key in entry, f"entries[{idx}] missing required key: {key}")
    require(isinstance(entry["topic"], str) and entry["topic"], f"entries[{idx}].topic must be non-empty string")
    require(isinstance(entry["kind"], str) and entry["kind"], f"entries[{idx}].kind must be non-empty string")
    require(isinstance(entry["status"], str) and entry["status"], f"entries[{idx}].status must be non-empty string")
    require(entry["kind"] in KINDS, f"entries[{idx}].kind has unknown value: {entry['kind']}")
    require(entry["status"] in STATUSES, f"entries[{idx}].status has unknown value: {entry['status']}")
    require(entry["currentness"] in CURRENTNESS, f"entries[{idx}].currentness has unknown value: {entry['currentness']}")
    require(entry["authority"] in AUTHORITIES, f"entries[{idx}].authority has unknown value: {entry['authority']}")
    for key in ["title", "path", "summary"]:
        require(isinstance(entry[key], str) and entry[key], f"entries[{idx}].{key} must be non-empty string")
    require(
        is_valid_iso_date(entry["updated"]),
        f"entries[{idx}].updated must be a valid YYYY-MM-DD date",
    )


def real_project_root(index_path: Path) -> Path | None:
    if (
        index_path.name == "index.json"
        and index_path.parent.name == "teamwork"
        and index_path.parent.parent.name == "docs"
    ):
        return index_path.parent.parent.parent
    return None


def checked_index_input(argument: str) -> Path:
    """Normalize the CLI spelling and lock the canonical project-index shape."""

    index_path = Path(os.path.abspath(argument))
    project_root = real_project_root(index_path)
    if project_root is not None:
        require(
            index_path == project_root / "docs/teamwork/index.json"
            and index_path.is_absolute(),
            "index input must remain lexically inside its project root",
        )
    return index_path


def read_standalone_index(path: Path) -> str:
    """Read a non-project template from the exact regular file that was checked."""

    try:
        expected = os.lstat(path)
    except OSError as exc:
        fail(f"cannot inspect index input: {path}: {exc}")
    require(
        stat.S_ISREG(expected.st_mode) and not stat.S_ISLNK(expected.st_mode),
        f"index input must be a regular file: {path}",
    )
    flags = _secure_open_flags(directory=False)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        fail(f"cannot open index input without following links: {path}: {exc}")
    try:
        opened = os.fstat(fd)
        require(
            _same_identity(opened, expected, directory=False),
            f"index input changed identity while being opened: {path}",
        )
        chunks: list[bytes] = []
        while chunk := os.read(fd, 1024 * 1024):
            chunks.append(chunk)
        final = os.fstat(fd)
        require(
            _same_identity(final, opened, directory=False),
            f"index input changed identity while being read: {path}",
        )
        try:
            return b"".join(chunks).decode("utf-8")
        except UnicodeDecodeError as exc:
            fail(f"index input must be valid UTF-8: {path}: {exc}")
    finally:
        os.close(fd)


def validate_active_pointers(active: dict, entries: list[dict]) -> None:
    entries_by_path: dict[str, list[dict]] = {}
    for entry in entries:
        entries_by_path.setdefault(entry["path"], []).append(entry)

    pointers: list[tuple[str, str]] = []
    for key in ACTIVE_POINTER_KEYS:
        value = active.get(key)
        if value is not None:
            pointers.append((f"active.{key}", value))

    results = active.get("results", [])
    seen_results: set[str] = set()
    for idx, value in enumerate(results):
        require(isinstance(value, str) and value, f"active.results[{idx}] must be non-empty string")
        require(value not in seen_results, f"active.results contains duplicate path: {value}")
        seen_results.add(value)
        pointers.append((f"active.results[{idx}]", value))

    for label, path in pointers:
        matches = entries_by_path.get(path, [])
        require(matches, f"{label} has no matching entries.path: {path}")
        eligible = [
            entry
            for entry in matches
            if entry["status"] in ACTIVE_STATUSES
            and entry["currentness"] == "current"
            and entry["authority"] in ACTIVE_AUTHORITIES
        ]
        require(
            eligible,
            f"{label} must resolve to a current accepted/active entry with non-candidate authority: {path}",
        )

        if label == "active.discussion":
            validate_discussion_path(path, "active.discussion")
            require(
                any(entry["kind"] == "discussion" for entry in eligible),
                "active.discussion must resolve to an entry with kind discussion",
            )
            require(
                any(entry["authority"] == "supporting" for entry in eligible if entry["kind"] == "discussion"),
                "active.discussion must resolve to a discussion entry with supporting authority",
            )


def validate_discussion_path(path: str, label: str) -> PurePosixPath:
    discussion_path = PurePosixPath(path)
    require(
        not discussion_path.is_absolute()
        and discussion_path.as_posix() == path
        and len(discussion_path.parts) > 3
        and discussion_path.parts[:3] == ("docs", "teamwork", "discussion")
        and ".." not in discussion_path.parts,
        f"{label} path must be under docs/teamwork/discussion/",
    )
    match = DISCUSSION_PATH_RE.fullmatch(path)
    require(match is not None, f"{label} path must be dated kebab-case Markdown")
    try:
        date.fromisoformat(match.group(1))
    except ValueError:
        fail(f"{label} path must begin with a valid YYYY-MM-DD date")
    return discussion_path


def validate_discussion_lifecycle(
    index: dict,
    index_path: Path,
    project_reader: SafeProjectReader | None,
) -> None:
    """Validate that a saved discussion has one coherent active/closed state."""

    active = index["active"]
    entries = index["entries"]
    active_path = active.get("discussion")
    discussion_entries = [entry for entry in entries if entry["kind"] == "discussion"]

    seen_discussion_paths: set[str] = set()
    for entry in discussion_entries:
        validate_discussion_path(entry["path"], "discussion entry")
        require(
            entry["path"] not in seen_discussion_paths,
            f"duplicate discussion entries.path: {entry['path']}",
        )
        seen_discussion_paths.add(entry["path"])
        require(
            entry["status"] in DISCUSSION_ENTRY_STATUSES,
            f"discussion entry status has unknown value: {entry['status']}",
        )

    if active_path is None:
        for entry in discussion_entries:
            require(
                entry["status"] != "active" and entry["currentness"] != "current",
                "active.discussion is null but a discussion entry remains active/current",
            )
    else:
        validate_discussion_path(active_path, "active.discussion")
        active_records = [entry for entry in discussion_entries if entry["path"] == active_path]
        require(
            len(active_records) == 1,
            "active.discussion must resolve to exactly one discussion entry",
        )
        active_record = active_records[0]
        require(active_record["status"] == "active", "active.discussion entry status must be active")
        require(
            active_record["currentness"] == "current",
            "active.discussion entry currentness must be current",
        )
        require(
            active_record["authority"] == "supporting",
            "active.discussion entry authority must be supporting",
        )
        for entry in discussion_entries:
            if entry is active_record:
                continue
            require(
                entry["status"] != "active" and entry["currentness"] != "current",
                "only active.discussion may have an active/current discussion entry",
            )

    for entry in discussion_entries:
        if entry["status"] == "active":
            require(active_path == entry["path"], "active discussion entry must be active.discussion")
        if entry["currentness"] == "current":
            require(active_path == entry["path"], "current discussion entry must be active.discussion")

        if entry["status"] == "accepted":
            require(
                entry["currentness"] == "historical" and entry["authority"] == "supporting",
                "closed accepted discussion must be historical supporting context",
            )
        if entry["status"] == "superseded":
            require(
                entry["currentness"] == "historical" and entry["authority"] == "superseded",
                "superseded discussion must be historical with superseded authority",
            )

    if project_reader is None:
        return

    expected_anchor = active_path or "none"
    current_path = active.get("current")
    require(isinstance(current_path, str) and current_path, "actual project index must have active.current")
    require(
        current_path == CANONICAL_CURRENT_PATH,
        f"actual project index active.current must be {CANONICAL_CURRENT_PATH}",
    )
    current_relative = PurePosixPath(current_path)
    require(
        not current_relative.is_absolute()
        and current_relative.as_posix() == current_path
        and ".." not in current_relative.parts,
        "active.current path must be a project-relative path",
    )
    current_text = project_reader.read_text(
        current_relative,
        "active.current",
    )
    current_anchor = runtime_discussion_anchor(
        current_text,
        current_relative.as_posix(),
        DISCUSSION_CURRENT_LINE_RE,
        "Active discussion",
    )
    require(
        current_anchor == expected_anchor,
        "current.md Active discussion anchor must match active.discussion",
    )
    readme_relative = PurePosixPath("docs/teamwork/README.md")
    readme_text = project_reader.read_text(readme_relative, "runtime README")
    readme_anchor = runtime_discussion_anchor(
        readme_text,
        readme_relative.as_posix(),
        DISCUSSION_README_LINE_RE,
        "Active discussion route",
    )
    require(
        readme_anchor == expected_anchor,
        "runtime README Active discussion route must match active.discussion",
    )

    for entry in discussion_entries:
        artifact_relative = PurePosixPath(entry["path"])
        artifact_text = project_reader.read_text(
            artifact_relative,
            "discussion artifact",
        )
        validate_discussion_artifact_text(
            artifact_text,
            expected_status=entry["status"],
            expected_updated=str(entry["updated"]),
        )


def validate_index(
    index: dict,
    index_path: Path,
    project_reader: SafeProjectReader | None = None,
) -> None:
    required_top = [
        "schema_version",
        "last_updated",
        "project",
        "source_of_truth_order",
        "ignore_globs",
        "budgets",
        "active",
        "entries",
        "profiles",
    ]
    for key in required_top:
        require(key in index, f"missing top-level key: {key}")

    require(index["schema_version"] == 1, "schema_version must be 1")
    require(
        is_valid_iso_date(index["last_updated"]),
        "last_updated must be a valid YYYY-MM-DD date",
    )

    project = index["project"]
    require(isinstance(project, dict), "project must be object")
    for key in ["name", "root", "description"]:
        require(key in project, f"project missing key: {key}")
        require(isinstance(project[key], str) and project[key], f"project.{key} must be non-empty string")
    if project_reader is not None:
        require(
            project["root"] == ".",
            "actual project index project.root must be the lexical project root '.'",
        )
        require(
            index_path == project_reader.project_root / "docs/teamwork/index.json",
            "canonical index path must remain lexically inside the project root",
        )

    sto = index["source_of_truth_order"]
    require(isinstance(sto, list) and len(sto) > 0, "source_of_truth_order must be non-empty list")

    ignores = index["ignore_globs"]
    require(isinstance(ignores, list), "ignore_globs must be list")
    require(".planning/**" in ignores, "ignore_globs must include .planning/**")

    budgets = index["budgets"]
    require(isinstance(budgets, dict), "budgets must be object")
    header_only_keys = {"header_first"}
    legacy_keys = {"default_max_files", "default_max_artifact_bodies", "header_first"}
    require(
        set(budgets) in (header_only_keys, legacy_keys),
        "budgets must be exactly header-first or the complete legacy numeric form",
    )
    require(budgets.get("header_first") is True, "budgets.header_first must be true")
    if set(budgets) == legacy_keys:
        max_files = budgets["default_max_files"]
        max_bodies = budgets["default_max_artifact_bodies"]
        require(
            isinstance(max_files, int) and not isinstance(max_files, bool),
            "budgets.default_max_files must be integer",
        )
        require(1 <= max_files <= 10, "budgets.default_max_files must be between 1 and 10")
        require(
            isinstance(max_bodies, int) and not isinstance(max_bodies, bool),
            "budgets.default_max_artifact_bodies must be integer",
        )
        require(0 <= max_bodies <= 5, "budgets.default_max_artifact_bodies must be between 0 and 5")

    active = index["active"]
    require(isinstance(active, dict), "active must be object")
    for key in ACTIVE_POINTER_KEYS:
        if key in active:
            value = active[key]
            require(value is None or (isinstance(value, str) and value), f"active.{key} must be null or non-empty string when present")
    if "results" in active:
        require(isinstance(active["results"], list), "active.results must be list when present")

    entries = index["entries"]
    require(isinstance(entries, list) and len(entries) > 0, "entries must be non-empty list")
    active_unique = set()
    for i, entry in enumerate(entries):
        require(isinstance(entry, dict), f"entries[{i}] must be object")
        validate_entry(entry, i)
        if entry.get("status") == "active":
            key = (entry.get("topic"), entry.get("kind"))
            require(key not in active_unique, f"duplicate active entry for topic+kind: {key[0]}::{key[1]}")
            active_unique.add(key)

    validate_active_pointers(active, entries)
    validate_discussion_lifecycle(index, index_path, project_reader)

    profiles = index["profiles"]
    require(isinstance(profiles, dict) and len(profiles) > 0, "profiles must be non-empty object")

    pending = index.get("pending", [])
    require(isinstance(pending, list), "pending must be list when present")
    require(len(pending) <= 5, "pending cap exceeded: max 5")


def validate_templates(root: Path) -> None:
    readme_path = root / "skills/using-teamwork/references/teamwork-index-readme-template.md"
    current_path = root / "skills/using-teamwork/references/teamwork-current-template.md"

    readme = read_text(readme_path)
    current = read_text(current_path)

    require(line_count(readme) <= 120, "teamwork-index-readme-template.md exceeds 120 lines")
    require(word_count(readme) <= 1200, "teamwork-index-readme-template.md exceeds 1200 words")

    require(line_count(current) <= 120, "teamwork-current-template.md exceeds 120 lines")
    require(word_count(current) <= 700, "teamwork-current-template.md exceeds 700 words")

    required_readme_phrases = [
        "broad scan",
        "stage",
        "compatibility retrieval hints",
        "not execution limits",
        "index.json",
        "Project instructions may point here",
        "Active discussion route",
    ]
    for phrase in required_readme_phrases:
        require(phrase.lower() in readme.lower(), f"README template missing required language: {phrase}")

    require(
        "Active discussion:" in current,
        "current template must expose an Active discussion anchor",
    )

def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python3 scripts/validate_teamwork_index.py <index-template.json>", file=sys.stderr)
        return 2

    root = Path(__file__).resolve().parents[1]
    project_reader: SafeProjectReader | None = None

    try:
        template_path = checked_index_input(sys.argv[1])
        project_root = real_project_root(template_path)
        if project_root is None:
            raw = read_standalone_index(template_path)
        else:
            project_reader = SafeProjectReader(project_root)
            project_reader.require_no_pending_discussion_transaction()
            raw = project_reader.read_text(
                PurePosixPath("docs/teamwork/index.json"),
                "index input",
            )
        data = json.loads(raw)
        validate_index(data, template_path, project_reader)
        if project_reader is not None:
            project_reader.require_no_pending_discussion_transaction()
        validate_templates(root)
    except (ValidationError, json.JSONDecodeError) as exc:
        failure: ValidationError | json.JSONDecodeError = exc
        if project_reader is not None:
            try:
                project_reader.require_no_pending_discussion_transaction()
            except ValidationError as transaction_exc:
                failure = transaction_exc
        print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    finally:
        if project_reader is not None:
            project_reader.close()

    print("PASS: Teamwork index contract/template validation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
