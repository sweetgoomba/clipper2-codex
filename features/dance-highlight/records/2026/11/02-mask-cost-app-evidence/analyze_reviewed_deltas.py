"""Separate reviewed-window classification changes from enclosing clip bounds."""
import json
import sys
from pathlib import Path

root = Path(__file__).parent / sys.argv[1]
results = []
for case in json.loads((root/'reviewed-case-comparison.json').read_text()):
    before, after = case['before'], case['after']
    edges = sorted({case['start'], case['end']} |
                   {row[key] for row in before + after for key in ('start', 'end')})
    differences = []
    for start, end in zip(edges, edges[1:]):
        t = (start + end) / 2
        def labels(rows):
            return sorted({(row['kind'], row['name'] or '') for row in rows
                           if row['start'] <= t < row['end']})
        left, right = labels(before), labels(after)
        if left != right:
            differences.append(dict(start=start, end=end, before=left, after=right))
    results.append(dict(title=case['title'], start=case['start'], end=case['end'],
                        user_feedback=case['user_feedback'],
                        identical_clip_rows=case['identical'],
                        classification_changed_seconds=sum(d['end']-d['start'] for d in differences),
                        differences=differences))
(root/'reviewed-case-analysis.json').write_text(json.dumps(results, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(dict(cases=len(results), classification_changed=[r for r in results if r['differences']],
                     boundary_only=[{k:r[k] for k in ('title','start','end')} for r in results
                                    if not r['differences'] and not r['identical_clip_rows']]), ensure_ascii=False))
