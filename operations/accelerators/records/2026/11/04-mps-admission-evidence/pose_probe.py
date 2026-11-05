import os,sys,json,time
from pathlib import Path
root=Path('/Users/jina/project/adlight/.worktrees/mps-admission-20261104/clipper_python')
for name in ['clipper_accelerators','clipper_plugin_sdk','clipper_face_core','plugins/dance_highlight']:sys.path.insert(0,str(root/name))
from clipper_accelerators import runtime
from clipper_accelerators.native_sessions import close_all,operation_reservation
import torch,cv2
from ultralytics import YOLO
from dance_highlight.services.pose_engine import PoseEngine
from dance_highlight.services.config import DanceConfig
import numpy as np,hashlib
from clipper_accelerators.model_boundary import model_call
runtime.configure({'acceleration_mode':'auto'},'mps','/private/tmp/clipper-mps-admission-20261104/pose',consumer='dance_highlight')
video='/Users/jina/Library/Application Support/Clipper Studio Dev/sources/youtube/BZDZBUyaJbA/source.mp4'
cap=cv2.VideoCapture(video);cap.set(cv2.CAP_PROP_POS_MSEC,50000);ok,frame=cap.read();cap.release();assert ok
weights='/Users/jina/Library/Application Support/Clipper Studio Dev/yolov8s-pose.pt'
engine=PoseEngine(DanceConfig(yolo_model_path=weights,yolo_device='mps',yolo_half=False));model=engine._model
model_id,estimated=operation_reservation(model,(frame,));calls=[]
try:
 for _ in range(2):
  start=time.perf_counter();out=engine.run_pose_on_frame(frame);torch.mps.synchronize()
  calls.append({'milliseconds':(time.perf_counter()-start)*1000,'people':len(out),'model_device':str(next(model.model.parameters()).device),'allocated_bytes':torch.mps.current_allocated_memory()})
 gpu_report=runtime.diagnostics()
 cpu=YOLO(weights)(frame,imgsz=640,device='cpu',half=False,conf=.25,iou=.7,verbose=False)[0]
 boxes=cpu.boxes.xyxy.cpu().numpy();ious=[];remaining=list(range(len(boxes)))
 for person in out:
  box=person['bbox'];scores=[]
  for i in remaining:
   other=boxes[i];lo=np.maximum(box[:2],other[:2]);hi=np.minimum(box[2:],other[2:]);area=np.maximum(hi-lo,0).prod();scores.append((float(area/((box[2:]-box[:2]).prod()+(other[2:]-other[:2]).prod()-area)),i))
  score,index=max(scores);ious.append(score);remaining.remove(index)
 print('PROBE_JSON='+json.dumps({'ok':True,'estimated_bytes':estimated,'frame_shape':frame.shape,'frame_sha256':hashlib.sha256(frame.tobytes()).hexdigest(),'calls':calls,'gpu_diagnostics':gpu_report,'cpu_people':len(boxes),'iou_min':min(ious)}))
except Exception as error:
 print('PROBE_JSON='+json.dumps({'ok':False,'estimated_bytes':estimated,'kind':getattr(error,'kind',None),'message':str(error),'details':getattr(error,'details',None),'calls':calls}))
finally:close_all()
