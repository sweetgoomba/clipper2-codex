"""Identity propagation needs a complete visual path, not endpoint agreement."""
from dataclasses import replace

import pytest

from dance_highlight.services.mask_continuity import TraceFrame, evaluate_track


def trace():
    # Start on a confirmed face, then follow the same body through an unknown.
    return [TraceFrame(i, i / 10., 0, (0,), (0,), .9) for i in range(61)]


def test_same_member_six_seconds_has_no_tracking_duration_cap():
    result = evaluate_track(trace(), anchor_owner=0, target_frames=range(1, 61))
    assert result['accepted']
    assert result['support_frames'] == list(range(1, 61))


def test_returning_to_same_anchor_does_not_excuse_middle_identity_switch():
    frames = trace()
    frames[30] = replace(frames[30], cycle_iou=.13, reverse_owners=(1,))
    result = evaluate_track(frames, anchor_owner=0, target_frames=range(40, 61))
    assert not result['accepted']
    assert result['reason'] == 'inconsistent_visual_path'


def test_camera_change_without_independent_texture_correspondence_blocks_name():
    frames = trace()
    frames[20] = replace(frames[20], cut_from_previous=True, cut_supported=False)
    result = evaluate_track(frames, anchor_owner=0, target_frames=range(40, 61))
    assert not result['accepted']
    assert result['reason'] == 'unconfirmed_camera_transition'


def test_verified_zoom_or_lighting_change_keeps_the_same_body():
    frames = trace()
    frames[20] = replace(frames[20], cut_from_previous=True, cut_supported=True)
    assert evaluate_track(frames, anchor_owner=0, target_frames=range(40, 61))['accepted']


@pytest.mark.parametrize('owners', [(1,), (0, 1), ()])
def test_tracking_a_supporting_or_ambiguous_body_does_not_name_main(owners):
    frames = trace()
    frames[45] = replace(frames[45], forward_owners=owners)
    assert not evaluate_track(frames, anchor_owner=0, target_frames=range(40, 61))['accepted']


def test_group_frame_cannot_receive_a_solo_name():
    frames = trace()
    frames[45] = replace(frames[45], main_owner=None)
    assert not evaluate_track(frames, anchor_owner=0, target_frames=range(40, 61))['accepted']


def test_reverse_mask_can_miss_head_pixels_but_cannot_own_a_different_body():
    frames = trace()
    frames[45] = replace(frames[45], reverse_owners=(), cycle_iou=.7)
    assert evaluate_track(frames, anchor_owner=0, target_frames=range(40, 61))['accepted']
    frames[45] = replace(frames[45], reverse_owners=(1,))
    assert not evaluate_track(frames, anchor_owner=0, target_frames=range(40, 61))['accepted']


def test_missing_target_sample_is_not_silently_skipped():
    frames = [f for f in trace() if f.frame_index != 45]
    assert not evaluate_track(frames, anchor_owner=0, target_frames=range(40, 61))['accepted']


def test_two_nearby_samples_cannot_confirm_a_part():
    assert not evaluate_track(trace(), anchor_owner=0, target_frames=(40, 41))['accepted']


def test_tracking_can_start_from_the_following_confirmed_part():
    assert evaluate_track(list(reversed(trace())), anchor_owner=0, target_frames=range(40))['accepted']


@pytest.mark.parametrize('overlap', [float('nan'), float('inf'), -1., 1.1])
def test_invalid_mask_overlap_is_not_evidence(overlap):
    frames = trace()
    frames[30] = replace(frames[30], cycle_iou=overlap)
    assert not evaluate_track(frames, anchor_owner=0, target_frames=range(40, 61))['accepted']


def recovery_example():
    import numpy as np
    from dance_highlight.services.face_evidence import FaceObservation
    from dance_highlight.services.reference_matcher import SegmentReferenceDecision
    from dance_highlight.services.segment import FrameRec, Segment
    box = (10., 10., 40., 90.)
    records = [FrameRec(i/10., 1, np.array(box), False, person_bboxes=[np.array(box)]) for i in range(60)]
    rows = [FaceObservation(i,i/10.,1,box,box,face_bbox=(18.,12.,30.,25.),
                            embedding=np.array([1.,0.]), detector_score=.99,
                            association='confirmed') for i in range(60)]
    spans = [(0.,2.,'A'),(2.,4.,None),(4.,6.,'A')]
    output = dict(segments=[Segment('main',i,a,b,[]) for i,(a,b,n) in enumerate(spans)],
                  decisions=[SegmentReferenceDecision(n,'matched' if n else 'unmatched','face') for a,b,n in spans],
                  labels=[1,None,2], previews=[[],[],[]], preview_sources=[({},{}),({},{}),({},{})],
                  evidence=[[(r,n) for r in rows if a<=r.time_seconds<b] for a,b,n in spans],
                  accurate_indices=[0,2], audit=[], anchors=[], fallback_names={})
    anchors = [dict(name='A',frame_index=i,time_seconds=i/10.) for i in (15,18,42,45)]
    return output, records, anchors


def test_recovery_preserves_faces_and_merges_same_member_without_duration_cap():
    from dance_highlight.services.mask_continuity import recover_mask_names
    original, records, anchors = recovery_example()
    calls = []
    def verify(anchor, path, targets):
        calls.append(anchor.frame_index)
        return dict(accepted=True,reason='confirmed_visual_path',support_frames=targets)
    result, audit = recover_mask_names(original,records,'unused',10.,anchors,verify_track=verify)
    assert [(s.start,s.end) for s in result['segments']] == [(0.,6.)]
    assert result['decisions'][0].reference_id == 'A'
    assert result['decisions'][0].reason == 'member_mask_continuity'
    assert audit['recovered_seconds'] == pytest.approx(2.)
    assert calls == [18,42]
    assert len(original['segments']) == 3
    assert result['anchors'] == [] and result['fallback_names'] == {}
    assert all(name is None for row,name in result['evidence'][0] if 2<=row.time_seconds<4)


@pytest.mark.parametrize('mixed', [False, True])
def test_group_only_unknowns_skip_tracking_but_mixed_main_remains_eligible(mixed):
    from dance_highlight.services.mask_continuity import recover_mask_names
    original, records, anchors = recovery_example()
    records = [replace(r, scene_kind='group', main_bbox=None)
               if 2 <= r.t < (3 if mixed else 4) else r for r in records]
    calls = []
    def verify(anchor, path, targets):
        calls.append(anchor.frame_index)
        return dict(accepted=False, reason='unconfirmed_main_ownership', frame=targets[0])
    result, audit = recover_mask_names(original, records, 'unused', 10., anchors,
                                       verify_track=verify, cut_frames=[])
    assert result is original
    assert audit['recovered_seconds'] == 0
    if mixed:
        assert calls
    else:
        assert calls == []
        assert audit['candidates'][0]['reason'] == 'no_main_targets'


def test_two_disagreeing_verified_directions_cannot_choose_a_name():
    from dance_highlight.services.mask_continuity import recover_mask_names
    from dance_highlight.services.reference_matcher import SegmentReferenceDecision
    original, records, anchors = recovery_example()
    original['decisions'][2] = SegmentReferenceDecision('B','matched','face')
    anchors = [a | {'name':'B' if a['frame_index']>=40 else 'A'} for a in anchors]
    result,audit = recover_mask_names(original,records,'unused',10.,anchors,
        verify_track=lambda *args:dict(accepted=True,reason='confirmed_visual_path'))
    assert result is original
    assert audit['candidates'][0]['reason'] == 'conflicting_tracking_names'


@pytest.mark.parametrize('case', ['single_anchor','gap','unconfirmed_face','failed_model'])
def test_unverified_seed_or_execution_cannot_name_unknown(case):
    from dance_highlight.services.mask_continuity import recover_mask_names
    original, records, anchors = recovery_example()
    if case == 'single_anchor': anchors = [anchors[0],anchors[2]]
    if case == 'gap':
        original['segments'][0] = replace(original['segments'][0],end=1.9)
        original['segments'][2] = replace(original['segments'][2],start=4.1)
    if case == 'unconfirmed_face':
        original['evidence'] = [[(replace(r,association='ambiguous'),n) for r,n in e] for e in original['evidence']]
    def verify(*args):
        if case == 'failed_model': raise RuntimeError('unavailable')
        raise AssertionError('must not call model without verified seed')
    result,audit = recover_mask_names(original,records,'unused',10.,anchors,verify_track=verify)
    assert result is original
    assert audit['recovered_seconds'] == 0.


def test_occluded_head_on_path_can_be_confirmed_by_reverse_with_mask_agreement():
    frames = trace()
    frames[30] = replace(frames[30],forward_owners=(),reverse_owners=(0,),cycle_iou=.91)
    assert evaluate_track(frames,anchor_owner=0,target_frames=range(40,61))['accepted']
    frames[30] = replace(frames[30],reverse_owners=(1,))
    assert not evaluate_track(frames,anchor_owner=0,target_frames=range(40,61))['accepted']


@pytest.mark.parametrize('cut_inventory_available',[False,True])
def test_product_pipeline_skips_mask_recovery_and_preserves_unknown(tmp_path,monkeypatch,cut_inventory_available):
    import json
    import numpy as np
    from dance_highlight.services import pipeline, member_timeline, secondary_faces, body_continuity, mask_tracker, context_faces
    from dance_highlight.services.config import DanceConfig
    from dance_highlight.services.dance_meta import DanceMetaBuilder
    from dance_highlight.services.face_cluster import SegmentFaceResult
    from dance_highlight.services.reference_matcher import ReferenceEmbeddingSample
    original,records,anchors = recovery_example()
    rows = [r for evidence in original['evidence'] for r,_ in evidence]
    monkeypatch.setattr(pipeline,'build_raw_main_segments',lambda _: original['segments'])
    monkeypatch.setattr(pipeline,'build_raw_group_segments',lambda _: [])
    monkeypatch.setattr(member_timeline,'refine_member_timeline',lambda *a,**k: original)
    monkeypatch.setattr(secondary_faces,'recover_secondary_names',lambda *a,**k: ({},{'video_anchors':anchors}))
    monkeypatch.setattr(body_continuity,'bridge_main_face_gaps',lambda output,*a: (output,{}))
    monkeypatch.setattr(context_faces,'collect_source_context',lambda *a,**k:([],dict(reason='complete' if cut_inventory_available else 'incomplete_source_decode')))
    class Tracker:
        provenance = {'name':'test-tracker'}
        created = 0
        def __init__(self,*args,**kwargs): Tracker.created += 1
        def __call__(self,anchor,path,targets): return dict(accepted=True,reason='confirmed_visual_path')
    monkeypatch.setattr(mask_tracker,'MaskTracker',Tracker)
    class Face:
        def batch_segment_embeddings(self,_video,segments,**kwargs):
            return [SegmentFaceResult(s,[],True,owned_observations=[r for r in rows if s.start<=r.time_seconds<s.end]) for s in segments]
        def cluster_embeddings(self,_): return []
    class Render:
        def extract_clip(self,*a,**k): raise AssertionError('source ranges only')
        def extract_thumbnail(self,_video,path,**kwargs): path.write_bytes(b'preview')
    config=DanceConfig();pipe=pipeline.DancePipeline(config,None,Face(),Render(),DanceMetaBuilder(config))
    pipe.analyze_video_to_records=lambda *a,**k: (records,10.,6.)
    pipe._download_reference_images=lambda *a: {}
    pipe._video_size=lambda _: (640,480)
    def references(_paths,sample_sink):
        sample_sink.extend(ReferenceEmbeddingSample(n,n,str(i)*64,100,100,np.eye(2)[i]) for i,n in enumerate(('A','B')))
        return {}
    pipe._build_reference_embeddings=references
    source=tmp_path/'input.mp4';source.write_bytes(b'source')
    meta=pipe.run(tmp_path,source,24)
    expected=[('a',0.,2.),('unknown',2.,4.),('a',4.,6.)]
    assert Tracker.created == 0
    assert [(c['person_id'],c['start'],c['end']) for c in meta['lists']['main']] == expected
    assert meta['stats']['mask_continuity_recovered_seconds'] == 0.
    audit=json.loads((tmp_path/'diagnostics/face_evidence.json').read_text())
    assert audit['mask_continuity_refinement']['reason'] == 'disabled_runtime_cost'
    assert 'model' not in audit['mask_continuity_refinement']
    assert meta['diagnostics']['performance']['stage_seconds']['mask_continuity'] == 0.
    assert {'mask_continuity','mask_tracker'} <= audit['runtime']['modules'].keys()


@pytest.mark.parametrize('endpoint', [364,432])
def test_actual_reviewed_hong_path_and_later_drifting_path(endpoint):
    import json
    from pathlib import Path
    data=json.loads((Path(__file__).parent/'fixtures/dance_scene_review/mask_continuity'/f'{endpoint}.json').read_text())
    frames=[TraceFrame(**(r|{'forward_owners':tuple(r['forward_owners']),
                             'reverse_owners':tuple(r['reverse_owners'])})) for r in data['frames']]
    result=evaluate_track(frames,anchor_owner=data['anchor_owner'],target_frames=data['target_frames'])
    assert result['accepted'] is data['expected_accepted']
    if endpoint==432:
        # Endpoint return is excellent, but the body in the middle is different.
        assert frames[0].cycle_iou > .9
        assert result['reason']=='inconsistent_visual_path'


def test_frozen_other_name_inside_unknown_vetoes_visual_only_recovery():
    from dance_highlight.services.mask_continuity import recover_mask_names
    original,records,anchors=recovery_example()
    anchors += [dict(name='B',frame_index=i,time_seconds=i/10.) for i in (25,28)]
    calls=[]
    def verify(*args):
        calls.append(args)
        return dict(accepted=True,reason='confirmed_visual_path')
    result,audit=recover_mask_names(original,records,'unused',10.,anchors,verify_track=verify)
    assert result is original
    assert not calls
    assert all(a['reason']=='conflicting_direct_face_anchor' for a in audit['candidates'][0]['attempts'])


def external_conflict_example(reverse=False):
    import numpy as np
    original, records, anchors = recovery_example()
    anchors = anchors[2:] if reverse else anchors[:2]
    frame = 41 if reverse else 19
    box = (100., 10., 130., 90.)
    records[frame] = replace(records[frame], main_bbox=np.array(box),
                            person_bboxes=[records[frame].main_bbox, np.array(box)])
    original['evidence'] = [[(replace(row, body_bbox=box, roi_bbox=box,
                                     face_bbox=(108., 12., 120., 25.))
                             if row.frame_index == frame else row, name)
                            for row, name in evidence] for evidence in original['evidence']]
    return original, records, anchors, {frame: dict(status='accepted', name='B')}


@pytest.mark.parametrize('reverse', [False, True])
@pytest.mark.parametrize('partial', [False, True])
def test_contrary_face_on_another_body_outside_target_needs_fresh_bidirectional_proof(reverse, partial):
    from dance_highlight.services.mask_continuity import recover_mask_names
    original, records, anchors, joint = external_conflict_example(reverse)
    calls = []
    def verify(anchor, path, targets):
        calls.append(list(targets))
        if partial and len(calls) == 1:
            return dict(accepted=False, reason='unconfirmed_main_ownership', frame=29 if reverse else 30)
        return dict(accepted=True, reason='confirmed_visual_path', support_frames=targets,
                    trace=[dict(frame=round(r.t * 10), forward=[0], reverse=[0]) for r in path])
    result, audit = recover_mask_names(original, records, 'unused', 10., anchors,
                                      verify_track=verify, joint_matches=joint)
    assert len(calls) == (2 if partial else 1)
    assert audit['recovered_seconds'] == pytest.approx((1.05 if reverse else .95) if partial else 2.)
    accepted = audit['candidates'][0]['attempts'][0]
    assert accepted['accepted']
    assert accepted['verified_other_body_faces'] == [dict(name='B', frame_index=41 if reverse else 19)]
    if partial:
        assert accepted['whole_path_rejection']['reason'] == 'unconfirmed_main_ownership'
        assert any(d.reference_id is None for d in result['decisions'])
    else:
        assert [(s.start, s.end) for s in result['segments']] == [(0., 6.)]
    assert len(original['segments']) == 3


@pytest.mark.parametrize('case', ['same_body', 'missing_trace', 'missing_forward', 'missing_reverse',
                                  'disagreeing_reverse', 'ambiguous_mask', 'ambiguous_face', 'missing_face_body'])
def test_external_contrary_face_cannot_be_ignored_without_two_unique_disjoint_body_owners(case):
    from dance_highlight.services.mask_continuity import recover_mask_names
    original, records, anchors, joint = external_conflict_example()
    if case == 'ambiguous_face':
        records[19] = replace(records[19], person_bboxes=[*records[19].person_bboxes, records[19].person_bboxes[1]])
    elif case == 'missing_face_body':
        records[19] = replace(records[19], person_bboxes=records[19].person_bboxes[:1])
    calls = []
    def verify(anchor, path, targets):
        calls.append(list(targets))
        forward = [1] if case == 'same_body' else [] if case == 'missing_forward' else [0, 2] if case == 'ambiguous_mask' else [0]
        backward = [] if case == 'missing_reverse' else [2] if case == 'disagreeing_reverse' else forward
        return dict(accepted=True, reason='confirmed_visual_path', support_frames=targets,
                    trace=[] if case == 'missing_trace' else [dict(frame=19, forward=forward, reverse=backward)])
    result, audit = recover_mask_names(original, records, 'unused', 10., anchors,
                                      verify_track=verify, joint_matches=joint)
    assert len(calls) == 1
    assert result is original
    attempt = audit['candidates'][0]['attempts'][0]
    assert not attempt['accepted'] and attempt['reason'] == 'conflicting_direct_face_anchor'
    assert audit['recovered_seconds'] == 0.


def frozen_main_behind_other_role_example():
    import numpy as np
    from dance_highlight.services.segment import Segment
    from dance_highlight.services.reference_matcher import SegmentReferenceDecision
    output, records, _ = recovery_example()
    rows = [row for evidence in output['evidence'] for row, _ in evidence]
    spans = [(0., 1., 'A'), (1., 2., 'B'), (2., 4., None), (4., 6., 'C')]
    output.update(segments=[Segment('main', i, a, b, []) for i, (a, b, _) in enumerate(spans)],
                  decisions=[SegmentReferenceDecision(n, 'matched' if n else 'unmatched', 'face') for _, _, n in spans],
                  labels=[1, 2, None, 3], previews=[[] for _ in spans],
                  preview_sources=[({}, {}) for _ in spans], accurate_indices=[0, 1, 3],
                  evidence=[[(row, n) for row in rows if a <= row.time_seconds < b] for a, b, n in spans])
    for frame in range(10, 20):
        box = np.array([100., 10., 130., 90.])
        records[frame] = replace(records[frame], main_bbox=box,
                                person_bboxes=[records[frame].main_bbox, box])
    joint = {f: dict(name='A', status='accepted') for f in (5, 8)}
    return output, records, joint


def test_frozen_joint_main_can_be_context_after_another_member_takes_main():
    from dance_highlight.services.mask_continuity import recover_mask_names
    output, records, joint = frozen_main_behind_other_role_example()
    calls = []
    def verify(anchor, path, targets):
        calls.append(anchor.frame_index)
        assert any(1. <= r.t < 2. and r.main_bbox[0] == 100. for r in path)
        return dict(accepted=True, reason='confirmed_visual_path', support_frames=targets,
                    trace=[dict(frame=round(r.t * 10), forward=[0], reverse=[0]) for r in path])
    result, audit = recover_mask_names(output, records, 'unused', 10., [],
                                      joint_matches=joint, verify_track=verify)
    assert calls == [8]
    assert [(s.start, s.end, d.reference_id) for s, d in zip(result['segments'], result['decisions'])] == [
        (0., 1., 'A'), (1., 2., 'B'), (2., 4., 'A'), (4., 6., 'C')]
    assert audit['candidates'][0]['attempts'][0]['seed_kind'] == 'joint_context_face'
    assert audit['recovered_seconds'] == 2.
    assert result['anchors'] == [] and result['fallback_names'] == {}
    assert output['decisions'][2].reference_id is None


@pytest.mark.parametrize('barrier', ['single_face', 'different_names', 'unconfirmed_face', 'cut_to_target',
                                     'cut_between_seed_pair', 'output_name_only'])
def test_extra_context_requires_original_repeated_joint_faces_in_target_shot(barrier):
    from dance_highlight.services.mask_continuity import recover_mask_names
    output, records, joint = frozen_main_behind_other_role_example()
    cuts = []
    if barrier == 'single_face':
        joint.pop(5)
    elif barrier == 'different_names':
        joint[5]['name'] = 'B'
    elif barrier == 'unconfirmed_face':
        output['evidence'][0] = [(replace(r, association='ambiguous') if r.frame_index == 5 else r, n)
                                 for r, n in output['evidence'][0]]
    elif barrier == 'cut_to_target':
        cuts = [15]
    elif barrier == 'cut_between_seed_pair':
        cuts = [7]
    else:
        joint = {}
    calls = []
    def verify(*args):
        calls.append(args)
        return dict(accepted=False, reason='test')
    result, audit = recover_mask_names(output, records, 'unused', 10., [],
                                      joint_matches=joint, cut_frames=cuts, verify_track=verify)
    assert calls == []
    assert result is output and audit['recovered_seconds'] == 0.


def test_extra_context_does_not_retrack_an_already_fully_proven_original_unknown():
    from dance_highlight.services.mask_continuity import recover_mask_names
    output, records, anchors = recovery_example()
    joint = {f: dict(name='A', status='accepted') for f in (5, 8)}
    calls = []
    def verify(anchor, path, targets):
        calls.append(anchor.frame_index)
        return dict(accepted=True, reason='confirmed_visual_path', support_frames=targets)
    result, audit = recover_mask_names(output, records, 'unused', 10., anchors,
                                      joint_matches=joint, verify_track=verify)
    assert calls == [18, 42]
    assert [(s.start, s.end) for s in result['segments']] == [(0., 6.)]


@pytest.mark.parametrize('left_name', ['A', 'Z'])
def test_competing_joint_contexts_are_all_checked_regardless_of_name_order(left_name):
    from dance_highlight.services.mask_continuity import recover_mask_names
    from dance_highlight.services.reference_matcher import SegmentReferenceDecision
    from dance_highlight.services.segment import Segment
    output, records, _ = frozen_main_behind_other_role_example()
    rows = [row for evidence in output['evidence'] for row, _ in evidence]
    spans = [(0., 1., left_name), (1., 2., 'B'), (2., 4., None),
             (4., 5., 'C'), (5., 6., 'D')]
    output.update(segments=[Segment('main', i, a, b, []) for i, (a, b, _) in enumerate(spans)],
                  decisions=[SegmentReferenceDecision(n, 'matched' if n else 'unmatched', 'face') for _, _, n in spans],
                  labels=[1, 2, None, 3, 4], previews=[[] for _ in spans],
                  preview_sources=[({}, {}) for _ in spans], accurate_indices=[0, 1, 3, 4],
                  evidence=[[(row, n) for row in rows if a <= row.time_seconds < b] for a, b, n in spans])
    joint = {f: dict(name=n, status='accepted') for n, frames in
             [(left_name, (5, 8)), ('D', (52, 55))] for f in frames}
    calls = []
    def verify(anchor, path, targets):
        calls.append(anchor.frame_index)
        return dict(accepted=True, reason='confirmed_visual_path', support_frames=targets)
    result, audit = recover_mask_names(output, records, 'unused', 10., [],
                                      joint_matches=joint, verify_track=verify)
    assert sorted(calls) == [8, 52]
    assert result is output and audit['recovered_seconds'] == 0.
    assert audit['candidates'][0]['reason'] == 'conflicting_tracking_names'


def test_joint_context_same_frame_other_body_is_a_separate_tracking_request():
    from dance_highlight.services.mask_continuity import recover_mask_names
    output, records, joint = frozen_main_behind_other_role_example()
    rows = {row.frame_index: row for evidence in output['evidence'] for row, _ in evidence}
    context = [('A', replace(rows[f], body_bbox=(100., 10., 130., 90.),
                             face_bbox=(105., 10., 120., 25.))) for f in (5, 8)]
    calls = []
    def verify(anchor, path, targets):
        calls.append((anchor.frame_index, anchor.body_bbox[0]))
        accepted = anchor.body_bbox[0] == 10.
        return dict(accepted=accepted, reason='confirmed_visual_path' if accepted else 'unconfirmed_main_ownership',
                    support_frames=targets if accepted else [])
    result, audit = recover_mask_names(output, records, 'unused', 10., [],
        joint_matches=joint, context_anchors=context, verify_track=verify)
    assert calls == [(8, 100.), (8, 10.)]
    assert audit['recovered_seconds'] == 2.
    assert result['decisions'][2].reference_id == 'A'


def test_missing_anchor_face_box_is_rejected_by_tracker_without_aborting_recovery():
    from dance_highlight.services.mask_continuity import recover_mask_names
    output, records, anchors = recovery_example()
    output['evidence'] = [[(replace(row, face_bbox=None), name) for row, name in evidence]
                           for evidence in output['evidence']]
    calls = []
    def verify(anchor, path, targets):
        calls.append(anchor.frame_index)
        assert anchor.face_bbox is None
        return dict(accepted=False, reason='unconfirmed_anchor_body')
    result, audit = recover_mask_names(output, records, 'unused', 10., anchors, verify_track=verify)
    assert calls == [18, 42]
    assert result is output and audit['recovered_seconds'] == 0.


@pytest.mark.parametrize('reverse', [[], [1]])
def test_joint_context_external_face_conflict_needs_strict_bidirectional_ownership(reverse):
    from dance_highlight.services.mask_continuity import recover_mask_names
    output, records, joint = frozen_main_behind_other_role_example()
    joint[19] = dict(name='B', status='accepted')
    output['evidence'][1] = [(replace(r, body_bbox=tuple(records[19].main_bbox)) if r.frame_index == 19 else r, n)
                             for r, n in output['evidence'][1]]
    calls = []
    def verify(anchor, path, targets):
        calls.append(anchor.frame_index)
        return dict(accepted=True, reason='confirmed_visual_path', support_frames=targets,
                    trace=[dict(frame=19, forward=[0], reverse=reverse)])
    result, audit = recover_mask_names(output, records, 'unused', 10., [],
                                      joint_matches=joint, verify_track=verify)
    assert calls == [8]
    assert result is output
    assert audit['candidates'][0]['attempts'][0]['reason'] == 'conflicting_direct_face_anchor'


def test_tracking_path_stops_on_last_target_observation_before_next_part():
    from dance_highlight.services.mask_continuity import recover_mask_names
    original,records,anchors=recovery_example()
    paths=[]
    def verify(anchor,path,targets):
        paths.append([round(r.t*10) for r in path])
        return dict(accepted=False,reason='test')
    recover_mask_names(original,records,'unused',10.,anchors,verify_track=verify)
    assert paths[0]==list(range(18,40))
    assert paths[1]==list(range(42,19,-1))


@pytest.mark.parametrize('left_stop,right_stop,expected', [
    (30,29,[(0.,2.95,'A'),(2.95,6.,'B')]),
    (26,34,[(0.,2.55,'A'),(2.55,3.45,None),(3.45,6.,'B')]),
    (36,29,[(0.,2.95,'A'),(2.95,3.55,None),(3.55,6.,'B')]),
])
def test_main_change_preserves_verified_sides_without_naming_gap_or_conflict(left_stop,right_stop,expected):
    from dance_highlight.services.mask_continuity import recover_mask_names
    from dance_highlight.services.reference_matcher import SegmentReferenceDecision
    original,records,anchors=recovery_example()
    original['decisions'][2]=SegmentReferenceDecision('B','matched','face')
    anchors=[a|{'name':'B' if a['frame_index']>=40 else 'A'} for a in anchors]
    def verify(anchor,path,targets):
        stop=left_stop if anchor.frame_index==18 else right_stop
        if stop in targets:
            return dict(accepted=False,reason='unconfirmed_main_ownership',frame=stop)
        # A second forward AND reverse check from the frozen face is required.
        frames=[round(r.t*10) for r in path]
        assert frames[0]==anchor.frame_index and set(targets)<=set(frames)
        assert stop not in frames
        return dict(accepted=True,reason='confirmed_visual_path',support_frames=targets)
    result,audit=recover_mask_names(original,records,'unused',10.,anchors,verify_track=verify)
    assert [(round(s.start,2),round(s.end,2),d.reference_id)
            for s,d in zip(result['segments'],result['decisions'])]==expected
    assert audit['recovered_seconds']==pytest.approx(sum(b-a for a,b,n in expected if n)-4.)
    assert sorted(r.frame_index for evidence in result['evidence'] for r,_ in evidence)==list(range(60))
    assert all(name is None for evidence in result['evidence'] for row,name in evidence if 2<=row.time_seconds<4)
    assert [(s.start,s.end) for s in original['segments']]==[(0.,2.),(2.,4.),(4.,6.)]


@pytest.mark.parametrize('failure', ['short_support','reverse_failed','camera_failed'])
def test_a_failed_or_unproven_partial_path_cannot_recover_a_name(failure):
    from dance_highlight.services.mask_continuity import recover_mask_names
    original,records,anchors=recovery_example()
    anchors=anchors[:2]
    def verify(anchor,path,targets):
        if len(targets)==20:
            return dict(accepted=False,reason='unconfirmed_camera_transition' if failure=='camera_failed'
                        else 'unconfirmed_main_ownership',frame=21 if failure=='short_support' else 30)
        return dict(accepted=False,reason='inconsistent_visual_path')
    result,audit=recover_mask_names(original,records,'unused',10.,anchors,verify_track=verify)
    assert result is original
    assert audit['recovered_seconds']==0.


def test_partial_verification_never_names_frames_outside_its_requested_path():
    from dance_highlight.services.mask_continuity import recover_mask_names
    original,records,anchors=recovery_example()
    def verify(anchor,path,targets):
        if anchor.frame_index != 18:
            return dict(accepted=False,reason='unconfirmed_camera_transition')
        if 30 in targets:
            return dict(accepted=False,reason='unconfirmed_main_ownership',frame=30)
        return dict(accepted=True,reason='confirmed_visual_path')
    result,audit=recover_mask_names(original,records,'unused',10.,anchors,verify_track=verify)
    assert [(round(s.start,2),round(s.end,2),d.reference_id)
            for s,d in zip(result['segments'],result['decisions'])]==[(0.,2.95,'A'),(2.95,4.,None),(4.,6.,'A')]


@pytest.mark.parametrize('reverse', [(),(1,)])
def test_torso_supported_frame_requires_same_owner_in_reverse(reverse):
    rows=trace()
    rows[30]=replace(rows[30],torso_fallback=True,reverse_owners=reverse)
    verdict=evaluate_track(rows,anchor_owner=0,target_frames=range(20,40))
    assert not verdict['accepted']


def test_complete_bidirectional_torso_proof_preserves_back_facing_main():
    rows=trace()
    rows[30]=replace(rows[30],torso_fallback=True)
    assert evaluate_track(rows,anchor_owner=0,target_frames=range(20,40))['accepted']


@pytest.mark.parametrize('forward,reverse', [((0,),()),((0,),(1,)),((0,),(0,1)),((),(0,)),((1,),(0,))])
def test_torso_on_bridge_frames_also_requires_two_unique_matching_directions(forward,reverse):
    rows=trace()
    rows[10]=replace(rows[10],torso_fallback=True,forward_owners=forward,reverse_owners=reverse)
    assert not evaluate_track(rows,anchor_owner=0,target_frames=range(30,50))['accepted']


@pytest.mark.parametrize('rejected_path_proves_cut',[False,True])
def test_main_face_partial_retry_cannot_claim_across_unvisited_cut(rejected_path_proves_cut):
    from dance_highlight.services.mask_continuity import recover_mask_names
    original,records,anchors=recovery_example()
    original['evidence']=[[(replace(o,frame_index=o.frame_index*2),n) for o,n in evidence] for evidence in original['evidence']]
    anchors=[dict(a,frame_index=a['frame_index']*2) for a in anchors if a['frame_index']<20]
    records=records[::2];seen=[]
    def partial(anchor,path,targets):
        seen.append([round(r.t*20) for r in path])
        if 60 in targets:
            return dict(accepted=False,reason='unconfirmed_main_ownership',frame=60,
                        camera=[dict(from_frame=56,to_frame=60,accepted=True)] if rejected_path_proves_cut else [])
        return dict(accepted=True,reason='confirmed_visual_path',support_frames=targets,trace=[])
    result,audit=recover_mask_names(original,records,'unused',20.,anchors,cut_frames=[57],verify_track=partial)
    assert seen[-1]==[36,40,44,48,52,56]
    assert [(s.start,s.end,d.reference_id) for s,d in zip(result['segments'],result['decisions'])]==[(0.,2.85,'A'),(2.85,4.,None),(4.,6.,'A')]


def test_unavailable_cut_inventory_cannot_be_treated_as_no_cuts():
    from dance_highlight.services.mask_continuity import recover_mask_names
    original,records,anchors=recovery_example()
    def must_not_track(*args):raise AssertionError('output edges lack camera coverage')
    result,audit=recover_mask_names(original,records,'unused',10.,anchors,cut_frames=None,verify_track=must_not_track)
    assert result is original
    assert audit['reason']=='source_cut_inventory_unavailable'
    assert audit['recovered_seconds']==0.


@pytest.mark.parametrize('reverse',[False,True])
@pytest.mark.parametrize('kind',['single','multiple'])
def test_unproved_cut_keeps_independently_verified_prefix(reverse,kind):
    from dance_highlight.services.mask_continuity import recover_mask_names
    original,records,anchors=recovery_example()
    anchors=anchors[2:] if reverse else anchors[:2]
    calls=[]
    def verify(anchor,path,targets):
        calls.append(list(targets))
        if len(targets)==20:
            if kind=='multiple':
                return dict(accepted=False,reason='multiple_unobserved_camera_transitions',
                            from_frame=31 if reverse else 29,to_frame=29 if reverse else 31,cut_frames=[30,31])
            return dict(accepted=False,reason='unconfirmed_camera_transition',
                        camera=[dict(accepted=False,from_frame=30 if reverse else 29,to_frame=29 if reverse else 30)])
        assert all(f>= (31 if kind=='multiple' else 30) for f in targets) if reverse else all(f<30 for f in targets)
        return dict(accepted=True,reason='confirmed_visual_path',support_frames=targets)
    result,audit=recover_mask_names(original,records,'unused',10.,anchors,cut_frames=[30,31] if kind=='multiple' else [30],verify_track=verify)
    assert len(calls)==2
    assert audit['recovered_seconds']> .7
    for seg,decision in zip(result['segments'],result['decisions']):
        if decision.reference_id and seg.start<4 and seg.end>2:
            assert seg.start>=(3.1 if kind=='multiple' else 3.) if reverse else seg.end<=3.


def seedless_neighbor_example():
    from dance_highlight.services.reference_matcher import SegmentReferenceDecision
    from dance_highlight.services.segment import Segment
    output, records, _ = recovery_example()
    rows = [row for evidence in output['evidence'] for row, _ in evidence]
    names = ['A', 'A', None, 'A', None, 'A']
    output.update(
        segments=[Segment('main', i, float(i), float(i + 1), []) for i in range(6)],
        decisions=[SegmentReferenceDecision(n, 'matched' if n else 'unmatched', 'face') for n in names],
        labels=[None] * 6, previews=[[] for _ in names],
        preview_sources=[({}, {}) for _ in names], accurate_indices=[0, 1, 3, 5],
        evidence=[[(row, names[i]) for row in rows if i <= row.time_seconds < i + 1] for i in range(6)],
    )
    return output, records


@pytest.mark.parametrize('seed_frames,expected_anchor', [([2, 5], 5), ([52, 55], 52)])
def test_search_reaches_original_seed_past_same_name_and_unknown_parts(seed_frames, expected_anchor):
    from dance_highlight.services.mask_continuity import recover_mask_names
    original, records = seedless_neighbor_example()
    anchors = [dict(name='A', frame_index=f, time_seconds=f / 10.) for f in seed_frames]
    calls = []
    def verify(anchor, path, targets):
        if targets == list(range(20, 30)):
            calls.append(anchor.frame_index)
        return dict(accepted=True, reason='confirmed_visual_path', support_frames=targets)
    result, audit = recover_mask_names(original, records, 'unused', 10., anchors, verify_track=verify)
    assert calls == [expected_anchor]
    target = next(c for c in audit['candidates'] if c['start'] == 2.)
    assert target['recovered_ranges'] == [dict(start=2., end=3., name='A')]
    # Intermediate names only guide search; original seed rows remain immutable.
    assert all(a['anchor_frame'] in seed_frames for c in audit['candidates'] for a in c['attempts'])
    assert result['anchors'] == []


@pytest.mark.parametrize('barrier', ['different_name', 'time_gap'])
@pytest.mark.parametrize('direction', [-1, 1])
def test_search_cannot_cross_seedless_other_name_or_time_gap(barrier, direction):
    from dance_highlight.services.mask_continuity import recover_mask_names
    from dance_highlight.services.reference_matcher import SegmentReferenceDecision
    original, records = seedless_neighbor_example()
    # The first named neighbor fixes A; the next intervening part is the barrier.
    index = 1 if direction == -1 else 4
    if direction == -1:
        original['decisions'][2] = SegmentReferenceDecision('A', 'matched', 'face')
        original['decisions'][3] = SegmentReferenceDecision(None, 'unmatched', 'face')
    target_frames = list(range(30, 40)) if direction == -1 else list(range(20, 30))
    if barrier == 'different_name':
        original['decisions'][index] = SegmentReferenceDecision('B', 'matched', 'face')
    else:
        original['segments'][index] = replace(original['segments'][index], end=index + .9)
    frames = [2, 5] if direction == -1 else [52, 55]
    anchors = [dict(name='A', frame_index=f, time_seconds=f / 10.) for f in frames]
    calls = []
    def verify(anchor, path, targets):
        if targets == target_frames:
            calls.append(anchor.frame_index)
        return dict(accepted=False, reason='unconfirmed_visual_path')
    recover_mask_names(original, records, 'unused', 10., anchors, verify_track=verify)
    assert not calls


def test_search_uses_nearest_seed_once_and_keeps_failed_camera_path_unknown():
    from dance_highlight.services.mask_continuity import recover_mask_names
    original, records = seedless_neighbor_example()
    frames = [32, 35, 52, 55]
    anchors = [dict(name='A', frame_index=f, time_seconds=f / 10.) for f in frames]
    calls = []
    def verify(anchor, path, targets):
        if targets == list(range(20, 30)):
            calls.append(anchor.frame_index)
        return dict(accepted=False, reason='unconfirmed_camera_transition')
    result, audit = recover_mask_names(original, records, 'unused', 10., anchors, verify_track=verify)
    assert calls == [32]
    assert result is original
    assert audit['recovered_seconds'] == 0.


def short_continuation_example(reverse=False):
    from dance_highlight.services.reference_matcher import SegmentReferenceDecision
    from dance_highlight.services.segment import Segment
    output, records, _ = recovery_example()
    rows = [row for evidence in output['evidence'] for row, _ in evidence]
    spans = [(0., 2., 'B' if reverse else 'A'), (2., 2.2, None),
             (2.2, 6., 'A' if reverse else 'B')]
    output.update(
        segments=[Segment('main', i, a, b, []) for i, (a, b, _) in enumerate(spans)],
        decisions=[SegmentReferenceDecision(n, 'matched' if n else 'unmatched',
                   'member_timeline_consensus') for _, _, n in spans],
        evidence=[[(row, n) for row in rows if a <= row.time_seconds < b] for a, b, n in spans],
    )
    anchors = [dict(name='A', frame_index=f, time_seconds=f / 10.)
               for f in ([23, 26] if reverse else [15, 18])]
    return output, records, anchors


@pytest.mark.parametrize('reverse', [False, True])
def test_short_unknown_uses_fresh_proof_of_adjacent_original_main(reverse):
    from dance_highlight.services.mask_continuity import recover_mask_names
    original, records, anchors = short_continuation_example(reverse)
    calls = []
    def verify(anchor, path, targets):
        calls.append((list(targets), [round(r.t * 10) for r in path]))
        return evaluate_track([TraceFrame(round(r.t * 10), r.t, 0, (0,), (0,), .9)
                               for r in path], anchor_owner=0, target_frames=targets)
    result, audit = recover_mask_names(original, records, 'unused', 10., anchors, verify_track=verify)
    assert audit['recovered_seconds'] == pytest.approx(.2)
    assert calls[0][0] == [20, 21]
    assert calls[1][0] == ([20, 21, 22] if reverse else [19, 20, 21])
    assert calls[0][1] == calls[1][1]  # No longer path or new seed.
    attempt = audit['candidates'][0]['attempts'][0]
    assert attempt['support_frames'] == [20, 21]
    assert attempt['verification_frames'] == calls[1][0]
    assert attempt['whole_path_rejection']['reason'] == 'insufficient_target_support'
    assert len(result['segments']) == 2
    assert original['decisions'][1].reference_id is None
    assert all(name is None for row, name in result['evidence'][0 if not reverse else 1]
               if 2 <= row.time_seconds < 2.2)


@pytest.mark.parametrize('barrier', ['gap', 'recovered_neighbor', 'other_neighbor',
                                   'missing_main', 'group', 'raw_cut', 'discovered_cut'])
def test_short_support_cannot_skip_an_ineligible_neighbor(barrier):
    from dance_highlight.services.mask_continuity import recover_mask_names
    from dance_highlight.services.reference_matcher import SegmentReferenceDecision
    original, records, anchors = short_continuation_example()
    if barrier == 'gap':
        original['segments'][0] = replace(original['segments'][0], end=1.95)
    elif barrier == 'recovered_neighbor':
        original['decisions'][0] = SegmentReferenceDecision('A', 'matched', 'member_body_continuity')
    elif barrier == 'other_neighbor':
        original['decisions'][0] = SegmentReferenceDecision('B', 'matched', 'member_timeline_consensus')
    elif barrier == 'missing_main':
        records[19] = replace(records[19], main_bbox=None)
    elif barrier == 'group':
        records[19] = replace(records[19], scene_kind='group')
    calls = []
    def verify(anchor, path, targets):
        calls.append(list(targets))
        return dict(accepted=False, reason='insufficient_target_support')
    if barrier == 'discovered_cut':
        verify.transition_cache = {20: dict(cut=True)}
    result, audit = recover_mask_names(original, records, 'unused', 10., anchors,
        cut_frames=[20] if barrier == 'raw_cut' else [], verify_track=verify)
    assert result is original
    assert len(calls) <= 1
    assert audit['recovered_seconds'] == 0.


@pytest.mark.parametrize('failure', ['ownership', 'missing_support', 'new_cut'])
def test_expanded_validation_needs_every_original_and_added_frame(failure):
    from dance_highlight.services.mask_continuity import recover_mask_names
    original, records, anchors = short_continuation_example()
    calls = []
    def verify(anchor, path, targets):
        calls.append(list(targets))
        if targets == [20, 21]:
            return dict(accepted=False, reason='insufficient_target_support')
        if failure == 'ownership':
            return dict(accepted=False, reason='unconfirmed_main_ownership', frame=19)
        if failure == 'new_cut':
            verify.transition_cache = {20: dict(cut=True)}
        return dict(accepted=True, reason='confirmed_visual_path',
                    support_frames=[19, 20] if failure == 'missing_support' else targets)
    result, audit = recover_mask_names(original, records, 'unused', 10., anchors, verify_track=verify)
    assert len(calls) == 2
    assert result is original
    assert audit['recovered_seconds'] == 0.


def test_conflict_fragment_cannot_borrow_the_whole_claim_support():
    from dance_highlight.services.mask_continuity import recover_mask_names
    original, records, anchors = short_continuation_example()
    anchors += [dict(name='B', frame_index=f, time_seconds=f / 10.) for f in (23, 26)]
    def verify(anchor, path, targets):
        if anchor.frame_index == 23:
            return dict(accepted=True, reason='confirmed_visual_path', support_frames=[21])
        return evaluate_track([TraceFrame(round(r.t * 10), r.t, 0, (0,), (0,), .9)
                               for r in path], anchor_owner=0, target_frames=targets)
    result, audit = recover_mask_names(original, records, 'unused', 10., anchors, verify_track=verify)
    assert result is original
    assert audit['recovered_seconds'] == 0.
