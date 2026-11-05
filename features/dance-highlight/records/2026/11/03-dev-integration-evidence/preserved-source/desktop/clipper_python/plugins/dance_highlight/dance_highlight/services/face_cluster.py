from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import dataclass, field
from tempfile import TemporaryFile
from typing import Callable, Dict, List, Optional, Tuple
import numpy as np
import cv2
from clipper_face_core.auraface import AuraFaceRecognizer
from clipper_face_core.face_models import AURAFACE_MODEL_NAME

from .segment import Segment, FrameRec
from .face_models import ensure_face_models, read_model_buffer
from .face_evidence import FaceObservation, Box, select_pose_face
from .person_thumbnails import FaceThumbnailStore
from .face_runtime import CachedFaceDetector, DanceFaceSession
from .opencv_acceleration import AcceleratedYuNet


@dataclass
class SegmentFaceResult:
    seg: Segment
    track_embeddings: List[np.ndarray]   # track 단위 평균 임베딩
    face_detected: bool
    track_evidence_images: List[List[bytes]] = field(default_factory=list)
    track_ids: List[int] = field(default_factory=list)
    observations: List[FaceObservation] = field(default_factory=list)
    owned_observations: List[FaceObservation] = field(default_factory=list)
    owned_previews: Dict[int, bytes] = field(default_factory=dict)
    track_thumbnail_images: List[List[bytes]] = field(default_factory=list)
    owned_thumbnails: Mapping[int, bytes] = field(default_factory=dict)


@dataclass(frozen=True)
class FaceEmbeddingCandidate:
    embedding: np.ndarray
    quality: float
    preview_jpeg: bytes = b""
    face_bbox: Box | None = None
    landmarks: tuple[tuple[float, float], ...] = ()
    candidate_boxes: tuple[Box, ...] = ()
    detector_score: float = 0.0
    face_sharpness: float = 0.0
    thumbnail_jpeg: bytes = b""
    detection_rotation_degrees: float = 0.0


def clamp_int(v: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, v))


class FaceClusterService:
    def __init__(self, config):
        self.config = config
        self._detector = None
        self._recognizer = None
        self._ensure_app()

    def _ensure_app(self):
        if self._detector is not None and self._recognizer is not None:
            return
        model_paths = ensure_face_models()
        from .face_models import sha256_file
        self.model_provenance = {name: {"path": str(path), "sha256": sha256_file(path)}
                                 for name, path in model_paths.items()}
        # 경로가 아니라 바이트를 넘긴다 — 이유는 read_model_buffer() 참고.
        no_config = np.empty(0, dtype=np.uint8)
        self._detector = cv2.FaceDetectorYN.create(
            "onnx",
            read_model_buffer(model_paths["opencv-yunet-face-detection"]),
            no_config,
            tuple(self.config.face_det_size),
            float(self.config.face_min_det_score),
            float(self.config.face_nms_threshold),
            int(self.config.face_top_k),
        )
        self._recognizer = AuraFaceRecognizer(model_paths[AURAFACE_MODEL_NAME],
                                              session_factory=DanceFaceSession)
        self._detector = CachedFaceDetector(AcceleratedYuNet(
            self._detector, model_paths['opencv-yunet-face-detection'],
            float(self.config.face_min_det_score), float(self.config.face_nms_threshold),
            int(self.config.face_top_k)))

    def _l2(self, v: np.ndarray) -> np.ndarray:
        n = float(np.linalg.norm(v) + 1e-9)
        return v / n

    def get_face_embedding(self, img_bgr: np.ndarray) -> Optional[np.ndarray]:
        candidate = self.get_face_embedding_candidate(img_bgr)
        return candidate.embedding if candidate is not None else None

    def get_face_embedding_candidate(self, img_bgr: np.ndarray) -> Optional[FaceEmbeddingCandidate]:
        return self._inspect_face(img_bgr)[0]

    def _inspect_face(self, img_bgr: np.ndarray, *, preferred_body: Box | None = None,
                      pose_record: FrameRec | None = None, source_body=None, offset=(0, 0),
                      require_pose: bool = False, cache: dict | None = None
                      ) -> tuple[Optional[FaceEmbeddingCandidate], str | None]:
        self._ensure_app()
        if img_bgr is None or img_bgr.size == 0:
            return None, 'empty_roi'

        h, w = img_bgr.shape[:2]
        if cache is not None and 'detections' in cache:
            faces = cache['detections']
        else:
            try:
                if cache is not None and 'detection_error' in cache:
                    raise cache.pop('detection_error')
                self._detector.setInputSize((int(w), int(h)))
                _, faces = self._detector.detect(img_bgr)
            except cv2.error:
                return None, 'detection_failed'
            if cache is not None:
                cache['detections'] = faces

        if (faces is None or len(faces) == 0) and not require_pose:
            return None, 'no_detection'

        faces = sorted([] if faces is None else faces, key=lambda face: float(face[-1]), reverse=True)
        selected = faces
        rotation_degrees = 0.
        if preferred_body is not None and not require_pose:
            bx1, by1, bx2, by2 = preferred_body
            selected = [f for f in faces if float(f[-1]) >= self.config.face_min_det_score
                        and bx1 <= float(f[0] + f[2] / 2) <= bx2
                        and by1 <= float(f[1] + f[3] / 2) <= by1 + .45 * (by2 - by1)]
            if len(selected) != 1:
                return None, 'ambiguous_main_faces' if selected else 'no_main_face'
        if require_pose:
            selected = [f for f in faces if float(f[-1]) >= self.config.face_min_det_score]
            boxes = [(float(f[0]) + offset[0], float(f[1]) + offset[1],
                      float(f[0] + f[2]) + offset[0], float(f[1] + f[3]) + offset[1]) for f in selected]
            index, failure = select_pose_face(boxes, source_body, pose_record)
            chosen = selected[index] if index is not None else None
            if chosen is None or float(chosen[-1]) < .9:
                from .pose_face_rotation import rotated_pose_face
                recovery = rotated_pose_face(img_bgr, self._detector, source_body, pose_record,
                                             offset, float(self.config.face_min_det_score))
                if recovery is not None and (chosen is None or recovery[0][-1] > chosen[-1]):
                    chosen, faces, rotation_degrees = recovery
            if chosen is None:
                return None, failure
            selected = [chosen]
        face = np.asarray(selected[0], dtype=np.float32)
        face_score = float(face[-1])
        if face_score < float(self.config.face_min_det_score):
            return None, 'low_detection_score'

        key = face.tobytes()
        if cache is not None and key in cache:
            return cache[key], None
        try:
            aligned = self._recognizer.alignCrop(img_bgr, face)
            emb = self._recognizer.feature(aligned)
        except (cv2.error, ValueError):
            return None, 'alignment_or_embedding_failed'

        emb = np.asarray(emb, dtype=np.float32).reshape(-1)
        try:
            ok, preview = cv2.imencode(".jpg", aligned, [cv2.IMWRITE_JPEG_QUALITY, 82])
            preview_jpeg = preview.tobytes() if ok else b""
        except cv2.error:
            preview_jpeg = b""
        def box(value):
            x, y, bw, bh = map(float, value[:4])
            return (max(0., x), max(0., y), min(float(w), x + bw), min(float(h), y + bh))
        face_box = box(face)
        fx1, fy1, fx2, fy2 = (int(v) for v in face_box)
        candidate = FaceEmbeddingCandidate(
            embedding=self._l2(emb).astype(np.float32),
            quality=self.face_embedding_quality(img_bgr, face, face_score),
            preview_jpeg=preview_jpeg,
            face_bbox=face_box,
            landmarks=tuple((float(x), float(y)) for x, y in face[4:14].reshape(5, 2)),
            candidate_boxes=tuple(box(f) for f in faces if float(f[-1]) >= self.config.face_min_det_score),
            detector_score=face_score,
            face_sharpness=self.blur_quality_score(img_bgr[fy1:fy2, fx1:fx2]),
            thumbnail_jpeg=self._display_thumbnail(img_bgr, face_box),
            detection_rotation_degrees=rotation_degrees,
        )
        if cache is not None:
            cache[key] = candidate
        return candidate, None

    def _display_thumbnail(self, img_bgr: np.ndarray, face_box: Box) -> bytes:
        """Keep source face pixels for display, separately from aligned evidence."""
        x1, y1, x2, y2 = face_box
        if x2 <= x1 or y2 <= y1:
            return b""
        height, width = img_bgr.shape[:2]
        side = min(width, height, int(np.ceil(max(x2 - x1, y2 - y1) * 1.4)))
        left = clamp_int(int((x1 + x2 - side) / 2), 0, width - side)
        top = clamp_int(int((y1 + y2 - side) / 2), 0, height - side)
        crop = img_bgr[top:top + side, left:left + side]
        try:
            if side > 256:
                crop = cv2.resize(crop, (256, 256), interpolation=cv2.INTER_AREA)
            ok, thumbnail = cv2.imencode(".jpg", crop, [cv2.IMWRITE_JPEG_QUALITY, 92])
            return thumbnail.tobytes() if ok else b""
        except cv2.error:
            return b""

    def detect_face_boxes(self, frame_bgr: np.ndarray) -> List[np.ndarray]:
        """Return full-frame face boxes in source-video pixel coordinates."""
        self._ensure_app()
        height, width = frame_bgr.shape[:2]
        scale = min(1.0, 960.0 / max(width, height))
        sample = cv2.resize(frame_bgr, None, fx=scale, fy=scale) if scale < 1.0 else frame_bgr
        try:
            self._detector.setInputSize((sample.shape[1], sample.shape[0]))
            _, faces = self._detector.detect(sample)
        except cv2.error:
            return []
        if faces is None:
            return []
        boxes: List[np.ndarray] = []
        for face in faces:
            if float(face[-1]) < float(self.config.face_min_det_score):
                continue
            x, y, face_width, face_height = (float(part) / scale for part in face[:4])
            boxes.append(np.asarray([
                max(0.0, x), max(0.0, y),
                min(float(width), x + face_width), min(float(height), y + face_height),
            ], dtype=np.float32))
        return boxes

    def group_face_embeddings(
        self, frame_bgr: np.ndarray, participant_bboxes: List[np.ndarray],
    ) -> List[np.ndarray]:
        """단체 참여자 몸 박스에 들어온 얼굴만 인식한다."""
        if not participant_bboxes:
            return []
        self._ensure_app()
        height, width = frame_bgr.shape[:2]
        scale = min(1.0, 960.0 / max(width, height))
        sample = cv2.resize(frame_bgr, None, fx=scale, fy=scale) if scale < 1.0 else frame_bgr
        try:
            self._detector.setInputSize((sample.shape[1], sample.shape[0]))
            _, faces = self._detector.detect(sample)
        except cv2.error:
            return []
        embeddings: List[np.ndarray] = []
        if faces is None:
            return embeddings
        for value in faces:
            face = np.asarray(value, dtype=np.float32).copy()
            face[:14] /= scale
            x, y, face_width, face_height = face[:4]
            center_x, center_y = float(x + face_width / 2), float(y + face_height / 2)
            if (float(face[-1]) < 0.5 or face_width < 20 or
                    not any(float(box[0]) <= center_x <= float(box[2]) and
                            float(box[1]) <= center_y <= float(box[3])
                            for box in participant_bboxes)):
                continue
            try:
                aligned = self._recognizer.alignCrop(frame_bgr, face)
                embedding = np.asarray(self._recognizer.feature(aligned), dtype=np.float32).reshape(-1)
            except (cv2.error, ValueError):
                continue
            embeddings.append(self._l2(embedding).astype(np.float32))
        return embeddings

    def face_embedding_quality(self, img_bgr: np.ndarray, face: np.ndarray, face_score: float) -> float:
        h, w = img_bgr.shape[:2]
        roi_area = max(1.0, float(w * h))
        face_area = max(1.0, float(face[2]) * float(face[3]))
        size_score = min(1.0, face_area / roi_area)
        blur_score = self.blur_quality_score(img_bgr)
        return float((0.65 * max(0.0, min(1.0, face_score))) + (0.25 * size_score) + (0.10 * blur_score))

    def blur_quality_score(self, img_bgr: np.ndarray) -> float:
        try:
            gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
            variance = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        except cv2.error:
            return 0.0
        return float(max(0.0, min(1.0, variance / 150.0)))

    def expand_face_roi(self, bbox: np.ndarray, w: int, h: int) -> Tuple[int, int, int, int]:
        x1, y1, x2, y2 = bbox.astype(np.float32)
        bw = float(x2 - x1)
        bh = float(y2 - y1)

        nx1 = int(x1 - bw * float(self.config.face_roi_expand_w))
        nx2 = int(x2 + bw * float(self.config.face_roi_expand_w))

        ny1 = int(y1 - bh * float(self.config.face_roi_expand_h_top))
        ny2 = int(y2 + bh * float(self.config.face_roi_expand_h_bottom))

        nx1 = clamp_int(nx1, 0, w - 1)
        nx2 = clamp_int(nx2, 0, w - 1)
        ny1 = clamp_int(ny1, 0, h - 1)
        ny2 = clamp_int(ny2, 0, h - 1)

        if nx2 <= nx1:
            nx2 = min(w - 1, nx1 + 1)
        if ny2 <= ny1:
            ny2 = min(h - 1, ny1 + 1)

        return nx1, ny1, nx2, ny2

    def _sample_bboxes(
        self,
        bboxes: List[Tuple],
        max_frames: int,
    ) -> List[Tuple]:
        """세그먼트 bbox 목록에서 최대 max_frames 개를 균등 간격으로 샘플링."""
        n = len(bboxes)
        if n <= max_frames:
            return bboxes
        indices = [int(i * n / max_frames) for i in range(max_frames)]
        return [bboxes[i] for i in indices]

    def _face_frames(self, cap, frame_to_tasks, *, prefetch):
        """Keep at most the current and next frame; embedding stays on the caller."""
        cur_fidx = 0
        max_frame_idx = max(frame_to_tasks)

        def read_next():
            nonlocal cur_fidx
            while cur_fidx <= max_frame_idx:
                fidx = cur_fidx
                cur_fidx += 1
                if fidx not in frame_to_tasks:
                    if not cap.grab():
                        return None
                    continue
                ret, frame = cap.read()
                if not ret:
                    return None
                caches = {}
                if prefetch:
                    height, width = frame.shape[:2]
                    for task_i, bbox, _, _ in frame_to_tasks[fidx]:
                        x1, y1, x2, y2 = self.expand_face_roi(bbox, width, height)
                        roi = frame[y1:y2, x1:x2]
                        cache = caches[task_i] = {}
                        if not roi.size:
                            continue
                        try:
                            self._detector.setInputSize((x2 - x1, y2 - y1))
                            _, cache['detections'] = self._detector.detect(roi)
                        except cv2.error as error:
                            # Replay the first failure once. A pose-owned retry
                            # after a failed legacy inspection must still run.
                            cache['detection_error'] = error.with_traceback(None)
                return fidx, frame, caches
            return None

        try:
            if not prefetch:
                while (data := read_next()) is not None:
                    yield data
                    data = None
                return
            with ThreadPoolExecutor(max_workers=1, thread_name_prefix='dance-face-roi') as pool:
                pending = pool.submit(read_next)
                try:
                    while (data := pending.result()) is not None:
                        pending = pool.submit(read_next)
                        yield data
                        data = None
                finally:
                    pending.cancel()
        finally:
            cap.release()

    def batch_segment_embeddings(
        self,
        video_path: str,
        segments: List[Segment],
        on_progress: Optional[Callable[[int, int], None]] = None,
        *, frame_records: Optional[List[FrameRec]] = None,
        evidence_only_indices: frozenset[int] = frozenset(),
        sample_all_main_frames: bool = False,
    ) -> List[SegmentFaceResult]:
        """
        VideoCapture를 한 번만 열어 모든 세그먼트의 얼굴 임베딩을 추출.

        - 세그먼트마다 cap을 재오픈하는 오버헤드 제거
        - config.face_candidate_sample_frames 개 후보 bbox를 균등 샘플링
        - 얼굴 품질 상위 config.face_sample_frames 개만 평균에 사용
        - Sequential forward read: random seek 대신 cap.grab()으로 비대상 프레임
          건너뜀 → H.264 seek 오버헤드(~1s/seek) 완전 제거
        - on_progress(completed: int, total: int): sampled frames plus empty scopes
        """
        total = len(segments)
        max_frames = max(1, int(self.config.face_sample_frames))
        candidate_frames = max(
            max_frames,
            int(getattr(self.config, "face_candidate_sample_frames", max_frames)),
        )
        completed = 0

        results: List[Optional[SegmentFaceResult]] = [None] * total

        # 처리 대상: (t, bbox, track_id, seg_idx) 수집 및 시간순 정렬
        tasks: List[Tuple[float, np.ndarray, int, int]] = []
        legacy_tasks: set[tuple[int, float, int]] = set()

        for seg_idx, seg in enumerate(segments):
            if seg.seg_type != "main" or not seg.bboxes:
                results[seg_idx] = SegmentFaceResult(seg=seg, track_embeddings=[], face_detected=False)
                completed += 1
                continue

            sampled = ([] if seg_idx in evidence_only_indices else
                       self._sample_bboxes(seg.bboxes, candidate_frames))
            legacy_tasks.update((seg_idx, float(t), int(tid)) for t, _, tid in sampled)
            if frame_records is not None and sample_all_main_frames:
                # Registered identities must not lose source observations when
                # analysis scopes are regrouped. A body ID may also survive a
                # change of face, so track changes cannot drive sampling alone.
                sampled = seg.bboxes
            elif frame_records is not None:
                dense, last = [], float('-inf')
                interval = float(getattr(self.config, 'face_identity_interval_sec', .2))
                for row in seg.bboxes:
                    if row[0] - last >= interval - 1e-6:
                        dense.append(row)
                        last = row[0]
                sampled = sorted({(float(t), int(tid)): (t, bbox, tid)
                                  for t, bbox, tid in [*sampled, *dense]}.values(), key=lambda row: row[0])
            for t, bbox, track_id in sampled:
                tasks.append((float(t), bbox, int(track_id), seg_idx))

        if not tasks:
            if on_progress and total:
                on_progress(total, total)
            return results  # type: ignore

        # 시간순 정렬
        tasks.sort(key=lambda x: x[0])

        # One continuous evidence scope may span the whole video. Report sample
        # progress so analysis does not appear stalled until that scope ends.
        progress_total = completed + len(tasks)
        if on_progress and completed:
            on_progress(completed, progress_total)

        # (seg_idx, track_id) → List[quality-scored embedding candidates]
        seg_track_candidates: Dict[Tuple[int, int], List[FaceEmbeddingCandidate]] = defaultdict(list)
        observations: Dict[int, List[FaceObservation]] = defaultdict(list)
        owned_observations: Dict[int, List[FaceObservation]] = defaultdict(list)
        processed: set[int] = set()
        owned_previews: Dict[int, Dict[int, bytes]] = defaultdict(dict)
        thumbnail_file = TemporaryFile()
        owned_thumbnails: Dict[int, FaceThumbnailStore] = defaultdict(
            lambda: FaceThumbnailStore(thumbnail_file))
        vid_fps = 30.0

        cap = cv2.VideoCapture(video_path)
        if cap.isOpened():
            vid_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            records = {int(round(r.t * vid_fps)): r for r in (frame_records or [])}

            # 타임스탬프 → 프레임 인덱스로 변환 후 그룹화.
            # t = fidx / fps 역산이므로 round()로 정확히 복원.
            # 같은 frame_idx에 복수 task가 있으면 한 번 decode로 모두 처리.
            frame_to_tasks: Dict[int, List[Tuple[int, np.ndarray, int, int]]] = {}
            for task_i, (t, bbox, track_id, seg_idx) in enumerate(tasks):
                fidx = int(round(t * vid_fps))
                frame_to_tasks.setdefault(fidx, []).append(
                    (task_i, bbox, track_id, seg_idx)
                )

            # Only the Dance detector wrapper makes setInputSize/detect atomic
            # across the CPU producer and main-thread pose rotation recovery.
            prefetch = (sample_all_main_frames and frame_records is not None
                        and isinstance(self._detector, CachedFaceDetector))
            with closing(self._face_frames(cap, frame_to_tasks, prefetch=prefetch)) as frames:
                for cur_fidx, frame, caches in frames:
                    fh, fw = frame.shape[:2]
                    for task_i, bbox, track_id, seg_idx in frame_to_tasks[cur_fidx]:
                        x1, y1, x2, y2 = self.expand_face_roi(bbox, fw, fh)
                        roi = frame[y1:y2, x1:x2]
                        preferred = ((float(bbox[0]) - x1, float(bbox[1]) - y1,
                                      float(bbox[2]) - x1, float(bbox[3]) - y1)
                                     if getattr(self.config, 'face_select_main_head', False) else None)
                        is_legacy = (seg_idx, tasks[task_i][0], track_id) in legacy_tasks
                        cache = caches.get(task_i, {})
                        candidate, failure = (self._inspect_face(roi, preferred_body=preferred, cache=cache)
                                              if is_legacy else (None, None))
                        if candidate is not None:
                            seg_track_candidates[(seg_idx, track_id)].append(candidate)
                        def offset_box(box):
                            return (box[0] + x1, box[1] + y1, box[2] + x1, box[3] + y1)
                        def observation(candidate, failure, association):
                            return FaceObservation(
                            frame_index=cur_fidx, time_seconds=cur_fidx / vid_fps,
                            track_id=track_id, body_bbox=tuple(float(v) for v in bbox),
                            roi_bbox=(float(x1), float(y1), float(x2), float(y2)),
                            face_bbox=offset_box(candidate.face_bbox) if candidate and candidate.face_bbox else None,
                            landmarks=tuple((x + x1, y + y1) for x, y in candidate.landmarks) if candidate else (),
                            candidate_boxes=tuple(offset_box(b) for b in candidate.candidate_boxes) if candidate else (),
                            embedding=candidate.embedding if candidate else None,
                            quality=candidate.quality if candidate else 0.,
                            detector_score=candidate.detector_score if candidate else 0.,
                            face_sharpness=candidate.face_sharpness if candidate else 0., failure=failure, association=association,
                            detection_rotation_degrees=getattr(candidate, 'detection_rotation_degrees', 0.),
                            )
                        if is_legacy:
                            observations[seg_idx].append(observation(candidate, failure, 'unassigned'))
                        owned, owned_failure = self._inspect_face(
                            roi, pose_record=records.get(cur_fidx), source_body=bbox,
                            offset=(x1, y1), require_pose=True, cache=cache,
                        ) if frame_records is not None else (None, 'pose_context_missing')
                        owned_observations[seg_idx].append(observation(
                            owned, owned_failure, 'confirmed' if owned else 'unassigned'))
                        if owned and owned.preview_jpeg:
                            owned_previews[seg_idx][cur_fidx] = owned.preview_jpeg
                        if owned:
                            thumbnail = getattr(owned, 'thumbnail_jpeg', b'') or owned.preview_jpeg
                            if thumbnail:
                                owned_thumbnails[seg_idx][cur_fidx] = thumbnail
                        processed.add(task_i)
                        completed += 1
                        if on_progress:
                            on_progress(completed, progress_total)
                    # Drop views before asking the producer for another frame.
                    del roi, frame

        for task_i, (t, bbox, track_id, seg_idx) in enumerate(tasks):
            if task_i not in processed:
                failure = FaceObservation(
                    frame_index=int(round(t * vid_fps)), time_seconds=round(t * vid_fps) / vid_fps,
                    track_id=track_id, body_bbox=tuple(float(v) for v in bbox),
                    roi_bbox=(), failure='frame_unreadable',
                )
                if (seg_idx, t, track_id) in legacy_tasks:
                    observations[seg_idx].append(failure)
                owned_observations[seg_idx].append(failure)
                completed += 1
                if on_progress:
                    on_progress(completed, progress_total)

        # 세그먼트별 결과 조립
        for seg_idx, seg in enumerate(segments):
            if results[seg_idx] is not None:
                continue  # 이미 처리됨 (non-main 세그먼트)

            track_ids = {int(track_id) for _, _, track_id in seg.bboxes}
            track_avg_embs: List[np.ndarray] = []
            track_evidence_images: List[List[bytes]] = []
            track_thumbnail_images: List[List[bytes]] = []
            retained_track_ids: List[int] = []

            for tid in track_ids:
                selected = sorted(
                    seg_track_candidates.get((seg_idx, tid), []),
                    key=lambda item: item.quality, reverse=True,
                )[:max_frames]
                embs = [candidate.embedding for candidate in selected]
                if len(embs) < 2:
                    continue
                avg = np.mean(np.stack(embs), axis=0)
                avg = self._l2(avg.astype(np.float32))
                track_avg_embs.append(avg)
                retained_track_ids.append(tid)
                track_evidence_images.append([candidate.preview_jpeg for candidate in selected if candidate.preview_jpeg])
                thumbnails = [getattr(candidate, 'thumbnail_jpeg', b'') or candidate.preview_jpeg
                              for candidate in selected]
                track_thumbnail_images.append([image for image in thumbnails if image])

            results[seg_idx] = SegmentFaceResult(
                seg=seg,
                track_embeddings=track_avg_embs,
                face_detected=len(track_avg_embs) > 0,
                track_evidence_images=track_evidence_images,
                track_ids=retained_track_ids,
                observations=sorted(observations[seg_idx], key=lambda o: o.frame_index),
                owned_observations=sorted(owned_observations[seg_idx], key=lambda o: o.frame_index),
                owned_previews=owned_previews[seg_idx],
                track_thumbnail_images=track_thumbnail_images,
                owned_thumbnails=owned_thumbnails[seg_idx],
            )

        return results  # type: ignore

    def top_quality_embeddings(
        self,
        candidates: List[FaceEmbeddingCandidate],
        limit: int,
    ) -> List[np.ndarray]:
        if limit <= 0:
            return []
        return [
            candidate.embedding
            for candidate in sorted(candidates, key=lambda item: item.quality, reverse=True)[:limit]
        ]

    def cluster_embeddings(self, embeddings: List[np.ndarray]) -> List[Optional[int]]:
        if not embeddings:
            return []
        if len(embeddings) == 1 and self.config.cluster_method != "dbscan":
            return [1]

        X = np.stack(embeddings, axis=0)

        if self.config.cluster_method == "dbscan":
            try:
                from sklearn.cluster import DBSCAN
            except Exception as e:
                raise RuntimeError("cluster_method=dbscan 사용하려면 scikit-learn이 필요합니다.") from e

            model = DBSCAN(
                eps=float(self.config.dbscan_eps),
                min_samples=int(self.config.dbscan_min_samples),
                metric="cosine",
            )
            labels = model.fit_predict(X)

        else:
            try:
                from sklearn.cluster import AgglomerativeClustering
            except Exception as e:
                raise RuntimeError("cluster_method=agglomerative 사용하려면 scikit-learn이 필요합니다.") from e

            model = AgglomerativeClustering(
                n_clusters=None,
                metric="cosine",
                linkage="average",
                distance_threshold=float(self.config.cluster_distance_threshold),
            )
            labels = model.fit_predict(X)

        out: List[Optional[int]] = []
        for lab in labels:
            if int(lab) < 0:
                out.append(None)
            else:
                out.append(int(lab) + 1)

        return out

    def get_face_embedding_from_image_path(self, image_path: str) -> Optional[np.ndarray]:
        # cv2.imread는 Windows에서 한글/유니코드 경로를 처리 못함
        # np.fromfile + cv2.imdecode로 우회
        try:
            buf = np.fromfile(image_path, dtype=np.uint8)
            img = cv2.imdecode(buf, cv2.IMREAD_COLOR)
        except Exception:
            img = None
        if img is None:
            return None
        return self.get_face_embedding(img)

    def average_embeddings(self, embeddings: List[np.ndarray]) -> Optional[np.ndarray]:
        if not embeddings:
            return None
        avg = np.mean(np.stack(embeddings), axis=0)
        return self._l2(avg.astype(np.float32))
