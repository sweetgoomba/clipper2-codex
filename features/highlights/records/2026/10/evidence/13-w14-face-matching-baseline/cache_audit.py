"""Read-only replay of existing W13 mapping and interval scoring functions."""
import ast
import hashlib
import json
import math
from pathlib import Path

ROOT = Path('/Users/jina/project/adlight')
BASE = ROOT / '.worktrees/w13-dance-metadata-eval-20261001/desktop/clipper_python'
OUTPUT = Path(__file__).resolve().parent / 'cache-audit.json'
SHA = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()

def load_functions(path, names, globals_dict):
    parsed = ast.parse(path.read_text())
    body = [node for node in parsed.body if isinstance(node, ast.FunctionDef) and node.name in names]
    assert len(body) == len(names)
    exec(compile(ast.Module(body=body, type_ignores=[]), str(path), 'exec'), globals_dict)
    return globals_dict

score_path = BASE / 'tools/w13_human_review.py'
map_path = BASE / 'tools/w13_face_cache_sweep.py'
score = load_functions(score_path, {'_union_seconds', 'compare_intervals'}, {'math': math})['compare_intervals']
mapping = load_functions(map_path, {'mapping_from_distances'}, {})['mapping_from_distances']
truth_path = BASE / 'output/human-review/yFTAYXDTjqI/user-ground-truth.json'
truth = json.loads(truth_path.read_text())
assert truth['status'] == 'confirmed' and len(truth['rows']) == 21
labels_path = ROOT / '.codex/features/highlights/records/2026/10/01-w13-holdout-source-labels-v1.json'
labels = json.loads(labels_path.read_text())
trace_path = Path(__file__).resolve().parent / 'selected-face-trace/trace-result.json'
trace = json.loads(trace_path.read_text())
results = {}
for condition, filename in [('saved256', 'movenet256-face-cache.json'), ('saved512', 'movenet512-face-baseline.json')]:
    cache_path = BASE / 'output/evaluation/yFTAYXDTjqI/human-truth-iteration' / filename
    data = json.loads(cache_path.read_text())
    assert SHA(truth_path) == data['manifest']['answer']['sha256']
    prediction = data['prediction']
    distances = prediction['cluster_candidate_distances']
    actual = prediction['cluster_to_member']
    reproduced = {str(k):v for k,v in mapping({int(k):v for k,v in distances.items()}, .60, .45, .08).items()}
    assert reproduced == actual
    nearest = {cid:min(ds, key=ds.get) for cid,ds in distances.items() if min(ds.values()) <= .60}
    outcomes = {}
    for name, chosen in [('stored', actual), ('nearest_only_counterfactual', nearest)]:
        main = [{'start':s['start_sec'], 'end':s['end_sec'], 'person_id':chosen.get(str(s['cluster_id']), 'unknown')} for s in prediction['kept_main']]
        main += [{'start':s['start_sec'], 'end':s['end_sec'], 'person_id':'unknown'} for s in prediction['dropped_main']]
        group = [{'start':s['start_sec'], 'end':s['end_sec']} for s in prediction['smoothed_group']]
        outcomes[name] = score(truth['rows'], {'main':main, 'group':group})
    assert all(abs(value-data['score'][key]) < 1e-7 for key,value in outcomes['stored'].items())
    redirected = []
    for cid, ds in distances.items():
        ranked = sorted(ds.items(), key=lambda x:x[1])
        if cid in actual and actual[cid] != ranked[0][0]:
            redirected.append({'cluster_id':cid, 'nearest':ranked[0], 'assigned':actual[cid], 'assigned_distance':ds[actual[cid]],
                               'affected_intervals':[[s['start_sec'],s['end_sec']] for s in prediction['kept_main'] if str(s['cluster_id'])==cid]})
    stage_trace = []
    refs = data['face_cache']['reference_embeddings']
    offset = 0
    for segment in prediction['kept_main']:
        count = segment['track_embedding_count']
        vectors = data['face_cache']['track_embeddings'][offset:offset+count]
        offset += count
        nearest_tracks = []
        for vector in vectors:
            ranked = sorted([(name, 1-math.fsum(a*b for a,b in zip(vector, ref))) for name,ref in refs.items()], key=lambda x:x[1])
            nearest_tracks.append(ranked[:2])
        stage_trace.append({'interval':[segment['start_sec'],segment['end_sec']], 'track_average_top2':nearest_tracks,
                            'cluster_id':segment['cluster_id'], 'final_reference_label':segment['person_id']})
    points = []
    for label in labels['frames']:
        if label['stratum'] != 'strict_solo':
            continue
        time_sec = label['frame_index']*1001/60000
        live = next(r for r in trace['rows'] if r['frame_index']==label['frame_index'] and r['condition']==condition)
        expected = {m for row in truth['rows'] if row['kind']=='main' and row['start_sec']<=time_sec<row['end_sec'] for m in row['members']}
        existing = [s['person_id'] for s in prediction['kept_main'] if s['start_sec']<=time_sec<s['end_sec']]
        points.append({'frame_index':label['frame_index'], 'time_sec':time_sec, 'input_label':sorted(expected),
                       'selected_body_matches_source_bbox':live['body_iou_to_source_label']>=.30,
                       'direct_roi_label':live.get('assigned'), 'existing_segment_label':existing,
                       'direct_label_agrees':live.get('assigned') in expected, 'segment_label_agrees':any(v in expected for v in existing)})
    selected = [p for p in points if p['selected_body_matches_source_bbox']]
    results[condition] = {'cache':{'path':str(cache_path),'sha256':SHA(cache_path)}, 'stored_mapping_and_scores_reproduced':True,
                          'mapping_rank_redirects':redirected, 'whole_pipeline_overlap_diagnostic':outcomes,
                          'point_trace':points, 'stage_trace':stage_trace,
                          'selected_correct_subset':{'count':len(selected), 'direct_roi_label_agrees':sum(p['direct_label_agrees'] for p in selected),
                                                     'stored_segment_label_agrees':sum(p['segment_label_agrees'] for p in selected)}}
report = {'schema':'w14_cached_mapping_audit_v1','truth':{'path':str(truth_path),'sha256':SHA(truth_path)},
          'source_body_labels':{'path':str(labels_path),'sha256':SHA(labels_path)},
          'replayed_code':[{'path':str(p),'sha256':SHA(p)} for p in [score_path,map_path]],
          'results':results,
          'limitation':'Same-video diagnostic on previously used labels. Interval overlap mixes body selection, boundaries and matching. Direct ROI vs segment aggregation is not an independent model accuracy comparison.'}
OUTPUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'output':str(OUTPUT),'sha256':SHA(OUTPUT),'selected_correct_subsets':{k:v['selected_correct_subset'] for k,v in results.items()}},ensure_ascii=False))
