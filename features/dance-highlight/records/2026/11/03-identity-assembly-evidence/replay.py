"""Pure boundary assembly over frozen diagnostics, no model or video IO."""
import sys,json,time,hashlib
from pathlib import Path
from dataclasses import replace
import numpy as np
ROOT=Path('/Users/jina/project/adlight/desktop/clipper_python')
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'plugins/dance_highlight')]
from dance_highlight.services.identity_projection import validate_identity_padding
from dance_highlight.services.performance_parts import _project
from dance_highlight.services.scene_boundaries import project_main_at_scene_cuts
from dance_highlight.services.face_recovery import ReferenceObservationMatcher
from dance_highlight.services.reference_matcher import ReferenceEmbeddingSample
from dance_highlight.services.part_boundary_events import coalesce_boundary_events
from dance_highlight.services.segment import Segment,FrameRec,build_main_evidence_scopes,build_raw_main_segments
from dance_highlight.services.face_evidence import FaceObservation
from dance_highlight.services.reference_matcher import SegmentReferenceDecision
BASE=Path('/Users/jina/Library/Application Support/Clipper Studio Dev/projects/files/116957ce-bd03-4d4a-a21d-984dc12487aa')
OUT=Path('/private/tmp/dance-identity-assembly-20261103')

def union(ranges):
 result=[]
 for lo,hi in sorted(ranges):
  if result and lo <=result[-1][1]+1e-6:result[-1][1]=max(result[-1][1],hi)
  else:result.append([lo,hi])
 return result

reports={}
for label,pid in [('MMN','1793649506337'),('ANT','1793649573540'),('NEON','1793649654322')]:
 src=BASE/pid;ep=src/'diagnostics/face_evidence.json';mp=src/'json/dance_meta.json'
 e=json.loads(ep.read_text());meta=json.loads(mp.read_text());a=e['output_named_continuity']['performance_parts'];fps=meta['stats']['fps'];records=[]
 for r in e['pose_heads']:
  box=np.asarray(r['candidate_main_bbox']) if r['candidate_main_bbox'] is not None else None
  records.append(FrameRec(r['time_seconds'],r['candidate_main_id'],box if r['scene_kind']=='main' else None,r['scene_kind']=='group',person_bboxes=[np.asarray(b) for b in r['body_boxes']],person_pose_keypoints=[np.asarray(p) for p in r['pose_keypoints']],candidate_main_bbox=box,scene_kind=r['scene_kind']))
 rows=[FaceObservation(**{k:np.asarray(v) if k=='embedding' and v is not None else v for k,v in o.items()}) for s in e['segments'][:e['main_result_count']] for o in s['owned_observations']]
 output=dict(segments=[],decisions=[],labels=[],evidence=[],preview_sources=[],previews=[],accurate_indices=[],anchors=[])
 for i,p in enumerate(a['parts']):
  start,end=p['range'];local=[r for r in rows if start<=r.time_seconds<end];name=p['name']
  output['segments'].append(Segment('main',i,start,end,[(r.time_seconds,np.asarray(r.body_bbox),r.track_id) for r in local]))
  output['decisions'].append(SegmentReferenceDecision(name,'matched' if name else 'unmatched','frozen_actual_output'))
  output['labels'].append(i if name else None);output['evidence'].append([(r,None) for r in local]);output['preview_sources'].append(({},{}));output['previews'].append([])
 eligibility=build_main_evidence_scopes(build_raw_main_segments(records))
 changes={r['observed_time']:r['cut_time'] for r in e['scene_boundary_refinement']['changes']}
 eligibility=[replace(s,start=changes.get(s.start,s.start),end=changes.get(s.end,s.end)) for s in eligibility]
 eligibility.extend(Segment('main',None,r['start'],r['end'],[]) for r in e['main_selection_refinement'].get('output_context',{}).get('restored',[]))
 cuts=sorted(set(e['main_selection_refinement']['cut_frames']) | {c['cut_frame'] for c in e['scene_boundary_refinement']['changes']})
 identity=dict(audit=e['identity_refinement'])
 args=dict(frame_records=records,frozen_observations=rows,joint_matches=e['secondary_reference_refinement']['joint_matches'],eligibility=eligibility,fps=fps,sample_step=4,cut_frames=cuts,handoffs=e['main_selection_refinement']['handoffs'])
 source_identity=dict(segments=[],decisions=[],labels=[],evidence=[],preview_sources=[],previews=[],accurate_indices=[],anchors=[])
 for span in a['identity_spans']:
  lo,hi=span['range'];local=[r for r in rows if r.frame_index in span['observation_frames']]
  source_identity['segments'].append(Segment('main',span['id'],lo,hi,[]));source_identity['decisions'].append(SegmentReferenceDecision(span['name'],'matched' if span['name'] else 'unmatched',span['reason']))
  source_identity['labels'].append(span['id']);source_identity['evidence'].append([(r,None) for r in local]);source_identity['preview_sources'].append(({},{}));source_identity['previews'].append([])
 projected,_=project_main_at_scene_cuts(source_identity['segments'],eligibility,fps=fps,cut_times=[c['cut_time'] for c in e['scene_boundary_refinement']['changes']])
 refs=[ReferenceEmbeddingSample(**dict(r,embedding=np.asarray(r['embedding']))) for r in e['references']]
 matcher=ReferenceObservationMatcher(references=refs,analysis_id='frozen-projection-replay',video_sha256='a'*64,detector_sha256='b'*64,recognizer_sha256='c'*64,config_sha256='d'*64,backend_version='opencv-replay',video_size=(1920,1080),max_distance=.6)
 args['matcher']=matcher
 start=time.perf_counter()
 validated,guard=validate_identity_padding(_project(source_identity,projected),source_identity,projected,frame_records=records,fps=fps,sample_step=4,cut_frames=cuts,handoffs=args['handoffs'],matcher=matcher,joint_matches=args['joint_matches'],frozen_observations=rows)
 guard_seconds=time.perf_counter()-start
 conflicts=[r for r in guard['rejected'] if r['reason']=='conflicting_projected_identity']
 for c in conflicts:
  found=[i for i,s in enumerate(output['segments']) if abs(s.start-c['start'])<1e-6 and abs(s.end-c['end'])<1e-6 and output['decisions'][i].reference_id==c['name']]
  assert len(found)==1, c
  i=found[0];output['decisions'][i]=SegmentReferenceDecision(None,'unmatched',c['reason']);output['labels'][i]=None
 start=time.perf_counter();new,audit=coalesce_boundary_events(output,identity,**args);elapsed=time.perf_counter()-start
 assert union((s.start,s.end) for s in output['segments'])==union((s.start,s.end) for s in new['segments'])
 assert [r.frame_index for group in output['evidence'] for r,_ in group]==[r.frame_index for group in new['evidence'] for r,_ in group]
 newmeta=json.loads(json.dumps(meta))
 for c in conflicts:
  found=[p for p in newmeta['lists']['main'] if abs(p['start']-c['start'])<1e-6 and abs(p['end']-c['end'])<1e-6 and p['person_id']==c['name']]
  assert len(found)==1
  found[0]['person_id']='unknown';found[0]['match_status']='unmatched';found[0]['match_reason']=c['reason']
 for join in audit['joins']:
  lo=join['boundary'];hi=join['canonical_time'];name=join['name'] or 'unknown'
  left=[c for c in newmeta['lists']['main'] if abs(c['end']-lo)<1e-6 and c['person_id']==name]
  right=[c for c in newmeta['lists']['main'] if abs(c['start']-lo)<1e-6 and abs(c['end']-hi)<1e-6 and c['person_id']=='unknown']
  assert len(left)==len(right)==1,(label,join)
  left[0]['end']=hi
  if 'duration' in left[0]:left[0]['duration']=hi-left[0]['start']
  newmeta['lists']['main'].remove(right[0])
 assert newmeta['lists']['group']==meta['lists']['group']
 def metrics(m):
  clips=m['lists']['main']+m['lists']['group'];return dict(clips=len(clips),short=sum(c['end']-c['start']<1 for c in clips),unknown=sum(c['end']-c['start'] for c in m['lists']['main'] if c['person_id']=='unknown'))
 reports[label]=dict(project_id=pid,seconds=elapsed,projection_guard_seconds=guard_seconds,projection_conflicts=conflicts,source_sha256=hashlib.sha256(ep.read_bytes()).hexdigest(),before=metrics(meta),after=metrics(newmeta),audit=audit,main_union_unchanged=True,group_unchanged=True,observations_unchanged=True)
 dest=OUT/'replay'/pid/'json';dest.mkdir(parents=True,exist_ok=True);(dest/'dance_meta.json').write_text(json.dumps(newmeta,ensure_ascii=False,indent=2))
 print(label,round(elapsed,4),metrics(meta),metrics(newmeta),'joins',[(j['boundary'],j['name']) for j in audit['joins']],'reject',[(j['boundary'],j['reason']) for j in audit['rejected']])
(OUT/'replay-results.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2))
sys.path.insert(0,'/private/tmp/dance-role-continuity-20261103');import evaluate_reviewed
old=[r for label,pid in [(k,v['project_id']) for k,v in reports.items()] for r in evaluate_reviewed.evaluate(label,pid)]
evaluate_reviewed.BASE=OUT/'replay'
new=[r for label,pid in [(k,v['project_id']) for k,v in reports.items()] for r in evaluate_reviewed.evaluate(label,pid)]
assert old==new
(OUT/'reviewed-14.json').write_text(json.dumps(dict(unchanged=True,cases=new),ensure_ascii=False,indent=2));print('14 reviewed intervals unchanged')
