# 결제와 PG 작업

## 2026-11-10 외부 취소 장애와 결제 운영 및 구독 정책

[이번 세션 전체 기록](records/2026/11/10-payment-operations-subscriptions-session-summary.md)에 운영 장애 원인·웹훅 라이브 시험, 관리자 목록과 공통 우측 패널, 마이페이지 A안, 최초 실패·유예 해지 정책, Docker와 로컬 도구, 두 차례 독립 검증·보완, 병합·커밋·푸시를 정리했다.

이번 세션은 integration/payment-operations-20261109의 API 3fda70f·관리자 2a65cf7·사용자 웹 a32f8ef를 원격에 게시했다. 이후 다른 세션의 후속 dev 반영으로 문서화 시점의 원격 dev에도 이 커밋들이 포함돼 있음을 확인했다. 이 세션에서 서버 배포를 수행한 것은 아니다. 시점별 SHA·검증 수치·남은 운영 확인과 [보고서 원본 경로 및 해시](records/2026/11/10-payment-operations-evidence/index.json)는 종합 기록을 따른다.

## 2026-11-04 이전 통합 기준

11월 4일 당시 두 세션의 인계 기준은 [고객 환불과 PG 작업 통합 정리](records/2026/11/04-two-session-pgops-summary.md)다. 고객 환불의 관리자 승인, 외부 취소 자동 후처리, 운영 화면, 앱 정산 복구, 가격·크레딧과 무료체험 **365일 상한**까지 서비스 기능은 dev에 반영됐다.

11월 4일 당시 실제 Toss 전체 E2E, 조건부 DB 테스트 86개, 운영 배포·문구 확정은 남아 있었다. 당시 API3311과 웹4203/4204는 정지 상태였고 새 API 빌드가 준비돼 있었다.

## dev 반영 전 필수 독립 검증

이 PG 작업은 정확한 커밋·tree의 테스트·빌드 후 별도 컨텍스트의 검증 세션 또는 에이전트에 검토를 맡긴다. 결과를 받아 P0/P1/P2를 보완·재검토한 뒤 최신 원격과 tree 일치를 확인하고 dev에 반영한다. Astra를 사용하지 않는 사용자 선택을 유지한다. [절차와 이번 적용 결과](records/2026/11/04-customer-refunds-default-and-pre-dev-review.md).

고객 환불은 플래그 설정 없이 기본 제공하며 관리자 승인 절차를 유지한다. 이전 활성화 설정 안내는 과거 기록이다.

## 2026-11-04 상태와 근거

- [두 세션 전체 변경과 다음 작업](records/2026/11/04-two-session-pgops-summary.md)
- [커밋·테스트·실앱 복구·서버 종료의 보존 증거](records/2026/11/04-two-session-pgops-evidence.json)
- [최종 미병합 감사와 웹서버 정리](records/2026/11/04-final-pgops-status-and-web-cleanup.md)
- [외부 취소 설계](records/2026/11/04-external-cancellation-effects-design.md) · [구현·검증](records/2026/11/04-external-cancellation-effects-verification.md)
- [가격·크레딧·유효기간 편집](records/2026/11/04-catalog-price-trial-validity-integration.md)
- [최종 유효기간 365일 상한](records/2026/11/04-trial-validity-365-limit.md)

## 프로모션 세션의 이전 PG 기록

아래는 2026-11-03 프로모션 세션의 범위다. 당시 ‘100원 문제는 다른 세션 담당’이라는 설명을 현재 PG 작업의 미완료로 해석하지 않는다. 위 통합 문서에 이후 구현·병합 결과가 있다.

[2026-11-03 이번 세션의 결제 구현·조사·문의문 분리 정리](records/2026/11/03-session-pg-discussions-and-changes.md).

추가 크레딧 승인 전 자격 검사 보완, 구독 차액의 빌링 MID, 업그레이드 계산/기간/크레딧과 기존 감사 수정 이력을 모았다. 구현·기존 정책 확인·외부 공식 조사·문의문 작성을 구분한다. 실제 토스망 결제나 해당 MID 계약 승인 완료로 확대하지 않는다.

**100원 최소 청구 때문에 즉시 업그레이드가 예약되는 문제는 다른 세션 담당으로 이번 작업·TODO·검증에서 제외한다.** 프로모션/Free/플러그인 등 전체 맥락은 [세션 종합](../../records/sessions/2026/11/03-promotion-signup-free-plugin-session-summary.md)을 따른다.
