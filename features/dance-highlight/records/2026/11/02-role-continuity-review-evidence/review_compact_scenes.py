from pathlib import Path
from dataclasses import replace
import hashlib,importlib.util,json,shutil,sys
import numpy as np
from dance_highlight.services import segment as old
OUT=Path('/private/tmp/dance-role-continuity-review-20261102')
source=Path('/Users/jina/project/adlight/desktop/clipper_python/plugins/dance_highlight/dance_highlight/services/segment.py')
frozen=OUT/'proposed_segment.py';shutil.copyfile(source,frozen)
spec=importlib.util.spec_from_file_location('dance_highlight.services.proposed_segment',frozen)
new=importlib.util.module_from_spec(spec);sys.modules[spec.name]=new;spec.loader.exec_module(new)
man=json.loads((OUT/'manifest.json').read_text());reports={}
for label,c in man.items():
 e=json.loads(Path(c['evidence']).read_text());m=json.loads(Path(c['meta']).read_text());fps=c['fps'];size=(m['diagnostics']['frame_width'],m['diagnostics']['frame_height'])
 rows=[old.FrameRec(p['time_seconds'],p['candidate_main_id'],None if p['candidate_main_bbox'] is None else np.asarray(p['candidate_main_bbox']),False,
                   person_bboxes=[np.asarray(b) for b in p['body_boxes']],person_pose_keypoints=[np.asarray(k) for k in p['pose_keypoints']]) for p in e['pose_heads']]
 a=old.classify_main_scenes(rows,size);b=new.classify_main_scenes(rows,size)
 runs=[]
 for i,(x,y) in enumerate(zip(a,b,strict=True)):
  if x.scene_kind!=y.scene_kind:
   if runs and runs[-1][-1]+1==i:runs[-1].append(i)
   else:runs.append([i])
 changes=[]
 for ids in runs:
  lo=rows[ids[0]].t;hi=rows[ids[-1]+1].t if ids[-1]+1<len(rows) else rows[ids[-1]].t
  intersections={kind:[{'start':max(lo,r['start']),'end':min(hi,r['end']),'name':r.get('person_id')} for r in m['lists'][kind] if r['start']<hi and lo<r['end']] for kind in ('main','group')}
  changes.append({'start':lo,'end':hi,'frames':[round(rows[i].t*fps) for i in ids],
                  'before':a[ids[0]].scene_kind,'after':b[ids[0]].scene_kind,'current_app_intersections':intersections})
 reports[label]={'changed_observations':sum(len(x) for x in runs),'changes':changes,
                 'old_group_demotions':sum(x.scene_kind=='group' and y.scene_kind!='group' for x,y in zip(a,b)),
                 'named_seconds_in_changed_scopes':sum(v['end']-v['start'] for x in changes for v in x['current_app_intersections']['main'] if v['name']!='unknown'),
                 'unknown_seconds_in_changed_scopes':sum(v['end']-v['start'] for x in changes for v in x['current_app_intersections']['main'] if v['name']=='unknown')}
 if label=='ANT':
  reports[label]['reviewed_eunchae_unchanged']=all(x.scene_kind==y.scene_kind for r,x,y in zip(rows,a,b) if 4.571<=r.t<6.139)
 print(label,json.dumps(reports[label],ensure_ascii=False),flush=True)

def posed(boxes):
 poses=[]
 for x,y,xx,yy in boxes:
  w,h=xx-x,yy-y;p=np.zeros((17,3));p[:,2]=.9
  p[:5,:2]=[[x+.5*w,y+.08*h],[x+.4*w,y+.06*h],[x+.6*w,y+.06*h],[x+.3*w,y+.08*h],[x+.7*w,y+.08*h]]
  p[[5,6,11,12,15,16],:2]=[[x+.3*w,y+.2*h],[x+.7*w,y+.2*h],[x+.35*w,y+.5*h],[x+.65*w,y+.5*h],[x+.35*w,y+.95*h],[x+.65*w,y+.95*h]]
  poses.append(p)
 return old.FrameRec(0,1,np.asarray(boxes[0]),False,person_bboxes=[np.asarray(b) for b in boxes],person_pose_keypoints=poses)
wide=posed([[820,500,870,730],[900,500,950,730],[980,500,1030,730]])
central=posed([[925,500,975,730]])
rows=[replace(central if .8<=i/10<1.1 else wide,t=i/10) for i in range(21)]
a=old.classify_main_scenes(rows,(1920,1080));b=new.classify_main_scenes(rows,(1920,1080))
counter={'description':'0.2s measured central torso inside a short single-body interval between NEW compact-group candidates; old bounded dropout fill can bypass the new veto.',
         'protected_times':[r.t for r in rows if new._observed_central_torso(r,(1920,1080))],
         'before':[{'t':r.t,'scene':x.scene_kind} for r,x in zip(rows,a)],
         'after':[{'t':r.t,'scene':x.scene_kind} for r,x in zip(rows,b)],
         'central_interval_changed_to_group':all(x.scene_kind=='main' and y.scene_kind=='group' for r,x,y in zip(rows,a,b) if .8<=r.t<1.1)}
result={'proposed_segment_sha256':hashlib.sha256(frozen.read_bytes()).hexdigest(),'actual':reports,'veto_bypass_counterexample':counter}
(OUT/'compact-scene-independent-review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print('VETO COUNTEREXAMPLE',json.dumps(counter),flush=True)
