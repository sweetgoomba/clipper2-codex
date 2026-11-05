import subprocess,json,concurrent.futures
from pathlib import Path
ROOT=Path('/Users/jina/project/adlight')
OUT=Path('/private/tmp/clipper-gpu-ref-audit-20261103')
REPOS=['desktop/clipper_electron','desktop/clipper_angular','desktop/clipper_nestjs','web/clipper_web_client','web/clipper_web_admin','web/clipper_web_api','web/clipper_infra','desktop/clipper_python','clipper_docs']
PATTERN=r'onnxruntime-directml|onnxruntime-windowsml|windows[ _-]?ml|DmlExecutionProvider|PREFER_GPU|clip_visual|same_people_dance|same_people_person'
def scan(repo):
    d=OUT/repo.replace('/','__')
    rows=(d/'refs.stdout.txt').read_text().splitlines()
    refs={}
    for row in rows:
        name,oid,kind,peeled,pkind=row.split('\t')
        sha=oid if kind=='commit' else (peeled if pkind=='commit' else None)
        if sha: refs.setdefault(sha,[]).append(name)
    args=['git','grep','-n','-I','-i','-E',PATTERN,*refs,'--']
    p=subprocess.run(args,cwd=ROOT/repo,capture_output=True,text=True)
    (d/'broad-tip-strings.stdout.txt').write_text(p.stdout)
    (d/'broad-tip-strings.stderr.txt').write_text(p.stderr)
    result={'repo':repo,'argv':args,'exit_code':p.returncode,'stderr':p.stderr,'matches':p.stdout.splitlines()}
    (d/'broad-tip-strings.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    results=list(pool.map(scan,REPOS))
(OUT/'broad-audit.json').write_text(json.dumps({'pattern':PATTERN,'results':results},ensure_ascii=False,indent=2)+'\n')
for r in results: print(json.dumps({'repo':r['repo'],'exit_code':r['exit_code'],'stderr':r['stderr'],'matches':r['matches']},ensure_ascii=False))
