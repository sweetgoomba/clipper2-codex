"""Replay normalized local evidence; never import a face detector or download assets."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
import time
import numpy as np
from clipper_face_core import (
    EmbeddingSpace, SourceEvidence, ReferenceSample, QueryEvidence, MatchPolicy,
    build_gallery, match_reference, combine_reference_matches,
)
from .manifest import load_replay_manifest, file_sha256


def _rss_bytes():
    import resource
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == 'darwin' else 1024)


def _counts(rows):
    counts = dict(total=len(rows), correct=0, wrong=0, unmatched=0, ambiguous=0, invalid=0, unlabelled=0)
    for row in rows:
        if row['expected_reference'] is None:
            counts['unlabelled'] += 1
        if row['status'] == 'matched':
            if row['expected_reference'] is not None:
                counts['correct' if row['reference_id'] == row['expected_reference'] else 'wrong'] += 1
        else:
            counts[row['status']] += 1
    return counts


def run_replay(manifest_path: Path, output_dir: Path) -> dict:
    start = time.monotonic()
    output_dir = Path(output_dir)
    if output_dir.exists():
        raise FileExistsError(output_dir)
    manifest = load_replay_manifest(manifest_path)
    inputs = {k: Path(v['path']) for k, v in manifest['inputs'].items()}
    dataset = json.loads(inputs['dataset'].read_text())
    space, policy = EmbeddingSpace(**manifest['space']), MatchPolicy(**manifest['policy'])

    def values(row, vectors):
        if row['space_fingerprint'] != space.fingerprint:
            raise ValueError('dataset embedding space mismatch')
        key = row['embedding_key']
        return SourceEvidence(**row['source']), None if key is None else vectors[key]

    with np.load(inputs['references'], allow_pickle=False) as vectors:
        references = []
        for row in dataset['references']:
            source, vector = values(row, vectors)
            references.append(ReferenceSample(row['id'], row['reference_id'], source, space,
                                               vector, row.get('failure')))
    gallery = build_gallery(references, space=space)
    queries, matches, rows = {}, {}, []
    with np.load(inputs['queries'], allow_pickle=False) as vectors:
        for row in dataset['queries']:
            if row['id'] in queries:
                raise ValueError('duplicate replay query ID')
            if 'association' not in row:
                raise ValueError('query requires explicit association')
            source, vector = values(row, vectors)
            q = QueryEvidence(row['id'], source, space, vector, row['association'],
                              row.get('failure'), tuple(tuple(v) for v in row.get('quality', [])))
            result = match_reference(q, gallery, policy)
            queries[q.observation_id], matches[q.observation_id] = q, result
            item = asdict(result)
            item.update(condition=row.get('condition', 'default'), expected_reference=row.get('expected_reference'))
            if 'expected_distances' in row:
                current = {c.reference_id: c.distance for c in result.candidates}
                expected = row['expected_distances']
                if current.keys() != expected.keys():
                    raise ValueError('distance comparison reference IDs differ')
                item['max_distance_delta'] = max(abs(current[k] - expected[k]) for k in current)
            if 'baseline_assigned' in row:
                item['baseline_assigned'] = row['baseline_assigned']
                item['baseline_assignment_agrees'] = result.reference_id == row['baseline_assigned']
            rows.append(item)
    scopes = []
    for scope in dataset.get('scopes', []):
        ids = scope['observation_ids']
        result = combine_reference_matches(scope['id'], [queries[k] for k in ids], [matches[k] for k in ids], policy)
        scopes.append({**asdict(result), 'baseline_reference_id': scope.get('baseline_reference_id')})
    centroid_checks = {}
    if 'baseline_centroids' in inputs:
        with np.load(inputs['baseline_centroids'], allow_pickle=False) as vectors:
            for entry in gallery.entries:
                prior = vectors[entry.reference_id]
                if prior.shape != entry.centroid.shape:
                    raise ValueError('centroid dimensions differ')
                centroid_checks[entry.reference_id] = {
                    'array_equal': bool(np.array_equal(entry.centroid, prior)),
                    'max_abs_delta': float(np.max(np.abs(entry.centroid - prior)))}
    report = dict(schema='reference_replay_result_v1', manifest_sha256=file_sha256(Path(manifest_path)),
                  model_calls=0, label_limitation=manifest['label_limitation'],
                  association_basis=manifest['association_basis'], space_fingerprint=space.fingerprint,
                  gallery_fingerprint=gallery.fingerprint, policy=asdict(policy), counts=_counts(rows),
                  by_condition={c: _counts([r for r in rows if r['condition'] == c])
                                for c in sorted({r['condition'] for r in rows})},
                  rows=rows, scopes=scopes, centroid_checks=centroid_checks,
                  reference_failures=[asdict(f) for f in gallery.failures],
                  wall_seconds=time.monotonic() - start, peak_rss_bytes=_rss_bytes())
    raw = json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False).encode('utf-8')
    limits = manifest['limits']
    if (report['wall_seconds'] > limits['wall_seconds'] or report['peak_rss_bytes'] > limits['rss_bytes']
            or len(raw) > limits['output_bytes']):
        raise RuntimeError('replay resource limit exceeded')
    output_dir.mkdir(parents=True, exist_ok=False)
    (output_dir / 'report.json').write_bytes(raw)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args()
    report = run_replay(args.manifest, args.output_dir)
    print(json.dumps({'model_calls': report['model_calls'], 'counts': report['counts']}))


if __name__ == '__main__':
    main()
