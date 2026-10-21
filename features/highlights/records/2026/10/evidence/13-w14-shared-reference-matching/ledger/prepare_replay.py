from pathlib import Path
from dataclasses import asdict
import hashlib,json
import numpy as np
from clipper_face_core import EmbeddingSpace, SourceEvidence, MatchPolicy
from clipper_face_core.contracts import fingerprint
from evaluation.reference_matching.manifest import file_sha256,code_inventory

archive=Path('/Users/jina/project/adlight/.codex/features/highlights/records/2026/10/evidence/13-w14-face-matching-baseline')
root=Path('/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/reference-replay-v1')
root.mkdir(parents=True,exist_ok=False)
manifest=json.loads((archive/'archive-manifest.json').read_text())
for f in manifest['files']:
 assert file_sha256(archive/f['path'])==f['sha256']
rp=json.loads((archive/'reference-gallery/plan.json').read_text())
tp=json.loads((archive/'selected-face-trace/plan.json').read_text())
rr=json.loads((archive/'reference-gallery/reference-result.json').read_text())
tr=json.loads((archive/'selected-face-trace/trace-result.json').read_text())
for item in [tp['source'],rp['truth'],*tp['caches'].values(),*rp['references'],*rp['models']]:
 assert file_sha256(Path(item['path']))==item['sha256'],item['path']
cache=json.loads(Path(tp['caches']['saved512']['path']).read_text())
segment=next(s for s in cache['prediction']['kept_main'] if s['start_sec']==10.6106)
assert segment['track_id']==3 and segment['person_id']=='하니' and segment['track_embedding_count']==1
space=EmbeddingSpace(rp['models'][1]['sha256'],'opencv_sface_alignCrop_5pt_v1','opencv_bgr_u8_v1','float32_l2_eps1e-9_v1',128,'opencv-4.13.0')
config=fingerprint(tp['config']);detector=rp['models'][0]['sha256']
refs=[]
for r in rr['rows']:
 x,y,w,h=r['detected_faces'][r['selected_face_index']]['xywh']
 box=(max(0,x),max(0,y),min(r['width'],x+w),min(r['height'],y+h))
 source=SourceEvidence('reference-probe-20261013',r['sha256'],1,detector,fingerprint(rp['algorithm']),
       'legacy_reference_import_v1','still_image',None,None,None,None,r['width'],r['height'],0,box,None,None,None)
 refs.append(dict(id=str(r['index']),reference_id=r['label'],embedding_key=str(r['index']),source=asdict(source),space_fingerprint=space.fingerprint))
queries=[];scope_ids=[]
for r in tr['rows']:
 id=f"{r['frame_index']}_{r['condition']}"
 x,y,w,h=r['face_candidates'][r['selected_candidate']]['source_xywh']
 is_scope=r['condition']=='saved512' and r['frame_index'] in (1032,1092,1152)
 if is_scope:
  assert segment['start_sec']<=r['time_sec']<segment['end_sec']
  scope_ids.append(id)
 source=SourceEvidence('target-trace-20261013',tp['source']['sha256'],1,detector,config,
       'legacy_roi_import_v1','derived_seconds',r['time_sec'],None,None,r['frame_index'],1920,1012,0,
       (max(0,x),max(0,y),min(1920,x+w),min(1012,y+h)),
       '3' if is_scope else None,'saved512-track3' if is_scope else None,
       (segment['start_sec'],segment['end_sec']) if is_scope else None)
 queries.append(dict(id=id,embedding_key=id,source=asdict(source),space_fingerprint=space.fingerprint,
                     association='confirmed',condition=r['condition'],expected_reference=r['input_reference_label'],
                     expected_distances=r['distances'],baseline_assigned=None if r['assigned']=='unknown' else r['assigned']))
data=dict(references=refs,queries=queries,scopes=[dict(id='saved512-track3',observation_ids=scope_ids,baseline_reference_id=segment['person_id'])],
          scope_basis='stored single-track segment plus three already-reviewed diagnostic samples; not independent continuous identity GT')
(root/'dataset.json').write_text(json.dumps(data,indent=2,ensure_ascii=False))
np.savez(root/'baseline-centroids.npz',**{k:np.array(v,np.float32) for k,v in cache['face_cache']['reference_embeddings'].items()})
paths=dict(references=archive/'reference-gallery/reference-embeddings.local.npz',queries=archive/'selected-face-trace/query-embeddings.local.npz',
           dataset=root/'dataset.json',baseline_centroids=root/'baseline-centroids.npz',source=Path(tp['source']['path']),
           truth=Path(rp['truth']['path']),cache512=Path(tp['caches']['saved512']['path']),reference_plan=archive/'reference-gallery/plan.json',
           query_plan=archive/'selected-face-trace/plan.json',reference_result=archive/'reference-gallery/reference-result.json',query_result=archive/'selected-face-trace/trace-result.json',
           reference_worker=archive/'reference-gallery/reference_probe.py',query_worker=archive/'selected-face-trace/trace.py',archive_manifest=archive/'archive-manifest.json',
           preparation_script=Path(__file__).resolve())
plan=dict(schema='reference_replay_v1',space=asdict(space),policy=asdict(MatchPolicy(.6,0,1)),
          inputs={k:dict(path=str(v),sha256=file_sha256(v)) for k,v in paths.items()},code=code_inventory(),
          label_limitation='Previously viewed 18 source body labels; no independent face ownership GT or held-out accuracy.',
          association_basis='legacy_selected_candidate_assumption_not_face_ownership_gt',
          limits=dict(wall_seconds=120,rss_bytes=2147483648,output_bytes=26214400))
(root/'manifest.json').write_text(json.dumps(plan,indent=2,ensure_ascii=False))
print(json.dumps(dict(root=str(root),references=len(refs),queries=len(queries),scope_observations=scope_ids)))
