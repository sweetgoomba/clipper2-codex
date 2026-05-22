# Template Builder Canvas Measurement Guides Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a horizontal-center action and Figma-like distance guides for the selected Template Builder preview element.

**Architecture:** Keep mutation state in `TemplateBuilderEditorComponent`; expose center action and measurement guide data through the existing workspace/canvas view models. Render guides as lightweight overlay elements in `TemplateBuilderCanvasComponent`, using original video px values for labels and scaled coordinates for placement.

**Tech Stack:** Angular standalone components, Karma/Jasmine specs, existing Template Builder editor VM contracts.

---

### Task 1: Lock Behavior With Tests

**Files:**
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.spec.ts`

- [ ] Add tests that verify:
  - The toolbar renders a `가로 중앙` button.
  - Clicking it emits an x-only patch that centers the selected text layer in the video frame.
  - A selected layer renders frame-edge distance labels.
  - A nearby visible layer renders a neighbor distance label.
- [ ] Run:
  - `npm test -- --watch=false --browsers=ChromeHeadless --include=src/features/template-builder/components/template-builder-editor.component.spec.ts`
- [ ] Expected first result: fail because the button and guide elements do not exist yet.

### Task 2: Extend View Models And Editor Logic

**Files:**
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-editor.contract.ts`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.ts`

- [ ] Add `CanvasMeasurementGuide` to the contract.
- [ ] Add `measurementGuides` and `centerSelectedLayerHorizontally` to the VM.
- [ ] Implement selected frame resolution for text/media/subtitle-line selections.
- [ ] Implement edge distance guides for top/bottom/left/right.
- [ ] Implement nearest-neighbor distance guide in each direction when another visible layer has overlapping projection.
- [ ] Implement `centerSelectedLayerHorizontally()` using the existing `movePatchForLayer()` path.

### Task 3: Render Toolbar Action And Canvas Overlay

**Files:**
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-workspace.component.html`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-workspace.component.scss`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-canvas.component.html`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-canvas.component.scss`

- [ ] Add a `가로 중앙` toolbar button wired to the VM.
- [ ] Disable it for read-only state or when no selected visible layer exists.
- [ ] Render guide lines and labels from `measurementGuides`.
- [ ] Style guide lines as thin orange overlays with compact black px labels.

### Task 4: Verify And Document

**Files:**
- Modify: `.codex/session-logs/2026-05-10.log`

- [ ] Run focused editor spec.
- [ ] Run Template Builder focused suite.
- [ ] Run `npm run build`.
- [ ] Run `git diff --check`.
- [ ] Record the decision and verification in the session log.
