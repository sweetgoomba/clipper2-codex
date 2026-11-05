"""Read original JSON and evaluate numeric gate predicates with stdlib only."""
from pathlib import Path
from collections import Counter
import math,json
P=Path('/private/tmp/dance-fragment-priorities-20261103')
manifest=json.loads(Path('/private/tmp/dance-continuity-next-20261103/baseline-manifest.json').read_text())
inventory=json.loads((P/'remaining-fragments.json').read_text());targets=[r for r in inventory['triage_rows']if r['triage_bucket']=='unknown_main_role_unproven']
allowed={'dominant_face','confirmed_dominant_face','corroborated_foreground_subject','confirmed_corroborated_foreground_subject'}
def same(a,b):return a is not None and b is not None and len(a)==len(b)and all(abs(x-y)<=1e-3 for x,y in zip(a,b))
def norm(x):return math.sqrt(sum(t*t for t in x))
def dist(a,b):return norm([x-y for x,y in zip(a,b)])
def mean(xs):return sum(xs)/len(xs)
def valid(o):return o and o.get('embedding')is not None and o.get('failure')is None and o.get('association')=='confirmed'and o.get('detector_score',0)>=.8
def retained(boxes,poses):
 suppressed=set()
 for i,a in enumerate(boxes):
  for j,b in enumerate(boxes):
   if i==j:continue
   area=(a[2]-a[0])*(a[3]-a[1]);other=(b[2]-b[0])*(b[3]-b[1]);inter=max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]))
   if area<=0 or other<=area or inter/area<.9:continue
   ka,kb=poses[i],poses[j];common=[k for k in range(5)if ka[k][2]>=.5 and kb[k][2]>=.5]
   if len(common)<3:continue
   xy=[p[:2]for p in kb[:5]if p[2]>=.5];span=dist([min(p[0]for p in xy),min(p[1]for p in xy)],[max(p[0]for p in xy),max(p[1]for p in xy)])
   if span<=0 or max(dist(ka[k][:2],kb[k][:2])for k in common)>.3*span:continue
   torso=[5,6,11,12];shared=[k for k in torso if ka[k][2]>=.5 and kb[k][2]>=.5];ac=sum(ka[k][2]>=.5 for k in torso);bc=sum(kb[k][2]>=.5 for k in torso)
   more=bc>=3 and bc>=ac+2 and bool(shared)and max(dist(ka[k][:2],kb[k][:2])for k in shared)<=.3*span
   if more or sum(kb[k][2]>=.5 for k in [13,14,15,16])>=sum(ka[k][2]>=.5 for k in [13,14,15,16])+2:suppressed.add(i)
 return [i for i in range(len(boxes))if i not in suppressed]
def describe(o,p,role,joint,width,height):
 boxes=p['body_boxes'];poses=p['pose_keypoints'];target=o['body_bbox'];selected=[i for i,b in enumerate(boxes)if same(b,target)];idx=selected[0]if len(selected)==1 else None
 kept=retained(boxes,poses);f=next((f for f in role.get('features',[])if same(f['box'],target)),None);measured=[];bad=[]
 for i in kept:
  b=boxes[i];pose=poses[i]
  if b[2]<.25*width or b[0]>.75*width:continue
  torso=[pose[k]for k in [5,6,11,12]]
  issues=[]
  if any(not all(math.isfinite(v)for v in t)for t in torso):issues.append('nonfinite')
  if any(t[2]<.75 for t in torso):issues.append('torso_confidence_below_0.75')
  if any(not(max(0,b[0])<=t[0]<min(width,b[2])and max(0,b[1])<=t[1]<min(height,b[3]))for t in torso):issues.append('torso_outside_observed_body_or_image')
  length=dist([mean([t[0]for t in torso[:2]]),mean([t[1]for t in torso[:2]])],[mean([t[0]for t in torso[2:]]),mean([t[1]for t in torso[2:]])])
  if length<4 or max(t[0]for t in torso)-min(t[0]for t in torso)<=0:issues.append('degenerate_torso')
  measured.append({'index':i,'selected':i==idx,'length_px':length,'issues':issues})
  if issues:bad.append({'index':i,'selected':i==idx,'issues':issues})
 chosen=next((v for v in measured if v['selected']),None);other=max((v['length_px']for v in measured if not v['selected']),default=0)
 torso_reasons=[]
 if bad:torso_reasons+=sorted({s for b in bad for s in b['issues']})
 if not chosen:torso_reasons.append('selected_body_not_retained_in_central_half')
 else:
  if chosen['length_px']<.08*height:torso_reasons.append('selected_torso_below_0.08_height')
  if chosen['length_px']<1.08*other:torso_reasons.append('selected_torso_not_1.08x_all_central_rivals')
 features=role.get('features',[]);all_feature_boxes=all(i<len(boxes)and same(feat['box'],boxes[i])for feat in features for i in [feat['index']]);features_complete=sorted(v['index']for v in features)==kept
 def score(v):return v['size']/height*max(0,1-abs(v['x']-width/2)/(width/2))**2 if v.get('size')is not None and v.get('x')is not None else None
 sf=score(f)if f else None;rival_scores=[score(v)for v in features if v is not f and score(v)is not None];max_other=max(rival_scores,default=0)
 face_other=max((v['size']for v in features if v is not f and v.get('size')is not None),default=0)
 return {'frame':o['frame_index'],'time':o['time_seconds'],'scene_kind':p['scene_kind'],'scene_reason':p['scene_reason'],'candidate_box_matches_owned':same(p.get('candidate_main_bbox'),target),'role_box_matches_owned':same(role.get('box'),target),'role_reason':role.get('reason'),'role_reason_allowed':role.get('reason')in allowed,'selected_index':idx,'selected_feature_source':f.get('source')if f else None,'selected_feature_size_px':f.get('size')if f else None,'selected_feature_x_px':f.get('x')if f else None,'role_feature_inventory_matches_original_retained':features_complete and all_feature_boxes,'body_count':len(boxes),'retained_body_count':len(kept),'central_torso_count':len(measured),'missing_measured_face_competitors':sum(v is not f and v.get('source')!='detected'for v in features),'face_size_ratio_to_largest_measured_rival':f['size']/face_other if f and f.get('size')is not None and face_other else None,'weighted_face_score_ratio':sf/max_other if sf is not None and max_other else None,'weighted_face_score_margin':sf-max_other if sf is not None else None,'valid_owned_face':valid(o),'detector_score':o.get('detector_score'),'face_failure':o.get('failure'),'joint':{k:joint.get(k)for k in ['name','status','best','distance','margin','primary','secondary']},'torso_gate_pass':not torso_reasons,'torso_gate_failures':torso_reasons,'torso_measurements':measured,'selected_torso_ratio_to_largest_central_rival':chosen['length_px']/other if chosen and other else None,'selected_torso_height_fraction':chosen['length_px']/height if chosen else None}
allc=[];perclip=[]
for info in manifest:
 title=info['title'];e=json.loads((Path(info['output_root'])/'diagnostics/face_evidence.json').read_text());meta=json.loads((Path(info['output_root'])/'json/dance_meta.json').read_text());fps=meta['stats']['fps'];width,height=meta['diagnostics']['frame_width'],meta['diagnostics']['frame_height'];obs={o['frame_index']:o for s in e['segments'][:e['main_result_count']]for o in s['owned_observations']};poses={round(p['time_seconds']*fps):p for p in e['pose_heads']};roles={r['frame']:r for r in e['main_selection_refinement']['role_observations']};joints={int(f):v for f,v in e['secondary_reference_refinement']['joint_matches'].items()}
 ids=[r for r in targets if r['video']==title]
 candidates=e['output_named_continuity']['observed_member_edges']['candidates']
 for c in candidates:
  hits=[r for r in ids if r['start']<c['end']-1e-6 and c['start']<r['end']-1e-6]
  if not hits or c['reason']!='unconfirmed_main_role':continue
  a,b=[obs[f]for f in c['seed_frames']];lo,hi=(a['time_seconds'],c['end'])if c['direction']=='left'else(c['start'],b['time_seconds']+1/fps)
  local=[o for o in obs.values()if lo<=o['time_seconds']<hi];local.sort(key=lambda o:o['frame_index']);frames=[describe(o,poses[o['frame_index']],roles.get(o['frame_index'],{}),joints.get(o['frame_index'],{}),width,height)for o in local];unknown=[f for f in frames if c['start']<=f['time']<c['end']]
  fg=[f for f in frames if f['role_reason_allowed']and f['role_box_matches_owned']and f['selected_feature_source']=='detected'and f['selected_feature_size_px']is not None]
  for f in unknown:f['distance_to_actual_foreground_seconds']=min((abs(g['time']-f['time'])for g in fg),default=None)
  fail=[]
  if not unknown:fail.append('no_unknown_samples')
  if not fg:fail.append('no_direct_foreground_anchor_in_local_seed_window')
  if any(not f['torso_gate_pass']for f in unknown):fail.append('unique_foreground_torso_failed')
  if fg and any(f['distance_to_actual_foreground_seconds']>.600001 for f in unknown):fail.append('direct_foreground_anchor_farther_than_0.600001_seconds')
  item={'video':title,'clips':[r['clip_id']for r in hits],'candidate':c,'local_window':[lo,hi],'actual_foreground_frames':[f['frame']for f in fg],'runtime_gate_subfailures':fail,'local_role_reason_counts':dict(Counter(f['role_reason']for f in frames)),'unknown_role_reason_counts':dict(Counter(f['role_reason']for f in unknown)),'selected_feature_sources':dict(Counter(f['selected_feature_source']for f in unknown)),'unknown_torso_failures':dict(Counter(k for f in unknown for k in f['torso_gate_failures'])),'unknown_samples':len(unknown),'unknown_valid_faces':sum(f['valid_owned_face']for f in unknown),'unknown_accepted_joint_names':dict(Counter(f['joint']['name']for f in unknown if f['joint']['status']=='accepted')),'unknown_best_joint_names':dict(Counter(f['joint']['best']for f in unknown if f['joint']['best'])),'unknown_scene_counts':dict(Counter(f['scene_kind']for f in unknown)),'unknown_joint_statuses':dict(Counter(f['joint']['status']for f in unknown)),'frames':frames}
  assert fail,(title,c)
  allc.append(item)
 for r in ids:
  hit=[c for c in allc if c['video']==title and r['clip_id']in c['clips']];assert hit
  perclip.append(dict(r,candidate_count=len(hit),subfailures=sorted({k for c in hit for k in c['runtime_gate_subfailures']}),torso_failures=sorted({k for c in hit for k in c['unknown_torso_failures']})))
summary={'clips':len(perclip),'candidate_attempts':len(allc),'unique_unknown_blocks':len({(c['video'],c['candidate']['start'],c['candidate']['end'])for c in allc}),'attempt_subfailure_counts':dict(Counter(k for c in allc for k in c['runtime_gate_subfailures'])),'clip_subfailure_counts':dict(Counter(k for c in perclip for k in c['subfailures'])),'clip_torso_subfailures':dict(Counter(k for c in perclip for k in c['torso_failures'])),'unknown_scene_kinds':dict(Counter(k for c in allc for k in c['unknown_scene_counts'])),'box_or_inventory_mismatch_frames':[dict(video=c['video'],frame=f['frame'],role_match=f['role_box_matches_owned'],candidate_match=f['candidate_box_matches_owned'],inventory_match=f['role_feature_inventory_matches_original_retained'])for c in allc for f in c['frames']if not(f['role_box_matches_owned']and f['candidate_box_matches_owned']and f['role_feature_inventory_matches_original_retained'])]}
result={'method':'JSON-only predicate reproduction; no models, decode, hashes, or product changes. Numeric calculations use original source pixel coordinates and seconds. Does not run downstream continuity gates.','summary':summary,'clips':perclip,'candidates':allc}
(P/'role-gate-18-details.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False,indent=2))
for c in allc:print(c['video'],c['clips'],c['candidate']['start'],c['candidate']['end'],c['candidate']['name'],c['candidate']['direction'],c['runtime_gate_subfailures'],c['unknown_role_reason_counts'],c['selected_feature_sources'],c['unknown_torso_failures'])
