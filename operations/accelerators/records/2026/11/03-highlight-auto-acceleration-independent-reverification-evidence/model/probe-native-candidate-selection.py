import os,json,tempfile
from pathlib import Path
from types import SimpleNamespace
from dataclasses import asdict
import numpy as np
from clipper_accelerators import runtime,environment,idle,profiles
from clipper_accelerators.contracts import Measurement,digest
root=Path(tempfile.mkdtemp(prefix='native-choice-',dir='/private/tmp/clipper-reaudit-20261103/model'));os.environ['CLIPPER_ACCELERATOR_HOME']=str(root)
env=environment.probe_environment({'system':'win32','host_arch':'x64','process_arch':'x64','os_build':'1'})
environment.native_environment=lambda *a:env
runtime.configure({'acceleration_mode':'auto'},'cuda:0',root,consumer='dance')
identity={'onnx_path':str(root/'model.onnx'),'onnx_sha256':'a'*64};spec=profiles.profile_spec('pose.yolov8s','s','dance','rect','full_frame',(1,3,2,2),identity)
profile={**spec,'id':digest(spec),'plugin':'dance_highlight','fixtures':[],'native_cpu_ms':[20.]*33,'incumbent_ms':[10.]*33,'incumbent_backend':'torch_cuda:0','incumbent_quality_passed':True}
profiles.profiles=lambda *a:[profile];idle.profiles=lambda *a:[profile];idle.validate_profile=lambda *a:None
pack={'pack_id':'native','manifest_sha256':'b'*64,'platform':'win32','python_abi':'cp311'}
def cand(index):return {'kind':'native','backend':'torch_cuda','onnx_sha256':'s','runtime_pack':pack,'adapter_id':'gpu'+str(index),'adapter_index':index,'incumbent_backend':'torch_cuda:'+str(index),'incumbent_precision':'fp32'}
candidates=[cand(0),cand(1)];idle._candidates=lambda *a:candidates
records={}
for index,candidate in enumerate(candidates):
 key=idle.candidate_id(profile,candidate,env)
 def measurement(ms):return asdict(Measurement(key,'complete',True,0,0,ms,ms,1,30,env.fingerprint))
 records[key+'.json']={'schema':1,'measurement':measurement(10. if index==0 else 1.),'native_execution_measurement':measurement(10. if index==0 else 1.),'cpu_native_execution_measurement':measurement(20.)}
idle._load=lambda path,default:records.get(Path(path).name,default)
import clipper_accelerators.runtime_catalog as catalog
admissions=[];catalog.qualified_backend=lambda *a:admissions.append(a) or SimpleNamespace(quality_certificate='enabled-scope')
gate=SimpleNamespace(estimated_items=100,consumer='dance',model_id='pose.yolov8s',source_sha='s',preprocessing='rect',purpose='full_frame',identity=identity,incumbent_backend='torch_cuda:0',incumbent_precision='fp32')
first=idle.choose_for_gate(gate,np.ones((1,3,2,2),np.float32))
profile['native_cpu_ms']=[1.]*33
second=idle.choose_for_gate(gate,np.ones((1,3,2,2),np.float32))
result={'incumbent_cuda0_ms':10,'alternative_cuda1_ms':1,'cpu_ms_initial':20,'choice_with_faster_alternative_gpu':first,'certificate_admission_calls_for_native_candidates':len(admissions),'choice_after_cpu_made_fastest':second}
(root/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));print(root)
