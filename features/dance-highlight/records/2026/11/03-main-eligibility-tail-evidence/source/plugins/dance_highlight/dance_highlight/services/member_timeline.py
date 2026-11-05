"""Dance-only, time-local member decisions before clip generation.

Body track IDs and an old whole-clip name never vote for a new piece. Video
anchors are a frozen set of repeated, direct reference matches; recovered faces
cannot become anchors. Missing faces stay unresolved outside a short gap.
"""
from dataclasses import asdict, replace
from collections import ChainMap
from types import SimpleNamespace
import numpy as np

from .main_identity import refine_switch_boundaries, split_segment
from .reference_matcher import SegmentReferenceDecision

MAX_SUPPORT_GAP_SECONDS = .6


def _valid(row):
    return (row.association == 'confirmed' and not row.failure
            and row.embedding is not None and row.detector_score >= .8)


def build_video_anchors(observations, matches):
    """Only repeated strong reference hits, never results of video recovery."""
    candidates = {}
    for row, match in zip(observations, matches, strict=True):
        if not _valid(row) or row.detector_score < .9 or not match.reference_id:
            continue
        distance = next((c.distance for c in match.candidates
                         if c.reference_id == match.reference_id), 2.)
        if distance <= .55:
            candidates[(match.reference_id, row.frame_index)] = row
    anchors = []
    for (name, _), row in candidates.items():
        if any(other_name == name and .15 <= abs(other.time_seconds-row.time_seconds) <= .6
               for (other_name, _), other in candidates.items()):
            anchors.append((name, row))
    return anchors


def match_video_anchors(row, anchors):
    from .temporal_support import independent_pair
    if not _valid(row) or not anchors:
        return None
    distances = {}
    for name, anchor in anchors:
        if anchor.frame_index == row.frame_index:
            continue
        distances.setdefault(name, []).append((1.-float(row.embedding @ anchor.embedding), anchor.time_seconds))
    candidates = []
    for name, values in distances.items():
        pair = independent_pair(values)
        if pair is not None:
            candidates.append((max(pair[0][0], pair[1][0]), name))
    candidates.sort()
    if (not candidates or candidates[0][0] > .5
            or len(candidates) > 1 and candidates[1][0]-candidates[0][0] < .08):
        return None
    return candidates[0][1]


def _window_name(row, rows, matches, segment, matcher, scope):
    """Average a short, coherent face window, never a whole body track."""
    indices = [i for i, other in enumerate(rows)
               if _valid(other) and abs(other.time_seconds-row.time_seconds) <= .4]
    if len(indices) < 3:
        return None
    vectors = np.asarray([rows[i].embedding for i in indices])
    center = vectors.mean(axis=0)
    center /= np.linalg.norm(center) + 1e-9
    if max(1.-vectors @ center) > .35:
        return None
    match = matcher.match(replace(row, embedding=center), segment, scope + '-window')
    direct_names = {matches[i].reference_id for i in indices if matches[i].reference_id}
    return match.reference_id if not direct_names or direct_names == {match.reference_id} else None


def _named_ranges(segment, rows, names, *, cut_times=()):
    hits = [(row, name) for row, name in zip(rows, names, strict=True) if name]
    # A single erroneous named frame cannot create a part or interrupt another.
    hits = [(row, name) for row, name in hits if any(
        other_name == name and .15 <= abs(other.time_seconds-row.time_seconds) <= MAX_SUPPORT_GAP_SECONDS
        for other, other_name in hits)]
    runs = []
    for row, name in hits:
        if runs and runs[-1][0] == name and row.time_seconds-runs[-1][1][-1].time_seconds <= MAX_SUPPORT_GAP_SECONDS:
            previous = runs[-1][1][-1]
            intervening = [o for o in rows if _valid(o) and previous.time_seconds < o.time_seconds < row.time_seconds]
            alien = [o for o in intervening if min(1.-float(o.embedding @ previous.embedding),
                                                  1.-float(o.embedding @ row.embedding)) > .6]
            if len(alien) < 2 or alien[-1].time_seconds-alien[0].time_seconds < .15:
                runs[-1][1].append(row)
                continue
        runs.append((name, [row]))
    ranges = []
    for name, support in runs:
        if len(support) < 2 or support[-1].time_seconds-support[0].time_seconds < .15:
            continue
        ranges.append({'start': max(segment.start, support[0].time_seconds-.1,
                                max((c for c in cut_times if c <= support[0].time_seconds), default=segment.start)),
                       'end': min(segment.end, support[-1].time_seconds+.1,
                                  min((c for c in cut_times if c > support[-1].time_seconds), default=segment.end)),
                       'name': name, 'first_time': support[0].time_seconds,
                       'last_time': support[-1].time_seconds,
                       'support_frames': [o.frame_index for o in support]})
    if ranges:
        if ranges[0]['start']-segment.start <= .3 and not any(
                segment.start < c <= ranges[0]['first_time'] for c in cut_times):
            ranges[0]['start'] = segment.start
        if segment.end-ranges[-1]['end'] <= .3 and not any(
                ranges[-1]['last_time'] < c < segment.end for c in cut_times):
            ranges[-1]['end'] = segment.end
    return ranges


def _named_evidence_boundaries(segment, ranges):
    candidates = []
    # Keep short identified appearances separate from surrounding unresolved
    # faces, without inventing cuts based on clip length. Close A/B runs use
    # their shared change boundary below instead of two artificial gaps.
    for index, run in enumerate(ranges):
        previous = ranges[index-1] if index else None
        following = ranges[index+1] if index+1 < len(ranges) else None
        edges = []
        if (previous is None or previous['name'] == run['name']
                or previous['last_time'] < segment.start
                or run['first_time']-previous['last_time'] > MAX_SUPPORT_GAP_SECONDS):
            edges.append(run['start'])
        if (following is None or following['name'] == run['name']
                or following['first_time'] >= segment.end
                or following['first_time']-run['last_time'] > MAX_SUPPORT_GAP_SECONDS):
            edges.append(run['end'])
        candidates.extend({'time': t, 'left_time': t, 'right_time': t,
                           'reason': 'named_evidence_edge', 'strength': 1.} for t in edges)
    return _select_boundaries(segment, candidates)


def _identity_boundaries(segment, rows, names, ranges, *, cut_times=()):
    candidates = []
    for left, right in zip(ranges, ranges[1:]):
        if left['name'] != right['name']:
            cuts = [cut for cut in cut_times if left['last_time'] < cut <= right['first_time']]
            # Multiple edit candidates make the exact source frame ambiguous,
            # not the independently supported change between two member names.
            # Retain the existing midpoint/visual-refinement proposal in that
            # case instead of merging both names into one conflicting piece.
            exact_cut = cuts[0] if len(cuts) == 1 else None
            candidates.append({'time': exact_cut if exact_cut is not None else (left['last_time']+right['first_time'])/2,
                               'left_time': left['last_time'], 'right_time': right['first_time'],
                               'reason': 'source_cut_face_change' if exact_cut is not None else 'repeated_reference_change',
                               'strength': 4. if exact_cut is not None else 2.})
    valid = [(o, name) for o, name in zip(rows, names, strict=True) if _valid(o)]
    # Bound classification by observed face coverage. A brief face appearance
    # cannot name several unseen seconds.
    if valid:
        gaps = []
        first, last = valid[0][0], valid[-1][0]
        if first.time_seconds-segment.start > .4:
            gaps.append(first.time_seconds-.1)
        if segment.end-last.time_seconds > .4:
            gaps.append(last.time_seconds+.1)
        for (a, _), (b, _) in zip(valid, valid[1:]):
            if b.time_seconds-a.time_seconds > .6:
                gaps.extend((a.time_seconds+.1, b.time_seconds-.1))
        candidates.extend({'time': t, 'left_time': t, 'right_time': t,
                           'reason': 'face_coverage_gap', 'strength': 3.} for t in gaps)
    for index in range(1, len(valid)):
        # Gather the nearest contiguous observations spanning the same minimum
        # support time at every sampling cadence. Two adjacent dense samples
        # alone may be only one source-frame interval apart.
        lo, hi = index-1, index
        while (lo > 0 and valid[index-1][0].time_seconds-valid[lo][0].time_seconds < .15
               and not any(valid[lo-1][0].time_seconds < cut <= valid[lo][0].time_seconds
                           for cut in cut_times)):
            lo -= 1
        while (hi+1 < len(valid) and valid[hi][0].time_seconds-valid[index][0].time_seconds < .15
               and not any(valid[hi][0].time_seconds < cut <= valid[hi+1][0].time_seconds
                           for cut in cut_times)):
            hi += 1
        left, right = valid[lo:index], valid[index:hi+1]
        a, b = left[-1][0], right[0][0]
        left_names, right_names = {n for _, n in left if n}, {n for _, n in right if n}
        if left_names & right_names:
            continue
        crossed = [cut for cut in cut_times if a.time_seconds < cut <= b.time_seconds]
        if len(crossed) > 1:
            continue
        if (b.time_seconds-a.time_seconds > .6 or a.time_seconds-left[0][0].time_seconds < .15
                or right[-1][0].time_seconds-b.time_seconds < .15
                or a.time_seconds-left[0][0].time_seconds > .6
                or right[-1][0].time_seconds-b.time_seconds > .6):
            continue
        lv, rv = np.asarray([o.embedding for o, _ in left]), np.asarray([o.embedding for o, _ in right])
        lc, rc = lv.mean(axis=0), rv.mean(axis=0)
        lc /= np.linalg.norm(lc)+1e-9; rc /= np.linalg.norm(rc)+1e-9
        distance = 1.-float(lc @ rc)
        if distance >= .65 and max(float(np.mean(1.-lv @ lc)), float(np.mean(1.-rv @ rc))) <= .3:
            candidates.append({'time': crossed[0] if crossed else (a.time_seconds+b.time_seconds)/2,
                               'left_time': a.time_seconds, 'right_time': b.time_seconds,
                               'reason': 'source_cut_face_change' if crossed else 'repeated_face_change',
                               'strength': 4. if crossed else distance})
    return _select_boundaries(segment, candidates)


def _select_boundaries(segment, candidates):
    selected = []
    for cut in sorted(candidates, key=lambda c: c['strength'], reverse=True):
        # The identity support itself requires 0.15 seconds. A separate 0.3s
        # clip floor would discard an already confirmed shorter member part.
        exact = cut['reason'] == 'source_cut_face_change'
        if ((segment.start < cut['time'] < segment.end if exact else
             cut['time']-segment.start >= .15 and segment.end-cut['time'] >= .15)
                and all(abs(cut['time']-other['time']) >= .15
                        or exact and other['reason'] == 'source_cut_face_change'
                        and abs(cut['time']-other['time']) > 1e-6 for other in selected)):
            selected.append(cut)
    return sorted(selected, key=lambda c: c['time'])


def _assign_piece(segment, selected, matcher, anchors, scope):
    usable = [(o, name) for o, name in selected if _valid(o)]
    def decision(name=None, reason='unresolved_face_interval'):
        return SegmentReferenceDecision(name, 'matched' if name else 'unmatched', reason)
    if len(usable) < 2 or usable[-1][0].time_seconds-usable[0][0].time_seconds < .15:
        return decision()
    supported = {}
    for row, name in usable:
        if name:
            supported.setdefault(name, []).append(row)
    supported = {name: hits for name, hits in supported.items()
                 if any(.15 <= b.time_seconds-a.time_seconds <= MAX_SUPPORT_GAP_SECONDS
                        for i, a in enumerate(hits) for b in hits[i+1:])}
    if len(supported) > 1:
        return decision(reason='conflicting_reference_parts')
    vectors = np.asarray([o.embedding for o, _ in usable])
    # Local aggregation recovers changing poses without a clip-wide duplicate
    # allocation rule. Distinct repeated faces must first be split.
    quality_rows = sorted((o for o, _ in usable), key=lambda o: o.quality, reverse=True)[:5]
    center = np.mean([o.embedding for o in quality_rows], axis=0)
    center /= np.linalg.norm(center)+1e-9
    if np.linalg.norm(center) < .99:
        return decision()
    representative = replace(quality_rows[0], embedding=center)
    aggregate = matcher.match(representative, segment, scope+'-piece')
    anchor_name = match_video_anchors(representative, anchors)
    name = next(iter(supported), None) or aggregate.reference_id or anchor_name
    if not name or aggregate.reference_id and aggregate.reference_id != name:
        return decision()
    hits = supported.get(name, [])
    if (hits and aggregate.reference_id != name and anchor_name != name
            and (hits[0].time_seconds-segment.start > .4 or segment.end-hits[-1].time_seconds > .4)):
        return decision(reason='insufficient_named_coverage')
    prototype = np.mean([o.embedding for o in hits], axis=0) if hits else center
    prototype /= np.linalg.norm(prototype)+1e-9
    alien = [o for o, _ in usable if 1.-float(o.embedding @ prototype) > .65]
    # Reject repeated evidence of another face, not unrelated embedding noise.
    # Keep the same .60 distance ceiling used for direct reference matching.
    if any(.15 <= b.time_seconds-a.time_seconds <= MAX_SUPPORT_GAP_SECONDS
           and 1.-float(a.embedding @ b.embedding) <= .6
           for i, a in enumerate(alien) for b in alien[i+1:]):
        return decision(reason='inconsistent_face_scope')
    return decision(name, 'member_timeline_consensus')


def _prepare_observations(segments, face_results, matcher):
    prepared, all_rows, all_matches = [], [], []
    for index, (segment, result) in enumerate(zip(segments, face_results, strict=True)):
        unique = {o.frame_index: o for o in getattr(result, 'owned_observations', [])
                  if segment.start <= o.time_seconds < segment.end}
        rows = sorted(unique.values(), key=lambda o: o.time_seconds)
        matches = [matcher.match(o, segment, f'main-{index}') for o in rows]
        prepared.append((rows, matches))
        all_rows.extend(rows); all_matches.extend(matches)
    return prepared, all_rows, all_matches


def video_reference_anchors(segments, face_results, matcher):
    _, rows, matches = _prepare_observations(segments, face_results, matcher)
    return build_video_anchors(rows, matches)


def refine_member_timeline(segments, decisions, labels, previews, face_results, matcher, *, video_path=None, seed_anchors=(), fallback_names=None, cut_times=()):
    output = _refine_member_scopes(segments, decisions, labels, previews, face_results, matcher,
                                   video_path=video_path, seed_anchors=seed_anchors, fallback_names=fallback_names, cut_times=cut_times)
    _merge_continuous_named(output, matcher, video_path=video_path)
    _keep_unidentified_in_review_bucket(output)
    return output


def refine_unresolved_with_names(primary, names, matcher, *, video_path=None):
    """Reconsider provisional unknown cuts using the second model's evidence.

    A first-pass boundary is not an identity boundary until names support it.
    Pool adjacent unknown scopes before applying the unchanged face-change,
    coverage and repeated-name checks. Confirmed scopes remain fixed.
    """
    keys = ('segments', 'decisions', 'labels', 'previews', 'evidence', 'preview_sources')
    output = {**primary, **{key: [] for key in keys}, 'accurate_indices': [],
              'fallback_names': {}, 'secondary_refinements': []}
    accurate = set(primary['accurate_indices'])
    groups = []
    for index, (seg, decision) in enumerate(zip(primary['segments'],primary['decisions'],strict=True)):
        previous = groups[-1][-1] if groups else None
        if (previous is not None and not decision.reference_id
                and not primary['decisions'][previous].reference_id
                and abs(primary['segments'][previous].end-seg.start) <= 1e-6):
            groups[-1].append(index)
        else:
            groups.append([index])
    for group in groups:
        index = group[0]
        seg = replace(primary['segments'][index], end=primary['segments'][group[-1]].end,
                      bboxes=[row for i in group for row in primary['segments'][i].bboxes])
        decision = primary['decisions'][index]
        evidence = [row for i in group for row in primary['evidence'][i]]
        local_names = {row.frame_index:names[row.frame_index] for row, _ in evidence
                       if not decision.reference_id and row.frame_index in names
                       and seg.start <= row.time_seconds < seg.end and _valid(row)}
        if not local_names:
            for i in group:
                if i in accurate:
                    output['accurate_indices'].append(len(output['segments']))
                for key in keys:
                    output[key].append(primary[key][i])
            continue
        thumbnails, owned = (ChainMap(*(primary['preview_sources'][i][k] for i in group)) for k in (0,1))
        local = _refine_member_scopes(
            [seg],[decision],[primary['labels'][index]],[primary['previews'][index]],
            [SimpleNamespace(owned_observations=[row for row,_ in evidence],
                             owned_thumbnails=thumbnails,owned_previews=owned)],matcher,
            video_path=video_path,seed_anchors=primary['anchors'],fallback_names=local_names, cut_times=primary.get('cut_times', ()))
        offset = len(output['segments'])
        output['accurate_indices'].extend(offset+i for i in local['accurate_indices'])
        for key in keys:
            output[key].extend(local[key])
        output['fallback_names'].update(local_names)
        if len(group) > 1:
            for audit in local['audit']:
                audit['reconsidered_unknown_ranges'] = [
                    (primary['segments'][i].start,primary['segments'][i].end) for i in group]
        output['secondary_refinements'].extend(local['audit'])
    _merge_continuous_named(output,matcher,video_path=video_path,preserve_named=True)
    _keep_unidentified_in_review_bucket(output)
    return output


def recover_final_face_edges(output, matcher, *, video_path=None, handoffs=None,
                             joint_matches=None, frame_records=()):
    """Extend final named clips using frozen neighboring face observations.

    Only unresolved output may change. A clip label is never a face vote, and
    a newly named interval cannot become evidence for the next interval.
    """
    keys = ('segments', 'decisions', 'labels', 'previews', 'evidence', 'preview_sources')
    frozen_names = dict(output.get('fallback_names', {}))
    frozen_names.update({row.frame_index:name for rows in output['evidence'] for row,name in rows
                         if name and _valid(row)})
    result = {**output, **{key:[] for key in keys}, 'accurate_indices':[]}
    changes=[]
    recovered_ranges=[]
    for index,(segment,decision) in enumerate(zip(output['segments'],output['decisions'],strict=True)):
        own=output['evidence'][index]
        hits={row.frame_index:frozen_names[row.frame_index] for row,_ in own
              if _valid(row) and row.frame_index in frozen_names}
        context=[index]
        start,end=segment.start,segment.end
        if not decision.reference_id and hits:
            for neighbor in (index-1,index+1):
                if not 0 <= neighbor < len(output['segments']): continue
                part=output['segments'][neighbor]
                if not output['decisions'][neighbor].reference_id: continue
                gap=segment.start-part.end if neighbor<index else part.start-segment.end
                if abs(gap)>1e-6: continue
                context.append(neighbor)
                if neighbor<index: start=max(part.start,segment.start-MAX_SUPPORT_GAP_SECONDS)
                else: end=min(part.end,segment.end+MAX_SUPPORT_GAP_SECONDS)
        candidate=None
        if len(context)>1:
            context.sort()
            rows=[row for i in context for row,_ in output['evidence'][i] if start<=row.time_seconds<end]
            thumbnails,previews=(ChainMap(*(output['preview_sources'][i][k] for i in context)) for k in (0,1))
            scope=replace(segment,start=start,end=end,bboxes=[box for i in context
                for box in output['segments'][i].bboxes if start<=box[0]<end])
            proposal=_refine_member_scopes([scope],[decision],[None],[[]],
                [SimpleNamespace(owned_observations=rows,owned_thumbnails=thumbnails,owned_previews=previews)],
                matcher,video_path=video_path,seed_anchors=output['anchors'],fallback_names=frozen_names,
                cut_times=output.get('cut_times', ()))
            pieces=[]
            for part,assignment,evidence in zip(proposal['segments'],proposal['decisions'],proposal['evidence'],strict=True):
                left,right=max(segment.start,part.start),min(segment.end,part.end)
                if right<=left: continue
                selected=[(row,name) for row,name in evidence if left<=row.time_seconds<right]
                votes={hits[row.frame_index] for row,_ in selected if row.frame_index in hits}
                supported=True
                for row,_ in selected:
                    if row.frame_index not in hits: continue
                    agreeing=[other for other in rows if _valid(other)
                        and frozen_names.get(other.frame_index)==assignment.reference_id
                        and 0<abs(other.time_seconds-row.time_seconds)<=MAX_SUPPORT_GAP_SECONDS
                        and 1.-float(row.embedding @ other.embedding)<=.6]
                    if not any(.15<=abs(a.time_seconds-b.time_seconds)<=MAX_SUPPORT_GAP_SECONDS
                               for j,a in enumerate(agreeing) for b in agreeing[j+1:]):
                        supported=False
                        break
                # Context alone cannot name a face-less edge or erase a contrary
                # original named face inside the unknown interval. A single bad
                # name must also match independent frozen neighboring faces.
                touches_named_neighbor=any(i!=index and output['decisions'][i].reference_id==assignment.reference_id
                    and (abs(output['segments'][i].end-left)<=1e-6
                         or abs(output['segments'][i].start-right)<=1e-6) for i in context)
                if (not assignment.reference_id or votes!={assignment.reference_id}
                        or not supported or not touches_named_neighbor):
                    assignment=decision
                pieces.append((replace(part,start=left,end=right,
                    bboxes=[box for box in part.bboxes if left<=box[0]<right]),assignment,selected))
            if any(assignment.reference_id for _,assignment,_ in pieces): candidate=pieces
        if candidate is None:
            if index in output['accurate_indices']:result['accurate_indices'].append(len(result['segments']))
            for key in keys:result[key].append(output[key][index])
            continue
        for part,assignment,selected in candidate:
            if assignment.reference_id:
                recovered_ranges.append((part.start,part.end,assignment.reference_id))
            result['accurate_indices'].append(len(result['segments']))
            result['segments'].append(part);result['decisions'].append(assignment)
            result['labels'].append(output['labels'][index]);result['evidence'].append(selected)
            sources=output['preview_sources'][index]
            result['preview_sources'].append(sources)
            ranked=sorted((row for row,_ in selected),key=lambda row:row.quality,reverse=True)
            result['previews'].append([sources[0].get(row.frame_index) or sources[1][row.frame_index]
                for row in ranked if row.frame_index in sources[0] or row.frame_index in sources[1]][:5])
        changes.append(dict(start=segment.start,end=segment.end,context_start=start,context_end=end,
            reason='original_neighbor_face_support'))
    if changes:
        from .output_continuity import coalesce_named_output
        result['fallback_names']=frozen_names
        merged,audit=coalesce_named_output(result,matcher,handoffs=handoffs,
            joint_matches=joint_matches,frame_records=frame_records)
        original_named=[(s,d.reference_id) for s,d in zip(output['segments'],output['decisions'])
                        if d.reference_id]
        # Commit only when every recovered part actually extends an original
        # named clip under the final handoff/identity consistency rules.
        for left,right,name in recovered_ranges:
            if not any(d.reference_id==name and s.start<=left+1e-6 and s.end>=right-1e-6
                       and any(old_name==name and min(s.end,old.end)>max(s.start,old.start)+1e-6
                               for old,old_name in original_named)
                       for s,d in zip(merged['segments'],merged['decisions'])):
                return dict(output,edge_recoveries=[],edge_recovery_reason='final_join_rejected')
        result=merged
        result['edge_recovery_joins']=audit['joins']
    result['edge_recoveries']=changes
    return result


def _refine_member_scopes(segments, decisions, labels, previews, face_results, matcher, *, video_path=None, seed_anchors=(), fallback_names=None, cut_times=()):
    """Partition every main scope, including previously named and unsplit ones."""
    prepared, all_rows, all_matches = _prepare_observations(segments, face_results, matcher)
    anchors = list({(name, row.frame_index): (name, row)
                    for name, row in [*seed_anchors, *build_video_anchors(all_rows, all_matches)]}.values())
    fallback_names = fallback_names or {}
    output = {'segments': [], 'decisions': [], 'labels': [], 'previews': [], 'fallback_names': fallback_names,
              'accurate_indices': [], 'audit': [], 'evidence': [], 'anchors': anchors, 'preview_sources': [],
              'cut_times': tuple(cut_times)}
    next_label = max((label for label in labels if label is not None), default=0) + 1
    for index, (seg, baseline, label, images, result, prepared_rows) in enumerate(zip(
            segments, decisions, labels, previews, face_results, prepared, strict=True)):
        rows, matches = prepared_rows
        names = []
        for row, match in zip(rows, matches, strict=True):
            name = match.reference_id if _valid(row) else None
            if _valid(row) and not name:
                name = match_video_anchors(row, anchors)
                if not name:
                    name = _window_name(row, rows, matches, seg, matcher, f'main-{index}')
                if not name:
                    # Only names cross the model boundary. Secondary vectors
                    # never enter the primary gallery or become video anchors.
                    name = fallback_names.get(row.frame_index)
            names.append(name)
        ranges = _named_ranges(seg, rows, names, cut_times=cut_times)
        boundaries = _identity_boundaries(seg, rows, names, ranges, cut_times=cut_times)
        if video_path and boundaries:
            changes = [b for b in boundaries if b['reason'] in ('repeated_reference_change', 'repeated_face_change')
                       and b['right_time']-b['left_time'] <= .65]
            refined = iter(refine_switch_boundaries(video_path, changes))
            adjusted = []
            for old in boundaries:
                new = next(refined) if old in changes else old
                score = new.get('visual_difference', 0)
                if score >= 20.:
                    adjusted.append(new)
                elif ('visual_peak_time' in new and score >= 6.
                      and score >= 3.*new['visual_median_difference']):
                    # Similar stage backgrounds can keep a real shot change
                    # below the absolute threshold. Require an isolated spike.
                    adjusted.append({**new, 'time':new['visual_peak_time'],
                                     'boundary_frame_index':new['visual_peak_frame_index']})
                else:
                    adjusted.append(old)
            boundaries = _select_boundaries(seg, adjusted)
        parts = split_segment(seg, boundaries)
        assignments = []
        joined_named_parts = []
        applied = bool(rows)
        if not applied:
            # An expanded body crop can include a different performer's face.
            # A legacy crop match cannot name the main body without ownership.
            unresolved = SegmentReferenceDecision(None, 'unmatched', 'main_face_unconfirmed')
            parts, assignments = [seg], [unresolved]
            output['segments'].append(seg); output['decisions'].append(unresolved)
            output['labels'].append(label); output['previews'].append(images)
            output['evidence'].append([])
            output['preview_sources'].append(({}, {}))
        else:
            resolved = []
            for part in parts:
                selected = [(o, name) for o, name in zip(rows, names, strict=True)
                            if part.start <= o.time_seconds < part.end]
                assignment = _assign_piece(part, selected, matcher, anchors, f'main-{index}')
                # A mixed or unresolved interval can still contain a clear
                # member appearance. Partition only that failed interval at
                # evidence edges; coherent named runs keep their full length.
                edges = _named_evidence_boundaries(part, ranges) if not assignment.reference_id else []
                if edges:
                    boundaries.extend(edges)
                    for local in split_segment(part, edges):
                        own = [(o, name) for o, name in selected if local.start <= o.time_seconds < local.end]
                        resolved.append((local, _assign_piece(local, own, matcher, anchors, f'main-{index}')))
                else:
                    resolved.append((part, assignment))
            continuous = []
            for part, assignment in resolved:
                if continuous and assignment.reference_id:
                    left, old = continuous[-1]
                    left_rows = [o for o in rows if left.start <= o.time_seconds < left.end and _valid(o)]
                    right_rows = [o for o in rows if part.start <= o.time_seconds < part.end and _valid(o)]
                    if (old.reference_id == assignment.reference_id and abs(left.end-part.start) <= 1e-6
                            and left_rows and right_rows
                            and 0 < right_rows[0].time_seconds-left_rows[-1].time_seconds <= MAX_SUPPORT_GAP_SECONDS):
                        union = replace(left,end=part.end,bboxes=left.bboxes+part.bboxes)
                        selected = [(o,n) for o,n in zip(rows,names,strict=True)
                                    if union.start <= o.time_seconds < union.end]
                        pooled = _assign_piece(union,selected,matcher,anchors,f'main-{index}-joined')
                        # A view-change proposal is not a final member boundary.
                        # Pooling must still reject a repeated incompatible face.
                        if pooled.reference_id == assignment.reference_id:
                            joined_named_parts.append(dict(time=part.start,name=pooled.reference_id,
                                                           start=union.start,end=union.end))
                            continuous[-1] = (union,pooled)
                            continue
                continuous.append((part,assignment))
            resolved = continuous
            parts = [part for part, _ in resolved]
            boundaries.sort(key=lambda b: b['time'])
            for part, assignment in resolved:
                selected = [(o, name) for o, name in zip(rows, names, strict=True)
                            if part.start <= o.time_seconds < part.end]
                assignments.append(assignment)
                output['evidence'].append(selected)
                output['accurate_indices'].append(len(output['segments']))
                output['segments'].append(part); output['decisions'].append(assignment)
                output['labels'].append(next_label if selected else None); next_label += 1
                owned = getattr(result, 'owned_previews', {})
                thumbnails = getattr(result, 'owned_thumbnails', {})
                output['preview_sources'].append((thumbnails, owned))
                candidates = sorted((o for o, _ in selected), key=lambda o: o.quality, reverse=True)
                output['previews'].append([thumbnails.get(o.frame_index) or owned[o.frame_index]
                                          for o in candidates if o.frame_index in thumbnails or o.frame_index in owned][:5])
        output['audit'].append({'parent_index': index, 'parent_start': seg.start, 'parent_end': seg.end,
                                'baseline': asdict(baseline), 'boundaries': boundaries, 'applied': applied,
                                'named_ranges': ranges,
                                'joined_named_parts': joined_named_parts,
                                'pieces': [{'start': p.start, 'end': p.end, 'decision': asdict(d)}
                                           for p, d in zip(parts, assignments, strict=True)]})
    _keep_unidentified_in_review_bucket(output)
    return output


def _merge_continuous_named(output, matcher, *, video_path=None, preserve_named=False):
    """A body track boundary alone does not end a confirmed member's part."""
    groups = []
    for index, (segment, decision, evidence) in enumerate(zip(
            output['segments'], output['decisions'], output['evidence'], strict=True)):
        join = False
        if groups and decision.reference_id:
            previous = groups[-1][-1]
            before = output['segments'][previous]
            old = output['decisions'][previous]
            left = [o for o, _ in output['evidence'][previous] if _valid(o)]
            right = [o for o, _ in evidence if _valid(o)]
            join = (old.reference_id == decision.reference_id
                    and abs(before.end-segment.start) <= 1e-6 and left and right
                    and 0 < right[0].time_seconds-left[-1].time_seconds <= MAX_SUPPORT_GAP_SECONDS)
        if join:
            groups[-1].append(index)
        else:
            groups.append([index])
    keys = ('segments', 'decisions', 'labels', 'previews', 'evidence', 'preview_sources')
    merged = {key: [] for key in keys}
    accurate = set(output['accurate_indices'])
    merged_accurate, audit = [], []
    for group in groups:
        first, last = group[0], group[-1]
        for key in keys:
            merged[key].append(output[key][first])
        if any(i in accurate for i in group):
            merged_accurate.append(len(merged['segments'])-1)
        if len(group) == 1:
            continue
        segment = replace(output['segments'][first], end=output['segments'][last].end,
                          bboxes=[row for i in group for row in output['segments'][i].bboxes])
        evidence = [row for i in group for row in output['evidence'][i]]
        thumbnails = ChainMap(*(output['preview_sources'][i][0] for i in group))
        owned = ChainMap(*(output['preview_sources'][i][1] for i in group))
        # A short B appearance can contribute one observation to each parent.
        # Reconsider their combined evidence before accepting a continuous A:
        # the union may now prove B or an unidentified face at the boundary.
        combined = _refine_member_scopes(
            [segment], [output['decisions'][first]], [output['labels'][first]], [[]],
            [SimpleNamespace(owned_observations=[o for o, _ in evidence],
                             owned_thumbnails=thumbnails, owned_previews=owned)],
            matcher, video_path=video_path, seed_anchors=output['anchors'],
            fallback_names=output.get('fallback_names'), cut_times=output.get('cut_times', ()))
        if preserve_named and any(d.reference_id != output['decisions'][first].reference_id
                                  for d in combined['decisions']):
            # A secondary-only pass cannot demote a previously named interval
            # as a side effect of pooling it with a newly recovered neighbor.
            offset = len(merged['segments'])-1
            merged_accurate = [i for i in merged_accurate if i != offset]
            merged_accurate.extend(offset+j for j,i in enumerate(group) if i in accurate)
            for key in keys:
                merged[key][-1:] = [output[key][i] for i in group]
            continue
        combined_start = len(merged['segments'])-1
        merged_accurate = [i for i in merged_accurate if i != combined_start]
        merged_accurate.extend(combined_start+i for i in combined['accurate_indices'])
        for key in keys:
            merged[key][-1:] = combined[key]
        audit.append({'start': segment.start, 'end': segment.end,
                      'source_ranges': [(output['segments'][i].start, output['segments'][i].end) for i in group],
                      'refinement': combined['audit']})
    merged['labels'] = [i+1 if decision.reference_id else None for i, decision in enumerate(merged['decisions'])]
    output.update(merged, accurate_indices=merged_accurate, merged_main_runs=audit)


def _keep_unidentified_in_review_bucket(output):
    """A failed roster match is unresolved, not proof of a new person.

    This refinement is only used with registered member references. Preserve
    every unresolved interval and its evidence in the existing unknown bucket;
    reference-free anonymous clustering continues through the legacy pipeline.
    """
    for index, decision in enumerate(output['decisions']):
        if not decision.reference_id:
            output['labels'][index] = None
