"""Conservative Dance-only recovery from source-frame, pose-owned evidence.

Never promotes recovered queries to anchors. Existing names and group recipients
are left to the baseline adapter. Sparse matches cannot name a mixed main scope.
"""
from dataclasses import asdict
from functools import cached_property
import numpy as np
from clipper_face_core import (
    EmbeddingSpace, SourceEvidence, ReferenceSample, QueryEvidence, MatchPolicy,
    GalleryBuildError, build_gallery, match_reference,
)
from .reference_matcher import SegmentReferenceDecision
from clipper_face_core.matching import match_reference_views
from clipper_face_core.contracts import ReferenceGallery

RECOVERY_VERSION = 'dance_pose_reference_views_v2'


class _FrozenDanceGallery(ReferenceGallery):
    # Shared contracts freeze their fields and embedding arrays. Rehashing the
    # same complete photo inventory for every query is unnecessary in Dance.
    @cached_property
    def fingerprint(self):
        return super().fingerprint


class ReferenceObservationMatcher:
    def __init__(self, *, references, analysis_id, video_sha256, detector_sha256,
                 recognizer_sha256, config_sha256, backend_version, video_size, max_distance):
        space = EmbeddingSpace(
            recognizer_sha256, 'yunet5_arcface112_v1',
            'bgr_to_rgb_mean127_5_std127_5_auraface_v1', 'float32_l2_eps_1e-9',
            int(np.asarray(references[0].embedding).size), backend_version,
        )
        def source(**kwargs):
            values = dict(analysis_id=analysis_id, source_sha256=video_sha256,
                          observation_version=1, detector_sha256=detector_sha256,
                          config_sha256=config_sha256, adapter_version=RECOVERY_VERSION,
                          time_kind='still_image', time_seconds=None, pts=None, time_base=None,
                          frame_index=None, width=video_size[0], height=video_size[1], rotation=0,
                          bbox_px=None, track_id=None, scope_id=None, scope_range_seconds=None)
            values.update(kwargs)
            return SourceEvidence(**values)
        gallery = build_gallery(tuple(ReferenceSample(
                r.sample_id, r.reference_id,
                source(source_sha256=r.image_sha256, width=r.width, height=r.height),
                space, r.embedding, None) for r in references), space=space)
        gallery = _FrozenDanceGallery(gallery.space, gallery.entries, gallery.samples,
                                      gallery.failures, gallery.aggregation_version)
        self.policy = MatchPolicy(max_distance=min(.6, max_distance), min_margin=.08, minimum_support=2)
        self.space, self.source, self.gallery = space, source, gallery

    def match(self, observation, segment, scope_id):
        obs = observation
        query = QueryEvidence(
            f'{scope_id}:frame:{obs.frame_index}',
            self.source(time_kind='derived_seconds', time_seconds=obs.time_seconds,
                        frame_index=obs.frame_index, bbox_px=obs.face_bbox, track_id=str(obs.track_id),
                        scope_id=scope_id, scope_range_seconds=(segment.start, segment.end)),
            self.space, obs.embedding, obs.association, obs.failure, (),
        )
        direct = match_reference(query, self.gallery, self.policy)
        if direct.reference_id or direct.status == 'invalid':
            return direct
        # The average can hide a useful view. Recovery still needs two
        # distinct source photos and separation from every competing member.
        views = match_reference_views(query, self.gallery, self.policy)
        return views if views.reference_id else direct


def recover_reference_decision(*, baseline, segment, observations, references, scope_id,
                               analysis_id, video_sha256, detector_sha256, recognizer_sha256,
                               config_sha256, backend_version, video_size, max_distance):
    audit = {'version': RECOVERY_VERSION, 'accepted': False, 'reason': 'baseline_kept',
             'baseline': asdict(baseline), 'matches': []}
    if baseline.status == 'matched' or baseline.reason not in (
            'distance_exceeded', 'duplicate_cluster_distance_exceeded'):
        return baseline, audit
    def reject(reason):
        audit['reason'] = reason
        return baseline, audit
    if not references or not observations:
        return reject('no_observations')
    try:
        matcher = ReferenceObservationMatcher(
            references=references, analysis_id=analysis_id, video_sha256=video_sha256,
            detector_sha256=detector_sha256, recognizer_sha256=recognizer_sha256,
            config_sha256=config_sha256, backend_version=backend_version,
            video_size=video_size, max_distance=max_distance)
    except GalleryBuildError as exc:
        return reject(exc.reason)
    policy = matcher.policy
    unique = {}
    for obs in observations:
        # Multiple copies of a decoded frame cannot create independent support.
        if obs.frame_index in unique:
            return reject('duplicate_frame_evidence')
        unique[obs.frame_index] = obs
    hits, valid, names = [], [], set()
    for obs in sorted(unique.values(), key=lambda o: o.time_seconds):
        if not segment.start <= obs.time_seconds < segment.end:
            return reject('observation_outside_scope')
        match = matcher.match(obs, segment, scope_id)
        audit['matches'].append({'frame_index': obs.frame_index, 'time_seconds': obs.time_seconds,
                                 'track_id': obs.track_id, 'status': match.status,
                                 'reference_id': match.reference_id, 'reason': match.reason,
                                 'candidates': [asdict(c) for c in match.candidates], 'margin': match.margin})
        if obs.association == 'confirmed' and match.status != 'invalid':
            valid.append(obs)
        if match.reference_id:
            names.add(match.reference_id)
            hits.append((obs, match))
        elif match.reason in ('tied_references', 'insufficient_margin'):
            return reject('competing_reference_evidence')
    if len(names) > 1:
        return reject('conflicting_references')
    if not names:
        return reject('no_direct_support')
    # A scope may merge several body tracks. Every one needs direct support;
    # the majority cluster is deliberately not allowed to hide a minority track.
    required_tracks = {int(tid) for _, _, tid in segment.bboxes}
    if not required_tracks or not required_tracks.issubset({o.track_id for o, _ in hits}):
        return reject('unverified_body_run')
    thirds = [[] for _ in range(3)]
    for obs, _ in hits:
        bucket = min(2, int(3 * (obs.time_seconds - segment.start) / (segment.end - segment.start)))
        thirds[bucket].append(obs.time_seconds)
    if any(len(times) < 2 or max(times) - min(times) < .15 for times in thirds):
        return reject('insufficient_temporal_coverage')
    # An unregistered second face would otherwise never vote against the name.
    # Require every usable face to agree with at least two directly named frames.
    # No transitive chaining through new or weak observations is permitted.
    for obs in valid:
        distances = sorted(1. - float(np.dot(obs.embedding, hit.embedding))
                           for hit, _ in hits if hit.frame_index != obs.frame_index)
        if len(distances) < 2 or distances[1] > .6:
            return reject('inconsistent_face_scope')
    if len(valid) != len(observations):
        return reject('incomplete_owned_scope')
    name = next(iter(names))
    distances = [next(c.distance for c in match.candidates if c.reference_id == name)
                 for _, match in hits]
    distance = float(np.mean(distances))
    audit.update(accepted=True, reason='pose_observation_consensus', support_frames=[o.frame_index for o,_ in hits])
    return SegmentReferenceDecision(name, 'matched', audit['reason'], distance, name,
                                    distance, policy.max_distance), audit
