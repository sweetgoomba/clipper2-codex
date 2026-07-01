# Dance Member Profile And Manual Mapping Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add saved artist member profiles with excluded members and project-level manual mapping from anonymous dance persons to real members.

**Architecture:** Extend the existing dance reference cache service into a profile service while preserving its public role in `DanceController`. Store project manual mappings in `ProjectSnapshot.result` and apply them in `ProjectDetailBuilder`; Angular edits through focused HTTP methods.

**Tech Stack:** NestJS, Angular signals, node:test, Karma/Jasmine.

---

### Task 1: Backend Artist Member Profile

**Files:**
- Modify: `desktop/clipper_nestjs/src/modules/dance/infrastructure/services/dance-reference-cache.service.ts`
- Modify: `desktop/clipper_nestjs/src/modules/dance/presentation/dto/resolve-members.dto.ts`
- Test: `desktop/clipper_nestjs/test/dance-reference-cache-profile.test.js`

- [x] Write failing tests for saving included/excluded members and returning complete profile hits.
- [x] Implement version-2 profile read/write in the existing cache service.
- [x] Keep lookup empty when selected images are incomplete for included members.

### Task 2: Angular Member Profile Flow

**Files:**
- Modify: `desktop/clipper_angular/src/features/dance-highlight/flow/dance-flow.state.ts`
- Modify: `desktop/clipper_angular/src/features/dance-highlight/flow/dance-flow.store.ts`
- Modify: `desktop/clipper_angular/src/features/dance-highlight/components/member-image-select/*`
- Test: `desktop/clipper_angular/src/features/dance-highlight/pages/dance-setup/dance-setup.component.spec.ts`

- [x] Write failing tests for excluding a resolved member before image selection.
- [x] Split all resolved members from included `members`.
- [x] Skip image selection only when the backend profile is complete.
- [x] Include `excludedMembers` in `dance_setup`.

### Task 3: Backend Manual Dance Assignment

**Files:**
- Modify: `desktop/clipper_nestjs/src/modules/projects/application/projects.service.ts`
- Modify: `desktop/clipper_nestjs/src/modules/projects/presentation/projects.controller.ts`
- Modify: `desktop/clipper_nestjs/src/modules/projects/application/project-detail-builder.ts`
- Test: `desktop/clipper_nestjs/test/project-detail-builder-dance-members.test.js`
- Test: `desktop/clipper_nestjs/test/dance-member-assignment-service.test.js`

- [x] Write failing tests for `person_1 -> 허윤진` assignment merging clips/renders into the member.
- [x] Add a controller endpoint to persist assignments.
- [x] Apply assignments when building detail.

### Task 4: Angular Manual Assignment UI

**Files:**
- Modify: `desktop/clipper_angular/src/core/history/project-history.service.ts`
- Modify: `desktop/clipper_angular/src/shell/projects/dance-result-detail/*`
- Modify: `desktop/clipper_angular/src/shell/projects/projects-detail-page/projects-detail-page.component.ts`
- Note: `projects.component.ts` was not changed because project cards route to the standalone detail page.

- [x] Add API client method for saving assignments.
- [x] Add a member assignment selector on anonymous person rows.
- [x] Reload detail after save.

### Task 5: Verification

- [x] Run targeted NestJS tests.
- [x] Run targeted Angular specs.
- [x] Run `npm run build` in Angular.
- [x] Run `npm run build` in NestJS.
- [x] Run `git diff --check` for touched repos.
- [x] Build packaged macOS arm64 app.
- [x] Smoke-launch packaged app and verify main window startup log.
