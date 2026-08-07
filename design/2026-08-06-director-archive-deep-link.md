# AI 숏폼 디렉터 보관함 상세 딥링크 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 보관함의 AI 숏폼 디렉터 `상세`에서 클릭한 스토리보드와 최종 영상을 열고 최종 영상 영역까지 자동 스크롤한다.

**Architecture:** 기존 렌더 작업의 `origin_storyboard_revision_id`와 `origin_render_revision_id`를 스토리보드 라우트에 전달한다. 스토어는 기존 candidate-production API로 해당 실행을 직접 복원하고, 페이지는 기존 최종 렌더 선택 기능을 호출한 뒤 영상 URL과 대상 요소가 준비되면 한 번만 스크롤한다.

**Tech Stack:** Angular 19 standalone/zoneless, signals, Angular Router, Jasmine/Karma

## Global Constraints

- 새 백엔드 API와 새 상세 화면을 만들지 않는다.
- 기존 후보 선택 진입, 일반 Clipper 편집, 다른 플러그인 상세 동작을 유지한다.
- 지정한 과거 스토리보드와 최종 렌더를 최신 항목으로 조용히 치환하지 않는다.
- 커밋·push와 앱 패키징은 사용자가 별도로 요청할 때만 수행한다.

---

### Task 1: 보관함 Director 상세 라우팅

**Files:**
- Modify: `src/shell/projects/projects/projects.component.ts`
- Test: `src/shell/projects/projects/projects.component.spec.ts`

**Interfaces:**
- Consumes: `PipelineJobSnapshot.params.origin_storyboard_revision_id`, `PipelineJobSnapshot.params.origin_render_revision_id`
- Produces: `/shortform/director/storyboard?storyboardRunId=<id>&finalRenderId=<id>`

- [ ] **Step 1: 실패하는 라우팅 테스트 작성**

```ts
it('opens a Director archive render in its storyboard page', () => {
  const component = Object.create(ProjectsComponent.prototype) as any;
  const navigate = jasmine.createSpy('navigate');
  component.router = { navigate };

  component.viewProject(directorRenderJob('render-director-1'));

  expect(navigate).toHaveBeenCalledOnceWith(
    ['/shortform/director/storyboard'],
    {
      queryParams: {
        storyboardRunId: 'storyboard-1',
        finalRenderId: 'render-director-1',
      },
    },
  );
});
```

- [ ] **Step 2: 테스트가 기존 `/projects/:id` 동작 때문에 실패하는지 확인**

Run:

```bash
npm test -- --watch=false --include='src/shell/projects/projects/projects.component.spec.ts'
```

Expected: 새 테스트 FAIL, 기존 테스트는 유지.

- [ ] **Step 3: Director 메타데이터가 완전할 때만 딥링크**

`viewProject(job)`의 첫 분기로 Director 작업과 두 원본 ID를 확인하고 위
라우트로 이동한다. 둘 중 하나라도 없으면 기존 프로젝트 상세 폴백을
그대로 실행한다.

- [ ] **Step 4: 라우팅 테스트 통과 확인**

Run:

```bash
npm test -- --watch=false --include='src/shell/projects/projects/projects.component.spec.ts'
```

Expected: PASS.

### Task 2: 스토리보드 실행 ID 직접 복원

**Files:**
- Modify: `src/features/shortform-director/state/shortform-director-production.store.ts`
- Test: `src/features/shortform-director/state/shortform-director-production.store.spec.ts`

**Interfaces:**
- Produces: `loadStoryboardRun(runId: string): Promise<void>`
- Uses existing gateway methods: `getRun`, `getResult`, `getProject`, `getStoryboardHistory`

- [ ] **Step 1: 지정한 실행을 최신 실행 대신 여는 실패 테스트 작성**

```ts
await store.loadStoryboardRun(productionRun.id);

expect(store.selectedStoryboardRunId()).toBe(productionRun.id);
expect(store.selection()).toEqual({
  candidateRunId: productionResult.candidateRunId,
  candidateId: productionResult.candidateId,
  profileId: productionRun.profileId,
});
expect(store.project()?.id).toBe(productionProject.id);
```

테스트 fixture의 storyboard history에는 다른 최신 실행을 앞에 두어,
구현이 무조건 최신 항목을 선택하면 실패하게 한다.

- [ ] **Step 2: 메서드 부재로 실패하는지 확인**

Run:

```bash
npm test -- --watch=false --include='src/features/shortform-director/state/shortform-director-production.store.spec.ts'
```

Expected: `loadStoryboardRun` 부재로 FAIL.

- [ ] **Step 3: 기존 API를 이용한 직접 복원 구현**

`loadStoryboardRun`은 `getRun/getResult/getProject`를 조회하고 lineage를
검증한 뒤 결과의 candidate ID와 run의 profile ID로 selection을 만든다.
그 selection으로 storyboard history를 불러오되 전달된 run을 선택하고
`loadExecutionState(project)`를 호출한다. 기존 request sequence를 사용해
늦게 끝난 이전 요청이 현재 화면을 덮지 못하게 한다.

- [ ] **Step 4: 스토어 테스트 통과 확인**

Run:

```bash
npm test -- --watch=false --include='src/features/shortform-director/state/shortform-director-production.store.spec.ts'
```

Expected: PASS.

### Task 3: 지정 렌더 선택과 최종 영상 영역 자동 스크롤

**Files:**
- Modify: `src/features/shortform-director/pages/production-page/production-page.component.ts`
- Modify: `src/features/shortform-director/pages/production-page/production-page.component.html`
- Test: `src/features/shortform-director/pages/production-page/production-page.component.spec.ts`

**Interfaces:**
- Consumes query params: `storyboardRunId`, `finalRenderId`
- Consumes store methods: `loadStoryboardRun`, `selectFinalRender`
- Produces DOM focus target: `#finalRenderSection`

- [ ] **Step 1: 딥링크 복원과 스크롤 실패 테스트 작성**

테스트 URL을 다음처럼 구성한다.

```ts
const url = '/shortform/director/storyboard'
  + `?storyboardRunId=${encodeURIComponent(productionRun.id)}`
  + '&finalRenderId=render-director-1';
```

gateway fixture가 해당 렌더 이력과 MP4 Blob을 반환하게 하고,
`scrollIntoView` spy를 설치한다. 페이지 로드 후 다음을 확인한다.

```ts
expect(component.production.selectedStoryboardRunId())
  .toBe(productionRun.id);
expect(component.production.selectedFinalRenderId())
  .toBe('render-director-1');
expect(scrollIntoView).toHaveBeenCalledTimes(1);
```

- [ ] **Step 2: 현재 selection 파라미터만 인식해 실패하는지 확인**

Run:

```bash
npm test -- --watch=false --include='src/features/shortform-director/pages/production-page/production-page.component.spec.ts'
```

Expected: 빈 상태가 나타나고 새 테스트 FAIL.

- [ ] **Step 3: 페이지 딥링크 hydration 구현**

`hydrateSelection`은 `storyboardRunId`가 있으면
`loadStoryboardRun(runId)`을 먼저 호출하고 `finalRenderId`가 있으면
`selectFinalRender(renderId)`를 호출한다. 일반 candidate selection
파라미터 경로는 기존 `loadSelection`을 그대로 사용한다.

`app-ai-video-production-card` 호스트에 `#finalRenderSection`을 부여한다.
페이지 effect는 딥링크의 render ID, store의 selected render ID,
`finalVideoUrl`, 대상 ElementRef가 모두 준비됐을 때만 다음을 한 번
실행한다.

```ts
target.nativeElement.scrollIntoView({ block: 'start' });
```

- [ ] **Step 4: 페이지 테스트 통과 확인**

Run:

```bash
npm test -- --watch=false --include='src/features/shortform-director/pages/production-page/production-page.component.spec.ts'
```

Expected: PASS.

### Task 4: 회귀 검증

**Files:**
- Verify only

- [ ] **Step 1: 직접 영향 테스트 묶음 실행**

```bash
npm test -- --watch=false \
  --include='src/shell/projects/projects/projects.component.spec.ts' \
  --include='src/shell/projects/projects-history-list/projects-history-list.component.spec.ts' \
  --include='src/features/shortform-director/state/shortform-director-production.store.spec.ts' \
  --include='src/features/shortform-director/pages/production-page/production-page.component.spec.ts' \
  --include='src/features/shortform-director/shortform-director-routing.integration.spec.ts'
```

Expected: PASS.

- [ ] **Step 2: Angular 빌드**

```bash
npm run build
```

Expected: build succeeds. 앱 패키징은 실행하지 않는다.

- [ ] **Step 3: 변경 범위 점검**

```bash
git diff --check
git status --short
```

Expected: 공백 오류가 없고, 이번 작업은 보관함 라우팅·스토어 복원·페이지
포커스와 그 테스트/문서에만 추가된다.
