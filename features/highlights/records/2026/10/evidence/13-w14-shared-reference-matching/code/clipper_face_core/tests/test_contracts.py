from dataclasses import replace
import importlib
import numpy as np
import pytest


def api():
    return importlib.import_module('clipper_face_core.contracts')


def space():
    return api().EmbeddingSpace('a'*64, 'align1', 'bgr1', 'l2epsilon1', 2, 'backend1')


def source(**kw):
    args = dict(analysis_id='run1', source_sha256='b'*64, observation_version=1,
                detector_sha256='c'*64, config_sha256='d'*64, adapter_version='adapter1',
                time_kind='derived_seconds', time_seconds=1.0, pts=None, time_base=None,
                frame_index=30, width=100, height=100, rotation=0, bbox_px=(10,20,50,80),
                track_id='track1', scope_id='scope1', scope_range_seconds=(0.0,2.0))
    args.update(kw)
    return api().SourceEvidence(**args)


def test_space_captures_preprocessing_and_rejects_empty_identity():
    a=space()
    for field in ['alignment_version','preprocessing_version','normalization_version','backend_version']:
        assert a.fingerprint != replace(a, **{field:'other'}).fingerprint
    with pytest.raises(ValueError): replace(a, recognizer_sha256='')
    with pytest.raises(ValueError): replace(a, dimension=True)


def test_coordinates_and_time_never_fabricate_pts():
    a=source()
    assert a.bbox_normalized == (0.1,0.2,0.5,0.8)
    assert a.pts is None and a.time_kind == 'derived_seconds'
    pts=source(time_kind='pts', pts=90, time_base=(1,90))
    with pytest.raises(ValueError): replace(pts,time_base=(1,0))
    with pytest.raises(ValueError): replace(pts,time_seconds=3)
    with pytest.raises(ValueError): replace(a,bbox_px=(0,0,101,100))
    with pytest.raises(ValueError): replace(a,scope_range_seconds=(0,1))
    with pytest.raises(ValueError): replace(a,rotation=45)


@pytest.mark.parametrize('values', [(0.6,0,True),(-1,0,1),(0.6,float('nan'),1),(0.6,0,0)])
def test_invalid_policy_rejected(values):
    with pytest.raises(ValueError): api().MatchPolicy(*values)


def test_vectors_own_immutable_storage_and_failures_remain_representable():
    a=np.array([1.,0.],np.float32)
    sample=api().ReferenceSample('r1','A',source(),space(),a,None)
    a[0]=0
    assert sample.embedding.tolist()==[1.,0.]
    with pytest.raises(ValueError): sample.embedding.setflags(write=True)
    q=api().QueryEvidence('q',source(),space(),np.array([np.nan,0]),'confirmed',None,())
    assert np.isnan(q.embedding[0])  # matching must return invalid, not erase this observation
