"""Source-frame evidence retained before Dance's legacy track averaging."""
from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np

Box = tuple[float, float, float, float]


@dataclass(frozen=True)
class FaceObservation:
    frame_index: int
    time_seconds: float  # derived from frame index / fps, not container PTS
    track_id: int
    body_bbox: Box
    roi_bbox: Box
    face_bbox: Box | None = None
    landmarks: tuple[tuple[float, float], ...] = ()
    candidate_boxes: tuple[Box, ...] = ()
    embedding: np.ndarray | None = field(default=None, repr=False)
    quality: float = 0.0
    detector_score: float = 0.0
    face_sharpness: float = 0.0
    failure: str | None = None
    association: str = 'unassigned'
    detection_rotation_degrees: float = 0.0


def face_body_association(observation: FaceObservation, bodies) -> str:
    """Accept only a unique geometric head/body pairing, not identity from a track ID."""
    face = observation.face_bbox
    if face is None or observation.failure:
        return 'unassigned'

    def in_head(box, body):
        cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
        return (body[0] <= cx <= body[2] and
                body[1] <= cy <= body[1] + .45 * (body[3] - body[1]))

    own = observation.body_bbox
    if not in_head(face, own) or not any(np.allclose(b, own, atol=.02, rtol=0) for b in bodies):
        return 'unassigned'
    owners = [b for b in bodies if in_head(face, b)]
    faces = [b for b in observation.candidate_boxes if in_head(b, own)]
    return 'confirmed' if len(owners) == 1 and len(faces) == 1 else 'ambiguous'


def select_pose_face(boxes, body, record):
    """Use measured head points; overlapping heads veto ownership.

    A body track is only a lookup hint. No identity is inferred from its ID.
    The same-frame pose must uniquely agree with the sampled body box.
    """
    from .track import bbox_iou
    if record is None or len(record.person_bboxes) != len(record.person_head_keypoints):
        return None, 'pose_context_missing'
    owners = [i for i, value in enumerate(record.person_bboxes) if bbox_iou(body, value) >= .7]
    if len(owners) != 1:
        return None, 'pose_body_unconfirmed'
    own = owners[0]
    heads = []
    for value in record.person_head_keypoints:
        points = np.asarray(value, dtype=np.float32)
        if points.ndim != 2 or points.shape[1] != 3:
            heads.append(np.empty((0, 2)))
        else:
            points = points[:5]
            heads.append(points[np.isfinite(points).all(axis=1) & (points[:, 2] >= .5), :2])
    if len(heads[own]) < 2:
        return None, 'pose_head_unconfirmed'
    accepted, conflict = [], False
    for index, (x1, y1, x2, y2) in enumerate(boxes):
        counts = [int(np.sum((pts[:, 0] >= x1) & (pts[:, 0] <= x2) &
                             (pts[:, 1] >= y1) & (pts[:, 1] <= y2))) for pts in heads]
        if counts[own] >= 2:
            if any(n >= 2 for j, n in enumerate(counts) if j != own):
                conflict = True
            else:
                accepted.append(index)
    if conflict or len(accepted) > 1:
        return None, 'pose_face_ambiguous'
    return (accepted[0], None) if accepted else (None, 'pose_face_missing')


def write_face_evidence(path, *, input_video, config, face_service, results, records, references, refinement=(), visible_refinement=(), main_result_count=None, secondary_refinement=None, body_continuity_refinement=None, mask_continuity_refinement=None, main_selection_refinement=None, scene_boundary_refinement=None, scene_context_refinement=None, native_scene_refinement=None, output_continuity_refinement=None):
    """Local evidence sidecar; never writes embeddings into UI meta or job logs."""
    from dataclasses import asdict
    from pathlib import Path
    import hashlib
    import json
    import sys
    import cv2
    import onnxruntime
    from . import face_cluster, pose_engine, pipeline, reference_matcher, main_identity, face_recovery, face_evidence, member_timeline, member_coverage
    from . import secondary_faces, segment, body_continuity, mask_continuity, mask_tracker, context_faces, camera_transitions, joint_identity, cut_face_link, sampled_face_link, pose_face_rotation, scene_boundaries
    from . import observed_main, main_face_link, main_role_timeline, scene_cut_proof, scene_context, temporal_support, native_scene, output_continuity
    from . import mask_frame_cache, stage_prominence, focal_composition, focal_output, incoming_context, face_runtime, opencv_acceleration, named_boundaries
    from . import observed_member_edges, performance_parts, shot_member_gaps, role_state, pose_observations, group_output, identity_projection, group_continuity, bounded_face_path, incoming_identity_boundary, part_boundary_events, ensemble_continuity
    from clipper_face_core import auraface
    from .face_models import sha256_file

    def serial(value):
        if isinstance(value, np.ndarray):
            return value.tolist()
        raise TypeError(type(value).__name__)
    modules = {module.__name__.rsplit('.', 1)[-1]: {
        'path': module.__file__, 'sha256': sha256_file(Path(module.__file__)),
    } for module in (face_cluster, pose_engine, pipeline, reference_matcher, auraface,
                    main_identity, face_recovery, face_evidence, member_timeline, member_coverage, secondary_faces, segment, body_continuity, mask_continuity, mask_tracker, context_faces, camera_transitions, joint_identity, cut_face_link, sampled_face_link, pose_face_rotation, scene_boundaries, observed_main, main_face_link, main_role_timeline, scene_cut_proof, scene_context, temporal_support, native_scene, output_continuity)}
    modules['mask_frame_cache'] = {'path': mask_frame_cache.__file__,
                                 'sha256': sha256_file(Path(mask_frame_cache.__file__))}
    for module in (stage_prominence, focal_composition, focal_output, incoming_context, face_runtime, opencv_acceleration, named_boundaries, observed_member_edges, performance_parts, shot_member_gaps, role_state, pose_observations, group_output, identity_projection, group_continuity, bounded_face_path, incoming_identity_boundary, part_boundary_events, ensemble_continuity):
        modules[module.__name__.rsplit('.', 1)[-1]] = {
            'path': module.__file__, 'sha256': sha256_file(Path(module.__file__))}
    session = getattr(getattr(face_service, '_recognizer', None), '_session', None)
    payload = {
        'schema_version': 'dance_face_evidence_v1',
        'runtime': {'python_executable': sys.executable, 'modules': modules,
                    'models': getattr(face_service, 'model_provenance', {}),
                    'opencv': cv2.__version__, 'onnxruntime': onnxruntime.__version__,
                    'recognizer_providers': session.get_providers() if session is not None else [],
                    'recognizer_stats': dict(getattr(session, 'stats', {})),
                    'detector_stats': dict(getattr(getattr(face_service, '_detector', None), 'stats', {})),
                    'opencv_face_acceleration': opencv_acceleration.runtime_status(face_service),
                    'opencv_cpu_parallelism': dict(getattr(face_service, 'cpu_runtime', {})),
                    'video_sha256': sha256_file(input_video),
                    'config_sha256': hashlib.sha256(repr(config).encode()).hexdigest()},
        'policy': {'recovery_applied': any(row['applied'] for row in refinement), 'time_kind': 'derived_seconds',
                   'pose_ownership': 'two_head_points_unique_owner_v1',
                   'pose_face_rotation': 'measured_eye_roll_v1',
                   'rotation_retry_below_detector_score': .9, 'rotation_eye_min_confidence': .5,
                   'rotation_min_eye_separation_px': 4., 'rotation_absolute_degrees': [15.,75.]},
        'identity_refinement': refinement,
        'main_selection_refinement': main_selection_refinement or {},
        'secondary_reference_refinement': secondary_refinement or {},
        'body_continuity_refinement': body_continuity_refinement or {},
        'mask_continuity_refinement': mask_continuity_refinement or {},
        'scene_boundary_refinement': scene_boundary_refinement or {},
        'scene_context_refinement': scene_context_refinement or {},
        'native_scene_refinement': native_scene_refinement or {},
        'output_named_continuity': output_continuity_refinement or {},
        'visible_member_refinement': visible_refinement,
        'main_result_count': len(results) if main_result_count is None else main_result_count,
        'references': [asdict(ref) for ref in references],
        'segments': [{'start': float(r.seg.start), 'end': float(r.seg.end),
                      'track_ids': getattr(r, 'track_ids', []),
                      'track_embeddings': r.track_embeddings,
                      'observations': [asdict(o) for o in getattr(r, 'observations', [])],
                      'owned_observations': [asdict(o) for o in getattr(r, 'owned_observations', [])]}
                     for r in results],
        'pose_heads': [{'time_seconds': r.t, 'body_boxes': r.person_bboxes,
                        'head_keypoints': r.person_head_keypoints,
                        'pose_keypoints': r.person_pose_keypoints,
                        'scene_kind': r.scene_kind, 'scene_reason': r.scene_reason,
                        'candidate_main_id': r.candidate_main_id,
                        'candidate_main_bbox': r.candidate_main_bbox} for r in records],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, default=serial), encoding='utf-8')
