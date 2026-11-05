import sys,json,time,statistics
from pathlib import Path
import cv2,numpy as np,onnxruntime as ort
root=Path('/Users/jina/project/adlight/.worktrees/mps-admission-20261104/clipper_python');sys.path[:0]=[str(root/p) for p in ('clipper_accelerators','clipper_face_core','plugins/dance_highlight')]
from clipper_accelerators.native_sessions import admit,close_all
from clipper_accelerators.face_adapter import decode_yunet
from dance_highlight.services.config import DanceConfig
from dance_highlight.services.face_runtime import configure_cpu_threads
scratch=Path('/private/tmp/clipper-mac-remaining-20261104');model=scratch/'yunet-dynamic.onnx';images=list(np.load(scratch/'yunet-mmn-inputs.npz').values());config=DanceConfig();configure_cpu_threads()
source=Path.home()/'Library/Application Support/Clipper Studio Dev/plugin_models/dance_highlight/face_detection_yunet_2023mar.onnx'
native=cv2.FaceDetectorYN.create('onnx',np.frombuffer(source.read_bytes(),np.uint8),np.empty(0,np.uint8),(320,320),float(config.face_min_det_score),float(config.face_nms_threshold),int(config.face_top_k))
baseline=[]
for im in images:
 h,w=im.shape[:2];native.setInputSize((w,h));baseline.append(native.detect(im)[1])
results=[]
try:
 admit('ort_coreml',model_id='face.yunet',estimated_bytes=256*1024*1024)
 for model_format,units in [('MLProgram','ALL'),('NeuralNetwork','ALL')]:
  so=ort.SessionOptions();so.log_severity_level=3;so.enable_profiling=True;so.profile_file_prefix=str(scratch/'yunet-profile');so.intra_op_num_threads=1
  start=time.perf_counter();s=ort.InferenceSession(str(model),sess_options=so,providers=[('CoreMLExecutionProvider',{'ModelFormat':model_format,'MLComputeUnits':units,'RequireStaticInputShapes':'0','ModelCacheDirectory':str(scratch/('coreml-yunet-'+model_format))}),'CPUExecutionProvider']);s.disable_fallback();load=(time.perf_counter()-start)*1000
  names=[v.name for v in s.get_outputs()];name=s.get_inputs()[0].name;timings=[];cold=[];rows=[]
  for repeat in range(3):
   rows=[]
   for i,image in enumerate(images):
    h,w=image.shape[:2];padded=((w+31)//32*32,(h+31)//32*32);start=time.perf_counter();blob=cv2.dnn.blobFromImage(cv2.copyMakeBorder(image,0,padded[1]-h,0,padded[0]-w,cv2.BORDER_CONSTANT));out=s.run(None,{name:blob});value=decode_yunet(dict(zip(names,out)),padded,float(config.face_min_det_score),float(config.face_nms_threshold),int(config.face_top_k));elapsed=(time.perf_counter()-start)*1000
    (cold if repeat==0 else timings).append(elapsed);ref=baseline[i];same=(value is None)==(ref is None) and (value is None or value.shape==ref.shape)
    rows.append({'shape':list(image.shape),'count':0 if value is None else len(value),'cpu_count':0 if ref is None else len(ref),'max_abs_diff':float(np.max(np.abs(value-ref))) if same and value is not None else None})
  profile=Path(s.end_profiling());counts={}
  for event in json.loads(profile.read_text()):
   provider=event.get('args',{}).get('provider')
   if provider:counts[provider]=counts.get(provider,0)+1
  results.append({'format':model_format,'load_ms':load,'mean_ms':statistics.mean(timings),'median_ms':statistics.median(timings),'total_ms':sum(timings)/2,'cold_ms':cold,'provider_nodes':counts,'samples':rows});print(json.dumps(results[-1]),flush=True)
 (scratch/'yunet-coreml-bench.json').write_text(json.dumps(results,indent=2)+'\n')
finally:close_all()
