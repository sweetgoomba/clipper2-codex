# TossPayments PG 최종 정책 변경 구현 계획

- 작성일: 2026-09-02
- 상태: 구현·검증 및 저장소별 로컬 커밋 완료
- 정책 기준: `2026-09-02-toss-payments-pg-final-policy-delta.md`
- 체크포인트: API `7a0d7fd`, Admin `5328418`, Customer `806b176`, Desktop Angular `f02bf221`, Desktop NestJS `60a4f07`

## 목표

Phase 4까지 구현된 결제·환불 기능을 2026-09-02 확정 정책에 맞춘다. 기존 환불 이력, 토스 취소 복구, 권한 분리 구조는 유지하고 요금제 변경 계산·이용기간 초기화·크레딧 처리·환불 가능 범위·화면 표시만 필요한 만큼 수정한다.

## 보호 조건

- 기존 migration 파일과 migration history를 수정하지 않는다.
- 5433·5434·5435 DB에는 migration이나 write를 실행하지 않는다.
- 실제 토스 결제·취소 API를 호출하지 않는다.
- Customer의 기존 `build/`와 API의 `docs/api/openapi.yaml.orig`를 수정·삭제·stage하지 않는다.
- `operator-jwt-expiry-test`와 `meme-overlay-timeline-seek` worktree를 수정하지 않는다.
- `BILLING_DELETED`, user-MID webhook, 가상계좌 발급·입금·만료 TODO는 이번 정책 변경과 섞지 않는다.

## Task 1 — 요금제 변경 분류와 차액 계산 도메인 고정

대상:

- `src/modules/payments/domain/subscription-plan-change-policy.ts`
- `src/modules/payments/domain/subscription-plan-change-policy.spec.ts`

작업:

- 월간→월간, 월간→연간, 연간→월간, 연간→연간과 동일·상향·하향 조합을 순수 함수로 분류한다.
- 연간→월간은 모두 거부한다.
- 즉시 변경은 같은 결제기간 상향, 같은 요금제 월간→연간, 월간→상위 연간으로 제한한다.
- 하향은 다음 결제일부터 적용한다.
- 기간 잔존가치와 정기구독 크레딧 잔존가치를 각각 계산하고 더 큰 차액을 선택한다.
- 정수 원 단위 반올림 규칙, 경계 시각, 잘못된 입력을 테스트로 고정한다.

검증:

- 새 순수 도메인 테스트를 먼저 실패시키고 최소 구현 후 통과시킨다.

## Task 2 — 차액 계산 입력과 결과 스냅샷 저장

대상:

- 신규 Admin DB migration `1788700000000-*`
- `payment.model.ts`
- `payment-order.entity.ts`
- `payment-orders.repository.ts`
- `typeorm-payment-orders.repository.ts`
- 각 spec과 datasource 등록

작업:

- 계산 시각, 기간 기준 잔존가치·차액, 크레딧 총량·사용량·잔존가치·차액, 최종 선택 기준과 금액을 결제 주문에 저장한다.
- 기존 결제 주문은 nullable로 보존하고 신규 즉시 변경 주문만 완전한 스냅샷을 요구한다.
- migration은 추가형으로만 작성한다.

검증:

- migration SQL 계약, entity↔domain 매핑, 생성·조회 round-trip 테스트.

## Task 3 — 현재 정기구독 크레딧 사용량 조회

대상:

- `credits.repository.ts`
- `typeorm-credits.repository.ts`
- 관련 spec

작업:

- 현재 유료 계약 기간 안에서 해당 정기구독으로 지급된 크레딧의 총 지급량과 실제 사용량을 조회한다.
- 환불 회수, 관리자 조정, 만료를 사용량과 혼동하지 않고 실제 소비 ledger를 기준으로 계산한다.
- 연간 계산의 기준 총량은 현재 연간 상품의 월 지급량 × 12로 고정한다.

검증:

- 월간·연간, 미사용·일부 사용·전량 사용·만료·환불 잠금 사례.

## Task 4 — 요금제 변경 견적·결제 흐름 변경

대상:

- `subscription-plan-changes.service.ts`
- 관련 service/controller/OpenAPI spec

작업:

- Task 1 분류 결과를 견적과 실행에서 공통 사용한다.
- 월간→연간 동일·상향 즉시 변경을 허용한다.
- 연간→월간은 명시적으로 거부한다.
- 즉시 변경 금액은 기간·크레딧 차액 중 큰 값으로 산정하고 Task 2 스냅샷을 주문에 저장한다.
- 생성된 견적을 실행할 때 현재 상태와 스냅샷 fingerprint를 다시 검증한다.
- 결제 실패·불확정이면 기존 이용권과 예약 변경을 그대로 유지한다.

검증:

- 8개 변경 유형, 견적 재사용·만료·상태 변경, 결제 실패·불확정 회귀 테스트.

## Task 5 — 즉시 변경 후 새 계약 시작과 크레딧 교체

대상:

- `payment-fulfillment.service.ts`
- `access-grants.service.ts`와 repository
- `subscriptions.repository.ts`와 TypeORM 구현
- `credit-grants.service.ts`와 repository
- 관련 spec

작업:

- 결제 승인 시각부터 목표 상품의 새 이용기간·결제주기·월별 크레딧 경계를 시작한다.
- 기존 이용권의 정기구독 크레딧만 종료하고 새 요금제 첫 월 크레딧 전량을 지급한다.
- 무료 체험과 별도 구매 크레딧은 유지한다.
- 같은 결제 주문 재처리에서도 중복 종료·중복 지급되지 않게 한다.

검증:

- 월간→월간, 월간→연간, 연간→연간 즉시 상향과 재실행·실패 rollback 테스트.

## Task 6 — 무료 체험·별도 구매 크레딧의 시각 기준 30일 만료

대상:

- `free-trial-provisioner.service.ts`
- `payment-fulfillment.service.ts`
- 시간 유틸리티와 관련 spec

작업:

- 한국 달력 자정 계산을 제거하고 실제 지급 시각 + 30×24시간으로 만료한다.
- 정기구독 월 경계 계산은 기존 월 앵커 시각 로직을 유지한다.
- 이미 적용된 migration은 수정하지 않고 런타임의 신규 지급만 변경한다.

검증:

- 자정 직전·직후, DST 비적용 한국 시간, 밀리초 경계 테스트.

## Task 7 — 월간·연간·추가 크레딧·상향 차액 환불 정책 변경

대상:

- `payment-refund-eligibility.service.ts`
- `payment-refund-command.service.ts`
- `payment-refund-effects.service.ts`
- 환불 query와 관련 spec/E2E

작업:

- 월간·연간 모두 해당 결제/계약의 정기구독 크레딧 실제 사용 이력이 0일 때만 전액 환불한다.
- 연간 부분 환불과 `benefit_period_end` 종료를 일반 환불에서 제거한다.
- 만료됐지만 실제 사용하지 않은 정기구독 크레딧은 연간 환불을 막지 않는다.
- 별도 구매 크레딧은 유효하고 전량 남아 있을 때만 전액 환불한다.
- 상향 차액 결제는 해당 상향 이후 지급된 크레딧이 미사용일 때 그 차액 결제 한 건만 전액 환불한다.
- 상향 환불 완료 시 현재 이용권을 즉시 종료하고 새 정기구독 크레딧을 회수하되 이전 이용권·결제·잔존가치는 복원하지 않는다.

검증:

- 상품별 허용·차단, 만료 미사용, 상향 연속 결제, 환불 후처리·재처리·동시성 E2E.

## Task 8 — Admin·Customer·OpenAPI 정합성 변경

대상:

- Web API OpenAPI와 계약 spec
- Admin 환불 워크벤치·상세와 API 모델
- Customer 결제내역·구독·크레딧 표시와 API 모델

작업:

- 관리자가 임의 부분 환불액을 입력하는 일반 흐름을 제거하고 취소 가능 전액을 확인값으로 표시한다.
- 연간 부분 환불·현재 월 종료 문구와 상태를 제거한다.
- 요금제 변경 견적에 기간 차액, 크레딧 차액, 최종 차액을 이해 가능한 수준으로 표시한다.
- 고객 화면은 전액 환불과 즉시 종료만 표시하고 내부 계산·provider 세부정보는 노출하지 않는다.

검증:

- API 계약 테스트, Admin·Customer focused test와 전체 테스트·빌드.

## Task 9 — 전체 검증과 후속 단계 판정

작업:

- API unit·build와 fake provider 기반 E2E를 실행한다.
- Admin·Customer·Desktop 전체 회귀 테스트와 build를 실행한다.
- 신규 disposable DB에서 전체 migration을 적용하고 스키마를 확인한다.
- 기존 migration이 적용된 disposable 복제 DB에서 새 migration만 적용해 데이터 보존을 검증한다.
- 실제 토스 호출, 운영 DB, push·merge·PR·deploy는 수행하지 않는다.

완료 후:

- 정책 변경 반영 결과를 별도 검증 보고서로 남긴다.
- 그 다음에만 기존 Phase 5 TODO 또는 Phase 6 출시 준비로 이동한다.
