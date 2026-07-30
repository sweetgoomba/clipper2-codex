# AI 숏폼 디렉터 시각 구성 품질 보완 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 모든 신규 장면이 실제 기본 시각 소재를 갖게 하고, 내부 매체 선택 이유가 화면에 노출되지 않으며, 도식이 비교·순서·루프·수치 목적에 맞는 레이아웃으로 렌더되게 한다.

**Architecture:** Web API의 `scene-media-decision` 응답을 단일 medium에서 `baseMedium + overlayMode`로 바꾸고, Desktop Nest가 이를 기존 VideoPlan의 다중 Layer로 컴파일한다. 신규 `diagram.semantic-card.v1`은 공통 motion 상태를 쓰되 variant별 Motion Canvas 레이아웃을 구분하며, 기존 `diagram.sequence-card.v1`은 저장 프로젝트 호환을 위해 유지한다.

**Tech Stack:** NestJS 11/Jest(OpenAI structured output), NestJS 11/TypeScript/node:test(VideoPlan·RenderRecipe·AssetPack), Motion Canvas 3.17/Vite, Angular 19/Jasmine

## Global Constraints

- 문서와 구현은 `.codex` 및 각 실제 코드 레포에만 두며 `clipper_docs`에는 추가하지 않는다.
- 기존 완료 영상·프로젝트 JSON·MP4를 수정하거나 삭제하지 않는다.
- 신규 provider, 모델 변경, 크레딧 차감, 환경변수 직접 삽입을 추가하지 않는다.
- 외부 provider 라이브 호출은 사용자 비용 승인 없이 실행하지 않는다.
- `decision.rationale`은 감사 데이터로만 남고 모든 최종 표시 문자열에서 제외한다.
- 신규 장면은 `official-source|image-search|generated-image|generated-video` 기본 시각 Layer를 반드시 하나 가진다.
- 도식과 kinetic typography는 기본 시각 소재를 대체하지 않는 overlay다.
- programmatic diagram은 `ceil(sceneCount / 3)`개 이하이며 연속 장면에 배치할 수 없다.
- 기존 `diagram.sequence-card.v1` 경로와 저장 프로젝트 호환을 유지한다.
- 각 태스크는 실패 테스트 확인, 최소 구현, 관련 테스트 통과, 독립 커밋 순서로 끝낸다.

---

## 파일 구조

### Web API

- `web/clipper_web_api/src/modules/shortform-director-inference/domain/shortform-director-inference.contract.ts`
  - v3 structured response schema와 manual validator의 단일 정본
- `web/clipper_web_api/src/modules/shortform-director-inference/application/shortform-director-inference.prompt.ts`
  - base visual·overlay·전체 영상 다양성 지시
- 기존 colocated spec
  - schema, validator, prompt, OpenAI transport의 실제 경계 검증

### Desktop Nest

- `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-inference-response.projector.ts`
  - Web API v3 응답의 안전한 projection
- `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-candidate-plan.compiler.ts`
  - base visual, optional diagram, text Layer 생성과 전체 장면 guard
- `desktop/clipper_nestjs/src/modules/shortform-director/domain/shortform-director.model.ts`
  - semantic diagram VideoPlan payload
- `desktop/clipper_nestjs/src/modules/shortform-director/domain/video-plan-contract.ts`
  - 저장 계약 validation
- `desktop/clipper_nestjs/src/modules/shortform-director/domain/programmatic-motion.ts`
  - provider-independent semantic card motion
- `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-render-recipe.compiler.ts`
  - semantic payload를 RenderRecipe overlay로 투영
- `desktop/clipper_nestjs/src/modules/shortform-director/domain/renderer-conformance.ts`
  - 신규 primitive 지원 여부 검증
- 기존 node:test
  - candidate compiler, Web API client projection, VideoPlan, RenderRecipe, conformance 검증

### Motion Canvas

- `desktop/clipper_nestjs/tools/shortform-director-motion-canvas-poc/src/recipe-projection.mjs`
  - semantic card projection
- `desktop/clipper_nestjs/tools/shortform-director-motion-canvas-poc/src/motion-sampler.ts`
  - generic item stagger sampler
- `desktop/clipper_nestjs/tools/shortform-director-motion-canvas-poc/src/render-state.ts`
  - semantic card projection type
- `desktop/clipper_nestjs/tools/shortform-director-motion-canvas-poc/src/scenes/director.tsx`
  - comparison·sequence·loop·metric layout
- `desktop/clipper_nestjs/test/shortform-director-motion-canvas-poc.test.js`
  - 실제 projection 결과 검증

### Angular

- `desktop/clipper_angular/src/features/shortform-director/models/shortform-director-project.ts`
  - 저장된 semantic payload와 motion union
- 기존 sequence preview spec
  - legacy preview 타입·동작 불변 검증

---

### Task 1: Web API 장면 미디어 결정 계약 v3

**Files:**

- Modify: `web/clipper_web_api/src/modules/shortform-director-inference/domain/shortform-director-inference.contract.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-inference/domain/shortform-director-inference.contract.spec.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-inference/application/shortform-director-inference.prompt.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-inference/application/shortform-director-inference.prompt.spec.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-inference/infrastructure/openai-shortform-director-inference.transport.spec.ts`

**Interfaces:**

- Produces:

```ts
interface SceneMediaDecisionV3 {
  sceneIndex: number;
  baseMedium:
    | 'official-source'
    | 'image-search'
    | 'generated-image'
    | 'generated-video';
  overlayMode: 'none' | 'kinetic-typography' | 'programmatic-diagram';
  rationale: string;
  factualRisk: 'low' | 'medium' | 'high';
  evidenceIds: string[];
  productionSourceIds: string[];
  searchBrief: string | null;
  generationBrief: string | null;
  programmaticBrief: {
    variant: 'comparison' | 'sequence' | 'loop' | 'metric';
    labels: string[];
    values: number[] | null;
  } | null;
}
```

- [ ] **Step 1: v3 출력 모양과 조건 검증의 실패 테스트 작성**

`validOutputs['scene-media-decision']`을 다음 모양으로 바꾸고, 별도 테스트에서 잘못된 조건을 거부한다.

```ts
{
  decisions: [{
    sceneIndex: 0,
    baseMedium: 'image-search',
    overlayMode: 'programmatic-diagram',
    rationale: '실제 제품 위에 두 선택지를 비교한다.',
    factualRisk: 'low',
    evidenceIds: ['evidence-1'],
    productionSourceIds: [],
    searchBrief: '2026 실제 제품 세로 이미지',
    generationBrief: null,
    programmaticBrief: {
      variant: 'comparison',
      labels: ['선택 A', '선택 B'],
      values: null,
    },
  }],
}
```

검증할 실패:

- `baseMedium`이 없는 구형 응답
- image search인데 `searchBrief=null`
- generated media인데 `generationBrief=null`
- diagram인데 `programmaticBrief=null`
- non-diagram인데 brief가 존재
- comparison label이 2개가 아님
- sequence label이 2~4개가 아님
- loop label이 3~5개가 아님
- metric values가 labels와 같은 개수가 아님

- [ ] **Step 2: 테스트가 기존 단일 medium 계약 때문에 실패하는지 확인**

Run:

```bash
cd /Users/jina/project/adlight/web/clipper_web_api
npm test -- --runInBand shortform-director-inference.contract.spec.ts shortform-director-inference.prompt.spec.ts openai-shortform-director-inference.transport.spec.ts
```

Expected: v3 fixture가 schema/manual validation에서 거부되고 prompt version 기대가 실패한다.

- [ ] **Step 3: schema와 manual validator를 v3으로 최소 변경**

`medium`과 `fallbackMedium`을 제거하고 `baseMedium`, `overlayMode`를 required로 둔다. `programmaticBrief`는 `variant`, `labels`, `values`만 허용하며 variant별 배열 길이와 metric 값 개수를 manual validator에서 검증한다.

- [ ] **Step 4: prompt를 v3으로 올리고 base/overlay 규칙 명시**

prompt version을 `shortform-director.scene-media-decision.v3`으로 올리고 다음 동작을 지시한다.

```text
Every scene must have one base visual.
Diagram and kinetic typography are overlays and never replace the base visual.
Use official-source or image-search for identifiable current people, artists,
products, and events. Use generated media only for conceptual visuals.
Across the whole video, use at most ceil(sceneCount / 3) diagram overlays and
never place diagrams in consecutive scenes.
The rationale is internal audit text and must not be reused as viewer-facing copy.
```

- [ ] **Step 5: transport fixture를 v3으로 바꾸고 관련 테스트 통과 확인**

Run:

```bash
cd /Users/jina/project/adlight/web/clipper_web_api
npm test -- --runInBand shortform-director-inference.contract.spec.ts shortform-director-inference.prompt.spec.ts openai-shortform-director-inference.transport.spec.ts
npm run build
```

Expected: 관련 Jest spec과 TypeScript build 통과.

- [ ] **Step 6: Web API 계약 변경 커밋**

```bash
git add src/modules/shortform-director-inference
git commit -m "feat(shortform-director): separate scene base visuals and overlays"
```

---

### Task 2: Desktop v3 projection과 VideoPlan 다중 Layer 컴파일

**Files:**

- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-inference-response.projector.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-candidate-plan.compiler.ts`
- Modify: `desktop/clipper_nestjs/test/shortform-director-web-api-clients.test.js`
- Modify: `desktop/clipper_nestjs/test/shortform-director-candidate-production.test.js`

**Interfaces:**

- Consumes: `SceneMediaDecisionV3`
- Produces: 장면마다 base visual Layer 1개, optional programmatic Layer 0~1개, text Layer 1개

- [ ] **Step 1: 내부 rationale 노출과 빈 base visual을 재현하는 실패 테스트 작성**

candidate compiler 테스트 입력에 다음 결정을 사용한다.

```js
{
  sceneIndex: 0,
  baseMedium: 'image-search',
  overlayMode: 'programmatic-diagram',
  rationale: '비교 도식이 정보를 가장 명확하게 전달합니다.',
  factualRisk: 'low',
  evidenceIds: ['evidence-1'],
  productionSourceIds: [],
  searchBrief: '실제 대상 세로 이미지',
  generationBrief: null,
  programmaticBrief: {
    variant: 'comparison',
    labels: ['기존 방식', '개선 방식'],
    values: null,
  },
}
```

다음을 literal로 검증한다.

```js
assert.equal(scene.beats[0].intent, '검증 가능한 주장');
assert.deepEqual(
  scene.beats[0].shots[0].layers.map((layer) => layer.assetStrategy),
  ['search', 'programmatic', 'programmatic'],
);
assert.equal(
  scene.beats[0].shots[0].layers.some(
    (layer) => layer.content.includes('가장 명확하게 전달합니다'),
  ),
  false,
);
assert.equal(
  scene.beats[0].shots[0].layers.find((layer) => layer.role === 'diagram').content,
  '화면 문구',
);
```

- [ ] **Step 2: 도식 상한과 연속 배치 guard의 실패 테스트 작성**

5개 장면 중 diagram 3개인 입력과 diagram이 index 1, 2에 연속된 입력이 각각 `ShortformDirectorCandidatePlanCompilerError`를 던지는지 검증한다. 5개 장면에서 diagram 2개이면서 비연속이면 통과해야 한다.

- [ ] **Step 3: Desktop 관련 테스트가 구형 projector/compiler 때문에 실패하는지 확인**

Run:

```bash
cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/shortform-director-web-api-clients.test.js test/shortform-director-candidate-production.test.js
```

Expected: v3 필드가 projector exact-key validation 또는 compiler에서 거부되고 Layer 기대가 실패한다.

- [ ] **Step 4: projector를 v3 exact contract로 변경**

`baseMedium`, `overlayMode`를 enum validation하고 old `medium`, `fallbackMedium`은 신규 응답에서 거부한다. Web API와 같은 조건부 brief 검증을 유지한다.

- [ ] **Step 5: compiler를 base + optional overlay + text로 변경**

```ts
const layers = [
  baseVisualLayerFor(context, decision.baseMedium),
  ...(decision.overlayMode === 'programmatic-diagram'
    ? [diagramLayerFor(context)]
    : []),
  textLayerFor(
    context,
    decision.overlayMode === 'kinetic-typography'
      ? 'kinetic_text'
      : 'caption',
  ),
];
```

diagram `content`는 `scene.onScreenText[0] ?? scene.claim`, beat `intent`는 `scene.claim`을 사용한다. `decision.rationale`은 inference artifact에만 남긴다.

- [ ] **Step 6: 전체 장면 guard 구현**

compile 입력 validation에서 diagram index 목록을 구하고:

```ts
const maximum = Math.ceil(videoPlan.scenes.length / 3);
```

보다 많으면 거부하며, 정렬된 index의 인접 차이가 1이면 거부한다.

- [ ] **Step 7: 관련 Desktop 테스트와 build 통과 확인**

Run:

```bash
cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/shortform-director-web-api-clients.test.js test/shortform-director-candidate-production.test.js
```

Expected: 관련 node:test 통과.

- [ ] **Step 8: Desktop v3 compiler 커밋**

```bash
git add src/modules/shortform-director/application/shortform-director-inference-response.projector.ts \
  src/modules/shortform-director/application/shortform-director-candidate-plan.compiler.ts \
  test/shortform-director-web-api-clients.test.js \
  test/shortform-director-candidate-production.test.js
git commit -m "feat(shortform-director): compile visual bases with overlays"
```

---

### Task 3: Semantic diagram VideoPlan·RenderRecipe 계약

**Files:**

- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/domain/shortform-director.model.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/domain/video-plan-contract.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/domain/programmatic-motion.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-candidate-plan.compiler.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-render-recipe.compiler.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/domain/renderer-conformance.ts`
- Modify: `desktop/clipper_nestjs/test/shortform-director-video-plan.test.js`
- Modify: `desktop/clipper_nestjs/test/shortform-director-render-recipe-compiler.test.js`
- Modify: `desktop/clipper_nestjs/test/shortform-director-renderer-conformance.test.js`

**Interfaces:**

- Produces:

```ts
interface VideoPlanDiagramSemanticCardContentV1 {
  schemaVersion: 'diagram-semantic-card-content.v1';
  primitive: 'diagram.semantic-card.v1';
  variant: 'comparison' | 'sequence' | 'loop' | 'metric';
  items: Array<{ id: string; label: string; value?: number }>;
}
```

- [ ] **Step 1: semantic payload 저장·검증 실패 테스트 작성**

VideoPlan 테스트에 comparison, sequence, loop, metric payload를 하나씩 넣어 통과 기대를 만들고 다음 invalid case를 거부한다.

- comparison item 3개
- loop item 2개
- metric item에 value 누락
- non-metric item에 value 존재
- 빈 label과 중복 id

기존 sequence-card fixture가 계속 통과하는 assertion을 유지한다.

- [ ] **Step 2: semantic motion exact copy 실패 테스트 작성**

RenderRecipe compiler에 metric payload:

```js
{
  schemaVersion: 'diagram-semantic-card-content.v1',
  primitive: 'diagram.semantic-card.v1',
  variant: 'metric',
  items: [
    { id: 'metric-1', label: '완료율', value: 92 },
    { id: 'metric-2', label: '재시도', value: 3 },
  ],
}
```

를 넣고 `params.programmaticMotion.content.headline`, `variant`, `items`가 exact copy인지 검증한다. headline에는 media rationale이 아니라 Layer `content` literal만 있어야 한다.

- [ ] **Step 3: 기존 domain이 semantic primitive를 거부하는 RED 확인**

Run:

```bash
cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/shortform-director-video-plan.test.js test/shortform-director-render-recipe-compiler.test.js test/shortform-director-renderer-conformance.test.js
```

Expected: semantic payload 또는 motion primitive unsupported 실패.

- [ ] **Step 4: semantic payload domain과 validator 구현**

variant별 item 수와 value 규칙을 순수 validator로 구현하고 `VideoPlanLayer.programmaticPayload`를 legacy sequence와 semantic card union으로 확장한다.

- [ ] **Step 5: deterministic semantic motion builder 구현**

기존 sequence sampler의 enter/hold/exit와 reference progress를 재사용하되 다음 content를 보존한다.

```ts
content: {
  eyebrow: 'COMPARE' | 'SEQUENCE' | 'LOOP' | 'METRIC';
  headline: string;
  variant: SemanticDiagramVariant;
  items: Array<{ id: string; order: number; label: string; value?: number }>;
}
```

- [ ] **Step 6: candidate compiler와 RenderRecipe compiler 연결**

`programmaticBrief.labels/values`를 variant별 stable item id와 exact label/value로 변환한다. RenderRecipe overlay primitive는 `diagram.semantic-card.v1`, styleRef는 `shortform-director.programmatic.diagram.semantic-card.v1`로 만든다.

- [ ] **Step 7: renderer conformance에 semantic capability 추가**

Motion Canvas adapter capability에 `shortform-director.motion.diagram-semantic-card.v1`을 추가하고 malformed variant/item motion을 fail-closed로 거부한다. 기존 sequence capability는 유지한다.

- [ ] **Step 8: 관련 domain/compiler/conformance 테스트 통과 확인**

Run:

```bash
cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/shortform-director-video-plan.test.js test/shortform-director-render-recipe-compiler.test.js test/shortform-director-renderer-conformance.test.js test/shortform-director-candidate-production.test.js
```

Expected: 신규 semantic과 legacy sequence 테스트 모두 통과.

- [ ] **Step 9: semantic 계약 커밋**

```bash
git add src/modules/shortform-director/domain \
  src/modules/shortform-director/application/shortform-director-candidate-plan.compiler.ts \
  src/modules/shortform-director/application/shortform-director-render-recipe.compiler.ts \
  test/shortform-director-video-plan.test.js \
  test/shortform-director-render-recipe-compiler.test.js \
  test/shortform-director-renderer-conformance.test.js \
  test/shortform-director-candidate-production.test.js
git commit -m "feat(shortform-director): add semantic diagram motion"
```

---

### Task 4: Motion Canvas variant별 실제 레이아웃

**Files:**

- Modify: `desktop/clipper_nestjs/tools/shortform-director-motion-canvas-poc/src/recipe-projection.mjs`
- Modify: `desktop/clipper_nestjs/tools/shortform-director-motion-canvas-poc/src/motion-sampler.ts`
- Modify: `desktop/clipper_nestjs/tools/shortform-director-motion-canvas-poc/src/render-state.ts`
- Modify: `desktop/clipper_nestjs/tools/shortform-director-motion-canvas-poc/src/scenes/director.tsx`
- Modify: `desktop/clipper_nestjs/test/shortform-director-motion-canvas-poc.test.js`

**Interfaces:**

- Consumes: RenderRecipe overlay `primitive='diagram.semantic-card.v1'`
- Produces: `projection.semanticCards[]`와 variant별 Motion Canvas layout

- [ ] **Step 1: projection의 semantic card 보존 실패 테스트 작성**

4개 overlay를 가진 hand-authored recipe를 만들어 projection 결과가 다음 literal variant 순서를 보존하는지 검증한다.

```js
assert.deepEqual(
  projection.semanticCards.map((card) => card.motion.content.variant),
  ['comparison', 'sequence', 'loop', 'metric'],
);
```

malformed metric value와 unsupported variant도 projection에서 거부해야 한다.

- [ ] **Step 2: 기존 projection이 신규 primitive를 거부하는 RED 확인**

Run:

```bash
cd /Users/jina/project/adlight/desktop/clipper_nestjs
node --test test/shortform-director-motion-canvas-poc.test.js
```

Expected: `Unsupported Director overlay primitive` 실패.

- [ ] **Step 3: recipe projection과 sampler 확장**

`semanticCards` 배열을 추가하고 schema/primitive/variant/items/layout/animation을 검증한다. item animation은 `sampleSemanticCardMotion()`이 order 기반 opacity, translate, scale을 반환한다.

- [ ] **Step 4: variant별 전용 레이아웃 구현**

`director.tsx`에서 하나의 `addSemanticCard`가 variant별 작은 렌더 함수에 위임한다.

```ts
switch (card.motion.content.variant) {
  case 'comparison': return addComparisonLayout(...);
  case 'sequence': return addSequenceLayout(...);
  case 'loop': return addLoopLayout(...);
  case 'metric': return addMetricLayout(...);
}
```

레이아웃 불변식:

- comparison: 동일 폭 좌우 카드 2개
- sequence: 세로 번호·연결선, 2~4 item
- loop: 중앙 공간을 둔 원형 위치, 3~5 item
- metric: 큰 숫자와 라벨, 1~3 tile

화면 headline은 motion content만 사용하고 renderer가 새 설명문을 만들지 않는다.

- [ ] **Step 5: projection 테스트와 Motion Canvas Vite build 통과 확인**

Run:

```bash
cd /Users/jina/project/adlight/desktop/clipper_nestjs
node --test test/shortform-director-motion-canvas-poc.test.js
npm --prefix tools/shortform-director-motion-canvas-poc run build
```

Expected: node:test와 Vite production build 통과.

- [ ] **Step 6: Motion Canvas 구현 커밋**

```bash
git add tools/shortform-director-motion-canvas-poc/src \
  test/shortform-director-motion-canvas-poc.test.js
git commit -m "feat(shortform-director): render semantic diagram variants"
```

---

### Task 5: Angular 저장 계약 호환

**Files:**

- Modify: `desktop/clipper_angular/src/features/shortform-director/models/shortform-director-project.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/sequence-card-preview/sequence-card-preview.component.spec.ts`

**Interfaces:**

- Consumes: legacy sequence payload/motion과 신규 semantic payload/motion union
- Produces: Angular compile 시 신규 저장 recipe를 안전하게 역직렬화할 타입

- [ ] **Step 1: semantic type fixture를 추가해 RED 확인**

model을 import하는 기존 spec에 다음 `satisfies` fixture를 추가한다.

```ts
const semanticMotion = {
  schemaVersion: 'shortform-director-programmatic-motion.v1',
  primitive: 'diagram.semantic-card.v1',
  sampler: 'semantic-card-stagger.v1',
  durationSec: 5,
  content: {
    eyebrow: 'COMPARE',
    headline: '두 방식의 차이',
    variant: 'comparison',
    items: [
      { id: 'item-1', order: 0, label: '기존' },
      { id: 'item-2', order: 1, label: '개선' },
    ],
  },
  layout: {
    coordinateSpace: 'normalized',
    stage: { x: 0.08, y: 0.18, width: 0.84, height: 0.64 },
  },
  animation: {
    easing: 'cubic-out',
    enter: { start: 0, end: 0.32, itemStagger: 0.08 },
    hold: { start: 0.32, end: 0.82 },
    exit: { start: 0.82, end: 1 },
  },
  referenceFrames: [],
} satisfies ShortformDirectorSemanticCardProgrammaticMotion;
```

- [ ] **Step 2: Angular type check가 type 부재로 실패하는지 확인**

Run:

```bash
cd /Users/jina/project/adlight/desktop/clipper_angular
npm test -- --watch=false --include='src/features/shortform-director/components/sequence-card-preview/sequence-card-preview.component.spec.ts'
```

Expected: semantic motion/payload type 부재로 compile 실패.

- [ ] **Step 3: legacy와 semantic union 타입 추가**

기존 `ShortformDirectorDiagramSequenceCardContent`와 sequence motion을 변경하지 않고 semantic payload/motion interface를 추가한다. 소비 타입만 union으로 확장한다.

- [ ] **Step 4: 관련 테스트와 Angular build 통과 확인**

Run:

```bash
cd /Users/jina/project/adlight/desktop/clipper_angular
npm test -- --watch=false --include='src/features/shortform-director/components/sequence-card-preview/sequence-card-preview.component.spec.ts'
npm run build
```

Expected: 기존 sequence preview와 Angular build 통과.

- [ ] **Step 5: Angular 호환 타입 커밋**

```bash
git add src/features/shortform-director/models/shortform-director-project.ts \
  src/features/shortform-director/components/sequence-card-preview/sequence-card-preview.component.spec.ts
git commit -m "feat(shortform-director): accept semantic diagram recipes"
```

---

### Task 6: 통합 회귀와 품질 게이트

**Files:**

- Modify if required by failing integration only:
  - `desktop/clipper_nestjs/test/shortform-director-candidate-production.test.js`
  - `desktop/clipper_nestjs/test/shortform-director-render-input-stage.test.js`
  - `desktop/clipper_nestjs/test/shortform-director-motion-canvas-render-integration.test.js`

**Interfaces:**

- Verifies: v3 response → base visual requirement → asset readiness → RenderRecipe → Motion Canvas projection

- [ ] **Step 1: 신규 candidate의 시각 요구사항 coverage 통합 테스트 작성**

5개 장면의 v3 결정을 compiler에 넣고 다음을 검증한다.

```js
assert.equal(assetPack.requirements.filter((item) => (
  item.strategy === 'source'
  || item.strategy === 'search'
  || item.strategy === 'generated-image'
  || item.strategy === 'generated-video'
)).length, 5);
assert.equal(assetPack.productionReadiness.status, 'waiting');
```

하나 이상의 base binding을 제거한 상태에서 render input staging이 거부되는지도 검증한다.

- [ ] **Step 2: 기존 경로가 coverage를 보장하지 못해 실패하는 RED 확인**

Run:

```bash
cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/shortform-director-candidate-production.test.js test/shortform-director-render-input-stage.test.js test/shortform-director-motion-canvas-render-integration.test.js
```

Expected: 누락된 통합 연결 또는 stale fixture가 있으면 명시적인 assertion에서 실패한다.

- [ ] **Step 3: 통합 실패만 최소 수정**

v3 field rename으로 남은 fixture와 projection 경계를 갱신한다. AssetPack readiness 또는 staging이 이미 누락 binding을 차단하면 production gate를 중복 추가하지 않는다.

- [ ] **Step 4: 세 레포 관련 테스트·빌드 실행**

Web API:

```bash
cd /Users/jina/project/adlight/web/clipper_web_api
npm test -- --runInBand
npm run build
```

Desktop Nest:

```bash
cd /Users/jina/project/adlight/desktop/clipper_nestjs
npm run build
node --test test/shortform-director-*.test.js
npm --prefix tools/shortform-director-motion-canvas-poc run build
```

Angular:

```bash
cd /Users/jina/project/adlight/desktop/clipper_angular
npm test -- --watch=false
npm run build
```

Expected: 전부 exit code 0. 외부 provider 호출은 0회.

- [ ] **Step 5: git diff와 저장소 상태 검토**

각 레포에서:

```bash
git diff --check
git status --short
git log -5 --oneline
```

모든 변경이 이 설계의 인수 조건에 연결되는지 확인한다. 예상 밖 사용자 변경은 커밋하지 않는다.

- [ ] **Step 6: 통합 보정이 있을 때만 별도 커밋**

```bash
git add test/shortform-director-candidate-production.test.js \
  test/shortform-director-render-input-stage.test.js \
  test/shortform-director-motion-canvas-render-integration.test.js
git commit -m "test(shortform-director): cover visual composition pipeline"
```

- [ ] **Step 7: 라이브 재검증 준비 상태 보고**

코드·fixture 검증 결과, 새 앱 빌드 필요 여부, 기존 두 프로젝트에서 재사용 가능한 단계, 실제 Naver/Gemini 예상 호출 수와 비용 승인 경계를 사용자에게 보고한다. 승인 전에는 라이브 호출하지 않는다.
