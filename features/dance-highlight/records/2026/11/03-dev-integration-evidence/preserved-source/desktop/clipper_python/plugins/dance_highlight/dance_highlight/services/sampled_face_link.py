"""Compare pose-owned face interiors across one observed camera transition.

No names are assigned here. Full body continuity is checked by MaskTracker.
"""
import cv2
import numpy as np

from .secondary_faces import _normalized


def sampled_face_match(primary, secondary, source, target):
    tables=[np.asarray(primary),np.asarray(secondary)]
    if (any(m.ndim!=2 or not np.isfinite(m).all() for m in tables)
            or tables[0].shape!=tables[1].shape
            or not 0<=source<tables[0].shape[0] or not 0<=target<tables[0].shape[1]):
        return dict(accepted=False,reason='incomplete_face_comparison')
    distances=[float(m[source,target]) for m in tables]
    margins=[]
    for m,d in zip(tables,distances,strict=True):
        competitors=[np.delete(m[source],target),np.delete(m[:,target],source)]
        margin=min((float(v.min())-d for v in competitors if len(v)),default=None)
        if margin is not None and margin<.08:
            return dict(accepted=False,reason='competing_or_ambiguous_sampled_face')
        margins.append(margin)
    accepted=max(distances)<=.6 and sum(distances)/2<=.5
    return dict(accepted=accepted,reason='mutual_sampled_faces' if accepted else 'weak_sampled_faces',
                distances=distances,margins=margins)

def _face_geometry(old, new, om, nm, of, nf):
    if of is None or nf is None:
        return None
    if old.shape != new.shape or om.shape != old.shape[:2] or nm.shape != new.shape[:2]:
        return None
    height, width = old.shape[:2]
    for mask, face in ((om, of), (nm, nf)):
        if (len(face) != 4 or not np.isfinite(face).all()
                or not 0 <= face[0] < face[2] <= width
                or not 0 <= face[1] < face[3] <= height):
            return None
        x, y = np.ceil(face[:2]).astype(int)
        xx, yy = np.floor(face[2:]).astype(int)
        interior = mask[y:yy, x:xx]
        if not interior.size or interior.mean() < .9:
            return None
    size = min(112, int(min(of[2]-of[0], of[3]-of[1], nf[2]-nf[0], nf[3]-nf[1])))
    return size if size >= 24 else None


def _head_patches(images, masks, size):
    patch = max(4, round(size / 7))
    stride = max(2, patch // 2)
    radius = max(1, round(size / 12))
    reports = []
    for a, b, am, bm in ((images[0], images[1], masks[0], masks[1]),
                          (images[1], images[0], masks[1], masks[0])):
        positions = []
        total = 0
        for y in range(0, size-patch+1, stride):
            for x in range(0, size-patch+1, stride):
                template = a[y:y+patch, x:x+patch]
                if am[y:y+patch, x:x+patch].mean() < .9 or template.std() < 4:
                    continue
                total += 1
                left, top = max(0, x-radius), max(0, y-radius)
                right, bottom = min(size, x+patch+radius), min(size, y+patch+radius)
                scores = cv2.matchTemplate(b[top:bottom, left:right], template, cv2.TM_CCOEFF_NORMED)
                coverage = cv2.matchTemplate(bm[top:bottom, left:right].astype(np.float32),
                    np.ones((patch, patch), np.float32), cv2.TM_CCORR) / (patch*patch)
                scores[coverage < .9] = -1
                if scores.max() >= .85:
                    positions.append((x, y))
        span = (np.ptp(np.asarray(positions), axis=0) + patch) / size if positions else np.zeros(2)
        reports.append(dict(matches=len(positions), eligible=total,
                            ratio=len(positions)/max(1, total), span=span.tolist()))
    accepted = all(r['matches'] >= 6 and r['ratio'] >= .6 and min(r['span']) >= .6 for r in reports)
    return dict(accepted=accepted, size=size, patch=patch, reports=reports)


def _warped_face(image, mask, face, matrix, size):
    # Neither background nor hair outside the detected face can supply evidence.
    interior = np.zeros(mask.shape, np.uint8)
    x, y = np.ceil(face[:2]).astype(int)
    xx, yy = np.floor(face[2:]).astype(int)
    interior[y:yy, x:xx] = mask[y:yy, x:xx]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float32)
    pixels = cv2.GaussianBlur(cv2.warpAffine(gray, matrix, (size, size)), (3, 3), 0)
    valid = cv2.erode(cv2.warpAffine(interior, matrix, (size, size), flags=cv2.INTER_NEAREST),
                      np.ones((3, 3), np.uint8))
    return pixels, valid


def normalized_head_link(old, new, om, nm, of, nf):
    size = _face_geometry(old, new, om, nm, of, nf)
    if size is None:
        return dict(accepted=False, reason='insufficient_face_support')
    views = []
    for image, mask, face in ((old, om, of), (new, nm, nf)):
        x, y, xx, yy = face
        matrix = np.float32([[size/(xx-x), 0, -x*size/(xx-x)], [0, size/(yy-y), -y*size/(yy-y)]])
        views.append(_warped_face(image, mask, face, matrix, size))
    return _head_patches([v[0] for v in views], [v[1] for v in views], size)


def landmark_head_link(old, new, om, nm, of, nf, op, np_):
    size = _face_geometry(old, new, om, nm, of, nf)
    if size is None:
        return dict(accepted=False, reason='insufficient_face_support')
    destination = np.float32([[.32, .38], [.68, .38], [.5, .75]])
    transforms = []
    for face, points in ((of, op), (nf, np_)):
        points = np.asarray(points, np.float32)
        if (points.shape != (5, 2) or not np.isfinite(points).all()
                or np.any(points < np.asarray(face[:2])) or np.any(points > np.asarray(face[2:]))):
            return dict(accepted=False, reason='invalid_face_landmarks')
        source = np.float32([points[0], points[1], (points[3]+points[4])/2])
        edges = source[1:] - source[0]
        if np.linalg.det(edges) <= 0 or np.linalg.norm(edges[0]) < 4:
            return dict(accepted=False, reason='degenerate_face_landmarks')
        matrix = cv2.getAffineTransform(source, destination)
        # The largest singular value bounds magnification in every direction.
        size = min(size, int(1. / np.linalg.svd(matrix[:, :2], compute_uv=False)[0]))
        transforms.append(matrix)
    if size < 24:
        return dict(accepted=False, reason='insufficient_native_pixels')
    views = [_warped_face(image, mask, face, matrix*size, size)
             for image, mask, face, matrix in zip((old, new), (om, nm), (of, nf), transforms, strict=True)]
    return _head_patches([v[0] for v in views], [v[1] for v in views], size)


class SampledFaceLink:
    def __init__(self):
        from .face_cluster import FaceClusterService
        from .config import DanceConfig
        from .face_models import SECONDARY_FACE_MODEL_SPEC,ensure_face_models
        from .opencv_acceleration import secondary_recognizer
        service=FaceClusterService(DanceConfig())
        self.detector,self.primary=service._detector,service._recognizer
        self.minimum_score=service.config.face_min_det_score
        spec=SECONDARY_FACE_MODEL_SPEC;path=ensure_face_models(specs=(spec,))[spec.name]
        self.secondary=secondary_recognizer(service, path)
        self.cache={}
        self.provenance=dict(version='observed_dual_face_pixels_v1',models=service.model_provenance,
            secondary_sha256=spec.sha256,detector_min_score=self.minimum_score,
            max_model_distance=.6,max_mean_distance=.5,min_margin=.08,
            min_native_face_pixels=24,max_normalized_size=112,min_ncc=.85,min_pixel_fraction=.6,min_face_mask_fraction=.9,min_matched_patch_count=6,min_matched_axis_span=.6,alignment='eyes_mouth_no_magnification')

    def _faces(self,image,frame):
        if frame in self.cache:return self.cache[frame]
        height,width=image.shape[:2];self.detector.setInputSize((width,height))
        _,detected=self.detector.detect(image);rows=[]
        for face in [] if detected is None else detected:
            if len(face)!=15 or not np.isfinite(face).all() or face[-1]<self.minimum_score:continue
            points=np.rint(face[4:14].reshape(5,2)).astype(int)
            box=np.r_[np.maximum(face[:2],0),np.minimum(face[:2]+face[2:4],[width,height])]
            if (min(box[2:]-box[:2])<8 or np.any(points<0)
                    or np.any(points[:,0]>=width) or np.any(points[:,1]>=height)):continue
            a=_normalized(self.primary.feature(self.primary.alignCrop(image,face)))
            b=_normalized(self.secondary.feature(self.secondary.alignCrop(image,face)))
            rows.append(dict(box=box,points=points,landmarks=face[4:14].reshape(5,2).copy(),primary=a,secondary=b))
        self.cache[frame]=rows
        return rows

    def __call__(self,old,new,old_owner,new_owner):
        from .face_evidence import select_pose_face
        before,after=self._faces(old[1],old[0]),self._faces(new[1],new[0])
        if not before or not after or any(r[k] is None for rows in (before,after) for r in rows for k in ('primary','secondary')):
            return dict(accepted=False,reason='incomplete_face_comparison')
        chosen=[]
        for sample,rows,owner in ((old,before,old_owner),(new,after,new_owner)):
            _,image,mask,record=sample
            owned=[i for i,r in enumerate(rows) if mask[r['points'][:,1],r['points'][:,0]].all()]
            index,_=select_pose_face([r['box'] for r in rows],record.person_bboxes[owner],record)
            if len(owned)!=1 or index!=owned[0]:
                return dict(accepted=False,reason='unconfirmed_sampled_face_ownership')
            chosen.append(index)
        matrices=[np.clip(1.-np.array([r[k] for r in before])@np.array([r[k] for r in after]).T,0.,2.) for k in ('primary','secondary')]
        identity=sampled_face_match(*matrices,*chosen)
        if not identity['accepted']:return identity
        pixels=landmark_head_link(old[1],new[1],old[2],new[2],before[chosen[0]]['box'],after[chosen[1]]['box'],before[chosen[0]]['landmarks'],after[chosen[1]]['landmarks'])
        return dict(accepted=pixels['accepted'],reason='observed_face_correspondence' if pixels['accepted'] else 'unconfirmed_face_pixels',
            identity=identity,head_pixels=pixels,source_face_count=len(before),target_face_count=len(after))
