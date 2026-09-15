# 운영·dev 통합 및 main 반영

최종 확인: 2026-09-15 KST. 상태: **커밋·푸시 완료 / 통합 검증 대기**.

[전체 작업 현황](../WORKBOARD.md)

## 현재 상태

8repo `integration/main-unification-20260911` 원격보존. 7개 merge commit, Client는 추가dev변경0. [정확한 SHA·조합 결과](../../implementation/2026-09-15-main-integration-result.md), [병합 기준](../../implementation/2026-09-15-main-integration-plan-update.md).

중복 integration worktree는 제거했다. 사용자 PC의 원본8repo는 후속 요청으로 다시 최신dev로 전환됐다. 통합 결과는 branch에 남아 있으며 현재 원본 소스와 동일하지 않다. main에는 반영하지 않았다.

## 다음 행동

재개 시 branch/remote 이동을 확인하고 통합판을 사용할 작업 공간부터 결정한다. Angular 크레딧확인+전체선택/삭제, Electron identity+키검사/종료, API/Admin 계약·migration, Nest 디스크정리+리소스소유권의 조합을 검증한다. dev로 실행한 로컬 앱 정상보고나 카드사 심사판 검증은 통합판 검증이 아니다.

그다음 main반영/배포 여부 결정. 서버 배포는 사용자 실행. 실제ML/Build5 HOLD 유지. 테스트·빌드·배포 재개 범위는 그때 사용자 지시를 확인한다.

## 제외한 과거 작업

사용자 결정대로 오래된 main 고유코드, 별도 feature/toss-payments-pg-integration, 밈·대사하이라이트 branch를 추가병합하지 않았다. 이를 자동 복원하거나 새 통합 범위로 넣지 않는다.

## 갱신 규칙

작업 재개 시 실제 branch/HEAD/미커밋과 아래 근거를 대조한다. 세션 종료 때 상태·중단 지점·다음 행동·검증 한계만 갱신하고, 세부 실행 이력은 날짜별 기록에 링크한다. 다른 작업의 우선순위나 상태를 자동 변경하지 않는다.
