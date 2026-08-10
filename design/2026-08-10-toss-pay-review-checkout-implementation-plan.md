# Toss Pay Review Checkout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 비로그인 심사자가 dev 요금 페이지에서 Toss Pay 공용 테스트 키로 단건결제와 빌링키 기반 최초 결제를 완료하고, 검증된 결제 결과를 Clipper DB와 공개 결과 페이지에서 확인할 수 있게 한다.

**Architecture:** `clipper_web_api`에 독립 `payments` 모듈을 추가하고 Toss Pay wire 형식은 provider adapter 안에 격리한다. Angular는 공개 checkout 생성과 공개 영수증 조회만 호출하며, 가격·상태·결제 승인은 서버가 소유한다. 기존 무통장 구매 요청과 이용권/크레딧 발급 경로는 호출하지 않는다.

**Tech Stack:** Node.js 22, NestJS 11, TypeScript, TypeORM/PostgreSQL(admin DataSource), Jest, Angular 19 standalone components/signals, RxJS, Jasmine/Karma, Docker Compose.

## Global Constraints

- 모든 저장소는 `feat/toss-pay-review-checkout` 브랜치에서 작업한다.
- 설계·계획·진행 문서는 코드 저장소가 아니라 `/Users/jina/project/adlight/.codex`에만 둔다.
- 코드 저장소에 새 Markdown 파일을 만들지 않는다.
- 앱 코드 저장소와 `.codex` 커밋은 분리한다.
- 커밋 명령은 계획에 제시하지만 사용자가 명시적으로 커밋을 요청하기 전에는 실행하지 않는다.
- API 응답은 기존 raw 계약을 유지하며 `{ data: ... }` 봉투를 추가하지 않는다.
- `clipper_web_api` 신규 feature는 `modules/<feature>/{domain,application,infrastructure,presentation}`와 상대경로 `.js` import 규칙을 따른다.
- DB 컬럼은 snake_case이고 TypeORM `@Column({ name })`으로 명시한다.
- Angular 컴포넌트는 `.ts/.html/.scss/.spec.ts` 4파일로 분리한다.
- 1개월·3개월은 `정기결제`와 `단건결제`, 12개월은 `단건결제`만 표시한다.
- 12개월 `recurring` 요청은 서버에서도 400으로 거부한다.
- 비로그인 checkout 생성은 `CLIPPER_ENV=dev`와 `TOSS_PAY_REVIEW_MODE=true`가 모두 참일 때만 허용한다.
- 공용 테스트 키는 `TOSS_PAY_API_KEY` 서버 환경변수에만 두고 Angular 번들·로그·DB 이벤트에 넣지 않는다.
- 빌링키는 기존 `SecretCipher`로 암호화 저장하고 평문을 로그·응답에 노출하지 않는다.
- 단건결제는 `PAY_COMPLETE`를 상태 API로 재검증한 뒤 저장한다.
- 정기결제는 빌링키 `ACTIVE` 재검증 후 최초 테스트 결제 1회만 실행한다.
- 반복 청구, 해지, 환불, 회원 연결, 이용권·크레딧 자동 지급은 구현하지 않는다.
- 브라우저 return URL과 callback payload만으로 `paid`를 기록하지 않는다.
- 결과 페이지 폴링은 2초 간격, 최대 10회로 제한한다.
- 구현 중 공식 문서가 설계와 충돌하면 `https://docs-pay.toss.im/llms.txt`와 링크된 최신 공식 문서를 우선하고 설계 문서를 함께 수정한다.

---

## 구현 중 독립 리뷰 반영 (2026-08-10)

- 서버 capability가 심사용 checkout 노출을 결정하며, 비활성·오류 환경은 기존 `/app/purchase` 구매 요청 동선을 보존한다.
- 익명 checkout은 dev + review mode + `sk_test_` 키 + 안전한 HTTPS base URL에서만 활성화하고, 결제 완료는 provider `TEST` 결과만 허용한다.
- 서버 허용 조합을 1·3개월 `one_time | recurring`, 12개월 `one_time`으로 제한한다.
- 취소 브라우저 복귀는 금융 상태를 바꾸지 않으며, 별도 reconcile API가 provider의 `PAY_CANCEL` 또는 `PAY_COMPLETE`를 확인한다.
- 최초 빌링 청구는 transaction-scoped repository와 주문 advisory lock으로 직렬화한다. `payment_pending` lease와 provider 상태 조회로 중복·불확실 응답을 복구한다.
- reverse proxy는 배포 구조에 맞춰 정확히 한 홉만 신뢰하고 공개 API rate limit에 실제 client IP를 사용한다.

---

## 승인된 후속 변경: 로컬 결제 UI 표시 모드 (2026-08-10)

**Goal:** 로컬 요금 페이지에도 dev와 동일한 Toss Pay 버튼을 표시하되 실제 checkout 대신 로컬 사용 불가 안내를 제공하고, stage/prod의 기존 구매 요청 fallback은 유지한다.

**Files:**

- Modify/Test: `web/clipper_web_api/src/modules/payments/application/review-payments.service.ts`
- Modify/Test: `web/clipper_web_api/src/modules/payments/application/review-payments.service.spec.ts`
- Modify/Test: `web/clipper_web_api/src/modules/payments/presentation/review-payments.controller.spec.ts`
- Modify: `web/clipper_web_api/docs/api/openapi.yaml`
- Modify: `web/clipper_web_client/src/app/core/api/models.ts`
- Modify/Test: `web/clipper_web_client/src/app/features/public/pricing/pricing.component.ts`
- Modify: `web/clipper_web_client/src/app/features/public/pricing/pricing.component.html`
- Modify/Test: `web/clipper_web_client/src/app/features/public/pricing/pricing.component.spec.ts`

**Interfaces:**

- Replace `ReviewCheckoutConfig { enabled: boolean }` with `ReviewCheckoutConfig { mode: 'checkout' | 'local_notice' | 'legacy_purchase' }`.
- `reviewCheckoutConfig()` returns `local_notice` when `WEB_BASE_URL` has a loopback hostname, `checkout` only for the existing safe dev review configuration, and `legacy_purchase` otherwise.
- `startCheckout()` keeps all existing provider/security checks; `local_notice` is a presentation capability only.

- [x] Add failing API tests for all three modes, including HTTP/HTTPS loopback and malformed/non-review fallbacks.
- [x] Implement the minimal server capability mode and update controller/OpenAPI expectations.
- [x] Run focused API tests and build.
- [x] Add failing Angular tests proving local buttons match checkout mode, clicking calls no checkout API, and the exact local 안내 is rendered.
- [x] Implement the mode signal/template branches while preserving checkout and legacy behavior.
- [x] Run focused/full client tests and build.
- [x] Run full API payment tests, OpenAPI parse, secret scan, and diff checks; record results in `.codex/implementation/WORKLOG.md`.

---

### Task 0: `.codex` 구현 추적 문서 준비

**Files:**
- Create: `/Users/jina/project/adlight/.codex/implementation/TASKS.md`
- Create: `/Users/jina/project/adlight/.codex/implementation/WORKLOG.md`

**Interfaces:**
- Consumes: 승인된 설계 `design/2026-08-10-toss-pay-review-checkout-design.md`와 이 구현 계획.
- Produces: 모든 후속 Task가 체크 상태와 검증 결과를 기록할 단일 진행 문서.

- [ ] **Step 1: `TASKS.md`에 범위와 저장소 상태를 기록한다**

```markdown
# Toss Pay Review Checkout Tasks

설계: `../design/2026-08-10-toss-pay-review-checkout-design.md`
계획: `../design/2026-08-10-toss-pay-review-checkout-implementation-plan.md`
브랜치: `feat/toss-pay-review-checkout`

- [ ] Contract and active-plan boundary
- [ ] Payment persistence
- [ ] Toss Pay provider adapter
- [ ] Checkout application flow
- [ ] Callback and first billing charge
- [ ] HTTP/module wiring
- [ ] Pricing checkout UI
- [ ] Public payment result UI
- [ ] Infra env wiring
- [ ] Full verification and dev smoke test

비범위: 이용권·크레딧 지급, 반복 청구, 해지, 환불, 운영 키 전환.
```

- [ ] **Step 2: `WORKLOG.md` 골격을 만든다**

```markdown
# Toss Pay Review Checkout Worklog

## Changed repositories

## Meaningful changes

## Verification

## Remaining risks
```

- [ ] **Step 3: 문서 위치와 브랜치를 검증한다**

Run:

```bash
git -C /Users/jina/project/adlight/.codex status --short --branch
git -C /Users/jina/project/adlight/web/clipper_web_client status --short --branch
git -C /Users/jina/project/adlight/web/clipper_web_api status --short --branch
git -C /Users/jina/project/adlight/web/clipper_infra status --short --branch
```

Expected: 네 저장소 모두 `feat/toss-pay-review-checkout`; 코드 저장소에는 변경 없음.

- [ ] **Step 4: 커밋 권한이 있을 때만 문서 변경을 커밋한다**

```bash
git add design/2026-08-10-toss-pay-review-checkout-design.md design/2026-08-10-toss-pay-review-checkout-implementation-plan.md implementation/TASKS.md implementation/WORKLOG.md
git commit -m "docs(toss-pay): plan review checkout integration"
```

### Task 1: OpenAPI 계약과 활성 플랜 조회 경계

**Files:**
- Modify: `web/clipper_web_api/docs/api/openapi.yaml`
- Test: `web/clipper_web_api/src/modules/billing/application/plans.service.spec.ts`
- Modify: `web/clipper_web_api/src/modules/billing/application/plans.service.ts`
- Modify: `web/clipper_web_api/src/modules/billing/billing.module.ts`

**Interfaces:**
- Consumes: 기존 `PlansRepository.findById(id: string): Promise<Plan | undefined>`.
- Produces: `PlansService.activeById(id: string): Promise<Plan>`와 OpenAPI schemas `ReviewPaymentType`, `ReviewPaymentStatus`, `CreateReviewCheckoutRequest`, `CreateReviewCheckoutResponse`, `ReviewPaymentOrder`.

- [ ] **Step 1: 활성 플랜만 반환하는 실패 테스트를 추가한다**

```ts
it('returns an active plan by id and rejects missing or inactive plans', async () => {
  const active = { id: 'p1', name: '1개월', months: 1, priceKrw: 19900, tokenAllowance: 100, isActive: true };
  const svc = new PlansService(fakeRepo([active]));

  await expect(svc.activeById('p1')).resolves.toEqual(active);
  await expect(svc.activeById('missing')).rejects.toThrow('plan not found');

  const inactiveSvc = new PlansService(fakeRepo([{ ...active, isActive: false }]));
  await expect(inactiveSvc.activeById('p1')).rejects.toThrow('plan not found');
});
```

- [ ] **Step 2: 테스트가 실패하는지 확인한다**

Run:

```bash
npm test -- --runInBand --runTestsByPath src/modules/billing/application/plans.service.spec.ts
```

Expected: FAIL because `activeById` does not exist.

- [ ] **Step 3: `PlansService.activeById`를 최소 구현하고 export한다**

```ts
async activeById(id: string): Promise<Plan> {
  const plan = await this.repo.findById(id);
  if (!plan || !plan.isActive) throw new NotFoundException('plan not found');
  return plan;
}
```

`BillingModule`의 `exports`에 `PlansService`를 추가한다.

- [ ] **Step 4: OpenAPI schemas와 네 경로를 추가한다**

```yaml
ReviewPaymentType:
  type: string
  enum: [one_time, recurring]
ReviewPaymentStatus:
  type: string
  enum: [created, checkout_ready, billing_active, payment_pending, paid, canceled, failed]
CreateReviewCheckoutRequest:
  type: object
  required: [planId, paymentType]
  properties:
    planId: { type: string, format: uuid }
    paymentType: { $ref: '#/components/schemas/ReviewPaymentType' }
CreateReviewCheckoutResponse:
  type: object
  required: [checkoutUrl]
  properties:
    checkoutUrl: { type: string, format: uri }
ReviewPaymentOrder:
  type: object
  required: [status, paymentType, planName, months, amountKrw, orderNo, testPayment, errorMessage]
  properties:
    status: { $ref: '#/components/schemas/ReviewPaymentStatus' }
    paymentType: { $ref: '#/components/schemas/ReviewPaymentType' }
    planName: { type: string }
    months: { type: integer }
    amountKrw: { type: integer }
    orderNo: { type: string }
    testPayment: { type: boolean }
    errorMessage: { type: string, nullable: true }
```

Add paths:

- `POST /payments/review/checkout`
- `GET /payments/review/orders/{receiptToken}`
- `POST /payments/toss/normal/result-callback`
- `POST /payments/toss/billing/result-callback`

Document checkout/result as unauthenticated review endpoints and callbacks as Toss server endpoints.

- [ ] **Step 5: 테스트와 계약 문자열을 검증한다**

Run:

```bash
npm test -- --runInBand --runTestsByPath src/modules/billing/application/plans.service.spec.ts
rg -n "/payments/review/checkout|/payments/review/orders|/payments/toss/normal/result-callback|/payments/toss/billing/result-callback" docs/api/openapi.yaml
```

Expected: test PASS; four paths found once each.

- [ ] **Step 6: 커밋 권한이 있을 때만 API 계약 커밋을 만든다**

```bash
git add docs/api/openapi.yaml src/modules/billing/application/plans.service.ts src/modules/billing/application/plans.service.spec.ts src/modules/billing/billing.module.ts
git commit -m "feat(payments): define review checkout contract"
```

### Task 2: 결제 주문·이벤트 영속성

**Files:**
- Create: `web/clipper_web_api/src/modules/payments/domain/payment.model.ts`
- Create: `web/clipper_web_api/src/modules/payments/domain/payment-orders.repository.ts`
- Create: `web/clipper_web_api/src/modules/payments/infrastructure/payment-order.entity.ts`
- Create: `web/clipper_web_api/src/modules/payments/infrastructure/payment-event.entity.ts`
- Create: `web/clipper_web_api/src/modules/payments/infrastructure/typeorm-payment-orders.repository.ts`
- Test: `web/clipper_web_api/src/modules/payments/infrastructure/typeorm-payment-orders.repository.spec.ts`
- Create: `web/clipper_web_api/src/core/database/migrations/admin/1786300000000-CreatePaymentOrders.ts`
- Modify: `web/clipper_web_api/src/core/database/admin.datasource.ts`
- Test: `web/clipper_web_api/src/core/database/admin.datasource.spec.ts`

**Interfaces:**
- Consumes: named TypeORM DataSource `admin`.
- Produces: `PaymentOrder`, `PaymentEvent`, `PaymentOrdersRepository` and atomic state transition methods used by Tasks 4–6.

- [ ] **Step 1: 도메인 타입과 repository 계약을 테스트에서 먼저 고정한다**

```ts
export type ReviewPaymentType = 'one_time' | 'recurring';
export type ReviewPaymentStatus =
  | 'created'
  | 'checkout_ready'
  | 'billing_active'
  | 'payment_pending'
  | 'paid'
  | 'canceled'
  | 'failed';

export interface PaymentOrder {
  id: string;
  orderNo: string;
  paymentType: ReviewPaymentType;
  reviewUserId: string | null;
  planId: string;
  planName: string;
  months: number;
  amountKrw: number;
  tokenAllowance: number;
  status: ReviewPaymentStatus;
  receiptTokenHash: string;
  payToken: string | null;
  billingKeyEnc: string | null;
  payMethod: string | null;
  paidAmountKrw: number | null;
  transactionId: string | null;
  tossMode: 'TEST' | 'LIVE' | null;
  errorCode: string | null;
  errorMessage: string | null;
  checkoutReadyAt: Date | null;
  billingActivatedAt: Date | null;
  paidAt: Date | null;
  failedAt: Date | null;
  createdAt: Date;
  updatedAt: Date;
}

export interface NewPaymentOrder {
  orderNo: string;
  paymentType: ReviewPaymentType;
  reviewUserId: string | null;
  planId: string;
  planName: string;
  months: number;
  amountKrw: number;
  tokenAllowance: number;
  receiptTokenHash: string;
}

export interface CheckoutReadyPatch {
  payToken?: string;
  billingKeyEnc?: string;
}

export interface PaidPaymentResult {
  mode: 'TEST' | 'LIVE';
  payToken: string;
  payMethod: string;
  paidAmountKrw: number;
  transactionId: string;
}

export interface NewPaymentEvent {
  paymentOrderId: string;
  eventType: string;
  dedupeKey: string | null;
  providerStatus: string | null;
  payload: Record<string, string | number | boolean | null>;
}
```

Repository contract must include:

```ts
abstract create(input: NewPaymentOrder): Promise<PaymentOrder>;
abstract findByOrderNo(orderNo: string): Promise<PaymentOrder | undefined>;
abstract findByReviewUserId(userId: string): Promise<PaymentOrder | undefined>;
abstract findByReceiptTokenHash(hash: string): Promise<PaymentOrder | undefined>;
abstract markCheckoutReady(id: string, patch: CheckoutReadyPatch): Promise<PaymentOrder>;
abstract markBillingActive(id: string, payMethod: string): Promise<PaymentOrder>;
abstract tryBeginFirstCharge(id: string): Promise<boolean>;
abstract markPaid(id: string, result: PaidPaymentResult): Promise<PaymentOrder>;
abstract markFailed(id: string, errorCode: string, errorMessage: string): Promise<PaymentOrder>;
abstract recordEvent(input: NewPaymentEvent): Promise<boolean>;
```

- [ ] **Step 2: repository 테스트를 작성한다**

Use a repository fixture whose mocked TypeORM repository exposes `findOne`, `save`, and `createQueryBuilder`. Cover these exact assertions:

```ts
it('finds and maps a review order by receipt token hash', async () => {
  orders.findOne.mockResolvedValue(entityFixture);
  await expect(repository.findByReceiptTokenHash('a'.repeat(64))).resolves.toMatchObject({
    orderNo: entityFixture.orderNo,
    receiptTokenHash: 'a'.repeat(64),
    billingKeyEnc: entityFixture.billingKeyEnc,
    status: entityFixture.status,
  });
  expect(orders.findOne).toHaveBeenCalledWith({ where: { receiptTokenHash: 'a'.repeat(64) } });
});

it('claims the first recurring charge only from billing_active', async () => {
  execute.mockResolvedValueOnce({ affected: 1 }).mockResolvedValueOnce({ affected: 0 });
  await expect(repository.tryBeginFirstCharge(entityFixture.id)).resolves.toBe(true);
  await expect(repository.tryBeginFirstCharge(entityFixture.id)).resolves.toBe(false);
  expect(where).toHaveBeenCalledWith('id = :id AND status = :status', {
    id: entityFixture.id,
    status: 'billing_active',
  });
});

it('records a duplicate event key only once', async () => {
  execute.mockResolvedValueOnce({ identifiers: [{ id: 'event-1' }] }).mockResolvedValueOnce({ identifiers: [] });
  await expect(repository.recordEvent(eventInput)).resolves.toBe(true);
  await expect(repository.recordEvent(eventInput)).resolves.toBe(false);
  expect(orIgnore).toHaveBeenCalledTimes(2);
});
```

- [ ] **Step 3: repository 테스트가 실패하는지 확인한다**

Run:

```bash
npm test -- --runInBand --runTestsByPath src/modules/payments/infrastructure/typeorm-payment-orders.repository.spec.ts
```

Expected: FAIL because payment domain/entity/repository files do not exist.

- [ ] **Step 4: migration 테스트를 먼저 추가한다**

Extend `admin.datasource.spec.ts` to assert:

```ts
expect(entityNames).toContain('PaymentOrderEntity');
expect(entityNames).toContain('PaymentEventEntity');
expect(migrationNames).toContain('CreatePaymentOrders1786300000000');
```

Add a migration SQL test that expects:

```ts
expect(sql).toContain('CREATE TABLE IF NOT EXISTS payment_orders');
expect(sql).toContain('CREATE TABLE IF NOT EXISTS payment_events');
expect(sql).toContain('receipt_token_hash');
expect(sql).toContain('billing_key_enc');
expect(sql).toContain('UNIQUE');
```

- [ ] **Step 5: migration과 엔티티를 구현한다**

The migration creates:

```sql
CREATE TABLE IF NOT EXISTS payment_orders (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  order_no varchar(50) NOT NULL UNIQUE,
  payment_type varchar(20) NOT NULL CHECK (payment_type IN ('one_time', 'recurring')),
  review_user_id varchar(50) UNIQUE,
  plan_id uuid NOT NULL,
  plan_name varchar(255) NOT NULL,
  months int NOT NULL CHECK (months > 0),
  amount_krw int NOT NULL CHECK (amount_krw > 0),
  token_allowance int NOT NULL CHECK (token_allowance >= 0),
  status varchar(30) NOT NULL,
  receipt_token_hash char(64) NOT NULL UNIQUE,
  pay_token varchar(50) UNIQUE,
  billing_key_enc text,
  pay_method varchar(20),
  paid_amount_krw int,
  transaction_id varchar(64) UNIQUE,
  toss_mode varchar(10),
  error_code varchar(120),
  error_message varchar(500),
  checkout_ready_at timestamptz,
  billing_activated_at timestamptz,
  paid_at timestamptz,
  failed_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CHECK (status IN ('created','checkout_ready','billing_active','payment_pending','paid','canceled','failed'))
);
```

`payment_events` uses `payment_order_id uuid REFERENCES payment_orders(id) ON DELETE RESTRICT`, `event_type`, nullable unique `dedupe_key`, nullable `provider_status`, sanitized `payload jsonb NOT NULL DEFAULT '{}'`, and `created_at`.

- [ ] **Step 6: TypeORM repository를 최소 구현한다**

Use `Repository.save` for ordinary transitions and a conditional query builder update for `tryBeginFirstCharge`:

```ts
const result = await this.orders.createQueryBuilder()
  .update(PaymentOrderEntity)
  .set({ status: 'payment_pending' })
  .where('id = :id AND status = :status', { id, status: 'billing_active' })
  .execute();
return result.affected === 1;
```

Use `INSERT ... ON CONFLICT (dedupe_key) DO NOTHING` semantics for idempotent events.

- [ ] **Step 7: admin DataSource에 entities와 migration을 등록한다**

Add both payment entities to `entities`, and `CreatePaymentOrders1786300000000` to `migrations`. Do not add cross-database foreign keys.

- [ ] **Step 8: persistence tests를 통과시킨다**

Run:

```bash
npm test -- --runInBand --runTestsByPath src/modules/payments/infrastructure/typeorm-payment-orders.repository.spec.ts src/core/database/admin.datasource.spec.ts
npm run build
```

Expected: all PASS; Nest build succeeds.

- [ ] **Step 9: 커밋 권한이 있을 때만 persistence 커밋을 만든다**

```bash
git add src/modules/payments src/core/database/admin.datasource.ts src/core/database/admin.datasource.spec.ts src/core/database/migrations/admin/1786300000000-CreatePaymentOrders.ts
git commit -m "feat(payments): persist review payment orders"
```

### Task 3: Toss Pay provider port와 HTTP adapter

**Files:**
- Create: `web/clipper_web_api/src/modules/payments/domain/toss-pay.provider.ts`
- Create: `web/clipper_web_api/src/modules/payments/infrastructure/http-toss-pay.provider.ts`
- Test: `web/clipper_web_api/src/modules/payments/infrastructure/http-toss-pay.provider.spec.ts`

**Interfaces:**
- Consumes: `ConfigService.get('TOSS_PAY_API_KEY')`, Node 22 global `fetch`, `AbortSignal.timeout(10000)`.
- Produces: provider-neutral methods `createOneTimePayment`, `createBillingKey`, `getBillingKeyStatus`, `bill`, `getPaymentStatus`.

- [ ] **Step 1: provider contract를 정의한다**

```ts
export interface CreateOneTimePaymentInput {
  orderNo: string;
  amount: number;
  amountTaxFree: number;
  productDesc: string;
  autoExecute: true;
  callbackVersion: 'V2';
  resultCallback: string;
  retUrl: string;
  retCancelUrl: string;
}

export interface CreateBillingKeyInput {
  userId: string;
  productDesc: string;
  resultCallback: string;
  returnSuccessUrl: string;
  returnFailureUrl: string;
}

export interface BillPaymentInput {
  billingKey: string;
  orderNo: string;
  productDesc: string;
  amount: number;
}

export interface TossPaidResult {
  mode: 'TEST' | 'LIVE';
  payToken: string;
  orderNo: string;
  payMethod: string;
  amount: number;
  paidAmount: number;
  transactionId: string;
  paidTs: string;
}

export interface TossPaymentStatus extends TossPaidResult {
  payStatus: string;
}

export class TossPayUncertainResultError extends Error {}

export abstract class TossPayProvider {
  abstract createOneTimePayment(input: CreateOneTimePaymentInput): Promise<{ payToken: string; checkoutPage: string }>;
  abstract createBillingKey(input: CreateBillingKeyInput): Promise<{ billingKey: string; checkoutUri: string }>;
  abstract getBillingKeyStatus(userId: string): Promise<{ userId: string; billingKey: string; status: string; payMethod: string }>;
  abstract bill(input: BillPaymentInput): Promise<TossPaidResult>;
  abstract getPaymentStatus(input: { payToken?: string; orderNo?: string }): Promise<TossPaymentStatus>;
}
```

- [ ] **Step 2: HTTP wire tests를 작성한다**

Mock `global.fetch` and assert exact endpoints/bodies:

```ts
expect(fetch).toHaveBeenCalledWith('https://pay.toss.im/api/v2/payments', expect.objectContaining({ method: 'POST' }));
expect(sentBody).toMatchObject({ apiKey: 'sk_test_public', autoExecute: true, callbackVersion: 'V2' });
expect(sentBody).not.toHaveProperty('priceKrw');
```

Required endpoint cases:

- `/api/v2/payments`
- `/api/v1/billing-key`
- `/api/v1/billing-key/status`
- `/api/v1/billing-key/bill`
- `/api/v2/status`

Also assert:

```ts
expect(AbortSignal.timeout).toHaveBeenCalledWith(10000);
await expect(provider.bill(input)).rejects.toThrow(TossPayUncertainResultError);
expect(error.message).not.toContain('sk_test_public');
expect(error.message).not.toContain('billing-key-secret');
```

- [ ] **Step 3: adapter tests가 실패하는지 확인한다**

Run:

```bash
npm test -- --runInBand --runTestsByPath src/modules/payments/infrastructure/http-toss-pay.provider.spec.ts
```

Expected: FAIL because provider port and adapter do not exist.

- [ ] **Step 4: 공통 POST helper와 오류 타입을 구현한다**

The helper must:

```ts
const response = await fetch(`https://pay.toss.im${path}`, {
  method: 'POST',
  headers: { 'content-type': 'application/json' },
  body: JSON.stringify({ apiKey, ...body }),
  signal: AbortSignal.timeout(10_000),
});
```

- Parse JSON without requiring an exact closed response shape.
- Treat non-2xx, invalid JSON, `code === -1`, timeout, and network errors as provider errors.
- Use an uncertainty-specific error for timeout/network/5xx during `bill` so application code never blindly repeats an approval.
- Keep API Key, billing key, and full provider body out of exception messages.

- [ ] **Step 5: each provider method를 구현한다**

Bill request body must include:

```ts
{
  billingKey,
  orderNo,
  productDesc,
  amount,
  amountTaxFree: 0,
  spreadOut: 0,
  cashReceipt: false,
  cashReceiptTradeOption: 'GENERAL',
  sendFailPush: true,
}
```

Status lookup sends `payToken` or `orderNo`, never both undefined.

- [ ] **Step 6: provider tests와 build를 통과시킨다**

Run:

```bash
npm test -- --runInBand --runTestsByPath src/modules/payments/infrastructure/http-toss-pay.provider.spec.ts
npm run build
```

Expected: PASS; no real network requests.

- [ ] **Step 7: 커밋 권한이 있을 때만 provider 커밋을 만든다**

```bash
git add src/modules/payments/domain/toss-pay.provider.ts src/modules/payments/infrastructure/http-toss-pay.provider.ts src/modules/payments/infrastructure/http-toss-pay.provider.spec.ts
git commit -m "feat(payments): add Toss Pay provider adapter"
```

### Task 4: 비로그인 checkout 생성과 공개 결과 조회

**Files:**
- Create: `web/clipper_web_api/src/modules/payments/application/review-payments.service.ts`
- Test: `web/clipper_web_api/src/modules/payments/application/review-payments.service.spec.ts`

**Interfaces:**
- Consumes: `PlansService.activeById`, `PaymentOrdersRepository`, `TossPayProvider`, `SecretCipher`, `ConfigService`.
- Produces: `startCheckout(input): Promise<{ checkoutUrl: string }>` and `getReviewOrder(receiptToken: string): Promise<ReviewPaymentOrderView>`.

```ts
export interface ReviewPaymentOrderView {
  status: ReviewPaymentStatus;
  paymentType: ReviewPaymentType;
  planName: string;
  months: number;
  amountKrw: number;
  orderNo: string;
  testPayment: boolean;
  errorMessage: string | null;
}
```

- [ ] **Step 1: checkout 실패 테스트를 작성한다**

Create a `setup()` fixture that returns the service plus mocked `plans`, `orders`, `toss`, `cipher`, and mutable config values. Cover these exact assertions:

```ts
it.each([
  ['prod', true],
  ['dev', false],
])('hides review checkout for env=%s reviewMode=%s', async (env, reviewMode) => {
  const { service } = setup({ env, reviewMode });
  await expect(service.startCheckout({ planId: PLAN_ID, paymentType: 'one_time' }))
    .rejects.toBeInstanceOf(NotFoundException);
});

it('derives one-time amount and product description from the active plan', async () => {
  const { service, toss, orders } = setup();
  toss.createOneTimePayment.mockResolvedValue({ payToken: 'pay-token', checkoutPage: 'https://pay.toss.im/checkout' });
  await expect(service.startCheckout({ planId: PLAN_ID, paymentType: 'one_time' }))
    .resolves.toEqual({ checkoutUrl: 'https://pay.toss.im/checkout' });
  expect(toss.createOneTimePayment).toHaveBeenCalledWith(expect.objectContaining({ amount: 19900, productDesc: '1개월' }));
  expect(orders.markCheckoutReady).toHaveBeenCalledWith(expect.any(String), { payToken: 'pay-token' });
});

it('rejects recurring checkout for a 12 month plan', async () => {
  const { service, plans } = setup();
  plans.activeById.mockResolvedValue({ ...activePlan, months: 12 });
  await expect(service.startCheckout({ planId: PLAN_ID, paymentType: 'recurring' }))
    .rejects.toBeInstanceOf(BadRequestException);
});

it('encrypts a new billing key and returns only checkoutUri', async () => {
  const { service, toss, cipher, orders } = setup();
  toss.createBillingKey.mockResolvedValue({ billingKey: 'plain-billing-key', checkoutUri: 'https://pay.toss.im/billing' });
  cipher.encrypt.mockReturnValue('encrypted-billing-key');
  await expect(service.startCheckout({ planId: PLAN_ID, paymentType: 'recurring' }))
    .resolves.toEqual({ checkoutUrl: 'https://pay.toss.im/billing' });
  expect(orders.markCheckoutReady).toHaveBeenCalledWith(expect.any(String), { billingKeyEnc: 'encrypted-billing-key' });
});

it('stores a SHA-256 receipt hash and exposes no secret fields in the public view', async () => {
  const { service, orders } = setup();
  const result = await service.getReviewOrder('receipt-token');
  expect(orders.findByReceiptTokenHash).toHaveBeenCalledWith(
    createHash('sha256').update('receipt-token').digest('hex'),
  );
  expect(result).toEqual({
    status: 'checkout_ready', paymentType: 'one_time', planName: '1개월', months: 1,
    amountKrw: 19900, orderNo: expect.stringMatching(/^clipper-review-[A-Za-z0-9_-]{20}$/),
    testPayment: true, errorMessage: null,
  });
  expect(result).not.toHaveProperty('billingKeyEnc');
  expect(result).not.toHaveProperty('payToken');
  expect(result).not.toHaveProperty('id');
});
```

Add a provider-failure case asserting `markFailed` receives a fixed sanitized error code/message, and assert generated recurring `reviewUserId` plus every `orderNo` matches `^clipper-review-[A-Za-z0-9_-]{20}$`.

- [ ] **Step 2: service tests가 실패하는지 확인한다**

Run:

```bash
npm test -- --runInBand --runTestsByPath src/modules/payments/application/review-payments.service.spec.ts
```

Expected: FAIL because `ReviewPaymentsService` does not exist.

- [ ] **Step 3: identifier와 URL helpers를 최소 구현한다**

```ts
const randomId = randomBytes(15).toString('base64url'); // 120 bits, 20 chars
const orderNo = `clipper-review-${randomId}`;
const reviewUserId = paymentType === 'recurring' ? `clipper-review-${randomBytes(15).toString('base64url')}` : null;
const receiptToken = randomBytes(32).toString('base64url');
const receiptTokenHash = createHash('sha256').update(receiptToken).digest('hex');
```

Build URLs from:

- `TOSS_PAY_CALLBACK_BASE_URL` for server callbacks.
- existing `WEB_BASE_URL` for `/payment/result?receiptToken=...` and `/payment/cancel?receiptToken=...`.

Reject missing/invalid HTTPS base URLs with `ServiceUnavailableException` before calling Toss Pay.

- [ ] **Step 4: one-time checkout를 구현한다**

Call provider with server-derived data:

```ts
{
  orderNo,
  amount: plan.priceKrw,
  amountTaxFree: 0,
  productDesc: plan.name,
  autoExecute: true,
  callbackVersion: 'V2',
  resultCallback: `${apiBase}/payments/toss/normal/result-callback`,
  retUrl: resultUrl,
  retCancelUrl: cancelUrl,
}
```

Persist the order before the provider call, then persist `payToken` and `checkout_ready` after success.

- [ ] **Step 5: recurring checkout를 구현한다**

Call provider with:

```ts
{
  userId: reviewUserId,
  productDesc: plan.name,
  resultCallback: `${apiBase}/payments/toss/billing/result-callback`,
  returnSuccessUrl: resultUrl,
  returnFailureUrl: cancelUrl,
}
```

Encrypt `billingKey` immediately. Persist only `billingKeyEnc`; return only `checkoutUri`.

- [ ] **Step 6: 공개 결과 조회를 구현한다**

Hash the incoming token, look up by hash, and return exactly:

```ts
{
  status: order.status,
  paymentType: order.paymentType,
  planName: order.planName,
  months: order.months,
  amountKrw: order.amountKrw,
  orderNo: order.orderNo,
  testPayment: order.tossMode !== 'LIVE',
  errorMessage: order.errorMessage,
}
```

- [ ] **Step 7: checkout tests와 build를 통과시킨다**

Run:

```bash
npm test -- --runInBand --runTestsByPath src/modules/payments/application/review-payments.service.spec.ts
npm run build
```

Expected: PASS.

- [ ] **Step 8: 커밋 권한이 있을 때만 checkout service 커밋을 만든다**

```bash
git add src/modules/payments/application/review-payments.service.ts src/modules/payments/application/review-payments.service.spec.ts
git commit -m "feat(payments): create anonymous review checkouts"
```

### Task 5: 단건 callback과 빌링 최초 결제 멱등 처리

**Files:**
- Modify: `web/clipper_web_api/src/modules/payments/application/review-payments.service.ts`
- Modify: `web/clipper_web_api/src/modules/payments/application/review-payments.service.spec.ts`

**Interfaces:**
- Consumes: Task 3 provider status/bill methods and Task 2 atomic repository transitions.
- Produces: `handleNormalResult(callback): Promise<void>` and `handleBillingResult(callback): Promise<void>`.

```ts
export interface NormalPaymentCallback {
  status: string;
  payToken: string;
  orderNo: string;
  payMethod: string;
  amount: number;
  discountedAmount: number;
  paidAmount: number;
  paidTs: string;
  transactionId: string;
}

export interface BillingKeyCallback {
  action: 'ACTIVATED' | 'REMOVED';
  userId: string;
  billingKey: string;
  payMethod?: string;
}

export interface ReviewPaymentCallbackHandler {
  handleNormalResult(callback: NormalPaymentCallback): Promise<void>;
  handleBillingResult(callback: BillingKeyCallback): Promise<void>;
}
```

- [ ] **Step 1: normal callback 실패 테스트를 추가한다**

With `statusFixture` set to `PAY_COMPLETE`, the stored order number, and the stored requested amount, cover:

```ts
it('marks one-time payment paid only after verified PAY_COMPLETE', async () => {
  toss.getPaymentStatus.mockResolvedValue(statusFixture);
  await service.handleNormalResult(normalCallback);
  expect(toss.getPaymentStatus).toHaveBeenCalledWith({ payToken: normalCallback.payToken });
  expect(orders.markPaid).toHaveBeenCalledWith(order.id, {
    mode: 'TEST', payToken: statusFixture.payToken, payMethod: statusFixture.payMethod,
    paidAmountKrw: statusFixture.paidAmount, transactionId: statusFixture.transactionId,
  });
});

it.each([
  [{ ...statusFixture, orderNo: 'different-order' }],
  [{ ...statusFixture, amount: order.amountKrw + 1 }],
  [{ ...statusFixture, payStatus: 'PAY_CANCEL' }],
])('never marks a mismatched or incomplete status paid', async (providerStatus) => {
  toss.getPaymentStatus.mockResolvedValue(providerStatus);
  await expect(service.handleNormalResult(normalCallback)).rejects.toBeInstanceOf(BadGatewayException);
  expect(orders.markPaid).not.toHaveBeenCalled();
});

it('returns idempotently when the order is already paid', async () => {
  orders.findByOrderNo.mockResolvedValue({ ...order, status: 'paid' });
  await expect(service.handleNormalResult(normalCallback)).resolves.toBeUndefined();
  expect(toss.getPaymentStatus).not.toHaveBeenCalled();
  expect(orders.markPaid).not.toHaveBeenCalled();
});
```

Verify requested `amount`, not `paidAmount`, because Toss discounts may reduce `paidAmount`.
Also assert `recordEvent` receives only `paymentOrderId`, event/dedupe/provider status, order number, amount, paid amount, pay method, transaction ID, and mode; its payload must not contain API key, billing key, or the raw callback object.

- [ ] **Step 2: billing callback 실패 테스트를 추가한다**

Cover the atomic first-charge claim and uncertainty branch with these assertions:

```ts
it('verifies ACTIVE billing state and executes the first bill once', async () => {
  toss.getBillingKeyStatus.mockResolvedValue({ userId: order.reviewUserId, billingKey: 'plain-key', status: 'ACTIVE', payMethod: 'CARD' });
  cipher.decrypt.mockReturnValue('plain-key');
  orders.tryBeginFirstCharge.mockResolvedValue(true);
  toss.bill.mockResolvedValue(paidFixture);
  await service.handleBillingResult(activatedCallback);
  expect(orders.markBillingActive).toHaveBeenCalledWith(order.id, 'CARD');
  expect(toss.bill).toHaveBeenCalledTimes(1);
  expect(orders.markPaid).toHaveBeenCalledTimes(1);
});

it('does not bill twice for a duplicate ACTIVATED callback', async () => {
  orders.findByReviewUserId.mockResolvedValue({ ...order, status: 'payment_pending' });
  toss.getPaymentStatus.mockResolvedValue(statusFixture);
  await service.handleBillingResult(activatedCallback);
  expect(toss.bill).not.toHaveBeenCalled();
  expect(orders.markPaid).toHaveBeenCalledTimes(1);
});

it('reconciles an uncertain bill through orderNo status lookup', async () => {
  toss.bill.mockRejectedValue(new TossPayUncertainResultError());
  toss.getPaymentStatus.mockResolvedValue(statusFixture);
  await service.handleBillingResult(activatedCallback);
  expect(toss.getPaymentStatus).toHaveBeenCalledWith({ orderNo: order.orderNo });
  expect(orders.markPaid).toHaveBeenCalledTimes(1);
});

it('keeps payment_pending and returns 503 when an uncertain bill cannot be verified', async () => {
  toss.bill.mockRejectedValue(new TossPayUncertainResultError());
  toss.getPaymentStatus.mockRejectedValue(new Error('status unavailable'));
  await expect(service.handleBillingResult(activatedCallback)).rejects.toBeInstanceOf(ServiceUnavailableException);
  expect(orders.markFailed).not.toHaveBeenCalled();
});

it('records REMOVED without starting a charge', async () => {
  await service.handleBillingResult({ ...activatedCallback, action: 'REMOVED' });
  expect(orders.recordEvent).toHaveBeenCalledWith(expect.objectContaining({ eventType: 'billing_removed' }));
  expect(toss.bill).not.toHaveBeenCalled();
});
```

Add a non-`ACTIVE` provider status case that throws `BadGatewayException`, does not call `tryBeginFirstCharge`, and does not call `bill`.

- [ ] **Step 3: callback tests가 실패하는지 확인한다**

Run:

```bash
npm test -- --runInBand --runTestsByPath src/modules/payments/application/review-payments.service.spec.ts
```

Expected: FAIL because callback methods do not exist.

- [ ] **Step 4: normal result 검증을 구현한다**

Algorithm:

```ts
const order = await orders.findByOrderNo(callback.orderNo);
if (!order) throw new NotFoundException('payment order not found');
if (order.status === 'paid') return;
const status = await toss.getPaymentStatus({ payToken: callback.payToken });
if (status.payStatus !== 'PAY_COMPLETE' || status.orderNo !== order.orderNo || status.amount !== order.amountKrw) {
  throw new BadGatewayException('payment verification failed');
}
await orders.markPaid(order.id, {
  mode: status.mode,
  payToken: status.payToken,
  payMethod: status.payMethod,
  paidAmountKrw: status.paidAmount,
  transactionId: status.transactionId,
});
await orders.recordEvent({
  paymentOrderId: order.id,
  eventType: 'normal_paid',
  dedupeKey: `normal-paid:${status.transactionId}`,
  providerStatus: status.payStatus,
  payload: {
    orderNo: status.orderNo,
    amount: status.amount,
    paidAmount: status.paidAmount,
    payMethod: status.payMethod,
    transactionId: status.transactionId,
    mode: status.mode,
  },
});
```

Derive `transactionId` from the PAY transaction when the status response provides a transaction list.

- [ ] **Step 5: billing activation과 최초 결제를 구현한다**

Algorithm:

```ts
const order = await orders.findByReviewUserId(callback.userId);
if (!order || order.paymentType !== 'recurring') throw new NotFoundException('payment order not found');
if (callback.action === 'REMOVED') {
  await orders.recordEvent({
    paymentOrderId: order.id,
    eventType: 'billing_removed',
    dedupeKey: `billing-removed:${callback.userId}`,
    providerStatus: 'REMOVED',
    payload: { userId: callback.userId },
  });
  return;
}
if (order.status === 'paid') return;
if (order.status === 'payment_pending') {
  await reconcilePendingFirstCharge(order);
  return;
}
const billing = await toss.getBillingKeyStatus(callback.userId);
if (!order.billingKeyEnc || billing.status !== 'ACTIVE' || billing.billingKey !== secretCipher.decrypt(order.billingKeyEnc)) {
  throw new BadGatewayException('billing key verification failed');
}
await orders.markBillingActive(order.id, billing.payMethod);
if (!await orders.tryBeginFirstCharge(order.id)) {
  const current = await orders.findByOrderNo(order.orderNo);
  if (current?.status === 'paid') return;
  if (current?.status === 'payment_pending') await reconcilePendingFirstCharge(current);
  return;
}
try {
  const paid = await toss.bill({
    billingKey: billing.billingKey,
    orderNo: order.orderNo,
    productDesc: order.planName,
    amount: order.amountKrw,
  });
  await orders.markPaid(order.id, {
    mode: paid.mode,
    payToken: paid.payToken,
    payMethod: paid.payMethod,
    paidAmountKrw: paid.paidAmount,
    transactionId: paid.transactionId,
  });
} catch (error) {
  if (error instanceof TossPayUncertainResultError) {
    await reconcilePendingFirstCharge(order);
    return;
  }
  throw error;
}
```

Implement the reconciliation helper with an exact order/amount check:

```ts
private async reconcilePendingFirstCharge(order: PaymentOrder): Promise<void> {
  try {
    const status = await this.toss.getPaymentStatus({ orderNo: order.orderNo });
    if (status.payStatus !== 'PAY_COMPLETE' || status.orderNo !== order.orderNo || status.amount !== order.amountKrw) {
      throw new ServiceUnavailableException('payment result is pending');
    }
    await this.orders.markPaid(order.id, {
      mode: status.mode,
      payToken: status.payToken,
      payMethod: status.payMethod,
      paidAmountKrw: status.paidAmount,
      transactionId: status.transactionId,
    });
  } catch (error) {
    if (error instanceof ServiceUnavailableException) throw error;
    throw new ServiceUnavailableException('payment result is pending');
  }
}
```

On `TossPayUncertainResultError`, call this helper. It marks paid only on verified `PAY_COMPLETE`; otherwise it keeps `payment_pending` and throws `ServiceUnavailableException` so Toss can retry the callback.

- [ ] **Step 6: callback tests와 full payment service tests를 통과시킨다**

Run:

```bash
npm test -- --runInBand --runTestsByPath src/modules/payments/application/review-payments.service.spec.ts
```

Expected: PASS; fake provider `bill` called exactly once across duplicate callbacks.

- [ ] **Step 7: 커밋 권한이 있을 때만 callback 커밋을 만든다**

```bash
git add src/modules/payments/application/review-payments.service.ts src/modules/payments/application/review-payments.service.spec.ts
git commit -m "feat(payments): verify Toss Pay callbacks idempotently"
```

### Task 6: DTO·rate limit·controller·module 배선

**Files:**
- Create: `web/clipper_web_api/src/modules/payments/presentation/dto/create-review-checkout.dto.ts`
- Create: `web/clipper_web_api/src/modules/payments/presentation/dto/normal-result-callback.dto.ts`
- Create: `web/clipper_web_api/src/modules/payments/presentation/dto/billing-result-callback.dto.ts`
- Create: `web/clipper_web_api/src/modules/payments/presentation/review-payment-rate-limiter.ts`
- Test: `web/clipper_web_api/src/modules/payments/presentation/review-payment-rate-limiter.spec.ts`
- Create: `web/clipper_web_api/src/modules/payments/presentation/review-payments.controller.ts`
- Test: `web/clipper_web_api/src/modules/payments/presentation/review-payments.controller.spec.ts`
- Create: `web/clipper_web_api/src/modules/payments/presentation/toss-pay-callback.controller.ts`
- Test: `web/clipper_web_api/src/modules/payments/presentation/toss-pay-callback.controller.spec.ts`
- Create: `web/clipper_web_api/src/modules/payments/payments.module.ts`
- Modify: `web/clipper_web_api/src/app.module.ts`
- Modify: `web/clipper_web_api/.env.example`

**Interfaces:**
- Consumes: Task 4/5 service methods.
- Produces: four OpenAPI-matching HTTP endpoints and app startup configuration.

- [ ] **Step 1: DTO validation tests를 controller spec에 작성한다**

DTOs:

```ts
export class CreateReviewCheckoutDto {
  @IsUUID() planId!: string;
  @IsIn(['one_time', 'recurring']) paymentType!: ReviewPaymentType;
}

export class NormalResultCallbackDto {
  @IsString() status!: string;
  @IsString() payToken!: string;
  @IsString() orderNo!: string;
  @IsString() payMethod!: string;
  @IsInt() amount!: number;
  @IsInt() discountedAmount!: number;
  @IsInt() paidAmount!: number;
  @IsString() paidTs!: string;
  @IsString() transactionId!: string;
}

export class BillingResultCallbackDto {
  @IsIn(['ACTIVATED', 'REMOVED']) action!: 'ACTIVATED' | 'REMOVED';
  @IsString() userId!: string;
  @IsString() billingKey!: string;
  @IsOptional() @IsString() payMethod?: string;
}
```

Extra Toss fields must be tolerated by the global whitelist behavior.

- [ ] **Step 2: rate limiter 실패 테스트를 작성한다**

```ts
for (let i = 0; i < 10; i += 1) limiter.assertAllowed('checkout:127.0.0.1', 10, 600_000, now);
expect(() => limiter.assertAllowed('checkout:127.0.0.1', 10, 600_000, now)).toThrow(TooManyRequestsException);
```

Add expiry cleanup test and separate `result:` bucket test with `60` requests per `60_000ms`. The limiter is explicitly process-local because dev deploy uses one API container; document that it must be replaced before multi-instance production use.

- [ ] **Step 3: controller delegation 실패 테스트를 작성한다**

Assert:

- checkout consumes the 10/10-minute bucket and calls `startCheckout`.
- result consumes the 60/minute bucket and calls `getReviewOrder`.
- normal callback calls `handleNormalResult` without browser auth.
- billing callback calls `handleBillingResult` without browser auth.
- callback controllers do not apply the review checkout limiter.

- [ ] **Step 4: presentation tests가 실패하는지 확인한다**

Run:

```bash
npm test -- --runInBand --runTestsByPath src/modules/payments/presentation/review-payment-rate-limiter.spec.ts src/modules/payments/presentation/review-payments.controller.spec.ts src/modules/payments/presentation/toss-pay-callback.controller.spec.ts
```

Expected: FAIL because DTOs/controllers/limiter do not exist.

- [ ] **Step 5: limiter와 controllers를 구현한다**

Routes:

```ts
@Controller('payments/review')
// POST checkout, GET orders/:receiptToken

@Controller('payments/toss')
// POST normal/result-callback, POST billing/result-callback
```

Use `@Ip()` for the current request IP and separate rate-limit bucket prefixes. Return raw service results.

- [ ] **Step 6: `PaymentsModule`을 조립한다**

Imports:

- `TypeOrmModule.forFeature([PaymentOrderEntity, PaymentEventEntity], 'admin')`
- `BillingModule`

Providers:

- `ReviewPaymentsService`
- `ReviewPaymentRateLimiter`
- `{ provide: PaymentOrdersRepository, useClass: TypeOrmPaymentOrdersRepository }`
- `{ provide: TossPayProvider, useClass: HttpTossPayProvider }`
- `SecretCipher` factory from `API_KEY_ENC_SECRET`

Controllers:

- `ReviewPaymentsController`
- `TossPayCallbackController`

Import `PaymentsModule` from `AppModule`.

- [ ] **Step 7: env example을 추가한다**

```dotenv
# Toss Pay review checkout — server-side only.
TOSS_PAY_API_KEY=
TOSS_PAY_REVIEW_MODE=false
TOSS_PAY_CALLBACK_BASE_URL=http://localhost:3000
```

Do not place the API Key in Angular environment files.

- [ ] **Step 8: presentation tests, full payments tests, build를 통과시킨다**

Run:

```bash
npm test -- --runInBand --runTestsByPath src/modules/payments/presentation/review-payment-rate-limiter.spec.ts src/modules/payments/presentation/review-payments.controller.spec.ts src/modules/payments/presentation/toss-pay-callback.controller.spec.ts
npm test -- --runInBand
npm run build
```

Expected: PASS; AppModule compiles with PaymentsModule.

- [ ] **Step 9: 커밋 권한이 있을 때만 HTTP wiring 커밋을 만든다**

```bash
git add .env.example src/app.module.ts src/modules/payments
git commit -m "feat(payments): expose review checkout endpoints"
```

### Task 7: Angular 결제 API와 요금 페이지 버튼

**Files:**
- Modify: `web/clipper_web_client/src/app/core/api/models.ts`
- Create: `web/clipper_web_client/src/app/core/api/payments-api.service.ts`
- Test: `web/clipper_web_client/src/app/core/api/payments-api.service.spec.ts`
- Create: `web/clipper_web_client/src/app/core/navigation/browser-navigation.service.ts`
- Modify: `web/clipper_web_client/src/app/features/public/pricing/pricing.component.ts`
- Modify: `web/clipper_web_client/src/app/features/public/pricing/pricing.component.html`
- Modify: `web/clipper_web_client/src/app/features/public/pricing/pricing.component.scss`
- Modify: `web/clipper_web_client/src/app/features/public/pricing/pricing.component.spec.ts`

**Interfaces:**
- Consumes: `POST /payments/review/checkout` and existing `Plan` model.
- Produces: `PaymentsApiService.startCheckout`, `BrowserNavigationService.assign`, and period-specific CTA behavior.

- [ ] **Step 1: API service 실패 테스트를 작성한다**

```ts
api.startCheckout({ planId: '00000000-0000-4000-8000-000000000001', paymentType: 'one_time' }).subscribe();
const req = http.expectOne(`${environment.apiBaseUrl}/payments/review/checkout`);
expect(req.request.method).toBe('POST');
expect(req.request.body).toEqual({ planId: '00000000-0000-4000-8000-000000000001', paymentType: 'one_time' });
```

Add `getReviewOrder(receiptToken)` GET coverage for Task 8.

- [ ] **Step 2: pricing 실패 테스트를 작성한다**

Use 1, 3, and 12 month plans and assert:

```ts
expect(buttonLabels(oneMonth)).toEqual(['정기결제', '단건결제']);
expect(buttonLabels(threeMonth)).toEqual(['정기결제', '단건결제']);
expect(buttonLabels(twelveMonth)).toEqual(['단건결제']);
```

Click a one-time button and assert:

```ts
expect(payments.startCheckout).toHaveBeenCalledWith({ planId: oneMonth.id, paymentType: 'one_time' });
expect(navigation.assign).toHaveBeenCalledWith('https://pay.toss.im/checkout');
```

Also assert double-click suppression, button disabled loading state, safe error message, and removal of `구매 요청 후 운영자 확인`/`입금 확인 후 발급` copy.

- [ ] **Step 3: Angular tests가 실패하는지 확인한다**

Run:

```bash
npm test -- --watch=false --browsers=ChromeHeadless --include='**/payments-api.service.spec.ts' --include='**/pricing.component.spec.ts'
```

Expected: FAIL because the payment service/navigation wrapper and CTAs do not exist.

- [ ] **Step 4: API models와 service를 구현한다**

```ts
export type ReviewPaymentType = 'one_time' | 'recurring';
export type ReviewPaymentStatus = 'created' | 'checkout_ready' | 'billing_active' | 'payment_pending' | 'paid' | 'canceled' | 'failed';
export interface CreateReviewCheckout { planId: string; paymentType: ReviewPaymentType; }
export interface ReviewCheckoutResponse { checkoutUrl: string; }
export interface ReviewPaymentOrder { status: ReviewPaymentStatus; paymentType: ReviewPaymentType; planName: string; months: number; amountKrw: number; orderNo: string; testPayment: boolean; errorMessage: string | null; }
```

`PaymentsApiService` calls only `environment.apiBaseUrl`; it does not add credentials or API Keys.

- [ ] **Step 5: navigation wrapper와 pricing component를 구현한다**

```ts
@Injectable({ providedIn: 'root' })
export class BrowserNavigationService {
  assign(url: string): void { window.location.assign(url); }
}
```

Pricing component state:

```ts
pendingCheckout = signal<string | null>(null);
checkoutError = signal<string | null>(null);
startCheckout(plan: Plan, paymentType: ReviewPaymentType): void {
  const requestKey = `${plan.id}:${paymentType}`;
  if (this.pendingCheckout() !== null) return;
  this.pendingCheckout.set(requestKey);
  this.checkoutError.set(null);
  this.paymentsApi.startCheckout({ planId: plan.id, paymentType }).subscribe({
    next: ({ checkoutUrl }) => this.navigation.assign(checkoutUrl),
    error: () => {
      this.pendingCheckout.set(null);
      this.checkoutError.set('결제창을 열지 못했습니다. 잠시 후 다시 시도해 주세요.');
    },
  });
}
```

Replace router links with real `<button type="button">` elements. Use a `.plan-actions` wrapper and existing pricing styles; do not refactor unrelated color tokens in this task.

Copy:

- subtitle: `원하는 플랜과 결제 방식을 선택하세요.`
- note: `심사 기간에는 토스페이 테스트 결제로 진행되며 실제 출금되지 않습니다.`

- [ ] **Step 6: targeted tests와 build를 통과시킨다**

Run:

```bash
npm test -- --watch=false --browsers=ChromeHeadless --include='**/payments-api.service.spec.ts' --include='**/pricing.component.spec.ts'
npm run build
```

Expected: PASS; production Angular build succeeds.

- [ ] **Step 7: 커밋 권한이 있을 때만 pricing UI 커밋을 만든다**

```bash
git add src/app/core/api src/app/core/navigation src/app/features/public/pricing
git commit -m "feat(payments): add review checkout buttons"
```

### Task 8: 공개 결제 결과·취소 페이지와 제한 폴링

**Files:**
- Create: `web/clipper_web_client/src/app/features/public/payment-result/payment-result.component.ts`
- Create: `web/clipper_web_client/src/app/features/public/payment-result/payment-result.component.html`
- Create: `web/clipper_web_client/src/app/features/public/payment-result/payment-result.component.scss`
- Create: `web/clipper_web_client/src/app/features/public/payment-result/payment-result.component.spec.ts`
- Modify: `web/clipper_web_client/src/app/features/public/public.routes.ts`

**Interfaces:**
- Consumes: `PaymentsApiService.getReviewOrder(receiptToken)`.
- Produces: public routes `/payment/result` and `/payment/cancel`.

- [ ] **Step 1: component 실패 테스트를 작성한다**

Create a fixture with mutable query params, route data, and a mocked `PaymentsApiService`. Cover these exact assertions:

```ts
it('shows an error and skips the API when receiptToken is missing', () => {
  const fixture = setup({ receiptToken: null });
  fixture.detectChanges();
  expect(paymentsApi.getReviewOrder).not.toHaveBeenCalled();
  expect(fixture.nativeElement.textContent).toContain('결제 확인 정보가 없습니다');
});

it('shows paid test details without entitlement copy', () => {
  paymentsApi.getReviewOrder.and.returnValue(of(paidOrder));
  const fixture = setup({ receiptToken: 'receipt-token' });
  fixture.detectChanges();
  const rendered = fixture.nativeElement.textContent;
  expect(rendered).toContain('테스트 결제 완료');
  expect(rendered).toContain(paidOrder.planName);
  expect(rendered).toContain(paidOrder.orderNo);
  expect(rendered).not.toContain('크레딧 지급');
  expect(rendered).not.toContain('이용권 발급');
});

it('polls every two seconds and stops on paid', fakeAsync(() => {
  paymentsApi.getReviewOrder.and.returnValues(
    of({ ...paidOrder, status: 'payment_pending' }),
    of(paidOrder),
  );
  const fixture = setup({ receiptToken: 'receipt-token' });
  fixture.detectChanges();
  expect(paymentsApi.getReviewOrder).toHaveBeenCalledTimes(1);
  tick(2_000);
  expect(paymentsApi.getReviewOrder).toHaveBeenCalledTimes(2);
  tick(20_000);
  expect(paymentsApi.getReviewOrder).toHaveBeenCalledTimes(2);
}));

it('stops after ten requests and shows refresh guidance', fakeAsync(() => {
  paymentsApi.getReviewOrder.and.returnValue(of({ ...paidOrder, status: 'payment_pending' }));
  const fixture = setup({ receiptToken: 'receipt-token' });
  fixture.detectChanges();
  tick(18_000);
  fixture.detectChanges();
  expect(paymentsApi.getReviewOrder).toHaveBeenCalledTimes(10);
  expect(fixture.nativeElement.textContent).toContain('새로고침');
}));

it('lets a verified paid state win on the cancel route', () => {
  paymentsApi.getReviewOrder.and.returnValue(of(paidOrder));
  const fixture = setup({ receiptToken: 'receipt-token', canceledRoute: true });
  fixture.detectChanges();
  expect(fixture.nativeElement.textContent).toContain('테스트 결제 완료');
  expect(fixture.nativeElement.textContent).not.toContain('결제가 취소되었습니다');
});

it('cancels scheduled polling on destroy', fakeAsync(() => {
  paymentsApi.getReviewOrder.and.returnValue(of({ ...paidOrder, status: 'payment_pending' }));
  const fixture = setup({ receiptToken: 'receipt-token' });
  fixture.detectChanges();
  fixture.destroy();
  tick(20_000);
  expect(paymentsApi.getReviewOrder).toHaveBeenCalledTimes(1);
}));
```

- [ ] **Step 2: component test가 실패하는지 확인한다**

Run:

```bash
npm test -- --watch=false --browsers=ChromeHeadless --include='**/payment-result.component.spec.ts'
```

Expected: FAIL because the component does not exist.

- [ ] **Step 3: routes와 component state를 구현한다**

Routes:

```ts
{ path: 'payment/result', loadComponent: () => import('./payment-result/payment-result.component').then(m => m.PaymentResultComponent) },
{ path: 'payment/cancel', loadComponent: () => import('./payment-result/payment-result.component').then(m => m.PaymentResultComponent), data: { canceled: true } },
```

Component constants:

```ts
const POLL_INTERVAL_MS = 2_000;
const MAX_POLL_ATTEMPTS = 10;
const TERMINAL = new Set<ReviewPaymentStatus>(['paid', 'canceled', 'failed']);
```

Use `signal` state and either bounded RxJS `timer/take` or an explicitly cleared timeout. Never exceed ten API calls for one component lifecycle.

- [ ] **Step 4: template와 styles를 구현한다**

States:

- missing/invalid receipt token
- loading / `결제 확인 중`
- `테스트 결제 완료`
- cancel guidance
- failure with sanitized message
- polling expired with `새로고침` button

Paid summary contains plan, duration, type, amount, order number, and `테스트 결제` badge. It must not say credits or license were issued.

- [ ] **Step 5: component tests와 production build를 통과시킨다**

Run:

```bash
npm test -- --watch=false --browsers=ChromeHeadless --include='**/payment-result.component.spec.ts' --include='**/payments-api.service.spec.ts'
npm run build
```

Expected: PASS.

- [ ] **Step 6: 커밋 권한이 있을 때만 result UI 커밋을 만든다**

```bash
git add src/app/features/public/payment-result src/app/features/public/public.routes.ts src/app/core/api
git commit -m "feat(payments): show public test payment results"
```

### Task 9: dev/stage/prod 환경변수 전달

**Files:**
- Modify: `web/clipper_infra/apps/compose.yml`
- Modify: `web/clipper_infra/env/stack.dev.env.example`
- Modify: `web/clipper_infra/env/stack.stage.env.example`
- Modify: `web/clipper_infra/env/stack.prod.env.example`

**Interfaces:**
- Consumes: API env keys defined in Tasks 4/6.
- Produces: container env wiring without putting Toss Pay keys in images or Angular builds.

- [ ] **Step 1: compose env 누락을 재현한다**

Run:

```bash
rg -n "TOSS_PAY_API_KEY|TOSS_PAY_REVIEW_MODE|TOSS_PAY_CALLBACK_BASE_URL" apps/compose.yml env/stack.*.env.example
```

Expected: no matches before implementation.

- [ ] **Step 2: API service env passthrough를 추가한다**

```yaml
TOSS_PAY_API_KEY: "${TOSS_PAY_API_KEY:-}"
TOSS_PAY_REVIEW_MODE: "${TOSS_PAY_REVIEW_MODE:-false}"
TOSS_PAY_CALLBACK_BASE_URL: "${TOSS_PAY_CALLBACK_BASE_URL:-}"
```

Only the `api` service receives these values.

- [ ] **Step 3: environment examples를 추가한다**

Dev:

```dotenv
TOSS_PAY_API_KEY=CHANGE_ME_OFFICIAL_SHARED_TEST_KEY
TOSS_PAY_REVIEW_MODE=true
TOSS_PAY_CALLBACK_BASE_URL=https://dev-api.clipperstudio.ai
```

Stage:

```dotenv
TOSS_PAY_API_KEY=CHANGE_ME
TOSS_PAY_REVIEW_MODE=false
TOSS_PAY_CALLBACK_BASE_URL=https://stage-api.clipperstudio.ai
```

Prod:

```dotenv
TOSS_PAY_API_KEY=CHANGE_ME
TOSS_PAY_REVIEW_MODE=false
TOSS_PAY_CALLBACK_BASE_URL=https://api.clipperstudio.ai
```

Never add `env/stack.dev.env`; it is ignored and belongs only on the deployment host.

- [ ] **Step 4: compose expansion을 검증한다**

Run:

```bash
docker compose --env-file env/stack.dev.env.example -f apps/compose.yml -f apps/compose.dev.yml config >/tmp/clipper-toss-pay-compose.yml
rg -n "TOSS_PAY_API_KEY|TOSS_PAY_REVIEW_MODE|TOSS_PAY_CALLBACK_BASE_URL" /tmp/clipper-toss-pay-compose.yml
```

Expected: the three variables appear under `api`, not under `web-client`.

- [ ] **Step 5: 커밋 권한이 있을 때만 infra 커밋을 만든다**

```bash
git add apps/compose.yml env/stack.dev.env.example env/stack.stage.env.example env/stack.prod.env.example
git commit -m "chore(payments): pass Toss Pay review env"
```

### Task 10: 전체 검증, migration 적용, dev 배포와 스모크 테스트

**Files:**
- Modify: `/Users/jina/project/adlight/.codex/implementation/TASKS.md`
- Modify: `/Users/jina/project/adlight/.codex/implementation/WORKLOG.md`
- Runtime-only ignored file on deploy host: `web/clipper_infra/env/stack.dev.env`

**Interfaces:**
- Consumes: Tasks 1–9 complete and green.
- Produces: verified dev deployment and an evidence-backed handoff to the Toss Pay reviewer.

- [ ] **Step 1: 모든 worktree가 올바른 branch이고 예상 변경만 있는지 확인한다**

Run:

```bash
git -C /Users/jina/project/adlight/web/clipper_web_api status --short --branch
git -C /Users/jina/project/adlight/web/clipper_web_client status --short --branch
git -C /Users/jina/project/adlight/web/clipper_infra status --short --branch
git -C /Users/jina/project/adlight/.codex status --short --branch
```

Expected: all on `feat/toss-pay-review-checkout`; no unrelated changes.

- [ ] **Step 2: API fresh verification을 실행한다**

Run:

```bash
npm test -- --runInBand
npm run build
```

Working directory: `web/clipper_web_api`.

Expected: all Jest tests PASS; Nest build exit 0.

- [ ] **Step 3: client fresh verification을 실행한다**

Run:

```bash
npm test -- --watch=false --browsers=ChromeHeadless
npm run build
```

Working directory: `web/clipper_web_client`.

Expected: all Karma tests PASS; production build exit 0.

- [ ] **Step 4: migration을 dev DB에 적용하기 전에 SQL과 대상 DB를 확인한다**

Run on the deployment host. Use the Compose one-off API container commands in
`../implementation/TOSS_PAY_DEV_DEPLOYMENT_HANDOFF.md` so this check receives
the same DB environment as the deployed API. Do not assume that running the
host repository's `npm run db:migrate:admin` automatically reads
`clipper_infra/env/stack.dev.env`.

```bash
npm run build
sed -n '1,260p' src/core/database/migrations/admin/1786300000000-CreatePaymentOrders.ts
node --input-type=module -e "const m=await import('./dist/core/database/admin.datasource.js'); const ds=m.default?.default??m.default; await ds.initialize(); const [{database_name}]=await ds.query('SELECT current_database() AS database_name'); console.log(database_name); await ds.destroy();"
```

Expected: migration SQL contains only the planned payment tables/indexes; the read-only query prints exactly `clipper_admin_dev`. The repository migration wrapper has no dry-run mode, so do not run `npm run db:migrate:admin` until both checks pass.

- [ ] **Step 5: deployment host의 ignored dev env에 공용 테스트 키를 설정한다**

```dotenv
TOSS_PAY_API_KEY=<official shared test key>
TOSS_PAY_REVIEW_MODE=true
TOSS_PAY_CALLBACK_BASE_URL=https://dev-api.clipperstudio.ai
```

Confirm `WEB_BASE_URL=https://dev.clipperstudio.ai` and valid `API_KEY_ENC_SECRET` already exist. Do not print the full env file.

- [ ] **Step 6: commit/push/deploy authority checkpoint를 지킨다**

The normal deploy script pulls Git state. Before deployment, obtain explicit user authorization for any still-unapproved commits and pushes. Use Conventional Commits from Tasks 1–9; never push unrelated changes.

- [ ] **Step 7: admin migration과 dev services를 배포한다**

On the dev host after approved branch commits are available, follow
`../implementation/TOSS_PAY_DEV_DEPLOYMENT_HANDOFF.md`. Build the new API
image, verify that its admin DataSource resolves to `clipper_admin_dev`, run the
pending migration through a Compose one-off API container, then recreate the
API and web client. No m2-proxy change or DB-container restart is required.

Expected: compose config passes; API and web client containers are recreated and healthy.

- [ ] **Step 8: read-only health와 public page를 확인한다**

Run:

```bash
curl -s https://dev-api.clipperstudio.ai/health
curl -s -I https://dev.clipperstudio.ai/pricing
```

Expected: API health success; pricing HTTP 200.

- [ ] **Step 9: 공용 테스트 키 수동 스모크 시나리오를 실행한다**

Checklist:

1. 로그아웃/시크릿 창에서 1개월 단건결제 버튼이 Toss Pay 결제창을 연다.
2. 테스트 결제를 완료하면 결과 페이지가 20초 이내 `테스트 결제 완료`를 표시한다.
3. 1개월 정기결제가 빌링 등록창을 열고 `ACTIVE` 후 최초 결제가 한 번만 기록된다.
4. 3개월 카드에 정기/단건 두 버튼이 보인다.
5. 12개월 카드에는 단건만 보인다.
6. 12개월 recurring API 직접 요청은 400이다.
7. callback 재전송에도 `payment_events`와 최초 bill이 중복되지 않는다.
8. `purchase_requests`, `licenses`, credit ledger row count가 스모크 전후 동일하다.
9. DB와 로그에 평문 `billingKey`와 API Key가 없다.

- [ ] **Step 10: worklog와 담당자 전달문을 기록한다**

`WORKLOG.md`에 실제 변경 파일, 테스트 명령 결과, migration 결과, dev URL 확인, 남은 위험을 기록한다. Toss Pay 담당자 전달문에는 다음만 포함한다.

```text
비로그인 상태에서 정기결제창과 단건결제창이 열리도록 수정했습니다.
1년 상품은 단건결제로만 연결했고, 공용 테스트 키로 결제 결과 저장까지 확인했습니다.
이번 단계에서는 이용권·크레딧 자동 지급과 반복 청구는 연결하지 않았습니다.
다음 심사 단계에서 추가로 필요한 자동 지급, 해지, 환불 범위를 안내 부탁드립니다.
```

- [ ] **Step 11: 최종 diff와 검증 증거를 확인한다**

Run:

```bash
git -C /Users/jina/project/adlight/web/clipper_web_api diff --check
git -C /Users/jina/project/adlight/web/clipper_web_client diff --check
git -C /Users/jina/project/adlight/web/clipper_infra diff --check
git -C /Users/jina/project/adlight/.codex diff --check
```

Expected: no whitespace errors; no files outside the approved scope.
