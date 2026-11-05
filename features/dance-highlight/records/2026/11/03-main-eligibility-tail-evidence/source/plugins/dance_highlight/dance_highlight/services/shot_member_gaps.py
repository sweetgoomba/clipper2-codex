"""Fill a two-sided same-name gap with independent original proof per shot.

Cuts reset body correspondence. An existing output name only nominates a gap;
original owned faces establish each shot, and the entire newly named interval
must follow its own shot's measured main body. No inferred name becomes a seed.
"""
from bisect import bisect_right
from collections import ChainMap
from dataclasses import replace
from time import perf_counter

import cv2
import numpy as np

from .body_continuity import _check_source_chain
from .member_timeline import _identity_boundaries, _valid
from .reference_matcher import SegmentReferenceDecision
from .segment import Segment

VERSION = 'independent_shot_member_gap_v2_proved_suffix'


# Deterministic work limits, not a clip-length or identity threshold. Exhaustion
# retains the original unknown; it never deletes an existing output interval.
MAX_SOURCE_PATHS = 12
MAX_SOURCE_FRAMES = 240


class _BoundedSource:
    def __init__(self, path, fps):
        self.path, self.fps = path, fps
        self.cap = None
        self.last_frame = None
        self.cache, self.failed_transitions = {}, []
        self.audit = dict(path_limit=MAX_SOURCE_PATHS, frame_limit=MAX_SOURCE_FRAMES,
                          paths_used=0, frames_reserved=0, frames_read=0, seeks=0,
                          exact_cache_hits=0, superset_cache_hits=0, read_budget_exhausted=False)

    def get(self, prop):
        return self.cap.get(prop)

    def set(self, prop, value):
        self.audit['seeks'] += 1
        return self.cap.set(prop, value)

    def read(self):
        # Pixel validation may revisit a frame after the first source scan.
        # Bound actual decoder reads, including those additional windows.
        if self.audit['frames_read'] >= MAX_SOURCE_FRAMES:
            self.audit['read_budget_exhausted'] = True
            return False, None
        self.last_frame = round(float(self.cap.get(cv2.CAP_PROP_POS_FRAMES)))
        self.audit['frames_read'] += 1
        return self.cap.read()

    def check(self, frames, rows, records, sample_step):
        key = tuple(frames)
        if key in self.cache:
            self.audit['exact_cache_hits'] += 1
            return self.cache[key]
        for low, high, reason in self.failed_transitions:
            if frames[0] <= low <= high <= frames[-1]:
                self.audit['superset_cache_hits'] += 1
                return reason
        count = frames[-1]-frames[0]+1
        if self.audit['paths_used'] >= MAX_SOURCE_PATHS:
            return 'source_path_budget_exhausted'
        if max(self.audit['frames_reserved'], self.audit['frames_read'])+count > MAX_SOURCE_FRAMES:
            return 'source_frame_budget_exhausted'
        self.audit['paths_used'] += 1
        self.audit['frames_reserved'] += count
        if self.cap is None:
            self.cap = cv2.VideoCapture(str(self.path))
        self.last_frame = None
        if not self.cap.isOpened() or abs(float(self.cap.get(cv2.CAP_PROP_FPS))-self.fps) > .01:
            failure = 'source_unavailable_or_fps_mismatch'
        else:
            try:
                failure = _check_source_chain(self, [rows[f] for f in frames], records)
            except (cv2.error, ValueError, RuntimeError, IndexError):
                failure = 'source_or_body_proof_error'
            if self.audit['read_budget_exhausted']:
                failure = 'source_frame_budget_exhausted'
        self.cache[key] = failure
        # These failures describe a particular measured point/transition and
        # persist in every containing path. A median-based isolated-change
        # failure is NOT monotone in path length, so only its exact path caches.
        if self.last_frame is not None:
            widths = {'visual_cut': 1, 'unconfirmed_body_continuity': sample_step,
                      'ambiguous_main_body': 0}
            if failure in widths:
                self.failed_transitions.append((self.last_frame-widths[failure], self.last_frame, failure))
        return failure

    def close(self):
        if self.cap is not None:
            self.cap.release()


def _owned(row, record):
    return bool(row is not None and record is not None and row.body_bbox is not None
                and record.main_bbox is not None
                and np.allclose(row.body_bbox, record.main_bbox, atol=1e-3, rtol=0))



def _fresh_main_role(record, row, role):
    """Require a current selected face measurement, not an incumbent hold.

    All original raw bodies remain in the source correspondence check. A
    missing rival face is not removed or replaced by an invented pose here.
    """
    if (record.scene_kind != 'main' or record.scene_reason != 'main_eligible_composition'
            or role.get('reason') not in ('measured_face_composition', 'dominant_face',
                'confirmed_dominant_face', 'corroborated_foreground_subject',
                'confirmed_corroborated_foreground_subject')
            or role.get('box') is None
            or not np.allclose(role['box'], row.body_bbox, atol=1e-3, rtol=0)):
        return False
    owners = [i for i, box in enumerate(record.person_bboxes)
              if np.allclose(box, row.body_bbox, atol=1e-3, rtol=0)]
    if len(owners) != 1:
        return False
    seen, selected = set(), None
    for feature in role.get('features', []):
        index = feature.get('index')
        box = np.asarray(feature.get('box', []))
        if (not isinstance(index, int) or isinstance(index, bool) or index in seen
                or not 0 <= index < len(record.person_bboxes) or box.shape != (4,)
                or not np.isfinite(box).all()
                or not np.allclose(box, record.person_bboxes[index], atol=1e-3, rtol=0)):
            return False
        seen.add(index)
        if index == owners[0]:
            selected = feature
    if selected is None or selected.get('source') != 'detected':
        return False
    try:
        size, x = float(selected['size']), float(selected['x'])
        return bool(np.isfinite(size) and size > 0 and np.isfinite(x)
                    and row.body_bbox[0] <= x <= row.body_bbox[2])
    except (KeyError, TypeError, ValueError):
        return False


def _handoff_overlaps(handoff, start, end, fps):
    """Closed brackets protect the exact two join boundaries as well."""
    try:
        current = float(handoff['time'] if handoff.get('time') is not None
                        else handoff['frame']/fps)
        previous = float(handoff['previous_time'] if handoff.get('previous_time') is not None
                         else handoff['previous_frame']/fps if handoff.get('previous_frame') is not None
                         else current)
        if not np.isfinite([previous, current]).all() or previous > current:
            return True
        return previous <= end+1e-6 and start-1e-6 <= current
    except (KeyError, TypeError, ValueError):
        return True


def _merge(output, groups):
    keys = ('segments', 'decisions', 'labels', 'evidence', 'previews', 'preview_sources')
    result = {**output, **{key: [] for key in keys}, 'accurate_indices': []}
    ends = {first: (last, name) for first, last, name in groups}
    i = 0
    while i < len(output['segments']):
        last, name = ends.get(i, (i, output['decisions'][i].reference_id))
        indices = range(i, last+1)
        for key in keys:
            result[key].append(output[key][i])
        if any(j in output['accurate_indices'] for j in indices):
            result['accurate_indices'].append(len(result['segments'])-1)
        if last != i:
            result['segments'][-1] = replace(output['segments'][i],
                end=output['segments'][last].end,
                bboxes=[box for j in indices for box in output['segments'][j].bboxes])
            result['decisions'][-1] = SegmentReferenceDecision(name, 'matched', VERSION)
            result['evidence'][-1] = [row for j in indices for row in output['evidence'][j]]
            result['previews'][-1] = [p for j in indices for p in output['previews'][j]][:5]
            result['preview_sources'][-1] = tuple(ChainMap(
                *(output['preview_sources'][j][k] for j in indices)) for k in (0, 1))
        i = last+1
    result['labels'] = [i+1 if d.reference_id else None for i, d in enumerate(result['decisions'])]
    return result


def _restore_suffixes(output, recoveries, fps):
    """Keep an unproved prefix intact; join only its proved suffix to the right."""
    keys = ('segments', 'decisions', 'labels', 'evidence', 'previews', 'preview_sources')
    result = {**output, **{key: [] for key in keys}, 'accurate_indices': []}
    for index, (segment, decision) in enumerate(zip(output['segments'], output['decisions'], strict=True)):
        local = [r for r in recoveries if not decision.reference_id
                 and r['start'] < segment.end and segment.start < r['end']]
        edges = sorted({segment.start, segment.end, *(max(segment.start, r['start']) for r in local),
                        *(min(segment.end, r['end']) for r in local)})
        for start, end in zip(edges, edges[1:]):
            if index in output['accurate_indices']:
                result['accurate_indices'].append(len(result['segments']))
            if not local:
                for key in keys:
                    result[key].append(output[key][index])
                continue
            claimed = next((r for r in local if r['start'] <= start and end <= r['end']), None)
            evidence = [(o, n) for o, n in output['evidence'][index] if start <= o.time_seconds < end]
            sources = tuple({f: value for f, value in table.items() if start <= f/fps < end}
                            for table in output['preview_sources'][index])
            result['segments'].append(replace(segment, start=start, end=end,
                bboxes=[b for b in segment.bboxes if start <= b[0] < end]))
            result['decisions'].append(SegmentReferenceDecision(claimed['name'], 'matched', VERSION)
                                       if claimed else decision)
            result['labels'].append(output['labels'][index])
            result['evidence'].append(evidence)
            result['preview_sources'].append(sources)
            ranked = sorted((o for o, _ in evidence), key=lambda o: o.quality, reverse=True)
            result['previews'].append([sources[0].get(o.frame_index) or sources[1][o.frame_index]
                for o in ranked if o.frame_index in sources[0] or o.frame_index in sources[1]][:5])
    groups = []
    for recovery in recoveries:
        first = next(i for i, s in enumerate(result['segments']) if abs(s.start-recovery['start']) < 1e-6)
        last = first
        while (last+1 < len(result['segments'])
               and result['decisions'][last+1].reference_id == recovery['name']
               and abs(result['segments'][last].end-result['segments'][last+1].start) < 1e-6
               and result['segments'][last].end <= recovery['end']+1e-6):
            last += 1
        groups.append((first, last, recovery['name']))
    return _merge(result, groups)


def recover_shot_member_gaps(output, frame_records, observations, joint_matches,
                             secondary_matches, matcher, *, video_path, fps, sample_step,
                             cut_frames, handoffs, role_observations, group_segments):
    source = _BoundedSource(video_path, fps)
    audit = dict(version=VERSION, recovered_seconds=0., candidates=[], recoveries=[],
                 source_budget=source.audit)
    if (matcher is None or cut_frames is None or handoffs is None or not observations
            or not np.isfinite(fps) or fps <= 0 or sample_step < 1):
        return output, dict(audit, reason='missing_original_context')
    cuts = sorted(set(int(f) for f in cut_frames))
    if not cuts:
        return output, dict(audit, reason='no_source_cuts')
    rows = {o.frame_index: o for o in observations}
    if len(rows) != len(observations):
        return output, dict(audit, reason='duplicate_original_frame')
    records = {round(r.t*fps): r for r in frame_records}
    if len(records) != len(frame_records):
        return output, dict(audit, reason='duplicate_original_pose')
    joints = {int(f): value for f, value in joint_matches.items()}
    secondary = {m['frame_index']: m for m in secondary_matches}
    roles = {r['frame']: r for r in role_observations}
    ordered = sorted(rows)
    names = {}

    def original_names(frame):
        if frame not in names:
            row, record = rows.get(frame), records.get(frame)
            accepted = set()
            if _owned(row, record) and _valid(row):
                primary = matcher.match(row, Segment('main', None, row.time_seconds,
                    row.time_seconds+1/fps, []), VERSION).reference_id
                if primary:
                    accepted.add(primary)
                joint = joints.get(frame, {})
                if joint.get('status') == 'accepted' and joint.get('name'):
                    accepted.add(joint['name'])
                match = secondary.get(frame, {})
                # Only the original direct-reference result. Window/video
                # recovery shares observations and cannot supply another seed.
                if match.get('reason') == 'secondary_reference_match' and match.get('name'):
                    accepted.add(match['name'])
            names[frame] = accepted
        return names[frame]

    def conflict(start, end, name):
        local = [rows[f] for f in ordered if start <= rows[f].time_seconds < end]
        if any(original_names(o.frame_index)-{name} for o in local):
            return 'competing_original_face'
        direct = [o for o in local if original_names(o.frame_index) == {name}]
        valid = [o for o in local if _valid(o) and _owned(o, records.get(o.frame_index))]
        if direct:
            alien = [o for o in valid if min(1.-float(o.embedding@s.embedding) for s in direct) > .65]
            if any(.15 <= b.time_seconds-a.time_seconds <= .6
                   and 1.-float(a.embedding@b.embedding) <= .6
                   for j, a in enumerate(alien) for b in alien[j+1:]):
                return 'repeated_alien_face'
        scope = Segment('main', None, start, end, [])
        boundaries = _identity_boundaries(scope, local,
            [name if original_names(o.frame_index) == {name} else None for o in local], [])
        if any(b['reason'] in ('repeated_face_change', 'repeated_reference_change') for b in boundaries):
            return 'repeated_identity_boundary'
        return None

    segments, decisions = output['segments'], output['decisions']
    groups, suffixes = [], []
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
            if first == 0 or last+1 == len(segments):
                continue
            left, right = first-1, last+1
            name = decisions[left].reference_id
            if (not name or name != decisions[right].reference_id
                    or decisions[left].status != 'matched' or decisions[right].status != 'matched'
                    or abs(segments[left].end-segments[first].start) > 1e-6
                    or abs(segments[last].end-segments[right].start) > 1e-6):
                continue
            start, end = segments[first].start, segments[last].end
            recovery_start = start
            candidate = dict(start=start, end=end, name=name, shots=[], cut_frames=[])
            audit['candidates'].append(candidate)
            started = perf_counter()
            lo, hi = start-.600001, end+.600001
            local = [f for f in ordered if lo <= rows[f].time_seconds <= hi]
            before = [f for f in local if segments[left].start <= rows[f].time_seconds < start
                      and original_names(f) == {name}]
            after = [f for f in local if end <= rows[f].time_seconds < segments[right].end
                     and original_names(f) == {name}]
            failure = None
            if not before or not after:
                failure = 'missing_original_two_sided_faces'
            else:
                candidate['cut_frames'] = [c for c in cuts if before[-1] < c <= after[0]]
                if not candidate['cut_frames']:
                    failure = 'no_source_cut_between_original_faces'
            unknown = [f for f, r in records.items() if start <= r.t < end]
            observed = [f for f in ordered if start <= rows[f].time_seconds < end]
            first_source, last_source = int(np.ceil(start*fps-1e-6)), int(np.ceil(end*fps-1e-6))
            expected = [f for f in range(first_source, last_source)
                        if (f-ordered[0]) % sample_step == 0]
            if failure is None and (not unknown or sorted(unknown) != observed or observed != expected):
                failure = 'missing_original_observation'
            if failure is None and any(records[f].scene_kind != 'main' or not _owned(rows[f], records[f])
                                       for f in unknown):
                failure = 'ineligible_or_unowned_main'
            if failure is None and any(not _fresh_main_role(records[f], rows[f], roles.get(f, {}))
                                       for f in unknown):
                failure = 'unmeasured_or_unowned_main_role'
            if failure is None and any(g.start < end and start < g.end for g in group_segments):
                failure = 'separate_group_overlap'
            if failure is None and any(_handoff_overlaps(h, start, end, fps) for h in handoffs):
                failure = 'main_handoff'
            if failure is None:
                failure = conflict(segments[left].start, segments[right].end, name)
            if failure is None:
                new_frames = range(first_source, last_source)
                shot_ids = {bisect_right(cuts, f) for f in new_frames}
                shot_ids.update((bisect_right(cuts, before[-1]), bisect_right(cuts, after[0])))
                for shot in sorted(shot_ids):
                    in_shot = [f for f in local if bisect_right(cuts, f) == shot]
                    new = [f for f in unknown if bisect_right(cuts, f) == shot]
                    shot_new_source = [f for f in new_frames if bisect_right(cuts, f) == shot]
                    shot_start = cuts[shot-1]/fps if shot else -float('inf')
                    shot_end = cuts[shot]/fps if shot < len(cuts) else float('inf')
                    new_start, new_end = max(start, shot_start), min(end, shot_end)
                    new_time = [new_start, new_end] if new_start < new_end else None
                    direct = [f for f in in_shot if original_names(f) == {name}]
                    pairs = [(a, b) for j, a in enumerate(direct) for b in direct[j+1:]
                             if .15-1e-6 <= rows[b].time_seconds-rows[a].time_seconds <= .600001]
                    detail = dict(shot=shot, new_frames=new, new_source_frames=shot_new_source,
                                  new_time=new_time, seed_frames=[], source_frames=[])
                    candidate['shots'].append(detail)
                    # Source time may begin between measured observations. An
                    # empty sampled list does not turn that time into an already
                    # named shot; even a partial source-frame interval stays unknown.
                    if (shot_new_source or new_time is not None) and not new:
                        failure = 'unobserved_new_shot_source'
                        break
                    if not pairs:
                        failure = 'shot_without_independent_original_faces'
                        break
                    supported = {f for pair in pairs for f in pair}
                    supported_source = [f for f in shot_new_source if min(
                        abs(f/fps-rows[s].time_seconds) for s in supported) <= .600001]
                    if len(supported_source) != len(shot_new_source):
                        # A shifted source edge can add a few unproved prefix
                        # frames to an otherwise independently proved gap. Do
                        # not discard that proof, or extend its .6s contract.
                        # Only one contiguous supported suffix in a single new
                        # shot is eligible; all other failures still abstain.
                        new_shots = {bisect_right(cuts, f) for f in new_frames}
                        if (not supported_source or len(new_shots) != 1
                                or supported_source != list(range(supported_source[0], last_source))):
                            failure = 'same_shot_support_expired'
                            break
                        recovery_start = supported_source[0]/fps
                        new = [f for f in unknown if records[f].t >= recovery_start]
                        shot_new_source = supported_source
                        new_start, new_end = recovery_start, end
                        new_time = [new_start, new_end]
                        detail.update(new_frames=new, new_source_frames=shot_new_source, new_time=new_time)
                        if not new:
                            failure = 'unobserved_new_shot_source'
                            break
                    targets = [records[f].t for f in new] or [start if in_shot[-1] < before[-1]+1 else end]
                    pairs.sort(key=lambda pair: max(abs(t-rows[f].time_seconds) for t in targets for f in pair))
                    if new_time is None:
                        detail.update(seed_frames=list(pairs[0]), proof_kind='original_named_shot_faces')
                        continue
                    detail['proof_kind'] = 'new_main_source_path'
                    attempts = []
                    for pair in pairs:
                        low, high = min([*new, *pair]), max([*new, *pair])
                        if new:
                            preceding = [f for f in in_shot if rows[f].time_seconds <= new_start]
                            following = [f for f in in_shot if rows[f].time_seconds >= new_end]
                            if preceding:
                                low = min(low, max(preceding))
                            if following:
                                high = max(high, min(following))
                        path = list(range(low, high+1, sample_step))
                        path_failure = None
                        if (path[-1] != high or any(f not in rows or f not in records for f in path)
                                or any(abs(rows[f].time_seconds-f/fps) > 1e-5
                                       or abs(records[f].t-rows[f].time_seconds) > 1e-5 for f in path)):
                            path_failure = 'missing_original_cadence'
                        elif path[0] > shot_new_source[0] or path[-1] < shot_new_source[-1]:
                            path_failure = 'unobserved_source_edge'
                        elif any(not _owned(rows[f], records[f]) or records[f].scene_kind != 'main' for f in path):
                            path_failure = 'ineligible_or_unowned_support_path'
                        elif any(_handoff_overlaps(h, rows[low].time_seconds, rows[high].time_seconds, fps)
                                 for h in handoffs):
                            path_failure = 'main_handoff_on_support_path'
                        else:
                            path_failure = source.check(path, rows, records, sample_step)
                        attempts.append(dict(seed_frames=list(pair), reason=path_failure or 'proved'))
                        if path_failure in ('source_path_budget_exhausted', 'source_frame_budget_exhausted'):
                            candidate['budget_reason'] = path_failure
                            break
                        if path_failure is None:
                            detail.update(seed_frames=list(pair), source_frames=path)
                            break
                    detail['attempts'] = attempts
                    if not detail['seed_frames']:
                        failure = 'shot_body_or_source_path_unconfirmed'
                        break
            if failure is None:
                group = (left, right, name)
                if recovery_start > start:
                    candidate.update(start=recovery_start, unresolved_prefix=[start, recovery_start])
                    suffixes.append(candidate)
                elif groups and left <= groups[-1][1]:
                    previous = groups[-1]
                    failure = conflict(segments[previous[0]].start, segments[right].end, name)
                    if failure is None and previous[2] == name:
                        groups[-1] = (previous[0], right, name)
                    elif failure is None:
                        failure = 'competing_accumulated_names'
                else:
                    groups.append(group)
                if failure is None:
                    audit['recovered_seconds'] += end-recovery_start
                    audit['recoveries'].append(candidate)
            candidate.update(reason=failure or 'independent_shot_main_identity', seconds=perf_counter()-started)
    finally:
        source.close()
    result = _merge(output, groups) if groups else output
    return (_restore_suffixes(result, suffixes, fps) if suffixes else result), audit
