from dataclasses import asdict
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys
import numpy as np
import pytest
from clipper_face_core import EmbeddingSpace, SourceEvidence, MatchPolicy

SPACE=EmbeddingSpace('a'*64,'align','bgr','l2eps',2,'test')
SOURCE=SourceEvidence('run','b'*64,1,'c'*64,'d'*64,'adapter','derived_seconds',1,None,None,30,100,100,0,(0,0,10,10),None,None,None)


def fixture(tmp_path):
    module=importlib.import_module('evaluation.reference_matching.manifest')
    np.savez(tmp_path/'references.npz',a=np.array([1,0],np.float32),b=np.array([0,1],np.float32))
    np.savez(tmp_path/'queries.npz',ok=[1,0],wrong=[0,1],far=[-1,0],uncertain=[1,0])
    def record(id,key,**kw):
        return dict(id=id,embedding_key=key,source=asdict(SOURCE),space_fingerprint=SPACE.fingerprint,**kw)
    data={'references':[record('a','a',reference_id='A'),record('b','b',reference_id='B')],
          'queries':[record('ok','ok',expected_reference='A'),record('wrong','wrong',expected_reference='A'),
                     record('far','far',expected_reference='A'),record('uncertain','uncertain',expected_reference='A',association='ambiguous'),
                     record('failed',None,expected_reference='A',failure='no_detection')],
          'scopes':[]}
    for row in data['queries']:
        row.setdefault('association', 'confirmed')
    (tmp_path/'dataset.json').write_text(json.dumps(data))
    (tmp_path/'source.bin').write_bytes(b'fixed local source')
    entries={name:{'path':str(tmp_path/f),'sha256':hashlib.sha256((tmp_path/f).read_bytes()).hexdigest()} for name,f in
             [('references','references.npz'),('queries','queries.npz'),('dataset','dataset.json'),('source','source.bin')]}
    plan={'schema':'reference_replay_v1','space':asdict(SPACE),'policy':asdict(MatchPolicy(.6,0,1)),
          'inputs':entries,'code':module.code_inventory(), 'label_limitation':'synthetic test only',
          'association_basis':'consumer-provided fixture',
          'limits':{'wall_seconds':120,'rss_bytes':2147483648,'output_bytes':26214400}}
    path=tmp_path/'manifest.json';path.write_text(json.dumps(plan));return path,data,plan


def run(path,out):
    return importlib.import_module('evaluation.reference_matching.replay').run_replay(path,out)


def test_replay_counts_all_outcomes_without_loading_models(tmp_path):
    path,_,_=fixture(tmp_path)
    r=run(path,tmp_path/'out')
    assert r['counts']=={'total':5,'correct':1,'wrong':1,'unmatched':1,'ambiguous':1,'invalid':1,'unlabelled':0}
    saved=json.loads((tmp_path/'out/report.json').read_text())
    assert saved['model_calls']==0 and len(saved['rows'])==5
    assert all('embedding' not in row for row in saved['rows'])


def test_changed_source_rejected_before_output(tmp_path):
    path,_,_=fixture(tmp_path);(tmp_path/'source.bin').write_bytes(b'changed')
    with pytest.raises(ValueError,match='hash'):run(path,tmp_path/'out')
    assert not (tmp_path/'out').exists()


def test_existing_output_is_never_overwritten(tmp_path):
    path,_,_=fixture(tmp_path);out=tmp_path/'out';out.mkdir();(out/'keep').write_text('user')
    with pytest.raises(FileExistsError):run(path,out)
    assert (out/'keep').read_text()=='user'


def test_dataset_space_cannot_be_assumed_from_manifest(tmp_path):
    path,data,plan=fixture(tmp_path)
    data['queries'][0]['space_fingerprint']='e'*64
    dataset=tmp_path/'dataset.json';dataset.write_text(json.dumps(data))
    plan['inputs']['dataset']['sha256']=hashlib.sha256(dataset.read_bytes()).hexdigest();path.write_text(json.dumps(plan))
    with pytest.raises(ValueError,match='space'):run(path,tmp_path/'out')


def test_pickle_arrays_rejected(tmp_path):
    path,_,plan=fixture(tmp_path)
    np.savez(tmp_path/'queries.npz',ok=np.array([object()],dtype=object))
    plan['inputs']['queries']['sha256']=hashlib.sha256((tmp_path/'queries.npz').read_bytes()).hexdigest();path.write_text(json.dumps(plan))
    with pytest.raises(ValueError,match='Object arrays'):run(path,tmp_path/'out')


def test_cli_runs_without_cv2_or_other_model_imports(tmp_path):
    path,_,_=fixture(tmp_path)
    script='''import importlib.abc,runpy,sys
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,name,path=None,target=None):
  if name.split('.')[0] in ('cv2','torch','onnxruntime'): raise RuntimeError('model import '+name)
sys.meta_path.insert(0,Block())
sys.argv=['replay','--manifest',sys.argv[1],'--output-dir',sys.argv[2]]
runpy.run_module('evaluation.reference_matching.replay',run_name='__main__')
'''
    r=subprocess.run([sys.executable,'-c',script,str(path),str(tmp_path/'out')],capture_output=True,text=True)
    assert r.returncode==0,r.stderr
    assert (tmp_path/'out/report.json').exists()


def test_missing_ownership_is_not_assumed_confirmed(tmp_path):
    path, data, plan = fixture(tmp_path)
    data['queries'][0].pop('association', None)
    dataset = tmp_path / 'dataset.json'
    dataset.write_text(json.dumps(data))
    plan['inputs']['dataset']['sha256'] = hashlib.sha256(dataset.read_bytes()).hexdigest()
    path.write_text(json.dumps(plan))
    with pytest.raises(ValueError, match='explicit association'):
        run(path, tmp_path / 'out')
    assert not (tmp_path / 'out').exists()
