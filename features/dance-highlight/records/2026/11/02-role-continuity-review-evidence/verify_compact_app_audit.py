"""Validate the saved JSON audit, not product code or model behavior."""
from pathlib import Path
import json

P=Path('/private/tmp/dance-role-continuity-review-20261102')
A=json.loads((P/'actual-app-compact-independent-audit.json').read_text())
M=json.loads((P/'manifest.json').read_text())
E=json.loads((P/'compact-scene-independent-review.json').read_text())
APP=Path('/Users/jina/Library/Application Support/Clipper Studio Dev/projects/files/116957ce-bd03-4d4a-a21d-984dc12487aa')
checks=[]
def check(name,value):
    checks.append({'check':name,'passed':bool(value)})
removed={'named':0.,'unknown':0.}
for label,v in A['videos'].items():
    check(label+': baseline JSON hashes match frozen independent review',v['metadata_hashes'][0]['meta']==M[label]['meta_sha256'] and v['metadata_hashes'][0]['evidence']==M[label]['evidence_sha256'])
    check(label+': both jobs/projects completed without error',all(t['job_status']==t['project_status']=='completed' and t['error'] is None and t['job_finished_matches_project'] for t in v['timings']))
    check(label+': source hash and input settings preserved',len(set(v['recorded_source_hashes']))==1 and v['same_config'] and v['same_dance_setup'])
    check(label+': exact reviewed segment loaded',v['recorded_modules']['segment']['sha256']==E['proposed_segment_sha256'])
    check(label+': no unexpected output coverage change',not any(v['outside_expected_coverage_changes'].values()))
    check(label+': no new or renamed main coverage',all(not r['after'] and len(r['before'])==1 for r in v['coverage_changes']['main']))
    check(label+': existing group coverage preserved',all(not r['before'] and r['after']==['None'] for r in v['coverage_changes']['group']))
    check(label+': expected scopes contain no final main',all(not x['after']['main'] for x in v['expected_scope_intersections']))
    check(label+': raw identity and reference evidence preserved',v['raw_segments_equal'] and all(v['top_evidence_equality'][k] for k in ['identity_refinement','references','secondary_reference_refinement','body_continuity_refinement','mask_continuity_refinement','visible_member_refinement']))
    check(label+': pose measurement differences limited to scene labels',all(r['path'].split('/')[-1] in ['scene_kind','scene_reason'] for r in v['pose_diffs']))
    check(label+': person descriptors preserved',all(r['path'].split('/')[2] in ['clip_ids','num_clips'] for r in v['person_diffs']))
    check(label+': SAM disabled in both runs',all(s['mask_policy']==s['joint_policy']=='disabled_runtime_cost_v1' and s['mask_reason']=='disabled_runtime_cost' and all(s[k]==0 for k in ['mask_seconds','joint_seconds','mask_candidates','mask_recovered_seconds','joint_corrected_seconds','joint_recovered_seconds']) and not any('sam' in x.lower() for x in s['models']) for s in v['sam']))
    metas=[json.loads((APP/pid/'json/dance_meta.json').read_text()) for pid in v['ids']]
    person_consistency=[]
    for m in metas:
        rows=m['lists']['main'];by_id={r['clip_id']:r for r in rows}
        for person in m['persons']:
            listed=person['clip_ids']
            person_consistency.append(person['num_clips']==len(listed) and all(cid in by_id and by_id[cid]['person_id']==person['person_id'] for cid in listed))
    check(label+': person clip references and counts valid',all(person_consistency))
    for r in v['coverage_changes']['main']:
        removed['unknown' if r['before']==['unknown'] else 'named']+=r['end']-r['start']
check('total main removed is exactly expected 2.002 seconds',abs(sum(removed.values())-2.002)<1e-8)
check('named/unknown removal split matches frozen expectation',abs(removed['named']-.5338666666666667)<1e-8 and abs(removed['unknown']-1.4681333333333333)<1e-8)
tiny=[{'video':label,**r,'duration':r['end']-r['start']} for label,v in A['videos'].items() for kind,rows in v['tiny_new_or_changed_clips'].items() for r in rows]
check('three newly tiny residuals reproduced',len(tiny)==3 and sorted(round(r['duration'],6) for r in tiny)==[.05005,.066733,.066733])
totals={key:[sum(v['metrics'][i][key] for v in A['videos'].values()) for i in [0,1]] for key in ['main','group','total','subsecond','under_0_1s','unknown_seconds']}
wall=[sum(v['timings'][i]['active_wall_seconds'] for v in A['videos'].values()) for i in [0,1]]
result={'checks':checks,'count':len(checks),'all_checks_passed':all(x['passed'] for x in checks),'quality_pass':False,'quality_finding':'P2: Three newly tiny unknown residuals of 3/4/4 source frames; do not equate expected coverage change with no quality regression.', 'main_removed_seconds':removed,'totals':totals,'tiny_residuals':tiny,'active_wall_seconds':wall,'wall_change_percent':(wall[1]/wall[0]-1)*100}
(P/'actual-app-compact-independent-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='checks'},ensure_ascii=False,indent=2))
assert result['all_checks_passed'],[x for x in checks if not x['passed']]
