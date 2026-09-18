# PG Integration Closeout Audit and Commits Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 정식 PG 통합의 현재 완료 상태와 남은 위험을 하나의 종료 감사 문서로 정리하고, Angular 진행 차단 UI는 새 feature 브랜치에, `.codex` 문서는 `main`에 각각 안전하게 저장한다.

**Architecture:** 제품 코드는 `desktop/clipper_angular` 한 저장소에만 남기고 문서 정본은 `.codex`에만 둔다. 과거 기록의 당시 미완료 표현을 그대로 재활성화하지 않고, 2026-09-18 최신 실행 증거와 현재 Git 상태를 기준으로 완료·잔여·별도 장기 과제를 구분한다.

**Tech Stack:** Git, Markdown, Angular tests/build evidence

**Spec:** `design/2026-09-18-billable-operation-blocking-progress-design.md`

## Global Constraints

- Angular 원본 checkout을 새 `feature/` 브랜치로 전환하고 이번 진행 차단 변경만 커밋한다.
- Angular 원격 push는 요청 범위가 아니므로 수행하지 않는다.
- `.codex` 변경은 문서 누락 감사와 잔여 작업 정리까지 포함해 커밋하고 `origin/main`에 push한다.
- 비밀값, 실제 OAuth/Toss 키, dump 내용은 문서에 기록하지 않는다.
- 과거 HOLD를 현재 결함으로 단정하지 않고 최신 실행 기록과 구분한다.

---

### Task 1: 최신 PG 통합 상태 감사

**Files:**
- Read: `handoff/WORKBOARD.md`
- Read: `handoff/tasks/integration.md`
- Read: `handoff/tasks/pg-production-followups.md`
- Read: `implementation/2026-09-18-development-pg-cutover-execution-log.md`
- Read: `implementation/2026-09-18-development-pg-cutover-runbook.md`
- Read: `implementation/2026-09-17-independent-dev-release-validation.md`

- [x] **Step 1:** 완료·보류·미검증 표현을 추출한다.
- [x] **Step 2:** 2026-09-18 최신 실행 결과로 해소된 과거 항목을 제거한다.
- [x] **Step 3:** 현재 Git 상태와 배포·실기 사용자 확인 기록을 교차검증한다.

### Task 2: 종료 감사 및 잔여 작업 문서화

**Files:**
- Create: `implementation/2026-09-18-pg-integration-closeout-and-remaining-work.md`
- Modify: `handoff/WORKBOARD.md`
- Modify: `implementation/TASKS.md`
- Modify: `implementation/WORKLOG.md`

- [x] **Step 1:** 완료 범위와 사용자가 직접 확인한 항목을 기록한다.
- [x] **Step 2:** 실제로 남은 필수 후속, 선택적 검증, 별도 장기 과제를 분리한다.
- [x] **Step 3:** 알려진 문제와 운영 주의사항에 증거 문서를 연결한다.
- [x] **Step 4:** Markdown 링크와 `git diff --check`를 검증한다.

### Task 3: Angular feature 브랜치 커밋

**Files:**
- Modify/Create: 현재 `desktop/clipper_angular` 변경 파일 전체

- [x] **Step 1:** 전체 Angular 테스트, 스타일 테스트, production build를 새로 실행한다.
- [x] **Step 2:** `dev`에서 `feature/billable-operation-blocking-progress-20260918` 브랜치를 만든다.
- [x] **Step 3:** 이번 기능 파일만 stage하고 staged diff를 확인한다.
- [x] **Step 4:** 기능 커밋을 만든 뒤 branch·HEAD·clean 상태를 확인한다.

### Task 4: `.codex` 문서 커밋과 push

**Files:**
- Create/Modify: Task 1–2의 `.codex` 문서와 기존 설계·계획 문서

- [x] **Step 1:** 링크 검사, 비밀값 패턴 검사, `git diff --check`를 실행한다.
- [x] **Step 2:** 이번 작업의 문서만 stage하고 staged diff를 확인한다.
- [ ] **Step 3:** 문서 커밋을 만들고 `origin/main`에 일반 push한다.
- [ ] **Step 4:** `git fetch` 후 로컬·원격 SHA 일치와 최종 상태를 확인한다.
