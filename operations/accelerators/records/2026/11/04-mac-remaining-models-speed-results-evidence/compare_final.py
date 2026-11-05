import json,hashlib
from pathlib import Path
root=Path('/private/tmp/clipper-mac-remaining-20261104')
before=json.loads((root/'baseline-mmn-result.json').read_text())
after=json.loads((root/'single-phased-mmn-result.json').read_text())
old=json.loads(Path('/private/tmp/clipper-face-speed-20261104/mmn-result.json').read_text())
report={
 'baseline_seconds':before['acceleration']['elapsed_seconds'],
 'after_seconds':after['acceleration']['elapsed_seconds'],
 'cpu_reanalysis':after['acceleration']['cpu_reanalysis'],
 'lists_equal':before['meta']['lists']==after['meta']['lists'],
 'previous_lists_equal':old['meta']['lists']==after['meta']['lists'],
 'config_equal':before['meta']['config']==after['meta']['config'],
 'stats_equal':before['meta']['stats']==after['meta']['stats'],
 'list_counts':{k:len(v) for k,v in after['meta']['lists'].items()},
 'before_performance':before['meta']['diagnostics']['performance'],
 'after_performance':after['meta']['diagnostics']['performance'],
 'after_models':after['acceleration_models'],
 'phase_selections':json.loads((root/'final-selections.json').read_text()),
}
report['reduction_percent']=(1-report['after_seconds']/report['baseline_seconds'])*100
(root/'single-phased-comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('before_performance','after_performance','after_models','phase_selections')},ensure_ascii=False,indent=2))
assert report['lists_equal'] and report['previous_lists_equal'] and report['config_equal'] and report['stats_equal']
assert not report['cpu_reanalysis']
