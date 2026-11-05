"""Distinguish stage flashes from cuts using consecutive source-frame structure.

This is a camera-boundary check, never evidence of a person's identity. Mask
ownership and a full forward/reverse cycle are still required independently.
"""
import cv2
import numpy as np

from .body_continuity import _color_cut


def structural_continuity(old, new):
    if old.shape != new.shape:
        return dict(continuous=False, reason='source_size_changed')
    height, width = old.shape[:2]
    region = np.zeros((height, width), np.uint8)
    # Broadcast logos and subtitles can remain identical across actual cuts.
    region[int(.15*height):int(.8*height), int(.2*width):int(.8*width)] = 255
    sift = cv2.SIFT_create(nfeatures=4000, contrastThreshold=.015)
    features = []
    for image in (old, new):
        points, descriptors = sift.detectAndCompute(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), region)
        if descriptors is None or len(descriptors) < 2:
            return dict(continuous=False, reason='insufficient_structure')
        features.append((np.asarray([p.pt for p in points], np.float32), descriptors))
    (x, dx), (y, dy) = features
    matcher = cv2.BFMatcher()
    def matches(a, b):
        return {p[0].queryIdx: p[0].trainIdx for p in matcher.knnMatch(a, b, k=2)
                if len(p) == 2 and p[0].distance < .7*p[1].distance}
    forward, reverse = matches(dx, dy), matches(dy, dx)
    pairs = [(i, j) for i, j in forward.items() if reverse.get(j) == i]
    if len(pairs) < 30:
        return dict(continuous=False, reason='insufficient_correspondence', matches=len(pairs))
    source = np.asarray([x[i] for i, _ in pairs])
    target = np.asarray([y[j] for _, j in pairs])
    matrix, mask = cv2.estimateAffinePartial2D(source, target, method=cv2.RANSAC, ransacReprojThreshold=3.)
    if matrix is None or mask is None:
        return dict(continuous=False, reason='no_structure_transform')
    good = mask.ravel().astype(bool)
    points = source[good]
    quadrants = {(int(x >= width/2), int(y >= height/2)) for x, y in points}
    flow = float(np.quantile(np.linalg.norm(points-target[good], axis=1), .9)) if len(points) else None
    continuous = len(points) >= 30 and good.mean() >= .6 and len(quadrants) >= 3 and flow <= .02*min(height, width)
    return dict(continuous=bool(continuous), inliers=len(points), matches=len(pairs),
                ratio=float(good.mean()), quadrants=len(quadrants), p90_flow=flow)


def classify_transition(old, new, *, include_structure=True):
    raw = bool(_color_cut(cv2.resize(old, (64, 36)), cv2.resize(new, (64, 36)))[0])
    if not raw:
        return dict(cut=False, color_candidate=False)
    if not include_structure:
        return dict(cut=True, color_candidate=True, structure_deferred=True)
    try:
        proof = structural_continuity(old, new)
    except (ValueError, RuntimeError, cv2.error) as error:
        return dict(cut=True, color_candidate=True, reason='structure_unavailable', error_type=type(error).__name__)
    # Stable background geometry is only a proposal. The raw boundary remains
    # until a particular tracked person's exact source pair is also verified.
    return dict(cut=True, color_candidate=True, structure=proof)


def photometric_body_link(old, new, old_mask, new_mask, old_face_bbox, new_face_bbox, *, analysis_width=640):
    """Require textured head AND torso correspondence in both eroded masks."""
    if old_face_bbox is None or new_face_bbox is None:
        return dict(accepted=False,reason='exact_face_unavailable')
    height,width = old.shape[:2]
    analysis_width = int(analysis_width)
    scale = analysis_width/width
    shape = (analysis_width,round(height*scale))
    images = [cv2.GaussianBlur(cv2.cvtColor(cv2.resize(im,shape),cv2.COLOR_BGR2GRAY).astype(np.float32),(3,3),0)
              for im in (old,new)]
    masks = [cv2.erode(cv2.resize(m.astype(np.uint8),shape,interpolation=cv2.INTER_NEAREST),np.ones((3,3),np.uint8))
             for m in (old_mask,new_mask)]
    regions = []
    for face_bbox in (old_face_bbox,new_face_bbox):
        x,y,xx,yy = np.asarray(face_bbox)*scale
        fw,fh,center = xx-x,yy-y,(x+xx)/2
        regions.append([(x,y,xx,yy),(center-fw,yy+.15*fh,center+fw,yy+2.5*fh)])
    patch,radius = 12,max(1,round(.02*min(shape)))
    reports = []
    for direction in (0,1):
        source,target = images[direction],images[1-direction]
        source_mask,target_mask = masks[direction],masks[1-direction]
        for zone,region,target_region in zip(('head','torso'),regions[direction],regions[1-direction],strict=True):
            x,y,xx,yy = map(int,region)
            tx,ty,txx,tyy = map(int,target_region)
            dx,dy = round((tx+txx-x-xx)/2),round((ty+tyy-y-yy)/2)
            good,total = 0,0
            for cy in range(max(patch//2,y+patch//2),min(shape[1]-patch//2,yy-patch//2+1),patch//2):
                for cx in range(max(patch//2,x+patch//2),min(shape[0]-patch//2,xx-patch//2+1),patch//2):
                    left,top = cx-patch//2,cy-patch//2
                    template = source[top:top+patch,left:left+patch]
                    if source_mask[top:top+patch,left:left+patch].mean() < .9 or template.std() < 4:
                        continue
                    a,b = max(0,tx,left+dx-radius),max(0,ty,top+dy-radius)
                    aa,bb = min(shape[0],txx,left+dx+patch+radius),min(shape[1],tyy,top+dy+patch+radius)
                    total += 1
                    if aa-a < patch or bb-b < patch:
                        continue
                    scores = cv2.matchTemplate(target[b:bb,a:aa],template,cv2.TM_CCOEFF_NORMED)
                    coverage = cv2.matchTemplate(target_mask[b:bb,a:aa].astype(np.float32),np.ones((patch,patch),np.float32),cv2.TM_CCORR)/(patch*patch)
                    scores[coverage < .9] = -1
                    good += int(float(scores.max()) >= .85)
            reports.append(dict(direction=direction,zone=zone,matches=good,eligible=total,
                                ratio=good/max(1,total)))
    accepted = all(r['matches'] >= (2 if r['zone']=='head' else 6) and r['ratio'] >= .6 for r in reports)
    return dict(accepted=accepted,reason='masked_head_and_torso' if accepted else 'unconfirmed_foreground',regions=reports)


def scan_source_transitions(video_path, fps, last_frame):
    cap = cv2.VideoCapture(str(video_path))
    transitions = {}
    try:
        if not cap.isOpened():
            return {},'source_unavailable'
        if abs(float(cap.get(cv2.CAP_PROP_FPS))-fps) > .001:
            return {},'source_fps_mismatch'
        previous = None
        for frame in range(last_frame+1):
            ok,image = cap.read()
            if not ok:
                return {},'incomplete_source_decode'
            if previous is not None:
                transitions[frame] = classify_transition(previous,image)
            previous = image
    except (OSError,RuntimeError,ValueError,cv2.error):
        return {},'source_decode_failed'
    finally:
        cap.release()
    return transitions,'complete'
