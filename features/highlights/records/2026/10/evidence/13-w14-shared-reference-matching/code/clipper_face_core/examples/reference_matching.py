"""Adapter example. The consumer supplies selected faces and same-person scopes."""
from collections import defaultdict
from collections.abc import Sequence
from clipper_face_core import (
    ReferenceSample, QueryEvidence, EmbeddingSpace, MatchPolicy, ReferenceGallery,
    ReferenceMatch, ConsensusResult, build_gallery, match_reference, combine_reference_matches,
)


def classify_selected_faces(
    references: Sequence[ReferenceSample], queries: Sequence[QueryEvidence], *,
    space: EmbeddingSpace, policy: MatchPolicy,
) -> tuple[ReferenceGallery, tuple[ReferenceMatch, ...], tuple[ConsensusResult, ...]]:
    if len({(q.source.analysis_id, q.source.source_sha256) for q in queries}) > 1:
        raise ValueError('Example requires the same analysis/source per query batch')
    unique = {}
    for query in queries:
        previous = unique.get(query.observation_id)
        if previous is not None and previous.fingerprint != query.fingerprint:
            raise ValueError('conflicting observation ID within query batch')
        unique.setdefault(query.observation_id, query)
    queries = tuple(unique.values())
    gallery = build_gallery(references, space=space)
    results = tuple(match_reference(q, gallery, policy) for q in queries)
    groups = defaultdict(list)
    for q, result in zip(queries, results):
        if q.source.scope_id is not None:
            groups[q.source.scope_id].append((q, result))
    scopes = tuple(combine_reference_matches(id, [q for q, _ in rows], [m for _, m in rows], policy)
                   for id, rows in groups.items())
    return gallery, results, scopes
