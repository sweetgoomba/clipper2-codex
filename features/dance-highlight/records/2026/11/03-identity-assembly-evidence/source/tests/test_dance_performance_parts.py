"""Final performance parts keep face evidence separate from output ownership."""
from dataclasses import replace

from dance_highlight.services.segment import Segment
from test_dance_output_continuity import Matcher, output_parts


def assemble(original, *, eligible=None, handoffs=(), matcher=None):
    from dance_highlight.services.performance_parts import build_performance_parts
    return build_performance_parts(original,
        eligibility=eligible or [Segment('main', None, 0., 30., [])],
        matcher=matcher or Matcher(), frame_records=[], frozen_observations=[],
        joint_matches={}, handoffs=handoffs, fps=100., video_path=None,
        scene_changes=[], cut_frames=[], group_segments=[], mask_refinement={})


def test_same_member_six_seconds_is_one_part_with_read_only_identity_spans():
    original = output_parts([(0., 2., 'A', 'A'), (2., 6., 'A', 'A')])
    before = [list(e) for e in original['evidence']]
    result, audit = assemble(original)
    assert [(s.start, s.end) for s in result['segments']] == [(0., 6.)]
    assert len(original['segments']) == 2
    assert all(a == b for a, b in zip(before, original['evidence']))
    assert result['anchors'] is original['anchors']
    assert [s['range'] for s in audit['identity_spans']] == [[0., 2.], [2., 6.]]
    assert audit['parts'][0]['source_spans'] == [0, 1]
    assert audit['parts'][0]['newly_named_seconds'] == 0.


def test_projection_never_borrows_evidence_images_or_extends_through_excluded_time():
    original = output_parts([(0., 3., 'A', 'A')])
    result, audit = assemble(original, eligible=[Segment('main', None, .1, .5, []),
                                                Segment('main', None, 2.5, 2.9, [])])
    assert [(s.start, s.end) for s in result['segments']] == [(.1, .5), (2.5, 2.9)]
    assert [p['source_spans'] for p in audit['parts']] == [[0], [0]]
    for part, rows, previews in zip(result['segments'], result['evidence'], result['previews']):
        assert all(part.start <= r.time_seconds < part.end for r, _ in rows)
        assert set(previews) <= {str(r.frame_index).encode() for r, _ in rows}
    assert len(original['evidence'][0]) == 4


def test_unknown_face_gaps_are_not_named_from_only_matching_endpoints():
    original = output_parts([(0., 1., 'A', 'A'), (1., 4., None, 'A'), (4., 6., 'A', 'A')])
    original['evidence'][1] = []
    result, audit = assemble(original)
    assert [(s.start, s.end, d.reference_id) for s, d in zip(result['segments'], result['decisions'])] == [
        (0., 1., 'A'), (1., 4., None), (4., 6., 'A')]
    assert sum(p['newly_named_seconds'] for p in audit['parts']) == 0.


def test_real_short_b_between_a_parts_is_not_removed():
    original = output_parts([(0., 2., 'A', 'A'), (2., 2.3, 'B', 'B'), (2.3, 6., 'A', 'A')])
    result, _ = assemble(original)
    assert [d.reference_id for d in result['decisions']] == ['A', 'B', 'A']
    assert [(s.start, s.end) for s in result['segments']] == [(0., 2.), (2., 2.3), (2.3, 6.)]


def test_unobserved_prefix_and_suffix_remain_unknown_with_two_middle_faces():
    original = output_parts([(0., 2.8, None, 'A'), (2.8, 3.2, 'A', 'A'), (3.2, 6., None, 'A')])
    original['evidence'][0] = original['evidence'][2] = []
    result, _ = assemble(original)
    assert [(s.start, s.end, d.reference_id) for s, d in zip(result['segments'], result['decisions'])] == [
        (0., 2.8, None), (2.8, 3.2, 'A'), (3.2, 6., None)]


def test_unknown_handoff_boundary_and_array_alignment_survive_projection():
    original = output_parts([(0., 6., None, 'A')])
    original['evidence'][0] = []
    result, audit = assemble(original, handoffs=[dict(previous_time=2.98, time=3.)])
    assert [(s.start, s.end) for s in result['segments']] == [(0., 3.), (3., 6.)]
    assert audit['projection']['unidentified_handoffs']['changes']
    assert all(len(result[k]) == 2 for k in ('decisions', 'labels', 'evidence', 'previews', 'preview_sources'))
    assert result['accurate_indices'] == [0, 1]


def test_output_assembly_resolves_one_observed_event_without_rewriting_identity():
    from test_dance_part_boundary_events import example
    from dance_highlight.services.performance_parts import build_performance_parts
    original, identity, args = example()
    original['audit'] = identity['audit']
    result, audit = build_performance_parts(original, **args,
        video_path=None, scene_changes=[], group_segments=[], mask_refinement={})
    assert [(s.start, s.end) for s in result['segments']] == [(0., 16/60)]
    assert result['decisions'][0].reference_id == 'A'
    assert audit['projection']['boundary_events']['joins']
    assert audit['parts'][0]['newly_named_seconds'] == 16/60-14/60
