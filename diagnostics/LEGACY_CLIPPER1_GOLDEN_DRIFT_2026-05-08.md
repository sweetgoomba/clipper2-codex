# Legacy Clipper1 Golden Drift Diagnostics

작성일: 2026-05-08

## 목적

기존 Clipper1 정답 이미지 25개와 현재 Clipper2 legacy renderer 출력의 차이를 case별/영역별로 수치화한다.

실행:

```bash
cd clipper_python
uv run python scripts/diagnose_clipper1_golden_frame_drift.py \
  --fixture-dir tests/fixtures/clipper1_golden_frames \
  --output-root /tmp/clipper1-golden-frame-drift-report \
  --write-diffs top \
  --top-diffs 10
```

초기 결과:

- `caseCount`: 25
- `failedCount`: 0
- worst case: `template-12-16_9`
- worst mismatch ratio: `0.03780864197530864`
- report output:
  - `/tmp/clipper1-golden-frame-drift-report/summary.json`
  - `/tmp/clipper1-golden-frame-drift-report/summary.tsv`
  - `/tmp/clipper1-golden-frame-drift-report/diffs/*.diff.png`

## 초기 상위 mismatch

| rank | case | ratio | worst region |
|---:|---|---:|---|
| 1 | `template-12-16_9` | `0.037809` | top |
| 2 | `template-1-full` | `0.036188` | content |
| 3 | `template-20-16_9` | `0.035125` | top |
| 4 | `template-11-16_9` | `0.034074` | top |
| 5 | `template-13-16_9` | `0.033920` | top |
| 6 | `template-8-16_9` | `0.032151` | top |
| 7 | `template-18-16_9` | `0.031933` | top |
| 8 | `template-16-16_9` | `0.031748` | top |
| 9 | `template-21-16_9` | `0.031713` | top |
| 10 | `template-7-16_9` | `0.031238` | top |

## 해석

전체 mismatch는 현재 허용 기준인 `0.04` 안에 들어온다. 하지만 상위 case 대부분의 worst region이 `top`이다.

`template-12-16_9` 세부 수치:

- 전체 mismatch ratio: `0.037809`
- top region mismatch ratio: `0.102660`
- content region mismatch ratio: `0.000646`
- bottom region mismatch ratio: `0.015384`

따라서 다음 렌더러 수정 후보는 media/content 배치가 아니라 top 영역의 project text와 box 렌더링이다. 특히 PIL text image 생성, 박스 width/height/padding, alpha edge, ffmpeg overlay 이후 인코딩 edge 차이를 우선 조사한다.

## 2026-05-08 13:15 KST 보정 후 결과

수정 내용:

- Clipper2 renderer가 `*_tracking` 음수값을 버리지 않도록 tracking 전용 숫자 parser를 추가했다.
- 박스형 text PNG의 canvas width 계산을 Clipper1 `create_text_image()`처럼 문장 전체 `font.getbbox(line)` 폭 + tracking으로 맞췄다.
- `template-12-16_9` main title PNG 크기를 Clipper1 기준으로 고정했다.
  - `Legacy Clipper1`: `(753, 135)`
  - `Template 12`: `(597, 135)`

실행:

```bash
cd clipper_python
uv run python scripts/diagnose_clipper1_golden_frame_drift.py \
  --fixture-dir tests/fixtures/clipper1_golden_frames \
  --output-root /tmp/clipper1-golden-frame-drift-report-after-title-width \
  --write-diffs top \
  --top-diffs 10
```

결과:

- `caseCount`: 25
- `failedCount`: 0
- worst case: `template-1-full`
- worst mismatch ratio: `0.02767361111111111`
- report output:
  - `/tmp/clipper1-golden-frame-drift-report-after-title-width/summary.json`
  - `/tmp/clipper1-golden-frame-drift-report-after-title-width/summary.tsv`
  - `/tmp/clipper1-golden-frame-drift-report-after-title-width/diffs/*.diff.png`

보정 후 상위 mismatch:

| rank | case | ratio | worst region |
|---:|---|---:|---|
| 1 | `template-1-full` | `0.027674` | content |
| 2 | `template-17-full` | `0.024510` | content |
| 3 | `template-3-16_9` | `0.015185` | top |
| 4 | `template-16-16_9` | `0.015110` | top |
| 5 | `template-6-1_1` | `0.015110` | top |
| 6 | `template-13-16_9` | `0.014581` | top |
| 7 | `template-20-16_9` | `0.014435` | top |
| 8 | `template-10-16_9` | `0.013735` | top |
| 9 | `template-9-16_9` | `0.012944` | top |
| 10 | `template-14-16_9` | `0.012591` | top |

`template-12-16_9` 변화:

- 전체 mismatch ratio: `0.037809 -> 0.011443`
- top region mismatch ratio: `0.102660 -> 0.024770`
- content region mismatch ratio: `0.000646 -> 0.000609`
- bottom region mismatch ratio: `0.015384 -> 0.009549`

해석:

- template-12의 큰 top 영역 차이는 제목 text PNG width/tracking 차이가 주 원인이었다.
- 이제 worst case가 full ratio case의 content 영역으로 이동했다.
- 다음 후보는 `template-1-full`, `template-17-full`의 full layout/content 합성 방식이다.

## 2026-05-08 13:26 KST full ratio overlay 순서 보정 후 결과

수정 내용:

- Clipper2 full 비율 render 순서를 Clipper1과 맞췄다.
- Clipper1 순서: `concat된 비디오 -> layout overlay -> 제목/자막/로고 overlay`.
- 이전 Clipper2 순서: `segment 안에 제목/자막/로고 overlay -> concat -> layout overlay`.
- full layout PNG에는 alpha가 있어, 이전 순서에서는 제목/자막/로고까지 layout에 눌려 어둡게 보였다.

실행:

```bash
cd clipper_python
uv run python scripts/diagnose_clipper1_golden_frame_drift.py \
  --fixture-dir tests/fixtures/clipper1_golden_frames \
  --output-root /tmp/clipper1-golden-frame-drift-report-after-full-layout-order \
  --write-diffs top \
  --top-diffs 10
```

결과:

- `caseCount`: 25
- `failedCount`: 0
- worst case: `template-3-16_9`
- worst mismatch ratio: `0.015185185185185185`
- report output:
  - `/tmp/clipper1-golden-frame-drift-report-after-full-layout-order/summary.json`
  - `/tmp/clipper1-golden-frame-drift-report-after-full-layout-order/summary.tsv`
  - `/tmp/clipper1-golden-frame-drift-report-after-full-layout-order/diffs/*.diff.png`

보정 후 상위 mismatch:

| rank | case | ratio | worst region |
|---:|---|---:|---|
| 1 | `template-3-16_9` | `0.015185` | top |
| 2 | `template-16-16_9` | `0.015110` | top |
| 3 | `template-6-1_1` | `0.015110` | top |
| 4 | `template-13-16_9` | `0.014581` | top |
| 5 | `template-17-full` | `0.014497` | content |
| 6 | `template-20-16_9` | `0.014435` | top |
| 7 | `template-10-16_9` | `0.013735` | top |
| 8 | `template-9-16_9` | `0.012944` | top |
| 9 | `template-14-16_9` | `0.012591` | top |
| 10 | `template-11-16_9` | `0.012010` | top |

full case 변화:

- `template-1-full`: `0.027674 -> 0.011059`
- `template-17-full`: `0.024510 -> 0.014497`

해석:

- full ratio의 큰 content mismatch는 layout overlay 순서가 주 원인이었다.
- 현재 25개 fixture의 worst mismatch가 `0.0152` 수준으로 내려왔다.
- 다음 후보는 `template-3-16_9` top 영역이다. 위치보다는 text/font edge와 layout/encoding edge가 남은 차이로 보인다.

## 2026-05-08 13:54 KST text height reference 보정 후 결과

수정 내용:

- Clipper2의 text height reference character set을 기존 Clipper1 `generate_reference_texts()` 기준으로 맞췄다.
- 이전 Clipper2 reference set이 짧아서 text PNG 안 glyph가 약 3px 낮게 배치됐다.
- `template-3-16_9` main title PNG bbox를 Clipper1 기준 `(2, 5, 531, 90)`으로 고정했다.

실행:

```bash
cd clipper_python
uv run python scripts/diagnose_clipper1_golden_frame_drift.py \
  --fixture-dir tests/fixtures/clipper1_golden_frames \
  --output-root /tmp/clipper1-golden-frame-drift-report-after-text-height-reference \
  --write-diffs top \
  --top-diffs 10
```

결과:

- `caseCount`: 25
- `failedCount`: 0
- worst case: `template-17-full`
- worst mismatch ratio: `0.012880015432098765`
- `template-3-16_9`: `0.015185 -> 0.007126`

## 2026-05-08 13:59 KST template-17 full pan 방향 pinning 후 결과

수정 내용:

- 기존 Clipper1 reference 영상의 `template-17-full`은 image pan 방향이 `right_to_left`로 생성됐다.
- Clipper2의 deterministic auto pan은 같은 media path에서 `left_to_right`를 골라 첫 프레임의 흰 원이 약 8px 오른쪽으로 밀렸다.
- recipe `effects[].params.fit/travelPx/offsetPx`를 LocalRenderAdapter가 읽도록 하고, `template-17-full.recipe.json`에 `fit=height`, `direction=right_to_left`, `travelPx=8`, `offsetPx=416`을 명시했다.

실행:

```bash
cd clipper_python
uv run python scripts/diagnose_clipper1_golden_frame_drift.py \
  --fixture-dir tests/fixtures/clipper1_golden_frames \
  --output-root /tmp/clipper1-golden-frame-drift-report-after-template17-pan-pin \
  --write-diffs top \
  --top-diffs 10
```

결과:

- `caseCount`: 25
- `failedCount`: 0
- worst case: `template-6-1_1`
- worst mismatch ratio: `0.011948302469135802`
- `template-17-full`: `0.012880 -> 0.005683`

보정 후 상위 mismatch:

| rank | case | ratio | worst region |
|---:|---|---:|---|
| 1 | `template-6-1_1` | `0.011948` | content |
| 2 | `template-16-16_9` | `0.009687` | top |
| 3 | `template-11-16_9` | `0.009001` | top |
| 4 | `template-13-16_9` | `0.008393` | top |
| 5 | `template-14-16_9` | `0.008144` | top |
| 6 | `template-15-16_9` | `0.007994` | top |
| 7 | `template-20-16_9` | `0.007971` | top |
| 8 | `template-12-16_9` | `0.007373` | top |
| 9 | `template-3-16_9` | `0.007126` | top |
| 10 | `template-7-16_9` | `0.007070` | top |

해석:

- 현재 상위 mismatch는 기존 큰 layout/text position drift가 아니라 zoom/resize 보간, 글자 edge, 인코딩 edge 차이에 가깝다.
- 다음 후보는 `template-6-1_1` content 영역이다. Clipper1의 MoviePy/Pillow zoom pipeline과 Clipper2 FFmpeg zoom/resize pipeline을 비교한다.

## 2026-05-08 14:12 KST fixture 기준 강화

판단:

- 사용자가 직접 `template-6-1_1` reference/current/diff를 확인했을 때 육안 차이가 거의 없었다.
- diff도 큰 layout drift가 아니라 원 가장자리, text edge, 색상 경계선 주변에 몰려 있다.
- 따라서 현재 단계에서는 픽셀을 더 맞추는 코드 수정보다, 지금까지 줄인 drift가 다시 커지지 않도록 비교 기준을 강화하는 것이 더 안전하다.

변경:

- `clipper1_golden_frames/manifest.json`의 25개 case `maxMismatchRatio`: `0.04 -> 0.015`
- `adlight_python/scripts/export_clipper1_reference_frames.py` 기본 `DEFAULT_MAX_MISMATCH_RATIO`: `0.04 -> 0.015`
- `clipper_python/tests/test_clipper1_video_render_golden_frames.py`에 checked-in fixture threshold test 추가

검증:

```bash
cd clipper_python
uv run pytest tests/test_clipper1_video_render_golden_frames.py -q
```

결과:

- `2 passed`
- 25개 Clipper1 answer frame case가 `maxMismatchRatio=0.015` 기준으로 통과한다.

## 2026-05-08 14:28 KST zoom resize filter 보정 후 결과

수정 내용:

- Clipper1 zoom path의 MoviePy `resize` effect는 OpenCV가 있으면 upsize에 `cv2.INTER_LINEAR`를 사용한다.
- Clipper2 FFmpeg zoom branch의 scale 단계에 `flags=bilinear`를 추가했다.
- `template-6-1_1` content 영역의 원 edge mismatch가 소폭 줄었다.

실행:

```bash
cd clipper_python
uv run python scripts/diagnose_clipper1_golden_frame_drift.py \
  --fixture-dir tests/fixtures/clipper1_golden_frames \
  --output-root /tmp/clipper1-golden-frame-drift-report-after-zoom-bilinear \
  --write-diffs top \
  --top-diffs 10
```

결과:

- `caseCount`: 25
- `failedCount`: 0
- worst case: `template-6-1_1`
- worst mismatch ratio: `0.01086226851851852`
- `template-6-1_1`: `0.011948 -> 0.010862`

보정 후 상위 mismatch:

| rank | case | ratio | worst region |
|---:|---|---:|---|
| 1 | `template-6-1_1` | `0.010862` | content |
| 2 | `template-16-16_9` | `0.009687` | top |
| 3 | `template-11-16_9` | `0.009001` | top |
| 4 | `template-13-16_9` | `0.008393` | top |
| 5 | `template-14-16_9` | `0.008144` | top |
| 6 | `template-15-16_9` | `0.007994` | top |
| 7 | `template-20-16_9` | `0.007971` | top |
| 8 | `template-12-16_9` | `0.007373` | top |
| 9 | `template-3-16_9` | `0.007126` | top |
| 10 | `template-7-16_9` | `0.007070` | top |

해석:

- 현재 worst는 여전히 `template-6-1_1`이지만 tightened threshold `0.015`보다 충분히 낮다.
- 다음 후보는 content geometry가 아니라 top text edge mismatch가 남은 `template-16-16_9`, `template-11-16_9`이다.

## 2026-05-08 14:45 KST legacy overlay format 보정 후 결과

판단:

- 기존 Clipper1 `VideoService.py`의 FFmpeg overlay filter는 `overlay=x:y` 형태를 쓰고 `format=auto`를 지정하지 않는다.
- Clipper2는 layout/logo/text PNG overlay에 `format=auto`를 붙이고 있었고, `template-16-16_9`의 반투명 subtitle box edge와 `template-11-16_9`의 outline/text edge mismatch가 여기서 크게 발생했다.

수정:

- layout/media, logo, text overlay filter에서 `format=auto`를 제거했다.
- full ratio의 final layout/text/logo overlay 경로도 같은 방식으로 맞췄다.
- renderer 출력이 의도적으로 바뀌었으므로 `clipper2_template_baseline_frames` 25개 frame을 다시 생성했다.
- 전체 worst가 `0.012` 아래로 들어온 상태라 `clipper1_golden_frames/manifest.json`과 exporter 기본 `maxMismatchRatio`를 `0.015 -> 0.012`로 강화했다.

실행:

```bash
cd clipper_python
uv run python scripts/diagnose_clipper1_golden_frame_drift.py \
  --fixture-dir tests/fixtures/clipper1_golden_frames \
  --output-root /tmp/clipper1-golden-frame-drift-report-after-legacy-overlay-format \
  --write-diffs top \
  --top-diffs 10
```

결과:

- `caseCount`: 25
- `failedCount`: 0
- worst case: `template-6-1_1`
- worst mismatch ratio: `0.011861496913580247`
- `template-11-16_9`: `0.009001 -> 0.003457`
- `template-16-16_9`: `0.009687 -> 0.006590`
- `template-12-16_9`: `0.007373 -> 0.003382`
- `template-1-full`: `0.011059 -> 0.000573`
- `template-17-full`: `0.005683 -> 0.001541`

보정 후 상위 mismatch:

| rank | case | ratio | worst region |
|---:|---|---:|---|
| 1 | `template-6-1_1` | `0.011861` | content |
| 2 | `template-16-4_3` | `0.006740` | top |
| 3 | `template-18-16_9` | `0.006653` | top |
| 4 | `template-16-16_9` | `0.006590` | top |
| 5 | `template-14-16_9` | `0.006551` | top |
| 6 | `template-15-16_9` | `0.006447` | top |
| 7 | `template-17-16_9` | `0.005795` | top |
| 8 | `template-6-16_9` | `0.004315` | content |
| 9 | `template-9-16_9` | `0.003513` | top |
| 10 | `template-21-16_9` | `0.003488` | content |

해석:

- `template-11`, `template-16`, full ratio 계열의 남은 edge mismatch는 legacy overlay format 보정으로 크게 줄었다.
- 이 시점의 전체 worst는 다시 `template-6-1_1` content edge이며, 기준 `0.012` 바로 아래였다.

## 2026-05-08 15:07 KST automatic zoom scale/crop 보정 후 결과

수정 내용:

- 기존 Clipper1 automatic zoom path는 먼저 source image를 content area 크기로 맞추고, 그 결과 clip을 시간에 따라 다시 확대/축소한다.
- Clipper2의 automatic zoom branch는 `zoompan` 단일 단계였기 때문에 `template-6-1_1` 첫 프레임의 원 edge 보간이 Clipper1 reference와 조금 달랐다.
- FFmpeg filter를 2단계로 바꿨다.
  - 1단계: `fps -> scale(... force_original_aspect_ratio=increase:flags=bilinear) -> crop`으로 content 크기 normalize
  - 2단계: `t * fps` 기반 legacy zoom factor로 frame별 scale 후 중앙 crop
- zoom frame count denominator는 Clipper1 `Zoom`처럼 `int(duration * fps)`를 쓰고, 최소 1로 clamp한다.
- renderer 출력이 의도적으로 바뀌었으므로 `clipper2_template_baseline_frames` 25개 frame을 다시 생성했다.
- 전체 worst가 `0.008` 아래로 들어온 상태라 `clipper1_golden_frames/manifest.json`과 exporter 기본 `maxMismatchRatio`를 `0.012 -> 0.008`로 강화했다.

실행:

```bash
cd clipper_python
uv run python scripts/diagnose_clipper1_golden_frame_drift.py \
  --fixture-dir tests/fixtures/clipper1_golden_frames \
  --output-root /tmp/clipper1-golden-frame-drift-report-after-zoom-scale-crop \
  --write-diffs top \
  --top-diffs 10
```

결과:

- `caseCount`: 25
- `failedCount`: 0
- worst case: `template-6-1_1`
- worst mismatch ratio: `0.0069791666666666665`
- `template-6-1_1`: `0.011861 -> 0.006979`

보정 후 상위 mismatch:

| rank | case | ratio | worst region |
|---:|---|---:|---|
| 1 | `template-6-1_1` | `0.006979` | content |
| 2 | `template-16-4_3` | `0.006740` | top |
| 3 | `template-18-16_9` | `0.006653` | top |
| 4 | `template-16-16_9` | `0.006590` | top |
| 5 | `template-14-16_9` | `0.006551` | top |
| 6 | `template-15-16_9` | `0.006447` | top |
| 7 | `template-17-16_9` | `0.005795` | top |
| 8 | `template-6-16_9` | `0.004315` | content |
| 9 | `template-9-16_9` | `0.003513` | top |
| 10 | `template-21-16_9` | `0.003488` | content |

해석:

- `template-6-1_1`의 남은 content mismatch는 절반 가까이 줄었다.
- 현재 기준 `maxMismatchRatio=0.008`에서는 25개 case가 모두 통과한다.
- 다음 기준 강화 전에는 상위 top edge 케이스가 실제 text 위치 drift인지, 아니면 edge/encoding noise인지 먼저 확인한다.

## 2026-05-08 15:31 KST x264 ultrafast preset 보정 후 결과

수정 내용:

- 기존 Clipper1 `VideoService.py`의 MoviePy `write_videofile()` 경로는 `preset='ultrafast'`, `codec='libx264'`를 사용한다.
- Clipper2 renderer는 `libx264`만 지정하고 x264 preset을 지정하지 않았다.
- segment render와 full-ratio final layout overlay encoding에 `-preset ultrafast`를 추가했다.
- renderer 출력이 의도적으로 바뀌었으므로 `clipper2_template_baseline_frames` 25개 frame을 다시 생성했다.
- 기준은 기존 `maxMismatchRatio=0.008`을 유지한다.

실행:

```bash
cd clipper_python
uv run python scripts/diagnose_clipper1_golden_frame_drift.py \
  --fixture-dir tests/fixtures/clipper1_golden_frames \
  --output-root /tmp/clipper1-golden-frame-drift-report-after-x264-ultrafast \
  --write-diffs top \
  --top-diffs 10
```

결과:

- `caseCount`: 25
- `failedCount`: 0
- worst case: `template-6-1_1`
- worst mismatch ratio: `0.0070119598765432094`

보정 후 상위 mismatch:

| rank | case | ratio | worst region |
|---:|---|---:|---|
| 1 | `template-6-1_1` | `0.007012` | content |
| 2 | `template-16-4_3` | `0.006553` | top |
| 3 | `template-14-16_9` | `0.006534` | top |
| 4 | `template-18-16_9` | `0.006534` | top |
| 5 | `template-16-16_9` | `0.006476` | top |
| 6 | `template-15-16_9` | `0.006345` | top |
| 7 | `template-17-16_9` | `0.005926` | top |
| 8 | `template-6-16_9` | `0.004701` | content |
| 9 | `template-4-16_9` | `0.003536` | top |
| 10 | `template-9-16_9` | `0.003513` | top |

해석:

- x264 preset 보정은 top edge 상위 케이스를 소폭 줄였다.
- `template-6-1_1`은 `0.006979 -> 0.007012`로 아주 조금 올라갔지만 여전히 `maxMismatchRatio=0.008` 안이다.
- 이 결과는 남은 top mismatch가 큰 위치 drift라기보다 text/image edge와 encoding 차이에 가깝다는 증거다.

## 2026-05-08 15:50 KST text height reference `므` 보정 후 결과

수정 내용:

- 기존 Clipper1 `generate_reference_texts()`의 `으` 계열 row는 `그느드르므브스으즈츠크트프흐`다.
- 현재 Clipper2 renderer의 `LEGACY_TEXT_HEIGHT_REFERENCE`는 같은 위치가 `그느드르무브스으즈츠크트프흐`였다.
- 평균 글자 높이 계산 기준은 text PNG 세로 배치에 영향을 줄 수 있으므로, Clipper1과 같은 `므` 기준으로 보정했다.
- renderer 출력이 의도적으로 바뀔 수 있으므로 `clipper2_template_baseline_frames` 25개 frame을 다시 생성했다.
- 기준은 기존 `maxMismatchRatio=0.008`을 유지한다.

TDD:

- RED: `test_legacy_text_height_reference_includes_clipper1_eu_row`가 `missing_chars == ['므']`로 실패했다.
- GREEN: `LEGACY_TEXT_HEIGHT_REFERENCE` 보정 후 focused test와 template style tests가 통과했다.

실행:

```bash
cd clipper_python
uv run python scripts/diagnose_clipper1_golden_frame_drift.py \
  --fixture-dir tests/fixtures/clipper1_golden_frames \
  --output-root /tmp/clipper1-golden-frame-drift-report-after-text-reference-mu \
  --write-diffs top \
  --top-diffs 10
```

결과:

- `caseCount`: 25
- `failedCount`: 0
- worst case: `template-6-1_1`
- worst mismatch ratio: `0.0070119598765432094`

보정 후 상위 mismatch:

| rank | case | ratio | worst region |
|---:|---|---:|---|
| 1 | `template-6-1_1` | `0.007012` | content |
| 2 | `template-16-4_3` | `0.006553` | top |
| 3 | `template-14-16_9` | `0.006534` | top |
| 4 | `template-18-16_9` | `0.006534` | top |
| 5 | `template-16-16_9` | `0.006476` | top |
| 6 | `template-15-16_9` | `0.006345` | top |
| 7 | `template-17-16_9` | `0.005926` | top |
| 8 | `template-6-16_9` | `0.004701` | content |
| 9 | `template-4-16_9` | `0.003536` | top |
| 10 | `template-9-16_9` | `0.003513` | top |

해석:

- 이 보정은 Clipper1 기준 데이터와 맞추는 correctness fix다.
- 현재 25개 fixture에서는 x264 ultrafast 보정 후 수치와 동일하게 유지됐다.
- 다음 기준 강화 전에는 `template-6-1_1` content edge와 top edge 상위 케이스를 더 분리해야 한다.

## 2026-05-08 16:05 KST automatic zoom source preprocessing 보정 후 결과

수정 내용:

- 기존 Clipper1 `_apply_zoom_effect()`는 자동 zoom 전에 source image를 content area 크기로 리사이즈/중앙 crop한다.
- RGB 이미지이면 그 중간 이미지를 `.jpg`로 저장한 뒤 MoviePy `ImageClip`으로 다시 읽고 zoom을 적용한다.
- Clipper2 renderer는 원본 PNG를 바로 ffmpeg scale/crop chain에 넣고 있었고, `template-6-1_1`의 hard color-band edge에서 차이가 났다.
- `motion_effect.summary.source == "auto"`인 image zoom에만 Clipper1식 중간 source image를 만들도록 보정했다.
- explicit recipe zoom은 기존 동작을 유지한다.
- renderer 출력이 의도적으로 바뀌었으므로 `clipper2_template_baseline_frames` 25개 frame을 다시 생성했다.
- 전체 worst가 `0.007` 아래로 들어왔으므로 `clipper1_golden_frames/manifest.json`과 exporter 기본 `maxMismatchRatio`를 `0.008 -> 0.007`로 강화했다.

TDD:

- RED: `test_automatic_zoom_uses_legacy_preprocessed_image_source`가 원본 `still.png`를 그대로 ffmpeg 입력으로 써서 실패했다.
- GREEN: automatic zoom source preprocessing 구현 후 focused test와 media looping tests가 통과했다.
- RED: golden/export threshold tests가 기존 `0.008` 기준 때문에 실패했다.
- GREEN: manifest와 export default를 `0.007`로 갱신한 뒤 focused tests가 통과했다.

실행:

```bash
cd clipper_python
uv run python scripts/diagnose_clipper1_golden_frame_drift.py \
  --fixture-dir tests/fixtures/clipper1_golden_frames \
  --output-root /tmp/clipper1-golden-frame-drift-report-after-autozoom-preprocess-threshold007 \
  --write-diffs top \
  --top-diffs 10
```

결과:

- `caseCount`: 25
- `failedCount`: 0
- worst case: `template-6-1_1`
- worst mismatch ratio: `0.006558641975308642`
- `template-6-1_1`: `0.007012 -> 0.006559`

보정 후 상위 mismatch:

| rank | case | ratio | worst region |
|---:|---|---:|---|
| 1 | `template-6-1_1` | `0.006559` | content |
| 2 | `template-16-4_3` | `0.006553` | top |
| 3 | `template-14-16_9` | `0.006534` | top |
| 4 | `template-18-16_9` | `0.006534` | top |
| 5 | `template-16-16_9` | `0.006476` | top |
| 6 | `template-15-16_9` | `0.006345` | top |
| 7 | `template-17-16_9` | `0.005926` | top |
| 8 | `template-6-16_9` | `0.004701` | content |
| 9 | `template-4-16_9` | `0.003536` | top |
| 10 | `template-9-16_9` | `0.003513` | top |

해석:

- `template-6-1_1` content edge는 줄었지만, `template-16-4_3` top edge와 거의 붙어 있다.
- 현재 기준은 `maxMismatchRatio=0.007`이다.
- 다음 기준 강화 전에는 top edge 상위 케이스의 text/image edge를 더 줄여야 한다.

## 2026-05-08 16:23 KST text height zero-glyph 평균 보정 후 결과

수정 내용:

- 기존 Clipper1 `get_average_text_height()`는 기준 문자별 bbox height를 그대로 평균낸다.
- 현재 Clipper2 `_average_text_height()`는 `height > 0`인 문자만 평균에 넣고 있었다.
- 일부 폰트, 특히 `template-16`의 `SCDream8.otf`에서는 zero-height glyph가 있어 평균 높이가 달라졌고, main title PNG glyph가 기존 Clipper1보다 1px 위에 그려졌다.
- zero-height glyph filtering을 제거해 Clipper1과 같은 평균 계산으로 맞췄다.
- renderer 출력이 의도적으로 바뀌었으므로 `clipper2_template_baseline_frames` 25개 frame을 다시 생성했다.
- 전체 top edge drift가 줄어 `clipper1_golden_frames/manifest.json`과 exporter 기본 `maxMismatchRatio`를 `0.007 -> 0.0067`로 강화했다.

TDD:

- RED: `test_template_16_main_titles_include_zero_height_reference_glyphs`가 `bbox top 3 != 4`로 실패했다.
- GREEN: `_average_text_height()` 보정 후 focused test와 기존 template-3 placement test가 통과했다.
- RED: golden/export threshold tests가 기존 `0.007` 기준 때문에 실패했다.
- GREEN: manifest와 export default를 `0.0067`로 갱신한 뒤 focused tests가 통과했다.

실행:

```bash
cd clipper_python
uv run python scripts/diagnose_clipper1_golden_frame_drift.py \
  --fixture-dir tests/fixtures/clipper1_golden_frames \
  --output-root /tmp/clipper1-golden-frame-drift-report-after-average-height-zero-glyphs-threshold0067 \
  --write-diffs top \
  --top-diffs 10
```

결과:

- `caseCount`: 25
- `failedCount`: 0
- worst case: `template-6-1_1`
- worst mismatch ratio: `0.006558641975308642`
- `template-16-4_3`: `0.006553 -> 0.003434`
- `template-14-16_9`: `0.006534 -> 0.003546`
- `template-18-16_9`: `0.006534 -> 0.003447`
- `template-16-16_9`: `0.006476 -> 0.003289`

보정 후 상위 mismatch:

| rank | case | ratio | worst region |
|---:|---|---:|---|
| 1 | `template-6-1_1` | `0.006559` | content |
| 2 | `template-6-16_9` | `0.004701` | content |
| 3 | `template-17-16_9` | `0.003935` | content |
| 4 | `template-14-16_9` | `0.003546` | content |
| 5 | `template-9-16_9` | `0.003513` | top |
| 6 | `template-18-16_9` | `0.003447` | content |
| 7 | `template-16-4_3` | `0.003434` | content |
| 8 | `template-11-16_9` | `0.003412` | content |
| 9 | `template-21-16_9` | `0.003391` | content |
| 10 | `template-12-16_9` | `0.003328` | content |

해석:

- top title edge drift는 크게 줄었다.
- 현재 기준은 `maxMismatchRatio=0.0067`이다.
- 다음 기준 강화 전에는 `template-6-1_1` 또는 `template-6-16_9` content edge를 더 줄여야 한다.

## 다음 작업 후보

## 2026-05-08 17:09 KST automatic zoom fast_bilinear 보정 후 결과

수정 내용:

- `template-6-1_1` mismatch는 콘텐츠 내부의 주황/파랑, 파랑/청록 hard edge row와 흰 원 edge에 집중돼 있었다.
- 기존 Clipper1의 MoviePy `resize.py`는 현재 설치 환경에서 OpenCV `cv2.INTER_LINEAR`를 사용한다.
- Clipper2 FFmpeg zoom branch의 `flags=bilinear`보다 `flags=fast_bilinear`가 해당 edge를 더 가깝게 만들었다.
- automatic/explicit zoom branch의 두 scale 단계 flag를 `fast_bilinear`로 바꿨다.
- renderer 출력이 의도적으로 바뀌었으므로 `clipper2_template_baseline_frames` 25개 frame을 다시 생성했다.
- `clipper1_golden_frames/manifest.json`과 exporter 기본 `maxMismatchRatio`를 `0.0067 -> 0.0065`로 강화했다.

TDD:

- RED: `test_automatic_zoom_uses_legacy_scale_crop_resize_filter`가 filter graph에 `flags=fast_bilinear`가 없어 실패했다.
- GREEN: zoom branch 보정 후 focused test와 golden fixture test가 통과했다.

실행:

```bash
cd clipper_python
uv run python scripts/diagnose_clipper1_golden_frame_drift.py \
  --fixture-dir tests/fixtures/clipper1_golden_frames \
  --output-root /tmp/clipper1-golden-frame-drift-report-after-fast-bilinear \
  --write-diffs top \
  --top-diffs 10
```

결과:

- `caseCount`: 25
- `failedCount`: 0
- worst case: `template-6-1_1`
- worst mismatch ratio: `0.006354166666666667`
- `template-6-1_1`: `0.006559 -> 0.006354`

보정 후 상위 mismatch:

| rank | case | ratio | worst region |
|---:|---|---:|---|
| 1 | `template-6-1_1` | `0.006354` | content |
| 2 | `template-6-16_9` | `0.004701` | content |
| 3 | `template-17-16_9` | `0.003935` | content |
| 4 | `template-14-16_9` | `0.003546` | content |
| 5 | `template-9-16_9` | `0.003513` | top |
| 6 | `template-18-16_9` | `0.003447` | content |
| 7 | `template-16-4_3` | `0.003434` | content |
| 8 | `template-11-16_9` | `0.003412` | content |
| 9 | `template-21-16_9` | `0.003391` | content |
| 10 | `template-12-16_9` | `0.003328` | content |

해석:

- `template-6-1_1` content edge drift는 소폭 줄었고, checked-in 기준은 `maxMismatchRatio=0.0065`다.
- `template-6-16_9`가 2위지만 `0.004701`이라 기준과는 거리가 있다.
- 다음 기준 강화 전에는 `template-6` 계열 content edge에서 남은 보간/encoding 차이를 더 분리한다.

## 다음 작업 후보

## 2026-05-08 17:32 KST legacy final re-encode 보정 후 결과

수정 내용:

- 기존 Clipper1 `_create_final_video()`는 클립이 하나여도 최종 단계에서 `concat=n=1:v=1:a=0`, `format=yuv420p`, `libx264`, `profile high`, `level 4.0`, `x264opts level=4.0:ref=3:bframes=3`를 거친다.
- 현재 Clipper2 `_concat_segments()`는 단일 segment를 파일 복사했고, 여러 segment도 `-c copy` concat을 사용했다.
- 이 때문에 Clipper1 reference에는 있는 최종 재인코딩 edge가 Clipper2 output에는 없었다.
- `_concat_segments()`를 segment 수와 무관하게 Clipper1식 final concat/filter/x264 encode 경로로 변경했다.
- renderer 출력이 의도적으로 바뀌었으므로 `clipper2_template_baseline_frames` 25개 frame을 다시 생성했다.
- `clipper1_golden_frames/manifest.json`과 exporter 기본 `maxMismatchRatio`를 `0.0065 -> 0.0064`로 강화했다.

TDD:

- RED: `test_concat_segments_reencodes_single_clip_with_legacy_final_x264_options`가 `adapter.commands[0]` 없음으로 실패했다.
- GREEN: `_concat_segments()` 보정 후 focused test와 golden fixture test가 통과했다.
- RED: threshold test가 manifest의 기존 `0.0065` 때문에 실패했다.
- GREEN: manifest와 export default를 `0.0064`로 갱신한 뒤 focused tests가 통과했다.

실행:

```bash
cd clipper_python
uv run python scripts/diagnose_clipper1_golden_frame_drift.py \
  --fixture-dir tests/fixtures/clipper1_golden_frames \
  --output-root /tmp/clipper1-golden-frame-drift-report-after-final-reencode \
  --write-diffs top \
  --top-diffs 10
```

결과:

- `caseCount`: 25
- `failedCount`: 0
- worst case: `template-6-1_1`
- worst mismatch ratio: `0.006317515432098766`
- `template-6-1_1`: `0.006354 -> 0.006318`
- `template-6-16_9`: `0.004701 -> 0.003358`

보정 후 상위 mismatch:

| rank | case | ratio | worst region |
|---:|---|---:|---|
| 1 | `template-6-1_1` | `0.006318` | content |
| 2 | `template-17-16_9` | `0.003854` | content |
| 3 | `template-14-16_9` | `0.003490` | content |
| 4 | `template-11-16_9` | `0.003441` | content |
| 5 | `template-9-16_9` | `0.003399` | top |
| 6 | `template-18-16_9` | `0.003383` | content |
| 7 | `template-16-4_3` | `0.003368` | content |
| 8 | `template-6-16_9` | `0.003358` | content |
| 9 | `template-16-16_9` | `0.003343` | content |
| 10 | `template-21-16_9` | `0.003316` | content |

해석:

- Clipper1 final encode stage를 맞추면서 `template-6-16_9`는 상위권에서 크게 내려갔다.
- `template-6-1_1`은 여전히 worst지만 checked-in 기준은 `maxMismatchRatio=0.0064`까지 강화됐다.
- 다음 기준 강화 전에는 `template-6-1_1`의 흰 원 edge와 horizontal color edge를 더 분리한다.

## 다음 작업 후보

1. `template-6-1_1` content edge에서 남은 resize/encoding 차이를 더 줄인다.
2. `template-17-16_9`, `template-14-16_9`의 content edge가 공통 인코딩 계열인지 확인한다.
3. 다음 기준 강화는 새 worst를 줄인 뒤 검토한다.

## 2026-05-08 17:52 KST legacy MoviePy/OpenCV auto-zoom frame sequence 보정 후 결과

수정 내용:

- `template-6-1_1`의 큰 잔여 mismatch는 content hard edge row에 몰려 있었다.
- 기존 Clipper1 `_apply_zoom_effect()`는 FFmpeg scale/crop이 아니라 MoviePy `ImageClip` + OpenCV `cv2.INTER_LINEAR` resize로 30fps full-frame segment를 먼저 만든다.
- Clipper2도 automatic image zoom에서 content-area preprocessed source를 만든 뒤, layout/white background 위에 30fps frame sequence를 생성하고 `ultrafast` segment encode를 수행하도록 맞췄다.
- renderer 출력이 의도적으로 바뀌었으므로 `clipper2_template_baseline_frames` 25개 frame을 다시 생성했다.
- `clipper1_golden_frames/manifest.json`과 exporter 기본 `maxMismatchRatio`를 `0.0064 -> 0.0039`로 강화했다.

TDD:

- RED: `test_automatic_zoom_renders_legacy_moviepy_frame_sequence`가 `-framerate 30` frame sequence input을 찾지 못해 실패했다.
- GREEN: auto image zoom frame sequence 경로 구현 후 focused tests와 media looping suite가 통과했다.
- RED: golden threshold test가 manifest의 기존 `0.0064` 때문에 실패했다.
- GREEN: manifest와 export default를 `0.0039`로 갱신한 뒤 focused tests가 통과했다.

실행:

```bash
cd clipper_python
uv run python scripts/diagnose_clipper1_golden_frame_drift.py \
  --fixture-dir tests/fixtures/clipper1_golden_frames \
  --output-root /tmp/clipper1-golden-frame-drift-report-after-legacy-cv2-autozoom-threshold0039 \
  --write-diffs top \
  --top-diffs 10
```

결과:

- `caseCount`: 25
- `failedCount`: 0
- worst case: `template-17-16_9`
- worst mismatch ratio: `0.0038541666666666668`
- `template-6-1_1`: `0.006318 -> 0.000114`

보정 후 상위 mismatch:

| rank | case | ratio | worst region |
|---:|---|---:|---|
| 1 | `template-17-16_9` | `0.003854` | content |
| 2 | `template-14-16_9` | `0.003490` | content |
| 3 | `template-11-16_9` | `0.003441` | content |
| 4 | `template-9-16_9` | `0.003399` | top |
| 5 | `template-18-16_9` | `0.003383` | content |
| 6 | `template-16-4_3` | `0.003368` | content |
| 7 | `template-6-16_9` | `0.003358` | content |
| 8 | `template-16-16_9` | `0.003343` | content |
| 9 | `template-21-16_9` | `0.003316` | content |
| 10 | `template-7-16_9` | `0.003291` | content |

해석:

- 이전 worst였던 `template-6-1_1`은 사실상 해결됐다.
- 새 기준은 `maxMismatchRatio=0.0039`다.
- 다음 기준 강화 전에는 `template-17-16_9`, `template-14-16_9`, `template-11-16_9` 등에 공통으로 남은 content edge를 분리한다.

## 2026-05-09 17:01 KST RAQM line width + automatic pan frame sequence 보정 후 결과

수정 내용:

- 현재 `clipper_python` uv 환경의 Pillow는 RAQM이 꺼져 있어 legacy Clipper1 venv와 text line bbox width가 달랐다.
- `uharfbuzz` shaped advance fallback으로 RAQM 없는 환경에서도 legacy `font.getbbox(line)` 중심 정렬 폭을 재현했다.
- 16:9 square source image는 auto zoom이 아니라 vertical auto pan 경로를 탄다.
- automatic image pan도 기존 Clipper1 MoviePy/OpenCV 방식처럼 30fps full-frame sequence를 먼저 만든 뒤 segment encode하도록 보정했다.

실행:

```bash
cd clipper_python
uv run python scripts/diagnose_clipper1_golden_frame_drift.py \
  --fixture-dir tests/fixtures/clipper1_golden_frames \
  --output-root /tmp/clipper1-golden-frame-drift-20260509-after-auto-pan-sequence \
  --write-diffs none
```

결과:

- `caseCount`: 25
- `failedCount`: 0
- worst case: `template-21-16_9`
- worst mismatch ratio: `0.0024286265432098765`
- checked-in 기준: `maxMismatchRatio=0.0025`

주요 target:

- `template-17-16_9`: `0.0038541666666666668 -> 0.0005690586419753086`
- `template-14-16_9`: `0.0005189043209876544`
- `template-11-16_9`: `0.0002642746913580247`

해석:

- 요청된 세 케이스의 공통 content edge는 automatic pan을 legacy frame sequence로 바꾸면서 대부분 제거됐다.
- 남은 worst는 content가 아니라 `template-21-16_9`, `template-6-16_9` 계열의 top text edge다.

## 2026-05-09 18:20 KST Paperlogy glyph cursor 보정 후 결과

수정 내용:

- RAQM line bbox fallback이 total advance만 사용하던 문제를 보정했다.
  - `Paperlogy-8ExtraBold.ttf`, 92px, `Template 21`, tracking `-4.6`에서 legacy line width는 `555.0`인데 기존 fallback은 `554.0`이었다.
  - 첫 glyph의 negative left bearing을 반영해 legacy `font.getbbox(line)` 폭과 맞췄다.
- 현재 Pillow/FreeType 조합은 Paperlogy `a` glyph bbox width를 legacy보다 1px 넓게 잡는다.
  - legacy cursor width: `a == 58`
  - current cursor width: `a == 59`
  - Paperlogy title에만 scoped compensation을 적용했다.
- SEBANG outline title에서는 같은 보정을 적용하면 `l` cursor가 `23 -> 22`로 줄어 regression이 생겨, Paperlogy scope guard를 추가했다.

실행:

```bash
cd clipper_python
uv run python scripts/diagnose_clipper1_golden_frame_drift.py \
  --fixture-dir tests/fixtures/clipper1_golden_frames \
  --output-root /tmp/clipper1-golden-frame-drift-20260509-paperlogy-scoped-all \
  --write-diffs top \
  --top-diffs 10
```

결과:

- `caseCount`: 25
- `failedCount`: 0
- worst case: `template-17-16_9`
- worst mismatch ratio: `0.0005690586419753086`
- checked-in 기준: `maxMismatchRatio=0.0006`

상위 mismatch:

| rank | case | mismatch | worst region |
| --- | --- | ---: | --- |
| 1 | `template-17-16_9` | `0.000569` | top |
| 2 | `template-12-16_9` | `0.000563` | top |
| 3 | `template-14-16_9` | `0.000519` | top |
| 4 | `template-19-16_9` | `0.000484` | top |
| 5 | `template-3-16_9` | `0.000332` | top |

주요 target:

- `template-21-16_9`: `0.0024286265432098765 -> 0.00017361111111111112`
- `template-6-16_9`: `0.001979166666666667 -> 0.00013310185185185185`
- `template-6-1_1`: `0.0014409722222222222 -> 0.00011381172839506173`
- `template-11-16_9`: Paperlogy scope guard 후 `0.0002642746913580247` 유지

해석:

- `template-21/6` 계열의 남은 top text edge는 Paperlogy cursor metric 차이였고, 보정 후 더 이상 기준을 지배하지 않는다.
- 최신 worst는 다시 `template-17/12/14/19` 계열의 top text edge다.
