"""Align output scene boundaries without changing observation timestamps.

The identity timeline can locate a camera cut between two pose observations.
The output scene mask must use that same edge, otherwise the first one or two
frames of a wide shot become an unsupported solo clip.
"""

from bisect import bisect_right
from dataclasses import replace
import math


def _confirmed_scene_cut(proof):
    if proof.get('spatial', {}).get('accepted'):
        return True
    structure = proof.get('structure', {})
    return (proof.get('cut') and structure.get('continuous') is False
            and structure.get('reason') not in
            ('insufficient_structure', 'insufficient_correspondence', 'no_structure_transform'))


def project_main_at_scene_cuts(segments, eligible, *, fps, cut_times):
    """Resolve subframe padding at verified cuts in output only.

    Identity support uses second-based padding; at fractional FPS its edge can
    miss an exact cut by a fraction of one frame. Only edges whose nearest
    source frame is this same verified cut may meet it. Real one-frame parts
    survive, and identity evidence/observations are never retimed.
    """
    from .segment import intersect_main_segments

    projected = intersect_main_segments(segments, eligible)
    audit = dict(output_edge_changes=[], zero_frame_output_parts=[])
    if not math.isfinite(fps) or fps <= 0:
        return projected, audit
    def frame_index(t):
        return math.floor(t * fps + .5 + 1e-9)
    cuts = {frame_index(t): t for t in cut_times}
    output = []
    for index, part in projected:
        start, end = (cuts.get(frame_index(t), t) for t in (part.start, part.end))
        if (start, end) != (part.start, part.end):
            audit["output_edge_changes"].append(dict(
                source_index=index, before=[part.start, part.end], after=[start, end]))
        if end <= start:
            audit["zero_frame_output_parts"].append(dict(
                source_index=index, start=part.start, end=part.end))
            continue
        output.append((index, replace(part, start=start, end=end,
            bboxes=[row for row in part.bboxes if start <= row[0] < end])))
    return output, audit


def split_unidentified_at_handoffs(projected, decisions, handoffs):
    """Keep observed main changes in unknown output without dividing names.

    Inference scopes remain intact. Source indices are retained for the
    existing evidence/thumbnail remapping after output projection.
    """
    by_time = {h['time']: h for h in handoffs if math.isfinite(h['time'])}
    output, changes = [], []
    for index, part in projected:
        cuts = sorted(t for t in by_time if part.start+1e-9 < t < part.end-1e-9) if not decisions[index].reference_id else []
        if not cuts:
            output.append((index, part))
            continue
        changes.extend(dict(source_index=index, **by_time[t]) for t in cuts)
        edges = [part.start, *cuts, part.end]
        for start, end in zip(edges, edges[1:]):
            output.append((index, replace(part, start=start, end=end,
                bboxes=[row for row in part.bboxes if start <= row[0] < end])))
    return output, dict(version='unknown_main_handoffs_v1', changes=changes)


def align_scene_segment_boundaries(
    records, main, groups, *, fps, cut_frames, sample_step, verify_cut
):
    audit = dict(version="scene_cut_alignment_v3_spatial", changes=[])
    if not math.isfinite(fps) or fps <= 0 or sample_step < 1:
        return main, groups, dict(audit, reason="invalid_source_cadence")
    cuts = sorted(set(cut_frames))
    boundaries = {}
    for left, right in zip(records, records[1:]):
        if {left.scene_kind, right.scene_kind} != {"main", "group"}:
            continue
        lower, upper = round(left.t * fps), round(right.t * fps)
        # Missing pose samples leave the intervening scene unobserved.
        if not 0 < upper - lower <= sample_step:
            continue
        candidates = cuts[bisect_right(cuts, lower) : bisect_right(cuts, upper)]
        # Multiple edges may be flashes or an unobserved intermediate shot.
        if len(candidates) != 1 or candidates[0] == upper:
            continue
        proof = verify_cut(candidates[0])
        if not _confirmed_scene_cut(proof):
            continue
        edge = candidates[0] / fps
        boundaries[right.t] = edge
        audit["changes"].append(
            dict(
                observed_time=right.t,
                cut_time=edge,
                cut_frame=candidates[0],
                from_scene=left.scene_kind,
                to_scene=right.scene_kind,
                source_proof=proof,
            )
        )

    def aligned(segments):
        output = []
        for segment in segments:
            start = boundaries.get(segment.start, segment.start)
            end = boundaries.get(segment.end, segment.end)
            output.append(
                replace(
                    segment,
                    start=start,
                    end=end,
                    bboxes=[row for row in segment.bboxes if start <= row[0] < end],
                )
            )
        return output

    # Legacy soft-group exports may overlap main clips. Their duration is not
    # the amount of time the strict scene mask excludes from solo output.
    scene_group_ranges = [
        dict(start=boundaries.get(left.t, left.t), end=boundaries.get(right.t, right.t))
        for left, right in zip(records, records[1:])
        if left.scene_kind == "group"
    ]
    return (
        aligned(main),
        aligned(groups),
        dict(
            audit,
            reason="complete",
            scene_group_ranges=scene_group_ranges,
            scene_group_seconds=sum(r["end"] - r["start"] for r in scene_group_ranges),
        ),
    )


def align_scene_segments_from_source(
    records, main, groups, *, video_path, fps, cut_frames, sample_step, proof_cache=None
):
    """Verify only the exact source pairs bracketing an observed role change."""
    import cv2
    from .camera_transitions import classify_transition
    from .scene_cut_proof import spatial_cut_candidate, spatial_cut_evidence

    from .source_reader import SourceFrameReader
    reader = None
    # The caller owns this cache for one immutable source and one job.
    if proof_cache is None:
        proofs = {}
    else:
        from pathlib import Path
        path = Path(video_path).resolve()
        try:
            stat = path.stat()
            version = (stat.st_size, stat.st_mtime_ns)
        except OSError:
            version = None
        signature = (str(path), fps, version)
        if proof_cache.get('source') != signature:
            proof_cache.clear()
            proof_cache['source'] = signature
        proofs = proof_cache.setdefault('frames', {})
    inventory = "provided_and_scene_brackets" if cut_frames is not None else "complete_scene_brackets"

    def verify(frame):
        nonlocal reader
        if frame in proofs:
            return proofs[frame]
        if reader is None:
            reader = SourceFrameReader(video_path, fps)
        before, after = reader.get(frame - 1), reader.get(frame)
        proof = classify_transition(before, after)
        if not _confirmed_scene_cut(proof) and spatial_cut_candidate(before, after):
            count = reader.cap.get(cv2.CAP_PROP_FRAME_COUNT)
            past_end = math.isfinite(count) and count > 0 and frame + 4 >= round(count)
            if frame < 5 or past_end:
                proof = dict(proof, spatial=dict(accepted=False, reason='incomplete_spatial_context'))
            else:
                images = [reader.get(index) for index in range(frame - 5, frame + 5)]
                proof = dict(proof, spatial=spatial_cut_evidence(images))
        proofs[frame] = proof
        return proofs[frame]

    try:
        # Color inventory can miss same-stage edits. Inspect every pair only
        # within adjacent main/group brackets; identity inventory is untouched.
        cut_frames = list(cut_frames or ())
        if math.isfinite(fps) and fps > 0 and sample_step >= 1:
            for left, right in zip(records, records[1:]):
                if {left.scene_kind, right.scene_kind} != {"main", "group"}:
                    continue
                lower, upper = round(left.t * fps), round(right.t * fps)
                if 0 < upper - lower <= sample_step:
                    for frame in range(lower + 1, upper + 1):
                        proof = verify(frame)
                        if proof.get('cut') or proof.get('spatial', {}).get('accepted'):
                            cut_frames.append(frame)
        aligned_main, aligned_groups, audit = align_scene_segment_boundaries(
            records,
            main,
            groups,
            fps=fps,
            cut_frames=cut_frames,
            sample_step=sample_step,
            verify_cut=verify,
        )
        return aligned_main, aligned_groups, dict(audit, cut_inventory=inventory,
            source_reads=dict(reader.stats) if reader is not None else {})
    except (OSError, ValueError, RuntimeError, cv2.error) as error:
        return (
            main,
            groups,
            dict(
                version="scene_cut_alignment_v3_spatial",
                reason="source_unavailable",
                changes=[],
                error_type=type(error).__name__,
            ),
        )
    finally:
        if reader is not None:
            reader.close()
