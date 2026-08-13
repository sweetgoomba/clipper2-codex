# Access and Credit System Replacement Roadmap Implementation Plan

> **공급자 전환 기록 (2026-08-13):** access·플러그인 권한·출처별 크레딧·결제 fulfillment 로드맵은 유지한다. 토스페이 직접 API에 연결된 익명 심사·구독·추가 크레딧 공급자 단계는 토스페이먼츠 PG 기준으로 교체하기 전까지 `dev`에 병합하지 않는다. 심사용 PG 교체와 전체 기능 전환을 분리한 현재 계획은 [`2026-08-13-toss-pay-direct-to-toss-payments-pg-handoff.md`](../records/sessions/2026-08-13-toss-pay-direct-to-toss-payments-pg-handoff.md)를 참고한다.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 기존 무통장·단일 `license` 기반 구조를 상품 등급, 기본 이용 자격, 출처별 크레딧, Toss 구독·추가 크레딧 결제 구조로 완전 교체한다.

**Architecture:** `clipper_web_api`가 상품·이용 자격·크레딧·결제의 SoT를 유지한다. 고객 웹과 관리자 웹은 새 API로 전환하고, 데스크톱은 `clipper_nestjs`의 인증 프록시와 `clipper_electron`의 플러그인 실행 경계에서 서버 권한을 다시 검증한다. 모든 저장소를 같은 전환 브랜치로 완성한 뒤에만 `dev`에 병합·배포한다.

**Tech Stack:** NestJS 11, TypeORM/PostgreSQL, Jest, Angular 19, Angular 22.1, Electron 43.3, Node.js 22/24, Toss Payments API

## Global Constraints

- 문서는 `/Users/jina/project/adlight/.codex` 안에만 저장한다.
- 코드는 각 저장소의 `dev`에서 바로 수정하지 않고 `feat/access-credit-system-replacement` 브랜치와 격리 워크트리에서 작업한다.
- API 브랜치는 `feat/billing-product-catalog-foundation`을 포함한 기준에서 시작한다. 해당 브랜치가 `dev`에 병합됐다면 최신 `dev`에서 시작한다.
- `clipper_web_api`, `clipper_web_client`, `clipper_web_admin`은 Node 22를 사용한다.
- `clipper_angular`, `clipper_electron`, `clipper_nestjs`는 Node 24를 사용한다.
- Angular 빌드 캐시 백엔드를 바꾸거나 SQLite 우회를 도입하지 않는다.
- 중간 커밋을 단독 배포할 필요는 없지만, 각 태스크는 관련 테스트와 빌드가 통과하는 검토 가능한 커밋으로 끝낸다.
- 새 마이그레이션으로 출시 전 기존 테스트 데이터와 legacy 테이블을 제거하고, 이미 적용된 과거 마이그레이션 파일은 수정하지 않는다.
- 익명 Toss 심사 결제는 유지하되 이용 자격이나 크레딧을 fulfillment하지 않는다.
- 모든 크레딧은 유효한 기본 이용 자격이 있을 때만 사용한다.
- 추가 크레딧은 모든 등급에 같은 상품·수량·가격으로 판매하는 선불 단건결제이며 플러그인 권한이나 이용기간을 부여하지 않는다.
- 외부 AI 실행과 Toss 네트워크 호출은 DB 트랜잭션 밖에서 수행하며, 30분 작업 전체를 하나의 트랜잭션으로 묶지 않는다.
- 요금제 개수·이름·가격, 플러그인 목록, 월 지급량, 크레딧 유효기간, 재시도 횟수, 환불 산식, 오프라인 유예는 코드 상수로 발명하지 않고 상품 데이터·설정·후속 정책으로 남긴다.
- API 응답은 raw JSON을 유지하고 `docs/api/openapi.yaml`을 계약 SoT로 사용한다.

---

## Dependency Map

```text
API catalog foundation
  -> API access/credit core
      -> API operations cutover
      -> authenticated Toss subscription/top-up
          -> web client billing cutover
          -> web admin operations
      -> desktop Nest proxy
          -> Angular entitlement UX
          -> Electron start/install enforcement
  -> legacy removal
  -> six-repository release gate
```

## Plan Set

| 순서 | 계획 | 주요 산출물 | 선행 조건 |
| --- | --- | --- | --- |
| 1 | `2026-08-12-access-credit-api-core.md` | 목표 DB, 이용 자격, 출처별 크레딧, 작업 차감·반환 | catalog foundation |
| 2 | `2026-08-12-authenticated-toss-subscription-topup.md` | 로그인 구독, 추가 크레딧, fulfillment, 익명 심사 보존 | 1 |
| 3 | `2026-08-12-web-client-billing-cutover.md` | 요금·결제·이용 자격·크레딧 UI | 1, 2의 OpenAPI |
| 4 | `2026-08-12-web-admin-access-credit-cutover.md` | 상품 카탈로그, 수동 이용 자격·크레딧 운영 | 1의 OpenAPI |
| 5 | `2026-08-12-desktop-entitlement-credit-cutover.md` | Nest 프록시, Angular 잠금 UI, Electron 실행 강제 | 1의 OpenAPI |
| 6 | `2026-08-12-legacy-billing-removal-release-gate.md` | legacy 제거, 전체 마이그레이션·로컬·배포 검증 | 1~5 |

### Task 1: Create Isolated Branches and Record Baselines

**Files:**
- Modify: none
- Test: each repository's existing test/build commands

**Interfaces:**
- Consumes: `feat/billing-product-catalog-foundation` in `clipper_web_api`; current `dev` in the other repositories
- Produces: one isolated worktree per repository on `feat/access-credit-system-replacement`

- [ ] **Step 1: Confirm every source checkout is clean and fetch current refs**

```bash
git -C web/clipper_web_api status --short --branch
git -C web/clipper_web_client status --short --branch
git -C web/clipper_web_admin status --short --branch
git -C desktop/clipper_angular status --short --branch
git -C desktop/clipper_electron status --short --branch
git -C desktop/clipper_nestjs status --short --branch
git -C web/clipper_web_api fetch origin
git -C web/clipper_web_client fetch origin
git -C web/clipper_web_admin fetch origin
git -C desktop/clipper_angular fetch origin
git -C desktop/clipper_electron fetch origin
git -C desktop/clipper_nestjs fetch origin
```

Expected: all six source checkouts contain no uncommitted files.

- [ ] **Step 2: Create isolated worktrees using `superpowers:using-git-worktrees`**

```bash
git -C web/clipper_web_api worktree add ../../.worktrees/clipper_web_api-access-credit -b feat/access-credit-system-replacement feat/billing-product-catalog-foundation
git -C web/clipper_web_client worktree add ../../.worktrees/clipper_web_client-access-credit -b feat/access-credit-system-replacement origin/dev
git -C web/clipper_web_admin worktree add ../../.worktrees/clipper_web_admin-access-credit -b feat/access-credit-system-replacement origin/dev
git -C desktop/clipper_angular worktree add ../../.worktrees/clipper_angular-access-credit -b feat/access-credit-system-replacement origin/dev
git -C desktop/clipper_electron worktree add ../../.worktrees/clipper_electron-access-credit -b feat/access-credit-system-replacement origin/dev
git -C desktop/clipper_nestjs worktree add ../../.worktrees/clipper_nestjs-access-credit -b feat/access-credit-system-replacement origin/dev
```

Expected: every worktree reports branch `feat/access-credit-system-replacement`. If the API catalog branch has already been merged, replace the API command's final ref with `origin/dev` after confirming that `1786500000000-CreateProductCatalog.ts` exists there.

- [ ] **Step 3: Install dependencies with each repository's pinned Node version**

```bash
cd .worktrees/clipper_web_api-access-credit && nvm use 22 && npm ci
cd .worktrees/clipper_web_client-access-credit && nvm use 22 && npm ci
cd .worktrees/clipper_web_admin-access-credit && nvm use 22 && npm ci
cd .worktrees/clipper_angular-access-credit && nvm use 24 && npm ci
cd .worktrees/clipper_electron-access-credit && nvm use 24 && npm ci
cd .worktrees/clipper_nestjs-access-credit && nvm use 24 && npm ci
```

Expected: lockfiles are unchanged after installation.

- [ ] **Step 4: Record the baseline without changing code**

```bash
cd .worktrees/clipper_web_api-access-credit && nvm use 22 && npm test -- --runInBand && npm run build
cd .worktrees/clipper_web_client-access-credit && nvm use 22 && npm test -- --watch=false --browsers=ChromeHeadless && npm run build
cd .worktrees/clipper_web_admin-access-credit && nvm use 22 && npm test -- --watch=false --browsers=ChromeHeadless && npm run build
cd .worktrees/clipper_angular-access-credit && nvm use 24 && npm test -- --watch=false --browsers=ChromeHeadless && npm run build:devapp
cd .worktrees/clipper_electron-access-credit && nvm use 24 && npm test && npm run build
cd .worktrees/clipper_nestjs-access-credit && nvm use 24 && npm run build && node --test test/*.test.js
```

Expected: all commands pass except a previously documented, unchanged baseline failure. Record any such failure before feature edits and do not hide it by weakening tests.

### Task 2: Enforce the Cross-Repository Merge Gate

**Files:**
- Create: `.codex/records/sessions/2026-08-12-access-credit-release-verification.md`
- Modify: none

**Interfaces:**
- Consumes: green outputs from all six implementation plans
- Produces: one evidence record that names exact commits, migration result, local smoke result, and dev deployment result

- [ ] **Step 1: Create the verification record with fixed sections**

```markdown
# Access/Credit Replacement Verification

## Commits
- clipper_web_api:
- clipper_web_client:
- clipper_web_admin:
- clipper_angular:
- clipper_electron:
- clipper_nestjs:

## Automated checks
| Repository | Command | Result |
| --- | --- | --- |

## Local smoke
- authenticated current access and credit summary:
- plugin entitlement denial:
- operation charge and exact-grant refund:
- Toss top-up payment and fulfillment:
- anonymous Toss review without fulfillment:

## Dev deployment
- migration:
- API health:
- web client:
- web admin:
- desktop devapp:

## Release decision
- approved commit set:
- approver:
- date:
```

- [ ] **Step 2: Refuse partial merge or deployment**

Run:

```bash
git -C /Users/jina/project/adlight/.worktrees/clipper_web_api-access-credit rev-parse HEAD
git -C /Users/jina/project/adlight/.worktrees/clipper_web_client-access-credit rev-parse HEAD
git -C /Users/jina/project/adlight/.worktrees/clipper_web_admin-access-credit rev-parse HEAD
git -C /Users/jina/project/adlight/.worktrees/clipper_angular-access-credit rev-parse HEAD
git -C /Users/jina/project/adlight/.worktrees/clipper_electron-access-credit rev-parse HEAD
git -C /Users/jina/project/adlight/.worktrees/clipper_nestjs-access-credit rev-parse HEAD
```

Expected: the six commit hashes are recorded together. No repository is merged to `dev` until the release-gate plan passes.

- [ ] **Step 3: Commit the completed verification evidence only after all checks pass**

```bash
git -C .codex add records/sessions/2026-08-12-access-credit-release-verification.md
git -C .codex commit -m "docs: record access credit release verification"
```
