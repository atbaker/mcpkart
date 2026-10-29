"""Free pre-actuation guards for the experimental recorded driver."""
import asyncio
import copy
import json
import math

import httpx
import pytest

from mcpkart.decisions import Budget
from mcpkart.question_context import PromptDomainError
from mcpkart.question_context_driver import QuestionContextDriver, WireCapture
from mcpkart.sim import Simulation

ROUTE = {
    'model': 'typesafe/jev-1.14', 'resolved_model': 'typesafe/jev-1.14-test',
    'provider': 'typesafe', 'provider_name': 'TypeSafe',
    'price_input_per_token': 0, 'price_output_per_token': 0,
    'price_per_request': 0, 'context_length': 262144, 'max_completion_tokens': 235929,
}


def response():
    return {'id': 'mock-native-1', 'model': ROUTE['resolved_model'], 'provider': 'TypeSafe',
            'answers': {'wheel': {'type': 'choice', 'choice': 'hard_right'},
                        'pedal': {'type': 'choice', 'choice': 'brake'}},
            'usage': {'input_tokens': 100, 'output_tokens': 10, 'cost': 0}}


def simulation():
    return Simulation(seed=43, course='stadium', road_width=24, max_speed=12,
                      max_steering_angle=.12, reset_after_s=3)


async def with_driver(tmp_path, handler, task, *, prompt_mode='policy', extended_domain=False,
                      include_wheel_motion=False, include_wheel_road_frame=False):
    capture = WireCapture()
    budget = Budget(tmp_path / 'isolated-budget.json')
    sim = simulation()
    async with httpx.AsyncClient(transport=httpx.MockTransport(handler), event_hooks=capture.hooks) as http:
        driver = QuestionContextDriver(budget=budget, http=http, capture=capture, route=ROUTE,
                                       config=sim.config(), output=tmp_path / 'run', api_key='mock-secret',
                                       prompt_mode=prompt_mode, extended_domain=extended_domain,
                                       include_wheel_motion=include_wheel_motion,
                                       include_wheel_road_frame=include_wheel_road_frame)
        return await task(driver, sim, budget)


@pytest.mark.parametrize('prompt_mode', ['policy', 'goal'])
def test_valid_reply_is_recorded_and_used_unchanged(tmp_path, prompt_mode):
    def handler(request):
        payload = json.loads(request.content)
        assert payload['state'] == {} and set(payload['questions']) == {'wheel', 'pedal'}
        if prompt_mode == 'goal':
            assert 'FIXED POLICY' not in json.dumps(payload)
        return httpx.Response(200, json=response())
    async def task(driver, sim, budget):
        record = await driver.decide(ROUTE, sim.observation())
        assert record['ok'] and record['action'] == 'hard_right_brake'
        assert record['budget_before']['requests'] == 0 and record['budget_after']['requests'] == 1
        assert record['physical_packet']['pedal_facts']['kart']['speed_m_s'] == 0
        assert driver.questions['wheel']['instructions'].get('current_facts') is None
        evidence = json.loads((tmp_path / 'run/calls/00000.json').read_text())
        assert evidence['wire']['saved_unmodified'] and len(evidence['wire']['responses']) == 1
        assert budget.summary()['pending'] == {}
    asyncio.run(with_driver(tmp_path, handler, task, prompt_mode=prompt_mode))


@pytest.mark.parametrize('fault', ['missing_id', 'empty_id', 'extra_head', 'missing_head',
                                  'bad_type', 'list_choice', 'wrong_model', 'wrong_provider',
                                  'missing_cost', 'missing_tokens', 'refusal', 'status_202'])
def test_invalid_reply_never_returns_a_control_and_stops_future_posts(tmp_path, fault):
    body = response()
    status = 200
    if fault == 'missing_id':
        body.pop('id')
    elif fault == 'empty_id':
        body['id'] = ' '
    elif fault == 'extra_head':
        body['answers']['other'] = {'type': 'choice', 'choice': 'left'}
    elif fault == 'missing_head':
        body['answers'].pop('pedal')
    elif fault == 'bad_type':
        body['answers']['wheel']['type'] = 'string'
    elif fault == 'list_choice':
        body['answers']['wheel']['choice'] = ['hard_right']
    elif fault == 'wrong_model':
        body['model'] = 'different-model'
    elif fault == 'wrong_provider':
        body['provider'] = 'different-provider'
    elif fault == 'missing_cost':
        body['usage'].pop('cost')
    elif fault == 'missing_tokens':
        body['usage'].pop('output_tokens')
    elif fault == 'refusal':
        body['answers']['pedal']['refusal'] = 'no'
    else:
        status = 202
    posts = []
    def handler(request):
        posts.append(request)
        return httpx.Response(status, json=body)
    async def task(driver, sim, budget):
        record = await driver.decide(ROUTE, sim.observation())
        assert not record['ok'] and record['action'] is None
        with pytest.raises(RuntimeError, match='stopped'):
            await driver.decide(ROUTE, sim.observation())
        assert len(posts) == budget.summary()['requests'] == 1
        assert budget.summary()['pending'] == {}
    asyncio.run(with_driver(tmp_path, handler, task))


def test_duplicate_response_id_is_rejected_before_second_actuation(tmp_path):
    async def task(driver, sim, budget):
        first = await driver.decide(ROUTE, sim.observation())
        second = await driver.decide(ROUTE, sim.observation())
        assert first['ok'] and not second['ok'] and second['action'] is None
        assert 'missing_or_duplicate_response_id' in second['wrapper_failures']
        assert budget.summary()['requests'] == 2
    asyncio.run(with_driver(tmp_path, lambda r: httpx.Response(200, json=response()), task))


def test_domain_exit_makes_no_post_and_no_reservation(tmp_path):
    def handler(request):
        raise AssertionError('Domain exits must not post')
    async def task(driver, sim, budget):
        sim.heading += math.pi
        with pytest.raises(PromptDomainError, match='not_forward'):
            await driver.decide(ROUTE, sim.observation())
        assert budget.summary()['requests'] == 0
        marker = json.loads((tmp_path / 'run/domain-stop.json').read_text())
        assert marker['quality_failure'] and not marker['model_post_started_for_this_snapshot']
    asyncio.run(with_driver(tmp_path, handler, task))


def test_extended_goal_driver_posts_behind_pose_and_uses_only_the_native_reply(tmp_path):
    posts = []
    def handler(request):
        posts.append(json.loads(request.content))
        return httpx.Response(200, json=response())
    async def task(driver, sim, budget):
        sim.heading += math.pi
        record = await driver.decide(ROUTE, sim.observation())
        assert record['ok'] and record['action'] == 'hard_right_brake'
        road = record['physical_packet']['wheel_facts']['road']
        assert road['preview'][0][1] < 0 and abs(road['preview_15m_bearing_deg']) > 90
        assert len(posts) == budget.summary()['requests'] == 1
        assert not (tmp_path / 'run/domain-stop.json').exists()
        assert 'FIXED POLICY' not in json.dumps(posts[0])
    asyncio.run(with_driver(tmp_path, handler, task, prompt_mode='goal', extended_domain=True))


def test_motion_driver_records_actual_state_and_uses_native_answer_unchanged(tmp_path):
    posts = []
    def handler(request):
        posts.append(json.loads(request.content))
        return httpx.Response(200, json=response())
    async def task(driver, sim, budget):
        sim.steering, sim.yaw_rate = -.03, .21
        sim.set_control('hard_left_accelerate')
        record = await driver.decide(ROUTE, sim.observation())
        assert record['ok'] and record['action'] == 'hard_right_brake'
        motion = record['physical_packet']['wheel_facts']['motion']
        assert motion['steering_angle_rad'] == -.03 and motion['yaw_rate_rad_s'] == .21
        assert motion['held_input'] == 'hard_left_accelerate'
        assert posts[0]['questions']['wheel']['instructions']['current_facts']['wheel_facts']['motion'] == motion
        assert 'motion' not in posts[0]['questions']['pedal']['instructions']['current_facts']['pedal_facts']
        assert len(posts) == budget.summary()['requests'] == 1
    asyncio.run(with_driver(tmp_path, handler, task, prompt_mode='goal', extended_domain=True,
                           include_wheel_motion=True))


def test_road_frame_driver_records_current_geometry_and_keeps_native_answer(tmp_path):
    posts = []
    def handler(request):
        posts.append(json.loads(request.content))
        return httpx.Response(200, json=response())
    async def task(driver, sim, budget):
        raw = sim.observation()
        record = await driver.decide(ROUTE, raw)
        assert record['ok'] and record['action'] == 'hard_right_brake'
        frame = record['physical_packet']['wheel_facts']['road_frame']
        assert frame['road_minus_kart_heading_rad'] == raw['track']['heading_error']
        assert posts[0]['questions']['wheel']['instructions']['current_facts']['wheel_facts']['road_frame'] == frame
        assert 'motion' not in record['physical_packet']['wheel_facts']
        assert len(posts) == budget.summary()['requests'] == 1
    asyncio.run(with_driver(tmp_path, handler, task, prompt_mode='goal', extended_domain=True,
                           include_wheel_road_frame=True))


@pytest.mark.parametrize('fault', ['missing', 'nonfinite', 'bool'])
def test_invalid_driver_road_geometry_stops_before_reservation_and_post(tmp_path, fault):
    def handler(request):
        raise AssertionError('Invalid geometry must not POST')
    async def task(driver, sim, budget):
        raw = sim.observation()
        if fault == 'missing':
            raw['track'].pop('heading_error')
        else:
            raw['track']['heading_error'] = math.nan if fault == 'nonfinite' else False
        before = budget.path.read_bytes()
        with pytest.raises(PromptDomainError):
            await driver.decide(ROUTE, raw)
        assert budget.path.read_bytes() == before
        assert driver.count == 0
    asyncio.run(with_driver(tmp_path, handler, task, prompt_mode='goal', extended_domain=True,
                           include_wheel_road_frame=True))


def test_external_ledger_change_prevents_a_post(tmp_path):
    def handler(request):
        raise AssertionError('Changed ledger must not post')
    async def task(driver, sim, budget):
        state = copy.deepcopy(budget.summary())
        state.pop('reserved_usd');state.pop('reserved_tokens');state.pop('remaining_usd')
        state['requests'] += 1
        budget.path.write_text(json.dumps(state))
        with pytest.raises(RuntimeError, match='shared budget changed'):
            await driver.decide(ROUTE, sim.observation())
    asyncio.run(with_driver(tmp_path, handler, task))


def test_overlapping_decisions_are_rejected_without_an_extra_post(tmp_path):
    async def run():
        entered, release = asyncio.Event(), asyncio.Event()
        async def handler(request):
            entered.set()
            await release.wait()
            return httpx.Response(200, json=response())
        async def task(driver, sim, budget):
            first = asyncio.create_task(driver.decide(ROUTE, sim.observation()))
            await entered.wait()
            with pytest.raises(RuntimeError, match='already deciding'):
                await driver.decide(ROUTE, sim.observation())
            release.set()
            assert (await first)['ok']
            assert budget.summary()['requests'] == 1
        await with_driver(tmp_path, handler, task)
    asyncio.run(run())
