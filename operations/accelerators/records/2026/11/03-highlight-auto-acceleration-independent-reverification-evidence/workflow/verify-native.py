import ast,importlib.util,sys,types,os,json,hashlib,threading
from pathlib import Path
from collections import OrderedDict
P=Path('/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103')
package=types.ModuleType('clipper_accelerators');package.__path__=[str(P/'clipper_accelerators/clipper_accelerators')];sys.modules['clipper_accelerators']=package
runtime=types.ModuleType('clipper_accelerators.runtime');runtime.cpu_only=lambda:False;sys.modules[runtime.__name__]=runtime
calls=[]
class Lease:
 def reserve(self,n):calls.append(['reserve',n])
 def register_native(self):calls.append(['register_native'])
 def check(self):pass
 def close(self):pass
class Leases:
 @staticmethod
 def acquire(adapter,n):calls.append(['acquire',n]);return Lease()
leases=types.ModuleType('clipper_accelerators.lease_client');leases.HostLease=Leases;sys.modules[leases.__name__]=leases
env=types.ModuleType('clipper_accelerators.environment');env.native_environment=lambda:types.SimpleNamespace(adapters=[types.SimpleNamespace(id='audit',backend_indices=[('torch_mps',0),('ort_coreml',0)])]);sys.modules[env.__name__]=env
os.environ.update(CLIPPER_ACCELERATOR_HOST_URL='http://audit-unused',CLIPPER_ACCELERATORS_WHOLE_UNIT_RECOVERY='1')
from clipper_accelerators import native_sessions
native_sessions.admit('mps',model_id='A',estimated_bytes=100)
native_sessions.admit('mps',model_id='B',estimated_bytes=200)
native_sessions.admit('mps',model_id='A',estimated_bytes=100)
native_sessions.admit('mps',model_id='A',estimated_bytes=150)
reservation_calls=list(calls);native_sessions.close_all();calls.clear()
from clipper_accelerators.model_boundary import model_call
watchdogs=[]
class Timer:
 def __init__(self,seconds,fn):self.seconds=seconds;self.daemon=False
 def start(self):watchdogs.append(['start',self.seconds])
 def cancel(self):watchdogs.append(['cancel',self.seconds])
threading.Timer=Timer
class Session:
 def __init__(self,*a,**kw):pass
 def get_providers(self):return ['CoreMLExecutionProvider','CPUExecutionProvider']
 def get_inputs(self):return [types.SimpleNamespace(name='input')]
 def get_outputs(self):return [types.SimpleNamespace(name='out')]
 def run(self,*a):return [types.SimpleNamespace(shape=(1,512))]
ort=types.SimpleNamespace(get_available_providers=lambda:['CoreMLExecutionProvider'],SessionOptions=lambda:types.SimpleNamespace(),InferenceSession=Session)
np=types.SimpleNamespace(zeros=lambda *a,**kw:None,float32='float32',isfinite=lambda x:types.SimpleNamespace(all=lambda:True))
base={'__name__':'audit_loader','Path':Path,'hashlib':hashlib,'ort':ort,'threading':threading,'OrderedDict':OrderedDict,'platform':types.SimpleNamespace(system=lambda:'Darwin'),'np':np,'AURAFACE_SHA256':'audit','time':__import__('time'),'logger':types.SimpleNamespace(info=lambda *a:None,warning=lambda *a,**kw:None)}
def load_class(rel,name,extra):
 tree=ast.parse((P/rel).read_text());node=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==name)
 namespace={**base,**extra};exec(compile(ast.Module(body=[node],type_ignores=[]),str(P/rel),'exec'),namespace);return namespace[name]
Accel=load_class('plugins/dance_highlight/dance_highlight/services/opencv_acceleration.py','AcceleratedSession',{'prepare_model':lambda *a,**kw:b'audit','accelerator_options':lambda *a:([('CoreMLExecutionProvider',{}),'CPUExecutionProvider'],object())})
Accel(Path('/private/tmp/audit-nonexistent.onnx'))
Face=load_class('plugins/dance_highlight/dance_highlight/services/face_runtime.py','DanceFaceSession',{})
Face('/private/tmp/audit-nonexistent.onnx')
result={'scope':'No model/native imports/inference or processes; actual source AST classes and model_call with fake ORT sessions/Timer/lease host.','memory_calls':reservation_calls,'watchdogs':watchdogs,'source_model_loads_executed':2}
Path('/private/tmp/clipper-reaudit-20261103/workflow/native.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
