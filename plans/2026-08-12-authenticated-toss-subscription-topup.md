# Authenticated Toss Subscription and Top-up Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 로그인 사용자가 Toss로 자동 갱신 구독을 시작하고 선불 추가 크레딧을 단건 구매하며, 결제 성공 저장과 이용 자격·크레딧 fulfillment를 멱등으로 분리한다.

**Architecture:** `payment_orders`/`payment_events`는 모든 결제 의도의 불변 스냅샷과 공급자 이벤트를 보관한다. Toss 상태를 검증해 `paid`를 저장한 뒤 별도의 짧은 fulfillment 트랜잭션으로 구독·이용 자격·크레딧을 만든다. 익명 심사 주문은 같은 provider adapter를 쓰지만 fulfillment 상태를 `not_applicable`로 고정한다.

**Tech Stack:** NestJS 11, TypeORM/PostgreSQL, Jest 30, `@nestjs/schedule`, Toss Payments HTTP API, Node.js 22

## Global Constraints

- 작업 경로는 `/Users/jina/project/adlight/.worktrees/clipper_web_api-access-credit`, 브랜치는 `feat/access-credit-system-replacement`이다.
- `2026-08-12-access-credit-api-core.md`의 새 카탈로그·이용 자격·크레딧 서비스를 선행 계약으로 사용한다.
- Node 22를 사용한다.
- Toss 네트워크 호출 중 DB 트랜잭션을 유지하지 않는다.
- 주문 성공 저장과 fulfillment를 분리하고, fulfillment 재시도는 결제를 다시 실행하지 않는다.
- 단건 추가 크레딧은 활성 이용 자격이 있을 때만 checkout을 시작하지만, checkout 후 자격이 끝나도 성공한 결제는 지급한다.
- 익명 심사 checkout은 로그인 없이 유지하고 이용 자격·크레딧을 절대 지급하지 않는다.
- 공개 테스트 API key와 `TEST` mode는 심사·개발에만 쓰고 실서비스 key를 코드나 문서에 저장하지 않는다.
- 빌링키는 암호화해 저장하고 API 응답·이벤트 payload·로그에 평문으로 남기지 않는다.
- Toss 공식 계약 `https://docs-pay.toss.im/reference/billing/create`, `/billing/bill`, `/billing/remove`, `/billing/billing-key-status`, `/billing/result-callback`을 provider adapter의 근거로 사용한다.
- 사용자가 구독을 해지하면 다음 청구를 먼저 차단하고 Toss 빌링키 삭제를 재시도 가능한 상태로 처리한다. `REMOVED` 콜백도 같은 상태 전이를 사용한다.
- 갱신 실패 유예기간·재시도 횟수는 현재 상품 정책으로 발명하지 않는다. 재시도 시각은 빈 값을 허용하는 설정값으로 두고 빈 값이면 최초 실패 후 자동 재시도하지 않는다.
- 유료 구독 업그레이드 차액결제는 산식이 확정되지 않았으므로 API를 노출하지 않는다. 주문 `purpose` 열거형만 `subscription_upgrade` 이력을 표현할 수 있게 둔다.

---

### Task 1: Generalize Payment Orders and Add Subscriptions

**Files:**
- Modify: `docs/api/openapi.yaml`
- Create: `src/core/database/migrations/admin/1786700000000-GeneralizePaymentsAndCreateSubscriptions.ts`
- Create: `src/core/database/migrations/admin/1786700000000-GeneralizePaymentsAndCreateSubscriptions.spec.ts`
- Modify: `src/modules/payments/domain/payment.model.ts`
- Modify: `src/modules/payments/domain/payment-orders.repository.ts`
- Modify: `src/modules/payments/infrastructure/payment-order.entity.ts`
- Modify: `src/modules/payments/infrastructure/typeorm-payment-orders.repository.ts`
- Modify: `src/modules/payments/infrastructure/typeorm-payment-orders.repository.spec.ts`
- Create: `src/modules/payments/domain/subscriptions.repository.ts`
- Create: `src/modules/payments/infrastructure/subscription.entity.ts`
- Create: `src/modules/payments/infrastructure/typeorm-subscriptions.repository.ts`
- Create: `src/modules/payments/infrastructure/typeorm-subscriptions.repository.spec.ts`
- Modify: `src/modules/payments/payments.module.ts`
- Modify: `src/core/database/admin.datasource.ts`

**Interfaces:**
- Consumes: catalog product and tier IDs
- Produces: generalized `PaymentOrder` snapshots and persistent `Subscription`

- [ ] **Step 1: Write the migration contract test**

```ts
it('stores payment purpose, fulfillment state, authenticated owner, and immutable snapshots', () => {
  expect(upSql).toContain('purpose varchar(40) NOT NULL');
  expect(upSql).toContain('fulfillment_status varchar(20) NOT NULL');
  expect(upSql).toContain('user_id varchar(36)');
  expect(upSql).toContain('product_code varchar(50) NOT NULL');
  expect(upSql).toContain('credits_snapshot int');
  expect(upSql).toContain('CREATE TABLE subscriptions');
});
```

- [ ] **Step 2: Run the migration test and confirm failure**

Run: `nvm use 22 && npm test -- --runInBand src/core/database/migrations/admin/1786700000000-GeneralizePaymentsAndCreateSubscriptions.spec.ts`

Expected: FAIL because the migration does not exist.

- [ ] **Step 3: Define exact payment and subscription states**

```ts
export type PaymentPurpose =
  | 'subscription_initial'
  | 'subscription_renewal'
  | 'subscription_upgrade'
  | 'credit_topup'
  | 'review';
export type FulfillmentStatus = 'not_applicable' | 'pending' | 'succeeded' | 'failed';
export type SubscriptionStatus = 'pending' | 'active' | 'past_due' | 'cancel_at_period_end' | 'canceled' | 'ended';
export type BillingKeyRemovalStatus = 'not_requested' | 'pending' | 'succeeded' | 'failed';
```

Orders store nullable `userId`, `billingProductId`, `creditProductId`, `subscriptionId`, plus snapshots `productCode`, `productName`, `planTierId`, `planTierCode`, `billingIntervalMonths`, `amountKrw`, `monthlyCredits`, `creditsSnapshot`. Review orders use `purpose: 'review'` and `fulfillmentStatus: 'not_applicable'`.

Subscriptions store user/product/tier IDs, status, encrypted billing key, provider user/display IDs, `currentPeriodStart`, `currentPeriodEnd`, `nextBillingAt`, nullable `cancelAt`, nullable `retryAt`, `billingKeyRemovalStatus`, and timestamps. Add one partial unique index for an open subscription per user.

- [ ] **Step 4: Implement repository idempotency transitions**

Add `tryMarkPaid`, `tryBeginFulfillment`, `markFulfillmentSucceeded`, and `markFulfillmentFailed`. Each transition uses a conditional update, so duplicate callbacks cannot re-open fulfillment. Add subscription methods `withSubscriptionLock`, `findOpenByUserId`, `create`, `activate`, `markPastDue`, `scheduleCancellation`, and `extendPeriod`.

- [ ] **Step 5: Run repository tests and build**

Run: `nvm use 22 && npm test -- --runInBand src/modules/payments/infrastructure src/core/database/migrations/admin/1786700000000-GeneralizePaymentsAndCreateSubscriptions.spec.ts && npm run build`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add docs/api/openapi.yaml src/core/database/admin.datasource.ts src/core/database/migrations/admin/1786700000000-* src/modules/payments
git commit -m "feat: generalize payment orders and subscriptions"
```

### Task 2: Implement Authenticated Top-up Checkout and Fulfillment

**Files:**
- Modify: `docs/api/openapi.yaml`
- Create: `src/modules/payments/application/topup-payments.service.ts`
- Create: `src/modules/payments/application/topup-payments.service.spec.ts`
- Create: `src/modules/payments/application/payment-fulfillment.service.ts`
- Create: `src/modules/payments/application/payment-fulfillment.service.spec.ts`
- Create: `src/modules/payments/presentation/dto/create-topup-checkout.dto.ts`
- Create: `src/modules/payments/presentation/topup-payments.controller.ts`
- Create: `src/modules/payments/presentation/topup-payments.controller.spec.ts`
- Create: `src/modules/payments/presentation/payment-orders.controller.ts`
- Create: `src/modules/payments/presentation/payment-orders.controller.spec.ts`
- Modify: `src/modules/payments/presentation/toss-pay-callback.controller.ts`
- Modify: `src/modules/payments/presentation/toss-pay-callback.controller.spec.ts`
- Modify: `src/modules/payments/payments.module.ts`

**Interfaces:**
- Consumes: `ProductCatalogService.activeCreditProductById`, `AccessGrantsService.current`, `CreditGrantsService.grant`
- Produces: checkout configuration, `POST /payments/topups/checkout`, secret-token order result/reconcile, and idempotent top-up fulfillment

- [ ] **Step 1: Add the checkout and order-view contract**

```text
GET  /payments/config
POST /payments/topups/checkout
body: { creditProductId: string }
response: { checkoutUrl: string, orderNo: string }
GET  /payments/orders/{receiptToken}
POST /payments/orders/{receiptToken}/reconcile
```

Authenticated payment result views include `purpose`, `status`, `fulfillmentStatus`, product snapshot, amount, order number, and safe error message. They never expose pay token or billing key.

`GET /payments/config` returns `{ mode: 'checkout'|'local_notice' }`; loopback `WEB_BASE_URL` returns `local_notice` while deployed HTTPS returns `checkout` when required provider configuration is present. Secret-token order endpoints are safe return-page reads and return no user identity or provider secrets.

- [ ] **Step 2: Write failing service tests**

```ts
it('rejects checkout without effective access', async () => {
  access.current.mockResolvedValue(null);
  await expect(service.startCheckout(userId, { creditProductId })).rejects.toThrow('NO_ACTIVE_ACCESS');
  expect(toss.createOneTimePayment).not.toHaveBeenCalled();
});

it('fulfills a paid top-up once even if access ended after checkout', async () => {
  orders.tryBeginFulfillment.mockResolvedValue(true);
  access.current.mockResolvedValue(null);
  await fulfillment.fulfill(order({ purpose: 'credit_topup', status: 'paid' }));
  expect(credits.grant).toHaveBeenCalledWith(expect.objectContaining({
    source: 'topup',
    idempotencyKey: `payment:${orderId}:topup`,
  }));
});
```

- [ ] **Step 3: Run focused tests and confirm failure**

Run: `nvm use 22 && npm test -- --runInBand src/modules/payments/application/topup-payments.service.spec.ts src/modules/payments/application/payment-fulfillment.service.spec.ts`

Expected: FAIL because top-up checkout and fulfillment services do not exist.

- [ ] **Step 4: Implement checkout with no open transaction around Toss**

Validate user/access/product, create the pending order in one DB call, commit, call `TossPayProvider.createOneTimePayment`, then mark checkout ready. On provider setup failure, mark the order failed with a safe message.

- [ ] **Step 5: Implement verified callback then fulfillment**

The callback retrieves provider status and verifies mode, order number, amount, pay token, and transaction ID exactly as the review flow does. It first persists `paid` and a deduplicated provider event. It then calls `fulfill(orderId)` in a separate `AdminTransactionRunner.run`; access/credit/payment repositories use that transaction's `EntityManager`. A fulfillment exception leaves payment `paid`, sets fulfillment `failed`, and returns success to a provider callback already proven paid; an internal recovery worker retries only fulfillment.

- [ ] **Step 6: Run payment tests and build**

Run: `nvm use 22 && npm test -- --runInBand src/modules/payments && npm run build`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add docs/api/openapi.yaml src/modules/payments
git commit -m "feat: add authenticated topup checkout fulfillment"
```

### Task 3: Implement Initial Recurring Subscription Checkout

**Files:**
- Modify: `docs/api/openapi.yaml`
- Create: `src/modules/payments/application/subscription-payments.service.ts`
- Create: `src/modules/payments/application/subscription-payments.service.spec.ts`
- Create: `src/modules/payments/presentation/dto/create-subscription-checkout.dto.ts`
- Create: `src/modules/payments/presentation/subscription-payments.controller.ts`
- Create: `src/modules/payments/presentation/subscription-payments.controller.spec.ts`
- Modify: `src/modules/payments/application/payment-fulfillment.service.ts`
- Modify: `src/modules/payments/application/payment-fulfillment.service.spec.ts`
- Modify: `src/modules/payments/presentation/toss-pay-callback.controller.ts`
- Modify: `src/modules/payments/domain/toss-pay.provider.ts`
- Modify: `src/modules/payments/infrastructure/http-toss-pay.provider.ts`
- Modify: `src/modules/payments/infrastructure/http-toss-pay.provider.spec.ts`
- Modify: `src/modules/payments/payments.module.ts`

**Interfaces:**
- Consumes: active auto-renewing `BillingProduct`, encrypted Toss billing key, access and credit services
- Produces: `POST /payments/subscriptions/checkout`, `GET /subscriptions/current`, `POST /subscriptions/current/retry`, and `POST /subscriptions/current/cancel`

- [ ] **Step 1: Add exact authenticated subscription routes**

```text
POST /payments/subscriptions/checkout  body { billingProductId }
GET  /subscriptions/current
POST /subscriptions/current/retry     body {}
POST /subscriptions/current/cancel    body { reason }
```

Reject products where `autoRenews` is false. Reject a second open subscription with `ACTIVE_ACCESS_CONFLICT`/`DUPLICATE_REQUEST` before calling Toss.

- [ ] **Step 2: Write failing initial-subscription tests**

```ts
it('creates one pending subscription and a recurring checkout', async () => {
  const result = await service.startCheckout(userId, { billingProductId });
  expect(subscriptions.create).toHaveBeenCalledWith(expect.objectContaining({ status: 'pending' }));
  expect(toss.createBillingKey).toHaveBeenCalledTimes(1);
  expect(result.checkoutUrl).toBe(checkoutUri);
});

it('activates subscription, access, and first monthly credits exactly once after first charge', async () => {
  await fulfillment.fulfill(paidInitialOrder);
  expect(access.activateSubscription).toHaveBeenCalledTimes(1);
  expect(credits.grant).toHaveBeenCalledWith(expect.objectContaining({ source: 'subscription' }));
  expect(subscriptions.activate).toHaveBeenCalledTimes(1);
});
```

- [ ] **Step 3: Run tests and confirm failure**

Run: `nvm use 22 && npm test -- --runInBand src/modules/payments/application/subscription-payments.service.spec.ts src/modules/payments/application/payment-fulfillment.service.spec.ts`

Expected: FAIL because subscription checkout does not exist.

- [ ] **Step 4: Implement billing-key registration and first charge**

Create a stable provider user ID derived from the internal user UUID with a non-secret SHA-256 prefix, and a unique display ID per subscription checkout. Store only the encrypted billing key. After Toss reports billing status `ACTIVE`, execute the first charge outside a DB transaction, verify the charge result, persist the paid order, then fulfillment creates/activates the subscription access grant and first monthly credit grant.

- [ ] **Step 5: Implement cancel-at-period-end**

Cancellation sets subscription status `cancel_at_period_end`, leaves current access and credits unchanged, clears `nextBillingAt`, and records an event. It does not perform an immediate refund. The access ends at `currentPeriodEnd` and future monthly grants stop at that boundary.

- [ ] **Step 6: Run subscription tests and build**

Run: `nvm use 22 && npm test -- --runInBand src/modules/payments && npm run build`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add docs/api/openapi.yaml src/modules/payments
git commit -m "feat: add recurring subscription checkout"
```

### Task 4: Add Renewal, Cancellation-Key Removal, Failed-Payment State, and Fulfillment Recovery

**Files:**
- Create: `src/modules/payments/application/subscription-renewal.service.ts`
- Create: `src/modules/payments/application/subscription-renewal.service.spec.ts`
- Create: `src/modules/payments/application/payment-recovery.scheduler.ts`
- Create: `src/modules/payments/application/payment-recovery.scheduler.spec.ts`
- Create: `src/modules/payments/domain/subscription-retry-policy.ts`
- Create: `src/modules/payments/domain/subscription-retry-policy.spec.ts`
- Modify: `src/modules/payments/domain/subscriptions.repository.ts`
- Modify: `src/modules/payments/infrastructure/typeorm-subscriptions.repository.ts`
- Modify: `src/modules/payments/application/payment-fulfillment.service.ts`
- Modify: `src/modules/payments/domain/toss-pay.provider.ts`
- Modify: `src/modules/payments/infrastructure/http-toss-pay.provider.ts`
- Modify: `src/modules/payments/infrastructure/http-toss-pay.provider.spec.ts`
- Modify: `src/modules/payments/payments.module.ts`

**Interfaces:**
- Consumes: subscription `nextBillingAt`, encrypted billing key, product snapshot, fulfillment state
- Produces: one idempotent renewal order per subscription cycle and recoverable `past_due` state

- [ ] **Step 1: Write failing renewal idempotency tests**

```ts
it('creates at most one renewal order per subscription period', async () => {
  await Promise.all([service.renew(subscriptionId, now), service.renew(subscriptionId, now)]);
  expect(orders.createRenewalForCycle).toHaveReturnedWith(expect.anything());
  expect(toss.chargeBillingKey).toHaveBeenCalledTimes(1);
});

it('marks past_due without ending access immediately when renewal fails', async () => {
  toss.chargeBillingKey.mockRejectedValue(providerDecline);
  await service.renew(subscriptionId, now);
  expect(subscriptions.markPastDue).toHaveBeenCalledWith(subscriptionId, expect.objectContaining({ retryAt: null }));
  expect(access.revoke).not.toHaveBeenCalled();
});
```

- [ ] **Step 2: Run tests and confirm failure**

Run: `nvm use 22 && npm test -- --runInBand src/modules/payments/application/subscription-renewal.service.spec.ts src/modules/payments/application/payment-recovery.scheduler.spec.ts`

Expected: FAIL because renewal and recovery workers do not exist.

- [ ] **Step 3: Implement one short locked claim, external charge, then persistence**

The service locks the subscription, creates or finds the cycle order with unique key `renewal:${subscriptionId}:${currentPeriodEnd.toISOString()}`, commits, charges Toss, then opens a new short transaction to store the result. Successful fulfillment extends `currentPeriodEnd` by `billingIntervalMonths`, updates the linked access end, sets the next bill date, and does not grant extra credits immediately; monthly grant scheduling remains the only monthly credit source.

- [ ] **Step 4: Make retry timing configuration explicit**

Add optional env `SUBSCRIPTION_RETRY_DELAYS_MINUTES` as a comma-separated sequence of positive integers. `parseSubscriptionRetryDelays(value: string | undefined): number[]` returns an empty list for empty/absent input and rejects zero, negative, duplicate, or non-integer values. A configured sequence creates `retryAt` values without embedding a business default in code. Every retry reuses the same cycle order and never creates a second successful charge.

`POST /subscriptions/current/retry` invokes the same locked cycle retry after an explicit user action. It is accepted only for `past_due`, and the cycle/order idempotency check returns the already-paid result without issuing another Toss approval.

- [ ] **Step 5: Add fulfillment recovery**

Every minute, find a bounded batch of `paid` orders with fulfillment `pending` or `failed` and retry `PaymentFulfillmentService.fulfill(orderId)`. The conditional claim and credit/access/subscription idempotency keys make duplicate workers safe.

- [ ] **Step 6: Delete billing keys without reopening renewal**

`POST /subscriptions/current/cancel` first locks the subscription, sets `cancel_at_period_end`, clears `nextBillingAt`, and marks billing-key removal `pending`, then commits. `TossPayProvider.removeBillingKey({ billingKey })` runs outside the transaction against `/api/v1/billing-key/remove`. Success or a verified `REMOVE`/`CANCEL` status clears the encrypted key and marks removal `succeeded`; transient failure leaves cancellation effective and the recovery scheduler retries only key removal. An unsolicited `action: 'REMOVED'` callback performs the same idempotent transition and never triggers a charge.

When `currentPeriodEnd` passes without a successful renewal, the scheduler ends the subscription access for every tier; it never downgrades to another paid tier. Existing unexpired credit grants remain held, `spendableBalance` becomes 0, and reactivation can make those still-valid grants spendable again.

- [ ] **Step 7: Run payment tests and build**

Run: `nvm use 22 && npm test -- --runInBand src/modules/payments && npm run build`

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add src/modules/payments
git commit -m "feat: add subscription renewal and payment recovery"
```

### Task 5: Move Anonymous Review Checkout onto the New Catalog

**Files:**
- Modify: `docs/api/openapi.yaml`
- Modify: `src/modules/payments/application/review-payments.service.ts`
- Modify: `src/modules/payments/application/review-payments.service.spec.ts`
- Modify: `src/modules/payments/presentation/dto/create-review-checkout.dto.ts`
- Modify: `src/modules/payments/presentation/review-payments.controller.ts`
- Modify: `src/modules/payments/presentation/review-payments.controller.spec.ts`
- Modify: `src/modules/payments/payments.module.ts`

**Interfaces:**
- Consumes: `ProductCatalogService.activeProductById`
- Produces: unchanged anonymous review capability using `{ billingProductId, paymentType }` and no fulfillment

- [ ] **Step 1: Write the no-fulfillment regression test**

```ts
it('stores anonymous review orders as not_applicable and never calls fulfillment', async () => {
  await service.startCheckout({ billingProductId, paymentType: 'one_time' });
  expect(orders.create).toHaveBeenCalledWith(expect.objectContaining({
    purpose: 'review', userId: null, fulfillmentStatus: 'not_applicable',
  }));
  expect(fulfillment.fulfill).not.toHaveBeenCalled();
});
```

Also keep recurring review restricted to 1/3-month products and one-time review to 1/3/12-month products.

- [ ] **Step 2: Run review tests and confirm failure**

Run: `nvm use 22 && npm test -- --runInBand src/modules/payments/application/review-payments.service.spec.ts src/modules/payments/presentation/review-payments.controller.spec.ts`

Expected: FAIL because the service still injects legacy `PlansService` and accepts `planId`.

- [ ] **Step 3: Replace the legacy plan dependency**

Inject `ProductCatalogService`, accept `billingProductId`, and snapshot product/tier/monthly credits. Preserve secret receipt token lookup, short polling/reconcile, callback URL rules, local unavailability notice, and the existing public-test-key provider behavior.

- [ ] **Step 4: Prove duplicate recurring review registration stays isolated**

Keep a unique review provider user ID per review attempt, so one card already registered to the test merchant can be surfaced as a provider limitation without touching real user subscriptions or fulfillment.

- [ ] **Step 5: Run all payment tests and build**

Run: `nvm use 22 && npm test -- --runInBand src/modules/payments && npm run build`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add docs/api/openapi.yaml src/modules/payments
git commit -m "refactor: move toss review checkout to product catalog"
```
