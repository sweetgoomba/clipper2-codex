# Template Builder Runtime Admin Mode Button Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Template Builder button that enables the existing temporary system-template edit capability for the current app runtime.

**Architecture:** NestJS owns the edit policy. Angular calls a small admin-mode endpoint, then reloads families so backend-computed `capabilities.canEdit` becomes active. The runtime flag is process-local and does not persist across app restart.

**Tech Stack:** NestJS controller/service, Angular signals/components, Node test runner, Karma.

---

### Task 1: Backend runtime edit-mode policy

**Files:**
- Modify: `clipper_nestjs/src/template-builder/dto/template-builder.dto.ts`
- Modify: `clipper_nestjs/src/template-builder/template-builder.service.ts`
- Modify: `clipper_nestjs/src/template-builder/template-builder.controller.ts`
- Test: `clipper_nestjs/test/template-builder-api.test.js`

- [x] Add a small response DTO: `TemplateBuilderSystemTemplateEditModeState { enabled: boolean }`.
- [x] Write a failing test showing `service.enableSystemTemplateEditMode()` flips system family `capabilities.canEdit` from `false` to `true`.
- [x] Implement runtime state in `TemplateBuilderService`.
- [x] Add controller route `POST /template-builder/admin/system-template-edit-mode`.
- [x] Keep env flag support unchanged.

### Task 2: Angular admin-mode button

**Files:**
- Modify: `clipper_angular/src/features/template-builder/models/template-builder.ts`
- Modify: `clipper_angular/src/features/template-builder/services/template-builder.service.ts`
- Modify: `clipper_angular/src/features/template-builder/pages/template-builder-page.component.ts`
- Modify: `clipper_angular/src/features/template-builder/pages/template-builder-page.component.html`
- Test: `clipper_angular/src/features/template-builder/pages/template-builder-page.component.spec.ts`

- [x] Add frontend response type `TemplateBuilderSystemTemplateEditModeState`.
- [x] Add service method `enableSystemTemplateEditMode()`.
- [x] Write a failing page test showing the button calls the service and reloads families with editable capabilities.
- [x] Add a header button labeled `임시 관리자 모드 실행`.
- [x] Disable the button once any system template already has `capabilities.canEdit=true`.
- [x] Show backend errors through the existing `error` signal.

### Task 3: Verification

**Commands:**
- `cd clipper_nestjs && npm run build`
- `cd clipper_nestjs && node --test test/template-builder-api.test.js`
- `cd clipper_angular && npm test -- --watch=false --include src/features/template-builder/pages/template-builder-page.component.spec.ts`
- `cd clipper_angular && npm run build`
- `cd clipper_nestjs && git diff --check`
- `cd clipper_angular && git diff --check`

Expected: all commands exit 0.

Result on 2026-05-12:
- [x] `clipper_nestjs`: `npm run build`
- [x] `clipper_nestjs`: `node --test test/template-builder-api.test.js test/template-builder-validation.test.js test/template-builder-render-payload.test.js`
- [x] `clipper_angular`: `npm test -- --watch=false --include src/features/template-builder/pages/template-builder-page.component.spec.ts --include src/features/template-builder/components/template-builder-editor.component.spec.ts --include src/features/template-builder/components/template-builder-workspace.component.spec.ts`
- [x] `clipper_angular`: `npm run build`
- [x] `clipper_nestjs`: `git diff --check`
- [x] `clipper_angular`: `git diff --check`
