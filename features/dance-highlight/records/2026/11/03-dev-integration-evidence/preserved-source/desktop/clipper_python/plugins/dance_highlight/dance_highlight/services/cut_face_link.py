"""Link exact source faces across a camera cut without assigning any name."""
import cv2
import numpy as np

from .camera_transitions import photometric_body_link
from .secondary_faces import _normalized


def mutual_face_match(primary, secondary, source, target):
    matrices = [np.asarray(primary), np.asarray(secondary)]
    if (any(m.ndim != 2 or not np.isfinite(m).all() for m in matrices)
            or matrices[0].shape != matrices[1].shape
            or not 0 <= source < matrices[0].shape[0]
            or not 0 <= target < matrices[0].shape[1]):
        return dict(accepted=False, reason='invalid_face_distances')
    margins = []
    for matrix in matrices:
        distance = float(matrix[source,target])
        if distance > .35:
            return dict(accepted=False, reason='weak_face_match')
        competitors = [np.delete(matrix[source],target),np.delete(matrix[:,target],source)]
        margin = min((float(v.min())-distance for v in competitors if len(v)),default=None)
        if margin is not None and margin < -1e-6:
            return dict(accepted=False, reason='competing_face')
        if margin is not None and margin < .08:
            return dict(accepted=False, reason='ambiguous_face')
        margins.append(margin)
    return dict(accepted=True, reason='mutual_dual_face_match',
                primary_distance=float(matrices[0][source,target]),
                secondary_distance=float(matrices[1][source,target]), margins=margins)


def weak_detection_recheck(primary, secondary, source, target, detector_scores):
    """Permit more evidence gathering, never accept an uncertain exact link.

    A weak selected pair must not conceal a strong different-person pairing
    in either model, including when mutual_face_match returned early.
    """
    identity = mutual_face_match(primary, secondary, source, target)
    if identity['reason'] != 'weak_face_match':
        return dict(eligible=False, reason='exact_identity_not_weak')
    scores = np.asarray(detector_scores, dtype=float)
    if (scores.shape != (2,) or not np.isfinite(scores).all()
            or np.any(scores < .28) or np.any(scores > 1.) or np.all(scores >= .9)):
        return dict(eligible=False, reason='no_uncertain_detection')
    distances, competitors = [], []
    for model, matrix in enumerate((np.asarray(primary), np.asarray(secondary))):
        distance = float(matrix[source, target])
        distances.append(distance)
        for axis, values in (('source_row', np.delete(matrix[source], target)),
                             ('target_column', np.delete(matrix[:, target], source))):
            if len(values):
                closest = float(values.min())
                # A weak first model must not hide a confident but ambiguous
                # or opposing result in the other model's comparison.
                if distance <= .35 and closest - distance < .08:
                    return dict(eligible=False, reason='conflicting_confident_model',
                                model=model, axis=axis, selected_distance=distance,
                                competitor_distance=closest)
                if closest <= .35 and distance - closest >= .08:
                    competitors.append(dict(model=model, axis=axis, distance=closest))
    return dict(eligible=not competitors,
                reason='strong_competing_face' if competitors else 'weak_low_confidence_owner',
                detector_scores=scores.tolist(), selected_distances=distances,
                strong_competitors=competitors)


def scaled_head_link(old, new, old_mask, new_mask, old_face, new_face):
    if old_face is None or new_face is None or old.shape != new.shape:
        return dict(accepted=False, reason='exact_face_unavailable')
    height,width = old.shape[:2]
    for face,mask in ((old_face,old_mask),(new_face,new_mask)):
        if (mask.shape != (height,width) or len(face) != 4 or not np.isfinite(face).all()
                or not 0 <= face[0] < face[2] <= width or not 0 <= face[1] < face[3] <= height
                or min(face[2]-face[0],face[3]-face[1]) < 8):
            return dict(accepted=False, reason='invalid_exact_face')
    # Keep enough existing pixels for multiple 12px head patches. A fixed
    # 640px full-frame resize erased small but resolved native faces. Never
    # upscale a tiny native face to manufacture texture for this proof.
    minimum_side = min(min(f[2]-f[0],f[3]-f[1]) for f in (old_face,new_face))
    analysis_width = min(width,max(640,int(np.ceil(24.*width/minimum_side))))
    reports = []
    for side,(source,target,sm,tm,sf,tf) in enumerate((
            (old,new,old_mask,new_mask,old_face,new_face),
            (new,old,new_mask,old_mask,new_face,old_face))):
        sf,tf = np.asarray(sf),np.asarray(tf)
        scale = (sf[2]-sf[0])/(tf[2]-tf[0])
        shift = sf[:2]-tf[:2]*scale
        matrix = np.array([[scale,0,shift[0]],[0,scale,shift[1]]],np.float32)
        warped = cv2.warpAffine(target,matrix,(width,height))
        mask = cv2.warpAffine(tm.astype(np.uint8),matrix,(width,height),flags=cv2.INTER_NEAREST).astype(bool)
        face = np.r_[tf[:2]*scale+shift,tf[2:]*scale+shift]
        proof = photometric_body_link(source,warped,sm,mask,sf,face,analysis_width=analysis_width)
        reports.extend(dict(r,scale_direction=side) for r in proof.get('regions',[]) if r['zone']=='head')
    accepted = len(reports)==4 and all(r['matches'] >= 2 and r['ratio'] >= .6 for r in reports)
    return dict(accepted=accepted,reason='scaled_head_pixels' if accepted else 'unconfirmed_head_pixels',
                analysis_width=analysis_width,regions=reports)


class CutFaceLink:
    def __init__(self, *, face_service=None):
        from .face_cluster import FaceClusterService
        from .config import DanceConfig
        from .face_models import SECONDARY_FACE_MODEL_SPEC,ensure_face_models,sha256_file
        from .opencv_acceleration import secondary_recognizer
        service = FaceClusterService(DanceConfig()) if face_service is None else face_service
        self.detector,self.primary = service._detector,service._recognizer
        self.minimum_score = service.config.face_min_det_score
        spec = SECONDARY_FACE_MODEL_SPEC
        path = ensure_face_models(specs=(spec,))[spec.name]
        self.secondary = secondary_recognizer(service, path)
        self.provenance = dict(version='exact_cut_dual_face_and_head_v4_weak_recheck',models=service.model_provenance,
                               secondary_sha256=sha256_file(path),max_model_distance=.35,min_margin=.08,
                               detector_min_score=self.minimum_score,head_min_ncc=.85,head_min_fraction=.6,
                               missing_face_rotations=[-30.,30.],duplicate_max_landmark_fraction=.15,
                               weak_owner_recheck_below=.9, strong_competitor_max_distance=.35,
                               strong_competitor_min_advantage=.08,head_target_short_side=24,
                               head_comparison_max_resolution='native')
        self.cache = {}

    def _faces(self, image, frame, rotation=0.):
        key = (frame,rotation)
        if key in self.cache:
            return self.cache[key]
        height,width = image.shape[:2]
        detected_image = image
        if rotation:
            matrix = cv2.getRotationMatrix2D((width/2.,height/2.),rotation,1.)
            detected_image = cv2.warpAffine(image,matrix,(width,height))
            inverse = cv2.invertAffineTransform(matrix)
        self.detector.setInputSize((width,height))
        _,detected = self.detector.detect(detected_image)
        rows = []
        for face in [] if detected is None else detected:
            # Preserve the detector's candidate inventory on both sides. A
            # second cutoff can erase a real owner OR a competing lookalike.
            # Acceptance still needs unique mask ownership, both face models,
            # bilateral margins, actual head pixels and the full body cycle.
            if len(face) != 15 or not np.isfinite(face).all() or face[-1] < self.minimum_score:
                continue
            if rotation:
                face = np.asarray(face,np.float32).copy()
                x,y,w,h = face[:4]
                corners = cv2.transform(np.array([[[x,y],[x+w,y],[x+w,y+h],[x,y+h]]]),inverse)[0]
                points = cv2.transform(face[4:14].reshape(1,5,2),inverse)[0]
                low,high = corners.min(axis=0),corners.max(axis=0)
                face[:4] = [*low,*(high-low)]
                face[4:14] = points.ravel()
            box = np.r_[face[:2],face[:2]+face[2:4]]
            points = np.rint(face[4:14].reshape(5,2)).astype(int)
            if (min(face[2:4]) < 8 or box[0]<0 or box[1]<0 or box[2]>width or box[3]>height
                    or np.any(points<0) or np.any(points[:,0]>=width) or np.any(points[:,1]>=height)):
                continue
            a = _normalized(self.primary.feature(self.primary.alignCrop(image,face)))
            b = _normalized(self.secondary.feature(self.secondary.alignCrop(image,face)))
            # Detection ownership and competitor inventory survive embedding failure.
            rows.append(dict(box=box,points=points,primary=a,secondary=b,rotation=rotation,
                             detector_score=float(face[-1])))
        self.cache[key] = rows
        return rows

    def _expanded_faces(self, image, frame, original):
        key = (frame,'expanded')
        if key in self.cache:
            return self.cache[key]
        rows = list(original)
        for rotation in (-30.,30.):
            for candidate in self._faces(image,frame,rotation=rotation):
                duplicates = []
                for i,row in enumerate(rows):
                    scale = min(row['box'][2]-row['box'][0],candidate['box'][2]-candidate['box'][0])
                    distances = np.linalg.norm(row['points']-candidate['points'],axis=1)
                    if scale > 0 and np.max(distances) <= .15*scale:
                        duplicates.append(i)
                # Retain original features, even failed features. A new view
                # cannot erase a competitor or resolve ambiguous geometry.
                if len(duplicates) != 1:
                    rows.append(candidate)
        self.cache[key] = rows
        return rows

    def __call__(self, old, new, old_mask, new_mask, old_frame, new_frame):
        if abs(new_frame-old_frame) != 1:
            return dict(accepted=False,reason='missing_exact_transition_pair')
        before,after = self._faces(old,old_frame),self._faces(new,new_frame)
        cache = getattr(self,'cache',{})
        before = cache.get((old_frame,'expanded'),before)
        after = cache.get((new_frame,'expanded'),after)
        owners = [[i for i,row in enumerate(rows) if mask[row['points'][:,1],row['points'][:,0]].all()]
                  for rows,mask in ((before,old_mask),(after,new_mask))]
        if all(len(v) <= 1 for v in owners) and any(not v for v in owners):
            before = self._expanded_faces(old,old_frame,before)
            after = self._expanded_faces(new,new_frame,after)
            owners = [[i for i,row in enumerate(rows) if mask[row['points'][:,1],row['points'][:,0]].all()]
                      for rows,mask in ((before,old_mask),(after,new_mask))]
        if any(row[key] is None for rows in (before,after) for row in rows for key in ('primary','secondary')):
            return dict(accepted=False,reason='incomplete_face_comparison')
        if any(len(v) != 1 for v in owners):
            return dict(accepted=False,reason='unconfirmed_unique_mask_face',owner_counts=list(map(len,owners)))
        source,target = owners[0][0],owners[1][0]
        tables = [np.clip(1.-np.array([r[key] for r in before])@np.array([r[key] for r in after]).T,0.,2.)
                  for key in ('primary','secondary')]
        identity = mutual_face_match(*tables,source,target)
        if not identity['accepted']:
            # Unique detected owners need no missing-face search. Previously
            # discovered rotated candidates above remain in this full table.
            recheck = weak_detection_recheck(*tables,source,target,
                [before[source].get('detector_score'),after[target].get('detector_score')])
            return dict(identity, sampled_recheck=recheck)
        pixels = scaled_head_link(old,new,old_mask,new_mask,before[source]['box'],after[target]['box'])
        return dict(accepted=pixels['accepted'],reason='exact_cut_face_correspondence' if pixels['accepted'] else pixels['reason'],
                    identity=identity,head_pixels=pixels,old_face_bbox=before[source]['box'].tolist(),
                    new_face_bbox=after[target]['box'].tolist(),source_face_count=len(before),target_face_count=len(after),
                    detection_rotations=[before[source].get('rotation',0.),after[target].get('rotation',0.)],
                    detector_scores=[before[source].get('detector_score'),after[target].get('detector_score')])
