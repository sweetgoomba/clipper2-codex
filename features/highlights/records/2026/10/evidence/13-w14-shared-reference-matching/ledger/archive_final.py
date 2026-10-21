from pathlib import Path
import hashlib
import json
import shutil
import subprocess

repo = Path.cwd()
base = Path('/Users/jina/project/adlight')
ledger = repo / '.superpowers/sdd/2026-10-13-shared-reference-face-matching'
destination = base / '.codex/features/highlights/records/2026/10/evidence/13-w14-shared-reference-matching'
destination.mkdir(parents=True, exist_ok=False)
entries = []

def save(source, relative):
    target = destination / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    data = target.read_bytes()
    entries.append(dict(path=relative, original_path=str(source),
                        sha256=hashlib.sha256(data).hexdigest(), bytes=len(data)))

files = ['pyproject.toml', 'uv.lock']
files += subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard',
                                  '--', 'clipper_face_core', 'evaluation'], text=True).splitlines()
for relative in sorted(set(files)):
    save(repo / relative, 'code/' + relative)
for file in sorted(ledger.iterdir()):
    if file.is_file() and file.suffix in ('.md', '.log', '.py', '.patch'):
        save(file, 'ledger/' + file.name)
output = repo.parents[1] / 'evaluation-output'
for version in ['reference-replay-v1', 'reference-replay-v2']:
    for relative in ['manifest.json', 'supervisor.json', 'stdout.log', 'stderr.log', 'result/report.json']:
        save(output / version / relative, 'replay/' + version + '/' + relative)
for relative in ['docs/superpowers/plans/2026-10-13-shared-reference-face-matching.md',
                 'docs/superpowers/specs/2026-10-13-shared-reference-face-matching-design.md',
                 '.codex/features/highlights/records/2026/10/13-w14-shared-reference-matching-implementation.md']:
    save(base / relative, 'documents/' + Path(relative).name)
manifest = dict(schema='w14_reference_matching_implementation_archive_v1', date='2026-10-13',
                repo=str(repo), branch=subprocess.check_output(['git','branch','--show-current'],text=True).strip(),
                head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
                uncommitted=True, entries=entries)
(destination / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
for entry in entries:
    assert hashlib.sha256((destination / entry['path']).read_bytes()).hexdigest() == entry['sha256']
print(json.dumps({'files': len(entries), 'bytes': sum(x['bytes'] for x in entries),
                  'manifest': str(destination / 'manifest.json')}))
