"""Separate source observations for very distant Dance ensembles.

Detailed poses never replace the selected main or its identity geometry.
Missing heads are not synthesized, and no name enters scene classification.
"""
from dataclasses import replace
from pathlib import Path
import cv2
import numpy as np

VERSION = 'native_distant_scene_v3_upper_unobserved'
IMAGE_SIZE = 1920


def _large_observed_head(record, video_size, *, min_height=None):
    width,height = video_size
    min_height = height/3 if min_height is None else min_height
    for box,head in zip(record.person_bboxes,record.person_head_keypoints):
        box,head = np.asarray(box),np.asarray(head)
        if box.shape != (4,) or head.ndim != 2 or head.shape[1] != 3:
            continue
        head = head[:5]
        visible = (np.isfinite(head).all(axis=1) & (head[:,2] >= .5)
                   & (head[:,0] >= max(0,box[0])) & (head[:,0] <= min(width,box[2]))
                   & (head[:,1] >= max(0,box[1])) & (head[:,1] <= min(height,box[3])))
        if visible.sum() >= 2 and box[3]-box[1] > min_height:
            return True
    return False


def _large_observed_foreground(record, video_size, *, min_height=None):
    if _large_observed_head(record, video_size, min_height=min_height):
        return True
    width,height = video_size
    min_height = height/3 if min_height is None else min_height
    for box,pose in zip(record.person_bboxes,record.person_pose_keypoints):
        box,pose = np.asarray(box),np.asarray(pose)
        if (box.shape != (4,) or pose.shape != (17,3) or not np.isfinite(box).all()
                or (box[2:] <= box[:2]).any() or box[3]-box[1] <= min_height):
            continue
        torso = pose[[5,6,11,12]]
        if (np.isfinite(torso).all() and (torso[:,2] >= .75).all()
                and (torso[:,0] >= max(0,box[0])).all() and (torso[:,0] < min(width,box[2])).all()
                and (torso[:,1] >= max(0,box[1])).all() and (torso[:,1] < min(height,box[3])).all()
                and np.ptp(torso[:,0]) > 0 and torso[:2,1].mean() < torso[2:,1].mean()):
            return True
    return False


def _geometry(person, video_size):
    width,height = video_size
    box,points = np.asarray(person['bbox']),np.asarray(person['pose_keypoints'])
    if (box.shape != (4,) or points.shape != (17,3) or not np.isfinite(box).all()
            or (box[2:] <= box[:2]).any()):
        return None
    visible = (np.isfinite(points).all(axis=1) & (points[:,2] >= .5)
               & (points[:,0] >= max(0,box[0])) & (points[:,0] < min(width,box[2]))
               & (points[:,1] >= max(0,box[1])) & (points[:,1] < min(height,box[3])))
    head = np.flatnonzero(visible[:5])
    torso = [5,6,11,12]
    full = (len(head) >= 2 and visible[torso].all() and (points[torso,2] >= .75).all()
            and visible[[13,14,15,16]].all()
            and points[head,1].max() < points[[5,6],1].mean()
            < points[[11,12],1].mean() < points[[15,16],1].mean())
    chains = []
    if len(head) >= 2:
        top = points[head[np.argmin(points[head,1])],:2]
        for side in ([5,11,13,15],[6,12,14,16]):
            if visible[side].all():
                chains.append(float(np.linalg.norm(np.diff(np.vstack([top,points[side,:2]]),axis=0),axis=1).sum()))
    extent = float(points[[15,16],1].max()-points[head,1].min()) if full else float(box[3]-box[1])
    extent = max(extent,*chains) if chains else extent
    # An incomplete body cut by the image boundary has no measured size bound.
    if not full and (box[0] <= 0 or box[1] <= 0 or box[2] >= width or box[3] >= height):
        extent = float('inf')
    rect = np.r_[points[torso,:2].min(axis=0),points[torso,:2].max(axis=0)]
    return dict(box=box,full=bool(full),extent=extent,rect=rect)


def _distinct_complete_count(people):
    rects = [p['rect'] for p in people if p['full'] and np.prod(p['rect'][2:]-p['rect'][:2]) > 0]
    remaining,count = set(range(len(rects))),0
    while remaining:
        pending = [remaining.pop()]
        count += 1
        while pending:
            rect = rects[pending.pop()]
            for j in sorted(remaining):
                other = rects[j]
                overlap = np.prod(np.maximum(0,np.minimum(rect[2:],other[2:])-np.maximum(rect[:2],other[:2])))
                if overlap >= .5*min(np.prod(rect[2:]-rect[:2]),np.prod(other[2:]-other[:2])):
                    remaining.remove(j)
                    pending.append(j)
    return count


def _separate_lower_partial_people(observations, people, video_size):
    """Separate small bottom foreground from a fully observed distant ensemble.

    Audience heads below the performers' feet do not bound performer scale.
    They still need measured small boxes and real head/shoulder observations;
    a large, side-clipped, or unobserved foreground body remains a veto.
    Original detector observations stay available in the audit.
    """
    if not people or any(p is None for p in people):
        return people, []
    width, height = video_size
    complete = [p for p in people if p['full']]
    if (_distinct_complete_count(complete) < 3
            or any(p['extent'] > height/6 for p in complete)):
        return people, []
    floor = max(np.asarray(o['pose_keypoints'])[[15,16],1].max()
                for o,p in zip(observations,people) if p['full'])
    excluded = []
    for index,(observation,person) in enumerate(zip(observations,people)):
        points,box = np.asarray(observation['pose_keypoints']),person['box']
        reliable = np.isfinite(points).all(axis=1) & (points[:,2] >= .5)
        visible = (reliable & (points[:,0] >= max(0,box[0]))
                   & (points[:,0] < min(width,box[2]))
                   & (points[:,1] >= max(0,box[1]))
                   & (points[:,1] < min(height,box[3])))
        if (not person['full'] and box[1] > floor
                and box[0] > 0 and box[2] < width
                # Normalize the one-pixel edge tolerance at 1080p. Half
                # precision may round a near-bottom box onto the image edge.
                and box[3] >= height-height/1080
                and max(box[2]-box[0],box[3]-box[1]) <= height/6
                and visible[:5].any() and visible[5:7].any()
                and not reliable[11:].any()):
            excluded.append(index)
    return [p for i,p in enumerate(people) if i not in excluded],excluded


def _separate_upper_unobserved_people(observations, people, video_size, record):
    """An unobserved box above measured performers cannot supply foreground.

    Stage decorations can produce a box without any confident joint. Keep
    every observed or clipped body, and any box overlapping performer height.
    This only removes a size veto: the original three-person, source-cut and
    temporal checks still have to prove the ensemble independently.
    """
    if not people or any(p is None for p in people):
        return people, []
    width, height = video_size
    complete = [p for p in people if p['full']]
    if (_distinct_complete_count(complete) < 2
            or any(p['extent'] > height/6 for p in complete)):
        return people, []
    top = min(p['box'][1] for p in complete)
    excluded = []
    for index, (observation, person) in enumerate(zip(observations, people)):
        points, box = np.asarray(observation['pose_keypoints']), person['box']
        if (not person['full'] and np.isfinite(points).all()
                and not (points[:, 2] >= .5).any()
                and 0 < box[0] < box[2] < width and 0 < box[1] < box[3] < top):
            # A native pose failure cannot erase a person observed by the
            # original detector, even below the ordinary foreground size.
            overlap = [i for i, body in enumerate(record.person_bboxes)
                       if (np.minimum(box[2:], body[2:]) > np.maximum(box[:2], body[:2])).all()]
            original = replace(record, person_bboxes=[record.person_bboxes[i] for i in overlap],
                person_head_keypoints=[record.person_head_keypoints[i]
                    if i < len(record.person_head_keypoints) else np.empty((0, 3)) for i in overlap],
                person_pose_keypoints=[record.person_pose_keypoints[i]
                    if i < len(record.person_pose_keypoints) else np.empty((0, 3)) for i in overlap])
            if _large_observed_foreground(original, video_size, min_height=0.):
                continue
            excluded.append(index)
    return [p for i, p in enumerate(people) if i not in excluded], excluded


def refine_with_scene_observations(records, observations, *, video_size, fps, cut_frames):
    audit = dict(version=VERSION,reason='complete',changes=[],runs=[],lower_partial_exclusions=[],
                 upper_unobserved_exclusions=[])
    if cut_frames is None:
        return records,dict(audit,reason='missing_cut_inventory')
    cuts = sorted(set(cut_frames))
    frames = [round(r.t*fps) for r in records]
    measured,small,candidates = [],[],[]
    for record,frame in zip(records,frames):
        observed = observations.get(frame,[])
        people = [_geometry(p,video_size) for p in observed]
        people,upper = _separate_upper_unobserved_people(observed,people,video_size,record)
        if upper:
            audit['upper_unobserved_exclusions'].append(dict(frame=frame,indices=upper))
        retained = [i for i in range(len(observed)) if i not in upper]
        people,excluded = _separate_lower_partial_people(
            [observed[i] for i in retained],people,video_size)
        if excluded:
            audit['lower_partial_exclusions'].append(dict(frame=frame,indices=[retained[i] for i in excluded]))
        complete_input = bool(people) and all(p is not None for p in people)
        bounded = (complete_input and not _large_observed_foreground(record,video_size)
                   and max(p['extent'] for p in people) <= video_size[1]/6)
        measured.append(people if complete_input else [])
        small.append(bool(bounded))
        candidates.append(bool(bounded and _distinct_complete_count(people) >= 3))

    def connected(first,last):
        return (all(0 < records[j].t-records[j-1].t <= .200001 for j in range(first+1,last+1))
                and not any(frames[first] < cut <= frames[last] for cut in cuts))

    def seen(box,boundaries):
        area = float(np.prod(box[2:]-box[:2]))
        for other in boundaries:
            overlap = float(np.prod(np.maximum(0,np.minimum(box[2:],other[2:])-np.maximum(box[:2],other[:2]))))
            if overlap/area >= .8 or overlap/max(1.,area+np.prod(other[2:]-other[:2])-overlap) >= .3:
                return True
        return False

    bounded = candidates.copy()
    i = 0
    while i < len(records):
        if candidates[i]:
            i += 1
            continue
        start = i
        while i < len(records) and not candidates[i]:
            i += 1
        if (start > 0 and i < len(records) and records[i].t-records[start].t <= .600001
                and all(small[start:i]) and connected(start-1,i)):
            boundaries = [p['box'] for j in (start-1,i) for p in measured[j]]
            if all(seen(p['box'],boundaries) for people in measured[start:i] for p in people):
                bounded[start:i] = [True]*(i-start)
    accepted = set()
    i = 0
    while i < len(records):
        if not bounded[i]:
            i += 1
            continue
        start = i
        i += 1
        while i < len(records) and bounded[i] and connected(i-1,i):
            i += 1
        if records[i-1].t-records[start].t >= .15-1e-6:
            accepted.update(range(start,i))
            audit['runs'].append(dict(first_frame=frames[start],last_frame=frames[i-1]))
    result = []
    for i,record in enumerate(records):
        if i in accepted and record.scene_kind != 'group':
            audit['changes'].append(dict(frame=frames[i],time=record.t,before=record.scene_kind))
            record = replace(record,main_id=None,main_bbox=None,is_group=True,
                group_bboxes=[p['box'].copy() for p in measured[i]],scene_kind='group',scene_reason='native_distant_ensemble')
        result.append(record)
    return (result if audit['changes'] else records),audit


def refine_native_scenes(records, video_path, fps, pose_analyzer, *, video_size, cut_frames, on_progress=None):
    audit = dict(version=VERSION,reason='complete',image_size=IMAGE_SIZE,requested_frames=[],changes=[])
    if cut_frames is None:
        return records,dict(audit,reason='missing_cut_inventory')
    requested = [round(r.t*fps) for r in records if not _large_observed_head(r,video_size)]
    audit['requested_frames'] = requested
    if not requested:
        return records,audit
    cap = cv2.VideoCapture(str(video_path))
    observations = {}
    try:
        if not cap.isOpened() or abs(cap.get(cv2.CAP_PROP_FPS)-fps) > .001:
            return records,dict(audit,reason='source_fps_unavailable')
        actual = (round(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),round(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        if actual != tuple(video_size):
            return records,dict(audit,reason='source_size_mismatch')
        for frame in requested:
            position = cap.get(cv2.CAP_PROP_POS_FRAMES)
            if 0 <= frame-position <= 60:
                for _ in range(round(frame-position)):
                    if not cap.grab():
                        return records,dict(audit,reason='source_frame_unavailable')
            elif not cap.set(cv2.CAP_PROP_POS_FRAMES,frame):
                return records,dict(audit,reason='source_seek_failed')
            if abs(cap.get(cv2.CAP_PROP_POS_FRAMES)-frame) > .1:
                return records,dict(audit,reason='source_position_mismatch')
            ok,image = cap.read()
            if not ok:
                return records,dict(audit,reason='source_frame_unavailable')
            observations[frame] = pose_analyzer.run_pose_on_frame(image,image_size=IMAGE_SIZE)
            if on_progress and len(observations)%25 == 0:
                on_progress(len(observations),len(requested))
        result,refinement = refine_with_scene_observations(records,observations,video_size=video_size,fps=fps,cut_frames=cut_frames)
        audit.update(refinement)
        audit['observations'] = [dict(frame=f,persons=people) for f,people in observations.items()]
        config = getattr(pose_analyzer,'config',None)
        model = Path(getattr(config,'yolo_model_path',''))
        if model.is_file():
            from .face_models import sha256_file
            audit['model_sha256'] = sha256_file(model)
        if config is not None:
            audit.update(conf=config.yolo_conf,iou=config.yolo_iou,device=config.yolo_device)
        return result,audit
    except Exception as error:
        return records,dict(audit,reason='native_scene_unavailable',changes=[],runs=[],
                            lower_partial_exclusions=[],upper_unobserved_exclusions=[],
                            error_type=type(error).__name__)
    finally:
        cap.release()
