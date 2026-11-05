import json,pathlib,hashlib,zipfile,stat,struct,datetime
R=pathlib.Path('/Users/jina/project/adlight/.worktrees'); P=R/'clipper-python-accelerators-20261103'; E=R/'clipper-electron-accelerators-20261103'; H=P/'.implementation-evidence/completion/handoff'; O=pathlib.Path('/private/tmp/clipper-reaudit-20261103/delivery')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
m=json.loads((H/'source-manifest.json').read_text());out={'run_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_files':len(m['files'])};bad=[]
for f in m['files']:
 rel=pathlib.PurePosixPath(f['path']);repo=rel.parts[1];path=pathlib.Path(m['repositories'][repo]['source_worktree']).joinpath(*rel.parts[2:]);got=sha(path) if path.is_file() else None
 if got!=f['sha256']:bad.append({'path':str(path),'actual':got,'expected':f['sha256']})
out['source_current_mismatches']=bad;z=zipfile.ZipFile(H/'clipper-acceleration-source.zip');bad=[]
for f in m['files']:
 try:got=hashlib.sha256(z.read(f['path'])).hexdigest()
 except KeyError:got=None
 if got!=f['sha256']:bad.append({'path':f['path'],'actual':got,'expected':f['sha256']})
out['source_zip_mismatches']=bad;out['source_zip_symlinks']=[i.filename for i in z.infolist() if stat.S_ISLNK(i.external_attr>>16)];out['source_sha_actual']=sha(H/'clipper-acceleration-source.zip');out['source_sha_recorded']=json.loads((H/'sha256.json').read_text());out['source_current_recorded']=json.loads((H/'source-current-check.json').read_text())
a=zipfile.ZipFile(E/'dist-app/Clipper Studio (dev)-0.0.1-arm64.zip');pref='Clipper Studio (dev).app/Contents/Resources/';out['packaged']={}
for name,root in [('clipper_python',P),('clipper_nestjs',R/'clipper-nestjs-accelerators-20261103/dist/bundled'),('renderer',R/'clipper-angular-accelerators-20261103/dist/clipper_angular/browser')]:
 count=0;bad=[]
 for n in a.namelist():
  if n.startswith(pref+name+'/') and not n.endswith('/'):
   rel=n[len(pref+name+'/'):];src=root/rel
   if name=='clipper_nestjs' and rel=='.env.packaged':src=R/'clipper-nestjs-accelerators-20261103/.env.packaged'
   count+=1
   if not src.is_file() or a.read(n)!=src.read_bytes():bad.append(rel)
 out['packaged'][name]={'checked':count,'mismatches':bad}
asar=a.read(pref+'app.asar');hs=struct.unpack_from('<I',asar,12)[0];header=json.loads(asar[16:16+hs]);off=8+struct.unpack_from('<I',asar,4)[0]
def walk(t,p=''):
 for n,f in t['files'].items():
  q=p+'/'+n if p else n
  if 'files' in f:yield from walk(f,q)
  else:yield q,f
files=dict(walk(header));bad=[];count=0
for n,f in files.items():
 if n.startswith('dist-electron/'):
  src=E/n;count+=1;begin=off+int(f.get('offset',0))
  if not src.is_file() or asar[begin:begin+f['size']]!=src.read_bytes():bad.append(n)
out['packaged']['electron_dist']={'checked':count,'mismatches':bad};out['asar_symlinks']=[n for n,f in files.items() if 'link' in f];out['dependency_packages']={n:'node_modules/'+n+'/package.json' in files for n in ['electron-log','electron-updater','builder-util-runtime','graceful-fs','js-yaml','lazy-val','lodash.escaperegexp','lodash.isequal','semver']}
out['mac_artifacts_recorded']=json.loads((P/'.implementation-evidence/completion/mac-artifacts.json').read_text());out['artifacts_actual']=[]
for n in ['Clipper Studio (dev)-0.0.1-arm64.zip','Clipper Studio (dev)-0.0.1-arm64.dmg']:
 f=E/'dist-app'/n;out['artifacts_actual'].append({'path':str(f),'bytes':f.stat().st_size,'sha256':sha(f)})
for n in ['current-work-merge/manifest.json','current-work-merge/new-user-files-sha.json']:
 rows=json.loads((P/'.implementation-evidence/completion'/n).read_text());bad=[]
 for x in rows:
  repo=x.get('repo','clipper_python');base=R/(repo.replace('_','-',1)+'-accelerators-20261103');path=base/x['path'];expected=x.get('merged_sha256') or x.get('sha256');actual=sha(path) if path.is_file() else None
  if actual!=expected:bad.append({'path':str(path),'actual':actual,'expected':expected})
 out[n]={'checked':len(rows),'mismatches':bad}
(O/'delivery-check.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out,ensure_ascii=False,indent=2))
