# Template Builder Multiple Layout Layers Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Template Builder에서 ratio별 layout image를 여러 장 쌓고, 표시 순서까지 다룰 수 있는 기반을 만든다.

**Architecture:** 기존 `layoutImage`는 migration bridge로 유지하고, 새 source of truth는 `variant.layers.layoutLayers[]`로 확장한다. 구현은 백엔드 contract/seed/render payload, Angular preview stack, Angular UI add/reorder/delete/edit 순서로 나눈다.

**Tech Stack:** NestJS Template Builder DTO/seed/payload mapper, Angular standalone components/signals, Karma/Jasmine, Node test runner.

---

## Phase 1: Backend Layout Stack Contract

**Files:**
- Modify: `clipper_nestjs/src/template-builder/dto/template-builder.dto.ts`
- Modify: `clipper_nestjs/src/template-builder/template-builder-seed.ts`
- Modify: `clipper_nestjs/src/project-manifest/legacy-clipper1-render-payload-mapper.ts`
- Modify: `clipper_nestjs/test/template-builder-api.test.js`
- Modify: `clipper_nestjs/test/template-builder-render-payload.test.js`

- [ ] **Step 1: Write failing DTO/seed regression**

Add assertions that legacy full ratio presets expose `layers.layoutLayers`:
- Normal full template 1: one layer, `gradient.png`.
- Exception full template 6: two layers, `6_full.png` first and `gradient.png` second.
- Non-full template 1 `16:9`: one layer matching legacy `layout_image`.

- [ ] **Step 2: Verify RED**

Run:

```bash
cd clipper_nestjs
npm run build
node --test test/template-builder-api.test.js
```

Expected: fails because `layoutLayers` does not exist.

- [ ] **Step 3: Implement DTO and seed bridge**

Add `TemplateBuilderLayoutLayer` and optional `TemplateBuilderLayers.layoutLayers`.

Seed rules:
- Every legacy preset with `layout_image` gets at least one layout layer.
- Full `gradient.png` only: `layoutLayers = [gradient]`, legacy `layoutImage.assetUri = null`.
- Full `_full.png`: `layoutLayers = [_full, gradient]`, legacy `layoutImage.assetUri = _full`.
- Non-full: `layoutLayers = [layout_image]`, legacy `layoutImage.assetUri = layout_image`.

- [ ] **Step 4: Write failing render payload regression**

Add a mapper test that emits `template_builder_layout_layers` in order when present.

- [ ] **Step 5: Implement mapper output**

Add `template_builder_layout_layers` to `template_settings` or `template_builder_render_contract` without removing legacy `layout_image` fallback.

## Phase 2: Angular Model And Preview Stack

**Files:**
- Modify: `clipper_angular/src/features/template-builder/models/template-builder.ts`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-editor.contract.ts`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.ts`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-canvas.component.html`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-canvas.component.scss`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.spec.ts`

- [ ] **Step 1: Write failing preview stack regression**

Add a spec with `variant.layers.layoutLayers = [_full, gradient]`.

Expected:
- Preview renders both layout layers.
- `_full` appears before `gradient`.
- `gradient` appears below logo/text and above `_full`.

- [ ] **Step 2: Implement read-only stack rendering**

Render `layoutLayers[]` when present. Keep existing single `layoutImage` path as fallback.

## Phase 3: Angular Layout Layer Row Selection

**Files:**
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.ts`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-workspace.component.html`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-inspector.component.html`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-editor.contract.ts`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.spec.ts`

- [ ] **Step 1: Add failing row regression**

Expected:
- `기본 레이어` shows one row per layout layer.
- Selecting a layout layer shows the media inspector for that exact layer.
- Existing `layoutImage` row still works for data without `layoutLayers`.

- [ ] **Step 2: Implement selection bridge**

Use selected media id values like `layoutLayers:<layerId>` for dynamic layout layers, while keeping `layoutImage` for legacy single-layer selection.

## Phase 4: Angular Add/Reorder/Delete Layout Layers

**Files:**
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-workspace.component.html`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-workspace.component.scss`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.ts`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.spec.ts`
- Modify: `clipper_angular/src/features/template-builder/pages/template-builder-page.component.ts`
- Modify: `clipper_angular/src/features/template-builder/pages/template-builder-page.component.spec.ts`

- [ ] **Step 1: Add failing command regressions**

Expected:
- Add layout layer appends a new layer to selected ratio only.
- Move up/down reorders selected ratio only.
- Delete removes selected layout layer and clears selection.

- [ ] **Step 2: Implement commands as `layers.layoutLayers` patches**

Keep upload and geometry editing scoped to selected layout layer.

## Phase 5: Renderer Follow-up

**Files:**
- Modify: `clipper_python/plugins/clipper1_video_render/clipper1_video_render/local_render_adapter.py`
- Modify: `clipper_python/tests/test_clipper1_video_render_media_looping.py`
- Modify: `clipper_python/tests/test_clipper1_video_render_remote_assets.py`

- [x] **Step 1: Inspect render worker support**

Find where Python/Clipper1 renderer consumes `layout_image`.

- [x] **Step 2: Add renderer tests before implementation**

Expected:
- When `template_builder_layout_layers` exists, renderer composites each layer in order before text/logo overlays.
- When absent, renderer keeps legacy `layout_image` behavior.

- [x] **Step 3: Implement renderer layout stack**

Implementation notes:
- `_visual_assets()` resolves `template_settings.template_builder_layout_layers` to ordered `layout_layers` with path and geometry.
- Non-final segment rendering overlays layout stack layers in order after the content media base and before logo/text overlays.
- Full-height renders defer layout stack to `_overlay_final_layout()`, which overlays each stack layer over the concatenated content video before logo/text overlays.
- Legacy single `layout_image` behavior remains the fallback when no stack exists.

## Verification

Focused checks per phase:

```bash
cd clipper_nestjs
npm run build
node --test test/template-builder-api.test.js test/template-builder-render-payload.test.js

cd ../clipper_angular
npm test -- --watch=false --include src/features/template-builder/components/template-builder-editor.component.spec.ts --include src/features/template-builder/pages/template-builder-page.component.spec.ts
npm run build
```

Whitespace:

```bash
cd clipper_nestjs && git diff --check
cd ../clipper_angular && git diff --check
```
