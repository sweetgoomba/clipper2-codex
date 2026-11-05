from pathlib import Path
import json,hashlib
import cv2,numpy as np
P=Path(__file__).parent;R=Path('/Users/jina/Library/Application Support/Clipper Studio Dev/projects/files/116957ce-bd03-4d4a-a21d-984dc12487aa');oldroot,newroot=[R/i for i in ['1793633791815','1793639268565']]
a,b=[json.loads((r/'diagnostics/face_evidence.json').read_text()) for r in [oldroot,newroot]];meta=json.loads((newroot/'json/dance_meta.json').read_text());target=next(r for r in meta['diagnostics']['clips'] if r['seg_type']=='main' and abs(r['start']-98.23146666666666)<1e-7)
oldrows={o['frame_index']:o for s in a['segments'][:a['main_result_count']] for o in s['owned_observations']};rows={o['frame_index']:o for s in b['segments'][:b['main_result_count']] for o in s['owned_observations'] if target['start']<=o['time_seconds']<target['end'] and o['face_bbox'] is not None and o['association']=='confirmed' and not o['failure']}
queries={p:hashlib.sha256((newroot/p).read_bytes()).hexdigest() for p in target['query_images']};matches={p:[] for p in queries};cap=cv2.VideoCapture(str(newroot/'diagnostics/source.mp4'));cv2.setNumThreads(1)
try:
 for frame,row in sorted(rows.items()):
  assert cap.set(cv2.CAP_PROP_POS_FRAMES,frame);ok,image=cap.read();assert ok and abs(cap.get(cv2.CAP_PROP_POS_FRAMES)-(frame+1))<.1
  x1,y1,x2,y2=map(int,row['roi_bbox']);roi=image[y1:y2,x1:x2];h,w=roi.shape[:2];fx1,fy1,fx2,fy2=np.asarray(row['face_bbox'])-np.array([x1,y1,x1,y1]);side=min(w,h,int(np.ceil(max(fx2-fx1,fy2-fy1)*1.4)));left=max(0,min(w-side,int((fx1+fx2-side)/2)));top=max(0,min(h-side,int((fy1+fy2-side)/2)));crop=roi[top:top+side,left:left+side]
  if side>256:crop=cv2.resize(crop,(256,256),interpolation=cv2.INTER_AREA)
  ok,jpg=cv2.imencode('.jpg',crop,[cv2.IMWRITE_JPEG_QUALITY,92]);assert ok;digest=hashlib.sha256(jpg.tobytes()).hexdigest()
  for p,v in queries.items():
   if digest==v:matches[p].append(dict(frame=frame,time=row['time_seconds'],quality=row['quality'],original_observation_identical=oldrows.get(frame)==row,original_joint=a['secondary_reference_refinement']['joint_matches'].get(str(frame),{}).get('name')))
finally:cap.release()
assert all(len(v)==1 and v[0]['original_observation_identical'] and v[0]['original_joint']==target['person_id'] for v in matches.values()),matches
newframes=[v[0]['frame'] for v in matches.values() if 98.2982<=v[0]['time']<98.531767]
assert sorted(newframes)==[5892,5896,5900,5904]
report=dict(scope='No model inference. JPEG92 source-ROI reconstruction exactly matches all5 diagnostic face queries;4 newly displayed crops belong to approved restored time.',range=[target['start'],target['end']],person_id=target['person_id'],matches=matches,newly_displayed_original_frames=sorted(newframes),all_exact_source_bytes=True)
(P/'neon-query-original-source-proof.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False))
