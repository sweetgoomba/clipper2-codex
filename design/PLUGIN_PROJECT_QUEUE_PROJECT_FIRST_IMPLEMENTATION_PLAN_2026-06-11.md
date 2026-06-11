# Project-First Plugin Queue Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the app toward the confirmed product model where users see Plugin and Project only, and queue/archive cards are Project-centered while existing `/jobs`, `VideoRenderJob`, and Python runtime `/jobs` remain internal execution layers.

**Architecture:** Phase 1 adds a Project-first facade over current execution systems instead of deleting `/jobs` or renaming `WorkflowExecutor` in one broad diff. Backend Projects become capable of draft/queued/running/completed/failed/cancelled states and can create ProjectRun records that wrap existing PipelineJob or VideoRenderJob executions. Angular consumes Project-centered view models and maps raw worker render messages to product messages such as `영상 생성 중`.

**Tech Stack:** NestJS 10, TypeScript 5.7, Node test runner, Angular 19 standalone/signals, Karma/Jasmine, existing JSON repositories.

---

## Current Status

Status as of 2026-06-11: **not started**.

This is a future implementation plan, not work completed in the current
shortform legacy parity session. The agreed execution order is:

1. Finish the shortform legacy UI/pre-render parity port first.
2. Only after that is stable and approved, start this Project-first / Plugin /
   Queue terminology and model cleanup.

Do not begin this plan while the shortform legacy parity work is still open.
In particular, do not mix Project-first queue changes into the shortform UI
port. The shortform phase may keep the existing Clipper2 shortform APIs and
current `/jobs`/render compatibility layers.

## Scope Guard

This plan is Phase 1. It does not remove `/jobs`, delete `VideoRenderJob`, or rename `WorkflowExecutor` globally. Those names remain current implementation details until Project-first behavior is stable.

When this plan is executed later, it implements:

- User plugin vs hidden runtime worker classification.
- Project status expansion from completed-only to Project lifecycle states.
- Generic Project creation for plugin-backed projects.
- Project queue endpoints that create internal execution runs while presenting Project state externally.
- Public progress message mapping.
- Angular project-card view model that removes the need for synthetic job cards.
- Documentation updates after code changes.

Do not commit automatically while executing this plan. The `.codex` repo currently has unrelated `implementation/*` deleted files, and app repos may have user changes. Use verification checkpoints and ask before any commit.

## File Structure

### Backend: `clipper_nestjs`

- Modify `src/plugins/dto/plugin.dto.ts`
  - Add plugin catalog classification fields used by API consumers.
- Modify `src/plugins/plugin-catalog.ts`
  - Mark user-facing plugins and hidden workers explicitly.
- Modify `src/plugins/plugins.service.ts`
  - Preserve existing list behavior, but expose classification metadata in manifests.
- Modify `src/projects/dto/project.dto.ts`
  - Expand `ProjectStatus`.
  - Add generic `CreateProjectRequest`.
  - Add `ProjectRunSnapshot`, `ProjectRunStatus`, `ProjectRunKind`, `QueueProjectRequest`.
- Modify `src/projects/project-repository.ts`
  - Normalize old completed-only projects on read.
- Create `src/projects/project-run-repository.ts`
  - Store ProjectRun snapshots in `$CLIPPER_DATA_DIR/project-runs/project-runs.json`.
- Modify `src/projects/projects.module.ts`
  - Register the ProjectRun repository.
- Modify `src/projects/projects.service.ts`
  - Add generic plugin project creation.
  - Add Project queue/cancel/retry/run-list methods.
  - Update project status from PipelineJob completion and render job start.
- Modify `src/projects/projects.controller.ts`
  - Add generic `/projects` create and project queue endpoints.
- Modify `src/jobs/jobs.service.ts`
  - Publish Project status changes when internal PipelineJob progresses.
- Modify `src/project-manifest/video-render-jobs.service.ts`
  - Allow callers to pass public message mapping or expose enough state for ProjectsService to map render progress.
- Create or modify tests:
  - `test/project-first-queue.test.js`
  - `test/workflow-executor-registry.test.js`
  - `test/shortform-project-api.test.js`

### Frontend: `clipper_angular`

- Modify `src/core/clipper-bridge.ts`
  - Add plugin classification fields to `PluginManifestView`.
- Modify `src/core/plugin-status.service.ts`
  - Use backend manifest classification where available.
  - Keep current local fallback for known plugins.
- Modify `src/core/project-history.service.ts`
  - Expand Project status type.
  - Add ProjectRun types and queue/cancel/retry methods.
  - Add public render message helper or consume it from a shell helper.
- Create `src/shell/projects/project-card-view.ts`
  - Convert `ProjectSnapshot`, optional ProjectRun, and optional render job into user-facing project card state.
- Create `src/shell/projects/project-card-view.spec.ts`
  - Test Project-first card behavior and render message simplification.
- Modify `src/shell/projects/projects.component.ts`
  - Use Project-centered card views.
  - Remove `syntheticProjectJobs`.
  - Keep `JobHistoryService` only as an internal bridge during migration.
- Modify `src/shell/projects/projects-detail-panel.component.html`
  - Stop showing raw render job messages.
- Modify `src/features/shortform/pages/shortform-workflow-page.component.ts`
  - Replace raw `response.renderJob.message` display with product copy.
- Modify tests:
  - `src/core/plugin-status.service.spec.ts`
  - `src/core/project-history.service.spec.ts`
  - `src/shell/projects/project-card-view.spec.ts`

### Documentation: `.codex`

- Modify `design/PLUGIN_PROJECT_QUEUE_TERMINOLOGY_2026-06-11.md`
  - Add implementation progress notes after code changes.
- Modify `handoff/NEXT.md`
  - Record the completed phase and verification.
- Modify or append `records/sessions/2026/06/11.md`
  - Record implementation result and commands.

---

## Task 1: Plugin Classification Metadata

**Files:**

- Modify: `clipper_nestjs/src/plugins/dto/plugin.dto.ts`
- Modify: `clipper_nestjs/src/plugins/plugin-catalog.ts`
- Modify: `clipper_angular/src/core/clipper-bridge.ts`
- Modify: `clipper_angular/src/core/plugin-status.service.ts`
- Test: `clipper_angular/src/core/plugin-status.service.spec.ts`
- Test: `clipper_nestjs/test/workflow-executor-registry.test.js`

- [ ] **Step 1: Add the backend DTO field**

Add this type and field to `clipper_nestjs/src/plugins/dto/plugin.dto.ts`:

```ts
export type PluginCatalogKind =
  | 'user_plugin'
  | 'runtime_worker'
  | 'internal_executor';

export interface PluginManifestView {
  name: string;
  version: string;
  displayName: string;
  description: string;
  author?: string;
  runtimeKind?: 'python_plugin' | 'nestjs_executor' | 'virtual_workflow';
  catalogKind?: PluginCatalogKind;
  storeVisible?: boolean;
  dashboardVisible?: boolean;
  capabilities?: {
    provides: string[];
    requires: string[];
  };
  // keep the existing resourceProfile/models fields unchanged
}
```

- [ ] **Step 2: Classify known catalog entries**

In `clipper_nestjs/src/plugins/plugin-catalog.ts`, set these fields:

```ts
shortform_url: {
  // existing fields
  catalogKind: 'user_plugin',
  storeVisible: true,
  dashboardVisible: false,
},
shortform_paste: {
  // existing fields
  catalogKind: 'user_plugin',
  storeVisible: true,
  dashboardVisible: false,
},
shortform_prompt: {
  // existing fields
  catalogKind: 'user_plugin',
  storeVisible: true,
  dashboardVisible: false,
},
dance_highlight: {
  // existing fields
  catalogKind: 'user_plugin',
  storeVisible: true,
  dashboardVisible: true,
},
dialog_highlight: {
  // existing fields
  catalogKind: 'user_plugin',
  storeVisible: true,
  dashboardVisible: true,
},
clipper1_video_render: {
  // existing fields
  catalogKind: 'runtime_worker',
  storeVisible: false,
  dashboardVisible: true,
},
```

If `simple_ffmpeg_transform` exposes a manifest in its executor, set `catalogKind: 'internal_executor'`, `storeVisible: false`, and `dashboardVisible: false` in that manifest.

- [ ] **Step 3: Extend Angular manifest type**

In `clipper_angular/src/core/clipper-bridge.ts`, add matching optional fields:

```ts
export type PluginCatalogKind =
  | 'user_plugin'
  | 'runtime_worker'
  | 'internal_executor';

export interface PluginManifestView {
  name: string;
  version: string;
  displayName: string;
  description: string;
  author?: string;
  runtimeKind?: 'python_plugin' | 'nestjs_executor' | 'virtual_workflow';
  catalogKind?: PluginCatalogKind;
  storeVisible?: boolean;
  dashboardVisible?: boolean;
  // keep existing fields unchanged
}
```

- [ ] **Step 4: Update Angular filtering**

In `clipper_angular/src/core/plugin-status.service.ts`, make the service prefer backend fields and fall back to current local sets:

```ts
function isStoreVisibleItem(item: PluginStoreItem): boolean {
  if (typeof item.manifest.storeVisible === 'boolean') return item.manifest.storeVisible;
  return USER_VISIBLE_PLUGINS.has(item.name);
}

function isRuntimeDashboardItem(item: PluginStoreItem): boolean {
  if (typeof item.manifest.dashboardVisible === 'boolean') return item.manifest.dashboardVisible;
  return isRuntimeStatusPlugin(item.name);
}
```

Use these helpers inside `userVisibleItems()` and `runtimeStatusItems()`.

- [ ] **Step 5: Add/update tests**

In `clipper_angular/src/core/plugin-status.service.spec.ts`, update the runtime status list test so the mock response includes backend classification:

```ts
req.flush([
  {
    manifest: { ...manifest('shortform_url', 'URL로 숏폼 제작'), catalogKind: 'user_plugin', storeVisible: true, dashboardVisible: false },
    status: status('shortform_url'),
  },
  {
    manifest: { ...manifest('shortform_paste', '붙여넣기로 숏폼 제작'), catalogKind: 'user_plugin', storeVisible: true, dashboardVisible: false },
    status: status('shortform_paste'),
  },
  {
    manifest: { ...manifest('shortform_prompt', '프롬프트로 숏폼 제작'), catalogKind: 'user_plugin', storeVisible: true, dashboardVisible: false },
    status: status('shortform_prompt'),
  },
  {
    manifest: { ...manifest('clipper1_video_render', '숏폼 렌더 워커'), catalogKind: 'runtime_worker', storeVisible: false, dashboardVisible: true },
    status: status('clipper1_video_render'),
  },
  {
    manifest: { ...manifest('dialog_highlight', '대사 중심 영상 하이라이트 추출'), catalogKind: 'user_plugin', storeVisible: true, dashboardVisible: true },
    status: status('dialog_highlight'),
  },
]);
```

Expected assertions remain:

```ts
expect(service.items().map((item) => item.name)).toEqual([
  'shortform_url',
  'shortform_paste',
  'shortform_prompt',
  'dialog_highlight',
]);
expect(service.runtimeItems().map((item) => item.name)).toEqual([
  'clipper1_video_render',
  'dialog_highlight',
]);
```

In `clipper_nestjs/test/workflow-executor-registry.test.js`, assert catalog classification:

```js
assert.equal((await registry.get('shortform_prompt')).runtimeKind, 'virtual_workflow');
const shortformManifest = await (await registry.get('shortform_prompt')).getManifest();
assert.equal(shortformManifest.catalogKind, 'user_plugin');
assert.equal(shortformManifest.storeVisible, true);

const renderManifest = await (await registry.get('clipper1_video_render')).getManifest();
assert.equal(renderManifest.catalogKind, 'runtime_worker');
assert.equal(renderManifest.storeVisible, false);
```

- [ ] **Step 6: Verify**

Run:

```bash
cd /Users/jina/project/adlight/clipper_nestjs
npm run build
node --test test/workflow-executor-registry.test.js
```

Expected:

```text
npm run build exits 0
workflow-executor-registry tests pass
```

Run:

```bash
cd /Users/jina/project/adlight/clipper_angular
npm test -- --watch=false --include=src/core/plugin-status.service.spec.ts
```

Expected:

```text
Chrome ... Executed ... SUCCESS
```

---

## Task 2: Project Lifecycle DTOs And Repository Compatibility

**Files:**

- Modify: `clipper_nestjs/src/projects/dto/project.dto.ts`
- Modify: `clipper_nestjs/src/projects/project-repository.ts`
- Modify: `clipper_angular/src/core/project-history.service.ts`
- Test: `clipper_nestjs/test/project-first-queue.test.js`
- Test: `clipper_angular/src/core/project-history.service.spec.ts`

- [ ] **Step 1: Expand backend Project status**

Change `clipper_nestjs/src/projects/dto/project.dto.ts`:

```ts
export type ProjectStatus =
  | 'draft'
  | 'queued'
  | 'running'
  | 'completed'
  | 'failed'
  | 'cancelled';
```

Change `ProjectSnapshot` fields so active projects can exist:

```ts
export interface ProjectSnapshot {
  projectId: string;
  jobId: string;
  ownerSubjectId: string;
  pluginName: string;
  status: ProjectStatus;
  title: string;
  sourceVideoPath: string | null;
  sourceAssets: SourceAsset[];
  outputRoot: string | null;
  params: Record<string, unknown>;
  result: Record<string, unknown>;
  artifacts: ProjectArtifact[];
  progress?: number;
  message?: string;
  error?: string | null;
  createdAt: string;
  updatedAt: string;
  completedAt?: string;
}
```

Add generic project creation and queue DTOs:

```ts
export interface CreateProjectRequest {
  pluginName: string;
  title?: string;
  params?: Record<string, unknown>;
}

export type ProjectRunKind =
  | 'pipeline'
  | 'render'
  | 'draft';

export type ProjectRunStatus =
  | 'queued'
  | 'running'
  | 'succeeded'
  | 'failed'
  | 'cancelled';

export interface ProjectRunSnapshot {
  runId: string;
  projectId: string;
  ownerSubjectId: string;
  kind: ProjectRunKind;
  status: ProjectRunStatus;
  progress: number;
  publicMessage: string;
  runtimeMessage?: string;
  internalJobId?: string;
  internalJobKind?: 'pipeline_job' | 'video_render_job' | 'python_runtime_job';
  result: Record<string, unknown> | null;
  error: string | null;
  createdAt: string;
  startedAt?: string;
  finishedAt?: string;
}

export interface QueueProjectRequest {
  runId?: string;
  params?: Record<string, unknown>;
}
```

- [ ] **Step 2: Normalize old projects in repository**

In `clipper_nestjs/src/projects/project-repository.ts`, normalize optional fields when loading:

```ts
private normalizeProject(project: ProjectSnapshot): ProjectSnapshot {
  return {
    ...project,
    status: project.status ?? 'completed',
    sourceAssets: project.sourceAssets ?? [],
    result: project.result ?? {},
    artifacts: project.artifacts ?? [],
    progress: project.progress ?? (project.status === 'completed' ? 1 : 0),
    message: project.message ?? (project.status === 'completed' ? '완료' : undefined),
    error: project.error ?? null,
  };
}
```

Use it in `ensureLoaded()`:

```ts
for (const project of parsed.projects ?? []) {
  const normalized = this.normalizeProject(project);
  this.projects.set(normalized.projectId, normalized);
}
```

- [ ] **Step 3: Mirror Angular Project status**

In `clipper_angular/src/core/project-history.service.ts`, replace the completed-only status:

```ts
export type ProjectStatus =
  | 'draft'
  | 'queued'
  | 'running'
  | 'completed'
  | 'failed'
  | 'cancelled';
```

Update `ProjectSnapshot`:

```ts
export interface ProjectSnapshot {
  projectId: string;
  jobId: string;
  ownerSubjectId?: string;
  pluginName: string;
  status: ProjectStatus;
  title: string;
  sourceVideoPath: string | null;
  sourceAssets?: SourceAsset[];
  outputRoot: string | null;
  params: Record<string, unknown>;
  result: Record<string, unknown>;
  artifacts: ProjectArtifact[];
  progress?: number;
  message?: string;
  error?: string | null;
  createdAt: string;
  updatedAt: string;
  completedAt?: string;
}
```

Add ProjectRun interfaces matching backend DTO.

- [ ] **Step 4: Add a repository compatibility test**

Add `clipper_nestjs/test/project-first-queue.test.js` with the same server helper pattern as `shortform-project-api.test.js`. First test only verifies old completed project shape still lists:

```js
test('projects endpoint accepts lifecycle status fields', async () => {
  await withServer(async (baseUrl) => {
    const created = await json(await fetch(`${baseUrl}/projects`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        pluginName: 'dialog_highlight',
        title: '인터뷰 하이라이트',
        params: { source: { kind: 'file', path: '/tmp/interview.mp4' } },
      }),
    }));

    assert.equal(created.pluginName, 'dialog_highlight');
    assert.equal(created.status, 'draft');
    assert.equal(created.progress, 0);
    assert.equal(created.message, '프로젝트 준비됨');

    const projects = await json(await fetch(`${baseUrl}/projects`));
    assert.equal(projects.length, 1);
    assert.equal(projects[0].projectId, created.projectId);
  });
});
```

This test will fail until Task 3 adds generic create support.

- [ ] **Step 5: Verify type compilation**

Run:

```bash
cd /Users/jina/project/adlight/clipper_nestjs
npm run build
```

Expected:

```text
TypeScript build exits 0
```

Run:

```bash
cd /Users/jina/project/adlight/clipper_angular
npm run build
```

Expected:

```text
Angular build exits 0
```

---

## Task 3: Generic Project Creation Endpoint

**Files:**

- Modify: `clipper_nestjs/src/projects/projects.controller.ts`
- Modify: `clipper_nestjs/src/projects/projects.service.ts`
- Test: `clipper_nestjs/test/project-first-queue.test.js`
- Modify: `clipper_angular/src/core/project-history.service.ts`
- Test: `clipper_angular/src/core/project-history.service.spec.ts`

- [ ] **Step 1: Add backend service method**

In `clipper_nestjs/src/projects/projects.service.ts`, add:

```ts
async createProject(
  request: CreateProjectRequest,
  auth: AuthContext,
): Promise<ProjectSnapshot> {
  const now = new Date().toISOString();
  const pluginName = String(request.pluginName ?? '').trim();
  if (!pluginName) {
    throw new BadRequestException('pluginName is required');
  }

  const projectId = `${pluginName}_project_${Date.now()}`;
  const title = request.title?.trim() || this.defaultProjectTitle(pluginName, request.params ?? {});

  const project: ProjectSnapshot = {
    projectId,
    jobId: projectId,
    ownerSubjectId: auth.subjectId,
    pluginName,
    status: 'draft',
    title,
    sourceVideoPath: null,
    sourceAssets: [],
    outputRoot: this.outputRootFor(auth.subjectId, projectId),
    params: request.params ?? {},
    result: {},
    artifacts: [],
    progress: 0,
    message: '프로젝트 준비됨',
    error: null,
    createdAt: now,
    updatedAt: now,
  };

  return this.repository.upsert(project);
}
```

If `outputRootFor()` is private and already exists, reuse it. If it is named differently, use the existing method that creates project output roots.

Add this helper near other private format helpers:

```ts
private defaultProjectTitle(pluginName: string, params: Record<string, unknown>): string {
  const explicitTitle = typeof params['title'] === 'string' ? params['title'].trim() : '';
  if (explicitTitle) return explicitTitle;
  if (pluginName === 'dialog_highlight') return '대사 하이라이트 프로젝트';
  if (pluginName === 'dance_highlight') return '안무 하이라이트 프로젝트';
  if (pluginName === 'shortform_prompt') return '프롬프트 숏폼 프로젝트';
  if (pluginName === 'shortform_url') return 'URL 숏폼 프로젝트';
  if (pluginName === 'shortform_paste') return '붙여넣기 숏폼 프로젝트';
  if (pluginName === 'variation') return '베리에이션 프로젝트';
  return '새 프로젝트';
}
```

- [ ] **Step 2: Add controller endpoint**

In `clipper_nestjs/src/projects/projects.controller.ts`, import `CreateProjectRequest` and add this route after `@Get()` list and before specific `clipper-studio` routes:

```ts
@Post()
create(
  @Body() body: CreateProjectRequest,
  @Headers() headers: IncomingHttpHeaders,
): Promise<ProjectSnapshot> {
  return this.authContext.fromHttpHeaders(headers).then((auth) =>
    this.projects.createProject(body, auth),
  );
}
```

- [ ] **Step 3: Add Angular service method**

In `clipper_angular/src/core/project-history.service.ts`, add:

```ts
export interface CreateProjectRequest {
  pluginName: string;
  title?: string;
  params?: Record<string, unknown>;
}
```

Add method:

```ts
async createProject(request: CreateProjectRequest): Promise<ProjectSnapshot> {
  const base = await this.backend.getBaseUrl();
  const project = await firstValueFrom(
    this.http.post<ProjectSnapshot>(`${base}/projects`, request),
  );
  this.projects.update((items) => [project, ...items.filter((item) => item.projectId !== project.projectId)]);
  return project;
}
```

- [ ] **Step 4: Add Angular test**

In `clipper_angular/src/core/project-history.service.spec.ts`:

```ts
it('creates a plugin project through the generic projects endpoint', async () => {
  const promise = service.createProject({
    pluginName: 'dialog_highlight',
    title: '인터뷰 하이라이트',
    params: { source: { kind: 'file', path: '/tmp/interview.mp4' } },
  });

  await Promise.resolve();
  const req = http.expectOne('http://127.0.0.1:19019/v1/projects');
  expect(req.request.method).toBe('POST');
  expect(req.request.body.pluginName).toBe('dialog_highlight');

  req.flush({
    projectId: 'dialog_highlight_project_1',
    jobId: 'dialog_highlight_project_1',
    ownerSubjectId: 'local-user',
    pluginName: 'dialog_highlight',
    status: 'draft',
    title: '인터뷰 하이라이트',
    sourceVideoPath: null,
    sourceAssets: [],
    outputRoot: null,
    params: req.request.body.params,
    result: {},
    artifacts: [],
    progress: 0,
    message: '프로젝트 준비됨',
    error: null,
    createdAt: '2026-06-11T00:00:00.000Z',
    updatedAt: '2026-06-11T00:00:00.000Z',
  });

  const project = await promise;
  expect(project.status).toBe('draft');
  expect(service.projects()[0].projectId).toBe('dialog_highlight_project_1');
});
```

- [ ] **Step 5: Verify**

Run:

```bash
cd /Users/jina/project/adlight/clipper_nestjs
npm run build
node --test test/project-first-queue.test.js
```

Expected:

```text
Build exits 0
project-first-queue create test passes
```

Run:

```bash
cd /Users/jina/project/adlight/clipper_angular
npm test -- --watch=false --include=src/core/project-history.service.spec.ts
```

Expected:

```text
ProjectHistoryService specs pass
```

---

## Task 4: ProjectRun Repository And Queue Endpoint For Pipeline Plugins

**Files:**

- Create: `clipper_nestjs/src/projects/project-run-repository.ts`
- Modify: `clipper_nestjs/src/projects/projects.module.ts`
- Modify: `clipper_nestjs/src/projects/projects.controller.ts`
- Modify: `clipper_nestjs/src/projects/projects.service.ts`
- Modify: `clipper_nestjs/src/jobs/jobs.service.ts`
- Test: `clipper_nestjs/test/project-first-queue.test.js`

- [ ] **Step 1: Create ProjectRun repository**

Create `clipper_nestjs/src/projects/project-run-repository.ts`:

```ts
import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { ProjectRunSnapshot } from './dto/project.dto';

interface ProjectRunStoreFile {
  version: 1;
  runs: ProjectRunSnapshot[];
}

export abstract class ProjectRunRepository {
  abstract list(projectId: string): Promise<ProjectRunSnapshot[]>;
  abstract get(runId: string): Promise<ProjectRunSnapshot | null>;
  abstract upsert(run: ProjectRunSnapshot): Promise<ProjectRunSnapshot>;
}

@Injectable()
export class JsonProjectRunRepository extends ProjectRunRepository {
  private loaded = false;
  private readonly runs = new Map<string, ProjectRunSnapshot>();
  private readonly storePath: string;

  constructor(config: ConfigService) {
    super();
    const dataRoot = config.get<string>('CLIPPER_DATA_DIR') ?? join(process.cwd(), '.clipper_data');
    this.storePath = join(dataRoot, 'project-runs', 'project-runs.json');
  }

  async list(projectId: string): Promise<ProjectRunSnapshot[]> {
    await this.ensureLoaded();
    return [...this.runs.values()]
      .filter((run) => run.projectId === projectId)
      .sort((a, b) => b.createdAt.localeCompare(a.createdAt));
  }

  async get(runId: string): Promise<ProjectRunSnapshot | null> {
    await this.ensureLoaded();
    return this.runs.get(runId) ?? null;
  }

  async upsert(run: ProjectRunSnapshot): Promise<ProjectRunSnapshot> {
    await this.ensureLoaded();
    this.runs.set(run.runId, run);
    await this.flush();
    return run;
  }

  private async ensureLoaded(): Promise<void> {
    if (this.loaded) return;
    try {
      const raw = await readFile(this.storePath, 'utf-8');
      const parsed = JSON.parse(raw) as ProjectRunStoreFile;
      for (const run of parsed.runs ?? []) {
        this.runs.set(run.runId, run);
      }
    } catch {
      // Missing or corrupt store: start empty. The next write recreates it.
    }
    this.loaded = true;
  }

  private async flush(): Promise<void> {
    await mkdir(dirname(this.storePath), { recursive: true });
    await writeFile(
      this.storePath,
      JSON.stringify({ version: 1, runs: [...this.runs.values()] }, null, 2),
      'utf-8',
    );
  }
}
```

- [ ] **Step 2: Register repository**

In `clipper_nestjs/src/projects/projects.module.ts`, add providers:

```ts
ProjectRunRepository,
{
  provide: ProjectRunRepository,
  useClass: JsonProjectRunRepository,
},
```

Use the exact provider style already used for `ProjectRepository`. If the file uses class providers directly, follow that local pattern.

- [ ] **Step 3: Add queue and run-list service methods**

Inject `ProjectRunRepository` and `JobsService` into `ProjectsService`. If adding `JobsService` creates a circular dependency, use `forwardRef` in `ProjectsModule` and `JobsModule`; keep the dependency one-way in method behavior.

Add:

```ts
async queueProject(
  projectId: string,
  request: QueueProjectRequest,
  auth: AuthContext,
): Promise<ProjectRunSnapshot> {
  const project = await this.get(projectId, auth);
  if (project.status === 'running' || project.status === 'queued') {
    throw new ConflictException('Project is already queued or running');
  }

  const now = new Date().toISOString();
  const runId = request.runId ?? `${projectId}_run_${Date.now()}`;
  const internalJobId = `${projectId}_${runId}`;
  const params = {
    ...project.params,
    ...(request.params ?? {}),
    project_id: project.projectId,
    title: project.title,
  };

  const run: ProjectRunSnapshot = {
    runId,
    projectId,
    ownerSubjectId: auth.subjectId,
    kind: 'pipeline',
    status: 'queued',
    progress: 0,
    publicMessage: '대기 중',
    runtimeMessage: undefined,
    internalJobId,
    internalJobKind: 'pipeline_job',
    result: null,
    error: null,
    createdAt: now,
  };

  await this.projectRuns.upsert(run);
  await this.repository.upsert({
    ...project,
    status: 'queued',
    progress: 0,
    message: '대기 중',
    error: null,
    updatedAt: now,
  });

  await this.jobs.start({
    pluginName: project.pluginName,
    jobId: internalJobId,
    params,
  }, auth);

  return run;
}

async listProjectRuns(projectId: string, auth: AuthContext): Promise<ProjectRunSnapshot[]> {
  await this.get(projectId, auth);
  return this.projectRuns.list(projectId);
}
```

- [ ] **Step 4: Add controller routes**

In `ProjectsController`:

```ts
@Post(':projectId/queue')
queue(
  @Param('projectId') projectId: string,
  @Body() body: QueueProjectRequest = {},
  @Headers() headers: IncomingHttpHeaders,
): Promise<ProjectRunSnapshot> {
  return this.authContext.fromHttpHeaders(headers).then((auth) =>
    this.projects.queueProject(projectId, body, auth),
  );
}

@Get(':projectId/runs')
listRuns(
  @Param('projectId') projectId: string,
  @Headers() headers: IncomingHttpHeaders,
): Promise<ProjectRunSnapshot[]> {
  return this.authContext.fromHttpHeaders(headers).then((auth) =>
    this.projects.listProjectRuns(projectId, auth),
  );
}
```

- [ ] **Step 5: Sync Project from PipelineJob progress**

In `JobsService.publish()` after the snapshot is updated, call a narrow `ProjectsService.recordJobProgress(updated)` method. Add the method in `ProjectsService`:

```ts
async recordJobProgress(job: PipelineJobSnapshot): Promise<void> {
  const projectId = typeof job.params['project_id'] === 'string' ? job.params['project_id'] : null;
  if (!projectId) return;

  const project = await this.repository.get(projectId);
  if (!project) return;

  const now = new Date().toISOString();
  const status = this.projectStatusFromPipelineJob(job.status);
  await this.repository.upsert({
    ...project,
    status,
    progress: job.progress,
    message: this.publicPipelineMessage(job.pluginName, job.message, status),
    error: job.error ?? null,
    result: job.result ?? project.result,
    updatedAt: now,
    ...(status === 'completed' ? { completedAt: job.finishedAt ?? now } : {}),
  });
}
```

Add helpers:

```ts
private projectStatusFromPipelineJob(status: PipelineJobStatus): ProjectStatus {
  if (status === 'waiting' || status === 'starting') return 'queued';
  if (status === 'running') return 'running';
  if (status === 'completed') return 'completed';
  if (status === 'cancelled') return 'cancelled';
  return 'failed';
}

private publicPipelineMessage(
  pluginName: string,
  runtimeMessage: string,
  status: ProjectStatus,
): string {
  if (status === 'queued') return '대기 중';
  if (status === 'completed') return '완료';
  if (status === 'failed') return '실패';
  if (status === 'cancelled') return '취소됨';
  return runtimeMessage || '처리 중';
}
```

This preserves detailed highlight messages because `runtimeMessage` is used for running pipeline jobs.

- [ ] **Step 6: Add queue test**

In `clipper_nestjs/test/project-first-queue.test.js`, add:

```js
test('queueing a plugin project creates a ProjectRun and marks the project queued', async () => {
  await withServer(async (baseUrl) => {
    const project = await json(await fetch(`${baseUrl}/projects`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        pluginName: 'dialog_highlight',
        title: '인터뷰 하이라이트',
        params: { video_path: '/tmp/interview.mp4' },
      }),
    }));

    const run = await json(await fetch(`${baseUrl}/projects/${project.projectId}/queue`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ runId: 'run_test_1' }),
    }));

    assert.equal(run.projectId, project.projectId);
    assert.equal(run.kind, 'pipeline');
    assert.equal(run.status, 'queued');
    assert.equal(run.internalJobKind, 'pipeline_job');

    const updated = await json(await fetch(`${baseUrl}/projects/${project.projectId}`));
    assert.equal(updated.status, 'queued');
    assert.equal(updated.message, '대기 중');

    const runs = await json(await fetch(`${baseUrl}/projects/${project.projectId}/runs`));
    assert.equal(runs.length, 1);
    assert.equal(runs[0].runId, 'run_test_1');
  });
}, { PLUGIN_URLS: '{}' });
```

If queuing starts real plugin execution and fails because no plugin runtime is available, keep the test focused by using a fake NestJS executor plugin such as `simple_ffmpeg_transform` with harmless params, or inject `PLUGIN_URLS` only if the current test runtime supports it. The expected behavior is that Project and ProjectRun are persisted before runtime execution completes.

- [ ] **Step 7: Verify**

Run:

```bash
cd /Users/jina/project/adlight/clipper_nestjs
npm run build
node --test test/project-first-queue.test.js
```

Expected:

```text
Build exits 0
Project creation and queue tests pass
```

---

## Task 5: Public Render Progress Mapping

**Files:**

- Modify: `clipper_angular/src/core/project-history.service.ts`
- Create: `clipper_angular/src/shell/projects/project-progress-presenter.ts`
- Create: `clipper_angular/src/shell/projects/project-progress-presenter.spec.ts`
- Modify: `clipper_angular/src/shell/projects/projects-detail-panel.component.html`
- Modify: `clipper_angular/src/shell/projects/projects-detail-panel.component.ts`
- Modify: `clipper_angular/src/features/shortform/pages/shortform-workflow-page.component.ts`

- [ ] **Step 1: Create presenter helper**

Create `clipper_angular/src/shell/projects/project-progress-presenter.ts`:

```ts
import type { VideoRenderJobSnapshot } from '../../core/project-history.service';

export function publicRenderJobMessage(job: VideoRenderJobSnapshot | null | undefined): string {
  if (!job) return '';
  switch (job.status) {
    case 'queued':
    case 'running':
      return '영상 생성 중';
    case 'succeeded':
      return '영상 생성 완료';
    case 'failed':
      return '영상 생성 실패';
    case 'cancelled':
      return '영상 생성 취소됨';
    default:
      return '영상 생성 중';
  }
}
```

- [ ] **Step 2: Add presenter spec**

Create `clipper_angular/src/shell/projects/project-progress-presenter.spec.ts`:

```ts
import type { VideoRenderJobSnapshot } from '../../core/project-history.service';
import { publicRenderJobMessage } from './project-progress-presenter';

function renderJob(status: VideoRenderJobSnapshot['status'], message: string): VideoRenderJobSnapshot {
  return {
    jobId: `job_${status}`,
    ownerSubjectId: 'local-user',
    projectId: 'project_1',
    outputId: 'output_1',
    recipeId: 'recipe_1',
    templatePresetId: 'template_1',
    providerId: 'video.render.legacy_clipper1.python_worker',
    status,
    progress: status === 'succeeded' ? 1 : 0.5,
    message,
    result: null,
    error: null,
    createdAt: '2026-06-11T00:00:00.000Z',
    request: {},
    history: [],
  };
}

describe('publicRenderJobMessage', () => {
  it('hides raw render worker messages while running', () => {
    expect(publicRenderJobMessage(renderJob('running', 'Concatenating rendered clips')))
      .toBe('영상 생성 중');
  });

  it('maps terminal render states to product messages', () => {
    expect(publicRenderJobMessage(renderJob('succeeded', 'Render execution completed')))
      .toBe('영상 생성 완료');
    expect(publicRenderJobMessage(renderJob('failed', 'ffmpeg failed')))
      .toBe('영상 생성 실패');
    expect(publicRenderJobMessage(renderJob('cancelled', 'cancelled')))
      .toBe('영상 생성 취소됨');
  });
});
```

- [ ] **Step 3: Use presenter in detail panel**

In `projects-detail-panel.component.ts`, expose:

```ts
import { publicRenderJobMessage } from './project-progress-presenter';

renderJobPublicMessage(job: VideoRenderJobSnapshot): string {
  return publicRenderJobMessage(job);
}
```

In `projects-detail-panel.component.html`, replace:

```html
<small>{{ activeJob.message }}</small>
```

with:

```html
<small>{{ renderJobPublicMessage(activeJob) }}</small>
```

Replace latest job message the same way:

```html
<small>{{ renderJobPublicMessage(latestJob) }}</small>
```

- [ ] **Step 4: Simplify shortform render start message**

In `shortform-workflow-page.component.ts`, replace:

```ts
this.renderMessage.set(`렌더 작업 시작 · ${response.renderJob.message ?? response.renderJob.status}`);
```

with:

```ts
this.renderMessage.set('영상 생성이 시작되었습니다.');
```

- [ ] **Step 5: Verify**

Run:

```bash
cd /Users/jina/project/adlight/clipper_angular
npm test -- --watch=false --include=src/shell/projects/project-progress-presenter.spec.ts
npm run build
```

Expected:

```text
Presenter specs pass
Angular build exits 0
```

---

## Task 6: Project-Centered Card View And Synthetic Job Removal

**Files:**

- Create: `clipper_angular/src/shell/projects/project-card-view.ts`
- Create: `clipper_angular/src/shell/projects/project-card-view.spec.ts`
- Modify: `clipper_angular/src/shell/projects/projects.component.ts`
- Modify: `clipper_angular/src/shell/projects/projects-history-list.component.html`
- Modify: `clipper_angular/src/shell/projects/projects-detail-panel.component.html`

- [ ] **Step 1: Create Project card view helper**

Create `project-card-view.ts`:

```ts
import type { PipelineJobSnapshot } from '../../core/job-history.service';
import type { ProjectSnapshot, VideoRenderJobSnapshot } from '../../core/project-history.service';
import { publicRenderJobMessage } from './project-progress-presenter';

export interface ProjectCardView {
  id: string;
  project: ProjectSnapshot;
  activeJob?: PipelineJobSnapshot;
  activeRenderJob?: VideoRenderJobSnapshot;
  status: ProjectSnapshot['status'];
  title: string;
  subtitle: string;
  progress: number;
  message: string;
}

export function projectCardView(
  project: ProjectSnapshot,
  options: {
    activeJob?: PipelineJobSnapshot;
    activeRenderJob?: VideoRenderJobSnapshot;
  } = {},
): ProjectCardView {
  const activeRenderJob = options.activeRenderJob;
  const activeJob = options.activeJob;
  const progress = activeRenderJob?.progress ?? activeJob?.progress ?? project.progress ?? (project.status === 'completed' ? 1 : 0);
  const message = activeRenderJob
    ? publicRenderJobMessage(activeRenderJob)
    : activeJob?.message ?? project.message ?? statusMessage(project.status);

  return {
    id: project.projectId,
    project,
    activeJob,
    activeRenderJob,
    status: project.status,
    title: project.title,
    subtitle: pluginSubtitle(project.pluginName),
    progress,
    message,
  };
}

function statusMessage(status: ProjectSnapshot['status']): string {
  if (status === 'draft') return '프로젝트 준비됨';
  if (status === 'queued') return '대기 중';
  if (status === 'running') return '처리 중';
  if (status === 'completed') return '완료';
  if (status === 'failed') return '실패';
  if (status === 'cancelled') return '취소됨';
  return '프로젝트';
}

function pluginSubtitle(pluginName: string): string {
  if (pluginName === 'dialog_highlight') return '대사 중심 영상 하이라이트 추출';
  if (pluginName === 'dance_highlight') return '안무 영상 하이라이트 추출';
  if (pluginName === 'shortform_prompt') return '프롬프트로 숏폼 제작';
  if (pluginName === 'shortform_url') return 'URL로 숏폼 제작';
  if (pluginName === 'shortform_paste') return '붙여넣기로 숏폼 제작';
  if (pluginName === 'shortform') return '숏폼 영상 제작';
  return pluginName;
}
```

- [ ] **Step 2: Add helper spec**

Create `project-card-view.spec.ts`:

```ts
import type { ProjectSnapshot, VideoRenderJobSnapshot } from '../../core/project-history.service';
import { projectCardView } from './project-card-view';

function project(overrides: Partial<ProjectSnapshot> = {}): ProjectSnapshot {
  return {
    projectId: 'project_1',
    jobId: 'job_1',
    ownerSubjectId: 'local-user',
    pluginName: 'shortform_prompt',
    status: 'running',
    title: '여행 숏폼',
    sourceVideoPath: null,
    sourceAssets: [],
    outputRoot: null,
    params: {},
    result: {},
    artifacts: [],
    progress: 0.2,
    message: '처리 중',
    error: null,
    createdAt: '2026-06-11T00:00:00.000Z',
    updatedAt: '2026-06-11T00:00:00.000Z',
    ...overrides,
  };
}

function renderJob(message: string): VideoRenderJobSnapshot {
  return {
    jobId: 'render_1',
    ownerSubjectId: 'local-user',
    projectId: 'project_1',
    outputId: 'output_1',
    recipeId: 'recipe_1',
    templatePresetId: 'template_1',
    providerId: 'video.render.legacy_clipper1.python_worker',
    status: 'running',
    progress: 0.4,
    message,
    result: null,
    error: null,
    createdAt: '2026-06-11T00:00:00.000Z',
    request: {},
    history: [],
  };
}

describe('projectCardView', () => {
  it('uses project identity instead of synthetic job identity', () => {
    const view = projectCardView(project({ projectId: 'project_shortform_1', jobId: 'render_job_1' }));
    expect(view.id).toBe('project_shortform_1');
    expect(view.title).toBe('여행 숏폼');
  });

  it('hides raw render worker messages', () => {
    const view = projectCardView(project(), {
      activeRenderJob: renderJob('Concatenating rendered clips'),
    });
    expect(view.message).toBe('영상 생성 중');
    expect(view.progress).toBe(0.4);
  });
});
```

- [ ] **Step 3: Replace synthetic job computation**

In `projects.component.ts`, remove:

```ts
readonly syntheticProjectJobs = computed(...)
readonly historyJobs = computed(() => [...this.jobs.jobs(), ...this.syntheticProjectJobs()])
private syntheticJobForProject(...)
```

Add project-centered computed values:

```ts
readonly projectCardViews = computed(() => {
  const jobsByProjectId = new Map<string, PipelineJobSnapshot>();
  for (const job of this.jobs.jobs()) {
    const projectId = typeof job.params['project_id'] === 'string' ? job.params['project_id'] : null;
    if (projectId && this.isActiveStatus(job.status)) jobsByProjectId.set(projectId, job);
  }

  return this.projects.projects()
    .map((project) => projectCardView(project, {
      activeJob: jobsByProjectId.get(project.projectId),
      activeRenderJob: this.activeRenderJobForProject(project.projectId),
    }))
    .sort((a, b) => this.projectTimeValue(b.project) - this.projectTimeValue(a.project));
});

readonly activeProjectViews = computed(() =>
  this.projectCardViews().filter((view) =>
    view.project.status === 'queued' || view.project.status === 'running'
  ),
);

readonly completedProjectViews = computed(() =>
  this.projectCardViews().filter((view) =>
    view.project.status === 'completed' || view.project.status === 'failed' || view.project.status === 'cancelled'
  ),
);
```

Add helper:

```ts
private projectTimeValue(project: ProjectSnapshot): number {
  return new Date(project.completedAt ?? project.updatedAt ?? project.createdAt).getTime();
}
```

If current templates require `PipelineJobSnapshot`, keep a narrow adapter for selected detail only during this phase, but do not recreate synthetic jobs for list rendering.

- [ ] **Step 4: Update templates to use Project card views**

Update history list inputs and local template loops so cards render `ProjectCardView` fields:

```html
<strong>{{ item.title }}</strong>
<small>{{ item.subtitle }}</small>
<span>{{ item.message }}</span>
```

Keep existing CSS classes and status label helpers where possible. If a helper only accepts `PipelineJobStatus`, add a Project-specific helper instead of casting.

- [ ] **Step 5: Verify Angular**

Run:

```bash
cd /Users/jina/project/adlight/clipper_angular
npm test -- --watch=false --include=src/shell/projects/project-card-view.spec.ts --include=src/shell/projects/project-progress-presenter.spec.ts
npm run build
```

Expected:

```text
Project card and presenter specs pass
Angular build exits 0
```

---

## Task 7: Shortform Render Project State

**Files:**

- Modify: `clipper_nestjs/src/shortform/shortform-project.service.ts`
- Modify: `clipper_nestjs/test/shortform-project-api.test.js`
- Modify: `clipper_angular/src/features/shortform/services/shortform-project.service.ts`
- Modify: `clipper_angular/src/features/shortform/pages/shortform-workflow-page.component.ts`

- [ ] **Step 1: Preserve user plugin identity for shortform projects**

In `ShortformProjectService.startRender()`, set `ProjectSnapshot.pluginName` from the source project if available. For prompt-only current flow, use `shortform_prompt`:

```ts
const pluginName = current.source.mode === 'prompt'
  ? 'shortform_prompt'
  : current.source.mode === 'url'
    ? 'shortform_url'
    : current.source.mode === 'paste'
      ? 'shortform_paste'
      : 'shortform_prompt';
```

Use it in the project snapshot:

```ts
pluginName,
status: 'running',
progress: 0,
message: '영상 생성 중',
error: null,
```

Keep `result.workflow = 'shortform'` and manifest workflow id unchanged for compatibility.

- [ ] **Step 2: Update render response test**

In `test/shortform-project-api.test.js`, change:

```js
assert.equal(renderResponse.project.pluginName, 'shortform');
```

to:

```js
assert.equal(renderResponse.project.pluginName, 'shortform_prompt');
assert.equal(renderResponse.project.status, 'running');
assert.equal(renderResponse.project.message, '영상 생성 중');
```

Keep:

```js
assert.equal(renderResponse.project.result.workflow, 'shortform');
```

- [ ] **Step 3: Ensure completed render can update Project later**

If current `VideoRenderJobsService` does not notify `ProjectsService` on render completion, do not add a broad event system in this task. Instead, ensure Project detail UI derives active render status from `VideoRenderJobSnapshot` until a later backend event integration.

- [ ] **Step 4: Verify**

Run:

```bash
cd /Users/jina/project/adlight/clipper_nestjs
npm run build
node --test test/shortform-project-api.test.js
```

Expected:

```text
Build exits 0
shortform project API tests pass
```

---

## Task 8: Full Verification And Documentation Closeout

**Files:**

- Modify: `.codex/design/PLUGIN_PROJECT_QUEUE_TERMINOLOGY_2026-06-11.md`
- Modify: `.codex/handoff/NEXT.md`
- Modify: `.codex/records/sessions/2026/06/11.md`

- [ ] **Step 1: Run backend focused checks**

Run:

```bash
cd /Users/jina/project/adlight/clipper_nestjs
npm run build
node --test test/workflow-executor-registry.test.js test/project-first-queue.test.js test/shortform-project-api.test.js
```

Expected:

```text
Build exits 0
All listed node tests pass
```

- [ ] **Step 2: Run Angular focused checks**

Run:

```bash
cd /Users/jina/project/adlight/clipper_angular
npm test -- --watch=false --include=src/core/plugin-status.service.spec.ts --include=src/core/project-history.service.spec.ts --include=src/shell/projects/project-progress-presenter.spec.ts --include=src/shell/projects/project-card-view.spec.ts
npm run build
```

Expected:

```text
Focused Angular specs pass
Angular build exits 0
```

- [ ] **Step 3: Run diff checks**

Run:

```bash
cd /Users/jina/project/adlight/clipper_nestjs
git diff --check

cd /Users/jina/project/adlight/clipper_angular
git diff --check

cd /Users/jina/project/adlight/.codex
git diff --check
```

Expected:

```text
All three commands exit 0
```

- [ ] **Step 4: Update documentation after this future implementation**

When this plan is executed later, append an implementation status section to
`.codex/design/PLUGIN_PROJECT_QUEUE_TERMINOLOGY_2026-06-11.md`. Do not add this
status while the plan is still unstarted.

```md
## Project-first Implementation Status

- Record the actual implemented Project-first changes here.
- Include only changes that were implemented and verified in that later phase.
- Do not mark Project-first work complete while shortform legacy parity is still open.
```

Append verification commands and results to the active session record only after
the implementation and verification commands have actually run.

Update `.codex/handoff/NEXT.md` latest section with a completed status only
after the implementation is finished and verified. Future template:

```md
Project-first implementation:

- Record the actual completed Project-first changes here.
- Include only verified changes from that later implementation phase.
- Verification:
  - `clipper_nestjs npm run build`: exit 0 after implementation
  - `clipper_nestjs node --test test/workflow-executor-registry.test.js test/project-first-queue.test.js test/shortform-project-api.test.js`: exit 0 after implementation
  - `clipper_angular npm test -- --watch=false --include=src/core/plugin-status.service.spec.ts --include=src/core/project-history.service.spec.ts --include=src/shell/projects/project-progress-presenter.spec.ts --include=src/shell/projects/project-card-view.spec.ts`: exit 0 after implementation
  - `clipper_angular npm run build`: exit 0 after implementation
```

If any command exits nonzero, record the failing command and do not mark the phase complete.

- [ ] **Step 5: Report worktree status**

Run:

```bash
cd /Users/jina/project/adlight/clipper_nestjs
git status --short

cd /Users/jina/project/adlight/clipper_angular
git status --short

cd /Users/jina/project/adlight/.codex
git status --short
```

Expected:

```text
Only task-related changes plus pre-existing unrelated .codex implementation deletions are present.
```

## Self-Review Checklist

- Spec coverage:
  - User terms Plugin/Project are reflected in plugin classification and Project card views.
  - `shortform_prompt`, `shortform_url`, `shortform_paste` remain separate user plugins.
  - Queue user unit becomes Project via Project lifecycle status and ProjectRun facade.
  - `clipper1_video_render` is classified as hidden runtime worker.
  - Highlight analysis detailed messages remain visible.
  - Render worker messages are mapped to `영상 생성 중` style product copy.
- Scope check:
  - Global renaming of `WorkflowExecutor`, deletion of `/jobs`, and full render-completion event integration are outside Phase 1.
  - Existing runtime infrastructure is reused.
- Verification:
  - Backend build and focused Node tests.
  - Angular focused specs and build.
  - `git diff --check` for touched repos.
