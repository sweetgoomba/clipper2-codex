"""Correct an early named-part boundary from a frozen face run across it.

The output boundary is not an evidence boundary. Two original, owned face
observations may prove that the outgoing member still occupies the selected
body after an early label switch. This never promotes an unknown/group part,
uses a recovered label as a seed, or calls SAM/new inference.
"""
from bisect import bisect_left
from collections import ChainMap
from dataclasses import replace
import cv2
import numpy as np

from .body_continuity import _check_source_chain
from .member_timeline import _valid
from .reference_matcher import SegmentReferenceDecision
from .segment import Segment

VERSION = 'original_face_run_boundary_v1'


def reconcile_named_boundaries(output, frame_records, observations, joint_matches, matcher,
                               *, video_path, fps, group_segments, handoffs):
    audit = dict(version=VERSION, corrected_seconds=0., corrections=[], candidates=[])
    if not observations or handoffs is None or not np.isfinite(fps) or fps <= 0:
        return output, audit
    records = {round(r.t*fps): r for r in frame_records}
    rows = sorted({o.frame_index:o for o in observations}.values(), key=lambda o:o.time_seconds)
    times = [o.time_seconds for o in rows]
    joints = {int(f):m for f,m in joint_matches.items()}
    # Every usable accepted identity interrupts a run, even when its detector
    # score is below the stricter quality required to seed a correction.
    accepted = [(o,joints[o.frame_index]['name']) for o in rows if _valid(o)
                and joints.get(o.frame_index,{}).get('status') == 'accepted'
                and joints[o.frame_index].get('name')]
    segments, decisions = output['segments'], output['decisions']
    cap = None
    try:
        for i in range(len(segments)-1):
            left,right = segments[i:i+2]
            name,other = decisions[i].reference_id,decisions[i+1].reference_id
            if not name or not other or name == other or abs(left.end-right.start)>1e-6:
                continue
            boundary = right.start
            before = [(o,n) for o,n in accepted if max(left.start,boundary-.6)<=o.time_seconds<boundary]
            after = [(o,n) for o,n in accepted if boundary<=o.time_seconds<min(right.end,boundary+.6)]
            if not before or before[-1][1] != name or not after or after[0][1] != name:
                continue
            same = []
            for row,n in after:
                if n != name:
                    break
                same.append(row)
            left_seeds = [o for o,n in before if n == name and o.detector_score >= .9]
            right_seeds = [o for o in same if o.detector_score >= .9]
            if not left_seeds or not right_seeds:
                continue
            a,b = left_seeds[-1],right_seeds[-1]
            if not .15-1e-6 <= b.time_seconds-a.time_seconds <= .6+1e-6:
                continue
            # Include the last observed source frame, never extrapolate to the
            # next face or a midpoint across unobserved subject changes.
            new_boundary = (b.frame_index+1)/fps
            if not boundary < new_boundary < right.end:
                continue
            local = rows[bisect_left(times,a.time_seconds):bisect_left(times,b.time_seconds+1e-6)]
            candidate = dict(index=i, before=boundary, after=new_boundary, name=name,
                             next_name=other, seed_frames=[a.frame_index,b.frame_index])
            audit['candidates'].append(candidate)
            expected = sorted(f for f in records if a.frame_index<=f<=b.frame_index)
            failure = None
            if [o.frame_index for o in local] != expected:
                failure = 'missing_original_observation'
            elif any(records[o.frame_index].main_bbox is None or o.body_bbox is None
                     or not np.allclose(records[o.frame_index].main_bbox,o.body_bbox,atol=1e-3,rtol=0) for o in local):
                failure = 'unowned_body'
            elif any(records[o.frame_index].scene_kind != 'main' for o in local):
                failure = 'non_main_path'
            elif any(g.start<new_boundary and a.time_seconds<g.end for g in group_segments):
                failure = 'group_on_path'
            elif any(a.frame_index<h['frame']<=b.frame_index for h in handoffs):
                failure = 'handoff'
            elif any(n!=name and a.frame_index<=o.frame_index<=b.frame_index for o,n in accepted):
                failure = 'conflicting_joint_face'
            if failure is None:
                scope = Segment('main',None,a.time_seconds,new_boundary,[])
                valid = [o for o in local if _valid(o)]
                direct = [matcher.match(o,scope,VERSION).reference_id for o in valid]
                if any(n and n!=name for n in direct):
                    failure = 'conflicting_primary_face'
                alien = [o for o in valid if min(1.-float(o.embedding@s.embedding) for s in (a,b))>.65]
                if any(.15<=y.time_seconds-x.time_seconds<=.6 and 1.-float(x.embedding@y.embedding)<=.6
                       for j,x in enumerate(alien) for y in alien[j+1:]):
                    failure = 'repeated_alien_face'
            if failure is None:
                if cap is None:
                    cap = cv2.VideoCapture(str(video_path))
                if not cap.isOpened() or abs(float(cap.get(cv2.CAP_PROP_FPS))-fps)>.01:
                    failure = 'source_unavailable_or_fps_mismatch'
                else:
                    failure = _check_source_chain(cap,local,records,audit=candidate)
            candidate['reason'] = failure or 'original_face_run_proved'
            if failure is None:
                audit['corrections'].append(candidate)
                audit['corrected_seconds'] += new_boundary-boundary
    finally:
        if cap is not None:
            cap.release()
    if not audit['corrections']:
        return output,audit
    result = {**output, **{k:list(output[k]) for k in
        ('segments','decisions','labels','previews','evidence','preview_sources','accurate_indices')}}
    for change in audit['corrections']:
        i,end = change['index'],change['after']
        left,right = result['segments'][i:i+2]
        boxes = left.bboxes+right.bboxes
        result['segments'][i] = replace(left,end=end,bboxes=[b for b in boxes if left.start<=b[0]<end])
        result['segments'][i+1] = replace(right,start=end,bboxes=[b for b in boxes if end<=b[0]<right.end])
        sources = tuple(ChainMap(result['preview_sources'][i][k],result['preview_sources'][i+1][k]) for k in (0,1))
        evidence = result['evidence'][i]+result['evidence'][i+1]
        for j in (i,i+1):
            part = result['segments'][j]
            kept = [(o,n) for o,n in evidence if part.start<=o.time_seconds<part.end]
            result['evidence'][j] = kept
            result['preview_sources'][j] = sources
            result['previews'][j] = [sources[0].get(o.frame_index) or sources[1][o.frame_index]
                for o,_ in sorted(kept,key=lambda e:e[0].quality,reverse=True)
                if o.frame_index in sources[0] or o.frame_index in sources[1]][:5]
        result['decisions'][i] = SegmentReferenceDecision(change['name'],'matched','original_face_run_boundary')
        result['accurate_indices'] = sorted(set(result['accurate_indices'])|{i,i+1})
    return result,audit
