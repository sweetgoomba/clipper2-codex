from dataclasses import replace
import numpy as np
import pytest
from dance_highlight.services.segment import FrameRec,classify_main_scenes


def person(x=600.,y=300.,scale=1.):
    points=np.array([[0,0],[-3,-2],[3,-2],[-6,0],[6,0],[-10,15],[10,15],[-17,35],[17,35],[-18,55],[18,55],[-8,50],[8,50],[-8,90],[8,90],[-8,125],[8,125]],float)
    points=points*scale+[x,y]
    return dict(bbox=np.r_[points.min(axis=0)-5*scale,points.max(axis=0)+5*scale],pose_keypoints=np.c_[points,np.ones(17)])


def example(times=None,people=None):
    times=np.arange(7)/10 if times is None else times
    people=people or [person(600.),person(680.),person(760.)]
    first=people[0]
    rows=[FrameRec(float(t),1,first['bbox'].copy(),False,person_bboxes=[first['bbox'].copy()],person_head_keypoints=[first['pose_keypoints'][:5].copy()],person_pose_keypoints=[first['pose_keypoints'].copy()]) for t in times]
    observed={round(t*10):people for t in times}
    return rows,observed


def refine(rows,observed,cuts=()):
    from dance_highlight.services.native_scene import refine_with_scene_observations
    return refine_with_scene_observations(classify_main_scenes(rows,(1920,1080)),observed,video_size=(1920,1080),fps=10.,cut_frames=cuts)


def test_separate_native_ensemble_observations_preserve_original_identity_geometry():
    rows,observed=example()
    assert all(r.scene_kind=='main' for r in classify_main_scenes(rows,(1920,1080)))
    result,audit=refine(rows,observed)
    assert all(r.scene_kind=='group' and r.main_id is None for r in result)
    assert all(r.main_id==1 and len(r.person_bboxes)==1 for r in rows)
    assert all(np.array_equal(r.person_bboxes[0],old.person_bboxes[0]) and len(r.person_bboxes)==1 for r,old in zip(result,rows))
    assert all(len(r.group_bboxes)==3 for r in result)
    assert len(audit['changes'])==len(rows)


def test_person_detection_dropout_does_not_mean_empty_scene_when_direct_group_is_observed():
    rows,observed=example()
    rows=[replace(r,main_id=None,main_bbox=None,person_bboxes=[],person_head_keypoints=[],person_pose_keypoints=[]) for r in rows]
    assert all(r.scene_kind=='group' for r in refine(rows,observed)[0])


@pytest.mark.parametrize('case',['foreground','crouch','missing_legs','clipped_body','no_heads','duplicate_chain','empty'])
def test_insufficient_or_foreground_native_evidence_cannot_remove_main(case):
    rows,observed=example();people=observed[0]
    if case=='foreground':people.append(person(900.,200.,4.))
    if case=='crouch':
        for p in people:
            p['pose_keypoints'][13:15,0]+=150.
            p['bbox'][2]+=150.
    if case=='missing_legs':people[0]['pose_keypoints'][13:,2]=0.
    if case=='clipped_body':
        clipped=person(960.,0.);clipped['bbox'][1]=0.;clipped['pose_keypoints'][13:,2]=0.;people.append(clipped)
    if case=='no_heads':
        for p in people:p['pose_keypoints'][:5,2]=0.
    if case=='duplicate_chain':
        people=[person(600.+i*8.) for i in range(5)]
        for f in observed:observed[f]=people
    if case=='empty':
        for f in observed:observed[f]=[]
    result,audit=refine(rows,observed)
    assert all(r.scene_kind=='main' for r in result)
    assert audit['changes']==[]


def test_native_background_cannot_overrule_original_large_observed_head():
    rows,observed=example();p=person(600.,100.,4.)
    rows=[replace(r,person_bboxes=[p['bbox']],person_head_keypoints=[p['pose_keypoints'][:5]],person_pose_keypoints=[p['pose_keypoints']]) for r in rows]
    assert all(r.scene_kind=='main' for r in refine(rows,observed)[0])


def test_short_new_foreground_and_cut_are_not_filled_as_detection_dropouts():
    rows,observed=example(np.arange(20)/10);observed[8]=[person(700.,100.,4.)];observed[9]=[]
    result,_=refine(rows,observed)
    assert result[8].scene_kind==result[9].scene_kind=='main'
    assert all(result[i].scene_kind=='group' for i in [0,7,10,19])
    rows,observed=example([0.,.1,.2,.3]);result,_=refine(rows,observed,cuts=[2])
    assert all(r.scene_kind=='main' for r in result)


def test_bounded_partial_detection_retains_group_without_inventing_people():
    rows,observed=example(np.arange(20)/10)
    for f in [7,8,9,10]:observed[f]=[observed[f][0]]
    result,_=refine(rows,observed)
    assert all(r.scene_kind=='group' for r in result)
    assert len(result[8].group_bboxes)==1


def test_missing_cut_inventory_and_sampling_gap_cannot_supply_temporal_proof():
    rows,observed=example();assert all(r.scene_kind=='main' for r in refine(rows,observed,cuts=None)[0])
    rows,observed=example([0.,.5]);assert all(r.scene_kind=='main' for r in refine(rows,observed)[0])


def test_continuous_main_six_seconds_has_no_new_duration_cap():
    from dance_highlight.services.segment import build_raw_main_segments
    rows,observed=example(np.arange(61)/10,people=[person(800.,100.,4.)])
    result,_=refine(rows,observed)
    assert [(s.start,s.end) for s in build_raw_main_segments(result)]==[(0.,6.)]


@pytest.mark.parametrize('case',['empty_head_foreground','invalid_geometry'])
def test_unobserved_large_competitor_is_not_silently_ignored(case):
    rows,observed=example();p=person(1000.,100.,4.)
    if case=='empty_head_foreground':p['pose_keypoints'][:,2]=0.
    else:p['pose_keypoints']=np.empty((0,3))
    for people in {id(v):v for v in observed.values()}.values():people.append(p)
    assert all(r.scene_kind=='main' for r in refine(rows,observed)[0])


def test_scene_adapter_reads_actual_requested_frames_and_keeps_base_geometry(tmp_path):
    import cv2
    from dance_highlight.services.native_scene import refine_native_scenes
    rows,observed=example();base=classify_main_scenes(rows,(1920,1080));source=tmp_path/'scene.avi'
    video=cv2.VideoWriter(str(source),cv2.VideoWriter_fourcc(*'MJPG'),10.,(1920,1080));assert video.isOpened()
    for _ in rows:video.write(np.zeros((1080,1920,3),np.uint8))
    video.release();calls=[]
    class Pose:
        def run_pose_on_frame(self,image,*,image_size):
            calls.append((image.shape,image_size));return observed[0]
    result,audit=refine_native_scenes(base,source,10.,Pose(),video_size=(1920,1080),cut_frames=[])
    assert audit['reason']=='complete' and len(calls)==len(rows)
    assert all(shape==(1080,1920,3) and size==1920 for shape,size in calls)
    assert all(r.scene_kind=='group' for r in result)
    assert all(r.main_id==1 and len(r.person_bboxes)==1 for r in base)
    assert audit['requested_frames']==list(range(7))


@pytest.mark.parametrize('failure',['short_source','wrong_fps','inference'])
def test_source_or_model_failure_keeps_all_original_scene_decisions(tmp_path,failure):
    import cv2
    from dance_highlight.services.native_scene import refine_native_scenes
    rows,observed=example();base=classify_main_scenes(rows,(1920,1080));source=tmp_path/'scene.avi'
    video=cv2.VideoWriter(str(source),cv2.VideoWriter_fourcc(*'MJPG'),20. if failure=='wrong_fps' else 10.,(1920,1080));assert video.isOpened()
    for _ in rows[:3] if failure=='short_source' else rows:video.write(np.zeros((1080,1920,3),np.uint8))
    video.release()
    class Pose:
        def run_pose_on_frame(self,image,*,image_size):
            if failure=='inference':raise RuntimeError('model failed')
            return observed[0]
    result,audit=refine_native_scenes(base,source,10.,Pose(),video_size=(1920,1080),cut_frames=[])
    assert result is base and audit['reason']!='complete' and audit['changes']==[]


def test_detail_pose_size_does_not_leak_into_subsequent_base_pose_call():
    from dance_highlight.services.pose_engine import PoseEngine
    from dance_highlight.services.config import DanceConfig
    engine=object.__new__(PoseEngine);engine.config=DanceConfig();sizes=[]
    def model(image,**kwargs):sizes.append(kwargs.get('imgsz'));return []
    engine._model=model;img=np.zeros((20,20,3),np.uint8)
    engine.run_pose_on_frame(img)
    engine.run_pose_on_frame(img,image_size=1920)
    engine.run_pose_on_frame(img)
    assert sizes==[640,1920,640]


def test_detail_detector_cannot_erase_original_large_head_hidden_torso():
    rows,observed=example();p=person(700.,100.,4.);p['pose_keypoints'][:5,2]=0.
    rows=[replace(r,main_bbox=p['bbox'],person_bboxes=[p['bbox']],person_head_keypoints=[p['pose_keypoints'][:5]],person_pose_keypoints=[p['pose_keypoints']]) for r in rows]
    result,audit=refine(rows,observed)
    assert all(r.scene_kind=='main' for r in result)
    assert audit['changes']==[]


def test_late_audit_failure_cannot_report_unapplied_scene_changes(tmp_path,monkeypatch):
    import cv2
    from types import SimpleNamespace
    from dance_highlight.services import face_models
    from dance_highlight.services.native_scene import refine_native_scenes
    rows,observed=example();base=classify_main_scenes(rows,(1920,1080));source=tmp_path/'scene.avi'
    video=cv2.VideoWriter(str(source),cv2.VideoWriter_fourcc(*'MJPG'),10.,(1920,1080));assert video.isOpened()
    for _ in rows:video.write(np.zeros((1080,1920,3),np.uint8))
    video.release();model=tmp_path/'model.pt';model.write_bytes(b'model')
    def fail_hash(path):raise OSError('file became unavailable')
    monkeypatch.setattr(face_models,'sha256_file',fail_hash)
    class Pose:
        config=SimpleNamespace(yolo_model_path=str(model),yolo_conf=.25,yolo_iou=.7,yolo_device='cpu')
        def run_pose_on_frame(self,image,*,image_size):return observed[0]
    result,audit=refine_native_scenes(base,source,10.,Pose(),video_size=(1920,1080),cut_frames=[])
    assert result is base and audit['reason']=='native_scene_unavailable'
    assert audit['changes']==[] and audit.get('runs',[])==[]


def lower_partial_person(bottom=1080.):
    points = np.zeros((17, 3))
    points[0] = (900., 1030., .9)
    points[5] = (885., 1060., .9)
    points[6] = (915., 1060., .9)
    return dict(bbox=np.array([875., 1010., 925., bottom]), pose_keypoints=points)


@pytest.mark.parametrize('bottom', [1079.6, 1080.])
def test_bottom_audience_below_complete_ensemble_does_not_cancel_group(bottom):
    rows, observed = example()
    audience = lower_partial_person(bottom)
    observed[0].append(audience)
    result, audit = refine(rows, observed)
    assert all(r.scene_kind == 'group' and len(r.group_bboxes) == 3 for r in result)
    assert len(audit['lower_partial_exclusions']) == len(rows)
    assert len(observed[0]) == 4


@pytest.mark.parametrize('case', ['large', 'overlap', 'lower_body', 'not_bottom',
                                  'no_head', 'head_outside', 'side_clipped', 'only_two_full'])
def test_cropped_foreground_cannot_be_ignored_as_bottom_audience(case):
    people = [person(x, 850.) for x in (600., 680., 760.)]
    candidate = lower_partial_person()
    if case == 'large': candidate['bbox'][0:3:2] = [700., 1000.]
    if case == 'overlap': candidate['bbox'][1] = 920.
    if case == 'lower_body': candidate['pose_keypoints'][11] = [900., 1070., .8]
    if case == 'not_bottom':
        candidate['bbox'] = np.array([875., 0., 925., 70.])
        candidate['pose_keypoints'][:, 1] -= 1010.
    if case == 'no_head': candidate['pose_keypoints'][0, 2] = 0.
    if case == 'head_outside': candidate['pose_keypoints'][0, 0] = 500.
    if case == 'side_clipped':
        candidate['bbox'][[0, 2]] = [-20., 100.]
        candidate['pose_keypoints'][:, 0] -= 850.
    if case == 'only_two_full': people = people[:2]
    people.append(candidate)
    rows, observed = example(people=people)
    result, audit = refine(rows, observed)
    assert all(r.scene_kind == 'main' for r in result)
    assert not audit.get('lower_partial_exclusions', [])


def test_saved_distant_ensemble_survives_unobserved_upper_stage_decoration():
    import json
    from pathlib import Path
    from dance_highlight.services.native_scene import refine_with_scene_observations
    fixture = json.loads((Path(__file__).parent / 'fixtures' /
                          'dance_native_upper_background.json').read_text())
    rows, observed = [], {}
    for sample in fixture['rows']:
        p, scene = sample['pose'], sample['scene_before']
        box = np.asarray(p['candidate_main_bbox']) if p['candidate_main_bbox'] is not None else None
        rows.append(FrameRec(p['time_seconds'], p['candidate_main_id'] if scene == 'main' else None,
            box if scene == 'main' else None, scene == 'group',
            person_bboxes=[np.asarray(b) for b in p['body_boxes']],
            person_head_keypoints=[np.asarray(k) for k in p['head_keypoints']],
            person_pose_keypoints=[np.asarray(k) for k in p['pose_keypoints']],
            scene_kind=scene, candidate_main_id=p['candidate_main_id'], candidate_main_bbox=box))
        observed[sample['frame']] = sample['native']
    result, audit = refine_with_scene_observations(rows, observed,
        video_size=tuple(fixture['video_size']), fps=fixture['fps'], cut_frames=fixture['cut_frames'])
    assert all(r.scene_kind == 'group' for r in result)
    assert {x['frame'] for x in audit['upper_unobserved_exclusions']} == {9296, 9300}
    assert len(observed[9296]) == 5
    assert all(np.array_equal(a.person_bboxes, b.person_bboxes) for a, b in zip(rows, result))


@pytest.mark.parametrize('case', ['visible_head', 'visible_torso', 'visible_limb', 'overlap',
                                  'clipped', 'only_one_full', 'large_ensemble'])
def test_uncertain_upper_foreground_keeps_its_scene_veto(case):
    people = [person(x, 650.) for x in (600., 680., 760.)]
    upper = dict(bbox=np.array([700., 100., 1000., 500.]), pose_keypoints=np.zeros((17, 3)))
    if case == 'visible_head': upper['pose_keypoints'][0] = [850., 150., .9]
    if case == 'visible_torso': upper['pose_keypoints'][5] = [800., 250., .9]
    if case == 'visible_limb': upper['pose_keypoints'][7] = [800., 300., .9]
    if case == 'overlap': upper['bbox'][3] = 700.
    if case == 'clipped': upper['bbox'][1] = 0.
    if case == 'only_one_full':
        for p in people[1:]: p['pose_keypoints'][13:, 2] = 0.
    if case == 'large_ensemble': people = [person(x, 500., 2.) for x in (600., 800., 1000.)]
    people.append(upper)
    rows, observed = example(people=people)
    result, audit = refine(rows, observed)
    assert all(r.scene_kind == 'main' for r in result)
    assert not audit.get('upper_unobserved_exclusions', [])


@pytest.mark.parametrize('support', ['head', 'torso'])
def test_original_observed_upper_body_veto_survives_native_pose_failure(support):
    upper = person(850., 150., 2.2)
    native = dict(bbox=upper['bbox'].copy(), pose_keypoints=upper['pose_keypoints'].copy())
    native['pose_keypoints'][:, 2] = .2
    original = upper['pose_keypoints'].copy()
    original[:, 2] = 0.
    if support == 'head': original[:5, 2] = 1.
    else: original[[5, 6, 11, 12], 2] = 1.
    rows, observed = example(people=[person(x, 650.) for x in (600., 680., 760.)] + [native])
    rows = [replace(r, main_bbox=upper['bbox'], person_bboxes=[upper['bbox']],
        person_head_keypoints=[original[:5]], person_pose_keypoints=[original]) for r in rows]
    result, audit = refine(rows, observed)
    assert all(r.scene_kind == 'main' for r in result)
    assert not audit.get('upper_unobserved_exclusions', [])
