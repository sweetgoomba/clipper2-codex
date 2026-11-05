# 결제와 PG 작업

두 세션의 현재 인계 기준은 [고객 환불과 PG 작업 통합 정리](records/2026/11/04-two-session-pgops-summary.md)다. 고객 환불의 관리자 승인, 외부 취소 자동 후처리, 운영 화면, 앱 정산 복구, 가격·크레딧과 무료체험 **365일 상한**까지 서비스 기능은 dev에 반영됐다.

실제 Toss 전체 E2E, 최근 조건부 DB 테스트 86개, 운영 배포·문구 확정은 남아 있다. API3311과 웹4203/4204는 현재 정지 상태이며 새 API 빌드는 준비됐다.

## dev 반영 전 필수 독립 검증

이 PG 작업은 정확한 커밋·tree의 테스트·빌드 후 별도 컨텍스트의 검증 세션 또는 에이전트에 검토를 맡긴다. 결과를 받아 P0/P1/P2를 보완·재검토한 뒤 최신 원격과 tree 일치를 확인하고 dev에 반영한다. Astra를 사용하지 않는 사용자 선택을 유지한다. [절차와 이번 적용 결과](records/2026/11/04-customer-refunds-default-and-pre-dev-review.md).

고객 환불은 플래그 설정 없이 기본 제공하며 관리자 승인 절차를 유지한다. 이전 활성화 설정 안내는 과거 기록이다.

## 현재 상태와 근거

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
