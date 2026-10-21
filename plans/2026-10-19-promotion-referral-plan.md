# Promotion referral implementation plan

**Goal:** Ship configurable plan-granting promotion codes, safe redemption and revocation, direct referral attribution and export, promotion-to-paid booking, and promotion topup eligibility.

**Architecture:** Web API admin database owns campaign, code, redemption and attribution keys. Web member/admin apps call authenticated endpoints. Existing access, credit, payment and retry engines remain the fulfillment engines; new identifiers connect source records. Docs and decisions live only in `/Users/jina/project/adlight/.codex`.

**Branches:** `feat/promotion-referral-20261019` in Web API, member client, admin client, desktop NestJS, and desktop Angular, each at freshly fetched `origin/dev`. The `.codex` checkout stays on its existing branch.

## Task 1 — Persist campaigns and source links

Files: new admin migration; promotion entities; access/credit/payment entity and domain mappings; admin datasource registry.

1. Write a migration test for schema, constraints, rollback, and linked ID columns. Run it to see the expected failure.
2. Add campaign/code/redemption schema; `promotion` access source; redemption link on access/credit/subscription/order. Set database uniqueness and indexes for code lookup, one redemption per member/campaign, attribution reports.
3. Keep schema and TypeORM entities consistent; run migration tests, build, and related entity tests.

## Task 2 — Admin campaign/code configuration and member redemption

Files: new promotion module with domain rule helpers, persistence, service, DTOs/controllers and tests; app module; admin audit.

1. Test date/status/cap/history/overlap/one-per-campaign decisions and concurrent requests, then implement transactionally using existing user lock and campaign row lock.
2. Support admin create/list/update/stop, code create/list/disable, member preview/redeem/status, with existing auth and operator permission guards.
3. Use existing access/credit grant services so code redemption issues a plan and credit grant; preserve original registration ID, operator audit and idempotency.

## Task 3 — Revoke unused promotion benefits

Files: promotion service and API; credit grant revocation API/repository; tests.

1. Test partial credit use, no cross-source changes, repeated revocation and race with credit spending.
2. Under the same member lock and DB transaction, revoke the promo access and only its remaining credit grants; append immutable negative ledger entries and audit reason.

## Task 4 — Attribution capture and topup eligibility

Files: topup checkout service, order/subscription repositories, payment fulfillment/renewal paths, tests; client topup eligibility.

1. Test promo active topup allowed, trial/admin alone denied, and checkout-time code snapshot retained through delayed provider completion.
2. Store redemption ID on topup order and its generated credits, and on a promo-origin subscription/initial/renewal order; never infer it from a later code.

## Task 5 — Deferred paid subscription booking

Files: subscription service/repositories/scheduler/controllers/DTOs, retry policy integration, client subscription UI, tests.

1. Test active-promo booking with same or changed paid tier, displayed terms and first-charge date, cancellation, revoke while booked, no early charge and first-charge success/failure.
2. Capture billing consent/key via current provider flow without charging until due; due worker charges using existing idempotency/reconciliation; reuse configured retry days for failed first charge without paid grace.
3. Maintain conversion code ID on that subscription and renewals. Allow a new independently started subscription to have no old code link.

## Task 6 — Analytics, CSV and admin/member UI

Files: promotion report query/service and admin endpoints; admin and member routes/components/API clients; tests.

1. Test per-code/member benefits and usage, paid/refunded topup, first subscription payment, subsequent renewals and immediate upgrades, and purchased-credit use without double counting.
2. Add filterable per-registration report and UTF-8 BOM CSV containing campaign/code/registration/member IDs and attributed credit, payment, refund, and usage totals. Preserve original transaction IDs/timestamps in the underlying payment and credit records. Label the output as attribution data, not commission/payout.
3. Admin UI for campaign/code settings (including four history checkboxes), redemption/revocation, report/export. Member UI for code redemption and direct paid conversion choices.

## Task 7 — Desktop compatibility, contract and verification

Files: desktop backend access/credit proxy and desktop account screen, API OpenAPI contract (executable API contract only; prose docs stay in `.codex`), UI and service tests.

1. Accept `promotion` as a plan and current-period credit source in the desktop proxy; show the promotion label in the desktop account view. Keep payment and registration logic in Web API.
2. Update API contract and contract tests for every endpoint/shape.
3. Run relevant test suites, builds, and focused database tests. Verify each requirement against the design and record remaining risks in `.codex`.
4. Review the complete diff and remove any test-only or generated artifacts. Do not commit or push without a separate request.
