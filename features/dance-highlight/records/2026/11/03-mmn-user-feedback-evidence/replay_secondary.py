from pathlib import Path
from types import SimpleNamespace
import json,sys,time,numpy as np
ROOT=Path('/Users/jina/project/adlight/desktop/clipper_python');sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'plugins/dance_highlight')]
from dance_highlight.services.member_timeline import refine_member_timeline,refine_unresolved_with_names
from dance_highlight.services.face_evidence import FaceObservation
from dance_highlight.services.segment import Segment,build_main_evidence_scopes,build_raw_main_segments,FrameRec
from dance_highlight.services.reference_matcher import ReferenceEmbeddingSample,SegmentReferenceDecision
from dance_highlight.services.face_recovery import ReferenceObservationMatcher
from dance_highlight.services.scene_boundaries import project_main_at_scene_cuts
BASE=Path.home()/'Library/Application Support/Clipper Studio Dev/projects/files/116957ce-bd03-4d4a-a21d-984dc12487aa';out=Path('/private/tmp/dance-user-clips-20261103')
from dance_highlight.services.secondary_faces import recover_secondary_names
from dance_highlight.services.face_cluster import FaceClusterService
from dance_highlight.services.config import DanceConfig
face=FaceClusterService(DanceConfig())
report={}
for label,pid in [('ANT','1793674460357')]:
 root=BASE/pid;e=json.loads((root/'diagnostics/face_evidence.json').read_text());meta=json.loads((root/'json/dance_meta.json').read_text());fps=meta['stats']['fps']; segments=[];fr=[]
 for s in e['segments'][:e['main_result_count']]:
  rows=[FaceObservation(**dict(o,embedding=np.array(o['embedding']) if o['embedding'] is not None else None)) for o in s['owned_observations']]
  segments.append(Segment('main',None,s['start'],s['end'],[(o.time_seconds,np.array(o.body_bbox),o.track_id) for o in rows]));fr.append(SimpleNamespace(owned_observations=rows,owned_previews={},owned_thumbnails={}))
 refs=[ReferenceEmbeddingSample(**dict(r,embedding=np.array(r['embedding']))) for r in e['references']]
 matcher=ReferenceObservationMatcher(references=refs,analysis_id='cut-support-replay',video_sha256=e['runtime']['video_sha256'],detector_sha256='b'*64,recognizer_sha256='c'*64,config_sha256=e['runtime']['config_sha256'],backend_version='replay',video_size=(1920,1080),max_distance=.6)
 decisions=[SegmentReferenceDecision(**a['baseline']) for a in e['identity_refinement']]
 fallback={m['frame_index']:m['name'] for m in e['secondary_reference_refinement']['matches'] if m.get('name')}
 records=[]
 for r in e['pose_heads']:
  box=np.array(r['candidate_main_bbox']) if r['candidate_main_bbox'] is not None else None
  records.append(FrameRec(r['time_seconds'],r['candidate_main_id'],box if r['scene_kind']=='main' else None,r['scene_kind']=='group',candidate_main_bbox=box,scene_kind=r['scene_kind']))
 eligible=build_main_evidence_scopes(build_raw_main_segments(records));outcomes={}
 for policy,cuts in [('before',()),('after',tuple(f/fps for f in e['main_selection_refinement']['cut_frames']))]:
  started=time.perf_counter()
  x=refine_member_timeline(segments,decisions,[None]*len(segments),[[] for _ in segments],fr,matcher,video_path=str(root/'diagnostics/source.mp4'),cut_times=cuts)
  current_fallback=fallback
  if policy=='after':
   photos={p.name:sorted(p.glob('*')) for p in (root/'refs/dance').iterdir() if p.is_dir()}
   current_fallback, secondary = recover_secondary_names(root/'diagnostics/source.mp4',photos,x,face,defer_structure=True)
   print('secondary',secondary['reason'],'targets',secondary.get('target_frames'),'names',len(current_fallback),flush=True)
  x=refine_unresolved_with_names(x,current_fallback,matcher,video_path=str(root/'diagnostics/source.mp4'))
  projected,_=project_main_at_scene_cuts(x['segments'],eligible,fps=fps,cut_times=[r['cut_time'] for r in e['scene_boundary_refinement']['changes']])
  parts=[dict(start=p.start,end=p.end,name=x['decisions'][i].reference_id,reason=x['decisions'][i].reason) for i,p in projected]
  outcomes[policy]=dict(seconds=time.perf_counter()-started,parts=parts,short=sum(p['end']-p['start']<1 for p in parts),clips=len(parts))
  (out/f'{label}-{policy}-identity.json').write_text(json.dumps({'audit':x['audit'],'secondary':x.get('secondary_refinements',[]),'parts':parts},ensure_ascii=False,indent=2))
  print(label,policy,{k:v for k,v in outcomes[policy].items() if k!='parts'},flush=True)
  if label=='MMN':print('target',[p for p in parts if p['start']<51 and p['end']>50.3],flush=True)
 report[label]=outcomes
(out/'identity-secondary-rerun-comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
