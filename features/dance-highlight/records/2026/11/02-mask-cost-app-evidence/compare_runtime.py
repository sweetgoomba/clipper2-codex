import json,sys
from pathlib import Path
root=Path(__file__).parent/sys.argv[1]
results=[]
for run in json.loads((root/'run-manifest.json').read_text()):
 new=root/'new'/str(run['project_id'])/'face_evidence.json'
 if not new.exists():continue
 before=json.loads((root/'baseline'/str(run['baseline_project_id'])/'face_evidence.json').read_text())
 after=json.loads(new.read_text())
 a,b=before['runtime'],after['runtime']
 mask=after.get('mask_continuity_refinement',{})
 joint=after.get('secondary_reference_refinement',{}).get('identity_revalidation',{})
 results.append(dict(title=run['title'],same_video_hash=a.get('video_sha256')==b.get('video_sha256'),
  same_model_hashes=a.get('models')==b.get('models'),same_config_hash=a.get('config_sha256')==b.get('config_sha256'),
  providers=b.get('recognizer_providers'),recognizer_stats=b.get('recognizer_stats'),
  mask_reason=mask.get('reason'),mask_recovered_seconds=mask.get('recovered_seconds'),
  mask_attempts=sum(len(c.get('attempts',[])) for c in mask.get('candidates',[])),
  mask_model_initialized=bool(mask.get('model')),joint_reason=joint.get('reason'),
  joint_model_initialized=bool(joint.get('model'))))
(root/'runtime-comparison.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
print(json.dumps([{k:v for k,v in r.items() if k not in ['providers','recognizer_stats']} for r in results],ensure_ascii=False))
