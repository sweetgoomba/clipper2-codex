# Clipper2 Plugin System Technical Analysis

작성 기준: 2026-05-26 현재 checkout 분석 결과.

이 문서는 Clipper2의 plugin system을 기술적으로 설명한다. 팀 공유용 전체 구조 문서인 [TEAM_ARCHITECTURE_OVERVIEW.md](TEAM_ARCHITECTURE_OVERVIEW.md)보다 더 낮은 레벨에서, plugin discovery, process ownership, runtime API, job protocol, model install, resource policy, 확장 절차를 정리한다.

## 결론 요약

Clipper2의 plugin system은 Python plugin process만 뜻하지 않는다. 현재 구조에서는 다음 네 계층이 함께 plugin system을 만든다.

```text
Angular feature/plugin UI
  -> NestJS plugin API and job control plane
  -> PluginHost implementation selected by runtime mode
  -> Python PluginRuntime HTTP/WS server
```

모드별 process ownership은 다르다.

- `local` / `devapp`: NestJS `LocalPluginHost`가 `uv run --directory <clipper_python> python -m <plugin> <port>`로 Python plugin을 직접 실행한다.
- `packaged`: Electron `LocalPluginManager`가 packaged Python runtime을 실행하고, NestJS `ElectronPluginHost`가 localhost bridge를 통해 Electron에 start/stop/status를 요청한다.
- `static`: compatibility mode다. NestJS `StaticPluginHost`가 이미 떠 있는 외부 plugin URL만 본다. 기본 실행 경로가 아니다.

Angular는 plugin process URL/port를 직접 알면 안 된다. Angular는 NestJS base URL만 알고, plugin start/status/job은 NestJS API로 처리한다.

## 용어 구분

현재 코드에서 "plugin"은 세 가지 의미로 쓰인다.

### Runtime plugin

실제 Python process로 실행되는 worker다.

현재 runtime plugin:

- `dance_highlight`
- `dialog_highlight`
- `clipper1_video_render`

각 runtime plugin은 `clipper_python/plugins/<plugin_name>/manifest.json`과 Python package를 가진다. 실행 시 FastAPI HTTP/WS server가 되고, `POST /jobs`, `GET /health`, WebSocket event stream을 제공한다.

### Workflow plugin

사용자에게 보이는 workflow entry다.

예:

- `dance_highlight`: 사용자 workflow이면서 runtime plugin이다.
- `dialog_highlight`: 사용자 workflow이면서 runtime plugin이다.
- `clipper1`: 사용자 workflow지만 Python runtime plugin이 아니다. NestJS catalog에 있는 virtual workflow plugin이다.
- `variation`: 사용자 workflow지만 Python runtime plugin이 아니다. NestJS catalog에 있는 virtual workflow plugin이다.

### Utility/runtime worker

사용자가 직접 "플러그인 앱"처럼 시작하지 않아도 기능 내부에서 사용되는 worker다.

예:

- `clipper1_video_render`: Template Builder text artifact, sample render, legacy render boundary 뒤에서 쓰이는 render worker다.

Angular의 Store/Dashboard에서는 user-visible workflow와 runtime status list를 분리한다. `clipper1_video_render`는 runtime status에는 중요하지만 일반 workflow card와는 다르게 취급된다.

## Repo별 구성

### `clipper_angular`

Angular는 plugin UI와 status 표시를 담당한다.

관련 핵심 파일:

- `src/core/backend-locator.ts`
- `src/core/plugin-status.service.ts`
- `src/core/plugin-job.ts`
- `src/core/model-download.service.ts`
- `src/core/clipper-bridge.ts`
- `src/core/pipeline-feature-registry.ts`

Angular 책임:

- NestJS base URL 결정.
- `/plugins` API로 plugin manifest/status/resource assessment 표시.
- `/plugins/:name/start`, `/plugins/:name/stop` 호출.
- `/jobs` API로 pipeline job 제출.
- `/v1/events` realtime WebSocket으로 job event 수신.
- packaged Electron에서 model download consent UI와 progress UI 표시.

Angular가 하면 안 되는 것:

- plugin process를 직접 spawn.
- plugin port를 env나 코드에 고정.
- Python plugin URL을 feature code에서 직접 호출.
- Naver/Kakao/OpenAI 같은 secret env를 직접 소비.

### `clipper_nestjs`

NestJS는 plugin control plane이다.

관련 핵심 파일:

- `src/plugins/plugin-host.ts`
- `src/plugins/plugins.module.ts`
- `src/plugins/plugins.controller.ts`
- `src/plugins/plugins.service.ts`
- `src/plugins/local-plugin-host.service.ts`
- `src/plugins/electron-plugin-host.service.ts`
- `src/plugins/static-plugin-host.service.ts`
- `src/plugins/local-plugin-process.ts`
- `src/plugins/local-plugin-manifest.ts`
- `src/plugins/plugin-port-allocator.ts`
- `src/plugins/plugin-catalog.ts`
- `src/jobs/jobs.service.ts`

NestJS 책임:

- PluginHost abstraction 선택.
- manifest/status/start/stop API 제공.
- plugin start 전 resource assessment와 admission 처리.
- job queue와 job repository 관리.
- plugin runtime에 job 제출.
- plugin WebSocket event를 받아 NestJS realtime event로 다시 broadcast.
- local/devapp에서 Python process 직접 실행.
- packaged에서 Electron bridge를 통해 Electron-owned process 제어.

### `clipper_electron`

Electron은 packaged mode의 process host이자 native adapter다.

관련 핵심 파일:

- `src/main/plugin/plugin-manager.ts`
- `src/main/plugin/plugin-process.ts`
- `src/main/plugin/manifest-loader.ts`
- `src/main/plugin/port-allocator.ts`
- `src/main/plugin/plugin-install-state.ts`
- `src/main/plugin/plugin-ipc.ts`
- `src/main/backend/plugin-host-bridge.ts`
- `src/main/backend/nest-manager.ts`
- `src/main/model-download-ipc.ts`
- `src/shared/ipc-contract.ts`
- `src/preload/preload.ts`

Electron 책임:

- packaged app에서 Python plugin process 실행.
- packaged app에서 NestJS process 실행.
- Electron plugin host bridge 제공.
- packaged plugin env와 ffmpeg/ffprobe path 주입.
- model install state 확인.
- model download/install progress를 Angular로 IPC 전달.
- plugin process stdout/stderr logging.

### `clipper_python`

Python repo는 plugin SDK와 실제 plugin 구현을 가진다.

관련 핵심 파일:

- `clipper_plugin_sdk/clipper_plugin_sdk/base.py`
- `clipper_plugin_sdk/clipper_plugin_sdk/routes.py`
- `clipper_plugin_sdk/clipper_plugin_sdk/models.py`
- `plugins/*/manifest.json`
- `plugins/*/<plugin_name>/__main__.py`
- `plugins/*/<plugin_name>/app.py`

Python 책임:

- `PluginBase`를 상속한 plugin 구현.
- `load_models()`에서 모델 초기화.
- `run_job()`에서 실제 작업 실행.
- `report_progress()`로 진행률 전달.
- 공통 HTTP/WS endpoint 제공.
- cancellation flag 확인.
- runtime accelerator probe 제공.

## 전체 control flow

### Plugin 목록과 상태 표시

```text
Angular PluginStatusService.refreshAll()
  -> BackendLocator.getBaseUrl()
  -> GET <NestJS>/plugins
  -> PluginsController.list()
  -> PluginsService.list()
  -> PluginHost.listManifests()
  -> PluginHost.getStatus(name)
  -> ResourcePolicy.assessStart(...)
  -> Angular Store/Dashboard render
```

NestJS `PluginsService.list()`는 runtime manifest에 virtual workflow manifest를 합친다. `clipper1`, `variation`은 Python process가 없어도 catalog에서 user-visible workflow로 표시될 수 있다.

### Plugin start

```text
Angular PluginStatusService.start(name)
  -> POST <NestJS>/plugins/:name/start
  -> PluginsService.start()
  -> get manifest/status
  -> resource assessment
  -> PluginHost.ensureStarted(name)
  -> mode별 process start
```

resource assessment 결과가 `critical`이면 start가 blocked된다. `warning` 또는 `unknown`이면 사용자의 confirmation이 필요하다.

### Pipeline job 실행

```text
Angular feature flow
  -> PluginJobService.startJob(pluginName, jobId, params)
  -> POST <NestJS>/jobs
  -> JobsService.enqueueJob()
  -> JobRepository create waiting snapshot
  -> JobQueue claim
  -> pluginHost.ensureStarted(pluginName)
  -> POST <plugin>/jobs { job_id, params }
  -> WS <plugin>/jobs/:jobId/events
  -> plugin progress/completed/error
  -> JobsService.publish()
  -> RealtimeGateway /v1/events
  -> Angular PluginJobService.watchJob()
```

중요한 점:

- Angular는 plugin WebSocket에 직접 붙지 않는다.
- NestJS가 plugin WebSocket을 보고, 자체 realtime gateway로 변환해서 Angular에 보낸다.
- Job 상태는 NestJS `JobRepository`에 저장된다.
- 앱/NestJS restart 시 active job은 interrupted/failed 처리된다.

## PluginHost abstraction

NestJS의 핵심 확장점은 `PluginHost`다.

```ts
abstract class PluginHost {
  canStartProcesses(): boolean
  listManifests(): Promise<PluginManifestView[]>
  getManifest(name): Promise<PluginManifestView | null>
  getStatus(name): Promise<PluginStatus>
  ensureStarted(name): Promise<string>
  stop(name): Promise<void>
}
```

구현체 선택은 `PluginsModule`에서 한다.

```text
if ELECTRON_PLUGIN_HOST_URL exists:
  ElectronPluginHost
else if CLIPPER_PLUGIN_HOST_MODE === static:
  StaticPluginHost
else:
  LocalPluginHost
```

### LocalPluginHost

`local` / `devapp` 기본 구현이다.

동작:

- `CLIPPER_PYTHON_ROOT`가 있으면 그 경로를 사용.
- 없으면 sibling `../clipper_python`를 탐색.
- `plugins/*/manifest.json`을 scan.
- plugin별 process state를 메모리에 보관.
- `PLUGIN_PORT_RANGE_START/END`가 있으면 해당 범위에서 port 할당.
- range가 없으면 OS ephemeral port 할당.
- `uv run --directory <pythonRoot> python -m <pluginName> <port> --idle-timeout 0` 실행.
- Python `.env.<mode>`를 직접 parse해서 non-empty 값만 child process env에 주입.
- `/health`가 OK가 될 때까지 최대 60초 대기.

상태:

- `stopped`
- `starting`
- `running`
- `stopping`
- `error`

concurrent `ensureStarted(name)` 호출은 `startingPromises` map으로 dedupe한다.

### ElectronPluginHost

`packaged` NestJS에서 쓰이는 구현이다.

동작:

- NestJS가 직접 Python process를 spawn하지 않는다.
- `ELECTRON_PLUGIN_HOST_URL`과 `ELECTRON_PLUGIN_HOST_TOKEN`으로 Electron bridge에 요청한다.
- bridge API로 manifest/status/start/stop을 수행한다.
- start 결과로 Python plugin base URL을 받는다.

이 구조의 이유:

- packaged 앱에서 native process, venv, bundled resources, userData path, ffmpeg path는 Electron이 가장 잘 안다.
- NestJS는 workflow control plane 역할을 유지하고, process host 책임은 Electron에 둔다.

### StaticPluginHost

compatibility mode다.

동작:

- `CLIPPER_PLUGIN_HOST_MODE=static`일 때만 사용.
- `PLUGIN_URLS` JSON에서 plugin name별 base URL을 읽는다.
- process spawn/stop을 하지 않는다.
- `/health`로 reachable 여부만 확인한다.

현재 정책상 plugin별 고정 URL env를 기본 실행 경로로 쓰지 않는다.

## Electron packaged bridge

packaged mode의 핵심은 Electron `PluginHostBridgeServer`다.

```text
Electron main
  -> LocalPluginManager
  -> PluginHostBridgeServer starts on 127.0.0.1:<dynamic>
  -> random bearer token generated
  -> ELECTRON_PLUGIN_HOST_URL/TOKEN injected into NestJS process
  -> NestJS ElectronPluginHost calls bridge
```

bridge endpoint:

```text
GET  /plugins
GET  /plugins/:name/manifest
GET  /plugins/:name/status
POST /plugins/:name/start
POST /plugins/:name/stop
GET  /resources
```

보안/격리 특성:

- localhost-only server다.
- random bearer token이 필요하다.
- token은 packaged NestJS env로만 주입된다.
- 외부 remote API가 아니라 같은 앱 내부 process control channel이다.

`POST /plugins/:name/start`는 model install state를 먼저 확인한다. 필수 model file이 없으면 `409 plugin_assets_missing`을 반환하고 Python process를 시작하지 않는다.

## Electron LocalPluginManager

Electron `LocalPluginManager`는 packaged mode의 Python process manager다.

NestJS `LocalPluginHost`와 비슷하지만 packaged 전용 책임이 더 있다.

동작:

- packaged resources의 `clipper_python/plugins` scan.
- manifest load.
- port allocation.
- process state tracking.
- concurrent start dedupe.
- `ensureStartedWithProgress()`로 model loading/download progress callback 제공.
- app shutdown 시 `stopAll()`.

dev spawn:

```text
uv run --directory <pythonRoot> python -m <moduleName> <port> --idle-timeout 0
```

packaged spawn:

```text
<userData>/clipper_venv/bin/python -m <moduleName> <port> --idle-timeout 0
```

Windows packaged에서는 `Scripts/python.exe`를 사용한다.

packaged env injection:

- `ConfigProvider.getPluginEnv()`에서 plugin env를 받는다.
- `CLIPPER_EXECUTION_MODE=packaged`.
- `CLIPPER_LEGACY_FONTS_DIR`.
- `IMAGEIO_FFMPEG_EXE`.
- `IMAGEIO_FFPROBE_EXE`.
- ffmpeg bin dir가 `PATH` 앞에 붙는다.

packaged start 전 preflight:

- venv 준비.
- ffmpeg/ffprobe 준비.

## Python PluginRuntime contract

Python plugin은 `PluginBase`를 상속한다.

plugin 개발자가 구현하는 메서드:

```python
class MyPlugin(PluginBase):
    name = "my_plugin"
    version = "0.1.0"

    def load_models(self) -> None:
        ...

    def run_job(self, request: JobRequest, cancel_flag: CancelFlag) -> dict[str, Any]:
        ...
```

선택 hook:

- `register_extra_routes(app)`: plugin별 custom route 등록.
- `get_runtime_accelerators()`: 실제 선택 accelerator/provider/device 반환.

PluginRuntime이 제공하는 표준 endpoint:

```text
GET    /health
GET    /runtime/accelerators
POST   /jobs
DELETE /jobs/:job_id
POST   /shutdown
WS     /jobs/:job_id/events
```

표준 job submit request:

```json
{
  "job_id": "dance_highlight_...",
  "params": {}
}
```

표준 progress event:

```json
{
  "type": "progress",
  "job_id": "...",
  "progress": 0.35,
  "message": "...",
  "timestamp": 1234567890
}
```

표준 terminal event:

```json
{
  "type": "completed",
  "job_id": "...",
  "status": "completed",
  "result": {},
  "error": null,
  "timestamp": 1234567890
}
```

실행 특성:

- `load_models()`는 FastAPI lifespan에서 server startup 시 실행된다.
- `run_job()`은 `asyncio.to_thread()`로 별도 thread에서 실행된다.
- cancellation은 `CancelFlag`를 통해 cooperative하게 처리한다.
- runtime은 active job task map과 completed result cache를 가진다.
- WebSocket이 job submit보다 먼저 연결되거나 job이 아주 빨리 끝나는 경우를 위해 short grace window와 completed result cache가 있다.
- `report_progress()`는 WebSocket이 연결되어 있을 때 progress event를 보낸다.

OOM/load failure 처리:

- model load 중 VRAM OOM은 exit code `10`.
- RAM OOM은 exit code `11`.
- 기타 load failure는 exit code `12`.
- runtime job 중 VRAM OOM은 `{"error": "VRAM_OOM_RUNTIME"}` 형태의 failed result로 변환된다.

## Manifest schema and catalog

각 Python plugin은 `manifest.json`을 가진다.

현재 필수 field:

- `name`
- `version`
- `display_name`
- `entrypoint`
- `min_app_version`

주요 field:

- `description`
- `author`
- `models`
- `accelerators`
- `capabilities.provides`
- `capabilities.requires`
- `resources.estimated_ram_mb`
- `resources.estimated_vram_mb`
- `resources.preferred_accelerators`
- `resources.cold_start_cost`
- `resources.max_concurrency`
- `resources.idle_policy`
- `permissions`

NestJS와 Electron은 manifest를 읽은 뒤 UI/API용 camelCase DTO로 변환한다.

```text
display_name -> displayName
estimated_ram_mb -> estimatedRamMb
estimated_vram_mb -> estimatedVramMb
preferred_accelerators -> preferredAccelerators
safe_to_evict_when_idle -> safeToEvictWhenIdle
```

현재 주의점:

- manifest schema validation은 얕다. 필수 field 존재만 확인한다.
- `permissions`는 문서화된 intent에 가깝고, 현재 runtime sandbox enforcement로 보이지 않는다.
- model size 정보는 manifest 자체가 아니라 NestJS catalog 또는 Electron hard-coded map에서 보강된다.
- `PLUGIN_CATALOG`는 virtual workflow와 model size/resource metadata 보강 역할을 한다.

## Current plugin inventory

### `dance_highlight`

성격:

- user-facing workflow.
- runtime plugin.

주요 capability:

- provides: `workflow.dance_highlight`
- requires: `video.analyze`, `project.manifest`

모델:

- `yolov8s-pose`
- `insightface-buffalo_l`

특징:

- `load_models()`에서 YOLO pose engine과 InsightFace face cluster service를 초기화한다.
- `get_runtime_accelerators()`는 selected primary device와 pipeline 정보를 반환한다.
- actual member image search owner는 NestJS다. Python env에 Naver/Kakao key를 두지 않는다.

### `dialog_highlight`

성격:

- user-facing workflow.
- runtime plugin.

주요 capability:

- provides: `workflow.dialog_highlight`
- requires: `video.analyze`, `project.manifest`

모델:

- `faster-whisper-small`
- `open-clip-ViT-B-32`

특징:

- `load_models()`에서 Whisper와 CLIP pipeline을 warm-up한다.
- download progress를 `print_download_progress()`로 stdout JSON event로 낸다.
- Electron packaged model download UI가 stdout event를 파싱한다.

### `clipper1_video_render`

성격:

- runtime worker.
- Template Builder와 Clipper Studio render boundary에서 사용.

주요 capability:

- provides: `video.render.legacy_clipper1`
- requires: `template.apply`, `project.manifest`

모델:

- 없음.

특징:

- Template Builder text artifact/subtitle artifact 생성.
- dry run 또는 execute render mode 지원.
- ffmpeg/ffprobe readiness가 필요한 작업 흐름이 있어 Template Builder UI 진입 전에 별도 gate가 있다.

### `clipper1` and `variation`

성격:

- virtual workflow plugin.
- Python runtime plugin이 아니다.

특징:

- NestJS `PLUGIN_CATALOG`에 존재한다.
- `VIRTUAL_WORKFLOW_PLUGINS`로 취급된다.
- status는 installed/stopped로 표현된다.
- start/stop은 runtime process start가 아니라 workflow route 진입과 연결된다.

## Model install and asset readiness

packaged mode에서 model install은 Electron 책임이다.

흐름:

```text
Angular ModelDownloadService.check(pluginName)
  -> window.clipperBridge.modelDownload.modelsNeeded(pluginName)
  -> Electron getPluginInstallState()
  -> actual model file presence check
  -> consent | ready

Angular confirm()
  -> window.clipperBridge.modelDownload.startPlugin(pluginName)
  -> Electron LocalPluginManager.ensureStartedWithProgress()
  -> Python load_models() emits stdout JSON progress
  -> Electron parses stdout
  -> Angular receives IPC progress events
  -> health OK
  -> ready marker written
```

현재 기준:

- source of truth는 marker file이 아니라 실제 model file presence다.
- marker가 없어도 model file이 모두 있으면 marker를 auto-restore한다.
- stale marker가 있어도 model file이 없으면 not installed로 본다.
- non-packaged mode에서는 `modelsNeeded()`가 `needed: false`를 반환한다.

현재 model file path mapping:

- `dance_highlight`
  - `yolov8s-pose`: userData의 `yolov8s-pose.pt`
  - `insightface-buffalo_l`: InsightFace model dir
- `dialog_highlight`
  - `faster-whisper-small`: HuggingFace hub cache
  - `open-clip-ViT-B-32`: HuggingFace hub cache

주의점:

- 새 model-bearing plugin을 추가하면 `plugin-install-state.ts`에 install-state path mapping이 필요하다.
- model size는 Electron `MODEL_SIZE_BYTES`와 NestJS `PLUGIN_CATALOG` 쪽에도 현재 중복되어 있다.

## Resource assessment

NestJS `PluginResourcePolicyService`는 plugin start 전 resource assessment를 만든다.

입력:

- manifest `resourceProfile`
- current plugin status
- host resource snapshot

출력:

- `ok`
- `warning`
- `critical`
- `unknown`
- `not_applicable`

판단:

- start 대상이 아니면 `not_applicable`.
- estimated RAM이 없으면 `unknown` 또는 warning.
- available memory보다 estimate가 크면 `critical`.
- available memory의 70%를 넘으면 `warning`.
- GPU required인데 telemetry가 없으면 warning.
- VRAM estimate가 있고 telemetry가 있으면 VRAM headroom도 확인.

packaged에서는 Electron bridge `/resources`가 Electron main, NestJS, plugin process를 포함한 resource snapshot을 제공한다. local/devapp에서는 static resource host가 쓰인다.

현재 resource assessment는 start admission에 쓰인다. `warning`/`unknown`은 confirmation 필요, `critical`은 blocked다.

## Port management

plugin port는 runtime allocator가 동적으로 할당한다.

지원 방식:

- `PLUGIN_PORT_RANGE_START` / `PLUGIN_PORT_RANGE_END`가 있으면 inclusive range에서 빈 port를 찾는다.
- range가 없으면 OS ephemeral port를 받는다.

중요한 정책:

- `PLUGIN_URL_DIALOG_HIGHLIGHT` 같은 plugin별 고정 포트 env는 기본 경로에서 쓰지 않는다.
- Angular가 port를 알아야 할 이유가 없다.
- NestJS gateway port와 Electron bridge port는 plugin port가 아니다.

현재 기술적 주의점:

- port allocation은 bind-and-release 방식이므로 TOCTOU race window가 있다.
- Electron `PortAllocator` comment에는 retry 필요성이 적혀 있지만 현재 manager start path에 EADDRINUSE retry는 구현되어 있지 않다.
- range mode에서는 claimed set으로 같은 manager 내부 중복은 피한다.

## Job queue and concurrency

NestJS job layer가 pipeline concurrency를 제어한다.

현재 관찰:

- `JobsService.maxGlobalConcurrentJobs = 1`.
- `ExecutionScope` 단위 max concurrent도 queue에서 반영된다.
- Python SDK 자체는 active job map을 갖고 여러 job id를 받을 수 있는 구조다.
- 하지만 현재 NestJS global queue가 1이라 앱 전체에서 한 번에 하나의 pipeline job만 실행된다.
- manifest `resources.max_concurrency`는 resource metadata로 노출되지만, 현재 JobsService에서 직접 per-plugin concurrency limit로 쓰는 구조는 보이지 않는다.

따라서 현재 concurrency의 실질적 owner는 NestJS job queue다.

## Error and status propagation

Plugin start error:

```text
PluginHost.ensureStarted()
  -> spawn failure / health timeout / bridge error
  -> PluginHostUnavailableError or generic error
  -> PluginsController or JobsController maps to HTTP error
  -> Angular displays error
```

Runtime process exit:

- requested stop이면 `stopped`.
- exit code `0`이면 `stopped`.
- non-zero unexpected exit이면 `error`와 `lastError`.
- local/devapp health wait timeout은 error state로 기록된다.

Job error:

```text
plugin run_job returns {"error": "..."}
  -> Python JobResult status failed
  -> WS completed event with error
  -> NestJS statusFromEvent marks failed
```

또는:

```text
plugin WebSocket error/early close
  -> NestJS publishes failed job event
```

Cancellation:

```text
Angular DELETE /jobs/:jobId
  -> NestJS queue remove
  -> if plugin baseUrl exists and job is starting/running:
       DELETE <plugin>/jobs/:jobId
  -> NestJS local state cancelled
```

Python cancellation is cooperative. Plugin implementation must check `cancel_flag.is_set()` in long-running work.

## Extension checklist: add a new runtime plugin

1. Add Python plugin package under `clipper_python/plugins/<plugin_name>/`.
2. Add `manifest.json` with required fields.
3. Add package `pyproject.toml`.
4. Add `<plugin_name>/__main__.py` that parses `port` and `--idle-timeout`, then calls `plugin.run(...)`.
5. Implement `<plugin_name>/app.py` with `PluginBase` subclass.
6. Implement `load_models()` and `run_job()`.
7. Call `report_progress(job_id, progress, message)` during long work.
8. Check `cancel_flag.is_set()` in long-running loops.
9. Add `get_runtime_accelerators()` if device/provider reporting matters.
10. Add or update NestJS `PLUGIN_CATALOG` if the plugin is user-visible or needs size/resource metadata enrichment.
11. Add Angular route mapping and feature UI if user-facing.
12. If packaged model consent is needed, update Electron install-state path mapping.
13. If model sizes should show in UI, update Electron model size maps and NestJS catalog metadata.
14. Smoke in `local`, `devapp`, and `packaged`.

Do not add plugin-specific static port env as the default path.

## Extension checklist: add a virtual workflow plugin

1. Add entry to NestJS `PLUGIN_CATALOG`.
2. Add name to `VIRTUAL_WORKFLOW_PLUGINS` if it has no Python runtime process.
3. Add Angular route mapping if user-visible.
4. Implement workflow API/service in NestJS if it does not map to `/jobs`.
5. Keep runtime start/stop semantics clear: virtual plugin start should not pretend to spawn a Python process.

## Current technical debt and risk areas

### Manifest and metadata duplication

Manifest shape exists in Python JSON, NestJS loader, Electron loader, shared IPC DTO, and Angular DTO. Validation is shallow and model size metadata is duplicated outside manifest.

Risk:

- New fields can silently disappear in one layer.
- Model size/install state can drift between NestJS and Electron.

Likely improvement:

- Define a shared manifest schema.
- Put model size or install-state metadata in one source of truth.
- Generate DTO types or validate with a shared schema.

### Model install state is hard-coded per known plugin

`plugin-install-state.ts` knows exact model paths for `dance_highlight` and `dialog_highlight`.

Risk:

- Adding a model-bearing plugin requires Electron code changes.
- Changing library cache behavior can break install detection.

Likely improvement:

- Extend manifest with install probes.
- Let each plugin declare representative model presence checks.

### Permissions are descriptive, not enforced

Manifest `permissions.filesystem` and `permissions.network` exist, but current runtime does not appear to enforce a sandbox based on them.

Risk:

- Manifest can imply safety boundaries that are not actually enforced.

Likely improvement:

- Treat permissions as documentation until enforcement exists.
- If enforcement is required, design it explicitly at Electron/Python process boundary.

### Capability graph is not a full scheduler

`capabilities.provides/requires` are exposed as metadata. Current observed flow does not use them as a full dependency resolver or scheduler.

Risk:

- Team may assume capability declarations automatically wire workflows.

Likely improvement:

- Document whether capabilities are UI metadata, planning metadata, or executable routing contracts.

### Startup timeout differs by mode

NestJS `LocalPluginHost` waits up to 60 seconds for health. Electron packaged `LocalPluginManager` waits without a fixed timeout while process remains alive.

Risk:

- First local/devapp start of heavy model plugins can time out if model download/load takes longer than 60 seconds.

Likely improvement:

- Separate model install/warm-up from health readiness in local/devapp too, or make timeout mode-aware.

### Port allocation has race window

Allocator binds a port, releases it, then child process binds later.

Risk:

- Another process could grab the port between allocation and plugin bind.

Likely improvement:

- Retry start once on bind/health failure caused by `EADDRINUSE`.
- Or pass an already-bound socket if the runtime protocol is redesigned.

### Resource profile maxConcurrency is not the active limiter

Manifest has `resources.max_concurrency`, but current effective pipeline limiter is NestJS job queue.

Risk:

- Manifest may say max concurrency 1, but enforcement is indirect/global.

Likely improvement:

- Decide whether per-plugin concurrency should be enforced in `JobsService`, `PluginHost`, or Python SDK.

## Files to read for deeper debugging

NestJS:

- [../../clipper_nestjs/src/plugins/plugin-host.ts](../../clipper_nestjs/src/plugins/plugin-host.ts)
- [../../clipper_nestjs/src/plugins/plugins.service.ts](../../clipper_nestjs/src/plugins/plugins.service.ts)
- [../../clipper_nestjs/src/plugins/local-plugin-host.service.ts](../../clipper_nestjs/src/plugins/local-plugin-host.service.ts)
- [../../clipper_nestjs/src/plugins/electron-plugin-host.service.ts](../../clipper_nestjs/src/plugins/electron-plugin-host.service.ts)
- [../../clipper_nestjs/src/jobs/jobs.service.ts](../../clipper_nestjs/src/jobs/jobs.service.ts)

Electron:

- [../../clipper_electron/src/main/plugin/plugin-manager.ts](../../clipper_electron/src/main/plugin/plugin-manager.ts)
- [../../clipper_electron/src/main/plugin/plugin-process.ts](../../clipper_electron/src/main/plugin/plugin-process.ts)
- [../../clipper_electron/src/main/backend/plugin-host-bridge.ts](../../clipper_electron/src/main/backend/plugin-host-bridge.ts)
- [../../clipper_electron/src/main/model-download-ipc.ts](../../clipper_electron/src/main/model-download-ipc.ts)
- [../../clipper_electron/src/main/plugin/plugin-install-state.ts](../../clipper_electron/src/main/plugin/plugin-install-state.ts)

Python:

- [../../clipper_python/clipper_plugin_sdk/clipper_plugin_sdk/base.py](../../clipper_python/clipper_plugin_sdk/clipper_plugin_sdk/base.py)
- [../../clipper_python/clipper_plugin_sdk/clipper_plugin_sdk/routes.py](../../clipper_python/clipper_plugin_sdk/clipper_plugin_sdk/routes.py)
- [../../clipper_python/plugins/dance_highlight/manifest.json](../../clipper_python/plugins/dance_highlight/manifest.json)
- [../../clipper_python/plugins/dialog_highlight/manifest.json](../../clipper_python/plugins/dialog_highlight/manifest.json)
- [../../clipper_python/plugins/clipper1_video_render/manifest.json](../../clipper_python/plugins/clipper1_video_render/manifest.json)

Angular:

- [../../clipper_angular/src/core/plugin-status.service.ts](../../clipper_angular/src/core/plugin-status.service.ts)
- [../../clipper_angular/src/core/plugin-job.ts](../../clipper_angular/src/core/plugin-job.ts)
- [../../clipper_angular/src/core/model-download.service.ts](../../clipper_angular/src/core/model-download.service.ts)
- [../../clipper_angular/src/core/backend-locator.ts](../../clipper_angular/src/core/backend-locator.ts)
