"""Read-only final app output audit; no model or decoder execution."""
import collections,json
from pathlib import Path
R=Path(__file__).parent
cases=json.loads((R/'run-manifest.json').read_text())
expected=json.loads((R/'expected-time-changes.json').read_text())
def read(p):return json.loads(p.read_text())
def name_at(clips,t):return sorted(c.get('person_id') or 'group' for c in clips if c['start']<=t<c['end'])
def changes(a,b):
 points=sorted({c[k] for c in a+b for k in ('start','end')});out=[]
 for s,e in zip(points,points[1:]):
  left,right=name_at(a,(s+e)/2),name_at(b,(s+e)/2)
  if left==right:continue
  if out and abs(out[-1]['end']-s)<1e-7 and out[-1]['before']==left and out[-1]['after']==right:out[-1]['end']=e
  else:out.append(dict(start=s,end=e,before=left,after=right))
 return out
def quality(m):
 out={}
 for typ,clips in [('named',[c for c in m['lists']['main'] if c['person_id']!='unknown']),('unknown',[c for c in m['lists']['main'] if c['person_id']=='unknown']),('group',m['lists']['group'])]:
  out[typ]=dict(count=len(clips),short=sum(c['end']-c['start']<1 for c in clips),seconds=sum(c['end']-c['start'] for c in clips),longest=max((c['end']-c['start'] for c in clips),default=0))
 return out
results=[]
for c in cases:
 folder=Path(c['output_root']);p=folder/'json/dance_meta.json'
 if not p.exists():continue
 before=R/'baseline'/c['baseline_project_id'];bm=read(before/'dance_meta.json');am=read(p);be=read(before/'face_evidence.json');ae=read(folder/'diagnostics/face_evidence.json')
 diff=changes(bm['lists']['main'],am['lists']['main'])
 outside=[d for d in diff if not any(d['start']>=x['start']-1e-6 and d['end']<=x['end']+1e-6 for x in expected[c['title']])]
 audit=ae['output_named_continuity'].get('performance_parts',{})
 results.append(dict(title=c['title'],main_changes=diff,main_changes_outside_expected=outside,group_changes=changes(bm['lists']['group'],am['lists']['group']),before=quality(bm),after=quality(am),original_face_segments_identical=be['segments']==ae['segments'],pose_heads_identical=be['pose_heads']==ae['pose_heads'],pose_original_measurements_identical=[{k:v for k,v in f.items() if k not in ('scene_kind','scene_reason')} for f in be['pose_heads']]==[{k:v for k,v in f.items() if k not in ('scene_kind','scene_reason')} for f in ae['pose_heads']],main_selection_refinement_identical=be['main_selection_refinement']==ae['main_selection_refinement'],main_selection_core_identical={k:v for k,v in be['main_selection_refinement'].items() if k!='preparation_context'}=={k:v for k,v in ae['main_selection_refinement'].items() if k!='preparation_context'},mask={k:v for k,v in ae['mask_continuity_refinement'].items() if k!='context_faces'},parts_version=audit.get('version'),identity_span_count=len(audit.get('identity_spans',[])),part_count=len(audit.get('parts',[])),newly_named_seconds=sum(p['newly_named_seconds'] for p in audit.get('parts',[]))))
(R/'output-audit.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(results,ensure_ascii=False,indent=2))
