"""Original face runs may straddle an output boundary without being a new part."""
from dataclasses import replace
import numpy as np
import pytest
from test_dance_body_continuity import example
from dance_highlight.services.face_recovery import ReferenceObservationMatcher
from dance_highlight.services.reference_matcher import ReferenceEmbeddingSample, SegmentReferenceDecision
from dance_highlight.services.segment import Segment


def case(tmp_path, **kwargs):
    path, old, records=example(tmp_path, **kwargs)
    rows=[o for part in old['evidence'] for o,_ in part]
    rows=[replace(o, embedding=np.array([1.,0.]) if o.time_seconds<=2.2 else np.array([0.,1.]),
        detector_score=.99,association='confirmed',failure=None,face_bbox=(40.,12.,55.,28.)) for o in rows]
    for r in records:r.scene_kind='main'
    segments=[Segment('main',1,0.,2.,[]),Segment('main',2,2.,6.,[])]
    out=dict(old,segments=segments,
        decisions=[SegmentReferenceDecision(n,'matched','test') for n in ('A','B')],
        labels=[1,2],evidence=[[(o,'A' if o.time_seconds<2. else 'B') for o in rows if s.start<=o.time_seconds<s.end] for s in segments],
        previews=[[b'A'],[b'B']],preview_sources=[({},{}),({}, {})],accurate_indices=[0,1])
    joint={o.frame_index:dict(status='accepted',name='A' if o.time_seconds<=2.2 else 'B') for o in rows}
    refs=[ReferenceEmbeddingSample(n,n,str(i)*64,160,100,np.eye(2)[i]) for i,n in enumerate(('A','B'))]
    matcher=ReferenceObservationMatcher(references=refs,analysis_id='test',video_sha256='a'*64,
        detector_sha256='b'*64,recognizer_sha256='c'*64,config_sha256='d'*64,
        backend_version='test',video_size=(160,100),max_distance=.6)
    return path,out,records,rows,joint,matcher


def run(data,**kw):
    from dance_highlight.services.named_boundaries import reconcile_named_boundaries
    path,out,records,rows,joint,matcher=data
    return reconcile_named_boundaries(out,records,rows,joint,matcher,video_path=path,fps=20.,
        group_segments=kw.pop('group_segments',[]),handoffs=kw.pop('handoffs',[]),**kw)


def test_face_pair_crossing_clip_boundary_corrects_only_the_proven_source_frames(tmp_path):
    data=case(tmp_path)
    result,audit=run(data)
    assert [(s.start,s.end,d.reference_id) for s,d in zip(result['segments'],result['decisions'])]==[
        (0.,2.25,'A'),(2.25,6.,'B')]
    assert audit['corrected_seconds']==pytest.approx(.25)
    assert len(result['segments'])==len(data[1]['segments'])==2
    assert data[1]['segments'][0].end==2.
    assert result['anchors']==data[1]['anchors']==[]
    assert result['fallback_names']=={}


@pytest.mark.parametrize('condition',['single_frame','missing_row','group','handoff','foreign_face',
    'unowned','overlap','source_missing','no_target_sample','prep_overlap'])
def test_boundary_without_full_original_identity_and_source_proof_is_unchanged(tmp_path,condition):
    data=list(case(tmp_path,overlap=condition=='overlap'));path,out,records,rows,joint,matcher=data;kw={}
    if condition=='single_frame': data[4]={44:joint[44]}
    elif condition=='missing_row':data[3]=[o for o in rows if o.frame_index!=40]
    elif condition=='group':kw['group_segments']=[Segment('group',None,2.05,2.1,[])]
    elif condition=='handoff':kw['handoffs']=[dict(frame=40)]
    elif condition=='foreign_face':joint[40]=dict(status='accepted',name='B')
    elif condition=='unowned':data[3]=[replace(o,body_bbox=(110.,10.,150.,90.)) if o.frame_index==40 else o for o in rows]
    elif condition=='source_missing':data[0]=tmp_path/'missing.avi'
    elif condition=='no_target_sample':out['segments'][0]=replace(out['segments'][0],end=2.21);out['segments'][1]=replace(out['segments'][1],start=2.21)
    elif condition=='prep_overlap':out['segments'][1]=replace(out['segments'][1],start=1.9)
    result,audit=run(data,**kw)
    assert result is out
    assert audit['corrected_seconds']==0.


def test_missing_joint_context_does_not_use_output_label_votes(tmp_path):
    data=list(case(tmp_path));data[4]={}
    result,audit=run(data)
    assert result is data[1]


def test_actual_cut_cannot_be_replaced_with_same_clothing_or_named_pair(tmp_path):
    data=list(case(tmp_path,cut=True));out=data[1]
    # Put the boundary and supporting pair across the source edit at frame 50.
    out['segments']=[replace(out['segments'][0],end=2.5),replace(out['segments'][1],start=2.5)]
    data[3]=[replace(o,embedding=np.array([1.,0.])) if o.time_seconds<=2.6 else o for o in data[3]]
    data[4]={o.frame_index:dict(status='accepted',name='A' if o.time_seconds<=2.6 else 'B') for o in data[3]}
    result,audit=run(data)
    assert result is out


def test_output_boundary_correction_is_idempotent(tmp_path):
    data=list(case(tmp_path));result,audit=run(data);data[1]=result
    again,_=run(data)
    assert again is result


def test_usable_joint_conflict_below_seed_quality_still_blocks_boundary_correction(tmp_path):
    data=list(case(tmp_path))
    data[3]=[replace(o,detector_score=.85) if o.frame_index==40 else o for o in data[3]]
    data[4][40]=dict(status='accepted',name='B')
    result,audit=run(data)
    assert result is data[1]
    assert audit['corrected_seconds']==0.
