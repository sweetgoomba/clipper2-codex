"""Deterministic, plugin-independent grouping of face observations.

Embeddings may only be compared within one model SHA/config space. Callers must
persist provenance; this module refuses to compare observations from different
spaces. Detection failure and uncertainty are different from an absent face.
"""

from __future__ import annotations

from dataclasses import dataclass
from collections import defaultdict
from typing import Callable, Literal, Sequence
import numpy as np


@dataclass(frozen=True)
class FaceObservation:
    observation_id: str
    track_id: str
    shot_id: str
    time_sec: float
    bbox_px: tuple[int, int, int, int]  # x1, y1, x2, y2 in source pixels
    embedding: np.ndarray | None
    quality: float
    source_sha256: str = ""
    model_sha256: str = ""
    config_sha256: str = ""
    time_base: str = "seconds"
    frame_width: int = 0
    frame_height: int = 0
    version: int = 1
    failure: Literal["none", "alignment", "embedding"] = "none"
    sharpness: float | None = None
    association_uncertain: bool = False

    @property
    def bbox_normalized(self) -> tuple[float, float, float, float] | None:
        if self.frame_width <= 0 or self.frame_height <= 0:
            return None
        x1, y1, x2, y2 = self.bbox_px
        return (x1 / self.frame_width, y1 / self.frame_height,
                x2 / self.frame_width, y2 / self.frame_height)


@dataclass(frozen=True)
class FaceInterval:
    shot_id: str
    start_sec: float
    end_sec: float
    observation_ids: tuple[str, ...]


@dataclass(frozen=True)
class FaceGroup:
    group_id: str
    track_ids: tuple[str, ...]
    observation_ids: tuple[str, ...]
    intervals: tuple[FaceInterval, ...]
    representative_observation_id: str
    status: Literal["grouped", "needs_review"]


def _normalized(vector: np.ndarray) -> np.ndarray:
    vector = np.asarray(vector, dtype=np.float32).reshape(-1)
    norm = float(np.linalg.norm(vector))
    if not np.isfinite(norm) or norm <= 1e-8:
        raise ValueError("Invalid face embedding")
    return vector / norm


def _intervals(observations: list[FaceObservation], gap: float) -> tuple[FaceInterval, ...]:
    by_shot: dict[str, list[FaceObservation]] = defaultdict(list)
    for observation in observations:
        by_shot[observation.shot_id].append(observation)
    intervals: list[FaceInterval] = []
    for shot_id, items in by_shot.items():
        items.sort(key=lambda item: (item.time_sec, item.observation_id))
        run: list[FaceObservation] = []
        for item in items:
            if run and item.time_sec - run[-1].time_sec > gap:
                intervals.append(FaceInterval(shot_id, run[0].time_sec, run[-1].time_sec,
                                              tuple(o.observation_id for o in run)))
                run = []
            run.append(item)
        if run:
            intervals.append(FaceInterval(shot_id, run[0].time_sec, run[-1].time_sec,
                                          tuple(o.observation_id for o in run)))
    return tuple(sorted(intervals, key=lambda item: (item.start_sec, item.shot_id)))


def rank_representatives(observations: Sequence[FaceObservation]) -> list[str]:
    """Order a group's observed faces for primary and replacement images."""
    spaces = {(item.model_sha256, item.config_sha256) for item in observations
              if item.embedding is not None}
    if len(spaces) > 1:
        raise ValueError("Cannot mix face embedding model/config spaces")
    vectors = [_normalized(item.embedding) for item in observations
               if item.embedding is not None]
    weights = [max(.01, item.quality) for item in observations
               if item.embedding is not None]
    center = _normalized(np.average(vectors, axis=0, weights=weights)) if vectors else None

    def score(item: FaceObservation) -> float:
        x1, y1, x2, y2 = item.bbox_px
        # Tiny crops can have high Laplacian variance from compression noise.
        size_factor = min(1.0, max(0, min(x2 - x1, y2 - y1)) / 80.0)
        sharpness = item.sharpness if item.sharpness is not None else item.quality
        similarity = (float(np.dot(_normalized(item.embedding), center))
                      if item.embedding is not None and center is not None else 0.0)
        return .5 * item.quality + .5 * sharpness * size_factor + .15 * similarity

    return [item.observation_id for item in sorted(observations, key=score, reverse=True)]


def group_observations(
    observations: list[FaceObservation], *, cosine_threshold: float = 0.55,
    max_gap_sec: float = 1.5,
    on_intervals_start: Callable[[], None] | None = None,
) -> list[FaceGroup]:
    """Group shot-local tracks, prohibiting co-visible tracks from merging.

    Greedy matching is deliberately conservative. Every observed track remains
    visible, including a track with no usable embedding. A face the detector did
    not find has no observation and cannot be recovered by this API.
    """
    if not 0 <= cosine_threshold <= 1 or max_gap_sec < 0:
        raise ValueError("Invalid grouping configuration")
    spaces = {(o.model_sha256, o.config_sha256) for o in observations if o.embedding is not None}
    if len(spaces) > 1:
        raise ValueError("Cannot mix face embedding model/config spaces")
    by_track: dict[str, list[FaceObservation]] = defaultdict(list)
    for observation in observations:
        by_track[observation.track_id].append(observation)
    track_order = sorted(by_track, key=lambda track: (
        min(o.time_sec for o in by_track[track]), track))

    def centroid(track_ids: list[str]) -> np.ndarray | None:
        vectors: list[np.ndarray] = []
        weights: list[float] = []
        for track in track_ids:
            for item in by_track[track]:
                if item.embedding is None:
                    continue
                vectors.append(_normalized(item.embedding))
                weights.append(max(0.01, item.quality))
        return _normalized(np.average(vectors, axis=0, weights=weights)) if vectors else None

    def co_visible(left: list[str], right: str) -> bool:
        for track in left:
            for a in by_track[track]:
                for b in by_track[right]:
                    if a.shot_id == b.shot_id and abs(a.time_sec - b.time_sec) < 0.001:
                        return True
        return False

    clusters: list[list[str]] = []
    uncertain: set[str] = set()
    for track in track_order:
        vector = centroid([track])
        candidates: list[tuple[float, int]] = []
        if vector is not None:
            for index, cluster in enumerate(clusters):
                other = centroid(cluster)
                if other is not None and not co_visible(cluster, track):
                    score = float(np.dot(vector, other))
                    if score >= cosine_threshold:
                        candidates.append((score, index))
        candidates.sort(reverse=True)
        if vector is None:
            uncertain.add(track)
        elif len(candidates) > 1 and candidates[0][0] - candidates[1][0] < 0.04:
            uncertain.add(track)
        if candidates:
            clusters[candidates[0][1]].append(track)
        else:
            clusters.append([track])

    if on_intervals_start is not None:
        on_intervals_start()
    groups: list[FaceGroup] = []
    for index, tracks in enumerate(clusters, 1):
        items = sorted((o for track in tracks for o in by_track[track]),
                       key=lambda o: (o.time_sec, o.observation_id))
        representative_id = rank_representatives(items)[0]
        groups.append(FaceGroup(
            group_id=f"person_{index:03d}", track_ids=tuple(tracks),
            observation_ids=tuple(o.observation_id for o in items),
            intervals=_intervals(items, max_gap_sec),
            representative_observation_id=representative_id,
            status="needs_review" if len(items) == 1 or any(t in uncertain for t in tracks)
            or any(item.association_uncertain for item in items) else "grouped",
        ))
    return groups
