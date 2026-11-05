import sys,copy,json,hashlib
from pathlib import Path
sys.path[:0]=['/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/clipper_accelerators','/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103']
from scripts.accelerators import benchmark_app as m
root=Path('/private/tmp/clipper-reaudit-20261103/root/benchmark');root.mkdir(parents=True,exist_ok=True)
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v),encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
results=[]
for label in ('control','missing_baseline','regression100x','zero_model_calls','different_identity','insufficient_diversity'):
 p=root/label;p.mkdir(exist_ok=True)
 video=p/'video.mp4';video.write_bytes(b'not decoded; fake owned analysis')
 src=p/'frozen/original.py';src.parent.mkdir(exist_ok=True);src.write_text('preserved reference')
 out=p/'original/json/person_highlight.json';payload={'groups':[{'person_id':'original-a'}],'clips':[{'start':0,'end':3}]};write(out,payload)
 corpus=p/'corpus.json';write(corpus,{'cases':[{'id':'case','video':str(video),'plugins':['person_highlight']}]})
 profile={'model_id':'pose.yolov8s','consumer':'person','backend':'ort_cuda','preprocessing':'ultralytics-original-rect-fp32','purpose':'full_frame','profile':[1,3,640,640]}
 matrix=p/'matrix.json';write(matrix,{'plugins':['person_highlight'],'rounds':3,'required_models':{'person_highlight':['pose.yolov8s']},'required_profiles':{'person_highlight':[profile]}})
 base=p/'baseline.json';write(base,{'schema':2,'purpose':'frozen_original_analysis','repositories':[{'root':str(src.parent),'files':{'original.py':{'sha256':sha(src)}}}],'corpus':{'path':str(corpus),'sha256':sha(corpus),'files':{str(video):{'sha256':sha(video)}}},'expected_outputs':[{'case':'case','plugin':'person_highlight','root':str(out.parents[1]),'files':{'json/person_highlight.json':{'sha256':sha(out)}},'stage_seconds':[1,1,1]}]})
 model={**profile,'selected_backend':'ort_cuda','executed_candidate_backend':'ort_cuda','calls':40,'gpu_calls':40,'samples':33,'distinct_inputs':24,'cpu_median_ms':10.,'candidate_median_ms':8.,'profile_verified':True,'execution_evidence':'profiled','graph_execution':'accelerator','provider_node_counts':{'CUDAExecutionProvider':5}}
 if label=='zero_model_calls':model['calls']=0
 if label=='insufficient_diversity':model['distinct_inputs']=1
 count=[0]
 class Process:
  def __init__(self,args):
   count[0]+=1;target=Path(args[args.index('--output')+1]);mode='cpu' if '--cpu' in args else 'verify'
   data=copy.deepcopy(payload)
   if label=='different_identity' and mode=='verify':data['groups'][0]['person_id']='wrong-b'
   write(target/'json/person_highlight.json',data)
   write(target/'json/acceleration.json',{'models':[model],'validation':{'status':'PASS','candidate_stage_seconds':100 if label=='regression100x' else 1}})
   write(Path(args[args.index('--result')+1]),{'acceleration':{'elapsed_seconds':1}})
  def poll(self):return 0
  def close(self,t):return True
 m._OwnedProcess=Process
 sys.argv=['bench','--matrix',str(matrix),'--corpus',str(corpus),'--out',str(p/'result'),'--candidate',str(p/'home'),'--baseline',str(p/'absent.json' if label=='missing_baseline' else base)]
 code=m.main();r=json.loads((p/'result/report.json').read_text());results.append({'case':label,'exit':code,'device':r['device_test_status'],'coverage':r['coverage_complete'],'timing':r['timing_status'],'baseline':r['baseline_status'],'comparison':r['comparison_status'],'process_calls':count[0],'release':r['release_status']})
assert results[0]['exit']==0
assert all(r['exit']!=0 for r in results[1:])
assert results[1]['process_calls']==0
(root/'results.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
