from pathlib import Path
from types import SimpleNamespace
import json,time,gc,statistics,sys,traceback,hashlib
import cv2,numpy as np,torch,onnxruntime as ort
from ultralytics.models.sam import SAM2VideoPredictor
from dance_highlight.services.mask_tracker import MaskTracker,head_owners
from clipper_face_core.auraface import AuraFaceRecognizer
ROOT=Path('/Users/jina/Library/Application Support/Clipper Studio Dev')
OUT=Path('/private/tmp/dance-gpu-audit-20261102')
MODELS=ROOT/'plugin_models/dance_highlight'
PROJECTS=ROOT/'projects/files/116957ce-bd03-4d4a-a21d-984dc12487aa'
CASES=[('ANTIFRAGILE','1793237055448',4.57),('NEON','1793237089917',78.38),('Made My Night','1793236627928',37.74)]
torch.set_num_threads(1);cv2.setNumThreads(1)
report={'torch':torch.__version__,'ort':ort.__version__,'mps':torch.backends.mps.is_available(),'providers':ort.get_available_providers(),'threads':torch.get_num_threads(),'sam':[],'face':{}}
def save(): (OUT/'results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
def emit(x): print(json.dumps(x,ensure_ascii=False),flush=True)
inputs=[]
for name,pid,start in CASES:
 meta=json.loads((PROJECTS/pid/'json/dance_meta.json').read_text())
 evidence=json.loads((PROJECTS/pid/'diagnostics/face_evidence.json').read_text())
 poses=[p for p in evidence['pose_heads'] if start<=p['time_seconds']<=start+1.55 and p.get('candidate_main_bbox')]
 video=meta['input_video'];cap=cv2.VideoCapture(video);fps=cap.get(cv2.CAP_PROP_FPS);cap.release()
 inputs.append((name,video,fps,poses))
# Same installed adapter, model, original frames, prompts and dtype. Only override constructor device in this process.
if 'sam' in sys.argv:
 original_init=SAM2VideoPredictor.__init__
 for name,video,fps,poses in inputs:
  masks_by_device={};owners_by_device={};item={'name':name,'frames':len(poses),'seconds':[p['time_seconds'] for p in poses]}
  for device in ['cpu','mps']:
   def init(self,*args,**kwargs):
    kwargs['overrides']=dict(kwargs.get('overrides',{}),device=device)
    return original_init(self,*args,**kwargs)
   SAM2VideoPredictor.__init__=init
   try:
    t=time.perf_counter();tracker=MaskTracker(video,fps,model_path=MODELS/'sam2.1_t.pt');setup=time.perf_counter()-t
   finally: SAM2VideoPredictor.__init__=original_init
   item[device]={'setup_sec':setup,'actual_device':str(tracker.predictor.device),'dtype':str(next(tracker.predictor.model.parameters()).dtype)}
   try:
    records=[SimpleNamespace(t=p['time_seconds']) for p in poses];runs=[]
    for repeat in range(2):
     cap=cv2.VideoCapture(video)
     if device=='mps':torch.mps.synchronize()
     t=time.perf_counter(); masks=[];owners=[]
     for pose,(_,_,mask) in zip(poses,tracker._masks(cap,records,bboxes=[poses[0]['candidate_main_bbox']]),strict=True):
      masks.append(mask);owners.append(head_owners(mask,[np.asarray(x) for x in pose['head_keypoints']]))
     if device=='mps':torch.mps.synchronize()
     runs.append(time.perf_counter()-t);cap.release()
    masks_by_device[device]=masks;owners_by_device[device]=owners
    item[device].update(runs_sec=runs,cache_hits=tracker.predictor.image_features.hits,cache_misses=tracker.predictor.image_features.misses)
   except Exception as e: item[device]['error']=repr(e);traceback.print_exc()
   del tracker;gc.collect()
   if device=='mps':torch.mps.empty_cache()
  if len(masks_by_device)==2:
   ious=[float(np.count_nonzero(a&b)/max(1,np.count_nonzero(a|b))) for a,b in zip(masks_by_device['cpu'],masks_by_device['mps'])]
   item['mask_iou_min']=min(ious);item['mask_iou_mean']=statistics.mean(ious)
   item['head_owner_differences']=sum(a!=b for a,b in zip(owners_by_device['cpu'],owners_by_device['mps']))
  report['sam'].append(item);save();emit(item)
# Real face crops, same alignment/preprocessing; measure model inference separately from I/O/detection.
if 'face' in sys.argv:
 detector=cv2.FaceDetectorYN.create(str(MODELS/'face_detection_yunet_2023mar.onnx'),'',(320,320),.75,.3,5000)
 alignment=AuraFaceRecognizer.__new__(AuraFaceRecognizer);blobs=[]
 for name,video,fps,poses in inputs:
  cap=cv2.VideoCapture(video)
  for pose in poses[::4]:
   cap.set(cv2.CAP_PROP_POS_MSEC,pose['time_seconds']*1000);ok,im=cap.read()
   if not ok:continue
   im=cv2.resize(im,(1280,720));detector.setInputSize((1280,720));_,faces=detector.detect(im)
   for face in [] if faces is None else faces:
    crop=alignment.alignCrop(im,face)
    blobs.append(cv2.dnn.blobFromImage(crop,1/127.5,(112,112),(127.5,)*3,swapRB=True))
  cap.release()
 blobs=blobs[:36];emit({'face_crops':len(blobs)})
 baseline=None
 for label,providers in [('cpu',['CPUExecutionProvider']),('coreml_gpu',[('CoreMLExecutionProvider',{'ModelFormat':'MLProgram','MLComputeUnits':'CPUAndGPU','ModelCacheDirectory':str(OUT/'coreml-cache'),'RequireStaticInputShapes':'0'}),'CPUExecutionProvider'])]:
  item={'requested_providers':providers,'crops':len(blobs)}
  try:
   opts=ort.SessionOptions();opts.enable_profiling=True;opts.profile_file_prefix=str(OUT/label)
   t=time.perf_counter();session=ort.InferenceSession(str(MODELS/'glintr100.onnx'),sess_options=opts,providers=providers);item['setup_sec']=time.perf_counter()-t
   item['actual_providers']=session.get_providers();item['input_shape']=session.get_inputs()[0].shape;key=session.get_inputs()[0].name
   t=time.perf_counter();session.run(None,{key:blobs[0]});item['first_inference_sec']=time.perf_counter()-t
   times=[]
   for repeat in range(3):
    t=time.perf_counter();outputs=[session.run(None,{key:b})[0].reshape(-1) for b in blobs];times.append(time.perf_counter()-t)
   item['runs_sec']=times;outputs=np.stack(outputs);outputs/=np.linalg.norm(outputs,axis=1,keepdims=True)
   if baseline is None:baseline=outputs
   else:item['cpu_cosine_min']=float(np.min(np.sum(baseline*outputs,axis=1)));item['cpu_cosine_mean']=float(np.mean(np.sum(baseline*outputs,axis=1)))
   profile=Path(session.end_profiling());events=json.loads(profile.read_text());counts={}
   for e in events:
    p=e.get('args',{}).get('provider')
    if p:counts[p]=counts.get(p,0)+1
   item['profile_provider_events']=counts
   del session;gc.collect()
  except Exception as e:item['error']=repr(e);traceback.print_exc()
  report['face'][label]=item;save();emit({label:item})
