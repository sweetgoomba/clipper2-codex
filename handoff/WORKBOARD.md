# 작업 현황판

최종 확인: **2026-09-15 KST**. 이 문서는 여러 세션에 걸친 작업의 **현재 상태와 재개 위치**를 찾는 시작점이다. 행 순서는 우선순위가 아니다. 사용자 선택 없이 마지막 작업을 전체 프로젝트의 다음 작업으로 지정하지 않는다.

## 작업 목록

| ID | 작업 | 상태 | 다음 행동 / 상세 인계 |
|---|---|---|---|
| W01 | 대사 하이라이트 개선 | 감사·5worktree 준비 이후 | [최신dev 대조 후 개선 범위 결정](tasks/dialog-highlight.md) |
| W02 | 밈 오버레이·seek | 사용자 작업 보존 | [기존 수정·추가요구 확인](tasks/meme-overlay.md) |
| W03 | 카드사 심사·임시 운영 | 심사 결과 대기 | [결과 후 기존운영 복원 또는 integration 배포](tasks/pg-card-review.md) |
| W04 | 운영·dev 통합 | 커밋·푸시 완료, 통합검증 대기 | [검증 후 main/배포 판단](tasks/integration.md) |
| W05 | CPU·리소스 안전성 | 구현·원격보존 완료, 실기 HOLD | [Windows/Build7 증거·SDK조건 확인](tasks/resource-safety.md) |
| W06 | 정식PG·운영 구축 잔여 | 기록상 미완료, 최신성 확인 | [환불/구독/웹훅·runner/운영 항목 선택](tasks/pg-production-followups.md) |
| W07 | 스토리보드 후속 | 8월기록, 재확인 필요 | [TODO와 최신코드 대조](tasks/storyboard.md) |
| W08 | 기타 장기보류 후보 | 재평가 대상 | [첫실행UX·stdout·보안·쇼츠분석 등](tasks/historical-backlog.md) |

## 공통 작업 공간과 보존

- 사용자 PC 원본8repo(`desktop/*`4, `web/*`4)는 dev. 당일 fetch/전환 후 clean, 로컬API·설치형앱 정상은 사용자보고.
- integration/main-unification-20260911은 8repo 원격보존. recovery/resource-safety-20260915는4repo 원격보존. 두 작업의 중복worktree 제거 완료.
- 활성 보존worktree는 대사하이라이트5개와 밈Angular1개. 이번조사에서는 변경하지 않았다.
- 옛feature/toss-payments-pg-integration, fix/operator-jwt-expiry-test 등 보존branch는 현재할일로 자동승격하지 않는다.
- 원격 상태는 당일 fetch·push확인 및 로컬원격참조 기준. 이번 문서감사에서 서버/Git원격을 재조회하지 않았다.
- 앱정리와 별개로 `.codex` 문서변경은 아직 미커밋일 수 있다. 세션 마무리에서 git status 확인.

## 상태를 읽는 법

- **대기:** 다음 행동은 있지만 사용자 선택/외부 결과를 기다림.
- **HOLD:** 명시적으로 보류. 자동재개 금지.
- **재확인 필요:** 과거 TODO의 최신 유효성 미검증. 미구현이라고 단정하지 않음.
- **보존 완료:** 코드가 남아 있다는 의미. 배포/기능검증 완료와 다름.

## 매 세션의 규칙

1. 이 현황판에서 사용자 요청에 해당하는 작업카드만 우선 읽는다.
2. 실제 branch/HEAD/미커밋과 카드 날짜를 확인한다. 서버실행SHA는 로컬Git으로 추정하지 않는다.
3. 작업 범위·제약을 유지한다. 서버는 사용자가 실행하고 에이전트는 안내만 한다. 실제ML/Build5 HOLD 유지.
4. 새 작업은 재개할 필요가 있을 때만 카드/행을 추가한다. 소규모 변경마다 별도관리체계를 늘리지 않는다.
5. 종료 시 해당카드의 상태/다음행동/검증한계 및 이 표를 함께 갱신한다. [카드양식](tasks/TEMPLATE.md)을 사용한다.
6. 실행명령·결과는 날짜별 session/implementation 기록에 남긴다. 현재카드에 오래된 상태를 계속 덧붙여 충돌시키지 않는다.
7. 다른 작업의 우선순위를 바꾸거나 과거미완료를 자동완료 처리하지 않는다. 커밋·푸시는 사용자 승인 범위에서만 한다.

## 이번 조사 범위

NEXT 원문, todos5개, PG TASKS, 9/4대사감사, 밈인계/seek기록, 9/15통합·복구·운영전환과 해당worktree Git을 확인했다. 소스기능 전체검증은 하지 않았다. [이번 세션 인계](../records/sessions/2026/09/15.md) 참조.
