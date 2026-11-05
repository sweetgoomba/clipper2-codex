"""Summarize original-time coverage of the user-reviewed intervals, read-only."""
import json,sys,collections
from pathlib import Path
root=Path(__file__).parent
cases={
 'MMN':[(1.9,2.3,'text intro; no main expected'),(2.3,4.37,'group'),(10.91,11.31,'카즈하 or group'),(34.73,35.44,'사쿠라 or group'),(37.738,39.339,'사쿠라'),(45.,48.,'사쿠라, approximate boundary'),(89.,93.,'카즈하, continuous through camera change')],
 'ANT':[(4.571,6.139,'홍은채'),(8.375,9.0,'홍은채'),(9.4,10.277,'김채원'),(32.633,33.433,'transition; either adjacent main acceptable')],
 'NEON':[(78.378,79.680,'시리'),(150.617,152.619,'group'),(183.15,184.82,'group')]
}
def coverage(meta,a,b):
 spans=[]
 for kind in ['main','group']:
  for c in meta['lists'][kind]:
   start,end=max(a,c['start']),min(b,c['end'])
   if end>start:
    spans.append(dict(start=start,end=end,kind=kind,name=c.get('person_id'),clip_start=c['start'],clip_end=c['end']))
 return sorted(spans,key=lambda r:(r['start'],r['kind']))
result=[]
for m in json.loads((root/'run-manifest.json').read_text()):
 new=Path(m['output_root'])/'json/dance_meta.json'
 if not new.exists():continue
 baseline=json.loads((root/'baseline'/str(m['baseline_project_id'])/'dance_meta.json').read_text())
 current=json.loads(new.read_text())
 for a,b,expected in cases[m['title']]:
  left,right=coverage(baseline,a,b),coverage(current,a,b)
  result.append(dict(title=m['title'],start=a,end=b,user_feedback=expected,before=left,after=right,identical=left==right))
(root/'reviewed-case-comparison.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(cases=len(result),changed=[{k:v for k,v in r.items() if k not in ('before','after')} for r in result if not r['identical']]),ensure_ascii=False))
