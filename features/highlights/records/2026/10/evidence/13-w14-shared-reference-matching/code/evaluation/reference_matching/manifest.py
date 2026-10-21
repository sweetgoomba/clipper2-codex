"""Reject changed inputs/code before a saved-feature replay produces output."""
import hashlib
import json
import math
from pathlib import Path
import clipper_face_core
from clipper_face_core import EmbeddingSpace, MatchPolicy


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def code_inventory() -> list[dict]:
    roots = [Path(clipper_face_core.__file__).parent, Path(__file__).parent]
    files = sorted(p.resolve() for root in roots for p in root.glob('*.py'))
    return [{'path': str(p), 'sha256': file_sha256(p)} for p in files]


def load_replay_manifest(path: Path) -> dict:
    data = json.loads(Path(path).read_text())
    if data.get('schema') != 'reference_replay_v1':
        raise ValueError('unsupported manifest schema')
    EmbeddingSpace(**data['space'])
    MatchPolicy(**data['policy'])
    for name in ('label_limitation', 'association_basis'):
        if not isinstance(data.get(name), str) or not data[name].strip():
            raise ValueError('missing ' + name)
    for name in ('wall_seconds', 'rss_bytes', 'output_bytes'):
        limit = data['limits'][name]
        if isinstance(limit, bool) or not isinstance(limit, (int, float)) or not math.isfinite(limit) or limit <= 0:
            raise ValueError('invalid resource limit')
    if data['code'] != code_inventory():
        raise ValueError('code hash inventory mismatch')
    if not {'references', 'queries', 'dataset', 'source'} <= data['inputs'].keys():
        raise ValueError('missing replay input')
    for entry in data['inputs'].values():
        p = Path(entry['path'])
        if not p.is_absolute() or file_sha256(p) != entry['sha256']:
            raise ValueError('input hash mismatch: ' + str(p))
    return data
