from types import SimpleNamespace
import numpy as np
import pytest


def test_secondary_gallery_requires_distinct_photos_for_every_roster_member():
    from dance_highlight.services.secondary_faces import build_secondary_gallery
    a = np.array([1., 0., 0.])
    b = np.array([0., 1., 0.])
    assert build_secondary_gallery([('A', 'photo1', a), ('A', 'photo1', a)], {'A'}) is None
    assert build_secondary_gallery([('A', 'photo1', a), ('A', 'photo2', a)], {'A', 'B'}) is None
    assert build_secondary_gallery([('A', 'photo1', a), ('A', 'photo2', a),
                                    ('B', 'photo1', b), ('B', 'photo3', b)], {'A', 'B'}) is None


def test_secondary_match_preserves_competing_identity_margin():
    from dance_highlight.services.secondary_faces import build_secondary_gallery, match_secondary_vector
    a, b = np.array([1., 0., 0.]), np.array([0., 1., 0.])
    gallery = build_secondary_gallery([('A', 'a1', a), ('A', 'a2', a),
                                       ('B', 'b1', b), ('B', 'b2', b)], {'A', 'B'})
    assert match_secondary_vector(a, gallery)['name'] == 'A'
    assert match_secondary_vector(np.array([1., 1., 0.])/np.sqrt(2), gallery)['name'] is None
    assert match_secondary_vector(np.array([0., 0., 1.]), gallery)['name'] is None
    assert match_secondary_vector(np.array([np.nan, 0., 0.]), gallery)['name'] is None


def test_secondary_queries_are_only_owned_faces_inside_unresolved_intervals():
    from dance_highlight.services.secondary_faces import unresolved_observations
    from test_dance_member_timeline import observation
    from dataclasses import replace
    rows = [observation(.1, 'A'), observation(1.1, '?'),
            replace(observation(1.3, '?'), association='ambiguous'),
            replace(observation(1.5, '?'), detector_score=.5), observation(2., '?')]
    rows = [replace(row, landmarks=((35.,20.),(55.,20.),(45.,25.),(40.,35.),(50.,35.))) for row in rows]
    rows.append(observation(1.7, '?'))  # No source landmarks: cannot align a second model.
    result = dict(segments=[SimpleNamespace(start=0., end=1.), SimpleNamespace(start=1., end=2.)],
                  decisions=[SimpleNamespace(reference_id='A'), SimpleNamespace(reference_id=None)],
                  evidence=[[(rows[0], 'A')], [(row, None) for row in rows[1:]]])
    assert list(unresolved_observations(result)) == [rows[1].frame_index]


@pytest.mark.parametrize('failure', [OSError('offline'), RuntimeError('model verification failed')])
def test_unavailable_secondary_model_preserves_primary_result(monkeypatch, failure):
    from dataclasses import replace
    from test_dance_member_timeline import observation
    from dance_highlight.services import face_models, secondary_faces
    row = replace(observation(.1, '?'), landmarks=((1.,1.),)*5)
    output = dict(segments=[SimpleNamespace(start=0., end=1.)],
                  decisions=[SimpleNamespace(reference_id=None)], evidence=[[(row,None)]])
    def unavailable(**kwargs):
        raise failure
    monkeypatch.setattr(face_models, 'ensure_face_models', unavailable)
    names, audit = secondary_faces.recover_secondary_names('unused.mp4', {'A':['unused.png']}, output, None)
    assert names == {}
    assert audit['reason'] == 'secondary_model_unavailable'
    assert audit['error_type'] == type(failure).__name__
    assert output['evidence'] == [[(row,None)]]


@pytest.mark.parametrize('incomplete_decode', [False,True])
@pytest.mark.parametrize('recovery_kind', ['photo', 'window'])
@pytest.mark.parametrize('already_named', [False,True])
def test_secondary_recovery_reads_only_requested_source_instants(tmp_path, monkeypatch, recovery_kind, already_named, incomplete_decode):
    import cv2
    from dataclasses import replace
    from test_dance_member_timeline import observation
    from dance_highlight.services import face_models, secondary_faces
    landmarks = ((20.,20.),(40.,20.),(30.,30.),(23.,40.),(37.,40.))
    reference_paths = {}
    for name, channel in [('A', 0), ('B', 2)]:
        reference_paths[name] = []
        for index, strength in enumerate((180, 200)):
            photo = np.zeros((64,64,3), np.uint8); photo[:,:,channel] = strength
            path = tmp_path/f'{name}-{index}.png'; assert cv2.imwrite(str(path), photo)
            reference_paths[name].append(path)
    video = tmp_path/'source.avi'
    writer = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*'MJPG'), 8, (64,64))
    assert writer.isOpened()
    for index in range(16):
        frame = np.zeros((64,64,3), np.uint8)
        frame[:,:,2 if 4 <= index < 8 else 0] = 200
        if recovery_kind == 'window' and 4 <= index < 8:
            frame[:,:,2] = {4:130,5:130,6:140,7:150}[index]
        writer.write(frame)
    writer.release()
    frames = (4,6,7) if recovery_kind == 'window' else (4,6)
    rows = [replace(observation(index/8, '?'), frame_index=index, landmarks=landmarks) for index in frames]
    output = dict(segments=[SimpleNamespace(start=.5,end=1.)], decisions=[SimpleNamespace(reference_id='A' if already_named else None)],
                  evidence=[[(row,None) for row in rows]])
    model = tmp_path/'model.onnx'; model.write_bytes(b'model loading is isolated by this test')
    monkeypatch.setattr(face_models, 'ensure_face_models', lambda **kwargs: {'opencv-sface-face-recognition':model})
    class Recognizer:
        def alignCrop(self, image, face): return image
        def feature(self, image):
            vector = np.zeros((1,128),np.float32)
            blue,_,red = image.mean(axis=(0,1))
            if recovery_kind == 'window' and red>blue and 120<red<170:
                value = .35 if red<135 else .36 if red<145 else .49
                vector[0,0] = value; vector[0,2] = np.sqrt(1-value*value)
            else:
                vector[0,0 if blue>red else 1] = 1
            return vector
    monkeypatch.setattr(cv2, 'FaceRecognizerSF', SimpleNamespace(create=lambda *_:Recognizer()))
    monkeypatch.setattr('onnxruntime.get_available_providers', lambda:['CPUExecutionProvider'])
    face_service = SimpleNamespace(get_face_embedding_candidate=lambda image:SimpleNamespace(
        face_bbox=(10.,10.,50.,50.),landmarks=landmarks,detector_score=.98))
    joint_context = {}
    names, audit = secondary_faces.recover_secondary_names(video, reference_paths, output, face_service,
        last_source_frame=17 if incomplete_decode else None, joint_context=joint_context)
    if incomplete_decode:
        assert joint_context == {}
    else:
        assert joint_context['secondary_recognizer'] is face_service._secondary_recognizer
        assert joint_context['anchors'] == audit['video_anchors']
        assert set(joint_context['observations']) == {a['frame_index'] for a in audit['video_anchors']}
        assert set(joint_context['vectors']) == set(joint_context['observations'])
    if already_named:
        assert names == {} and audit['matches'] == []
        assert set(audit['joint_matches']) == set(frames)
        assert audit['reason'] == ('incomplete_source_decode' if incomplete_decode else 'complete')
        return
    if incomplete_decode and recovery_kind == 'window':
        assert names == {7:'A'}
        assert all('window_support_frames' not in row for row in audit['matches'])
        return
    assert names == {frame:'A' if recovery_kind == 'window' else 'B' for frame in frames}
    assert [row['frame_index'] for row in audit['matches']] == list(frames)
    if recovery_kind == 'window':
        assert all(row['reason']=='secondary_reference_window_match' for row in audit['matches'][:2])
    assert len(audit['references']) == 4


def test_secondary_video_anchors_require_both_models_and_local_repeats():
    from dataclasses import replace
    from test_dance_member_timeline import observation
    from dance_highlight.services.secondary_faces import confirmed_secondary_anchors
    a, b = np.eye(3)[:2]
    gallery = {'A':a,'B':b}
    rows = [observation(t,'A') for t in (.1,.3,2.,5.)]
    seeds = [('A',row) for row in rows]
    vectors = {row.frame_index:a for row in rows}
    # Same primary label with a different secondary reference name cannot seed.
    wrong = replace(observation(.5,'A'),frame_index=50)
    seeds.append(('A',wrong));vectors[50]=b
    anchors = confirmed_secondary_anchors(seeds,vectors,gallery)
    assert [(name,row.frame_index) for name,row in anchors] == [('A',rows[0].frame_index),('A',rows[1].frame_index)]
    assert all(row.embedding.size == 3 for _,row in anchors)


def test_secondary_video_match_needs_independent_times_and_competing_members():
    from dataclasses import replace
    from test_dance_member_timeline import observation
    from dance_highlight.services.secondary_faces import match_secondary_video
    a, b, q = np.eye(3)
    gallery = {'A':a,'B':b}
    # A's in-video appearance is closer to the query than its still photo.
    rows = [(name,replace(observation(t,name),embedding=vector))
            for name,vector in [('A',q),('B',b)] for t in (.1,.3)]
    query = replace(observation(5.,'?'),embedding=q)
    assert match_secondary_video(query,rows,gallery)['name'] == 'A'
    assert match_secondary_video(query,rows[:2],gallery)['name'] is None
    assert match_secondary_video(query,[rows[0],*rows[2:]],gallery)['name'] is None
    # A query cannot support itself or a near duplicate in its own neighborhood.
    near = [(n,replace(r,time_seconds=5.+i*.2)) for i,(n,r) in enumerate(rows)]
    assert match_secondary_video(query,near,gallery)['name'] is None
    tie = [(n,replace(r,embedding=q)) for n,r in rows]
    assert match_secondary_video(query,tie,gallery)['name'] is None


@pytest.mark.parametrize('incomplete_decode', [False,True])
@pytest.mark.parametrize('video_window', [False,True])
@pytest.mark.parametrize('no_target_face', [False,True])
def test_source_recovery_uses_frozen_cross_model_video_anchors(tmp_path, monkeypatch, no_target_face, video_window, incomplete_decode):
    import cv2
    from dataclasses import replace
    from test_dance_member_timeline import observation
    from dance_highlight.services import face_models, secondary_faces
    landmarks = ((20.,20.),(40.,20.),(30.,30.),(23.,40.),(37.,40.))
    references = {}
    for name,channel in [('A',0),('B',1)]:
        references[name] = []
        for index,strength in enumerate((160,200)):
            image=np.zeros((64,64,3),np.uint8);image[:,:,channel]=strength
            path=tmp_path/f'{name}-{index}.png';assert cv2.imwrite(str(path),image)
            references[name].append(path)
    path=tmp_path/'source.avi'
    writer=cv2.VideoWriter(str(path),cv2.VideoWriter_fourcc(*'MJPG'),8,(64,64));assert writer.isOpened()
    for frame in range(56):
        color=(180,0,180) if frame in (0,2) else (0,200,0) if frame in (8,10) else (0,0,180 if video_window and frame==50 else 200)
        writer.write(np.full((64,64,3),color,np.uint8))
    writer.release()
    def row(frame,name):
        return replace(observation(frame/8,name),frame_index=frame,landmarks=landmarks)
    query_frames=(48,50,51) if video_window else (48,50)
    queries=[row(i,'?') for i in query_frames]
    if no_target_face:
        queries=[replace(o,embedding=None,face_bbox=None,landmarks=(),failure='no_detection') for o in queries]
    seeds=[('A',row(i,'A')) for i in (0,2)]+[('B',row(i,'B')) for i in (8,10)]
    output=dict(segments=[SimpleNamespace(start=6.,end=6.5)],decisions=[SimpleNamespace(reference_id=None)],
                evidence=[[(o,None) for o in queries]],anchors=seeds)
    model=tmp_path/'model.onnx';model.write_bytes(b'external inference isolated')
    monkeypatch.setattr(face_models,'ensure_face_models',lambda **_: {'opencv-sface-face-recognition':model})
    class Recognizer:
        def alignCrop(self,image,face):return image
        def feature(self,image):
            blue,green,red=image.mean(axis=(0,1));v=np.zeros((1,128),np.float32)
            if green>100:v[0,1]=1
            elif red>100 and blue>100:
                v[0,0]=.6 if video_window else .7
                v[0,2]=np.sqrt(1-v[0,0]**2)
            elif red>100 and video_window:
                v[0,0]=.48*.6;v[0,2]=.48*.8;v[0,3]=.7
                v[0,4]=np.sqrt(1-.48**2-.7**2)*(1 if red>190 else -1)
            elif red>100:v[0,2]=1
            else:v[0,0]=1
            return v
    monkeypatch.setattr(cv2,'FaceRecognizerSF',SimpleNamespace(create=lambda *_:Recognizer()))
    face_service=SimpleNamespace(get_face_embedding_candidate=lambda _:SimpleNamespace(
        face_bbox=(10.,10.,50.,50.),landmarks=landmarks,detector_score=.98))
    names,audit=secondary_faces.recover_secondary_names(path,references,output,face_service,
        last_source_frame=60 if incomplete_decode else 54)
    assert names==({} if no_target_face or video_window and incomplete_decode else {i:'A' for i in query_frames})
    inventory=audit['source_transitions']
    assert audit['reason']==('incomplete_source_decode' if incomplete_decode else 'complete')
    assert inventory['reason']==('incomplete_source_decode' if incomplete_decode else 'complete')
    assert inventory['through_frame']==(55 if incomplete_decode else 54)
    if video_window and incomplete_decode:
        assert all(m['name'] is None for m in audit['matches'])
        return
    assert len(audit['video_anchors'])==4
    expected_reason='secondary_video_window_match' if video_window else 'secondary_video_match'
    assert all(m['reason']==expected_reason and m['reference_match']['name'] is None for m in audit['matches'])
    assert all(set(m['candidates'][0]['support_frames'])=={0,2} for m in audit['matches'])


def test_secondary_window_averages_only_coherent_faces_inside_unknown_scope():
    from dataclasses import replace
    from test_dance_member_timeline import observation
    from dance_highlight.services.secondary_faces import secondary_window_matches, match_secondary_vector
    gallery={'A':np.array([1.,0.,0.]),'B':np.array([0.,1.,0.])}
    rows=[observation(t,'?') for t in (.1,.3,.5)]
    vectors={row.frame_index:np.array([x,0.,np.sqrt(1-x*x)]) for row,x in zip(rows,(.35,.36,.49))}
    targets={row.frame_index:row for row in rows}
    matches={frame:match_secondary_vector(v,gallery) for frame,v in vectors.items()}
    assert [m['name'] for m in matches.values()]==[None,None,'A']
    result=secondary_window_matches([(0.,.6)],targets,vectors,matches,gallery)
    assert {frame:m['name'] for frame,m in result.items()}=={rows[0].frame_index:'A',rows[1].frame_index:'A'}
    assert all(m['window_support_frames']==[row.frame_index for row in rows] for m in result.values())
    assert secondary_window_matches([(0.,.4),(.4,.6)],targets,vectors,matches,gallery)=={}
    conflict={**matches,rows[-1].frame_index:{'name':'B'}}
    assert secondary_window_matches([(0.,.6)],targets,vectors,conflict,gallery)=={}
    alien={**vectors,rows[-1].frame_index:np.array([0.,1.,0.])}
    assert secondary_window_matches([(0.,.6)],targets,alien,matches,gallery)=={}


def video_window_example():
    from dataclasses import replace
    from test_dance_member_timeline import observation
    from dance_highlight.services.secondary_faces import match_secondary_vector
    gallery={'A':np.eye(5)[0],'B':np.eye(5)[1]}
    anchor=.6*np.eye(5)[0]+.8*np.eye(5)[2]
    anchors=[(name,replace(observation(t,name),embedding=vector))
             for name,vector in [('A',anchor),('B',gallery['B'])] for t in (.1,.3)]
    rows=[observation(t,'?') for t in (6.,6.2,6.4)]
    vectors={row.frame_index:.48*anchor+.7*np.eye(5)[3]+sign*np.sqrt(1-.48**2-.7**2)*np.eye(5)[4]
             for row,sign in zip(rows,(1,-1,1))}
    targets={row.frame_index:row for row in rows}
    matches={frame:match_secondary_vector(vector,gallery) for frame,vector in vectors.items()}
    return targets,vectors,matches,gallery,anchors


def test_secondary_video_window_uses_owned_source_faces_and_complete_cut_inventory():
    from dataclasses import replace
    from dance_highlight.services.secondary_faces import secondary_window_matches
    targets,vectors,matches,gallery,anchors=video_window_example()
    assert all(match['name'] is None for match in matches.values())
    kwargs=dict(video_anchors=anchors,cut_frames=[])
    recovered=secondary_window_matches([(6.,6.5)],targets,vectors,matches,gallery,**kwargs)
    assert {frame:m['name'] for frame,m in recovered.items()}=={frame:'A' for frame in targets}
    assert all(m['name'] is None for m in matches.values())
    assert secondary_window_matches([(6.,6.5)],targets,vectors,matches,gallery,video_anchors=anchors)=={}
    frames=list(targets)
    assert secondary_window_matches([(6.,6.5)],targets,vectors,matches,gallery,
                                   video_anchors=anchors,cut_frames=[frames[-1]])=={}
    invalid={**targets,frames[1]:replace(targets[frames[1]],association='ambiguous')}
    assert secondary_window_matches([(6.,6.5)],invalid,vectors,matches,gallery,**kwargs)=={}
    invalid={**targets,frames[1]:replace(targets[frames[1]],embedding=None,failure='no_detection')}
    assert secondary_window_matches([(6.,6.5)],invalid,vectors,matches,gallery,**kwargs)=={}


@pytest.mark.parametrize('case',['missing_member','one_view','near_window_edge','conflicting_name','incoherent','primary_boundary'])
def test_secondary_video_window_preserves_independent_competing_evidence(case):
    from dataclasses import replace
    from dance_highlight.services.secondary_faces import secondary_window_matches
    targets,vectors,matches,gallery,anchors=video_window_example()
    scopes=[(6.,6.5)]
    frames=list(targets)
    if case=='missing_member':anchors=anchors[:2]
    if case=='one_view':anchors=[anchors[0],*anchors[2:]]
    if case=='near_window_edge':
        # Both views are >2s from the first query but within2s of its last
        # contributing face. A query-only exclusion would accept this leak.
        anchors=[(name,replace(row,time_seconds=t,frame_index=round(t*10)))
                 for (name,row),t in zip(anchors,(8.1,8.3,.1,.3))]
    if case=='conflicting_name':matches[frames[-1]]={'name':'B'}
    if case=='incoherent':vectors[frames[-1]]=gallery['B']
    if case=='primary_boundary':scopes=[(6.,6.3),(6.3,6.5)]
    assert secondary_window_matches(scopes,targets,vectors,matches,gallery,
                                   video_anchors=anchors,cut_frames=[])=={}
