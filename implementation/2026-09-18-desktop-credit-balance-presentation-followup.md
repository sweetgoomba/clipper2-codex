# 데스크톱 크레딧 잔액 표시 후속

날짜: 2026-09-18 KST

상태: **원인 확인·정책 제안 기록 완료. 이번 작업에서는 제품 코드 수정 안 함.**

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

### 선택 사항 — 300 / 400과 사용 100 복원

이 표기를 제품에서 계속 원한다면 `heldBalance`로 추론하지 않는다. 서버가 다음 중 합의된 의미를 명시적으로 제공해야 한다.

- 현재 유효한 grant의 `initialCredits` 합계
- 현재 유효한 grant의 `remainingCredits` 합계
- 그 둘을 기준으로 계산한 `consumedCredits`

무료체험, 구독, 추가 구매, 만료, 취소, 환불이 섞일 때 어떤 grant를 분모에 포함할지 정책을 먼저 정해야 한다. 정책 결정 전의 안전한 최소 UI는 `사용 가능 300` 단일 표시다.

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

## 7. 이번 작업의 경계

이번에는 원인 조사와 문서화만 수행한다. Desktop/Web API 제품 코드, DB schema/data, 배포 환경은 이 문제 때문에 변경하지 않는다. 실제 표시 수정은 별도 사용자 승인과 테스트 우선 구현으로 진행한다.
