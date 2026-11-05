"""Read-only comparison of packaged-app runs, retaining every clip difference."""
import collections
import datetime as dt
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parent
APP = Path.home() / 'Library/Application Support/Clipper Studio Dev'

def read(path):
    return json.loads(path.read_text())

def seconds(a, b):
    return (dt.datetime.fromisoformat(b.replace('Z', '+00:00')) -
            dt.datetime.fromisoformat(a.replace('Z', '+00:00'))).total_seconds()

def canonical_clips(meta):
    return [{k: row.get(k) for k in ('seg_type', 'start', 'end', 'person_id', 'person_ids')}
            for kind in ('main', 'group') for row in meta['lists'][kind]]

def quality(meta):
    clips = canonical_clips(meta)
    counts = collections.Counter((c['seg_type'], c['person_id'] or '') for c in clips)
    return dict(counts={f'{a}:{b}': n for (a, b), n in sorted(counts.items())},
                unknown_seconds=sum(c['end']-c['start'] for c in clips
                                    if c['seg_type']=='main' and c['person_id']=='unknown'),
                subsecond_clips=sum(c['end']-c['start'] < 1 for c in clips),
                clip_count=len(clips))

def reference_hashes(params):
    return [(m['memberName'], [(hashlib.sha256(Path(p).read_bytes()).hexdigest())
                             for p in m.get('validatedImagePaths', [])])
            for m in params['dance_setup']['members']]

reports=[]
projects=read(APP/'projects/projects.json')['projects']
baseline_times={r['title']:r for r in read(ROOT/'baseline-timings.json')}
for case in read(ROOT/'run-manifest.json'):
    job=read(APP/f"jobs/items/{case['job_id']}.json")['job']
    baseline=read(ROOT/f"baseline/{case['baseline_project_id']}/project.json")
    bmeta=read(ROOT/f"baseline/{case['baseline_project_id']}/dance_meta.json")
    report=dict(case, status=job['status'], progress=job.get('progress'), message=job.get('message'),
                error=job.get('error'), started=job.get('startedAt'),
                same_reference_selections=job['params']['dance_setup']==baseline['params']['dance_setup'],
                same_reference_bytes=reference_hashes(job['params'])==reference_hashes(baseline['params']),
                source=job['params']['source'])
    if job.get('startedAt'):
        report['queue_seconds']=seconds(job['createdAt'],job['startedAt'])
        project=next((p for p in projects if str(p['projectId'])==str(case['project_id'])),{})
        overlay=APP/f"projects/items/{case['project_id']}.json"
        if overlay.exists():
            project=read(overlay).get('project') or project
        finished=project.get('completedAt') or job.get('finishedAt')
        report['finished']=finished
        report['active_wall_seconds']=seconds(job['startedAt'],finished or dt.datetime.now(dt.timezone.utc).isoformat())
        if finished:
            report['baseline_active_wall_seconds']=baseline_times[case['title']]['active_wall_seconds']
            report['wall_reduction_percent']=100*(1-report['active_wall_seconds']/report['baseline_active_wall_seconds'])
            report['baseline_pipeline_seconds']=baseline_times[case['title']]['pipeline_seconds']
    path=Path(case['output_root'])/'json/dance_meta.json'
    if path.exists():
        meta=read(path)
        report['baseline_quality']=quality(bmeta)
        report['new_quality']=quality(meta)
        old=canonical_clips(bmeta);new=canonical_clips(meta)
        report['identical_clips']=old==new
        report['identical_full_clip_rows']=bmeta['lists']==meta['lists']
        report['identical_person_cards']=bmeta['persons']==meta['persons']
        report['diagnostic_frame_count']=len(meta['diagnostics']['frames'])
        report['identical_diagnostic_frames']=bmeta['diagnostics']['frames']==meta['diagnostics']['frames']
        thumbs={c['thumbnail_path'] for rows in meta['lists'].values() for c in rows if c.get('thumbnail_path')}
        changed_thumbs=[]
        for thumb in sorted(thumbs):
            left=Path(baseline['outputRoot'])/thumb;right=Path(case['output_root'])/thumb
            if not left.exists() or not right.exists() or hashlib.sha256(left.read_bytes()).digest()!=hashlib.sha256(right.read_bytes()).digest():
                changed_thumbs.append(thumb)
        report['thumbnail_count']=len(thumbs)
        report['changed_thumbnails']=changed_thumbs
        report['same_config']=bmeta['config']==meta['config']
        report['performance']=meta.get('diagnostics',{}).get('performance')
        if report['performance']:
            report['pipeline_reduction_percent']=100*(1-report['performance']['total_before_metadata_write_seconds']/baseline_times[case['title']]['pipeline_seconds'])
        oldset=collections.Counter(json.dumps(c,sort_keys=True,ensure_ascii=False) for c in old)
        newset=collections.Counter(json.dumps(c,sort_keys=True,ensure_ascii=False) for c in new)
        report['removed_or_changed_clips']=[json.loads(c) for c in (oldset-newset).elements()]
        report['added_or_changed_clips']=[json.loads(c) for c in (newset-oldset).elements()]
        target=ROOT/'new'/str(case['project_id']);target.mkdir(parents=True,exist_ok=True)
        for relative in ['json/dance_meta.json','diagnostics/face_evidence.json']:
            source=Path(case['output_root'])/relative
            name=source.name
            if source.exists() and not (target/name).exists(): (target/name).write_bytes(source.read_bytes())
        (target/'job.json').write_text(json.dumps(job,ensure_ascii=False,indent=2)+'\n')
        (target/'project.json').write_text(json.dumps(project,ensure_ascii=False,indent=2)+'\n')
    reports.append(report)
(ROOT/'run-comparison.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2)+'\n')
for report in reports:
    print(json.dumps({k:v for k,v in report.items() if k not in
        ['removed_or_changed_clips','added_or_changed_clips','output_root','source']},ensure_ascii=False))
