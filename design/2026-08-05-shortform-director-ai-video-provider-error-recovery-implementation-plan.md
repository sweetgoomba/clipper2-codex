# Shortform Director AI Video Provider Error Recovery Implementation Plan

> **For agentic workers:** Execute this plan with test-driven development and verify each repository independently. Do not call a paid video provider, package the desktop app, commit, or push unless the user explicitly asks.

**Goal:** Preserve a safe, useful AI-video provider rejection on the affected cut across app restarts, permit a same-revision retry when no provider job was created, and remove the Clipper-template prompt contradiction that prohibited requested scene-native text.

**Architecture:** The Web API remains the only component that sees the raw Google or fal.ai response. It extracts a small allowlisted diagnostic, returns that through the existing error boundary, and never forwards raw response bodies or credentials. Desktop Nest turns a failed pre-submission response into a persisted `generation_failed` job. Angular renders the stored diagnostic and lets the user resubmit the same approved revision. A successful submission clears the previous failure.

**Tech Stack:** NestJS 11/Jest, NestJS 10/node:test, Angular 19/Karma, local JSON project storage, OpenAPI YAML.

## Global constraints

- Preserve all unrelated dirty-worktree changes.
- Do not automatically retry a paid provider request.
- A failed job is resubmittable only when both `webApiJobId` and `providerRequestId` are absent.
- Reuse the existing deterministic revision, approval, and idempotency key.
- Persist only `code`, `message`, `providerStatus`, `providerCode`, `providerMessage`, and `failedAt`.
- Never persist or return API keys, authorization headers, raw provider bodies, prompts, or stack traces.
- Do not run an application packaging build or a paid provider end-to-end call.

## Task 1: Web API safe provider diagnostics and prompt correction

**Files:**

- Modify: `web/clipper_web_api/src/modules/shortform-director-video-generation/domain/ai-video-generation.transport.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-video-generation/infrastructure/gemini-omni-video.transport.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-video-generation/infrastructure/gemini-omni-video.transport.spec.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-video-generation/infrastructure/seedance-video.transport.spec.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-video-generation/application/shortform-director-video-generation.service.ts`
- Modify: `web/clipper_web_api/src/modules/shortform-director-video-generation/application/shortform-director-video-generation.service.spec.ts`
- Modify: `web/clipper_web_api/docs/api/openapi.yaml`
- Modify: the colocated AI-video OpenAPI contract test if the current suite requires an explicit schema assertion.

1. Add failing tests proving that:
   - Clipper-template mode allows requested scene-native text and numbers while still prohibiting dialogue, narration, spoken-word subtitles, and music.
   - A Google-style HTTP 400 body yields only an allowlisted provider status, code, and message.
   - A fal.ai validation body yields the same normalized fields.
   - Secret-looking values outside the allowlisted diagnostic fields are not exposed.
   - The Web API 502 response includes the normalized diagnostic fields.
2. Run only the affected Jest tests and confirm the new assertions fail for the intended reason.
3. Extend `AiVideoProviderError` with optional provider code and message fields.
4. On non-2xx provider responses, parse JSON once, read only known error fields, normalize whitespace, redact credential-like fragments, and truncate the message.
5. Forward only the normalized fields through `providerException`.
6. Update the Clipper-template prompt so scene-native requested text is allowed.
7. Update OpenAPI for the optional diagnostic fields.
8. Re-run the affected Jest tests.

## Task 2: Desktop persistence and same-revision recovery

**Files:**

- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/domain/ai-video-job.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-ai-video.service.ts`
- Modify: `desktop/clipper_nestjs/test/shortform-director-ai-video-job.test.js`
- Modify: `desktop/clipper_nestjs/test/shortform-director-ai-video-service.test.js`

1. Add failing tests proving that:
   - Optional provider diagnostics round-trip through the persisted job parser.
   - A provider rejection before a provider job ID exists returns and stores `generation_failed`.
   - Recreating the service still lists the same failure.
   - Syncing that failed job resubmits the same revision/idempotency key.
   - A successful retry clears the old failure.
   - A failed job that already has a provider job ID cannot be resubmitted.
2. Run the Desktop build followed by only the two affected node:test files and confirm the new tests fail for the intended reason.
3. Extend the job failure type and parser with the optional normalized fields.
4. Permit `generation_failed -> planned` only for a pre-submission failure with no remote IDs.
5. Convert a known Web API provider rejection into a persisted failure job instead of leaving only a transient HTTP error.
6. Use the same recovery path from both `start` and `sync`.
7. Clear `failure` on a successful submission.
8. Re-run the focused Desktop build/tests.

## Task 3: Angular persisted failure display and retry affordance

**Files:**

- Modify: `desktop/clipper_angular/src/features/shortform-director/models/shortform-director-production.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/ai-video-shot-status-list/ai-video-shot-status-list.component.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/ai-video-shot-status-list/ai-video-shot-status-list.component.html`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/ai-video-shot-status-list/ai-video-shot-status-list.component.spec.ts`

1. Add failing component tests proving that a persisted provider status/code/message is visible and that a pre-submission `generation_failed` job offers `제출 다시 시도`.
2. Run only the component spec and confirm failure.
3. Extend the client type, render the normalized diagnostic below the friendly message, and route the retry through the existing refresh action.
4. Confirm a job with a remote provider ID is not presented as a new paid submission retry.
5. Re-run the focused Angular spec.

## Task 4: Verification and handoff

1. Run the complete affected Web API AI-video test set and `npm run build`.
2. Run the Desktop Nest build and all Shortform Director AI-video client/domain/service/controller tests.
3. Run the Angular AI-video component, production service, and production store specs.
4. Inspect diffs for accidental raw error-body, credential, or prompt persistence.
5. Report changed behavior, exact verification results, and the fact that packaging/provider E2E were intentionally not run.
