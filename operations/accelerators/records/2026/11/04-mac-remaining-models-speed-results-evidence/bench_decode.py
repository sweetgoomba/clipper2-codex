from pathlib import Path
import cv2,time,json,hashlib
video=str(Path.home()/'Library/Application Support/Clipper Studio Dev/sources/youtube/BZDZBUyaJbA/source.mp4');results=[];frames={}
for mode in ('default','any'):
 params=[] if mode=='default' else [cv2.CAP_PROP_HW_ACCELERATION,cv2.VIDEO_ACCELERATION_ANY]
 cap=cv2.VideoCapture(video,cv2.CAP_FFMPEG,params);opened=cap.isOpened();start=time.perf_counter();values=[];digests=[]
 if opened:
  for i in range(1200):
   if i%4:
    assert cap.grab()
   else:
    ok,frame=cap.read();assert ok
    if i in (0,100,200,300,400):digests.append(hashlib.sha256(frame.tobytes()).hexdigest())
  backend=cap.getBackendName();hw=cap.get(cv2.CAP_PROP_HW_ACCELERATION)
 else:backend=None;hw=None
 cap.release();results.append({'mode':mode,'opened':opened,'backend':backend,'hw':hw,'seconds':time.perf_counter()-start,'hashes':digests})
Path('/private/tmp/clipper-mac-remaining-20261104/decode-bench.json').write_text(json.dumps(results,indent=2));print(json.dumps(results))
