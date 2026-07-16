# AI 숏폼 디렉터 — Programmatic motion과 deterministic preview PoC 설계

작성일: 2026-07-16 KST

상위 설계:

- `.codex/design/PROMPT_SHORTFORM_QUALITY_AND_HYBRID_GENERATION_DIRECTION_2026-07-15.md`
- `.codex/design/SHORTFORM_DIRECTOR_RENDER_RECIPE_COMPILER_FOUNDATION_DESIGN_2026-07-16.md`

## 목적

첫 programmatic primitive인 `diagram.sequence-card.v1`의 화면 구조와 시간 변화를 provider-independent 계약으로 만든다.

```text
VideoPlan programmatic diagram Layer
                 ↓
RenderRecipe overlay.params.programmaticMotion
  ├─ semantic content
  ├─ normalized layout
  ├─ normalized animation phases
  └─ deterministic reference frames
                 ↓
Angular browser preview
```

이번 PoC는 영상 파일을 만들지 않는다. FFmpeg, Python, Remotion, Motion Canvas나 image/video provider를 선택하거나 실행하지 않는다.

후속 상태:

- 초기 PoC의 generic step copy 소유권은 `.codex/design/SHORTFORM_DIRECTOR_DIAGRAM_STEP_COPY_OWNERSHIP_DESIGN_2026-07-16.md`에서 확정했다.
- 새 VideoPlan은 exact step copy를 `Layer.programmaticPayload`로 소유한다.
- 아래 generic `상황/확인/행동`은 payload가 없는 기존 저장 프로젝트에만 적용되는 compiler compatibility fallback이다.

## 별도 preview API를 만들지 않는 이유

현재 owner-scoped RenderRecipe compile endpoint가 이미 side-effect-free preview boundary다.

별도 preview endpoint나 preview 전용 모델을 만들면 다음 두 정본이 생긴다.

- renderer가 소비할 programmatic motion 정보
- Angular가 소비할 preview 정보

따라서 diagram overlay 자체에 `programmaticMotion`을 넣고 Angular가 그대로 소비한다. 향후 renderer adapter도 같은 motion contract를 구현해야 한다.

## 계약

```ts
interface SequenceCardProgrammaticMotionV1 {
  schemaVersion: 'shortform-director-programmatic-motion.v1';
  primitive: 'diagram.sequence-card.v1';
  sampler: 'sequence-card-stagger.v1';
  durationSec: number;
  content: {
    eyebrow: 'SEQUENCE';
    headline: string;
    steps: [
      { id: 'context'; order: 0; label: string },
      { id: 'evidence'; order: 1; label: string },
      { id: 'action'; order: 2; label: string },
    ];
  };
  layout: {
    coordinateSpace: 'normalized';
    stage: { x: 0.08; y: 0.18; width: 0.84; height: 0.64 };
    direction: 'vertical';
  };
  animation: {
    easing: 'cubic-out';
    enter: { start: 0; end: 0.32; stepStagger: 0.08 };
    hold: { start: 0.32; end: 0.82 };
    exit: { start: 0.82; end: 1 };
  };
  referenceFrames: SequenceCardReferenceFrameV1[];
}
```

시간은 Layer 내부의 `0..1` normalized progress다. duration이 바뀌어도 motion 구조는 동일하며 renderer는 `localTime / layerDuration`으로 progress를 계산할 수 있다.

색, 폰트, 그림자, 픽셀 단위 배치는 계약에 넣지 않는다. Angular는 기존 Material semantic token을 사용하고 향후 renderer style adapter는 별도 계약으로 결정한다.

## semantic content

현재 계약:

- Layer `content`를 headline으로 사용한다.
- Layer `programmaticPayload`가 `context → evidence → action` exact step copy를 소유한다.
- compiler는 authored label을 motion `content.steps`로 그대로 전달하고 order만 추가한다.
- payload가 없는 기존 저장 프로젝트에만 `상황 → 확인 → 행동`을 fallback으로 사용한다.
- payload가 존재하지만 malformed면 generic copy로 숨기지 않고 compile error로 중단한다.

## deterministic sampler

sampler는 순수 함수다.

- 입력: motion spec과 normalized progress
- 출력: container, connector, 세 step의 opacity/translate/scale
- easing: `cubic-out`
- 모든 부동소수점 출력은 소수점 4자리로 반올림
- 입력 객체를 변경하지 않음
- 동일 입력은 deep-equal frame을 만듦

reference progress:

```text
start  0.00
reveal 0.24
hold   0.56
exit   0.90
end    1.00
```

reference frame은 향후 renderer 구현이 browser preview와 같은 결과를 내는지 확인하는 conformance fixture 역할도 한다.

## RenderRecipe embedding

programmatic diagram overlay:

```text
tracks.overlays[].params
  schemaVersion: shortform-director-layer-overlay.v1
  primitive: diagram.sequence-card.v1
  ...
  programmaticMotion: SequenceCardProgrammaticMotionV1
```

text overlay에는 `programmaticMotion`을 넣지 않는다.

경로, URL, artifact payload, provider/model 정보, credential은 포함하지 않는다.

## Angular preview

RenderRecipe compile 성공 뒤 지원되는 programmatic motion이 있으면 작은 preview inspector를 표시한다.

- 9:16 canvas 안에서 normalized stage geometry를 적용
- 기본 frame은 `hold`
- `시작 / 공개 / 유지 / 퇴장 / 끝` 기준 프레임을 버튼으로 선택
- 선택한 frame의 container/connector/step state를 그대로 CSS opacity/transform에 적용
- autoplay, timer, audio playback, canvas/WebGL, rendered video는 없음
- renderer/provider 미선정 안내 유지

사용자가 현재 recipe를 만드는 project 상태를 변경하면 기존 recipe와 preview는 함께 무효화된다.

## acceptance

대표 41.2초 recipe의 `layer_value_approval_visual`:

- primitive 1개
- motion duration 6.9초
- headline은 원 Layer content와 일치
- VideoPlan payload에서 온 3개 authored semantic step
- 5개 deterministic reference frame
- start/end는 보이지 않고 hold는 세 step이 모두 보임
- 같은 project snapshot을 두 번 compile하면 motion과 frame이 deep equal
- text overlay에는 motion contract 없음
- Angular에서 hold frame이 기본으로 보이며 frame 선택 시 DOM style이 계약 값으로 변경

## 비범위

- 실제 영상/이미지 preview 생성
- autoplay와 실시간 재생 clock
- renderer/provider 선택 및 adapter
- project artifact staging
- 두 번째 이상의 programmatic primitive와 자유 형식 diagram DSL
- typography/color/style token의 cross-runtime 계약
- BGM/SFX/caption motion
- render operation, queue, retry, persist
- server/Electron 실행, commit/push/deploy
