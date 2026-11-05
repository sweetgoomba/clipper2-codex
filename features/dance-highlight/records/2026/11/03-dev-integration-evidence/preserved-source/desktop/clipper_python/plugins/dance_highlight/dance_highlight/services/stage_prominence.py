"""Corroborate a front performer with two independent perspective measurements.

Face scale alone favors people crossing the camera. Torso length alone favors
an extended pose. Agreement can preserve an isolated front performer when a
supporting row happens to straddle the exact image center. Temporal confirmation
and camera-subject evidence remain the responsibility of the role timeline.
"""
import numpy as np


def foreground_subject(features, width, height):
    measured = []
    torso_peers = []
    for feature in features:
        size, x = feature.get('size'), feature.get('x')
        pose = np.asarray(feature.get('pose_keypoints', []))
        if pose.shape != (17, 3):
            if size is not None and x is not None:
                return None
            continue
        torso = pose[[5, 6, 11, 12]]
        if (not np.isfinite(torso).all() or (torso[:, 2] < .75).any()
                or (torso[:, 0] < 0).any() or (torso[:, 0] >= width).any()
                or (torso[:, 1] < 0).any() or (torso[:, 1] >= height).any()):
            if size is not None and x is not None:
                return None
            continue
        length = float(np.linalg.norm(torso[:2, :2].mean(axis=0) - torso[2:, :2].mean(axis=0)))
        if length < .08 * height:
            if size is not None and x is not None:
                return None
            continue
        torso_peers.append((feature, length))
        if size is not None and x is not None:
            measured.append((feature, length))
    if len(measured) < 3:
        return None
    selected, length = max(measured, key=lambda pair: pair[0]['size'])
    if not .2 * width <= selected['x'] <= .8 * width or selected['size'] < .04 * height:
        return None
    others = [(f, scale) for f, scale in measured if f is not selected]
    # A faceless peer still competes via its measured torso.
    # Both measurements must be uniquely larger; two people in the front row
    # supply no single-subject evidence. The role timeline still requires a
    # sustained observation before this can replace an incumbent.
    if (selected['size'] < 1.08 * max(f['size'] for f, _ in others)
            or any(length < 1.08 * scale for peer, scale in torso_peers if peer is not selected)):
        return None
    return selected


def selected_foreground_torso(record, selected_box, video_size):
    """Corroborate the selected front performer, including faceless rivals."""
    from .observed_main import retained_bodies
    width, height = video_size
    boxes, poses = record.person_bboxes, record.person_pose_keypoints
    if len(boxes) != len(poses) or any(np.asarray(p).shape != (17, 3) for p in poses):
        return False
    measured = []
    selected = None
    for i in retained_bodies(boxes, poses):
        box, pose = np.asarray(boxes[i]), np.asarray(poses[i])
        # A clipped body at the outer edge cannot compete for this central
        # role. Any unobserved body reaching the central half remains a veto.
        if box[2] < .25*width or box[0] > .75*width:
            continue
        torso = pose[[5, 6, 11, 12]]
        if (not np.isfinite(torso).all() or (torso[:, 2] < .75).any()
                or (torso[:, 0] < max(0., box[0])).any()
                or (torso[:, 0] >= min(width, box[2])).any()
                or (torso[:, 1] < max(0., box[1])).any()
                or (torso[:, 1] >= min(height, box[3])).any()):
            return False
        length = float(np.linalg.norm(torso[:2, :2].mean(axis=0)-torso[2:, :2].mean(axis=0)))
        if length < 4. or np.ptp(torso[:, 0]) <= 0:
            return False
        measured.append((i, length))
        if np.allclose(box, selected_box, atol=1e-3, rtol=0):
            selected = (i, length)
    return bool(selected and selected[1] >= .08*height
        and all(selected[1] >= 1.08*length for i, length in measured if i != selected[0]))
