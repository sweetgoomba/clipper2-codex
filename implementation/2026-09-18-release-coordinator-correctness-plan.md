# Release Coordinator Correctness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make remote Windows builds derive the correct server profile, build only the exact selected release, and install dependencies in an isolated per-job Windows workspace.

**Architecture:** Web API owns build-channel derivation from `DESKTOP_RELEASE_TARGET`; Admin displays that read-only decision and sends no channel. Admin selection becomes a single reactive source of truth with no candidate fallback. Infra configures per-job source isolation for the development Windows runner as well as production.

**Tech Stack:** Angular signals/Jasmine, NestJS/TypeScript/Jest, Node ESM/node:test, PowerShell Windows runner scripts.

**Spec:** `.codex/implementation/2026-09-18-release-coordinator-correctness-design.md`

## Global Constraints

- Preserve failed Build 52 as audit history; do not edit or delete release DB rows.
- Do not publish an artifact or start another remote build during implementation.
- Keep explicit channel choice for artifact publication; remove it only from build start.
- Do not add old-client compatibility branches.
- All behavior changes require a failing regression test before implementation.

---

### Task 1: Derive the build channel in Web API

**Files:**
- Modify: `web/clipper_web_api/src/modules/releases/application/desktop-release-policy.ts`
- Modify: `web/clipper_web_api/src/modules/releases/application/releases.service.ts`
- Modify: `web/clipper_web_api/src/modules/releases/presentation/release-admin.controller.ts`
- Modify: `web/clipper_web_api/src/modules/releases/presentation/dto/start-build.dto.ts`
- Modify: `web/clipper_web_api/src/modules/releases/domain/release.model.ts`
- Modify: `web/clipper_web_api/src/modules/releases/infrastructure/typeorm-releases.repository.ts`
- Test: corresponding release policy, service, DTO, and controller specs

**Interfaces:**
- Produces `DesktopReleasePolicy.buildChannel(): 'dev' | 'rc'`.
- Build-start endpoints accept no operator-selected channel.
- Console coordinator adds `buildChannel: ReleaseChannelName`.

- [x] Write tests that development derives `dev`, production derives `rc`, and build start removes client channel input.
- [x] Run the targeted Jest tests and confirm they fail because the current DTO/service require `channel`.
- [x] Implement the minimal server-derived contract and coordinator response.
- [x] Run targeted tests and the release module suite.

### Task 2: Make Admin build the exact visible release

**Files:**
- Modify: `web/clipper_web_admin/src/app/features/portal/versions/services/version-console.store.ts`
- Modify: `web/clipper_web_admin/src/app/features/portal/versions/services/version-console-api.models.ts`
- Modify: `web/clipper_web_admin/src/app/features/portal/versions/services/version-console-api.service.ts`
- Modify: `web/clipper_web_admin/src/app/features/portal/versions/models/version-console.models.ts`
- Modify: `web/clipper_web_admin/src/app/features/portal/versions/models/version-console.selectors.ts`
- Modify: `web/clipper_web_admin/src/app/features/portal/versions/components/version-coordinator-section/version-coordinator-section.component.ts`
- Modify: `web/clipper_web_admin/src/app/features/portal/versions/components/version-coordinator-section/version-coordinator-section.component.html`
- Modify: Admin version-console specs and mock state

**Interfaces:**
- `startWindowsBuildForSelectedRelease(): void` sends an empty build-start body for the exact selected release.
- `coordinator` is computed from live selection and exposes the server-derived build channel.

- [x] Write tests proving channel selection is absent, visible target follows release selection, an unsnapshotted release cannot fall back, and build-start sends the exact selected release ID.
- [x] Run the targeted Angular tests and confirm the expected failures.
- [x] Implement the minimal reactive selection and selector-free Coordinator.
- [x] Run the targeted versions tests and Admin build.

### Task 3: Isolate development Windows runner sources

**Files:**
- Modify: `web/clipper_infra/runner/windows/run-windows-runner-container.ps1`
- Modify: `web/clipper_infra/runner/windows/windows-scripts.test.mjs`
- Document behavior and deployment evidence in the `.codex` design record.

**Interfaces:**
- Both `dev` and `prod` Windows containers receive `CLIPPER_RELEASE_WORK_ROOT=C:\runner-work` and `CLIPPER_RELEASE_ARCHIVE_ROOT=C:\runner-output\artifacts`.

- [x] Write a script-contract test proving the development runner also receives both isolation variables.
- [x] Run the Windows script test and confirm failure under the current production-only conditional.
- [x] Move isolation configuration out of the production-only block while retaining the production replacement guard.
- [x] Run runner and Windows script test suites.

### Task 4: Cross-repository verification and handoff

- [x] Run Web API build and full tests.
- [x] Run Admin full tests and production build.
- [x] Run Infra runner and Windows script tests.
- [x] Inspect diffs for unrelated changes and run `git diff --check` in all changed repositories.
- [x] Record exact Windows runner pull/recreate/health commands and expected Build 53 evidence; do not execute the remote build from this workspace.

Verification note: the Infra bundle contract now allows exactly one opposite-environment API literal in Admin for desktop artifact-profile validation. A second occurrence still fails as a wrong runtime environment. The complete Infra suite passes with 157 tests passed, one Windows-only test skipped, and no failures.
