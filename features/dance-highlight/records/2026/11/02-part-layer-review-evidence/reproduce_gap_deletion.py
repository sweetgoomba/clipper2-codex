"""Synthetic in-memory ablation of frozen source. No model/app inference."""
from pathlib import Path
from types import SimpleNamespace
import json
import numpy as np
from dance_highlight.services.face_evidence import FaceObservation
from dance_highlight.services.reference_matcher import SegmentReferenceDecision
from dance_highlight.services.segment import Segment
from dance_highlight.services import member_timeline as mt

OUT=Path('/private/tmp/dance-part-layer-review-20261102')
class Matcher:
    def match(self,row,*args):
        name='A' if row.embedding is not None and row.embedding[0]>.9 else 'B' if row.embedding is not None and row.embedding[1]>.9 else None
        return SimpleNamespace(reference_id=name,status='matched' if name else 'unmatched',reason='synthetic',
                               candidates=[SimpleNamespace(reference_id=name,distance=.2)] if name else [])
def obs(t,name):
    return FaceObservation(round(t*30),t,7,(0.,0.,100.,100.),(0.,0.,100.,100.),
        face_bbox=(30.,10.,60.,40.),embedding=np.array([1.,0.,0.] if name=='A' else [0.,1.,0.]),detector_score=.98,association='confirmed')
def run(times,end):
    rows=[obs(t,n) for t,n in times]
    seg=Segment('main',7,0.,end,[(o.time_seconds,np.asarray(o.body_bbox),7) for o in rows])
    out=mt.refine_member_timeline([seg],[SegmentReferenceDecision(None,'unmatched','synthetic')],[None],[[]],
        [SimpleNamespace(owned_observations=rows,owned_previews={})],Matcher())
    return {'parts':[{'start':s.start,'end':s.end,'name':d.reference_id,'reason':d.reason}
                     for s,d in zip(out['segments'],out['decisions'])],
            'boundaries':[x for a in out['audit'] for x in a['boundaries']],
            'evidence_frames':[o.frame_index for rows in out['evidence'] for o,n in rows]}
cases=[('early_pair_then_unobserved',[(.1,'A'),(.3,'A')],3.),
       ('same_name_both_sides_unobserved_gap',[(.1,'A'),(.3,'A'),(2.1,'A'),(2.3,'A')],2.5),
       ('brief_middle_appearance',[(2.9,'A'),(3.1,'A')],6.),
       ('observed_short_B_between_A',[(float(t),'B' if 1.0<=t<1.3 else 'A') for t in np.arange(.1,2.,.05)],2.),
       ('observed_continuous_30_seconds',[(float(t),'A') for t in np.arange(.1,30.,.2)],30.)]
original=mt._select_boundaries
results=[]
for name,times,end in cases:
    before=run(times,end)
    mt._select_boundaries=lambda segment,candidates:original(segment,[x for x in candidates if x['reason']!='face_coverage_gap'])
    try: after=run(times,end)
    finally: mt._select_boundaries=original
    result={'case':name,'synthetic':True,'input_times':times,'end':end,'before':before,'after_gap_candidate_deletion':after,
            'raw_evidence_frames_unchanged':before['evidence_frames']==after['evidence_frames']}
    results.append(result)
    print(name,'before',before['parts'],'after',after['parts'])
assert results[0]['before']['parts'][1]['name'] is None
assert results[0]['after_gap_candidate_deletion']['parts']==[{'start':0.,'end':3.,'name':'A','reason':'member_timeline_consensus'}]
assert len(results[1]['before']['parts'])==3 and len(results[1]['after_gap_candidate_deletion']['parts'])==1
assert len(results[2]['before']['parts'])==3 and len(results[2]['after_gap_candidate_deletion']['parts'])==1
assert [x['name'] for x in results[3]['before']['parts']]==['A','B','A']
assert results[3]['before']==results[3]['after_gap_candidate_deletion']
assert results[4]['before']==results[4]['after_gap_candidate_deletion']
assert all(x['raw_evidence_frames_unchanged'] for x in results)
(OUT/'gap-deletion-counterexamples.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
print('Five synthetic cases checked; three unsupported-name expansions reproduced; original source files untouched.')
