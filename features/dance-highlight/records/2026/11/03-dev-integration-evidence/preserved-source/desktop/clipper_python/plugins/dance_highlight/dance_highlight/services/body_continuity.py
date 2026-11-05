"""Bridge a face gap only through a uniquely continuous selected main body.

Confirmed names on both sides are frozen inputs. A bridge never supplies face
matches, video anchors, or support for another bridge. Person Highlight does
not import this Dance-only stage.
"""
from collections import ChainMap
from dataclasses import replace
import cv2
import numpy as np

from .member_timeline import _valid
from .reference_matcher import SegmentReferenceDecision
from .track import bbox_iou

CONTINUITY_VERSION = 'main_body_face_gap_v2_observed_pose'


def _appearance(image, box):
    x,y,xx,yy = map(float,box)
    h,w = image.shape[:2]
    crop = image[max(0,int(y+.15*(yy-y))):min(h,int(y+.75*(yy-y))),
                 max(0,int(x+.2*(xx-x))):min(w,int(x+.8*(xx-x)))]
    if not crop.size:
        return np.zeros(160,np.float32)
    hsv = cv2.cvtColor(cv2.resize(crop,(32,48)),cv2.COLOR_BGR2HSV)
    parts = []
    for tile in (hsv[:24],hsv[24:]):
        for channels,bins,ranges in (([0,1],[8,8],[0,180,0,256]),([2],[16],[0,256])):
            value = cv2.calcHist([tile],channels,None,bins,ranges).reshape(-1)
            parts.append(value/(np.linalg.norm(value)+1e-9))
    value = np.concatenate(parts)
    return value/(np.linalg.norm(value)+1e-9)


def _color_cut(previous, current):
    # Same luminance/color guard used by the Person shot detector, kept local
    # because this plugin must run without Person being installed.
    luma = float(cv2.absdiff(cv2.cvtColor(previous,cv2.COLOR_BGR2GRAY),
                             cv2.cvtColor(current,cv2.COLOR_BGR2GRAY)).mean())
    if luma <= 10.:
        return False,luma
    def histogram(image):
        hsv = cv2.cvtColor(image,cv2.COLOR_BGR2HSV)
        value = cv2.calcHist([hsv],[0,1],None,[16,8],[0,180,0,256])
        return cv2.normalize(value,value)
    color = cv2.compareHist(histogram(previous),histogram(current),cv2.HISTCMP_BHATTACHARYYA)
    return ((luma > 45. and color > .27) or (luma > 20. and color > .28)
            or (luma > 10. and color > .5)),luma


def _unique_body_link(previous, current):
    old_boxes,old_views,a = previous
    boxes,views,b = current
    costs = np.full((len(old_boxes),len(boxes)),-2.)
    for i,old in enumerate(old_boxes):
        for j,new in enumerate(boxes):
            overlap = bbox_iou(old,new)
            similarity = float(old_views[i] @ views[j])
            if overlap >= .3 and similarity >= .8:
                costs[i,j] = .6*overlap+.4*similarity
    score = costs[a,b]
    competitors = [*np.delete(costs[a,:],b),*np.delete(costs[:,b],a)]
    return score >= 0. and (not competitors or score-max(competitors) >= .08)


def _unique_pose_link(previous, current, old_owner, owner):
    """Reuse measured heads/torso, with every competing body in both directions."""
    from .observed_main import strict_pose_corresponding
    contexts = []
    for record, selected in ((previous,old_owner),(current,owner)):
        poses = [np.asarray(p) for p in record.person_pose_keypoints]
        if (len(poses) != len(record.person_bboxes) or any(p.shape != (17,3) for p in poses)
                or record.main_bbox is None
                or not np.allclose(record.person_bboxes[selected],record.main_bbox,atol=.02,rtol=0)):
            return False
        contexts.append(dict(features=[dict(index=i,pose_keypoints=p) for i,p in enumerate(poses)]))
    # An occluded competitor is still a possible owner. The pose matcher gives
    # incomplete pairs infinite cost; do not let that manufacture uniqueness.
    for source, selected, target, target_selected in (
            (previous,old_owner,current,owner),(current,owner,previous,old_owner)):
        left = np.asarray(source.person_pose_keypoints[selected])
        for i,box in enumerate(target.person_bboxes):
            if i == target_selected or bbox_iou(source.person_bboxes[selected],box) <= 0.:
                continue
            right = np.asarray(target.person_pose_keypoints[i])
            valid = (np.isfinite(left).all(axis=1) & np.isfinite(right).all(axis=1)
                     & (left[:,2] >= .5) & (right[:,2] >= .5))
            if valid[:5].sum() < 2 or not valid[[5,6,11,12]].all():
                return False
            if min(np.linalg.norm(p[[5,6],:2].mean(axis=0)-p[[11,12],:2].mean(axis=0))
                   for p in (left,right)) < 4.:
                return False
    before,after = contexts
    found = strict_pose_corresponding(before,before['features'][old_owner],after)
    return found is not None and found['index'] == owner


def _check_source_chain(cap, rows, records, *, audit=None):
    """Read every source frame for cuts; compare every measured main pose."""
    frames = {row.frame_index:row for row in rows}
    if any(row.frame_index not in records for row in rows):
        return 'missing_pose_context'
    if any(b.time_seconds-a.time_seconds > .200001 for a,b in zip(rows,rows[1:])):
        return 'missing_main_observation'
    first,last = rows[0].frame_index,rows[-1].frame_index
    if (not cap.set(cv2.CAP_PROP_POS_FRAMES,first)
            or abs(float(cap.get(cv2.CAP_PROP_POS_FRAMES))-first) > .1):
        return 'source_seek_failed'
    previous_image,previous_body,previous_record = None,None,None
    differences = []
    for index in range(first,last+1):
        ok,image = cap.read()
        if not ok or abs(float(cap.get(cv2.CAP_PROP_POS_FRAMES))-(index+1)) > .1:
            return 'source_frame_unavailable'
        small = cv2.resize(image,(64,36))
        if previous_image is not None:
            cut,difference = _color_cut(previous_image,small)
            differences.append(difference)
            if cut:
                return 'visual_cut'
        previous_image = small
        if index not in frames:
            continue
        row,record = frames[index],records[index]
        boxes = record.person_bboxes
        owners = [i for i,box in enumerate(boxes) if bbox_iou(np.asarray(row.body_bbox),box) >= .7]
        if len(owners) != 1:
            return 'ambiguous_main_body'
        current = (boxes,[_appearance(image,box) for box in boxes],owners[0])
        if previous_body is not None and not _unique_body_link(previous_body,current):
            if not _unique_pose_link(previous_record,record,previous_body[2],owners[0]):
                return 'unconfirmed_body_continuity'
            if audit is not None:
                audit.setdefault('pose_link_frames',[]).append(index)
        previous_body = current
        previous_record = record
    # Similar stage colors can hide an editorial cut. Reject an isolated
    # structural jump, while repeated lighting flicker does not become a cut.
    limit = max(6.,3.*float(np.median(differences))) if differences else 6.
    jumps = [first+i+1 for i,difference in enumerate(differences) if difference > limit]
    if jumps:
        from .bounded_face_path import prove_source_face_paths
        proof = prove_source_face_paths(cap, rows, records, jumps)
        if audit is not None:
            audit['source_face_path'] = proof
        if not proof['accepted']:
            return 'isolated_visual_change'
    return None


def bridge_main_face_gaps(output, frame_records, video_path):
    audit = dict(version=CONTINUITY_VERSION,recovered_seconds=0.,bridges=[],candidates=[])
    candidates = []
    decisions,segments = output['decisions'],output['segments']
    i = 0
    while i < len(segments):
        if decisions[i].reference_id:
            i += 1
            continue
        first = i
        while i+1 < len(segments) and not decisions[i+1].reference_id:
            i += 1
        last = i
        i += 1
        if first == 0 or last+1 == len(segments):
            continue
        name = decisions[first-1].reference_id
        if name != decisions[last+1].reference_id or any(
                abs(segments[j].end-segments[j+1].start) > 1e-6 for j in range(first-1,last+1)):
            continue
        start,end = segments[first].start,segments[last].end
        left = [o for o,n in output['evidence'][first-1] if n == name and _valid(o)
                and start-.6 <= o.time_seconds < start]
        right = [o for o,n in output['evidence'][last+1] if n == name and _valid(o)
                 and end <= o.time_seconds <= end+.6]
        if not left or not right:
            continue
        a,b = max(left,key=lambda o:o.time_seconds),min(right,key=lambda o:o.time_seconds)
        evidence = sorted({o.frame_index:(o,n) for j in range(first-1,last+2)
                           for o,n in output['evidence'][j]
                           if a.time_seconds <= o.time_seconds <= b.time_seconds}.values(),
                          key=lambda item:item[0].time_seconds)
        candidate = dict(start=start,end=end,name=name,seed_frames=[a.frame_index,b.frame_index])
        audit['candidates'].append(candidate)
        if any(n and n != name for o,n in evidence if _valid(o)):
            candidate['reason'] = 'conflicting_face_name'
            continue
        alien = [o for o,_ in evidence if _valid(o)
                 and min(1.-float(o.embedding @ seed.embedding) for seed in (a,b)) > .65]
        if any(.15 <= y.time_seconds-x.time_seconds <= .6 and 1.-float(x.embedding @ y.embedding) <= .6
               for j,x in enumerate(alien) for y in alien[j+1:]):
            candidate['reason'] = 'conflicting_face_evidence'
            continue
        candidates.append((first,last,[o for o,_ in evidence],candidate))
    if not candidates:
        return output,audit
    cap = cv2.VideoCapture(str(video_path))
    groups = []
    try:
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.)
        records = {round(record.t*fps):record for record in frame_records}
        for first,last,rows,candidate in candidates:
            failure = _check_source_chain(cap,rows,records,audit=candidate) if cap.isOpened() else 'source_unavailable'
            candidate['reason'] = failure or 'confirmed_body_continuity'
            if failure:
                continue
            audit['bridges'].append(dict(candidate,source_frames=[row.frame_index for row in rows]))
            audit['recovered_seconds'] += candidate['end']-candidate['start']
            group = (first-1,last+1)
            if groups and group[0] <= groups[-1][1]:
                groups[-1] = (groups[-1][0],group[1])
            else:
                groups.append(group)
    finally:
        cap.release()
    if not groups:
        return output,audit
    keys = ('segments','decisions','labels','previews','evidence','preview_sources')
    merged = {**output,**{key:[] for key in keys},'accurate_indices':[]}
    ends = dict(groups)
    i = 0
    while i < len(segments):
        last = ends.get(i,i)
        indices = range(i,last+1)
        for key in keys:
            merged[key].append(output[key][i])
        if any(j in output['accurate_indices'] for j in indices):
            merged['accurate_indices'].append(len(merged['segments'])-1)
        if last != i:
            merged['segments'][-1] = replace(segments[i],end=segments[last].end,
                                             bboxes=[row for j in indices for row in segments[j].bboxes])
            merged['decisions'][-1] = SegmentReferenceDecision(decisions[i].reference_id,'matched','member_body_continuity')
            merged['evidence'][-1] = [row for j in indices for row in output['evidence'][j]]
            merged['previews'][-1] = [image for j in indices for image in output['previews'][j]][:5]
            merged['preview_sources'][-1] = tuple(ChainMap(*(output['preview_sources'][j][k] for j in indices)) for k in (0,1))
        i = last+1
    merged['labels'] = [i+1 if d.reference_id else None for i,d in enumerate(merged['decisions'])]
    return merged,audit
