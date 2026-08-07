# Storyboard Final Render Isolation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ensure a newly generated storyboard never displays the previous storyboard project's completed final render.

**Architecture:** Keep final-render persistence project-scoped as it is today. Reset the Angular execution state when a newly generated storyboard project replaces the current project, and reject final-render poll responses whose originating project is no longer current.

**Tech Stack:** Angular, TypeScript, Angular signals, Jasmine/Karma

## Global Constraints

- Do not change Desktop API contracts or persisted project schemas.
- Preserve completed final renders when the user selects their original storyboard.
- Do not run a paid AI-video or final-render operation.
- Do not run the macOS app packaging build.
- Do not commit or push without an explicit request.

---

### Task 1: Isolate final-render state by current storyboard project

**Files:**
- Modify: `src/features/shortform-director/state/shortform-director-production.store.spec.ts`
- Modify: `src/features/shortform-director/state/shortform-director-production.store.ts`

**Interfaces:**
- Consumes: `ShortformDirectorProject.id`, `ShortformDirectorProject.production.activeRenderRevisionId`
- Produces: `finalRender()` and `finalVideoUrl()` that only describe the currently selected storyboard project

- [ ] **Step 1: Add failing regression tests**

Add a test that seeds a completed render and final-video URL on an existing
project, generates a second project, and expects both signals to be cleared:

```ts
store.project.set(previousProject);
store.finalRender.set({
  renderId: 'render.previous',
  status: 'completed',
  progress: 1,
  message: '완료',
  error: null,
  resultAvailable: true,
});
store.finalVideoUrl.set('blob:previous-final-video');

await store.generatePlan(
  productionPreflight.approvalVersion,
  productionPreflight.approvalId,
);

expect(store.project()?.id).toBe(nextProject.id);
expect(store.finalRender()).toBeNull();
expect(store.finalVideoUrl()).toBeNull();
```

Add a second test using a deferred `getFinalRenderStatus()` promise. Switch to
the next project before resolving the previous project's completed status, then
expect `finalRender()` to remain `null`.

- [ ] **Step 2: Run the focused spec and verify RED**

Run:

```bash
npm test -- --watch=false --include=src/features/shortform-director/state/shortform-director-production.store.spec.ts
```

Expected: the new tests fail because `generatePlan()` retains the previous
execution state and `pollFinalRender()` accepts a stale response.

- [ ] **Step 3: Clear execution state before accepting the new project**

In `generatePlan()`, after the new run, result, and project have all succeeded
and immediately before `acceptSucceededRun(...)`, add:

```ts
this.clearExecutionState();
```

This reuses the same reset boundary already used by historical storyboard
selection.

- [ ] **Step 4: Guard final-render mutations after awaited requests**

In `pollFinalRender(projectId, renderId)`, after
`getFinalRenderStatus(...)` resolves, stop before setting state when:

```ts
if (this.destroyed || this.project()?.id !== projectId) break;
```

After `downloadFinalRender(...)` resolves, repeat the same guard before
creating or replacing the object URL.

Only clear `startingFinalRender` at the end when the originating project is
still current:

```ts
if (this.project()?.id === projectId) {
  this.startingFinalRender.set(false);
}
```

- [ ] **Step 5: Run focused tests and verify GREEN**

Run:

```bash
npm test -- --watch=false --include=src/features/shortform-director/state/shortform-director-production.store.spec.ts
```

Expected: all tests in the focused spec pass.

- [ ] **Step 6: Run Shortform Director Angular tests**

Run:

```bash
npm test -- --watch=false --include=src/features/shortform-director/**/*.spec.ts
```

Expected: all selected Shortform Director tests pass.

- [ ] **Step 7: Run the Angular build**

Run:

```bash
npm run build
```

Expected: Angular compilation succeeds.

- [ ] **Step 8: Review the scoped diff**

Run:

```bash
git diff -- src/features/shortform-director/state/shortform-director-production.store.ts src/features/shortform-director/state/shortform-director-production.store.spec.ts
```

Expected: the diff contains only the new-project reset, stale-poll guards, and
their regression tests.
