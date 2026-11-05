# External Cancellation Effects Implementation Plan

> For agentic workers: REQUIRED SUB-SKILL: superpowers:subagent-driven-development or superpowers:executing-plans. Follow tasks below and record progress.

**Goal:** Verified full Toss-dashboard cancellations automatically reconcile their own credits/access/renewal with durable recovery and visible exceptions.
**Architecture:** A per-order external-effects outbox is separate from ordinary refund requests. Observation persists evidence and work atomically; a worker re-verifies provider truth outside the financial DB transaction, then applies scoped idempotent effects under existing locks.
**Tech Stack:** NestJS/TypeORM/PostgreSQL/Jest and Angular/Material/Karma.
**Spec:** /Users/jina/project/adlight/.codex/features/payments/records/2026/11/04-external-cancellation-effects-design.md

## Global Constraints
- Full external cancellation automatically reclaims only remaining credits from the affected payment and ends only its related entitlement/renewal. Customer refunds still require administrator approval.
- Already-used credits and partial cancellations require operator review; no negative wallet or unrelated credit clawback.
- Preserve other valid paid periods, grants and user ownership. Never send Toss cancelPayment from external reconciliation.
- Do not modify existing uncommitted pricing/signup-validity hunks, .env/local ports, artifacts, live/shared databases or unrelated worktrees.
- Provider verification occurs outside DB transactions; persistent retries and deterministic financial references survive restart and duplicate delivery.

## Review Focus
1. A historical canceled payment must preserve a later paid period and renewal.
2. An annual payment can have multiple monthly grants and future grant scheduling.
3. Concurrent normal refund/fulfillment/renewal/credit spending must not deadlock or issue canceled benefits.
4. Partial→full, multiple same-amount transactions, stale lookups and rollback/restart must be monotonic and idempotent.
5. A failed desktop operation returning credits later must not make a revoked grant spendable again.

## Task 1 — API external effects and contract
Files: new application/external-cancellation-effects.service.ts, domain/external-cancellation-effects.ts, appropriate admin migration after1793665100000, provider-cancellation-observation.service.ts, provider-cancellation-incidents.service.ts, payments.module.ts, payment-fulfillment.service.ts, subscription-renewal.service.ts and relevant payment/subscription repositories/guards, docs/api/openapi.yaml; colocated unit/isolated-PG specs. A small extracted provider validator may be used to prevent circular imports, preserving its current exported entry point.
Interface: incident `effects` exactly as the Spec Contract; existing recheck route also retries after verification. No new customer endpoint or arbitrary rights-write DTO.
- [x] Add failing isolated PG tests asserting a fully externally canceled topup loses its own remaining credits exactly once and other credits remain.
- [x] Add implementation/migration, durable observation enqueue/backfill, worker/retry and scoped transaction effects. Record red and green test evidence.
- [x] Add meaningful tests for monthly/annual, past/current/upgrade/used/partial, concurrency, internal refund coexistence, stale/mismatched provider, interrupted worker and delayed returns.
- [x] Fence fulfillment, renewal preparation/failure and late-result application under the spec lock order; test barriers and null-order annual attribution.
- [x] Extend existing payment history summaries with external pending/retry/review/completion without changing client request semantics. Resolved effects leave unresolved warning lists/counts, preserving factual order cancellation markers and unrelated reconciliation_required status.
- [x] Extend OpenAPI/query and module wiring; keep money and rights states distinct. Test DI, controller/permission/recheck contracts.
- [x] Reconcile pending customer requests to resolved_externally in a separate recoverable transaction after all snapshot payments finish external effects; extend raw filter/count and public completion source, test crash/multiorder/concurrent approval.
- [x] Run build and full API suite including disposable PG. Self-review the actual diff, report files/test logs and excluded hunks. Do not commit or push until root integration gate.

## Task 2 — Admin external effects visibility
Files: core/api/models.ts, mock data/interceptor and related tests, cancellation-incidents component ts/html/scss/spec, customer-refund-approvals component/filter and payment-refunds API service query types; payment-operations API contract tests if necessary.
- [x] Test compact pending/complete/review/retry states and readable details, missing legacy effects fallback, permission/recheck behavior and stable row layout.
- [x] Add external-resolution request filter/count/tab and truthful external completion label, without administrator approve/reject actions on completed rows.
- [x] Add `effects` type and one compact grid column using existing status chips plus tooltip/popover for details; use existing recheck action with accurate wording. No inline row expansion added.
- [x] Run focused tests then full Admin suite/build/check:colors; preserve signup-validity and mock-price hunks.

## Task 3 — Integration, independent review and combined status
- [x] Review user-facing client cancellation copy against updated money/internal state; change/test only if misleading.
- [x] Independent review across API and Admin; fix P1/P2 with regression tests.
- [x] Verify clean staged/archived session-only tree where mixed files contain parent edits; no env/artifact/price/signup-validity changes enter the new feature.
- [x] Record combined audit states: already dev; implemented but uncommitted; newly implemented external effects; verification gaps/remaining operator exceptions. Make no claim of real Toss end-to-end effects without an actual authorized test.

## Completion evidence

2026-11-04: API91afe80/Adminb68e415 pushed to remote dev after selected-source full suites/builds and clean independent review. Local migration/API health passed; real Toss cleanup E2E and production deployment not claimed. Combined audit and all rulings: `04-external-cancellation-effects-verification.md`.
