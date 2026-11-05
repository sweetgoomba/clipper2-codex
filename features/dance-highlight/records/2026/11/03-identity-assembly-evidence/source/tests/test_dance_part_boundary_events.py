"""A single observed transition must not produce two output boundaries."""
from dataclasses import replace
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from dance_highlight.services.face_evidence import FaceObservation
from dance_highlight.services.segment import FrameRec, Segment
from test_dance_output_continuity import output_parts


def example(*, name='A', event='handoff'):
    from test_dance_identity_projection import stable_records
    records, _ = stable_records()
    box = records[0].main_bbox
    rows = [FaceObservation(f, f/60, 0, tuple(box), tuple(box),
        face_bbox=(35, 10, 65, 30), embedding=np.array([1., 0.]),
        detector_score=.99, association='confirmed') for f in [0, 4, 8, 12]]
    new_box = box + np.array([200., 0., 200., 0.])
    new_pose = records[0].person_pose_keypoints[0].copy()
    new_pose[:, 0] += 200
    records.append(FrameRec(16/60, 1 if event == 'handoff' else None,
        new_box if event == 'handoff' else None, event != 'handoff',
        person_bboxes=[box, new_box], person_pose_keypoints=[records[0].person_pose_keypoints[0], new_pose],
        candidate_main_bbox=new_box, scene_kind='main' if event == 'handoff' else 'group'))
    output = output_parts([(0., 14/60, name, 'A'), (14/60, 16/60, None, 'B')])
    output['evidence'] = [[(r, name) for r in rows], []]
    output['segments'] = [replace(s, bboxes=[(r.time_seconds, np.array(r.body_bbox), 0)
        for r, _ in output['evidence'][i]]) for i, s in enumerate(output['segments'])]
    output['preview_sources'] = [({r.frame_index: bytes([r.frame_index+1]) for r in rows}, {}), ({}, {})]
    output['previews'] = [list(output['preview_sources'][0][0].values()), []]
    boundary = dict(time=14/60, left_time=12/60, right_time=16/60,
                    reason='repeated_face_change')
    identity = dict(audit=[dict(boundaries=[boundary])])
    handoffs = [dict(previous_time=12/60, time=16/60, previous_frame=12, frame=16,
        boundary_policy='first_observed_new_main') ] if event == 'handoff' else []
    return output, identity, dict(frame_records=records, frozen_observations=rows,
        matcher=SimpleNamespace(match=lambda *_: SimpleNamespace(reference_id='A')),
        joint_matches={r.frame_index: dict(status='accepted', name='A') for r in rows},
        eligibility=[Segment('main', None, 0., .8 if event == 'handoff' else 16/60, [])],
        fps=60., sample_step=4, cut_frames=[], handoffs=handoffs)


def run(output, identity, kwargs):
    from dance_highlight.services.part_boundary_events import coalesce_boundary_events
    return coalesce_boundary_events(output, identity, **kwargs)


@pytest.mark.parametrize('event', ['handoff', 'scene_exit'])
@pytest.mark.parametrize('name', ['A', None])
def test_same_observation_event_does_not_leave_an_empty_unknown_clip(event, name):
    original, identity, args = example(name=name, event=event)
    result, audit = run(original, identity, args)
    assert [(s.start, s.end) for s in result['segments']] == [(0., 16/60)]
    assert result['decisions'][0].reference_id == name
    assert [r.frame_index for r, _ in result['evidence'][0]] == [0, 4, 8, 12]
    assert result['previews'][0] == original['previews'][0]
    assert result['anchors'] is original['anchors']
    assert [(s.start, s.end) for s in original['segments']] == [(0., 14/60), (14/60, 16/60)]
    assert identity['audit'][0]['boundaries'][0]['time'] == 14/60
    assert audit['joins'][0]['boundary'] == 14/60
    assert audit['joins'][0]['canonical_time'] == 16/60


@pytest.mark.parametrize('failure', ['cut', 'precise_cut', 'different_bracket', 'other_handoff',
    'missing_handoffs', 'missing_cuts', 'missing_record', 'role_gap', 'inside_observation',
    'actual_short_b', 'last_face_conflict', 'no_independent_pair', 'wrong_body', 'invalid_fps',
    'non_midpoint', 'other_boundary_reason', 'no_role_event', 'primary_conflict', 'missing_primary'])
def test_no_join_without_the_same_event_and_unopposed_original_support(failure):
    output, identity, args = example()
    boundary = identity['audit'][0]['boundaries'][0]
    if failure == 'cut': args['cut_frames'] = [15]
    elif failure == 'precise_cut': boundary['boundary_frame_index'] = 14
    elif failure == 'different_bracket': boundary['left_time'] = 8/60
    elif failure == 'other_handoff': args['handoffs'][0]['previous_time'] = 8/60
    elif failure == 'missing_handoffs': args['handoffs'] = None
    elif failure == 'missing_cuts': args['cut_frames'] = None
    elif failure == 'missing_record': args['frame_records'].pop(2)
    elif failure == 'role_gap':
        args['eligibility'] = [Segment('main', None, 0., 14/60, []), Segment('main', None, 15/60, .8, [])]
    elif failure == 'inside_observation':
        row = replace(args['frozen_observations'][-1], frame_index=15, time_seconds=15/60)
        args['frozen_observations'] = [*args['frozen_observations'], row]
    elif failure == 'actual_short_b':
        output['decisions'][1] = replace(output['decisions'][1], reference_id='B', status='matched')
    elif failure == 'last_face_conflict': args['joint_matches'][12] = dict(status='conflict', name=None)
    elif failure == 'no_independent_pair': args['joint_matches'] = {12: dict(status='accepted', name='A')}
    elif failure == 'wrong_body':
        args['frozen_observations'][-1] = replace(args['frozen_observations'][-1], body_bbox=(200., 0., 300., 210.))
    elif failure == 'invalid_fps': args['fps'] = float('nan')
    elif failure == 'non_midpoint': boundary['time'] = 15/60
    elif failure == 'other_boundary_reason': boundary['reason'] = 'repeated_reference_change'
    elif failure == 'no_role_event': args['handoffs'] = []
    elif failure == 'primary_conflict':
        args['matcher'] = SimpleNamespace(match=lambda r, *_: SimpleNamespace(reference_id='B' if r.frame_index == 12 else 'A'))
    elif failure == 'missing_primary': args['matcher'] = None
    result, audit = run(output, identity, args)
    assert [(s.start, s.end) for s in result['segments']] == [(0., 14/60), (14/60, 16/60)]
    assert not audit['joins']


def saved_case(case):
    rows = [FaceObservation(**{k: np.asarray(v) if k == 'embedding' and v is not None else v
        for k, v in o.items()}) for o in case['owned_observations']]
    records = []
    for r in case['pose_heads']:
        box = np.asarray(r['candidate_main_bbox']) if r['candidate_main_bbox'] is not None else None
        records.append(FrameRec(r['time_seconds'], r['candidate_main_id'],
            box if r['scene_kind'] == 'main' else None, r['scene_kind'] == 'group',
            person_bboxes=[np.asarray(b) for b in r['body_boxes']],
            person_pose_keypoints=[np.asarray(p) for p in r['pose_keypoints']],
            candidate_main_bbox=box, scene_kind=r['scene_kind']))
    output = output_parts([(s['range'][0], s['range'][1], s['name'], 'A') for s in case['outputs']])
    output['evidence'] = [[(r, s['name']) for r in rows if s['range'][0] <= r.time_seconds < s['range'][1]]
        for s in case['outputs']]
    output['segments'] = [replace(s, bboxes=[(r.time_seconds, np.asarray(r.body_bbox), r.track_id)
        for r, _ in output['evidence'][i]]) for i, s in enumerate(output['segments'])]
    output['previews'] = [[] for _ in case['outputs']]
    output['preview_sources'] = [({}, {}) for _ in case['outputs']]
    # Preserve excluded gaps between the saved output episodes.
    eligible = [Segment('main', None, *s['range'], []) for s in case['outputs']]
    return output, dict(audit=[dict(boundaries=[case['boundary']])]), dict(
        frame_records=records, frozen_observations=rows, joint_matches=case['joint_matches'],
        matcher=SimpleNamespace(match=lambda r, *_: SimpleNamespace(reference_id=case['primary_names'].get(str(r.frame_index)))),
        eligibility=eligible, fps=case['fps'], sample_step=case['sample_step'],
        cut_frames=case['cut_frames'], handoffs=case['handoffs'])


CASES = json.loads((Path(__file__).parent/'fixtures/dance_scene_review/coincident_boundary_events.json').read_text())['cases']


@pytest.mark.parametrize('case', CASES, ids=lambda c: c['id'])
def test_saved_app_events_preserve_roles_and_actual_incoming_observations(case):
    original, identity, args = saved_case(case)
    result, audit = run(original, identity, args)
    if case['id'] == 'neon-34334':
        assert not audit['joins']
        assert len(result['segments']) == len(original['segments'])
    else:
        assert len(audit['joins']) == 1
        assert len(result['segments']) == len(original['segments'])-1
        assert result['segments'][0].end == pytest.approx(case['boundary']['right_time'])
        assert result['decisions'][0].reference_id == original['decisions'][0].reference_id
    assert result['segments'][0].start == original['segments'][0].start
    assert result['segments'][-1].end == original['segments'][-1].end
    assert [r.frame_index for group in result['evidence'] for r, _ in group] == [
        r.frame_index for group in original['evidence'] for r, _ in group]
