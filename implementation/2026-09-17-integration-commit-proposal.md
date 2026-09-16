# 통합 수정 커밋·작업 공간 정리안

2026-09-17 KST. 사용자 요청: 실기 검증 전에 Git 상태 정리, `.codex`도 커밋·푸시. **명시적으로 요청한 `.codex` 커밋·푸시와 코드 저장소 커밋 제안을 구분한다.** 원본 dev 갱신·코드 push·추가 병합은 실행하지 않는다.

## 현재 확인

8repo `git ls-remote --heads origin dev`를 재확인했고 로컬 origin/dev와 동일했다. 원본8repo 모두 clean. Angular 원본 `019687d9`는 원격 `98d44958`보다 44커밋, Nest 원본 `e99b3962`는 원격 `4c32e03c`보다 17커밋 뒤다. 다른6repo는 일치한다. 통합8repo는 이 원격 dev를 이미 모두 포함하므로 원본 checkout의 behind가 통합 누락을 의미하지 않는다.

코드 작업 공간: `.worktrees/dev-pg-local-validation-20260917/`, 공통 branch `integration/dev-pg-local-validation-20260917`.

## 실행 결과: 사용자 승인 후 4개 로컬 커밋 완료

사용자는 코드4repo 로컬 커밋안에 “응”으로 승인했다. 아래 범위 그대로 fresh 빌드·테스트 후 커밋했으며 코드 push·원본 dev 갱신·추가 병합은 하지 않았다.

| 저장소 | 새 HEAD | fresh 검증 |
|---|---|---|
| Angular | `dba50096dd86fb591f2d26af1132f6de2cca52e4` | devapp build, 관련 8 spec 226/226 PASS |
| Electron | `6766c0645d8151eac1ea075e08f89871cb4ad4df` | build, 전체 955/955 PASS |
| Nest | `fda1eda586fe2b80a444691303fb1e52fef57a34` | build, 전체 2,678/2,678 PASS |
| Web API | `8b074a59a454b47323f9e490d9bfd8d6c2a51ec5` | build, 259 suites / 2,802 tests PASS; 기존 5 suites / 21 tests SKIP |

로그: `/private/tmp/pg-commit-angular-node24.log`, `/private/tmp/pg-commit-electron.log`, `/private/tmp/pg-commit-nest.log`, `/private/tmp/pg-commit-api.log`. Angular 첫 시도는 셸의 Node 24.3.0이 CLI 최소 버전 미달로 종료했다(`/private/tmp/pg-commit-angular.log`). 설치된 Node 24.19.0을 명령 PATH에만 지정해 통과했으며 소스·의존성 변경은 없다. Angular는 `CI=true`로 캐시를 사용하지 않았고 `ChromeHeadlessNoSandbox`에서 app.config/app.component/operation-recovery/operation-billing/job-history/local-api-auth/account-summary/projects spec과 test-setup을 실행했다.

명시한 57파일만 stage했고 unstaged/staged `diff --check` 통과. 커밋 후 통합8repo 모두 clean, 원본8repo는 기존 dev HEAD 그대로 clean임을 재확인했다. 옛 PG 보완 worktree의 미커밋 변경은 건드리지 않았다. 설치형 새 수정본의 UI·Google OAuth·Windows 실기는 미완료다.

`.codex`의 직전 문서21파일은 `3f4ac3c7553bc71d70ce0a5d166567cd1899d07e`로 커밋·push 완료했다. 이번 커밋 결과·인계 갱신은 별도 문서 커밋으로 기존 origin/main에 일반 push하고 원격 SHA를 확인한다. 원격 전진 시 임의 병합/force push하지 않는다.

## 승인된 제안 원문: 저장소별 1개 커밋, 총 4개

서로 의존하는 과금 coordinator·job 상태·outbox·UI 회귀를 잘게 나눠 불완전한 중간 상태를 만들지 않고, 저장소마다 수정과 대응 테스트를 같이 보존한다. 커밋 직전 파일 목록·diff·검증을 다시 확인한다.

| 저장소 | 기존 HEAD | 파일 수 | 커밋 범위 | 제안 메시지 |
|---|---|---:|---|---|
| Angular | `ac879329` | 9 (기존7+신규2) | 로그인/온라인 과금 복구 연결, Shortform 재시도 preflight, 서버 종결 후 잔액 갱신·계정 응답 격리 및 specs | `fix(billing): recover pending operations and refresh account state` |
| Electron | `827fcda` | 4 | Nest spawn/종료 시 PID identity 확보, owned-child 검증 계약 및 회귀 | `fix(runtime): preserve owned process identities through shutdown` |
| Nest | `f452b6f` | 40 (기존33+신규7) | R02–R05/R07/R09–R13의 복구·차감·preflight·재시도 출력 격리, Variation 최초/재시도 영속 연결, 삭제 전 환급 보존, 관련 regression 및 Dialog 테스트 안정화 | `fix(billing): make job recovery and cancellation refunds durable` |
| Web API | `7392147` | 4 (기존3+신규1) | operation transaction의 같은 manager로 policy 조회, 제한 pool 회귀 | `fix(operations): reuse transaction manager for policy lookup` |

기존 검증 증거는 [최신 Nest 결과](2026-09-17-archive-refund-fix-result.md), [Astra 전체 수정 결과](2026-09-17-astra-fix-result.md)에 있다. 새 코드 커밋 직전에는 각 범위에 맞는 fresh 검증을 실행한다. 설치형 실기 미완료는 커밋 보존과 별개이며 완료로 기록하지 않는다.

## `.codex` 커밋·푸시 (이번 사용자 명시 요청)

- `.codex`는 별도 Git 저장소, 현재 main. 기존 HEAD와 origin/main은 `139e3d4766f6d598647bb853cc43d390dc9fd2e9`로 일치했다.
- remote: 기존 origin `git@github.com-personal:sweetgoomba/clipper2-codex.git`.
- 범위: 이번 PG/앱 이름 통합 설계·병합 이력·Astra 진단/수정/검증·인계·9/16~17 세션 기록과 진단 스크립트, 이 정리안. 기존 변경20파일 + 신규 정리안1파일.
- 과거 문서의 “현재 정본/완료/승인 대기” 표현에 최신 결과 링크와 역사 기록 표시를 추가한다. 과거 실행 증거 자체는 삭제하지 않는다.
- 제안 메시지: `docs(handoff): preserve PG integration audits and commit plan`.
- 명시적 파일 목록만 stage하고 diff/민감정보 패턴/진단 스크립트 구문을 확인한 뒤 커밋한다. push는 origin main에 일반 push만 사용한다. 원격이 전진해 거절하면 force/merge/rebase 없이 멈춰 보고한다.
- 커밋 SHA·원격 일치·clean 여부는 실제 실행 뒤 Git으로 확인해 사용자에게 보고한다. 문서 push는 코드 push나 배포가 아니다.

## 이번에 건드리지 않을 것

- 원본 Angular/Nest dev: fast-forward도 사용자에게 범위·영향을 설명하고 별도 승인 후 수행한다. 이번 코드 커밋 승인에 포함시키지 않는다.
- `.worktrees/pg-contract-render-refund-20260916/`: Nest7파일, Web API OpenAPI1파일의 옛 미커밋 변경은 보존. 통합본과의 중복·사용 중 여부 확인 전 커밋/삭제/덮어쓰기하지 않는다.
- 다른 기능 worktree 및 디스크에 없는 옛 임시 worktree 등록도 일괄 prune하지 않는다.
- 나머지4개 clean 통합repo에는 불필요한 커밋을 만들지 않는다.
- `.codex` 외 다른 문서 저장소를 자동 커밋·푸시하지 않는다.

다음 행동: 수정본 설치형 로컬 실기. 원본 dev 동기화와 코드 push는 별도 승인 항목으로 두고, 실제 ML/Build5 HOLD·서버 직접 접속 금지·DB 전환 별도 승인을 유지한다.
