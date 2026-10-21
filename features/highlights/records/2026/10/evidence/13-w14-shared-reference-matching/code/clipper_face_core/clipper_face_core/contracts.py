"""Versioned, plugin-neutral reference matching contracts. No model imports."""
from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
import hashlib
import json
import math
import re
from typing import Literal
import numpy as np

Status = Literal['matched', 'ambiguous', 'unmatched', 'invalid']


def _text(value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Expected non-empty identifier')


def _sha(value: str) -> None:
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):
        raise ValueError('Expected lowercase SHA-256')


def _integer(value: int, minimum: int) -> None:
    if type(value) is not int or value < minimum:
        raise ValueError('Invalid integer')


def _finite(value: float) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _immutable(vector: np.ndarray | None) -> np.ndarray | None:
    if vector is None:
        return None
    a = np.asarray(vector, dtype='<f4')
    return np.frombuffer(a.tobytes(), dtype='<f4').reshape(a.shape)


def _payload(value):
    if isinstance(value, np.ndarray):
        return {'shape': list(value.shape), 'f32_sha256': hashlib.sha256(value.tobytes()).hexdigest()}
    if is_dataclass(value):
        return {f.name: _payload(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, dict):
        return {k: _payload(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_payload(v) for v in value]
    return value


def fingerprint(value) -> str:
    raw = json.dumps({'schema': 'face_matching_v1', 'value': _payload(value)},
                     sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


@dataclass(frozen=True)
class EmbeddingSpace:
    recognizer_sha256: str
    alignment_version: str
    preprocessing_version: str
    normalization_version: str
    dimension: int
    backend_version: str
    metric: str = 'cosine_distance'

    def __post_init__(self):
        _sha(self.recognizer_sha256)
        for name in ('alignment_version', 'preprocessing_version', 'normalization_version', 'backend_version'):
            _text(getattr(self, name))
        _integer(self.dimension, 1)
        if self.metric != 'cosine_distance':
            raise ValueError('Unsupported metric')

    @property
    def fingerprint(self):
        return fingerprint(self)


@dataclass(frozen=True)
class SourceEvidence:
    analysis_id: str
    source_sha256: str
    observation_version: int
    detector_sha256: str
    config_sha256: str
    adapter_version: str
    time_kind: Literal['pts', 'derived_seconds', 'still_image']
    time_seconds: float | None
    pts: int | None
    time_base: tuple[int, int] | None
    frame_index: int | None
    width: int
    height: int
    rotation: int
    bbox_px: tuple[float, float, float, float] | None
    track_id: str | None
    scope_id: str | None
    scope_range_seconds: tuple[float, float] | None

    def __post_init__(self):
        for v in (self.analysis_id, self.adapter_version):
            _text(v)
        for v in (self.source_sha256, self.detector_sha256, self.config_sha256):
            _sha(v)
        for v in (self.observation_version, self.width, self.height):
            _integer(v, 1)
        if type(self.rotation) is not int or self.rotation not in (0, 90, 180, 270):
            raise ValueError('Invalid display rotation')
        if self.frame_index is not None:
            _integer(self.frame_index, 0)
        for name in ('track_id', 'scope_id'):
            if getattr(self, name) is not None:
                _text(getattr(self, name))
        for name in ('bbox_px', 'time_base', 'scope_range_seconds'):
            if getattr(self, name) is not None:
                object.__setattr__(self, name, tuple(getattr(self, name)))
        if self.time_kind == 'pts':
            if type(self.pts) is not int or self.time_base is None or len(self.time_base) != 2:
                raise ValueError('PTS requires integer timestamp and rational time base')
            for v in self.time_base:
                _integer(v, 1)
            expected = self.pts * self.time_base[0] / self.time_base[1]
            if not _finite(self.time_seconds) or not math.isclose(self.time_seconds, expected, abs_tol=1e-9):
                raise ValueError('PTS and seconds disagree')
        elif self.time_kind == 'derived_seconds':
            if not _finite(self.time_seconds) or self.pts is not None or self.time_base is not None:
                raise ValueError('Derived seconds cannot claim source PTS')
        elif self.time_kind == 'still_image':
            if any(v is not None for v in (self.time_seconds, self.pts, self.time_base, self.frame_index)):
                raise ValueError('Still image cannot claim video time')
        else:
            raise ValueError('Invalid time kind')
        if self.bbox_px is not None:
            if len(self.bbox_px) != 4 or not all(_finite(v) for v in self.bbox_px):
                raise ValueError('Invalid bbox')
            x1, y1, x2, y2 = self.bbox_px
            if not (0 <= x1 < x2 <= self.width and 0 <= y1 < y2 <= self.height):
                raise ValueError('Bbox outside display frame')
        if self.scope_range_seconds is not None:
            r = self.scope_range_seconds
            if (not self.scope_id or len(r) != 2 or not all(_finite(v) for v in r)
                    or self.time_seconds is None or not r[0] <= self.time_seconds < r[1]):
                raise ValueError('Observation outside declared scope')

    @property
    def bbox_normalized(self):
        if self.bbox_px is None:
            return None
        x1, y1, x2, y2 = self.bbox_px
        return x1 / self.width, y1 / self.height, x2 / self.width, y2 / self.height


@dataclass(frozen=True, eq=False)
class ReferenceSample:
    sample_id: str
    reference_id: str
    source: SourceEvidence
    space: EmbeddingSpace
    embedding: np.ndarray | None = field(repr=False)
    failure: str | None

    def __post_init__(self):
        _text(self.sample_id)
        _text(self.reference_id)
        object.__setattr__(self, 'embedding', _immutable(self.embedding))
        if self.failure is not None:
            _text(self.failure)


@dataclass(frozen=True, eq=False)
class QueryEvidence:
    observation_id: str
    source: SourceEvidence
    space: EmbeddingSpace
    embedding: np.ndarray | None = field(repr=False)
    association: Literal['confirmed', 'ambiguous', 'unassigned']
    failure: str | None
    quality: tuple[tuple[str, float], ...]

    def __post_init__(self):
        _text(self.observation_id)
        if self.association not in ('confirmed', 'ambiguous', 'unassigned'):
            raise ValueError('Invalid association')
        if self.failure is not None:
            _text(self.failure)
        object.__setattr__(self, 'embedding', _immutable(self.embedding))
        object.__setattr__(self, 'quality', tuple(tuple(v) for v in self.quality))
        for key, value in self.quality:
            _text(key)
            if not _finite(value):
                raise ValueError('Invalid quality value')

    @property
    def fingerprint(self):
        return fingerprint(self)


@dataclass(frozen=True)
class MatchPolicy:
    max_distance: float
    min_margin: float
    minimum_support: int

    def __post_init__(self):
        for v in (self.max_distance, self.min_margin):
            if not _finite(v) or not 0 <= v <= 2:
                raise ValueError('Cosine distance policy must be within [0,2]')
        _integer(self.minimum_support, 1)

    @property
    def fingerprint(self):
        return fingerprint(self)


@dataclass(frozen=True)
class SampleFailure:
    sample_id: str
    reference_id: str
    reason: str


@dataclass(frozen=True, eq=False)
class GalleryEntry:
    reference_id: str
    centroid: np.ndarray = field(repr=False)
    used_sample_ids: tuple[str, ...]

    def __post_init__(self):
        _text(self.reference_id)
        object.__setattr__(self, 'centroid', _immutable(self.centroid))
        object.__setattr__(self, 'used_sample_ids', tuple(self.used_sample_ids))


@dataclass(frozen=True)
class ReferenceGallery:
    space: EmbeddingSpace
    entries: tuple[GalleryEntry, ...]
    samples: tuple[ReferenceSample, ...]
    failures: tuple[SampleFailure, ...]
    aggregation_version: str

    def __post_init__(self):
        for name in ('entries', 'samples', 'failures'):
            object.__setattr__(self, name, tuple(getattr(self, name)))
        _text(self.aggregation_version)

    @property
    def fingerprint(self):
        return fingerprint(self)


@dataclass(frozen=True)
class CandidateDistance:
    reference_id: str
    distance: float


@dataclass(frozen=True)
class ReferenceMatch:
    observation_id: str
    status: Status
    reference_id: str | None
    candidates: tuple[CandidateDistance, ...]
    margin: float | None
    reason: str
    space_fingerprint: str
    gallery_fingerprint: str
    policy_fingerprint: str
    evidence_fingerprint: str


@dataclass(frozen=True)
class ConsensusResult:
    scope_id: str
    status: Status
    reference_id: str | None
    reason: str
    matches: tuple[ReferenceMatch, ...]
    used_observation_ids: tuple[str, ...]
    excluded: tuple[tuple[str, str], ...]
    gallery_fingerprint: str
    policy_fingerprint: str
