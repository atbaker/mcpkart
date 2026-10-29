"""Question-local prompt contracts; all HTTP is explicitly mocked."""
import asyncio
import copy
import json
import math
from pathlib import Path

import httpx
import pytest

from mcpkart.decisions import Budget, DecisionClient
from mcpkart.question_context import (
    PromptDomainError,
    QuestionContextClient,
    project_facts,
    validate_facts,
)
from mcpkart.sim import Simulation

ROUTE = {
    'model': 'typesafe/jev-1.14', 'resolved_model': 'typesafe/jev-1.14-test',
    'provider': 'typesafe', 'provider_name': 'TypeSafe',
    'price_input_per_token': 0, 'price_output_per_token': 0,
    'price_per_request': 0, 'context_length': 262144, 'max_completion_tokens': 235929,
}


def current():
    sim = Simulation(seed=43, course='stadium', road_width=24,
                     max_speed=12, max_steering_angle=.12, reset_after_s=3)
    return sim, project_facts(sim.observation(), config=sim.config())


def test_projection_preserves_current_pose_and_coordinates():
    sim, _ = current()
    original = sim.observation()
    snapshot = copy.deepcopy(original)
    facts = project_facts(original, config=sim.config())
    assert original == snapshot == sim.observation()
    road = facts['wheel_facts']['road']
    _, x, y = road['preview'][0]
    assert road['preview_15m_bearing_deg'] == round(math.degrees(math.atan2(y, x)), 4)
    assert facts['wheel_facts']['next_gate'] == facts['pedal_facts']['next_gate']
    assert set(facts) == {'wheel_facts', 'pedal_facts'}
    def keys(value):
        if not isinstance(value, dict):
            return set()
        return set(value).union(*(keys(child) for child in value.values()))
    assert not keys(facts) & {'action', 'control', 'eligible', 'recommendation'}


@pytest.mark.parametrize('change', ['behind', 'nonfinite', 'bearing', 'gate', 'speed'])
def test_unsupported_snapshot_is_rejected_before_client_budget_access(change):
    sim, facts = current()
    if change == 'behind':
        facts['wheel_facts']['road']['preview'][0][1] = -1
    elif change == 'nonfinite':
        facts['pedal_facts']['current_road_frame']['velocity_left_m_s'] = math.nan
    elif change == 'bearing':
        facts['wheel_facts']['road']['preview_15m_bearing_deg'] += 1
    elif change == 'gate':
        for head in facts.values():
            head['next_gate'] = {'known': True, 'signed_plane_m': 1}
    else:
        facts['pedal_facts']['kart']['speed_m_s'] = -1
    with pytest.raises(PromptDomainError):
        QuestionContextClient(current_facts=facts, budget=object(), http_client=object(),
                              handling=sim.config()['handling'], api_key='mock-secret')


def test_missing_component_is_a_domain_error():
    with pytest.raises(PromptDomainError):
        validate_facts({'wheel_facts': {}})


def test_goal_prompt_preserves_facts_and_all_physical_choices_without_policy():
    sim, facts = current()
    kwargs = {'current_facts': facts, 'budget': object(), 'http_client': object(),
              'handling': sim.config()['handling'], 'api_key': 'mock-secret'}
    policy = QuestionContextClient(**kwargs)
    goal = QuestionContextClient(**kwargs, prompt_mode='goal')
    assert goal.instruction_style == 'question_local_goal_only_v1'
    assert goal.component_criteria == policy.component_criteria
    for head in ('wheel', 'pedal'):
        question = goal.questions[head]
        assert question['instructions']['current_facts'] == policy.questions[head]['instructions']['current_facts']
        assert question['criteria'] == policy.component_criteria[head]
    instructions = json.dumps(goal.questions)
    for forbidden in ('FIXED POLICY', 'ELIGIBILITY', 'WORKED', 'theta <', 'theta >',
                      'B=true', 'B=false', 'speed<2', 'unwind', 'gentlest'):
        assert forbidden not in instructions
    assert 'all 120 required checkpoint gates' in goal.instructions
    assert goal.questions['wheel']['instructions']['current_facts']['wheel_facts']['road'] == facts['wheel_facts']['road']


def test_default_policy_questions_match_both_saved_successful_model_examples():
    path = Path(__file__).resolve().parents[1] / 'docs/experiments/current-driver-examples.json'
    for example in json.loads(path.read_text())['successful_race_examples']:
        facts = {head + '_facts': example['questions'][head]['instructions']['current_facts'][head + '_facts']
                 for head in ('wheel', 'pedal')}
        sim, _ = current()
        api = QuestionContextClient(current_facts=facts, budget=object(), http_client=object(),
                                    handling=sim.config()['handling'], api_key='mock-secret')
        assert api.questions == example['questions']


def test_unknown_prompt_mode_is_rejected_before_budget_access():
    sim, facts = current()
    with pytest.raises(ValueError, match='Unknown question-local prompt mode'):
        QuestionContextClient(current_facts=facts, budget=object(), http_client=object(),
                              handling=sim.config()['handling'], api_key='mock-secret', prompt_mode='unknown')


def test_extended_goal_domain_keeps_questions_identical_on_previously_supported_facts():
    sim, facts = current()
    kwargs = {'current_facts': facts, 'budget': object(), 'http_client': object(),
              'handling': sim.config()['handling'], 'api_key': 'mock-secret', 'prompt_mode': 'goal'}
    assert QuestionContextClient(**kwargs).questions == QuestionContextClient(**kwargs, extended_domain=True).questions


def test_extended_domain_projects_behind_preview_and_passed_required_gate_as_facts():
    sim, _ = current()
    sim.heading += math.pi
    with pytest.raises(PromptDomainError, match='not_forward'):
        project_facts(sim.observation(), config=sim.config())
    facts = project_facts(sim.observation(), config=sim.config(), extended_domain=True)
    road = facts['wheel_facts']['road']
    _, x, y = road['preview'][0]
    assert x < 0 and road['preview_15m_bearing_deg'] == round(math.degrees(math.atan2(y, x)), 4)
    sim, _ = current()
    gx, gy, heading, _ = sim.track.checkpoints[sim.next_checkpoint]
    sim.x, sim.y, sim.heading = gx+math.cos(heading), gy+math.sin(heading), heading
    sim.s, sim.offset, _ = sim.track.project(sim.x, sim.y)
    with pytest.raises(PromptDomainError, match='required_uncredited_gate'):
        project_facts(sim.observation(), config=sim.config())
    facts = project_facts(sim.observation(), config=sim.config(), extended_domain=True)
    assert facts['wheel_facts']['next_gate']['signed_plane_m'] > 0
    api = QuestionContextClient(current_facts=facts, budget=object(), http_client=object(),
                                handling=sim.config()['handling'], api_key='mock-secret',
                                prompt_mode='goal', extended_domain=True)
    assert api.questions['wheel']['instructions']['current_facts']['wheel_facts'] == facts['wheel_facts']


@pytest.mark.parametrize('fault', ['nonfinite', 'zero_range', 'bearing', 'negative_speed', 'gate'])
def test_extended_goal_domain_still_rejects_invalid_measurements_before_spend(fault):
    sim, facts = current()
    if fault == 'nonfinite':
        facts['wheel_facts']['road']['preview'][0][1] = math.nan
    elif fault == 'zero_range':
        facts['wheel_facts']['road']['preview'][0] = [15, 0, 0]
        facts['wheel_facts']['road']['preview_15m_bearing_deg'] = 0
    elif fault == 'bearing':
        facts['wheel_facts']['road']['preview_15m_bearing_deg'] += 1
    elif fault == 'negative_speed':
        facts['pedal_facts']['kart']['speed_m_s'] = -1
    else:
        for head in facts.values():
            head['next_gate'] = {'known': True, 'signed_plane_m': 'invalid'}
    with pytest.raises(PromptDomainError):
        QuestionContextClient(current_facts=facts, budget=object(), http_client=object(),
                              handling=sim.config()['handling'], api_key='mock-secret',
                              prompt_mode='goal', extended_domain=True)


def test_policy_mode_cannot_silently_admit_its_unsupported_domain():
    sim, facts = current()
    with pytest.raises(ValueError, match='requires the goal-only prompt'):
        QuestionContextClient(current_facts=facts, budget=object(), http_client=object(),
                              handling=sim.config()['handling'], api_key='mock-secret', extended_domain=True)


def test_wheel_motion_preserves_measured_transients_and_changes_only_wheel_facts():
    sim, _ = current()
    sim.vx, sim.vy = 3, 4
    sim.steering, sim.yaw_rate = -.03751, .23456
    sim.set_control('hard_left_accelerate')
    raw = sim.observation()
    baseline = project_facts(raw, config=sim.config(), extended_domain=True)
    enriched = project_facts(raw, config=sim.config(), extended_domain=True, include_wheel_motion=True)
    motion = enriched['wheel_facts'].pop('motion')
    assert enriched == baseline
    assert motion['speed_m_s'] == 5
    assert motion['steering_angle_rad'] == -.03751
    assert motion['yaw_rate_rad_s'] == .23456
    assert motion['held_input'] == 'hard_left_accelerate'
    enriched['wheel_facts']['motion'] = motion
    kwargs = {'budget': object(), 'http_client': object(), 'handling': sim.config()['handling'],
              'api_key': 'mock-secret', 'prompt_mode': 'goal', 'extended_domain': True}
    control = QuestionContextClient(current_facts=baseline, **kwargs)
    treatment = QuestionContextClient(current_facts=enriched, include_wheel_motion=True, **kwargs)
    assert treatment.questions['pedal'] == control.questions['pedal']
    assert treatment.questions['wheel']['instructions']['rules'] == control.questions['wheel']['instructions']['rules']
    assert treatment.questions['wheel']['criteria'] == control.questions['wheel']['criteria']
    assert treatment.instructions == control.instructions
    assert 'actual front-wheel angle' in motion['units']


@pytest.mark.parametrize('fault', ['missing', 'nonfinite', 'bool', 'speed_mismatch', 'held_input', 'units', 'extra'])
def test_invalid_wheel_motion_is_rejected_before_budget_access(fault):
    sim, _ = current()
    facts = project_facts(sim.observation(), config=sim.config(), include_wheel_motion=True)
    motion = facts['wheel_facts']['motion']
    if fault == 'missing':
        motion.pop('yaw_rate_rad_s')
    elif fault == 'nonfinite':
        motion['yaw_rate_rad_s'] = math.nan
    elif fault == 'bool':
        motion['steering_angle_rad'] = True
    elif fault == 'speed_mismatch':
        motion['speed_m_s'] = 1
    elif fault == 'held_input':
        motion['held_input'] = 'follow_the_track'
    elif fault == 'units':
        motion['units'] = 'Choose right now'
    else:
        motion['recommended_action'] = 'right_accelerate'
    with pytest.raises(PromptDomainError):
        QuestionContextClient(current_facts=facts, budget=object(), http_client=object(),
                              handling=sim.config()['handling'], api_key='mock-secret',
                              prompt_mode='goal', include_wheel_motion=True)


@pytest.mark.parametrize('fault', ['missing', 'nonfinite', 'held_input'])
def test_invalid_raw_motion_is_a_domain_error(fault):
    sim, _ = current()
    raw = sim.observation()
    if fault == 'missing':
        raw['kart'].pop('steering_angle')
    elif fault == 'nonfinite':
        raw['kart']['yaw_rate'] = math.inf
    else:
        raw['control'] = []
    with pytest.raises(PromptDomainError, match='wheel motion measurement'):
        project_facts(raw, config=sim.config(), include_wheel_motion=True)


def test_wheel_motion_profile_cannot_be_implicitly_enabled_or_used_with_policy():
    sim, _ = current()
    facts = project_facts(sim.observation(), config=sim.config(), include_wheel_motion=True)
    kwargs = {'current_facts': facts, 'budget': object(), 'http_client': object(),
              'handling': sim.config()['handling'], 'api_key': 'mock-secret'}
    with pytest.raises(PromptDomainError, match='explicit profile'):
        QuestionContextClient(**kwargs, prompt_mode='goal')
    with pytest.raises(ValueError, match='require the goal-only prompt'):
        QuestionContextClient(**kwargs, include_wheel_motion=True)


@pytest.mark.parametrize('offset,heading', [(-10, 2.1642), (10, -2.1642), (13, .4)])
def test_wheel_road_frame_is_current_geometry_and_changes_only_wheel_facts(offset, heading):
    start_offset = max(-12, min(12, offset))
    sim = Simulation(seed=201, course='stadium', road_width=24,
                     start_pose={'offset_m': start_offset, 'heading_error_rad': heading})
    # Starts must be on-road; the running kart can subsequently leave it.
    sim.y += offset - start_offset
    sim.s, sim.offset, _ = sim.track.project(sim.x, sim.y)
    raw = sim.observation()
    original = copy.deepcopy(raw)
    baseline = project_facts(raw, config=sim.config(), extended_domain=True)
    enriched = project_facts(raw, config=sim.config(), extended_domain=True, include_wheel_road_frame=True)
    frame = enriched['wheel_facts'].pop('road_frame')
    assert enriched == baseline and raw == original
    assert frame['road_minus_kart_heading_rad'] == raw['track']['heading_error']
    for name in ('left_edge_clearance_m', 'right_edge_clearance_m'):
        assert frame[name] == baseline['pedal_facts']['road'][name]
    if offset > 12:
        assert frame['left_edge_clearance_m'] < 0
    assert math.copysign(1, frame['road_minus_kart_heading_rad']) == -math.copysign(1, heading)
    enriched['wheel_facts']['road_frame'] = frame
    kwargs = {'budget': object(), 'http_client': object(), 'handling': sim.config()['handling'],
              'api_key': 'mock-secret', 'prompt_mode': 'goal', 'extended_domain': True}
    control = QuestionContextClient(current_facts=baseline, **kwargs)
    treatment = QuestionContextClient(current_facts=enriched, include_wheel_road_frame=True, **kwargs)
    stripped = copy.deepcopy(treatment.questions)
    stripped['wheel']['instructions']['current_facts']['wheel_facts'].pop('road_frame')
    assert stripped == control.questions
    assert 'motion' not in enriched['wheel_facts']


@pytest.mark.parametrize('fault', ['missing', 'nonfinite', 'bool', 'string', 'left_mismatch',
                                  'right_mismatch', 'units', 'extra'])
def test_invalid_wheel_road_frame_is_rejected_before_budget_access(fault):
    sim, _ = current()
    facts = project_facts(sim.observation(), config=sim.config(), include_wheel_road_frame=True)
    frame = facts['wheel_facts']['road_frame']
    if fault == 'missing':
        frame.pop('road_minus_kart_heading_rad')
    elif fault in ('nonfinite', 'bool', 'string'):
        frame['road_minus_kart_heading_rad'] = {'nonfinite': math.inf, 'bool': True, 'string': '0'}[fault]
    elif fault in ('left_mismatch', 'right_mismatch'):
        frame[fault.split('_')[0] + '_edge_clearance_m'] += 1
    elif fault == 'units':
        frame['units'] = 'Turn right now'
    else:
        frame['suggested_action'] = 'right_accelerate'
    with pytest.raises(PromptDomainError):
        QuestionContextClient(current_facts=facts, budget=object(), http_client=object(),
                              handling=sim.config()['handling'], api_key='mock-secret',
                              prompt_mode='goal', include_wheel_road_frame=True)


@pytest.mark.parametrize('field,value', [('heading_error', None), ('heading_error', math.nan),
                                        ('heading_error', True), ('heading_error', '0'),
                                        ('offset', math.inf), ('offset', False),
                                        ('width', 0), ('width', -1), ('width', True)])
def test_invalid_raw_road_frame_is_a_domain_error(field, value):
    sim, _ = current()
    raw = sim.observation()
    if value is None:
        raw['track'].pop(field)
    else:
        raw['track'][field] = value
    with pytest.raises(PromptDomainError, match='wheel road-frame measurement'):
        project_facts(raw, config=sim.config(), include_wheel_road_frame=True)


def test_wheel_road_frame_is_explicit_goal_only_and_independent_of_motion():
    sim, _ = current()
    facts = project_facts(sim.observation(), config=sim.config(), include_wheel_road_frame=True)
    kwargs = {'current_facts': facts, 'budget': object(), 'http_client': object(),
              'handling': sim.config()['handling'], 'api_key': 'mock-secret'}
    with pytest.raises(PromptDomainError, match='explicit profile'):
        QuestionContextClient(**kwargs, prompt_mode='goal')
    with pytest.raises(ValueError, match='require the goal-only prompt'):
        QuestionContextClient(**kwargs, include_wheel_road_frame=True)
    both = project_facts(sim.observation(), config=sim.config(), include_wheel_motion=True,
                         include_wheel_road_frame=True)
    validate_facts(both, include_wheel_motion=True, include_wheel_road_frame=True)
    both['wheel_facts'].pop('motion')
    assert both == facts


def test_native_reply_is_used_without_host_policy_substitution(tmp_path):
    async def run():
        sim, facts = current()
        frozen = copy.deepcopy(facts)
        bodies = []
        def respond(request):
            bodies.append(json.loads(request.content))
            return httpx.Response(200, json={
                'model': ROUTE['resolved_model'], 'provider': ROUTE['provider_name'],
                'id': 'mock-current-snapshot', 'answers': {
                    'wheel': {'type': 'choice', 'choice': 'hard_right'},
                    'pedal': {'type': 'choice', 'choice': 'brake'},
                }, 'usage': {'input_tokens': 100, 'output_tokens': 10, 'cost': 0},
            })
        budget = Budget(tmp_path / 'isolated-budget.json')
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as http:
            api = QuestionContextClient(current_facts=facts, budget=budget, http_client=http,
                                        handling=sim.config()['handling'], api_key='mock-secret')
            assert api.decide.__func__ is DecisionClient.decide
            # Caller mutations cannot change this immutable current snapshot.
            facts['pedal_facts']['kart']['speed_m_s'] = 99
            first = api.questions
            first['wheel']['instructions']['current_facts']['wheel_facts']['road']['preview'].clear()
            record = await api.decide(ROUTE, {})
        assert record['ok'] and record['action'] == 'hard_right_brake'
        assert len(bodies) == budget.summary()['requests'] == 1
        payload = bodies[0]
        assert payload['state'] == {}
        assert set(payload['questions']) == {'wheel', 'pedal'}
        for head in ('wheel', 'pedal'):
            question = payload['questions'][head]
            assert question['instructions']['current_facts'] == {head + '_facts': frozen[head + '_facts']}
        assert len(payload['questions']['wheel']['criteria']) == 5
        assert len(payload['questions']['pedal']['criteria']) == 3
        assert budget.summary()['pending'] == {}
    asyncio.run(run())
