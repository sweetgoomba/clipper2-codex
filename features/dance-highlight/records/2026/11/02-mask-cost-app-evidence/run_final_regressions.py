"""Run the dance pipeline and isolated Person regressions before packaging."""
import subprocess
from pathlib import Path

repo = Path('/Users/jina/project/adlight/desktop/clipper_python')
tests = sorted(str(p.relative_to(repo)) for p in (repo/'tests').glob('test_dance_*.py'))
tests += ['plugins/person_highlight/tests']
log = Path(__file__).with_name('disabled-dance-person-regressions.log')
with log.open('w') as output:
    print('Command: .venv/bin/python -m pytest -q ' + ' '.join(tests), file=output, flush=True)
    result = subprocess.run([str(repo/'.venv/bin/python'), '-m', 'pytest', '-q', *tests],
                            cwd=repo, stdout=output, stderr=subprocess.STDOUT)
print(log.read_text())
raise SystemExit(result.returncode)
