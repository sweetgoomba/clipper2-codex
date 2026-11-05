"""Independent pure-function checks of fixed bridge and cached scene replay."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,sys
import numpy as np
from dance_highlight.services import segment as old
from dance_highlight.services.native_scene import refine_with_scene_observations
P=Path('/private/tmp/dance-role-continuity-review-20261102')
spec=importlib.util.spec_from_file_location('dance_highlight.services.bridge_final',P/'bridge-final-segment.py')
s=importlib.util.module_from_spec(spec);sys.modules[spec.name]=s;spec.loader.exec_module(s)
node=next(n for n in ast.parse((P/'reproduce_bridge_foreground.py').read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='human_pose')
ns={'np':np};exec(compile(ast.Module(body=[node],type_ignores=[]),'independent-human-fixture','exec'),ns);human_pose=ns['human_pose']
d=json.loads((P/'bridge-final-fixture.json').read_text())
def row(r):
    group=r.get('scene_kind')=='group'
    return s.FrameRec(r['time_seconds'],None if group else r['candidate_main_id'],None if group or r['candidate_main_bbox'] is None else np.array(r['candidate_main_bbox']),group,
        person_bboxes=[np.array(b) for b in r['body_boxes']],group_bboxes=[np.array(b) for b in r.get('group_bboxes',[])],person_pose_keypoints=[np.array(p) for p in r['pose_keypoints']],person_head_keypoints=[np.array(p) for p in r.get('head_keypoints',[])],scene_kind=r.get('scene_kind','main'),scene_reason=r.get('scene_reason','main_eligible_composition'),candidate_main_id=r['candidate_main_id'],candidate_main_bbox=None if r['candidate_main_bbox'] is None else np.array(r['candidate_main_bbox']))
cases=[]
names=['positive','foreground_at_old_art','missing_pose','mismatched_pose_count','bad_pose_shape','nonfinite_pose','missing_native_anchor','ambiguous_native_anchor','duplicate_observed_body','new_observed_body','central_one_sample','cut_at_gap','cut_at_right','handoff','camera_episode','missing_inventory','missing_sample','clipped_observed_body','no_person']
for name in names:
    rows=[row(r) for r in d['rows']];target=next(r for r in rows if round(r.t*d['fps'])==d['target_frame']);idx=next(i for i,r in enumerate(rows) if r is target)
    args=dict(video_size=(1920,1080),fps=d['fps'],sample_step=d['sample_step'],cut_frames=[],handoffs=[],camera_episodes=[])
    if name=='foreground_at_old_art':target.person_pose_keypoints[1]=human_pose(target.person_bboxes[1])
    if name=='missing_pose':target.person_pose_keypoints=[]
    if name=='mismatched_pose_count':target.person_pose_keypoints.pop()
    if name=='bad_pose_shape':target.person_pose_keypoints[0]=np.zeros((5,3))
    if name=='nonfinite_pose':target.person_pose_keypoints[0][0,0]=np.nan
    if name=='missing_native_anchor':rows[idx-1].group_bboxes=[]
    if name=='ambiguous_native_anchor':rows[idx-1].group_bboxes.append(rows[idx-1].group_bboxes[1].copy())
    if name=='duplicate_observed_body':target.person_bboxes[1]=target.person_bboxes[0].copy();target.person_pose_keypoints[1]=target.person_pose_keypoints[0].copy()
    if name=='new_observed_body':target.person_bboxes[0]+=np.array([400,0,400,0]);target.person_pose_keypoints[0][:,0]+=400
    if name=='central_one_sample':target.person_bboxes[0]=np.array([920.,500.,1000.,700.]);target.person_pose_keypoints[0]=human_pose(target.person_bboxes[0])
    if name=='cut_at_gap':args['cut_frames']=[d['target_frame']]
    if name=='cut_at_right':args['cut_frames']=[d['target_frame']+d['sample_step']]
    if name=='handoff':args['handoffs']=[{'time':target.t}]
    if name=='camera_episode':args['camera_episodes']=[{'start_frame':d['target_frame'],'end_frame':d['target_frame']}]
    if name=='missing_inventory':args['handoffs']=None
    if name=='missing_sample':rows.pop(idx-1)
    if name=='clipped_observed_body':target.person_bboxes[0][0]=0;target.person_pose_keypoints[0]=human_pose(target.person_bboxes[0])
    if name=='no_person':target.scene_kind='no_person'
    expected='group' if name=='positive' else target.scene_kind
    out,audit=s.bridge_compact_group_gaps(rows,**args);actual=next(r.scene_kind for r in out if r.t==target.t)
    assert actual==expected,(name,actual,audit)
    if name=='positive':
        assert audit['bridges'][0]['left_anchor_frame']==8608 and audit['bridges'][0]['right_anchor_frame']==8616
        assert audit['bridges'][0]['observed_body_counts']==[2] and audit['bridges'][0]['unobserved_box_counts']==[1]
        assert target.scene_kind=='main' and target.main_bbox is not None
    else:assert not audit['bridges'],(name,audit)
    cases.append({'case':name,'expected':expected,'actual':actual,'passed':True,'audit':audit})

manifest=json.loads((P/'manifest.json').read_text());replays={}
for label,c in manifest.items():
    evidence=json.loads(Path(c['evidence']).read_text());meta=json.loads(Path(c['meta']).read_text());size=(meta['diagnostics']['frame_width'],meta['diagnostics']['frame_height']);fps=c['fps']
    records=[]
    for r in evidence['pose_heads']:
        q=row(r);q.main_id=r['candidate_main_id'];q.main_bbox=None if r['candidate_main_bbox'] is None else np.array(r['candidate_main_bbox']);q.is_group=False;q.scene_kind='main';q.scene_reason='main_eligible_composition';records.append(q)
    changed_base=[round(r.t*fps) for r in records if bool(old.distributed_full_body_ensemble(r,size))!=bool(s.distributed_full_body_ensemble(r,size))]
    assert not changed_base,(label,changed_base)
    native={r['frame']:r['persons'] for r in evidence['native_scene_refinement']['observations']};roles=evidence['main_selection_refinement']
    before,_=refine_with_scene_observations(old.classify_main_scenes(records,size),native,video_size=size,fps=fps,cut_frames=roles['cut_frames'])
    proposed,_=refine_with_scene_observations(s.classify_main_scenes(records,size),native,video_size=size,fps=fps,cut_frames=roles['cut_frames'])
    after,audit=s.bridge_compact_group_gaps(proposed,video_size=size,fps=fps,sample_step=4,cut_frames=roles['cut_frames'],handoffs=roles['handoffs'],camera_episodes=roles['camera_episodes'])
    ranges=[]
    for i,(a,b) in enumerate(zip(before,after)):
        assert not(a.scene_kind=='group' and b.scene_kind!='group'),(label,i)
        if a.scene_kind!=b.scene_kind:
            end=records[i+1].t if i+1<len(records) else records[i].t
            if ranges and abs(ranges[-1]['end']-records[i].t)<1e-8:ranges[-1]['end']=end;ranges[-1]['frames'].append(round(records[i].t*fps))
            else:ranges.append({'start':records[i].t,'end':end,'frames':[round(records[i].t*fps)],'before':a.scene_kind,'after':b.scene_kind})
    replays[label]={'observations':len(records),'existing_distributed_predicate_changes':changed_base,'scene_changes':ranges,'bridge_audit':audit}
    print(label,json.dumps(replays[label],ensure_ascii=False),flush=True)
result={'segment_sha256':hashlib.sha256((P/'bridge-final-segment.py').read_bytes()).hexdigest(),'fixture_sha256':hashlib.sha256((P/'bridge-final-fixture.json').read_bytes()).hexdigest(),'independent_cases':cases,'cached_three_video_replay':replays,'all_checks_passed':True,'scope':'Frozen pure functions and saved native/regular observations only; no full product suite, new inference, video decode, or actual-app rerun.'}
(P/'bridge-final-independent-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print('PASS independent cases',len(cases),'predicate observations',sum(r['observations'] for r in replays.values()),'source',result['segment_sha256'])
