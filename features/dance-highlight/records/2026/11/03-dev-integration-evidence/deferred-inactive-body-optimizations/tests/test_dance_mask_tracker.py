import cv2
import pytest
import numpy as np
from dance_highlight.services.mask_tracker import head_owners


@pytest.mark.parametrize('bad_frame', [None, 3, 1])
def test_reverse_failure_stops_inference_and_closes_source(monkeypatch, bad_frame):
    from dance_highlight.services import mask_tracker as module
    from dance_highlight.services.face_evidence import FaceObservation
    from dance_highlight.services.segment import FrameRec
    image = np.zeros((100, 100, 3), np.uint8)
    mask = np.zeros((100, 100), bool); mask[:, :50] = True
    box = np.array([0., 0., 50., 100.])
    head = np.array([[20., 20., .9], [30., 20., .9]])
    records = [FrameRec(i/10., 1, box, False, person_bboxes=[box],
                       person_head_keypoints=[head]) for i in range(5)]
    anchor = FaceObservation(0, 0., 1, tuple(box), tuple(box), face_bbox=(10., 10., 40., 30.))
    tracker = module.MaskTracker.__new__(module.MaskTracker)
    tracker.source = 'unused'; tracker.fps = 10.; tracker.on_progress = None
    tracker._cuts = lambda *args: set()
    closed, inferred = [], []
    class Capture:
        def __init__(self, *args): pass
        def isOpened(self): return True
        def get(self, prop): return 10.
        def release(self): closed.append('capture')
    monkeypatch.setattr(module.cv2, 'VideoCapture', Capture)
    def masks(cap, rows, **kwargs):
        reverse = 'masks' in kwargs
        try:
            for record in rows:
                frame = round(record.t*10)
                if reverse: inferred.append(frame)
                current = ~mask if reverse and frame == bad_frame else mask
                yield frame, image, current
        finally:
            closed.append('reverse' if reverse else 'forward')
    tracker._masks = masks
    result = tracker(anchor, records, [1, 2, 3, 4])
    assert result['accepted'] is (bad_frame is None)
    if bad_frame is None:
        assert result['support_frames'] == [1, 2, 3, 4]
        assert inferred == [4, 3, 2, 1, 0]
    else:
        assert result['reason'] == 'inconsistent_visual_path'
        assert inferred == list(range(4, bad_frame-1, -1))
    assert closed == ['forward', 'reverse', 'capture']


def test_mask_owner_requires_two_confident_head_points_and_unique_body():
    mask = np.zeros((100,100),bool); mask[10:40,10:40] = True
    heads = [np.array([[20,20,.9],[25,25,.9],[30,30,.1]]),np.array([[70,70,.9],[80,80,.9]])]
    assert head_owners(mask,heads) == (0,)
    assert head_owners(mask,[heads[0],heads[0]]) == (0,1)
    assert head_owners(mask,[heads[0][:1]]) == ()


def test_multiple_camera_cuts_between_pose_samples_are_not_endpoint_proof(monkeypatch):
    from dance_highlight.services import mask_tracker as module
    from dance_highlight.services.face_evidence import FaceObservation
    from dance_highlight.services.segment import FrameRec
    image=np.zeros((100,100,3),np.uint8);mask=np.ones((100,100),bool)
    box=np.array([10.,10.,90.,90.]);head=np.array([[30.,20.,.9],[50.,20.,.9]])
    records=[FrameRec(i/100.,1,box,False,person_bboxes=[box],person_head_keypoints=[head]) for i in (0,10,20,30)]
    anchor=FaceObservation(0,0.,1,tuple(box),tuple(box),face_bbox=(20.,10.,60.,30.))
    tracker=module.MaskTracker.__new__(module.MaskTracker);tracker.source='unused';tracker.fps=100.;tracker.on_progress=None
    class Capture:
        def __init__(self,*args):pass
        def isOpened(self):return True
        def get(self,prop):return 100.
        def release(self):pass
    monkeypatch.setattr(module.cv2,'VideoCapture',Capture)
    tracker._cuts=lambda *args: {3,7}
    tracker._masks=lambda cap,rows,**kwargs: ((round(r.t*100),image,mask) for r in rows)
    result=tracker(anchor,records,[10,20,30])
    assert not result['accepted']
    assert result['reason']=='multiple_unobserved_camera_transitions'


@pytest.mark.parametrize('reverse', [False,True])
def test_later_multiple_cuts_do_not_hide_an_earlier_main_change(monkeypatch,reverse):
    from dance_highlight.services import mask_tracker as module
    from dance_highlight.services.face_evidence import FaceObservation
    from dance_highlight.services.segment import FrameRec
    box=np.array([0.,0.,50.,100.]);other=box+[50.,0.,50.,0.]
    head=np.array([[20.,20.,.9],[30.,20.,.9]])
    frames=[0,10,20,30,40]
    if reverse:frames.reverse()
    stop=20
    records=[FrameRec(i/100.,1,other if i==stop else box,False,
        person_bboxes=[box,other],person_head_keypoints=[head,head+[50.,0.,0.]]) for i in frames]
    anchor=FaceObservation(frames[0],frames[0]/100.,1,tuple(box),tuple(box),face_bbox=(10.,10.,40.,30.))
    tracker=module.MaskTracker.__new__(module.MaskTracker)
    tracker.source='unused';tracker.fps=100.;tracker.on_progress=None
    class Capture:
        def __init__(self,*args):pass
        def isOpened(self):return True
        def get(self,prop):return 100.
        def release(self):pass
    monkeypatch.setattr(module.cv2,'VideoCapture',Capture)
    tracker._cuts=lambda *args:{13,17} if reverse else {23,27}
    mask=np.zeros((100,100),bool);mask[:,:50]=True
    image=np.zeros((100,100,3),np.uint8)
    tracker._masks=lambda cap,rows,**kwargs:((round(r.t*100),image,mask) for r in rows)
    result=tracker(anchor,records,frames[1:])
    # Report the first actual failure from this anchor. Prefix recovery can
    # then rerun both directions without reaching the later unobserved cuts.
    assert result['reason']=='unconfirmed_main_ownership'
    assert result['frame']==20


@pytest.mark.parametrize('seek_result,reported', [(False,0.),(True,0.),(True,20.5)])
def test_source_position_must_match_requested_frame(seek_result,reported):
    from dance_highlight.services.mask_tracker import MaskTracker
    class Capture:
        position=50.
        def get(self,_):return self.position
        def set(self,*args):self.position=reported;return seek_result
        def read(self):raise AssertionError('must reject the wrong source position before reading')
    with pytest.raises(ValueError,match='source_(seek_failed|position_mismatch)'):
        MaskTracker._read(Capture(),20)


def test_failed_or_short_source_read_is_not_visual_evidence():
    from dance_highlight.services.mask_tracker import MaskTracker
    class Capture:
        def get(self,_):return 20.
        def read(self):return False,None
    with pytest.raises(ValueError,match='source_frame_unavailable'):
        MaskTracker._read(Capture(),20)


@pytest.mark.parametrize('case',['confirmed','no_faces','opposing_name','outside_path','wrong_face_body','missing_reverse_owner','changed_foreground'])
def test_photometric_cut_requires_same_person_faces_on_both_sides_in_verified_path(monkeypatch,case):
    from dance_highlight.services import mask_tracker as module
    from dance_highlight.services.face_evidence import FaceObservation
    from dance_highlight.services.segment import FrameRec
    from dataclasses import replace
    image=np.zeros((100,100,3),np.uint8);mask=np.zeros((100,100),bool);mask[:,:50]=True
    box=np.array([0.,0.,50.,100.]);other=box+[50.,0.,50.,0.]
    head=np.array([[20.,20.,.9],[30.,20.,.9]])
    records=[FrameRec(i/10.,1,box,False,person_bboxes=[box,other],person_head_keypoints=[head,head+[50.,0.,0.]]) for i in range(7)]
    anchor=FaceObservation(0,0.,1,tuple(box),tuple(box),face_bbox=(10.,10.,40.,30.),embedding=np.array([1.,0.]),detector_score=.99,association='confirmed')
    after=replace(anchor,frame_index=2,time_seconds=.2)
    if case=='wrong_face_body':after=replace(after,body_bbox=tuple(other))
    if case=='outside_path':after=replace(after,frame_index=8,time_seconds=.8)
    tracker=module.MaskTracker.__new__(module.MaskTracker);tracker.source='unused';tracker.fps=10.;tracker.on_progress=None
    tracker.joint_faces=[] if case=='no_faces' else [('A',anchor),('B' if case=='opposing_name' else 'A',after)]
    tracker.transition_cache={1:dict(cut=True,color_candidate=True,structure=dict(continuous=True))}
    tracker._cuts=lambda *args:{1}
    class Capture:
        def __init__(self,*args):pass
        def isOpened(self):return True
        def get(self,prop):return 10.
        def release(self):pass
    monkeypatch.setattr(module.cv2,'VideoCapture',Capture)
    def masks(cap,rows,**kwargs):
        for r in rows:
            current=mask.copy()
            if case=='missing_reverse_owner' and 'masks' in kwargs and round(r.t*10)==2:current[:30]=False
            yield round(r.t*10),image,current
    tracker._masks=masks
    tracker._locate_mask_face=lambda *args:(10.,10.,40.,30.)
    tracker._link_cut_faces=lambda *args:dict(accepted=False,reason='no_face_correspondence')
    monkeypatch.setattr(module,'photometric_body_link',lambda *args:dict(accepted=case!='changed_foreground'))
    result=tracker(anchor,records,list(range(1,7)))
    assert result['accepted']==(case=='confirmed')
    if case=='confirmed':assert result['identity_supported_transitions'][0]['support_frames']==[0,2]


def test_exact_mask_face_requires_one_current_detected_face_inside_mask():
    from dance_highlight.services.mask_tracker import owned_mask_face
    image=np.zeros((100,100,3),np.uint8);mask=np.zeros((100,100),bool);mask[10:90,10:60]=True
    face=np.array([10.,10.,20.,20.,15.,15.,25.,15.,20.,20.,15.,25.,25.,25.,.99],np.float32)
    class Detector:
        faces=np.array([face])
        def setInputSize(self,size):pass
        def detect(self,image):return None,self.faces
    detector=Detector()
    assert owned_mask_face(image,mask,detector)==(20.,20.,40.,40.)
    detector.faces=np.array([face,face])
    assert owned_mask_face(image,mask,detector) is None
    detector.faces=np.array([face+np.array([50,0,0,0,50,0,50,0,50,0,50,0,50,0,0])])
    assert owned_mask_face(image,mask,detector) is None
    detector.faces=None
    assert owned_mask_face(image,mask,detector) is None


def torso_example():
    mask=np.zeros((100,100),bool);mask[20:90,10:45]=True
    pose=np.zeros((17,3),np.float32)
    pose[[5,6,12,11]]=[[15,30,.95],[40,30,.95],[40,80,.95],[15,80,.95]]
    return mask,pose


def test_torso_ownership_requires_confident_full_torso_when_head_is_hidden():
    from dance_highlight.services.mask_tracker import pose_owners
    mask,pose=torso_example()
    assert pose_owners(mask,[pose[:5]],[pose])==((0,),True)
    assert pose_owners(mask,[pose[:5]],[])==((),False)
    assert pose_owners(mask,[pose[:5],pose[:5]],[pose,pose])==((0,1),True)


@pytest.mark.parametrize('case',['visible_head_outside','low_confidence','nonfinite','out_of_frame','tiny_torso','partial_mask','missing_point'])
def test_torso_fallback_cannot_replace_missing_or_conflicting_pose_evidence(case):
    from dance_highlight.services.mask_tracker import pose_owners
    mask,pose=torso_example()
    if case=='visible_head_outside':pose[:2]=[[70,10,.9],[80,10,.9]]
    if case=='low_confidence':pose[5,2]=.74
    if case=='nonfinite':pose[6,0]=np.nan
    if case=='out_of_frame':pose[5,0]=-5
    if case=='tiny_torso':pose[[5,6,12,11],:2]=[[20,40],[22,40],[22,42],[20,42]]
    if case=='partial_mask':mask[50:65]=False
    if case=='missing_point':pose=pose[:12]
    assert pose_owners(mask,[pose[:5]],[pose])==((),False)


def test_measured_head_ownership_is_not_overridden_by_torso():
    from dance_highlight.services.mask_tracker import pose_owners
    mask,pose=torso_example()
    head=np.array([[20,25,.9],[30,25,.9]])
    assert pose_owners(mask,[head],[pose])==((0,),False)


@pytest.mark.parametrize('reverse_missing', [False,True])
def test_tracker_connects_torso_evidence_in_both_directions(monkeypatch,reverse_missing):
    from dataclasses import replace
    from dance_highlight.services import mask_tracker as module
    from dance_highlight.services.face_evidence import FaceObservation
    from dance_highlight.services.segment import FrameRec
    mask,pose=torso_example();image=np.zeros((100,100,3),np.uint8)
    box=np.array([10.,10.,45.,90.]);head=np.array([[20.,25.,.9],[30.,25.,.9]])
    records=[FrameRec(i/10.,1,box,False,person_bboxes=[box],
        person_head_keypoints=[head if i in (0,4) else pose[:5]],person_pose_keypoints=[pose]) for i in range(5)]
    anchor=FaceObservation(0,0.,1,tuple(box),tuple(box),face_bbox=(15.,20.,35.,30.))
    tracker=module.MaskTracker.__new__(module.MaskTracker);tracker.source='unused';tracker.fps=10.;tracker.on_progress=None
    class Capture:
        def __init__(self,*args):pass
        def isOpened(self):return True
        def get(self,prop):return 10.
        def release(self):pass
    monkeypatch.setattr(module.cv2,'VideoCapture',Capture)
    tracker._cuts=lambda *args:set()
    def masks(cap,rows,**kwargs):
        for r in rows:
            current=mask.copy()
            if reverse_missing and 'masks' in kwargs and r.t==.2:current[29:32]=False
            yield round(r.t*10),image,current
    tracker._masks=masks
    result=tracker(anchor,records,[1,2,3,4])
    assert result['accepted'] is (not reverse_missing)
    if result['accepted']:
        assert [t['frame'] for t in result['trace'] if t['torso_fallback']]==[1,2,3]


def test_fallback_keeps_owner_indices_when_some_poses_are_missing():
    from dance_highlight.services.mask_tracker import pose_owners
    mask,pose=torso_example();empty=np.empty((0,3))
    assert pose_owners(mask,[empty,pose[:5]],[empty,pose])==((1,),True)
    assert pose_owners(mask,[empty,pose[:5]],[pose])==((),False)


def test_inserted_cut_frames_do_not_inherit_nearby_torso_observations(monkeypatch):
    from dataclasses import replace
    from dance_highlight.services import mask_tracker as module
    from dance_highlight.services.face_evidence import FaceObservation
    from dance_highlight.services.segment import FrameRec
    mask,pose=torso_example();image=np.zeros((100,100,3),np.uint8)
    box=np.array([10.,10.,45.,90.]);head=np.array([[20.,25.,.9],[30.,25.,.9]])
    records=[FrameRec(i/10.,1,box,False,person_bboxes=[box],person_head_keypoints=[head],
                       person_pose_keypoints=[pose]) for i in (0,2,4,6)]
    anchor=FaceObservation(0,0.,1,tuple(box),tuple(box),face_bbox=(15.,20.,35.,30.),
        embedding=np.array([1.,0.]),detector_score=.99,association='confirmed')
    tracker=module.MaskTracker.__new__(module.MaskTracker);tracker.source='unused';tracker.fps=10.;tracker.on_progress=None
    tracker.joint_faces=[('A',anchor),('A',replace(anchor,frame_index=2,time_seconds=.2))]
    tracker.transition_cache={1:dict(cut=True,color_candidate=True,structure=dict(continuous=True))}
    tracker._cuts=lambda *args:{1}
    class Capture:
        def __init__(self,*args):pass
        def isOpened(self):return True
        def get(self,prop):return 10.
        def release(self):pass
    monkeypatch.setattr(module.cv2,'VideoCapture',Capture)
    inserted=[]
    def masks(cap,rows,**kwargs):
        for r in rows:
            if round(r.t*10)==1:
                assert r.person_head_keypoints==[]
                assert r.person_pose_keypoints==[]
                inserted.append(r.t)
            yield round(r.t*10),image,mask
    tracker._masks=masks;tracker._locate_mask_face=lambda *args:(15.,20.,35.,30.)
    monkeypatch.setattr(module,'photometric_body_link',lambda *args:dict(accepted=True))
    result=tracker(anchor,records,[2,4,6])
    assert result['accepted'] and inserted==[.1,.1]


@pytest.mark.parametrize('case',['one_head_owned','duplicate','collinear','crossed'])
def test_torso_requires_missing_head_and_valid_four_corner_geometry(case):
    from dance_highlight.services.mask_tracker import pose_owners
    mask,pose=torso_example()
    if case=='one_head_owned':pose[:2]=[[20,25,.9],[80,10,.9]]
    if case=='duplicate':pose[6]=pose[5]
    if case=='collinear':pose[[5,6,12,11],:2]=[[15,30],[20,40],[30,60],[40,80]]
    if case=='crossed':pose[[12,11]]=pose[[11,12]]
    assert pose_owners(mask,[pose[:5]],[pose])==((),False)
