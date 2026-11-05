from dataclasses import asdict
from threading import Event, get_ident
from types import SimpleNamespace
import weakref

import cv2
import numpy as np
import pytest

from dance_highlight.services.face_cluster import FaceClusterService
from dance_highlight.services.face_runtime import CachedFaceDetector
from dance_highlight.services.segment import FrameRec, Segment


class Capture:
    def __init__(self, count):
        self.count, self.index = count, 0
        self.frames = []
        self.peak_frames = 0
        self.released = False

    def isOpened(self):
        return True

    def get(self, _prop):
        return 1.

    def read(self):
        if self.index >= self.count:
            return False, None
        frame = np.full((24, 24, 3), self.index, np.uint8)
        self.index += 1
        self.frames.append(weakref.ref(frame))
        self.peak_frames = max(self.peak_frames, sum(ref() is not None for ref in self.frames))
        return True, frame

    def grab(self):
        self.index += 1
        return self.index <= self.count

    def release(self):
        self.released = True


class Detector:
    def setInputSize(self, size):
        self.size = size

    def detect(self, image):
        assert self.size == (image.shape[1], image.shape[0])
        return 1, np.array([[1, 1, 8, 8, 2, 2, 6, 2, 4, 4, 2, 6, 6, 6, .99]], np.float32)


class Recognizer:
    def alignCrop(self, image, _face):
        return image

    def feature(self, image):
        return np.array([[1., image[0, 0, 0]]], np.float32)


def run_batch(monkeypatch, *, count=4, detector=None, recognizer=None, registered=True,
              capture=None, progress=None, rows=None):
    service = FaceClusterService.__new__(FaceClusterService)
    service.config = SimpleNamespace(
        face_sample_frames=2, face_candidate_sample_frames=20,
        face_min_det_score=.28, face_roi_expand_w=0.,
        face_roi_expand_h_top=0., face_roi_expand_h_bottom=0.,
    )
    service._detector = detector or CachedFaceDetector(Detector())
    service._recognizer = recognizer or Recognizer()
    capture = capture or Capture(count)
    monkeypatch.setattr('dance_highlight.services.face_cluster.cv2.VideoCapture', lambda _: capture)
    body = np.array([0., 0., 20., 20.])
    rows = [(float(i), body, 7) for i in range(count)] if rows is None else rows
    records = [FrameRec(t, tid, box, False, person_bboxes=[box],
                       person_head_keypoints=[np.array([[2., 2., .9], [6., 2., .9]])])
               for t, box, tid in rows]
    result = service.batch_segment_embeddings(
        'fake.mp4', [Segment('main', 7, 0., float(count), rows)],
        frame_records=records, sample_all_main_frames=registered, on_progress=progress,
    )[0]
    return result, capture


def test_registered_prefetch_overlaps_next_detection_with_main_thread_embedding(monkeypatch):
    # A serial loop (or prefetch submitted after embedding) cannot satisfy this handshake.
    embedding_started, next_detection = Event(), Event()
    caller = get_ident()
    overlapped = []
    progress_threads = []

    class OverlapDetector(Detector):
        def detect(self, image):
            if int(image[0, 0, 0]) == 1:
                assert embedding_started.wait(2.)
                next_detection.set()
            return super().detect(image)

    class OverlapRecognizer(Recognizer):
        def feature(self, image):
            assert get_ident() == caller
            if int(image[0, 0, 0]) == 0:
                embedding_started.set()
                overlapped.append(next_detection.wait(.5))
            return super().feature(image)

    result, capture = run_batch(
        monkeypatch, detector=CachedFaceDetector(OverlapDetector()), recognizer=OverlapRecognizer(),
        progress=lambda done, total: progress_threads.append((get_ident(), done, total)),
    )

    assert overlapped == [True]
    assert [o.frame_index for o in result.owned_observations] == [0, 1, 2, 3]
    assert progress_threads == [(caller, i, 4) for i in range(1, 5)]
    assert capture.peak_frames <= 2
    assert capture.released


def fingerprint(result):
    def serial(value):
        if isinstance(value, np.ndarray):
            return (value.dtype.str, value.shape, value.tobytes())
        if isinstance(value, dict):
            return {key: serial(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [serial(item) for item in value]
        return value
    return serial({
        'embeddings': result.track_embeddings, 'tracks': result.track_ids,
        'observations': [asdict(o) for o in result.observations],
        'owned': [asdict(o) for o in result.owned_observations],
        'previews': result.owned_previews, 'thumbnails': dict(result.owned_thumbnails),
        'evidence': result.track_evidence_images,
        'track_thumbnails': result.track_thumbnail_images,
    })


def test_prefetch_preserves_evidence_retries_and_unreadable_frames(monkeypatch):
    # Caching a detection error permanently would drop the second, pose-owned attempt.
    class FailingDetector(Detector):
        def __init__(self):
            self.failed = False

        def detect(self, image):
            frame = int(image[0, 0, 0])
            if frame == 0 and not self.failed:
                self.failed = True
                raise cv2.error('first attempt fails')
            if frame == 2:
                return 1, None
            return super().detect(image)

    body = np.array([0., 0., 20., 20.])
    rows = [(float(i), body, 7) for i in (0, 2, 3, 5)]
    serial, _ = run_batch(monkeypatch, count=6, rows=rows, capture=Capture(4),
                          detector=CachedFaceDetector(FailingDetector()), registered=False)
    prefetched, capture = run_batch(monkeypatch, count=6, rows=rows, capture=Capture(4),
                                    detector=CachedFaceDetector(FailingDetector()))

    assert fingerprint(prefetched) == fingerprint(serial)
    assert [o.failure for o in prefetched.observations] == [
        'detection_failed', 'no_detection', None, 'frame_unreadable']
    assert [o.failure for o in prefetched.owned_observations] == [
        None, 'pose_face_missing', None, 'frame_unreadable']
    assert capture.peak_frames <= 2
    assert capture.released


def test_prefetch_releases_capture_when_progress_callback_fails(monkeypatch):
    capture = Capture(20)

    def fail(_done, _total):
        raise RuntimeError('cancelled')

    with pytest.raises(RuntimeError, match='cancelled'):
        run_batch(monkeypatch, count=20, capture=capture, progress=fail)

    assert capture.released
    assert capture.index <= 2
    assert not any(ref() is not None for ref in capture.frames)


@pytest.mark.parametrize('registered', [False, True])
def test_unwrapped_detector_keeps_all_inference_on_caller_thread(monkeypatch, registered):
    # The unwrapped OpenCV detector and caller-provided adapters may have mutable state.
    caller = get_ident()

    class CallerDetector(Detector):
        def setInputSize(self, size):
            assert get_ident() == caller
            super().setInputSize(size)

        def detect(self, image):
            assert get_ident() == caller
            return super().detect(image)

    result, capture = run_batch(monkeypatch, detector=CallerDetector(), registered=registered)

    assert [o.frame_index for o in result.owned_observations] == [0, 1, 2, 3]
    assert capture.released


def test_prefetch_keeps_multiple_same_frame_tasks_in_order_with_two_frame_memory_bound(monkeypatch):
    # Unbounded submission can preserve result order while retaining every decoded frame.
    body = np.array([0., 0., 20., 20.])
    rows = [(float(i), body, tid) for i in range(80) for tid in (7, 9)]
    result, capture = run_batch(monkeypatch, count=80, rows=rows)

    assert [(o.frame_index, o.track_id) for o in result.owned_observations] == [
        (i, tid) for i in range(80) for tid in (7, 9)]
    assert capture.peak_frames <= 2
    assert capture.released
