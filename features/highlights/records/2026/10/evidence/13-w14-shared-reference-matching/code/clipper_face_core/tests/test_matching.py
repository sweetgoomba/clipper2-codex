from dataclasses import replace, asdict
import importlib
import json
import numpy as np
import pytest
from face_fixtures import sample, query, SPACE
from clipper_face_core import build_gallery, MatchPolicy


def match(q, g=None, p=None):
    g=build_gallery([sample(),sample('r2','B',(0,1))],space=SPACE) if g is None else g
    return importlib.import_module('clipper_face_core.matching').match_reference(q,g,p or MatchPolicy(.6,0,1))


def test_repeated_identity_is_independent_of_other_queries_and_call_order():
    qs=[query('q1'),query('q2'),query('q3',(0,1))]
    original=match(qs[0])
    forward=[match(q) for q in qs]
    reverse=[match(q) for q in reversed(qs)]
    assert [r.reference_id for r in forward]==['A','A','B']
    assert forward==list(reversed(reverse))
    assert original==forward[0]


def test_distance_and_margin_boundaries_and_tie():
    g=build_gallery([sample()],space=SPACE)
    assert match(query(vector=(0,1)),g,MatchPolicy(1,0,1)).status=='matched'
    assert match(query(vector=(0,1)),g,MatchPolicy(.99,0,1)).status=='unmatched'
    assert match(query(),p=MatchPolicy(.6,1,1)).status=='matched' # distances 0 and 1
    tie=query(vector=np.array([1,1],np.float32)/np.sqrt(np.float32(2)))
    result=match(tie)
    assert result.status=='ambiguous' and result.margin==0 and result.reference_id is None


def test_single_reference_still_requires_distance():
    g=build_gallery([sample()],space=SPACE)
    result=match(query(),g)
    assert result.status=='matched' and result.margin is None
    assert result.reason=='single_reference_distance_only'
    assert match(query(vector=(-1,0)),g).status=='unmatched'


@pytest.mark.parametrize('values', [dict(vector=None),dict(vector=(0,0)),dict(vector=(2,0)),
    dict(vector=(np.nan,0)),dict(vector=(np.inf,0)),dict(vector=(1,0,0)),
    dict(space=replace(SPACE,normalization_version='different')),dict(failure='align_failed')])
def test_invalid_query_preserved(values):
    r=match(query(**values))
    assert r.status=='invalid' and r.reference_id is None
    assert r.observation_id=='q1' and r.reason and r.evidence_fingerprint


@pytest.mark.parametrize('association',['ambiguous','unassigned'])
def test_uncertain_face_ownership_does_not_get_name_but_retains_distances(association):
    r=match(query(association=association))
    assert r.status=='ambiguous' and r.reference_id is None
    assert [(v.reference_id,v.distance) for v in r.candidates]==[('A',0.0),('B',1.0)]


def test_results_bind_policy_gallery_and_evidence_without_embedding_payload():
    r=match(query())
    assert r.policy_fingerprint!=match(query(),p=MatchPolicy(.5,0,1)).policy_fingerprint
    assert r.evidence_fingerprint!=match(query(vector=(0,1))).evidence_fingerprint
    assert 'embedding' not in json.dumps(asdict(r))


def test_malformed_gallery_is_not_compared():
    g=build_gallery([sample()],space=SPACE)
    assert match(query(),replace(g,entries=())).status=='invalid'
    bad=replace(g.entries[0],centroid=np.array([0,0],np.float32))
    assert match(query(),replace(g,entries=(bad,))).status=='invalid'
