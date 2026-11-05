import os,sys,json,contextlib,tempfile
from pathlib import Path
from types import SimpleNamespace,ModuleType
import numpy as np
from clipper_accelerators import runtime,environment,yolo_adapter,onnx_adapter
root=Path(tempfile.mkdtemp(prefix='native-observation-',dir='/private/tmp/clipper-reaudit-20261103/model'))
os.environ['CLIPPER_ACCELERATOR_HOME']=str(root/'home')
environment.native_environment=lambda *a:environment.probe_environment({'system':'darwin','host_arch':'arm64','process_arch':'arm64','os_build':'14'})
runtime.configure({'acceleration_mode':'auto'},'mps',root,consumer='dance')
path=root/'weights.pt';path.write_bytes(b'weights')
class Tensor:
 def __init__(self,x):self.x=x
 def to(self,*a,**kw):return self
sys.modules['torch']=SimpleNamespace(no_grad=contextlib.nullcontext,device=lambda x:x,from_numpy=lambda x:Tensor(x),float16='float16',float32='float32')
mod=ModuleType('ultralytics.nn.autobackend');mod.AutoBackend=lambda *a,**kw:lambda x:np.ones((1,56,1),np.float32)
sys.modules['ultralytics.nn.autobackend']=mod
onnx_adapter.admitted=lambda *a,**kw:False
class Model:
 def __init__(self,infer):self.infer=infer;self.predictor=SimpleNamespace(model=SimpleNamespace(backend=SimpleNamespace(original=SimpleNamespace(forward=lambda x:np.ones((1,56,1),np.float32)))))
 def __call__(self,frame,**kw):self.infer(frame);return 'routed'
yolo_adapter.build_remote_yolo=lambda path,infer:Model(infer)
yolo_adapter._native_full_model=lambda p:lambda frame,**kw:'legacy'
model=yolo_adapter._routed_pose(path,{'backend':'ort_coreml','onnx_path':str(path),'onnx_sha256':runtime.file_sha(path)},device='mps',half=True)
for i in range(40):assert model(np.ones((1,3,2,2),np.float32)*i,device='mps',half=True)=='legacy'
gate=runtime._state['models'][0]
result={'actual_yolo_calls':gate.calls,'raw_incumbent_samples':len(gate.observed_incumbent_ms),'raw_distinct_inputs':len(gate.observed_inputs),'full_prediction_diagnostic_samples':len(gate.observed_prediction_ms),'published_observed_incumbent':gate.report()['observed_incumbent'],'incumbent_precision':gate.incumbent_precision,'reason':gate.reason}
(root/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));print(root)
