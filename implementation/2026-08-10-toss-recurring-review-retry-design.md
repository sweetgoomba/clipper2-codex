# Toss Recurring Review Retry Fix Design

## Goal

Make Toss Pay recurring checkout repeatable during anonymous card-company review,
and keep Clipper's review order status consistent with Toss when billing-key
registration is canceled or fails without a callback.

The change remains limited to the dev-only Toss review payment flow. It does not
grant credits or licenses and does not define the production subscription model.

## Confirmed failure

The first recurring test completed through `ACTIVE`, the first billing charge,
and local `paid` persistence. Three later attempts stopped after the local
`billing_key_created` event. Direct Toss status checks reported one `FAIL` and
two `CANCEL` billing keys while the corresponding local orders remained
`checkout_ready`.

Two existing behaviors explain the mismatch:

1. Billing-key creation omits Toss's optional `displayId`, although Toss requires
   it when the same payment method must be registered more than once.
2. `reconcileReviewOrder()` reconciles one-time payments only. Toss normally
   does not callback for retryable billing registration failures, so recurring
   orders cannot currently learn `CANCEL` or `FAIL` from the status API.

## Considered approaches

### 1. Delete the prior test billing key before every retry

This can unblock one known payment method but mutates shared test-store state,
requires manual secret handling, and cannot control registrations created by
other users of the public test key. It is unsuitable as the normal review flow.

### 2. Require every reviewer to use a never-before-registered payment method

This requires no code change, but it is not reproducible because the public test
API key is shared and a reviewer cannot know which payment methods are already
registered.

### 3. Use a unique `displayId` and reconcile recurring billing status

This follows Toss's documented multiple-billing-key mechanism and makes failed
or canceled registrations visible locally. This is the selected approach.

## Design

### Billing-key identity

For each review recurring order:

- Continue generating the existing unique `reviewUserId`.
- Send `displayId = orderNo` when creating the billing key.
- Send the same `userId + displayId` pair when querying billing-key status.
- Accept `displayId` in the Toss result callback and require it to equal the
  matched order's `orderNo` before changing order state.

`orderNo` is already persisted, unique, uses Toss-compatible characters, and is
shorter than Toss's 50-character limit. No new database column or migration is
needed.

### Recurring reconciliation

When the private receipt-token reconciliation endpoint reads a non-terminal
recurring order, it will decrypt the stored billing key and query Toss with the
order's `reviewUserId` and `orderNo` display ID. It will verify that the response
belongs to the expected user and billing key before acting.

State handling:

| Toss status | Local result |
| --- | --- |
| `CREATE` | Keep `checkout_ready`; registration is still pending |
| `ACTIVE` | Record activation idempotently and run/reconcile the first charge |
| `CANCEL` | Mark `canceled` and record a deduplicated `billing_canceled` event |
| `FAIL` | Mark `failed` with `billing_registration_failed` and record a deduplicated `billing_registration_failed` event |
| `REMOVE` | Mark `failed` with `billing_removed` and record a deduplicated `billing_removed` event |
| Unknown | Leave the order unchanged; do not infer a terminal result |

Terminal local orders (`paid`, `canceled`, or `failed`) will not call Toss again.
Repeated result-page polling remains idempotent through existing terminal-state
checks and unique event deduplication keys.

### Callback flow

The successful callback continues to be the fastest path:

1. Match the order by `userId`.
2. Verify callback `displayId` and encrypted billing key against the order.
3. Query Toss using `userId + displayId`.
4. Verify `ACTIVE` and payment method.
5. Mark billing active, record `billing_activated`, and perform the first charge.

The result-page reconciliation is a fallback for a missed success callback and
the primary way to observe failure statuses for which Toss sends no callback.

## Error and security behavior

- Never expose or log the plaintext billing key.
- Reject callback or status data whose user, display ID, or billing key does not
  match the stored order.
- Provider/network errors remain temporary service failures and do not mark the
  order failed.
- Toss `CREATE` remains non-terminal.
- Existing public receipt-token hashing and API key handling remain unchanged.

## Files in scope

- `src/modules/payments/domain/toss-pay.provider.ts`
- `src/modules/payments/infrastructure/http-toss-pay.provider.ts`
- `src/modules/payments/application/review-payments.service.ts`
- `src/modules/payments/presentation/dto/billing-result-callback.dto.ts`
- Their existing focused Jest specifications

No client, infra, database migration, credit, license, or legacy purchase-request
code changes are required.

## Verification

Automated tests must prove:

- billing-key creation sends `displayId = orderNo`;
- billing-key status lookup sends both `userId` and `displayId`;
- callbacks reject a mismatched display ID;
- recurring reconciliation leaves `CREATE` pending;
- recurring reconciliation maps `CANCEL`, `FAIL`, and `REMOVE` correctly;
- recurring reconciliation resumes an `ACTIVE` order through the first charge;
- terminal orders do not call Toss again;
- existing one-time payment behavior remains unchanged.

After deployment, the browser smoke test repeats recurring checkout with a
previously registered test card and confirms the new order reaches `paid`. A
canceled registration must no longer remain indefinitely ambiguous once its
result page reconciles the order.
