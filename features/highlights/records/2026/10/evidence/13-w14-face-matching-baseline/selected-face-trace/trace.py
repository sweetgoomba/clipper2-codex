"""Temporary current-model diagnosis; never import or change a product plugin."""
import hashlib
import json
import resource
import sys
import time
from pathlib import Path
from collections import defaultdict

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent
plan = json.loads((ROOT / 'plan.json').read_text())
assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == plan['worker_sha256']
cv2.setNumThreads(1)
started = time.monotonic()
buffers = []
for entry in plan['models']:
    raw = Path(entry['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == entry['sha256']
    buffers.append(np.frombuffer(raw, np.uint8))
empty = np.empty(0, np.uint8)
detector = cv2.FaceDetectorYN.create('onnx', buffers[0], empty, (320, 320), .28, .30, 5000)
recognizer = cv2.FaceRecognizerSF.create('onnx', buffers[1], empty)
reference_file = Path(plan['reference_embeddings']['path'])
assert hashlib.sha256(reference_file.read_bytes()).hexdigest() == plan['reference_embeddings']['sha256']
with np.load(reference_file, allow_pickle=False) as saved:
    by_label = defaultdict(list)
    for index, ref in enumerate(plan['references']):
        by_label[Path(ref['path']).parent.name].append(saved[str(index)])
centroids = {}
for label, items in by_label.items():
    mean = np.mean(np.stack(items), axis=0)
    centroids[label] = mean / (np.linalg.norm(mean) + 1e-9)

def expanded_box(box, width, height):
    x1,y1,x2,y2 = np.asarray(box, np.float32)
    w,h=float(x2-x1),float(y2-y1)
    values=(int(x1-w*.15),int(y1-h*.35),int(x2+w*.15),int(y2+h*.10))
    return (max(0,min(width-1,values[0])),max(0,min(height-1,values[1])),max(0,min(width-1,values[2])),max(0,min(height-1,values[3])))

def iou(a,b):
    w=max(0,min(a[2],b[2])-max(a[0],b[0]));h=max(0,min(a[3],b[3])-max(a[1],b[1]));inter=w*h
    return inter/((a[2]-a[0])*(a[3]-a[1])+(b[2]-b[0])*(b[3]-b[1])-inter)

capture = cv2.VideoCapture(plan['source']['path'])
assert capture.isOpened()
assert abs(capture.get(cv2.CAP_PROP_FPS)-60000/1001)<1e-5
tasks={row['frame_index']:row for row in plan['samples']}
rows=[];vectors={};detector_calls=0;embedding_calls=0;frame_index=0
while frame_index<=max(tasks):
    if time.monotonic()-started>110:
        raise TimeoutError('Trace budget reached')
    if frame_index not in tasks:
        assert capture.grab(), f'Decode skip failed at {frame_index}'
        frame_index+=1
        continue
    ok,frame=capture.read()
    assert ok and frame.shape[:2]==(1012,1920)
    sample=tasks[frame_index]
    for condition,box in sample['body_boxes'].items():
        row={'frame_index':frame_index,'time_sec':sample['time_sec'],'condition':condition,
             'input_reference_label':sample['expected_reference_label_from_user_timeline'],
             'body_bbox':box,'anonymous_source_id':sample['anonymous_source_id']}
        if box is None:
            row['status']='no_selected_body';rows.append(row);continue
        row['body_iou_to_source_label']=iou(box,sample['body_boxes']['annotated_target'])
        x1,y1,x2,y2=expanded_box(box,1920,1012)
        row['roi_xyxy']=[x1,y1,x2,y2]
        roi=frame[y1:y2,x1:x2]
        assert roi.size
        detector.setInputSize((roi.shape[1],roi.shape[0]))
        detector_calls+=1
        assert detector_calls<=plan['limits']['max_detector_calls']
        _,faces=detector.detect(roi)
        faces=sorted(faces if faces is not None else [],key=lambda f:float(f[-1]),reverse=True)
        row['face_candidates']=[{'source_xywh':[float(f[0]+x1),float(f[1]+y1),float(f[2]),float(f[3])],
                                 'score':float(f[-1])} for f in faces]
        if not faces:
            row['status']='no_detection';rows.append(row);continue
        chosen=np.asarray(faces[0],np.float32)
        try:
            aligned=recognizer.alignCrop(roi,chosen)
            embedding_calls+=1
            assert embedding_calls<=plan['limits']['max_embedding_calls']
            vector=np.asarray(recognizer.feature(aligned),np.float32).reshape(-1)
            assert vector.shape==(128,) and np.isfinite(vector).all()
            vector/=np.linalg.norm(vector)+1e-9
            vectors[f'{frame_index}_{condition}']=vector
        except (cv2.error,AssertionError) as exc:
            row.update(status='embedding_failed',error_type=type(exc).__name__);rows.append(row);continue
        distances={label:1-float(np.dot(vector,centroid)) for label,centroid in centroids.items()}
        ranked=sorted(distances.items(),key=lambda item:item[1])
        row.update(status='embedded',distances=distances,nearest=ranked[0][0],nearest_distance=ranked[0][1],
                   nearest_margin=ranked[1][1]-ranked[0][1],assigned=ranked[0][0] if ranked[0][1]<=.60 else 'unknown',
                   selected_candidate=0)
        cropname=f'{frame_index}_{condition}.jpg'
        preview=roi.copy()
        for i,f in enumerate(faces):
            fx,fy,fw,fh=[int(v) for v in f[:4]]
            cv2.rectangle(preview,(fx,fy),(fx+fw,fy+fh),(0,255,0) if i==0 else (0,128,255),2)
        if preview.shape[0]>480:
            preview=cv2.resize(preview,(int(preview.shape[1]*480/preview.shape[0]),480))
        assert cv2.imwrite(str(ROOT/cropname),preview)
        row['roi_preview']=cropname
        rows.append(row)
    (ROOT/'progress.json').write_text(json.dumps({'frame_index':frame_index,'detector_calls':detector_calls,'embedding_calls':embedding_calls}))
    frame_index+=1
capture.release()
summary={}
for condition in plan['samples'][0]['body_boxes']:
    subset=[r for r in rows if r['condition']==condition]
    valid=[r for r in subset if r['status']=='embedded']
    selected_correct=[r for r in subset if r.get('body_iou_to_source_label',0)>=.30]
    summary[condition]={'samples':len(subset),'embedded':len(valid),'no_detection':sum(r['status']=='no_detection' for r in subset),
                        'nearest_agrees_with_input_label':sum(r.get('nearest')==r['input_reference_label'] for r in subset),
                        'threshold_agrees_with_input_label':sum(r.get('assigned')==r['input_reference_label'] for r in subset),
                        'unknown':sum(r.get('assigned')=='unknown' for r in subset),
                        'body_box_matches':len(selected_correct),
                        'direct_name_agrees_within_body_matches':sum(r.get('assigned')==r['input_reference_label'] for r in selected_correct)}
report={'schema':'w14_target_roi_trace_result_v1','summary':summary,'rows':rows,'actual':{'frame_count':len(tasks),'detector_calls':detector_calls,
        'embedding_calls':embedding_calls,'wall_seconds':time.monotonic()-started,'peak_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},
        'interpretation_limit':plan['gt_limit']}
(ROOT/'trace-result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
np.savez(ROOT/'query-embeddings.local.npz',**vectors)
print(json.dumps({'summary':summary,'actual':report['actual']},ensure_ascii=False))
