from pathlib import Path
from collections import Counter
import json,hashlib,copy
P=Path(__file__).parent;APP=Path('/Users/jina/Library/Application Support/Clipper Studio Dev');ROOT=APP/'projects/files/116957ce-bd03-4d4a-a21d-984dc12487aa';REPO=Path('/Users/jina/project/adlight/desktop/clipper_python');TASK=Path('/private/tmp/dance-continuity-next-20261103')
runs=json.loads((TASK/'app/run-manifest.json').read_text());manifest=json.loads((TASK/'final-source-manifest.json').read_text());before_manifest=json.loads((TASK/'before-manifest.json').read_text());images=json.loads((P/'member-app-images-audit.json').read_text());query_proof=json.loads((P/'neon-query-original-source-proof.json').read_text());checks=[];videos={};metas={}
def read(p):return json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def check(n,v):checks.append(dict(name=n,passed=bool(v)))
def normalize(rows):return [{k:v for k,v in row.items() if k not in ('seg_id','clip_id','thumbnail_path')} for row in rows]
def merge(rows,start,end,name):
 selected=[i for i,r in enumerate(rows) if start-1e-8<=r['start'] and r['end']<=end+1e-8]
 assert selected and selected==list(range(selected[0],selected[-1]+1)) and abs(rows[selected[0]]['start']-start)<1e-8 and abs(rows[selected[-1]]['end']-end)<1e-8
 return rows[:selected[0]]+[dict(rows[selected[0]],end=end,person_id=name)]+rows[selected[-1]+1:]
def strip_source_index(v):
 if isinstance(v,dict):return {k:strip_source_index(x) for k,x in v.items() if k not in ('source_index','elapsed_seconds')}
 if isinstance(v,list):return [strip_source_index(x) for x in v]
 return v
protected={'ANT':[(82.182,82.6826),(180.8806,182.6826)],'NEON':[(93.05953333333333,94.92816666666667),(115.6155,115.9158)]}
for run in runs:
 label=run['title'];v=read(P/f'final-app-{label}-audit.json')['videos'][label];ids=v['ids'];old,new=[read(ROOT/pid/'json/dance_meta.json') for pid in ids];a,b=[read(ROOT/pid/'diagnostics/face_evidence.json') for pid in ids];metas[label]=[old,new]
 predicted=copy.deepcopy(old['lists'])
 if label=='MMN':predicted['main']=merge(predicted['main'],104.02058333333333,106.70660000000001,'허윤진')
 if label=='ANT':predicted['main']=merge(predicted['main'],62.5625,69.20246666666667,'김채원')
 if label=='NEON':
  predicted['main']=merge(predicted['main'],98.23146666666666,99.96653333333333,'오아');predicted['group']=[r for r in predicted['group'] if not(abs(r['start']-98.2982)<1e-8 and abs(r['end']-98.53176666666667)<1e-8)]
 check(label+' exact approved output transformation',all(normalize(predicted[k])==normalize(new['lists'][k]) for k in ('main','group')))
 check(label+' all outputs completed without error',all(t['job_status']==t['project_status']=='completed' and t['error'] is None and t['job_finished_matches_project'] for t in v['timings']))
 prior=read(Path('/private/tmp/dance-member-part-review-20261102')/f'final-app-{label}-audit.json')['videos'][label]
 check(label+' 414 baseline metadata and evidence unchanged',prior['ids'][1]==ids[0] and v['metadata_hashes'][0]==prior['metadata_hashes'][1])
 check(label+' metadata and evidence audit hashes current',all(sha(ROOT/pid/rel)==v['metadata_hashes'][i][key] for i,pid in enumerate(ids) for key,rel in [('meta','json/dance_meta.json'),('evidence','diagnostics/face_evidence.json')]))
 check(label+' config/setup/source metadata equal',v['same_config'] and v['same_dance_setup'] and all(v['input_metadata_equal'].values()))
 check(label+' source video bytes match both recorded input hashes',images[label]['source_hashes_match'])
 jobs=[read(APP/'jobs/items'/f'dance_{pid}.json')['job'] for pid in ids]
 check(label+' job reference selections and requested source identical',jobs[0]['params']['dance_setup']==jobs[1]['params']['dance_setup'] and jobs[0]['params']['source']==jobs[1]['params']['source'])
 photo_hashes={m['memberName']:{sha(Path(p)) for p in m['validatedImagePaths']} for m in jobs[1]['params']['dance_setup']['members']}
 check(label+' current original reference files match recorded recognition gallery',all(ref['image_sha256'] in photo_hashes[ref['reference_id']] for ref in b['references']))
 check(label+' raw face observations/embeddings/identity/references identical',all(a[k]==b[k] for k in ('segments','identity_refinement','references','body_continuity_refinement','visible_member_refinement')))
 check(label+' original role/cut/handoff/camera inventory identical',{k:x for k,x in a['main_selection_refinement'].items() if k!='preparation_context'}=={k:x for k,x in b['main_selection_refinement'].items() if k!='preparation_context'})
 check(label+' native observations unchanged',a['native_scene_refinement']==b['native_scene_refinement'])
 expected_frames={'MMN':{6268,6272,6276,6280,6284},'ANT':set(),'NEON':{5892,5896,5900,5904}}[label]
 check(label+' original pose geometry and ownership unchanged',len(a['pose_heads'])==len(b['pose_heads']) and all({k:v for k,v in x.items() if k not in ('scene_kind','scene_reason')}=={k:v for k,v in y.items() if k not in ('scene_kind','scene_reason')} for x,y in zip(a['pose_heads'],b['pose_heads'])))
 changed_pose={round(x['time_seconds']*new['stats']['fps']) for x,y in zip(a['pose_heads'],b['pose_heads']) if x!=y}
 check(label+' pose scene labels change only at approved frames',changed_pose==expected_frames)
 # NEON resolves one deferred source cut during approved foreground-context evaluation.
 secondary_a,secondary_b=copy.deepcopy(a['secondary_reference_refinement']),copy.deepcopy(b['secondary_reference_refinement']);mask_a,mask_b=copy.deepcopy(a['mask_continuity_refinement']),copy.deepcopy(b['mask_continuity_refinement']);extra_transition=[]
 for oldside,newside in [(secondary_a['source_transitions'],secondary_b['source_transitions']),(mask_a.get('context_faces',{}),mask_b.get('context_faces',{}))]:
  left,right=oldside.get('camera_transitions',[]),newside.get('camera_transitions',[])
  assert len(left)==len(right)
  for i,(x,y) in enumerate(zip(left,right)):
   if x!=y:
    extra_transition.append(y['frame']);check(label+' deferred5906 remains a hard source cut',label=='NEON' and y['frame']==5906 and x.get('structure_deferred') is True and x['cut'] is True and y['cut'] is True and {k:z for k,z in x.items() if k!='structure_deferred'}=={k:z for k,z in y.items() if k not in ('structure','spatial')});right[i]=copy.deepcopy(x)
 check(label+' original secondary identity and mask records otherwise identical',secondary_a==secondary_b and mask_a==mask_b)
 prep_a=a['main_selection_refinement'].get('preparation_context',{});prep_b=b['main_selection_refinement'].get('preparation_context',{})
 check(label+' accepted preparation changes unchanged except output indices',strip_source_index(prep_a.get('accepted',[]))==strip_source_index(prep_b.get('accepted',[])))
 check(label+' no output name/coverage change outside approved times',not any(v['outside_expected_coverage_changes'].values()))
 check(label+' four protected source episodes preserved',all(not(d['start']<hi and lo<d['end']) for lo,hi in protected.get(label,[]) for changes in v['coverage_changes'].values() for d in changes))
 check(label+' all prior user windows preserved',all(c['clipped_coverage_equal'] for c in v['reviewed_cases']))
 check(label+' no new tiny fragments',not any(v['tiny_new_or_changed_clips'].values()))
 check(label+' clip diagnostics and person links consistent',v['clip_diagnostics_aligned'] and v['person_links_valid'])
 descriptors=lambda m:{p['person_id']:{k:v for k,v in p.items() if k not in ('clip_ids','num_clips')} for p in m['persons']}
 check(label+' person names/descriptors unchanged',descriptors(old)==descriptors(new))
 check(label+' SAM OFF policies/runtime/candidates/recovery/models',all(s['mask_policy']==s['joint_policy']=='disabled_runtime_cost_v1' and s['mask_reason']=='disabled_runtime_cost' and all(s[k]==0 for k in ('mask_seconds','joint_seconds','mask_candidates','mask_recovered_seconds','joint_corrected_seconds','joint_recovered_seconds')) and not any('sam' in n.lower() for n in s['models']) for s in v['sam']))
 check(label+' all final thumbnails exact original same-start bytes',images[label]['all_final_thumbnails_match_original_same_start'])
 check(label+' unchanged diagnostic face-query sequences exact',images[label]['all_unchanged_query_sequences_match'])
 check(label+' changed face-query bytes traced to original owners',images[label]['all_changed_query_bytes_from_original_owners'] or label=='NEON' and query_proof['all_exact_source_bytes'] and query_proof['newly_displayed_original_frames']==[5892,5896,5900,5904])
 check(label+' other image assets unchanged',images[label]['other_images_identical'])
 modules=b['runtime']['modules'];dance={name:d for name,d in modules.items() if name!='auraface'};wanted={Path(p).stem:h for p,h in manifest.items() if p.startswith('plugins/dance_highlight/dance_highlight/')}
 check(label+' all41 Dance runtime modules match reviewed source',len(dance)==41 and all(d['sha256']==wanted.get(name) for name,d in dance.items()))
 check(label+' all42 runtime module file bytes match recorded hashes',len(modules)==42 and all(sha(d['path'])==d['sha256'] for d in modules.values()))
 check(label+' shared AuraFace unchanged',a['runtime']['modules']['auraface']['sha256']==modules['auraface']['sha256'])
 check(label+' model files/runtime config/recognition providers unchanged',all(a['runtime'][k]==b['runtime'][k] for k in ('models','config_sha256','opencv','onnxruntime','recognizer_providers')))
 installed=Path(modules['pipeline']['path']).parents[1];code={p:h for p,h in manifest.items() if p.startswith('plugins/dance_highlight/dance_highlight/') and p.endswith('.py')}
 check(label+' all58 installed Dance Python files equal freeze',len(code)==58 and all(sha(installed/p.split('plugins/dance_highlight/dance_highlight/',1)[1])==h for p,h in code.items()))
 shot=b['output_named_continuity']['shot_member_gaps'];budget=shot['source_budget'];check(label+' actual shot stage recovery and bounded source work',abs(shot['recovered_seconds']-(.46733333333334315 if label=='ANT' else 0))<1e-8 and budget['paths_used']<=(1 if label=='ANT' else 0) and budget['frames_read']==(49 if label=='ANT' else 0))
 check(label+' shot timing correctly nested', 'shot_member_gaps' in new['diagnostics']['performance']['nested_stages']['cluster_map'])
 stages=v['performance_stages'];deltas={k:stages[1].get(k,0)-stages[0].get(k,0) for k in stages[0].keys()|stages[1].keys()};walls=[t['active_wall_seconds'] for t in v['timings']]
 videos[label]=dict(ids=ids,metrics=v['metrics'],coverage_changes=v['coverage_changes'],clip_changes=v['clip_changes'],active_wall_seconds=walls,wall_change_seconds=walls[1]-walls[0],wall_change_percent=(walls[1]/walls[0]-1)*100,pipeline_seconds=[t['pipeline_seconds'] for t in v['timings']],stage_seconds=stages,stage_delta_seconds=deltas,shot_source_budget=budget,shot_seconds=stages[1]['shot_member_gaps'],thumbnails_checked=len(images[label]['thumbnails']),original_pose_count=len(b['pose_heads']),raw_recognition_and_geometry_preserved=True,deferred_structure_frames=sorted(set(extra_transition)),preparation_accepted_counts=[len(prep_a.get('accepted',[])),len(prep_b.get('accepted',[]))])
 print(label,'checked',len(checks),'failures',[c['name'] for c in checks if not c['passed']],flush=True)
check('all181 reviewed source/test files still match final freeze',all(sha(REPO/p)==h for p,h in manifest.items()))
check('Person31 and SDK25 files unchanged from start',all(before_manifest.get(p)==h for p,h in manifest.items() if 'person_highlight/' in p or 'clipper_plugin_sdk/' in p))
check('all14 user windows included',sum(len(read(P/f'final-app-{label}-audit.json')['videos'][label]['reviewed_cases']) for label in videos)==14)
totals={k:[sum(v['metrics'][i][k] for v in videos.values()) for i in (0,1)] for k in ('total','main','group','subsecond','under_0_1s','unknown_seconds','main_seconds')};wall=[sum(v['active_wall_seconds'][i] for v in videos.values()) for i in (0,1)]
check('expected409 outputs and226 subsecond',totals['total']==[414,409] and totals['subsecond']==[230,226])
check('unknown drops only approved ANT0.467333sec',abs(totals['unknown_seconds'][0]-totals['unknown_seconds'][1]-.46733333333334315)<1e-8)
short={cat:[sum(sum(r['end']-r['start']<1-1e-8 for r in m[i]['lists'][kind] if kind=='group' or (r['person_id']=='unknown')==(cat=='unknown')) for m in metas.values()) for i in (0,1)] for cat,kind in [('named','main'),('unknown','main'),('group','group')]}
report=dict(scope='Independent completed packaged-app comparison with original saved evidence, runtime/asset byte verification and targeted source-ROI proof; no new model inference or repeated performance benchmark.',checks=checks,check_count=len(checks),all_checks_passed=all(c['passed'] for c in checks),failures=[c['name'] for c in checks if not c['passed']],videos=videos,totals=totals,short_categories=short,active_wall_seconds=wall,wall_change_seconds=wall[1]-wall[0],wall_change_percent=(wall[1]/wall[0]-1)*100,diagnostic_query_exception_proof=str(P/'neon-query-original-source-proof.json'),source_freeze=str(TASK/'final-source-manifest.json'),limitations=['Single actual run per video/version; wall-time increase is observed, cause is not isolated experimentally.','Review establishes no unapproved output or source-evidence changes in these3 videos, not exhaustive identity ground truth for every scene.'])
(P/'final-app-independent-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ('checks','videos')},ensure_ascii=False,indent=2))
