#!/usr/bin/env python3
"""Probe Codex app-server request_user_input transport without scoring prose."""

from __future__ import annotations

import argparse
import hashlib
import json
import queue
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


SCENARIOS = {
    "collaborate_bounded_native_request": {
        "expected_requests": 1,
        "max_questions_per_request": 3,
        "forbid_text_question": True,
        "prompt": (
            "Collaborate on this public CLI rename with me. Existing scripts either keep "
            "working through an alias or break at the next major release; those are "
            "the only genuine choices. Give the synthesis, tradeoff, and recommendation "
            "first, then ask the bounded choice through the native question surface."
        ),
    },
    "open_brainstorm_prose_question": {
        "expected_requests": 0,
        "require_text_question": True,
        "prompt": (
            "Brainstorm ways to make a developer tool feel easier to adopt. Widen the "
            "candidate space, synthesize the main tension, recommend the next-best option, "
            "then ask one genuinely open steering question in prose. Do not turn it into "
            "invented finite choices."
        ),
    },
    "collaborate_checkpoint_persistence": {
        "expected_requests": 0,
        "require_text_question": True,
        "sandbox": "workspace-write",
        "require_collaborate_checkpoint": True,
        "prompt": (
            "Let's think this through together over several turns. We need to make a "
            "public developer tool easier to adopt without increasing maintenance cost. "
            "Build a substantive synthesis, central tension, and recommendation, persist "
            "the Collaborate checkpoint through Writer plus transaction readback, then ask "
            "one genuinely open steering question so we can continue."
        ),
    },
    "explicit-grill-independent-batch": {
        "expected_requests": 1,
        "max_questions_per_request": 3,
        "forbid_text_question": True,
        "prompt": (
            "Collaborate in grill mode before changing this public SDK. Compatibility horizon, "
            "telemetry default, and deprecation messaging are all material and "
            "independent: no answer changes another question's options. Ask them "
            "as one global-only bounded native batch with stable ids, after a recommendation."
        ),
    },
    "explicit-grill-dependent-sequence": {
        "expected_requests": 3,
        "max_questions_per_request": 1,
        "forbid_text_question": True,
        "prompts": [
            (
                "Collaborate in grill mode before changing this public SDK. Start at the "
                "global layer: first decide whether compatibility is required. Only that "
                "answer determines valid boundary options, so ask only that prerequisite."
            ),
            (
                "The global compatibility answer is resolved and checkpointed. Continue at "
                "the boundary layer and ask only the dependent rollout-window decision."
            ),
            (
                "The boundary rollout-window answer is resolved and checkpointed. Continue "
                "at the detail layer and ask only the now-valid messaging detail."
            ),
        ],
        "expected_question_key_order": ["global_compatibility", "boundary_rollout", "detail_messaging"],
    },
}


class ProtocolError(RuntimeError):
    pass


def developer_instructions_for_scenario(scenario: str) -> str:
    if SCENARIOS[scenario].get("sandbox") == "workspace-write":
        return (
            "This is an isolated workspace behavior observation. Follow the user request "
            "and installed project instructions. Do not change implementation files or "
            "perform external actions."
        )
    return (
        "This is a read-only behavior observation. Follow the user request without "
        "editing files or performing external actions."
    )


def collaboration_mode_for_scenario(
    scenario: str,
    *,
    model: str,
    effort: str,
) -> dict[str, Any]:
    mode = "plan" if int(SCENARIOS[scenario]["expected_requests"]) else "default"
    return {
        "mode": mode,
        "settings": {
            "model": model,
            "reasoning_effort": effort,
            "developer_instructions": developer_instructions_for_scenario(scenario),
        },
    }


def collaborate_checkpoint_digest(root: Path) -> str:
    path = root / "docs" / "teamwork" / "collaborate" / "current.md"
    try:
        content = path.read_bytes()
    except OSError as exc:
        raise ProtocolError("managed Collaborate checkpoint was not created") from exc
    required = (
        b"Artifact Type: collaborate",
        b"Schema Version: 1",
        b'"schema_version": 1',
    )
    if not all(marker in content for marker in required):
        raise ProtocolError("managed Collaborate checkpoint is not a canonical v1 record")
    return hashlib.sha256(content).hexdigest()


def forbidden_generic_collaborate_artifacts(root: Path) -> list[str]:
    forbidden_roots = (
        root / "docs" / "teamwork" / "workflows" / "conclusion",
        root / "docs" / "teamwork" / "workflows" / "collaborate",
        root / "docs" / "teamwork" / "workflows" / "execution",
    )
    return sorted(
        path.relative_to(root).as_posix()
        for directory in forbidden_roots
        if directory.exists()
        for path in directory.rglob("*")
        if path.is_file()
    )


def validate_request_params(
    params: Any,
    *,
    expected_thread_id: str | None = None,
    expected_turn_id: str | None = None,
    existing_request_count: int = 0,
    expected_request_count: int = 1,
    max_questions_per_request: int = 3,
    allow_auto_resolution: bool = False,
) -> list[str]:
    """Validate only the callable transport shape, not decision semantics or IDs."""

    if not isinstance(params, dict):
        return ["params must be an object"]

    errors: list[str] = []
    for name in ("itemId", "threadId", "turnId"):
        if not isinstance(params.get(name), str) or not params[name]:
            errors.append(f"{name} must be a non-empty string")
    if expected_thread_id is not None and params.get("threadId") != expected_thread_id:
        errors.append("threadId does not match the active thread")
    if expected_turn_id is not None and params.get("turnId") != expected_turn_id:
        errors.append("turnId does not match the active turn")
    if existing_request_count >= expected_request_count:
        errors.append("request_user_input exceeds the bounded scenario count")
    if not allow_auto_resolution and params.get("autoResolutionMs") is not None:
        errors.append("autoResolutionMs must be omitted for a material decision")

    questions = params.get("questions")
    if not isinstance(questions, list) or not 1 <= len(questions) <= max_questions_per_request:
        return errors + [
            f"questions must contain one to {max_questions_per_request} items"
        ]

    for index, question in enumerate(questions, 1):
        prefix = f"questions[{index}]"
        if not isinstance(question, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for name in ("id", "header", "question"):
            if not isinstance(question.get(name), str) or not question[name].strip():
                errors.append(f"{prefix}.{name} must be a non-empty string")
        if question.get("isSecret") is True:
            errors.append(f"{prefix} must not collect credential contents")
        options = question.get("options")
        if not isinstance(options, list) or not 2 <= len(options) <= 3:
            errors.append(f"{prefix}.options must contain two or three items")
            continue
        labels: list[str] = []
        for option_index, option in enumerate(options, 1):
            option_prefix = f"{prefix}.options[{option_index}]"
            if not isinstance(option, dict):
                errors.append(f"{option_prefix} must be an object")
                continue
            label = option.get("label")
            description = option.get("description")
            if not isinstance(label, str) or not label.strip():
                errors.append(f"{option_prefix}.label must be non-empty")
            else:
                labels.append(label)
            if not isinstance(description, str) or not description.strip():
                errors.append(f"{option_prefix}.description must be non-empty")
        if len(labels) != len(set(labels)):
            errors.append(f"{prefix}.options labels must be unique")
    return errors


def response_for_request(params: dict[str, Any], answer: str | None = None) -> dict[str, Any]:
    answers: dict[str, dict[str, list[str]]] = {}
    for question in params["questions"]:
        selected = answer or question["options"][0]["label"]
        answers[question["id"]] = {"answers": [selected]}
    return {"answers": answers}


@dataclass
class AppServerProbe:
    command: list[str]
    cwd: Path
    model: str
    effort: str
    timeout_seconds: int
    scenario: str = "collaborate_bounded_native_request"
    review_path: Path | None = None
    events: list[str] = field(default_factory=list)
    observed_item_ids: list[str] = field(default_factory=list)
    observed_question_keys: list[str] = field(default_factory=list)
    observed_turn_ids: list[str] = field(default_factory=list)
    returned_answer_keys: list[str] = field(default_factory=list)
    native_question_sha256: list[str] = field(default_factory=list)
    rejected_native_question_sha256: list[str] = field(default_factory=list)
    agent_message_sha256: list[str] = field(default_factory=list)
    agent_message_count: int = 0
    text_question_observed: bool = False
    collaborate_checkpoint_sha256: str | None = None
    generic_collaborate_artifacts: list[str] = field(default_factory=list)
    _process: subprocess.Popen[str] | None = field(default=None, init=False)
    _messages: queue.Queue[dict[str, Any]] = field(default_factory=queue.Queue, init=False)
    _next_id: int = field(default=1, init=False)
    _server_request_ids: set[str | int] = field(default_factory=set, init=False)

    def _start(self) -> None:
        self._process = subprocess.Popen(
            self.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
            cwd=self.cwd,
        )
        assert self._process.stdout

        def read_stdout() -> None:
            for line in self._process.stdout:
                try:
                    value = json.loads(line)
                except json.JSONDecodeError:
                    self._messages.put({"_invalid": True})
                else:
                    self._messages.put(value if isinstance(value, dict) else {"_invalid": True})

        threading.Thread(target=read_stdout, daemon=True).start()

    def _send(self, value: dict[str, Any]) -> None:
        if self._process is None or self._process.stdin is None:
            raise ProtocolError("app-server stdin is unavailable")
        self._process.stdin.write(json.dumps(value, separators=(",", ":")) + "\n")
        self._process.stdin.flush()

    def _next_message(self, timeout: float | None = None) -> dict[str, Any]:
        try:
            message = self._messages.get(timeout=timeout or self.timeout_seconds)
        except queue.Empty as exc:
            raise ProtocolError("app-server lifecycle timed out") from exc
        if message.get("_invalid"):
            raise ProtocolError("app-server emitted non-JSON output")
        return message

    def _request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        request_id = self._next_id
        self._next_id += 1
        self._send({"id": request_id, "method": method, "params": params})
        while True:
            message = self._next_message()
            if message.get("id") == request_id and "error" in message:
                raise ProtocolError(f"{method} failed: {message['error']}")
            if message.get("id") == request_id and isinstance(message.get("result"), dict):
                return message["result"]
            if message.get("method") == "item/tool/requestUserInput":
                raise ProtocolError(f"request_user_input arrived before {method} completed")

    @staticmethod
    def _id(result: dict[str, Any], key: str) -> str:
        value = result.get(key)
        value = value.get("id") if isinstance(value, dict) else None
        if not isinstance(value, str) or not value:
            raise ProtocolError(f"{key}/start did not return {key}.id")
        return value

    def _write_review(self, label: str, value: Any) -> None:
        if self.review_path is None:
            return
        self.review_path.parent.mkdir(parents=True, exist_ok=True)
        rendered = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2)
        with self.review_path.open("a", encoding="utf-8") as review:
            review.write(f"[{label}]\n{rendered}\n[/{label}]\n")

    def _handle_user_input(
        self,
        message: dict[str, Any],
        *,
        thread_id: str,
        turn_id: str,
        expected_count: int,
        max_questions_per_request: int,
        allow_auto_resolution: bool,
    ) -> bool:
        if message.get("method") != "item/tool/requestUserInput":
            return False
        params = message.get("params")
        errors = validate_request_params(
            params,
            expected_thread_id=thread_id,
            expected_turn_id=turn_id,
            existing_request_count=len(self._server_request_ids),
            expected_request_count=expected_count,
            max_questions_per_request=max_questions_per_request,
            allow_auto_resolution=allow_auto_resolution,
        )
        questions = params.get("questions") if isinstance(params, dict) else None
        question_json = json.dumps(questions, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(question_json.encode()).hexdigest()
        if errors:
            self.rejected_native_question_sha256.append(digest)
            self._write_review("rejected native request_user_input", questions)
            raise ProtocolError("invalid request_user_input params: " + "; ".join(errors))
        request_id = message.get("id")
        if not isinstance(request_id, (str, int)) or request_id in self._server_request_ids:
            raise ProtocolError("request_user_input lacks a unique request id")
        assert isinstance(params, dict) and isinstance(questions, list)
        self._server_request_ids.add(request_id)
        self.observed_item_ids.append(params["itemId"])
        self.observed_turn_ids.append(params["turnId"])
        self.observed_question_keys.extend(question["id"] for question in questions)
        self.native_question_sha256.append(digest)
        self._write_review("native request_user_input", questions)
        response = response_for_request(params)
        self.returned_answer_keys.extend(response["answers"])
        self._send({"id": request_id, "result": response})
        self.events.append("item/tool/requestUserInput")
        return True

    def snapshot(self, *, status: str, blocker: str | None = None,
                 resolved_request_count: int = 0) -> dict[str, Any]:
        result: dict[str, Any] = {
            "status": status,
            "scenario": self.scenario,
            "model": self.model,
            "effort": self.effort,
            "collaboration_mode": collaboration_mode_for_scenario(
                self.scenario,
                model=self.model,
                effort=self.effort,
            )["mode"],
            "events": self.events,
            "observed_item_ids": self.observed_item_ids,
            "observed_question_keys": self.observed_question_keys,
            "observed_turn_ids": self.observed_turn_ids,
            "returned_answer_keys": self.returned_answer_keys,
            "resolved_request_count": resolved_request_count,
            "native_question_sha256": self.native_question_sha256,
            "rejected_native_question_sha256": self.rejected_native_question_sha256,
            "agent_message_sha256": self.agent_message_sha256,
            "agent_message_count": self.agent_message_count,
            "text_question_observed": self.text_question_observed,
            "collaborate_checkpoint_sha256": self.collaborate_checkpoint_sha256,
            "generic_collaborate_artifacts": self.generic_collaborate_artifacts,
            "semantic_quality": "not_evaluated",
        }
        if blocker is not None:
            result["blocker"] = blocker
        return result

    def run_once(self) -> dict[str, Any]:
        spec = SCENARIOS[self.scenario]
        expected_count = int(spec["expected_requests"])
        prompts = spec.get("prompts") or [spec["prompt"]]
        if not isinstance(prompts, list) or not prompts:
            raise ProtocolError("scenario prompts must be a non-empty list")
        self._start()
        resolved_ids: set[str | int] = set()
        try:
            self._request(
                "initialize",
                {"clientInfo": {"name": "teamwork-user-input-probe", "version": "1"},
                 "capabilities": {"experimentalApi": True}},
            )
            self.events.append("initialize")
            self._send({"method": "initialized", "params": {}})
            self.events.append("initialized")
            thread = self._request(
                "thread/start",
                {
                    "cwd": str(self.cwd),
                    "model": self.model,
                    "approvalPolicy": "never",
                    "sandbox": str(spec.get("sandbox", "read-only")),
                    "ephemeral": True,
                    "serviceName": "teamwork_user_input_probe",
                },
            )
            thread_id = self._id(thread, "thread")
            self.events.append("thread/start")
            for prompt in prompts:
                turn = self._request(
                    "turn/start",
                    {
                        "threadId": thread_id,
                        "effort": self.effort,
                        "collaborationMode": collaboration_mode_for_scenario(
                            self.scenario,
                            model=self.model,
                            effort=self.effort,
                        ),
                        "input": [{"type": "text", "text": str(prompt)}],
                    },
                )
                turn_id = self._id(turn, "turn")
                self.events.append("turn/start")

                completed = False
                deadline = time.monotonic() + self.timeout_seconds
                while time.monotonic() < deadline and not completed:
                    try:
                        message = self._next_message(max(0.01, deadline - time.monotonic()))
                    except ProtocolError as exc:
                        if "timed out" in str(exc):
                            break
                        raise
                    if self._handle_user_input(
                        message,
                        thread_id=thread_id,
                        turn_id=turn_id,
                        expected_count=expected_count,
                        max_questions_per_request=int(
                            spec.get("max_questions_per_request", 3)
                        ),
                        allow_auto_resolution=bool(spec.get("allow_auto_resolution")),
                    ):
                        continue
                    if message.get("method") == "serverRequest/resolved":
                        params = message.get("params")
                        if (
                            not isinstance(params, dict)
                            or params.get("threadId") != thread_id
                            or params.get("requestId") not in self._server_request_ids
                            or params["requestId"] in resolved_ids
                        ):
                            raise ProtocolError("serverRequest/resolved does not match one native request")
                        resolved_ids.add(params["requestId"])
                        self.events.append("serverRequest/resolved")
                        continue
                    if message.get("method") == "item/completed":
                        params = message.get("params")
                        item = params.get("item") if isinstance(params, dict) else None
                        if (
                            isinstance(params, dict)
                            and params.get("threadId") == thread_id
                            and params.get("turnId") == turn_id
                            and isinstance(item, dict)
                            and item.get("type") == "agentMessage"
                            and isinstance(item.get("text"), str)
                        ):
                            text = item["text"]
                            self.agent_message_count += 1
                            self.agent_message_sha256.append(hashlib.sha256(text.encode()).hexdigest())
                            self._write_review("assistant item", text)
                            if "?" in text or "？" in text:
                                self.text_question_observed = True
                        continue
                    if message.get("method") == "turn/completed":
                        params = message.get("params")
                        done = params.get("turn") if isinstance(params, dict) else None
                        if (
                            not isinstance(params, dict)
                            or params.get("threadId") != thread_id
                            or not isinstance(done, dict)
                            or done.get("id") != turn_id
                        ):
                            self.events.append("turn/completed")
                            raise ProtocolError("turn/completed does not match the active turn")
                        self.events.append("turn/completed")
                        status = done.get("status")
                        if status != "completed":
                            error = done.get("error")
                            detail = ""
                            if isinstance(error, dict) and isinstance(error.get("message"), str):
                                detail = f": {error['message']}"
                            raise ProtocolError(f"turn completed with status {status!r}{detail}")
                        completed = True

                if not completed:
                    raise ProtocolError("turn did not complete")

            expected_keys = spec.get("expected_question_key_order")
            if expected_keys is not None and self.observed_question_keys != expected_keys:
                raise ProtocolError("native question keys do not match expected dependency order")
            if spec.get("require_collaborate_checkpoint"):
                self.collaborate_checkpoint_sha256 = collaborate_checkpoint_digest(
                    self.cwd
                )
                self.generic_collaborate_artifacts = (
                    forbidden_generic_collaborate_artifacts(self.cwd)
                )
                if self.generic_collaborate_artifacts:
                    raise ProtocolError(
                        "Collaborate was duplicated through a generic artifact route"
                    )
            if len(self._server_request_ids) != expected_count:
                raise ProtocolError(f"expected exactly {expected_count} request_user_input events")
            if len(resolved_ids) != expected_count:
                raise ProtocolError("not every request_user_input was resolved")
            if self.returned_answer_keys != self.observed_question_keys:
                raise ProtocolError("answer keys do not match observed question ids in order")
            if spec.get("forbid_text_question") and self.text_question_observed:
                raise ProtocolError("assistant duplicated the native prompt as a text question")
            if spec.get("require_text_question") and not self.text_question_observed:
                raise ProtocolError("assistant omitted the required open prose question")
            return self.snapshot(
                status="passed",
                resolved_request_count=len(resolved_ids),
            )
        finally:
            if self._process is not None:
                self._process.terminate()
                try:
                    self._process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self._process.kill()
                    self._process.wait(timeout=3)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--effort", required=True)
    parser.add_argument("--repeats", required=True, type=int)
    parser.add_argument("--timeout-seconds", required=True, type=int)
    parser.add_argument("--workdir", required=True, type=Path)
    parser.add_argument(
        "--scenario",
        choices=tuple(SCENARIOS),
        default="collaborate_bounded_native_request",
    )
    parser.add_argument(
        "--review-dir",
        type=Path,
        help="explicit temporary directory for ephemeral question and prose review",
    )
    parser.add_argument("--server-command", default='["codex", "app-server", "--stdio"]')
    args = parser.parse_args()
    if args.repeats < 1 or args.timeout_seconds < 1:
        parser.error("--repeats and --timeout-seconds must be positive")
    try:
        command = json.loads(args.server_command)
    except json.JSONDecodeError as exc:
        parser.error(f"--server-command must be a JSON argv array: {exc}")
    if not isinstance(command, list) or not command or not all(
        isinstance(value, str) and value for value in command
    ):
        parser.error("--server-command must be a non-empty JSON string array")

    results: list[dict[str, Any]] = []
    blocked = False
    for repeat in range(args.repeats):
        review_path = (
            args.review_dir.resolve() / f"repeat-{repeat + 1}.txt"
            if args.review_dir
            else None
        )
        probe = AppServerProbe(
            command,
            args.workdir.resolve(),
            args.model,
            args.effort,
            args.timeout_seconds,
            args.scenario,
            review_path=review_path,
        )
        try:
            results.append(probe.run_once())
        except (OSError, ProtocolError) as exc:
            blocked = True
            results.append(probe.snapshot(status="blocked", blocker=str(exc)))
    print(json.dumps({"results": results}, separators=(",", ":")))
    return 2 if blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())
