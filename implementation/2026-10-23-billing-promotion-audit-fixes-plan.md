# 프로모션·결제 감사 17건 수정 계획

**Goal:** 감사 A01–A17의 재현된 결함을 고치고 실제 DB·비동기 순서 회귀 검사로 검증한다.
**Spec:** `.codex/implementation/2026-10-23-billing-promotion-baseline-audit.md` 및 `.codex/design/2026-10-23-promotion-campaign-current-state.md`.
**Architecture:** 기존 domain/application/infrastructure 경계를 유지한다. DB 반환·원자적 상태 전이·크레딧 가용 조건의 실제 중복만 통합하고 화면은 기존 projection과 공용 컴포넌트를 재사용한다.
**Tech:** NestJS/TypeORM/PostgreSQL, Angular 22, Jest/ChromeHeadless.

## 범위와 작업 위치

사용자가 감사 수정 방향을 승인했다. 추가 승인 대기 없이 구현·검증한다. 제품 소스는 최신 origin/dev에서 만든 `fix/billing-promotion-audit-20261023` 브랜치, `.worktrees/billing-promotion-audit-20261023/web/{clipper_web_api,clipper_web_client,clipper_web_admin}`에서 수정한다. 원본 API의 로컬 설정 2개와 원본 관리자 수정 브랜치를 보존한다. 네이티브 worktree 도구는 루트가 Git 저장소가 아니어서 실패하여 Git worktree로 생성했다. 문서는 모두 `.codex`에 둔다. 이번 요청은 수정이며 커밋·푸시·병합은 별도 요청 전 수행하지 않는다.

## 제약

- 기존 프로모션·크레딧 유효기간·FIFO·정산 귀속 정책 유지. 결제 금액·회원 혜택 변경 정책을 발명하지 않는다.
- 실제 Toss/운영 DB 및 기존 로컬 DB 사용 금지. 가짜 결제 제공자와 격리 PostgreSQL 사용.
- API raw 응답 유지. 새로운 엔드포인트나 상품 설정 불필요.
- 공개 내부 캠페인명 비노출. 동일 캠페인 1회, 코드별 상한, 다른 지급분 보존 유지.
- 실패 테스트/기존 실제 재현 → 최소 수정 → 관련 회귀 → 통합 검증.
- 작업 분담: 부모는 access/credits; 환불 담당은 refund repository/services; 결제 담당은 subscriptions/reconciliation/renewal/fulfillment; 화면 담당은 client/admin. 공유 파일 수정 필요 시 부모와 먼저 조율한다.

## 검증 초점

1. UPDATE 반환에서 0행/1행과 실제 TypeORM PostgreSQL 배열 형식.
2. PG 사전 조회/응답 지연 중 환불 철회·구독 취소·만료 교차.
3. 프로세스 중단 직후 재시작과 중복 실행의 지급/환불 각 1회.
4. depleted 지급분의 회수 후 작업 환급, 별도 지급분 보존.
5. 초기 조회/카탈로그 지연, 예약 취소/첫 결제 실패 후 화면의 실제 이용권·잔액.

## T1 — 이용권·크레딧 계약 (A01, A06–A09)

Files: `access/infrastructure/typeorm-access.repository.ts`, `typeorm-free-trials.repository.ts`; `access/application/access-grants.service.ts`; `credits/infrastructure/typeorm-credits.repository.ts`; 각 colocated tests와 실제 DB 회귀.
Interfaces: 기존 repository API 유지. 지급/회수 반환은 유효 모델 또는 계약에 맞는 0행 처리.
- [x] 실제 DB 반환 0/1행 및 회수 후 환급, 연장 nextCreditGrantAt, 미래 시작 등급 변경, 업그레이드 잠금 잔액 테스트를 먼저 실패시킨다.
- [x] UPDATE 반환 정규화를 적용하고 0행 검사. 기간 변경에 다음 월 지급 일정 재계산. 미래 startsAt 보존. depleted 포함 회수. 잔액/차감 가용 조건 공유.
- [x] 집중 Jest 및 격리 PostgreSQL 검증. 이미 정상인 FIFO·만료·다른 지급분 보존을 회귀 검사.

## T2 — 환불 원자성·복구 (A02, A17)

Files: `payments/infrastructure/typeorm-payment-refunds.repository.ts`, `payments/application/payment-refund-execution.service.ts`, `payment-refund-recovery.scheduler.ts`, 관련 tests.
Interfaces: 부모 상태와 항목 claim을 같은 잠금으로 보호. voided/completed 상태 뒤늦은 overwrite 방지. processing 부모 아래 미선점 pending 자식 복구.
- [x] 사전조회 대기→철회→실행 반환에서 PG 호출0, 부모 종결 상태 유지 테스트.
- [x] 부모 선점 직후 중단→다음 worker 자동 완료 테스트.
- [x] 조건부 상태 전이/선점 순서를 최소 수정하고 기존 완료·부분 완료·실패/불확실 복구 검증.

## T3 — 구독 청구·복구 (A03–A05)

Files: `payments/infrastructure/typeorm-subscriptions.repository.ts`, `application/subscription-renewal.service.ts`, `payment-reconciliation.service.ts`, `payment-recovery.scheduler.ts`, `subscription-plan-changes.service.ts`, 필요 시 orders repository/domain, 관련 tests.
Interfaces: 환불 중 새 청구 불가. 이미 시작된 청구의 결과 조회는 유지. 업그레이드는 저장된 주문 snapshot으로 복구. 미결 갱신 청구가 취소/만료 뒤 성공해도 지급 또는 일관된 보상 완료.
- [x] 환불 중 past_due 자동/수동 재시도 PG 호출0 회귀.
- [x] upgrade 승인 응답 유실→webhook/운영자/스케줄러 복구, 추가 청구0·지급1 회귀.
- [x] due 이후 renewal claim→취소→만료→PG 성공 순서에서 paid 지급 성공 회귀.
- [x] 새로운 청구와 기존 청구 복구의 경계를 구분해 수정, 목적별 확정 로직 재사용.

## T4 — 회원·관리자 표시/비동기 (A10–A16)

Files: client `credits.component.html`, `dashboard.component.ts/html/spec.ts`, `promotions.component.ts/spec.ts`; admin `members/detail/member-detail.component.ts/spec.ts`.
Interfaces: 외부 API 변화 없이 실제 expiresAt/current access/payment method permission 사용. admin 최신 dev에는 이전 ae9b15d가 없으므로 pending 포함 유효 이용권 우선 규칙 전체를 구현.
- [x] 잘못된 만료일·카드 변경 숨김·취소 예약 상품·결제 재시도 후 잔액 미갱신·응답 역전·등급 지연·캠페인명 노출의 실패 테스트.
- [x] 날짜/selector/projection 재사용 및 최신 응답 보호로 수정.
- [x] 회원/관리자 집중 ChromeHeadless, 빌드 검증.

## T5 — 통합 검증·리뷰·기록

- [x] T1–T4 diff 검토, 실제 DB 재현 시나리오를 수정본에 재실행.
- [x] API 전체 Jest와 빌드, client/admin 전체 테스트 및 빌드(기존 실패가 있으면 원인 분리), DB 통합 회귀.
- [x] 독립 코드 리뷰에서 발견된 중요한 회귀를 수정 후 관련 테스트 실행.
- [x] `.codex` 완료 보고·WORKBOARD 업데이트, 격리 DB 종료, 원본 작업 상태 보존 확인.

## 진행 기록

- 시작 기준: API db0ca36, client fbd4573, admin 090d4e7. 감사 당시 API 전체 4471, client 관련102, admin 관련131 통과.
- Ruling: 미측정 성과 조회 대량 성능 및 로컬 저장 완료 신뢰 정책은 확정 결함17건과 분리한 기존 기록을 유지한다. 이번 수정에 임의 과금 정책 변경은 포함하지 않는다.

- 완료: A01–A17 및 독립 리뷰 R1/R2 수정·검증 완료. API 전체 4,490, 실제 PG 48, 회원 513, 관리자 2,393 통과; 세 빌드 통과. 원본 유지·임시 DB 종료·미커밋 상태. [완료 근거](2026-10-23-billing-promotion-audit-fixes-result.md).

- 2026-10-26: 후속 사용자 요청으로 수정 브랜치 커밋·푸시 및 원격 dev 병합 완료. API 2ac17a9, 회원 90f17e3, 관리자 4e2fbe6; 관리자 ae9b15d도 포함. [병합 근거](2026-10-26-billing-promotion-audit-dev-merge.md).
