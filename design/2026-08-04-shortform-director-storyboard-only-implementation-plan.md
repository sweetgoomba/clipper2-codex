# Shortform Director Storyboard-Only Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Execution status (2026-08-04):** Implemented locally on the three matching
`feat/shortform-director-storyboard-only` branches. No commit or push was
created. Web API (986 tests), Angular (1,720 tests), both production builds,
Desktop Nest clean build, all 505 Director tests, and 16 directly affected
`ProjectsService` tests pass. The full Desktop Nest legacy suite still contains
unrelated authentication-fixture and variation/TTS-mock failures; no paid
provider E2E was run.

**Goal:** Preserve the existing Shortform Director through candidate-specific storyboard generation while physically removing every asset, narration, render, and completed-output path.

**Architecture:** Keep the existing `candidate-production` preflight, two inference calls, compiler, `ShortformDirectorProject` schema, JSON repository, and artifact lineage. Remove downstream runtime registrations and files in Web API and Desktop Nest, then reduce Angular's production page to a read-only storyboard page while leaving all upstream screens unchanged.

**Tech Stack:** NestJS 11 + Jest (`clipper_web_api`), NestJS 10 + `node:test` (`clipper_nestjs`), Angular 19 + Angular Material + Karma/Jasmine (`clipper_angular`), local JSON persistence.

## Global Constraints

- Base every target repository on its current clean `feat/shortform-director-foundation` head.
- Use the same new branch name in all changed code repositories: `feat/shortform-director-storyboard-only`.
- Do not create a worktree.
- Do not commit or push unless the user explicitly requests it.
- Do not change `ShortformDirectorProject` or migrate existing local JSON.
- Keep `video-plan` and `scene-media-decision`; remove all later paid or local production operations.
- Keep existing profile, research, reference, topic, candidate, run, and artifact behavior unchanged.
- User-facing copy says “스토리보드”; internal `candidate-production` names may remain.
- The first storyboard screen is read-only.
- Do not call an external provider during automated verification.
- Preserve raw Nest responses and existing error shapes.

---

### Task 1: Create Matching Branches and Record the Baseline

**Files:**
- Verify only; no source files changed.

**Interfaces:**
- Consumes: clean local `feat/shortform-director-foundation` branches at Web API `29871e7`, Desktop Nest `a578dce`, and Angular `c82489a`.
- Produces: three local `feat/shortform-director-storyboard-only` branches at the same starting commits.

- [ ] **Step 1: Verify exact clean bases**

Run in each target repository:

```bash
git status --short --branch
git rev-parse --short HEAD
git rev-list --left-right --count '@{upstream}...HEAD'
```

Expected:

```text
web/clipper_web_api       feat/shortform-director-foundation  29871e7  0 0
desktop/clipper_nestjs    feat/shortform-director-foundation  a578dce  0 0
desktop/clipper_angular   feat/shortform-director-foundation  c82489a  0 0
```

- [ ] **Step 2: Create the matching branches**

Run in each target repository:

```bash
git switch -c feat/shortform-director-storyboard-only
```

Expected: each repository reports a new branch based on its current foundation HEAD.

- [ ] **Step 3: Run focused retained-flow baselines**

Run:

```bash
# web/clipper_web_api
npm test -- --runInBand \
  src/modules/shortform-director-inference/domain/shortform-director-inference.contract.spec.ts \
  src/modules/shortform-director-inference/presentation/shortform-director-inference.controller.spec.ts

# desktop/clipper_nestjs
npm run build
node --test \
  test/shortform-director-candidate-generation.test.js \
  test/shortform-director-candidate-production.test.js

# desktop/clipper_angular
npm test -- --watch=false --browsers=ChromeHeadless \
  --include='src/features/shortform-director/shortform-director-registration.spec.ts' \
  --include='src/features/shortform-director/pages/production-page/production-page.component.spec.ts'
```

Expected: all selected baseline tests pass before deletion work starts.

---

### Task 2: Remove the Web API Generated-Media Runtime

**Files:**
- Modify: `web/clipper_web_api/src/app.module.ts`
- Create: `web/clipper_web_api/src/app.module.spec.ts`
- Delete: `web/clipper_web_api/src/modules/shortform-director-assets/`
- Delete:
  - `web/clipper_web_api/src/modules/shortform-director-production/application/shortform-director-production-capability.service.ts`
  - `web/clipper_web_api/src/modules/shortform-director-production/application/shortform-director-production-capability.service.spec.ts`
  - `web/clipper_web_api/src/modules/shortform-director-production/presentation/shortform-director-production-capability.controller.ts`
  - `web/clipper_web_api/src/modules/shortform-director-production/presentation/shortform-director-production-capability.controller.spec.ts`
  - `web/clipper_web_api/src/modules/shortform-director-production/presentation/shortform-director-production-capability.openapi.spec.ts`
  - `web/clipper_web_api/src/modules/shortform-director-production/shortform-director-production.module.ts`
- Retain:
  - `web/clipper_web_api/src/modules/shortform-director-production/domain/shortform-director-production-capability-catalog.ts`
  - `web/clipper_web_api/src/modules/shortform-director-production/domain/shortform-director-production-capability-catalog.spec.ts`

**Interfaces:**
- Consumes: `ShortformDirectorInferenceModule` and its imports of `inferenceImplementation()` from the retained catalog.
- Produces: an `AppModule` with inference and storyboard capabilities but no generated-media or public production-capability module.

- [ ] **Step 1: Write a failing AppModule boundary test**

Create `src/app.module.spec.ts`:

```ts
import { MODULE_METADATA } from '@nestjs/common/constants';
import { AppModule } from './app.module.js';
import { ShortformDirectorAssetsModule } from './modules/shortform-director-assets/shortform-director-assets.module.js';
import { ShortformDirectorProductionModule } from './modules/shortform-director-production/shortform-director-production.module.js';

describe('AppModule storyboard-only boundary', () => {
  it('does not register generated-media or production-capability runtimes', () => {
    const imports = Reflect.getMetadata(
      MODULE_METADATA.IMPORTS,
      AppModule,
    ) as unknown[];
    expect(imports).not.toContain(ShortformDirectorAssetsModule);
    expect(imports).not.toContain(ShortformDirectorProductionModule);
  });
});
```

- [ ] **Step 2: Run the test and verify the boundary fails**

Run:

```bash
npm test -- --runInBand src/app.module.spec.ts
```

Expected: FAIL because both modules are currently registered.

- [ ] **Step 3: Remove runtime registrations**

Delete these imports and entries from `src/app.module.ts`:

```ts
import { ShortformDirectorAssetsModule } from './modules/shortform-director-assets/shortform-director-assets.module.js';
import { ShortformDirectorProductionModule } from './modules/shortform-director-production/shortform-director-production.module.js';
```

and:

```ts
ShortformDirectorAssetsModule,
ShortformDirectorProductionModule,
```

Update the boundary test to avoid importing deleted modules. It must inspect
registered module class names instead:

```ts
const names = imports.map((value) =>
  typeof value === 'function' ? value.name : '',
);
expect(names).not.toContain('ShortformDirectorAssetsModule');
expect(names).not.toContain('ShortformDirectorProductionModule');
expect(names).toContain('ShortformDirectorInferenceModule');
```

- [ ] **Step 4: Delete the generated-media and routable capability files**

Delete the exact files/directories listed for this task. Do not delete the
production capability catalog because generic inference still imports its
implementation IDs and pricing metadata.

- [ ] **Step 5: Verify retained inference and removed runtime boundaries**

Run:

```bash
npm test -- --runInBand \
  src/app.module.spec.ts \
  src/modules/shortform-director-production/domain/shortform-director-production-capability-catalog.spec.ts \
  src/modules/shortform-director-inference/domain/shortform-director-inference.contract.spec.ts \
  src/modules/shortform-director-inference/presentation/shortform-director-inference.controller.spec.ts
npm run build
```

Expected: all tests and build pass; `video-plan` and
`scene-media-decision` remain valid inference purposes.

---

### Task 3: Lock the Desktop Nest Storyboard HTTP Boundary

**Files:**
- Create: `desktop/clipper_nestjs/test/shortform-director-storyboard-only-boundary.test.js`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/presentation/shortform-director-project.controller.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/shortform-director.module.ts`

**Interfaces:**
- Consumes: `ShortformDirectorCandidateProductionController`,
  `ShortformDirectorCandidateProductionService`, and the retained project
  repository.
- Produces: registered routes through candidate-production result/project
  retrieval and no routes for assets, narration, regeneration, render, or
  output.

- [ ] **Step 1: Write the failing controller-registration test**

Create a `node:test` file that loads the built module and reads Nest route
metadata. The retained set must include:

```js
[
  'ShortformDirectorProfileController',
  'ShortformDirectorResearchController',
  'ShortformDirectorCandidateGenerationController',
  'ShortformDirectorCandidateProductionController',
  'ShortformDirectorProjectController',
]
```

The forbidden set must include:

```js
[
  'ShortformDirectorNarrationController',
  'ShortformDirectorRenderController',
  'ShortformDirectorProductionCapabilityController',
  'ShortformDirectorSceneEditController',
]
```

Assert all retained names exist and all forbidden names are absent from:

```js
const { MODULE_METADATA } = require('@nestjs/common/constants');
const controllers = Reflect.getMetadata(
  MODULE_METADATA.CONTROLLERS,
  ShortformDirectorModule,
);
```

- [ ] **Step 2: Run the test and verify it fails**

Run:

```bash
npm run build
node --test test/shortform-director-storyboard-only-boundary.test.js
```

Expected: FAIL because four forbidden controllers are still registered.

- [ ] **Step 3: Remove post-VideoPlan project endpoints**

Keep project list/create, content strategy, VideoPlan, and project read methods.
Remove controller methods and DTO imports for:

```text
GET    :projectId/asset-candidates
POST   :projectId/assets/auto-prepare
GET    :projectId/assets/preflight
PUT    :projectId/asset-bindings/:layerId
POST   :projectId/asset-bindings/:layerId/upload
PUT    :projectId/asset-bindings/:layerId/rights
DELETE :projectId/asset-bindings/:layerId
GET    :projectId/render-recipe
POST   :projectId/render-input-stage
```

The last retained planning mutation is:

```text
POST :projectId/video-plan
```

- [ ] **Step 4: Remove downstream controllers and providers from the module**

Remove controller registration for narration, render, production capability,
and scene edit. Remove their imports.

Remove provider registrations for:

```text
ShortformDirectorAssetService
ShortformDirectorAutomaticAssetService
ShortformDirectorLayerAssetExecutor
ShortformDirectorGeneratedMediaWebApiClient
ShortformDirectorNarrationService
ShortformDirectorNarrationCueSynthesizer
ShortformDirectorSceneNarrationService
ShortformDirectorProductionCapabilityService
ShortformDirectorProductionCapabilityWebApiClient
ShortformDirectorSceneEditService
ShortformDirectorProjectMutationCoordinator
ShortformDirectorSceneMediaService
ShortformDirectorRenderRecipeCompiler
ShortformDirectorRenderRecipeService
ShortformDirectorRenderInputStageService
ShortformDirectorRendererAdapterRegistry
ShortformDirectorMotionCanvasWorker
ShortformDirectorMotionCanvasRendererAdapter
ShortformDirectorRenderWorkflowExecutor
ShortformDirectorRenderOperationService
ShortformDirectorVaultPublisher
```

Remove their downstream repositories, validators, storage adapters, media
search providers, renderer multi-provider binding, and module imports
`TtsSynthesisModule`, `JobsModule`, and `PluginsModule`.

- [ ] **Step 5: Run the boundary test**

Run:

```bash
npm run build
node --test test/shortform-director-storyboard-only-boundary.test.js
```

Expected: PASS.

---

### Task 4: Delete Desktop Nest Downstream Implementations

**Files:**
- Delete application files:
  - `shortform-director-asset.service.ts`
  - `shortform-director-automatic-asset.service.ts`
  - `shortform-director-layer-asset-call-plan.ts`
  - `shortform-director-layer-asset-executor.ts`
  - `shortform-director-narration-cue-synthesizer.ts`
  - `shortform-director-narration.service.ts`
  - `shortform-director-production-capability-web-api.client.ts`
  - `shortform-director-production-capability.service.ts`
  - `shortform-director-render-input-stage.service.ts`
  - `shortform-director-render-operation.service.ts`
  - `shortform-director-render-recipe.compiler.ts`
  - `shortform-director-render-recipe.service.ts`
  - `shortform-director-render-workflow.executor.ts`
  - `shortform-director-renderer-adapter.registry.ts`
  - `shortform-director-scene-edit.service.ts`
  - `shortform-director-scene-media.service.ts`
  - `shortform-director-scene-narration.service.ts`
  - `shortform-director-vault-publisher.service.ts`
- Delete downstream domain ports:
  - `domain/project-regeneration-operation-audit.repository.ts`
  - `domain/scene-media-revision.repository.ts`
  - `domain/shortform-director-renderer-adapter.ts`
- Retain compatibility model and pure transformation files:
  - `domain/asset-pack.ts`
  - `domain/asset-acquisition.ts`
  - `domain/asset-production-readiness.ts`
  - `domain/narration-audio.ts`
  - `domain/production-state.ts`
  - `domain/scene-production.ts`
  - all narration, render, revision, and renderer value types referenced by
    `ShortformDirectorProject`
  - `domain/shortform-director.model.ts`
- Delete downstream infrastructure:
  - local asset, narration, render input, render output, vault storage
  - Motion Canvas and Remotion adapters/workers
  - narration, render, regeneration, and scene-media artifact validators
- Delete downstream presentation:
  - narration, render, production capability, and scene-edit controllers
  - their asset, narration, regeneration, and render DTOs
- Delete these execution tests:
  - `test/shortform-director-automatic-asset-preparation.test.js`
  - `test/shortform-director-motion-canvas-poc.test.js`
  - `test/shortform-director-motion-canvas-render-integration.test.js`
  - `test/shortform-director-motion-canvas-renderer.test.js`
  - `test/shortform-director-narration-artifact-validation.test.js`
  - `test/shortform-director-narration-regeneration.test.js`
  - `test/shortform-director-production-capability.test.js`
  - `test/shortform-director-project-regeneration.test.js`
  - `test/shortform-director-remotion-render-integration.test.js`
  - `test/shortform-director-render-input-stage.test.js`
  - `test/shortform-director-render-operation.test.js`
  - `test/shortform-director-render-recipe-compiler.test.js`
  - `test/shortform-director-render-revision.test.js`
  - `test/shortform-director-renderer-adapter-foundation.test.js`
  - `test/shortform-director-renderer-conformance.test.js`
  - `test/shortform-director-scene-edit-http.test.js`
  - `test/shortform-director-scene-edit.test.js`
  - `test/shortform-director-scene-media-regeneration.test.js`
  - `test/shortform-director-scene-media-revision-activation.test.js`
  - `test/shortform-director-scene-media-revision.test.js`
  - `test/shortform-director-vault-publish.test.js`
- Retain compatibility tests:
  - `test/shortform-director-asset-acquisition.test.js`
  - `test/shortform-director-asset-pack.test.js`
  - `test/shortform-director-narration-audio.test.js`
  - pure project parsing, compiler, and JSON repository tests

**Interfaces:**
- Consumes: compatibility-only `assetPack` and `narrationAudio` types required by
  `ShortformDirectorProject`.
- Produces: a compiling Nest module whose only Director post-candidate execution
  is candidate-production storyboard generation.

- [ ] **Step 1: Delete isolated downstream source and test files**

Delete the application, domain-port, infrastructure, presentation, DTO, and
test paths listed in this task. Do not delete general `projects`, `sources`,
`jobs`, `video-render`, template-builder, variation, or shortform prompt files.

- [ ] **Step 2: Compile to expose forbidden retained references**

Run:

```bash
npm run build
```

Expected initially: TypeScript errors identify imports of deleted execution
code. Remove only references that activate or expose downstream Director
production. Do not change the retained project JSON shape.

- [ ] **Step 3: Add compatibility assertions to candidate-production tests**

In `test/shortform-director-candidate-production.test.js`, assert a successful
result still contains:

```js
assert.equal(result.schemaVersion,
  'shortform-director-candidate-production-result.v1');
assert.equal(result.project.videoPlan.scenes.length > 0, true);
assert.ok(result.project.assetPack);
assert.ok(result.project.narrationAudio);
```

Also assert the public run still ends with:

```js
assert.equal(run.kind, 'video-plan');
assert.equal(run.status, 'succeeded');
```

- [ ] **Step 4: Run retained Director tests**

Run:

```bash
npm run build
node --test \
  test/shortform-director-candidate-generation.test.js \
  test/shortform-director-candidate-production.test.js \
  test/shortform-director-storyboard-only-boundary.test.js \
  test/shortform-director-research*.test.js
```

Expected: PASS with no external provider call.

---

### Task 5: Change Angular Routing and Candidate Actions to Storyboards

**Files:**
- Modify: `desktop/clipper_angular/src/app/app.routes.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/shortform-director-registration.spec.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/shortform-director-routing.integration.spec.ts`
- Modify:
  - `components/director-sidebar/director-sidebar.component.ts`
  - `components/director-sidebar/director-sidebar.component.spec.ts`
  - `components/video-candidate-set/video-candidate-set.component.html`
  - `components/video-candidate-set/video-candidate-set.component.spec.ts`
  - `pages/candidates-page/candidates-page.component.ts`
- Delete: `desktop/clipper_angular/src/features/shortform-director/pages/outputs-page/`

**Interfaces:**
- Consumes: the existing candidate selection tuple
  `{ candidateRunId, candidateId, profileId }`.
- Produces: navigation to `/shortform/director/storyboard` and no outputs route.

- [ ] **Step 1: Change registration expectations first**

Update the expected lazy paths to:

```ts
[
  'profiles',
  'ideas',
  'candidates',
  'storyboard',
  'runs',
]
```

Update expected component names to keep the current component temporarily:

```ts
[
  'ProfilesPageComponent',
  'IdeasPageComponent',
  'CandidatesPageComponent',
  'ProductionPageComponent',
  'RunsPageComponent',
]
```

Add assertions that neither `production` nor `outputs` exists.

- [ ] **Step 2: Run routing tests and verify they fail**

Run:

```bash
npm test -- --watch=false --browsers=ChromeHeadless \
  --include='src/features/shortform-director/shortform-director-registration.spec.ts' \
  --include='src/features/shortform-director/shortform-director-routing.integration.spec.ts'
```

Expected: FAIL because the old routes still exist.

- [ ] **Step 3: Replace the route and navigation labels**

Change:

```ts
{ path: 'production', ... }
{ path: 'outputs', ... }
```

to one route:

```ts
{
  path: 'storyboard',
  loadComponent: () =>
    import('../features/shortform-director/pages/production-page/production-page.component')
      .then((m) => m.ProductionPageComponent),
}
```

The sidebar step becomes:

```ts
{ path: 'storyboard', label: '스토리보드', icon: 'view_array' }
```

Delete the completed-video step. Keep `실행 기록`.

- [ ] **Step 4: Change candidate copy and navigation**

The candidate button says `스토리보드 만들기`. The candidates page navigates
to `['/shortform/director/storyboard']` with the same opaque query parameters.
No other candidate-generation behavior changes.

- [ ] **Step 5: Run routing and candidate tests**

Run:

```bash
npm test -- --watch=false --browsers=ChromeHeadless \
  --include='src/features/shortform-director/shortform-director-registration.spec.ts' \
  --include='src/features/shortform-director/shortform-director-routing.integration.spec.ts' \
  --include='src/features/shortform-director/components/director-sidebar/director-sidebar.component.spec.ts' \
  --include='src/features/shortform-director/components/video-candidate-set/video-candidate-set.component.spec.ts' \
  --include='src/features/shortform-director/pages/candidates-page/candidates-page.component.spec.ts'
```

Expected: PASS.

---

### Task 6: Reduce Angular Production State to Storyboard Generation

**Files:**
- Modify:
  - `desktop/clipper_angular/src/features/shortform-director/state/shortform-director-production.store.ts`
  - `desktop/clipper_angular/src/features/shortform-director/state/shortform-director-production.store.spec.ts`
  - `desktop/clipper_angular/src/features/shortform-director/pages/production-page/production-page.component.ts`
  - `desktop/clipper_angular/src/features/shortform-director/pages/production-page/production-page.component.html`
  - `desktop/clipper_angular/src/features/shortform-director/pages/production-page/production-page.component.scss`
  - `desktop/clipper_angular/src/features/shortform-director/pages/production-page/production-page.component.spec.ts`
  - `desktop/clipper_angular/src/features/shortform-director/components/production-preflight-card/*`
- Create:
  - `desktop/clipper_angular/src/features/shortform-director/components/storyboard-scene-list/storyboard-scene-list.component.ts`
  - `desktop/clipper_angular/src/features/shortform-director/components/storyboard-scene-list/storyboard-scene-list.component.html`
  - `desktop/clipper_angular/src/features/shortform-director/components/storyboard-scene-list/storyboard-scene-list.component.scss`
  - `desktop/clipper_angular/src/features/shortform-director/components/storyboard-scene-list/storyboard-scene-list.component.spec.ts`

**Interfaces:**
- Consumes: unchanged `ShortformDirectorProductionGateway` methods
  `getPreflight`, `startProduction`, `getRun`, `getResult`, `getProject`, and
  `listRuns`.
- Produces: read-only rendering of `ShortformDirectorProject.videoPlan.scenes`.

- [ ] **Step 1: Write failing storyboard page tests**

The page spec must assert:

```ts
expect(text).toContain('스토리보드');
expect(text).toContain(project.title);
expect(root.querySelectorAll('app-storyboard-scene-list')).toHaveSize(1);
expect(root.querySelector('app-production-workflow')).toBeNull();
expect(root.querySelector('app-production-model-summary')).toBeNull();
expect(root.querySelector('app-production-artifact-inspector')).toBeNull();
```

The scene-list spec must assert each scene renders:

```text
scene.order
scene.intent
scene.durationMs
beat.intent
the audioTimeline narration cue text matching beat.narrationCueId
shot.intent
caption layer content where layer.role === 'caption'
visual layer assetStrategy where layer.kind === 'visual'
```

It must also assert there are no edit or regenerate buttons.

- [ ] **Step 2: Run page and scene-list tests and verify they fail**

Run:

```bash
npm test -- --watch=false --browsers=ChromeHeadless \
  --include='src/features/shortform-director/pages/production-page/production-page.component.spec.ts' \
  --include='src/features/shortform-director/components/storyboard-scene-list/storyboard-scene-list.component.spec.ts'
```

Expected: FAIL because the read-only component does not exist and production
controls still render.

- [ ] **Step 3: Trim the store**

Keep signals and methods for:

```text
selection
preflight
run
result
project
loadingPreflight
loadingProject
generatingPlan
preflightError
planError
canGeneratePlan
loadSelection
generatePlan
loadProject/run/result history needed to resume
```

Remove all state and methods for capability catalogs, artifacts, project
regeneration, assets, rights, narration, scene production, render stage, and
render operations.

- [ ] **Step 4: Implement the read-only scene list**

Use the unchanged project types. For each scene render:

```text
scene.order, scene.intent, and scene.durationMs
beat.intent
audioTimeline.narrationCues.find(cue => cue.id === beat.narrationCueId)?.text
shot.intent
shot.layers.filter(layer => layer.role === 'caption').map(layer => layer.content)
shot.layers.filter(layer => layer.kind === 'visual').map(layer => layer.assetStrategy)
```

Do not render raw evidence IDs, source claim IDs, artifact IDs, layer IDs,
provider IDs, or production readiness.

- [ ] **Step 5: Reduce the page to preflight, progress, error, and result**

The primary approval dialog copy becomes:

```text
스토리보드 생성 비용 승인
선택한 영상 후보를 장면별 스토리보드로 만들까요?
```

Keep provider, model, maximum calls, estimated cost, credential revision, and
approval ID in the existing explicit confirmation dialog details. After
success, render project title and `app-storyboard-scene-list`.

- [ ] **Step 6: Run focused Angular tests**

Run:

```bash
npm test -- --watch=false --browsers=ChromeHeadless \
  --include='src/features/shortform-director/state/shortform-director-production.store.spec.ts' \
  --include='src/features/shortform-director/pages/production-page/production-page.component.spec.ts' \
  --include='src/features/shortform-director/components/production-preflight-card/production-preflight-card.component.spec.ts' \
  --include='src/features/shortform-director/components/storyboard-scene-list/storyboard-scene-list.component.spec.ts'
```

Expected: PASS.

---

### Task 7: Delete Angular Downstream UI and HTTP Clients

**Files:**
- Delete component directories:
  - `director-render-operation-card`
  - `production-artifact-inspector`
  - `production-generated-media-strategy-form`
  - `production-layer-card`
  - `production-layer-editor`
  - `production-model-summary`
  - `production-programmatic-strategy-form`
  - `production-revision-history`
  - `production-scene-card`
  - `production-scene-content-form`
  - `production-scene-plan`
  - `production-search-strategy-form`
  - `production-source-strategy-form`
  - `production-workflow`
- Delete:
  - `models/shortform-director-production-capability.ts`
  - `models/shortform-director-scene-edit.ts`
  - `services/shortform-director-scene-production.gateway.ts`
  - `services/shortform-director-scene-production.service.ts`
  - `services/shortform-director-scene-production.service.spec.ts`
  - `state/shortform-director-scene-production.store.ts`
  - `state/shortform-director-scene-production.store.spec.ts`
- Modify:
  - `services/shortform-director-project.service.ts`
  - `services/shortform-director-project.service.spec.ts`
  - `models/shortform-director-project.ts`
  - `models/shortform-director-workspace.ts`
  - `src/app/app.config.ts`

**Interfaces:**
- Consumes: the retained candidate-production gateway and project compatibility
  types.
- Produces: no Angular call site for asset, narration, regeneration, render, or
  output endpoints.

- [ ] **Step 1: Delete downstream components, services, stores, and specs**

Delete only the exact Director paths listed above. Keep the production
preflight component, production result model, production gateway/service, and
new storyboard scene list.

- [ ] **Step 2: Trim project service HTTP methods**

Delete methods for:

```text
production capabilities
asset candidates/preflight/auto-prepare/binding/upload/rights
narration presets/audio synthesis/file
render recipe/input stage/jobs/output files
scene and layer mutations/regeneration/revisions
```

Keep only methods still referenced by candidate-production/storyboard loading.
The reduced storyboard page loads projects through
`ShortformDirectorProductionGateway.getProject(runId)`. Delete
`ShortformDirectorProjectService`, its spec, and its provider registration from
`src/app/app.config.ts`.

- [ ] **Step 3: Preserve compatibility types without executable UI helpers**

Do not remove `assetPack` or `narrationAudio` from
`ShortformDirectorProject`. Remove only models and helper functions that exist
solely for downstream execution or editing.

- [ ] **Step 4: Prove no forbidden endpoint strings remain**

Run:

```bash
rg -n \
  "auto-prepare|asset-bindings|narration-audio|render-jobs|render-outputs|render-input-stage|scene-production-state|regenerations" \
  src/features/shortform-director src/app
```

Expected: no results.

- [ ] **Step 5: Run Director tests and build**

Run:

```bash
npm test -- --watch=false --browsers=ChromeHeadless \
  --include='src/features/shortform-director/**/*.spec.ts'
npm run build
```

Expected: all Director tests and the production build pass.

---

### Task 8: Cross-Repository Verification

**Files:**
- Modify if test evidence exposes a defect: only files already in scope above.
- Do not update status or handoff documents until implementation evidence is
  complete.

**Interfaces:**
- Consumes: all prior task outputs.
- Produces: evidence that retained storyboard generation works and downstream
  production is absent.

- [ ] **Step 1: Verify Web API**

Run:

```bash
npm test -- --runInBand
npm run build
```

Expected: all suites pass and build succeeds.

- [ ] **Step 2: Verify Desktop Nest**

Run:

```bash
npm run build
node --test test/*.test.js
```

Expected: all retained suites pass, with only the already documented
environment-dependent render skips absent or irrelevant because Director render
tests were deleted.

- [ ] **Step 3: Verify Angular**

Run:

```bash
npm test -- --watch=false --browsers=ChromeHeadless
npm run build
```

Expected: all suites pass and build succeeds.

- [ ] **Step 4: Inspect repository diffs**

Run in each changed code repository:

```bash
git status --short
git diff --check
git diff --stat
git diff --name-status
```

Expected:

- no change outside the storyboard-only boundary;
- no commit or push;
- no modification to admin, Electron, Python, or legacy repositories;
- large deletions are limited to Director generated media, assets, narration,
  regeneration, render, outputs, and their tests.

- [ ] **Step 5: Report verification without claiming external E2E**

Report:

- branch names and starting heads;
- retained storyboard flow;
- removed routes and runtimes;
- exact test/build results;
- no paid provider call performed;
- any remaining compatibility-only fields or internal production names.
