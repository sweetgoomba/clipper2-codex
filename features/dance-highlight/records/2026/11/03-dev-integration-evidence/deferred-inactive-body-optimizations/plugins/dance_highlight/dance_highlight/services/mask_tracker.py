"""Source-frame SAM2 adapter, isolated from Person and shared face services."""
from dataclasses import replace
from types import SimpleNamespace
import cv2
import numpy as np

from .camera_transitions import classify_transition, photometric_body_link
from .face_models import FaceModelSpec, ensure_face_models, is_model_file_valid
from .mask_continuity import TraceFrame, evaluate_track
from .track import bbox_iou
from .mask_frame_cache import SamImageFeatures, SamMasks, source_frames, verified_transitions

MODEL_SPEC = FaceModelSpec(
    'sam2.1-tiny-body-continuity', 'sam2.1_t.pt',
    'https://github.com/ultralytics/assets/releases/download/v8.4.0/sam2.1_t.pt',
    '3c1e81ca9b037dd39d70a014ddb9a813d6c4c4e12555420db7eaff31689bd4e3', 78105722)


def permits_sampled_head_link(proof):
    if (not proof.get('accepted') and proof.get('reason') == 'weak_face_match'
            and proof.get('sampled_recheck', {}).get('eligible') is True):
        return True
    counts = proof.get('owner_counts',[])
    return (not proof.get('accepted') and proof.get('reason') == 'unconfirmed_unique_mask_face'
            and len(counts) == 2 and all(n in (0,1) for n in counts) and 0 in counts)


def head_owners(mask, heads):
    owners = []
    height,width = mask.shape
    for i,points in enumerate(heads):
        points = np.asarray(points)
        if points.ndim != 2 or points.shape[1] != 3:
            continue
        points = points[:5]
        xy = points[np.isfinite(points).all(axis=1) & (points[:,2] >= .5),:2]
        xy = np.rint(xy).astype(int)
        xy = xy[(xy[:,0]>=0)&(xy[:,0]<width)&(xy[:,1]>=0)&(xy[:,1]<height)]
        if len(xy) >= 2 and mask[xy[:,1],xy[:,0]].sum() >= 2:
            owners.append(i)
    return tuple(owners)


def pose_owners(mask, heads, poses):
    """A missing head can use a fully measured torso, never a visible wrong head."""
    owned = head_owners(mask,heads)
    if owned or len(heads) != len(poses):
        return owned,False
    height,width = mask.shape
    owners = []
    for i,(head,pose) in enumerate(zip(heads,poses,strict=True)):
        head,pose = np.asarray(head),np.asarray(pose)
        if pose.shape != (17,3) or head.ndim != 2 or head.shape[1] != 3:
            continue
        visible = head[:5]
        visible = visible[np.isfinite(visible).all(axis=1) & (visible[:,2] >= .5)]
        visible = visible[(visible[:,0] >= 0) & (visible[:,0] < width)
                          & (visible[:,1] >= 0) & (visible[:,1] < height)]
        if len(visible) >= 2:
            continue
        torso = pose[[5,6,12,11]]
        if not np.isfinite(torso).all() or np.any(torso[:,2] < .75):
            continue
        xy = np.rint(torso[:,:2]).astype(np.int32)
        if (np.any(xy < 0) or np.any(xy[:,0] >= width) or np.any(xy[:,1] >= height)
                or len(np.unique(xy,axis=0)) != 4 or not cv2.isContourConvex(xy)):
            continue
        region = np.zeros(mask.shape,np.uint8)
        cv2.fillConvexPoly(region,xy,1)
        region = cv2.erode(region,np.ones((3,3),np.uint8)).astype(bool)
        if region.sum() >= 25 and mask[xy[:,1],xy[:,0]].all() and mask[region].mean() >= .9:
            owners.append(i)
    return tuple(owners),bool(owners)


def record_owners(mask, record):
    poses = record.person_pose_keypoints
    if len(poses) != len(record.person_bboxes):
        poses = []
    return pose_owners(mask,record.person_head_keypoints,poses)


def owned_mask_face(image, mask, detector):
    """Locate a unique face now, rather than transporting an old face box."""
    ys,xs = np.where(mask)
    if not len(xs):
        return None
    x,y,xx,yy = int(xs.min()),int(ys.min()),int(xs.max())+1,int(ys.max())+1
    sample = image[y:yy,x:xx]
    detector.setInputSize((sample.shape[1],sample.shape[0]))
    _,faces = detector.detect(sample)
    selected = []
    for face in [] if faces is None else faces:
        if len(face) != 15 or not np.isfinite(face).all() or face[-1] < .9:
            continue
        points = np.rint(face[4:14].reshape(5,2)+[x,y]).astype(int)
        if (np.any(points < 0) or np.any(points[:,0] >= mask.shape[1])
                or np.any(points[:,1] >= mask.shape[0]) or not mask[points[:,1],points[:,0]].all()):
            continue
        if face[2] <= 0 or face[3] <= 0:
            continue
        selected.append(tuple(map(float,(face[0]+x,face[1]+y,face[0]+x+face[2],face[1]+y+face[3]))))
    return selected[0] if len(selected) == 1 else None



class MaskTracker:
    def __init__(self, video_path, fps, *, model_path=None, on_progress=None, joint_faces=(), source_inventory=None):
        import torch
        import ultralytics
        from ultralytics.models.sam import SAM2VideoPredictor
        # Verify the exact published asset before the library loads its checkpoint.
        path = model_path or ensure_face_models(specs=(MODEL_SPEC,))[MODEL_SPEC.name]
        if not is_model_file_valid(path,MODEL_SPEC):
            raise ValueError('tracking_model_hash_mismatch')
        class MaskInput(SAM2VideoPredictor):
            def _prepare_prompts(self,*args,**kwargs):
                points,labels,masks = super()._prepare_prompts(*args,**kwargs)
                if masks is not None and masks.ndim == 3:
                    masks = masks[:,None]
                return points,labels,masks
            def get_im_features(self, im, batch=1):
                if batch != 1 or getattr(self,'source_frame',None) is None:
                    return super().get_im_features(im,batch=batch)
                return self.image_features.get(self.source_frame,im,
                    lambda:super(MaskInput,self).get_im_features(im,batch=batch))
        self.predictor = MaskInput(overrides=dict(conf=.25,task='segment',mode='predict',
            imgsz=512,model=str(path),device='cpu',save=False,verbose=False))
        self.predictor.setup_model(verbose=False)
        self.predictor.imgsz = [512,512]
        self.predictor.model.set_imgsz([512,512])
        self.predictor._bb_feat_sizes = [[128,128],[64,64],[32,32]]
        self.predictor.image_features = SamImageFeatures()
        self.source = str(video_path)
        self.fps = fps
        self.on_progress = on_progress
        self.joint_faces = joint_faces
        self.mask_cache = SamMasks()
        self.transition_cache = verified_transitions(source_inventory, video_path, fps)
        self.provenance = dict(name=MODEL_SPEC.name,sha256=MODEL_SPEC.sha256,image_size=512,
                               torch=torch.__version__,ultralytics=ultralytics.__version__,
                               ownership='head_or_bidirectional_torso_v1',torso_min_confidence=.75,
                               torso_min_mask_fraction=.9,torso_min_eroded_area=25)
        self.provenance['image_feature_cache_bytes'] = self.predictor.image_features.max_bytes
        self.provenance['device'] = str(self.predictor.device)
        self.provenance['reused_transition_frames'] = len(self.transition_cache)
        self.provenance['mask_cache'] = dict(hits=0, misses=0, max_bytes=self.mask_cache.max_bytes)

    def _masks(self, cap, records, **prompts):
        import torch
        predictor = self.predictor
        predictor.inference_state = {}
        predictor.dataset = SimpleNamespace(mode='video',frames=len(records),frame=0)
        predictor.init_state(predictor)
        frames = [round(record.t*self.fps) for record in records]
        images = source_frames(cap,frames,self._read)
        cached = self.mask_cache.get(frames, prompts)
        packed, retained = [], 0
        try:
            if cached is not None:
                for frame, image, mask in zip(frames, images, cached, strict=True):
                    yield frame, image, mask
                return
            with torch.inference_mode():
                for index,(frame,image) in enumerate(zip(frames,images,strict=True)):
                    predictor.source_frame = frame
                    predictor.dataset.frame = index
                    predictor.batch = ([self.source],[image],[''])
                    tensor = predictor.preprocess([image])
                    prediction = predictor.inference(tensor,**(prompts if index == 0 else {}))
                    result = predictor.postprocess(prediction,tensor,[image])[0]
                    mask = (result.masks.data[0].cpu().numpy().astype(bool)
                            if result.masks is not None and len(result.masks) == 1
                            else np.zeros(image.shape[:2],bool))
                    if retained <= self.mask_cache.max_bytes:
                        bits = np.packbits(mask)
                        retained += bits.nbytes
                        if retained <= self.mask_cache.max_bytes:
                            packed.append((mask.shape, bits))
                        else:
                            packed.clear()
                    yield frame,image,mask
        finally:
            if len(packed) == len(frames):
                self.mask_cache.put_packed(frames, prompts, packed)
            self.provenance['mask_cache'].update(hits=self.mask_cache.hits, misses=self.mask_cache.misses)
            images.close()
            predictor.source_frame = None
            predictor.inference_state = {}

    @staticmethod
    def _read(cap, frame):
        current = float(cap.get(cv2.CAP_PROP_POS_FRAMES))
        if 0 <= frame-current <= 12:
            for _ in range(round(frame-current)):
                if not cap.grab():
                    raise ValueError('source_frame_unavailable')
        elif not cap.set(cv2.CAP_PROP_POS_FRAMES,frame):
            raise ValueError('source_seek_failed')
        if abs(float(cap.get(cv2.CAP_PROP_POS_FRAMES))-frame) > .1:
            raise ValueError('source_position_mismatch')
        ok,image = cap.read()
        if not ok or abs(float(cap.get(cv2.CAP_PROP_POS_FRAMES))-(frame+1)) > .1:
            raise ValueError('source_frame_unavailable')
        return image

    def _cuts(self,cap,first,last):
        if not hasattr(self,'transition_cache'):
            self.transition_cache = {}
        previous,previous_frame = None,None
        for frame in range(first+1,last+1):
            if frame in self.transition_cache:
                continue
            if previous_frame != frame-1:
                previous = self._read(cap,frame-1)
            image = self._read(cap,frame)
            self.transition_cache[frame] = classify_transition(previous,image)
            previous,previous_frame = image,frame
        return {frame for frame in range(first+1,last+1) if self.transition_cache[frame]['cut']}

    def _identity_brackets(self, cuts, frames, anchor):
        from .member_timeline import _valid
        faces = [(name,row) for name,row in getattr(self,'joint_faces',())
                 if row.frame_index in frames and _valid(row) and row.detector_score >= .9 and row.face_bbox is not None]
        names = {name for name,row in faces if row.frame_index == anchor.frame_index}
        if len(names) != 1:
            return {}
        name = next(iter(names))
        brackets = {}
        for cut in cuts:
            if not getattr(self,'transition_cache',{}).get(cut,{}).get('structure',{}).get('continuous'):
                continue
            before = [row for n,row in faces if n == name and row.frame_index < cut]
            after = [row for n,row in faces if n == name and row.frame_index >= cut]
            if before and after:
                left,right = max(before,key=lambda r:r.frame_index),min(after,key=lambda r:r.frame_index)
                if (.15-1e-6 <= right.time_seconds-left.time_seconds <= .6+1e-6
                        and not any(n != name and left.frame_index <= row.frame_index <= right.frame_index for n,row in faces)):
                    brackets[cut] = (name,left,right)
        return brackets

    def _locate_mask_face(self, image, mask):
        if not hasattr(self,'face_detector'):
            from .face_models import FACE_MODEL_SPECS, read_model_buffer
            spec = next(s for s in FACE_MODEL_SPECS if s.name == 'opencv-yunet-face-detection')
            paths = ensure_face_models(specs=(spec,))
            self.face_detector = cv2.FaceDetectorYN.create('onnx',read_model_buffer(paths[spec.name]),
                np.empty(0,np.uint8),(320,320),.9,.3,5000)
            self.provenance['transition_face_detector_sha256'] = spec.sha256
        return owned_mask_face(image,mask,self.face_detector)

    def _link_cut_faces(self, old, new, old_mask, new_mask, old_frame, new_frame):
        if not hasattr(self,'cut_face_link'):
            from .cut_face_link import CutFaceLink
            self.cut_face_link = CutFaceLink()
            self.provenance['cut_face_link'] = self.cut_face_link.provenance
        return self.cut_face_link(old,new,old_mask,new_mask,old_frame,new_frame)

    def _link_sampled_heads(self, old, new):
        from .sampled_face_link import SampledFaceLink
        if abs(old[0]-new[0])/self.fps > .200001:
            return dict(accepted=False,reason='distant_head_samples')
        owners = [head_owners(sample[2],sample[3].person_head_keypoints) for sample in (old,new)]
        if any(len(values) != 1 for values in owners):
            return dict(accepted=False,reason='ambiguous_sampled_head')
        if not hasattr(self,'sampled_face_link'):
            self.sampled_face_link = SampledFaceLink()
            self.provenance['sampled_face_link'] = self.sampled_face_link.provenance
        return self.sampled_face_link(old,new,owners[0][0],owners[1][0])

    def __call__(self, anchor, records, target_frames):
        if not records or round(records[0].t*self.fps) != anchor.frame_index:
            return dict(accepted=False,reason='missing_anchor_frame')
        frames = [round(r.t*self.fps) for r in records]
        if (len(frames) != len(set(frames)) or not set(target_frames) <= set(frames)
                or any(abs(b.t-a.t) > .200001 for a,b in zip(records,records[1:]))):
            return dict(accepted=False,reason='missing_path_observation')
        original_frames = set(frames)
        owners = [i for i,b in enumerate(records[0].person_bboxes)
                  if bbox_iou(np.asarray(anchor.body_bbox),b) >= .7]
        if len(owners) != 1 or anchor.face_bbox is None:
            return dict(accepted=False,reason='unconfirmed_anchor_body')
        face = anchor.face_bbox
        points = [[(face[0]+face[2])/2,(face[1]+face[3])/2]]
        labels = [1]
        for i,h in enumerate(records[0].person_head_keypoints):
            h = np.asarray(h)
            if i == owners[0] or h.ndim != 2 or h.shape[1] != 3:
                continue
            h = h[np.isfinite(h).all(axis=1)&(h[:,2]>=.5),:2]
            if len(h) >= 2:
                points.append(h.mean(axis=0).tolist()); labels.append(0)
        cap = cv2.VideoCapture(self.source)
        if not cap.isOpened():
            cap.release()
            return dict(accepted=False,reason='source_unavailable')
        trace,packed,camera = [],{},[]
        try:
            if abs(float(cap.get(cv2.CAP_PROP_FPS))-self.fps) > .001:
                return dict(accepted=False,reason='source_fps_mismatch')
            cuts = self._cuts(cap,min(frames),max(frames))
            # Dense source pixels cannot fill a span with multiple unobserved
            # cuts and no intervening body observations.
            unobserved = {}
            for left,right in zip(frames,frames[1:]):
                low,high = sorted((left,right))
                transitions = sorted(c for c in cuts if low < c <= high)
                if len(transitions) > 1:
                    for cut in transitions:
                        unobserved[cut] = dict(from_frame=left,to_frame=right,cut_frames=transitions)
            brackets = self._identity_brackets(cuts,frames,anchor)
            if cuts:
                # Extra source instants provide pixels/masks, not invented pose
                # observations. Only original sampled targets can receive names.
                by_frame = dict(zip(frames,records,strict=True))
                for cut in cuts:
                    for frame in (cut-1,cut):
                        if frame not in by_frame:
                            nearest = min(records,key=lambda r:abs(round(r.t*self.fps)-frame))
                            by_frame[frame] = replace(nearest,t=frame/self.fps,main_id=None,main_bbox=None,
                                person_head_keypoints=[],person_pose_keypoints=[],scene_kind='group')
                frames = sorted(by_frame,reverse=frames[0]>frames[-1])
                records = [by_frame[f] for f in frames]
            identity_transitions = []
            previous = None
            previous_sample,pending = None,None
            forward = self._masks(cap,records,bboxes=[anchor.body_bbox],points=[points],labels=[labels])
            try:
                for record,(frame,image,mask) in zip(records,forward,strict=True):
                    owned,torso = record_owners(mask,record)
                    main = [i for i,b in enumerate(record.person_bboxes) if record.main_bbox is not None
                            and record.scene_kind != 'group' and bbox_iou(record.main_bbox,b) >= .7]
                    main = main[0] if len(main) == 1 else None
                    if frame in target_frames and (main is None or owned != (main,)):
                        return dict(accepted=False,reason='unconfirmed_main_ownership',frame=frame)
                    changed = False
                    if previous is not None:
                        old_frame,old_image,old_mask,old_record = previous
                        low,high = sorted((old_frame,frame))
                        transitions = sorted(c for c in cuts if low < c <= high)
                        if len(transitions) > 1:
                            return dict(accepted=False,reason='multiple_unobserved_camera_transitions',
                                        from_frame=old_frame,to_frame=frame,cut_frames=transitions)
                        changed = bool(transitions)
                        if changed:
                            cut = transitions[0]
                            if cut in unobserved:
                                return dict(accepted=False,reason='multiple_unobserved_camera_transitions',
                                            **unobserved[cut])
                            if cut in brackets:
                                name,left,right = brackets[cut]
                                if {old_frame,frame} != {cut-1,cut}:
                                    return dict(accepted=False,reason='missing_exact_transition_pair')
                                old_face = self._locate_mask_face(old_image,old_mask)
                                new_face = self._locate_mask_face(image,mask)
                                link = photometric_body_link(old_image,image,old_mask,mask,old_face,new_face)
                                link.update(old_face_bbox=old_face,new_face_bbox=new_face)
                                identity_transitions.append(dict(cut_frame=cut,name=name,
                                    support_frames=[left.frame_index,right.frame_index],foreground=link))
                            else:
                                link = self._link_cut_faces(old_image,image,old_mask,mask,old_frame,frame)
                            camera.append(dict(from_frame=old_frame,to_frame=frame,**link))
                            if not link['accepted']:
                                if permits_sampled_head_link(link) and previous_sample is not None:
                                    pending = (camera[-1],previous_sample)
                                else:
                                    return dict(accepted=False,reason='unconfirmed_camera_transition',camera=camera)
                    if frame in original_frames:
                        sample = (frame,image,mask,record)
                        if pending is not None:
                            entry,before = pending
                            proof = self._link_sampled_heads(before,sample)
                            if not proof['accepted']:
                                entry['sampled_head_rejection'] = proof
                                return dict(accepted=False,reason='unconfirmed_camera_transition',camera=camera)
                            rejected = {k:v for k,v in entry.items() if k not in ('from_frame','to_frame')}
                            entry.update(accepted=True,reason='sampled_face_correspondence',
                                exact_rejection=rejected,evidence_frames=[before[0],frame],sampled_faces=proof)
                            pending = None
                        previous_sample = sample
                    trace.append(TraceFrame(frame,record.t,main,owned,(),0.,changed,True,torso))
                    packed[frame] = np.packbits(mask)
                    previous = (frame,image,mask,record)
                    if self.on_progress and len(trace) % 8 == 0:
                        self.on_progress(len(trace),2*len(records))
            finally:
                forward.close()
            if pending is not None:
                return dict(accepted=False,reason='unconfirmed_camera_transition',camera=camera)
            endpoint = previous[2]
            backwards = self._masks(cap,list(reversed(records)),masks=endpoint[None].astype(np.uint8))
            indices = {t.frame_index:i for i,t in enumerate(trace)}
            try:
                for record,(frame,image,mask) in zip(reversed(records),backwards,strict=True):
                    original = np.unpackbits(packed.pop(frame),count=mask.size).reshape(mask.shape).astype(bool)
                    overlap = float(np.count_nonzero(mask&original)/max(1,np.count_nonzero(mask|original)))
                    i = indices[frame]
                    owned,torso = record_owners(mask,record)
                    trace[i] = replace(trace[i],reverse_owners=owned,cycle_iou=overlap,
                                       torso_fallback=trace[i].torso_fallback or torso)
                    # One failed cycle makes this entire path invalid. Keep the
                    # same verdict (and retry policy) without inferring its tail.
                    if not .5 <= overlap <= 1.:
                        break
                    if self.on_progress and len(packed) % 8 == 0:
                        self.on_progress(2*len(records)-len(packed),2*len(records))
            finally:
                backwards.close()
            verdict = evaluate_track(trace,anchor_owner=owners[0],target_frames=target_frames)
            if verdict['accepted'] and brackets:
                traces = {t.frame_index:t for t in trace}
                by_frame = dict(zip(frames,records,strict=True))
                for _,left,right in brackets.values():
                    for row in (left,right):
                        record,t = by_frame[row.frame_index],traces[row.frame_index]
                        owned = tuple(i for i,body in enumerate(record.person_bboxes) if bbox_iou(np.asarray(row.body_bbox),body) >= .7)
                        if len(owned) != 1 or t.forward_owners != owned or t.reverse_owners != owned:
                            verdict = dict(accepted=False,reason='unconfirmed_identity_bracket_body')
            return dict(verdict,camera=camera,identity_supported_transitions=identity_transitions,trace=[dict(frame=f.frame_index,forward=f.forward_owners,
                        reverse=f.reverse_owners,cycle_iou=f.cycle_iou,torso_fallback=f.torso_fallback) for f in trace])
        finally:
            cap.release()
