import json,sys,hashlib,contextlib,io,ast
from pathlib import Path
import numpy as np
p=Path('/private/tmp/dance-user-clips-20261103'); services=Path('plugins/dance_highlight/dance_highlight/services')
names=['member_timeline','stage_prominence','pipeline']
def hashes():return {n:hashlib.sha256((services/(n+'.py')).read_bytes()).hexdigest() for n in names}
before=hashes();result={}
for script in ['independent_cut_probe','independent_cut_snap_probe','independent_same_name_cut_probe']:
 source=(p/(script+'.py')).read_text().replace(script+'.json',script+'-final.json')
 with contextlib.redirect_stdout(io.StringIO()):exec(compile(source,str(p/(script+'.py')),'exec'),{'__name__':'__main__'})
 result[script]=json.loads((p/(script+'-final.json')).read_text())
from dance_highlight.services.face_evidence import FaceObservation
from dance_highlight.services.segment import Segment
from dance_highlight.services.member_timeline import _identity_boundaries
from dance_highlight.services.stage_prominence import foreground_subject
d=json.loads(Path('tests/fixtures/dance_scene_review/mmn50_cut_support.json').read_text());rows=[FaceObservation(**dict(o,embedding=np.array(o['embedding']) if o['embedding'] is not None else None)) for o in d['observations']]
cut=3047/d['fps'];bounds=_identity_boundaries(Segment('main',0,49.9,51.3,[]),rows,[None]*len(rows),[],cut_times=[cut]);result['mmn50']={'boundaries':bounds,'correct_cut':any(abs(b['time']-cut)<1e-8 for b in bounds),'false_boundary_removed':not any(50.6<b['time']<50.8 for b in bounds)}
rows=[]
for t,n in [(.1,'A'),(.3,'A'),(.45,'B'),(.55,'A'),(.75,'A')]:rows.append(FaceObservation(round(t*100),t,7,(0.,0.,100.,100.),(0.,0.,100.,100.),face_bbox=(30.,10.,60.,40.),embedding=np.array([1.,0.,0.] if n=='A' else [0.,1.,0.]),detector_score=.98,association='confirmed'))
result['two_short_cuts']=_identity_boundaries(Segment('main',7,0.,1.,[]),rows,[None]*len(rows),[],cut_times=[.4,.5])
c=json.loads(Path('tests/fixtures/dance_foreground_reviewed.json').read_text());fs=[dict(f,pose_keypoints=np.array(f['pose_keypoints'])) for f in c['cases'][0]['features']];base=foreground_subject(fs,c['width'],c['height']);pose=base['pose_keypoints'].copy();pose[:,:2]=pose[:,:2]*.2+[500,300];small=dict(base,index=99,size=None,source='missing',x=float(pose[[5,6,11,12],0].mean()),pose_keypoints=pose,box=(np.array(base['box'])*.2+np.array([500,300,500,300])).tolist());other=foreground_subject(fs+[small],c['width'],c['height']);result['small_faceless_distant_peer']={'base':base['index'],'with_peer':other['index'] if other else None}
tree=ast.parse((services/'member_timeline.py').read_text());result['scope_cut_forwarding']=[{'line':x.lineno,'keywords':[k.arg for k in x.keywords]} for x in ast.walk(tree) if isinstance(x,ast.Call) and isinstance(x.func,ast.Name) and x.func.id=='_refine_member_scopes']
result['hashes_before']=before;result['hashes_after']=hashes();result['stable']=result['hashes_before']==result['hashes_after'];result['models_called']=False;result['video_reads']=0
(p/'independent-final-review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps(result,ensure_ascii=False))
