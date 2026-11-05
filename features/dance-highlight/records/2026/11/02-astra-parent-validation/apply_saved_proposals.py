"""Experimental application to copied semantic clip rows; never writes app data."""
from pathlib import Path
from copy import deepcopy
import json
ROOT=Path('/private/tmp/dance-astra-parent-validation-20261102');REVIEW=Path('/private/tmp/dance-astra-review-20261102');M=json.loads((REVIEW/'manifest.json').read_text())

def key(c):return c['start'],c['end'],c['person_id']
def apply(rows, proposals):
    original=deepcopy(rows);out=deepcopy(rows);audit=[]
    for p in proposals:
        targets=[i for i,c in enumerate(out) if c['person_id']=='unknown' and abs(c['start']-p['start'])<1e-6 and abs(c['end']-p['end'])<1e-6]
        if len(targets)!=1:continue
        i=targets[0];side=p['proof']['side'];j=i-1 if side=='left' else i+1
        if not 0<=j<len(out) or out[j]['person_id']!=p['name']:continue
        left,right=sorted((i,j));a,b=out[left],out[right]
        if abs(a['end']-b['start'])>1e-6:continue
        named=deepcopy(out[j]);named['start']=a['start'];named['end']=b['end']
        out[left:right+1]=[named];audit.append(dict(start=p['start'],end=p['end'],name=p['name'],side=side,seed_frames=p['proof']['seeds']))
    assert rows==original
    # Existing named coverage and the total individual coverage cannot shrink.
    for c in original:
        if c['person_id']!='unknown':assert any(n['person_id']==c['person_id'] and n['start']<=c['start']+1e-6 and n['end']>=c['end']-1e-6 for n in out)
    assert abs(sum(c['end']-c['start'] for c in original)-sum(c['end']-c['start'] for c in out))<1e-6
    return out,audit

def metrics(rows):return dict(clips=len(rows),subsecond=sum(c['end']-c['start']<1 for c in rows),unknown_seconds=sum(c['end']-c['start'] for c in rows if c['person_id']=='unknown'))
reports=[]
for title,info in M.items():
    meta=json.loads(Path(info['meta']).read_text());old=[{k:c.get(k) for k in ('start','end','person_id')} for c in meta['lists']['main']]
    ps=json.loads((REVIEW/f'{title}-one-sided-summary.json').read_text())['proposals']
    # Evaluation strata derive from the independent review, not a product allowlist.
    clear=[p for p in ps if title=='ANT' and p['start']<100]
    for policy,selected in [('all_shadow_candidates',ps),('reviewed_clear_main_only',clear)]:
        out,audit=apply(old,selected)
        # A mismatched neighboring name must never be written.
        fake=[dict(p,name='__not_a_neighbor__') for p in selected]
        assert apply(old,fake)[0]==old
        # Same target cannot be used twice; only original frozen proposals are consumed.
        assert apply(old,selected+selected)[0]==out
        # Preserve every existing named change boundary, including Hong->Kim.
        for a,b in zip(old,old[1:]):
            if a['person_id'] not in ('unknown',None) and b['person_id'] not in ('unknown',None) and a['person_id']!=b['person_id'] and abs(a['end']-b['start'])<1e-6:
                assert any(abs(c['end']-a['end'])<1e-6 for c in out)
                assert any(abs(c['start']-b['start'])<1e-6 for c in out)
        reports.append(dict(video=title,policy=policy,before=metrics(old),after=metrics(out),applied=audit,known_coverage_preserved=True,total_main_duration_preserved=True))
        (ROOT/f'{title}-{policy}-main.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
(ROOT/'saved-output-application.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2));print(json.dumps(reports,ensure_ascii=False))
