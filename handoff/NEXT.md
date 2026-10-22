# 다음 세션 시작 안내

최신 갱신: **2026-10-23 KST (W17)**. 아래 W13/W14·QA 설명은 별도 표기된 10/16 스냅샷이다.

**W17 프로모션:** Web API·관리자 웹·회원 웹의 프로모션 캠페인/복수 코드 후속 작업과 데스크톱 NestJS·Angular의 프로모션 출처 인식이 원격 `dev`에 병합됐다(API `0776268`, 관리자 `98e2e8c`, 회원 `fbd4573`, NestJS `b9602b2f`, Angular `1a839571`). 캠페인 공통 설정의 **코드별 등록 상한**, 회원당 캠페인 1회, 유료/관리자 지급 이력 선택, XLSX 성과와 회원 참여 내역이 현재 기준이다. 데스크톱 NestJS 전체 테스트는 별도 실패로 통과하지 못했고, 변경 경로 테스트와 빌드는 통과했다. 재개 시 [W17 카드](tasks/festival-voucher.md), [현행 설계](../design/2026-10-23-promotion-campaign-current-state.md), [병합 기록](../implementation/2026-10-23-promotion-campaign-dev-merge.md)을 먼저 읽는다. 운영 배포/DB 적용과 실제 Toss 결제망 검증은 완료로 취급하지 않는다.

**다음 주 범위:** [10/19~23 작업 초안](2026-10-16-next-week-scope-draft.md)을 먼저 본다. 사용자의 최신 방향은 기존 안무 플러그인의 **무대 하이라이트 전환**, 저동작 솔로 무대 지원, 별도 사용성 개선, **인물 하이라이트 플러그인 시연**, 대사 하이라이트 개선이다. 6번 배포·빌드·브랜치 전략과 앱/플러그인 버전 관리는 낮은 우선순위로 추가했다. 아래의 "Person MVP 보류"는 10/16 당시 상태이며 다음 주 제품 개발을 보류하라는 뜻이 아니다.

안무·인물 하이라이트를 이어갈 때는 [작업 현황판의 10/16 최신 요약](WORKBOARD.md), [고정 스레드 1~5·7~9 / 8개 저장소 dev 감사](2026-10-16-pinned-thread-dev-reconciliation.md), [W13 노트북 71개·W14 얼굴 평가 회고](../features/highlights/records/2026/10/16-w13-w14-experiment-reconciliation.md)를 먼저 읽는다. 사용자 보고상 대표님께 전달한 새 빌드의 SHA·영상/참조 입력을 고정하고, W13 메인/군무/컷과 W14 얼굴 신원/구간을 분리해 현재 dev와 비교한다. 72번 노트북은 제품 미채택, Person MVP는 보류, 통합 시험 tree의 수동 클립 수정·긴 구간 분할은 dev 미반영 미커밋이다. 코드 수정 전에 해당 저장소의 원격 `dev`를 다시 fetch한다. 10/16 대조 당시 Angular·Web API·Admin·Client·Infra 기본 checkout은 원격보다 뒤에 있었다.

QA/W06은 [W16](tasks/payment-qa-bugs.md)·[W06](tasks/pg-production-followups.md)의 10/16 상단 갱신을 우선한다. 아래 9/29 지침의 “새 MID 발급만 됨”, “8repo dev clean”, “하이라이트 전체 조사부터 시작”은 지금의 상태가 아니다.

## 9/29 당시 시작 안내 (이력)

1. [작업 현황판](WORKBOARD.md)에서 사용자가 선택한 작업을 확인한다. [새 세션 시작 프롬프트](prompts/2026-09-29-new-sessions.md)에 5개 세션의 시작 문구가 있다.
2. 해당 작업카드와 필요한 repo 규칙을 읽는다. [9/29 인계](../records/sessions/2026/09/29.md)에 이번 대화의 결정·완료 사항·검증 한계가 있다.
3. 원본8repo는 이번 조회 기준 dev·clean·로컬 origin/dev와 0/0. 재개 시 실제 상태를 다시 읽고, 코드 수정 전에 필요한 repo의 최신 origin/dev에서 새 브랜치·격리 작업 폴더를 만든다.
4. `dev-merge-0.0.36`, `storyboard-ux-overhaul-20260920` 폴더는 삭제됐다. 브랜치는 보존됐다. 과거 문서의 해당 폴더를 재사용하지 않는다.
5. PG는 심사 완료·새 MID 2개·테스트/라이브 키 발급 사용자 보고 단계다. 우선 MID/키/기존 결제·billingKey·DB 영향과 전환안을 설명한다. 실결제·환불은 구체적 대상/금액 확인 뒤, 서버는 사용자 실행 방식으로 진행한다.
6. 하이라이트는 전체 조사 세션에서 공통 구조·변경 이력·측정 계획을 정리하고 안무/인물/대사 세 세션의 인계 프롬프트를 만든다. 출력이 미정인 인물 플러그인을 확정 구현처럼 다루지 않는다.
7. 기존 HOLD는 해당 세션의 새로운 사용자 지시와 대조한다. 과거 단위테스트 PASS를 실제 ML/PG/운영 배포 완료로 재사용하지 않는다.
8. 종료 시 해당 작업카드·보드·세션 기록을 갱신한다. 요청 없는 commit/push·새 작업 세션 생성은 하지 않는다.

## 바로 이동

- [공통 버그·문구·기획 보정](tasks/app-bugfix.md)
- [TossPayments 새 MID·키 전환](tasks/pg-production-followups.md)
- [스토리보드 후속 개선](tasks/storyboard.md)
- [홈·보관함·큐](tasks/home-archive.md)
- [하이라이트 전체 조사](tasks/highlight-overview.md)
- [ICP TC4 기존 로그 활용](tasks/icp-tc4.md)

[과거 NEXT 원문](archive/2026/09/next-through-2026-09-18.md) · [9/18 PG 통합 종료 감사](../implementation/2026-09-18-pg-integration-closeout-and-remaining-work.md).
