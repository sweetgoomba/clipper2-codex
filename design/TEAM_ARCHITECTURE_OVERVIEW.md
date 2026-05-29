# Clipper2 Team Architecture Overview

작성 기준: 2026-05-29 현재 checkout 확인 결과.

이 문서는 팀원에게 Clipper2의 전체 구조를 설명하기 위한 문서다. 구현 세부사항보다 "어떤 repo가 어떤 책임을 갖고, 실행 시 어떤 프로세스들이 어떻게 연결되는지"를 이해하는 데 초점을 둔다.

## 한 문장 설명

Clipper2는 Angular UI, NestJS control plane, Electron desktop host, Python worker/plugin runtime, NestJS-native workflow executor가 분리된 다중 프로세스 데스크톱 앱이다.

사용자는 하나의 데스크톱 앱을 쓰지만, 내부적으로는 UI, API/control, native host, compute worker가 역할을 나눠 협력한다.

## 전체 그림

```text
User
  |
  v
Angular UI
  |
  | HTTP / events
  v
NestJS control plane
  |
  +-- WorkflowExecutorRegistry
      |
      +-- PythonPluginWorkflowExecutor -> PluginHost -> Python plugins/workers
      +-- NestJS-native workflow executor
      +-- Virtual workflow entry

Electron desktop host
  |
  +-- app window
  +-- packaged NestJS process host
  +-- packaged Python process host
  +-- native IPC: file dialog, ffmpeg/model download, capture, auth
```

핵심은 Angular가 모든 것을 직접 알지 않는다는 점이다. Angular는 NestJS API만 호출하고, NestJS가 workflow와 plugin 실행을 조율한다. NestJS 안에서는 `WorkflowExecutor`가 job 실행 단위를 통합하고, 필요에 따라 Python plugin, NestJS-native executor, virtual workflow로 나눈다. Electron은 데스크톱 앱을 실제로 띄우고 OS/native 기능과 packaged process 실행을 담당한다. Python은 영상 분석, 렌더링, 모델 기반 처리처럼 무거운 작업을 수행한다.

## Repo별 책임

### `clipper_angular`

사용자 화면을 담당한다.

주요 역할:

- Store, Dashboard, Projects, Template Builder, Dance Highlight, Dialog Highlight UI 제공.
- 사용자 입력을 받고 진행 상태를 보여준다.
- NestJS API를 호출한다.
- Electron 환경에서는 preload bridge를 통해 NestJS base URL을 얻는다.

하지 않는 일:

- Python plugin process를 직접 실행하지 않는다.
- plugin URL이나 plugin port를 직접 알지 않는다.
- secret env/API key를 직접 소비하지 않는다.
- packaged runtime에서 `.env.*`를 직접 읽지 않는다.

팀원에게는 "`clipper_angular`는 화면과 사용자 경험만 담당한다. 실제 작업 실행이나 데이터 소유권은 NestJS 뒤쪽에 있다"라고 설명하면 된다.

### `clipper_nestjs`

앱의 control plane이다.

주요 역할:

- Angular가 호출하는 API gateway 역할.
- 프로젝트, 소스, 작업 큐, 작업 이력, 리소스 상태 관리.
- Template Builder official/custom template API 제공.
- Dance Highlight의 artist/member data와 member image search API 제공.
- plugin catalog, plugin status, plugin job orchestration 관리.
- `WorkflowExecutorRegistry`로 Python runtime plugin, NestJS-native executor, virtual workflow를 같은 job/start-stop/status 모델에 연결한다.
- local/devapp에서는 Python plugin process를 `LocalPluginHost`로 직접 실행할 수 있다.
- packaged에서는 Electron plugin host bridge를 통해 Electron이 관리하는 Python process를 제어한다.
- NestJS-native executor는 별도 Python HTTP server 없이 NestJS process 안에서 job을 실행한다.

하지 않는 일:

- 데스크톱 창을 만들거나 native file dialog를 직접 열지 않는다.
- Angular 화면 상태를 직접 소유하지 않는다.
- packaged 앱의 native process host 역할을 직접 맡지 않는다. 단, NestJS-native workflow의 job 단위 child process 실행은 control plane 내부 executor 책임으로 둘 수 있다.

팀원에게는 "`clipper_nestjs`는 Clipper2의 관제탑이다. UI 요청을 받아 workflow를 결정하고, `WorkflowExecutor`로 필요한 실행 방식을 고른 뒤, 결과를 다시 UI에 돌려준다"라고 설명하면 된다.

### `clipper_electron`

데스크톱 앱 host이자 native adapter다.

주요 역할:

- Electron window 생성.
- packaged 앱에서 Angular 정적 파일 로드.
- packaged 앱에서 NestJS bundle 실행.
- packaged 앱에서 Python plugin process 실행.
- NestJS가 Python plugin을 제어할 수 있도록 plugin host bridge 제공.
- ffmpeg/ffprobe download IPC와 readiness 관리.
- model download/install IPC와 상태 관리.
- file dialog, capture, YouTube auth 같은 OS/native 기능 제공.
- macOS/Windows installer packaging.

하지 않는 일:

- 비즈니스 workflow를 직접 결정하지 않는다.
- Template Builder나 Dance Highlight의 domain API를 직접 제공하지 않는다.
- Angular가 직접 처리해야 할 UI 상태를 소유하지 않는다.

팀원에게는 "`clipper_electron`은 설치형 앱 껍데기이자 OS 연결 계층이다. packaged 모드에서는 내부 NestJS와 Python worker를 실제 프로세스로 띄우는 host 역할도 한다. 다만 NestJS-native workflow의 실행 판단과 job 기록은 NestJS에 남는다"라고 설명하면 된다.

### `clipper_python`

무거운 작업을 수행하는 plugin/worker workspace다.

주요 역할:

- `dialog_highlight` plugin.
- `dance_highlight` plugin.
- `clipper1_video_render` plugin.
- template text preview artifact 생성.
- sample render, video render, analysis 같은 compute 작업 처리.
- 공통 plugin SDK 제공.

하지 않는 일:

- Angular UI를 제공하지 않는다.
- NestJS API gateway 역할을 하지 않는다.
- Naver/Kakao image search key를 소유하지 않는다.
- member image search API의 owner가 아니다. 현재 owner는 NestJS다.

팀원에게는 "`clipper_python`은 실제 계산 작업자다. NestJS가 일을 시키면 Python plugin이 영상 처리, 분석, 렌더링을 수행한다"라고 설명하면 된다.

## 프로세스 흐름

### 일반적인 작업 실행 흐름

```text
1. 사용자가 Angular UI에서 작업을 시작한다.
2. Angular는 NestJS API를 호출한다.
3. NestJS는 요청을 검증하고 project/job/workflow 상태를 만든다.
4. NestJS는 `WorkflowExecutorRegistry`에서 실행할 executor를 찾는다.
5. executor가 Python plugin, NestJS-native worker, virtual workflow 중 맞는 경로로 작업을 수행한다.
6. 진행 상태와 결과는 NestJS를 거쳐 Angular에 표시된다.
```

이 구조 덕분에 UI는 plugin process의 세부 실행 방식에 묶이지 않는다. plugin 실행 방식이 local/devapp/packaged에서 달라져도 Angular 쪽 계약은 NestJS API 호출로 유지된다.

### packaged 앱 실행 흐름

```text
1. 사용자가 설치된 Clipper2 앱을 실행한다.
2. Electron main process가 시작된다.
3. Electron이 packaged resources에서 Angular renderer를 로드한다.
4. Angular는 Electron preload bridge로 NestJS base URL을 요청한다.
5. Electron은 내부 NestJS bundle을 동적 port로 실행한다.
6. NestJS가 ready 상태가 되면 Angular가 API를 호출한다.
7. Python plugin이 필요하면 NestJS의 Python executor가 Electron plugin host bridge에 요청한다.
8. Electron이 packaged Python runtime/plugin process를 실행한다.
9. NestJS-native executor는 packaged NestJS process 안에서 실행된다. 필요한 OS/native path 주입은 Electron packaged env/runtime 정책을 따른다.
```

packaged 모드에서 NestJS port와 plugin port는 고정값이 아니다. 런타임이 동적으로 할당하고, 필요한 연결 정보만 내부적으로 전달한다.

## 실행 모드

Clipper2의 실행 모드는 `local`, `devapp`, `packaged` 세 가지다.

| 모드 | 용도 | UI | NestJS | Python plugin | env |
| --- | --- | --- | --- | --- | --- |
| `local` | 브라우저 기반 개발 | Angular dev server | 직접 실행 | NestJS가 필요 시 실행 | `.env.local` |
| `devapp` | 패키징하지 않은 Electron 앱 개발 | Electron + Angular dev server | 직접 실행 | NestJS가 필요 시 실행 | `.env.devapp` |
| `packaged` | 실제 설치형 앱 | Electron packaged renderer | Electron이 내부 실행 | Electron/NestJS가 관리 | `.env.packaged` |

### `local`

브라우저에서 Angular dev server를 직접 열어 개발하는 모드다.

```text
Browser
  -> Angular dev server
  -> NestJS dev server
  -> Python plugin, 필요 시 NestJS LocalPluginHost가 실행
```

이 모드에서는 Electron을 실행하지 않는다.

### `devapp`

패키징하지 않은 Electron shell에서 실제 데스크톱 앱에 가까운 흐름을 확인하는 모드다.

```text
Electron devapp
  -> Angular dev server를 BrowserWindow에 로드
  -> 외부에서 실행 중인 NestJS API 호출
  -> Python plugin, 필요 시 NestJS LocalPluginHost가 실행
```

이 모드는 installer 산출물을 만들지 않는다. 데스크톱 창, preload bridge, Electron IPC 흐름을 개발 중 확인하기 위한 모드다.

### `packaged`

실제 설치형 앱 모드다.

```text
Electron packaged app
  -> bundled Angular static files
  -> bundled NestJS server
  -> bundled Python runtime/plugins
```

packaged에서는 Electron이 process host 역할을 맡는다. NestJS와 Python plugin은 앱 내부 resources에서 실행되고, env는 packaged resources의 `.env.packaged`만 사용한다.

## Env/runtime 규칙

현재 env/runtime 설계의 핵심은 실행 모드를 명확히 분리하는 것이다.

규칙:

- packaged build/runtime은 `.env.local`, `.env.devapp`, generic `.env`를 읽거나 복사하지 않는다.
- 각 repo는 자신이 소비하는 env 파일만 가진다.
- 실제 `.env.<mode>` 파일에는 값이 있는 key만 둔다.
- optional blank placeholder를 real env 파일에 넣지 않는다.
- OS별 env 파일을 만들지 않는다.
- Windows/Mac별 absolute path를 env에 기본값처럼 넣지 않는다.
- 표준 sibling checkout이나 packaged resources에서 path를 추론해야 한다.
- plugin별 고정 포트를 env에 나열하지 않는다.
- plugin port는 mode별 runtime이 동적으로 할당한다.

Repo별 env 소유권:

- `clipper_nestjs`: NestJS API, image search keys, Template Builder DB/S3, plugin orchestration 설정.
- `clipper_python`: Python plugin이 직접 소비하는 runtime credential.
- `clipper_electron`: devapp renderer URL과 NestJS base URL처럼 Electron이 직접 소비하는 값.
- `clipper_angular`: secret env를 직접 소비하지 않음. build/serve configuration으로 mode만 구분.

## Plugin/workflow runtime boundary

Plugin/workflow 실행은 다음 원칙을 따른다.

```text
Angular
  -> NestJS /plugins, /jobs, feature API
  -> WorkflowExecutorRegistry
      -> PythonPluginWorkflowExecutor
          -> PluginHost abstraction
          -> LocalPluginHost | ElectronPluginHost | StaticPluginHost
          -> Python plugin HTTP server
      -> NestJS-native executor
      -> VirtualWorkflowExecutor
```

현재 기본 방향:

- `local` / `devapp`: NestJS `LocalPluginHost`가 Python plugin process를 실행한다.
- `packaged`: NestJS `ElectronPluginHost`가 Electron bridge를 통해 Python plugin process를 제어한다.
- NestJS-native executor는 Python process를 만들지 않고 NestJS 내부 service/child process로 job을 실행한다.
- virtual workflow는 Store/Dashboard entry와 route 성격이며, 직접 `/jobs` runtime이 아닐 수 있다.
- `StaticPluginHost`: compatibility mode다. 기본 경로에서 plugin별 고정 URL을 쓰지 않는다.

이 boundary가 중요한 이유:

- plugin이 늘어나도 Angular 수정 없이 NestJS catalog/API 중심으로 확장할 수 있다.
- port 충돌을 env 파일로 관리하지 않고 runtime allocator로 처리할 수 있다.
- packaged와 dev 실행 방식이 달라도 Angular의 API 계약은 유지된다.

## 대표 기능으로 보는 구조

### Template Builder

Template Builder는 top-level `템플릿` 메뉴에서 system/custom template family와 ratio variant를 편집하는 기능이다.

구조:

```text
Angular Template Builder UI
  -> NestJS Template Builder API
  -> official template registry / S3 asset / local custom JSON
  -> 필요 시 WorkflowExecutor -> clipper1_video_render Python plugin
```

중요한 현재 기준:

- Template Builder 목록 API 자체는 ffmpeg/ffprobe를 직접 쓰지 않는다.
- 하지만 text preview renderer warm-up과 sample render는 `clipper1_video_render` worker를 사용한다.
- 그래서 본 UI는 ffmpeg/ffprobe ready 이후에 시작한다.
- Angular는 ffmpeg/ffprobe readiness를 확인하고, ready 전에는 Template Builder 본 UI를 렌더링하지 않는다.
- sample render 요청도 ffmpeg/ffprobe ready 여부를 다시 확인한다.

팀원에게는 "템플릿 목록 조회는 NestJS API지만, 미리보기/샘플 렌더는 Python render worker까지 이어지는 흐름이다. 그래서 화면 진입 전에 ffmpeg/ffprobe 준비를 확인한다"라고 설명하면 된다.

### Dance Highlight

Dance Highlight는 artist/member detection, member image selection, reference image selection, pipeline execution을 포함한다.

구조:

```text
Angular Dance UI
  -> NestJS Dance API
  -> NestJS image search / artist-member data
  -> WorkflowExecutor -> dance_highlight Python plugin
```

중요한 현재 기준:

- member image search는 Python plugin이 아니라 NestJS image search API가 담당한다.
- Naver/Kakao image search key는 NestJS env에 있어야 한다.
- Python env에는 Naver/Kakao key를 두지 않는다.
- member image selection 화면은 내부 단계 컨테이너가 스크롤을 소유한다.

팀원에게는 "Dance UI는 후보 이미지와 작업 흐름을 NestJS에 요청하고, 실제 분석/처리는 dance_highlight Python plugin이 맡는다. 이미지 검색 credential은 NestJS 소유다"라고 설명하면 된다.

## Build/package 흐름

설치형 앱 build는 `clipper_electron`의 build script가 전체 repo를 묶는다.

큰 단계:

```text
1. clipper_angular build:packaged
2. clipper_nestjs bundle
3. clipper_electron TypeScript compile
4. target platform용 uv binary 준비
5. electron-builder로 installer 생성
```

packaged resources에 포함되는 핵심:

- Angular build output.
- NestJS bundled output.
- `clipper_nestjs/.env.packaged`.
- Python plugin source/SDK.
- `clipper_python/.env.packaged`.
- target platform용 `uv` binary.

packaged resources에 포함하면 안 되는 것:

- `.env.local`
- `.env.devapp`
- generic `.env`
- Python virtualenv cache
- test/build/cache artifacts

## Windows packaging 운영 기준

Windows packaged build에서 과거 발생한 `EBUSY`는 Clipper2 코드 문제가 아니라 PowerToys `Command Palette`가 새로 생성된 `Clipper2.exe`를 잡으면서 발생한 file sharing conflict로 정리됐다.

현재 기준:

- Windows build 중에는 PowerToys `Command Palette`를 끈다.
- `Keyboard Manager`는 사용해도 된다.
- `win.asar: false`를 다시 넣지 않는다.
- electron-builder Step 5 retry를 다시 넣지 않는다.
- build script lock cleanup/fail-fast 우회를 다시 넣지 않는다.

팀원에게는 "Windows 빌드 EBUSY는 앱 packaging 구조 문제가 아니라 외부 프로세스가 exe를 잡은 운영 환경 문제다. 해결책은 build script 우회가 아니라 Command Palette를 끄는 것"이라고 설명하면 된다.

## Current repo snapshot

2026-05-29 세션 기준:

```text
.codex:           workflow-executor-design, docs pending
clipper_nestjs:   design/workflow-executor, WorkflowExecutor implementation pending, base main @ 73c2519
clipper_electron: main @ f701677 Revert "Update electron builder"
clipper_angular:  main @ 70d6e58 Improve template sample render flow
clipper_python:   main @ 535131c Render sample images as cover
```

`.codex`는 별도 git repo다. 앱 코드 변경과 `.codex` 문서 변경은 별도 commit으로 관리한다.

## 팀 설명용 짧은 스크립트

회의에서 짧게 설명해야 하면 아래 순서로 말하면 된다.

1. Clipper2는 단일 앱처럼 보이지만 내부적으로는 Angular, NestJS, Electron, Python 네 영역으로 나뉜 다중 프로세스 앱이다.
2. Angular는 화면이다. 사용자가 보는 UI와 interaction을 담당하고 NestJS API만 호출한다.
3. NestJS는 control plane이다. 프로젝트, 템플릿, 작업 큐, WorkflowExecutor dispatch, image search 같은 앱의 중심 로직을 관리한다.
4. Electron은 데스크톱 host다. 창을 띄우고, packaged 앱에서 NestJS와 Python process를 실행하고, native IPC와 installer packaging을 담당한다.
5. Python은 주요 worker/plugin runtime이다. 영상 분석, 렌더링, 모델 기반 처리처럼 무거운 작업을 한다. 단순 ffmpeg workflow처럼 NestJS 안에서 직접 실행할 수 있는 작업은 NestJS-native executor로 붙일 수 있다.
6. 실행 모드는 `local`, `devapp`, `packaged` 세 가지이고, 각각 `.env.local`, `.env.devapp`, `.env.packaged`만 사용한다.
7. packaged 앱에서는 `.env.local`을 절대 읽거나 복사하지 않고, plugin port도 고정 env로 관리하지 않는다.
8. Windows build의 `EBUSY`는 PowerToys Command Palette의 외부 lock 이슈로 정리되어 있고, 코드 우회는 다시 넣지 않는다.

## 헷갈리기 쉬운 질문

### Angular가 Python plugin을 직접 호출하나?

아니다. Angular는 NestJS API만 호출한다. plugin URL/port는 Angular가 몰라야 한다.

### Electron이 백엔드인가?

일반적인 API backend는 NestJS다. Electron은 desktop host/native adapter이고, packaged 앱에서 NestJS와 Python process를 실행하는 host 역할을 한다.

### NestJS와 Electron은 둘 다 process를 관리하나?

mode와 executor 종류에 따라 다르다. local/devapp에서는 NestJS가 Python plugin process를 직접 실행할 수 있다. packaged에서는 Electron이 Python native process host 역할을 하고, NestJS는 Electron bridge를 통해 제어한다. NestJS-native executor는 Python plugin process가 아니라 NestJS 내부 실행 단위다.

### WorkflowExecutor와 PluginHost는 뭐가 다른가?

`WorkflowExecutor`는 `/jobs` 실행 단위다. Python plugin, NestJS-native executor, virtual workflow를 같은 job/start-stop/status 모델로 묶는다. `PluginHost`는 그중 Python plugin process를 list/start/stop/status 하는 낮은 계층이다.

### 왜 plugin port를 env에 고정하지 않나?

plugin이 늘어날수록 plugin별 port env를 관리할 수 없기 때문이다. runtime allocator가 동적으로 port를 할당하고 registry가 현재 상태를 관리하는 구조가 맞다.

### Dance member image search key는 어디에 있어야 하나?

NestJS env에 있어야 한다. 현재 member image search owner는 NestJS이고, Python env에는 Naver/Kakao key를 두지 않는다.

### Template Builder는 왜 ffmpeg/ffprobe 준비 후 시작하나?

목록 조회만 보면 필요 없어 보이지만, 페이지 진입 시 text preview renderer warm-up이 있고 sample render도 `clipper1_video_render` worker를 사용한다. 사용자 관점에서는 Template Builder 기능 진입 전에 ffmpeg/ffprobe readiness를 보장하는 것이 맞다.

## 더 자세히 볼 문서

- [../README.ARCHITECTURE.md](../README.ARCHITECTURE.md)
- [PLUGIN_SYSTEM_TECHNICAL_ANALYSIS.md](PLUGIN_SYSTEM_TECHNICAL_ANALYSIS.md)
- [WORKFLOW_EXECUTOR_PLUGIN_RUNTIME_DESIGN.md](WORKFLOW_EXECUTOR_PLUGIN_RUNTIME_DESIGN.md)
- [../README.RUNTIME.md](../README.RUNTIME.md)
- [../README.OPERATIONS.md](../README.OPERATIONS.md)
- [../operations/env-runtime/records/2026/05/21-execution-env-mode-design.md](../operations/env-runtime/records/2026/05/21-execution-env-mode-design.md)
- [../operations/env-runtime/runbooks/execution-mode-runbook.md](../operations/env-runtime/runbooks/execution-mode-runbook.md)
- [../operations/windows-packaging/records/2026/05/21-powertoys-ebusy-diagnosis.md](../operations/windows-packaging/records/2026/05/21-powertoys-ebusy-diagnosis.md)
- [../features/template-builder/records/2026/05/22-angular-template-builder-and-dance-ui-checkpoint.md](../features/template-builder/records/2026/05/22-angular-template-builder-and-dance-ui-checkpoint.md)
