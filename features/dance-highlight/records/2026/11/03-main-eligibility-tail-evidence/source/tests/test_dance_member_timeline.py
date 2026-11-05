"""Dance-only member coverage: time order wins over a whole-clip label."""
from dataclasses import replace
from types import SimpleNamespace
import numpy as np
import pytest
from dance_highlight.services.face_evidence import FaceObservation
from dance_highlight.services.reference_matcher import SegmentReferenceDecision
from dance_highlight.services.segment import Segment


def observation(t, name):
    vector = {'A': [1., 0., 0.], 'B': [0., 1., 0.], '?': [0., 0., 1.]}[name]
    return FaceObservation(round(t * 30), t, 7, (0., 0., 100., 100.), (0., 0., 100., 100.),
                           face_bbox=(30., 10., 60., 40.), embedding=np.array(vector),
                           detector_score=.98, association='confirmed')


class Matcher:
    def match(self, row, *_args):
        name = 'A' if row.embedding is not None and row.embedding[0] > .9 else (
            'B' if row.embedding is not None and row.embedding[1] > .9 else None)
        return SimpleNamespace(reference_id=name, status='matched' if name else 'unmatched',
                               reason='accepted' if name else 'distance_exceeded',
                               candidates=[SimpleNamespace(reference_id=name, distance=.2)] if name else [])


def refine(rows, end, baseline='A', matcher=None, **kwargs):
    from dance_highlight.services.member_timeline import refine_member_timeline
    seg = Segment('main', 7, 0., end, [(o.time_seconds, np.array(o.body_bbox), 7) for o in rows])
    decision = SegmentReferenceDecision(baseline, 'matched' if baseline else 'unmatched', 'baseline')
    result = SimpleNamespace(owned_observations=rows, owned_previews={o.frame_index: b'face' for o in rows})
    return refine_member_timeline([seg], [decision], [7], [[]], [result], matcher or Matcher(), **kwargs)


def test_independent_secondary_names_can_recover_a_repeated_unknown_main_face():
    rows = [observation(float(t), '?') for t in np.arange(.1, 3., .2)]
    names = {row.frame_index: 'A' for row in rows}
    output = refine(rows, 3., baseline=None, fallback_names=names)
    assert [d.reference_id for d in output['decisions']] == ['A']
    assert [(s.start, s.end) for s in output['segments']] == [(0., 3.)]
    assert output['anchors'] == []  # A secondary name cannot seed AuraFace recovery.


def test_secondary_name_does_not_override_a_primary_reference_match():
    rows = [observation(float(t), 'A') for t in np.arange(.1, 3., .2)]
    output = refine(rows, 3., fallback_names={row.frame_index: 'B' for row in rows})
    assert [d.reference_id for d in output['decisions']] == ['A']


def test_several_source_cut_candidates_do_not_erase_a_confirmed_name_change():
    # A real edit can produce two adjacent source-cut detections. Both sides
    # still have repeated, independent member evidence; uncertainty about the
    # exact edit frame must not merge the two names into one unresolved part.
    rows = [observation(t, 'A') for t in (.1, .3, .5, .7)] + [
        observation(t, 'B') for t in (1.1, 1.3, 1.5, 1.7, 1.9)]
    result = refine(rows, 2., cut_times=(.8, .8333333333333334))
    assert [d.reference_id for d in result['decisions']] == ['A', 'B']
    assert result['segments'][0].end == pytest.approx(.9)
    assert result['segments'][1].start == pytest.approx(.9)
    boundary = result['audit'][0]['boundaries'][0]
    assert boundary['reason'] == 'repeated_reference_change'


def test_multiple_cut_candidates_without_different_member_support_create_no_name_boundary():
    rows = [observation(t, 'A') for t in (.1, .3, .5, .7, 1.1, 1.3, 1.5, 1.7, 1.9)]
    result = refine(rows, 2., cut_times=(.8, .8333333333333334))
    assert [d.reference_id for d in result['decisions']] == ['A']
    assert not result['audit'][0]['boundaries']


def partition_unknown(primary, boundaries):
    """Retain the primary pass's provisional cuts without adding face evidence."""
    from dance_highlight.services.main_identity import split_segment
    from copy import deepcopy
    output = deepcopy(primary)
    original = output['segments'][0]
    rows = output['evidence'][0]
    parts = split_segment(original, [{'time': t} for t in boundaries])
    output.update(segments=parts, decisions=[output['decisions'][0] for _ in parts],
                  labels=[None for _ in parts], previews=[[] for _ in parts],
                  preview_sources=[({}, {}) for _ in parts],
                  evidence=[[(o, n) for o, n in rows if p.start <= o.time_seconds < p.end]
                            for p in parts], accurate_indices=list(range(len(parts))))
    return output


def test_secondary_evidence_reconsiders_provisional_cuts_between_unknown_parts():
    from dance_highlight.services.member_timeline import refine_unresolved_with_names
    rows = [observation(t, '?') for t in (.067, .133, .2, .267, .333, .4, .467, .533)]
    primary = partition_unknown(refine(rows, .567, baseline=None), [.367])
    names = {rows[i].frame_index: 'A' for i in (0, 3, 6)}
    result = refine_unresolved_with_names(primary, names, Matcher())
    assert [(s.start, s.end, d.reference_id) for s, d in zip(result['segments'], result['decisions'])] == [(0., .567, 'A')]
    assert all(d.reference_id is None for d in primary['decisions'])
    assert result['anchors'] == []
    assert [o.frame_index for part in result['evidence'] for o, _ in part] == [o.frame_index for o in rows]


def test_secondary_reconsideration_preserves_a_real_handoff_inside_unknown_parts():
    from dance_highlight.services.member_timeline import refine_unresolved_with_names
    rows = [observation(float(t), '?') for t in np.arange(.1, 2., .1)]
    primary = partition_unknown(refine(rows, 2., baseline=None), [.45, .95, 1.45])
    names = {o.frame_index: 'A' if o.time_seconds < 1 else 'B' for o in rows}
    result = refine_unresolved_with_names(primary, names, Matcher())
    assert [d.reference_id for d in result['decisions']] == ['A', 'B']
    assert result['segments'][0].end == pytest.approx(.95)
    assert result['segments'][1].start == pytest.approx(.95)
    assert result['segments'][-1].end == 2.


def test_secondary_reconsideration_never_bridges_missing_output_time():
    from dance_highlight.services.member_timeline import refine_unresolved_with_names
    rows = [observation(t, '?') for t in (.1, .2, .5, .6)]
    primary = partition_unknown(refine(rows, .7, baseline=None), [.4])
    primary['segments'][0] = replace(primary['segments'][0], end=.3)
    names = {o.frame_index: 'A' for o in rows}
    result = refine_unresolved_with_names(primary, names, Matcher())
    assert all(d.reference_id is None for d in result['decisions'])
    assert [(s.start, s.end) for s in result['segments']] == [(0., .3), (.4, .7)]


@pytest.mark.parametrize('middle_duration', [.25, .6])
@pytest.mark.parametrize('middle_name', [None, 'B'])
def test_secondary_reconsideration_keeps_a_repeated_middle_face(middle_duration, middle_name):
    from dance_highlight.services.member_timeline import refine_unresolved_with_names
    class NoNames:
        def match(self, *_args):
            return SimpleNamespace(reference_id=None, candidates=[])
    rows = [observation(round(float(t), 6), '?') for t in np.arange(.1, 3., .05)]
    primary = partition_unknown(refine(rows, 3., baseline=None), [1.15, 1.35, 1.55])
    for i, part in enumerate(primary['evidence']):
        primary['evidence'][i] = [(replace(o, embedding=np.array([1., 0., 0.])), n)
                                  if 1. <= o.time_seconds < 1.+middle_duration else (o, n) for o, n in part]
    names = {o.frame_index: 'A' for o in rows if o.time_seconds < 1. or o.time_seconds >= 1.+middle_duration}
    if middle_name:
        names.update({o.frame_index: middle_name for o in rows if 1. <= o.time_seconds < 1.+middle_duration})
    result = refine_unresolved_with_names(primary, names, NoNames())
    assert [d.reference_id for d in result['decisions']] == ['A', middle_name, 'A']
    assert result['segments'][1].start == pytest.approx(.975)
    assert result['segments'][1].end == pytest.approx(.975+middle_duration)


def test_secondary_reconsideration_keeps_an_internal_face_observation_gap():
    from dance_highlight.services.member_timeline import refine_unresolved_with_names
    rows = [observation(round(float(t), 6), '?') for t in np.arange(.1, 3., .1)]
    primary = partition_unknown(refine(rows, 3., baseline=None), [1.2, 1.8])
    primary['evidence'] = [[(o, n) for o, n in part if o.time_seconds < 1. or o.time_seconds >= 2.]
                           for part in primary['evidence']]
    names = {o.frame_index: 'A' for part in primary['evidence'] for o, _ in part}
    result = refine_unresolved_with_names(primary, names, Matcher())
    for time, name in ((.5, 'A'), (1.5, None), (2.5, 'A')):
        assert next(d.reference_id for s, d in zip(result['segments'], result['decisions'])
                    if s.start <= time < s.end) == name


def test_secondary_reconsideration_without_new_hits_preserves_original_scopes():
    from dance_highlight.services.member_timeline import refine_unresolved_with_names
    rows = [observation(float(t), '?') for t in np.arange(.1, 2., .1)]
    primary = partition_unknown(refine(rows, 2., baseline=None), [.45, .95, 1.45])
    result = refine_unresolved_with_names(primary, {}, Matcher())
    assert [(s.start, s.end) for s in result['segments']] == [(s.start, s.end) for s in primary['segments']]
    assert result['secondary_refinements'] == []


def edge_context_primary(*, missing_gap=False, conflicting=False):
    class NoNames:
        def match(self, *_args):
            return SimpleNamespace(reference_id=None, candidates=[])
    rows = [observation(t, 'B' if conflicting and .8 <= t < 1. else 'A')
            for t in (.1, .3, .5, .7, .9, 1.1, 1.3, 1.5, 1.7, 1.9)]
    primary = partition_unknown(refine(rows, 2., baseline=None, matcher=NoNames()), [.8, 1.])
    for i in (0, 2):
        primary['decisions'][i] = SegmentReferenceDecision('A', 'matched', 'frozen_primary')
        primary['evidence'][i] = [(o, 'A') for o, _ in primary['evidence'][i]]
    if missing_gap:
        primary['segments'][0] = replace(primary['segments'][0], end=.75)
        primary['segments'][2] = replace(primary['segments'][2], start=1.05)
    return primary, rows, NoNames()


def final_edge_refinement(primary, names, matcher):
    from dance_highlight.services.member_timeline import refine_unresolved_with_names, recover_final_face_edges
    from dance_highlight.services.output_continuity import coalesce_named_output
    output=refine_unresolved_with_names(primary,names,matcher)
    output=recover_final_face_edges(output,matcher,handoffs=[])
    return coalesce_named_output(output,matcher,handoffs=[])[0]


def test_secondary_edge_uses_frozen_neighbor_faces_without_new_anchors():
    primary, rows, matcher = edge_context_primary()
    output = final_edge_refinement(primary, {rows[4].frame_index:'A'}, matcher)
    assert [(s.start, s.end, d.reference_id) for s, d in zip(output['segments'], output['decisions'])] == [(0., 2., 'A')]
    assert output['anchors'] == primary['anchors'] == []
    assert [o.frame_index for part in output['evidence'] for o, _ in part] == [o.frame_index for o in rows]
    assert primary['decisions'][1].reference_id is None


@pytest.mark.parametrize('case', ['no_new_face', 'different_face', 'misnamed_single_face', 'missing_time'])
def test_secondary_edge_cannot_invent_support_from_a_neighbor_label(case):
    primary, rows, matcher = edge_context_primary(missing_gap=case=='missing_time', conflicting=case in ('different_face','misnamed_single_face'))
    names = {} if case=='no_new_face' else {rows[4].frame_index:'B' if case=='different_face' else 'A'}
    output = final_edge_refinement(primary, names, matcher)
    assert next(d.reference_id for s, d in zip(output['segments'], output['decisions']) if s.start<=.9<s.end) is None
    for time in (.3, 1.3):
        assert next(d.reference_id for s, d in zip(output['segments'], output['decisions']) if s.start<=time<s.end)=='A'


@pytest.mark.parametrize('handoffs', [None, [{'previous_time':.7,'time':.8}]])
def test_final_face_edge_keeps_unknown_when_real_join_is_rejected(handoffs):
    from dance_highlight.services.member_timeline import recover_final_face_edges
    primary, rows, matcher = edge_context_primary()
    for key in ('segments','decisions','labels','previews','evidence','preview_sources'):
        primary[key]=primary[key][:2]
    primary['accurate_indices']=[0,1]
    primary['fallback_names']={rows[4].frame_index:'A'}
    after=recover_final_face_edges(primary,matcher,handoffs=handoffs)
    assert [(s.start,s.end,d.reference_id) for s,d in zip(after['segments'],after['decisions'])]==[(0.,.8,'A'),(.8,1.,None)]


def test_final_face_edge_recovery_does_not_create_a_detached_named_fragment():
    from dance_highlight.services.member_timeline import recover_final_face_edges
    class NoNames:
        def match(self, *_args): return SimpleNamespace(reference_id=None,candidates=[])
    rows=[observation(float(t),'A') for t in np.arange(.1,4.,.2)]
    output=partition_unknown(refine(rows,4.,baseline=None,matcher=NoNames()),[1.,3.])
    for i in (0,2):
        output['decisions'][i]=SegmentReferenceDecision('A','matched','frozen')
        output['evidence'][i]=[(o,'A') for o,_ in output['evidence'][i]]
    output['evidence'][1]=[(replace(o,embedding=np.array([0.,0.,1.])),n)
        if not 1.4<=o.time_seconds<=2. else (o,n) for o,n in output['evidence'][1]]
    output['fallback_names']={o.frame_index:'A' for o in rows if 1.4<=o.time_seconds<=2.}
    after=recover_final_face_edges(output,NoNames(),handoffs=[])
    assert [(s.start,s.end,d.reference_id) for s,d in zip(after['segments'],after['decisions'])]==[(0.,1.,'A'),(1.,3.,None),(3.,4.,'A')]


def test_one_secondary_hit_cannot_create_a_member_part():
    rows = [observation(float(t), '?') for t in np.arange(.1, 3., .2)]
    output = refine(rows, 3., baseline=None, fallback_names={rows[3].frame_index: 'A'})
    assert all(d.reference_id is None for d in output['decisions'])


def test_distant_secondary_hits_do_not_count_as_a_repeated_local_identity():
    from dance_highlight.services.member_timeline import refine_unresolved_with_names
    rows = [observation(float(t), '?') for t in np.arange(.1,6.,.2)]
    primary = refine(rows,6.,baseline=None)
    output = refine_unresolved_with_names(primary,{rows[0].frame_index:'A',rows[-1].frame_index:'A'},Matcher())
    assert all(d.reference_id is None for d in output['decisions'])


def test_secondary_hit_cannot_name_an_unowned_face():
    rows = [replace(observation(float(t), '?'), association='ambiguous') for t in np.arange(.1, 3., .2)]
    output = refine(rows, 3., baseline=None, fallback_names={row.frame_index: 'A' for row in rows})
    assert all(d.reference_id is None for d in output['decisions'])


@pytest.mark.parametrize('recovered_name', ['A', 'B'])
def test_secondary_refinement_is_confined_to_unknown_intervals(recovered_name):
    from dance_highlight.services.member_timeline import refine_unresolved_with_names
    rows = [observation(float(t), '?' if t < 2 else 'A') for t in np.arange(.1,6.,.2)]
    primary = refine(rows,6.,baseline=None)
    assert [d.reference_id for d in primary['decisions']] == [None,'A']
    original_start = primary['segments'][1].start
    fallback = {row.frame_index:recovered_name for row in rows}  # Includes known instants deliberately.
    output = refine_unresolved_with_names(primary,fallback,Matcher())
    assert [d.reference_id for d in primary['decisions']] == [None,'A']
    for seg, decision in zip(output['segments'],output['decisions']):
        if seg.end > original_start + 1e-6:
            assert decision.reference_id == 'A'
    if recovered_name == 'A':
        assert [(s.start,s.end) for s in output['segments']] == [(0.,6.)]
    else:
        assert [d.reference_id for d in output['decisions']] == ['B','A']
        assert output['segments'][0].end == pytest.approx(original_start)


def test_already_named_ten_second_clip_splits_six_second_a_four_second_b_at_same_position():
    rows = [observation(float(t), 'A' if t < 6 else 'B') for t in np.arange(.1, 10, .2)]
    result = refine(rows, 10.)
    pieces = list(zip(result['segments'], result['decisions']))
    assert {d.reference_id for _, d in pieces} == {'A', 'B'}
    assert len(pieces) == 2
    assert [s.end - s.start for s, _ in pieces] == pytest.approx([6., 4.])
    assert all(s.end <= 6.0001 if d.reference_id == 'A' else s.start >= 5.9999 for s, d in pieces)
    assert sum(len(s.bboxes) for s, _ in pieces) == len(rows)
    assert sum(s.end - s.start for s, _ in pieces) == pytest.approx(10.)


@pytest.mark.parametrize('duration', [6., 10., 30.])
def test_continuous_main_performer_remains_one_clip_without_duration_limit(duration):
    rows = [observation(float(t), 'A') for t in np.arange(.1, duration, .2)]
    result = refine(rows, duration)
    assert [(s.start, s.end) for s in result['segments']] == [(0., duration)]
    assert [d.reference_id for d in result['decisions']] == ['A']


@pytest.mark.parametrize('secondary', [False, True])
def test_same_member_view_change_does_not_survive_as_a_final_clip_boundary(secondary):
    from dance_highlight.services.member_timeline import refine_unresolved_with_names
    class Views(Matcher):
        def match(self, row, *_args):
            if not _args[-1].endswith('-piece'):
                return SimpleNamespace(reference_id=None, candidates=[])
            return SimpleNamespace(reference_id='A', candidates=[SimpleNamespace(reference_id='A', distance=.2)])
    rows = [replace(observation(float(t), 'A'),
                    embedding=np.array([1.,0.,0.]) if t < 3 else np.array([.3,np.sqrt(.91),0.]),
                    quality=1. if i in (0,5,10,15,20) else 0.)
            for i,t in enumerate(np.arange(.1,6.,.2))]
    output = refine(rows,6.,baseline=None,matcher=Views())
    if secondary:
        output = refine_unresolved_with_names(output,{o.frame_index:'A' for o in rows},Views())
    assert [(s.start,s.end,d.reference_id) for s,d in zip(output['segments'],output['decisions'])] == [(0.,6.,'A')]
    assert sum(len(e) for e in output['evidence']) == len(rows)
    assert sum(len(s.bboxes) for s in output['segments']) == len(rows)


def test_same_names_do_not_hide_repeated_incompatible_faces_when_joined():
    class MisleadingPhotos(Matcher):
        def match(self, row, *_args):
            if not _args[-1].endswith('-piece'):
                return SimpleNamespace(reference_id=None, candidates=[])
            return SimpleNamespace(reference_id='A', candidates=[SimpleNamespace(reference_id='A', distance=.2)])
    rows = [replace(observation(float(t),'A'),embedding=np.eye(3)[0 if t < 3 else 1])
            for t in np.arange(.1,3.6,.2)]
    output = refine(rows,3.6,matcher=MisleadingPhotos())
    assert len(output['segments']) == 2
    assert all(d.reference_id == 'A' for d in output['decisions'])
    assert sum(s.end-s.start for s in output['segments']) == pytest.approx(3.6)


@pytest.mark.parametrize('middle,end_index', [('?', 21), ('B', 19)])
@pytest.mark.parametrize('dense_everywhere', [True, False])
def test_dense_transition_evidence_preserves_short_middle_and_returning_member(middle, end_index, dense_everywhere):
    # 60fps, skip4: transition observations are closer than the required
    # 0.15 seconds of identity support. More samples must not erase a part.
    rows = [replace(observation(i/15., middle if 15 <= i < end_index else 'A'),
                    frame_index=i*4) for i in range(45)]
    if not dense_everywhere:
        # Regular 0.2s samples, 12 legacy candidates and dense transition
        # neighborhoods reproduce the real collector's mixed cadence.
        sampled = {int(i*45/12) for i in range(12)} | set(range(0, 45, 3))
        sampled.update(i for i in range(45)
                       if min(abs(i-edge) for edge in (14, 15, end_index-1, end_index)) <= 3)
        rows = [row for i, row in enumerate(rows) if i in sampled]
    result = refine(rows, 3.)
    assert [d.reference_id for d in result['decisions']] == ['A', None if middle == '?' else 'B', 'A']
    assert [(s.start, s.end) for s in result['segments']] == pytest.approx(
        [(0., 14.5/15), (14.5/15, (end_index-.5)/15), ((end_index-.5)/15, 3.)])


def test_dense_repeated_unknown_faces_still_have_a_change_boundary():
    class UnknownMatcher:
        def match(self, *_args):
            return SimpleNamespace(reference_id=None, status='unmatched', candidates=[])
    rows = [replace(observation(i/15., 'A' if i < 15 else 'B'), frame_index=i*4)
            for i in range(30)]
    result = refine(rows, 2., baseline=None, matcher=UnknownMatcher())
    assert [d.reference_id for d in result['decisions']] == [None, None]
    assert result['segments'][0].end == pytest.approx(14.5/15)


def test_isolated_face_outliers_cannot_veto_an_entire_confirmed_main_run():
    rows = [observation(i/5., '?' if i in (5, 9) else 'A') for i in range(25)]
    # The two similar outliers are 0.8s apart with repeatedly confirmed A
    # between them. They do not form a continuous other-person part.
    result = refine(rows, 5.)
    assert [d.reference_id for d in result['decisions']] == ['A']
    assert [(s.start,s.end) for s in result['segments']] == [(0.,5.)]


@pytest.mark.parametrize('second_name,gap,expected', [('A', 0., 1), ('B', 0., 2), ('A', 1., 2)])
def test_adjacent_parent_tracks_join_only_for_continuous_same_member(second_name, gap, expected):
    from dance_highlight.services.member_timeline import refine_member_timeline
    segments, results = [], []
    for i, (start, end, name) in enumerate(((0., 3., 'A'), (3.+gap, 6.+gap, second_name))):
        rows = [replace(observation(float(t), name), track_id=i) for t in np.arange(start+.1, end, .2)]
        segments.append(Segment('main', i, start, end, [(o.time_seconds, np.array(o.body_bbox), i) for o in rows]))
        results.append(SimpleNamespace(owned_observations=rows, owned_previews={o.frame_index: str(o.time_seconds).encode() for o in rows}))
    output = refine_member_timeline(segments, [SegmentReferenceDecision(None,'unmatched','baseline')]*2,
                                   [0,1], [[],[]], results, Matcher())
    assert len(output['segments']) == expected
    assert sum(s.end-s.start for s in output['segments']) == pytest.approx(6.)
    assert sum(len(rows) for rows in output['evidence']) == 30
    if expected == 1:
        assert (output['segments'][0].start, output['segments'][0].end) == (0., 6.)
        assert output['decisions'][0].reference_id == 'A'
        assert len(output['previews']) == len(output['preview_sources']) == len(output['labels']) == 1
        assert output['accurate_indices'] == [0]


def test_short_b_part_between_a_parts_is_preserved_without_majority_vote():
    rows = [observation(float(t), 'B' if 1 <= t < 1.8 else 'A') for t in np.arange(.1, 3, .2)]
    result = refine(rows, 3.)
    assert [d.reference_id for d in result['decisions']] == ['A', 'B', 'A']
    assert result['segments'][1].end - result['segments'][1].start == pytest.approx(.8)


def test_failed_mixed_scope_keeps_a_repeated_named_run_in_its_own_interval():
    rows = [observation(.1, '?'), replace(observation(.3, '?'), embedding=np.array([0.,0.,-1.])),
            observation(.5, '?')]
    rows += [observation(float(t), 'A') for t in np.arange(.7, 2., .2)]
    result = refine(rows, 2., baseline=None)
    assert [d.reference_id for d in result['decisions']] == [None, 'A']
    assert result['segments'][1].start == pytest.approx(.6)
    assert result['segments'][1].end == 2.


def test_failed_piece_preserves_confirmed_run_when_next_member_is_nearby():
    from dance_highlight.services.member_timeline import _named_evidence_boundaries
    # A camera cut places the next member at 3.1s. A's named evidence ends
    # at 2.6s; rejecting the unconfirmed tail must not also discard A's part.
    segment = Segment('main', 7, 0., 3.1, [])
    ranges = [dict(start=0., end=2.7, name='A', first_time=.1, last_time=2.6),
              dict(start=3., end=3.7, name='B', first_time=3.1, last_time=3.6)]
    cuts = _named_evidence_boundaries(segment, ranges)
    assert any(cut['time'] == pytest.approx(2.7) for cut in cuts)


@pytest.mark.parametrize('middle', ['B', '?'])
def test_short_other_face_across_parent_boundary_is_not_swallowed_by_same_member(middle):
    from dance_highlight.services.member_timeline import refine_member_timeline
    rows = [observation(float(t), middle if 2.8 < t < 3.2 else 'A') for t in np.arange(.1,6.,.2)]
    segments = [Segment('main',i,start,end,[]) for i,(start,end) in enumerate(((0.,3.),(3.,6.)))]
    results = [SimpleNamespace(owned_observations=[o for o in rows if s.start <= o.time_seconds < s.end]) for s in segments]
    output = refine_member_timeline(segments,[SegmentReferenceDecision(None,'unmatched','baseline')]*2,
                                   [0,1],[[],[]],results,Matcher())
    assert [d.reference_id for d in output['decisions']] == ['A', 'B' if middle=='B' else None, 'A']
    assert [(round(s.start,6),round(s.end,6)) for s in output['segments']] == [(0.,2.8),(2.8,3.2),(3.2,6.)]


def test_unknown_second_face_never_inherits_named_parent():
    rows = [observation(float(t), 'A' if t < 2 else '?') for t in np.arange(.1, 4, .2)]
    result = refine(rows, 4.)
    assert any(d.reference_id is None for d in result['decisions'])
    assert all(s.end <= 2.01 for s, d in zip(result['segments'], result['decisions']) if d.reference_id == 'A')


def test_missing_main_face_evidence_never_inherits_a_name_from_the_expanded_body_crop():
    result = refine([], 2., baseline='A')
    assert [d.reference_id for d in result['decisions']] == [None]
    assert result['decisions'][0].reason == 'main_face_unconfirmed'
    assert result['labels'] == [None]


def test_one_wrong_named_frame_cannot_create_a_member_clip():
    rows = [observation(float(t), 'B' if .99 < t < 1.2 else 'A') for t in np.arange(.1, 3, .2)]
    result = refine(rows, 3.)
    assert all(d.reference_id != 'B' for d in result['decisions'])


def test_unidentified_scope_can_recover_without_needing_a_switch():
    result = refine([observation(float(t), 'B') for t in np.arange(.1, 2, .2)], 2., baseline=None)
    assert [d.reference_id for d in result['decisions']] == ['B']


def test_invalid_pose_and_duplicate_frames_cannot_supply_two_supports():
    a = observation(.1, 'A')
    rows = [a, a, replace(observation(.3, 'A'), association='ambiguous')]
    result = refine(rows, 1., baseline=None)
    assert all(d.reference_id is None for d in result['decisions'])


def test_confirmed_video_anchors_are_direct_only_and_need_independent_frames():
    from dance_highlight.services.member_timeline import build_video_anchors, match_video_anchors
    rows = [observation(t, 'A') for t in (.1, .3, .5)]
    direct = [Matcher().match(o) for o in rows]
    anchors = build_video_anchors(rows, direct)
    query = replace(observation(2., 'A'), embedding=np.array([.8, 0., .6]))
    assert match_video_anchors(query, anchors) == 'A'
    assert match_video_anchors(query, build_video_anchors([rows[0], rows[0]], direct[:2])) is None
    ambiguous = SimpleNamespace(reference_id=None, candidates=[], status='unmatched', reason='distance_exceeded')
    assert not build_video_anchors(rows, [ambiguous] * 3)


def test_coherent_short_scope_uses_its_own_average_without_cross_clip_duplicate_penalty():
    class NoisyMatcher(Matcher):
        def match(self, row, *_args):
            # Individual pose variation is weak, but their coherent mean is clear.
            if abs(row.embedding[1]) > .1:
                return SimpleNamespace(reference_id=None, status='unmatched', reason='distance_exceeded', candidates=[])
            return super().match(row)
    rows = [replace(observation(float(t), 'A'), embedding=np.array([.98, .199 if i % 2 else -.199, 0.]))
            for i, t in enumerate(np.arange(.1, 2, .2))]
    for o in rows: o.embedding[:] /= np.linalg.norm(o.embedding)
    result = refine(rows, 2., baseline=None, matcher=NoisyMatcher())
    assert [d.reference_id for d in result['decisions']] == ['A']


def test_long_unregistered_second_identity_is_split_even_without_reference_names():
    rows = [replace(observation(float(t), '?'), embedding=np.array([0., 0., 1.] if t < 2 else [0., 0., -1.]))
            for t in np.arange(.1, 4, .2)]
    result = refine(rows, 4., baseline=None)
    assert len(result['segments']) >= 2
    assert any(abs(s.end-2) < .11 for s in result['segments'])


def test_visible_supporting_member_is_sampled_and_main_body_is_not_duplicated():
    from dance_highlight.services.member_coverage import visible_member_segments
    from dance_highlight.services.segment import FrameRec
    main = np.array([0., 0., 100., 200.]); other = np.array([200., 0., 300., 200.])
    heads = np.array([[220., 20., .9], [240., 20., .9], [230., 30., .9]])
    records = [FrameRec(t, 1, main, False, person_bboxes=[main, other],
                        person_head_keypoints=[heads- [200., 0., 0.], heads]) for t in (0., .2, .4, .6)]
    result = visible_member_segments(records)
    assert len(result) == 1
    assert all(np.array_equal(row[1], other) for row in result[0].bboxes)
    assert result[0].end > .6


def test_multiple_visible_bodies_cannot_share_a_track_on_the_same_frame():
    from dance_highlight.services.member_coverage import visible_member_segments
    from dance_highlight.services.segment import FrameRec
    a = np.array([0., 0., 100., 200.]); b = np.array([45., 0., 145., 200.])
    h = np.array([[10., 20., .9], [30., 20., .9]])
    records = [FrameRec(t, None, None, True, person_bboxes=[a, b],
                        person_head_keypoints=[h, h+[45., 0., 0.]]) for t in (0., .2, .4, .6)]
    result = visible_member_segments(records)
    assert len(result) == 2
    assert all(len({row[0] for row in s.bboxes}) == len(s.bboxes) for s in result)


def test_continuous_unknown_face_is_not_split_for_clip_count():
    rows = [observation(float(t), '?') for t in np.arange(.1, 10., .2)]
    result = refine(rows, 10., baseline=None)
    assert len(result['segments']) == 1
    assert len(set(result['labels'])) == 1


def test_unresolved_roster_faces_remain_in_one_review_bucket_without_invented_people():
    rows = [replace(observation(float(t), '?'), embedding=np.array([0., 0., 1.] if t < 2 else [0., 0., -1.]))
            for t in np.arange(.1, 4., .2)]
    result = refine(rows, 4., baseline=None)
    assert set(result['labels']) == {None}
    assert all(d.reference_id is None for d in result['decisions'])
    assert sum(s.end-s.start for s in result['segments']) == pytest.approx(4.)
    assert sum(len(e) for e in result['evidence']) == len(rows)


def test_sparse_early_face_does_not_name_unobserved_rest_of_clip():
    result = refine([observation(.1, 'A'), observation(.3, 'A')], 3., baseline=None)
    named = [(s.start, s.end) for s, d in zip(result['segments'], result['decisions']) if d.reference_id]
    assert named == [(0., .4)]


def test_short_confirmed_face_run_stays_separate_from_unobserved_time():
    result = refine([observation(2.9, 'A'), observation(3.1, 'A')], 6., baseline=None)
    named = [s for s, d in zip(result['segments'], result['decisions']) if d.reference_id=='A']
    assert len(named) == 1
    assert named[0].start == pytest.approx(2.8)
    assert named[0].end == pytest.approx(3.2)


def test_unobserved_gap_uses_unknown_bucket_instead_of_inventing_a_person():
    result = refine([observation(.1, 'A'), observation(.3, 'A')], 3., baseline=None)
    assert [label for label, d in zip(result['labels'], result['decisions']) if not d.reference_id] == [None]


def test_subtracted_visible_clip_uses_faces_from_its_remaining_interval():
    from dance_highlight.services.member_coverage import append_visible_member_clips
    main = refine([observation(float(t), 'A') for t in np.arange(.1, 2., .2)], 2.)
    extra = refine([observation(float(t), 'A') for t in np.arange(.1, 3., .2)], 3.)
    images = {round(t*30): str(round(t,1)).encode() for t in np.arange(.1, 3., .2)}
    extra['preview_sources'] = [({}, images)] * len(extra['segments'])
    result = append_visible_member_clips(main, extra, Matcher())
    index = next(i for i,s in enumerate(result['segments']) if s.start==2.)
    assert result['previews'][index]
    assert all(float(image) >= 2. for image in result['previews'][index])


@pytest.mark.parametrize('score', [.85, .98])
def test_short_unregistered_second_face_is_split_at_the_same_confidence_used_for_naming(score):
    rows = [replace(observation(float(t), '?' if .8 < t < 1.2 else 'A'), detector_score=score)
            for t in np.arange(.1, 3., .2)]
    result = refine(rows, 3.)
    assert [d.reference_id for d in result['decisions']] == ['A', None, 'A']
    assert result['segments'][1].start == pytest.approx(.8)
    assert result['segments'][1].end == pytest.approx(1.2)


def test_visual_refinement_cannot_cross_unobserved_gap_or_reorder_ranges(monkeypatch):
    from dance_highlight.services import member_timeline as module
    seen = []
    def late_refinement(_video, boundaries):
        seen.extend(boundaries)
        return [dict(b, time=11/30, visual_difference=30.) for b in boundaries]
    monkeypatch.setattr(module, 'refine_switch_boundaries', late_refinement)
    rows = [observation(.1,'A'),observation(.3,'A'),observation(3.7,'B'),observation(3.9,'B')]
    seg = Segment('main',7,0.,4.,[])
    result = module.refine_member_timeline([seg],[SegmentReferenceDecision(None,'unmatched','baseline')],
             [7],[[]],[SimpleNamespace(owned_observations=rows)],Matcher(),video_path='source.mp4')
    assert not seen  # no precise transition can be inferred across a 3.4s blind gap
    assert all(s.end > s.start for s in result['segments'])
    assert sum(s.end-s.start for s in result['segments']) == pytest.approx(4.)
    assert all(a.end == pytest.approx(b.start) for a,b in zip(result['segments'],result['segments'][1:]))


def test_dense_unmatched_faces_do_not_hide_short_named_appearance():
    from dance_highlight.services.face_recovery import ReferenceObservationMatcher
    from dance_highlight.services.reference_matcher import ReferenceEmbeddingSample
    reference = ReferenceEmbeddingSample('A','A/0','a'*64,100,100,np.array([.41,-np.sqrt(1-.41**2),0.]))
    matcher = ReferenceObservationMatcher(references=[reference],analysis_id='test',video_sha256='b'*64,
              detector_sha256='c'*64,recognizer_sha256='d'*64,config_sha256='e'*64,
              backend_version='test',video_size=(100,100),max_distance=.6)
    rows = [replace(observation(float(t),'A'), embedding=np.array([1.,0.,0.] if 2.8<t<3.2 else [.5,np.sqrt(.75),0.]))
            for t in np.arange(.1,6.,.2)]
    result = refine(rows,6.,baseline=None,matcher=matcher)
    named = [s for s,d in zip(result['segments'],result['decisions']) if d.reference_id=='A']
    assert len(named)==1
    assert named[0].start==pytest.approx(2.8)
    assert named[0].end==pytest.approx(3.2)


def test_direct_visible_member_anchors_recover_main_face_without_recursive_names():
    from dance_highlight.services.member_timeline import video_reference_anchors, refine_member_timeline
    class AngleMatcher(Matcher):
        def match(self, row, *_):
            name = 'A' if row.embedding[0] > .5 else None
            return SimpleNamespace(reference_id=name, status='matched' if name else 'unmatched',
                                   reason='accepted' if name else 'distance_exceeded',
                                   candidates=[SimpleNamespace(reference_id='A',distance=.4)] if name else [])
    seed_rows = [replace(observation(t,'A'),embedding=np.array([.6,.8,0.])) for t in (.1,.3,.5)]
    seg=Segment('main',1,0.,1.,[]);matcher=AngleMatcher()
    anchors=video_reference_anchors([seg],[SimpleNamespace(owned_observations=seed_rows)],matcher)
    query_rows=[replace(observation(t,'A'),embedding=np.array([.2,np.sqrt(.96),0.])) for t in (.1,.3,.5,.7,.9)]
    result=refine_member_timeline([seg],[SegmentReferenceDecision(None,'unmatched','baseline')],[1],[[]],
              [SimpleNamespace(owned_observations=query_rows)],matcher,seed_anchors=anchors)
    assert [d.reference_id for d in result['decisions']]==['A']
    assert not video_reference_anchors([seg],[SimpleNamespace(owned_observations=query_rows)],matcher)


def test_two_brief_named_appearances_do_not_name_unresolved_time_between_them():
    from dance_highlight.services.face_recovery import ReferenceObservationMatcher
    from dance_highlight.services.reference_matcher import ReferenceEmbeddingSample
    reference = ReferenceEmbeddingSample('A','A/0','a'*64,100,100,np.array([.41,-np.sqrt(1-.41**2),0.]))
    matcher = ReferenceObservationMatcher(references=[reference],analysis_id='test',video_sha256='b'*64,
              detector_sha256='c'*64,recognizer_sha256='d'*64,config_sha256='e'*64,
              backend_version='test',video_size=(100,100),max_distance=.6)
    rows = [replace(observation(float(t),'A'), embedding=np.array(
                [1.,0.,0.] if 2.8<t<3.4 or 6.<t<6.4 else [.5,np.sqrt(.75),0.]))
            for t in np.arange(.1,9.,.2)]
    result = refine(rows,9.,baseline=None,matcher=matcher)
    named = [s for s,d in zip(result['segments'],result['decisions']) if d.reference_id=='A']
    assert np.array([(s.start,s.end) for s in named]) == pytest.approx(np.array([(2.8,3.4),(6.,6.4)]))
    assert sum(s.end-s.start for s in result['segments']) == pytest.approx(9.)


def test_named_evidence_boundaries_preserve_required_span_with_dense_legacy_samples():
    from dance_highlight.services.face_recovery import ReferenceObservationMatcher
    from dance_highlight.services.reference_matcher import ReferenceEmbeddingSample
    reference = ReferenceEmbeddingSample('A','A/0','a'*64,100,100,np.array([.41,-np.sqrt(1-.41**2),0.]))
    matcher = ReferenceObservationMatcher(references=[reference],analysis_id='test',video_sha256='b'*64,
              detector_sha256='c'*64,recognizer_sha256='d'*64,config_sha256='e'*64,
              backend_version='test',video_size=(100,100),max_distance=.6)
    named_times = [2.9,2.9667,3.1,3.1667]
    times = sorted({*np.arange(.1,6.,.2),*named_times})
    rows = [replace(observation(float(t),'A'), embedding=np.array(
                [1.,0.,0.] if any(abs(t-n)<1e-6 for n in named_times) else [.5,np.sqrt(.75),0.])) for t in times]
    result = refine(rows,6.,baseline=None,matcher=matcher)
    named = [s for s,d in zip(result['segments'],result['decisions']) if d.reference_id=='A']
    assert len(named)==1
    assert named[0].start==pytest.approx(2.8)
    assert named[0].end==pytest.approx(3.2667)


def test_unrelated_embedding_outliers_do_not_veto_repeated_member_evidence():
    from dance_highlight.services.member_timeline import _assign_piece
    rows = [observation(float(t),'A') for t in np.arange(.1,3.,.2)]
    rows[4] = replace(rows[4], embedding=np.array([0.,0.,1.]))
    rows[9] = replace(rows[9], embedding=np.array([0.,0.,-1.]))
    evidence = [(o,'A' if o.embedding[0] else None) for o in rows]
    decision = _assign_piece(Segment('main',1,0.,3.,[]),evidence,Matcher(),[],'test')
    assert decision.reference_id=='A'


@pytest.mark.parametrize('pose_distance', [0., .55])
def test_repeated_coherent_alien_face_still_vetoes_a_mixed_piece(pose_distance):
    from dance_highlight.services.member_timeline import _assign_piece
    rows = [observation(float(t),'A') for t in np.arange(.1,3.,.2)]
    rows[4] = replace(rows[4], embedding=np.array([0.,0.,1.]))
    # Two consecutive observations 0.2s apart represent an actual other-face
    # part. Distant isolated outliers with A between them are tested separately.
    rows[5] = replace(rows[5], embedding=np.array([0.,np.sqrt(1-(1-pose_distance)**2),1-pose_distance]))
    evidence = [(o,'A' if o.embedding[0] else None) for o in rows]
    decision = _assign_piece(Segment('main',1,0.,3.,[]),evidence,Matcher(),[],'test')
    assert decision.reference_id is None
    assert decision.reason=='inconsistent_face_scope'


@pytest.mark.parametrize('hard_cut', [True, False])
def test_low_contrast_identity_cut_uses_visual_spike_but_gradual_change_keeps_estimate(tmp_path, hard_cut):
    import cv2
    from dance_highlight.services.member_timeline import refine_member_timeline
    path=tmp_path/'subtle-cut.avi'
    writer=cv2.VideoWriter(str(path),cv2.VideoWriter_fourcc(*'MJPG'),30.,(160,90))
    assert writer.isOpened()
    for frame in range(48):
        value=(65 if frame<24 else 77) if hard_cut else 40+frame
        writer.write(np.full((90,160,3),value,np.uint8))
    writer.release()
    rows=[observation(t,'A') for t in (.1,.3,.5,.7)]+[observation(t,'B') for t in (1.1,1.3,1.5)]
    seg=Segment('main',1,0.,1.6,[])
    result=refine_member_timeline([seg],[SegmentReferenceDecision('A','matched','baseline')],[1],[[]],
          [SimpleNamespace(owned_observations=rows)],Matcher(),video_path=str(path))
    assert [d.reference_id for d in result['decisions']]==['A','B']
    assert result['segments'][0].end==pytest.approx(.8 if hard_cut else .9)
    if hard_cut:
        assert result['audit'][0]['boundaries'][0]['boundary_frame_index']==24


def test_camera_cut_support_cannot_create_a_preceding_face_change():
    """MMN: new-shot Yunjin faces must not split the preceding shot at 50.684."""
    import json
    from pathlib import Path
    from dance_highlight.services.member_timeline import _identity_boundaries, _named_ranges
    data = json.loads((Path(__file__).parent / 'fixtures/dance_scene_review/mmn50_cut_support.json').read_text())
    rows = [FaceObservation(**dict(o, embedding=np.array(o['embedding']) if o['embedding'] is not None else None))
            for o in data['observations']]
    segment = Segment('main', 0, 49.9, 51.3, [])
    names = [data['secondary_names'].get(str(o.frame_index)) for o in rows]
    ranges = _named_ranges(segment, rows, names)
    result = _identity_boundaries(segment, rows, names, ranges,
                                  cut_times=[3047/data['fps']])
    assert not any(50.6 < b['time'] < 50.8 for b in result)


def test_source_camera_cut_keeps_the_same_named_performer_continuous():
    rows = [observation(round(float(t), 6), 'A') for t in np.arange(.1, 2., .1)]
    result = refine(rows, 2., cut_times=(1.,))
    assert [(s.start, s.end, d.reference_id) for s,d in zip(result['segments'], result['decisions'])] == [(0.,2.,'A')]


def test_source_camera_cut_owns_a_real_member_change_instead_of_a_midpoint():
    rows = [observation(round(float(t), 6), 'A' if t<1 else 'B') for t in np.arange(.1, 2., .1)]
    result = refine(rows, 2., cut_times=(1.,))
    assert [(s.start, s.end, d.reference_id) for s,d in zip(result['segments'], result['decisions'])] == [(0.,1.,'A'),(1.,2.,'B')]


def test_direct_same_name_across_a_view_change_never_creates_a_short_unknown():
    class ViewMatcher:
        def match(self, row, *_):
            distance=1.-float(row.embedding @ np.array([2**-.5,2**-.5,0.]))
            name='A' if distance<=.6 else None
            return SimpleNamespace(reference_id=name, candidates=[SimpleNamespace(reference_id='A',distance=distance)])
    rows=[observation(.1,'A'), observation(.3,'A'), observation(.55,'B')]
    result=refine(rows,.7,matcher=ViewMatcher(),cut_times=(.5,))
    assert [(s.start,s.end,d.reference_id) for s,d in zip(result['segments'],result['decisions'])] == [(0.,.7,'A')]


def test_named_padding_stops_at_a_source_cut_even_near_the_scope_edge():
    from dance_highlight.services.member_timeline import _named_ranges
    rows = [observation(t,'B') for t in (.85,1.05,1.25)]
    segment=Segment('main',0,.75,1.35,[])
    ranges=_named_ranges(segment,rows,['B']*3,cut_times=(.834,))
    assert ranges[0]['start'] == pytest.approx(.834)
