"""Independent saved-fixture counterexamples for bbox-only group support."""
from pathlib import Path
import importlib.util,sys,json,hashlib
import numpy as np
P=Path('/private/tmp/dance-role-continuity-review-20261102')
spec=importlib.util.spec_from_file_location('dance_highlight.services.bridge_draft',P/'bridge-draft-segment.py')
s=importlib.util.module_from_spec(spec);sys.modules[spec.name]=s;spec.loader.exec_module(s)
from dance_highlight.services.native_scene import _large_observed_foreground
data=json.loads((P/'bridge-draft-fixture.json').read_text())
def example():
    rows=[s.FrameRec(r['time_seconds'],r['candidate_main_id'] if r['scene_kind']=='main' else None,np.array(r['candidate_main_bbox']) if r['scene_kind']=='main' else None,r['scene_kind']=='group',person_bboxes=[np.array(b) for b in r['body_boxes']],person_pose_keypoints=[np.array(p) for p in r['pose_keypoints']],scene_kind=r['scene_kind'],scene_reason=r['scene_reason'],candidate_main_id=r['candidate_main_id'],candidate_main_bbox=np.array(r['candidate_main_bbox'])) for r in data['rows']]
    target=next(r for r in rows if round(r.t*data['fps'])==data['target_frame'])
    return rows,target
def human_pose(box):
    x,y,xx,yy=box;w=xx-x;h=yy-y;p=np.zeros((17,3));p[:,2]=.99
    p[:5,:2]=[[x+.5*w,y+.08*h],[x+.4*w,y+.07*h],[x+.6*w,y+.07*h],[x+.3*w,y+.08*h],[x+.7*w,y+.08*h]]
    p[[5,6,11,12,15,16],:2]=[[x+.3*w,y+.2*h],[x+.7*w,y+.2*h],[x+.35*w,y+.5*h],[x+.65*w,y+.5*h],[x+.35*w,y+.95*h],[x+.65*w,y+.95*h]]
    return p
reports=[]
for case in ['original','new_reliable_foreground_at_old_art_bbox','missing_gap_pose']:
    rows,target=example()
    if case=='new_reliable_foreground_at_old_art_bbox':
        index=int(np.argmax([b[3]-b[1] for b in target.person_bboxes]))
        target.person_pose_keypoints[index]=human_pose(target.person_bboxes[index])
    if case=='missing_gap_pose':target.person_pose_keypoints=[]
    before=target.scene_kind
    output,audit=s.bridge_compact_group_gaps(rows,video_size=(1920,1080),fps=data['fps'],sample_step=data['sample_step'],cut_frames=[],handoffs=[],camera_episodes=[])
    got=next(r for r in output if r.t==target.t)
    reports.append({'case':case,'before':before,'after':got.scene_kind,'central_veto':s._observed_central_torso(target,(1920,1080)),'existing_large_foreground_guard':_large_observed_foreground(target,(1920,1080)),'gap_box_heights':[float(b[3]-b[1]) for b in target.person_bboxes],'bridges':audit['bridges']})
out={'reviewed_segment_sha256':hashlib.sha256((P/'bridge-draft-segment.py').read_bytes()).hexdigest(),'cases':reports,'scope':'Synthetic pose perturbations on the saved real fixture, calling the frozen proposed bridge. No ML or video decode.'}
(P/'bridge-foreground-counterexamples.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(out,ensure_ascii=False,indent=2))
