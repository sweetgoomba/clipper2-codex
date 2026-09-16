# 작업 현황판

최종 확인: **2026-09-17 KST**. 이 문서는 여러 세션에 걸친 작업의 **현재 상태와 재개 위치**를 찾는 시작점이다. 행 순서는 우선순위가 아니다. 사용자 선택 없이 마지막 작업을 전체 프로젝트의 다음 작업으로 지정하지 않는다.

## 작업 목록

| ID | 작업 | 상태 | 다음 행동 / 상세 인계 |
|---|---|---|---|
| W01 | 대사 하이라이트 개선 | 감사·5worktree 준비 이후 | [최신dev 대조 후 개선 범위 결정](tasks/dialog-highlight.md) |
| W02 | 밈 오버레이·seek | 사용자 작업 보존 | [기존 수정·추가요구 확인](tasks/meme-overlay.md) |
| W03 | 카드사 심사·임시 운영 | 심사 결과 대기 | [결과 후 기존운영 복원 또는 integration 배포](tasks/pg-card-review.md) |
| W04 | 운영·dev 통합 | 원본8repo dev 최신·clean. 통합8repo push 완료·원격 SHA 일치·clean. 설치형 실기 남음 | [최신 Git 결과](../implementation/2026-09-17-integration-commit-proposal.md) · [상세 인계](tasks/integration.md) |
| W05 | CPU·리소스 안전성 | 구현·원격보존 완료, 실기 HOLD | [Windows/Build7 증거·SDK조건 확인](tasks/resource-safety.md) |
| W06 | 정식PG·운영 구축 잔여 | 기록상 미완료, 최신성 확인 | [환불/구독/웹훅·runner/운영 항목 선택](tasks/pg-production-followups.md) |
| W07 | 스토리보드 후속 | 8월기록, 재확인 필요 | [TODO와 최신코드 대조](tasks/storyboard.md) |
| W08 | 기타 장기보류 후보 | 재평가 대상 | [첫실행UX·stdout·보안·쇼츠분석 등](tasks/historical-backlog.md) |
| W09 | 운영·개발 앱 표시 이름 | 이름·환경별 identity 보존. R06/R07 수정·회귀 통과·로컬 커밋. 실제 Google OAuth·Windows NSIS 실기 필요 | [상세 결과](tasks/app-window-name.md) |

## 공통 작업 공간과 보존

최신 push 상태는 위 W04와 최신 Git 결과를 따른다. 아래 커밋 시점의 “원본 유지/코드 push 없음”은 후속 사용자 승인 이전 기록이다. 문서 작성 위치는 사용자 지시에 따라 `.codex`로 한정하며 잘못 추가한 `clipper_docs` TODO는 이동 완료했다.

- 사용자 PC 원본8repo(`desktop/*`4, `web/*`4)는 dev와 clean. 사용자 명시 요청 후 Angular를 `98d449584055b324f223678f058e255c7d464c80`, Nest를 `4c32e03c327003e85ec5da248e362d4e85b49fb7`로 fast-forward pull했다. 원본8repo 모두 origin/dev와 0/0이다.
- integration/main-unification-20260911은 8repo 원격보존. recovery/resource-safety-20260915는4repo 원격보존. 두 작업의 중복worktree 제거 완료.
- 정식 PG 통합 결과는 `.worktrees/dev-pg-local-validation-20260917/`의 8개 저장소별 `integration/dev-pg-local-validation-20260917` branch에 있다. Astra R01–R13+A14 및 추가 환급 보완은 사용자 승인 후 Angular `dba50096`, Electron `6766c06`, Nest `fda1eda`, Web API `8b074a5`로 로컬 커밋했다. fresh 빌드·테스트 통과, 통합8repo clean이며 원본8repo는 기존 dev HEAD 그대로 clean이다. 설치형 실기·잔여 위험 검증 전 전체 로컬 완료로 판정하지 않는다. 옛 feature/PG 보완 및 다른 작업 worktree의 변경은 보존한다. 이번 추가 병합·코드 push·원본 dev 갱신·배포는 없다. `.codex`는 별도 사용자 요청으로 커밋·푸시한다.
- 옛feature/toss-payments-pg-integration, fix/operator-jwt-expiry-test 등 보존branch는 현재할일로 자동승격하지 않는다.
- 원격 상태는 2026-09-17 Astra 감사에서 8repo `git ls-remote`로 dev/integration 참조를 재확인했고 로컬 origin 참조와 같았다. fetch/branch 이동 없이 통합 HEAD가 모두 포함함을 확인했다. 배포 서버 상태는 재조회하지 않았다.
- 앱정리와 별개로 `.codex` 문서변경은 아직 미커밋일 수 있다. 세션 마무리에서 git status 확인.
- 정식 PG 통합용 8repo worktree는 `.worktrees/dev-pg-local-validation-20260917/`이며 각 branch는 `integration/dev-pg-local-validation-20260917`이다. 원본 checkout은 그대로다. 현재 HEAD, 전체 테스트·빌드, 별도 로컬 DB migration, API/Web/macOS 앱 smoke와 한계는 [2026-09-17 최종 로컬 검증 결과](../implementation/2026-09-17-local-pg-integration-validation-result.md)에 기록했다.

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

## 이번 W04 검증 범위

최신 판정은 [취소·삭제 환급 및 Dialog 수정 결과](../implementation/2026-09-17-archive-refund-fix-result.md)다. 사용자 승인 후 삭제 전 확정 가능한 환급 의도/outbox를 보존하고, 옛 params의 attempt ID fallback을 제거해 정확한 owner+job만 사용한다. Dialog는 제품 기본 1초 제한을 유지하고 HTTP 요청/timeout 테스트를 분리했다. 최종 Nest 전체 2,678/2,678, 대상 70/70, Dialog 새 프로세스 20회×11건, 격리 부팅 PASS. 독립 재리뷰 잔여 지적 없음. 다음은 수정본 설치형 로컬 실기이며 Google/Windows는 사용자 실행, ML/Build5 HOLD다. 기존 4repo 미커밋 변경·8repo HEAD·원본 checkout은 보존했다. 새 커밋·push·배포·실제 DB 변경은 없으며 DB 리허설로 자동 진행하지 않는다.

이전 세션은 8repo 통합, 전체/대상 테스트·빌드, 별도 로컬 User/Admin/Release migration, 과거 schema fixture, migration 누락-table guard, dump restore, 로컬 API 정책, Web Client 브라우저, macOS 개발 설치형 앱을 확인했다. 이는 실행한 시나리오의 증거이며 이번 결함을 부정하지 않는다. Windows NSIS, 실제 ML, Build 5 전체 QA, 실제 Toss 결제, 개발 DB 복제본·실제 개발서버 전환은 수행하지 않았다. [이전 로컬 검증 기록](../implementation/2026-09-17-local-pg-integration-validation-result.md) 참조.
