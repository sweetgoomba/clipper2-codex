from dataclasses import replace
import importlib
import numpy as np
import pytest
from face_fixtures import SPACE, sample


def build(samples):
    module=importlib.import_module('clipper_face_core.gallery')
    return module.build_gallery(samples, space=SPACE)


def test_mean_matches_existing_dance():
    vectors=[np.array([1,0],np.float32),np.array([0,1],np.float32)]
    avg=np.mean(np.stack(vectors),axis=0)
    expected=avg/(float(np.linalg.norm(avg))+1e-9)
    g=build([sample('r1',vector=vectors[0]),sample('r2',vector=vectors[1])])
    np.testing.assert_array_equal(g.entries[0].centroid,expected)
    assert g.entries[0].used_sample_ids==('r1','r2')


def test_duplicate_sample_id_is_not_an_extra_vote():
    a,b=sample(),sample('r2',vector=(0,1))
    g=build([a,b])
    d=build([a,a,b])
    assert g.fingerprint==d.fingerprint
    assert len(d.samples)==2


def test_conflicting_sample_id_rejected():
    with pytest.raises(ValueError,match='conflicting_sample_id'):
        build([sample(),sample(label='B')])


def test_gallery_owns_immutable_vectors():
    a=np.array([1,0],np.float32)
    s=sample(vector=a);g=build([s]);stamp=g.fingerprint
    a[:]=[0,1]
    assert g.entries[0].centroid.tolist()==[1,0]
    assert g.fingerprint==stamp
    with pytest.raises(ValueError): g.entries[0].centroid.setflags(write=True)


@pytest.mark.parametrize('vector', [None,(0,0),(2,0),(float('nan'),0),(float('inf'),0),(1,0,0)])
def test_invalid_samples_preserved_without_losing_valid_reference(vector):
    g=build([sample('valid'),sample('bad','B',vector)])
    assert [e.reference_id for e in g.entries]==['A']
    assert g.failures[0].sample_id=='bad'
    assert len(g.samples)==2


def test_all_failed_and_cancelled_means_report_failures():
    with pytest.raises(ValueError,match='no_valid_references') as exc:
        build([sample(vector=None)])
    assert len(exc.value.failures)==1
    g=build([sample('a1','A'),sample('b1','B'),sample('b2','B',(-1,0))])
    assert [e.reference_id for e in g.entries]==['A']
    assert {f.sample_id for f in g.failures}=={'b1','b2'}


def test_mixed_embedding_space_rejected_even_if_one_sample_failed():
    wrong=replace(SPACE,normalization_version='different')
    with pytest.raises(ValueError,match='space_mismatch'):
        build([sample(),sample('r2',vector=None,space=wrong)])


def test_nearly_cancelled_reference_does_not_invalidate_other_references():
    from clipper_face_core import MatchPolicy, match_reference
    from face_fixtures import query
    g = build([sample('a1', 'A'), sample('b1', 'B'),
               sample('b2', 'B', (-1, .0001))])
    assert [entry.reference_id for entry in g.entries] == ['A']
    assert {(f.sample_id, f.reason) for f in g.failures} == {
        ('b1', 'invalid_centroid'), ('b2', 'invalid_centroid')}
    result = match_reference(query(), g, MatchPolicy(.6, 0, 1))
    assert (result.status, result.reference_id) == ('matched', 'A')
