# Clipper2 Video Render Ownership

작성일: 2026-06-09

Status: current architecture decision note

이 문서는 Clipper1 legacy render parity와 무관하게, Clipper2 앱 전체에서 "영상 생성 로직"을 어디에 두는 것이 가장 나은지 정리한다.

핵심 결론:

> Clipper2의 영상 생성은 NestJS 안에 ffmpeg/render 구현을 직접 넣는 구조가 아니라, NestJS가 `video.render` contract와 job/control plane을 소유하고 실제 렌더 실행은 교체 가능한 provider/runtime이 소유하는 구조가 맞다.

현재 로컬 데스크톱 앱 기준 기본 실행 runtime은 Python/FastAPI worker가 가장 자연스럽다. 단, 간단한 ffmpeg transform처럼 Python SDK나 별도 media/model stack이 필요 없는 작업은 NestJS-native `WorkflowExecutor`로 둘 수 있다.

---

## 1. 용어 정리

"영상 생성 로직"은 하나의 덩어리가 아니다. Clipper2에서는 다음 층으로 나누어 봐야 한다.

```text
Workflow / product decision
  어떤 입력으로 어떤 영상을 만들지, 어떤 provider를 쓸지, job/project 상태를 어떻게 남길지

Render contract
  RenderRecipe, VideoRenderJob, ProjectManifest, artifact contract

Preview
  사용자가 최종 렌더 전에 볼 수 있는 편집 중 preview/timeline

Render execution
  ffmpeg 실행, filter graph 구성, media normalize, subtitle/image/audio compositing,
  thumbnail/preview artifact 생성, progress/cancel/result 반환

Runtime / host
  ffmpeg/ffprobe 준비, packaged path, process start/stop, local resource telemetry
```

이 층을 섞으면 NestJS가 렌더러가 되거나, Python worker가 product backend가 되거나, Electron이 queue/project policy를 갖게 된다. Clipper2의 장기 구조는 이 셋을 분리하는 것이다.

---

## 2. 기존 문서에서 다룬 관련 내용

### `.codex/standards/SOLID_AND_BOUNDARIES.md`

Clipper2의 기본 책임 경계를 정의한다.

- Angular: UI state, user interaction, view rendering.
- NestJS: app API, orchestration, project/job/queue state, DTO contract.
- FastAPI plugin: Python compute, model inference, heavy pipeline execution.
- Electron: desktop host, native OS integration, packaged runtime bootstrap.

영상 생성과 관련해서 중요한 내용:

- 상위 workflow는 `local ffmpeg`, `Python worker`, `remote render farm` 같은 실제 구현체를 직접 알면 안 된다.
- workflow가 알아야 하는 것은 provider 이름이 아니라 capability contract다.
- `workflow.clipper_studio -> ... -> template.apply -> video.render`처럼 workflow는 capability를 요청한다.
- NestJS는 capability registry가 policy에 따라 provider를 선택할 수 있는 위치다.
- render recipe가 vendor/local runtime-specific response shape에 묶이면 안 된다.

의미:

- NestJS가 렌더 실행 세부 구현을 직접 소유하면 control plane과 renderer가 섞인다.
- 반대로 Python worker가 project/job/history를 소유해도 boundary 위반이다.
- 올바른 경계는 `NestJS contract/control -> provider/runtime execution`이다.

### `.codex/design/NESTJS_CONTROL_PLANE_REDESIGN.md`

NestJS를 Clipper2의 main app backend/control plane으로 세우는 설계 문서다.

핵심 내용:

- Clipper2의 메인 앱 백엔드와 API control plane은 NestJS가 맡는다.
- FastAPI plugin은 Python 계산 worker로 제한한다.
- Electron은 desktop host/native adapter 역할에 집중한다.
- Python 쪽 책임 예시로 `torch`, `onnxruntime`, `ffmpeg-heavy pipeline`, model inference가 들어간다.
- Angular는 NestJS API를 기본 API surface로 보고, FastAPI나 Electron IPC를 orchestration 용도로 직접 조합하지 않는 방향이다.

의미:

- 영상 생성 요청, job 생성, 상태 기록, project manifest 관리는 NestJS가 소유한다.
- 하지만 ffmpeg-heavy pipeline 자체는 NestJS control plane으로 끌어들이지 않는다.

### `.codex/design/BACKEND_ROLE_SPLIT_CURRENT.md`

현재 backend 역할 분리를 가장 직접적으로 정리한 문서다.

핵심 내용:

- NestJS는 local app API와 control plane이다.
- NestJS 담당은 workflow/plugin catalog, source normalization, job queue/history, project 저장, `ProjectManifest`, `TemplatePreset`, `RenderRecipe`, `VideoRenderJob` contract, provider registry/selection, `WorkflowExecutor` dispatch다.
- Python/FastAPI는 product backend가 아니라 compute worker다.
- Python/FastAPI 담당은 torch/onnx/STT/vision/model inference, Python 생태계가 자연스러운 video-heavy/ffmpeg-heavy 처리, plugin SDK 기반 progress/cancel/result다.
- 참고로 "Python이 자연스러운 작업은 계속 Python/FastAPI worker로 둔다. 간단한 ffmpeg transform처럼 NestJS service/child process로 충분하고 Python SDK가 필요 없는 작업은 NestJS-native `WorkflowExecutor`로 둘 수 있다."

의미:

- Clipper2 전체 기준의 기본 판단도 이 문서와 같다.
- final render처럼 긴 실행, 복합 media compositing, Python media/model stack과 가까운 작업은 Python worker가 자연스럽다.
- 단순 transform은 NestJS-native executor가 허용되는 예외다.

### `.codex/design/WORKFLOW_CAPABILITY_RESOURCE_ARCHITECTURE.md`

Workflow, capability, provider, resource monitoring 관점의 설계 문서다.

핵심 내용:

- 초기 capability 후보에 `template.apply`, `video.render`, `video.analyze`, `asset.store`, `project.manifest`가 포함된다.
- `video.render`는 ffmpeg 기반 최종 렌더링 capability로 정의된다.
- capability 구현 위치 기준은 다음과 같다.
  - API orchestration, provider routing, key policy: NestJS 우선.
  - torch/onnx/STT/vision/video-heavy Python 처리: Python worker.
  - native filesystem/dialog/OS path/open: Electron host adapter.
  - UI state/display only: Angular.
- `video.render` provider 예시는 local ffmpeg, remote render farm이다.
- resource-aware plugin management는 실제 CPU/RAM/GPU를 점유하는 runtime process를 모니터링 대상으로 본다.

의미:

- `video.render`는 workflow가 직접 호출하는 제품 기능이 아니라 공유 capability다.
- 실제 provider/runtime은 local ffmpeg worker일 수도 있고 remote render farm일 수도 있다.
- 이 구조를 유지하려면 workflow와 NestJS API는 provider-specific ffmpeg 구현에 묶이면 안 된다.

### `.codex/design/WORKFLOW_PLUGIN_CAPABILITY_REDESIGN_PLAN.md`

Workflow, capability, provider를 분리하는 장기 설계 문서다.

핵심 내용:

- `video.render`는 "ffmpeg 또는 다른 렌더러로 최종 영상 생성" capability다.
- capability는 꼭 별도 process일 필요가 없다. NestJS service, Electron host 기능, Python worker, 외부 API 중 하나일 수 있다.
- workflow는 특정 provider에 직접 붙지 않고, NestJS control plane이 환경/권한/설정/resource 상태에 맞는 provider를 고른다.
- 목표 구조에서 NestJS는 workflow registry, capability registry, provider registry, source/job/project/resource policy, artifact storage를 소유한다.
- Python compute workers는 model-heavy pipeline, video-heavy pipeline, plugin SDK job runtime을 소유한다.
- Python 소유 범위에는 "ffmpeg/video-heavy 처리 중 Python 생태계가 자연스러운 부분"이 명시되어 있다.
- 초기 권장 결정으로 "`video.render`는 당장은 Python/ffmpeg 기존 경로를 유지하되, API 계약은 `RenderRecipe`로 옮긴다"가 정리되어 있다.

의미:

- 렌더러 구현체의 위치는 provider/runtime 선택 문제다.
- 하지만 contract는 NestJS 중심에 있어야 한다.
- 장기적으로 remote render farm이나 다른 local renderer로 바꿔도 workflow/editor/project model은 유지되어야 한다.

### `.codex/design/WORKFLOW_EXECUTOR_PLUGIN_RUNTIME_DESIGN.md`

Python plugin만 전제로 하던 `/jobs` 실행 단위를 `WorkflowExecutor`로 확장하는 문서다.

핵심 내용:

- 현재 runtime plugin은 Python HTTP/WS process를 전제로 했지만, 앞으로 간단한 ffmpeg 처리처럼 NestJS 안에서 직접 실행하는 workflow도 같은 Store/job/status 모델에 들어와야 한다.
- `JobsService`는 `WorkflowExecutorRegistry`에서 executor를 찾아 실행한다.
- executor runtime kind는 `python_plugin`, `nestjs_executor`, `virtual_workflow`로 나뉜다.
- 첫 NestJS-native executor 예시로 `simple_ffmpeg_transform`이 추가되었다.
- 설계 원칙은 Angular contract 유지, 기존 Python plugin 유지, NestJS-native workflow는 Python HTTP/WS server를 흉내내지 않기, packaged process ownership 유지다.
- ffmpeg process가 NestJS child process일 수는 있지만, Electron의 packaged app host 책임이나 Python packaged venv 책임을 NestJS로 옮기는 것은 아니라고 설명한다.

의미:

- "ffmpeg가 들어가면 무조건 Python"은 아니다.
- 하지만 "final render/video generation engine 전체를 NestJS에 넣자"도 아니다.
- 단순하고 독립적인 transform은 NestJS-native executor가 가능하고, 복합 영상 생성은 provider/runtime 경계 뒤의 worker로 두는 것이 맞다.

### `.codex/design/SHORTFORM_PLUGIN_SPLIT_SHARED_CORE_DESIGN.md`

Clipper1/Variation을 넘어 shared shortform core를 만드는 설계 문서다.

핵심 내용:

- user-facing workflow entry는 virtual workflow로 표현할 수 있고, 최종 render/job 실행은 NestJS `WorkflowExecutor` 경계로 연결한다.
- Python render worker는 `PythonPluginWorkflowExecutor`를 통해 유지하고, NestJS-native job이 필요한 경우 별도 executor로 추가한다.
- workflow별 UI와 시작 방식은 다르지만 render/preview/provider 계약은 같아야 한다.
- final render output은 `video.rendered` artifact로 정규화한다.
- 1차 preview는 Angular-native full shortform preview다.
- MP4를 미리 ffmpeg로 생성하지 않고, `PreviewTimeline`과 DOM/CSS/audio 기반 renderer로 편집 중 preview를 제공한다.
- WASM ffmpeg는 bundle size, 성능, worker 관리, file IO 비용 때문에 1차 preview 기본 경로가 아니다.

의미:

- 편집 preview와 final render는 분리한다.
- Angular가 preview를 담당하더라도 final MP4 생성은 `video.render` job/provider 경계로 간다.
- render와 preview는 같은 `RenderRecipe`에서 파생된 계약을 써야 preview/render 차이를 줄일 수 있다.

### `.codex/design/TEAM_ARCHITECTURE_OVERVIEW.md`

팀원이 Clipper2 전체 구조를 이해하기 위한 요약 문서다.

핵심 내용:

- Clipper2는 Angular UI, NestJS control plane, Electron desktop host, Python worker/plugin runtime, NestJS-native workflow executor가 분리된 다중 process 데스크톱 앱이다.
- Angular는 NestJS API만 호출하고, NestJS가 workflow와 plugin 실행을 조율한다.
- `WorkflowExecutor`가 Python plugin, NestJS-native executor, virtual workflow로 job 실행 단위를 나눈다.
- Electron은 app window, packaged NestJS process host, packaged Python process host, ffmpeg/model download, file dialog 같은 native IPC를 담당한다.
- Python은 영상 분석, 렌더링, 모델 기반 처리처럼 무거운 작업을 수행한다.
- 단순 ffmpeg workflow처럼 NestJS 안에서 직접 실행할 수 있는 작업은 NestJS-native executor로 붙일 수 있다.

의미:

- 이 문서도 "NestJS control plane + worker execution" 모델을 팀 설명용으로 고정하고 있다.
- Clipper2 전체 관점에서 final render는 Python worker 쪽이 기본이고, 단순 transform은 NestJS-native 예외다.

### `.codex/README.RUNTIME.md`

실행 모드별 runtime 정책 요약 문서다.

핵심 내용:

- local 모드에서는 NestJS `WorkflowExecutor`가 Python plugin을 `LocalPluginHost`로 실행하거나 NestJS-native executor를 직접 실행한다.
- devapp 모드도 기본적으로 NestJS `LocalPluginHost` 경로를 따른다.
- packaged 모드에서는 Python plugin process는 Electron bridge가 host하고, NestJS-native executor는 packaged NestJS process 안에서 실행된다.

의미:

- render provider/runtime의 실행 위치는 mode에 따라 host 방식이 달라질 수 있다.
- contract와 dispatch는 NestJS에 두되, packaged Python process host는 Electron bridge를 통해 제어하는 구조가 맞다.

### `.codex/README.OPERATIONS.md`

운영/패키징 관점에서 ffmpeg/ffprobe 준비 상태를 정리한 문서다.

핵심 내용:

- ffmpeg/ffprobe는 Electron download IPC가 준비 상태를 관리한다.
- Template Builder는 sample render와 text preview worker warm-up 때문에 진입 전에 ffmpeg/ffprobe readiness를 확인한다.

의미:

- ffmpeg binary 설치/ready 상태는 OS/package/runtime 문제이므로 Electron host adapter 영역이다.
- 하지만 render job 자체의 product orchestration은 NestJS 경계로 들어오고, 실제 render execution은 provider/runtime에서 수행된다.

### `.codex/context/PROJECT_HISTORY_AND_STATUS.md`

레거시에서 Clipper2로 이어진 구조적 판단의 배경을 모은 문서다.

핵심 내용:

- 과거 문제는 모든 pipeline을 하나의 runtime에 넣은 것과 제품 경계가 코드 경계와 맞지 않은 것이었다.
- 플러그인별로 Python/Torch/ONNX Runtime/DirectML/CUDA 같은 선택을 분리해야 한다는 판단이 있었다.
- NestJS는 앱/API 경계 역할을 맡고, Python은 내부 연산 플러그인 쪽으로 이동한다.
- Python plugin runtime은 FastAPI route, job 관리, cancellation, health 같은 인프라를 갖는 방향으로 정리되었다.

의미:

- 영상 생성/분석처럼 dependency와 resource 특성이 강한 작업을 main app backend에 섞지 않는 것이 Clipper2 재설계의 출발점이었다.

### Clipper1 관련 문서들

다음 문서들은 legacy Clipper1 이식 과정에서 작성되었지만, app-wide decision의 근거라기보다는 이미 같은 경계가 구현에 적용된 예시로 본다.

- `.codex/design/CLIPPER1_INVENTORY_AND_SHARED_CAPABILITY_PLAN.md`
- `.codex/design/CLIPPER_STUDIO_WORKFLOW_REDESIGN.md`
- `.codex/implementation/CLIPPER_STUDIO_CHECKPOINT_*.md`
- `.codex/implementation/CLIPPER1_RENDER_PARITY_CHECKPOINT_*.md`

관련 내용:

- `clipper1_video_render`는 사용자-facing workflow가 아니라 내부 `video.render` provider/runtime이다.
- NestJS는 provider 선택, job 생성, recipe/payload mapping, result recording을 담당한다.
- Python worker는 render execution boundary를 담당한다.

이 문서의 결론은 Clipper1 legacy 경로 때문에 정한 것이 아니다. 다만 Clipper1 이식 기록은 "control plane과 render execution을 분리하는 방식이 이미 적용된 사례"로 참고할 수 있다.

---

## 3. Clipper2 전체 기준 결정

### 3.1 NestJS가 소유해야 하는 것

NestJS는 영상 생성의 product/control layer를 소유한다.

담당:

- Angular가 호출하는 기본 API.
- workflow 선택과 실행 순서 결정.
- `source.ingest`, `template.apply`, `video.render` 같은 capability routing.
- provider registry와 provider 선택 정책.
- resource policy와 실행 가능 여부 판단.
- job queue, retry, cancel, history.
- `ProjectManifest`, `ProjectArtifact`, `RenderRecipe`, `VideoRenderJob` contract.
- render output artifact를 project history에 반영.
- Python worker 또는 NestJS-native executor의 progress/result를 같은 event/job model로 정규화.

NestJS에 두면 좋은 코드는 다음 성격이다.

- "무엇을 만들 것인가"를 결정하는 코드.
- "어떤 provider를 쓸 것인가"를 결정하는 코드.
- "결과를 어떤 project artifact로 기록할 것인가"를 결정하는 코드.
- network/provider key/billing/fallback/retry 같은 product policy.
- 짧고 독립적인 ffmpeg utility transform 중 Python media stack이 필요 없는 코드.

### 3.2 render provider/runtime이 소유해야 하는 것

실제 final MP4 생성 실행은 `video.render` provider/runtime이 소유한다.

담당:

- ffmpeg command/filter graph 구성.
- image/video/audio normalization.
- subtitle burn-in 또는 subtitle track 생성.
- overlay, layout, title, logo, background, transition, motion effect 처리.
- TTS/BGM/audio mix.
- thumbnail/proxy/preview artifact 생성.
- 긴 실행 중 progress parsing.
- cancel signal 처리.
- render 실패 원인 정규화.
- CPU/GPU/RAM을 많이 쓰는 media/model-heavy 단계.

현재 로컬 앱 기준 이 provider/runtime의 기본 형태는 Python/FastAPI worker가 가장 적합하다.

이유:

- Python 생태계가 OpenCV, Pillow, numpy, movie/media utility, model/STT/vision stack과 잘 맞는다.
- Clipper2의 영상 생성은 단순 transcoding보다 media composition, subtitle, template, analysis/model-heavy 처리와 결합될 가능성이 높다.
- 별도 worker process로 격리하면 render crash/OOM이 main app API를 직접 죽이지 않는다.
- process 단위 resource telemetry, start/stop, idle policy, concurrency 제한을 적용하기 쉽다.
- Python worker는 plugin SDK의 progress/cancel/result contract에 맞춰 장시간 job을 표현하기 좋다.
- 나중에 remote render farm, Rust renderer, Node renderer로 교체해도 NestJS의 `video.render` provider contract를 유지할 수 있다.

### 3.3 Electron이 소유해야 하는 것

Electron은 렌더링의 product logic이나 filter graph를 소유하지 않는다. Electron은 desktop host adapter다.

담당:

- packaged Angular/NestJS/Python process bootstrap.
- packaged resource path, userData path, app resources path.
- ffmpeg/ffprobe download, install marker, readiness 확인.
- file dialog, open file, OS integration.
- Python worker process host in packaged mode.
- process telemetry bridge.

Electron에 queue/project/render policy를 넣으면 desktop host와 product backend가 결합된다. 그러면 local/dev/server-like 실행 모드와 API test가 어려워진다.

### 3.4 Angular가 소유해야 하는 것

Angular는 영상 생성의 UI와 preview interaction을 소유한다.

담당:

- 편집 화면 상태.
- user input collection.
- preview timeline display.
- render job 상태 표시.
- provider availability/status 표시.

Angular에 두면 안 되는 것:

- Python worker URL/port 직접 호출.
- ffmpeg provider 선택.
- provider credential/key/billing policy.
- project/job source of truth.
- final MP4 생성 orchestration.

Preview는 별도 문제다. 1차 preview는 Angular-native DOM/CSS/audio 기반으로 두는 것이 맞다. MP4 proof generation이 필요해지면 `PreviewRenderer` 또는 별도 capability 뒤에 둔다.

---

## 4. 왜 final render를 NestJS 내부 구현으로 넣지 않는가

NestJS는 Clipper2의 중심 backend이지만, 중심 backend라는 말이 모든 실행을 직접 해야 한다는 뜻은 아니다.

NestJS 안에 final video render implementation을 넣으면 다음 문제가 생긴다.

### 4.1 control plane과 compute worker가 섞인다

NestJS는 app API, queue, project, provider routing, result recording을 안정적으로 유지해야 한다. 그런데 ffmpeg final render는 CPU/RAM/IO를 오래 점유하고, platform별 binary/path, progress parsing, cancellation, media staging, cleanup까지 동반한다.

이 코드가 NestJS core service 안으로 들어오면 main app API process가 renderer가 된다. render failure, memory pressure, stuck ffmpeg process가 앱 API 안정성과 직접 결합된다.

### 4.2 provider 교체성이 떨어진다

장기적으로 `video.render` provider는 다음처럼 바뀔 수 있어야 한다.

```text
video.render
  -> local_ffmpeg_python_worker
  -> local_ffmpeg_nestjs_executor
  -> remote_render_farm
  -> future_rust_renderer
  -> future_gpu_renderer
```

NestJS service 안에 ffmpeg filter graph와 media composition 세부 구현이 hardcode되면 provider 교체가 API/control plane 수정으로 이어진다. 반대로 NestJS가 `RenderRecipe`와 provider registry만 소유하면 provider 교체는 adapter/runtime boundary에서 끝난다.

### 4.3 video-heavy code는 Python ecosystem과 가깝다

Clipper2의 영상 생성은 단순 `ffmpeg -i input output`이 아니라 다음과 결합될 가능성이 크다.

- image/video crop/fit/cover/letterbox.
- subtitle layout and text measurement.
- image motion, pan, zoom, transition.
- TTS/BGM/audio mix.
- video analysis output 반영.
- face/pose/scene/STT/model 결과와 연결.
- thumbnail/frame extraction.

이 영역은 Python media/model 생태계와 붙는 편이 유지보수 비용이 낮다.

### 4.4 packaged runtime 책임과 충돌한다

ffmpeg binary 준비, packaged resource path, userData path, Python worker bootstrap은 Electron host adapter와 관련이 깊다. NestJS가 final renderer 자체가 되면, NestJS가 packaged ffmpeg path와 process lifecycle 세부를 더 많이 알아야 한다.

필요한 것은 NestJS가 Electron bridge를 통해 readiness/path/status를 요청하는 것이지, Electron 책임을 NestJS로 옮기는 것이 아니다.

### 4.5 UI/API test 경계가 흐려진다

NestJS에는 contract test, job state test, provider selection test가 잘 맞는다. Render worker에는 fixture/golden frame/render output test가 잘 맞는다.

이 둘을 한 process/service에 섞으면 테스트가 무거워지고, 작은 API 변경 검증도 ffmpeg dependency와 묶인다.

### 4.6 NestJS와 FastAPI/Python runtime 차이가 주는 영향

NestJS와 FastAPI/Python의 구조적 차이도 이 판단에 영향을 준다. 다만 결론을 "Node.js는 single-thread라서 영상 생성이 불가능하다"로 이해하면 안 된다.

NestJS는 Node.js 위에서 동작한다. Node.js는 event loop 중심 runtime이고, 한 process의 JavaScript 실행은 일반적으로 main thread 하나에서 돈다. 그래서 API request 처리, orchestration, queue/job state, SSE/WebSocket event, provider routing 같은 I/O 중심 작업에 잘 맞는다. 반대로 CPU-bound 작업을 JavaScript main thread에서 오래 실행하면 event loop가 막혀 API responsiveness가 떨어진다.

하지만 ffmpeg는 보통 JavaScript 안에서 직접 계산하지 않고 `child_process.spawn()`으로 외부 process를 실행한다. 이 경우 실제 encoding CPU 작업은 ffmpeg process가 수행한다. Node.js에도 `worker_threads`, `cluster`, child process 같은 우회 수단이 있다. 따라서 NestJS에서 ffmpeg를 실행하는 것 자체는 기술적으로 가능하고, 짧고 단순한 transform은 NestJS-native executor로 둘 수 있다.

문제는 final video generation이 단순 ffmpeg spawn 하나로 끝나지 않는다는 점이다. 최종 영상 생성 engine이 되면 media staging/cache/cleanup, subtitle/image/audio composition, progress parsing, cancellation, error normalization, template/layout 처리, visual parity test가 함께 붙는다. 이 코드가 NestJS core로 들어오면 Node.js의 event loop 특성과 별개로 control plane이 media compute worker 역할까지 떠안게 된다.

FastAPI/Python도 CPU-bound 작업에 마법처럼 강한 것은 아니다. Python에는 GIL이 있고, 순수 Python CPU-bound thread 병렬 처리에는 한계가 있다. FastAPI도 기본적으로 async I/O web framework다. 다만 Clipper2의 영상 생성은 순수 Python thread computation보다 ffmpeg subprocess, native library, OpenCV/Pillow/numpy/torch/onnx/STT/vision stack, file/media preprocessing과 더 가깝다. 이 영역은 Python 생태계와 process worker 격리가 더 자연스럽다.

따라서 runtime 차이는 다음 정도의 의미를 가진다.

- NestJS/Node.js는 app API와 orchestration에 강하고, 장시간 CPU/media-heavy 작업을 main control plane에 직접 넣으면 event loop responsiveness와 process 안정성에 부담을 준다.
- FastAPI/Python은 media/model-heavy worker를 구성하기 쉽고, native library와 subprocess 기반 작업을 plugin runtime으로 격리하기 좋다.
- ffmpeg 자체는 어느 쪽에서도 spawn할 수 있으므로, 선택 기준은 "실행 가능 여부"가 아니라 "이 작업이 control plane인지, media/render worker인지"다.

---

## 5. 왜 Python/FastAPI worker가 현재 기본값인가

Python worker가 현재 기본값인 이유는 legacy 때문이 아니라, Clipper2의 작업 특성과 맞기 때문이다.

### 5.1 heavy media/model dependency 격리

영상 생성은 ffmpeg뿐 아니라 OpenCV/Pillow/numpy/torch/onnx/STT/vision 계열 dependency와 자주 만난다. 이 dependency를 NestJS main backend에 섞지 않고 Python worker로 격리하면 각 workflow/provider별 dependency 선택이 쉬워진다.

### 5.2 process fault isolation

render job은 길고 실패 가능성이 높다. ffmpeg crash, OOM, invalid media, codec 문제, file lock 문제는 product API와 격리되어야 한다. 별도 worker process면 render worker만 restart하거나 job만 fail 처리할 수 있다.

### 5.3 progress/cancel/result contract

FastAPI plugin runtime은 job submit, event stream, cancel, health, result를 표현하기 쉽다. NestJS는 이 event를 받아 같은 job history로 정규화하면 된다.

### 5.4 local and future remote provider symmetry

Python worker도 provider이고, remote render farm도 provider다. NestJS에서 보면 둘 다 `video.render` provider다. 이 대칭성이 유지되어야 나중에 remote rendering, GPU rendering, cloud offload를 붙이기 쉽다.

### 5.5 main app backend 안정성

NestJS API는 사용자가 프로젝트를 열고, 편집하고, job 상태를 확인하고, 실패 후 재시도할 수 있게 계속 살아 있어야 한다. render engine은 무겁고 불안정할 수 있으므로 별도 runtime이 더 안전하다.

---

## 6. NestJS-native ffmpeg executor가 맞는 경우

다음 조건을 만족하면 NestJS-native `WorkflowExecutor`가 더 단순할 수 있다.

- 작업이 짧고 독립적이다.
- Python SDK/plugin runtime이 필요 없다.
- OpenCV/Pillow/numpy/torch/STT/vision dependency가 없다.
- ffmpeg args가 단순하고 provider 교체 가치가 낮다.
- 실패해도 product API 안정성에 큰 영향을 주지 않도록 child process cleanup이 단순하다.
- output이 하나의 utility artifact 정도다.

예:

- thumbnail 한 장 추출.
- metadata/codec probe.
- 짧은 trim/transcode.
- sample utility transform.
- upload 전 normalize.

반대로 다음 조건이면 Python/FastAPI worker 또는 별도 render provider가 맞다.

- 최종 MP4 생성이다.
- template/layout/subtitle/audio/image/video composition이 있다.
- 여러 asset을 stage/cache/cleanup해야 한다.
- 긴 progress/cancel이 중요하다.
- CPU/RAM/IO를 오래 점유한다.
- model/vision/media Python dependency와 결합된다.
- golden frame, visual parity, render fixture test가 필요하다.

---

## 7. 권장 target architecture

```text
Angular
  -> NestJS App API
      -> SourceService
      -> ProjectService
      -> JobQueueService
      -> CapabilityRegistry
      -> ProviderRegistry
      -> RenderRecipeProvider
      -> WorkflowExecutorRegistry
          -> PythonPluginWorkflowExecutor
              -> video.render local Python/FastAPI worker
          -> NestjsWorkflowExecutor
              -> simple ffmpeg transform when appropriate
          -> RemoteProviderExecutor
              -> future remote render farm
      -> ProjectManifest / ArtifactStore

Electron Host Adapter
  -> packaged NestJS process host
  -> packaged Python worker host
  -> ffmpeg/ffprobe download/readiness
  -> resource path and process telemetry

Python/FastAPI Render Worker
  -> ffmpeg-heavy final render
  -> media normalization
  -> subtitle/image/audio compositing
  -> progress/cancel/result
  -> video.rendered artifacts
```

Important ownership split:

```text
NestJS owns:
  RenderRecipe schema
  VideoRenderJob lifecycle
  provider selection
  job/project history
  artifact registration

Render provider owns:
  how the recipe becomes mp4
  ffmpeg details
  media-specific implementation
  render progress/cancel mechanics
```

---

## 8. Implementation rules for future work

### Rule 1. Final render must go through `video.render`

새로운 숏폼/하이라이트/템플릿 기능이 최종 MP4를 만든다면 직접 ffmpeg를 호출하지 말고 `video.render` capability/provider 경계를 통해 실행한다.

### Rule 2. `RenderRecipe`는 provider-neutral이어야 한다

`RenderRecipe`에는 "무엇을 렌더할지"가 들어가야 한다. 특정 ffmpeg filter syntax, Python-only object, remote API response shape은 들어가면 안 된다.

### Rule 3. NestJS service는 provider adapter까지만 안다

NestJS는 provider id, availability, input/output DTO, job event mapping을 알아도 된다. 하지만 provider 내부의 filter graph, OpenCV pipeline, subtitle image generation 세부 구현은 알면 안 된다.

### Rule 4. Python worker는 product source of truth를 소유하지 않는다

Python worker는 job input을 받아 artifact를 만들고 result를 돌려준다. project history, billing, auth, workflow catalog, user-facing route는 NestJS가 소유한다.

### Rule 5. Electron은 runtime readiness와 host 기능만 담당한다

Electron은 ffmpeg/ffprobe 준비, packaged path, process host, file dialog, telemetry를 담당한다. render queue policy나 project manifest update를 담당하지 않는다.

### Rule 6. Preview와 final render를 분리하되 contract를 공유한다

편집 중 preview는 Angular-native renderer로 빠르게 제공한다. final MP4 render는 `video.render` provider로 보낸다. 둘은 같은 `RenderRecipe` 또는 그로부터 파생된 `PreviewTimeline`을 사용해 차이를 줄인다.

### Rule 7. NestJS-native executor는 예외가 아니라 별도 runtime kind다

간단한 ffmpeg transform을 NestJS-native executor로 만드는 것은 허용된다. 단, 이것도 `WorkflowExecutor`와 job/artifact contract 안에 들어와야 하고, final render provider 경계를 우회하면 안 된다.

---

## 9. Decision checklist

새 영상 관련 기능을 추가할 때 다음 순서로 판단한다.

1. 이 코드는 product state, queue, project, provider policy인가?
   - 그렇다면 NestJS.
2. 이 코드는 사용자의 편집 interaction 또는 immediate preview인가?
   - 그렇다면 Angular.
3. 이 코드는 OS path, packaged resource, ffmpeg install/readiness, process host인가?
   - 그렇다면 Electron host adapter.
4. 이 코드는 final MP4 생성, media composition, ffmpeg-heavy, model/video-heavy 처리인가?
   - 그렇다면 `video.render` provider/runtime. 현재 기본값은 Python/FastAPI worker.
5. 이 코드는 짧고 단순한 ffmpeg transform이며 Python SDK가 필요 없는가?
   - 그렇다면 NestJS-native `WorkflowExecutor`도 가능하다.
6. 이 기능이 나중에 hosted renderer나 다른 local renderer로 바뀔 가능성이 있는가?
   - 그렇다면 반드시 provider contract 뒤에 둔다.

---

## 10. 피해야 할 방향

- Angular가 Python render worker URL/port를 직접 알고 호출한다.
- Electron이 render queue, project history, provider policy를 소유한다.
- NestJS core service에 final render ffmpeg filter graph와 compositing 구현을 직접 넣는다.
- Python/FastAPI worker가 user-facing workflow catalog, project history, auth/billing을 소유한다.
- workflow code가 `local_ffmpeg`, `python_worker`, `remote_render_farm` 같은 provider implementation에 직접 의존한다.
- `RenderRecipe`에 provider-specific response shape이나 local runtime detail을 넣는다.
- preview를 만들기 위해 매번 ffmpeg로 MP4를 생성한다.

---

## 11. 남은 설계 과제

다음은 별도 구현/설계에서 더 구체화해야 한다.

- `RenderRecipe` schema의 provider-neutral 범위.
- `video.render` provider manifest와 capability metadata.
- ffmpeg/ffprobe path env 표준 이름.
- render job concurrency/admission control.
- worker별 estimated RAM/CPU/GPU resource declaration.
- render progress event 표준화.
- remote render farm provider contract.
- preview timeline과 final render recipe 간 diff 검증.
- render output artifact naming/versioning policy.

---

## 12. 최종 판단

Clipper2 전체에서 영상 생성 로직의 가장 좋은 위치는 다음처럼 나뉜다.

```text
영상 생성을 시작하고 기록하는 로직:
  NestJS

영상 생성이 무엇을 의미하는지 표현하는 계약:
  NestJS-owned DTO/contract (`RenderRecipe`, `VideoRenderJob`, `ProjectManifest`)

최종 MP4를 실제로 만드는 로직:
  `video.render` provider/runtime
  현재 local default는 Python/FastAPI worker

간단한 ffmpeg utility transform:
  NestJS-native `WorkflowExecutor` 가능

ffmpeg/ffprobe 설치와 packaged process/path:
  Electron host adapter

편집 중 preview:
  Angular-native preview renderer
```

따라서 "영상 생성 로직을 NestJS에 둘지 Python에 둘지"의 답은 단순한 양자택일이 아니다. NestJS/Node.js와 FastAPI/Python의 runtime 차이는 Python worker 기본값을 강화하는 근거지만, Node.js에서 ffmpeg 실행이 불가능하다는 뜻은 아니다. Clipper2의 올바른 구조는 NestJS가 `video.render` 계약과 orchestration을 소유하고, 실제 render execution은 provider/runtime으로 분리하는 것이다. 그 provider의 현재 기본 구현체로는 Python/FastAPI worker가 가장 적합하다.
