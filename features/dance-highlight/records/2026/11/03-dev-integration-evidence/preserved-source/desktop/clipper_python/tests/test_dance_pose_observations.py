"""Duplicate full-body observations must not become two face owners."""
import copy
import json
from pathlib import Path

import numpy as np
import pytest

from dance_highlight.services.segment import FrameRec


def fixture(name='neon53_duplicate_observations.json'):
    data = json.loads((Path(__file__).parent /
        'fixtures/dance_scene_review'/name).read_text())
    records = [FrameRec(p['time_seconds'], 1, np.asarray(p['candidate_main_bbox']), False,
        person_bboxes=[np.asarray(b) for b in p['body_boxes']],
        person_head_keypoints=[np.asarray(k) for k in p['head_keypoints']],
        person_pose_keypoints=[np.asarray(k) for k in p['pose_keypoints']]) for p in data['pose_heads']]
    return data, records


def normalize(records, fps):
    from dance_highlight.services.pose_observations import canonicalize_pose_observations
    return canonicalize_pose_observations(records, fps=fps)


def test_same_source_head_torso_and_legs_have_one_face_owner():
    from dance_highlight.services.face_evidence import select_pose_face

    data, records = fixture()
    original_counts = [len(r.person_bboxes) for r in records]
    result, audit = normalize(records, data['fps'])
    assert [len(r.person_bboxes) for r in result] == [n - (0 < i < 6) for i,n in enumerate(original_counts)]
    assert len(audit['changes']) == 5
    assert [len(r.person_bboxes) for r in records] == original_counts
    for i in range(1, 6):
        record = result[i]
        own = next(j for j,b in enumerate(record.person_bboxes) if np.array_equal(b, record.main_bbox))
        head = record.person_head_keypoints[own][:3,:2]
        face = np.r_[head.min(0)-2, head.max(0)+2]
        index, failure = select_pose_face([face], record.main_bbox, record)
        assert index == 0 and failure is None


def test_reordering_detector_candidates_cannot_change_the_canonical_observations():
    data, records = fixture()
    reordered = copy.deepcopy(records)
    for r in reordered:
        r.person_bboxes.reverse()
        r.person_head_keypoints.reverse()
        r.person_pose_keypoints.reverse()
    a, _ = normalize(records, data['fps'])
    b, _ = normalize(reordered, data['fps'])
    for x,y in zip(a,b):
        assert sorted(tuple(v) for v in x.person_bboxes) == sorted(tuple(v) for v in y.person_bboxes)
        assert np.array_equal(x.main_bbox, y.main_bbox)


@pytest.mark.parametrize('different', ['head', 'torso', 'hips', 'legs', 'low_face_confidence', 'low_torso_confidence', 'low_leg_confidence'])
def test_overlapping_boxes_do_not_merge_distinct_or_unobserved_people(different):
    data, records = fixture()
    record = records[1]
    first, second = 5, 7
    r = FrameRec(record.t, 1, record.person_bboxes[first], False,
        person_bboxes=[record.person_bboxes[first].copy(), record.person_bboxes[second].copy()],
        person_pose_keypoints=[record.person_pose_keypoints[first].copy(), record.person_pose_keypoints[second].copy()])
    pose = r.person_pose_keypoints[1]
    if different == 'head':
        pose[:5,0] += 70
    elif different == 'torso':
        pose[[5,6,11,12],0] += 150
    elif different == 'legs':
        pose[13:17,0] += 150
    elif different == 'hips':
        pose[[11,12],1] += 150
    elif different == 'low_leg_confidence':
        pose[13:17,2] = .4
    elif different == 'low_face_confidence':
        pose[:3,2] = .4
    else:
        pose[[5,6,11,12],2] = .4
    r.person_head_keypoints = [p[:5] for p in r.person_pose_keypoints]
    result, audit = normalize([r], data['fps'])
    assert len(result[0].person_bboxes) == 2
    assert not audit['changes']


def test_role_and_identity_stages_receive_the_same_canonical_observations(tmp_path, monkeypatch):
    from dance_highlight.services import observed_main, native_scene
    from dance_highlight.services.pipeline import DancePipeline
    from dance_highlight.services.config import DanceConfig
    from dance_highlight.services.reference_matcher import ReferenceEmbeddingSample

    data, records = fixture()
    expected, _ = normalize(records, data['fps'])
    expected_counts = [len(r.person_bboxes) for r in expected]
    seen = []

    def refine(rows, *args, **kwargs):
        assert [len(r.person_bboxes) for r in rows] == expected_counts
        seen.append('role')
        return rows, dict(reason='complete', cut_frames=[], handoffs=[])

    monkeypatch.setattr(observed_main, 'refine_main_roles', refine)
    monkeypatch.setattr(native_scene, 'refine_native_scenes', lambda rows, *a, **k: (rows, {}))

    class ReachedFace(Exception):
        pass

    class Face:
        def batch_segment_embeddings(self, source, segments, **kwargs):
            assert [len(r.person_bboxes) for r in kwargs['frame_records']] == expected_counts
            seen.append('identity')
            raise ReachedFace

    pipe = DancePipeline(DanceConfig(), None, Face(), None, None)
    pipe.analyze_video_to_records = lambda *a, **k: (records, data['fps'], records[-1].t+.1)
    pipe._download_reference_images = lambda *a: {}

    def refs(paths, sample_sink):
        sample_sink.append(ReferenceEmbeddingSample('A', 'A', 'a'*64, 100, 100, np.array([1.,0.])))
        return {}

    pipe._build_reference_embeddings = refs
    pipe._video_size = lambda *a: (1920,1080)
    source = tmp_path/'source.mp4'
    source.write_bytes(b'source')
    with pytest.raises(ReachedFace):
        pipe.run(tmp_path, source, 1)
    assert seen == ['role', 'identity']


def test_uncertain_ears_cannot_expand_head_match_tolerance():
    from dance_highlight.services.pose_observations import _same_full_body
    _, records = fixture()
    r = records[1]
    a,b = [r.person_bboxes[i].copy() for i in (5,7)]
    pa,pb = [r.person_pose_keypoints[i].copy() for i in (5,7)]
    pb[:3,0] += 15
    pa[3:5,2] = pb[3:5,2] = .6
    assert not _same_full_body(a,pa,b,pb)
    pa[3:5,0] = [a[0]+1,a[2]-1]
    pb[3:5,0] = [b[0]+1,b[2]-1]
    assert not _same_full_body(a,pa,b,pb)


@pytest.mark.parametrize('invalid_legs', [[0.,0.], [975.,440.]])
def test_matching_but_anatomically_impossible_legs_are_not_full_body_evidence(invalid_legs):
    from dance_highlight.services.pose_observations import _same_full_body
    _, records = fixture()
    r = records[1]
    a,b = [r.person_bboxes[i].copy() for i in (5,7)]
    pa,pb = [r.person_pose_keypoints[i].copy() for i in (5,7)]
    pa[13:17,:2] = pb[13:17,:2] = invalid_legs
    assert not _same_full_body(a,pa,b,pb)


def test_non_transitive_duplicate_component_is_preserved_and_idempotent():
    data, records = fixture()
    source = records[1]
    box, pose = source.person_bboxes[5], source.person_pose_keypoints[5]
    boxes = [box+np.array([dx,0,dx,0]) for dx in (0,-10,10)]
    poses = [pose+np.array([dx,0,0]) for dx in (0,-10,10)]
    record = FrameRec(source.t, 1, box, False, person_bboxes=boxes,
        person_pose_keypoints=poses, person_head_keypoints=[p[:5] for p in poses])
    first, audit = normalize([record], data['fps'])
    second, _ = normalize(first, data['fps'])
    assert len(first[0].person_bboxes) == len(second[0].person_bboxes) == 3
    assert not audit['changes']


@pytest.mark.parametrize('mirrored', [False, True])
def test_shared_head_cannot_hide_a_leg_chain_owned_by_another_person(mirrored):
    data, records = fixture('mmn_hybrid_observation.json')
    r = records[0]
    if mirrored:
        for b in r.person_bboxes:
            b[0],b[2] = 1920-b[2],1920-b[0]
        for p in r.person_pose_keypoints:
            p[:,0] = 1920-p[:,0]
        r.person_bboxes.reverse()
        r.person_pose_keypoints.reverse()
        r.person_head_keypoints = [p[:5] for p in r.person_pose_keypoints]
    out, audit = normalize(records, data['fps'])
    assert len(out[0].person_bboxes) == len(r.person_bboxes)
    assert not audit['changes']


@pytest.mark.parametrize('unrelated_joints', [[14,16], [12], [6]])
def test_missing_other_side_of_foreign_person_cannot_authorize_hybrid_merge(unrelated_joints):
    data, records = fixture('mmn_hybrid_observation.json')
    r = records[0]
    r.person_pose_keypoints[3][unrelated_joints,2] = .1
    out, audit = normalize(records, data['fps'])
    assert len(out[0].person_bboxes) == len(r.person_bboxes)
    assert not audit['changes']
