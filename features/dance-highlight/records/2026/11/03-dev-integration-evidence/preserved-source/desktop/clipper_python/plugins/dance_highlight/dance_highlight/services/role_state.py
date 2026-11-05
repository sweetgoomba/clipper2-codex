"""Retain an independently established main role inside a measured ensemble.
No original observation, name, group membership, or source coordinate is edited.
"""

import numpy as np
from .native_scene import _distinct_complete_count
from .observed_main import retained_bodies, strict_pose_corresponding
from .stage_prominence import foreground_subject


def sample_proof(record, role, video_size):
    width, height = video_size
    target = record.candidate_main_bbox

    def reject(reason, **details):
        return dict(accepted=False, reason=reason, **details)

    boxes = [np.asarray(b) for b in record.person_bboxes]
    poses = [np.asarray(p) for p in record.person_pose_keypoints]
    if (
        target is None
        or len(boxes) != len(poses)
        or not boxes
        or any(b.shape != (4,) or not np.isfinite(b).all() or (b[2:] <= b[:2]).any() for b in boxes)
        or any(p.shape != (17, 3) or not np.isfinite(p).all() for p in poses)
    ):
        return reject("invalid_original_geometry")
    kept = retained_bodies(boxes, poses)
    selected = [i for i in kept if np.allclose(boxes[i], target, atol=1e-3, rtol=0)]
    if len(selected) != 1:
        return reject("ambiguous_original_target")
    selected = selected[0]
    if (
        role is None
        or role.get("box") is None
        or not np.allclose(role["box"], target, atol=1e-3, rtol=0)
    ):
        return reject("role_target_mismatch")
    if role.get("reason") not in (
        "measured_face_composition",
        "confirmed_measured_face_composition",
    ):
        return reject("different_original_role_basis")
    features = {}
    details = []
    for f in role.get("features", []):
        i = f.get("index")
        if (
            not isinstance(i, int)
            or i in features
            or i not in kept
            or f.get("box") is None
            or not np.allclose(f["box"], boxes[i], atol=1e-3, rtol=0)
        ):
            return reject("feature_original_owner_mismatch")
        if f.get("size") is not None and (
            not np.isfinite(f["size"])
            or f["size"] <= 0
            or f.get("source") not in ("detected", "repeated_same_pose_geometry")
        ):
            return reject("invalid_face_measurement")
        features[i] = dict(f, pose_keypoints=poses[i])
    if set(features) != set(kept):
        return reject("missing_original_competitor")
    t = features[selected]
    if t.get("source") != "detected" or t.get("size") is None:
        return reject("target_face_not_directly_measured")

    def weight(x):
        return max(0, 1 - abs(x - width / 2) / (width / 2)) ** 2

    for i in kept:
        box, pose, f = boxes[i], poses[i], features[i]
        torso = pose[[5, 6, 11, 12]]
        central = bool(box[2] >= 0.25 * width and box[0] <= 0.75 * width)
        reliable = bool(
            (torso[:, 2] >= 0.75).all()
            and (
                (torso[:, :2] >= np.maximum(box[:2], [0, 0]))
                & (torso[:, :2] < np.minimum(box[2:], [width, height]))
            ).all()
            and torso[:2, 1].mean() < torso[2:, 1].mean()
        )
        if not reliable:
            return reject("unmeasured_plausible_competitor", index=i)
        x = float(torso[:, 0].mean())
        if x is None:
            return reject("unmeasured_competitor_position", index=i)
        if reliable and (f.get("x") is None or abs(x - f["x"]) > 1e-3):
            return reject("role_position_mismatch", index=i)
        length = float(np.linalg.norm(torso[:2, :2].mean(axis=0) - torso[2:, :2].mean(axis=0)))
        if reliable and (length < 4 or np.ptp(torso[:, 0]) <= 0):
            return reject("degenerate_torso", index=i)
        details.append(
            dict(
                index=i,
                selected=i == selected,
                central=central,
                x=x,
                face=f.get("size"),
                source=f.get("source"),
                face_score=f["size"] / height * weight(x) if f.get("size") is not None else None,
                torso_length=length,
                torso_score=length / height * weight(x) if length else None,
                body_height=float(box[3] - box[1]),
                clipped=bool(
                    (box[:2] <= 0).any()
                    or (box[2:] >= np.array([width, height])).any()
                    or f.get("cropped_foreground", False)
                ),
            )
        )
    # Retention here is a main inside a measured ensemble, never a duet rule.
    complete = []
    for i in kept:
        b, p = boxes[i], poses[i]
        v = (
            (p[:, 2] >= 0.5)
            & (p[:, 0] >= max(0, b[0]))
            & (p[:, 0] < min(width, b[2]))
            & (p[:, 1] >= max(0, b[1]))
            & (p[:, 1] < min(height, b[3]))
        )
        xy = p[[5, 6, 11, 12], :2]
        full = bool(
            v[:5].sum() >= 2
            and v[[5, 6, 11, 12, 15, 16]].all()
            and p[:5, 1][v[:5]].max()
            < p[[5, 6], 1].mean()
            < p[[11, 12], 1].mean()
            < p[[15, 16], 1].mean()
        )
        complete.append(dict(full=full, rect=np.r_[xy.min(axis=0), xy.max(axis=0)]))
    if _distinct_complete_count(complete) < 3:
        return reject("not_three_distinct_observed_ensemble_bodies")
    target_details = next(d for d in details if d["selected"])
    others = [d for d in details if not d["selected"]]
    observed = [d for d in details if d["face_score"] is not None]
    face_runner = max((d["face_score"] for d in others if d["face_score"] is not None), default=0.0)
    if target_details["face_score"] <= 1.06 * face_runner:
        return reject("face_composition_not_uniquely_retained", details=details)
    # Recompute the original scale-based foreground overrides before retention.
    ranked = sorted([features[d["index"]] for d in observed], key=lambda f: f["size"], reverse=True)
    if (
        len(ranked) >= 2
        and ranked[0]["size"] >= 1.3 * ranked[1]["size"]
        and (
            0.25 * width <= ranked[0]["x"] <= 0.75 * width
            or ranked[0].get("cropped_foreground", False)
        )
        and ranked[0]["index"] != selected
    ):
        return reject("different_dominant_foreground", details=details)
    foreground = foreground_subject(list(features.values()), width, height)
    if foreground is not None and foreground["index"] != selected:
        return reject("different_corroborated_foreground", details=details)
    torso_runners = []
    for d in others:
        # An unmeasured face cannot disappear from competition at a central-half
        # boundary. Its original torso and complete box must positively bound a
        # smaller background body regardless of horizontal position.
        if (d["source"] != "detected" or d["face"] is None) and (
            d["clipped"]
            or d["torso_length"] >= target_details["torso_length"]
            or d["body_height"] >= target_details["body_height"]
        ):
            return reject("unmeasured_face_on_possible_foreground", details=details)
        if not d["central"]:
            continue
        torso_runners.append(d["torso_score"])
        if target_details["torso_score"] <= 1.06 * d["torso_score"]:
            return reject("torso_composition_not_uniquely_retained", details=details)
    return dict(
        accepted=True,
        reason="same_original_role_with_observed_competitor_dominance",
        selected=selected,
        face_ratio=target_details["face_score"] / face_runner if face_runner else None,
        torso_ratio=target_details["torso_score"] / max(torso_runners) if torso_runners else None,
        details=details,
    )


def body_path_record(record):
    boxes = [np.asarray(b) for b in record.person_bboxes]
    poses = [np.asarray(p) for p in record.person_pose_keypoints]
    features = [dict(index=i, pose_keypoints=poses[i]) for i in retained_bodies(boxes, poses)]
    selected = [
        f
        for f in features
        if record.candidate_main_bbox is not None
        and np.allclose(boxes[f["index"]], record.candidate_main_bbox, atol=1e-3, rtol=0)
    ]
    return dict(features=features), selected[0] if len(selected) == 1 else None


def prove_role_state(
    records,
    roles,
    owned_names,
    *,
    video_size,
    fps,
    cut_frames,
    handoffs,
    camera_episodes,
    identity_boundaries=(),
):
    # Caller supplies only original final_name == direct_joint_name with owned=True.
    # A joint prediction alone is not a trusted named role and cannot enter here.
    audit = dict(version="bounded_original_role_state_v1", candidates=[], accepted=[])
    if cut_frames is None or handoffs is None or camera_episodes is None:
        return dict(audit, reason="missing_source_role_inventory")
    frames = [round(r.t * fps) for r in records]
    by_role = {r["frame"]: r for r in roles}
    step = round(np.median(np.diff(frames))) if len(frames) > 1 else 0

    def direct(i):
        return owned_names.get(frames[i])

    def eligible_anchor(i, name):
        return (
            0 <= i < len(records)
            and records[i].scene_kind == "main"
            and records[i].scene_reason == "main_eligible_composition"
            and direct(i) == name
        )

    i = 0
    while i < len(records):
        if records[i].scene_kind != "group":
            i += 1
            continue
        start = i
        while i < len(records) and records[i].scene_kind == "group":
            i += 1
        end = i
        if not 0 < start < end < len(records):
            continue
        item = dict(start=records[start].t, end=records[end].t, frames=frames[start:end])
        audit["candidates"].append(item)
        name = direct(start - 1)
        if not name or direct(end) != name:
            item["reason"] = "different_or_missing_original_named_bracket"
            continue
        left, right = start - 1, end
        while (
            left > 0
            and records[start - 1].t - records[left].t < 0.15 - 1e-6
            and eligible_anchor(left - 1, name)
        ):
            left -= 1
        while (
            right + 1 < len(records)
            and records[right].t - records[end].t < 0.15 - 1e-6
            and eligible_anchor(right + 1, name)
        ):
            right += 1
        item.update(
            name=name,
            left=records[left].t,
            right=records[right].t,
            proof_frames=frames[left : right + 1],
        )
        if (
            not all(eligible_anchor(j, name) for j in [left, start - 1, end, right])
            or records[start - 1].t - records[left].t < 0.15 - 1e-6
            or records[right].t - records[end].t < 0.15 - 1e-6
        ):
            item["reason"] = "missing_two_sustained_original_main_anchors"
            continue
        if any(
            records[j].scene_reason != "distributed_full_body_ensemble" for j in range(start, end)
        ):
            item["reason"] = "protected_group_kind"
            continue
        if any(direct(j) != name for j in range(left, right + 1)):
            item["reason"] = "missing_or_conflicting_original_owned_face"
            continue
        if any(frames[j] - frames[j - 1] != step for j in range(left + 1, right + 1)):
            item["reason"] = "missing_pose_cadence"
            continue
        if any(frames[left] < c <= frames[right] for c in cut_frames):
            item["reason"] = "original_source_cut"
            continue
        if any(
            h.get("previous_time", h["time"]) <= records[right].t and h["time"] >= records[left].t
            for h in handoffs
        ):
            item["reason"] = "original_main_handoff"
            continue
        if any(
            p["start_frame"] <= frames[right] and p["end_frame"] >= frames[left]
            for p in camera_episodes
        ):
            item["reason"] = "camera_role_episode"
            continue
        if any(records[left].t < t <= records[right].t for t in identity_boundaries):
            item["reason"] = "original_identity_boundary"
            continue
        samples = []
        failed = False
        for j in range(left, right + 1):
            proof = sample_proof(records[j], by_role.get(frames[j]), video_size)
            samples.append(dict(frame=frames[j], **proof))
            if not proof["accepted"]:
                item.update(
                    reason="unproved_temporal_composition",
                    failed_frame=frames[j],
                    sample_proofs=samples,
                )
                failed = True
                break
        if failed:
            continue
        for j in range(left + 1, right + 1):
            old, a = body_path_record(records[j - 1])
            new, b = body_path_record(records[j])
            matched = strict_pose_corresponding(old, a, new) if a is not None else None
            reverse = strict_pose_corresponding(new, b, old) if b is not None else None
            if (
                matched is None
                or b is None
                or matched["index"] != b["index"]
                or reverse is None
                or reverse["index"] != a["index"]
            ):
                item.update(reason="selected_body_path_changed", failed_frame=frames[j])
                failed = True
                break
        if failed:
            continue
        item.update(
            reason="accepted",
            sample_proofs=samples,
            main_role_frames=frames[start:end],
            group_export_policy="preserve_original_dual_eligibility",
        )
        audit["accepted"].append(item)
    return dict(audit, reason="complete")
