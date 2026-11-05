"""Original face pixels across a suspected jump, after the body/identity guards.

This is neither face recognition nor a persistent tracker. Each independent
window starts at two original, exclusively owned detections and reads at most
five consecutive source frames. It cannot create names or gallery evidence.
"""
import time

import cv2
import numpy as np

from .face_evidence import select_pose_face


_PIXEL_ERROR = 2.  # Native source pixels, independent of face or video size.
_MIN_POINTS = 6  # Redundant spatial support, beyond a three-point affine fit.
_LK = dict(winSize=(41, 41), maxLevel=3,
           criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, .01))


def _inside(points, box):
    return ((points[:, 0] >= box[0]) & (points[:, 0] <= box[2])
            & (points[:, 1] >= box[1]) & (points[:, 1] <= box[3]))


def _observed_face(row):
    if (row.association != 'confirmed' or row.failure
            or row.detector_score < .8 or row.face_bbox is None):
        return None
    try:
        face = np.asarray(row.face_bbox, dtype=np.float64)
    except (TypeError, ValueError):
        return None
    if (face.shape != (4,) or not np.isfinite(face).all()
            or face[0] >= face[2] or face[1] >= face[3]):
        return None
    return face


def _owned_face(row, record, shape):
    face = _observed_face(row)
    if face is None or record is None:
        return None
    height, width = shape
    if (not 0 <= face[0] < face[2] <= width
            or not 0 <= face[1] < face[3] <= height):
        return None
    owner, failure = select_pose_face([face], np.asarray(row.body_bbox), record)
    return face if owner == 0 and failure is None else None


def _direction(images, first_face, last_face):
    mask = np.zeros(images[0].shape, np.uint8)
    x, y = np.ceil(first_face[:2]).astype(int)
    xx, yy = np.floor(first_face[2:]).astype(int)
    mask[y:yy, x:xx] = 255
    points = cv2.goodFeaturesToTrack(images[0], 300, .01, 4, mask=mask, blockSize=5)
    report = dict(initial_points=0 if points is None else len(points), survived=0)
    if points is None or len(points) < _MIN_POINTS:
        return report, None
    alive = np.ones(len(points), dtype=bool)
    path = [points[:, 0].copy()]
    height, width = images[0].shape
    for before, after in zip(images, images[1:]):
        target, status, _ = cv2.calcOpticalFlowPyrLK(before, after, points, None, **_LK)
        if target is None or status is None:
            return report, None
        returned, reverse_status, _ = cv2.calcOpticalFlowPyrLK(after, before, target, None, **_LK)
        if returned is None or reverse_status is None:
            return report, None
        error = np.linalg.norm(points[:, 0] - returned[:, 0], axis=1)
        alive &= (status[:, 0].astype(bool) & reverse_status[:, 0].astype(bool)
                  & np.isfinite(target[:, 0]).all(axis=1) & (error <= _PIXEL_ERROR)
                  & _inside(target[:, 0], (0, 0, width-1, height-1)))
        path.append(target[:, 0].copy())
        points = target
    alive &= _inside(points[:, 0], last_face)
    if alive.sum() < _MIN_POINTS:
        return report, None
    path = [p[alive] for p in path]
    points = path[-1][:, None].copy()
    alive = np.ones(len(points), dtype=bool)
    for before, after in zip(images[::-1], images[-2::-1]):
        points, status, _ = cv2.calcOpticalFlowPyrLK(before, after, points, None, **_LK)
        if points is None or status is None:
            return report, None
        alive &= status[:, 0].astype(bool)
    error = np.linalg.norm(points[:, 0] - path[0], axis=1)
    alive &= np.isfinite(error) & (error <= _PIXEL_ERROR)
    report['survived'] = int(alive.sum())
    if alive.sum() < _MIN_POINTS:
        return report, None
    path = [p[alive] for p in path]
    # A line, single corner, or support smaller than the measurement error
    # cannot establish a face's spatial correspondence.
    minimum_spread = min(float(np.linalg.eigvalsh(np.cov(p.T))[0]) for p in path)
    report.update(roundtrip_median=float(np.median(error[alive])),
                  roundtrip_max=float(error[alive].max()), minimum_spatial_variance=minimum_spread)
    if minimum_spread <= _PIXEL_ERROR**2:
        return report, None
    return report, path


def _window(images, left, right, records):
    gray = [cv2.cvtColor(im, cv2.COLOR_BGR2GRAY) if im.ndim == 3 else im for im in images]
    report = dict(frames=[left.frame_index, right.frame_index], accepted=False, directions=[])
    if any(im.shape != gray[0].shape for im in gray):
        report['reason'] = 'source_size_changed'
        return report
    first = _owned_face(left, records.get(left.frame_index), gray[0].shape)
    last = _owned_face(right, records.get(right.frame_index), gray[-1].shape)
    if first is None or last is None:
        report['reason'] = 'original_owned_face_missing'
        return report
    forward, a = _direction(gray, first, last)
    reverse, b = _direction(gray[::-1], last, first)
    report['directions'] = [forward, reverse]
    if a is None or b is None:
        report['reason'] = 'unconfirmed_reciprocal_face_pixels'
        return report
    # Independently seeded paths must occupy the same observed face interior
    # throughout the window, not merely return to the right endpoint later.
    intersections = [float(cv2.intersectConvexConvex(cv2.convexHull(x), cv2.convexHull(y))[0])
                     for x, y in zip(a, b[::-1], strict=True)]
    report['minimum_path_intersection_area'] = min(intersections)
    report['accepted'] = min(intersections) > _PIXEL_ERROR**2
    report['reason'] = 'bounded_owned_face_pixels' if report['accepted'] else 'disagreeing_face_paths'
    return report


def prove_source_face_paths(cap, rows, records, jump_frames):
    """Cover every jump edge; a single unproven window preserves the veto."""
    started = time.perf_counter()
    audit = dict(version='bounded_owned_face_pixels_v1', accepted=False, windows=[],
                 decoded_frames=0, seconds=0.)
    jumps = set(jump_frames)
    windows = [(a, b) for a, b in zip(rows, rows[1:])
               if any(a.frame_index < f <= b.frame_index for f in jumps)]
    covered = {f for a, b in windows for f in jumps if a.frame_index < f <= b.frame_index}
    try:
        if not jumps or covered != jumps or any(not 1 <= b.frame_index-a.frame_index <= 4 for a, b in windows):
            audit['reason'] = 'unbounded_original_face_window'
            return audit
        missing = sorted({row.frame_index for window in windows for row in window
                          if _observed_face(row) is None})
        if missing:
            audit.update(reason='original_owned_face_missing', unavailable_face_frames=missing)
            return audit
        for left, right in windows:
            first, last = left.frame_index, right.frame_index
            if (not cap.set(cv2.CAP_PROP_POS_FRAMES, first)
                    or abs(float(cap.get(cv2.CAP_PROP_POS_FRAMES))-first) > .1):
                audit['reason'] = 'source_seek_failed'
                return audit
            images = []
            for frame in range(first, last+1):
                ok, image = cap.read()
                audit['decoded_frames'] += 1
                if (not ok or not isinstance(image, np.ndarray) or image.dtype != np.uint8
                        or image.ndim not in (2, 3)
                        or abs(float(cap.get(cv2.CAP_PROP_POS_FRAMES))-(frame+1)) > .1):
                    audit['reason'] = 'source_frame_unavailable'
                    return audit
                images.append(image)
            result = _window(images, left, right, records)
            result['jump_frames'] = sorted(f for f in jumps if first < f <= last)
            audit['windows'].append(result)
            if not result['accepted']:
                audit['reason'] = result['reason']
                return audit
        audit.update(accepted=True, reason='all_jump_windows_have_owned_face_paths')
        return audit
    except (cv2.error, np.linalg.LinAlgError) as error:
        audit.update(reason='source_pixel_proof_unavailable', error_type=type(error).__name__)
        return audit
    finally:
        audit['seconds'] = float(time.perf_counter()-started)
