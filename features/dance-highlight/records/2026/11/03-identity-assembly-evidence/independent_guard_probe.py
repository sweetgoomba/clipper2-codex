"""Bounded synthetic function probes; no model, video, or filesystem writes in product."""
import json, hashlib, importlib.util
from pathlib import Path
from dataclasses import replace
from types import SimpleNamespace
import numpy as np

ROOT=Path('/Users/jina/project/adlight/desktop/clipper_python/plugins/dance_highlight/dance_highlight/services')
OUT=Path('/private/tmp/dance-identity-assembly-20261103/independent-source-review')
OUT.mkdir(exist_ok=True)
manifest={}
for name in ('identity_projection','part_boundary_events','member_timeline','output_continuity'):
    data=(ROOT/(name+'.py')).read_bytes();dst=OUT/(name+'.py');dst.write_bytes(data)
    manifest[name]=hashlib.sha256(data).hexdigest()
    import sys
    spec=importlib.util.spec_from_file_location('dance_highlight.services.'+name,dst)
    mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)

from dance_highlight.services.face_evidence import FaceObservation
from dance_highlight.services.segment import FrameRec,Segment
from dance_highlight.services.reference_matcher import SegmentReferenceDecision
from dance_highlight.services.identity_projection import validate_identity_padding
from dance_highlight.services.member_timeline import recover_final_face_edges

box=np.array([10.,0.,90.,210.])
frames=[0,4,8,12,16,20,24]
rows=[FaceObservation(f,f/60,0,tuple(box),tuple(box),face_bbox=(35,10,65,30),
    embedding=np.array([1.,0.]),detector_score=.99,association='confirmed') for f in frames]
records=[FrameRec(r.time_seconds,0,box.copy(),False,person_bboxes=[box.copy()],scene_kind='main') for r in rows]
def output(spans):
    return dict(segments=spans,decisions=[SegmentReferenceDecision('A','matched','member_timeline_consensus') for _ in spans],
        labels=list(range(1,len(spans)+1)),accurate_indices=list(range(len(spans))),anchors=[],
        evidence=[[(r,'A') for r in rows if s.start<=r.time_seconds<s.end] for s in spans],
        previews=[[] for _ in spans],preview_sources=[({}, {}) for _ in spans])
class Matcher:
    def match(self,row,*_):
        return SimpleNamespace(reference_id='A',candidates=[SimpleNamespace(reference_id='A',distance=.1)])
matcher=Matcher()
parent=output([Segment('main',0,0.,20/60,[]),Segment('main',0,20/60,.5,[])])
projected=[(0,Segment('main',0,0.,20/60,[])),(1,Segment('main',0,20/60,22/60,[]))]
original=output([s for _,s in projected])
joints={f:{'status':'accepted','name':'B' if f==20 else 'A'} for f in frames}
guarded,audit=validate_identity_padding(original,parent,projected,frame_records=records,fps=60.,sample_step=4,
    cut_frames=[],handoffs=[],matcher=matcher,joint_matches=joints,frozen_observations=rows)
recovered=recover_final_face_edges(guarded,matcher,video_path=None,handoffs=[],joint_matches=joints,frame_records=records)
result={'source_sha256':manifest,'input_names':[d.reference_id for d in original['decisions']],
    'guarded_names':[d.reference_id for d in guarded['decisions']],'guard_rejected':audit['rejected'],
    'after_recovery':[[s.start,s.end,d.reference_id] for s,d in zip(recovered['segments'],recovered['decisions'])],
    'edge_recoveries':recovered.get('edge_recoveries'),
    'joint_at_conflict':joints[20],'models_called':False,'video_read':False}
(OUT/'guard-recovery-counterexample.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps(result,ensure_ascii=False,indent=2))
