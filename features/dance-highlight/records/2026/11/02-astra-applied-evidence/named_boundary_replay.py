from pathlib import Path
import json,time,numpy as np
from dance_highlight.services.face_evidence import FaceObservation
from dance_highlight.services.face_recovery import ReferenceObservationMatcher
from dance_highlight.services.reference_matcher import ReferenceEmbeddingSample,SegmentReferenceDecision
from dance_highlight.services.segment import FrameRec,Segment
from dance_highlight.services.named_boundaries import reconcile_named_boundaries
ROOT=Path('/private/tmp/dance-quality-paths-20261102');M=json.load(open('/private/tmp/dance-astra-review-20261102/manifest.json'))
for name,inf in M.items():
 e=json.load(open(inf['evidence']));m=json.load(open(inf['meta']));fps=inf['fps']
 obs=[FaceObservation(**(d|{'embedding':None if d['embedding'] is None else np.array(d['embedding'],np.float32)})) for s in e['segments'][:e['main_result_count']] for d in s['owned_observations']]
 records=[FrameRec(r['time_seconds'],r['candidate_main_id'],np.asarray(r['candidate_main_bbox']) if r['candidate_main_bbox'] is not None else None,r['scene_kind']=='group',person_bboxes=[np.asarray(b) for b in r['body_boxes']],person_pose_keypoints=[np.asarray(k) for k in r['pose_keypoints']],scene_kind=r['scene_kind']) for r in e['pose_heads']]
 refs=[ReferenceEmbeddingSample(**(d|{'embedding':np.asarray(d['embedding'],np.float32)})) for d in e['references']]
 matcher=ReferenceObservationMatcher(references=refs,analysis_id='replay',video_sha256=e['runtime']['video_sha256'],detector_sha256='a'*64,recognizer_sha256='b'*64,config_sha256=e['runtime']['config_sha256'],backend_version=e['runtime']['opencv'],video_size=(m['diagnostics']['frame_width'],m['diagnostics']['frame_height']),max_distance=.6)
 clips=m['lists']['main']; segments=[Segment('main',None,c['start'],c['end'],[]) for c in clips];decisions=[SegmentReferenceDecision(None if c['person_id']=='unknown' else c['person_id'],'test','test') for c in clips]
 out=dict(segments=segments,decisions=decisions,labels=list(range(len(clips))),previews=[[] for _ in clips],evidence=[[(o,None) for o in obs if s.start<=o.time_seconds<s.end] for s in segments],preview_sources=[({}, {}) for _ in clips],accurate_indices=list(range(len(clips))),anchors=[],fallback_names={})
 groups=[Segment('group',None,c['start'],c['end'],[]) for c in m['lists']['group']]
 t=time.perf_counter();new,audit=reconcile_named_boundaries(out,records,obs,e['secondary_reference_refinement']['joint_matches'],matcher,video_path=inf['video'],fps=fps,group_segments=groups,handoffs=e['main_selection_refinement']['handoffs']);elapsed=time.perf_counter()-t
 audit['elapsed_seconds']=elapsed
 audit['output']=[dict(start=s.start,end=s.end,name=d.reference_id) for s,d in zip(new['segments'],new['decisions'])]
 (ROOT/f'{name}-named-boundaries-replay.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))
 assert abs(sum(s.end-s.start for s in segments)-sum(s.end-s.start for s in new['segments']))<1e-6
 print(name,json.dumps({k:v for k,v in audit.items() if k not in ('candidates','output')},ensure_ascii=False),flush=True)
