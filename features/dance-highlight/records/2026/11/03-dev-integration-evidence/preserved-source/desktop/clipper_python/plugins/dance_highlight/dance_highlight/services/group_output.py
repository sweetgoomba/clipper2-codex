"""Project automatic source-range outputs without changing scene judgments.

The pipeline supplies clips from one source, all displayed/exported without a
person crop. A group entirely contained in one confirmed named main would replay
the same source frames. Keep its evidence, but omit that redundant output card.
This is an output policy, never identity or main/group classification evidence.
"""
from __future__ import annotations

import math
from typing import AbstractSet, Any, Sequence

from .dance_meta import DanceClipItem


def _valid_range(item: DanceClipItem) -> bool:
    return (math.isfinite(item.start) and math.isfinite(item.end)
            and 0 <= item.start < item.end)


def project_group_outputs(
    main_items: Sequence[DanceClipItem],
    group_items: Sequence[DanceClipItem],
    *,
    matched_main_ids: AbstractSet[str],
    source_ranges: bool,
) -> tuple[list[DanceClipItem], dict[str, Any]]:
    """Return original item objects; preserve all input lists and identifiers.

    No gap tolerance or union of multiple mains is allowed. Exact source-time
    containment also guarantees containment under identical export rounding.
    Caller must restrict this to newly generated automatic source-range results.
    """
    named = [item for item in main_items
             if item.seg_type == 'main' and item.clip_id in matched_main_ids
             and item.person_id and item.person_id != 'unknown' and _valid_range(item)]
    kept: list[DanceClipItem] = []
    suppressed: list[dict[str, Any]] = []
    for group in group_items:
        covers = []
        if (source_ranges and group.seg_type == 'group' and group.clip_id
                and not group.person_id and not group.person_ids and _valid_range(group)):
            covers = [main for main in named
                      if main.start <= group.start and group.end <= main.end]
        if len(covers) != 1:
            kept.append(group)
            continue
        main = covers[0]
        if any(other.person_id != main.person_id
               and other.start < group.end and group.start < other.end
               for other in named):
            kept.append(group)
            continue
        suppressed.append({
            'group_clip_id': group.clip_id,
            'group_start': group.start, 'group_end': group.end,
            'covering_main_clip_id': main.clip_id, 'person_id': main.person_id,
            'main_start': main.start, 'main_end': main.end,
            'reason': 'single_named_main_contains_source_range',
        })
    return kept, {
        'version': 'contained_group_output_v1',
        'classification_changed': False,
        'input_group_count': len(group_items), 'output_group_count': len(kept),
        'suppressed': suppressed,
    }
