import sys,json,time
from pathlib import Path
if 'clipper_accelerators.owned_stage' in getattr(sys,'orig_argv',[]):
 try:entry=json.loads(Path(sys.argv[-1]).read_text()).get('entry','')
 except (OSError,ValueError):entry=''
 if entry=='clipper_accelerators.visual_unit:execute_visual_unit':
  from clipper_accelerators.native_face import CoreMLFaceSession
  from clipper_accelerators.native_yunet import StaticYuNet
  records=[]
  def wrap(cls):
   old=cls._record
   def record(self,*args,**kwargs):
    row=old(self,*args,**kwargs);records.append({'at':time.time(),'record':row.report()})
    p=Path('/private/tmp/clipper-mac-remaining-20261104/final-selections.json');tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(records,ensure_ascii=False,indent=2));tmp.replace(p)
    return row
   cls._record=record
  wrap(CoreMLFaceSession);wrap(StaticYuNet)
  from dance_highlight.services.pose_engine import PoseEngine
  pose_release=PoseEngine.release_mps_model
  def release_pose(self):
   import sys
   torch=sys.modules.get('torch');before=torch.mps.current_allocated_memory() if torch is not None else None
   result=pose_release(self)
   after=torch.mps.current_allocated_memory() if torch is not None else None
   records.append({'at':time.time(),'record':{'model_id':'pose.phase_release','released':result,'mps_before_bytes':before,'mps_after_bytes':after}})
   p=Path('/private/tmp/clipper-mac-remaining-20261104/final-selections.json');tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(records,ensure_ascii=False,indent=2));tmp.replace(p)
   return result
  PoseEngine.release_mps_model=release_pose
