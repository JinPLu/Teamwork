"""Eval case, rubric, and ledger validation."""

from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any

from .contracts import *  # noqa: F403
from .sources import (
    validate_design_adversarial_reference_contract,
    validate_semantic_sources,
    validate_skill_source_contract,
)
from ..semantic_review import SemanticReviewError, validate_accepted_ledger_v2


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))  # noqa: F405
    except ValueError:
        return str(path)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise EvalError(f"{display_path(path)}: invalid JSON: {exc}") from exc  # noqa: F405


def require_string(value: Any, field: str, path: Path) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvalError(f"{display_path(path)}: {field} must be a non-empty string")  # noqa: F405
    return value


def require_string_list(value: Any, field: str, path: Path) -> list[str]:
    if not isinstance(value, list) or not value:
        raise EvalError(f"{display_path(path)}: {field} must be a non-empty list")  # noqa: F405
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise EvalError(f"{display_path(path)}: {field} must contain non-empty strings")  # noqa: F405
    return value


def is_package_relative(value: str) -> bool:
    path = Path(value)
    return not path.is_absolute() and ".." not in path.parts


def is_glob_like(value: str) -> bool:
    return any(char in value for char in GLOB_CHARS)  # noqa: F405


def _producer_path_allowed(producer_class: str, source: str) -> bool:
    for prefix in PRODUCER_PATH_PREFIXES[producer_class]:  # noqa: F405
        if source == prefix or (prefix.endswith("/") and source.startswith(prefix)):
            return True
    return False


def validate_producers(
    value: Any,
    path: Path,
    requirement_key: tuple[str, str],
) -> list[tuple[str, str]]:
    if not isinstance(value, list) or not value:
        raise EvalError(f"{display_path(path)}: producers must be a non-empty list")  # noqa: F405
    producers: list[tuple[str, str]] = []
    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict) or set(item) != {"class", "source"}:
            raise EvalError(
                f"{display_path(path)}: producers[{index}] must contain exactly class and source"
            )  # noqa: F405
        producer_class = require_string(item.get("class"), f"producers[{index}].class", path)
        source = require_string(item.get("source"), f"producers[{index}].source", path)
        if producer_class not in PRODUCER_CLASSES:  # noqa: F405
            raise EvalError(f"{display_path(path)}: unknown producer class: {producer_class}")  # noqa: F405
        if not is_package_relative(source) or is_glob_like(source):
            raise EvalError(f"{display_path(path)}: producer source must be one exact package path: {source}")  # noqa: F405
        if not _producer_path_allowed(producer_class, source):
            raise EvalError(
                f"{display_path(path)}: {source} is not owned by producer class {producer_class}"
            )  # noqa: F405
        candidate = ROOT / source  # noqa: F405
        if not candidate.is_file():
            raise EvalError(f"{display_path(path)}: producer source does not exist: {source}")  # noqa: F405
        producers.append((producer_class, source))
    if len(producers) != len(set(producers)):
        raise EvalError(f"{display_path(path)}: duplicate producer binding")  # noqa: F405
    expected = CASE_PRODUCER_REQUIREMENTS[requirement_key]  # noqa: F405
    if set(producers) != expected:
        missing = sorted(expected - set(producers))
        extra = sorted(set(producers) - expected)
        raise EvalError(
            f"{display_path(path)}: producer binding mismatch for "
            f"{requirement_key[0]}/{requirement_key[1]}; missing={missing}, extra={extra}"
        )  # noqa: F405
    return producers


def _require_source_phrases(source: str, path: Path, source_path: str, groups: list[tuple[str, ...]]) -> None:
    normalized = " ".join(source.casefold().replace("_", "-").split())
    for alternatives in groups:
        if not any(item.casefold() in normalized for item in alternatives):
            raise EvalError(
                f"{display_path(path)}: bound producer {source_path} lacks source-owned rule {alternatives[0]}"
            )  # noqa: F405


def _seed_legacy_v1_memory(memory: Path) -> None:
    """Create a disposable legacy-v1 memory tree for transaction probes.

    Fresh 5.1 templates are v2 case-bundle inputs and intentionally no longer
    carry maintained legacy current/README files. These eval probes exercise the
    legacy transaction CLI, so they seed the smallest valid legacy fixture inside
    the temporary project instead of depending on fresh-init templates.
    """

    memory.mkdir(parents=True, exist_ok=True)
    (memory / "current.md").write_text(
        "# Teamwork Current State\n\n"
        "Last Updated: 2026-06-01\n\n"
        "## Active Snapshot\n\n"
        "- Current focus: Transaction probe.\n"
        "- Active design: none.\n"
        "- Active plan: none.\n"
        "- Active Goal progress: none.\n"
        "- Progress summary: Disposable legacy-v1 memory fixture.\n"
        "- Latest result: Probe memory is ready.\n"
        "- Blockers: none recorded.\n",
        encoding="utf-8",
    )
    (memory / "README.md").write_text(
        "# Teamwork Runtime Index README\n\nDisposable legacy-v1 probe fixture.\n",
        encoding="utf-8",
    )
    (memory / "index.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "last_updated": "2026-06-01",
                "project": {
                    "name": "Probe Project",
                    "root": ".",
                    "description": "Disposable Teamwork legacy-v1 memory fixture.",
                },
                "source_of_truth_order": ["active", "linked", "header_search", "fulltext"],
                "ignore_globs": [".planning/**"],
                "budgets": {"header_first": True},
                "active": {
                    "collaborate": None,
                    "current": "docs/teamwork/current.md",
                    "design": None,
                    "plan": None,
                    "progress": None,
                    "report": None,
                    "results": [],
                },
                "collaborate_consumed_sources": [],
                "entries": [
                    {
                        "topic": "probe",
                        "kind": "result",
                        "title": "Transaction probe",
                        "status": "active",
                        "currentness": "current",
                        "authority": "active-summary",
                        "path": "docs/teamwork/current.md",
                        "linked": [],
                        "evidence_paths": ["docs/teamwork/current.md"],
                        "supersedes": [],
                        "search_keys": ["probe"],
                        "updated": "2026-06-01",
                        "summary": "Disposable legacy-v1 memory fixture for transaction probes.",
                    }
                ],
                "profiles": {},
                "pending": [],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


@lru_cache(maxsize=16)
def _collaborate_transaction_cli_probe(source: str) -> str | None:
    """Exercise the case-v2 Collaborate owner CLI rather than parser details."""

    with tempfile.TemporaryDirectory(prefix="teamwork-collaborate-probe-") as temporary:
        root = Path(temporary)
        script = root / "discussion-transaction.py"
        script.write_text(source, encoding="utf-8")
        project = root / "project"
        memory = project / "docs/teamwork"
        memory.mkdir(parents=True, exist_ok=True)
        index = {
            "schema_version": 2,
            "project": {
                "name": "Teamwork",
                "root": ".",
                "description": "Local Teamwork case-bundle index for this project.",
            },
            "active_cases": [],
            "claim_heads": {},
            "aliases": {},
            "recent_cases": [],
            "migration": None,
        }
        try:
            (memory / "index.json").write_text(
                json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        except OSError as exc:
            return f"cannot prepare case-v2 transaction probe: {exc}"

        def invoke(*arguments: str) -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                [sys.executable, str(script), *arguments], cwd=root, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=10,
            )

        try:
            inspected = invoke("case-inspect", "--project-root", str(project))
            if inspected.returncode != 0:
                return f"case-inspect command failed: {inspected.stderr.strip()}"
            inspection = json.loads(inspected.stdout)
            revision = inspection.get("revision") if isinstance(inspection, dict) else None
            if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{64}", revision):
                return "case-inspect command did not return an opaque revision"

            schema = invoke("case-schema", "create")
            if schema.returncode != 0:
                return f"case-schema create command failed: {schema.stderr.strip()}"
            skeleton = json.loads(schema.stdout)
            if not isinstance(skeleton, dict) or skeleton.get("operation") != "create":
                return "case-schema create did not return the create request skeleton"
            request = {
                **skeleton,
                "expected_revision": revision,
                "case_seed": "01" * 32,
                "title": "Probe Collaborate transaction ownership",
                "task_key": "probe-collaborate-transaction",
                "aliases": ["probe-collaborate-transaction"],
                "initial_phase": "collaborating",
            }
            request_path = root / "request.json"
            request_path.write_text(json.dumps(request, ensure_ascii=False), encoding="utf-8")
            applied = invoke("case-apply", "--project-root", str(project), "--request", str(request_path))
            if applied.returncode != 0:
                return f"case-apply create command failed: {applied.stderr.strip()}"
            result = json.loads(applied.stdout)
            if not isinstance(result, dict) or result.get("schema_mode") != "case-v2":
                return "case-apply create did not produce a case-v2 result"
            case_id = result.get("case_id")
            manifest_revision = result.get("manifest_revision")
            revision = result.get("revision")
            if not all(isinstance(value, str) and value for value in (case_id, manifest_revision, revision)):
                return "case-apply create did not return case and revision identifiers"

            upsert_schema = invoke("case-schema", "collaborate-upsert")
            if upsert_schema.returncode != 0:
                return f"case-schema collaborate-upsert command failed: {upsert_schema.stderr.strip()}"
            upsert = json.loads(upsert_schema.stdout)
            if not isinstance(upsert, dict) or upsert.get("operation") != "collaborate-upsert":
                return "case-schema collaborate-upsert did not return the update request skeleton"
            upsert.update(
                {
                    "expected_revision": revision,
                    "case_id": case_id,
                    "expected_manifest_revision": manifest_revision,
                    "source_digest": "02" * 32,
                    "body": "The Collaborate case-v2 transaction owner route is executable.",
                }
            )
            request_path.write_text(json.dumps(upsert, ensure_ascii=False), encoding="utf-8")
            applied = invoke("case-apply", "--project-root", str(project), "--request", str(request_path))
            if applied.returncode != 0:
                return f"case-apply collaborate-upsert command failed: {applied.stderr.strip()}"
            result = json.loads(applied.stdout)
            changed = result.get("changed_paths") if isinstance(result, dict) else None
            if not isinstance(changed, list) or not any(str(item).endswith("/live/collaborate.md") for item in changed):
                return "case-apply collaborate-upsert did not produce the case-v2 Collaborate checkpoint"

            checked = invoke("case-inspect", "--project-root", str(project))
            if checked.returncode != 0:
                return f"post-apply case-inspect failed: {checked.stderr.strip()}"
            final = json.loads(checked.stdout)
            active_cases = final.get("active_cases") if isinstance(final, dict) else None
            if not isinstance(active_cases, list) or not active_cases:
                return "case-inspect did not recover the active case-v2 Collaborate record"
        except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
            return f"transaction owner CLI probe failed: {exc}"
    return None


def _require_collaborate_transaction_cli(source: str, path: Path, source_path: str) -> None:
    failure = _collaborate_transaction_cli_probe(source)
    if failure is not None:
        raise EvalError(  # noqa: F405
            f"{display_path(path)}: bound producer {source_path} lacks a working case-inspect/case-schema/case-apply Collaborate transaction route: {failure}"
        )


@lru_cache(maxsize=16)
def _workflow_artifact_transaction_cli_probe(source: str) -> str | None:
    """Exercise the generic workflow artifact case-v2 transaction route end to end."""

    with tempfile.TemporaryDirectory(prefix="teamwork-case-artifact-probe-") as temporary:
        root = Path(temporary)
        script = root / "discussion-transaction.py"
        script.write_text(source, encoding="utf-8")
        project = root / "project"
        memory = project / "docs/teamwork"
        memory.mkdir(parents=True, exist_ok=True)
        index = {
            "schema_version": 2,
            "project": {
                "name": "Teamwork",
                "root": ".",
                "description": "Local Teamwork case-bundle index for this project.",
            },
            "active_cases": [],
            "claim_heads": {},
            "aliases": {},
            "recent_cases": [],
            "migration": None,
        }
        try:
            (memory / "index.json").write_text(
                json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        except OSError as exc:
            return f"cannot prepare case-v2 workflow artifact probe: {exc}"

        def invoke(*arguments: str) -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                [sys.executable, str(script), *arguments],
                cwd=root,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=10,
            )

        try:
            inspected = invoke("case-inspect", "--project-root", str(project))
            if inspected.returncode != 0:
                return f"case-inspect command failed: {inspected.stderr.strip()}"
            inspection = json.loads(inspected.stdout)
            revision = inspection.get("revision") if isinstance(inspection, dict) else None
            if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{64}", revision):
                return "case-inspect command did not return an opaque revision"

            schema = invoke("case-schema", "create")
            if schema.returncode != 0:
                return f"case-schema create command failed: {schema.stderr.strip()}"
            request = json.loads(schema.stdout)
            if not isinstance(request, dict) or request.get("operation") != "create":
                return "case-schema create did not return the create request skeleton"
            request.update(
                {
                    "expected_revision": revision,
                    "case_seed": "03" * 32,
                    "title": "Probe workflow artifact transaction",
                    "task_key": "probe-workflow-artifact",
                    "aliases": ["probe-workflow-artifact"],
                    "initial_phase": "planned",
                }
            )
            applied = invoke(
                "case-apply",
                "--project-root",
                str(project),
                "--request-json",
                json.dumps(request),
            )
            if applied.returncode != 0:
                return f"case-apply create command failed: {applied.stderr.strip()}"
            result = json.loads(applied.stdout)
            if not isinstance(result, dict) or result.get("schema_mode") != "case-v2":
                return "case-apply create did not produce a case-v2 result"
            case_id = result.get("case_id")
            manifest_revision = result.get("manifest_revision")
            revision = result.get("revision")
            if not all(isinstance(value, str) and value for value in (case_id, manifest_revision, revision)):
                return "case-apply create did not return case and revision identifiers"

            plan_schema = invoke("case-schema", "plan-upsert")
            if plan_schema.returncode != 0:
                return f"case-schema plan-upsert command failed: {plan_schema.stderr.strip()}"
            plan_request = json.loads(plan_schema.stdout)
            if not isinstance(plan_request, dict) or plan_request.get("operation") != "plan-upsert":
                return "case-schema plan-upsert did not return the plan request skeleton"
            plan_request.update(
                {
                    "expected_revision": revision,
                    "case_id": case_id,
                    "expected_manifest_revision": manifest_revision,
                    "source_digest": "04" * 32,
                    "body": "## Plan\n\n- Direct case-v2 workflow artifact transaction probe.",
                }
            )
            applied = invoke(
                "case-apply",
                "--project-root",
                str(project),
                "--request-json",
                json.dumps(plan_request),
            )
            if applied.returncode != 0:
                return f"case-apply plan-upsert command failed: {applied.stderr.strip()}"
            result = json.loads(applied.stdout)
            expected_path = f"docs/teamwork/cases/{case_id}/plan.md"
            changed = result.get("changed_paths") if isinstance(result, dict) else None
            if not isinstance(changed, list) or expected_path not in changed:
                return "case-apply plan-upsert did not produce the transaction-derived case plan path"

            checked = invoke("case-inspect", "--project-root", str(project))
            if checked.returncode != 0:
                return f"post-apply case-inspect failed: {checked.stderr.strip()}"
            final = json.loads(checked.stdout)
            active_cases = final.get("active_cases") if isinstance(final, dict) else None
            if not isinstance(active_cases, list) or not active_cases:
                return "case-inspect did not recover the active case-v2 workflow artifact"
            manifest = active_cases[0].get("state") if isinstance(active_cases[0], dict) else None
            artifacts = manifest.get("artifacts") if isinstance(manifest, dict) else None
            if not isinstance(artifacts, dict) or not any(
                isinstance(item, dict)
                and item.get("path") == expected_path
                and item.get("role") == "plan"
                for item in artifacts.values()
            ):
                return "case-inspect did not recover the transaction-owned case workflow registration"
        except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
            return f"case-v2 workflow artifact transaction owner CLI probe failed: {exc}"
    return None


def _require_workflow_artifact_transaction_cli(source: str, path: Path, source_path: str) -> None:
    failure = _workflow_artifact_transaction_cli_probe(source)
    if failure is not None:
        raise EvalError(  # noqa: F405
            f"{display_path(path)}: bound producer {source_path} lacks a working case-inspect/case-schema/case-apply workflow artifact transaction route: {failure}"
        )


def _role_from_source(source_path: str) -> str | None:
    for mapping in ROLE_TEMPLATE_PATHS.values():  # noqa: F405
        for role, candidate in mapping.items():
            if candidate == source_path:
                return role
    return None


ROLE_SOURCE_RULES: dict[str, list[tuple[str, ...]]] = {
    "researcher": [("sanitized",), ("private",), ("read-only",)],
    "explorer": [("local",), ("do not browse", "never browse"), ("read-only",)],
    "debugger": [("immutable",), ("same path",), ("authority",)],
    "designer": [
        ("genuine alternatives",),
        ("governing criteria",),
        ("direct evidence",),
        ("assumption/disconfirming-evidence challenge",),
        ("read-only",),
        ("decision",),
    ],
    "planner": [("selected direction",), ("execution-ready plan packet",), ("write authority: none",), ("do not implement",)],
    "worker": [("canonical",), ("suitable installed dependencies", "installed dependencies"), ("proportional",), ("residue",)],
    "writer": [
        ("standalone document", "independent document"),
        ("bounded writing brief",),
        ("reader-first",),
        ("preserve meaning",),
        ("do not research",),
        ("code-coupled",),
    ],
    "plan-reviewer": [("independently",), ("direct proof", "evidence", "proof"), ("read-only",)],
    "reviewer": [("correctness",), ("read-only",), ("direct evidence", "direct proof")],
}


def validate_bound_producer_sources(
    data: dict[str, Any],
    path: Path,
    source_overrides: dict[str, str] | None = None,
) -> None:
    """Bind case behavior to source semantics, not just a path that exists."""

    overrides = source_overrides or {}
    capability, scenario, _ = capability_key(data, path)
    for producer in data["producers"]:
        source_path = producer["source"]
        try:
            source = overrides[source_path] if source_path in overrides else (ROOT / source_path).read_text(encoding="utf-8")  # noqa: F405
        except OSError as exc:
            raise EvalError(f"{display_path(path)}: cannot read bound producer {source_path}: {exc}") from exc  # noqa: F405
        if producer["class"] == "skill":
            if source_path == DESIGN_ADVERSARIAL_REFERENCE_PATH:  # noqa: F405
                validate_design_adversarial_reference_contract(source)
            else:
                validate_skill_source_contract(Path(source_path).parent.name, source)
            if (capability, scenario) == ("ask", "latent-preference-collaborate"):
                _require_source_phrases(source, path, source_path, [
                    ("latent preferences and unformed intent",),
                    ("Only Root may activate",),
                    ("never starts Collaborate or asks",),
                ])
            readiness_skill_rules = {
                "reclass-research": [
                    ("Researcher never asks",),
                    ("exact gap",),
                    ("reclassification signal",),
                ],
                "reclass-explore": [
                    ("Explorer never asks",),
                    ("exact local-evidence gap",),
                    ("reclassification signal",),
                ],
                "reclass-debug": [
                    ("A leaf never asks directly",),
                    ("returns that exact gap",),
                    ("reclassification signal",),
                ],
                "reclass-plan": [
                    ("Planner never asks users",),
                    ("exact missing required value",),
                    ("reclassification signal",),
                ],
                "reclass-review": [
                    ("Reviewer and Plan Reviewer never ask",),
                    ("proof gap or ambiguity blocker",),
                    ("reclassification signal",),
                ],
                "reclass-goal": [
                    ("Root alone asks once",),
                    ("one active gap",),
                    ("reclassified to Collaborate",),
                ],
                "reclass-init": [
                    ("Explorer and Worker never ask",),
                    ("reclassify it to Collaborate",),
                    ("resumes the same Init workflow",),
                ],
                "reclass-update": [
                    ("Explorer and Worker never ask",),
                    ("reclassified to Collaborate",),
                    ("resumes the same Update workflow",),
                ],
            }
            if capability == "ask" and scenario in readiness_skill_rules:
                _require_source_phrases(
                    source, path, source_path, readiness_skill_rules[scenario]
                )
        elif producer["class"] == "root-policy":
            _require_source_phrases(source, path, source_path, [
                ("root alone asks",),
                ("produce the real requested result first", "result first"),
                ("ground claims",),
                ("preserve unrelated", "preserve dirty work"),
            ])
            if capability == "ask" and scenario not in {
                "discoverable-native", "required-input", "dialogue-native"
            }:
                _require_source_phrases(source, path, source_path, [
                    ("Inspect before asking",),
                    ("discoverable/safe/reversible -> act",),
                    ("one missing user value",),
                    ("then resume",),
                    ("unformed intent/preference -> Collaborate",),
                    ("Leaves return exact gap/reclassification",),
                    ("One asker/owner/gap",),
                    ("no repeats",),
                ])
            if (capability, scenario) == ("ask", "dialogue-native"):
                _require_source_phrases(source, path, source_path, [
                    ("Discuss/brainstorm/stress-test activates Collaborate",),
                    ("synthesis/tension/options plus", "contributes synthesis/tension/candidate space first", "contribute synthesis/tension/candidate-space/recommendation", "contribute synthesis/tension/options"),
                    ("one high-information question", "one useful question", "Ask only if feedback helps", "Ask only if useful"),
                    ("open prose", "open questions stay prose", "open questions use prose"),
                    ("host-native 2-3 finite choices", "host-native bounded surface"),
                    ("Challenge moves", "major public/installable/release/migration"),
                    ("explicit question-first", "explicit sustained question-first", "question-first"),
                    ("default-save only case-v2 Collaborate/Goal checkpoints",),
                ])
            if capability == "collaborate":
                _require_source_phrases(source, path, source_path, [
                    ("Discuss/brainstorm/stress-test activates Collaborate",),
                    ("dialogue|brainstorm",),
                    ("Challenge moves",),
                    ("Adversarial is challenge, not mode",),
                    ("Default one child",),
                    ("daily cap4",),
                    ("5-8 only for explicit adversarial/release with host support", "5-8 only explicit adversarial/release with host support", "5-8 only explicit adversarial/release with host-support"),
                    ("Unavailable role or unverified isolation = capability-blocked", "Unavailable role/isolation = capability-blocked"),
                    ("default-save only case-v2 Collaborate/Goal checkpoints",),
                    ("No legacy-v1 artifact/collaborate/goal write fallback", "no artifact/collaborate/goal/manual/report/"),
                ])
        elif producer["class"] == "role-template":
            role = _role_from_source(source_path)
            if role is None:
                raise EvalError(f"{display_path(path)}: unrecognized role producer {source_path}")  # noqa: F405
            role_contract = [
                ("mission:",), ("owned scope:",), ("verify:",),
                ("do not expand scope",), ("do not self-accept",),
                *ROLE_SOURCE_RULES[role],
            ]
            if role == "writer":
                role_contract.extend([
                    ("low-cost bounded disposable leaf",),
                    ("transaction inspect/cas/journal/atomic apply/readback",),
                ])
            _require_source_phrases(source, path, source_path, role_contract)
            if capability == "ask" and role in {
                "researcher", "explorer", "debugger", "planner", "worker",
                "reviewer", "plan-reviewer",
            }:
                readiness_role_contract = [
                    ("Readiness:",),
                    ("never ask",),
                    ("owner",),
                    ("scope",),
                    ("reclassification signal",),
                    ("Root",),
                ]
                if role in {"reviewer", "plan-reviewer"}:
                    readiness_role_contract.append(("closing evidence",))
                else:
                    readiness_role_contract.append(("resume condition",))
                _require_source_phrases(
                    source, path, source_path, readiness_role_contract
                )
            if capability == "research" and role == "researcher":
                _require_source_phrases(source, path, source_path, [
                    ("claim_map", "claim-map"),
                    ("active_gap", "active-gap"),
                    ("wave",),
                    ("evidence_delta", "evidence-delta"),
                    ("contradiction",),
                    ("not_found", "not-found"),
                    ("coverage_stop", "coverage-stop"),
                    ("lightest adequate lookup",),
                ])
        elif source_path == "scripts/discussion-transaction.py":
            if (capability, scenario) == ("persistence", "generic-artifact-writer"):
                _require_workflow_artifact_transaction_cli(source, path, source_path)
            else:
                _require_collaborate_transaction_cli(source, path, source_path)
        elif source_path == "scripts/init-project-files.py":
            _require_source_phrases(source, path, source_path, [
                ("-recover-init-transaction",), ("journal",), ("project-local",),
            ])
        elif source_path == "scripts/check-update.sh":
            _require_source_phrases(source, path, source_path, [
                ("readiness",), ("global",), ("profile",),
            ])
        if (capability, scenario) in {("native", "minimal-change"), ("native", "engineering-quality")}:
            if producer["class"] == "root-policy":
                _require_source_phrases(source, path, source_path, [
                    ("produce the real requested result first", "result first"),
                    ("current canonical owner", "canonical owner"),
                    ("focused automated regression evidence", "focused evidence"),
                    ("low-risk mechanical work", "low-risk docs", "full suites run only", "focused evidence"),
                    ("Default one child",),
                    ("daily cap4",),
                    ("5-8 only for explicit adversarial/release with host support", "5-8 only explicit adversarial/release with host support", "5-8 only explicit adversarial/release with host-support"),
                    ("Unavailable role or unverified isolation = capability-blocked", "Unavailable role/isolation = capability-blocked"),
                    ("preserve unrelated", "preserve dirty work"),
                    ("stop when the requested result", "stop when the result", "stop when result"),
                ])
                normalized_source = " ".join(source.casefold().split())
                if not any(
                    phrase in normalized_source
                    for phrase in ("do not add an unrequested wrapper", "avoid unrequested wrappers", "avoid wrappers/", "minimal logic")
                ):
                    raise EvalError(f"{display_path(path)}: Root producer lost the conditional wrapper/fallback rule")  # noqa: F405
            elif producer["class"] == "role-template":
                _require_source_phrases(source, path, source_path, [
                    ("canonical reuse", "canonical owner"),
                    ("built-ins or installed dependencies", "built-in", "installed dependency"),
                    ("proportional",),
                    ("preserve unrelated",),
                    ("remove instrumentation", "own residue"),
                    ("stop",),
                ])
        if (capability, scenario) == ("verification", "monotonic-evidence") and producer["class"] == "role-template":
            _require_source_phrases(source, path, source_path, [("read-only",), ("evidence",), ("accept",)])
        if capability == "research" and producer["class"] in {"root-policy", "skill"}:
            if producer["class"] == "root-policy":
                _require_source_phrases(source, path, source_path, [
                    ("Exact roles: Research->Researcher", "Named workflows: Research->Researcher"),
                    ("Default one child",),
                    ("daily cap4",),
                    ("5-8 only for explicit adversarial/release with host support", "5-8 only explicit adversarial/release with host support", "5-8 only explicit adversarial/release with host-support"),
                    ("Unavailable role or unverified isolation = capability-blocked", "Unavailable role/isolation = capability-blocked"),
                ])
            elif source_path == "skills/teamwork-research/SKILL.md":
                _require_source_phrases(source, path, source_path, [
                    ("Research -> Researcher",),
                    ("Root MUST NOT browse",),
                    ("Default to one Researcher",),
                    ("daily work stays within cap4",),
                    ("five to eight",),
                    ("bounded sanitized packet",),
                    ("`lookup`: one canonical or official source",),
                    ("claim_map", "claim-map"),
                    ("active_gap", "active-gap"),
                    ("evidence_delta", "evidence-delta"),
                    ("contradiction",),
                    ("coverage_stop", "coverage-stop"),
                ])
        if capability == "plan" and producer["class"] in {"skill", "role-template"}:
            _require_source_phrases(source, path, source_path, [("proof",)])
            if producer["class"] != "role-template" or _role_from_source(source_path) == "planner":
                _require_source_phrases(source, path, source_path, [("dependencies",)])
            if producer["class"] == "skill":
                _require_source_phrases(source, path, source_path, [("proof targets",), ("case-v2",), ("capability-blocked",)])
        if capability == "review" and (
            producer["class"] in {"root-policy", "skill"}
            or (
                producer["class"] == "role-template"
                and _role_from_source(source_path) in {"reviewer", "plan-reviewer"}
            )
        ):
            _require_source_phrases(source, path, source_path, [
                ("one repair batch", "one repair/delta", "repair batch/delta", "repair-batch/delta-recheck"),
                ("delta recheck", "delta-recheck"),
            ])
            if producer["class"] == "skill":
                _require_source_phrases(source, path, source_path, [("case-v2 review artifact",), ("unsupported", "support")])
        if capability == "goal" and producer["class"] == "skill":
            _require_source_phrases(source, path, source_path, [("case-v2 Goal",), ("strategy",), ("failure",), ("verification")])
        if capability in {"init", "update"} and producer["class"] in {"root-policy", "skill"}:
            if producer["class"] == "root-policy":
                _require_source_phrases(source, path, source_path, [
                    ("case-v2",),
                    ("capability-blocked",),
                ])
            else:
                _require_source_phrases(source, path, source_path, [
                    ("case-v2",),
                    ("capability-blocked",),
                    ("migrate --project-root <exact-project-root>",),
                    ("resume --project-root <exact-project-root>",),
                ])
        if capability == "persistence":
            if scenario == "normal-doc-writer" and producer["class"] == "role-template":
                _require_source_phrases(source, path, source_path, [
                    ("standalone document",),
                    ("bounded writing brief",),
                    ("unmanaged exact path",),
                    ("do not research",),
                    ("code-coupled",),
                ])
            elif scenario == "generic-artifact-writer":
                if producer["class"] == "root-policy":
                    _require_source_phrases(source, path, source_path, [
                        ("default-save reusable artifacts", "initialized writable projects default-save", "initialized writable named workflows default-save", "writable initialized projects default-save"),
                        ("frozen packet", "frozen packets", "frozen Writer packet"),
                        ("transaction",),
                        ("readback",),
                        ("no-files/off-record/read-only/no-writes override", "No-writes/no-files/off-record"),
                        ("deliver result, report unsaved/blocked", "deliver core result, report unsaved/blocked"),
                        ("no root/worker/strong-role fallback", "no Root/Worker/strong-role/named-method fallback", "no role/method fallback"),
                    ])
                elif producer["class"] == "skill":
                    _require_source_phrases(source, path, source_path, [
                        ("case-v2",),
                        ("case-inspect",),
                        ("case-schema <plan-upsert> -> case-apply -> case-inspect/readback",),
                        ("completion artifact",),
                        ("Plan approval does not authorize implementation, release",),
                        ("frozen",),
                        ("read back", "readback"),
                        ("no Planner, Root, or Worker fallback writes it",),
                    ])
                elif producer["class"] == "role-template":
                    _require_source_phrases(source, path, source_path, [
                        ("frozen bounded writing brief",),
                        ("completion companions",),
                        ("joins before claiming saved/durable",),
                        ("interruption before case-apply gives no durable claim",),
                        ("managed artifacts only through their exact case-v2 specialized transaction",),
                        ("case-schema <operation> -> case-apply/readback",),
                        ("v2 case bundle sinks", "v2 case-bundle", "case-v2 only"),
                        ("accept transaction-derived destination",),
                        ("read back", "readback"),
                        ("required transaction gate",),
                    ])
            elif scenario == "specialized-artifact-writer":
                if producer["class"] == "root-policy":
                    _require_source_phrases(source, path, source_path, [
                        ("default-save only case-v2 Collaborate/Goal checkpoints",),
                        ("frozen packet", "frozen packets", "frozen Writer packet"),
                        ("transaction",),
                        ("readback",),
                    ])
                elif producer["class"] == "skill":
                    _require_source_phrases(source, path, source_path, [
                        ("maintain one Collaborate checkpoint", "canonical current path", "defaults to a managed Collaborate checkpoint", "managed case-v2 Collaborate checkpoint"),
                        ("discussion-transaction.py collaborate-inspect", "discussion-transaction.py case-inspect"),
                        ("discussion-transaction.py collaborate-schema", "case-schema"),
                        ("discussion-transaction.py collaborate-apply", "case-apply"),
                        ("managed Collaborate checkpoint", "managed case-v2 Collaborate checkpoint"),
                        ("v2, the transaction derives", "v2 case-bundle", "In case-v2, Writer uses"),
                        ("readback",),
                        ("dispatches writer", "dispatch Writer", "Writer calls only the controlled transaction route"),
                        ("sole filesystem writer", "sole caller of managed artifact transactions", "no Root, Designer, Worker, Reviewer, direct/manual file"),
                    ])
                elif producer["class"] == "role-template":
                    _require_source_phrases(source, path, source_path, [
                        ("checkpoint artifacts",),
                        ("successful transaction readback",),
                        ("collaborate-inspect -> collaborate-schema <operation> -> collaborate-apply -> collaborate-inspect/readback", "case-schema <operation> -> case-apply/readback"),
                        ("legacy Discussion/Design=read-only sources, no write route", "legacy-v1 artifacts/collaborate/goal are read-only migration inputs, no write route"),
                        ("Goal=attempts/progress", "Goal=goal-acquire/goal-update/goal-transfer/goal-close"),
                        ("v2 case bundle sinks", "v2 case bundle", "case-v2 only"),
                        ("required transaction gate",),
                        ("accept transaction-derived destination",),
                    ])
            elif scenario == "negative-overrides":
                if producer["class"] == "root-policy":
                    _require_source_phrases(source, path, source_path, [
                        ("no-files/off-record/read-only/no-writes override", "No-writes/no-files/off-record"),
                        ("deliver result, report unsaved/blocked", "deliver core result, report unsaved/blocked"),
                        ("no root/worker/strong-role fallback", "no Root/Worker/strong-role/named-method fallback", "no role/method fallback"),
                    ])
                elif producer["class"] == "skill":
                    _require_source_phrases(source, path, source_path, [
                        ("no files",),
                        ("off-record",),
                        ("read-only",),
                        ("no writes",),
                        ("unsaved/blocked",),
                    ])
                elif producer["class"] == "role-template":
                    _require_source_phrases(source, path, source_path, [
                        ("blocked without writing",),
                        ("required transaction gate",),
                    ])
            elif scenario == "explore-no-artifact":
                if producer["class"] == "root-policy":
                    _require_source_phrases(source, path, source_path, [
                        ("explore, check-only work, tiny one-shots", "explore/check-only/tiny one-shots"),
                        ("create no standalone artifact", "ordinary explanations create none", "explanations create none"),
                    ])
                elif producer["class"] == "skill":
                    _require_source_phrases(source, path, source_path, [
                        ("do not create an explore report", "create a standalone artifact"),
                        ("evidence belongs in the workflow writing brief", "Evidence belongs in the workflow packet"),
                        ("writer never creates an independent explore artifact",),
                    ])
                elif producer["class"] == "role-template":
                    _require_source_phrases(source, path, source_path, [
                        ("read-only",),
                        ("write authority: none",),
                        ("standalone docs/artifacts require a bounded writing brief",),
                    ])
            elif scenario == "code-coupled-owner":
                if producer["class"] == "root-policy":
                    _require_source_phrases(source, path, source_path, [
                        ("code-coupled text implementer-owned", "code-coupled text stays implementer-owned"),
                    ])
                elif producer["class"] == "role-template" and _role_from_source(source_path) == "worker":
                    _require_source_phrases(source, path, source_path, [
                        ("owned scope",),
                        ("canonical reuse", "canonical owner"),
                        ("residue",),
                    ])
                elif producer["class"] == "role-template":
                    _require_source_phrases(source, path, source_path, [
                        ("do not write code, comments", "no code/comments"),
                        ("docstrings",),
                        ("tests",),
                        ("schemas",),
                        ("manifests",),
                        ("config",),
                    ])


def normalize_contract_key(value: str) -> str:
    return "-".join(value.strip().casefold().replace("_", "-").split())


def capability_key(data: dict[str, Any], path: Path) -> tuple[str, str, str]:
    expected = data["expected"]
    if not isinstance(expected, dict):
        raise EvalError(f"{display_path(path)}: expected must be an object")  # noqa: F405
    capability = require_string(expected.get("capability"), "expected.capability", path)
    scenario = require_string(expected.get("scenario"), "expected.scenario", path)
    language = require_string(expected.get("language"), "expected.language", path)
    if language not in {"en", "zh"}:
        raise EvalError(f"{display_path(path)}: expected.language must be en or zh")  # noqa: F405
    return capability, scenario, language


def validate_case(path: Path, known_rubrics: set[str]) -> dict[str, Any]:
    data = load_json(path)
    if not isinstance(data, dict):
        raise EvalError(f"{display_path(path)}: case must be a JSON object")  # noqa: F405
    missing = sorted(REQUIRED_CASE_FIELDS - set(data))  # noqa: F405
    if missing:
        raise EvalError(f"{display_path(path)}: missing required fields: {', '.join(missing)}")  # noqa: F405

    case_id = require_string(data["id"], "id", path)
    if not ID_RE.fullmatch(case_id):  # noqa: F405
        raise EvalError(f"{display_path(path)}: id must be kebab-case")  # noqa: F405
    split = require_string(data["split"], "split", path)
    if split not in SPLITS:  # noqa: F405
        raise EvalError(f"{display_path(path)}: split must be one of {sorted(SPLITS)}")  # noqa: F405
    expected_filename = f"{case_id}.{split}.v4.json"
    if path.name != expected_filename:
        raise EvalError(f"{display_path(path)}: active case filename must be {expected_filename}")  # noqa: F405

    source = require_string(data["source"], "source", path)
    if source not in SOURCES:  # noqa: F405
        raise EvalError(f"{display_path(path)}: source must be one of {sorted(SOURCES)}")  # noqa: F405
    platforms = require_string_list(data["platforms"], "platforms", path)
    if set(platforms) != PLATFORMS:  # noqa: F405
        raise EvalError(
            f"{display_path(path)}: capability cases must cover codex, cursor, and claude"
        )  # noqa: F405

    prompt = require_string(data["prompt"], "prompt", path)
    capability, scenario, _language = capability_key(data, path)
    requirement_key = (capability, scenario)
    if requirement_key not in CAPABILITY_REQUIREMENTS:  # noqa: F405
        raise EvalError(
            f"{display_path(path)}: unknown capability/scenario: {capability}/{scenario}"
        )  # noqa: F405
    validate_producers(data["producers"], path, requirement_key)
    validate_bound_producer_sources(data, path)
    requires = {
        normalize_contract_key(item)
        for item in require_string_list(data["expected"].get("requires"), "expected.requires", path)
    }
    missing_requirements = sorted(CAPABILITY_REQUIREMENTS[requirement_key] - requires)  # noqa: F405
    if missing_requirements:
        raise EvalError(
            f"{display_path(path)}: capability coverage missing: {', '.join(missing_requirements)}"
        )  # noqa: F405

    if requirement_key == ("native", "engineering-quality"):
        pair = data.get("pair")
        if not isinstance(pair, dict) or set(pair) != {"dimension", "positive", "negative"}:
            raise EvalError(
                f"{display_path(path)}: native engineering-quality case needs dimension/positive/negative pair"
            )  # noqa: F405
        dimension = require_string(pair["dimension"], "pair.dimension", path)
        if dimension not in NATIVE_QUALITY_PAIR_DIMENSIONS:  # noqa: F405
            raise EvalError(f"{display_path(path)}: unknown native pair dimension: {dimension}")  # noqa: F405
        require_string(pair["positive"], "pair.positive", path)
        require_string(pair["negative"], "pair.negative", path)

    must = require_string_list(data["must"], "must", path)
    must_not = require_string_list(data["must_not"], "must_not", path)
    combined_negative = " ".join(must_not).casefold()
    if "no-implementation" in requires and not any(
        term in combined_negative
        for term in ("implement", "edit", "change files", "实施", "实现", "修改")
    ):
        raise EvalError(
            f"{display_path(path)}: no-implementation contract needs an observable negative control"
        )  # noqa: F405
    if (capability, scenario) in {
        ("collaborate", "dialogue"),
        ("collaborate", "explicit-save"),
        ("collaborate", "persistence-boundary"),
    }:
        if not any(term in " ".join(must + must_not).casefold() for term in ("authority", "授权")):
            raise EvalError(
                f"{display_path(path)}: Collaborate boundary must preserve authority semantics"
            )  # noqa: F405
    if scenario == "privacy-boundary" and not any(
        term in combined_negative for term in ("secret", "credential", "sensitive", "秘密", "凭据", "敏感")
    ):
        raise EvalError(f"{display_path(path)}: privacy case needs a sensitive-data negative control")  # noqa: F405
    if (capability, scenario) == ("collaborate", "explicit-save") and "$teamwork-collaborate" not in prompt:
        raise EvalError(f"{display_path(path)}: explicit-save prompt must explicitly invoke $teamwork-collaborate")  # noqa: F405
    if (capability, scenario) == ("collaborate", "dialogue") and "$teamwork-collaborate" in prompt:
        raise EvalError(f"{display_path(path)}: natural dialogue control must not use $teamwork-collaborate")  # noqa: F405

    evidence = data["evidence"]
    if isinstance(evidence, str):
        evidence_items = [evidence]
    elif isinstance(evidence, list) and evidence and all(
        isinstance(item, str) and item.strip() for item in evidence
    ):
        evidence_items = evidence
    else:
        raise EvalError(f"{display_path(path)}: evidence must be a non-empty string or string list")  # noqa: F405
    if not any(
        "static" in item.casefold() or "静态" in item
        for item in evidence_items
    ):
        raise EvalError(
            f"{display_path(path)}: deterministic case must state its static-evidence limit"
        )  # noqa: F405

    rubric = data.get("rubric")
    if rubric is not None:
        rubric_id = require_string(rubric, "rubric", path)
        if rubric_id not in known_rubrics:
            raise EvalError(f"{display_path(path)}: unknown rubric: {rubric_id}")  # noqa: F405
    return data


def validate_rubrics() -> set[str]:
    if not RUBRIC_DIR.is_dir():  # noqa: F405
        raise EvalError("evals/teamwork/rubrics/ is missing")  # noqa: F405
    rubrics: set[str] = set()
    for path in sorted(RUBRIC_DIR.glob("*.json")):  # noqa: F405
        data = load_json(path)
        if not isinstance(data, dict):
            raise EvalError(f"{display_path(path)}: rubric must be a JSON object")  # noqa: F405
        rubric_id = require_string(data.get("id"), "id", path)
        if rubric_id in rubrics:
            raise EvalError(f"{display_path(path)}: duplicate rubric id: {rubric_id}")  # noqa: F405
        has_criteria = isinstance(data.get("criteria"), list) and bool(data["criteria"])
        has_dimensions = isinstance(data.get("dimensions"), list) and bool(data["dimensions"])
        if not has_criteria and not has_dimensions:
            raise EvalError(
                f"{display_path(path)}: rubric must define non-empty criteria or dimensions"
            )  # noqa: F405
        rubrics.add(rubric_id)
    if not rubrics:
        raise EvalError("no rubrics found")  # noqa: F405
    return rubrics


def require_evidence_path(value: Any, field: str, path: Path, index: int) -> str:
    item = require_string(value, field, path)
    if item == PLACEHOLDER:  # noqa: F405
        raise EvalError(f"{display_path(path)}:{index}: {field} must not be {PLACEHOLDER}")  # noqa: F405
    if not is_package_relative(item) or not (ROOT / item).exists():  # noqa: F405
        raise EvalError(f"{display_path(path)}:{index}: {field} path does not exist: {item}")  # noqa: F405
    return item


def validate_owned_files(items: list[str], path: Path, index: int) -> None:
    for item in items:
        if item == PLACEHOLDER or not is_package_relative(item):  # noqa: F405
            raise EvalError(f"{display_path(path)}:{index}: invalid owned_files entry: {item}")  # noqa: F405
        if not is_glob_like(item) and not (ROOT / item).exists():  # noqa: F405
            raise EvalError(f"{display_path(path)}:{index}: owned_files path does not exist: {item}")  # noqa: F405


def validate_optimizer_candidate_entry(data: dict[str, Any], path: Path, index: int) -> None:
    kind = require_string(data.get("kind"), "kind", path)
    if kind not in OPTIMIZER_KINDS:  # noqa: F405
        raise EvalError(f"{display_path(path)}:{index}: kind must be one of {sorted(OPTIMIZER_KINDS)}")  # noqa: F405
    gate = require_string(data.get("gate_decision"), "gate_decision", path)
    if gate not in OPTIMIZER_GATE_DECISIONS:  # noqa: F405
        raise EvalError(f"{display_path(path)}:{index}: invalid gate_decision")  # noqa: F405
    decision = require_string(data.get("decision"), "decision", path)
    if decision not in OPTIMIZER_DECISIONS:  # noqa: F405
        raise EvalError(f"{display_path(path)}:{index}: invalid decision")  # noqa: F405
    for field in ("provider", "model", "model_config", "release_audit", "reviewer"):
        item = require_string(data.get(field), field, path)
        if item == PLACEHOLDER:  # noqa: F405
            raise EvalError(f"{display_path(path)}:{index}: {field} must not be {PLACEHOLDER}")  # noqa: F405
    for field in ("prompt_or_template", "baseline", "treatment", "rollback"):
        require_evidence_path(data.get(field), field, path, index)
    validate_owned_files(require_string_list(data.get("owned_files"), "owned_files", path), path, index)
    require_string_list(data.get("denylist"), "denylist", path)
    validation = require_string_list(data.get("validation"), "validation", path)
    if all(item == PLACEHOLDER for item in validation):  # noqa: F405
        raise EvalError(f"{display_path(path)}:{index}: validation must include real evidence")  # noqa: F405


def validate_ledger_lines(path: Path, name: str, required_fields: set[str]) -> int:
    if not path.is_file():
        raise EvalError(f"missing ledger: {display_path(path)}")  # noqa: F405
    entries: list[dict[str, Any]] = []
    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError as exc:
            raise EvalError(f"{display_path(path)}:{index}: invalid JSONL: {exc}") from exc  # noqa: F405
        if not isinstance(data, dict):
            raise EvalError(f"{display_path(path)}:{index}: ledger entry must be an object")  # noqa: F405
        require_string(data.get("date"), "date", path)
        missing = sorted(required_fields - set(data))
        if missing:
            raise EvalError(f"{display_path(path)}:{index}: missing ledger fields: {', '.join(missing)}")  # noqa: F405
        if name == "optimizer-candidates.jsonl":
            validate_optimizer_candidate_entry(data, path, index)
        entries.append(data)
    if not entries:
        raise EvalError(f"{display_path(path)}: ledger must not be empty")  # noqa: F405
    if name == "accepted.jsonl":
        try:
            validate_accepted_ledger_v2(entries)
        except SemanticReviewError as exc:
            raise EvalError(f"{display_path(path)}: {exc}") from exc  # noqa: F405
    return len(entries)


def validate_ledgers() -> int:
    if not LEDGER_DIR.is_dir():  # noqa: F405
        raise EvalError("evals/teamwork/ledgers/ is missing")  # noqa: F405
    count = 0
    for name, fields in sorted(LEDGER_SCHEMAS.items()):  # noqa: F405
        path = LEDGER_DIR / name  # noqa: F405
        if name == "optimizer-candidates.jsonl" and not path.exists():
            continue
        count += validate_ledger_lines(path, name, fields)
    return count


def _validate_coverage(cases: list[dict[str, Any]]) -> None:
    observed_by_split: dict[str, set[tuple[str, str, str]]] = {split: set() for split in SPLITS}  # noqa: F405
    for case in cases:
        observed_by_split[case["split"]].add(capability_key(case, CASE_DIR / "<loaded>"))  # noqa: F405
    missing_dev = sorted(DEV_CAPABILITY_COVERAGE - observed_by_split["dev"])  # noqa: F405
    if missing_dev:
        raise EvalError(f"missing dev capability coverage: {missing_dev}")  # noqa: F405
    missing_release = sorted(RELEASE_CAPABILITY_COVERAGE - observed_by_split["release"])  # noqa: F405
    if missing_release:
        raise EvalError(f"missing release capability coverage: {missing_release}")  # noqa: F405
    dimensions = {
        case["pair"]["dimension"]
        for case in cases
        if capability_key(case, CASE_DIR / "<loaded>")[:2] == ("native", "engineering-quality")  # noqa: F405
    }
    missing_dimensions = sorted(NATIVE_QUALITY_PAIR_DIMENSIONS - dimensions)  # noqa: F405
    if missing_dimensions:
        raise EvalError(f"missing native engineering-quality pairs: {missing_dimensions}")  # noqa: F405


def selected_cases(selection: str) -> list[dict[str, Any]]:
    validate_semantic_sources()
    if not CASE_DIR.is_dir():  # noqa: F405
        raise EvalError("evals/teamwork/cases/ is missing")  # noqa: F405
    known_rubrics = validate_rubrics()
    validate_ledgers()
    cases = [validate_case(path, known_rubrics) for path in sorted(CASE_DIR.glob("*.v4.json"))]  # noqa: F405
    if not cases:
        raise EvalError("no active v4 cases found")  # noqa: F405
    ids = [case["id"] for case in cases]
    duplicates = sorted({case_id for case_id in ids if ids.count(case_id) > 1})
    if duplicates:
        raise EvalError(f"duplicate case id: {', '.join(duplicates)}")  # noqa: F405
    _validate_coverage(cases)
    selected = cases if selection == "all" else [case for case in cases if case["split"] == selection]
    if not selected:
        raise EvalError(f"split {selection!r} has no cases")  # noqa: F405
    return selected
