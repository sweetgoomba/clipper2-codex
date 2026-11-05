"""Output deduplication must preserve the underlying group/main decisions."""
from copy import deepcopy

import pytest

from dance_highlight.services.dance_meta import DanceClipItem


def clip(kind, start, end, person=None, index=0, **kwargs):
    return DanceClipItem(index, kind, start, end, None, person,
        clip_id=f'{kind}_{index:04d}', thumbnail_path=f'{kind}_{index:04d}.jpg', **kwargs)


def project(mains, groups, *, source_ranges=True):
    from dance_highlight.services.group_output import project_group_outputs
    return project_group_outputs(mains, groups, matched_main_ids={
        item.clip_id for item in mains if item.person_id in {'a', 'b'}
    }, source_ranges=source_ranges)


@pytest.mark.parametrize('start,end', [(3., 3.4), (2., 8.), (2., 2.01)])
def test_single_named_main_contains_the_entire_group_output(start, end):
    mains = [clip('main', 2., 8., 'a')]
    groups = [clip('group', start, end, person_ids=())]
    before = deepcopy((mains, groups))
    output, audit = project(mains, groups)
    assert output == []
    assert (mains, groups) == before
    assert audit['input_group_count'] == 1 and audit['output_group_count'] == 0
    assert audit['suppressed'] == [{
        'group_clip_id': 'group_0000', 'group_start': start, 'group_end': end,
        'covering_main_clip_id': 'main_0000', 'person_id': 'a',
        'main_start': 2., 'main_end': 8.,
        'reason': 'single_named_main_contains_source_range',
    }]


@pytest.mark.parametrize('mains,groups,source_ranges', [
    ([clip('main', 3., 6., 'a')], [clip('group', 2.99, 5.)], True),
    ([clip('main', 3., 6., 'a')], [clip('group', 4., 6.01)], True),
    ([clip('main', 3., 4.5, 'a'), clip('main', 4.5, 6., 'a', 1)], [clip('group', 3., 6.)], True),
    ([clip('main', 3., 6., 'unknown')], [clip('group', 3., 6.)], True),
    ([clip('main', 3., 6., 'person_1')], [clip('group', 3., 6.)], True),
    ([clip('main', 3., 6., 'a'), clip('main', 5.9, 8., 'b', 1)], [clip('group', 3., 6.)], True),
    ([clip('main', 3., 6., 'a')], [clip('group', 3., 6., person_ids=('a',))], True),
    ([clip('main', 3., 6., 'a')], [clip('group', 3., 6., 'a')], True),
    ([clip('main', 3., 6., 'a')], [clip('group', 3., 6.)], False),
    ([clip('main', 3., 6., 'a')], [clip('group', 4., 4.)], True),
    ([clip('main', 3., 6., 'a')], [clip('group', float('nan'), 4.)], True),
    ([clip('main', 3., float('inf'), 'a')], [clip('group', 3., 6.)], True),
])
def test_preserve_nonredundant_or_ambiguous_outputs(mains, groups, source_ranges):
    output, audit = project(mains, groups, source_ranges=source_ranges)
    assert output == groups
    assert audit['suppressed'] == []


def test_registered_name_is_not_sufficient_without_a_matched_decision():
    from dance_highlight.services.group_output import project_group_outputs
    group = clip('group', 3., 6.)
    output, audit = project_group_outputs([clip('main', 2., 8., 'a')], [group],
        matched_main_ids=set(), source_ranges=True)
    assert output == [group] and not audit['suppressed']


def test_preserved_clip_ids_and_thumbnails_are_not_renumbered():
    groups = [clip('group', 3., 4., index=0), clip('group', 8., 9., index=1)]
    output, audit = project([clip('main', 2., 6., 'a')], groups)
    assert output == [groups[1]] and output[0] is groups[1]
    assert output[0].clip_id == 'group_0001'
    assert output[0].thumbnail_path == 'group_0001.jpg'


def test_boundary_touching_other_member_does_not_overlap():
    groups = [clip('group', 3., 6.)]
    output, _ = project([clip('main', 2., 6., 'a'), clip('main', 6., 8., 'b', 1)], groups)
    assert not output
