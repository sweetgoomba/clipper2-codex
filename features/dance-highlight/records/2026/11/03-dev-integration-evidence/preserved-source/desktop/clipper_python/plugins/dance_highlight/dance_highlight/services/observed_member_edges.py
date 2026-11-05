"""Restore an unnamed output edge from an original, continuously selected main.

Output labels propose a neighboring member; two original owned faces must
independently establish that name. No restored label becomes recognition data.
"""
from collections import ChainMap
from dataclasses import replace
import cv2
import numpy as np

from .body_continuity import _check_source_chain
from .member_timeline import _valid
from .reference_matcher import SegmentReferenceDecision
from .segment import Segment

VERSION = 'observed_main_member_edge_v1'


def _unique_foreground_torso(record, video_size):
    from .stage_prominence import selected_foreground_torso
    return selected_foreground_torso(record, record.main_bbox, video_size)


def recover_observed_member_edges(output, frame_records, observations, joint_matches, matcher,
                                  *, video_path, fps, sample_step, handoffs, role_observations, video_size):
    audit = dict(version=VERSION, recovered_seconds=0., candidates=[], recoveries=[])
    if (handoffs is None or not observations or not role_observations
            or not np.isfinite(fps) or fps <= 0 or sample_step < 1):
        return output, audit
    records = {round(r.t*fps): r for r in frame_records}
    rows = sorted({o.frame_index: o for o in observations}.values(), key=lambda o:o.time_seconds)
    joints = {int(f): m for f, m in joint_matches.items()}
    roles = {r['frame']: r for r in role_observations}
    names = {}
    def original_name(row):
        if row.frame_index not in names:
            primary = matcher.match(row, Segment('main', None, row.time_seconds,
                row.time_seconds+1/fps, []), VERSION).reference_id if _valid(row) else None
            joint = joints.get(row.frame_index, {})
            secondary = joint.get('name') if _valid(row) and joint.get('status') == 'accepted' else None
            names[row.frame_index] = (primary, secondary)
        return names[row.frame_index]

    segments, decisions = output['segments'], output['decisions']
    groups = []
    cap = None
    try:
        i = 0
        while i < len(segments):
            if decisions[i].reference_id:
                i += 1
                continue
            first = i
            while (i+1 < len(segments) and not decisions[i+1].reference_id
                   and abs(segments[i].end-segments[i+1].start) < 1e-6):
                i += 1
            last = i
            i += 1
            start, end = segments[first].start, segments[last].end
            accepted = []
            for neighbor, direction in ((first-1, 'left'), (last+1, 'right')):
                if not 0 <= neighbor < len(segments):
                    continue
                span, name = segments[neighbor], decisions[neighbor].reference_id
                if not name or abs((span.end-start) if direction == 'left' else (end-span.start)) > 1e-6:
                    continue
                edge = start if direction == 'left' else end
                available = [o for o in rows if span.start <= o.time_seconds < span.end
                    and abs(o.time_seconds-edge) <= .600001 and _valid(o) and o.detector_score >= .9
                    and name in original_name(o) and all(n in (None, name) for n in original_name(o))]
                pairs = [(a, b) for j, a in enumerate(available) for b in available[j+1:]
                         if .15-1e-6 <= b.time_seconds-a.time_seconds <= .600001]
                if not pairs:
                    continue
                a, b = min(pairs, key=lambda pair: abs(pair[0 if direction == 'right' else 1].time_seconds-edge))
                lo, hi = (a.time_seconds, end) if direction == 'left' else (start, b.time_seconds+1/fps)
                local = [o for o in rows if lo <= o.time_seconds < hi]
                candidate = dict(start=start, end=end, name=name, direction=direction,
                                 seed_frames=[a.frame_index, b.frame_index])
                audit['candidates'].append(candidate)
                failure = None
                expected = sorted(f for f, r in records.items() if lo <= r.t < hi)
                if (not local or [o.frame_index for o in local] != expected
                        or any(b-a != sample_step for a, b in zip(expected, expected[1:]))):
                    failure = 'missing_original_observation'
                elif any(records[o.frame_index].scene_kind != 'main' for o in local):
                    failure = 'non_main_path'
                elif any(o.body_bbox is None or records[o.frame_index].main_bbox is None
                         or not np.allclose(o.body_bbox, records[o.frame_index].main_bbox, atol=1e-3, rtol=0)
                         for o in local):
                    failure = 'unowned_main_path'
                elif any(lo < h['time'] < hi for h in handoffs):
                    failure = 'main_handoff'
                elif any(n and n != name for o in local for n in original_name(o)):
                    failure = 'conflicting_original_face'
                if failure is None:
                    unknown = [o for o in local if start <= o.time_seconds < end]
                    actual_foreground = []
                    for o in local:
                        role = roles.get(o.frame_index, {})
                        if role.get('reason') not in ('dominant_face', 'confirmed_dominant_face',
                                'corroborated_foreground_subject', 'confirmed_corroborated_foreground_subject'):
                            continue
                        if role.get('box') is None or not np.allclose(role['box'], o.body_bbox, atol=1e-3, rtol=0):
                            continue
                        if any(f.get('source') == 'detected' and f.get('size') is not None
                               and np.allclose(f['box'], o.body_bbox, atol=1e-3, rtol=0)
                               for f in role.get('features', [])):
                            actual_foreground.append(o.time_seconds)
                    if (not unknown or not actual_foreground
                            or any(not _unique_foreground_torso(records[o.frame_index], video_size)
                                   or min(abs(t-o.time_seconds) for t in actual_foreground) > .600001
                                   for o in unknown)):
                        failure = 'unconfirmed_main_role'
                if failure is None:
                    step = float(np.median(np.diff([o.time_seconds for o in local])))
                    tolerance = min(.1, step/2)+.5/fps+1e-6
                    if (local[0].time_seconds-lo > tolerance or hi-local[-1].time_seconds > tolerance):
                        failure = 'unobserved_output_edge'
                if failure is None:
                    alien = [o for o in local if _valid(o)
                             and min(1.-float(o.embedding@s.embedding) for s in (a, b)) > .65]
                    if any(.15 <= y.time_seconds-x.time_seconds <= .6
                           and 1.-float(x.embedding@y.embedding) <= .6
                           for j, x in enumerate(alien) for y in alien[j+1:]):
                        failure = 'repeated_alien_face'
                if failure is None:
                    if cap is None:
                        cap = cv2.VideoCapture(str(video_path))
                    if not cap.isOpened() or abs(cap.get(cv2.CAP_PROP_FPS)-fps) > .01:
                        failure = 'source_unavailable_or_fps_mismatch'
                    else:
                        failure = _check_source_chain(cap, local, records, audit=candidate)
                candidate['reason'] = failure or 'original_selected_main_continuity'
                if failure is None:
                    accepted.append((neighbor, name, candidate))
            if not accepted:
                continue
            if len({name for _, name, _ in accepted}) != 1:
                for _, _, candidate in accepted:
                    candidate['reason'] = 'competing_original_names'
                continue
            name = accepted[0][1]
            group = (min(first, *(j for j, _, _ in accepted)), max(last, *(j for j, _, _ in accepted)), name)
            if groups and group[0] <= groups[-1][1] and groups[-1][2] == name:
                groups[-1] = (groups[-1][0], group[1], name)
            else:
                groups.append(group)
            audit['recovered_seconds'] += end-start
            audit['recoveries'].append(dict(start=start, end=end, name=name,
                directions=[c['direction'] for _, _, c in accepted]))
    finally:
        if cap is not None:
            cap.release()
    if not groups:
        return output, audit
    keys = ('segments', 'decisions', 'labels', 'previews', 'evidence', 'preview_sources')
    result = {**output, **{k: [] for k in keys}, 'accurate_indices': []}
    ends = {a: (b, name) for a, b, name in groups}
    i = 0
    while i < len(segments):
        last, name = ends.get(i, (i, decisions[i].reference_id))
        indices = range(i, last+1)
        for key in keys:
            result[key].append(output[key][i])
        if any(j in output['accurate_indices'] for j in indices):
            result['accurate_indices'].append(len(result['segments'])-1)
        if last != i:
            result['segments'][-1] = replace(segments[i], end=segments[last].end,
                bboxes=[r for j in indices for r in segments[j].bboxes])
            result['decisions'][-1] = SegmentReferenceDecision(name, 'matched', VERSION)
            result['evidence'][-1] = [r for j in indices for r in output['evidence'][j]]
            result['previews'][-1] = [p for j in indices for p in output['previews'][j]][:5]
            result['preview_sources'][-1] = tuple(ChainMap(*(output['preview_sources'][j][k] for j in indices)) for k in (0, 1))
        i = last+1
    result['labels'] = [i+1 if d.reference_id else None for i, d in enumerate(result['decisions'])]
    return result, audit
