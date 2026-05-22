# Template Builder Common Layer and Preview Lock Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move `layoutImage` into a shared `공통 레이어` section, rename the old fixed-layer bucket to `기본 레이어`, and lock preview selection so layout editing can only move/resize the layout image while keeping `contentArea` visible between layout and text.

**Architecture:** The Angular template builder editor stays the single source of truth for section labels, selection rules, and preview z-order. The preview canvas keeps `layoutImage` as the only common editable layer, `contentArea` as a non-editable guide layer, and all text/logo layers as the `기본 레이어` group. Selection gating is enforced in the editor component so preview pointer events cannot switch away from layout editing when the common layer is active.

**Tech Stack:** Angular 19 standalone components, signal state, component specs with zoneless TestBed, existing template-builder preview snapshot tests.

---

### Task 1: Lock In The New Left-Panel Structure

**Files:**
- Modify: `src/features/template-builder/components/template-builder-editor.component.ts`
- Modify: `src/features/template-builder/components/template-builder-editor.component.html`
- Modify: `src/features/template-builder/components/template-builder-editor.component.spec.ts`

- [ ] **Step 1: Write the failing test**

Add a spec that expects the left panel text to contain `공통 레이어` and `기본 레이어`, and not `고정 레이어`.

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- --watch=false --browsers=ChromeHeadless --include=src/features/template-builder/components/template-builder-editor.component.spec.ts`
Expected: FAIL because the template still renders `고정 레이어`.

- [ ] **Step 3: Write minimal implementation**

Move `layoutImage` into a separate common-layer row list and render the remaining rows under `기본 레이어`.

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- --watch=false --browsers=ChromeHeadless --include=src/features/template-builder/components/template-builder-editor.component.spec.ts`
Expected: PASS for the new section-label assertions.

### Task 2: Keep Content Area Visible Above Layout But Below Text

**Files:**
- Modify: `src/features/template-builder/components/template-builder-editor.component.html`
- Modify: `src/features/template-builder/components/template-builder-editor.component.scss`
- Modify: `src/features/template-builder/services/template-builder-preview-render-snapshot.export.spec.ts`
- Modify: `src/features/template-builder/components/template-builder-editor.component.spec.ts`

- [ ] **Step 1: Write the failing test**

Add a snapshot assertion that `contentArea` is rendered above `layoutImage` in DOM/z-order terms while text layers still render above `contentArea`.

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- --watch=false --browsers=ChromeHeadless --include=src/features/template-builder/services/template-builder-preview-render-snapshot.export.spec.ts`
Expected: FAIL until z-index is explicit.

- [ ] **Step 3: Write minimal implementation**

Give `layoutImage`, `contentArea`, and text layers explicit stacking order so the guide stays visible without covering text.

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- --watch=false --browsers=ChromeHeadless --include=src/features/template-builder/services/template-builder-preview-render-snapshot.export.spec.ts`
Expected: PASS with the updated stacking order.

### Task 3: Prevent Non-Layout Preview Selection While Layout Is Active

**Files:**
- Modify: `src/features/template-builder/components/template-builder-editor.component.ts`
- Modify: `src/features/template-builder/components/template-builder-editor.component.html`
- Modify: `src/features/template-builder/components/template-builder-editor.component.spec.ts`

- [ ] **Step 1: Write the failing test**

Add a spec that selects `레이아웃`, clicks a title or subtitle preview target, and expects the selection to remain on `layoutImage`.

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- --watch=false --browsers=ChromeHeadless --include=src/features/template-builder/components/template-builder-editor.component.spec.ts`
Expected: FAIL because preview clicks still switch selection.

- [ ] **Step 3: Write minimal implementation**

Guard preview click/drag/keyboard selection paths so they ignore non-layout layers when the layout media layer is selected.

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- --watch=false --browsers=ChromeHeadless --include=src/features/template-builder/components/template-builder-editor.component.spec.ts`
Expected: PASS and the layout selection remains stable.

### Task 4: Verify The Page Still Clones And Renders Correctly

**Files:**
- Modify: `src/features/template-builder/pages/template-builder-page.component.spec.ts` if the section label changes affect page rendering

- [ ] **Step 1: Run the focused component tests**

Run: `npm test -- --watch=false --browsers=ChromeHeadless --include=src/features/template-builder/components/template-builder-editor.component.spec.ts`

- [ ] **Step 2: Run the page tests**

Run: `npm test -- --watch=false --browsers=ChromeHeadless --include=src/features/template-builder/pages/template-builder-page.component.spec.ts`

- [ ] **Step 3: Run the build**

Run: `npm run build`

- [ ] **Step 4: Commit**

Use a focused commit message describing the common-layer preview lock behavior.
