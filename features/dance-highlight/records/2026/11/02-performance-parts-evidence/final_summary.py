import copy
import json
from pathlib import Path

ROOT = Path(__file__).parent


def read(path):
    return json.loads(path.read_text())


def role_content(evidence):
    role = copy.deepcopy(evidence['main_selection_refinement'])
    preparation = role.get('preparation_context', {})
    preparation.pop('elapsed_seconds', None)
    for decision in preparation.get('rejected', []):
        decision.pop('source_index', None)
    return role


results = []
for case in read(ROOT / 'run-comparison.json'):
    baseline = ROOT / 'baseline' / case['baseline_project_id']
    before = read(baseline / 'face_evidence.json')
    after = read(Path(case['output_root']) / 'diagnostics/face_evidence.json')
    old_stages = read(baseline / 'dance_meta.json')['diagnostics']['performance']['stage_seconds']
    new_stages = case['performance']['stage_seconds']
    native_before, native_after = before['native_scene_refinement'], after['native_scene_refinement']
    results.append(dict(title=case['title'],
                        old_wall_seconds=case['baseline_active_wall_seconds'],
                        new_wall_seconds=case['active_wall_seconds'],
                        role_content_same_except_timing_and_output_index=role_content(before) == role_content(after),
                        native_requested_frames_same=native_before['requested_frames'] == native_after['requested_frames'],
                        native_observations_same=native_before['observations'] == native_after['observations'],
                        native_observation_count=len(native_after['observations']),
                        new_group_context=native_after['compact_group_context'],
                        stages={k:dict(before=old_stages.get(k), after=v, delta=v-old_stages.get(k, 0))
                                for k, v in new_stages.items()}))
total_before = sum(r['old_wall_seconds'] for r in results)
total_after = sum(r['new_wall_seconds'] for r in results)
report = dict(results=results, total_before_seconds=total_before, total_after_seconds=total_after,
              total_increase_percent=100*(total_after/total_before-1),
              caveat='One actual app execution per video per version; stage timings do not establish causality.')
(ROOT / 'final-summary.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(report, ensure_ascii=False, indent=2))
