# Subscription Payment Method Management Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 로그인 사용자가 Clipper 마이페이지에서 현재 토스페이 자동결제 수단을 안전하게 확인하고, 기존 빌링키를 잃지 않으면서 새 결제수단으로 교체하며, `past_due`이면 고지한 미결제 갱신금액을 교체 직후 한 번 재시도할 수 있게 한다.

**Architecture:** API 계약을 먼저 고정하고, `subscriptions`에는 현재 결제수단의 안전한 표시 스냅샷만 추가하며, 변경 작업은 `subscription_payment_method_changes`로 별도 영속화한다. `SubscriptionPaymentMethodsService`가 조회·변경 시작·후보 검증·원자적 교체·만료·이전 키 정리를 전담하고, 기존 `SubscriptionRenewalService`는 새 승인 claim 직전에 진행 중 변경 여부만 확인한다. 웹 클라이언트는 대시보드 결제수단 카드, 금액 고지 확인창, 인증 복귀 결과 화면을 제공한다.

**Tech Stack:** Node.js 22, NestJS, TypeScript, TypeORM raw SQL repositories, PostgreSQL, Jest, OpenAPI 3.1, Angular 19 standalone components, Angular Material, Jasmine/Karma.

## Global Constraints

- 구현 대상은 `clipper_web_api`와 `clipper_web_client`뿐이다. `clipper_angular`, `clipper_electron`, `clipper_web_admin`, `clipper_infra`의 프레임워크 버전이나 코드는 변경하지 않는다.
- API와 웹 클라이언트는 각 레포의 `.nvmrc`에 맞춰 Node.js 22를 사용한다. 웹 클라이언트의 Angular 19를 업그레이드하지 않는다.
- 코드는 두 레포의 기존 `feat/access-credit-system-replacement` 기능 브랜치에서만 변경한다. `dev`에 직접 커밋하지 않는다.
- 문서 변경은 `.codex` 레포의 `main` 브랜치에만 기록한다.
- API 정본은 `clipper_web_api/docs/api/openapi.yaml`이다. 구현보다 계약을 먼저 변경한다.
- 토스 API Key, 평문 빌링키, 전체 카드번호, 카드 BIN, 계좌번호를 DB·로그·이벤트 payload·HTTP 응답에 남기지 않는다.
- 사용자에게 노출·저장할 결제수단 정보는 결제수단, 카드사명, 카드번호 끝 4자리, 카드 종류, 토스머니 연결 은행명, 공급자 상태, 마지막 확인 시각뿐이다.
- 결제수단 변경 유효시간은 생성 시각부터 정확히 30분이다. 사용자별 30분 polling은 하지 않는다.
- 결과 화면 polling은 2초 간격, 최대 15회인 30초로 제한한다.
- `active` 변경은 즉시 결제하지 않는다. `past_due` 변경은 사용자가 상품명·금액·즉시 재결제를 확인한 경우에만 교체 직후 기존 갱신 주문을 한 번 수동 재시도한다.
- `pending`, `cancel_at_period_end`, `stopped`, `canceled`, `ended` 구독에서는 변경을 시작하지 않는다.
- 후보 키가 `ACTIVE`로 검증되고 DB 교체가 커밋되기 전까지 기존 빌링키를 유지한다.
- 진행 중 변경은 아직 시작하지 않은 새 자동·수동 승인 claim만 막는다. 이미 `payment_pending` 또는 `paid`인 주문의 상태 확인과 fulfillment 복구는 막지 않는다.
- 직접 재시도 실패는 기존 D+1·D+2 자동 재시도 순번을 소모하지 않는다.
- 이메일·SMS·알림톡, 토스 오류코드별 사용자 메시지 전면 개편, 복수 결제수단 보관, 예비 결제수단, 관리자 대리 변경은 이번 범위에서 제외한다.
- 기존 `결제 다시 시도` 버튼과 `POST /subscriptions/current/retry`는 유지한다. 이 동작은 현재 빌링키로만 청구하며 토스 카드 선택 화면을 열지 않는다.
- 새 스타일은 기존 CSS 변수와 컴포넌트 패턴을 사용하며 임의의 raw hex 색상을 추가하지 않는다.

---

## File Map

### `clipper_web_api`

- `docs/api/openapi.yaml`: 결제수단 조회·변경·결과 API와 안전한 callback 필드를 정의한다.
- `src/core/database/migrations/admin/1787200000000-CreateSubscriptionPaymentMethodChanges.ts`: 구독 표시 스냅샷 컬럼과 변경 요청 테이블을 생성한다.
- `src/core/database/migrations/admin/1787200000000-CreateSubscriptionPaymentMethodChanges.spec.ts`: migration SQL과 rollback을 검증한다.
- `src/core/database/admin.datasource.ts`: 새 entity와 migration을 등록한다.
- `src/core/database/admin.datasource.spec.ts`: 마지막 migration과 entity 등록을 검증한다.
- `src/modules/payments/domain/subscription.model.ts`: 현재 결제수단 안전 스냅샷 타입을 추가한다.
- `src/modules/payments/domain/subscriptions.repository.ts`: 스냅샷 갱신과 원자적 현재 키 교체 계약을 추가한다.
- `src/modules/payments/domain/subscription-payment-method-change.model.ts`: 변경 상태와 consent/cleanup 모델을 정의한다.
- `src/modules/payments/domain/subscription-payment-method-changes.repository.ts`: 변경 생성·조회·조건부 전이·배치 조회 계약을 정의한다.
- `src/modules/payments/domain/toss-pay.provider.ts`: 토스 빌링키 상태의 안전한 표시 필드를 정의한다.
- `src/modules/payments/infrastructure/subscription.entity.ts`: 스냅샷 컬럼 매핑을 추가한다.
- `src/modules/payments/infrastructure/subscription-payment-method-change.entity.ts`: 변경 요청 entity를 추가한다.
- `src/modules/payments/infrastructure/typeorm-subscriptions.repository.ts`: 스냅샷·swap SQL을 구현한다.
- `src/modules/payments/infrastructure/typeorm-subscription-payment-method-changes.repository.ts`: 변경 요청 raw SQL repository를 구현한다.
- `src/modules/payments/infrastructure/http-toss-pay.provider.ts`: 토스 상태 응답의 safe metadata를 파싱한다.
- `src/modules/payments/application/subscription-payment-methods.service.ts`: 기능의 application orchestration을 전담한다.
- `src/modules/payments/application/subscription-payment-methods.service.spec.ts`: 조회·동의·교체·만료·복구 경쟁을 검증한다.
- `src/modules/payments/application/subscription-renewal.service.ts`: 새 승인 claim 직전에 open change gate를 추가한다.
- `src/modules/payments/application/payment-recovery.scheduler.ts`: 변경 만료·후보 키·이전 키 정리를 100개 배치로 실행한다.
- `src/modules/payments/presentation/dto/start-subscription-payment-method-change.dto.ts`: `past_due` consent snapshot 기대값을 검증한다.
- `src/modules/payments/presentation/dto/billing-result-callback.dto.ts`: safe metadata callback 필드를 추가한다.
- `src/modules/payments/presentation/subscriptions.controller.ts`: 인증된 조회·시작·상태·reconcile·cancel endpoints를 제공한다.
- `src/modules/payments/presentation/toss-pay-callback.controller.ts`: 현재 구독, 후보 키, 이전 키 callback을 안전하게 분기한다.
- `src/modules/payments/payments.module.ts`: entity, repository, service provider를 등록한다.

### `clipper_web_client`

- `src/app/core/api/models.ts`: 결제수단·변경 시작·변경 결과 모델을 추가한다.
- `src/app/core/api/payments-api.service.ts`: 새 5개 endpoint 호출을 추가한다.
- `src/app/core/api/mock/mock-data.ts`: 안전한 결제수단 mock을 추가한다.
- `src/app/core/api/mock/mock-api.interceptor.ts`: 새 endpoint mock 응답을 추가한다.
- `src/app/features/portal/dashboard/dashboard.component.{ts,html,scss}`: 결제수단 카드와 변경 시작 dialog를 추가한다.
- `src/app/features/portal/payment-method-result/payment-method-result.component.{ts,html,scss,spec.ts}`: 인증 복귀 후 최대 30초 상태 확인을 구현한다.
- `src/app/features/portal/portal.routes.ts`: 로그인 보호 아래 성공·취소 결과 route를 추가한다.
- `src/app/features/portal/portal.routes.spec.ts`: route lazy component를 검증한다.

---

### Task 1: OpenAPI Contract

**Files:**
- Modify: `clipper_web_api/docs/api/openapi.yaml`

**Interfaces:**
- Consumes: 기존 `Subscription`, `SubscriptionRenewalOrder`, `TossBillingResultCallback` schemas.
- Produces: `CurrentSubscriptionPaymentMethod`, `StartSubscriptionPaymentMethodChangeRequest`, `SubscriptionPaymentMethodChangeCheckout`, `SubscriptionPaymentMethodChangeResult` schemas와 5개 authenticated endpoints.

- [ ] **Step 1: 현재 OpenAPI 계약에서 사용자 응답에 provider 식별자나 빌링키가 없는지 기준을 기록한다**

Run:

```bash
cd /Users/jina/project/adlight/.worktrees/clipper_web_api-access-credit
nvm use 22
rg -n "billingKey|providerDisplayId|subscriptions/current" docs/api/openapi.yaml
```

Expected: callback schema에는 `billingKey`가 있지만 `Subscription` 응답에는 없다.

- [ ] **Step 2: 안전한 조회·변경 schemas를 추가한다**

Add these exact semantic shapes under `components.schemas`:

```yaml
SubscriptionPaymentMethod:
  type: object
  additionalProperties: false
  required: [providerStatus, payMethod, cardCompanyName, cardLast4, cardMethodType, accountBankName, verifiedAt]
  properties:
    providerStatus: { type: [string, 'null'] }
    payMethod: { type: [string, 'null'], enum: [CARD, TOSS_MONEY, null] }
    cardCompanyName: { type: [string, 'null'] }
    cardLast4: { type: [string, 'null'], pattern: '^[0-9]{4}$' }
    cardMethodType: { type: [string, 'null'] }
    accountBankName: { type: [string, 'null'] }
    verifiedAt: { type: [string, 'null'], format: date-time }

SubscriptionPaymentMethodChangeBlockReason:
  type: [string, 'null']
  enum: [SUBSCRIPTION_STATE, PAYMENT_RESULT_PENDING, CHANGE_IN_PROGRESS, null]

SubscriptionPaymentMethodRenewalConsent:
  type: object
  additionalProperties: false
  required: [orderNo, productName, amountKrw]
  properties:
    orderNo: { type: string }
    productName: { type: string }
    amountKrw: { type: integer, minimum: 1 }

CurrentSubscriptionPaymentMethod:
  type: object
  additionalProperties: false
  required: [paymentMethod, fresh, changeAllowed, changeBlockedReason, renewalConsent]
  properties:
    paymentMethod:
      oneOf:
        - { $ref: '#/components/schemas/SubscriptionPaymentMethod' }
        - { type: 'null' }
    fresh: { type: boolean }
    changeAllowed: { type: boolean }
    changeBlockedReason: { $ref: '#/components/schemas/SubscriptionPaymentMethodChangeBlockReason' }
    renewalConsent:
      oneOf:
        - { $ref: '#/components/schemas/SubscriptionPaymentMethodRenewalConsent' }
        - { type: 'null' }

StartSubscriptionPaymentMethodChangeRequest:
  type: object
  additionalProperties: false
  properties:
    expectedRenewalOrderNo: { type: string, maxLength: 120 }
    expectedAmountKrw: { type: integer, minimum: 1 }

SubscriptionPaymentMethodChangeCheckout:
  type: object
  additionalProperties: false
  required: [changeId, checkoutUrl, expiresAt]
  properties:
    changeId: { type: string, format: uuid }
    checkoutUrl: { type: string, format: uri }
    expiresAt: { type: string, format: date-time }

SubscriptionPaymentMethodChangeResult:
  type: object
  additionalProperties: false
  required: [changeId, status, expiresAt, retryAfterActivation, renewalOutcome, errorMessage]
  properties:
    changeId: { type: string, format: uuid }
    status:
      type: string
      enum: [created, checkout_ready, activated, swapped, canceled, expired, failed]
    expiresAt: { type: string, format: date-time }
    retryAfterActivation: { type: boolean }
    renewalOutcome:
      type: string
      enum: [not_required, pending, succeeded, failed]
    errorMessage: { type: [string, 'null'] }
```

- [ ] **Step 3: endpoints를 추가하고 상태 코드를 고정한다**

Add:

```yaml
/subscriptions/current/payment-method:
  get:
    operationId: getCurrentSubscriptionPaymentMethod
    security: [{ bearerAuth: [] }]
    responses:
      '200':
        content:
          application/json:
            schema: { $ref: '#/components/schemas/CurrentSubscriptionPaymentMethod' }
      '401': { description: Missing or invalid JWT. }
      '404': { description: Subscription not found. }

/subscriptions/current/payment-method/changes:
  post:
    operationId: startSubscriptionPaymentMethodChange
    security: [{ bearerAuth: [] }]
    requestBody:
      content:
        application/json:
          schema: { $ref: '#/components/schemas/StartSubscriptionPaymentMethodChangeRequest' }
    responses:
      '201':
        content:
          application/json:
            schema: { $ref: '#/components/schemas/SubscriptionPaymentMethodChangeCheckout' }
      '400': { description: Consent snapshot fields are incomplete. }
      '401': { description: Missing or invalid JWT. }
      '404': { description: Subscription or overdue renewal order not found. }
      '409': { description: State, amount, order, unresolved provider result, or open-change conflict. }
      '503': { description: Toss Pay registration is unavailable. }

/subscriptions/current/payment-method/changes/{changeId}:
  get:
    operationId: getSubscriptionPaymentMethodChange
    security: [{ bearerAuth: [] }]
    parameters:
      - name: changeId
        in: path
        required: true
        schema: { type: string, format: uuid }
    responses:
      '200':
        content:
          application/json:
            schema: { $ref: '#/components/schemas/SubscriptionPaymentMethodChangeResult' }
      '401': { description: Missing or invalid JWT. }
      '404': { description: Change not found for authenticated user. }

/subscriptions/current/payment-method/changes/{changeId}/reconcile:
  post:
    operationId: reconcileSubscriptionPaymentMethodChange
    security: [{ bearerAuth: [] }]
    responses:
      '201':
        content:
          application/json:
            schema: { $ref: '#/components/schemas/SubscriptionPaymentMethodChangeResult' }

/subscriptions/current/payment-method/changes/{changeId}/cancel:
  post:
    operationId: cancelSubscriptionPaymentMethodChange
    security: [{ bearerAuth: [] }]
    responses:
      '201':
        content:
          application/json:
            schema: { $ref: '#/components/schemas/SubscriptionPaymentMethodChangeResult' }
```

For the last two paths, copy the same required `changeId` path parameter and `401`/`404` responses from the GET path instead of using a shared unresolved reference.

- [ ] **Step 4: callback schema에 safe metadata만 추가한다**

Require `displayId` and add optional fields:

```yaml
TossBillingResultCallback:
  type: object
  additionalProperties: false
  required: [action, userId, displayId, billingKey]
  properties:
    action: { type: string, enum: [ACTIVATED, REMOVED] }
    userId: { type: string }
    displayId: { type: string }
    billingKey: { type: string }
    payMethod: { type: string }
    cardCompanyName: { type: string }
    cardNum4Print: { type: string, pattern: '^[0-9]{4}$' }
    cardMethodType: { type: string }
    accountBankName: { type: string }
```

- [ ] **Step 5: 계약 파일의 구조와 민감정보 노출을 확인한다**

Run:

```bash
npm run build
rg -n "CurrentSubscriptionPaymentMethod|payment-method/changes|cardNum4Print" docs/api/openapi.yaml
```

Expected: build passes; 사용자 response schema 어디에도 `billingKey`, `providerUserId`, `providerDisplayId` property가 없다.

- [ ] **Step 6: API 계약을 커밋한다**

```bash
git add docs/api/openapi.yaml
git commit -m "docs: define subscription payment method api"
```

---

### Task 2: Database Schema and Domain Models

**Files:**
- Create: `clipper_web_api/src/core/database/migrations/admin/1787200000000-CreateSubscriptionPaymentMethodChanges.ts`
- Create: `clipper_web_api/src/core/database/migrations/admin/1787200000000-CreateSubscriptionPaymentMethodChanges.spec.ts`
- Create: `clipper_web_api/src/modules/payments/domain/subscription-payment-method-change.model.ts`
- Create: `clipper_web_api/src/modules/payments/domain/subscription-payment-method-changes.repository.ts`
- Create: `clipper_web_api/src/modules/payments/infrastructure/subscription-payment-method-change.entity.ts`
- Modify: `clipper_web_api/src/modules/payments/domain/subscription.model.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/subscription.entity.ts`
- Modify: `clipper_web_api/src/core/database/admin.datasource.ts`
- Modify: `clipper_web_api/src/core/database/admin.datasource.spec.ts`

**Interfaces:**
- Consumes: `BillingKeyRemovalStatus`, TypeORM `EntityManager` binding pattern.
- Produces: `SubscriptionPaymentMethodSnapshot`, `SubscriptionPaymentMethodChange`, `SubscriptionPaymentMethodChangesRepository` and registered schema.

- [ ] **Step 1: migration test를 먼저 작성한다**

The test must capture `up()` and `down()` SQL and assert all of these literals:

```ts
expect(upSql).toContain('ADD COLUMN payment_method_provider_status');
expect(upSql).toContain('ADD COLUMN card_num4_print');
expect(upSql).toContain('CREATE TABLE subscription_payment_method_changes');
expect(upSql).toContain("status IN ('created', 'checkout_ready', 'activated', 'swapped', 'canceled', 'expired', 'failed')");
expect(upSql).toContain('REFERENCES subscriptions(id) ON DELETE RESTRICT');
expect(upSql).toContain('REFERENCES payment_orders(id) ON DELETE RESTRICT');
expect(upSql).toContain("WHERE status IN ('created', 'checkout_ready', 'activated')");
expect(downSql).toContain('DROP TABLE IF EXISTS subscription_payment_method_changes');
expect(downSql).toContain('DROP COLUMN IF EXISTS payment_method_provider_status');
```

- [ ] **Step 2: migration test를 실행해 실패를 확인한다**

Run:

```bash
npm test -- --runInBand src/core/database/migrations/admin/1787200000000-CreateSubscriptionPaymentMethodChanges.spec.ts
```

Expected: FAIL because the migration module does not exist.

- [ ] **Step 3: migration을 구현한다**

`up()` must add these nullable columns to `subscriptions`:

```sql
payment_method_provider_status varchar(20),
pay_method varchar(20),
card_company_name varchar(100),
card_num4_print varchar(4),
card_method_type varchar(30),
account_bank_name varchar(100),
payment_method_verified_at timestamptz
```

Create the change table with these exact columns:

```sql
id uuid PRIMARY KEY,
subscription_id uuid NOT NULL REFERENCES subscriptions(id) ON DELETE RESTRICT,
provider_display_id varchar(80) NOT NULL UNIQUE,
candidate_billing_key_enc text,
candidate_key_removal_status varchar(20) NOT NULL DEFAULT 'not_requested',
candidate_key_removal_error_code varchar(120),
status varchar(30) NOT NULL,
expires_at timestamptz NOT NULL,
retry_after_activation boolean NOT NULL DEFAULT false,
consented_renewal_order_id uuid REFERENCES payment_orders(id) ON DELETE RESTRICT,
consented_product_name varchar(200),
consented_amount_krw integer,
consented_at timestamptz,
previous_billing_key_enc text,
previous_provider_display_id varchar(80),
previous_key_removal_status varchar(20) NOT NULL DEFAULT 'not_requested',
previous_key_removal_error_code varchar(120),
error_code varchar(120),
completed_at timestamptz,
created_at timestamptz NOT NULL DEFAULT now(),
updated_at timestamptz NOT NULL DEFAULT now()
```

Add checks for status, candidate/previous removal status, positive consent amount, and all-or-none consent fields. Add:

```sql
CREATE UNIQUE INDEX uq_subscription_payment_method_changes_open
ON subscription_payment_method_changes(subscription_id)
WHERE status IN ('created', 'checkout_ready', 'activated');

CREATE INDEX idx_subscription_payment_method_changes_expiry
ON subscription_payment_method_changes(expires_at, id)
WHERE status IN ('created', 'checkout_ready', 'activated');

CREATE INDEX idx_subscription_payment_method_changes_candidate_removal
ON subscription_payment_method_changes(updated_at, id)
WHERE status IN ('canceled', 'expired', 'failed')
  AND candidate_key_removal_status IN ('pending', 'failed');

CREATE INDEX idx_subscription_payment_method_changes_previous_removal
ON subscription_payment_method_changes(updated_at, id)
WHERE status = 'swapped'
  AND previous_billing_key_enc IS NOT NULL
  AND previous_key_removal_status IN ('pending', 'failed');
```

`down()` drops indexes, table, then the seven subscription columns in reverse order.

- [ ] **Step 4: domain model을 추가한다**

Define:

```ts
export const SUBSCRIPTION_PAYMENT_METHOD_CHANGE_STATUSES = [
  'created', 'checkout_ready', 'activated', 'swapped', 'canceled', 'expired', 'failed',
] as const;

export type SubscriptionPaymentMethodChangeStatus =
  (typeof SUBSCRIPTION_PAYMENT_METHOD_CHANGE_STATUSES)[number];

export interface SubscriptionPaymentMethodSnapshot {
  providerStatus: string | null;
  payMethod: string | null;
  cardCompanyName: string | null;
  cardNum4Print: string | null;
  cardMethodType: string | null;
  accountBankName: string | null;
  verifiedAt: Date | null;
}

export interface SubscriptionPaymentMethodChange {
  id: string;
  subscriptionId: string;
  providerDisplayId: string;
  candidateBillingKeyEnc: string | null;
  candidateKeyRemovalStatus: BillingKeyRemovalStatus;
  candidateKeyRemovalErrorCode: string | null;
  status: SubscriptionPaymentMethodChangeStatus;
  expiresAt: Date;
  retryAfterActivation: boolean;
  consentedRenewalOrderId: string | null;
  consentedProductName: string | null;
  consentedAmountKrw: number | null;
  consentedAt: Date | null;
  previousBillingKeyEnc: string | null;
  previousProviderDisplayId: string | null;
  previousKeyRemovalStatus: BillingKeyRemovalStatus;
  previousKeyRemovalErrorCode: string | null;
  errorCode: string | null;
  completedAt: Date | null;
  createdAt: Date;
  updatedAt: Date;
}
```

Extend `Subscription` with the seven snapshot properties using the same names.

- [ ] **Step 5: repository abstract contract를 정의한다**

Define exact methods:

```ts
abstract bind(manager: EntityManager): SubscriptionPaymentMethodChangesRepository;
abstract create(input: NewSubscriptionPaymentMethodChange): Promise<SubscriptionPaymentMethodChange>;
abstract findById(id: string): Promise<SubscriptionPaymentMethodChange | undefined>;
abstract findByProviderDisplayId(displayId: string): Promise<SubscriptionPaymentMethodChange | undefined>;
abstract findByPreviousProviderDisplayId(displayId: string): Promise<SubscriptionPaymentMethodChange | undefined>;
abstract findOpenBySubscriptionId(subscriptionId: string): Promise<SubscriptionPaymentMethodChange | undefined>;
abstract hasOpenBySubscriptionId(subscriptionId: string): Promise<boolean>;
abstract setCheckoutReady(id: string, candidateBillingKeyEnc: string): Promise<SubscriptionPaymentMethodChange>;
abstract markActivated(id: string): Promise<SubscriptionPaymentMethodChange>;
abstract markSwapped(id: string, input: PreviousPaymentMethodInput): Promise<SubscriptionPaymentMethodChange>;
abstract markCanceled(id: string, at: Date): Promise<boolean>;
abstract markExpired(id: string, at: Date): Promise<boolean>;
abstract markFailed(id: string, errorCode: string, at: Date): Promise<SubscriptionPaymentMethodChange>;
abstract markCandidateKeyRemovalSucceeded(id: string): Promise<SubscriptionPaymentMethodChange>;
abstract markCandidateKeyRemovalFailed(id: string, errorCode: string): Promise<SubscriptionPaymentMethodChange>;
abstract markPreviousKeyRemovalSucceeded(id: string): Promise<SubscriptionPaymentMethodChange>;
abstract markPreviousKeyRemovalFailed(id: string, errorCode: string): Promise<SubscriptionPaymentMethodChange>;
abstract findExpiredOpenIds(at: Date, limit: number): Promise<string[]>;
abstract findPendingCandidateKeyRemovalIds(limit: number): Promise<string[]>;
abstract findPendingPreviousKeyRemovalIds(limit: number): Promise<string[]>;
```

`NewSubscriptionPaymentMethodChange` includes the UUIDs, display ID, expiry, retry flag, and nullable consent snapshot. `PreviousPaymentMethodInput` contains the encrypted old key and old display ID.

- [ ] **Step 6: entities와 datasource registration을 추가한다**

Map every column explicitly with snake_case names. Add `SubscriptionPaymentMethodChangeEntity` to both `TypeOrmModule.forFeature` later and `admin.datasource.ts` now. Register `CreateSubscriptionPaymentMethodChanges1787200000000` after `CreateSubscriptionRenewalPolicy1787100000000`.

Update datasource spec:

```ts
expect(entityNames).toContain('SubscriptionPaymentMethodChangeEntity');
expect(migrationNames.at(-1)).toBe(
  'CreateSubscriptionPaymentMethodChanges1787200000000',
);
```

- [ ] **Step 7: focused tests와 build를 실행한다**

Run:

```bash
npm test -- --runInBand src/core/database/migrations/admin/1787200000000-CreateSubscriptionPaymentMethodChanges.spec.ts src/core/database/admin.datasource.spec.ts
npm run build
```

Expected: PASS; TypeScript build succeeds.

- [ ] **Step 8: schema와 domain을 커밋한다**

```bash
git add src/core/database src/modules/payments/domain src/modules/payments/infrastructure/subscription.entity.ts src/modules/payments/infrastructure/subscription-payment-method-change.entity.ts
git commit -m "feat: add payment method change schema"
```

---

### Task 3: TypeORM Repositories and Safe Subscription Snapshot

**Files:**
- Create: `clipper_web_api/src/modules/payments/infrastructure/typeorm-subscription-payment-method-changes.repository.ts`
- Create: `clipper_web_api/src/modules/payments/infrastructure/typeorm-subscription-payment-method-changes.repository.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/domain/subscriptions.repository.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/typeorm-subscriptions.repository.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/typeorm-subscriptions.repository.spec.ts`

**Interfaces:**
- Consumes: Task 2 models and abstract repository.
- Produces: concurrency-safe change transitions plus `updatePaymentMethodSnapshot()` and `swapPaymentMethod()`.

- [ ] **Step 1: repository failure tests를 작성한다**

Cover these exact cases with mocked `EntityManager.query` rows:

```ts
it('open 상태만 조건부로 expired 전이한다');
it('partial unique violation은 진행 중 변경 충돌로 변환한다');
it('이전 display id로 swapped 변경을 찾는다');
it('취소·만료·실패 후보 키 삭제 대상을 100개 이하로 찾는다');
it('이전 키 삭제 대상은 swapped pending/failed만 100개 이하로 찾는다');
it('row의 timestamptz와 snake_case 필드를 domain model로 변환한다');
```

Extend subscription repository tests:

```ts
it('stores only safe payment method metadata');
it('swaps key, display id and safe snapshot with active/past_due status guard');
it('does not include open method changes in new due charge selection but keeps unresolved order reconciliation selectable');
```

- [ ] **Step 2: tests를 실행해 실패를 확인한다**

Run:

```bash
npm test -- --runInBand src/modules/payments/infrastructure/typeorm-subscription-payment-method-changes.repository.spec.ts src/modules/payments/infrastructure/typeorm-subscriptions.repository.spec.ts
```

Expected: FAIL because implementation and new subscription methods are absent.

- [ ] **Step 3: subscription repository 계약을 추가한다**

Add:

```ts
export interface SwapSubscriptionPaymentMethodInput {
  billingKeyEnc: string;
  providerDisplayId: string;
  snapshot: SubscriptionPaymentMethodSnapshot;
}

abstract updatePaymentMethodSnapshot(
  id: string,
  snapshot: SubscriptionPaymentMethodSnapshot,
): Promise<Subscription>;

abstract swapPaymentMethod(
  id: string,
  input: SwapSubscriptionPaymentMethodInput,
): Promise<Subscription>;
```

- [ ] **Step 4: change repository를 raw SQL로 구현한다**

Use the existing `bind(manager)` pattern. Conditional transitions must return booleans where a callback/scheduler race is expected:

```sql
UPDATE subscription_payment_method_changes
SET status = 'expired', completed_at = $2, updated_at = now()
WHERE id = $1
  AND status IN ('created', 'checkout_ready', 'activated')
  AND expires_at <= $2
RETURNING id
```

`markCanceled` uses the same open status set without the expiry comparison. `markCanceled`, `markExpired`, and `markFailed` set `candidate_key_removal_status='pending'` so provider creation succeeded just before a process crash even when `candidate_billing_key_enc` is still null. `markSwapped` accepts only `activated`, leaves candidate removal `not_requested` because that key is now current, and stores old encrypted key/display ID with previous removal status `pending` when an old key exists, otherwise `not_requested`.

- [ ] **Step 5: subscription snapshot and swap SQL을 구현한다**

`updatePaymentMethodSnapshot` updates only the seven safe columns. `swapPaymentMethod` performs one guarded update:

```sql
UPDATE subscriptions
SET billing_key_enc = $2,
    provider_display_id = $3,
    payment_method_provider_status = $4,
    pay_method = $5,
    card_company_name = $6,
    card_num4_print = $7,
    card_method_type = $8,
    account_bank_name = $9,
    payment_method_verified_at = $10,
    billing_key_removal_status = 'not_requested',
    updated_at = now()
WHERE id = $1 AND status IN ('active', 'past_due')
RETURNING *
```

Do not change period, retry cursor, access, or order fields.

In `findDueRenewalIds`, keep the unresolved-order `EXISTS` branch independent. Add the open-change `NOT EXISTS` guard only to the `active next_billing_at` and `past_due retry_at` branches so an already pending/paid-unfulfilled order remains recoverable.

- [ ] **Step 6: tests와 build를 실행한다**

Run:

```bash
npm test -- --runInBand src/modules/payments/infrastructure/typeorm-subscription-payment-method-changes.repository.spec.ts src/modules/payments/infrastructure/typeorm-subscriptions.repository.spec.ts
npm run build
```

Expected: PASS.

- [ ] **Step 7: repositories를 커밋한다**

```bash
git add src/modules/payments/domain src/modules/payments/infrastructure
git commit -m "feat: persist subscription payment method changes"
```

---

### Task 4: Toss Provider Safe Metadata

**Files:**
- Modify: `clipper_web_api/src/modules/payments/domain/toss-pay.provider.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/http-toss-pay.provider.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/http-toss-pay.provider.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/presentation/dto/billing-result-callback.dto.ts`

**Interfaces:**
- Consumes: Toss billing status/callback response.
- Produces: `TossBillingKeyStatus` with nullable safe metadata and validated callback DTO fields.

- [ ] **Step 1: provider parsing tests를 먼저 추가한다**

```ts
expect(await provider.getBillingKeyStatus(input)).toEqual({
  userId: 'provider-user',
  billingKey: 'secret-key',
  status: 'ACTIVE',
  payMethod: 'CARD',
  cardCompanyName: '신한카드',
  cardNum4Print: '1234',
  cardMethodType: 'CREDIT',
  accountBankName: null,
});
```

Add separate assertions for `TOSS_MONEY` and missing optional fields. Add DTO validation tests through the callback controller suite so `cardNum4Print: '12345'` is rejected.

- [ ] **Step 2: focused test를 실행해 실패를 확인한다**

Run:

```bash
npm test -- --runInBand src/modules/payments/infrastructure/http-toss-pay.provider.spec.ts src/modules/payments/presentation/toss-pay-callback.controller.spec.ts
```

Expected: safe fields are missing from returned values.

- [ ] **Step 3: provider type과 parser를 구현한다**

Extend the interface:

```ts
export interface TossBillingKeyStatus {
  userId: string;
  billingKey: string;
  status: string;
  payMethod: string | null;
  cardCompanyName: string | null;
  cardNum4Print: string | null;
  cardMethodType: string | null;
  accountBankName: string | null;
}
```

Use `optionalString` for every display field, then normalize `cardNum4Print` to `null` unless it matches `/^[0-9]{4}$/`. Never return the complete provider payload.

- [ ] **Step 4: callback DTO에 같은 safe fields를 추가한다**

Use `@IsOptional()`, `@IsString()`, and for the last four digits `@Matches(/^\d{4}$/)`.

- [ ] **Step 5: tests와 build를 실행한다**

Run:

```bash
npm test -- --runInBand src/modules/payments/infrastructure/http-toss-pay.provider.spec.ts src/modules/payments/presentation/toss-pay-callback.controller.spec.ts
npm run build
```

Expected: PASS.

- [ ] **Step 6: provider support를 커밋한다**

```bash
git add src/modules/payments/domain/toss-pay.provider.ts src/modules/payments/infrastructure/http-toss-pay.provider.ts src/modules/payments/infrastructure/http-toss-pay.provider.spec.ts src/modules/payments/presentation/dto/billing-result-callback.dto.ts
git commit -m "feat: read safe toss billing metadata"
```

---

### Task 5: Payment Method Read and Change Start Service

**Files:**
- Create: `clipper_web_api/src/modules/payments/application/subscription-payment-methods.service.ts`
- Create: `clipper_web_api/src/modules/payments/application/subscription-payment-methods.service.spec.ts`
- Create: `clipper_web_api/src/modules/payments/presentation/dto/start-subscription-payment-method-change.dto.ts`

**Interfaces:**
- Consumes: subscription, change, order repositories; `TossPayProvider`; `SecretCipher`; `ConfigService`; `AdminTransactionRunner`.
- Produces: `current(userId)`, `start(userId,dto,now)`, `get(userId,changeId)`, `cancel(userId,changeId,now)`.

- [ ] **Step 1: current 조회 tests를 작성한다**

Cover:

```ts
it('ACTIVE status와 암호화 키 일치 시 safe snapshot만 반환하고 갱신한다');
it('provider 조회 실패 시 cached snapshot과 fresh=false를 반환한다');
it('cache가 없고 provider 조회가 실패하면 paymentMethod=null을 반환한다');
it('active면 changeAllowed=true와 renewalConsent=null을 반환한다');
it('past_due면 authoritative renewal order의 상품명·금액을 반환한다');
it('payment_pending 또는 paid-unfulfilled renewal이면 PAYMENT_RESULT_PENDING으로 막는다');
it('open change가 있으면 CHANGE_IN_PROGRESS로 막는다');
it('cancel_at_period_end 등 비허용 상태면 SUBSCRIPTION_STATE로 막는다');
```

Provider key comparison test must decrypt `billingKeyEnc` and assert a mismatch is treated as `fresh=false`; it must not place either key in a thrown message.

- [ ] **Step 2: change 시작 tests를 작성한다**

Cover:

```ts
it('active 변경은 consent 없이 30분 만료 request를 만들고 Toss checkout을 반환한다');
it('past_due 변경은 expected orderNo와 amount를 모두 요구한다');
it('past_due의 기대값과 서버 order가 다르면 시작하지 않는다');
it('provider result가 unresolved면 시작하지 않는다');
it('open change가 있으면 새 후보를 만들지 않는다');
it('Toss create 성공 뒤 후보 키 암호화 저장이 끝나야 checkout URL을 반환한다');
it('Toss create 실패 시 request를 failed로 전이하고 현재 subscription key를 유지한다');
```

Assert `expiresAt === new Date(now.getTime() + 30 * 60_000)`.

- [ ] **Step 3: tests를 실행해 실패를 확인한다**

Run:

```bash
npm test -- --runInBand src/modules/payments/application/subscription-payment-methods.service.spec.ts
```

Expected: FAIL because the service does not exist.

- [ ] **Step 4: DTO validation을 구현한다**

```ts
export class StartSubscriptionPaymentMethodChangeDto {
  @IsOptional()
  @IsString()
  @MaxLength(120)
  expectedRenewalOrderNo?: string;

  @IsOptional()
  @IsInt()
  @Min(1)
  expectedAmountKrw?: number;
}
```

The service, not the DTO alone, enforces that both fields are absent for `active` and both are present for `past_due`.

- [ ] **Step 5: current 조회를 구현한다**

Use `findLatestByUserId`. Build a safe response with no identifiers. The provider refresh path:

```ts
const status = await this.toss.getBillingKeyStatus({
  userId: subscription.providerUserId,
  displayId: subscription.providerDisplayId,
});
const storedKey = this.cipher.decrypt(subscription.billingKeyEnc);
if (status.userId !== subscription.providerUserId || status.billingKey !== storedKey) {
  throw new TossPayProviderError('billing status identity mismatch');
}
```

Map safe metadata to `SubscriptionPaymentMethodSnapshot` with `verifiedAt: now`, persist it, and return `fresh: true`. In the provider failure catch, return the stored snapshot with `fresh: false`; do not fail dashboard loading.

Find the renewal consent order by the current idempotency key:

```ts
const key = `renewal:${subscription.id}:${subscription.currentPeriodEnd!.toISOString()}`;
const order = await orders.findByIdempotencyKey(key);
```

Return it only for `past_due` and only when it is the current failed/retryable renewal order.

- [ ] **Step 6: change 시작을 구현한다**

Within one admin transaction and subscription advisory lock:

1. Re-read the subscription.
2. Require `active` or `past_due`.
3. Require `hasUnresolvedRenewal=false`.
4. Require `findOpenBySubscriptionId` to be empty.
5. For `past_due`, compare DTO order and amount to the authoritative current renewal order.
6. Insert `created` with a random UUID, `displayId` prefix `clipper-method-`, expiry +30 minutes, and consent snapshot.

After commit, call `createBillingKey` with:

```ts
{
  userId: subscription.providerUserId,
  displayId: change.providerDisplayId,
  productDesc: 'Clipper 자동결제 수단 변경',
  resultCallback: `${callbackBase}/payments/toss/billing/result-callback`,
  returnSuccessUrl: `${webBase}/app/payment-method/result?change=${change.id}`,
  returnFailureUrl: `${webBase}/app/payment-method/cancel?change=${change.id}`,
}
```

Encrypt and persist the candidate key before returning `checkoutUri`.

- [ ] **Step 7: authenticated get/cancel model helpers를 구현한다**

`get(userId,changeId)` loads the change and subscription and returns 404 unless ownership matches. Derive `renewalOutcome` from the consented renewal order:

- no retry flag: `not_required`
- paid + fulfillment succeeded: `succeeded`
- failed/canceled: `failed`
- all other states: `pending`

`cancel()` conditionally changes only `created|checkout_ready|activated` to `canceled`; it never edits `subscriptions`.

- [ ] **Step 8: focused tests와 build를 실행한다**

Run:

```bash
npm test -- --runInBand src/modules/payments/application/subscription-payment-methods.service.spec.ts
npm run build
```

Expected: PASS.

- [ ] **Step 9: query/start service를 커밋한다**

```bash
git add src/modules/payments/application/subscription-payment-methods.service.ts src/modules/payments/application/subscription-payment-methods.service.spec.ts src/modules/payments/presentation/dto/start-subscription-payment-method-change.dto.ts
git commit -m "feat: start subscription payment method changes"
```

---

### Task 6: Candidate Verification, Atomic Swap, and Immediate Past-Due Retry

**Files:**
- Modify: `clipper_web_api/src/modules/payments/application/subscription-payment-methods.service.ts`
- Modify: `clipper_web_api/src/modules/payments/application/subscription-payment-methods.service.spec.ts`

**Interfaces:**
- Consumes: Task 5 service and `SubscriptionRenewalService.retryCurrent()`.
- Produces: `handleCandidateBillingResult(dto,now)`, `reconcile(userId,changeId,now)`, idempotent activation/swap.

- [ ] **Step 1: verification and race tests를 작성한다**

Cover:

```ts
it('callback user/display/key와 provider ACTIVE identity가 모두 일치해야 swap한다');
it('후보 ACTIVE가 아니면 현재 키를 유지한다');
it('expiresAt 이상이면 late candidate를 연결하지 않고 expired 처리한다');
it('callback과 reconcile이 동시에 와도 한 번만 swapped 전이에 성공한다');
it('swap transaction은 old key/display를 change에 옮기고 새 safe snapshot을 subscription에 쓴다');
it('active swap은 bill이나 retryCurrent를 호출하지 않는다');
it('past_due swap은 consent order와 amount를 재검증한 뒤 retryCurrent를 한 번 호출한다');
it('consent 이후 주문·금액·구독 상태가 달라지면 승인하지 않고 candidate를 failed 처리한다');
it('동시에 기존 카드 수동 재시도가 payment_pending을 만들면 후보를 swap하지 않는다');
it('즉시 retry 실패는 새 결제수단을 유지하고 past_due를 유지한다');
it('중복 callback은 두 번째 swap과 두 번째 retry를 실행하지 않는다');
```

- [ ] **Step 2: tests를 실행해 실패를 확인한다**

Run:

```bash
npm test -- --runInBand src/modules/payments/application/subscription-payment-methods.service.spec.ts
```

Expected: FAIL on absent callback/reconcile behavior.

- [ ] **Step 3: shared candidate verification을 구현한다**

Both callback and reconcile call one private method. It must:

1. Load by candidate `providerDisplayId` or authenticated `changeId`.
2. Return existing terminal result for `swapped|canceled|expired|failed`.
3. Compare DB time to `expiresAt` before provider call.
4. Decrypt candidate key and call status API.
5. Require status `ACTIVE`, matching user ID, display ID context, and exact billing key.
6. Build the safe snapshot only from status response.

Callback additionally requires DTO user/display/billing key equality before the provider call. `reconcile` uses stored candidate identity and never accepts client-provided billing identity.

- [ ] **Step 4: atomic swap을 구현한다**

Inside one transaction:

```ts
await subscriptions.withSubscriptionLock(subscriptionId, async () => {
  const currentSubscription = await subscriptions.findById(subscriptionId);
  const currentChange = await changes.findById(changeId);
  await changes.markActivated(changeId);
  await subscriptions.swapPaymentMethod(subscriptionId, {
    billingKeyEnc: currentChange.candidateBillingKeyEnc!,
    providerDisplayId: currentChange.providerDisplayId,
    snapshot,
  });
  await changes.markSwapped(changeId, {
    previousBillingKeyEnc: currentSubscription.billingKeyEnc,
    previousProviderDisplayId: currentSubscription.providerDisplayId,
  });
});
```

Before `markActivated`, require that the change is open and unexpired, the subscription is still `active|past_due`, and a `past_due` consent order is still the same failed/retryable order with the same amount. If that order became `payment_pending` or `paid` through a concurrent retry, do not swap. Use the transaction-bound repositories for every call. Never decrypt the old key inside this transaction.

- [ ] **Step 5: post-commit actions를 구현한다**

After swap commit:

- If `retryAfterActivation`, call `renewals.retryCurrent(userId)` exactly once for the winner that performed `swapped`.
- After the immediate retry attempt, call `removePreviousKey(changeId)`; removal failure is caught and persisted for scheduler retry, and never changes the payment result.
- If retry throws provider/payment failure, return a `swapped` result with `renewalOutcome='failed'` as derived from the order, or `pending` when result remains uncertain. Do not revert the new key.

- [ ] **Step 6: reconcile behavior를 구현한다**

`reconcile()` performs at most one status lookup per HTTP call when local state is `checkout_ready` or `activated`. It returns immediately for all terminal states. The web page controls the 2-second retry frequency; the server does not start a polling loop.

- [ ] **Step 7: focused tests와 build를 실행한다**

Run:

```bash
npm test -- --runInBand src/modules/payments/application/subscription-payment-methods.service.spec.ts src/modules/payments/application/subscription-renewal.service.spec.ts
npm run build
```

Expected: PASS.

- [ ] **Step 8: swap flow를 커밋한다**

```bash
git add src/modules/payments/application/subscription-payment-methods.service.ts src/modules/payments/application/subscription-payment-methods.service.spec.ts
git commit -m "feat: swap subscription billing method safely"
```

---

### Task 7: Renewal Gate, Expiry, and Billing-Key Cleanup Recovery

**Files:**
- Modify: `clipper_web_api/src/modules/payments/application/subscription-renewal.service.ts`
- Modify: `clipper_web_api/src/modules/payments/application/subscription-renewal.service.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/application/payment-recovery.scheduler.ts`
- Modify: `clipper_web_api/src/modules/payments/application/payment-recovery.scheduler.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/application/subscription-payment-methods.service.ts`
- Modify: `clipper_web_api/src/modules/payments/application/subscription-payment-methods.service.spec.ts`

**Interfaces:**
- Consumes: `hasOpenBySubscriptionId`, change batch finders, candidate/previous encrypted keys.
- Produces: no-new-charge gate and bounded recovery methods `expire(changeId,now)`, `removeCandidateKey(changeId)`, `removePreviousKey(changeId)`.

- [ ] **Step 1: renewal gate tests를 작성한다**

Cover the distinction explicitly:

```ts
it('open change가 있으면 새 renewal order claim을 시작하지 않는다');
it('open change 중에도 기존 payment_pending order status reconcile은 계속한다');
it('open change 중에도 paid-unfulfilled order fulfillment는 계속한다');
it('manual retry도 새 claim 직전에 open change를 거부한다');
```

The gate belongs after existing paid/pending order branches and immediately before creating/reclaiming a new provider charge. For stale `payment_pending` reclaim, do not block provider result verification; only block a not-found row from being billed again while the change is open.

- [ ] **Step 2: expiry and cleanup tests를 작성한다**

```ts
it('30분 지난 open change 한 worker만 expired 전이한다');
it('expired candidate key 삭제 성공을 terminal cleanup으로 끝낸다');
it('candidate 삭제 실패가 subscription current key를 바꾸지 않는다');
it('swapped old key 삭제 성공과 실패를 change row에 기록한다');
it('late ACTIVE after expired는 candidate 삭제만 하고 swap하지 않는다');
it('expired 처리 후 due retry가 다시 selectable하다');
```

- [ ] **Step 3: scheduler tests를 작성한다**

Assert call order and bounds:

```ts
expect(changes.findExpiredOpenIds).toHaveBeenCalledWith(now, 100);
expect(changes.findPendingCandidateKeyRemovalIds).toHaveBeenCalledWith(100);
expect(changes.findPendingPreviousKeyRemovalIds).toHaveBeenCalledWith(100);
expect(paymentMethods.expire).toHaveBeenCalledWith(changeId, expect.any(Date));
expect(paymentMethods.removeCandidateKey).toHaveBeenCalledWith(changeId);
expect(paymentMethods.removePreviousKey).toHaveBeenCalledWith(changeId);
```

Every item failure must be isolated through the existing `independently()` helper.

- [ ] **Step 4: tests를 실행해 실패를 확인한다**

Run:

```bash
npm test -- --runInBand src/modules/payments/application/subscription-renewal.service.spec.ts src/modules/payments/application/payment-recovery.scheduler.spec.ts src/modules/payments/application/subscription-payment-methods.service.spec.ts
```

Expected: FAIL on missing gates and cleanup calls.

- [ ] **Step 5: renewal gate를 구현한다**

Inject `SubscriptionPaymentMethodChangesRepository`. In the transaction-bound `renew()` preparation:

```ts
const changes = this.paymentMethodChanges.bind(manager);
if (await changes.hasOpenBySubscriptionId(subscription.id)) {
  throw new ConflictException('PAYMENT_METHOD_CHANGE_IN_PROGRESS');
}
```

Place this block only after the existing paid and `payment_pending` reuse/reconciliation branches and immediately before a new charge claim. Repeat the guard inside stale claim reclaim immediately before `tryReclaimRenewalCharge`, after fresh subscription/order reload.

- [ ] **Step 6: cleanup methods를 구현한다**

- `expire(id,now)`: conditionally marks expired; only the winning transition schedules candidate cleanup.
- `removeCandidateKey(id)`: allowed for `canceled|expired|failed` with pending/failed candidate cleanup. If `candidateBillingKeyEnc` exists, decrypt and remove it. If it is null, query Toss once with the subscription's provider user ID and the stored candidate display ID to recover a provider-created key from the create-call crash gap, then remove the exact returned key. A transient status/removal failure records `candidate_key_removal_status='failed'` for bounded retry. It never changes `subscriptions`.
- `removePreviousKey(id)`: allowed only for `swapped` with pending/failed cleanup; decrypts previous key, calls Toss remove, conditionally records success/failure.
- Errors stored in candidate/previous removal error columns are sanitized provider error codes capped at 120 chars, never raw payloads.

- [ ] **Step 7: scheduler에 세 bounded loops를 추가한다**

Call expiration before renewal processing so just-expired changes unblock on the same scheduler minute. Then process terminal candidate-key cleanup. Call old-key cleanup after renewal/fulfillment. Use a fresh clock for each item, following the existing deadline-safety pattern.

- [ ] **Step 8: focused tests와 build를 실행한다**

Run:

```bash
npm test -- --runInBand src/modules/payments/application/subscription-renewal.service.spec.ts src/modules/payments/application/payment-recovery.scheduler.spec.ts src/modules/payments/application/subscription-payment-methods.service.spec.ts
npm run build
```

Expected: PASS.

- [ ] **Step 9: concurrency and recovery를 커밋한다**

```bash
git add src/modules/payments/application/subscription-renewal.service.ts src/modules/payments/application/subscription-renewal.service.spec.ts src/modules/payments/application/payment-recovery.scheduler.ts src/modules/payments/application/payment-recovery.scheduler.spec.ts src/modules/payments/application/subscription-payment-methods.service.ts src/modules/payments/application/subscription-payment-methods.service.spec.ts
git commit -m "feat: recover payment method changes safely"
```

---

### Task 8: Controllers, Callback Routing, and Module Wiring

**Files:**
- Modify: `clipper_web_api/src/modules/payments/presentation/subscriptions.controller.ts`
- Modify: `clipper_web_api/src/modules/payments/presentation/subscriptions.controller.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/presentation/toss-pay-callback.controller.ts`
- Modify: `clipper_web_api/src/modules/payments/presentation/toss-pay-callback.controller.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/payments.module.ts`

**Interfaces:**
- Consumes: Task 5–7 service methods.
- Produces: OpenAPI-matching protected endpoints and callback dispatch priority.

- [ ] **Step 1: subscription controller tests를 추가한다**

Assert the authenticated user ID is passed to:

```ts
paymentMethods.current(userId);
paymentMethods.start(userId, dto);
paymentMethods.get(userId, changeId);
paymentMethods.reconcile(userId, changeId);
paymentMethods.cancel(userId, changeId);
```

Also assert UUID validation rejects invalid `changeId` by applying `ParseUUIDPipe` to each path parameter.

- [ ] **Step 2: callback routing tests를 추가한다**

The routing order must be:

```ts
1. subscriptions.findByProviderDisplayId(displayId)
2. changes.findByProviderDisplayId(displayId)
3. changes.findByPreviousProviderDisplayId(displayId)
4. reviewPayments.handleBillingResult(dto)
```

Cover:

```ts
it('swapped candidate now belonging to current subscription uses current-subscription callback');
it('not-yet-swapped candidate uses payment-method change callback');
it('late old REMOVED callback marks old-key cleanup and never cancels current subscription');
it('unknown display id falls through to review checkout callback');
```

- [ ] **Step 3: tests를 실행해 실패를 확인한다**

Run:

```bash
npm test -- --runInBand src/modules/payments/presentation/subscriptions.controller.spec.ts src/modules/payments/presentation/toss-pay-callback.controller.spec.ts
```

Expected: FAIL because new routes and dispatch dependencies are missing.

- [ ] **Step 4: controller endpoints를 구현한다**

Add these decorators exactly:

```ts
@Get('subscriptions/current/payment-method')
@Post('subscriptions/current/payment-method/changes')
@Get('subscriptions/current/payment-method/changes/:changeId')
@Post('subscriptions/current/payment-method/changes/:changeId/reconcile')
@Post('subscriptions/current/payment-method/changes/:changeId/cancel')
```

Continue using the class-level JWT guard and whitelist validation pipe.

- [ ] **Step 5: callback routing을 구현한다**

For current subscription, preserve the existing handler. For candidate change, call `handleCandidateBillingResult`. For previous old key, accept only `REMOVED` and call `handlePreviousBillingKeyRemoved`; that handler decrypts the stored previous key and requires both callback user ID and callback key to match before recording cleanup success. `ACTIVATED` for an old ID is ignored/rejected without mutating current subscription.

- [ ] **Step 6: module wiring을 구현한다**

Register:

```ts
TypeOrmModule.forFeature([
  PaymentOrderEntity,
  PaymentEventEntity,
  SubscriptionEntity,
  SubscriptionPaymentMethodChangeEntity,
], 'admin')
```

Add `SubscriptionPaymentMethodsService` and bind `SubscriptionPaymentMethodChangesRepository` to `TypeOrmSubscriptionPaymentMethodChangesRepository`.

- [ ] **Step 7: controller tests와 build를 실행한다**

Run:

```bash
npm test -- --runInBand src/modules/payments/presentation/subscriptions.controller.spec.ts src/modules/payments/presentation/toss-pay-callback.controller.spec.ts
npm run build
```

Expected: PASS.

- [ ] **Step 8: API surface를 커밋한다**

```bash
git add src/modules/payments/presentation src/modules/payments/payments.module.ts
git commit -m "feat: expose subscription payment method changes"
```

---

### Task 9: Web Client API Models and Service

**Files:**
- Modify: `clipper_web_client/src/app/core/api/models.ts`
- Modify: `clipper_web_client/src/app/core/api/payments-api.service.ts`
- Modify: `clipper_web_client/src/app/core/api/payments-api.service.spec.ts`
- Modify: `clipper_web_client/src/app/core/api/mock/mock-data.ts`
- Modify: `clipper_web_client/src/app/core/api/mock/mock-api.interceptor.ts`
- Modify: `clipper_web_client/src/app/core/api/mock/mock-api.interceptor.spec.ts`

**Interfaces:**
- Consumes: Task 1 OpenAPI schemas.
- Produces: Angular models and five typed HTTP methods.

- [ ] **Step 1: API service tests를 작성한다**

Assert exact URLs, methods, credentials, and bodies:

```ts
getCurrentPaymentMethod();
startPaymentMethodChange({ expectedRenewalOrderNo, expectedAmountKrw });
getPaymentMethodChange(changeId);
reconcilePaymentMethodChange(changeId);
cancelPaymentMethodChange(changeId);
```

Every authenticated call uses `{ withCredentials: true }`.

- [ ] **Step 2: tests를 실행해 실패를 확인한다**

Run:

```bash
cd /Users/jina/project/adlight/.worktrees/clipper_web_client-access-credit
nvm use 22
npm test -- --watch=false --browsers=ChromeHeadless --include=src/app/core/api/payments-api.service.spec.ts
```

Expected: FAIL because methods and models are absent.

- [ ] **Step 3: TypeScript models를 OpenAPI와 동일하게 추가한다**

```ts
export interface SubscriptionPaymentMethod {
  providerStatus: string | null;
  payMethod: 'CARD' | 'TOSS_MONEY' | null;
  cardCompanyName: string | null;
  cardLast4: string | null;
  cardMethodType: string | null;
  accountBankName: string | null;
  verifiedAt: string | null;
}

export interface CurrentSubscriptionPaymentMethod {
  paymentMethod: SubscriptionPaymentMethod | null;
  fresh: boolean;
  changeAllowed: boolean;
  changeBlockedReason: 'SUBSCRIPTION_STATE' | 'PAYMENT_RESULT_PENDING' | 'CHANGE_IN_PROGRESS' | null;
  renewalConsent: { orderNo: string; productName: string; amountKrw: number } | null;
}

export type SubscriptionPaymentMethodChangeStatus =
  | 'created' | 'checkout_ready' | 'activated' | 'swapped'
  | 'canceled' | 'expired' | 'failed';

export interface SubscriptionPaymentMethodChangeResult {
  changeId: string;
  status: SubscriptionPaymentMethodChangeStatus;
  expiresAt: string;
  retryAfterActivation: boolean;
  renewalOutcome: 'not_required' | 'pending' | 'succeeded' | 'failed';
  errorMessage: string | null;
}
```

- [ ] **Step 4: HTTP methods와 mock paths를 구현한다**

Use `encodeURIComponent(changeId)` for every path. The mock must return a card ending in `1234` and never include billing/provider identifiers. A mock start request returns `/app/payment-method/result?change=<uuid>`.

- [ ] **Step 5: focused tests와 build를 실행한다**

Run:

```bash
npm test -- --watch=false --browsers=ChromeHeadless --include=src/app/core/api/payments-api.service.spec.ts --include=src/app/core/api/mock/mock-api.interceptor.spec.ts
npm run build
```

Expected: PASS.

- [ ] **Step 6: client API layer를 커밋한다**

```bash
git add src/app/core/api
git commit -m "feat: add payment method client api"
```

---

### Task 10: Dashboard Payment Method Card and Consent Dialog

**Files:**
- Modify: `clipper_web_client/src/app/features/portal/dashboard/dashboard.component.ts`
- Modify: `clipper_web_client/src/app/features/portal/dashboard/dashboard.component.html`
- Modify: `clipper_web_client/src/app/features/portal/dashboard/dashboard.component.scss`
- Modify: `clipper_web_client/src/app/features/portal/dashboard/dashboard.component.spec.ts`

**Interfaces:**
- Consumes: Task 9 `PaymentsApiService` methods and current `ConfirmDialogComponent`.
- Produces: safe payment method UI, normal/past-due change consent, Toss redirect.

- [ ] **Step 1: component behavior tests를 작성한다**

Cover:

```ts
it('카드사·끝 4자리·카드 종류·마지막 확인 시각을 표시한다');
it('Toss Money는 연결 은행명을 표시하고 카드 필드는 표시하지 않는다');
it('fresh=false면 마지막 확인 정보임을 표시한다');
it('paymentMethod=null이면 정보를 불러오지 못했다는 문구를 표시한다');
it('active 변경 확인창은 지금 결제되지 않고 다음 결제부터 적용됨을 표시한다');
it('past_due 확인창은 상품명·정확한 금액과 변경하고 n원 결제 CTA를 표시한다');
it('past_due 시작 body에 화면 응답의 orderNo와 amount만 보낸다');
it('changeAllowed=false면 변경 버튼을 비활성화하고 차단 이유를 표시한다');
it('start 성공 후 checkoutUrl로 이동한다');
it('기존 결제 다시 시도 버튼은 계속 현재 retry endpoint를 호출한다');
```

- [ ] **Step 2: tests를 실행해 실패를 확인한다**

Run:

```bash
npm test -- --watch=false --browsers=ChromeHeadless --include=src/app/features/portal/dashboard/dashboard.component.spec.ts
```

Expected: FAIL because the payment method card is absent.

- [ ] **Step 3: loading state를 분리해 구현한다**

Increase `pendingLoads` from 3 to 4, but do not set global `loadError` when payment-method refresh alone fails. Add:

```ts
readonly paymentMethod = signal<CurrentSubscriptionPaymentMethod | null>(null);
readonly paymentMethodLoadError = signal(false);
readonly changingPaymentMethod = signal(false);
readonly paymentMethodChangeError = signal<string | null>(null);
```

Call `getCurrentPaymentMethod()` only after a non-null current subscription is loaded; when no subscription exists, decrement the fourth pending load without issuing the request.

- [ ] **Step 4: display label helpers를 구현한다**

- CARD: `토스페이 · {cardCompanyName} · **** {cardLast4}`.
- TOSS_MONEY: `토스페이 · 토스머니 · {accountBankName}`.
- Missing values: `토스페이 자동결제 수단`.
- `fresh=false`: `마지막으로 확인된 정보`.

Do not render provider status codes verbatim except `ACTIVE` as `정상 등록됨`; other values render `결제수단 확인 필요`.

- [ ] **Step 5: active와 past_due dialog를 구현한다**

Active message:

```text
새 결제수단 등록이 완료되면 다음 결제부터 새 결제수단이 사용됩니다. 지금은 결제되지 않습니다.
```

Past-due message:

```text
새 결제수단 등록이 완료되면 미결제된 {상품명} 갱신금액 {금액}원이 즉시 결제됩니다. 결제가 완료되면 구독이 정상 상태로 복구됩니다.
```

Past-due confirm label is `변경하고 {금액}원 결제`; active confirm label is `결제수단 변경`. No checkbox is added.

- [ ] **Step 6: redirect와 errors를 구현한다**

After dialog confirmation, call `startPaymentMethodChange` and use the existing `BrowserNavigationService.assign(response.checkoutUrl)`. On 409, show `결제 상태가 변경되었습니다. 화면을 새로고침한 뒤 다시 확인해 주세요.` Other failures use `결제수단 변경을 시작하지 못했습니다.`.

- [ ] **Step 7: template와 SCSS를 구현한다**

Place the payment method card inside the existing subscription section, below subscription dates and above action buttons. Reuse `.btn`, `.muted`, card radius, border, and spacing variables. Preserve the separate `결제 다시 시도` action when `past_due`.

- [ ] **Step 8: focused tests와 build를 실행한다**

Run:

```bash
npm test -- --watch=false --browsers=ChromeHeadless --include=src/app/features/portal/dashboard/dashboard.component.spec.ts
npm run build
```

Expected: PASS.

- [ ] **Step 9: dashboard UI를 커밋한다**

```bash
git add src/app/features/portal/dashboard
git commit -m "feat: manage payment method from dashboard"
```

---

### Task 11: Authenticated Payment Method Result Page

**Files:**
- Create: `clipper_web_client/src/app/features/portal/payment-method-result/payment-method-result.component.ts`
- Create: `clipper_web_client/src/app/features/portal/payment-method-result/payment-method-result.component.html`
- Create: `clipper_web_client/src/app/features/portal/payment-method-result/payment-method-result.component.scss`
- Create: `clipper_web_client/src/app/features/portal/payment-method-result/payment-method-result.component.spec.ts`
- Modify: `clipper_web_client/src/app/features/portal/portal.routes.ts`
- Modify: `clipper_web_client/src/app/features/portal/portal.routes.spec.ts`

**Interfaces:**
- Consumes: Task 9 get/reconcile/cancel APIs.
- Produces: `/app/payment-method/result` and `/app/payment-method/cancel` authenticated routes.

- [ ] **Step 1: result component tests를 작성한다**

Use `fakeAsync` and `tick` to cover:

```ts
it('change query가 없으면 잘못된 요청을 표시하고 API를 호출하지 않는다');
it('성공 route는 checkout_ready 동안 각 poll마다 reconcile을 호출한다');
it('2초 간격으로 최대 15회만 reconcile 상태를 확인한다');
it('swapped and not_required면 변경 완료를 표시하고 polling을 멈춘다');
it('swapped and succeeded면 결제수단 변경과 구독 복구 완료를 표시한다');
it('swapped and failed면 새 결제수단은 등록됐지만 결제 실패임을 표시한다');
it('canceled/expired/failed면 현재 결제수단 유지 문구를 표시한다');
it('cancel route는 cancel API를 한 번 호출한 뒤 상태를 표시한다');
it('component destroy 시 timer subscription을 해제한다');
```

- [ ] **Step 2: route tests를 추가한다**

Assert both lazy routes exist under `PORTAL_ROUTES`:

```ts
{ path: 'payment-method/result', data: { canceled: false }, ... }
{ path: 'payment-method/cancel', data: { canceled: true }, ... }
```

Because they are portal routes, the existing parent auth guard remains effective.

- [ ] **Step 3: tests를 실행해 실패를 확인한다**

Run:

```bash
npm test -- --watch=false --browsers=ChromeHeadless --include=src/app/features/portal/payment-method-result/payment-method-result.component.spec.ts --include=src/app/features/portal/portal.routes.spec.ts
```

Expected: FAIL because component/routes do not exist.

- [ ] **Step 4: finite polling state machine을 구현한다**

Use RxJS `timer(0, 2000).pipe(take(15), switchMap(...), takeUntilDestroyed())`.

- normal result route calls `reconcilePaymentMethodChange(changeId)` on each tick while the preceding response is `created|checkout_ready|activated`; each server call performs at most one provider status lookup and terminal responses perform none;
- cancel route calls `cancelPaymentMethodChange(changeId)` once, then uses `getPaymentMethodChange(changeId)` only if a later refresh is required.

Stop early for `swapped|canceled|expired|failed`. The 15-tick cap therefore also caps provider reconciliation calls at 15 and never creates a 30-minute polling loop.

- [ ] **Step 5: terminal copy와 actions를 구현한다**

- `swapped/not_required`: `결제수단이 변경되었습니다. 다음 결제부터 새 결제수단이 사용됩니다.`
- `swapped/succeeded`: `결제수단 변경과 미결제 갱신 결제가 완료되었습니다.`
- `swapped/failed`: `새 결제수단은 등록되었지만 미결제 금액 결제에 실패했습니다. 마이페이지에서 상태를 확인해 주세요.`
- `canceled|expired|failed`: `결제수단이 변경되지 않았습니다. 기존 결제수단은 유지됩니다.`
- 30초 미확정: `등록 결과를 확인 중입니다. 잠시 후 다시 확인해 주세요.` and button `다시 확인`.

Provide `마이페이지로 돌아가기` linking to `/app` for every terminal state.

- [ ] **Step 6: focused tests와 build를 실행한다**

Run:

```bash
npm test -- --watch=false --browsers=ChromeHeadless --include=src/app/features/portal/payment-method-result/payment-method-result.component.spec.ts --include=src/app/features/portal/portal.routes.spec.ts
npm run build
```

Expected: PASS.

- [ ] **Step 7: result UI를 커밋한다**

```bash
git add src/app/features/portal/payment-method-result src/app/features/portal/portal.routes.ts src/app/features/portal/portal.routes.spec.ts
git commit -m "feat: show payment method change results"
```

---

### Task 12: Cross-Repository Verification and Documentation Alignment

**Files:**
- Modify only if behavior differs: `.codex/design/2026-08-13-subscription-payment-method-management-design.md`
- Modify: `.codex/plans/2026-08-13-subscription-payment-method-management.md` checkboxes during execution.

**Interfaces:**
- Consumes: all prior tasks.
- Produces: verified build/test evidence and a deployable feature branch state.

- [ ] **Step 1: API payment suite를 실행한다**

Run:

```bash
cd /Users/jina/project/adlight/.worktrees/clipper_web_api-access-credit
nvm use 22
npm test -- --runInBand src/modules/payments src/core/database/admin.datasource.spec.ts src/core/database/migrations/admin/1787200000000-CreateSubscriptionPaymentMethodChanges.spec.ts
```

Expected: all selected suites PASS, no open handle warning caused by this feature.

- [ ] **Step 2: API full tests와 build를 실행한다**

Run:

```bash
npm test -- --runInBand
npm run build
```

Expected: PASS.

- [ ] **Step 3: web-client tests와 build를 실행한다**

Run:

```bash
cd /Users/jina/project/adlight/.worktrees/clipper_web_client-access-credit
nvm use 22
npm test -- --watch=false --browsers=ChromeHeadless
npm run build
```

Expected: PASS under Angular 19 and Node 22.

- [ ] **Step 4: 민감정보와 범위 drift를 정적 확인한다**

Run:

```bash
cd /Users/jina/project/adlight
rg -n "billingKey|providerDisplayId|providerUserId" .worktrees/clipper_web_client-access-credit/src/app
rg -n "cardNumber|accountNumber|cardBin" .worktrees/clipper_web_api-access-credit/src/modules/payments .worktrees/clipper_web_client-access-credit/src/app
git -C .worktrees/clipper_web_api-access-credit diff --name-only origin/feat/access-credit-system-replacement...HEAD
git -C .worktrees/clipper_web_client-access-credit diff --name-only origin/feat/access-credit-system-replacement...HEAD
```

Expected: no client model/template contains billing/provider identifiers; no full card/account/BIN field was added; changed files stay within API/client scope.

- [ ] **Step 5: migration up/down을 disposable local DB에서 확인한다**

Use the project migration commands against the existing local development database only after confirming its configured DB name is not stage/production:

```bash
cd /Users/jina/project/adlight/.worktrees/clipper_web_api-access-credit
rg -n "CLIPPER_ADMIN_DATABASE_NAME" .env* ../clipper_infra/env 2>/dev/null
npm run db:migrate:admin
```

Expected: the new migration applies once and a second run reports no pending migration. Do not run a destructive rollback against a shared database; the SQL rollback is covered by the migration spec.

- [ ] **Step 6: development-server manual scenarios를 검증한다**

Verify these six scenarios and record observed order/change/subscription statuses without recording secrets:

1. `active` card display refresh and card ending.
2. `active` card change with no immediate payment order.
3. `past_due` exact product/amount dialog and immediate retry after new registration.
4. registration cancel leaves original key/current method unchanged.
5. 30-minute expiry or test-clock equivalent unblocks scheduled renewal.
6. old-key removal failure leaves new method current and scheduler retries cleanup.

- [ ] **Step 7: code review 전에 두 worktree가 clean/expected인지 확인한다**

Run:

```bash
git -C /Users/jina/project/adlight/.worktrees/clipper_web_api-access-credit status --short --branch
git -C /Users/jina/project/adlight/.worktrees/clipper_web_client-access-credit status --short --branch
git -C /Users/jina/project/adlight/.codex status --short --branch
```

Expected: API/client are on `feat/access-credit-system-replacement`; `.codex` is on `main`; only intended uncommitted checkbox/document updates remain.

- [ ] **Step 8: 구현과 달라진 설계 세부가 있으면 `.codex/main`에만 반영하고 커밋한다**

```bash
cd /Users/jina/project/adlight/.codex
git add design/2026-08-13-subscription-payment-method-management-design.md plans/2026-08-13-subscription-payment-method-management.md
git commit -m "docs: align payment method implementation"
```

If no design difference exists, commit only the completed checkbox updates or leave them uncommitted until the feature review is complete.

---

## Acceptance Checklist

- [ ] 마이페이지는 카드사·끝 4자리·카드 종류 또는 토스머니 은행명만 표시한다.
- [ ] 토스 조회 장애가 마이페이지 전체를 실패시키지 않는다.
- [ ] `active` 변경은 즉시 결제하지 않는다.
- [ ] `past_due` 변경은 상품명·금액·즉시 재결제 고지 후에만 시작된다.
- [ ] 사용자 표시 금액과 서버 주문이 달라지면 변경 등록을 거부한다.
- [ ] 후보 키 활성화·identity 검증 전에는 기존 키가 유지된다.
- [ ] 교체 transaction은 새 키/current metadata와 old-key cleanup record를 원자적으로 기록한다.
- [ ] 결과 polling은 2초 × 최대 15회이며 30분 polling이 없다.
- [ ] 30분 만료와 늦은 callback이 현재 키를 덮어쓰지 않는다.
- [ ] 진행 중 변경은 새 charge claim만 막고 기존 pending/paid 결과 복구는 막지 않는다.
- [ ] 기존 직접 재시도 버튼이 유지되고 manual failure가 자동 retry cursor를 소모하지 않는다.
- [ ] 이전 `displayId`의 늦은 `REMOVED` callback이 현재 구독을 취소하지 않는다.
- [ ] 후보·이전 키 삭제 실패는 bounded scheduler로 복구된다.
- [ ] API full test/build와 Angular 19 client full test/build가 Node 22에서 통과한다.
