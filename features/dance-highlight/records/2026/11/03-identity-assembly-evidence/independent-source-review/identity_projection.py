"""Validate identity-only padding after projecting it onto main output ranges."""
import math

import numpy as np

from .member_timeline import _valid
from .observed_main import strict_pose_corresponding
from .reference_matcher import SegmentReferenceDecision


def _body(record):
    box = record.main_bbox if record.main_bbox is not None else record.candidate_main_bbox
    boxes, poses = record.person_bboxes, record.person_pose_keypoints
    if box is None or len(boxes) != len(poses):
        return None, None
    if any(np.asarray(p).shape != (17, 3) for p in poses):
        return None, None
    features = [dict(index=i, pose_keypoints=np.asarray(p)) for i,p in enumerate(poses)]
    selected = [f for f,b in zip(features, boxes)
                if np.allclose(b, box, atol=1e-3, rtol=0)]
    return dict(features=features), selected[0] if len(selected) == 1 else None


def _path(records, part, support, *, fps, sample_step, cut_frames, handoffs):
    before = [r for r in records if r.t <= part.start]
    if not before or part.start-before[-1].t >= sample_step/fps+1e-6:
        return 'unobserved_output_body', []
    owner = before[-1]
    through_end = [r for r in records if r.t < part.end]
    if not through_end or part.end-through_end[-1].t > sample_step/fps+1e-6:
        return 'unobserved_output_body', []
    lo = min(round(owner.t*fps), support.frame_index)
    hi = max(round(through_end[-1].t*fps), support.frame_index)
    local = [r for r in records if lo <= round(r.t*fps) <= hi]
    frames = [round(r.t*fps) for r in local]
    if (not frames or frames[0] != lo or frames[-1] != hi
            or any(b-a != sample_step for a,b in zip(frames, frames[1:]))):
        return 'missing_original_observation', frames
    if cut_frames is None or any(lo < cut and (cut/fps < part.end or cut <= support.frame_index)
                                for cut in cut_frames):
        return 'source_cut_or_missing_inventory', frames
    if handoffs is None or any(lo/fps < h['time'] and
                              (h['time'] < part.end or h['time'] <= support.time_seconds)
                              for h in handoffs):
        return 'main_handoff_or_missing_inventory', frames
    bodies = [_body(r) for r in local]
    if any(selected is None for _,selected in bodies):
        return 'unobserved_selected_pose', frames
    anchor = next(r for r in local if round(r.t*fps) == support.frame_index)
    anchor_box = anchor.main_bbox if anchor.main_bbox is not None else anchor.candidate_main_bbox
    if not np.allclose(anchor_box, support.body_bbox, atol=1e-3, rtol=0):
        return 'support_not_selected_body', frames
    for (left, a), (right, b) in zip(bodies, bodies[1:]):
        linked = strict_pose_corresponding(left, a, right)
        if linked is None or linked['index'] != b['index']:
            return 'selected_body_discontinuity', frames
    return None, frames


def validate_identity_padding(output, identity, projected, *, frame_records, fps,
                              sample_step, cut_frames, handoffs, matcher, joint_matches,
                              frozen_observations):
    """Do not turn a face outside a part into a name for a different body.

    Timeline-consensus padding needs an original body path. A clipped part
    whose retained owned faces all oppose the parent's name cannot inherit
    that name from discarded observations. Separate recovery proofs retain
    their existing validation contracts.
    """
    audit = dict(version='observed_identity_projection_v2', rejected=[], verified=[])
    if not frame_records or not math.isfinite(fps) or fps <= 0 or sample_step < 1:
        return output, audit
    result = dict(output)
    result['decisions'] = list(output['decisions'])
    result['labels'] = list(output['labels'])
    result['accurate_indices'] = list(output['accurate_indices'])
    records = sorted(frame_records, key=lambda r:r.t)
    records_by_frame = {round(r.t*fps): r for r in records}
    joints = {int(f): match for f,match in joint_matches.items()}
    for index, (parent, part) in enumerate(projected):
        decision = output['decisions'][index]
        if decision.reason != 'member_timeline_consensus' or not decision.reference_id:
            continue
        observed = sorted((r for r,_ in identity['evidence'][parent] if _valid(r)),
                          key=lambda r:r.time_seconds)
        source = identity['segments'][parent]
        local = [r for r in observed if part.start <= r.time_seconds < part.end]
        if ((part.start > source.start or part.end < source.end) and local
                and all(r.frame_index in records_by_frame
                    and records_by_frame[r.frame_index].main_bbox is not None
                    and np.allclose(r.body_bbox, records_by_frame[r.frame_index].main_bbox, atol=1e-3, rtol=0)
                    and joints.get(r.frame_index, {}).get('status') == 'accepted'
                    and joints[r.frame_index].get('name') not in (None, decision.reference_id)
                    for r in local)):
            reason = 'conflicting_projected_identity'
            audit['rejected'].append(dict(parent_span=parent, start=part.start, end=part.end,
                name=decision.reference_id, reason=reason,
                conflicting_faces=[dict(frame=r.frame_index, name=joints[r.frame_index]['name']) for r in local]))
            result['decisions'][index] = SegmentReferenceDecision(None, 'unmatched', reason)
            result['labels'][index] = None
            result['accurate_indices'] = [i for i in result['accurate_indices'] if i != index]
            continue
        if not observed or not (part.end <= observed[0].time_seconds
                                or part.start > observed[-1].time_seconds):
            continue
        # A parent's consensus, window-voted evidence name, or restored label
        # cannot certify its own padding. Use only original face-model results.
        named = []
        for row in observed:
            primary = matcher.match(row, identity['segments'][parent], 'identity-padding').reference_id if matcher else None
            joint = joints.get(row.frame_index, {})
            secondary = joint.get('name') if joint.get('status') == 'accepted' else None
            if joint.get('status') != 'conflict' and decision.reference_id in (primary, secondary) and all(
                    name in (None, decision.reference_id) for name in (primary, secondary)):
                named.append(row)
        support = (named[0] if part.end <= observed[0].time_seconds else named[-1]) if named else None
        failure, frames = ('no_named_source_support', []) if support is None else _path(
            records, part, support, fps=fps, sample_step=sample_step,
            cut_frames=cut_frames, handoffs=handoffs)
        conflicts = []
        if failure is None:
            frame_set = set(frames)
            for row in frozen_observations:
                if row.frame_index not in frame_set or not _valid(row):
                    continue
                record = records_by_frame[row.frame_index]
                selected_box = record.main_bbox if record.main_bbox is not None else record.candidate_main_bbox
                if not np.allclose(row.body_bbox, selected_box, atol=1e-3, rtol=0):
                    continue  # A different person's face is not an identity vote for this path.
                primary = matcher.match(row, identity['segments'][parent], 'identity-padding-conflict').reference_id if matcher else None
                joint = joints.get(row.frame_index, {})
                secondary = joint.get('name') if joint.get('status') == 'accepted' else None
                if joint.get('status') == 'conflict' or any(
                        name is not None and name != decision.reference_id for name in (primary, secondary)):
                    conflicts.append(dict(frame=row.frame_index, primary=primary,
                        secondary=secondary, joint_status=joint.get('status')))
            if conflicts:
                failure = 'conflicting_original_face'
        candidate = dict(parent_span=parent, start=part.start, end=part.end,
            name=decision.reference_id, support_frame=support.frame_index if support else None,
            source_frames=frames)
        if conflicts:
            candidate['conflicting_faces'] = conflicts
        if failure is None:
            audit['verified'].append(dict(candidate, reason='same_observed_selected_body'))
            continue
        audit['rejected'].append(dict(candidate, reason=failure))
        result['decisions'][index] = SegmentReferenceDecision(None, 'unmatched', 'unsupported_identity_padding')
        result['labels'][index] = None
        result['accurate_indices'] = [i for i in result['accurate_indices'] if i != index]
    return result, audit
