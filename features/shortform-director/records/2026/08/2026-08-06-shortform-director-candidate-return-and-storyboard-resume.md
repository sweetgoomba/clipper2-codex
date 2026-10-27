# Shortform Director Candidate Return and Storyboard Resume Implementation Plan

> **2026-10-26 문서 이관 안내:** 후보 복귀·과거 스토리보드 재개를 다룬 초기 구현 계획이다. **사용자 지정 스크롤 복원 부분은 같은 날 후속 설계에서 철회**됐다. [철회 이유·후속 설계](../../../../../design/2026-08-06-candidate-return-cleanup-and-clipper-title-design.md)와 [후속 구현 계획](../../../../../design/2026-08-06-candidate-return-cleanup-and-clipper-title.md)을 함께 읽는다. 아래 완료 체크는 당시 이력이며 스크롤 복원을 다시 추가하라는 지시가 아니다.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Return from a storyboard to the exact candidate list context and scroll position, and open persisted storyboard projects even when a redundant historical result artifact is unavailable.

**Architecture:** Candidate navigation stores its scroll offset in the current browser history entry before routing and includes the topic context in the storyboard URL for fallback navigation. The storyboard back action uses the existing browser-style navigation service. Historical storyboard hydration trusts the candidate-scoped history response and validates the returned run/project lineage without requiring the separate result endpoint.

**Tech Stack:** Angular standalone components and signals, Angular Router/Location, Jasmine, TypeScript.

## Global Constraints

- Do not run `npm run build:app:mac:arm64:local-api`; the user owns packaged app builds.
- Do not call paid AI/video providers.
- Preserve unrelated uncommitted changes in all repositories.
- Keep the fix within the existing Shortform Director navigation and production-store boundaries.

---

### Task 1: Preserve candidate context and scroll on storyboard round trips

**Files:**
- Create: `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-candidate-return.service.ts`
- Create: `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-candidate-return.service.spec.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/pages/candidates-page/candidates-page.component.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/pages/candidates-page/candidates-page.component.spec.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/pages/production-page/production-page.component.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/pages/production-page/production-page.component.html`
- Modify: `desktop/clipper_angular/src/features/shortform-director/pages/production-page/production-page.component.spec.ts`
- Modify: `desktop/clipper_angular/src/core/navigation/nav-history.service.ts`
- Modify: `desktop/clipper_angular/src/core/navigation/nav-history.service.spec.ts`

**Interfaces:**
- Produces: `ShortformDirectorCandidateReturnService.remember(scrollTop: number): void`
- Produces: `ShortformDirectorCandidateReturnService.read(): number | null`
- Produces: `NavHistoryService.back(fallback: unknown[], extras?: NavigationExtras): void`
- Produces: `ProductionPageComponent.backToCandidates(): void`

- [x] **Step 1: Write failing navigation and history-state tests**

Add tests proving that candidate navigation remembers the current scroll offset, includes `researchRunId` and `topicId`, and that the production back button delegates to browser-style back with a complete fallback query.

- [x] **Step 2: Run focused Angular tests and verify failure**

Run:

```bash
npm test -- --watch=false --include='src/features/shortform-director/pages/candidates-page/candidates-page.component.spec.ts' --include='src/features/shortform-director/pages/production-page/production-page.component.spec.ts' --include='src/core/navigation/nav-history.service.spec.ts'
```

Expected: FAIL because return-state persistence and browser-style production back are not implemented.

- [x] **Step 3: Implement browser-history scroll memory and back navigation**

Persist the scroll offset without changing the current URL:

```ts
remember(scrollTop: number): void {
  const history = this.document.defaultView?.history;
  if (!history) return;
  history.replaceState({
    ...(asRecord(history.state) ?? {}),
    shortformDirectorCandidateScrollTop: scrollTop,
  }, '');
}
```

Before routing to the storyboard, record the `.director-shell__content` offset and pass all candidate context:

```ts
this.candidateReturn.remember(this.scrollViewport()?.scrollTop ?? 0);
await this.router.navigate(['/shortform/director/storyboard'], {
  queryParams: {
    candidateRunId: selected.candidateRunId,
    candidateId,
    profileId,
    researchRunId,
    topicId,
  },
});
```

Restore the stored offset after candidate data has rendered, and replace the storyboard anchor with a button that calls:

```ts
this.navHistory.back(
  ['/shortform/director/candidates'],
  { queryParams: { profileId, researchRunId, topicId } },
);
```

- [x] **Step 4: Run focused Angular tests and verify pass**

Run the command from Step 2. Expected: PASS.

### Task 2: Resume stored storyboard projects without a result-artifact 404

**Files:**
- Modify: `desktop/clipper_angular/src/features/shortform-director/state/shortform-director-production.store.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/state/shortform-director-production.store.spec.ts`

**Interfaces:**
- Consumes: candidate-scoped `ShortformDirectorStoryboardHistoryItemV1`
- Produces: historical hydration using `getRun(runId)` and `getProject(runId)` only

- [x] **Step 1: Write a failing historical hydration test**

Configure `getResult` to reject with HTTP 404 while history, run, and project remain valid. Assert that the project opens, no not-found presentation appears, and `getResult` is not called.

- [x] **Step 2: Run the store test and verify failure**

Run:

```bash
npm test -- --watch=false --include='src/features/shortform-director/state/shortform-director-production.store.spec.ts'
```

Expected: FAIL because historical hydration currently calls `getResult` inside `Promise.all`.

- [x] **Step 3: Separate new-run and historical-run hydration**

Keep strict `run + result + project` validation immediately after generating a new storyboard. For a history item, fetch only run and project and validate:

```ts
run.status === 'succeeded'
  && run.id === historyItem.runId
  && run.profileId === selection.profileId
  && run.projectId === project.id
  && historyItem.projectId === project.id
```

Then set `result` to `null`, retain the project, and load execution state.

- [x] **Step 4: Run the store test and verify pass**

Run the command from Step 2. Expected: PASS.

### Task 3: Regression verification

**Files:**
- Verify only; no new files.

**Interfaces:**
- Consumes: Tasks 1 and 2.
- Produces: evidence that the Angular application remains buildable and Shortform Director tests pass.

- [x] **Step 1: Run all Shortform Director Angular tests**

Run:

```bash
npm test -- --watch=false --include='src/features/shortform-director/**/*.spec.ts'
```

Expected: PASS.

- [x] **Step 2: Run the Angular build**

Run:

```bash
npm run build
```

Expected: PASS. Do not run the packaged Electron app build.
