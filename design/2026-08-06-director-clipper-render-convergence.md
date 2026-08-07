# AI 숏폼 디렉터 Clipper 렌더 통합 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** AI 숏폼 디렉터 최종 영상을 기존 Clipper 렌더·전역 큐·프로젝트 보관함 흐름으로 만들고, Full 시스템 템플릿과 렌더 버전을 양쪽 화면에서 동일하게 표시한다.

**Architecture:** `ShortformProjectService.startRender()`와 `clipper_video_render`를 유일한 실행 경계로 유지한다. Director는 렌더 작업에 `shortform_director` 출처 메타데이터와 안정적인 보관함 프로젝트 ID를 전달하고, 전역 Jobs WebSocket 이벤트로 상태를 갱신한다. 완성 MP4는 프로젝트 보관함의 버전 경로만 정식 원본으로 사용하며 Director 화면은 같은 프로젝트 파일을 참조한다.

**Tech Stack:** NestJS 11, TypeScript 5.7, Angular 19 signals, RxJS 7, 기존 `/v1/events` WebSocket, Node test runner, Jasmine/Karma.

## Global Constraints

- 최종 렌더 실행기는 기존 `clipper_video_render`를 그대로 사용한다.
- 실행 큐·완료 작업에서 출처 기능은 `shortform_director`로 표시한다.
- 상태 확인용 반복 HTTP polling과 1초 `setTimeout` 반복을 사용하지 않는다.
- 새 렌더가 실패해도 기존 활성 렌더 버전을 유지한다.
- Director와 프로젝트 보관함은 같은 정식 MP4 파일을 참조한다.
- Full 시스템 템플릿은 읽기 전용이며 출력 크기는 `1080×1920`이다.
- 새 템플릿 생성 비율은 기존 `1:1`, `4:3`만 유지한다.
- 패키징 빌드는 실행하지 않는다. 사용자가 직접 패키징한다.
- 기존 dirty worktree의 관련 없는 변경은 수정하거나 스테이징하지 않는다.
- 사용자가 별도로 요청하기 전에는 커밋하거나 푸시하지 않는다.

---

## 파일 구조

### NestJS

- `src/modules/jobs/application/jobs.service.ts`
  - terminal job을 기다리는 이벤트 기반 Promise 경계를 제공한다.
- `src/modules/shortform/domain/shortform-project.model.ts`
  - Director 렌더 출처 계약을 정의한다.
- `src/modules/shortform/application/shortform-project.service.ts`
  - 렌더 params에 출처·리비전 정보를 전달하고 기존 polling watcher를 제거한다.
- `src/modules/projects/application/projects.service.ts`
  - Director 렌더 결과를 하나의 보관함 프로젝트에 버전으로 누적한다.
- `src/modules/projects/application/project-detail-builder.ts`
  - Director 렌더 버전을 `ProjectRenderItem[]`으로 투영한다.
- `src/modules/projects/domain/project.model.ts`
  - `shortform_director` 프로젝트 상세 category를 표현한다.
- `src/modules/shortform-director/domain/production-state.ts`
  - 렌더 리비전과 보관함 프로젝트·작업·파일 참조를 연결한다.
- `src/modules/shortform-director/application/shortform-director-clipper-render.adapter.ts`
  - 일반 Clipper 프로젝트 입력만 준비하고 Director 전용 타이틀 폭 계산을 제거한다.
- `src/modules/shortform-director/application/shortform-director-final-render.service.ts`
  - 보관함 프로젝트를 단일 원본으로 사용하고 Director MP4 복사를 제거한다.
- `src/modules/shortform-director/presentation/shortform-director-final-render.controller.ts`
  - 기존 API 경계를 유지하면서 보관함 파일을 스트리밍한다.

### Angular

- `src/features/template-builder/models/template-builder.ts`
  - API 응답의 `full` ratio 타입을 표현하되 생성 ratio 목록과 분리한다.
- `src/features/template-builder/pages/template-builder-page/template-builder-page.component.ts`
  - family의 실제 variant를 기준으로 Full을 선택한다.
- `src/features/template-builder/components/template-builder-editor/template-builder-editor.component.ts`
  - Full family에 Full 탭과 `1080×1920` 캔버스를 표시한다.
- `src/core/history/job-history.service.ts`
  - 기존 WebSocket snapshot을 Director도 소비할 수 있는 상태 원본으로 유지한다.
- `src/features/shortform-director/state/shortform-director-production.store.ts`
  - 최종 렌더 polling을 제거하고 Job snapshot 이벤트를 구독한다.
- `src/features/shortform-director/components/ai-video-production-card/*`
  - 실행 큐 이동 동작과 현재 job 상태를 표시한다.
- `src/features/shortform-director/pages/production-page/*`
  - 실행 큐 이동 라우팅을 연결한다.
- `src/shell/projects/models/projects-view.ts`
  - 실행기와 별개인 출처 기능 정렬 키를 카드에 보존한다.
- `src/shell/projects/projects/projects.component.ts`
  - Director 큐·완료 카드를 `AI 숏폼 디렉터`로 분류하고 재렌더 job을 한 프로젝트 카드로 접는다.
- `src/shell/projects/projects-history-list/projects-history-list.component.ts`
  - 출처 기능 키를 사용해 섹션 순서를 계산한다.
- `src/shell/projects/projects-detail-page/*`
  - Director 프로젝트의 활성 영상과 이전 렌더 버전을 표시한다.
- `src/core/history/project-history.service.ts`
  - Director 상세 category와 version file URL을 표현한다.

---

### Task 1: Full 시스템 템플릿을 Angular 템플릿 페이지에 정상 표시

**Files:**
- Modify: `desktop/clipper_angular/src/features/template-builder/models/template-builder.ts`
- Modify: `desktop/clipper_angular/src/features/template-builder/pages/template-builder-page/template-builder-page.component.ts`
- Modify: `desktop/clipper_angular/src/features/template-builder/components/template-builder-editor/template-builder-editor.component.ts`
- Test: `desktop/clipper_angular/src/features/template-builder/pages/template-builder-page/template-builder-page.component.spec.ts`
- Test: `desktop/clipper_angular/src/features/template-builder/components/template-builder-editor/template-builder-editor.component.spec.ts`

**Interfaces:**
- Produces: `TemplateBuilderRatio = '16:9' | '4:3' | '1:1' | 'full'`
- Preserves: `SHORTFORM_TEMPLATE_BUILDER_CREATE_RATIOS = ['1:1', '4:3']`
- Produces: family 실제 variant에서 선택 가능한 ratio를 계산하는 helper

- [ ] **Step 1: Full family 선택 회귀 테스트 작성**

```ts
it('selects the existing full variant instead of a missing 1:1 variant', async () => {
  service.listFamilies.and.resolveTo([fullSystemFamily()]);
  await component.loadFamilies();
  expect(component.editorSelectedRatio()).toBe('full');
  expect(fixture.nativeElement.textContent).toContain('1080 x 1920');
  expect(fixture.nativeElement.textContent).not.toContain('1:1 비율 템플릿이 없습니다');
});
```

- [ ] **Step 2: 편집기 ratio 테스트 작성**

```ts
it('exposes only the full ratio supplied by the readonly full family', () => {
  fixture.componentRef.setInput('family', fullSystemFamily());
  fixture.detectChanges();
  expect(fixture.componentInstance.ratios).toEqual(['full']);
});
```

- [ ] **Step 3: 대상 테스트를 실행해 현재 실패 확인**

Run:

```bash
cd desktop/clipper_angular
npm test -- --watch=false --browsers=ChromeHeadless \
  --include=src/features/template-builder/pages/template-builder-page/template-builder-page.component.spec.ts \
  --include=src/features/template-builder/components/template-builder-editor/template-builder-editor.component.spec.ts
```

Expected: Full ratio가 Angular 타입/선택 목록에 없어 실패한다.

- [ ] **Step 4: API ratio와 생성 가능 ratio를 분리**

```ts
export const TEMPLATE_BUILDER_RATIOS =
  ['16:9', '4:3', '1:1', 'full'] as const;
export const SHORTFORM_TEMPLATE_BUILDER_CREATE_RATIOS =
  ['1:1', '4:3'] as const;
export type TemplateBuilderRatio =
  typeof TEMPLATE_BUILDER_RATIOS[number];
export type ShortformTemplateBuilderCreateRatio =
  typeof SHORTFORM_TEMPLATE_BUILDER_CREATE_RATIOS[number];
```

새 템플릿 폼은 create ratio 상수만 사용하고, editor의 `ratios` 및
`defaultSelectedRatioForFamily()`은 `family.variants`에 실제 존재하는
ratio를 사용한다. 읽기 전용 Full family에는 저장·삭제·복제 버튼을
노출하지 않는다.

- [ ] **Step 5: 대상 테스트와 Angular build 실행**

Run: Step 3 명령.

Expected: 두 spec 모두 PASS.

Run:

```bash
cd desktop/clipper_angular
npm run build
```

Expected: build 성공.

---

### Task 2: Jobs terminal 이벤트 경계로 기존 Shortform 서버 polling 제거

**Files:**
- Modify: `desktop/clipper_nestjs/src/modules/jobs/application/jobs.service.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform/application/shortform-project.service.ts`
- Create: `desktop/clipper_nestjs/test/jobs-terminal-wait.test.js`
- Test: `desktop/clipper_nestjs/test/shortform-project-api.test.js`

**Interfaces:**
- Produces:

```ts
JobsService.waitForTerminal(
  jobId: string,
  auth: AuthContext,
): Promise<PipelineJobSnapshot>
```

- A terminal status is `completed | failed | cancelled`.
- The Promise resolves from the same lifecycle that publishes the terminal job snapshot.

- [ ] **Step 1: terminal 대기 테스트 작성**

다음 세 경우를 검증한다.

```js
test('waitForTerminal resolves immediately for an already completed job');
test('waitForTerminal resolves once when publish stores a terminal state');
test('waitForTerminal does not issue repeated repository reads while waiting');
```

세 번째 테스트는 repository `get` 호출 수를 고정하고 가짜 타이머를
진행해도 호출 수가 증가하지 않는지 확인한다.

- [ ] **Step 2: Nest build 후 새 테스트 실패 확인**

Run:

```bash
cd desktop/clipper_nestjs
npm run build
node --test test/jobs-terminal-wait.test.js
```

Expected: `waitForTerminal`이 없어 FAIL.

- [ ] **Step 3: race-safe terminal waiter 구현**

`JobsService`에 job별 waiter 집합을 추가한다. waiter 등록 전후 사이에
terminal 전환이 발생할 수 있으므로 현재 snapshot을 확인하고 waiter를
등록한 뒤 한 번 재확인한다. `publish()`가 terminal snapshot을 저장하고
프로젝트 기록까지 마친 다음 해당 waiter를 한 번만 resolve한다.

```ts
private readonly terminalWaiters =
  new Map<string, Set<JobTerminalWaiter>>();

interface JobTerminalWaiter {
  ownerSubjectId: string;
  resolve(snapshot: PipelineJobSnapshot): void;
  reject(error: Error): void;
}
```

- [ ] **Step 4: Shortform watcher의 반복 timer 제거**

`watchShortformRenderJob()`의 240회 loop를 삭제하고 다음 형태로
대체한다.

```ts
const job = await this.jobs.waitForTerminal(jobId, auth);
if (job.status === 'completed') {
  await this.succeedBillableOperation(operation);
  return;
}
await this.failBillableOperation(operation, terminalFailureMessage(job));
await this.syncShortformProjectAfterRenderJob(project, jobId, auth);
```

- [ ] **Step 5: 관련 Nest 테스트 실행**

Run:

```bash
cd desktop/clipper_nestjs
npm run build
node --test \
  test/jobs-terminal-wait.test.js \
  test/jobs-commit-phase.test.js \
  test/shortform-project-api.test.js
```

Expected: 모두 PASS, `watchShortformRenderJob`에 polling loop 없음.

---

### Task 3: 렌더 실행기와 Director 출처 기능을 분리

**Files:**
- Modify: `desktop/clipper_nestjs/src/modules/shortform/domain/shortform-project.model.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform/application/shortform-project.service.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-final-render.service.ts`
- Modify: `desktop/clipper_nestjs/src/modules/projects/application/projects.service.ts`
- Test: `desktop/clipper_nestjs/test/shortform-director-final-render-service.test.js`
- Test: `desktop/clipper_nestjs/test/project-output-render-path.test.js`

**Interfaces:**
- Produces:

```ts
export interface ShortformRenderOrigin {
  featureName: 'shortform_director';
  directorProjectId: string;
  // ShortformDirectorProject.videoPlan.id
  storyboardRevisionId: string;
  renderRevisionId: string;
  archiveProjectId: string;
}

export interface StartShortformProjectRenderRequest {
  jobId?: string;
  renderProjectId?: string;
  origin?: ShortformRenderOrigin;
  providerId?: string;
  dryRun?: boolean;
}
```

- Job executor remains `clipper_video_render`.
- Job params expose trusted snake-case projection:
  `origin_feature_name`, `origin_project_id`,
  `origin_storyboard_revision_id`, `origin_render_revision_id`,
  `archive_project_id`.

- [ ] **Step 1: Director start contract test 수정**

```js
assert.equal(call.request.origin.featureName, 'shortform_director');
assert.equal(call.request.origin.directorProjectId, projectId);
assert.equal(call.request.origin.renderRevisionId, result.renderId);
assert.equal(call.request.origin.archiveProjectId, `director-project.${projectId}`);
```

- [ ] **Step 2: 일반 Clipper와 Director params 분리 테스트 작성**

일반 Clipper 요청에는 origin params가 없고, Director 요청에만 정확한
다섯 필드가 포함되는지 검증한다. 임의의 다른 featureName은
`BadRequestException`으로 거절한다.

- [ ] **Step 3: 대상 테스트 실패 확인**

Run:

```bash
cd desktop/clipper_nestjs
npm run build
node --test \
  test/shortform-director-final-render-service.test.js \
  test/project-output-render-path.test.js
```

Expected: origin 계약이 없어 FAIL.

- [ ] **Step 4: typed origin 전달 구현**

Director final render start가 현재 storyboard revision을 해석해
`ShortformRenderOrigin`을 구성한다. `ShortformProjectService.startRender()`
는 이 객체를 검증한 뒤 render job params로 복사한다. 일반 Clipper
요청 경로는 변경하지 않는다.

`storyboardRevisionId`에는 별도 추정 ID를 만들지 않고 현재
`ShortformDirectorProject.videoPlan.id`를 사용한다.

- [ ] **Step 5: 대상 테스트 재실행**

Run: Step 3 명령.

Expected: PASS.

---

### Task 4: 프로젝트 보관함에 하나의 Director 프로젝트와 버전 파일 저장

**Files:**
- Modify: `desktop/clipper_nestjs/src/modules/projects/application/projects.service.ts`
- Modify: `desktop/clipper_nestjs/src/modules/projects/application/project-detail-builder.ts`
- Modify: `desktop/clipper_nestjs/src/modules/projects/domain/project.model.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/domain/production-state.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-final-render.service.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/presentation/shortform-director-final-render.controller.ts`
- Create: `desktop/clipper_nestjs/test/shortform-director-project-archive.test.js`
- Test: `desktop/clipper_nestjs/test/shortform-director-final-render-service.test.js`
- Test: `desktop/clipper_nestjs/test/project-file-media-ticket.test.js`

**Interfaces:**
- Produces persisted revision metadata:

```ts
export interface ShortformDirectorCompletedRenderRevisionV1 {
  renderId: string;
  storyboardRevisionId: string;
  jobId: string;
  archiveProjectId: string;
  videoRelativePath: string;
  thumbnailRelativePath?: string;
  completedAt: string;
}
```

- Canonical video path:
  `renders/revisions/<renderRevisionId>/main.mp4`
- Project result keys:
  `active_render_revision_id`, `video_relative_path`,
  `thumbnail_relative_path`, `render_revisions`.

- [ ] **Step 1: archive 누적 테스트 작성**

첫 번째와 두 번째 render job을 차례로 완료했을 때 다음을 검증한다.

```js
assert.equal(project.projectId, stableArchiveProjectId);
assert.equal(project.pluginName, 'shortform_director');
assert.equal(project.result.render_revisions.length, 2);
assert.equal(project.result.active_render_revision_id, secondRevisionId);
assert.equal(project.result.video_relative_path, secondVideoPath);
```

두 revision 파일이 모두 존재하고 staging `renders/main.mp4`는 정식
결과로 남지 않는지도 확인한다.

- [ ] **Step 2: 실패·재시도·idempotency 테스트 작성**

```js
test('a failed rerender keeps the previous active revision');
test('recording the same completed job twice does not duplicate a revision');
test('legacy Director files remain readable without becoming the new canonical path');
```

- [ ] **Step 3: 상세 projection 및 파일 ticket 테스트 작성**

`ProjectDetail.category`가 `shortform_director`이고 `renders` 배열이 최신
순서의 두 `ProjectRenderItem`을 반환하는지 확인한다. 각 version path에
프로젝트 파일 ticket을 발급하고 다른 경로는 거절하는지 검증한다.

- [ ] **Step 4: 대상 테스트 실패 확인**

Run:

```bash
cd desktop/clipper_nestjs
npm run build
node --test \
  test/shortform-director-project-archive.test.js \
  test/shortform-director-final-render-service.test.js \
  test/project-file-media-ticket.test.js
```

Expected: Director archive projection이 없어 FAIL.

- [ ] **Step 5: canonical version 저장 구현**

`ProjectsService.recordCompletedJob()`에서 검증된 Director origin을
감지하면 다음 순서로 처리한다.

1. stable archive root와 version target을 owner scope 아래 계산한다.
2. 렌더러의 staging `renders/main.mp4`를 version target으로 원자적
   `rename`한다.
3. 기존 ProjectSnapshot의 `render_revisions`를 읽어 동일 renderId를
   교체하거나 새 항목을 추가한다.
4. 새 revision을 active로 지정하고 `pluginName`을
   `shortform_director`로 저장한다.
5. 기존 revision 파일과 metadata는 유지한다.

Director final service는 새 revision에 대해 `copyFile()`을 호출하지
않고 `ProjectsService.resolveProjectFile()`로 canonical 파일을
스트리밍한다. 기존 Director 전용 파일은 legacy revision에 한해 기존
읽기 경로를 유지한다.

- [ ] **Step 6: ProjectDetail projection 구현**

```ts
export interface ProjectDetail extends ProjectSnapshot {
  category:
    | 'dialog'
    | 'dance'
    | 'shortform_director'
    | 'unknown';
  // existing fields...
}
```

`render_revisions`를 `ProjectRenderItem[]`으로 변환하면서
`renderId`, `title`, `videoPath`, `durationSec`을 채운다.

- [ ] **Step 7: 대상 테스트와 Nest build 재실행**

Run: Step 4 명령.

Expected: 모두 PASS.

Run:

```bash
cd desktop/clipper_nestjs
npm run build
```

Expected: build 성공.

---

### Task 5: Director와 일반 Clipper의 템플릿 render payload를 단일화

**Files:**
- Modify: `desktop/clipper_nestjs/src/modules/shortform-director/application/shortform-director-clipper-render.adapter.ts`
- Modify: `desktop/clipper_nestjs/src/modules/shortform/application/shortform-project.service.ts`
- Test: `desktop/clipper_nestjs/test/shortform-director-clipper-render-adapter.test.js`
- Test: `desktop/clipper_nestjs/test/shortform-director-render-contract.test.js`
- Test: `desktop/clipper_nestjs/test/template-builder-full-family.test.js`

**Interfaces:**
- Consumes: published preset
  `FIRST_FAMILY_FULL_TEMPLATE_PRESET_ID`
- Produces: 일반 Clipper와 동일한 `templateVersionSnapshot`과 render payload
- Preserves: Director가 생성한 `mainTitle1`, `mainTitle2` 문자열
- Prohibits: Director adapter가 font size, tracking, layer position,
  canvas scale을 별도로 지정하는 동작

- [ ] **Step 1: 일반 Clipper와 Director payload 동등성 테스트 작성**

Director adapter가 생성한 `mainTitle1`, `mainTitle2`를 추출한 뒤,
동일한 두 문자열과 Full preset, visibility를 입력한 일반 prepared
project와 다음 payload 필드가 동일한지 비교한다.

```js
assert.deepEqual(directorPayload.template, clipperPayload.template);
assert.deepEqual(directorPayload.title, clipperPayload.title);
assert.deepEqual(directorPayload.subtitleStyle, clipperPayload.subtitleStyle);
```

- [ ] **Step 2: 타이틀 문구 생성과 렌더 스타일 책임을 분리하는 테스트 작성**

Director는 스토리보드 제목에서 `mainTitle1`과 선택적 `mainTitle2`
문자열을 만들 수 있다. 이 테스트는 줄 분리 결과를 허용하되 adapter가
`fontSize`, `tracking`, `x`, `y`, `width`, `height` 같은 템플릿 스타일
값을 project input에 추가하지 않는지 검증한다.

- [ ] **Step 3: 대상 테스트 실패 확인**

Run:

```bash
cd desktop/clipper_nestjs
npm run build
node --test \
  test/shortform-director-clipper-render-adapter.test.js \
  test/shortform-director-render-contract.test.js \
  test/template-builder-full-family.test.js
```

Expected: 현재 Director 경로와 일반 Clipper 경로의 template snapshot
또는 payload 차이가 드러나 FAIL.

- [ ] **Step 4: payload 차이를 만드는 입력 경계만 제거**

Director adapter는 타이틀 문자열과 Full preset ID만 일반
`ShortformProject`에 넣는다. 타이틀 문자열을 두 줄로 나누는 순수
content formatter는 유지할 수 있지만 font size, tracking, layer
position, canvas scale, template snapshot 생성은 모두
`ShortformProjectService`와 template catalog에 맡긴다. 실패한 동등성
테스트에서 확인된 차이만 제거하고 인접 코드는 정리하지 않는다.

- [ ] **Step 5: 대상 테스트 재실행**

Run: Step 3 명령.

Expected: PASS.

---

### Task 6: Director 화면의 최종 렌더 polling을 Jobs WebSocket 구독으로 교체

**Files:**
- Modify: `desktop/clipper_angular/src/features/shortform-director/models/shortform-director-production.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-production.gateway.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/services/shortform-director-production.service.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/state/shortform-director-production.store.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/ai-video-production-card/ai-video-production-card.component.ts`
- Modify: `desktop/clipper_angular/src/features/shortform-director/components/ai-video-production-card/ai-video-production-card.component.html`
- Modify: `desktop/clipper_angular/src/features/shortform-director/pages/production-page/production-page.component.ts`
- Test: `desktop/clipper_angular/src/features/shortform-director/state/shortform-director-production.store.spec.ts`
- Test: `desktop/clipper_angular/src/features/shortform-director/pages/production-page/production-page.component.spec.ts`

**Interfaces:**
- Consumes: `JobHistoryService.connect(handler)` and `jobs.snapshot`
- Start result includes: `renderId`, `jobId`, `archiveProjectId`, `status`
- Produces: `queueJobId` signal and `queueRequested` output

- [ ] **Step 1: 장기 waiting 상태 테스트 작성**

```ts
it('keeps a final render waiting without issuing status polling requests', async () => {
  await store.startFinalRender();
  jobStream.emit(snapshotWith(jobId, 'waiting'));
  tick(60 * 60 * 1000);
  expect(gateway.getFinalRenderStatus).not.toHaveBeenCalled();
  expect(store.finalRender()?.status).toBe('waiting');
});
```

- [ ] **Step 2: terminal event와 reconnect 테스트 작성**

```ts
it('loads the final artifact once after the matching job completes');
it('ignores snapshots for unrelated plugin jobs');
it('restores a pending render from the full snapshot after reconnect');
it('unsubscribes from job history when the store is destroyed');
```

완료 테스트는 terminal snapshot 한 번에 status reconcile GET과 파일
다운로드가 각각 한 번만 호출되는지 확인한다.

- [ ] **Step 3: 현재 polling 구현으로 테스트 실패 확인**

Run:

```bash
cd desktop/clipper_angular
npm test -- --watch=false --browsers=ChromeHeadless \
  --include=src/features/shortform-director/state/shortform-director-production.store.spec.ts \
  --include=src/features/shortform-director/pages/production-page/production-page.component.spec.ts
```

Expected: `pollFinalRender()`가 반복 GET을 호출해 FAIL.

- [ ] **Step 4: 공유 JobHistoryService 구독 구현**

store가 로드될 때 `JobHistoryService.connect()`를 한 번 호출한다.
snapshot에서 `queueJobId`가 같은 job만 투영하고 terminal 상태가 되면
`getFinalRenderStatus()`를 한 번 호출해 Director revision을
reconcile한다. 이후 canonical project file URL을 사용한다.

다음을 삭제한다.

- `pollFinalRender()`
- final render용 `delay(1_000)`
- 최대 240회 loop

- [ ] **Step 5: 실행 큐 이동 버튼 연결**

Director 카드에 렌더가 waiting/starting/running일 때
`실행 큐에서 보기` 버튼을 표시한다. production page는 다음 라우트로
이동한다.

```ts
this.router.navigate(['/projects'], {
  queryParams: {
    plugin: 'shortform_director',
    job: queueJobId,
  },
});
```

렌더 시작 직후 자동으로 이동하지 않는다.

- [ ] **Step 6: 대상 테스트 재실행**

Run: Step 3 명령.

Expected: PASS, final render status polling 없음.

---

### Task 7: 프로젝트 보관함에서 Director 큐·완료 섹션과 렌더 버전 표시

**Files:**
- Modify: `desktop/clipper_angular/src/core/history/project-history.service.ts`
- Modify: `desktop/clipper_angular/src/shell/projects/models/projects-view.ts`
- Modify: `desktop/clipper_angular/src/shell/projects/projects/projects.component.ts`
- Modify: `desktop/clipper_angular/src/shell/projects/projects-history-list/projects-history-list.component.ts`
- Modify: `desktop/clipper_angular/src/shell/projects/projects-detail-page/projects-detail-page.component.ts`
- Modify: `desktop/clipper_angular/src/shell/projects/projects-detail-page/projects-detail-page.component.html`
- Modify: `desktop/clipper_angular/src/shell/projects/projects-detail-page/projects-detail-page.component.scss`
- Test: `desktop/clipper_angular/src/shell/projects/projects/projects.component.spec.ts`
- Test: `desktop/clipper_angular/src/shell/projects/projects-history-list/projects-history-list.component.spec.ts`
- Test: `desktop/clipper_angular/src/shell/projects/projects-detail-page/projects-detail-page.component.spec.ts`

**Interfaces:**
- Produces: `ProjectJobCardView.featureName`
- `effectiveFeatureName(job)` returns `shortform_director` only when trusted
  origin metadata says so; otherwise it preserves existing classification.
- Consumes: `ProjectDetail.category === 'shortform_director'` and
  `detail.renders`.

- [ ] **Step 1: 큐·완료 섹션 분류 테스트 작성**

```ts
it('labels a Clipper executor job from Director as AI 숏폼 디렉터');
it('groups completed Director renders outside the 클리퍼 section');
it('sorts the Director section by installed feature order');
it('collapses rerender jobs for one archive project into one completed card');
```

- [ ] **Step 2: Director 상세 버전 테스트 작성**

두 render item이 있는 상세 fixture로 최신 영상이 기본 선택되고 이전
버전 버튼을 누르면 해당 `videoUrl`이 재생되는지 확인한다.

- [ ] **Step 3: 대상 테스트 실패 확인**

Run:

```bash
cd desktop/clipper_angular
npm test -- --watch=false --browsers=ChromeHeadless \
  --include=src/shell/projects/projects/projects.component.spec.ts \
  --include=src/shell/projects/projects-history-list/projects-history-list.component.spec.ts \
  --include=src/shell/projects/projects-detail-page/projects-detail-page.component.spec.ts
```

Expected: 현재 모든 `clipper_video_render`가 `클리퍼`로 분류되어 FAIL.

- [ ] **Step 4: 출처 기능 기준 카드 분류 구현**

```ts
private effectiveFeatureName(job: PipelineJobSnapshot): string {
  return job.pluginName === 'clipper_video_render'
    && job.params['origin_feature_name'] === 'shortform_director'
      ? 'shortform_director'
      : job.pluginName;
}
```

`cardPluginLabel`, section key, feature order가 이 값을 사용하게 한다.
기존 Variation 우선 분류와 일반 Clipper 합치기 규칙은 유지한다.

- [ ] **Step 5: 한 프로젝트 카드와 Director 상세 구현**

같은 `archive_project_id`를 가진 terminal job은 최신 완료 project 카드
하나로 접는다. 상세 페이지의 `shortform_director` 분기에서는
`detail.renders`를 최신순으로 표시하고 선택한 video URL을 재생한다.

- [ ] **Step 6: 대상 테스트와 Angular build 재실행**

Run: Step 3 명령.

Expected: PASS.

Run:

```bash
cd desktop/clipper_angular
npm run build
```

Expected: build 성공.

---

### Task 8: 통합 회귀 검증

**Files:**
- Verify only; 구현 과정에서 변경한 파일 외 추가 수정 금지.

**Interfaces:**
- Verifies all earlier task contracts together.

- [ ] **Step 1: NestJS Director·Jobs·Projects 관련 테스트 실행**

Run:

```bash
cd desktop/clipper_nestjs
npm run build
node --test \
  test/jobs-terminal-wait.test.js \
  test/jobs-commit-phase.test.js \
  test/project-output-render-path.test.js \
  test/project-file-media-ticket.test.js \
  test/shortform-project-api.test.js \
  test/shortform-director-clipper-render-adapter.test.js \
  test/shortform-director-final-render-service.test.js \
  test/shortform-director-project-archive.test.js \
  test/shortform-director-render-contract.test.js \
  test/template-builder-full-family.test.js
```

Expected: 모두 PASS.

- [ ] **Step 2: Angular 관련 전체 spec 실행**

Run:

```bash
cd desktop/clipper_angular
npm test -- --watch=false --browsers=ChromeHeadless \
  --include=src/features/template-builder/**/*.spec.ts \
  --include=src/features/shortform-director/**/*.spec.ts \
  --include=src/shell/projects/**/*.spec.ts
```

Expected: 모두 PASS.

- [ ] **Step 3: 일반 빌드 실행**

Run:

```bash
cd desktop/clipper_nestjs
npm run build
cd ../clipper_angular
npm run build
```

Expected: 두 build 성공. 패키징 명령은 실행하지 않는다.

- [ ] **Step 4: 정적 금지 패턴 확인**

Run:

```bash
rg -n "pollFinalRender|for \\(let attempt = 0; attempt < 240|setTimeout\\(resolve, 1000\\)" \
  desktop/clipper_angular/src/features/shortform-director \
  desktop/clipper_nestjs/src/modules/shortform
```

Expected: 최종 렌더 상태 감시 polling 결과 없음.

- [ ] **Step 5: 변경 범위 확인**

Run:

```bash
git -C desktop/clipper_nestjs diff --check
git -C desktop/clipper_angular diff --check
git -C desktop/clipper_nestjs status --short
git -C desktop/clipper_angular status --short
```

Expected: 공백 오류 없음. 관련 없는 사용자 변경은 그대로 보존됨.
