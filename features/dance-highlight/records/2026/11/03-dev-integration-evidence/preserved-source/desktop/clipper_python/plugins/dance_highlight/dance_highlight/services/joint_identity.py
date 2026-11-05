"""Revalidate Dance names using frozen independent face and body evidence.

No recovered name or embedding enters either model's recognition gallery.
This stage runs after ordinary naming/merging, so a one-model aggregate cannot
overwrite an independently verified correction or refill a conflict.
"""
from bisect import bisect_right
from collections import ChainMap, defaultdict
from dataclasses import replace
import numpy as np

from .member_timeline import _valid
from .secondary_faces import _normalized

VERSION = 'joint_face_identity_v4_chronological_runs'


def joint_video_matches(rows, vectors, anchors, roster, *, query_frames=None):
    """Compare every roster member in each model; exclude the query vicinity."""
    from .temporal_support import independent_pair
    requested = set(rows) if query_frames is None else set(query_frames) & rows.keys()
    result = {f:dict(name=None,status='unavailable',reason='missing_joint_embedding') for f in rows if f in requested}
    if not requested:
        return result
    normalized = {}
    dimensions = None
    for frame,row in rows.items():
        if frame not in vectors or not _valid(row):
            continue
        a,b = _normalized(row.embedding),_normalized(vectors[frame])
        if a is None or b is None:
            continue
        shape = (a.size,b.size)
        if dimensions is None:
            dimensions = shape
        if shape == dimensions:
            normalized[frame] = (a,b)
    if not normalized:
        return result
    query = [f for f in normalized if f in requested]
    if not query:
        return result
    names = sorted(roster)
    for frame in query:
        result[frame] = dict(name=None,status='insufficient',reason='incomplete_joint_gallery')
    if not names:
        return result
    owners = defaultdict(set)
    for anchor in anchors:
        if anchor['frame_index'] in normalized:
            owners[anchor['frame_index']].add(anchor['name'])
    banks = {name:[f for f,labels in owners.items() if labels == {name}] for name in names}
    if any(len(bank) < 2 for bank in banks.values()):
        return result
    times = np.array([rows[f].time_seconds for f in query])
    tables,supports = [],[]
    for model in (0,1):
        matrix = np.asarray([normalized[f][model] for f in query])
        table,source_frames = [],[]
        for name in names:
            bank = banks[name]
            bank_times = np.array([rows[f].time_seconds for f in bank])
            features = np.asarray([normalized[f][model] for f in bank])
            distances = np.clip(1.-matrix@features.T,0.,2.)
            distances[np.abs(times[:,None]-bank_times) <= 2.000001] = np.inf
            pairs = [independent_pair(zip(values,bank_times,bank),minimum_gap=.15-1e-6)
                     for values in distances]
            table.append(np.asarray([max(pair[0][0],pair[1][0]) if pair else np.inf for pair in pairs]))
            source_frames.append(np.asarray([[pair[0][2],pair[1][2]] if pair else [bank[0],bank[0]]
                                             for pair in pairs]))
        tables.append(np.stack(table,axis=1))
        supports.append(source_frames)
    primary,secondary = tables
    for i,frame in enumerate(query):
        if not np.isfinite(primary[i]).all() or not np.isfinite(secondary[i]).all():
            continue
        average = (primary[i]+secondary[i])/2
        order = np.argsort(average)
        best = int(order[0])
        margin = float(average[order[1]]-average[best]) if len(names)>1 else None
        agree = int(np.argmin(primary[i])) == int(np.argmin(secondary[i])) == best
        if len(names)>1:
            agree = agree and all(np.sort(table[i])[1]-np.sort(table[i])[0] > 1e-6 for table in tables)
        accepted = agree and average[best] <= .5 and max(primary[i,best],secondary[i,best]) <= .6 and (margin is None or margin >= .08)
        result[frame] = dict(name=names[best] if accepted else None,
            status='accepted' if accepted else 'insufficient' if agree else 'conflict',
            reason='joint_video_match' if accepted else 'joint_video_rejected',best=names[best],
            distance=float(average[best]),margin=margin,primary=float(primary[i,best]),secondary=float(secondary[i,best]),
            model_candidates=[[dict(name=names[j], distance=float(table[i,j]))
                               for j in np.argsort(table[i], kind='stable')] for table in tables],
            support_frames=[supports[k][best][i].tolist() for k in (0,1)])
    return result


def _apply_ranges(output, changes):
    from .main_identity import split_segment
    from .reference_matcher import SegmentReferenceDecision
    keys = ('segments','decisions','labels','previews','evidence','preview_sources')
    parts = []
    for i,segment in enumerate(output['segments']):
        ranges = changes.get(i)
        slices = split_segment(segment,[dict(time=r['start']) for r in ranges[1:]]) if ranges else [segment]
        for j,part in enumerate(slices):
            name = ranges[j]['name'] if ranges else output['decisions'][i].reference_id
            changed = bool(ranges and name != output['decisions'][i].reference_id)
            evidence = [(o,n) for o,n in output['evidence'][i] if part.start <= o.time_seconds < part.end]
            parts.append(dict(segment=part,name=name,changed=changed,evidence=evidence,source=i))
    groups = []
    for part in parts:
        if (groups and part['name'] and part['name'] == groups[-1][-1]['name']
                and abs(groups[-1][-1]['segment'].end-part['segment'].start)<1e-6
                and (part['changed'] or any(p['changed'] for p in groups[-1]))):
            groups[-1].append(part)
        else:
            groups.append([part])
    result = {**output,**{k:[] for k in keys},'accurate_indices':[]}
    for group in groups:
        first,last = group[0],group[-1]
        source,name = first['source'],first['name']
        changed = any(p['changed'] for p in group)
        result['segments'].append(replace(first['segment'],end=last['segment'].end,
            bboxes=[b for p in group for b in p['segment'].bboxes]))
        result['decisions'].append(SegmentReferenceDecision(name,'matched' if name else 'unmatched',
            'joint_identity_correction' if name else 'joint_identity_conflict') if changed else output['decisions'][source])
        evidence = [e for p in group for e in p['evidence']]
        sources = tuple(ChainMap(*(output['preview_sources'][p['source']][k] for p in group)) for k in (0,1))
        previews = [sources[0].get(o.frame_index) or sources[1][o.frame_index]
                    for o,_ in sorted(evidence,key=lambda e:e[0].quality,reverse=True)
                    if o.frame_index in sources[0] or o.frame_index in sources[1]][:5]
        result['evidence'].append(evidence)
        result['preview_sources'].append(sources)
        result['previews'].append(previews)
        if any(p['source'] in changes or p['source'] in output['accurate_indices'] for p in group):
            result['accurate_indices'].append(len(result['segments'])-1)
    result['labels'] = [i+1 if d.reference_id else None for i,d in enumerate(result['decisions'])]
    return result


def revalidate_named_segments(output, frame_records, video_path, fps, matches, video_anchors, *,
                              cut_frames=(), camera_transitions=(), verify_track=None, on_progress=None,
                              source_inventory=None):
    from .track import bbox_iou
    rows = {o.frame_index:o for evidence in output['evidence'] for o,_ in evidence}
    records = {round(r.t*fps):r for r in frame_records}
    audit = dict(version=VERSION,corrected_seconds=0.,recovered_seconds=0.,conflict_seconds=0.,candidates=[])
    accepted = [(m['name'],rows[f]) for f,m in matches.items() if f in rows and
                m.get('status') == 'accepted' and m.get('name') and _valid(rows[f]) and rows[f].detector_score >= .9]
    if not accepted:
        return output,audit
    if cut_frames is None:
        from .camera_transitions import scan_source_transitions
        transitions,reason = scan_source_transitions(video_path,fps,max(records,default=0))
        if reason != 'complete':
            return output,dict(audit,reason=reason)
        cut_frames = [f for f,d in transitions.items() if d['cut']]
        camera_transitions = [dict(frame=f,**d) for f,d in transitions.items() if d['color_candidate']]
        audit['camera_transitions'] = camera_transitions
    # A stable-background proposal only admits an identity candidate here.
    # The tracker retains raw cuts and demands exact masked foreground proof.
    proposals = {d['frame'] for d in camera_transitions if d.get('structure',{}).get('continuous')}
    raw_cuts = sorted(set(cut_frames))
    cuts = sorted(set(raw_cuts)-proposals)
    # Accepted main observations retain their temporal order. In A -> B -> A,
    # neither A run can borrow support or a tracking anchor across B.
    runs = []
    for name,row in sorted(accepted,key=lambda item:(item[1].time_seconds,item[1].frame_index)):
        shot = bisect_right(cuts,row.frame_index)
        if (not runs or runs[-1]['name'] != name or runs[-1]['shot'] != shot
                or row.time_seconds-runs[-1]['rows'][-1].time_seconds > .6+1e-6):
            runs.append(dict(name=name,shot=shot,rows=[]))
        runs[-1]['rows'].append(row)
    for j,run in enumerate(runs):
        pairs = [(a,b) for k,a in enumerate(run['rows']) for b in run['rows'][k+1:]
                 if .15-1e-6 <= b.time_seconds-a.time_seconds <= .6+1e-6]
        supported = {r.frame_index for pair in pairs for r in pair}
        run['repeated'] = [r for r in run['rows'] if r.frame_index in supported]
        run['lower'] = runs[j-1]['rows'][-1].frame_index if j else -float('inf')
        run['upper'] = runs[j+1]['rows'][0].frame_index if j+1 < len(runs) else float('inf')
    frozen = [(a['name'],rows[a['frame_index']]) for a in video_anchors if a['frame_index'] in rows]
    verifier,changes = verify_track,{}
    for i,(segment,decision) in enumerate(zip(output['segments'],output['decisions'],strict=True)):
        local_runs = [r for r in runs if r['name'] != decision.reference_id and
                      any(segment.start <= o.time_seconds < segment.end for o in r['repeated'])]
        if not local_runs:
            continue
        targets = sorted(f for f,r in records.items() if segment.start <= r.t < segment.end)
        if not targets:
            continue
        candidate = dict(start=segment.start,end=segment.end,old_name=decision.reference_id,attempts=[])
        audit['candidates'].append(candidate)
        claims = {f:set() for f in targets}
        claim_limits = {f:defaultdict(list) for f in targets}
        disputed = set()
        for run in local_runs:
            name,shot = run['name'],run['shot']
            inside = [o for o in run['repeated'] if segment.start <= o.time_seconds < segment.end]
            seeds = [o for o in run['repeated'] if any(abs(o.time_seconds-r.time_seconds) <= .6+1e-6 for r in inside)]
            # The nearest earlier original face can cover the start of a piece.
            before = [o for o in seeds if o.time_seconds <= segment.start]
            anchor = max(before,key=lambda o:o.time_seconds) if before else min(seeds,key=lambda o:o.time_seconds)
            shot_targets = [f for f in targets if bisect_right(cuts,f) == shot and run['lower'] < f < run['upper']]
            # Every independent pair contributes only inside this chronological
            # run, including dense samples whose adjacent gaps are below .15s.
            for k,a in enumerate(seeds):
                for b in seeds[k+1:]:
                    if .15-1e-6 <= b.time_seconds-a.time_seconds <= .6+1e-6:
                        disputed.update(f for f in shot_targets if a.time_seconds-1e-6 <= records[f].t <= b.time_seconds+1e-6)
            for direction in (-1,1):
                subset = [f for f in shot_targets if (f-anchor.frame_index)*direction >= 0]
                if not subset or (max(subset)-min(subset))/fps < .15-1e-6:
                    continue
                lo,hi = min(anchor.frame_index,*subset),max(anchor.frame_index,*subset)
                path = [records[f] for f in sorted(records) if lo <= f <= hi]
                if direction == -1:
                    path.reverse()
                try:
                    if verifier is None:
                        from .mask_tracker import MaskTracker
                        verifier = MaskTracker(video_path,fps,joint_faces=accepted,source_inventory=source_inventory,
                            on_progress=(lambda done,total:on_progress(i+done/max(1,total),len(output['segments']))) if on_progress else None)
                        audit['model'] = verifier.provenance
                    proof = verifier(anchor,path,subset)
                    if not proof['accepted'] and proof.get('reason') == 'unconfirmed_main_ownership':
                        stop = proof.get('frame')
                        partial = [f for f in subset if stop in subset and (f-stop)*direction < 0]
                        if partial and (max(partial)-min(partial))/fps >= .15-1e-6:
                            low,high = min(anchor.frame_index,*partial),max(anchor.frame_index,*partial)
                            retry = verifier(anchor,[r for r in path if low <= round(r.t*fps) <= high],partial)
                            if retry['accepted']:
                                proof = dict(retry,support_frames=sorted(set(retry.get('support_frames',partial)) & set(partial)),whole_path_rejection=proof)
                    if proof['accepted']:
                        support = sorted(set(proof.get('support_frames',subset)) & set(subset))
                        trace = {t['frame']:t for t in proof.get('trace',[])}
                        low,high = min(anchor.frame_index,*support),max(anchor.frame_index,*support)
                        conflicts = []
                        for other,row in [*frozen,*accepted]:
                            if other == name or not low <= row.frame_index <= high:
                                continue
                            t = trace.get(row.frame_index)
                            record = records.get(row.frame_index)
                            owners = [j for j,box in enumerate(record.person_bboxes) if bbox_iou(np.asarray(row.body_bbox),box) >= .7] if record else []
                            if (not t or not owners or not (t['forward'] or t['reverse']) or
                                    any(j in t['forward'] or j in t['reverse'] for j in owners)):
                                conflicts.append(dict(name=other,frame_index=row.frame_index))
                        if conflicts:
                            proof = dict(proof,accepted=False,reason='conflicting_direct_face_anchor',conflicts=conflicts)
                        else:
                            proven_cuts = {t['cut_frame'] for t in proof.get('identity_supported_transitions',[])
                                           if t.get('foreground',{}).get('accepted')}
                            proven_cuts.update(c for c in raw_cuts for link in proof.get('camera',[])
                                               if link.get('accepted') and min(link['from_frame'],link['to_frame']) < c <= max(link['from_frame'],link['to_frame']))
                            boundaries = [c for c in raw_cuts if c not in proven_cuts]
                            for f in support:
                                claims[f].add(name)
                                shot_index = bisect_right(boundaries,f)
                                lower = max(segment.start,boundaries[shot_index-1]/fps) if shot_index else segment.start
                                upper = min(segment.end,boundaries[shot_index]/fps) if shot_index < len(boundaries) else segment.end
                                claim_limits[f][name].append((lower,upper))
                except Exception as error:
                    proof = dict(accepted=False,reason='tracking_unavailable',error_type=type(error).__name__)
                candidate['attempts'].append(dict(name=name,anchor_frame=anchor.frame_index,
                    run_start_frame=run['rows'][0].frame_index,run_end_frame=run['rows'][-1].frame_index,**proof))
        edges = [segment.start,*[(a+b)/(2*fps) for a,b in zip(targets,targets[1:])],segment.end]
        ranges = []
        for k,frame in enumerate(targets):
            values = claims[frame]
            name = next(iter(values)) if len(values)==1 else None if values or frame in disputed else decision.reference_id
            a,b = edges[k:k+2]
            limits = claim_limits[frame].get(name,[])
            if name is None:
                shot = bisect_right(raw_cuts,frame)
                lo = max(a,raw_cuts[shot-1]/fps) if shot else a
                hi = min(b,raw_cuts[shot]/fps) if shot < len(raw_cuts) else b
                limits = [(lo,hi)]
            bounds = sorted({a,b,*[max(a,min(b,t)) for pair in limits for t in pair]})
            for start,end in zip(bounds,bounds[1:]):
                if end <= start:
                    continue
                value = name if any(lo <= start and end <= hi for lo,hi in limits) else decision.reference_id
                if ranges and ranges[-1]['name'] == value:
                    ranges[-1]['end'] = end
                else:
                    ranges.append(dict(start=start,end=end,name=value))
        if any(r['name'] != decision.reference_id for r in ranges):
            changes[i] = ranges
            candidate['ranges'] = ranges
            key = 'corrected_seconds' if decision.reference_id else 'recovered_seconds'
            audit[key] += sum(r['end']-r['start'] for r in ranges if r['name'] and r['name'] != decision.reference_id)
            if decision.reference_id:
                audit['conflict_seconds'] += sum(r['end']-r['start'] for r in ranges if not r['name'])
        if on_progress:
            on_progress(i+1,len(output['segments']))
    if hasattr(verifier,'transition_cache'):
        audit['camera_transitions'] = [dict(frame=f,**d) for f,d in sorted(verifier.transition_cache.items()) if d['color_candidate']]
    return (_apply_ranges(output,changes) if changes else output),audit
