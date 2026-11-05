import os,sys,json,time,threading,tomllib
from pathlib import Path
root=Path('/Users/jina/project/adlight/.worktrees/mps-admission-20261104/clipper_python')
paths=[str(root/p) for p in tomllib.loads((root/'pyproject.toml').read_text())['tool']['uv']['workspace']['members']]
sys.path[:0]=paths;os.environ['PYTHONPATH']=os.pathsep.join(paths)
data=Path.home()/'Library/Application Support/Clipper Studio Dev'
os.environ['CLIPPER_DANCE_FACE_MODEL_DIR']=str(data/'plugin_models/dance_highlight')
os.chdir(data)
from clipper_accelerators.visual_unit import run_visual_unit
params=json.loads((data/'jobs/items/dance_1793724487371.json').read_text())['job']['params']
params={k:v for k,v in params.items() if k not in ('billing_attempt_id','operation_run_id')}
params['output_root']='/private/tmp/clipper-face-speed-20261104/mmn'
params['acceleration_mode']='auto'
started=time.perf_counter()
def progress(percent,message):
 print(json.dumps({'event':'progress','elapsed_seconds':round(time.perf_counter()-started,2),'percent':percent,'message':message},ensure_ascii=False),flush=True)
try:
 result=run_visual_unit('dance_highlight','mmn-face-coreml-20261104',params,'mps',threading.Event(),progress)
 Path('/private/tmp/clipper-face-speed-20261104/mmn-result.json').write_text(json.dumps(result,ensure_ascii=False,allow_nan=False,indent=2)+'\n')
 print(json.dumps({'event':'complete','elapsed_seconds':time.perf_counter()-started,'acceleration':result.get('acceleration'),'models':result.get('acceleration_models')},ensure_ascii=False),flush=True)
except Exception as error:
 print(json.dumps({'event':'error','elapsed_seconds':time.perf_counter()-started,'type':type(error).__name__,'message':str(error),'details':getattr(error,'details',None)}),flush=True)
 raise
