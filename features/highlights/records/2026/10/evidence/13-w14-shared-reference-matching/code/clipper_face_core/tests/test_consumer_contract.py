from dataclasses import replace
import importlib.util
from pathlib import Path
import pytest
from face_fixtures import sample, query, SOURCE, SPACE
from clipper_face_core import MatchPolicy


def classify(qs):
    path=Path(__file__).parents[1]/'examples/reference_matching.py'
    spec=importlib.util.spec_from_file_location('face_consumer_example',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.classify_selected_faces([sample(),sample('r2','B',(0,1))],qs,space=SPACE,policy=MatchPolicy(.6,0,1))


def test_consumer_keeps_intervals_ids_uncertainty_and_conflicts():
    def at(q,scope):return replace(q,source=replace(SOURCE,scope_id=scope,scope_range_seconds=None if scope is None else (0,2)))
    qs=[at(query('a1'),'a'),at(query('a2'),'b'),at(query('unknown',association='unassigned'),None),
        at(query('bad',None),None),at(query('conflict1'),'c'),at(query('conflict2',(0,1)),'c')]
    before=[q.fingerprint for q in qs]
    gallery,results,scopes=classify(qs)
    assert [q.fingerprint for q in qs]==before
    assert [r.observation_id for r in results]==[q.observation_id for q in qs]
    assert [r.status for r in results]==['matched','matched','ambiguous','invalid','matched','matched']
    assert [(s.scope_id,s.reference_id,s.status) for s in scopes]==[('a','A','matched'),('b','A','matched'),('c',None,'ambiguous')]
    assert len(gallery.entries)==2


def test_consumer_rejects_cross_source_batch():
    with pytest.raises(ValueError,match='same analysis/source'):
        classify([query('a'),query('b',source=replace(SOURCE,source_sha256='e'*64))])


@pytest.mark.parametrize('scopes', [(None, None), ('first', 'second')])
def test_consumer_rejects_conflicting_observation_ids_across_batch(scopes):
    qs = [query('same', vector, source=replace(SOURCE, scope_id=scope,
              scope_range_seconds=None if scope is None else (0, 2)))
          for vector, scope in zip([(1, 0), (0, 1)], scopes)]
    with pytest.raises(ValueError, match='conflicting observation ID'):
        classify(qs)


def test_consumer_deduplicates_identical_observations():
    q = query('same')
    _, results, scopes = classify([q, q])
    assert len(results) == 1
    assert results[0].observation_id == 'same'
    assert len(scopes) == 1
    assert scopes[0].used_observation_ids == ('same',)
