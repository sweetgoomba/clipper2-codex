"""Model files and legacy detection DTO; no backend import."""
from dataclasses import dataclass
from pathlib import Path
import hashlib
import numpy as np

@dataclass(frozen=True)
class ModelFiles:
    detector: Path
    recognizer: Path
    detector_sha256: str
    recognizer_sha256: str

    def verify(self) -> None:
        for path, expected in ((self.detector, self.detector_sha256),
                               (self.recognizer, self.recognizer_sha256)):
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != expected:
                raise ValueError(f"Face model hash mismatch: {path.name}")


@dataclass(frozen=True)
class FaceDetection:
    bbox_px: tuple[int, int, int, int]
    embedding: np.ndarray | None
    quality: float
    score: float
    failure: str
    sharpness: float | None = None


