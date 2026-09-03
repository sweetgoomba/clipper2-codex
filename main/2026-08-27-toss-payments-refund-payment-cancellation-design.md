# TossPayments 환불·결제취소 조사 및 설계 검토

- 작성일: 2026-08-27
- 상태: 조사·현황 검증·설계안
- 구현 승인 상태: **미승인**
- 범위: TossPayments 결제취소, 금전 환불, entitlement 종료, credit 조정 및 실패 작업 credit 복구의 경계와 환불 시스템 설계 후보

## 0. 문서의 성격과 사용 원칙

이 문서는 구현 명세가 아니라 현재 repository와 공식 자료를 기준으로 만든 검토 자료다. 여기서 `추천`은 기술 구조에 관한 추천이며, 환불 가능 기간·산식·예외·고객 고지 같은 사업·법무·회계·운영 정책이 승인됐다는 뜻이 아니다.

다음 우선순위를 적용했다.

1. 현재 repository의 실제 코드·OpenAPI·DB 모델·적용 migration 상태
2. 현재 세션에서 이미 승인된 확정 정책 및 설계 결정
3. 최신 TossPayments 공식 문서
4. 국가법령정보센터 및 소관 기관의 최신 공식 1차 자료
5. `.codex`의 최신 handoff/task/decision 문서
6. 과거 세션 문서
7. 다른 팀원이 작성한 잠정 기획·법무 문서

실제 코드와 문서가 다를 때 문서를 현재 사실로 덮어쓰지 않았다. 반대로 코드에 있다는 이유만으로 그 정책이 사업·법무 승인을 받았다고 간주하지도 않았다. 특히 다음 항목은 재검증 없이 승계하지 않았다.

- 잠정 전액 환불 정책
- 정기결제 미판매
- 결제 후 이용권 수동 발급
- 가격 미확정
- Trial 운영 방식
- 무료 플랜 entitlement 정책

이 문서를 작성하면서 코드, DB, provider, migration history는 변경하지 않았다. TossPayments 실제 취소·환불 호출, live payment, live refund, merge, push, PR, deploy도 수행하지 않았다.

## 1. 요약 결론

현재 구현에는 구독의 다음 결제 방지를 위한 **기간 말 취소**가 있지만, 실제 결제금의 전액·부분 환불을 수행하는 내부 환불 subsystem은 없다. `operation_refund`는 실패한 작업에 사용된 내부 credit을 복구하는 기능일 뿐, TossPayments의 payment cancellation이나 고객에게 돈을 돌려주는 환불이 아니다.

따라서 다음 lifecycle을 독립적으로 모델링해야 한다.

1. 구독 자동결제 취소
2. 실제 결제금의 전액 환불
3. 실제 결제금의 부분 환불
4. entitlement 종료
5. 구독 결제로 지급된 credit의 회수·조정
6. top-up 결제 환불과 top-up credit 조정
7. 실패한 작업의 내부 credit 반환·복구
8. 보상성 credit 지급

추천하는 기술 방향은 처음부터 full/partial을 표현할 수 있는 durable refund case 구조를 만들되, 실제로 활성화하는 판단 규칙은 전략·법무·세무회계·운영CS가 승인한 branch만 허용하는 방식이다. 이는 “초기에는 무조건 전액 환불”이라는 뜻이 아니다. 전액 환불도 사용 여부, 법정 철회, 회사 귀책, 미성년자 계약 등 정책과 법적 예외가 필요하므로 별도의 승인 대상이다.

일반적인 환불 금액은 사용자가 요구한 숫자나 관리자가 자유 입력한 숫자로 정하지 않는다. 시스템이 versioned policy와 현재 상태를 바탕으로 eligibility, 금액, entitlement 종료 시점, credit 효과를 계산하고, 필요한 경우 권한 있는 담당자가 그 계산 결과를 승인하는 구조가 적절하다. 예외적인 수기 override가 필요하다면 일반 경로와 분리하고 더 높은 권한, 사유, 증빙, 감사기록을 요구해야 한다.

## 2. Phase A — Repository Current State

### 2.1 Repository와 worktree

2026-08-27 read-only 확인 기준이다.

| worktree | branch/범위 | HEAD | tracked diff | staged diff | 비고 |
|---|---|---:|---|---|---|
| Angular | `toss-payments-pg-integration` | `f0da4e4a4aca` | 없음 | 없음 | clean |
| Electron | `toss-payments-pg-integration` | `abdc57537413` | 없음 | 없음 | clean |
| Infra | `toss-payments-pg-integration` | `e6ae78f58b55` | 없음 | 없음 | clean |
| NestJS | `toss-payments-pg-integration` | `8e131e3f601f` | 없음 | 없음 | clean |
| Web admin | `toss-payments-pg-integration` | `cbf7c52a2055` | 없음 | 없음 | clean |
| Web API | `toss-payments-pg-integration` | `a85e2fa665a8` | 없음 | 없음 | clean |
| Web customer | `toss-payments-pg-integration` | `2fbd5e9c6c43` | 없음 | 없음 | 기존 untracked `build/`만 존재 |

`customer`의 untracked `build/`는 삭제하거나 stage하지 않았다.

다른 병렬 작업도 read-only로 확인했다.

| 작업 | HEAD | 관찰된 범위 | 환불 설계와의 관계 |
|---|---:|---|---|
| `meme-overlay-timeline-seek` | `9568f436a57d` | desktop Angular meme 관련 파일 | 직접 관련 없음. 수정 금지 |
| `operator-jwt-expiry-test` | `a1d91b6165eb` | `operator-jwt.strategy.spec.ts` | 직접 refund domain은 아니나 향후 관리자 환불 권한·인증과 간접 접점 가능. 수정 금지 |

현재 환불 설계가 향후 공유할 가능성이 높은 영역은 Web API의 payment/access/credit 모듈, admin API/UI의 운영자 권한과 환불 처리 화면, admin DB의 migration/schema다. 구현 전 각 worktree의 최신 HEAD와 migration 번호 충돌을 다시 확인해야 한다.

### 2.2 Running processes와 listener

| port | 실제 cwd | health 확인 | 판단 |
|---:|---|---|---|
| 3000 | `/Users/jina/project/adlight/web/clipper_web_api` | HTTP 200 | feature worktree가 아니라 main web API 디렉터리 |
| 4201 | `/Users/jina/project/adlight/web/clipper_web_client` | HTTP 200 | feature worktree가 아니라 main web client 디렉터리 |

따라서 이 listener를 feature 구현 검증 결과로 간주하면 안 된다.

### 2.3 Database

모든 확인은 read-only로 수행했으며 migration이나 write를 실행하지 않았다.

| port | DB | applied migration | feature code와의 관계 | 현재 판단 |
|---:|---|---:|---|---|
| 5433 | `clipper_admin` | 28, latest `178660...` | feature API에는 총 45개, `178810...`까지 존재 | feature 기준 17개가 적용되지 않은 상태 |
| 5434 | `clipper_release` | 2 | feature datasource와 일치 | 현재 일치 |
| 5435 | `clipper_user` | 7 | feature datasource에는 4개 | 병렬 작업의 migration 3개가 더 적용된 상태 |

5433은 feature schema를 실제 적용해 검증한 DB가 아니다. 5435는 feature 코드보다 앞서거나 다른 병렬 migration을 포함하므로, 향후 migration 작성 시 번호·schema·적용 순서를 다시 조정해야 한다. 기존 DB와 migration history는 수정하지 않는다.

### 2.4 현재 코드에서 확인된 가격·Trial·entitlement

API `a85e2fa`, customer `2fbd5e9`, admin `cbf7c52`를 기준으로 과거 자동검증 기록과 현재 파일을 대조했다.

현재 pricing catalog는 다음 값을 갖는다.

| plan | 월 결제 | 연 결제 |
|---|---:|---:|
| Basic | 5,900원 | 58,800원 |
| Pro | 10,900원 | 82,800원 |
| Business | 29,900원 | 234,000원 |

연간 구독은 연 결제금 선결제이며, 구독 benefit credit은 월 단위 grant로 설계돼 있다.

현재 top-up catalog는 다음과 같다.

| credits | 가격 | 현재 유효기간 |
|---:|---:|---:|
| 400 | 5,900원 | 365일 |
| 1,000 | 10,900원 | 365일 |
| 4,000 | 29,900원 | 365일 |

365일은 현재 코드 값이지만 영구 확정 정책이라는 증거는 없다.

현재 Trial은 다음과 같이 구현돼 있다.

- 계정당 한 번 400 credits
- Trial 자체 만료일 없음
- 유료 전환 후에도 남은 Trial credit 유지
- effective access는 paid/admin access를 우선하고, 없으면 Trial fallback
- Trial과 Basic은 각각 정의된 5개 plugin allowlist
- Pro와 Business는 등록된 모든 plugin 사용 가능

free-trial migration의 `eligible_from = 2026-08-30T14:26:40.000Z`는 코드에 존재하지만 사용자가 정확한 시각을 승인했다는 기록이 없다. 운영 적용 전 **미확정 값**으로 취급한다. 이미 적용된 migration history를 수정해서 해결해서는 안 되며, 실제 적용 여부와 보정 방식은 별도 설계·승인이 필요하다.

관련 파일:

- [가격 catalog migration](/Users/jina/project/adlight/.worktrees/clipper_web_api-toss-payments-pg-integration/src/core/database/migrations/admin/1788000000000-ConfigurePricingCatalog.ts)
- [Trial policy migration](/Users/jina/project/adlight/.worktrees/clipper_web_api-toss-payments-pg-integration/src/core/database/migrations/admin/1788100000000-CreateFreeTrialPolicy.ts)
- [승인된 가격·Trial·entitlement 설계](/Users/jina/project/adlight/.worktrees/clipper_web_api-toss-payments-pg-integration/docs/superpowers/specs/2026-08-24-pricing-trial-and-entitlements-design.md)
- [effective access service](/Users/jina/project/adlight/.worktrees/clipper_web_api-toss-payments-pg-integration/src/modules/access/application/effective-access.service.ts)

### 2.5 현재 top-up의 실제 동작

현재 코드가 구현하는 상태는 다음과 같다.

- top-up 구매 시점에는 active paid subscription이 필요하다.
- paid access가 끝나도 이미 발급된 top-up grant 자체는 사라지지 않는다.
- 다만 paid 또는 admin plan access가 다시 생길 때까지 top-up credit을 사용할 수 없다.
- 보류 중에도 top-up 유효기간은 계속 흐른다.
- Trial만으로는 top-up credit을 사용할 수 없다.

이것은 **현재 코드에서 확인된 동작**이지, 전략팀이 이 세부 정책을 승인했다는 뜻은 아니다. 전략팀 문구인 “추가 크레딧 충전(유료 플랜 대상 무제한 이용 가능)”은 유료 플랜 대상이라는 큰 방향만 시사할 뿐, 아래를 확정하지 않는다.

- 구매할 때만 유료 플랜이면 되는지
- 사용할 때도 유료 플랜이어야 하는지
- 구독 종료 후 top-up을 보유만 할지, 계속 쓸 수 있는지
- `admin access`를 유료 플랜과 동일하게 취급할지
- “무제한”이 구매 횟수, 총량, 기간 중 사용 중 무엇을 뜻하는지

특히 전략팀이 “구매할 때만 유료 플랜이면 되고, 구매한 top-up은 구독 종료 후에도 사용할 수 있다”고 정하면 기술적으로 새로운 entitlement 문제가 생긴다. top-up 자체에는 plan tier나 plugin 권한이 없다. 따라서 이용권 없이 top-up을 쓸 때 마지막 구독 등급의 기능을 허용할지, 공통 기능만 허용할지, 별도의 top-up-only entitlement를 만들지 정해야 한다. 이 결정을 생략하면 credit은 있는데 사용할 기능이 없거나, 반대로 구독 없이 구독 기능을 사용할 수 있는 모순이 생긴다.

여기서 `admin access`는 관리자가 내부 운영·지원 목적으로 부여할 수 있는 access source를 뜻한다. 일반 고객이 구매한 유료 구독이 아니므로, top-up 구매·사용 자격에서 paid subscription과 같게 취급할지는 별도 정책이다.

### 2.6 현재 결제·구독·credit 구현

현재 코드에서 확인된 내용:

- 결제 승인 후 자동 fulfillment가 구현돼 있다.
- 구독 취소는 현재 period-end cancellation이며 다음 자동결제를 막는 개념이다.
- 이 구독 취소는 TossPayments의 과거 결제 payment cancellation을 호출하지 않는다.
- `operation_refund`는 실패한 작업에서 차감된 내부 credit을 복구한다.
- provider에서 이미 취소된 payment는 reconciliation 과정에서 외부 상태로 관찰할 수 있다.
- 외부 취소 관찰 후 entitlement·credit을 자동 정리하는 완결된 내부 효과는 없다.

관련 파일:

- [payment fulfillment service](/Users/jina/project/adlight/.worktrees/clipper_web_api-toss-payments-pg-integration/src/modules/payments/application/payment-fulfillment.service.ts)
- [TossPayments provider interface](/Users/jina/project/adlight/.worktrees/clipper_web_api-toss-payments-pg-integration/src/modules/payments/domain/toss-payments.provider.ts)
- [OpenAPI](/Users/jina/project/adlight/.worktrees/clipper_web_api-toss-payments-pg-integration/docs/api/openapi.yaml)
- [OpenAPI contract test](/Users/jina/project/adlight/.worktrees/clipper_web_api-toss-payments-pg-integration/src/modules/payments/presentation/payments-openapi-contract.spec.ts)

### 2.7 구현됐지만 별도 확인이 필요한 것

- feature DB migration 전체가 실제 DB에 적용된 상태의 검증
- 운영 Toss MID가 사용하는 date-based API version
- top-up 구매·사용 자격의 사업 승인 여부
- Trial `eligible_from` 정확한 시각
- public legal content의 실제 승인 여부와 현행 처리자·수탁자 반영 여부
- 외부에서 취소된 payment를 reconciliation했을 때 내부 entitlement·credit을 어떻게 맞출지

### 2.8 설계만 있거나 아직 존재하지 않는 것

현재 repository에는 다음 환불 기능이 없다.

- customer refund request API/UI
- admin/CS refund case 조회·심사·승인 UI
- payment full/partial cancellation provider method
- refund eligibility evaluator
- 환불 금액 산정과 policy version snapshot
- refund case와 provider attempt의 durable 상태 모델
- 환불 전 사용 상태 revalidation과 동시성 차단
- idempotency key 영속화·재사용
- provider timeout/unknown outcome reconciliation
- 환불 완료 후 entitlement 종료와 credit adjustment orchestration
- refund audit trail과 권한 모델
- 고객 통지와 증빙 흐름
- 회계·세무 후속 처리 연계

## 3. Phase B — 과거 문서 및 공식 자료 대조

### 3.1 읽고 대조한 내부 문서

- `.codex/main/2026-08-26-toss-payments-pg-pricing-trial-entitlements-session-handoff.md`
- `clipper_docs/launch/2026-08-20-planning-team-requests.md`
- `clipper_docs/launch/2026-08-20-legal-drafts-for-review.md`
- `.codex/main/2026-08-21-toss-payments-pg-upgrade-consent-and-manual-verification-handoff.md`
- `.codex/main/2026-08-19-toss-payments-pg-integration-session-handoff.md`
- repository에서 `refund`, `환불`, `결제취소`, `payment cancellation`, `CANCELED`, `PARTIAL_CANCELED`를 검색해 발견한 관련 기록과 코드

두 `clipper_docs` 문서는 2026-08-20 당시 다른 팀원이 작성한 잠정 기획 요청과 미검토 법무 초안이다. 사실 또는 법률의 source of truth로 사용하지 않았다.

### 3.2 과거 판단이 현재 상태로 수정된 항목

| 과거 문서·가정 | 새 근거 | 수정 이유 | 현재 적용 상태 |
|---|---|---|---|
| 정기결제 미판매 | 현재 subscription·billing 구현 | 실제 코드에 정기 구독 lifecycle 존재 | 폐기/충돌 |
| 결제 후 이용권 수동 발급 | 자동 fulfillment 구현 | 승인 결제에서 entitlement 자동 발급 | 폐기/충돌 |
| 가격 미확정 | pricing catalog migration과 승인 설계 | 구체 가격이 코드에 반영 | 현재 코드 사실. 사업 변경 가능성은 별개 |
| Trial/free 정책 없음 또는 과거 잠정안 | Trial policy migration과 effective access | 400 credits, no expiry, fallback 및 plugin 범위 구현 | 현재 코드 사실. `eligible_from` 시각은 미확정 |
| 전액 환불을 폭넓게 허용 | 현행 구현에 돈 환불 기능 없음; 공식 법과 상품 사용 상태 검토 필요 | 과거 문구만으로 환불 정책 확정 불가 | 폐기/재결정 필요 |
| subscription cancellation과 refund를 혼용 | 현재 period-end cancellation과 Toss payment cancel은 별개 | 서로 다른 원인·상태·provider 호출 | 분리 필요 |
| 실패 작업 refund와 돈 환불을 혼용 가능 | `operation_refund` 구현 | 내부 credit restoration일 뿐 금전 이동 없음 | 명칭·domain 경계 명확화 필요 |
| AI 관련 의무가 2026-01-22 시행 예정 또는 단순 미래 사항 | AI 기본법 제31조는 2026-01-22 시행, 현재 통합 법령은 2026-07-21 개정문, 시행령은 2026-08-20 현행 | 현재 시점의 시행 법령으로 다시 표기해야 함 | 법령 사실 업데이트; Clipper 적용은 법무 검토 |

### 3.3 영역별 분류

#### 3.3.1 현재도 유효

- 가격·Trial·entitlement의 현재 코드 상태
- 연간 결제 선결제와 월 단위 subscription benefit credit grant 구조
- payment 승인 후 자동 fulfillment
- period-end subscription cancellation
- `operation_refund`의 실패 작업 credit 복구 역할
- top-up이 subscription payment와 별도 결제라는 domain 구분
- 환불과 entitlement/credit 조정이 하나의 상태가 아니라는 원칙
- 적용 가능한 청약철회·환불 규정과 필수 고지는 최신 공식 자료 기준으로 재검토해야 한다는 요구

#### 3.3.2 현재 구현·확정 정책과 충돌하거나 폐기

- 정기결제 미판매
- 결제 후 이용권 수동 발급
- 가격 미확정
- Trial/free entitlement가 없다는 전제
- 사용 여부와 예외를 보지 않는 잠정 “무조건 전액 환불”
- subscription cancellation을 payment refund와 같은 것으로 취급하는 설명
- `operation_refund`를 고객 금전 환불로 해석하는 설명

#### 3.3.3 확인되지 않음

- 운영 MID의 실제 Toss date-based API version
- Trial `eligible_from`의 승인된 정확한 시각
- top-up 365일 유효기간이 확정 정책인지
- strategy 문구의 “무제한” 정확한 의미
- top-up의 구매 시점·사용 시점 paid-plan 요건
- public legal page 문구의 법무 승인 여부
- Toss가 수탁자·국외이전 등 개인정보 고지에 어떻게 반영돼야 하는지에 필요한 실제 계약·데이터 흐름
- Clipper가 법률상 계속거래에 해당하는 범위
- 각 결제수단과 운영 MID 계약에서 실제 가능한 취소 조건·시간 제한

#### 3.3.4 사업 결정 필요

- 일반 환불 가능 기간과 “미사용”의 정의
- 월 구독 환불 정책
- 연간 구독의 미래 미제공 기간에 대한 중도 해지·부분 환불 정책과 산식
- top-up 환불 가능 조건과 부분 사용 시 처리
- 구독 환불 시 access 종료 시점: 즉시 또는 환불 대상 기간과 연동
- 회사 귀책·중복 결제·오결제 등 정책 분류
- top-up의 구매·보유·사용 자격과 구독 종료 후 동작
- Trial과 top-up이 함께 있을 때 소비 우선순위 및 환불 효과
- admin access가 top-up 자격에 미치는 영향
- 자동 심사 범위와 사람 승인 범위
- 고객 self-service 여부
- 예외 override를 허용할지와 승인 권한

#### 3.3.5 법률·약관·회계·CS 확인 필요

- `법무`: 전자상거래법상 청약철회 기간·기산점·디지털콘텐츠 예외가 Clipper 상품 구조에 적용되는 방식
- `법무`: 계속거래 해당 여부와 중도 해지·환급 규정 적용
- `법무`: 미성년자 계약 동의·취소 처리와 본인·법정대리인 확인
- `법무`: 회사 귀책, 표시·광고·상품 불일치, 서비스 장애 등 법정 예외
- `법무`: 환불·해지 약관, 결제 전 고지·동의, 디지털콘텐츠 제공 개시 동의·철회 제한 고지
- `법무`: AI 생성물·서비스 표시 의무가 Clipper에 적용되는지와 표시 방식
- `법무`: Toss 및 기타 처리업체의 개인정보 처리위탁·국외이전·자동화된 결정 관련 고지
- `세무·회계`: 전액·부분 취소의 매출 인식, 부가세, 현금영수증·카드전표·세금계산서 정정
- `세무·회계`: 연간 선결제와 월별 서비스 제공, 미래분 환불의 회계 처리
- `운영·CS`: 접수 채널, 증빙, 응답 SLA, 예외 escalation, 고객 안내 template
- `운영·CS`: provider 성공·내부 처리 실패·unknown outcome 때 수동 대응과 재처리
- `운영·CS`: 관리자 권한, 이중 승인 필요 여부, 수기 override 통제

### 3.4 요청 영역별 추출·검증 matrix

| 영역 | 현재도 유효 | 충돌·폐기 | 확인되지 않음 | 사업 결정 필요 | 전문가 확인 필요 |
|---|---|---|---|---|---|
| 환불 | subscription cancellation, money refund, operation credit restoration은 서로 다름 | 잠정 무조건 전액 환불, 세 lifecycle 혼용 | 결제수단별 실제 취소 조건과 운영 MID 제약 | 상품별 eligibility·산식·예외 | `법무` 철회·예외, `세무·회계` 취소 처리, `운영·CS` 접수·승인 |
| 구독 | 정기 구독과 period-end cancellation 구현 | 정기결제 미판매 전제 | 계속거래 해당 범위 | 월·연간 중도 해지와 access 종료 시점 | `법무` 계속거래·약관, `세무·회계` 연간 매출 인식 |
| 가격 | 현재 catalog에 구체 가격 존재 | 가격 미확정 전제 | 현 가격의 향후 변경 계획 | 할인·연간 환불 시 가격 산식 | `세무·회계` 공급가액·부가세·반올림 |
| 무료 플랜/Trial | 1회 400, no expiry, paid/admin 우선 후 fallback 구현 | Trial/free가 없다는 과거 전제 | `eligible_from` 정확한 승인 시각 | Trial 사용·top-up과의 우선순위 변경 여부 | `법무` 표시·조건 고지, `운영·CS` 예외 처리 |
| 자동 발급 | 결제 승인 후 자동 fulfillment 구현 | 결제 후 수동 이용권 발급 전제 | 외부 취소 관찰 뒤 자동 내부 효과 | 실패 시 고객 access를 언제 열고 닫을지 | `운영·CS` fulfillment·환불 장애 대응 |
| CS | 개별 case와 정책 승인을 구분해야 함 | 관리자가 정상 건 금액을 임의 입력하는 방식 | 현재 조직·권한·SLA | 자동 승인과 사람 검토 범위 | `운영·CS` 접수, 증빙, escalation, 안내 |
| 세무·회계 | 관련 법령과 정정 제도 존재 | 잠정 법무 초안을 회계정책으로 사용 | Clipper의 실제 분개·증빙 방식 | 회사가 채택할 연간 할인 회수 등 | `세무·회계` 전액·부분 취소, 매출, 세금계산서·증빙 |
| 개인정보 | 실제 데이터 흐름 기준 검토 원칙 | 미검토 초안을 확정 방침으로 취급 | Toss 계약, 처리 데이터, 보유·재위탁 | 서비스가 수집할 환불계좌·증빙 최소범위 | `법무` PIPA와 처리방침, `운영·CS` 접근권한 |
| 약관 | 현재 구현·실제 상품과 일치해야 함 | placeholder 포함 초안을 승인 약관으로 취급 | 최종 승인 문구 | 회사가 제공할 추가 보장 정책 | `법무` 철회·해지·환불·제공 개시 고지 |
| 미성년자 | 민법상 성년·동의·취소 기본 규정 존재 | 일반 미사용 환불 규칙만 적용한다는 가정 | 현재 연령·대리인 확인 수단 | 미성년자 가입·구매 허용 범위 | `법무` 계약 취소, `운영·CS` 본인·대리인 확인 |
| 디지털콘텐츠 | 제공 개시와 철회 제한에 법정 요건 존재 | credit 사용 즉시 무조건 환불 불가라는 단정 | Clipper 각 기능의 법적 성격 | sample·체험·고지 UX 범위 | `법무` 가분성·제공 개시·예외 적용 |
| 계속거래 | 관련 정의와 해지·환급 규정 존재 | 모든 SaaS 구독에 자동 적용/비적용 단정 | Clipper 월·연간 계약의 해당 여부 | 법 허용 범위 안의 중도 해지 정책 | `법무` 적용 판단, `세무·회계` 미래 미제공분 처리 |
| AI 표시 | AI 기본법 제31조와 시행령 시행 중 | 시행 전이라는 과거식 표기 | Clipper 기능별 표시 대상 | 표시 위치·제품 UX | `법무` 적용 범위·문구, 제품 확인 |
| 수탁/국외이전 | PIPA 제26조·제28조의8 관련 규정 존재 | 현 provider 목록이 완결됐다는 가정 | Toss와 타 업체의 실제 역할·저장 위치 | 필요 최소 처리업체와 데이터 흐름 | `법무·개인정보` 위탁·국외이전·재위탁 고지 |

### 3.5 근거 성격의 분리

- **사실로 확인된 것**: 공식 Toss 문서의 API 동작과 현행 공식 법령에 실제 규정이 존재한다는 점. 법령이 Clipper에 적용된다는 해석까지 포함하지 않는다.
- **현재 코드에서 확인된 것**: 가격, Trial, entitlement, top-up gate, 자동 fulfillment, period-end cancellation, `operation_refund`, refund subsystem 부재.
- **과거 문서에만 존재하는 것**: 정기결제 미판매, 수동 이용권 발급, 미확정 가격, 폭넓은 잠정 전액 환불 등 현재 코드와 충돌하거나 승인을 입증하지 못하는 주장.
- **최신 공식 자료에서 새롭게 확인된 것**: Toss idempotency key 15일, 국내 취소 webhook 비의존, 가상계좌 취소 차이, 현행 법령의 시행 상태와 조문.
- **해석 또는 전문가 판단이 필요한 것**: 디지털콘텐츠·계속거래·미성년자·AI 표시·개인정보 규정의 Clipper 적용, 회계 처리, CS 예외와 권한.

## 4. TossPayments 최신 공식 문서 확인 결과

확인일은 2026-08-27이다. 과거 handoff가 아니라 TossPayments 공식 문서를 기준으로 다시 확인했다.

### 4.1 Payment cancellation API

- endpoint: `POST /v1/payments/{paymentKey}/cancel`
- `cancelReason`: 필수, 최대 200자
- 전액 취소: `cancelAmount`를 보내지 않음
- 부분 취소: `cancelAmount`를 보냄
- 응답 Payment 객체의 대표 상태: `CANCELED`, `PARTIAL_CANCELED`
- 취소 이력: `cancels` 배열
- 개별 취소 식별·추적: `transactionKey`
- 잔여 취소 가능 금액과 부분 취소 가능 여부를 provider 응답에서 확인 가능

출처: [TossPayments 결제 취소 가이드](https://docs.tosspayments.com/guides/v2/cancel-payment), [TossPayments Core API](https://docs.tosspayments.com/reference)

### 4.2 Idempotency와 retry

- POST 요청에 idempotency key를 사용할 수 있다.
- key 최대 길이는 300자다.
- 같은 key의 결과 보존 기간은 15일이다.
- 동일 요청이 처리 중이면 409 응답 가능성이 있다.
- timeout이나 응답 유실 때 새 key를 무작정 발급하면 중복 취소 위험이 있다.

따라서 환불 attempt마다 key를 durable storage에 저장하고 같은 logical attempt의 retry에서 재사용해야 한다. 15일 이후나 상태 미확정 장기 건은 provider Payment 조회와 수동 reconciliation이 필요하다.

출처: [TossPayments API 인증 및 멱등성](https://docs.tosspayments.com/reference/using-api/authorization)

### 4.3 동기 응답, webhook, reconciliation

- 국내 결제 취소에서는 일반적으로 `CANCEL_STATUS_CHANGED` webhook에 의존할 수 없다.
- 취소 API의 동기 응답을 우선 처리하되, timeout·응답 유실·내부 transaction 실패를 대비해 Payment 조회 reconciliation이 필요하다.
- webhook은 전달 실패 시 최대 7회 재전송된다.
- webhook이 존재하더라도 도착 순서나 동기 API 응답과의 경쟁을 고려해야 한다.

출처: [Webhook 이벤트](https://docs.tosspayments.com/reference/using-api/webhook-events), [Webhook 가이드](https://docs.tosspayments.com/guides/v2/webhook)

### 4.4 가상계좌

- 입금 전에는 전액 취소만 가능하고 별도의 환불계좌가 필요하지 않다.
- 입금 후 부분 취소에는 환불계좌 정보가 필요할 수 있다.
- 취소가 즉시 확정되지 않고 `PENDING` 등의 상태를 거칠 수 있다.
- 계좌 유효성, 환불 가능 시간, 은행 처리 결과 때문에 카드와 다른 비동기 운영 흐름이 필요하다.

가상계좌의 발급·입금·만료 검증은 기존 TODO로 유지하며 이번 환불 설계의 첫 구현 범위로 끌어오지 않는다. 다만 환불 subsystem의 상태 모델이 비동기 완료를 표현할 수 있어야 한다.

### 4.5 API version

현재 코드의 `/v1` path만으로 실제 date-based API version을 알 수 없다. test/live MID별 개발자센터 설정을 확인해야 하며, 공식 versioning 문서와 맞춰야 한다.

출처: [TossPayments API 버전](https://docs.tosspayments.com/reference/versioning)

## 5. 최신 공식 법률·정책 자료 확인

아래는 법령상 규정의 존재를 확인한 것이며, Clipper의 실제 상품·계약 구조에 그대로 적용된다는 법률 판단이 아니다.

### 5.1 전자상거래 등에서의 소비자보호에 관한 법률

- 확인 규정: 제17조 청약철회, 제18조 청약철회 등의 효과
- 현재 시행 여부: 시행 중
- 현행 기준 확인일: 2026-08-27
- 일반 청약철회: 법정 서면 등을 받은 날 또는 재화·용역 공급이 늦은 경우 공급 개시일부터 7일 등 법정 기산 규칙 존재
- 표시·광고 또는 계약 내용과 다르게 이행된 경우: 공급받은 날부터 3개월 이내이면서 그 사실을 안 날 또는 알 수 있었던 날부터 30일 이내
- 디지털콘텐츠: 제공이 개시된 경우 철회 제한 가능성이 있으나, 가분적 제공·미제공 부분, 사전 고지, 시험사용 상품 등 법정 요건을 함께 검토해야 함
- 적법한 철회 시 대금 환급: 법정 요건 아래 3영업일 기준과 결제업자에 대한 취소·정지 요청 의무가 문제됨
- 환급 지연 시 시행령상 지연배상률 15% 규정 확인

공식 근거: [전자상거래법 제17조·제18조](https://www.law.go.kr/LSW/lsLawLinkInfo.do?chrClsCd=010202&lsId=009318&lsJoLnkSeq=1000527255), [전자상거래법 시행령 관련 규정](https://www.law.go.kr/LSW/lsLinkCommonInfo.do?lspttninfSeq=63485)

적용 판단:

- 법령상 규정: 확인 완료
- Clipper의 구독, Trial, credit, top-up 각각에 적용되는 방식: 법무 검토 필요
- “credit을 일부 사용하면 언제나 환불 불가”라고 단정 가능 여부: 법무 검토 필요
- 디지털콘텐츠 제공 개시 동의·철회 제한 고지의 현 UI 충족 여부: 법무 및 구현 검토 필요
- 회사 귀책·불일치·법정 취소 사유: 일반 사업 정책보다 우선할 수 있으므로 법무 검토 필요

### 5.2 계속거래

방문판매 등에 관한 법률에는 계속거래 정의와 계약 해지·환급 관련 규정이 존재한다. 그러나 모든 SaaS 구독이 자동으로 동일하게 분류되는 것은 아니며 계약기간, 거래 구조, 대금 지급 방식 등 적용 요건을 확인해야 한다.

공식 근거: [방문판매법 제31조 관련](https://www.law.go.kr/lsLinkCommonInfo.do?lsJoLnkSeq=1026852729), [계속거래 정의·제32조 관련](https://law.go.kr/detcInfoP.do?detcSeq=50562)

적용 판단:

- 법령상 제도 존재: 확인 완료
- Clipper 월간·연간 구독 해당 여부: 법무 검토 필요
- 연간 중도 해지 시 미래 미제공 기간 환급 산식과 위약금 가능 범위: 법무·사업·회계 공동 검토 필요

### 5.3 미성년자

민법상 성년은 19세이며, 미성년자의 법률행위는 원칙적으로 법정대리인의 동의와 취소 가능성 문제가 있다.

공식 근거: [민법 제4조](https://www.law.go.kr/lsLinkCommonInfo.do?chrClsCd=010202&lsJoLnkSeq=1026056227), [민법 제5조](https://www.law.go.kr/lsLinkCommonInfo.do?lsJoLnkSeq=1031397911)

적용 판단:

- 법령상 기본 규정: 확인 완료
- Clipper의 연령 확인, 법정대리인 동의, 취소 요청자 확인 절차: 법무·운영 검토 필요
- 미성년자 취소를 일반 “미사용 환불” 규칙으로 제한 가능하다는 결론: 내릴 수 없음

### 5.4 개인정보 처리위탁·국외이전·자동화된 결정

- 개인정보보호법 제26조: 업무위탁에 관한 문서화·공개·관리감독 등
- 개인정보보호법 제28조의8: 개인정보 국외이전의 근거·고지 등
- 개인정보보호법 제37조의2: 자동화된 결정에 대한 정보주체 권리와 사업자 의무

공식 근거: [개인정보보호법 제26조](https://www.law.go.kr/LSW/lsSideInfoP.do?docCls=jo&joBrNo=00&joNo=0026&lsiSeq=270351&urlMode=lsScJoRltInfoR), [제28조의8](https://www.law.go.kr/lsLinkCommonInfo.do?chrClsCd=010202&lsJoLnkSeq=1029334953), [제37조의2](https://www.law.go.kr/LSW/lsLinkCommonInfo.do?chrClsCd=010202&lsJoLnkSeq=1029334889)

적용 판단:

- 법령상 규정: 확인 완료
- TossPayments와 다른 처리업체의 법적 지위, 실제 처리 데이터, 저장 위치, 재위탁·국외이전 여부: 계약과 데이터 흐름 확인 필요
- 자동 환불 eligibility 또는 fraud 판단이 제37조의2의 자동화된 결정에 해당하는지: 법무 검토 필요
- 현 개인정보처리방침의 수탁자·업무·국외이전 표기 적정성: 법무·개인정보 담당 확인 필요

### 5.5 AI 표시

인공지능 발전과 신뢰 기반 조성 등에 관한 기본법 제31조의 투명성 의무는 2026-01-22 시행됐고, 현재 확인한 통합 법령은 2026-07-21 개정문이다. 시행령 제23조도 현재 시행 중이다.

공식 근거: [AI 기본법 제31조](https://www.law.go.kr/LSW/lsSideInfoP.do?docCls=jo&joBrNo=00&joNo=0031&lsiSeq=282791&urlMode=lsScJoRltInfoR), [AI 기본법 시행령 제23조](https://www.law.go.kr/lsInfoP.do?lsiSeq=282879&viewCls=lsRvsDocInfoR)

적용 판단:

- 법령 시행 사실: 확인 완료
- Clipper의 AI 기능·생성 결과가 어떤 표시 대상인지: 법무·제품 검토 필요
- 환불 기능과 직접 같은 lifecycle은 아니지만 결제 전 상품 설명·고지와 연결될 수 있음

### 5.6 세무·회계

부가가치세법 시행령 제70조와 국세청의 수정세금계산서 안내에서 계약 해제·공급가액 변동 등에 따른 정정 근거와 발급 시점을 확인할 수 있다.

공식 근거: [부가가치세법 시행령 제70조](https://law.go.kr/LSW/lsLinkCommonInfo.do?lspttninfSeq=112887), [국세청 수정세금계산서 안내](https://j.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7791&mi=2465)

적용 판단:

- 관련 정정 제도 존재: 확인 완료
- 카드취소, 현금영수증, 세금계산서, 부분 환불별 Clipper의 실제 회계처리: 세무·회계 담당 확인 필요
- 연간 선결제의 매출 인식과 미래분 환불 분개: 회계정책 확인 필요

### 5.7 현재 public legal content

[customer legal content](/Users/jina/project/adlight/.worktrees/clipper_web_client-toss-payments-pg-integration/src/app/features/public/legal/legal-content.ts)에는 placeholder와 검토 메모가 남아 있으며 TossPayments가 processor/수탁자 목록 등에 완결되게 반영됐다고 보기 어렵다. 이는 승인된 법률 문구가 아니다. 법무 검토 없이 문구를 확정하거나 배포하면 안 된다.

## 6. 환불 관련 domain boundary

### 6.1 구독 자동결제 취소

- 원인: 고객이 다음 갱신을 원하지 않음
- 변경 상태: subscription이 period end에 종료되도록 예약
- 과거 결제금 반환: 없음
- provider 호출: billing schedule/계약 구조에 따라 필요할 수 있으나 현재 구현은 과거 payment cancel이 아님
- entitlement: 이미 결제한 기간 말까지 유지
- idempotency: 취소 예약 명령에 필요

### 6.2 실제 결제금 전액 환불

- 원인: 적법한 철회, 중복 결제, 회사 귀책, 승인된 미사용 환불 등
- 변경 상태: 해당 payment 전체 취소, refund case와 attempt 완료
- provider 호출: 필요
- entitlement: 해당 결제가 만든 유료 access를 승인된 기준에 따라 종료
- credit: 해당 결제가 발급한 **미사용** subscription/top-up credit은 회수하는 것이 금전·혜택의 이중 보유를 막는 기본 구조
- 사용된 credit이 있으면: 일반적인 “미사용 전액 환불” 요건에는 맞지 않는다. 그렇다고 모든 경우 환불 불가로 단정할 수는 없고, 법정 취소·회사 귀책·미성년자 등의 별도 branch가 필요하다.
- idempotency와 recovery: 필수

결제금을 전액 돌려주고 그 결제로 지급한 미사용 credit을 그대로 남기는 것은 정상 기본 경로로 설계하지 않는다. 보상성 credit을 남기려면 환불과 분리된 별도 승인·사유·ledger entry가 필요하다.

### 6.3 실제 결제금 부분 환불

- 원인: 승인된 미래 미제공 서비스 환급, top-up 일부 미사용분 환급, 과오금 정정 등
- 변경 상태: 한 payment에서 일부 금액 취소, 잔여 취소 가능액 감소
- provider 호출: 필요, `cancelAmount` 지정
- entitlement: 돈이 일부 환불됐다는 이유로 “부분적으로 활성화”되는 것이 아님. access는 활성 또는 종료라는 별도 결정이 필요하다.
- credit: 어떤 grant를 얼마만큼 회수하는지 policy 산식과 attribution 필요
- idempotency, 동시성, 반올림, 누적 취소액 검증: 필수

연간 구독에서 부분 환불을 논할 때 이미 지나가고 제공이 완료된 기간을 일반 환불 대상으로 삼는다는 뜻이 아니다. 검토 대상은 해당 법률·약관·정책이 인정하는 경우의 **미래 미제공 기간**이다. 예를 들어 12개월 선결제 후 4개월 사용했다면 미래 기간은 원칙적으로 8개월이며, “50%”나 “남은 6개월” 같은 임의 숫자는 근거가 없다. 실제 금액은 승인된 산식, 할인 회수 여부, 세금, 제공 기준일을 적용해 시스템이 계산해야 한다.

### 6.4 Entitlement 종료

- 원인: subscription period end, 환불 승인, 관리자 조치, 법적 취소 등
- 변경 상태: 기능 사용 권한
- provider 호출: 자체적으로는 없음
- money refund와 관계: 환불 성공의 내부 효과일 수 있지만 같은 상태가 아님
- 실패 복구: provider 환불 성공 후 entitlement 종료가 실패하면 재시도 가능한 `internal_effects_pending` 상태가 필요

### 6.5 구독 benefit credit 조정

구독 결제 직후 자동 지급된 benefit credit은 payment와 attribution을 가져야 한다. 적법한 전액 환불이 완료되면 그 결제로 발급됐고 아직 사용되지 않은 credit을 회수한다. 이미 사용된 credit이 있으면 일반 미사용 전액 환불 branch가 아니라 별도 정책·법적 사유 평가로 넘어간다.

“전부 사용됐지만 전액 환불을 기본 허용”하거나 “정책이 없으니 관리자가 임의 금액을 입력”하는 방식은 제안하지 않는다.

### 6.6 Top-up 환불과 구독 환불

top-up은 구독과 별도 payment다. 따라서 구독 결제를 환불한다고 top-up 결제까지 자동 환불해서는 안 되며, top-up credit을 자동 삭제해서도 안 된다.

현재 코드대로라면 구독 access가 끝난 뒤에도 top-up grant는 유효기간까지 보유되지만 사용할 수 없다. 이후 paid/admin access가 다시 생기면 남은 유효기간 안에서 다시 사용할 수 있다. 그러나 이 동작은 사업 승인을 다시 받아야 한다.

top-up 자체 환불은 별도 case다.

- 미사용 top-up의 전액 환불 가능 여부
- 일부 사용 top-up의 잔여분 부분 환불 가능 여부와 산식
- top-up credit 회수와 결제금 취소 순서
- 환불 중 새로운 credit 사용 차단
- 만료된 top-up의 환불 가능성
- 회사 귀책·법정 취소 예외

를 별도로 정해야 한다.

### 6.7 실패 작업의 내부 credit 반환·복구

- 원인: 렌더링·AI 처리 등 내부 operation 실패
- 변경 상태: credit ledger와 operation 상태
- provider 호출: 없음
- 결제금 반환: 없음
- idempotency: 같은 operation에 credit을 두 번 돌려주지 않도록 필요

명칭에 `refund`가 있더라도 customer money refund와 API, 상태, 권한, 감사기록을 공유하지 않는다.

### 6.8 보상성 credit

CS가 장애나 불편에 대해 credit을 추가 지급하는 행위는 환불이나 credit restoration이 아니다. 별도의 compensation reason, 승인 권한, 한도와 ledger entry가 필요하다.

## 7. 환불 판단과 승인 구조

### 7.1 누가 무엇을 승인하는가

“정책 승인”과 “개별 요청 승인”은 다르다.

- 전략/제품: 어떤 상품에 어떤 환불 정책과 산식을 제공할지 결정
- 법무: 법정 철회·예외·약관·고지·동의와 상품 적용 판단
- 세무·회계: 취소 증빙, 매출·세금·정산 처리
- 운영·CS: 접수·증빙·예외·SLA·고객 안내와 수동 절차
- 회사의 권한 있는 최종 결정자: 위 검토를 바탕으로 운영 정책 활성화 승인
- 관리자/CS 담당자: 승인된 정책 아래 개별 case를 승인·거절하거나 예외 escalation

따라서 “정책 승인 전까지 전액 환불만 활성화”라는 표현은 부정확하다. 전액 환불 규칙도 승인돼야 한다. 더 정확한 원칙은 **승인된 policy branch만 활성화**하는 것이다.

### 7.2 시스템이 판단할 수 있는 것

사람이 모든 금액을 직접 계산할 필요는 없다. 승인된 규칙이 존재하면 backend가 다음을 계산할 수 있다.

- 대상 payment와 결제수단
- 결제·서비스 제공·credit 사용 시점
- 전액/부분/불가/법무·CS 검토 대상 분류
- 예상 환불액과 산식의 각 항목
- entitlement 종료 시점
- 회수할 credit grant
- 사용 중·중복 요청·이미 취소된 금액
- 제출이 필요한 증빙과 review route

다만 시스템은 승인되지 않은 규칙을 스스로 만들 수 없다. 법적 해석, 회사 귀책 판단, 미성년자 확인, 예외 증빙처럼 정형화하기 어려운 것은 사람의 검토가 필요할 수 있다.

### 7.3 사용자가 요청하는 방식

일반 사용자는 “12,500원을 환불해 달라”고 산식을 제출하는 방식이 아니라 대상 구매와 사유를 선택해 환불을 요청한다. 시스템은 현재 상태와 policy version을 기준으로 예상 결과를 제시한다.

관리자도 정상 case에서는 환불 금액을 자유 입력하지 않는다. 시스템 quote를 검토·승인한다. 불가피한 override만 별도 권한으로 허용하며 최소한 다음을 기록한다.

- 원래 계산 결과
- override 금액
- 표준 규칙과 다른 이유
- 증빙
- 요청자·승인자
- timestamp
- 관련 고객 통지

### 7.4 Quote의 stale 문제

quote를 만든 뒤 credit이 더 사용되거나 시간이 지나 서비스 제공 구간이 바뀔 수 있다. 따라서 승인·provider 호출 직전에 quote를 재검증해야 한다. 필요한 경우 대상 grant를 일시적으로 사용 불가 상태로 예약하거나, 짧은 quote 유효시간과 optimistic locking을 사용해야 한다.

## 8. 환불 설계에서 새로 확인된 누락

새 설계에서 검토해야 할 후보이며, 모두 첫 구현 범위라는 뜻은 아니다.

- full/partial refund를 별도 명령과 상태로 표현
- subscription/payment/entitlement/credit lifecycle 분리
- payment별 누적 취소액과 refundable balance
- refund case와 provider attempt 분리
- 정책 version과 계산 input/output snapshot
- 원 결제와 grant/consumption attribution
- 동시 credit 사용과 환불 승인 경쟁 제어
- 같은 payment에 대한 중복·병렬 환불 방지
- idempotency key 생성·저장·재사용·만료 후 reconciliation
- provider timeout, 409 processing, definitive failure, unknown outcome 구분
- 동기 응답, GET 조회, webhook 간 source reconciliation
- provider 성공 후 내부 효과 실패를 위한 durable retry
- 내부 효과 선적용으로 돈은 못 돌려주고 access만 사라지는 상황 방지
- 외부 dashboard에서 수동 취소한 payment의 탐지와 내부 동기화
- 부분 환불의 통화 최소단위, 반올림, 할인·세금 배분
- 카드·간편결제·가상계좌 등 수단별 차이
- 가상계좌 환불계좌 정보의 보안·개인정보 처리
- 환불 사유 code와 provider용 설명의 구분
- customer-visible reason과 내부 investigation note 분리
- 관리자 역할, 금액 한도, 이중 승인, separation of duties
- append-only audit trail
- 고객 통지, 영수증·취소 증빙, 처리 예상시간
- 재처리와 manual reconciliation runbook
- metrics와 alert: 오래된 processing, unknown, internal effects pending
- 탈퇴·개인정보 삭제 요청과 법정보존 대상 결제·환불 기록의 관계
- chargeback/지급거절은 일반 환불과 별도 lifecycle인지
- 환율·해외결제 도입 시 금액 차이
- 법정 환불과 goodwill compensation의 분리

## 9. 설계 대안

### 대안 A — Durable refund case + versioned policy quote + 승인 + provider attempt

흐름:

1. 고객 또는 관리자가 대상 payment와 사유로 refund case를 생성한다.
2. evaluator가 승인된 policy version으로 eligibility와 quote를 계산한다.
3. 자동 승인 가능한 branch는 다음 단계로 가고, 나머지는 review queue로 보낸다.
4. 승인 시 quote를 재검증한다.
5. durable provider attempt와 idempotency key를 만든다.
6. Toss cancellation을 호출한다.
7. 성공 또는 reconciliation 확인 후 entitlement·credit 내부 효과를 transactionally 기록한다.
8. 내부 효과가 실패하면 provider를 다시 취소하지 않고 내부 효과만 재시도한다.
9. 고객 통지와 회계·감사 event를 남긴다.

장점:

- full과 partial을 같은 subsystem에서 명확히 표현 가능
- provider 성공과 내부 상태 실패를 안전하게 복구 가능
- 정책 변경 이력을 보존하고 왜 그 금액이 나왔는지 설명 가능
- 자동 판단과 사람 승인을 함께 지원
- 외부 수동 취소도 reconciliation을 통해 흡수 가능

단점:

- DB 모델, evaluator, worker/reconciliation, 관리자 UI가 필요
- 구현 난이도와 초기 검증 범위가 가장 큼
- policy owner들의 선결정 없이 evaluator branch를 활성화할 수 없음

운영 영향:

- review queue, exception runbook, 권한과 SLA가 필요
- 대신 수기 계산과 중복 취소 위험이 크게 줄어듦

리스크:

- 과도하게 범용화하면 초기 범위가 커질 수 있음
- 따라서 schema는 full/partial을 표현하되 첫 release에서는 승인된 최소 branch만 구현·활성화해야 함

### 대안 B — Toss dashboard 수동 취소 + 내부 reconciliation

흐름:

1. CS가 별도 절차로 eligibility와 금액을 확인한다.
2. 권한 있는 담당자가 TossPayments dashboard에서 취소한다.
3. Clipper가 Payment 조회/reconciliation으로 취소를 감지한다.
4. 내부 entitlement·credit 효과를 수동 또는 자동 적용한다.

장점:

- provider cancel API 구현 전 제한된 운영 가능
- 초기 개발 범위가 작음
- 소량 요청을 사람이 면밀히 검토 가능

단점:

- 이중 입력과 수기 계산 오류
- dashboard 권한과 내부 권한이 분리돼 감사가 어려움
- provider 성공 후 내부 반영 누락 가능
- 처리 속도와 CS 비용이 큼

운영 영향:

- 상세 runbook, 이중 확인, daily reconciliation이 필요

리스크:

- 규모가 조금만 커져도 누락·중복·권한 오남용 위험이 높음
- 영구 구조로 추천하지 않음

### 대안 C — 고객 self-service 자동 환불

흐름:

1. 고객이 구매를 선택하고 환불을 요청한다.
2. 시스템이 즉시 eligibility와 금액을 계산한다.
3. 조건을 만족하면 사람 승인 없이 provider cancel과 내부 효과를 처리한다.

장점:

- 고객 경험과 처리 속도가 가장 좋음
- CS 부담이 낮음

단점:

- 정책과 법적 예외가 충분히 정형화돼야 함
- credit 사용·동시성·fraud·계정 탈취 방어 요구가 큼
- 잘못된 취소는 되돌리기 어려움

운영 영향:

- 자동화율은 높지만 강한 monitoring과 exception handling이 필요

리스크:

- 현재처럼 정책과 법률 적용이 미확정인 단계에는 부적합
- 장기 목표 또는 제한된 “명백한 중복·미사용 결제” branch에만 고려 가능

## 10. 추천안

대안 A를 추천한다. 다만 모든 환불 정책을 지금 확정하거나 모든 branch를 첫 release에 활성화하자는 뜻은 아니다.

핵심은 다음 두 층을 분리하는 것이다.

- **표현 가능한 기술 구조**: full/partial, provider unknown, 내부 효과 pending, entitlement 종료, credit 회수 등을 처음부터 명시적으로 표현
- **활성화된 운영 정책**: 전략·법무·세무회계·운영CS 검토를 마친 branch만 evaluator에서 사용

처음부터 부분 환불을 표현할 수 있게 하는 이유는 Toss 자체가 부분 취소를 지원하고, 연간 미래 미제공분·top-up 일부 미사용분·과오금 등에서 필요해질 가능성이 높기 때문이다. 이후 schema와 audit model을 다시 뜯는 비용을 줄일 수 있다.

그러나 “부분 환불 기능을 표현한다”와 “부분 환불 정책을 지금 운영한다”는 다르다. 산식과 eligibility가 승인되지 않았다면 해당 branch는 비활성 상태여야 한다. 전액 환불도 마찬가지다. 승인되지 않은 전액 환불을 임시 기본값으로 사용하지 않는다.

추천 상태 모델 예시:

Refund case:

- `received`
- `evaluating`
- `quoted`
- `review_required`
- `ineligible`
- `approved`
- `rejected`

Provider attempt:

- `created`
- `processing`
- `provider_unknown`
- `provider_succeeded`
- `internal_effects_pending`
- `completed`
- `definitive_failed`

Quote가 포함해야 할 최소 정보:

- target payment
- full/partial type
- 계산된 환불 금액과 통화
- 적용 policy ID/version
- reason category
- calculation breakdown
- entitlement 종료 시점
- 회수·유지·보상할 credit grant 목록
- 계산 당시 subscription/payment/grant/consumption snapshot
- quote expiry와 revalidation 결과

상태 이름과 실제 schema는 구현 설계 단계에서 repository convention에 맞춰 다시 확정한다.

## 11. 타 서비스 공식 정책에서 얻은 참고점

타 서비스 정책은 Clipper의 정답이나 법적 근거가 아니라 가능한 운영 패턴의 참고다.

- Runway: 미사용 또는 거의 미사용 조건을 시스템이 판단하며, 환불되면 plan과 미사용 plan credit을 잃는 구조를 안내한다.
- Midjourney: lifetime GPU usage 20분 미만과 같은 수치 조건을 사용한다.
- Vrew: 14일과 premium 기능 미사용을 전액 환불 조건으로 두고, 그 외에는 별도 부분 환불 산식을 제시한다.
- ChatGPT 한국 정책 안내: 7일 이내 미사용 전액 환불과 그 외 prorated 처리, 자동 eligibility 확인 예시가 있다.

공식 참고:

- [Runway 환불 안내](https://help.runwayml.com/hc/en-us/articles/24343363554067-Requesting-a-refund-for-your-plan-or-payment)
- [Midjourney 환불 안내](https://docs.midjourney.com/hc/en-us/articles/25386088618253-Requesting-a-Refund)
- [Vrew 환불 정책](https://vrew.ai/ko/refund-policy/)
- [ChatGPT 환불 안내](https://help.openai.com/en/articles/7232895)

공통적으로 확인되는 설계상 시사점은 다음과 같다.

- 고객이 임의 금액을 계산하기보다 시스템이 eligibility를 판단한다.
- 사용량 또는 premium 기능 사용 여부가 전액 환불 조건에 영향을 준다.
- 환불 시 구독 혜택을 유지하지 않는다.
- 부분 환불을 제공한다면 공개된 산식과 시스템 계산이 필요하다.

Clipper는 상품 구조, 한국 법 적용, credit attribution이 다르므로 그대로 복사해서는 안 된다.

## 12. 담당 조직에 전달할 결정·확인 목록

### 12.1 전략·제품

- 월 구독의 일반 환불 가능 조건은 무엇인가?
- 연간 구독 중도 해지를 제공할 것인가? 제공한다면 미래 미제공분 산식은 무엇인가?
- “미사용”은 credit 미사용, premium 기능 미사용, 서비스 제공 미개시 중 무엇으로 판단하는가?
- top-up은 구매할 때와 사용할 때 각각 paid plan이 필요한가?
- 구독 종료 후 top-up을 보유·사용할 수 있는가?
- 이용권 없이 top-up 사용을 허용한다면 어떤 plan tier/plugin 권한을 부여하는가?
- top-up 유효기간 365일을 유지하는가?
- Trial, subscription benefit, top-up credit의 소비 우선순위와 환불 시 회수 순서는 무엇인가?
- 회사 귀책·중복 결제·오결제에 어떤 별도 정책을 둘 것인가?
- self-service, 자동 승인, 관리자 승인의 범위는 어디까지인가?
- strategy 문서의 “유료 플랜 대상 무제한 이용 가능”에서 “무제한”은 무엇을 뜻하는가?

### 12.2 법무·약관·개인정보

- 각 상품을 디지털콘텐츠·용역·계속거래 중 어떻게 평가하는가?
- 청약철회 기간과 기산점, 제공 개시, 가분적 제공의 Clipper 적용은 어떻게 되는가?
- credit 일부 사용, plugin 실행, 결과물 생성 중 어떤 행위가 제공 개시·사용으로 평가되는가?
- 법정 철회 제한을 위해 필요한 결제 전 고지·명시적 동의·sample 제공 요건은 무엇인가?
- 회사 귀책·계약 불일치·서비스 장애와 미성년자 취소는 일반 정책과 어떻게 분리해야 하는가?
- 연간 중도 해지와 위약금·할인 회수 산식에 법적 제한이 있는가?
- 자동 eligibility/거절이 자동화된 결정 규정의 적용 대상인가?
- TossPayments의 위탁, 재위탁, 국외이전, 보유기간을 어떻게 고지해야 하는가?
- AI 기본법상 Clipper의 표시 대상과 표시 방식은 무엇인가?
- 약관·환불정책·개인정보처리방침의 최종 승인 문구는 무엇인가?

### 12.3 세무·회계

- 카드·가상계좌·현금영수증·세금계산서의 전액·부분 취소 처리 절차는 무엇인가?
- 연간 선결제 매출은 어떻게 인식하며 미래분 환불 시 어떤 분개가 필요한가?
- 할인된 연간 결제의 부분 환불에서 월 정상가 재계산을 허용·채택하는가?
- 부분 취소의 공급가액·부가세·반올림 배분 기준은 무엇인가?
- 결제월과 환불월이 다를 때 정산·증빙·신고 처리는 어떻게 하는가?
- Toss 수수료와 환불 수수료가 있다면 누가 부담하고 어떻게 회계처리하는가?

### 12.4 운영·CS

- 환불 접수 채널과 필수 정보·증빙은 무엇인가?
- 어떤 case를 자동 승인하고 어떤 case를 사람이 검토하는가?
- 담당자별 승인 금액 한도와 이중 승인 조건은 무엇인가?
- 고객에게 예상 환불액·근거·처리기간을 어떻게 안내하는가?
- provider timeout/unknown, provider 성공 후 내부 실패, 외부 dashboard 취소를 어떻게 처리하는가?
- 수기 override를 허용한다면 escalation과 감사 절차는 무엇인가?
- 거절·부분 승인·처리 지연에 대한 고객 안내 template과 SLA는 무엇인가?
- 계정 탈취 또는 fraud가 의심될 때 환불을 어떻게 보류·확인하는가?

이 질문들은 사용자가 임의로 답해야 할 개발 세부 질문이 아니다. 정책 소유 조직과 전문가의 답을 수집하기 위한 handoff 목록이다.

## 13. 구현 전 acceptance gate

다음이 충족되기 전 refund 구현을 시작하지 않는다.

1. 전략·제품이 최초 활성화할 상품별 policy branch와 산식을 문서로 결정
2. 법무가 청약철회·디지털콘텐츠·계속거래·미성년자·약관·고지를 검토
3. 세무·회계가 전액·부분 취소와 증빙·매출 처리 방식을 확인
4. 운영·CS가 접수·승인·예외·권한·SLA를 확정
5. 운영 MID의 Toss API version과 결제수단별 취소 조건을 확인
6. top-up의 구매·사용·구독 종료 후 entitlement 정책을 확정
7. Trial `eligible_from` 처리 결정을 별도로 승인
8. refund case/attempt, quote, attribution, reconciliation 경계에 대해 사용자가 명시적으로 설계를 승인
9. 병렬 worktree와 migration/schema 충돌을 다시 점검

승인 후에도 바로 provider 실호출부터 시작하지 않는다. 별도 구현 계획과 테스트 전략을 작성하고 test key 환경에서 provider contract, idempotency, timeout/reconciliation, 내부 효과 retry를 검증한 뒤 live 단계는 별도 승인한다.

## 14. 기존 TODO 유지

다음 작업은 삭제하거나 환불 첫 구현 범위와 섞지 않는다.

- `BILLING_DELETED` exact candidate/extant-previous integration test
- user-MID webhook
- 가상계좌 발급
- 가상계좌 입금
- 가상계좌 만료 검증

가상계좌의 비동기 환불 특성은 상태 모델이 수용해야 하지만, 위 TODO 자체를 환불 설계의 첫 작업으로 이동하지 않는다.

## 15. 최종 분류표

| 항목 | 분류 | 근거 유형 | 다음 조치 |
|---|---|---|---|
| 현재 가격 catalog | 현재도 유효 | 현재 코드·승인 설계 | 변경 요청 전 유지 |
| Trial 400/no expiry/fallback | 현재도 유효 | 현재 코드·승인 설계 | 운영 적용 검증 |
| Trial `eligible_from` 정확한 시각 | 확인되지 않음 | 코드에만 존재, 명시 승인 없음 | 별도 승인 |
| 자동 fulfillment | 현재도 유효 | 현재 코드 | 환불 내부 효과와 연결 설계 |
| 정기결제 미판매 | 충돌/폐기 | 과거 문서만 존재 | 사용 금지 |
| 수동 이용권 발급 | 충돌/폐기 | 과거 문서만 존재 | 사용 금지 |
| 잠정 무조건 전액 환불 | 충돌/폐기 | 잠정 문서, 현재 구현 없음 | 상품·법률별 재결정 |
| period-end subscription cancellation | 현재도 유효 | 현재 코드 | money refund와 분리 유지 |
| money refund subsystem | 아직 존재하지 않음 | 현재 코드/OpenAPI | 승인 후 설계·구현 |
| `operation_refund` | 현재도 유효 | 현재 코드 | credit restoration으로 명확화 |
| 부분 취소 API와 idempotency 제약 | 새롭게 확인 | Toss 공식 문서 | provider 설계에 반영 |
| domestic cancel webhook 비의존 | 새롭게 확인 | Toss 공식 문서 | sync response+GET reconciliation |
| top-up paid-plan 구매·사용 자격 | 사업 결정 필요 | 현재 코드와 strategy 문구 불충분 | 전략팀 확인 |
| 이용권 없는 top-up의 기능 권한 | 사업 결정 필요 | entitlement 공백 | 전략팀 결정 후 기술 설계 |
| 청약철회·디지털콘텐츠 예외 | 법무 확인 필요 | 현행 공식 법령 | Clipper 적용 의견 |
| 계속거래 해당 여부 | 법무 확인 필요 | 현행 공식 법령 | 계약 구조 검토 |
| 미성년자 취소 | 법무·운영 확인 필요 | 민법 | 확인·처리 절차 설계 |
| 환불 회계·세무 처리 | 세무·회계 확인 필요 | 부가세 법령·국세청 안내 | 내부 회계정책 확정 |
| 고객 접수·승인·예외 | 운영·CS 확인 필요 | 아직 운영정책 없음 | runbook/SLA/권한 확정 |
| Toss 위탁·국외이전 표기 | 법무·개인정보 확인 필요 | PIPA, 실제 계약 미확인 | 계약·data flow 검토 |
| AI 표시 | 법무·제품 확인 필요 | 현행 AI 기본법 | 서비스 적용 판단 |

## 16. 현재 중지점

이 문서의 작성으로 조사·현황 검증·설계 대안 정리는 완료했지만 환불 정책이나 구현 설계가 승인된 것은 아니다. 다음 단계는 담당 조직의 답변을 반영해 policy matrix와 최초 활성화 범위를 구체화하고, 사용자가 수정된 설계를 명시적으로 승인하는 것이다.

그 승인 전까지 다음을 수행하지 않는다.

- DB 변경 또는 migration 생성·실행·history 수정
- refund 코드 구현
- provider cancellation 구현 또는 실제 호출
- live payment/refund
- merge, push, PR 생성·수정, deploy
