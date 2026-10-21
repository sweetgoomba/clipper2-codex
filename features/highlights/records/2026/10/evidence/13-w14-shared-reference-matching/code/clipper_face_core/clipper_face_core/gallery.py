"""Prepare reference centroids without importing a detector or a consumer plugin."""
from collections import defaultdict
from collections.abc import Sequence
import numpy as np
from .contracts import (EmbeddingSpace, ReferenceSample, ReferenceGallery,
                        GalleryEntry, SampleFailure, fingerprint)
from ._vectors import embedding_failure


class GalleryBuildError(ValueError):
    def __init__(self, reason: str, failures=()):
        super().__init__(reason)
        self.reason = reason
        self.failures = tuple(failures)


def build_gallery(samples: Sequence[ReferenceSample], *, space: EmbeddingSpace) -> ReferenceGallery:
    unique, stamps, groups, failures = [], {}, defaultdict(list), []
    for sample in samples:
        if sample.space != space:
            raise GalleryBuildError('space_mismatch', failures)
        stamp = fingerprint(sample)
        if sample.sample_id in stamps:
            if stamps[sample.sample_id] != stamp:
                raise GalleryBuildError('conflicting_sample_id', failures)
            continue
        stamps[sample.sample_id] = stamp
        unique.append(sample)
        reason = sample.failure or embedding_failure(sample.embedding, space.dimension)
        if reason:
            failures.append(SampleFailure(sample.sample_id, sample.reference_id, reason))
        else:
            groups[sample.reference_id].append(sample)
    entries = []
    for reference_id, items in groups.items():
        mean = np.mean(np.stack([s.embedding for s in items]), axis=0)
        norm = float(np.linalg.norm(mean))
        if not np.isfinite(norm) or norm <= 1e-8:
            failures.extend(SampleFailure(s.sample_id, reference_id, 'invalid_centroid') for s in items)
            continue
        centroid = mean / (norm + 1e-9)
        if embedding_failure(centroid, space.dimension):
            failures.extend(SampleFailure(s.sample_id, reference_id, 'invalid_centroid') for s in items)
            continue
        entries.append(GalleryEntry(reference_id, centroid, tuple(s.sample_id for s in items)))
    if not entries:
        raise GalleryBuildError('no_valid_references', failures)
    return ReferenceGallery(space, tuple(entries), tuple(unique), tuple(failures),
                            'mean_f32_l2_eps1e-9_v1')
