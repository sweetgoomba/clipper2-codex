# 프로모션·가입 혜택·Free

[11/03 최종 배지·여섯 저장소 dev 반영 결과](../plugin-catalog/records/2026/11/03-store-plan-badges-dev-merge.md).

현재 기준: **2026-11-03 KST**. [세션 종합 정리](../../records/sessions/2026/11/03-promotion-signup-free-plugin-session-summary.md) · [W19 현재 작업카드](../../handoff/tasks/signup-promotion-plan-entitlements.md).

## 구현한 현재 출시 범위

Google 복귀 후 신규 가입 동의에서 선택 코드를 입력하고 최초 가입 혜택과 프로모션 크레딧을 별도 지급한다. 일반 크레딧/이용권 혜택과 신규/기존/모두 대상·선택 조건을 분리했다. 캠페인→복수 코드, 코드별 등록 인원 제한, 캠페인당 회원1회, 참여 내역/이메일 조회·남은 혜택 회수를 유지한다.

종료일 미정·날짜↔미정 수정·기간 단축, 생성 전 공통 확인창과 등록 후 수정/삭제 제한까지 구현·검증했다. 프로모션 유료 예약·레퍼럴 성과·XLSX는 현재 코드에서 제거했고 보존 브랜치에 남겼다. 일반 결제/환불/원본 크레딧 장부는 유지한다.

- [가입·Free 초기 구현·검증](records/2026/11/02-ai-booth-signup-free-implementation-and-verification.md)
- [혜택/참여 조건·월별 만료](records/2026/11/02-campaign-eligibility-implementation-and-verification.md)
- [생성 확인·수정 가능/불가](records/2026/11/02-campaign-create-confirmation-and-edit-rules.md)
- [종료일·인원 제한·확인 표 최종 스타일](records/2026/11/02-campaign-deadline-and-summary-colors.md)
- [종료일 미정 추가/수정 검증](records/2026/11/02-open-ended-campaign-edit-regression-check.md)

## 분리한 관련 작업

Free 지속 상태·가입 혜택1회·요금제별 플러그인 실행 검사·제안F 공통4카드와 관리자 일괄 설정은 W19에 구현했다. [플러그인·요금제 현황](../plugin-catalog/README.md)을 따른다. 현재 기능은 작업 브랜치 커밋·푸시·원격 dev 통합 완료이며, 과거10/28~29 및 목업 단계의 ‘미구현’ 기록은 당시 상태다.

[PG/결제 논의와 실제 보완](../payments/records/2026/11/03-session-pg-discussions-and-changes.md)을 프로모션 범위와 구분한다. **100원 최소 청구 업그레이드 문제는 다른 세션 담당으로 이번 구현·TODO·검증에서 제외한다.**

앱/웹 전체 플러그인 목록 동기화·분류·공개·전역 중지는 [W18 후속 TODO](../../handoff/tasks/plugin-catalog-sync.md)다. 이를 이미 구현한 허용 설정/가격 카드와 혼동하지 않는다. [초기 스토어 UX 사례 조사](records/2026/10/29-store-plan-badges-and-final-action-ux-research.md)와 [추가 참여 조건 후보](records/2026/11/02-campaign-eligibility-followup-candidates.md)는 참고자료이며 자동 착수할 목록이 아니다.
