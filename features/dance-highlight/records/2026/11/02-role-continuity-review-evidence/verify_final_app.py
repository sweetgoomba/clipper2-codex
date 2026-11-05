"""Verify completed final-app JSON/image audit against frozen baseline evidence."""
from pathlib import Path
import hashlib,json
P=Path('/private/tmp/dance-role-continuity-review-20261102')
ROOT=Path('/Users/jina/Library/Application Support/Clipper Studio Dev/projects/files/116957ce-bd03-4d4a-a21d-984dc12487aa')
frozen=json.loads((P/'manifest.json').read_text())
source=json.loads((P/'bridge-full-anchor-independent-verification.json').read_text())
images=json.loads((P/'final-app-thumbnail-audit.json').read_text())
reproductions=json.loads((P/'final-app-thumbnail-reproduction.json').read_text())
native=json.loads((P/'final-app-native-cost-audit.json').read_text())
videos={k:json.loads((P/f'final-app-{k}-audit.json').read_text())['videos'][k] for k in ['MMN','ANT','NEON']}
checks=[]
def check(name,value):checks.append({'check':name,'passed':bool(value)})
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
removed={'named':0.,'unknown':0.}
named_short_totals=[0,0]
for label,v in videos.items():
    check(label+': original baseline audit hashes preserved',v['metadata_hashes'][0]['meta']==frozen[label]['meta_sha256'] and v['metadata_hashes'][0]['evidence']==frozen[label]['evidence_sha256'])
    check(label+': final metadata still matches completed audit',all(sha(ROOT/pid/rel)==v['metadata_hashes'][i][name] for i,pid in enumerate(v['ids']) for name,rel in [('meta','json/dance_meta.json'),('evidence','diagnostics/face_evidence.json')]))
    check(label+': completed jobs without errors',all(t['job_status']==t['project_status']=='completed' and t['error'] is None and t['job_finished_matches_project'] for t in v['timings']))
    check(label+': expected reviewed segment loaded',v['recorded_modules']['segment']['sha256']==source['segment_sha256'])
    check(label+': recorded loaded segment and pipeline files match',all(sha(Path(v['recorded_modules'][k]['path']))==v['recorded_modules'][k]['sha256'] for k in ['segment','pipeline']))
    check(label+': input source bytes and settings preserved',images[label]['source_hash_verified'] and v['same_config'] and v['same_dance_setup'] and all(v['input_metadata_equal'].values()))
    check(label+': output changes confined to two expected scopes',not any(v['outside_expected_coverage_changes'].values()))
    check(label+': no new named main or identity substitution',all(not r['after'] and len(r['before'])==1 for r in v['coverage_changes']['main']))
    check(label+': no existing group coverage removed',all(not r['before'] and r['after']==['None'] for r in v['coverage_changes']['group']))
    check(label+': expected group scopes contain no final main',all(not s['after']['main'] for s in v['expected_scope_intersections']))
    check(label+': user-reviewed ranges preserved',all(s['equal'] for s in v['reviewed_cases']))
    check(label+': no new sub-0.1-second changed clip',not any(v['tiny_new_or_changed_clips'].values()))
    check(label+': subsecond count did not increase',v['metrics'][1]['subsecond']<=v['metrics'][0]['subsecond'])
    check(label+': raw identity/reference observations preserved',v['raw_segments_equal'] and all(v['top_evidence_equality'][k] for k in ['identity_refinement','references','secondary_reference_refinement','body_continuity_refinement','mask_continuity_refinement','visible_member_refinement']))
    check(label+': raw pose measurements preserved',all(d['path'].split('/')[-1] in ['scene_kind','scene_reason'] for d in v['pose_diffs']))
    check(label+': person descriptors preserved',all(d['path'].split('/')[2] in ['clip_ids','num_clips'] for d in v['person_diffs']))
    metas=[json.loads((ROOT/pid/'json/dance_meta.json').read_text()) for pid in v['ids']]
    for i,m in enumerate(metas):
        named_short_totals[i]+=sum(r['person_id']!='unknown' and r['end']-r['start']<1-1e-8 for r in m['lists']['main'])
    good=True
    for m in metas:
        byid={r['clip_id']:r for r in m['lists']['main']}
        for person in m['persons']:
            good &= person['num_clips']==len(person['clip_ids']) and all(cid in byid and byid[cid]['person_id']==person['person_id'] for cid in person['clip_ids'])
    check(label+': person card references valid',good)
    check(label+': SAM OFF in both runs',all(s['mask_policy']==s['joint_policy']=='disabled_runtime_cost_v1' and s['mask_reason']=='disabled_runtime_cost' and all(s[k]==0 for k in ['mask_seconds','joint_seconds','mask_candidates','mask_recovered_seconds','joint_corrected_seconds','joint_recovered_seconds']) and not any('sam' in x.lower() for x in s['models']) for s in v['sam']))
    query=images[label]['semantic_query_images']
    check(label+': surviving diagnostic/reference images preserved',query['all_matched_sequences_equal'] and query['all_other_image_paths_and_bytes_equal'] and not query['unexpected_new_paths'])
    check(label+': removed query images belong only to excluded unknown clips',all(r['person_id']=='unknown' and any(s['start']-1e-8<=r['start'] and r['end']<=s['end']+1e-8 for s in v['expected_scope_intersections']) for r in query['removed_owners']))
    check(label+': surviving same-start thumbnails unchanged',images[label]['all_surviving_matches_same_bytes'])
    n=native[label]
    check(label+': native pose requests and observations unchanged',n['requested_frames_equal'] and n['native_observations_equal'] and n['same_model_settings'] and n['requested_frame_counts']==n['observed_frame_counts'] and n['reason']==['complete','complete'])
    for r in v['coverage_changes']['main']:removed['unknown' if r['before']==['unknown'] else 'named']+=r['end']-r['start']
check('all fourteen user cases compared',sum(len(v['reviewed_cases']) for v in videos.values())==14)
check('exactly final expected main exclusion',abs(sum(removed.values())-.6673333333333333)<1e-8 and abs(removed['named']-.06673333333333333)<1e-8 and abs(removed['unknown']-.6006)<1e-8)
check('MMN output rows unchanged',all(not r['added_or_changed'] and not r['removed_or_changed'] for r in videos['MMN']['clip_changes'].values()))
newstart=[dict(video=k,**r) for k,v in images.items() for r in v['new_start_thumbnails']]
check('only expected ANT group thumbnail has a new start',len(newstart)==1 and newstart[0]['video']=='ANT' and newstart[0]['kind']=='group' and abs(newstart[0]['row']['start']-146.61313333333334)<1e-8)
check('changed thumbnail reproduced from source',len(reproductions)>=1 and all(x['same_bytes'] for x in reproductions))
totals={key:[sum(v['metrics'][i][key] for v in videos.values()) for i in [0,1]] for key in ['main','group','total','subsecond','under_0_1s','unknown_seconds']}
wall=[sum(v['timings'][i]['active_wall_seconds'] for v in videos.values()) for i in [0,1]]
result={'checks':checks,'count':len(checks),'all_checks_passed':all(x['passed'] for x in checks), 'review_scope':'All final output intervals/names, 14 prior user ranges, saved identity/pose evidence, all image hashes and changed-thumbnail source reproduction; not a new ground-truth review of every scene.', 'main_removed_seconds':removed,'totals':totals,'active_wall_seconds':wall,'wall_change_percent':(wall[1]/wall[0]-1)*100,'image_counts':[sum(v['image_counts'][i] for v in images.values()) for i in [0,1]],'unchanged_surviving_thumbnail_count':sum(len(v['matched_surviving_clip_thumbnails']) for v in images.values()),'new_start_thumbnail_count':len(newstart)}
result['named_subsecond_clips']=named_short_totals
(P/'final-app-independent-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='checks'},ensure_ascii=False,indent=2))
assert result['all_checks_passed'],[x for x in checks if not x['passed']]
