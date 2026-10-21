"""Combine only consumer-declared same-person observations, preserving conflicts."""
from collections.abc import Sequence
from .contracts import QueryEvidence, ReferenceMatch, MatchPolicy, ConsensusResult


def combine_reference_matches(scope_id: str, evidence: Sequence[QueryEvidence],
                              matches: Sequence[ReferenceMatch], policy: MatchPolicy) -> ConsensusResult:
    if not isinstance(scope_id, str) or not scope_id.strip():
        raise ValueError('empty_scope_id')
    observations, results = {}, {}
    scope_key = None
    for q in evidence:
        if q.observation_id in observations and observations[q.observation_id].fingerprint != q.fingerprint:
            raise ValueError('conflicting_observation_id')
        s = q.source
        key = (s.analysis_id, s.source_sha256, s.scope_id, s.scope_range_seconds)
        if s.scope_id != scope_id or (scope_key is not None and key != scope_key):
            raise ValueError('source_or_scope_mismatch')
        scope_key = key
        observations[q.observation_id] = q
    for match in matches:
        previous = results.get(match.observation_id)
        if previous is not None and previous != match:
            raise ValueError('conflicting_match')
        results[match.observation_id] = match
    if observations.keys() != results.keys():
        raise ValueError('missing_evidence_or_match')
    ordered = tuple(results[id] for id in observations)
    gallery_id, space_id = None, None
    for m in ordered:
        q = observations[m.observation_id]
        if (m.policy_fingerprint != policy.fingerprint or m.space_fingerprint != q.space.fingerprint
                or m.evidence_fingerprint != q.fingerprint
                or (gallery_id is not None and m.gallery_fingerprint != gallery_id)
                or (space_id is not None and m.space_fingerprint != space_id)):
            raise ValueError('match_provenance_mismatch')
        if m.status not in ('matched', 'ambiguous', 'unmatched', 'invalid') or (
                (m.status == 'matched') != (m.reference_id is not None)):
            raise ValueError('invalid_match_state')
        gallery_id, space_id = m.gallery_fingerprint, m.space_fingerprint
    support = {m.reference_id for m in ordered if m.status == 'matched'}
    selected = None
    if not ordered:
        status, reason = 'invalid', 'no_evidence'
    elif len(support) > 1:
        status, reason = 'ambiguous', 'conflicting_references'
    elif len(support) == 1 and sum(m.status == 'matched' for m in ordered) >= policy.minimum_support:
        status, reason, selected = 'matched', 'supported_reference', next(iter(support))
    elif all(m.status == 'invalid' for m in ordered):
        status, reason = 'invalid', 'no_valid_evidence'
    elif all(m.status in ('invalid', 'unmatched') for m in ordered):
        status, reason = 'unmatched', 'distance_exceeded'
    else:
        status, reason = 'ambiguous', 'insufficient_support'
    used = tuple(m.observation_id for m in ordered if selected is not None and m.reference_id == selected)
    excluded = tuple((m.observation_id, reason if m.status == 'matched' else m.reason)
                     for m in ordered if m.observation_id not in used)
    return ConsensusResult(scope_id, status, selected, reason, ordered, used, excluded,
                           gallery_id or '', policy.fingerprint)
