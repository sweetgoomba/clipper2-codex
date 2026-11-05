"""Read-only acceptance audit for the completed three packaged-app runs."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parent
SOURCE = Path('/Users/jina/project/adlight/desktop/clipper_python')
read = lambda p: json.loads(p.read_text())
reports = read(ROOT/'run-comparison.json')
assert len(reports) == 3 and all(r['status'] == 'completed' for r in reports)
result = []
for r in reports:
    old = read(ROOT/'baseline'/r['baseline_project_id']/'face_evidence.json')
    new = read(ROOT/'new'/r['project_id']/'face_evidence.json')
    meta = read(ROOT/'new'/r['project_id']/'dance_meta.json')
    before = read(ROOT/'baseline'/r['baseline_project_id']/'dance_meta.json')
    stages = meta['diagnostics']['performance']['stage_seconds']
    modules = new['runtime']['modules']
    module_matches = {}
    for name in ('pipeline', 'observed_main', 'face_evidence', 'named_boundaries'):
        path = SOURCE/'plugins/dance_highlight/dance_highlight/services'/f'{name}.py'
        module_matches[name] = modules[name]['sha256'] == hashlib.sha256(path.read_bytes()).hexdigest()
    correction = new['output_named_continuity']['named_boundaries']
    coverage = lambda m: sum(c['end']-c['start'] for c in m['lists']['main'])
    check = dict(
        title=r['title'], project_id=r['project_id'],
        frozen_original_face_segments_identical=old['segments'] == new['segments'],
        pose_heads_identical=old['pose_heads'] == new['pose_heads'],
        diagnostic_frames_identical=r['identical_diagnostic_frames'],
        person_cards_identical=r['identical_person_cards'],
        all_group_rows_identical=before['lists']['group'] == meta['lists']['group'],
        main_coverage_seconds_before=coverage(before),
        main_coverage_seconds_after=coverage(meta),
        coverage_conserved=abs(coverage(before)-coverage(meta)) < 1e-9,
        quality_counts_identical=r['baseline_quality'] == r['new_quality'],
        compiled_modules_match_source=module_matches,
        shared_auraface_module_unchanged=old['runtime']['modules']['auraface']['sha256'] == modules['auraface']['sha256'],
        sam_mask_seconds=stages['mask_continuity'], sam_joint_seconds=stages['joint_identity'],
        lightweight_pose_appearance_seconds=stages['body_continuity'],
        named_boundary_seconds=stages['named_boundaries'], correction=correction,
        role_observation_count=len(new['main_selection_refinement']['role_observations']),
        frame_count=len(meta['diagnostics']['frames']),
        changed_thumbnails=r['changed_thumbnails'],
    )
    assert all(module_matches.values()), check
    assert stages['mask_continuity'] == stages['joint_identity'] == 0
    assert check['coverage_conserved'] and check['quality_counts_identical']
    assert check['frozen_original_face_segments_identical'] and check['pose_heads_identical']
    assert check['diagnostic_frames_identical'] and check['all_group_rows_identical']
    assert check['shared_auraface_module_unchanged'] and check['person_cards_identical']
    if r['title'] == 'ANTIFRAGILE':
        assert len(correction['corrections']) == 1
        assert abs(correction['corrected_seconds'] - 0.28361666666666) < 1e-9
        assert len(r['removed_or_changed_clips']) == len(r['added_or_changed_clips']) == 2
    else:
        assert not correction['corrections'] and r['identical_clips']
    result.append(check)
reviewed = read(ROOT/'reviewed-case-comparison.json')
assert len(reviewed) == 14 and all(c['identical'] for c in reviewed)
old_wall = sum(r['baseline_active_wall_seconds'] for r in reports)
new_wall = sum(r['active_wall_seconds'] for r in reports)
out = dict(checks=result, reviewed_cases=len(reviewed), reviewed_cases_unchanged=True,
           baseline_wall_seconds=old_wall, new_wall_seconds=new_wall,
           observed_wall_reduction_percent=100*(1-new_wall/old_wall),
           subsecond_clips_before=sum(r['baseline_quality']['subsecond_clips'] for r in reports),
           subsecond_clips_after=sum(r['new_quality']['subsecond_clips'] for r in reports),
           unknown_seconds_before=sum(r['baseline_quality']['unknown_seconds'] for r in reports),
           unknown_seconds_after=sum(r['new_quality']['unknown_seconds'] for r in reports))
(ROOT/'final-checks.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='checks'},ensure_ascii=False))
