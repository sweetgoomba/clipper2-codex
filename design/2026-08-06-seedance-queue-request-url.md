# Seedance Queue Request URL Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore status polling and MP4 retrieval for existing Seedance 2.0 jobs by using fal.ai's actual queue request root.

**Architecture:** Preserve the current asynchronous job and persistence contracts. Split the Seedance submission root from the queue request root inside the transport so existing stored request IDs remain sufficient.

**Tech Stack:** NestJS, TypeScript, Jest, native `fetch`

## Global Constraints

- Do not submit or regenerate paid provider jobs during verification.
- Do not change the AI video job database schema.
- Do not change Desktop or Angular code.
- Do not run the macOS app packaging build; the user will run it.

---

### Task 1: Correct Seedance queue operation URLs

**Files:**
- Modify: `src/modules/shortform-director-video-generation/infrastructure/seedance-video.transport.spec.ts`
- Modify: `src/modules/shortform-director-video-generation/infrastructure/seedance-video.transport.ts`

**Interfaces:**
- Consumes: persisted `FalVideoSubmission.providerRequestId`
- Produces: status GET at the parent queue endpoint and result GET at the same parent queue endpoint

- [ ] **Step 1: Write the failing transport test**

Change the expected status and result calls to these hand-derived literal URLs:

```ts
expect(fetcher.mock.calls[0]?.[0]).toBe(
  'https://queue.fal.run/bytedance/seedance-2.0/requests/fal-request-1/status',
);
expect(fetcher.mock.calls[1]?.[0]).toBe(
  'https://queue.fal.run/bytedance/seedance-2.0/requests/fal-request-1',
);
```

Keep the submission assertion unchanged:

```ts
expect(url).toBe(
  'https://queue.fal.run/bytedance/seedance-2.0/text-to-video',
);
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```bash
npm test -- --runInBand src/modules/shortform-director-video-generation/infrastructure/seedance-video.transport.spec.ts
```

Expected: the polling test fails because the actual status URL still contains
`/text-to-video/requests/`.

- [ ] **Step 3: Implement the minimal URL-root split**

Define the parent endpoint and derive the submission endpoint:

```ts
const FAL_QUEUE_ENDPOINT_ROOT =
  'https://queue.fal.run/bytedance/seedance-2.0';
const FAL_TEXT_TO_VIDEO_SUBMISSION_ROOT =
  `${FAL_QUEUE_ENDPOINT_ROOT}/text-to-video`;
```

Use `FAL_TEXT_TO_VIDEO_SUBMISSION_ROOT` only for submission. Build status and
result URLs from `FAL_QUEUE_ENDPOINT_ROOT`.

- [ ] **Step 4: Run focused and module tests**

Run:

```bash
npm test -- --runInBand src/modules/shortform-director-video-generation/infrastructure/seedance-video.transport.spec.ts
npm test -- --runInBand src/modules/shortform-director-video-generation
```

Expected: all selected tests pass without provider calls.

- [ ] **Step 5: Run the Web API build**

Run:

```bash
npm run build
```

Expected: TypeScript compilation succeeds.

- [ ] **Step 6: Review the diff**

Run:

```bash
git diff -- src/modules/shortform-director-video-generation/infrastructure/seedance-video.transport.ts src/modules/shortform-director-video-generation/infrastructure/seedance-video.transport.spec.ts
```

Expected: only the URL-root split and its regression expectations are present.
