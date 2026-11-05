"""Independent identity per shot; no body identity propagation across cuts."""
from dataclasses import replace
from types import SimpleNamespace
import copy

import cv2
import numpy as np
import pytest

from dance_highlight.services.face_evidence import FaceObservation
from dance_highlight.services.reference_matcher import SegmentReferenceDecision
from dance_highlight.services.segment import FrameRec, Segment


class FrozenMatcher:
    def match(self, row, segment, scope):
        vector = row.embedding
        name = 'A' if vector[0] > .99 else 'B' if vector[1] > .99 else None
        return SimpleNamespace(reference_id=name)


def fixture(tmp_path):
    fps = 20.
    path = tmp_path/'shots.avi'
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*'MJPG'),fps,(200,120))
    assert writer.isOpened()
    rows, records, roles, secondary = [], [], [], []
    for f in range(60):
        box = np.array([25.,10.,75.,110.]) if f < 20 else np.array([110.,10.,160.,110.])
        image = np.full((120,200,3),(20,40,20) if f<20 else (200,150,30),np.uint8)
        cv2.rectangle(image,tuple(box[:2].astype(int)),tuple(box[2:].astype(int)),(30,50,190),-1)
        writer.write(image)
        if f % 2: continue
        named = 10<=f<=18 or 32<=f<=38
        embedding = np.array([1.,0.,0.],np.float32) if f<20 else np.array([.8,0.,.6],np.float32)
        row = FaceObservation(f,f/fps,1 if f<20 else 9,tuple(box),tuple(box),
            face_bbox=tuple([box[0]+10,15,box[0]+30,35]) if named else None,
            embedding=embedding if named else None,detector_score=.95 if named else 0.,
            association='confirmed' if named else 'unassigned',failure=None if named else 'no_detection')
        rows.append(row)
        records.append(FrameRec(f/fps,row.track_id,box,False,person_bboxes=[box],
            scene_kind='main',scene_reason='main_eligible_composition',
            candidate_main_id=row.track_id,candidate_main_bbox=box))
        roles.append(dict(frame=f,box=box.tolist(),reason='measured_face_composition',features=[dict(index=0,box=box.tolist(),source='detected',size=20.,x=float((box[0]+box[2])/2))]))
        if 32<=f<=38:secondary.append(dict(frame_index=f,name='A',reason='secondary_reference_match',distance=.5,margin=.1))
    writer.release()
    segments=[Segment('main',None,a,b,[(o.time_seconds,np.array(o.body_bbox),o.track_id) for o in rows if a<=o.time_seconds<b]) for a,b in [(0.,1.1),(1.1,1.5),(1.5,3.)]]
    output=dict(segments=segments,decisions=[SegmentReferenceDecision(n,'matched' if n else 'unmatched','original') for n in ['A',None,'A']],labels=[1,None,2],previews=[[],[],[]],preview_sources=[({}, {}) for _ in segments],evidence=[[(o,None) for o in rows if s.start<=o.time_seconds<s.end] for s in segments],accurate_indices=[],anchors=[],fallback_names={})
    return dict(output=output,frame_records=records,observations=rows,joint_matches={},secondary_matches=secondary,matcher=FrozenMatcher(),video_path=path,fps=fps,sample_step=2,cut_frames=[20],handoffs=[],role_observations=roles,group_segments=[])


def run(args):
    from dance_highlight.services.shot_member_gaps import recover_shot_member_gaps
    return recover_shot_member_gaps(**args)


def test_same_member_is_independently_proved_per_shot_with_different_body_tracks(tmp_path):
    args=fixture(tmp_path);original=args['output'];before=copy.deepcopy(original)
    result,audit=run(args)
    assert [(s.start,s.end,d.reference_id) for s,d in zip(result['segments'],result['decisions'])]==[(0.,3.,'A')]
    assert audit['recovered_seconds']==pytest.approx(.4)
    assert len(audit['recoveries'])==1
    proof=audit['recoveries'][0]
    assert proof['cut_frames']==[20]
    assert all(len(s['seed_frames'])==2 for s in proof['shots'])
    assert all(not (min(s['source_frames'])<20<=max(s['source_frames'])) for s in proof['shots'] if s['source_frames'])
    assert len(original['segments'])==3
    assert [d.reference_id for d in original['decisions']]==['A',None,'A']
    assert original['anchors']==result['anchors']==before['anchors']==[]
    assert all(n is None for o,n in result['evidence'][0])


@pytest.mark.parametrize('case',['uncut','one_face','adjacent_faces','window_faces','video_faces',
    'group_record','separate_group','missing_row','missing_record','missing_role','competitor','handoff',
    'different_neighbors','one_sided','new_intermediate_shot','competing_face','repeated_alien'])
def test_unproved_or_competing_intervals_remain_unknown(tmp_path,case):
    args=fixture(tmp_path)
    if case=='uncut':args['cut_frames']=[]
    elif case=='one_face':args['secondary_matches']=args['secondary_matches'][:1]
    elif case=='adjacent_faces':args['secondary_matches']=args['secondary_matches'][:2]
    elif case in ('window_faces','video_faces'):
        for m in args['secondary_matches']:m['reason']='secondary_reference_window_match' if case=='window_faces' else 'secondary_video_match'
    elif case=='group_record':args['frame_records'][12].scene_kind='group'
    elif case=='separate_group':args['group_segments']=[Segment('group',None,1.2,1.3,[])]
    elif case=='missing_row':args['observations']=[o for o in args['observations'] if o.frame_index!=24]
    elif case=='missing_record':args['frame_records']=[r for r in args['frame_records'] if r.t!=1.2]
    elif case=='missing_role':args['role_observations']=[r for r in args['role_observations'] if r['frame']!=24]
    elif case=='competitor':
        r=args['frame_records'][12];r.person_bboxes=[r.main_bbox,r.main_bbox.copy()]
    elif case=='handoff':args['handoffs']=[dict(frame=24,time=1.2,previous_frame=22,previous_time=1.1)]
    elif case=='different_neighbors':args['output']['decisions'][-1]=SegmentReferenceDecision('B','matched','original')
    elif case=='one_sided':args['output']['decisions'][0]=SegmentReferenceDecision(None,'unmatched','original')
    elif case=='new_intermediate_shot':args['cut_frames']=[20,25,27]
    elif case in ('competing_face','repeated_alien'):
        args['observations']=[replace(o,face_bbox=(120.,15.,140.,35.),embedding=np.array([0.,1.,0.] if case=='competing_face' else [0.,0.,1.],np.float32),detector_score=.95,association='confirmed',failure=None) if o.frame_index in ((24,) if case=='competing_face' else (22,24,26,28)) else o for o in args['observations']]
    result,audit=run(args)
    assert result is args['output']
    assert audit['recovered_seconds']==0.


def expired_prefix_fixture(tmp_path):
    args=fixture(tmp_path)
    args['secondary_matches']=[dict(frame_index=f,name='A',reason='secondary_reference_match') for f in (36,38,40)]
    args['observations']=[replace(o,face_bbox=(120.,15.,140.,35.),embedding=np.array([.8,0.,.6],np.float32),detector_score=.95,association='confirmed',failure=None) if o.frame_index==40 else o for o in args['observations']]
    args['output']['preview_sources'][1]=({22:b'prefix',24:b'suffix'}, {})
    return args


def test_expired_unknown_prefix_does_not_discard_a_separately_proved_suffix(tmp_path):
    args=expired_prefix_fixture(tmp_path); original=copy.deepcopy(args['output'])
    result,audit=run(args)
    assert [(s.start,s.end,d.reference_id) for s,d in zip(result['segments'],result['decisions'])]==[
        (0.,1.1,'A'), (1.1,1.2,None), (1.2,3.,'A')]
    assert audit['recovered_seconds']==pytest.approx(.3)
    assert audit['recoveries'][0]['start']==pytest.approx(1.2)
    assert audit['recoveries'][0]['unresolved_prefix']==[1.1,1.2]
    assert all(o.time_seconds<1.2 and n is None for o,n in result['evidence'][1])
    assert set(result['preview_sources'][1][0])=={22}
    assert 22 not in result['preview_sources'][2][0]
    assert 24 in result['preview_sources'][2][0]
    assert [(s.start,s.end) for s in args['output']['segments']]==[(s.start,s.end) for s in original['segments']]
    assert args['output']['fallback_names']==result['fallback_names']=={}


@pytest.mark.parametrize('veto',['group','handoff','role','competing_face','source','budget','multi_shot'])
def test_suffix_recovery_keeps_every_existing_proof_and_work_limit(tmp_path,monkeypatch,veto):
    from dance_highlight.services import shot_member_gaps as module
    args=expired_prefix_fixture(tmp_path)
    if veto=='group':args['group_segments']=[Segment('group',None,1.2,1.3,[])]
    if veto=='handoff':args['handoffs']=[dict(time=1.3,previous_time=1.2)]
    if veto=='role':args['role_observations']=[r for r in args['role_observations'] if r['frame']!=24]
    if veto=='competing_face':
        args['observations']=[replace(o,face_bbox=(120.,15.,140.,35.),embedding=np.array([0.,1.,0.]),
            detector_score=.95,association='confirmed',failure=None) if o.frame_index==24 else o
            for o in args['observations']]
    if veto=='source':monkeypatch.setattr(module._BoundedSource,'check',lambda *a:'visual_cut')
    if veto=='budget':monkeypatch.setattr(module,'MAX_SOURCE_PATHS',0)
    if veto=='multi_shot':args['cut_frames']=[20,27]
    result,audit=run(args)
    assert result is args['output']
    assert audit['recovered_seconds']==0.


def test_proved_suffix_across_existing_unknown_pieces_keeps_the_prefix_and_all_evidence(tmp_path):
    args=expired_prefix_fixture(tmp_path); out=args['output']; old=copy.deepcopy(out)
    for key in ('segments','decisions','labels','evidence','previews','preview_sources'):
        out[key]=old[key][:1]+[old[key][1],copy.deepcopy(old[key][1])]+old[key][2:]
    out['segments'][1]=replace(old['segments'][1],end=1.3)
    out['segments'][2]=replace(old['segments'][1],start=1.3)
    for i in (1,2):
        s=out['segments'][i]
        out['evidence'][i]=[(o,n) for o,n in old['evidence'][1] if s.start<=o.time_seconds<s.end]
    result,audit=run(args)
    assert [(s.start,s.end,d.reference_id) for s,d in zip(result['segments'],result['decisions'])]==[
        (0.,1.1,'A'),(1.1,1.2,None),(1.2,3.,'A')]
    actual=[o.frame_index for part in result['evidence'] for o,_ in part]
    assert actual==[o.frame_index for part in old['evidence'] for o,_ in part]
    assert audit['recovered_seconds']==pytest.approx(.3)


def test_an_internal_source_support_hole_is_never_trimmed_or_filled(tmp_path):
    args=fixture(tmp_path);out=args['output']
    out['segments'][1]=replace(out['segments'][1],end=2.8)
    out['segments'][2]=replace(out['segments'][2],start=2.8)
    for i,s in enumerate(out['segments']):
        out['evidence'][i]=[(o,None) for o in args['observations'] if s.start<=o.time_seconds<s.end]
    seeds=(24,28,54,58)
    args['secondary_matches']=[dict(frame_index=f,name='A',reason='secondary_reference_match') for f in seeds]
    args['observations']=[replace(o,face_bbox=(120.,15.,140.,35.),embedding=np.array([.8,0.,.6]),
        detector_score=.95,association='confirmed',failure=None) if o.frame_index in seeds else o
        for o in args['observations']]
    result,audit=run(args)
    assert result is out
    assert audit['candidates'][0]['reason']=='same_shot_support_expired'
    assert audit['recovered_seconds']==0.


def test_decoder_seek_failure_cannot_prove_shot(tmp_path,monkeypatch):
    from dance_highlight.services import shot_member_gaps as module
    args=fixture(tmp_path)
    class BadCapture:
        def isOpened(self):return True
        def get(self,prop):return args['fps'] if prop==cv2.CAP_PROP_FPS else 999
        def set(self,*args):return False
        def release(self):pass
    monkeypatch.setattr(module.cv2,'VideoCapture',lambda _:BadCapture())
    result,audit=run(args)
    assert result is args['output']
    assert audit['recovered_seconds']==0.


def test_missing_both_pose_and_face_at_new_interval_boundary_cannot_hide_cadence(tmp_path):
    args=fixture(tmp_path)
    args['observations']=[o for o in args['observations'] if o.frame_index not in (20,22)]
    args['frame_records']=[r for r in args['frame_records'] if round(r.t*20) not in (20,22)]
    result,audit=run(args)
    assert result is args['output']
    assert audit['recovered_seconds']==0.


def test_unknown_source_edge_must_be_inside_a_measured_shot_path(tmp_path):
    args=fixture(tmp_path)
    args['output']['segments'][0]=replace(args['output']['segments'][0],end=1.05)
    args['output']['segments'][1]=replace(args['output']['segments'][1],start=1.05)
    args['observations']=[o for o in args['observations'] if o.frame_index!=20]
    args['frame_records']=[r for r in args['frame_records'] if round(r.t*20)!=20]
    result,audit=run(args)
    assert result is args['output']
    assert audit['recovered_seconds']==0.


def test_a_failed_body_transition_is_not_reread_for_larger_seed_paths(tmp_path):
    args=fixture(tmp_path)
    r=args['frame_records'][12];r.person_bboxes=[r.main_bbox,r.main_bbox+[1.,0.,1.,0.]]
    result,audit=run(args)
    assert result is args['output']
    assert audit['source_budget']['paths_used']==1
    assert audit['source_budget']['superset_cache_hits']>=1


def test_many_candidates_have_a_deterministic_video_source_budget(tmp_path,monkeypatch):
    from dance_highlight.services import shot_member_gaps as module
    args=fixture(tmp_path);base=copy.deepcopy(args);copies=24
    args['observations']=[];args['frame_records']=[];args['role_observations']=[]
    args['secondary_matches']=[];args['cut_frames']=[]
    keys=('segments','decisions','labels','evidence','previews','preview_sources')
    args['output']={**base['output'],**{key:[] for key in keys}}
    for j in range(copies):
        shift=j*3.;offset=j*60
        args['observations'].extend(replace(o,frame_index=o.frame_index+offset,time_seconds=o.time_seconds+shift) for o in base['observations'])
        args['frame_records'].extend(replace(r,t=r.t+shift) for r in base['frame_records'])
        args['role_observations'].extend(dict(r,frame=r['frame']+offset) for r in base['role_observations'])
        args['secondary_matches'].extend(dict(r,frame_index=r['frame_index']+offset) for r in base['secondary_matches'])
        args['cut_frames'].append(20+offset)
        args['output']['segments'].extend(replace(s,start=s.start+shift,end=s.end+shift,bboxes=[]) for s in base['output']['segments'])
        for key in keys[1:]:args['output'][key].extend(copy.deepcopy(base['output'][key]) if key!='evidence' else [[],[],[]])
    class Source:
        def __init__(self):self.position=0;self.reads=0;self.seeks=0
        def isOpened(self):return True
        def get(self,prop):return 20. if prop==cv2.CAP_PROP_FPS else self.position
        def set(self,prop,value):self.position=int(value);self.seeks+=1;return True
        def read(self):
            self.position+=1;self.reads+=1
            return True,np.full((120,200,3),70,np.uint8)
        def release(self):pass
    source=Source();monkeypatch.setattr(module.cv2,'VideoCapture',lambda _:source)
    result,audit=run(args)
    assert source.seeks<=12
    assert source.reads<=240
    assert audit['source_budget']['paths_used']==source.seeks
    assert audit['source_budget']['frames_read']==source.reads
    assert any(c.get('budget_reason') for c in audit['candidates'])
    assert 0<audit['recovered_seconds']<copies*.4


@pytest.mark.parametrize('case',['no_measured_face_keep_previous_selection','awaiting_sustained_composition',
    'missing_feature','stale_feature','wrong_geometry','duplicate_feature','contradictory_scene'])
def test_new_unknown_requires_fresh_original_selected_role(tmp_path,case):
    args=fixture(tmp_path);role=next(r for r in args['role_observations'] if r['frame']==24)
    if case in ('no_measured_face_keep_previous_selection','awaiting_sustained_composition'):role['reason']=case
    elif case=='missing_feature':role['features']=[]
    elif case=='stale_feature':role['features'][0]['source']='pose'
    elif case=='wrong_geometry':role['features'][0]['box']=[0.,0.,20.,20.]
    elif case=='duplicate_feature':role['features'].append(dict(role['features'][0]))
    elif case=='contradictory_scene':args['frame_records'][12].scene_reason='distributed_full_body_ensemble'
    result,audit=run(args)
    assert result is args['output']
    assert audit['recovered_seconds']==0.


@pytest.mark.parametrize('handoff',[
    dict(frame=22,time=1.1,previous_frame=20,previous_time=1.),
    dict(frame=30,time=1.5,previous_frame=28,previous_time=1.4),
    dict(frame=32,time=1.6,previous_frame=20,previous_time=1.),
    dict(frame=22,time=1.1),
    dict(frame=32,time=1.6,previous_frame=20),
])
def test_confirmed_handoff_brackets_include_new_join_boundaries(tmp_path,handoff):
    args=fixture(tmp_path);args['handoffs']=[handoff]
    result,audit=run(args)
    assert result is args['output']
    assert audit['recovered_seconds']==0.


def test_exact_source_paths_cache_but_median_failures_do_not_poison_supersets(tmp_path,monkeypatch):
    from dance_highlight.services import shot_member_gaps as module
    args=fixture(tmp_path)
    class Source:
        def __init__(self):self.position=0
        def isOpened(self):return True
        def get(self,prop):return 20. if prop==cv2.CAP_PROP_FPS else self.position
        def set(self,prop,value):self.position=int(value);return True
        def read(self):
            value={20:0,21:40,22:0,23:40,24:40,25:40,26:40,27:0,28:40,29:0,30:40}[self.position]
            self.position+=1
            image=np.full((120,200,3),value,np.uint8)
            cv2.rectangle(image,(110,10),(160,110),(70,70,70),-1)
            return True,image
        def release(self):pass
    monkeypatch.setattr(module.cv2,'VideoCapture',lambda _:Source())
    source=module._BoundedSource(args['video_path'],20.)
    rows={o.frame_index:o for o in args['observations']}
    records={round(r.t*20):r for r in args['frame_records']}
    try:
        assert source.check([22,24,26],rows,records,2)=='isolated_visual_change'
        assert source.check([22,24,26],rows,records,2)=='isolated_visual_change'
        assert source.check([20,22,24,26,28,30],rows,records,2) is None
        assert source.audit['paths_used']==2
        assert source.audit['frames_read']==16
        assert source.audit['exact_cache_hits']==1
        assert source.audit['superset_cache_hits']==0
    finally:source.close()


def test_source_budget_counts_extra_reads_from_pixel_validation(monkeypatch):
    from dance_highlight.services import shot_member_gaps as module
    calls=[]
    class Source:
        def __init__(self): self.position=0
        def isOpened(self): return True
        def get(self,prop): return 20. if prop==cv2.CAP_PROP_FPS else self.position
        def read(self):
            calls.append(self.position)
            self.position+=1
            return True,np.zeros((2,2,3),np.uint8)
        def release(self): pass
    def additional_pixel_reads(source,*_args):
        for _ in range(3):
            ok,_=source.read()
            if not ok: return 'source_frame_unavailable'
        return None
    monkeypatch.setattr(module,'MAX_SOURCE_FRAMES',2)
    monkeypatch.setattr(module.cv2,'VideoCapture',lambda _:Source())
    monkeypatch.setattr(module,'_check_source_chain',additional_pixel_reads)
    source=module._BoundedSource('unused',20.)
    try:
        assert source.check([0,1],{0:None,1:None},{},1)=='source_frame_budget_exhausted'
        assert calls==[0,1]
        assert source.audit['frames_read']==2
    finally: source.close()


@pytest.mark.parametrize('start',[.91,.95,.99])
def test_new_time_before_cut_without_a_sampled_row_is_not_named_shot_evidence(tmp_path,start):
    args=fixture(tmp_path)
    args['output']['segments'][0]=replace(args['output']['segments'][0],end=start)
    args['output']['segments'][1]=replace(args['output']['segments'][1],start=start)
    result,audit=run(args)
    assert result is args['output']
    assert audit['recovered_seconds']==0.
    assert audit['source_budget']['frames_read']==0
