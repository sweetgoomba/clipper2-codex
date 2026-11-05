"""Read-only audit of final diagnostic viewer changes, separate from output clips."""
from pathlib import Path
import json

P = Path('/private/tmp/dance-role-continuity-review-20261102')
R = Path('/Users/jina/Library/Application Support/Clipper Studio Dev/projects/files/116957ce-bd03-4d4a-a21d-984dc12487aa')
manifest = json.loads((P / 'final-app-run-manifest.json').read_text())
scopes = {'MMN': [], 'ANT': [(146.613, 146.814)], 'NEON': [(143.676, 144.012)]}
results = {}
for item in manifest:
    name = item['title']
    ids = [item['baseline_project_id'], item['project_id']]
    metas = [json.loads((R / pid / 'json/dance_meta.json').read_text()) for pid in ids]
    evidence = [json.loads((R / pid / 'diagnostics/face_evidence.json').read_text()) for pid in ids]
    frames = [m['diagnostics']['frames'] for m in metas]
    assert len(frames[0]) == len(frames[1])
    changes = []
    for index, (old, new) in enumerate(zip(*frames)):
        fields = sorted(k for k in old.keys() | new.keys() if old.get(k) != new.get(k))
        if not fields:
            continue
        assert old['t'] == new['t']
        inside = any(start <= old['t'] < end for start, end in scopes[name])
        existing_group = name == 'NEON' and 229.229 <= old['t'] <= 229.697
        assert inside or existing_group, (name, index, fields)
        if inside:
            assert set(fields) <= {'main_track_id', 'main_body', 'group', 'group_bodies', 'group_faces'}
            assert old['group'] is False and new['group'] is True
        else:
            assert fields == ['group_bodies']
            assert old['group'] is True and new['group'] is True
            assert evidence[0]['pose_heads'][index]['scene_reason'] == 'native_distant_ensemble'
            assert evidence[1]['pose_heads'][index]['scene_reason'] == 'compact_distant_ensemble'
        changes.append({
            'index': index, 'time': old['t'], 'fields': fields,
            'in_expected_output_scope': inside,
            'group_before_after': [old['group'], new['group']],
            'group_body_count_before_after': [len(old['group_bodies']), len(new['group_bodies'])],
            'group_face_count_before_after': [len(old['group_faces']), len(new['group_faces'])],
            'scene_reason_before_after': [e['pose_heads'][index]['scene_reason'] for e in evidence],
        })
    checks = {
        'same_raw_viewer_bodies_and_faces': all(a['bodies'] == b['bodies'] and a['faces'] == b['faces'] for a, b in zip(*frames)),
        'no_unexplained_viewer_fields_or_scopes': True,
        'changed_frame_count_expected': len(changes) == {'MMN': 0, 'ANT': 4, 'NEON': 14}[name],
    }
    assert all(checks.values())
    results[name] = {'checks': checks, 'changes': changes}
result = {
    'scope': 'Diagnostic viewer routing, not a claim that all displayed group boxes are unchanged.',
    'all_checks_passed': True, 'videos': results,
}
(P / 'final-app-viewer-routing-audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({name: {'changed_frames': len(v['changes']), 'checks': v['checks']} for name, v in results.items()}, ensure_ascii=False, indent=2))
