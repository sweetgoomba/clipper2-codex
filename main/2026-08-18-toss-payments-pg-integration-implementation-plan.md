# Toss Payments PG Full Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 로그인한 실제 사용자가 토스페이먼츠 PG V2로 Basic·Pro 월간/연간 카드 구독과 카드·카카오페이·네이버페이·토스페이·계좌이체·가상계좌 추가 크레딧 결제를 안전하게 완료하고, 중복·장애·웹훅 재전송 이후에도 결제·구독·이용 자격·크레딧 상태가 한 번의 결과로 수렴하도록 구현한다.

**Architecture:** 기존 access-credit 도메인의 지급, 갱신, 재시도, 작업 실패 크레딧 반환 경계를 유지하고 토스페이 직접 연동 provider만 PG V2 provider로 교체한다. OpenAPI를 API/고객 웹/관리자 웹의 정본으로 삼고, 결제 주문·구독 계약 스냅샷·빌링 인증 attempt·웹훅 inbox를 짧은 DB 트랜잭션과 고정 멱등키로 연결한다. 브라우저는 서버가 발급한 checkout session의 Client Key와 주문 스냅샷만 사용하며, 모든 공급자 결과는 API가 저장 주문 및 토스 조회 결과와 대조한다.

**Tech Stack:** Node.js 22, NestJS 11, TypeScript 5.7, TypeORM/PostgreSQL 16, Jest 30, Angular 19, Angular Material, Toss Payments SDK V2 (`@tosspayments/tosspayments-sdk`), Docker Compose, native `node:test`.

**Spec:** `.codex/main/2026-08-18-toss-payments-pg-integration-design.md` and `.codex/main/2026-08-18-toss-payments-pg-integration-session-handoff.md`

## Global Constraints

- API와 고객 웹의 모든 설치·테스트·빌드는 Node.js 22에서 실행한다.
- 구현은 `feature/toss-payments-pg-integration` 전용 격리 worktree에서만 수행한다.
- 원본 `feat/access-credit-system-replacement`, 각 저장소 `dev`, 원본 worktree, 현재 `dev.clipperstudio.ai` 익명 PG review 배포는 수정·rebase·reset·삭제하지 않는다.
- 각 저장소의 access-credit 보존 HEAD는 이미 같은 이름의 원격 브랜치에 정확히 push되었으며 다시 force-push하지 않는다.
- feature 브랜치는 로컬 구현·검증만 하고 원격 push, PR, 배포, `dev` 병합을 하지 않는다.
- 승인된 설계를 구현하며 추가 브레인스토밍이나 review mode 호환 계층을 만들지 않는다.
- 월간·연간 구독은 카드 빌링만 지원한다.
- 추가 크레딧은 카드, 카카오페이, 네이버페이, 토스페이, 계좌이체, 가상계좌만 지원한다.
- 모든 표시·청구 금액은 부가세 포함 KRW이고 토스 POST payload의 `taxFreeAmount`는 `0`이다.
- 토스 API 버전은 개발자센터 `2024-06-01` 계약과 그 응답 fixture를 사용한다.
- 일반 결제와 빌링의 Client Key·Secret Key를 분리하고 Secret Key, 평문 billingKey, authKey, 가상계좌 secret을 응답·로그·감사 payload에 노출하지 않는다.
- `customerKey`는 이메일·전화번호·사용자 ID가 아닌 무작위 UUID 계열 값이며 길이는 50자 이하이다.
- 토스의 모든 POST 요청은 논리 작업 생성 시 저장한 고정 UUID v4 `Idempotency-Key`를 사용한다. 15일 초과 미확정 작업은 새 청구를 만들지 않고 `reconciliation_required`로 보낸다.
- 공급자 네트워크 호출 동안 DB 트랜잭션을 열어두지 않는다.
- 돈 환불 요청·승인·취소 API·자격 회수·크레딧 회수 기능은 만들지 않는다.
- 외부 `CANCELED`와 `PARTIAL_CANCELED`는 기록·운영 경고만 만들고 이용 자격과 크레딧을 자동 변경하지 않는다.
- 작업 실패로 이미 차감한 서비스 내부 크레딧을 원래 grant로 반환·복구하는 기존 기능과 용어는 유지한다.
- 테스트는 RED 확인 → 최소 GREEN 구현 → 관련 회귀 테스트 순서로 실행하고, 각 기능 경계마다 로컬 커밋한다.
- 수동 테스트키 실행에 실제 키나 MID 설정이 없으면 추측값을 넣지 않고 자동 검증 결과와 미실행 체크리스트를 분리해 보고한다.

## Worktree Map

| Repository | Feature worktree |
| --- | --- |
| API | `/Users/jina/project/adlight/.worktrees/clipper_web_api-toss-payments-pg-integration` |
| Customer web | `/Users/jina/project/adlight/.worktrees/clipper_web_client-toss-payments-pg-integration` |
| Admin web | `/Users/jina/project/adlight/.worktrees/clipper_web_admin-toss-payments-pg-integration` |
| Infra | `/Users/jina/project/adlight/.worktrees/clipper_infra-toss-payments-pg-integration` |
| Desktop Angular | `/Users/jina/project/adlight/.worktrees/clipper_angular-toss-payments-pg-integration` |
| Desktop Electron | `/Users/jina/project/adlight/.worktrees/clipper_electron-toss-payments-pg-integration` |
| Desktop local API | `/Users/jina/project/adlight/.worktrees/clipper_nestjs-toss-payments-pg-integration` |

## File Responsibility Map

- `clipper_web_api/docs/api/openapi.yaml`: 최종 URL, 인증 경계, request/response schema의 정본.
- `clipper_web_api/src/modules/payments/domain/payment.model.ts`: 주문 상태, 목적, 안전한 공급자 결제 스냅샷.
- `clipper_web_api/src/modules/payments/domain/subscription.model.ts`: 현재 계약과 예약 변경 스냅샷, billing/benefit anchor.
- `clipper_web_api/src/modules/payments/domain/billing-auth-attempt.model.ts`: 최초 가입·결제수단 변경의 복구 가능한 카드 인증 상태.
- `clipper_web_api/src/modules/payments/domain/payment-webhook.model.ts`: 정규화된 webhook inbox와 운영 경고 상태.
- `clipper_web_api/src/modules/payments/domain/toss-payments.provider.ts`: PG V2 외부 호출의 유일한 도메인 포트; 결제 취소 메서드는 두지 않는다.
- `clipper_web_api/src/modules/payments/infrastructure/http-toss-payments.provider.ts`: 고정 API origin, 키 세트 분리, 멱등 헤더, 응답 정규화.
- `clipper_web_api/src/modules/payments/application/billing-auth.service.ts`: authKey 선저장, 빌링키 발급·회수·교체 orchestration.
- `clipper_web_api/src/modules/payments/application/payment-reconciliation.service.ts`: timeout/409/웹훅 뒤 토스 재조회와 로컬 상태 수렴.
- `clipper_web_api/src/modules/payments/application/payment-webhook.service.ts`: 세 webhook의 inbox claim, 검증, 처리.
- `clipper_web_api/src/modules/payments/application/payment-fulfillment.service.ts`: 결제 성공과 상품 지급을 분리하고 한 번만 지급.
- `clipper_web_client/src/app/core/payments/toss-payments-sdk.service.ts`: 브라우저의 SDK V2 호출을 감싼 얇은 adapter.
- `clipper_web_client/src/app/features/portal/payment-checkout/*`: 로그인 사용자 checkout session 렌더링.
- `clipper_web_client/src/app/features/portal/payment-history/*`: 본인 결제내역·영수증·가상계좌 정보 표시.
- `clipper_web_admin/src/app/features/portal/payment-operations/*`: 주문·webhook·fulfillment·reconciliation 운영 조회; 환불 동작은 제공하지 않는다.
- `clipper_infra/env/stack.*.env.example`: 일곱 개 PG 환경변수 계약.

---

### Task 1: Complete the isolated `origin/dev` merges without changing protected worktrees

**Files:**
- Modify: `clipper_web_api/.env.example`
- Modify: `clipper_web_api/docs/api/openapi.yaml`
- Modify: `clipper_web_api/src/core/database/admin.datasource.ts`
- Modify: `clipper_web_api/src/core/database/admin.datasource.spec.ts`
- Modify: all currently unmerged files under `clipper_web_api/src/modules/payments/`
- Modify: `clipper_web_client/src/app/core/api/models.ts`
- Modify: `clipper_web_client/src/app/core/api/payments-api.service.ts`
- Modify: `clipper_web_client/src/app/features/public/payment-result/*`
- Modify: `clipper_web_client/src/app/features/public/pricing/*`
- Modify: `clipper_infra/env/stack.dev.env.example`
- Verify only: the four already-clean feature worktrees for admin, desktop Angular, Electron, and desktop local API

**Interfaces:**
- Consumes: the preserved access-credit HEADs and fetched `origin/dev` commits listed in the session handoff.
- Produces: seven isolated feature worktrees with no unmerged paths; API keeps the compiling access-credit behavior and retains the PG V2 provider as the tested replacement boundary for Tasks 8–19; customer web keeps authenticated pricing/topup/dashboard flows and retains the SDK wrapper for Tasks 20–21; infra keeps deployment structure but does not run it.

- [ ] **Step 1: Capture the current merge-conflict RED state**

```bash
git diff --name-only --diff-filter=U
```

Run in API, customer web, and infra feature worktrees. Expected: API and customer web list the previously recorded `UU`/`UD` paths, infra lists only `env/stack.dev.env.example`; the four other feature worktrees return no path.

- [ ] **Step 2: Resolve API conflicts to one provider boundary**

Use the access-credit versions of subscription, renewal, payment-method, fulfillment, repository, controller, and ownership logic as the compiling base. Retain the `origin/dev` PG V2 files under the names below without routing live access-credit services through them before their RED tests in Tasks 8–16. `payments.module.ts` must contain one `controllers` property and must register each provider required by the temporarily coexisting access-credit and review code exactly once:

```ts
import { TossPaymentsProvider } from './domain/toss-payments.provider.js';
import { HttpTossPaymentsProvider } from './infrastructure/http-toss-payments.provider.js';

{ provide: TossPaymentsProvider, useClass: HttpTossPaymentsProvider }
```

Keep `MigrateReviewPaymentsToTossPaymentsPg1786560000000` registered between `178650...` and `178660...`. Keep the access-credit OpenAPI sections and the PG V2 schemas temporarily; Task 2 removes review URLs and freezes the final contract.

- [ ] **Step 3: Resolve customer web and infra conflicts**

Keep the access-credit authenticated models/services/screens, retain `TossPaymentsSdkService`, and represent a checkout result with the final discriminant names so later tasks do not add a second union:

```ts
export type PaymentFlow = 'normal_payment' | 'billing_auth';
export type PaymentResultState =
  | 'pending'
  | 'waiting_for_deposit'
  | 'paid'
  | 'failed'
  | 'reconciliation_required';
```

In infra, keep compose/runbook changes but use the seven final environment variable names from Global Constraints. Do not retain `TOSS_PAYMENTS_REVIEW_MODE` in the resolved env example.

- [ ] **Step 4: Verify the merge index is complete and the baseline is syntactically clean**

```bash
git diff --name-only --diff-filter=U
git diff --check
```

Expected: both commands produce no conflict/error output in API, customer web, and infra. Then run Node 22 `npm test -- --runInBand` and `npm run build` in API, and `npm test -- --watch=false` plus `npm run build` in customer web. All commands must PASS before the merge commits; a failure is debugged as a merge-resolution defect before proceeding.

- [ ] **Step 5: Finish the three merge commits locally**

```bash
git add .
git commit --no-edit
```

Expected: one local merge commit in each of API, customer web, and infra. Do not push any feature branch.

### Task 2: Freeze the final OpenAPI contract before application code

**Files:**
- Modify: `clipper_web_api/docs/api/openapi.yaml`
- Create: `clipper_web_api/src/modules/payments/presentation/payments-openapi-contract.spec.ts`

**Interfaces:**
- Consumes: existing JWT security scheme, catalog schemas, access-credit schemas, and admin role guards.
- Produces: exact endpoint and DTO names consumed by Tasks 9–22.

- [ ] **Step 1: Write the failing contract test**

```ts
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

const source = readFileSync(join(process.cwd(), 'docs/api/openapi.yaml'), 'utf8');

describe('Toss Payments full PG OpenAPI', () => {
  it.each([
    '/payments/subscriptions/checkout:',
    '/payments/topups/checkout:',
    '/payments/orders/{receiptToken}/checkout:',
    '/payments/orders/{receiptToken}:',
    '/payments/orders/{receiptToken}/reconcile:',
    '/payments/history:',
    '/subscriptions/current:',
    '/subscriptions/current/cancel:',
    '/subscriptions/current/resume:',
    '/subscriptions/current/retry:',
    '/subscriptions/current/plan-change:',
    '/subscriptions/current/payment-method/changes:',
    '/payments/tosspayments/normal/success:',
    '/payments/tosspayments/billing/success:',
    '/payments/tosspayments/fail:',
    '/payments/tosspayments/webhook:',
    '/admin/payments/orders:',
    '/admin/payments/webhooks:',
    '/admin/payments/reconciliation:',
  ])('contains %s', path => expect(source).toContain(path));

  it('contains no anonymous review payment contract or money-refund operation', () => {
    expect(source).not.toMatch(/payments\/review|review_user_id|TOSS_PAYMENTS_REVIEW_MODE/);
    expect(source).not.toMatch(/operationId:.*(?:refund|cancelPayment)/i);
  });
});
```

- [ ] **Step 2: Run the test to verify RED**

Run: `npm test -- --runInBand src/modules/payments/presentation/payments-openapi-contract.spec.ts`

Expected: FAIL because final history, resume, plan-change, webhook, and admin operations paths are absent and review paths still exist.

- [ ] **Step 3: Define exact request and response schemas**

Use these discriminants in `openapi.yaml`:

```yaml
PaymentPurpose:
  type: string
  enum: [subscription_initial, subscription_renewal, subscription_upgrade, credit_topup]
PaymentStatus:
  type: string
  enum: [created, checkout_ready, authorization_pending, payment_pending, waiting_for_deposit, paid, canceled, expired, failed, reconciliation_required]
CheckoutSession:
  type: object
  required: [flow, receiptToken, clientKey, customerKey, orderId, orderName, amount, successUrl, failUrl]
  properties:
    flow: { type: string, enum: [normal_payment, billing_auth] }
    receiptToken: { type: string }
    clientKey: { type: string }
    customerKey: { type: string }
    orderId: { type: string }
    orderName: { type: string }
    amount:
      type: object
      required: [currency, value]
      properties:
        currency: { type: string, enum: [KRW] }
        value: { type: integer, minimum: 1 }
    successUrl: { type: string, format: uri }
    failUrl: { type: string, format: uri }
    virtualAccountDueDate: { type: string, format: date-time, nullable: true }
```

`POST /payments/subscriptions/checkout` accepts only `billingProductCode`; `POST /payments/topups/checkout` accepts only `creditProductCode`; `POST /subscriptions/current/plan-change` accepts only `billingProductCode`. All three reread active catalog rows server-side. Customer order/session/history/subscription operations use bearer JWT. Redirect and webhook operations are public capability endpoints. Admin list/reconcile operations use the existing operator guard. `DELETE /subscriptions/current/plan-change` cancels one scheduled change.

- [ ] **Step 4: Run the contract test and API schema-adjacent tests**

Run: `npm test -- --runInBand src/modules/payments/presentation/payments-openapi-contract.spec.ts src/modules/catalog/presentation/catalog.controller.spec.ts`

Expected: PASS with no `review` purpose/schema/path and no payment cancellation/refund operation.

- [ ] **Step 5: Commit**

```bash
git add docs/api/openapi.yaml src/modules/payments/presentation/payments-openapi-contract.spec.ts
git commit -m "docs(payments): define full PG API contract"
```

### Task 3: Add one forward-only PG schema migration after all existing migrations

**Files:**
- Create: `clipper_web_api/src/core/database/migrations/admin/1787300000000-CreateTossPaymentsPgIntegration.ts`
- Create: `clipper_web_api/src/core/database/migrations/admin/1787300000000-CreateTossPaymentsPgIntegration.spec.ts`
- Modify: `clipper_web_api/src/core/database/admin.datasource.ts`
- Modify: `clipper_web_api/src/core/database/admin.datasource.spec.ts`

**Interfaces:**
- Consumes: schema after `1787200000000-CreateSubscriptionPaymentMethodChanges` and the destructive review-data cleanup already isolated in `1786560000000`.
- Produces: final payment orders, subscription contract snapshots, generalized billing auth attempts, and webhook inbox. No past migration is edited.

- [ ] **Step 1: Write migration-shape tests**

```ts
it('removes review purpose and creates recoverable PG state', async () => {
  await migration.up(queryRunner);
  const sql = queryRunner.query.mock.calls.map(([value]) => value).join('\n');
  expect(sql).toContain("'authorization_pending'");
  expect(sql).toContain("'waiting_for_deposit'");
  expect(sql).toContain("'reconciliation_required'");
  expect(sql).toContain('billing_key_fingerprint');
  expect(sql).toContain('billing_auth_attempts');
  expect(sql).toContain('payment_webhook_inbox');
  expect(sql).not.toContain("purpose IN ('review')");
});
```

Also assert that `admin.datasource` orders `178730...` after `178720...`, and that the migration never issues `DELETE FROM subscriptions`, `DELETE FROM credit_grants`, or `DELETE FROM user_access_grants`.

- [ ] **Step 2: Run the migration tests to verify RED**

Run: `npm test -- --runInBand src/core/database/migrations/admin/1787300000000-CreateTossPaymentsPgIntegration.spec.ts src/core/database/admin.datasource.spec.ts`

Expected: FAIL because the migration class is absent.

- [ ] **Step 3: Implement the forward migration**

The `up()` SQL performs these exact transformations:

```sql
ALTER TABLE payment_orders DROP CONSTRAINT IF EXISTS CK_payment_orders_purpose;
ALTER TABLE payment_orders DROP CONSTRAINT IF EXISTS payment_orders_status_check;
ALTER TABLE payment_orders
  ADD COLUMN provider_status varchar(40),
  ADD COLUMN key_set varchar(20) NOT NULL DEFAULT 'widget',
  ADD COLUMN easy_pay_provider varchar(40),
  ADD COLUMN receipt_url text,
  ADD COLUMN virtual_account_bank_code varchar(20),
  ADD COLUMN virtual_account_bank_name varchar(80),
  ADD COLUMN virtual_account_number_masked varchar(80),
  ADD COLUMN virtual_account_holder_name varchar(80),
  ADD COLUMN virtual_account_due_at timestamptz,
  ADD COLUMN virtual_account_secret_enc text,
  ADD COLUMN reconciliation_reason varchar(120),
  ADD COLUMN reconciled_at timestamptz,
  ADD COLUMN external_cancel_status varchar(30),
  ADD COLUMN external_cancel_detected_at timestamptz;
```

Recreate status and purpose checks with only the enums from Task 2. Drop obsolete `plan_id`, `plan_name`, `months`, `token_allowance`, `billing_auth_key_enc`, and order-level `billing_key_enc` after copying no data because `178656...` already removed review orders. Keep order `customer_key` as the checkout snapshot.

Extend `subscriptions` with non-null `customer_key`, `billing_key_fingerprint`, product/price/interval/monthly-credit snapshots, `billing_anchor_at`, `benefit_anchor_at`, and nullable scheduled product snapshots plus `scheduled_change_effective_at`. Populate existing access-credit subscriptions from their current catalog rows before setting non-null constraints. Rename `subscription_payment_method_changes` to `billing_auth_attempts`; add `purpose`, encrypted `auth_key_enc`, fixed `issue_idempotency_key`, `customer_key`, candidate/current/previous key fingerprints, `authorization_pending` and `reconciliation_required` states, then migrate existing rows to purpose `payment_method_change`.

Create `payment_webhook_inbox` with a unique lowercase 64-hex SHA-256 `dedupe_key`, safe identifiers, normalized JSON restricted to string-valued `createdAt|status|reason|depositStatus`, `received|processing|processed|retryable_failed|manual_review` status, retry count/timestamps, and bounded error code. Add a bounded encrypted-only `deposit_secret_enc` for delayed `DEPOSIT_CALLBACK` verification and enforce status-aware erasure plus mutually consistent payment/deposit/billing-deletion event shapes. Create indexes for open auth-attempt recovery, webhook retry claim, stale processing recovery, admin `(received_at DESC,id DESC)` cursor listing, order history `(user_id, created_at, id)`, payment-key lookup, and billing-key fingerprint lookup.

The `down()` reverses only this migration's schema operations and restores the immediately preceding constraints; it does not fabricate deleted review rows.

- [ ] **Step 4: Run migration tests**

Run: `npm test -- --runInBand src/core/database/migrations/admin/1787300000000-CreateTossPaymentsPgIntegration.spec.ts src/core/database/admin.datasource.spec.ts`

Expected: PASS, including migration ordering and non-destructive-data assertions.

- [ ] **Step 5: Commit**

```bash
git add src/core/database/migrations/admin/1787300000000-CreateTossPaymentsPgIntegration.ts src/core/database/migrations/admin/1787300000000-CreateTossPaymentsPgIntegration.spec.ts src/core/database/admin.datasource.ts src/core/database/admin.datasource.spec.ts
git commit -m "feat(payments): add full PG persistence schema"
```

### Task 4: Seed exact products and calculate monthly benefit anniversaries

**Files:**
- Create: `clipper_web_api/src/core/database/migrations/admin/1787400000000-SeedTossPaymentsCatalog.ts`
- Create: `clipper_web_api/src/core/database/migrations/admin/1787400000000-SeedTossPaymentsCatalog.spec.ts`
- Modify: `clipper_web_api/src/core/database/admin.datasource.ts`
- Modify: `clipper_web_api/src/core/database/admin.datasource.spec.ts`
- Modify: `clipper_web_api/src/modules/access/domain/month-anniversary.ts`
- Modify: `clipper_web_api/src/modules/access/domain/month-anniversary.spec.ts`
- Modify: `clipper_web_api/src/modules/access/application/monthly-credit-grant.service.ts`
- Modify: `clipper_web_api/src/modules/access/application/monthly-credit-grant.service.spec.ts`

**Interfaces:**
- Consumes: catalog tables and existing idempotent monthly grant mechanism.
- Produces: product codes `basic_monthly`, `basic_yearly`, `pro_monthly`, `pro_yearly`, `credits_100`, `credits_500`, `credits_1000`; `monthAnniversary(anchor, offsetMonths)` and `nextMonthAnniversary(anchor, current)`.

- [ ] **Step 1: Write failing seed and calendar tests**

```ts
expect(monthAnniversary(new Date('2024-01-31T09:30:00.000Z'), 1))
  .toEqual(new Date('2024-02-29T09:30:00.000Z'));
expect(monthAnniversary(new Date('2024-01-31T09:30:00.000Z'), 2))
  .toEqual(new Date('2024-03-31T09:30:00.000Z'));
expect(nextMonthAnniversary(
  new Date('2024-01-31T09:30:00.000Z'),
  new Date('2024-02-29T09:30:00.000Z'),
)).toEqual(new Date('2024-03-31T09:30:00.000Z'));
```

Migration tests assert all seven codes, prices `19900/190900/39900/382900/5900/27900/49900`, credits `400/1000/100/500/1000`, 365-day topup validity, monthly/12-month intervals, Basic's five plugin keys, and Pro's six plugin keys.

- [ ] **Step 2: Run tests to verify RED**

Run: `npm test -- --runInBand src/core/database/migrations/admin/1787400000000-SeedTossPaymentsCatalog.spec.ts src/modules/access/domain/month-anniversary.spec.ts src/modules/access/application/monthly-credit-grant.service.spec.ts`

Expected: FAIL because the seed and offset-based anniversary function do not exist and the grant expiry still follows a fixed validity path.

- [ ] **Step 3: Implement deterministic catalog seed and calendar math**

Seed by code with `INSERT ... ON CONFLICT (code) DO UPDATE` so a fresh DB receives the approved initial values and deployment reruns are idempotent. Replace the tier entitlements for `basic` and `pro` with these exact arrays:

```ts
export const BASIC_PLUGIN_KEYS = [
  'shortform_url',
  'shortform_paste',
  'shortform_prompt',
  'dialog_highlight',
  'dance_highlight',
] as const;

export const PRO_PLUGIN_KEYS = [...BASIC_PLUGIN_KEYS, 'variation'] as const;
```

Implement anniversary calculation from the immutable original anchor rather than chaining shortened months:

```ts
export function monthAnniversary(anchor: Date, offsetMonths: number): Date {
  const absoluteMonth = anchor.getUTCMonth() + offsetMonths;
  const year = anchor.getUTCFullYear() + Math.floor(absoluteMonth / 12);
  const month = ((absoluteMonth % 12) + 12) % 12;
  const lastDay = new Date(Date.UTC(year, month + 1, 0)).getUTCDate();
  return new Date(Date.UTC(
    year,
    month,
    Math.min(anchor.getUTCDate(), lastDay),
    anchor.getUTCHours(),
    anchor.getUTCMinutes(),
    anchor.getUTCSeconds(),
    anchor.getUTCMilliseconds(),
  ));
}
```

Monthly subscription/admin grants expire at the next benefit anniversary. Annual subscriptions enqueue twelve monthly benefits instead of a 12× lump sum. An expired original grant may receive a refund ledger entry but remains unspendable.

- [ ] **Step 4: Run focused access/catalog tests**

Run: `npm test -- --runInBand src/core/database/migrations/admin/1787400000000-SeedTossPaymentsCatalog.spec.ts src/modules/access/domain/month-anniversary.spec.ts src/modules/access/application/monthly-credit-grant.service.spec.ts src/modules/operations/application/operations.service.spec.ts`

Expected: PASS for month-end, leap-year, annual twelve-grant, entitlement re-read, and expired-grant refund behavior.

- [ ] **Step 5: Commit**

```bash
git add src/core/database/migrations/admin/1787400000000-SeedTossPaymentsCatalog.ts src/core/database/migrations/admin/1787400000000-SeedTossPaymentsCatalog.spec.ts src/core/database/admin.datasource.ts src/core/database/admin.datasource.spec.ts src/modules/access/domain/month-anniversary.ts src/modules/access/domain/month-anniversary.spec.ts src/modules/access/application/monthly-credit-grant.service.ts src/modules/access/application/monthly-credit-grant.service.spec.ts
git commit -m "feat(catalog): seed PG products and exact benefit anchors"
```

### Task 5: Replace review payment types with final order persistence

**Files:**
- Modify: `clipper_web_api/src/modules/payments/domain/payment.model.ts`
- Modify: `clipper_web_api/src/modules/payments/domain/payment-orders.repository.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/payment-order.entity.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/typeorm-payment-orders.repository.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/typeorm-payment-orders.repository.spec.ts`
- Modify: `clipper_web_api/docs/api/openapi.yaml`
- Modify: `clipper_web_api/src/modules/payments/presentation/payments-openapi-contract.spec.ts`

**Interfaces:**
- Consumes: Task 3 columns and Task 2 enums.
- Produces: `PaymentOrder`, `NewPaymentOrder`, `ProviderPaymentSnapshot`, owner-scoped history, state transitions, and idempotent fulfillment claims.

- [ ] **Step 1: Write failing repository tests**

```ts
it('maps a virtual-account order without exposing its secret', async () => {
  const order = await repository.findByOrderNo('ord_pg_1');
  expect(order).toMatchObject({
    status: 'waiting_for_deposit',
    providerStatus: 'WAITING_FOR_DEPOSIT',
    virtualAccount: {
      bankCode: '088',
      bankName: '신한',
      accountNumberMasked: '110-*****-6789',
      holderName: '클리퍼스튜디오',
    },
  });
  expect(JSON.stringify(order)).not.toContain('deposit-secret');
});
```

Add tests for `findByPaymentKey`, owner-filtered cursor history, `tryBeginConfirmation`, `markWaitingForDeposit`, `tryMarkPaid`, `tryBeginFulfillment`, external cancel observation, and `reconciliation_required` without creating a replacement order.

- [ ] **Step 2: Run repository tests to verify RED**

Run: `npm test -- --runInBand src/modules/payments/infrastructure/typeorm-payment-orders.repository.spec.ts`

Expected: FAIL on removed review types and missing PG fields/methods.

- [ ] **Step 3: Implement final types and transitions**

```ts
export const PAYMENT_STATUSES = [
  'created', 'checkout_ready', 'authorization_pending', 'payment_pending',
  'waiting_for_deposit', 'paid', 'canceled', 'expired', 'failed',
  'reconciliation_required',
] as const;
export type PaymentStatus = (typeof PAYMENT_STATUSES)[number];

export const PAYMENT_PURPOSES = [
  'subscription_initial', 'subscription_renewal',
  'subscription_upgrade', 'credit_topup',
] as const;
export type PaymentPurpose = (typeof PAYMENT_PURPOSES)[number];

export interface ProviderPaymentSnapshot {
  providerStatus: string;
  paymentKey: string;
  method: string | null;
  easyPayProvider: string | null;
  receiptUrl: string | null;
  lastTransactionKey: string | null;
  paidAmountKrw: number;
  virtualAccount: VirtualAccountSnapshot | null;
}

export interface VirtualAccountSnapshot {
  bankCode: string;
  bankName: string | null;
  accountNumberMasked: string;
  holderName: string | null;
  dueAt: Date;
}
```

Map encrypted values only to repository-internal fields used by services; customer DTO mappers explicitly pick safe fields. All compare-and-set transitions include the allowed prior states in SQL/TypeORM conditions so duplicate callbacks return the already-converged order.

Binding clarification: `tryMarkPaid()` accepts `expired` only after Task 12/13 has re-queried and verified provider `DONE`. This preserves the approved virtual-account rule that a late real deposit overrides local expiry; arbitrary callbacks or local guesses cannot use the exception.

- [ ] **Step 4: Run repository and entity tests**

Run: `npm test -- --runInBand src/modules/payments/infrastructure/typeorm-payment-orders.repository.spec.ts`

Expected: PASS with no exported `ReviewPaymentType`, `ReviewPaymentStatus`, or `review` purpose.

- [ ] **Step 5: Commit**

```bash
git add src/modules/payments/domain/payment.model.ts src/modules/payments/domain/payment-orders.repository.ts src/modules/payments/infrastructure/payment-order.entity.ts src/modules/payments/infrastructure/typeorm-payment-orders.repository.ts src/modules/payments/infrastructure/typeorm-payment-orders.repository.spec.ts
git commit -m "refactor(payments): model final PG order states"
```

### Task 6: Persist subscription contract snapshots and recoverable billing-auth attempts

**Files:**
- Modify: `clipper_web_api/src/modules/payments/domain/subscription.model.ts`
- Modify: `clipper_web_api/src/modules/payments/domain/subscriptions.repository.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/subscription.entity.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/typeorm-subscriptions.repository.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/typeorm-subscriptions.repository.spec.ts`
- Create: `clipper_web_api/src/modules/payments/domain/billing-auth-attempt.model.ts`
- Create: `clipper_web_api/src/modules/payments/domain/billing-auth-attempts.repository.ts`
- Create: `clipper_web_api/src/modules/payments/infrastructure/billing-auth-attempt.entity.ts`
- Create: `clipper_web_api/src/modules/payments/infrastructure/typeorm-billing-auth-attempts.repository.ts`
- Create: `clipper_web_api/src/modules/payments/infrastructure/typeorm-billing-auth-attempts.repository.spec.ts`
- Preserve until Task 19: `clipper_web_api/src/modules/payments/domain/subscription-payment-method-change.model.ts`
- Preserve until Task 19: `clipper_web_api/src/modules/payments/domain/subscription-payment-method-changes.repository.ts`
- Preserve until Task 19: `clipper_web_api/src/modules/payments/infrastructure/subscription-payment-method-change.entity.ts`
- Preserve until Task 19: `clipper_web_api/src/modules/payments/infrastructure/typeorm-subscription-payment-method-changes.repository.ts`
- Preserve until Task 19: `clipper_web_api/src/modules/payments/infrastructure/typeorm-subscription-payment-method-changes.repository.spec.ts`

**Interfaces:**
- Consumes: Task 3 generalized table and Task 4 product values.
- Produces: immutable `SubscriptionContractSnapshot`, replaceable `ScheduledPlanChange`, and `BillingAuthAttempt` for `subscription_initial|payment_method_change`.

Binding clarification: include `planTierCode` in current/scheduled snapshots; map `customerKey`, nullable key fingerprint, billing/benefit anchors, full scheduled snapshot, and safe card fields; remove direct-provider IDs and bank-name fields. Legacy encrypted keys with null fingerprints remain inert and are excluded from renewal/deletion claims. New install/swap writes key+fingerprint+safe card atomically, null-safe CAS permits explicit legacy re-registration, and removal success clears both key and fingerprint. Attempt persistence covers receipt hash, current/candidate/previous fingerprints, candidate card snapshot, consent, cleanup status/errors, terminal timestamps, exact 15-day expiry, and authKey clearing. After day 15 an uncertain attempt moves to blocking `reconciliation_required`; it is not silently replaced with a new idempotency key. Do not delete the five old change files in Task 6; Tasks 14–16 migrate their consumers and Task 19 performs final deletion/registration cleanup.

- [ ] **Step 1: Write failing persistence tests**

```ts
const contract: SubscriptionContractSnapshot = {
  billingProductId: 'product-pro-yearly',
  planTierId: 'tier-pro',
  productCode: 'pro_yearly',
  productName: 'Pro 연간',
  priceKrw: 382900,
  billingIntervalMonths: 12,
  monthlyCredits: 1000,
  planTierCode: 'pro',
  monthlyCreditValidityDays: null,
};

expect(await subscriptions.schedulePlanChange('sub-1', {
  ...contract,
  effectiveAt: new Date('2027-01-31T00:00:00.000Z'),
})).toMatchObject({ scheduledChange: { productCode: 'pro_yearly' } });
```

Billing-attempt tests assert supplied immutable UUID/receipt hash persistence, exact 15-day expiry, authKey persistence before issue, fixed idempotency-key reuse, receipt/payment-order/open-subscription and three fingerprint lookups, atomic current-key swap, candidate safe-card persistence with authKey clearing, terminal/reconciliation clearing, cleanup claims/results, and one open attempt per subscription. Subscription selectors require both encrypted key and non-null fingerprint before automatic charge/deletion.

- [ ] **Step 2: Run tests to verify RED**

Run: `npm test -- --runInBand src/modules/payments/infrastructure/typeorm-subscriptions.repository.spec.ts src/modules/payments/infrastructure/typeorm-billing-auth-attempts.repository.spec.ts`

Expected: FAIL because contract/schedule fields and generalized repository do not exist.

- [ ] **Step 3: Implement exact models and compare-and-set methods**

```ts
export type BillingAuthPurpose = 'subscription_initial' | 'payment_method_change';
export type BillingAuthAttemptStatus =
  | 'created'
  | 'checkout_ready'
  | 'authorization_pending'
  | 'billing_key_issued'
  | 'completed'
  | 'canceled'
  | 'expired'
  | 'failed'
  | 'reconciliation_required';

export interface SubscriptionContractSnapshot {
  billingProductId: string;
  planTierId: string;
  productCode: string;
  productName: string;
  priceKrw: number;
  billingIntervalMonths: number;
  monthlyCredits: number;
  planTierCode: string;
  monthlyCreditValidityDays: number | null;
}

export interface ScheduledPlanChange extends SubscriptionContractSnapshot {
  effectiveAt: Date;
}

export interface BillingAuthAttempt {
  id: string;
  subscriptionId: string;
  paymentOrderId: string | null;
  purpose: BillingAuthPurpose;
  customerKey: string;
  authKeyEnc: string | null;
  issueIdempotencyKey: string;
  receiptTokenHash: string;
  candidateBillingKeyEnc: string | null;
  candidateBillingKeyFingerprint: string | null;
  currentBillingKeyFingerprint: string | null;
  previousBillingKeyEnc: string | null;
  previousBillingKeyFingerprint: string | null;
  status: BillingAuthAttemptStatus;
  expiresAt: Date;
  createdAt: Date;
  updatedAt: Date;
}
```

`SubscriptionsRepository.swapBillingKey()` receives encrypted key, HMAC fingerprint, safe card snapshot, and expected prior fingerprint in one DB transaction using `IS NOT DISTINCT FROM`. Initial install has the same atomicity. Scheduled changes are full snapshots, not only catalog foreign keys; cancellation nulls every scheduled field atomically. `BillingAuthAttemptsRepository` binds all physical recovery/cleanup/consent/card fields and exposes id/receipt/payment-order/open-subscription/fingerprint lookups, issue CAS writes, terminal/reconciliation writes, and fingerprint-gated cleanup claims/results.

- [ ] **Step 4: Run persistence tests**

Run: `npm test -- --runInBand src/modules/payments/infrastructure/typeorm-subscriptions.repository.spec.ts src/modules/payments/infrastructure/typeorm-billing-auth-attempts.repository.spec.ts`

Expected: PASS for snapshot preservation, one-open-attempt constraint, and atomic key swap.

- [ ] **Step 5: Commit**

```bash
git add src/modules/payments/domain/subscription.model.ts src/modules/payments/domain/subscriptions.repository.ts src/modules/payments/domain/billing-auth-attempt.model.ts src/modules/payments/domain/billing-auth-attempts.repository.ts src/modules/payments/infrastructure/subscription.entity.ts src/modules/payments/infrastructure/typeorm-subscriptions.repository.ts src/modules/payments/infrastructure/typeorm-subscriptions.repository.spec.ts src/modules/payments/infrastructure/billing-auth-attempt.entity.ts src/modules/payments/infrastructure/typeorm-billing-auth-attempts.repository.ts src/modules/payments/infrastructure/typeorm-billing-auth-attempts.repository.spec.ts
git commit -m "feat(subscriptions): persist contracts and billing auth attempts"
```

### Task 7: Add durable webhook inbox and warning persistence

**Files:**
- Create: `clipper_web_api/src/modules/payments/domain/payment-webhook.model.ts`
- Create: `clipper_web_api/src/modules/payments/domain/payment-webhooks.repository.ts`
- Create: `clipper_web_api/src/modules/payments/infrastructure/payment-webhook-inbox.entity.ts`
- Create: `clipper_web_api/src/modules/payments/infrastructure/typeorm-payment-webhooks.repository.ts`
- Create: `clipper_web_api/src/modules/payments/infrastructure/typeorm-payment-webhooks.repository.spec.ts`

**Interfaces:**
- Consumes: Task 3 webhook table.
- Produces: `receive`, `claimNext`, `markProcessed`, `markRetryableFailure`, `markManualReview`, and admin cursor listing without raw sensitive payloads.

Binding clarification: Toss `data.orderId` maps to provider `orderNo`, while `paymentOrderId` is a separate nullable internal UUID link. `receive` never accepts that internal ID; a result CAS may attach it only after Task 13 re-queries and verifies the owned order. Once linked, null preserves it, the same UUID is idempotent, and a different UUID fails rather than relinking. Dedupe is a validated SHA-256 digest of canonical safe identity after secrets are replaced by fingerprints; it is per delivery key, so status/deposit events for one transition both persist while an identical key is ignored. The repository accepts no raw body, rejects unknown top-level properties, and stores only exact string-valued normalized keys `createdAt|status|reason|depositStatus`; identifiers use dedicated bounded columns and unknown/nested normalized values are rejected. To survive an out-of-order `DEPOSIT_CALLBACK`, Task 13 may write only `SecretCipher` ciphertext to a dedicated internal `depositSecretEnc` column; it is `select:false`, explicitly claim-only through a non-enumerable slot/accessor, absent from JSON/object spread and every safe/admin projection, retained only for retries, and cleared on processed/manual terminal state. Claim uses one short transaction/CTE with `FOR UPDATE SKIP LOCKED` and can reclaim stale `processing` leases; finite inputs must satisfy `staleBefore < now`, it returns the newly stored `processingStartedAt` as a strictly newer fencing token, and every result write CASes on both row id and that token so a reclaimed stale worker cannot finalize the newer lease. Task 3 fix round 5 adds the secret column and processing partial index first. Admin listing validates limit `1..100` and a finite/UUID cursor, queries `limit + 1` in `(received_at,id) DESC`, returns exact four-field OpenAPI items plus a separate structured next cursor, and exposes no normalized payload/provider identifier/database id. Only fixed uppercase internal error codes are stored and mapped to the API `errorMessage`; arbitrary exception/provider text is forbidden.

- [ ] **Step 1: Write failing inbox tests**

```ts
it('stores both event types but deduplicates a repeated delivery key', async () => {
  const staleBefore = new Date(now.getTime() - 5 * 60_000);
  expect(await repository.receive(event('PAYMENT_STATUS_CHANGED', 'ord-1', 'DONE'))).toEqual({ inserted: true });
  expect(await repository.receive(event('DEPOSIT_CALLBACK', 'ord-1', 'DONE'))).toEqual({ inserted: true });
  expect(await repository.receive(event('DEPOSIT_CALLBACK', 'ord-1', 'DONE'))).toEqual({ inserted: false });
  expect(await repository.claimNext(now, staleBefore)).toMatchObject({ orderNo: 'ord-1' });
  expect(await repository.claimNext(now, staleBefore)).toMatchObject({ orderNo: 'ord-1' });
});

it('rejects unknown plaintext fields instead of persisting them', async () => {
  const unsafe = {
    ...event('BILLING_DELETED', null, null),
    billingKeyFingerprint: 'a'.repeat(64),
    normalizedPayload: { reason: 'USER_REQUEST', billingKey: 'billing-key-plain' },
  } as unknown as NewPaymentWebhook;
  await expect(repository.receive(unsafe)).rejects.toThrow();
});
```

- [ ] **Step 2: Run tests to verify RED**

Run: `npm test -- --runInBand src/modules/payments/infrastructure/typeorm-payment-webhooks.repository.spec.ts`

Expected: FAIL because the repository is absent.

- [ ] **Step 3: Implement inbox claim and bounded normalized payloads**

```ts
export type TossWebhookEventType =
  | 'PAYMENT_STATUS_CHANGED'
  | 'DEPOSIT_CALLBACK'
  | 'BILLING_DELETED';

export interface NewPaymentWebhook {
  eventType: TossWebhookEventType;
  dedupeKey: string;
  providerEventId: string | null;
  orderNo: string | null;
  paymentKey: string | null;
  billingKeyFingerprint: string | null;
  depositSecretEnc: string | null;
  providerStatus: string | null;
  normalizedPayload: {
    createdAt?: string;
    status?: string;
    reason?: string;
    depositStatus?: string;
  };
}
```

Use `INSERT ... ON CONFLICT (dedupe_key) DO NOTHING` for delivery dedupe and a `FOR UPDATE SKIP LOCKED` claim transaction with stale-processing recovery. Validate dedupe/fingerprint values as exact lowercase 64-character hexadecimal digests. The normalized payload allowlist is exactly `createdAt`, `status`, `reason`, and `depositStatus`; it excludes card, account, secret, billingKey, authKey, and arbitrary nested provider objects. Encrypted `depositSecretEnc` is a separate claim-only field and terminal processing clears it. Enforce event-shape consistency, and let only the three processing-result CAS methods attach a verified internal payment-order UUID.

- [ ] **Step 4: Run repository tests**

Run: `npm test -- --runInBand src/modules/payments/infrastructure/typeorm-payment-webhooks.repository.spec.ts`

Expected: PASS for dedupe, concurrent claim, retry timestamp, manual review, and payload redaction.

- [ ] **Step 5: Commit**

```bash
git add src/modules/payments/domain/payment-webhook.model.ts src/modules/payments/domain/payment-webhooks.repository.ts src/modules/payments/infrastructure/payment-webhook-inbox.entity.ts src/modules/payments/infrastructure/typeorm-payment-webhooks.repository.ts src/modules/payments/infrastructure/typeorm-payment-webhooks.repository.spec.ts
git commit -m "feat(payments): persist verified webhook inbox"
```

### Task 7A: Align the persisted card display snapshot with the official Billing object

This execution prerequisite was added after the 2026-08-19 official Toss Payments MCP recheck. `Billing.card.number` is a partially masked string of up to 20 characters; the contract does not promise an accurate numeric last-four value, and the issuer is returned as `card.issuerCode`, not a company name. Do not guess digits from a masked value or label an issuer code as a name.

**Files:**
- Create: `clipper_web_api/src/core/database/migrations/admin/1787500000000-AlignTossPaymentsCardSnapshots.ts`
- Create: `clipper_web_api/src/core/database/migrations/admin/1787500000000-AlignTossPaymentsCardSnapshots.spec.ts`
- Modify: `clipper_web_api/src/core/database/admin.datasource.ts`
- Modify: `clipper_web_api/src/core/database/admin.datasource.spec.ts`
- Modify: `clipper_web_api/docs/api/openapi.yaml`
- Modify: `clipper_web_api/src/modules/payments/presentation/payments-openapi-contract.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/domain/subscription.model.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/subscription.entity.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/typeorm-subscriptions.repository.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/typeorm-subscriptions.repository.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/billing-auth-attempt.entity.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/typeorm-billing-auth-attempts.repository.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/typeorm-billing-auth-attempts.repository.spec.ts`

**Interfaces:**
- Consumes: the Task 3 schema, Task 6 atomic billing-key persistence, and official `Billing.card.{issuerCode,number,cardType}`.
- Produces: one honest safe-card snapshot `{ method, cardIssuerCode, cardNumberMasked, cardType, verifiedAt }` for subscriptions and billing-auth candidates. It deliberately has no direct-provider `ACTIVE` status and no fabricated company name or last four digits.

Binding clarification from the independent PostgreSQL review: raw TypeORM 1 `UPDATE ... RETURNING` results are `[returnedRows, affectedCount]`, not a raw row array. Every update-returning path in the two owned repositories must decode that exact shape strictly, including zero-row CAS fallbacks and boolean cancel/expire results; malformed/count-inconsistent shapes fail closed. INSERT and SELECT results remain raw row arrays. Unit fixtures must mirror the real driver shape, and an isolated PostgreSQL integration case must prove one-row and zero-row behavior. For OpenAPI, absence is represented only by the outer nullable `paymentMethod`; once a `SubscriptionPaymentMethod` object exists, all five required fields are non-null and complete, matching the domain and database all-null-or-complete invariant.

- [ ] **Step 1: Write failing schema, persistence, and OpenAPI tests**

Use a representative official masked value that does not end in four digits:

```ts
const paymentMethod = {
  method: 'CARD' as const,
  cardIssuerCode: '61',
  cardNumberMasked: '12345678****789*',
  cardType: '신용',
  verifiedAt: new Date('2026-08-19T00:00:00.000Z'),
};

expect(saved.cardNumberMasked).toBe('12345678****789*');
expect(JSON.stringify(saved)).not.toContain('cardNum4Print');
```

Assert the new append-only migration registration; final subscription and candidate column names; all-null-or-complete CARD snapshot checks; exact issuer-code, masked-number, and card-type bounds; safe down reconstruction of the 178720 columns without inventing an `ACTIVE` provider state; and removal of `providerStatus`, `cardCompanyName`, and `cardLast4` from the final OpenAPI payment-method projection.

Also reproduce the real TypeORM update tuple in both repository suites. Cover one-row mapping, zero-row fallback/false results, and malformed or count-inconsistent tuples for every shared update decoder. Parse the OpenAPI schema and reject all-null or mixed-null inner payment-method objects while accepting outer `paymentMethod: null` and a complete snapshot.

- [ ] **Step 2: Run tests to verify RED**

Run:

```bash
npm test -- --runInBand \
  src/core/database/migrations/admin/1787500000000-AlignTossPaymentsCardSnapshots.spec.ts \
  src/core/database/admin.datasource.spec.ts \
  src/modules/payments/presentation/payments-openapi-contract.spec.ts \
  src/modules/payments/infrastructure/typeorm-subscriptions.repository.spec.ts \
  src/modules/payments/infrastructure/typeorm-billing-auth-attempts.repository.spec.ts
```

Expected: FAIL because `178750` and the official safe-card field names do not exist yet.

- [ ] **Step 3: Add the append-only alignment migration and final mappings**

`178750` replaces only the legacy display columns with:

```text
subscriptions.payment_method
subscriptions.card_issuer_code
subscriptions.card_number_masked
subscriptions.card_type
subscriptions.payment_method_verified_at

billing_auth_attempts.candidate_payment_method
billing_auth_attempts.candidate_card_issuer_code
billing_auth_attempts.candidate_card_number_masked
billing_auth_attempts.candidate_card_type
billing_auth_attempts.candidate_payment_method_verified_at
```

The snapshot is either entirely null or entirely present with `method = 'CARD'`, an exact two-character uppercase alphanumeric Toss issuer code (`^[0-9A-Z]{2}$`, including official values such as `3K`, `W1`, and `3A`), a bounded value containing a mask marker, one of the official card types, and a verification timestamp. Existing direct-provider display data is cleared rather than relabeled; its null-fingerprint key is already inert and requires PG re-registration. `down()` reconstructs the 178720 column layout for rollback but leaves obsolete provider status null and derives a numeric last-four only when the stored masked value genuinely ends in four digits.

Update Task 6 entities/repositories atomically: install and swap write every safe field with the key/fingerprint, key removal may retain the already-safe historical display snapshot, and billing-auth issue stores the complete candidate snapshot while clearing authKey. OpenAPI exposes the same honest names and no provider status.

- [ ] **Step 4: Verify static and real database behavior**

Run the five focused suites above, targeted ESLint, build diagnostics, and `git diff --check`. On an isolated PostgreSQL 15 database, run the full migration chain, assert valid/null snapshots and rejection of partial/unmasked/invalid-code rows, then revert `178750` and verify the 178720-compatible columns and checks are restored.

- [ ] **Step 5: Commit**

```bash
git add src/core/database/migrations/admin/1787500000000-AlignTossPaymentsCardSnapshots.ts src/core/database/migrations/admin/1787500000000-AlignTossPaymentsCardSnapshots.spec.ts src/core/database/admin.datasource.ts src/core/database/admin.datasource.spec.ts docs/api/openapi.yaml src/modules/payments/presentation/payments-openapi-contract.spec.ts src/modules/payments/domain/subscription.model.ts src/modules/payments/infrastructure/subscription.entity.ts src/modules/payments/infrastructure/typeorm-subscriptions.repository.ts src/modules/payments/infrastructure/typeorm-subscriptions.repository.spec.ts src/modules/payments/infrastructure/billing-auth-attempt.entity.ts src/modules/payments/infrastructure/typeorm-billing-auth-attempts.repository.ts src/modules/payments/infrastructure/typeorm-billing-auth-attempts.repository.spec.ts
git commit -m "fix(payments): align safe card snapshots"
```

### Task 8: Finish the Toss Payments PG V2 provider adapter

**Files:**
- Modify: `clipper_web_api/src/modules/payments/domain/toss-payments.provider.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/http-toss-payments.provider.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/http-toss-payments.provider.spec.ts`
- Delete: `clipper_web_api/src/modules/payments/domain/toss-pay.provider.ts`
- Delete: `clipper_web_api/src/modules/payments/infrastructure/http-toss-pay.provider.ts`
- Delete: `clipper_web_api/src/modules/payments/infrastructure/http-toss-pay.provider.spec.ts`

**Interfaces:**
- Consumes: official PG V2 contract reconfirmed on 2026-08-18.
- Produces: confirm, lookup by order ID, lookup by payment key, billing-key issue, billing charge, and billing-key delete. There is deliberately no money-cancel method.

Binding clarification from the 2026-08-19 official authorization/API recheck: `Idempotency-Key` is supported on every POST, while non-POST methods are themselves idempotent. Confirm, billing-key issue, and billing charge therefore use only the caller-persisted POST key and classify ambiguous POST outcomes as uncertain. Billing-key DELETE sends no idempotency header, accepts only the documented empty `200`, and surfaces transport/5xx failures as bounded retryable provider failures for the cleanup worker; retrying the same DELETE is safe and must never create a replacement logical operation.

- [ ] **Step 1: Add failing adapter fixtures**

```ts
expect(await provider.getPaymentByPaymentKey({
  paymentKey: 'pay_safe_lookup',
  keySet: 'widget',
})).toMatchObject({
  orderId: 'ord-1',
  status: 'WAITING_FOR_DEPOSIT',
  virtualAccount: {
    bankCode: '088',
    accountNumber: '110123456789',
    dueDate: '2026-08-19T10:00:00+09:00',
    secret: null,
  },
});

expect(await provider.confirmPayment(virtualAccountConfirmation)).toMatchObject({
  status: 'WAITING_FOR_DEPOSIT',
  virtualAccount: { secret: 'deposit-secret' },
});
```

Assert widget/billing Basic auth selection, API origin fixed to `https://api.tosspayments.com`, URL encoding, all POST `Idempotency-Key` headers, no idempotency header on GET/DELETE, `taxFreeAmount: 0` for confirm and billing charge, safe card/easyPay/receipt/virtual-account parsing (including valid alphanumeric issuer `3K`, rejection of lowercase/invalid issuer codes, and exact default Korean card types `신용|체크|기프트`), 404 mapping, POST-mutation 409 `IDEMPOTENT_REQUEST_PROCESSING` mapping to uncertain, timeout/5xx/invalid-success-body mapping to uncertain for POST state-changing calls, empty-200/self-idempotent DELETE behavior, and bounded public errors. The adapter does not request English enum responses, so an English card type is an invalid success body rather than a value that can later violate Task 7A persistence. The official Payment `secret` is top-level; normalize it under the internal virtual-account object. A successful virtual-account confirmation requires and returns it, while a later GET is allowed to return `null` and must never be treated as secret recovery.

- [ ] **Step 2: Run adapter tests to verify RED**

Run: `npm test -- --runInBand src/modules/payments/infrastructure/http-toss-payments.provider.spec.ts`

Expected: FAIL on payment-key lookup, safe response fields, tax-free amount, and 409 classification.

- [ ] **Step 3: Implement the final provider contract**

```ts
export abstract class TossPaymentsProvider {
  abstract confirmPayment(input: ConfirmPaymentInput): Promise<TossPaymentsPayment>;
  abstract getPaymentByOrderId(input: PaymentLookupByOrderId): Promise<TossPaymentsPayment>;
  abstract getPaymentByPaymentKey(input: PaymentLookupByPaymentKey): Promise<TossPaymentsPayment>;
  abstract issueBillingKey(input: IssueBillingKeyInput): Promise<TossBillingAuthorization>;
  abstract chargeBillingKey(input: ChargeBillingKeyInput): Promise<TossPaymentsPayment>;
  abstract deleteBillingKey(input: DeleteBillingKeyInput): Promise<void>;
}
```

Use these exact input/result types in the same port:

```ts
export interface PaymentLookupByOrderId {
  orderId: string;
  keySet: TossPaymentsKeySet;
}

export interface PaymentLookupByPaymentKey {
  paymentKey: string;
  keySet: TossPaymentsKeySet;
}

export interface DeleteBillingKeyInput {
  billingKey: string;
}

export interface TossBillingAuthorization {
  billingKey: string;
  customerKey: string;
  method: string;
  card: TossSafeCardSnapshot | null;
}

export interface TossSafeCardSnapshot {
  issuerCode: string;
  cardNumberMasked: string;
  cardType: '신용' | '체크' | '기프트';
}

export interface TossVirtualAccountDetails {
  bankCode: string;
  accountNumber: string;
  customerName: string;
  dueDate: string;
  secret: string | null;
}
```

`TossPaymentsPayment` adds nullable `card`, `easyPayProvider`, `receiptUrl`, and `virtualAccount` fields to its existing verified identifiers/status/amount fields. Accept a receipt URL only when URL parsing succeeds with HTTPS and the exact `dashboard.tosspayments.com` host. Card parsing preserves only the official issuer code, already-masked number, and card type; issuer codes are exact two-character uppercase alphanumeric values (`^[0-9A-Z]{2}$`), not numeric-only, because the official code table includes `3K`, `W1`, and `3A`. Reject an unmasked or overlong card number instead of storing guessed digits. The issue response exposes only `billingKey`, returned `customerKey`, `method`, and the same safe card fields. Keep plaintext keys and the initial virtual-account secret in method-local/result scope only until the caller encrypts them. Treat concurrent-idempotency 409 as retryable uncertain state and reuse the caller's stored key; never generate an adapter-level replacement key.

- [ ] **Step 4: Run adapter tests and scan the port**

Run: `npm test -- --runInBand src/modules/payments/infrastructure/http-toss-payments.provider.spec.ts`

Run: `rg -n "cancelPayment|/v1/payments/.*/cancel|TOSS_PAY_(?!MENTS)" src/modules/payments --pcre2`

Expected: tests PASS; scan returns no cancellation method/path or direct Toss adapter reference.

- [ ] **Step 5: Commit**

```bash
git add src/modules/payments/domain/toss-payments.provider.ts src/modules/payments/infrastructure/http-toss-payments.provider.ts src/modules/payments/infrastructure/http-toss-payments.provider.spec.ts src/modules/payments/domain/toss-pay.provider.ts src/modules/payments/infrastructure/http-toss-pay.provider.ts src/modules/payments/infrastructure/http-toss-pay.provider.spec.ts
git commit -m "feat(payments): complete Toss Payments V2 provider"
```

### Task 9: Create owner-bound checkout sessions and secure payment redirects

**Files:**
- Create: `clipper_web_api/src/modules/payments/application/payment-checkout-session.service.ts`
- Create: `clipper_web_api/src/modules/payments/application/payment-checkout-session.service.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/presentation/payment-orders.controller.ts`
- Modify: `clipper_web_api/src/modules/payments/presentation/payment-orders.controller.spec.ts`
- Create: `clipper_web_api/src/modules/payments/presentation/toss-payments-redirect.controller.ts`
- Create: `clipper_web_api/src/modules/payments/presentation/toss-payments-redirect.controller.spec.ts`
- Create: `clipper_web_api/src/modules/payments/presentation/dto/billing-auth-success-query.dto.ts`
- Create: `clipper_web_api/src/modules/payments/presentation/dto/normal-payment-success-query.dto.ts`
- Create: `clipper_web_api/src/modules/payments/presentation/dto/payment-fail-query.dto.ts`
- Modify: `clipper_web_api/src/modules/payments/domain/payment-orders.repository.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/typeorm-payment-orders.repository.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/typeorm-payment-orders.repository.spec.ts`

**Interfaces:**
- Consumes: Task 2 `CheckoutSession`, Task 5 order lookup, JWT subject, receipt token hash, and the four browser-safe URL/client-key env values used by this task.
- Produces: `PaymentCheckoutSessionService.get(userId, receiptToken)`, normal/billing/fail redirect endpoints, and browser-safe sessions.

Binding clarification from the official V2 redirect contract recheck: the three query DTO files do not exist at this base and are created, not modified. Normal success requires the preset 43-character receipt capability plus `paymentKey`, provider `orderId`, and integer `amount`; billing success requires receipt plus `authKey` (maximum 300) and the exact stored `customerKey`; failure requires receipt plus bounded `code` and `message`, while `orderId` is optional because `PAY_PROCESS_CANCELED` can omit it. The provider `orderId` is `PaymentOrder.orderNo`, never the internal UUID. Customer checkout/result/reconcile endpoints remain JWT-owner scoped and may use only `findByReceiptTokenHashForUser`. Public redirects are capability-authenticated: add a deliberately named `findByReceiptCapabilityHash` repository lookup for Tasks 9 and 12, and never expose it through a customer controller. This is the only unscoped order lookup permitted.

The Task 9 redirect controller exports narrow injection tokens/interfaces for billing completion and `confirmNormalPayment`. Task 12's `TopupPaymentsService` directly satisfies the normal handler. Billing auth issuance alone is not a completed business flow: Task 16 creates `BillingAuthorizationRedirectService`, which calls Task 10 to issue/recover the candidate key and then dispatches by attempt purpose to Task 11 initial charge or Task 16 card swap. Task 19 binds the two final handlers with `useExisting`. This avoids a stub implementation, keeps Task 9 compilable without importing future files, and prevents a successful card registration from stopping before initial payment/card swap. A billing-issue uncertain result still redirects to the fixed result page because Task 10 has already persisted the recoverable attempt; invalid receipt/customer/order/amount correlations remain a bounded 400. The failure route hashes the receipt, correlates either the billing attempt or order capability (including the no-`orderId` cancel case), maps exact `PAY_PROCESS_CANCELED` to canceled and other failures to failed, stores only a bounded validated provider code plus fixed generic text, discards the raw provider message, and always derives the browser redirect from configured `WEB_BASE_URL`. Checkout session mapping uses only the widget or billing client key, maps `orderId` from `orderNo`, derives virtual-account due time as `createdAt + 24h` for normal checkout, and never reads any of the four secret/HMAC environment values. URL configuration accepts HTTPS origins and, for the checked-in local examples only, HTTP loopback origins; reject non-loopback HTTP, credentials, query, and fragment components before constructing fixed paths.

Remove the Task 9 controller's imports of transitional topup/subscription/direct-review services. It maps the owner-filtered `PaymentOrder` to the exact safe OpenAPI result itself and exports a third narrow `reconcileOrder(internalOrderId)` handler token; Task 12's generic reconciliation service satisfies it and Task 19 binds it with `useExisting`. Reconciliation then rereads the same owner-scoped receipt before returning, so a handler result cannot bypass ownership. The safe result is a closed projection and never serializes customerKey, receipt hash, operation idempotency keys, internal foreign keys, provider raw status/errors, or encrypted fields. Because the final PG Payment response supplies bank code but no trustworthy bank-name field, correct `VirtualAccount.bankName` (and legacy-safe holderName) to required-but-nullable OpenAPI properties instead of fabricating a name; add parsed contract coverage.

Virtual-account masking is one canonical fail-closed format: exactly three visible prefix digits, a hyphen, one or more asterisks, a hyphen, and exactly four visible suffix digits (`^[0-9]{3}-\*{1,71}-[0-9]{4}$`, maximum 80 characters). The customer projection and OpenAPI both reject all-digit values, a full account plus a stray asterisk, noncanonical separators, or more than seven visible digits. Task 12 strips only ASCII spaces/hyphens from a provider account containing otherwise digits, requires 8–78 digits, and stores `${digits.slice(0, 3)}-${'*'.repeat(digits.length - 7)}-${digits.slice(-4)}`; it never stores the full account number.

Do not route a browser failure through the repositories' broad administrative/recovery terminal methods. A stale or forged fail redirect must never change `authorization_pending`, `payment_pending`, `waiting_for_deposit`, `billing_key_issued`, `paid`, or reconciliation state, because provider lookup may still prove payment/key issuance. Add dedicated atomic pre-checkout failure CAS methods to both repositories: only `created|checkout_ready` can become canceled/failed, and a zero-row race is a safe no-op followed by the normal result redirect. An initial-subscription receipt legitimately resolves to both an attempt and its linked order; require `attempt.paymentOrderId === order.id` and apply the same pre-checkout CAS to both inside one `AdminTransactionRunner` transaction so result polling does not remain checkout-ready after a partial write. A card-change receipt resolves only to its null-order attempt and a topup receipt only to its order; any other dual/mismatched correlation fails closed without mutating either. Keep the broader methods for their existing explicit cleanup/recovery callers.

- [ ] **Step 1: Write failing security/controller tests**

```ts
await expect(service.get('different-user', receiptToken)).rejects.toThrow('not found');
expect(await service.get('user-1', receiptToken)).toEqual({
  flow: 'normal_payment',
  receiptToken,
  clientKey: 'test_ck_widget',
  customerKey: expect.any(String),
  orderId: 'ord-1',
  orderName: '500 크레딧',
  amount: { currency: 'KRW', value: 27900 },
  successUrl: 'https://api.example/payments/tosspayments/normal/success?receipt=token',
  failUrl: 'https://api.example/payments/tosspayments/fail?receipt=token',
  virtualAccountDueDate: expect.any(String),
});
```

Assert no Secret Key, authKey, billingKey, webhook secret, or encrypted field is serialized. Assert redirects use a 256-bit receipt capability to find the order and redirect only to configured `WEB_BASE_URL`, never a query-supplied URL.

- [ ] **Step 2: Run tests to verify RED**

Run: `npm test -- --runInBand src/modules/payments/application/payment-checkout-session.service.spec.ts src/modules/payments/presentation/payment-orders.controller.spec.ts src/modules/payments/presentation/toss-payments-redirect.controller.spec.ts src/modules/payments/infrastructure/typeorm-payment-orders.repository.spec.ts src/modules/payments/infrastructure/typeorm-billing-auth-attempts.repository.spec.ts src/modules/payments/presentation/payments-openapi-contract.spec.ts`

Expected: FAIL because owner-bound checkout retrieval and final redirect controller do not exist.

- [ ] **Step 3: Implement safe session mapping and redirects**

```ts
export interface CheckoutSession {
  flow: 'normal_payment' | 'billing_auth';
  receiptToken: string;
  clientKey: string;
  customerKey: string;
  orderId: string;
  orderName: string;
  amount: { currency: 'KRW'; value: number };
  successUrl: string;
  failUrl: string;
  virtualAccountDueDate: string | null;
}
```

Hash receipt tokens with SHA-256 before querying. The bearer-protected GET rechecks `order.userId === userId`. Public redirect controllers accept only validated bounded query strings, hand off provider processing through the narrow Task 10/12 tokens, then issue a 302 to `${WEB_BASE_URL}/app/payment/result?receipt=<encoded token>`. Failure messages stored to DB are validated provider error codes plus fixed bounded generic text, not raw query content.

- [ ] **Step 4: Run security/controller tests**

Run: `npm test -- --runInBand src/modules/payments/application/payment-checkout-session.service.spec.ts src/modules/payments/presentation/payment-orders.controller.spec.ts src/modules/payments/presentation/toss-payments-redirect.controller.spec.ts src/modules/payments/infrastructure/typeorm-payment-orders.repository.spec.ts src/modules/payments/infrastructure/typeorm-billing-auth-attempts.repository.spec.ts src/modules/payments/presentation/payments-openapi-contract.spec.ts`

Expected: PASS for ownership, redaction, allowed base URL, and bounded redirect queries.

- [ ] **Step 5: Commit**

```bash
git add docs/api/openapi.yaml src/modules/payments/application/payment-checkout-session.service.ts src/modules/payments/application/payment-checkout-session.service.spec.ts src/modules/payments/presentation/payment-orders.controller.ts src/modules/payments/presentation/payment-orders.controller.spec.ts src/modules/payments/presentation/toss-payments-redirect.controller.ts src/modules/payments/presentation/toss-payments-redirect.controller.spec.ts src/modules/payments/presentation/dto/billing-auth-success-query.dto.ts src/modules/payments/presentation/dto/normal-payment-success-query.dto.ts src/modules/payments/presentation/dto/payment-fail-query.dto.ts src/modules/payments/domain/payment-orders.repository.ts src/modules/payments/infrastructure/typeorm-payment-orders.repository.ts src/modules/payments/infrastructure/typeorm-payment-orders.repository.spec.ts src/modules/payments/domain/billing-auth-attempts.repository.ts src/modules/payments/infrastructure/typeorm-billing-auth-attempts.repository.ts src/modules/payments/infrastructure/typeorm-billing-auth-attempts.repository.spec.ts src/modules/payments/presentation/payments-openapi-contract.spec.ts
git commit -m "feat(payments): secure checkout sessions and redirects"
```

### Task 10: Recover billing-key issue responses with encrypted auth attempts

**Files:**
- Create: `clipper_web_api/src/modules/payments/application/billing-key-fingerprint.service.ts`
- Create: `clipper_web_api/src/modules/payments/application/billing-key-fingerprint.service.spec.ts`
- Create: `clipper_web_api/src/modules/payments/application/billing-auth.service.ts`
- Create: `clipper_web_api/src/modules/payments/application/billing-auth.service.spec.ts`
- Create: `clipper_web_api/src/modules/payments/application/billing-auth-recovery.scheduler.ts`
- Create: `clipper_web_api/src/modules/payments/application/billing-auth-recovery.scheduler.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/domain/billing-auth-attempts.repository.ts`
- Modify: `clipper_web_api/src/modules/payments/domain/toss-payments.provider.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/typeorm-billing-auth-attempts.repository.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/typeorm-billing-auth-attempts.repository.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/http-toss-payments.provider.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/http-toss-payments.provider.spec.ts`

**Interfaces:**
- Consumes: `SecretCipher`, `BillingAuthAttemptsRepository`, `TossPaymentsProvider.issueBillingKey`, and `TOSS_PAYMENTS_BILLING_KEY_HMAC_SECRET`.
- Produces: `completeAuthorization({receiptToken, customerKey, authKey})`, `recoverAttempt(attemptId)`, and keyed fingerprint comparison.

`BillingAuthService.completeAuthorization` performs only durable issue/recovery and returns the attempt with its candidate key; it does not satisfy the final browser redirect handler by itself because initial subscription charge or card swap still has to run. Task 16's coordinator owns that final dispatch. Task 10 does not register an interim redirect provider.

The application must durably account for every successfully returned billing key before allowing semantic failure to discard it. Add a rejected-candidate CAS that atomically stores encrypted key plus HMAC fingerprint, clears authKey, leaves the safe-card snapshot all null, sets a fixed internal error, transitions to `failed`, and marks candidate cleanup pending in the same SQL statement. If the returned `customerKey` mismatches, or the response is not the contracted card method with a complete safe card, use that one terminal write so there is no crash window containing a cleanup-only key mislabeled `billing_key_issued`; the fingerprint-gated cleanup worker can then delete the exact durable key. A valid response maps provider method `카드` to internal `CARD`, stores the complete safe snapshot, and clears authKey in the same write. A concurrent same-idempotency response is accepted only when the reread candidate fingerprint matches; a different candidate fails closed into reconciliation/cleanup rather than overwriting it.

Attempt expiry distinguishes provider uncertainty from durable issuance. `created|checkout_ready` may become `expired`; an `authorization_pending` attempt at its 15-day deadline becomes blocking `reconciliation_required` and never gets a replacement idempotency key. A `billing_key_issued` attempt is already durable and must not expire or enter reconciliation merely because downstream activation/swap was interrupted; Task 16's completion recovery keeps retrying it. Change `findExpiredOpenIds` so already-issued and already-reconciliation rows cannot fill the batch and starve genuinely expirable attempts.

Public-callback state handling is exact and idempotent. A malformed or missing receipt capability, a customer-key mismatch, or a success callback against `created` is a bounded `BadRequestException` before any provider call. `checkout_ready` persists the incoming encrypted auth key once; `authorization_pending` ignores a repeated query auth key and resumes only the already-persisted ciphertext with the original issue idempotency key. A matching `billing_key_issued|completed|canceled|expired|failed` attempt returns its current state without another issue call, while `reconciliation_required` rethrows `TossPaymentsUncertainResultError` so the browser proceeds to polling. The fingerprint service emits lowercase 64-hex HMAC-SHA-256 and compares only fixed-length decoded digests with `timingSafeEqual`; malformed fingerprints compare false and neither plaintext keys nor auth keys appear in logs/errors.

The provider idempotency contract requires concurrent responses for one immutable issue key to contain the same billing key. If a losing response has the same fingerprint, accept the already-persisted candidate without overwriting it. A different fingerprint is a provider-contract breach: preserve the first durable candidate, move the attempt to `reconciliation_required` with a fixed internal code, and never overwrite it or claim the conflicting untrusted plaintext as the active/cleanup candidate. Returned customer/card-policy mismatches are different: their single issued key and terminal cleanup state are persisted together through the rejected-candidate CAS.

Independent-review fix binding: the real HTTP adapter must not let non-key semantic parsing hide a successfully returned billing key. Once `issueBillingKey` has a valid non-empty `billingKey`, carry customerKey, method, and card fields as untrusted semantic data to `BillingAuthService`; only the service may classify them after encrypting and fingerprinting the key and choosing the valid-candidate or rejected-cleanup-candidate CAS. Add a concrete adapter-to-service regression for malformed issuer, mask, card type, method, and customer data with a returned key. If a deterministic provider error races the exact-deadline scheduler and `markFailed` rereads `reconciliation_required`, the service throws `TossPaymentsUncertainResultError` rather than returning reconciliation as a normal completion. Keep the service fingerprint-conflict test double identical to the repository's cleanup-state preservation.

- [ ] **Step 1: Write failing loss-recovery tests**

```ts
await expect(service.completeAuthorization(input)).rejects.toThrow(TossPaymentsUncertainResultError);
expect(repository.savedAuthorization).toMatchObject({
  authKeyEnc: expect.not.stringContaining('auth-key-plain'),
  issueIdempotencyKey: fixedIdempotencyKey,
  status: 'authorization_pending',
});

provider.issueBillingKey.mockResolvedValueOnce(billingAuthorization);
await service.recoverAttempt('attempt-1');
expect(provider.issueBillingKey).toHaveBeenLastCalledWith(expect.objectContaining({
  authKey: 'auth-key-plain',
  idempotencyKey: fixedIdempotencyKey,
}));
expect(repository.completed.authKeyEnc).toBeNull();
```

Add tests for malformed/missing receipt and input customerKey mismatch before any provider call; repeated `authorization_pending` callbacks ignoring their new authKey; issued/terminal duplicates making zero provider calls; `reconciliation_required` surfacing uncertainty; returned customerKey/card-contract mismatch using one atomically failed encrypted cleanup-candidate write with no intermediate `billing_key_issued`; concurrent same-fingerprint convergence/different-fingerprint failure; expired attempt; same-key 409 retry; exact 15-day transition to reconciliation; issued-candidate non-expiry; HMAC determinism with timing-safe malformed-digest rejection; and plaintext absence from logger/event mocks.

- [ ] **Step 2: Run tests to verify RED**

Run: `npm test -- --runInBand src/modules/payments/infrastructure/http-toss-payments.provider.spec.ts src/modules/payments/application/billing-key-fingerprint.service.spec.ts src/modules/payments/application/billing-auth.service.spec.ts src/modules/payments/application/billing-auth-recovery.scheduler.spec.ts src/modules/payments/infrastructure/typeorm-billing-auth-attempts.repository.spec.ts`

Expected: FAIL because the services do not exist.

- [ ] **Step 3: Implement the persist-before-call state machine**

```ts
export interface CompleteBillingAuthorizationInput {
  receiptToken: string;
  customerKey: string;
  authKey: string;
}

async completeAuthorization(input: CompleteBillingAuthorizationInput): Promise<BillingAuthAttempt> {
  const attempt = await this.requireOpenAttempt(input.receiptToken, input.customerKey);
  await this.attempts.saveAuthorizationPending(
    attempt.id,
    this.cipher.encrypt(input.authKey),
    attempt.issueIdempotencyKey,
  );
  return this.issueStoredAttempt(attempt.id);
}
```

`issueStoredAttempt()` rereads/decrypts the stored authKey, calls the provider with the stored customerKey/idempotency key, immediately encrypts billingKey and computes `HMAC-SHA-256(secret, billingKey)`, then stores either the validated complete card candidate or the atomically failed rejected candidate before clearing authKey. Transport/5xx/409 leaves the attempt recoverable. Non-retryable rejection with no issued key clears authKey and marks failed. The scheduler selects unexpired pending attempts, never replaces the idempotency key, and moves only unresolved authorization (not an already-stored candidate) to reconciliation at the deadline.

- [ ] **Step 4: Run billing-auth tests**

Run: `npm test -- --runInBand src/modules/payments/infrastructure/http-toss-payments.provider.spec.ts src/modules/payments/application/billing-key-fingerprint.service.spec.ts src/modules/payments/application/billing-auth.service.spec.ts src/modules/payments/application/billing-auth-recovery.scheduler.spec.ts src/modules/payments/infrastructure/typeorm-billing-auth-attempts.repository.spec.ts`

Expected: PASS for response-loss recovery, encryption, fingerprint, expiry, and log redaction.

- [ ] **Step 5: Commit**

```bash
git add src/modules/payments/application/billing-key-fingerprint.service.ts src/modules/payments/application/billing-key-fingerprint.service.spec.ts src/modules/payments/application/billing-auth.service.ts src/modules/payments/application/billing-auth.service.spec.ts src/modules/payments/application/billing-auth-recovery.scheduler.ts src/modules/payments/application/billing-auth-recovery.scheduler.spec.ts src/modules/payments/domain/billing-auth-attempts.repository.ts src/modules/payments/domain/toss-payments.provider.ts src/modules/payments/infrastructure/typeorm-billing-auth-attempts.repository.ts src/modules/payments/infrastructure/typeorm-billing-auth-attempts.repository.spec.ts src/modules/payments/infrastructure/http-toss-payments.provider.ts src/modules/payments/infrastructure/http-toss-payments.provider.spec.ts
git commit -m "feat(payments): recover billing authorization issues"
```

### Task 11: Implement initial monthly and annual card subscription payment

**Files:**
- Create: `clipper_web_api/src/core/database/migrations/admin/1787600000000-IndexSubscriptionInitialOrders.ts`
- Create: `clipper_web_api/src/core/database/migrations/admin/1787600000000-IndexSubscriptionInitialOrders.spec.ts`
- Modify: `clipper_web_api/src/core/database/admin.datasource.ts`
- Modify: `clipper_web_api/src/core/database/admin.datasource.spec.ts`
- Modify: `clipper_web_api/src/modules/catalog/domain/product-catalog.repository.ts`
- Modify: `clipper_web_api/src/modules/catalog/application/product-catalog.service.ts`
- Modify: `clipper_web_api/src/modules/catalog/application/product-catalog.service.spec.ts`
- Modify: `clipper_web_api/src/modules/catalog/infrastructure/typeorm-product-catalog.repository.ts`
- Modify: `clipper_web_api/src/modules/catalog/infrastructure/typeorm-product-catalog.repository.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/domain/payment-orders.repository.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/typeorm-payment-orders.repository.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/typeorm-payment-orders.repository.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/application/subscription-payments.service.ts`
- Modify: `clipper_web_api/src/modules/payments/application/subscription-payments.service.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/presentation/subscriptions.controller.ts`
- Modify: `clipper_web_api/src/modules/payments/presentation/subscriptions.controller.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/presentation/dto/create-subscription-checkout.dto.ts`

**Interfaces:**
- Consumes: manager-bound active catalog/access reads, Task 6 subscription/attempt repositories, Task 10 billing auth result, Task 8 billing charge, Task 9 checkout-session projection, and the existing `PaymentFulfillmentService.fulfill(orderId)` port whose exact behavior is finalized in Task 14.
- Produces: `createCheckout(userId, billingProductCode)`, idempotent `completeInitialBilling(attemptId)`, user-authorized `retryInitial(userId)`, and a closed current-subscription DTO. Task 15 makes the existing `/subscriptions/current/retry` endpoint dispatch pending initial retry versus past-due renewal retry; Task 11 does not add a second public retry route.

Binding clarification from the 2026-08-19 official V2 recheck: a successful card automatic-billing approval is a Payment with exact `type=BILLING`, `method=카드`, `status=DONE`, `currency=KRW`, and a non-null complete `card`. `type=NORMAL` is not valid here. The same POST idempotency key returns the first response for 15 days. Therefore uncertainty and crash recovery always reuse the original order, payload, and billing-charge key, while a confirmed decline can be retried only as a new, explicitly user-authorized logical `subscription_initial` order with a new order number and new charge key. Never create that replacement while an initial order is pending, under reconciliation, or paid but not fulfilled.

Catalog and access authorization must be evaluated inside the same short transaction that creates the checkout. Add manager binding and product-by-code lookup to the catalog repository/service. Under `AccessRepository.withUserLock(userId)`, reread the active recurring product and its active tier, reject current or scheduled access, reject an unresolved open subscription, then create the pending subscription, initial order, and linked auth attempt. The subscription, order, and attempt share the random customer key, receipt hash, order link, and immutable issue/charge keys. Mark both order and attempt checkout-ready before commit; after commit, obtain the browser-safe session through Task 9's `PaymentCheckoutSessionService.get(userId, receiptToken)`.

Task 9 and Task 10 can leave a keyless pending subscription after a canceled/failed/expired pre-checkout attempt. A later checkout may retire and replace it only when the linked attempt is terminal, the linked order is still pre-checkout or equivalently terminal, no billing key/fingerprint/payment-method snapshot is installed, and no paid/unfulfilled or uncertain state exists. Atomically finish any leftover pre-checkout order, cancel that old pending subscription, and create a fresh flow from the current catalog. Never recycle an authorization-pending, billing-key-issued, payment-pending, reconciliation, or paid-unfulfilled flow. A terminal initial attempt passed later through the Task 16 coordinator calls `completeInitialBilling` only to converge its linked order/keyless pending subscription; it performs zero provider calls.

Multiple initial orders make the old unordered subscription/purpose lookup unsafe. Add deterministic latest-initial lookup ordered by `(created_at DESC,id DESC)`, an unresolved-initial predicate, purpose-restricted begin/reclaim/fail CAS methods, and a pre-checkout-expiry CAS. Add a forward migration, without changing `178730`, for a latest-order partial index and a unique unresolved-initial partial index. The latter covers pre-checkout/pending/reconciliation states and paid-but-not-fulfilled so concurrent retries cannot create two chargeable logical orders.

- [ ] **Step 1: Write failing initial-payment tests**

```ts
const checkout = await service.createCheckout('user-1', 'basic_yearly');
expect(checkout).toMatchObject({ flow: 'billing_auth', amount: { value: 190900, currency: 'KRW' } });
expect(subscriptions.created).toMatchObject({
  status: 'pending',
  customerKey: expect.stringMatching(/^[0-9a-f-]{36}$/),
  contract: { priceKrw: 190900, billingIntervalMonths: 12, monthlyCredits: 400 },
});

await service.completeInitialBilling('attempt-1');
expect(provider.chargeBillingKey).toHaveBeenCalledWith(expect.objectContaining({
  amount: 190900,
  idempotencyKey: expect.any(String),
}));
expect(fulfillment.fulfill).toHaveBeenCalledTimes(1);
```

Add monthly Basic/Pro, annual Basic/Pro, inactive product, existing open subscription, tampered catalog input, charge failure with no access/credits, duplicate success, and uncertain charge with no replacement order tests.

Also add active-or-scheduled access, concurrent checkout, full transaction rollback, keyless terminal pending-flow restart, no restart for issued/pending/reconciliation/paid-unfulfilled states, strict attempt/order/subscription/customer/receipt/issue-key/contract correlation, all invalid billing Payment shapes, crash after install/claim/provider/paid, exact 15-day lookup-only recovery, deterministic-decline completion with retained key, user-authorized new-order retry, concurrent retry, closed current DTO, and secret-absence tests. Repository tests prove that broad `markFailed()` is never used for an initial charge conclusion and that losing CAS workers cannot call the provider.

- [ ] **Step 2: Run tests to verify RED**

Run: `npm test -- --runInBand src/core/database/migrations/admin/1787600000000-IndexSubscriptionInitialOrders.spec.ts src/core/database/admin.datasource.spec.ts src/modules/catalog/application/product-catalog.service.spec.ts src/modules/catalog/infrastructure/typeorm-product-catalog.repository.spec.ts src/modules/payments/infrastructure/typeorm-payment-orders.repository.spec.ts src/modules/payments/application/subscription-payments.service.spec.ts src/modules/payments/presentation/subscriptions.controller.spec.ts`

Expected: FAIL because code-based manager-bound catalog lookup, initial-order indexes/CAS, generalized attempts/PG charge, safe retry, and final snapshots do not exist.

- [ ] **Step 3: Implement initial subscription state transitions**

```ts
const customerKey = randomUUID();
const orderNo = `sub_${randomUUID().replaceAll('-', '')}`;
const receiptToken = randomBytes(32).toString('base64url');
const issueIdempotencyKey = randomUUID();
const chargeIdempotencyKey = randomUUID();
```

`completeInitialBilling` first locks and validates the linked attempt/order/subscription and snapshots in one short transaction, installs only the exact issued candidate on the pending subscription, and claims the fixed initial order. The network call happens after commit. A fresh claim calls the billing POST; a stale payment-pending or reconciliation claim first queries by the same order number and, before the 15-day boundary only, may repeat the identical POST/key after a verified not-found. Concurrent losers return the current pending state and do not call the provider. At or after the conservative 15-day boundary, lookup is allowed but a POST retry or replacement key/order is not.

For verified `DONE`, persist the safe provider snapshot and `paid` order state together with auth-attempt `completed` and its installed current fingerprint, then invoke fulfillment outside that transaction. A paid duplicate completes the attempt and retries fulfillment only. A deterministic provider rejection CASes only `subscription_initial/payment_pending` to failed and marks the auth attempt completed in the same transaction; the pending subscription keeps its installed key and receives no access or credits. Do not mark the attempt failed, which would queue deletion of the current key, and do not leave it issued for the completion scheduler to replay a known decline. Semantic mismatch or ambiguous provider outcome writes order reconciliation and leaves the attempt issued so Task 16 recovery uses only the original order/key. `retryInitial(userId)` requires an explicitly pending subscription with a complete usable key and latest deterministically failed initial order, confirms no unresolved initial payment, creates one new logical initial order with fresh receipt/order/charge keys under the user lock, and runs the same verifier. Replacement-card support for such a pending subscription belongs to Task 16 and does not itself auto-charge.

- [ ] **Step 4: Run initial subscription tests**

Run: `npm test -- --runInBand src/core/database/migrations/admin/1787600000000-IndexSubscriptionInitialOrders.spec.ts src/core/database/admin.datasource.spec.ts src/modules/catalog/application/product-catalog.service.spec.ts src/modules/catalog/infrastructure/typeorm-product-catalog.repository.spec.ts src/modules/payments/infrastructure/typeorm-payment-orders.repository.spec.ts src/modules/payments/application/subscription-payments.service.spec.ts src/modules/payments/presentation/subscriptions.controller.spec.ts`

Expected: PASS for four products, one-time activation, transaction-bound authorization, terminal-flow restart, tamper checks, exact billing response validation, crash convergence, deterministic new-order retry, and uncertain same-order recovery. Task 14 owns the final fulfillment implementation and its focused suite; Task 11 verifies only the existing `fulfill(orderId)` boundary with a mock.

- [ ] **Step 5: Commit**

```bash
git add src/core/database/migrations/admin/1787600000000-IndexSubscriptionInitialOrders.ts src/core/database/migrations/admin/1787600000000-IndexSubscriptionInitialOrders.spec.ts src/core/database/admin.datasource.ts src/core/database/admin.datasource.spec.ts src/modules/catalog/domain/product-catalog.repository.ts src/modules/catalog/application/product-catalog.service.ts src/modules/catalog/application/product-catalog.service.spec.ts src/modules/catalog/infrastructure/typeorm-product-catalog.repository.ts src/modules/catalog/infrastructure/typeorm-product-catalog.repository.spec.ts src/modules/payments/domain/payment-orders.repository.ts src/modules/payments/infrastructure/typeorm-payment-orders.repository.ts src/modules/payments/infrastructure/typeorm-payment-orders.repository.spec.ts src/modules/payments/application/subscription-payments.service.ts src/modules/payments/application/subscription-payments.service.spec.ts src/modules/payments/presentation/subscriptions.controller.ts src/modules/payments/presentation/subscriptions.controller.spec.ts src/modules/payments/presentation/dto/create-subscription-checkout.dto.ts
git commit -m "feat(subscriptions): charge initial PG billing payment"
```

### Task 12: Implement one-time topup confirmation and virtual-account waiting state

**Files:**
- Modify: `clipper_web_api/src/modules/payments/application/topup-payments.service.ts`
- Modify: `clipper_web_api/src/modules/payments/application/topup-payments.service.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/presentation/topup-payments.controller.ts`
- Modify: `clipper_web_api/src/modules/payments/presentation/topup-payments.controller.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/presentation/dto/create-topup-checkout.dto.ts`
- Create: `clipper_web_api/src/modules/payments/application/payment-reconciliation.service.ts`
- Create: `clipper_web_api/src/modules/payments/application/payment-reconciliation.service.spec.ts`

**Interfaces:**
- Consumes: active access, credit product code, Task 8 confirm/lookups, Task 5 transitions, and the existing `PaymentFulfillmentService.fulfill(orderId)` port whose exact behavior is finalized in Task 14.
- Produces: `createCheckout(userId, creditProductCode)`, `confirmNormalPayment(receiptToken, paymentKey, orderId, amount)`, and `reconcileOrder(orderId)`.

`TopupPaymentsService.confirmNormalPayment` structurally satisfies Task 9's normal-success redirect handler token and uses the dedicated receipt-capability lookup only inside the public callback path. Task 19 binds that token to the service with `useExisting`; owner-facing reads remain owner-filtered.

- [ ] **Step 1: Write failing normal/virtual-account tests**

```ts
provider.confirmPayment.mockResolvedValue(payment({ status: 'WAITING_FOR_DEPOSIT', method: '가상계좌' }));
const result = await service.confirmNormalPayment(callback);
expect(result.status).toBe('waiting_for_deposit');
expect(fulfillment.fulfill).not.toHaveBeenCalled();

provider.getPaymentByOrderId.mockResolvedValue(payment({ status: 'DONE', method: '가상계좌' }));
await reconciliation.reconcileOrder(order.id);
await reconciliation.reconcileOrder(order.id);
expect(fulfillment.fulfill).toHaveBeenCalledTimes(1);
```

Add tests for active-access gating, purchase before access expiry followed by DONE after expiry, three credit products, callback orderId/paymentKey/amount mismatch, card/easyPay/transfer DONE, unexpected completed method warning plus normal single fulfillment, confirm timeout then lookup, VA due-at 24 hours, expiry without fulfillment, and late provider DONE overriding local expiry.

- [ ] **Step 2: Run tests to verify RED**

Run: `npm test -- --runInBand src/modules/payments/application/topup-payments.service.spec.ts src/modules/payments/application/payment-reconciliation.service.spec.ts src/modules/payments/presentation/topup-payments.controller.spec.ts`

Expected: FAIL on PG confirm, waiting status, and reconciliation behavior.

- [ ] **Step 3: Implement normal payment confirmation**

```ts
const ALLOWED_TOPUP_METHODS = new Set([
  '카드', '간편결제', '계좌이체', '가상계좌',
]);
const ALLOWED_EASY_PAY_PROVIDERS = new Set([
  '카카오페이', '네이버페이', '토스페이',
]);
```

Create a server-snapshotted order only after active access validation; give every order a random customerKey, receipt token hash, fixed confirm idempotency key, and VA due time `createdAt + 24h`. Confirm with stored order ID and amount. Persist provider safe details and encrypted deposit secret. `DONE` starts idempotent fulfillment; `WAITING_FOR_DEPOSIT` never does. Unexpected successfully completed methods create a warning event and still fulfill the purchased product exactly once. On uncertain confirm, lookup using the stored key set/order ID; if no conclusion is available, mark reconciliation without creating or charging a second order.

For a returned virtual account, strip only ASCII spaces/hyphens from `accountNumber`, reject any other character or a resulting length outside 8–78 digits, and persist only the canonical mask `${digits.slice(0, 3)}-${'*'.repeat(digits.length - 7)}-${digits.slice(-4)}`. Never persist the full provider account number. This exact representation must satisfy Task 9's final projection/OpenAPI guard.

- [ ] **Step 4: Run topup/reconciliation tests**

Run: `npm test -- --runInBand src/modules/payments/application/topup-payments.service.spec.ts src/modules/payments/application/payment-reconciliation.service.spec.ts src/modules/payments/presentation/topup-payments.controller.spec.ts`

Expected: PASS for immediate methods, VA issue/deposit/expiry, mismatch rejection, late DONE, and one fulfillment.

- [ ] **Step 5: Commit**

```bash
git add src/modules/payments/application/topup-payments.service.ts src/modules/payments/application/topup-payments.service.spec.ts src/modules/payments/application/payment-reconciliation.service.ts src/modules/payments/application/payment-reconciliation.service.spec.ts src/modules/payments/presentation/topup-payments.controller.ts src/modules/payments/presentation/topup-payments.controller.spec.ts src/modules/payments/presentation/dto/create-topup-checkout.dto.ts
git commit -m "feat(payments): confirm topups and virtual accounts"
```

### Task 13: Verify and process all three Toss webhook events

**Files:**
- Create: `clipper_web_api/src/modules/payments/application/payment-webhook.service.ts`
- Create: `clipper_web_api/src/modules/payments/application/payment-webhook.service.spec.ts`
- Create: `clipper_web_api/src/modules/payments/application/payment-webhook-recovery.scheduler.ts`
- Create: `clipper_web_api/src/modules/payments/application/payment-webhook-recovery.scheduler.spec.ts`
- Create: `clipper_web_api/src/modules/payments/presentation/toss-payments-webhook.controller.ts`
- Create: `clipper_web_api/src/modules/payments/presentation/toss-payments-webhook.controller.spec.ts`
- Create: `clipper_web_api/src/modules/payments/presentation/dto/toss-payments-webhook.dto.ts`

**Interfaces:**
- Consumes: Task 7 inbox, Task 8 lookups, Task 10 fingerprint, Task 12 reconciliation, subscription/current/candidate/previous fingerprint lookups.
- Produces: one public `POST /payments/tosspayments/webhook` endpoint and retry worker for `PAYMENT_STATUS_CHANGED`, `DEPOSIT_CALLBACK`, `BILLING_DELETED`.

- [ ] **Step 1: Write failing webhook tests**

```ts
await controller.receive({
  eventType: 'DEPOSIT_CALLBACK',
  createdAt: '2026-08-18T12:00:00+09:00',
  data: { orderId: 'ord-va', status: 'DONE', secret: 'callback-secret' },
});
expect(provider.getPaymentByOrderId).toHaveBeenCalledWith({ orderId: 'ord-va', keySet: 'widget' });
expect(fulfillment.fulfill).toHaveBeenCalledTimes(1);
```

Add tests that body-only PAYMENT_STATUS_CHANGED never marks paid before lookup; deposit secret uses timing-safe comparison; invalid secret becomes manual review; duplicate and reversed payment/deposit events converge; BILLING_DELETED hashes plaintext immediately and distinguishes current/candidate/previous/unmatched keys; current deletion stops future charges and marks re-registration required; candidate/previous deletion does not stop current billing; CANCELED/PARTIAL_CANCELED creates warning only.

- [ ] **Step 2: Run tests to verify RED**

Run: `npm test -- --runInBand src/modules/payments/application/payment-webhook.service.spec.ts src/modules/payments/application/payment-webhook-recovery.scheduler.spec.ts src/modules/payments/presentation/toss-payments-webhook.controller.spec.ts`

Expected: FAIL because the webhook endpoint and processor are absent.

- [ ] **Step 3: Implement receive-then-verify processing**

```ts
switch (event.eventType) {
  case 'PAYMENT_STATUS_CHANGED':
    return this.verifyPayment(event, false);
  case 'DEPOSIT_CALLBACK':
    return this.verifyPayment(event, true);
  case 'BILLING_DELETED':
    return this.applyBillingDeletion(event);
}
```

The controller validates only the event envelope, normalizes and stores safe identifiers, responds promptly, and never logs the body. The processor re-queries Payment for both payment events and checks stored order ID/amount/currency/type before delegating to reconciliation. It decrypts the stored VA secret solely for timing-safe comparison. For BILLING_DELETED it computes the HMAC while the DTO is in memory, discards the plaintext, queries fingerprints, and applies the exact current/candidate/previous rules. Retry uses inbox status and bounded backoff; repeated delivery is safe.

- [ ] **Step 4: Run webhook and reconciliation tests**

Run: `npm test -- --runInBand src/modules/payments/application/payment-webhook.service.spec.ts src/modules/payments/application/payment-webhook-recovery.scheduler.spec.ts src/modules/payments/presentation/toss-payments-webhook.controller.spec.ts src/modules/payments/application/payment-reconciliation.service.spec.ts`

Expected: PASS for all event types, duplicate/reversed delivery, safe deletion correlation, and external cancellation warnings.

- [ ] **Step 5: Commit**

```bash
git add src/modules/payments/application/payment-webhook.service.ts src/modules/payments/application/payment-webhook.service.spec.ts src/modules/payments/application/payment-webhook-recovery.scheduler.ts src/modules/payments/application/payment-webhook-recovery.scheduler.spec.ts src/modules/payments/presentation/toss-payments-webhook.controller.ts src/modules/payments/presentation/toss-payments-webhook.controller.spec.ts src/modules/payments/presentation/dto/toss-payments-webhook.dto.ts
git commit -m "feat(payments): verify Toss payment webhooks"
```

### Task 14: Fulfill paid products once and retain internal credit recovery

**Files:**
- Modify: `clipper_web_api/src/modules/payments/application/payment-fulfillment.service.ts`
- Modify: `clipper_web_api/src/modules/payments/application/payment-fulfillment.service.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/application/payment-recovery.scheduler.ts`
- Modify: `clipper_web_api/src/modules/payments/application/payment-recovery.scheduler.spec.ts`
- Verify: `clipper_web_api/src/modules/operations/application/operation-recovery.service.ts`
- Verify: `clipper_web_api/src/modules/operations/application/operation-recovery.service.spec.ts`
- Verify: `clipper_web_api/src/modules/credits/application/credit-grants.service.ts`
- Verify: `clipper_web_api/src/modules/credits/application/credit-grants.service.spec.ts`

**Interfaces:**
- Consumes: paid orders and exact anchors from Tasks 4–6.
- Produces: idempotent fulfillment for initial, renewal, upgrade, and topup plus retry-only recovery after payment success.

Binding clarification: while updating `PaymentRecoveryScheduler`, replace its old `SubscriptionPaymentMethodChangesRepository` dependency and expiry/candidate/previous cleanup calls with the final `BillingAuthAttemptsRepository` contract. Cleanup claims must require a non-null corresponding fingerprint; migrated direct-provider ciphertext is never sent to PG.

- [ ] **Step 1: Write failing fulfillment tests**

```ts
await Promise.all([service.fulfill(order.id), service.fulfill(order.id)]);
expect(access.activateSubscription).toHaveBeenCalledTimes(1);
expect(credits.grant).toHaveBeenCalledTimes(1);

expect(credits.grant).toHaveBeenCalledWith(expect.objectContaining({
  source: 'subscription',
  credits: 400,
  expiresAt: new Date('2026-09-30T10:00:00.000Z'),
}));
```

Add topup 365-day grant, annual first-month-only grant, upgrade delta grant, failed fulfillment retry without recharging, stale claim reclaim, and expired-source internal credit return remaining unspendable tests. Keep operation recovery tests green with `charge_then_refund` terminology.

- [ ] **Step 2: Run tests to verify RED**

Run: `npm test -- --runInBand src/modules/payments/application/payment-fulfillment.service.spec.ts src/modules/payments/application/payment-recovery.scheduler.spec.ts src/modules/operations/application/operation-recovery.service.spec.ts src/modules/credits/application/credit-grants.service.spec.ts`

Expected: FAIL on exact benefit expiry and final purpose/state types; existing internal credit refund tests remain PASS.

- [ ] **Step 3: Implement short claim/fulfill/finalize phases**

```ts
if (!(await this.orders.tryBeginFulfillment(order.id, staleBefore))) return;
try {
  await this.transaction.run(manager => this.applyPurpose(manager, order));
  await this.orders.markFulfillmentSucceeded(order.id);
} catch (error) {
  await this.orders.markFulfillmentFailed(order.id, classify(error));
  throw error;
}
```

Initial and renewal activation use contract snapshots, but access checks continue reading current tier plugin entitlements. Subscription grants expire at the next immutable benefit anchor; topups expire exactly 365 days after paidAt. Upgrade grants only the rounded remaining-cycle credit delta supplied by Task 17. The recovery worker retries fulfillment only and never calls confirm/charge. Do not rename or remove operation-layer `refund` ledger types because they represent internal credit restoration.

- [ ] **Step 4: Run fulfillment and internal recovery tests**

Run: `npm test -- --runInBand src/modules/payments/application/payment-fulfillment.service.spec.ts src/modules/payments/application/payment-recovery.scheduler.spec.ts src/modules/operations/application/operation-recovery.service.spec.ts src/modules/operations/application/operations.service.spec.ts src/modules/credits/application/credit-grants.service.spec.ts`

Expected: PASS with one grant per logical payment and unchanged operation-failure credit restoration.

- [ ] **Step 5: Commit**

```bash
git add src/modules/payments/application/payment-fulfillment.service.ts src/modules/payments/application/payment-fulfillment.service.spec.ts src/modules/payments/application/payment-recovery.scheduler.ts src/modules/payments/application/payment-recovery.scheduler.spec.ts
git commit -m "feat(payments): fulfill paid products idempotently"
```

### Task 15: Preserve anchored renewals, D+1/D+2 recovery, cancel, and resume

**Files:**
- Modify: `clipper_web_api/docs/api/openapi.yaml`
- Modify: `clipper_web_api/src/modules/payments/application/subscription-renewal.service.ts`
- Modify: `clipper_web_api/src/modules/payments/application/subscription-renewal.service.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/application/subscription-renewal-policy.service.ts`
- Modify: `clipper_web_api/src/modules/payments/application/subscription-renewal-policy.service.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/presentation/subscriptions.controller.ts`
- Modify: `clipper_web_api/src/modules/payments/presentation/subscriptions.controller.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/presentation/payments-openapi-contract.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/presentation/dto/cancel-subscription.dto.ts`

**Interfaces:**
- Consumes: stored contract/billing anchor, PG billing charge, payment reconciliation, existing configurable retry policy.
- Produces: scheduler/manual renewal, pending-initial versus past-due retry dispatch on the existing route, `cancelAtPeriodEnd`, `resume`, and period-end billing-key cleanup.

Binding clarification: migrate every renewal-service open-card-change check from `SubscriptionPaymentMethodChangesRepository` to `BillingAuthAttemptsRepository`. Automatic charge and billing-key deletion require both encrypted key and non-null fingerprint; paid fulfillment recovery remains separate.

Preserve the single public `POST /subscriptions/current/retry` route. The controller first asks Task 11 for a pending initial-payment retry: Task 11 returns `null` only when the current subscription is not pending, but throws a bounded conflict for a pending subscription whose latest initial order is not deterministically failed. Only the `null` case delegates to this task's existing past-due renewal retry. Update OpenAPI to describe both user-authorized cases. An initial retry creates the new logical order/key specified by Task 11; a past-due retry continues the existing renewal order/key. Never fall through from an unresolved pending initial payment into renewal or create a replacement for uncertainty.

- [ ] **Step 1: Write failing renewal policy tests**

```ts
expect(await service.cancel('user-1')).toMatchObject({
  status: 'cancel_at_period_end',
  cancelAt: new Date('2026-09-30T10:00:00.000Z'),
});
expect(provider.deleteBillingKey).not.toHaveBeenCalled();

expect(await service.resume('user-1')).toMatchObject({
  status: 'active',
  nextBillingAt: new Date('2026-09-30T10:00:00.000Z'),
});
```

Add monthly Jan-31 anchoring, annual 12-month anchoring, annual monthly benefits, D+0/D+1/D+2/D+3, manual retry not consuming automatic index, immutable cycle policy snapshot, no duplicate charge while unresolved, invalid/deleted key stopping automatic charge, and late DONE after cancellation moving cancelAt to the paid period end.

- [ ] **Step 2: Run tests to verify RED**

Run: `npm test -- --runInBand src/modules/payments/application/subscription-renewal.service.spec.ts src/modules/payments/application/subscription-renewal-policy.service.spec.ts src/modules/payments/presentation/subscriptions.controller.spec.ts src/modules/payments/presentation/payments-openapi-contract.spec.ts`

Expected: FAIL on PG provider types, resume endpoint, and original-anchor period math.

- [ ] **Step 3: Implement anchored renewal and cancellation semantics**

```ts
const nextPeriodEnd = monthAnniversary(
  subscription.billingAnchorAt,
  completedBillingCycles + subscription.contract.billingIntervalMonths,
);
```

Create one renewal order with the active or scheduled contract snapshot before calling the provider. Reuse its billing charge idempotency key across scheduled/manual conclusion retries. `cancel()` clears any scheduled plan change but retains the billing key until paid period end. `resume()` is allowed only before cancelAt with a usable current key. At period end and with no unresolved payment, delete the key, then mark deletion success/failure without ending already-earned data. Provider uncertainty blocks new charge creation until lookup/retry concludes.

- [ ] **Step 4: Run renewal tests**

Run: `npm test -- --runInBand src/modules/payments/application/subscription-renewal.service.spec.ts src/modules/payments/application/subscription-renewal-policy.service.spec.ts src/modules/payments/presentation/subscriptions.controller.spec.ts src/modules/payments/presentation/payments-openapi-contract.spec.ts`

Expected: PASS for monthly/annual anchors, recovery policy, cancel/resume, and late DONE.

- [ ] **Step 5: Commit**

```bash
git add docs/api/openapi.yaml src/modules/payments/application/subscription-renewal.service.ts src/modules/payments/application/subscription-renewal.service.spec.ts src/modules/payments/application/subscription-renewal-policy.service.ts src/modules/payments/application/subscription-renewal-policy.service.spec.ts src/modules/payments/presentation/subscriptions.controller.ts src/modules/payments/presentation/subscriptions.controller.spec.ts src/modules/payments/presentation/payments-openapi-contract.spec.ts src/modules/payments/presentation/dto/cancel-subscription.dto.ts
git commit -m "feat(subscriptions): renew and cancel on fixed anchors"
```

### Task 16: Replace direct payment-method status lookup with PG card re-registration

**Files:**
- Modify: `clipper_web_api/src/modules/payments/application/subscription-payment-methods.service.ts`
- Modify: `clipper_web_api/src/modules/payments/application/subscription-payment-methods.service.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/presentation/subscriptions.controller.ts`
- Modify: `clipper_web_api/src/modules/payments/presentation/subscriptions.controller.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/presentation/dto/start-subscription-payment-method-change.dto.ts`
- Create: `clipper_web_api/src/modules/payments/application/billing-authorization-redirect.service.ts`
- Create: `clipper_web_api/src/modules/payments/application/billing-authorization-redirect.service.spec.ts`
- Create: `clipper_web_api/src/modules/payments/application/billing-authorization-completion.scheduler.ts`
- Create: `clipper_web_api/src/modules/payments/application/billing-authorization-completion.scheduler.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/domain/subscriptions.repository.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/typeorm-subscriptions.repository.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/typeorm-subscriptions.repository.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/domain/billing-auth-attempts.repository.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/typeorm-billing-auth-attempts.repository.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/typeorm-billing-auth-attempts.repository.spec.ts`

**Interfaces:**
- Consumes: Task 10 billing auth service, atomic `swapBillingKey`, current billing-key fingerprint, renewal service.
- Produces: current safe payment-method view and start/result/reconcile/cancel card-change flow.

Binding clarification: this task removes the main application consumer of `SubscriptionPaymentMethodChangesRepository` but does not delete its files or DI/entity registration yet. Candidate/previous deletion may claim only fingerprinted PG keys, and a migrated null-fingerprint current key can be replaced via null-safe CAS but never charged or automatically deleted.

A pending subscription may start card replacement only after Task 11 has durably classified its latest initial order as a deterministic failure and `hasUnresolvedInitial()` is false. Add a dedicated pending-key replacement CAS; do not broaden the active/past-due `swapBillingKey` predicate. The replacement attempt has no charge-order link and installing the new card does not itself charge. It preserves the old key for fingerprint-gated cleanup, leaves the subscription pending, and the user explicitly invokes the existing retry route later so Task 11 creates a new logical initial order and charge key. Issued, payment-pending, reconciliation, or paid-unfulfilled initial flows block replacement.

Create the final Task 9 billing-success handler here, when both business completions exist. `BillingAuthorizationRedirectService.completeAuthorization(input)` first delegates to Task 10's durable issue/recovery. For a `billing_key_issued` attempt it dispatches `subscription_initial` to Task 11 `completeInitialBilling(attempt.id)` and `payment_method_change` to this task's `completeChange(attempt.id)`. A terminal initial attempt is also passed to Task 11's zero-provider settlement path so a linked pre-checkout order and keyless pending subscription cannot remain stuck; terminal card-change attempts remain no-ops that preserve the current key. Completed initial duplicates may retry fulfillment only and never charge again. Provider uncertainty is rethrown only after Task 10 has persisted recoverable state, so the public controller can redirect to polling. Task 19 binds the Task 9 billing handler token to this coordinator with `useExisting`.

Add bounded selectors ordered by `(updated_at,id)` for `billing_key_issued` business completion and terminal initial-attempt settlement, plus a non-overlapping completion scheduler. It invokes the same coordinator, so a crash after candidate persistence but before initial charge/card swap converges without reopening billing authorization or replacing any idempotency key, and issue failure/expiry converges the linked order/subscription even without a browser retry. Completion methods must be idempotent under duplicate scheduler/controller races; one attempt cannot install two keys, charge two initial orders, or swap twice. Stale pending subscriptions whose terminal attempts have been settled are canceled; fingerprinted installed keys are queued through the existing subscription cleanup state instead of being silently discarded.

- [ ] **Step 1: Write failing card-change tests**

```ts
await service.completeChange('user-1', 'attempt-1');
expect(subscriptions.swapBillingKey).toHaveBeenCalledWith('sub-1', expect.objectContaining({
  expectedCurrentFingerprint: 'current-hmac',
  billingKeyFingerprint: 'candidate-hmac',
}));
expect(provider.deleteBillingKey).toHaveBeenCalledWith({ billingKey: 'old-key' });
```

Add candidate failure/cancel preserving old key, safe card display only, no `getBillingKeyStatus` call, normal active subscription no charge, pending deterministic-initial-failure replacement without auto-charge, unresolved-initial replacement rejection, terminal initial settlement, past_due explicit product/amount/instant-retry consent, failed past_due retry retaining new key and recovery status, issue response loss recovery, and candidate/previous deletion cleanup tests.

- [ ] **Step 2: Run tests to verify RED**

Run: `npm test -- --runInBand src/modules/payments/application/subscription-payment-methods.service.spec.ts src/modules/payments/application/billing-authorization-redirect.service.spec.ts src/modules/payments/application/billing-authorization-completion.scheduler.spec.ts src/modules/payments/presentation/subscriptions.controller.spec.ts src/modules/payments/infrastructure/typeorm-subscriptions.repository.spec.ts src/modules/payments/infrastructure/typeorm-billing-auth-attempts.repository.spec.ts`

Expected: FAIL because the service depends on the direct-provider ACTIVE lookup and old change repository.

- [ ] **Step 3: Implement issue-swap-delete flow**

```ts
export interface StartPaymentMethodChangeInput {
  userId: string;
  retryPastDueAfterChange: boolean;
  consentedProductName: string | null;
  consentedAmountKrw: number | null;
}
```

Keep the current key until Task 10 stores a candidate key. In one transaction compare the expected current fingerprint, install candidate encrypted key/fingerprint/safe card snapshot, and record the previous key for cleanup. Delete the previous key after commit. For past_due, require server-rendered current contract name/amount and explicit consent, then retry the unresolved renewal with its original order/idempotency key; payment failure does not roll back the new key. Never attempt a provider status lookup for a billing key.

- [ ] **Step 4: Run card-change tests**

Run: `npm test -- --runInBand src/modules/payments/application/subscription-payment-methods.service.spec.ts src/modules/payments/application/billing-authorization-redirect.service.spec.ts src/modules/payments/application/billing-authorization-completion.scheduler.spec.ts src/modules/payments/presentation/subscriptions.controller.spec.ts src/modules/payments/application/billing-auth.service.spec.ts src/modules/payments/infrastructure/typeorm-subscriptions.repository.spec.ts src/modules/payments/infrastructure/typeorm-billing-auth-attempts.repository.spec.ts`

Expected: PASS for current-key preservation, atomic swap, cleanup, past_due consent, and response-loss recovery.

- [ ] **Step 5: Commit**

```bash
git add src/modules/payments/application/subscription-payment-methods.service.ts src/modules/payments/application/subscription-payment-methods.service.spec.ts src/modules/payments/application/billing-authorization-redirect.service.ts src/modules/payments/application/billing-authorization-redirect.service.spec.ts src/modules/payments/application/billing-authorization-completion.scheduler.ts src/modules/payments/application/billing-authorization-completion.scheduler.spec.ts src/modules/payments/domain/subscriptions.repository.ts src/modules/payments/infrastructure/typeorm-subscriptions.repository.ts src/modules/payments/infrastructure/typeorm-subscriptions.repository.spec.ts src/modules/payments/domain/billing-auth-attempts.repository.ts src/modules/payments/infrastructure/typeorm-billing-auth-attempts.repository.ts src/modules/payments/infrastructure/typeorm-billing-auth-attempts.repository.spec.ts src/modules/payments/presentation/subscriptions.controller.ts src/modules/payments/presentation/subscriptions.controller.spec.ts src/modules/payments/presentation/dto/start-subscription-payment-method-change.dto.ts
git commit -m "feat(subscriptions): change cards through PG billing auth"
```

### Task 17: Implement immediate Basic-to-Pro upgrade and scheduled plan changes

**Files:**
- Create: `clipper_web_api/src/modules/payments/application/subscription-plan-changes.service.ts`
- Create: `clipper_web_api/src/modules/payments/application/subscription-plan-changes.service.spec.ts`
- Create: `clipper_web_api/src/modules/payments/presentation/dto/change-subscription-plan.dto.ts`
- Modify: `clipper_web_api/src/modules/payments/presentation/subscriptions.controller.ts`
- Modify: `clipper_web_api/src/modules/payments/presentation/subscriptions.controller.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/application/subscription-renewal.service.ts`
- Modify: `clipper_web_api/src/modules/payments/application/subscription-renewal.service.spec.ts`

**Interfaces:**
- Consumes: current contract snapshot, target active catalog product, current period/benefit anchors, billing provider, fulfillment.
- Produces: `changePlan(userId, billingProductCode)`, `cancelScheduledChange(userId)`, immediate upgrade order, and renewal-time schedule application.

- [ ] **Step 1: Write failing price/credit calculation tests**

```ts
expect(calculateProratedUpgrade({
  currentPriceKrw: 19900,
  targetPriceKrw: 39900,
  periodStartMs: 0,
  periodEndMs: 100,
  changedAtMs: 25,
})).toBe(15000);

expect(calculateProratedCreditDelta({
  currentMonthlyCredits: 400,
  targetMonthlyCredits: 1000,
  benefitStartMs: 0,
  benefitEndMs: 100,
  changedAtMs: 25,
})).toBe(450);
```

Add same-cycle Basic→Pro only, monthly stays monthly, annual stays annual, amount `<100` scheduled instead of charged, DONE before entitlement/grant, failed/uncertain charge no upgrade, Pro→Basic scheduled, monthly↔annual scheduled, one schedule replace/cancel, cancellation clearing schedule, catalog changes after scheduling not altering snapshot, and scheduled contract applied to next renewal tests.

- [ ] **Step 2: Run tests to verify RED**

Run: `npm test -- --runInBand src/modules/payments/application/subscription-plan-changes.service.spec.ts src/modules/payments/application/subscription-renewal.service.spec.ts src/modules/payments/presentation/subscriptions.controller.spec.ts`

Expected: FAIL because plan-change service and endpoints do not exist.

- [ ] **Step 3: Implement exact ceiling calculations and state transitions**

```ts
export function prorateCeil(fullDifference: number, remainingMs: number, fullMs: number): number {
  return Math.ceil((fullDifference * remainingMs) / fullMs);
}

export function calculateProratedUpgrade(input: {
  currentPriceKrw: number;
  targetPriceKrw: number;
  periodStartMs: number;
  periodEndMs: number;
  changedAtMs: number;
}): number {
  return prorateCeil(
    input.targetPriceKrw - input.currentPriceKrw,
    input.periodEndMs - input.changedAtMs,
    input.periodEndMs - input.periodStartMs,
  );
}

export function calculateProratedCreditDelta(input: {
  currentMonthlyCredits: number;
  targetMonthlyCredits: number;
  benefitStartMs: number;
  benefitEndMs: number;
  changedAtMs: number;
}): number {
  return prorateCeil(
    input.targetMonthlyCredits - input.currentMonthlyCredits,
    input.benefitEndMs - input.changedAtMs,
    input.benefitEndMs - input.benefitStartMs,
  );
}

export const TOSS_MINIMUM_CARD_PAYMENT_KRW = 100;
```

Snapshot the target product at request time. For same-interval Basic→Pro, create one `subscription_upgrade` order for the prorated positive price delta; charge the current billing key using the order's fixed idempotency key; after verified DONE, atomically replace the contract/tier and fulfill `ceil((targetMonthlyCredits-currentMonthlyCredits)×remainingBenefit/fullBenefit)` credits once. Every downgrade or cycle change, and a sub-minimum upgrade, writes/replaces the scheduled snapshot effective at currentPeriodEnd. Renewal consumes and clears that snapshot only after the next charge succeeds.

- [ ] **Step 4: Run plan-change tests**

Run: `npm test -- --runInBand src/modules/payments/application/subscription-plan-changes.service.spec.ts src/modules/payments/application/subscription-renewal.service.spec.ts src/modules/payments/presentation/subscriptions.controller.spec.ts src/modules/payments/application/payment-fulfillment.service.spec.ts`

Expected: PASS for rounding, minimum, immediate/scheduled boundaries, replacement/cancel, and idempotent credit delta.

- [ ] **Step 5: Commit**

```bash
git add src/modules/payments/application/subscription-plan-changes.service.ts src/modules/payments/application/subscription-plan-changes.service.spec.ts src/modules/payments/presentation/dto/change-subscription-plan.dto.ts src/modules/payments/presentation/subscriptions.controller.ts src/modules/payments/presentation/subscriptions.controller.spec.ts src/modules/payments/application/subscription-renewal.service.ts src/modules/payments/application/subscription-renewal.service.spec.ts
git commit -m "feat(subscriptions): upgrade now and schedule plan changes"
```

### Task 18: Expose safe customer history and admin payment operations

**Files:**
- Create: `clipper_web_api/src/modules/payments/application/payment-history.service.ts`
- Create: `clipper_web_api/src/modules/payments/application/payment-history.service.spec.ts`
- Create: `clipper_web_api/src/modules/payments/presentation/payment-history.controller.ts`
- Create: `clipper_web_api/src/modules/payments/presentation/payment-history.controller.spec.ts`
- Create: `clipper_web_api/src/modules/payments/presentation/dto/list-payment-history-query.dto.ts`
- Create: `clipper_web_api/src/modules/payments/application/admin-payment-operations.service.ts`
- Create: `clipper_web_api/src/modules/payments/application/admin-payment-operations.service.spec.ts`
- Create: `clipper_web_api/src/modules/payments/presentation/admin-payment-operations.controller.ts`
- Create: `clipper_web_api/src/modules/payments/presentation/admin-payment-operations.controller.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/application/admin-payment-fulfillment.service.ts`
- Modify: `clipper_web_api/src/modules/payments/application/admin-payment-fulfillment.service.spec.ts`

**Interfaces:**
- Consumes: owner-filtered order history, webhook admin listing, reconciliation service, existing operator guards and fulfillment retry.
- Produces: safe customer history and read/reconcile-only admin operations.

- [ ] **Step 1: Write failing authorization/redaction tests**

```ts
const page = await history.list('user-1', { limit: 20, cursor: null });
expect(page.items[0]).toMatchObject({
  orderNo: 'ord-1',
  productName: '500 크레딧',
  amountKrw: 27900,
  status: 'waiting_for_deposit',
  receiptUrl: 'https://dashboard.tosspayments.com/receipt/redacted-safe-id',
});
expect(JSON.stringify(page)).not.toMatch(/billingKey|authKey|secretEnc|accountNumber":"[0-9]{8}/);
```

Assert another user's receipt/history returns not found, admin lists bounded safe rows, operator roles reuse current guards, reconciliation calls provider lookup only, and no controller exposes refund/payment-cancel methods.

- [ ] **Step 2: Run tests to verify RED**

Run: `npm test -- --runInBand src/modules/payments/application/payment-history.service.spec.ts src/modules/payments/presentation/payment-history.controller.spec.ts src/modules/payments/application/admin-payment-operations.service.spec.ts src/modules/payments/presentation/admin-payment-operations.controller.spec.ts`

Expected: FAIL because history/admin operations services do not exist.

- [ ] **Step 3: Implement explicit safe DTO mappers**

```ts
export interface CustomerPaymentHistoryItem {
  orderNo: string;
  purpose: PaymentPurpose;
  productName: string;
  amountKrw: number;
  status: PaymentStatus;
  fulfillmentStatus: FulfillmentStatus;
  method: string | null;
  easyPayProvider: string | null;
  receiptUrl: string | null;
  virtualAccount: Omit<VirtualAccountSnapshot, 'secretEnc'> | null;
  createdAt: string;
  paidAt: string | null;
}
```

Map fields explicitly instead of spreading entities. Customer queries include `user_id` in SQL and use opaque cursor ordering. Admin endpoints list orders, webhook inbox, and reconciliation warnings; the only mutations are existing fulfillment retry and provider re-query reconciliation. Do not add a cancel/refund DTO, service method, or UI capability.

- [ ] **Step 4: Run history/admin API tests**

Run: `npm test -- --runInBand src/modules/payments/application/payment-history.service.spec.ts src/modules/payments/presentation/payment-history.controller.spec.ts src/modules/payments/application/admin-payment-operations.service.spec.ts src/modules/payments/presentation/admin-payment-operations.controller.spec.ts src/modules/payments/application/admin-payment-fulfillment.service.spec.ts`

Expected: PASS for ownership, redaction, pagination, guarded operations, and read/reconcile-only scope.

- [ ] **Step 5: Commit**

```bash
git add src/modules/payments/application/payment-history.service.ts src/modules/payments/application/payment-history.service.spec.ts src/modules/payments/presentation/payment-history.controller.ts src/modules/payments/presentation/payment-history.controller.spec.ts src/modules/payments/presentation/dto/list-payment-history-query.dto.ts src/modules/payments/application/admin-payment-operations.service.ts src/modules/payments/application/admin-payment-operations.service.spec.ts src/modules/payments/presentation/admin-payment-operations.controller.ts src/modules/payments/presentation/admin-payment-operations.controller.spec.ts src/modules/payments/application/admin-payment-fulfillment.service.ts src/modules/payments/application/admin-payment-fulfillment.service.spec.ts
git commit -m "feat(payments): expose safe history and operations"
```

### Task 19: Wire the final Nest module and remove review/direct legacy surfaces

**Files:**
- Modify: `clipper_web_api/src/modules/payments/payments.module.ts`
- Create: `clipper_web_api/src/modules/payments/payments.module.spec.ts`
- Modify: `clipper_web_api/src/core/database/admin.datasource.ts`
- Modify: `clipper_web_api/.env.example`
- Delete: `clipper_web_api/src/modules/payments/application/review-payments.service.ts`
- Delete: `clipper_web_api/src/modules/payments/application/review-payments.service.spec.ts`
- Delete: `clipper_web_api/src/modules/payments/presentation/review-payments.controller.ts`
- Delete: `clipper_web_api/src/modules/payments/presentation/review-payments.controller.spec.ts`
- Delete: `clipper_web_api/src/modules/payments/presentation/review-payment-rate-limiter.ts`
- Delete: `clipper_web_api/src/modules/payments/presentation/review-payment-rate-limiter.spec.ts`
- Delete: `clipper_web_api/src/modules/payments/presentation/toss-payments-review-redirect.controller.ts`
- Delete: `clipper_web_api/src/modules/payments/presentation/toss-payments-review-redirect.controller.spec.ts`
- Delete: `clipper_web_api/src/modules/payments/presentation/dto/create-review-checkout.dto.ts`
- Delete: `clipper_web_api/src/modules/payments/presentation/toss-pay-callback.controller.ts`
- Delete: `clipper_web_api/src/modules/payments/presentation/toss-pay-callback.controller.spec.ts`
- Delete: `clipper_web_api/src/modules/payments/presentation/dto/billing-result-callback.dto.ts`
- Delete: `clipper_web_api/src/modules/payments/domain/subscription-payment-method-change.model.ts`
- Delete: `clipper_web_api/src/modules/payments/domain/subscription-payment-method-changes.repository.ts`
- Delete: `clipper_web_api/src/modules/payments/infrastructure/subscription-payment-method-change.entity.ts`
- Delete: `clipper_web_api/src/modules/payments/infrastructure/typeorm-subscription-payment-method-changes.repository.ts`
- Delete: `clipper_web_api/src/modules/payments/infrastructure/typeorm-subscription-payment-method-changes.repository.spec.ts`

**Interfaces:**
- Consumes: all final repositories, services, controllers, schedulers, and entities.
- Produces: one compileable payments module with no review mode, direct Toss API, or duplicate controllers/provider registrations.

Binding clarification: delete the five old payment-method-change model/repository/entity files here, after Tasks 14–16 have migrated every consumer, and remove their datasource/TypeORM/DI registrations in the same commit. The old direct callback is also removed here, so no deleted type may remain imported anywhere.

Register the Task 9 normal-success and billing-success handler tokens exactly once with `useExisting: TopupPaymentsService` and `useExisting: BillingAuthorizationRedirectService`; do not instantiate duplicate service state behind the redirect controller.

- [ ] **Step 1: Write a failing module-surface test**

```ts
it('contains only authenticated full-PG and webhook providers', async () => {
  const module = await Test.createTestingModule({ imports: [PaymentsModule] })
    .overrideProvider(TossPaymentsProvider)
    .useValue(provider)
    .compile();
  expect(module.get(PaymentWebhookService)).toBeDefined();
  expect(module.get(BillingAuthService)).toBeDefined();
});
```

Add a source scan test asserting no runtime source contains `ReviewPayments`, `/payments/review`, `TOSS_PAYMENTS_REVIEW_MODE`, `TOSS_PAY_API_KEY`, or `TossPayProvider`.

- [ ] **Step 2: Run module/build tests to verify RED**

Run: `npm test -- --runInBand src/modules/payments/payments.module.spec.ts`

Run: `npm run build`

Expected: FAIL until all final entities/providers/controllers are registered and review/direct legacy imports are removed.

- [ ] **Step 3: Register final module dependencies and env contract**

```ts
@Module({
  imports: [
    TypeOrmModule.forFeature([
      PaymentOrderEntity,
      PaymentEventEntity,
      SubscriptionEntity,
      BillingAuthAttemptEntity,
      PaymentWebhookInboxEntity,
    ], 'admin'),
    AccessModule,
    CatalogModule,
    CreditsModule,
    AuthModule,
  ],
  controllers: FINAL_PAYMENT_CONTROLLERS,
  providers: FINAL_PAYMENT_PROVIDERS,
})
export class PaymentsModule {}
```

Define `FINAL_PAYMENT_CONTROLLERS` and `FINAL_PAYMENT_PROVIDERS` in the same module with every class added in Tasks 7–18 exactly once. `.env.example` contains only the seven PG variables plus the existing `API_KEY_ENC_SECRET`; it explains that client keys are browser-safe and all secrets remain API-only.

- [ ] **Step 4: Run API focused suite and build under Node 22**

Run: `/bin/zsh -lc 'source ~/.zshrc && nvm use 22 >/dev/null && npm test -- --runInBand src/modules/payments src/modules/access src/modules/catalog src/modules/credits src/modules/operations'`

Run: `/bin/zsh -lc 'source ~/.zshrc && nvm use 22 >/dev/null && npm run build'`

Expected: PASS with no conflict markers, missing DI providers, review runtime symbols, or direct-provider symbols.

- [ ] **Step 5: Commit**

```bash
git add .env.example src/modules/payments src/core/database/admin.datasource.ts
git commit -m "refactor(payments): remove review and direct Toss flows"
```

### Task 20: Align customer-web API models, SDK wrapper, and guarded checkout route

**Files:**
- Modify: `clipper_web_client/package.json`
- Modify: `clipper_web_client/package-lock.json`
- Modify: `clipper_web_client/src/app/core/api/models.ts`
- Modify: `clipper_web_client/src/app/core/api/payments-api.service.ts`
- Modify: `clipper_web_client/src/app/core/api/payments-api.service.spec.ts`
- Modify: `clipper_web_client/src/app/core/payments/toss-payments-sdk.service.ts`
- Modify: `clipper_web_client/src/app/core/payments/toss-payments-sdk.service.spec.ts`
- Move final implementation to: `clipper_web_client/src/app/features/portal/payment-checkout/payment-checkout.component.ts`
- Create: `clipper_web_client/src/app/features/portal/payment-checkout/payment-checkout.component.html`
- Create: `clipper_web_client/src/app/features/portal/payment-checkout/payment-checkout.component.scss`
- Create: `clipper_web_client/src/app/features/portal/payment-checkout/payment-checkout.component.spec.ts`
- Modify: `clipper_web_client/src/app/features/portal/portal.routes.ts`
- Modify: `clipper_web_client/src/app/features/portal/portal.routes.spec.ts`
- Delete: the four `src/app/features/public/payment-checkout/*` files after moving their PG SDK behavior

**Interfaces:**
- Consumes: Task 2 OpenAPI `CheckoutSession`, authenticated API client, official SDK V2.
- Produces: typed API methods and guarded `/app/payment/checkout?receipt=...` page.

- [ ] **Step 1: Write failing client/SDK/component tests**

```ts
await service.requestBillingAuth(session);
expect(payment.requestBillingAuth).toHaveBeenCalledWith({
  method: 'CARD',
  customerKey: session.customerKey,
  successUrl: session.successUrl,
  failUrl: session.failUrl,
});

await service.requestNormalPayment(session);
expect(widgets.setAmount).toHaveBeenCalledWith({ currency: 'KRW', value: 27900 });
expect(widgets.requestPayment).toHaveBeenCalledWith(expect.objectContaining({
  orderId: session.orderId,
  orderName: session.orderName,
}));
```

Assert API methods send product code only, session retrieval carries bearer auth, missing receipt/error blocks SDK calls, widget renders into stable element IDs, VA due date is forwarded, and route lives under guarded portal rather than public routes.

- [ ] **Step 2: Run tests to verify RED**

Run: `/bin/zsh -lc 'source ~/.zshrc && nvm use 22 >/dev/null && npm test -- --watch=false --include src/app/core/api/payments-api.service.spec.ts --include src/app/core/payments/toss-payments-sdk.service.spec.ts --include src/app/features/portal/payment-checkout/payment-checkout.component.spec.ts --include src/app/features/portal/portal.routes.spec.ts'`

Expected: FAIL because models still mix actual/review results and checkout is public.

- [ ] **Step 3: Implement the exact client boundary**

```ts
export interface CheckoutSession {
  flow: 'normal_payment' | 'billing_auth';
  receiptToken: string;
  clientKey: string;
  customerKey: string;
  orderId: string;
  orderName: string;
  amount: { currency: 'KRW'; value: number };
  successUrl: string;
  failUrl: string;
  virtualAccountDueDate: string | null;
}
```

Load `payment(clientKey, customerKey)` for billing and `widgets({customerKey})` for normal payment. Render payment methods and agreement once, set the server amount object, and request payment with server order ID/name/success/fail URL plus virtual-account validity options. Never accept client key, amount, order name, or URL from route query. Remove all review unions and public checkout route.

- [ ] **Step 4: Run client boundary tests**

Run: `/bin/zsh -lc 'source ~/.zshrc && nvm use 22 >/dev/null && npm test -- --watch=false --include src/app/core/api/payments-api.service.spec.ts --include src/app/core/payments/toss-payments-sdk.service.spec.ts --include src/app/features/portal/payment-checkout/payment-checkout.component.spec.ts --include src/app/features/portal/portal.routes.spec.ts'`

Expected: PASS for V2 call shapes, server-authoritative fields, and authenticated routing.

- [ ] **Step 5: Commit**

```bash
git add package.json package-lock.json src/app/core/api src/app/core/payments src/app/features/portal/payment-checkout src/app/features/portal/portal.routes.ts src/app/features/portal/portal.routes.spec.ts src/app/features/public/payment-checkout
git commit -m "feat(web): add authenticated Toss checkout"
```

### Task 21: Finish pricing, topup, result, subscription management, and payment history UI

**Files:**
- Modify: `clipper_web_client/src/app/features/public/pricing/pricing.component.ts`
- Modify: `clipper_web_client/src/app/features/public/pricing/pricing.component.html`
- Modify: `clipper_web_client/src/app/features/public/pricing/pricing.component.scss`
- Modify: `clipper_web_client/src/app/features/public/pricing/pricing.component.spec.ts`
- Modify: `clipper_web_client/src/app/features/public/public.routes.ts`
- Modify: `clipper_web_client/src/app/features/portal/topup/topup.component.ts`
- Modify: `clipper_web_client/src/app/features/portal/topup/topup.component.html`
- Modify: `clipper_web_client/src/app/features/portal/topup/topup.component.scss`
- Modify: `clipper_web_client/src/app/features/portal/topup/topup.component.spec.ts`
- Move final result implementation to: `clipper_web_client/src/app/features/portal/payment-result/payment-result.component.ts`
- Create: `clipper_web_client/src/app/features/portal/payment-result/payment-result.component.html`
- Create: `clipper_web_client/src/app/features/portal/payment-result/payment-result.component.scss`
- Create: `clipper_web_client/src/app/features/portal/payment-result/payment-result.component.spec.ts`
- Modify: `clipper_web_client/src/app/features/portal/dashboard/dashboard.component.ts`
- Modify: `clipper_web_client/src/app/features/portal/dashboard/dashboard.component.html`
- Modify: `clipper_web_client/src/app/features/portal/dashboard/dashboard.component.spec.ts`
- Create: `clipper_web_client/src/app/features/portal/payment-history/payment-history.component.ts`
- Create: `clipper_web_client/src/app/features/portal/payment-history/payment-history.component.html`
- Create: `clipper_web_client/src/app/features/portal/payment-history/payment-history.component.scss`
- Create: `clipper_web_client/src/app/features/portal/payment-history/payment-history.component.spec.ts`
- Modify: `clipper_web_client/src/app/features/portal/portal.routes.ts`
- Delete: `clipper_web_client/src/app/features/public/payment-result/*` after moving the final behavior

**Interfaces:**
- Consumes: Task 20 API types/methods, auth returnUrl, final catalog/subscription/history DTOs.
- Produces: complete actual-user UI with no anonymous review action.

- [ ] **Step 1: Write failing user-flow tests**

```ts
it('returns a logged-out product choice through Google login', async () => {
  await component.subscribe('pro_yearly');
  expect(auth.loginWithGoogle).toHaveBeenCalledWith('/pricing?subscribe=pro_yearly');
});

it('shows virtual account details without an unmasked account value', async () => {
  api.order.mockResolvedValue(waitingVirtualAccountOrder);
  await component.load('receipt-token');
  expect(fixture.nativeElement.textContent).toContain('입금 대기');
  expect(fixture.nativeElement.textContent).toContain('110-***-123456');
});
```

Add tests for four subscription products, three topups, active-access topup gating, waiting/paid/failed/reconciliation result polling, receipt link safety, cancel/resume, manual retry, card change with past_due consent copy, exact safe `cardIssuerCode`/`cardNumberMasked` rendering without last-four inference, immediate/scheduled plan-change copy and schedule replace/cancel, history ownership DTO rendering, and absence of review/refund/customer-support controls.

- [ ] **Step 2: Run focused UI tests to verify RED**

Run: `/bin/zsh -lc 'source ~/.zshrc && nvm use 22 >/dev/null && npm test -- --watch=false --include src/app/features/public/pricing/pricing.component.spec.ts --include src/app/features/portal/topup/topup.component.spec.ts --include src/app/features/portal/payment-result/payment-result.component.spec.ts --include src/app/features/portal/dashboard/dashboard.component.spec.ts --include src/app/features/portal/payment-history/payment-history.component.spec.ts'`

Expected: FAIL because pricing/result still contain review branches and history/subscription actions are incomplete.

- [ ] **Step 3: Implement the final customer journeys**

```ts
async subscribe(productCode: string): Promise<void> {
  if (!this.auth.isAuthenticated()) {
    await this.auth.loginWithGoogle(`/pricing?subscribe=${encodeURIComponent(productCode)}`);
    return;
  }
  const checkout = await this.payments.createSubscriptionCheckout(productCode);
  await this.router.navigate(['/app/payment/checkout'], { queryParams: { receipt: checkout.receiptToken } });
}
```

Pricing always displays server catalog values and only actual `구독 시작` actions. Topup creates checkout by credit product code and routes to the guarded page. Result reads only receipt token, queries the owner-bound API, and polls only pending/reconciliation states with bounded intervals. Dashboard renders current contract, next billing/benefit date, safe card, cancel/resume/retry/change/scheduled-change controls. It displays the server-provided issuer code and already-masked number as safe values with a code fallback; it never guesses a company name, unmasks, or derives a numeric last four. History shows safe receipt and VA details. Keep legal refund-document route unchanged; remove only transactional money-refund controls because legal copy is outside this implementation.

- [ ] **Step 4: Run customer web tests and build under Node 22**

Run: `/bin/zsh -lc 'source ~/.zshrc && nvm use 22 >/dev/null && npm test -- --watch=false'`

Run: `/bin/zsh -lc 'source ~/.zshrc && nvm use 22 >/dev/null && npm run build'`

Expected: all customer tests and production build PASS; bundle/source scan contains no payment review mode.

- [ ] **Step 5: Commit**

```bash
git add src/app/features/public/pricing src/app/features/public/public.routes.ts src/app/features/public/payment-result src/app/features/portal/topup src/app/features/portal/payment-result src/app/features/portal/dashboard src/app/features/portal/payment-history src/app/features/portal/portal.routes.ts
git commit -m "feat(web): complete subscription and topup journeys"
```

### Task 22: Add admin payment/webhook/reconciliation operations without refunds

**Files:**
- Modify: `clipper_web_admin/src/app/core/api/models.ts`
- Create: `clipper_web_admin/src/app/core/api/payment-operations-api.service.ts`
- Create: `clipper_web_admin/src/app/core/api/payment-operations-api.service.spec.ts`
- Create: `clipper_web_admin/src/app/features/portal/payment-operations/payment-operations.component.ts`
- Create: `clipper_web_admin/src/app/features/portal/payment-operations/payment-operations.component.html`
- Create: `clipper_web_admin/src/app/features/portal/payment-operations/payment-operations.component.scss`
- Create: `clipper_web_admin/src/app/features/portal/payment-operations/payment-operations.component.spec.ts`
- Modify: `clipper_web_admin/src/app/features/portal/portal.routes.ts`
- Modify: `clipper_web_admin/src/app/features/portal/portal.routes.spec.ts`
- Modify: `clipper_web_admin/src/app/features/portal/plans/plans.component.spec.ts`
- Modify: `clipper_web_admin/src/app/features/portal/plans/plans.component.ts`
- Modify: `clipper_web_admin/src/app/features/portal/plans/plans.component.html`

**Interfaces:**
- Consumes: Task 18 admin API plus existing catalog, fulfillment-retry, renewal-policy APIs.
- Produces: payment operations route with orders/webhooks/reconciliation tabs and requery/fulfillment-retry actions only.

- [ ] **Step 1: Write failing admin tests**

```ts
it('offers reconciliation and fulfillment retry but no refund action', async () => {
  await component.load();
  const text = fixture.nativeElement.textContent;
  expect(text).toContain('상태 재확인');
  expect(text).toContain('지급 재처리');
  expect(text).not.toContain('환불 실행');
  expect(text).not.toContain('결제 취소');
});
```

Add API URL/query tests, safe field rendering, webhook retry/manual-review status, external cancellation warning, billing-key-deleted warning, existing catalog price/credit/plugin editing, and route guard tests.

- [ ] **Step 2: Run admin tests to verify RED**

Run: `/bin/zsh -lc 'source ~/.zshrc && nvm use 22 >/dev/null && npm test -- --watch=false --include src/app/core/api/payment-operations-api.service.spec.ts --include src/app/features/portal/payment-operations/payment-operations.component.spec.ts --include src/app/features/portal/portal.routes.spec.ts --include src/app/features/portal/plans/plans.component.spec.ts'`

Expected: FAIL because the operations service/component/route do not exist.

- [ ] **Step 3: Implement read/reconcile operations UI**

```ts
export interface AdminPaymentOperation {
  id: string;
  orderNo: string;
  purpose: PaymentPurpose;
  status: PaymentStatus;
  fulfillmentStatus: FulfillmentStatus;
  reconciliationReason: string | null;
  externalCancelStatus: string | null;
  updatedAt: string;
}
```

Use paginated API calls for orders, webhook inbox, and warnings. Buttons call only `POST /admin/payments/orders/{id}/reconcile` and the existing fulfillment retry endpoint. Catalog screens continue editing Basic/Pro products, monthly credits, active flags, plugin entitlements, and topup values. Do not display any secret/fingerprint or create a refund/cancel method.

- [ ] **Step 4: Run admin suite and build**

Run: `/bin/zsh -lc 'source ~/.zshrc && nvm use 22 >/dev/null && npm test -- --watch=false'`

Run: `/bin/zsh -lc 'source ~/.zshrc && nvm use 22 >/dev/null && npm run build'`

Expected: all admin tests and build PASS; source scan finds no payment refund execution control.

- [ ] **Step 5: Commit**

```bash
git add src/app/core/api/models.ts src/app/core/api/payment-operations-api.service.ts src/app/core/api/payment-operations-api.service.spec.ts src/app/features/portal/payment-operations src/app/features/portal/portal.routes.ts src/app/features/portal/portal.routes.spec.ts src/app/features/portal/plans
git commit -m "feat(admin): add PG payment operations console"
```

### Task 23: Replace review deployment variables with full PG runtime validation

**Files:**
- Modify: `clipper_infra/apps/compose.yml`
- Modify: `clipper_infra/env/stack.dev.env.example`
- Modify: `clipper_infra/env/stack.stage.env.example`
- Modify: `clipper_infra/env/stack.prod.env.example`
- Modify: `clipper_infra/runbooks/deploy-dev.md`
- Modify: `clipper_infra/scripts/deploy-dev.sh`
- Delete: `clipper_infra/scripts/validate-toss-review-env.sh`
- Delete: `clipper_infra/scripts/validate-toss-review-env.test.mjs`
- Create: `clipper_infra/scripts/validate-toss-payments-env.sh`
- Create: `clipper_infra/scripts/validate-toss-payments-env.test.mjs`

**Interfaces:**
- Consumes: seven API env names, no browser-bundled secret, API container recreation requirement.
- Produces: fail-closed env validation and compose passthrough; it performs no deployment.

- [ ] **Step 1: Write failing shell-validator tests**

```js
test('requires separate widget and billing keys plus HMAC secret', () => {
  const result = runValidator(validEnv({ TOSS_PAYMENTS_BILLING_KEY_HMAC_SECRET: '' }));
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /TOSS_PAYMENTS_BILLING_KEY_HMAC_SECRET/);
});

test('rejects removed review and direct-Toss variables', () => {
  const result = runValidator(validEnv({ TOSS_PAYMENTS_REVIEW_MODE: 'true' }));
  assert.notEqual(result.status, 0);
});
```

Also assert HTTPS return/web URLs outside explicit localhost test fixtures, distinct non-empty widget/billing secrets, no secret interpolation into customer-web service/build args, and compose config includes all API vars.

- [ ] **Step 2: Run infra tests to verify RED**

Run: `node --test scripts/validate-toss-payments-env.test.mjs`

Expected: FAIL because the new validator is absent.

- [ ] **Step 3: Implement exact validation and runbook scope**

```sh
required_names='TOSS_PAYMENTS_WIDGET_CLIENT_KEY TOSS_PAYMENTS_WIDGET_SECRET_KEY TOSS_PAYMENTS_BILLING_CLIENT_KEY TOSS_PAYMENTS_BILLING_SECRET_KEY TOSS_PAYMENTS_RETURN_BASE_URL WEB_BASE_URL TOSS_PAYMENTS_BILLING_KEY_HMAC_SECRET'
```

The validator reports variable names only, never values. Compose passes all seven only to API. The runbook documents PG V2 API version `2024-06-01`, webhook URL/event registration, Client/Secret separation, API container recreation after key changes, and test-key checklist location. Keep deploy commands descriptive but do not execute the script or alter the running dev stack.

- [ ] **Step 4: Run static infra verification**

Run: `node --test scripts/validate-toss-payments-env.test.mjs`

Run: `docker compose --env-file env/stack.dev.env.example -f apps/compose.yml -f apps/compose.dev.yml config --quiet`

Expected: validator tests PASS and compose config is valid with example values; no container is created or restarted.

- [ ] **Step 5: Commit**

```bash
git add apps/compose.yml env/stack.dev.env.example env/stack.stage.env.example env/stack.prod.env.example runbooks/deploy-dev.md scripts/deploy-dev.sh scripts/validate-toss-review-env.sh scripts/validate-toss-review-env.test.mjs scripts/validate-toss-payments-env.sh scripts/validate-toss-payments-env.test.mjs
git commit -m "chore(infra): configure full Toss Payments PG"
```

### Task 24: Verify desktop access-credit contracts remain compatible

**Files:**
- Verify: `clipper_angular/src/shell/store/store/store.component.spec.ts`
- Verify: `clipper_angular/src/shell/settings/settings/settings.component.spec.ts`
- Verify: `clipper_electron/test/web-client-url.test.js`
- Verify: `clipper_nestjs/test/access-credit-proxy.test.js`
- Verify: existing operation failure/refund tests in desktop Angular and local API

**Interfaces:**
- Consumes: unchanged `/access/current`, `/credits/*`, `/operations/*`, `/pricing`, and `/app/credits` contracts.
- Produces: evidence that PG changes do not leak into desktop runtime and internal credit recovery remains intact.

- [ ] **Step 1: Confirm the already-merged contract assertions**

```ts
expect(openWebClientPath).toHaveBeenCalledWith('/pricing');
expect(openWebClientPath).toHaveBeenCalledWith('/app/credits');
```

```js
assert.deepEqual(calls, [
  ['/access/current', { bearerToken: 'user-jwt' }],
  ['/credits/summary', { bearerToken: 'user-jwt' }],
]);
```

The merged baseline already contains these assertions. Confirm them with `rg -n "openWebClientPath|/access/current|/credits/summary"` in the listed test files, make no source or test edit, and do not rename `LicensePolicyService` as part of PG integration.

- [ ] **Step 2: Run desktop Angular tests/build with Node 22**

Run: `/bin/zsh -lc 'source ~/.zshrc && nvm use 22 >/dev/null && npm test -- --watch=false'`

Run: `/bin/zsh -lc 'source ~/.zshrc && nvm use 22 >/dev/null && npm run build'`

Expected: PASS, including locked-plugin pricing navigation, credits navigation, charge/refund guard, and access entitlement tests.

- [ ] **Step 3: Run Electron tests/build with Node 22**

Run: `/bin/zsh -lc 'source ~/.zshrc && nvm use 22 >/dev/null && npm test && npm run build'`

Expected: PASS with external web navigation still restricted to known web-client paths.

- [ ] **Step 4: Run desktop local API tests/build with Node 22**

Run: `/bin/zsh -lc 'source ~/.zshrc && nvm use 22 >/dev/null && npm run build && node --test "test/*.js" "test/*.mjs"'`

Expected: PASS for authenticated access/credit proxy, operation charging, and failure credit refund.

- [ ] **Step 5: Confirm the desktop feature worktrees remain unchanged**

```bash
git status --short --branch
```

Expected: no additional desktop diff and no new commit. If a verification fails, diagnose it under `superpowers:systematic-debugging` before deciding whether the shared API contract requires a scoped test or production change.

### Task 25: Run full migration, security, test, and build verification without deployment

**Files:**
- Create: `clipper_web_api/docs/payments/toss-payments-test-key-checklist.md`
- Verify: files owned by Tasks 2–24

**Interfaces:**
- Consumes: all implemented branches.
- Produces: reproducible verification evidence and a manual test-key checklist; no deployment, feature push, or dev merge.

- [ ] **Step 1: Write the exact manual test-key checklist**

```markdown
- [ ] Basic monthly card registration and first payment
- [ ] Basic annual card registration and first payment
- [ ] Pro monthly card registration and first payment
- [ ] Pro annual card registration and first payment
- [ ] Topup by card, Kakao Pay, Naver Pay, Toss Pay, and bank transfer
- [ ] Virtual account issue, pre-deposit waiting, DONE deposit, and expiry
- [ ] Card change for active and past_due subscriptions
- [ ] Scheduled and manual renewal retry, cancel, and resume
- [ ] Immediate Basic-to-Pro upgrade and scheduled downgrade/cycle change
- [ ] Duplicate PAYMENT_STATUS_CHANGED and DEPOSIT_CALLBACK delivery
- [ ] Current, candidate, and previous-key BILLING_DELETED delivery
```

For every row record test/live mode, order number, expected local state, expected Toss state, webhook delivery count, and whether fulfillment happened once. State explicitly that no Toss cancel/refund API is exercised.

- [ ] **Step 2: Verify a clean PostgreSQL 16 migration chain**

Create one explicitly named disposable PostgreSQL 16 container and three empty databases:

```bash
docker run --detach --name clipper-pg-migration-test-20260818 --publish 55432:5432 --env POSTGRES_USER=clipper_test --env POSTGRES_PASSWORD=clipper_test --env POSTGRES_DB=clipper_admin_test postgres:16
docker exec clipper-pg-migration-test-20260818 pg_isready -U clipper_test -d clipper_admin_test
docker exec clipper-pg-migration-test-20260818 createdb -U clipper_test clipper_user_test
docker exec clipper-pg-migration-test-20260818 createdb -U clipper_test clipper_release_test
/usr/bin/env CLIPPER_DATABASE_HOST=127.0.0.1 CLIPPER_ADMIN_DATABASE_PORT=55432 CLIPPER_ADMIN_DATABASE_NAME=clipper_admin_test CLIPPER_ADMIN_DATABASE_USER=clipper_test CLIPPER_ADMIN_DATABASE_PASSWORD=clipper_test npm run db:migrate:admin
/usr/bin/env CLIPPER_DATABASE_HOST=127.0.0.1 CLIPPER_USER_DATABASE_PORT=55432 CLIPPER_USER_DATABASE_NAME=clipper_user_test CLIPPER_USER_DATABASE_USER=clipper_test CLIPPER_USER_DATABASE_PASSWORD=clipper_test npm run db:migrate:user
/usr/bin/env CLIPPER_DATABASE_HOST=127.0.0.1 CLIPPER_RELEASE_DATABASE_PORT=55432 CLIPPER_RELEASE_DATABASE_NAME=clipper_release_test CLIPPER_RELEASE_DATABASE_USER=clipper_test CLIPPER_RELEASE_DATABASE_PASSWORD=clipper_test npm run db:migrate:release
docker exec clipper-pg-migration-test-20260818 psql -U clipper_test -d clipper_admin_test -c "SELECT code, price_krw FROM billing_products ORDER BY code"
docker exec clipper-pg-migration-test-20260818 psql -U clipper_test -d clipper_admin_test -c "SELECT code, credits, price_krw, validity_days FROM credit_products ORDER BY code"
```

Expected: migrations `178630` through `178740` apply in timestamp order; query output matches Task 4; no existing migration file is modified. After recording output, confirm the exact target with `docker ps --filter name=^/clipper-pg-migration-test-20260818$`, then remove only that disposable container with `docker rm --force clipper-pg-migration-test-20260818`.

- [ ] **Step 3: Run complete automated verification**

API under Node 22:

```bash
npm test -- --runInBand
npm run build
npx eslint "{src,apps,libs,test}/**/*.ts"
```

Customer/admin under Node 22, in each worktree:

```bash
npm test -- --watch=false
npm run build
```

Infra and desktop use the exact commands from Tasks 23–24. Expected: every command exits 0 and ESLint performs no file writes.

- [ ] **Step 4: Run security and scope scans**

```bash
rg -n "payments/review|TOSS_PAYMENTS_REVIEW_MODE|TOSS_PAY_API_KEY|TossPayProvider|cancelPayment|/v1/payments/.*/cancel" src docs/api/openapi.yaml .env.example --pcre2
rg -n "billingKey|authKey|virtualAccount.*secret|SECRET_KEY" src/modules/payments/presentation src/modules/payments/application
git diff --check
git status --short --branch
```

Expected: first scan has no runtime/contract matches; second scan finds only deliberate internal handling and tests, never response DTO/log payload spreading; diff check is clean. Every repository remains on `feature/toss-payments-pg-integration`; protected original worktrees remain clean `dev`; no feature branch is pushed.

- [ ] **Step 5: Review requirements and commit verification documentation**

Check every section of the design against Tasks 2–24, inspect all local commits, and record tests not run because real test keys/MID settings are unavailable. Then commit the checklist in API:

```bash
git add docs/payments/toss-payments-test-key-checklist.md
git commit -m "docs(payments): add PG test-key verification checklist"
```

Do not deploy, run `scripts/deploy-dev.sh`, push feature branches, open a PR, or merge into any `dev` branch.
