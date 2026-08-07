# AI 숏폼 디렉터 계보 Breadcrumb Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Director 사이드바와 선택 누락 inbox를 제거하고, 실제 선택 계보 breadcrumb 및 정확한 보관함 프로젝트 딥링크를 제공한다.

**Architecture:** 공통 breadcrumb는 표시 전용 standalone 컴포넌트로 만들고 각 페이지가 보유한 프로필·주제·후보 데이터를 항목으로 전달한다. 선택 누락은 `CanActivateFn`이 컴포넌트 활성화 전에 유효한 이전 단계로 돌려보낸다. 보관함 진입은 잘못 해석한 storyboard run ID 대신 Director project ID와 video plan revision을 사용한다.

**Tech Stack:** Angular standalone components, Angular Router guards and `UrlTree`, signals, Jasmine/Karma.

## Global Constraints

- 왼쪽 Director 단계 사이드바를 렌더링하지 않는다.
- breadcrumb 중간에는 `아이디어 찾기`와 `영상 후보` 같은 단계명을 반복하지 않는다.
- 선택 누락 inbox UI를 렌더링하지 않는다.
- 실제 데이터가 0개인 정상 빈 상태는 유지한다.
- 보관함 상세는 정확한 Director 프로젝트와 최종 렌더를 연다.
- 앱 패키징 빌드와 git commit은 실행하지 않는다.

---

### Task 1: 공통 계보 Breadcrumb와 사이드바 제거

**Files:**
- Create: `src/features/shortform-director/components/director-breadcrumb/director-breadcrumb.component.ts`
- Create: `src/features/shortform-director/components/director-breadcrumb/director-breadcrumb.component.html`
- Create: `src/features/shortform-director/components/director-breadcrumb/director-breadcrumb.component.scss`
- Create: `src/features/shortform-director/components/director-breadcrumb/director-breadcrumb.component.spec.ts`
- Modify: `src/features/shortform-director/layout/shortform-director-shell/shortform-director-shell.component.ts`
- Modify: `src/features/shortform-director/layout/shortform-director-shell/shortform-director-shell.component.html`
- Modify: `src/features/shortform-director/layout/shortform-director-shell/shortform-director-shell.component.scss`
- Modify: `src/features/shortform-director/layout/shortform-director-shell/shortform-director-shell.component.spec.ts`

**Interfaces:**
- Produces: `DirectorBreadcrumbItem` with `label`, optional `routerLink`, and optional `queryParams`.
- Produces: `DirectorBreadcrumbComponent.items` required input.

- [ ] **Step 1: Write failing component and shell tests**

Assert a breadcrumb renders linked ancestors, a text-only current item, full
labels in `title`, and an accessible breadcrumb navigation. Assert the shell
contains no `app-director-sidebar` and keeps one child outlet.

- [ ] **Step 2: Run tests and verify RED**

Run:
`npm test -- --watch=false --include=src/features/shortform-director/components/director-breadcrumb/director-breadcrumb.component.spec.ts --include=src/features/shortform-director/layout/shortform-director-shell/shortform-director-shell.component.spec.ts`

Expected: the new component is missing and the shell still renders the sidebar.

- [ ] **Step 3: Implement the minimal component and shell layout**

Use an ordered list inside `nav[aria-label="현재 작업 경로"]`. Render previous
items with `RouterLink`, the last item with `aria-current="page"`, and remove
`DirectorSidebarComponent` from shell imports and markup.

- [ ] **Step 4: Run tests and verify GREEN**

Run the Task 1 command and expect all included tests to pass.

### Task 2: 필수 선택 라우트 보호와 inbox 제거

**Files:**
- Create: `src/features/shortform-director/routing/shortform-director-context.guards.ts`
- Create: `src/features/shortform-director/routing/shortform-director-context.guards.spec.ts`
- Modify: `src/app/app.routes.ts`
- Modify: `src/features/shortform-director/pages/ideas-page/ideas-page.component.ts`
- Modify: `src/features/shortform-director/pages/ideas-page/ideas-page.component.html`
- Modify: `src/features/shortform-director/pages/candidates-page/candidates-page.component.ts`
- Modify: `src/features/shortform-director/pages/candidates-page/candidates-page.component.html`
- Modify: `src/features/shortform-director/pages/production-page/production-page.component.ts`
- Modify: `src/features/shortform-director/pages/production-page/production-page.component.html`

**Interfaces:**
- Produces: `shortformDirectorIdeasContextGuard`,
  `shortformDirectorCandidatesContextGuard`,
  `shortformDirectorStoryboardContextGuard`.
- Consumes: bounded opaque query values from
  `opaqueWorkspaceQueryValue(value: string | null)`.

- [ ] **Step 1: Write failing guard tests**

Assert complete URLs return `true`; incomplete ideas, candidates, and storyboard
URLs return literal expected `UrlTree` strings for profiles, ideas, or candidates.

- [ ] **Step 2: Run tests and verify RED**

Run:
`npm test -- --watch=false --include=src/features/shortform-director/routing/shortform-director-context.guards.spec.ts`

Expected: guard exports do not exist.

- [ ] **Step 3: Implement guards and attach them to routes**

Build redirects with `Router.createUrlTree`, preserving only verified contextual
IDs needed by the destination. Add `canActivate` to ideas, candidates, and
storyboard child routes.

- [ ] **Step 4: Remove prerequisite empty-state branches**

Remove `DirectorEmptyStateComponent` imports and the three prerequisite inbox
branches. Render each page's normal content because the route guard now owns the
invalid-context case.

- [ ] **Step 5: Run page and routing tests**

Run the guard test plus ideas, candidates, production, and routing integration
specs. Expect no prerequisite inbox and correct redirects.

### Task 3: 페이지별 실제 선택 계보

**Files:**
- Modify: `src/features/shortform-director/pages/profiles-page/profiles-page.component.ts`
- Modify: `src/features/shortform-director/pages/profiles-page/profiles-page.component.html`
- Modify: `src/features/shortform-director/pages/ideas-page/ideas-page.component.ts`
- Modify: `src/features/shortform-director/pages/ideas-page/ideas-page.component.html`
- Modify: `src/features/shortform-director/pages/candidates-page/candidates-page.component.ts`
- Modify: `src/features/shortform-director/pages/candidates-page/candidates-page.component.html`
- Modify: `src/features/shortform-director/pages/production-page/production-page.component.ts`
- Modify: `src/features/shortform-director/pages/production-page/production-page.component.html`
- Modify: `src/features/shortform-director/pages/runs-page/runs-page.component.ts`
- Modify: `src/features/shortform-director/pages/runs-page/runs-page.component.html`
- Test: corresponding `*.component.spec.ts` files.

**Interfaces:**
- Consumes: `DirectorBreadcrumbItem[]`.
- Produces: computed page breadcrumb items whose links retain profile, research,
  topic, and candidate context.

- [ ] **Step 1: Add failing page breadcrumb assertions**

Use literal Korean labels to assert ideas has profile name, candidates has profile
and topic names, and storyboard has profile, topic, candidate, and current page
without duplicated intermediate stage labels.

- [ ] **Step 2: Run page specs and verify RED**

Expected: pages do not render `app-director-breadcrumb`.

- [ ] **Step 3: Add computed items and render the shared component**

Use each page store's already loaded domain objects. For production, derive
profile name from `planningContext.brandProfile.brandName`, topic name from the
first `campaignBrief.prompt` segment, and candidate name from `project.title`.

- [ ] **Step 4: Run page specs and verify GREEN**

Run all five page specs and expect all breadcrumb assertions to pass.

### Task 4: 보관함 Director 프로젝트 딥링크

**Files:**
- Modify: `src/shell/projects/projects/projects.component.ts`
- Modify: `src/shell/projects/projects/projects.component.spec.ts`
- Modify: `src/features/shortform-director/services/shortform-director-production.gateway.ts`
- Modify: `src/features/shortform-director/services/shortform-director-production.service.ts`
- Modify: `src/features/shortform-director/services/shortform-director-production.service.spec.ts`
- Modify: `src/features/shortform-director/state/shortform-director-production.store.ts`
- Modify: `src/features/shortform-director/state/shortform-director-production.store.spec.ts`
- Modify: `src/features/shortform-director/pages/production-page/production-page.component.ts`
- Modify: `src/features/shortform-director/pages/production-page/production-page.component.spec.ts`

**Interfaces:**
- Produces:
  `getProjectById(projectId: string): Promise<ShortformDirectorProject>`.
- Produces:
  `loadArchiveProject(projectId: string, storyboardRevisionId: string): Promise<void>`.
- Archive query contract:
  `projectId`, `storyboardRevisionId`, `finalRenderId`.

- [ ] **Step 1: Replace the misleading archive tests with failing real-metadata tests**

Use `origin_director_project_id`, a `videoPlan.id` storyboard revision, and a
render ID. Assert navigation emits the new query contract and the page calls
project-by-ID rather than run-by-ID.

- [ ] **Step 2: Run archive tests and verify RED**

Expected: navigation still emits `storyboardRunId` and project hydration calls
the candidate-production run endpoints.

- [ ] **Step 3: Add project-by-ID gateway and store hydration**

Call `GET /projects/shortform-director/projects/:projectId`, validate project ID
and `videoPlan.id`, set project/config state, and load narration, AI video, and
final render state without requiring candidate selection.

- [ ] **Step 4: Update production archive query and rendering**

Hydrate with project and revision IDs, allow project content to render without a
candidate selection, hide new-storyboard creation in that case, select the exact
render, and scroll only after its video URL is ready.

- [ ] **Step 5: Run archive tests and verify GREEN**

Run projects component, production service, production store, and production
page specs. Expect all archive assertions to pass.

### Task 5: 통합 검증

**Files:**
- Modify: `src/features/shortform-director/shortform-director-routing.integration.spec.ts`

**Interfaces:**
- Consumes: final route guards, breadcrumb component, and archive query contract.

- [ ] **Step 1: Update the routing integration expectation**

Assert every valid Director route renders one app page, no sidebar, the expected
page, and a breadcrumb. Use complete valid queries for candidates and storyboard.

- [ ] **Step 2: Run the Director impact suite**

Run all Director shell, route guard, page, store, service, projects, and routing
integration specs. Expect all tests to pass.

- [ ] **Step 3: Run the full Angular suite**

Run: `npm test -- --watch=false --progress=false --reporters=dots`

Expected: all Angular tests pass.

- [ ] **Step 4: Check the diff**

Run: `git diff --check`

Expected: no whitespace errors. Do not run app packaging and do not commit.
