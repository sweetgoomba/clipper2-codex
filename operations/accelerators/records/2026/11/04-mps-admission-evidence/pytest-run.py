import os,sys,tomllib
from pathlib import Path
root=Path(os.environ.get('CLIPPER_MPS_TEST_ROOT','/Users/jina/project/adlight/.worktrees/mps-admission-20261104/clipper_python'))
paths=[str(root)]+[str(root/p) for p in tomllib.loads((root/'pyproject.toml').read_text())['tool']['uv']['workspace']['members']]
sys.path[:0]=paths;os.environ['PYTHONPATH']=os.pathsep.join(paths+[os.environ.get('PYTHONPATH','')])
os.chdir(root)
if __name__=='__main__':
 os.execv(sys.executable,[sys.executable,'-m','pytest',*sys.argv[1:]])
