"""Experimental question-local driving prompt from studies 0050–0053.

Facts describe the current pose; native controls are selected only by Jev.
The application default and the ordinary DecisionClient are unchanged.
"""

from __future__ import annotations

import copy
import math
from typing import Any

from .bench import driving_evidence
from .decisions import DecisionClient
from .sim import ACTIONS

PROMPT_VERSION = "question_context_v1"
INSTRUCTION_STYLE = "qualified_question_component_policy_v1"

COMMON_DEFINITIONS = (
    "Apply the following fixed bearing policy to the CURRENT factual state; its eligible wheel and pedal form one native input. "
    "These are supplied engineering rules, not a claim that the input is optimal or pursuit-equivalent. "
    "Read x=ego_x_m and y=ego_y_m from the road.preview row whose ahead_m equals 15, using road.preview_columns. "
    "The 15 m centre bearing theta equals round(degrees(atan2(y,x)),4), calculated from those rounded raw coordinates. "
    "If road.preview_15m_bearing_deg is present, read theta directly from that factual scalar; otherwise compute theta yourself. "
    "Positive theta means LEFT of the kart nose, negative theta means RIGHT. Thresholds are -22, -7, +7 and +22 degrees; "
    "exact threshold ties choose the smaller absolute wheel angle. "
    "Let speed=kart.speed_m_s and L=current_road_frame.velocity_left_m_s. "
    "Let B be true exactly when road.on_road is false, OR (road.offset_m>0 AND "
    "road.left_edge_clearance_m<=3 AND L>=0.5), OR (road.offset_m<0 AND "
    "road.right_edge_clearance_m<=3 AND L<=-0.5). Otherwise B is false. "
    "The speed<2 acceleration rule takes priority even when B is true."
)

WHEEL_CLAUSES = {
    "hard_right": "FIXED POLICY ELIGIBILITY: choose this wheel exactly when theta < -22 degrees.",
    "right": "FIXED POLICY ELIGIBILITY: choose this wheel exactly when -22 <= theta < -7 degrees.",
    "straight": "FIXED POLICY ELIGIBILITY: choose this wheel exactly when -7 <= theta <= +7 degrees.",
    "left": "FIXED POLICY ELIGIBILITY: choose this wheel exactly when +7 < theta <= +22 degrees.",
    "hard_left": "FIXED POLICY ELIGIBILITY: choose this wheel exactly when theta > +22 degrees.",
}

PEDAL_CLAUSES = {
    "accelerate": "FIXED POLICY ELIGIBILITY: choose ACCELERATE exactly when speed<2 OR (speed>=2 AND B is false).",
    "coast": "FIXED POLICY ELIGIBILITY: choose COAST exactly when B is true AND 2<=speed<=6.",
    "brake": "FIXED POLICY ELIGIBILITY: choose BRAKE exactly when B is true AND speed>6.",
}

DRIVING_TASK_PREFIX = "DRIVING POLICY. Choose the next native input by executing the supplied policy exactly. "

WHEEL_TASK = "\nWHEEL TASK: Select the single allowed absolute wheel ID whose supplied policy condition holds. Return only that wheel choice."

PEDAL_TASK = (
    "\nPEDAL TASK: Select the single allowed pedal ID whose supplied policy condition holds. "
    "Return only that pedal choice; the wheel is selected separately in this same request."
)

SHARED = (
    "Apply the following fixed bearing policy to the CURRENT factual state; its eligible wheel and pedal form one native input. "
    "These are supplied engineering rules, not a claim that the input is optimal or pursuit-equivalent. "
)

PEDAL_EXAMPLES = (
    "\nFIXED WORKED PEDAL EXAMPLES (speed and L in m/s, distances in metres; never the current query's answer): "
    "on_road=true, offset_m=-10, left_edge_clearance_m=22, right_edge_clearance_m=2, L=+1, speed=8: "
    "right-side clearance is small but velocity is inward; B=false -> accelerate. "
    "on_road=true, offset_m=+10, left_edge_clearance_m=2, right_edge_clearance_m=22, L=-1, speed=8: "
    "left-side clearance is small but velocity is inward; B=false -> accelerate. "
    "on_road=true, offset_m=-10, left_edge_clearance_m=22, right_edge_clearance_m=2, L=-1, speed=8: "
    "all three right-side predicates hold; B=true -> brake. "
    "on_road=true, offset_m=+10, left_edge_clearance_m=2, right_edge_clearance_m=22, L=+1, speed=8: "
    "all three left-side predicates hold; B=true -> brake. "
    "on_road=false, speed=0: low-speed priority -> accelerate. "
    "on_road=false, speed=4: B=true -> coast. "
    "on_road=false, speed=8: B=true -> brake."
)

ROAD_FRAME_UNITS = (
    "Angles are degrees and velocities are m/s in the CURRENT ROAD frame. "
    "Positive nose_vs_road_deg and velocity_vs_road_deg mean LEFT of the current road tangent. "
    "Positive velocity_left_m_s means LEFT; positive velocity_forward_m_s means FORWARD along that tangent."
)


class PromptDomainError(ValueError):
    """A current pose is outside the domain evaluated for this prompt."""


def project_facts(raw: dict, *, config: dict) -> dict:
    """Project current geometry and motion without evaluating a driving rule.

    The factual bearing is atan2 of the same rounded preview coordinates sent
    to the model. No eligible action, risk predicate or suggested control is
    computed here. The qualified domain requires the 15 m target ahead and
    no positive uncredited required gate plane.
    """
    base = driving_evidence(raw, "road_navigation", config=config)
    columns = base["road"]["preview_columns"]
    rows = [row for row in base["road"]["preview"] if row[0] == 15]
    if columns[:3] != ["ahead_m", "ego_x_m", "ego_y_m"] or len(rows) != 1:
        raise PromptDomainError("Exactly one original 15 m preview is required")
    _, x, y = rows[0][:3]
    if not all(_finite(value) for value in (x, y)) or x <= 0:
        raise PromptDomainError("15m_preview_not_forward")
    gate = {name: base["next_gate"][name] for name in ("known", "signed_plane_m")}
    if gate["known"] and gate["signed_plane_m"] > 0:
        raise PromptDomainError("required_uncredited_gate_already_positive")
    compact = driving_evidence(raw, "compact", config=config)
    result = {
        "wheel_facts": {
            "units": copy.deepcopy(base["units"]),
            "road": {
                "preview_15m_bearing_deg": round(math.degrees(math.atan2(y, x)), 4),
                "preview_columns": copy.deepcopy(columns[:3]),
                "preview": [copy.deepcopy(rows[0][:3])],
            },
            "next_gate": copy.deepcopy(gate),
        },
        "pedal_facts": {
            "units": copy.deepcopy(base["units"]),
            "kart": {"speed_m_s": base["kart"]["speed_m_s"]},
            "road": {name: base["road"][name] for name in (
                "on_road", "offset_m", "left_edge_clearance_m", "right_edge_clearance_m",
            )},
            "current_road_frame": {
                "velocity_left_m_s": compact["present"]["road_lateral_m_s"],
                "units": ROAD_FRAME_UNITS,
            },
            "next_gate": copy.deepcopy(gate),
        },
    }
    validate_facts(result)
    return result


def _finite(value: Any) -> bool:
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value))


def validate_facts(facts: dict) -> None:
    """Reject malformed or unsupported facts before a request is reserved."""
    def finite_tree(value):
        if isinstance(value, float) and not math.isfinite(value):
            raise PromptDomainError("Nonfinite current fact")
        if isinstance(value, dict):
            for item in value.values():
                finite_tree(item)
        elif isinstance(value, (tuple, list)):
            for item in value:
                finite_tree(item)

    finite_tree(facts)
    try:
        if set(facts) != {"wheel_facts", "pedal_facts"}:
            raise PromptDomainError("Both factual component groups are required")
        wheel, pedal = facts["wheel_facts"], facts["pedal_facts"]
        road = wheel["road"]
        if road["preview_columns"] != ["ahead_m", "ego_x_m", "ego_y_m"]:
            raise PromptDomainError("Original preview columns required")
        if len(road["preview"]) != 1 or road["preview"][0][0] != 15:
            raise PromptDomainError("Exactly one 15 m target required")
        _, x, y = road["preview"][0]
        if not all(_finite(value) for value in (x, y)) or x <= 0:
            raise PromptDomainError("15m_preview_not_forward")
        if road["preview_15m_bearing_deg"] != round(math.degrees(math.atan2(y, x)), 4):
            raise PromptDomainError("Bearing differs from current preview coordinates")
        if wheel["next_gate"] != pedal["next_gate"]:
            raise PromptDomainError("Component gate facts differ")
        gate = wheel["next_gate"]
        if gate["known"] and gate["signed_plane_m"] > 0:
            raise PromptDomainError("required_uncredited_gate_already_positive")
        if not _finite(pedal["kart"]["speed_m_s"]) or pedal["kart"]["speed_m_s"] < 0:
            raise PromptDomainError("Finite nonnegative speed required")
        if not _finite(pedal["current_road_frame"]["velocity_left_m_s"]):
            raise PromptDomainError("Finite current lateral velocity required")
    except (KeyError, IndexError, TypeError) as error:
        raise PromptDomainError("Malformed current component facts") from error


def build_questions(component_criteria: dict, facts: dict) -> dict:
    """Build both complete native menus, with facts inside each question."""
    validate_facts(facts)
    wheel, pedal = COMMON_DEFINITIONS[len(SHARED):].split("Let speed=", 1)
    definitions = {
        "wheel": (SHARED + wheel).replace("road.", "wheel_facts.road."),
        "pedal": (SHARED + "Let speed=" + pedal).replace(
            "kart.", "pedal_facts.kart.",
        ).replace("current_road_frame.", "pedal_facts.current_road_frame.").replace(
            "road.", "pedal_facts.road.",
        ) + PEDAL_EXAMPLES,
    }
    result = {}
    for head, clauses, task in (
        ("wheel", WHEEL_CLAUSES, WHEEL_TASK),
        ("pedal", PEDAL_CLAUSES, PEDAL_TASK),
    ):
        physical = component_criteria[head]
        if set(physical) != set(clauses):
            raise ValueError("Original complete component menu required")
        result[head] = {
            "type": "choice",
            "instructions": {
                "rules": DRIVING_TASK_PREFIX + definitions[head] + task,
                "current_facts": {head + "_facts": copy.deepcopy(facts[head + "_facts"])},
            },
            "criteria": {name: description + " " + clauses[name]
                         for name, description in physical.items()},
        }
    return result


class QuestionContextClient(DecisionClient):
    """One immutable factual snapshot; ordinary deciding and decoding inherited.

    Call ``decide(route, {})`` once for this snapshot. Construct a fresh client
    for the next observation while sharing its HTTP client and Budget. Native
    controls, including the complete wheel/pedal inverse, stay unchanged.
    """

    def __init__(self, *, current_facts: dict, budget, http_client,
                 handling: dict, api_key: str | None = None):
        validate_facts(current_facts)
        self._current_facts = copy.deepcopy(current_facts)
        super().__init__(
            budget=budget, actions=ACTIONS, api_key=api_key, http_client=http_client,
            max_input_tokens=16384, control_language="geometry", decision_layout="factored",
            handling=handling,
        )
        self.instructions = COMMON_DEFINITIONS
        self.instruction_style = INSTRUCTION_STYLE

    @property
    def questions(self) -> dict:
        return build_questions(self.component_criteria, self._current_facts)
