"""Move a late existing named boundary to the first observed incoming body.

Original independent joint faces anchor one selected-body path. Output names,
main eligibility, group membership and evidence identities never supply votes
and never change. Source pixels are read only after the observed path passes.
"""
from collections import ChainMap
from dataclasses import replace
import math
import time

import cv2
import numpy as np

from .body_continuity import _color_cut
from .member_timeline import _valid
from .observed_main import strict_pose_corresponding
from .scene_cut_proof import spatial_cut_candidate
from .segment import Segment
from .source_reader import SourceFrameReader

VERSION = 'original_incoming_selected_body_v1'


def _model_ranks(joint):
    ranks = joint.get('model_candidates')
    if not isinstance(ranks, (list, tuple)) or len(ranks) != 2:
        return None
    try:
        if not math.isfinite(joint['margin']):
            return None
        for rows in ranks:
            if (len(rows) < 2 or len({r['name'] for r in rows}) != len(rows)
                    or any(not r['name'] or not math.isfinite(r['distance']) for r in rows)
                    or any(a['distance'] > b['distance'] for a, b in zip(rows, rows[1:]))):
                return None
        if {r['name'] for r in ranks[0]} != {r['name'] for r in ranks[1]}:
            return None
        values = [next(r['distance'] for r in rows if r['name'] == joint['best']) for rows in ranks]
        if not np.allclose(values, [joint['primary'], joint['secondary']], atol=1e-6, rtol=0):
            return None
        if not np.isclose(np.mean(values), joint['distance'], atol=1e-6, rtol=0):
            return None
    except (KeyError, TypeError, ValueError, StopIteration):
        return None
    return ranks


def _body(record):
    if record.scene_kind != 'main' or record.main_bbox is None:
        return None
    boxes, poses = record.person_bboxes, record.person_pose_keypoints
    if len(boxes) != len(poses):
        return None
    if any(np.asarray(p).shape != (17, 3) or not np.isfinite(p).all() for p in poses):
        return None
    features = [dict(index=i, pose_keypoints=np.asarray(p)) for i, p in enumerate(poses)]
    selected = [f for f, box in zip(features, boxes)
                if np.allclose(box, record.main_bbox, atol=1e-3, rtol=0)]
    return dict(features=features, selected=selected[0]) if len(selected) == 1 else None


def _owns(row, record):
    return (row.body_bbox is not None and record.main_bbox is not None
            and np.allclose(row.body_bbox, record.main_bbox, atol=1e-3, rtol=0))


def reconcile_incoming_identity_boundary(output, frame_records, observations, joint_matches,
                                        matcher, *, fps, sample_step, cut_frames, source_path,
                                        video_size, handoffs=()):
    """Return output and audit; failures return the original object unchanged.

Only two adjacent, already different named main parts can be corrected. The
incoming part needs two original accepted joint faces separated by at least
.15s, each with the same primary-video winner and no positive photo conflict.
Every intervening sampled selected body must reciprocally match. The boundary
can move only to the first such observed incoming sample, never a midpoint.
"""
    started = time.perf_counter()
    audit = dict(version=VERSION, corrections=[], candidates=[], corrected_seconds=0.,
                 source_reads=dict(reads=0, seeks=0, grabs=0, cache_hits=0, decode_seconds=0.))
    def finish(result, reason='complete'):
        audit.update(reason=reason, seconds=time.perf_counter() - started)
        return result, audit
    keys = ('segments', 'decisions', 'labels', 'previews', 'evidence', 'preview_sources')
    count = len(output['segments'])
    if any(len(output[k]) != count for k in keys):
        return finish(output, 'misaligned_output_arrays')
    if (not math.isfinite(fps) or fps <= 0 or not isinstance(sample_step, int) or sample_step < 1
            or cut_frames is None or handoffs is None or matcher is None):
        return finish(output, 'missing_source_context')
    records = {round(r.t * fps): r for r in frame_records}
    rows = {o.frame_index: o for o in observations}
    if len(records) != len(frame_records) or len(rows) != len(observations):
        return finish(output, 'duplicate_original_observation')
    joints = {int(f): j for f, j in joint_matches.items()}
    photo = {}
    bodies = {}
    def measured(frame):
        if frame not in bodies:
            bodies[frame] = _body(records[frame]) if frame in records else None
        return bodies[frame]
    def primary(row):
        if row.frame_index not in photo:
            scope = Segment('main', None, row.time_seconds, row.time_seconds + 1 / fps, [])
            photo[row.frame_index] = matcher.match(row, scope, VERSION).reference_id
        return photo[row.frame_index]
    def anchor(row, name):
        frame = row.frame_index
        joint = joints.get(frame, {})
        ranks = _model_ranks(joint)
        if (not _valid(row) or row.detector_score < .9 or frame not in records
                or abs(row.time_seconds - frame / fps) > 1e-6
                or not _owns(row, records[frame]) or measured(frame) is None
                or joint.get('status') != 'accepted' or joint.get('name') != name or ranks is None):
            return False
        return (all(r[0]['name'] == name for r in ranks)
                and max(joint['primary'], joint['secondary']) <= .6
                and joint['distance'] <= .5 and joint.get('margin', 0) >= .08
                and primary(row) in (None, name))
    def conflict(frame, name, *, strict_joint=True):
        joint = joints.get(frame, {})
        if strict_joint and joint.get('status') == 'conflict':
            return 'original_joint_conflict'
        if joint.get('status') == 'accepted' and joint.get('name') != name:
            return 'opposite_original_joint'
        if joint:
            ranks = _model_ranks(joint)
            if ranks is None:
                return 'invalid_original_model_ranks'
            for candidates, threshold in zip(ranks, (.6, .637)):
                a, b = candidates[:2]
                if (a['name'] != name and a['distance'] <= threshold
                        and b['distance'] - a['distance'] >= .08):
                    return 'opposite_reliable_original_model'
        row = rows.get(frame)
        if row is not None and _valid(row):
            if not _owns(row, records[frame]):
                return 'unowned_original_face'
            if primary(row) not in (None, name):
                return 'opposite_original_photo'
        return None

    def retained_outgoing(left, start, name):
        seeds = [o for o in sorted(rows.values(), key=lambda o: o.frame_index)
                 if left.start <= o.time_seconds < start / fps and anchor(o, name)]
        pair = next(((a, b) for b in reversed(seeds) for a in reversed(seeds)
                     if b.time_seconds - a.time_seconds >= .15 - 1e-6), None)
        if pair is None:
            return None, 'no_independent_retained_outgoing_anchors'
        a, b = pair
        path = list(range(a.frame_index, start, sample_step))
        if (not path or path[-1] != start - sample_step
                or any(a.frame_index < cut < start for cut in cut_frames)):
            return None, 'retained_outgoing_source_discontinuity'
        previous = None
        for frame in path:
            current = measured(frame)
            if current is None:
                return None, 'unobserved_retained_outgoing_body'
            if previous is not None:
                linked = strict_pose_corresponding(previous, previous['selected'], current)
                if linked is None or linked['index'] != current['selected']['index']:
                    return None, 'retained_outgoing_body_discontinuity'
            # This protects the existing outgoing name, without extending it.
            # Weak rejected model disagreement is not a contrary identity;
            # accepted joint/photo or reliable opposing model evidence is.
            if conflict(frame, name, strict_joint=False):
                return None, 'conflicting_retained_outgoing_identity'
            previous = current
        return dict(seed_frames=[a.frame_index, b.frame_index], path_frames=path), None

    reader = None
    try:
        for index in range(count - 1):
            left, right = output['segments'][index:index + 2]
            old, name = (d.reference_id for d in output['decisions'][index:index + 2])
            if (left.seg_type != 'main' or right.seg_type != 'main' or not old or not name
                    or old == name or abs(left.end - right.start) > 1e-6):
                continue
            seeds = [o for o in sorted(rows.values(), key=lambda o: o.frame_index)
                     if right.start <= o.time_seconds < right.end and anchor(o, name)]
            pair = next(((a, b) for i, a in enumerate(seeds) for b in seeds[i + 1:]
                         if b.time_seconds - a.time_seconds >= .15 - 1e-6), None)
            if pair is None:
                continue
            first, last = pair
            reverse = []
            previous = None
            stop = 'existing_left_start'
            for frame in range(last.frame_index, math.ceil(left.start * fps) - 1, -sample_step):
                current = measured(frame)
                if current is None:
                    stop = 'missing_or_ineligible_selected_body'
                    break
                if previous is not None:
                    if any(frame < cut <= frame + sample_step for cut in cut_frames):
                        stop = 'source_cut_inventory'
                        break
                    linked = strict_pose_corresponding(previous, previous['selected'], current)
                    if linked is None or linked['index'] != current['selected']['index']:
                        stop = 'unproven_or_different_selected_body'
                        break
                reverse.append(frame)
                previous = current
            if not reverse or first.frame_index not in reverse or reverse[-1] / fps >= right.start - 1e-8:
                continue
            start = reverse[-1]
            if start / fps <= left.start:
                continue
            path = list(reversed(reverse))
            candidate = dict(index=index, name=name, previous_name=old, before=right.start,
                             after=start / fps, seed_frames=[first.frame_index, last.frame_index],
                             path_frames=path, geometry_stop=stop)
            audit['candidates'].append(candidate)
            failure = next((reason for f in path if (reason := conflict(f, name))), None)
            outgoing = None
            if failure is None:
                outgoing, failure = retained_outgoing(left, start, old)
            source_first = outgoing['path_frames'][0] if outgoing else start
            if outgoing:
                candidate['retained_outgoing'] = outgoing
            if failure is None and any(source_first < cut <= last.frame_index for cut in cut_frames):
                failure = 'source_cut_inventory'
            if failure is None and any(start < h['frame'] <= last.frame_index for h in handoffs):
                failure = 'main_handoff_inside_incoming_path'
            if failure is not None:
                candidate['reason'] = failure
                continue
            if reader is None:
                reader = SourceFrameReader(source_path, fps)
            previous_image = reader.get(source_first)
            if previous_image.shape[:2] != (video_size[1], video_size[0]):
                raise ValueError('source_size_mismatch')
            for source_frame in range(source_first + 1, last.frame_index + 1):
                current_image = reader.get(source_frame)
                if current_image.shape != previous_image.shape:
                    raise ValueError('source_size_mismatch')
                color = _color_cut(cv2.resize(previous_image, (64, 36)), cv2.resize(current_image, (64, 36)))[0]
                if color or spatial_cut_candidate(previous_image, current_image):
                    failure = 'source_transition'
                    candidate['source_transition_frame'] = source_frame
                    break
                previous_image = current_image
            candidate['reason'] = failure or 'original_incoming_selected_body'
            candidate['source_frames_checked'] = [source_first, last.frame_index]
            if failure is None:
                audit['corrections'].append(candidate)
    except (OSError, ValueError, RuntimeError, cv2.error) as error:
        audit.update(corrections=[], error_type=type(error).__name__)
        return finish(output, 'source_unavailable')
    finally:
        if reader is not None:
            audit['source_reads'] = dict(reader.stats)
            reader.close()
    if not audit['corrections']:
        return finish(output)
    # Every candidate has passed before any output object is copied or changed.
    result = {**output, **{key: list(output[key]) for key in keys}}
    for change in audit['corrections']:
        i, boundary = change['index'], change['after']
        left, right = result['segments'][i:i + 2]
        if not left.start < boundary < right.end:
            audit.update(corrections=[])
            return finish(output, 'overlapping_boundary_corrections')
        boxes = left.bboxes + right.bboxes
        result['segments'][i] = replace(left, end=boundary, bboxes=[b for b in boxes if left.start <= b[0] < boundary])
        result['segments'][i + 1] = replace(right, start=boundary, bboxes=[b for b in boxes if boundary <= b[0] < right.end])
        sources = tuple(ChainMap(result['preview_sources'][i][k], result['preview_sources'][i + 1][k]) for k in (0, 1))
        evidence = result['evidence'][i] + result['evidence'][i + 1]
        for j in (i, i + 1):
            part = result['segments'][j]
            kept = [(o, n) for o, n in evidence if part.start <= o.time_seconds < part.end]
            result['evidence'][j] = kept  # Preserve original evidence identity, including None.
            result['preview_sources'][j] = sources
            result['previews'][j] = [sources[0].get(o.frame_index) or sources[1][o.frame_index]
                for o, _ in sorted(kept, key=lambda entry: entry[0].quality, reverse=True)
                if o.frame_index in sources[0] or o.frame_index in sources[1]][:5]
    audit['corrected_seconds'] = sum(c['before'] - c['after'] for c in audit['corrections'])
    return finish(result)
