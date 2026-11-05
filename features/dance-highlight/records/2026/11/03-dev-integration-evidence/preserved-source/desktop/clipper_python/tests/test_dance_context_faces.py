from dataclasses import replace

import pytest

from test_dance_member_timeline import observation


@pytest.mark.parametrize('inventory_case',['complete','wrong_source','wrong_fps','partial','absent'])
def test_source_context_keeps_boundaries_without_unused_face_models(tmp_path,monkeypatch,inventory_case):
    import cv2
    import numpy as np
    from types import SimpleNamespace
    from dance_highlight.services import context_faces,face_models,camera_transitions
    path=tmp_path/'boundaries.avi'
    writer=cv2.VideoWriter(str(path),cv2.VideoWriter_fourcc(*'MJPG'),10.,(80,60))
    assert writer.isOpened()
    for i in range(20): writer.write(np.full((60,80,3),(0,0,40) if i<10 else (240,240,0),np.uint8))
    writer.release()
    records=[SimpleNamespace(t=i/10) for i in range(20)]
    def forbidden(*args,**kwargs):raise AssertionError('SAM-off source context must not load face models')
    monkeypatch.setattr(face_models,'ensure_face_models',forbidden)
    inventory=dict(reason='complete',source_path=str(path.resolve()),fps=10.,through_frame=19,
        cut_frames=[10],camera_transitions=[dict(frame=10,cut=True,color_candidate=True,proof='saved')])
    if inventory_case=='complete':
        monkeypatch.setattr(context_faces.cv2,'VideoCapture',forbidden)
    elif inventory_case=='wrong_source':inventory.update(source_path=str(tmp_path/'other.avi'),cut_frames=[5])
    elif inventory_case=='wrong_fps':inventory.update(fps=30.,cut_frames=[5])
    elif inventory_case=='partial':inventory.update(through_frame=4,cut_frames=[5])
    else:inventory=None
    cuts,audit=context_faces.collect_source_context(path,records,10.,source_inventory=inventory)
    assert audit['reason']=='complete'
    assert cuts==[10]
    assert [r['frame'] for r in audit['camera_transitions']]==[10]
    if inventory_case=='complete':assert audit['camera_transitions']==inventory['camera_transitions']


def test_context_seed_requires_two_models_same_shot_repetition_and_unique_body():
    from dance_highlight.services.context_faces import select_context_anchors
    def candidate(t, name='A', secondary='A', distance=.4, score=.99):
        row = replace(observation(t,name), frame_index=round(t*10),detector_score=score)
        return dict(name=name,secondary_name=secondary,distance=distance,observation=row)
    rows = [candidate(.1),candidate(.3),candidate(1.),candidate(1.2),
            candidate(2.,secondary='B'),candidate(2.2,secondary='B'),
            candidate(3.,distance=.58),candidate(3.2,distance=.58),
            candidate(4.,score=.85),candidate(4.2,score=.85)]
    # A camera transition separates 1.0 and 1.2, despite repeated names.
    cuts = [11]
    accepted = select_context_anchors(rows,cuts,10.)
    assert [(n,o.time_seconds) for n,o in accepted] == [('A',.1),('A',.3)]
    # Two simultaneous bodies claiming one identity cannot serve as anchors.
    duplicate = candidate(.1)
    duplicate['observation'] = replace(duplicate['observation'],track_id=99,body_bbox=(100.,0.,150.,90.))
    assert select_context_anchors([*rows[:2],duplicate],[],10.) == []


def test_context_collection_does_no_work_when_every_main_is_named():
    from dance_highlight.services.context_faces import collect_context_anchors
    from test_dance_mask_continuity import recovery_example
    original,records,_ = recovery_example()
    original['decisions'][1] = replace(original['decisions'][0])
    anchors,cuts,audit = collect_context_anchors('must-not-open',records,10.,original,None,None,{})
    assert not anchors and not cuts
    assert audit['reason'] == 'no_unknown_main'


def test_nonmain_face_in_same_shot_can_name_only_its_verified_main_interval():
    from dance_highlight.services.mask_continuity import recover_mask_names
    from test_dance_mask_continuity import recovery_example
    original,records,_ = recovery_example()
    # Context B is not in the main-face evidence or main-name neighborhood.
    contexts = [('B',replace(observation(t,'B'),frame_index=round(t*10),detector_score=.99))
                for t in (4.2,4.5)]
    calls = []
    def verify(anchor,path,targets):
        calls.append((anchor.frame_index,targets))
        return dict(accepted=True,reason='confirmed_visual_path',support_frames=targets)
    result,audit = recover_mask_names(original,records,'unused',10.,[],verify_track=verify,
                                     context_anchors=contexts,cut_frames=[30])
    assert calls == [(42,list(range(30,40)))]
    assert [(s.start,s.end,d.reference_id) for s,d in zip(result['segments'],result['decisions'])] == [
        (0.,2.,'A'),(2.,3.,None),(3.,4.,'B'),(4.,6.,'A')]
    assert audit['recovered_seconds'] == pytest.approx(1.)
    assert result['anchors'] == original['anchors']
    assert all(n is None for evidence in result['evidence'] for row,n in evidence if 2<=row.time_seconds<4)


def test_context_face_from_another_shot_is_not_sent_to_tracker():
    from dance_highlight.services.mask_continuity import recover_mask_names
    from test_dance_mask_continuity import recovery_example
    original,records,_ = recovery_example()
    contexts=[('B',replace(observation(t,'B'),frame_index=round(t*10),detector_score=.99)) for t in (4.2,4.5)]
    def forbidden(*args):raise AssertionError('cross-shot context must not reach inference')
    result,audit=recover_mask_names(original,records,'unused',10.,[],verify_track=forbidden,
                                    context_anchors=contexts,cut_frames=[40])
    assert result is original and audit['recovered_seconds']==0.


@pytest.mark.parametrize('case',['distinct','duplicate_main','decode_error','reuse_complete','reject_wrong_source','reject_partial_inventory'])
def test_context_source_samples_other_body_and_keeps_gallery_frozen(tmp_path,monkeypatch,case):
    import cv2
    import numpy as np
    from types import SimpleNamespace
    from dance_highlight.services import context_faces,face_models
    from dance_highlight.services.segment import FrameRec,Segment
    from dance_highlight.services.reference_matcher import SegmentReferenceDecision
    from test_dance_member_timeline import Matcher
    refs={}
    for name,channel in [('A',0),('B',2)]:
        refs[name]=[]
        for i,value in enumerate((160,200)):
            image=np.zeros((100,100,3),np.uint8);image[:,:,channel]=value
            path=tmp_path/f'{name}-{i}.png';assert cv2.imwrite(str(path),image);refs[name].append(path)
    video=tmp_path/'source.avi';writer=cv2.VideoWriter(str(video),cv2.VideoWriter_fourcc(*'MJPG'),10,(100,100))
    assert writer.isOpened()
    for _ in range(20):writer.write(np.full((100,100,3),(0,0,200),np.uint8))
    writer.release()
    if case=='decode_error':
        class BrokenCapture:
            def __init__(self,*_):pass
            def isOpened(self):return True
            def get(self,_):return 10.
            def read(self):raise cv2.error('decoder failed')
            def release(self):pass
        monkeypatch.setattr(cv2,'VideoCapture',BrokenCapture)
    model=tmp_path/'sface.onnx';model.write_bytes(b'test controls inference')
    monkeypatch.setattr(face_models,'ensure_face_models',lambda **_: {'opencv-sface-face-recognition':model})
    class Recognizer:
        def alignCrop(self,image,face):return image
        def feature(self,image):
            v=np.zeros((1,128),np.float32);v[0,0 if image[:,:,0].mean()>image[:,:,2].mean() else 1]=1;return v
    monkeypatch.setattr(cv2,'FaceRecognizerSF',SimpleNamespace(create=lambda *_:Recognizer()))
    candidate=SimpleNamespace(face_bbox=(5.,5.,20.,20.),landmarks=((7.,7.),)*5,
                              detector_score=.99,embedding=np.array([0.,1.,0.]),quality=1.,
                              detection_rotation_degrees=30.)
    calls=[]
    class Face:
        def get_face_embedding_candidate(self,_):return candidate
        def expand_face_roi(self,body,w,h):return tuple(map(int,body))
        def _inspect_face(self,image,**kwargs):
            assert kwargs['require_pose'] is True
            calls.append(tuple(kwargs['source_body']))
            if kwargs['source_body'][0]==0 and case in ('distinct','reuse_complete','reject_wrong_source','reject_partial_inventory'):
                return SimpleNamespace(**(vars(candidate)|{'embedding':np.array([1.,0.,0.])})),None
            return candidate,None
    left=np.array([0.,0.,45.,95.],np.float32);right=np.array([50.,0.,95.,95.],np.float32)
    records=[FrameRec(i/10,1,left,False,person_bboxes=[left,right],scene_kind='main') for i in range(20)]
    output=dict(segments=[Segment('main',1,0.,2.,[])],
                decisions=[SegmentReferenceDecision(None,'unmatched','test')])
    inventory=None
    if case in ('reuse_complete','reject_wrong_source','reject_partial_inventory'):
        inventory=dict(reason='complete',source_path=str(video.resolve()),fps=10.,through_frame=19,
                       cut_frames=[],camera_transitions=[])
        if case=='reuse_complete':
            from dance_highlight.services import camera_transitions
            def forbid_rescan(*_):raise AssertionError('verified source cuts must be reused')
            monkeypatch.setattr(camera_transitions,'classify_transition',forbid_rescan)
        elif case=='reject_wrong_source':
            inventory['source_path']=str(tmp_path/'different.avi');inventory['cut_frames']=[4,8,12,16]
        else:
            inventory['through_frame']=5;inventory['cut_frames']=[4]
    anchors,cuts,audit=context_faces.collect_context_anchors(video,records,10.,output,Face(),Matcher(),refs,source_inventory=inventory)
    if case=='decode_error':
        assert not anchors and audit['reason']=='context_source_failed'
        return
    assert audit['reason']=='complete' and not cuts
    if case=='duplicate_main':
        assert not anchors
        return
    assert len(anchors)>=4 and all(name=='B' for name,_ in anchors)
    assert set(calls)=={tuple(left),tuple(right)}
    assert all(row.track_id==-2 and row.face_bbox[0]==55. for _,row in anchors)
    import json
    saved = json.loads(json.dumps(audit))
    assert saved['reason']=='complete'
    assert all(row['detection_rotation_degrees']==30. for row in saved['anchors'])
    assert all(row['landmarks']==[[57.,7.]]*5 for row in saved['anchors'])
    assert all(row['detector_score']==.99 for row in saved['anchors'])
    assert set(output)=={'segments','decisions'}


def test_context_optional_model_failure_keeps_original_analysis(monkeypatch):
    from dance_highlight.services import context_faces,face_models
    from test_dance_mask_continuity import recovery_example
    original,records,_=recovery_example()
    def unavailable(**_):raise OSError('offline')
    monkeypatch.setattr(face_models,'ensure_face_models',unavailable)
    anchors,cuts,audit=context_faces.collect_context_anchors('unused',records,10.,original,None,None,{'A':['photo']})
    assert not anchors and not cuts
    assert audit['reason']=='context_model_unavailable'
    assert original['decisions'][1].reference_id is None


@pytest.mark.parametrize('start,cuts,expected_start',[(2.05,[20.8],2.08),(2.,[29.5,29.8],2.98)])
def test_context_label_stays_inside_exact_cut_bounds_between_pose_samples(start,cuts,expected_start):
    from dance_highlight.services.mask_continuity import recover_mask_names
    from test_dance_mask_continuity import recovery_example
    original,records,_=recovery_example()
    original['segments'][1]=replace(original['segments'][1],start=start)
    contexts=[('B',replace(observation(t,'B'),frame_index=round(t*10),detector_score=.99)) for t in (4.2,4.5)]
    result,_=recover_mask_names(original,records,'unused',10.,[],
        verify_track=lambda a,p,t:dict(accepted=True,reason='confirmed_visual_path',support_frames=t),
        context_anchors=contexts,cut_frames=cuts)
    named=[s for s,d in zip(result['segments'],result['decisions']) if d.reference_id=='B']
    assert named[0].start==pytest.approx(expected_start)
    assert any(s.start==start and s.end==pytest.approx(expected_start) and d.reference_id is None
               for s,d in zip(result['segments'],result['decisions']))


@pytest.mark.parametrize('other_owner',[0,1,'unowned','missing'])
def test_context_trace_checks_other_direct_identity_on_the_same_body(other_owner):
    import numpy as np
    from dance_highlight.services.mask_continuity import recover_mask_names
    from test_dance_mask_continuity import recovery_example
    original,records,anchors=recovery_example()
    contexts=[('B',replace(observation(t,'B'),frame_index=round(t*10),detector_score=.99)) for t in (4.8,5.1)]
    # A's directly confirmed body lies between context B and the target.
    if other_owner==1:
        for i in (42,45):
            records[i]=replace(records[i],person_bboxes=[np.array([100,10,140,90]),records[i].main_bbox])
    def verify(anchor,path,targets):
        if anchor.frame_index!=48:
            return dict(accepted=False,reason='inconsistent_visual_path')
        trace=[dict(frame=round(r.t*10),forward=() if other_owner=='unowned' and round(r.t*10) in (42,45) else (0,),
                    reverse=() if other_owner=='unowned' and round(r.t*10) in (42,45) else (0,)) for r in path
               if not (other_owner=='missing' and round(r.t*10) in (42,45))]
        return dict(accepted=True,reason='confirmed_visual_path',support_frames=targets,trace=trace)
    result,audit=recover_mask_names(original,records,'unused',10.,anchors,verify_track=verify,
                                    context_anchors=contexts)
    if other_owner!=1:
        assert result is original
        assert any(a['reason']=='conflicting_direct_face_anchor'
                   for c in audit['candidates'] for a in c['attempts'])
    else:
        assert any(d.reference_id=='B' for d in result['decisions'])
