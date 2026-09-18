# 현재 크레딧 혜택 진행 막대 설계

날짜: 2026-09-18 KST

상태: **Web API·Desktop Angular 구현 완료. Desktop NestJS 전달 누락 보완 및 로컬 회귀 검증 완료. 보완분 미커밋·미배포.**

## 1. 목적

계정의 실제 사용 가능 크레딧과, 현재 무료 체험 또는 현재 이용기간에 지급된 크레딧의 소진 정도를 서로 다른 개념으로 정확히 표시한다.

다음 잘못된 표시는 다시 만들지 않는다.

- 남은 잔액을 분자와 분모에 중복 사용한 `300 / 300`
- operation 과금에 존재하지 않는 계정 전체 `보류 0`
- 추가 구매 크레딧을 월 기본 제공량의 분모에 섞어 진행률이 갑자기 커지는 표시

## 2. 확정 표시 원칙

### 계정 전체 잔액

항상 모든 현재 사용 가능 source를 합친 정본 잔액을 표시한다.

```text
사용 가능 700
```

이 값은 기존 `spendableBalance`다. 정기구독, 관리자 지급 플랜, 추가 구매, 프로모션, 관리자 조정, 사용 가능한 무료 체험 잔액이 현재 접근 정책에 따라 합산될 수 있다.

### 진행 막대

진행 막대는 계정 전체 자산이 아니라 **현재 적용 중인 하나의 혜택 단위**만 표시한다.

- 무료 체험 중: 무료 체험 지급 건의 남은 양 / 최초 지급량
- 유료 구독 중: 현재 월 이용기간에 발급된 정기구독 지급 건들의 남은 양 / 최초 지급량 합계
- 관리자 부여 이용권 사용 중: 현재 월 이용기간에 발급된 `admin_plan` 지급 건들의 남은 양 / 최초 지급량 합계
- 추가 구매만 보유한 상태: 진행 막대 없음

예시:

```text
사용 가능 700
무료 체험 남음 300 / 400
출처  무료 체험 300 · 추가 구매 400
```

```text
사용 가능 1,300
이번 이용기간 남음 300 / 400
출처  정기구독 300 · 추가 구매 1,000
```

진행 막대의 채움 비율은 `remainingCredits / initialCredits`다. `initialCredits - remainingCredits`를 화면에서 일반적인 `사용`이라고 부르지 않는다. 관리자 회수나 결제 조정도 차이를 만들 수 있기 때문이다.

### 크레딧 source별 포함 범위

`관리자 부여 이용권`과 `관리자 직접 지급 크레딧`은 서로 다른 개념이다.

| 사용자 관점 | 내부 source | `사용 가능` 총액 | 현재 혜택 진행 막대 | 의미 |
| --- | --- | --- | --- | --- |
| 무료 체험 크레딧 | `free_trial` | 포함 | 활성 유료·관리자 이용권이 없을 때 포함 | 최초 무료 체험 지급분 |
| 정기결제 이용권 크레딧 | `subscription` | 포함 | 포함 | 결제한 이용권의 현재 benefit period 기본 지급분 |
| 관리자 부여 이용권 크레딧 | `admin_plan` | 포함 | 포함 | 관리자가 이용권을 부여했고 그 이용권 정책에 따라 지급된 현재 period 크레딧 |
| 추가 구매 크레딧 | `topup` | 포함 | 제외 | 사용자가 별도로 구매한 크레딧 |
| 관리자 직접 지급 크레딧 | `admin_adjustment` | 포함 | 제외 | 관리자가 이용권과 무관하게 수동으로 추가한 크레딧 |
| 프로모션 크레딧 | `promotion` | 포함 | 제외 | 이벤트·프로모션 지급분 |

여기서 `admin_plan`은 단순히 관리자가 크레딧을 넣어 준 경우가 아니다. 관리자가 사용자에게 플랜 이용권을 부여하면 access grant가 생성되고, 그 이용권의 월 기본 제공량이 `admin_plan` source로 지급된다. 반대로 관리자 화면에서 크레딧만 직접 지급하면 `admin_adjustment`이며, 이용권이나 월 기본 제공량을 만들지 않는다.

혼합 사례:

```text
관리자 부여 이용권: 현재 period 400 중 100 차감 -> 300
추가 구매: 1,000
관리자 직접 지급: 200
프로모션: 100

사용 가능 1,600
이번 이용기간 남음 300 / 400
```

따라서 진행 막대는 계정의 모든 크레딧 자산 비율이 아니라, 현재 무료 체험 또는 현재 이용권 기본 혜택의 남은 비율이다.

무료 체험 400 중 100을 차감한 상태에서 관리자가 크레딧 200을 직접 지급했다면 다음처럼 표시한다.

```text
사용 가능 500
무료 체험 남음 300 / 400
출처  무료 체험 300 · 관리자 지급 200
```

무료 체험 잔액이 남아 있는 동안 정기결제 또는 관리자 부여 이용권이 활성화되면, 무료 체험 잔액은 `사용 가능` 총액과 출처 목록에 계속 포함하지만 진행 막대는 현재 이용권 benefit period를 우선 표시한다.

## 3. 월 리셋 기준

월 기본 제공 크레딧의 분모는 달력의 매월 1일이 아니라 서버에 저장된 현재 `benefitPeriodStart`와 `benefitPeriodEnd`를 기준으로 한다.

- 월간 구독: 결제 기준 월 주기
- 연간 구독: 결제 시 연간 전량을 지급하지 않고, 매 월 기념일마다 월 기본 제공량 지급
- 다음 benefit period가 시작되면 이전 period 대신 새 period의 지급량과 잔액으로 진행 막대를 교체
- 추가 구매 크레딧은 별도 만료 정책을 따르며 월 진행 막대의 분모에 포함하지 않음

따라서 월 기본 제공량 400 중 100을 썼다면 `300 / 400`이고, 추가 구매 1,000을 더 해도 진행 막대는 계속 `300 / 400`이다. 계정 전체 사용 가능 잔액만 `1,300`으로 바뀐다.

## 4. 서버 계약

`GET /credits/summary` 응답에 하위 호환 가능한 nullable 필드 `currentBenefit`을 추가한다.

```ts
interface CurrentCreditBenefit {
  kind: 'free_trial' | 'plan_period';
  source: 'free_trial' | 'subscription' | 'admin_plan';
  initialCredits: number;
  remainingCredits: number;
  periodStart: string;
  periodEnd: string | null;
}

interface CreditSummary {
  heldBalance: number; // legacy/deprecated, 기존 소비처 호환용으로 당장은 유지
  spendableBalance: number;
  bySource: CreditSourceBalance[];
  currentBenefit: CurrentCreditBenefit | null;
}
```

`periodStart`와 `periodEnd`는 ISO 8601 UTC 문자열이다. 무료 체험도 현재 grant의 `grantedAt`과 `expiresAt`을 사용한다.

`heldBalance`는 이번 작업에서 제거하지 않는다. 의미 없는 신규 사용을 막고, 기존 소비처 확인 후 별도 호환성 작업으로 deprecated/제거한다.

## 5. 서버 산출 규칙

### 플랜 혜택

1. 현재 유효한 `user_access_grants`를 찾는다.
2. 현재 시각을 포함하는 `benefitPeriodStart <= now < benefitPeriodEnd` 지급 건을 찾는다.
3. source가 현재 access의 `subscription` 또는 `admin_plan`과 같고, 상태가 `active` 또는 `depleted`인 지급 건만 포함한다.
4. 같은 source와 같은 benefit period의 지급 건들을 합산한다.
   - 최초 지급과 같은 달의 업그레이드 차액 지급을 하나의 진행 막대로 표현하기 위함이다.
   - 관리자 부여 이용권의 같은 달 등급 변경 전·후 지급 건도 같은 period라면 함께 합산한다.
5. `initialCredits`와 `remainingCredits`를 각각 합산한다.

`revoked`, `expired`, `refund_locked` 지급 건은 진행 막대에서 제외한다. 특히 `refund_locked`는 환불 처리 중인 개별 지급 건 상태이지 계정 전체의 보류 잔액이 아니다.

### 무료 체험

정기결제 또는 관리자 부여 이용권 혜택이 없을 때, 현재 시각 범위에 있는 `free_trial` 지급 건 하나를 사용한다. 상태는 `active` 또는 `depleted`를 허용한다. 따라서 무료 체험 크레딧을 모두 사용한 뒤에도 만료 전이라면 `0 / 400`을 표시할 수 있다.

### 선택 우선순위

```text
현재 정기결제/관리자 부여 이용권 혜택 > 현재 무료 체험 > 진행 막대 없음
```

무료 체험 잔액이 남아 있더라도 정기결제 또는 관리자 부여 이용권이 현재 적용 중이면 진행 막대는 이용권의 현재 월 혜택을 보여준다. 무료 체험 잔액은 `사용 가능` 총액과 출처별 목록에서 계속 확인한다.

## 6. DB와 조회 구현

새 DB migration은 필요하지 않다. 현재 `credit_grants`에 이미 다음 값이 있다.

- `initial_credits`
- `remaining_credits`
- `granted_at`, `expires_at`
- `benefit_period_start`, `benefit_period_end`
- `source`, `status`, `access_grant_id`

`CreditsRepository`에 현재 혜택용 조회를 추가한다. 플랜 조회는 현재 period의 `active`/`depleted` 지급 건을 반환하고, 무료 체험 조회는 현재 유효기간의 최신 지급 건을 반환한다. 서비스가 합산과 우선순위를 담당한다.

## 7. Desktop UI

데스크톱 설치형 앱의 실제 응답 경로는 `Web API → Desktop NestJS → Desktop Angular`다. Angular가 Web API를 직접 호출하는 구조가 아니다. Desktop NestJS의 `CreditsService`가 `/credits/summary` 응답을 허용 목록 방식으로 다시 투영하므로, Web API에 필드를 추가할 때 이 계층의 응답 타입·검증·전달도 함께 갱신해야 한다.

이번 최초 구현에서는 이 중간 계층이 계획과 검증 범위에서 빠져 `currentBenefit`을 제거했다. Web API 단위 테스트와 Angular mock 테스트는 각각 통과했지만 실제 설치형 앱에서는 막대가 보이지 않았다. 보완 후 Desktop NestJS는 유효한 `currentBenefit`만 전달하고, 필드가 없거나 `null`인 구버전 Web API 응답은 `null`로 정규화한다.

1단계에서 단일화한 `사용 가능 N` 표시는 그대로 유지한다.

`currentBenefit !== null`일 때만 그 아래에 진행 막대를 다시 표시한다.

- `free_trial`: `무료 체험 남음 300 / 400`
- `subscription`, `admin_plan`: `이번 이용기간 남음 300 / 400`
- `aria-valuemin=0`
- `aria-valuenow=remainingCredits`
- `aria-valuemax=initialCredits`
- 초기값이 0이거나 서버 값이 비정상인 경우 막대를 숨기고 `사용 가능 N`만 표시
- 설정 화면과 홈 사이드 패널은 같은 `AccountSummaryStore` 파생값을 사용

`보류` 범례는 복구하지 않는다. source 목록과 크레딧 변동 내역도 그대로 유지한다.

## 8. 하위 호환과 배포 순서

1. Web API에 nullable `currentBenefit`을 추가하고 OpenAPI/단위/통합 테스트를 갱신한다.
2. API를 먼저 배포한다.
3. Desktop NestJS가 필드 부재를 `null`로 정규화하고, 필드가 있으면 닫힌 계약으로 검증·전달한다.
4. Desktop Angular가 nullable 계약을 소비한다.
5. 새 Desktop을 배포한다.
6. 기존 Desktop은 추가 필드를 기존 투영 과정에서 무시하므로 영향을 받지 않는다.

여기서 `이전 API`는 전체 PG 적용 전 서버라는 뜻으로 한정되지 않는다. `currentBenefit` 필드를 추가하기 전의 모든 Web API 빌드를 뜻한다. 새 Desktop이 그런 서버에 연결돼도 Desktop NestJS가 누락 필드를 `null`로 바꾸므로 진행 막대만 숨고 `사용 가능 N`은 정상 표시된다. 이 호환 처리는 구버전 앱의 로그인이나 기능을 차단하지 않는다.

## 9. 필수 테스트

### Web API

- 무료 체험 400 지급 후 100 차감: `currentBenefit=300/400`
- 무료 체험 전액 소진: 만료 전 `0/400`
- 구독 월 지급 400 후 100 차감: 현재 period `300/400`
- 현재 period 구독 업그레이드 차액 지급: 같은 period 지급 건 합산
- 관리자 부여 이용권 등급 상향 차액 지급: 같은 period 지급 건 합산
- 추가 구매 1,000 추가: `spendableBalance`만 증가하고 `currentBenefit`은 불변
- 다음 월 지급: 새 period 값으로 전환
- 만료·회수·환불 잠금 지급 건 제외
- 유료 플랜과 무료 체험 잔액 공존: 플랜 혜택 우선
- 혜택 없이 추가 구매만 존재: `currentBenefit=null`
- OpenAPI schema와 실제 응답 일치

### Desktop Angular

- `currentBenefit`이 없거나 null이면 진행 막대 없음
- 무료 체험과 플랜의 문구 구분
- 전체 사용 가능 잔액과 진행 막대 분모가 독립적임
- 추가 구매가 있어도 진행 막대 분모가 변하지 않음
- `보류` 문구가 다시 나타나지 않음
- 설정 화면과 홈 사이드 패널 동일 동작

### Desktop NestJS 계약 브리지

- Web API의 유효한 `currentBenefit`을 필드별로 검증해 그대로 전달
- 알 수 없는 상위·하위 필드는 기존 보안 경계대로 제거
- 구버전 Web API처럼 `currentBenefit`이 없거나 `null`이면 `null`로 정규화
- `free_trial`은 source `free_trial`만 허용
- `plan_period`는 source `subscription` 또는 `admin_plan`만 허용하고 `periodEnd` 필수
- 잘못된 응답은 `BadGatewayException`으로 변환

## 10. 이번 후속 작업에서 하지 않는 것

- 기존 grant/ledger 데이터 재작성
- 추가 구매를 월 기본 제공량에 합산
- 달력 월 기준으로 강제 리셋
- `heldBalance` 즉시 삭제
- 환불 처리 중 지급 건을 계정 전체 `보류`로 재도입

## 11. 구현 및 검증 결과

2026-09-18에 다음 범위로 구현했다.

- Web API `GET /credits/summary`에 `currentBenefit`을 추가했다.
- 플랜 혜택은 현재 유효한 access의 source와 현재 benefit period가 일치하는 `active`/`depleted` 지급 건만 합산한다.
- 무료 체험은 정기결제·관리자 부여 이용권 혜택이 없을 때 현재 유효한 최신 지급 건을 사용한다.
- Desktop NestJS는 Web API 응답의 `currentBenefit`을 검증해 Angular로 전달한다. 필드가 없거나 `null`인 구버전 응답은 `null`로 정규화하며, 잘못된 값은 유효한 데이터처럼 전달하지 않는다.
- Desktop Angular는 `spendableBalance`를 `사용 가능 N`의 정본으로 유지하고, 검증된 `currentBenefit`이 있을 때만 설정 화면과 홈 사이드 패널에 진행 막대를 표시한다.
- DB migration과 기존 grant/ledger 데이터 변경은 없다.

검증 결과:

- Web API 전체 Jest: 271 suites, 2,906 tests 통과(5 suites/21 tests는 기존 skip)
- Web API 프로덕션 빌드: 통과
- Desktop Angular 전체 Karma: 4,683 tests 통과
- Desktop SCSS breakpoint 검증: 6 tests 통과
- Desktop Angular 프로덕션 빌드: 통과
  - 현재 macOS/Node 환경에서 Angular의 기본 LMDB 캐시 모듈이 네이티브 충돌하여 `NG_BUILD_CACHE_STORE=sqlite`로 캐시 backend만 바꿔 검증했다.
  - 이 우회는 소스·설정·산출물 계약을 변경하지 않는다.
- 세 작업 공간 `git diff --check`: 통과

최초 완료 판정 뒤 실제 설치형 응답 경로에서 Desktop NestJS 투영 누락을 발견했다. 2026-09-18 보완 작업에서는 별도 `fix/desktop-credit-summary-proxy-20260918` 작업공간에서 실패 재현 테스트를 먼저 추가하고, 유효 값 전달·구버전 필드 부재/null 호환·잘못된 variant 거부를 구현했다.

보완 검증 결과:

- Desktop NestJS 프로덕션 TypeScript 빌드: 통과
- 크레딧 프록시 계약 테스트: 8/8 통과
- 기존 경로 의존 프로세스 테스트 파일 1개를 제외한 전체 회귀: 2,711/2,711 통과
- `owned-child-process-registry.test.js`: 긴 격리 worktree 경로에서는 5/6, 변경 전 원본 checkout에서는 6/6 통과. 실패 항목은 child process identity 비교이며 크레딧 코드와 무관하다.
- Desktop NestJS `git diff --check`: 통과

기존 Web API·Desktop Angular 구현은 각 기능 브랜치와 문서에 커밋·푸시돼 있다. 이번 Desktop NestJS 보완 코드와 문서 보완만 아직 커밋·푸시·dev 반영·앱 재빌드를 하지 않았다.
