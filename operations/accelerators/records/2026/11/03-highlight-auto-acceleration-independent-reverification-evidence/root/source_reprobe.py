import sys,hashlib,json
from pathlib import Path
sys.path.insert(0,'/Users/jina/project/adlight/.worktrees/clipper-python-accelerators-20261103/clipper_accelerators')
from clipper_accelerators.immutable_source import preserve_source,resolve_source
root=Path('/private/tmp/clipper-reaudit-20261103/root/source');root.mkdir(parents=True,exist_ok=True)
source=root/'사용자 입력.mp4';original=b'original fixture bytes'*100;source.write_bytes(original);digest=hashlib.sha256(original).hexdigest()
refs=[preserve_source(root/'프로젝트 결과',source,digest) for _ in range(3)]
assert all(r==refs[0] for r in refs)
preserved=resolve_source(refs[0]);assert preserved.read_bytes()==original
assert preserved.stat().st_ino!=source.stat().st_ino
source.write_bytes(b'changed original user file')
assert resolve_source(refs[0]).read_bytes()==original
files=list((root/'프로젝트 결과/.acceleration/sources').rglob('original*'))
result={'repeated_preservations':3,'source_assets':len(files),'same_reference':all(r==refs[0] for r in refs),'independent_inode':preserved.stat().st_ino!=source.stat().st_ino,'preserved_bytes_survive_external_mutation':True,'scope':'tiny byte fixture, no media decode or app'}
assert len(files)==1
(root/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False))
