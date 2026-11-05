"""Read-only audit of persisted app outputs; writes only its own audit result."""
import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

OUT = Path('/private/tmp/dance-astra-review-20261102')
PARENT = Path('/private/tmp/dance-quality-paths-20261102/app')
APP = Path('/Users/jina/Library/Application Support/Clipper Studio Dev')
ROOT = APP / 'projects/files/116957ce-bd03-4d4a-a21d-984dc12487aa'
REPO = Path('/Users/jina/project/adlight/desktop/clipper_python')
IDS = {'MMN': ('1793610108675', '1793617663026'),
       'ANT': ('1793610363935', '1793617753764'),
       'NEON': ('1793610789306', '1793617837063')}

def read(p): return json.loads(p.read_text())
def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for data in iter(lambda: f.read(1024 * 1024), b''): h.update(data)
    return h.hexdigest()
def stamp(v): return datetime.fromisoformat(v.replace('Z', '+00:00'))
def seconds(start, end): return (stamp(end) - stamp(start)).total_seconds()
def short(v):
    if isinstance(v, (list, dict)): return {'type': type(v).__name__, 'length': len(v)}
    return v
def diff(a, b, path=''):
    if a == b: return []
    if isinstance(a, dict) and isinstance(b, dict):
        rows = []
        for k in sorted(set(a) | set(b)):
            p = path + '/' + str(k)
            if k not in a or k not in b:
                rows.append({'path': p, 'before': short(a.get(k)), 'after': short(b.get(k)), 'added': k not in a, 'removed': k not in b})
            else: rows += diff(a[k], b[k], p)
        return rows
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        return [row for i, (x, y) in enumerate(zip(a, b)) for row in diff(x, y, path + '/' + str(i))]
    return [{'path': path, 'before': short(a), 'after': short(b)}]
def union(rows):
    result = []
    for s, e in sorted((r['start'], r['end']) for r in rows):
        if result and s <= result[-1][1]: result[-1][1] = max(e, result[-1][1])
        else: result.append([s, e])
    return result
def metrics(m):
    main, group = m['lists']['main'], m['lists']['group']
    allrows = main + group
    u = union(main)
    return {'main': len(main), 'group': len(group), 'total': len(allrows),
            'per_name': dict(Counter(r['person_id'] for r in main)),
            'subsecond': sum(r['end'] - r['start'] < 1 for r in allrows),
            'unknown_seconds': sum(r['end'] - r['start'] for r in main if r['person_id'] == 'unknown'),
            'main_duration_sum': sum(r['end'] - r['start'] for r in main),
            'main_union_seconds': sum(e - s for s, e in u)}
def images(root):
    return {str(p.relative_to(root)): sha(p) for p in sorted(root.rglob('*'))
            if p.is_file() and p.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp')}
def intersect(m, start, end):
    return [(kind, r.get('person_id'), max(r['start'], start), min(r['end'], end), r['start'], r['end'])
            for kind, rows in m['lists'].items() for r in rows if r['start'] < end and r['end'] > start]

prior = read(OUT / 'input-hashes.json')
reviewed_hashes = read(OUT / 'boundary-final-source-hashes.json')
case_ranges = {
    'MMN': [(1.9,2.3),(2.3,4.37),(10.91,11.31),(34.73,35.44),(37.738,39.339),(45,48),(89,93)],
    'ANT': [(4.571,6.139),(8.375,9),(9.4,10.277),(32.633,33.433)],
    'NEON': [(78.378,79.68),(150.617,152.619),(183.15,184.82)]}
audit = {'generated_at': datetime.now().astimezone().isoformat(), 'method': 'direct live project and job JSON, all image bytes, baseline hashes frozen by independent review', 'videos': {}}
for label, (before_id, after_id) in IDS.items():
    live = []
    for tag, pid in [('baseline', before_id), ('new', after_id)]:
        paths = {'dance_meta.json': ROOT / pid / 'json/dance_meta.json',
                 'face_evidence.json': ROOT / pid / 'diagnostics/face_evidence.json',
                 'project.json': APP / 'projects/items' / (pid + '.json'),
                 'job.json': APP / 'jobs/items' / ('dance_' + pid + '.json')}
        values = {k: read(p) for k, p in paths.items()}
        values['job.json'] = values['job.json']['job']
        values['project.json'] = values['project.json']['project']
        values['snapshot_equal'] = {k: values[k] == read(PARENT / tag / pid / k) for k in paths}
        values['hashes'] = {k: {'path': str(p), 'sha256': sha(p)} for k, p in paths.items()}
        live.append(values)
    a, b = live
    ma, mb = a['dance_meta.json'], b['dance_meta.json']
    ea, eb = a['face_evidence.json'], b['face_evidence.json']
    ia, ib = images(ROOT / before_id), images(ROOT / after_id)
    image_changes = diff(ia, ib)
    stages_a = ma['diagnostics']['performance']['stage_seconds']
    stages_b = mb['diagnostics']['performance']['stage_seconds']
    timings = []
    for v in live:
        j, p = v['job.json'], v['project.json']
        timings.append({'job_created': j['createdAt'], 'started': j['startedAt'], 'project_completed': p['completedAt'],
                        'job_finished': j.get('finishedAt'), 'queue_seconds': seconds(j['createdAt'], j['startedAt']),
                        'active_wall_seconds': seconds(j['startedAt'], p['completedAt']),
                        'created_to_completed_seconds': seconds(j['createdAt'], p['completedAt']),
                        'pipeline_seconds': v['dance_meta.json']['diagnostics']['performance']['total_before_metadata_write_seconds'],
                        'job_status': j['status'], 'project_status': p['status'], 'error': j.get('error')})
    modules = {}
    for name in ['pipeline', 'observed_main', 'face_evidence', 'named_boundaries']:
        module = eb['runtime']['modules'][name]
        rel = 'plugins/dance_highlight/dance_highlight/services/' + name + '.py'
        modules[name] = {'recorded': module['sha256'], 'loaded_file_now': sha(Path(module['path'])),
                         'repo_now': sha(REPO / rel), 'independently_reviewed': reviewed_hashes.get(rel)}
    sam = []
    for meta, evidence in [(ma, ea), (mb, eb)]:
        stats = meta['stats']; stage = meta['diagnostics']['performance']['stage_seconds']
        mask = evidence['mask_continuity_refinement']
        sam.append({'mask_seconds': stage['mask_continuity'], 'joint_seconds': stage['joint_identity'],
                    'mask_policy': stats['mask_continuity_recovery'], 'joint_policy': stats['joint_identity_revalidation'],
                    'mask_reason': mask['reason'], 'candidate_count': len(mask['candidates']),
                    'mask_recovered_seconds': stats['mask_continuity_recovered_seconds'],
                    'joint_corrected_seconds': stats['joint_identity_corrected_seconds'],
                    'joint_recovered_seconds': stats['joint_identity_recovered_seconds'],
                    'runtime_model_keys': list(evidence['runtime']['models'])})
    source_hash = sha(Path(mb['input_video']))
    audit['videos'][label] = {
        'project_ids': [before_id, after_id], 'snapshot_equal': [v['snapshot_equal'] for v in live],
        'input_hashes': [v['hashes'] for v in live],
        'baseline_matches_independent_frozen_hashes': {
            'meta': a['hashes']['dance_meta.json']['sha256'] == prior[label]['meta']['sha256'],
            'evidence': a['hashes']['face_evidence.json']['sha256'] == prior[label]['evidence']['sha256']},
        'source_path_equal': ma['input_video'] == mb['input_video'], 'source_actual_hash': source_hash,
        'source_equal_to_both_run_hashes_and_frozen_review': source_hash == ea['runtime']['video_sha256'] == eb['runtime']['video_sha256'] == prior[label]['video_sha256_actual'],
        'same_config': ma['config'] == mb['config'], 'same_setup': ma['dance_setup'] == mb['dance_setup'],
        'same_runtime_models': ea['runtime']['models'] == eb['runtime']['models'],
        'same_references_including_embeddings': ea['references'] == eb['references'],
        'meta_diff': diff(ma, mb),
        'evidence_nonruntime_diff': diff({k:v for k,v in ea.items() if k != 'runtime'}, {k:v for k,v in eb.items() if k != 'runtime'}),
        'clip_diff': diff(ma['lists'], mb['lists']),
        'all_person_cards_equal': ma['persons'] == mb['persons'],
        'all_group_rows_equal': ma['lists']['group'] == mb['lists']['group'],
        'names_equal': [r['person_id'] for r in ma['lists']['main']] == [r['person_id'] for r in mb['lists']['main']],
        'main_union_equal': union(ma['lists']['main']) == union(mb['lists']['main']),
        'unknown_rows_equal': [r for r in ma['lists']['main'] if r['person_id']=='unknown'] == [r for r in mb['lists']['main'] if r['person_id']=='unknown'],
        'metrics': [metrics(ma), metrics(mb)], 'image_count': [len(ia),len(ib)], 'image_changes': image_changes,
        'image_hashes': [ia, ib], 'diagnostic_frame_count': len(mb['diagnostics']['frames']),
        'frames_equal': ma['diagnostics']['frames'] == mb['diagnostics']['frames'],
        'original_face_segments_equal': ea['segments'] == eb['segments'], 'pose_heads_equal': ea['pose_heads'] == eb['pose_heads'],
        'timings': timings, 'observed_wall_reduction_percent': 100*(1-timings[1]['active_wall_seconds']/timings[0]['active_wall_seconds']),
        'sam': sam, 'stages': [stages_a, stages_b], 'module_hashes': modules,
        'correction': eb['output_named_continuity']['named_boundaries'],
        'cases': [{'start':s, 'end':e, 'before':intersect(ma,s,e), 'after':intersect(mb,s,e), 'unchanged':intersect(ma,s,e)==intersect(mb,s,e)} for s,e in case_ranges[label]],
    }

dest = OUT / 'actual-app-independent-audit.json'
dest.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + '\n')
for label, v in audit['videos'].items():
    print(json.dumps({'video':label, 'snapshot_equal':v['snapshot_equal'], 'frozen_baseline':v['baseline_matches_independent_frozen_hashes'],
                      'clip_diff':v['clip_diff'], 'image_count':v['image_count'], 'image_changes':v['image_changes'],
                      'metrics':v['metrics'], 'timings':v['timings'], 'sam':v['sam'],
                      'evidence_nonruntime_diff':v['evidence_nonruntime_diff'],
                      'meta_diff_paths':[r['path'] for r in v['meta_diff']]}, ensure_ascii=False))
print('SAVED', dest)
