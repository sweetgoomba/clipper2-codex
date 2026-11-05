"""Read only saved JSON. No repository imports, models, video decode, or project writes."""
from pathlib import Path
from collections import Counter,defaultdict
import json,hashlib
P=Path('/private/tmp/dance-fragment-priorities-20261103')
M=Path('/private/tmp/dance-continuity-next-20261103/baseline-manifest.json')
I=Path('/private/tmp/dance-episode-review-20261103/fragment-pattern-inventory.json')
G=Path('/private/tmp/dance-episode-review-20261103/same-name-gaps.json')
manifest=json.loads(M.read_text());inventory=json.loads(I.read_text());EPS=1e-6
candidate={'MMN':(104.57113333333334,104.90480000000001),'ANT':(64.43093333333333,64.89826666666667),'NEON':(98.29820000000001,98.53176666666667)}
def overlap(a,b):return max(0.,min(a['end'],b['end'])-max(a['start'],b['start']))
def named(x):return x and x.get('person_id') not in (None,'unknown')
def touch(a,b):return a and b and abs(a['end']-b['start'])<EPS
def counter(x):return dict(Counter(x))
def ranges(x):return [dict(start=v['range'][0],end=v['range'][1],**{k:y for k,y in v.items()if k!='range'})for v in x]
allrows=[];gaps=[];videos={};provenance=[]
for info in manifest:
 title=info['title'];base=Path(info['output_root']);mp=base/'json/dance_meta.json';ep=base/'diagnostics/face_evidence.json'
 meta=json.loads(mp.read_text());e=json.loads(ep.read_text());main=meta['lists']['main'];groups=meta['lists']['group'];fps=meta['stats']['fps'];step=meta['config']['analyze_skip']/fps
 assert len(main)==len(e['output_named_continuity']['performance_parts']['parts'])
 pp=e['output_named_continuity']['performance_parts'];spans=ranges(pp['identity_spans']);parts=pp['parts'];role=e['main_selection_refinement'];cuts=role['cut_frames'];handoffs=role['handoffs'];joints={int(f):j for f,j in e['secondary_reference_refinement']['joint_matches'].items()}
 observations={o['frame_index']:o for s in e['segments'][:e['main_result_count']]for o in s['owned_observations']};poses=e['pose_heads'];boundaries=[b for a in e['identity_refinement']for b in a['boundaries']]
 orig=inventory['videos'][title];rows=[]
 for typ,items in [('named',orig['named_short_rows']),('unknown',[x for x in orig['unknown_rows']if x['end']-x['start']<1-EPS]),('group',orig['group_short_rows'])]:
  for old in items:
   row=dict(old,video=title,kind=typ,seconds=old['end']-old['start']);a,b=row['start'],row['end'];target=candidate[title]
   row['excluded_direct_candidate']=abs(a-target[0])<EPS and abs(b-target[1])<EPS
   row['candidate_adjacent_named_fragment']=typ=='named' and (abs(b-target[0])<EPS or abs(a-target[1])<EPS)
   row['internal_cut_frames']=[f for f in cuts if a+EPS<f/fps<b-EPS]
   row['edge_cuts_one_source_frame']={edge:[f for f in cuts if abs(f/fps-row[edge])<=1.00001/fps]for edge in ('start','end')}
   row['nearby_handoffs_one_sample']=[h for h in handoffs if a-step-EPS<=h['time']<=b+step+EPS]
   row['role_correction_reasons']=counter(c['reason']for c in role['changes']if a<=c['time']<b)
   row['scene_reason_counts']=counter(p['scene_reason']for p in poses if a<=p['time_seconds']<b)
   row['scene_kinds']=counter(p['scene_kind']for p in poses if a<=p['time_seconds']<b)
   obs=[o for o in observations.values()if a<=o['time_seconds']<b]
   row['observed_samples']=len(obs);row['face_failures']=counter(o.get('failure')or 'none'for o in obs)
   row['valid_original_owned_faces']=sum(o.get('embedding') is not None and o.get('failure') is None and o.get('association')=='confirmed' and o.get('detector_score',0)>=.8 for o in obs)
   js=[joints[o['frame_index']]for o in obs if o['frame_index']in joints]
   row['joint_statuses']=counter(j.get('status')for j in js)
   row['accepted_joint_names']=counter(j.get('name')for j in js if j.get('status')=='accepted')
   row['identity_boundaries_near_edges']=counter(x['reason']for x in boundaries if min(abs(x['time']-a),abs(x['time']-b))<=step/2+EPS)
   row['original_identity_spans']=[dict(id=s['id'],start=s['start'],end=s['end'],name=s['name'],reason=s['reason'])for s in spans if overlap(row,s)>EPS]
   row['audit_rejections']={}
   for stage,items2 in [('body',e['body_continuity_refinement']['candidates']),('observed_member_edges',e['output_named_continuity']['observed_member_edges']['candidates']),('unknown_joins',e['output_named_continuity']['unknown_main_joins']['candidates'])]:
    row['audit_rejections'][stage]=counter(c.get('reason')for c in items2 if overlap(row,c)>EPS)
   if typ=='named':
    idx=next(i for i,r in enumerate(main)if r['clip_id']==row['clip_id']);part=parts[idx];row['source_spans']=part['source_spans']
    a_spans=[s for s in spans if s['id']in part['source_spans']]
    row['longer_same_named_identity_span']=any(s['name']==row['person_id'] and s['end']-s['start']>=1-EPS for s in a_spans)
    row['different_named_touching_neighbors']=[r['person_id']for r in (row.get('left'),row.get('right'))if named(r)and r['person_id']!=row['person_id']and(touch(r,row)or touch(row,r))]
    row['accepted_joint_agrees']=row['accepted_joint_names'].get(row['person_id'],0)>0
   rows.append(row)
 # Whole unknown blocks prevent counting artificial clip divisions as distinct episodes.
 for block in orig['unknown_blocks']:
  row=dict(block,video=title);a,b=row['start'],row['end'];row['excluded_candidate']=abs(a-candidate[title][0])<EPS and abs(b-candidate[title][1])<EPS
  row['internal_cuts']=[f for f in cuts if a+EPS<f/fps<b-EPS]
  row['nearby_handoffs']=[h['frame']for h in handoffs if a-step-EPS<=h['time']<=b+step+EPS]
  row['member_edge_reasons']=counter(c['reason']for c in e['output_named_continuity']['observed_member_edges']['candidates']if overlap(row,c)>EPS)
  row['body_reasons']=counter(c['reason']for c in e['body_continuity_refinement']['candidates']if overlap(row,c)>EPS)
  row['unknown_join_reasons']=counter(c['reason']for c in e['output_named_continuity']['unknown_main_joins']['candidates']if overlap(row,c)>EPS)
  gaps.append(row)
 videos[title]={'project_id':info['project_id'],'fps':fps,'samples_step_seconds':step,'mask_status':e['mask_continuity_refinement']['reason'],'joint_revalidation_status':e['secondary_reference_refinement']['identity_revalidation']['reason'],'counts':counter(r['kind']for r in rows),'main_count':len(main),'group_count':len(groups)}
 provenance.append({'video':title,'project_id':info['project_id'],'metadata_sha256':hashlib.sha256(mp.read_bytes()).hexdigest(),'evidence_sha256':hashlib.sha256(ep.read_bytes()).hexdigest()});allrows+=rows
assert counter(r['kind']for r in allrows)=={'named':71,'unknown':80,'group':79}
# All counts below exclude the three direct candidate intervals. Companion named
# fragments are separately excluded from proposed future investigation cohorts.
remaining=[r for r in allrows if not r['excluded_direct_candidate']]
future=[r for r in remaining if not r['candidate_adjacent_named_fragment']]
cohorts={}
def add(name,test):
 hits=[r for r in future if test(r)];cohorts[name]={'count':len(hits),'by_video':counter(r['video']for r in hits),'by_kind':counter(r['kind']for r in hits),'seconds':sum(r['seconds']for r in hits),'clips':[f"{r['video']}:{r['clip_id']}"for r in hits]};return hits
add('group_already_covered_by_one_named_main',lambda r:r['kind']=='group'and r['category']=='already_covered_by_one_named_main')
add('group_partly_overlaps_named_main',lambda r:r['kind']=='group'and r['category']=='partial_named_main_overlap')
add('group_same_named_bracket',lambda r:r['kind']=='group'and r['category']=='exact_same_named_bracket')
add('group_no_same_named_proof',lambda r:r['kind']=='group'and r['category']=='no_same_named_proof')
add('named_projection_of_longer_named_identity_span',lambda r:r['kind']=='named'and r['longer_same_named_identity_span'])
add('named_touching_unknown',lambda r:r['kind']=='named'and r['category']=='touches_unknown')
add('named_with_different_touching_name',lambda r:r['kind']=='named'and r['different_named_touching_neighbors'])
add('named_with_different_neighbor_and_original_joint',lambda r:r['kind']=='named'and r['different_named_touching_neighbors']and r['accepted_joint_agrees'])
add('named_with_different_neighbor_joint_and_cut_or_handoff',lambda r:r['kind']=='named'and r['different_named_touching_neighbors']and r['accepted_joint_agrees']and(any(r['edge_cuts_one_source_frame'].values())or r['nearby_handoffs_one_sample']))
add('unknown_no_valid_original_owned_face',lambda r:r['kind']=='unknown'and not r['valid_original_owned_faces'])
add('unknown_with_accepted_joint_names',lambda r:r['kind']=='unknown'and bool(r['accepted_joint_names']))
add('unknown_blocked_by_main_role',lambda r:r['kind']=='unknown'and 'unconfirmed_main_role'in r['audit_rejections']['observed_member_edges'])
add('unknown_with_recorded_contradiction',lambda r:r['kind']=='unknown'and any(any(x in reasons for x in ['conflicting_face_evidence','conflicting_original_names','repeated_original_face_change'])for reasons in r['audit_rejections'].values()))
add('unknown_interior_cut',lambda r:r['kind']=='unknown'and bool(r['internal_cut_frames']))
add('unknown_near_handoff',lambda r:r['kind']=='unknown'and bool(r['nearby_handoffs_one_sample']))
# Eligibility oscillation is a candidate structure only: group short bracketed
# by same name, without an internal recorded cut/handoff. Does not prove body.
add('group_same_name_no_internal_cut_or_handoff',lambda r:r['kind']=='group'and r['category']=='exact_same_named_bracket'and not r['internal_cut_frames']and not r['nearby_handoffs_one_sample'])
summary={'total_baseline_clips':len(allrows),'excluded_direct_candidate_rows':sum(r['excluded_direct_candidate']for r in allrows),'candidate_adjacent_named_fragments':sum(r['candidate_adjacent_named_fragment']for r in allrows),'remaining_inventory_rows':len(remaining),'future_investigation_rows':len(future),'future_kind_counts':counter(r['kind']for r in future),'cohorts_overlap':True,'cohorts':cohorts}
result={'method':'JSON only: structural candidates and original audit evidence, not visual ground truth or permission to merge','provenance':provenance,'videos':videos,'summary':summary,'rows':allrows,'unknown_blocks':gaps,'same_name_gaps_prior_inventory':json.loads(G.read_text())}
(P/'remaining-fragments.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'videos':videos,'summary':summary},ensure_ascii=False,indent=2))
