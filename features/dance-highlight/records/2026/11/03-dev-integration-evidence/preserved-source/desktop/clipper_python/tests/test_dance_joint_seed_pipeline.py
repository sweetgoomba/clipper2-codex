import pytest
from test_dance_mask_continuity import recovery_example

@pytest.mark.parametrize('cut_inventory_available',[False,True])
@pytest.mark.parametrize('inside_unknown',[False,True])
def test_pipeline_keeps_joint_faces_without_running_supplemental_mask_recovery(tmp_path,monkeypatch,cut_inventory_available,inside_unknown):
    import json
    import numpy as np
    from dance_highlight.services import pipeline, member_timeline, secondary_faces, body_continuity, mask_tracker, context_faces
    from dance_highlight.services.config import DanceConfig
    from dance_highlight.services.dance_meta import DanceMetaBuilder
    from dance_highlight.services.face_cluster import SegmentFaceResult
    from dance_highlight.services.reference_matcher import ReferenceEmbeddingSample
    original,records,anchors = recovery_example()
    if inside_unknown:
        anchors = [dict(name='A', frame_index=i, time_seconds=i/10.) for i in (22,25)]
    rows = [r for evidence in original['evidence'] for r,_ in evidence]
    monkeypatch.setattr(pipeline,'build_raw_main_segments',lambda _: original['segments'])
    monkeypatch.setattr(pipeline,'build_raw_group_segments',lambda _: [])
    monkeypatch.setattr(member_timeline,'refine_member_timeline',lambda *a,**k: original)
    monkeypatch.setattr(secondary_faces,'recover_secondary_names',lambda *a,**k: ({},{'video_anchors':[], 'joint_matches':{a['frame_index']:dict(name=a['name'],status='accepted',reason='joint_video_match') for a in anchors}}))
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
    joint = audit['secondary_reference_refinement']['identity_revalidation']
    assert joint['reason'] == 'disabled_runtime_cost'
    assert 'model' not in joint
    assert meta['diagnostics']['performance']['stage_seconds']['joint_identity'] == 0.
    assert meta['diagnostics']['performance']['stage_seconds']['mask_continuity'] == 0.
    assert {'mask_continuity','mask_tracker'} <= audit['runtime']['modules'].keys()
