"""No inference: compare strict native third-person proposal against current code."""
import json,sys
from pathlib import Path
import numpy as np
sys.path.insert(0,'/Users/jina/project/adlight/desktop/clipper_python/plugins/dance_highlight')
from dance_highlight.services import native_scene as n
from dance_highlight.services.segment import FrameRec
root=Path('/private/tmp/dance-deep-profile-20261102/quality');base=Path('/private/tmp/dance-yunet-sface-20261102/app/new');details=json.loads((root/'native-third-person-diagnostic.json').read_text());old_geometry=n._geometry;old_count=n._distinct_complete_count;out={}
for label,pid in [('MMN','1793603593237'),('ANT','1793603739918'),('NEON','1793603971986')]:
 e=json.loads((base/pid/'face_evidence.json').read_text());m=json.loads((base/pid/'dance_meta.json').read_text());fps=m['stats']['fps'];size=(m['diagnostics']['frame_width'],m['diagnostics']['frame_height']);observed={r['frame']:r['persons'] for r in e['native_scene_refinement']['observations']};records=[];positive={(d['frame'],i) for d in details[label]['all_potential'] for i in d['independent_upper_indices']}
 for f,people in observed.items():
  for i,p in enumerate(people):p['_diagnostic_positive']=(f,i) in positive
 for p in e['pose_heads']:
  records.append(FrameRec(p['time_seconds'],p['candidate_main_id'],np.array(p['candidate_main_bbox']) if p['candidate_main_bbox'] else None,p['scene_kind']=='group',person_bboxes=[np.array(b) for b in p['body_boxes']],person_head_keypoints=[np.array(k) for k in p['head_keypoints']],person_pose_keypoints=[np.array(k) for k in p['pose_keypoints']],scene_kind=p['scene_kind'],scene_reason=p['scene_reason']))
 current,ca=n.refine_with_scene_observations(records,observed,video_size=size,fps=fps,cut_frames=e['main_selection_refinement']['cut_frames'])
 def geometry(person,video_size):
  result=old_geometry(person,video_size)
  return dict(result,positive=person['_diagnostic_positive']) if result is not None else None
 def count(people):
  value=old_count(people)
  if value!=2 or any(p['box'][3]-p['box'][1]>size[1]/6 for p in people):return value
  return old_count([dict(p,full=p['full'] or p.get('positive',False)) for p in people])
 n._geometry,n._distinct_complete_count=geometry,count
 try:proposal,pa=n.refine_with_scene_observations(records,observed,video_size=size,fps=fps,cut_frames=e['main_selection_refinement']['cut_frames'])
 finally:n._geometry,n._distinct_complete_count=old_geometry,old_count
 changes=[dict(frame=round(a.t*fps),time=a.t,before=a.scene_kind,after=b.scene_kind) for a,b in zip(current,proposal) if a.scene_kind!=b.scene_kind];out[label]=dict(changes=changes,potential_frames=sorted(f for f,_ in positive),additional_change_count=len(changes));print(label,out[label])
(root/'native-third-person-replay.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
