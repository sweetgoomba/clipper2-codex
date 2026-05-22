# Clipper1 Render Parity Checkpoint - 2026-05-08

작성 시각: 2026-05-08 18:03 KST

## 현재 상태

Legacy Clipper1 template render parity는 이제 기존 Clipper1에서 실제로 만든 정답 이미지 25개를 fixture로 두고 비교한다. 현재 기준은 `channelTolerance=32`, `maxMismatchRatio=0.0039`이며 전체 25개가 통과한다.

현재 최악 케이스는 `template-17-16_9`, mismatch `0.0038541666666666668`이다. 이전 최악이던 `template-6-1_1`은 automatic image zoom을 기존 Clipper1 MoviePy/OpenCV 방식의 30fps frame sequence로 맞춘 뒤 `0.006317515432098766 -> 0.00011381172839506173`까지 내려갔다.

`.codex`는 root 문서 디렉터리이고 root가 git repo가 아니라서 커밋 대상은 아니다. 코드 변경은 아래 두 repo에 나누어 커밋했다.

## 커밋

- `clipper_python` branch: `feature/plugin-architecture`
  - `e79e7a4 feat: tighten legacy clipper1 render parity`
- `adlight_python` branch: `feature/d2x-electron`
  - `4afaca5 test: add clipper1 reference frame exporter`

두 repo 모두 각각 원격 branch보다 1 commit 앞서 있고 working tree는 깨끗하다.

## 이번 세션에서 완료한 것

- 기존 Clipper1 `adlight_python`의 `VideoService.create_video()`로 실제 영상을 만든 뒤 첫 프레임을 추출하는 reference exporter를 만들었다.
- 21개 design `16:9` + ratio edge 4개, 총 25개 Clipper1 reference frame fixture를 `clipper_python/tests/fixtures/clipper1_golden_frames`에 커밋했다.
- 현재 Clipper2 renderer output을 회귀 방지용 baseline fixture로 `clipper_python/tests/fixtures/clipper2_template_baseline_frames`에 커밋했다.
- full ratio layout overlay 순서와 gradient overlay 성격을 반영했다.
- text PNG overlay, text height zero-height glyph 포함, final x264 reencode, automatic image zoom OpenCV frame sequence 보정을 TDD로 진행했다.
- `template-6-1_1`의 큰 pixel drift를 사실상 제거했다.
- golden frame 비교 기준을 단계적으로 `0.04 -> 0.015 -> 0.012 -> 0.008 -> 0.007 -> 0.0067 -> 0.0065 -> 0.0064 -> 0.0039`까지 강화했다.

## 주요 파일

- Clipper1 reference exporter: `adlight_python/scripts/export_clipper1_reference_frames.py`
- Exporter tests: `adlight_python/tests/test_export_clipper1_reference_frames.py`
- Renderer adapter: `clipper_python/plugins/clipper1_video_render/clipper1_video_render/local_render_adapter.py`
- Renderer dependency: `clipper_python/plugins/clipper1_video_render/pyproject.toml`
- Golden fixtures: `clipper_python/tests/fixtures/clipper1_golden_frames`
- Clipper2 baseline fixtures: `clipper_python/tests/fixtures/clipper2_template_baseline_frames`
- Drift diagnostics: `clipper_python/scripts/diagnose_clipper1_golden_frame_drift.py`
- Baseline promotion: `clipper_python/scripts/promote_legacy_template_smoke_baseline.py`

## 검증

- `clipper_python`: `uv run pytest -q`
  - `108 passed, 4 skipped in 88.73s`
- `clipper_python`: `uv run python -m compileall scripts`
  - 통과
- `clipper_python`: `git diff --check`
  - 통과
- `clipper_python`: `uv lock --check`
  - `Resolved 140 packages in 3ms`
- `adlight_python`: `.venv/bin/python -m unittest discover -s tests -p test_export_clipper1_reference_frames.py`
  - `Ran 6 tests ... OK`
- `adlight_python`: `git diff --check`
  - 통과

## 남은 일

- `template-17-16_9`의 content edge drift를 먼저 진단한다.
- 그 다음 `template-14-16_9`, `template-11-16_9`의 공통 content edge 차이를 본다.
- 줄일 수 있는 공통 원인이 있으면 TDD로 보정하고, 그 뒤 `maxMismatchRatio=0.0039`보다 더 낮출 수 있는지 판단한다.
- 25개 fixture 이후 coverage를 더 넓힐지 결정한다.
- reference MP4/thumbnail fixture를 장기적으로 repo에 계속 둘지, 필요하면 경량화할지 판단한다.

## 다음 세션 프롬프트

```text
Using Superpowers.

README.md부터 읽고, .codex/implementation/CLIPPER1_RENDER_PARITY_CHECKPOINT_2026-05-08.md, .codex/implementation/NEXT_SESSION_PROMPT.md, .codex/session-logs 최신 내용을 확인한 뒤 이어서 진행해줘.

현재 legacy Clipper1 template render parity는 25개 Clipper1 reference frame fixture 기준 maxMismatchRatio=0.0039까지 강화됐고, 최신 worst는 template-17-16_9 mismatch 0.0038541666666666668이야. template-6-1_1은 legacy MoviePy/OpenCV auto zoom frame sequence 보정 후 0.00011381172839506173까지 내려갔어.

다음 작업은 template-17-16_9, template-14-16_9, template-11-16_9의 공통 content edge 차이를 진단하고, TDD로 줄일 수 있으면 줄인 뒤 기준을 더 강화하는 거야. 문서화가 필요한 결정/진행은 계속 .codex에 기록하고 세션 로그도 남겨줘. 설명은 한국어로 해줘.
```
