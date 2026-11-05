"""Replay a proposed anchoring contract on saved pose; no model or video reads."""
from pathlib import Path
import importlib.util,json,sys
import numpy as np
from dance_highlight.services import segment as old
P=Path('/private/tmp/dance-role-continuity-review-20261102')
spec=importlib.util.spec_from_file_location('dance_highlight.services.frozen_compact',P/'proposed_segment.py')
new=importlib.util.module_from_spec(spec);sys.modules[spec.name]=new;spec.loader.exec_module(new)
man=json.loads((P/'manifest.json').read_text());result={}
for label,c in man.items():
    e=json.loads(Path(c['evidence']).read_text());m=json.loads(Path(c['meta']).read_text())
    size=(m['diagnostics']['frame_width'],m['diagnostics']['frame_height'])
    rows=[old.FrameRec(p['time_seconds'],p['candidate_main_id'],None if p['candidate_main_bbox'] is None else np.asarray(p['candidate_main_bbox']),False,person_bboxes=[np.asarray(b) for b in p['body_boxes']],person_pose_keypoints=[np.asarray(k) for k in p['pose_keypoints']]) for p in e['pose_heads']]
    a=old.classify_main_scenes(rows,size);b=new.classify_main_scenes(rows,size)
    max_step=1.5*4/c['fps']
    anchored=[x.scene_kind=='group' for x in a]
    i=0
    while i<len(rows):
        if b[i].scene_kind!='group':i+=1;continue
        start=i;i+=1
        while i<len(rows) and b[i].scene_kind=='group' and rows[i].t-rows[i-1].t<=max_step+1e-8:i+=1
        if any(a[j].scene_kind=='group' for j in range(start,i)):
            anchored[start:i]=[True]*(i-start)
    spans=[]
    for i,(was,now) in enumerate(zip(a,anchored)):
        if now and was.scene_kind!='group':
            end=rows[i+1].t if i+1<len(rows) else rows[i].t
            if spans and abs(spans[-1]['end']-rows[i].t)<1e-8:spans[-1]['end']=end
            else:spans.append({'start':rows[i].t,'end':end})
    impacted=[]
    for clip in m['lists']['main']:
        parts=[(clip['start'],clip['end'])]
        for s in spans:
            next_parts=[]
            for lo,hi in parts:
                if s['end']<=lo or s['start']>=hi:next_parts.append((lo,hi));continue
                if lo<s['start']:next_parts.append((lo,s['start']))
                if s['end']<hi:next_parts.append((s['end'],hi))
            parts=next_parts
        if parts!=[(clip['start'],clip['end'])]:impacted.append({'original':{k:clip[k] for k in ['clip_id','start','end','person_id']},'remaining':[{'start':lo,'end':hi,'seconds':hi-lo} for lo,hi in parts]})
    result[label]={'added_group_spans':spans,'baseline_main_after_scope_subtraction':impacted}
    print(label,json.dumps(result[label],ensure_ascii=False))
out={'contract':'Read-only simulation: preserve completed legacy strict group; retain each temporally contiguous final compact group run only when it contains a legacy strict group observation. Regular 4-source-frame samples; 1.5-step continuity. This is a contract simulation, not an implementation or actual-app rerun.', 'videos':result}
(P/'anchored-compact-contract-review.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
