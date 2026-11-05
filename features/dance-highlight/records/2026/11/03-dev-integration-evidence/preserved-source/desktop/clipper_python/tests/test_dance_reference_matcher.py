"""The app assigns registered members from each selected main segment's face evidence."""

import importlib
import importlib.util
from types import SimpleNamespace

import numpy as np
import pytest


def _api():
    name = "dance_highlight.services.reference_matcher"
    assert importlib.util.find_spec(name) is not None, "Dance reference adapter is missing"
    return importlib.import_module(name)


def _vector(x, y):
    value = np.asarray([x, y], dtype=np.float32)
    return value / (np.linalg.norm(value) + 1e-9)


def _assign(scopes):
    matcher = _api()
    return matcher.assign_reference_person_ids(
        references=(
            matcher.ReferenceEmbeddingSample("A", "A/0", "a" * 64, 100, 100, _vector(1, 0)),
            matcher.ReferenceEmbeddingSample("B", "B/0", "b" * 64, 100, 100, _vector(0, 1)),
        ),
        scopes=scopes,
        analysis_id="test-run",
        video_sha256="c" * 64,
        detector_sha256="d" * 64,
        recognizer_sha256="e" * 64,
        config_sha256="f" * 64,
        backend_version="opencv-test",
        video_size=(1920, 1080),
        max_distance=0.6,
        min_margin=0.0,
    )


def test_separate_main_segments_can_both_match_same_member():
    Scope = _api().SegmentEmbeddingScope
    result = _assign((
        Scope("segment-0", 0.0, 1.0, (_vector(1, 0),)),
        Scope("segment-1", 2.0, 3.0, (_vector(.98, .02),)),
    ))

    assert [item.reference_id for item in result] == ["A", "A"]
    assert [item.status for item in result] == ["matched", "matched"]


def test_conflicting_faces_inside_one_segment_remain_unassigned():
    Scope = _api().SegmentEmbeddingScope
    result = _assign((
        Scope("segment-0", 0.0, 1.0, (_vector(1, 0), _vector(0, 1))),
    ))

    assert result[0].reference_id is None
    assert result[0].status == "ambiguous"
    assert result[0].reason == "conflicting_references"


def test_face_without_a_close_reference_remains_unassigned():
    Scope = _api().SegmentEmbeddingScope
    result = _assign((
        Scope("segment-0", 0.0, 1.0, (_vector(-1, 0),)),
    ))

    assert result[0].reference_id is None
    assert result[0].status == "unmatched"
    assert result[0].closest_reference_id in ("A", "B")
    assert result[0].closest_distance is not None
    assert result[0].decision_threshold == 0.6


def test_only_majority_main_cluster_faces_can_name_segment():
    from dance_highlight.services.pipeline import select_majority_cluster_embeddings

    # A background face matches B; two selected-main tracks do not.
    selected = select_majority_cluster_embeddings(
        embeddings=(_vector(-1, 0), _vector(-1, 0), _vector(0, 1)),
        track_map=(0, 0, 0),
        labels=(4, 4, 9),
        raw_labels=(4,),
    )
    matcher = _api()
    decisions = matcher.assign_reference_person_ids(
        references=(matcher.ReferenceEmbeddingSample("B", "B/0", "b" * 64, 100, 100, _vector(0, 1)),),
        scopes=(matcher.SegmentEmbeddingScope("segment-0", 0.0, 1.0, selected[0], cluster_id=4),),
        analysis_id="test-run",
        video_sha256="c" * 64,
        detector_sha256="d" * 64,
        recognizer_sha256="e" * 64,
        config_sha256="f" * 64,
        backend_version="opencv-test",
        video_size=(1920, 1080),
        max_distance=0.6,
        min_margin=0.0,
    )

    assert len(selected[0]) == 2
    assert decisions[0].reference_id is None


def test_duplicate_cluster_guard_rejects_weak_second_match():
    matcher = _api()
    references = (matcher.ReferenceEmbeddingSample("A", "A/0", "a" * 64, 100, 100, _vector(1, 0)),)
    scopes = (
        matcher.SegmentEmbeddingScope("segment-0", 0.0, 1.0, (_vector(1, 0),), cluster_id=4),
        matcher.SegmentEmbeddingScope("segment-1", 2.0, 3.0, (_vector(.5, .866),), cluster_id=9),
    )
    decisions = matcher.assign_reference_person_ids(
        references=references,
        scopes=scopes,
        analysis_id="test-run",
        video_sha256="c" * 64,
        detector_sha256="d" * 64,
        recognizer_sha256="e" * 64,
        config_sha256="f" * 64,
        backend_version="opencv-test",
        video_size=(1920, 1080),
        max_distance=0.6,
        min_margin=0.0,
        duplicate_threshold=0.45,
        duplicate_margin=0.08,
    )

    assert decisions[0].reference_id == "A"
    assert decisions[1].reference_id is None
    assert decisions[1].reason == "duplicate_cluster_distance_exceeded"
    assert decisions[1].closest_reference_id == "A"
    assert decisions[1].decision_threshold == 0.08


def test_invalid_gallery_returns_unresolved_instead_of_aborting_job():
    matcher = _api()
    decisions = matcher.assign_reference_person_ids(
        references=(matcher.ReferenceEmbeddingSample("A", "A/0", "a" * 64, 100, 100, np.zeros(2)),),
        scopes=(matcher.SegmentEmbeddingScope("segment-0", 0.0, 1.0, (_vector(1, 0),)),),
        analysis_id="test-run",
        video_sha256="c" * 64,
        detector_sha256="d" * 64,
        recognizer_sha256="e" * 64,
        config_sha256="f" * 64,
        backend_version="opencv-test",
        video_size=(1920, 1080),
        max_distance=0.6,
        min_margin=0.0,
    )

    assert decisions[0].status == "invalid"
    assert decisions[0].reason == "no_valid_references"


def test_dance_pipeline_passes_main_tracks_to_shared_matcher(tmp_path):
    from dance_highlight.services.pipeline import DancePipeline
    from dance_highlight.services.segment import Segment

    pipeline = DancePipeline.__new__(DancePipeline)
    pipeline.config = SimpleNamespace(
        member_match_threshold=0.6,
        member_duplicate_threshold=0.45,
        member_duplicate_margin=0.08,
    )
    video = tmp_path / "source.mp4"
    video.write_bytes(b"fixed-test-source")
    matcher = _api()
    references = [
        matcher.ReferenceEmbeddingSample("A", "A/0", "a" * 64, 100, 100, _vector(1, 0)),
        matcher.ReferenceEmbeddingSample("B", "B/0", "b" * 64, 100, 100, _vector(0, 1)),
    ]
    segments = [
        Segment("main", 1, 0.0, 1.0, []),
        Segment("main", 2, 2.0, 3.0, []),
    ]
    decisions = pipeline._assign_reference_members(
        segments=segments,
        selected_track_embeddings=((_vector(1, 0),), (_vector(1, 0),)),
        cluster_ids=(0, 1),
        reference_samples=references,
        input_video=video,
        project_id=42,
        video_size=(1920, 1080),
    )

    assert [decision.reference_id for decision in decisions] == ["A", "A"]


@pytest.mark.parametrize("with_refinement,invalid_gallery,with_handoff", [(False,False,False),(True,False,False),(False,True,False),(True,False,True)])
def test_app_run_preserves_identity_decisions_as_source_ranges(tmp_path, monkeypatch, with_refinement, invalid_gallery, with_handoff):
    from dance_highlight.services import pipeline as pipeline_module
    from dance_highlight.services.pipeline import DancePipeline
    from dance_highlight.services.segment import Segment

    segments = [Segment("main", 1, 0.0, 1.0, []), Segment("main", 2, 2.0, 5.0 if with_refinement else 3.0, [])]
    group_start = 3.1 if with_refinement else 3.0
    group_segments = [Segment("group", None, group_start, 4.0, [])]
    monkeypatch.setattr(pipeline_module, "build_raw_main_segments", lambda _: segments)
    monkeypatch.setattr(pipeline_module, "build_raw_group_segments", lambda _: group_segments)
    monkeypatch.setattr(pipeline_module, "smooth_main_segments", lambda rows, **_: rows)
    monkeypatch.setattr(pipeline_module, "smooth_group_segments", lambda rows, **_: rows)

    class Face:
        def get_face_embedding_candidate(self, _image):
            # These fixture photos are 2x2 white pixels, with no real face for
            # the optional independent/context face extraction stages.
            return None

        def get_face_embedding_from_image_path(self, _path):
            return _vector(1, 0)

        def average_embeddings(self, values):
            return _vector(1, 0)

        def batch_segment_embeddings(self, _video, rows, on_progress=None, *, frame_records=None, evidence_only_indices=frozenset(), sample_all_main_frames=False):
            from dance_highlight.services.face_evidence import FaceObservation
            results=[]
            for i,seg in enumerate(rows):
                owned=[FaceObservation(round(t*30),float(t),i+1,(0.,0.,300.,300.),(0.,0.,300.,300.),
                        face_bbox=(100.,100.,200.,200.),embedding=_vector(1,0),
                        detector_score=.95,association='confirmed') for t in np.arange(seg.start+.1,seg.end,.2)]
                if with_refinement and i==1:
                    owned=[]
                    for t in np.arange(2.1,5.,.2):
                        owned.append(FaceObservation(round(t*30),float(t),2,(0.,0.,300.,300.),(0.,0.,300.,300.),
                            face_bbox=(10.,10.,20.,20.) if t<3. else (100.,100.,200.,200.),
                            embedding=_vector(-1,0) if t<3. else _vector(1,0),detector_score=.95,association='confirmed'))
                results.append(SimpleNamespace(seg=seg,track_embeddings=[_vector(-1,0) if with_refinement and i==1 else _vector(1,0)],
                    face_detected=True,track_evidence_images=[[b"matched-face-preview"]],owned_observations=owned,
                    owned_previews={o.frame_index:b"matched-face-preview" for o in owned}))
            return results

        def cluster_embeddings(self, _values):
            return [0, 1]

    class Render:
        def extract_clip(self, _video, path, _start, _end, **kwargs):
            pytest.fail("Source-range analysis must defer all video encoding to export")

        def extract_thumbnail(self, _video, path, ts_sec):
            path.write_bytes(b"image")

    from dance_highlight.services.dance_meta import DanceMetaBuilder
    from dance_highlight.services.config import DanceConfig

    import cv2
    image = np.full((2, 2, 3), 255, dtype=np.uint8)
    ok, encoded = cv2.imencode(".png", image)
    assert ok
    photos = []
    for index in range(3):
        path = tmp_path / f"photo-{index}.png"
        path.write_bytes(encoded.tobytes())
        photos.append(path)
    video = tmp_path / "source.mp4"
    video.write_bytes(b"video-source-for-test")
    pipeline = DancePipeline.__new__(DancePipeline)
    pipeline.config = DanceConfig(
        min_main_seg_sec=0.0, bridge_gap_sec=0.0, merge_gap_sec=0.0, min_group_seg_sec=0.0,
    )
    pipeline.pose = None  # Video records are supplied by this identity-path fixture.
    pipeline.face = Face()
    pipeline.render = Render()
    pipeline.meta_builder = DanceMetaBuilder(pipeline.config)
    pipeline.analyze_video_to_records = lambda *_args, **_kwargs: ([], 30.0, 5.0)
    pipeline._download_reference_images = lambda *_args: {"A": photos}
    pipeline._collect_group_face_samples = lambda *_args: [] if with_refinement else [
        (0, 3.2, _vector(1, 0)), (0, 3.8, _vector(1, 0)),
    ]
    pipeline._filter_group_like_main_segments = lambda main_segs, **_kwargs: main_segs
    pipeline._video_size = lambda _path: (1920, 1080)
    pipeline._map_cluster_to_member_name = lambda **_kwargs: (_ for _ in ()).throw(
        AssertionError("legacy global cluster mapping must not decide registered member names")
    )

    if invalid_gallery:
        def invalid_references(_paths, *, sample_sink):
            matcher = _api()
            sample_sink.extend([
                matcher.ReferenceEmbeddingSample("A","A/0","a"*64,100,100,_vector(1,0)),
                matcher.ReferenceEmbeddingSample("A","A/1","b"*64,100,100,_vector(-1,0)),
            ])
            return {"A": np.zeros(2)}
        pipeline._build_reference_embeddings = invalid_references

    if with_handoff:
        from dance_highlight.services import observed_main
        monkeypatch.setattr(observed_main, "refine_main_roles", lambda records,*a,**k:(records,dict(
            reason="complete",cut_frames=[],handoffs=[dict(frame=75,time=2.5),dict(frame=105,time=3.5)])))

    result = pipeline.run(tmp_path, video, 42)
    main = result["lists"]["main"]
    person_ids = [clip["person_id"] for clip in main]
    assert result["media_mode"] == "source_ranges"
    assert result["source_video_path"] == "diagnostics/source.mp4"
    assert not list((tmp_path / "clips").rglob("*.mp4"))
    assert all("clip_path" not in clip for clip in main)
    assert [clip["clip_id"] for clip in main] == [f"main_{i:04d}" for i in range(len(main))]
    assert all((tmp_path / clip["thumbnail_path"]).is_file() for clip in main)
    if with_refinement:
        assert [clip["start"] for clip in main] == pytest.approx([0., 2., 2.5, 3.] if with_handoff else [0., 2., 3.])
        assert [clip["end"] for clip in main] == pytest.approx([1., 2.5, 3., 5.] if with_handoff else [1., 3., 5.])

    if invalid_gallery:
        assert all(name.startswith("person_") for name in person_ids)
        assert result["stats"]["identity_split_parent_count"]==0
    elif with_refinement:
        assert person_ids[0]==person_ids[-1]=="a"
        assert person_ids==(["a","unknown","unknown","a"] if with_handoff else ["a","unknown","a"])
        assert result["stats"]["identity_split_parent_count"]==1
    else:
        assert person_ids == ["a", "a"]
    # A group face never becomes main evidence. Only the *output card* is
    # redundant when the already-established named main contains its whole range.
    assert [tuple(clip["person_ids"]) for clip in result["lists"]["group"]] == ([] if with_refinement else [()])
    assert result["stats"]["reference_matching"] == "shared_reference_v1"
    diagnostics = result["diagnostics"]
    original_group = [clip for clip in diagnostics['clips'] if clip['seg_type'] == 'group']
    assert [(clip['clip_id'], clip['start'], clip['end']) for clip in original_group] == [('group_0000', group_start, 4.)]
    assert (tmp_path / original_group[0]['thumbnail_path']).is_file()
    projection = diagnostics['group_output_projection']
    assert projection['classification_changed'] is False
    assert len(projection['suppressed']) == int(with_refinement)
    assert result['stats']['smoothed_group_segments'] == 1
    assert diagnostics["schema_version"] == "dance_diagnostics_v1"
    import json
    evidence = json.loads((tmp_path / diagnostics["face_evidence_path"]).read_text())
    assert evidence['schema_version'] == 'dance_face_evidence_v1'
    if with_handoff:
        assert [c['time'] for c in evidence['scene_boundary_refinement']['unidentified_handoffs']['changes']]==[2.5]
    assert len(evidence['segments']) == 2
    assert evidence['runtime']['video_sha256']
    for module in ('face_cluster','main_identity','face_recovery','face_evidence'):
        assert evidence['runtime']['modules'][module]['sha256']
    assert evidence['policy']['recovery_applied'] is (not invalid_gallery)
    assert diagnostics["source_video_path"] == "diagnostics/source.mp4"
    assert (tmp_path / diagnostics["source_video_path"]).read_bytes() == b"video-source-for-test"
    assert diagnostics["gaps"] == ([{"start": 1.0, "end": 2.0}] if with_refinement else [{"start": 1.0, "end": 2.0}, {"start": 4.0, "end": 5.0}])
    if invalid_gallery:
        assert diagnostics["clips"][0]["match_status"] == "invalid"
        assert not evidence["policy"]["recovery_applied"]
        return
    assert diagnostics["clips"][0]["match_status"] == "matched"
    assert diagnostics["clips"][0]["reference_images"]
    query_image = diagnostics["clips"][0]["query_images"][0]
    assert (tmp_path / query_image).read_bytes() == b"matched-face-preview"
