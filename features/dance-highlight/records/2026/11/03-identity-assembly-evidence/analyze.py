"""Read saved JSON only; no decoder, inference, or pipeline replay."""
import json
from pathlib import Path
from collections import Counter, defaultdict
import numpy as np
ROOT=Path.home()/'Library/Application Support/Clipper Studio Dev/projects/files/116957ce-bd03-4d4a-a21d-984dc12487aa'
OUT=Path('/private/tmp/dance-identity-assembly-20261103')
PROJECTS={'MMN':'1793649506337','ANT':'1793649573540','NEON':'1793649654322'}
EPS=1e-6

def valid(o):return o['association']=='confirmed' and not o['failure'] and o['embedding'] is not None and o['detector_score']>=.8

def inside(t,r):return r[0]-1e-7<=t<r[1]-1e-7

def overlaps(a,b):return min(a[1],b[1])-max(a[0],b[0])>EPS

def pair(fs,obs):return any(.15-1e-7<=abs(obs[f]['time_seconds']-obs[g]['time_seconds'])<=.6+1e-7 for i,f in enumerate(fs) for g in fs[i+1:])

def primary_matches(obs,refs):
 # Exact published centroid-then-two-photo rule; saved vectors only.
 groups=defaultdict(list)
 for r in refs:groups[r['reference_id']].append(r)
 names=sorted(groups);centroids=[];photos=[]
 for n in names:
  x=np.asarray([r['embedding'] for r in groups[n]],np.float32);mu=x.mean(axis=0);centroids.append(mu/(np.linalg.norm(mu)+1e-9))
  photos.append(np.asarray(list({r['image_sha256']:r['embedding'] for r in groups[n]}.values()),np.float32))
 result={}
 for f,o in obs.items():
  if not valid(o):continue
  v=np.asarray(o['embedding'],np.float32)
  if not np.isfinite(v).all() or abs(float(np.linalg.norm(v))-1)>1e-5:continue
  ds=np.clip(1-np.asarray(centroids)@v,0,2);order=sorted(range(len(names)),key=lambda i:(float(ds[i]),names[i]));best=order[0];margin=float(ds[order[1]]-ds[best]) if len(order)>1 else None
  name=names[best] if ds[best]<=.6 and (margin is None or margin>=.08) else None
  reason='accepted' if name else 'distance_exceeded' if ds[best]>.6 else 'insufficient_margin'
  distances=[{'name':names[i],'distance':float(ds[i])} for i in order];mode='centroid'
  if not name:
   vd=[float(np.sort(np.clip(1-x@v,0,2))[min(1,len(x)-1)]) for x in photos];vo=sorted(range(len(names)),key=lambda i:(vd[i],names[i]));b=vo[0];mg=vd[vo[1]]-vd[b] if len(vo)>1 else None
   if vd[b]<=.6 and (mg is None or mg>=.08) and len(photos[b])>=2:
    name=names[b];reason='supported_reference_views';mode='two_photo';margin=mg;distances=[{'name':names[i],'distance':vd[i]} for i in vo]
  result[f]={'name':name,'reason':reason,'mode':mode,'best':distances[0]['name'],'distance':distances[0]['distance'],'margin':margin,'candidates':distances}
 return result

results={}
for label,project in PROJECTS.items():
 base=ROOT/project;e=json.loads((base/'diagnostics/face_evidence.json').read_text());m=json.loads((base/'json/dance_meta.json').read_text());pp=e['output_named_continuity']['performance_parts'];spans=pp['identity_spans'];parts=pp['parts'];fps=m['stats']['fps']
 obs={o['frame_index']:o for s in e['segments'][:e['main_result_count']] for o in s.get('owned_observations',[])}
 primary=primary_matches(obs,e['references']);joint={int(f):v for f,v in e['secondary_reference_refinement']['joint_matches'].items()};secondary={r['frame_index']:r for r in e['secondary_reference_refinement']['matches']}
 poses={round(p['time_seconds']*fps):p for p in e['pose_heads']}; roles={r['frame']:r for r in e['main_selection_refinement']['role_observations']};handoffs=e['main_selection_refinement']['handoffs'];cuts=e['main_selection_refinement']['cut_frames'];changes=e['scene_boundary_refinement']['changes']
 boundaries=[dict(parent_index=r['parent_index'],**b) for r in e['identity_refinement'] for b in r.get('boundaries',[])];named=defaultdict(set)
 for r in [*e['identity_refinement'],*e['secondary_reference_refinement']['interval_refinements']]:
  for n in r.get('named_ranges',[]):named[n['name']].update(n['support_frames'])
 eligible=[]
 for p in parts:
  a,b=p['range']
  if eligible and abs(eligible[-1][1]-a)<EPS:eligible[-1][1]=b
  else:eligible.append([a,b])
 def eligible_at(t):return any(inside(t,r) for r in eligible)
 def brief(f):
  o=obs[f];j=joint.get(f,{});s=secondary.get(f,{});p=poses.get(f,{});r=roles.get(f,{})
  return {'frame':f,'time':o['time_seconds'],'valid_owned_face':valid(o),'face_score':o['detector_score'],'failure':o['failure'],'association':o['association'],'primary':primary.get(f,{}),'joint':{k:j.get(k) for k in ['name','status','best','reason','distance','margin']},'secondary':{k:s.get(k) for k in ['name','reason']},'timeline_support_names':[n for n,fs in named.items() if f in fs],'scene':p.get('scene_kind'),'scene_reason':p.get('scene_reason'),'role_reason':r.get('reason')}
 def supports(fs,name):
  direct=[f for f in fs if primary.get(f,{}).get('name')==name]
  accepted=[f for f in fs if joint.get(f,{}).get('status')=='accepted' and joint[f].get('name')==name]
  clean=[f for f in set(direct+accepted) if joint.get(f,{}).get('status')!='conflict' and primary.get(f,{}).get('name') in (None,name) and (joint.get(f,{}).get('status')!='accepted' or joint[f].get('name')==name)]
  return {'primary_direct':direct,'joint_accepted':accepted,'clean_independent':sorted(clean),'clean_independent_pair':pair(clean,obs),'timeline_support':[f for f in fs if f in named[name]]}
 records=[]
 for i,p in enumerate(parts):
  a,b=p['range'];ss=[spans[n] for n in p['source_spans']];fs=[f for f,o in obs.items() if inside(o['time_seconds'],[a,b])];sfs=sorted({f for s in ss for f in s['observation_frames'] if f in obs});same=[s for s in ss if s['name']==p['name']];pruned=bool(len(ss)==1 and (a>ss[0]['range'][0]+EPS or b<ss[0]['range'][1]-EPS));duration=b-a
  rec={'index':i,**p,'duration':duration,'short':duration<1,'source_identity_spans':ss,'single_parent_trimmed':pruned,'created_short_from_long':bool(duration<1 and pruned and ss[0]['range'][1]-ss[0]['range'][0]>=1),'frames_inside':fs,'valid_owned_faces_inside':[f for f in fs if valid(obs[f])],'support_inside':supports(fs,p['name']) if p['name'] else None,'support_parent':supports(sfs,p['name']) if p['name'] else None,'previous':parts[i-1] if i else None,'next':parts[i+1] if i+1<len(parts) else None,'cuts_inside_or_at_edges':[f for f in cuts if a-1e-7<=f/fps<=b+1e-7],'handoffs_inside_or_bracketing':[h for h in handoffs if h.get('previous_time',h['time'])<=b+EPS and h['time']>=a-EPS],'scene_changes_at_edges':[c for c in changes if min(abs(c['cut_time']-a),abs(c['cut_time']-b))<EPS],'identity_boundaries_at_edges':[q for q in boundaries if min(abs(q['time']-a),abs(q['time']-b))<EPS]}
  if p['name']:
   rec['accepted_support_outside_part']=[f for f in rec['support_parent']['clean_independent'] if f not in rec['support_inside']['clean_independent']]
   rec['accepted_support_outside_eligibility']=[f for f in rec['support_parent']['clean_independent'] if not eligible_at(obs[f]['time_seconds'])]
   rec['support_class']='direct_pair_inside' if rec['support_inside']['clean_independent_pair'] else 'direct_hit_inside_without_independent_pair' if rec['support_inside']['clean_independent'] else 'only_parent_independent_support' if rec['support_parent']['clean_independent'] else 'no_direct_or_joint_accepted_support_in_parent'
  rec['observations']=[brief(f) for f in fs] if duration<1 else []
  records.append(rec)
 samebound=[]
 for a,b in zip(spans,spans[1:]):
  if not a['name'] or a['name']!=b['name'] or abs(a['range'][1]-b['range'][0])>EPS:continue
  t=a['range'][1];both=[i for i,p in enumerate(parts) if a['id'] in p['source_spans'] and b['id'] in p['source_spans'] and p['name']==a['name']];left=[i for i,p in enumerate(parts) if p['name']==a['name'] and abs(p['range'][1]-t)<EPS];right=[i for i,p in enumerate(parts) if p['name']==a['name'] and abs(p['range'][0]-t)<EPS]
  samebound.append({'left_span':a['id'],'right_span':b['id'],'name':a['name'],'time':t,'merged_output_parts':both,'left_output_parts_at_boundary':left,'right_output_parts_at_boundary':right,'retained_touching_boundary':bool(left and right),'identity_boundary':[q for q in boundaries if abs(q['time']-t)<EPS]})
 counts={'main_parts':len(parts),'named_parts':sum(bool(p['name']) for p in parts),'unknown_parts':sum(not p['name'] for p in parts),'named_short':sum(r['short'] and bool(r['name']) for r in records),'unknown_short':sum(r['short'] and not r['name'] for r in records),'named_short_trimmed':sum(r['short'] and bool(r['name']) and r['single_parent_trimmed'] for r in records),'unknown_short_trimmed':sum(r['short'] and not r['name'] and r['single_parent_trimmed'] for r in records),'named_short_from_long':sum(bool(r['name']) and r['created_short_from_long'] for r in records),'unknown_short_from_long':sum(not r['name'] and r['created_short_from_long'] for r in records),'same_name_original_boundaries':len(samebound),'same_name_retained_touching_boundaries':sum(r['retained_touching_boundary'] for r in samebound)}
 counts['named_short_support']=dict(Counter(r['support_class'] for r in records if r['short'] and r['name']))
 counts['named_trimmed_short_support']=dict(Counter(r['support_class'] for r in records if r['short'] and r['name'] and r['single_parent_trimmed']))
 results[label]={'project':project,'fps':fps,'counts':counts,'parts':records,'same_name_original_boundaries':samebound,'projection':pp['projection'],'eligibility_union_of_final_main_parts':eligible,'original_direct_matches':{str(f):v for f,v in primary.items()},'all_original_observation_briefs':{str(f):brief(f) for f in obs}}
 print(label,json.dumps(counts,ensure_ascii=False))
 print('TRIMMED NAMED',[(r['index'],r['range'],r['name'],r['support_class'],r['support_inside']['clean_independent']) for r in records if r['short'] and r['name'] and r['single_parent_trimmed']])
 print('SAME RETAINED',[r for r in samebound if r['retained_touching_boundary']])
(OUT/'inventory.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
