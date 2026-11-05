"""Canonical views of duplicate full-body observations, isolated to Dance.

Nested detector boxes can predict the same visible head, torso and legs twice.
Those hypotheses are not two independent people. Preserve the raw hypotheses
in the audit and use one original observation consistently in later stages.
"""
from dataclasses import replace

import numpy as np

from .observed_main import strict_pose_corresponding


def _same_full_body(a, pa, b, pb, video_size=None):
    areas = [float(np.prod(box[2:]-box[:2])) for box in (a, b)]
    if min(areas) <= 0:
        return False
    intersection = float(np.prod(np.maximum(0, np.minimum(a[2:], b[2:])-np.maximum(a[:2], b[:2]))))
    if intersection < .9*min(areas):
        return False
    # Both eyes and the nose must be directly well observed in BOTH poses.
    # An uncertain ear cannot veto (or supply) this stronger frontal proof.
    if any((p[:3, 2] < .75).any() or (p[[5,6,11,12], 2] < .75).any()
           or (p[13:17, 2] < .5).any() for p in (pa, pb)):
        return False
    anatomy = [0,1,2,5,6,11,12,13,14,15,16]
    for box, pose in ((a, pa), (b, pb)):
        if not ((pose[anatomy,:2] >= box[:2]) & (pose[anatomy,:2] < box[2:])).all():
            return False
        if video_size is not None and not ((pose[anatomy,:2] >= 0)
                & (pose[anatomy,:2] < video_size)).all():
            return False
        if not (pose[:3,1].max() < pose[[5,6],1].mean() < pose[[11,12],1].mean()
                < pose[[13,14],1].mean() < pose[[15,16],1].mean()):
            return False
    # Bound corresponding frontal-landmark displacement by the smaller
    # directly observed eye separation. Ears do not supply matching tolerance.
    eye_distances = [float(np.linalg.norm(p[1,:2]-p[2,:2])) for p in (pa,pb)]
    if min(eye_distances) < 4:
        return False
    if np.linalg.norm(pa[:3,:2]-pb[:3,:2], axis=1).max() >= min(eye_distances):
        return False
    left = dict(index=0, pose_keypoints=pa)
    right = dict(index=1, pose_keypoints=pb)
    if strict_pose_corresponding(dict(features=[left]), left, dict(features=[right])) is None:
        return False
    lengths = [float(np.linalg.norm(p[[5,6],:2].mean(axis=0)-p[[11,12],:2].mean(axis=0))) for p in (pa,pb)]
    if min(lengths) < 4:
        return False
    if np.linalg.norm(pa[[5,6,11,12],:2]-pb[[5,6,11,12],:2], axis=1).max() > .3*min(lengths):
        return False
    # A shared head cannot erase another person's independently observed legs.
    return bool(np.linalg.norm(pa[13:17,:2]-pb[13:17,:2], axis=1).max() <= .3*np.mean(lengths))


def _foreign_leg_chain(group, boxes, poses, video_size):
    """A shared head cannot authorize borrowing another person's whole leg."""
    if len(group) < 2:
        return None
    for i in group:
        pose = poses[i]
        for other, outside in enumerate(poses):
            if other in group or (outside[:3,2] < .75).any():
                continue
            eye_scale = min(np.linalg.norm(p[1,:2]-p[2,:2]) for p in (pose,outside))
            if eye_scale < 4 or np.linalg.norm(pose[:3,:2]-outside[:3,:2], axis=1).max() < eye_scale:
                continue  # No independently observed different head.
            for member in group:
                if member == i:
                    continue
                for chain in ([13,15], [14,16]):
                    # Only this disputed chain must be visible. Missing joints
                    # on the other side cannot erase positive ownership evidence.
                    points = [0,1,2,*chain]
                    xy = outside[points,:2]
                    box = boxes[other]
                    if ((outside[chain,2] < .5).any()
                            or not ((xy >= box[:2]) & (xy < box[2:])).all()
                            or video_size is not None and not ((xy >= 0) & (xy < video_size)).all()
                            or not outside[:3,1].max() < outside[chain[0],1] < outside[chain[1],1]):
                        continue
                    internal = np.linalg.norm(pose[chain,:2]-poses[member][chain,:2], axis=1)
                    external = np.linalg.norm(pose[chain,:2]-outside[chain,:2], axis=1)
                    if (external < internal).all():
                        return dict(component=group, observation=i, paired_with=member,
                            outside_owner=other, joints=chain,
                            internal_distances=internal.tolist(), external_distances=external.tolist())
    return None


def canonicalize_pose_observations(records, *, fps, video_size=None):
    audit = dict(version='canonical_full_body_observations_v1', changes=[], deferred=[],
                 reason='complete', raw_body_count=0, canonical_body_count=0)
    result = []
    for record in records:
        boxes = [np.asarray(b) for b in record.person_bboxes]
        poses = [np.asarray(p) for p in record.person_pose_keypoints]
        audit['raw_body_count'] += len(boxes)
        valid = (len(poses) == len(boxes) and len(record.person_head_keypoints) == len(boxes)
                 and all(b.shape == (4,) and np.isfinite(b).all() and (b[2:] > b[:2]).all() for b in boxes)
                 and all(p.shape == (17,3) and np.isfinite(p).all() for p in poses))
        if not valid or len(boxes) < 2:
            result.append(record)
            audit['canonical_body_count'] += len(boxes)
            continue
        pairs = {}
        def same(i, j):
            key = tuple(sorted((i,j)))
            if key not in pairs:
                pairs[key] = _same_full_body(boxes[i], poses[i], boxes[j], poses[j], video_size)
            return pairs[key]

        # Prefer a complete enclosing observation, never the current main or
        # its name. Coordinates break ties independently of detector ordering.
        order = sorted(range(len(boxes)), key=lambda i: (
            -float(np.prod(boxes[i][2:]-boxes[i][:2])), tuple(boxes[i]), tuple(poses[i].ravel())))
        # A~B and A~C cannot erase B or C when B and C disagree. Defer the
        # entire ambiguous component, rather than choosing an arbitrary pair.
        groups = []
        deferred = None
        pending = set(order)
        for i in order:
            if i not in pending:
                continue
            component, frontier = {i}, [i]
            pending.remove(i)
            while frontier:
                current = frontier.pop()
                neighbors = {j for j in pending if same(current, j)}
                component.update(neighbors)
                pending.difference_update(neighbors)
                frontier.extend(neighbors)
            group = [j for j in order if j in component]
            if not all(same(a, b) for k,a in enumerate(group) for b in group[k+1:]):
                deferred = dict(reason='non_transitive_body_hypotheses', component=group)
                break
            foreign = _foreign_leg_chain(group, boxes, poses, video_size)
            if foreign is not None:
                deferred = dict(reason='foreign_leg_chain', **foreign)
                break
            groups.append(group)
        if deferred is not None:
            # Preserve witnesses too: replacing an outside witness in another
            # component could otherwise authorize a merge on a second pass.
            audit['deferred'].append(dict(frame=round(record.t*fps), time=record.t, **deferred))
            audit['canonical_body_count'] += len(boxes)
            result.append(record)
            continue
        aliases = {i: g[0] for g in groups for i in g}
        kept = sorted(g[0] for g in groups)
        audit['canonical_body_count'] += len(kept)
        if len(kept) == len(boxes):
            result.append(record)
            continue

        def canonical_box(box):
            if box is None:
                return None
            owners = [i for i,b in enumerate(boxes) if np.array_equal(box, b)]
            return boxes[aliases[owners[0]]] if len(owners) == 1 else box

        group_boxes = []
        for box in record.group_bboxes:
            canonical = canonical_box(box)
            if not any(np.array_equal(canonical, old) for old in group_boxes):
                group_boxes.append(canonical)
        result.append(replace(record,
            person_bboxes=[record.person_bboxes[i] for i in kept],
            person_head_keypoints=[record.person_head_keypoints[i] for i in kept],
            person_pose_keypoints=[record.person_pose_keypoints[i] for i in kept],
            main_bbox=canonical_box(record.main_bbox),
            candidate_main_bbox=canonical_box(record.candidate_main_bbox), group_bboxes=group_boxes))
        audit['changes'].append(dict(frame=round(record.t*fps), time=record.t,
            canonical_to_raw=kept,
            equivalence_groups=[dict(representative=g[0], raw_members=g) for g in groups if len(g)>1],
            raw_observations=[dict(index=i, box=boxes[i].tolist(),
                head_keypoints=np.asarray(record.person_head_keypoints[i]).tolist(),
                pose_keypoints=poses[i].tolist()) for i in range(len(boxes))]))
    return result, audit
