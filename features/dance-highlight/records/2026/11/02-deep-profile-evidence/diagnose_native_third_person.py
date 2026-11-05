"""Saved-observation diagnostic only; no model inference or product mutation."""
import sys,json
from pathlib import Path
from collections import Counter
from dataclasses import replace
import numpy as np
sys.path.insert(0,'/Users/jina/project/adlight/desktop/clipper_python/plugins/dance_highlight')
from dance_highlight.services import native_scene as n
from dance_highlight.services.segment import FrameRec
from dance_highlight.services.track import bbox_iou
BASE=Path('/private/tmp/dance-yunet-sface-20261102/app/new');OUT=Path('/private/tmp/dance-deep-profile-20261102/quality');reports={}

def upper(person,size):
 w,h=size;b=np.array(person['bbox']);p=np.array(person['pose_keypoints']);vis=np.isfinite(p).all(1)&(p[:,2]>=.5)&(p[:,0]>=max(0,b[0]))&(p[:,0]<min(w,b[2]))&(p[:,1]>=max(0,b[1]))&(p[:,1]<min(h,b[3]));heads=np.flatnonzero(vis[:5]);torso=[5,6,11,12]
 return bool(len(heads)>=2 and vis[torso].all() and (p[torso,2]>=.75).all() and p[heads,1].max()<p[[5,6],1].mean()<p[[11,12],1].mean() and np.ptp(p[torso,0])>0)

for label,pid in [('MMN','1793603593237'),('ANT','1793603739918'),('NEON','1793603971986')]:
 e=json.loads((BASE/pid/'face_evidence.json').read_text());m=json.loads((BASE/pid/'dance_meta.json').read_text());fps=m['stats']['fps'];size=(m['diagnostics']['frame_width'],m['diagnostics']['frame_height']);obs={r['frame']:r['persons'] for r in e['native_scene_refinement']['observations']};records=[];rows=[]
 for p in e['pose_heads']:
  r=FrameRec(p['time_seconds'],p['candidate_main_id'],np.array(p['candidate_main_bbox']) if p['candidate_main_bbox'] else None,p['scene_kind']=='group',person_bboxes=[np.array(b) for b in p['body_boxes']],person_head_keypoints=[np.array(k) for k in p['head_keypoints']],person_pose_keypoints=[np.array(k) for k in p['pose_keypoints']],scene_kind=p['scene_kind'],scene_reason=p['scene_reason']);records.append(r);f=round(r.t*fps);observed=obs.get(f,[]);people=[n._geometry(x,size) for x in observed];people,excluded=n._separate_upper_unobserved_people(observed,people,size,r);retained=[i for i in range(len(observed)) if i not in excluded];people,lower=n._separate_lower_partial_people([observed[i] for i in retained],people,size);retained=[v for j,v in enumerate(retained) if j not in lower]
  bounded=bool(people) and all(v is not None for v in people) and not n._large_observed_foreground(r,size) and max(v['extent'] for v in people)<=size[1]/6
  count=n._distinct_complete_count([v for v in people if v is not None]);details=[]
  for index,v in zip(retained,people):
   if v is None:continue
   original=[j for j,b in enumerate(r.person_bboxes) if bbox_iou(v['box'],b)>=.7]
   original_upper=[j for j in original if j<len(r.person_pose_keypoints) and upper(dict(bbox=r.person_bboxes[j],pose_keypoints=r.person_pose_keypoints[j]),size)]
   positive=upper(observed[index],size);details.append(dict(index=index,box=v['box'].tolist(),full=v['full'],extent=v['extent'],head_torso=positive,original_matches=original,original_head_torso=original_upper))
  complete=[v for v in people if v is not None and v['full']]
  positive=[];strict=[]
  for d,v in zip(details,[v for v in people if v is not None]):
   if d['head_torso'] and not d['full']:
    candidate=dict(v,full=True)
    if n._distinct_complete_count(complete+[candidate])>count:
     positive.append(d['index'])
     if len(d['original_matches'])==1 and len(d['original_head_torso'])==1:strict.append(d['index'])
  rows.append(dict(frame=f,time=r.t,scene=r.scene_kind,bounded=bounded,original_foreground=n._large_observed_foreground(r,size),upper_excluded=excluded,full_count=count,independent_upper_indices=positive,corroborated_upper_indices=strict,potential=bounded and count==2 and bool(positive),strict_potential=bounded and count==2 and bool(strict),people=details))
 detail=[d for d in rows if (label=='NEON' and 154.154<=d['time']<=157.958) or d['potential']]
 reports[label]=dict(all_potential=[d for d in rows if d['potential']],strict_potential=[d for d in rows if d['strict_potential']],details=detail)
 print(label,'potential',sum(d['potential'] for d in rows),'strict',sum(d['strict_potential'] for d in rows),flush=True)
 if label=='NEON':
  target=[d for d in rows if 154.154<=d['time']<=157.958];print('target',Counter((d['bounded'],d['full_count'],len(d['independent_upper_indices']),d['original_foreground']) for d in target));print('potential times',[round(d['time'],4) for d in target if d['potential']])
(OUT/'native-third-person-diagnostic.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2))
