from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
import tracemalloc

import cv2
import numpy as np
import pytest

from dance_highlight.services.face_cluster import FaceClusterService
from dance_highlight.services.segment import Segment


@dataclass
class DummyConfig:
    face_det_size: tuple[int, int] = (320, 320)
    face_min_det_score: float = 0.28
    face_nms_threshold: float = 0.3
    face_top_k: int = 5000
    face_roi_expand_w: float = 0.0
    face_roi_expand_h_top: float = 0.0
    face_roi_expand_h_bottom: float = 0.0
    face_sample_frames: int = 5
    face_candidate_sample_frames: int = 12


class FakeDetector:
    def __init__(self, faces: np.ndarray | None) -> None:
        self.faces = faces
        self.input_size: tuple[int, int] | None = None

    def setInputSize(self, size: tuple[int, int]) -> None:
        self.input_size = size

    def detect(self, _img: np.ndarray):
        return 1, self.faces


class FakeRecognizer:
    def __init__(self, feature: np.ndarray) -> None:
        self.feature_value = feature
        self.aligned_shape: tuple[int, ...] | None = None

    def alignCrop(self, img: np.ndarray, _face: np.ndarray) -> np.ndarray:
        self.aligned_shape = img.shape
        return img

    def feature(self, _aligned: np.ndarray) -> np.ndarray:
        return self.feature_value


class FrameScoreDetector:
    def setInputSize(self, _size: tuple[int, int]) -> None:
        pass

    def detect(self, img: np.ndarray):
        frame_id = int(img[0, 0, 0])
        score = 0.10 + frame_id * 0.07
        face = np.array([[0, 0, 10, 10, 1, 1, 8, 1, 5, 5, 2, 8, 8, 8, score]], dtype=np.float32)
        return 1, face


class FrameFeatureRecognizer:
    def alignCrop(self, img: np.ndarray, _face: np.ndarray) -> np.ndarray:
        return img

    def feature(self, aligned: np.ndarray) -> np.ndarray:
        frame_id = float(aligned[0, 0, 0])
        return np.array([[1.0, frame_id]], dtype=np.float32)


class FakeVideoCapture:
    def __init__(self, total_frames: int = 12, fps: float = 1.0) -> None:
        self.total_frames = total_frames
        self.fps = fps
        self.index = 0

    def isOpened(self) -> bool:
        return True

    def get(self, prop: int) -> float:
        if prop == 5:  # cv2.CAP_PROP_FPS
            return self.fps
        return 0.0

    def read(self):
        if self.index >= self.total_frames:
            return False, None
        frame = np.full((24, 24, 3), self.index, dtype=np.uint8)
        self.index += 1
        return True, frame

    def grab(self) -> bool:
        if self.index >= self.total_frames:
            return False
        self.index += 1
        return True

    def release(self) -> None:
        pass


def make_service(detector: FakeDetector, recognizer: FakeRecognizer) -> FaceClusterService:
    service = FaceClusterService.__new__(FaceClusterService)
    service.config = DummyConfig()
    service._detector = detector
    service._recognizer = recognizer
    return service


def test_get_face_embedding_uses_opencv_detector_and_normalizes_feature() -> None:
    # OpenCV YuNet face row: x, y, w, h, five landmarks, score.
    faces = np.array([[0, 0, 10, 10, 1, 1, 8, 1, 5, 5, 2, 8, 8, 8, 0.95]], dtype=np.float32)
    detector = FakeDetector(faces)
    recognizer = FakeRecognizer(np.array([[3.0, 4.0]], dtype=np.float32))
    service = make_service(detector, recognizer)

    emb = service.get_face_embedding(np.zeros((24, 32, 3), dtype=np.uint8))

    assert detector.input_size == (32, 24)
    assert recognizer.aligned_shape == (24, 32, 3)
    assert emb is not None
    np.testing.assert_allclose(emb, np.array([0.6, 0.8], dtype=np.float32), rtol=1e-6)


@pytest.mark.parametrize("image_shape,face_box,thumbnail_size", [
    ((480, 640), (100, 90, 240, 180), 256),
    ((200, 300), (-10, -5, 100, 80), 126),
    ((160, 200), (180, 140, 40, 40), 28),
])
def test_display_thumbnail_uses_bounded_source_pixels_and_preserves_recognition_evidence(
    image_shape, face_box, thumbnail_size,
):
    face = np.array([[*face_box, 1, 1, 8, 1, 5, 5, 2, 8, 8, 8, .95]], dtype=np.float32)
    source = np.full((*image_shape, 3), (240, 30, 10), dtype=np.uint8)
    aligned = np.full((112, 112, 3), (10, 30, 240), dtype=np.uint8)

    class Recognizer:
        feature_calls = 0

        def alignCrop(self, _image, _face):
            return aligned

        def feature(self, image):
            assert image is aligned
            self.feature_calls += 1
            return np.array([3., 4.], dtype=np.float32)

    recognizer = Recognizer()
    service = make_service(FakeDetector(face), recognizer)
    okay, evidence = cv2.imencode(".jpg", aligned, [cv2.IMWRITE_JPEG_QUALITY, 82])
    assert okay

    candidate = service.get_face_embedding_candidate(source)

    assert candidate is not None
    assert candidate.preview_jpeg == evidence.tobytes()
    assert recognizer.feature_calls == 1
    np.testing.assert_array_equal(candidate.embedding, np.array([.6, .8], dtype=np.float32))
    thumbnail_bytes = getattr(candidate, "thumbnail_jpeg", b"")
    assert thumbnail_bytes
    thumbnail = cv2.imdecode(np.frombuffer(thumbnail_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
    assert thumbnail.shape == (thumbnail_size, thumbnail_size, 3)
    np.testing.assert_allclose(thumbnail.mean(axis=(0, 1)), [240, 30, 10], atol=2)


@pytest.mark.parametrize("thumbnail", [None, b"source-thumbnail"])
def test_batch_retains_display_thumbnails_separately_with_legacy_candidate_fallback(
    monkeypatch, thumbnail,
):
    candidate = SimpleNamespace(
        embedding=np.array([.6, .8], dtype=np.float32), quality=1.,
        preview_jpeg=b"aligned-evidence", face_bbox=None, landmarks=(),
        candidate_boxes=(), detector_score=.95, face_sharpness=1.,
    )
    if thumbnail is not None:
        candidate.thumbnail_jpeg = thumbnail
    service = make_service(FakeDetector(None), FakeRecognizer(np.ones(2)))
    monkeypatch.setattr(service, "_inspect_face", lambda *_args, **_kwargs: (candidate, None))
    monkeypatch.setattr("dance_highlight.services.face_cluster.cv2.VideoCapture",
                        lambda _: FakeVideoCapture(2, 1.))
    body = np.array([0., 0., 20., 20.])
    segment = Segment("main", 7, 0., 2., [(0., body, 7), (1., body, 7)])

    result = service.batch_segment_embeddings("fake.mp4", [segment], frame_records=[])[0]

    expected_thumbnail = thumbnail or b"aligned-evidence"
    assert result.track_evidence_images == [[b"aligned-evidence", b"aligned-evidence"]]
    assert result.owned_previews == {0: b"aligned-evidence", 1: b"aligned-evidence"}
    assert getattr(result, "track_thumbnail_images", []) == [[expected_thumbnail, expected_thumbnail]]
    assert getattr(result, "owned_thumbnails", {}) == {0: expected_thumbnail, 1: expected_thumbnail}


def test_dense_display_images_use_bounded_memory_and_preserve_later_split_thumbnails(monkeypatch):
    from dance_highlight.services.face_cluster import FaceEmbeddingCandidate
    from dance_highlight.services.main_identity import refine_main_identities
    from dance_highlight.services.reference_matcher import SegmentReferenceDecision

    service = make_service(FakeDetector(None), FakeRecognizer(np.ones(2)))
    service.config = DummyConfig(face_sample_frames=2, face_candidate_sample_frames=2)
    service.config.face_identity_interval_sec = .2

    def inspect(image, *, cache, **_kwargs):
        if 'candidate' not in cache:
            index = int(image[0, 0, 0])
            cache['candidate'] = FaceEmbeddingCandidate(
                embedding=np.array([1., 0.] if index < 100 else [0., 1.], dtype=np.float32),
                quality=float(index), preview_jpeg=b'aligned-evidence', detector_score=.95,
                face_bbox=(1., 1., 3., 3.) if index < 100 else (10., 10., 22., 22.),
                thumbnail_jpeg=bytes([index]) * (64 * 1024),
            )
        return cache['candidate'], None

    class Matcher:
        def match(self, observation, *_args):
            name = 'B' if observation.time_seconds >= 20. else None
            return SimpleNamespace(
                reference_id=name, status='matched' if name else 'unmatched',
                reason='accepted' if name else 'distance_exceeded',
                candidates=[SimpleNamespace(reference_id='B', distance=.2)] if name else [],
            )

    monkeypatch.setattr(service, '_inspect_face', inspect)
    monkeypatch.setattr('dance_highlight.services.face_cluster.cv2.VideoCapture',
                        lambda _: FakeVideoCapture(200, 5.))
    body = np.array([0., 0., 24., 24.])
    segment = Segment('main', 7, 0., 40., [(i / 5, body, 7) for i in range(200)])

    tracemalloc.start()
    try:
        result = service.batch_segment_embeddings('fake.mp4', [segment], frame_records=[])[0]
        output = refine_main_identities(
            [segment], [SegmentReferenceDecision(None, 'unmatched', 'distance_exceeded')],
            [3], [[]], [result], Matcher(),
        )
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    assert len(result.observations) == 2
    assert len(result.owned_observations) == len(result.owned_thumbnails) == 200
    assert result.owned_previews == {i: b'aligned-evidence' for i in range(200)}
    assert [piece.start for piece in output['segments']] == [0., 20.]
    assert output['previews'][0][0] == bytes([99]) * (64 * 1024)
    assert output['previews'][1][0] == bytes([199]) * (64 * 1024)
    assert peak < 3 * 1024 * 1024, f'dense display images retained {peak} bytes in memory'


def test_get_face_embedding_rejects_below_threshold_face() -> None:
    faces = np.array([[0, 0, 10, 10, 1, 1, 8, 1, 5, 5, 2, 8, 8, 8, 0.10]], dtype=np.float32)
    service = make_service(
        FakeDetector(faces),
        FakeRecognizer(np.array([[3.0, 4.0]], dtype=np.float32)),
    )

    assert service.get_face_embedding(np.zeros((24, 32, 3), dtype=np.uint8)) is None


def test_get_face_embedding_returns_none_when_no_face_detected() -> None:
    service = make_service(
        FakeDetector(None),
        FakeRecognizer(np.array([[3.0, 4.0]], dtype=np.float32)),
    )

    assert service.get_face_embedding(np.zeros((24, 32, 3), dtype=np.uint8)) is None


def test_invalid_auraface_landmarks_skip_the_face_without_failing_the_job() -> None:
    faces = np.array([[0, 0, 10, 10, 1, 1, 8, 1, 5, 5, 2, 8, 8, 8, 0.95]], dtype=np.float32)

    class InvalidRecognizer:
        def alignCrop(self, _frame, _face):
            raise ValueError("Invalid YuNet landmarks")

    service = make_service(FakeDetector(faces), InvalidRecognizer())

    assert service.get_face_embedding(np.zeros((24, 32, 3), dtype=np.uint8)) is None


def test_group_face_embeddings_exclude_faces_outside_participant_bodies() -> None:
    faces = np.array([
        [10, 10, 20, 20, 12, 12, 25, 12, 18, 20, 13, 26, 25, 26, 0.90],
        [110, 10, 20, 20, 112, 12, 125, 12, 118, 20, 113, 26, 125, 26, 0.95],
    ], dtype=np.float32)
    service = make_service(
        FakeDetector(faces), FakeRecognizer(np.array([[3.0, 4.0]], dtype=np.float32)),
    )

    result = service.group_face_embeddings(
        np.zeros((100, 200, 3), dtype=np.uint8),
        [np.array([0, 0, 60, 80], dtype=np.float32)],
    )

    assert len(result) == 1
    np.testing.assert_allclose(result[0], [0.6, 0.8])


def test_batch_segment_embeddings_scans_candidate_frames_and_averages_top_quality(monkeypatch) -> None:
    service = FaceClusterService.__new__(FaceClusterService)
    service.config = DummyConfig(face_min_det_score=0.0)
    service._detector = FrameScoreDetector()
    service._recognizer = FrameFeatureRecognizer()
    monkeypatch.setattr(
        "dance_highlight.services.face_cluster.cv2.VideoCapture",
        lambda _path: FakeVideoCapture(),
    )

    segment = Segment(
        seg_type="main",
        label=7,
        start=0.0,
        end=11.0,
        bboxes=[
            (float(i), np.array([0, 0, 20, 20], dtype=np.float32), 7)
            for i in range(12)
        ],
    )

    results = service.batch_segment_embeddings("fake.mp4", [segment])

    top_frame_embeddings = []
    for frame_id in range(7, 12):
        emb = np.array([1.0, float(frame_id)], dtype=np.float32)
        top_frame_embeddings.append(emb / (np.linalg.norm(emb) + 1e-9))
    expected = np.mean(np.stack(top_frame_embeddings), axis=0)
    expected = expected / (np.linalg.norm(expected) + 1e-9)

    assert results[0].face_detected is True
    assert len(results[0].track_embeddings) == 1
    np.testing.assert_allclose(results[0].track_embeddings[0], expected, rtol=1e-6)
    assert len(results[0].track_evidence_images[0]) == 5
    assert all(cv2.imdecode(np.frombuffer(image, dtype=np.uint8), cv2.IMREAD_COLOR) is not None
               for image in results[0].track_evidence_images[0])

    # Low-ranked faces are still usable evidence even when excluded from the mean.
    assert len(results[0].observations) == 12
    assert results[0].track_ids == [7]
    assert [o.frame_index for o in results[0].observations] == list(range(12))
    assert [o.time_seconds for o in results[0].observations] == list(range(12))
    assert all(o.track_id == 7 for o in results[0].observations)


def test_single_face_is_retained_with_source_coordinates_without_accepting_a_track(monkeypatch):
    face = np.array([[1, 2, 8, 9, 2, 3, 7, 3, 4, 5, 3, 8, 6, 8, .9]], dtype=np.float32)
    service = make_service(FakeDetector(face), FakeRecognizer(np.array([[3., 4.]])))
    monkeypatch.setattr('dance_highlight.services.face_cluster.cv2.VideoCapture',
                        lambda _: FakeVideoCapture(total_frames=4, fps=2.0))
    segment = Segment('main', 7, 1.0, 2.0,
                      [(1.5, np.array([4., 5., 20., 22.]), 7)])
    result = service.batch_segment_embeddings('fake.mp4', [segment])[0]
    assert result.face_detected is False
    assert result.track_embeddings == []
    assert len(result.observations) == 1
    obs = result.observations[0]
    assert obs.frame_index == 3 and obs.time_seconds == 1.5
    assert obs.body_bbox == (4., 5., 20., 22.)
    assert obs.face_bbox == (5., 7., 13., 16.)
    assert obs.landmarks[0] == (6., 8.)
    assert obs.failure is None
    np.testing.assert_allclose(obs.embedding, [.6, .8])


def test_no_face_is_recorded_separately_from_a_single_valid_observation(monkeypatch):
    service = make_service(FakeDetector(None), FakeRecognizer(np.array([[3., 4.]])))
    monkeypatch.setattr('dance_highlight.services.face_cluster.cv2.VideoCapture',
                        lambda _: FakeVideoCapture(total_frames=1))
    result = service.batch_segment_embeddings('fake.mp4', [
        Segment('main', 1, 0., 1., [(0., np.array([0., 0., 20., 20.]), 1)])])[0]
    assert len(result.observations) == 1
    assert result.observations[0].failure == 'no_detection'
    assert result.observations[0].embedding is None


def test_main_face_selection_prefers_unique_head_over_higher_scoring_background_face():
    faces=np.array([
        [4, 1, 10, 10, 5,2,12,2,8,5,6,9,11,9,.99],
        [12, 30, 12, 12, 14,32,22,32,18,35,15,40,21,40,.8],
    ], dtype=np.float32)
    service=make_service(FakeDetector(faces), FakeRecognizer(np.array([[3.,4.]])))
    legacy=service.get_face_embedding_candidate(np.zeros((100,60,3),dtype=np.uint8))
    assert legacy.face_bbox == (4.,1.,14.,11.)
    candidate,failure=service._inspect_face(np.zeros((100,60,3),dtype=np.uint8),
                                            preferred_body=(0.,25.,50.,100.))
    assert failure is None
    assert candidate.face_bbox == (12.,30.,24.,42.)


def test_main_face_selection_does_not_guess_between_two_heads_inside_the_body():
    faces=np.array([
        [4, 28, 10, 10, 5,29,12,29,8,32,6,36,11,36,.99],
        [22, 30, 12, 12, 24,32,32,32,28,35,25,40,31,40,.8],
    ], dtype=np.float32)
    service=make_service(FakeDetector(faces), FakeRecognizer(np.array([[3.,4.]])))
    candidate,failure=service._inspect_face(np.zeros((100,60,3),dtype=np.uint8),
                                            preferred_body=(0.,25.,50.,100.))
    assert candidate is None
    assert failure == 'ambiguous_main_faces'


class RecordingCreate:
    """cv2 팩토리 호출 인자를 그대로 붙잡는다."""

    def __init__(self, result: object) -> None:
        self.result = result
        self.args: tuple = ()

    def __call__(self, *args, **kwargs):
        self.args = args
        return self.result


@dataclass
class LoadedFaceModels:
    detector_create: RecordingCreate
    recognizer_create: RecordingCreate
    detector_bytes: bytes
    recognizer_bytes: bytes
    model_dir: Path


def load_face_models(monkeypatch, tmp_path: Path) -> LoadedFaceModels:
    """실제 __init__ 경로(_ensure_app)를 태우고 cv2에 넘어간 인자를 회수한다."""
    model_dir = tmp_path / "plugin_models"
    model_dir.mkdir()
    detector_bytes = b"yunet-onnx-bytes"
    recognizer_bytes = b"auraface-onnx-bytes"
    (model_dir / "det.onnx").write_bytes(detector_bytes)
    (model_dir / "rec.onnx").write_bytes(recognizer_bytes)

    monkeypatch.setattr(
        "dance_highlight.services.face_cluster.ensure_face_models",
        lambda: {
            "opencv-yunet-face-detection": model_dir / "det.onnx",
            "auraface-v1-face-recognition": model_dir / "rec.onnx",
        },
    )
    detector_create = RecordingCreate(FakeDetector(None))
    recognizer_create = RecordingCreate(FakeRecognizer(np.zeros((1, 2), dtype=np.float32)))
    monkeypatch.setattr(cv2.FaceDetectorYN, "create", detector_create)
    monkeypatch.setattr("dance_highlight.services.face_cluster.AuraFaceRecognizer", recognizer_create)

    FaceClusterService(DummyConfig())

    return LoadedFaceModels(
        detector_create=detector_create,
        recognizer_create=recognizer_create,
        detector_bytes=detector_bytes,
        recognizer_bytes=recognizer_bytes,
        model_dir=model_dir,
    )


def test_face_models_are_created_from_file_bytes(monkeypatch, tmp_path: Path) -> None:
    loaded = load_face_models(monkeypatch, tmp_path)

    framework, model_buffer, config_buffer = loaded.detector_create.args[:3]
    assert framework == "onnx"
    assert bytes(model_buffer) == loaded.detector_bytes
    assert config_buffer.size == 0

    assert loaded.recognizer_create.args == (loaded.model_dir / "rec.onnx",)


def test_face_model_paths_are_never_handed_to_opencv(monkeypatch, tmp_path: Path) -> None:
    """Windows 한글 경로에서 cv2가 모델 파일을 못 열어(-5:Bad argument) 플러그인이 죽는다.

    OpenCV의 C++ 파일 열기는 narrow 문자열을 ANSI 코드페이지(한국어 윈도우=CP949)로
    해석하는데 파이썬은 UTF-8을 넘긴다. macOS/Linux는 둘 다 UTF-8이라 이 실패를
    **재현할 수 없으므로**, '경로 문자열을 cv2에 넘기지 않는다'는 계약을 대신 고정한다.
    이 테스트를 깨는 프로덕션 변경 = create()에 str(path)를 다시 넘기는 것.
    """
    loaded = load_face_models(monkeypatch, tmp_path)

    passed = loaded.detector_create.args
    leaked = [arg for arg in passed if isinstance(arg, str) and str(loaded.model_dir) in arg]
    assert leaked == []


def test_batch_preserves_legacy_aggregate_and_adds_pose_owned_face(monkeypatch):
    from dance_highlight.services.segment import FrameRec
    faces = np.array([
        [1, 1, 8, 8, 2, 2, 6, 2, 4, 4, 2, 6, 6, 6, .99],
        [11, 11, 8, 8, 12, 12, 16, 12, 14, 14, 12, 16, 16, 16, .8],
    ], dtype=np.float32)
    class Recognizer:
        def alignCrop(self, img, face):
            return np.full((5, 5, 3), face[0], dtype=np.uint8)
        def feature(self, crop):
            return np.array([1., float(crop[0,0,0])], dtype=np.float32)
    service = make_service(FakeDetector(faces), Recognizer())
    monkeypatch.setattr('dance_highlight.services.face_cluster.cv2.VideoCapture',
                        lambda _: FakeVideoCapture(2, 1.))
    body = np.array([0., 0., 20., 20.])
    seg = Segment('main', 7, 0., 2., [(0., body, 7), (1., body, 7)])
    records = [FrameRec(float(t), 7, body, False, person_bboxes=[body],
                       person_head_keypoints=[np.array([[12.,12.,.9], [16.,12.,.9]])]) for t in (0,1)]
    result = service.batch_segment_embeddings('fake.mp4', [seg], frame_records=records)[0]
    np.testing.assert_allclose(result.track_embeddings[0], np.array([1.,1.])/np.sqrt(2), rtol=1e-6)
    assert len(result.owned_observations) == 2
    for observation in result.owned_observations:
        assert observation.association == 'confirmed'
        assert observation.face_bbox == (11.,11.,19.,19.)
        np.testing.assert_allclose(observation.embedding, np.array([1.,11.])/np.sqrt(122), rtol=1e-6)


def test_unreadable_sample_frames_remain_explicit_failures(monkeypatch):
    service = make_service(FakeDetector(None), FakeRecognizer(np.ones(2)))
    monkeypatch.setattr('dance_highlight.services.face_cluster.cv2.VideoCapture',
                        lambda _: FakeVideoCapture(1, 1.))
    body = np.array([0., 0., 20., 20.])
    seg = Segment('main', 7, 0., 3., [(float(t), body, 7) for t in range(3)])
    result = service.batch_segment_embeddings('fake.mp4', [seg])[0]
    assert [o.failure for o in result.observations] == ['no_detection', 'frame_unreadable', 'frame_unreadable']


def test_dense_owned_samples_do_not_change_legacy_averages(monkeypatch):
    from dance_highlight.services.segment import FrameRec
    service = FaceClusterService.__new__(FaceClusterService)
    service.config = DummyConfig(face_min_det_score=0., face_candidate_sample_frames=2, face_sample_frames=2)
    service.config.face_identity_interval_sec = .2
    service._detector = FrameScoreDetector()
    service._recognizer = FrameFeatureRecognizer()
    monkeypatch.setattr('dance_highlight.services.face_cluster.cv2.VideoCapture',lambda _:FakeVideoCapture(12,5.))
    body=np.array([0.,0.,20.,20.]);rows=[(i/5,body,7) for i in range(12)]
    seg=Segment('main',7,0.,2.4,rows)
    baseline=service.batch_segment_embeddings('fake.mp4',[seg])[0]
    records=[FrameRec(t,7,body,False,person_bboxes=[body],person_head_keypoints=[np.array([[2,2,.9],[5,5,.9]])]) for t,_,_ in rows]
    dense=service.batch_segment_embeddings('fake.mp4',[seg],frame_records=records)[0]
    assert len(dense.owned_observations)==12
    assert len(dense.observations)==2
    np.testing.assert_array_equal(dense.track_embeddings,baseline.track_embeddings)


def test_supporting_member_sampling_skips_unused_legacy_track_averages(monkeypatch):
    service = FaceClusterService.__new__(FaceClusterService)
    service.config = DummyConfig(face_min_det_score=0.0)
    service._detector = FrameScoreDetector()
    service._recognizer = FrameFeatureRecognizer()
    monkeypatch.setattr('dance_highlight.services.face_cluster.cv2.VideoCapture',
                        lambda _: FakeVideoCapture(total_frames=12, fps=30.))
    body = np.array([0., 0., 20., 20.])
    segment = Segment('main', -1, 0., .4, [(i/30., body, -1) for i in range(12)])
    result = service.batch_segment_embeddings('fake.mp4', [segment], frame_records=[],
                                              evidence_only_indices={0})[0]
    assert result.track_embeddings == []
    assert result.observations == []
    assert [o.frame_index for o in result.owned_observations] == [0, 6]


def test_short_main_body_run_keeps_repeated_face_samples_between_regular_samples(monkeypatch):
    from dance_highlight.services.segment import FrameRec
    face = np.array([[0,0,10,10,1,1,8,1,5,5,2,8,8,8,.99]],np.float32)
    service = make_service(FakeDetector(face),FakeRecognizer(np.array([[1.,0.]],np.float32)))
    service.config.face_candidate_sample_frames = 2
    service.config.face_sample_frames = 2
    monkeypatch.setattr('dance_highlight.services.face_cluster.cv2.VideoCapture',
                        lambda _: FakeVideoCapture(49,60.))
    body=np.array([0.,0.,20.,20.]);rows=[(i/60.,body,2 if 8<=i<=20 else 1) for i in range(0,49,4)]
    records=[FrameRec(t,tid,body,False,person_bboxes=[body],
                     person_head_keypoints=[np.array([[2.,2.,.9],[5.,5.,.9]])]) for t,_,tid in rows]
    result=service.batch_segment_embeddings('fake.mp4',[Segment('main',None,0.,.81,rows)],frame_records=records,
                                            sample_all_main_frames=True)[0]
    assert [o.frame_index for o in result.owned_observations if o.track_id==2] == [8,12,16,20]
    assert all(o.association=='confirmed' for o in result.owned_observations)


def test_continuous_analysis_scope_reports_progress_before_last_sample(monkeypatch):
    service = make_service(FakeDetector(None), FakeRecognizer(np.ones(2)))
    capture = FakeVideoCapture(12, 5.)
    monkeypatch.setattr('dance_highlight.services.face_cluster.cv2.VideoCapture', lambda _: capture)
    body = np.array([0., 0., 20., 20.])
    seg = Segment('main', None, 0., 2.4, [(i/5., body, 1) for i in range(12)])
    reports = []
    service.batch_segment_embeddings('fake.mp4', [seg], frame_records=[],
                                     on_progress=lambda done, total: reports.append((done/total, capture.index)))
    assert any(0 < fraction < 1 and frame < 12 for fraction, frame in reports)
    assert reports[-1][0] == 1.
    assert [f for f, _ in reports] == sorted(f for f, _ in reports)


def test_registered_sampling_keeps_each_pose_observation_even_when_body_id_does_not_change(monkeypatch):
    service = make_service(FakeDetector(None), FakeRecognizer(np.ones(2)))
    service.config.face_candidate_sample_frames = 2
    service.config.face_sample_frames = 2
    monkeypatch.setattr('dance_highlight.services.face_cluster.cv2.VideoCapture',
                        lambda _: FakeVideoCapture(49, 60.))
    body = np.array([0., 0., 20., 20.])
    seg = Segment('main', None, 0., .81, [(i/60., body, 7) for i in range(0, 49, 4)])
    result = service.batch_segment_embeddings('fake.mp4', [seg], frame_records=[],
                                              sample_all_main_frames=True)[0]
    assert [o.frame_index for o in result.owned_observations] == list(range(0,49,4))
    assert len(result.observations) == 2  # legacy aggregate input stays separate
def test_agglomerative_single_face_forms_one_cluster_after_scene_filtering():
    service = FaceClusterService.__new__(FaceClusterService)
    service.config = SimpleNamespace(cluster_method='agglomerative', cluster_distance_threshold=.6)
    assert service.cluster_embeddings([np.array([1., 0.], dtype=np.float32)]) == [1]
