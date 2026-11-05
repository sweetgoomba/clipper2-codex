from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest

from dance_highlight.services.face_evidence import FaceObservation
from dance_highlight.services.reference_matcher import SegmentReferenceDecision
from dance_highlight.services.segment import Segment


class Matcher:
    def match(self, row, *_args):
        name = 'A' if row.embedding[0] > .9 else 'B' if row.embedding[1] > .9 else None
        return SimpleNamespace(reference_id=name)


def output_parts(specs):
    result = dict(segments=[], decisions=[], labels=[], evidence=[], previews=[],
                  preview_sources=[], accurate_indices=[], anchors=[], inference_audit=['preserve'])
    for index, (start, end, assigned, observed) in enumerate(specs):
        times = sorted(set([start+.04, start+.24, end-.24, end-.04]))
        rows = [FaceObservation(round(t*100), t, index, (0., 0., 100., 200.), (0., 0., 100., 200.),
                    face_bbox=(20., 10., 40., 30.), embedding=np.eye(3)[0 if observed == 'A' else 1],
                    detector_score=.99, association='confirmed') for t in times]
        result['segments'].append(Segment('main', index, start, end,
            [(o.time_seconds, np.asarray(o.body_bbox), index) for o in rows]))
        result['decisions'].append(SegmentReferenceDecision(assigned,
            'matched' if assigned else 'unmatched', 'existing'))
        result['labels'].append(index+1 if assigned else None)
        result['evidence'].append([(o, observed) for o in rows])
        thumbs = {o.frame_index: f'{o.frame_index}'.encode() for o in rows}
        result['preview_sources'].append((thumbs, {}))
        result['previews'].append(list(thumbs.values()))
    result['accurate_indices'] = [len(specs)-1]
    return result


def combine(output, handoffs=()):
    from dance_highlight.services.output_continuity import coalesce_named_output
    return coalesce_named_output(output, Matcher(), handoffs=handoffs)


def test_continuous_six_seconds_becomes_one_clip_with_all_evidence_preserved():
    original = output_parts([(0., 2., 'A', 'A'), (2., 6., 'A', 'A')])
    result, audit = combine(original)
    assert [(s.start, s.end) for s in result['segments']] == [(0., 6.)]
    assert [d.reference_id for d in result['decisions']] == ['A']
    assert [o.frame_index for group in result['evidence'] for o, _ in group] == [
        o.frame_index for group in original['evidence'] for o, _ in group]
    assert result['accurate_indices'] == [0]
    assert len(result['segments'][0].bboxes) == 8
    assert result['inference_audit'] is original['inference_audit']
    assert len(original['segments']) == 2
    assert len(audit['joins']) == 1
    assert set(result['previews'][0]).issubset(set(sum(original['previews'], [])))


def test_a_conflicting_later_piece_does_not_erase_a_valid_prefix_join():
    result, audit = combine(output_parts([(0., 2., 'A', 'A'), (2., 4., 'A', 'A'), (4., 6., 'A', 'B')]))
    assert [(s.start, s.end) for s in result['segments']] == [(0., 4.), (4., 6.)]
    assert [d.reference_id for d in result['decisions']] == ['A', 'A']
    assert len(audit['joins']) == 1


def test_the_accumulated_union_is_checked_even_when_each_adjacent_pair_passes():
    from dance_highlight.services.member_timeline import _assign_piece
    original = output_parts([(0., 1., 'A', 'A'), (1., 2., 'A', 'A'), (2., 3., 'A', 'A')])
    for index, (start, end, times) in enumerate([
        (0., .3, [.02, .1, .2, .28]), (.3, .5, [.31, .49]), (.5, .8, [.52, .6, .7, .78])]):
        template = original['evidence'][index][0][0]
        rows = [(replace(template, frame_index=round(t*100), time_seconds=t,
                         embedding=np.array([0., 1., 0.]) if t in (.2, .52) else np.array([1., 0., 0.])),
                 None if t in (.2, .52) else 'A') for t in times]
        original['evidence'][index] = rows
        original['segments'][index] = replace(original['segments'][index], start=start, end=end,
            bboxes=[(o.time_seconds, np.asarray(o.body_bbox), index) for o, _ in rows])
    for left, right in [(0, 1), (1, 2)]:
        union = replace(original['segments'][left], end=original['segments'][right].end)
        assert _assign_piece(union, original['evidence'][left]+original['evidence'][right],
                             Matcher(), [], 'control').reference_id == 'A'
    result, audit = combine(original)
    assert [(s.start, s.end) for s in result['segments']] == [(0., .5), (.5, .8)]
    assert len(audit['joins']) == 1


@pytest.mark.parametrize('specs', [
    [(0., 2., None, 'A'), (2., 4., None, 'A')],
    [(0., 2., 'A', 'A'), (2., 4., 'B', 'B')],
    [(0., 2., 'A', 'A'), (2.001, 4., 'A', 'A')],
    [(0., 2., 'A', 'A'), (2., 4., 'A', 'B')],
])
def test_no_gap_unknown_identity_change_or_conflicting_face_is_joined(specs):
    original = output_parts(specs)
    result, audit = combine(original)
    assert [(s.start, s.end) for s in result['segments']] == [(s.start, s.end) for s in original['segments']]
    assert audit['joins'] == []


def test_actual_handoff_bracket_protects_boundary_but_not_an_unrelated_child_edge():
    original = output_parts([(0., 2., 'A', 'A'), (2., 6., 'A', 'A')])
    protected, audit = combine(original, [dict(previous_time=1.98, time=2.04)])
    assert len(protected['segments']) == 2
    assert audit['joins'] == []
    joined, _ = combine(original, [dict(previous_time=.0, time=.04)])
    assert [(s.start, s.end) for s in joined['segments']] == [(0., 6.)]


def test_missing_main_audit_or_unobserved_face_gap_keeps_existing_clips():
    original = output_parts([(0., 2., 'A', 'A'), (2., 6., 'A', 'A')])
    unchanged, audit = combine(original, None)
    assert len(unchanged['segments']) == 2
    assert audit['joins'] == []
    original['evidence'][0] = original['evidence'][0][:2]
    result, audit = combine(original)
    assert len(result['segments']) == 2
    assert audit['joins'] == []


@pytest.mark.parametrize('handoff', [{}, dict(previous_time=1., time=float('nan')),
                                    dict(previous_time=2., time=1.)])
def test_invalid_handoff_proof_keeps_the_existing_boundary(handoff):
    original = output_parts([(0., 2., 'A', 'A'), (2., 6., 'A', 'A')])
    result, audit = combine(original, [handoff])
    assert len(result['segments']) == 2
    assert audit['joins'] == []


def test_distinct_raw_names_are_not_joined_when_their_filename_forms_collide():
    from dance_highlight.services.output_continuity import coalesce_named_output
    original = output_parts([(0., 2., 'a b', 'A'), (2., 6., 'a_b', 'A')])
    original['evidence'] = [[(row, 'a_b') for row, _ in group] for group in original['evidence']]
    matcher = SimpleNamespace(match=lambda *_: SimpleNamespace(reference_id='a_b'))
    result, audit = coalesce_named_output(original, matcher, handoffs=[])
    assert len(result['segments']) == 2
    assert [d.reference_id for d in result['decisions']] == ['a b', 'a_b']
    assert audit['joins'] == []


def recorded_chaewon_parts(expanded=False):
    import json
    from pathlib import Path
    from dance_highlight.services.face_recovery import ReferenceObservationMatcher
    from dance_highlight.services.reference_matcher import ReferenceEmbeddingSample
    data=json.loads((Path(__file__).parent/'fixtures/dance_scene_review/made_my_night_continuity.json').read_text())
    source=data['output'];name=source['name']
    observations=[]
    for item in source['observations']:
        row=dict(item);primary_name=row.pop('primary_name')
        row['embedding']=np.asarray(row['embedding'],dtype=np.float32) if row['embedding'] is not None else None
        observations.append((FaceObservation(**row),primary_name))
    output=dict(segments=[],decisions=[],labels=[],evidence=[],previews=[],preview_sources=[],
                accurate_indices=[0,1],anchors=[])
    for i,(start,end) in enumerate(source['expanded_ranges'] if expanded else source['ranges']):
        rows=[row for row in observations if start<=row[0].time_seconds<end]
        output['segments'].append(Segment('main',None,start,end,[]))
        output['decisions'].append(SegmentReferenceDecision(name,'matched','member_timeline_consensus'))
        output['labels'].append(i+1);output['evidence'].append(rows)
        output['previews'].append([]);output['preview_sources'].append(({},{}))
    references=[ReferenceEmbeddingSample(**dict(row,embedding=np.asarray(row['embedding'],dtype=np.float32)))
                for row in source['references']]
    matcher=ReferenceObservationMatcher(references=references,analysis_id='recorded-continuity-test',
        video_sha256='0'*64,detector_sha256='1'*64,recognizer_sha256='2'*64,config_sha256='3'*64,
        backend_version='saved-embeddings',video_size=(1920,1080),max_distance=.6)
    return output,matcher,{int(k):v for k,v in data['joint_matches'].items()}


def test_recorded_35_36_37_rechecks_the_old_edge_after_right_parts_join():
    from dance_highlight.services.output_continuity import coalesce_named_output
    original,matcher,joint=recorded_chaewon_parts(expanded=True)
    result,audit=coalesce_named_output(original,matcher,handoffs=[],joint_matches=joint)
    assert [(s.start,s.end) for s in result['segments']] == [(79.8798,84.63455)]
    assert result['evidence'][0] == sum(original['evidence'],[])
    assert audit['joins'][-1]['source_indices'] == [0,1,2]


def test_a_plausible_contrary_model_result_cannot_be_discarded_as_dual_rejected_noise():
    from dance_highlight.services.output_continuity import coalesce_named_output
    original,matcher,joint=recorded_chaewon_parts(expanded=True)
    joint[4848]=dict(joint[4848],secondary=.55)
    result,_=coalesce_named_output(original,matcher,handoffs=[],joint_matches=joint)
    assert len(result['segments']) > 1


def test_recorded_chaewon_36_37_join_uses_dual_support_without_changing_evidence():
    from dance_highlight.services.output_continuity import coalesce_named_output
    original,matcher,joint=recorded_chaewon_parts()
    baseline,_=coalesce_named_output(original,matcher,handoffs=[])
    assert len(baseline['segments']) == 2  # The recorded primary-only union rejects a view change.
    result,audit=coalesce_named_output(original,matcher,handoffs=[],joint_matches=joint)
    assert [(s.start,s.end) for s in result['segments']] == [(81.34793333333333,84.63455)]
    assert result['decisions'][0].reference_id == '김채원'
    assert result['evidence'][0] == original['evidence'][0]+original['evidence'][1]
    assert len(audit['joins']) == 1


@pytest.mark.parametrize('barrier',['missing_anchor','missing_bridge','contrary_best','accepted_other',
                                  'named_other','handoff_inside_support'])
def test_joint_join_never_crosses_unproved_or_contrary_boundary_support(barrier):
    from dance_highlight.services.output_continuity import coalesce_named_output
    original,matcher,joint=recorded_chaewon_parts();handoffs=[]
    if barrier=='missing_anchor':joint.pop(4876)
    elif barrier=='missing_bridge':joint.pop(4896)
    elif barrier=='contrary_best':joint[4896]=dict(joint[4896],best='사쿠라')
    elif barrier=='accepted_other':joint[4896]=dict(joint[4896],status='accepted',name='사쿠라')
    elif barrier=='named_other':
        original['evidence'][0]=[(row,'사쿠라' if row.frame_index==4896 else name)
                                 for row,name in original['evidence'][0]]
    else:handoffs=[dict(previous_time=81.6,time=81.7)]
    result,audit=coalesce_named_output(original,matcher,handoffs=handoffs,joint_matches=joint)
    assert len(result['segments']) == 2
    assert audit['joins'] == []


def recorded_sakura_gap():
    import json
    from pathlib import Path
    from dance_highlight.services.segment import FrameRec
    data=json.loads((Path(__file__).parent/'fixtures/dance_scene_review/made_my_night_sakura_gap.json').read_text())
    original,matcher,_=recorded_chaewon_parts()
    original.update(segments=[],decisions=[],labels=[],evidence=[],previews=[],preview_sources=[],accurate_indices=[])
    observations=[]
    for item in data['observations']:
        row=dict(item);name=row.pop('primary_name')
        row['embedding']=np.asarray(row['embedding'],np.float32) if row['embedding'] is not None else None
        observations.append((FaceObservation(**row),name))
    for i,p in enumerate(data['parts']):
        original['segments'].append(Segment('main',None,p['start'],p['end'],[]))
        original['decisions'].append(SegmentReferenceDecision(p['name'],'matched' if p['name'] else 'unmatched','existing'))
        original['evidence'].append([(o,n) for o,n in observations if p['start']<=o.time_seconds<p['end']])
        original['previews'].append([]);original['preview_sources'].append(({},{}))
        original['labels'].append(i+1 if p['name'] else None);original['accurate_indices'].append(i)
    records=[]
    for r in data['records']:
        main=r['scene_kind']=='main'
        records.append(FrameRec(r['time_seconds'],r['candidate_main_id'] if main else None,
            r['candidate_main_bbox'] if main else None,not main,person_bboxes=r['body_boxes'],
            person_pose_keypoints=r['pose_keypoints'],person_head_keypoints=r['head_keypoints'],
            scene_kind=r['scene_kind'],scene_reason=r['scene_reason'],candidate_main_id=r['candidate_main_id'],
            candidate_main_bbox=r['candidate_main_bbox']))
    return original,matcher,dict(frame_records=records,fps=data['fps'],cut_frames=data['cut_frames'],
        mask_refinement=data['mask_refinement'],joint_matches={int(k):v for k,v in data['joint_matches'].items()})


@pytest.mark.parametrize('membership_type',[list,tuple])
def test_recorded_sakura_unknown_sample_extends_the_original_verified_mask_path(membership_type):
    from dance_highlight.services.output_continuity import coalesce_named_output
    original,matcher,kwargs=recorded_sakura_gap()
    # Runtime mask traces use tuples; the saved JSON diagnostics use lists.
    for candidate in kwargs['mask_refinement']['candidates']:
        for proof in candidate['attempts']:
            for trace in proof.get('trace',[]):
                for key in ('forward','reverse'):
                    trace[key]=membership_type(trace[key])
    result,audit=coalesce_named_output(original,matcher,handoffs=[],**kwargs)
    assert [(s.start,s.end) for s in result['segments']] == [(32.515816666666666,34.8348),(35.4354,35.6356)]
    assert [d.reference_id for d in result['decisions']] == ['사쿠라','사쿠라']
    assert result['evidence'][0] == sum(original['evidence'][:3],[])
    assert result['anchors'] is original['anchors']
    assert original['decisions'][1].reference_id is None
    assert audit['bridges'][0]['source_frames'] == [2080]
    assert audit['bridges'][0]['seed_frames'] == [2060,2124]
    assert audit['bridges'][0]['extended_from_frame'] == 2084


@pytest.mark.parametrize('membership',[None,2,'2',{'index':2},[2,3],(2,3),[2.0],[True]])
def test_mask_edge_requires_one_valid_original_owner(membership):
    from dance_highlight.services.output_continuity import coalesce_named_output
    original,matcher,kwargs=recorded_sakura_gap()
    proof=kwargs['mask_refinement']['candidates'][1]['attempts'][1]
    edge=next(t for t in proof['trace'] if t['frame']==2084)
    edge.update(forward=membership,reverse=membership)
    result,audit=coalesce_named_output(original,matcher,handoffs=[],**kwargs)
    assert len(result['segments'])==len(original['segments'])
    assert not audit['bridges']


@pytest.mark.parametrize('barrier',['missing_proof','failed_proof','wrong_mask_owner','missing_frozen_anchor',
    'primary_other','accepted_other','plausible_other','handoff','cut_inside_extension','missing_pose',
    'invalid_pose','group_sample','same_track_different_body','competing_mask','competing_mask_edge'])
def test_sakura_gap_requires_original_mask_ownership_and_observed_body_path(barrier):
    from dance_highlight.services.output_continuity import coalesce_named_output
    original,matcher,kwargs=recorded_sakura_gap();handoffs=[]
    right=kwargs['mask_refinement']['candidates'][1]['attempts'][1]
    if barrier=='missing_proof':kwargs['mask_refinement']['candidates'].pop()
    elif barrier=='failed_proof':right['accepted']=False
    elif barrier=='wrong_mask_owner':
        right['trace'][-1].update(forward=[0],reverse=[0])
    elif barrier=='missing_frozen_anchor':kwargs['joint_matches'].pop(2124)
    elif barrier=='primary_other':
        original['evidence'][1]=[(row,'김채원') for row,_ in original['evidence'][1]]
    elif barrier=='accepted_other':
        kwargs['joint_matches'][2080].update(status='accepted',name='김채원')
    elif barrier=='plausible_other':
        kwargs['joint_matches'][2080].update(status='conflict',name=None,best='김채원',primary=.4)
    elif barrier=='handoff':handoffs=[dict(previous_time=34.6346,time=34.70133333333333)]
    elif barrier=='cut_inside_extension':kwargs['cut_frames'].append(2082)
    elif barrier in ('competing_mask','competing_mask_edge'):
        frame=2080 if barrier=='competing_mask' else 2084
        kwargs['mask_refinement']['candidates'].append(dict(attempts=[dict(accepted=True,name='김채원',
            anchor_frame=2200,support_frames=[frame],trace=[dict(frame=frame,forward=[1 if frame==2080 else 2],
            reverse=[1 if frame==2080 else 2],cycle_iou=.9)])]))
    else:
        records=kwargs['frame_records'];index=next(i for i,r in enumerate(records) if round(r.t*kwargs['fps'])==2080)
        if barrier=='missing_pose':records.pop(index)
        elif barrier=='invalid_pose':records[index].person_pose_keypoints[1][5][2]=0.
        elif barrier=='group_sample':records[index]=replace(records[index],scene_kind='group',main_bbox=None)
        else:records[index]=replace(records[index],main_bbox=records[index].person_bboxes[0],
                                   candidate_main_bbox=records[index].person_bboxes[0])
    result,audit=coalesce_named_output(original,matcher,handoffs=handoffs,**kwargs)
    assert [(s.start,s.end) for s in result['segments']] == [(s.start,s.end) for s in original['segments']]
    assert not audit['bridges']


def test_real_pipeline_coalesces_a_stale_named_boundary_after_projection(tmp_path, monkeypatch):
    from dance_highlight.services import pipeline, observed_main, secondary_faces, context_faces, joint_identity
    from dance_highlight.services.config import DanceConfig
    from dance_highlight.services.dance_meta import DanceMetaBuilder
    from dance_highlight.services.face_cluster import SegmentFaceResult
    from dance_highlight.services.reference_matcher import ReferenceEmbeddingSample
    from dance_highlight.services.segment import FrameRec
    box = np.array([0., 0., 100., 200.])
    records = [FrameRec(float(t), 1, box, False) for t in np.arange(.1, 10., .2)]
    seg = Segment('main', 1, 0., 10., [(r.t, box, 1) for r in records])
    monkeypatch.setattr(pipeline, 'build_raw_main_segments', lambda _: [seg])
    monkeypatch.setattr(pipeline, 'build_raw_group_segments', lambda _: [])
    monkeypatch.setattr(observed_main, 'refine_main_roles', lambda rows, *a, **k:
        (rows, dict(reason='complete', changes=[], handoffs=[], cut_frames=[])))
    monkeypatch.setattr(secondary_faces, 'recover_secondary_names', lambda *a, **k: ({}, {}))
    monkeypatch.setattr(context_faces, 'collect_source_context', lambda *a, **k: ([], dict(reason='complete')))
    revalidate = joint_identity.revalidate_named_segments
    def stale_boundary(*args, **kwargs):
        result, audit = revalidate(*args, **kwargs)
        assert len(result['segments']) == 1
        return joint_identity._apply_ranges(result, {0: [dict(start=0., end=3., name='A'),
                                                        dict(start=3., end=10., name='A')]}), audit
    monkeypatch.setattr(joint_identity, 'revalidate_named_segments', stale_boundary)
    class Face:
        def batch_segment_embeddings(self, _source, segments, **kwargs):
            rows = [FaceObservation(round(r.t*30), r.t, 1, tuple(box), tuple(box),
                face_bbox=(20., 10., 40., 30.), embedding=np.array([1., 0., 0.]),
                detector_score=.99, association='confirmed') for r in records]
            return [SegmentFaceResult(s, [], True, owned_observations=rows) for s in segments]
        def cluster_embeddings(self, _): return []
    class Render:
        def extract_thumbnail(self, _source, path, **kwargs): path.write_bytes(b'preview')
    config = DanceConfig()
    pipe = pipeline.DancePipeline(config, None, Face(), Render(), DanceMetaBuilder(config))
    pipe.analyze_video_to_records = lambda *a, **k: (records, 30., 10.)
    pipe._download_reference_images = lambda *a: {}
    def references(_, sample_sink):
        for index, name in enumerate(('A', 'B')):
            sample_sink.append(ReferenceEmbeddingSample(name, name, str(index)*64, 100, 100, np.eye(3)[index]))
        return {}
    pipe._build_reference_embeddings = references
    pipe._video_size = lambda _: (640, 480)
    source = tmp_path/'input.mp4'
    source.write_bytes(b'source')
    result = pipe.run(tmp_path, source, 12)
    assert [(c['start'], c['end'], c['person_id']) for c in result['lists']['main']] == [(0., 10., 'a')]
    assert 'named_boundaries' in result['diagnostics']['performance']['nested_stages']['cluster_map']
    assert 'group_context' in result['diagnostics']['performance']['nested_stages']['segment_build']


@pytest.mark.parametrize('barrier',[None,'no_samples','handoff','sample_inside','invalid_face_inside'])
def test_fresh_kazuha_empty_projection_prefix_joins_its_owned_sample(barrier):
    import json
    from pathlib import Path
    from dance_highlight.services.output_continuity import coalesce_named_output
    data=json.loads((Path(__file__).parent/'fixtures/dance_scene_review/made_fresh_context_holes.json').read_text())['output_empty']
    output,matcher,_=recorded_chaewon_parts()
    for key in ('segments','decisions','labels','evidence','previews','preview_sources'):output[key]=[]
    for i,p in enumerate(data['parts']):
        output['segments'].append(Segment('main',None,p['start'],p['end'],p['bboxes']))
        output['decisions'].append(SegmentReferenceDecision(p['name'],'matched',p['reason']))
        output['labels'].append(i+1);rows=[]
        for item in data['evidence'][i]:
            row=dict(item);name=row.pop('primary_name')
            row['embedding']=np.asarray(row['embedding'],np.float32) if row['embedding'] is not None else None
            rows.append((FaceObservation(**row),name))
        output['evidence'].append(rows);output['previews'].append([]);output['preview_sources'].append(({},{}))
    records=[SimpleNamespace(**r) for r in data['records']];handoffs=[]
    if barrier=='no_samples':records=[]
    elif barrier=='handoff':handoffs=[dict(previous_time=88.85543333333334,time=88.8888)]
    elif barrier=='sample_inside':output['segments'][0]=replace(output['segments'][0],start=88.8)
    elif barrier=='invalid_face_inside':
        output['evidence'][0]=[(replace(output['evidence'][1][0][0],time_seconds=88.87,embedding=None,failure='pose_face_missing'),None)]
    result,audit=coalesce_named_output(output,matcher,handoffs=handoffs,frame_records=records)
    assert len(result['segments'])==(1 if barrier is None else 2)
    if barrier is None:
        assert (result['segments'][0].start,result['segments'][0].end)==(88.85543333333334,90.65723333333334)
        assert result['evidence'][0]==output['evidence'][1]
        assert audit['joins'][0]['reason']=='sample_boundary_fragment'
