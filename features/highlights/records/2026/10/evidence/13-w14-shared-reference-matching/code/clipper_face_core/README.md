# clipper-face-core 0.2.0

Optional, plugin-neutral face observations and reference matching for Python 3.11.
The SDK has no dependency on this package. Consumers own model preparation and their
venvs; package import never downloads weights or initializes a model. NumPy is the
base dependency. Install `clipper-face-core[opencv]` only in consumers using the
YuNet/SFace backend. CPU wheels are the tested route; Windows is not yet verified.

## Reference matching

```python
from clipper_face_core import build_gallery, match_reference, combine_reference_matches

gallery = build_gallery(reference_samples, space=embedding_space)
results = [match_reference(q, gallery, explicit_policy) for q in selected_faces]
consensus = combine_reference_matches(scope_id, selected_faces, results, explicit_policy)
```

See `examples/reference_matching.py` for a complete consumer adapter with scope
partitioning. It rejects conflicting observation IDs across the complete batch
and deduplicates identical repeats. It takes no Dance Segment, UI, SDK/job or
PersonGroup objects.

- `EmbeddingSpace` fingerprints recognizer weight SHA, alignment, preprocessing,
  normalization, dimension, backend version and cosine **distance** (smaller is closer).
  Detector/config hashes live separately in `SourceEvidence`.
- `ReferenceSample` connects an opaque, consumer-supplied reference ID to an image
  source/observation, a feature or explicit failure. `build_gallery` uses float32
  mean followed by L2 with epsilon 1e-9, preserving the existing Dance baseline.
  Invalid samples remain in `failures`; no valid reference raises `GalleryBuildError`.
  Invalid centroids are excluded with per-sample failure reasons so one nearly
  cancelled reference cannot invalidate other valid references.
  Mixed spaces and conflicting duplicate sample IDs are rejected. Identical IDs
  do not acquire extra weight. Vectors have immutable, owned storage.
- `QueryEvidence` carries the selected observation, source provenance, feature or
  failure, quality evidence and consumer-declared `association` certainty. The core
  does not decide which body owns a face. `confirmed` is a consumer assertion, not
  proof that a body/face connection is correct.
- `MatchPolicy(max_distance, min_margin, minimum_support)` has no defaults. Thresholds
  need evaluation per embedding space. `match_reference` returns all reference
  distances, top-two margin, `matched / ambiguous / unmatched / invalid`, reasons,
  and fingerprints binding the query, gallery and policy. Different queries may
  match the same reference. Adding a query cannot reserve a name or change another
  query's choice. A tie is ambiguous; a single reference must pass distance and has
  no margin evidence.
- `combine_reference_matches` accepts only one source/analysis/scope with matching
  provenance. Duplicate observations do not add support. Strong matches to different
  references produce `conflicting_references`, never an averaged-away identity.
  Insufficient support remains ambiguous. Individual failed/uncertain results are
  retained in the consensus. An empty scope returns `invalid / no_evidence`.

Time and geometry are explicit: display-frame pixel xyxy plus derived normalized
coordinates, rotation applied before coordinates, integer PTS + rational time base
when known, otherwise `derived_seconds`. Never label frame-index/FPS estimates as
source PTS. Scope ranges are consumer-supplied half-open intervals. The library does
not create tracks, split a consumer's clips or infer physical identity continuity.

## Existing observation/grouping API

The prior `ModelFiles`, `FaceDetection`, `OpenCvFaceBackend`, `FaceObservation`,
`FaceGroup`, `FaceInterval`, `group_observations` and `rank_representatives` exports
remain available. The OpenCV class is lazily imported; DTOs do not require cv2.

`OpenCvFaceBackend.detect(frame_bgr)` returns all **valid-geometry** YuNet candidates;
SFace alignment/embedding failures preserve a candidate with `embedding=None`.
Legacy grouping/representative policies and optional progress callback are unchanged.
The legacy Person `FaceObservation` still uses seconds/frame index and recognizer/
config fingerprints. It is not silently upgraded to the new reference contract.

Do not directly mix legacy Person vectors normalized by `vector/norm` with the
Dance baseline normalized by `vector/(norm+1e-9)`. Declare and evaluate the precise
processing space. This package does not add a persistent embedding cache.

## Verification and current integration boundary

`evaluation/reference_matching` replays hashed local feature artifacts without
loading ML models. Its manifest pins files, code, processing space, policy and
limits; changed inputs, incompatible spaces, pickle arrays and existing output
folders are rejected. Run the CLI under an external supervisor for enforceable
wall-time/RSS limits; the worker also checks measured limits before writing output.
Every replay query must declare association explicitly; missing metadata is never
treated as confirmed face ownership.

The initial replay reproduced all five reference centroids and all 54 saved query
comparisons exactly. A three-sample diagnostic scope returns the expected reference
instead of the old global cluster's different name. These are previously inspected
examples, not independent accuracy results. W13 product integration, consumer venv
installation/fingerprint, independent face-ownership labels, broader video quality
and Windows remain separate verification steps. No Dance/Person app behavior is
changed merely by adding this workspace package.
