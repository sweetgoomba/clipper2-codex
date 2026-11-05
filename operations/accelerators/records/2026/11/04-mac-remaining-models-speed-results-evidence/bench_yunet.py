import os,sys,json,time,statistics
from pathlib import Path
import numpy as np,cv2,onnx,onnxruntime as ort
root=Path('/Users/jina/project/adlight/.worktrees/mps-admission-20261104/clipper_python')
sys.path[:0]=[str(root/p) for p in ('clipper_accelerators','clipper_face_core','plugins/dance_highlight')]
from clipper_accelerators.face_adapter import decode_yunet
from dance_highlight.services.face_cluster import FaceClusterService
from dance_highlight.services.config import DanceConfig
from dance_highlight.services.face_runtime import configure_cpu_threads
scratch=Path('/private/tmp/clipper-mac-remaining-20261104');data=Path.home()/'Library/Application Support/Clipper Studio Dev'
model_path=data/'plugin_models/dance_highlight/face_detection_yunet_2023mar.onnx'
m=onnx.load(model_path)
for i,p in ((2,'height'),(3,'width')):
 dim=m.graph.input[0].type.tensor_type.shape.dim[i];dim.ClearField('dim_value');dim.dim_param=p
for out in m.graph.output:
 dim=out.type.tensor_type.shape.dim[1];dim.ClearField('dim_value');dim.dim_param='anchors_'+out.name.rsplit('_',1)[-1]
del m.graph.value_info[:];onnx.checker.check_model(m);onnx.save(m,scratch/'yunet-dynamic.onnx')
config=DanceConfig();service=FaceClusterService.__new__(FaceClusterService);service.config=config
pose=json.loads(next(Path('/private/tmp/clipper-face-speed-20261104/mmn').rglob('face_evidence.json')).read_text())['pose_heads']
cap=cv2.VideoCapture(str(data/'sources/youtube/BZDZBUyaJbA/source.mp4'));images=[]
for sec in [0,20,50,75,100,130]:
 cap.set(cv2.CAP_PROP_POS_MSEC,sec*1000);ok,frame=cap.read();assert ok
 row=min(pose,key=lambda r:abs(r['time_seconds']-sec));h,w=frame.shape[:2]
 # Actual Dance expand_face_roi at frozen pose boxes, plus native whole frame.
 for box in row['body_boxes'][:2]:
  x1,y1,x2,y2=service.expand_face_roi(np.asarray(box,np.float32),w,h);images.append(np.ascontiguousarray(frame[y1:y2,x1:x2]))
 if sec in (0,50):images.append(frame)
cap.release();configure_cpu_threads()
np.savez_compressed(scratch/'yunet-mmn-inputs.npz',**{str(i):im for i,im in enumerate(images)})
detector=cv2.FaceDetectorYN.create('onnx',np.frombuffer(model_path.read_bytes(),np.uint8),np.empty(0,np.uint8),(320,320),float(config.face_min_det_score),float(config.face_nms_threshold),int(config.face_top_k))
baseline=[];times=[]
for repeat in range(3):
 outputs=[];current=[]
 for image in images:
  h,w=image.shape[:2];detector.setInputSize((w,h));start=time.perf_counter();value=detector.detect(image)[1];current.append((time.perf_counter()-start)*1000);outputs.append(value)
 if repeat:times.extend(current)
 baseline=outputs
results=[{'engine':'opencv','mean_ms':statistics.mean(times),'median_ms':statistics.median(times),'total_ms':sum(times)/2}]
for threads in [0,1,2,4]:
 so=ort.SessionOptions();so.intra_op_num_threads=threads;so.log_severity_level=3
 start=time.perf_counter();session=ort.InferenceSession(str(scratch/'yunet-dynamic.onnx'),sess_options=so,providers=['CPUExecutionProvider']);load_ms=(time.perf_counter()-start)*1000
 name=session.get_inputs()[0].name;names=[v.name for v in session.get_outputs()];times=[];rows=[]
 for repeat in range(3):
  rows=[]
  for i,image in enumerate(images):
   start=time.perf_counter();h,w=image.shape[:2];padded=((w+31)//32*32,(h+31)//32*32)
   blob=cv2.dnn.blobFromImage(cv2.copyMakeBorder(image,0,padded[1]-h,0,padded[0]-w,cv2.BORDER_CONSTANT))
   outputs=dict(zip(names,session.run(None,{name:blob}),strict=True));value=decode_yunet(outputs,padded,float(config.face_min_det_score),float(config.face_nms_threshold),int(config.face_top_k))
   elapsed=(time.perf_counter()-start)*1000
   if repeat:times.append(elapsed)
   reference=baseline[i];same=(value is None)==(reference is None) and (value is None or value.shape==reference.shape)
   diff=float(np.max(np.abs(value-reference))) if same and value is not None else None
   rows.append({'shape':list(image.shape),'count':0 if value is None else len(value),'cpu_count':0 if reference is None else len(reference),'max_abs_diff':diff})
 results.append({'engine':'ort_cpu','threads':threads,'load_ms':load_ms,'mean_ms':statistics.mean(times),'median_ms':statistics.median(times),'total_ms':sum(times)/2,'samples':rows})
 print(json.dumps(results[-1]),flush=True)
(scratch/'yunet-cpu-bench.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results[0]),flush=True)
