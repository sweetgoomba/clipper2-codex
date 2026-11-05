# 추가 크레딧 승인 전 구매 자격 검사와 기존 정책 확인

2026-10-28 KST. 사용자 요청: 명시적으로 변경한 항목 외 결제 정책은 기존대로 유지한다. 기존 구현과 새 구현 항목을 섞어 미해결 정책처럼 제시하지 않는다. 추가 크레딧 결제 승인 전 구매 자격 검사를 보완한다.

## 작업 위치와 범위

- 저장소: `/Users/jina/project/adlight/.worktrees/signup-promotion-plugin-access-20261028/web/clipper_web_api`
- 브랜치: `feat/signup-promotion-plugin-access-20261028`
- 구현 전 최신 원격 dev로 fast-forward한 기준: `b2aead8e99270f6a71384668b38b3fa095ddbf6f`. 원본 checkout은 사용하지 않았다.
- 제품 변경은 API 결제 관련 6개 파일이다. 커밋·푸시·병합은 이번 요청 범위가 아니므로 수행하지 않았다.
- 요금제별 플러그인 허용과 영구 기본 상태, 가입 시 크레딧 전용 프로모션 기능은 설계 논의 단계다. 이번 보완이 해당 전체 기능의 구현 완료를 뜻하지 않는다.

## 후속 확인된 정책 범위

- 유료 요금제는 Basic/Pro/Business 3등급이고, 기본 상태를 포함하면 4가지 이용 상태다. 기본 상태 이름은 미정이다.
- 플러그인 사용 가능 여부는 사용 당시의 이용 상태로 결정한다. 기본 상태는 가입 크레딧 잔액/만료와 분리한다.
- 같은 추가 크레딧 상품의 가격은 요금제별로 달리하지 않는다. 사용자는 추가 크레딧 신규 구매를 활성 유료·프로모션 이용권에만 허용한다고 명시했다. 기본 상태나 프로모션 크레딧만 받은 상태는 신규 구매 자격이 아니다.
- 개발 서버와 로컬의 실제 `/catalog/credit-products` 응답에서 400/1,000/4,000 상품 모두 `validityDays=30`임을 확인했다. 운영 API는 502여서 운영 상품 값은 확인하지 못했다. 실제 유효기간은 주문에 보존한 값으로 결제 성공 시점부터 계산한다.
- 정기결제 크레딧의 월별 지급/만료, 연간 구독의 월별 지급, 먼저 지급된 유효 크레딧부터 차감, 기존 요금제 변경 계산, 기존 환불, 가입 혜택 최초 1회 지급은 기존 정책을 유지한다.
- 추가 구매분은 구매 시 지급된 수량·만료일을 유지한다. 이용권 변경/종료가 추가 크레딧 유효기간을 초기화하거나 구매 당시 플러그인 권한을 연장하지 않는다.

## 앞서 나열한 5개 항목의 실제 현황

| 항목 | 현재 코드와 테스트 확인 결과 | 이번 제품 변경 |
|---|---|---|
| 정기 크레딧 사용 후 업그레이드 | `subscription-plan-change-policy.ts`는 남은 기간과 크레딧 사용량에 따른 잔여 가치를 각각 계산하고 더 큰 추가 결제액을 선택한다. `fulfillRestartedSubscriptionUpgrade`와 `replaceSubscriptionForImmediatePlanChange`는 이전 정기 지급분을 정리하고 새 계약 기간을 시작한다. 순수 정책·발급·이용권 교체 테스트가 있다. | 없음: 기존 구현 |
| 변경 시 크레딧 만료 유지 | `fulfillTopup`은 `paidAt`과 주문의 유효일수로 만료일을 정하며 `accessGrantId`와 `subscriptionId`는 null이다. 이용권 교체는 해당 이용권에 속한 정기 지급분만 처리한다. 정확한 30일 및 이용권 없는 상태의 유효 크레딧 사용 테스트가 있다. | 없음: 기존 구현 |
| 결제 환불과 혜택 처리 | `PaymentRefundEligibilityService`가 기존 환불 자격/사용량 규칙을 적용한다. `PaymentRefundEffectsService`는 원화 환불 항목 완료 후 해당 환불에 잠긴 지급분을 회수하고 이용권을 처리한다. 사용량 재검사·환불 대상 지급분 처리·다른 이용권 유지 테스트가 있다. | 없음: 기존 구현 |
| 가입 혜택 재지급 방지 | `FreeTrialProvisioner`는 회원 잠금 후 기존 참여 정보를 찾고, 있으면 기존 결과를 반환한다. 반복/동시 호출 1회 지급 테스트가 있다. 영구 기본 상태 도입 때도 이 기존 일회 지급 규칙을 사용한다. | 없음: 기존 구현 |
| 현재 등급별 플러그인 실행 제한 | `EffectiveAccessService.allowsPlugin`은 정의돼 있지만 현재 제품 코드에 호출부가 없다. 확인한 `OperationsService.quote/start`는 과금 작업과 크레딧을 검사한다. | 이번 신규 플러그인 차등 기능에서 구현할 항목이며, 기존 구현 완료로 표시하지 않는다 |

## 승인 전 자격 검사 보완

기존 테스트에는 이용권 만료 후에도 이미 만든 추가 크레딧 주문의 결제를 완료하는 동작이 명시돼 있었다. 사용자가 승인 전 자격 재검사를 요청했으므로 이 동작과 테스트를 함께 변경했다.

- `TopupPaymentsService.requirePurchaseAccess`로 주문 생성과 신규 승인 시작의 구매 자격 판정을 공유한다. 현재 유료 구독의 실제 유효 기간 또는 현재 적용되는 프로모션 이용권을 확인한다.
- 동일한 트랜잭션 매니저의 기존 구독/회원 advisory lock을 사용한다. 승인 시작 상태 변경까지 잠금이 유지된다.
- 아직 승인 시작 전인 `checkout_ready` 주문은 자격이 없으면 PG 승인 호출 전에 `NO_ACTIVE_ACCESS`로 거절한다.
- 이미 `paid`인 응답과 승인 진행/상태 확인 중인 주문의 기존 멱등 처리·복구는 유지한다. 새 구매를 시작하는 검사와 이미 시작한 결제의 상태 복구를 구분한다.
- 거절 시 컨트롤러는 기존 실패 처리와 결제 결과 화면으로 연결한다. 기존 pre-checkout CAS를 재사용하여 이미 시작한 결제 상태를 덮지 않는다.
- 공통 결제 실패 문구: ‘현재 이용 중인 유료·프로모션 이용권이 없어 추가 크레딧 결제를 진행하지 않았습니다.’

변경 파일:

- `src/modules/payments/application/topup-payments.service.ts`와 해당 spec
- `src/modules/payments/presentation/toss-payments-redirect.controller.ts`와 해당 spec
- `src/modules/payments/domain/payment-failure-message.ts`와 해당 spec

## 검증

- 수정 전 유료 자격 소멸, 정확한 paid period 종료 시각, 프로모션 회수의 3개 회귀 사례가 승인돼 실패함을 확인했다. 정상/이미 결제/진행 중 복구 사례는 기존 동작을 확인했다.
- 결과 화면 연결과 거절 사유 안내의 2개 테스트도 구현 전 실패를 확인했다.
- 수정 후 관련 3개 suite **82개 통과**.
- `npm run build` 통과.
- 전체 `npm test -- --runInBand --json ...`: **457개 suite, 4,845개 테스트 통과; 10개 suite / 69개 테스트 skip; 실패 0**. 최초 sandbox 실행은 임시 HTTP listen EPERM으로 중단됐으며, 임시 포트 바인딩이 가능한 실행으로 재검증했다.
- `git diff --check` 통과.
- 코드 리뷰 스킬에 따른 독립 읽기 검토: 조치할 지적 없음. 트랜잭션 잠금과 순서, 재시도 상태, 실패 CAS를 검토했다. 별도 PostgreSQL 동시성/실제 PG망 실험을 수행한 결과로 확대하지 않는다.

검증 원본은 `/private/tmp/clipper-topup-confirmation-access-tests-20261028.json` 및 같은 이름의 `.log`에 있다.
