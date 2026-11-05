import sys,json,time,statistics
from pathlib import Path
import cv2,numpy as np,onnx,onnxruntime as ort
root=Path('/Users/jina/project/adlight/.worktrees/mps-admission-20261104/clipper_python');sys.path[:0]=[str(root/p) for p in ('clipper_accelerators','clipper_face_core','plugins/dance_highlight')]
from clipper_accelerators.native_sessions import admit,close_all
from clipper_accelerators.face_adapter import prepare_model
from dance_highlight.services.face_runtime import configure_cpu_threads
scratch=Path('/private/tmp/clipper-mac-remaining-20261104');base=Path.home()/'Library/Application Support/Clipper Studio Dev/plugin_models/dance_highlight';source=base/'face_recognition_sface_2021dec.onnx';configure_cpu_threads()
sf=cv2.FaceRecognizerSF.create('onnx',np.frombuffer(source.read_bytes(),np.uint8),np.empty(0,np.uint8));yn=cv2.FaceDetectorYN.create('onnx',np.frombuffer((base/'face_detection_yunet_2023mar.onnx').read_bytes(),np.uint8),np.empty(0,np.uint8),(320,320),.6,.3,5000);crops=[]
for im in np.load(scratch/'yunet-mmn-inputs.npz').values():
 if im.shape[:2]!=(1080,1920):continue
 yn.setInputSize((1920,1080));faces=yn.detect(im)[1]
 for f in ([] if faces is None else faces):crops.append(sf.alignCrop(im,f))
np.savez_compressed(scratch/'sface-mmn-inputs.npz',**{str(i):v for i,v in enumerate(crops)})
refs=[sf.feature(v) for v in crops];results=[];times=[]
for i in range(3):
 for v in crops:
  start=time.perf_counter();sf.feature(v)
  if i:times.append((time.perf_counter()-start)*1000)
results.append({'engine':'opencv','mean_ms':statistics.mean(times),'median_ms':statistics.median(times),'count':len(crops)})
model=scratch/'sface-prepared.onnx';model.write_bytes(prepare_model(source))
try:
 for backend in ('ort_cpu','coreml_fp32','coreml_fp16'):
  if backend=='coreml_fp16':
   from onnxruntime.transformers.float16 import convert_float_to_float16
   from onnxruntime.transformers.onnx_model import OnnxModel
   m=convert_float_to_float16(onnx.load(model),keep_io_types=True);OnnxModel(m).topological_sort();onnx.checker.check_model(m);model=scratch/'sface-fp16.onnx';onnx.save(m,model)
  so=ort.SessionOptions();so.log_severity_level=3;so.enable_profiling=True;so.profile_file_prefix=str(scratch/'sface-profile')
  providers=['CPUExecutionProvider']
  if backend.startswith('coreml'):
   admit('ort_coreml',model_id='face.sface',estimated_bytes=model.stat().st_size*4+64*1024*1024)
   providers=[('CoreMLExecutionProvider',{'ModelFormat':'MLProgram','MLComputeUnits':'ALL','RequireStaticInputShapes':'1','ModelCacheDirectory':str(scratch/backend)}),'CPUExecutionProvider']
  start=time.perf_counter();session=ort.InferenceSession(str(model),sess_options=so,providers=providers);session.disable_fallback();load=(time.perf_counter()-start)*1000;name=session.get_inputs()[0].name;times=[];cos=[]
  for repeat in range(3):
   for v,ref in zip(crops,refs):
    start=time.perf_counter();out=session.run(None,{name:cv2.dnn.blobFromImage(v,1.,(112,112),swapRB=True,crop=False)})[0]
    if repeat:times.append((time.perf_counter()-start)*1000)
    cos.append(float(np.sum(ref*out)/(np.linalg.norm(ref)*np.linalg.norm(out))))
  counts={}
  for e in json.loads(Path(session.end_profiling()).read_text()):
   p=e.get('args',{}).get('provider')
   if p:counts[p]=counts.get(p,0)+1
  results.append({'engine':backend,'mean_ms':statistics.mean(times),'median_ms':statistics.median(times),'load_ms':load,'cosine_min':min(cos),'provider_nodes':counts});print(json.dumps(results[-1]),flush=True)
 (scratch/'sface-bench.json').write_text(json.dumps(results,indent=2))
finally:close_all()
