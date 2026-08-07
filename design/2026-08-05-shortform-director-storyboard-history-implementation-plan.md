# Shortform Director Storyboard History Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show the latest full storyboard by default, preserve and reopen every storyboard generated for the same candidate, allow each new generation to choose its own model and production mode, and keep scenes in one vertical sequence.

**Architecture:** Continue treating each existing `video-plan` run and its project as one immutable storyboard version. Add a candidate-scoped Desktop Nest summary endpoint over current run/artifact/project storage, then give the Angular store separate history, selected-project, and new-generation draft state. Hide history in a Material menu and render the selected project as the primary page content.

**Tech Stack:** NestJS 10 + `node:test` + local JSON (`clipper_nestjs`), Angular 19 standalone components + Material + signals + Karma/Jasmine (`clipper_angular`).

## Global Constraints

- Do not introduce a project revision array or migrate existing run/project JSON.
- The newest successful storyboard is the default full-page content.
- Do not use a history-only landing page or permanent left sidebar.
- Previous records are hidden until `다른 스토리보드 N개` is opened.
- Scenes are full-width and ordered vertically; shots remain nested under their owning scene.
- `새 스토리보드 만들기` never mutates or deletes the selected project.
- Every new generation can choose any supported video model and either production mode.
- A failed or cancelled new generation leaves the previously selected storyboard visible.
- `다른 스토리보드 N개` counts other successful, openable storyboards.
- Existing narration, AI-video job, and final-render state must switch with the selected project.
- Use Angular Material and existing semantic SCSS tokens; add no raw hex/rgba values.
- Do not run `npm run build:app:mac:arm64:local-api`; the user performs packaged builds.
- Do not commit or push unless the user explicitly requests it.
- Preserve unrelated dirty-worktree changes.

---

### Task 1: Add the candidate-scoped Desktop Nest history contract

**Files:**
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-candidate-production.service.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/presentation/shortform-director-candidate-production.controller.ts`
- Modify: `desktop/clipper_nestjs/test/shortform-director-candidate-production.test.js`

**Interfaces:**
- Produces:

```ts
export interface ShortformDirectorStoryboardHistoryItemV1 {
  runId: string;
  projectId: string | null;
  status: 'running' | 'partial' | 'succeeded' | 'failed' | 'cancelled';
  startedAt: string;
  finishedAt?: string;
  title: string | null;
  model: AiVideoModel | null;
  mode: AiVideoProductionMode | null;
  durationMs: number | null;
  sceneCount: number | null;
  shotCount: number | null;
  canOpen: boolean;
  failureCode?: string;
  failureStage?: string;
}

export interface ShortformDirectorStoryboardHistoryV1 {
  schemaVersion: 'shortform-director-storyboard-history.v1';
  candidateRunId: string;
  candidateId: string;
  items: ShortformDirectorStoryboardHistoryItemV1[];
}
```

- Produces:

```ts
storyboards(
  candidateRunId: string,
  candidateId: string,
  auth: Pick<AuthContext, 'subjectId'>,
): Promise<ShortformDirectorStoryboardHistoryV1>;
```

- Produces HTTP GET:
  `/projects/shortform-director/candidate-production/candidate-runs/:candidateRunId/candidates/:candidateId/storyboards`.

- [ ] **Step 1: Write failing history service cases**

Build test fixtures with three `video-plan` runs:

```js
[
  {
    id: 'run.director.newest',
    status: 'succeeded',
    startedAt: '2026-08-05T03:00:00.000Z',
    candidateRunId: CANDIDATE_RUN_ID,
    candidateId: CANDIDATE_ID,
  },
  {
    id: 'run.director.older',
    status: 'succeeded',
    startedAt: '2026-08-05T01:00:00.000Z',
    candidateRunId: CANDIDATE_RUN_ID,
    candidateId: CANDIDATE_ID,
  },
  {
    id: 'run.director.other-candidate',
    status: 'succeeded',
    startedAt: '2026-08-05T04:00:00.000Z',
    candidateRunId: CANDIDATE_RUN_ID,
    candidateId: 'candidate.director.other',
  },
]
```

Assert the response contains only newest and older, in that order, and that
their project summaries include model, mode, scene count, shot count, and
duration. Add a failed matching run with a `candidate-production-input`
artifact and assert it appears as `canOpen: false` with safe failure code/stage.
Add a run whose artifacts predate candidate lineage and assert it is omitted.

- [ ] **Step 2: Add a failing controller route assertion**

Instantiate the controller with a service spy and assert:

```js
await controller.storyboards(
  CANDIDATE_RUN_ID,
  CANDIDATE_ID,
  trustedHeaders,
);
assert.deepEqual(service.storyboards.mock.calls[0].arguments.slice(0, 2), [
  CANDIDATE_RUN_ID,
  CANDIDATE_ID,
]);
```

- [ ] **Step 3: Build and run the focused test to confirm RED**

Run:

```bash
cd desktop/clipper_nestjs
npm run build
node --test test/shortform-director-candidate-production.test.js
```

Expected: build or test FAIL because the history method/route is absent.

- [ ] **Step 4: Implement artifact-backed history projection**

For each user-owned `video-plan` run:

1. inspect output refs newest-first for
   `candidate-production-result`;
2. if no result identity exists, inspect input refs newest-first for
   `candidate-production-input`;
3. compare both candidate IDs exactly;
4. load the user-owned project when `projectId` exists;
5. project model/mode using `parseAiVideoProductionConfig`, with
   `DEFAULT_AI_VIDEO_PRODUCTION_CONFIG` only when an older project has no
   snapshot;
6. count scenes and nested shots;
7. set `canOpen` only for a succeeded run with a draft video plan;
8. sort by `startedAt` descending.

Catch an unreadable individual legacy artifact and continue to the next ref;
do not fail the complete history because one old run is malformed. Do not
swallow repository-level failures.

Add the controller route:

```ts
@Get(
  'candidate-runs/:candidateRunId/candidates/:candidateId/storyboards',
)
async storyboards(
  @Param('candidateRunId') candidateRunId: string,
  @Param('candidateId') candidateId: string,
  @Headers() headers: IncomingHttpHeaders,
) {
  return this.production.storyboards(
    candidateRunId,
    candidateId,
    await this.authContext.fromHttpHeaders(headers),
  );
}
```

- [ ] **Step 5: Build and run the focused test to confirm GREEN**

Run the command from Step 3. Expected: PASS.

---

### Task 2: Add the Angular history HTTP and model contract

**Files:**
- Modify: `desktop/clipper_angular/src/features/shortform-director/models/shortform-director-production.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-production.gateway.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-production.service.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-production.service.spec.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/testing/shortform-director-production.fixtures.ts`

**Interfaces:**
- Consumes: `ShortformDirectorStoryboardHistoryV1` from Task 1.
- Produces:

```ts
getStoryboardHistory(
  candidateRunId: string,
  candidateId: string,
): Promise<ShortformDirectorStoryboardHistoryV1>;
```

- Produces: reusable `storyboardHistory` fixture with newest and older projects.

- [ ] **Step 1: Write the failing service request test**

Call:

```ts
const promise = service.getStoryboardHistory(
  productionCandidateRunId,
  productionCandidateId,
);
```

Expect:

```ts
const request = http.expectOne(
  `${baseUrl}/projects/shortform-director/candidate-production/`
  + `candidate-runs/${encodeURIComponent(productionCandidateRunId)}/`
  + `candidates/${encodeURIComponent(productionCandidateId)}/storyboards`,
);
expect(request.request.method).toBe('GET');
request.flush(storyboardHistory);
await expectAsync(promise).toBeResolvedTo(storyboardHistory);
```

- [ ] **Step 2: Run the service spec and confirm RED**

Run:

```bash
cd desktop/clipper_angular
npm test -- --watch=false --browsers=ChromeHeadless \
  --include='src/features/shortform-director/services/shortform-director-production.service.spec.ts'
```

Expected: FAIL because the gateway method and model do not exist.

- [ ] **Step 3: Add the strict TypeScript interfaces and GET method**

Mirror the raw Desktop response exactly. Keep `listRuns` only if another
consumer still uses it; otherwise remove it from this gateway after the store
migration in Task 3. Do not add a response envelope or client-side N+1 result
filtering.

- [ ] **Step 4: Run the service spec and confirm GREEN**

Run the command from Step 2. Expected: PASS.

---

### Task 3: Separate selected storyboard state from new-generation draft state

**Files:**
- Modify: `desktop/clipper_angular/src/features/shortform-director/state/shortform-director-production.store.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/state/shortform-director-production.store.spec.ts`

**Interfaces:**
- Consumes: `getStoryboardHistory` from Task 2 and existing run/result/project endpoints.
- Produces signals:

```ts
readonly storyboardHistory =
  signal<ShortformDirectorStoryboardHistoryItemV1[]>([]);
readonly selectedStoryboardRunId = signal<string | null>(null);
readonly creatingStoryboard = signal(false);
readonly otherStoryboardCount = computed(/* other successful items */);
```

- Produces methods:

```ts
beginNewStoryboard(): Promise<void>;
cancelNewStoryboard(): void;
selectStoryboard(runId: string): Promise<void>;
```

- [ ] **Step 1: Replace the old history tests with failing latest-first tests**

Assert that `loadSelection`:

```ts
expect(gateway.getStoryboardHistory).toHaveBeenCalledOnceWith(
  productionCandidateRunId,
  productionCandidateId,
);
expect(store.selectedStoryboardRunId()).toBe(newest.runId);
expect(store.project()?.id).toBe(newest.projectId);
expect(store.storyboardHistory()).toEqual(history.items);
expect(store.creatingStoryboard()).toBeFalse();
expect(gateway.getPreflight).not.toHaveBeenCalled();
```

Assert an empty history starts creation and loads preflight. Assert selecting
the older run loads its project and execution state.

- [ ] **Step 2: Add failing new-generation isolation tests**

With an existing selected project:

```ts
await store.beginNewStoryboard();
await store.selectModel('veo-3.1-fast');
await store.selectMode('ai-integrated');

expect(store.project()).toBe(existingProject);
expect(store.creatingStoryboard()).toBeTrue();
expect(store.productionConfig()).toEqual({
  schemaVersion: 'ai-video-production-config.v1',
  model: 'veo-3.1-fast',
  mode: 'ai-integrated',
});
```

Reject `startProduction` and assert the same selected project/run remains.
Resolve it and assert history is refreshed, the new run becomes selected, and
`creatingStoryboard` becomes false.

- [ ] **Step 3: Run the store spec and confirm RED**

Run:

```bash
cd desktop/clipper_angular
npm test -- --watch=false --browsers=ChromeHeadless \
  --include='src/features/shortform-director/state/shortform-director-production.store.spec.ts'
```

Expected: FAIL because the store still lists profile runs, selects only one,
and locks model/mode whenever a project exists.

- [ ] **Step 4: Implement independent history and draft state**

Change `loadSelection` to:

```ts
const history = await this.gateway.getStoryboardHistory(
  selection.candidateRunId,
  selection.candidateId,
);
this.storyboardHistory.set(history.items);
this.historyChecked.set(true);
const latest = history.items.find((item) => item.canOpen);
if (latest) {
  await this.selectStoryboard(latest.runId);
} else {
  await this.beginNewStoryboard();
}
```

`beginNewStoryboard` copies the currently selected project's config as the
unlocked draft when present, otherwise uses the default, then reloads only
preflight. It must not call `loadSelection` or `reset`.

`selectModel` and `selectMode` are permitted when
`creatingStoryboard() === true`, even if `project()` is non-null. Their
preflight reload must preserve history, current project, narration jobs, and
render state.

`selectStoryboard` must load run/result/project, validate candidate lineage,
set all three selected values, and then call `loadExecutionState(project)`.
It must leave the old selection untouched until all required responses pass.

On successful `generatePlan`, refresh history and select the created run. On
failure, set `planError` without clearing `project`, `run`, `result`, history,
or creation config.

- [ ] **Step 5: Run the store spec and confirm GREEN**

Run the command from Step 3. Expected: PASS.

---

### Task 4: Build the hidden storyboard history menu

**Files:**
- Create: `desktop/clipper_angular/src/features/shortform-director/components/storyboard-history-menu/storyboard-history-menu.component.ts`
- Create: `desktop/clipper_angular/src/features/shortform-director/components/storyboard-history-menu/storyboard-history-menu.component.html`
- Create: `desktop/clipper_angular/src/features/shortform-director/components/storyboard-history-menu/storyboard-history-menu.component.scss`
- Create: `desktop/clipper_angular/src/features/shortform-director/components/storyboard-history-menu/storyboard-history-menu.component.spec.ts`

**Interfaces:**
- Consumes:

```ts
items = input.required<readonly ShortformDirectorStoryboardHistoryItemV1[]>();
selectedRunId = input<string | null>(null);
```

- Produces:

```ts
storyboardSelected = output<string>();
```

- [ ] **Step 1: Write failing menu behavior tests**

Assert that the closed fixture does not render history item titles in the
document, the trigger says `다른 스토리보드 2개`, opening the Material menu
reveals newest/older metadata, disabled failed items cannot emit, and clicking
an openable older item emits its run ID.

- [ ] **Step 2: Run the new component spec and confirm RED**

Run:

```bash
cd desktop/clipper_angular
npm test -- --watch=false --browsers=ChromeHeadless \
  --include='src/features/shortform-director/components/storyboard-history-menu/storyboard-history-menu.component.spec.ts'
```

Expected: FAIL because the component does not exist.

- [ ] **Step 3: Implement the Material menu**

Use `MatButtonModule`, `MatMenuModule`, and `DatePipe`. The trigger count is:

```ts
readonly otherCount = computed(() =>
  this.items().filter(
    (item) => item.canOpen && item.runId !== this.selectedRunId(),
  ).length,
);
```

Render only when `otherCount() > 0` or a non-successful attempt exists.
Successful items show timestamp, model label, mode label, duration, and latest
marker. Non-openable items show status and optional safe failure code/stage.
Do not keep the menu panel or its item text in the normal page layout.

Use only existing semantic tokens in SCSS.

- [ ] **Step 4: Run the component spec and confirm GREEN**

Run the command from Step 2. Expected: PASS.

---

### Task 5: Make the production page latest-first

**Files:**
- Modify: `desktop/clipper_angular/src/features/shortform-director/pages/production-page/production-page.component.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/pages/production-page/production-page.component.html`
- Modify: `desktop/clipper_angular/src/features/shortform-director/pages/production-page/production-page.component.scss`
- Modify: `desktop/clipper_angular/src/features/shortform-director/pages/production-page/production-page.component.spec.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/storyboard-scene-list/storyboard-scene-list.component.spec.ts`

**Interfaces:**
- Consumes: Task 3 store state and Task 4 history menu.
- Produces: latest storyboard as primary content, on-demand history, and an explicit new-storyboard creation panel.

- [ ] **Step 1: Write failing latest-first page tests**

With an existing history, assert:

```ts
expect(root.textContent).toContain(productionProject.title);
expect(root.querySelector('app-storyboard-scene-list')).not.toBeNull();
expect(root.querySelector('app-production-setup-card')).toBeNull();
expect(root.querySelector('app-production-preflight-card')).toBeNull();
expect(root.textContent).toContain('다른 스토리보드 1개');
expect(
  root.querySelector('[data-action="new-storyboard"]'),
).not.toBeNull();
expect(root.querySelector('.production-page__history-sidebar')).toBeNull();
```

Assert the visible top-level scene elements follow project scene order and
occupy one list, rather than two scene columns.

- [ ] **Step 2: Write failing new-storyboard interaction tests**

Click `[data-action="new-storyboard"]` and assert the existing storyboard
remains in the DOM while unlocked setup and preflight appear. Change the model
and mode, approve generation, then assert the confirm copy says
`새 스토리보드 생성` rather than `다시 생성` or overwrite wording.

Click cancel and assert the setup/preflight disappear while the selected
storyboard remains.

- [ ] **Step 3: Run page and scene tests to confirm RED**

Run:

```bash
cd desktop/clipper_angular
npm test -- --watch=false --browsers=ChromeHeadless \
  --include='src/features/shortform-director/pages/production-page/production-page.component.spec.ts' \
  --include='src/features/shortform-director/components/storyboard-scene-list/storyboard-scene-list.component.spec.ts'
```

Expected: FAIL because setup/preflight are always first and there is no hidden
history control or independent creation state.

- [ ] **Step 4: Reorder the page around selected project content**

When a project exists, render:

```html
<section class="production-page__current-storyboard">
  <header class="production-page__storyboard-header">
    <!-- title; latest/index, model, mode, and duration metadata -->
    <app-storyboard-history-menu
      [items]="production.storyboardHistory()"
      [selectedRunId]="production.selectedStoryboardRunId()"
      (storyboardSelected)="selectStoryboard($event)"
    />
    <button
      mat-flat-button
      type="button"
      data-action="new-storyboard"
      (click)="beginNewStoryboard()"
    >
      새 스토리보드 만들기
    </button>
  </header>
  <app-storyboard-scene-list [project]="project" />
  <app-ai-video-production-card ... />
</section>
```

Render setup/preflight only if there is no project or
`creatingStoryboard()` is true. Add a `취소` button when a selected project
exists. Keep the current project visible below the temporary creation panel.

Do not use a two-column scene container. Preserve the existing full-width
ordered scene list and keep each shot under its scene.

- [ ] **Step 5: Update component methods and approval copy**

Use:

```ts
selectModel(model: AiVideoModel): void;
beginNewStoryboard(): void;
cancelNewStoryboard(): void;
selectStoryboard(runId: string): void;
```

The confirmation dialog title is `새 스토리보드 생성 비용 승인`, and its
confirm label is `새 스토리보드 생성 승인`. No copy implies replacement.

- [ ] **Step 6: Run page and scene tests to confirm GREEN**

Run the command from Step 3. Expected: PASS.

---

### Task 6: Storyboard history regression verification

**Files:**
- Verify only.

**Interfaces:**
- Consumes: Tasks 1–5.
- Produces: evidence that immutable history and selected-project production state work without packaging.

- [ ] **Step 1: Verify Desktop Nest**

```bash
cd desktop/clipper_nestjs
npm run build
node --test \
  test/shortform-director-candidate-production.test.js \
  test/shortform-director-ai-video-service.test.js \
  test/shortform-director-storyboard-only-boundary.test.js
```

- [ ] **Step 2: Verify Angular**

```bash
cd desktop/clipper_angular
npm test -- --watch=false --browsers=ChromeHeadless \
  --include='src/features/shortform-director/services/shortform-director-production.service.spec.ts' \
  --include='src/features/shortform-director/state/shortform-director-production.store.spec.ts' \
  --include='src/features/shortform-director/components/storyboard-history-menu/storyboard-history-menu.component.spec.ts' \
  --include='src/features/shortform-director/components/storyboard-scene-list/storyboard-scene-list.component.spec.ts' \
  --include='src/features/shortform-director/pages/production-page/production-page.component.spec.ts'
npm run build
```

- [ ] **Step 3: Inspect the source boundary**

Run:

```bash
cd /Users/jina/project/adlight
rg -n \"history-sidebar|grid-template-columns.*storyboard__scene\" \
  desktop/clipper_angular/src/features/shortform-director
```

Expected: no permanent storyboard-history sidebar and no multi-column
top-level scene layout. Do not run a paid generation or packaged Electron
build.
