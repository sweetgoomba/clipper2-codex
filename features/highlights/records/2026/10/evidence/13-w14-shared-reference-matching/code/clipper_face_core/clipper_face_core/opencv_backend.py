"""Optional OpenCV YuNet/SFace backend for all-face observations.

No model download happens here. Plugins decide when/how licensed model assets are
prepared and pass verified files. Replacing the backend requires a new model hash,
embedding cache namespace and calibrated threshold; old vectors must not mix.
"""

from __future__ import annotations

import hashlib
try:
    import cv2
except ImportError as exc:
    raise ImportError("Install clipper-face-core[opencv] in the consuming plugin environment") from exc
from .backend_types import ModelFiles, FaceDetection
import numpy as np


class OpenCvFaceBackend:
    backend_id = "opencv-yunet-2023mar+sface-2021dec+focus-v2"

    def __init__(self, files: ModelFiles, *, score_threshold: float = 0.6,
                 nms_threshold: float = 0.3, top_k: int = 5000):
        files.verify()
        self.model_sha256 = files.recognizer_sha256
        self.config_sha256 = hashlib.sha256(
            f"{self.backend_id}:{score_threshold}:{nms_threshold}:{top_k}".encode()
        ).hexdigest()
        empty = np.empty(0, dtype=np.uint8)
        self.detector = cv2.FaceDetectorYN.create(
            "onnx", np.frombuffer(files.detector.read_bytes(), np.uint8), empty,
            (320, 320), score_threshold, nms_threshold, top_k,
        )
        self.recognizer = cv2.FaceRecognizerSF.create(
            "onnx", np.frombuffer(files.recognizer.read_bytes(), np.uint8), empty,
        )

    def detect(self, frame_bgr: np.ndarray) -> list[FaceDetection]:
        if frame_bgr is None or frame_bgr.size == 0:
            return []
        height, width = frame_bgr.shape[:2]
        self.detector.setInputSize((width, height))
        _, faces = self.detector.detect(frame_bgr)
        results: list[FaceDetection] = []
        for raw in faces if faces is not None else []:
            face = np.asarray(raw, dtype=np.float32)
            x, y, w, h = (float(v) for v in face[:4])
            bbox = (max(0, int(x)), max(0, int(y)),
                    min(width, int(x + w)), min(height, int(y + h)))
            if bbox[2] <= bbox[0] or bbox[3] <= bbox[1]:
                continue
            score = float(face[-1])
            crop = frame_bgr[bbox[1]:bbox[3], bbox[0]:bbox[2]]
            blur = min(1.0, float(cv2.Laplacian(cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY),
                                                cv2.CV_64F).var()) / 150.0)
            crop_height, crop_width = crop.shape[:2]
            if min(crop_height, crop_width) < 8:
                focus = 0.0
            else:
                # Bottom edges may be subtitles or clothing rather than a sharp face.
                upper_face = crop[int(crop_height * .12):int(crop_height * .55),
                                  int(crop_width * .13):int(crop_width * .87)]
                focus = min(1.0, float(cv2.Laplacian(
                    cv2.cvtColor(upper_face, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var()) / 150.0)
            size = min(1.0, (w * h) / max(1.0, width * height) * 12.0)
            # Landmark symmetry is a limited proxy for frontal/unoccluded faces.
            eyes = face[4:8].reshape(2, 2)
            nose = face[8:10]
            eye_mid = eyes.mean(axis=0)
            symmetry = 1.0 - min(1.0, abs(float(nose[0] - eye_mid[0])) / max(1.0, w / 2))
            quality = max(0.0, min(1.0, .4 * score + .25 * blur + .2 * size + .15 * symmetry))
            try:
                aligned = self.recognizer.alignCrop(frame_bgr, face)
                vector = np.asarray(self.recognizer.feature(aligned), np.float32).reshape(-1)
                norm = float(np.linalg.norm(vector))
                if norm <= 1e-8:
                    raise ValueError("empty embedding")
                embedding, failure = vector / norm, "none"
            except (cv2.error, ValueError):
                embedding, failure = None, "embedding"
            results.append(FaceDetection(bbox, embedding, quality, score, failure, focus))
        return results
