# Final Render Version History Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Let a completed Shortform Director storyboard be rendered again without replacing its earlier completed final videos, while keeping the latest successful render as the default preview.

**Architecture:** Persist one pending render pointer and an ordered set of completed render pointers in each storyboard project. The NestJS final-render service owns reservation, promotion, rollback, historical authorization, and listing. Angular loads this history per project, preserves the current preview during a rerender, and switches or downloads completed versions explicitly.

**Tech Stack:** NestJS, TypeScript, Angular signals, Jasmine/Karma, Node test runner

## Global Constraints

- Preserve legacy projects that contain only `activeRenderRevisionId`.
- Allow only one pending final render per storyboard project.
- Do not change narration, shot-generation, or storyboard-generation behavior.
- Do not run paid provider operations.
- Do not run `npm run build:app:mac:arm64:local-api` or another macOS packaging build.
- Do not commit or push without an explicit user request.

---

### Task 1: Extend the persisted production state compatibly

**Files:**
- Modify: `../clipper_nestjs/src/modules/shortform-director/domain/production-state.ts`
- Modify: `../clipper_nestjs/test/shortform-director-project-production-state.test.js`

**Interfaces:**
- Persist: `pendingRenderRevisionId`
- Persist: `completedRenderRevisions[]`
- Preserve: legacy `activeRenderRevisionId`

- [ ] **Step 1: Add RED tests for empty and legacy state**

Add assertions that a newly created production state contains:

```js
assert.equal(state.pendingRenderRevisionId, null);
assert.deepEqual(state.completedRenderRevisions, []);
```

Add a hydration test whose stored JSON contains only:

```js
{
  schemaVersion: 1,
  activeRenderRevisionId: 'render.legacy'
}
```

Expect hydration to retain the active ID and supply empty defaults for the two
new fields.

- [ ] **Step 2: Add RED validation tests**

Verify that valid completed entries preserve both opaque render IDs and ISO
timestamps, and that malformed or duplicate entries are rejected by the
existing invalid-state fallback rather than leaking partially parsed data.

- [ ] **Step 3: Run the focused test**

Run:

```bash
node --test test/shortform-director-project-production-state.test.js
```

Expected: new assertions fail because the fields are not yet created or
hydrated.

- [ ] **Step 4: Implement the state contract**

In `production-state.ts`:

- add a completed revision value type;
- add optional persisted interface members so existing TypeScript fixtures do
  not require broad unrelated rewrites;
- include `pendingRenderRevisionId: null` and
  `completedRenderRevisions: []` in `createEmptyShortformDirectorProductionState`;
- hydrate absent legacy values to those defaults;
- validate every completed item with the existing opaque-ID rules and an ISO
  timestamp check;
- enforce unique render IDs and preserve dense array ordering.

- [ ] **Step 5: Re-run the focused test and verify GREEN**

Run the same Node test command and confirm it passes.

---

### Task 2: Implement pending reservation, promotion, and history access

**Files:**
- Modify: `../clipper_nestjs/src/modules/shortform-director/application/shortform-director-final-render.service.ts`
- Modify: `../clipper_nestjs/test/shortform-director-final-render-service.test.js`

**Behavior:**
- Starting a rerender preserves the prior active revision.
- Completing a pending render promotes it only after MP4 materialization.
- Failed or cancelled work clears only the matching pending pointer.
- Completed historical render IDs remain valid for status and file access.

- [ ] **Step 1: Add RED lifecycle tests**

Extend the service harness so it can seed project production state and issue
more than one render ID. Add tests proving:

```js
assert.equal(saved.production.activeRenderRevisionId, 'render.previous');
assert.equal(saved.production.pendingRenderRevisionId, 'render.next');
```

after rerender start, and after completion:

```js
assert.equal(saved.production.activeRenderRevisionId, 'render.next');
assert.equal(saved.production.pendingRenderRevisionId, null);
assert.deepEqual(
  saved.production.completedRenderRevisions.map((item) => item.renderId),
  ['render.previous', 'render.next'],
);
```

Use the project `updatedAt` as the fallback completion time for the legacy
active revision.

- [ ] **Step 2: Add RED failure and concurrency tests**

Cover:

- renderer start failure clears `render.next` but preserves
  `render.previous`;
- failed and cancelled terminal snapshots clear only the matching pending ID;
- a second `start()` while a pending ID exists throws `ConflictException`;
- a stale status observation cannot promote or clear a different pending ID.

- [ ] **Step 3: Add RED authorization and listing tests**

Cover:

- the legacy active ID and every completed-history ID can be queried;
- a historical completed file can be resolved;
- unknown IDs still return not found;
- history is newest first and marks exactly the active revision;
- failed and cancelled IDs never appear in history.

- [ ] **Step 4: Run the focused service test**

Run:

```bash
node --test test/shortform-director-final-render-service.test.js
```

Expected: the new tests fail against active-only reservation and authorization.

- [ ] **Step 5: Implement lifecycle helpers**

Refactor the service around small private helpers:

- normalize completed history, including a missing legacy active pointer;
- reserve a new pending ID with compare-and-swap;
- authorize a render when it is pending, active, or completed;
- promote a matching pending render after successful materialization;
- clear only a matching pending render after start or terminal failure.

Every compare-and-swap mutation must reload the current project and verify that
the expected pending ID still matches before writing.

- [ ] **Step 6: Implement the history result**

Add a service method returning:

```ts
{
  activeRenderRevisionId: string | null;
  pendingRenderRevisionId: string | null;
  items: Array<{
    renderId: string;
    completedAt: string;
    active: boolean;
  }>;
}
```

Return completed items only, sorted by descending `completedAt`.

- [ ] **Step 7: Re-run the focused service test and verify GREEN**

Run the same Node test command and confirm all cases pass.

---

### Task 3: Expose the completed-render list through the Desktop API

**Files:**
- Modify: `../clipper_nestjs/src/modules/shortform-director/presentation/shortform-director-final-render.controller.ts`
- Modify: `../clipper_nestjs/test/shortform-director-final-render-service.test.js` if controller-contract assertions share that harness

- [ ] **Step 1: Add the collection route**

Add:

```ts
@Get()
list(@Param('projectId') projectId: string) {
  return this.finalRenderService.list(projectId);
}
```

Keep it before the `@Get(':renderId')` route and preserve the existing start,
status, and file routes.

- [ ] **Step 2: Build and run focused NestJS tests**

Run:

```bash
npm run build
node --test test/shortform-director-project-production-state.test.js test/shortform-director-final-render-service.test.js
```

Expected: NestJS compiles and both focused suites pass.

---

### Task 4: Add Angular history contracts and transport

**Files:**
- Modify: `src/features/shortform-director/models/shortform-director-production.ts`
- Modify: `src/features/shortform-director/models/shortform-director-project.ts`
- Modify: `src/features/shortform-director/testing/shortform-director-production.fixtures.ts`
- Modify: `src/features/shortform-director/services/shortform-director-production.gateway.ts`
- Modify: `src/features/shortform-director/services/shortform-director-production.service.ts`
- Modify: `src/features/shortform-director/services/shortform-director-production.service.spec.ts`

- [ ] **Step 1: Add a RED transport test**

Call:

```ts
service.listFinalRenders('project.1');
```

Expect:

```ts
GET /v1/projects/shortform-director/projects/project.1/final-renders
```

and flush a response containing an active ID, pending ID, and completed items.

- [ ] **Step 2: Run the focused service spec**

Run:

```bash
npm test -- --watch=false --include=src/features/shortform-director/services/shortform-director-production.service.spec.ts
```

Expected: compilation or expectation failure because the method does not
exist.

- [ ] **Step 3: Add models and gateway method**

Define history result/item interfaces in
`shortform-director-production.ts`. Add optional pending/history members to the
project production model for compatibility with older fixture objects. Add
`listFinalRenders(projectId)` to the gateway and HTTP service.

Update the common production fixture with empty pending/history defaults.

- [ ] **Step 4: Re-run the focused service spec and verify GREEN**

Run the same Angular service test command.

---

### Task 5: Preserve and select completed final videos in the Angular store

**Files:**
- Modify: `src/features/shortform-director/state/shortform-director-production.store.ts`
- Modify: `src/features/shortform-director/state/shortform-director-production.store.spec.ts`

**Signals:**
- `completedFinalRenders`
- `selectedFinalRenderId`
- `loadingFinalRenderId`

- [ ] **Step 1: Add RED rerender tests**

Seed an active completed preview and history, then call
`startFinalRender()`. Expect the existing blob URL and selected render ID to
remain unchanged while the new render is waiting.

Resolve the poll as completed and expect:

- the new file is downloaded;
- the new ID becomes selected;
- the old object URL is revoked only when the new URL replaces it;
- history is refreshed and contains both versions.

- [ ] **Step 2: Add RED failure and selection tests**

Cover:

- asynchronous failure preserves the prior selected ID and blob URL;
- start failure also preserves them;
- `selectFinalRender(renderId)` downloads and displays a historical version;
- failed historical download leaves the current preview unchanged;
- loading or switching storyboard projects clears history, selection, and
  pending status, and revokes the old URL.

- [ ] **Step 3: Run the focused store spec**

Run:

```bash
npm test -- --watch=false --include=src/features/shortform-director/state/shortform-director-production.store.spec.ts
```

Expected: new tests fail because rerender start clears the preview and history
state does not exist.

- [ ] **Step 4: Implement history loading**

During execution-state loading:

1. fetch the completed history;
2. set the normalized completed list;
3. download the active render as the default selected preview;
4. resume polling the pending render without replacing the active preview.

If a legacy active render job/file is missing, retain normal storyboard
loading and report no completed preview.

- [ ] **Step 5: Implement rerender preservation and promotion**

Remove the eager `replaceFinalVideoUrl(null)` from `startFinalRender()`.
Keep the existing selected preview during waiting/running/failed/cancelled
states. On completed:

1. download the new MP4;
2. verify the same project is still selected;
3. replace and revoke the previous object URL;
4. select the new render;
5. refresh completed history.

Keep stale-project guards after every awaited status/file/history call.

- [ ] **Step 6: Implement historical selection**

`selectFinalRender(renderId)` must:

- ignore the current selection and unknown IDs;
- set `loadingFinalRenderId`;
- download the selected completed MP4;
- replace the URL and selected ID only after a successful download;
- preserve the current video on failure;
- clear its loading marker only for the originating project/request.

- [ ] **Step 7: Re-run the focused store spec and verify GREEN**

Run the same Angular store test command.

---

### Task 6: Add rerender and history controls to the production card

**Files:**
- Create: `src/features/shortform-director/components/ai-video-production-card/ai-video-production-card.component.spec.ts`
- Modify: `src/features/shortform-director/components/ai-video-production-card/ai-video-production-card.component.ts`
- Modify: `src/features/shortform-director/components/ai-video-production-card/ai-video-production-card.component.html`
- Modify: `src/features/shortform-director/components/ai-video-production-card/ai-video-production-card.component.scss`
- Modify: `src/features/shortform-director/pages/production-page/production-page.component.ts`
- Modify: `src/features/shortform-director/pages/production-page/production-page.component.html`

- [ ] **Step 1: Add RED component tests**

Render the standalone card with a completed final URL. Assert that:

- the video remains visible;
- the action label is `최종 영상 다시 만들기`;
- clicking emits `finalRenderRequested`;
- while rerendering, the existing video remains visible and the action is
  disabled.

Provide two completed history items and assert that:

- the non-selected item appears under `이전 최종 영상 1개`;
- selecting it emits its render ID;
- the selected/loading state is distinguishable.

- [ ] **Step 2: Run the focused component spec**

Run:

```bash
npm test -- --watch=false --include=src/features/shortform-director/components/ai-video-production-card/ai-video-production-card.component.spec.ts
```

Expected: compilation or DOM expectation failure because the new inputs,
output, and controls do not exist.

- [ ] **Step 3: Add component inputs and outputs**

Add inputs for completed history, selected render ID, and loading render ID.
Add:

```ts
readonly finalRenderSelected = output<string>();
```

- [ ] **Step 4: Restructure the final-render template**

Always keep the completed video preview independent of the action button.
Choose the label from whether a completed URL exists:

```html
{{ finalVideoUrl() ? '최종 영상 다시 만들기' : '최종 영상 만들기' }}
```

Disable the action while a render is starting or pending. Below the preview,
show prior completed versions newest first, excluding the selected version
from the `이전 최종 영상 N개` count and selection list.

- [ ] **Step 5: Wire the production page**

Pass store history/selection/loading signals to the card and delegate
`finalRenderSelected` to `production.selectFinalRender(renderId)`.

- [ ] **Step 6: Re-run the component and store specs**

Run:

```bash
npm test -- --watch=false --include=src/features/shortform-director/components/ai-video-production-card/ai-video-production-card.component.spec.ts
npm test -- --watch=false --include=src/features/shortform-director/state/shortform-director-production.store.spec.ts
```

Expected: both focused suites pass.

---

### Task 7: Run regression verification and inspect the diff

- [ ] **Step 1: Run all Shortform Director NestJS tests**

From `../clipper_nestjs`:

```bash
node --test test/shortform-director-*.test.js
```

- [ ] **Step 2: Run all Shortform Director Angular tests**

From `clipper_angular`:

```bash
npm test -- --watch=false --include=src/features/shortform-director/**/*.spec.ts
```

- [ ] **Step 3: Run compilation builds**

Run:

```bash
npm run build
```

in both `clipper_nestjs` and `clipper_angular`. Do not run an app packaging
build.

- [ ] **Step 4: Review only scoped changes**

Inspect `git diff` in both repositories. Confirm:

- no provider calls, API keys, or generated media are present;
- no unrelated dirty-worktree changes were overwritten;
- previous completed final-render files remain addressable;
- the old preview remains visible throughout a rerender;
- no commit or push was created.
