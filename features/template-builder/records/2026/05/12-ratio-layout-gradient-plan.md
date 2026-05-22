# Template Builder Ratio Layout And Full Gradient Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Template Builder에서 layout image를 비율별로 독립 편집하게 되돌리고, full ratio의 gradient/content-area preview 기준을 정리한다.

**Architecture:** `layoutImage`는 더 이상 family 공통 레이어로 전파하지 않고, 선택된 `variant.ratio`의 media layer로만 저장한다. full ratio의 `gradient.png`는 콘텐츠 위에 얹히는 overlay 성격으로 모델링하되, 기존 단일 `layout_image` render contract와 충돌하는 다중 layout layer 문제는 별도 설계 문서로 분리한다.

**Tech Stack:** NestJS Template Builder service/seed/legacy mapper, Angular standalone Template Builder editor/page specs, Karma/Jasmine, Node test runner.

---

### Task 1: Ratio-Specific Layout Image Save

**Files:**
- Modify: `clipper_nestjs/test/template-builder-api.test.js`
- Modify: `clipper_nestjs/src/template-builder/template-builder.service.ts`
- Modify: `clipper_angular/src/features/template-builder/pages/template-builder-page.component.spec.ts`
- Modify: `clipper_angular/src/features/template-builder/pages/template-builder-page.component.ts`

- [ ] **Step 1: Write failing backend regression**

Change the existing family-wide sync test so it asserts a `layoutImage` patch only updates the selected ratio.

Expected behavior:
- Updating `full.layers.layoutImage` changes `full` only.
- Existing `16:9.layers.layoutImage` geometry and `assetUri` remain unchanged.

- [ ] **Step 2: Verify backend RED**

Run:

```bash
cd clipper_nestjs
npm run build
node --test test/template-builder-api.test.js
```

Expected: the updated regression fails because current `updateVariant()` still applies `sharedLayoutImagePatch` to all variants.

- [ ] **Step 3: Implement backend fix**

Remove the cross-ratio `sharedLayoutImagePatch` behavior from `TemplateBuilderService.updateVariant()`. Only the requested ratio should receive `request.layers`.

- [ ] **Step 4: Write failing Angular optimistic-state regression**

Change the existing page spec so optimistic `layoutImage` patching affects only the selected ratio.

Expected behavior:
- Selected ratio receives the new layout image patch immediately.
- Non-selected ratios keep their previous layout image values.

- [ ] **Step 5: Verify Angular RED**

Run:

```bash
cd clipper_angular
npm test -- --watch=false --include src/features/template-builder/pages/template-builder-page.component.spec.ts
```

Expected: the updated regression fails because current `applyVariantLayerPatch()` still propagates `layoutImage` to all variants.

- [ ] **Step 6: Implement Angular optimistic-state fix**

Update `applyVariantLayerPatch()` so it only merges the patch into the selected ratio.

### Task 2: Move Layout Row Out Of Common Layer UI

**Files:**
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.ts`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-workspace.component.html`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.spec.ts`

- [ ] **Step 1: Write failing UI regression**

Add or update an editor spec proving:
- `레이아웃` appears in the selected ratio's default layer list.
- The `공통 레이어` section is not shown when no actual common layer row exists.

- [ ] **Step 2: Verify RED**

Run:

```bash
cd clipper_angular
npm test -- --watch=false --include src/features/template-builder/components/template-builder-editor.component.spec.ts
```

Expected: the new/updated regression fails because `레이아웃` is still exposed through `commonLayerRow`.

- [ ] **Step 3: Implement UI move**

Set `commonLayerRow` to `null`, add `layoutImage` to `defaultLayerRows`, and only render the `공통 레이어` section when there is a row.

### Task 3: Full Ratio Gradient Preview And Content Area Fallback

**Files:**
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-canvas.component.scss`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.spec.ts`
- Modify: `clipper_nestjs/src/template-builder/template-builder-seed.ts`
- Modify: `clipper_nestjs/src/project-manifest/legacy-clipper1-render-payload-mapper.ts`
- Modify: `clipper_nestjs/test/template-builder-api.test.js`
- Modify: `clipper_nestjs/test/template-builder-render-payload.test.js`

- [ ] **Step 1: Write failing content fallback regression**

Add an Angular spec proving `.canvas-content-area` fallback background is solid `#babcbb`, not the old gradient.

- [ ] **Step 2: Implement fallback color**

Change the content area preview fallback background to `#babcbb`.

- [ ] **Step 3: Write failing full ratio seed regression**

Add a NestJS seed regression proving:
- For normal full presets whose legacy `layout_image` is `gradient.png`, `contentArea.assetUri` points to `gradient.png`.
- For full presets whose legacy `layout_image` is a real `_full.png`, `layoutImage.assetUri` keeps that `_full.png` and `contentArea.assetUri` still points to `gradient.png`.

- [ ] **Step 4: Implement seed mapping**

In `template-builder-seed.ts`, treat full ratio `gradient.png` as the overlay/content-area asset and keep real `_full.png` layout images as the lower layout layer.

- [ ] **Step 5: Preserve current final render compatibility**

Update the legacy render payload mapper so a full ratio with no `layoutImage.assetUri` can still emit `layout_image` from `contentArea.assetUri`. Keep `_full.png` precedence when present.

### Task 4: Multiple Layout Layers Design Only

**Files:**
- Create: `.codex/design/2026-05-12-template-builder-multiple-layout-layers-design.md`

- [ ] **Step 1: Document the future model**

Describe a later `layoutLayers[]` model with per-ratio storage, z-order controls, renderer payload implications, migration from single `layoutImage`, and why it is not included in the current patch.

### Task 5: Verification And Handoff

**Files:**
- Modify: `.codex/session-logs/2026-05-12.log`
- Modify: `.codex/implementation/NEXT_SESSION_PROMPT.md` if needed

- [ ] **Step 1: Run focused checks**

Run the changed focused suites:

```bash
cd clipper_nestjs
npm run build
node --test test/template-builder-api.test.js test/template-builder-render-payload.test.js

cd ../clipper_angular
npm test -- --watch=false --include src/features/template-builder/pages/template-builder-page.component.spec.ts --include src/features/template-builder/components/template-builder-editor.component.spec.ts
npm run build
```

- [ ] **Step 2: Check whitespace**

Run:

```bash
cd clipper_nestjs && git diff --check
cd ../clipper_angular && git diff --check
```

- [ ] **Step 3: Update logs**

Append concise notes to the session log with root cause, changed files, verification results, and any remaining manual checks.
