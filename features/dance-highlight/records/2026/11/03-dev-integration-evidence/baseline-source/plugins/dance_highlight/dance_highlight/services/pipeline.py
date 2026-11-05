from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Sequence
import hashlib
import json
import logging
import os
import requests
import shutil
import time

# AV1(libdav1d) 멀티스레드 크래시 방지: VideoCapture 열기 전에 설정
os.environ.setdefault('OPENCV_FFMPEG_THREAD_COUNT', '1')

import cv2
import numpy as np

from .config import DanceConfig
from .protocols import PoseAnalyzer, FaceClusterer, Renderer, MetaBuilder, SegmentFaceResultLike
from .track import TrackAssigner
from .segment import (
    MainSelector,
    FrameRec,
    Segment,
    build_raw_main_segments,
    build_main_evidence_scopes,
    classify_main_scenes,
    intersect_main_segments,
    build_raw_group_segments,
    smooth_main_segments,
    smooth_group_segments,
)
from .dance_meta import DanceClipItem
from .diagnostics import coverage_gaps, frame_diagnostics
from .person_thumbnails import persist_person_thumbnails, release_person_thumbnails
from .reference_matcher import (
    ReferenceEmbeddingSample,
    SegmentEmbeddingScope,
    SegmentReferenceDecision,
    assign_reference_person_ids,
)
from .face_models import FACE_MODEL_SPECS, sha256_file
from clipper_face_core.face_models import AURAFACE_MODEL_NAME
from collections import Counter, defaultdict

MIN_USABLE_REFERENCE_IMAGES = 3
logger = logging.getLogger("dance_highlight.pipeline")


def _is_usable_reference_embedding(value: np.ndarray | None) -> bool:
    if value is None:
        return False
    vector = np.asarray(value)
    if vector.ndim != 1 or vector.size == 0 or not np.all(np.isfinite(vector)):
        return False
    return abs(float(np.linalg.norm(vector)) - 1.0) <= 1e-5


def _unknown_main_seconds(segments, decisions, eligible):
    return sum(part.end-part.start for index, part in intersect_main_segments(segments, eligible)
               if decisions[index].status != "matched")


def _output_identity_changes(before, after, eligible):
    """Count identity changes only where a main clip will actually be output."""
    def rows(state):
        segments, decisions = state
        return [(part.start, part.end, decisions[index].reference_id
                 if decisions[index].status == "matched" else None)
                for index, part in intersect_main_segments(segments, eligible)]
    left, right = rows(before), rows(after)
    changes = dict(recovered_seconds=0., corrected_seconds=0., conflict_seconds=0.)
    for a, b, old in left:
        for c, d, new in right:
            overlap = min(b, d)-max(a, c)
            if overlap <= 0 or old == new:
                continue
            key = 'recovered_seconds' if old is None else 'conflict_seconds' if new is None else 'corrected_seconds'
            changes[key] += overlap
    return changes


def _include_incoming_preparation(identity, records, joint_matches, *, video_path,
                                  fps, cut_frames, face_service, joint_context):
    """Extend clip context only after normal identity and scene decisions finish."""
    from .incoming_context import (VERSION, IncomingFaceQuery,
                                   incoming_preparation_context, apply_preparation_contexts)
    if not joint_context.get('anchors'):
        return identity, dict(version=VERSION, reason='original_joint_gallery_unavailable', accepted=[])
    query = None
    started = time.perf_counter()
    try:
        query = IncomingFaceQuery(face_service, video_path, fps, joint_context,
                                  joint_context['secondary_recognizer'])
        contexts, audit = incoming_preparation_context(identity, records, joint_matches,
            fps=fps, cut_frames=cut_frames, query=query)
        result = apply_preparation_contexts(identity, contexts)
        audit['elapsed_seconds'] = time.perf_counter()-started
        return result, audit
    except (OSError, ValueError, RuntimeError, cv2.error) as error:
        return identity, dict(version=VERSION, reason='incoming_context_unavailable',
                              error_type=type(error).__name__, accepted=[])
    finally:
        if query is not None:
            query.close()


def select_majority_cluster_embeddings(
    *,
    embeddings: Sequence[np.ndarray],
    track_map: Sequence[int],
    labels: Sequence[int | None],
    raw_labels: Sequence[int | None],
) -> tuple[tuple[np.ndarray, ...], ...]:
    """Keep only tracks selected by Dance's per-segment main-cluster vote."""
    selected: list[list[np.ndarray]] = [[] for _ in raw_labels]
    for embedding, segment_index, label in zip(embeddings, track_map, labels, strict=True):
        if label is not None and label == raw_labels[segment_index]:
            selected[segment_index].append(embedding)
    return tuple(tuple(values) for values in selected)


def confirmed_group_recipients(
    groups: Sequence[Segment],
    main_segments: Sequence[Segment],
    main_decisions: Sequence[SegmentReferenceDecision],
    face_matches: Sequence[tuple[int, float, SegmentReferenceDecision]],
) -> tuple[tuple[str, ...], ...]:
    """반복 확인된 단체 얼굴과 대부분 겹치는 매칭 단독 클립만 사용한다."""
    face_frames: list[dict[str, set[float]]] = [defaultdict(set) for _ in groups]
    best_distances: list[dict[str, float]] = [{} for _ in groups]
    for group_index, frame_time, decision in face_matches:
        if (not 0 <= group_index < len(groups) or decision.status != "matched"
                or decision.reference_id is None or decision.distance is None):
            continue
        member = decision.reference_id
        face_frames[group_index][member].add(frame_time)
        best_distances[group_index][member] = min(
            best_distances[group_index].get(member, float("inf")), decision.distance,
        )

    recipients = []
    for group_index, group in enumerate(groups):
        names = {
            member for member, times in face_frames[group_index].items()
            if len(times) >= 2 and best_distances[group_index][member] <= 0.55
        }
        duration = max(1e-9, group.end - group.start)
        for main, decision in zip(main_segments, main_decisions, strict=True):
            if decision.status != "matched" or decision.reference_id is None:
                continue
            overlap = max(0.0, min(group.end, main.end) - max(group.start, main.start))
            if overlap >= duration * 0.5:
                names.add(decision.reference_id)
        recipients.append(tuple(sorted(names)))
    return tuple(recipients)

def _safe_filename(name: str) -> str:
    """파일명으로 안전한 문자열로 변환."""
    import re
    import unicodedata
    s = unicodedata.normalize("NFC", (name or "").strip())
    s = s.replace("\\", " ").replace("/", " ")
    s = re.sub(r"[<>:\"|?*\x00-\x1F]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    if not s:
        s = "untitled"
    return s


class DancePipeline:
    """안무 하이라이트 파이프라인 오케스트레이터.

    모든 의존성은 Protocol 타입으로 받는다.
    구체 구현은 외부에서 주입하거나 create_default_pipeline() 팩토리로 생성.
    """

    def __init__(
        self,
        config: DanceConfig,
        pose: PoseAnalyzer,
        face: FaceClusterer,
        render: Renderer,
        meta_builder: MetaBuilder,
    ):
        self.config = config
        self.pose = pose
        self.face = face
        self.render = render
        self.meta_builder = meta_builder

    def analyze_video_to_records(
        self,
        video_path: str,
        frame_progress_cb=None,
    ) -> Tuple[List[FrameRec], float, float]:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"cannot open video: {video_path}")

        fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        duration = (total_frames / fps) if total_frames > 0 else 0.0

        from clipper_accelerators.runtime import set_estimate
        set_estimate('pose.yolov8s',(total_frames+int(self.config.analyze_skip)-1)//int(self.config.analyze_skip))
        selector = MainSelector(
            fps=fps,
            group_fps=fps / max(1, int(self.config.analyze_skip)),
        )
        tracker = TrackAssigner(
            track_match_iou=self.config.track_match_iou,
            track_ttl_sec=self.config.track_ttl_sec,
        )

        recs: List[FrameRec] = []
        fidx = 0
        face_stride = max(1, round(fps / (max(1, int(self.config.analyze_skip)) * 5)))
        report_every = max(1, int(self.config.analyze_skip) * 30)
        last_reported = -1

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if (fidx % int(self.config.analyze_skip)) != 0:
                fidx += 1
                continue

            t = float(fidx) / fps
            persons = self.pose.run_pose_on_frame(frame)
            main, is_group = selector.select(persons, frame.shape, time_seconds=t)
            face_boxes = self.face.detect_face_boxes(frame) if persons and len(recs) % face_stride == 0 else []
            evidence = {
                "group_bboxes": list(selector.last_group_member_bboxes),
                "person_bboxes": [np.asarray(person["bbox"], dtype=np.float32) for person in persons],
                "face_bboxes": face_boxes,
                "person_head_keypoints": [np.asarray(person.get("head_keypoints", []), dtype=np.float32)
                                           for person in persons],
                "person_pose_keypoints": [np.asarray(person.get("pose_keypoints", []), dtype=np.float32)
                                           for person in persons],
                "group_candidate": selector.last_group_candidate,
                "group_score_gap": selector.last_group_score_gap,
                "group_area_ratio": selector.last_group_area_ratio,
            }

            if main is None:
                recs.append(FrameRec(t=t, main_id=None, main_bbox=None, is_group=bool(is_group), **evidence))
            else:
                mid = tracker.assign(t, main["bbox"])
                recs.append(FrameRec(t=t, main_id=int(mid), main_bbox=main["bbox"], is_group=bool(is_group), **evidence))

            if frame_progress_cb and total_frames > 0 and fidx % report_every == 0:
                ratio = min(fidx / total_frames, 1.0)
                bucket = int(ratio * 10)
                if bucket != last_reported:
                    last_reported = bucket
                    frame_progress_cb(ratio)

            fidx += 1

        cap.release()
        return recs, fps, float(duration)
    
    def _download_reference_images(
        self,
        project_root: Path,
        dance_setup: Optional[Dict[str, Any]],
    ) -> Dict[str, List[Path]]:
        if not dance_setup:
            return {}

        members = dance_setup.get("members", []) or []
        out: Dict[str, List[Path]] = {}

        refs_root = project_root / "refs" / "dance"
        refs_root.mkdir(parents=True, exist_ok=True)

        for member in members:
            member_name = (
                member.get("memberName")
                or member.get("memberKey")
                or "member"
            )
            member_key = _safe_filename(member_name).lower().replace(" ", "_")
            member_dir = refs_root / member_key
            member_dir.mkdir(parents=True, exist_ok=True)

            saved_paths: List[Path] = []
            # New jobs carry prevalidated local files; selectedImages remains the
            # original URL selection for old jobs and project metadata.
            sources = member.get("validatedImagePaths")
            if sources is None:
                sources = member.get("selectedImages", []) or []
            for idx, source in enumerate(sources):
                if not isinstance(source, str):
                    continue
                ext = Path(source.split("?")[0]).suffix.lower() or ".jpg"
                if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
                    ext = ".jpg"
                save_path = member_dir / f"ref_{idx:02d}{ext}"

                if Path(source).is_absolute():
                    local_path = Path(source)
                    if not local_path.is_file():
                        raise ValueError(f"Reference image missing for {member_name}: {source}")
                    if local_path.resolve() != save_path.resolve():
                        shutil.copyfile(local_path, save_path)
                else:
                    try:
                        resp = requests.get(source, timeout=15)
                        resp.raise_for_status()
                        save_path.write_bytes(resp.content)
                    except requests.RequestException as exc:
                        logger.warning("Reference download failed for %s: %s", member_name, exc)
                        continue
                saved_paths.append(save_path)

            out[member_name] = saved_paths

        return out

    def _build_reference_embeddings(
        self,
        ref_image_paths: Dict[str, List[Path]],
        sample_sink: Optional[List[ReferenceEmbeddingSample]] = None,
    ) -> Dict[str, np.ndarray]:
        ref_embs: Dict[str, np.ndarray] = {}

        for member_name, paths in ref_image_paths.items():
            embs: List[np.ndarray] = []

            for index, p in enumerate(paths):
                emb = self.face.get_face_embedding_from_image_path(str(p))
                if _is_usable_reference_embedding(emb):
                    embs.append(emb)
                    if sample_sink is not None:
                        image_bytes = p.read_bytes()
                        image = cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
                        if image is None:
                            raise ValueError(f"Reference image cannot be decoded: {p}")
                        height, width = image.shape[:2]
                        sample_sink.append(ReferenceEmbeddingSample(
                            reference_id=member_name,
                            sample_id=f"{member_name}/{index}",
                            image_sha256=hashlib.sha256(image_bytes).hexdigest(),
                            width=int(width),
                            height=int(height),
                            embedding=emb,
                        ))

            print(f"[REF] member={member_name} total_images={len(paths)} valid_face_embs={len(embs)}", flush=True)

            if len(embs) < MIN_USABLE_REFERENCE_IMAGES:
                raise ValueError(
                    f"Reference images for {member_name} require at least "
                    f"{MIN_USABLE_REFERENCE_IMAGES} usable faces; found {len(embs)}"
                )

            avg = self.face.average_embeddings(embs)
            if avg is not None:
                ref_embs[member_name] = avg

        print(f"[REF] built_ref_embeddings={list(ref_embs.keys())}", flush=True)
        return ref_embs

    def _cluster_centroids_from_tracks(
        self,
        labels: List[Optional[int]],
        all_embs: List[np.ndarray],
    ) -> Dict[int, np.ndarray]:
        cluster_to_embs = defaultdict(list)

        for lab, emb in zip(labels, all_embs):
            if lab is None:
                continue
            cluster_to_embs[int(lab)].append(emb)

        centroids: Dict[int, np.ndarray] = {}
        for cid, embs in cluster_to_embs.items():
            if not embs:
                continue
            centroid = np.mean(np.stack(embs), axis=0)
            centroid = centroid / (np.linalg.norm(centroid) + 1e-9)
            centroids[cid] = centroid.astype(np.float32)

        return centroids

    def _assign_reference_members(
        self,
        *,
        segments: List[Segment],
        selected_track_embeddings: Sequence[tuple[np.ndarray, ...]],
        cluster_ids: Sequence[int | None],
        reference_samples: List[ReferenceEmbeddingSample],
        input_video: Path,
        project_id: int,
        video_size: Tuple[int, int],
    ) -> tuple[SegmentReferenceDecision, ...]:
        model_hashes = {spec.name: spec.sha256 for spec in FACE_MODEL_SPECS}
        source_hash = sha256_file(input_video)
        config_hash = hashlib.sha256(repr(self.config).encode("utf-8")).hexdigest()
        scopes = tuple(
            SegmentEmbeddingScope(
                scope_id=f"main-{index}",
                start_sec=float(seg.start),
                end_sec=float(seg.end),
                track_embeddings=tuple(track_embeddings),
                cluster_id=cluster_id,
            )
            for index, (seg, track_embeddings, cluster_id) in enumerate(
                zip(segments, selected_track_embeddings, cluster_ids, strict=True)
            )
        )
        return assign_reference_person_ids(
            references=reference_samples,
            scopes=scopes,
            analysis_id=f"dance-project-{project_id}-{source_hash[:12]}",
            video_sha256=source_hash,
            detector_sha256=model_hashes["opencv-yunet-face-detection"],
            recognizer_sha256=model_hashes[AURAFACE_MODEL_NAME],
            config_sha256=config_hash,
            backend_version=f"opencv-{cv2.__version__}",
            video_size=video_size,
            max_distance=float(self.config.member_match_threshold),
            min_margin=0.0,
            duplicate_threshold=float(self.config.member_duplicate_threshold),
            duplicate_margin=float(self.config.member_duplicate_margin),
        )

    def _video_size(self, input_video: Path) -> Tuple[int, int]:
        cap = cv2.VideoCapture(str(input_video))
        try:
            if not cap.isOpened():
                raise RuntimeError(f"cannot open video for face provenance: {input_video}")
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            if width <= 0 or height <= 0:
                raise RuntimeError(f"invalid video dimensions: {input_video}")
            return width, height
        finally:
            cap.release()

    def _collect_group_face_samples(
        self, video_path: str, groups: Sequence[Segment], recs: Sequence[FrameRec],
    ) -> list[tuple[int, float, np.ndarray]]:
        """단체 클립마다 최대 5개 참여자 프레임을 한 번의 영상 순회로 읽는다."""
        tasks: list[tuple[int, FrameRec]] = []
        for group_index, group in enumerate(groups):
            eligible = [rec for rec in recs if group.start <= rec.t < group.end
                        and rec.is_group and rec.group_bboxes]
            count = min(5, len(eligible))
            tasks.extend((group_index, eligible[int(index * len(eligible) / count)])
                         for index in range(count))
        if not tasks:
            return []

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return []
        samples: list[tuple[int, float, np.ndarray]] = []
        try:
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            frame_tasks: dict[int, list[tuple[int, FrameRec]]] = defaultdict(list)
            for group_index, rec in tasks:
                frame_tasks[int(round(rec.t * fps))].append((group_index, rec))
            current = 0
            for frame_index in sorted(frame_tasks):
                while current < frame_index:
                    if not cap.grab():
                        return samples
                    current += 1
                ok, frame = cap.read()
                if not ok:
                    return samples
                current += 1
                for group_index, rec in frame_tasks[frame_index]:
                    for embedding in self.face.group_face_embeddings(frame, rec.group_bboxes):
                        samples.append((group_index, float(rec.t), embedding))
        finally:
            cap.release()
        return samples

    def _person_display_name(self, person_id: str) -> str:
        if person_id == "unknown":
            return "미확인 인물"
        if person_id.startswith("person_") and person_id[7:].isdigit():
            return f"미확인 인물 {person_id[7:]}"
        return person_id.replace("_", " ")

    def _map_cluster_to_member_name(
        self,
        cluster_centroids: Dict[int, np.ndarray],
        ref_embs: Dict[str, np.ndarray],
        threshold: float = 0.60,
        duplicate_threshold: float = 0.45,
        duplicate_margin: float = 0.08,
    ) -> Dict[int, str]:
        if not cluster_centroids or not ref_embs:
            print(f"[MAP] skipped cluster_centroids={len(cluster_centroids)} ref_embs={len(ref_embs)}", flush=True)
            return {}

        mapping: Dict[int, str] = {}
        cluster_candidates: Dict[int, List[Tuple[str, float]]] = {}

        for cid, cent in cluster_centroids.items():
            best_name = None
            best_dist = 999.0
            candidates: List[Tuple[str, float]] = []

            for member_name, ref_emb in ref_embs.items():
                dist = 1 - float(np.dot(cent, ref_emb))
                candidates.append((member_name, dist))
                print(f"[MAP] cluster={cid} candidate={member_name} dist={dist:.4f}", flush=True)

                if dist < best_dist:
                    best_dist = dist
                    best_name = member_name

            print(f"[MAP] cluster={cid} best_name={best_name} best_dist={best_dist:.4f} threshold={threshold}", flush=True)
            cluster_candidates[cid] = sorted(candidates, key=lambda item: item[1])

        assigned_clusters: set[int] = set()
        assigned_members: set[str] = set()
        # 멤버별 '주인(primary)' 클러스터까지의 거리. 아래 폴백의 중복 배정 판정 기준이 된다.
        primary_dist: Dict[str, float] = {}
        candidate_pairs = sorted(
            (
                (dist, cid, member_name)
                for cid, candidates in cluster_candidates.items()
                for member_name, dist in candidates
                if dist <= threshold
            ),
            key=lambda item: item[0],
        )

        for dist, cid, member_name in candidate_pairs:
            if cid in assigned_clusters or member_name in assigned_members:
                continue
            mapping[cid] = member_name
            assigned_clusters.add(cid)
            assigned_members.add(member_name)
            primary_dist[member_name] = dist

        # 폴백: 위에서 못 붙은 클러스터. 한 사람이 각도·조명 탓에 여러 클러스터로 쪼개지는
        # 경우를 살리려면 중복 배정이 필요하지만, 조건 없이 허용하면 참조 멤버가 1명일 때
        # 임계값 안에 든 남의 클러스터까지 전부 그 한 명에게 빨려든다. 그래서 이미 주인
        # 클러스터가 있는 멤버에 덧붙일 때는 '그 주인만큼 닮았을 때'만 붙인다.
        for cid, candidates in cluster_candidates.items():
            if cid in assigned_clusters or not candidates:
                continue
            best_name, best_dist = candidates[0]
            if best_dist > threshold:
                continue

            if best_name not in assigned_members:
                mapping[cid] = best_name
                assigned_clusters.add(cid)
                assigned_members.add(best_name)
                primary_dist[best_name] = best_dist
                continue

            limit = min(duplicate_threshold, primary_dist[best_name] + duplicate_margin)
            if best_dist > limit:
                print(
                    f"[MAP] dup_rejected cluster={cid} member={best_name}"
                    f" dist={best_dist:.4f} limit={limit:.4f}",
                    flush=True,
                )
                continue

            mapping[cid] = best_name
            assigned_clusters.add(cid)

        print(f"[MAP] final_mapping={mapping}", flush=True)
        return mapping
    

    def _segment_overlap_ratio(self, a_start: float, a_end: float, b_start: float, b_end: float) -> float:
        inter = max(0.0, min(a_end, b_end) - max(a_start, b_start))
        dur = max(1e-9, a_end - a_start)
        return inter / dur

    def _filter_group_like_main_segments(
        self,
        main_segs: List[Segment],
        group_segs: List[Segment],
        overlap_threshold: float = 0.6,
        keep_short_intro_sec: float = 3.2,
    ) -> List[Segment]:
        if not main_segs or not group_segs:
            return main_segs

        filtered: List[Segment] = []

        for seg in main_segs:
            seg_dur = float(seg.end - seg.start)

            if seg.start < 12.0 and seg_dur <= keep_short_intro_sec:
                filtered.append(seg)
                continue

            max_overlap = 0.0
            for g in group_segs:
                ov = self._segment_overlap_ratio(seg.start, seg.end, g.start, g.end)
                if ov > max_overlap:
                    max_overlap = ov

            if max_overlap >= overlap_threshold:
                print(
                    f"[GROUP-FILTER] drop main seg start={seg.start:.3f} end={seg.end:.3f} "
                    f"dur={seg_dur:.3f} overlap={max_overlap:.3f}",
                    flush=True
                )
                continue

            filtered.append(seg)

        print(
            f"[GROUP-FILTER] main_before={len(main_segs)} main_after={len(filtered)} group_count={len(group_segs)}",
            flush=True
        )
        return filtered
    
    def run(
        self,
        project_root: Path,
        input_video: Path,
        project_id: int,
        progress_cb: Optional[callable] = None,
        dance_setup: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        last_progress = None

        def _progress(p: int, msg: str):
            nonlocal last_progress
            current = (int(p), str(msg))
            if current == last_progress:
                return
            last_progress = current
            if progress_cb:
                try:
                    progress_cb(*current)
                except Exception:
                    pass

        def _fmt(sec: float) -> str:
            """초 → '1m 23.4s' 형식"""
            m = int(sec) // 60
            s = sec - m * 60
            return f"{m}m {s:.1f}s" if m else f"{s:.1f}s"

        _t_total = time.perf_counter()
        _timings: dict = {}

        project_root = project_root.resolve()
        input_video = input_video.resolve()

        print("[DANCE] step: download_reference_images start", flush=True)
        _t = time.perf_counter()
        ref_image_paths = self._download_reference_images(project_root, dance_setup)
        _timings["download_refs"] = time.perf_counter() - _t
        print(f"[DANCE] step: download_reference_images done, count={len(ref_image_paths)}", flush=True)
        print(f"[DANCE][T] download_refs: {_fmt(_timings['download_refs'])}", flush=True)

        clips_root = project_root / self.config.clips_dir_rel
        json_root = project_root / self.config.json_dir_rel
        clips_main_dir = clips_root / "main"
        clips_group_dir = clips_root / "group"

        clips_main_dir.mkdir(parents=True, exist_ok=True)
        clips_group_dir.mkdir(parents=True, exist_ok=True)
        json_root.mkdir(parents=True, exist_ok=True)

        def _frame_progress_cb(ratio: float):
            p = int(10 + ratio * 10)  # 10% → 20%
            _progress(p, "영상 프레임을 분석하고 있습니다")

        # analyze_video_to_records(YOLO/torch CUDA)를 먼저 실행해 pose device를 확정.
        print("[DANCE] step: analyze_video_to_records start", flush=True)
        _progress(10, "영상 프레임을 분석하고 있습니다")
        _t = time.perf_counter()
        recs, fps, duration = self.analyze_video_to_records(str(input_video), frame_progress_cb=_frame_progress_cb)
        _timings["yolo"] = time.perf_counter() - _t
        print(
            f"[DANCE] step: analyze_video_to_records done, frames={len(recs)}", flush=True
        )
        print(
            f"[DANCE][T] yolo: {_fmt(_timings['yolo'])}"
            f"  (frames={len(recs)}, video={_fmt(duration)}, fps={fps:.1f})",
            flush=True,
        )

        _t = time.perf_counter()
        reference_samples: List[ReferenceEmbeddingSample] = []
        ref_embs = self._build_reference_embeddings(ref_image_paths, sample_sink=reference_samples)
        _timings["ref_embs"] = time.perf_counter() - _t
        print(f"[DANCE] step: build_reference_embeddings done, embs={list(ref_embs.keys())}", flush=True)
        print(f"[DANCE][T] ref_embeddings: {_fmt(_timings['ref_embs'])}", flush=True)
        _progress(20, "영상 프레임을 분석하고 있습니다")

        main_role_refinement = {}
        if reference_samples:
            from .observed_main import refine_main_roles
            _progress(21, "메인 인물의 구도와 연속성을 확인하고 있습니다")
            recs, main_role_refinement = refine_main_roles(
                recs, input_video, fps, self.face, self.config,
                on_progress=lambda done,total:_progress(21+int(8*done/max(1,total)),
                    "메인 인물의 구도와 연속성을 확인하고 있습니다"))

        _t = time.perf_counter()
        # Scene eligibility controls exported roles, not available identity
        # evidence. Keep original selected-body observations through inference.
        evidence_recs = recs
        native_scene_refinement = {}
        if reference_samples:
            from .native_scene import refine_native_scenes
            size = self._video_size(input_video)
            recs = classify_main_scenes(recs, size)
            _progress(29, "원경 단체 장면을 확인하고 있습니다")
            native_started = time.perf_counter()
            recs, native_scene_refinement = refine_native_scenes(
                recs, input_video, fps, self.pose, video_size=size,
                cut_frames=main_role_refinement.get('cut_frames') if main_role_refinement.get('reason') == 'complete' else None,
                on_progress=lambda done,total:_progress(29, "원경 단체 장면을 확인하고 있습니다"))
            _timings["native_scene"] = time.perf_counter()-native_started
        eligible_main = build_main_evidence_scopes(build_raw_main_segments(recs))
        raw_main = build_raw_main_segments(evidence_recs)
        raw_group = build_raw_group_segments(recs)
        scene_boundary_refinement = {}
        if reference_samples:
            from .scene_boundaries import align_scene_segments_from_source
            eligible_main, raw_group, scene_boundary_refinement = align_scene_segments_from_source(
                recs, eligible_main, raw_group, video_path=input_video, fps=fps,
                cut_frames=main_role_refinement.get('cut_frames') if main_role_refinement.get('reason') == 'complete' else None,
                sample_step=max(1, int(self.config.analyze_skip)))

        main_segs = build_main_evidence_scopes(raw_main) if reference_samples else smooth_main_segments(
            raw_main,
            min_main_seg_sec=self.config.min_main_seg_sec,
            bridge_gap_sec=self.config.bridge_gap_sec,
            merge_gap_sec=self.config.merge_gap_sec,
        )
        group_segs = smooth_group_segments(
            raw_group,
            min_group_seg_sec=.15 if reference_samples else self.config.min_group_seg_sec,
            merge_gap_sec=0. if reference_samples else self.config.merge_gap_sec,
        )

        if not reference_samples:
            main_segs = self._filter_group_like_main_segments(
                main_segs=main_segs,
                group_segs=group_segs,
                overlap_threshold=0.6,
                keep_short_intro_sec=3.2,
            )
        _timings["segment_build"] = time.perf_counter() - _t
        print(
            f"[DANCE][T] segment_build: {_fmt(_timings['segment_build'])}"
            f"  (main={len(main_segs)}, group={len(group_segs)})",
            flush=True,
        )
        _progress(30, "구간을 정리하고 있습니다")

        # Registered members: retain selected-main evidence before deciding
        # identity or clip boundaries, including group overlaps and no-face gaps.
        # batch_segment_embeddings: VideoCapture를 한 번만 열어 전체 처리

        def _face_progress(done: int, total: int):
            p = 30 + int(done / total * 15)  # 30% → 45%
            _progress(p, "얼굴 특징을 추출하고 있습니다")

        _t = time.perf_counter()
        # Dance member clips must come from the selected main body. Supporting
        # faces may identify a group participant, but cannot create solo clips.
        all_face_results: List[SegmentFaceResultLike] = self.face.batch_segment_embeddings(
            str(input_video),
            main_segs,
            on_progress=_face_progress,
            frame_records=evidence_recs,
            sample_all_main_frames=bool(reference_samples),
        )
        face_results = all_face_results
        _timings["face_extract"] = time.perf_counter() - _t
        print(
            f"[DANCE][T] face_extract: {_fmt(_timings['face_extract'])}"
            f"  (segs={len(main_segs)}, candidates/seg={self.config.face_candidate_sample_frames},"
            f" selected/seg={self.config.face_sample_frames},"
            f" owned_samples={sum(len(getattr(r, 'owned_observations', [])) for r in all_face_results)})",
            flush=True,
        )

        _progress(45, "얼굴 특징을 추출하고 있습니다")

        kept_main_segs: List[Segment] = []
        kept_face_results = []
        dropped_no_face = 0

        # 🔥 1. 모든 track embedding 수집
        all_embs: List[np.ndarray] = []
        track_map: List[int] = []  # index → segment index
        track_evidence: List[List[bytes]] = []

        for seg_idx, r in enumerate(face_results):
            has_owned_faces = reference_samples and any(
                o.association == "confirmed" and o.embedding is not None and not o.failure
                for o in getattr(r, "owned_observations", []))
            if not reference_samples and (not r.face_detected or not r.track_embeddings) and not has_owned_faces:
                dropped_no_face += 1
                continue

            kept_main_segs.append(r.seg)
            kept_face_results.append(r)

            for track_index, emb in enumerate(r.track_embeddings):
                all_embs.append(emb)
                track_map.append(len(kept_main_segs) - 1)
                previews = getattr(r, "track_evidence_images", [])
                thumbnails = getattr(r, "track_thumbnail_images", [])
                display_images = thumbnails[track_index] if track_index < len(thumbnails) else []
                track_evidence.append(display_images or (previews[track_index] if track_index < len(previews) else []))

        # 🔥 2. 클러스터링
        _t = time.perf_counter()
        if all_embs:
            labels = self.face.cluster_embeddings(all_embs)
        else:
            labels = []

        # ---------------------------------
        # 🔥 작은 cluster 병합 (post merge)
        # ---------------------------------

        cluster_to_embs = defaultdict(list)

        for lab, emb in zip(labels, all_embs):
            if lab is None:
                continue
            cluster_to_embs[int(lab)].append(emb)

        # centroid 계산
        cluster_centroids = {}
        for cid, embs in cluster_to_embs.items():
            if not embs:
                continue
            centroid = np.mean(np.stack(embs), axis=0)
            centroid = centroid / (np.linalg.norm(centroid) + 1e-9)
            cluster_centroids[cid] = centroid

        # 작은 cluster 탐지 (3개 미만)
        small_clusters = [cid for cid, embs in cluster_to_embs.items() if len(embs) < 3]

        for small_cid in small_clusters:
            if small_cid not in cluster_centroids:
                continue

            small_cent = cluster_centroids[small_cid]

            best_match = None
            best_dist = 999

            for cid, cent in cluster_centroids.items():
                if cid == small_cid:
                    continue
                dist = 1 - float(np.dot(small_cent, cent))  # cosine distance
                if dist < best_dist:
                    best_dist = dist
                    best_match = cid

            # 0.45 이하이면 병합
            if best_match is not None and best_dist < 0.45:
                for i in range(len(labels)):
                    if labels[i] == small_cid:
                        labels[i] = best_match

        # 3. segment별 majority voting
        segment_votes: Dict[int, List[int]] = {}

        for lab, seg_idx in zip(labels, track_map):
            if lab is None:
                continue
            segment_votes.setdefault(seg_idx, []).append(int(lab))

        # 1. segment별 raw cluster label 계산
        raw_labels: List[Optional[int]] = []

        for seg_idx in range(len(kept_main_segs)):
            votes = segment_votes.get(seg_idx, [])
            if not votes:
                raw_labels.append(None)
            else:
                most_common_label = Counter(votes).most_common(1)[0][0]
                raw_labels.append(int(most_common_label))

        selected_evidence: List[List[bytes]] = [[] for _ in kept_main_segs]
        for previews, seg_idx, label in zip(track_evidence, track_map, labels, strict=True):
            if label is not None and label == raw_labels[seg_idx]:
                selected_evidence[seg_idx].extend(previews)

        # 2. cluster centroid 계산
        cluster_centroids = self._cluster_centroids_from_tracks(labels, all_embs)

        # Registered member names come from each main segment's selected face
        # evidence. Anonymous cluster labels remain only as the fallback bucket.
        reference_decisions = self._assign_reference_members(
            segments=kept_main_segs,
            selected_track_embeddings=select_majority_cluster_embeddings(
                embeddings=all_embs,
                track_map=track_map,
                labels=labels,
                raw_labels=raw_labels,
            ),
            cluster_ids=raw_labels,
            reference_samples=reference_samples,
            input_video=input_video,
            project_id=project_id,
            video_size=self._video_size(input_video),
        ) if kept_main_segs else ()

        # Group recipients use the original decisions. A newly recovered solo
        # name cannot spread through temporal overlap into a group clip.
        baseline_main_segments = list(kept_main_segs)
        baseline_reference_decisions = reference_decisions
        matcher = None
        output_continuity_refinement = {}
        identity_refinement = {"accurate_indices": [], "audit": []}
        secondary_refinement = {}
        joint_context = {}
        secondary_recovered_seconds = 0.
        body_continuity_refinement = {}
        mask_continuity_refinement = {}
        joint_identity_refinement = {}
        scene_context_refinement = {}
        scene_context_cuts = (main_role_refinement.get('cut_frames')
                              if main_role_refinement.get('reason') == 'complete' else None)
        if reference_samples and kept_main_segs:
            from .face_recovery import ReferenceObservationMatcher
            from clipper_face_core import GalleryBuildError
            from .member_timeline import refine_member_timeline, refine_unresolved_with_names
            from .secondary_faces import recover_secondary_names
            from .body_continuity import bridge_main_face_gaps
            from .mask_continuity import recover_mask_names
            from .context_faces import collect_context_anchors
            from .joint_identity import revalidate_named_segments
            model_hashes = {spec.name: spec.sha256 for spec in FACE_MODEL_SPECS}
            try:
                matcher = ReferenceObservationMatcher(
                    references=reference_samples, analysis_id=f"dance-project-{project_id}",
                    video_sha256=sha256_file(input_video),
                    detector_sha256=model_hashes["opencv-yunet-face-detection"],
                    recognizer_sha256=model_hashes[AURAFACE_MODEL_NAME],
                    config_sha256=hashlib.sha256(repr(self.config).encode()).hexdigest(),
                    backend_version=f"opencv-{cv2.__version__}", video_size=self._video_size(input_video),
                    max_distance=float(self.config.member_match_threshold),
                )
            except GalleryBuildError as exc:
                # Baseline already records the invalid gallery; anonymous clips
                # must remain exportable when no reference centroid is usable.
                identity_refinement["skipped_reason"] = exc.reason
            else:
                identity_refinement = refine_member_timeline(
                    kept_main_segs, reference_decisions, raw_labels, selected_evidence,
                    kept_face_results, matcher, video_path=str(input_video),
                )
                primary_unknown_seconds = _unknown_main_seconds(
                    identity_refinement['segments'], identity_refinement['decisions'], eligible_main)
                fallback_names, secondary_refinement = recover_secondary_names(
                    input_video, ref_image_paths, identity_refinement, self.face,
                    joint_context=joint_context,
                    last_source_frame=max((round(r.t*fps) for r in evidence_recs),default=0),
                    on_progress=lambda done,total:_progress(55+int(10*done/max(1,total)),
                                                             '메인 인물의 얼굴 근거를 교차 확인하고 있습니다'))
                if fallback_names:
                    identity_refinement = refine_unresolved_with_names(
                        identity_refinement,fallback_names,matcher,video_path=str(input_video))
                secondary_refinement['interval_refinements'] = identity_refinement.get('secondary_refinements',[])
                secondary_recovered_seconds = primary_unknown_seconds-_unknown_main_seconds(
                    identity_refinement['segments'], identity_refinement['decisions'], eligible_main)
                _progress(65,'메인 인물의 연속 구간을 확인하고 있습니다')
                stage_before = (list(identity_refinement['segments']), list(identity_refinement['decisions']))
                identity_refinement, body_continuity_refinement = bridge_main_face_gaps(
                    identity_refinement,evidence_recs,input_video)
                body_continuity_refinement['output_changes'] = _output_identity_changes(
                    stage_before, (identity_refinement['segments'], identity_refinement['decisions']), eligible_main)
                context_anchors,context_cuts,context_audit = collect_context_anchors(
                    input_video,evidence_recs,fps,identity_refinement,self.face,matcher,ref_image_paths,
                    source_inventory=secondary_refinement.get('source_transitions'),
                    on_progress=lambda done,total:_progress(65+int(done/max(1,total)),
                        '같은 장면에 등장한 멤버의 얼굴 근거를 확인하고 있습니다'))
                if context_audit.get('reason') == 'complete':
                    scene_context_cuts = context_cuts
                stage_before = (list(identity_refinement['segments']), list(identity_refinement['decisions']))
                # User-disabled: retain the invocation for later bounded evaluation.
                # identity_refinement, mask_continuity_refinement = recover_mask_names(
                #     identity_refinement,evidence_recs,input_video,fps,secondary_refinement.get('video_anchors',[]),
                #     context_anchors=context_anchors,
                #     joint_matches=secondary_refinement.get('joint_matches',{}),
                #     cut_frames=context_cuts if context_audit.get('reason') == 'complete' else None,
                #     on_progress=lambda done,total:_progress(66+int(2*done/max(1,total)),
                #         '확인된 인물의 움직임을 따라 미확인 구간을 검증하고 있습니다'))
                _timings['mask_continuity'] = 0.
                mask_continuity_refinement = dict(version='disabled_runtime_cost_v1',
                    reason='disabled_runtime_cost', recovered_seconds=0., candidates=[])
                mask_continuity_refinement['output_changes'] = _output_identity_changes(
                    stage_before, (identity_refinement['segments'], identity_refinement['decisions']), eligible_main)
                mask_continuity_refinement['context_faces'] = context_audit
                stage_before = (list(identity_refinement['segments']), list(identity_refinement['decisions']))
                # User-disabled: retain the invocation for later bounded evaluation.
                # identity_refinement,joint_identity_refinement = revalidate_named_segments(
                #     identity_refinement,evidence_recs,input_video,fps,secondary_refinement.get('joint_matches',{}),
                #     secondary_refinement.get('video_anchors',[]),
                #     cut_frames=context_cuts if context_audit.get('reason') == 'complete' else None,
                #     camera_transitions=context_audit.get('camera_transitions',()),
                #     on_progress=lambda done,total:_progress(68+int(done/max(1,total)),
                #         '미확인 구간과 멤버 이름의 충돌을 재검증하고 있습니다'))
                _timings['joint_identity'] = 0.
                joint_identity_refinement = dict(version='disabled_runtime_cost_v1',
                    reason='disabled_runtime_cost', corrected_seconds=0., recovered_seconds=0., conflict_seconds=0., candidates=[])
                joint_identity_refinement['output_changes'] = _output_identity_changes(
                    stage_before, (identity_refinement['segments'], identity_refinement['decisions']), eligible_main)
                secondary_refinement['identity_revalidation'] = joint_identity_refinement
                old_unknown_seconds = _unknown_main_seconds(kept_main_segs, reference_decisions, eligible_main)
                new_unknown_seconds = _unknown_main_seconds(
                    identity_refinement["segments"], identity_refinement["decisions"], eligible_main)
                identity_refinement["recovered_seconds"] = old_unknown_seconds-new_unknown_seconds
                kept_main_segs = identity_refinement["segments"]
                reference_decisions = tuple(identity_refinement["decisions"])
                raw_labels = identity_refinement["labels"]
                selected_evidence = identity_refinement["previews"]

        if reference_samples:
            from .scene_context import preserve_main_context
            from .scene_boundaries import align_scene_segments_from_source
            context_cuts = None if scene_context_cuts is None else sorted(
                set(scene_context_cuts) | {round(c['cut_time']*fps)
                    for c in scene_boundary_refinement.get('changes',[])})
            context_recs, scene_context_refinement = preserve_main_context(
                recs, identity_refinement, secondary_refinement.get('joint_matches',{}),
                video_size=self._video_size(input_video), fps=fps, cut_frames=context_cuts,
                handoffs=main_role_refinement.get('handoffs', ()),
                camera_transitions=mask_continuity_refinement.get('context_faces', {}).get('camera_transitions', ()))
            if scene_context_refinement['changes']:
                context_main = build_main_evidence_scopes(build_raw_main_segments(context_recs))
                context_group = build_raw_group_segments(context_recs)
                context_main, context_group, context_boundaries = align_scene_segments_from_source(
                    context_recs, context_main, context_group, video_path=input_video, fps=fps,
                    cut_frames=context_cuts, sample_step=max(1, int(self.config.analyze_skip)))
                if context_boundaries.get('reason') == 'complete':
                    scene_context_refinement['added_main_seconds'] = (
                        sum(s.end-s.start for s in context_main)-sum(s.end-s.start for s in eligible_main))
                    recs, eligible_main, raw_group = context_recs, context_main, context_group
                    scene_boundary_refinement = context_boundaries
                    group_segs = smooth_group_segments(raw_group, min_group_seg_sec=.15, merge_gap_sec=0.)
                else:
                    # Keep the already verified output if rereading the source fails.
                    scene_context_refinement.update(reason='scene_alignment_unavailable',
                        proposed_changes=scene_context_refinement['changes'],changes=[],
                        alignment=context_boundaries)
            from .scene_boundaries import project_main_at_scene_cuts, split_unidentified_at_handoffs
            if main_role_refinement.get('camera_episodes') and 'evidence' in identity_refinement:
                from .focal_output import restore_focal_output
                source_cuts = main_role_refinement['cut_frames']
                source_frames = [round(r.t*fps) for r in recs]
                bounds = []
                for episode in main_role_refinement['camera_episodes']:
                    first, last = episode['start_frame'], episode['end_frame']
                    lo, hi = source_frames.index(first), source_frames.index(last)
                    start = recs[lo].t
                    previous = source_frames[lo-1] if lo else -1
                    leading_cuts = [cut for cut in source_cuts if previous < cut <= first]
                    if leading_cuts:
                        start = max(leading_cuts)/fps
                    end = recs[hi+1].t if hi+1 < len(recs) else min(duration, recs[hi].t+1/fps)
                    end = min([end]+[cut/fps for cut in source_cuts if last < cut and cut/fps < end])
                    bounds.append((start, end))
                identity_refinement, focal_output = restore_focal_output(
                    identity_refinement, main_role_refinement['camera_episodes'], recs,
                    secondary_refinement.get('joint_matches', {}), fps=fps,
                    cut_frames=source_cuts, bounds=bounds,
                    handoffs=main_role_refinement.get('handoffs', ()))
                main_role_refinement['output_context'] = focal_output
                if focal_output['restored']:
                    # Role coverage is separate from visible face coverage.
                    # Only the verified episode's actual face observations are
                    # retained; hidden frames supply no borrowed face evidence.
                    extra = [Segment('main', None, p['start'], p['end'], [])
                             for p in focal_output['restored']]
                    eligible_main = [part for _, part in intersect_main_segments(
                        [Segment('main', None, 0., duration, [])], [*eligible_main, *extra])]
                    kept_main_segs = identity_refinement['segments']
                    reference_decisions = tuple(identity_refinement['decisions'])
                    raw_labels = identity_refinement['labels']
                    selected_evidence = identity_refinement['previews']
            projected, projection_audit = project_main_at_scene_cuts(
                kept_main_segs, eligible_main, fps=fps,
                cut_times=[c['cut_time'] for c in scene_boundary_refinement.get('changes',[])])
            scene_boundary_refinement.update(projection_audit)
            projected, handoff_audit = split_unidentified_at_handoffs(
                projected, reference_decisions,
                main_role_refinement.get('handoffs', []) if main_role_refinement.get('reason') == 'complete' else [])
            scene_boundary_refinement['unidentified_handoffs'] = handoff_audit
            indices = [index for index, _ in projected]
            accurate = set(identity_refinement['accurate_indices'])
            kept_main_segs = [part for _, part in projected]
            reference_decisions = tuple(reference_decisions[index] for index in indices)
            raw_labels = [raw_labels[index] for index in indices]
            selected_evidence = [selected_evidence[index] for index in indices]
            identity_refinement['accurate_indices'] = [i for i, old in enumerate(indices) if old in accurate]
            # Inference audit retains context; final arrays describe output only.
            if 'segments' in identity_refinement:
                identity_refinement['segments'] = kept_main_segs
                identity_refinement['decisions'] = list(reference_decisions)
                identity_refinement['labels'] = raw_labels
                identity_refinement['previews'] = selected_evidence
                evidence, sources, images = [], [], []
                for index, part in projected:
                    selected = [(row, name) for row, name in identity_refinement['evidence'][index]
                                if part.start <= row.time_seconds < part.end]
                    thumbnails, owned = identity_refinement['preview_sources'][index]
                    candidates = sorted((row for row, _ in selected), key=lambda row: row.quality, reverse=True)
                    images.append([thumbnails.get(row.frame_index) or owned[row.frame_index]
                                   for row in candidates if row.frame_index in thumbnails or row.frame_index in owned][:5])
                    evidence.append(selected)
                    sources.append((thumbnails, owned))
                identity_refinement['evidence'] = evidence
                identity_refinement['preview_sources'] = sources
                identity_refinement['previews'] = selected_evidence = images
                if matcher is not None:
                    from .output_continuity import coalesce_named_output
                    identity_refinement, output_continuity_refinement = coalesce_named_output(
                        identity_refinement, matcher,
                        handoffs=main_role_refinement.get('handoffs')
                        if main_role_refinement.get('reason') == 'complete' else None,
                        joint_matches=secondary_refinement.get('joint_matches', {}),
                        frame_records=recs, fps=fps,
                        cut_frames=main_role_refinement.get('cut_frames'),
                        mask_refinement=mask_continuity_refinement)
                    identity_refinement, preparation_context = _include_incoming_preparation(
                        identity_refinement, recs, secondary_refinement.get('joint_matches', {}),
                        video_path=input_video, fps=fps,
                        cut_frames=main_role_refinement.get('cut_frames'),
                        face_service=self.face, joint_context=joint_context)
                    main_role_refinement['preparation_context'] = preparation_context
                    kept_main_segs = identity_refinement['segments']
                    reference_decisions = tuple(identity_refinement['decisions'])
                    raw_labels = identity_refinement['labels']
                    selected_evidence = identity_refinement['previews']
            else:
                # Without per-frame evidence no context image can be claimed
                # to belong to a newly cropped output interval.
                selected_evidence = [[] for _ in projected]

        release_person_thumbnails(all_face_results)

        # 4. unique cluster label 수집 (None 제외)
        unique_labels = sorted({lab for lab in raw_labels if lab is not None})

        # 5. 연속 번호 재매핑
        label_map = {old: idx + 1 for idx, old in enumerate(unique_labels)}

        # 6. 최종 person_ids 생성
        person_ids: List[str] = []
        for lab, decision in zip(raw_labels, reference_decisions, strict=True):
            member_name = decision.reference_id if decision.status == "matched" else None
            if member_name is not None:
                safe_name = _safe_filename(member_name).lower().replace(" ", "_")
                person_ids.append(safe_name)
            elif lab is None:
                person_ids.append("unknown")
            else:
                person_ids.append(f"person_{label_map[lab]}")
            print(
                f"[MATCH] segment={len(person_ids) - 1} status={decision.status}"
                f" reason={decision.reason} member={member_name or '-'}",
                flush=True,
            )

        _timings["cluster_map"] = time.perf_counter() - _t
        print(
            f"[DANCE][T] cluster_map: {_fmt(_timings['cluster_map'])}"
            f"  (embs={len(all_embs)}, clusters={len(unique_labels)},"
            f" persons={len(set(p for p in person_ids if p != 'unknown'))})",
            flush=True,
        )
        _progress(70, "함께 등장 멤버를 확인하고 있습니다")
        group_face_samples = self._collect_group_face_samples(str(input_video), group_segs, recs)
        group_face_matches: list[tuple[int, float, SegmentReferenceDecision]] = []
        if group_face_samples and reference_samples:
            source_hash = sha256_file(input_video)
            model_hashes = {spec.name: spec.sha256 for spec in FACE_MODEL_SPECS}
            scopes = tuple(
                SegmentEmbeddingScope(
                    scope_id=f"group-{group_index}-face-{index}",
                    start_sec=frame_time,
                    end_sec=frame_time + 1 / max(1.0, fps),
                    track_embeddings=(embedding,),
                )
                for index, (group_index, frame_time, embedding) in enumerate(group_face_samples)
            )
            face_decisions = assign_reference_person_ids(
                references=reference_samples,
                scopes=scopes,
                analysis_id=f"dance-project-{project_id}-{source_hash[:12]}",
                video_sha256=source_hash,
                detector_sha256=model_hashes["opencv-yunet-face-detection"],
                recognizer_sha256=model_hashes[AURAFACE_MODEL_NAME],
                config_sha256=hashlib.sha256(repr(self.config).encode("utf-8")).hexdigest(),
                backend_version=f"opencv-{cv2.__version__}",
                video_size=self._video_size(input_video),
                max_distance=0.60,
                min_margin=0.05,
            )
            group_face_matches = [
                (group_index, frame_time, decision)
                for (group_index, frame_time, _), decision in zip(
                    group_face_samples, face_decisions, strict=True,
                )
            ]
        group_recipients = confirmed_group_recipients(
            group_segs, baseline_main_segments, baseline_reference_decisions, group_face_matches,
        )
        _progress(75, "장면 썸네일을 생성하고 있습니다")

        # 원본 구간과 썸네일만 저장한다. 장면 영상은 내보내기 시 생성한다.
        _t = time.perf_counter()
        main_items: List[DanceClipItem] = []
        total_main_clips = max(len(kept_main_segs), 1)
        for idx, seg in enumerate(kept_main_segs):
            person_id = person_ids[idx]
            thumb_path = clips_main_dir / f"main_{idx:04d}.jpg"
            self.render.extract_thumbnail(str(input_video), thumb_path, ts_sec=float(seg.start))

            main_items.append(DanceClipItem(
                seg_id=idx,
                seg_type="main",
                start=float(seg.start),
                end=float(seg.end),
                clip_path=None,
                person_id=person_id,
                clip_id=f"main_{idx:04d}",
                thumbnail_path=str(thumb_path.relative_to(project_root)),
            ))
            p = 75 + int((idx + 1) / total_main_clips * 7)  # 75% → 82%
            _progress(p, "장면 썸네일을 생성하고 있습니다")

        _timings["clips_main"] = time.perf_counter() - _t
        print(
            f"[DANCE][T] clips_main: {_fmt(_timings['clips_main'])}"
            f"  (n={len(kept_main_segs)})",
            flush=True,
        )

        _t = time.perf_counter()
        group_items: List[DanceClipItem] = []
        total_group_clips = max(len(group_segs), 1)
        for idx, seg in enumerate(group_segs):
            thumb_path = clips_group_dir / f"group_{idx:04d}.jpg"
            self.render.extract_thumbnail(str(input_video), thumb_path, ts_sec=float(seg.start))

            group_items.append(DanceClipItem(
                seg_id=idx,
                seg_type="group",
                start=float(seg.start),
                end=float(seg.end),
                clip_path=None,
                person_id=None,
                # Visible group participants are not solo main performers.
                # Keep this clip in the shared bucket; user assignment is explicit.
                person_ids=(),
                clip_id=f"group_{idx:04d}",
                thumbnail_path=str(thumb_path.relative_to(project_root)),
            ))
            p = 82 + int((idx + 1) / total_group_clips * 3)  # 82% → 85%
            _progress(p, "단체 장면 썸네일을 생성하고 있습니다")

        _timings["clips_group"] = time.perf_counter() - _t
        print(
            f"[DANCE][T] clips_group: {_fmt(_timings['clips_group'])}"
            f"  (n={len(group_segs)})",
            flush=True,
        )

        # person별 clip 모으기
        person_to_clips: Dict[str, List[str]] = {}
        for item in main_items:
            pid = item.person_id or "unknown"
            assert item.clip_id is not None
            person_to_clips.setdefault(pid, []).append(item.clip_id)

        persons: List[Dict[str, Any]] = []
        person_images = persist_person_thumbnails(project_root, person_ids, selected_evidence)

        _progress(85, "인물별로 클립을 정리하고 있습니다")

        person_items = sorted(person_to_clips.items(), key=lambda kv: kv[0])

        # persons 목록 순서 보존하며 수집
        for pid, clips in person_items:
            clips_sorted = sorted(clips)
            persons.append({
                "person_id": pid,
                "person_name": self._person_display_name(pid),
                "num_clips": len(clips_sorted),
                "clip_ids": clips_sorted,
            })
            if pid in person_images:
                persons[-1]["person_image_path"] = person_images[pid]

        _progress(90, "인물 정보를 정리했습니다")

        stats = {
            "reference_matching": "shared_reference_v1",
            "main_selection_policy": main_role_refinement.get("version") if main_role_refinement.get("reason") == "complete" else "current_frame_elapsed_v2",
            "scene_policy": "observed_ensemble_v3_pose_extent" if reference_samples else "legacy_group_overlap",
            "scene_group_seconds": scene_boundary_refinement.get("scene_group_seconds", sum(b.t-a.t for a,b in zip(recs,recs[1:]) if a.scene_kind == 'group')),
            "scene_boundary_policy": scene_boundary_refinement.get("version") if scene_boundary_refinement.get("reason") == "complete" else "observed_sample_edges",
            "native_scene_policy": native_scene_refinement.get('version'),
            "native_scene_changed_observations": len(native_scene_refinement.get('changes',[])),
            "scene_context_policy": scene_context_refinement.get('version'),
            "scene_context_added_main_seconds": scene_context_refinement.get('added_main_seconds',0.),
            "secondary_reference_recovery": secondary_refinement.get('version'),
            "secondary_reference_recovered_seconds": secondary_recovered_seconds,
            "body_continuity_recovery": body_continuity_refinement.get('version'),
            "body_continuity_recovered_seconds": body_continuity_refinement.get('output_changes', {}).get('recovered_seconds',0.),
            "mask_continuity_recovery": mask_continuity_refinement.get('version'),
            "mask_continuity_recovered_seconds": mask_continuity_refinement.get('output_changes', {}).get('recovered_seconds',0.),
            "joint_identity_revalidation": joint_identity_refinement.get('version'),
            "joint_identity_corrected_seconds": joint_identity_refinement.get('output_changes', {}).get('corrected_seconds',0.),
            "joint_identity_recovered_seconds": joint_identity_refinement.get('output_changes', {}).get('recovered_seconds',0.),
            "joint_identity_conflict_seconds": joint_identity_refinement.get('output_changes', {}).get('conflict_seconds',0.),
            "main_identity_refinement": "member_timeline_evidence_first_v6_independent_pair",
            "main_scope_policy": "identity_context_before_scene_mask" if reference_samples else "legacy_body_smoothing",
            "main_face_sampling": "all_pose_observations" if reference_samples else "interval_and_candidates",
            "main_evidence_scope_count": len(main_segs),
            "main_evidence_seconds": sum(s.end-s.start for s in main_segs),
            "main_eligible_seconds": sum(s.end-s.start for s in eligible_main),
            "output_named_continuity": output_continuity_refinement.get('version'),
            "output_named_join_count": len(output_continuity_refinement.get('joins', [])),
            "incoming_preparation_context_count": len(main_role_refinement.get('preparation_context', {}).get('accepted', [])),
            "visible_member_clips_added": identity_refinement.get("visible_member_clips_added", 0),
            "identity_split_parent_count": sum(row["applied"] and len(row["pieces"]) > 1 for row in identity_refinement["audit"]),
            "identity_recovered_seconds": identity_refinement.get("recovered_seconds", 0),
            "reference_match_distance_max": float(self.config.member_match_threshold),
            "reference_match_min_margin": 0.0,
            "reference_match_status_counts": {
                status: sum(decision.status == status for decision in reference_decisions)
                for status in ("matched", "ambiguous", "unmatched", "invalid")
            },
            "fps": float(fps),
            "duration_sec": float(duration),
            "raw_main_segments": int(len(raw_main)),
            "raw_group_segments": int(len(raw_group)),
            "smoothed_main_segments": int(len(main_segs)),
            "smoothed_group_segments": int(len(group_segs)),
            "kept_main_segments": int(len(kept_main_segs)),
            "dropped_main_no_face": int(dropped_no_face),
            "num_persons_inferred": int(len([p for p in person_to_clips.keys() if p != "unknown"])),
        }

        input_rel = str(input_video.relative_to(project_root)) if str(input_video).startswith(str(project_root)) else str(input_video)

        _progress(95, "결과를 정리하고 있습니다")

        meta = self.meta_builder.build(
            project_id=project_id,
            input_video_rel=input_rel,
            main_items=main_items,
            group_items=group_items,
            persons=persons,
            stats=stats,
            dance_setup=dance_setup,
        )

        diagnostic_root = project_root / "diagnostics"
        diagnostic_root.mkdir(parents=True, exist_ok=True)
        source_copy = diagnostic_root / f"source{input_video.suffix.lower() or '.mp4'}"
        if input_video != source_copy and (
            not source_copy.exists() or not source_copy.samefile(input_video)
        ):
            # The prior source may be a hard link; replace the link, not its contents.
            source_copy.unlink(missing_ok=True)
            try:
                if os.environ.get('CLIPPER_ACCELERATORS_WHOLE_UNIT_RECOVERY')=='1':
                    shutil.copy2(input_video, source_copy)
                else:
                    os.link(input_video, source_copy)
            except OSError:
                shutil.copy2(input_video, source_copy)
        meta["media_mode"] = "source_ranges"
        meta["source_video_path"] = str(source_copy.relative_to(project_root))

        query_root = diagnostic_root / "query"
        query_root.mkdir(exist_ok=True)

        clip_evidence: list[dict[str, Any]] = []
        for index, item in enumerate(main_items):
            segment = kept_main_segs[index]
            decision = reference_decisions[index]
            member = decision.reference_id or decision.closest_reference_id
            query_paths: List[str] = []
            for image_index, image_bytes in enumerate(selected_evidence[index][:5]):
                path = query_root / f"main_{index:04d}_{image_index}.jpg"
                path.write_bytes(image_bytes)
                query_paths.append(str(path.relative_to(project_root)))
            clip_evidence.append({
                "clip_id": item.clip_id,
                "thumbnail_path": item.thumbnail_path,
                "start": item.start,
                "end": item.end,
                "person_id": item.person_id,
                "seg_type": item.seg_type,
                "main_track_id": segment.label,
                "body_samples": [
                    {"t": round(float(t), 3), "bbox": [round(float(value), 2) for value in bbox]}
                    for t, bbox, _ in segment.bboxes
                ],
                "cluster_id": raw_labels[index],
                "group_overlap_ratio": round(max((
                    self._segment_overlap_ratio(segment.start, segment.end, group.start, group.end)
                    for group in group_segs
                ), default=0.0), 3),
                "match_status": decision.status,
                "match_reason": decision.reason,
                "matched_reference": decision.reference_id,
                "closest_reference": member,
                "closest_distance": decision.distance if decision.reference_id else decision.closest_distance,
                "distance_threshold": float(decision.decision_threshold or self.config.member_match_threshold),
                "query_images": query_paths,
                "reference_images": [str(path.relative_to(project_root)) for path in ref_image_paths.get(member or "", [])],
            })
        clip_evidence.extend({
            "clip_id": item.clip_id,
            "thumbnail_path": item.thumbnail_path,
            "start": item.start,
            "end": item.end,
            "person_id": item.person_id,
            "seg_type": item.seg_type,
            "match_status": "group",
            "match_reason": "similar_prominence",
            "visible_reference_ids": list(group_recipients[index]),
        } for index, item in enumerate(group_items))
        width, height = self._video_size(input_video)
        no_face_scopes = [
            {"start": float(result.seg.start), "end": float(result.seg.end), "reason": "no_face_samples"}
            for result in face_results if not (result.face_detected and result.track_embeddings)
            and not any(o.association == "confirmed" and o.embedding is not None and not o.failure
                        for o in getattr(result, "owned_observations", []))
        ]
        meta["diagnostics"] = {
            "schema_version": "dance_diagnostics_v1",
            "source_video_path": str(source_copy.relative_to(project_root)),
            "frame_width": width,
            "frame_height": height,
            "frames": frame_diagnostics(recs),
            "identity_refinement": identity_refinement["audit"],
            "merged_main_runs": identity_refinement.get("merged_main_runs", []),
            "output_named_continuity": output_continuity_refinement,
            "raw_main_runs": [{"start": float(s.start), "end": float(s.end), "track_id": s.label}
                              for s in raw_main],
            "visible_member_refinement": identity_refinement.get("visible_audit", []),
            "clips": clip_evidence,
            "gaps": [
                {"start": start, "end": end}
                for start, end in coverage_gaps(duration, ((item.start, item.end) for item in [*main_items, *group_items]))
            ],
            "rejections": [] if reference_samples else no_face_scopes,
            "unresolved_main_scopes": no_face_scopes if reference_samples else [],
        }

        from .face_evidence import write_face_evidence
        evidence_path = diagnostic_root / "face_evidence.json"
        write_face_evidence(evidence_path, input_video=input_video, config=self.config,
                            face_service=self.face, results=all_face_results, records=recs,
                            references=reference_samples, refinement=identity_refinement["audit"],
                            visible_refinement=identity_refinement.get("visible_audit", []),
                            secondary_refinement=secondary_refinement,
                            body_continuity_refinement=body_continuity_refinement,
                            mask_continuity_refinement=mask_continuity_refinement,
                            main_selection_refinement=main_role_refinement,
                            scene_boundary_refinement=scene_boundary_refinement,
                            scene_context_refinement=scene_context_refinement,
                            native_scene_refinement=native_scene_refinement,
                            output_continuity_refinement=output_continuity_refinement,
                            main_result_count=len(face_results))
        meta["diagnostics"]["face_evidence_path"] = str(evidence_path.relative_to(project_root))

        out_meta = json_root / self.config.meta_filename
        out_meta.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

        _t_elapsed = time.perf_counter() - _t_total
        print(
            f"[DANCE][T] TOTAL: {_fmt(_t_elapsed)}"
            f"  | download_refs={_fmt(_timings.get('download_refs', 0))}"
            f"  yolo={_fmt(_timings.get('yolo', 0))}"
            f"  ref_embs={_fmt(_timings.get('ref_embs', 0))}"
            f"  segment_build={_fmt(_timings.get('segment_build', 0))}"
            f"  face_extract={_fmt(_timings.get('face_extract', 0))}"
            f"  cluster_map={_fmt(_timings.get('cluster_map', 0))}"
            f"  clips_main={_fmt(_timings.get('clips_main', 0))}"
            f"  clips_group={_fmt(_timings.get('clips_group', 0))}",
            flush=True,
        )

        return meta


def create_default_pipeline(config: DanceConfig | None = None) -> DancePipeline:
    """기본 구체 구현으로 DancePipeline을 생성하는 팩토리."""
    from .pose_engine import PoseEngine
    from .face_cluster import FaceClusterService
    from .render import RenderService
    from .dance_meta import DanceMetaBuilder

    if config is None:
        config = DanceConfig()

    return DancePipeline(
        config=config,
        pose=PoseEngine(config),
        face=FaceClusterService(config),
        render=RenderService(config),
        meta_builder=DanceMetaBuilder(config),
    )
