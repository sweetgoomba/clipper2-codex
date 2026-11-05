"""Synthetic original-photo contradiction; frozen source, no inference/video."""
import importlib.util,sys,json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
ROOT=Path('/private/tmp/dance-identity-assembly-20261103/independent-source-review-v3')
for name in ('identity_projection','member_timeline','part_boundary_events'):
    spec=importlib.util.spec_from_file_location('dance_highlight.services.'+name,ROOT/(name+'.py'))
    mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
from dance_highlight.services.face_evidence import FaceObservation
from dance_highlight.services.segment import FrameRec,Segment
from dance_highlight.services.reference_matcher import SegmentReferenceDecision
from dance_highlight.services.member_timeline import _assign_piece
from dance_highlight.services.part_boundary_events import coalesce_boundary_events

xy=np.array([[50,20],[45,18],[55,18],[40,20],[60,20],[35,50],[65,50],[30,80],[70,80],[25,110],[75,110],[40,120],[60,120],[40,160],[60,160],[40,200],[60,200]],float)
pose=np.c_[xy,np.ones(17)];box=np.array([10.,0.,90.,210.])
rows=[FaceObservation(f,f/60,0,tuple(box),tuple(box),face_bbox=(35,10,65,30),embedding=np.array([0.,1.]) if f==12 else np.array([1.,0.]),detector_score=.99,association='confirmed') for f in (0,4,8,12)]
records=[FrameRec(r.time_seconds,0,box,False,person_bboxes=[box],person_pose_keypoints=[pose.copy()],scene_kind='main') for r in rows]
other=box+np.array([200,0,200,0]);otherpose=pose.copy();otherpose[:,0]+=200
records.append(FrameRec(16/60,1,other,False,person_bboxes=[box,other],person_pose_keypoints=[pose.copy(),otherpose],scene_kind='main'))
class Matcher:
    def match(self,row,*_):return SimpleNamespace(reference_id='A' if row.embedding[0]>.9 else 'B' if row.embedding[1]>.9 else None)
matcher=Matcher();evidence=[(r,matcher.match(r).reference_id) for r in rows]
left=Segment('main',0,0.,14/60,[(r.time_seconds,box,0) for r in rows]);tail=Segment('main',0,14/60,16/60,[])
left_decision=_assign_piece(left,evidence,matcher,[],'original')
output=dict(segments=[left,tail],decisions=[left_decision,SegmentReferenceDecision(None,'unmatched','unresolved_face_interval')],labels=[1,None],accurate_indices=[0],anchors=[],evidence=[evidence,[]],previews=[[],[]],preview_sources=[({},{}),({},{})])
identity=dict(audit=[dict(boundaries=[dict(time=14/60,left_time=12/60,right_time=16/60,reason='repeated_face_change')])])
result,audit=coalesce_boundary_events(output,identity,matcher=matcher,frame_records=records,frozen_observations=rows,
    joint_matches={r.frame_index:dict(status='accepted',name='A') for r in rows},eligibility=[Segment('main',0,0.,1.,[])],fps=60.,sample_step=4,cut_frames=[],
    handoffs=[dict(previous_frame=12,frame=16,previous_time=12/60,time=16/60,boundary_policy='first_observed_new_main')])
report=dict(original_consensus=left_decision.reference_id,last_original_primary=evidence[-1][1],last_joint='A',after=[[s.start,s.end,d.reference_id] for s,d in zip(result['segments'],result['decisions'])],audit=audit,models_called=False,video_read=False)
(ROOT/'primary-contradiction-counterexample.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
