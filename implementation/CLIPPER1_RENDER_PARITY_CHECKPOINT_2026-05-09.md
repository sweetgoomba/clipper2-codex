# Clipper1 Render Parity Checkpoint - 2026-05-09

작성 시각: 2026-05-09 17:01 KST
최신 갱신: 2026-05-09 18:20 KST
정책 갱신: 2026-05-09

## 현재 상태

Legacy Clipper1 template render parity는 25개 Clipper1 reference frame fixture 기준 `channelTolerance=32`, `maxMismatchRatio=0.0006`까지 강화됐다.

2026-05-09 정책 전환으로 이 기준은 더 이상 active optimization target이 아니라 legacy compatibility guard로 동결한다. 남은 top text edge를 `0.0004` 이하로 줄이기 위한 추가 픽셀 튜닝은 진행하지 않는다. 새 우선순위는 Template Builder preview와 final render가 같은 결과를 내도록 만드는 preview/final parity다. 상세 정책은 `.codex/implementation/TEMPLATE_RENDERING_POLICY_2026-05-09.md`를 따른다.

이번 세션 시작 시 현재 `uv` 환경의 Pillow가 RAQM 없이 동작하면서 top/bottom text edge가 크게 벌어져 25개 golden 비교가 깨졌다. 기존 Clipper1 venv는 Pillow RAQM/Harfbuzz가 켜져 있었고, Clipper2 uv 환경은 RAQM이 없었다. 이를 `uharfbuzz` 기반 line width fallback으로 보정했다.

이후 `template-17-16_9`, `template-14-16_9`, `template-11-16_9`의 공통 content edge는 auto pan 경로가 원인이었다. 16:9 square media는 auto zoom이 아니라 vertical auto pan을 타는데, Clipper2는 아직 FFmpeg scale/crop 근사를 쓰고 있었다. 기존 Clipper1은 MoviePy/OpenCV로 30fps frame sequence를 먼저 만들기 때문에, Clipper2 auto pan도 같은 frame sequence 경로로 맞췄다.

추가로 남은 worst였던 `template-21-16_9`, `template-6-16_9`, `template-6-1_1` top text edge는 Paperlogy title glyph cursor 차이가 원인이었다. RAQM line bbox fallback이 첫 glyph의 negative left bearing을 놓쳤고, 현재 Pillow/FreeType 조합은 Paperlogy `a` glyph bbox width를 legacy보다 1px 넓게 잡았다. Paperlogy에만 scoped glyph cursor compensation을 적용해 다른 outline font regression을 피했다.

## 수치

최신 진단 command:

```bash
cd clipper_python
uv run python scripts/diagnose_clipper1_golden_frame_drift.py \
  --fixture-dir tests/fixtures/clipper1_golden_frames \
  --output-root /tmp/clipper1-golden-frame-drift-20260509-paperlogy-scoped-all \
  --write-diffs none
```

결과:

- `caseCount`: 25
- `failedCount`: 0
- latest worst: `template-17-16_9`
- latest worst mismatch: `0.0005690586419753086`
- 기준: `maxMismatchRatio=0.0006`

주요 target 변화:

- `template-21-16_9`: `0.0024286265432098765 -> 0.00017361111111111112`
- `template-6-16_9`: `0.001979166666666667 -> 0.00013310185185185185`
- `template-6-1_1`: `0.0014409722222222222 -> 0.00011381172839506173`
- `template-17-16_9`: `0.0038541666666666668 -> 0.0005690586419753086`
- `template-14-16_9`: `0.003546대 -> 0.0005189043209876544`
- `template-11-16_9`: `0.003457대 -> 0.0002642746913580247`

## 변경

- `clipper_python/plugins/clipper1_video_render/clipper1_video_render/local_render_adapter.py`
  - Pillow RAQM이 없는 환경에서 `uharfbuzz` shaped advance로 legacy RAQM line bbox width를 재현한다.
  - RAQM line bbox fallback에 negative left bearing을 반영한다.
  - Paperlogy title glyph cursor width를 legacy Pillow/FreeType metric에 맞춘다.
  - automatic image pan도 legacy MoviePy/OpenCV 방식처럼 30fps full-frame sequence를 만든 뒤 segment encode한다.
- `clipper_python/plugins/clipper1_video_render/pyproject.toml`
  - `uharfbuzz` dependency 추가.
- `clipper_python/tests/test_clipper1_video_render_template_styles.py`
  - RAQM 없는 환경의 legacy line width, negative left bearing, Paperlogy glyph cursor regression 추가.
- `clipper_python/tests/test_clipper1_video_render_media_looping.py`
  - automatic pan frame sequence regression 추가.
- `clipper_python/tests/fixtures/clipper1_golden_frames/manifest.json`
  - `maxMismatchRatio`를 `0.0006`으로 강화.
- `clipper_python/tests/fixtures/clipper2_template_baseline_frames`
  - intentional render output change에 맞춰 baseline frame 재생성.
- `adlight_python/scripts/export_clipper1_reference_frames.py`
  - default `maxMismatchRatio`를 `0.0006`으로 강화.

## 검증

완료:

- RED: `test_legacy_line_bbox_width_matches_raqm_centering_without_pillow_raqm`가 `463.0 != 454`로 실패.
- GREEN: 같은 focused test 통과.
- RED: `test_automatic_pan_renders_legacy_moviepy_frame_sequence`가 `-framerate` 없음으로 실패.
- GREEN: 같은 focused test 통과.
- RED: `test_legacy_line_bbox_width_includes_negative_raqm_left_bearing`가 `554.0 != 555.0`으로 실패.
- GREEN: 같은 focused test 통과.
- RED: `test_legacy_glyph_width_matches_raqm_cursor_without_pillow_raqm`가 `59.0 != 58.0`으로 실패.
- RED: `test_legacy_glyph_width_compensation_does_not_shift_sebang_outline_titles`가 `22.0 != 23.0`으로 실패한 뒤 Paperlogy scope로 제한.
- GREEN: text metric focused tests와 `tests/test_clipper1_video_render_template_styles.py` 통과.
- `clipper_python uv run python scripts/diagnose_clipper1_golden_frame_drift.py --fixture-dir tests/fixtures/clipper1_golden_frames --output-root /tmp/clipper1-golden-frame-drift-20260509-paperlogy-scoped-all --write-diffs top --top-diffs 10`
  - `25 cases`, `failed 0`, worst `template-17-16_9` `0.0005690586419753086`
- `clipper_python uv run pytest tests/test_clipper1_video_render_golden_frames.py tests/test_clipper2_template_baseline_frames.py -q`
  - `4 passed in 56.53s`
- `clipper_python uv run pytest tests/test_clipper1_video_render_golden_frames.py tests/test_clipper2_template_baseline_frames.py tests/test_clipper1_video_render_media_looping.py tests/test_clipper1_video_render_template_styles.py -q`
  - `49 passed in 56.17s`
- `adlight_python venv310/bin/python -m unittest discover -s tests -p test_export_clipper1_reference_frames.py`
  - `Ran 6 tests ... OK`
- `clipper_python uv run pytest -q`
  - `113 passed, 4 skipped in 93.71s`
- `clipper_python uv run python -m compileall scripts`
  - 통과
- `clipper_python uv lock --check`
  - `Resolved 141 packages in 4ms`
- `clipper_python git diff --check`
  - 통과
- `adlight_python git diff --check`
  - 통과

## 다음 작업

- Legacy Clipper1 golden frame fixture는 `maxMismatchRatio=0.0006` compatibility guard로 유지한다.
- 다음 구현 우선순위는 Template Builder preview/final parity다.
- 먼저 Template Builder canvas preview, sample render, published/final render payload mapping 경로를 inventory하고, 같은 variant snapshot에서 geometry/visibility/style이 preview와 final에 동일하게 전달되는 테스트 경계를 만든다.
