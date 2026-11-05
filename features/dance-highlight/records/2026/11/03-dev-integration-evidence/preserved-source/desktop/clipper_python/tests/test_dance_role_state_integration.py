"""Role retention consumes frozen identity and preserves the group output."""
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from dance_highlight.services.scene_context import preserve_main_context
from dance_highlight.services.segment import FrameRec, Segment


def case():
    data = json.loads((Path(__file__).parent /
        'fixtures/dance_scene_review/mmn104_role_state.json').read_text())
    records = []
    evidence = []
    joints = {}
    for row in data['pose_heads']:
        bbox = np.array(row['candidate_main_bbox'])
        main = row['scene_kind'] == 'main'
        records.append(FrameRec(row['time_seconds'], row['candidate_main_id'] if main else None,
            bbox if main else None, not main,
            person_bboxes=[np.array(b) for b in row['body_boxes']],
            person_pose_keypoints=[np.array(p) for p in row['pose_keypoints']],
            person_head_keypoints=[np.array(p) for p in row['head_keypoints']],
            scene_kind=row['scene_kind'], scene_reason=row['scene_reason'],
            candidate_main_id=row['candidate_main_id'], candidate_main_bbox=bbox))
        frame = round(row['time_seconds'] * data['fps'])
        # Fixture membership was checked against original owned face records.
        name = data['owned_names'][str(frame)]
        joints[frame] = dict(status='accepted', name=name, best=name)
        evidence.append((SimpleNamespace(frame_index=frame, time_seconds=row['time_seconds'],
            body_bbox=bbox, association='confirmed', failure=None,
            embedding=np.array([1.]), detector_score=.95), name))
    span = data['identity_spans'][0]
    identity = dict(segments=[Segment('main', None, *span['range'], [])],
        decisions=[SimpleNamespace(status='matched', reference_id=span['name'])],
        evidence=[evidence])
    return data, records, identity, joints


def run(data, records, identity, joints, **kwargs):
    return preserve_main_context(records, identity, joints, video_size=(1920, 1080),
        fps=data['fps'], cut_frames=data['cut_frames'], handoffs=data['handoffs'],
        role_observations=data['roles'], **kwargs)


def test_retained_role_connects_existing_part_but_keeps_group_export():
    data, records, identity, joints = case()
    result, audit = run(data, records, identity, joints, camera_episodes=data['camera_episodes'])
    original_group = [i for i, r in enumerate(records) if r.scene_kind == 'group']
    assert len(original_group) == 5
    assert all(result[i].scene_kind == 'main' and result[i].is_group for i in original_group)
    assert len(audit['role_state']['accepted']) == 1
    assert all(r['role_retention'] and not r['exclusive_foreground'] for r in audit['changes'])
    assert all(records[i].scene_kind == 'group' for i in original_group)
    assert all(new.person_bboxes is old.person_bboxes for new, old in zip(result, records))


@pytest.mark.parametrize('barrier', ['missing_inventory', 'conflicting_final_name',
    'unowned_face', 'source_cut', 'identity_boundary'])
def test_frozen_source_and_identity_contract_is_enforced_at_integration(barrier):
    data, records, identity, joints = case()
    episodes = data['camera_episodes']
    if barrier == 'missing_inventory':
        episodes = None
    elif barrier == 'conflicting_final_name':
        identity['decisions'][0].reference_id = 'another-member'
    elif barrier == 'unowned_face':
        for observation, _ in identity['evidence'][0]:
            observation.body_bbox = np.zeros(4)
    elif barrier == 'source_cut':
        data['cut_frames'].append(round(records[6].t * data['fps']))
    elif barrier == 'identity_boundary':
        identity['segments'][0].start = records[5].t
    _, audit = run(data, records, identity, joints, camera_episodes=episodes)
    assert not audit['role_state']['accepted']
    assert not any(row.get('role_retention') for row in audit['changes'])
