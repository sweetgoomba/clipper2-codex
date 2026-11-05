import json
from pathlib import Path
r=Path(__file__).parent
frozen=json.loads((r.parent/'final-source-manifest.json').read_text());rows=[]
for c in json.loads((r/'run-manifest.json').read_text()):
 p=Path(c['output_root'])/'diagnostics/face_evidence.json'
 if not p.exists():continue
 a=json.loads(p.read_text());b=json.loads((r/f"baseline/{c['baseline_project_id']}/face_evidence.json").read_text())
 mods=a['runtime']['modules'];checks={};shared={}
 for name,mod in mods.items():
  path=mod['path'];key='plugins/dance_highlight/dance_highlight/services/'+name+'.py'
  if '/dance_highlight/services/' in path:
   checks[name]=key in frozen and mod['sha256']==frozen[key] and '/Application Support/Clipper Studio Dev/venvs/plugins/dance_highlight/' in path
  else:shared[name]=name in b['runtime']['modules'] and mod['sha256']==b['runtime']['modules'][name]['sha256']
 out=dict(title=c['title'],loaded_dance_modules=checks,shared_module_hashes_unchanged=shared,mask_reason=a['mask_continuity_refinement'].get('reason'),new_role=a['scene_context_refinement']['role_state']['version'])
 rows.append(out)
 assert all(checks.values()) and all(shared.values()),out
(r/'runtime-source-audit.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
print([{k:v for k,v in x.items() if k not in ('loaded_dance_modules','shared_module_hashes_unchanged')} for x in rows])
