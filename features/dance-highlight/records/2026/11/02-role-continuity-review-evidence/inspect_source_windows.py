"""Pixel/pose inspection only: no model, app job, or source modification."""
import hashlib,json,math
from pathlib import Path
import cv2
import numpy as np
from dance_highlight.services.face_evidence import FaceObservation
from dance_highlight.services.segment import FrameRec
from dance_highlight.services.body_continuity import _color_cut,_appearance,_unique_body_link,_unique_pose_link,_check_source_chain
from dance_highlight.services.track import bbox_iou

OUT=Path('/private/tmp/dance-role-continuity-review-20261102')
MAN=json.loads((OUT/'manifest.json').read_text())
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
 return h.hexdigest()

reports={}
for label,info in MAN.items():
 e=json.loads(Path(info['evidence']).read_text());m=json.loads(Path(info['meta']).read_text());fps=info['fps'];a,b=info['candidate'][0]['seed_frames']
 raw={r['frame_index']:r for seg in e['segments'][:e['main_result_count']] for r in seg['owned_observations']}
 obs={f:FaceObservation(**(r|{'embedding':None if r['embedding'] is None else np.asarray(r['embedding'],np.float32)})) for f,r in raw.items() if a<=f<=b}
 pose={round(p['time_seconds']*fps):p for p in e['pose_heads']}
 recs={f:FrameRec(p['time_seconds'],p['candidate_main_id'],None if p['candidate_main_bbox'] is None else np.asarray(p['candidate_main_bbox']),p['scene_kind']=='group',
     person_bboxes=[np.asarray(x) for x in p['body_boxes']],person_pose_keypoints=[np.asarray(x) for x in p['pose_keypoints']],scene_kind=p['scene_kind']) for f,p in pose.items() if a-8<=f<=b+8}
 roles={r['frame']:r for r in e['main_selection_refinement']['role_observations']}
 joints={int(k):v for k,v in e['secondary_reference_refinement']['joint_matches'].items()}
 cap=cv2.VideoCapture(info['source']);audit={};actual=_check_source_chain(cap,[obs[f] for f in sorted(obs)],recs,audit=audit);cap.release()
 cap=cv2.VideoCapture(info['source']);cap.set(cv2.CAP_PROP_POS_FRAMES,a-8)
 frames={};pairs=[];bodies=[];old_body=old_rec=None;prev=None
 for f in range(a-8,b+9):
  ok,img=cap.read()
  if not ok: raise RuntimeError((label,'decode',f))
  assert abs(cap.get(cv2.CAP_PROP_POS_FRAMES)-(f+1))<.1
  frames[f]=cv2.resize(img,(960,540))
  if a<=f<=b:
   small=cv2.resize(img,(64,36))
   if prev is not None:
    cut,luma=_color_cut(prev,small)
    hist=[]
    for s in (prev,small):
     h=cv2.calcHist([cv2.cvtColor(s,cv2.COLOR_BGR2HSV)],[0,1],None,[16,8],[0,180,0,256]);hist.append(cv2.normalize(h,h))
    pairs.append({'frame':f,'time':f/fps,'luma':luma,'color':cv2.compareHist(*hist,cv2.HISTCMP_BHATTACHARYYA),'color_cut':bool(cut)})
   prev=small
   if f in obs:
    row,rec=obs[f],recs[f];owners=[i for i,box in enumerate(rec.person_bboxes) if bbox_iou(np.asarray(row.body_bbox),box)>=.7]
    body={'frame':f,'time':f/fps,'owners':owners,'role':roles[f]['reason'],'selected_box':rec.main_bbox.tolist() if rec.main_bbox is not None else None,
          'scene':rec.scene_kind,'body_count':len(rec.person_bboxes),'valid_face':row.association=='confirmed' and not row.failure and row.embedding is not None and row.detector_score>=.8,
          'face_failure':row.failure,'detector':row.detector_score,'joint_status':joints.get(f,{}).get('status'),'joint_name':joints.get(f,{}).get('name')}
    if len(owners)==1:
     current=(rec.person_bboxes,[_appearance(img,box) for box in rec.person_bboxes],owners[0])
     if old_body is not None:
      body['appearance_link']=bool(_unique_body_link(old_body,current))
      body['pose_link']=bool(_unique_pose_link(old_rec,rec,old_body[2],owners[0]))
      body['either_link']=body['appearance_link'] or body['pose_link']
     old_body,old_rec=current,rec
    bodies.append(body)
 cap.release()
 peak=max(pairs,key=lambda p:p['luma']);median=float(np.median([p['luma'] for p in pairs]))
 interesting=sorted({peak['frame'],*[x['frame'] for x in pairs if x['color_cut']],*[x['frame'] for x in pairs if x['luma']>max(6.,3*median)]})
 chosen=sorted({a,b,round(info['start']*fps),round(info['end']*fps),*[round(x) for x in np.linspace(a,b,6)],peak['frame']-1,peak['frame']})
 chosen=[f for f in chosen if f in frames]
 cols=3;w,h=480,310;canvas=np.zeros((math.ceil(len(chosen)/cols)*h,cols*w,3),np.uint8)
 for k,f in enumerate(chosen):
  im=frames[f].copy(); nearby=min(recs,key=lambda x:abs(x-f));r=recs[nearby]
  for box in r.person_bboxes:
   x,y,xx,yy=(np.asarray(box)*.5).astype(int);cv2.rectangle(im,(x,y),(xx,yy),(160,160,160),1)
  if r.main_bbox is not None:
   x,y,xx,yy=(r.main_bbox*.5).astype(int);cv2.rectangle(im,(x,y),(xx,yy),(0,255,255),3)
  im=cv2.resize(im,(480,270));tile=np.zeros((h,w,3),np.uint8);tile[40:]=im
  cv2.putText(tile,f'{label} frame {f}  {f/fps:.4f}s  pose {nearby}',(7,16),cv2.FONT_HERSHEY_SIMPLEX,.42,(255,255,255),1,cv2.LINE_AA)
  cv2.putText(tile,roles.get(nearby,{}).get('reason','')[:62],(7,33),cv2.FONT_HERSHEY_SIMPLEX,.35,(180,220,255),1,cv2.LINE_AA)
  y,x=divmod(k,cols);canvas[y*h:(y+1)*h,x*w:(x+1)*w]=tile
 cv2.imwrite(str(OUT/f'{label}-source-contact.jpg'),canvas,[cv2.IMWRITE_JPEG_QUALITY,94])
 for f in interesting:
  cv2.imwrite(str(OUT/f'{label}-pair-{f-1}.jpg'),frames[f-1],[cv2.IMWRITE_JPEG_QUALITY,95])
  cv2.imwrite(str(OUT/f'{label}-pair-{f}.jpg'),frames[f],[cv2.IMWRITE_JPEG_QUALITY,95])
 refs=(obs[a],obs[b]);alien=[]
 for f,o in obs.items():
  if o.association=='confirmed' and not o.failure and o.embedding is not None and o.detector_score>=.8:
   dist=[1.-float(o.embedding@seed.embedding) for seed in refs]
   if min(dist)>.65:alien.append({'frame':f,'time':o.time_seconds,'seed_distances':dist})
 reports[label]={'source_sha256':sha(info['source']),'runtime_video_sha256':e['runtime']['video_sha256'],'seed_frames':[a,b],
     'original_check_reason':actual,'original_check_audit':audit,'max_luma':peak,'median_luma':median,'old_spike_limit':max(6.,3*median),
     'suspicious_pairs':interesting,'pixel_pairs':pairs,'body_steps':bodies,'alien_valid_faces':alien,
     'handoffs':[x for x in e['main_selection_refinement']['handoffs'] if x['previous_frame']<=b and x['frame']>=a],
     'cuts':[f for f in e['main_selection_refinement']['cut_frames'] if a<=f<=b],
     'group_clips':[c for c in m['lists']['group'] if c['start']<b/fps and c['end']>a/fps]}
 print(label,'reason',actual,'luma',peak['luma'],'median',median,'suspicious',interesting,'body failures',[(x['frame'],x.get('either_link'),x['owners']) for x in bodies if len(x['owners'])!=1 or x.get('either_link') is False],flush=True)
(OUT/'source-window-inspection.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2)+'\n')
