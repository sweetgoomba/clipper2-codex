# Isolated Face Candidate Comparison Implementation Plan

> **2026-10-26 문서 이관 안내:** AuraFace·Intel0095 격리 비교 실행 계획이다. [실제 실행 결과·실패·남은 정답 검증](14-w14-candidate-runtime-and-face-review.md)와 [후속 공통 모델 결정](23-person-highlight-checkpoint-and-shared-face-model.md)를 함께 읽는다. 아래의 제품 미통합·GT 대기 상태는 10/14 당시 기록이다.

> **For agentic workers:** Use superpowers:executing-plans inline. Preserve the existing W14 worktree and all earlier experiments. Do not commit/push or integrate product code.

**Goal:** Prepare the two supplied videos and two licensed recognition candidates, verify their actual CPU execution/preprocessing, and produce a controlled comparison and a ground-truth review packet without claiming unlabelled accuracy.

**Architecture:** Evaluation-only modules consume saved YuNet observations and original source frames. Candidate embeddings remain in separate spaces. The existing gallery/matching core and product adapters are preserved. New-video face labels are obtained before accuracy scoring.

**Tech Stack:** uv-managed Python3.11, existing OpenCV4.13 CPU, optional ORT/OpenVINO in a dedicated evaluation venv, existing ffmpeg/yt-dlp tools.

**Spec:** [인식 후보 비교시험 설계](14-w14-recognition-candidate-evaluation-design.md) · [추가 영상 입력 준비](14-w14-holdout-input-preparation.md).

## Global constraints

- Mac Apple Silicon only and Windows x64 as eventual distribution targets; executing on the present Mac is not Windows verification.
- Gallery23/source20segments/451observations/406selected faces stay fixed for the first comparison. Model-specific required alignment is explicit.
- New videos: `J9DlrnNlgfE`, `6bVUjsUi9sw`; each `[30,60)`, `[80,110)`, `[125,155)`, `[165,195)` seconds. No new-video tuning.
- No core, SDK, Dance/Person product code, existing venv, workspace lock, or W13 changes. Evaluation-only code under `evaluation/candidate_comparison/`.
- New files in `evaluation-output/candidate-comparison-20261014/`; never overwrite v1–v5. Models/media/venv separate from reports.
- CPU1 thread/batch1; inference worker max600seconds/4GiB RSS; report output max2GiB. Acquisition (models+media) max4GiB and dedicated venv/cache max4GiB, checked before inference; no silent increase.
- Weight rights/provenance and preprocessing must be inspected before inference. No InsightFace pack, 0009, paid API, product deployment, or automatic retries.
- User clarified GT means the actual selected face identity, not a request to re-label all main-dancer intervals. Their subsequent `그래` is treated as consent to the previously enumerated isolated execution scope with this clarification. Stop only for material new scope, unavailable necessary input, or permission denial.

## Review focus

1. Comparing same-dimensional vectors from different spaces must fail.
2. A reflection, reversed landmark convention, or double normalization must not silently pass as valid input.
3. Native/runtime failure must remain an inference error rather than ordinary recognition rejection.
4. Unknown/absent GT must not enter accuracy denominators or be invented from the old main timeline.
5. Mixed physical identities sharing one track ID must not be silently averaged into one identity.

## Task 1 — Immutable source/model/runtime preparation

**Files:** new output `preparation.json`, `models/*`, `sources/*`, runtime lock/metadata and acquisition logs.
**Consumes:** source URLs, exact public weight URLs/known checksums, existing reference/dataset paths.
**Produces:** local file paths, actual hashes/sizes, metadata, preserved license texts, runtime versions.

- [x] Verify isolated worktree, disk budget, existing tool versions and available native Python.
- [x] Fetch provider manifests/licenses and pin revision; download exact required weights only, check provider checksum plus local SHA256.
- [x] Fetch video metadata and use existing downloader for at most1080p video-only sources; keep the selected source file unchanged for all candidates. Record original available resolution and do not mislabel selected1080p as maximum/source-master resolution. Existing128/112 aligned JPEGs are not model inputs.
- [x] Create dedicated venv with pinned CPU runtimes; resolve without touching project lock or product venv. Record wheel/platform metadata and installed native licenses.
- [x] Inspect ONNX graph/IR shapes, dtype, graph input normalization and provider alignment/preprocessing code. Record unresolved issues before any probe.

## Task 2 — Fixed input and candidate adapters

**Files:** `evaluation/candidate_comparison/adapters.py`, `test_adapters.py`, `prepare_inputs.py`; output `input-manifest.json`.
**Interfaces:** `align_face(frame_bgr, landmarks_xy, template_xy, size) -> uint8 crop`; `preprocess(crop, model_spec) -> float32 NCHW`; `embed(aligned) -> float32 L2 vector` with explicit space ID/failure.

- [x] Read existing `coverage_replay.py`, `owned_replay.py`, and core matching contracts; reuse saved `face_candidates`, selected index, source ROI and frame ID.
- [x] Write tests that fail on RGB/BGR reversal, duplicate normalization, invalid landmarks and zero/nonfinite vectors; verify RED, implement minimal adapter, verify GREEN.
- [x] Preserve SFace compatibility facade by leaving product code unchanged. Add AuraFace ORT and0095 OpenVINO only after Task1 specifications are grounded.
- [x] Build all fixed input/GT status records and resource/inference-call manifest before model loading; distinguish unlabelled data from outside-gallery faces.

## Task 3 — Runtime proof, comparison, and review packet

**Files:** `evaluation/candidate_comparison/run.py`, `test_report.py`, output timing/errors/vectors/scores, small review page reusing existing comparison style.
**Consumes:** Task1 verified assets and Task2 manifest; existing23ref and406video face slots.
**Produces:** actual call counts/runtime evidence, per-observation scores and failures, selected-face label review data; no automatic quality claim.

- [x] Test that missing/error/unlabelled records stay in reports and are excluded only from explicitly labelled identity metric denominators; reproduce failing tests, implement, verify.
- [x] One bounded smoke per model with fixed inputs, then one cached full embedding pass after successful shape/numerical checks. Record smoke calls separately from maximum429 per-model first pass.
- [x] Recompute model-specific reference gallery and scores. Do not reuse SFace thresholds or tune on supplied holdouts. Label score ranking as ranking, not confirmed recognition accuracy.
- [x] For new videos, decode the predeclared240source-second frames with actual PTS provenance and create anonymous visibility/face-review material. Do not infer named identity from appearance or old main GT. Request only necessary user labels together.
- [x] Verify score calculations independently, provenance completeness, failure accounting and relevant regression tests. If code is implemented, use one independent review as required by executing-plans; no new user-owned thread.
- [x] Update W14/WORKBOARD/dated record/W13 contract with executed counts, limits, accepted/rejected changes, and remaining GT/Windows/W13 integration gaps.

## Execution ledger

- Plan initial self-review: existing product boundaries and latest face-label clarification preserved. No commit/push; user's persistent instruction to continue substantial authorized work overrides repeated execution-method selection. This session implements inline.
- Tasks1–3 completed for isolated execution/input preparation/review packet. New-candidate native CPU runs succeeded. Recognition quality/threshold and new-video evaluation remain pending independent GT; they are not marked complete.

- Actual: candidate each426full+1smoke; 23references/403video vectors,3alignment errors,36no-face9association uncertain. SFace406cache. Relevant116pytest +5Node assertions, independent6060distance agreement. Temporal initial review19 (segment20 has no selected face).
- Ruling: preserve input-manifest v1 for the initial Aura smoke; freeze v2 after ps preflight fix. First smoke external monitor failed but native completed. Later workers externally monitored. No repeated model run to hide the first failure.
- Ruling: OpenVINO default import loads converter telemetry; full run uses inspected official CI=true opt-out with consent=False. Initial smoke import-event delivery unknown; native inference data was not passed to telemetry.
- Ruling: no-video-GT means uncalibrated score rankings and a label packet only. Do not force winner or use main-interval labels as face labels. Risk: more label work remains before quality can be judged.
