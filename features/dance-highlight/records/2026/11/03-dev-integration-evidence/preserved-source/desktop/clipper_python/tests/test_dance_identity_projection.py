"""A name padded from a later face must still belong to the projected main."""
import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from dance_highlight.services.face_evidence import FaceObservation
from dance_highlight.services.performance_parts import _project
from dance_highlight.services.reference_matcher import SegmentReferenceDecision
from dance_highlight.services.segment import FrameRec, Segment
from test_dance_output_continuity import output_parts


def apply_guard(records, rows, *, start=.025, end=.055, fps=60., cuts=(), names=None,
                independent_names=None, primary_name=None, joint_status='accepted'):
    from dance_highlight.services.identity_projection import validate_identity_padding
    parent = output_parts([(start, rows[-1].time_seconds+.1, 'B', 'B')])
    parent['decisions'][0] = SegmentReferenceDecision('B', 'matched', 'member_timeline_consensus')
    parent['evidence'][0] = list(zip(rows, names or ['B']*len(rows)))
    projected = [(0, Segment('main', 0, start, end, []))]
    output = _project(parent, projected)
    from types import SimpleNamespace
    matcher = SimpleNamespace(match=lambda *_: SimpleNamespace(reference_id=primary_name))
    raw_names = independent_names if independent_names is not None else [name for _,name in parent['evidence'][0]]
    result, audit = validate_identity_padding(output, parent, projected,
        frame_records=records, fps=fps, sample_step=4, cut_frames=cuts, handoffs=[], matcher=matcher,
        joint_matches={r.frame_index:{'status':joint_status,'name':name}
                       for r,name in zip(rows,raw_names) if name}, frozen_observations=rows)
    assert parent['decisions'][0].reference_id == 'B'
    return result, audit


def test_real_neon_padding_before_different_main_does_not_create_two_frame_name():
    data = json.loads((Path(__file__).parent/'fixtures/dance_scene_review/neon42_identity_padding.json').read_text())
    records = [FrameRec(r['time_seconds'], 0, np.asarray(r['candidate_main_bbox']), False,
        person_bboxes=[np.asarray(b) for b in r['body_boxes']],
        person_pose_keypoints=[np.asarray(p) for p in r['pose_keypoints']],
        candidate_main_bbox=np.asarray(r['candidate_main_bbox']), scene_kind=r['scene_kind'])
        for r in data['pose_heads']]
    import dataclasses
    fields = {f.name for f in dataclasses.fields(FaceObservation)}
    rows = [FaceObservation(**{k:(np.asarray(v) if k == 'embedding' else v)
        for k,v in r.items() if k in fields}) for r in data['owned_observations'] if r['frame_index'] >= 2556]
    result, audit = apply_guard(records, rows, start=data['part'][0], end=data['part'][1], fps=data['fps'],
                               names=[None if r.frame_index == 2556 else 'B' for r in rows])
    assert result['decisions'][0].reference_id is None
    assert result['labels'] == [None] and result['accurate_indices'] == []
    assert audit['rejected'][0]['support_frame'] == 2560
    assert audit['rejected'][0]['reason'] == 'selected_body_discontinuity'


def stable_records():
    pose=np.array([[50,20],[45,18],[55,18],[40,20],[60,20],[35,50],[65,50],
        [30,80],[70,80],[25,110],[75,110],[40,120],[60,120],[40,160],
        [60,160],[40,200],[60,200]],dtype=float)
    pose=np.c_[pose,np.ones(17)]
    box=np.array([10.,0.,90.,210.])
    records=[FrameRec(t,0,box.copy(),False,person_bboxes=[box.copy()],
        person_pose_keypoints=[pose.copy()],candidate_main_bbox=box.copy(),scene_kind='main')
        for t in [0.,4/60,8/60,12/60]]
    rows=[FaceObservation(f,f/60,0,tuple(box),tuple(box),face_bbox=(35,10,65,30),
        embedding=np.array([0.,1.]),detector_score=.99,association='confirmed') for f in [8,12]]
    return records, rows


def test_clipping_cannot_inherit_a_parent_name_opposed_by_every_retained_face():
    records, rows = stable_records()
    result, audit = apply_guard(records, rows, start=8/60, end=10/60,
        names=['B', 'B'], independent_names=['A', 'B'])
    assert result['decisions'][0].reference_id is None
    assert result['decisions'][0].reason == 'conflicting_projected_identity'
    assert audit['rejected'][0]['reason'] == 'conflicting_projected_identity'


def test_accepted_parent_face_inside_projection_is_not_treated_as_external_padding():
    records, rows = stable_records()
    result, audit = apply_guard(records, rows, start=8/60, end=13/60,
        names=['B', 'B'], independent_names=['A', 'B'])
    assert result['decisions'][0].reference_id == 'B'
    assert audit['rejected'] == []


def test_saved_neon_retained_face_does_not_inherit_young_from_excluded_group():
    from types import SimpleNamespace
    from dance_highlight.services.identity_projection import validate_identity_padding
    from dance_highlight.services.performance_parts import _project
    data = json.loads((Path(__file__).parent/'fixtures/dance_scene_review/neon187_projected_identity.json').read_text())
    records = [FrameRec(r['time_seconds'], r['candidate_main_id'],
        np.asarray(r['candidate_main_bbox']) if r['scene_kind'] == 'main' else None, r['scene_kind'] == 'group',
        person_bboxes=[np.asarray(b) for b in r['body_boxes']],
        person_pose_keypoints=[np.asarray(p) for p in r['pose_keypoints']],
        candidate_main_bbox=np.asarray(r['candidate_main_bbox']), scene_kind=r['scene_kind']) for r in data['pose_heads']]
    rows = [FaceObservation(**{k:np.asarray(v) if k == 'embedding' and v is not None else v
        for k,v in r.items()}) for r in data['owned_observations']]
    parent = output_parts([(*data['parent']['range'], '영', 'A')])
    parent['decisions'][0] = replace(parent['decisions'][0], reason='member_timeline_consensus')
    parent['evidence'] = [[(r, None) for r in rows]]
    projected = [(0, Segment('main', None, *data['part'], []))]
    result, audit = validate_identity_padding(_project(parent, projected), parent, projected,
        frame_records=records, fps=data['fps'], sample_step=4, cut_frames=[], handoffs=[],
        matcher=SimpleNamespace(match=lambda *_: SimpleNamespace(reference_id=None)),
        joint_matches=data['joint_matches'], frozen_observations=rows)
    assert result['decisions'][0].reference_id is None  # No single-frame guess of the competing name.
    assert audit['rejected'][0]['conflicting_faces'] == [dict(frame=11252, name='아이찡')]
    assert parent['decisions'][0].reference_id == '영'


def test_later_face_recovery_cannot_reuse_the_rejected_parent_vote():
    from dance_highlight.services.identity_projection import validate_identity_padding
    from dance_highlight.services.member_timeline import recover_final_face_edges
    from test_dance_member_timeline import Matcher
    parent = output_parts([(0., .4, 'B', 'B'), (.4, 1., 'B', 'B')])
    parent['decisions'][0] = replace(parent['decisions'][0], reason='member_timeline_consensus')
    row = next(r for r, _ in parent['evidence'][0] if abs(r.time_seconds-.36) < 1e-6)
    parent['fallback_names'] = {row.frame_index: 'B'}
    projected = [(0, replace(parent['segments'][0], start=.35)), (1, parent['segments'][1])]
    records = [FrameRec(row.time_seconds, 0, np.asarray(row.body_bbox), False, scene_kind='main')]
    joints = {row.frame_index: dict(status='accepted', name='A')}
    result, _ = validate_identity_padding(_project(parent, projected), parent, projected,
        frame_records=records, fps=100., sample_step=4, cut_frames=[], handoffs=[],
        matcher=Matcher(), joint_matches=joints, frozen_observations=[row])
    recovered = recover_final_face_edges(result, Matcher(), handoffs=[], joint_matches=joints)
    assert recovered['decisions'][0].reference_id is None
    assert len(recovered['segments']) == 2
    assert parent['fallback_names'][row.frame_index] == 'B'
    assert dict((r.frame_index, n) for r,n in parent['evidence'][0])[row.frame_index] == 'B'


def test_unobserved_short_piece_keeps_name_when_same_body_connects_to_face():
    records, rows = stable_records()
    result, audit = apply_guard(records, rows)
    assert result['decisions'][0].reference_id == 'B'
    assert not audit['rejected'] and audit['verified'][0]['support_frame'] == 8


@pytest.mark.parametrize('kind', ['cut', 'cut_at_anchor', 'missing_record', 'ambiguous_pose', 'no_pose', 'handoff'])
def test_padding_cannot_cross_missing_or_conflicting_source_evidence(kind):
    records, rows = stable_records()
    cuts=[]
    if kind == 'cut': cuts=[3]
    elif kind == 'cut_at_anchor': cuts=[8]
    elif kind == 'missing_record': records.pop(1)
    elif kind == 'ambiguous_pose':
        records[1].person_bboxes.append(records[1].main_bbox.copy()+1)
        records[1].person_pose_keypoints.append(records[1].person_pose_keypoints[0].copy())
    elif kind == 'no_pose': records[1].person_pose_keypoints=[]
    else:
        records[1].candidate_main_bbox = records[1].main_bbox = np.array([200.,0.,280.,210.])
        records[1].person_bboxes[0]=records[1].main_bbox
        records[1].person_pose_keypoints[0][:,0]+=190
    result, audit=apply_guard(records,rows,cuts=cuts)
    assert result['decisions'][0].reference_id is None and audit['rejected']


def test_direct_face_inside_piece_is_not_rejected_for_short_duration():
    records, rows=stable_records()
    rows.insert(0,replace(rows[0],frame_index=2,time_seconds=2/60))
    result,audit=apply_guard(records,rows,cuts=[1])
    assert result['decisions'][0].reference_id == 'B' and not audit['rejected']


def test_suffix_padding_checks_the_whole_part_not_only_its_start():
    records, rows=stable_records()
    rows=[replace(rows[0],frame_index=0,time_seconds=0.)]
    records[-1].person_pose_keypoints[0][:,0]+=190
    result,audit=apply_guard(records,rows,start=.14,end=.23)
    assert result['decisions'][0].reference_id is None and audit['rejected']


def test_an_unnamed_face_on_a_different_body_is_not_the_named_support():
    records, rows=stable_records()
    records[-1].person_pose_keypoints[0][:,0]+=190
    result,audit=apply_guard(records,rows,names=[None,'B'])
    assert result['decisions'][0].reference_id is None
    assert audit['rejected'][0]['support_frame'] == 12


def test_parent_consensus_without_a_named_original_face_is_not_an_anchor():
    records, rows=stable_records()
    result,audit=apply_guard(records,rows,names=[None,None])
    assert result['decisions'][0].reference_id is None
    assert audit['rejected'][0]['reason'] == 'no_named_source_support'


def test_window_voted_evidence_name_is_not_an_independent_anchor():
    records,rows=stable_records()
    result,audit=apply_guard(records,rows,names=['B','B'],independent_names=[None,None])
    assert result['decisions'][0].reference_id is None
    assert audit['rejected'][0]['reason'] == 'no_named_source_support'


def test_conflicting_original_face_models_cannot_supply_a_padding_anchor():
    records,rows=stable_records()
    result,audit=apply_guard(records,rows,primary_name='A')
    assert result['decisions'][0].reference_id is None
    assert audit['rejected'][0]['reason'] == 'no_named_source_support'


def test_joint_conflict_is_not_silently_treated_as_missing_second_model():
    records,rows=stable_records()
    result,audit=apply_guard(records,rows,primary_name='B',joint_status='conflict')
    assert result['decisions'][0].reference_id is None
    assert audit['rejected'][0]['reason'] == 'no_named_source_support'


def test_positive_other_identity_on_same_pose_path_vetoes_distant_name():
    records,rows=stable_records()
    result,audit=apply_guard(records,rows,independent_names=['A','B'])
    assert result['decisions'][0].reference_id is None
    assert audit['rejected'][0]['reason'] == 'conflicting_original_face'
    assert audit['rejected'][0]['conflicting_faces'][0]['frame'] == 8
