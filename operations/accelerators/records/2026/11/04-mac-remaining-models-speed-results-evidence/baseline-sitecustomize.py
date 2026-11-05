"""Throwaway timing hook: original model outputs and pipeline remain unchanged."""
import sys,os,json,atexit,time
from pathlib import Path
if 'clipper_accelerators.owned_stage' in getattr(sys,'orig_argv',[]):
 try:entry=json.loads(Path(sys.argv[-1]).read_text()).get('entry','')
 except (OSError,ValueError):entry=''
 if entry=='clipper_accelerators.visual_unit:execute_visual_unit':
  import numpy as np
  from dance_highlight.services.face_runtime import CachedFaceDetector
  root=Path('/private/tmp/clipper-mac-remaining-20261104/profile');root.mkdir(exist_ok=True)
  stats={};saved={};original=CachedFaceDetector._detect
  def detect(self,image):
   prior=self.stats['detection_seconds'];hits=self.stats['cache_hits'];start=time.perf_counter()
   result=original(self,image);shape=tuple(image.shape);key='x'.join(map(str,shape));row=stats.setdefault(key,{'shape':shape,'requests':0,'native_seconds':0.,'cache_hits':0,'wall_seconds':0.})
   row['requests']+=1;row['native_seconds']+=self.stats['detection_seconds']-prior;row['cache_hits']+=self.stats['cache_hits']-hits;row['wall_seconds']+=time.perf_counter()-start
   bucket=(shape[0]//256,shape[1]//256)
   if bucket not in saved and len(saved)<32:
    path=root/f'crop-{len(saved)}.npy';np.save(path,image);saved[bucket]={'path':str(path),'shape':shape}
   return result
  CachedFaceDetector._detect=detect
  def finish():
   (root/'detector-shapes.json').write_text(json.dumps({'shapes':list(stats.values()),'samples':list(saved.values())},indent=2))
  atexit.register(finish)
