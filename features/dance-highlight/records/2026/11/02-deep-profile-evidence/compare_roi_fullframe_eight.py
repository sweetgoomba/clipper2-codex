"""Read-only same-source-frame alternative-face diagnosis; explicit --run required.

Source membership, photo roster, thresholds and model weights remain frozen.
ROI/fullframe/saved alternatives have ONE source frame id, never separate votes.
Outputs, PNG crops and reusable diagnostic vectors stay below --output.
"""
import argparse, dataclasses, hashlib, json, os, sys, time
from pathlib import Path
ROOT = Path('/Users/jina/project/adlight/desktop/clipper_python')
BASE = Path('/private/tmp/dance-yunet-sface-20261102/app/new')
PROJECTS = Path.home()/'Library/Application Support/Clipper Studio Dev/projects/files/116957ce-bd03-4d4a-a21d-984dc12487aa'
MODEL_DIR = Path.home()/'Library/Application Support/Clipper Studio Dev/plugin_models/dance_highlight'
CASES = [('ANT','1793603739918',[280,296,320,344]), ('MMN','1793603593237',[2300,2320,2344,2356])]


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()


def encode(value):
    if dataclasses.is_dataclass(value): return dataclasses.asdict(value)
    if hasattr(value, 'tolist'): return value.tolist()
    if isinstance(value, Path): return str(value)
    if isinstance(value, set): return sorted(value)
    raise TypeError(type(value).__name__)


def write_json(path, value):
    Path(path).write_text(json.dumps(value, default=encode, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true', help='Explicitly permit bounded model inference')
    parser.add_argument('--output', type=Path, default=Path('/private/tmp/dance-deep-profile-20261102/quality/roi-fullframe-eight'))
    args = parser.parse_args()
    if not args.run:
        print('Prepared. No models loaded. Pass --run only after the app benchmark finishes.'); return
    sys.path.insert(0, str(ROOT/'plugins/dance_highlight'))
    sys.path.insert(0, str(ROOT))
    os.environ['CLIPPER_DANCE_FACE_MODEL_DIR'] = str(MODEL_DIR)
    import cv2, numpy as np
    from dance_highlight.services.config import DanceConfig
    from dance_highlight.services.face_cluster import FaceClusterService
    from dance_highlight.services.face_runtime import configure_cpu_threads
    from dance_highlight.services.face_models import SECONDARY_FACE_MODEL_SPEC, is_model_file_valid
    from dance_highlight.services.opencv_acceleration import secondary_recognizer, runtime_status
    from dance_highlight.services.face_evidence import FaceObservation, select_pose_face
    from dance_highlight.services.segment import FrameRec, Segment
    from dance_highlight.services.face_recovery import ReferenceObservationMatcher
    from dance_highlight.services.reference_matcher import ReferenceEmbeddingSample
    from dance_highlight.services.member_timeline import build_video_anchors, match_video_anchors, _valid
    from dance_highlight.services.secondary_faces import _normalized, build_secondary_gallery, match_secondary_vector, match_secondary_video
    from dance_highlight.services.joint_identity import joint_video_matches
    from dance_highlight.services.track import bbox_iou
    from dance_highlight.services.source_reader import SourceFrameReader
    args.output.mkdir(parents=True, exist_ok=True)
    spath = MODEL_DIR/SECONDARY_FACE_MODEL_SPEC.filename
    assert is_model_file_valid(spath, SECONDARY_FACE_MODEL_SPEC), 'Existing SFace weights missing or invalid; no download permitted'
    configure_cpu_threads()
    summaries = []
    photo_cache = {}

    def row(data):
        return FaceObservation(**{**data, 'embedding':np.array(data['embedding'],np.float32) if data['embedding'] is not None else None})

    def face15(observation):
        b = observation.face_bbox
        return np.array([b[0],b[1],b[2]-b[0],b[3]-b[1],*np.asarray(observation.landmarks).reshape(-1), observation.detector_score], np.float32)

    def sfeature(recognizer, image, face, path=None):
        aligned = recognizer.alignCrop(image, face)
        if path is not None: assert cv2.imwrite(str(path),aligned)
        vector = _normalized(recognizer.feature(aligned))
        assert vector is not None and vector.size == 128
        return vector

    def shift_face(face, offset):
        f = np.asarray(face,np.float32).copy()
        f[0] += offset[0]; f[1] += offset[1]
        f[4:14:2] += offset[0]; f[5:14:2] += offset[1]
        return f

    def ownership(faces, offset, body, record, min_score):
        faces = sorted([] if faces is None else faces, key=lambda f:float(f[-1]), reverse=True)
        faces = [f for f in faces if float(f[-1]) >= min_score]
        source = [shift_face(f,offset) for f in faces]
        boxes = [(float(f[0]),float(f[1]),float(f[0]+f[2]),float(f[1]+f[3])) for f in source]
        index, failure = select_pose_face(boxes, body, record)
        heads = []
        for pts in record.person_head_keypoints:
            pts=np.asarray(pts,np.float32)[:5]
            heads.append(pts[np.isfinite(pts).all(axis=1)&(pts[:,2]>=.5),:2])
        counts = [[int(np.sum((p[:,0]>=b[0])&(p[:,0]<=b[2])&(p[:,1]>=b[1])&(p[:,1]<=b[3]))) for p in heads] for b in boxes]
        return dict(sorted_yunet15_local=faces,sorted_yunet15_source=source,selected_index=index,failure=failure,
                    original_body_iou=[bbox_iou(body,b) for b in record.person_bboxes],head_point_counts_by_face_and_body=counts)

    class DetectorCapture:
        def __init__(self, wrapped, folder): self.wrapped,self.folder,self.calls=wrapped,folder,[]
        def __getattr__(self,key): return getattr(self.wrapped,key)
        def setInputSize(self,size): self.size=tuple(size);return self.wrapped.setInputSize(size)
        def detect(self,image):
            started=time.perf_counter();result=self.wrapped.detect(image);elapsed=time.perf_counter()-started
            path=self.folder/f'detector-input-{len(self.calls)}.png'
            assert cv2.imwrite(str(path),image)
            self.calls.append(dict(input_size=self.size,input_png=str(path),seconds=elapsed,status=result[0],yunet15=None if result[1] is None else result[1].copy()))
            return result

    class AuraCapture:
        def __init__(self,wrapped,folder):self.wrapped,self.folder,self.calls=wrapped,folder,[]
        def __getattr__(self,key):return getattr(self.wrapped,key)
        def alignCrop(self,image,face):
            aligned=self.wrapped.alignCrop(image,face);path=self.folder/f'auraface-aligned-{len(self.calls)}.png'
            assert cv2.imwrite(str(path),aligned)
            self.calls.append(dict(yunet15=np.asarray(face).copy(),aligned_png=str(path),aligned_pixel_sha256=hashlib.sha256(aligned.tobytes()).hexdigest()))
            return aligned
        def feature(self,aligned):return self.wrapped.feature(aligned)

    for label,pid,frames in CASES:
        folder=args.output/label;folder.mkdir(exist_ok=True)
        epath=BASE/pid/'face_evidence.json';mpath=BASE/pid/'dance_meta.json'
        e=json.loads(epath.read_text());meta=json.loads(mpath.read_text());fps=meta['stats']['fps'];source=Path(meta['input_video'])
        originals={o['frame_index']:row(o) for s in e['segments'][:e['main_result_count']] for o in s['owned_observations']}
        poses={round(p['time_seconds']*fps):p for p in e['pose_heads']}
        refs=[ReferenceEmbeddingSample(**{**r,'embedding':np.array(r['embedding'],np.float32)}) for r in e['references']]
        models=e['runtime']['models'];size=(meta['diagnostics']['frame_width'],meta['diagnostics']['frame_height'])
        started=time.perf_counter();service=FaceClusterService(DanceConfig(**meta['config']));service._detector.prepare_source(size);secondary=secondary_recognizer(service,spath)
        model_init=time.perf_counter()-started
        assert all(service.model_provenance[k]['sha256']==v['sha256'] for k,v in models.items())
        matcher=ReferenceObservationMatcher(references=refs,analysis_id='same-frame-alternatives',video_sha256=e['runtime']['video_sha256'],detector_sha256=models['opencv-yunet-face-detection']['sha256'],recognizer_sha256=models['auraface-v1-face-recognition']['sha256'],config_sha256=e['runtime']['config_sha256'],backend_version=e['runtime']['opencv'],video_size=size,max_distance=.6)
        scope=Segment('main',0,0,meta['stats']['duration_sec'],[])
        report=dict(case=label,project_id=pid,source=str(source),source_sha256=e['runtime']['video_sha256'],evidence_sha256=digest(epath),meta_sha256=digest(mpath),config=meta['config'],fps=fps,models=models,secondary_model_sha256=SECONDARY_FACE_MODEL_SPEC.sha256,policy=e['policy'],joint_policy=e['secondary_reference_refinement']['joint_policy'],source_frame_count=len(frames),alternative_independence='ROI, fullframe and saved candidates from one frame share one source observation; never combine as independent votes',timings=dict(model_initialization=model_init),frames=[])
        queries={}
        started=time.perf_counter()
        with SourceFrameReader(source,fps) as reader:
            for f in frames:
                frame_folder=folder/str(f);frame_folder.mkdir(exist_ok=True)
                image=reader.get(f);saved=originals[f];p=poses[f];body=np.array(saved.body_bbox,np.float32)
                record=FrameRec(p['time_seconds'],saved.track_id,body,False,person_bboxes=[np.array(b,np.float32) for b in p['body_boxes']],person_head_keypoints=[np.array(h,np.float32) for h in p['head_keypoints']],person_pose_keypoints=[np.array(k,np.float32) for k in p['pose_keypoints']])
                assert cv2.imwrite(str(frame_folder/'source.png'),image)
                data=dict(frame_index=f,time_seconds=saved.time_seconds,source_png=str(frame_folder/'source.png'),source_pixel_sha256=hashlib.sha256(image.tobytes()).hexdigest(),pose=p,saved_observation=saved,source_joint_match=e['secondary_reference_refinement']['joint_matches'].get(str(f)),alternatives={})
                saved_sf=sfeature(secondary,image,face15(saved),frame_folder/'saved-sface-aligned.png')
                queries[(f,'saved')]=(saved,saved_sf)
                data['alternatives']['saved']=dict(observation=saved,sface_vector=saved_sf,sface_alignment_face15=face15(saved),sface_aligned_png=str(frame_folder/'saved-sface-aligned.png'),raw15_note='Reconstructed from saved bbox/landmarks; original detector row was not retained by the historical run')
                expected=service.expand_face_roi(body,*size);actual=tuple(int(v) for v in saved.roi_bbox)
                data['roi_config_matches_saved']=expected==actual;assert expected==actual,(f,expected,actual)
                for variant,box in [('roi',actual),('fullframe',(0,0,*size))]:
                    vf=frame_folder/variant;vf.mkdir(exist_ok=True);x1,y1,x2,y2=box;crop=image[y1:y2,x1:x2]
                    detector=DetectorCapture(service._detector,vf);recognizer=AuraCapture(service._recognizer,vf)
                    service._detector,service._recognizer=detector,recognizer
                    tick=time.perf_counter()
                    try:candidate,failure=service._inspect_face(crop,pose_record=record,source_body=body,offset=(x1,y1),require_pose=True)
                    finally:service._detector,service._recognizer=detector.wrapped,recognizer.wrapped
                    alt=dict(seconds=time.perf_counter()-tick,roi_bbox=box,failure=failure,detector_calls=detector.calls,auraface_alignment=recognizer.calls)
                    if detector.calls:alt['unrotated_pose_ownership']=ownership(detector.calls[0]['yunet15'],(x1,y1),body,record,float(service.config.face_min_det_score))
                    if candidate is not None:
                        def shift_box(b):return (b[0]+x1,b[1]+y1,b[2]+x1,b[3]+y1)
                        obs=dataclasses.replace(saved,roi_bbox=box,face_bbox=shift_box(candidate.face_bbox),landmarks=tuple((x+x1,y+y1) for x,y in candidate.landmarks),candidate_boxes=tuple(shift_box(b) for b in candidate.candidate_boxes),embedding=candidate.embedding,quality=candidate.quality,detector_score=candidate.detector_score,face_sharpness=candidate.face_sharpness,failure=None,association='confirmed',detection_rotation_degrees=candidate.detection_rotation_degrees)
                        sf=sfeature(secondary,image,face15(obs),vf/'sface-aligned.png');queries[(f,variant)]=(obs,sf)
                        raw=recognizer.calls[-1]['yunet15'];alt.update(observation=obs,sface_vector=sf,sface_alignment_face15=face15(obs),sface_aligned_png=str(vf/'sface-aligned.png'),selected_yunet15_local=raw,selected_yunet15_source=shift_face(raw,(x1,y1)),same_frame_aura_cosine_distance_from_saved=float(1.-obs.embedding@saved.embedding),same_frame_sface_cosine_distance_from_saved=float(1.-sf@saved_sf),landmark_rms_px_from_saved=float(np.sqrt(np.mean((np.asarray(obs.landmarks)-np.asarray(saved.landmarks))**2))),eligible_current_valid=_valid(obs),eligible_strong_face=obs.detector_score>=.9)
                    data['alternatives'][variant]=alt
                report['frames'].append(data)
                write_json(frame_folder/'comparison.json',data)
                print(label,'query',f,[(v,a.get('observation').detector_score if a.get('observation') else a.get('failure')) for v,a in data['alternatives'].items()],flush=True)
            report['query_decode']=reader.stats
        report['timings']['eight_frame_query_part']=time.perf_counter()-started
        write_json(folder/'comparison.json',report)

        # Recreate only the historical frozen gallery, with separate cost accounting.
        tick=time.perf_counter();photo_samples=[];photo_audit=[]
        wanted={(r['name'],r['source_sha256']) for r in e['secondary_reference_refinement']['references']}
        for member in sorted((PROJECTS/pid/'refs/dance').iterdir()):
            if not member.is_dir():continue
            for path in sorted(member.iterdir()):
                if not path.is_file():continue
                sha=digest(path);key=(member.name,sha)
                if key not in wanted:continue
                reused=key in photo_cache
                if not reused:
                    image=cv2.imdecode(np.frombuffer(path.read_bytes(),np.uint8),cv2.IMREAD_COLOR)
                    cand=service.get_face_embedding_candidate(image);assert cand is not None,key
                    raw=np.array([cand.face_bbox[0],cand.face_bbox[1],cand.face_bbox[2]-cand.face_bbox[0],cand.face_bbox[3]-cand.face_bbox[1],*np.asarray(cand.landmarks).reshape(-1),cand.detector_score],np.float32)
                    photo_cache[key]=sfeature(secondary,image,raw)
                photo_samples.append((*key,photo_cache[key]));photo_audit.append(dict(name=member.name,source_sha256=sha,path=str(path),cache_reused=reused))
        assert {(n,h) for n,h,_ in photo_samples}==wanted,'Historical SFace photo set mismatch'
        roster={r.reference_id for r in refs};gallery=build_secondary_gallery(photo_samples,roster);assert gallery is not None
        report['timings']['frozen_photo_gallery']=time.perf_counter()-tick
        anchors=e['secondary_reference_refinement']['video_anchors'];anchor_frames=sorted({a['frame_index'] for a in anchors})
        tick=time.perf_counter();vectors={}
        with SourceFrameReader(source,fps,max_bytes=8*1024*1024) as reader:
            for j,f in enumerate(anchor_frames):
                saved=originals[f];vectors[f]=sfeature(secondary,reader.get(f),face15(saved))
                if j%200==0:print(label,'frozen gallery',j,'/',len(anchor_frames),flush=True)
            report['gallery_decode']=reader.stats
        report['timings']['frozen_video_gallery']=time.perf_counter()-tick
        np.savez_compressed(folder/'frozen-sface-vectors.npz',**{str(f):v for f,v in vectors.items()})
        write_json(folder/'frozen-gallery.json',dict(evidence_sha256=report['evidence_sha256'],anchors=anchors,photo_samples=[dict(name=n,source_sha256=h,embedding=v) for n,h,v in photo_samples],photos=photo_audit,roster=roster,primary_reference_fingerprint=matcher.gallery.fingerprint))
        tick=time.perf_counter()
        ordered=list(originals.values());matches=[matcher.match(o,scope,'frozen-original') for o in ordered]
        primary_anchors=build_video_anchors(ordered,matches)
        report['primary_anchor_count']=len(primary_anchors);report['frozen_dual_anchor_count']=len(anchors)
        sanchors=[(a['name'],dataclasses.replace(originals[a['frame_index']],embedding=vectors[a['frame_index']])) for a in anchors]
        frozen_rows={f:originals[f] for f in anchor_frames}
        parity=[]
        for data in report['frames']:
            f=data['frame_index']
            for variant,alt in data['alternatives'].items():
                if (f,variant) not in queries:continue
                obs,sf=queries[(f,variant)]
                joint=joint_video_matches({**frozen_rows,f:obs},{**vectors,f:sf},anchors,roster,query_frames={f})[f]
                alt['matches']=dict(auraface_reference=matcher.match(obs,scope,'same-frame-alternative'),auraface_video_name=match_video_anchors(obs,primary_anchors),sface_reference=match_secondary_vector(sf,gallery),sface_video=match_secondary_video(dataclasses.replace(obs,embedding=sf),sanchors,gallery),joint=joint)
                if variant=='saved':
                    old=data['source_joint_match'] or {};parity.append(dict(frame_index=f,old=old,new=joint,same_status_name=(old.get('status'),old.get('name'))==(joint.get('status'),joint.get('name')),distance_delta=abs(old.get('distance',0)-joint.get('distance',0))))
            write_json(folder/str(f)/'comparison.json',data)
        report['frozen_joint_saved_query_parity']=parity;report['timings']['frozen_matching_no_model']=time.perf_counter()-tick;report['runtime']=runtime_status(service)
        report['summary']=[dict(frame_index=d['frame_index'],time_seconds=d['time_seconds'],alternatives={v:dict(failure=a.get('failure'),score=a['observation'].detector_score if 'observation' in a else None,rotation=a['observation'].detection_rotation_degrees if 'observation' in a else None,landmark_rms=a.get('landmark_rms_px_from_saved'),aura_distance_from_saved=a.get('same_frame_aura_cosine_distance_from_saved'),sface_distance_from_saved=a.get('same_frame_sface_cosine_distance_from_saved'),matches=a.get('matches')) for v,a in d['alternatives'].items()}) for d in report['frames']]
        write_json(folder/'comparison.json',report)
        summaries.append({k:report[k] for k in ('case','timings','source_frame_count','primary_anchor_count','frozen_dual_anchor_count','frozen_joint_saved_query_parity','summary')})
        write_json(args.output/'summary.json',summaries)
        print(label,'complete',report['timings'],flush=True)
    print('Done. No production writes. Same-frame alternatives have not been combined.',flush=True)


if __name__=='__main__':main()
