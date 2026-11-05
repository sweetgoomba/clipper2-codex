"""Coalesce confirmed Dance parts using their final eligible face evidence."""
from collections import ChainMap
from dataclasses import replace
import math
import numpy as np

from .member_timeline import MAX_SUPPORT_GAP_SECONDS, _assign_piece, _valid
from .observed_main import retained_bodies, strict_pose_corresponding

VERSION = 'final_named_continuity_v3_mask_edges'


def _bridge_mask_edges(output, *, handoffs, joint_matches, frame_records, fps, cut_frames, mask_refinement):
    """Extend original mask proof over an observed gap at its sampled edge.

    Both neighboring parts need their own frozen face seed and accepted mask
    path. An unknown body must connect uniquely to one of those paths in the
    same shot. Neither output labels nor newly recovered samples become seeds.
    """
    groups=[[i] for i in range(len(output['segments']))]
    if not (frame_records and fps and joint_matches and mask_refinement) or cut_frames is None or handoffs is None:
        return output,[],groups
    brackets=[]
    for h in handoffs:
        try:
            a,b=float(h['previous_time']),float(h['time'])
        except (KeyError,TypeError,ValueError):
            return output,[],groups
        if not math.isfinite(a) or not math.isfinite(b) or a>=b:
            return output,[],groups
        brackets.append((a,b))
    records={round(r.t*fps):r for r in frame_records}
    observations={o.frame_index:(o,n) for rows in output['evidence'] for o,n in rows}
    segments,decisions=output['segments'],output['decisions']
    cuts=sorted(set(cut_frames))

    def owns(value,index):
        # Native mask traces use tuples; diagnostic JSON uses lists.
        return (isinstance(value,(tuple,list)) and len(value)==1
                and isinstance(value[0],(int,np.integer)) and not isinstance(value[0],(bool,np.bool_))
                and value[0]==index)

    def body(frame):
        r=records.get(frame)
        if r is None or r.main_bbox is None or r.scene_kind!='main':return None,None
        boxes=[np.asarray(b) for b in r.person_bboxes]
        poses=[np.asarray(p) for p in r.person_pose_keypoints]
        if len(boxes)!=len(poses) or any(p.shape!=(17,3) for p in poses):return None,None
        features=[dict(index=i,pose_keypoints=poses[i]) for i in retained_bodies(boxes,poses)]
        selected=[f for f in features if np.allclose(boxes[f['index']],r.main_bbox,atol=1e-3,rtol=0)]
        return dict(features=features),selected[0] if len(selected)==1 else None

    def proof_for(frame,name):
        _,selected=body(frame)
        if selected is None:return None
        for candidate in mask_refinement.get('candidates',[]):
            for proof in candidate.get('attempts',[]):
                anchor=proof.get('anchor_frame');joint=joint_matches.get(anchor,{})
                row=observations.get(anchor,(None,None))[0]
                if (not proof.get('accepted') or proof.get('name')!=name
                        or proof.get('seed_kind') not in ('main_face','joint_face')
                        or frame not in proof.get('support_frames',()) or row is None or not _valid(row)
                        or row.detector_score<.9 or joint.get('status')!='accepted' or joint.get('name')!=name):continue
                trace={t['frame']:t for t in proof.get('trace',())}
                t=trace.get(frame,{});seed=trace.get(anchor,{})
                _,seed_body=body(anchor)
                if (seed_body is not None and np.allclose(row.body_bbox,records[anchor].main_bbox,atol=1e-3,rtol=0)
                        and all(owns(t.get(key),selected['index']) for key in ('forward','reverse'))
                        and all(owns(seed.get(key),seed_body['index']) for key in ('forward','reverse'))
                        and t.get('cycle_iou',0)>=.5 and seed.get('cycle_iou',0)>=.5):
                    return anchor
        return None

    def extension(frames):
        if any(a<cut<=b for a,b in zip(frames,frames[1:]) for cut in cuts):return False
        for a,b in zip(frames,frames[1:]):
            if not 0<records[b].t-records[a].t<=.200001:return False
            old,selected=body(a);new,target=body(b)
            found=strict_pose_corresponding(old,selected,new) if selected is not None and target is not None else None
            if found is None or found['index']!=target['index']:return False
        return True

    bridges=[];ranges=[];i=0
    while i<len(segments):
        if decisions[i].reference_id:i+=1;continue
        first=i
        while i+1<len(segments) and not decisions[i+1].reference_id:i+=1
        last=i;i+=1
        if first==0 or last+1==len(segments):continue
        left,right=first-1,last+1;name=decisions[left].reference_id
        if (not name or decisions[right].reference_id!=name
                or decisions[left].status!='matched' or decisions[right].status!='matched'
                or any(abs(segments[j].end-segments[j+1].start)>1e-6 for j in range(left,right))):continue
        start,end=segments[first].start,segments[last].end
        unknown=sorted(f for f,r in records.items() if start<=r.t<end)
        before=[f for f,r in records.items() if segments[left].start<=r.t<start]
        after=[f for f,r in records.items() if end<=r.t<segments[right].end]
        if not unknown or not before or not after:continue
        a,b=max(before),min(after)
        # Accepted competing paths may come from seeds outside our face
        # bracket. Their positive ownership is why the mask stage kept an
        # unknown, and cannot be erased by extending another accepted path.
        if any(proof.get('accepted') and proof.get('name') not in (None,name)
               and set(proof.get('support_frames',())).intersection([a,*unknown,b])
               for candidate in mask_refinement.get('candidates',())
               for proof in candidate.get('attempts',())):continue
        # A missing pose row cannot disappear from an otherwise valid path.
        expected={o.frame_index for j in range(first,last+1) for o,_ in output['evidence'][j]}
        if set(unknown)!=expected or any(body(f)[1] is None for f in unknown):continue
        if any(f not in observations or not np.allclose(observations[f][0].body_bbox,
               records[f].main_bbox,atol=1e-3,rtol=0) for f in unknown):continue
        left_seed,right_seed=proof_for(a,name),proof_for(b,name)
        if left_seed is None or right_seed is None or not left_seed<a<b<right_seed:continue
        lo,hi=records[left_seed].t,records[right_seed].t
        if any(lo<y and x<hi for x,y in brackets):continue
        if any(j.get('status')=='accepted' and j.get('name')!=name
               for f,j in joint_matches.items() if left_seed<=f<=right_seed):continue
        if any(n and n!=name for f,(o,n) in observations.items()
               if left_seed<=f<=right_seed and _valid(o)):continue
        # Weak faces contribute no identity votes. A plausible different best
        # result still prevents extending the body path into that sample.
        if any(joint_matches.get(f,{}).get('best',name)!=name
               and not (joint_matches[f].get('primary',0)>.6 and joint_matches[f].get('secondary',0)>.6)
               for f in unknown):continue
        extended=a if extension([a,*unknown]) else b if extension([*unknown,b]) else None
        if extended is None:continue
        bridges.append(dict(start=start,end=end,name=name,source_frames=unknown,
            seed_frames=[left_seed,right_seed],extended_from_frame=extended,
            source_indices=list(range(left,right+1)),reason='frozen_mask_pose_continuity'))
        if ranges and left<=ranges[-1][1]:ranges[-1]=(ranges[-1][0],right)
        else:ranges.append((left,right))
    if not bridges:return output,[],groups
    ends=dict(ranges);groups=[];i=0
    while i<len(segments):
        last=ends.get(i,i);groups.append(list(range(i,last+1)));i=last+1
    keys=('segments','decisions','labels','evidence','previews','preview_sources')
    result={key:[] for key in keys};accurate=[]
    for group in groups:
        first,last=group[0],group[-1]
        for key in keys:result[key].append(output[key][first])
        if any(j in output['accurate_indices'] for j in group):accurate.append(len(result['segments'])-1)
        if first==last:continue
        result['segments'][-1]=replace(segments[first],end=segments[last].end,
            bboxes=[box for j in group for box in segments[j].bboxes])
        result['decisions'][-1]=replace(decisions[first],reason='frozen_mask_pose_continuity')
        result['evidence'][-1]=[row for j in group for row in output['evidence'][j]]
        result['previews'][-1]=[image for j in group for image in output['previews'][j]][:5]
        result['preview_sources'][-1]=tuple(ChainMap(*(output['preview_sources'][j][k] for j in group)) for k in (0,1))
    return dict(output,**result,accurate_indices=accurate),bridges,groups


def _joint_supported_union(union, rows, boundary, name, joint_matches, brackets, matcher, anchors):
    """Recheck a primary view-change conflict using frozen dual face support.

    Only unnamed weak observations between independent agreeing faces can be
    omitted from this check. Original output evidence and names stay intact.
    A contrary named face anywhere in the accumulated union still vetoes it.
    """
    usable=[(row,primary_name,joint_matches.get(row.frame_index,{}))
            for row,primary_name in rows if _valid(row)]
    if any(primary_name and primary_name!=name
           or joint.get('status')=='accepted' and joint.get('name')!=name
           for _,primary_name,joint in usable):
        return None
    direct=[row for row,_,joint in usable
            if joint.get('status')=='accepted' and joint.get('name')==name]
    left=[row for row in direct if row.time_seconds<boundary]
    right=[row for row in direct if row.time_seconds>=boundary]
    if not left or not right:
        return None
    before,after=left[0].time_seconds,right[-1].time_seconds
    if after-before<.15 or any(before<b and a<after for a,b in brackets):
        return None
    bridged=[]
    for row,primary_name,joint in usable:
        if before<row.time_seconds<after:
            if (joint.get('status') not in ('accepted','insufficient','conflict')
                    or joint.get('best',joint.get('name'))!=name
                    and not (joint.get('primary',0)>.6 and joint.get('secondary',0)>.6)):
                return None
            if not primary_name and joint.get('status')!='accepted':
                bridged.append(row.frame_index)
    if not bridged:
        return None
    checked=_assign_piece(union,[(row,n) for row,n in rows if row.frame_index not in bridged],
                          matcher,anchors,'final-output-joint-union')
    return checked if checked.status=='matched' and checked.reference_id==name else None


def _empty_sampling_edge(segment, evidence, neighbor, records, brackets, *, prefix):
    """A projected slice between measured samples is not another face scope."""
    if evidence or segment.bboxes or not neighbor or not records:
        return False
    if any(segment.start<=r.t<segment.end for r in records):return False
    before=[r for r in records if r.t<segment.start]
    after=[r for r in records if r.t>=segment.end]
    if not before or not after or any(a<segment.end and segment.start<b for a,b in brackets):return False
    a,b=max(before,key=lambda r:r.t),min(after,key=lambda r:r.t)
    if not 0<b.t-a.t<=.200001:return False
    record,row=(b,neighbor[0]) if prefix else (a,neighbor[-1])
    return (abs(record.t-row.time_seconds)<=1e-6 and record.main_bbox is not None
            and np.allclose(record.main_bbox,row.body_bbox,atol=1e-3,rtol=0))


def _coalesce_named_pass(output, matcher, *, handoffs, joint_matches=None, frame_records=()):
    """Remove a stale boundary without adding a name, duration, or gallery seed.

    Inference scopes can include neighboring group scenes. Only the evidence
    already projected into final individual clips may justify this join.
    Every accumulated union must pass the existing identity consistency check.
    """
    audit = dict(version=VERSION, reason='complete', joins=[])
    if handoffs is None:
        audit['reason'] = 'main_handoff_audit_unavailable'
        return output, audit, []
    brackets = []
    for handoff in handoffs:
        try:
            before, after = float(handoff['previous_time']), float(handoff['time'])
        except (KeyError, TypeError, ValueError):
            audit['reason'] = 'invalid_main_handoff_audit'
            return output, audit, []
        if not math.isfinite(before) or not math.isfinite(after) or before >= after:
            audit['reason'] = 'invalid_main_handoff_audit'
            return output, audit, []
        brackets.append((before, after))

    keys = ('segments', 'decisions', 'labels', 'evidence', 'previews', 'preview_sources')
    result = {key: [] for key in keys}
    original_accurate = set(output['accurate_indices'])
    accurate, groups = [], []
    for index, values in enumerate(zip(*(output[key] for key in keys), strict=True)):
        segment, decision, _, evidence, _, sources = values
        joined = False
        if groups and decision.status == 'matched' and decision.reference_id:
            previous = result['segments'][-1]
            old = result['decisions'][-1]
            boundary = segment.start
            left = sorted((o for o, _ in result['evidence'][-1] if _valid(o)),
                          key=lambda o: o.time_seconds)
            right = sorted((o for o, _ in evidence if _valid(o)), key=lambda o: o.time_seconds)
            empty_edge=(_empty_sampling_edge(previous,result['evidence'][-1],right,frame_records,brackets,prefix=True)
                        or _empty_sampling_edge(segment,evidence,left,frame_records,brackets,prefix=False))
            if (old.status == 'matched' and old.reference_id == decision.reference_id
                    and abs(previous.end-boundary) <= 1e-6
                    and (empty_edge or left and right
                         and 0 < right[0].time_seconds-left[-1].time_seconds <= MAX_SUPPORT_GAP_SECONDS)
                    and not any(a < boundary <= b for a, b in brackets)):
                union = replace(previous, end=segment.end, bboxes=previous.bboxes+segment.bboxes)
                rows = result['evidence'][-1]+evidence
                pooled = _assign_piece(union, sorted(rows, key=lambda item: item[0].time_seconds),
                                       matcher, output['anchors'], 'final-output-union')
                join_reason='sample_boundary_fragment' if empty_edge else pooled.reason
                if pooled.reason=='inconsistent_face_scope' and joint_matches:
                    joint=_joint_supported_union(union,sorted(rows,key=lambda item:item[0].time_seconds),
                        boundary,decision.reference_id,joint_matches,brackets,matcher,output['anchors'])
                    if joint is not None:
                        pooled=joint
                        join_reason='frozen_joint_view_continuity'
                if pooled.status == 'matched' and pooled.reference_id == decision.reference_id:
                    thumbnails = ChainMap(result['preview_sources'][-1][0], sources[0])
                    owned = ChainMap(result['preview_sources'][-1][1], sources[1])
                    candidates = sorted((row for row, _ in rows), key=lambda row: row.quality, reverse=True)
                    images = [thumbnails.get(row.frame_index) or owned[row.frame_index]
                              for row in candidates if row.frame_index in thumbnails or row.frame_index in owned][:5]
                    result['segments'][-1] = union
                    result['evidence'][-1] = rows
                    result['preview_sources'][-1] = (thumbnails, owned)
                    result['previews'][-1] = images
                    groups[-1].append(index)
                    audit['joins'].append(dict(start=union.start, boundary=boundary, end=union.end,
                        reference_id=decision.reference_id, source_indices=list(groups[-1]),
                        reason=join_reason))
                    joined = True
        if not joined:
            for key, value in zip(keys, values, strict=True):
                result[key].append(value)
            groups.append([index])
        if index in original_accurate and len(groups)-1 not in accurate:
            accurate.append(len(groups)-1)
    return dict(output, **result, accurate_indices=accurate), audit, groups


def coalesce_named_output(output, matcher, *, handoffs, joint_matches=None, frame_records=(), fps=None,
                          cut_frames=None, mask_refinement=None):
    """Reconsider an earlier edge when a later join supplies original support."""
    output,bridges,sources=_bridge_mask_edges(output,handoffs=handoffs,joint_matches=joint_matches,
        frame_records=frame_records,fps=fps,cut_frames=cut_frames,mask_refinement=mask_refinement)
    joins=[]
    while True:
        result,audit,groups=_coalesce_named_pass(output,matcher,handoffs=handoffs,joint_matches=joint_matches,
                                              frame_records=frame_records)
        for join in audit['joins']:
            joins.append(dict(join,source_indices=[old for i in join['source_indices'] for old in sources[i]]))
        if not audit['joins']:
            return result,dict(audit,joins=joins,bridges=bridges)
        sources=[[old for i in group for old in sources[i]] for group in groups]
        output=result


def coalesce_unknown_output(output, frame_records, observations, joint_matches, *, fps,
                            sample_step, handoffs, video_path):
    """Join only a source-verified selected body; its identity stays unknown."""
    import cv2
    from .body_continuity import _check_source_chain
    from .member_timeline import _identity_boundaries
    audit = dict(version='unknown_selected_main_continuity_v1', candidates=[], joins=[])
    if handoffs is None or not observations or not math.isfinite(fps) or fps <= 0 or sample_step < 1:
        return output, audit
    records = {round(r.t*fps): r for r in frame_records}
    original = {o.frame_index: o for o in observations}
    joints = {int(f): m for f, m in joint_matches.items()}
    segments, decisions = output['segments'], output['decisions']
    groups, cap = [], None
    try:
        for i, (segment, decision) in enumerate(zip(segments, decisions, strict=True)):
            if not groups or decision.reference_id:
                groups.append([i])
                continue
            group = groups[-1]
            left = segments[group[0]]
            if decisions[group[-1]].reference_id or abs(segments[group[-1]].end-segment.start) > 1e-6:
                groups.append([i])
                continue
            lo, boundary, hi = left.start, segment.start, segment.end
            candidate = dict(start=lo, boundary=boundary, end=hi)
            audit['candidates'].append(candidate)
            frames = sorted(f for f, r in records.items() if lo <= r.t < hi)
            rows = [original[f] for f in frames if f in original]
            failure = None
            if (not rows or [o.frame_index for o in rows] != frames
                    or any(b-a != sample_step for a, b in zip(frames, frames[1:]))):
                failure = 'missing_original_observation'
            elif rows[0].time_seconds >= boundary or rows[-1].time_seconds < boundary:
                failure = 'missing_boundary_observation'
            elif any(lo < h['time'] < hi for h in handoffs):
                failure = 'main_handoff'
            elif any(records[o.frame_index].scene_kind != 'main'
                     or records[o.frame_index].main_bbox is None or o.body_bbox is None
                     or not np.allclose(o.body_bbox, records[o.frame_index].main_bbox, atol=1e-3, rtol=0)
                     for o in rows):
                failure = 'unowned_main_path'
            names = {n for j in [*group, i] for o, n in output['evidence'][j] if n and _valid(o)}
            names.update(joints[f]['name'] for f in frames if f in joints
                         and joints[f].get('status') == 'accepted' and joints[f].get('name'))
            if failure is None and len(names) > 1:
                failure = 'conflicting_original_names'
            if failure is None:
                # Unknown registered names do not erase a repeated change of
                # observed face identity, even when the body path looks alike.
                face_changes = [b for b in _identity_boundaries(
                    replace(left, end=hi), rows, [None]*len(rows), [])
                    if b['reason'] == 'repeated_face_change']
                if face_changes:
                    candidate['face_changes'] = face_changes
                    failure = 'repeated_original_face_change'
            if failure is None:
                if cap is None:
                    cap = cv2.VideoCapture(str(video_path))
                if not cap.isOpened() or abs(cap.get(cv2.CAP_PROP_FPS)-fps) > .01:
                    failure = 'source_unavailable_or_fps_mismatch'
                else:
                    failure = _check_source_chain(cap, rows, records, audit=candidate)
            candidate['reason'] = failure or 'same_unidentified_main'
            if failure:
                groups.append([i])
            else:
                group.append(i)
                audit['joins'].append(dict(candidate, source_indices=list(group)))
    finally:
        if cap is not None:
            cap.release()
    if not audit['joins']:
        return output, audit
    keys = ('segments', 'decisions', 'labels', 'evidence', 'previews', 'preview_sources')
    result = {**output, **{key: [] for key in keys}, 'accurate_indices': []}
    for group in groups:
        first, last = group[0], group[-1]
        for key in keys:
            result[key].append(output[key][first])
        if any(j in output['accurate_indices'] for j in group):
            result['accurate_indices'].append(len(result['segments'])-1)
        if first == last:
            continue
        result['segments'][-1] = replace(segments[first], end=segments[last].end,
            bboxes=[row for j in group for row in segments[j].bboxes])
        result['evidence'][-1] = [row for j in group for row in output['evidence'][j]]
        result['previews'][-1] = [image for j in group for image in output['previews'][j]][:5]
        result['preview_sources'][-1] = tuple(ChainMap(*(output['preview_sources'][j][k] for j in group)) for k in (0, 1))
    result['labels'] = [i+1 if d.reference_id else None for i, d in enumerate(result['decisions'])]
    return result, audit
