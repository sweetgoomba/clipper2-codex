# 프로모션·크레딧·이용권·결제 전체 흐름 감사

작성: 2026-10-23 KST. **이 문서는 수정 전 기준 감사 기록**이다. 당시에는 제품 코드 수정을 시작하지 않았다.

> 후속: 사용자 승인 후 A01–A17 및 독립 리뷰 추가 2건을 수정·검증했다. 현재 작업 트리·미커밋 상태·검증 결과는 [수정 결과](2026-10-23-billing-promotion-audit-fixes-result.md)를 따른다. 아래 재현은 수정 전 코드에 대한 기록이다.

## 판단

확정된 결함·표시 불일치 17건을 확인했다. 우선 수정 P1 6건, 일반 수정 P2 8건, 낮은 우선순위 P3 3건이다. 별도로 완료 수량 정산의 클라이언트 신뢰 경계 1건은 현재 로컬 저장 기준 정책과 함께 검토해야 한다.

기존 테스트가 통과해도 현재 구현을 안전하다고 판단하기 어렵다. 실제 PostgreSQL에서 취소된 환불 실행, 환불 중 자동 청구, 결제 후 이용권 미지급, 회수 대상 크레딧의 재활성화, DB UPDATE 반환 계약 오류를 재현했다. 테스트 수보다 드라이버 계약·상태 전이·실행 순서를 다루는 검증의 보강이 중요하다.

## 기준과 범위

| 저장소 | 검토한 로컬 기준 |
|---|---|
| Web API | `dev`, `db0ca36` |
| 관리자 웹 | `fix/member-promotion-access-summary-20261023`, `ae9b15d` |
| 회원 웹 | `dev`, `fbd4573` |
| Desktop NestJS | `dev`, `0fe9f8b0` |
| Desktop Angular | `dev`, `89e62cb9` |

정책 기준은 [현재 프로모션 설계](../design/2026-10-23-promotion-campaign-current-state.md)와 사용자의 이후 지시다. 이번 감사는 위 checkout의 전체 관련 흐름을 대상으로 하며, 원격의 그 이후 변경이나 운영 서버에서 실행 중인 revision과의 일치를 주장하지 않는다. API의 기존 `.env.example`, `auth.controller.ts` 로컬 변경을 보존했다. 제품 소스·Git 브랜치·운영/기존 로컬 DB·실제 결제에는 변경을 가하지 않았다.

검토 경로: 캠페인/코드 생성·수정·활성 상태·삭제 제한 → 미리보기·자격 검사·동시 등록·상한 → 이용권/월별 크레딧 지급 → FIFO 차감·만료·작업 환급·회수 → 카드 등록/이탈·예약 첫 결제·재시도·갱신·상품 변경·구독 취소 → 환불 실행·취소·복구 → 성과 집계/XLSX → 회원/관리자/데스크톱 상태 표시.

## 확정 사항 요약

| ID | 우선순위 | 문제 |
|---|---|---|
| A01 | P1 | 이용권 UPDATE 반환 형식 오류로 잘못된 응답 및 0행 변경의 거짓 성공 |
| A02 | P1 | 취소 완료된 환불을 지연된 실행 요청이 다시 실행 |
| A03 | P1 | 환불 처리로 중단한 연체 구독이 자동/수동 갱신 청구 대상에 남음 |
| A04 | P1 | 불확실한 업그레이드 결제를 PG 성공 확인 후에도 자동 복구하지 못함 |
| A05 | P1 | 갱신 청구·구독 취소·만료 처리가 겹치면 결제만 되고 지급 실패 |
| A06 | P1 | 즉시 요금제 변경으로 회수해야 할 소진 크레딧이 작업 환급으로 재활성화 |
| A07 | P2 | 관리자 이용권 기간 연장 시 다음 월 크레딧 지급 일정 누락 |
| A08 | P2 | 시작 예정 관리자 이용권의 등급 변경이 시작일을 현재로 당김 |
| A09 | P2 | 업그레이드 처리 중 표시/견적의 사용 가능 잔액과 실제 차감 가능액 불일치 |
| A10 | P2 | 프로모션 크레딧의 실제 만료일 대신 월 혜택 종료일 표시 |
| A11 | P2 | 첫 결제 실패 회원에게 카드 변경 UI를 숨김 |
| A12 | P2 | 예약 취소 후 관리자 헤더가 현재 프로모션 대신 과거 예약 상품 표시 |
| A13 | P2 | 첫 결제 재시도 성공 후 이용권·크레딧 화면 미갱신 |
| A14 | P3 | QR 등록 성공 후 늦은 초기 조회가 새 참여 내역을 덮음 |
| A15 | P3 | 카탈로그 지연 시 혜택 모달에 실제 등급명이 표시되지 않음 |
| A16 | P3 | 회수 안내에 회원에게 숨기기로 한 내부 캠페인명 노출 |
| A17 | P2 | 환불 작업 선점 직후 장애가 나면 자동 복구 대상에서 영구 누락 |

## P1: 금전·크레딧·이용권 정합성

### A01 — UPDATE 결과를 도메인 객체로 잘못 변환

- 위치: `web/clipper_web_api/src/modules/access/infrastructure/typeorm-access.repository.ts:272–452`, 대표 `:356`; `typeorm-free-trials.repository.ts:41`.
- 설치된 TypeORM PostgreSQL 드라이버는 raw UPDATE 결과를 `[rows, affectedCount]`로 반환한다. 해당 메서드는 이를 행 목록으로 선언하고 `requiredGrant(rows[0])`를 호출하여 **행 배열 자체**를 이용권으로 변환한다. 빈 배열도 truthy라 변경 0건을 실패로 인식하지 못한다.
- 실제 DB 재현: `updatePeriod`로 종료일을 바꾸면 DB 저장은 정상이나 반환한 `id/status`가 undefined, 날짜는 Invalid Date였다. 이미 12월까지 연장된 이용권에 11월 시각으로 `endExpired`를 호출하면 DB는 active를 유지하는데 메서드는 성공 반환했다.
- 영향: 관리자 이용권 수정 응답이 깨지고 상위 작업은 무변경을 성공으로 판단할 수 있다. 기존 업그레이드 지급 경로 `payment-fulfillment.service.ts:581–610`은 반환 `access.id`를 사용하므로 크레딧의 이용권 연결도 누락될 수 있다. 무료체험 정책 UPDATE도 같은 형식 오류다.
- 수정: 이미 사용 중인 `returningRows`와 동일한 정규화를 모든 UPDATE 반환 경로에 적용하고, 변경 0건·1건의 의미를 호출자 계약에 맞게 처리한다. 각 호출자의 후속 상태 변경도 검증한다.
- 필수 회귀: 실제 PostgreSQL에서 UPDATE 0행/1행, 변경된 객체의 모든 필수 필드, 만료와 갱신 교차 실행. 기존 mocks의 `[row]` 반환을 실제 드라이버 형식과 일치시킨다.

### A02 — 취소한 환불이 다시 실행됨

- 위치: `web/clipper_web_api/src/modules/payments/application/payment-refund-execution.service.ts:38–88`; `infrastructure/typeorm-payment-refunds.repository.ts:378–396`, `:773–815`.
- 실행 요청은 환불 상태와 PG 사전 조회를 수행한 뒤 item을 claim한다. 그 사이 다른 운영자가 환불을 취소하면 case는 voided, item은 failed가 되고 잠긴 크레딧은 풀린다. 그러나 claim은 부모 case의 voided 여부를 재검사하지 않고 failed item을 다시 가져간다.
- 실제 DB + 가짜 PG + 실제 effects 서비스 재현: `voidAccepted=true → moneyStatus=voided → cancelCalls=1 → moneyStatus=completed, internalStatus=completed`. 원래 크레딧 400은 `active`, `refund_case_id=null`로 남았다.
- 영향: 취소됐다고 알려준 환불이 진행되고, 돈을 돌려준 뒤에도 크레딧을 사용할 수 있다. 늦은 사전 조회 실패가 완료 상태를 manual_action_required로 덮는 경로도 동일한 상태 전이 보호 문제다.
- 수정: 부모 case 상태와 item claim을 같은 원자적 조건/잠금으로 보호하고 취소·실행의 순서를 고정한다. 종결 상태를 이전 단계로 덮는 UPDATE를 조건부로 바꾼다.
- 필수 회귀: preflight 전후, claim 전후, 취소 후 지연 실행, 이중 실행, completed 이후 늦은 실패. 취소 성공 뒤에는 PG 호출이 0회여야 한다.

### A03 — 환불 처리 중에도 갱신 재시도 청구

- 위치: `web/clipper_web_api/src/modules/payments/infrastructure/typeorm-subscriptions.repository.ts:350–362`; `application/subscription-renewal.service.ts:125–185`, `:402–412`; due finder `typeorm-subscriptions.repository.ts:195–235`.
- `beginRefund`는 nextBillingAt을 지우지만 연체 구독의 status=past_due와 retryAt은 남긴다. due finder와 실행 판단에는 refundProcessingCaseId/renewalPausedForRefundAt 차단이 없다.
- 실제 DB 재현: 환불 처리 ID 및 중단 시각이 있고 nextBillingAt=null인 구독이 due finder에 선택되며, 실제 renew 호출에서 가짜 PG `chargeCalls=1`이었다.
- 영향: 운영자가 환불을 접수해 자동결제를 멈춘 회원에게 다음 결제가 발생할 수 있다.
- 수정: 갱신 후보 선정과 실제 청구 직전 검증 모두 환불 중단을 적용한다. 이미 PG에 전송한 청구의 확인·복구는 새 청구 시작과 분리해 처리한다.
- 필수 회귀: active/past_due 각각의 환불 시작 후 자동 및 수동 재시도, 이미 진행 중인 청구와 환불의 교차 실행.

### A04 — 업그레이드 결제의 불확실한 결과 복구 누락

- 위치: `web/clipper_web_api/src/modules/payments/application/payment-reconciliation.service.ts:193–198`; `payment-recovery.scheduler.ts:36–43`; `subscription-plan-changes.service.ts:631`, `:668`.
- 업그레이드 결제를 보낸 뒤 응답을 잃으면 reconciliation_required가 된다. 일반 재조정은 주문과 일치하는 PG DONE을 받아도 SUBSCRIPTION_PROVIDER_STATUS_INCONCLUSIVE로 남긴다. 스케줄러에는 첫 결제·갱신·이미 paid인 지급 복구만 있고 미확정 업그레이드 확정 경로가 없다.
- 실제 repository + reconciliation 서비스 재현: provider DONE, 결과 reconciliation_required 유지, `fulfillCalls=0`.
- 영향: 승인된 결제가 자동 복구되지 않으며 미확정 업그레이드가 다른 변경·갱신을 막을 수 있다. 동일한 변경 요청을 다시 제출하는 경로에 의존한다.
- 수정: 저장된 업그레이드 주문 snapshot으로 PG 확인·paid 확정·지급을 재개하는 공통 복구 경로를 만들고 스케줄러/관리자 재조정/웹훅에서 사용한다.
- 필수 회귀: PG 승인 직후 timeout, 프로세스 종료, 브라우저 이탈, 새 quote 없이 복구, 중복 webhook. 승인·지급은 각 1회.

### A05 — 갱신 중 취소·만료가 겹치면 결제 후 지급 실패

- 위치: `web/clipper_web_api/src/modules/payments/application/payment-fulfillment.service.ts:765–771`; `subscription-renewal.service.ts:315–343`, `:70–121`.
- 갱신 청구가 진행 중일 때 취소하면 cancelAt에 기존 기간 종료일이 저장된다. 별도 만료 실행이 구독을 ended로 바꾼 뒤 결제가 성공하면 fulfillment는 renewalAttemptedAt > cancelAt을 이유로 거절한다. 정기 작업은 보통 결제 기일을 조금 지난 후 실행하므로 이 비교가 성립한다.
- 실제 서비스/DB 재현: provider 응답 일시 보류 → cancel → endExpiredAccess → provider DONE. 주문은 paid, fulfillment는 failed, 직접 재시도도 INVALID_ENDED_RENEWAL_ATTEMPT였다.
- 영향: 청구 성공 뒤 이용권·크레딧이 지급되지 않는 상태가 자동 복구되지 않는다.
- 수정: 미확정 갱신이 있으면 만료 확정을 보류하거나, 실제 취소 요청 시각과 이미 claim된 청구의 순서를 보존해 일관되게 처리한다. 단순히 날짜 비교를 없애면 늦게 시작한 청구까지 허용할 수 있으므로 청구 권리 획득 시점 검증이 필요하다.
- 필수 회귀: dueAt + epsilon의 정상 갱신 claim, 취소, 다중 worker 만료, PG 지연 성공·실패. A01을 고친 뒤에도 이 별도 상태 전이 문제를 검증한다.

### A06 — 즉시 상품 변경 후 소진된 이전 크레딧 재활성화

- 위치: `web/clipper_web_api/src/modules/credits/infrastructure/typeorm-credits.repository.ts:150–154`; `application/credit-grants.service.ts:461`.
- 구독 교체 회수 조회는 active·잔액 양수만 포함한다. 모두 사용한 depleted 지급분은 회수 표시를 하지 않는다. 이후 그 크레딧을 사용하던 작업이 실패하면 환급 경로가 depleted를 active로 바꾼다.
- 실제 DB 재현: 400 지급 → 400 사용 → 즉시 변경 회수 → 작업 실패 환급 400. 이전 지급분이 active/잔액400/차감가능400으로 복원됐다.
- 영향: 새 요금제의 지급 크레딧과 회수했어야 할 이전 크레딧이 함께 사용 가능해진다.
- 수정: 프로모션 회수에 이미 적용된 것처럼 active/depleted를 모두 회수 대상으로 고정하고, 원장 차감량만 양수 잔액에 한정한다. 작업 환급 후에도 회수 상태를 보존한다.
- 필수 회귀: 전액 소진·부분 소진·미사용 각각의 상품 변경 뒤 작업 실패/부분 환급.

## P2: 지급 일정·회원 안내·운영 화면

### A07 — 관리자 이용권 연장 후 월 지급 누락

- 위치: `web/clipper_web_api/src/modules/access/application/access-grants.service.ts:470`; `infrastructure/typeorm-access.repository.ts:431`.
- 10/1–11/1 이용권의 nextCreditGrantAt은 마지막 월이라 null이다. 10/23에 종료일을 1/1로 연장해도 이 값을 복원하지 않으므로 11월·12월 지급이 누락된다. 실제 서비스+메모리 저장소 실행으로 확인했다.
- 수정: 기간 연장 시 anchor·마지막 지급 경계를 기준으로 다음 지급일을 재계산한다. 현재 월 재지급은 하지 않는다. 종료일 단축 후 재연장도 검사한다.

### A08 — 미래 시작 이용권의 등급 변경이 즉시 시작으로 변함

- 위치: `web/clipper_web_api/src/modules/access/application/access-grants.service.ts:515–528`.
- grantAdmin은 미래 시작 이용권도 active로 저장하지만 changeAdminTier는 scheduled 상태일 때만 시작일을 보존한다. 11/1 시작 Basic을 10/23에 Pro로 바꾸면 시작일이 10/23이 되고 차액도 당일 지급된다. 실제 서비스+메모리 저장소에서 확인했다.
- 수정: 현재 상태명에만 의존하지 않고 startsAt과 현재 시각으로 예정 여부를 판단한다. 미래 시작·최초 지급 일정을 같이 보존한다.

### A09 — 사용 가능 잔액 조회와 차감 조건 불일치

- 위치: `web/clipper_web_api/src/modules/credits/infrastructure/typeorm-credits.repository.ts:399`; 비교 대상 `:375–383`.
- 미확정 구독 업그레이드 동안 실제 차감은 해당 구독 크레딧을 제외하지만 sumCurrentBySource는 포함한다. 실제 PostgreSQL에서 표시 잔액400/차감가능0을 확인했다. quote는 가능하다고 안내한 뒤 start가 INSUFFICIENT_CREDITS로 실패할 수 있다.
- 수정: 보유와 사용 가능의 의미를 구분하고, 사용 가능 조회·견적·실제 차감에 동일한 조건을 적용한다.

### A10 — 프로모션 크레딧 사용 기한 오표시

- 위치: `web/clipper_web_client/src/app/features/portal/credits/credits.component.html:80–82`.
- benefitPeriodEnd를 expiresAt보다 우선 표시한다. 10/23 등록·유효기간7일의 실제 만료는 10/30인데 화면에는 월 경계 11/23이 보인다. 서버 지급·projection·템플릿을 대조해 확인했다.
- 수정: 사용 기한은 expiresAt으로 표시한다. 월 혜택 기간을 따로 표시할 때도 이름과 의미를 구분한다.

### A11 — 첫 결제 실패 후 카드 변경 불가

- 위치: `web/clipper_web_client/src/app/features/portal/dashboard/dashboard.component.ts:241`; `dashboard.component.html:166`.
- pending을 canManageSubscription에서 제외해 결제수단 영역을 통째로 숨긴다. 서버는 확정 실패한 첫 결제의 카드 변경을 지원한다. `pending + firstPaymentFailedAt` 입력으로 원본 함수를 실행해 false를 확인했다.
- 수정: 카드 관리와 요금제 변경 조건을 분리하고 서버 changeAllowed를 반영한다. 첫 결제 실패·연체·예약만 완료·카드 미등록 상태를 각각 검증한다.

### A12 — 예약 취소 후 관리자 헤더에 잘못된 상품

- 위치: `web/clipper_web_admin/src/app/features/portal/members/detail/member-detail.component.ts:244`, `:259`.
- 현재 ae9b15d는 구독이 없거나 pending인 경우만 유효 프로모션을 우선한다. Business 프로모션 중 Basic 예약을 취소하면 최신 구독 canceled와 Basic 이름이 남아 헤더가 “구독 취소됨 / Basic 월간”으로 돌아간다. ended/stopped도 같다. 원본 computed 실행으로 확인했다.
- 수정: 현재 유효 이용권을 header의 근거로 사용하고 취소·종료된 구독 이력은 해당 구독 영역에서 표시한다. 앞서 고친 pending 사례에 canceled/ended/stopped 회귀 검증을 추가한다.

### A13 — 재시도 결제 성공 후 대시보드 미갱신

- 위치: `web/clipper_web_client/src/app/features/portal/dashboard/dashboard.component.ts:345–347`, `:537–540`.
- 재시도에서 paid/fulfillment succeeded가 와도 구독만 다시 읽는다. 원본 메서드 실행 결과 subscription=active로 바뀐 뒤 access=null/credits=0이 그대로였다.
- 수정: 성공 시 기존 refreshAccountProjections를 사용해 이용권·크레딧·구독·카드를 함께 갱신한다.

### A17 — 환불 작업 선점 직후 중단 시 자동 복구 누락

- 위치: `web/clipper_web_api/src/modules/payments/application/payment-refund-recovery.scheduler.ts:29–32`; `infrastructure/typeorm-payment-refunds.repository.ts:231–257`, `:400–436`.
- scheduler가 부모 환불 건을 pending에서 processing으로 바꾼 직후, 첫 상세 항목을 선점하기 전에 프로세스가 종료되면 부모는 processing, 자식은 pending으로 남는다. 다음 부모 조회는 pending만 찾고 상세 복구는 uncertain 또는 오래된 processing만 찾으므로 어느 쪽도 선택하지 않는다.
- 실제 PostgreSQL repository 재현: 3개 환불을 부모 선점까지만 수행한 뒤 다음 날 시각으로 조회했다. 각 항목은 processing/pending이며 `nextParent=null`, `nextRecoveryAfterOneDay=null`이었다. 수동 재시도 전까지 환불과 관련 잠금이 남을 수 있다.
- 수정: 부모 선점에 만료 후 회수 가능한 임대를 두거나 processing 부모 아래 pending 항목을 복구 대상으로 포함한다. PG 중복 취소 방지는 기존 항목 선점과 함께 보장한다.
- 필수 회귀: 부모 선점 직후 프로세스 종료 → 새 scheduler가 동일 환불을 중복 취소 없이 완료.

## P3: 요청 순서와 문구

### A14 — 초기 조회가 등록 후 조회를 덮음

`web/clipper_web_client/src/app/features/portal/promotions/promotions.component.ts:86–90`. QR query로 진입하면 초기 mine/history 응답 전에 등록할 수 있다. 등록 후 최신 조회가 완료된 뒤 늦은 초기 응답이 오면 참여 내역이 지워진다. 원본 load와 RxJS Subject로 재현했다. 요청 세대 확인 또는 switchMap으로 최신 결과만 반영한다.

### A15 — 카탈로그 지연 시 모달의 등급명 누락

`web/clipper_web_client/src/app/features/portal/promotions/promotions.component.ts:136–139`. preview 응답이 catalog보다 빠르면 모달에 '이용권'이라는 기본 문자열을 고정하고, 나중에 catalog가 와도 열린 모달은 갱신되지 않는다. 원본 메서드 실행에서 바깥 상태는 Business인데 모달은 '이용권'으로 남았다. 등급 정보를 준비한 뒤 열거나 preview에 회원 표시용 등급명을 포함한다.

### A16 — 회수 안내의 내부 캠페인명

`web/clipper_web_client/src/app/features/portal/dashboard/dashboard.component.html:15`. 회수 안내가 campaignName을 사용한다. 내부 캠페인명 비노출이라는 확정 규칙에 맞게 실제 등록 코드를 사용한다. 기존 테스트의 캠페인명 노출 기대도 함께 수정한다.

## 별도 검토: 완료 수량 정산의 신뢰 경계

`web/clipper_web_api/src/modules/operations/application/storyboard-settlement.ts:14–25`는 서버에 완료 receipt가 있어도 회원이 completed=[]를 제출하면 전액 환급한다. 일반 fail 경로는 materialHash가 있으면 전액 실패 처리를 차단하지만(`operations.service.ts:269`), 수량 정산 경로는 제출 목록의 누락을 검사하지 않는다. 현재 테스트도 이 빈 목록 환급을 명시한다.

기술적으로 결과를 받은 클라이언트가 완료 목록을 축소해 비용을 줄일 수 있는 경계다. 다만 데스크톱의 현 정책은 로컬에 실제 저장된 문서를 기준으로 정산하므로 단순히 서버 receipt 수만 강제하면 정상 저장 실패의 환급을 막을 수 있다. 서버가 확인한 완료와 로컬 저장 실패 증거를 함께 정의하는 수정이 필요하며, 이 항목은 위 17건과 구분한다.

## SOLID·추상화·중복 판단과 리팩토링 범위

현재 코드는 domain/application/infrastructure/presentation과 추상 repository를 이미 사용한다. 전면 재작성이나 상속 계층 추가보다 **여러 곳에서 다르게 적용되는 동일 규칙을 좁게 통합하는 것**이 필요하다.

| 개선 대상 | 실제 문제와 연결 | 권장 경계 |
|---|---|---|
| DB UPDATE 반환 정규화 | A01: 구현체가 약속한 UserAccessGrant 계약을 지키지 못함 | 같은 DB driver의 결과 정규화 및 0/1행 계약을 공유. 실제 DB 계약 테스트 필수 |
| 구독·환불 상태 전이 | A02–A05, A17: 청구/취소/복구에서 필요한 검사가 누락됨 | 상태 판단을 순수 규칙으로 모으고, 실제 전이는 잠금·조건부 UPDATE 및 중단 후 재개 가능한 선점으로 수행 |
| 확정 결제의 지급/복구 | A04: initial/renewal/upgrade가 각각 다른 복구 범위 | 목적별 검증을 유지하면서 확정·재조정·지급 호출 경로를 공통화 |
| 크레딧 회수 | A06: promotion의 depleted 보호가 subscription에 빠짐 | 출처별 대상 선정과 공통 회수 상태 처리를 분리 |
| 크레딧 사용 가능 판정 | A09: 잔액과 차감 쿼리 조건이 갈라짐 | 조회/견적/차감의 동일 가용성 predicate 또는 repository query builder |
| 이용권 시점과 지급 일정 | A07–A08: status와 시각 판정이 경로별로 다름 | 시작 예정/현재/만료 판단 및 다음 월 경계 계산을 공통화 |
| 회원 결제 상태 selector | A11–A13: pending 하나로 서로 다른 행동을 묶음 | 예약 준비, 첫 결제 실패, 카드 변경 가능, 현재 이용권을 각각 독립 selector로 표현 |
| 조회 요청 수명 | A14–A15: 모달과 비동기 조회 결과의 시점 불일치 | 화면별 요청 취소·최신 세대 보호와 필요한 데이터 준비 조건 |

SRP 관점에서는 하나의 UI 관리 조건이 카드 변경과 상품 변경을 동시에 결정하거나, 결제 서비스가 상태 규칙·PG 호출·지급 복구를 모두 직접 분기하는 부분이 문제다. DIP의 기본 repository 경계는 존재한다. LSP/반환 계약은 A01에서 실제로 깨져 있다. OCP/ISP를 이유로 기능별 상속 클래스나 추상 인터페이스를 무조건 추가할 근거는 없다. 재사용해야 할 것은 정확히 같은 정책이며, 서로 다른 사용자 행동까지 한 함수로 묶으면 A11 같은 오류가 난다.

추가 개선 후보(확정 장애 수에는 미포함): PromotionReportService.report는 매 페이지 조회마다 전체 필터 결과를 200개씩 끝까지 읽어 summary를 계산한다(:73–100). 결과가 커지면 매 페이지 비용이 전체 데이터량에 비례한다. DB 집계와 페이지 조회 분리 및 실행계획 측정이 필요하다. 대규모 운영 부하를 이번에 측정하지 않았으므로 실제 성능 장애로 단정하지 않는다. Desktop Angular ApiCreditLedgerEntry.type의 payment_refund_revoke 누락도 계약 정리 대상이며 서버 displayName으로 현재 화면 장애는 확인하지 못했다.

## 검증 증거

| 검증 | 결과 |
|---|---|
| Web API 현재 소스 빌드 | 통과 |
| Web API 전체 Jest | 430 suites 통과, 6 skipped; 4,471 tests 통과, 26 skipped; snapshots 5 통과 |
| 프로모션/카탈로그/관련 migration 집중 테스트 | 9 suites / 91 tests 통과(위 전체 실행과 중복, 별도 합산 금지) |
| 결제 application/domain/presentation 집중 테스트 | 43 suites / 774 tests 통과(전체 실행과 중복) |
| 이용권/크레딧/작업 정산 집중 테스트 | 26 suites / 272 tests 통과(전체 실행과 중복) |
| 회원 웹 관련 ChromeHeadless 테스트 | 102/102 통과 |
| 관리자 웹 관련 ChromeHeadless 테스트 | 131/131 통과 |
| 격리 PostgreSQL 관리자 migration | 빈 DB에 현재 93개 migration 적용 성공 |
| 실제 PostgreSQL 크레딧 원장 테스트 | 5/5 통과(기본 전체 Jest에서 opt-in으로 제외되는 검사) |
| 실제 서비스+DB 프로모션 동시성 | 상한2 코드에 10명 동시 시도 → 성공2/상한거절8; 같은 캠페인 두 번째 코드도 별도2 성공 |
| 실제 서비스+DB 동일 회원 동시 등록 | 성공1/동일코드 이력거절1, 같은 캠페인 다른 코드 거절 확인 |
| 실제 서비스+DB 성과/회수/지연 월 지급 | 4등록/4,000크레딧 집계; 프로모션 회수 후 별도 관리자 지급500 보존; 지연된 2개월 월 지급2건 확인 |

새 결함 재현은 실제 DB(A01–A06의 관련 경로, A09, A17)와 원본 서비스/메서드 메모리 실행(A07–A08, A11–A15) 및 계약 대조(A10, A16)를 구분했다. PostgreSQL은 실제 DB를 사용했고 결제 제공자는 가짜 provider이며 네트워크 승인/청구/환불은 실행하지 않았다. 회원/관리자 브라우저에서 모든 재현을 수동으로 수행한 결과는 아니다.

임시 PostgreSQL은 `/private/tmp/clipper-billing-audit-k82_4cl7`의 전용 Unix socket/port55493, promotion_audit/payments_audit 및 TEMP TABLE만 사용했다. 기존 Docker/DB를 건드리지 않았다. 감사를 마친 뒤 이 임시 서버를 정상 종료했다. 재현 스크립트는 `/private/tmp/clipper-billing-audit-k82_4cl7/promotion-probes.cjs`, `/private/tmp/payments-baseline-repro.cjs`에 생성했으며 제품 파일에 포함하지 않았다.

정상 확인: 회원별 잠금과 캠페인별 거래 직렬화, 동일 캠페인 중복 방지, 코드별 상한, 프로모션 회수 시 다른 지급분 보존, 과거 이력 유지, 프로모션 종료 후 남은 크레딧의 개별 유효기간, 등록 ID 기반 주문 귀속. 결제액과 환불은 status=paid 주문의 누적 환불로 집계하며 환불 시 주문 status 자체를 지우지 않는 것을 확인했다.

한계: 실제 Toss망·운영 배포 revision·운영 데이터·다중 서버 부하·대량 XLSX 성능·데스크톱 빌드/전체 테스트는 이번 범위에서 검증하지 않았다. 검사한 시나리오 이외의 모든 버그가 없다는 보증은 아니다.

## 수정 순서와 완료 기준

1. A01 DB 반환 계약부터 고쳐 후속 상태 처리의 안전한 기반을 만든다. 실제 PostgreSQL 회귀를 저장소 테스트에 포함한다.
2. A02–A05, A17 환불·갱신·취소·복구 경계를 고친다. 가짜 PG의 지연/불확실 응답과 별도 DB 연결을 사용해 양쪽 실행 순서를 모두 재현한다.
3. A06–A09 회수·가용성·월 지급 일정 규칙을 통합한다. 기존 FIFO·유효기간·프로모션 회수 정책은 유지한다.
4. A10–A16 회원/관리자 상태 조회·표시를 고친다. 기존 공통 projection/selector를 재사용하고 네트워크 응답 역전·실패 후 성공을 검사한다.
5. 필요한 공통화만 수행하고 변경 전후 동작 및 회귀검사를 비교한다. 상품/정산 정책 변경과 단순 리팩토링을 같은 변경으로 섞지 않는다.

이번 결과는 수정 작업을 시작하기 위한 기준 보고서다. 기능이 dev에 병합됐다는 기존 기록은 보존하며, 안전성 검증과 발견한 결함 해결은 별도 미완료 작업으로 추적한다.
