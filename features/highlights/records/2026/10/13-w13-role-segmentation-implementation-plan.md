# W13 역할 판정·구간 비교 Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans inline. User requested continuous work through a reviewable notebook; no extra per-task approval and no commits.

**Goal:** 저장된 MoveNet512·YOLO26s에서 단독/공동 메인·군무·검토 필요를 구분하고, 짧은 오선택 완화 전후와 구간을 새 노트북에서 비교한다.

**Architecture:** 기존 pose/익명 추적/움직임/메인 점수 코드는 보존한다. 새 순수 함수가 역할을 결정하고, 별도 시간 후처리와 평가기가 결과를 소비한다. 라벨은 평가기만 읽는다.

**Tech Stack:** 기존 Python3.11, NumPy/SciPy, pytest, JSON, notebook HTML/JavaScript; 새 dependency/모델 없음.

**Spec:** [승인된 조사·설계 §6–10](13-w13-pipeline-research-and-scoped-redesign.md), [실험 초안](13-w13-pipeline-redesign-experiment-manifest.json).

## Global Constraints

- 기존 worktree `feature/w13-dance-metadata-eval-20261001` 재사용. 기존 dirty3개/모델/정답/노트북 보존. 제품·W14 변경 없음.
- 전체 0–133.654059초, frozen truth 21행. 신규 추론·다운로드·얼굴·완성 clip·외부 과금0. 2모델×C0/C1/C2=6cache 재생.
- 각120초/RSS2GiB, 전체 출력100MiB. 모든 설정·코드 hash를 실행 전 고정한다. 후속 재실행은 별도 revision으로 남긴다.
- 미표시 무시, 명시적 제외 negative 평가, main/group 중첩은 별도 보고. 이름을 predictor에 입력하지 않는다.
- 자동 결과는 연구 후보이며 품질 목표 미달이면 미채택을 명확히 표시한다.

## Review Focus

1. 저품질·누락이 군무로 둔갑하거나 강제 메인이 생기는 경우 → Task1.
2. 공동 메인 선택 시 오선택을 숨기고 한 명 맞으면 정답이라고 세는 경우 → Task2.
3. 중첩 GT/미표시/제외가 예측 mask나 거짓 분모로 사용되는 경우 → Task2.
4. 긴 누락/shot 경계/다른 track을 짧은 튐으로 병합하는 경우 → Task1.
5. 타임라인 끝·불규칙 관측의 구간 시간 오류, UI bbox/원본 비동기 → Task1/3.

### Task 1: 역할 판정과 구간

**Files:** create `tools/w13_role_policy.py`, `tests/test_w13_role_policy.py` in existing experiment worktree.

**Interfaces:** `classify_roles(features, selected, config) -> list[dict]`; `suppress_short_excursions(frames, max_sec=.3, max_margin=.14) -> list[dict]`; `build_segments(frames, duration, max_gap=.15) -> list[dict]`. Output frame has time_sec, role, main_track_ids, main_bboxes, persons, reason, evidence, raw provenance. Group/unknown have empty confirmed mains. Input unchanged.

- [x] RED: dominant solo despite moving peers; similar ensemble group with empty main; separated top subset joint; invalid motion unknown; standing pose retains established role; elapsed-time debounce; unavailable main/gap resets; weak A-B-A suppressed only if A remains visible; strong/long B preserved; shot/gap not bridged; end bound and invalid-time rejection.
- [x] GREEN: same C0 main score, dominant score gaps and motion/observation support, quality guards, seconds-based group/joint debounce. Exact thresholds recorded before replay. No GT imports.
- [x] Verify: existing Python interpreter `-m pytest tests/test_w13_role_policy.py tests/test_w13_temporal_pose.py -q`; all pass.

### Task 2: 分리 평가와 frozen 실행

**Files:** create `tools/w13_role_evaluation.py`, `tools/w13_role_experiment.py`, `tests/test_w13_role_evaluation.py`.

**Interfaces:** `evaluate_roles(frames, truth) -> dict`; `evaluate_sparse(frames, pose, labels) -> dict`; `evaluate_boundaries(segments, truth, duration) -> dict`; CLI `python -m tools.w13_role_experiment --manifest PATH`.

- [x] RED: group-only/main-only/overlap/exclude/unmarked are separate; extra selected body lowers selection precision; missing target remains in coverage denominator; boundary matching one-to-one and ignores unlabeled/overlap domain; hash mismatch/existing output rejected.
- [x] GREEN: freeze manifest with candidate parameters, code hashes, baseline caches and label hashes; validate then write new output folder only. Compute C0/C1/C2 per model, resource receipt and failures. Preserve all outputs including unsuccessful settings.
- [x] Verify: targeted tests pass; perform exactly6 cache conditions and inspect metrics/limits. If gates fail, label candidate failed; no silent tuning sweep. HOTA/IDF1/identity/true identity-specific switch latency unavailable, do not manufacture scores.

### Task 3: 새 노트북과 영상 비교

**Files:** create `tools/w13_build_role_review.py`, `notebooks/w13_dance_iteration_lab_13_roles_and_segments.ipynb`; new output review HTML.

**Interfaces:** consumes Task2 JSONs, references existing proxy video without new video export. Display C0→C2 per model, optional C1→C2; group border green/no main, joint orange boxes, single red, unknown amber notice. Distinguish legacy contradictory group+main in C0.

- [x] Generate new notebook only, visible failures/limitations, current truth unchanged, full-source synchronized time slider updates during drag, clickable predicted segments and truth intervals.
- [x] Execute notebook read-only output cells once; inspect in browser with both model choices, group/solo/unknown frames, scrub and segment jump.
- [x] Verify: no cell errors, source/truth/cache hashes unchanged; report notebook location and how user compares.

### Task 4: 회귀·독립 리뷰·인계

- [x] Run full pytest once after meaningful unit gates, save log. Report existing skips/failures precisely; no ML tests/downloads beyond authorized cache mode.
- [x] Fresh reviewer as required by executing-plans skill; review new files including untracked files directly, not HEAD diff alone. Fix material defects with reproducing tests.
- [x] Record results and limitations in dated record/W13/WORKBOARD; user approval needed only for actual quality judgment. No commit/push/merge/deploy.
