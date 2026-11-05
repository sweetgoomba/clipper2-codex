import cv2
import numpy as np
import pytest


def textured(seed=1):
    rng = np.random.default_rng(seed)
    return cv2.GaussianBlur(rng.integers(0, 256, (400, 600, 3), dtype=np.uint8), (3, 3), 0)


def test_central_structure_survives_lighting_and_small_movement():
    from dance_highlight.services.camera_transitions import structural_continuity
    old = textured()
    new = cv2.warpAffine(old, np.float32([[1, 0, 2], [0, 1, 1]]), (600, 400))
    new = cv2.convertScaleAbs(new, alpha=.7, beta=40)
    assert structural_continuity(old, new)['continuous']


def test_identical_broadcast_overlay_does_not_hide_changed_scene():
    from dance_highlight.services.camera_transitions import structural_continuity
    old, new = textured(), textured(2)
    new[:60] = old[:60]
    new[320:] = old[320:]
    new[:, :120] = old[:, :120]
    new[:, 480:] = old[:, 480:]
    assert not structural_continuity(old, new)['continuous']


def test_large_camera_movement_and_missing_structure_remain_cuts():
    from dance_highlight.services.camera_transitions import structural_continuity
    old = textured()
    moved = cv2.warpAffine(old, np.float32([[1, 0, 60], [0, 1, 0]]), (600, 400))
    assert not structural_continuity(old, moved)['continuous']
    assert not structural_continuity(old, np.zeros_like(old))['continuous']


def test_stable_background_is_only_a_proposal_and_does_not_remove_foreground_cut():
    from dance_highlight.services.camera_transitions import classify_transition
    old=textured(23);new=old.copy()
    noise=np.random.default_rng(7).integers(0,30,(240,360),dtype=np.uint8)
    old[80:320,120:480]=np.stack([noise,noise+200,noise],axis=2)
    new[80:320,120:480]=np.stack([noise+200,noise,noise],axis=2)
    result=classify_transition(old,new)
    assert result['color_candidate'] and result['cut']
    assert result['structure']['continuous']  # A static background alone must not authorize crossing.


def test_geometry_failure_preserves_color_cut(monkeypatch):
    from dance_highlight.services import camera_transitions as module
    monkeypatch.setattr(module, '_color_cut', lambda *args: (True, {}))
    def fail(*args):
        raise cv2.error('invalid transform')
    monkeypatch.setattr(module, 'structural_continuity', fail)
    result = module.classify_transition(textured(), textured())
    assert result['cut'] and result['color_candidate']
    assert result['reason'] == 'structure_unavailable'


def test_tracker_caches_exact_source_pairs_for_repeated_paths(monkeypatch):
    from dance_highlight.services import mask_tracker as module
    tracker = module.MaskTracker.__new__(module.MaskTracker)
    tracker._read = lambda cap, frame: np.full((2, 2, 3), frame, np.uint8)
    calls = []
    def classify(old, new):
        pair = (int(old[0, 0, 0]), int(new[0, 0, 0]))
        calls.append(pair)
        return dict(cut=pair[1] == 3, color_candidate=True)
    monkeypatch.setattr(module, 'classify_transition', classify)
    assert tracker._cuts(None, 0, 4) == {3}
    assert tracker._cuts(None, 2, 5) == {3}
    assert calls == [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)]


def test_failed_source_pair_is_not_cached_as_continuous(monkeypatch):
    from dance_highlight.services import mask_tracker as module
    tracker = module.MaskTracker.__new__(module.MaskTracker)
    def fail(cap, frame):
        raise ValueError('source_frame_unavailable')
    tracker._read = fail
    with pytest.raises(ValueError, match='source_frame_unavailable'):
        tracker._cuts(None, 0, 1)
    tracker._read = lambda cap, frame: np.zeros((2, 2, 3), np.uint8)
    monkeypatch.setattr(module, 'classify_transition', lambda *args: dict(cut=True, color_candidate=True))
    assert tracker._cuts(None, 0, 1) == {1}


def test_source_scan_requires_all_expected_frames_and_fps(tmp_path):
    from dance_highlight.services.camera_transitions import scan_source_transitions
    path=tmp_path/'source.avi'
    writer=cv2.VideoWriter(str(path),cv2.VideoWriter_fourcc(*'MJPG'),10.,(64,64))
    for _ in range(5):writer.write(np.zeros((64,64,3),np.uint8))
    writer.release()
    transitions,reason=scan_source_transitions(path,10.,4)
    assert reason=='complete' and len(transitions)==4
    assert scan_source_transitions(path,10.,6)[1]=='incomplete_source_decode'
    assert scan_source_transitions(path,20.,4)[1]=='source_fps_mismatch'


def test_masked_head_and_torso_proof_accepts_lighting_but_rejects_foreground_insertion():
    from dance_highlight.services.camera_transitions import photometric_body_link
    old=textured(71)
    light=cv2.convertScaleAbs(old,alpha=.75,beta=40)
    mask=np.zeros(old.shape[:2],bool);mask[30:390,150:450]=True
    face=(235.,50.,315.,130.)
    assert photometric_body_link(old,light,mask,mask,face,face)['accepted']
    inserted=old.copy();inserted[30:390,150:450]=textured(81)[30:390,150:450]
    assert not photometric_body_link(old,inserted,mask,mask,face,face)['accepted']
    assert not photometric_body_link(inserted,old,mask,mask,face,face)['accepted']
    # Same clothes/body/background cannot stand in for the replaced head.
    head_only=old.copy();head_only[30:155,210:340]=textured(91)[30:155,210:340]
    assert not photometric_body_link(old,head_only,mask,mask,face,face)['accepted']
    assert not photometric_body_link(old,light,np.zeros_like(mask),mask,face,face)['accepted']
    assert not photometric_body_link(np.zeros_like(old),np.zeros_like(old),mask,mask,face,face)['accepted']
    assert not photometric_body_link(old,light,mask,mask,None,face)['accepted']


def test_deferred_structure_preserves_cuts_without_running_unused_sift(monkeypatch):
    from dance_highlight.services import camera_transitions as module
    monkeypatch.setattr(module,'_color_cut',lambda *args:(True,{}))
    def forbidden(*args):raise AssertionError('structure is not requested yet')
    monkeypatch.setattr(module,'structural_continuity',forbidden)
    result=module.classify_transition(textured(),textured(),include_structure=False)
    assert result==dict(cut=True,color_candidate=True,structure_deferred=True)
