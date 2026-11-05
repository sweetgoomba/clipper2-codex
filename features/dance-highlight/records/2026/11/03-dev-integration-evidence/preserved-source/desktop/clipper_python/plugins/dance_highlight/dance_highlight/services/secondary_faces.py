"""Independent SFace evidence for Dance main faces, including existing names.

SFace and AuraFace vectors never share a gallery. Names returned here still
need repeated time-local support in member_timeline; they cannot seed its
primary video anchors.
"""
from bisect import bisect_right
from collections import defaultdict
from dataclasses import replace
import numpy as np

SECONDARY_VERSION = 'sface_main_revalidation_v6_independent_pair'


def _normalized(vector):
    value = np.asarray(vector, dtype=np.float32).reshape(-1)
    norm = float(np.linalg.norm(value))
    return value / norm if np.isfinite(value).all() and norm > 1e-9 else None


def build_secondary_gallery(samples, roster):
    groups, owners = defaultdict(dict), {}
    dimension = None
    for name, source_hash, vector in samples:
        value = _normalized(vector)
        if value is None:
            continue
        if (source_hash in owners and owners[source_hash] != name
                or dimension is not None and value.size != dimension):
            return None
        dimension = value.size
        owners[source_hash] = name
        groups[name][source_hash] = value
    if not roster or any(len(groups[name]) < 2 for name in roster):
        return None
    gallery = {name: _normalized(np.mean(list(groups[name].values()), axis=0)) for name in roster}
    return gallery if all(value is not None for value in gallery.values()) else None


def match_secondary_vector(vector, gallery):
    value = _normalized(vector)
    if value is None or not gallery or any(v.size != value.size for v in gallery.values()):
        return dict(name=None, reason='invalid_secondary_embedding', candidates=[])
    ranked = sorted((max(0., min(2., 1.-float(value @ center))), name) for name, center in gallery.items())
    distance, name = ranked[0]
    margin = ranked[1][0]-distance if len(ranked) > 1 else None
    # OpenCV SFace's published cosine similarity threshold is .363. A separate
    # roster margin and repeated source instants are also required by Dance.
    accepted = distance <= .637 and (margin is None or margin >= .08)
    return dict(name=name if accepted else None, distance=distance, margin=margin,
                reason='secondary_reference_match' if accepted else 'secondary_reference_rejected',
                candidates=[dict(name=n, distance=d) for d, n in ranked])


def unresolved_observations(output):
    from .member_timeline import _valid
    return {row.frame_index: row
            for segment, decision, evidence in zip(output['segments'], output['decisions'], output['evidence'], strict=True)
            if not decision.reference_id
            for row, _ in evidence
            if segment.start <= row.time_seconds < segment.end and _valid(row)
            and row.face_bbox is not None and len(row.landmarks) == 5}


def confirmed_secondary_anchors(primary_anchors, vectors, gallery):
    """Frozen direct-photo agreement in both models, never recovered names."""
    candidates = [(name,replace(row,embedding=vectors[row.frame_index]))
                  for name,row in primary_anchors if row.frame_index in vectors
                  and match_secondary_vector(vectors[row.frame_index],gallery)['name'] == name]
    return [(name,row) for name,row in candidates if any(
        other_name == name and .15 <= abs(other.time_seconds-row.time_seconds) <= .6
        for other_name,other in candidates)]


def match_secondary_video(row, anchors, gallery):
    from .temporal_support import independent_pair
    # Exclude the query's neighborhood. Two views from another source time
    # must agree, and every roster member must participate in the comparison.
    candidates = []
    for name in gallery:
        values = [(1.-float(row.embedding @ other.embedding),other.time_seconds,other.frame_index)
                        for other_name,other in anchors if other_name == name
                        and abs(other.time_seconds-row.time_seconds) > 2.]
        pair = independent_pair(values)
        if pair is None:
            return dict(name=None,reason='incomplete_secondary_video_gallery',candidates=[])
        first,second = pair
        candidates.append(dict(name=name,distance=max(first[0],second[0]),support_frames=[first[2],second[2]]))
    candidates.sort(key=lambda c:c['distance'])
    if not candidates:
        return dict(name=None,reason='incomplete_secondary_video_gallery',candidates=[])
    best = candidates[0]
    margin = candidates[1]['distance']-best['distance'] if len(candidates)>1 else None
    accepted = best['distance'] <= .5 and (margin is None or margin >= .08)
    return dict(name=best['name'] if accepted else None,distance=best['distance'],margin=margin,
                reason='secondary_video_match' if accepted else 'secondary_video_rejected',candidates=candidates)


def secondary_window_matches(scopes, targets, vectors, matches, gallery, *, video_anchors=(), cut_frames=None):
    """Reduce short-lived feature noise without crossing a primary boundary.

    All windows use the frozen per-frame matches. A recovered window cannot
    supply support or manufacture agreement for another window.
    """
    from .member_timeline import _valid
    cuts = sorted(set(cut_frames)) if cut_frames is not None else None
    recovered = {}
    for start,end in scopes:
        rows = sorted((row for frame,row in targets.items()
                       if frame in vectors and _valid(row) and start <= row.time_seconds < end),key=lambda row:row.time_seconds)
        for row in rows:
            if matches[row.frame_index]['name']:
                continue
            nearby = [other for other in rows if abs(other.time_seconds-row.time_seconds) <= .4+1e-9
                      and (cuts is None or bisect_right(cuts,other.frame_index) == bisect_right(cuts,row.frame_index))]
            if len(nearby)<3 or nearby[-1].time_seconds-nearby[0].time_seconds<.15:
                continue
            features = np.asarray([vectors[other.frame_index] for other in nearby])
            center = _normalized(features.mean(axis=0))
            if center is None or max(1.-features @ center) > .35:
                continue
            match = match_secondary_vector(center,gallery)
            reason = 'secondary_reference_window_match'
            if not match['name'] and cuts is not None and video_anchors:
                independent = [(name,anchor) for name,anchor in video_anchors
                               if all(abs(anchor.time_seconds-other.time_seconds) > 2. for other in nearby)]
                match = match_secondary_video(replace(row,embedding=center),independent,gallery)
                reason = 'secondary_video_window_match'
            names = {matches[other.frame_index]['name'] for other in nearby}-{None}
            if match['name'] and (not names or names == {match['name']}):
                recovered[row.frame_index] = {**match,'reason':reason,
                    'window_support_frames':[other.frame_index for other in nearby],
                    'reference_match':matches[row.frame_index]}
    return recovered


def recover_secondary_names(video_path, reference_paths, primary_output, face_service, *, on_progress=None, last_source_frame=None, joint_context=None, defer_structure=False):
    import hashlib
    from pathlib import Path
    import cv2
    from .face_models import SECONDARY_FACE_MODEL_SPEC, ensure_face_models
    from .opencv_acceleration import secondary_recognizer
    from .camera_transitions import classify_transition

    targets = unresolved_observations(primary_output)
    from .member_timeline import _valid
    all_rows = {o.frame_index:o for evidence in primary_output['evidence'] for o,_ in evidence
                if _valid(o) and o.face_bbox is not None and len(o.landmarks)==5}
    spec = SECONDARY_FACE_MODEL_SPEC
    audit = dict(version=SECONDARY_VERSION, model_sha256=spec.sha256,
                 alignment='opencv_sface_align112_v1', embedding_dimension=128,
                 max_distance=.637, min_margin=.08, references=[], matches=[])
    seeds = primary_output.get('anchors', [])
    requested = {row.frame_index:row for _,row in seeds
                 if row.face_bbox is not None and len(row.landmarks) == 5}
    requested.update(all_rows)
    if not requested or not reference_paths:
        audit['reason'] = 'no_unresolved_faces' if not targets else 'no_reference_paths'
        return {}, audit
    try:
        paths = ensure_face_models(specs=(spec,))
        recognizer = secondary_recognizer(face_service, paths[spec.name])
    except (OSError, RuntimeError, cv2.error) as error:
        # Existing installations may not have the optional second model yet.
        # Its download/load failure must preserve the completed primary result.
        audit.update(reason='secondary_model_unavailable', error_type=type(error).__name__)
        return {}, audit

    def feature(image, box, landmarks, score):
        face = np.array([box[0],box[1],box[2]-box[0],box[3]-box[1],
                         *np.asarray(landmarks).reshape(-1),score],np.float32)
        value = _normalized(recognizer.feature(recognizer.alignCrop(image,face)))
        return value if value is not None and value.size == 128 else None

    samples = []
    for name, photos in reference_paths.items():
        for path in photos:
            data = Path(path).read_bytes()
            image = cv2.imdecode(np.frombuffer(data,dtype=np.uint8),cv2.IMREAD_COLOR)
            if image is None:
                continue
            candidate = face_service.get_face_embedding_candidate(image)
            if candidate is None:
                continue
            try:
                vector = feature(image,candidate.face_bbox,candidate.landmarks,candidate.detector_score)
            except (cv2.error, ValueError):
                continue
            if vector is not None:
                digest = hashlib.sha256(data).hexdigest()
                samples.append((name,digest,vector))
                audit['references'].append(dict(name=name,source_sha256=digest))
    gallery = build_secondary_gallery(samples,set(reference_paths))
    if gallery is None:
        audit['reason'] = 'incomplete_secondary_gallery'
        return {}, audit

    requested.update(targets)
    vectors, matches, index, done = {}, {}, 0, 0
    last_frame = max(max(requested),last_source_frame or 0)
    cap = cv2.VideoCapture(str(video_path))
    source_cuts,source_transitions,previous = [],[],None
    inventory = dict(reason='incomplete_source_decode',source_path=str(Path(video_path).resolve()),
                     fps=float(cap.get(cv2.CAP_PROP_FPS)),through_frame=-1,cut_frames=source_cuts,
                     camera_transitions=source_transitions)
    try:
        if not cap.isOpened():
            audit['reason'] = 'secondary_source_unavailable'
            return {}, audit
        while index <= last_frame:
            ok,image = cap.read()
            if not ok:
                break
            if previous is not None:
                transition = (classify_transition(previous,image,include_structure=False)
                              if defer_structure else classify_transition(previous,image))
                if transition['cut']:
                    source_cuts.append(index)
                if transition['color_candidate']:
                    source_transitions.append(dict(frame=index,**transition))
            previous = image
            inventory['through_frame'] = index
            if index in requested:
                row = requested[index]
                match = dict(name=None,reason='secondary_frame_unavailable',candidates=[])
                if ok:
                    try:
                        vector = feature(image,row.face_bbox,row.landmarks,row.detector_score)
                        match = match_secondary_vector(vector,gallery)
                        if vector is not None:
                            vectors[index] = vector
                    except (cv2.error, ValueError):
                        match['reason'] = 'secondary_alignment_failed'
                if index in targets:
                    matches[index] = match
                done += 1
                if on_progress:
                    on_progress(done,len(requested))
            index += 1
    finally:
        cap.release()
    if index > last_frame and np.isfinite(inventory['fps']) and inventory['fps'] > 0:
        inventory['reason'] = 'complete'
    audit['source_transitions'] = inventory
    anchors = confirmed_secondary_anchors(seeds,vectors,gallery)
    audit['video_anchors'] = [dict(name=name,frame_index=row.frame_index,time_seconds=row.time_seconds)
                              for name,row in anchors]
    from .joint_identity import joint_video_matches
    audit['joint_matches'] = joint_video_matches(requested,vectors,audit['video_anchors'],set(reference_paths))
    if joint_context is not None and inventory['reason'] == 'complete':
        # Runtime-only original gallery for targeted incoming-context queries.
        # Recovered names never become anchors; model objects stay out of JSON.
        frames = {a['frame_index'] for a in audit['video_anchors']}
        joint_context.update(
            observations={f: requested[f] for f in frames},
            vectors={f: vectors[f] for f in frames},
            anchors=[dict(a) for a in audit['video_anchors']],
            roster=set(reference_paths), secondary_recognizer=recognizer)
    audit['joint_policy'] = dict(max_mean_distance=.5,max_model_distance=.6,min_mean_margin=.08,
        query_exclusion_seconds=2.,minimum_source_time_separation=.15,all_roster_members_required=True,
        gallery_source='original_repeated_dual_photo_anchors')
    audit['video_policy'] = dict(max_distance=.5,min_margin=.08,query_exclusion_seconds=2.,
                                minimum_source_time_separation=.15,all_roster_members_required=True)
    names = {}
    for index,match in matches.items():
        row = targets[index]
        if not match['name'] and index in vectors:
            video = match_secondary_video(replace(row,embedding=vectors[index]),anchors,gallery)
            if video['name']:
                match = {**video,'reference_match':match}
        matches[index] = match
    scopes = [(segment.start,segment.end) for segment,decision in zip(
        primary_output['segments'],primary_output['decisions'],strict=True) if not decision.reference_id]
    if inventory['reason'] == 'complete':
        matches.update(secondary_window_matches(scopes,targets,vectors,matches,gallery,video_anchors=anchors,
            cut_frames=source_cuts))
    audit['window_policy'] = dict(radius_seconds=.4,minimum_frames=3,minimum_time_span=.15,
                                 max_distance_to_center=.35,primary_scope_bounds=True,
                                 video_gallery='original_repeated_dual_photo_anchors',
                                 complete_source_cuts_required=True,exclude_every_window_source=True)
    for index,match in matches.items():
        row = targets[index]
        audit['matches'].append(dict(frame_index=index,time_seconds=row.time_seconds,**match))
        if match['name']:
            names[index] = match['name']
    audit['reason'] = inventory['reason'] if done == len(requested) else 'incomplete_source_decode'
    audit['target_frames'] = len(targets)
    return names, audit
