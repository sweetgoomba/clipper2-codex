import datetime as dt
import json
import sys
import time
from pathlib import Path

root=Path(__file__).parent
app=Path.home()/'Library/Application Support/Clipper Studio Dev'
if len(sys.argv)>1:
    time.sleep(min(55,float(sys.argv[1])))
manifest=json.loads((root/'run-manifest.json').read_text())
rows=[]
for case in manifest:
    job=json.loads((app/f"jobs/items/{case['job_id']}.json").read_text())['job']
    started=job.get('startedAt')
    elapsed=None
    if started:
        end=dt.datetime.fromisoformat(job['finishedAt'].replace('Z','+00:00')) if job.get('finishedAt') else dt.datetime.now(dt.timezone.utc)
        elapsed=round((end-dt.datetime.fromisoformat(started.replace('Z','+00:00'))).total_seconds())
    rows.append(dict(title=case['title'],status=job['status'],progress=job.get('progress'),
                     message=job.get('message'),elapsed=elapsed,error=job.get('error')))
print(json.dumps(rows,ensure_ascii=False))
entries=[]
for line in (app/'logs/python.dance_highlight.jsonl').read_text(errors='replace').splitlines():
    try: row=json.loads(line)
    except ValueError: continue
    if row.get('ts','')>=manifest[0]['submitted']:
        entries.append(row)
with (root/'packaged-run-log.jsonl').open('w') as f:
    for row in entries:f.write(json.dumps(row,ensure_ascii=False)+'\n')
cursor=root/'watch-cursor.txt'
since=cursor.read_text() if cursor.exists() else manifest[0]['submitted']
for row in entries:
    if row['ts']>since and ('[DANCE][T]' in row.get('msg','') or row.get('level')=='error'):
        print(row['ts'],row['msg'])
if entries:cursor.write_text(entries[-1]['ts'])
