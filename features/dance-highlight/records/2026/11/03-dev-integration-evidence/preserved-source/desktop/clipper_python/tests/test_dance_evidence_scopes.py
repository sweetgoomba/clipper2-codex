from types import SimpleNamespace
import json

import numpy as np
import pytest

from dance_highlight.services import segment
from dance_highlight.services.segment import FrameRec, Segment
from dance_highlight.services.config import DanceConfig
from dance_highlight.services.face_cluster import SegmentFaceResult
from dance_highlight.services.face_evidence import FaceObservation
from dance_highlight.services.reference_matcher import ReferenceEmbeddingSample
from dance_highlight.services.pipeline import DancePipeline
from dance_highlight.services.dance_meta import DanceMetaBuilder


def test_evidence_scopes_keep_short_body_changes_and_real_gaps_without_mutation():
    box = np.array([0., 0., 100., 200.])
    raw = [Segment('main', tid, start, end, [(start, box, tid)])
           for tid,start,end in [(1,0.,2.), (2,2.,2.4), (1,2.4,6.), (1,6.2,8.)]]
    scopes = segment.build_main_evidence_scopes(raw)
    assert [(s.start,s.end) for s in scopes] == [(0.,6.),(6.2,8.)]
    assert [row[2] for row in scopes[0].bboxes] == [1,2,1]
    assert all(s.label is None for s in scopes)
    assert [(s.start,s.end,len(s.bboxes)) for s in raw] == [(0.,2.,1),(2.,2.4,1),(2.4,6.,1),(6.2,8.,1)]


def _run(tmp_path, *, group=False, faces=True, wide=False, face_window=None, name_switch=None):
    body = np.array([0.,0.,100.,200.])
    records = [FrameRec(float(t),1,body,group) for t in np.linspace(20.,24.,41)]
    if wide:
        for rec in records:
            rec.person_bboxes = ([np.array(b, dtype=float) for b in
                [[20,250,60,350],[240,250,280,350],[490,250,530,350]]]
                if 21 <= rec.t < 23 else [body])
            rec.main_bbox = rec.person_bboxes[0]
    def has_face(t):
        return faces and (face_window is None or face_window[0]-1e-8 <= t <= face_window[1]+1e-8)
    class Face:
        def batch_segment_embeddings(self, _video, segments, **_):
            assert _['sample_all_main_frames'] is True
            return [SegmentFaceResult(seg, [], False, owned_observations=[
                FaceObservation(round(t*10),t,tid,tuple(box),tuple(box),
                    face_bbox=(20.,10.,40.,30.) if has_face(t) else None,
                    embedding=np.array([0.,1.] if name_switch is not None and t >= name_switch else [1.,0.]) if has_face(t) else None,
                    detector_score=.99 if has_face(t) else 0.,
                    association='confirmed' if has_face(t) else 'unassigned',
                    failure=None if has_face(t) else 'no_detection') for t,box,tid in seg.bboxes],
                owned_previews={round(t*10): str(t).encode() for t,_,_ in seg.bboxes if has_face(t)}) for seg in segments]
        def cluster_embeddings(self, _): return []
    class Render:
        def extract_thumbnail(self, _video,path,**_): path.write_bytes(b'thumbnail')
    config = DanceConfig()
    pipe = DancePipeline(config,None,Face(),Render(),DanceMetaBuilder(config))
    pipe.analyze_video_to_records = lambda *_a,**_k:(records,10.,25.)
    pipe._download_reference_images = lambda *_:{}
    def refs(_,*,sample_sink):
        sample_sink.append(ReferenceEmbeddingSample('A','a','a'*64,100,100,np.array([1.,0.])))
        if name_switch is not None:
            sample_sink.append(ReferenceEmbeddingSample('B','b','b'*64,100,100,np.array([0.,1.])))
        return {}
    pipe._build_reference_embeddings = refs
    pipe._video_size = lambda _:(640,480)
    source=tmp_path/'source.mp4';source.write_bytes(b'source')
    return pipe.run(tmp_path,source,1)


def test_named_main_is_not_discarded_before_face_analysis_due_to_group_overlap(tmp_path):
    meta = _run(tmp_path,group=True)
    assert [(c['start'],c['end'],c['person_id']) for c in meta['lists']['main']] == [(20.,24.,'a')]
    assert meta['lists']['group'] == []
    assert meta['stats']['smoothed_group_segments'] == 1
    raw_groups = [c for c in meta['diagnostics']['clips'] if c['seg_type'] == 'group']
    assert [(c['start'], c['end']) for c in raw_groups] == [(20.,24.)]
    assert meta['diagnostics']['clips'][0]['group_overlap_ratio'] == 1.
    assert meta['diagnostics']['group_output_projection']['classification_changed'] is False


def test_group_overlapping_only_unknown_is_preserved_in_outputs_and_diagnostics(tmp_path):
    meta = _run(tmp_path, group=True, faces=False)
    assert [(c['start'],c['end'],c['person_id']) for c in meta['lists']['main']] == [(20.,24.,'unknown')]
    assert [(c['start'],c['end']) for c in meta['lists']['group']] == [(20.,24.)]
    assert not meta['diagnostics']['group_output_projection']['suppressed']


def test_registered_main_without_detected_face_stays_visible_as_unknown(tmp_path):
    meta = _run(tmp_path,faces=False)
    assert [(c['start'],c['end'],c['person_id']) for c in meta['lists']['main']] == [(20.,24.,'unknown')]
    assert meta['stats']['dropped_main_no_face'] == 0
    assert meta['diagnostics']['rejections'] == []
    assert meta['diagnostics']['unresolved_main_scopes'] == [
        {'start':20.,'end':24.,'reason':'no_face_samples'}]


def test_registered_pipeline_keeps_wide_ensemble_only_as_group_even_if_faces_match(tmp_path):
    meta = _run(tmp_path, wide=True)
    assert [(c['start'], c['end'], c['person_id']) for c in meta['lists']['main']] == [
        (20.,21.,'a'), (23.,24.,'a')]
    assert [(c['start'],c['end']) for c in meta['lists']['group']] == [(21.,23.)]
    assert meta['stats']['scene_group_seconds'] == 2.
    assert all(not c.get('person_ids') for c in meta['lists']['group'])
    evidence = json.loads((tmp_path/'diagnostics/face_evidence.json').read_text())
    reviewed = next(r for r in evidence['pose_heads'] if r['time_seconds'] == 21.)
    assert reviewed['scene_kind'] == 'group'
    assert reviewed['candidate_main_id'] == 1
    assert reviewed['candidate_main_bbox'] == [20.,250.,60.,350.]


def test_scene_output_boundary_keeps_repeated_identity_support_from_group_context(tmp_path):
    # Only two pose samples fall after group ends. Their .1s span is too short
    # alone; repeated same-body observations just before the scene boundary
    # provide the existing .15s face support. They must not create group solos.
    meta = _run(tmp_path, wide=True, face_window=(22.7, 23.1))
    clips = meta['lists']['main']
    assert any(c['person_id'] == 'a' and c['start'] == 23. and c['end'] > 23.1 for c in clips)
    assert all(c['end'] <= 21. or c['start'] >= 23. for c in clips)
    assert all(not c.get('person_ids') for c in meta['lists']['group'])
    evidence = json.loads((tmp_path/'diagnostics/face_evidence.json').read_text())
    times = [o['time_seconds'] for s in evidence['segments'] for o in s['owned_observations']
             if o['embedding'] is not None]
    assert any(22.7 <= t < 23. for t in times)


def test_member_change_near_scene_edge_keeps_two_sided_identity_support(tmp_path):
    meta = _run(tmp_path, wide=True, name_switch=23.2)
    clips = [c for c in meta['lists']['main'] if c['start'] >= 23.]
    assert [c['person_id'] for c in clips] == ['a', 'b']
    assert np.allclose([(c['start'], c['end']) for c in clips], [(23., 23.15), (23.15, 24.)])


def test_scene_projection_preserves_continuous_member_and_exact_partial_boundaries():
    box = np.array([0., 0., 100., 200.])
    named = [Segment('main', 7, 0., 6., [(float(t), box, 7) for t in range(7)])]
    eligible = [Segment('main', None, a, b, []) for a, b in [(0., 1.), (1., 2.), (3.25, 6.)]]
    parts = segment.intersect_main_segments(named, eligible)
    assert [(index, s.start, s.end) for index, s in parts] == [(0, 0., 2.), (0, 3.25, 6.)]
    assert [r[0] for r in parts[1][1].bboxes] == [4., 5.]
    assert named[0].end == 6. and len(named[0].bboxes) == 7
    whole = segment.intersect_main_segments(named, [Segment('main', None, 0., 6., [])])
    assert [(s.start, s.end) for _, s in whole] == [(0., 6.)]
    assert segment.intersect_main_segments(named, []) == []


def test_scene_projection_queries_and_recovery_metrics_describe_visible_main_only(tmp_path):
    meta = _run(tmp_path, wide=True)
    after = next(c for c in meta['diagnostics']['clips'] if c['seg_type']=='main' and c['start']==23.)
    assert after['query_images']
    assert all(23. <= float((tmp_path/p).read_bytes()) < 24. for p in after['query_images'])
    assert meta['stats']['identity_recovered_seconds'] == pytest.approx(2.)


def test_pipeline_aligns_scene_output_without_retiming_identity_observations(tmp_path, monkeypatch):
    from dataclasses import replace
    from dance_highlight.services import scene_boundaries
    calls=[]
    def align(rows, main, groups, **kwargs):
        calls.append(kwargs)
        edges={21.:20.95,23.:22.95}
        def shift(parts):
            return [replace(s,start=edges.get(s.start,s.start),end=edges.get(s.end,s.end)) for s in parts]
        return shift(main),shift(groups),dict(version='scene_cut_alignment_v1',reason='complete',scene_group_seconds=2.,changes=[dict(observed_time=21.,cut_time=20.95)])
    monkeypatch.setattr(scene_boundaries,'align_scene_segments_from_source',align)
    meta=_run(tmp_path,wide=True)
    assert len(calls)==1 and calls[0]['cut_frames'] is None
    assert [(c['start'],c['end'],c['person_id']) for c in meta['lists']['main']]==[(20.,20.95,'a'),(22.95,24.,'a')]
    assert [(c['start'],c['end']) for c in meta['lists']['group']]==[(20.95,22.95)]
    assert meta['stats']['scene_boundary_policy']=='scene_cut_alignment_v1'
    evidence=json.loads((tmp_path/'diagnostics/face_evidence.json').read_text())
    assert evidence['scene_boundary_refinement']['changes'][0]['cut_time']==20.95
    observations=[o['time_seconds'] for s in evidence['segments'] for o in s['owned_observations']]
    assert 21. in observations and 23. in observations
    assert 20.95 not in observations and 22.95 not in observations
