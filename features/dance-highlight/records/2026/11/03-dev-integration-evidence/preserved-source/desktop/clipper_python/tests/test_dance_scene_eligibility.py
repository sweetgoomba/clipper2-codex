"""User-reviewed scene composition, independent of face identity success."""
import json
from pathlib import Path

import numpy as np
import pytest

from dance_highlight.services import segment
from dance_highlight.services.segment import FrameRec, MainSelector, build_raw_main_segments


def _classify(records, size=(1920, 1080)):
    return segment.classify_main_scenes(records, size)


@pytest.mark.parametrize('fixture', ['antifragile', 'neon', 'made-my-night'])
@pytest.mark.parametrize('scale', [1., .5])
def test_user_reviewed_scene_does_not_force_a_main_in_distant_ensemble(fixture, scale):
    data = json.loads((Path(__file__).parent/'fixtures/dance_scene_review'/f'{fixture}.json').read_text())
    selector = MainSelector(fps=60., group_fps=15.)
    recs = []
    for row in data['rows']:
        people = [{k: np.asarray(v, np.float32).copy() for k,v in p.items()} for p in row['persons']]
        for person in people:
            person['bbox'] *= scale
            person['keypoints'] *= scale
            person['head_keypoints'][:, :2] *= scale
        chosen, group = selector.select(people, (int(1080*scale), int(1920*scale), 3), time_seconds=row['time_seconds'])
        recs.append(FrameRec(row['time_seconds'], 1 if chosen else None,
                             chosen['bbox'] if chosen else None, group,
                             person_bboxes=[p['bbox'] for p in people]))
    result = _classify(recs, (int(1920*scale), int(1080*scale)))
    reviewed = [r for r in result if data['start'] <= r.t < data['end']]
    assert reviewed
    if data['expected_scene'] == 'group':
        assert all(r.main_id is None and r.is_group for r in reviewed)
    else:
        assert all(r.main_id is not None for r in reviewed)
    # Frozen input preserves the original tentative selection for audit/replay.
    assert all(r.main_id is not None for r in recs if data['start'] <= r.t < data['end'])


def _record(t, boxes, group=False):
    values = [np.asarray(b, np.float32) for b in boxes]
    return FrameRec(t, 1 if values else None, values[0] if values else None,
                    group, person_bboxes=values)


def test_group_does_not_swallow_a_short_closeup_or_bridge_over_it():
    wide = [[300,500,430,800],[850,500,980,800],[1300,500,1430,800]]
    close = [[650,80,1250,1080]]
    recs = [_record(i/10, close if 1 <= i/10 < 1.3 else wide) for i in range(24)]
    result = _classify(recs)
    assert [(s.start,s.end) for s in build_raw_main_segments(result)] == [(1.,1.3)]
    assert all(r.is_group for r in result if r.t < 1 or r.t >= 1.3)


def test_empty_scene_clears_group_and_continuous_main_has_no_duration_cap():
    body = [[650,80,1250,1080]]
    recs = [_record(i/10, body if i < 60 else [], group=i >= 60) for i in range(66)]
    result = _classify(recs)
    assert [(s.start,s.end) for s in build_raw_main_segments(result)] == [(0.,6.)]
    assert all(not r.is_group and r.main_id is None for r in result[60:])


def test_a_single_isolated_wide_detection_does_not_remove_a_main():
    body = [[650,80,1250,1080]]
    wide = [[300,500,430,800],[850,500,980,800],[1300,500,1430,800]]
    recs = [_record(i/10, wide if i == 10 else body) for i in range(21)]
    assert all(r.main_id is not None for r in _classify(recs))


def test_medium_framed_formation_does_not_automatically_veto_its_main():
    # Distributed bodies alone do not establish that a clearly framed main is
    # absent. The conservative scene gate applies to distant ensembles only.
    medium = [[300,350,460,780],[800,350,990,780],[1300,350,1460,780]]
    result = _classify([_record(i/10, medium) for i in range(31)])
    assert [(s.start,s.end) for s in build_raw_main_segments(result)] == [(0.,3.)]


@pytest.mark.parametrize('fps', [15.,24.,30.,60.])
def test_ensemble_confirmation_respects_actual_analysis_cadence(fps):
    wide = [[300,500,430,800],[850,500,980,800],[1300,500,1430,800]]
    result = _classify([_record(i/fps, wide) for i in range(0, int(fps*3), 4)])
    assert all(r.main_id is None and r.is_group for r in result)


def test_partially_obscured_ensemble_does_not_make_remaining_peripheral_body_main():
    wide = [[300,500,430,800],[850,500,980,800],[1300,500,1430,800]]
    records = [_record(i/10, [wide[0]] if .8 <= i/10 < 1.3 else wide) for i in range(21)]
    result = _classify(records)
    assert all(r.main_id is None and r.is_group for r in result)


@pytest.mark.parametrize('end', [.9,1.,1.1])
def test_short_main_with_new_framing_is_not_a_group_detector_dropout(end):
    wide = [[300,500,430,800],[850,500,980,800],[1300,500,1430,800]]
    foreground = [[800,300,1100,760]]
    records = [_record(i/10, foreground if .8 <= i/10 < end else wide) for i in range(21)]
    result = _classify(records)
    assert [(s.start,s.end) for s in build_raw_main_segments(result)] == [(.8,end)]


def test_user_reviewed_distributed_full_body_ensemble_is_group_despite_a_false_tall_box():
    data=json.loads((Path(__file__).parent/'fixtures/dance_scene_review/neon-distributed-ensemble.json').read_text())
    records=[]
    for p in data['rows']:
        records.append(FrameRec(p['time_seconds'],p['candidate_main_id'],np.asarray(p['candidate_main_bbox']),False,
            person_bboxes=[np.array(b) for b in p['body_boxes']],
            person_head_keypoints=[np.array(h) for h in p['head_keypoints']],
            person_pose_keypoints=[np.array(k) for k in p['pose_keypoints']]))
    rows=[r for r in _classify(records) if data['start']+4/59.94005994<=r.t<data['end']-4/59.94005994]
    assert rows
    assert all(r.scene_kind=='group' and r.main_bbox is None for r in rows)


def _posed_ensemble(boxes):
    poses=[]
    for x,y,xx,yy in boxes:
        w,h=xx-x,yy-y
        p=np.zeros((17,3));p[:,2]=.9
        p[:5,:2]=[[x+.5*w,y+.08*h],[x+.4*w,y+.06*h],[x+.6*w,y+.06*h],[x+.3*w,y+.08*h],[x+.7*w,y+.08*h]]
        p[[5,6,11,12,15,16],:2]=[[x+.3*w,y+.2*h],[x+.7*w,y+.2*h],[x+.35*w,y+.5*h],[x+.65*w,y+.5*h],[x+.35*w,y+.95*h],[x+.65*w,y+.95*h]]
        poses.append(p)
    return FrameRec(0,1,np.array(boxes[0]),False,person_bboxes=[np.array(b) for b in boxes],
                    person_head_keypoints=[p[:5] for p in poses],person_pose_keypoints=poses)


def test_distributed_ensemble_requires_visible_pose_and_preserves_foreground_and_compact_main():
    from dataclasses import replace
    wide=_posed_ensemble([[180,250,400,850],[750,250,980,850],[1320,250,1540,850]])
    def classify(rec):return _classify([replace(rec,t=i/10) for i in range(5)])
    assert all(r.scene_kind=='group' for r in classify(wide))
    compact=_posed_ensemble([[600,250,820,850],[800,250,1030,850],[1010,250,1230,850]])
    assert all(r.scene_kind=='main' for r in classify(compact))
    cropped=_posed_ensemble([[600,50,1250,1080],[180,250,400,850],[750,250,980,850],[1320,250,1540,850]])
    cropped.person_pose_keypoints[0][[15,16],2]=0
    assert all(r.scene_kind=='main' for r in classify(cropped))
    weak=_posed_ensemble([[180,250,400,850],[750,250,980,850],[1320,250,1540,850]])
    weak.person_pose_keypoints[1][[15,16],2]=0
    assert all(r.scene_kind=='main' for r in classify(weak))


def test_reliable_torso_keeps_large_foreground_veto_when_head_and_feet_are_hidden():
    from dataclasses import replace
    rec=_posed_ensemble([[600,50,1250,1080],[180,250,400,850],[750,250,980,850],[1320,250,1540,850]])
    rec.person_pose_keypoints[0][:5,2]=.2
    rec.person_pose_keypoints[0][[15,16],2]=0
    result=_classify([replace(rec,t=i/10) for i in range(5)])
    assert all(r.scene_kind=='main' for r in result)


def test_one_person_pose_cannot_certify_multiple_distributed_body_boxes():
    from dataclasses import replace
    rec=_posed_ensemble([[180,250,400,850],[750,250,980,850],[1320,250,1540,850]])
    rec.person_pose_keypoints=[rec.person_pose_keypoints[1].copy() for _ in range(3)]
    rec.person_head_keypoints=[p[:5] for p in rec.person_pose_keypoints]
    result=_classify([replace(rec,t=i/10) for i in range(5)])
    assert all(r.scene_kind=='main' for r in result)


@pytest.mark.parametrize('offset', [0., 8.])
def test_overlapping_boxes_cannot_count_repeated_torso_evidence_as_three_people(offset):
    from dataclasses import replace
    rec=_posed_ensemble([[300,250,1150,850],[500,250,1350,850],[700,250,1550,850]])
    pose=_posed_ensemble([[750,250,980,850]]).person_pose_keypoints[0]
    rec.person_pose_keypoints=[pose.copy() for _ in range(3)]
    for i,p in enumerate(rec.person_pose_keypoints):
        p[:,:2] += offset*i
    rec.person_head_keypoints=[p[:5] for p in rec.person_pose_keypoints]
    result=_classify([replace(rec,t=i/10) for i in range(5)])
    assert all(r.scene_kind=='main' for r in result)


@pytest.mark.parametrize('order', [[0,1,2,3], [1,0,2,3], [3,2,1,0]])
def test_ambiguous_pose_overlap_components_do_not_depend_on_detection_order(order):
    from dataclasses import replace
    rec=_posed_ensemble([[100,250,300,850],[140,250,340,850],[180,250,380,850],[1320,250,1540,850]])
    for attr in ('person_bboxes','person_head_keypoints','person_pose_keypoints'):
        values=getattr(rec,attr)
        setattr(rec,attr,[values[i] for i in order])
    result=_classify([replace(rec,t=i/10) for i in range(5)])
    assert all(r.scene_kind=='main' for r in result)


@pytest.mark.parametrize('scale', [.5, 1., 2.])
def test_reviewed_distant_ensemble_uses_observed_body_extent_not_box_padding(scale):
    data=json.loads((Path(__file__).parent/'fixtures/dance_scene_review/made-observed-distant-ensemble.json').read_text())
    records=[]
    for p in data['rows']:
        poses=[np.asarray(k).copy() for k in p['pose_keypoints']]
        for pose in poses:pose[:,:2]*=scale
        records.append(FrameRec(p['time_seconds'],p['candidate_main_id'],np.asarray(p['candidate_main_bbox'])*scale,False,
            person_bboxes=[np.asarray(b)*scale for b in p['body_boxes']],
            person_head_keypoints=[k[:5] for k in poses],person_pose_keypoints=poses))
    result=_classify(records,(round(1920*scale),round(1080*scale)))
    reviewed=[r for r in result if data['start']<=r.t<data['end']]
    assert reviewed and all(r.scene_kind=='group' and r.main_bbox is None for r in reviewed)


@pytest.mark.parametrize('missing', ['head', 'torso', 'feet'])
def test_distant_pose_extent_cannot_hide_an_incompletely_observed_person(missing):
    from dataclasses import replace
    rec=_posed_ensemble([[500,400,650,790],[750,400,900,790],[1000,400,1150,790],[1250,400,1400,790]])
    indices={'head':range(5),'torso':[5,6,11,12],'feet':[15,16]}[missing]
    rec.person_pose_keypoints[0][indices,2]=0
    result=_classify([replace(rec,t=i/10) for i in range(5)])
    assert all(r.scene_kind=='main' for r in result)


def test_duplicate_foreground_detections_cannot_change_typical_person_size():
    from dataclasses import replace
    rec=_posed_ensemble([[500,300,650,690],[850,450,1000,690],[1200,450,1350,690]])
    for attr in ('person_bboxes','person_head_keypoints','person_pose_keypoints'):
        values=getattr(rec,attr)
        values.extend([values[0].copy(),values[0].copy()])
    result=_classify([replace(rec,t=i/10) for i in range(5)])
    assert all(r.scene_kind=='main' for r in result)


def test_invalid_head_position_cannot_shrink_a_large_foreground_person():
    from dataclasses import replace
    rec=_posed_ensemble([[700,100,1100,800],[300,400,450,790],[1150,400,1300,790],[1400,400,1550,790]])
    rec.person_pose_keypoints[0][:5,1]=650
    result=_classify([replace(rec,t=i/10) for i in range(5)])
    assert all(r.scene_kind=='main' for r in result)


def test_distant_compact_formation_supplies_geometry_without_horizontal_spread_requirement():
    rec = _posed_ensemble([[820,500,870,730], [900,500,950,730], [980,500,1030,730]])
    assert segment.distributed_full_body_ensemble(rec, (1920,1080), allow_compact=True)
    assert not segment.distributed_full_body_ensemble(rec, (1920,1080))


@pytest.mark.parametrize('counterexample', ['duo', 'foreground', 'repeated_pose', 'unobserved_heads'])
def test_compact_group_proof_does_not_suppress_a_main_without_three_real_distant_people(counterexample):
    from dataclasses import replace
    boxes = [[820,500,870,730], [900,500,950,730], [980,500,1030,730]]
    if counterexample == 'duo': boxes = boxes[:2]
    if counterexample == 'foreground': boxes[0] = [820,200,1000,850]
    rec = _posed_ensemble(boxes)
    if counterexample == 'repeated_pose':
        rec.person_pose_keypoints = [rec.person_pose_keypoints[0].copy() for _ in boxes]
    if counterexample == 'unobserved_heads':
        for p in rec.person_pose_keypoints: p[:5,2] = .1
    result = _classify([replace(rec,t=i/10) for i in range(6)])
    assert all(r.scene_kind == 'main' for r in result)


def test_compact_role_examples_preserve_main_and_defer_unanchored_group():
    data = json.loads((Path(__file__).parent/'fixtures/dance_scene_review/compact_formation_roles.json').read_text())
    for case in data:
        rows = [FrameRec(r['time_seconds'], r['candidate_main_id'], np.array(r['candidate_main_bbox']), False,
            person_bboxes=[np.array(b) for b in r['body_boxes']],
            person_pose_keypoints=[np.array(p) for p in r['pose_keypoints']]) for r in case['rows']]
        result = [r for r in _classify(rows) if case.get('start', rows[0].t) <= r.t
                  <= case.get('end', rows[-1].t)]
        # The NEON reference remains a true group scene. Its isolated pose
        # window is insufficient to exclude a main under the extension-only
        # contract; source/native scene proof is handled separately. Do not
        # change the recorded scene truth to disguise that recall limitation.
        if case['expected'] == 'main':
            assert all(r.scene_kind == 'main' for r in result), case['name']
        else:
            assert {r.scene_kind for r in result} == {'main', 'group'}, case['name']
        assert all(r.main_bbox is not None for r in rows)


def test_sustained_central_subject_vetoes_compact_group_even_with_brief_pose_dropout():
    from dataclasses import replace
    rec = _posed_ensemble([[820,500,870,730], [930,500,990,730], [1050,500,1100,730]])
    rows = [replace(rec, t=i/10) for i in range(9)]
    rows[4] = _posed_ensemble([[820,500,870,730], [900,500,950,730], [980,500,1030,730]])
    rows[4].t = .4
    assert all(r.scene_kind == 'main' for r in _classify(rows))


def test_compact_group_gap_fill_cannot_erase_sustained_central_subject():
    from dataclasses import replace
    wide = _posed_ensemble([[820,500,870,730], [910,500,990,730], [1050,500,1100,730]])
    wide.person_pose_keypoints[1][[5,6,11,12],0] -= 10
    central = _posed_ensemble([[910,500,990,730]])
    rows = [replace(central if 1 <= i/10 <= 1.2 else wide, t=i/10) for i in range(24)]
    # Each side has an independently confirmed group anchor. The new compact
    # extension must still stop at the sustained possible central subject.
    anchor = _posed_ensemble([[400,500,450,730], [900,500,950,730], [1400,500,1450,730]])
    for i in [0,1,2,21,22,23]:
        rows[i] = replace(anchor, t=i/10)
    result = _classify(rows)
    assert all(r.scene_kind == 'main' for r in result if 1 <= r.t <= 1.2)
    assert all(r.scene_kind == 'group' for r in result if r.t < 1 or r.t > 1.2)


def test_new_compact_veto_does_not_change_preexisting_wide_group_gap_fill():
    from dataclasses import replace
    wide = _posed_ensemble([[820,500,870,730], [900,500,950,730], [980,500,1030,730], [300,500,350,730]])
    wide.person_pose_keypoints[3][:,2] = .1
    central = _posed_ensemble([[925,500,975,730]])
    rows = [replace(central if .8 <= i/10 < 1.1 else wide, t=i/10) for i in range(21)]
    assert all(r.scene_kind == 'group' for r in _classify(rows))


def test_new_compact_evidence_cannot_create_an_isolated_group_island():
    from dataclasses import replace
    compact = _posed_ensemble([[820,500,870,730], [900,500,950,730], [980,500,1030,730]])
    rows = [replace(compact, t=i/10) for i in range(6)]
    assert all(r.scene_kind == 'main' for r in _classify(rows))


def test_new_compact_evidence_can_extend_a_confirmed_group_run():
    from dataclasses import replace
    compact = _posed_ensemble([[820,500,870,730], [900,500,950,730], [980,500,1030,730]])
    wide = _posed_ensemble([[400,500,450,730], [900,500,950,730], [1400,500,1450,730]])
    rows = [replace(compact if i < 4 else wide, t=i/10) for i in range(10)]
    assert all(r.scene_kind == 'group' for r in _classify(rows))


def test_confirmed_group_after_missing_samples_cannot_anchor_compact_evidence():
    from dataclasses import replace
    compact = _posed_ensemble([[820,500,870,730], [900,500,950,730], [980,500,1030,730]])
    wide = _posed_ensemble([[400,500,450,730], [900,500,950,730], [1400,500,1450,730]])
    rows = [replace(compact, t=i/10) for i in range(6)]
    rows += [replace(wide, t=3+i/10) for i in range(6)]
    result = _classify(rows)
    assert all(r.scene_kind == 'main' for r in result[:6])
    assert all(r.scene_kind == 'group' for r in result[6:])
