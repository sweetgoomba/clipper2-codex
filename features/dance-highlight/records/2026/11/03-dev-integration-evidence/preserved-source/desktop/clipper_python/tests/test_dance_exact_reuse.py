from pathlib import Path
import cv2
import numpy as np


def test_detector_reuses_only_identical_pixels_and_geometry():
    from dance_highlight.services.face_runtime import CachedFaceDetector
    class Detector:
        calls=0
        def setInputSize(self,size): self.size=size
        def detect(self,image):
            self.calls+=1
            return 1,np.array([[image.sum(),*self.size]],np.float32)
    raw=Detector(); detector=CachedFaceDetector(raw)
    image=np.zeros((2,2,3),np.uint8)
    detector.setInputSize((2,2))
    _,a=detector.detect(image); a[:]=99
    _,b=detector.detect(image)
    np.testing.assert_array_equal(b,[[0,2,2]])
    strided=np.zeros((2,4,3),np.uint8)[:,::2,:]
    assert not strided.flags.c_contiguous
    np.testing.assert_array_equal(detector.detect(strided)[1],b)
    assert raw.calls==1
    image[0,0,0]=1
    _,c=detector.detect(image)
    np.testing.assert_array_equal(c,[[1,2,2]])
    detector.setInputSize((4,4))
    _,d=detector.detect(image)
    np.testing.assert_array_equal(d,[[1,4,4]])
    assert raw.calls==3


def test_detector_input_size_belongs_to_request_thread():
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from dance_highlight.services.face_runtime import CachedFaceDetector
    class Detector:
        def setInputSize(self,size): self.size=size
        def detect(self,image): return 1,np.array(self.size)
    detector=CachedFaceDetector(Detector())
    first_ready,second_ready=Event(),Event()
    def first():
        detector.setInputSize((10,20));first_ready.set()
        assert second_ready.wait(2)
        return detector.detect(np.zeros((2,2,3),np.uint8))[1]
    def second():
        assert first_ready.wait(2)
        detector.setInputSize((30,40));second_ready.set()
        return detector.detect(np.zeros((2,2,3),np.uint8))[1]
    with ThreadPoolExecutor(2) as pool:
        a=pool.submit(first);b=pool.submit(second)
        np.testing.assert_array_equal(a.result(),[10,20])
        np.testing.assert_array_equal(b.result(),[30,40])


def test_mask_cache_requires_complete_identical_temporal_input():
    from dance_highlight.services.mask_frame_cache import SamMasks
    cache=SamMasks(max_bytes=100)
    frames=[1,5,9]
    prompts=dict(bboxes=[[0,0,10,10]],points=[[[2,2]]],labels=[[1]])
    masks=[np.full((8,8),i%2,bool) for i in range(3)]
    cache.put(frames,prompts,masks)
    actual=list(cache.get(frames,prompts))
    assert all(np.array_equal(x,y) for x,y in zip(actual,masks,strict=True))
    actual[0][:]=True
    assert not next(cache.get(frames,prompts)).any()
    assert cache.get(frames[:2],prompts) is None  # num_frames affects SAM memory attention
    assert cache.get(list(reversed(frames)),prompts) is None
    assert cache.get(frames,{**prompts,'labels':[[0]]}) is None
    cache.put([13,17],prompts,[np.ones((32,32),bool)]*2)
    assert cache.retained_bytes<=100


def test_verified_transition_inventory_avoids_decoding_but_keeps_structure(tmp_path):
    from dance_highlight.services.mask_tracker import MaskTracker
    from dance_highlight.services.mask_frame_cache import verified_transitions
    source=tmp_path/'source.mp4'
    inventory=dict(reason='complete',source_path=str(source),fps=30.,through_frame=10,
        cut_frames=[4],camera_transitions=[dict(frame=4,cut=True,color_candidate=True,
                                               structure=dict(continuous=True))])
    tracker=MaskTracker.__new__(MaskTracker)
    tracker.transition_cache=verified_transitions(inventory,source,30.)
    tracker._read=lambda *a: (_ for _ in ()).throw(AssertionError('unexpected decode'))
    assert tracker._cuts(None,1,8)=={4}
    assert tracker.transition_cache[4]['structure']['continuous']
    assert verified_transitions({**inventory,'source_path':str(tmp_path/'other.mp4')},source,30.)=={}
    assert verified_transitions({**inventory,'fps':60.},source,30.)=={}
    assert verified_transitions({**inventory,'reason':'incomplete'},source,30.)=={}
    assert verified_transitions({**inventory,'cut_frames':[4,8]},source,30.)=={}
