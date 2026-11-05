from dataclasses import replace
from types import SimpleNamespace
import numpy as np
import pytest
from dance_highlight.services.segment import FrameRec, Segment
from dance_highlight.services.face_cluster import SegmentFaceResult
from dance_highlight.services.face_evidence import FaceObservation
from dance_highlight.services.reference_matcher import ReferenceEmbeddingSample
from dance_highlight.services.config import DanceConfig
from dance_highlight.services.dance_meta import DanceMetaBuilder
from dance_highlight.services.pipeline import DancePipeline


@pytest.mark.parametrize('secondary', [False, True])
@pytest.mark.parametrize('joint_faces', [False, True])
def test_product_pipeline_names_only_main_body_without_supplemental_tracking(tmp_path, monkeypatch, secondary, joint_faces):
    from dance_highlight.services import pipeline as module
    main = np.array([0., 0., 100., 200.]); other = main + [200., 0., 200., 0.]
    head = np.array([[20., 20., .9], [40., 20., .9]])
    records = [FrameRec(float(t), 1, main, False, person_bboxes=[main, other],
                        person_head_keypoints=[head, head + [200., 0., 0.]]) for t in np.arange(.1, 10., .2)]
    main_segment = Segment('main', 1, 0., 10., [(r.t, main, 1) for r in records])
    monkeypatch.setattr(module, 'build_raw_main_segments', lambda _: [main_segment])
    monkeypatch.setattr(module, 'build_raw_group_segments', lambda _: [])
    class Face:
        def batch_segment_embeddings(self, _video, segments, **_):
            for done in range(21):
                _['on_progress'](done, 20)
            results = []
            for seg in segments:
                rows = []
                for t, box, tid in seg.bboxes:
                    vector = np.eye(4)[2 if tid < 0 else (0 if t < 6 else (3 if secondary else 1))]
                    rows.append(FaceObservation(round(t*30),t,tid,tuple(box),tuple(box),
                                                face_bbox=(20.,10.,40.,30.), embedding=vector,
                                                detector_score=.99,association='confirmed'))
                # Regression: the useful pose-owned faces survive even with no legacy average.
                results.append(SegmentFaceResult(seg, [], True, owned_observations=rows))
            return results
        def cluster_embeddings(self, _): return []
    class Render:
        def extract_clip(self, *_args, **_kwargs): raise AssertionError('analysis must retain source ranges')
        def extract_thumbnail(self, _video, path, **_): path.write_bytes(b'preview')
    config = DanceConfig(); pipe = DancePipeline(config, None, Face(), Render(), DanceMetaBuilder(config))
    pipe.analyze_video_to_records = lambda *_a, **_k: (records, 30., 10.)
    pipe._download_reference_images = lambda *_: {}
    def references(_, sample_sink):
        for i, name in enumerate(('A','B','C')):
            sample_sink.append(ReferenceEmbeddingSample(name, name, str(i)*64, 100, 100, np.eye(4)[i]))
        return {}
    pipe._build_reference_embeddings = references
    pipe._video_size = lambda _: (640,480)
    if secondary or joint_faces:
        from dance_highlight.services import secondary_faces
        def recover(_video, _references, primary, _face, **kwargs):
            names = {row.frame_index:'B' for seg, decision, evidence in zip(
                primary['segments'],primary['decisions'],primary['evidence'])
                if decision.reference_id is None for row,_ in evidence
                if seg.start <= row.time_seconds < seg.end}
            joint = {row.frame_index:dict(name='A',status='accepted') for evidence in primary['evidence']
                     for row,_ in evidence if 5.65 < row.time_seconds < 6.15} if joint_faces else {}
            return names, {'version':'test-secondary','matches':[],'joint_matches':joint}
        monkeypatch.setattr(secondary_faces,'recover_secondary_names',recover)
    if joint_faces:
        from dance_highlight.services import context_faces
        monkeypatch.setattr(context_faces,'collect_source_context',lambda *args,**kwargs:([],dict(reason='complete')))
    from dance_highlight.services import mask_tracker
    def forbidden_tracker(*args,**kwargs):
        raise AssertionError('supplemental body tracking is disabled')
    monkeypatch.setattr(mask_tracker,'MaskTracker',forbidden_tracker)
    from dance_highlight.services import scene_context
    preserve_context=scene_context.preserve_main_context
    context_calls=[]
    def checked_final_context(rows,identity,joint,**kwargs):
        names={d.reference_id for d in identity['decisions']}
        assert names=={'A','B'}
        context_calls.append(kwargs['cut_frames'])
        return preserve_context(rows,identity,joint,**kwargs)
    monkeypatch.setattr(scene_context,'preserve_main_context',checked_final_context)
    source = tmp_path/'input.mp4';source.write_bytes(b'source')
    progress = []
    meta = pipe.run(tmp_path, source, 12, progress_cb=lambda p, msg: progress.append((p, msg)))
    assert context_calls==[[]] if joint_faces else context_calls==[None]
    clips = meta['lists']['main']
    # C is repeatedly identifiable beside the main performer. That is not a
    # Dance solo clip: only the selected main body may name a member clip.
    assert set(c['person_id'] for c in clips) == {'a','b'}
    assert len(clips) == 2
    assert np.allclose([(c['start'], c['end']) for c in clips], [(0.,6.),(6.,10.)])
    assert meta['stats']['joint_identity_corrected_seconds']==0.
    assert meta['stats'].get('visible_member_clips_added', 0) == 0
    assert meta['media_mode'] == 'source_ranges'
    assert sum(msg == '얼굴 특징을 추출하고 있습니다' for _, msg in progress) <= 16
    if secondary:
        assert meta['stats']['secondary_reference_recovered_seconds'] == pytest.approx(4.)
