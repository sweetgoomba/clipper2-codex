"""Select a stage main from measured composition and continuous body evidence.

Applied before face naming, only to registered Dance analysis. No reference
names, evaluation labels, or clip duration limits enter this stage.
"""

from dataclasses import replace
from math import ceil
import cv2, numpy as np
from .body_continuity import _color_cut
from .face_evidence import select_pose_face
from .segment import FrameRec
from .track import TrackAssigner
from .main_face_link import MainFaceLink, observed_face_target
from .main_role_timeline import choose_roles, extend_near_ties
from .focal_composition import camera_focal_evidence

VERSION = "observed_main_geometry_v3_camera_subject"


def retained_bodies(boxes, points):
    """Suppress a nested partial duplicate only with agreeing observed heads."""
    suppressed = set()
    for i, a in enumerate(boxes):
        for j, b in enumerate(boxes):
            if i == j:
                continue
            area = float(np.prod(a[2:] - a[:2]))
            other_area = float(np.prod(b[2:] - b[:2]))
            intersection = float(
                np.prod(np.maximum(0, np.minimum(a[2:], b[2:]) - np.maximum(a[:2], b[:2])))
            )
            if area <= 0 or other_area <= area or intersection / area < 0.9:
                continue
            ka, kb = points[i], points[j]
            common = (ka[:5, 2] >= 0.5) & (kb[:5, 2] >= 0.5)
            if common.sum() < 3:
                continue
            xy = kb[:5, :2][kb[:5, 2] >= 0.5]
            span = float(np.linalg.norm(xy.max(axis=0) - xy.min(axis=0)))
            if (
                span <= 0
                or np.linalg.norm(ka[:5, :2][common] - kb[:5, :2][common], axis=1).max()
                > 0.3 * span
            ):
                continue
            torso = [5, 6, 11, 12]
            shared_torso = (ka[torso, 2] >= .5) & (kb[torso, 2] >= .5)
            more_torso = (
                (kb[torso, 2] >= .5).sum() >= 3
                and (kb[torso, 2] >= .5).sum() >= (ka[torso, 2] >= .5).sum() + 2
                and shared_torso.any()
                and np.linalg.norm(ka[torso, :2][shared_torso] - kb[torso, :2][shared_torso], axis=1).max() <= .3 * span
            )
            if more_torso or (kb[[13, 14, 15, 16], 2] >= 0.5).sum() >= (ka[[13, 14, 15, 16], 2] >= 0.5).sum() + 2:
                suppressed.add(i)
    return [i for i in range(len(boxes)) if i not in suppressed]


def measured_features(record, detected, width, height):
    boxes = [np.asarray(b) for b in record.person_bboxes]
    points = [np.asarray(p) for p in record.person_pose_keypoints]
    if len(points) != len(boxes) or any(p.shape != (17, 3) for p in points):
        raise ValueError("pose_confidence_unavailable")
    kept = retained_bodies(boxes, points)
    pose = FrameRec(
        record.t,
        None,
        None,
        False,
        person_bboxes=[boxes[i] for i in kept],
        person_head_keypoints=[points[i][:5] for i in kept],
    )
    faces = [
        np.asarray(a) for a in detected if len(a) == 15 and np.isfinite(a).all() and a[-1] >= 0.8
    ]
    face_boxes = [np.r_[a[:2], a[:2] + a[2:4]] for a in faces]
    features = []
    for i in kept:
        k = points[i]
        torso = k[[5, 6, 11, 12]]
        valid = (
            np.isfinite(torso).all(axis=1)
            & (torso[:, 2] >= 0.5)
            & (torso[:, 0] >= 0)
            & (torso[:, 0] < width)
            & (torso[:, 1] >= 0)
            & (torso[:, 1] < height)
        )
        head = k[:5]
        visible = np.isfinite(head).all(axis=1) & (head[:, 2] >= 0.5)
        x = (
            float(torso[:, 0].mean())
            if valid.all()
            else float(head[visible, 0].mean())
            if visible.sum() >= 2
            else None
        )
        index, reason = select_pose_face(face_boxes, boxes[i], pose)
        face = faces[index] if index is not None else None
        cropped = bool(
            boxes[i][3] >= 0.98 * height
            and np.isfinite(k[[15, 16]]).all()
            and (k[[15, 16], 2] < 0.5).all()
        )
        features.append(
            dict(
                index=i,
                box=boxes[i].tolist(),
                pose_keypoints=k,
                head_keypoints=k[:5],
                cropped_foreground=cropped,
                x=x,
                size=float(np.sqrt(face[2] * face[3])) if face is not None else None,
                source="detected" if face is not None else "missing",
                reason=reason,
            )
        )
    return features


def strict_pose_corresponding(row, a, other):
    def cost(a, b):
        left, right = a["pose_keypoints"], b["pose_keypoints"]
        valid = (
            np.isfinite(left).all(axis=1)
            & np.isfinite(right).all(axis=1)
            & (left[:, 2] >= 0.5)
            & (right[:, 2] >= 0.5)
        )
        head = [i for i in range(5) if valid[i]]
        torso = [5, 6, 11, 12]
        if len(head) < 2 or not valid[torso].all():
            return float("inf")
        sizes = [
            np.linalg.norm(p[[5, 6], :2].mean(axis=0) - p[[11, 12], :2].mean(axis=0))
            for p in (left, right)
        ]
        if min(sizes) < 4:
            return float("inf")
        return float(
            np.linalg.norm(left[head + torso, :2] - right[head + torso, :2], axis=1).mean()
            / np.mean(sizes)
        )

    def nearest(a, other):
        values = sorted([(cost(a, b), b) for b in other["features"]], key=lambda q: q[0])
        if (
            not values
            or values[0][0] > 0.3
            or len(values) > 1
            and values[1][0] - values[0][0] < 0.08
        ):
            return None
        return values[0][1]

    b = nearest(a, other)
    if b is None:
        return None
    reverse = nearest(b, row)
    return b if reverse is not None and reverse["index"] == a["index"] else None


def confirmed_main_handoffs(rows, cut_frames, corresponding=None):
    """Record a selected-body change while both bodies remain observable.

    Array indices identify bodies only inside their own source frame. The
    boundary is the first selected-new-body sample, not an exact source cut.
    """
    if cut_frames is None:
        return []
    corresponding = corresponding or strict_pose_corresponding
    result = []
    for previous, current in zip(rows, rows[1:]):
        if (not 0 < current['time']-previous['time'] <= .200001
                or any(previous['frame'] < cut <= current['frame'] for cut in cut_frames)):
            continue
        left = next((f for f in previous['features'] if f['index'] == previous['index']), None)
        right = next((f for f in current['features'] if f['index'] == current['index']), None)
        if left is None or right is None:
            continue
        outgoing = corresponding(previous, left, current)
        incoming = corresponding(current, right, previous)
        if (outgoing is None or incoming is None or outgoing['index'] == right['index']
                or incoming['index'] == left['index']):
            continue
        result.append(dict(frame=current['frame'], time=current['time'],
            previous_frame=previous['frame'], previous_time=previous['time'],
            boundary_policy='first_observed_new_main',
            previous_selected=left['index'], current_selected=right['index'],
            outgoing_current=outgoing['index'], incoming_previous=incoming['index']))
    return result


def collect_geometry(records, video_path, fps, detector, on_progress=None):
    frames = {round(r.t * fps): r for r in records}
    if len(frames) != len(records):
        raise ValueError("duplicate_pose_frame")
    cap = cv2.VideoCapture(str(video_path))
    rows = []
    cuts = []
    try:
        if not cap.isOpened() or abs(float(cap.get(cv2.CAP_PROP_FPS)) - fps) > 0.001:
            raise ValueError("source_fps_mismatch")
        width, height = (
            round(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            round(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        )
        previous = None
        for frame in range(max(frames) + 1):
            ok, image = cap.read()
            if not ok or abs(cap.get(cv2.CAP_PROP_POS_FRAMES) - (frame + 1)) > 0.1:
                raise ValueError("source_frame_unavailable")
            small = cv2.resize(image, (64, 36))
            if previous is not None and _color_cut(previous, small)[0]:
                cuts.append(frame)
            previous = small
            if frame not in frames:
                continue
            record = frames[frame]
            detected = []
            if record.person_bboxes:
                detector.setInputSize((width, height))
                _, found = detector.detect(image)
                detected = [] if found is None else found
            rows.append(
                dict(
                    frame=frame,
                    time=record.t,
                    features=measured_features(record, detected, width, height),
                )
            )
            if on_progress and len(rows) % 150 == 0:
                on_progress(len(rows), len(records))
        if len(rows) != len(records):
            raise ValueError("incomplete_pose_source")
        return rows, cuts, width, height
    finally:
        cap.release()


def refine_main_roles(records, video_path, fps, face_service, config, *, on_progress=None):
    audit = dict(
        version=VERSION, reason="no_main_observations", changes=[], face_correspondences=[]
    )
    if not records or not any(r.main_bbox is not None for r in records):
        return records, audit
    link = None
    try:
        rows, cuts, width, height = collect_geometry(
            records, video_path, fps, face_service._detector, on_progress
        )
        camera_episodes = camera_focal_evidence(rows, width, height, cuts)
        old = {
            round(r.t * fps): dict(
                candidate_main_bbox=None
                if r.main_bbox is None
                else np.asarray(r.main_bbox).tolist()
            )
            for r in records
        }
        face_proofs = {}
        pose_proofs = {}
        def pose_corresponding(row, person, other):
            # Pose arrays remain frozen while role scores/selected indices change.
            key = (row['frame'], person['index'], other['frame'])
            if key not in pose_proofs:
                pose_proofs[key] = strict_pose_corresponding(row, person, other)
            return pose_proofs[key]

        def corresponding(row, a, other):
            nonlocal link
            result = pose_corresponding(row, a, other)
            if result is not None:
                return result
            if a["source"] != "detected" or not (
                a["cropped_foreground"] or any(f["cropped_foreground"] for f in other["features"])
            ):
                return None
            lo, hi = sorted([row["frame"], other["frame"]])
            if not 0 < abs(row["time"] - other["time"]) <= 0.200001 or any(
                lo < c <= hi for c in cuts
            ):
                return None
            key = (row["frame"], a["index"], other["frame"])
            if key not in face_proofs:
                if link is None:
                    link = MainFaceLink(video_path, face_service)
                target, proof = observed_face_target(
                    row,
                    a,
                    other,
                    link.get(row["frame"]),
                    link.get(other["frame"]),
                    cuts,
                    pose_corresponding,
                )
                face_proofs[key] = (None if target is None else target["index"], proof)
            index, _ = face_proofs[key]
            return next((f for f in other["features"] if f["index"] == index), None)

        # Round the existing 0.2 s observation window to source-frame precision.
        # At 59.94 fps, 12 frames take 0.2002 s; a float cutoff otherwise drops
        # the second corroborating face that the same 60 fps sequence retains.
        geometry_window_frames = ceil(.2 * fps - 1e-9)
        for n, row in enumerate(rows):
            for feature in row["features"]:
                if feature["size"] is not None:
                    continue
                matches = []
                for direction in (-1, 1):
                    last = feature
                    previous = row
                    index = n + direction
                    while (
                        0 <= index < len(rows)
                        and abs(rows[index]["frame"] - row["frame"]) <= geometry_window_frames
                    ):
                        nxt = rows[index]
                        lo, hi = sorted([previous["frame"], nxt["frame"]])
                        if any(lo < c <= hi for c in cuts):
                            break
                        q = corresponding(previous, last, nxt)
                        if q is None:
                            break
                        if q["source"] == "detected":
                            matches.append(q["size"])
                        last, previous, index = q, nxt, index + direction
                if len(matches) >= 2 and max(matches) <= 1.4 * min(matches):
                    feature["size"] = sum(matches) / len(matches)
                    feature["source"] = "repeated_same_pose_geometry"
        choose_roles(rows, old, width, height, cuts, corresponding)
        extend_near_ties(rows, cuts, corresponding)
        by_frame = {row['frame']: row for row in rows}
        for episode in camera_episodes:
            for target in episode['visible_targets']:
                row = by_frame[target['frame']]
                person = next(f for f in row['features'] if f['index'] == target['index'])
                row.update(index=person['index'], box=person['box'], reason=episode['reason'])
            for frame in episode['role_only_frames']:
                # A role can continue while its body is hidden. Supplying the
                # passing foreground box here would manufacture its identity.
                by_frame[frame].update(index=None, box=None, reason='occluded_camera_subject')
        tracker = TrackAssigner(config.track_match_iou, config.track_ttl_sec)
        result = []
        for record, row in zip(records, rows, strict=True):
            box = None if row["box"] is None else np.asarray(row["box"], np.float32)
            tid = None if box is None else tracker.assign(record.t, box)
            result.append(replace(record, main_id=tid, main_bbox=box))
            if row["box"] != old[row["frame"]]["candidate_main_bbox"]:
                audit["changes"].append(
                    dict(
                        frame=row["frame"],
                        time=row["time"],
                        before=old[row["frame"]]["candidate_main_bbox"],
                        after=row["box"],
                        reason=row["reason"],
                    )
                )
        audit.update(
            reason="complete",
            observations=len(rows),
            cut_frames=cuts,
            camera_episodes=camera_episodes,
            role_observations=[dict(frame=row['frame'], box=row['box'], reason=row['reason'],
                features=[{k: f[k] for k in ('index', 'box', 'x', 'size', 'source', 'cropped_foreground')}
                          for f in row['features']]) for row in rows],
            handoffs=confirmed_main_handoffs(rows, cuts, pose_corresponding),
            face_correspondences=[
                dict(frames=[a, c], source=b, target=v[0], proof=v[1])
                for (a, b, c), v in face_proofs.items()
            ],
        )
        if link is not None:
            audit["face_models"] = link.link.provenance
        return result, audit
    except (OSError, ValueError, RuntimeError, cv2.error, AttributeError) as error:
        return records, dict(
            audit,
            reason="main_geometry_unavailable",
            error_type=type(error).__name__,
            error=str(error),
        )
    finally:
        if link is not None:
            link.close()
