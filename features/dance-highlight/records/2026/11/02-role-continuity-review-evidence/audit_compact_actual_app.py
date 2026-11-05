"""Independent read-only audit of completed app JSON. No models/video/image I/O."""
from pathlib import Path
from collections import Counter
from datetime import datetime
import hashlib
import json

OUT = Path('/private/tmp/dance-role-continuity-review-20261102')
APP = Path('/Users/jina/Library/Application Support/Clipper Studio Dev')
ROOT = APP / 'projects/files/116957ce-bd03-4d4a-a21d-984dc12487aa'
RUNS = json.loads((OUT / 'actual-app-run-manifest.json').read_text())
EXPECTED = json.loads((OUT / 'compact-scene-independent-review.json').read_text())['actual']
EPS = 1e-8

def read(p):
    return json.loads(p.read_text())

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def seconds(a, b):
    return (datetime.fromisoformat(b.replace('Z', '+00:00')) - datetime.fromisoformat(a.replace('Z', '+00:00'))).total_seconds()

def semantic(row):
    return tuple((k, json.dumps(v, sort_keys=True, ensure_ascii=False)) for k, v in sorted(row.items()) if k not in {'seg_id', 'clip_id', 'thumbnail_path'})

def brief(row):
    return {k: row.get(k) for k in ('clip_id', 'start', 'end', 'person_id', 'thumbnail_path')}

def covers(rows, t):
    return sorted(str(r.get('person_id')) for r in rows if r['start'] <= t < r['end'])

def delta(a, b, scopes):
    knots = sorted({v for r in a+b+scopes for v in (r['start'], r['end'])})
    changes = []
    for start, end in zip(knots, knots[1:]):
        if end-start < EPS:
            continue
        mid = (start+end)/2
        before, after = covers(a, mid), covers(b, mid)
        if before == after:
            continue
        expected = any(r['start']-EPS <= mid < r['end']+EPS for r in scopes)
        if changes and abs(changes[-1]['end']-start)<EPS and (changes[-1]['before'], changes[-1]['after'], changes[-1]['expected_scope']) == (before, after, expected):
            changes[-1]['end'] = end
        else:
            changes.append({'start':start, 'end':end, 'before':before, 'after':after, 'expected_scope':expected})
    return changes

def intersection(rows, start, end):
    return [dict(brief(r), overlap_start=max(start,r['start']), overlap_end=min(end,r['end'])) for r in rows if r['start']<end-EPS and r['end']>start+EPS]

def metrics(meta):
    main, group = meta['lists']['main'], meta['lists']['group']
    rows = main+group
    return {'main':len(main), 'group':len(group), 'total':len(rows),
            'subsecond':sum(r['end']-r['start']<1-EPS for r in rows),
            'under_0_1s':sum(r['end']-r['start']<.1-EPS for r in rows),
            'unknown_seconds':sum(r['end']-r['start'] for r in main if r['person_id']=='unknown'),
            'main_seconds':sum(r['end']-r['start'] for r in main),
            'names':dict(Counter(r['person_id'] for r in main))}

def recursive_diff(a, b, path=''):
    if a == b:
        return []
    if isinstance(a, dict) and isinstance(b, dict):
        out=[]
        for key in sorted(a.keys() | b.keys()):
            p=path+'/'+str(key)
            if key not in a or key not in b:
                out.append({'path':p,'change':'added' if key not in a else 'removed'})
            else:
                out.extend(recursive_diff(a[key],b[key],p))
        return out
    if isinstance(a,list) and isinstance(b,list) and len(a)==len(b):
        return [x for i,(v,w) in enumerate(zip(a,b)) for x in recursive_diff(v,w,path+'/'+str(i))]
    def summary(v):
        return {'type':type(v).__name__,'length':len(v)} if isinstance(v,(list,dict)) else v
    return [{'path':path,'before':summary(a),'after':summary(b)}]

def sam(meta,evidence):
    stat=meta['stats']; stage=meta['diagnostics']['performance']['stage_seconds']
    mask=evidence['mask_continuity_refinement']
    return {'mask_policy':stat['mask_continuity_recovery'], 'joint_policy':stat['joint_identity_revalidation'],
            'mask_seconds':stage['mask_continuity'], 'joint_seconds':stage['joint_identity'],
            'mask_reason':mask['reason'],'mask_candidates':len(mask['candidates']),
            'mask_recovered_seconds':stat['mask_continuity_recovered_seconds'],
            'joint_corrected_seconds':stat['joint_identity_corrected_seconds'],
            'joint_recovered_seconds':stat['joint_identity_recovered_seconds'],
            'models':list(evidence['runtime']['models'])}

statuses={r['title']:read(APP/'jobs/items'/f"{r['job_id']}.json")['job']['status'] for r in RUNS}
if any(v!='completed' for v in statuses.values()):
    print(json.dumps({'audit_not_started':statuses}));raise SystemExit(2)

audit={'method':'Direct comparison of completed app metadata and saved diagnostics JSON only; no new model, decode, image extraction, or product tests.', 'videos':{}}
for run in RUNS:
    label=run['title']; ids=[run['baseline_project_id'],run['project_id']]
    metas=[read(ROOT/pid/'json/dance_meta.json') for pid in ids]
    evidence=[read(ROOT/pid/'diagnostics/face_evidence.json') for pid in ids]
    jobs=[read(APP/'jobs/items'/f'dance_{pid}.json')['job'] for pid in ids]
    projects=[read(APP/'projects/items'/f'{pid}.json')['project'] for pid in ids]
    scopes=EXPECTED[label]['changes'];a,b=metas;ea,eb=evidence
    differences={kind:delta(a['lists'][kind],b['lists'][kind],scopes) for kind in ['main','group']}
    clip_changes={}
    for kind in ['main','group']:
        old,new=a['lists'][kind],b['lists'][kind]
        ca,cb=Counter(map(semantic,old)),Counter(map(semantic,new))
        removed=[brief(r) for r in old if semantic(r) not in cb]
        added=[brief(r) for r in new if semantic(r) not in ca]
        oldmap={semantic(r):r for r in old}
        clip_changes[kind]={'removed_or_changed':removed,'added_or_changed':added,
                            'unchanged_semantic_rows':sum((ca&cb).values()),
                            'unchanged_rows_with_reindexed_ids':sum(r['clip_id']!=oldmap[semantic(r)]['clip_id'] for r in new if semantic(r) in oldmap)}
    pose_diffs=recursive_diff(ea.get('pose_heads'),eb.get('pose_heads'))
    scopes_audit=[{'start':s['start'],'end':s['end'],
        'before':{k:intersection(a['lists'][k],s['start'],s['end']) for k in ['main','group']},
        'after':{k:intersection(b['lists'][k],s['start'],s['end']) for k in ['main','group']}}
        for s in scopes]
    timings=[]
    for m,j,p in zip(metas,jobs,projects):
        timings.append({'active_wall_seconds':seconds(j['startedAt'],p['completedAt']),
                        'queue_seconds':seconds(j['createdAt'],j['startedAt']),
                        'pipeline_seconds':m['diagnostics']['performance']['total_before_metadata_write_seconds'],
                        'job_status':j['status'],'project_status':p['status'],'error':j.get('error'),
                        'job_finished_matches_project':j.get('finishedAt')==p['completedAt']})
    report={'ids':ids,'metrics':[metrics(m) for m in metas],'coverage_changes':differences,
        'outside_expected_coverage_changes':{k:[r for r in rows if not r['expected_scope']] for k,rows in differences.items()},
        'clip_changes':clip_changes,'expected_scope_intersections':scopes_audit,
        'tiny_new_or_changed_clips':{k:[r for r in v['added_or_changed'] if r['end']-r['start']<.1-EPS] for k,v in clip_changes.items()},
        'sam':[sam(m,e) for m,e in zip(metas,evidence)],'timings':timings,
        'same_config':a['config']==b['config'],'same_dance_setup':a['dance_setup']==b['dance_setup'],
        'person_diffs':recursive_diff(a['persons'],b['persons']),
        'recorded_source_hashes':[e['runtime']['video_sha256'] for e in evidence],
        'recorded_modules':eb['runtime']['modules'],
        'evidence_keys':list(eb),'raw_segments_equal':ea['segments']==eb['segments'],
        'pose_diffs':pose_diffs,'top_evidence_equality':{k:ea[k]==eb.get(k) for k in ea},
        'metadata_hashes':[{name:digest(ROOT/pid/rel) for name,rel in [('meta','json/dance_meta.json'),('evidence','diagnostics/face_evidence.json')]} for pid in ids]}
    audit['videos'][label]=report
    print(label,json.dumps({k:report[k] for k in ['metrics','coverage_changes','tiny_new_or_changed_clips','sam','timings','same_config','same_dance_setup','raw_segments_equal']},ensure_ascii=False))
(OUT/'actual-app-compact-independent-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
