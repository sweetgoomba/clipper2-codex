import json
from pathlib import Path
r=Path(__file__).parent
manifest=json.loads((r/'run-manifest.json').read_text())
expected=json.loads((r/'expected-time-changes.json').read_text())
for c in manifest:
 p=Path(c['output_root'])/'json/dance_meta.json'
 if not p.exists():continue
 old=json.loads((r/f"baseline/{c['baseline_project_id']}/dance_meta.json").read_text());new=json.loads(p.read_text())
 changes=[]
 for kind in ('main','group'):
  a=old['lists'][kind];b=new['lists'][kind];points=sorted({x[k] for x in a+b for k in ('start','end')})
  at=lambda cs,t:sorted(x.get('person_id') or 'group' for x in cs if x['start']<=t<x['end'])
  for s,e in zip(points,points[1:]):
   before,after=at(a,(s+e)/2),at(b,(s+e)/2)
   if before!=after:changes.append(dict(kind=kind,start=s,end=e,before=before,after=after))
 outside=[d for d in changes if not any(x['start']-1e-6<=d['start'] and d['end']<=x['end']+1e-6 for x in expected[c['title']])]
 print(json.dumps(dict(title=c['title'],changes=changes,outside_expected=outside),ensure_ascii=False))
 assert not outside
