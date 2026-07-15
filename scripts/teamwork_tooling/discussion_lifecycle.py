"""Fail-closed evidence helpers for a controlled discussion write lifecycle.

The helpers intentionally never invoke a model, read credentials, or mutate the
project being observed.  A caller snapshots a disposable worktree before a
workspace-write treatment, then compares that snapshot with the post-treatment
state.  The comparison permits only Teamwork's durable discussion footprint.
This endpoint comparison cannot prove that a path was not written and then
restored completely between the two snapshots.
"""

from __future__ import annotations

import hashlib
import os
import re
import stat
from dataclasses import dataclass
from datetime import date
from pathlib import Path, PurePosixPath
from typing import Iterable, Mapping


SCHEMA_VERSION = 3
MEMORY_ANCHORS = (
    "docs/teamwork/index.json",
    "docs/teamwork/current.md",
    "docs/teamwork/README.md",
)
DISCUSSION_DIRECTORY = "docs/teamwork/discussion"
_DISCUSSION_PATH_RE = re.compile(
    r"^docs/teamwork/discussion/(\d{4}-\d{2}-\d{2})-([a-z0-9]+(?:-[a-z0-9]+)*)\.md$"
)
_ALLOWED_NEW_DIRECTORIES = frozenset({"docs", "docs/teamwork", DISCUSSION_DIRECTORY})
_UNSAFE_MANAGED_FILE_MODE = 0o7133  # special/execute bits, or group/world write
_UNSAFE_NEW_DIRECTORY_MODE = 0o022


class DiscussionLifecycleError(ValueError):
    """Raised when a snapshot or lifecycle footprint is not safe to accept."""


class FreshSessionRecoveryError(DiscussionLifecycleError):
    """Raised when a fresh-session response lacks the requested recovery anchors."""


@dataclass(frozen=True)
class ManifestEntry:
    """One non-root filesystem entry, represented without file contents."""

    kind: str
    mode: int
    device: int | None = None
    inode: int | None = None
    size: int | None = None
    sha256: str | None = None
    nlink: int | None = None
    link_target: str | None = None

    def to_dict(self) -> dict[str, object]:
        value: dict[str, object] = {"kind": self.kind, "mode": self.mode}
        if self.device is not None:
            value["device"] = self.device
        if self.inode is not None:
            value["inode"] = self.inode
        if self.size is not None:
            value["size"] = self.size
        if self.sha256 is not None:
            value["sha256"] = self.sha256
        if self.nlink is not None:
            value["nlink"] = self.nlink
        if self.link_target is not None:
            value["link_target"] = self.link_target
        return value

    @classmethod
    def from_dict(cls, value: object, *, path: str) -> "ManifestEntry":
        if not isinstance(value, dict):
            raise DiscussionLifecycleError(f"manifest entry {path} must be an object")
        allowed = {
            "kind",
            "mode",
            "device",
            "inode",
            "size",
            "sha256",
            "nlink",
            "link_target",
        }
        unknown = sorted(set(value) - allowed)
        if unknown:
            raise DiscussionLifecycleError(
                f"manifest entry {path} has unknown fields: {', '.join(unknown)}"
            )
        kind = value.get("kind")
        mode = value.get("mode")
        device = value.get("device")
        inode = value.get("inode")
        size = value.get("size")
        sha256 = value.get("sha256")
        nlink = value.get("nlink")
        link_target = value.get("link_target")
        if kind not in {"directory", "file", "symlink", "other"}:
            raise DiscussionLifecycleError(f"manifest entry {path} has invalid kind")
        if not isinstance(mode, int) or isinstance(mode, bool) or not 0 <= mode <= 0o7777:
            raise DiscussionLifecycleError(f"manifest entry {path} has invalid mode")
        for label, number in (("device", device), ("inode", inode)):
            if number is not None and (
                not isinstance(number, int) or isinstance(number, bool) or number < 0
            ):
                raise DiscussionLifecycleError(
                    f"manifest entry {path} has invalid {label}"
                )
        if kind in {"file", "directory"} and (device is None or inode is None):
            raise DiscussionLifecycleError(
                f"manifest {kind} entry {path} must include device and inode"
            )
        if kind not in {"file", "directory"} and (
            device is not None or inode is not None
        ):
            raise DiscussionLifecycleError(
                f"manifest {kind} entry {path} must not include device or inode"
            )
        if size is not None and (
            not isinstance(size, int) or isinstance(size, bool) or size < 0
        ):
            raise DiscussionLifecycleError(f"manifest entry {path} has invalid size")
        if sha256 is not None and (
            not isinstance(sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", sha256)
        ):
            raise DiscussionLifecycleError(f"manifest entry {path} has invalid sha256")
        if nlink is not None and (
            not isinstance(nlink, int) or isinstance(nlink, bool) or nlink < 1
        ):
            raise DiscussionLifecycleError(f"manifest entry {path} has invalid nlink")
        if link_target is not None and not isinstance(link_target, str):
            raise DiscussionLifecycleError(
                f"manifest entry {path} has invalid link_target"
            )
        if kind == "file" and (size is None or sha256 is None or nlink is None):
            raise DiscussionLifecycleError(
                f"manifest file entry {path} must include size, sha256, and nlink"
            )
        if kind != "file" and (size is not None or sha256 is not None or nlink is not None):
            raise DiscussionLifecycleError(
                f"manifest non-file entry {path} must not include size, sha256, or nlink"
            )
        if kind == "symlink" and link_target is None:
            raise DiscussionLifecycleError(
                f"manifest symlink entry {path} must include link_target"
            )
        if kind != "symlink" and link_target is not None:
            raise DiscussionLifecycleError(
                f"manifest non-symlink entry {path} must not include link_target"
            )
        return cls(
            kind=kind,
            mode=mode,
            device=device,
            inode=inode,
            size=size,
            sha256=sha256,
            nlink=nlink,
            link_target=link_target,
        )


@dataclass(frozen=True)
class ProjectRootMetadata:
    """Identity and permissions of the observed project root itself."""

    kind: str
    device: int
    inode: int
    mode: int

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "device": self.device,
            "inode": self.inode,
            "mode": self.mode,
        }

    @classmethod
    def from_dict(cls, value: object) -> "ProjectRootMetadata":
        if not isinstance(value, dict):
            raise DiscussionLifecycleError("manifest root_metadata must be an object")
        required = {"kind", "device", "inode", "mode"}
        missing = sorted(required - set(value))
        unknown = sorted(set(value) - required)
        if missing:
            raise DiscussionLifecycleError(
                f"manifest root_metadata missing fields: {', '.join(missing)}"
            )
        if unknown:
            raise DiscussionLifecycleError(
                f"manifest root_metadata has unknown fields: {', '.join(unknown)}"
            )
        kind = value["kind"]
        device = value["device"]
        inode = value["inode"]
        mode = value["mode"]
        if kind != "directory":
            raise DiscussionLifecycleError(
                "manifest root_metadata kind must be directory"
            )
        for label, number in (("device", device), ("inode", inode)):
            if not isinstance(number, int) or isinstance(number, bool) or number < 0:
                raise DiscussionLifecycleError(
                    f"manifest root_metadata has invalid {label}"
                )
        if not isinstance(mode, int) or isinstance(mode, bool) or not 0 <= mode <= 0o7777:
            raise DiscussionLifecycleError("manifest root_metadata has invalid mode")
        return cls(kind=kind, device=device, inode=inode, mode=mode)


@dataclass(frozen=True)
class WorkspaceManifest:
    """Content-and-metadata snapshot of the root and every project entry."""

    root: str
    root_metadata: ProjectRootMetadata
    entries: Mapping[str, ManifestEntry]

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": SCHEMA_VERSION,
            "root": self.root,
            "root_metadata": self.root_metadata.to_dict(),
            "entries": {
                path: self.entries[path].to_dict() for path in sorted(self.entries)
            },
        }

    @classmethod
    def from_dict(cls, value: object) -> "WorkspaceManifest":
        if not isinstance(value, dict):
            raise DiscussionLifecycleError("manifest must be an object")
        required = {"schema_version", "root", "root_metadata", "entries"}
        missing = sorted(required - set(value))
        unknown = sorted(set(value) - required)
        if missing:
            raise DiscussionLifecycleError(
                f"manifest missing fields: {', '.join(missing)}"
            )
        if unknown:
            raise DiscussionLifecycleError(
                f"manifest has unknown fields: {', '.join(unknown)}"
            )
        if value["schema_version"] != SCHEMA_VERSION:
            raise DiscussionLifecycleError(
                f"manifest schema_version must be {SCHEMA_VERSION}"
            )
        root = value["root"]
        entries = value["entries"]
        if not isinstance(root, str) or not root:
            raise DiscussionLifecycleError("manifest root must be a non-empty string")
        if not isinstance(entries, dict):
            raise DiscussionLifecycleError("manifest entries must be an object")
        parsed: dict[str, ManifestEntry] = {}
        for path, entry in entries.items():
            _require_safe_relative_path(path, label="manifest entry")
            parsed[path] = ManifestEntry.from_dict(entry, path=path)
        return cls(
            root=root,
            root_metadata=ProjectRootMetadata.from_dict(value["root_metadata"]),
            entries=parsed,
        )


@dataclass(frozen=True)
class WorkspaceChange:
    """One path whose manifest representation changed between two snapshots."""

    path: str
    before: ManifestEntry | None
    after: ManifestEntry | None

    @property
    def action(self) -> str:
        if self.before is None:
            return "created"
        if self.after is None:
            return "removed"
        return "modified"


@dataclass(frozen=True)
class DiscussionWriteFootprint:
    """Validated, minimal set of worktree paths touched by one lifecycle phase."""

    changes: tuple[WorkspaceChange, ...]
    discussion_path: str | None

    @property
    def changed_paths(self) -> tuple[str, ...]:
        return tuple(change.path for change in self.changes)

    @property
    def changed_memory_anchors(self) -> tuple[str, ...]:
        return tuple(path for path in MEMORY_ANCHORS if path in self.changed_paths)

    def to_dict(self) -> dict[str, object]:
        return {
            "changed_paths": list(self.changed_paths),
            "changed_memory_anchors": list(self.changed_memory_anchors),
            "discussion_path": self.discussion_path,
            "changes": [
                {
                    "path": change.path,
                    "action": change.action,
                    "before": change.before.to_dict() if change.before else None,
                    "after": change.after.to_dict() if change.after else None,
                }
                for change in self.changes
            ],
        }


@dataclass(frozen=True)
class FreshSessionRecovery:
    """A narrow structural assertion about one fresh-session response."""

    matched_fragments: tuple[str, ...]
    question_mark_count: int


def _require_safe_relative_path(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise DiscussionLifecycleError(f"{label} path must be a non-empty string")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or path.as_posix() != value:
        raise DiscussionLifecycleError(
            f"{label} path is not a safe relative POSIX path: {value!r}"
        )
    return value


def _require_same_inode(
    opened: os.stat_result, expected: os.stat_result, *, path: str
) -> None:
    if (
        opened.st_dev != expected.st_dev
        or opened.st_ino != expected.st_ino
        or not stat.S_ISREG(opened.st_mode)
        or expected.st_nlink != 1
        or opened.st_nlink != 1
    ):
        raise DiscussionLifecycleError(
            f"filesystem entry changed identity while capturing manifest: {path}"
        )


def _hash_file(
    directory_fd: int, name: str, *, display_path: str, expected: os.stat_result
) -> str:
    digest = hashlib.sha256()
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise DiscussionLifecycleError(
            "platform cannot safely capture files without following symlinks"
        )
    flags = os.O_RDONLY | nofollow | getattr(os, "O_CLOEXEC", 0)
    fd = -1
    try:
        fd = os.open(name, flags, dir_fd=directory_fd)
        _require_same_inode(os.fstat(fd), expected, path=display_path)
        handle = os.fdopen(fd, "rb")
        fd = -1
        with handle:
            while chunk := handle.read(1024 * 1024):
                digest.update(chunk)
    except OSError as exc:
        raise DiscussionLifecycleError(f"cannot hash {display_path}: {exc}") from exc
    finally:
        if fd >= 0:
            os.close(fd)
    return digest.hexdigest()


def _entry_from_dirent(
    entry: os.DirEntry[str],
    directory_fd: int,
    *,
    display_path: str,
    root_device: int,
) -> tuple[ManifestEntry, os.stat_result]:
    try:
        metadata = entry.stat(follow_symlinks=False)
    except OSError as exc:
        raise DiscussionLifecycleError(f"cannot stat {entry.path}: {exc}") from exc
    if metadata.st_dev != root_device:
        raise DiscussionLifecycleError(
            f"filesystem entry crosses project root device boundary: {display_path}"
        )
    mode = stat.S_IMODE(metadata.st_mode)
    if stat.S_ISDIR(metadata.st_mode):
        return (
            ManifestEntry(
                kind="directory",
                mode=mode,
                device=metadata.st_dev,
                inode=metadata.st_ino,
            ),
            metadata,
        )
    if stat.S_ISREG(metadata.st_mode):
        if metadata.st_nlink != 1:
            raise DiscussionLifecycleError(
                f"regular file must have exactly one hard link: {display_path}"
            )
        return (
            ManifestEntry(
                kind="file",
                mode=mode,
                device=metadata.st_dev,
                inode=metadata.st_ino,
                size=metadata.st_size,
                sha256=_hash_file(
                    directory_fd,
                    entry.name,
                    display_path=display_path,
                    expected=metadata,
                ),
                nlink=metadata.st_nlink,
            ),
            metadata,
        )
    if stat.S_ISLNK(metadata.st_mode):
        raise DiscussionLifecycleError(
            f"symlink is not permitted in observed project: {display_path}"
        )
    raise DiscussionLifecycleError(
        f"special filesystem node is not permitted in observed project: {display_path}"
    )


def capture_workspace_manifest(project_root: Path | str) -> WorkspaceManifest:
    """Capture a project tree without following symlinks.

    Every safe entry is represented, including ``.git`` metadata.  Symlinks,
    multiply-linked regular files, special nodes, and entries on another device
    fail immediately because they can escape the manifest's one-path-per-object
    boundary.  Portable ``stat`` metadata cannot independently identify an
    ancestor symlink or a same-device bind mount; callers must provide a trusted
    parent path and an unmounted disposable fixture.
    """

    root = Path(os.path.abspath(os.fspath(Path(project_root).expanduser())))
    try:
        requested_root_stat = os.lstat(root)
    except OSError as exc:
        raise DiscussionLifecycleError(f"cannot stat project root {root}: {exc}") from exc
    if stat.S_ISLNK(requested_root_stat.st_mode):
        raise DiscussionLifecycleError(f"project root must not be a symlink: {root}")
    if not stat.S_ISDIR(requested_root_stat.st_mode):
        raise DiscussionLifecycleError(f"project root is not a directory: {root}")
    entries: dict[str, ManifestEntry] = {}

    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory_flag = getattr(os, "O_DIRECTORY", None)
    if nofollow is None or directory_flag is None:
        raise DiscussionLifecycleError(
            "platform cannot safely capture directories without following symlinks"
        )
    directory_flags = (
        os.O_RDONLY | nofollow | directory_flag | getattr(os, "O_CLOEXEC", 0)
    )

    def walk(directory_fd: int, relative: PurePosixPath, root_device: int) -> None:
        try:
            with os.scandir(directory_fd) as iterator:
                children = sorted(iterator, key=lambda child: child.name)
        except OSError as exc:
            raise DiscussionLifecycleError(f"cannot list {relative}: {exc}") from exc
        for child in children:
            rel = (relative / child.name).as_posix()
            manifest_entry, metadata = _entry_from_dirent(
                child,
                directory_fd,
                display_path=rel,
                root_device=root_device,
            )
            entries[rel] = manifest_entry
            if manifest_entry.kind == "directory":
                child_fd = -1
                try:
                    child_fd = os.open(child.name, directory_flags, dir_fd=directory_fd)
                    opened = os.fstat(child_fd)
                    if (
                        opened.st_dev != metadata.st_dev
                        or opened.st_ino != metadata.st_ino
                        or not stat.S_ISDIR(opened.st_mode)
                    ):
                        raise DiscussionLifecycleError(
                            f"filesystem entry changed identity while capturing manifest: {rel}"
                        )
                    walk(child_fd, PurePosixPath(rel), root_device)
                except OSError as exc:
                    raise DiscussionLifecycleError(f"cannot open directory {rel}: {exc}") from exc
                finally:
                    if child_fd >= 0:
                        os.close(child_fd)

    root_fd = -1
    root_metadata: ProjectRootMetadata | None = None
    try:
        root_fd = os.open(root, directory_flags)
        root_stat = os.fstat(root_fd)
        if (
            root_stat.st_dev != requested_root_stat.st_dev
            or root_stat.st_ino != requested_root_stat.st_ino
            or not stat.S_ISDIR(root_stat.st_mode)
        ):
            raise DiscussionLifecycleError(
                f"project root changed identity while capturing manifest: {root}"
            )
        root_metadata = ProjectRootMetadata(
            kind="directory",
            device=root_stat.st_dev,
            inode=root_stat.st_ino,
            mode=stat.S_IMODE(root_stat.st_mode),
        )
        walk(root_fd, PurePosixPath("."), root_stat.st_dev)
    except OSError as exc:
        raise DiscussionLifecycleError(f"cannot open project root {root}: {exc}") from exc
    finally:
        if root_fd >= 0:
            os.close(root_fd)
    if root_metadata is None:
        raise DiscussionLifecycleError(f"could not capture project root metadata: {root}")
    return WorkspaceManifest(
        root=str(root), root_metadata=root_metadata, entries=entries
    )


def manifest_changes(
    before: WorkspaceManifest, after: WorkspaceManifest
) -> tuple[WorkspaceChange, ...]:
    """Return a deterministic pre/post diff, rejecting accidental cross-root use."""

    if before.root != after.root:
        raise DiscussionLifecycleError(
            "pre/post manifests describe different project roots; refuse cross-worktree comparison"
        )
    if before.root_metadata.kind != after.root_metadata.kind:
        raise DiscussionLifecycleError("project root type changed between snapshots")
    if (
        before.root_metadata.device != after.root_metadata.device
        or before.root_metadata.inode != after.root_metadata.inode
    ):
        raise DiscussionLifecycleError("project root identity changed between snapshots")
    if before.root_metadata.mode != after.root_metadata.mode:
        raise DiscussionLifecycleError("project root mode changed between snapshots")
    return tuple(
        WorkspaceChange(
            path=path,
            before=before.entries.get(path),
            after=after.entries.get(path),
        )
        for path in sorted(set(before.entries) | set(after.entries))
        if before.entries.get(path) != after.entries.get(path)
    )


def _discussion_artifact_path(path: str) -> bool:
    match = _DISCUSSION_PATH_RE.fullmatch(path)
    if match is None:
        return False
    try:
        date.fromisoformat(match.group(1))
    except ValueError:
        return False
    return True


def _validate_allowed_change(change: WorkspaceChange) -> str | None:
    """Return a violation message, or ``None`` for one permitted change."""

    path = change.path
    if path in MEMORY_ANCHORS:
        if change.after is None or change.after.kind != "file":
            return f"managed memory anchor must remain a regular file: {path}"
        if change.before is not None and change.before.mode != change.after.mode:
            return f"modified existing file must preserve mode: {path}"
        return None
    if _discussion_artifact_path(path):
        if change.after is None or change.after.kind != "file":
            return f"discussion artifact must remain a regular file: {path}"
        if change.before is not None and change.before.mode != change.after.mode:
            return f"modified existing file must preserve mode: {path}"
        return None
    if path in _ALLOWED_NEW_DIRECTORIES:
        if change.before is None and change.after is not None and change.after.kind == "directory":
            if change.after.mode & _UNSAFE_NEW_DIRECTORY_MODE:
                return f"new directory must not be group/world writable: {path}"
            return None
        return f"only creation of a required parent directory is permitted: {path}"
    if path.startswith(f"{DISCUSSION_DIRECTORY}/"):
        return f"discussion artifact must be dated kebab-case Markdown: {path}"
    return f"write outside the discussion lifecycle allowlist: {path}"


def _managed_state_violations(manifest: WorkspaceManifest) -> list[str]:
    violations: list[str] = []
    for path, entry in manifest.entries.items():
        if entry.kind == "symlink":
            violations.append(f"symlink is not permitted in observed project: {path}")
            continue
        if entry.kind == "other":
            violations.append(
                f"special filesystem node is not permitted in observed project: {path}"
            )
            continue
        if entry.kind == "file" and entry.nlink != 1:
            violations.append(f"regular file must have exactly one hard link: {path}")
            continue
        if path in _ALLOWED_NEW_DIRECTORIES:
            if entry.kind != "directory":
                violations.append(f"managed ancestor must be a directory: {path}")
            elif entry.mode & _UNSAFE_NEW_DIRECTORY_MODE:
                violations.append(
                    "managed ancestor directory must not be group/world writable: "
                    + path
                )
            continue
        if path in MEMORY_ANCHORS:
            label = "managed memory anchor"
        elif _discussion_artifact_path(path):
            label = "managed discussion artifact"
        else:
            continue
        if entry.kind != "file":
            violations.append(f"{label} must be a regular file: {path}")
        elif entry.mode & _UNSAFE_MANAGED_FILE_MODE:
            violations.append(f"unsafe permissions on {label}: {path}")
    return violations


def validate_discussion_write_footprint(
    before: WorkspaceManifest,
    after: WorkspaceManifest,
    *,
    require_discussion_change: bool = True,
    require_memory_anchor_updates: bool = False,
    allow_discussion_replacement: bool = False,
) -> DiscussionWriteFootprint:
    """Validate the minimal worktree footprint of a persisted discussion update.

    A valid default footprint can modify only the three runtime-memory anchors
    and one date-prefixed discussion Markdown artifact.  Explicit replacement
    mode instead requires one existing artifact modification, one new artifact,
    and all three anchor updates.  On first creation, the necessary ``docs``
    parent directories may be added.  Removing an artifact, swapping it for a
    symlink, changing existing file modes, or changing any other worktree path
    fails closed.

    ``require_memory_anchor_updates`` is intended for activation/closure checks;
    leave it false for an ordinary checkpoint that only updates the same active
    discussion artifact.
    """

    changes = manifest_changes(before, after)
    violations = _managed_state_violations(before) + _managed_state_violations(after)
    violations.extend(
        violation
        for change in changes
        if (violation := _validate_allowed_change(change)) is not None
    )
    discussion_changes = [
        change for change in changes if _discussion_artifact_path(change.path)
    ]
    if allow_discussion_replacement:
        actions = sorted(change.action for change in discussion_changes)
        if len(discussion_changes) != 2 or actions != ["created", "modified"]:
            violations.append(
                "discussion replacement must modify one existing dated artifact and create one new dated artifact"
            )
    elif len(discussion_changes) > 1:
        violations.append(
            "at most one dated discussion artifact may change: "
            + ", ".join(change.path for change in discussion_changes)
        )
    if require_discussion_change and not discussion_changes:
        violations.append("discussion lifecycle did not change a dated discussion artifact")
    changed_paths = {change.path for change in changes}
    if require_memory_anchor_updates or allow_discussion_replacement:
        missing = [path for path in MEMORY_ANCHORS if path not in changed_paths]
        if missing:
            violations.append(
                "discussion lifecycle did not update every runtime-memory anchor: "
                + ", ".join(missing)
            )
    if violations:
        raise DiscussionLifecycleError("; ".join(violations))
    return DiscussionWriteFootprint(
        changes=changes,
        discussion_path=(
            next(
                (change.path for change in discussion_changes if change.action == "created"),
                discussion_changes[0].path if discussion_changes else None,
            )
            if discussion_changes
            else None
        ),
    )


def _normalize_text(value: str) -> str:
    return " ".join(value.casefold().split())


def assert_fresh_session_recovery(
    output: str,
    *,
    required_fragments: Iterable[str],
    maximum_question_marks: int = 1,
) -> FreshSessionRecovery:
    """Check explicit recovery anchors in a fresh-session response.

    This intentionally makes no semantic claim by itself.  The caller supplies
    concise, decision-relevant fragments recovered from the persisted artifact;
    the helper then proves that the fresh response mentions each one and does not
    turn recovery into a multi-question interrogation.
    """

    if not isinstance(output, str) or not output.strip():
        raise FreshSessionRecoveryError("fresh-session output must be a non-empty string")
    if (
        not isinstance(maximum_question_marks, int)
        or isinstance(maximum_question_marks, bool)
        or maximum_question_marks < 0
    ):
        raise FreshSessionRecoveryError("maximum_question_marks must be a non-negative integer")
    fragments = tuple(required_fragments)
    if not fragments:
        raise FreshSessionRecoveryError("fresh-session recovery requires at least one anchor fragment")
    normalized_output = _normalize_text(output)
    normalized_fragments: list[str] = []
    for fragment in fragments:
        if not isinstance(fragment, str) or not fragment.strip():
            raise FreshSessionRecoveryError(
                "fresh-session recovery fragments must be non-empty strings"
            )
        normalized = _normalize_text(fragment)
        if normalized not in normalized_output:
            raise FreshSessionRecoveryError(
                f"fresh-session output did not recover required fragment: {fragment!r}"
            )
        normalized_fragments.append(fragment)
    question_mark_count = output.count("?") + output.count("？")
    if question_mark_count > maximum_question_marks:
        raise FreshSessionRecoveryError(
            "fresh-session output exceeds the question bound: "
            f"{question_mark_count} > {maximum_question_marks}"
        )
    return FreshSessionRecovery(
        matched_fragments=tuple(normalized_fragments),
        question_mark_count=question_mark_count,
    )
