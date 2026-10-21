import numpy as np
from dataclasses import replace

from clipper_face_core import grouping
from clipper_face_core.grouping import FaceObservation, group_observations


def face(identifier: str, track: str, shot: str, sec: float, vector, box=(0, 0, 20, 20)):
    return FaceObservation(
        observation_id=identifier,
        track_id=track,
        shot_id=shot,
        time_sec=sec,
        bbox_px=box,
        embedding=np.asarray(vector, dtype=np.float32) if vector is not None else None,
        quality=0.8,
    )


def test_two_simultaneous_faces_never_merge_even_with_identical_embeddings():
    observations = [
        face('a1', 'a', 's0', 0.0, [1, 0]),
        face('b1', 'b', 's0', 0.0, [1, 0], (30, 0, 50, 20)),
        face('a2', 'a', 's0', 0.5, [1, 0]),
        face('b2', 'b', 's0', 0.5, [1, 0], (30, 0, 50, 20)),
    ]
    groups = group_observations(observations, cosine_threshold=0.5)
    assert len(groups) == 2
    assert {frozenset(group.track_ids) for group in groups} == {frozenset({'a'}), frozenset({'b'})}


def test_reappearance_joins_across_shots_but_unknown_is_preserved():
    observations = [
        face('a1', 'a', 's0', 0.0, [1, 0]),
        face('a2', 'a', 's0', 0.5, [1, 0]),
        face('b1', 'b', 's1', 5.0, [0.99, 0.01]),
        face('u1', 'u', 's1', 5.0, None, (30, 0, 50, 20)),
    ]
    groups = group_observations(observations, cosine_threshold=0.7)
    assert len(groups) == 2
    assert any(set(group.track_ids) == {'a', 'b'} for group in groups)
    assert any(group.status == 'needs_review' and group.track_ids == ('u',) for group in groups)


def test_same_scene_id_distinct_source_intervals_are_retained():
    observations = [
        face('a1', 'a', 's0', 1.0, [1, 0]),
        face('a2', 'a', 's0', 1.5, [1, 0]),
        face('a3', 'a', 's0', 8.0, [1, 0]),
    ]
    [group] = group_observations(observations, cosine_threshold=0.7, max_gap_sec=1.0)
    assert [(interval.shot_id, interval.start_sec, interval.end_sec) for interval in group.intervals] == [
        ('s0', 1.0, 1.5), ('s0', 8.0, 8.0),
    ]


def test_interval_phase_starts_before_intervals_are_calculated(monkeypatch):
    events = []
    calculate = grouping._intervals

    def record_calculation(observations, gap):
        events.append('calculate')
        return calculate(observations, gap)

    monkeypatch.setattr(grouping, '_intervals', record_calculation)
    grouping.group_observations(
        [face('a1', 'a', 's0', 0.0, [1, 0])],
        on_intervals_start=lambda: events.append('intervals'),
    )
    assert events == ['intervals', 'calculate']


def test_representative_prefers_sharp_face_over_slightly_higher_composite_quality():
    blurry = FaceObservation('blur', 'track', 'shot', 0.0, (0, 0, 100, 100),
                             np.array([1, 0], np.float32), 0.9, sharpness=0.1)
    sharp = FaceObservation('sharp', 'track', 'shot', 0.5, (0, 0, 100, 100),
                            np.array([1, 0], np.float32), 0.8, sharpness=0.9)

    [group] = group_observations([blurry, sharp])

    assert group.representative_observation_id == 'sharp'


def test_single_observation_is_retained_but_marked_for_review():
    [group] = group_observations([face('one', 'track', 'shot', 0.0, [1, 0])])

    assert group.status == 'needs_review'
    assert group.observation_ids == ('one',)


def test_representative_does_not_favor_noisy_tiny_face_over_larger_clear_face():
    tiny = FaceObservation('tiny', 'track', 'shot', 0.0, (0, 0, 20, 20),
                           np.array([1, 0], np.float32), 0.7, sharpness=1.0)
    large = FaceObservation('large', 'track', 'shot', 0.5, (0, 0, 100, 100),
                            np.array([1, 0], np.float32), 0.7, sharpness=0.6)

    [group] = group_observations([tiny, large])

    assert group.representative_observation_id == 'large'


def test_replacement_candidates_use_the_same_quality_order_as_primary():
    tiny = FaceObservation('tiny', 'track', 'shot', 0.0, (0, 0, 20, 20),
                           np.array([1, 0], np.float32), 0.7, sharpness=1.0)
    large = FaceObservation('large', 'track', 'shot', 0.5, (0, 0, 100, 100),
                            np.array([1, 0], np.float32), 0.7, sharpness=0.6)
    medium = FaceObservation('medium', 'track', 'shot', 1.0, (0, 0, 70, 70),
                             np.array([1, 0], np.float32), 0.7, sharpness=0.5)

    ranked = grouping.rank_representatives([tiny, large, medium])

    assert ranked == ['large', 'medium', 'tiny']
    assert group_observations([tiny, large, medium])[0].representative_observation_id == ranked[0]


def test_representative_ranking_rejects_mixed_embedding_spaces():
    first = replace(face('a', 'track', 'shot', 0.0, [1, 0]), model_sha256='model-a')
    second = replace(face('b', 'track', 'shot', 0.5, [1, 0]), model_sha256='model-b')

    with np.testing.assert_raises_regex(ValueError, 'embedding model/config spaces'):
        grouping.rank_representatives([first, second])
