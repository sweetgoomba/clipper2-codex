"""Dance-only identity continuity from frozen, directly recognized faces.

Masks describe a visual path, never an identity gallery. Recovered names cannot
become seeds for another recovery, and group observations cannot receive names.
"""
from dataclasses import dataclass
import math
import time

VERSION = 'frozen_face_mask_continuity_v11_joint_context'


@dataclass(frozen=True)
class TraceFrame:
    frame_index: int
    time_seconds: float
    main_owner: int | None
    forward_owners: tuple[int, ...]
    reverse_owners: tuple[int, ...]
    cycle_iou: float
    cut_from_previous: bool = False
    cut_supported: bool = True
    torso_fallback: bool = False


def evaluate_track(frames, *, anchor_owner, target_frames):
    """Require agreement throughout the path, including before the target part."""
    def reject(reason):
        return dict(accepted=False, reason=reason)
    targets = set(target_frames)
    by_frame = {f.frame_index: f for f in frames}
    if not frames or len(by_frame) != len(frames) or not targets or not targets <= by_frame.keys():
        return reject('missing_path_observation')
    if any(not math.isfinite(f.time_seconds) for f in frames):
        return reject('invalid_source_time')
    delta = [b.time_seconds-a.time_seconds for a,b in zip(frames,frames[1:])]
    if delta and (any(abs(d) > .200001 or d == 0 for d in delta)
                  or not (all(d > 0 for d in delta) or all(d < 0 for d in delta))):
        return reject('missing_path_observation')
    if any(not math.isfinite(f.cycle_iou) or not .5 <= f.cycle_iou <= 1. for f in frames):
        return reject('inconsistent_visual_path')
    if any(f.cut_from_previous and not f.cut_supported for f in frames):
        return reject('unconfirmed_camera_transition')
    first = frames[0]
    if first.forward_owners != (anchor_owner,) or first.reverse_owners != (anchor_owner,):
        return reject('unconfirmed_anchor_body')
    for f in frames:
        if f.torso_fallback and (len(f.forward_owners) != 1 or f.reverse_owners != f.forward_owners):
            return reject('unconfirmed_torso_ownership')
        # Reverse head points may be occluded, but cannot land on a different
        # body even in the interval between the anchor and target.
        if (f.reverse_owners and
                (f.forward_owners or (f.main_owner,)) != f.reverse_owners):
            return reject('conflicting_reverse_body')
        if f.frame_index in targets and (f.main_owner is None
                or f.forward_owners != (f.main_owner,)
                or f.reverse_owners not in ((), (f.main_owner,))):
            return reject('unconfirmed_main_ownership')
    times = [by_frame[i].time_seconds for i in targets]
    if max(times)-min(times) < .15-1e-6:
        return reject('insufficient_target_support')
    return dict(accepted=True, reason='confirmed_visual_path', support_frames=sorted(targets),
                minimum_cycle_iou=min(f.cycle_iou for f in frames))


def _continuation_validation_frames(index, segments, decisions, name, anchor,
                                    path, targets, fps, cuts):
    """Validate a short tail with its immediate original main, on the same path.

    These extra samples are verification only. The unknown claim stays fixed,
    and a neighboring output label can never replace a frozen face seed.
    """
    if (max(targets) - min(targets)) / fps >= .15 - 1e-6:
        return None
    forward = anchor.frame_index < min(targets)
    neighbor = index - 1 if forward else index + 1
    if not 0 <= neighbor < len(segments):
        return None
    left, right = sorted((index, neighbor))
    decision = decisions[neighbor]
    if (abs(segments[left].end - segments[right].start) > 1e-6
            or decision.reference_id != name
            or decision.reason != 'member_timeline_consensus'):
        return None
    scope = segments[neighbor]
    extras = sorted((r for r in path if (round(r.t * fps) < min(targets) if forward
                                        else round(r.t * fps) > max(targets))),
                    key=lambda r: r.t, reverse=forward)
    verification = list(targets)
    nearest = min(targets) if forward else max(targets)
    for record in extras:
        frame = round(record.t * fps)
        if (not scope.start <= record.t < scope.end or record.main_bbox is None
                or record.scene_kind == 'group' or abs(frame - nearest) / fps > .200001):
            return None
        verification.append(frame)
        if any(min(verification) < cut <= max(verification) for cut in cuts):
            return None
        if (max(verification) - min(verification)) / fps >= .15 - 1e-6:
            return sorted(verification)
        nearest = frame
    return None


def recover_mask_names(output, frame_records, video_path, fps, video_anchors, *,
                       verify_track=None, on_progress=None, context_anchors=(), cut_frames=(),
                       joint_matches=None, source_inventory=None):
    """Name verified portions of unknowns; keep the input evidence immutable."""
    from collections import ChainMap
    from dataclasses import replace
    from itertools import groupby
    from bisect import bisect_right
    from .main_identity import split_segment
    from .member_timeline import _valid
    from .reference_matcher import SegmentReferenceDecision
    from .track import bbox_iou
    import numpy as np

    audit = dict(version=VERSION, recovered_seconds=0., candidates=[])
    if cut_frames is None:
        return output,dict(audit,reason='source_cut_inventory_unavailable')
    segments, decisions = output['segments'], output['decisions']
    rows = {o.frame_index:o for evidence in output['evidence'] for o,_ in evidence}
    seeds = [(a['name'],rows[a['frame_index']]) for a in video_anchors
             if a['frame_index'] in rows and _valid(rows[a['frame_index']])
             and rows[a['frame_index']].detector_score >= .9]
    seeds = [(name,o) for name,o in seeds if any(n == name and
             .15-1e-6 <= abs(o.time_seconds-r.time_seconds) <= .6+1e-6 for n,r in seeds)]
    seed_kinds = {(name,o.frame_index):'main_face' for name,o in seeds}
    cuts = sorted(set(cut_frames))
    # These matches were computed from original observations and the frozen
    # photo-confirmed galleries before any body recovery. A recovered clip
    # name, window match or tracking result can never enter this seed pool.
    joint_evidence = [(m['name'],rows[f]) for f,m in (joint_matches or {}).items()
             if f in rows and m.get('status') == 'accepted' and m.get('name')
             and _valid(rows[f])]
    # A single original contrary face is still a conflict even when it cannot
    # provide the repeated support required to start another tracking path.
    conflict_seeds = [*seeds,*joint_evidence]
    joint = [(name,row) for name,row in joint_evidence if row.detector_score >= .9]
    joint = [(name,o) for name,o in joint if any(n == name and
             .15-1e-6 <= abs(o.time_seconds-r.time_seconds) <= .6+1e-6 and
             bisect_right(cuts,o.frame_index) == bisect_right(cuts,r.frame_index)
             for n,r in joint)]
    for name,row in joint:
        key = (name,row.frame_index)
        if key not in seed_kinds:
            seeds.append((name,row))
            seed_kinds[key] = 'joint_face'
    audit['joint_seed_count'] = sum(kind == 'joint_face' for kind in seed_kinds.values())
    recovered = {}
    verifier = verify_track
    records_by_frame = {round(r.t*fps):r for r in frame_records}
    for i,(seg,decision) in enumerate(zip(segments,decisions,strict=True)):
        if decision.reference_id:
            continue
        targets = sorted(round(r.t*fps) for r in frame_records if seg.start <= r.t < seg.end)
        if not targets:
            continue
        # Neither a full path nor a partial retry can name a group-only target.
        # Keep mixed paths: their main portion may still have valid support.
        if all(records_by_frame[f].scene_kind == 'group' or
               records_by_frame[f].main_bbox is None for f in targets):
            audit['candidates'].append(dict(start=seg.start,end=seg.end,attempts=[],
                                             reason='no_main_targets'))
            continue
        attempts = []
        for step in (-1,1):
            j = i
            nearby_name = None
            while 0 <= j+step < len(segments):
                k = j+step
                left,right = sorted((j,k))
                if abs(segments[left].end-segments[right].start) > 1e-6:
                    break
                j = k
                name = decisions[j].reference_id
                if not name:
                    continue
                if nearby_name is not None and name != nearby_name:
                    break
                nearby_name = name
                local = [o for n,o in seeds if n == name and
                         segments[j].start <= o.time_seconds < segments[j].end]
                if local:
                    anchor = (max if step == -1 else min)(local,key=lambda o:o.time_seconds)
                    attempts.append((name,anchor,targets,False))
                    break
        # A face may be recognizable while another member is main. Its name
        # can reach only this existing main's verified samples in the same
        # detected shot; other main bodies along the path are not its identity.
        for shot in {bisect_right(cuts,f) for f in targets}:
            local_targets = [f for f in targets if bisect_right(cuts,f) == shot]
            by_name = {}
            for name,anchor in context_anchors:
                if (_valid(anchor) and anchor.detector_score >= .9
                        and bisect_right(cuts,anchor.frame_index) == shot):
                    by_name.setdefault(name,[]).append(anchor)
            for name,rows_for_name in sorted(by_name.items()):
                anchor = min(rows_for_name,key=lambda o:min(abs(o.frame_index-f) for f in local_targets))
                for direction in (-1,1):
                    subset = [f for f in local_targets if (f-anchor.frame_index)*direction > 0]
                    if subset and (max(subset)-min(subset))/fps >= .15-1e-6:
                        attempts.append((name,anchor,subset,True))
        # A directly recognized main may later become a supporting performer.
        # Its original joint face remains a valid same-shot body seed even
        # when another named main prevents the neighboring-segment search.
        def attempt_key(name, anchor, frames):
            return (name, anchor.frame_index, tuple(anchor.body_bbox),
                    None if anchor.face_bbox is None else tuple(anchor.face_bbox), tuple(frames))
        existing = {attempt_key(n,a,fs) for n,a,fs,_ in attempts}
        extra_context = set()
        for shot in {bisect_right(cuts,f) for f in targets}:
            local_targets = [f for f in targets if bisect_right(cuts,f) == shot]
            for name in sorted({n for n,o in joint if bisect_right(cuts,o.frame_index) == shot}):
                local = [o for n,o in joint if n == name and bisect_right(cuts,o.frame_index) == shot]
                anchor = min(local,key=lambda o:min(abs(o.frame_index-f) for f in local_targets))
                for direction in (-1,1):
                    subset = [f for f in local_targets if (f-anchor.frame_index)*direction > 0]
                    key = attempt_key(name,anchor,subset)
                    if (subset and (max(subset)-min(subset))/fps >= .15-1e-6
                            and key not in existing):
                        attempts.append((name,anchor,subset,True))
                        extra_context.add(key)
                        existing.add(key)
        if not attempts:
            continue
        candidate = dict(start=seg.start,end=seg.end,attempts=[],reason='unconfirmed_visual_path')
        audit['candidates'].append(candidate)
        claims = {frame:set() for frame in targets}
        claim_limits = {frame:{} for frame in targets}
        continuous_claims = set()
        original_proven_frames = None
        for name,anchor,attempt_targets,is_context in attempts:
            joint_context = attempt_key(name,anchor,attempt_targets) in extra_context
            if joint_context:
                if original_proven_frames is None:
                    # Only the completed original attempts can skip new work.
                    # Competing new contexts must all run, regardless of order.
                    original_proven_frames = {f for f,names in claims.items() if len(names) == 1}
                if all(f in original_proven_frames for f in attempt_targets):
                    continue
            low,high = min(anchor.frame_index,min(attempt_targets)),max(anchor.frame_index,max(attempt_targets))
            path = [r for r in frame_records if low <= round(r.t*fps) <= high]
            if anchor.frame_index > max(attempt_targets):
                path.reverse()
            path_conflicts = [dict(name=n,frame_index=o.frame_index) for n,o in conflict_seeds
                              if n != name and low <= o.frame_index <= high]
            conflicts = [c for c in path_conflicts if c['frame_index'] in attempt_targets]
            if conflicts:
                candidate['attempts'].append(dict(name=name,anchor_frame=anchor.frame_index,
                    accepted=False,reason='conflicting_direct_face_anchor',conflicts=conflicts))
                continue
            if verifier is None:
                try:
                    from .mask_tracker import MaskTracker
                    verifier = MaskTracker(video_path,fps,source_inventory=source_inventory,on_progress=(
                        lambda done,total:on_progress(i+done/max(1,total),len(segments)))
                        if on_progress else None)
                    audit['model'] = verifier.provenance
                except Exception as exc:
                    audit['reason'] = 'tracking_unavailable'
                    audit['error'] = type(exc).__name__
                    return output,audit
            started = time.monotonic()
            try:
                proof = verifier(anchor,path,attempt_targets)
                if not is_context and proof.get('reason') == 'insufficient_target_support' and not proof['accepted']:
                    raw_cuts = set(cuts) | {f for f,d in getattr(verifier,'transition_cache',{}).items() if d.get('cut')}
                    verification = _continuation_validation_frames(
                        i, segments, decisions, name, anchor, path, attempt_targets, fps, raw_cuts)
                    if verification:
                        retry = verifier(anchor,path,verification)
                        raw_cuts |= {f for f,d in getattr(verifier,'transition_cache',{}).items() if d.get('cut')}
                        complete = (set(verification) <= set(retry.get('support_frames',()))
                                    and not any(min(verification) < c <= max(verification) for c in raw_cuts))
                        if retry['accepted'] and complete:
                            proof = dict(retry,support_frames=list(attempt_targets),
                                         verification_frames=verification,whole_path_rejection=proof)
                            continuous_claims.add((name,tuple(attempt_targets)))
                        else:
                            proof = dict(proof,continuous_support_retry=retry)
                # Recheck the prefix before the first body or cut failure in
                # BOTH directions. A failed whole-path mask is never proof.
                stop = None
                forward = anchor.frame_index < attempt_targets[0]
                if not proof['accepted']:
                    if proof['reason'] == 'unconfirmed_main_ownership':
                        stop = proof.get('frame') if proof.get('frame') in attempt_targets else None
                    elif proof['reason'] == 'unconfirmed_camera_transition':
                        failed = [c for c in proof.get('camera',[]) if not c.get('accepted')]
                        stop = failed[0].get('to_frame') if failed else None
                    elif proof['reason'] == 'multiple_unobserved_camera_transitions' and proof.get('cut_frames'):
                        stop = min(proof['cut_frames']) if forward else max(proof['cut_frames'])-1
                if stop is not None:
                    partial = [f for f in attempt_targets if (f < stop if forward else f > stop)]
                    if partial and (max(partial)-min(partial))/fps >= .15-1e-6:
                        lo,hi = min(anchor.frame_index,min(partial)),max(anchor.frame_index,max(partial))
                        retry = verifier(anchor,[r for r in path if lo <= round(r.t*fps) <= hi],partial)
                        proof = (dict(retry,support_frames=sorted(set(retry.get('support_frames',partial)) & set(partial)),
                                      whole_path_rejection=proof) if retry['accepted']
                                 else dict(proof,partial_retry=retry))
            except Exception as exc:
                proof = dict(accepted=False,reason='tracking_failed',error=type(exc).__name__)
            if proof['accepted'] and (is_context or path_conflicts):
                # Another member may be main between seed and target. Reject
                # only if the tracked body itself has a different direct name.
                trace = {t['frame']:t for t in proof.get('trace',[])}
                conflicts = []
                verified_other_bodies = []
                support = [anchor.frame_index,*proof.get('support_frames',attempt_targets)]
                verified_low,verified_high = min(support),max(support)
                for other_name,row in [*conflict_seeds,*context_anchors]:
                    if other_name == name or not verified_low <= row.frame_index <= verified_high:
                        continue
                    t = trace.get(row.frame_index)
                    if t is None:
                        conflicts.append(dict(name=other_name,frame_index=row.frame_index))
                        continue
                    record = records_by_frame.get(row.frame_index)
                    owners = [j for j,body in enumerate(record.person_bboxes)
                              if bbox_iou(np.asarray(row.body_bbox),body) >= .7] if record else []
                    if (not owners or not (t['forward'] or t['reverse'])
                            or any(j in t['forward'] or j in t['reverse'] for j in owners)
                            # Deferring a main-face conflict needs positive,
                            # unique ownership in BOTH directions. An absent
                            # head or ambiguous mask cannot clear the conflict.
                            or ((not is_context or joint_context) and
                                (len(owners) != 1 or len(t['forward']) != 1 or t['forward'] != t['reverse']))):
                        conflicts.append(dict(name=other_name,frame_index=row.frame_index))
                    else:
                        item = dict(name=other_name,frame_index=row.frame_index)
                        if item not in verified_other_bodies:
                            verified_other_bodies.append(item)
                if conflicts:
                    proof = dict(proof,accepted=False,reason='conflicting_direct_face_anchor',conflicts=conflicts)
                elif not is_context or joint_context:
                    proof = dict(proof,verified_other_body_faces=verified_other_bodies)
            proof = dict(proof,elapsed_seconds=time.monotonic()-started)
            candidate['attempts'].append(dict(name=name,anchor_frame=anchor.frame_index,
                                              seed_kind=('joint_context_face' if joint_context else 'context_face')
                                              if is_context else seed_kinds[(name,anchor.frame_index)],**proof))
            if proof['accepted']:
                # Only this accepted attempt can relax a raw cut. A rejected
                # longer path may have visited a cut which its retry did not.
                raw_cuts = sorted(set(cuts) | {f for f,d in getattr(verifier,'transition_cache',{}).items() if d.get('cut')})
                proven = {c for c in raw_cuts for link in proof.get('camera',[])
                          if not is_context and link.get('accepted')
                          and min(link['from_frame'],link['to_frame']) < c <= max(link['from_frame'],link['to_frame'])}
                boundaries = [c for c in raw_cuts if c not in proven]
                for frame in proof.get('support_frames',attempt_targets):
                    if frame in claims and frame in attempt_targets:
                        claims[frame].add(name)
                        shot = bisect_right(boundaries,frame)
                        lower = max(seg.start,boundaries[shot-1]/fps) if shot else seg.start
                        upper = min(seg.end,boundaries[shot]/fps) if shot < len(boundaries) else seg.end
                        claim_limits[frame].setdefault(name,[]).append((lower,upper))
            if on_progress:
                on_progress(i+1,len(segments))
        names = [next(iter(claims[f])) if len(claims[f]) == 1 else None for f in targets]
        # Conflicting directions can leave fragments shorter than the original
        # proof. Those fragments need their own minimum temporal support.
        for name,indices in groupby(range(len(targets)),key=lambda k:names[k]):
            indices = list(indices)
            # Expanded verification covers the whole original claim only.
            # Any competing name breaks that proof; its remaining fragment
            # must satisfy the usual independent temporal support requirement.
            continuous = (name,tuple(targets[k] for k in indices)) in continuous_claims
            if name and not continuous and (targets[indices[-1]]-targets[indices[0]])/fps < .15-1e-6:
                for k in indices:
                    names[k] = None
        if any(names):
            edges = [seg.start,*[(a+b)/(2*fps) for a,b in zip(targets,targets[1:])],seg.end]
            ranges = []
            for k,(frame,name) in enumerate(zip(targets,names,strict=True)):
                a,b = edges[k:k+2]
                limits = [(max(a,x),min(b,y)) for x,y in claim_limits[frame].get(name,[])
                          if max(a,x) < min(b,y)]
                bounds = sorted({a,b,*[t for pair in limits for t in pair]})
                for start,end in zip(bounds,bounds[1:]):
                    value = name if any(x <= start and end <= y for x,y in limits) else None
                    if ranges and ranges[-1]['name'] == value:
                        ranges[-1]['end'] = end
                    else:
                        ranges.append(dict(start=start,end=end,name=value))
            recovered[i] = ranges
            candidate.update(reason='confirmed_visual_path' if len(ranges) == 1 else 'confirmed_partial_visual_path',
                             recovered_ranges=[r for r in ranges if r['name']])
            if len(ranges) == 1:
                candidate['name'] = ranges[0]['name']
            audit['recovered_seconds'] += sum(r['end']-r['start'] for r in ranges if r['name'])
        elif any(len(values) > 1 for values in claims.values()):
            candidate['reason'] = 'conflicting_tracking_names'
    if not recovered:
        return output,audit
    # Split only where the verified name changes. Keep unknown remainders and
    # their original face observations; every original instant appears once.
    keys = ('segments','decisions','labels','previews','evidence','preview_sources')
    expanded = {**output,**{key:[] for key in keys},'accurate_indices':[]}
    named_parts = {}
    for i,seg in enumerate(segments):
        ranges = recovered.get(i)
        parts = split_segment(seg,[dict(time=r['start']) for r in ranges[1:]]) if ranges else [seg]
        for k,part in enumerate(parts):
            index = len(expanded['segments'])
            name = ranges[k]['name'] if ranges else None
            if name:
                named_parts[index] = name
            evidence = [(o,n) for o,n in output['evidence'][i] if part.start <= o.time_seconds < part.end]
            thumbnails,owned = output['preview_sources'][i]
            previews = [thumbnails.get(o.frame_index) or owned[o.frame_index]
                        for o,_ in sorted(evidence,key=lambda row:row[0].quality,reverse=True)
                        if o.frame_index in thumbnails or o.frame_index in owned][:5]
            expanded['segments'].append(part)
            expanded['decisions'].append(decisions[i])
            expanded['labels'].append(output['labels'][i])
            expanded['evidence'].append(evidence if ranges else output['evidence'][i])
            expanded['previews'].append(previews if ranges else output['previews'][i])
            expanded['preview_sources'].append(output['preview_sources'][i])
            if i in output['accurate_indices']:
                expanded['accurate_indices'].append(index)
    output = expanded
    segments,decisions = output['segments'],output['decisions']
    recovered = named_parts
    # Only joins involving a newly recovered piece change old clip boundaries.
    names = [recovered.get(i,d.reference_id) for i,d in enumerate(decisions)]
    groups = []
    for i,seg in enumerate(segments):
        if (groups and names[i] and names[i] == names[groups[-1][-1]]
                and abs(segments[i-1].end-seg.start) <= 1e-6
                and (i in recovered or any(j in recovered for j in groups[-1]))):
            groups[-1].append(i)
        else:
            groups.append([i])
    merged = {**output,**{key:[] for key in keys},'accurate_indices':[]}
    for indices in groups:
        first,last = indices[0],indices[-1]
        changed = any(i in recovered for i in indices)
        merged['segments'].append(replace(segments[first],end=segments[last].end,
            bboxes=[b for i in indices for b in segments[i].bboxes]) if changed else segments[first])
        merged['decisions'].append(SegmentReferenceDecision(names[first],'matched','member_mask_continuity')
                                   if changed else decisions[first])
        merged['evidence'].append([row for i in indices for row in output['evidence'][i]])
        merged['previews'].append([p for i in indices for p in output['previews'][i]][:5])
        merged['preview_sources'].append(tuple(ChainMap(*(output['preview_sources'][i][k] for i in indices)) for k in (0,1)))
        if any(i in output['accurate_indices'] for i in indices):
            merged['accurate_indices'].append(len(merged['segments'])-1)
    merged['labels'] = [i+1 if d.reference_id else None for i,d in enumerate(merged['decisions'])]
    return merged,audit
