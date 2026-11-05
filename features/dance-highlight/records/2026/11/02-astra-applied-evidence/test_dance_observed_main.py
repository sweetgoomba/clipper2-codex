from types import SimpleNamespace
import numpy as np
from dance_highlight.services.segment import FrameRec
from dance_highlight.services.observed_main import measured_features,refine_main_roles
from dance_highlight.services.main_role_timeline import choose_roles


def pose(cx):
    p=np.zeros((17,3));p[:,2]=.9
    p[:5,:2]=[[cx,120],[cx-15,115],[cx+15,115],[cx-25,120],[cx+25,120]]
    p[5:,:2]=[[cx-25,180],[cx+25,180],[cx-40,230],[cx+40,230],[cx-50,270],[cx+50,270],
              [cx-20,300],[cx+20,300],[cx-20,400],[cx+20,400],[cx-20,500],[cx+20,500]]
    return p


def record(t,scale=1):
    boxes=[np.array([cx-60,60,cx+60,550])*scale for cx in (200,500)]
    poses=[pose(cx) for cx in (200,500)]
    for p in poses:p[:,:2]*=scale
    return FrameRec(t,42,boxes[0],False,person_bboxes=boxes,person_head_keypoints=[p[:5] for p in poses],person_pose_keypoints=poses)


def faces(scale=1):
    rows=[]
    for cx in (200,500):
        a=np.array([cx-30,90,60,80,cx-15,115,cx+15,115,cx,120,cx-10,145,cx+10,145,.95]);a[:14]*=scale;rows.append(a)
    return rows


def geometry(records,scale=1):
    return [dict(frame=round(r.t*10),time=r.t,features=measured_features(r,faces(scale),1000*scale,600*scale)) for r in records],[],1000*scale,600*scale


def test_reselects_measured_center_body_without_mutating_input_or_capping_six_seconds(monkeypatch):
    from dance_highlight.services import observed_main as m
    records=[record(i/10) for i in range(61)]
    monkeypatch.setattr(m,'collect_geometry',lambda *args:geometry(records))
    out,audit=refine_main_roles(records,'unused',10,SimpleNamespace(_detector=None),SimpleNamespace(track_match_iou=.3,track_ttl_sec=.5))
    assert audit['reason']=='complete'
    assert all(np.array_equal(r.main_bbox,r.person_bboxes[1]) for r in out)
    assert len({r.main_id for r in out})==1 and out[-1].t-out[0].t==6
    assert all(np.array_equal(r.main_bbox,r.person_bboxes[0]) and r.main_id==42 for r in records)
    assert all(r.is_group is False for r in out)


def test_actual_face_geometry_and_role_are_resolution_invariant():
    chosen=[]
    for scale in (.5,1,2):
        records=[record(0,scale)];rows,cuts,w,h=geometry(records,scale)
        choose_roles(rows,{0:dict(candidate_main_bbox=records[0].main_bbox.tolist())},w,h,cuts,lambda *_:None)
        chosen.append(rows[0]['index'])
    assert chosen==[1,1,1]


def test_role_audit_preserves_selected_subject_and_reason_even_when_selection_did_not_change(monkeypatch):
    from dance_highlight.services import observed_main as m
    records=[record(i/10) for i in range(4)]
    for r in records:
        r.main_bbox=r.person_bboxes[1]
    monkeypatch.setattr(m,'collect_geometry',lambda *args:geometry(records))
    out,audit=refine_main_roles(records,'unused',10,SimpleNamespace(_detector=None),
        SimpleNamespace(track_match_iou=.3,track_ttl_sec=.5))
    assert audit['changes']==[]
    assert [(r['frame'],r['reason']) for r in audit['role_observations']]==[
        (0,'measured_face_composition'),(1,'measured_face_composition'),
        (2,'measured_face_composition'),(3,'measured_face_composition')]
    assert all(r['box']==records[0].person_bboxes[1].tolist() for r in audit['role_observations'])


def test_missing_face_and_incomplete_source_preserve_original_body(monkeypatch):
    from dance_highlight.services import observed_main as m
    records=[record(0),record(.1)]
    rows=[dict(frame=i,time=r.t,features=measured_features(r,[],1000,600)) for i,r in enumerate(records)]
    monkeypatch.setattr(m,'collect_geometry',lambda *args:(rows,[],1000,600))
    config=SimpleNamespace(track_match_iou=.3,track_ttl_sec=.5)
    out,audit=refine_main_roles(records,'unused',10,SimpleNamespace(_detector=None),config)
    assert all(np.array_equal(a.main_bbox,b.main_bbox) for a,b in zip(records,out))
    def broken(*_):raise ValueError('source_frame_unavailable')
    monkeypatch.setattr(m,'collect_geometry',broken)
    out,audit=refine_main_roles(records,'unused',10,SimpleNamespace(_detector=None),config)
    assert out is records and audit['reason']=='main_geometry_unavailable'


def handoff_rows(indices=(0,1), *, reverse_second=False):
    rows,_,_,_=geometry([record(0),record(.1)])
    for row,index in zip(rows,indices):row.update(index=index,reason='confirmed_measured_face_composition')
    if reverse_second:
        for f in rows[1]['features']:f['index']=1-f['index']
        rows[1]['index']=1-indices[1]
    return rows


def test_observed_handoff_requires_two_distinct_bodies_present_on_both_sides():
    from dance_highlight.services.observed_main import confirmed_main_handoffs
    found=confirmed_main_handoffs(handoff_rows(),[])
    assert [(r['frame'],r['time']) for r in found]==[(1,.1)]
    assert found[0]['previous_frame']==0 and found[0]['previous_time']==0
    assert found[0]['boundary_policy']=='first_observed_new_main'
    assert confirmed_main_handoffs(handoff_rows((0,0),reverse_second=True),[])==[]
    assert len(confirmed_main_handoffs(handoff_rows(reverse_second=True),[]))==1


def test_cut_gap_and_ambiguous_body_match_cannot_supply_handoff():
    from dance_highlight.services.observed_main import confirmed_main_handoffs
    assert confirmed_main_handoffs(handoff_rows(),[1])==[]
    assert confirmed_main_handoffs(handoff_rows(),None)==[]
    rows=handoff_rows();rows[1]['time']=.5
    assert confirmed_main_handoffs(rows,[])==[]
    rows=handoff_rows();rows[1]['features'].append({**rows[1]['features'][0],'index':2})
    assert confirmed_main_handoffs(rows,[])==[]
    for side,absent in [(0,1),(1,0)]:
        rows=handoff_rows()
        rows[side]['features']=[f for f in rows[side]['features'] if f['index']!=absent]
        assert confirmed_main_handoffs(rows,[])==[]


def test_nested_partial_duplicate_with_same_head_but_less_observed_torso_is_removed():
    from dance_highlight.services.observed_main import retained_bodies
    full=pose(200); partial=full.copy()
    partial[[6,11,12],2]=.1
    full[13:,2]=partial[13:,2]=.1
    boxes=[np.array([140.,60.,260.,550.]),np.array([145.,65.,255.,290.])]
    assert retained_bodies(boxes,[full,partial])==[0]
    # Different observed head means overlapping dancers, not a duplicate.
    partial[:5,0]+=20
    assert retained_bodies(boxes,[full,partial])==[0,1]


def test_camera_role_hides_occluded_body_instead_of_borrowing_a_foreground_face(monkeypatch):
    from dance_highlight.services import observed_main as m
    records=[record(i/10) for i in range(3)]
    monkeypatch.setattr(m,'collect_geometry',lambda *args:geometry(records))
    episode=dict(start_frame=0,end_frame=2,start_time=0.,end_time=.2,
                 visible_targets=[dict(frame=0,index=1),dict(frame=2,index=1)],
                 role_only_frames=[1],reason='stationary_camera_subject_behind_lateral_foreground')
    monkeypatch.setattr(m,'camera_focal_evidence',lambda *args:[episode])
    out,audit=refine_main_roles(records,'unused',10,SimpleNamespace(_detector=None),
                               SimpleNamespace(track_match_iou=.3,track_ttl_sec=.5))
    assert audit['reason']=='complete'
    assert out[1].main_id is None and out[1].main_bbox is None
    assert np.array_equal(out[0].main_bbox,records[0].person_bboxes[1])
    assert np.array_equal(out[2].main_bbox,records[2].person_bboxes[1])
    assert audit['camera_episodes'][0]['role_only_frames']==[1]
    assert not audit['handoffs']


def test_missing_face_window_uses_source_frames_at_fractional_fps(monkeypatch):
    from dance_highlight.services import observed_main as m
    for fps in (60., 60000/1001):
        records = [record(frame/fps) for frame in (0, 4, 8, 12)]
        rows, _, width, height = geometry(records)
        for row, frame in zip(rows, (0, 4, 8, 12), strict=True):
            row['frame'] = frame
            if frame < 8:
                row['features'][1].update(size=None, source='missing')
        monkeypatch.setattr(m, 'collect_geometry', lambda *args: (rows, [], width, height))
        out, audit = refine_main_roles(records, 'unused', fps, SimpleNamespace(_detector=None),
                                      SimpleNamespace(track_match_iou=.3, track_ttl_sec=.5))
        assert audit['reason'] == 'complete'
        assert all(np.array_equal(r.main_bbox, r.person_bboxes[1]) for r in out)


def test_missing_face_window_still_stops_at_source_cut_or_unobserved_extra_frame(monkeypatch):
    from dance_highlight.services import observed_main as m
    fps = 60000/1001
    for frames, cuts in [((0, 4, 8, 12), [10]), ((0, 4, 8, 13), [])]:
        records = [record(frame/fps) for frame in frames]
        rows, _, width, height = geometry(records)
        for row, frame in zip(rows, frames, strict=True):
            row['frame'] = frame
            if frame < 8:
                row['features'][1].update(size=None, source='missing')
        monkeypatch.setattr(m, 'collect_geometry', lambda *args: (rows, cuts, width, height))
        out, audit = refine_main_roles(records, 'unused', fps, SimpleNamespace(_detector=None),
                                      SimpleNamespace(track_match_iou=.3, track_ttl_sec=.5))
        assert audit['reason'] == 'complete'
        assert np.array_equal(out[0].main_bbox, out[0].person_bboxes[0])


def test_repeated_role_queries_reuse_same_frozen_pose_correspondence(monkeypatch):
    from collections import Counter
    from dance_highlight.services import observed_main as m
    records=[record(i/10) for i in range(12)]
    monkeypatch.setattr(m,'collect_geometry',lambda *args:geometry(records))
    raw=m.strict_pose_corresponding;calls=Counter()
    def counted(row,person,other):
        calls[(row['frame'],person['index'],other['frame'])]+=1
        return raw(row,person,other)
    monkeypatch.setattr(m,'strict_pose_corresponding',counted)
    out,audit=m.refine_main_roles(records,'unused',10,SimpleNamespace(_detector=None),SimpleNamespace(track_match_iou=.3,track_ttl_sec=.5))
    assert audit['reason']=='complete'
    assert all(np.array_equal(r.main_bbox,r.person_bboxes[1]) for r in out)
    assert max(calls.values())==1
