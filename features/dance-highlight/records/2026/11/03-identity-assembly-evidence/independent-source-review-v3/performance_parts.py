"""Assemble Dance output parts from immutable recognition spans.

Recognition scopes describe where the face evidence supports a name. Output
parts additionally respect scene eligibility and main-role handoffs. Keep the
input scopes and their observations intact so a merged part never becomes new
recognition evidence. Preparation remains a separate pipeline output.
"""
import time

from .scene_boundaries import project_main_at_scene_cuts, split_unidentified_at_handoffs

VERSION = 'performance_parts_v5_boundary_events'


def _project(identity, projected):
    indices = [i for i, _ in projected]
    result = dict(identity)
    result['segments'] = [part for _, part in projected]
    for key in ('decisions', 'labels'):
        result[key] = [identity[key][i] for i in indices]
    accurate = set(identity['accurate_indices'])
    result['accurate_indices'] = [i for i, old in enumerate(indices) if old in accurate]
    result.update(evidence=[], preview_sources=[], previews=[])
    for index, part in projected:
        selected = [(row, name) for row, name in identity['evidence'][index]
                    if part.start <= row.time_seconds < part.end]
        thumbnails, owned = identity['preview_sources'][index]
        candidates = sorted((row for row, _ in selected), key=lambda row: row.quality, reverse=True)
        result['previews'].append([thumbnails.get(row.frame_index) or owned[row.frame_index]
            for row in candidates if row.frame_index in thumbnails or row.frame_index in owned][:5])
        result['evidence'].append(selected)
        result['preview_sources'].append((thumbnails, owned))
    return result


def _span_inventory(identity):
    return [dict(id=i, range=[s.start, s.end], name=d.reference_id, reason=d.reason,
                 observation_frames=[o.frame_index for o, _ in identity['evidence'][i]])
            for i, (s, d) in enumerate(zip(identity['segments'], identity['decisions'], strict=True))]


def _part_inventory(output, spans):
    parts = []
    for segment, decision in zip(output['segments'], output['decisions'], strict=True):
        sources = [s for s in spans if s['range'][0] < segment.end and s['range'][1] > segment.start]
        newly_named = sum(max(0., min(s['range'][1], segment.end)-max(s['range'][0], segment.start))
                          for s in sources if not s['name']) if decision.reference_id else 0.
        parts.append(dict(range=[segment.start, segment.end], name=decision.reference_id,
                          source_spans=[s['id'] for s in sources], newly_named_seconds=newly_named))
    return parts


def build_performance_parts(identity, *, eligibility, matcher, frame_records,
                            frozen_observations, joint_matches, handoffs, fps, video_path,
                            scene_changes, cut_frames, group_segments, mask_refinement,
                            role_observations=(), video_size=None, sample_step=4,
                            secondary_matches=()):
    """Single output assembly point; no face/model service or new anchors.

    ``identity`` is a frozen input. Its current names are not permission to fill
    an unseen gap. Existing verified edge/name joins retain their full guards.
    The provenance audit records any newly named time separately from merging
    already named spans. Missing handoff evidence remains distinct from [].
    """
    spans = _span_inventory(identity)
    projected, projection = project_main_at_scene_cuts(identity['segments'], eligibility,
        fps=fps, cut_times=[c['cut_time'] for c in scene_changes])
    projected, handoff_audit = split_unidentified_at_handoffs(
        projected, identity['decisions'], handoffs or [])
    projection['unidentified_handoffs'] = handoff_audit
    result = _project(identity, projected)
    from .identity_projection import validate_identity_padding
    verified_cuts = None if cut_frames is None else sorted(set(cut_frames) |
        {round(change['cut_time']*fps) for change in scene_changes})
    result, padding_audit = validate_identity_padding(result, identity, projected,
        frame_records=frame_records, fps=fps, sample_step=sample_step,
        cut_frames=verified_cuts, handoffs=handoffs, matcher=matcher, joint_matches=joint_matches,
        frozen_observations=frozen_observations)
    projection['identity_padding'] = padding_audit
    continuity, named_seconds, edge_seconds, shot_seconds = {}, 0., 0., 0.
    if matcher is not None:
        from .shot_member_gaps import recover_shot_member_gaps
        from .observed_member_edges import recover_observed_member_edges
        from .member_timeline import recover_final_face_edges
        from .output_continuity import coalesce_named_output, coalesce_unknown_output
        from .named_boundaries import reconcile_named_boundaries
        started = time.perf_counter()
        result, shot_gaps = recover_shot_member_gaps(result, frame_records,
            frozen_observations, joint_matches, secondary_matches, matcher,
            video_path=video_path, fps=fps, sample_step=sample_step,
            cut_frames=verified_cuts, handoffs=handoffs,
            role_observations=role_observations, group_segments=group_segments)
        shot_seconds = time.perf_counter()-started
        started = time.perf_counter()
        result, observed_edges = recover_observed_member_edges(result, frame_records,
            frozen_observations, joint_matches, matcher, video_path=video_path, fps=fps,
            sample_step=sample_step, handoffs=handoffs, role_observations=role_observations,
            video_size=video_size)
        edge_seconds = time.perf_counter()-started
        result = recover_final_face_edges(result, matcher, video_path=video_path,
            handoffs=handoffs, joint_matches=joint_matches, frame_records=frame_records)
        result, continuity = coalesce_named_output(result, matcher,
            handoffs=handoffs, joint_matches=joint_matches, frame_records=frame_records,
            fps=fps, cut_frames=cut_frames, mask_refinement=mask_refinement)
        continuity['face_edge_recoveries'] = result.get('edge_recoveries', [])
        continuity['face_edge_joins'] = result.get('edge_recovery_joins', [])
        continuity['face_edge_reason'] = result.get('edge_recovery_reason')
        continuity['observed_member_edges'] = observed_edges
        continuity['shot_member_gaps'] = shot_gaps
        started = time.perf_counter()
        result, unknown_joins = coalesce_unknown_output(result, frame_records,
            frozen_observations, joint_matches, fps=fps, sample_step=sample_step,
            handoffs=handoffs, video_path=video_path)
        edge_seconds += time.perf_counter()-started
        continuity['unknown_main_joins'] = unknown_joins
        started = time.perf_counter()
        result, boundaries = reconcile_named_boundaries(result, frame_records,
            frozen_observations, joint_matches, matcher, video_path=video_path, fps=fps,
            group_segments=group_segments, handoffs=handoffs)
        from .incoming_identity_boundary import reconcile_incoming_identity_boundary
        result, incoming_boundary = reconcile_incoming_identity_boundary(result, frame_records,
            frozen_observations, joint_matches, matcher, fps=fps, sample_step=sample_step,
            cut_frames=verified_cuts, source_path=video_path, video_size=video_size,
            handoffs=handoffs)
        named_seconds = time.perf_counter()-started
        continuity['named_boundaries'] = boundaries
        continuity['incoming_identity_boundary'] = incoming_boundary
    # Final output policy only: the aligned edge cannot seed any recovery pass.
    from .part_boundary_events import coalesce_boundary_events
    result, event_audit = coalesce_boundary_events(result, identity,
        frame_records=frame_records, frozen_observations=frozen_observations,
        joint_matches=joint_matches, eligibility=eligibility, fps=fps,
        sample_step=sample_step, cut_frames=verified_cuts, handoffs=handoffs, matcher=matcher)
    projection['boundary_events'] = event_audit
    return result, dict(version=VERSION, identity_spans=spans,
                        parts=_part_inventory(result, spans), projection=projection,
                        continuity=continuity, named_boundary_seconds=named_seconds,
                        observed_continuity_seconds=edge_seconds, shot_gap_seconds=shot_seconds)
