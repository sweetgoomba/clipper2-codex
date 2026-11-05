"""Source coordinates, pixels and transition evidence survive decode reuse."""
import cv2
import numpy as np
import pytest


def test_overlapping_source_windows_decode_once_with_bounded_storage(tmp_path):
    from dance_highlight.services.source_reader import SourceFrameReader
    source=tmp_path/'source.avi'
    writer=cv2.VideoWriter(str(source),cv2.VideoWriter_fourcc(*'MJPG'),30.,(48,32))
    for i in range(25):writer.write(np.full((32,48,3),i*8,np.uint8))
    writer.release()
    cap=cv2.VideoCapture(str(source));expected=[]
    for _ in range(25):expected.append(cap.read()[1])
    cap.release()
    reader=SourceFrameReader(source,30.,max_bytes=48*32*3*4)
    try:
        for f in [5,6,5,6,7,8,9,8,7,6,23,24]:
            np.testing.assert_array_equal(reader.get(f),expected[f])
            assert reader.retained_bytes<=48*32*3*4
        assert reader.stats['cache_hits']>=5
        assert reader.stats['seeks']==1  # Initial short gap is decoded forward.
        assert reader.stats['reads']<15
    finally:reader.close()
    assert not reader.cap.isOpened()


def test_source_reuse_rejects_fps_mismatch_and_missing_frame(tmp_path):
    from dance_highlight.services.source_reader import SourceFrameReader
    source=tmp_path/'source.avi';w=cv2.VideoWriter(str(source),cv2.VideoWriter_fourcc(*'MJPG'),30.,(48,32))
    w.write(np.zeros((32,48,3),np.uint8));w.release()
    with pytest.raises(ValueError,match='fps'):SourceFrameReader(source,60.)
    with SourceFrameReader(source,30.) as reader:
        with pytest.raises(ValueError,match='unavailable'):reader.get(1)


def test_cached_gallery_keeps_shared_match_fingerprints_and_payload(monkeypatch):
    from dataclasses import asdict
    from dance_highlight.services.face_recovery import ReferenceObservationMatcher
    from dance_highlight.services.reference_matcher import ReferenceEmbeddingSample
    from dance_highlight.services.face_evidence import FaceObservation
    from dance_highlight.services.segment import Segment
    from clipper_face_core.contracts import fingerprint
    matcher=ReferenceObservationMatcher(references=[ReferenceEmbeddingSample('A','a','a'*64,10,10,np.array([1.,0.])),ReferenceEmbeddingSample('B','b','b'*64,10,10,np.array([0.,1.]))],analysis_id='test',video_sha256='a'*64,detector_sha256='b'*64,recognizer_sha256='c'*64,config_sha256='d'*64,backend_version='test',video_size=(100,100),max_distance=.6)
    original=fingerprint(matcher.gallery)
    import clipper_face_core.contracts as contracts
    calls=[]
    frozen=matcher.gallery
    def counted(value):
        if value is frozen:calls.append(value)
        return fingerprint(value)
    monkeypatch.setattr(contracts,'fingerprint',counted)
    # A plain immutable gallery remains the shared core's behavior reference.
    from clipper_face_core.contracts import ReferenceGallery
    raw=ReferenceGallery(matcher.gallery.space,matcher.gallery.entries,matcher.gallery.samples,matcher.gallery.failures,matcher.gallery.aggregation_version)
    row=FaceObservation(1,.1,1,(0,0,50,80),(0,0,50,80),face_bbox=(10,10,30,30),embedding=np.array([1.,0.]),association='confirmed')
    seg=Segment('main',1,0.,1.,[])
    fast=asdict(matcher.match(row,seg,'scope'))
    gallery=matcher.gallery;matcher.gallery=raw
    assert asdict(matcher.match(row,seg,'scope'))==fast
    assert gallery.fingerprint==original
    matcher.gallery=gallery
    for _ in range(4):assert asdict(matcher.match(row,seg,'scope'))==fast
    assert len(calls)==1  # Querying again must not serialize every reference photo again.
