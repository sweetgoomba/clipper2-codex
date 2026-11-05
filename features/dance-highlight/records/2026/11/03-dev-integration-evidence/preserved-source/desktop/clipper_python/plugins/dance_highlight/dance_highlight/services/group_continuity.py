"""Continue observed ensemble membership independently of the selected main.

Only gaps between original exported groups can be joined. Three distinct
physical bodies must remain directly observed and reciprocally matched through
all samples. Original source frames veto intervening edits. This changes group
output only; it never mutates frame records or supplies identity evidence.
"""
from bisect import bisect_left
from dataclasses import replace
from itertools import combinations
import math
import time

import cv2
import numpy as np

from .body_continuity import _color_cut
from .observed_main import strict_pose_corresponding
from .scene_cut_proof import spatial_cut_candidate
from .source_reader import SourceFrameReader

VERSION = 'observed_group_membership_v1'


def _shared_head(a, b):
    common = a['head_visible'] & b['head_visible']
    scale = min(a['head_span'], b['head_span'])
    return bool(common.sum() >= 2 and scale > 0
                and np.linalg.norm(a['pose_keypoints'][:5, :2][common]
                                   - b['pose_keypoints'][:5, :2][common], axis=1).max() <= .3 * scale)


def _members(record, video_size):
    width, height = video_size
    if len(record.person_bboxes) != len(record.person_pose_keypoints):
        return None, 'missing_pose_inventory'
    features = []
    for index, (box, pose) in enumerate(zip(record.person_bboxes, record.person_pose_keypoints)):
        try:
            box, pose = np.asarray(box, dtype=float), np.asarray(pose, dtype=float)
        except (TypeError, ValueError):
            return None, 'malformed_geometry'
        if (box.shape != (4,) or pose.shape != (17, 3)
                or not np.isfinite(box).all() or not np.isfinite(pose).all()
                or (box[2:] <= box[:2]).any()):
            return None, 'malformed_geometry'
        visible = ((pose[:, 2] >= .5)
                   & (pose[:, 0] >= max(0, box[0])) & (pose[:, 0] < min(width, box[2]))
                   & (pose[:, 1] >= max(0, box[1])) & (pose[:, 1] < min(height, box[3])))
        # An observed large partial body is contrary framing evidence even
        # when its head/torso cannot qualify as one of the group witnesses.
        if visible.any() and box[3] - box[1] > 2 * height / 3:
            return None, 'observed_large_foreground'
        head = np.flatnonzero(visible[:5])
        head_xy = pose[:5, :2][visible[:5]]
        head_span = float(np.linalg.norm(np.ptp(head_xy, axis=0))) if len(head_xy) >= 2 else 0.
        torso = [5, 6, 11, 12]
        length = float(np.linalg.norm(pose[[5, 6], :2].mean(axis=0)
                                      - pose[[11, 12], :2].mean(axis=0)))
        # Positive membership needs a complete directly observed facial core.
        # Complementary two-point hypotheses cannot prove distinct heads.
        reliable = bool(visible[:3].all() and head_span > 0 and visible[torso].all()
                        and (pose[torso, 2] >= .75).all() and length >= 4
                        and pose[head, 1].max() < pose[[5, 6], 1].mean()
                        < pose[[11, 12], 1].mean())
        full = bool(reliable and visible[[15, 16]].all()
                    and pose[[11, 12], 1].mean() < pose[[15, 16], 1].mean())
        xy = pose[torso, :2]
        # Retain all observations as matching competitors. A weak observation
        # can make ownership ambiguous but cannot become a positive witness.
        features.append(dict(index=index, pose_keypoints=pose, reliable=reliable,
                             full=full, length=length, head_visible=visible[:5], head_span=head_span,
                             torso_rect=np.r_[xy.min(axis=0), xy.max(axis=0)]))
    # A shared observed head is one owner even when detector hypotheses
    # attach disjoint torsos or legs to it. Partial competing bodies count
    # as ambiguity too; they need not qualify as positive group witnesses.
    for a, b in combinations(features, 2):
        if _shared_head(a, b):
            a['reliable'] = a['full'] = b['reliable'] = b['full'] = False
    reliable = [f for f in features if f['reliable']]
    if len(reliable) < 3:
        return None, 'fewer_than_three_observed_members'
    lengths = [f['length'] for f in reliable]
    if max(lengths) > 1.4 * float(np.median(lengths)):
        return None, 'observed_size_dominance'
    return dict(features=features), None


def _independent(members):
    for a, b in combinations(members, 2):
        left_head = a['pose_keypoints'][:5, :2][a['head_visible']]
        right_head = b['pose_keypoints'][:5, :2][b['head_visible']]
        # Prove spatial separation of observed head regions, rather than
        # treating failure to detect duplicate ownership as independence.
        separation = np.linalg.norm(left_head[:, None] - right_head[None, :], axis=2).min()
        if separation <= max(a['head_span'], b['head_span']):
            return False
        left, right = a['torso_rect'], b['torso_rect']
        area = min(float(np.prod(left[2:] - left[:2])), float(np.prod(right[2:] - right[:2])))
        overlap = float(np.prod(np.maximum(0, np.minimum(left[2:], right[2:])
                                            - np.maximum(left[:2], right[:2]))))
        if area <= 0 or overlap >= .5 * area:
            return False
    return True


def _observed_paths(records, video_size):
    measured = []
    for record in records:
        row, reason = _members(record, video_size)
        if row is None:
            return None, reason
        measured.append(row)
    paths = []
    for anchor in measured[0]['features']:
        if not anchor['full']:
            continue
        path = [anchor]
        for previous, current in zip(measured, measured[1:]):
            found = strict_pose_corresponding(previous, path[-1], current)
            if (found is None or not found['reliable']
                    or not 1 / 1.4 <= found['length'] / path[-1]['length'] <= 1.4):
                break
            path.append(found)
        if len(path) == len(records) and path[-1]['full']:
            paths.append(path)
    for witnesses in combinations(paths, 3):
        if all(_independent([path[i] for path in witnesses]) for i in range(len(records))):
            return [[person['index'] for person in path] for path in witnesses], None
    return None, 'fewer_than_three_reciprocal_paths'


def stabilize_group_segments(records, groups, *, video_size, fps, sample_step,
                             cut_frames, source_path, exclusive_foreground_frames=()):
    """Return group segments and proof audit; keep every input record unchanged.

    Call after final scene/context classification and before presentation-only
    group-card filtering. Source reads are restricted to gaps already supported
    by three observed paths. Any source error rolls back all proposed joins.
    A main handoff/name is not evidence that group membership disappeared.
    """
    started = time.perf_counter()
    audit = dict(version=VERSION, reason='complete', bridges=[], rejected=[],
                 source_reads=dict(reads=0, seeks=0, grabs=0, cache_hits=0, decode_seconds=0.))
    def finish(result, reason='complete'):
        audit.update(reason=reason, seconds=time.perf_counter() - started)
        return result, audit
    if cut_frames is None:
        return finish(groups, 'missing_cut_inventory')
    if (not math.isfinite(fps) or fps <= 0 or sample_step < 1
            or len(video_size) != 2 or min(video_size) <= 0):
        return finish(groups, 'invalid_source_cadence')
    if len(groups) < 2 or len(records) < 3:
        return finish(groups)
    times = [r.t for r in records]
    if any(not math.isfinite(t) for t in times) or any(b <= a for a, b in zip(times, times[1:])):
        return finish(groups, 'invalid_observation_times')
    if any(g.seg_type != 'group' or not math.isfinite(g.start) or not math.isfinite(g.end)
           or g.end <= g.start for g in groups):
        return finish(groups, 'invalid_group_segments')
    ordered = sorted(groups, key=lambda g: (g.start, g.end))
    frames = [round(t * fps) for t in times]
    cuts = sorted(set(cut_frames))
    exclusive = set(exclusive_foreground_frames)
    joins = set()
    reader = None
    try:
        for index, (left, right) in enumerate(zip(ordered, ordered[1:])):
            if right.start <= left.end:
                continue
            lower = bisect_left(times, left.end - 1e-8) - 1
            upper = bisect_left(times, right.start - 1e-8)
            report = dict(start=left.end, end=right.start)
            def reject(reason, **details):
                audit['rejected'].append(dict(report, reason=reason, **details))
            if lower < 0 or upper >= len(records) or upper - lower < 2:
                reject('unbounded_observations')
                continue
            first, last = frames[lower], frames[upper]
            cut_hits = [cut for cut in cuts if first < cut <= last]
            if cut_hits:
                reject('source_cut_inventory', cut_frames=cut_hits)
                continue
            if any(frames[i] - frames[i - 1] != sample_step for i in range(lower + 1, upper + 1)):
                reject('missing_source_sample')
                continue
            if exclusive.intersection(frames[lower:upper + 1]):
                reject('existing_exclusive_foreground_proof')
                continue
            if not records[lower].is_group or not records[upper].is_group:
                reject('unconfirmed_group_anchor')
                continue
            paths, reason = _observed_paths(records[lower:upper + 1], video_size)
            if paths is None:
                reject(reason)
                continue
            if reader is None:
                reader = SourceFrameReader(source_path, fps)
            previous = reader.get(first)
            if previous.shape[:2] != (video_size[1], video_size[0]):
                raise ValueError('source_size_mismatch')
            transition = None
            for frame in range(first + 1, last + 1):
                current = reader.get(frame)
                if current.shape != previous.shape:
                    raise ValueError('source_size_mismatch')
                color = bool(_color_cut(cv2.resize(previous, (64, 36)), cv2.resize(current, (64, 36)))[0])
                spatial = bool(spatial_cut_candidate(previous, current))
                if color or spatial:
                    transition = dict(frame=frame, color_candidate=color, spatial_candidate=spatial)
                    break
                previous = current
            if transition:
                reject('source_transition', **transition)
                continue
            joins.add(index)
            audit['bridges'].append(dict(report, frames=frames[lower:upper + 1], paths=paths,
                                         anchor_frames=[first, last],
                                         source_frames_checked=[first, last]))
    except (OSError, ValueError, RuntimeError, cv2.error) as error:
        audit.update(bridges=[], error_type=type(error).__name__)
        return finish(groups, 'source_unavailable')
    finally:
        if reader is not None:
            audit['source_reads'] = dict(reader.stats)
            reader.close()
    if not joins:
        return finish(groups)
    result = [ordered[0]]
    for index, segment in enumerate(ordered[1:]):
        if index in joins:
            result[-1] = replace(result[-1], end=segment.end,
                                 bboxes=[*result[-1].bboxes, *segment.bboxes])
        else:
            result.append(segment)
    return finish(result)
