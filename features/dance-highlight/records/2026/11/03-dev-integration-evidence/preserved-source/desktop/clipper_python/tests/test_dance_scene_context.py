"""Context can retain a real main through an ambiguous medium ensemble."""
from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest

from dance_highlight.services.scene_context import preserve_main_context
from dance_highlight.services.segment import FrameRec, Segment, build_raw_main_segments


def pose(box):
    x,y,xx,yy=box;w,h=xx-x,yy-y
    k=np.zeros((17,3));k[:,2]=.95
    k[:5,:2]=[[x+.5*w,y+.06*h],[x+.4*w,y+.05*h],[x+.6*w,y+.05*h],
              [x+.3*w,y+.07*h],[x+.7*w,y+.07*h]]
    k[[5,6,11,12,15,16],:2]=[[x+.2*w,y+.2*h],[x+.8*w,y+.2*h],
        [x+.25*w,y+.5*h],[x+.75*w,y+.5*h],[x+.3*w,y+.95*h],[x+.7*w,y+.95*h]]
    return k


def record(t,kind='group',distant=False):
    boxes=([[820,30,1100,1080]] if kind=='main' else
           [[840,300,1080,980],[200,300,440,980],[1480,300,1720,980]])
    if distant:boxes=[[x,600,xx,900] for x,_,xx,_ in boxes]
    bodies=[np.array(b,float) for b in boxes];poses=[pose(b) for b in boxes]
    return FrameRec(t,1 if kind=='main' else None,bodies[0] if kind=='main' else None,
        kind=='group',person_bboxes=bodies,person_pose_keypoints=poses,
        person_head_keypoints=[k[:5] for k in poses],scene_kind=kind,
        scene_reason='main_eligible_composition' if kind=='main' else 'distributed_full_body_ensemble',
        candidate_main_id=1,candidate_main_bbox=bodies[0])


def inputs(records,names=None):
    names=names or ['member-a']*len(records);fps=60.
    segments=[];decisions=[];evidence=[];joint={}
    for r,name in zip(records,names,strict=True):
        frame=round(r.t*fps)
        segments.append(Segment('main',1,r.t,r.t+.1,[]))
        decisions.append(SimpleNamespace(reference_id=name,status='matched' if name else 'unmatched'))
        face=SimpleNamespace(frame_index=frame,time_seconds=r.t,body_bbox=r.candidate_main_bbox,
            association='confirmed',failure=None,embedding=np.array([1.,0.]),detector_score=.95)
        evidence.append([(face,name)])
        joint[frame]=dict(status='accepted',name=name)
    return dict(segments=segments,decisions=decisions,evidence=evidence),joint


def run(records,names=None,edit=None):
    identity,joint=inputs(records,names)
    if edit:edit(identity,joint)
    return preserve_main_context(records,identity,joint,video_size=(1920,1080),fps=60.,cut_frames=[])


def test_continuous_main_remains_one_six_second_clip_across_medium_camera_view():
    recs=[record(i/10,'main' if i<10 else 'group') for i in range(61)]
    result,audit=run(recs)
    assert len(audit['changes'])==51
    assert [(s.start,s.end) for s in build_raw_main_segments(result)]==[(0.,6.)]
    assert all(r.scene_kind=='group' and r.main_id is None for r in recs[10:])
    # A group export may still accompany this context-compatible solo.
    assert all(r.is_group for r in result[10:])


def test_symmetric_medium_ensemble_alone_never_creates_a_main():
    recs=[record(i/10) for i in range(61)]
    result,audit=run(recs)
    assert result==recs and not audit['changes']


def test_supported_original_medium_main_can_retain_its_continuing_part():
    recs=[record(i/10) for i in range(20)]
    for i in range(10):
        recs[i]=replace(recs[i],scene_kind='main',scene_reason='main_eligible_composition',
                        main_id=1,main_bbox=recs[i].candidate_main_bbox)
    result,audit=run(recs)
    assert len(audit['changes']) == 10
    assert all(r.scene_kind=='main' for r in result)


def test_agreeing_weak_suffix_stops_when_original_direct_support_expires():
    recs=[record(i/10,'main' if i<5 else 'group') for i in range(15)]
    def edit(identity,joint):
        for frame in range(48,85,6):
            joint[frame]=dict(status='insufficient',name=None,reason='joint_video_rejected',
                              best='member-a',margin=.2)
    result,_=run(recs,edit=edit)
    assert all(r.scene_kind=='main' for r in result[:14])
    assert result[14].scene_kind == 'group'


def test_recorded_chaewon_55_56_has_no_scene_hole_despite_medium_seed_and_weak_tail():
    import json
    from pathlib import Path
    data=json.loads((Path(__file__).parent/'fixtures/dance_scene_review/made_my_night_continuity.json').read_text())
    records=[]
    for row in data['scene']['records']:
        main=row['scene_kind']=='main'
        records.append(FrameRec(row['time_seconds'],row['candidate_main_id'] if main else None,
            row['candidate_main_bbox'] if main else None,not main,
            person_bboxes=row['body_boxes'],person_pose_keypoints=row['pose_keypoints'],
            person_head_keypoints=row['head_keypoints'],scene_kind=row['scene_kind'],scene_reason=row['scene_reason'],
            candidate_main_id=row['candidate_main_id'],candidate_main_bbox=row['candidate_main_bbox']))
    name=data['scene']['name']
    identity=dict(segments=[Segment('main',None,116.85,118.50171666666667,[])],
        decisions=[SimpleNamespace(reference_id=name,status='matched')],
        evidence=[[(SimpleNamespace(**dict(row,embedding=np.array([1.]))),name)
                   for row in data['scene']['owned_observations']]])
    joint={int(k):v for k,v in data['joint_matches'].items()}
    result,audit=preserve_main_context(records,identity,joint,video_size=(1920,1080),
                                      fps=data['fps'],cut_frames=data['cut_frames'])
    assert all(r.scene_kind=='main' for r in result)
    assert [row['frame'] for row in audit['changes']] == list(range(7032,7081,4))


@pytest.mark.parametrize('barrier',['distant','second_center','missing_torso','gap','other_name','unknown'])
def test_context_stops_at_observed_scene_or_identity_barriers(barrier):
    recs=[record(i/10,'main' if i<5 else 'group') for i in range(15)]
    names=['member-a']*len(recs)
    for i in range(8,len(recs)):
        r=recs[i]
        if barrier=='distant':recs[i]=record(r.t,distant=True)
        elif barrier=='second_center':
            b=np.array([900,300,1140,980]);r.person_bboxes.append(b);r.person_pose_keypoints.append(pose(b))
        elif barrier=='missing_torso':r.person_pose_keypoints[1][5,2]=0
        elif barrier=='gap':recs[i]=replace(r,t=r.t+1.)
        elif barrier=='other_name':names[i]='member-b'
        elif barrier=='unknown':names[i]=None
    result,_=run(recs,names)
    assert all(r.scene_kind=='main' for r in result[:8])
    assert all(r.scene_kind=='group' for r in result[8:])


def test_bounded_missing_joint_observation_does_not_make_a_one_frame_group_hole():
    recs=[record(i/10,'main' if i<5 else 'group') for i in range(15)]
    result,_=run(recs,edit=lambda identity,joint:joint.pop(48))
    assert all(r.scene_kind=='main' for r in result)


def test_contrary_joint_face_is_not_interpolated_over_or_used_to_chain_context():
    recs=[record(i/10,'main' if i<5 else 'group') for i in range(15)]
    result,_=run(recs,edit=lambda identity,joint:joint[48].update(name='member-b'))
    assert all(r.scene_kind=='group' for r in result[8:])


def test_a_valid_face_on_another_body_cannot_qualify_this_main():
    recs=[record(i/10,'main' if i<5 else 'group') for i in range(15)]
    def edit(identity,joint):
        for i in range(5,15):identity['evidence'][i][0][0].body_bbox=recs[i].person_bboxes[1]
    result,audit=run(recs,edit=edit)
    assert not audit['changes'] and all(r.scene_kind=='group' for r in result[5:])


def test_context_is_direction_independent_and_input_names_are_never_changed():
    recs=[record(i/10,'main' if i>=10 else 'group') for i in range(15)]
    identity,joint=inputs(recs);before=[d.reference_id for d in identity['decisions']]
    result,audit=preserve_main_context(recs,identity,joint,video_size=(1920,1080),fps=60.,cut_frames=[])
    assert all(r.scene_kind=='main' for r in result) and len(audit['changes'])==10
    assert [d.reference_id for d in identity['decisions']]==before


def test_head_missing_central_torso_still_vetoes_unique_center():
    recs=[record(i/10,'main' if i<5 else 'group') for i in range(15)]
    for r in recs[5:]:
        b=np.array([900,300,1140,980]);k=pose(b);k[:5,2]=0
        r.person_bboxes.append(b);r.person_pose_keypoints.append(k)
    result,audit=run(recs)
    assert not audit['changes'] and all(r.scene_kind=='group' for r in result[5:])


@pytest.mark.parametrize('status,best,margin',[('conflict','member-a',.2),
    ('insufficient','member-b',.2),('insufficient','member-a',.01)])
def test_rejected_competing_identity_is_not_a_missing_observation(status,best,margin):
    recs=[record(i/10,'main' if i<5 else 'group') for i in range(15)]
    def edit(identity,joint):
        joint[48]=dict(status=status,name=None,reason='joint_video_rejected',best=best,margin=margin)
    result,_=run(recs,edit=edit)
    assert all(r.scene_kind=='group' for r in result[8:])


def test_agreeing_weak_distance_can_be_bounded_without_changing_identity():
    recs=[record(i/10,'main' if i<5 else 'group') for i in range(15)]
    def edit(identity,joint):
        joint[48]=dict(status='insufficient',name=None,reason='joint_video_rejected',
                      best='member-a',margin=.2)
    result,_=run(recs,edit=edit)
    assert all(r.scene_kind=='main' for r in result)


@pytest.mark.parametrize('missing',[None,24,30])
def test_camera_cut_requires_direct_agreement_on_both_adjacent_observations(missing):
    recs=[record(i/10,'main' if i<5 else 'group') for i in range(15)]
    identity,joint=inputs(recs)
    if missing is not None:joint.pop(missing)
    result,audit=preserve_main_context(recs,identity,joint,video_size=(1920,1080),
                                       fps=60.,cut_frames=[27])
    if missing is None:assert all(r.scene_kind=='main' for r in result)
    else:assert not audit['changes'] and all(r.scene_kind=='group' for r in result[5:])


def test_no_inventory_means_no_context_reclassification():
    recs=[record(i/10,'main' if i<5 else 'group') for i in range(15)]
    identity,joint=inputs(recs)
    result,audit=preserve_main_context(recs,identity,joint,video_size=(1920,1080),fps=60.)
    assert result==recs and audit['reason']=='cut_inventory_unavailable'


def test_two_camera_cuts_cannot_hide_an_unobserved_intermediate_main():
    recs=[record(i/10,'main' if i<5 else 'group') for i in range(15)]
    identity,joint=inputs(recs)
    result,audit=preserve_main_context(recs,identity,joint,video_size=(1920,1080),
                                       fps=60.,cut_frames=[26,28])
    assert not audit['changes'] and all(r.scene_kind=='group' for r in result[5:])


def test_observed_main_handoff_stops_retention_even_when_frozen_names_agree():
    recs=[record(i/10,'main' if i<5 else 'group') for i in range(15)]
    identity,joint=inputs(recs)
    result,_=preserve_main_context(recs,identity,joint,video_size=(1920,1080),fps=60.,
        cut_frames=[],handoffs=[dict(previous_time=.7,time=.8)])
    assert all(r.scene_kind=='main' for r in result[:8])
    assert all(r.scene_kind=='group' for r in result[8:])


@pytest.mark.parametrize('barrier',[None,'unproved_cut','other_face','missing_owned_face','handoff',
                                  'model_conflict','weak_competitor','missing_model_ranks','plausible_model_rival',
                                  'malformed_model_ranks','invalid_joint_score','missing_left_face','missing_right_face'])
def test_recorded_chaewon_35_36_retains_only_the_bounded_same_person_camera_gap(barrier):
    import json
    from pathlib import Path
    data=json.loads((Path(__file__).parent/'fixtures/dance_scene_review/made_my_night_continuity.json').read_text())
    source=data['bounded_scene'];records=[]
    for row in source['records']:
        main=row['scene_kind']=='main'
        records.append(FrameRec(row['time_seconds'],row['candidate_main_id'] if main else None,
            row['candidate_main_bbox'] if main else None,not main,
            person_bboxes=row['body_boxes'],person_pose_keypoints=row['pose_keypoints'],
            person_head_keypoints=row['head_keypoints'],scene_kind=row['scene_kind'],scene_reason=row['scene_reason'],
            candidate_main_id=row['candidate_main_id'],candidate_main_bbox=row['candidate_main_bbox']))
    name=source['name'];evidence=[(SimpleNamespace(**dict(row,embedding=np.array([1.]))),name)
                                for row in source['owned_observations']]
    identity=dict(segments=[Segment('main',None,80.7,81.55,[])],
        decisions=[SimpleNamespace(reference_id=name,status='matched')],evidence=[evidence])
    joints={int(k):v for k,v in data['joint_matches'].items()};transitions=data['camera_transitions'];handoffs=[]
    if barrier=='unproved_cut':transitions=[]
    elif barrier=='other_face':joints[4864]=dict(joints[4864],status='accepted',name='사쿠라')
    elif barrier=='missing_owned_face':evidence[4][0].association='unassigned'
    elif barrier=='handoff':handoffs=[dict(previous_time=81.01426666666667,time=81.081)]
    elif barrier=='model_conflict':
        joints[4864]=dict(joints[4864],status='conflict',name=None,best=name,
                          primary=.1,secondary=.8,margin=.2)
    elif barrier=='weak_competitor':
        joints[4864]=dict(joints[4864],status='insufficient',name=None,best=name,margin=.001)
    elif barrier=='missing_model_ranks':joints[4860].pop('model_candidates')
    elif barrier=='malformed_model_ranks':joints[4860]['model_candidates'][0].pop()
    elif barrier=='invalid_joint_score':joints[4860]['primary']=float('nan')
    elif barrier=='missing_left_face':joints.pop(4852)
    elif barrier=='missing_right_face':joints.pop(4876)
    elif barrier=='plausible_model_rival':
        joint=joints[4860]
        rival=next(c for c in joint['model_candidates'][0] if c['name']=='홍은채')
        rival['distance']=.59
        means=sorted((sum(next(c['distance'] for c in model if c['name']==member)
                          for model in joint['model_candidates'])/2,member)
                     for member in [c['name'] for c in joint['model_candidates'][0]])
        joint['margin']=means[1][0]-means[0][0]
    result,audit=preserve_main_context(records,identity,joints,video_size=(1920,1080),fps=data['fps'],
        cut_frames=data['bounded_cut_frames'],camera_transitions=transitions,handoffs=handoffs)
    changed=[round(r.t*data['fps']) for old,r in zip(records,result) if old.scene_kind!=r.scene_kind]
    assert changed == ([4856,4860,4864,4868,4872] if barrier is None else [])


def fresh_context_hole(name,corrected_role=False):
    import json
    from pathlib import Path
    data=json.loads((Path(__file__).parent/'fixtures/dance_scene_review/made_fresh_context_holes.json').read_text())
    source=data['cases'][name];records=[]
    for r in source['current_role_records'] if corrected_role else source['records']:
        records.append(FrameRec(r['time_seconds'],r['main_id'],r['main_bbox'],r['is_group'],
            person_bboxes=r['body_boxes'],person_pose_keypoints=r['pose_keypoints'],person_head_keypoints=r['head_keypoints'],
            scene_kind=r['scene_kind'],scene_reason=r['scene_reason'],candidate_main_id=r['candidate_main_id'],
            candidate_main_bbox=r['candidate_main_bbox']))
    evidence=[]
    for r in source['owned_observations']:
        if corrected_role and r['frame_index']==5436:
            r=dict(source['corrected_body_observation'],primary_name=None)
        row=dict(r);primary=row.pop('primary_name')
        row['embedding']=(np.asarray(row['embedding']) if corrected_role and row['frame_index']==5436
                          else np.array([1.]) if not row['failure'] else None)
        evidence.append((SimpleNamespace(**row),primary))
    identity=dict(segments=[Segment('main',None,s['start'],s['end'],[]) for s in source['spans']],
        decisions=[SimpleNamespace(reference_id=s['name'],status=s['status']) for s in source['spans']],evidence=[evidence])
    joint={int(k):v for k,v in source['joint_matches'].items()}
    if corrected_role:joint[5436]=source['corrected_joint']
    return records,identity,joint,dict(fps=data['fps'],video_size=(1920,1080),cut_frames=source['cut_frames'],
        camera_transitions=source['camera_transitions'],handoffs=source['current_role_handoffs'] if corrected_role else source['handoffs'])


@pytest.mark.parametrize('barrier',[None,'handoff','different_face','missing_new_shot_face','another_cut','unobserved_body'])
def test_fresh_chaewon_cut_retains_the_observed_same_main_without_rechecking_old_main_faces(barrier):
    records,identity,joint,kwargs=fresh_context_hole('chaewon')
    if barrier=='handoff':kwargs['handoffs']=[dict(previous_time=5072/kwargs['fps'],time=5076/kwargs['fps'])]
    elif barrier=='different_face':joint[5080]=dict(joint[5080],status='accepted',name='카즈하')
    elif barrier=='missing_new_shot_face':
        for f in list(joint):
            if f>=5076 and joint[f].get('status')=='accepted':joint.pop(f)
    elif barrier=='another_cut':
        kwargs['cut_frames'].append(5082);kwargs['camera_transitions'].append(dict(frame=5082,structure=dict(continuous=False)))
    elif barrier=='unobserved_body':
        record=next(r for r in records if round(r.t*kwargs['fps'])==5080)
        record.person_pose_keypoints[2][5][2]=0.
    result,_=preserve_main_context(records,identity,joint,**kwargs)
    restored=[round(r.t*kwargs['fps']) for r in result if 5076<=round(r.t*kwargs['fps'])<=5088 and r.scene_kind=='main']
    assert restored==([5076,5080,5084,5088] if barrier is None else [])


@pytest.mark.parametrize('corrected_role',[False,True])
def test_fresh_kazuha_wide_focus_keeps_directly_confirmed_body_without_a_total_duration_cap(corrected_role):
    records,identity,joint,kwargs=fresh_context_hole('kazuha',corrected_role=corrected_role)
    result,_=preserve_main_context(records,identity,joint,**kwargs)
    restored=[round(r.t*kwargs['fps']) for r in result if 5448<=round(r.t*kwargs['fps'])<=5476 and r.scene_kind=='main']
    assert restored==(list(range(5448,5480,4)) if corrected_role else [])
    if corrected_role:
        observation=next(o for o,_ in identity['evidence'][0] if o.frame_index==5436)
        assert observation.detector_score<.8
        assert joint[5436]['status']=='unavailable'  # The old selected Chaewon face is never copied.


def test_only_consumed_deferred_camera_proofs_are_resolved_without_changing_scene():
    import copy
    records,identity,joint,kwargs=fresh_context_hole('chaewon')
    expected,audit=preserve_main_context(records,identity,joint,**kwargs)
    originals={p['frame']:copy.deepcopy(p) for p in kwargs['camera_transitions']}
    kwargs['camera_transitions']=[{k:v for k,v in p.items() if k!='structure'}|{'structure_deferred':True} for p in kwargs['camera_transitions']]
    calls=[]
    def resolve(frame):
        calls.append(frame)
        return originals[frame]
    actual,after=preserve_main_context(records,identity,joint,**kwargs,resolve_transition=resolve)
    assert [r.scene_kind for r in actual]==[r.scene_kind for r in expected]
    assert after==audit
    assert calls and len(calls)==len(set(calls))
