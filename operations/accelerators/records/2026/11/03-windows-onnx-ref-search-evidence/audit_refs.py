import concurrent.futures
import datetime
import json
from pathlib import Path
import re
import subprocess

ROOT = Path('/Users/jina/project/adlight')
OUT = Path('/private/tmp/clipper-gpu-ref-audit-20261103')
OUT.mkdir(exist_ok=True)
REPOS = ['desktop/clipper_electron', 'desktop/clipper_angular', 'desktop/clipper_nestjs',
         'web/clipper_web_client', 'web/clipper_web_admin', 'web/clipper_web_api',
         'web/clipper_infra', 'desktop/clipper_python', 'clipper_docs']
TEXT_PATTERN = r'clipper[-_ ]gpu[-_ ]kit|run[-_]kit[.]py|directml20261103[-_]053501|Clipper GPU 시험|DmlExecutionProvider:0|auto:PREFER_GPU|same_people_dance|same_people_person|matched_box_iou_min|MLOperatorAuthorImpl|Init provider bridge failed'
PATH_PATTERN = re.compile(r'run[-_]?kit|clipper[-_]gpu[-_]kit|directml|windows[-_ ]?ml|gpu.*(kit|bench)|onnx.*(bench|kit|trial|export)|bench.*(gpu|onnx)', re.I)

def audit(repo):
    directory = OUT / repo.replace('/', '__')
    directory.mkdir(exist_ok=True)
    commands = []
    errors = []
    def git(label, args, allowed=(0,)):
        proc = subprocess.run(['git', *args], cwd=ROOT/repo, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout = proc.stdout.decode('utf-8', errors='backslashreplace')
        stderr = proc.stderr.decode('utf-8', errors='backslashreplace')
        (directory/(label+'.stdout.txt')).write_text(stdout)
        (directory/(label+'.stderr.txt')).write_text(stderr)
        row = {'label':label, 'argv':['git',*args], 'exit_code':proc.returncode,
               'stdout_bytes':len(proc.stdout), 'stderr_bytes':len(proc.stderr)}
        commands.append(row)
        if proc.returncode not in allowed:
            errors.append({**row, 'stderr':stderr})
        return proc.returncode, stdout, stderr

    _, head, _ = git('head', ['rev-parse','HEAD'])
    _, status_before, _ = git('status-before', ['status','--porcelain=v1','--untracked-files=no'])
    _, refs_text, _ = git('refs', ['for-each-ref','--format=%(refname)\t%(objectname)\t%(objecttype)\t%(*objectname)\t%(*objecttype)'])
    refs = []
    commits = {}
    for line in refs_text.splitlines():
        name, oid, kind, peeled, peeled_kind = line.split('\t')
        sha = oid if kind == 'commit' else (peeled if peeled_kind == 'commit' else None)
        row = {'ref':name, 'object_sha':oid, 'object_type':kind, 'commit_sha':sha}
        refs.append(row)
        if sha:
            commits.setdefault(sha, []).append(name)
        else:
            errors.append({'unsearchable_ref':row})
    matches = []
    path_matches = []
    for i, (sha, names) in enumerate(commits.items()):
        code, output, _ = git('tip-'+sha+'-strings', ['grep','-n','-I','-i','-E',TEXT_PATTERN,sha,'--'], allowed=(0,1))
        if code == 0:
            matches.append({'commit_sha':sha, 'refs':names, 'lines':output.splitlines()})
        _, paths, _ = git('tip-'+sha+'-paths',['ls-tree','-r','--name-only',sha])
        hits = [path for path in paths.splitlines() if PATH_PATTERN.search(path)]
        if hits:
            path_matches.append({'commit_sha':sha,'refs':names,'paths':hits})
    _, objects, _ = git('reachable-objects',['rev-list','--objects','--all'])
    object_hits = [line for line in objects.splitlines() if PATH_PATTERN.search(line)]
    _, history_paths, _ = git('history-paths',['log','--all','--format=','--name-only'])
    history_hits = sorted({line for line in history_paths.splitlines() if PATH_PATTERN.search(line)})
    _, pickaxe, _ = git('history-strings',['log','--all','--format=%H %s','-G'+TEXT_PATTERN,'--'])
    _, status_after, _ = git('status-after', ['status','--porcelain=v1','--untracked-files=no'])
    result = {'repo':repo, 'head_sha':head.strip(), 'refs':refs, 'ref_count':len(refs),
              'unique_tip_commits':len(commits), 'tip_text_matches':matches, 'tip_path_matches':path_matches,
              'reachable_object_path_matches':object_hits, 'history_path_matches':history_hits,
              'history_string_change_commits':pickaxe.splitlines(), 'errors':errors,
              'tracked_status_before_after_same':status_before==status_after, 'commands':commands}
    (directory/'summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result

with concurrent.futures.ThreadPoolExecutor(max_workers=9) as pool:
    results=list(pool.map(audit,REPOS))
payload={'recorded_at_kst':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(),
         'text_pattern':TEXT_PATTERN,'path_pattern':PATH_PATTERN.pattern,'repos':results}
(OUT/'audit.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
for r in results:
    print(json.dumps({k:r[k] for k in ['repo','head_sha','ref_count','unique_tip_commits','tip_text_matches','tip_path_matches','history_path_matches','history_string_change_commits','errors','tracked_status_before_after_same']},ensure_ascii=False))
