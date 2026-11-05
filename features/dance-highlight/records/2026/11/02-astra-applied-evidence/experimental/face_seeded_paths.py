"""Join a whole face gap to an original, independently named subject path.

Uses existing observations and source pixels only. No SAM, new face inference,
output-label votes, or gallery updates. Main/group eligibility stays frozen.
"""
from bisect import bisect_left, bisect_right
from collections import ChainMap
from dataclasses import replace
import cv2
import numpy as np

from .body_continuity import _check_source_chain
from .member_timeline import _valid
from .reference_matcher import SegmentReferenceDecision
from .segment import Segment

VERSION = 'original_face_pair_path_v1'


def _nearest_pair(rows, side):
    ordered = rows if side == 'right' else rows[::-1]
    j = 1
    for i, first in enumerate(ordered):
        j = max(j, i+1)
        while j < len(ordered) and abs(ordered[j].time_seconds-first.time_seconds) < .15-1e-6:
            j += 1
        if j < len(ordered) and abs(ordered[j].time_seconds-first.time_seconds) <= .6+1e-6:
            return sorted((first, ordered[j]), key=lambda row: row.frame_index)
    return None


def _join_proposals(output, proposals):
    if not proposals:
        return output
    edges = {min(p['index'], p['neighbor_index']) for p in proposals}
    names = {p['index']: p['name'] for p in proposals}
    keys = ('segments', 'decisions', 'labels', 'previews', 'evidence', 'preview_sources')
    result = {**output, **{key: [] for key in keys}, 'accurate_indices': []}
    accurate = set(output['accurate_indices'])
    i = 0
    while i < len(output['segments']):
        last = i
        while last in edges:
            last += 1
        indices = range(i, last+1)
        for key in keys:
            result[key].append(output[key][i])
        if any(j in accurate for j in indices):
            result['accurate_indices'].append(len(result['segments'])-1)
        if last != i:
            name = next(names[j] for j in indices if j in names)
            result['segments'][-1] = replace(output['segments'][i], end=output['segments'][last].end,
                bboxes=[box for j in indices for box in output['segments'][j].bboxes])
            result['decisions'][-1] = SegmentReferenceDecision(name, 'matched', 'original_face_pair_path')
            result['evidence'][-1] = [row for j in indices for row in output['evidence'][j]]
            # Start with named evidence, never a different person's unknown preview.
            ordered = sorted(indices, key=lambda j: output['decisions'][j].reference_id != name)
            result['previews'][-1] = [image for j in ordered for image in output['previews'][j]][:5]
            result['preview_sources'][-1] = tuple(
                ChainMap(*(output['preview_sources'][j][k] for j in ordered)) for k in (0, 1))
        i = last+1
    result['labels'] = [i+1 if d.reference_id else None for i, d in enumerate(result['decisions'])]
    return result


def recover_face_seeded_paths(output, frame_records, observations, joint_matches, matcher,
                             *, video_path, fps, group_segments, handoffs, role_observations):
    audit = dict(version=VERSION, recovered_seconds=0., proposals=[], candidates=[], source_checks=0)
    if not observations or not np.isfinite(fps) or fps <= 0 or handoffs is None:
        audit['reason'] = 'missing_original_context'
        return output, audit
    records = {round(r.t*fps): r for r in frame_records}
    rows_by_frame = {o.frame_index: o for o in observations}
    rows = sorted(rows_by_frame.values(), key=lambda o: o.time_seconds)
    times = [o.time_seconds for o in rows]
    record_frames = sorted(records)
    joints = {int(k): v for k, v in joint_matches.items()}
    roles = {r['frame']: r for r in role_observations}
    primary = {}
    segments, decisions = output['segments'], output['decisions']

    def owned(row):
        record = records.get(row.frame_index)
        return (record is not None and record.main_bbox is not None
                and row.body_bbox is not None
                and np.allclose(row.body_bbox, record.main_bbox, atol=1e-3, rtol=0))

    def named_seed(row, name):
        match = joints.get(row.frame_index, {})
        return (_valid(row) and row.detector_score >= .9 and owned(row)
                and match.get('status') == 'accepted' and match.get('name') == name)

    cap = None
    source_cache = {}  # Frozen observations/source within this invocation only.
    try:
        for index, (segment, decision) in enumerate(zip(segments, decisions)):
            if decision.reference_id:
                continue
            candidate = dict(index=index, start=segment.start, end=segment.end, paths=[])
            audit['candidates'].append(candidate)
            lo = bisect_right(times, segment.start)-1
            hi = bisect_left(times, segment.end)
            if lo < 0 or hi >= len(rows):
                candidate['reason'] = 'missing_boundary_observation'
                continue
            for side, neighbor_index in (('left', index-1), ('right', index+1)):
                if not 0 <= neighbor_index < len(segments):
                    continue
                neighbor, name = segments[neighbor_index], decisions[neighbor_index].reference_id
                gap = segment.start-neighbor.end if side == 'left' else neighbor.start-segment.end
                if not name or abs(gap) > 1e-6:
                    continue
                seed_rows = rows[bisect_left(times, neighbor.start):bisect_left(times, neighbor.end)]
                pair = _nearest_pair([o for o in seed_rows if named_seed(o, name)], side)
                if pair is None:
                    continue
                first, last = min(rows[lo].frame_index, pair[0].frame_index), max(rows[hi].frame_index, pair[1].frame_index)
                path_rows = rows[bisect_left(times, first/fps-1e-6):bisect_right(times, last/fps+1e-6)]
                path = dict(side=side, name=name, neighbor_index=neighbor_index,
                            seed_frames=[o.frame_index for o in pair], proof_frames=[first, last])
                candidate['paths'].append(path)
                expected = record_frames[bisect_left(record_frames, first):bisect_right(record_frames, last)]
                failure = None
                if [o.frame_index for o in path_rows] != expected:
                    failure = 'missing_original_observation'
                elif any(not owned(o) for o in path_rows):
                    failure = 'unowned_body'
                elif any(records[o.frame_index].scene_kind != 'main' for o in path_rows):
                    failure = 'non_main_path'
                elif any(g.start < (last+1)/fps and first/fps < g.end for g in group_segments):
                    failure = 'group_on_proof_path'
                elif any(first < h['frame'] <= last for h in handoffs):
                    failure = 'handoff'
                elif any(not roles.get(o.frame_index, {}).get('closeup_subject')
                         or roles[o.frame_index].get('box') is None
                         or not np.allclose(roles[o.frame_index]['box'], o.body_bbox, atol=1e-3, rtol=0)
                         for o in path_rows):
                    failure = 'unproven_main_role_on_path'
                if failure is None:
                    valid = [o for o in path_rows if _valid(o)]
                    if any(joints.get(o.frame_index, {}).get('status') == 'accepted'
                           and joints[o.frame_index].get('name') != name for o in valid):
                        failure = 'accepted_face_conflict'
                    scope = Segment('main', None, first/fps, (last+1)/fps, [])
                    for row in valid:
                        if row.frame_index not in primary:
                            primary[row.frame_index] = matcher.match(row, scope, VERSION).reference_id
                    if any(primary[o.frame_index] and primary[o.frame_index] != name for o in valid):
                        failure = 'primary_face_conflict'
                    alien = [o for o in valid if min(1.-float(o.embedding @ s.embedding) for s in pair) > .65]
                    for j, a in enumerate(alien):
                        for b in alien[j+1:]:
                            if b.time_seconds-a.time_seconds > .6:
                                break
                            if b.time_seconds-a.time_seconds >= .15 and 1.-float(a.embedding @ b.embedding) <= .6:
                                failure = 'repeated_alien_face'
                if failure is None:
                    if cap is None:
                        cap = cv2.VideoCapture(str(video_path))
                    if not cap.isOpened() or abs(float(cap.get(cv2.CAP_PROP_FPS))-fps) > .01:
                        failure = 'source_unavailable_or_fps_mismatch'
                    else:
                        key = first, last
                        if key not in source_cache:
                            source_audit = {}
                            reason = _check_source_chain(cap, path_rows, records, audit=source_audit)
                            source_cache[key] = reason, source_audit
                            audit['source_checks'] += 1
                        failure, source_audit = source_cache[key]
                        path.update(source_audit)
                path['reason'] = failure
            good = [p for p in candidate['paths'] if p['reason'] is None]
            if len({p['name'] for p in good}) != 1:
                candidate['reason'] = 'conflicting_paths' if good else 'no_proven_path'
                continue
            # Only remove the edge whose complete original path was checked.
            chosen = min(good, key=lambda p: p['proof_frames'][1]-p['proof_frames'][0])
            audit['proposals'].append(dict(index=index, start=segment.start, end=segment.end, **chosen))
            audit['recovered_seconds'] += segment.end-segment.start
            candidate['reason'] = 'proven_original_face_path'
    finally:
        if cap is not None:
            cap.release()
    return _join_proposals(output, audit['proposals']), audit
