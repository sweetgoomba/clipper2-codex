# Toss Payments PG 가격·무료체험·권한 정책 세션 인수인계

- 작성일: 2026-08-26 (Asia/Seoul)
- 구현일: 2026-08-24
- 최신 상태 source of truth: **이 문서**
- API 계약 source of truth: `clipper_web_api/docs/api/openapi.yaml`
- 작업 branch: 7개 repository 모두 `feature/toss-payments-pg-integration`

## 0. 문서 우선순위와 상태 구분

- 이 문서는 8월 24일 가격·Trial·권한 구현과 8월 26일 종료 시점의 HEAD, status, 테스트,
  프로세스, DB 상태에 대한 최신 정본이다.
- `2026-08-21-toss-payments-pg-upgrade-consent-and-manual-verification-handoff.md`는 기존
  PG·webhook·수동 검증·환불 사전조사의 정본이다. 그 문서의 현재 HEAD, 테스트 수,
  listener, DB, worktree 목록은 이 문서가 대체한다.
- `2026-08-19-toss-payments-pg-integration-session-handoff.md`는 초기 구현 이력이며 현재 상태
  판단에는 사용하지 않는다.
- 승인 설계는 `docs/superpowers/specs/2026-08-24-pricing-trial-and-entitlements-design.md`다.
  단, `all → allowlist`의 단일 transaction 표현은 현재 두 요청 구현과 다르므로 7·13절의
  제한을 우선한다.
- `clipper_docs/launch/2026-08-20-planning-team-requests.md`와
  `clipper_docs/launch/2026-08-20-legal-drafts-for-review.md`는 기획·법무 검토를 위한
  **비최신 참고자료**다. 작성 당시의 잠정안과 미검증 법률 문구가 포함돼 있으며 현재 코드,
  승인된 가격·Trial·구독 정책, 법무 의견을 대체하지 않는다. 다음 세션에서 반드시 읽되
  사실이나 결정으로 바로 채택하지 말고 현재 상태와 항목별로 대조한다.
- 특히 두 문서가 인용하거나 전제한 법령·법안·시행령·가이드라인, 청약철회 기간과 기산점,
  디지털콘텐츠/계속거래의 철회·환불 예외 및 고지·동의 요건은 작성 당시 검토됐더라도 현재
  유효하다고 가정하지 않는다. 다음 세션 시점의 최신 공식 원문과 시행일을 다시 확인하고,
  Clipper의 실제 판매·자동결제·서비스 제공 방식에 적용되는지도 별도로 검토한다.
- Git HEAD와 실제 diff가 문서보다 우선한다. persistent DB나 live Toss에서 확인하지 않은
  동작은 완료로 기록하지 않는다.

상태 용어:

- **구현+자동검증**: commit됐고 2026-08-26 현재 HEAD의 전체 test/build가 통과함.
- **격리 DB 검증**: 2026-08-24 disposable PostgreSQL에서 확인함.
- **브라우저 검증**: compiled UI+task fixture로 확인했으며 live API/Toss 검증은 아님.
- **미검증**: 코드는 있지만 persistent 개발 DB·실제 시간 경과·live provider에서 미확인.
- **미구현**: 설계나 TODO만 있고 실행 코드는 없음.

## 1. 세션 목적

환불 설계 전에 다음을 마무리하는 것이 목적이었다.

1. `access-credit`와 임시 review/foundation worktree가 PG branch에 흡수됐는지 확인하고 정리.
2. 전략팀 가격표를 Basic/Pro/Business 월간·연간 카탈로그에 반영.
3. 연간은 연 1회 선결제, 크레딧은 월별 지급으로 확정.
4. 실제 할인율과 설정 할인율의 전역 표시 모드 구현.
5. Trial 400, 유료/Trial 잔액 우선순위, 월 크레딧 비이월 구현.
6. Trial/Basic allowlist와 Pro/Business 모든 등록 플러그인 정책 구현.
7. 고객 가격 페이지와 관리자 카탈로그 UI 반영.
8. API/DB/OpenAPI/clients를 검증하고 환불 설계 전 기준점 기록.

환불 산식, provider cancellation, 환불 UI, 법률 판단은 이번 범위가 아니었다.

## 2. 조사·논의·구현한 내용

### worktree/branch 조사

- `feat/access-credit-system-replacement`는 단순 Toss Pay 간편결제 실험 branch가 아니다.
  access/credit ledger, plugin entitlement, top-up, subscription recovery/payment-method change 등
  현재 PG의 선행 기반을 포함한다.
- 7개 repo 모두에서 `git merge-base --is-ancestor feat/access-credit-system-replacement HEAD`
  exit 0을 확인했다. 즉 각 PG branch가 해당 선행 branch 전체 이력을 포함한다.
- infra/API/client의 `feat/toss-payments-pg-review-checkout`, API의
  `feat/billing-product-catalog-foundation`도 대응 PG HEAD의 ancestor(exit 0)다.
- 관련 worktree는 제거했고 branch는 보존했다. 다른 세션 worktree는 건드리지 않았다.

### 확정 가격

| Tier | 월간 | 월 credits | 연간 월 환산 | 연간 일시 결제 | 설정 할인 | 실제 할인 |
|---|---:|---:|---:|---:|---:|---:|
| Basic | 5,900원 | 400 | 4,900원 | 58,800원 | 15% | 16.9%→17% |
| Pro | 10,900원 | 1,000 | 6,900원 | 82,800원 | 30% | 36.7%→37% |
| Business | 29,900원 | 4,000 | 19,500원 | 234,000원 | 35% | 34.8%→35% |

- 연간 금액은 12개월 총액을 한 번에 승인한다.
- 전역 `actual | manual` 표시 모드, 초기 `actual`.
- customer는 server-selected 정수 effective 값만 사용한다.
- admin은 actual 1자리 소수/configured 정수/effective 정수를 함께 본다.

### Trial·credits·plugins

- Trial은 계정당 1회 400, 만료 없음. 유료 전환 때 남은 Trial 잔액을 삭제하지 않는다.
- paid/admin access가 우선하고, paid 상태에서는 만료가 빠른 유료 월 grant→top-up→Trial 순.
- paid access 종료 후 Trial 잔액이 있으면 Trial 권한으로 fallback한다.
- 유료 월 credits는 이월하지 않는다. annual도 최초 1회+이후 월 경계 11회 지급한다.
- Trial/Basic은 서로 독립된 다음 5-key allowlist다:
  `shortform_url`, `shortform_paste`, `shortform_prompt`, `dialog_highlight`, `dance_highlight`.
- Pro/Business는 `all`: 현재와 미래의 **등록된** plugin만 자동 허용. unknown key는 거부.
- 같은 interval에서 rank 상승은 즉시, 하향 또는 interval 변경은 기간 말 예약.
- top-up은 현재 half-open paid period `start <= now < end`에서만 구매 가능.

### clients

- customer pricing: 카드별 토글 제거, 상단 월/연 selector 하나로 3개 tier를 함께 전환.
- annual card: 월 환산액+연간 총액+server effective 할인율을 표시.
- admin: rank, entitlement mode/allowlist, recurring/top-up, actual/manual, annual configured discount,
  free-trial policy를 편집.
- create는 inactive, 삭제 기능은 추가하지 않았다. Trial은 유료 product/checkout/change 대상 차단.

## 3. 실제 코드 변경사항

세션 시작 직전 commit→현재 HEAD의 committed diff다.

| Repo | 시작 | HEAD | commits | diff |
|---|---|---|---:|---|
| API | `a47a971` | `a85e2fa665a8497ff66c4939e417fb10fc48df8d` | 24 | 70 files, +7,723/-468 |
| customer | `fd71462` | `2fbd5e9c6c43b1efefd334cf57dc6bc80254cb43` | 6 | 20 files, +1,013/-268 |
| admin | `2ccb825` | `cbf7c52a20555ff736e0be7711dd3645fdfe59c4` | 7 | 12 files, +1,689/-179 |

핵심 구현:

- forward catalog/free-trial migrations, entities, repositories
- actual/manual discount 계산과 closed public/admin projection
- Trial participation+non-expiring grant+effective access
- access별 spendable source fencing, transaction/lock 기반 debit·operation refund
- registered plugin 기반 `allowlist | all`
- rank 기반 plan change, durable rejected quote expiry
- Trial billing guard, paid-period-only top-up
- customer global interval UI, admin policy editors와 authoritative reload

`clipper_angular`, `clipper_electron`, `clipper_nestjs`, `clipper_infra` PG worktree에는
2026-08-24 이후 commit이나 tracked/staged diff가 없다.

## 4. 실제 파일별 변경사항

아래 파일 목록은 각 baseline→HEAD의 `git diff --name-status`와 일치한다.

### API: 계약·설계·DB

- `docs/api/openapi.yaml`: catalog/discount/EffectiveAccess/Trial endpoints 계약.
- `docs/superpowers/specs/2026-08-24-pricing-trial-and-entitlements-design.md`: 승인 설계.
- `docs/superpowers/plans/2026-08-24-pricing-catalog-and-discounts.md`: catalog 실행 계획.
- `docs/superpowers/plans/2026-08-24-free-trial-credit-and-plan-lifecycle.md`: Trial/lifecycle 계획.
- `docs/superpowers/plans/2026-08-24-pricing-and-catalog-clients.md`: clients 계획.
- `src/core/database/admin.datasource.ts`: 새 entities/migrations 등록.
- `src/core/database/admin.datasource.spec.ts`: 등록 계약 회귀.
- `src/core/database/migrations/admin/1788000000000-ConfigurePricingCatalog.ts`: 가격/rank/
  entitlement/discount/top-up/unique-index migration.
- `src/core/database/migrations/admin/1788000000000-ConfigurePricingCatalog.spec.ts`: exact SQL/up/down 회귀.
- `src/core/database/migrations/admin/1788100000000-CreateFreeTrialPolicy.ts`: policy/participation/source migration.
- `src/core/database/migrations/admin/1788100000000-CreateFreeTrialPolicy.spec.ts`: cutoff/schema/down guard 회귀.

### API: access/Trial

```text
M src/modules/access/access.module.ts
M src/modules/access/application/access-grants.service.ts
M src/modules/access/application/access-grants.service.spec.ts
A src/modules/access/application/effective-access.service.ts
A src/modules/access/application/effective-access.service.spec.ts
A src/modules/access/application/free-trial-policy.service.ts
A src/modules/access/application/free-trial-policy.service.spec.ts
A src/modules/access/application/free-trial-provisioner.service.ts
A src/modules/access/application/free-trial-provisioner.service.spec.ts
M src/modules/access/application/monthly-credit-grant.service.spec.ts
A src/modules/access/domain/free-trial.model.ts
A src/modules/access/domain/free-trials.repository.ts
A src/modules/access/infrastructure/free-trial-policy.entity.ts
A src/modules/access/infrastructure/user-free-trial.entity.ts
A src/modules/access/infrastructure/typeorm-free-trials.repository.ts
A src/modules/access/infrastructure/typeorm-free-trials.repository.spec.ts
A src/modules/access/presentation/admin-free-trial-policy.controller.ts
A src/modules/access/presentation/admin-free-trial-policy.controller.spec.ts
M src/modules/access/presentation/current-access.controller.spec.ts
A src/modules/access/presentation/dto/update-free-trial-policy.dto.ts
```

역할: module wiring, paid/admin 우선+Trial fallback projection, one-time provisioning, future policy
mutation, ORM persistence, operator endpoints, annual 11-anniversary/OpenAPI 회귀.

### API: catalog/discount

```text
M src/modules/catalog/catalog.module.ts
M src/modules/catalog/domain/product-catalog.model.ts
M src/modules/catalog/domain/product-catalog.repository.ts
M src/modules/catalog/application/product-catalog.service.ts
M src/modules/catalog/application/product-catalog.service.spec.ts
M src/modules/catalog/infrastructure/plan-tier.entity.ts
M src/modules/catalog/infrastructure/billing-product.entity.ts
A src/modules/catalog/infrastructure/catalog-presentation-setting.entity.ts
M src/modules/catalog/infrastructure/typeorm-product-catalog.repository.ts
M src/modules/catalog/infrastructure/typeorm-product-catalog.repository.spec.ts
M src/modules/catalog/presentation/catalog.controller.ts
M src/modules/catalog/presentation/catalog.controller.spec.ts
M src/modules/catalog/presentation/admin-catalog.controller.ts
M src/modules/catalog/presentation/admin-catalog.controller.spec.ts
M src/modules/catalog/presentation/dto/create-plan-tier.dto.ts
M src/modules/catalog/presentation/dto/update-plan-tier.dto.ts
M src/modules/catalog/presentation/dto/create-billing-product.dto.ts
M src/modules/catalog/presentation/dto/update-billing-product.dto.ts
A src/modules/catalog/presentation/dto/update-catalog-presentation-settings.dto.ts
```

역할: actual/manual 계산, closed projections, annual/manual invariants, settings lock, partial unique
409, DTO undefined merge 보존, Trial billing 차단과 회귀.

### API: credits/operations/payments

```text
M src/modules/credits/domain/credit.model.ts
M src/modules/credits/domain/credits.repository.ts
M src/modules/credits/application/credit-grants.service.ts
M src/modules/credits/application/credit-grants.service.spec.ts
M src/modules/credits/infrastructure/typeorm-credits.repository.ts
M src/modules/credits/infrastructure/typeorm-credits.repository.spec.ts
M src/modules/credits/presentation/credits.controller.spec.ts
M src/modules/operations/domain/operation-definitions.ts
M src/modules/operations/application/operations.service.ts
M src/modules/operations/application/operations.service.spec.ts
M src/modules/operations/application/operation-recovery.service.ts
M src/modules/operations/application/operation-recovery.service.spec.ts
M src/modules/payments/application/payment-fulfillment.service.ts
M src/modules/payments/application/payment-fulfillment.service.spec.ts
M src/modules/payments/application/subscription-payments.service.ts
M src/modules/payments/application/subscription-payments.service.spec.ts
M src/modules/payments/application/subscription-plan-changes.service.ts
M src/modules/payments/application/subscription-plan-changes.service.spec.ts
M src/modules/payments/application/topup-payments.service.ts
M src/modules/payments/application/topup-payments.service.spec.ts
```

역할: `free_trial` source, source-filtered `FOR UPDATE`, transactional authorization/debit/refund,
registered plugin set, ranked plan changes, annual/top-up fulfillment, Trial checkout guard,
paid-period top-up와 전 범위 회귀.

### customer 20 files

```text
M src/app/core/api/models.ts
M src/app/core/api/catalog-api.service.spec.ts
M src/app/core/api/access-api.service.spec.ts
M src/app/core/api/mock/mock-data.ts
M src/app/core/api/mock/mock-api.interceptor.ts
M src/app/core/api/mock/mock-api.interceptor.spec.ts
A src/app/core/payments/subscription-eligibility.ts
A src/app/core/payments/subscription-eligibility.spec.ts
M src/app/features/portal/credits/credits.component.ts
M src/app/features/portal/credits/credits.component.spec.ts
M src/app/features/portal/dashboard/dashboard.component.ts
M src/app/features/portal/dashboard/dashboard.component.html
M src/app/features/portal/dashboard/dashboard.component.spec.ts
M src/app/features/portal/topup/topup.component.ts
M src/app/features/portal/topup/topup.component.html
M src/app/features/portal/topup/topup.component.spec.ts
M src/app/features/public/pricing/pricing.component.ts
M src/app/features/public/pricing/pricing.component.html
M src/app/features/public/pricing/pricing.component.scss
M src/app/features/public/pricing/pricing.component.spec.ts
```

역할: 새 closed contracts/mocks, Trial label, paid-period predicate, top-up fail-closed, global interval
selector, annual copy/server discount, login-return·keyboard·responsive 회귀.

### admin 12 files

```text
M src/app/core/api/models.ts
M src/app/core/api/catalog-api.service.ts
M src/app/core/api/catalog-api.service.spec.ts
M src/app/core/api/mock/mock-data.ts
M src/app/core/api/mock/mock-api.interceptor.ts
M src/app/core/api/mock/mock-api.interceptor.spec.ts
M src/app/features/portal/members/detail/member-detail.component.ts
M src/app/features/portal/members/detail/member-detail.component.spec.ts
M src/app/features/portal/plans/plans.component.ts
M src/app/features/portal/plans/plans.component.html
M src/app/features/portal/plans/plans.component.scss
M src/app/features/portal/plans/plans.component.spec.ts
```

역할: discount trio/settings/free-trial contracts, stateful server-like mocks, member Trial label,
rank/entitlement/discount/Trial controls, pending serialization, rollback/reload, dormant allowlist,
Trial product exclusion과 회귀.

### `.codex` 문서

루트는 Git repo가 아니므로 아래는 Git commit 대상이 아니다.

- `2026-08-21-toss-payments-pg-upgrade-consent-and-manual-verification-handoff.md`: 8월 24일
  구현 요약과 이 최신 문서 pointer 추가.
- `2026-08-26-toss-payments-pg-pricing-trial-entitlements-session-handoff.md`: 현재 문서.

## 5. DB/OpenAPI/API 변경사항

### DB — code+격리 DB 검증, persistent DB 미적용

`178800`: tier `entitlement_mode`, `upgrade_rank`; product `display_discount_percent`;
singleton presentation settings; 4 tiers, 6 recurring, 3 top-up; Trial/Basic allowlists; active
tier+interval partial unique index.

`178810`: singleton free-trial policy; `user_free_trials(user_id PK, credit_grant_id UNIQUE)`;
`credit_grants.source=free_trial`; 초기 400/enabled; 고정 cutoff
`2026-08-30T14:26:40.000Z`; 참여/grant 이력이 있으면 down 거부.

2026-08-26 persistent DB read-only 결과:

| DB | port | migrations | latest |
|---|---:|---:|---:|
| admin | 5433 | 28 | 1786600000000 |
| release | 5434 | 2 | 1782790000000 |
| user | 5435 | 7 | 1786100000000 |

새 migrations는 persistent 개발 DB에 적용되지 않았다.

### OpenAPI/API — 구현+자동검증

- `PlanTier.entitlementMode/upgradeRank`
- public product `effectiveDiscountPercent`; admin product configured/actual/effective trio
- `AdminCatalog.presentationSettings`
- `EffectiveAccess`와 `free_trial` source
- `GET/PATCH /admin/free-trial-policy`
- `PATCH /admin/catalog/presentation-settings`
- `GET /catalog`은 sellable tier만 노출해 internal Trial 제외
- `GET /access/current`는 과거 grant/date view 대신 EffectiveAccess
- Trial product creation/activation/checkout/change 차단
- Trial lazy provisioning, access-specific credit source fencing, paid-period top-up

OpenAPI YAML parse/exact schema는 Jest에 포함된다. deployed Swagger/live contract는 미검증이다.

## 6. 새롭게 확정된 설계 결정

1. annual은 12개월 총액 연 1회 결제, credits는 월별 지급.
2. paid monthly credits는 이월하지 않음.
3. Trial 400은 1회·무기한, paid conversion 때 잔액 보존.
4. paid/admin access 우선, paid 기간 중 Trial은 마지막 spend fallback.
5. Trial/Basic 독립 5-key allowlist, Pro/Business registered plugins 전체.
6. Pro/Business는 현재 같은 권한이지만 독립 변경 가능.
7. same-interval rank 상승 즉시; 하향/교차 interval 예약.
8. top-up은 current paid subscription period에서만 구매.
9. actual/manual은 global; customer는 server effective 값만 사용.
10. customer interval selector는 page-level 하나.
11. catalog 수정은 새 checkout/quote에만 적용하고 기존 snapshots를 소급 수정하지 않음.
12. Trial은 subscription/payment product가 아님.
13. catalog는 create-inactive/update/deactivate; delete 미추가.

## 7. 결정되지 않은 사항과 구현상 제한

미결정:

- refund/provider cancellation 전액·부분 조건, 월/연/top-up/상향/가상계좌별 산식
- 경과 기간·사용 credits·잔액·청약철회 경계
- refund 승인권한, CS/SLA/알림/감사보존, access/subscription/ledger 조정
- provider 취소 idempotency, 응답 유실, webhook/reconciliation/retry
- 기존 계정 Trial backfill
- 장래 Pro/Business 권한 차등
- catalog 실제 DELETE 필요 여부
- dormant allowlist 변경까지 DB 원자성이 필요한지 여부
- merge/PR/push/deploy와 운영 migration 시점

확인 필요한 구현값:

- Trial cutoff `2026-08-30T14:26:40.000Z`는 code/test/disposable DB에 있지만, 사용자가 그
  정확한 시각을 명시 승인한 기록은 확인되지 않았다. shared/production 적용 전에 확인한다.
  이미 `178810`이 적용된 DB라면 migration history를 고치지 말고 forward migration을 쓴다.

현재 atomicity 제한:

- admin `all → allowlist`는 plugin PUT 후 tier PATCH다. nonempty validated dormant list를 먼저
  저장하므로 PATCH 실패 시 effective mode는 `all`로 안전하고 UI는 authority를 reload한다.
- 두 HTTP 요청이 하나의 DB transaction은 아니므로 dormant rows가 일부 바뀔 수 있다.

## 8. 검토한 대안과 선택하지 않은 이유

- annual 월별 청구: 전략 금액을 월 환산으로 해석하고 기존 12개월 결제 구조를 유지해 제외.
- 모든 tier explicit plugin rows: future plugin 누락 위험 때문에 제외.
- `*` wildcard row: API/validator/snapshot 전반의 특수값 누출 때문에 제외.
- Trial=0원 renewable subscription: Toss billing lifecycle과 섞이므로 별도 participation 선택.
- paid conversion 때 Trial 삭제: 조기 결제 사용자가 손해라서 제외.
- paid credits 이월/annual 12배 즉시 지급: monthly allowance 정책을 깨서 제외.
- 카드별 interval selector: 비교와 state consistency가 나빠 전역 selector 선택.
- browser 할인 계산: global policy를 우회하므로 server projection 선택.
- any access top-up: Trial/admin에게 불가능한 checkout을 노출하므로 paid period로 제한.
- 기존 migration 수정: applied history 위험 때문에 forward migrations 선택.
- worktree와 branch 동시 삭제: branch 삭제 승인이 없어 worktree만 제거.

## 9. 테스트 및 검증 결과

### 2026-08-26 fresh full verification, Node v22.22.3

| Repo | test | result | build |
|---|---|---|---|
| API | `npm test -- --runInBand` | 161 suites, 1,486 tests, 0 fail | exit 0 |
| customer | ChromeHeadless | 207/207 SUCCESS | exit 0, 493.49 kB |
| admin | ChromeHeadless | 258/258 SUCCESS | exit 0, 539.58 kB |

admin build는 성공했으나 500 kB budget을 39.58 kB 초과하는 기존 warning이 있다. API test의
`evidence database unavailable`, `network down` log는 의도된 failure fixture이며 실패가 아니다.
세 baseline→HEAD `git diff --check`도 exit 0이다.

### 2026-08-24 disposable PostgreSQL 16.14

- admin 45 migrations through `178810`, user 4
- pricing down/up, exact rows/constraints/index
- Trial race: participation/grant/ledger 각 1, payment artifacts 0
- two-connection credit race: negative/duplicate debit 없음
- container/tmpfs 삭제; 현재 55462 listener 없음

이 DB 검증은 8월 26일 재실행하지 않았다. 이후 final Trial billing guard는 Jest로 검증됐다.

### 2026-08-24 browser evidence

- customer 1280/390, selector/grid/copy/focus/product-code
- admin actual/manual/incomplete rejection/reload/Trial independence
- 9 screenshots, customer 53 URLs에서 Toss requests 0
- held GET old DOM→release new DOM, bounded helper 3/3
- 경로: `.superpowers/sdd/2026-08-24-pricing-and-catalog-clients/task-5-visual-evidence/`

compiled UI+fixture 검증이며 live API/DB/Toss가 아니다. 8월 26일 재촬영하지 않았다.

최종 fix diff 별도 review에서 Critical/Important/fix-caused Minor 없음. reviewer focused tests:
API 210, customer 63, admin 47.

## 10. 현재 구현 상태

| 항목 | 상태 | 남은 검증 |
|---|---|---|
| 새 가격/tiers/products/top-ups | 구현+자동+격리 DB | persistent DB/live Toss |
| actual/manual | 구현+자동+browser | live admin API/DB |
| Trial 400 | 구현+자동+격리 DB | cutoff 승인/실제 신규 user |
| paid priority/Trial fallback | 구현+자동+격리 DB | live account flow |
| monthly non-rollover/annual monthly grants | 구현+자동 | 실제 시간 경과 |
| allowlist/all | 구현+자동 | desktop end-to-end |
| ranked changes | 구현+자동 | Business 실제 charge |
| paid-only top-up | 구현+자동 | 새 packs 실제 Toss |
| customer/admin UI | 구현+자동+fixture browser | feature live integration |
| 돈 환불/provider cancellation | **미구현** | 설계도 미승인 |
| merge/deploy/shared migration | **하지 않음/확인 불가** | 별도 승인 |

## 11. 남은 TODO

가격/Trial:

- exact cutoff 확인, existing-user backfill 결정
- 필요 시 combined entitlement endpoint
- persistent DB backup/migration dry-run
- feature API/customer/admin live integration, test-key 6 recurring+3 top-up checkout
- admin bundle warning 별도 최적화 여부

환불:

- `next renewal cancel`, provider money refund, failed-operation credit refund를 분리해 설계
- 법률·약관·회계·CS 항목 분류와 사용자 승인
- 기획팀 요청서와 법무 초안의 각 주장을 `현재도 유효`, `현재 구현과 충돌/폐기`,
  `코드·운영 확인 필요`, `사업 결정 필요`, `법무·세무 확인 필요`로 분류
- 특히 잠정 전액환불, 정기결제 미판매, 결제→이용권 수동 발급, 가격 미확정이라는 8월 20일
  전제가 현재 PG 구현·승인 정책과 충돌하는지 확인하고 초안에 그대로 반영하지 않기
- 약관·개인정보처리방침·환불정책의 실제 현재 코드 정본과 초안이 여전히 일치하는지 확인
- 법무 주장마다 최신 공식 1차 자료에서 `정확한 법령/조문`, `현재 시행 여부·시행일`,
  `적용 요건`, `기간의 기산점과 계산`, `예외 요건`, `필수 고지·동의 절차`를 독립적으로
  재검증하고 확인일과 근거 링크를 남기기. 문서에 적힌 법률 해석이나 청약철회 기간을 그대로
  복사하지 않으며, 해석이 필요한 부분은 확정 결론 대신 법무 검토 필요사항으로 분리하기

기존 PG:

- `BILLING_DELETED` exact candidate/extant-previous repository integration test
- user-MID `PAYMENT_STATUS_CHANGED`/`DEPOSIT_CALLBACK`
- 가상계좌 발급·입금·만료·입금 후 취소
- renewal/retry/past_due/stopped 시간·fault 검증
- provider 데이터 기반 admin reconciliation/manual-review UI 검증
- merge/push/PR/deploy는 각각 별도 승인

## 12. 다음 세션 우선순위

1. 이 최신 handoff를 읽은 직후 아래 두 팀 문서를 처음 참고자료로 완전히 읽는다.
   - `clipper_docs/launch/2026-08-20-planning-team-requests.md`
   - `clipper_docs/launch/2026-08-20-legal-drafts-for-review.md`
2. 두 문서에서 환불·구독·가격·무료 플랜/Trial·자동 발급·CS·세무·개인정보·약관·미성년자·
   디지털콘텐츠·계속거래·AI 표시·수탁/국외이전과 관련된 참고/확인/고려 항목을 추출한다.
3. 추출 결과를 `유효`, `현재 코드/결정과 충돌`, `확인되지 않음`, `사업 결정`,
   `법무·세무·운영 확인`으로 분류한다. 문서 자체를 근거로 사실·법률·정책을 확정하지 않는다.
4. 두 문서의 법령·법안·청약철회·환불·계속거래·디지털콘텐츠 관련 주장은 다음 세션 시점의
   최신 공식 1차 자료로 다시 조사한다. 법령명/조문, 시행 여부·시행일, 적용 요건, 기간의
   기산점, 예외와 필수 고지·동의 요건, Clipper 적용 가능성을 표로 기록하고 확인일과 링크를
   남긴다. 불명확한 법률 해석은 법무 검토 대상으로 표시하며 자체적으로 확정하지 않는다.
5. 8월 21일/19일 handoff와 과거 환불 문서를 읽고 위 분류를 현재 PG 이력과 대조한다.
6. 7개 PG worktree status/diff/HEAD, listener cwd/health, DB migration count를 read-only 재확인.
7. cutoff는 미확정 운영값으로 유지하고 임의 수정·migration 적용 금지.
8. 환불/provider cancellation **설계**부터 시작. 현재 코드/OpenAPI/DB, 최신 Toss 공식 계약,
   최신 공식 법률·정책 자료와 법무 검토 필요사항을 대조한다.
9. brainstorming으로 질문 1개씩, 2~3개 대안 비교. 승인 전 구현 금지.

## 13. 주의사항 및 절대 하면 안 되는 작업

- localhost 5432와 persistent admin 5433에 pending migrations를 실행하지 않는다.
- applied migration file을 수정하지 않는다. 공유 DB 상태 확인 후 forward migration만 설계.
- 승인 없이 live charge/refund/provider cancel, merge/push/PR/deploy 금지.
- raw billing/secret key와 암호문 출력·문서화 금지.
- customer의 기존 `?? build/` 삭제/stage/commit 금지.
- `clipper_angular-meme-overlay-timeline-seek`, `clipper_web_api-operator-jwt-expiry-test`는 다른
  세션 소유이므로 변경/정리 금지.
- 3000/4201은 HTTP 200이지만 feature server가 아니다.
  - PID 146, cwd `web/clipper_web_api`, branch `merge/meme-overlay-into-dev`, HEAD `5e50065`
  - PID 78333, cwd `web/clipper_web_client`, branch `dev`, HEAD `4b361ef`
- current worktrees: PG 7개+위 다른 세션 2개. 삭제된 worktree branch는 모두 남아 있다.
- API status는 local remote-tracking ref 기준 +0/-0이나 이번 종료 시 fetch/ls-remote는 안 했다.
  실제 remote server 상태로 과장하지 않는다. 다른 PG repos는 upstream을 표시하지 않는다.

PG 기준점:

| repo | HEAD | status |
|---|---|---|
| angular | `f0da4e4a4aca26bbf08ccbc16856b085c06b0404` | clean |
| electron | `abdc5753741301f4bf22278a22ca8e20dc78ac24` | clean |
| infra | `e6ae78f58b559cf3715f6acaecf6ac067a4e7930` | clean |
| nestjs | `8e131e3f601f981259c7bf00bb1a3001631c0fe5` | clean |
| API | `a85e2fa665a8497ff66c4939e417fb10fc48df8d` | tracked clean |
| customer | `2fbd5e9c6c43b1efefd334cf57dc6bc80254cb43` | only `?? build/` |
| admin | `cbf7c52a20555ff736e0be7711dd3645fdfe59c4` | clean |

## 14. 참고 문서/자료

- API spec: `docs/superpowers/specs/2026-08-24-pricing-trial-and-entitlements-design.md`
- plans: 같은 API worktree의 `docs/superpowers/plans/2026-08-24-*.md` 세 개
- OpenAPI: `docs/api/openapi.yaml`
- evidence: API worktree `.superpowers/sdd/2026-08-24-*`
- 이전 최신 PG: `.codex/main/2026-08-21-toss-payments-pg-upgrade-consent-and-manual-verification-handoff.md`
- 초기 PG: `.codex/main/2026-08-19-toss-payments-pg-integration-session-handoff.md`
- refund policy notes: `.codex/main/2026-08-19-clipper-product-policy-business-meeting.md`
- refund meeting brief: `.codex/main/2026-08-19-clipper-pg-product-policy-meeting-brief.md`
- original PG design: `.codex/main/2026-08-18-toss-payments-pg-integration-design.md`
- catalog foundation: `.codex/implementation/2026-08-12-billing-product-catalog-foundation-plan.md`
- 기획팀 요청서(비최신 참고자료):
  `/Users/jina/project/adlight/clipper_docs/launch/2026-08-20-planning-team-requests.md`
- 법무 검토 초안(미검토·비최신 참고자료):
  `/Users/jina/project/adlight/clipper_docs/launch/2026-08-20-legal-drafts-for-review.md`

## 15. 다음 세션 시작 프롬프트

```text
Using Superpowers.

토스페이먼츠 PG 연동 작업을 이어서 진행해줘.

먼저 아래 문서를 완전히 읽어줘.
- /Users/jina/project/adlight/.codex/main/2026-08-26-toss-payments-pg-pricing-trial-entitlements-session-handoff.md
- /Users/jina/project/adlight/clipper_docs/launch/2026-08-20-planning-team-requests.md
- /Users/jina/project/adlight/clipper_docs/launch/2026-08-20-legal-drafts-for-review.md
- /Users/jina/project/adlight/.codex/main/2026-08-21-toss-payments-pg-upgrade-consent-and-manual-verification-handoff.md
- /Users/jina/project/adlight/.codex/main/2026-08-19-toss-payments-pg-integration-session-handoff.md

두 clipper_docs 문서는 다른 팀원이 2026-08-20 작성한 기획 요청서와 미검토 법무 초안이야.
정보가 최신화되지 않았고 잠정안·틀린 가정·검증되지 않은 법률 문구가 포함될 수 있으므로
source of truth로 취급하지 마. 먼저 끝까지 읽은 뒤 환불·구독·가격·무료 플랜/Trial·자동 발급·
CS·세무·개인정보·약관·미성년자·디지털콘텐츠·계속거래·AI 표시·수탁/국외이전에서 참고할
사항, 확인할 사항, 고려할 사항을 뽑아줘.

추출한 항목은 `현재도 유효`, `현재 코드/확정 정책과 충돌하거나 폐기`, `확인되지 않음`,
`사업 결정 필요`, `법무·세무·운영 확인 필요`로 나눠. 문서 문구만으로 사실이나 법률 판단을
확정하지 말고 실제 repository/OpenAPI/DB와 최신 공식 자료, 필요 시 전문가 검토와 대조해.
특히 문서의 잠정 전액환불, 정기결제 미판매, 결제→이용권 수동 발급, 가격 미확정 전제는
현재 PG 구현·이번 세션의 승인 정책과 충돌할 수 있으므로 그대로 가져오지 마.

특히 문서에 적힌 법령·법안·시행령·기관 가이드라인, 청약철회 가능 기간과 기산점,
디지털콘텐츠·계속거래의 철회/환불 예외, 필수 고지·동의 요건은 작성 당시 검토됐다는 이유로
맞다고 가정하지 마. 다음 세션 현재 시점의 국가법령정보센터와 소관 기관 등 최신 공식 1차
자료에서 정확한 법령명/조문, 현재 시행 여부와 시행일, 적용 요건, 기간 계산, 예외 요건을
독립적으로 다시 확인해. 각 항목에 확인일과 근거 링크를 남기고 Clipper의 실제 상품·결제·
서비스 제공 방식에 적용되는지 구분해. 해석상 여지가 있거나 전문가 판단이 필요한 부분은
확정하지 말고 `법무 검토 필요`로 표시해.

그다음 7개 toss-payments-pg-integration worktree의 branch, HEAD, git status, tracked/staged
diff를 read-only로 다시 확인해줘. customer의 기존 untracked build/는 삭제하거나 stage하지 마.
meme-overlay-timeline-seek와 operator-jwt-expiry-test는 다른 작업이므로 건드리지 마.

3000/4201 listener의 실제 cwd와 health, Docker 5433/5434/5435 DB migration count를
read-only로 확인해. 종료 시 3000/4201은 feature가 아니라 main web 디렉터리에서 실행 중이었다.
기존 DB에는 migration이나 쓰기를 하지 마.

가격·Trial·권한 코드는 API a85e2fa, customer 2fbd5e9, admin cbf7c52까지 구현·자동검증됐다.
단, free-trial migration의 eligible_from 2026-08-30T14:26:40.000Z는 정확한 시각을 내가
명시 승인했다는 기록이 확인되지 않았으므로 운영 적용 전 미확정 값으로 다뤄. applied
migration history를 수정하지 마.

다음 첫 제품 작업은 돈 환불/provider payment cancellation 설계야. 구현부터 시작하지 말고,
과거 환불 문서와 현재 코드/OpenAPI/DB를 대조한 뒤 Toss 최신 공식 문서와 관련 최신 공식
법률·정책 자료를 확인해줘. 다음 자동결제 취소, 실제 결제금 전액·부분 환불, 실패 작업의
내부 크레딧 반환은 서로 분리해.

현재 유효, 현재 구현과 충돌, 미결정, 법률·약관·회계·CS 확인 필요, 새 설계 누락으로
분류해줘. Superpowers brainstorming으로 현황을 요약하고 질문은 한 번에 하나씩, 2~3개
대안과 장단점을 제안해줘.

내가 설계를 승인하기 전에는 DB/migration 변경, refund 코드, provider 취소 호출, live
결제·환불, merge, push, PR, deploy를 하지 마. raw billing/secret key를 출력·문서화하지 마.

BILLING_DELETED exact candidate/extant-previous integration test, user-MID webhook,
가상계좌 발급·입금·만료 TODO는 지우지 말되 환불 설계와 섞지 마.
```
