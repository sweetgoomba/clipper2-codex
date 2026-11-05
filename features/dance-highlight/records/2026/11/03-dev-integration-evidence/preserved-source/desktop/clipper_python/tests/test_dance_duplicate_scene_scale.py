"""Same-person duplicate geometry must not invent a foreground scale veto."""
from dataclasses import replace
import json
from pathlib import Path

import numpy as np
import pytest

from dance_highlight.services import segment
from dance_highlight.services.segment import FrameRec


def _actual():
    row = json.loads((Path(__file__).parent / 'fixtures/dance_scene_review/neon185_duplicate.json').read_text())
    return FrameRec(row['time_seconds'], row['candidate_main_id'], np.array(row['candidate_main_bbox']), False,
        person_bboxes=[np.array(b) for b in row['body_boxes']],
        person_head_keypoints=[np.array(p) for p in row['head_keypoints']],
        person_pose_keypoints=[np.array(p) for p in row['pose_keypoints']])


def _snapshot(record):
    return [[value.copy() for value in getattr(record, key)] for key in (
        'person_bboxes', 'person_head_keypoints', 'person_pose_keypoints')]


def _assert_original_observations(record, frozen):
    for key, expected in zip(('person_bboxes', 'person_head_keypoints', 'person_pose_keypoints'), frozen):
        actual = getattr(record, key)
        assert len(actual) == len(expected)
        assert all(np.array_equal(a, b) for a, b in zip(actual, expected))


def test_actual_same_head_torso_duplicate_does_not_veto_ensemble_or_delete_source_observations():
    record = _actual()
    frozen = _snapshot(record)
    assert len(record.person_bboxes) == 5
    assert segment.distributed_full_body_ensemble(record, (1920, 1080))
    _assert_original_observations(record, frozen)
    rows = [replace(record, t=record.t+i/10) for i in range(5)]
    classified = segment.classify_main_scenes(rows, (1920, 1080))
    assert all(r.scene_kind == 'group' for r in classified)
    for original, result in zip(rows, classified):
        _assert_original_observations(original, frozen)
        _assert_original_observations(result, frozen)
        assert len(result.group_bboxes) == 5
        assert np.array_equal(result.candidate_main_bbox, original.main_bbox)


@pytest.mark.parametrize('case', ['different_head', 'missing_head', 'different_torso',
                                 'hidden_foreground_feet', 'partial_torso'])
def test_overlapping_foreground_requires_same_complete_head_and_torso_evidence(case):
    record = _actual()
    points = record.person_pose_keypoints[3]
    if case == 'different_head':
        points[:5, 0] += 25
    elif case == 'missing_head':
        points[:5, 2] = .1
    elif case == 'different_torso':
        points[[5, 6, 11, 12], 0] += 70
    elif case == 'hidden_foreground_feet':
        points[[15, 16], 2] = .1
    else:
        points[[11, 12], 2] = .1
    frozen = _snapshot(record)
    assert not segment.distributed_full_body_ensemble(record, (1920, 1080))
    _assert_original_observations(record, frozen)


@pytest.mark.parametrize('order', [[0, 1, 2, 3, 4], [4, 3, 2, 1, 0], [3, 0, 4, 2, 1]])
def test_same_body_scale_deduplication_does_not_depend_on_detection_order(order):
    record = _actual()
    record = replace(record,
        person_bboxes=[record.person_bboxes[i] for i in order],
        person_head_keypoints=[record.person_head_keypoints[i] for i in order],
        person_pose_keypoints=[record.person_pose_keypoints[i] for i in order])
    frozen = _snapshot(record)
    assert segment.distributed_full_body_ensemble(record, (1920, 1080))
    _assert_original_observations(record, frozen)
