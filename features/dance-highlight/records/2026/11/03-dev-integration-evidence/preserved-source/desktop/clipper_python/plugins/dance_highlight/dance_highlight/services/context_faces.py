"""Retain directly recognized non-main faces as local tracking evidence.

These observations never enter a recognition gallery and never create clips.
Only the mask verifier may connect them to an existing unknown main interval.
"""
from bisect import bisect_right
from collections import Counter
import cv2
import numpy as np


def select_context_anchors(candidates, cut_frames, fps):
    from .member_timeline import _valid
    counts = Counter((c['observation'].frame_index,c['name']) for c in candidates if c['name'])
    eligible = [(c['name'],c['observation']) for c in candidates
                if not c.get('is_main') and c['name'] and c['secondary_name'] == c['name'] and c['distance'] <= .55
                and _valid(c['observation']) and c['observation'].detector_score >= .9
                and counts[(c['observation'].frame_index,c['name'])] == 1]
    return [(name,row) for name,row in eligible if any(
        other_name == name and .15-1e-6 <= abs(other.time_seconds-row.time_seconds) <= .6+1e-6
        and bisect_right(cut_frames,other.frame_index) == bisect_right(cut_frames,row.frame_index)
        for other_name,other in eligible)]


def collect_source_context(video_path, records, fps, *, source_inventory=None):
    """Keep source cuts/camera evidence without extracting unused SAM anchors."""
    from pathlib import Path
    from .camera_transitions import classify_transition
    audit = dict(version='same_shot_source_context_v1', anchors=[], identity_extraction=False)
    verified = (source_inventory is not None and source_inventory.get('reason') == 'complete'
                and source_inventory.get('source_path') == str(Path(video_path).resolve())
                and abs(source_inventory.get('fps',0.)-fps) <= .001
                and source_inventory.get('through_frame',-1) >= max((round(r.t*fps) for r in records),default=0))
    if verified:
        cuts = list(source_inventory['cut_frames'])
        transitions = list(source_inventory['camera_transitions'])
    else:
        cap = cv2.VideoCapture(str(video_path))
        cuts,transitions = [],[]
        try:
            if not cap.isOpened() or abs(float(cap.get(cv2.CAP_PROP_FPS))-fps) > .001:
                return [],dict(audit,reason='context_source_unavailable')
            previous,index = None,0
            while True:
                ok,image = cap.read()
                if not ok:
                    break
                if previous is not None:
                    transition = classify_transition(previous,image)
                    if transition['cut']:
                        cuts.append(index)
                    if transition['color_candidate']:
                        transitions.append(dict(frame=index,**transition))
                previous = image
                index += 1
            if records and index <= round(records[-1].t*fps):
                return [],dict(audit,reason='incomplete_source_decode')
        except (OSError,RuntimeError,ValueError,cv2.error) as error:
            return [],dict(audit,reason='context_source_failed',error_type=type(error).__name__)
        finally:
            cap.release()
    audit.update(reason='complete',cut_frames=cuts,camera_transitions=transitions)
    return cuts,audit


def collect_context_anchors(video_path, records, fps, output, face_service, matcher,
                            reference_paths, *, on_progress=None, source_inventory=None):
    from pathlib import Path
    import hashlib
    from .face_evidence import FaceObservation
    from .face_models import SECONDARY_FACE_MODEL_SPEC, ensure_face_models
    from .opencv_acceleration import secondary_recognizer
    from .secondary_faces import build_secondary_gallery, match_secondary_vector
    from .track import bbox_iou
    from .segment import Segment

    audit = dict(version='same_shot_context_faces_v1',anchors=[],sample_interval_seconds=.4)
    unknown = [(s.start,s.end) for s,d in zip(output['segments'],output['decisions'],strict=True)
               if not d.reference_id]
    if not unknown:
        return [],[],dict(audit,reason='no_unknown_main')
    if not reference_paths:
        return [],[],dict(audit,reason='no_reference_paths')
    try:
        spec = SECONDARY_FACE_MODEL_SPEC
        paths = ensure_face_models(specs=(spec,))
        recognizer = secondary_recognizer(face_service, paths[spec.name])
        def feature(image,box,landmarks,score):
            face = np.array([box[0],box[1],box[2]-box[0],box[3]-box[1],
                             *np.asarray(landmarks).reshape(-1),score],np.float32)
            vector = recognizer.feature(recognizer.alignCrop(image,face)).reshape(-1)
            norm = float(np.linalg.norm(vector))
            return vector/norm if norm > 1e-9 and np.isfinite(vector).all() else None
        samples = []
        for name,photos in reference_paths.items():
            for path in photos:
                data = Path(path).read_bytes()
                image = cv2.imdecode(np.frombuffer(data,np.uint8),cv2.IMREAD_COLOR)
                if image is None:
                    continue
                candidate = face_service.get_face_embedding_candidate(image)
                if candidate is None:
                    continue
                vector = feature(image,candidate.face_bbox,candidate.landmarks,candidate.detector_score)
                if vector is not None:
                    samples.append((name,hashlib.sha256(data).hexdigest(),vector))
        gallery = build_secondary_gallery(samples,set(reference_paths))
        if gallery is None:
            return [],[],dict(audit,reason='incomplete_secondary_gallery')
    except (OSError,RuntimeError,ValueError,cv2.error) as error:
        return [],[],dict(audit,reason='context_model_unavailable',error_type=type(error).__name__)

    cuts, source_audit = collect_source_context(video_path, records, fps, source_inventory=source_inventory)
    if source_audit['reason'] != 'complete':
        return [], [], dict(audit, reason=source_audit['reason'],
                           **({'error_type': source_audit['error_type']} if 'error_type' in source_audit else {}))
    transitions = source_audit['camera_transitions']
    shot = lambda frame:bisect_right(cuts,frame)
    target_shots = {shot(round(r.t*fps)) for r in records if any(a <= r.t < b for a,b in unknown)}
    selected,buckets = {},set()
    for record in records:
        frame = round(record.t*fps)
        bucket = int(record.t/.4)
        if shot(frame) in target_shots and bucket not in buckets:
            selected[frame] = record
            buckets.add(bucket)
    cap = cv2.VideoCapture(str(video_path))
    candidates,index,done = [],0,0
    try:
        if not cap.isOpened():
            return [],cuts,dict(audit,reason='context_source_unavailable')
        while cap.grab():
            record = selected.get(index)
            if record is not None:
                ok,image = cap.retrieve()
                if not ok:
                    return [],cuts,dict(audit,reason='incomplete_source_decode')
                height,width = image.shape[:2]
                for owner,body in enumerate(record.person_bboxes):
                    is_main = (record.scene_kind != 'group' and record.main_bbox is not None
                               and bbox_iou(body,record.main_bbox) >= .7)
                    x,y,xx,yy = face_service.expand_face_roi(body,width,height)
                    candidate,_ = face_service._inspect_face(image[y:yy,x:xx],pose_record=record,
                        source_body=body,offset=(x,y),require_pose=True)
                    if candidate is None:
                        continue
                    box = candidate.face_bbox
                    row = FaceObservation(index,index/fps,-owner-1,tuple(body),(x,y,xx,yy),
                        face_bbox=(box[0]+x,box[1]+y,box[2]+x,box[3]+y),
                        landmarks=tuple((a+x,b+y) for a,b in candidate.landmarks),
                        embedding=candidate.embedding,quality=candidate.quality,
                        detector_score=candidate.detector_score,association='confirmed',
                        detection_rotation_degrees=getattr(candidate,'detection_rotation_degrees',0.))
                    match = matcher.match(row,Segment('main',0,0.,index/fps+1,[]),'context-face')
                    if not match.reference_id:
                        continue
                    distance = next(c.distance for c in match.candidates if c.reference_id == match.reference_id)
                    secondary = None
                    if distance <= .55 and row.detector_score >= .9:
                        vector = feature(image,row.face_bbox,row.landmarks,row.detector_score)
                        if vector is not None:
                            secondary = match_secondary_vector(vector,gallery)['name']
                    candidates.append(dict(name=match.reference_id,secondary_name=secondary,
                                           distance=distance,observation=row,is_main=is_main))
                done += 1
                if on_progress:
                    on_progress(done,len(selected))
            index += 1
        if done != len(selected):
            return [],cuts,dict(audit,reason='incomplete_source_decode')
    except (OSError,RuntimeError,ValueError,cv2.error) as error:
        return [],cuts,dict(audit,reason='context_extraction_failed',error_type=type(error).__name__)
    finally:
        cap.release()
    anchors = select_context_anchors(candidates,cuts,fps)
    audit.update(reason='complete',sampled_frames=done,direct_candidates=len(candidates),cut_frames=cuts,
                 camera_transitions=transitions,
                 anchors=[dict(name=name,frame_index=row.frame_index,time_seconds=row.time_seconds,
                               body_bbox=list(map(float,row.body_bbox)),face_bbox=list(map(float,row.face_bbox)),
                               landmarks=[list(map(float,point)) for point in row.landmarks],
                               detector_score=float(row.detector_score),
                               detection_rotation_degrees=float(row.detection_rotation_degrees))
                          for name,row in anchors])
    return anchors,cuts,audit
