import json
from pathlib import Path

OUT = Path('/private/tmp/dance-astra-review-20261102')
APP = Path('/Users/jina/Library/Application Support/Clipper Studio Dev')
ROOT = APP / 'projects/files/116957ce-bd03-4d4a-a21d-984dc12487aa'
d = json.loads((OUT / 'actual-app-independent-audit.json').read_text())
checks = []
def check(name, ok):
    checks.append({'check': name, 'passed': bool(ok)})
    assert ok, name

for label, v in d['videos'].items():
    check(label + ': parent snapshots equal live app records', all(all(x.values()) for x in v['snapshot_equal']))
    check(label + ': baseline unchanged since independent review', all(v['baseline_matches_independent_frozen_hashes'].values()))
    booleans = {k:x for k,x in v.items() if isinstance(x,bool)}
    check(label + ': input, identity, group, union, unknown, frames and raw evidence preserved', all(booleans.values()))
    check(label + ': counts, durations and fragmentation unchanged', v['metrics'][0] == v['metrics'][1])
    check(label + ': all prior feedback ranges unchanged', all(c['unchanged'] for c in v['cases']))
    check(label + ': no image additions or removals', v['image_count'][0] == v['image_count'][1] and not any(x.get('added') or x.get('removed') for x in v['image_changes']))
    expected = ['/main/49/end', '/main/50/start'] if label == 'ANT' else []
    check(label + ': only expected clip changes', [x['path'] for x in v['clip_diff']] == expected)
    expected_image = ['/clips/dance/main/main_0050.jpg'] if label == 'ANT' else []
    check(label + ': only expected thumbnail changes', [x['path'] for x in v['image_changes']] == expected_image)
    check(label + ': only timing and additive evidence changes', {x['path'] for x in v['evidence_nonruntime_diff']} == {
        '/main_selection_refinement/preparation_context/elapsed_seconds', '/main_selection_refinement/role_observations',
        '/output_named_continuity/named_boundaries', '/scene_boundary_refinement/source_reads/decode_seconds'})
    for i, row in enumerate(v['sam']):
        check(label + ': SAM OFF ' + str(i), row['mask_seconds'] == row['joint_seconds'] == row['candidate_count'] == 0
              and row['mask_reason'] == 'disabled_runtime_cost'
              and row['mask_policy'] == row['joint_policy'] == 'disabled_runtime_cost_v1')
    before_id, after_id = v['project_ids']
    for pid in (before_id, after_id):
        e = json.loads((ROOT/pid/'diagnostics/face_evidence.json').read_text())
        j = e['secondary_reference_refinement']['identity_revalidation']
        check(label + ': joint no candidates or changes ' + pid, j['reason']=='disabled_runtime_cost' and j['candidates']==[] and all(j[k]==0 for k in ('corrected_seconds','recovered_seconds','conflict_seconds')))
    for module, h in v['module_hashes'].items():
        check(label + ': loaded source ' + module, h['recorded'] == h['loaded_file_now'] == h['repo_now'])
        if h['independently_reviewed']:
            check(label + ': reviewed source ' + module, h['recorded'] == h['independently_reviewed'])
    check(label + ': completed jobs with matching finish time', all(x['job_status']==x['project_status']=='completed' and x['error'] is None and x['job_finished']==x['project_completed'] for x in v['timings']))
    allowed_meta = ['/created_at','/project_id','/diagnostics/output_named_continuity/named_boundaries','/diagnostics/performance/']
    if label == 'ANT':
        allowed_meta += ['/lists/main/49/end','/lists/main/50/start','/diagnostics/clips/49/end','/diagnostics/clips/50/start',
                         '/diagnostics/clips/49/body_samples','/diagnostics/clips/50/body_samples','/diagnostics/clips/49/match_reason']
    check(label + ': no other metadata change', all(any(x['path'].startswith(prefix) for prefix in allowed_meta) for x in v['meta_diff']))

a = json.loads((ROOT/'1793610363935/json/dance_meta.json').read_text())
b = json.loads((ROOT/'1793617753764/json/dance_meta.json').read_text())
aa, ab = [a['diagnostics']['clips'][i]['body_samples'] for i in (49,50)]
ba, bb = [b['diagnostics']['clips'][i]['body_samples'] for i in (49,50)]
check('ANT: four existing body samples reassigned without changing evidence', ba == aa + ab[:4] and bb == ab[4:])
check('ANT: 17 source-frame boundary correction', abs((b['lists']['main'][50]['start']-a['lists']['main'][50]['start'])*b['stats']['fps']-17)<1e-8)
check('ANT: thumbnail byte-perfect reproduction at saved start', all(x['same_bytes'] for x in json.loads((OUT/'actual-app-thumbnail-reproduction.json').read_text())))
check('total: 429 clips, 1776 images, 9266 observed frames, 14 user ranges', sum(v['metrics'][1]['total'] for v in d['videos'].values())==429
      and sum(v['image_count'][1] for v in d['videos'].values())==1776
      and sum(v['diagnostic_frame_count'] for v in d['videos'].values())==9266
      and sum(len(v['cases']) for v in d['videos'].values())==14)

totals = {k: sum(v['timings'][i]['active_wall_seconds'] for v in d['videos'].values()) for i,k in enumerate(('before_wall','after_wall'))}
totals['observed_reduction_seconds'] = totals['before_wall']-totals['after_wall']
totals['observed_reduction_percent'] = 100*(1-totals['after_wall']/totals['before_wall'])
result = {'checks':checks, 'count':len(checks), 'totals':totals, 'conclusion':'Only ANT 49/50 boundary and its dependent thumbnail/body-sample assignment changed; SAM remains OFF.'}
(OUT/'actual-app-independent-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'checks_passed':len(checks),'totals':totals},ensure_ascii=False))
