"""An original face run may name an observed main edge, never an unseen gap."""
from dataclasses import replace
import numpy as np
import pytest

from test_dance_body_continuity import example
from dance_highlight.services.reference_matcher import SegmentReferenceDecision


def recover(tmp_path, *, condition=None, assemble=False, direction='left'):
    from dance_highlight.services.observed_member_edges import recover_observed_member_edges
    path, output, records = example(tmp_path, cut=condition == 'cut', overlap=condition == 'competitor')
    # A continuous main loses its face at t=2 and remains selected until t=4.
    # There is no named clip on the other side to seed the old bridge.
    for key in ('segments', 'decisions', 'labels', 'previews', 'evidence', 'preview_sources'):
        output[key] = output[key][:2] if direction == 'left' else output[key][1:]
    output['accurate_indices'] = [0, 1]
    # Stop at the last observed source frame, not an extrapolated tail.
    if direction == 'left':
        output['segments'][-1] = replace(output['segments'][-1], end=3.85)
    rows = [o for evidence in output['evidence'] for o, _ in evidence]
    records = [replace(r, scene_kind='main') for r in records
               if (r.t < 4. if direction == 'left' else r.t >= 2.)]
    for record in records:
        poses = []
        for i, box in enumerate(record.person_bboxes):
            pose = np.zeros((17, 3))
            x = (box[0]+box[2])/2
            pose[[5, 6, 11, 12]] = [[x-8, 30, .99], [x+8, 30, .99],
                [x-8, 60 if i == 0 else 45, .99], [x+8, 60 if i == 0 else 45, .99]]
            poses.append(pose)
        record.person_pose_keypoints = poses
    roles = [dict(frame=round(r.t*20), box=r.main_bbox.tolist(), reason='dominant_face',
                  features=[dict(box=r.main_bbox.tolist(), source='detected', size=20.)]) for r in records]
    if condition == 'borrowed_role':
        for role in roles:
            role['features'][0]['source'] = 'repeated_same_pose_geometry'
    if condition == 'missing_role':
        roles = []
    if condition in ('duet', 'unobserved_rival', 'collapsed_rival'):
        for record in records:
            # A second foreground body reaches the central half, even when
            # face detection fails. It must remain a competitor for the role.
            record.person_bboxes[1] = np.array([75., 10., 115., 90.])
            pose = record.person_pose_keypoints[0].copy()
            pose[:, 0] += 45.
            if condition == 'unobserved_rival':
                pose[11, 2] = .1
            if condition == 'collapsed_rival':
                pose[[5, 6, 11, 12]] = [95., 40., .99]
            record.person_pose_keypoints[1] = pose
    if condition == 'single_face':
        rows = [replace(o, embedding=None, association='unassigned', failure='no_detection')
                if o.time_seconds < 1.8 else o for o in rows]
    if condition in ('missing', 'both_missing'):
        rows = [o for o in rows if o.time_seconds != 2.6]
        if condition == 'both_missing':
            records = [r for r in records if r.t != 2.6]
    if condition == 'group':
        records[13] = replace(records[13], scene_kind='group', is_group=True, main_bbox=None)
    if condition == 'conflicting_face':
        rows = [replace(o, embedding=np.array([0., 1.]), detector_score=.99,
                        association='confirmed', failure=None) if o.time_seconds == 2.6 else o for o in rows]
    class Matcher:
        def match(self, row, *args):
            return SegmentReferenceDecision('A' if row.embedding[0] else 'B', 'matched', 'original')
    handoffs = [{'frame': 52, 'time': 2.6, 'previous_time': 2.4}] if condition == 'handoff' else []
    if assemble:
        from dance_highlight.services.performance_parts import build_performance_parts
        return output, build_performance_parts(output, eligibility=output['segments'],
            matcher=Matcher(), frame_records=records, frozen_observations=rows, joint_matches={},
            fps=20., sample_step=4, handoffs=handoffs, video_path=path,
            role_observations=roles, video_size=(160, 100), scene_changes=[], cut_frames=[],
            group_segments=[], mask_refinement={})
    return output, recover_observed_member_edges(output, records, rows, {}, Matcher(),
        video_path=path, fps=20., sample_step=4, handoffs=handoffs,
        role_observations=roles, video_size=(160, 100))


def test_original_face_pair_keeps_one_main_through_one_sided_face_loss(tmp_path):
    before, (after, audit) = recover(tmp_path)
    assert [(s.start, s.end, d.reference_id) for s, d in zip(after['segments'], after['decisions'])] == [(0., 3.85, 'A')]
    assert audit['recovered_seconds'] == pytest.approx(1.85)
    assert after['anchors'] == before['anchors'] == []
    assert after['fallback_names'] == before['fallback_names'] == {}
    assert all(n is None for o, n in after['evidence'][0] if o.time_seconds >= 2.)
    assert len(before['segments']) == 2


def test_right_original_face_pair_restores_only_the_observed_main_prefix(tmp_path):
    before, (after, audit) = recover(tmp_path, direction='right')
    assert [(s.start, s.end, d.reference_id) for s, d in zip(after['segments'], after['decisions'])] == [(2., 6., 'A')]
    assert audit['recovered_seconds'] == pytest.approx(2.)
    assert audit['recoveries'][0]['directions'] == ['right']
    assert all(n is None for o, n in after['evidence'][0] if o.time_seconds < 4.)
    assert after['anchors'] == before['anchors']


@pytest.mark.parametrize('condition', ['single_face', 'missing', 'both_missing', 'group',
    'conflicting_face', 'handoff', 'cut', 'competitor', 'borrowed_role', 'missing_role',
    'duet', 'unobserved_rival', 'collapsed_rival'])
def test_one_sided_name_never_crosses_missing_or_opposing_evidence(tmp_path, condition):
    before, (after, audit) = recover(tmp_path, condition=condition)
    assert after is before
    assert audit['recovered_seconds'] == 0.


def test_performance_parts_records_recovery_separately_from_original_identity(tmp_path):
    before, (after, audit) = recover(tmp_path, assemble=True)
    assert [(s.start, s.end, d.reference_id) for s, d in zip(after['segments'], after['decisions'])] == [(0., 3.85, 'A')]
    assert [span['name'] for span in audit['identity_spans']] == ['A', None]
    assert audit['parts'][0]['newly_named_seconds'] == pytest.approx(1.85)
    assert audit['continuity']['observed_member_edges']['recovered_seconds'] == pytest.approx(1.85)
    assert after['anchors'] == before['anchors']
