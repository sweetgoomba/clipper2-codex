import datetime as dt,json
from pathlib import Path
r=Path(__file__).parent;app=Path.home()/'Library/Application Support/Clipper Studio Dev'
for c in json.loads((r/'run-manifest.json').read_text()):
 j=json.loads((app/f"jobs/items/{c['job_id']}.json").read_text())['job'];p=Path(c['output_root'])/'json/dance_meta.json'
 if not p.exists():continue
 m=json.loads(p.read_text());clips=m['lists']['main']+m['lists']['group'];row=dict(title=c['title'],status=j['status'],clips=len(clips),short=sum(x['end']-x['start']<1 for x in clips),unknown=sum(x['end']-x['start'] for x in m['lists']['main'] if x['person_id']=='unknown'),stages=m['diagnostics']['performance']['stage_seconds'],pipeline=m['diagnostics']['performance']['total_before_metadata_write_seconds'])
 start=j.get('startedAt');end=j.get('finishedAt')
 if start and end:row['wall']=(dt.datetime.fromisoformat(end)-dt.datetime.fromisoformat(start)).total_seconds()
 print(json.dumps(row,ensure_ascii=False))
