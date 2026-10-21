"""Recorded, opt-in Jev driver for the question-local experimental prompt."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import re
from pathlib import Path

from .decisions import DecisionClient
from .question_context import (
    COMMON_DEFINITIONS,
    INSTRUCTION_STYLE,
    PromptDomainError,
    QuestionContextClient,
    build_questions,
    project_facts,
)
from .sim import ACTIONS, Simulation


def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()


def _read(path):
    return json.loads(Path(path).read_text())


def _safe(value, secret):
    if isinstance(value, dict):
        return {_safe(key, secret): _safe(item, secret) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe(item, secret) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return "NONFINITE:" + repr(value)
    if isinstance(value, str):
        if secret:
            value = value.replace(secret, "[REDACTED]")
        value = re.sub(r"(?i)bearer\s+\S+", "Bearer [REDACTED]", value)
        return re.sub(r"sk-or-v1-[A-Za-z0-9_-]+", "[REDACTED]", value)
    return value


def _write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


class WireCapture:
    """HTTPX hooks retain bodies and status; authentication headers are omitted."""

    def __init__(self):
        self.requests = []
        self.responses = []

    def clear(self):
        self.requests.clear()
        self.responses.clear()

    async def request(self, request):
        self.requests.append({"url": str(request.url), "method": request.method,
                              "body": bytes(request.content)})

    async def response(self, response):
        await response.aread()
        try:
            body = response.json()
        except ValueError:
            body = None
        self.responses.append({"status": response.status_code, "body": bytes(response.content),
                               "json": body})

    @property
    def hooks(self):
        return {"request": [self.request], "response": [self.response]}

    def evidence(self, secret):
        raw = {
            "requests": [{"url": item["url"], "method": item["method"],
                          "body_utf8": item["body"].decode(errors="replace"),
                          "body_sha256": hashlib.sha256(item["body"]).hexdigest()}
                         for item in self.requests],
            "responses": [{"status": item["status"], "json": item["json"],
                           "body_utf8": item["body"].decode(errors="replace"),
                           "body_sha256": hashlib.sha256(item["body"]).hexdigest()}
                          for item in self.responses],
        }
        safe = _safe(raw, secret)
        return {**safe, "saved_unmodified": safe == raw}


def _number(value):
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and value >= 0)


class QuestionContextDriver:
    """A fresh factual client per observation, with replies checked before use.

    Use the ordinary benchmark loop with ``telemetry="raw"``. The race header
    contains question templates; each actual question is recorded separately.
    HTTP must use the supplied capture's hooks. The optional admission callback
    runs before each POST, so a caller can bind runtime, source and budget rules.
    """

    def __init__(self, *, budget, http, capture: WireCapture, route: dict,
                 config: dict, output: Path, api_key=None, admission=None):
        self.budget, self.http, self.capture = budget, http, capture
        self.route, self.config = copy.deepcopy(route), copy.deepcopy(config)
        self.output, self.admission = Path(output), admission
        self.expected_budget = _read(budget.path)
        self.count, self.seen_ids = 0, set()
        self._busy = self._stopped = False
        self._header = DecisionClient(
            budget=budget, http_client=http, api_key=api_key, actions=ACTIONS,
            handling=config["handling"], max_input_tokens=16384,
            control_language="geometry", decision_layout="factored",
        )
        self._header.instructions = COMMON_DEFINITIONS
        self._header.instruction_style = INSTRUCTION_STYLE
        canonical = Simulation.from_config(config).observation()
        self._templates = build_questions(
            self._header.component_criteria, project_facts(canonical, config=config),
        )
        for question in self._templates.values():
            question["instructions"].pop("current_facts")

    def __getattr__(self, name):
        return getattr(self._header, name)

    @property
    def questions(self):
        return copy.deepcopy(self._templates)

    async def decide(self, route, observation):
        if self._busy or self._stopped:
            raise RuntimeError("Driver is already deciding or stopped after an invalid reply")
        self._busy = True
        try:
            return await self._decide(route, observation)
        finally:
            self._busy = False

    async def _decide(self, route, observation):
        before = _read(self.budget.path)
        if route != self.route or before != self.expected_budget or before.get("pending"):
            self._stopped = True
            raise RuntimeError("Route or shared budget changed before POST")
        try:
            facts = project_facts(observation, config=self.config)
        except PromptDomainError as error:
            self._stopped = True
            _write_new(self.output / "domain-stop.json", {
                "reason": str(error), "raw": _safe(observation, self.api_key),
                "model_post_started_for_this_snapshot": False,
                "quality_failure": True, "no_host_correction": True,
            })
            raise
        if self.admission:
            self.admission()
        api = QuestionContextClient(
            current_facts=facts, budget=self.budget, http_client=self.http,
            handling=self.config["handling"], api_key=self.api_key,
        )
        questions = api.questions
        query = {"index": self.count, "physical_packet": facts,
                 "wire_state": {}, "questions": questions, "budget_before": before}
        _write_new(self.output / f"query-{self.count:05d}.json", query)
        self.capture.clear()
        try:
            original = await api.decide(route, {})
        except BaseException:
            self._stopped = True
            _write_new(self.output / f"interrupted-call-{self.count:05d}.json", {
                "budget_before": before, "budget_after": _read(self.budget.path),
                "wire": self.capture.evidence(self.api_key), "no_action_returned": True,
            })
            raise
        after = _read(self.budget.path)
        record = copy.deepcopy(original)
        wire = self.capture.evidence(self.api_key)
        failures = []
        payload = {"model": route["model"], "state": {}, "questions": questions,
                   "provider": {"only": [route["provider"]], "allow_fallbacks": False}}
        if len(self.capture.requests) != 1 or self.capture.requests[0]["body"] != encoded(payload):
            failures.append("actual_wire_request_mismatch")
        if not wire["saved_unmodified"]:
            failures.append("unsafe_or_nonfinite_wire_text")
        raw = self.capture.responses[0]["json"] if len(self.capture.responses) == 1 else None
        if not isinstance(raw, dict):
            failures.append("missing_single_raw_response")
        else:
            if self.capture.responses[0]["status"] != 200:
                failures.append("unexpected_http_status")
            response_id = raw.get("id")
            if not isinstance(response_id, str) or not response_id.strip() or response_id in self.seen_ids:
                failures.append("missing_or_duplicate_response_id")
            else:
                self.seen_ids.add(response_id)
            if (raw.get("model") != route["resolved_model"]
                    or raw.get("provider") != route["provider_name"]
                    or any(raw.get(key) != record.get(key) for key in ("model", "provider", "id", "usage"))):
                failures.append("strict_response_identity_or_usage_mismatch")
            answers = raw.get("answers")
            if not isinstance(answers, dict) or set(answers) != {"wheel", "pedal"}:
                failures.append("unexpected_answer_heads")
            else:
                choices = {}
                for head, allowed in api.component_criteria.items():
                    answer = answers[head]
                    if (not isinstance(answer, dict) or answer.get("type") != "choice"
                            or answer.get("refusal") or not isinstance(answer.get("choice"), str)
                            or answer["choice"] not in allowed):
                        failures.append("invalid_raw_" + head)
                    else:
                        choices[head] = answer["choice"]
                if len(choices) == 2 and (
                    choices != record["component_choices"]
                    or api._component_actions[(choices["wheel"], choices["pedal"])] != record["action"]
                ):
                    failures.append("native_inverse_mismatch")
            usage = raw.get("usage")
            if (not isinstance(usage, dict) or not _number(usage.get("cost"))
                    or usage["cost"] != record.get("cost")):
                failures.append("invalid_raw_reported_cost")
        usage = record.get("usage") or {}
        counts = [usage.get(key) for key in ("input_tokens", "output_tokens")]
        certain = (record.get("cost_source") == "reported" and _number(record.get("cost"))
                   and all(isinstance(n, int) and not isinstance(n, bool) and n >= 0 for n in counts))
        if not certain:
            failures.append("uncertain_accounting")
        else:
            expected = copy.deepcopy(before)
            expected["requests"] += 1
            expected["charged_tokens"] += sum(counts)
            expected["charged_usd"] += record["cost"]
            expected["reported_cost_usd"] += record["cost"]
            if after != expected or after.get("pending"):
                failures.append("unexpected_shared_ledger_transition")
            self.expected_budget = expected
        if failures:
            record["unapplied_reply_action"] = record.get("action")
            record["upstream_error"] = record.get("error")
            record.update(ok=False, action=None, error="question_context_guard_failure",
                          error_detail=";".join(failures), wrapper_failures=failures)
        if not record["ok"]:
            self._stopped = True
        record.update(physical_packet=facts, wire_questions=questions, wire_state={},
                      budget_before=before, budget_after=after,
                      wire_payload_sha256=hashlib.sha256(encoded(payload)).hexdigest())
        safe_record = _safe(record, self.api_key)
        _write_new(self.output / "calls" / f"{self.count:05d}.json", {
            "index": self.count, "wire": wire, "query": query,
            "original_record": _safe(original, self.api_key), "returned_record": safe_record,
        })
        self.count += 1
        return safe_record
