"""Throwaway diagnosis of an existing, user-labelled gallery; no product imports."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import resource
import time
import sys

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent
plan = json.loads((ROOT / 'plan.json').read_text())
assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == plan['worker_sha256']
assert len(plan['references']) == 23
started = time.monotonic()
cv2.setNumThreads(1)
model_buffers = []
for entry in plan['models']:
    raw = Path(entry['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == entry['sha256']
    model_buffers.append(np.frombuffer(raw, np.uint8))
empty = np.empty(0, dtype=np.uint8)
detector = cv2.FaceDetectorYN.create('onnx', model_buffers[0], empty, (320, 320), 0.28, 0.30, 5000)
recognizer = cv2.FaceRecognizerSF.create('onnx', model_buffers[1], empty)
rows, vectors = [], {}
for index, entry in enumerate(plan['references']):
    if time.monotonic() - started > 110:
        raise TimeoutError('Reference probe budget reached')
    path = Path(entry['path'])
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == entry['sha256']
    frame = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
    row = {'index': index, 'label': path.parent.name, 'path': str(path), 'sha256': entry['sha256']}
    if frame is None:
        row['status'] = 'decode_failed'
        rows.append(row)
        continue
    height, width = frame.shape[:2]
    assert height * width <= 25_000_000, 'Unexpected reference image size'
    row.update(width=width, height=height)
    (ROOT / 'progress.json').write_text(json.dumps({'reference_index': index, 'stage': 'before_detection'}))
    detector.setInputSize((width, height))
    _, faces = detector.detect(frame)
    faces = sorted(faces if faces is not None else [], key=lambda f: float(f[-1]), reverse=True)
    row['detected_faces'] = [{'xywh': f[:4].astype(float).tolist(), 'score': float(f[-1])} for f in faces]
    row['face_count'] = len(faces)
    if not faces:
        row['status'] = 'no_detection'
    else:
        selected = np.asarray(faces[0], np.float32)
        try:
            aligned = recognizer.alignCrop(frame, selected)
            vector = np.asarray(recognizer.feature(aligned), np.float32).reshape(-1)
            assert vector.shape == (128,) and np.isfinite(vector).all()
            vector = vector / (np.linalg.norm(vector) + 1e-9)
            vectors[index] = vector.astype(np.float32)
            row.update(status='embedded', selected_face_index=0)
        except (cv2.error, AssertionError) as exc:
            row.update(status='embedding_failed', error_type=type(exc).__name__)
    rows.append(row)
    (ROOT / 'progress.json').write_text(json.dumps({'reference_index': index, 'stage': 'reference_completed', 'completed_count': len(rows)}))

members = sorted({r['label'] for r in rows})
centroids = {}
for member in members:
    items = [vectors[r['index']] for r in rows if r['label'] == member and r['index'] in vectors]
    if items:
        mean = np.mean(np.stack(items), axis=0)
        centroids[member] = mean / (np.linalg.norm(mean) + 1e-9)

for row in rows:
    idx = row['index']
    if idx not in vectors:
        continue
    scores = {}
    for member in members:
        items = [vectors[r['index']] for r in rows if r['label'] == member and r['index'] != idx and r['index'] in vectors]
        if not items:
            continue
        mean = np.mean(np.stack(items), axis=0)
        mean /= np.linalg.norm(mean) + 1e-9
        scores[member] = 1.0 - float(np.dot(vectors[idx], mean))
    ranked = sorted(scores.items(), key=lambda item: item[1])
    nearest = ranked[0][0]
    best_other = min(distance for label, distance in ranked if label != row['label'])
    row['leave_one_out'] = {
        'distances': scores, 'nearest': nearest,
        'nearest_correct_to_input_label': nearest == row['label'],
        'with_existing_threshold': nearest if ranked[0][1] <= .60 else 'unknown',
        'own_distance': scores[row['label']], 'best_other_distance': best_other,
        'own_advantage': best_other - scores[row['label']],
    }

cache = json.loads(Path(plan['comparison_cache']['path']).read_text())
assert hashlib.sha256(Path(plan['comparison_cache']['path']).read_bytes()).hexdigest() == plan['comparison_cache']['sha256']
checks = {}
for member, center in centroids.items():
    stored = np.asarray(cache['face_cache']['reference_embeddings'][member], np.float32)
    checks[member] = {'max_abs_diff': float(np.max(np.abs(center - stored))), 'within_1e_5': bool(np.allclose(center, stored, atol=1e-5, rtol=0))}

summary = {
    'reference_count': len(rows), 'embedded': len(vectors),
    'no_detection': sum(r['status'] == 'no_detection' for r in rows),
    'multi_face_images': sum(r.get('face_count', 0) > 1 for r in rows),
    'nearest_correct': sum(r.get('leave_one_out', {}).get('nearest_correct_to_input_label', False) for r in rows),
    'threshold_correct': sum(r.get('leave_one_out', {}).get('with_existing_threshold') == r['label'] for r in rows),
    'threshold_unknown': sum(r.get('leave_one_out', {}).get('with_existing_threshold') == 'unknown' for r in rows),
    'member_counts': dict(Counter(r['label'] for r in rows)),
    'stored_centroid_checks': checks,
    'wall_seconds': time.monotonic() - started,
    'peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    'opencv_version': cv2.__version__, 'numpy_version': np.__version__,
    'python_version': sys.version.split()[0],
}
report = {'schema': 'w14_reference_gallery_diagnostic_result_v1', 'summary': summary, 'rows': rows,
          'limits': 'User-labelled gallery consistency only; no video accuracy, face identity ground truth or model-selection claim.'}
(ROOT / 'reference-result.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
np.savez(ROOT / 'reference-embeddings.local.npz', **{str(k):v for k,v in vectors.items()})
print(json.dumps(summary, ensure_ascii=False))
