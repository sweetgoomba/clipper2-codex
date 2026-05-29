# Workflow Executor Plugin Runtime Design

작성 기준: 2026-05-29

## 목적

현재 Clipper2의 runtime plugin은 사실상 Python HTTP/WS process를 전제로 한다. `dance_highlight`, `dialog_highlight`, `clipper1_video_render`는 모두 `clipper_python/plugins/*` manifest를 가진 Python runtime plugin이다.

앞으로는 간단한 ffmpeg 처리처럼 NestJS 안에서 직접 실행하는 workflow도 Plugin Store, job history, start/stop/status 모델에 같은 방식으로 보여야 한다.

이 문서는 그 확장을 위한 설계다.

## 구현 현황

2026-05-29 기준 `clipper_nestjs`의 `design/workflow-executor` 브랜치에서 초기 구현을 진행했고, `ceaa6ab Add workflow executor runtime dispatch`로 커밋했다.

구현된 범위:

- `src/workflows/` 아래에 `WorkflowExecutor` interface, registry, Python adapter, virtual workflow executor를 추가했다.
- 기존 `JobsService`의 Python `/jobs` submit + WebSocket event 처리 로직을 `PythonPluginWorkflowExecutor`로 이동했다.
- `JobsService`는 `PluginHost` 대신 `WorkflowExecutorRegistry`에서 executor를 찾아 `run(context)`를 호출한다.
- `PluginsService`는 `PluginHost`와 virtual catalog를 직접 섞지 않고 `WorkflowExecutorRegistry`를 통해 list/status/start/stop을 만든다.
- `PluginManifestView.runtimeKind`를 추가했고, catalog/local manifest에 `python_plugin`, `virtual_workflow`를 명시했다.
- 첫 NestJS-native executor 예시로 `simple_ffmpeg_transform`을 추가했다.
- registry가 Python/NestJS-native/virtual executor를 함께 노출하는 contract test를 추가했다.

검증:

- `clipper_nestjs npm run build`: passed.
- `clipper_nestjs npm run bundle`: passed.
- `clipper_nestjs node --test test/workflow-executor-registry.test.js`: passed (`2 passed`).
- `simple_ffmpeg_transform` direct executor start smoke: passed locally with `runtimeState=running`.
- `clipper_nestjs git diff --check`: passed.

아직 남은 범위:

- `simple_ffmpeg_transform`의 Angular 진입 UI와 실제 local/devapp/packaged smoke.
- packaged Electron에서 NestJS-native ffmpeg executor에 줄 ffmpeg path env 표준 최종 확정.
- executor별 concurrency/resource 정책을 실제 job admission에 반영할지 검토.
- Python plugin runtime regression smoke.

## 현재 구조 요약

현재 `/jobs` 실행 흐름은 `PluginHost`에 강하게 묶여 있다.

```text
Angular PluginJobService.startJob(pluginName, params)
  -> POST NestJS /jobs
  -> JobsService.enqueueJob()
  -> JobsService.runJob()
  -> pluginHost.ensureStarted(pluginName)
  -> POST <pluginBaseUrl>/jobs
  -> WS <pluginBaseUrl>/jobs/:jobId/events
  -> JobsService.publish()
  -> Angular RealtimeEventService
```

코드 기준:

- `clipper_nestjs/src/jobs/jobs.service.ts`
  - `pluginHost.ensureStarted(snapshot.pluginName)`
  - `submitToPlugin(baseUrl, jobId, params)`
  - `watchPluginEvents(snapshot)`
- `clipper_nestjs/src/plugins/plugin-host.ts`
  - Python runtime process를 list/start/stop/status 하는 추상화.
- `clipper_nestjs/src/plugins/local-plugin-host.service.ts`
  - local/devapp에서 `uv run --directory <clipper_python> python -m <plugin> <port>` 실행.
- `clipper_nestjs/src/plugins/electron-plugin-host.service.ts`
  - packaged에서 Electron bridge에 start/stop/status 요청.

현재 virtual workflow plugin도 있다.

```ts
export const VIRTUAL_WORKFLOW_PLUGINS = new Set(['clipper1', 'variation']);
```

하지만 이것은 Store/Dashboard에 workflow card를 보여주기 위한 catalog 성격이다. 현재 `/jobs` runtime executor는 아니다.

## 문제

새 기능이 다음 조건을 만족해야 하면 현재 구조로는 부족하다.

```text
예: simple_ffmpeg_transform

- Plugin Store에 다른 plugin과 같이 보인다.
- job history에 남는다.
- start/stop/status 모델에 들어온다.
- Angular는 기존처럼 NestJS /jobs API만 호출한다.
- 구현은 Python process가 아니라 NestJS service + child_process ffmpeg spawn으로 충분하다.
```

현재 `JobsService`는 job 실행을 Python runtime HTTP/WS protocol로만 처리한다. NestJS 내부 executor로 dispatch하는 분기점이 없다.

## 설계 원칙

1. Angular contract는 유지한다.
   - Angular는 계속 NestJS API만 호출한다.
   - Angular는 executor가 Python인지 NestJS인지 몰라야 한다.
2. Python plugin 구조는 유지한다.
   - 기존 `dance_highlight`, `dialog_highlight`, `clipper1_video_render`는 깨지지 않아야 한다.
3. NestJS-native workflow는 Python HTTP/WS server를 흉내내지 않는다.
   - 같은 job event contract를 쓰되, NestJS 내부에서 직접 event를 publish한다.
4. Plugin Store와 job history는 같은 plugin identity를 사용한다.
   - `pluginName`은 UI card, job snapshot, executor dispatch의 공통 key다.
5. packaged process ownership은 유지한다.
   - Python process host는 packaged에서 계속 Electron이 맡는다.
   - NestJS-native executor는 packaged NestJS process 안에서 실행된다.
   - native file dialog, packaged venv, model install 같은 OS/native host 책임을 NestJS로 옮기지 않는다.

## 핵심 변경: WorkflowExecutor

`PluginHost`는 "Python runtime process control" 책임으로 남긴다. 그 위에 `/jobs` 실행 책임을 담당하는 `WorkflowExecutor` 계층을 추가한다.

```ts
export type WorkflowRuntimeKind =
  | 'python_plugin'
  | 'nestjs_executor'
  | 'virtual_workflow';

export interface WorkflowRuntimeStatus {
  installState: 'installed' | 'not_installed';
  runtimeState: 'stopped' | 'starting' | 'running' | 'stopping' | 'error';
  lastError?: string;
  startedAt?: string;
}

export interface WorkflowRunContext {
  jobId: string;
  pluginName: string;
  params: Record<string, unknown>;
  signal: AbortSignal;
  publishProgress(progress: number, message: string): Promise<void>;
  complete(result: Record<string, unknown> | null): Promise<void>;
  fail(error: string): Promise<void>;
}

export interface WorkflowExecutor {
  readonly pluginName: string;
  readonly runtimeKind: WorkflowRuntimeKind;

  getManifest(): Promise<PluginManifestView>;
  getStatus(): Promise<WorkflowRuntimeStatus>;
  getResourceAssessment?(): Promise<PluginResourceAssessment>;

  start(options?: PluginStartOptions): Promise<void>;
  stop(): Promise<void>;

  run(context: WorkflowRunContext): Promise<void>;
  cancel?(jobId: string): Promise<void>;
}
```

중요한 분리:

- `start()`는 runtime readiness를 만든다.
- `run()`은 특정 job을 실행한다.
- Python executor의 `start()`는 기존 `PluginHost.ensureStarted()`를 호출한다.
- NestJS executor의 `start()`는 ffmpeg 존재 확인, warm-up, 내부 state 전환 같은 작업만 한다.

## Executor 종류

### 1. PythonPluginWorkflowExecutor

기존 동작을 감싼 adapter다.

```text
PythonPluginWorkflowExecutor
  -> PluginHost.ensureStarted(pluginName)
  -> POST <baseUrl>/jobs
  -> WS <baseUrl>/jobs/:jobId/events
  -> context.publishProgress / complete / fail
```

현재 `JobsService.runJob()`, `submitToPlugin()`, `watchPluginEvents()`에 흩어진 Python-specific logic을 이 executor로 옮긴다.

장점:

- `JobsService`가 Python HTTP/WS protocol을 몰라도 된다.
- NestJS executor를 추가해도 `JobsService` 구조가 단순하게 유지된다.

### 2. NestjsWorkflowExecutor

NestJS 내부 service가 job을 직접 수행한다.

예: `simple_ffmpeg_transform`

```text
NestjsFfmpegTransformExecutor.run(context)
  -> input validation
  -> output path 준비
  -> child_process.spawn(ffmpeg, args)
  -> stderr/progress parse
  -> context.publishProgress(...)
  -> context.complete({ outputPath, ... })
```

ffmpeg process는 NestJS child process지만, packaged 앱의 native process host 책임을 NestJS로 옮기는 것은 아니다. 여기서 말하는 child process는 해당 workflow의 계산 작업이다. Electron의 packaged app host 책임, NestJS process host 책임, Python packaged venv 책임은 그대로 Electron에 남는다.

### 3. VirtualWorkflowExecutor

`clipper1`, `variation`처럼 아직 `/jobs` executor가 아닌 workflow entry를 명시적으로 표현한다.

```text
virtual_workflow
  -> Store/Dashboard card 표시
  -> route 진입 가능
  -> start/stop은 no-op 또는 not_applicable
  -> /jobs 실행 대상은 아님
```

이 분리를 명시하면 "catalog에는 있는데 왜 job으로 실행되지 않는가"가 덜 헷갈린다.

## Registry 설계

새 모듈:

```text
clipper_nestjs/src/workflows/
  workflow-executor.ts
  workflow-executor-registry.service.ts
  python-plugin-workflow-executor.ts
  virtual-workflow-executor.ts
  nestjs-ffmpeg-transform.executor.ts
```

Registry 책임:

```ts
export class WorkflowExecutorRegistry {
  list(): Promise<WorkflowExecutor[]>;
  get(pluginName: string): Promise<WorkflowExecutor>;
  has(pluginName: string): Promise<boolean>;
}
```

초기 구현 방식:

- Python runtime plugin들은 `PluginHost.listManifests()` 결과로 adapter를 만든다.
- NestJS-native executor provider는 registry에 등록한다. 2026-05-29 초기 구현에서는 `simple_ffmpeg_transform`이 `NestjsFfmpegTransformExecutor.getManifest()`로 manifest를 제공한다.
- `VIRTUAL_WORKFLOW_PLUGINS`는 `VirtualWorkflowExecutor`로 매핑한다.

## Catalog 확장

현재 `PluginManifestView`에 runtime kind를 추가한다.

```ts
export interface PluginManifestView {
  name: string;
  version: string;
  displayName: string;
  description: string;
  author?: string;
  runtimeKind?: 'python_plugin' | 'nestjs_executor' | 'virtual_workflow';
  capabilities?: {
    provides: string[];
    requires: string[];
  };
  ...
}
```

예시:

```ts
simple_ffmpeg_transform: {
  name: 'simple_ffmpeg_transform',
  version: '0.1.0',
  displayName: '간단 영상 변환',
  description: 'ffmpeg으로 입력 영상에 간단한 변환을 적용합니다.',
  runtimeKind: 'nestjs_executor',
  capabilities: {
    provides: ['workflow.simple_ffmpeg_transform', 'video.transform.ffmpeg'],
    requires: ['source.ingest', 'ffmpeg.ready'],
  },
  resourceProfile: {
    estimatedRamMb: 512,
    estimatedVramMb: 0,
    requiresGpu: false,
    preferredAccelerators: ['cpu'],
    coldStartCost: 'low',
    maxConcurrency: 1,
  },
  models: [],
}
```

## Plugin Store 통합

현재 `PluginsService`는 `PluginHost`와 virtual catalog를 섞어서 list/status/start/stop을 만든다. 이를 `WorkflowExecutorRegistry` 중심으로 바꾼다.

변경 전:

```text
PluginsService
  -> PluginHost list/status/start/stop
  -> virtual workflow catalog merge
```

변경 후:

```text
PluginsService
  -> WorkflowExecutorRegistry list/status/start/stop
```

이렇게 하면 Store에서는 세 종류가 모두 같은 list item으로 보인다.

```text
dance_highlight          runtimeKind=python_plugin
dialog_highlight         runtimeKind=python_plugin
clipper1_video_render    runtimeKind=python_plugin
simple_ffmpeg_transform  runtimeKind=nestjs_executor
clipper1                 runtimeKind=virtual_workflow
variation                runtimeKind=virtual_workflow
```

UI는 필요한 경우 `runtimeKind`로 표시/버튼 정책을 다르게 할 수 있다.

## Job 실행 통합

`JobsService`는 더 이상 `PluginHost`를 직접 사용하지 않는다. 대신 registry에서 executor를 찾아 실행한다.

변경 전:

```ts
const baseUrl = await this.pluginHost.ensureStarted(snapshot.pluginName);
await this.submitToPlugin(baseUrl, jobId, snapshot.params);
await this.watchPluginEvents(snapshot);
```

변경 후:

```ts
const executor = await this.workflowExecutors.get(snapshot.pluginName);
await executor.start();
await executor.run(context);
```

`context`는 `JobsService`가 만든다. 그래서 모든 executor는 같은 방식으로 job history와 realtime event에 기록된다.

```text
context.publishProgress()
  -> JobRepository.update()
  -> RealtimeGatewayService.broadcastToSubject()

context.complete()
  -> JobRepository.update(completed)
  -> ProjectsService.recordCompletedJob()
  -> RealtimeGatewayService.broadcastToSubject()

context.fail()
  -> JobRepository.update(failed)
  -> RealtimeGatewayService.broadcastToSubject()
```

## Cancellation

현재 cancel은 job local state를 cancelled로 바꾸고, Python plugin job이면 `DELETE <baseUrl>/jobs/:jobId`를 호출한다.

새 구조:

```text
JobsService.cancel(jobId)
  -> queue remove
  -> executor.cancel(jobId)
  -> AbortController.abort()
  -> publish cancelled event
```

Executor별 동작:

- Python executor
  - 기존 `DELETE <plugin>/jobs/:jobId` 호출.
- NestJS ffmpeg executor
  - jobId별 child process를 map에 보관.
  - cancel 시 `SIGTERM`, timeout 후 `SIGKILL`.
  - `AbortSignal`도 함께 확인.
- Virtual executor
  - no-op.

## Start/Stop semantics

기존 status enum을 유지한다.

```text
stopped | starting | running | stopping | error
```

Python executor:

- `start`: plugin process start.
- `stop`: plugin process stop.
- `running`: plugin HTTP server가 떠 있음.

NestJS executor:

- `start`: executor readiness 확인.
  - 예: ffmpeg binary 확인, output root 준비, optional warm-up.
- `stop`: active job cancellation 또는 idle state 전환.
- `running`: executor가 job을 받을 준비가 된 상태.
- 실제 ffmpeg child process는 job 단위로 생성/종료된다.

Virtual executor:

- `start`: no-op.
- `stop`: no-op.
- `runtimeState`: `stopped` 또는 `not_applicable` 성격. 기존 enum 유지가 필요하면 `stopped`.

## Packaged mode 영향

Python executor packaged:

```text
NestJS PythonPluginWorkflowExecutor
  -> ElectronPluginHost
  -> Electron PluginHostBridgeServer
  -> Electron LocalPluginManager
  -> packaged Python venv process
```

NestJS executor packaged:

```text
NestJS NestjsFfmpegTransformExecutor
  -> packaged NestJS process 안에서 ffmpeg child process 실행
```

주의:

- packaged NestJS가 ffmpeg를 실행하려면 ffmpeg path를 알아야 한다.
- 현재 Electron `NestProcess`는 `CLIPPER_YTDLP_FFMPEG_LOCATION`을 NestJS env에 주입한다.
- 일반 workflow executor용으로는 별도 표준 env를 정하는 편이 좋다.

제안:

```text
CLIPPER_FFMPEG_BIN
CLIPPER_FFPROBE_BIN
```

또는 기존 `FFMPEG_BIN` 사용을 유지하되 packaged Electron이 해당 env를 명확히 주입한다.

중요한 금지:

- packaged에서 `.env.local`을 읽거나 복사하지 않는다.
- plugin별 고정 port/env를 추가하지 않는다.

## 간단 ffmpeg workflow 예시

예시 이름:

```text
simple_ffmpeg_transform
```

Angular 요청:

```ts
pluginJobs.startJob('simple_ffmpeg_transform', {
  jobId,
  params: {
    source: { type: 'local_file', path: '/path/input.mp4' },
    transform: { type: 'scale', width: 720 },
  },
});
```

NestJS executor:

```text
1. SourceService로 source 준비.
2. output path 생성.
3. ffmpeg args 구성.
4. child_process.spawn(ffmpeg, args).
5. stderr progress를 parse해서 context.publishProgress().
6. 완료 시 context.complete({ outputPath }).
7. 실패 시 context.fail(message).
```

Plugin Store:

```text
name: simple_ffmpeg_transform
runtimeKind: nestjs_executor
status: installed/running/stopped/error
models: []
resourceProfile: low/cpu
```

## 구현 단계

### Phase 1: 구조 도입, 기존 동작 보존

목표:

- 기존 Python plugin job이 그대로 동작한다.
- `JobsService`에서 Python-specific logic을 executor adapter로 이동한다.

작업:

1. `WorkflowExecutor` interface 추가.
2. `PythonPluginWorkflowExecutor` 추가.
3. `WorkflowExecutorRegistry` 추가.
4. `JobsService`가 `PluginHost` 대신 registry를 사용하게 변경.
5. 기존 `/jobs` 테스트를 통과시킨다.

검증:

- `dance_highlight` job submit path가 기존과 같은 request/event flow를 유지한다.
- `dialog_highlight` job submit path가 기존과 같은 request/event flow를 유지한다.
- 기존 plugin list/start/stop API가 regression 없이 동작한다.

### Phase 2: Plugin Store list/start/stop 통합

목표:

- `PluginsService`가 `WorkflowExecutorRegistry`를 통해 Python, NestJS, virtual workflow를 같은 방식으로 list/status/start/stop한다.

작업:

1. `PluginManifestView.runtimeKind` 추가.
2. virtual workflow도 executor로 표현.
3. `PluginsService`의 virtual merge logic을 registry로 이동.
4. Angular `PluginStatusService`가 `runtimeKind`를 optional field로 받아도 깨지지 않게 갱신.

검증:

- Store/Dashboard에서 기존 plugin card가 유지된다.
- `clipper1`, `variation` virtual workflow의 route card가 유지된다.
- Python runtime status list가 유지된다.

### Phase 3: 첫 NestJS-native executor 추가

목표:

- `simple_ffmpeg_transform` 같은 NestJS-native plugin을 추가한다.

작업:

1. `NestjsFfmpegTransformExecutor` 추가.
2. executor `getManifest()` 또는 catalog metadata에 `runtimeKind: 'nestjs_executor'` 항목 추가.
3. ffmpeg binary resolution 정책 확정.
4. job cancellation에서 child process 종료 처리.
5. Angular route 또는 Store entry 연결.

검증:

- local 모드에서 `/jobs`로 `simple_ffmpeg_transform` 실행.
- devapp 모드에서 같은 job 실행.
- packaged 모드에서 ffmpeg path 주입 후 같은 job 실행.
- job history, progress, completed/failed/cancelled 상태가 기존 plugin과 같은 UI에 보인다.

## 테스트 계획

NestJS unit/contract:

- registry가 Python manifest를 `PythonPluginWorkflowExecutor`로 노출한다.
- registry가 `runtimeKind: 'nestjs_executor'` NestJS executor를 노출한다.
- `JobsService`가 executor `run()`을 호출하고 event를 repository/realtime에 기록한다.
- cancellation이 executor `cancel()`과 AbortSignal을 호출한다.
- Python executor adapter가 기존 `/jobs` + WS event를 normalize한다.

Angular:

- `PluginStatusService`가 `runtimeKind`가 있어도 기존 cards를 표시한다.
- `PluginJobService` contract는 변경하지 않는다.

Packaged smoke:

- Electron packaged app에서 Python plugin start path 유지.
- NestJS-native ffmpeg executor가 packaged ffmpeg path로 실행.
- `.env.local`이 packaged에 포함되지 않음.

## Open Questions

1. NestJS-native executor가 `running` 상태를 언제까지 유지할지.
   - 제안: `start()` 후 app session 동안 `running`, `stop()` 시 `stopped`.
2. ffmpeg path 표준 env 이름.
   - 제안: `FFMPEG_BIN`을 우선 유지하고 packaged Electron에서 명시 주입.
   - 대안: `CLIPPER_FFMPEG_BIN` / `CLIPPER_FFPROBE_BIN` 신설.
3. Plugin Store에서 `virtual_workflow`의 start/stop 버튼을 숨길지 disabled로 둘지.
   - 제안: UI에서는 route 진입 버튼만 보여준다.
4. `resourceProfile.maxConcurrency`를 executor별 concurrency로 실제 enforcement할지.
   - 현재는 `JobsService.maxGlobalConcurrentJobs = 1`이 실질 limiter다.
   - Phase 1에서는 global 1 유지, Phase 3 이후 executor별 limit 검토.

## 결론

현재 구조에서 NestJS로 간단 ffmpeg plugin을 "기능"으로 만드는 것은 가능하다. 하지만 Plugin Store, job history, start/stop 모델까지 같은 plugin처럼 통합하려면 `/jobs` 실행 단위를 `PluginHost`가 아니라 `WorkflowExecutor`로 추상화해야 한다.

권장 구현 순서는 다음이다.

```text
1. WorkflowExecutor interface와 Python adapter 도입
2. JobsService를 executor registry 기반으로 전환
3. PluginsService/Plugin Store를 runtimeKind 기반 registry로 정리
4. 첫 NestJS-native ffmpeg executor 추가
```

이 방식이면 기존 Python plugin은 유지하면서 NestJS-native plugin을 점진적으로 추가할 수 있다.
