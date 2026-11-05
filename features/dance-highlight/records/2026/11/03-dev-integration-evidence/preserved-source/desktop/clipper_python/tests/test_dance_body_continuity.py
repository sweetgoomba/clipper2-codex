"""Source-video checks for a face gap inside one continuous main part."""
from dataclasses import replace
import cv2
import numpy as np
import pytest

from dance_highlight.services.face_evidence import FaceObservation
from dance_highlight.services.reference_matcher import SegmentReferenceDecision
from dance_highlight.services.segment import FrameRec, Segment


def example(tmp_path, *, cut=False, overlap=False, conflict=False):
    path = tmp_path/'body.avi'
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*'MJPG'), 20., (160, 100))
    assert writer.isOpened()
    main = np.array([30., 10., 70., 90.])
    other = main.copy() if overlap else main + [80., 0., 80., 0.]
    for frame in range(120):
        image = np.full((100, 160, 3), (20, 40, 20), np.uint8)
        if cut and frame >= 50:
            image[:] = (200, 180, 20)
        cv2.rectangle(image, (30, 10), (70, 90), (30, 50, 200), -1)
        cv2.rectangle(image, (110, 10), (150, 90), (200, 40, 40), -1)
        writer.write(image)
    writer.release()
    rows = []
    records = []
    for frame in range(0, 120, 4):
        t = frame/20.
        named = t < 2. or t >= 4.
        row = FaceObservation(frame, t, 1 if t < 3 else 8, tuple(main), tuple(main),
                              face_bbox=(40., 12., 55., 28.) if named else None,
                              embedding=np.array([1., 0.]) if named else None,
                              detector_score=.99 if named else 0.,
                              association='confirmed' if named else 'unassigned',
                              failure=None if named else 'no_detection')
        rows.append((row, 'A' if named else None))
        records.append(FrameRec(t, row.track_id, main, False, person_bboxes=[main, other]))
    if conflict:
        row, _ = rows[13]
        rows[13] = (replace(row, embedding=np.array([0., 1.]), detector_score=.99,
                            association='confirmed', failure=None), 'B')
    segments = [Segment('main', i, start, end,
                        [(o.time_seconds, main, o.track_id) for o,_ in rows if start <= o.time_seconds < end])
                for i,(start,end) in enumerate(((0.,2.),(2.,4.),(4.,6.)))]
    output = dict(segments=segments,
                  decisions=[SegmentReferenceDecision(name, 'matched' if name else 'unmatched', 'test')
                             for name in ('A',None,'A')],
                  labels=[1,None,2], previews=[[b'left'],[],[b'right']],
                  evidence=[[(o,n) for o,n in rows if s.start <= o.time_seconds < s.end] for s in segments],
                  preview_sources=[({}, {}) for _ in segments], accurate_indices=[0,1,2],
                  anchors=[], audit=[], fallback_names={})
    return path, output, records


def test_body_continuity_keeps_six_second_part_through_face_gap_and_track_id_change(tmp_path):
    from dance_highlight.services.body_continuity import bridge_main_face_gaps
    path, original, records = example(tmp_path)
    result, audit = bridge_main_face_gaps(original, records, path)
    assert [(s.start,s.end) for s in result['segments']] == [(0.,6.)]
    assert [d.reference_id for d in result['decisions']] == ['A']
    assert audit['recovered_seconds'] == pytest.approx(2.)
    assert audit['bridges'][0]['seed_frames'] == [36,80]
    assert len(original['segments']) == 3
    # Body continuity does not manufacture face matches or new gallery anchors.
    assert result['anchors'] == []
    assert result['fallback_names'] == {}
    assert all(name is None for row,name in result['evidence'][0] if 2. <= row.time_seconds < 4.)


@pytest.mark.parametrize('case',['same_pose','competing_pose','handoff','missing_pose'])
def test_observed_unique_pose_can_bridge_color_change_but_never_ambiguity(tmp_path,case):
    from dance_highlight.services.body_continuity import bridge_main_face_gaps
    path,original,records=example(tmp_path)
    writer=cv2.VideoWriter(str(path),cv2.VideoWriter_fourcc(*'MJPG'),20.,(160,100))
    assert writer.isOpened()
    for frame in range(120):
        image=np.full((100,160,3),(20,40,20),np.uint8)
        # Similar luminance, different hue: clothing/light appearance alone
        # rejects this pair although the observed head and torso never move.
        color=(180,40,120) if 44<=frame<72 else (20,40,180)
        cv2.rectangle(image,(30,10),(70,90),color,-1)
        cv2.rectangle(image,(110,10),(150,90),(200,40,40),-1)
        writer.write(image)
    writer.release()
    pose=np.zeros((17,3),np.float32)
    for i,(x,y) in {0:(50,20),1:(46,18),2:(54,18),3:(42,20),4:(58,20),
                   5:(40,35),6:(60,35),11:(43,60),12:(57,60)}.items():pose[i]=[x,y,.99]
    for r in records:
        other=pose.copy();other[:,0]+=80
        r.person_pose_keypoints=[pose.copy(),other]
        if case=='competing_pose':r.person_pose_keypoints[1]=pose.copy()
        if case=='handoff' and r.t>=2.2:r.person_pose_keypoints.reverse()
        if case=='missing_pose' and r.t==2.2:r.person_pose_keypoints=[]
    result,audit=bridge_main_face_gaps(original,records,path)
    if case=='same_pose':
        assert [(s.start,s.end,d.reference_id) for s,d in zip(result['segments'],result['decisions'])]==[(0.,6.,'A')]
        assert audit['bridges'][0]['pose_link_frames']
        assert result['anchors']==original['anchors']==[]
        assert result['fallback_names']=={}
    else:
        assert result is original
        assert audit['recovered_seconds']==0.


@pytest.mark.parametrize('reverse', [False, True])
@pytest.mark.parametrize('nearby', [False, True])
def test_pose_bridge_keeps_partly_observed_competing_body_in_uniqueness_check(reverse, nearby):
    from dance_highlight.services.body_continuity import _unique_pose_link
    pose = np.zeros((17,3),np.float32)
    for i,(x,y) in {0:(50,20),1:(46,18),2:(54,18),3:(42,20),4:(58,20),
                   5:(40,35),6:(60,35),11:(43,60),12:(57,60)}.items():
        pose[i] = [x,y,.99]
    box = np.array([30.,10.,70.,90.])
    shift = 10. if nearby else 80.
    competitor = pose.copy(); competitor[:,0] += shift
    competitor[[11,12],2] = .1  # Occlusion must not remove a competing person.
    before = FrameRec(0.,1,box,False,person_bboxes=[box,box+[shift,0,shift,0]],
                      person_pose_keypoints=[pose,competitor])
    after = FrameRec(.1,1,box+[5,0,5,0],False,
                    person_bboxes=[box+[5,0,5,0]],
                    person_pose_keypoints=[pose+[5,0,0]])
    args = (after,before) if reverse else (before,after)
    assert _unique_pose_link(*args,0,0) is (not nearby)


@pytest.mark.parametrize('condition', ['cut','overlap','conflict','different_name','missing_pose','missing_source'])
def test_body_continuity_cannot_cross_unverified_identity_or_source_gap(tmp_path, condition):
    from dance_highlight.services.body_continuity import bridge_main_face_gaps
    path, original, records = example(tmp_path, **{condition:True} if condition in ('cut','overlap','conflict') else {})
    if condition == 'different_name':
        original['decisions'][-1] = SegmentReferenceDecision('B','matched','test')
    if condition == 'missing_pose':
        records = [r for r in records if r.t != 3.]
    if condition == 'missing_source':
        path = tmp_path/'missing.avi'
    result, audit = bridge_main_face_gaps(original, records, path)
    assert result['segments'] == original['segments']
    assert [d.reference_id for d in result['decisions']] == [d.reference_id for d in original['decisions']]
    assert audit['recovered_seconds'] == 0.


def test_body_bridge_vetoes_repeated_other_face_even_without_its_name(tmp_path):
    from dance_highlight.services.body_continuity import bridge_main_face_gaps
    path, output, records = example(tmp_path)
    output['evidence'][1] = [(replace(row, embedding=np.array([0.,1.]),
                                    detector_score=.99, association='confirmed', failure=None), None)
                             for row,_ in output['evidence'][1]]
    result, audit = bridge_main_face_gaps(output, records, path)
    assert result is output
    assert audit['candidates'][0]['reason'] == 'conflicting_face_evidence'


@pytest.mark.parametrize('reverse', [False,True])
def test_body_link_requires_unique_correspondence_in_both_directions(reverse):
    from dance_highlight.services.body_continuity import _unique_body_link
    view = np.ones(160,dtype=np.float32)/np.sqrt(160)
    previous = ([np.array([0.,0.,40.,80.]), np.array([30.,0.,70.,80.])],[view,view],0)
    current = ([np.array([15.,0.,55.,80.]), np.array([100.,0.,140.,80.])],[view,view],0)
    assert not _unique_body_link(*(current,previous) if reverse else (previous,current))


def test_body_bridge_does_not_name_an_unbounded_gap(tmp_path):
    from dance_highlight.services.body_continuity import bridge_main_face_gaps
    path, output, records = example(tmp_path)
    output['decisions'][0] = SegmentReferenceDecision(None,'unmatched','test')
    result, audit = bridge_main_face_gaps(output, records, path)
    assert result is output
    assert audit['bridges'] == []


@pytest.mark.parametrize('seek_result', [False,True])
def test_failed_or_inaccurate_seek_cannot_validate_the_wrong_source_frames(tmp_path, monkeypatch, seek_result):
    from dance_highlight.services import body_continuity
    path, output, records = example(tmp_path, cut=True)
    capture = cv2.VideoCapture
    class WrongPosition:
        def __init__(self, path): self.actual = capture(path)
        def set(self, *args): return seek_result  # Cursor remains at source frame 0.
        def get(self, prop): return self.actual.get(prop)
        def read(self): return self.actual.read()
        def isOpened(self): return self.actual.isOpened()
        def release(self): self.actual.release()
    monkeypatch.setattr(body_continuity.cv2,'VideoCapture',WrongPosition)
    result, audit = body_continuity.bridge_main_face_gaps(output, records, path)
    assert result is output
    assert audit['recovered_seconds'] == 0.


def test_registered_product_pipeline_emits_one_continuous_part_with_body_audit(tmp_path, monkeypatch):
    import json
    from dance_highlight.services import pipeline
    from dance_highlight.services.config import DanceConfig
    from dance_highlight.services.dance_meta import DanceMetaBuilder
    from dance_highlight.services.face_cluster import SegmentFaceResult
    from dance_highlight.services.reference_matcher import ReferenceEmbeddingSample
    source, original, records = example(tmp_path)
    rows = [o for evidence in original['evidence'] for o,_ in evidence]
    scope = Segment('main',1,0.,6.,[(o.time_seconds,np.array(o.body_bbox),o.track_id) for o in rows])
    monkeypatch.setattr(pipeline,'build_raw_main_segments',lambda _: [scope])
    monkeypatch.setattr(pipeline,'build_raw_group_segments',lambda _: [])
    class Face:
        def batch_segment_embeddings(self, _video, segments, **kwargs):
            return [SegmentFaceResult(seg,[],True,owned_observations=rows) for seg in segments]
        def cluster_embeddings(self, _): return []
    class Render:
        def extract_clip(self, *args, **kwargs): raise AssertionError('source ranges only')
        def extract_thumbnail(self, _video, path, **kwargs): path.write_bytes(b'preview')
    config = DanceConfig()
    pipe = pipeline.DancePipeline(config,None,Face(),Render(),DanceMetaBuilder(config))
    pipe.analyze_video_to_records = lambda *args,**kwargs: (records,20.,6.)
    pipe._download_reference_images = lambda *args: {}
    def references(_paths, sample_sink):
        for i,name in enumerate(('A','B')):
            sample_sink.append(ReferenceEmbeddingSample(name,name,str(i)*64,100,100,np.eye(2)[i]))
        return {}
    pipe._build_reference_embeddings = references
    project = tmp_path/'project'
    meta = pipe.run(project,source,42)
    assert [(c['person_id'],c['start'],c['end']) for c in meta['lists']['main']] == [('a',0.,6.)]
    assert meta['stats']['body_continuity_recovered_seconds'] == pytest.approx(2.)
    evidence = json.loads((project/'diagnostics/face_evidence.json').read_text())
    assert evidence['body_continuity_refinement']['bridges'][0]['name'] == 'A'
    assert 'body_continuity' in evidence['runtime']['modules']


@pytest.mark.parametrize('second_conflict', [False,True])
def test_multiple_bridges_share_only_original_named_support(tmp_path, second_conflict):
    from dance_highlight.services.body_continuity import bridge_main_face_gaps
    path, output, records = example(tmp_path)
    rows = [o for evidence in output['evidence'] for o,_ in evidence]
    ranges = [(0.,1.2,'A'),(1.2,1.8,None),(1.8,3.,'A'),(3.,3.6,None),(3.6,6.,'A')]
    output['segments'] = []
    output['evidence'] = []
    for i,(start,end,name) in enumerate(ranges):
        local = [o for o in rows if start <= o.time_seconds < end]
        output['segments'].append(Segment('main',i,start,end,[(o.time_seconds,np.array(o.body_bbox),o.track_id) for o in local]))
        evidence = []
        for row in local:
            alien = second_conflict and i == 3
            evidence.append((replace(row,embedding=np.array([0.,1.] if alien else [1.,0.]) if name or alien else None,
                                     detector_score=.99 if name or alien else 0.,
                                     association='confirmed' if name or alien else 'unassigned',
                                     failure=None if name or alien else 'no_detection'),name))
        output['evidence'].append(evidence)
    output['decisions'] = [SegmentReferenceDecision(n,'matched' if n else 'unmatched','test') for _,_,n in ranges]
    output.update(labels=[1,None,2,None,3],previews=[[] for _ in ranges],
                  preview_sources=[({}, {}) for _ in ranges],accurate_indices=list(range(5)))
    result, audit = bridge_main_face_gaps(output,records,path)
    expected = [(0.,3.),(3.,3.6),(3.6,6.)] if second_conflict else [(0.,6.)]
    assert [(s.start,s.end) for s in result['segments']] == expected
    assert len(audit['bridges']) == (1 if second_conflict else 2)
    assert result['fallback_names'] == {}
