import json,math
from pathlib import Path
import cv2
import numpy as np
from dance_highlight.services.camera_transitions import structural_continuity
OUT=Path('/private/tmp/dance-role-continuity-review-20261102')
MAN=json.loads((OUT/'manifest.json').read_text())
specs=[('MMN',2298,'zoom_peak'),('MMN',2360,'zoom_return'),('ANT',616,'lighting_peak'),('NEON',4912,'real_wide_cut'),('MMN',2407,'real_view_cut')]
results=[]
def describe(image):
 h,w=image.shape[:2];mask=np.zeros((h,w),np.uint8);mask[int(.15*h):int(.8*h),int(.2*w):int(.8*w)]=255
 p,d=cv2.SIFT_create(nfeatures=4000,contrastThreshold=.015).detectAndCompute(cv2.cvtColor(image,cv2.COLOR_BGR2GRAY),mask)
 return np.asarray([v.pt for v in p],np.float32),d
def matches(a,b):
 return {v[0].queryIdx:v[0].trainIdx for v in cv2.BFMatcher().knnMatch(a,b,k=2) if len(v)==2 and v[0].distance<.7*v[1].distance}
for label,f,kind in specs:
 cap=cv2.VideoCapture(MAN[label]['source']);cap.set(cv2.CAP_PROP_POS_FRAMES,f-1);ok,a=cap.read();ok2,b=cap.read();cap.release();assert ok and ok2
 cv2.setRNGSeed(0);old=structural_continuity(a,b)
 x,dx=describe(a);y,dy=describe(b);forward,reverse=matches(dx,dy),matches(dy,dx);pairs=[(i,j) for i,j in forward.items() if reverse.get(j)==i]
 row={'video':label,'frame':f,'kind':kind,'existing_structure':old,'match_count':len(pairs),'fit':None}
 if len(pairs)>=3:
  p=np.asarray([x[i] for i,j in pairs]);q=np.asarray([y[j] for i,j in pairs]);cv2.setRNGSeed(0)
  matrix,mask=cv2.estimateAffinePartial2D(p,q,method=cv2.RANSAC,ransacReprojThreshold=3.)
  if matrix is not None:
   good=mask.ravel().astype(bool);mapped=cv2.transform(p.reshape(1,-1,2),matrix)[0];res=np.linalg.norm(mapped-q,axis=1)
   row['fit']={'matrix':matrix.tolist(),'inliers':int(good.sum()),'inlier_ratio':float(good.mean()),'scale':float(np.linalg.norm(matrix[:,0])),
               'rotation_degrees':float(math.degrees(math.atan2(matrix[1,0],matrix[0,0]))),
               'inlier_p90_compensated_residual':float(np.quantile(res[good],.9)),
               'all_match_p90_compensated_residual':float(np.quantile(res,.9))}
 canvas=np.concatenate([cv2.resize(a,(640,360)),cv2.resize(b,(640,360))],axis=1)
 cv2.imwrite(str(OUT/f'{label}-{f}-exact-pair.jpg'),canvas,[cv2.IMWRITE_JPEG_QUALITY,95])
 results.append(row);print(json.dumps(row),flush=True)
(OUT/'structural-pair-checks.json').write_text(json.dumps(results,indent=2)+'\n')
