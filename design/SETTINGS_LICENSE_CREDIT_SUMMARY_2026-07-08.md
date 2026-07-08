# Settings License Credit Summary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the desktop Settings page hardcoded license and credit values with the authenticated user's current license summary.

**Architecture:** Reuse the existing web_api `GET /licenses/current` source of truth. Add a thin local NestJS `GET /v1/licenses/current` proxy that forwards the caller bearer token to web_api, then bind the Angular Settings page to that local endpoint through a small settings account service.

**Tech Stack:** NestJS, Angular standalone components, Angular HttpClient, TypeScript, existing local API auth interceptor.

---

### Task 1: web_api current license response

**Files:**
- Modify: `web/clipper_web_api/src/modules/billing/domain/license.model.ts`
- Modify: `web/clipper_web_api/src/modules/billing/application/licenses.service.ts`
- Test: `web/clipper_web_api/src/modules/billing/presentation/licenses.controller.spec.ts`

- [ ] Add `creditBalance`, `creditAllowance`, and `creditsUsed` to the current license response while keeping `tokenBalance` for compatibility.
- [ ] Verify active, queued, expired, and none states have stable values.

### Task 2: local NestJS license proxy

**Files:**
- Modify: `desktop/clipper_nestjs/src/core/web-api/web-api-client.service.ts`
- Create or modify: `desktop/clipper_nestjs/src/modules/licenses/*`
- Modify: `desktop/clipper_nestjs/src/app.module.ts`
- Test: `desktop/clipper_nestjs/test/web-api-client.test.js`
- Test: `desktop/clipper_nestjs/test/license-current-proxy.test.js`

- [ ] Add a GET helper to `WebApiClient`.
- [ ] Expose `GET /v1/licenses/current`, forwarding the local auth bearer token to web_api.
- [ ] Map web_api failures to existing local error handling without exposing secrets.

### Task 3: Angular Settings binding

**Files:**
- Create: `desktop/clipper_angular/src/shell/settings/settings/settings-account.service.ts`
- Modify: `desktop/clipper_angular/src/shell/settings/settings/settings.component.ts`
- Modify: `desktop/clipper_angular/src/shell/settings/settings/settings.component.html`
- Modify: `desktop/clipper_angular/src/shell/settings/settings/settings.component.scss`
- Test: `desktop/clipper_angular/src/shell/settings/settings/settings.component.spec.ts`

- [ ] Load the current license summary from local NestJS.
- [ ] Replace hardcoded plan and credit values with loading/error/none/active/queued/depleted labels.
- [ ] Use the response allowance/usage to calculate the progress bar.

### Task 4: verification and docs

**Files:**
- Modify: `.codex/handoff/NEXT.md`
- Modify: `.codex/records/sessions/2026/07/07.md`

- [ ] Run focused tests and builds for changed repos.
- [ ] Commit each repo's changes in small phase commits.
- [ ] Record DB audit and settings summary without secrets.
