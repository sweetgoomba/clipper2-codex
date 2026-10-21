import json,os,subprocess,sys,time
from pathlib import Path
root=Path('/Users/jina/project/adlight/.worktrees/shared-reference-face-matching-20261013/evaluation-output/reference-replay-v2')
plan=json.loads((root/'manifest.json').read_text());limits=plan['limits']
subprocess.run(['ps','-o','rss=','-p',str(os.getpid())],capture_output=True,text=True,check=True)
started=time.monotonic();peak=0;stop=None
with (root/'stdout.log').open('w') as out,(root/'stderr.log').open('w') as err:
 proc=subprocess.Popen([sys.executable,'-m','evaluation.reference_matching.replay','--manifest',str(root/'manifest.json'),'--output-dir',str(root/'result')],stdout=out,stderr=err)
 try:
  while proc.poll() is None:
   rss=subprocess.run(['ps','-o','rss=','-p',str(proc.pid)],capture_output=True,text=True)
   if rss.stdout.strip():peak=max(peak,int(rss.stdout.strip())*1024)
   output=sum(p.stat().st_size for p in root.rglob('*') if p.is_file())
   if time.monotonic()-started>limits['wall_seconds']:stop='wall'
   if peak>limits['rss_bytes']:stop='rss'
   if output>limits['output_bytes']:stop='output'
   if stop:proc.kill();break
   time.sleep(.025)
  code=proc.wait()
 finally:
  if proc.poll() is None:proc.kill();proc.wait()
result=dict(exit_code=code,stopped_by_limit=stop,wall_seconds=time.monotonic()-started,peak_sampled_rss_bytes=peak,
            output_bytes=sum(p.stat().st_size for p in root.rglob('*') if p.is_file()))
(root/'supervisor.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result))
if code:print((root/'stderr.log').read_text());sys.exit(code)
if stop:sys.exit(1)
