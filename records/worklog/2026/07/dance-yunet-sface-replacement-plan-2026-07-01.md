# Dance YuNet SFace Replacement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans
> to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for
> tracking.

**Goal:** Remove InsightFace from `dance_highlight` and use OpenCV YuNet/SFace
so the Windows plugin can install and run without MSVC Build Tools.

**Architecture:** Keep the existing `FaceClusterService` public methods and
segment/track clustering flow. Replace only the face backend: model files are
downloaded into `userData/plugin_models/dance_highlight` in packaged mode, then
OpenCV `FaceDetectorYN` detects a face inside each person ROI and
`FaceRecognizerSF` generates the embedding.

**Tech Stack:** Python 3.11, OpenCV Python `FaceDetectorYN`/`FaceRecognizerSF`,
Electron main process model install state, uv lock.

---

## Fixed Model Sources

Checked on 2026-07-01 against OpenCV model zoo:

- YuNet:
  - URL: `https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx`
  - SHA-256: `8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4`
  - Size: `232589`
  - Directory license: MIT
- SFace:
  - URL: `https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx`
  - SHA-256: `0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79`
  - Size: `38696353`
  - Directory license: Apache 2.0

Local API check passed with `opencv-python 4.13.0`:

```text
cv2.FaceDetectorYN -> present
cv2.FaceRecognizerSF -> present
FaceDetectorYN.create(...) -> FaceDetectorYN
FaceRecognizerSF.create(...) -> FaceRecognizerSF
```

## File Map

- Create `desktop/clipper_python/plugins/dance_highlight/dance_highlight/services/face_models.py`
  - Own OpenCV face model specs, cache path resolution, download, size/hash
    verification, and JSON progress emission.
- Modify `desktop/clipper_python/plugins/dance_highlight/dance_highlight/services/face_cluster.py`
  - Replace InsightFace `FaceAnalysis` with OpenCV YuNet/SFace.
  - Preserve `get_face_embedding`, `batch_segment_embeddings`,
    `cluster_embeddings`, and `average_embeddings` call contracts.
- Modify `desktop/clipper_python/plugins/dance_highlight/dance_highlight/services/config.py`
  - Remove InsightFace config fields and add YuNet/SFace detector thresholds.
- Modify `desktop/clipper_python/plugins/dance_highlight/dance_highlight/app.py`
  - Update model loading names and runtime pipeline label.
- Modify `desktop/clipper_python/plugins/dance_highlight/pyproject.toml`
  - Remove `insightface` and dance-local `onnxruntime` dependencies.
- Modify `desktop/clipper_python/plugins/dance_highlight/manifest.json`
  - Replace InsightFace model entry with YuNet/SFace entries and remove
    `insightface` dependency.
- Modify `desktop/clipper_electron/src/main/plugin/plugin-install-state.ts`
  - Point dance model install checks at OpenCV model files under userData.
- Modify `desktop/clipper_electron/test/plugin-install-state.test.mjs`
  - Lock the new dance model install-state mapping.
- Modify `desktop/clipper_electron/src/main/plugin/plugin-venv.ts`
  - Remove temporary `--no-build-package insightface` once the dependency is gone.
- Add Python tests:
  - `desktop/clipper_python/tests/test_dance_face_models.py`
  - `desktop/clipper_python/tests/test_dance_face_cluster_opencv.py`

## Task 1: Lock Electron Dance Model Install State

- [ ] Write tests proving `dance_highlight` is installed when
  `yolov8s-pose.pt`, YuNet, and SFace files exist under userData.
- [ ] Write tests proving missing YuNet/SFace files are reported by model name.
- [ ] Change `plugin-install-state.ts` to remove the InsightFace path mapping and
  use:
  - `userData/yolov8s-pose.pt`
  - `userData/plugin_models/dance_highlight/face_detection_yunet_2023mar.onnx`
  - `userData/plugin_models/dance_highlight/face_recognition_sface_2021dec.onnx`
- [ ] Run:

```text
cd desktop/clipper_electron
npx tsc -p tsconfig.json
node --test test/plugin-install-state.test.mjs
```

## Task 2: Add OpenCV Face Model Asset Helper

- [ ] Add `FaceModelSpec`, `FACE_MODEL_SPECS`, `get_face_model_dir`,
  `is_model_file_valid`, and `ensure_face_models`.
- [ ] Download into a temp file, verify exact size and SHA-256, then atomically
  replace the target file.
- [ ] Emit JSON `download_progress` events with `model_name` matching manifest
  model names.
- [ ] Add tests for env override, hash validation, and fake downloader behavior.
- [ ] Run:

```text
cd desktop/clipper_python
uv run pytest tests/test_dance_face_models.py -q
```

## Task 3: Replace InsightFace Backend

- [ ] Change `FaceClusterService` to lazily create:
  - `cv2.FaceDetectorYN.create(yunet_path, "", config.face_det_size, ...)`
  - `cv2.FaceRecognizerSF.create(sface_path, "")`
- [ ] In `get_face_embedding`, call `setInputSize((w, h))`, sort detected faces
  by score, run `alignCrop`, run `feature`, and L2-normalize the embedding.
- [ ] Preserve existing behavior: return `None` if no face, below threshold, or
  OpenCV raises a recoverable detection/alignment error.
- [ ] Add fake detector/recognizer unit tests for normalized embeddings and
  below-threshold rejection.
- [ ] Run:

```text
cd desktop/clipper_python
uv run pytest tests/test_dance_face_cluster_opencv.py -q
```

## Task 4: Remove InsightFace From Metadata And Lock

- [ ] Update Python config/app/manifest/pyproject naming from InsightFace to
  OpenCV YuNet/SFace.
- [ ] Remove `insightface` and dance-local `onnxruntime` from dance dependencies.
- [ ] Run:

```text
cd desktop/clipper_python
uv lock
rg -n "insightface|buffalo_l|FaceAnalysis" plugins/dance_highlight pyproject.toml uv.lock
```

Expected: no matches in dance plugin files; `uv.lock` has no `insightface`
package entry.

## Task 5: Full Local Verification

- [ ] Run Python targeted tests:

```text
cd desktop/clipper_python
uv run pytest tests/test_dance_face_models.py tests/test_dance_face_cluster_opencv.py -q
```

- [ ] Run Electron verification:

```text
cd desktop/clipper_electron
npx tsc -p tsconfig.json
node --test test/*.js test/*.mjs
```

- [ ] If a representative dance sample is available on Mac, run:

```text
cd desktop/clipper_python
CLIPPER_E2E_DANCE_VIDEO=/path/to/sample.mp4 uv run pytest tests/e2e/test_real_pipeline.py::test_dance_highlight_real_pipeline -q -s
```

## Task 6: Windows Handoff

- [ ] On the Windows PC without MSVC Build Tools, verify:
  - first launch opens the window;
  - dance plugin venv install no longer attempts `insightface`;
  - YuNet/SFace files download under `%APPDATA%\Clipper2\plugin_models\dance_highlight`;
  - a small dance job reaches plugin execution.

## Progress 2026-07-01

- Runtime isolation batch is implemented in `desktop/clipper_electron`.
- Found and fixed one nested plugin venv path issue before starting model
  replacement: packaged plugin cwd and PATH now use explicit userData.
- Implemented OpenCV YuNet/SFace face backend for `dance_highlight`.
- Removed `insightface`, `buffalo_l`, and `FaceAnalysis` from the dance plugin
  runtime code and `uv.lock`.
- Updated Electron model install state and model size metadata for:
  - `opencv-yunet-face-detection`
  - `opencv-sface-face-recognition`
- Local verification completed:

```text
cd desktop/clipper_python
uv run --package clipper-plugin-dance-highlight python -m pytest tests/test_dance_face_models.py tests/test_dance_face_cluster_opencv.py -q
-> 8 passed

CLIPPER_DANCE_FACE_MODEL_DIR=/private/tmp/clipper-face-model-check uv run --package clipper-plugin-dance-highlight python -c "..."
-> FaceDetectorYN FaceRecognizerSF

cd desktop/clipper_electron
npx tsc -p tsconfig.json
node --test test/*.js test/*.mjs
-> 47 passed

CLIPPER_DANCE_FACE_MODEL_DIR=/private/tmp/clipper-face-model-check uv run --package clipper-plugin-dance-highlight python -m pytest tests/e2e/test_plugin_smoke.py::test_health_reports_plugin_identity -q -s -k dance_highlight
-> 1 passed, 2 deselected

CLIPPER_DANCE_FACE_MODEL_DIR=/private/tmp/clipper-face-model-check uv run --package clipper-plugin-dance-highlight python -m pytest tests/e2e/test_plugin_smoke.py::test_job_with_missing_video_fails_gracefully -q -s -k dance_highlight
-> 1 passed, 1 deselected

User-run representative Mac sample:

```text
cd desktop/clipper_python
CLIPPER_E2E_DANCE_VIDEO="/Users/jina/project/adlight/desktop/clipper_python/sample_videos/KiiiKiii - 404 (New Era) #엠카운트다운 EP.915 | Mnet 260205 방송.mp4" \
uv run --package clipper-plugin-dance-highlight python -m pytest tests/e2e/test_real_pipeline.py::test_dance_highlight_real_pipeline -q -s
-> 1 passed in 111.13s

uv run --package clipper-plugin-dance-highlight python -m pytest tests/test_dance_face_models.py tests/test_dance_face_cluster_opencv.py -q
-> 8 passed in 0.65s
```

Observed sample output summary:

```text
duration_sec=190.7239
raw_main_segments=200
smoothed_main_segments=62
kept_main_segments=61
dropped_main_no_face=1
num_persons_inferred=8
montages=8
lists.main=61
lists.group=0
```

Quality note: this proves the Mac pipeline executes with YuNet/SFace, but it
does not prove final face clustering quality. If the expected member count for
the sample is lower than 8, tune `cluster_distance_threshold` and/or sampling
after visual review of the generated montages.
```

Still not completed:

- Mac representative dance visual quality review/tuning.
- Windows packaged installer verification on a normal PC without MSVC Build
  Tools.
- Windows dance plugin venv install/run smoke.
