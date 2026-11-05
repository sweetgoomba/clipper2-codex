"""Compare identity-time coverage separately from changed clip boundaries."""
import json,sys,collections
from pathlib import Path
root=Path(__file__).parent/sys.argv[1]
rows=[]
for run in json.loads((root/'run-manifest.json').read_text()):
 new=Path(run['output_root'])/'json/dance_meta.json'
 if not new.exists():continue
 old=json.loads((root/'baseline'/str(run['baseline_project_id'])/'dance_meta.json').read_text())
 new=json.loads(new.read_text())
 a,b=old['lists']['main'],new['lists']['main']
 edges=sorted({float(c[k]) for c in a+b for k in ('start','end')})
 changes=[]
 for start,end in zip(edges,edges[1:]):
  t=(start+end)/2
  left=sorted({c.get('person_id') or 'none' for c in a if c['start']<=t<c['end']})
  right=sorted({c.get('person_id') or 'none' for c in b if c['start']<=t<c['end']})
  if left==right:continue
  if changes and changes[-1]['end']==start and changes[-1]['before']==left and changes[-1]['after']==right:
   changes[-1]['end']=end
  else:changes.append(dict(start=start,end=end,before=left,after=right))
 agg=collections.defaultdict(float)
 for c in changes:agg[(tuple(c['before']),tuple(c['after']))]+=c['end']-c['start']
 rows.append(dict(title=run['title'],changed_seconds=sum(c['end']-c['start'] for c in changes),changes=changes,
                  transitions=[dict(before=list(k[0]),after=list(k[1]),seconds=v) for k,v in agg.items()]))
(root/'identity-coverage-comparison.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
print(json.dumps([{k:v for k,v in row.items() if k!='changes'} for row in rows],ensure_ascii=False))
