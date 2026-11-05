from pathlib import Path
from types import SimpleNamespace
import sys,json,numpy as np,time
ROOT=Path('/Users/jina/project/adlight/desktop/clipper_python');sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'plugins/dance_highlight')]
from dance_highlight.services.config import DanceConfig
from dance_highlight.services.face_cluster import FaceClusterService
from dance_highlight.services.segment import Segment,FrameRec
from dance_highlight.services.reference_matcher import ReferenceEmbeddingSample,SegmentReferenceDecision
from dance_highlight.services.face_recovery import ReferenceObservationMatcher
from dance_highlight.services.member_timeline import refine_member_timeline
base=Path.home()/'Library/Application Support/Clipper Studio Dev/projects/files/116957ce-bd03-4d4a-a21d-984dc12487aa/1793674437287';e=json.loads((base/'diagnostics/face_evidence.json').read_text());data=json.loads((ROOT/'tests/fixtures/dance_scene_review/mmn103_role_subject.json').read_text());byframe={r['frame']:r['expected_box'] for r in data['rows']};fps=59.94005994005994
records=[];bboxes=[]
for r in e['pose_heads']:
 f=round(r['time_seconds']*fps)
 if not 6172<=f<=6188:continue
 box=np.array(byframe[f]);bboxes.append((r['time_seconds'],box,7));records.append(FrameRec(r['time_seconds'],7,box,False,person_bboxes=[np.array(b) for b in r['body_boxes']],person_head_keypoints=[np.array(p) for p in r['head_keypoints']],person_pose_keypoints=[np.array(p) for p in r['pose_keypoints']]))
seg=Segment('main',7,102.93616666666667,103.25315,bboxes)
face=FaceClusterService(DanceConfig());start=time.perf_counter();results=face.batch_segment_embeddings(str(base/'diagnostics/source.mp4'),[seg],frame_records=records,sample_all_main_frames=True)
refs=[ReferenceEmbeddingSample(**dict(r,embedding=np.array(r['embedding']))) for r in e['references']]
matcher=ReferenceObservationMatcher(references=refs,analysis_id='corrected-owner-probe',video_sha256=e['runtime']['video_sha256'],detector_sha256='b'*64,recognizer_sha256='c'*64,config_sha256=e['runtime']['config_sha256'],backend_version='new-face-probe',video_size=(1920,1080),max_distance=.6)
out=refine_member_timeline([seg],[SegmentReferenceDecision(None,'unmatched','probe')],[None],[[]],results,matcher)
from dance_highlight.services.face_evidence import FaceObservation
from dance_highlight.services.member_timeline import build_video_anchors, refine_unresolved_with_names
from dance_highlight.services.secondary_faces import recover_secondary_names
original_rows=[FaceObservation(**dict(o,embedding=np.array(o['embedding']) if o['embedding'] is not None else None)) for scope in e['segments'][:e['main_result_count']] for o in scope['owned_observations']]
original_scope=Segment('main',None,0.,max(o.time_seconds for o in original_rows)+1.,[])
original_matches=[matcher.match(o,original_scope,'seed') for o in original_rows]
out['anchors']=build_video_anchors(original_rows,original_matches)
photos={p.name:sorted(p.glob('*')) for p in (base/'refs/dance').iterdir() if p.is_dir()}
names,secondary=recover_secondary_names(base/'diagnostics/source.mp4',photos,out,face,defer_structure=True)
out=refine_unresolved_with_names(out,names,matcher,video_path=str(base/'diagnostics/source.mp4'))
r={'secondary_reason':secondary['reason'],'secondary_names':names,'seconds':time.perf_counter()-start,'new_selected_owner_face_matches':[(o.frame_index,matcher.match(o,seg,'probe').reference_id,o.failure) for o in results[0].owned_observations],'output':[(s.start,s.end,d.reference_id) for s,d in zip(out['segments'],out['decisions'])]}
Path('/private/tmp/dance-user-clips-20261103/corrected-owner-secondary.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));print(json.dumps(r,ensure_ascii=False))
