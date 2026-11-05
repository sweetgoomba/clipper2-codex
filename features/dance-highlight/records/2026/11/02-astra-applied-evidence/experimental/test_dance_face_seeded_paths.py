"""A missing face is not a new part when an original face pair proves its path."""
from dataclasses import replace
import numpy as np
import pytest

from test_dance_body_continuity import example
from dance_highlight.services.face_recovery import ReferenceObservationMatcher
from dance_highlight.services.reference_matcher import ReferenceEmbeddingSample
from dance_highlight.services.segment import Segment


def setup_path(tmp_path, **kwargs):
    path, output, records = example(tmp_path, **kwargs)
    observations = [o for rows in output['evidence'] for o, _ in rows]
    for record in records:
        record.scene_kind = 'main'
    joint = {o.frame_index: dict(status='accepted', name='A')
             for o in observations if o.time_seconds >= 4.}
    for key in ('segments', 'decisions', 'labels', 'previews', 'evidence', 'preview_sources'):
        output[key] = output[key][1:]
    output['accurate_indices'] = [0, 1]
    refs = [ReferenceEmbeddingSample(n, n, str(i)*64, 160, 100, np.eye(2)[i])
            for i, n in enumerate(('A', 'B'))]
    matcher = ReferenceObservationMatcher(
        references=refs, analysis_id='test', video_sha256='a'*64,
        detector_sha256='b'*64, recognizer_sha256='c'*64, config_sha256='d'*64,
        backend_version='test', video_size=(160, 100), max_distance=.6)
    return path, output, records, observations, joint, matcher


def run(data, **kwargs):
    from dance_highlight.services.face_seeded_paths import recover_face_seeded_paths
    path, output, records, observations, joint, matcher = data
    return recover_face_seeded_paths(output, records, observations, joint, matcher,
        video_path=path, fps=20., group_segments=kwargs.pop('group_segments', []),
        handoffs=kwargs.pop('handoffs', []),
        role_observations=kwargs.pop('role_observations', [dict(frame=o.frame_index,
            box=list(o.body_bbox), closeup_subject=True, reason='measured_face_composition') for o in observations]), **kwargs)


def test_original_pair_on_one_side_recovers_whole_prefix_and_removes_its_boundary(tmp_path):
    data = setup_path(tmp_path)
    output, audit = run(data)
    assert [(s.start, s.end, d.reference_id) for s, d in
            zip(output['segments'], output['decisions'])] == [(2., 6., 'A')]
    assert audit['recovered_seconds'] == pytest.approx(2.)
    assert audit['proposals'][0]['seed_frames'] == [80, 84]
    assert output['previews'] == [[b'right']]
    assert output['anchors'] == [] and output['fallback_names'] == {}
    assert all(n is None for o, n in output['evidence'][0] if o.time_seconds < 4.)
    assert len(data[1]['segments']) == 2  # Input and original observations stay frozen.


@pytest.mark.parametrize('condition', ['cut', 'overlap', 'no_pair', 'same_frame_pair',
    'unowned_seed', 'missing_observation', 'group_at_seed', 'group_inside',
    'handoff', 'other_accepted_face', 'other_primary_face', 'no_bracket'])
def test_unverified_paths_do_not_name_or_merge_unknown(tmp_path, condition):
    data = list(setup_path(tmp_path, **{condition: True} if condition in ('cut', 'overlap') else {}))
    path, output, records, rows, joint, matcher = data
    kwargs = {}
    if condition == 'no_pair':
        data[4] = {80: joint[80]}
    elif condition == 'same_frame_pair':
        data[3] = [o for o in rows if o.frame_index < 80] + [rows[20], rows[20]]
        data[4] = {80: joint[80]}
    elif condition == 'unowned_seed':
        data[3] = [replace(o, body_bbox=(110., 10., 150., 90.)) if o.time_seconds >= 4. else o for o in rows]
    elif condition == 'missing_observation':
        data[3] = [o for o in rows if o.frame_index != 52]
    elif condition == 'group_at_seed':
        records[21].scene_kind = 'group'
    elif condition == 'group_inside':
        kwargs['group_segments'] = [Segment('group', None, 3.1, 3.2, [])]
    elif condition == 'handoff':
        kwargs['handoffs'] = [dict(frame=60)]
    elif condition in ('other_accepted_face', 'other_primary_face'):
        data[3] = [replace(o, embedding=np.array([0., 1.]), detector_score=.99,
                           association='confirmed', failure=None, face_bbox=(40.,12.,55.,28.))
                   if o.frame_index == 60 else o for o in rows]
        if condition == 'other_accepted_face':
            joint[60] = dict(status='accepted', name='B')
    elif condition == 'no_bracket':
        data[3] = [o for o in rows if o.time_seconds > 2.]
        data[2] = [r for r in records if r.t > 2.]
    result, audit = run(data, **kwargs)
    assert result is output
    assert audit['recovered_seconds'] == 0.


def test_original_pair_cannot_be_replaced_by_recovered_output_names(tmp_path):
    data = list(setup_path(tmp_path))
    data[4] = {}
    output, audit = run(data)
    assert output is data[1]
    assert audit['proposals'] == []


def test_proven_prefix_is_idempotent_and_never_split_by_duration(tmp_path):
    data = list(setup_path(tmp_path))
    data[1]['segments'][0] = replace(data[1]['segments'][0], start=0.)
    output, audit = run(data)
    assert [(s.start, s.end) for s in output['segments']] == [(0., 6.)]
    data[1] = output
    again, second_audit = run(data)
    assert again is output
    assert second_audit['proposals'] == []


def test_two_successful_original_paths_with_different_names_stay_unresolved(tmp_path):
    data = list(setup_path(tmp_path))
    path, full, records = example(tmp_path)
    for r in records:
        r.scene_kind = 'main'
    rows = [o for part in full['evidence'] for o, _ in part]
    rows = [replace(o, embedding=None, association='unassigned', failure='no_detection')
            if o.frame_index == 80 else replace(o, embedding=np.array([0.,1.]))
            if o.time_seconds > 4. else o for o in rows]
    full['decisions'][2] = replace(full['decisions'][2], reference_id='B')
    joint = {o.frame_index: dict(status='accepted', name='A' if o.time_seconds < 2. else 'B')
             for o in rows if o.time_seconds < 2. or o.time_seconds > 4.}
    data[:5] = [path, full, records, rows, joint]
    result, audit = run(data)
    assert result is full
    assert audit['candidates'][0]['reason'] == 'conflicting_paths'


def test_source_fps_mismatch_never_proves_different_frames(tmp_path):
    from dance_highlight.services.face_seeded_paths import recover_face_seeded_paths
    path, out, records, rows, joint, matcher = setup_path(tmp_path)
    # Maintain row/frame agreement but request an incompatible source timebase.
    records = [replace(r, t=r.t*2) for r in records]
    rows = [replace(o, time_seconds=o.time_seconds*2) for o in rows]
    out['segments'] = [replace(s, start=s.start*2, end=s.end*2) for s in out['segments']]
    result, audit = recover_face_seeded_paths(out, records, rows, joint, matcher,
        video_path=path, fps=10., group_segments=[], handoffs=[],
        role_observations=[dict(frame=o.frame_index, box=list(o.body_bbox), closeup_subject=True) for o in rows])
    assert result is out
    assert audit['candidates'][0]['paths'][0]['reason'] == 'source_unavailable_or_fps_mismatch'


@pytest.mark.parametrize('condition', ['missing', 'fallback', 'wrong_subject', 'one_frame', 'wide_inside_unknown'])
def test_identity_path_without_two_original_positive_role_observations_is_not_applied(tmp_path, condition):
    data = setup_path(tmp_path)
    roles = [dict(frame=o.frame_index, box=list(o.body_bbox), closeup_subject=True) for o in data[3]]
    if condition == 'missing':
        roles = []
    elif condition == 'fallback':
        for r in roles:
            r['closeup_subject'] = False
    elif condition == 'wrong_subject':
        for r in roles:
            r['box'] = [110.,10.,150.,90.]
    elif condition == 'one_frame':
        roles = [r for r in roles if r['frame'] == 80]
    elif condition == 'wide_inside_unknown':
        next(r for r in roles if r['frame'] == 60)['closeup_subject'] = False
    result, audit = run(data, role_observations=roles)
    assert result is data[1]
    assert audit['recovered_seconds'] == 0.
