# NestJS Control Plane 중심 Clipper2 재설계

작성일: 2026-04-29

2026-05-29 현재 상태: 이 문서의 방향은 `WorkflowExecutorRegistry` 도입으로 일부 구현됐다. Angular는 NestJS API만 호출하고, NestJS `JobsService`가 `WorkflowExecutor`를 통해 Python plugin, NestJS-native executor, virtual workflow를 dispatch하는 구조로 이동 중이다. Python process lifecycle은 여전히 `PluginHost`/Electron bridge가 담당한다.

이 문서는 Clipper2에서 NestJS의 역할이 지나치게 축소되는 문제를 바로잡기 위한 설계 초안이다. 기존 `.codex/CLIPPER2_NEXT_ARCHITECTURE_PLAN.md`는 Electron main process에 `PipelineQueueManager`를 두는 방향으로 작성되었지만, 팀의 장기 아키텍처 기준을 고려하면 그 방향은 보완이 필요하다.

핵심 결론:

> Clipper2의 메인 앱 백엔드와 API control plane은 NestJS가 맡고, FastAPI plugin은 Python 계산 worker로 제한하며, Electron은 데스크톱 host/native adapter 역할에 집중하는 것이 팀 방향과 더 맞다.

---

## 1. 팀 기준 아키텍처 재확인

팀의 기본 방향은 다음이다.

```text
Angular
  - 프론트엔드 SPA
  - 사용자 UI

NestJS
  - 메인 백엔드 서버
  - Angular가 호출하는 주 API
  - DTO/API 계약의 중심
  - 인증, 권한, queue, project, orchestration

FastAPI / Python
  - Python 생태계가 필요한 계산 worker
  - torch, onnxruntime, ffmpeg-heavy pipeline, model inference
  - 메인 product API가 아니라 compute API

Electron
  - 설치형 앱 shell
  - OS/native 기능
  - local process host
  - packaged runtime bootstrap
```

이 방향 자체는 여전히 유효하다. Clipper2가 plugin architecture로 이동했다고 해서 NestJS를 주변부로 밀어낼 이유는 없다.

---

## 2. 현재 Clipper2가 왜 Electron-heavy가 되었는가

현재 Clipper2는 다음 이유로 Electron 쪽 책임이 커졌다.

- Python plugin process를 실제로 spawn/kill 할 수 있는 위치가 Electron main process다.
- packaged app에서 `resourcesPath`, `userData`, venv, uv, ffmpeg, file dialog 같은 OS 책임이 Electron에 있다.
- Angular가 빠르게 plugin URL을 얻고 FastAPI `/jobs`를 직접 호출하는 방식이 구현 속도상 쉬웠다.
- NestJS는 초기에는 dance pre-pipeline API만 필요했기 때문에 역할이 작게 시작됐다.

이건 초기 구현으로는 이해 가능하다. 하지만 최종 아키텍처로 굳히면 문제가 생긴다.

---

## 3. 그대로 두면 생기는 문제

### 3.1 Angular가 여러 백엔드를 직접 알게 된다

현재 Angular는 다음을 모두 알고 있다.

- Electron IPC
- NestJS local API
- Python plugin FastAPI URL
- Python plugin WebSocket

이 구조는 레거시에서 이미 겪었던 문제와 닮아 있다. 어떤 API는 NestJS로, 어떤 API는 FastAPI로, 어떤 API는 Electron IPC로 가면 프론트엔드가 orchestration을 떠안게 된다.

### 3.2 NestJS가 메인 백엔드가 아니라 보조 API가 된다

지금 상태에서는 NestJS가 dance artist/member/image search만 맡는다. 이렇게 굳어지면 팀의 "NestJS를 메인 백엔드로 사용한다"는 원칙과 어긋난다.

### 3.3 Electron 없이는 앱이 성립하기 어려워진다

Electron main process가 queue, plugin lifecycle, project state, job orchestration까지 모두 맡으면 다음 실행 형태가 어려워진다.

- Angular + NestJS + FastAPI를 각각 localhost로 띄우는 개발 모드
- Docker compose로 웹/서버처럼 띄우는 모드
- 원격 서버에 배포해 브라우저로 접속하는 demo/server mode

Electron은 데스크톱 packaged app에서는 필수지만, 앱의 product backend 자체가 Electron에 묶이면 안 된다.

### 3.4 DTO/API 계약 공유가 약해진다

Angular와 NestJS를 같은 monorepo에 두고 DTO/interface를 공유하려는 방향과도 맞지 않다. Angular가 Python plugin API를 직접 호출하면 결국 TypeScript DTO 공유의 장점이 줄어든다.

---

## 4. 수정된 역할 분리

권장 구조:

```text
Angular
  -> NestJS App API만 기본 호출
  -> Electron IPC는 native 기능이 필요할 때만 호출

NestJS
  -> Project / Queue / Job / Source / Plugin API의 중심
  -> FastAPI plugin compute API를 호출하거나 proxy
  -> Angular에 단일 API surface 제공

FastAPI Plugin
  -> 모델 로딩
  -> 실제 pipeline job 실행
  -> progress/event 제공
  -> Python-only compute 책임

Electron
  -> local NestJS 실행
  -> local Python plugin 실행
  -> process registry / port allocation / venv / ffmpeg / file dialog
  -> NestJS가 plugin을 제어할 수 있는 host bridge 제공
```

중요한 변화:

> QueueManager는 Electron이 아니라 NestJS에 두는 것을 기본안으로 본다.

단, NestJS가 직접 OS process spawn을 할지 여부는 실행 모드별로 달라진다.

---

## 5. NestJS가 가져야 할 책임

### 5.1 App API Facade

Angular가 기본적으로 호출하는 API는 NestJS 하나로 수렴한다.

예:

```text
POST /v1/sources/check
POST /v1/projects
GET  /v1/projects
GET  /v1/projects/:id
POST /v1/jobs
GET  /v1/jobs
GET  /v1/jobs/:id
POST /v1/jobs/:id/cancel
GET  /v1/jobs/:id/events
GET  /v1/plugins
GET  /v1/plugins/:name/status
POST /v1/plugins/:name/start
POST /v1/plugins/:name/stop
```

Angular는 Python plugin의 `/jobs` URL을 직접 몰라도 된다.

### 5.2 Queue / Project Orchestration

NestJS가 앱 레벨 job queue와 project state의 source of truth가 된다.

NestJS 책임:

- job enqueue
- 순차 실행 정책
- cancel/retry/reorder
- job history
- project metadata 저장
- plugin 선택
- FastAPI job start
- FastAPI progress stream 수신 후 Angular에 전달

초기 저장소는 JSON 파일이어도 된다. 장기적으로 SQLite/PostgreSQL로 바꿀 수 있다.

### 5.3 Plugin Control API

NestJS가 plugin status/start/stop API를 제공한다.

다만 packaged Electron 모드에서는 NestJS가 직접 Python process를 spawn하지 않고 Electron host bridge에 요청하는 편이 안전하다.

```text
Angular
  -> NestJS /v1/plugins/dance_highlight/start
  -> NestJS PluginHostPort
  -> Electron host bridge
  -> Python process spawn
```

### 5.4 Source / Preflight

YouTube check, file metadata check, duration limit, source normalization은 NestJS API로 제공한다.

실제 yt-dlp가 Python plugin 의존성으로 있어야 한다면 NestJS가 plugin preflight endpoint를 호출해도 된다.

```text
Angular -> NestJS /v1/sources/check
NestJS -> plugin /preflight/youtube/check
```

Angular가 plugin preflight endpoint를 직접 호출하지 않는다.

### 5.5 LLM Proxy / Auth / Billing 확장

Clipper1 통합까지 고려하면 LLM API key 보호가 중요하다. NestJS는 remote server 또는 LLM proxy와 연결되는 자연스러운 위치다.

초기에는 local NestJS가 bundled env를 읽을 수 있지만, 제품화 단계에서는 remote NestJS/API server와 연동해야 한다.

---

## 6. Electron의 수정된 책임

Electron은 "앱 백엔드"가 아니라 "desktop host adapter"다.

Electron이 계속 맡아야 하는 것:

- packaged Angular renderer 로딩
- local NestJS process 실행
- local Python plugin process 실행
- port allocation
- venv/uv/bootstrap
- ffmpeg binary download
- model download trigger와 local file path 관리
- native file dialog
- app logs
- app shutdown cleanup

Electron이 되도록 맡지 말아야 하는 것:

- product-level queue policy
- project history source of truth
- API DTO의 중심
- business orchestration
- Clipper1 workflow 상태 관리

Electron은 NestJS가 사용할 수 있는 Host Bridge를 제공한다.

예:

```ts
interface PluginHostBridge {
  discover(): Promise<PluginManifestView[]>;
  getStatus(name: string): Promise<PluginStatus>;
  ensureStarted(name: string): Promise<{ baseUrl: string }>;
  stop(name: string): Promise<void>;
  getFfmpegStatus(): Promise<FfmpegStatus>;
  ensureFfmpeg(): Promise<void>;
}
```

이 bridge는 Electron 모드에서는 IPC/HTTP loopback으로 구현하고, non-Electron 모드에서는 LocalProcessHost 또는 RemotePluginHost로 대체한다.

---

## 7. 실행 모드별 구조

### 7.1 Packaged Electron App

```text
Electron
  starts Angular renderer
  starts local NestJS
  starts Python plugins on demand

Angular
  calls NestJS API
  uses Electron IPC only for native UI if necessary

NestJS
  calls Electron host bridge for plugin process control
  calls Python plugin HTTP/WS for compute jobs
```

이 모드에서 Electron은 process host다. 하지만 Angular의 메인 API는 NestJS다.

### 7.2 Local Dev Mode

```text
Terminal 1: Angular localhost:4200
Terminal 2: NestJS localhost:9019
Terminal 3+: Python plugins manually or by NestJS LocalProcessHost
```

NestJS는 설정에 따라 두 방식 중 하나를 쓸 수 있다.

- 이미 떠 있는 plugin URL을 env로 받는다.
- NestJS가 dev용 LocalProcessHost로 `uv run python -m plugin`을 직접 spawn한다.

이 경우 Electron 없이도 대부분의 앱 기능이 동작한다. 파일 선택 같은 native 기능만 browser fallback을 쓴다.

### 7.3 Docker / Server Mode

```text
Angular static server
NestJS API server
Python plugin containers or processes
```

NestJS는 RemotePluginHost를 사용한다.

```text
NestJS -> http://dance-plugin:54822
NestJS -> http://dialog-plugin:54821
```

이 모드에서는 Electron이 없다. 따라서 Electron에 product orchestration을 두면 안 된다.

---

## 8. FastAPI plugin의 역할 재정의

FastAPI plugin은 외부 사용자-facing backend가 아니라 compute worker API다.

권장 endpoint:

```text
GET  /health
POST /jobs
DELETE /jobs/:id
WS   /jobs/:id/events
POST /preflight/youtube/check
POST /preflight/file/check
```

NestJS가 이 API를 호출하고, Angular에는 NestJS API만 노출한다.

FastAPI plugin이 가져도 되는 책임:

- 모델 로딩
- Python-only 분석
- ffmpeg-heavy processing
- yt-dlp처럼 Python 생태계에 가까운 source processing
- job progress event 생성

FastAPI plugin이 가지면 안 좋은 책임:

- 사용자 인증
- billing/subscription
- 앱 전체 queue
- project history
- Angular 전용 DTO 계약

---

## 9. Clipper1 통합에 미치는 영향

Clipper1은 NestJS 중심 설계가 더 필요하다.

Clipper1에는 다음 단계가 있다.

- prompt/news URL/text/image 입력
- LLM script generation
- clip 구성
- media search/download
- TTS
- template 적용
- final render
- 사용자 편집
- super clone

이건 단순 Python job 하나가 아니라 product workflow다. 따라서 workflow/project state를 NestJS가 관리해야 한다.

권장:

```text
Angular features/clipper-studio
  -> NestJS /v1/clipper-studio/*

NestJS
  -> project/workflow state
  -> LLM proxy
  -> media/search policy
  -> Python clipper_studio plugin job orchestration

Python clipper_studio plugin
  -> Python-only generation/render worker
```

즉 Clipper1은 `clipper_studio` Python plugin만으로 끝나는 것이 아니라, NestJS module과 Angular feature가 함께 들어와야 한다.

---

## 10. Monorepo 방향

Angular와 NestJS는 TypeScript 생태계이므로 monorepo로 합치는 장점이 크다.

권장 장기 구조:

```text
clipper_app/
  apps/
    angular/
    nestjs/
    electron/
  packages/
    contracts/
      src/
        plugin.dto.ts
        queue.dto.ts
        project.dto.ts
        clipper-studio.dto.ts
    ui/
    config/

clipper_python/
  clipper_plugin_sdk/
  plugins/
```

또는 Python까지 한 repo에 둘 수는 있지만, TypeScript DTO 공유 장점은 Python에는 직접 적용되지 않는다. Python은 OpenAPI/codegen 또는 별도 Pydantic schema alignment로 맞추는 편이 현실적이다.

단기적으로는 repo를 바로 합치지 않아도 된다. 먼저 `contracts` 패키지를 어떻게 둘지 결정하고, NestJS API를 중심으로 DTO를 정리하는 것이 우선이다.

---

## 11. 수정된 다음 Phase

### Phase 1: NestJS를 App API Facade로 확장

- Angular가 plugin job을 직접 호출하는 경로를 줄인다.
- NestJS에 `plugins`, `jobs`, `projects` module을 추가한다.
- 현재 Electron plugin IPC와 Python plugin API를 감싸는 service boundary를 만든다.

### Phase 2: PluginHost abstraction

NestJS 내부에 다음 추상화를 둔다.

```ts
abstract class PluginHost {
  abstract list(): Promise<PluginManifestView[]>;
  abstract getStatus(name: string): Promise<PluginStatus>;
  abstract ensureStarted(name: string): Promise<string>;
  abstract stop(name: string): Promise<void>;
}
```

구현체:

- `ElectronPluginHost`: packaged Electron에서 Electron host bridge 호출
- `StaticPluginHost`: local/dev에서 env plugin URL 사용
- `RemotePluginHost`: docker/server에서 remote plugin URL 사용

### Phase 3: NestJS QueueManager

- QueueManager는 NestJS module로 구현한다.
- 처음에는 in-memory + JSON snapshot으로 시작한다.
- job 실행 시 PluginHost로 plugin URL을 얻고 Python `/jobs` 호출/WS 구독을 NestJS가 담당한다.

### Phase 4: Angular 전환

- `PluginJobService`가 Python URL을 직접 호출하지 않게 한다.
- Angular는 NestJS `JobApi`만 호출한다.
- 진행률도 NestJS WebSocket/SSE 또는 polling으로 받는다.

### Phase 5: Electron 책임 축소

- Electron은 plugin process host bridge와 native 기능만 제공한다.
- product queue/project API는 Electron IPC가 아니라 NestJS API를 통한다.

### Phase 6: Clipper1 편입

- NestJS `clipper-studio` module 추가
- Python `clipper_studio` plugin 추가
- Angular `features/clipper-studio` 추가
- LLM proxy 전략 확정

---

## 12. 결론

우려는 맞다. 현재 구현은 초기 MVP로는 동작하지만, 그대로 확장하면 NestJS가 주변화되고 Electron 없이는 앱이 성립하기 어려워진다.

따라서 다음 설계 기준은 다음으로 수정한다.

1. Angular의 기본 API 대상은 NestJS 하나로 수렴한다.
2. NestJS가 queue/project/job/plugin orchestration의 중심이 된다.
3. FastAPI plugin은 Python compute worker로 제한한다.
4. Electron은 desktop host/native adapter로 제한한다.
5. local/dev/docker/server mode는 NestJS의 `PluginHost` 구현체만 바꿔서 대응한다.

이 구조가 팀의 Angular + NestJS + FastAPI + Electron 아키텍처와 더 잘 맞고, Clipper1 통합에도 더 안전하다.

---

## 13. 기존 Electron PluginManager는 어떻게 되는가

현재 `clipper_electron`의 `LocalPluginManager`는 필요 없어진 것이 아니다. 다만 최종 아키텍처에서는 이름과 책임을 더 명확히 분리해야 한다.

현재 Electron `LocalPluginManager`가 하는 일:

- plugin manifest discovery
- Python plugin process spawn
- port allocation
- health check
- start/stop
- runtime state 저장
- process exit/error 감지
- model download flow와 연결

이 중 대부분은 여전히 Electron packaged app에서 필요하다. 특히 Python process를 실제로 띄우고 죽이는 일, packaged resource path와 userData/venv를 아는 일은 Electron이 가장 자연스럽다.

문제는 이 manager가 "제품 레벨의 plugin orchestration"까지 맡으면 안 된다는 점이다.

### 13.1 유지해야 하는 책임

Electron 쪽에는 다음 책임을 가진 host-level manager가 남는다.

```text
ElectronPluginHostManager
  - discover plugin packages from resourcesPath
  - ensure plugin venv/runtime is ready
  - spawn Python plugin process
  - allocate local port
  - wait for /health
  - stop process
  - report pid/port/runtime state
```

즉, OS process manager이자 desktop runtime adapter다.

### 13.2 NestJS로 옮겨야 하는 책임

NestJS 쪽에는 별도의 product-level service가 생긴다.

```text
NestJS PluginService / PluginHost
  - Angular-facing plugin API
  - plugin availability/status DTO
  - plugin start/stop command endpoint
  - job/queue orchestration에서 plugin URL 확보
  - local/dev/docker/electron mode별 host implementation 선택
```

NestJS는 직접 OS process를 항상 띄우는 것이 아니라, 실행 모드에 맞는 `PluginHost` 구현체를 통해 plugin runtime에 접근한다.

### 13.3 이름을 분리해야 하는 이유

현재 이름인 `PluginManager`는 너무 넓다. 다음 두 개념이 섞일 수 있다.

- host-level manager: 프로세스를 띄우고 포트를 관리하는 OS/runtime 책임
- app-level manager: 어떤 plugin을 사용자에게 노출하고 어떤 job에 연결할지 결정하는 제품 책임

따라서 리팩터링 시 이름을 이렇게 나누는 것이 좋다.

```text
clipper_electron
  ElectronPluginHostManager 또는 LocalPluginProcessManager

clipper_nestjs
  PluginService
  PluginHost abstraction
  ElectronPluginHost / StaticPluginHost / RemotePluginHost
```

### 13.4 실행 모드별 PluginHost

```text
Packaged Electron
  NestJS ElectronPluginHost
    -> Electron host bridge
    -> ElectronPluginHostManager
    -> Python plugin process

Local dev
  NestJS StaticPluginHost
    -> env에 적힌 http://127.0.0.1:54821 같은 plugin URL 사용

Local dev advanced
  NestJS LocalProcessPluginHost
    -> NestJS가 uv run으로 plugin process 직접 spawn

Docker/server
  NestJS RemotePluginHost
    -> http://dance-plugin:54822 같은 remote/container URL 사용
```

이렇게 하면 Electron packaged app에서도 기존 process 관리 코드를 재사용할 수 있고, Electron 없이도 NestJS 중심 API 구조를 유지할 수 있다.

### 13.5 결론

기존 Electron PluginManager는 폐기 대상이 아니다. 제품 아키텍처에서의 위치가 바뀐다.

```text
Before
  Angular -> Electron PluginManager -> Python plugin URL
  Angular -> Python plugin /jobs

After
  Angular -> NestJS Plugin/Job API
  NestJS -> PluginHost abstraction
  Packaged mode PluginHost -> Electron host manager
  NestJS -> Python plugin /jobs
```

즉, Electron PluginManager는 "메인 플러그인 관리자"에서 "Electron 환경의 plugin process host adapter"로 내려온다. NestJS가 app-level plugin manager가 되고, Electron은 packaged desktop에서만 필요한 process host 구현체가 된다.
