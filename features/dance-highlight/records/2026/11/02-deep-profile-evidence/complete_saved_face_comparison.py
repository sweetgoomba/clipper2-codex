"""Finish diagnostic tables entirely from the already saved vectors; NO inference."""
import sys,json,time
from pathlib import Path
from dataclasses import asdict,replace
import numpy as np
sys.path.insert(0,'/Users/jina/project/adlight/desktop/clipper_python/plugins/dance_highlight')
from dance_highlight.services.face_evidence import FaceObservation
from dance_highlight.services.face_recovery import ReferenceObservationMatcher
from dance_highlight.services.reference_matcher import ReferenceEmbeddingSample
from dance_highlight.services.segment import Segment
from dance_highlight.services.member_timeline import build_video_anchors,match_video_anchors
from dance_highlight.services.secondary_faces import build_secondary_gallery,match_secondary_vector,match_secondary_video
from dance_highlight.services.joint_identity import joint_video_matches
root=Path('/private/tmp/dance-deep-profile-20261102/quality/roi-fullframe-eight');summaries=[]
def loadrow(r):return FaceObservation(**(r|{'embedding':None if r['embedding'] is None else np.array(r['embedding'],np.float32)}))
def enc(x):
 if hasattr(x,'tolist'):return x.tolist()
 return asdict(x)
for label in ['ANT','MMN']:
 folder=root/label;path=folder/'comparison.json';report=json.loads(path.read_text());e=json.loads((Path('/private/tmp/dance-yunet-sface-20261102/app/new')/report['project_id']/'face_evidence.json').read_text());frozen=json.loads((folder/'frozen-gallery.json').read_text());vectors={int(f):v for f,v in np.load(folder/'frozen-sface-vectors.npz').items()};refs=[ReferenceEmbeddingSample(**(r|{'embedding':np.array(r['embedding'],np.float32)})) for r in e['references']]
 rows={r['frame_index']:loadrow(r) for s in e['segments'][:e['main_result_count']] for r in s['owned_observations']};size=(1920,1080);models=e['runtime']['models'];scope=Segment('main',0,0,max(o.time_seconds for o in rows.values())+1,[])
 matcher=ReferenceObservationMatcher(references=refs,analysis_id='same-frame-alternatives',video_sha256=e['runtime']['video_sha256'],detector_sha256=models['opencv-yunet-face-detection']['sha256'],recognizer_sha256=models['auraface-v1-face-recognition']['sha256'],config_sha256=e['runtime']['config_sha256'],backend_version=e['runtime']['opencv'],video_size=size,max_distance=.6)
 assert matcher.gallery.fingerprint==frozen['primary_reference_fingerprint']
 tick=time.perf_counter();ordered=list(rows.values());anchors=build_video_anchors(ordered,[matcher.match(o,scope,'frozen-original') for o in ordered]);gallery=build_secondary_gallery([(r['name'],r['source_sha256'],np.array(r['embedding'],np.float32)) for r in frozen['photo_samples']],set(frozen['roster']));sanchors=[(a['name'],replace(rows[a['frame_index']],embedding=vectors[a['frame_index']])) for a in frozen['anchors']];frozen_rows={f:rows[f] for f in vectors};parity=[]
 for data in report['frames']:
  f=data['frame_index']
  for variant,alt in data['alternatives'].items():
   if 'observation' not in alt:continue
   o=loadrow(alt['observation']);sf=np.array(alt['sface_vector'],np.float32);joint=joint_video_matches({**frozen_rows,f:o},{**vectors,f:sf},frozen['anchors'],set(frozen['roster']),query_frames={f})[f]
   alt['matches']=dict(auraface_reference=matcher.match(o,scope,'same-frame-alternative'),auraface_video_name=match_video_anchors(o,anchors),sface_reference=match_secondary_vector(sf,gallery),sface_video=match_secondary_video(replace(o,embedding=sf),sanchors,gallery),joint=joint)
   if variant=='saved':
    old=data['source_joint_match'] or {};parity.append(dict(frame_index=f,old=old,new=joint,same_status_name=(old.get('status'),old.get('name'))==(joint.get('status'),joint.get('name')) if old else None,distance_delta=abs(old['distance']-joint['distance']) if 'distance' in old and 'distance' in joint else None))
  (folder/str(f)/'comparison.json').write_text(json.dumps(data,default=enc,ensure_ascii=False,indent=2))
 report['frozen_joint_saved_query_parity']=parity;report['primary_anchor_count']=len(anchors);report['frozen_dual_anchor_count']=len(frozen['anchors']);report['timings']['final_matching_no_inference']=time.perf_counter()-tick
 if 'frozen_video_gallery' not in report['timings']:
  report['timings']['frozen_gallery_wall_estimate_from_saved_file_mtimes']=(folder/'frozen-gallery.json').stat().st_mtime-path.stat().st_mtime
  report['timings']['note']='First script completed all vectors but stopped on absent historical match for invalid score <.8. Final tables computed with no inference. MMN gallery elapsed estimate includes photo-cache reuse and saving.'
 report['summary']=[dict(frame_index=d['frame_index'],time_seconds=d['time_seconds'],alternatives={v:dict(failure=a.get('failure'),score=a['observation']['detector_score'] if 'observation' in a else None,rotation=a['observation']['detection_rotation_degrees'] if 'observation' in a else None,landmark_rms=a.get('landmark_rms_px_from_saved'),aura_distance_from_saved=a.get('same_frame_aura_cosine_distance_from_saved'),sface_distance_from_saved=a.get('same_frame_sface_cosine_distance_from_saved'),matches=a.get('matches')) for v,a in d['alternatives'].items()}) for d in report['frames']]
 path.write_text(json.dumps(report,default=enc,ensure_ascii=False,indent=2));summaries.append({k:report[k] for k in ('case','timings','source_frame_count','primary_anchor_count','frozen_dual_anchor_count','frozen_joint_saved_query_parity','summary')});print(label,'complete',report['timings'],flush=True)
(root/'summary.json').write_text(json.dumps(summaries,default=enc,ensure_ascii=False,indent=2))
