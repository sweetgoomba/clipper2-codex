"""Explain diagnostic image renumbering by its owning output clip."""
from pathlib import Path
import json
P=Path('/private/tmp/dance-role-continuity-review-20261102')
ROOT=Path('/Users/jina/Library/Application Support/Clipper Studio Dev/projects/files/116957ce-bd03-4d4a-a21d-984dc12487aa')
A=json.loads((P/'final-app-thumbnail-audit.json').read_text())
for label,v in A.items():
    metas=[json.loads((ROOT/pid/'json/dance_meta.json').read_text()) for pid in v['ids']]
    clips=[{r['thumbnail_path']:r for r in m['diagnostics']['clips']} for m in metas]
    matches=[];matched_old=set();matched_new=set()
    for pair in v['matched_surviving_clip_thumbnails']:
        before=clips[0][pair['before_path']];after=clips[1][pair['after_path']]
        q0=before.get('query_images',[]);q1=after.get('query_images',[])
        matches.append({'before_clip_id':before['clip_id'],'after_clip_id':after['clip_id'],'before_paths':q0,'after_paths':q1,'same_image_sequence':[v['image_hashes'][0][x] for x in q0]==[v['image_hashes'][1][x] for x in q1]})
        matched_old.update(q0);matched_new.update(q1)
    allq=[{q for c in mapping.values() for q in c.get('query_images',[])} for mapping in clips]
    removed=allq[0]-matched_old;added=allq[1]-matched_new
    removed_owners=[{'clip_id':c['clip_id'],'start':c['start'],'end':c['end'],'person_id':c.get('person_id'),'query_images':c.get('query_images',[])} for c in clips[0].values() if any(q in removed for q in c.get('query_images',[]))]
    excluded=[allq[i]|{r['thumbnail_path'] for rows in metas[i]['lists'].values() for r in rows} for i in [0,1]]
    other=[{k:h for k,h in v['image_hashes'][i].items() if k not in excluded[i]} for i in [0,1]]
    v['semantic_query_images']={'matched_clip_sequences':matches,'all_matched_sequences_equal':all(r['same_image_sequence'] for r in matches),'query_counts':[len(x) for x in allq],'removed_paths':sorted(removed),'removed_owners':removed_owners,'unexpected_new_paths':sorted(added),'other_image_counts':[len(x) for x in other],'all_other_image_paths_and_bytes_equal':other[0]==other[1]}
    print(label,json.dumps({k:x for k,x in v['semantic_query_images'].items() if k not in ['matched_clip_sequences','removed_paths']},ensure_ascii=False))
(P/'final-app-thumbnail-audit.json').write_text(json.dumps(A,ensure_ascii=False,indent=2)+'\n')
