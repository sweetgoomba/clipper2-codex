import json,cv2,numpy as np
from pathlib import Path
s=Path('/private/tmp/dance-astra-review-20261102');out=Path('/private/tmp/dance-astra-parent-validation-20261102');manifest=json.loads((s/'manifest.json').read_text());rows=[]
for label,info in manifest.items():
 a=json.loads((s/f'{label}-one-sided-summary.json').read_text());e=json.loads(Path(info['evidence']).read_text());fps=info['fps'];pose={round(r['time_seconds']*fps):r for r in e['pose_heads']};cap=cv2.VideoCapture(info['video'])
 for p in a['proposals']:
  frames=[round(p['start']*fps),round((p['start']+p['end'])/2*fps),round((p['end']-.001)*fps),*p['proof']['seeds']];tiles=[]
  for f in frames:
   cap.set(cv2.CAP_PROP_POS_FRAMES,f);ok,img=cap.read()
   if not ok:raise RuntimeError(f)
   r=pose[min(pose,key=lambda k:abs(k-f))];box=r['candidate_main_bbox']
   if box is not None:cv2.rectangle(img,tuple(np.rint(box[:2]).astype(int)),tuple(np.rint(box[2:]).astype(int)),(0,0,255),4)
   tile=cv2.resize(img,(384,216));tile=cv2.copyMakeBorder(tile,30,0,0,0,cv2.BORDER_CONSTANT,value=(255,255,255));cv2.putText(tile,f'{label} {f/fps:.3f}s f{f}',(8,20),cv2.FONT_HERSHEY_SIMPLEX,.5,(0,0,0),1);tiles.append(tile)
  rows.append(np.hstack(tiles))
 cap.release()
cv2.imwrite(str(out/'five-candidates.jpg'),np.vstack(rows))
