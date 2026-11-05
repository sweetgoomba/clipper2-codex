import sys,json,time,statistics
from pathlib import Path
import cv2,numpy as np,onnx,onnxruntime as ort
root=Path('/Users/jina/project/adlight/.worktrees/mps-admission-20261104/clipper_python');sys.path[:0]=[str(root/p) for p in ('clipper_accelerators','clipper_face_core','plugins/dance_highlight')]
from clipper_accelerators.native_sessions import admit,close_all
from clipper_accelerators.face_adapter import decode_yunet,prepare_model
from dance_highlight.services.config import DanceConfig
from dance_highlight.services.face_runtime import configure_cpu_threads
scratch=Path('/private/tmp/clipper-mac-remaining-20261104');source=Path.home()/'Library/Application Support/Clipper Studio Dev/plugin_models/dance_highlight/face_detection_yunet_2023mar.onnx';config=DanceConfig();configure_cpu_threads();images=[]
cap=cv2.VideoCapture(str(Path.home()/'Library/Application Support/Clipper Studio Dev/sources/youtube/BZDZBUyaJbA/source.mp4'))
for t in (0,10,30,50,75,100,130,150):
 cap.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,im=cap.read();assert ok;images.append(im)
cap.release();h,w=images[0].shape[:2];padded=((w+31)//32*32,(h+31)//32*32)
model=scratch/'yunet-static.onnx';model.write_bytes(prepare_model(source,spatial_size=padded))
native=cv2.FaceDetectorYN.create('onnx',np.frombuffer(source.read_bytes(),np.uint8),np.empty(0,np.uint8),(w,h),float(config.face_min_det_score),float(config.face_nms_threshold),int(config.face_top_k));refs=[];cpu=[]
for im in images:
 start=time.perf_counter();refs.append(native.detect(im)[1]);cpu.append((time.perf_counter()-start)*1000)
results=[{'backend':'opencv','median_ms':statistics.median(cpu),'mean_ms':statistics.mean(cpu)}]
try:
 admit('ort_coreml',model_id='face.yunet',estimated_bytes=256*1024*1024)
 for precision in ('fp32','fp16'):
  if precision=='fp16':
   from onnxruntime.transformers.float16 import convert_float_to_float16
   from onnxruntime.transformers.onnx_model import OnnxModel
   m=convert_float_to_float16(onnx.load(model),keep_io_types=True);OnnxModel(m).topological_sort();onnx.checker.check_model(m);model=scratch/'yunet-static-fp16.onnx';onnx.save(m,model)
  so=ort.SessionOptions();so.log_severity_level=3;so.enable_profiling=True;so.profile_file_prefix=str(scratch/'static-yunet-profile');so.intra_op_num_threads=1
  start=time.perf_counter();s=ort.InferenceSession(str(model),sess_options=so,providers=[('CoreMLExecutionProvider',{'ModelFormat':'MLProgram','MLComputeUnits':'ALL','RequireStaticInputShapes':'1','ModelCacheDirectory':str(scratch/('coreml-static-yunet-'+precision))}),'CPUExecutionProvider']);s.disable_fallback();load=(time.perf_counter()-start)*1000
  names=[v.name for v in s.get_outputs()];name=s.get_inputs()[0].name;timings=[];rows=[]
  for repeat in range(3):
   rows=[]
   for i,im in enumerate(images):
    start=time.perf_counter();blob=cv2.dnn.blobFromImage(cv2.copyMakeBorder(im,0,padded[1]-h,0,padded[0]-w,cv2.BORDER_CONSTANT));out=s.run(None,{name:blob});value=decode_yunet(dict(zip(names,out)),padded,float(config.face_min_det_score),float(config.face_nms_threshold),int(config.face_top_k));elapsed=(time.perf_counter()-start)*1000
    if repeat:timings.append(elapsed)
    ref=refs[i];same=(value is None)==(ref is None) and (value is None or value.shape==ref.shape)
    rows.append({'count':0 if value is None else len(value),'cpu_count':0 if ref is None else len(ref),'max_abs_diff':float(np.max(np.abs(value-ref))) if same and value is not None else None})
  counts={}
  for e in json.loads(Path(s.end_profiling()).read_text()):
   provider=e.get('args',{}).get('provider')
   if provider:counts[provider]=counts.get(provider,0)+1
  results.append({'backend':'coreml','precision':precision,'load_ms':load,'median_ms':statistics.median(timings),'mean_ms':statistics.mean(timings),'provider_nodes':counts,'samples':rows});print(json.dumps(results[-1]),flush=True)
 (scratch/'yunet-static-bench.json').write_text(json.dumps(results,indent=2))
finally:close_all()
