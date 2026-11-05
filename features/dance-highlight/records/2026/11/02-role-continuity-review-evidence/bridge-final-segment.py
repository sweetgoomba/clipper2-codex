from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Dict, List, Optional, Tuple
import math
import numpy as np

from .track import bbox_iou


def center_score(keypoints: np.ndarray, frame_w: int) -> float:
    sx = (float(keypoints[5][0]) + float(keypoints[6][0])) / 2
    hx = (float(keypoints[11][0]) + float(keypoints[12][0])) / 2
    cx = (sx + hx) / 2
    return float(max(0.0, 1.0 - abs(cx - frame_w / 2) / (frame_w / 2)))


def scale_score(bbox: np.ndarray, frame_area: float) -> float:
    x1, y1, x2, y2 = [float(v) for v in bbox.tolist()]
    area = max(1.0, (x2 - x1) * (y2 - y1))
    return float(min(1.0, area / float(frame_area)))


def pose_energy_score(keypoints: np.ndarray) -> float:
    pairs = [(5, 7), (7, 9), (6, 8), (8, 10), (5, 6), (11, 12)]
    e = 0.0
    for a, b in pairs:
        e += float(np.linalg.norm(keypoints[a] - keypoints[b]))
    return float(e)


def main_score(p: dict, w: int, h: int) -> float:
    return float(
        0.45 * center_score(p["keypoints"], w) +
        0.35 * scale_score(p["bbox"], w * h) +
        # Retain the existing 1080p calibration in relative frame units.
        # Raw pixel limb lengths must not change ranking when a video is resized.
        0.20 * (pose_energy_score(p["keypoints"]) / (300.0 * h / 1080.0))
    )


class MainSelector:
    def __init__(self, fps: float = 30.0, group_fps: Optional[float] = None):
        self.main_bbox = None
        self.main_score_ref = None
        self.main_area_ref = None

        self.cand_bbox = None
        self.cand_score = None
        self.cand_since = None
        self._fps = max(1., float(fps))
        self._time_seconds = -1. / self._fps
        self.CANDIDATE_MARGIN = 0.06
        self.HARD_SWITCH_MARGIN = 0.16

        self.group_state = False
        self.group_enter_cnt = 0
        self.group_exit_cnt = 0
        group_rate = fps if group_fps is None else group_fps
        self.GROUP_ENTER_FRAMES = max(3, int(group_rate * 0.35))
        self.GROUP_EXIT_FRAMES = max(3, int(group_rate * 0.25))
        self.last_group_member_bboxes: List[np.ndarray] = []
        self.last_group_candidate = False
        self.last_group_score_gap: Optional[float] = None
        self.last_group_area_ratio: Optional[float] = None

    def group_member_boxes(self, scored, areas) -> List[np.ndarray]:
        """단체 장면에서 충분히 두드러진 참여자의 몸 박스만 남긴다."""
        if len(scored) < 2:
            return []
        min_score = float(scored[1][0]) - 0.12
        min_area = min(areas[:2]) / 2.0
        return [
            np.asarray(person["bbox"], dtype=np.float32)
            for (score, person), area in zip(scored, areas, strict=True)
            if float(score) >= min_score and area >= min_area
        ]

    def group_candidate_now(self, scored, areas):
        if len(scored) < 2:
            return False

        s0, _ = scored[0]
        s1, _ = scored[1]

        if (s0 - s1) > 0.10:
            return False

        ar = (max(areas) / (min(areas) + 1e-6))
        if ar > 1.9:
            return False

        return True

    def update_group_state(self, is_group_candidate):
        if not self.group_state:
            if is_group_candidate:
                self.group_enter_cnt += 1
                if self.group_enter_cnt >= self.GROUP_ENTER_FRAMES:
                    self.group_state = True
                    self.group_exit_cnt = 0
            else:
                self.group_enter_cnt = 0
        else:
            if not is_group_candidate:
                self.group_exit_cnt += 1
                if self.group_exit_cnt >= self.GROUP_EXIT_FRAMES:
                    self.group_state = False
                    self.group_enter_cnt = 0
            else:
                self.group_exit_cnt = 0

    def select(self, persons, frame_shape, *, time_seconds=None):
        now = self._time_seconds + 1. / self._fps if time_seconds is None else float(time_seconds)
        if now < self._time_seconds:
            self.cand_since = None
            self.cand_bbox = None
        self._time_seconds = now
        h, w = frame_shape[:2]
        if not persons:
            self.main_bbox = None
            self.main_score_ref = None
            self.main_area_ref = None
            self.cand_bbox = None
            self.cand_since = None
            self.last_group_member_bboxes = []
            self.last_group_candidate = False
            self.last_group_score_gap = None
            self.last_group_area_ratio = None
            return None, False

        scored = [(main_score(p, w, h), p) for p in persons]
        scored.sort(key=lambda x: x[0], reverse=True)

        best_score, best_person = scored[0]

        areas = []
        for _, p in scored:
            x1, y1, x2, y2 = p["bbox"]
            areas.append(max(1.0, float((x2 - x1) * (y2 - y1))))

        is_group_candidate = self.group_candidate_now(scored, areas)
        self.last_group_candidate = is_group_candidate
        self.last_group_score_gap = float(scored[0][0] - scored[1][0]) if len(scored) >= 2 else None
        self.last_group_area_ratio = float(max(areas) / (min(areas) + 1e-6)) if len(areas) >= 2 else None
        self.update_group_state(is_group_candidate)
        self.last_group_member_bboxes = self.group_member_boxes(scored, areas) if self.group_state else []

        if self.main_bbox is None:
            self.main_bbox = best_person["bbox"]
            self.main_score_ref = float(best_score)
            self.main_area_ref = max(1.0, float((self.main_bbox[2] - self.main_bbox[0]) * (self.main_bbox[3] - self.main_bbox[1])))
            return best_person, self.group_state

        follow_p = max(persons, key=lambda p: bbox_iou(self.main_bbox, p["bbox"]))
        follow_iou = bbox_iou(self.main_bbox, follow_p["bbox"])
        if follow_iou <= 0.10:
            # No current detection follows the old body. An arbitrary IoU tie
            # must not become the incumbent while the best person waits.
            self.main_bbox = best_person["bbox"]
            self.main_score_ref = float(best_score)
            self.main_area_ref = max(1.0, float((self.main_bbox[2] - self.main_bbox[0]) * (self.main_bbox[3] - self.main_bbox[1])))
            self.cand_since = None
            self.cand_bbox = None
            return best_person, self.group_state

        follow_score = main_score(follow_p, w, h)

        curr_area = max(1.0, float((follow_p["bbox"][2] - follow_p["bbox"][0]) * (follow_p["bbox"][3] - follow_p["bbox"][1])))
        area_ratio = curr_area / (float(self.main_area_ref) + 1e-6)

        weak_main = (
            follow_iou < 0.12 or
            area_ratio < 0.78 or
            (follow_score < (float(self.main_score_ref) * 0.86))
        )

        switch_seconds = .10 if weak_main else .25

        self.main_bbox = follow_p["bbox"]
        self.main_score_ref = 0.80 * float(self.main_score_ref) + 0.20 * float(follow_score)
        self.main_area_ref = float(curr_area)

        if best_score > float(follow_score) * (1 + self.HARD_SWITCH_MARGIN):
            self.main_bbox = best_person["bbox"]
            self.main_score_ref = float(best_score)
            self.main_area_ref = max(1.0, float((self.main_bbox[2] - self.main_bbox[0]) * (self.main_bbox[3] - self.main_bbox[1])))
            self.cand_since = None
            self.cand_bbox = None
            return best_person, self.group_state

        if best_score > float(follow_score) * (1 + self.CANDIDATE_MARGIN) or weak_main:
            if self.cand_bbox is None or bbox_iou(self.cand_bbox, best_person["bbox"]) <= 0.35:
                self.cand_since = now

            self.cand_bbox = best_person["bbox"]
            self.cand_score = float(best_score)
        else:
            self.cand_since = None
            self.cand_bbox = None

        if self.cand_since is not None and now - self.cand_since >= switch_seconds - 1e-9:
            self.main_bbox = self.cand_bbox
            self.main_score_ref = float(self.cand_score)
            self.main_area_ref = max(1.0, float((self.main_bbox[2] - self.main_bbox[0]) * (self.main_bbox[3] - self.main_bbox[1])))
            self.cand_since = None
            self.cand_bbox = None

        final = max(persons, key=lambda p: bbox_iou(self.main_bbox, p["bbox"]))
        return final, self.group_state


@dataclass
class FrameRec:
    t: float
    main_id: Optional[int]
    main_bbox: Optional[np.ndarray]
    is_group: bool
    group_bboxes: List[np.ndarray] = field(default_factory=list)
    person_bboxes: List[np.ndarray] = field(default_factory=list)
    face_bboxes: List[np.ndarray] = field(default_factory=list)
    group_candidate: bool = False
    group_score_gap: Optional[float] = None
    group_area_ratio: Optional[float] = None
    person_head_keypoints: List[np.ndarray] = field(default_factory=list)
    scene_kind: str = "unclassified"
    scene_reason: Optional[str] = None
    candidate_main_id: Optional[int] = None
    candidate_main_bbox: Optional[np.ndarray] = None
    person_pose_keypoints: List[np.ndarray] = field(default_factory=list)


def _observed_body_joints(body, pose, video_size):
    width, height = video_size
    visible = np.isfinite(pose).all(axis=1) & (pose[:, 2] >= .5)
    visible &= (pose[:, 0] >= 0) & (pose[:, 0] < width) & (pose[:, 1] >= 0) & (pose[:, 1] < height)
    inside = ((pose[:, 0] >= body[0]) & (pose[:, 0] <= body[2]) &
              (pose[:, 1] >= body[1]) & (pose[:, 1] <= body[3]))
    head_visible = (visible[:5] & inside[:5]).sum() >= 2
    torso_indices = [5, 6, 11, 12]
    torso = pose[torso_indices]
    torso_visible = (visible[torso_indices] & inside[torso_indices]).all()
    torso_reliable = (torso_visible and (torso[:, 2] >= .75).all()
                      and torso[:2, 1].mean() < torso[2:, 1].mean())
    return visible, inside, head_visible, torso_visible, torso_reliable


def distributed_full_body_ensemble(rec: FrameRec, video_size: Tuple[int, int], *, allow_compact=False) -> bool:
    """A spread or distant formation of fully observed performers.

    Reliable heads filter stage-art detections. A large partial foreground
    person still vetoes group classification even if their feet are cropped.
    """
    width, height = video_size
    if len(rec.person_bboxes) != len(rec.person_pose_keypoints):
        return False
    trusted, complete, measured_torsos, person_extents, complete_extents = [], [], [], [], []
    for body, pose in zip(rec.person_bboxes, rec.person_pose_keypoints, strict=True):
        body, pose = np.asarray(body), np.asarray(pose)
        if body.shape != (4,) or pose.shape != (17, 3) or not np.isfinite(body).all():
            continue
        if body[2] <= body[0] or body[3] <= body[1]:
            continue
        visible, inside, head_visible, torso_visible, torso_reliable = _observed_body_joints(
            body, pose, video_size)
        if not head_visible and not torso_reliable:
            continue
        trusted.append(body)
        person_extents.append(float(body[3]-body[1]))
        if not head_visible or not torso_visible or not visible[[15, 16]].all():
            continue
        shoulder, hip, ankle = [float(pose[j, 1].mean()) for j in ([5, 6], [11, 12], [15, 16])]
        head_y = pose[:5, 1][visible[:5] & inside[:5]]
        if shoulder < hip < ankle:
            # Broad overlapping detector boxes may repeat one measured person.
            # Count distinct torso evidence, not detector rows or arm extent.
            torso = pose[[5, 6, 11, 12]]
            rect = np.r_[torso[:, :2].min(axis=0), torso[:, :2].max(axis=0)]
            area = float(np.prod(rect[2:] - rect[:2]))
            if area <= 0:
                continue
            measured_torsos.append(rect)
            complete.append(body)
            if head_y.max() < shoulder and inside[[15, 16]].all():
                person_extents[-1] = float(pose[[15, 16], 1].max() - head_y.min())
            complete_extents.append(person_extents[-1])
    # Treat each connected overlap component as one uncertain physical body.
    # Retain every rectangle when finding components so row order cannot turn
    # a chain of duplicate measurements into several people.
    remaining = set(range(len(complete)))
    distinct = []
    distinct_extents = []
    while remaining:
        component = {remaining.pop()}
        pending = list(component)
        while pending:
            rect = measured_torsos[pending.pop()]
            area = float(np.prod(rect[2:] - rect[:2]))
            for index in sorted(remaining):
                other = measured_torsos[index]
                overlap = float(np.prod(np.maximum(0., np.minimum(rect[2:], other[2:])
                                                    - np.maximum(rect[:2], other[:2]))))
                if overlap >= .5 * min(area, float(np.prod(other[2:] - other[:2]))):
                    remaining.remove(index)
                    component.add(index)
                    pending.append(index)
        distinct.append(min((complete[i] for i in component),
                            key=lambda b: (float(np.prod(b[2:] - b[:2])), tuple(b))))
        distinct_extents.append(min(complete_extents[i] for i in component))
    complete = distinct
    if len(complete) < 3:
        return False
    largest = max(float(b[3]-b[1]) for b in trusted)
    typical = float(np.median([b[3]-b[1] for b in complete]))
    spread = (max(b[2] for b in complete)-min(b[0] for b in complete)) / max(1, width)
    spread_formation = largest <= 2*height/3. and largest <= 1.4*typical and spread >= .5
    # Box padding and outstretched clothing can enlarge a distant performer.
    # Measure head-to-ankle span only for a fully observed person; otherwise
    # keep their entire box as a conservative size bound. A larger incomplete
    # foreground body still vetoes this path, including when its head is hidden.
    # A distant formation can be tightly clustered in the center. Horizontal
    # spread is not solo evidence: retain the three distinct full-body proofs
    # and conservative scale/foreground guards without that layout restriction.
    distant_formation = (max(person_extents) <= height/3.
                         and max(person_extents) <= 1.4*float(np.median(distinct_extents))
                         and largest <= 2*height/3. and (spread >= .3 or allow_compact))
    return spread_formation or distant_formation


def _observed_central_torso(rec, video_size):
    """A possible central subject vetoes NEW compact-group exclusion only.

    This does not identify a member or prove a main. Incomplete head/feet do
    not remove the veto when the torso itself is measured inside its body.
    """
    width, height = video_size
    for box, pose in zip(rec.person_bboxes, rec.person_pose_keypoints):
        box, pose = np.asarray(box), np.asarray(pose)
        if box.shape != (4,) or pose.shape != (17, 3):
            continue
        torso = pose[[5, 6, 11, 12]]
        if (np.isfinite(torso).all() and (torso[:, 2] >= .5).all()
                and (torso[:, 0] >= max(0., box[0])).all()
                and (torso[:, 0] <= min(width-1., box[2])).all()
                and (torso[:, 1] >= max(0., box[1])).all()
                and (torso[:, 1] <= min(height-1., box[3])).all()
                and torso[:, 0].min() <= width/2 <= torso[:, 0].max()):
            return True
    return False


def _compact_ensemble_runs(recs, distributed, video_size, max_step):
    candidates = [not wide and distributed_full_body_ensemble(r, video_size, allow_compact=True)
                  for r, wide in zip(recs, distributed, strict=True)]
    # Role context is measured independently of the group candidate. A missed
    # ankle must not split a sustained central subject into one-frame votes.
    central = [_observed_central_torso(r, video_size) for r in recs]
    protected = set()
    i = 0
    while i < len(recs):
        if not central[i]:
            i += 1
            continue
        start = i
        i += 1
        while i < len(recs) and central[i] and recs[i].t-recs[i-1].t <= max_step+1e-6:
            i += 1
        if recs[i-1].t-recs[start].t >= .15-1e-9:
            protected.update(range(start, i))
    i = 0
    while i < len(recs):
        if not candidates[i]:
            i += 1
            continue
        start = i
        i += 1
        while i < len(recs) and candidates[i] and recs[i].t-recs[i-1].t <= max_step+1e-6:
            i += 1
        if any(j in protected for j in range(start, i)):
            candidates[start:i] = [False]*(i-start)
    return candidates, protected


def _accept_group_candidates(recs, candidates, small_people, max_step, compact, protected_central):
    # A brief pose dropout during a wide shot must not invent a solo. Never
    # bridge a closeup, an empty frame, a sampling gap or an unbounded interval.
    bounded = candidates.copy()
    def seen_in_formation(box, boundaries):
        for boundary in boundaries:
            for other in boundary.person_bboxes:
                if bbox_iou(box, other) >= .3:
                    return True
                # Pose detectors may retain only part of an occluded body.
                area = max(1., float((box[2]-box[0])*(box[3]-box[1])))
                intersection = max(0., min(box[2],other[2])-max(box[0],other[0])) * max(
                    0., min(box[3],other[3])-max(box[1],other[1]))
                if intersection / area >= .8:
                    return True
        return False

    i = 0
    while i < len(recs):
        if candidates[i]:
            i += 1
            continue
        start = i
        while i < len(recs) and not candidates[i]:
            i += 1
        if (start > 0 and i < len(recs)
                # New compact endpoints cannot use gap filling to erase a
                # central subject that explicitly vetoed group exclusion.
                and (not (compact[start-1] or compact[i])
                     or not any(j in protected_central for j in range(start, i)))
                and recs[i].t - recs[start].t <= .600001
                and all(recs[j].t - recs[j - 1].t <= max_step + 1e-6 for j in range(start, i + 1))
                and all(small_people[start:i])
                and all(
                    seen_in_formation(max(record.person_bboxes, key=lambda box: float(box[3]-box[1])),
                                      (recs[start - 1], recs[i]))
                    for record in recs[start:i])):
            bounded[start:i] = [True] * (i - start)

    accepted = [False] * len(recs)
    i = 0
    while i < len(recs):
        if not bounded[i]:
            i += 1
            continue
        start = i
        i += 1
        while i < len(recs) and bounded[i] and recs[i].t - recs[i - 1].t <= max_step + 1e-6:
            i += 1
        # Backdate a confirmed run so debounce does not leak solo frames at cuts.
        if recs[i - 1].t - recs[start].t >= .15 - 1e-9:
            accepted[start:i] = [True] * (i - start)

    return accepted


def classify_main_scenes(recs: List[FrameRec], video_size: Tuple[int, int]) -> List[FrameRec]:
    """Separate sustained wide ensembles from tentative solo selections.

    This gate uses composition before recognition. Unknown faces are never a
    reason to discard a main. Compact center formations and closeups remain
    eligible; the old soft group score alone cannot veto them.
    """
    width, height = video_size
    intervals = [b.t-a.t for a,b in zip(recs,recs[1:]) if b.t > a.t]
    max_step = max(.2, 1.5 * float(np.median(intervals))) if intervals else .2
    candidates, small_people, distributed = [], [], []
    for rec in recs:
        spread_ensemble = distributed_full_body_ensemble(rec, video_size)
        distributed.append(spread_ensemble)
        boxes = np.asarray(rec.person_bboxes, dtype=np.float32).reshape(-1, 4)
        if len(boxes):
            heights = boxes[:, 3] - boxes[:, 1]
            largest = float(max(heights))
            # Ignore tiny background detections when measuring the formation.
            peers = boxes[heights >= .6 * largest]
            spread = float(max(peers[:, 2]) - min(peers[:, 0])) / max(1, width)
            small = 0 < largest <= height / 3.
            candidates.append((small and len(peers) >= 2 and spread >= .30) or spread_ensemble)
            small_people.append(small)
        else:
            candidates.append(False)
            small_people.append(False)

    confirmed = _accept_group_candidates(recs, candidates, small_people, max_step,
                                         [False]*len(recs), set())
    compact, protected_central = _compact_ensemble_runs(recs, distributed, video_size, max_step)
    # Vetoes govern newly added evidence, never the pre-existing wide gate.
    compact = [added and not base for base, added in zip(candidates, compact, strict=True)]
    candidates = [base or added for base, added in zip(candidates, compact, strict=True)]

    proposed = _accept_group_candidates(recs, candidates, small_people, max_step,
                                        compact, protected_central)
    # New compact evidence can extend an established group episode, but cannot
    # invent a standalone group island and fragment an otherwise continuous
    # performance. The anchor is the ORIGINAL completed group mask, including
    # its debounce; raw per-frame candidate votes are not sufficient.
    accepted = confirmed.copy()
    i = 0
    while i < len(recs):
        if not proposed[i]:
            i += 1
            continue
        start = i
        i += 1
        while i < len(recs) and proposed[i] and recs[i].t-recs[i-1].t <= max_step+1e-6:
            i += 1
        if any(confirmed[start:i]):
            accepted[start:i] = [True]*(i-start)

    result = []
    for rec, group, spread_ensemble, compact_ensemble in zip(recs, accepted, distributed, compact, strict=True):
        rec = replace(rec, candidate_main_id=rec.main_id, candidate_main_bbox=rec.main_bbox)
        if group:
            result.append(replace(rec, main_id=None, main_bbox=None, is_group=True,
                                  group_bboxes=list(rec.person_bboxes), scene_kind="group",
                                  scene_reason=("distributed_full_body_ensemble" if spread_ensemble else
                                                "compact_distant_ensemble" if compact_ensemble else "sustained_wide_ensemble")))
        elif rec.main_id is None or rec.main_bbox is None:
            result.append(replace(rec, is_group=False, group_bboxes=[], scene_kind="no_person",
                                  scene_reason="no_selected_body"))
        else:
            result.append(replace(rec, scene_kind="main", scene_reason="main_eligible_composition"))
    return result


def bridge_compact_group_gaps(recs, *, video_size, fps, sample_step,
                              cut_frames, handoffs, camera_episodes):
    """Bridge only observed dropouts beside the new compact group extension.

    Both sides must already be groups. Every intervening body must have a
    unique, scale-stable counterpart in the immediately adjacent confirmed
    group frame on each side. Native group bodies use the native evidence;
    raw stage-art boxes cannot serve as confirmed person anchors. Source
    cuts, possible focal subjects and known role changes veto the bridge.
    This never supplies identity evidence or performs model inference.
    """
    audit = dict(version='compact_group_gap_v1', bridges=[])
    if cut_frames is None or handoffs is None or camera_episodes is None:
        return recs, dict(audit, reason='missing_source_role_inventory')
    if not math.isfinite(fps) or fps <= 0 or sample_step < 1:
        return recs, dict(audit, reason='invalid_source_cadence')
    frames = [round(r.t*fps) for r in recs]
    def uninterrupted(a,b):
        return all(frames[j]-frames[j-1]==sample_step for j in range(a+1,b+1))
    def blocked(a,b):
        return (any(frames[a] < f <= frames[b] for f in cut_frames)
                or any(recs[a].t < h['time'] <= recs[b].t for h in handoffs)
                or any(p['start_frame'] <= frames[b] and p['end_frame'] >= frames[a]
                       for p in camera_episodes))
    def observed_boxes(record):
        if len(record.person_bboxes) != len(record.person_pose_keypoints):
            return None
        boxes=[]
        for box,pose in zip(record.person_bboxes,record.person_pose_keypoints,strict=True):
            box,pose=np.asarray(box),np.asarray(pose)
            if (box.shape!=(4,) or pose.shape!=(17,3) or not np.isfinite(box).all()
                    or not np.isfinite(pose).all() or (box[2:]<=box[:2]).any()):
                return None
            _,_,head,_,torso=_observed_body_joints(box,pose,video_size)
            if head or torso:
                boxes.append(box)
        return boxes
    def anchor_boxes(record):
        if record.scene_reason=='native_distant_ensemble':
            # These are the measured native bodies that actually proved group,
            # not the regular detector's boxes (which can contain stage art).
            return record.group_bboxes or None
        return observed_boxes(record)
    def correspond(boxes,anchors):
        if boxes is None or len(boxes)<2 or anchors is None:
            return False
        assigned=[]
        for box in boxes:
            options=[i for i,other in enumerate(anchors)
                if np.asarray(other).shape==(4,) and np.isfinite(other).all()
                and (other[2:] > other[:2]).all() and bbox_iou(box,other) >= .3
                and 1/1.4 <= (box[3]-box[1])/(other[3]-other[1]) <= 1.4]
            if len(options)!=1:
                return False
            assigned.append(options[0])
        return len(set(assigned))==len(assigned)
    output=list(recs)
    i=0
    while i<len(recs):
        if recs[i].scene_kind=='group':
            i+=1
            continue
        start=i
        while i<len(recs) and recs[i].scene_kind!='group':
            i+=1
        if not (0 < start < i < len(recs) and recs[i].t-recs[start].t <= .600001
                and any(recs[j].scene_reason=='compact_distant_ensemble' for j in (start-1,i))
                and uninterrupted(start-1,i) and not blocked(start-1,i)
                and all(r.scene_kind=='main' and r.scene_reason=='main_eligible_composition'
                        and not _observed_central_torso(r,video_size) for r in recs[start:i])):
            continue
        left,right=anchor_boxes(recs[start-1]),anchor_boxes(recs[i])
        gap_boxes=[observed_boxes(r) for r in recs[start:i]]
        if any(boxes is None or any(box[3]-box[1] > video_size[1]/3
               or box[0] <= 0 or box[1] <= 0 or box[2] >= video_size[0] or box[3] >= video_size[1]
               for box in boxes) for boxes in gap_boxes):
            continue
        if not all(correspond(boxes,left) and correspond(boxes,right) for boxes in gap_boxes):
            continue
        for j in range(start,i):
            output[j]=replace(recs[j],main_id=None,main_bbox=None,is_group=True,
                group_bboxes=gap_boxes[j-start],scene_kind='group',
                scene_reason='compact_group_observation_bridge')
        audit['bridges'].append(dict(start=recs[start].t,end=recs[i].t,
            frames=frames[start:i],left_anchor_frame=frames[start-1],right_anchor_frame=frames[i],
            anchor_sources=[recs[start-1].scene_reason,recs[i].scene_reason],
            observed_body_counts=[len(boxes) for boxes in gap_boxes],
            unobserved_box_counts=[len(recs[j].person_bboxes)-len(gap_boxes[j-start])
                                   for j in range(start,i)],
            reason='bidirectional_observed_ensemble'))
    return output,dict(audit,reason='complete')


@dataclass
class Segment:
    seg_type: str
    label: Optional[int]
    start: float
    end: float
    bboxes: List[Tuple[float, np.ndarray, int]]  # 🔥 track_id 추가


def build_raw_main_segments(recs: List[FrameRec]) -> List[Segment]:
    segs: List[Segment] = []

    cur_id: Optional[int] = None
    cur_start: Optional[float] = None
    cur_bboxes: List[Tuple[float, np.ndarray, int]] = []
    last_t: Optional[float] = None

    for r in recs:
        # main이 없는 프레임
        if r.main_id is None or r.main_bbox is None:
            if cur_id is not None and cur_start is not None and last_t is not None:
                segs.append(
                    Segment(
                        seg_type="main",
                        label=int(cur_id),
                        start=float(cur_start),
                        end=float(r.t),
                        bboxes=cur_bboxes,
                    )
                )
            cur_id = None
            cur_start = None
            cur_bboxes = []
            last_t = float(r.t)
            continue

        # 새로운 세그먼트 시작
        if cur_id is None:
            cur_id = int(r.main_id)
            cur_start = float(r.t)
            cur_bboxes = [
                (float(r.t), r.main_bbox, int(r.main_id))
            ]
        else:
            # track_id 변경 → 세그먼트 종료 후 새로 시작
            if int(r.main_id) != int(cur_id):
                segs.append(
                    Segment(
                        seg_type="main",
                        label=int(cur_id),
                        start=float(cur_start),
                        end=float(r.t),
                        bboxes=cur_bboxes,
                    )
                )
                cur_id = int(r.main_id)
                cur_start = float(r.t)
                cur_bboxes = [
                    (float(r.t), r.main_bbox, int(r.main_id))
                ]
            else:
                # 동일 track → 계속 누적
                cur_bboxes.append(
                    (float(r.t), r.main_bbox, int(r.main_id))
                )

        last_t = float(r.t)

    # 마지막 세그먼트 정리
    if cur_id is not None and cur_start is not None and last_t is not None:
        segs.append(
            Segment(
                seg_type="main",
                label=int(cur_id),
                start=float(cur_start),
                end=float(last_t),
                bboxes=cur_bboxes,
            )
        )

    return segs

def build_main_evidence_scopes(raw_segments: List[Segment]) -> List[Segment]:
    """Collect continuous observations for identity analysis, not final clips.

    Body changes remain in every bbox row. No short run is absorbed into an
    adjacent identity and no unobserved time gap is filled.
    """
    scopes: List[Segment] = []
    for segment in sorted(raw_segments, key=lambda s: s.start):
        if segment.end <= segment.start:
            continue
        if scopes and abs(scopes[-1].end - segment.start) <= 1e-6:
            scopes[-1].end = segment.end
            scopes[-1].bboxes.extend(segment.bboxes)
        else:
            scopes.append(replace(segment, label=None, bboxes=list(segment.bboxes)))
    return scopes


def build_raw_group_segments(recs: List[FrameRec]) -> List[Segment]:
    segs: List[Segment] = []
    on = False
    start = None
    last_t = None

    for r in recs:
        if r.is_group and not on:
            on = True
            start = float(r.t)
        elif (not r.is_group) and on:
            on = False
            if start is not None:
                segs.append(Segment("group", None, float(start), float(r.t), []))
            start = None
        last_t = float(r.t)

    if on and start is not None and last_t is not None:
        segs.append(Segment("group", None, float(start), float(last_t), []))

    return segs


def merge_close_segments(segs: List[Segment], gap_sec: float) -> List[Segment]:
    if not segs:
        return segs
    segs = sorted(segs, key=lambda s: s.start)
    out = [segs[0]]
    for s in segs[1:]:
        prev = out[-1]
        if prev.seg_type == s.seg_type and prev.label == s.label and (s.start - prev.end) <= float(gap_sec):
            prev.end = max(prev.end, s.end)
            if prev.seg_type == "main":
                prev.bboxes.extend(s.bboxes)
        else:
            out.append(s)
    return out


def smooth_main_segments(
    segs: List[Segment],
    min_main_seg_sec: float,
    bridge_gap_sec: float,
    merge_gap_sec: float,
) -> List[Segment]:
    if not segs:
        return segs

    segs = sorted(segs, key=lambda s: s.start)

    changed = True
    while changed:
        changed = False
        new_segs: List[Segment] = []
        i = 0
        while i < len(segs):
            s = segs[i]
            dur = float(s.end - s.start)
            if dur >= float(min_main_seg_sec):
                new_segs.append(s)
                i += 1
                continue

            prev = new_segs[-1] if new_segs else None
            nxt = segs[i + 1] if (i + 1) < len(segs) else None

            if prev and nxt and prev.label == nxt.label:
                prev.end = nxt.end
                prev.bboxes.extend(s.bboxes)
                prev.bboxes.extend(nxt.bboxes)
                i += 2
                changed = True
                continue

            if prev and nxt:
                prev_d = float(prev.end - prev.start)
                nxt_d = float(nxt.end - nxt.start)
                if prev_d >= nxt_d:
                    prev.end = max(prev.end, s.end)
                    prev.bboxes.extend(s.bboxes)
                else:
                    nxt.start = min(nxt.start, s.start)
                    nxt.bboxes = s.bboxes + nxt.bboxes
                i += 1
                changed = True
                continue

            if prev and not nxt:
                prev.end = max(prev.end, s.end)
                prev.bboxes.extend(s.bboxes)
                i += 1
                changed = True
                continue

            if (not prev) and nxt:
                nxt.start = min(nxt.start, s.start)
                nxt.bboxes = s.bboxes + nxt.bboxes
                i += 1
                changed = True
                continue

            i += 1

        segs = new_segs

    changed = True
    while changed:
        changed = False
        segs = sorted(segs, key=lambda s: s.start)
        out: List[Segment] = []
        i = 0
        while i < len(segs):
            if i >= 2:
                a = out[-1]
                b = segs[i]
                c = segs[i + 1] if (i + 1) < len(segs) else None

                if c and a.label == c.label and float(b.end - b.start) <= float(bridge_gap_sec):
                    a.end = c.end
                    a.bboxes.extend(b.bboxes)
                    a.bboxes.extend(c.bboxes)
                    i += 2
                    changed = True
                    continue

            out.append(segs[i])
            i += 1

        segs = out

    segs = merge_close_segments(segs, float(merge_gap_sec))
    return segs


def smooth_group_segments(
    segs: List[Segment],
    min_group_seg_sec: float,
    merge_gap_sec: float,
) -> List[Segment]:
    if not segs:
        return segs
    segs = merge_close_segments(segs, float(merge_gap_sec))
    segs = [s for s in segs if float(s.end - s.start) >= float(min_group_seg_sec)]
    segs = merge_close_segments(segs, float(merge_gap_sec))
    return segs


def intersect_main_segments(segments, eligible):
    """Apply output eligibility after identity inference; keep source indices.

    Eligibility is a time mask, never an identity vote. Adjacent body runs
    share eligibility, while a real excluded interval always splits output.
    """
    windows = []
    for scope in sorted(eligible, key=lambda s: s.start):
        if scope.end <= scope.start:
            continue
        if windows and scope.start <= windows[-1][1]:
            windows[-1] = (windows[-1][0], max(windows[-1][1], scope.end))
        else:
            windows.append((scope.start, scope.end))
    result = []
    for index, segment in enumerate(segments):
        for lower, upper in windows:
            start, end = max(segment.start, lower), min(segment.end, upper)
            if end > start:
                result.append((index, replace(segment, start=start, end=end,
                    bboxes=[row for row in segment.bboxes if start <= row[0] < end])))
    return result
