"""An existing named boundary can move only over observed incoming-body frames."""
import copy
from dataclasses import fields,replace
import importlib
import json
from pathlib import Path
import pickle
from types import SimpleNamespace

import cv2
import numpy as np
import pytest
from dance_highlight.services.face_evidence import FaceObservation
from dance_highlight.services.reference_matcher import SegmentReferenceDecision
from dance_highlight.services.segment import FrameRec,Segment

FIXTURE=Path(__file__).parent/'fixtures/dance_scene_review/incoming_identity_boundary_ant154.json'


def example():
    d=json.loads(FIXTURE.read_text());records=[];observations=[];joint={};photo={}
    names={f.name for f in fields(FaceObservation)}
    for r in d['rows']:
        records.append(FrameRec(r['time'],1,np.array(r['selected_box']),True,
            person_bboxes=[np.array(b) for b in r['body_boxes']],
            person_pose_keypoints=[np.array(p) for p in r['pose_keypoints']],scene_kind=r['scene_kind']))
        observations.append(FaceObservation(**{k:np.array(v) if k=='embedding' and v is not None else v
                                                for k,v in r['face'].items() if k in names}))
        if r['joint']:joint[r['frame']]=r['joint']
        photo[r['frame']]=r['photo']['name']
    parts=[Segment('main',i,s['start'],s['end'],[(r.t,r.main_bbox,r.main_id) for r in records if s['start']<=r.t<s['end']]) for i,s in enumerate(d['segments'])]
    evidence=[[(o,joint.get(o.frame_index,{}).get('name')) for o in observations if s.start<=o.time_seconds<s.end] for s in parts]
    images={o.frame_index:str(o.frame_index).encode() for o in observations}
    output=dict(segments=parts,decisions=[SegmentReferenceDecision(s['name'],'matched','member_timeline_consensus') for s in d['segments']],
        labels=[1,2],evidence=evidence,previews=[[b'old-A'],[b'old-B']],preview_sources=[(images,{}) for _ in parts],
        accurate_indices=[0,1],anchors=[],fallback_names={})
    class OriginalPhotoMatcher:
        # Frozen original photo decisions from the real matcher replay. No
        # parent output label is available to this source evidence fixture.
        def match(self,o,*args):return SimpleNamespace(reference_id=photo.get(o.frame_index))
    return d,output,records,observations,joint,OriginalPhotoMatcher(),photo


class ObservedSource:
    image=np.zeros((1080,1920,3),np.uint8)
    def __init__(self,*args):self.stats=dict(reads=0,seeks=0,grabs=0,cache_hits=0,decode_seconds=0.)
    def get(self,frame):self.stats['reads']+=1;return self.image
    def close(self):pass


def run(monkeypatch,data,reader=ObservedSource,**kw):
    module=importlib.import_module('dance_highlight.services.incoming_identity_boundary')
    monkeypatch.setattr(module,'SourceFrameReader',reader)
    d,out,records,obs,joint,matcher,_=data
    kwargs=dict(fps=d['fps'],sample_step=4,cut_frames=d['cut_frames'],source_path='original-source.mp4',video_size=(1920,1080))
    kwargs.update(kw)
    return module.reconcile_incoming_identity_boundary(out,records,obs,joint,matcher,**kwargs)


def test_original_ant154_incoming_body_moves_existing_boundary_to_first_observed_B(monkeypatch):
    data=example();frozen=pickle.dumps(data[1:5]);out=data[1]
    result,audit=run(monkeypatch,data)
    assert result['segments'][0].end==pytest.approx(9272/data[0]['fps'])
    assert result['segments'][1].start==result['segments'][0].end
    assert audit['corrected_seconds']==pytest.approx(.13346666666666)
    assert audit['corrections'][0]['seed_frames']==[9308,9320]
    assert audit['corrections'][0]['path_frames']==list(range(9272,9321,4))
    assert audit['corrections'][0]['source_frames_checked']==[9244,9320]
    assert audit['source_reads']['reads']==77
    assert pickle.dumps(data[1:5])==frozen
    assert result['decisions']==out['decisions'] and result['labels']==out['labels']
    assert result['anchors']==[] and result['fallback_names']=={}
    assert len(result['segments'])==2
    original_evidence={o.frame_index:n for entries in out['evidence'] for o,n in entries}
    assert {o.frame_index:n for entries in result['evidence'] for o,n in entries}==original_evidence
    for i,s in enumerate(result['segments']):
        assert all(s.start<=o.time_seconds<s.end for o,n in result['evidence'][i])
        assert all(s.start<=t<s.end for t,*_ in s.bboxes)
        assert all(s.start<=int(image)/data[0]['fps']<s.end for image in result['previews'][i])
    # Group output/membership is independent: every original source row here
    # deliberately remains group=True while scene_kind remains main-eligible.
    assert all(r.is_group for r in data[2])


@pytest.mark.parametrize('case',['unknown_left','same_name','nonadjacent','single_anchor','too_close_pair',
    'weak_anchor','unowned_anchor','primary_disagrees','bad_ranks','missing_ranks','joint_conflict',
    'joint_other_name','photo_other_name','positive_model_other_name','missing_sample','missing_body',
    'genuine_group','missing_pose','ambiguous_pose','cut','missing_cut_inventory','duplicate_face','duplicate_record'])
def test_original_counterevidence_prevents_boundary_relabeling(monkeypatch,case):
    data=list(example());d,out,records,obs,joint,matcher,photo=data;kw={}
    index={round(r.t*d['fps']):i for i,r in enumerate(records)}
    if case=='unknown_left':out['decisions'][0]=SegmentReferenceDecision(None,'unmatched','unknown')
    if case=='same_name':out['decisions'][0]=out['decisions'][1]
    if case=='nonadjacent':out['segments'][0]=replace(out['segments'][0],end=154.7)
    if case=='single_anchor':joint.pop(9320);joint.pop(9312)
    if case=='too_close_pair':joint.pop(9320) # 9308/9312 only .0667s apart
    if case=='weak_anchor':data[3]=[replace(o,detector_score=.5) if o.frame_index==9320 else o for o in obs]
    if case=='unowned_anchor':data[3]=[replace(o,body_bbox=(0,0,10,10)) if o.frame_index==9320 else o for o in obs]
    if case=='primary_disagrees':joint[9308]['model_candidates'][0][0]['name']='김채원'
    if case=='bad_ranks':joint[9308]['primary']=.1
    if case=='missing_ranks':joint[9308].pop('model_candidates')
    if case=='joint_conflict':joint[9284]['status']='conflict'
    if case=='joint_other_name':joint[9284].update(status='accepted',name='김채원')
    if case=='photo_other_name':photo[9284]='김채원'
    if case=='positive_model_other_name':
        j=joint[9284];ranks=j['model_candidates'][0]
        next(r for r in ranks if r['name']=='김채원')['distance']=.2
        ranks.sort(key=lambda r:r['distance'])
    if case=='missing_sample':records.pop(index[9284])
    if case=='missing_body':records[index[9284]].main_bbox=None
    if case=='genuine_group':records[index[9284]].scene_kind='group'
    if case=='missing_pose':records[index[9284]].person_pose_keypoints=[]
    if case=='ambiguous_pose':
        r=records[index[9284]];i=next(i for i,b in enumerate(r.person_bboxes) if np.array_equal(b,r.main_bbox))
        r.person_bboxes.append(r.person_bboxes[i].copy());r.person_pose_keypoints.append(r.person_pose_keypoints[i].copy())
    if case=='cut':kw['cut_frames']=[9282]
    if case=='missing_cut_inventory':kw['cut_frames']=None
    if case=='duplicate_face':obs.append(obs[-1])
    if case=='duplicate_record':records.append(records[-1])
    frozen=pickle.dumps(data[1:5]);result,audit=run(monkeypatch,data,**kw)
    assert result is out and not audit['corrections']
    assert pickle.dumps(data[1:5])==frozen
    assert audit['source_reads']['reads']==0


def test_unknown_or_conflicting_joint_outside_the_B_path_does_not_vote(monkeypatch):
    data=example();assert data[4][9264]['status']=='conflict'
    result,audit=run(monkeypatch,data)
    assert result is not data[1] and len(audit['corrections'])==1


@pytest.mark.parametrize('failure',['open','read','size','actual_cut'])
def test_source_failure_or_actual_cut_returns_original_even_after_geometry_passes(monkeypatch,failure):
    pixels=FIXTURE.parent/'group_continuity_source'
    class Source(ObservedSource):
        def __init__(self,*args):
            if failure=='open':raise OSError('unavailable')
            super().__init__(*args)
        def get(self,frame):
            if failure=='read':raise ValueError('missing source frame')
            if failure=='size':return np.zeros((100,100,3),np.uint8)
            if failure=='actual_cut':return cv2.imread(str(pixels/('3576.png' if frame<9282 else '3577.png')))
            return super().get(frame)
    data=example();result,audit=run(monkeypatch,data,reader=Source)
    assert result is data[1] and not audit['corrections']


def test_repeated_run_is_idempotent(monkeypatch):
    data=list(example());data[1],_=run(monkeypatch,data)
    result,audit=run(monkeypatch,data)
    assert result is data[1] and not audit['corrections']


@pytest.mark.parametrize('margin',[float('nan'),None,'invalid'])
def test_malformed_original_joint_margin_never_becomes_an_anchor(monkeypatch,margin):
    data=example();data[4][9308]['margin']=margin
    result,audit=run(monkeypatch,data)
    assert result is data[1] and not audit['corrections']


@pytest.mark.parametrize('condition',['boundary_source_cut','handoff_inside_path','misaligned_arrays'])
def test_boundary_context_cannot_be_repaired_by_an_incoming_name(monkeypatch,condition):
    data=example();kwargs={}
    if condition=='boundary_source_cut':kwargs['cut_frames']=[9270]
    if condition=='handoff_inside_path':kwargs['handoffs']=[dict(frame=9284)]
    if condition=='misaligned_arrays':data[1]['labels'].pop()
    result,audit=run(monkeypatch,data,**kwargs)
    assert result is data[1] and not audit['corrections']


def test_source_failure_on_later_candidate_rolls_back_every_boundary(monkeypatch):
    data=list(example());d,out,records,obs,joints,matcher,photo=data
    offset=12000;seconds=offset/d['fps'];original_count=len(out['segments'])
    out['segments'] += [replace(s,start=s.start+seconds,end=s.end+seconds,
        bboxes=[(t+seconds,*rest) for t,*rest in s.bboxes]) for s in out['segments']]
    for key in ('decisions','labels','previews','preview_sources'):
        out[key] += list(out[key])
    out['evidence'] += [[(replace(o,frame_index=o.frame_index+offset,time_seconds=o.time_seconds+seconds),n) for o,n in entries] for entries in out['evidence']]
    out['accurate_indices'] += [i+original_count for i in out['accurate_indices']]
    records += [replace(r,t=r.t+seconds) for r in records]
    obs += [replace(o,frame_index=o.frame_index+offset,time_seconds=o.time_seconds+seconds) for o in obs]
    joints.update({f+offset:copy.deepcopy(j) for f,j in list(joints.items())})
    class FailsLater(ObservedSource):
        def get(self,frame):
            if frame>offset:raise OSError('second original source window unavailable')
            return super().get(frame)
    result,audit=run(monkeypatch,data,reader=FailsLater)
    assert result is out and not audit['corrections'] and audit['corrected_seconds']==0
    assert audit['reason']=='source_unavailable'


def test_left_start_between_samples_cannot_leave_an_unobserved_named_fragment(monkeypatch):
    data=example();out=data[1];out['segments'][0]=replace(out['segments'][0],start=9270/data[0]['fps'])
    result,audit=run(monkeypatch,data)
    assert result is out and not audit['corrections']
    assert audit['source_reads']['reads']==0


@pytest.mark.parametrize('case',['no_A_pair','A_selected_path_break','opposite_A_face'])
def test_retained_outgoing_name_needs_its_own_original_anchors_and_selected_path(monkeypatch,case):
    data=list(example());d,out,records,obs,joint,matcher,photo=data
    if case=='no_A_pair':
        for f in [9244,9248,9252,9256]:joint[f]['status']='insufficient'
    if case=='A_selected_path_break':
        row=next(r for r in records if round(r.t*d['fps'])==9260);row.person_pose_keypoints=[]
    if case=='opposite_A_face':joint[9264].update(status='accepted',name='카즈하')
    result,audit=run(monkeypatch,data)
    assert result is out and not audit['corrections']
    assert audit['source_reads']['reads']==0
