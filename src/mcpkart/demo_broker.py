"""Single-writer MCP race broker with durable step receipts for Temporal replay.

Live admission requires a finite release, the authoritative ledger and complete
source/server-bound timing and interface evidence.
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
import time
from contextlib import AsyncExitStack
from pathlib import Path

import httpx
from fastmcp import Client

from .bench import percentiles, tool
from .decisions import Budget
from .demo_contract import MODELS
from .duel import TRIO_RACERS, DuelSimulation
from .duel_bench import audit_duel, free_choices, sources
from .duel_clock import mock_routes
from .duel_decisions import BudgetJournal, DuelDecisionClient, DuelDriver, duel_facts
from .question_context_driver import WireCapture, _write_new, encoded

LABELS = dict(zip(TRIO_RACERS, ("Jev", "OpenAI Decisions", "Clef"), strict=True))


class UnresolvedStep(RuntimeError):
    """A previous dispatch may have occurred; never dispatch it a second time."""


class Receipts:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS operations "
            "(identity TEXT PRIMARY KEY, state TEXT NOT NULL, receipt TEXT)"
        )
        self.db.commit()

    def get(self, identity):
        row = self.db.execute(
            "SELECT state, receipt FROM operations WHERE identity=?", (identity,)
        ).fetchone()
        if row is None:
            return None
        if row[0] != "done":
            raise UnresolvedStep("Unresolved operation; preserve evidence and stop: " + identity)
        return json.loads(row[1])

    def begin(self, identity):
        with self.db:
            self.db.execute("INSERT INTO operations VALUES (?, 'started', NULL)", (identity,))

    def complete(self, identity, value):
        with self.db:
            self.db.execute(
                "UPDATE operations SET state='done', receipt=? WHERE identity=?",
                (json.dumps(value, allow_nan=False), identity),
            )

    def close(self):
        self.db.close()


class DemoBroker:
    def __init__(self, *, url, output, logical_id, deadline=180, max_decisions=1100,
                 mock_delay=.2, transport_factory=None, live_status_path=None, paid=False, admission=None,
                 clock_path=None, interface_path=None, deployment_path=None):
        if paid and (admission is None or transport_factory is None):
            raise ValueError("Paid demo admission needs a new finite registration and complete clock gate")
        self.paid, self.admission = paid, admission
        self.clock_path, self.interface_path, self.deployment_path = clock_path, interface_path, deployment_path
        if paid and (deadline != admission.plan["deadline_s"] or max_decisions != admission.plan["max_decisions"]):
            raise ValueError("Live limits differ from the prospective registration")
        if not isinstance(logical_id, str) or not logical_id.startswith("mcpkart-"):
            raise ValueError("Use a dedicated mcpkart- logical race ID")
        if not 0 < deadline <= 600 or not 1 <= max_decisions <= 1100 or not 0 <= mock_delay <= 2:
            raise ValueError("Invalid finite demo bounds")
        self.url, self.output, self.logical_id = url, Path(output), logical_id
        self.deadline, self.max_decisions, self.mock_delay = deadline, max_decisions, mock_delay
        self.transport_factory = transport_factory
        self.live_status_path = Path(live_status_path) if live_status_path else self.output.parent / "live-status.json"
        self.output.mkdir(parents=True, exist_ok=False)
        self.receipts = Receipts(self.output / "receipts.sqlite3")
        self.stack = AsyncExitStack()
        self.initial = None
        self.stop = False
        self.frozen = sources()
        self.routes = admission.plan["routes"] if paid else mock_routes(MODELS, TRIO_RACERS)
        self.setup = {"racer_ids": list(TRIO_RACERS), "contact": "ghost"}
        self.config = DuelSimulation(**self.setup).config()
        self.budget = admission.budget if paid else Budget(self.output / "mock-budget.json", max_tokens=500000000)
        self.before = json.loads(self.budget.path.read_text())
        self.journal = BudgetJournal(self.budget, self.output / "budget-events.jsonl")
        self.locks = {r: asyncio.Lock() for r in TRIO_RACERS}
        self.lifecycle = asyncio.Lock()
        self.samples = {r: [] for r in TRIO_RACERS}
        self.drivers = {}
        self.http = {}
        self.observations = {}
        self.errors = []
        self.metrics = {r: {"thinking": False, "requests": 0} for r in TRIO_RACERS}

    async def __aenter__(self):
        try:
            return await self.prepare()
        except BaseException:
            await self.stack.aclose()
            self.journal.close()
            self.receipts.close()
            raise

    async def prepare(self):
        self.mcp = await self.stack.enter_async_context(Client(self.url, timeout=45))
        self.runtime = await tool(self.mcp, "runtime_info")
        if self.runtime.get("backend") != "process":
            raise ValueError("The demo requires process-isolated physics")
        if self.paid:
            self.admission.qualify(self.runtime, self.clock_path, self.interface_path, self.deployment_path)
        seen_ids = set()
        for rid in TRIO_RACERS:
            capture = WireCapture()
            route = self.routes[rid]

            async def mock(request, route=route):
                packet = json.loads(request.content)
                facts = {h + "_facts": packet["questions"][h]["instructions"]["current_facts"][h + "_facts"]
                         for h in ("wheel", "pedal")}
                wheel, pedal = free_choices(facts)
                await asyncio.sleep(self.mock_delay)
                import uuid
                return httpx.Response(200, json={
                    "id": "mock-" + uuid.uuid4().hex,
                    "model": route["resolved_model"], "provider": route["provider_name"],
                    "answers": {"wheel": {"type": "choice", "choice": wheel},
                                "pedal": {"type": "choice", "choice": pedal}},
                    "usage": {"input_tokens": 0, "output_tokens": 0, "cost": 0},
                })

            transport = self.transport_factory(rid) if self.transport_factory else httpx.MockTransport(mock)
            http = await self.stack.enter_async_context(httpx.AsyncClient(
                transport=transport, event_hooks=capture.hooks, timeout=10, follow_redirects=False,
            ))
            self.http[rid] = http
            self.drivers[rid] = DuelDriver(
                racer_id=rid, config=self.config, route=route, budget=self.journal.view(rid),
                http=http, capture=capture, output=self.output / rid, api_key="agentcore-private-credential",
                admission=self.admission.check if self.paid else None, seen_ids=seen_ids,
            )
        if self.transport_factory:
            # Mock-only initialization: complete cloud session startup before
            # starting the physics epoch. These probes never reserve model funds.
            preview = DuelSimulation(**self.setup)

            async def warm(rid):
                api = DuelDecisionClient(
                    facts=duel_facts(preview.observation(rid), self.config, rid),
                    handling=self.config["handling"], budget=None,
                    http_client=object(), api_key="free-placeholder",
                )
                route = mock_routes(MODELS, TRIO_RACERS)[rid]
                response = await self.http[rid].post("https://openrouter.ai/api/alpha/decisions", content=encoded({
                    "model": self.routes[rid]["model"], "state": {}, "questions": api.questions,
                    "provider": {"only": [self.routes[rid]["provider"]], "allow_fallbacks": False},
                }), extensions={"mcpkart_mock": True})
                response.raise_for_status()
                native = response.json()
                if native.get("model") != route["resolved_model"] or native.get("usage") != {
                    "input_tokens": 0, "output_tokens": 0, "cost": 0,
                }:
                    raise ValueError("Cloud mock warmup did not return the expected free route")
                return {"racer_id": rid, "native_id": native["id"], "model_requests": 0}

            _write_new(self.output / "prewarm-receipts.json", await asyncio.gather(*(warm(r) for r in TRIO_RACERS)))
        _write_new(self.output / "collection-start.json", {
            "source_sha256": self.frozen, "routes": self.routes, "setup": self.setup, "seed": 0,
            "free": not self.paid, "budget_before": self.before, "max_decisions_per_racer": self.max_decisions,
        })
        return self

    async def __aexit__(self, *_):
        try:
            if self.initial and not (self.output / "race.json").exists():
                await self.finish()
        finally:
            await self.stack.aclose()
            self.journal.close()
            self.receipts.close()

    def publish(self):
        if not self.initial:
            return
        path = self.live_status_path
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps({
            "race_id": self.initial["race_id"],
            "driver_labels": {r: LABELS[r] + ("" if self.paid else " · scripted mock") for r in TRIO_RACERS},
            "driver_metrics": self.metrics,
        }))
        temporary.replace(path)

    async def start(self):
        async with self.lifecycle:
            identity = self.logical_id + ":start"
            cached = self.receipts.get(identity)
            if cached is not None:
                return cached
            self.receipts.begin(identity)
            self.initial = await tool(self.mcp, "start_duel", {
                "deadline": self.deadline,
                "label": ("Jev vs OpenAI Decisions vs Clef" if self.paid else "Three-kart scripted mock") + " · Temporal + MCP" + (
                    " + AgentCore" if self.transport_factory else ""
                ),
                "race_setup": self.setup,
            })
            if set(self.initial["drivers"]) != set(TRIO_RACERS):
                raise ValueError("Start the MCP server with --trio")
            self.observations = {r: self.initial["drivers"][r]["observation"] for r in TRIO_RACERS}
            self.publish()
            receipt = {"logical_id": self.logical_id, "racers": list(TRIO_RACERS)}
            self.receipts.complete(identity, receipt)
            return receipt

    async def step(self, rid, seq):
        if rid not in TRIO_RACERS or isinstance(seq, bool) or not isinstance(seq, int) or seq < 0:
            raise ValueError("Invalid racer or decision sequence")
        async with self.locks[rid]:
            identity = f"{self.logical_id}:{rid}:{seq}"
            cached = self.receipts.get(identity)
            if cached is not None:
                return cached
            if not self.initial or seq != len(self.samples[rid]):
                raise ValueError("Start the race and use the next decision sequence")
            if sources() != self.frozen:
                raise RuntimeError("Source changed during collection")
            observation = self.observations[rid]
            if self.stop or observation["finished"] or observation["status"] != "running":
                return {"done": True, "seq": seq}
            if seq >= self.max_decisions:
                self.stop = True
                raise RuntimeError("Finite decision ceiling reached")
            self.receipts.begin(identity)
            started = time.monotonic_ns()
            self.metrics[rid]["thinking"] = True
            self.publish()
            try:
                record = await self.drivers[rid].decide(observation)
                pending = {**record, "applied": False, "command_seq": None, "observation_tick": observation["tick"],
                           "reason": "invalid_native_reply" if not record["ok"] else "stopped_before_apply"}
                self.samples[rid].append(pending)
                if not record["ok"]:
                    raise RuntimeError("Invalid native model reply")
                if self.stop:
                    receipt = {"done": True, "seq": seq, "applied": False}
                    self.receipts.complete(identity, receipt)
                    return receipt
                command_seq = sum(bool(s["applied"]) for s in self.samples[rid])
                ack = await tool(self.mcp, "drive_duel", {
                    "race_id": self.initial["race_id"], "racer_id": rid,
                    "driver_token": self.initial["drivers"][rid]["driver_token"],
                    "action_id": record["action"], "observation_tick": observation["tick"],
                    "command_seq": command_seq,
                })
                pending.update({
                    "command_seq": command_seq, "observation_tick": observation["tick"],
                    "applied": ack["applied"], "applied_tick": ack.get("applied_tick"),
                    "applied_ns": ack.get("applied_ns"), "reason": ack.get("reason"),
                    "observe_to_apply_ms": (ack.get("applied_ns", time.monotonic_ns())
                                            - observation["observed_ns"]) / 1e6,
                })
                self.observations[rid] = ack["observation"]
                self.metrics[rid].update(thinking=False, requests=self.drivers[rid].count,
                                         last_latency_ms=record["latency_ms"])
                self.publish()
                receipt = {"done": ack["observation"]["finished"] or ack["observation"]["status"] != "running",
                           "seq": seq, "applied": ack["applied"],
                           "step_ms": (time.monotonic_ns() - started) / 1e6}
                self.receipts.complete(identity, receipt)
                return receipt
            except BaseException as error:
                self.stop = True
                self.errors.append({"racer_id": rid, "type": type(error).__name__})
                raise

    async def finish(self):
        self.stop = True
        # Drain in-flight replies before settling the final single-writer chain.
        async with self.lifecycle, self.locks["red"], self.locks["blue"], self.locks["green"]:
            identity = self.logical_id + ":finish"
            cached = self.receipts.get(identity)
            if cached is not None:
                return cached
            if not self.initial:
                return {"started": False}
            self.receipts.begin(identity)
            race = await tool(self.mcp, "finish_duel", {
                "race_id": self.initial["race_id"], "owner_token": self.initial["owner_token"],
                "reason": "driver_error" if self.errors else "drivers_finished",
            })
            metrics = {r: {"requests": self.drivers[r].count,
                           "api_latency_ms": percentiles([s["latency_ms"] for s in self.samples[r]]),
                           "cost_usd": sum(s["cost"] for s in self.samples[r]),
                           "discarded": sum(not s["applied"] for s in self.samples[r])}
                       for r in TRIO_RACERS}
            race.update(driver_labels={r: LABELS[r] + ("" if self.paid else " · scripted mock") for r in TRIO_RACERS},
                        driver_metrics=metrics)
            _write_new(self.output / "race.json", race)
            _write_new(self.output / "decisions.json", self.samples)
            _write_new(self.output / "collection.json", {
                "free": not self.paid, "errors": self.errors, "metrics": metrics,
                "budget_before": self.before, "budget_after": self.journal.check(),
                "source_unchanged": sources() == self.frozen, "collection_complete": True,
            })
            proof = audit_duel(self.output) if not self.errors and race["timing"]["infrastructure_valid"] else None
            if proof:
                _write_new(self.output / "proof.json", proof)
            else:
                _write_new(self.output / "failure-audit.json", audit_duel(self.output, allow_failures=True))
            receipt = {"summary": race["summary"], "audit": proof, "recording": str(self.output / "race.json")}
            _write_new(self.output / "receipt.json", receipt)
            self.receipts.complete(identity, receipt)
            return receipt
