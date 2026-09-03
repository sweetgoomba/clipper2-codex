# 토스페이먼츠 환불 백엔드 구현 계획

- 작성일: 2026-08-31
- 상태: 구현 전 상세 계획
- 선행 조건: 무료 체험·크레딧·기능 사용 정책 구현 완료
- 대상: Web API 중심, Infra 검증 일부

> 실제 실행 전 사용자의 구현 승인이 필요하다. 승인 후 `superpowers:executing-plans`와 테스트 우선 방식으로 수행한다. 이 계획은 토스 테스트·운영 결제를 실제로 취소할 권한을 부여하지 않는다. Provider 단위 테스트는 가짜 응답만 사용하고, 실제 토스 테스트키 검증도 별도 체크포인트에서 승인받는다.

## Goal

관리자가 환불금액과 사유를 입력하면 시스템이 다음을 안전하게 수행하도록 한다.

- 한 환불 건에 기본 구독 결제와 여러 상향 차액 결제를 묶음
- 토스 결제별 전액 또는 부분 취소
- 여러 취소 중 일부만 성공해도 사실을 잃지 않고 나머지를 재처리
- timeout·5xx·응답 유실 때 중복 환불 방지
- 환불 전 크레딧·갱신 잠금
- 환불 후 정기구독 종료와 정확한 크레딧 회수
- 토스 관리자 사이트에서 수동 취소한 거래 재조회·검증
- 원결제 상태, 금전 환불 상태, 내부 정기구독·크레딧 상태 분리

## Architecture

```text
관리자 환불 미리보기
  -> 환불 자격·관련 결제·크레딧 사용 여부 계산
  -> 관리자 금액·사유 입력
  -> 환불 건 + 결제별 항목 + 환불 전 잠금 저장
  -> DB commit
  -> 결제별 토스 최신 상태 전체 사전 확인
  -> 한 건씩 순차 취소
  -> 결과가 불확실하면 같은 키로 조회·재시도
  -> 필수 결제 취소 완료
  -> 하나의 Admin DB transaction에서 구독·크레딧 후처리
```

토스 호출은 DB transaction 밖에서 수행한다. 작업 상태는 DB에 먼저 저장하며 브라우저 연결이 끊겨도 recovery scheduler가 이어서 처리한다.

## Domain 경계

서로 다른 상태를 합치지 않는다.

- 정기구독 다음 결제 취소: 기존 `cancel_at_period_end`
- 결제금 환불: 새 `PaymentRefundCase`와 결제별 `PaymentRefundItem`
- 정기구독 종료: 환불 결과에 따른 즉시 또는 구독 월 경계 종료
- 크레딧 회수: 환불 대상 지급 건 잠금 후 별도 ledger로 회수
- 실패한 작업 크레딧 복구: 기존 `operation_refund`, 토스 호출 없음

## Task 1 — 환불 판단에 필요한 결제 스냅샷을 명시적으로 저장

**Files**

- Create: `clipper_web_api/src/core/database/migrations/admin/1788300000000-PersistPaymentRefundSnapshots.ts`
- Modify: `clipper_web_api/src/core/database/admin.datasource.ts`
- Modify: `clipper_web_api/src/core/database/admin.datasource.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/domain/payment.model.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/payment-order.entity.ts`
- Modify: `clipper_web_api/src/modules/payments/domain/payment-orders.repository.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/typeorm-payment-orders.repository.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/typeorm-payment-orders.repository.spec.ts`
- Modify: `clipper_web_api/src/modules/credits/domain/credit.model.ts`
- Modify: `clipper_web_api/src/modules/credits/domain/credits.repository.ts`
- Modify: `clipper_web_api/src/modules/credits/infrastructure/credit-grant.entity.ts`
- Modify: `clipper_web_api/src/modules/credits/infrastructure/typeorm-credits.repository.ts`
- Modify: `clipper_web_api/src/modules/credits/infrastructure/typeorm-credits.repository.spec.ts`

- [ ] 먼저 새 스냅샷의 entity/repository round-trip 실패 테스트를 작성한다.
- [ ] `payment_orders`에 다음 nullable/additive 필드를 추가한다.

```ts
interface PaymentRefundSnapshot {
  basePaymentOrderId: string | null;
  subscriptionPeriodStart: Date | null;
  subscriptionPeriodEnd: Date | null;
  benefitPeriodStart: Date | null;
  benefitPeriodEnd: Date | null;
  sourceBillingProductId: string | null;
  sourcePlanTierId: string | null;
  sourcePriceKrw: number | null;
  sourceMonthlyCredits: number | null;
  targetPriceKrw: number | null;
}
```

- [ ] `base_payment_order_id`는 같은 테이블의 결제를 가리키는 nullable FK로 만들고 삭제는 `RESTRICT`한다.
- [ ] 금액은 원 단위 정수·0 이상 check를 둔다. 기간은 start < end일 때만 유효하도록 check를 둔다.
- [ ] `credit_grants`에는 nullable `benefit_period_start`, `benefit_period_end`를 함께 추가한다. 두 값은 둘 다 NULL이거나 start < end여야 한다. 정기구독·관리자 이용권의 월별 지급 건은 두 값을 필수로 채우고, 무료 체험·추가 구매·관리자 독립 지급은 NULL로 둔다.
- [ ] 기존 정기구독·관리자 이용권 지급 건은 `granted_at`과 유효한 `expires_at`으로 월 범위를 안전하게 확인할 수 있는 행만 backfill한다. 확인할 수 없는 과거 행은 NULL로 남기고 환불 판단에서 임의 추론하지 않는다.
- [ ] 과거 결제에는 nullable을 허용한다. opaque 중복 방지 키를 migration SQL에서 억지로 파싱하지 않는다.
- [ ] 새 결제는 application validation으로 purpose별 필수 스냅샷을 강제한다. 과거 스냅샷 부족 결제는 환불 미리보기에서 `LEGACY_SNAPSHOT_INCOMPLETE`로 차단한다.
- [ ] 테스트와 build를 실행한다.

```bash
cd /Users/jina/project/adlight/.worktrees/clipper_web_api-toss-payments-pg-integration
npm test -- --runInBand src/core/database/admin.datasource.spec.ts src/modules/payments/infrastructure/typeorm-payment-orders.repository.spec.ts
npm run build
```

Review checkpoint: migration이 기존 결제 행을 삭제·재작성하지 않는지 확인한다.

## Task 2 — 최초·갱신·상향 결제가 정확한 기간과 연결을 기록

**Files**

- Modify: `clipper_web_api/src/modules/payments/application/subscription-payments.service.ts`
- Modify: `clipper_web_api/src/modules/payments/application/subscription-payments.service.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/application/subscription-renewal.service.ts`
- Modify: `clipper_web_api/src/modules/payments/application/subscription-renewal.service.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/application/subscription-plan-changes.service.ts`
- Modify: `clipper_web_api/src/modules/payments/application/subscription-plan-changes.service.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/application/payment-fulfillment.service.ts`
- Modify: `clipper_web_api/src/modules/payments/application/payment-fulfillment.service.spec.ts`
- Modify: `clipper_web_api/src/modules/access/application/monthly-credit-grant.service.ts`
- Modify: `clipper_web_api/src/modules/access/application/monthly-credit-grant.service.spec.ts`
- Modify: `clipper_web_api/src/modules/credits/application/credit-grants.service.ts`
- Modify: `clipper_web_api/src/modules/credits/application/credit-grants.service.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/domain/payment-orders.repository.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/typeorm-payment-orders.repository.ts`

- [ ] 먼저 다음 실패 테스트를 작성한다.

- 월간 최초 결제는 결제기간과 혜택 월이 동일
- 연간 최초 결제는 결제기간 12개월, 혜택 월 1개월
- 갱신 결제는 시도 시각이 아니라 예정된 period start/end 저장
- 상향 결제는 원래 상품·가격·월 크레딧, 대상 상품·가격·월 크레딧, 현재 혜택 월, 기본 결제 ID 저장
- 한 구독 월에 두 번 상향하면 두 상향 결제 모두 같은 기본 결제와 연결되고 각 전후 스냅샷은 독립 보존
- 최초·월별·상향 크레딧 지급 건이 같은 `benefitPeriodStart/End`를 저장해 해당 월 사용 여부를 정확히 묶을 수 있음

- [ ] `PaymentFulfillmentService.upgradeSnapshot()`과 `renewalPeriodStart()`가 중복 방지 키 문자열을 파싱하는 방식을 제거하고 명시적 필드를 사용한다.
- [ ] `PaymentOrdersRepository`에 다음 조회를 추가한다.

```ts
findPaidBaseForSubscriptionPeriod(
  subscriptionId: string,
  periodAt: Date,
): Promise<PaymentOrder | undefined>;

listPaidRefundGroup(
  subscriptionId: string,
  subscriptionPeriodStart: Date,
): Promise<PaymentOrder[]>;
```

월간은 현재 한 달 결제기간의 기본·상향 결제를 반환한다. 연간은 현재 연 결제기간의 기본 결제와 그 연 결제기간 안에서 발생한 모든 상향 차액 결제를 반환한다. 예를 들어 연 구독 2개월차에 상향하고 5개월차에 환불해도 2개월차 상향 결제를 누락하지 않는다.

- [ ] 중복 방지 키는 중복 호출 방지 목적으로만 사용하고 business snapshot을 운반하지 않는다.
- [ ] 테스트와 build를 실행한다.

```bash
npm test -- --runInBand src/modules/payments/application/subscription-payments.service.spec.ts src/modules/payments/application/subscription-renewal.service.spec.ts src/modules/payments/application/subscription-plan-changes.service.spec.ts src/modules/payments/application/payment-fulfillment.service.spec.ts src/modules/payments/infrastructure/typeorm-payment-orders.repository.spec.ts
npm run build
```

Review checkpoint: 월간·연간·상향 예시를 DB 스냅샷 표로 확인한다.

## Task 3 — 환불 건·결제별 항목·시도·내부 이력 schema 생성

**Files**

- Create: `clipper_web_api/src/core/database/migrations/admin/1788400000000-CreatePaymentRefundWorkflow.ts`
- Create: `clipper_web_api/src/modules/payments/domain/payment-refund.model.ts`
- Create: `clipper_web_api/src/modules/payments/domain/payment-refunds.repository.ts`
- Create: `clipper_web_api/src/modules/payments/infrastructure/payment-refund-case.entity.ts`
- Create: `clipper_web_api/src/modules/payments/infrastructure/payment-refund-item.entity.ts`
- Create: `clipper_web_api/src/modules/payments/infrastructure/payment-refund-attempt.entity.ts`
- Create: `clipper_web_api/src/modules/payments/infrastructure/payment-refund-internal-event.entity.ts`
- Create: `clipper_web_api/src/modules/payments/infrastructure/typeorm-payment-refunds.repository.ts`
- Create: `clipper_web_api/src/modules/payments/infrastructure/typeorm-payment-refunds.repository.spec.ts`
- Modify: `clipper_web_api/src/core/database/admin.datasource.ts`
- Modify: `clipper_web_api/src/core/database/admin.datasource.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/payments.module.ts`
- Modify: `clipper_web_api/src/modules/payments/payments.module.spec.ts`

- [ ] domain 상태 전이 테스트를 먼저 작성한다.

```ts
type RefundCaseKind =
  | 'monthly_subscription'
  | 'annual_subscription'
  | 'additional_credit';

type RefundMoneyStatus =
  | 'pending'
  | 'processing'
  | 'partially_completed'
  | 'completed'
  | 'manual_action_required'
  | 'voided';

type RefundInternalStatus =
  | 'not_started'
  | 'pending'
  | 'completed'
  | 'retry_required';

type RefundItemStatus =
  | 'pending'
  | 'processing'
  | 'uncertain'
  | 'failed'
  | 'completed';

type RefundCompletionSource = 'toss_api' | 'toss_dashboard';
type SubscriptionRefundEndMode = 'immediate' | 'benefit_period_end' | 'none';
```

- [ ] 환불 건에는 `userId`, nullable `subscriptionId`, kind, 돈/내부 상태, 종료 방식·시각, 사유, 선택 메모, 계획·실제 합계, 생성·실행 관리자, 원래 구독 복구 스냅샷, timestamps를 둔다.
- [ ] 결제별 항목에는 결제 ID, 목적 snapshot, 원금, 실행 직전 취소 가능 잔액, 요청 금액, 전액/부분 구분, 부분 취소 가능 snapshot, 고정 중복 방지 키, 실제 취소 금액·거래키·시각·완료 경로, 안전한 오류를 둔다.
- [ ] 시도 이력에는 요청·재조회·수동 보고·수동 검증 종류와 결과만 저장한다. 비밀키·Authorization header·원문 토스 응답은 저장하지 않는다.
- [ ] 내부 이벤트는 잠금·갱신 중단·크레딧 회수·구독 종료·결제수단 삭제의 멱등 처리키와 안전한 전후 값을 저장한다.
- [ ] 다음 제약을 migration과 repository 테스트로 고정한다.

- 금액은 양의 원 단위 정수
- 요청 합계 = case 계획 합계
- 같은 환불 건 안에서 같은 결제 중복 금지
- 같은 결제에 `pending/processing/uncertain` 환불 항목 동시 2개 금지하는 partial unique index
- 항목 중복 방지 키 unique
- 완료 상태에는 실제 거래키·금액·시각 필수
- `voided`는 토스 성공 항목이 0건일 때만 application에서 허용

- [ ] repository claim은 lease + `SKIP LOCKED`로 복수 인스턴스 동시 실행을 방지한다.
- [ ] 테스트와 build를 실행한다.

```bash
npm test -- --runInBand src/core/database/admin.datasource.spec.ts src/modules/payments/infrastructure/typeorm-payment-refunds.repository.spec.ts src/modules/payments/payments.module.spec.ts
npm run build
```

Review checkpoint: 상태표와 DB 제약이 상세 설계의 용어와 일치하는지 확인한다.

## Task 4 — 원결제 환불 잔액·크레딧 잠금·구독 환불 상태 추가

**Files**

- Create: `clipper_web_api/src/core/database/migrations/admin/1788500000000-AddRefundHoldsAndBalances.ts`
- Modify: `clipper_web_api/src/modules/payments/domain/payment.model.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/payment-order.entity.ts`
- Modify: `clipper_web_api/src/modules/payments/domain/subscription.model.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/subscription.entity.ts`
- Modify: `clipper_web_api/src/modules/credits/domain/credit.model.ts`
- Modify: `clipper_web_api/src/modules/credits/infrastructure/credit-grant.entity.ts`
- Modify: `clipper_web_api/src/modules/credits/domain/credits.repository.ts`
- Modify: `clipper_web_api/src/modules/credits/infrastructure/typeorm-credits.repository.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/typeorm-payment-orders.repository.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/typeorm-subscriptions.repository.spec.ts`
- Modify: `clipper_web_api/src/modules/credits/infrastructure/typeorm-credits.repository.spec.ts`

- [ ] entity/repository 실패 테스트를 먼저 작성한다.
- [ ] `payment_orders`에 다음 필드를 추가한다.

```ts
type PaymentRefundStatus = 'none' | 'partial' | 'full';

cumulativeRefundedKrw: number;
refundableBalanceKrw: number | null;
refundStatus: PaymentRefundStatus;
lastRefundProviderCheckedAt: Date | null;
```

원결제 `status`는 환불로 덮어쓰지 않는다. 전액 환불 후에도 최초 결제가 성공했다는 사실은 유지하고 `refundStatus = full`로 표현한다.

- [ ] `subscriptions`에 `refundProcessingCaseId`, `refundEndAt`, `refundEndMode`, `renewalPausedForRefundAt`를 추가한다. 일반 다음 결제 취소의 `cancelAt`과 구분한다.
- [ ] `credit_grants.status`에 `refund_locked`를 추가하고 `refundCaseId`, `refundLockedAt`를 둔다.
- [ ] `credit_ledger_entries.type`에 `payment_refund_revoke`를 추가한다.
- [ ] 잠긴 지급 건은 잔액 조회와 소비 대상에서 제외하지만 관리자 상세에서는 보인다.
- [ ] 작업 실패 복구가 `refund_locked` 또는 이미 `revoked`된 지급 건의 잔액을 다시 spendable로 만들지 않는 테스트를 추가한다.
- [ ] backfill은 기존 결제의 누적 환불액 0, 환불 상태 none으로 설정한다. 취소 가능 잔액은 결제 성공이 명확한 행만 `paid_amount_krw` 또는 원금으로 설정하고 불명확한 행은 NULL로 두어 토스 재조회가 필요하게 한다.
- [ ] 테스트와 build를 실행한다.

```bash
npm test -- --runInBand src/modules/payments/infrastructure/typeorm-payment-orders.repository.spec.ts src/modules/payments/infrastructure/typeorm-subscriptions.repository.spec.ts src/modules/credits/infrastructure/typeorm-credits.repository.spec.ts src/modules/credits/application/credit-grants.service.spec.ts src/modules/operations/application/operation-recovery.service.spec.ts
npm run build
```

Review checkpoint: 잠금이 삭제가 아니며 고객 사용 가능 잔액에서만 제외되는지 확인한다.

## Task 5 — 토스 결제 조회 응답에 환불 상태를 안전하게 포함

**Files**

- Modify: `clipper_web_api/src/modules/payments/domain/toss-payments.provider.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/http-toss-payments.provider.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/http-toss-payments.provider.spec.ts`

- [ ] 공식 문서 fixture를 최소 필드로 재작성해 실패 테스트를 먼저 만든다.

```ts
interface TossPaymentCancellation {
  transactionKey: string;
  cancelAmount: number;
  refundableAmount: number;
  canceledAt: string;
  cancelStatus: string;
  cancelReason: string | null;
}

interface TossPaymentsPayment {
  // existing fields
  balanceAmount: number;
  isPartialCancelable: boolean;
  cancels: TossPaymentCancellation[];
  virtualAccountRefundStatus: string | null;
}
```

- [ ] 누락 가능한 `cancels`는 빈 배열로 정규화하되 잘못된 금액·거래키를 조용히 받아들이지 않는다.
- [ ] 정수·0 이상 금액, ISO 시각, 안전한 receipt URL 등 기존 parser 원칙을 유지한다.
- [ ] 전체 취소, 여러 번 부분 취소, 이미 취소된 결제, 가상계좌 취소 상태 fixture를 테스트한다.
- [ ] 실제 응답 원문이나 secret을 로그에 남기지 않는 오류 테스트를 유지한다.

```bash
npm test -- --runInBand src/modules/payments/infrastructure/http-toss-payments.provider.spec.ts
npm run build
```

Review checkpoint: 현재 사용 중인 Toss API 버전과 fixture field 명을 공식 문서에 다시 대조한다.

## Task 6 — 토스 전액·부분 취소 provider method 추가

**Files**

- Modify: `clipper_web_api/src/modules/payments/domain/toss-payments.provider.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/http-toss-payments.provider.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/http-toss-payments.provider.spec.ts`

- [ ] 실패 테스트를 먼저 작성한다.

의도한 입력:

```ts
interface CancelPaymentInput {
  paymentKey: string;
  keySet: TossPaymentsKeySet;
  cancelReason: string;
  cancelAmount?: number;
  idempotencyKey: string;
  refundReceiveAccount?: {
    bank: string;
    accountNumber: string;
    holderName: string;
  };
}
```

- [ ] `POST /v1/payments/{paymentKey}/cancel`과 `Idempotency-Key` header를 검증한다.
- [ ] 전액 취소에서는 `cancelAmount` field 자체를 보내지 않는다.
- [ ] 부분 취소에서는 양의 안전한 정수만 보낸다.
- [ ] 빈 사유, CR/LF, 토스 제한인 200자 초과, 잘못된 payment key, 0/음수/소수 금액을 토스 호출 전에 차단한다.
- [ ] widget/billing 결제의 원래 `keySet`에 맞는 secret을 선택한다. secret 값은 테스트 출력에 나타나지 않는다.
- [ ] timeout·연결 종료·일부 5xx는 `TossPaymentsUncertainResultError`, 명확한 4xx는 안전한 provider error로 구분한다.
- [ ] `refundReceiveAccount`는 향후 가상계좌 환불을 위한 provider 입력만 제공한다. 이번 환불 UI나 가상계좌 TODO를 구현하지 않는다. 실제 결제수단이 이를 요구하면 `manual_action_required`로 차단한다.

```bash
npm test -- --runInBand src/modules/payments/infrastructure/http-toss-payments.provider.spec.ts
npm run build
```

Review checkpoint: 전액/부분 request body와 중복 방지 header snapshot을 확인한다.

## Task 7 — 상품별 환불 자격과 관리자 미리보기 구현

**Files**

- Create: `clipper_web_api/src/modules/payments/application/payment-refund-eligibility.service.ts`
- Create: `clipper_web_api/src/modules/payments/application/payment-refund-eligibility.service.spec.ts`
- Create: `clipper_web_api/src/modules/payments/application/payment-refund-query.service.ts`
- Create: `clipper_web_api/src/modules/payments/application/payment-refund-query.service.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/domain/payment-orders.repository.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/typeorm-payment-orders.repository.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/typeorm-payment-orders.repository.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/domain/subscriptions.repository.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/typeorm-subscriptions.repository.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/typeorm-subscriptions.repository.spec.ts`
- Modify: `clipper_web_api/src/modules/credits/domain/credits.repository.ts`
- Modify: `clipper_web_api/src/modules/credits/infrastructure/typeorm-credits.repository.ts`
- Modify: `clipper_web_api/src/modules/credits/infrastructure/typeorm-credits.repository.spec.ts`

- [ ] 다음 정책표를 실패 테스트로 먼저 고정한다.

월간 정기구독:

- 현재 혜택 월의 기본·모든 상향 크레딧 `remaining = initial`이면 관련 결제 모두 전액 가능
- 하나라도 일부 사용이면 전체 구독 환불 차단
- 무료 체험·추가 구매 크레딧 사용은 무관
- 즉시 종료

연간 정기구독:

- 현재 혜택 월 기본·상향 크레딧 모두 미사용이면 현재 월 포함, 즉시 종료
- 하나라도 사용했으면 현재 월 제외, 다음 혜택 월 경계 종료
- 부분 취소 금액은 자동 계산하지 않음
- 현재 연 결제기간의 기본 연 결제와 그 기간 중 발생한 모든 상향 차액 결제를 후보로 반환
- 과거 혜택 월에 상향했더라도 상향 결제가 현재 연 결제기간의 미래 기간까지 포함하면 후보에서 누락하지 않음

추가 구매 크레딧:

- `active`, 만료 전, `remaining = initial`, 같은 결제의 진행 중 환불 없음이면 전액 가능
- 일부 사용·만료·잠금·회수면 차단
- 실패 작업 복구로 전량 보전됐으면 새 미리보기에서 가능

- [ ] 차단 이유는 stable code와 사람이 읽을 근거를 함께 반환한다.

```ts
type RefundEligibilityReason =
  | 'ELIGIBLE'
  | 'CREDITS_USED'
  | 'CREDITS_EXPIRED'
  | 'REFUND_ALREADY_IN_PROGRESS'
  | 'PAYMENT_NOT_PAID'
  | 'PROVIDER_STATE_REFRESH_REQUIRED'
  | 'PARTIAL_CANCELLATION_UNAVAILABLE'
  | 'LEGACY_SNAPSHOT_INCOMPLETE';
```

- [ ] 미리보기 응답은 결제 후보, 원금, 현재 내부 취소 가능 잔액, 전액/부분 허용, 연결된 지급 건과 사용량, 종료 시각을 반환한다. 토스의 최신 상태 확인 전에는 “최종 가능”이라고 표시하지 않는다.
- [ ] 월별 정기구독 지급 건은 nullable `paymentOrderId`만 믿지 않고 `subscriptionId + benefitPeriodStart/End`로 현재 혜택 월을 묶는다. 상향 지급 건의 `paymentOrderId`와 결제 스냅샷도 함께 대조한다.
- [ ] 연간 항목 금액은 `null`로 반환해 관리자가 입력해야 하며 서버는 1원 이상·현재 잔액 이하·전체 합계 일치를 검증한다.
- [ ] 테스트와 build를 실행한다.

```bash
npm test -- --runInBand src/modules/payments/application/payment-refund-eligibility.service.spec.ts src/modules/payments/application/payment-refund-query.service.spec.ts
npm run build
```

Review checkpoint: 각 판단이 “해당 결제로 지급된 크레딧”만 보는지 확인한다.

## Task 8 — 환불 건 생성과 실행 전 잠금을 하나의 DB transaction으로 처리

**Files**

- Create: `clipper_web_api/src/modules/payments/application/payment-refund-command.service.ts`
- Create: `clipper_web_api/src/modules/payments/application/payment-refund-command.service.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/domain/payment-refunds.repository.ts`
- Modify: `clipper_web_api/src/modules/credits/domain/credits.repository.ts`
- Modify: `clipper_web_api/src/modules/payments/domain/subscriptions.repository.ts`
- Modify: TypeORM repositories and specs

- [ ] 실패 테스트를 먼저 작성한다.

- 같은 user가 소유한 결제만 선택 가능
- 미리보기 이후 지급 건이 사용됐으면 생성 transaction이 실패
- 같은 결제의 동시 환불 생성 중 한 건만 성공
- 환불 건·항목 저장, 지급 건 잠금, 구독 갱신 pause, 예약 변경 pause가 모두 성공하거나 모두 rollback
- 전액 항목의 관리자가 입력한 금액 변조 차단
- 연간 부분 금액의 항목별·합계 검증
- 필수 토스 취소 사유와 선택 메모 분리

- [ ] transaction 안에서는 토스를 호출하지 않는다.
- [ ] 크레딧 소비와 같은 per-user lock을 반드시 사용한다. 구독 환불의 lock 순서는 `subscription row → user access lock → credit grant rows → payment/refund rows`로 고정하고 갱신·월별 지급도 같은 순서를 따르게 해 deadlock을 피한다.
- [ ] 크레딧은 `refund_locked`로 바꾸되 잔액을 아직 0으로 만들지 않는다.
- [ ] 구독의 원래 status, nextBillingAt, cancelAt, scheduledChange를 환불 건 복구 스냅샷에 저장한다.
- [ ] 환불 건 저장 후 DB에 `pending` 상태가 남으므로 HTTP 요청이 끊겨도 scheduler가 처리할 수 있게 한다.

```bash
npm test -- --runInBand src/modules/payments/application/payment-refund-command.service.spec.ts src/modules/payments/infrastructure/typeorm-payment-refunds.repository.spec.ts src/modules/credits/infrastructure/typeorm-credits.repository.spec.ts src/modules/payments/infrastructure/typeorm-subscriptions.repository.spec.ts
npm run build
```

Review checkpoint: 토스 호출 전 lock/rollback 경계를 sequence test로 확인한다.

## Task 9 — 전체 사전 확인 후 결제별 순차 취소 처리

**Files**

- Create: `clipper_web_api/src/modules/payments/application/payment-refund-execution.service.ts`
- Create: `clipper_web_api/src/modules/payments/application/payment-refund-execution.service.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/payments.module.ts`
- Modify: `clipper_web_api/src/modules/payments/payments.module.spec.ts`

- [ ] 가짜 provider로 다음 실패 테스트를 먼저 만든다.

- 모든 항목을 먼저 조회한 뒤에만 첫 취소 호출
- 소유 결제 key, 원금, 기존 취소 합계, 잔액, 부분 취소 가능 여부 불일치 시 돈을 하나도 취소하지 않음
- 전액 항목은 `cancelAmount` 없음
- 부분 항목은 관리자 입력 금액
- 항목은 생성 순서 또는 명시한 sequence로 한 건씩 호출
- 같은 환불 건 재실행 시 완료 항목은 다시 취소하지 않음
- 한 항목 성공·다음 항목 명확한 실패 → 일부 완료
- 불확실한 항목 발생 → 그 항목 확인 전 뒤 항목 진행 중단

- [ ] 각 항목의 중복 방지 키는 생성 때 한 번 만들고 재시도에서도 바꾸지 않는다.
- [ ] provider 성공 응답의 새 취소 거래를 이전 조회 snapshot과 비교해 실제 거래키·금액·시각을 기록한다.
- [ ] 항목 완료와 payment order의 누적 환불액·잔액 갱신은 하나의 짧은 DB transaction으로 처리한다.
- [ ] 실제 누적 취소가 원금을 넘는다면 완료 처리하지 않고 관리자 조치 필요로 둔다.

```bash
npm test -- --runInBand src/modules/payments/application/payment-refund-execution.service.spec.ts src/modules/payments/infrastructure/http-toss-payments.provider.spec.ts src/modules/payments/infrastructure/typeorm-payment-refunds.repository.spec.ts
npm run build
```

Review checkpoint: 두 결제 중 하나만 성공한 상태의 DB row와 관리자용 상태를 확인한다.

## Task 10 — 불확실 결과·재조회·15일 이후 처리와 recovery scheduler

**Files**

- Create: `clipper_web_api/src/modules/payments/application/payment-refund-recovery.service.ts`
- Create: `clipper_web_api/src/modules/payments/application/payment-refund-recovery.service.spec.ts`
- Create: `clipper_web_api/src/modules/payments/application/payment-refund-recovery.scheduler.ts`
- Create: `clipper_web_api/src/modules/payments/application/payment-refund-recovery.scheduler.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/payments.module.ts`
- Modify: `clipper_web_api/src/modules/payments/payments.module.spec.ts`

- [ ] 실패 테스트를 먼저 작성한다.

- timeout 뒤 토스 조회에 예정 거래 발견 → 완료
- timeout 뒤 조회에 거래 없음, 15일 이내 → 같은 키 재시도
- 15일 이후 → 먼저 조회하고 실제 취소 없음이 명확할 때만 새 logical attempt와 새 키 생성
- 조회 결과가 여전히 모호함 → `manual_action_required`
- 여러 scheduler 인스턴스가 같은 item을 중복 claim하지 않음
- 브라우저 요청이 없어도 pending case 처리
- 최대 자동 시도와 backoff 적용

- [ ] “15일”은 attempt 생성 시각과 현재 시각으로 계산하고 설정 상수에 근거 주석을 남긴다.
- [ ] recovery scheduler는 10초마다 due item을 claim한다. 불확실 결과의 자동 재조회 간격은 10초, 1분, 5분, 30분, 2시간, 12시간으로 두고 여섯 번째 자동 확인 뒤 `manual_action_required`로 전환한다. 운영 중 수치는 코드 상수와 테스트로 함께 조정할 수 있게 한다.
- [ ] HTTP 4xx라도 “이미 취소됨”, 잔액 변경 등의 경우 provider 조회 결과로 최종 판단한다. 에러 문자열만 보고 완료 처리하지 않는다.
- [ ] scheduler는 safe error code만 저장하고 로그 redaction을 유지한다.

```bash
npm test -- --runInBand src/modules/payments/application/payment-refund-recovery.service.spec.ts src/modules/payments/application/payment-refund-recovery.scheduler.spec.ts src/modules/payments/payments.module.spec.ts
npm run build
```

Review checkpoint: 재시도마다 어떤 키를 쓰는지 timeline으로 확인한다.

## Task 11 — 토스 관리자 사이트 수동 취소와 외부 취소 연결 검증

**Files**

- Create: `clipper_web_api/src/modules/payments/application/payment-refund-manual-verification.service.ts`
- Create: `clipper_web_api/src/modules/payments/application/payment-refund-manual-verification.service.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/application/payment-reconciliation.service.ts`
- Modify: `clipper_web_api/src/modules/payments/application/payment-reconciliation.service.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/application/payment-webhook.service.ts`
- Modify: `clipper_web_api/src/modules/payments/application/payment-webhook.service.spec.ts`

- [ ] 다음 실패 테스트를 먼저 작성한다.

- 관리자의 “수동 취소함” 보고만으로 완료되지 않음
- 재조회에서 이전 snapshot에 없던 취소 거래를 찾고 금액 일치 → `toss_dashboard` 완료
- 거래는 있으나 금액 불일치 → 관리자 조치 필요, 실제 금액은 별도 표시
- 취소 거래 없음 → 미확인 유지
- 내부 case 없는 외부 `CANCELED/PARTIAL_CANCELED` → reconciliation warning, 구독·크레딧 자동 변경 없음
- 외부 취소를 기존/새 환불 건에 연결한 뒤 같은 검증 흐름 사용

- [ ] 웹훅과 동기 API 응답은 모두 토스 결제 snapshot을 갱신할 수 있지만, 내부 후처리는 검증된 refund item을 기준으로만 시작한다.
- [ ] 기존 top-up 중심 reconciliation을 최초·갱신·상향 결제에도 적용하되 자동 환불 건 생성을 하지 않는다.
- [ ] `BILLING_DELETED` exact candidate/extant-previous TODO는 이번 Task에 섞지 않는다.

```bash
npm test -- --runInBand src/modules/payments/application/payment-refund-manual-verification.service.spec.ts src/modules/payments/application/payment-reconciliation.service.spec.ts src/modules/payments/application/payment-webhook.service.spec.ts
npm run build
```

Review checkpoint: 외부 취소가 자동으로 이용권을 없애지 않는 안전 경계를 확인한다.

## Task 12 — 환불 완료 후 정기구독·크레딧 내부 처리

**Files**

- Create: `clipper_web_api/src/modules/payments/application/payment-refund-effects.service.ts`
- Create: `clipper_web_api/src/modules/payments/application/payment-refund-effects.service.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/domain/subscriptions.repository.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/typeorm-subscriptions.repository.ts`
- Modify: `clipper_web_api/src/modules/credits/domain/credits.repository.ts`
- Modify: `clipper_web_api/src/modules/credits/infrastructure/typeorm-credits.repository.ts`
- Modify: `clipper_web_api/src/modules/access/domain/access.repository.ts`
- Modify: `clipper_web_api/src/modules/access/infrastructure/typeorm-access.repository.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/typeorm-subscriptions.repository.spec.ts`
- Modify: `clipper_web_api/src/modules/credits/infrastructure/typeorm-credits.repository.spec.ts`
- Modify: `clipper_web_api/src/modules/access/infrastructure/typeorm-access.repository.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/application/subscription-renewal.service.spec.ts`
- Modify: `clipper_web_api/src/modules/access/application/monthly-credit-grant.service.spec.ts`

- [ ] 상품별 실패 테스트를 먼저 작성한다.

월간 구독:

1. 모든 결제 항목 완료 전에는 최종 회수·종료 안 함
2. 대상 기본·상향 지급 건 전량 회수
3. 구독·access 즉시 종료
4. 다음 결제·미래 지급·예약 변경 중단
5. 결제수단 삭제 요청
6. 무료 체험·추가 구매 크레딧 유지

연간 현재 월 미사용:

- 완료 뒤 현재 월 기본·상향 지급 건 회수, 즉시 종료

연간 현재 월 사용:

- 현재 월 지급 건 유지
- `refundEndAt = 다음 혜택 월 경계`
- next billing과 미래 지급은 즉시 중단
- access grant 종료 시각도 같은 `refundEndAt`으로 단축
- 경계 scheduler에서 남은 정기구독 크레딧 만료와 구독·access 최종 종료

추가 구매:

- 연결된 top-up 지급 건만 전량 회수
- 정기구독과 다른 지급 건 유지

공통:

- 같은 effects를 두 번 실행해도 ledger·종료 event·billing-key 삭제가 중복되지 않음
- 토스 완료 후 DB transaction 실패 → money completed + internal retry_required
- internal retry는 토스를 다시 부르지 않음
- 이미 잠긴 지급 건에 작업 실패 복구가 와도 spendable이 되지 않음

- [ ] 내부 처리 전체를 한 Admin DB transaction으로 실행하되 토스 billing key 삭제는 외부 호출이므로 DB transaction 뒤 별도 멱등 단계로 처리한다.
- [ ] 토스 취소가 0건인 void만 잠금·구독 상태를 복구할 수 있다. 잠금 중 만료된 크레딧은 `expired`로 풀고 `active`로 되살리지 않는다.
- [ ] 한 건이라도 취소 성공하면 자동 void/원상복구하지 않는다.

```bash
npm test -- --runInBand src/modules/payments/application/payment-refund-effects.service.spec.ts src/modules/payments/infrastructure/typeorm-subscriptions.repository.spec.ts src/modules/credits/infrastructure/typeorm-credits.repository.spec.ts src/modules/access/infrastructure/typeorm-access.repository.spec.ts src/modules/payments/application/subscription-renewal.service.spec.ts src/modules/access/application/monthly-credit-grant.service.spec.ts
npm run build
```

Review checkpoint: 돈 상태와 내부 상태가 서로 독립적으로 실패·복구되는지 확인한다.

## Task 13 — 관리자 환불 API와 최고 관리자 권한

**Files**

- Create: `clipper_web_api/src/modules/payments/presentation/admin-payment-refunds.controller.ts`
- Create: `clipper_web_api/src/modules/payments/presentation/admin-payment-refunds.controller.spec.ts`
- Create: `clipper_web_api/src/modules/payments/presentation/dto/create-payment-refund.dto.ts`
- Create: `clipper_web_api/src/modules/payments/presentation/dto/preview-payment-refund.dto.ts`
- Create: `clipper_web_api/src/modules/payments/presentation/dto/manual-payment-refund-verification.dto.ts`
- Create: `clipper_web_api/src/modules/payments/presentation/dto/link-external-payment-cancellation.dto.ts`
- Create: `clipper_web_api/src/modules/payments/presentation/dto/void-payment-refund.dto.ts`
- Create: `clipper_web_api/src/modules/payments/presentation/dto/list-payment-refunds-query.dto.ts`
- Modify: `clipper_web_api/src/modules/payments/payments.module.ts`
- Modify: `clipper_web_api/src/modules/payments/payments.module.spec.ts`
- Modify: `clipper_web_api/docs/api/openapi.yaml`
- Modify: `clipper_web_api/src/modules/payments/presentation/payments-openapi-contract.spec.ts`

- [ ] controller/guard 실패 테스트를 먼저 작성한다.
- [ ] read API는 `OperatorJwtGuard`, mutation API는 `OperatorJwtGuard + OperatorSuperAdminGuard`를 서버에서 적용한다.
- [ ] 다음 endpoint를 OpenAPI와 구현에 맞춘다.

```text
GET  /admin/members/:userId/refund-options
POST /admin/refunds/preview
POST /admin/refunds
GET  /admin/refunds
GET  /admin/refunds/:refundCaseId
POST /admin/refunds/:refundCaseId/retry
POST /admin/refunds/:refundCaseId/requery
POST /admin/refunds/:refundCaseId/manual-cancellation-verification
POST /admin/refunds/:refundCaseId/retry-internal
POST /admin/refunds/:refundCaseId/void
POST /admin/refunds/:refundCaseId/link-external-cancellation
```

- [ ] `POST /admin/refunds`는 환불 건·잠금을 저장하고 `202 Accepted` 성격의 processing 응답을 반환한다. 브라우저 요청 안에서 모든 토스 호출 완료를 보장하지 않는다.
- [ ] DTO는 UUID, 원 단위 정수, 필수 사유, 선택 메모 길이를 whitelist validation한다.
- [ ] 응답에서 paymentKey 전체, customerKey, secret, billingKey, raw provider payload를 제외한다.
- [ ] 생성·실행·재시도·수동 검증 관리자 ID가 이력에 남는지 검증한다.

```bash
npm test -- --runInBand src/modules/payments/presentation/admin-payment-refunds.controller.spec.ts src/modules/payments/presentation/payments-openapi-contract.spec.ts src/modules/payments/payments.module.spec.ts
npm run build
```

Review checkpoint: 일반 운영자와 최고 관리자 권한표를 API 테스트로 확인한다.

## Task 14 — 회원·고객 조회 API에 환불 상태 포함

**Files**

- Modify: `clipper_web_api/src/modules/members/domain/member.model.ts`
- Modify: `clipper_web_api/src/modules/members/application/members.service.ts`
- Modify: `clipper_web_api/src/modules/members/application/members.service.spec.ts`
- Modify: `clipper_web_api/src/modules/members/members.module.ts`
- Modify: `clipper_web_api/src/modules/members/presentation/dto/list-members-query.dto.ts`
- Modify: `clipper_web_api/src/modules/members/presentation/dto/list-members-query.dto.spec.ts`
- Modify: `clipper_web_api/src/modules/members/presentation/members.controller.ts`
- Modify: `clipper_web_api/src/modules/members/presentation/members.controller.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/payments.module.ts`
- Modify: `clipper_web_api/src/modules/payments/payments.module.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/domain/subscriptions.repository.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/typeorm-subscriptions.repository.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/typeorm-subscriptions.repository.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/domain/payment-refunds.repository.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/typeorm-payment-refunds.repository.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/typeorm-payment-refunds.repository.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/application/payment-history.service.ts`
- Modify: `clipper_web_api/src/modules/payments/application/payment-history.service.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/presentation/payment-history.controller.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/application/subscription-payments.service.ts`
- Modify: `clipper_web_api/src/modules/payments/presentation/subscriptions.controller.spec.ts`
- Modify: `clipper_web_api/src/modules/credits/application/credit-grants.service.ts`
- Modify: `clipper_web_api/docs/api/openapi.yaml`
- Modify: `clipper_web_api/src/modules/payments/presentation/payments-openapi-contract.spec.ts`

- [ ] 관리자 회원 목록에 구독 상태, 현재 혜택 월 종료, 다음 결제, 전체 사용 가능 크레딧, 결제/환불 문제 여부를 추가하는 실패 테스트를 작성한다. 현재의 access grant를 정기구독 사실로 간주하지 않고 `SubscriptionsRepository`의 실제 구독을 기준으로 조합한다.
- [ ] 페이지의 사용자 ID 묶음에 대해 구독과 환불 문제 상태를 한 번씩 조회하는 batch repository method를 추가해 회원마다 query하는 N+1 구조를 만들지 않는다.
- [ ] 회원 filter는 `all`, 현재 구독 중, 다음 결제 취소, 결제 실패/중단, 종료/구독 없음, 결제·환불 확인 필요를 서버 query로 처리한다. 기존 access grant의 `scheduled` 상태를 정기구독 상태 filter로 재사용하지 않는다.
- [ ] 회원 상세용 API가 구독·크레딧 지급 건·결제·환불을 별도 section으로 반환하도록 한다. 기존 수동 연장·크레딧 조정 endpoint와 환불을 합치지 않는다.
- [ ] 고객 결제내역 항목에 다음 필드를 추가한다.

```ts
originalAmountKrw: number;
refundedAmountKrw: number;
remainingAmountKrw: number;
refundStatus: 'none' | 'processing' | 'partial' | 'full' | 'attention_required';
refundCompletedAt: string | null;
```

- [ ] 고객 구독 응답에 `refundProcessing`, `refundEndAt`, `refundEndMode`, `nextBillingStopped`를 추가한다.
- [ ] 고객 크레딧 지급 목록에서 `refund_locked`를 “환불 처리 중”으로 보여주되 사용 가능 잔액에는 합산하지 않는다.
- [ ] 내부 attempt/error/provider 상세는 고객 응답에서 제외한다.

```bash
npm test -- --runInBand src/modules/members/application/members.service.spec.ts src/modules/payments/application/payment-history.service.spec.ts src/modules/payments/presentation/payment-history.controller.spec.ts src/modules/payments/presentation/subscriptions.controller.spec.ts src/modules/credits/application/credit-grants.service.spec.ts src/modules/payments/presentation/payments-openapi-contract.spec.ts
npm run build
```

Review checkpoint: Admin 상세 응답과 Customer 응답의 정보 노출 차이를 검토한다.

## Task 15 — 환불 백엔드 통합·동시성 테스트

**Files**

- Create: `clipper_web_api/test/payment-refunds.e2e-spec.ts`
- Create: `clipper_web_api/test/payment-refund-concurrency.e2e-spec.ts`
- Add test fixtures under: `clipper_web_api/test/fixtures/toss-payments/`

- [ ] 신규 disposable DB에서 다음 시나리오를 자동화한다.

- 월간 미사용 기본 결제 + 2개 상향 결제 모두 전액 취소
- 월간 기본 또는 상향 크레딧 일부 사용 시 생성 차단
- 무료 체험만 사용했을 때 월간 환불 허용
- 연간 현재 월 미사용 부분 취소 + 즉시 종료
- 연간 현재 월 사용 부분 취소 + 다음 혜택 월 종료
- 추가 구매 미사용 전액 취소
- 추가 구매 일부 사용·만료 차단
- 두 관리자의 같은 결제 동시 생성
- 환불 미리보기와 유료 동작 차감 동시 실행
- 월별 크레딧 지급·자동 갱신·예약 변경과 환불 동시 실행
- 첫 취소 성공, 두 번째 timeout, 조회 후 완료
- 첫 취소 성공, 두 번째 명확한 실패, 수동 취소 후 검증
- 토스 전부 성공, 내부 transaction 1회 실패, 내부만 재처리
- 외부 dashboard 취소 발견, 자동 내부 변경 없음

- [ ] 실제 네트워크는 차단한 fake provider로 전체 suite를 먼저 통과시킨다.
- [ ] 전체 API 테스트와 build를 실행한다.

```bash
cd /Users/jina/project/adlight/.worktrees/clipper_web_api-toss-payments-pg-integration
npm test -- --runInBand
npm run test:e2e -- --runInBand
npm run build
```

- [ ] test log에 토스 secret, access token, billingKey, 전체 paymentKey가 나타나지 않는지 검색한다.
- [ ] 사용자 검토 전 stage·commit·push하지 않는다.

## Task 16 — 관리자 환불 상세에 안전한 시도·내부 처리 이력 제공

**Files**

- Modify: `clipper_web_api/src/modules/payments/domain/payment-refunds.repository.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/typeorm-payment-refunds.repository.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/typeorm-payment-refunds.repository.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/application/payment-refund-query.service.ts`
- Modify: `clipper_web_api/src/modules/payments/application/payment-refund-query.service.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/presentation/dto/list-payment-refunds-query.dto.ts`
- Modify: `clipper_web_api/src/modules/payments/presentation/dto/list-payment-refunds-query.dto.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/presentation/admin-payment-refunds.controller.ts`
- Modify: `clipper_web_api/src/modules/payments/presentation/admin-payment-refunds.controller.spec.ts`
- Modify: `clipper_web_api/docs/api/openapi.yaml`
- Modify: `clipper_web_api/src/modules/payments/presentation/payments-openapi-contract.spec.ts`

- [ ] 관리자 환불 상세 응답 실패 테스트를 먼저 작성한다.
- [ ] 환불 건에 속한 결제 취소 시도를 생성 시각과 ID의 안정된 오름차순으로 조회한다.
- [ ] 환불 건의 내부 처리 이력을 생성 시각과 ID의 안정된 오름차순으로 조회한다.
- [ ] 관리자 상세 응답에 `attempts`와 `internalEvents`를 추가한다.
- [ ] 결제 취소 시도에는 시도 ID, 환불 항목 ID, 종류, 결과, 관리자 ID, 안전한 provider code/message, 취소 금액, 생성 시각만 노출한다.
- [ ] 내부 처리 이력에는 이력 ID, event type, 결과, 안전한 error code/message, 생성 시각만 노출한다.
- [ ] 전체 paymentKey, billingKey, customerKey, idempotency key, provider transaction key, 원문 provider payload, 내부 before/after snapshot, 원문 예외 메시지는 응답과 OpenAPI에서 제외한다.
- [ ] 전체 환불 탭의 서버 필터를 위해 선택적 `viewStatus`를 추가한다. 값은 `processing`, `partially_completed`, `manual_action_required`, `internal_retry_required`, `completed`로 고정한다.
- [ ] `processing`은 금전 상태 `pending` 또는 `processing`, `partially_completed`와 `manual_action_required`는 같은 금전 상태, `internal_retry_required`는 종료되지 않은 환불 건의 내부 상태 `retry_required`, `completed`는 금전·내부 상태가 모두 `completed`인 건만 반환한다.
- [ ] 기존 `moneyStatus` filter는 유지하되 `moneyStatus`와 `viewStatus`를 동시에 보내면 400으로 거부한다.
- [ ] 기존 상세 endpoint를 확장하며 새 endpoint나 mutation을 추가하지 않는다.
- [ ] repository, query, OpenAPI 계약 테스트와 build를 실행한다.

```bash
npm test -- --runInBand src/modules/payments/infrastructure/typeorm-payment-refunds.repository.spec.ts src/modules/payments/application/payment-refund-query.service.spec.ts src/modules/payments/presentation/dto/list-payment-refunds-query.dto.spec.ts src/modules/payments/presentation/admin-payment-refunds.controller.spec.ts src/modules/payments/presentation/payments-openapi-contract.spec.ts
npm run build
```

Review checkpoint: Admin 환불 상세가 UI의 두 timeline을 구성할 수 있으면서 provider·credential·내부 snapshot을 노출하지 않는지 확인한다.

## 완료 기준

- 모든 환불 종류와 종료 방식이 domain 테스트로 고정된다.
- 원결제 성공 상태와 환불 상태를 별도로 조회할 수 있다.
- 다중 결제 취소에 부분 성공 상태가 존재하고 안전하게 이어서 처리할 수 있다.
- 불확실한 토스 결과를 실패로 단정하거나 새 키로 성급히 재호출하지 않는다.
- 수동 취소는 토스 재조회로 검증된다.
- 환불 잠금과 유료 동작 차감이 같은 지급 건을 동시에 소비하지 못한다.
- 토스 완료 후 내부 실패를 토스 재호출 없이 복구한다.
- 일반 운영자는 mutation API를 호출할 수 없다.
- 기존 migration, 기존 DB, 운영 토스 환경에 변경이 없다.
