"""Resolve duplicate output edges for one recorded observation transition.

Identity midpoints are provisional between observations. Scene exits and main
handoffs already use the first observation of the new state. Do not export the
empty interval between those two representations as another unknown person.
Original identity evidence and the main time mask remain immutable.
"""
from collections import ChainMap
from dataclasses import replace
import math

from .identity_projection import _path
from .member_timeline import _valid


def _covered(start, end, eligibility):
    cursor = start
    for part in sorted(eligibility, key=lambda s: s.start):
        if part.end <= cursor:
            continue
        if part.start > cursor + 1e-6:
            return False
        cursor = max(cursor, part.end)
        if cursor >= end - 1e-6:
            return True
    return False


def coalesce_boundary_events(output, identity, *, frame_records, frozen_observations,
                             joint_matches, eligibility, fps, sample_step, cut_frames,
                             handoffs, matcher=None):
    """Join only an observation-free unknown tail of the outgoing state.

No duration floor, new face match, source read, or new role eligibility. A
named outgoing state needs independent accepted faces through its last sample;
an unknown state stays unknown. A source-refined edge always takes precedence.
"""
    audit = dict(version='single_observation_boundary_v1', joins=[], rejected=[])
    if (handoffs is None or cut_frames is None or not math.isfinite(fps) or fps <= 0
            or sample_step < 1 or not frame_records):
        return output, audit
    records = {round(r.t*fps): r for r in frame_records}
    original = {r.frame_index: r for r in frozen_observations}
    joints = {int(f): value for f, value in joint_matches.items()}
    boundaries = [b for parent in identity.get('audit', ()) for b in parent.get('boundaries', ())]
    groups = []
    for index, part in enumerate(output['segments']):
        decision = output['decisions'][index]
        if not groups or decision.reference_id or decision.status != 'unmatched':
            groups.append([index])
            continue
        left_index = groups[-1][-1]
        left = output['segments'][left_index]
        edges = [b for b in boundaries if abs(b['time']-part.start) <= 1e-6]
        if (abs(left.end-part.start) > 1e-6 or not edges
                or any(b.get('boundary_frame_index') is not None for b in edges)):
            groups.append([index])
            continue
        edges = [b for b in edges if b['reason'] == 'repeated_face_change'
            and all(math.isfinite(b[k]) for k in ('time', 'left_time', 'right_time'))
            and abs(b['right_time']-part.end) <= 1e-6
            and abs(b['time']-(b['left_time']+b['right_time'])/2) <= 1e-6]
        if len(edges) != 1:
            groups.append([index])
            continue
        edge = edges[0]
        lo, hi = round(edge['left_time']*fps), round(edge['right_time']*fps)
        before, after = records.get(lo), records.get(hi)
        same_handoff = any(h.get('boundary_policy') == 'first_observed_new_main'
            and abs(h['previous_time']-edge['left_time']) <= 1e-6
            and abs(h['time']-edge['right_time']) <= 1e-6 for h in handoffs)
        scene_exit = (after is not None and after.scene_kind != 'main'
            and not any(s.start <= after.t < s.end for s in eligibility))
        if (hi-lo != sample_step or before is None or after is None
                or before.scene_kind != 'main' or before.main_bbox is None
                or not (same_handoff or scene_exit)
                or not _covered(edge['left_time'], part.end, eligibility)):
            groups.append([index])
            continue
        candidate = dict(source_indices=[left_index, index], boundary=part.start,
            canonical_time=part.end, observation_frames=[lo, hi],
            event_uncertainty=[edge['left_time'], edge['right_time']],
            event='main_handoff' if same_handoff else 'scene_exit')
        failure = None
        support = original.get(lo)
        if (any(part.start <= r.time_seconds < part.end for r in frozen_observations)
                or output['evidence'][index] or part.bboxes):
            failure = 'observed_interval'
        elif any(lo < cut <= hi for cut in cut_frames):
            failure = 'source_cut'
        elif support is None:
            failure = 'missing_outgoing_observation'
        name = output['decisions'][left_index].reference_id
        if failure is None and name:
            rows = sorted((r for r in frozen_observations
                if max(left.start, support.time_seconds-.6) <= r.time_seconds <= support.time_seconds),
                key=lambda r: r.time_seconds)
            named = [r for r in rows if _valid(r) and joints.get(r.frame_index, {}).get('status') == 'accepted'
                and joints[r.frame_index].get('name') == name]
            if (not named or named[-1].frame_index != lo
                    or support.time_seconds-named[0].time_seconds < .15
                    or any(joints.get(r.frame_index, {}).get('status') == 'conflict'
                        or joints.get(r.frame_index, {}).get('status') == 'accepted'
                        and joints[r.frame_index].get('name') != name for r in rows)):
                failure = 'unconfirmed_outgoing_name'
            elif matcher is None:
                failure = 'missing_primary_name_proof'
            else:
                contrary = [r.frame_index for r in rows if _valid(r)
                    and matcher.match(r, left, 'boundary-event-original-face').reference_id not in (None, name)]
                if contrary:
                    failure = 'conflicting_original_primary'
                    candidate['conflicting_primary_frames'] = contrary
                else:
                    support = named[0]
        if failure is None:
            # Use frozen observations, not the accumulated output as proof.
            path = replace(left, start=support.time_seconds, end=part.end)
            failure, frames = _path(frame_records, path, support, fps=fps,
                sample_step=sample_step, cut_frames=cut_frames, handoffs=handoffs)
            candidate['support_frames'] = frames
            # Check the last original owner as well as the earlier name seed.
            if failure is None:
                failure, _ = _path(frame_records, path, original[lo], fps=fps,
                    sample_step=sample_step, cut_frames=cut_frames, handoffs=handoffs)
        if failure:
            audit['rejected'].append(dict(candidate, reason=failure))
            groups.append([index])
        else:
            groups[-1].append(index)
            delta = part.end-part.start if name else 0.
            audit['joins'].append(dict(candidate, name=name, newly_named_seconds=delta,
                unknown_delta_seconds=-delta, reason='existing_observation_boundary_policy'))
    if not audit['joins']:
        return output, audit
    keys = ('segments', 'decisions', 'labels', 'evidence', 'previews', 'preview_sources')
    result = {**output, **{key: [] for key in keys}, 'accurate_indices': []}
    for group in groups:
        first, last = group[0], group[-1]
        for key in keys:
            result[key].append(output[key][first])
        if any(i in output['accurate_indices'] for i in group):
            result['accurate_indices'].append(len(result['segments'])-1)
        if first != last:
            result['segments'][-1] = replace(output['segments'][first], end=output['segments'][last].end,
                bboxes=[b for i in group for b in output['segments'][i].bboxes])
            result['evidence'][-1] = [r for i in group for r in output['evidence'][i]]
            result['preview_sources'][-1] = tuple(ChainMap(*(output['preview_sources'][i][k] for i in group)) for k in (0, 1))
    return result, audit
