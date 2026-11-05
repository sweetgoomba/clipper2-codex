"""After all timed jobs finish, hash all images and map clips by content/time."""
from pathlib import Path
from collections import defaultdict
import hashlib,json
P=Path('/private/tmp/dance-role-continuity-review-20261102')
APP=Path('/Users/jina/Library/Application Support/Clipper Studio Dev')
ROOT=APP/'projects/files/116957ce-bd03-4d4a-a21d-984dc12487aa'
RUNS=json.loads((P/'final-app-run-manifest.json').read_text())
def read(p):return json.loads(p.read_text())
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
statuses={r['title']:read(APP/'jobs/items'/f"{r['job_id']}.json")['job']['status'] for r in RUNS}
assert all(v=='completed' for v in statuses.values()),statuses
def key(kind,r):return (kind,r['start'],r['end'],r.get('person_id'),tuple(r.get('person_ids',[])))
def same_start(kind,r):return (kind,r['start'],r.get('person_id'),tuple(r.get('person_ids',[])))
result={}
for run in RUNS:
    label=run['title'];ids=[run['baseline_project_id'],run['project_id']]
    metas=[read(ROOT/pid/'json/dance_meta.json') for pid in ids]
    imgs=[]
    for pid in ids:
        root=ROOT/pid
        imgs.append({str(f.relative_to(root)):sha(f) for f in sorted(root.rglob('*')) if f.is_file() and f.suffix.lower() in ['.jpg','.jpeg','.png','.webp']})
    listed=[{r['thumbnail_path'] for rows in m['lists'].values() for r in rows} for m in metas]
    assert all(path in imgs[i] for i,paths in enumerate(listed) for path in paths),(label,'missing listed thumbnail')
    old={key(k,r):r for k,rows in metas[0]['lists'].items() for r in rows}
    starts=defaultdict(list)
    for k,rows in metas[0]['lists'].items():
        for r in rows:starts[same_start(k,r)].append(r)
    matches=[];new_starts=[]
    for kind,rows in metas[1]['lists'].items():
        for row in rows:
            prior=old.get(key(kind,row));method='same_semantic_row'
            if prior is None:
                candidates=starts[same_start(kind,row)]
                if len(candidates)==1:prior=candidates[0];method='same_kind_person_start_changed_end'
            if prior is None:
                new_starts.append({'kind':kind,'row':row,'sha256':imgs[1][row['thumbnail_path']]});continue
            matches.append({'kind':kind,'start':row['start'],'end':row['end'],'person_id':row.get('person_id'),'before_path':prior['thumbnail_path'],'after_path':row['thumbnail_path'],'method':method,'same_bytes':imgs[0][prior['thumbnail_path']]==imgs[1][row['thumbnail_path']]})
    nonclip=[{k:v for k,v in img.items() if k not in paths} for img,paths in zip(imgs,listed)]
    nonclip_changes=[k for k in sorted(nonclip[0].keys()|nonclip[1].keys()) if nonclip[0].get(k)!=nonclip[1].get(k)]
    source=ROOT/ids[1]/'diagnostics/source.mp4'
    evidence=[read(ROOT/pid/'diagnostics/face_evidence.json') for pid in ids]
    recorded=[e['runtime']['video_sha256'] for e in evidence]
    actual=sha(source)
    result[label]={'ids':ids,'image_counts':[len(x) for x in imgs],'clip_thumbnail_counts':[len(x) for x in listed],
        'nonclip_counts':[len(x) for x in nonclip],'nonclip_changed_paths':nonclip_changes,
        'matched_surviving_clip_thumbnails':matches,'new_start_thumbnails':new_starts,
        'all_surviving_matches_same_bytes':all(x['same_bytes'] for x in matches),
        'recorded_source_hashes':recorded,'new_saved_source_sha256':actual,'source_hash_verified':recorded==[actual,actual],
        'image_hashes':imgs}
    print(label,json.dumps({k:result[label][k] for k in ['image_counts','clip_thumbnail_counts','nonclip_counts','nonclip_changed_paths','new_start_thumbnails','all_surviving_matches_same_bytes','source_hash_verified']},ensure_ascii=False),flush=True)
(P/'final-app-thumbnail-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
