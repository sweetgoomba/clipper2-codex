# 무료 체험·크레딧·기능 사용 정책 구현 계획

- 작성일: 2026-08-31
- 상태: 구현 전 상세 계획
- 선행 문서: `2026-08-31-toss-payments-pg-completion-refund-credit-design.md`
- 대상: Web API, Customer web, Admin web, Desktop Angular, Desktop NestJS

> 실제 실행 전 사용자의 구현 승인이 필요하다. 승인 후 `superpowers:executing-plans`와 테스트 우선 방식으로 아래 체크박스를 순서대로 수행한다. 기존 DB에는 migration을 실행하지 않고, commit·push도 별도 요청이 있을 때만 한다.

## Goal

이용권 중심으로 묶여 있는 현재 크레딧 사용 구조를 다음 확정 정책으로 바꾼다.

- 회원가입 시 무료 체험 400크레딧 자동 지급
- 무료 체험·추가 구매 크레딧은 한국 날짜 기준 30일 만료
- 정기구독 크레딧은 구독 시작일 기준 매월 만료하며 이월 없음
- 출처와 무관하게 충전 시점이 빠른 크레딧부터 차감
- 무료 기능은 정기구독·크레딧과 무관하게 사용
- 유료 기능은 사용 가능한 크레딧만 확인
- 요금제별 플러그인 차등 없음
- 추가 구매는 현재 유료 정기구독 중일 때만 가능하지만 구매한 크레딧은 구독 종료 뒤에도 만료 전까지 사용 가능

## Architecture

Web API가 날짜·발급·차감·구매 자격의 최종 판단을 한다. 회원 계정은 User DB, 크레딧은 Admin DB에 있어 한 DB transaction으로 묶을 수 없으므로 User DB의 내구성 있는 가입 작업과 Admin DB의 멱등한 지급을 연결한다. Desktop은 플러그인 자체를 이용권으로 잠그지 않고, 실제 유료 동작 시작 시 Web API의 크레딧 견적·차감 결과만 사용한다.

## Tech Stack

- NestJS, TypeORM, PostgreSQL, Jest
- Angular 19, signals, Angular Material, Karma
- Desktop NestJS, TypeScript, `node:test`
- OpenAPI `docs/api/openapi.yaml`

## Task 1 — 한국 날짜 기반 만료·구독 월 계산을 먼저 고정

**Files**

- Create: `clipper_web_api/src/shared/time/korea-calendar.ts`
- Create: `clipper_web_api/src/shared/time/korea-calendar.spec.ts`
- Modify: `clipper_web_api/src/modules/access/domain/month-anniversary.ts`
- Modify: `clipper_web_api/src/modules/access/domain/month-anniversary.spec.ts`

- [ ] 실패 테스트를 먼저 작성한다.

검증할 사례:

- `2026-08-28` 한국 날짜 가입 → `2026-09-27T00:00:00+09:00` 만료
- `2026-01-31` 시작 → 2월 마지막 날 경계 → 3월 31일 원래 기준일 복귀
- 한국 자정 직전·직후가 같은 UTC 날짜 계산으로 섞이지 않음
- leap year 2월
- DST를 쓰지 않는 `Asia/Seoul` 고정 오프셋

의도한 공개 함수:

```ts
export function endExclusiveAfterKoreanCalendarDays(
  source: Date,
  inclusiveDays: number,
): Date;

export function koreanMonthAnniversary(
  anchor: Date,
  offsetMonths: number,
): Date;

export function nextKoreanMonthAnniversary(
  anchor: Date,
  current: Date,
): Date;
```

- [ ] 다음 명령으로 새 테스트가 현재 구현에서 실패하는지 확인한다.

```bash
cd /Users/jina/project/adlight/.worktrees/clipper_web_api-toss-payments-pg-integration
npm test -- --runInBand src/shared/time/korea-calendar.spec.ts src/modules/access/domain/month-anniversary.spec.ts
```

- [ ] 최소 구현으로 테스트를 통과시킨다. 문자열 locale 파싱에 의존하지 말고 한국 시간 `UTC+09:00`의 달력 필드를 명시적으로 변환한다.
- [ ] 기존 `monthAnniversary` 호출부를 새 한국 날짜 함수로 옮기되 공개 이름 변경 범위를 최소화한다.
- [ ] 같은 명령으로 통과를 확인한다.

Review checkpoint: 날짜 예시 표와 테스트 결과를 사용자에게 보여준다. 자동 commit은 하지 않는다.

## Task 2 — 기존 정책을 지우지 않고 후속 migration으로 런칭 정책 적용

**Files**

- Create: `clipper_web_api/src/core/database/migrations/admin/1788200000000-ApplyLaunchCreditAccessPolicies.ts`
- Modify: `clipper_web_api/src/core/database/admin.datasource.ts`
- Modify: `clipper_web_api/src/core/database/admin.datasource.spec.ts`
- Modify: `clipper_web_api/src/modules/access/domain/free-trial.model.ts`
- Modify: `clipper_web_api/src/modules/access/infrastructure/free-trial-policy.entity.ts`
- Modify: `clipper_web_api/src/modules/access/infrastructure/typeorm-free-trials.repository.ts`
- Modify: `clipper_web_api/src/modules/access/infrastructure/typeorm-free-trials.repository.spec.ts`
- Modify: `clipper_web_api/src/modules/access/presentation/admin-free-trial-policy.controller.spec.ts`
- Modify: `clipper_web_api/docs/api/openapi.yaml`
- Modify: `clipper_web_api/src/modules/payments/presentation/payments-openapi-contract.spec.ts`

- [ ] datasource 계약 테스트에 새 migration 등록 기대를 먼저 추가하고 실패를 확인한다.
- [ ] free-trial domain에서 `eligibleFrom`을 제거하고 `validityDays: 30`을 추가하는 테스트를 먼저 고친다.
- [ ] migration `up`에 다음 변경만 넣는다.

```text
free_trial_policies
  - eligible_from 제거
  - validity_days int NOT NULL DEFAULT 30, CHECK > 0 추가
  - initial_credits = 400, validity_days = 30, is_enabled = true

credit_products
  - 모든 추가 구매 상품 validity_days = 30

plan_tiers
  - basic/pro/business/trial entitlement_mode = 'all'
```

`plan_plugin_entitlements`의 과거 행은 history 보존을 위해 삭제하지 않는다. 이후 런타임과 관리자 UI가 이 행을 사용하지 않게 한다.

- [ ] `down`은 원래 임의 cutoff 시각을 만들어내지 않는다. 스키마 rollback이 필요하면 `eligible_from`을 nullable로 복구하고 `NULL`을 넣는다.
- [ ] 기존 `1788100000000-CreateFreeTrialPolicy.ts`를 수정하지 않았는지 `git diff --`로 확인한다.
- [ ] OpenAPI `FreeTrialPolicy`에서 `eligibleFrom`을 제거하고 `validityDays`를 추가한다.
- [ ] 관련 단위 테스트와 build를 실행한다.

```bash
npm test -- --runInBand src/core/database/admin.datasource.spec.ts src/modules/access/infrastructure/typeorm-free-trials.repository.spec.ts src/modules/access/presentation/admin-free-trial-policy.controller.spec.ts src/modules/payments/presentation/payments-openapi-contract.spec.ts
npm run build
```

Review checkpoint: migration SQL, 기존 migration 무변경 diff, OpenAPI 변경을 검토한다.

## Task 3 — 회원가입 작업을 User DB에 내구성 있게 기록

**Files**

- Create: `clipper_web_api/src/core/database/migrations/user/1788200000000-CreateUserOnboardingJobs.ts`
- Create: `clipper_web_api/src/modules/users/domain/user-onboarding-job.model.ts`
- Create: `clipper_web_api/src/modules/users/domain/user-onboarding-jobs.repository.ts`
- Create: `clipper_web_api/src/modules/users/infrastructure/user-onboarding-job.entity.ts`
- Create: `clipper_web_api/src/modules/users/infrastructure/typeorm-user-onboarding-jobs.repository.ts`
- Create: `clipper_web_api/src/modules/users/infrastructure/typeorm-user-onboarding-jobs.repository.spec.ts`
- Modify: `clipper_web_api/src/core/database/user.datasource.ts`
- Modify: `clipper_web_api/src/core/database/user.datasource.spec.ts`
- Modify: `clipper_web_api/src/modules/users/infrastructure/typeorm-users.repository.ts`
- Modify: `clipper_web_api/src/modules/users/infrastructure/typeorm-users.repository.spec.ts`
- Modify: `clipper_web_api/src/modules/users/users.module.ts`

- [ ] 먼저 다음 실패 테스트를 작성한다.

- 새 Google/dev 사용자를 생성하는 같은 User DB transaction에서 `free_trial_provisioning` 작업이 한 건 생성된다.
- 동일 사용자·작업 종류는 unique 제약으로 한 건만 존재한다.
- 기존 사용자를 다시 로그인하면 새 작업을 중복 생성하지 않는다.
- 사용자 저장이 rollback되면 가입 작업도 남지 않는다.

- [ ] job 상태를 다음으로 제한한다.

```ts
type UserOnboardingJobStatus =
  | 'pending'
  | 'processing'
  | 'retryable_failed'
  | 'completed'
  | 'manual_review';
```

필수 필드: `userId`, `kind`, `status`, `attemptCount`, `nextAttemptAt`, `leaseUntil`, 안전한 마지막 오류 코드, 생성·수정·완료 시각. access token이나 Google 원문 profile은 저장하지 않는다.

- [ ] `UsersRepository.create()`가 사용자와 가입 작업을 한 transaction에서 저장하도록 구현한다. 기존 공개 반환형 `User`는 유지한다.
- [ ] `FOR UPDATE SKIP LOCKED` 또는 원자적 update로 복수 API 인스턴스가 같은 작업을 동시에 claim하지 못하게 한다.
- [ ] user datasource에 entity/migration을 등록한다.
- [ ] 테스트와 build를 실행한다.

```bash
npm test -- --runInBand src/core/database/user.datasource.spec.ts src/modules/users/infrastructure/typeorm-users.repository.spec.ts src/modules/users/infrastructure/typeorm-user-onboarding-jobs.repository.spec.ts src/modules/users/application/users.service.spec.ts
npm run build
```

Review checkpoint: User DB transaction 경계와 개인정보 미저장을 검토한다.

## Task 4 — 무료 체험 지급을 가입일 기준 멱등 작업으로 전환

**Files**

- Create: `clipper_web_api/src/modules/access/application/free-trial-onboarding.service.ts`
- Create: `clipper_web_api/src/modules/access/application/free-trial-onboarding.service.spec.ts`
- Create: `clipper_web_api/src/modules/access/application/free-trial-onboarding.scheduler.ts`
- Create: `clipper_web_api/src/modules/access/application/free-trial-onboarding.scheduler.spec.ts`
- Modify: `clipper_web_api/src/modules/access/application/free-trial-provisioner.service.ts`
- Modify: `clipper_web_api/src/modules/access/application/free-trial-provisioner.service.spec.ts`
- Modify: `clipper_web_api/src/modules/access/application/effective-access.service.ts`
- Modify: `clipper_web_api/src/modules/access/application/effective-access.service.spec.ts`
- Modify: `clipper_web_api/src/modules/access/access.module.ts`
- Modify: `clipper_web_api/src/modules/credits/application/credit-grants.service.ts`
- Modify: `clipper_web_api/src/modules/credits/application/credit-grants.service.spec.ts`
- Modify: `clipper_web_api/src/modules/credits/presentation/credits.controller.ts`
- Modify: `clipper_web_api/src/modules/credits/presentation/credits.controller.spec.ts`

- [ ] 실패 테스트를 먼저 작성한다.

핵심 사례:

- 지급량 400, `grantedAt = user.createdAt`, `expiresAt = 가입일 기준 31일차 00:00 KST`
- 실제 작업 처리 시각이 늦어져도 충전·만료 기준은 변하지 않음
- `free-trial:<userId>` 중복 방지 키로 재시도해도 한 지급 건·한 ledger·한 참여만 존재
- 지급 transaction 실패 시 onboarding job이 재시도 상태가 됨
- 만료된 과거 가입자의 누락을 복구해도 spendable balance는 늘지 않음
- 정책 비활성화 시 새 지급은 하지 않고 job을 명확한 완료/건너뜀 상태로 남김

- [ ] `FreeTrialProvisioner.ensureForUser()`에서 `at`을 지급 기준으로 사용하지 않고 `user.createdAt`과 policy `validityDays`를 사용한다.
- [ ] `EffectiveAccessService.resolve()`가 정상 발급 경로로 무료 체험을 생성하지 않게 한다.
- [ ] 첫 `/credits/summary`·`/credits/grants` 조회에서는 누락 복구를 시도하되, 복구 실패가 크레딧 조회 전체를 숨기지 않도록 안전한 오류 계약을 정한다. 같은 요청에서 복구 성공 시 새 잔액을 반환한다.
- [ ] scheduler는 1분마다 due job을 확인하고 claim된 가입 작업만 처리한다. 실패 뒤 재시도 간격은 1분, 5분, 30분, 2시간, 12시간으로 두며 여섯 번째 실패 뒤 `manual_review`로 전환한다. 첫 크레딧 조회의 멱등 복구는 이 대기시간과 별도로 즉시 시도할 수 있다.
- [ ] 테스트와 build를 실행한다.

```bash
npm test -- --runInBand src/modules/access/application/free-trial-provisioner.service.spec.ts src/modules/access/application/free-trial-onboarding.service.spec.ts src/modules/access/application/free-trial-onboarding.scheduler.spec.ts src/modules/access/application/effective-access.service.spec.ts src/modules/credits/presentation/credits.controller.spec.ts
npm run build
```

Review checkpoint: 정상 지급, 장애 재시도, 첫 조회 복구가 같은 멱등키를 쓰는지 확인한다.

## Task 5 — 30일과 구독 월 만료를 모든 지급 경로에 적용

**Files**

- Modify: `clipper_web_api/src/modules/payments/application/payment-fulfillment.service.ts`
- Modify: `clipper_web_api/src/modules/payments/application/payment-fulfillment.service.spec.ts`
- Modify: `clipper_web_api/src/modules/access/application/monthly-credit-grant.service.ts`
- Modify: `clipper_web_api/src/modules/access/application/monthly-credit-grant.service.spec.ts`
- Modify: `clipper_web_api/src/modules/access/application/access-grants.service.ts`
- Modify: `clipper_web_api/src/modules/access/application/access-grants.service.spec.ts`

- [ ] 추가 구매 결제가 자정 근처에서 완료되는 사례와 31일 구독 시작 사례를 실패 테스트로 추가한다.
- [ ] `creditValidityDays * 24h` 계산을 제거하고 한국 날짜 end-exclusive 계산을 사용한다.
- [ ] 정기구독 최초·갱신·월별 지급·상향 추가 지급이 같은 혜택 월의 끝을 사용하게 한다.
- [ ] 연간 구독도 최초 결제에서 첫 달 크레딧만 지급하고 이후 scheduler가 매월 지급한다는 기존 흐름을 회귀 테스트로 고정한다.
- [ ] 다음 월 지급 직전에 이전 월 남은 정기구독 크레딧을 만료 처리하는 로직이 멱등한지 검증한다.
- [ ] 테스트와 build를 실행한다.

```bash
npm test -- --runInBand src/modules/payments/application/payment-fulfillment.service.spec.ts src/modules/access/application/monthly-credit-grant.service.spec.ts src/modules/access/application/access-grants.service.spec.ts src/modules/access/domain/month-anniversary.spec.ts
npm run build
```

Review checkpoint: 무료 체험·추가 구매·정기구독 세 종류의 만료 예시를 표로 비교한다.

## Task 6 — 크레딧 차감 순서를 충전 시점 우선으로 변경

**Files**

- Modify: `clipper_web_api/src/modules/credits/infrastructure/typeorm-credits.repository.ts`
- Modify: `clipper_web_api/src/modules/credits/infrastructure/typeorm-credits.repository.spec.ts`
- Modify: `clipper_web_api/src/modules/credits/application/credit-grants.service.spec.ts`

- [ ] 현재 만료일 우선 정렬에서 실패하는 테스트를 먼저 추가한다.

예시:

```text
A 무료 체험: grantedAt 8/1, expiresAt 8/31
B 추가 구매: grantedAt 8/5, expiresAt 8/20
결과: expiresAt이 더 빠른 B가 아니라 먼저 충전된 A부터 차감
```

- [ ] `lockSpendableGrants()` 정렬을 다음으로 고정한다.

```sql
ORDER BY granted_at ASC, id ASC
```

- [ ] status, remaining, granted/expires 범위와 `FOR UPDATE` 조건은 유지한다.
- [ ] 한 동작이 여러 지급 건을 나눠 차감한 실제 ledger가 정확한 원본 지급 건을 가리키고, 실패 복구가 역으로 되돌리는 기존 테스트를 함께 실행한다.

```bash
npm test -- --runInBand src/modules/credits/infrastructure/typeorm-credits.repository.spec.ts src/modules/credits/application/credit-grants.service.spec.ts src/modules/operations/application/operation-recovery.service.spec.ts
npm run build
```

Review checkpoint: 차감 순서가 출처 우선이나 만료일 우선으로 다시 섞이지 않았는지 확인한다.

## Task 7 — Web API의 이용권·플러그인 차단을 제거하고 크레딧만 검사

**Files**

- Modify: `clipper_web_api/src/modules/credits/application/credit-grants.service.ts`
- Modify: `clipper_web_api/src/modules/credits/application/credit-grants.service.spec.ts`
- Modify: `clipper_web_api/src/modules/operations/application/operations.service.ts`
- Modify: `clipper_web_api/src/modules/operations/application/operations.service.spec.ts`
- Modify: `clipper_web_api/src/modules/access/application/effective-access.service.ts`
- Modify: `clipper_web_api/src/modules/access/application/effective-access.service.spec.ts`
- Modify: `clipper_web_api/src/modules/credits/presentation/credits.controller.spec.ts`
- Modify: `clipper_web_api/docs/api/openapi.yaml`
- Modify: `clipper_web_api/src/modules/payments/presentation/payments-openapi-contract.spec.ts`

- [ ] 실패 테스트를 다음 정책으로 교체한다.

- 이용권 없음 + 유효한 무료 체험 크레딧 → 유료 동작 가능
- 구독 종료 + 유효한 추가 구매 크레딧 → 유료 동작 가능
- 구독 중 + 잔액 부족 → `INSUFFICIENT_CREDITS`
- 이용권 없음 + 잔액 부족 → `INSUFFICIENT_CREDITS`
- 등록되지 않은 동작 key → 기존의 등록 검증으로 차단
- 무료 동작은 operations billing endpoint를 거치지 않는 기존 경로 유지

- [ ] `CreditGrantsService.consume()`에서 `EffectiveAccessService.resolve()`, `allowsPlugin()`, 이용권별 `spendableCreditSources` 의존을 제거한다.
- [ ] 모든 spendable source를 중앙 상수로 정의하지 말고 repository가 유효·잠금되지 않은 모든 지급 건을 반환하도록 계약을 단순화한다. 환불 잠금 status는 후속 환불 계획에서 자동 제외된다.
- [ ] `OperationQuoteReason`에서 `NO_ACTIVE_ACCESS`, `PLUGIN_NOT_ENTITLED`를 제거하고 `INSUFFICIENT_CREDITS`만 잔액 차단 사유로 남긴다.
- [ ] `/credits/summary`의 `spendableBalance`가 이용권 유무가 아닌 실제 유효 지급 건 합계가 되게 하고 `blockedReason`을 제거한다.
- [ ] `/access/current`는 구독·관리자 이용 상태 표시용으로 유지하되 유료 동작 권한이라는 의미를 제거한다.
- [ ] OpenAPI와 계약 테스트를 갱신한다.

```bash
npm test -- --runInBand src/modules/credits/application/credit-grants.service.spec.ts src/modules/operations/application/operations.service.spec.ts src/modules/access/application/effective-access.service.spec.ts src/modules/credits/presentation/credits.controller.spec.ts src/modules/payments/presentation/payments-openapi-contract.spec.ts
npm run build
```

Review checkpoint: 서버가 요금제 등급 또는 플러그인 허용 목록을 유료 동작 판단에 사용하지 않는지 검색 결과를 확인한다.

## Task 8 — 추가 구매 자격은 구독 상태로 유지하고 사용 자격과 분리

**Files**

- Modify: `clipper_web_api/src/modules/payments/application/topup-payments.service.ts`
- Modify: `clipper_web_api/src/modules/payments/application/topup-payments.service.spec.ts`
- Modify: `clipper_web_api/src/modules/payments/presentation/topup-payments.controller.spec.ts`

- [ ] 다음 상태표를 실패 테스트로 고정한다.

| 정기구독 상태 | 새 추가 크레딧 구매 |
|---|---|
| `active` | 허용 |
| `cancel_at_period_end`, 현재 기간 전 | 허용 |
| `past_due` | 차단 |
| `stopped`, `ended`, `canceled`, 없음 | 차단 |

- [ ] 구매 자격 검사에서 `EffectiveAccessService` 또는 관리자 이용권을 사용하지 않고 `SubscriptionsRepository`의 실제 유료 정기구독만 확인한다.
- [ ] 구매 후 지급 건에는 subscription ID를 사용 자격으로 묶지 않는다. 환불 추적용 `paymentOrderId`만 필수로 유지한다.
- [ ] 구독 종료 뒤 기존 top-up 지급 건 소비가 가능한 Task 7 회귀 테스트를 함께 실행한다.

```bash
npm test -- --runInBand src/modules/payments/application/topup-payments.service.spec.ts src/modules/payments/presentation/topup-payments.controller.spec.ts src/modules/credits/application/credit-grants.service.spec.ts
npm run build
```

Review checkpoint: 구매 조건과 사용 조건이 코드에서 서로 다른 서비스에 있는지 확인한다.

## Task 9 — Desktop NestJS의 플러그인 이용권 차단 제거

**Files**

- Delete: `clipper_nestjs/src/modules/plugins/application/plugin-access.service.ts`
- Modify: `clipper_nestjs/src/modules/plugins/application/plugins.service.ts`
- Modify: `clipper_nestjs/src/modules/plugins/presentation/plugins.controller.ts`
- Modify: `clipper_nestjs/src/modules/plugins/domain/plugin.model.ts`
- Modify: `clipper_nestjs/src/modules/plugins/plugins.module.ts`
- Modify: `clipper_nestjs/src/modules/credits/application/credits.service.ts`
- Modify: `clipper_nestjs/test/plugin-access-controller.test.js`
- Modify: `clipper_nestjs/test/access-credit-proxy.test.js`
- Modify: `clipper_nestjs/test/plugins-install.test.js`
- Modify: `clipper_nestjs/test/plugins-service-runtime-diagnostics.test.js`
- Modify: `clipper_nestjs/test/shortform-operation-entitlement.test.js`

- [ ] 현재 `NO_ACTIVE_ACCESS`와 `PLUGIN_NOT_ENTITLED`를 기대하는 테스트를 새 정책으로 먼저 바꿔 실패를 확인한다.
- [ ] 설치·시작·목록에서 정기구독/요금제 허용 목록 검사를 제거하고 더 이상 쓰이지 않는 `PluginAccessService`를 삭제한다. `PluginsModule`의 `AccessModule` 의존도 함께 제거한다.
- [ ] 인증이 필요한 Web API 유료 동작과 플러그인 로컬 실행은 구분한다. 플러그인 잠금을 없앤다고 사용자 인증 token 전달을 없애지 않는다.
- [ ] 플러그인 상태 DTO의 `entitled`, `entitlementReason`은 제거하거나 항상 true로 남기지 말고 계약 자체를 정리한다.
- [ ] build 후 관련 compiled test를 실행한다.

```bash
cd /Users/jina/project/adlight/.worktrees/clipper_nestjs-toss-payments-pg-integration
npm run build
node --test test/plugin-access-controller.test.js test/plugins-install.test.js test/plugins-service-runtime-diagnostics.test.js test/shortform-operation-entitlement.test.js test/operations-controller.test.js test/web-api-operation-run.test.js test/access-credit-proxy.test.js
```

Review checkpoint: 플러그인 시작과 유료 동작 크레딧 차감이 서로 다른 경계임을 코드와 테스트로 확인한다.

## Task 10 — Desktop Angular의 이용권 잠금과 오래된 안내 제거

**Files**

- Modify: `clipper_angular/src/core/plugins/plugin-route.guards.ts`
- Modify: `clipper_angular/src/core/plugins/plugin-route.guards.spec.ts`
- Delete: `clipper_angular/src/core/access/access-entitlement.service.ts`
- Delete: `clipper_angular/src/core/access/access-entitlement.service.spec.ts`
- Modify: `clipper_angular/src/core/index.ts`
- Modify: `clipper_angular/src/core/operations/operation-billing.service.ts`
- Modify: `clipper_angular/src/core/operations/operation-billing.service.spec.ts`
- Modify: `clipper_angular/src/shared/operations/operation-charge-guard.service.ts`
- Modify: `clipper_angular/src/shared/operations/operation-charge-guard.service.spec.ts`
- Modify: `clipper_angular/src/app/app.routes.ts`
- Modify: `clipper_angular/src/app/app.routes.spec.ts`
- Modify: `clipper_angular/src/core/bridge/clipper-bridge.ts`
- Modify: `clipper_angular/src/core/plugins/plugin-status.service.ts`
- Modify: `clipper_angular/src/core/plugins/plugin-status.service.spec.ts`
- Modify: `clipper_angular/src/shell/store/store/store.component.ts`
- Modify: `clipper_angular/src/shell/store/store/store.component.spec.ts`
- Modify: `clipper_angular/src/shell/store/plugin-card/plugin-card.component.ts`
- Modify: `clipper_angular/src/shell/store/plugin-card/plugin-card.component.spec.ts`
- Modify: `clipper_angular/src/shell/store/plugin-detail/plugin-detail.component.ts`
- Modify: `clipper_angular/src/shell/store/plugin-detail/plugin-detail.component.spec.ts`
- Modify: `clipper_angular/src/shell/settings/settings/settings.component.html`
- Modify: `clipper_angular/src/shell/settings/settings/settings.component.spec.ts`
- Modify: `clipper_angular/src/shell/settings/settings/settings-account.service.ts`

- [ ] 플러그인 route가 이용권 없이도 통과하는 테스트를 먼저 작성한다.
- [ ] `pluginEntitledGuard`를 route 구성과 export에서 제거하고, 그 용도로만 존재하는 Desktop `AccessEntitlementService`와 spec을 삭제한다. Web Customer의 `/access/current` 조회는 그대로 유지한다.
- [ ] `OperationQuoteReason`을 Web API와 동일하게 `INSUFFICIENT_CREDITS` 중심으로 바꾼다.
- [ ] 크레딧 부족 문구만 남기고 “이용권이 필요합니다”, “현재 요금제에서 사용할 수 없습니다” 안내를 제거한다.
- [ ] 전체 Angular 테스트와 build를 실행한다.

```bash
cd /Users/jina/project/adlight/.worktrees/clipper_angular-toss-payments-pg-integration
npm test -- --watch=false
npm run build
```

Review checkpoint: 무료 기능 route와 유료 동작 confirm 흐름을 각각 smoke test한다.

## Task 11 — Customer/Admin 모델과 문구를 새 정책에 맞춤

**Files**

- Modify: `clipper_web_client/src/app/core/api/models.ts`
- Modify: `clipper_web_client/src/app/core/api/access-api.service.spec.ts`
- Modify: `clipper_web_client/src/app/core/api/catalog-api.service.spec.ts`
- Modify: `clipper_web_client/src/app/core/api/mock/mock-data.ts`
- Modify: `clipper_web_client/src/app/core/api/mock/mock-api.interceptor.spec.ts`
- Modify: `clipper_web_client/src/app/features/portal/dashboard/dashboard.component.ts`
- Modify: `clipper_web_client/src/app/features/portal/dashboard/dashboard.component.html`
- Modify: `clipper_web_client/src/app/features/portal/dashboard/dashboard.component.spec.ts`
- Modify: `clipper_web_client/src/app/features/portal/credits/credits.component.ts`
- Modify: `clipper_web_client/src/app/features/portal/credits/credits.component.html`
- Modify: `clipper_web_client/src/app/features/portal/credits/credits.component.spec.ts`
- Modify: `clipper_web_client/src/app/features/portal/topup/topup.component.spec.ts`
- Modify: `clipper_web_client/src/app/features/public/pricing/pricing.component.ts`
- Modify: `clipper_web_client/src/app/features/public/pricing/pricing.component.html`
- Modify: `clipper_web_client/src/app/features/public/pricing/pricing.component.scss`
- Modify: `clipper_web_client/src/app/features/public/pricing/pricing.component.spec.ts`
- Modify: `clipper_web_admin/src/app/core/api/models.ts`
- Modify: `clipper_web_admin/src/app/features/portal/members/detail/member-detail.component.html`
- Modify: `clipper_web_admin/src/app/features/portal/members/detail/member-detail.component.spec.ts`
- Modify: `clipper_web_admin/src/app/features/portal/plans/plans.component.ts`
- Modify: `clipper_web_admin/src/app/features/portal/plans/plans.component.html`
- Modify: `clipper_web_admin/src/app/features/portal/plans/plans.component.scss`
- Modify: `clipper_web_admin/src/app/features/portal/plans/plans.component.spec.ts`

- [ ] Customer의 `CreditBlockedReason`, `NO_ACTIVE_ACCESS`, “이용권이 없으면 보유만 가능” 기대를 먼저 제거하고 새 테스트를 작성한다.
- [ ] 구독 없음 + 유효한 추가 구매 크레딧이 `spendableBalance`로 표시되는지 검증한다.
- [ ] 추가 구매 버튼은 현재 유료 정기구독 상태일 때만 보이되 서버 검사를 대체하지 않는다는 테스트를 유지한다.
- [ ] 고객 요금 페이지에서 요금제별 플러그인 목록 비교를 제거하고 모든 요금제가 같은 기능을 사용하며 월 지급 크레딧만 다르다는 문구로 바꾼다.
- [ ] Admin의 무료 체험 정책에서 cutoff 입력·표시를 제거하고 400크레딧·30일 정책을 표시한다.
- [ ] Admin 요금제 편집에서 플러그인 차등 설정 UI를 제거한다. 동작별 크레딧 가격 관리 UI는 유지한다.
- [ ] Admin 수동 크레딧 문구에서 “이용권이 없으면 사용 불가”를 제거한다.
- [ ] 각 저장소 테스트와 build를 실행한다.

```bash
cd /Users/jina/project/adlight/.worktrees/clipper_web_client-toss-payments-pg-integration
npm test -- --watch=false
npm run build

cd /Users/jina/project/adlight/.worktrees/clipper_web_admin-toss-payments-pg-integration
npm test -- --watch=false
npm run build
```

Customer web 검증 중 기존 untracked `build/`는 건드리지 않는다.

## Task 12 — Phase 1 계약·migration 통합 검증

**Files**

- Modify: `clipper_web_api/test/app.e2e-spec.ts`
- Modify: `clipper_web_api/test/jest-e2e.json`
- Create: `clipper_web_api/test/credit-access-launch-policy.e2e-spec.ts`

- [ ] 신규 빈 Admin/User DB에 전체 migration을 적용한다. 5433·5434·5435는 사용하지 않는다.
- [ ] 다음 e2e 흐름을 자동화한다.

1. 새 사용자 생성
2. 무료 체험 작업 처리
3. 400크레딧과 가입일 기준 만료 확인
4. 이용권 없이 유료 동작 차감
5. 정기구독 시작 및 월 크레딧 지급
6. 추가 구매 후 구독 종료
7. 추가 구매 크레딧 계속 사용
8. 충전 시점 우선 차감
9. 작업 실패 시 원 지급 건으로 복구

- [ ] API 전체 테스트와 build를 실행한다.

```bash
cd /Users/jina/project/adlight/.worktrees/clipper_web_api-toss-payments-pg-integration
npm test -- --runInBand
npm run test:e2e -- --runInBand
npm run build
```

- [ ] 관련 저장소들의 `git status --short`, tracked diff, staged diff를 기록한다.
- [ ] 사용자 검토 전 stage·commit·push하지 않는다.

## 완료 기준

- 정책별 단위·통합 테스트가 모두 통과한다.
- OpenAPI와 Web API 응답, Customer/Admin/Desktop 타입이 일치한다.
- 요금제 등급과 플러그인 허용 목록이 유료 동작 차단에 사용되지 않는다.
- 구독 종료 후 추가 구매 크레딧 사용이 가능하다.
- 30일·구독 월 날짜 계산이 한국 날짜 예시와 일치한다.
- 기존 작업 실패 크레딧 복구가 깨지지 않는다.
- 기존 migration과 보호 대상 worktree/file에 변경이 없다.
