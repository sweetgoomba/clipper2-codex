"""A verified off-center front performer must not become a short group hole."""
from copy import deepcopy
from types import SimpleNamespace

import numpy as np
import pytest

from dance_highlight.services.scene_context import preserve_main_context
from dance_highlight.services.segment import FrameRec, Segment


def _pose(box):
    x, y, xx, yy = box
    w, h = xx-x, yy-y
    p = np.zeros((17, 3)); p[:, 2] = .95
    p[:5, :2] = [[x+.5*w,y+.06*h],[x+.4*w,y+.05*h],[x+.6*w,y+.05*h],
                 [x+.3*w,y+.07*h],[x+.7*w,y+.07*h]]
    p[[5,6,11,12,15,16], :2] = [[x+.2*w,y+.2*h],[x+.8*w,y+.2*h],
        [x+.25*w,y+.5*h],[x+.75*w,y+.5*h],[x+.3*w,y+.95*h],[x+.7*w,y+.95*h]]
    return p


def _case():
    boxes = [np.array(b, float) for b in
             [[640,200,900,980], [200,300,440,980], [1300,300,1540,980]]]
    records, roles, faces, matches = [], [], [], {}
    for i in range(14):
        t = i/10; frame = i*6; group = 5 <= i <= 8
        poses = [_pose(b) for b in boxes]
        record = FrameRec(t, None if group else 1, None if group else boxes[0], group,
            person_bboxes=list(boxes), person_pose_keypoints=poses,
            person_head_keypoints=[p[:5] for p in poses],
            scene_kind='group' if group else 'main',
            scene_reason='distributed_full_body_ensemble' if group else 'main_eligible_composition',
            candidate_main_id=1, candidate_main_bbox=boxes[0])
        records.append(record)
        roles.append(dict(frame=frame, box=boxes[0].tolist(),
            reason='corroborated_foreground_subject', features=[
                dict(index=j, box=b.tolist(), x=float(p[[5,6,11,12],0].mean()),
                     size=70. if j == 0 else 50., source='detected')
                for j, (b, p) in enumerate(zip(boxes, poses))]))
        faces.append((SimpleNamespace(frame_index=frame, time_seconds=t,
            body_bbox=boxes[0], association='confirmed', failure=None,
            embedding=np.array([1.,0.]), detector_score=.95), 'a'))
        matches[frame] = dict(status='accepted', name='a', best='a')
    identity = dict(segments=[Segment('main',1,0.,1.4,[])],
        decisions=[SimpleNamespace(reference_id='a', status='matched')], evidence=[faces])
    return records, identity, matches, roles


def _run(case, **kwargs):
    records, identity, matches, roles = case
    return preserve_main_context(records, identity, matches, video_size=(1920,1080),
        fps=60., cut_frames=[], role_observations=roles, **kwargs)


def test_bounded_off_center_foreground_retains_existing_main_and_frozen_evidence():
    case = _case(); before = deepcopy(case[1]); result, audit = _run(case)
    assert all(r.scene_kind == 'main' for r in result)
    assert not any(r.is_group for r in result)
    assert [r['frame'] for r in audit['changes']] == [30,36,42,48]
    assert all(r.scene_kind == 'group' for r in case[0][5:9])
    assert [d.reference_id for d in case[1]['decisions']] == [d.reference_id for d in before['decisions']]
    assert [o.frame_index for o, _ in case[1]['evidence'][0]] == [o.frame_index for o, _ in before['evidence'][0]]
    assert all(np.array_equal(o.embedding, saved.embedding)
               for (o, _), (saved, _) in zip(case[1]['evidence'][0], before['evidence'][0]))


@pytest.mark.parametrize('barrier', ['missing_roles', 'wrong_role_body', 'stale_role_geometry',
    'missing_detected_face', 'repeated_target_face', 'face_only_dominance', 'equal_foreground', 'faceless_rival',
    'missing_rival_pose', 'contrary_identity', 'unconfirmed_final_identity', 'missing_right_anchor',
    'single_positive_frame', 'handoff'])
def test_foreground_scene_retention_preserves_independent_barriers(barrier):
    case = _case(); records, identity, matches, roles = case
    for i in range(5,9):
        r, role = records[i], roles[i]
        if barrier == 'wrong_role_body': role['box'] = r.person_bboxes[1].tolist()
        if barrier == 'stale_role_geometry': role['features'][0]['box'] = [0,0,100,100]
        if barrier == 'missing_detected_face': role['features'][0]['source'] = 'missing'
        if barrier == 'repeated_target_face': role['features'][0]['source'] = 'repeated_same_pose_geometry'
        if barrier == 'face_only_dominance': r.person_pose_keypoints[0] = _pose([640,300,900,980])
        if barrier == 'equal_foreground': role['features'][1]['size'] = 70.
        if barrier in ('faceless_rival', 'missing_rival_pose'):
            b = np.array([800,100,1120,1050.]); p = _pose(b)
            if barrier == 'missing_rival_pose': p[:,2] = 0.
            r.person_bboxes.append(b); r.person_pose_keypoints.append(p)
            r.person_head_keypoints.append(p[:5])
        if barrier == 'single_positive_frame' and i != 6: role['reason'] = 'measured_face_composition'
    if barrier == 'missing_roles': roles.clear()
    if barrier == 'contrary_identity': matches[36]['name'] = 'b'
    if barrier == 'unconfirmed_final_identity': identity['decisions'][0].reference_id = None
    if barrier == 'missing_right_anchor':
        for f in range(54,79,6): matches.pop(f, None)
    result, audit = _run(case, handoffs=[dict(time=.7, previous_time=.6)] if barrier == 'handoff' else [])
    assert not audit['changes']
    assert all(r.scene_kind == 'group' for r in result[5:9])


def test_saved_neon_front_subject_keeps_part_across_a_real_angle_change():
    import json
    from pathlib import Path
    from dance_highlight.services.face_evidence import FaceObservation
    data = json.loads((Path(__file__).parent/'fixtures/dance_scene_review/neon98_foreground_context.json').read_text())
    records = [FrameRec(r['time_seconds'], r['candidate_main_id'] if r['scene_kind'] == 'main' else None,
        np.array(r['candidate_main_bbox']) if r['scene_kind'] == 'main' else None,
        r['scene_kind'] == 'group', person_bboxes=[np.array(b) for b in r['body_boxes']],
        person_pose_keypoints=[np.array(p) for p in r['pose_keypoints']],
        person_head_keypoints=[np.array(p) for p in r['head_keypoints']],
        scene_kind=r['scene_kind'], scene_reason=r['scene_reason'],
        candidate_main_id=r['candidate_main_id'], candidate_main_bbox=np.array(r['candidate_main_bbox']))
        for r in data['records']]
    observations = {int(f): FaceObservation(**row, embedding=np.array([1.]))
                    for f, row in data['observations'].items()}
    identity = dict(segments=[Segment('main', None, *s['range'], []) for s in data['spans']],
        decisions=[SimpleNamespace(reference_id=s['name'], status='matched' if s['name'] else 'unmatched')
                   for s in data['spans']], evidence=[[(observations[f], None) for f in s['observation_frames']]
                   for s in data['spans']])
    kwargs = dict(video_size=data['video_size'], fps=data['fps'], cut_frames=data['cut_frames'],
                  handoffs=data['handoffs'], camera_transitions=data['camera_transitions'])
    joints = {int(f): value for f, value in data['joint_matches'].items()}
    _, baseline = preserve_main_context(records, identity, joints, **kwargs)
    result, audit = preserve_main_context(records, identity, joints, role_observations=data['roles'], **kwargs)
    old = {r['frame'] for r in baseline['changes']}
    assert [r['frame'] for r in audit['changes'] if r['frame'] not in old] == [5892,5896,5900,5904]
    assert not any(r.is_group for r in result if 5892 <= round(r.t*data['fps']) <= 5904)
    assert 5906 in data['cut_frames']
    assert all(new.person_bboxes is old.person_bboxes and new.person_pose_keypoints is old.person_pose_keypoints
               for new, old in zip(result, records))
    # A different identity in the close-up must keep the real cut and group.
    for frame, value in joints.items():
        if frame >= 5906 and value.get('status') == 'accepted': value['name'] = 'other-member'
    _, rejected = preserve_main_context(records, identity, joints, role_observations=data['roles'], **kwargs)
    assert not {5892,5896,5900,5904} & {r['frame'] for r in rejected['changes']}


def test_mixed_original_group_keeps_its_whole_export_after_context_prefix_retention():
    from dataclasses import replace
    records, identity, matches, roles = case = _case()
    for i, r in enumerate(records):
        b = np.array([760 if i < 7 else 750, 200., 1020 if i < 7 else 1010, 980.])
        r.person_bboxes[0] = b; r.person_pose_keypoints[0] = _pose(b)
        r.person_head_keypoints[0] = r.person_pose_keypoints[0][:5]
        group = 5 <= i <= 10
        records[i] = replace(r, candidate_main_bbox=b, main_bbox=None if group else b,
            main_id=None if group else 1, is_group=group,
            scene_kind='group' if group else 'main',
            scene_reason='distributed_full_body_ensemble' if group else 'main_eligible_composition')
        identity['evidence'][0][i][0].body_bbox = b
        roles[i]['box'] = b.tolist(); roles[i]['features'][0]['box'] = b.tolist()
        roles[i]['features'][0]['x'] = float(b[[0,2]].mean())
        if i in (5,6): roles[i]['reason'] = 'measured_face_composition'
    result, audit = _run(case)
    assert all(r.scene_kind == 'main' for r in result)
    # The early center-only rows still belong to the original group run.
    assert all(r.is_group for r in result[5:11])
    assert not any(c['exclusive_foreground'] for c in audit['changes'])
