"""Compare saved inputs and actual model execution, not UI labels alone."""
from pathlib import Path
import hashlib,json

root=Path(__file__).parent
results=[]
for case in json.loads((root/'run-manifest.json').read_text()):
    output=Path(case['output_root'])
    path=output/'diagnostics/face_evidence.json'
    if not path.exists():continue
    before=json.loads((root/f"baseline/{case['baseline_project_id']}/face_evidence.json").read_text())
    after=json.loads(path.read_text())
    oldroot=Path(json.loads((root/f"baseline/{case['baseline_project_id']}/project.json").read_text())['outputRoot'])
    def refs(folder):
        return {str(p.relative_to(folder/'refs')):hashlib.sha256(p.read_bytes()).hexdigest()
                for p in (folder/'refs').rglob('*') if p.is_file()}
    fields=['reference_id','sample_id','image_sha256','width','height']
    identity=lambda e:[{k:r[k] for k in fields} for r in e['references']]
    results.append(dict(title=case['title'],
        source_sha256_equal=before['runtime']['video_sha256']==after['runtime']['video_sha256'],
        config_sha256_equal=before['runtime']['config_sha256']==after['runtime']['config_sha256'],
        saved_reference_files_equal=refs(oldroot)==refs(output),
        reference_manifest_equal=identity(before)==identity(after),
        reference_embeddings_equal=[r['embedding'] for r in before['references']]==[r['embedding'] for r in after['references']],
        mask_reason=after['mask_continuity_refinement'].get('reason'),
        acceleration=after['runtime']['opencv_face_acceleration']))
(root/'provenance-comparison.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
print(json.dumps([{k:v for k,v in r.items() if k!='acceleration'} for r in results],ensure_ascii=False))
