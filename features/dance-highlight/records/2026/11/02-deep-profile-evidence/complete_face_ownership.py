"""No inference: restore raw ownership audit with historical detection threshold."""
import sys,json
from pathlib import Path
import numpy as np
sys.path.insert(0,'/Users/jina/project/adlight/desktop/clipper_python/plugins/dance_highlight')
from dance_highlight.services.segment import FrameRec
from dance_highlight.services.face_evidence import select_pose_face
from dance_highlight.services.track import bbox_iou
root=Path('/private/tmp/dance-deep-profile-20261102/quality/roi-fullframe-eight')
for label in ['ANT','MMN']:
 path=root/label/'comparison.json';report=json.loads(path.read_text());threshold=report['config']['face_min_det_score']
 for data in report['frames']:
  p=data['pose'];body=np.array(data['saved_observation']['body_bbox']);r=FrameRec(p['time_seconds'],1,body,False,person_bboxes=[np.array(b) for b in p['body_boxes']],person_head_keypoints=[np.array(h) for h in p['head_keypoints']]);heads=[]
  for points in r.person_head_keypoints:
   points=points[:5];heads.append(points[np.isfinite(points).all(1)&(points[:,2]>=.5),:2])
  for v,a in data['alternatives'].items():
   if v=='saved':continue
   faces=a['detector_calls'][0]['yunet15'];faces=sorted([] if faces is None else faces,key=lambda f:f[-1],reverse=True);faces=[f for f in faces if f[-1]>=threshold];source=[];x,y=a['roi_bbox'][:2]
   for f in faces:
    s=np.array(f,np.float32);s[0]+=x;s[1]+=y;s[4:14:2]+=x;s[5:14:2]+=y;source.append(s)
   boxes=[(f[0],f[1],f[0]+f[2],f[1]+f[3]) for f in source];index,failure=select_pose_face(boxes,body,r);counts=[[int(np.sum((h[:,0]>=b[0])&(h[:,0]<=b[2])&(h[:,1]>=b[1])&(h[:,1]<=b[3]))) for h in heads] for b in boxes];a['unrotated_pose_ownership']=dict(min_detection_score=threshold,sorted_yunet15_local=faces,sorted_yunet15_source=[f.tolist() for f in source],selected_index=index,failure=failure,original_body_iou=[bbox_iou(body,b) for b in r.person_bboxes],head_point_counts_by_face_and_body=counts)
   assert index is not None and failure is None,(label,data['frame_index'],v)
  (root/label/str(data['frame_index'])/'comparison.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
 path.write_text(json.dumps(report,ensure_ascii=False,indent=2));print(label,'ownership all 8 ROI/full alternatives confirmed; min score',threshold)
