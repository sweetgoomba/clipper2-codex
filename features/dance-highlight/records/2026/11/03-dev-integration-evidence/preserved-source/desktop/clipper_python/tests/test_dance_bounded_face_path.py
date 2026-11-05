"""A source jump needs original, uniquely owned pixels in both directions."""
import json
from dataclasses import replace
from pathlib import Path

import cv2
import numpy as np
import pytest

from dance_highlight.services.face_evidence import FaceObservation
from dance_highlight.services.segment import FrameRec


FIXTURE = Path(__file__).parent / 'fixtures/dance_face_path'


class SourceFrames:
    def __init__(self, images):
        self.images = images
        self.position = min(images)
        self.read_frames = []
        self.seek_frames = []

    def set(self, prop, value):
        assert prop == cv2.CAP_PROP_POS_FRAMES
        self.position = int(value)
        self.seek_frames.append(self.position)
        return True

    def get(self, prop):
        assert prop == cv2.CAP_PROP_POS_FRAMES
        return self.position

    def read(self):
        frame = self.position
        self.position += 1
        self.read_frames.append(frame)
        return frame in self.images, self.images.get(frame)


def actual_window():
    data = json.loads((FIXTURE / 'mmn38.json').read_text())
    images = {f: cv2.imread(str(FIXTURE / f'mmn38-{f}.png')) for f in data['source_frames']}
    rows, records = [], {}
    for endpoint in data['endpoints']:
        row = FaceObservation(**endpoint['observation'])
        rows.append(row)
        records[row.frame_index] = FrameRec(
            row.time_seconds, row.track_id, np.asarray(row.body_bbox), False,
            person_bboxes=[np.asarray(b) for b in endpoint['body_boxes']],
            person_head_keypoints=[np.asarray(h) for h in endpoint['head_keypoints']])
    return images, rows, records


def prove(images, rows, records, jumps=(2298,)):
    from dance_highlight.services.bounded_face_path import prove_source_face_paths
    cap = SourceFrames(images)
    result = prove_source_face_paths(cap, rows, records, jumps)
    json.dumps(result)  # Audit must use ordinary JSON values.
    return result, cap


def test_original_zoom_has_two_independent_owned_face_paths():
    images, rows, records = actual_window()
    result, cap = prove(images, rows, records)
    assert result['accepted']
    assert cap.read_frames == [2296, 2297, 2298, 2299, 2300]
    assert result['windows'][0]['frames'] == [2296, 2300]
    assert all(d['survived'] >= 6 for d in result['windows'][0]['directions'])
    assert result['seconds'] >= 0


@pytest.mark.parametrize('case', ['other_face', 'flash', 'no_person', 'occlusion_then_other'])
def test_unsampled_other_person_or_missing_pixels_never_bridge(case):
    images, rows, records = actual_window()
    images = {f: im.copy() for f, im in images.items()}
    if case in ('flash', 'no_person'):
        images[2298][:] = 255 if case == 'flash' else 0
    else:
        donor = cv2.imread(str(FIXTURE / 'mmn38-other-face.png'))
        for frame in ([2298] if case == 'other_face' else [2298, 2299, 2300]):
            images[frame][110:280, 190:320] = cv2.resize(donor, (130, 170))
        if case == 'occlusion_then_other':
            images[2298][110:280, 190:320] = 127
    result, _ = prove(images, rows, records)
    assert not result['accepted']


@pytest.mark.parametrize('case', ['unowned', 'failure', 'low_score', 'missing_face',
                                 'outside_image', 'missing_head', 'competing_head'])
def test_endpoint_face_must_have_original_exclusive_owner(case):
    images, rows, records = actual_window()
    if case == 'unowned':
        rows[0] = replace(rows[0], association='ambiguous')
    elif case == 'failure':
        rows[0] = replace(rows[0], failure='no_detection')
    elif case == 'low_score':
        rows[0] = replace(rows[0], detector_score=.79)
    elif case == 'missing_face':
        rows[0] = replace(rows[0], face_bbox=None)
    elif case == 'outside_image':
        rows[0] = replace(rows[0], face_bbox=(-10., 10., 20., 40.))
    else:
        record = records[2296]
        if case == 'missing_head':
            record.person_head_keypoints = []
        else:
            # The original selected head is body index 1 in this source frame.
            record.person_head_keypoints[4] = record.person_head_keypoints[1].copy()
    result, _ = prove(images, rows, records)
    assert not result['accepted']


@pytest.mark.parametrize('endpoint', [0, 1])
@pytest.mark.parametrize('change', [dict(face_bbox=None), dict(association='ambiguous'),
                                  dict(failure='no_detection'), dict(detector_score=.79),
                                  dict(face_bbox=(1., 2., 3.)),
                                  dict(face_bbox=(1., 2., float('nan'), 4.))])
def test_missing_endpoint_evidence_does_not_spend_source_reads(endpoint, change):
    images, rows, records = actual_window()
    rows[endpoint] = replace(rows[endpoint], **change)
    result, cap = prove(images, rows, records)
    assert not result['accepted']
    assert cap.seek_frames == []
    assert cap.read_frames == []
    assert result['decoded_frames'] == 0


def test_second_jump_cannot_borrow_a_successful_first_window():
    images, rows, records = actual_window()
    rows.append(replace(rows[0], frame_index=2304, time_seconds=2304/59.94005994))
    records[2304] = records[2296]
    images.update({2300+i: images[2300-i].copy() for i in range(1, 5)})
    images[2302][:] = 0
    result, cap = prove(images, rows, records, (2298, 2302))
    assert not result['accepted']
    assert result['windows'][0]['accepted']
    assert 2302 in cap.read_frames


@pytest.mark.parametrize('case', ['uncovered_jump', 'too_many_frames', 'missing_source'])
def test_only_complete_adjacent_original_windows_are_allowed(case):
    images, rows, records = actual_window()
    jumps = (2296,) if case == 'uncovered_jump' else (2298,)
    if case == 'too_many_frames':
        rows[-1] = replace(rows[-1], frame_index=2304)
        records[2304] = records.pop(2300)
    elif case == 'missing_source':
        del images[2298]
    result, _ = prove(images, rows, records, jumps)
    assert not result['accepted']


def test_featureless_face_is_not_positive_continuity():
    images, rows, records = actual_window()
    result, _ = prove({f: np.zeros_like(im) for f, im in images.items()}, rows, records)
    assert not result['accepted']


@pytest.mark.parametrize('case', ['opencv_error', 'missing_flow'])
def test_unavailable_optical_flow_preserves_unconfirmed_result(monkeypatch, case):
    from dance_highlight.services import bounded_face_path
    images, rows, records = actual_window()
    def unavailable(*args, **kwargs):
        if case == 'opencv_error':
            raise cv2.error('optical flow unavailable')
        return None, None, None
    monkeypatch.setattr(bounded_face_path.cv2, 'calcOpticalFlowPyrLK', unavailable)
    result, _ = prove(images, rows, records)
    assert not result['accepted']
    assert result['reason'] in ('source_pixel_proof_unavailable', 'unconfirmed_reciprocal_face_pixels')
    assert result['seconds'] >= 0


def test_pixel_verifier_does_not_hide_programming_errors(monkeypatch):
    from dance_highlight.services import bounded_face_path
    images, rows, records = actual_window()
    def broken(*args, **kwargs):
        raise RuntimeError('programming error')
    monkeypatch.setattr(bounded_face_path.cv2, 'calcOpticalFlowPyrLK', broken)
    with pytest.raises(RuntimeError, match='programming error'):
        prove(images, rows, records)


@pytest.mark.parametrize('condition', ['cut', 'overlap', 'conflict', 'different_name'])
def test_existing_cut_body_and_name_guards_reject_before_the_pixel_exception(tmp_path, monkeypatch, condition):
    from dance_highlight.services import bounded_face_path, body_continuity
    from dance_highlight.services.reference_matcher import SegmentReferenceDecision
    from test_dance_body_continuity import example
    path, output, records = example(tmp_path, **{condition: True} if condition != 'different_name' else {})
    if condition == 'different_name':
        output['decisions'][-1] = SegmentReferenceDecision('B', 'matched', 'test')
    def must_not_run(*args, **kwargs):
        raise AssertionError('Earlier cut/body/identity failure must not request a pixel exception')
    monkeypatch.setattr(bounded_face_path, 'prove_source_face_paths', must_not_run)
    result, audit = body_continuity.bridge_main_face_gaps(output, records, path)
    assert result is output
    assert audit['recovered_seconds'] == 0.
