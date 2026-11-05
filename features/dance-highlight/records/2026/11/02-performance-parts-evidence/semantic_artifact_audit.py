"""Match artifacts by source interval/category, not renumbered clip filenames."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parent


def read(path):
    return json.loads(path.read_text())


def key(clip):
    return (clip['seg_type'], clip['start'], clip['end'], clip.get('person_id'),
            tuple(clip.get('person_ids') or []))


reports = []
for case in read(ROOT / 'run-manifest.json'):
    before = ROOT / 'baseline' / case['baseline_project_id']
    new_root = Path(case['output_root'])
    path = new_root / 'json/dance_meta.json'
    if not path.exists():
        continue
    old_meta, new_meta = read(before / 'dance_meta.json'), read(path)
    old_root = Path(read(before / 'project.json')['outputRoot'])
    old_clips = {key(c): c for kind in ('main', 'group') for c in old_meta['lists'][kind]}
    compared, mismatches, changed = 0, [], []
    for kind in ('main', 'group'):
        for clip in new_meta['lists'][kind]:
            previous = old_clips.get(key(clip))
            if previous is None:
                changed.append(clip)
                continue
            left = old_root / previous['thumbnail_path']
            right = new_root / clip['thumbnail_path']
            compared += 1
            if not left.exists() or not right.exists() or hashlib.sha256(left.read_bytes()).digest() != hashlib.sha256(right.read_bytes()).digest():
                mismatches.append(dict(interval=key(clip), before=str(left), after=str(right)))
    reports.append(dict(title=case['title'], unchanged_clip_thumbnails_compared=compared,
                        unchanged_clip_thumbnail_mismatches=mismatches, changed_clips=changed))
(ROOT / 'semantic-artifact-audit.json').write_text(json.dumps(reports, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(reports, ensure_ascii=False, indent=2))
