"""Read saved runs only. No model inference and no product writes."""
import hashlib
import json
import statistics
from collections import defaultdict
from pathlib import Path

O = Path('/private/tmp/dance-astra-review-20261102')
B = Path('/private/tmp/dance-mask-cost-20261102')
manifest = json.loads((O/'manifest.json').read_text())
runs = json.loads((B/'optimized/run-comparison.json').read_text())
coverage = json.loads((B/'disabled/identity-coverage-comparison.json').read_text())
results = {}
inputs = {}
critical = {'MMN': [(38.20473333333334,39.3393)], 'ANT': [(4.571233333333334,6.139466666666666),(9.9098,10.276933333333334)], 'NEON': []}

def compact(a):
    trace=a.get('trace',[])
    return {**{k:a.get(k) for k in ('name','anchor_frame','seed_kind','accepted','reason','elapsed_seconds')},
            'trace_count':len(trace),
            'trace_extent':[min(t['frame'] for t in trace),max(t['frame'] for t in trace)] if trace else None,
            'support_count':len(a.get('support_frames',[])),
            'camera':[{'from_frame':x.get('from_frame'),'to_frame':x.get('to_frame'),'accepted':x.get('accepted'),'reason':x.get('reason'),'exact_reason':x.get('exact_rejection',{}).get('reason'),'evidence_frames':x.get('evidence_frames')} for x in a.get('camera',[])],
            'whole_rejection':a.get('whole_path_rejection',{}).get('reason'),
            'partial_rejection':a.get('partial_retry',{}).get('reason')}

for n, run, cov in zip(('MMN','ANT','NEON'),runs,coverage,strict=True):
    path=B/'optimized/new'/run['project_id']/'face_evidence.json'
    e=json.loads(path.read_text())
    inputs[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
    mask=e['mask_continuity_refinement']; joint=e['secondary_reference_refinement']['identity_revalidation']
    attempts=[{**compact(a),'candidate_start':c['start'],'candidate_end':c['end']} for c in mask['candidates'] for a in c['attempts']]
    groups=defaultdict(lambda:dict(count=0,accepted=0,seconds=0.,accepted_seconds=0.))
    for a in attempts:
        g=groups[a['seed_kind'] or 'precheck_without_seed_kind']; g['count']+=1;g['accepted']+=bool(a['accepted']);g['seconds']+=a['elapsed_seconds'] or 0.;g['accepted_seconds']+=(a['elapsed_seconds'] or 0.) if a['accepted'] else 0.
    elapsed=[a['elapsed_seconds'] for a in attempts if a['elapsed_seconds'] is not None]
    good=[a for a in attempts if a['accepted']]; bad=[a for a in attempts if not a['accepted']]
    model=mask['model']
    candidate_rows=[]
    for c in mask['candidates']:
        accepted=[a for a in c['attempts'] if a.get('accepted')]
        if accepted or any(c['start']<b and a<c['end'] for a,b in critical[n]):
            candidate_rows.append(dict(start=c['start'],end=c['end'],reason=c['reason'],
                recovered_ranges=c.get('recovered_ranges',[]),
                total_attempt_seconds=sum(a.get('elapsed_seconds',0.) for a in c['attempts']),
                attempts=[compact(a) for a in c['attempts']]))
    latest=json.loads(Path(manifest[n]['meta']).read_text())
    proposals=json.loads((O/f'{n}-one-sided-summary.json').read_text())['proposals']
    remaining=[]
    for c in cov['changes']:
        if c['after']!=['unknown']: continue
        bounds=sorted({c['start'],c['end'],*[v for r in latest['lists']['main'] for v in (r['start'],r['end']) if c['start']<v<c['end']]})
        for a,b in zip(bounds,bounds[1:]):
            mid=(a+b)/2; names={r['person_id'] for r in latest['lists']['main'] if r['start']<=mid<r['end']}
            if names=={'unknown'}:
                remaining.append(dict(start=a,end=b,old_sam_name=c['before'][0],
                    one_sided_overlap=sum(max(0.,min(b,p['end'])-max(a,p['start'])) for p in proposals if p['name']==c['before'][0])))
    roles=[]
    latest_e=json.loads(Path(manifest[n]['evidence']).read_text())
    for p in proposals:
        lo,hi=p['proof']['proof_frames']
        local=[r for r in latest_e['pose_heads'] if lo<=round(r['time_seconds']*manifest[n]['fps'])<=hi]
        reasons=defaultdict(int)
        for r in local:reasons[r['scene_reason']]+=1
        roles.append(dict(start=p['start'],end=p['end'],name=p['name'],proof_frames=[lo,hi],scene_reasons=dict(reasons),
            selection_changes=[c for c in latest_e['main_selection_refinement']['changes'] if lo<=c['frame']<=hi],
            overlapping_camera_episodes=[c for c in latest_e['main_selection_refinement'].get('camera_episodes',[]) if c['start_frame']<=hi and lo<=c['end_frame']]))
    results[n]=dict(project_id=run['project_id'],source_sha=e['runtime']['video_sha256'],
        same_source_as_latest=e['runtime']['video_sha256']==latest_e['runtime']['video_sha256'],
        stage_seconds={k:run['performance']['stage_seconds'][k] for k in ['mask_continuity','joint_identity']},
        mask_raw_recovered=mask['recovered_seconds'],mask_output_changes=mask['output_changes'],joint_output_changes=joint['output_changes'],
        attempt_count=len(attempts),accepted_count=len(good),rejected_count=len(bad),
        attempt_seconds=sum(elapsed),accepted_seconds=sum(a['elapsed_seconds'] or 0. for a in good),
        rejected_seconds=sum(a['elapsed_seconds'] or 0. for a in bad),
        attempt_median=statistics.median(elapsed),attempt_max=max(elapsed),
        stage_minus_attempt_timers=run['performance']['stage_seconds']['mask_continuity']-sum(elapsed),
        model={k:model.get(k) for k in ['name','sha256','image_size','device','mask_cache','image_feature_cache_bytes','reused_transition_frames']},
        by_seed_kind=dict(groups),candidates=candidate_rows,attempts=attempts,
        joint_candidates=[{**{k:v for k,v in c.items() if k!='attempts'},'attempts':[compact(a) for a in c['attempts']]} for c in joint.get('candidates',[])],
        historical_name_vs_unknown_delta=sum(c['end']-c['start'] for c in cov['changes'] if c['after']==['unknown']),
        historical_delta_still_unknown=sum(r['end']-r['start'] for r in remaining),
        one_sided_overlap_with_historical_delta=sum(r['one_sided_overlap'] for r in remaining),
        historical_delta_ranges=remaining,one_sided_role_audit=roles)

(O/'sam-addendum-evidence.json').write_text(json.dumps(dict(inputs=inputs,results=results),ensure_ascii=False,indent=2))
for n,r in results.items():
    print(n, json.dumps({k:v for k,v in r.items() if k not in ('candidates','attempts','joint_candidates','historical_delta_ranges','one_sided_role_audit')},ensure_ascii=False))
    print('CRITICAL',json.dumps([c for c in r['candidates'] if any(c['start']<b and a<c['end'] for a,b in critical[n])],ensure_ascii=False))
    print('ROLE',json.dumps(r['one_sided_role_audit'],ensure_ascii=False))
