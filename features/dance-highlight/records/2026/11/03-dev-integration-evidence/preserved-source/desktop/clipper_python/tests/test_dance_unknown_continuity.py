"""Unknown identity does not require one clip per face inference scope."""
from dataclasses import replace
import numpy as np
import pytest
from test_dance_body_continuity import example
from dance_highlight.services.reference_matcher import SegmentReferenceDecision


def run(tmp_path, condition=None):
    from dance_highlight.services.output_continuity import coalesce_unknown_output
    path, output, records = example(tmp_path, cut=condition == 'cut', overlap=condition == 'competitor')
    output['decisions'] = [SegmentReferenceDecision(None, 'unmatched', 'no_consensus') for _ in range(3)]
    output['labels'] = [None]*3
    if condition == 'named_middle':
        output['decisions'][1] = SegmentReferenceDecision('B', 'matched', 'original')
    records = [replace(r, scene_kind='main') for r in records]
    if condition == 'unnamed_face_change':
        output['evidence'] = [[(replace(o,
            embedding=np.array([1., 0.]) if o.time_seconds < 2. else np.array([0., 1.]),
            detector_score=.99, association='confirmed', failure=None), None)
            for o, _ in evidence] for evidence in output['evidence']]
    rows = [o for evidence in output['evidence'] for o, _ in evidence]
    if condition == 'missing':
        records = [r for r in records if r.t != 2.6]
        rows = [o for o in rows if o.time_seconds != 2.6]
    handoffs = [dict(time=2., previous_time=1.8), dict(time=4., previous_time=3.8)] if condition == 'handoff' else []
    joints = {0: dict(status='accepted', name='A'), 40: dict(status='accepted', name='B'),
              80: dict(status='accepted', name='C')} if condition == 'conflicting_faces' else {}
    result = coalesce_unknown_output(output, records, rows, joints,
        fps=20., sample_step=4, handoffs=handoffs, video_path=path)
    return output, result


def test_continuous_unidentified_main_is_one_part_without_borrowing_a_name(tmp_path):
    original, (result, audit) = run(tmp_path)
    assert [(s.start, s.end) for s in result['segments']] == [(0., 6.)]
    assert [d.reference_id for d in result['decisions']] == [None]
    assert len(audit['joins']) == 2
    assert result['evidence'][0] == sum(original['evidence'], [])
    assert result['anchors'] == original['anchors']
    assert len(original['segments']) == 3


@pytest.mark.parametrize('condition', ['cut', 'competitor', 'missing', 'handoff', 'conflicting_faces', 'named_middle'])
def test_unknown_identity_does_not_authorize_erasing_a_performer_boundary(tmp_path, condition):
    original, (result, audit) = run(tmp_path, condition)
    assert len(result['segments']) >= 2
    if condition in ('handoff', 'conflicting_faces', 'named_middle', 'competitor'):
        assert result is original
        assert not audit['joins']


def test_repeated_different_faces_keep_the_boundary_even_without_registered_names(tmp_path):
    _, (result, audit) = run(tmp_path, 'unnamed_face_change')
    assert [(s.start, s.end) for s in result['segments']] == [(0., 2.), (2., 6.)]
    assert audit['candidates'][0]['reason'] == 'repeated_original_face_change'
    assert all(d.reference_id is None for d in result['decisions'])
