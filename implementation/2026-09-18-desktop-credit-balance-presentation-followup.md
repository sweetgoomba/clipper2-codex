# 데스크톱 크레딧 잔액 표시 후속

날짜: 2026-09-18 KST

상태: **1단계 표시 정리와 현재 혜택 진행 막대 구현·로컬 회귀 테스트 완료. 미배포.**

## 1. 사용자 확인 현상

신규 무료 체험에서 400크레딧을 지급받은 뒤 URL 숏폼과 붙여넣기 숏폼에 각각 50크레딧을 사용했다.

- ledger: `+400`, `-50`, `-50`
- 실제 사용 가능 잔액: `300`
- 데스크톱 표시: `300 / 300`, `보류 0`, `사용 가능 300`

`300 / 300`은 최초 지급량 400과 사용량 100을 표현하지 못한다. `보류 0`도 현재 operation 과금 모델에 존재하지 않는 일반적인 예약 잔액처럼 읽히므로 잘못된 UX다.

## 2. 직접 원인

Web API의 현재 credit summary 계약은 `heldBalance`, `spendableBalance`, `bySource`다. `CreditGrantsService.summaryWithManager()`는 현재 유효한 grant의 남은 크레딧을 합산한 뒤 다음처럼 같은 값을 두 필드에 반환한다.

```text
heldBalance = 300
spendableBalance = 300
```

Desktop Angular의 `AccountSummaryStore`는 이를 다음처럼 다시 계산한다.

```text
creditBalance = spendableBalance
creditTotal = max(spendableBalance, heldBalance)
creditHeld = creditTotal - creditBalance
```

따라서 `creditTotal=300`, `creditHeld=0`이 되고 화면은 `300 / 300`, `보류 0`이 된다. 서버의 `heldBalance`는 최초 지급량 400이나 누적 사용량 100이 아니다.

## 3. 발생 경위

- 과거 license adapter에는 `creditAllowance`, `creditBalance`, `creditsUsed`가 있어 최초 할당량과 현재 잔액을 분리할 수 있었다.
- 당시에도 `creditsUsed`를 화면에서 `보류`라고 부른 잘못된 표현이 이미 있었다.
- PG 통합 후 legacy license adapter를 제거한 Angular commit `ac879329`에서 새 credit summary를 기존 미터 UI에 연결했다.
- 새 summary에는 최초 지급량/누적 사용량이 없는데도 `heldBalance`를 전체량처럼 사용하면서 `300 / 300` 회귀가 생겼다.
- Web API의 현재 구현은 `heldBalance`와 `spendableBalance`를 동일하게 반환하므로 두 값의 차이를 `보류`로 표시하는 UI는 현재 정책에서 의미가 없다.

## 4. 보류 개념 판정

일반 유료 operation에는 별도의 크레딧 예약·보류 단계가 없다.

```text
작업 시작 시 차감 -> 성공 시 확정 -> 실행 실패·취소 시 환급
```

따라서 계정 전체 미터에 표시할 일반적인 `보류 크레딧`은 필요하지 않다.

`refund_locked`는 별개다. 결제 환불 처리 중인 특정 credit grant를 잠그는 상태이며, 해당 지급 건에 `환불 처리 중`으로 표시해야 한다. 이를 계정 전체의 `보류` 잔액이나 operation 진행 중 예약액으로 재해석하면 안 된다.

## 5. 권장 후속 수정

### 1단계 — Desktop 표시 정리

- `보류` 범례와 `creditHeld`, `creditUsedProgress`, 관련 aria 문구를 제거한다.
- summary만 있는 화면에서는 정본인 `사용 가능 300`을 우선 표시한다.
- `300 / 300`처럼 남은 잔액을 분모와 분자에 중복 표시하지 않는다.
- 설정 화면과 홈 사이드 패널을 같은 `AccountSummaryStore` 규칙으로 함께 수정한다.
- `보류`와 `available / available` 표기가 다시 나타나지 않는 회귀 테스트를 추가한다.

### 2단계 — API 계약 정리

- 실제 의미가 분명한 `availableBalance` 또는 기존 `spendableBalance` 하나를 정본으로 삼는다.
- `heldBalance`는 기존 소비처를 조사한 뒤 deprecated 처리하고 단계적으로 제거한다.
- `refund_locked`는 grant 상태로 유지하고 계정 전체 잔액 필드와 섞지 않는다.

### 후속 구현 — 현재 혜택의 300 / 400 복원

이 표기는 `heldBalance`에서 추론하지 않고 서버가 명시적으로 제공하는 `currentBenefit`으로 구현했다.

- 현재 무료 체험 또는 현재 플랜 benefit period의 `initialCredits` 합계
- 같은 지급 범위의 `remainingCredits` 합계
- 추가 구매·프로모션·관리자 조정은 분모에서 제외

따라서 무료 체험 400 중 100을 사용했다면 `무료 체험 남음 300 / 400`을 표시한다. 추가 구매 1,000이 있어도 막대는 `300 / 400`을 유지하고 전체 잔액만 `사용 가능 1,300`이 된다.

## 6. 영향 파일과 검증 기준

예상 영향 파일:

- Desktop Angular `src/shell/account/account-summary.store.ts`
- Desktop Angular 설정 화면과 홈 사이드 패널 template/spec
- Web API `src/modules/credits/application/credit-grants.service.ts` 및 OpenAPI 계약(2단계 진행 시)

완료 기준:

1. 현재 사례에서 `사용 가능 300`은 정확히 보인다.
2. `300 / 300`, `보류 0`은 보이지 않는다.
3. 환불 처리 중인 grant만 해당 이력/지급 건에 `환불 처리 중`으로 표시된다.
4. 여러 credit source와 만료·환불이 섞여도 최초 지급량/사용량을 `heldBalance`에서 추론하지 않는다.

## 7. 1단계 구현 결과

2026-09-18에 사용자 승인 후 Desktop Angular에 다음 최소 수정을 적용했다.

- `AccountSummaryStore` 표시 규칙을 `spendableBalance` 기준의 `사용 가능 N`으로 단일화했다.
- 설정 화면과 홈 사이드 패널에서 `available / total` 미터, `보류` 범례, 관련 aria 표시를 제거했다.
- 출처별 잔액과 크레딧 변동 내역은 그대로 유지했다.
- API의 `heldBalance` 필드, Web API, DB schema/data, 과금·환불 상태는 변경하지 않았다.
- 실패하는 UI 회귀 테스트를 먼저 확인한 뒤 구현했고, `AccountSummaryStore`·설정·홈 사이드 패널 관련 테스트를 포함한 회귀 검증이 통과했다.
- 최종적으로 Desktop Angular 전체 테스트 4,683개와 프로덕션 빌드가 통과했다.

## 8. 남은 경계

- API 계약에서 `heldBalance`를 deprecated/제거할지는 기존 소비처 조사 후 별도로 결정한다.
- `initialCredits - remainingCredits`를 일반적인 `사용`이라고 부르지는 않는다. 관리자 회수나 결제 조정도 차이를 만들 수 있으므로 화면은 `남음`으로 표현한다.
- `refund_locked`는 개별 grant의 환불 처리 상태로 유지하며, 계정 전체 `보류` 잔액으로 표시하지 않는다.

## 9. 현재 혜택 진행 막대 구현 결과

확정 정책과 상세 구현은 `2026-09-18-current-credit-benefit-progress-design.md`에 기록했다.

- 계정 전체 정본: `spendableBalance` → `사용 가능 N`
- 진행 막대 정본: nullable `currentBenefit`
- 무료 체험: `무료 체험 남음 N / 최초 지급량`
- 정기결제·관리자 부여 이용권: `이번 이용기간 남음 N / 현재 period 지급량`
- 추가 구매만 보유하거나 구버전 API 응답이면 진행 막대 없음
- 설정 화면과 홈 사이드 패널은 동일한 `AccountSummaryStore` 파생값을 사용

용어 구분:

- `admin_plan`: 관리자가 사용자에게 이용권을 부여하고, 그 이용권 정책에 따라 지급한 현재 period 기본 크레딧. 진행 막대에 포함한다.
- `admin_adjustment`: 관리자가 이용권과 무관하게 크레딧만 직접 지급한 것. `사용 가능` 총액에는 포함하지만 진행 막대에는 포함하지 않는다.
- `topup`, `promotion`: `사용 가능` 총액에는 포함하지만 현재 이용권/무료 체험 진행 막대에는 포함하지 않는다.

최종 로컬 검증은 Web API 2,906 tests와 빌드, Desktop Angular 4,683 tests와 빌드까지 통과했다. 구현과 문서는 각 기능 브랜치 및 `.codex/main`에 커밋·푸시했으며, 개발 브랜치 병합과 서버 배포는 아직 수행하지 않았다.
