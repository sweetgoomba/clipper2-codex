# Template Builder System Template Admin Edit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Allow development-admin editing of built-in Template Builder system templates through an override store, without implementing login.

**Architecture:** NestJS computes edit capabilities from a small policy that currently reads `TEMPLATE_BUILDER_SYSTEM_TEMPLATE_EDIT=1`. System template edits are stored in a dedicated JSON override repository and merged onto preset-generated system families. Angular consumes backend capabilities instead of treating `readonly` as the only edit gate.

**Tech Stack:** Angular signals/components, NestJS services/controllers, JSON file repositories, Node test runner, Karma.

---

### Task 1: Backend capabilities and system override repository

**Files:**
- Modify: `clipper_nestjs/src/template-builder/dto/template-builder.dto.ts`
- Modify: `clipper_nestjs/src/template-builder/template-builder.repository.ts`
- Modify: `clipper_nestjs/src/template-builder/template-builder.module.ts`
- Modify: `clipper_nestjs/src/template-builder/template-builder.service.ts`
- Test: `clipper_nestjs/test/template-builder-api.test.js`

- [x] Add optional `capabilities` to `TemplateBuilderFamily`.
- [x] Add `JsonTemplateBuilderSystemOverrideRepository` storing `template-builder-system-overrides.json`.
- [x] Register the override repository in `TemplateBuilderModule`.
- [x] Merge overrides onto preset-generated system families in `listFamilies()` and `getFamily()`.
- [x] Attach capabilities to every returned family.
- [x] Add tests proving env flag off blocks system edits and env flag on stores/returns overrides.

### Task 2: Backend edit policy integration

**Files:**
- Modify: `clipper_nestjs/src/template-builder/template-builder.service.ts`
- Test: `clipper_nestjs/test/template-builder-api.test.js`
- Test: `clipper_nestjs/test/template-builder-validation.test.js`

- [x] Replace direct `family.readonly` checks in variant/common-style update paths with `canEditFamily()`.
- [x] Keep rename/delete/variant create/sample render/publish/asset upload blocked for system families.
- [x] Ensure user template behavior remains unchanged.

### Task 3: Angular capability model

**Files:**
- Modify: `clipper_angular/src/features/template-builder/models/template-builder.ts`
- Modify: `clipper_angular/src/features/template-builder/pages/template-builder-page.component.ts`
- Modify: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.ts`
- Test: `clipper_angular/src/features/template-builder/pages/template-builder-page.component.spec.ts`
- Test: `clipper_angular/src/features/template-builder/components/template-builder-editor.component.spec.ts`

- [x] Add optional `capabilities` to Angular `TemplateBuilderFamily`.
- [x] Use `capabilities.canEdit` to decide editor readonly state.
- [x] Use `capabilities.canRename` and `capabilities.canDelete` for header actions.
- [x] Keep clone available for system templates.
- [x] Add tests for editable system template with rename/delete still hidden.

### Task 4: Verification

**Commands:**
- `cd clipper_nestjs && npm run build`
- `cd clipper_nestjs && node --test test/template-builder-api.test.js test/template-builder-validation.test.js test/template-builder-render-payload.test.js`
- `cd clipper_angular && npm test -- --watch=false --include src/features/template-builder/pages/template-builder-page.component.spec.ts --include src/features/template-builder/components/template-builder-editor.component.spec.ts`
- `cd clipper_angular && npm run build`
- `cd clipper_nestjs && git diff --check`
- `cd clipper_angular && git diff --check`

Expected: all commands exit 0.

Result on 2026-05-12:
- [x] `clipper_nestjs`: `npm run build`
- [x] `clipper_nestjs`: `node --test test/template-builder-api.test.js`
- [x] `clipper_nestjs`: `node --test test/template-builder-validation.test.js test/template-builder-render-payload.test.js`
- [x] `clipper_angular`: `npm test -- --watch=false --include src/features/template-builder/pages/template-builder-page.component.spec.ts`
- [x] `clipper_angular`: `npm test -- --watch=false --include src/features/template-builder/components/template-builder-editor.component.spec.ts`
- [x] `clipper_angular`: `npm test -- --watch=false --include src/features/template-builder/components/template-builder-workspace.component.spec.ts`
- [x] `clipper_angular`: `npm run build`
- [x] `clipper_nestjs`: `git diff --check`
- [x] `clipper_angular`: `git diff --check`
