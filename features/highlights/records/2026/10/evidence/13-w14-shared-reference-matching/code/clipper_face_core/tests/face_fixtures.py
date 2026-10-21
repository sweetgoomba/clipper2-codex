from dataclasses import replace
import numpy as np
from clipper_face_core.contracts import EmbeddingSpace, SourceEvidence, ReferenceSample, QueryEvidence

SPACE=EmbeddingSpace('a'*64,'align','bgr','l2_eps1e-9',2,'test')
SOURCE=SourceEvidence('run','b'*64,1,'c'*64,'d'*64,'test','derived_seconds',1.0,None,None,30,100,100,0,(10,20,50,80),'track','scope',(0,2))


def sample(id='r1', label='A', vector=(1,0), **kw):
    values=dict(sample_id=id,reference_id=label,source=SOURCE,space=SPACE,
                embedding=None if vector is None else np.array(vector,np.float32),failure=None)
    values.update(kw)
    return ReferenceSample(**values)


def query(id='q1', vector=(1,0), **kw):
    values=dict(observation_id=id,source=SOURCE,space=SPACE,
                embedding=None if vector is None else np.array(vector,np.float32),association='confirmed',failure=None,quality=())
    values.update(kw)
    return QueryEvidence(**values)
