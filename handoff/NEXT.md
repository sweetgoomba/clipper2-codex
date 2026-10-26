# 다음 세션 시작 안내

**2026-10-23 안무 메인 전용·완료 지연 원격 dev 반영:** Python `ea27940`, Nest `0fe9f8b0`를 dev·작업 브랜치에 atomic push했고 원본 두 저장소 dev·clean·0/0이다. 안무 주변 얼굴 보충/단체 자동 멤버 배정을 제거하고 메인 얼굴 근거를 요구한다. 저장 병합·완료 복구·UI 준비 상태·취소/progress 경합을 보완했다. 관련 Python507·Nest전체4,941 통과. Python 전체의 렌더5개 실패는 기존 dev에서도 재현돼 남겨두었다. 후속 사용자 요청으로 기본 dist-app의 ARM64 앱을 다시 빌드·실행했다. 기존 완료 결과는 유지하며 새 분석에 정책이 적용된다. [원인·정책·회귀·빌드·검증 한계](../features/highlights/records/2026/10/23-dance-main-only-and-completion-delay.md).

**2026-10-23 인물 이동 모달80px 원격 dev 반영 완료:** Angular `af8fe16e`을 dev·`fix/person-move-picker-spacing-20261023`에 커밋·atomic push했다. 썸네일80×80px·이름/장면 수 간격2px, 원본 Angular dev·clean·0/0 확인. 전체9,647(seed20261023)·스타일14 통과, 최초 템플릿 간헐 실패는 단독193·전체 재검사 통과 이력과 함께 기록했다. 앞서 실행한 별도 ARM64 앱에도 같은 수정이 포함됐다. [후속 기록](../features/highlights/records/2026/10/23-highlight-result-usability-followup.md).

**2026-10-23 카드 정렬·이동 모달 dev 반영 완료:** Angular `7c06eade`를 원격 dev와 `fix/dance-result-card-alignment-20261023`에 반영했다. 안무 카드 텍스트·hover 아이콘 중앙 정렬, 인물 이동 아이콘 통일, 공통 얼굴 선택 모달·장면 수 표시를 포함한다. 전체9,619(seed20261023)·관련150·스타일14·화면 빌드 통과. 임의 순서의 템플릿/Store 간헐 실패 이력과 실제 앱 반영 범위는 [후속 기록](../features/highlights/records/2026/10/23-highlight-result-usability-followup.md)을 읽는다. 이후 사용자 요청으로 원본8개 최신 dev pull 및 로컬 API용 ARM64 앱 재빌드·실행을 완료하여 추가 모달 변경도 앱에 포함됐다. 당시 Angular `01b815f3`, Nest `df4d586f`, Python `11fbc9d`; 정확한8개 SHA·실행 범위는 같은 기록의 마지막 절을 읽는다.

**2026-10-23 결과 화면 후속 dev 반영 완료:** 안무·인물 결과 화면 사용성·100px 사진 품질·Windows hover 수정은 Angular `baf2f54d`, Python `3b3e203`으로 원격 dev에 반영했다. 원본 두 저장소도 dev·clean이다. Angular9,612+스타일14, Python 안무·공통 얼굴206, 병합 후 hover135 통과. [변경·빌드·병합 기록](../features/highlights/records/2026/10/23-highlight-result-usability-followup.md).

**2026-10-23 최종 통합:** 세 관련 세션을 재감사하고 빠져 있던 무대 파이프라인 작업도 원격 dev에 반영했다. Angular `975e16f6`, Electron `dfc84d4`, Nest `15f534b9`, Python `584d76b`; 작업 브랜치와 dev SHA가 모두 일치한다. Angular 8,330+스타일 14 / Electron 1,721 / Nest 4,258 / Python 1,512 통과·6 skip. 이전 Nest 종료 테스트 실패는 이번 재검증에서 해소됐다. [최종 통합·검증·한계](../features/highlights/records/2026/10/23-stage-person-integration-dev-merge-result.md)를 먼저 읽는다. 앱 재빌드·실영상·Windows 확인은 별도다.

**2026-10-23 무대 사용성 후속 완료:** [구현·검증·dev 반영 기록](../features/highlights/records/2026/10/23-stage-usability-source-ranges-dev-merge.md)을 먼저 읽는다. 원본 구간 저장, 편집·선택·숏폼 구성·묶음 드래그·미확인 얼굴 썸네일은 Angular `f488e8a4`, Nest `8397afbc`, Python `3fbb002`로 원격 dev에 충돌 없이 반영됐다. 다음 확인은 실제 영상에서 편집 범위와 출력 일치, 실제 카드 드롭, Windows 검증이다.

**2026-10-23 W14 최신:** 인물 하이라이트의 데스크톱 4개 저장소는 원격 `dev` 병합·푸시 완료다. 먼저 [병합 체크포인트·검증·인계](../features/highlights/records/2026/10/23-person-highlight-dev-merge-and-stage-usability-handoff.md), [W14 카드](tasks/person-highlight.md)를 읽는다. 병합 보류 지시는 후속 사용자 승인으로 해제됐다. 무대 사용성 후속은 위 기록처럼 구현·dev 반영을 완료했다. 무대 파이프라인 세션은 별도 정확도 개선을 이어간다. 추가 얼굴 모델 교체나 별도 병합을 이미 수행했다고 간주하지 않는다. Web API 과금·권한 후속도 `ba68b2b`로 원격 dev 반영 및 로컬 DB 확인을 완료했다([기록](../features/highlights/records/2026/10/23-person-highlight-web-api-billing-dev-merge.md)). 기존 로컬 미커밋 사본이 남아 있어도 원격 미반영으로 오해하지 않는다.

최신 갱신: **2026-10-23 KST (W14·W17)**. 아래 W13/W14·QA 설명은 별도 표기된 10/16 스냅샷이다.

**W17 프로모션:** Web API·관리자 웹·회원 웹의 프로모션 캠페인/복수 코드 후속 작업과 데스크톱 NestJS·Angular의 프로모션 출처 인식이 원격 `dev`에 병합됐다(API `0776268`, 관리자 `98e2e8c`, 회원 `fbd4573`, NestJS `b9602b2f`, Angular `1a839571`). 캠페인 공통 설정의 **코드별 등록 상한**, 회원당 캠페인 1회, 유료/관리자 지급 이력 선택, XLSX 성과와 회원 참여 내역이 현재 기준이다. 데스크톱 NestJS 전체 테스트는 별도 실패로 통과하지 못했고, 변경 경로 테스트와 빌드는 통과했다. 재개 시 [W17 카드](tasks/festival-voucher.md), [현행 설계](../design/2026-10-23-promotion-campaign-current-state.md), [병합 기록](../implementation/2026-10-23-promotion-campaign-dev-merge.md)을 먼저 읽는다. 운영 배포/DB 적용과 실제 Toss 결제망 검증은 완료로 취급하지 않는다.

**다음 주 범위:** [10/19~23 작업 초안](2026-10-16-next-week-scope-draft.md)을 먼저 본다. 사용자의 최신 방향은 기존 안무 플러그인의 **무대 하이라이트 전환**, 저동작 솔로 무대 지원, 별도 사용성 개선, **인물 하이라이트 플러그인 시연**, 대사 하이라이트 개선이다. 6번 배포·빌드·브랜치 전략과 앱/플러그인 버전 관리는 낮은 우선순위로 추가했다. 아래의 "Person MVP 보류"는 10/16 당시 상태이며 다음 주 제품 개발을 보류하라는 뜻이 아니다.

**10/16 재개 안내(이력):** 당시에는 안무·인물 하이라이트 재개 전에 [작업 현황판의 10/16 요약](WORKBOARD.md), [고정 스레드 1~5·7~9 / 8개 저장소 dev 감사](2026-10-16-pinned-thread-dev-reconciliation.md), [W13 노트북 71개·W14 얼굴 평가 회고](../features/highlights/records/2026/10/16-w13-w14-experiment-reconciliation.md)를 먼저 읽도록 안내했다. 사용자 보고상 대표님께 전달한 새 빌드의 SHA·영상/참조 입력을 고정하고, W13 메인/군무/컷과 W14 얼굴 신원/구간을 분리해 현재 dev와 비교한다. 72번 노트북은 제품 미채택, Person MVP는 보류, 통합 시험 tree의 수동 클립 수정·긴 구간 분할은 dev 미반영 미커밋이다. 코드 수정 전에 해당 저장소의 원격 `dev`를 다시 fetch한다. 10/16 대조 당시 Angular·Web API·Admin·Client·Infra 기본 checkout은 원격보다 뒤에 있었다.

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
