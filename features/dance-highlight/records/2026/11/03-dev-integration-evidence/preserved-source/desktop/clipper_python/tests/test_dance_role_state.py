import copy, json, pickle
from dataclasses import replace
from pathlib import Path
import numpy as np
import pytest
from dance_highlight.services.segment import FrameRec
from dance_highlight.services.role_state import prove_role_state, sample_proof

FIXTURE = Path(__file__).parent / "fixtures/dance_scene_review/mmn104_role_state.json"


@pytest.fixture(scope="session")
def original():
    f = json.loads(FIXTURE.read_text())
    records = []
    for p in f["pose_heads"]:
        box = np.asarray(p["candidate_main_bbox"]) if p["candidate_main_bbox"] is not None else None
        records.append(
            FrameRec(
                p["time_seconds"],
                p["candidate_main_id"] if p["scene_kind"] == "main" else None,
                box if p["scene_kind"] == "main" else None,
                p["scene_kind"] == "group",
                person_bboxes=[np.array(b) for b in p["body_boxes"]],
                person_head_keypoints=[np.array(k) for k in p["head_keypoints"]],
                person_pose_keypoints=[np.array(k) for k in p["pose_keypoints"]],
                candidate_main_id=p["candidate_main_id"],
                candidate_main_bbox=box,
                scene_kind=p["scene_kind"],
                scene_reason=p["scene_reason"],
            )
        )
    return dict(
        records=records,
        roles=f["roles"],
        owned_names={int(k): v for k, v in f["owned_names"].items()},
        video_size=(1920, 1080),
        fps=f["fps"],
        cut_frames=f["cut_frames"],
        handoffs=f["handoffs"],
        camera_episodes=f["camera_episodes"],
    )


def run(original, mutate=None):
    args = copy.deepcopy(original)
    if mutate:
        mutate(args)
    frozen = pickle.dumps(args)
    out = prove_role_state(**args)
    assert pickle.dumps(args) == frozen
    return out


def first_gap(args):
    i = next(i for i, r in enumerate(args["records"]) if r.scene_kind == "group")
    return i, args["records"][i], args["roles"][i]


def test_actual_continuous_role_is_retained_without_group_deletion_or_observation_mutation(
    original,
):
    a = run(original)["accepted"]
    assert len(a) == 1
    assert a[0]["frames"] == [6268, 6272, 6276, 6280, 6284]
    assert a[0]["group_export_policy"] == "preserve_original_dual_eligibility"
    assert len(a[0]["sample_proofs"]) == 13
    assert all(s["face_ratio"] > 1.06 and s["torso_ratio"] > 1.06 for s in a[0]["sample_proofs"])


@pytest.mark.parametrize("key", ["cut_frames", "handoffs", "camera_episodes"])
def test_missing_role_inventory_cannot_retain(original, key):
    assert not run(original, lambda a: a.update({key: None}))["accepted"]


def test_even_a_short_source_cut_blocks(original):
    assert not run(original, lambda a: a["cut_frames"].append(6270))["accepted"]


def test_original_handoff_blocks(original):
    assert not run(original, lambda a: a["handoffs"].append(dict(time=6270 / a["fps"])))["accepted"]


def test_camera_subject_change_blocks(original):
    assert not run(
        original, lambda a: a["camera_episodes"].append(dict(start_frame=6270, end_frame=6272))
    )["accepted"]


def test_original_identity_boundary_blocks(original):
    assert not run(original, lambda a: a.update(identity_boundaries=[6270 / a["fps"]]))["accepted"]


@pytest.mark.parametrize("name", [None, "different_member_same_costume"])
def test_identical_costume_or_body_path_cannot_replace_original_identity(original, name):
    def mutate(a):
        a["owned_names"][6272] = name

    assert not run(original, mutate)["accepted"]


def test_native_distant_ensemble_is_protected(original):
    def mutate(a):
        i, r, role = first_gap(a)
        a["records"][i] = replace(r, scene_reason="native_distant_ensemble")

    assert not run(original, mutate)["accepted"]


def test_one_short_original_main_is_not_a_sustained_anchor(original):
    def mutate(a):
        a["records"] = a["records"][2:]
        a["roles"] = a["roles"][2:]

    assert not run(original, mutate)["accepted"]


def test_missing_observed_pose_cadence_blocks(original):
    def mutate(a):
        del a["records"][5]
        del a["roles"][5]

    assert not run(original, mutate)["accepted"]


@pytest.mark.parametrize("source", ["missing", "repeated_same_pose_geometry"])
def test_selected_face_must_be_original_detection(original, source):
    def mutate(a):
        i, r, role = first_gap(a)
        f = next(f for f in role["features"] if np.allclose(f["box"], r.candidate_main_bbox))
        f["source"] = source
        if source == "missing":
            f["size"] = None

    assert not run(original, mutate)["accepted"]


def test_missing_competitor_cannot_be_dropped_from_role_inventory(original):
    def mutate(a):
        i, r, role = first_gap(a)
        role["features"] = role["features"][:-1]

    assert not run(original, mutate)["accepted"]


def add_competitor(a, kind):
    i, r, role = first_gap(a)
    index = len(r.person_bboxes)
    box = np.array([840.0, 230.0, 1120.0, 1000.0])
    pose = np.zeros((17, 3))
    pose[:, 2] = 0.1
    pose[:5] = [[980, 300, 1], [970, 295, 1], [990, 295, 1], [960, 302, 1], [1000, 302, 1]]
    pose[[5, 6, 11, 12]] = [[940, 400, 1], [1020, 400, 1], [950, 600, 1], [1010, 600, 1]]
    pose[[15, 16]] = [[955, 950, 1], [1005, 950, 1]]
    size = 10.0
    source = "detected"
    if kind == "unmeasured_pose":
        pose[:, 2] = 0.1
        size = None
        source = "missing"
    if kind == "faceless_large_box":
        pose[:5, 2] = 0.1
        pose[[11, 12], 1] = 480.0
        size = None
        source = "missing"
    r.person_bboxes.append(box)
    r.person_pose_keypoints.append(pose)
    r.person_head_keypoints.append(pose[:5].copy())
    role["features"].append(
        dict(
            index=index,
            box=box.tolist(),
            size=size,
            x=980.0,
            source=source,
            cropped_foreground=False,
        )
    )


@pytest.mark.parametrize(
    "kind", ["unmeasured_pose", "faceless_large_box", "different_torso_foreground"]
)
def test_central_or_foreground_competitor_veto(original, kind):
    assert not run(original, lambda a: add_competitor(a, kind))["accepted"]


def test_near_tied_measured_face_does_not_prove_one_role(original):
    def mutate(a):
        i, r, role = first_gap(a)
        target = next(f for f in role["features"] if np.allclose(f["box"], r.candidate_main_bbox))
        other = next(f for f in role["features"] if f["index"] != target["index"])
        weight = lambda x: (1 - abs(x - 960) / 960) ** 2
        other["size"] = target["size"] * weight(target["x"]) / weight(other["x"]) / 1.03

    assert not run(original, mutate)["accepted"]


def test_role_reason_alone_does_not_hide_selected_body_switch(original):
    def mutate(a):
        i, r, role = first_gap(a)
        other = next(
            f for f in role["features"] if not np.allclose(f["box"], r.candidate_main_bbox)
        )
        a["records"][i] = replace(r, candidate_main_bbox=np.array(other["box"]))
        role["box"] = other["box"]

    assert not run(original, mutate)["accepted"]


def test_source_cache_owner_mismatch_blocks(original):
    def mutate(a):
        i, r, role = first_gap(a)
        role["features"][0]["box"][0] += 2

    assert not run(original, mutate)["accepted"]


def test_duet_cannot_be_reinterpreted_as_this_ensemble_rule(original):
    def mutate(a):
        for i, (r, role) in enumerate(zip(a["records"], a["roles"])):
            target = next(
                f for f in role["features"] if np.allclose(f["box"], r.candidate_main_bbox)
            )
            other = next(f for f in role["features"] if f["index"] != target["index"])
            keep = [target["index"], other["index"]]
            a["records"][i] = replace(
                r,
                person_bboxes=[r.person_bboxes[k] for k in keep],
                person_pose_keypoints=[r.person_pose_keypoints[k] for k in keep],
                person_head_keypoints=[r.person_head_keypoints[k] for k in keep],
            )
            role["features"] = [dict(f, index=j) for j, f in enumerate([target, other])]

    assert not run(original, mutate)["accepted"]


@pytest.mark.parametrize("order", ["reverse", "rotate"])
def test_detection_order_does_not_define_the_role(original, order):
    def mutate(a):
        for n, (r, role) in enumerate(zip(a["records"], a["roles"])):
            k = len(r.person_bboxes)
            indices = (
                list(reversed(range(k)))
                if order == "reverse"
                else list(range(n % k, k)) + list(range(n % k))
            )
            mapping = {old: new for new, old in enumerate(indices)}
            a["records"][n] = replace(
                r,
                person_bboxes=[r.person_bboxes[j] for j in indices],
                person_pose_keypoints=[r.person_pose_keypoints[j] for j in indices],
                person_head_keypoints=[r.person_head_keypoints[j] for j in indices],
            )
            role["features"] = [
                dict(f, index=mapping[f["index"]]) for f in reversed(role["features"])
            ]

    assert run(original, mutate)["accepted"][0]["frames"] == [6268, 6272, 6276, 6280, 6284]


@pytest.mark.parametrize("side", ["left", "right"])
def test_large_offcenter_unmeasured_cropped_body_vetoes_retention(original, side):
    def mutate(a):
        for r, role in zip(a["records"], a["roles"]):
            index = len(r.person_bboxes)
            box = np.array(
                [0.0, 0.0, 479.0, 1080.0] if side == "left" else [1441.0, 0.0, 1920.0, 1080.0]
            )
            pose = np.zeros((17, 3))
            pose[:, 2] = 0.1
            r.person_bboxes.append(box)
            r.person_pose_keypoints.append(pose)
            r.person_head_keypoints.append(pose[:5].copy())
            role["features"].append(
                dict(
                    index=index,
                    box=box.tolist(),
                    size=None,
                    x=float((box[0] + box[2]) / 2),
                    source="missing",
                    cropped_foreground=True,
                )
            )

    assert not run(original, mutate)["accepted"]


@pytest.mark.parametrize(
    "source,size", [("missing", None), ("detected", None), ("repeated_same_pose_geometry", 10.0)]
)
def test_measured_offcenter_torso_does_not_bound_large_faceless_body(original, source, size):
    def mutate(a):
        for r, role in zip(a["records"], a["roles"]):
            index = len(r.person_bboxes)
            box = np.array([10.0, 100.0, 470.0, 1060.0])
            pose = np.zeros((17, 3))
            pose[:, 2] = 0.1
            pose[[5, 6, 11, 12]] = [[200, 500, 1], [280, 500, 1], [210, 560, 1], [270, 560, 1]]
            r.person_bboxes.append(box)
            r.person_pose_keypoints.append(pose)
            r.person_head_keypoints.append(pose[:5].copy())
            role["features"].append(
                dict(
                    index=index,
                    box=box.tolist(),
                    size=size,
                    x=240.0,
                    source=source,
                    cropped_foreground=False,
                )
            )

    assert not run(original, mutate)["accepted"]


@pytest.mark.parametrize("edge", ["left", "right", "straddles_right"])
def test_handoff_closed_observation_bracket_overlap_vetoes(original, edge):
    def mutate(a):
        lo = a["records"][0].t
        hi = a["records"][-1].t
        previous, time = (
            (lo - 0.1, lo)
            if edge == "left"
            else (hi, hi + 0.1)
            if edge == "right"
            else (hi - 0.01, hi + 0.1)
        )
        a["handoffs"].append(dict(previous_time=previous, time=time))

    assert not run(original, mutate)["accepted"]


@pytest.mark.parametrize("kind", ["cut", "identity"])
@pytest.mark.parametrize("edge,expected", [("left", True), ("right", False)])
def test_point_boundaries_begin_a_shot_but_cannot_cross_the_proof(original, kind, edge, expected):
    def mutate(a):
        record = a["records"][0 if edge == "left" else -1]
        if kind == "cut":
            a["cut_frames"].append(round(record.t * a["fps"]))
        else:
            a["identity_boundaries"] = [record.t]

    assert bool(run(original, mutate)["accepted"]) is expected


def test_role_audit_can_be_written_as_json(original):
    audit = run(original)
    assert json.loads(json.dumps(audit))["accepted"][0]["frames"] == [6268, 6272, 6276, 6280, 6284]
