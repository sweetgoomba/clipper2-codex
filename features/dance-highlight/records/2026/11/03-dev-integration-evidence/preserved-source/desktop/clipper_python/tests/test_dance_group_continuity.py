"""Group membership may continue while the selected main stays unchanged."""
import copy
import importlib
import importlib.util
import json
from pathlib import Path
import pickle

import cv2
import numpy as np
import pytest

from dance_highlight.services.segment import FrameRec, Segment

FIXTURE = Path(__file__).parent/'fixtures/dance_scene_review/group_continuity.json'


def service():
    name = 'dance_highlight.services.group_continuity'
    assert importlib.util.find_spec(name) is not None, 'Missing group-only continuity API'
    return importlib.import_module(name)


def records(rows):
    output = []
    for row in rows:
        p, d = row['pose'], row['output']
        output.append(FrameRec(row['time'], d['main_track_id'],
            None if d['main_body'] is None else np.array(d['main_body']), d['group'],
            person_bboxes=[np.array(b) for b in p['body_boxes']],
            group_bboxes=[np.array(b) for b in d['group_bodies']],
            person_head_keypoints=[np.array(k) for k in p['head_keypoints']],
            person_pose_keypoints=[np.array(k) for k in p['pose_keypoints']],
            scene_kind=p['scene_kind'], scene_reason=p['scene_reason'],
            candidate_main_id=p['candidate_main_id'],
            candidate_main_bbox=None if p['candidate_main_bbox'] is None else np.array(p['candidate_main_bbox'])))
    return output


def case(title='MMN'):
    data = next(v for v in json.loads(FIXTURE.read_text())['videos'] if v['title']==title)
    return data, records(data['rows']), [Segment('group',None,g['start'],g['end'],[]) for g in data['groups']]


class ObservedSource:
    """Replace external video I/O only. Real geometry and pixel gates still run."""
    image = np.zeros((1080,1920,3), np.uint8)
    def __init__(self, source, fps):
        self.stats = dict(reads=0,seeks=0,grabs=0,cache_hits=0,decode_seconds=0.)
    def get(self, frame):
        self.stats['reads'] += 1
        return self.image
    def close(self):
        pass


def run(monkeypatch, data, recs, groups, reader=ObservedSource, **changes):
    module = service()
    monkeypatch.setattr(module,'SourceFrameReader',reader)
    kwargs = dict(video_size=(1920,1080),fps=data['fps'],sample_step=4,
                  cut_frames=data['cut_frames'],source_path='external-source.mp4',
                  exclusive_foreground_frames=data.get('exclusive_foreground_frames',()))
    kwargs.update(changes)
    return module.stabilize_group_segments(recs,groups,**kwargs)


@pytest.mark.parametrize('title,count,short,reads', [('MMN',31,19,29),('ANT',31,23,33),('NEON',50,30,43)])
def test_recorded_whole_video_projection_preserves_main_and_only_joins_five_proven_gaps(monkeypatch,title,count,short,reads):
    data,recs,groups = case(title)
    frozen = pickle.dumps((recs,groups))
    result,audit = run(monkeypatch,data,recs,groups)
    assert len(result)==count
    assert sum(g.end-g.start<1 for g in result)==short
    assert [(b['start'],b['end']) for b in audit['bridges']]==[(b['start'],b['end']) for b in data['expected_bridges']]
    assert all(len(b['paths'])>=3 and len(b['frames'])==len(b['paths'][0]) for b in audit['bridges'])
    assert pickle.dumps((recs,groups))==frozen
    assert audit['source_reads']['reads']==reads
    assert audit['seconds']>=0


def positive():
    data,recs,groups = case()
    recs=[r for r in recs if 2448<=round(r.t*data['fps'])<=2476]
    groups=[g for g in groups if abs(g.end-40.90753333333333)<1e-8 or abs(g.start-41.30793333333333)<1e-8]
    return data,recs,groups


@pytest.mark.parametrize('veto',['cut','missing_inventory','missing_sample','empty','weak_torso',
    'duplicate','stranger','malformed','exclusive','unconfirmed_anchor'])
def test_counterevidence_cannot_be_filled_from_group_endpoints(monkeypatch,veto):
    data,recs,groups=positive();kwargs={}
    if veto=='cut':kwargs['cut_frames']=[2460]
    if veto=='missing_inventory':kwargs['cut_frames']=None
    if veto=='missing_sample':recs.pop(3)
    if veto=='empty':recs[3].person_bboxes=[];recs[3].person_pose_keypoints=[]
    if veto=='weak_torso':
        for pose in recs[3].person_pose_keypoints:pose[[5,6,11,12],2]=.1
    if veto=='duplicate':
        for r in recs:
            r.person_bboxes=[r.person_bboxes[0].copy() for _ in range(3)]
            r.person_pose_keypoints=[r.person_pose_keypoints[0].copy() for _ in range(3)]
    if veto=='stranger':
        for box,pose in zip(recs[3].person_bboxes,recs[3].person_pose_keypoints):
            box[[1,3]]+=100;pose[:,1]+=100
    if veto=='malformed':recs[3].person_pose_keypoints[0]=np.empty((0,3))
    if veto=='exclusive':kwargs['exclusive_foreground_frames']=[2460]
    if veto=='unconfirmed_anchor':recs[0].is_group=False
    result,audit=run(monkeypatch,data,recs,groups,**kwargs)
    assert [(g.start,g.end) for g in result]==[(g.start,g.end) for g in groups]
    assert not audit['bridges']
    assert audit['source_reads']['reads']==0


@pytest.mark.parametrize('name',['title','closeup','two_people','native_unobserved'])
def test_original_title_closeup_and_unobserved_people_are_not_new_group_membership(monkeypatch,name):
    window=next(r for r in json.loads(FIXTURE.read_text())['negative_windows'] if r['name']==name)
    recs=records(window['rows']);recs[0].is_group=recs[-1].is_group=True
    groups=[Segment('group',None,recs[0].t,recs[1].t,[]),Segment('group',None,recs[-1].t,recs[-1].t+.2,[])]
    # Geometry must veto the real one-person closeup even without a cut vote.
    data=dict(fps=60000/1001,cut_frames=[])
    result,audit=run(monkeypatch,data,recs,groups)
    assert [(g.start,g.end) for g in result]==[(g.start,g.end) for g in groups]
    assert not audit['bridges']


@pytest.mark.parametrize('failure',['open','decode','dimensions'])
def test_unavailable_source_never_authorizes_a_group_bridge(monkeypatch,failure):
    class Unavailable(ObservedSource):
        def __init__(self,*args):
            if failure=='open':raise OSError('missing source')
            super().__init__(*args)
        def get(self,frame):
            if failure=='decode':raise ValueError('incomplete source')
            return np.zeros((100,100,3),np.uint8)
    data,recs,groups=positive()
    result,audit=run(monkeypatch,data,recs,groups,reader=Unavailable)
    assert result==groups
    assert not audit['bridges']
    assert audit['reason']=='source_unavailable'


def test_source_pixels_reject_a_real_cut_even_when_pose_and_inventory_are_stale(monkeypatch):
    # Original adjacent source frames at the reviewed MMN group->closeup cut.
    root=FIXTURE.parent/'group_continuity_source'
    before=cv2.imread(str(root/'3576.png'));after=cv2.imread(str(root/'3577.png'))
    assert before is not None and after is not None
    class CutSource(ObservedSource):
        def get(self,frame):
            self.stats['reads']+=1
            return before if frame<2460 else after
    data,recs,groups=positive()
    result,audit=run(monkeypatch,data,recs,groups,reader=CutSource,cut_frames=[])
    assert result==groups
    assert not audit['bridges']
    assert any(r['reason']=='source_transition' for r in audit['rejected'])


def test_fully_observed_group_has_no_artificial_duration_limit(monkeypatch):
    data,recs,_=positive()
    prototype=recs[0]
    recs=[copy.deepcopy(prototype) for _ in range(100)]
    for i,r in enumerate(recs):
        r.t=i*4/data['fps']
        r.is_group=i in (0,99)
        # A simultaneous main handoff is independent of group membership.
        r.main_id=1 if i<50 else 2
    groups=[Segment('group',None,0,recs[1].t,[]),
            Segment('group',None,recs[-1].t,recs[-1].t+.2,[])]
    frozen=pickle.dumps(recs)
    result,audit=run(monkeypatch,data,recs,groups,cut_frames=[],exclusive_foreground_frames=[])
    assert len(result)==1 and result[0].end==groups[-1].end
    assert audit['bridges'][0]['end']-audit['bridges'][0]['start']>6
    assert pickle.dumps(recs)==frozen


def test_later_source_failure_rolls_back_earlier_proposed_join(monkeypatch):
    class PartialSource(ObservedSource):
        def get(self,frame):
            if frame>=12636:raise OSError('later window became unavailable')
            return super().get(frame)
    data,recs,groups=case('NEON')
    result,audit=run(monkeypatch,data,recs,groups,reader=PartialSource)
    assert result==groups and not audit['bridges']
    assert audit['reason']=='source_unavailable'


def shared_head_scene(*, shared=True, partial_competitor=False, jitter=0.):
    poses=[]
    for i in range(3):
        p=np.zeros((17,3));p[:,2]=.99
        p[:5,:2]=np.array([[480,200],[470,190],[490,190],[460,200],[500,200]])
        if not shared:p[:5,0]+=100*i
        else:p[:5,0]+=jitter*i
        p[[5,6,11,12],:2]=[[460+100*i,320],[500+100*i,320],[470+100*i,480],[490+100*i,480]]
        p[[13,14,15,16],:2]=[[470+100*i,550],[490+100*i,550],[470+100*i,620],[490+100*i,620]]
        poses.append(p)
    if partial_competitor:
        p=poses[0].copy();p[5:,2]=0.;poses.append(p)
    boxes=[np.array([450.,150.,810.,660.]) for _ in poses]
    recs=[FrameRec(i/15,1,boxes[0],i in (0,3),person_bboxes=copy.deepcopy(boxes),
                   person_pose_keypoints=copy.deepcopy(poses),scene_kind='main') for i in range(4)]
    groups=[Segment('group',None,0,1/15,[]),Segment('group',None,3/15,.3,[])]
    return dict(fps=60,cut_frames=[]),recs,groups


@pytest.mark.parametrize('case',['same_head','jittered_head','partial_head_competitor'])
def test_shared_observed_head_cannot_supply_independent_group_members(monkeypatch,case):
    data,recs,groups=shared_head_scene(shared=case!='partial_head_competitor',
        partial_competitor=case=='partial_head_competitor',jitter=1. if case=='jittered_head' else 0.)
    result,audit=run(monkeypatch,data,recs,groups)
    assert result==groups
    assert not audit['bridges']
    assert audit['source_reads']['reads']==0


def test_independently_observed_heads_and_torsos_can_share_detector_box_extent(monkeypatch):
    data,recs,groups=shared_head_scene(shared=False)
    result,audit=run(monkeypatch,data,recs,groups)
    assert len(result)==1 and len(audit['bridges'])==1


@pytest.mark.parametrize('case',['complementary_partial_heads','disjoint_partial_heads_with_third_person'])
def test_partial_head_hypotheses_do_not_prove_three_independent_heads(monkeypatch,case):
    data,recs,groups=shared_head_scene()
    for row in recs:
        visible=([0,1],[0,2],[3,4]) if case=='complementary_partial_heads' else ([0,1],[3,4],[0,1,2,3,4])
        for i,(pose,indices) in enumerate(zip(row.person_pose_keypoints,visible)):
            pose[:5,2]=.1;pose[list(indices),2]=.99
            if case=='disjoint_partial_heads_with_third_person' and i==2:pose[:5,0]+=200
    result,audit=run(monkeypatch,data,recs,groups)
    assert result==groups
    assert not audit['bridges']
    assert audit['source_reads']['reads']==0


def test_actual_ant134_turning_heads_are_withheld_without_complete_head_proof(monkeypatch):
    data,recs,groups=case('ANT')
    result,audit=run(monkeypatch,data,recs,groups)
    withheld=data['withheld_after_independent_head_review'][0]
    rejected=next(r for r in audit['rejected'] if r['start']==withheld['start'])
    assert rejected['reason']=='fewer_than_three_observed_members'
    assert all(b['start']!=withheld['start'] for b in audit['bridges'])
