"""Bounded group observation gaps need both scene anchors and every body."""
import json
from pathlib import Path

import numpy as np
import pytest

from dance_highlight.services.segment import FrameRec
from dance_highlight.services.track import bbox_iou


def example():
    data = json.loads((Path(__file__).parent/'fixtures/dance_scene_review/compact_group_gap.json').read_text())
    rows = [FrameRec(r['time_seconds'], r['candidate_main_id'] if r['scene_kind']=='main' else None,
        np.array(r['candidate_main_bbox']) if r['scene_kind']=='main' else None, r['scene_kind']=='group',
        person_bboxes=[np.array(b) for b in r['body_boxes']],
        group_bboxes=[np.array(b) for b in r['group_bboxes']],
        person_pose_keypoints=[np.array(p) for p in r['pose_keypoints']],
        scene_kind=r['scene_kind'], scene_reason=r['scene_reason'],
        candidate_main_id=r['candidate_main_id'], candidate_main_bbox=np.array(r['candidate_main_bbox']))
        for r in data['rows']]
    target = next(r for r in rows if round(r.t*data['fps'])==data['target_frame'])
    return rows, target, dict(video_size=(1920,1080), fps=data['fps'], sample_step=data['sample_step'],
                              cut_frames=[], handoffs=[], camera_episodes=[],
                              native_observations=data['native_observations'])


def bridge(rows, args):
    from dance_highlight.services.segment import bridge_compact_group_gaps
    return bridge_compact_group_gaps(rows, **args)


def test_actual_native_to_compact_group_gap_retains_all_body_observations():
    rows, target, args = example()
    output, audit = bridge(rows, args)
    changed = [(a,b) for a,b in zip(rows,output) if a.scene_kind!=b.scene_kind]
    assert len(changed)==1 and changed[0][0] is target
    assert changed[0][1].scene_kind=='group' and changed[0][1].main_bbox is None
    assert target.scene_kind=='main' and target.main_bbox is not None
    assert all(a.t==b.t and a.person_bboxes is b.person_bboxes for a,b in zip(rows,output))
    assert len(audit['bridges'])==1
    assert audit['bridges'][0]['start']==target.t
    assert audit['bridges'][0]['left_anchor_frame']==8608
    assert audit['bridges'][0]['right_anchor_frame']==8616
    assert len(changed[0][1].group_bboxes)==2  # Stage art is not a confirmed person.


@pytest.mark.parametrize('veto', ['cut','handoff','camera_episode','missing_inventory',
    'missing_sample','new_body','scale_jump','central_subject','duplicate_body','no_person',
    'missing_pose','observed_foreground_at_old_art','missing_native_anchor',
    'missing_native_observation','unobserved_native_body','partial_native_match'])
def test_group_gap_keeps_ambiguous_or_changed_roles(veto):
    rows, target, args = example()
    frame=round(target.t*args['fps'])
    if veto=='cut': args['cut_frames']=[frame]
    if veto=='handoff': args['handoffs']=[{'time':target.t}]
    if veto=='camera_episode': args['camera_episodes']=[{'start_frame':frame,'end_frame':frame}]
    if veto=='missing_inventory': args['cut_frames']=None
    if veto=='missing_sample': rows.pop(rows.index(target)-1)
    if veto=='new_body': target.person_bboxes[0]+=np.array([400.,0.,400.,0.])
    if veto=='scale_jump': target.person_bboxes[0][1]-=300.
    if veto=='central_subject':
        target.person_bboxes[0]=np.array([850.,500.,1070.,900.])
        target.person_pose_keypoints[0][[5,6,11,12]]=[[930,600,1],[990,600,1],[930,750,1],[990,750,1]]
    if veto=='duplicate_body':
        target.person_bboxes[1]=target.person_bboxes[0].copy()
        target.person_pose_keypoints[1]=target.person_pose_keypoints[0].copy()
    if veto=='no_person': target.scene_kind='no_person'
    if veto=='missing_pose': target.person_pose_keypoints=[]
    if veto=='missing_native_anchor': rows[rows.index(target)-1].group_bboxes=[]
    if veto=='missing_native_observation': args['native_observations']=[]
    if veto=='unobserved_native_body':
        anchor=next(o for o in args['native_observations'] if o['frame']==8608)
        for person in anchor['persons']:
            points=np.array(person['pose_keypoints'])
            points[:,2]=0.
            person['pose_keypoints']=points.tolist()
    if veto=='partial_native_match':
        anchor=next(o for o in args['native_observations'] if o['frame']==8608)
        person=max(anchor['persons'],key=lambda p:bbox_iou(np.array(p['bbox']),target.person_bboxes[2]))
        points=np.array(person['pose_keypoints']);points[:5,2]=0.
        person['pose_keypoints']=points.tolist()
    if veto=='observed_foreground_at_old_art':
        x,y,xx,yy=target.person_bboxes[1]
        w,h=xx-x,yy-y
        p=np.zeros((17,3));p[:,2]=.99
        p[:5,:2]=[[x+.5*w,y+.08*h],[x+.4*w,y+.07*h],[x+.6*w,y+.07*h],
                    [x+.3*w,y+.08*h],[x+.7*w,y+.08*h]]
        p[[5,6,11,12,15,16],:2]=[[x+.3*w,y+.2*h],[x+.7*w,y+.2*h],
            [x+.35*w,y+.5*h],[x+.65*w,y+.5*h],[x+.35*w,y+.95*h],[x+.65*w,y+.95*h]]
        target.person_pose_keypoints[1]=p
    output,audit=bridge(rows,args)
    assert all(a.scene_kind==b.scene_kind for a,b in zip(rows,output))
    assert not audit['bridges']
