from pathlib import Path
import sys,json,numpy as np,copy,time
sys.path.insert(0,'/Users/jina/project/adlight/desktop/clipper_python/plugins/dance_highlight')
from dance_highlight.services.main_role_timeline import choose_roles,extend_near_ties
from dance_highlight.services.observed_main import strict_pose_corresponding
BASE=Path.home()/'Library/Application Support/Clipper Studio Dev/projects/files/116957ce-bd03-4d4a-a21d-984dc12487aa';report={}
for label,pid in [('MMN','1793674437287'),('ANT','1793674460357'),('NEON','1793674513908')]:
 e=json.loads((BASE/pid/'diagnostics/face_evidence.json').read_text());a=e['main_selection_refinement'];fps=59.94005994005994
 poses={round(p['time_seconds']*fps):p for p in e['pose_heads']};changes={r['frame']:r['before'] for r in a['changes']};original=a['role_observations'];rows=copy.deepcopy(original)
 old={r['frame']:dict(candidate_main_bbox=changes.get(r['frame'],r['box'])) for r in rows}
 proofs={(r['frames'][0],r['source'],r['frames'][1]):r['target'] for r in a['face_correspondences']}
 for r in rows:
  r['time']=poses[r['frame']]['time_seconds']
  for f in r['features']:f['pose_keypoints']=np.array(poses[r['frame']]['pose_keypoints'][f['index']])
 def corresponding(r,f,q):
  result=strict_pose_corresponding(r,f,q)
  if result is not None:return result
  idx=proofs.get((r['frame'],f['index'],q['frame']))
  return next((x for x in q['features'] if x['index']==idx),None)
 start=time.perf_counter();choose_roles(rows,old,1920,1080,a['cut_frames'],corresponding);extend_near_ties(rows,a['cut_frames'],corresponding)
 byframe={r['frame']:r for r in rows}
 for episode in a['camera_episodes']:
  for t in episode['visible_targets']:
   r=byframe[t['frame']];f=next(f for f in r['features'] if f['index']==t['index']);r.update(index=f['index'],box=f['box'])
  for frame in episode['role_only_frames']:byframe[frame].update(index=None,box=None)
 diff=[dict(frame=r['frame'],time=r['time'],before=o['box'],after=r['box'],reason=r['reason']) for r,o in zip(rows,original) if r['box']!=o['box']]
 report[label]=dict(changed=len(diff),seconds=time.perf_counter()-start,changes=diff)
 print(label,'changed',len(diff),'seconds',report[label]['seconds'],flush=True)
 if label=='MMN':
  for x in diff:
   if 49.8<x['time']<51.1 or 102.8<x['time']<103.4:print(x,flush=True)
Path('/private/tmp/dance-user-clips-20261103/role-replay.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
