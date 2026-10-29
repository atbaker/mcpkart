"""OpenRouter Decisions transport and a persistent, conservative experiment budget.

No retries, fallbacks, control smoothing, or simulation policy live here. A failed
decision has ``action=None``; the race runner retains its last applied controls.
"""

from __future__ import annotations

import asyncio
import fcntl
import json
import math
import os
import re
import time
import uuid
from collections.abc import Mapping, Sequence
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Self

import httpx
from dotenv import dotenv_values

BASE_URL = "https://openrouter.ai"
DECISIONS_URL = f"{BASE_URL}/api/alpha/decisions"
DEFAULT_MODELS = (
    "openai/gpt-6-luna-decisions",
    "typesafe/jev-1.14",
    "cloudflare/clef",
)
DEFAULT_PROVIDERS = {
    "openai/gpt-6-luna-decisions": "openai",
    "typesafe/jev-1.14": "typesafe",
    "cloudflare/clef": "primeintellect",
}
CONTROL_LANGUAGES = ("numeric", "explicit", "geometry")
DECISION_LAYOUTS = ("joint", "factored")
FACTORED_WHEEL_INSTRUCTIONS = (
    " For this wheel question, choose only the ABSOLUTE wheel setting to hold NEXT. "
    "The pedal is selected in the separate pedal question in this same request. "
    "Both selected settings form one direct input."
)
FACTORED_PEDAL_INSTRUCTIONS = (
    " For this pedal question, choose only ACCELERATE, COAST, or BRAKE to hold NEXT. "
    "The wheel is selected in the separate wheel question in this same request. "
    "Both selected settings form one direct input."
)
_WHEEL_SETTINGS = (("hard_right", -1.0), ("right", -0.5), ("straight", 0.0),
                   ("left", 0.5), ("hard_left", 1.0))
_PEDAL_SETTINGS = (("accelerate", 1.0, 0.0), ("coast", 0.0, 0.0), ("brake", 0.0, 1.0))
DRIVING_INSTRUCTIONS = (
    "This is a fictional kart-racing video-game simulation; no real vehicles are controlled. "
    "Drive the kart through the ordered checkpoints and complete three laps as quickly as possible. "
    "Use the structured telemetry and road geometry in state. Select exactly one direct control. "
    "It stays applied while the next decision is being requested; the race keeps advancing in real time. "
    "Avoid leaving the road, slow for bends when necessary, and steer back onto the road if off-road. "
    "There is no automatic steering, lane keeping, or racing-line follower. "
    "If state.rescue.after_s is a number, remaining off-road for that many seconds returns the kart "
    "to the track at rest with coast controls. A null value disables rescue. "
    "After a rescue, continue choosing direct controls. "
    "Use state.units and state.handling for coordinate conventions and physical limits."
)
DAMPED_DRIVING_INSTRUCTIONS = (
    "Avoid overcorrection: select the gentlest wheel angle that can keep the near road corridor "
    "reachable. The wheel setting is absolute, so repeating moderate LEFT holds that turn "
    "continuously; it is not a small incremental nudge. Use STRAIGHT to unwind when the required "
    "heading is nearly reached. Existing yaw persists briefly after a new wheel command; allow for "
    "that response lag and the next inference interval. When the nose is already turning quickly LEFT"
    " toward alignment, unwind before it rotates too far LEFT; when already turning quickly RIGHT "
    "toward alignment, unwind before it rotates too far RIGHT. If the road is already being lost, "
    "slow down rather than holding full steering and full throttle indefinitely. Choose the single "
    "wheel-and-pedal input to hold NEXT in this fictional kart game. The kart keeps moving during "
    "inference (usually about 0.25 seconds). Complete all 120 ordered gates quickly; keep the kart on"
    " the road. Each choice sets an ABSOLUTE wheel angle, not a change to the previous input. LEFT "
    "wheels rotate the nose left; RIGHT wheels rotate it right; straight wheels do not auto-align. "
    "First judge the nearby road corridor from the CURRENT nose and motion. road.road_vs_kart_deg is "
    "ROAD tangent minus NOSE: negative means the road faces RIGHT of the nose; positive means LEFT. A"
    " left bend describes the road, not necessarily the steering correction needed now. Check "
    "road.preview ego_x_m/ego_y_m at 3, 6 and 10 metres, edge clearance, actual wheel angle and yaw. "
    "Avoid steering farther toward an edge when the nose and motion already point out across it. Use "
    "future bends for speed planning; do not replace current alignment with the distant bend label. "
    "Use the physical wheel angles/radii in the choices, allowing for grip and response lag. Braking "
    "lowers speed and allows tighter turns; do not remain stopped once forward progress is safe. For "
    "next_gate, credit requires crossing its plane from negative to positive within its width. If its"
    " plane is already positive without credit, recover to its approach side before crossing forward."
    " After rescue continue from the stopped kart. All controls remain your choice."
)

INSTRUCTION_STYLES = {
    "original": DRIVING_INSTRUCTIONS,
    "damped": DAMPED_DRIVING_INSTRUCTIONS,
    "question_first": (
        "Which steering-and-pedal input should this fictional racing kart apply NEXT "
        "to stay on the road and advance through its next checkpoint? "
        + DRIVING_INSTRUCTIONS
    ),
    "driving_guide": (
        "Which absolute wheel-angle and pedal input should this fictional kart hold NEXT "
        "to stay on the road while advancing through the next checkpoint? "
        "Driving guide: judge current alignment and lateral motion before following a future bend. "
        "For example, on a straight road, a kart pointing left of the road direction needs a rightward "
        "heading correction; pointing right needs a leftward correction. "
        "A kart moving toward an edge needs to reduce that outward motion. "
        "Centre the wheels as alignment is restored: centred wheels do not automatically centre the kart. "
        "As braking reduces grip-limited speed, the same held wheel angle can turn more tightly. "
        "Unwind steering as needed while slowing, and release braking in time to continue forward. "
        + DRIVING_INSTRUCTIONS
    ),
}


class BudgetExceeded(RuntimeError):
    """The next request cannot be safely reserved within the existing budget."""


class RouteDiscoveryError(RuntimeError):
    """The requested model and explicitly selected provider are not discoverable."""


def explicit_control_description(action: Mapping[str, Any]) -> str:
    """Describe the existing physical input without adding a driving policy."""
    steering = {
        -1.0: "Hold a hard RIGHT wheel angle (-1)",
        -0.5: "Hold a moderate RIGHT wheel angle (-0.5)",
        0.0: "Hold the wheels STRAIGHT (0)",
        0.5: "Hold a moderate LEFT wheel angle (+0.5)",
        1.0: "Hold a hard LEFT wheel angle (+1)",
    }
    pedals = {
        (1.0, 0.0): "ACCELERATE: throttle 1, brake 0",
        (0.0, 0.0): "COAST: throttle 0, brake 0",
        (0.0, 1.0): "BRAKE: throttle 0, brake 1",
    }
    try:
        return f"{steering[action['steer']]}; {pedals[(action['throttle'], action['brake'])]}."
    except (KeyError, TypeError) as exc:
        raise ValueError("Explicit control language requires the existing discrete steering/pedal inputs") from exc


def geometry_control_description(action: Mapping[str, Any], handling: Mapping[str, Any] | None) -> str:
    """Describe fixed input geometry; never derive a target or choose a control."""
    try:
        maximum, wheelbase = handling["max_steering_angle"], handling["wheelbase"]
        steer = action["steer"]
        if (any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
                for v in (maximum, wheelbase, steer))
                or not 0 < maximum < math.pi/2 or wheelbase <= 0 or not -1 <= steer <= 1):
            raise ValueError("Invalid physical input geometry")
        pedal = {(1.0, 0.0): "ACCELERATE", (0.0, 0.0): "COAST", (0.0, 1.0): "BRAKE"}[
            (action["throttle"], action["brake"])]
        angle = steer*maximum
        turn = "STRAIGHT" if not angle else "LEFT" if angle > 0 else "RIGHT"
        radius = wheelbase/abs(math.tan(angle)) if angle else None
        geometry = ("a straight nominal path" if radius is None
                    else f"a nominal bicycle turn radius of {radius:.1f} metres")
        return (f"Hold wheels {turn} at {abs(math.degrees(angle)):.2f} degrees; {geometry} "
                f"before grip/response transients. {pedal}.")
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Geometry control language requires valid physical actions and vehicle handling") from exc


def factored_control_menu(
    actions: Mapping[str, Any], handling: Mapping[str, Any] | None, control_language: str,
) -> tuple[dict[str, dict[str, str]], dict[tuple[str, str], str]]:
    """Describe fixed native components and build their exact physical inverse map.

    This requires the complete native 5-by-3 product. It never consults an
    observation, chooses an input, or derives a desired path or steering target.
    """
    try:
        maximum, wheelbase = handling["max_steering_angle"], handling["wheelbase"]
        if (any(isinstance(value, bool) or not isinstance(value, (int, float))
                or not math.isfinite(value) for value in (maximum, wheelbase))
                or not 0 < maximum < math.pi / 2 or wheelbase <= 0):
            raise ValueError("Invalid physical input geometry")
        native = {(steer, throttle, brake): (wheel_id, pedal_id)
                  for wheel_id, steer in _WHEEL_SETTINGS
                  for pedal_id, throttle, brake in _PEDAL_SETTINGS}
        inverse = {}
        for action_id, action in actions.items():
            if not isinstance(action_id, str) or not action_id or not isinstance(action, Mapping):
                raise ValueError("Factored actions must be named physical definitions")
            physical = tuple(action[field] for field in ("steer", "throttle", "brake"))
            if (any(isinstance(value, bool) or not isinstance(value, (int, float))
                    or not math.isfinite(value) for value in physical)
                    or physical not in native or native[physical] in inverse):
                raise ValueError("Factored actions must be an unambiguous native Cartesian product")
            inverse[native[physical]] = action_id
        if len(inverse) != len(native):
            raise ValueError("Factored actions must include the complete native Cartesian product")

        wheel = {}
        for wheel_id, steer in _WHEEL_SETTINGS:
            angle = steer * maximum
            direction = "STRAIGHT" if not angle else "LEFT" if angle > 0 else "RIGHT"
            description = f"Hold absolute wheel angle {angle:+g} radians ({direction}; steer {steer:+g})."
            if control_language == "geometry":
                # Preserve the existing geometry language, removing only the
                # fixed pedal clause now represented by the separate head.
                description = geometry_control_description(
                    {"steer": steer, "throttle": 0.0, "brake": 0.0}, handling,
                ).removesuffix(" COAST.")
            wheel[wheel_id] = description
        pedal = {
            "accelerate": "ACCELERATE: throttle 1, brake 0.",
            "coast": "COAST: throttle 0, brake 0.",
            "brake": "BRAKE: throttle 0, brake 1.",
        }
        return {"wheel": wheel, "pedal": pedal}, inverse
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(
            "Factored decisions require valid handling and the complete unambiguous native 5-by-3 action menu"
        ) from exc


def load_api_key(env_path: str | Path = ".env") -> str:
    """Read a key without putting it in command arguments, logs, or global env."""
    key = os.environ.get("OPENROUTER_API_KEY") or dotenv_values(env_path).get("OPENROUTER_API_KEY")
    if not isinstance(key, str) or not key.strip():
        raise RuntimeError("OPENROUTER_API_KEY is missing from the environment or ignored .env")
    return key.strip()


def _nonnegative(value: Any, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Missing or invalid {name}") from exc
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"Missing or invalid {name}")
    return number


async def discover_routes(
    client: httpx.AsyncClient | None = None,
    models: Sequence[str] = DEFAULT_MODELS,
    provider_overrides: Mapping[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Read the public Decisions catalog and pin one provider per requested model.

    ``model`` preserves the requested public API identifier; ``resolved_model``
    records the catalog's canonical version. Actual response identities must still
    be recorded because a catalog alias can change. Clef has no dated canonical
    version in the currently published catalog. Provider overrides are chosen
    before collecting comparison results, never as a request fallback.
    """
    owns_client = client is None
    client = client or httpx.AsyncClient(timeout=15, follow_redirects=False)
    try:
        response = await client.get(f"{BASE_URL}/api/v1/models", params={"output_modalities": "decisions"})
        response.raise_for_status()
        catalog = {entry["id"]: entry for entry in response.json()["data"]}
        providers = {**DEFAULT_PROVIDERS, **(provider_overrides or {})}
        observed_at = datetime.now(UTC).isoformat()
        routes = []
        for model in models:
            entry = catalog.get(model)
            if not entry or "decisions" not in entry.get("architecture", {}).get("output_modalities", []):
                raise RouteDiscoveryError(f"Requested Decisions model absent from public catalog: {model}")
            provider = providers.get(model)
            if not provider:
                raise RouteDiscoveryError(f"No preselected provider for requested model: {model}")
            response = await client.get(f"{BASE_URL}/api/v1/models/{model}/endpoints")
            response.raise_for_status()
            endpoints = response.json()["data"]["endpoints"]
            matching = [ep for ep in endpoints if ep.get("tag") == provider and ep.get("status", 0) == 0]
            if not matching:
                raise RouteDiscoveryError(f"Selected provider {provider} is unavailable for {model}")
            endpoint = matching[0]
            pricing = endpoint["pricing"]
            routes.append(
                {
                    "model": model,
                    "resolved_model": entry.get("canonical_slug", model),
                    "canonical_version_available": entry.get("canonical_slug", model) != model,
                    "canonical_version_pinned": False,
                    "provider": provider,
                    "provider_name": endpoint["provider_name"],
                    "endpoint_name": endpoint.get("name"),
                    "price_input_per_token": _nonnegative(pricing.get("prompt"), "prompt price"),
                    "price_output_per_token": _nonnegative(pricing.get("completion"), "completion price"),
                    "price_per_request": _nonnegative(pricing.get("request", 0), "request price"),
                    "context_length": endpoint.get("context_length", entry.get("context_length")),
                    "max_prompt_tokens": endpoint.get("max_prompt_tokens"),
                    "max_completion_tokens": endpoint.get("max_completion_tokens"),
                    "catalog_observed_at": observed_at,
                    "catalog_entry": entry,
                    "endpoint": endpoint,
                }
            )
        return routes
    finally:
        if owns_client:
            await client.aclose()


class Budget:
    """Atomic on-disk ledger; interrupted reservations remain charged and bounded.

    A separate lock file serializes read/check/write across clients and processes.
    Reopening a ledger never resets it or increases any of its existing limits.
    Omitting the request limit preserves its saved authorization; new ledgers
    start at 25,000 requests. Pending work is included in both dollar and token ceilings. Uncertain failures
    consume the whole reservation rather than pretending that timeouts are free.
    """

    def __init__(
        self,
        path: str | Path = "artifacts/budget.json",
        cap_usd: float = 10.0,
        max_requests: int | None = None,
        max_tokens: int = 250_000_000,
    ) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock_path = self.path.with_suffix(self.path.suffix + ".lock")
        cap_usd = _nonnegative(cap_usd, "budget cap")
        if cap_usd > 20:
            raise ValueError("The authorized experiment budget is at most $20")
        if (max_requests is not None and max_requests < 1) or max_tokens < 1:
            raise ValueError("Request and token ceilings must be positive")
        with self._locked():
            if self.path.exists():
                state = self._read()
                state["cap_usd"] = min(state["cap_usd"], cap_usd)
                if max_requests is not None:
                    state["max_requests"] = min(state["max_requests"], max_requests)
                state["max_tokens"] = min(state["max_tokens"], max_tokens)
            else:
                state = {
                    "schema_version": 1,
                    "cap_usd": cap_usd,
                    "max_requests": 25_000 if max_requests is None else max_requests,
                    "max_tokens": max_tokens,
                    "requests": 0,
                    "charged_usd": 0.0,
                    "charged_tokens": 0,
                    "reported_cost_usd": 0.0,
                    "uncertain_requests": 0,
                    "pending": {},
                }
            self._write(state)

    @contextmanager
    def _locked(self):
        with self.lock_path.open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)

    def _read(self) -> dict[str, Any]:
        state = json.loads(self.path.read_text())
        if state.get("schema_version") != 1:
            raise ValueError("Unsupported budget ledger schema; refusing to reset spending")
        for name in ("cap_usd", "charged_usd", "reported_cost_usd"):
            _nonnegative(state[name], name)
        return state

    def _write(self, state: dict[str, Any]) -> None:
        temporary = self.path.with_name(f".{self.path.name}.{uuid.uuid4().hex}.tmp")
        try:
            with temporary.open("w") as output:
                json.dump(state, output, indent=2, allow_nan=False)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, self.path)
        finally:
            temporary.unlink(missing_ok=True)

    def summary(self) -> dict[str, Any]:
        with self._locked():
            state = self._read()
        reserved_usd = sum(item["cost"] for item in state["pending"].values())
        reserved_tokens = sum(item["tokens"] for item in state["pending"].values())
        return {
            **state,
            "reserved_usd": reserved_usd,
            "reserved_tokens": reserved_tokens,
            "remaining_usd": max(0.0, state["cap_usd"] - state["charged_usd"] - reserved_usd),
        }

    def reserve(self, cost: float, tokens: int, *, model: str, provider: str) -> str:
        cost = _nonnegative(cost, "reservation cost")
        if tokens < 1:
            raise ValueError("Reservation must include a positive token ceiling")
        with self._locked():
            state = self._read()
            reserved_usd = sum(item["cost"] for item in state["pending"].values())
            reserved_tokens = sum(item["tokens"] for item in state["pending"].values())
            if state["requests"] >= state["max_requests"]:
                raise BudgetExceeded("Experiment request ceiling reached")
            if state["charged_tokens"] + reserved_tokens + tokens > state["max_tokens"]:
                raise BudgetExceeded("Experiment token ceiling would be exceeded")
            if state["charged_usd"] + reserved_usd + cost > state["cap_usd"]:
                raise BudgetExceeded("Experiment spending cap would be exceeded by next reservation")
            reservation = uuid.uuid4().hex
            state["pending"][reservation] = {
                "cost": cost,
                "tokens": tokens,
                "model": model,
                "provider": provider,
                "reserved_at": datetime.now(UTC).isoformat(),
            }
            state["requests"] += 1
            self._write(state)
            return reservation

    def commit(self, reservation: str, *, cost: float | None = None, tokens: int | None = None) -> float:
        if cost is not None:
            cost = _nonnegative(cost, "reported cost")
        if tokens is not None and tokens < 0:
            raise ValueError("Reported tokens cannot be negative")
        with self._locked():
            state = self._read()
            item = state["pending"].pop(reservation)
            charged = item["cost"] if cost is None else cost
            state["charged_usd"] += charged
            state["charged_tokens"] += item["tokens"] if tokens is None else tokens
            if cost is None:
                state["uncertain_requests"] += 1
            else:
                state["reported_cost_usd"] += cost
            self._write(state)
        return charged


class DecisionClient:
    def __init__(
        self,
        *,
        budget: Budget,
        actions: Mapping[str, Any],
        api_key: str | None = None,
        timeout_s: float = 5.0,
        http_client: httpx.AsyncClient | None = None,
        max_input_tokens: int = 8192,
        env_path: str | Path = ".env",
        control_language: str = "numeric",
        instruction_style: str = "original",
        handling: Mapping[str, Any] | None = None,
        decision_layout: str = "joint",
    ) -> None:
        self.budget = budget
        self.api_key = api_key or load_api_key(env_path)
        if control_language not in CONTROL_LANGUAGES:
            raise ValueError(f"Unknown control language: {control_language}")
        self.control_language = control_language
        if instruction_style not in INSTRUCTION_STYLES:
            raise ValueError(f"Unknown instruction style: {instruction_style}")
        self.instruction_style = instruction_style
        self.instructions = INSTRUCTION_STYLES[instruction_style]
        self.criteria = {}
        for action_id, action in actions.items():
            description = (
                action
                if isinstance(action, str)
                else (
                    action.get("description")
                    if isinstance(action, Mapping)
                    else getattr(action, "description", None)
                )
            )
            if not isinstance(description, str) or not description:
                raise ValueError(f"Missing description for action {action_id}")
            if control_language == "explicit":
                if not isinstance(action, Mapping):
                    raise ValueError("Explicit control language requires physical action definitions")
                description = explicit_control_description(action)
            elif control_language == "geometry":
                description = geometry_control_description(action, handling)
            self.criteria[action_id] = description
        if not self.criteria:
            raise ValueError("The decision action menu cannot be empty")
        if decision_layout not in DECISION_LAYOUTS:
            raise ValueError(f"Unknown decision layout: {decision_layout}")
        self.decision_layout = decision_layout
        self.component_criteria, self._component_actions = (
            factored_control_menu(actions, handling, control_language)
            if decision_layout == "factored" else ({}, {})
        )
        self.timeout_s = timeout_s
        self.max_input_tokens = max_input_tokens
        self._owns_client = http_client is None
        # HTTPX's default transport has zero retries and honors environment
        # proxies. Supplying a transport disables that proxy discovery, which
        # also bypasses managed Cloud network-secret injection.
        self.http_client = http_client or httpx.AsyncClient(
            timeout=timeout_s, follow_redirects=False
        )

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_):
        if self._owns_client:
            await self.http_client.aclose()

    def _safe_detail(self, value: Any) -> str:
        """Bound diagnostic text and redact credentials even if a server echoes one."""
        if not isinstance(value, str):
            value = json.dumps(value, ensure_ascii=False, default=str)
        value = value.replace(self.api_key, "[REDACTED]")
        value = re.sub(r"(?i)bearer\s+\S+", "Bearer [REDACTED]", value)
        value = re.sub(r"sk-or-v1-[A-Za-z0-9_-]+", "[REDACTED]", value)
        return value[:250]

    def _error_detail(self, result: Mapping[str, Any], fallback: str) -> str:
        error = result.get("error")
        if isinstance(error, dict):
            code = error.get("code")
            message = error.get("message", error.get("detail", fallback))
            return self._safe_detail(f"{code}: {message}" if code is not None else message)
        return self._safe_detail(error or result.get("refusal") or fallback)

    @property
    def questions(self) -> dict[str, Any]:
        """Return the exact current wire questions for recording and admission.

        Build these on access so custom static instructions keep their existing
        behavior. Copies of the criteria prevent provenance consumers from
        mutating the client's validated menus.
        """
        if self.decision_layout == "factored":
            return {
                "wheel": {
                    "type": "choice",
                    "instructions": self.instructions + FACTORED_WHEEL_INSTRUCTIONS,
                    "criteria": dict(self.component_criteria["wheel"]),
                },
                "pedal": {
                    "type": "choice",
                    "instructions": self.instructions + FACTORED_PEDAL_INSTRUCTIONS,
                    "criteria": dict(self.component_criteria["pedal"]),
                },
            }
        return {"control": {
            "type": "choice", "instructions": self.instructions, "criteria": dict(self.criteria),
        }}

    async def decide(self, route: Mapping[str, Any], observation: Mapping[str, Any]) -> dict[str, Any]:
        requested_model = route["model"]
        requested_provider = route["provider"]
        payload = {
            "model": requested_model,
            "state": observation,
            "questions": self.questions,
            "provider": {"only": [requested_provider], "allow_fallbacks": False},
        }
        encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()
        route_input_limit = route.get("max_prompt_tokens") or route.get("context_length")
        if route_input_limit and self.max_input_tokens > int(route_input_limit):
            raise ValueError("Configured input token ceiling exceeds the selected route context")
        # Compressed image bytes do not bound the model's expanded image tokens.
        # Reserve the complete advertised input window for multimodal requests.
        def has_image(value):
            if isinstance(value, Mapping):
                return value.get("type") == "image_url" or any(has_image(v) for v in value.values())
            return isinstance(value, (list, tuple)) and any(has_image(v) for v in value)

        if has_image(observation) and (not route_input_limit or self.max_input_tokens != int(route_input_limit)):
            raise ValueError("Image requests must reserve the full route input context")
        # Text requests use UTF-8 bytes plus framing as a conservative bound.
        # Image requests reserve their whole input window above; also bound wire size.
        input_byte_bound = len(encoded) + 512
        if self.decision_layout == "factored":
            # A provider may duplicate shared state while evaluating the two
            # questions. Count a second complete state conservatively, even
            # though the HTTP body transmits that state only once.
            input_byte_bound += len(json.dumps(
                observation, ensure_ascii=False, separators=(",", ":"), allow_nan=False,
            ).encode())
        if input_byte_bound > self.max_input_tokens:
            raise ValueError("Decision request exceeds the configured conservative input token ceiling")
        # The advertised completion ceiling covers the entire HTTP response,
        # including both factored answers. Reserve it once per request; do not
        # divide or shrink it because the questions have a finite choice menu.
        max_output = int(route.get("max_completion_tokens") or route.get("context_length") or 1_000_000)
        input_price = _nonnegative(route["price_input_per_token"], "input token price")
        output_price = _nonnegative(route["price_output_per_token"], "output token price")
        request_price = _nonnegative(route.get("price_per_request", 0), "request price")
        reservation_cost = self.max_input_tokens * input_price + max_output * output_price + request_price
        reservation = self.budget.reserve(
            reservation_cost,
            self.max_input_tokens + max_output,
            model=requested_model,
            provider=requested_provider,
        )
        record = {
            "ok": False,
            "action": None,
            "requested_model": requested_model,
            "requested_provider": requested_provider,
            "resolved_model": route.get("resolved_model"),
            "model": None,
            "provider": None,
            "id": None,
            "request_started_ns": time.perf_counter_ns(),
            "response_received_ns": None,
            "latency_ms": None,
            "usage": {},
            "cost": None,
            "cost_source": "reservation",
            "error": None,
            "error_detail": None,
            "reservation_id": reservation,
            "payload_bytes": len(encoded),
            "input_token_ceiling": self.max_input_tokens,
            "input_byte_bound": input_byte_bound,
            "control_language": self.control_language,
            "instruction_style": self.instruction_style,
            "choice_probabilities": None,
            "choice_confidence": None,
            "decision_layout": self.decision_layout,
            "component_choices": {"wheel": None, "pedal": None} if self.decision_layout == "factored" else None,
            "component_errors": None,
            "component_probabilities": None,
            "component_confidence": None,
        }
        reported_cost = None
        reported_tokens = None
        try:
            response = await self.http_client.post(
                DECISIONS_URL,
                content=encoded,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                timeout=self.timeout_s,
            )
            record["response_received_ns"] = time.perf_counter_ns()
            record["http_status"] = response.status_code
            try:
                result = response.json()
            except ValueError:
                result = {}
            if not isinstance(result, dict):
                result = {}
            metadata = result.get("metadata")
            metadata = metadata if isinstance(metadata, dict) else {}
            usage = result.get("usage") or metadata.get("usage") or {}
            if not isinstance(usage, dict):
                usage = {}
            record.update(
                {
                    "model": result.get("model"),
                    "provider": result.get("provider"),
                    "id": result.get("id"),
                    "usage": usage,
                }
            )
            raw_cost = usage.get("cost", result.get("cost", metadata.get("cost")))
            if raw_cost is not None:
                try:
                    reported_cost = _nonnegative(raw_cost, "response cost")
                    record["cost_source"] = "reported"
                except ValueError:
                    pass
            input_tokens, output_tokens = usage.get("input_tokens"), usage.get("output_tokens")
            if (
                isinstance(input_tokens, int)
                and not isinstance(input_tokens, bool)
                and input_tokens >= 0
                and isinstance(output_tokens, int)
                and not isinstance(output_tokens, bool)
                and output_tokens >= 0
            ):
                reported_tokens = input_tokens + output_tokens
            if not response.is_success:
                record["error"] = f"http_{response.status_code}"
                record["error_detail"] = self._error_detail(result, response.text)
                if response.status_code == 502 and re.search(
                    r"\bOpenAI\s+refused\s+to\s+answer\b", record["error_detail"], re.IGNORECASE
                ):
                    record["error"] = "refusal"
            elif result.get("error"):
                record["error"] = "api_error"
                record["error_detail"] = self._error_detail(result, "Unspecified Decisions API error")
            elif result.get("refusal"):
                record["error"] = "refusal"
                record["error_detail"] = self._error_detail(result, "Decision refused")
            else:
                answers = result.get("answers")
                if self.decision_layout == "factored":
                    action, component_errors = self._decode_components(answers, record)
                    answer = None
                else:
                    answer = answers.get("control") if isinstance(answers, dict) else None
                    action = answer.get("choice") if isinstance(answer, dict) else None
                    component_errors = {}
                if component_errors:
                    record["component_errors"] = component_errors
                    record["error"] = "refusal" if "refusal" in component_errors.values() else "invalid_action"
                    record["error_detail"] = self._safe_detail(component_errors)
                elif isinstance(answer, dict) and answer.get("refusal"):
                    record["error"] = "refusal"
                    record["error_detail"] = self._safe_detail(answer["refusal"])
                elif not isinstance(action, str) or action not in self.criteria:
                    record["error"] = "invalid_action"
                elif not isinstance(result.get("model"), str) or not isinstance(result.get("provider"), str):
                    record["error"] = "missing_response_identity"
                elif (
                    result["provider"].casefold()
                    != str(route.get("provider_name", requested_provider)).casefold()
                ):
                    record["error"] = "unexpected_provider"
                elif result["model"] not in {requested_model, route.get("resolved_model", requested_model)}:
                    record["error"] = "unexpected_model"
                else:
                    record["ok"] = True
                    record["action"] = action
                    if self.decision_layout == "factored":
                        # Component uncertainty is descriptive only. No joint
                        # distribution or confidence is fabricated from it.
                        self._record_component_uncertainty(answers, record)
                    else:
                        probabilities = answer.get("probabilities")
                        if isinstance(probabilities, dict):
                            record["choice_probabilities"] = {
                                key: value for key, value in probabilities.items()
                                if key in self.criteria and isinstance(value, (int, float))
                                and not isinstance(value, bool) and math.isfinite(value) and 0 <= value <= 1
                            } or None
                        confidence = answer.get("confidence")
                        if (isinstance(confidence, (int, float)) and not isinstance(confidence, bool)
                                and math.isfinite(confidence) and 0 <= confidence <= 1):
                            record["choice_confidence"] = confidence
        except asyncio.CancelledError:
            record["error"] = "cancelled"
            raise
        except httpx.TimeoutException:
            record["error"] = "timeout"
        except httpx.HTTPError:
            record["error"] = "transport_error"
        finally:
            record["response_received_ns"] = record["response_received_ns"] or time.perf_counter_ns()
            record["latency_ms"] = (record["response_received_ns"] - record["request_started_ns"]) / 1_000_000
            record["cost"] = self.budget.commit(reservation, cost=reported_cost, tokens=reported_tokens)
        return record

    def _decode_components(self, answers: Any, record: dict[str, Any]) -> tuple[str | None, dict[str, str]]:
        """Validate both heads before permitting a single native action."""
        errors = {}
        choices = record["component_choices"]
        for component, criteria in self.component_criteria.items():
            answer = answers.get(component) if isinstance(answers, dict) else None
            if not isinstance(answer, dict):
                errors[component] = "missing_answer"
            elif answer.get("refusal"):
                errors[component] = "refusal"
            elif answer.get("type") != "choice":
                errors[component] = "invalid_type"
            elif not isinstance(answer.get("choice"), str) or answer["choice"] not in criteria:
                errors[component] = "invalid_choice"
            else:
                choices[component] = answer["choice"]
        if errors:
            return None, errors
        return self._component_actions[(choices["wheel"], choices["pedal"])], {}

    def _record_component_uncertainty(self, answers: Mapping[str, Any], record: dict[str, Any]) -> None:
        probabilities, confidence = {}, {}
        for component, criteria in self.component_criteria.items():
            answer = answers[component]
            raw_probabilities = answer.get("probabilities")
            if isinstance(raw_probabilities, dict):
                valid = {
                    key: value for key, value in raw_probabilities.items()
                    if key in criteria and isinstance(value, (int, float))
                    and not isinstance(value, bool) and math.isfinite(value) and 0 <= value <= 1
                }
                if valid:
                    probabilities[component] = valid
            value = answer.get("confidence")
            if (isinstance(value, (int, float)) and not isinstance(value, bool)
                    and math.isfinite(value) and 0 <= value <= 1):
                confidence[component] = value
        record["component_probabilities"] = probabilities or None
        record["component_confidence"] = confidence or None
