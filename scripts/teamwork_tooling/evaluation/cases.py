"""Eval case, rubric, and ledger validation."""

from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
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


@lru_cache(maxsize=16)
def _discussion_transaction_cli_probe(source: str) -> str | None:
    """Exercise the owner CLI rather than freezing a parser implementation detail."""

    with tempfile.TemporaryDirectory(prefix="teamwork-discussion-probe-") as temporary:
        root = Path(temporary)
        script = root / "discussion-transaction.py"
        script.write_text(source, encoding="utf-8")
        project = root / "project"
        memory = project / "docs/teamwork"
        memory.mkdir(parents=True)
        for name in ("index.json", "current.md", "README.md"):
            template = ROOT / "templates/teamwork-memory" / name  # noqa: F405
            try:
                (memory / name).write_bytes(template.read_bytes())
            except OSError as exc:
                return f"cannot prepare transaction probe: {exc}"

        def invoke(*arguments: str) -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                [sys.executable, str(script), *arguments], cwd=root, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, timeout=10,
            )

        try:
            inspected = invoke("inspect", "--project-root", str(project))
            if inspected.returncode != 0:
                return f"inspect command failed: {inspected.stderr.strip()}"
            inspection = json.loads(inspected.stdout)
            revision = inspection.get("revision") if isinstance(inspection, dict) else None
            if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{64}", revision):
                return "inspect command did not return an opaque revision"

            schema = invoke("schema", "create")
            if schema.returncode != 0:
                return f"schema command failed: {schema.stderr.strip()}"
            skeleton = json.loads(schema.stdout)
            if not isinstance(skeleton, dict) or skeleton.get("operation") != "create" or "expected_revision" not in skeleton:
                return "schema command did not return the create request skeleton"

            request = skeleton
            request["expected_revision"] = revision
            record = request["record"]
            record.update(
                {
                    "slug": "probe-decision",
                    "title": "Probe transaction ownership",
                    "updated": "2026-07-19",
                    "goal": "Verify the public transaction route.",
                    "current_branch": "Run the owner CLI directly.",
                    "return_path": "Resume through inspect.",
                    "blockers": ["none"],
                    "convergence": "The owned current artifact exists.",
                    "key_evidence": ["CLI probe output."],
                }
            )
            if record.get("schema_version") == 2:
                record["frontier"] = [
                    {
                        "id": "Q1",
                        "title": "Apply owner",
                        "level": "goal",
                        "status": "current",
                        "prompt": "Should apply own the persisted write?",
                        "options": [
                            {
                                "id": "managed",
                                "label": "Managed route",
                                "tradeoff": "Keeps transaction ownership explicit.",
                            },
                            {
                                "id": "direct",
                                "label": "Direct route",
                                "tradeoff": "Would bypass the owner and must be rejected.",
                            },
                        ],
                        "recommendation": "managed",
                        "largest_downside": "The probe is narrower than a full discussion lifecycle.",
                        "why_critical": "The answer proves which path owns writes.",
                        "blocks": ["transaction ownership"],
                        "depends_on": [],
                        "closure_signal": "The managed apply produces the active discussion.",
                        "resolution": None,
                    }
                ]
                record["current_batch"] = ["Q1"]
            else:
                record["settled"] = ["The parser route is executable."]
                record["still_open"] = ["Does apply own the write?"]
            applied = invoke(
                "apply", "--project-root", str(project), "--request-json", json.dumps(request),
            )
            if applied.returncode != 0:
                return f"apply command failed: {applied.stderr.strip()}"
            result = json.loads(applied.stdout)
            if not isinstance(result, dict) or result.get("path") != "docs/teamwork/discussion/current.md":
                return "apply command did not produce the transaction-owned active discussion"

            checked = invoke("inspect", "--project-root", str(project))
            if checked.returncode != 0:
                return f"post-apply inspect failed: {checked.stderr.strip()}"
            final = json.loads(checked.stdout)
            active = final.get("active") if isinstance(final, dict) else None
            if not isinstance(active, dict) or active.get("path") != "docs/teamwork/discussion/current.md":
                return "inspect command did not recover the transaction-owned active discussion"
        except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
            return f"transaction owner CLI probe failed: {exc}"
    return None


def _require_discussion_transaction_cli(source: str, path: Path, source_path: str) -> None:
    failure = _discussion_transaction_cli_probe(source)
    if failure is not None:
        raise EvalError(  # noqa: F405
            f"{display_path(path)}: bound producer {source_path} lacks a working inspect/schema/apply transaction route: {failure}"
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
    "designer": [("genuine alternatives",), ("read-only",), ("decision",)],
    "planner": [("selected direction",), ("single exact plan path", "one single exact plan path"), ("do not implement",)],
    "worker": [("canonical",), ("proportional",), ("residue",)],
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
        elif producer["class"] == "root-policy":
            _require_source_phrases(source, path, source_path, [
                ("root alone asks",),
                ("produce the real requested result first",),
                ("ground claims",),
                ("preserve unrelated",),
            ])
        elif producer["class"] == "role-template":
            role = _role_from_source(source_path)
            if role is None:
                raise EvalError(f"{display_path(path)}: unrecognized role producer {source_path}")  # noqa: F405
            _require_source_phrases(source, path, source_path, [
                ("mission:",), ("owned scope:",), ("verify:",),
                ("do not expand scope",), ("do not self-accept",),
                *ROLE_SOURCE_RULES[role],
            ])
        elif source_path == "scripts/discussion-transaction.py":
            _require_discussion_transaction_cli(source, path, source_path)
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
                    ("produce the real requested result first",),
                    ("current canonical owner", "canonical owner"),
                    ("focused automated regression evidence",),
                    ("low-risk mechanical work", "low-risk docs"),
                    ("preserve unrelated",),
                    ("stop when the requested result",),
                ])
                if "do not add an unrequested wrapper" not in " ".join(source.casefold().split()):
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
    if scenario in {"natural-question-first", "explicit-save", "persistence-boundary"}:
        if not any(term in " ".join(must + must_not).casefold() for term in ("authority", "授权")):
            raise EvalError(
                f"{display_path(path)}: Grill boundary must preserve authority semantics"
            )  # noqa: F405
    if scenario == "privacy-boundary" and not any(
        term in combined_negative for term in ("secret", "credential", "sensitive", "秘密", "凭据", "敏感")
    ):
        raise EvalError(f"{display_path(path)}: privacy case needs a sensitive-data negative control")  # noqa: F405
    if scenario == "explicit-save" and "$grill-me" not in prompt:
        raise EvalError(f"{display_path(path)}: explicit-save prompt must explicitly invoke $grill-me")  # noqa: F405
    if scenario == "natural-question-first" and "$grill-me" in prompt:
        raise EvalError(f"{display_path(path)}: natural question-first control must not use $grill-me")  # noqa: F405

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
