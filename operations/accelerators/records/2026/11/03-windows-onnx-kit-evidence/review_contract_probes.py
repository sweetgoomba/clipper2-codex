"""Run only reviewed pure comparison/main functions with fake inference; no models."""
import argparse
import ast
import datetime as dt
import json
from pathlib import Path
import time
import traceback
from types import SimpleNamespace
import numpy as np

source=Path('/Users/jina/Downloads/run_kit.py').read_text()
tree=ast.parse(source)
names={'main','compare','_people','_iou','_yunet_scores'}
functions=ast.Module(body=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in names],type_ignores=[])
kit=Path('/private/tmp/clipper-kit-file-audit-20261103/fake-kit')
(kit/'models').mkdir(parents=True,exist_ok=True)
(kit/'models'/'manifest.json').write_text(json.dumps({'auraface':{'file':'no-real-model','samples':'aura','kind':'embedding','used_by':['test']}}))
np.savez(kit/'samples.npz',aura=np.ones((8,1),np.float32))
calls=[]
class FakeSession:
    def __init__(self,provider):self.provider=provider
    def get_providers(self):return [self.provider]
def run_all(session,inputs,runs,batch=1):
    calls.append({'provider':session.provider,'batch':batch})
    if batch==8 and session.provider=='FakeGPU':raise RuntimeError('batch8 failed')
    return [[np.ones((1,2),np.float32)] for _ in inputs],{'median_ms_per_item':1.0,'first_run_ms':2.,'batch':batch}
scope={'np':np,'argparse':argparse,'json':json,'KIT':kit,'dt':dt,'traceback':traceback,
       'SKIP_PROVIDERS':{'CPUExecutionProvider'},'ort':SimpleNamespace(__version__='FAKE',get_available_providers=lambda:['CPUExecutionProvider','FakeGPU']),
       'system_info':lambda:{},'make_session':lambda path,provider:(FakeSession(provider),0.),'run_all':run_all}
exec(compile(functions,'reviewed-functions','exec'),scope)
import sys
sys.argv=['probe','--label','fake']
scope['main']()
report=json.loads(next((kit/'results').glob('*.json')).read_text())
row=report['models']['auraface']['rows']['FakeGPU']
assert calls==[{'provider':'CPUExecutionProvider','batch':1},{'provider':'FakeGPU','batch':1},{'provider':'FakeGPU','batch':8},{'provider':'CPUExecutionProvider','batch':8}]
assert 'error' in row and 'median_ms_per_item' not in row
cpu=[np.full((1,1,1),.9,np.float32) for _ in range(6)]+[np.zeros((1,1,4),np.float32) for _ in range(3)]+[np.zeros((1,1,10),np.float32) for _ in range(3)]
other=[x.copy() for x in cpu]
for x in other[6:]:x.fill(1000)
face=scope['compare']('yunet',[cpu],[other])
pred=np.zeros((1,56,1),np.float32);pred[0,:5,0]=[10,10,5,5,.9]
changed=pred.copy();changed[0,5:,0]=1000
pose=scope['compare']('yolo',[[pred]],[[changed]])
result={'model_inference_executed':False,'batch1_overwritten_by_batch8_error':True,'calls':calls,'yunet_boxes_landmarks_changed_1000_comparison':face,'yolo_keypoints_changed_1000_comparison':pose}
Path('/private/tmp/clipper-kit-file-audit-20261103/contract-probes.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
