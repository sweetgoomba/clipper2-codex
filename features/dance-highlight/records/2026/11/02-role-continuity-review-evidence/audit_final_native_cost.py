"""Compare saved native pose requests, observations, and timing counters."""
from pathlib import Path
import json
P=Path('/private/tmp/dance-role-continuity-review-20261102')
ROOT=Path('/Users/jina/Library/Application Support/Clipper Studio Dev/projects/files/116957ce-bd03-4d4a-a21d-984dc12487aa')
result={}
for label in ['MMN','ANT','NEON']:
    v=json.loads((P/f'final-app-{label}-audit.json').read_text())['videos'][label]
    ns=[json.loads((ROOT/pid/'diagnostics/face_evidence.json').read_text())['native_scene_refinement'] for pid in v['ids']]
    result[label]={'requested_frame_counts':[len(n.get('requested_frames',[])) for n in ns],
        'observed_frame_counts':[len(n.get('observations',[])) for n in ns],
        'requested_frames_equal':ns[0]['requested_frames']==ns[1]['requested_frames'],
        'native_observations_equal':ns[0]['observations']==ns[1]['observations'],
        'native_scene_seconds':[s.get('native_scene') for s in v['performance_stages']],
        'group_context_seconds':[s.get('group_context',0) for s in v['performance_stages']],
        'changes_count':[len(n.get('changes',[])) for n in ns],
        'native_run_counts':[len(n.get('runs',[])) for n in ns],
        'reason':[n['reason'] for n in ns],
        'compact_group_context':ns[1].get('compact_group_context'),
        'same_model_settings':all(ns[0].get(k)==ns[1].get(k) for k in ['image_size','model_sha256','conf','iou','device'])}
(P/'final-app-native-cost-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:{f:v[f] for f in ['requested_frame_counts','native_scene_seconds','group_context_seconds']} for k,v in result.items()},indent=2))
