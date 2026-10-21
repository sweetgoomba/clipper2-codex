import numpy as np

from clipper_face_core.opencv_backend import OpenCvFaceBackend


class _SingleFaceDetector:
    def setInputSize(self, size):
        assert size == (160, 160)

    def detect(self, frame):
        face = np.array([[0, 0, 160, 160, 40, 40, 120, 40, 80, 80,
                          48, 116, 112, 116, .99]], dtype=np.float32)
        return 1, face


class _Recognizer:
    def alignCrop(self, frame, face):
        return frame

    def feature(self, crop):
        return np.array([1.0, 0.0], dtype=np.float32)


def test_subtitle_edges_do_not_make_a_blurred_face_sharp():
    # Both frames have identical high-frequency text-like edges below the face.
    # Only the eye/upper-face region differs. The detector/recognizer are replaced
    # at the model boundary; the real backend's quality calculation is exercised.
    blurred = np.full((160, 160, 3), 128, dtype=np.uint8)
    blurred[120:, ::2] = 0
    blurred[120:, 1::2] = 255
    clear = blurred.copy()
    checker = ((np.indices((70, 112)).sum(axis=0) % 2) * 255).astype(np.uint8)
    clear[20:90, 24:136] = checker[..., None]
    backend = object.__new__(OpenCvFaceBackend)
    backend.detector = _SingleFaceDetector()
    backend.recognizer = _Recognizer()

    [blurred_face] = backend.detect(blurred)
    [clear_face] = backend.detect(clear)

    assert blurred_face.sharpness < 0.1
    assert clear_face.sharpness > 0.8
