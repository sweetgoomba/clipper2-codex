# Template Builder Box Sizing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a box effect width mode so text boxes can either fit text with horizontal padding or use a fixed editable width.

**Architecture:** Store the mode on the common text `box` style as `sizing: 'text' | 'fixed'` plus `width`. Angular inspector displays either `paddingX` or `width`, preview resizing writes fixed width to the common style, and Python text artifacts render using the same contract.

**Tech Stack:** Angular standalone components, NestJS DTO/seed/common-style merge, Python Pillow text artifact renderer.

---

### Task 1: Angular UI and Preview Contract

**Files:**
- Modify: `clipper_angular/src/features/template-builder/models/template-builder.ts`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-editor.contract.ts`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-inspector.component.html`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.ts`
- Test: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.spec.ts`

- [ ] Write RED tests for the box width mode select, conditional `paddingX`/`width` fields, text-fit horizontal resize lock, and fixed-width preview resize emitting a common style patch.
- [ ] Run the focused Angular spec and confirm the new tests fail because `sizing/width` are not implemented.
- [ ] Add optional box `sizing` and `width` contract fields with defaults for new templates.
- [ ] Add inspector controls and editor methods for `updateBoxSizing` and width updates.
- [ ] Make text-fit box mode hide horizontal resize handles and fixed mode emit `box.width` from preview resize.
- [ ] Re-run the focused Angular spec.

### Task 2: Backend Contract and Renderer

**Files:**
- Modify: `clipper_nestjs/src/template-builder/dto/template-builder.dto.ts`
- Modify: `clipper_nestjs/src/template-builder/template-builder-seed.ts`
- Modify: `clipper_python/plugins/clipper1_video_render/clipper1_video_render/template_builder_text_renderer.py`
- Modify: `clipper_python/plugins/clipper1_video_render/clipper1_video_render/template_builder_text_artifacts.py`
- Test: `clipper_python/tests/test_template_builder_text_renderer.py`

- [ ] Write RED tests for fixed-width text artifact rendering and text-fit required width behavior.
- [ ] Run the focused Python tests and confirm the new tests fail.
- [ ] Add NestJS DTO defaults for `sizing` and `width`.
- [ ] Update Python renderer normalization so `fixed` uses `box.width`, while `text` uses text required width plus padding.
- [ ] Re-run focused Python tests.

### Task 3: Documentation and Verification

**Files:**
- Modify: `.codex/session-logs/2026-05-10.log`

- [ ] Record the decision that box width mode is part of ratio-common text effects.
- [ ] Run Angular focused tests, Python focused tests, Angular build, NestJS build, and `git diff --check`.
