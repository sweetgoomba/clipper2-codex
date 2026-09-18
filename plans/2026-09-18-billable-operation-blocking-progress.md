# Billable Operation Blocking Progress Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 과금 확인창 전후의 모든 유료 작업 대기 구간에서 페이지 전체를 차단하는 중앙 스피너를 일관되게 표시한다.

**Architecture:** standalone `BlockingProgressComponent`를 `MatDialog`로 여는 root service를 만들고 작업별 ref가 일시 중단·재개·종료를 소유한다. `OperationChargeGuardService`의 선택 수명주기 훅으로 견적 완료 시 스피너에서 과금 확인창으로 전환하고, 승인 시 확인창에서 스피너로 되돌린다.

**Tech Stack:** Angular 19 standalone/zoneless, Angular Material 19 `MatDialog`·`MatProgressSpinner`, Jasmine/Karma, SCSS semantic tokens

**Spec:** `.codex/design/2026-09-18-billable-operation-blocking-progress-design.md`

## Global Constraints

- 화면에는 전체 스크림과 중앙 스피너만 표시하고 가시 텍스트·별도 카드는 추가하지 않는다.
- 진행 차단과 과금 확인창을 동시에 표시하지 않는다.
- 기존 과금 순서, API 계약, 크레딧 정책, 오류 표시를 변경하지 않는다.
- 새 Angular 컴포넌트는 TS/HTML/SCSS/spec 4파일, standalone, OnPush, semantic token 규칙을 지킨다.
- 구현은 현재 최신 `dev`에서 수행하고 커밋·push는 별도 사용자 요청 전에는 하지 않는다.

---

### Task 1: 공용 전체 화면 진행 차단 UI

**Files:**
- Create: `src/shared/ui/blocking-progress/blocking-progress.component.ts`
- Create: `src/shared/ui/blocking-progress/blocking-progress.component.html`
- Create: `src/shared/ui/blocking-progress/blocking-progress.component.scss`
- Create: `src/shared/ui/blocking-progress/blocking-progress.component.spec.ts`
- Create: `src/shared/ui/blocking-progress/blocking-progress.service.ts`
- Create: `src/shared/ui/blocking-progress/blocking-progress.service.spec.ts`
- Create: `src/shared/ui/blocking-progress/index.ts`
- Modify: `src/styles.scss`

**Interfaces:**
- Produces: `BlockingProgressService.open(): BlockingProgressRef`
- Produces: `BlockingProgressRef.suspend(): void`, `resume(): void`, `close(): void`

- [x] **Step 1: 컴포넌트와 서비스 실패 테스트 작성**

  컴포넌트 테스트는 indeterminate spinner와 접근성 이름을 확인한다. 서비스 테스트는 `disableClose`, 전체 스크림 class, dialog focus, `suspend → resume → close`에서 dialog ref가 정확히 열리고 닫히며 종료된 ref는 다시 열리지 않는지 확인한다.

- [x] **Step 2: RED 확인**

  Run: `./node_modules/.bin/ng test --watch=false --progress=false --include=src/shared/ui/blocking-progress/blocking-progress.component.spec.ts --include=src/shared/ui/blocking-progress/blocking-progress.service.spec.ts`

  Expected: 새 component/service가 없어 컴파일 실패.

- [x] **Step 3: 최소 구현**

  `MatProgressSpinner`만 렌더하는 component를 만들고, service가 `MatDialog.open(BlockingProgressComponent, { disableClose: true, autoFocus: 'dialog', restoreFocus: false, panelClass: 'blocking-progress-panel', backdropClass: 'blocking-progress-backdrop' })`로 연다. ref는 suspend 시 현재 dialog를 닫고 resume 시 새 dialog를 열며 close 이후 resume을 무시한다.

- [x] **Step 4: GREEN 확인**

  Run: Task 1의 동일 Karma 명령.

  Expected: 공용 UI 테스트 전부 통과.

### Task 2: 과금 확인창 전환 수명주기

**Files:**
- Modify: `src/shared/operations/operation-charge-guard.service.ts`
- Modify: `src/shared/operations/operation-charge-guard.service.spec.ts`

**Interfaces:**
- Produces: `OperationChargeGuardLifecycle { beforeDialogOpen?: () => void; afterDialogClose?: (confirmed: boolean) => void }`
- Modifies: `confirm(operationKey, options, lifecycle?)`

- [x] **Step 1: 수명주기 실패 테스트 작성**

  견적 Promise가 끝나기 전에는 `beforeDialogOpen`이 호출되지 않고, 견적 직후 확인창보다 먼저 호출되며, 확인창 결과가 true/false일 때 `afterDialogClose`가 해당 값으로 확인 반환보다 먼저 호출되는 테스트를 추가한다. 크레딧 부족 안내도 같은 전환 규칙을 검증한다.

- [x] **Step 2: RED 확인**

  Run: `./node_modules/.bin/ng test --watch=false --progress=false --include=src/shared/operations/operation-charge-guard.service.spec.ts`

  Expected: 세 번째 인자와 훅 호출이 구현되지 않아 실패.

- [x] **Step 3: 최소 구현**

  견적 조회 뒤, 부족 안내 또는 과금 확인창을 열기 직전에 `beforeDialogOpen`을 호출한다. 다이얼로그가 닫히면 결과를 boolean으로 받은 뒤 `afterDialogClose(result)`를 호출하고 그 값을 반환한다. 견적 예외 때는 훅을 호출하지 않는다.

- [x] **Step 4: GREEN 확인**

  Run: Task 2의 동일 Karma 명령.

  Expected: 기존 견적 상세 테스트와 수명주기 테스트 전부 통과.

### Task 3: 여섯 유료 작업 진입점 연결

**Files:**
- Modify/Test: `src/features/shortform/pages/shortform-workflow-page/shortform-workflow-page.component.ts`
- Modify/Test: `src/features/shortform/pages/shortform-workflow-page/shortform-workflow-page.component.spec.ts`
- Modify/Test: `src/features/dialog-highlight/pages/dialog-setup/dialog-setup.component.ts`
- Modify/Test: `src/features/dialog-highlight/pages/dialog-setup/dialog-setup.component.spec.ts`
- Modify/Test: `src/features/dance-highlight/pages/dance-setup/dance-setup.component.ts`
- Modify/Test: `src/features/dance-highlight/pages/dance-setup/dance-setup.component.spec.ts`
- Modify/Test: `src/features/variation-v2/pages/v2-variation-list/v2-variation-list.component.ts`
- Modify/Test: `src/features/variation-v2/pages/v2-variation-list/v2-variation-list.component.spec.ts`
- Modify/Test: `src/features/variation-v2/pages/v2-results/v2-results.component.ts`
- Modify/Test: `src/features/variation-v2/pages/v2-results/v2-results.component.spec.ts`
- Modify/Test: `src/shell/projects/projects/projects.component.ts`
- Modify/Test: `src/shell/projects/projects/projects.component.spec.ts`

**Interfaces:**
- Consumes: `BlockingProgressService`, `BlockingProgressRef`, `OperationChargeGuardLifecycle`

- [x] **Step 1: 호출부 실패 테스트 작성**

  각 진입점에서 첫 비동기 사전 작업 전에 `open()`이 호출되고, guard에 `beforeDialogOpen`·`afterDialogClose`가 전달되며, 성공·취소·예외 모두 최종 `close()`를 호출하는 테스트를 추가한다. 승인 뒤 서버 작업이 보류된 테스트에서는 ref가 재개된 동안 Promise가 끝나지 않음을 확인한다.

- [x] **Step 2: RED 확인**

  Run: 여섯 변경 spec을 `--include`로 지정한 Karma 명령.

  Expected: `BlockingProgressService`가 주입·호출되지 않아 실패.

- [x] **Step 3: 최소 연결 구현**

  각 유료 흐름은 준비 완료 시 `const progress = blockingProgress.open()`으로 시작하고 `try/finally`에서 `progress.close()`한다. guard의 `beforeDialogOpen`은 `progress.suspend()`, `afterDialogClose(true)`는 `progress.resume()`을 호출한다. 취소·부족이면 resume하지 않고 반환한다. readiness 자체가 별도 동의 모달을 열 수 있는 대사/댄스 흐름은 readiness 완료 뒤에 진행 차단을 시작한다.

- [x] **Step 4: 호출부 GREEN 확인**

  Run: Task 3의 여섯 spec Karma 명령.

  Expected: 기존 동작 테스트와 새 차단 전환 테스트 전부 통과.

### Task 4: 회귀 검증 및 기록

**Files:**
- Modify: `.codex/implementation/WORKLOG.md`
- Modify: `.codex/implementation/TASKS.md`

**Interfaces:**
- Consumes: Task 1~3의 전체 구현

- [x] **Step 1: 관련 테스트 묶음 실행**

  Run: 공용 component/service, charge guard, 여섯 호출부 spec을 한 Karma 실행에 포함.

  Expected: 전부 통과.

- [x] **Step 2: 전체 빌드 실행**

  Run: `npm run build`

  Expected: Angular production build 성공.

- [x] **Step 3: 전체 테스트 실행**

  Run: `npm test -- --watch=false --progress=false`

  Expected: 전체 Karma 및 SCSS 검증 통과.

- [x] **Step 4: 문서 기록**

  WORKLOG에 변경 파일, 확인된 여섯 과금 진입점, 테스트·빌드 결과, 남은 실제 화면 검증 항목을 기록하고 TASKS에 완료 상태를 반영한다.
