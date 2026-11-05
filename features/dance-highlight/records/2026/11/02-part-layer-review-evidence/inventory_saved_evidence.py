import hashlib,json
from collections import Counter
from pathlib import Path

ROOT=Path('/Users/jina/Library/Application Support/Clipper Studio Dev/projects/files/116957ce-bd03-4d4a-a21d-984dc12487aa')
OUT=Path('/private/tmp/dance-part-layer-review-20261102')
IDS={'MMN':'1793617663026','ANT':'1793617753764','NEON':'1793617837063'}
CASES={'MMN':[(1.9,2.3),(34.73,35.44),(37.738,39.339),(45,48)],
       'ANT':[(4.571,6.139),(9.4,10.277),(48,49),(75,76),(117.25,117.72),(180,181)],
       'NEON':[(38,39),(78.378,79.68),(150.617,152.619),(183.15,184.82)]}
output={}
for name,pid in IDS.items():
    mp=ROOT/pid/'json/dance_meta.json';ep=ROOT/pid/'diagnostics/face_evidence.json'
    m=json.loads(mp.read_text());e=json.loads(ep.read_text());fps=m['stats']['fps']
    main=m['lists']['main']; groups=m['lists']['group']; role=e['main_selection_refinement']
    obs={o['frame_index']:o for s in e['segments'][:e['main_result_count']] for o in s['owned_observations']}
    joints={int(k):v for k,v in e['secondary_reference_refinement']['joint_matches'].items()}
    boundaries=[b for a in e['identity_refinement'] for b in a['boundaries']]
    reasons=Counter(x['reason'] for x in boundaries)
    def overlaps(a,b,s,t): return a<t and s<b
    def valid(o): return o['association']=='confirmed' and not o['failure'] and o['embedding'] is not None and o['detector_score']>=.8
    unknowns=[];i=0
    while i<len(main):
        if main[i]['person_id']!='unknown': i+=1;continue
        first=i
        while i+1<len(main) and main[i+1]['person_id']=='unknown' and abs(main[i]['end']-main[i+1]['start'])<1e-6:i+=1
        last=i;i+=1
        a,b=main[first]['start'],main[last]['end']
        prev=main[first-1] if first else None; nxt=main[last+1] if last+1<len(main) else None
        contrary=[]
        for f,o in obs.items():
            j=joints.get(f,{})
            if a<=o['time_seconds']<b and valid(o) and j.get('status')=='accepted' and j.get('name'):
                contrary.append({'frame':f,'time':o['time_seconds'],'name':j['name'],'detector':o['detector_score']})
        unknowns.append({'start':a,'end':b,'clip_count':last-first+1,'previous_name':prev['person_id'] if prev else None,
                         'next_name':nxt['person_id'] if nxt else None,
                         'contiguous_same_name_bracket': bool(prev and nxt and prev['person_id']==nxt['person_id'] and abs(prev['end']-a)<1e-6 and abs(b-nxt['start'])<1e-6),
                         'accepted_joint_faces':contrary,
                         'body_checks':[c for c in e['body_continuity_refinement']['candidates'] if overlaps(a,b,c['start'],c['end'])],
                         'role_reasons':dict(Counter(r['reason'] for r in role['role_observations'] if a<=r['frame']/fps<b)),
                         'cut_frames':[f for f in role['cut_frames'] if a<=f/fps<b]})
    cases=[]
    for a,b in CASES[name]:
        cases.append({'start':a,'end':b,'output':[{**c,'kind':kind} for kind,rows in [('main',main),('group',groups)] for c in rows if overlaps(a,b,c['start'],c['end'])],
                      'role_reasons':dict(Counter(r['reason'] for r in role['role_observations'] if a<=r['frame']/fps<b)),
                      'handoffs':[h for h in role['handoffs'] if overlaps(a,b,h['previous_time'],h['time'])],
                      'initial_boundary_reasons':dict(Counter(c['reason'] for c in boundaries if a<=c['time']<b)),
                      'body_checks':[c for c in e['body_continuity_refinement']['candidates'] if overlaps(a,b,c['start'],c['end'])]})
    output[name]={'project':pid,'meta_sha256':hashlib.sha256(mp.read_bytes()).hexdigest(),'evidence_sha256':hashlib.sha256(ep.read_bytes()).hexdigest(),
                  'initial_identity_scopes':len(e['identity_refinement']),'initial_boundary_reasons':dict(reasons),'initial_boundary_count':len(boundaries),
                  'role_reasons':dict(Counter(r['reason'] for r in role['role_observations'])),
                  'camera_episode_count':len(role['camera_episodes']),'handoff_count':len(role['handoffs']),
                  'body_check_reasons':dict(Counter(c['reason'] for c in e['body_continuity_refinement']['candidates'])),
                  'unknown_blocks':unknowns,'selected_cases':cases}
(OUT/'saved-evidence-inventory.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
for name,v in output.items():
    brackets=[u for u in v['unknown_blocks'] if u['contiguous_same_name_bracket']]
    print(name,'initial boundaries',v['initial_boundary_reasons'],'same-name unknown brackets',len(brackets))
    for u in brackets[:10]:
        print('bracket',u['start'],u['end'],u['previous_name'],'accepted',dict(Counter(o['name'] for o in u['accepted_joint_faces'])),
              'body',[(c['reason'],c['start'],c['end']) for c in u['body_checks']],'roles',u['role_reasons'])
    for c in v['selected_cases']:
        print('case',c['start'],c['end'],'roles',c['role_reasons'],'initial',c['initial_boundary_reasons'],
              'body',[(x['reason'],x['start'],x['end']) for x in c['body_checks']])
