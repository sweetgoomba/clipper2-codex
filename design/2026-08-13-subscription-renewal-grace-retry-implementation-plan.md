# Subscription Renewal Grace And Retry Implementation Plan

> **공급자 전환 기록 (2026-08-13):** 유예기간, 자동·수동 재시도 순번, 미정산 결제 복구, fulfillment 정책은 유지한다. 실제 결제 승인·상태 조회·빌링키 처리는 현재 토스페이 직접 adapter에 연결돼 있으므로 토스페이먼츠 PG 전환 시 재검증·교체한다. 구현은 전체 기능 브랜치에 보존하며 현재 경계는 [`2026-08-13-toss-pay-direct-to-toss-payments-pg-handoff.md`](../records/sessions/2026-08-13-toss-pay-direct-to-toss-payments-pg-handoff.md)를 따른다.

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 갱신 결제 최초 실패 후 3일 동안 기존 등급 이용을 유지하고 `D+1`, `D+2`에 자동 재시도하며, 이 일 단위 정책을 관리자 페이지에서 안전하게 변경할 수 있게 한다.

**Architecture:** 관리자 DB의 단일 정책 레코드를 다음 실패 회차의 원본으로 사용하고, 최초 실패 시 구독에 유예 종료일과 재시도 일정을 스냅샷한다. 구독 이용권의 종료일을 유예 종료일까지 연장하되 다음 크레딧 지급일은 비워 미납 회차 크레딧을 막는다. 결제 성공은 기존 멱등 주문과 fulfillment 흐름으로 복구하고, 유예 종료 시 구독과 이용권을 함께 종료한다.

**Tech Stack:** NestJS 11, TypeScript 5.7, TypeORM raw SQL repositories, PostgreSQL, Jest 30, Angular 19 standalone components/signals, Jasmine/Karma, Docker Compose.

## Global Constraints

- 모든 로컬 설치·빌드·테스트는 Node.js 24에서 실행한다.
- API, 고객 웹, 관리자 웹, 인프라는 각 저장소의 기존 `feat/access-credit-system-replacement` 브랜치에서 작업한다.
- `.codex` 저장소는 별도 기능 브랜치를 만들지 않고 `main`만 사용한다.
- 최초 운영값은 유예기간 `3일`, 최초 실패일 기준 자동 재시도 `[1, 2]`일이다.
- 관리자 입력은 일 단위만 지원하고 유예기간은 `1~30일`, 재시도는 최대 5회로 제한한다.
- 재시도 일수는 양의 정수·중복 없음·오름차순이며 모두 유예기간보다 작아야 한다.
- 빈 재시도 목록은 유예기간만 유지하고 자동 재시도하지 않는다는 뜻이다.
- 시간·분 단위 반복, 반복 횟수 기반 일정 생성, Cron 입력, 무제한 재시도는 구현하지 않는다.
- 정책 변경은 변경 이후 처음 실패한 회차에만 적용하고 이미 `past_due`인 회차에는 소급하지 않는다.
- 사용자의 직접 재결제 실패는 자동 재시도 순번과 예약 시각을 바꾸지 않는다.
- 유예 중에는 직전 등급 플러그인과 만료되지 않은 기존 크레딧만 사용하며 새 회차 크레딧은 결제 복구 전까지 지급하지 않는다.
- 기존 결제 주문 멱등키, 결제 상태 조회, fulfillment 멱등성은 유지하며 같은 회차에 새 주문을 만들지 않는다.
- 설정은 DB를 단일 기준으로 사용하며 `SUBSCRIPTION_RETRY_DELAYS_MINUTES` 환경변수는 제거한다.
- API 계약은 `clipper_web_api/docs/api/openapi.yaml`을 먼저 수정하고 고객·관리자 모델을 동일하게 맞춘다.
- 이번 계획은 결제수단 재등록 화면, 이메일·SMS 알림, Toss 오류코드별 영구·일시 실패 분류를 추가하지 않는다. 정해진 두 번의 재시도와 웹 내 상태 안내만 구현한다.

---

### Task 1: 갱신 실패 정책 API 계약 고정

**Files:**
- Modify: `clipper_web_api/docs/api/openapi.yaml`
- Modify: `clipper_web_api/docs/api/README.md`

**Interfaces:**
- Produces: `SubscriptionRenewalPolicy`, `UpdateSubscriptionRenewalPolicyRequest`, 확장된 `Subscription` 스키마.
- Produces: `GET /admin/subscription-renewal-policy`, `PUT /admin/subscription-renewal-policy`.
- Consumes: 기존 `bearerAuth`, `Subscription` 계약.

- [ ] **Step 1: 관리자 정책과 사용자 구독 응답 계약을 먼저 추가한다**

```yaml
SubscriptionRenewalPolicy:
  type: object
  additionalProperties: false
  required: [gracePeriodDays, retryDays, updatedAt, updatedBy]
  properties:
    gracePeriodDays: { type: integer, minimum: 1, maximum: 30 }
    retryDays:
      type: array
      maxItems: 5
      uniqueItems: true
      items: { type: integer, minimum: 1 }
    updatedAt: { type: string, format: date-time }
    updatedBy: { type: [string, 'null'], format: uuid }

UpdateSubscriptionRenewalPolicyRequest:
  type: object
  additionalProperties: false
  required: [gracePeriodDays, retryDays]
  properties:
    gracePeriodDays: { type: integer, minimum: 1, maximum: 30 }
    retryDays:
      type: array
      maxItems: 5
      uniqueItems: true
      items: { type: integer, minimum: 1 }
```

`Subscription.status`에 `stopped`를 추가하고 응답 필수 필드에 다음을 추가한다.

```yaml
firstPaymentFailedAt: { type: [string, 'null'], format: date-time }
graceEndsAt: { type: [string, 'null'], format: date-time }
retryAt: { type: [string, 'null'], format: date-time }
```

- [ ] **Step 2: 관리자 엔드포인트를 계약에 추가한다**

```yaml
/admin/subscription-renewal-policy:
  get:
    operationId: adminGetSubscriptionRenewalPolicy
    tags: [payments]
    security: [{ bearerAuth: [] }]
    responses:
      '200':
        content:
          application/json:
            schema: { $ref: '#/components/schemas/SubscriptionRenewalPolicy' }
  put:
    operationId: adminUpdateSubscriptionRenewalPolicy
    tags: [payments]
    security: [{ bearerAuth: [] }]
    requestBody:
      required: true
      content:
        application/json:
          schema: { $ref: '#/components/schemas/UpdateSubscriptionRenewalPolicyRequest' }
    responses:
      '200':
        content:
          application/json:
            schema: { $ref: '#/components/schemas/SubscriptionRenewalPolicy' }
      '400': { description: Invalid grace period or retry-day sequence. }
      '401': { description: Missing or invalid operator JWT. }
```

- [ ] **Step 3: API 계약 설명에 정책 적용 시점을 명시한다**

`docs/api/README.md`의 결제 계약 설명에 다음을 기록한다.

```text
The renewal policy is read from the admin database when an active subscription first enters past_due. The selected grace period and retry days are copied to that subscription recovery cycle and are not recalculated when an operator later changes the default policy.
```

- [ ] **Step 4: OpenAPI 문법과 계약을 검증한다**

Run: `npx --yes @redocly/cli@latest lint docs/api/openapi.yaml`

Expected: 파싱 오류와 새 스키마 참조 오류가 없고, 기존 경고 수가 증가하지 않는다.

- [ ] **Step 5: 계약 변경을 커밋한다**

```bash
git add docs/api/openapi.yaml docs/api/README.md
git commit -m "docs: define subscription renewal recovery API"
```

### Task 2: 정책·실패 회차·감사 이력을 저장하는 DB 구조 추가

**Files:**
- Create: `clipper_web_api/src/core/database/migrations/admin/1787100000000-CreateSubscriptionRenewalPolicy.ts`
- Create: `clipper_web_api/src/core/database/migrations/admin/1787100000000-CreateSubscriptionRenewalPolicy.spec.ts`
- Modify: `clipper_web_api/src/core/database/admin.datasource.ts`
- Modify: `clipper_web_api/src/core/database/admin.datasource.spec.ts`

**Interfaces:**
- Produces table: `subscription_renewal_policies` singleton row `id = 1`.
- Produces table: `subscription_renewal_policy_events` immutable before/after audit.
- Produces subscription columns: `first_payment_failed_at`, `grace_ends_at`, `retry_days_snapshot`, `next_retry_index`.
- Produces subscription status: `stopped`.

- [ ] **Step 1: 실패하는 마이그레이션 계약 테스트를 작성한다**

```ts
it('seeds a three-day grace with D+1 and D+2 retries and stores cycle snapshots', async () => {
  await new CreateSubscriptionRenewalPolicy1787100000000().up(runner);
  const sql = statements.join(' ').replace(/\s+/g, ' ');
  expect(sql).toContain('CREATE TABLE subscription_renewal_policies');
  expect(sql).toContain("VALUES (1, 3, ARRAY[1, 2]::int[]");
  expect(sql).toContain('CREATE TABLE subscription_renewal_policy_events');
  expect(sql).toContain('first_payment_failed_at timestamptz');
  expect(sql).toContain('grace_ends_at timestamptz');
  expect(sql).toContain('retry_days_snapshot int[]');
  expect(sql).toContain('next_retry_index int');
  expect(sql).toContain("'stopped'");
});
```

- [ ] **Step 2: 테스트가 구현 부재로 실패하는지 확인한다**

Run: `npm test -- --runInBand --runTestsByPath src/core/database/migrations/admin/1787100000000-CreateSubscriptionRenewalPolicy.spec.ts`

Expected: migration module을 찾지 못해 FAIL.

- [ ] **Step 3: 정책과 감사 테이블을 생성한다**

마이그레이션 `up()`에 다음 구조를 사용한다.

```sql
CREATE TABLE subscription_renewal_policies (
  id smallint PRIMARY KEY CHECK (id = 1),
  grace_period_days int NOT NULL CHECK (grace_period_days BETWEEN 1 AND 30),
  retry_days int[] NOT NULL CHECK (
    cardinality(retry_days) <= 5
    AND 0 < ALL(retry_days)
    AND grace_period_days > ALL(retry_days)
  ),
  updated_by uuid REFERENCES operators(id) ON DELETE SET NULL,
  updated_at timestamptz NOT NULL DEFAULT now()
);
INSERT INTO subscription_renewal_policies (
  id, grace_period_days, retry_days, updated_by
) VALUES (1, 3, ARRAY[1, 2]::int[], NULL);

CREATE TABLE subscription_renewal_policy_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  operator_id uuid NOT NULL REFERENCES operators(id) ON DELETE RESTRICT,
  previous_grace_period_days int NOT NULL,
  previous_retry_days int[] NOT NULL,
  grace_period_days int NOT NULL,
  retry_days int[] NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IDX_subscription_renewal_policy_events_created
ON subscription_renewal_policy_events(created_at DESC, id DESC);
```

- [ ] **Step 4: 구독 실패 회차 상태와 `stopped` 상태를 추가한다**

```sql
ALTER TABLE subscriptions
  ADD COLUMN first_payment_failed_at timestamptz,
  ADD COLUMN grace_ends_at timestamptz,
  ADD COLUMN retry_days_snapshot int[],
  ADD COLUMN next_retry_index int;

ALTER TABLE subscriptions DROP CONSTRAINT subscriptions_status_check;
ALTER TABLE subscriptions ADD CONSTRAINT subscriptions_status_check CHECK (
  status IN (
    'pending', 'active', 'past_due', 'cancel_at_period_end',
    'canceled', 'ended', 'stopped'
  )
);

-- 이 기능이 출시되기 전 개발 DB의 구형 past_due 행은 recovery snapshot이
-- 없으므로 새 정책을 소급 추정하지 않고 중지 상태로 정리한다.
UPDATE subscriptions
SET status = 'stopped', next_billing_at = NULL, retry_at = NULL,
    billing_key_removal_status = CASE
      WHEN billing_key_enc IS NULL THEN billing_key_removal_status
      ELSE 'pending'
    END,
    updated_at = now()
WHERE status = 'past_due';

ALTER TABLE subscriptions ADD CONSTRAINT subscriptions_recovery_state_check CHECK (
  status <> 'past_due' OR (
    first_payment_failed_at IS NOT NULL
    AND grace_ends_at IS NOT NULL
    AND retry_days_snapshot IS NOT NULL
    AND next_retry_index IS NOT NULL
  )
);
```

기존 due index는 `retry_at`을 포함하도록 교체한다.

```sql
DROP INDEX IDX_subscriptions_due_billing;
CREATE INDEX IDX_subscriptions_due_billing
ON subscriptions(COALESCE(retry_at, next_billing_at), id)
WHERE status IN ('active', 'past_due');
```

`down()`은 새 index/constraint/columns/table을 역순으로 제거하고 기존 status constraint와 due index를 복원한다.

- [ ] **Step 5: datasource migration 목록과 순서를 검증한다**

`admin.datasource.ts` entities는 늘리지 않고 새 migration만 마지막에 등록한다. `admin.datasource.spec.ts`에는 다음 기대값을 추가한다.

```ts
expect(migrationNames.at(-1)).toBe(
  'CreateSubscriptionRenewalPolicy1787100000000',
);
```

- [ ] **Step 6: 마이그레이션 테스트를 실행한다**

Run: `npm test -- --runInBand --runTestsByPath src/core/database/migrations/admin/1787100000000-CreateSubscriptionRenewalPolicy.spec.ts src/core/database/admin.datasource.spec.ts`

Expected: PASS.

- [ ] **Step 7: DB 구조를 커밋한다**

```bash
git add src/core/database/migrations/admin/1787100000000-CreateSubscriptionRenewalPolicy.ts src/core/database/migrations/admin/1787100000000-CreateSubscriptionRenewalPolicy.spec.ts src/core/database/admin.datasource.ts src/core/database/admin.datasource.spec.ts
git commit -m "feat: persist subscription renewal recovery policy"
```

### Task 3: 정책 저장소와 관리자 API 구현

**Files:**
- Create: `clipper_web_api/src/modules/payments/domain/subscription-renewal-policy.model.ts`
- Create: `clipper_web_api/src/modules/payments/domain/subscription-renewal-policies.repository.ts`
- Create: `clipper_web_api/src/modules/payments/infrastructure/typeorm-subscription-renewal-policies.repository.ts`
- Create: `clipper_web_api/src/modules/payments/infrastructure/typeorm-subscription-renewal-policies.repository.spec.ts`
- Create: `clipper_web_api/src/modules/payments/application/subscription-renewal-policy.service.ts`
- Create: `clipper_web_api/src/modules/payments/application/subscription-renewal-policy.service.spec.ts`
- Create: `clipper_web_api/src/modules/payments/presentation/dto/update-subscription-renewal-policy.dto.ts`
- Create: `clipper_web_api/src/modules/payments/presentation/admin-subscription-renewal-policy.controller.ts`
- Create: `clipper_web_api/src/modules/payments/presentation/admin-subscription-renewal-policy.controller.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/payments.module.ts`

**Interfaces:**
- Produces type: `SubscriptionRenewalPolicy { gracePeriodDays, retryDays, updatedAt, updatedBy }`.
- Produces repository: `current(manager?)`, `update(operatorId, input)`.
- Produces service: `current()`, `update(operatorId, input)`.
- Consumes: `OperatorJwtGuard`, `AdminTransactionRunner`.

- [ ] **Step 1: 정책 유효성 테스트를 먼저 작성한다**

```ts
it.each([
  [{ gracePeriodDays: 0, retryDays: [1] }, 'INVALID_GRACE_PERIOD'],
  [{ gracePeriodDays: 31, retryDays: [1] }, 'INVALID_GRACE_PERIOD'],
  [{ gracePeriodDays: 3, retryDays: [2, 1] }, 'INVALID_RETRY_DAYS'],
  [{ gracePeriodDays: 3, retryDays: [1, 1] }, 'INVALID_RETRY_DAYS'],
  [{ gracePeriodDays: 3, retryDays: [1, 2, 3] }, 'INVALID_RETRY_DAYS'],
  [{ gracePeriodDays: 10, retryDays: [1, 2, 3, 4, 5, 6] }, 'INVALID_RETRY_DAYS'],
])('rejects unsafe policy %p', async (input, code) => {
  await expect(service.update(operatorId, input)).rejects.toMatchObject({
    message: code,
  });
});

it('accepts an empty retry list and persists an audit event', async () => {
  await expect(
    service.update(operatorId, { gracePeriodDays: 3, retryDays: [] }),
  ).resolves.toMatchObject({ gracePeriodDays: 3, retryDays: [] });
});
```

- [ ] **Step 2: 정책 모델과 저장소 계약을 추가한다**

```ts
export interface SubscriptionRenewalPolicy {
  gracePeriodDays: number;
  retryDays: number[];
  updatedAt: Date;
  updatedBy: string | null;
}

export interface UpdateSubscriptionRenewalPolicyInput {
  gracePeriodDays: number;
  retryDays: number[];
}

export abstract class SubscriptionRenewalPoliciesRepository {
  abstract bind(manager: EntityManager): SubscriptionRenewalPoliciesRepository;
  abstract current(): Promise<SubscriptionRenewalPolicy>;
  abstract update(
    operatorId: string,
    input: UpdateSubscriptionRenewalPolicyInput,
  ): Promise<SubscriptionRenewalPolicy>;
}
```

- [ ] **Step 3: singleton row 잠금과 감사 이력을 같은 트랜잭션에 구현한다**

`TypeOrmSubscriptionRenewalPoliciesRepository.update()`는 다음 순서로 실행한다.

```sql
SELECT * FROM subscription_renewal_policies WHERE id = 1 FOR UPDATE;
UPDATE subscription_renewal_policies
SET grace_period_days = $1, retry_days = $2, updated_by = $3, updated_at = now()
WHERE id = 1
RETURNING *;
INSERT INTO subscription_renewal_policy_events (
  operator_id, previous_grace_period_days, previous_retry_days,
  grace_period_days, retry_days
) VALUES ($3, $4, $5, $1, $2);
```

입력값이 현재값과 같으면 `UPDATE`와 감사 이벤트를 만들지 않고 현재값을 반환한다. repository spec은 배열 변환, `FOR UPDATE`, before/after audit 파라미터를 검증한다.

- [ ] **Step 4: 서비스에서 일 단위 안전 범위를 강제한다**

```ts
private validate(input: UpdateSubscriptionRenewalPolicyInput): void {
  if (
    !Number.isInteger(input.gracePeriodDays) ||
    input.gracePeriodDays < 1 ||
    input.gracePeriodDays > 30
  ) throw new BadRequestException('INVALID_GRACE_PERIOD');
  if (input.retryDays.length > 5) {
    throw new BadRequestException('INVALID_RETRY_DAYS');
  }
  for (let index = 0; index < input.retryDays.length; index += 1) {
    const day = input.retryDays[index];
    const previous = input.retryDays[index - 1];
    if (
      !Number.isInteger(day) || day < 1 || day >= input.gracePeriodDays ||
      (previous !== undefined && day <= previous)
    ) throw new BadRequestException('INVALID_RETRY_DAYS');
  }
}
```

유효성 검사를 통과한 뒤 `AdminTransactionRunner` 안에서 bound repository의 `update()`를 호출한다.

- [ ] **Step 5: DTO와 인증된 관리자 controller를 구현한다**

```ts
export class UpdateSubscriptionRenewalPolicyDto {
  @IsInt() @Min(1) @Max(30)
  gracePeriodDays!: number;

  @IsArray() @ArrayMaxSize(5) @ArrayUnique() @IsInt({ each: true }) @Min(1, { each: true })
  retryDays!: number[];
}
```

```ts
@Controller('admin/subscription-renewal-policy')
@UseGuards(OperatorJwtGuard)
@UsePipes(new ValidationPipe({ whitelist: true, transform: true }))
export class AdminSubscriptionRenewalPolicyController {
  @Get() current() { return this.policies.current(); }

  @Put()
  update(@Req() request: Request, @Body() dto: UpdateSubscriptionRenewalPolicyDto) {
    const operator = request.user as AuthenticatedOperator;
    return this.policies.update(operator.id, dto);
  }
}
```

controller spec은 guard metadata, operator ID 전달, DTO 외 필드 제거를 검증한다.

- [ ] **Step 6: module provider와 controller를 등록하고 관련 테스트를 실행한다**

Run: `npm test -- --runInBand --runTestsByPath src/modules/payments/infrastructure/typeorm-subscription-renewal-policies.repository.spec.ts src/modules/payments/application/subscription-renewal-policy.service.spec.ts src/modules/payments/presentation/admin-subscription-renewal-policy.controller.spec.ts`

Expected: PASS.

- [ ] **Step 7: 정책 API를 커밋한다**

```bash
git add src/modules/payments
git commit -m "feat: manage subscription renewal policy"
```

### Task 4: 구독 실패 회차 스냅샷과 자동 재시도 순번 구현

**Files:**
- Modify: `clipper_web_api/src/modules/payments/domain/subscription.model.ts`
- Modify: `clipper_web_api/src/modules/payments/domain/subscription-retry-policy.ts`
- Modify: `clipper_web_api/src/modules/payments/domain/subscription-retry-policy.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/domain/subscriptions.repository.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/subscription.entity.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/typeorm-subscriptions.repository.ts`
- Modify: `clipper_web_api/src/modules/payments/infrastructure/typeorm-subscriptions.repository.spec.ts`

**Interfaces:**
- Produces: `startRecoveryCycle(failedAt, policy)`, `nextRetryAt(cycle, nextIndex)` pure functions.
- Produces repository methods: `beginPastDue`, `advancePastDueRetry`, `markStopped`, `findLatestByUserId`.
- Consumes: `SubscriptionRenewalPolicy` from Task 3.

- [ ] **Step 1: 절대 시점 일정 계산 테스트를 작성한다**

```ts
it('builds D+1 and D+2 from the first failure rather than from each retry', () => {
  const failedAt = new Date('2026-08-13T10:00:00.000Z');
  const cycle = startRecoveryCycle(failedAt, {
    gracePeriodDays: 3,
    retryDays: [1, 2],
  });
  expect(cycle.graceEndsAt.toISOString()).toBe('2026-08-16T10:00:00.000Z');
  expect(cycle.retryAt?.toISOString()).toBe('2026-08-14T10:00:00.000Z');
  expect(nextRetryAt(cycle, 1)?.toISOString()).toBe('2026-08-15T10:00:00.000Z');
  expect(nextRetryAt(cycle, 2)).toBeNull();
});
```

기존 환경변수 파싱 테스트는 삭제하고 빈 목록과 최대 5개 일정 계산을 추가한다.

- [ ] **Step 2: 계산 테스트가 기존 누적 지연 구현에서 실패하는지 확인한다**

Run: `npm test -- --runInBand --runTestsByPath src/modules/payments/domain/subscription-retry-policy.spec.ts`

Expected: 절대 `D+2` 기대값 또는 새 함수 부재로 FAIL.

- [ ] **Step 3: 구독 모델과 순수 일정 함수를 구현한다**

```ts
export interface SubscriptionRecoveryCycle {
  firstPaymentFailedAt: Date;
  graceEndsAt: Date;
  retryDaysSnapshot: number[];
  nextRetryIndex: number;
  retryAt: Date | null;
}

export function startRecoveryCycle(
  failedAt: Date,
  policy: Pick<SubscriptionRenewalPolicy, 'gracePeriodDays' | 'retryDays'>,
): SubscriptionRecoveryCycle {
  return {
    firstPaymentFailedAt: failedAt,
    graceEndsAt: addDays(failedAt, policy.gracePeriodDays),
    retryDaysSnapshot: [...policy.retryDays],
    nextRetryIndex: 0,
    retryAt: policy.retryDays[0] === undefined
      ? null
      : addDays(failedAt, policy.retryDays[0]),
  };
}
```

`Subscription`에 네 recovery 필드를 추가하고 `SUBSCRIPTION_STATUSES`에 `stopped`를 추가한다.

- [ ] **Step 4: repository 상태 전이 계약을 구현한다**

```ts
abstract beginPastDue(
  id: string,
  cycle: SubscriptionRecoveryCycle,
): Promise<Subscription>;
abstract advancePastDueRetry(
  id: string,
  nextRetryIndex: number,
  retryAt: Date | null,
): Promise<Subscription>;
abstract markStopped(id: string, at: Date): Promise<Subscription>;
abstract findLatestByUserId(userId: string): Promise<Subscription | undefined>;
```

SQL 전이 규칙은 다음과 같다.

- `beginPastDue`: `active`만 `past_due`로 바꾸고 네 recovery 필드를 한 번 저장한다.
- `advancePastDueRetry`: `past_due`에서 index와 `retry_at`만 변경하고 최초 실패/유예/스냅샷은 보존한다.
- `markStopped`: `past_due AND grace_ends_at <= at`만 `stopped`로 바꾸고 자동 청구·재시도를 비우며 `billing_key_removal_status = 'pending'`으로 둔다.
- `activate`, `extendPeriod`, `scheduleCancellation`, `markCanceled`, `markEnded`는 recovery 필드를 모두 비운다.
- `findOpenByUserId`는 일반 `stopped`를 제외하되, 유예 종료 전에 시작된 미정산 갱신 주문이 있으면 정산이 끝날 때까지 open으로 취급한다. `findLatestByUserId`는 상태 제한 없이 최신 구독을 반환한다.
- billing key 제거 대상 status에 `stopped`를 추가하되, 미정산 갱신 주문이 있는 `stopped` 구독은 제거 대상에서 제외한다.

- [ ] **Step 5: repository SQL 테스트에 상태 전이와 필드 보존을 추가한다**

```ts
expect(updateSql).toContain("status = 'past_due'");
expect(updateSql).toContain('first_payment_failed_at = $2');
expect(updateSql).toContain('retry_days_snapshot = $4');
expect(stoppedSql).toContain("status = 'stopped'");
expect(stoppedSql).toContain("billing_key_removal_status = 'pending'");
expect(advanceSql).not.toContain('first_payment_failed_at =');
```

- [ ] **Step 6: 도메인과 repository 테스트를 실행한다**

Run: `npm test -- --runInBand --runTestsByPath src/modules/payments/domain/subscription-retry-policy.spec.ts src/modules/payments/infrastructure/typeorm-subscriptions.repository.spec.ts`

Expected: PASS.

- [ ] **Step 7: 실패 회차 상태를 커밋한다**

```bash
git add src/modules/payments/domain src/modules/payments/infrastructure
git commit -m "feat: snapshot subscription renewal recovery cycles"
```

### Task 5: 유예 중 이용권 유지와 미납 회차 크레딧 차단

**Files:**
- Modify: `clipper_web_api/src/modules/access/domain/access.repository.ts`
- Modify: `clipper_web_api/src/modules/access/infrastructure/typeorm-access.repository.ts`
- Modify: `clipper_web_api/src/modules/access/infrastructure/typeorm-access.repository.spec.ts`
- Modify: `clipper_web_api/src/modules/access/application/access-grants.service.ts`
- Modify: `clipper_web_api/src/modules/access/application/access-grants.service.spec.ts`
- Modify: `clipper_web_api/src/modules/access/application/monthly-credit-grant.service.spec.ts`

**Interfaces:**
- Produces repository: `startSubscriptionGrace(id, graceEndsAt)`.
- Produces service: `startSubscriptionGrace({ userId, subscriptionId, graceEndsAt }, manager)`.
- Consumes: 기존 access grant row lock와 `subscription_id` 연결.

- [ ] **Step 1: 유예 시작 시 이용권은 유지하고 다음 크레딧은 막는 테스트를 작성한다**

```ts
it('extends subscription access to grace end without an unpaid credit schedule', async () => {
  const result = await service.startSubscriptionGrace(
    {
      userId: 'user-1',
      subscriptionId: 'subscription-1',
      graceEndsAt: new Date('2026-08-16T10:00:00.000Z'),
    },
    manager,
  );
  expect(repository.startSubscriptionGrace).toHaveBeenCalledWith(
    'grant-1',
    new Date('2026-08-16T10:00:00.000Z'),
  );
  expect(repository.appendEvent).toHaveBeenCalledWith(
    expect.objectContaining({ eventType: 'subscription_grace_started' }),
  );
  expect(result.nextCreditGrantAt).toBeNull();
});
```

- [ ] **Step 2: repository에 원자적인 유예 전이를 구현한다**

```sql
UPDATE user_access_grants
SET status = 'active', ends_at = $2, next_credit_grant_at = NULL,
    ended_at = NULL, ended_reason = NULL, updated_at = now()
WHERE id = $1 AND source = 'subscription'
  AND status IN ('active', 'ended')
RETURNING *;
```

`findBySubscriptionId()`의 `FOR UPDATE`를 그대로 사용하여 월별 지급 스케줄러와 같은 row를 직렬화한다. 월별 지급 스케줄러가 먼저 끝내도 유예 전이가 다시 활성화하고, 유예 전이가 먼저 끝나면 `next_credit_grant_at = NULL`이므로 새 크레딧을 지급하지 않는다.

- [ ] **Step 3: service 이벤트와 멱등 동작을 구현한다**

이미 같은 `graceEndsAt`으로 active/null-next-credit 상태이면 현재 grant를 반환하고 중복 이벤트를 만들지 않는다. 최초 변경에만 다음 payload를 남긴다.

```ts
{
  eventType: 'subscription_grace_started',
  reason: '구독 갱신 결제 실패 유예',
  payload: {
    subscriptionId: input.subscriptionId,
    graceEndsAt: input.graceEndsAt.toISOString(),
  },
}
```

- [ ] **Step 4: 월별 크레딧 서비스 회귀 테스트를 추가한다**

`nextCreditGrantAt: null`, `endsAt: graceEndsAt`인 구독 grant를 처리해도 `credits.grant`와 `endExpired`가 호출되지 않는 테스트를 추가한다.

- [ ] **Step 5: access 관련 테스트를 실행한다**

Run: `npm test -- --runInBand --runTestsByPath src/modules/access/infrastructure/typeorm-access.repository.spec.ts src/modules/access/application/access-grants.service.spec.ts src/modules/access/application/monthly-credit-grant.service.spec.ts`

Expected: PASS.

- [ ] **Step 6: 유예 이용권 구현을 커밋한다**

```bash
git add src/modules/access
git commit -m "feat: preserve subscription access during payment grace"
```

### Task 6: 갱신 실패·자동 재시도·직접 재결제·최종 중지 연결

**Files:**
- Modify: `clipper_web_api/src/modules/payments/application/subscription-renewal.service.ts`
- Modify: `clipper_web_api/src/modules/payments/application/subscription-renewal.service.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/application/payment-recovery.scheduler.ts`
- Modify: `clipper_web_api/src/modules/payments/application/payment-recovery.scheduler.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/application/payment-fulfillment.service.spec.ts`

**Interfaces:**
- Consumes: policy service from Task 3, recovery schedule from Task 4, grace access from Task 5.
- Produces: D+0 → D+1 → D+2 → D+3 state machine.
- Preserves: one renewal order per `subscriptionId + currentPeriodEnd`.

- [ ] **Step 1: 시간축별 실패 테스트를 먼저 작성한다**

다음 네 테스트를 고정 시각으로 작성한다.

```ts
it('D+0 snapshots policy, starts grace, and schedules D+1', async () => {});
it('D+1 automatic failure schedules absolute D+2', async () => {});
it('D+2 automatic failure leaves no automatic retry before D+3', async () => {});
it('manual retry failure preserves the current automatic retry index and time', async () => {});
```

D+0 기대값:

```ts
expect(subscriptions.beginPastDue).toHaveBeenCalledWith(
  'subscription-1',
  expect.objectContaining({
    firstPaymentFailedAt: d0,
    graceEndsAt: d3,
    retryDaysSnapshot: [1, 2],
    nextRetryIndex: 0,
    retryAt: d1,
  }),
);
expect(access.startSubscriptionGrace).toHaveBeenCalledWith(
  expect.objectContaining({ graceEndsAt: d3 }),
  manager,
);
```

- [ ] **Step 2: 기존 환경변수 의존을 제거하고 정책 snapshot을 연결한다**

`SubscriptionRenewalService`에서 `retryDelaysMinutes`, `parseSubscriptionRetryDelays`를 제거하고 `SubscriptionRenewalPolicyService`를 주입한다. 최초 `active` 실패는 현재 DB 정책으로 `startRecoveryCycle()`을 만들고, 같은 transaction에서 다음을 실행한다.

```ts
await orders.markFailed(...);
await subscriptions.beginPastDue(subscription.id, cycle);
await this.access.startSubscriptionGrace({
  userId: subscription.userId,
  subscriptionId: subscription.id,
  graceEndsAt: cycle.graceEndsAt,
}, manager);
await orders.recordEvent({
  eventType: 'subscription_renewal_failed',
  payload: {
    subscriptionId: subscription.id,
    attemptKind: 'initial',
    firstPaymentFailedAt: cycle.firstPaymentFailedAt.toISOString(),
    graceEndsAt: cycle.graceEndsAt.toISOString(),
    retryDays: cycle.retryDaysSnapshot,
    retryAt: cycle.retryAt?.toISOString() ?? null,
    errorCode,
  },
});
```

- [ ] **Step 3: 자동 실패만 다음 순번을 소비하도록 구현한다**

`renew(subscriptionId, now, retryKind)`의 세 번째 인자를 `'scheduled' | 'manual'`로 명시한다. scheduler 기본값은 `'scheduled'`, 사용자 API는 `'manual'`을 전달한다. 실제 승인 선점 시 주문에는 `renewalAttemptKind`, `renewalAttemptedAt`, `renewalAttemptRetryIndex`를 함께 저장하고, 상태 조회 결과를 정산할 때는 호출자가 전달한 값이 아니라 이 스냅샷을 사용한다.

- active 갱신 실패: 새 cycle 시작.
- past_due scheduled 실패: `nextRetryIndex + 1`로 이동하고 최초 실패 시각에 snapshot 일수를 더해 다음 `retryAt` 계산.
- past_due manual 실패: 저장된 `nextRetryIndex`, `retryAt`을 그대로 둠.
- `now >= graceEndsAt`: Toss를 호출하지 않고 `SUBSCRIPTION_GRACE_EXPIRED` conflict.

`TossPayUncertainResultError`와 `payment_pending`은 실패 횟수를 증가시키지 않고 기존 결제 상태 조회 흐름을 유지한다. 불명확 결과의 즉시 상태 조회까지 실패하면 active 구독에는 동일한 recovery cycle과 access grace를 시작하되 주문을 `failed`로 바꾸거나 자동 재시도 index를 소비하지 않는다. 다음 조회에서는 새 결제 승인을 호출하지 않고 먼저 같은 주문번호의 상태를 재조회한다. 조회 결과가 `PAY_COMPLETE`이면 즉시 복구하고, `PAY_FAIL`이면 주문에 저장된 시도가 자동 재시도였을 때만 해당 순번을 소비한다. `payment_pending -> failed` 조건부 전이에 성공한 worker만 순번 이동과 실패 이벤트를 같은 트랜잭션에서 기록한다.

- [ ] **Step 4: 성공 복구가 상태를 비우고 한 번만 지급되는지 검증한다**

기존 fulfillment가 `periodStart = original currentPeriodEnd`에서 access/subscription을 연장하는지 유지한다. `extendPeriod()`가 recovery 필드를 모두 비우는 것을 assertion하고, 같은 paid order 재처리 시 기간 연장·크레딧 지급이 한 번뿐인지 회귀 테스트한다.

- [ ] **Step 5: D+3 최종 중지와 access 종료를 구현한다**

`findExpiredAccessIds()`의 기한을 상태별로 계산한다.

```sql
WHERE (
  s.status IN ('active', 'cancel_at_period_end')
  AND s.current_period_end <= $1
) OR (
  s.status = 'past_due'
  AND s.grace_ends_at <= $1
)
```

`endExpiredAccess()`는 lock 안에서:

- `past_due`: `graceEndsAt`에 access를 끝내고 `markStopped()`.
- `cancel_at_period_end`: `currentPeriodEnd`에 access를 끝내고 `markEnded()`.
- `active`: 기존 paid-period 만료 처리를 유지하되 renewal 처리 후 최신 상태를 다시 읽음.

중지 후 billing-key 제거 scheduler가 `stopped`도 처리하는지 테스트한다.

단, 유예 종료 전에 선점한 주문이 `payment_pending`이거나 `paid`지만 fulfillment가 끝나지 않았다면 구독은 `stopped`로 전환해 이용권을 종료한 뒤에도 해당 주문을 계속 정산한다. 이 동안 billing key 제거와 새 구독 생성은 보류한다. 성공이 확인되면 `stopped`에서도 기간을 원래 기준일에서 연장하고, 최종 실패하면 보류를 해제한다. 월별 크레딧 scheduler가 access를 먼저 `ended`로 만들었더라도 subscription의 `stopped` 전이는 별도로 실행되어야 한다.

- [ ] **Step 6: scheduler 테스트에 D+3 종료 순서를 추가한다**

```ts
expect(renewals.renew).toHaveBeenCalledWith(
  'subscription-1', now, 'scheduled',
);
expect(renewals.endExpiredAccess).toHaveBeenCalledWith(
  'subscription-3', now,
);
```

동일 scheduler process에서 갱신 실패가 먼저 `past_due`/grace로 바뀌고, 그 뒤 expired 조회가 최신 grace 기한을 사용한다는 repository/service 테스트를 추가한다. 배치가 오래 걸려도 각 승인 선점 직전에 현재 시각을 다시 읽어 유예 종료 이후 새 승인을 시작하지 않는 테스트도 포함한다.

- [ ] **Step 7: 갱신과 scheduler 테스트를 실행한다**

Run: `npm test -- --runInBand --runTestsByPath src/modules/payments/application/subscription-renewal.service.spec.ts src/modules/payments/application/payment-recovery.scheduler.spec.ts src/modules/payments/application/payment-fulfillment.service.spec.ts`

Expected: PASS.

- [ ] **Step 8: 갱신 복구 상태 머신을 커밋한다**

```bash
git add src/modules/payments/application src/modules/payments/infrastructure/typeorm-subscriptions.repository.ts
git commit -m "feat: retry failed subscription renewals with grace"
```

### Task 7: 사용자에게 유예·다음 재시도·최종 중지 상태 표시

**Files:**
- Modify: `clipper_web_api/src/modules/payments/application/subscription-payments.service.ts`
- Modify: `clipper_web_api/src/modules/payments/application/subscription-payments.service.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/presentation/subscriptions.controller.spec.ts`
- Modify: `clipper_web_client/src/app/core/api/models.ts`
- Modify: `clipper_web_client/src/app/core/api/mock/mock-data.ts`
- Modify: `clipper_web_client/src/app/features/portal/dashboard/dashboard.component.ts`
- Modify: `clipper_web_client/src/app/features/portal/dashboard/dashboard.component.html`
- Modify: `clipper_web_client/src/app/features/portal/dashboard/dashboard.component.scss`
- Modify: `clipper_web_client/src/app/features/portal/dashboard/dashboard.component.spec.ts`

**Interfaces:**
- Produces safe `SubscriptionView` fields: `firstPaymentFailedAt`, `graceEndsAt`, `retryAt`.
- Produces UI status label: `stopped: 결제 실패로 구독 중지`.
- Consumes: `findLatestByUserId` from Task 4.

- [ ] **Step 1: API safe-view 테스트를 확장한다**

```ts
expect(await service.current('user-1')).toEqual({
  id: 'subscription-1',
  billingProductId: 'product-1',
  planTierId: 'tier-1',
  status: 'past_due',
  currentPeriodStart,
  currentPeriodEnd,
  nextBillingAt,
  cancelAt: null,
  firstPaymentFailedAt: d0,
  graceEndsAt: d3,
  retryAt: d1,
});
expect(view).not.toHaveProperty('billingKeyEnc');
expect(view).not.toHaveProperty('retryDaysSnapshot');
expect(view).not.toHaveProperty('providerUserId');
```

- [ ] **Step 2: 최신 구독 상태를 반환하고 직접 재결제 기한을 검사한다**

`current()`는 `findLatestByUserId()`를 사용하여 `stopped`도 보여준다. `retryCurrent()`는 `past_due`이고 `now < graceEndsAt`일 때만 `'manual'` 재시도를 실행한다.

- [ ] **Step 3: 고객 웹 모델과 mock을 계약에 맞춘다**

```ts
export type SubscriptionStatus =
  | 'pending' | 'active' | 'past_due' | 'cancel_at_period_end'
  | 'canceled' | 'ended' | 'stopped';

export interface SubscriptionView {
  // existing public fields
  firstPaymentFailedAt: string | null;
  graceEndsAt: string | null;
  retryAt: string | null;
}
```

- [ ] **Step 4: dashboard 유예 안내 테스트를 먼저 추가한다**

```ts
it('shows grace end and the next automatic retry for past_due', () => {
  const { fixture } = setup({ subscription: pastDue });
  const text = fixture.nativeElement.textContent;
  expect(text).toContain('이용 가능 기한');
  expect(text).toContain('2026-08-16');
  expect(text).toContain('다음 자동 재시도');
  expect(text).toContain('2026-08-14');
});

it('shows that automatic retry is exhausted while manual retry remains', () => {
  const { fixture } = setup({
    subscription: { ...pastDue, retryAt: null },
  });
  expect(fixture.nativeElement.textContent).toContain('예정된 자동 재시도 없음');
  expect(fixture.nativeElement.querySelector('[data-action="retry-subscription"]')).not.toBeNull();
});
```

- [ ] **Step 5: 기존의 잘못된 paid-period 안내를 grace 안내로 교체한다**

`past_due` 문구를 다음 의미로 렌더링한다.

```text
갱신 결제에 실패했지만 유예기간 동안 기존 등급을 이용할 수 있습니다.
이용 가능 기한: {graceEndsAt}
다음 자동 재시도: {retryAt 또는 예정된 자동 재시도 없음}
```

`stopped`이면 결제 다시 시도 버튼을 숨기고 요금제 페이지에서 새 구독을 시작하라고 안내한다.

- [ ] **Step 6: API와 고객 웹 테스트를 실행한다**

Run API: `npm test -- --runInBand --runTestsByPath src/modules/payments/application/subscription-payments.service.spec.ts src/modules/payments/presentation/subscriptions.controller.spec.ts`

Run client: `npm test -- --watch=false --browsers=ChromeHeadless`

Expected: 모두 PASS.

- [ ] **Step 7: API safe view와 고객 웹을 저장소별로 커밋한다**

```bash
# clipper_web_api
git add src/modules/payments/application/subscription-payments.service.ts src/modules/payments/application/subscription-payments.service.spec.ts src/modules/payments/presentation/subscriptions.controller.spec.ts
git commit -m "feat: expose subscription payment grace status"

# clipper_web_client
git add src/app/core/api src/app/features/portal/dashboard
git commit -m "feat: show subscription payment grace status"
```

### Task 8: 관리자 결제 실패 정책 화면 구현

**Files:**
- Create: `clipper_web_admin/src/app/core/api/subscription-renewal-policy-api.service.ts`
- Create: `clipper_web_admin/src/app/core/api/subscription-renewal-policy-api.service.spec.ts`
- Modify: `clipper_web_admin/src/app/core/api/models.ts`
- Modify: `clipper_web_admin/src/app/core/api/mock/mock-data.ts`
- Modify: `clipper_web_admin/src/app/core/api/mock/mock-api.interceptor.ts`
- Create: `clipper_web_admin/src/app/features/portal/subscription-renewal-policy/subscription-renewal-policy.component.ts`
- Create: `clipper_web_admin/src/app/features/portal/subscription-renewal-policy/subscription-renewal-policy.component.html`
- Create: `clipper_web_admin/src/app/features/portal/subscription-renewal-policy/subscription-renewal-policy.component.scss`
- Create: `clipper_web_admin/src/app/features/portal/subscription-renewal-policy/subscription-renewal-policy.component.spec.ts`
- Modify: `clipper_web_admin/src/app/features/portal/portal.routes.ts`
- Modify: `clipper_web_admin/src/app/features/portal/portal.routes.spec.ts`
- Modify: `clipper_web_admin/src/app/shared/layout/app-header/app-header.component.ts`
- Modify: `clipper_web_admin/src/app/shared/layout/app-header/app-header.component.spec.ts`

**Interfaces:**
- Produces admin route: `/subscription-renewal-policy`.
- Produces service: `getPolicy()`, `updatePolicy(input)`.
- Consumes Task 1 admin API contract.

- [ ] **Step 1: 관리자 API client 테스트를 작성한다**

```ts
service.getPolicy().subscribe();
expect(http.expectOne(`${environment.apiBaseUrl}/admin/subscription-renewal-policy`).request.method)
  .toBe('GET');

service.updatePolicy({ gracePeriodDays: 7, retryDays: [1, 3, 5] }).subscribe();
const request = http.expectOne(`${environment.apiBaseUrl}/admin/subscription-renewal-policy`);
expect(request.request.method).toBe('PUT');
expect(request.request.body).toEqual({ gracePeriodDays: 7, retryDays: [1, 3, 5] });
```

- [ ] **Step 2: 관리자 모델과 API client를 구현한다**

```ts
export interface SubscriptionRenewalPolicy {
  gracePeriodDays: number;
  retryDays: number[];
  updatedAt: string;
  updatedBy: string | null;
}

export type UpdateSubscriptionRenewalPolicy = Pick<
  SubscriptionRenewalPolicy,
  'gracePeriodDays' | 'retryDays'
>;
```

- [ ] **Step 3: 화면 유효성 테스트를 먼저 작성한다**

```ts
it('renders the current 3-day D+1 D+2 policy', () => {
  expect(text()).toContain('유예기간 3일');
  expect(text()).toContain('1일 후');
  expect(text()).toContain('2일 후');
});

it('rejects duplicate, unordered, and out-of-grace retry days before PUT', () => {
  component.gracePeriodDays.set(3);
  component.retryDaysText.set('2, 1');
  component.save();
  expect(api.updatePolicy).not.toHaveBeenCalled();
  expect(component.error()).toContain('오름차순');
});
```

- [ ] **Step 4: 단순한 일 단위 입력 화면을 구현한다**

화면에는 다음 세 영역만 둔다.

- 유예기간 숫자 입력: `1~30`, 단위 `일`.
- 재시도 일수 입력: 쉼표로 구분한 `1, 2` 형식, 도움말 `최초 실패일 기준`.
- 저장 전 미리보기: `D+1 → D+2 → D+3 이용 중지`.

파싱 함수는 공백을 제거한 뒤 빈 문자열은 `[]`로, 그 외에는 10진 양의 정수 배열로 바꾼다. API와 같은 검증을 클라이언트에서도 수행하지만 최종 검증 기준은 서버다. 저장 중 버튼을 비활성화하고 성공/실패 메시지를 `aria-live`로 표시한다.

- [ ] **Step 5: mock, route, header navigation을 연결한다**

`MOCK_SUBSCRIPTION_RENEWAL_POLICY`는 `3`, `[1, 2]`를 반환한다. route와 header에 다음 항목을 추가한다.

```ts
{
  path: 'subscription-renewal-policy',
  loadComponent: () => import(
    './subscription-renewal-policy/subscription-renewal-policy.component'
  ).then((m) => m.SubscriptionRenewalPolicyComponent),
}
```

```ts
{ label: '결제 실패 정책', path: '/subscription-renewal-policy' }
```

- [ ] **Step 6: 관리자 테스트와 빌드를 실행한다**

Run: `npm test -- --watch=false --browsers=ChromeHeadless`

Run: `npm run build`

Expected: PASS, production build 성공.

- [ ] **Step 7: 관리자 화면을 커밋한다**

```bash
git add src/app/core/api src/app/features/portal/subscription-renewal-policy src/app/features/portal/portal.routes.ts src/app/features/portal/portal.routes.spec.ts src/app/shared/layout/app-header
git commit -m "feat: manage subscription renewal recovery policy"
```

### Task 9: 환경변수 이중 기준 제거와 전체 검증

**Files:**
- Modify: `clipper_infra/apps/compose.yml`
- Modify: `clipper_infra/env/stack.dev.env.example`
- Modify: `clipper_infra/env/stack.stage.env.example`
- Modify: `clipper_infra/env/stack.prod.env.example`
- Modify: `clipper_web_api/README.md`

**Interfaces:**
- Removes: `SUBSCRIPTION_RETRY_DELAYS_MINUTES`.
- Verifies: DB policy is the only retry configuration source.

- [ ] **Step 1: infra에서 기존 retry 환경변수를 제거한다**

```text
apps/compose.yml
env/stack.dev.env.example
env/stack.stage.env.example
env/stack.prod.env.example
```

위 네 파일의 `SUBSCRIPTION_RETRY_DELAYS_MINUTES` 선언만 제거하고 다른 환경값은 변경하지 않는다.

- [ ] **Step 2: API README에 마이그레이션과 운영 확인 절차를 추가한다**

```text
1. npm run db:migrate:admin
2. GET /admin/subscription-renewal-policy에서 3 / [1,2] 확인
3. 관리자 화면에서 값을 저장하고 재배포 없이 다시 조회되는지 확인
4. 이미 past_due인 회차의 snapshot은 바뀌지 않는지 확인
```

- [ ] **Step 3: 남은 환경변수·구형 파서 참조가 없는지 확인한다**

Run: `rg -n "SUBSCRIPTION_RETRY_DELAYS_MINUTES|parseSubscriptionRetryDelays|retryDelaysMinutes" clipper_web_api clipper_infra`

Expected: 결과 없음.

- [ ] **Step 4: API 전체 테스트와 빌드를 실행한다**

Run: `npm test -- --runInBand`

Run: `npm run build`

Expected: 모든 Jest suite PASS, Nest build 성공.

- [ ] **Step 5: 고객 웹 전체 테스트와 빌드를 실행한다**

Run: `npm test -- --watch=false --browsers=ChromeHeadless`

Run: `npm run build`

Expected: 모든 Jasmine spec PASS, production build 성공.

- [ ] **Step 6: 관리자 웹 전체 테스트와 빌드를 실행한다**

Run: `npm test -- --watch=false --browsers=ChromeHeadless`

Run: `npm run build`

Expected: 모든 Jasmine spec PASS, production build 성공.

- [ ] **Step 7: Compose 설정을 렌더링해 문법을 확인한다**

Run: `docker compose --env-file env/stack.dev.env.example -f apps/compose.yml -f apps/compose.dev.yml config`

Expected: configuration rendered successfully, 제거된 환경변수 없음.

- [ ] **Step 8: 시나리오 기반 통합 검증을 수행한다**

테스트 DB 또는 로컬 고정 clock에서 다음을 확인한다.

```text
D+0 최초 실패 -> subscription=past_due, graceEndsAt=D+3, retryAt=D+1
                 access.endsAt=D+3, nextCreditGrantAt=null
D+1 실패       -> retryAt=D+2, 같은 renewal order 사용
D+1.5 수동 실패 -> retryAt=D+2 유지
D+2 실패       -> retryAt=null, 수동 재결제 버튼 유지
D+2.5 성공     -> subscription=active, recovery fields=null,
                 원래 결제 기준일에서 기간 연장, 회차 크레딧 한 번 지급
D+3 미복구     -> subscription=stopped, access=ended,
                 자동 재시도 중단, billing key 제거 예약
D+3 미정산     -> subscription=stopped, access=ended,
                 유예 전 claim 상태 조회 지속, billing key 제거·새 구독 보류
미정산 성공     -> 원래 기준일에서 subscription/access 복구
미정산 실패     -> stopped 유지, billing key 제거 보류 해제
정책 7/[1,3,5] 변경 -> 기존 past_due는 3/[1,2] 유지,
                       다음 신규 실패만 7/[1,3,5] snapshot
```

- [ ] **Step 9: 저장소별 최종 diff를 검토하고 infra/docs를 커밋한다**

```bash
# clipper_infra
git add apps/compose.yml env/stack.dev.env.example env/stack.stage.env.example env/stack.prod.env.example
git commit -m "chore: remove legacy subscription retry env"

# clipper_web_api
git add README.md
git commit -m "docs: add renewal recovery operations guide"
```

- [ ] **Step 10: 각 저장소의 최종 상태와 커밋 범위를 기록한다**

Run in each repository: `git status --short --branch && git log --oneline origin/feat/access-credit-system-replacement..HEAD`

Expected: 의도한 저장소만 clean 상태이고, 갱신 유예·재시도 관련 커밋만 새로 존재한다.
