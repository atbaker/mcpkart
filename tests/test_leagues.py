"""Course/speed experiments preserve direct controls and recorded physics."""
import base64
import io
import json
import math
from pathlib import Path
from xml.etree import ElementTree

import httpx
import pytest
from fastmcp import Client
from PIL import Image

from mcpkart.bench import driving_evidence, reference_durations, reference_trial, tool
from mcpkart.decisions import Budget, DecisionClient, geometry_control_description
from mcpkart.process_runtime import ProcessRaceRuntime
from mcpkart.scene import ORIGIN, scene_geometry
from mcpkart.sim import ACTIONS, Simulation, Track, scripted_action
from mcpkart.web import create_app


def test_original_track_and_handling_contract_remains_exact():
    reference = json.loads(Path('scripts/clock_helpers/reference.json').read_text())
    assert Simulation().config() == reference['trials'][0]['config']


@pytest.mark.parametrize('course', ['oval','circle'])
def test_symmetric_courses_reverse_by_reflection(course):
    ccw, cw = Track(course), Track(course+'_clockwise')
    assert len(ccw.points) == len(cw.points) == 256
    assert ccw.length == pytest.approx(cw.length)
    for (x,y),(rx,ry),left,right in zip(ccw.points,cw.points,ccw.curvatures,cw.curvatures):
        assert (x,y) == pytest.approx((-rx,ry))
        assert left > 0 and right < 0


@pytest.mark.parametrize('setup', [{'max_speed':0}, {'max_speed':math.nan}, {'max_speed':True},
                                  {'road_width':-1}, {'course':'missing'}, {'max_steering_angle':0}])
def test_invalid_race_settings_are_rejected(setup):
    with pytest.raises(ValueError):
        Simulation(**setup)


def test_speed_class_clamps_actual_velocity_without_steering_assistance():
    sim=Simulation(max_speed=8,reset_after_s=None)
    heading=sim.heading
    sim.set_control('straight_accelerate')
    for _ in range(90):
        sim.step()
        assert sim.speed <= 8+1e-12
    assert sim.max_speed_seen == pytest.approx(8)
    assert sim.heading == pytest.approx(heading,abs=1e-12) and sim.action_id == 'straight_accelerate'


@pytest.mark.parametrize('course', ['oval','oval_clockwise','circle','circle_clockwise',
                                  'stadium','stadium_clockwise'])
def test_custom_courses_have_paired_direct_control_references(course):
    setup={'course':course,'max_speed':8,'road_width':12,'max_steering_angle':.12}
    result=reference_trial(0,deadline=180,race_setup=setup)
    assert result['finished'] and result['summary']['checkpoints_passed']==120
    assert result['summary']['resets']==0 and result['summary']['offroad_time']==0
    replay=Simulation.from_config(result['config'])
    assert replay.config()==result['config']


def test_stadium_has_straights_tangent_curves_and_reflected_direction():
    ccw, cw = Track('stadium'), Track('stadium_clockwise')
    assert ccw.length == pytest.approx(120+60*math.pi, abs=.03)
    assert ccw.length == pytest.approx(cw.length)
    for (x,y),(rx,ry),left,right in zip(ccw.points,cw.points,ccw.curvatures,cw.curvatures):
        assert (x,y) == pytest.approx((-rx,ry))
        assert left == pytest.approx(-right,abs=1e-12)
    assert sum(abs(c) < 1e-8 for c in ccw.curvatures) > 70
    assert max(ccw.curvatures) == pytest.approx(1/30,rel=.005)
    assert min(ccw.curvatures) >= -1e-10


def test_scripted_reference_uses_actual_steering_range(monkeypatch):
    from mcpkart import bench

    calls=[]
    def checked(observation, *, max_steering_angle):
        calls.append(max_steering_angle)
        return scripted_action(observation,max_steering_angle=max_steering_angle)
    monkeypatch.setattr(bench,'scripted_action',checked)
    bench.reference_trial(0,deadline=.1,race_setup={'max_steering_angle':.12})
    assert calls and set(calls)=={.12}
    with pytest.raises(ValueError,match='steering range'):
        scripted_action(Simulation().observation(),max_steering_angle=0)


def test_near_field_retains_actual_points_and_pose_without_policy():
    sim=Simulation(course='stadium',max_speed=12,max_steering_angle=.12)
    raw=sim.observation(); state=driving_evidence(raw,'near_field',config=sim.config())
    expected=[p for p in raw['track']['lookahead'] if p['distance']<=15]
    assert len(state['road']['centre_points'])==len(expected)
    for source,point in zip(expected,state['road']['centre_points']):
        assert point['forward_m']==pytest.approx(source['x'],abs=.001)
        assert point['left_m']==pytest.approx(source['y'],abs=.001)
    assert state['kart']['nose_left_of_road_deg']==pytest.approx(
        -math.degrees(raw['track']['heading_error']),abs=.001)
    assert state['handling']['max_wheel_deg']==pytest.approx(math.degrees(.12),abs=.001)
    assert not {'future_bends','target_speed','recommended_action'} & state.keys()


def test_geometry_control_words_describe_vehicle_limits_without_selecting_input():
    handling=Simulation(max_steering_angle=.06).config()['handling']
    hard=geometry_control_description(ACTIONS['hard_left_accelerate'],handling)
    moderate=geometry_control_description(ACTIONS['left_accelerate'],handling)
    assert 'LEFT at 3.44 degrees' in hard and 'radius of 30.0 metres' in hard
    assert 'LEFT at 1.72 degrees' in moderate and 'radius of 60.0 metres' in moderate
    assert 'a straight nominal path' in geometry_control_description(ACTIONS['straight_coast'],handling)
    assert 'RIGHT at 3.44 degrees' in geometry_control_description(ACTIONS['hard_right_brake'],handling)
    original=Simulation().config()['handling']
    assert 'radius of 5.4 metres' in geometry_control_description(ACTIONS['hard_left_accelerate'],original)


@pytest.mark.parametrize('handling',[None,{}, {'max_steering_angle':True,'wheelbase':1.8},
                                     {'max_steering_angle':.06,'wheelbase':math.nan}])
def test_geometry_menu_rejects_missing_or_invalid_vehicle_before_spend(tmp_path,handling):
    budget=Budget(tmp_path/'budget.json')
    with pytest.raises(ValueError,match='Geometry control language'):
        DecisionClient(budget=budget,actions=ACTIONS,api_key='fake',control_language='geometry',handling=handling)
    assert budget.summary()['requests']==0


@pytest.mark.asyncio
async def test_geometry_menu_preserves_all_native_choices_and_racing_instructions(tmp_path):
    from mcpkart.decisions import DRIVING_INSTRUCTIONS

    handling=Simulation(max_steering_angle=.06).config()['handling']
    route={'model':'typesafe/jev-1.14','provider':'typesafe','provider_name':'TypeSafe','context_length':262144,
           'price_input_per_token':.000000042,'price_output_per_token':0,'max_completion_tokens':1}
    def respond(request):
        payload=json.loads(request.content);question=payload['questions']['control']
        assert question['instructions']==DRIVING_INSTRUCTIONS
        assert set(question['criteria'])==set(ACTIONS)
        assert 'radius of 30.0 metres' in question['criteria']['hard_right_coast']
        return httpx.Response(200,json={'model':route['model'],'provider':'TypeSafe',
                                       'answers':{'control':{'choice':'hard_right_coast'}},
                                       'usage':{'input_tokens':100,'output_tokens':1,'cost':.0000042}})
    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as http:
        client=DecisionClient(budget=Budget(tmp_path/'budget.json'),actions=ACTIONS,api_key='fake',http_client=http,
                              control_language='geometry',handling=handling,max_input_tokens=16384)
        result=await client.decide(route,{'synthetic_test':True})
    assert result['ok'] and result['action']=='hard_right_coast'
    assert result['control_language']=='geometry'


def test_reference_selection_rejects_a_different_speed_class(tmp_path):
    setup={'max_speed':8}
    result=reference_trial(0,deadline=180,race_setup=setup)
    path=tmp_path/'reference.json'
    path.write_text(json.dumps({'trials':[result]}))
    assert reference_durations(path,setup)[0]==result['elapsed']
    with pytest.raises(ValueError,match='Reference track/handling'):
        reference_durations(path)


@pytest.mark.asyncio
async def test_course_settings_reach_the_actual_python_physics_child(tmp_path):
    runtime=ProcessRaceRuntime()
    app=create_app(runtime=runtime,replay_root=tmp_path)
    setup={'course':'oval_clockwise','road_width':16,'max_speed':6,'max_steering_angle':.12}
    try:
        async with Client(app.state.mcp_server) as client:
            initial=await tool(client,'start_race',{'deadline':2,'race_setup':setup})
            assert initial['track']['width']==16
            await tool(client,'drive',{'race_id':initial['race_id'],'action_id':'straight_accelerate',
                                      'observation_tick':initial['tick'],'command_seq':1})
            report=await tool(client,'finish_race')
        assert report['config']==Simulation(**setup).config()
        assert report['process_provenance']['worker_module']=='mcpkart.physics_worker'
    finally:
        await runtime.close()


def test_svg_and_png_are_factual_equivalent_camera_views_with_valid_jev_image_size():
    sim=Simulation(course='oval',max_speed=8)
    raw=sim.observation()
    svg=driving_evidence(raw,'scene_svg',config=sim.config())
    png=driving_evidence(raw,'scene_image',config=sim.config())
    assert {k:v for k,v in svg.items() if k!='scene'}=={k:v for k,v in png.items() if k!='scene'}
    ElementTree.fromstring(svg['scene'])
    encoded=png['scene']['image_url']['url'].split(',',1)[1]
    image=Image.open(io.BytesIO(base64.b64decode(encoded)))
    assert image.size==(384,384) and image.size[0]*image.size[1]>=78400
    assert svg['handling']['max_speed_m_s']==8
    scene=scene_geometry(raw,sim.config())
    assert scene['kart'][0][1] < ORIGIN[1]  # Nose is screen-up.
    assert scene['left'][5][0] < scene['right'][5][0]


@pytest.mark.asyncio
async def test_image_budget_reserves_route_context_before_any_remote_call(tmp_path):
    route={'model':'typesafe/jev-1.14','provider':'typesafe','context_length':262144,
           'price_input_per_token':.000000042,'price_output_per_token':0,'max_completion_tokens':1}
    state=driving_evidence(Simulation().observation(),'scene_image')
    budget=Budget(tmp_path/'budget.json')
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r:pytest.fail('Unexpected request'))) as http:
        client=DecisionClient(budget=budget,actions=ACTIONS,api_key='fake',http_client=http,max_input_tokens=8192)
        with pytest.raises(ValueError,match='Image requests must reserve'):
            await client.decide(route,state)
    assert budget.summary()['requests']==0
