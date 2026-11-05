"""A zoom threshold does not establish a new solo performer."""
import json
from pathlib import Path
from dataclasses import replace
import numpy as np
import pytest
from dance_highlight.services.segment import FrameRec, classify_main_scenes

DATA=json.loads((Path(__file__).parent/'fixtures/dance_scene_review/mmn50_ensemble_zoom.json').read_text())


def inputs():
    rows=[]
    for r in DATA['rows']:
        rows.append(FrameRec(r['time_seconds'],r['candidate_main_id'],np.array(r['candidate_main_bbox']),False,
            person_bboxes=[np.array(b) for b in r['body_boxes']],
            person_head_keypoints=[np.array(k) for k in r['head_keypoints']],
            person_pose_keypoints=[np.array(k) for k in r['pose_keypoints']]))
    return classify_main_scenes(rows,(DATA['width'],DATA['height']))


def apply(records=None, **kw):
    from dance_highlight.services.ensemble_continuity import continue_observed_ensemble
    args=dict(video_size=(1920,1080),fps=DATA['fps'],sample_step=4,
              cut_frames=DATA['cut_frames'],handoffs=[],camera_episodes=[],role_observations=DATA['roles'])
    args.update(kw)
    return continue_observed_ensemble(inputs() if records is None else records,**args)


def test_uniform_zoom_does_not_leave_a_solo_sliver_before_the_camera_cut():
    before=inputs();result,audit=apply(before)
    assert [round(r.t*DATA['fps']) for r in before if 50.65<r.t<50.8 and r.scene_kind=='main']==[3036,3040,3044]
    assert all(r.scene_kind=='group' and r.main_bbox is None for r in result if 50.25<=r.t<50.834)
    assert all(r.scene_kind=='main' for r in result if r.t>50.834)
    assert audit['continued_frames']==[3036,3040,3044]
    assert before[0] is result[0]
    assert all(np.array_equal(a.candidate_main_bbox,b.candidate_main_bbox) for a,b in zip(before,result))


@pytest.mark.parametrize('missing', ['cut_frames','handoffs','camera_episodes','role_observations'])
def test_missing_original_proofs_never_extend_a_group(missing):
    before=inputs();out,audit=apply(before,**{missing:None})
    assert out is before


def test_an_unestablished_group_does_not_swallow_a_main():
    records=[replace(r,main_id=r.candidate_main_id,main_bbox=r.candidate_main_bbox,is_group=False,
                     scene_kind='main',scene_reason='main_eligible_composition') for r in inputs()]
    result,audit=apply(records)
    assert result is records


@pytest.mark.parametrize('veto', ['cut','handoff','focal','dominant','missing_body','missing_pose','sampling_gap'])
def test_new_subject_or_unobserved_formation_is_not_a_group_tail(veto):
    records=inputs();args={};index=next(i for i,r in enumerate(records) if round(r.t*DATA['fps'])==3036)
    if veto=='cut':args['cut_frames']=[2989,3036,3047]
    if veto=='handoff':args['handoffs']=[dict(time=records[index].t)]
    if veto=='focal':args['camera_episodes']=[dict(start_frame=3036,end_frame=3044)]
    if veto=='dominant':
        roles=json.loads(json.dumps(DATA['roles']))
        for r in roles:
            if r['frame']>=3036:r['reason']='confirmed_corroborated_foreground_subject'
        args['role_observations']=roles
    if veto=='missing_body':records[index]=replace(records[index],person_bboxes=records[index].person_bboxes[:-1],person_pose_keypoints=records[index].person_pose_keypoints[:-1])
    if veto=='missing_pose':records[index].person_pose_keypoints[0][15,2]=0
    if veto=='sampling_gap':records.pop(index+1)
    result,audit=apply(records,**args)
    assert all(r.scene_kind=='main' for r in result if 50.65<r.t<50.8)


def test_an_unconfirmed_but_measured_new_foreground_subject_is_not_overridden():
    roles=json.loads(json.dumps(DATA['roles']))
    for r in roles:
        if r['frame']<3036:continue
        r['reason']='awaiting_sustained_composition'
        measured=[f for f in r['features'] if f['size'] is not None]
        biggest=max(measured,key=lambda f:f['size'])
        biggest['size']=2*max(f['size'] for f in measured if f is not biggest)
    result,audit=apply(role_observations=roles)
    assert all(r.scene_kind=='main' for r in result if 50.65<r.t<50.8)


def test_role_measurements_for_a_different_selected_body_are_not_current_proof():
    roles=json.loads(json.dumps(DATA['roles']))
    for r in roles:
        if r['frame']>=3036:r['box']=r['features'][0]['box']
    result,audit=apply(role_observations=roles)
    assert all(r.scene_kind=='main' for r in result if 50.65<r.t<50.8)
