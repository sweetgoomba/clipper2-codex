# Toss Recurring Review Retry Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make anonymous Toss recurring-payment review retries use a distinct billing-key display ID and reconcile non-callback registration outcomes into the local order.

**Architecture:** Reuse each persisted review `orderNo` as Toss `displayId`, so no schema change is needed. Extend the existing provider contract to carry `userId + displayId`, validate callback identity, and add a recurring branch to receipt-token reconciliation that maps Toss billing status through existing repository transitions.

**Tech Stack:** Node.js 24, NestJS, TypeScript, TypeORM, Jest, Toss Pay billing-key HTTP API

## Global Constraints

- Work only on a new branch based on `clipper_web_api/dev` in an isolated worktree.
- Keep documentation under `/Users/jina/project/adlight/.codex`.
- Do not change the client, infra, schema, credits, licenses, or legacy purchase requests.
- Do not log or expose the plaintext billing key or API key.
- Use `orderNo` as `displayId`; do not add a database column.
- Do not mix the separate operator JWT fixed-date test fix into this branch.

---

### Task 1: Carry `displayId` through the Toss provider boundary

**Files:**
- Modify: `src/modules/payments/domain/toss-pay.provider.ts:15-21,81-92`
- Modify: `src/modules/payments/infrastructure/http-toss-pay.provider.ts:36-53`
- Test: `src/modules/payments/infrastructure/http-toss-pay.provider.spec.ts:67-127,258-269`

**Interfaces:**
- `CreateBillingKeyInput` gains required `displayId: string`.
- `getBillingKeyStatus(input: { userId: string; displayId: string })` replaces the string argument.

- [ ] **Step 1: Write failing provider tests**

Require billing creation to send `displayId: 'clipper-review-abcdefghijklmnopqrst'`. Change status lookup to call `getBillingKeyStatus({ userId: 'review-user', displayId: 'review-order' })` and require both fields in the HTTP body.

- [ ] **Step 2: Confirm RED**

Run `npm test -- --runInBand src/modules/payments/infrastructure/http-toss-pay.provider.spec.ts`.

Expected: failure because the provider contract does not yet support `displayId` or an object status argument.

- [ ] **Step 3: Implement the minimal provider change**

Add `displayId: string` to `CreateBillingKeyInput`. Change the abstract and HTTP method to accept `{ userId: string; displayId: string }`, then pass that object to the existing authenticated `post()` helper.

- [ ] **Step 4: Confirm GREEN**

Run the same focused provider spec and require all tests to pass.

- [ ] **Step 5: Commit**

Stage the provider interface, implementation, and spec. Commit as `fix(payments): identify Toss billing keys by display ID`.

### Task 2: Send and validate the review order display ID

**Files:**
- Modify: `src/modules/payments/application/review-payments.service.ts:42-47,135-150,249-333`
- Modify: `src/modules/payments/presentation/dto/billing-result-callback.dto.ts:4-10`
- Test: `src/modules/payments/application/review-payments.service.spec.ts:191-230,312-565`
- Test: `src/modules/payments/presentation/toss-pay-callback.controller.spec.ts:21-35`

**Interfaces:**
- `BillingKeyCallback` gains required `displayId: string`.
- Billing creation sends `displayId: orderNo`.
- Callback DTO retains and validates `displayId` while stripping unrelated fields.
- Callback handling rejects a display ID different from the matched order's `orderNo`.

- [ ] **Step 1: Write failing service and DTO tests**

Require recurring checkout input `displayId` to equal the stored `orderNo`. Add `displayId` to the valid callback fixture and expected DTO. Add a mismatched-display-ID callback test expecting `BadGatewayException`, no status lookup, and no charge. Require the successful callback status lookup argument to equal `{ userId: activatedCallback.userId, displayId: normalCallback.orderNo }`.

- [ ] **Step 2: Confirm RED**

Run `npm test -- --runInBand src/modules/payments/application/review-payments.service.spec.ts src/modules/payments/presentation/toss-pay-callback.controller.spec.ts`.

Expected: failures because display ID creation, DTO retention, and callback verification are missing.

- [ ] **Step 3: Implement display ID propagation**

Add `displayId: orderNo` to `createBillingKey()`. Add `displayId` to `BillingKeyCallback` and `@IsString() displayId` to the DTO. Before decrypting a callback billing key, compare `callback.displayId` to `order.orderNo`. Query status with `{ userId: callback.userId, displayId: order.orderNo }`.

- [ ] **Step 4: Confirm GREEN**

Run the same two focused specs and require both to pass.

- [ ] **Step 5: Commit**

Stage the service, DTO, and their specs. Commit as `fix(payments): propagate Toss billing display ID`.

### Task 3: Reconcile recurring registration status

**Files:**
- Modify: `src/modules/payments/application/review-payments.service.ts:166-206,249-336,538-585`
- Test: `src/modules/payments/application/review-payments.service.spec.ts:453-727`

**Interfaces:**
- `reconcileReviewOrder(receiptToken)` continues returning `ReviewPaymentOrderView`.
- A private recurring path decrypts the stored key, queries with `userId + displayId`, verifies identity, and updates through existing repository methods.

- [ ] **Step 1: Write failing recurring reconciliation tests**

Cover these isolated outcomes:

- `CREATE`: remains `checkout_ready`, no state mutation.
- `CANCEL`: becomes `canceled` with a deduplicated `billing_canceled` event.
- `FAIL`: becomes `failed` with code/event `billing_registration_failed`.
- `REMOVE`: becomes `failed` with code/event `billing_removed`.
- `ACTIVE`: records activation, runs/reconciles the first charge, and reaches `paid` on success.
- Local `paid`, `canceled`, or `failed`: no Toss status lookup.
- Mismatched user or billing key: `BadGatewayException`, no mutation.
- Provider/network failure: `ServiceUnavailableException`, no terminal mutation.

Every status lookup must use `{ userId: activatedCallback.userId, displayId: normalCallback.orderNo }`.

- [ ] **Step 2: Confirm RED**

Run `npm test -- --runInBand src/modules/payments/application/review-payments.service.spec.ts`.

Expected: recurring reconciliation returns `checkout_ready` without a Toss status lookup.

- [ ] **Step 3: Implement recurring reconciliation**

Split reconciliation by payment type while preserving the one-time branch. For recurring non-terminal orders, require `reviewUserId` and encrypted billing key, decrypt it, and query Toss using `orderNo` as display ID.

Use these exact mappings:

- `CANCEL`: event `billing_canceled`, dedupe key `billing-canceled:<reviewUserId>`, provider `CANCEL`, local `canceled`.
- `FAIL`: code/event `billing_registration_failed`, dedupe key `billing-registration-failed:<reviewUserId>`, provider `FAIL`, local `failed`.
- `REMOVE`: code/event `billing_removed`, dedupe key `billing-removed:<reviewUserId>`, provider `REMOVE`, local `failed`.
- `ACTIVE`: reuse `billing_activated` and `processFirstCharge()`; reload by `orderNo` before returning the view.
- `CREATE` or unknown: keep the current non-terminal order.

- [ ] **Step 4: Confirm GREEN**

Run the focused service spec and require all tests to pass.

- [ ] **Step 5: Run all payment tests**

Run `npm test -- --runInBand --testPathPatterns=src/modules/payments` and require all payment tests to pass.

- [ ] **Step 6: Commit**

Stage the service and service spec. Commit as `fix(payments): reconcile Toss billing registration status`.

### Task 4: Verify, document, and publish

**Files:**
- Modify: `/Users/jina/project/adlight/.codex/implementation/TOSS_PAY_DEV_DEPLOYMENT_HANDOFF.md`
- Modify: `/Users/jina/project/adlight/.codex/implementation/WORKLOG.md`

**Interfaces:**
- Redeployment is API-only; there is no client, infra, or migration change.

- [ ] **Step 1: Run focused regression and build**

Run `npm test -- --runInBand --testPathPatterns=src/modules/payments`, then `npm run build`. Both must pass.

- [ ] **Step 2: Run the full API suite**

Run `npm test -- --runInBand`. Before the separate operator test branch is merged, only the previously documented fixed-date operator JWT test may fail. Any other failure blocks completion.

- [ ] **Step 3: Review the diff**

Run `git diff dev...HEAD --check`, `git diff --stat dev...HEAD`, and `git status --short`. Confirm there are no migrations, client changes, secrets, unrelated refactors, or credit/license grants.

- [ ] **Step 4: Update `.codex` handoff**

Document API-only redeployment, the repeated-card smoke test, and expected recurring event sequence. Explicitly state that no migration, web deployment, proxy change, or DB restart is needed.

- [ ] **Step 5: Commit documentation**

Stage the handoff and worklog. Commit as `docs: add Toss recurring retry redeployment`.

- [ ] **Step 6: Push verified feature branches**

Push `fix/toss-recurring-review-retry` in both `clipper_web_api` and `.codex`. Do not merge into `dev` or `.codex/main` until the verified diff is reported and merge authorization is clear.
