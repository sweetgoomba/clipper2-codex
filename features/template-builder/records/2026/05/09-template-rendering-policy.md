# Template Rendering Policy - 2026-05-09

## 결정

Legacy Clipper1 pixel parity 작업은 현재 기준에서 active optimization target이 아니라 compatibility guard로 전환한다.

- 25개 legacy Clipper1 reference frame fixture 기준은 `channelTolerance=32`, `maxMismatchRatio=0.0006`에서 동결한다.
- 이 fixture는 기존 21개 템플릿을 이미 사용 중인 내부 팀의 영상 출력이 갑자기 바뀌지 않게 막는 회귀 방지 장치다.
- 별도 제품 판단 없이 `maxMismatchRatio`를 더 낮추기 위해 Clipper1의 edge/padding/metric 차이를 계속 추적하지 않는다.
- 새 Template Builder와 Clipper2 modern template renderer의 성공 기준은 `Clipper1과 픽셀 단위로 동일함`이 아니라 `사용자가 보는 preview와 실제 final render가 같은 레이아웃/텍스트/미디어 결과를 냄`이다.

## 배경

기존 Clipper1 템플릿 구현은 Zeplin에서 읽은 디자인 치수를 Pillow, FFmpeg, MoviePy/OpenCV 출력에 맞추기 위해 수동 보정한 값이 많다.

- Pillow text image padding, bbox, font metric 때문에 Zeplin 치수와 실제 렌더 치수가 정확히 일치하지 않는 경우가 있었다.
- 일부 텍스트는 당시 구현 한계로 아래쪽 glyph가 잘리는 등 품질 문제가 있었다.
- 이런 문제까지 Clipper2에서 그대로 복제하면 modern Template Builder의 품질 목표와 충돌한다.

따라서 legacy parity는 운영 호환성의 하한선이고, modern renderer의 설계 목표는 아니다.

## 렌더링 계약

### 1. Legacy Compatibility Guard

대상:

- 기존 Clipper1 built-in template preset
- 기존 프로젝트/내부 팀이 이미 의존하는 legacy-compatible render path
- `clipper_python/tests/fixtures/clipper1_golden_frames`

정책:

- 현재 `0.0006` 기준을 통과해야 한다.
- 기존 출력 안정성을 깨는 변경은 명시적인 migration/versioning 없이 넣지 않는다.
- Clipper1의 known bug를 modern renderer에 복제하기 위한 추가 최적화는 하지 않는다.

### 2. Preview/Final Parity Contract

대상:

- Template Builder에서 사용자가 편집하는 canvas preview
- Template Builder sample render
- published custom template을 적용한 final video render

정책:

- preview와 final render는 같은 normalized template model에서 좌표, 크기, visibility, style, asset reference를 읽어야 한다.
- preview-only CSS 계산과 final-only legacy payload mapping이 따로 drift하지 않게 테스트 경계를 둔다.
- pixel comparison을 쓰더라도 비교 대상은 Clipper1 golden frame이 아니라 같은 Template Builder payload에서 나온 preview frame과 final frame이다.
- video encoding edge noise는 허용하되 layer geometry, text box bounds, asset placement, visibility, color/alpha 같은 의미 있는 차이는 실패시킨다.

### 3. Modern Quality Guard

대상:

- 새 Template Builder 템플릿
- 의도적으로 modernized version으로 승격한 기존 템플릿

정책:

- 텍스트 ascender/descender가 잘리지 않아야 한다.
- line-height, padding, box height, outline/shadow가 glyph bounding box를 침범하지 않아야 한다.
- legacy 템플릿을 개선하려면 silent parity drift가 아니라 별도 template version 또는 modernization decision으로 다룬다.

### 4. Hybrid Text Preview Policy

대상:

- Template Builder preview의 텍스트 레이어
- sample/final renderer가 만드는 deterministic text artifact

정책:

- 사용자가 편집 중일 때 preview를 final renderer 호출에 동기적으로 묶지 않는다.
- 브라우저/CSS 텍스트는 즉시 fallback preview로 유지한다.
- final renderer 기반 텍스트 artifact는 background에서 생성하고, 도착하면 같은 layer frame 안에 PNG로 표시한다.
- artifact 요청이 실패하거나 늦으면 기존 browser preview를 유지한다.
- stale artifact가 잘못 표시되지 않도록 layer/style/text snapshot 기반 cache key나 generation guard를 둔다.
- legacy Clipper1의 glyph clipping bug를 그대로 복제하는 것이 목적이 아니라, modern renderer가 실제로 낼 결과를 preview에 더 가깝게 보여주는 것이 목적이다.

## 다음 우선순위

1. Template Builder preview path와 final render payload/render path를 파일 단위로 inventory한다.
2. 같은 Template Builder variant snapshot에서 preview/final이 공유해야 하는 normalized render contract를 문서화하고 테스트 seam을 정한다.
3. 먼저 geometry/visibility/style payload 일치성 테스트를 추가한다.
4. plain text layer부터 hybrid final-render text artifact preview를 붙인다.
5. 실제 worker cold/warm latency와 stale artifact behavior를 측정한다.
6. 그 다음 가능한 범위에서 subtitle exact artifact와 preview frame/sample-final frame 비교를 추가한다.
