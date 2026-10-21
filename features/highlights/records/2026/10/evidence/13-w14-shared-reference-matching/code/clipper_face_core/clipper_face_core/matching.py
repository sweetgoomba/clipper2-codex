"""Independent reference comparison: no cross-query allocation or clustering."""
import numpy as np
from .contracts import QueryEvidence, ReferenceGallery, MatchPolicy, ReferenceMatch, CandidateDistance
from ._vectors import embedding_failure


def match_reference(query: QueryEvidence, gallery: ReferenceGallery,
                    policy: MatchPolicy) -> ReferenceMatch:
    def result(status, reason, candidates=(), margin=None, reference_id=None):
        return ReferenceMatch(query.observation_id, status, reference_id, candidates, margin,
                              reason, query.space.fingerprint, gallery.fingerprint,
                              policy.fingerprint, query.fingerprint)

    if query.space != gallery.space:
        return result('invalid', 'space_mismatch')
    reason = query.failure or embedding_failure(query.embedding, query.space.dimension)
    if reason:
        return result('invalid', reason)
    ids = [e.reference_id for e in gallery.entries]
    if (not ids or len(ids) != len(set(ids)) or any(
            embedding_failure(e.centroid, gallery.space.dimension) for e in gallery.entries)):
        return result('invalid', 'invalid_gallery')
    candidates = tuple(sorted((CandidateDistance(e.reference_id,
        max(0.0, min(2.0, 1.0 - float(np.dot(query.embedding, e.centroid)))))
        for e in gallery.entries), key=lambda c: (c.distance, c.reference_id)))
    first = candidates[0]
    margin = candidates[1].distance - first.distance if len(candidates) > 1 else None
    if query.association != 'confirmed':
        return result('ambiguous', 'association_' + query.association, candidates, margin)
    if first.distance > policy.max_distance:
        return result('unmatched', 'distance_exceeded', candidates, margin)
    if margin is not None and (margin == 0 or margin < policy.min_margin):
        return result('ambiguous', 'tied_references' if margin == 0 else 'insufficient_margin',
                      candidates, margin)
    return result('matched', 'single_reference_distance_only' if margin is None else 'accepted',
                  candidates, margin, first.reference_id)
