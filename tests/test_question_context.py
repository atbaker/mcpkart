"""Question-local prompt contracts; all HTTP is explicitly mocked."""
import asyncio
import copy
import json
import math

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
