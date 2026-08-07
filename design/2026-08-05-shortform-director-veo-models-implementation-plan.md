# Shortform Director Veo Models Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add selectable Veo 3.1 Lite Generate and Veo 3.1 Fast Generate models, generate 720p 9:16 clips in supported 4/6/8-second provider requests, and base user cost approval on the provider-requested duration.

**Architecture:** Extend the existing AI-video capability snapshots in Web API, Desktop Nest, and Angular. Add one Google Veo long-running-operation transport to Web API and reuse the existing persisted provider resource column so jobs survive restart without a migration. Keep the planned storyboard duration separate from the rounded provider duration so final Clipper rendering trims excess tail time.

**Tech Stack:** NestJS 11 + Jest + TypeORM (`clipper_web_api`), NestJS 10 + `node:test` + local JSON (`clipper_nestjs`), Angular 19 + Material + Karma/Jasmine (`clipper_angular`).

## Global Constraints

- User-facing models are exactly `Veo 3.1 Lite Generate` and `Veo 3.1 Fast Generate`.
- Internal selection IDs are `veo-3.1-lite` and `veo-3.1-fast`.
- Provider model IDs are `veo-3.1-lite-generate-preview` and `veo-3.1-fast-generate-preview`.
- Both models output 720×1280, 9:16 video.
- Provider request duration is one of 4, 6, or 8 seconds and never exceeds 8 seconds.
- A storyboard scene may contain multiple shots; do not add Veo extension or concatenate provider generations into one logical request.
- Preserve planned duration and trim a longer provider result during existing final rendering.
- Lite pricing snapshot is USD 0.05/second; Fast is USD 0.10/second.
- Use the existing Google AI runtime credential; do not add Web Admin fields.
- Do not add a DB migration; store a Veo operation name in the existing `provider_file_id` provider-resource column.
- Do not call paid providers during tests.
- Do not run `npm run build:app:mac:arm64:local-api`; the user performs packaged builds.
- Do not commit or push unless the user explicitly requests it.
- Preserve unrelated dirty-worktree changes.

---

### Task 1: Extend the Web API model and OpenAPI contracts

**Files:**
- Modify: `web/clipper_web_api/src/modules/shortform-director-production/domain/shortform-director-production-capability-catalog.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-production/domain/shortform-director-production-capability-catalog.spec.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-video-generation/presentation/dto/create-ai-video-job.dto.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-video-generation/presentation/shortform-director-video-generation.controller.spec.ts`
- Modify: `web/clipper_web_api/docs/api/openapi.yaml`
- Modify: `web/clipper_web_api/src/modules/shortform-director-video-generation/presentation/shortform-director-video-generation.openapi.spec.ts`

**Interfaces:**
- Produces: `AiVideoModelId = 'gemini-omni' | 'seedance-2.0' | 'veo-3.1-lite' | 'veo-3.1-fast'`.
- Produces: catalog entries whose provider is `google-veo`, duration is 4–8 seconds, and rates are 0.05/0.10.
- Consumed by: Web job validation, Desktop capability snapshots, and Angular model selectors.

- [ ] **Step 1: Write failing catalog and OpenAPI expectations**

Add exact catalog expectations:

```ts
expect(aiVideoModels()).toEqual(expect.arrayContaining([
  expect.objectContaining({
    id: 'veo-3.1-lite',
    displayName: 'Veo 3.1 Lite Generate',
    provider: 'google-veo',
    providerModelId: 'veo-3.1-lite-generate-preview',
    minDurationSeconds: 4,
    maxDurationSeconds: 8,
    estimatedUsdPerSecond: 0.05,
  }),
  expect.objectContaining({
    id: 'veo-3.1-fast',
    displayName: 'Veo 3.1 Fast Generate',
    provider: 'google-veo',
    providerModelId: 'veo-3.1-fast-generate-preview',
    minDurationSeconds: 4,
    maxDurationSeconds: 8,
    estimatedUsdPerSecond: 0.1,
  }),
]));
```

Change the OpenAPI enum expectation to:

```ts
expect(request.properties.model.enum).toEqual([
  'gemini-omni',
  'seedance-2.0',
  'veo-3.1-lite',
  'veo-3.1-fast',
]);
```

- [ ] **Step 2: Run focused tests and confirm RED**

Run:

```bash
cd web/clipper_web_api
npm test -- --runInBand \
  src/modules/shortform-director-production/domain/shortform-director-production-capability-catalog.spec.ts \
  src/modules/shortform-director-video-generation/presentation/shortform-director-video-generation.openapi.spec.ts
```

Expected: FAIL because both model IDs and OpenAPI enum entries are absent.

- [ ] **Step 3: Add the two catalog entries and DTO/OpenAPI enum values**

Extend the types without changing the existing default:

```ts
export type AiVideoModelId =
  | 'gemini-omni'
  | 'seedance-2.0'
  | 'veo-3.1-lite'
  | 'veo-3.1-fast';
```

Add both generated-media implementation IDs and selectable entries. Extend
`CreateAiVideoJobDto.model`, `ShortformDirectorAiVideoModel.id`,
`CreateShortformDirectorAiVideoJob.model`, and
`ShortformDirectorAiVideoJob.model` with the same four selection IDs. Extend
the catalog schema with:

```yaml
displayName:
  enum:
    - Gemini Omni
    - Seedance 2.0
    - Veo 3.1 Lite Generate
    - Veo 3.1 Fast Generate
provider:
  enum: [gemini, fal, google-veo]
providerModelId:
  enum:
    - gemini-omni-flash-preview
    - bytedance/seedance-2.0/text-to-video
    - veo-3.1-lite-generate-preview
    - veo-3.1-fast-generate-preview
```

Allow `ShortformDirectorAiVideoModel.maxDurationSeconds` to be as low as 8.
Keep the job request duration schema at the overall 3–15 boundary; the service
performs model-specific validation. Update the controller catalog test to
expect all four model IDs.

- [ ] **Step 4: Run focused tests and confirm GREEN**

Run the command from Step 2. Expected: PASS.

---

### Task 2: Add the Google Veo long-running-operation transport

**Files:**
- Create: `web/clipper_web_api/src/modules/shortform-director-video-generation/infrastructure/veo-video.transport.ts`
- Create: `web/clipper_web_api/src/modules/shortform-director-video-generation/infrastructure/veo-video.transport.spec.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-video-generation/domain/ai-video-generation.transport.ts`

**Interfaces:**
- Produces:

```ts
export interface VeoVideoSubmission {
  provider: 'google-veo';
  providerRequestId: string;
  operationName: string;
  requestedDurationSeconds: 4 | 6 | 8;
}
```

- Produces: `VeoVideoTransport.submit`, `inspect`, and `download`.
- Consumes: existing `AI_VIDEO_FETCH`, `productionPrompt`, safe provider error parsing, and MP4 download parsing.

- [ ] **Step 1: Write transport tests with mocked fetch**

Cover both model URLs, exact request body, polling, error status, and download:

```ts
expect(fetcher).toHaveBeenCalledWith(
  'https://generativelanguage.googleapis.com/v1beta/models/'
    + 'veo-3.1-lite-generate-preview:predictLongRunning',
  expect.objectContaining({
    method: 'POST',
    body: JSON.stringify({
      instances: [{ prompt: expect.any(String) }],
      parameters: {
        numberOfVideos: 1,
        resolution: '720p',
        aspectRatio: '9:16',
        durationSeconds: 8,
      },
    }),
  }),
);
expect(submission).toEqual({
  provider: 'google-veo',
  providerRequestId:
    'veo-515698846fc170de0934ce730509b3c56d08fd96c89270df005e7d752c822a95',
  operationName: 'operations/veo-operation-1',
  requestedDurationSeconds: 8,
});
```

Use planned durations `3.2`, `5.1`, and `7.019` to prove rounding to 4, 6,
and 8. Mock a completed operation with
`response.generateVideoResponse.generatedSamples[0].video.uri`, then assert
the URI is fetched with `x-goog-api-key`.

- [ ] **Step 2: Run the new test and confirm RED**

Run:

```bash
cd web/clipper_web_api
npm test -- --runInBand \
  src/modules/shortform-director-video-generation/infrastructure/veo-video.transport.spec.ts
```

Expected: FAIL because the transport and submission type do not exist.

- [ ] **Step 3: Implement duration selection and the transport**

Use one deterministic helper:

```ts
export function veoRequestedDurationSeconds(value: number): 4 | 6 | 8 {
  if (value <= 4) return 4;
  if (value <= 6) return 6;
  if (value <= 8) return 8;
  throw new AiVideoProviderError(
    'PROVIDER_RESPONSE_INVALID',
    'Veo duration is outside the supported range.',
  );
}
```

`submit` must choose the provider model from the selection ID, call
`:predictLongRunning`, validate a non-empty operation name, store that name
only in `operationName`, and expose
`providerRequestId = "veo-" + sha256(operationName)`.
`inspect` must map unfinished operations to `processing`, completed operations
with a video URI to `ready`, and completed operation errors to `failed`.
`download` must re-read the completed operation, accept only an HTTPS Google
video URI, and pass the response through `videoDownload`.

- [ ] **Step 4: Run the transport test and confirm GREEN**

Run the command from Step 2. Expected: PASS.

---

### Task 3: Route and persist Veo Web API jobs

**Files:**
- Modify: `web/clipper_web_api/src/modules/shortform-director-video-generation/application/shortform-director-video-generation.service.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-video-generation/application/shortform-director-video-generation.service.spec.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-video-generation/infrastructure/ai-video-job.entity.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-video-generation/infrastructure/typeorm-ai-video-job.repository.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-video-generation/infrastructure/typeorm-ai-video-job.repository.spec.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-video-generation/shortform-director-video-generation.module.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-video-generation/shortform-director-video-generation.module.spec.ts`

**Interfaces:**
- Consumes: `VeoVideoTransport` and `VeoVideoSubmission`.
- Produces: persisted jobs with `provider = 'google-veo'` and operation name in `provider_file_id`.
- Produces: restart-safe `get` and `result` routing based on persisted submission type.

- [ ] **Step 1: Add failing service and repository cases**

Assert that Lite and Fast:

```ts
expect(googleCredentials.resolveRuntimeCredential).toHaveBeenCalled();
expect(falCredentials.resolveRuntimeCredential).not.toHaveBeenCalled();
expect(veo.submit).toHaveBeenCalledWith(
  expect.objectContaining({ model: 'veo-3.1-fast' }),
);
```

Round-trip a repository entity:

```ts
provider: 'google-veo',
providerFileId: 'operations/veo-operation-1',
model: 'veo-3.1-lite',
providerRequestedDurationSeconds: 8,
```

and assert the reconstructed domain submission contains
`operationName: 'operations/veo-operation-1'`.

- [ ] **Step 2: Run focused tests and confirm RED**

Run:

```bash
cd web/clipper_web_api
npm test -- --runInBand \
  src/modules/shortform-director-video-generation/application/shortform-director-video-generation.service.spec.ts \
  src/modules/shortform-director-video-generation/infrastructure/typeorm-ai-video-job.repository.spec.ts \
  src/modules/shortform-director-video-generation/shortform-director-video-generation.module.spec.ts
```

Expected: FAIL because the new transport is not injected, routed, or persisted.

- [ ] **Step 3: Implement model-based routing and persistence**

Inject `VeoVideoTransport`. Route transport and credential explicitly:

```ts
switch (model) {
  case 'gemini-omni':
    return { credential: 'google', transport: this.gemini };
  case 'seedance-2.0':
    return { credential: 'fal', transport: this.seedance };
  case 'veo-3.1-lite':
  case 'veo-3.1-fast':
    return { credential: 'google', transport: this.veo };
}
```

Do not retain the current `Gemini else Seedance` ternaries. Register the Veo
transport in the module. Extend the entity provider union to
`'gemini' | 'fal' | 'google-veo'`. Persist `operationName` in
`providerFileId`, reconstruct it after a repository reload, and require the
field for both `gemini` and `google-veo`. A new Veo submission starts in
`processing`; only FAL queue submissions start in `queued`.

- [ ] **Step 4: Run focused tests and confirm GREEN**

Run the command from Step 2. Expected: PASS.

- [ ] **Step 5: Run the Web API feature suite and build**

Run:

```bash
cd web/clipper_web_api
npm test -- --runInBand src/modules/shortform-director-video-generation
npm run build
```

Expected: all video-generation tests and TypeScript build pass without a
provider call.

---

### Task 4: Extend Desktop Nest capability, parsing, and cost approval

**Files:**
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/domain/ai-video-production.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/domain/ai-video-job.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-ai-video.service.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-ai-video-web-api.client.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/presentation/dto/start-shortform-director-candidate-production.dto.ts`
- Modify: `desktop/clipper_nestjs/test/shortform-director-ai-video-job.test.js`
- Modify: `desktop/clipper_nestjs/test/shortform-director-ai-video-client.test.js`
- Modify: `desktop/clipper_nestjs/test/shortform-director-ai-video-service.test.js`
- Modify: `desktop/clipper_nestjs/test/shortform-director-candidate-production.test.js`

**Interfaces:**
- Produces: Desktop `AiVideoModel` union with both Veo selection IDs.
- Produces:

```ts
export function aiVideoProviderRequestedDurationSeconds(
  model: AiVideoModel,
  plannedDurationSeconds: number,
): number;
```

- Consumed by: storyboard planning constraints, job approval fingerprints, Web API submission, and stored-job parsing.

- [ ] **Step 1: Add failing capability and cost tests**

Add assertions:

```js
assert.deepEqual(aiVideoModelCapability('veo-3.1-lite'), {
  displayName: 'Veo 3.1 Lite Generate',
  provider: 'google_ai',
  modelId: 'veo-3.1-lite-generate-preview',
  output: { width: 720, height: 1280, aspectRatio: '9:16' },
  shotDurationSec: { minimum: 4, maximum: 8 },
  estimatedCostUsdPerSecond: 0.05,
});
assert.equal(
  aiVideoProviderRequestedDurationSeconds('veo-3.1-fast', 7.019),
  8,
);
```

Create a Fast project with a 7.019-second shot and assert preflight keeps
`durationSeconds === 7.019` but returns `estimatedCostUsd === 0.8`.

- [ ] **Step 2: Build and run focused tests to confirm RED**

Run:

```bash
cd desktop/clipper_nestjs
npm run build
node --test \
  test/shortform-director-ai-video-job.test.js \
  test/shortform-director-ai-video-client.test.js \
  test/shortform-director-ai-video-service.test.js \
  test/shortform-director-candidate-production.test.js
```

Expected: build or tests fail on the missing model IDs/helper.

- [ ] **Step 3: Add model snapshots and deterministic request-duration calculation**

Extend all strict model/provider-model parsers and the DTO enum. Implement:

```ts
export function aiVideoProviderRequestedDurationSeconds(
  model: AiVideoModel,
  plannedDurationSeconds: number,
): number {
  if (model === 'veo-3.1-lite' || model === 'veo-3.1-fast') {
    if (plannedDurationSeconds <= 4) return 4;
    if (plannedDurationSeconds <= 6) return 6;
    if (plannedDurationSeconds <= 8) return 8;
    throw new AiVideoProductionConfigError(
      'AI video duration exceeds the selected model',
    );
  }
  return model === 'seedance-2.0'
    ? Math.ceil(plannedDurationSeconds)
    : plannedDurationSeconds;
}
```

In `plannedJob`, preserve `durationSeconds` but calculate approval cost from
the helper result:

```ts
const providerDurationSeconds =
  aiVideoProviderRequestedDurationSeconds(config.model, durationSeconds);
const estimatedCostUsd = roundUsd(
  providerDurationSeconds * capability.estimatedCostUsdPerSecond,
);
```

The Web API request still carries planned duration; its provider transport
performs the same deterministic rounding and returns the actual
`providerRequestedDurationSeconds`.

- [ ] **Step 4: Run focused tests and confirm GREEN**

Run the command from Step 2. Expected: PASS.

---

### Task 5: Add both Veo choices to Angular

**Files:**
- Modify: `desktop/clipper_angular/src/features/shortform-director/models/shortform-director-production.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/models/shortform-director-production.spec.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/production-setup-card/production-setup-card.component.html`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/production-setup-card/production-setup-card.component.spec.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/pages/production-page/production-page.component.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/pages/production-page/production-page.component.spec.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/ai-video-production-card/ai-video-production-card.component.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/testing/shortform-director-production.fixtures.ts`

**Interfaces:**
- Consumes: the four-model Desktop API contract.
- Produces: four selectable model buttons and type-safe production/preflight/job parsing.

- [ ] **Step 1: Add failing UI expectations**

Assert the setup card contains:

```ts
expect(text).toContain('Veo 3.1 Lite Generate');
expect(text).toContain('Veo 3.1 Fast Generate');
expect(
  root.querySelector('[data-model="veo-3.1-lite"]'),
).not.toBeNull();
expect(
  root.querySelector('[data-model="veo-3.1-fast"]'),
).not.toBeNull();
expect(text.match(/컷당 최대 8초/g)?.length).toBe(2);
```

Click Fast and assert the emitted selection is `veo-3.1-fast`.

- [ ] **Step 2: Run focused Angular tests and confirm RED**

Run:

```bash
cd desktop/clipper_angular
npm test -- --watch=false --browsers=ChromeHeadless \
  --include='src/features/shortform-director/models/shortform-director-production.spec.ts' \
  --include='src/features/shortform-director/components/production-setup-card/production-setup-card.component.spec.ts' \
  --include='src/features/shortform-director/pages/production-page/production-page.component.spec.ts'
```

Expected: FAIL because the Veo labels and model buttons are absent.

- [ ] **Step 3: Extend model unions and render both buttons**

Use:

```ts
export type AiVideoModel =
  | 'gemini-omni'
  | 'seedance-2.0'
  | 'veo-3.1-lite'
  | 'veo-3.1-fast';
```

Extend `AiVideoModelCapability.displayName` and `modelId` unions. Add two
Material buttons following the current model-button markup, with 720p, 9:16,
and maximum 8-second descriptions. Change the page `selectModel` parameter to
`AiVideoModel` rather than repeating a literal union. Replace the
AI-production card's binary Seedance/Gemini display-name ternary with an
exhaustive four-model label function.

- [ ] **Step 4: Run focused Angular tests and confirm GREEN**

Run the command from Step 2. Expected: PASS.

---

### Task 6: Cross-repository Veo regression verification

**Files:**
- Verify only.

**Interfaces:**
- Consumes: Tasks 1–5.
- Produces: evidence that all four models compile and existing Omni/Seedance paths remain intact.

- [ ] **Step 1: Verify Web API**

```bash
cd web/clipper_web_api
npm test -- --runInBand \
  src/modules/shortform-director-production/domain/shortform-director-production-capability-catalog.spec.ts \
  src/modules/shortform-director-video-generation
npm run build
```

- [ ] **Step 2: Verify Desktop Nest**

```bash
cd desktop/clipper_nestjs
npm run build
node --test \
  test/shortform-director-ai-video-job.test.js \
  test/shortform-director-ai-video-client.test.js \
  test/shortform-director-ai-video-service.test.js \
  test/shortform-director-candidate-production.test.js
```

- [ ] **Step 3: Verify Angular**

```bash
cd desktop/clipper_angular
npm test -- --watch=false --browsers=ChromeHeadless \
  --include='src/features/shortform-director/models/shortform-director-production.spec.ts' \
  --include='src/features/shortform-director/components/production-setup-card/production-setup-card.component.spec.ts' \
  --include='src/features/shortform-director/pages/production-page/production-page.component.spec.ts'
npm run build
```

Expected: every command exits 0. Do not run a provider smoke call or packaged
Electron build.
