# Shortform Workflow Store Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move shortform workflow page state signals and synchronous state transitions into a page-scoped store without changing existing UI behavior.

**Architecture:** Add `ShortformWorkflowStore` under `src/features/shortform/pages`. Provide it from `ShortformWorkflowPageComponent` so state resets when the page is destroyed. The page keeps service calls and async orchestration for this step, but delegates state mutation to the store.

**Tech Stack:** Angular standalone component providers, Angular signals, Jasmine/Karma.

---

### Task 1: Store Contract Tests

**Files:**
- Create: `src/features/shortform/pages/shortform-workflow.store.spec.ts`

- [x] **Step 1: Write failing tests**

Add tests that verify:
- `patchRenderSettings` preserves existing `titleVisibility` fields and updates `updatedAt`.
- `ensureTitleDefaults` initializes generated titles without overwriting existing user title edits.
- `markMediaFailed` records failed URLs and clears the active preview media URL when it fails.
- `requestPreviewSeek` increments request ids.
- category selection resets the second category to the first option of the selected primary category.

- [x] **Step 2: Run tests to verify RED**

Run:
```bash
./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless '--include=src/features/shortform/pages/shortform-workflow.store.spec.ts'
```

Expected: FAIL because `shortform-workflow.store.ts` does not exist yet.

### Task 2: Implement Page-Scoped Store

**Files:**
- Create: `src/features/shortform/pages/shortform-workflow.store.ts`
- Modify: `src/features/shortform/pages/shortform-workflow-page.component.ts`

- [x] **Step 1: Add store**

Create an `@Injectable()` class with the current workflow signals and synchronous mutators. Do not use `providedIn: 'root'`.

- [x] **Step 2: Provide and alias from page**

Add `providers: [ShortformWorkflowStore]` to the page component. Replace direct signal declarations with aliases to `this.store` so existing template and tests can keep using `component.project`, `component.error`, and the same template bindings.

- [x] **Step 3: Delegate sync mutations**

Move sync mutations such as render setting patching, title defaults, prompt helper/category changes, preview seek request, failed-media tracking, and input content updates into store methods. Keep async service calls in the page for this task.

- [x] **Step 4: Run targeted tests**

Run:
```bash
./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless '--include=src/features/shortform/pages/shortform-workflow.store.spec.ts'
./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless '--include=src/features/shortform/pages/shortform-workflow-page.component.spec.ts'
```

Expected: PASS.

### Task 3: Verify Refactor Safety

**Files:**
- Modify only if verification reveals a regression in files changed by Task 2.

- [x] **Step 1: Run full shortform tests**

Run:
```bash
./node_modules/.bin/ng test --watch=false --browsers=ChromeHeadless '--include=src/features/shortform/**/*.spec.ts'
```

Expected: PASS.

- [x] **Step 2: Run build**

Run:
```bash
npm run build
```

Expected: PASS.

- [x] **Step 3: Run diff check**

Run:
```bash
git diff --check
```

Expected: no output.
