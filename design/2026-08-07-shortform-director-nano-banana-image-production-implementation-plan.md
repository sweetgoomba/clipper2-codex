# Shortform Director Nano Banana 2 이미지 제작 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** AI 숏폼 디렉터에서 Nano Banana 2로 1:1·1K 이미지를 약 2.5~3초 간격의 컷별로 생성하고, 기존 Clipper 기본 1:1 템플릿·TTS·자막·타이틀·렌더 큐로 최종 영상을 만든다.

**Architecture:** 기존 AI 영상 설정과 작업은 그대로 유지하고, 상위 생성 미디어 설정에서 `generated-video`와 `generated-image`를 구분한다. Web API에는 원본 이미지 bytes를 ACK 전까지 보관하는 영속 AI 이미지 작업을 추가하고, Desktop Nest가 검증 후 `CLIPPER_DATA_DIR`에 영구 저장한다. 최종 렌더는 새 렌더러를 만들지 않고 기존 `ShortformProjectService` 경계에 이미지 `mediaSlots`와 기본 1:1 템플릿을 전달한다.

**Tech Stack:** NestJS 10 + `node:test`(Desktop), Angular 19 zoneless + NgRx Signals + Material 19, NestJS 11 + TypeORM/PostgreSQL + Jest(Web API), Gemini Developer API raw REST Interactions API.

## Implementation Status — 2026-08-07

- [x] Task 1: Generated-media config and backward-compatible project persistence
- [x] Task 2: Multi-image storyboard contract, prompt, compiler, and TTS alignment
- [x] Task 3: Web API Nano Banana capability and raw Gemini transport
- [x] Task 4: Persisted Web AI image job, result blob, ACK, migration, and OpenAPI
- [x] Task 5: Desktop image job domain and exact local image validation
- [ ] Task 6: Desktop Web client, per-shot approval service, result ACK, recovery, and file endpoint
- [ ] Task 7: Angular model selection and storyboard image-cut presentation
- [ ] Task 8: Angular per-image approval, state recovery, errors, and thumbnails
- [ ] Task 9: Existing Clipper 1:1 template render adapter and image motion
- [ ] Task 10: Cross-repository regression verification and manual smoke checklist

사용자의 `task5 까지만 진행하고 일단 중지` 지시에 따라 Task 5의 구현·집중 검증·독립
검토까지 완료한 뒤 멈췄다. Task 6은 시작하지 않았다. 상세 세션 기록은
`.codex/records/sessions/2026/08/07.md`, 작업별 실행 기록은
`.codex/.superpowers/sdd/2026-08-07-shortform-director-nano-banana-image-production-implementation-plan/`
에 있다.

## Global Constraints

- 설계 정본은 `.codex/design/2026-08-07-shortform-director-nano-banana-image-production-design.md`다.
- 사용자 표시 이름은 `Nano Banana 2`, 공급자 모델은 `gemini-3.1-flash-image`다.
- 요청은 `response_format.aspect_ratio: "1:1"`,
  `response_format.image_size: "1K"`로 고정하고 결과는 정확히
  1024×1024여야 한다.
- Nano Banana 2는 `clipper-template`만 허용한다. `ai-integrated` 요청은 Desktop Nest와 Web API에서 모두 400으로 거부한다.
- 이미지 출력 예상가는 장당 USD 0.067이다. 실제 사용량 기반 추정치는 입력 USD 0.50/1M tokens, 텍스트·thinking 출력 USD 3/1M tokens, 이미지 출력 USD 60/1M tokens를 사용한다.
- 목표 이미지 수는 `minimum=max(sceneCount, ceil(durationSec/3.0))`, `maximum=max(minimum, ceil(durationSec/2.5))` 범위다.
- 이미지 움직임은 전역 컷 순서대로 `zoom-in → pan-left → pan-right`를 반복한다.
- 이미지 픽셀 안에는 타이틀·대사 자막·숫자·로고·UI 문구·워터마크를 요청하지 않는다. 정확한 텍스트는 Clipper 레이어가 담당한다.
- Nano Banana 2 최종 렌더는 `system.template-builder.default-shortform`의 1:1 preset과 1080×1080 콘텐츠 영역을 사용한다.
- 기존 Gemini Omni, Seedance 2.0, Veo의 AI 영상 작업·Full 템플릿·최종 렌더 동작은 회귀시키지 않는다.
- Google 자격 증명은 기존 `GoogleAiCredentialService`를 재사용한다. Web Admin이나 새 provider credential은 추가하지 않는다.
- 자동 테스트와 구현 검증에서 실제 유료 Google 호출을 실행하지 않는다. 실제 호출은 사용자의 화면 비용 승인 뒤 수동 smoke에서만 수행한다.
- 기존 세 저장소의 dirty worktree를 보존한다. 관련 없는 정리·포맷 변경·파일 이동은 하지 않는다.
- 사용자가 직접 수행하는 `npm run build:app:mac:arm64:local-api` 패키징 빌드는 실행하지 않는다.
- 커밋과 push는 사용자가 별도로 요청하기 전에는 하지 않는다.

---

## File Map

### Desktop Nest: 생성 미디어 계약과 스토리보드

- Create `desktop/clipper_nestjs/src/modules/shortform-director/domain/ai-image-production.ts`: Nano Banana 2 capability와 config parser.
- Create `desktop/clipper_nestjs/src/modules/shortform-director/domain/generated-media-production.ts`: 새 video/image 상위 union과 legacy video config 호환 resolver.
- Modify `desktop/clipper_nestjs/src/modules/shortform-director/domain/production-state.ts`: 새 config와 image jobs를 strict hydration.
- Modify `desktop/clipper_nestjs/src/modules/shortform-director/domain/shortform-director.model.ts`: image shot의 narration range와 motion preset.
- Modify candidate production DTO/controller/preflight/service/mapper: 새 설정을 승인 snapshot과 두 LLM 호출에 전달.
- Modify inference projector/compiler/timing alignment/narration service: scene별 여러 image shot을 검증·컴파일·TTS 정렬.

### Web API: 이미지 생성 공급자와 영속 작업

- Extend `web/clipper_web_api/src/modules/shortform-director-production/domain/shortform-director-production-capability-catalog.ts`: 공개 AI image model capability.
- Create `web/clipper_web_api/src/modules/shortform-director-image-generation/`: transport, domain job, repository, TypeORM entity/repository, service, controller, DTO, module.
- Create user DB migration `1786100000000-CreateShortformDirectorAiImageJobs.ts`.
- Modify `web/clipper_web_api/docs/api/openapi.yaml`, user datasource, app module.

### Desktop Nest: 로컬 이미지 작업

- Create `ai-image-job.ts`, Web API client, image file inspector/storage, service, DTO, controller.
- Modify Shortform Director module and project production state persistence.
- Provide authenticated local result endpoint for Angular thumbnail blob download.

### Angular: 선택·상태·비용·thumbnail

- Widen production models/gateway/service/store to the generated media union.
- Modify production setup card so Nano Banana 2 forces Clipper mode.
- Modify storyboard scene list to show several image cuts and total image price.
- Create `ai-image-shot-status-list` four-file component.
- Branch the existing production card/page between AI video and AI image flows.

### Existing Clipper render seam

- Export the built-in default 1:1 preset ID from `template-builder-default-family.ts`.
- Modify `shortform-director-clipper-render.adapter.ts` to emit `media.image` assets and motion presets for image projects while retaining current video behavior.

---

### Task 1: Generated-media config and backward-compatible project persistence

**Files:**
- Create: `desktop/clipper_nestjs/src/modules/shortform-director/domain/ai-image-production.ts`
- Create: `desktop/clipper_nestjs/src/modules/shortform-director/domain/generated-media-production.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/domain/production-state.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-candidate-project.mapper.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/presentation/dto/start-shortform-director-candidate-production.dto.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/presentation/shortform-director-candidate-production.controller.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-candidate-production-preflight.service.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-candidate-production.service.ts`
- Test: `desktop/clipper_nestjs/test/shortform-director-generated-media-production.test.js`
- Test: `desktop/clipper_nestjs/test/shortform-director-project-production-state.test.js`
- Test: `desktop/clipper_nestjs/test/shortform-director-candidate-production.test.js`

**Interfaces:**
- Consumes: unchanged `AiVideoProductionConfigV1` for stored legacy projects.
- Produces:

```ts
export interface GeneratedVideoProductionConfigV1 {
  schemaVersion: 'generated-media-production-config.v1';
  kind: 'generated-video';
  model: AiVideoModel;
  mode: AiVideoProductionMode;
}

export interface GeneratedImageProductionConfigV1 {
  schemaVersion: 'generated-media-production-config.v1';
  kind: 'generated-image';
  model: 'nano-banana-2';
  mode: 'clipper-template';
}

export type GeneratedMediaProductionConfigV1 =
  | GeneratedVideoProductionConfigV1
  | GeneratedImageProductionConfigV1;

export const DEFAULT_GENERATED_MEDIA_PRODUCTION_CONFIG:
  GeneratedVideoProductionConfigV1;

export function parseGeneratedMediaProductionConfig(
  value: unknown,
): GeneratedMediaProductionConfigV1;

export function resolveGeneratedMediaProductionConfig(
  state: Pick<
    ShortformDirectorProductionStateV1,
    'generatedMediaProductionConfig' | 'aiVideoProductionConfig'
  >,
): GeneratedMediaProductionConfigV1;
```

- `ShortformDirectorProductionStateV1.generatedMediaProductionConfig?` is the new write path.
- `ShortformDirectorProductionStateV1.aiVideoProductionConfig?` remains read-only compatibility for old JSON.

- [ ] **Step 1: Write failing domain and persistence tests**

```js
assert.deepEqual(
  parseGeneratedMediaProductionConfig({
    schemaVersion: 'generated-media-production-config.v1',
    kind: 'generated-image',
    model: 'nano-banana-2',
    mode: 'clipper-template',
  }),
  {
    schemaVersion: 'generated-media-production-config.v1',
    kind: 'generated-image',
    model: 'nano-banana-2',
    mode: 'clipper-template',
  },
);
assert.throws(() => parseGeneratedMediaProductionConfig({
  schemaVersion: 'generated-media-production-config.v1',
  kind: 'generated-image',
  model: 'nano-banana-2',
  mode: 'ai-integrated',
}));
assert.equal(
  resolveGeneratedMediaProductionConfig({
    aiVideoProductionConfig: {
      schemaVersion: 'ai-video-production-config.v1',
      model: 'gemini-omni',
      mode: 'clipper-template',
    },
  }).kind,
  'generated-video',
);
```

- [ ] **Step 2: Run the focused tests and confirm they fail for missing types**

Run:

```bash
cd desktop/clipper_nestjs
npm run build
node --test test/shortform-director-generated-media-production.test.js test/shortform-director-project-production-state.test.js test/shortform-director-candidate-production.test.js
```

Expected: build/test failure because the new parser, state key, and Nano config do not exist.

- [ ] **Step 3: Implement exact image capability and union parser**

```ts
export const NANO_BANANA_2_CAPABILITY = Object.freeze({
  displayName: 'Nano Banana 2',
  provider: 'google_ai',
  providerModelId: 'gemini-3.1-flash-image',
  aspectRatio: '1:1',
  imageSize: '1K',
  width: 1024,
  height: 1024,
  estimatedUsdPerImage: 0.067,
} as const);
```

The parser must reject extra keys and invalid image mode. `generated-media-production.ts` converts legacy `AiVideoProductionConfigV1` into the new `generated-video` shape without rewriting stored JSON.

- [ ] **Step 4: Wire candidate preflight and start DTO to the new shape**

The GET preflight query must carry `kind`, `model`, and `mode`. The POST body uses one decorated DTO with all five allowed model names; the domain parser performs the cross-field check:

```ts
@Equals('generated-media-production-config.v1')
schemaVersion!: 'generated-media-production-config.v1';

@IsIn(['generated-video', 'generated-image'])
kind!: 'generated-video' | 'generated-image';

@IsIn([
  'gemini-omni',
  'seedance-2.0',
  'veo-3.1-lite',
  'veo-3.1-fast',
  'nano-banana-2',
])
model!: AiVideoModel | 'nano-banana-2';

@IsIn(['clipper-template', 'ai-integrated'])
mode!: AiVideoProductionMode;
```

The approval snapshot must include the full normalized config so switching video↔image invalidates a stale approval ID.

- [ ] **Step 5: Persist only the new key for newly created storyboards**

`ShortformDirectorCandidateProjectMapper` writes:

```ts
production: {
  ...createEmptyShortformDirectorProductionState(),
  generatedMediaProductionConfig: { ...input.productionConfig },
}
```

All current readers in candidate production use `resolveGeneratedMediaProductionConfig`; no new code writes `aiVideoProductionConfig`.

- [ ] **Step 6: Run tests and inspect the diff**

Run:

```bash
cd desktop/clipper_nestjs
npm run build
node --test test/shortform-director-generated-media-production.test.js test/shortform-director-project-production-state.test.js test/shortform-director-candidate-production.test.js
git diff --check
```

Expected: all focused tests pass; old video config hydration remains green; no commit is created.

---

### Task 2: Multi-image storyboard contract, prompt, compiler, and TTS alignment

**Files:**
- Modify: `web/clipper_web_api/src/modules/shortform-director-inference/domain/shortform-director-inference.contract.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-inference/domain/shortform-director-inference.contract.spec.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-inference/application/shortform-director-inference.prompt.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-inference/application/shortform-director-inference.prompt.spec.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-inference-response.projector.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-candidate-production.service.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-candidate-plan.compiler.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/domain/shortform-director.model.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/domain/video-plan-contract.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/domain/video-plan-timing-alignment.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-narration.service.ts`
- Test: `desktop/clipper_nestjs/test/shortform-director-candidate-production.test.js`
- Test: `desktop/clipper_nestjs/test/shortform-director-video-plan.test.js`
- Test: `desktop/clipper_nestjs/test/shortform-director-tts-timing-alignment.test.js`
- Test: `desktop/clipper_nestjs/test/shortform-director-narration-service.test.js`

**Interfaces:**
- Consumes: `GeneratedMediaProductionConfigV1` from Task 1.
- Produces:

```ts
export interface SceneMediaDecisionV1 {
  sceneIndex: number;
  baseMedium: 'generated-video' | 'generated-image';
  overlayMode: 'none';
  generationBrief: string | null;
  imageBriefs: string[] | null;
}

export interface VideoPlanShot {
  narrationRange?: {
    startCharacter: number;
    endCharacter: number;
  };
  motionPreset?: 'zoom-in' | 'pan-left' | 'pan-right';
}
```

- `generated-video` requires one non-empty `generationBrief` and `imageBriefs:null`.
- `generated-image` requires `generationBrief:null` and one or more distinct `imageBriefs`.

- [ ] **Step 1: Write failing Web inference contract and prompt tests**

```ts
expect(parseSceneMediaDecision({
  sceneIndex: 0,
  baseMedium: 'generated-image',
  overlayMode: 'none',
  generationBrief: null,
  imageBriefs: [
    'A Korean investor comparing two paper account statements at a desk',
    'A close-up of a hand marking a policy calendar with a red pencil',
  ],
  rationale: '두 시각 전환으로 문제와 확인 행동을 분리한다.',
  factualRisk: 'medium',
  evidenceIds: ['evidence.1'],
  productionSourceIds: [],
  searchBrief: null,
  programmaticBrief: null,
}).imageBriefs).toHaveLength(2);
```

The prompt test must assert all of:

```ts
expect(prompt).toContain('generated-image');
expect(prompt).toContain('10개 이상 12개 이하');
expect(prompt).toContain('이미지 안에 읽을 수 있는 글자');
expect(prompt).toContain('각 scene에 최소 1개');
```

- [ ] **Step 2: Run the Web inference tests and confirm contract failure**

Run:

```bash
cd web/clipper_web_api
npm test -- --runInBand src/modules/shortform-director-inference/domain/shortform-director-inference.contract.spec.ts src/modules/shortform-director-inference/application/shortform-director-inference.prompt.spec.ts
```

Expected: failure because `imageBriefs` and the image-specific prompt branch do not exist.

- [ ] **Step 3: Implement the conditional schema and prompt**

`generatedMediaProduction.kind === 'generated-image'` must:

- ask the first inference for semantic scenes and narration without video min/max language;
- ask the second inference for `generated-image` decisions;
- calculate and inject the exact total allowed image count;
- demand concrete subject/place/action/composition differences;
- forbid readable text, numbers, logos, interface copy, watermarks, audio, and camera movement.

The existing video branch keeps its current model duration, audio, and text policies byte-for-byte where practical.

- [ ] **Step 4: Write failing Desktop projector and compiler tests**

Use a 30,000ms, 5-scene fixture with 10 image briefs. Assert:

```js
assert.equal(plan.scenes.length, 5);
assert.equal(
  plan.scenes.flatMap((scene) => scene.beats.flatMap((beat) => beat.shots)).length,
  10,
);
assert.deepEqual(
  allShots.map((shot) => shot.motionPreset),
  [
    'zoom-in', 'pan-left', 'pan-right',
    'zoom-in', 'pan-left', 'pan-right',
    'zoom-in', 'pan-left', 'pan-right',
    'zoom-in',
  ],
);
assert.ok(allShots.every((shot) =>
  shot.layers.some((layer) =>
    layer.assetStrategy === 'generated-image'
  )
));
```

Add rejection tests for 9 and 13 total images, an empty scene image list, duplicate adjacent briefs, and `generated-video` with non-null `imageBriefs`.

- [ ] **Step 5: Implement deterministic image-shot compilation**

The compiler must:

1. preserve semantic scene/beat count;
2. create one `VideoPlanShot` per image brief;
3. split narration text at punctuation, then whitespace, choosing boundaries nearest equal character weights;
4. store non-overlapping `narrationRange` values that cover the cue text;
5. derive estimated shot duration from each range character weight;
6. attach motion presets by global image-shot index;
7. create one generated-image visual layer with that shot's unique brief.

Use this exact helper signature:

```ts
export function imageShotNarrationRanges(
  narration: string,
  shotCount: number,
): Array<{ startCharacter: number; endCharacter: number }>;
```

- [ ] **Step 6: Keep the image count stable through TTS alignment**

`alignVideoPlanTiming` continues to proportionally align existing shot boundaries. `ShortformDirectorNarrationService` must skip the video-model `splitAlignedShots` pass for `generated-image`, so a user's approved image count never increases after TTS.

Test a 30-second estimated plan aligned to 34.7 seconds and assert the same 10 shot IDs remain, their durations cover 34.7 seconds contiguously, and no image job exists before explicit image approval.

- [ ] **Step 7: Run focused Desktop and Web tests**

Run:

```bash
cd web/clipper_web_api
npm test -- --runInBand src/modules/shortform-director-inference/domain/shortform-director-inference.contract.spec.ts src/modules/shortform-director-inference/application/shortform-director-inference.prompt.spec.ts

cd ../../desktop/clipper_nestjs
npm run build
node --test test/shortform-director-candidate-production.test.js test/shortform-director-video-plan.test.js test/shortform-director-tts-timing-alignment.test.js test/shortform-director-narration-service.test.js
git diff --check
```

Expected: image plan tests and unchanged representative video plan tests pass.

---

### Task 3: Web API Nano Banana capability and raw Gemini transport

**Files:**
- Modify: `web/clipper_web_api/src/modules/shortform-director-production/domain/shortform-director-production-capability-catalog.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-production/domain/shortform-director-production-capability-catalog.spec.ts`
- Create: `web/clipper_web_api/src/modules/shortform-director-image-generation/domain/ai-image-generation.transport.ts`
- Create: `web/clipper_web_api/src/modules/shortform-director-image-generation/infrastructure/gemini-image.transport.ts`
- Create: `web/clipper_web_api/src/modules/shortform-director-image-generation/infrastructure/gemini-image.transport.spec.ts`

**Interfaces:**
- Consumes: existing `GoogleAiCredentialService`; no Google SDK.
- Produces:

```ts
export interface AiImageModel {
  id: 'nano-banana-2';
  displayName: 'Nano Banana 2';
  provider: 'google-ai';
  providerModelId: 'gemini-3.1-flash-image';
  aspectRatio: '1:1';
  imageSize: '1K';
  width: 1024;
  height: 1024;
  estimatedUsdPerImage: 0.067;
  supportedModes: readonly ['clipper-template'];
}

export interface AiImageProviderResult {
  providerRequestId: string;
  mimeType: 'image/png' | 'image/jpeg' | 'image/webp';
  bytes: Buffer;
  usage: {
    totalInputTokens: number;
    totalOutputTokens: number;
    totalThoughtTokens: number;
    totalTokens: number;
  } | null;
  actualEstimatedCostUsd: number | null;
}
```

- [ ] **Step 1: Write capability and exact request-shape tests**

```ts
expect(aiImageModel('nano-banana-2')).toEqual(expect.objectContaining({
  providerModelId: 'gemini-3.1-flash-image',
  aspectRatio: '1:1',
  imageSize: '1K',
  width: 1024,
  height: 1024,
  estimatedUsdPerImage: 0.067,
  supportedModes: ['clipper-template'],
}));
```

The transport spec must capture `fetch` and assert:

```ts
expect(requestUrl).toBe(
  'https://generativelanguage.googleapis.com/v1beta/interactions',
);
expect(body).toEqual({
  model: 'gemini-3.1-flash-image',
  input: prompt,
  response_format: {
    type: 'image',
    aspect_ratio: '1:1',
    image_size: '1K',
  },
  store: false,
});
```

- [ ] **Step 2: Run tests and confirm failure**

Run:

```bash
cd web/clipper_web_api
npm test -- --runInBand src/modules/shortform-director-production/domain/shortform-director-production-capability-catalog.spec.ts src/modules/shortform-director-image-generation/infrastructure/gemini-image.transport.spec.ts
```

Expected: missing image capability/transport failure.

- [ ] **Step 3: Implement the transport with bounded parsing**

The transport must:

- set `x-goog-api-key`, never put credentials in the URL;
- use a 180-second abort timeout;
- require `status:"completed"` and decode exactly one
  `steps[].type=="model_output"` image content block;
- reject missing/multiple images and MIME outside PNG/JPEG/WebP;
- cap decoded bytes at 32 MiB;
- sanitize Google `error.status`, `error.code`, and `error.message`;
- retain `x-request-id`/response metadata as `providerRequestId`, falling back to a generated opaque ID;
- compute usage estimate as fixed image output plus reported input and text/thinking tokens.

- [ ] **Step 4: Test success, safety error, empty image, malformed base64, and usage cost**

For a success with 200 input tokens and 50 thinking tokens:

```ts
expect(result.actualEstimatedCostUsd).toBeCloseTo(
  0.067 + (200 * 0.5 / 1_000_000) + (50 * 3 / 1_000_000),
  8,
);
```

Provider errors must retain safe fields but never response headers or API keys.

- [ ] **Step 5: Run focused tests and diff check**

Run:

```bash
cd web/clipper_web_api
npm test -- --runInBand src/modules/shortform-director-production/domain/shortform-director-production-capability-catalog.spec.ts src/modules/shortform-director-image-generation/infrastructure/gemini-image.transport.spec.ts
git diff --check
```

Expected: all capability and transport tests pass without network access.

---

### Task 4: Persisted Web AI image job, result blob, ACK, migration, and OpenAPI

**Files:**
- Create: `web/clipper_web_api/src/modules/shortform-director-image-generation/domain/ai-image-job.ts`
- Create: `web/clipper_web_api/src/modules/shortform-director-image-generation/domain/ai-image-job.repository.ts`
- Create: `web/clipper_web_api/src/modules/shortform-director-image-generation/infrastructure/ai-image-job.entity.ts`
- Create: `web/clipper_web_api/src/modules/shortform-director-image-generation/infrastructure/typeorm-ai-image-job.repository.ts`
- Create: `web/clipper_web_api/src/modules/shortform-director-image-generation/infrastructure/typeorm-ai-image-job.repository.spec.ts`
- Create: `web/clipper_web_api/src/modules/shortform-director-image-generation/application/shortform-director-image-generation.service.ts`
- Create: `web/clipper_web_api/src/modules/shortform-director-image-generation/application/shortform-director-image-generation.service.spec.ts`
- Create: `web/clipper_web_api/src/modules/shortform-director-image-generation/presentation/dto/create-ai-image-job.dto.ts`
- Create: `web/clipper_web_api/src/modules/shortform-director-image-generation/presentation/dto/ack-ai-image-result.dto.ts`
- Create: `web/clipper_web_api/src/modules/shortform-director-image-generation/presentation/shortform-director-image-generation.controller.ts`
- Create: `web/clipper_web_api/src/modules/shortform-director-image-generation/presentation/shortform-director-image-generation.controller.spec.ts`
- Create: `web/clipper_web_api/src/modules/shortform-director-image-generation/shortform-director-image-generation.module.ts`
- Create: `web/clipper_web_api/src/core/database/migrations/user/1786100000000-CreateShortformDirectorAiImageJobs.ts`
- Create: `web/clipper_web_api/src/core/database/migrations/user/1786100000000-CreateShortformDirectorAiImageJobs.spec.ts`
- Modify: `web/clipper_web_api/src/core/database/user.datasource.ts`
- Modify: `web/clipper_web_api/src/core/database/user.datasource.spec.ts`
- Modify: `web/clipper_web_api/src/app.module.ts`
- Modify: `web/clipper_web_api/docs/api/openapi.yaml`

**Interfaces:**
- Consumes: `GeminiImageTransport.generate(...)` from Task 3.
- Produces authenticated raw endpoints:

```text
GET  /shortform-director/image-generation/models
POST /shortform-director/image-generation/jobs
GET  /shortform-director/image-generation/jobs/:jobId
GET  /shortform-director/image-generation/jobs/:jobId/result
POST /shortform-director/image-generation/jobs/:jobId/result-ack
```

- Public status is `processing | ready | failed | output_expired`.
- Successful job metadata includes MIME, bytes, checksum, usage, `estimatedCostUsd:0.067`, and nullable `actualEstimatedCostUsd`.

- [ ] **Step 1: Define OpenAPI request and raw response contracts first**

The create body is:

```yaml
required:
  - idempotencyKey
  - projectId
  - shotId
  - revisionId
  - model
  - mode
  - prompt
properties:
  model:
    type: string
    enum: [nano-banana-2]
  mode:
    type: string
    enum: [clipper-template]
```

`result` returns binary image content. `result-ack` requires the Desktop-calculated `checksum` and `sizeBytes`.

- [ ] **Step 2: Write failing migration/entity/repository tests**

Assert snake_case columns, unique `(owner_subject_id,idempotency_key)`, `bytea result_blob`, `result_expires_at`, `result_acked_at`, and no cross-database foreign key.

- [ ] **Step 3: Implement entity, migration, repository, and datasource wiring**

The domain job stores:

```ts
interface AiImageJob {
  id: string;
  ownerSubjectId: string;
  idempotencyKey: string;
  inputDigest: string;
  projectId: string;
  shotId: string;
  revisionId: string;
  model: 'nano-banana-2';
  mode: 'clipper-template';
  prompt: string;
  status: 'processing' | 'ready' | 'failed' | 'output_expired';
  providerRequestId: string | null;
  credentialRevision: string;
  outputMimeType: string | null;
  outputSizeBytes: number | null;
  outputChecksum: string | null;
  resultBlob: Buffer | null;
  usage: Record<string, number> | null;
  estimatedCostUsd: 0.067;
  actualEstimatedCostUsd: number | null;
  providerFailure: {
    status: number | null;
    code: string | null;
    message: string;
  } | null;
  processingDeadlineAt: string | null;
  resultExpiresAt: string | null;
  resultAckedAt: string | null;
  createdAt: string;
  updatedAt: string;
}
```

- [ ] **Step 4: Write failing service idempotency, persistence, expiry, and ACK tests**

The tests must prove:

- the `processing` row is saved before transport invocation;
- same owner/idempotency/digest returns the same job and calls transport once;
- same idempotency with a different digest returns 409;
- successful bytes survive a new service instance using the same repository;
- result access is owner-scoped;
- matching ACK deletes only `result_blob`;
- wrong checksum/size returns 409 and retains the blob;
- unacknowledged data expires exactly seven days after success;
- expired results return 410 and never resubmit Google;
- a persisted `processing` job is never automatically resubmitted after restart.
- a `processing` job that remains unresolved for five minutes is persisted as
  `failed/provider_result_unknown`; the UI warns that a newly approved retry
  can incur another charge.

- [ ] **Step 5: Implement service and controller**

Create flow:

1. validate model/mode/prompt/idempotency;
2. resolve Google credential;
3. save `processing`;
4. call the transport once;
5. save `ready` plus blob/checksum/usage/expiry, or `failed` plus safe provider error;
6. return raw public job metadata.

Set `processingDeadlineAt` to five minutes after creation. `get` and
idempotency replay reconcile an expired processing deadline to
`provider_result_unknown` without calling Google.

The controller streams the stored bytes directly and sets the stored MIME and content length. It must never expose prompt, result blob, owner ID, input digest, or API key.

- [ ] **Step 6: Register module, entity, migration, and validate OpenAPI**

Add `ShortformDirectorImageGenerationModule` to `AppModule`; add entity and migration to the user datasource arrays. Extend existing OpenAPI validation specs so all controller paths and enums are present.

- [ ] **Step 7: Run focused and build verification**

Run:

```bash
cd web/clipper_web_api
npm test -- --runInBand src/core/database/migrations/user/1786100000000-CreateShortformDirectorAiImageJobs.spec.ts src/core/database/user.datasource.spec.ts src/modules/shortform-director-image-generation
npm run build
git diff --check
```

Expected: migration, repository, service, controller, OpenAPI, and build pass with fake transport only.

---

### Task 5: Desktop image job domain and exact local image validation

**Files:**
- Create: `desktop/clipper_nestjs/src/modules/shortform-director/domain/ai-image-job.ts`
- Create: `desktop/clipper_nestjs/src/modules/shortform-director/infrastructure/generated-image-file.inspector.ts`
- Create: `desktop/clipper_nestjs/src/modules/shortform-director/infrastructure/local-shortform-director-generated-image.storage.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/domain/production-state.ts`
- Test: `desktop/clipper_nestjs/test/shortform-director-ai-image-job.test.js`
- Test: `desktop/clipper_nestjs/test/shortform-director-generated-image-storage.test.js`
- Fixture: `desktop/clipper_nestjs/test/fixtures/shortform-director/generated-image-1024.png`
- Fixture: `desktop/clipper_nestjs/test/fixtures/shortform-director/generated-image-512.webp`
- Fixture: `desktop/clipper_nestjs/test/fixtures/shortform-director/generated-image-1024.jpg`

**Interfaces:**
- Produces:

```ts
export interface AiImageGeneratedAssetV1 {
  relativePath: string;
  sizeBytes: number;
  checksum: `sha256:${string}`;
  mediaType: 'image/png' | 'image/jpeg' | 'image/webp';
  width: 1024;
  height: 1024;
  downloadedAt: string;
}

export interface AiImageJobV1 {
  schemaVersion: 'ai-image-job.v1';
  revisionId: string;
  attempt: number;
  retryOfRevisionId: string | null;
  idempotencyKey: string;
  approvalId: string;
  ownerSubjectId: string;
  projectId: string;
  storyboardRunId: string;
  shotId: string;
  model: 'nano-banana-2';
  providerModelId: 'gemini-3.1-flash-image';
  mode: 'clipper-template';
  prompt: string;
  estimatedCostUsd: 0.067;
  actualEstimatedCostUsd: number | null;
  status:
    | 'planned'
    | 'generating'
    | 'output_ready'
    | 'downloading'
    | 'ready'
    | 'generation_failed'
    | 'output_expired'
    | 'download_failed'
    | 'validation_failed'
    | 'cancelled';
  webApiJobId: string | null;
  providerRequestId: string | null;
  credentialRevision: string;
  asset: AiImageGeneratedAssetV1 | null;
  usage: {
    totalInputTokens: number;
    totalOutputTokens: number;
    totalThoughtTokens: number;
    totalTokens: number;
  } | null;
  failure: {
    code: string;
    message: string;
    providerStatus?: number;
    providerCode?: string;
    providerMessage?: string;
    failedAt: string;
  } | null;
  createdAt: string;
  updatedAt: string;
}
```

- [ ] **Step 1: Write failing state-transition and strict hydration tests**

Test planned→generating→output_ready→downloading→ready, rejected backward transitions, retry only from failed states with a new idempotency key, and duplicate revision rejection in `production-state.ts`.

- [ ] **Step 2: Write failing PNG/JPEG/WebP signature and dimension tests**

```js
assert.deepEqual(inspectGeneratedImage(png1024), {
  mediaType: 'image/png',
  extension: 'png',
  width: 1024,
  height: 1024,
});
assert.throws(
  () => inspectGeneratedImage(webp512),
  /1024x1024/,
);
assert.throws(
  () => inspectGeneratedImage(Buffer.from('not-image')),
  /signature/,
);
```

- [ ] **Step 3: Implement bounded file inspection without a new image dependency**

Parse:

- PNG IHDR width/height;
- JPEG SOF0/SOF1/SOF2 width/height;
- WebP VP8, VP8L, and VP8X canvas width/height.

Require signature/MIME agreement, exact 1024×1024, non-empty bytes, and at most 32 MiB.

- [ ] **Step 4: Implement atomic local storage**

Write to:

```text
shortform-director/projects/<projectId>/assets/generated-images/<shotId>/<revisionId>.<ext>
```

Use `.part`, compute SHA-256 while writing, validate before atomic rename, and never overwrite a completed revision file. Return only a safe relative path.

- [ ] **Step 5: Run focused tests**

Run:

```bash
cd desktop/clipper_nestjs
npm run build
node --test test/shortform-director-ai-image-job.test.js test/shortform-director-generated-image-storage.test.js test/shortform-director-project-production-state.test.js
git diff --check
```

Expected: domain transition, strict JSON hydration, format parsing, invalid-size rejection, and atomic storage pass.

---

### Task 6: Desktop Web client, per-shot approval service, result ACK, recovery, and file endpoint

**Files:**
- Create: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-ai-image-web-api.client.ts`
- Create: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-ai-image.service.ts`
- Create: `desktop/clipper_nestjs/src/modules/shortform-director/presentation/dto/start-shortform-director-ai-image.dto.ts`
- Create: `desktop/clipper_nestjs/src/modules/shortform-director/presentation/shortform-director-ai-image.controller.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/shortform-director.module.ts`
- Test: `desktop/clipper_nestjs/test/shortform-director-ai-image-client.test.js`
- Test: `desktop/clipper_nestjs/test/shortform-director-ai-image-service.test.js`
- Test: `desktop/clipper_nestjs/test/shortform-director-ai-image-controller.test.js`

**Interfaces:**
- Consumes: Web endpoints from Task 4, image job/storage from Task 5.
- Produces local endpoints:

```text
GET  /v1/projects/shortform-director/projects/:projectId/ai-image/jobs
GET  /v1/projects/shortform-director/projects/:projectId/ai-image/shots/:shotId/preflight
POST /v1/projects/shortform-director/projects/:projectId/ai-image/shots/:shotId/jobs
POST /v1/projects/shortform-director/projects/:projectId/ai-image/revisions/:revisionId/sync
GET  /v1/projects/shortform-director/projects/:projectId/ai-image/revisions/:revisionId/file
```

```ts
export interface ShortformDirectorAiImagePreflightV1 {
  schemaVersion: 'shortform-director-ai-image-preflight.v1';
  ready: true;
  projectId: string;
  shotId: string;
  revisionId: string;
  approvalId: string;
  model: 'nano-banana-2';
  providerModelId: 'gemini-3.1-flash-image';
  mode: 'clipper-template';
  aspectRatio: '1:1';
  imageSize: '1K';
  width: 1024;
  height: 1024;
  prompt: string;
  estimatedCostUsd: 0.067;
  existingStatus: AiImageJobV1['status'] | null;
}
```

- [ ] **Step 1: Write failing Web client parsing tests**

Assert exact route paths, bearer propagation, 180-second create timeout, 60-second result timeout, strict job lineage parsing, binary stream download, and ACK body `{checksum,sizeBytes}`.

- [ ] **Step 2: Write failing service tests for approval and restart recovery**

Test:

- preflight rejects video projects and any non-image visual shot;
- start requires exact `approvalId` and `confirmed:true`;
- cost approval mismatch returns 409 before Web call;
- successful Web response is downloaded, validated, stored, ACKed, and linked through `activeSceneMediaRevisions`;
- download failure retains the same Web job ID and `sync` downloads without a new create;
- validation failure retains provider metadata and requires explicit same-result revalidation;
- generation failure retry uses a new approval/idempotency revision and never regenerates ready siblings;
- a reconstructed service reads jobs from project JSON and resumes `output_ready`/`download_failed`;
- no provider call occurs for `preflight` or thumbnail file download.

- [ ] **Step 3: Implement strict client and provider failure projection**

The client must parse safe Google status/code/message fields into the existing Director failure shape. `result-ack` occurs only after atomic local persistence and matching checksum.

- [ ] **Step 4: Implement service locking and project persistence**

Use the same per-project/per-shot in-process lock pattern as AI video. Persist `planned` before Web submission, every transition after it, and active layer revision only after local file readiness.

The first attempt is `attempt:1`. A failed provider attempt makes the next
preflight derive `attempt+1`, `retryOfRevisionId`, a new `revisionId`, and a
new `approvalId`; therefore a retry cannot overwrite the earlier local file
or reuse its cost approval.

- [ ] **Step 5: Implement controller and authenticated file streaming**

The file route resolves the stored job by owner/project/revision, verifies the path stays inside `CLIPPER_DATA_DIR`, sets stored MIME and content length, and returns `StreamableFile`. It must not accept a caller-supplied path.

- [ ] **Step 6: Wire providers into `ShortformDirectorModule` and run tests**

Run:

```bash
cd desktop/clipper_nestjs
npm run build
node --test test/shortform-director-ai-image-client.test.js test/shortform-director-ai-image-service.test.js test/shortform-director-ai-image-controller.test.js test/shortform-director-ai-video-service.test.js
git diff --check
```

Expected: image flow passes and existing AI video service remains green.

---

### Task 7: Angular model selection and storyboard image-cut presentation

**Files:**
- Modify: `desktop/clipper_angular/src/features/shortform-director/models/shortform-director-production.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/models/shortform-director-production.spec.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/models/shortform-director-project.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/testing/shortform-director-production.fixtures.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/production-setup-card/production-setup-card.component.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/production-setup-card/production-setup-card.component.html`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/production-setup-card/production-setup-card.component.scss`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/production-setup-card/production-setup-card.component.spec.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/storyboard-scene-list/storyboard-scene-list.component.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/storyboard-scene-list/storyboard-scene-list.component.html`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/storyboard-scene-list/storyboard-scene-list.component.scss`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/storyboard-scene-list/storyboard-scene-list.component.spec.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-production.gateway.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-production.service.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/state/shortform-director-production.store.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/state/shortform-director-production.store.spec.ts`

**Interfaces:**
- Consumes: generated media config and image shot fields from Tasks 1–2.
- Produces UI selection where `selectModel('nano-banana-2')` atomically sets:

```ts
{
  schemaVersion: 'generated-media-production-config.v1',
  kind: 'generated-image',
  model: 'nano-banana-2',
  mode: 'clipper-template',
}
```

- [ ] **Step 1: Write failing setup-card tests**

Assert the Nano card displays:

- `Nano Banana 2`
- `1:1 · 1K · 1024×1024`
- `장당 예상 USD 0.067`
- the explanation that Clipper handles voice/subtitles/title.

Clicking it emits Nano config and hides/disables `AI 통합 제작 방식`; switching back to a video model restores both video modes.

- [ ] **Step 2: Write failing service/store request tests**

Assert preflight query includes `kind=generated-image`, POST sends the exact new config, and selecting Nano resets a stale preflight/approval from another model.

- [ ] **Step 3: Implement the generated-media model union and selection**

Keep existing display helpers for video and add:

```ts
export function generatedMediaModelDisplayName(
  config: GeneratedMediaProductionConfigV1,
): string {
  return config.kind === 'generated-image'
    ? 'Nano Banana 2'
    : aiVideoModelDisplayName(config.model);
}
```

Do not add resolution controls or arbitrary px inputs.

- [ ] **Step 4: Write failing storyboard scene-list tests**

Render a 30-second, 5-scene fixture with 10 image shots and assert:

- semantic scenes remain five vertical sections;
- each scene contains its own image-cut rows;
- each row shows prompt summary, expected duration, and Korean motion label;
- summary shows `이미지 10장` and `예상 이미지 생성비 USD 0.67`;
- no internal IDs appear before advanced detail is expanded.

- [ ] **Step 5: Implement scene/image-cut presentation**

Motion labels:

```ts
const MOTION_LABELS = {
  'zoom-in': '천천히 확대',
  'pan-left': '오른쪽에서 왼쪽으로 이동',
  'pan-right': '왼쪽에서 오른쪽으로 이동',
} as const;
```

Use existing Material components and semantic SCSS tokens only; do not create a new grid-first storyboard layout.

- [ ] **Step 6: Run focused Angular tests**

Run:

```bash
cd desktop/clipper_angular
npm test -- --watch=false --browsers=ChromeHeadless --include=src/features/shortform-director/models/shortform-director-production.spec.ts --include=src/features/shortform-director/components/production-setup-card/production-setup-card.component.spec.ts --include=src/features/shortform-director/components/storyboard-scene-list/storyboard-scene-list.component.spec.ts --include=src/features/shortform-director/state/shortform-director-production.store.spec.ts
git diff --check
```

Expected: selection, forced mode, exact request, history hydration, and image-cut summary tests pass.

---

### Task 8: Angular per-image approval, state recovery, errors, and thumbnails

**Files:**
- Create: `desktop/clipper_angular/src/features/shortform-director/components/ai-image-shot-status-list/ai-image-shot-status-list.component.ts`
- Create: `desktop/clipper_angular/src/features/shortform-director/components/ai-image-shot-status-list/ai-image-shot-status-list.component.html`
- Create: `desktop/clipper_angular/src/features/shortform-director/components/ai-image-shot-status-list/ai-image-shot-status-list.component.scss`
- Create: `desktop/clipper_angular/src/features/shortform-director/components/ai-image-shot-status-list/ai-image-shot-status-list.component.spec.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/models/shortform-director-production.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-production.gateway.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-production.service.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-production.service.spec.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/state/shortform-director-production.store.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/state/shortform-director-production.store.spec.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/ai-video-production-card/ai-video-production-card.component.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/ai-video-production-card/ai-video-production-card.component.html`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/ai-video-production-card/ai-video-production-card.component.spec.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/pages/production-page/production-page.component.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/pages/production-page/production-page.component.html`
- Modify: `desktop/clipper_angular/src/features/shortform-director/pages/production-page/production-page.component.spec.ts`

**Interfaces:**
- Consumes: local image endpoints from Task 6.
- Produces gateway methods:

```ts
listAiImageJobs(projectId: string): Promise<AiImageJobV1[]>;
getAiImagePreflight(
  projectId: string,
  shotId: string,
): Promise<ShortformDirectorAiImagePreflightV1>;
startAiImage(
  projectId: string,
  shotId: string,
  approvalId: string,
): Promise<AiImageJobV1>;
syncAiImage(
  projectId: string,
  revisionId: string,
): Promise<AiImageJobV1>;
downloadAiImage(
  projectId: string,
  revisionId: string,
): Promise<Blob>;
```

- [ ] **Step 1: Write failing component tests for all user-visible states**

Cover `시작 전`, `생성 중`, `로컬 저장 완료`, `생성 실패`, `파일 검증 실패`, `결과 만료`. Each row shows prompt, duration, motion, USD 0.067, safe provider message, and only the valid action for that state.

A ready row with provider usage must label and display
`실제 사용량 기반 추정 비용`; it must not call the value an actual invoice
or exact charge.

- [ ] **Step 2: Write failing store tests for per-shot isolation**

Prove:

- preflight does not generate;
- confirm starts only the selected image shot;
- a failed shot does not clear ready siblings;
- refresh/sync does not create a new provider job;
- project reload restores persisted jobs;
- image flow never starts video polling;
- ready jobs fetch one thumbnail blob and reuse its object URL;
- project switch and store destruction call `URL.revokeObjectURL`.

- [ ] **Step 3: Implement gateway/service/store image methods**

Use Angular `HttpClient` with `responseType:'blob'` for the authenticated local file route. Store thumbnails as `Record<revisionId,string>` object URLs, not base64 in application state.

- [ ] **Step 4: Implement the image status component**

Use `<img>` only with the store-created object URL. Missing thumbnail must show a neutral placeholder without retry loops. Keep technical IDs and credential revision inside the existing advanced disclosure.

- [ ] **Step 5: Branch the existing production card**

For `generated-image`:

- step 1 remains Clipper narration;
- step 2 title becomes `2. AI 이미지 생성`;
- render `AiImageShotStatusListComponent`;
- step 3 enables only when narration and every image shot are ready.

For `generated-video`, retain current markup and behavior. Do not rename or move the existing production card files in this task.

- [ ] **Step 6: Run focused Angular tests**

Run:

```bash
cd desktop/clipper_angular
npm test -- --watch=false --browsers=ChromeHeadless --include=src/features/shortform-director/components/ai-image-shot-status-list/ai-image-shot-status-list.component.spec.ts --include=src/features/shortform-director/components/ai-video-production-card/ai-video-production-card.component.spec.ts --include=src/features/shortform-director/services/shortform-director-production.service.spec.ts --include=src/features/shortform-director/state/shortform-director-production.store.spec.ts --include=src/features/shortform-director/pages/production-page/production-page.component.spec.ts
git diff --check
```

Expected: image approval, error, recovery, thumbnail lifecycle, and unchanged video production UI pass.

---

### Task 9: Existing Clipper 1:1 template render adapter and image motion

**Files:**
- Modify: `desktop/clipper_nestjs/src/modules/template-builder/domain/template-builder-default-family.ts`
- Modify: `desktop/clipper_nestjs/src/modules/project-manifest/infrastructure/template-builder-published-preset-source.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-clipper-render.adapter.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-final-render.service.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/domain/asset-production-readiness.ts`
- Test: `desktop/clipper_nestjs/test/template-builder-default-shortform-family.test.js`
- Test: `desktop/clipper_nestjs/test/shortform-director-clipper-render-adapter.test.js`
- Test: `desktop/clipper_nestjs/test/shortform-director-final-render-service.test.js`
- Test: `desktop/clipper_nestjs/test/project-detail-builder-shortform-director.test.js`

**Interfaces:**
- Consumes: ready `AiImageJobV1` assets and motion presets.
- Produces:

```ts
export const DEFAULT_SHORTFORM_TEMPLATE_PRESET_ID =
  'template_builder.custom.system.template-builder.default-shortform.ratio.1_u3a1';
```

- Image projects use:

```ts
renderSettings: {
  ratio: '1:1',
  templateId: DEFAULT_SHORTFORM_TEMPLATE_PRESET_ID,
  compositionMode: 'clipper-template',
  titleVisibility: {
    mainTitle: true,
    subTitle: false,
    bottomTitle: false,
    logo: false,
  },
}
```

- [ ] **Step 1: Write failing default preset and image render tests**

Assert the published preset source exposes the exact ID above, output canvas 1080×1920, and content area `{x:0,y:456,width:1080,height:1080}`.

Render adapter fixture assertions:

```js
assert.equal(prepared.renderSettings.ratio, '1:1');
assert.equal(
  prepared.renderSettings.templateId,
  DEFAULT_SHORTFORM_TEMPLATE_PRESET_ID,
);
assert.deepEqual(
  prepared.clips.flatMap((clip) => clip.mediaPool.assets)
    .map((asset) => asset.kind),
  Array(10).fill('media.image'),
);
assert.deepEqual(
  prepared.clips.flatMap((clip) => clip.mediaSlots)
    .map((slot) => slot.motionPreset),
  expectedMotionCycle,
);
```

- [ ] **Step 2: Export and verify the default preset constant**

Use the same constant in both published preset source tests and Director adapter. Do not duplicate the literal in application code.

- [ ] **Step 3: Generalize render readiness by generated media kind**

Image projects require:

- TTS-aligned narration ready;
- one ready image job for every generated-image shot;
- active revision pointing to each ready local asset.

Video projects keep their current audio/duration checks. Image assets do not require source audio or MP4 duration validation.

- [ ] **Step 4: Map image assets into the existing Clipper project**

For each image shot:

```ts
assets.push({
  artifactId: `director-image.${job.revisionId}`,
  label: shot.intent,
  kind: 'media.image',
  providerId: job.model,
  mediaType: job.asset.mediaType,
  width: 1024,
  height: 1024,
  sourcePath: localAssetPath(job.asset.relativePath),
  sizeBytes: job.asset.sizeBytes,
  checksum: job.asset.checksum,
});

mediaSlots.push({
  id: `slot.${beat.id}.${shotIndex}`,
  clipId: beat.id,
  assetId,
  startMs: shot.startMs - beat.startMs,
  endMs: shot.startMs - beat.startMs + shot.durationMs,
  fit: 'fill',
  motionPreset: shot.motionPreset,
});
```

Keep `clipperMainTitleLines`, narration lines, subtitles, TTS settings, BGM, effects, standard render queue, render history, and archive integration unchanged.

- [ ] **Step 5: Add explicit video regression assertions**

Existing Gemini/Seedance/Veo fixture must still use:

```js
assert.equal(renderSettings.ratio, 'full');
assert.equal(
  renderSettings.templateId,
  FIRST_FAMILY_FULL_TEMPLATE_PRESET_ID,
);
assert.ok(allVideoAssets.every((asset) => asset.kind === 'media.video'));
```

Also start a second final render from the same ready image project and assert
that it creates a new standard render revision while the Web image client has
zero additional create calls.

- [ ] **Step 6: Run focused render tests**

Run:

```bash
cd desktop/clipper_nestjs
npm run build
node --test test/template-builder-default-shortform-family.test.js test/shortform-director-clipper-render-adapter.test.js test/shortform-director-final-render-service.test.js test/project-detail-builder-shortform-director.test.js test/shortform-director-ai-video-service.test.js
git diff --check
```

Expected: image render uses the standard 1:1 Clipper preset and motion effects; video render remains Full.

---

### Task 10: Cross-repository regression verification and manual smoke checklist

**Files:**
- Modify only if a discovered contract mismatch requires it: `.codex/design/2026-08-07-shortform-director-nano-banana-image-production-design.md`
- Create: `.codex/design/2026-08-07-shortform-director-nano-banana-image-production-review.md`

**Interfaces:**
- Consumes every prior task.
- Produces an evidence report listing commands, pass/fail counts, unverified manual items, and no claim of a paid provider smoke unless the user actually approved and ran it.

- [ ] **Step 1: Run complete focused Web API verification**

```bash
cd web/clipper_web_api
npm run build
npm test -- --runInBand src/modules/shortform-director-production src/modules/shortform-director-image-generation src/modules/shortform-director-inference src/core/database/user.datasource.spec.ts src/core/database/migrations/user/1786100000000-CreateShortformDirectorAiImageJobs.spec.ts
git diff --check
```

- [ ] **Step 2: Run complete focused Desktop Nest verification**

```bash
cd desktop/clipper_nestjs
npm run build
node --test test/shortform-director-generated-media-production.test.js test/shortform-director-project-production-state.test.js test/shortform-director-candidate-production.test.js test/shortform-director-video-plan.test.js test/shortform-director-tts-timing-alignment.test.js test/shortform-director-narration-service.test.js test/shortform-director-ai-image-job.test.js test/shortform-director-generated-image-storage.test.js test/shortform-director-ai-image-client.test.js test/shortform-director-ai-image-service.test.js test/shortform-director-ai-image-controller.test.js test/shortform-director-clipper-render-adapter.test.js test/shortform-director-final-render-service.test.js test/shortform-director-ai-video-service.test.js
git diff --check
```

- [ ] **Step 3: Run complete focused Angular verification**

```bash
cd desktop/clipper_angular
npm run build
npm test -- --watch=false --browsers=ChromeHeadless --include=src/features/shortform-director
git diff --check
```

Do not run the Electron packaged-app build.

- [ ] **Step 4: Inspect all three repository diffs for scope**

Verify:

- no new package dependency;
- no Web Admin change;
- no credential secret in logs, errors, DB public response, or UI;
- no automatic Google retry;
- no image job created during storyboard/TTS;
- no existing video config rewritten on read;
- no Full-template behavior change for video projects;
- no raw hex/rgba in new Angular SCSS.

- [ ] **Step 5: Prepare the manual application smoke checklist**

The review document must leave these unchecked for the user-built app:

```text
[ ] 새 스토리보드에서 Nano Banana 2 선택
[ ] Clipper 템플릿 방식만 표시
[ ] 30초·5 scene에서 이미지 10~12개와 정확한 총 예상 비용 표시
[ ] 비용 승인 전 Google 호출 없음
[ ] 한 이미지 승인·성공 후 1024×1024 thumbnail 표시
[ ] 한 이미지 실패가 성공한 다른 이미지를 지우지 않음
[ ] 앱 재시작 후 상태·thumbnail 복구
[ ] TTS 생성 후 이미지 수는 그대로이고 타임라인만 재정렬
[ ] 최종 렌더가 기존 실행 큐에 들어감
[ ] 결과가 AI 숏폼 디렉터와 프로젝트 보관함에 표시
[ ] 최종 영상은 기본 1:1 템플릿, 타이틀, 자막, TTS, BGM·효과음 사용
[ ] zoom-in → pan-left → pan-right 반복 확인
[ ] 기존 Omni/Seedance/Veo 프로젝트는 Full 템플릿 유지
```

- [ ] **Step 6: Record verification truthfully**

Write the exact command outputs and any environment-limited failures in the review. Do not mark actual Gemini generation or packaged-app rendering complete unless the user explicitly runs and confirms them.

---

## Execution Order

```text
Task 1 config/persistence
  → Task 2 storyboard image shots
  → Task 3 Gemini transport
  → Task 4 Web persisted job
  → Task 5 Desktop job/storage
  → Task 6 Desktop orchestration
  → Task 7 selection/storyboard UI
  → Task 8 generation UI
  → Task 9 existing Clipper render seam
  → Task 10 regression verification
```

Task 3 can be implemented after Task 1 without waiting for Task 2, but this plan keeps one sequential execution path so shared dirty worktrees are easier to review. Each task ends green and leaves the repositories uncommitted until the user requests a commit.
