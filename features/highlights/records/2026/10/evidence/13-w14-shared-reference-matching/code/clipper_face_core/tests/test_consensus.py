from dataclasses import replace
import importlib
import pytest
from face_fixtures import sample, query, SOURCE, SPACE
from clipper_face_core import MatchPolicy, build_gallery, match_reference

G=build_gallery([sample(),sample('r2','B',(0,1))],space=SPACE)
P=MatchPolicy(.6,0,2)


def combine(qs, matches=None, policy=P):
    matches=[match_reference(q,G,policy) for q in qs] if matches is None else matches
    return importlib.import_module('clipper_face_core.consensus').combine_reference_matches('scope',qs,matches,policy)


def test_conflicting_references_are_preserved():
    r=combine([query('a'),query('b',(0,1))])
    assert (r.status,r.reason,r.reference_id)==('ambiguous','conflicting_references',None)
    assert {m.reference_id for m in r.matches}=={'A','B'}
    assert set(dict(r.excluded))=={'a','b'}


def test_support_preserves_failed_and_ambiguous_evidence():
    r=combine([query('a'),query('b'),query('bad',None)])
    assert r.reference_id=='A' and r.used_observation_ids==('a','b')
    assert dict(r.excluded)=={'bad':'missing_embedding'}
    low=combine([query('a'),query('uncertain',association='ambiguous')])
    assert low.status=='ambiguous' and low.reason=='insufficient_support'
    assert len(low.matches)==2


def test_duplicate_observation_is_not_an_extra_vote_and_conflict_rejected():
    a=query()
    r=combine([a,a])
    assert r.reason=='insufficient_support' and len(r.matches)==1
    with pytest.raises(ValueError,match='conflicting_observation_id'):
        combine([a,query(vector=(0,1))])


@pytest.mark.parametrize('change', [dict(source_sha256='e'*64),dict(analysis_id='other'),dict(scope_id='other'),dict(scope_range_seconds=(0,3))])
def test_same_track_number_cannot_mix_sources_or_scopes(change):
    q=replace(query('b'),source=replace(SOURCE,**change))
    with pytest.raises(ValueError): combine([query('a'),q])


def test_gallery_policy_space_or_stale_evidence_cannot_mix():
    qs=[query('a'),query('b')];ms=[match_reference(q,G,P) for q in qs]
    for field in ('gallery_fingerprint','policy_fingerprint','space_fingerprint','evidence_fingerprint'):
        with pytest.raises(ValueError): combine(qs,[ms[0],replace(ms[1],**{field:'e'*64})])
    with pytest.raises(ValueError): combine([query('a',(0,1)),qs[1]],ms)
    with pytest.raises(ValueError): combine(qs,ms[:1])


@pytest.mark.parametrize('qs,status,reason',[
    ([], 'invalid','no_evidence'),
    ([query(vector=None)],'invalid','no_valid_evidence'),
    ([query(vector=(-1,0))],'unmatched','distance_exceeded'),
    ([query(association='ambiguous')],'ambiguous','insufficient_support'),
])
def test_empty_and_nonmatching_scopes_remain_visible(qs,status,reason):
    r=combine(qs)
    assert (r.status,r.reason)==(status,reason)
    assert len(r.matches)==len(qs)


def test_independent_scopes_do_not_change_previous_result():
    qs=[query('a'),query('b')]
    expected=combine(qs)
    combine([query('c',(0,1)),query('d',(0,1))])
    assert combine(qs)==expected
