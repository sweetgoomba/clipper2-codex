# Refund request / plan change guard implementation plan

Goal: implement the user's agreed refund flow in the existing API and customer web checkout, preserving ongoing mail work.
Spec: current chat approval on 2026-11-10. Existing scheduled changes are cancelled atomically with a subscription refund request after explicit confirmation; new plan changes are blocked during pending approval. Credit use and automatic renewal policy stay unchanged. No automatic mail triggers or production deployment.

Architecture: use the existing subscription advisory transaction lock for both refund creation and plan mutation. Return a scheduled-change confirmation snapshot/token with refund eligibility; reject a stale/missing token before cancelling a reservation. Reuse the existing refund request status and subscription reservation columns, without a migration. Expose pending request on current subscription for customer UI; server is authoritative.

Approved copy: 이후 환불 신청을 취소하거나 환불 신청이 승인되지 않더라도, 취소된 플랜 변경 예약은 자동으로 복원되지 않아요.

Existing working copies contain prior approved mail changes; continue in place and do not commit, reset, or move those changes.

- [x] API RED: test pending-refund quote/new change rejection; atomic create/cancel, rollback, stale confirmation, topup independence, idempotency and both request orderings on real PostgreSQL.
- [x] API GREEN: repository pending query; lock refund creation and bind option reads; confirmation token validation; block new mutations while allowing settlement/recovery of already submitted charges; current-subscription pending status.
- [x] Client RED/GREEN: eligibility metadata and request token; scheduled cancellation notice with approved copy; stale option refresh; pending dashboard state, disabled change controls and link to refund history. No automatic restoration.
- [x] Contract: update OpenAPI and typed client / mock responses.
- [x] Verify focused tests, full API/client unit suites, isolated PostgreSQL concurrency, builds and browser confirmation UI. Review own scoped diff and record limits.

Review focus: approval after a historical quote; refund submit vs new quote; change after dialog opens; repeated request key after reservation cancellation; already approved charges must still settle; only subscription refunds block plan changes; cancellation and creation must both roll back.


## Verification and delivery
- API full unit suite: 493 suites / 5,347 tests passed; 18 environment-gated suites / 198 tests skipped.
- Customer web full headless suite: 667 tests passed.
- Explicit isolated PostgreSQL runs: 16 tests passed, including atomic rollback, both operation orderings, safe replay after a new reservation, topup independence and a one-connection pool. Temporary PostgreSQL stopped after verification.
- API Nest build and production customer Angular build passed. Angular emitted a non-blocking initial-bundle budget warning (515.19 kB vs 500 kB).
- Browser: real PaymentHistoryComponent + shared ConfirmDialog rendered inside the customer app shell; exact approved notice and scheduled cancellation date/product verified. Local review URL: http://localhost:4203/mail-review-index.html#/my/payment-history . No external payment or refund request was sent.
- Independent scoped review found a transaction connection escape in replay/preview reads. Reproduced with failing tests; fixed by passing EntityManager through replay and binding all preview repositories. Follow-up review found no actionable issue.
- Ruling: existing dirty API/client working copies were continued in place to preserve the previously approved mail work. No branch rewrite, commit, push, production deployment, env change or database migration.
- Ruling: current-subscription GET exposes optional pendingRefundRequestId; the UI preserves it across mutation responses that omit it, and refreshes authoritative state on return. Automatic renewal policy and credit usage remain unchanged. No automatic mail triggers were connected.
