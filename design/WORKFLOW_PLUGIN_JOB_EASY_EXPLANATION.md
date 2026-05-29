# Workflow, Plugin, Job 쉽게 이해하기

작성 기준: 2026-05-29

이 문서는 공식 아키텍처 문서라기보다, 지금 Clipper2 구조를 헷갈리지 않게 이해하기 위한 설명용 문서다.

최대한 쉽게 말하면:

```text
Angular는 화면이다.
NestJS는 일을 접수하고 순서를 정하는 관제탑이다.
WorkflowExecutor는 "이 일을 어떤 방식으로 실행할지" 고르는 실행 어댑터다.
PluginHost는 그중 Python plugin process를 띄우고 끄는 하위 도구다.
Electron은 설치형 앱에서 OS와 실제 process 실행을 맡는 host다.
Python은 무거운 분석/렌더링 작업자다.
```

## 제일 큰 그림

사용자가 앱에서 버튼을 누르면 대충 이런 흐름이다.

```text
사용자
  -> Angular UI
  -> NestJS API
  -> Job 생성
  -> WorkflowExecutor 선택
  -> 실제 실행 방식으로 전달
      -> Python plugin
      -> NestJS-native executor
      -> virtual workflow entry
  -> 진행률/결과 저장
  -> Angular에 다시 표시
```

핵심은 Angular가 직접 Python plugin URL이나 port를 몰라야 한다는 점이다. Angular는 그냥 NestJS API만 호출한다.

## 단어 정리

### Workflow

Workflow는 사용자가 하려는 "제품 기능 흐름"이다.

예:

- Dance Highlight: 댄스 영상에서 하이라이트를 뽑는 흐름.
- Dialog Highlight: 대사가 중요한 영상에서 하이라이트를 뽑는 흐름.
- Clipper1: 숏폼을 만드는 흐름.
- Variation: 여러 변형 숏폼을 batch로 만드는 흐름.
- simple_ffmpeg_transform: 영상을 ffmpeg으로 간단히 변환하는 흐름 예시.

Workflow는 "무엇을 할 것인가"에 가깝다.

### Job

Job은 workflow를 실제로 한 번 실행한 기록이다.

예를 들어 Dance Highlight가 workflow라면:

```text
내가 오늘 17:30에 video-a.mp4로 실행한 Dance Highlight
```

이게 job이다.

같은 workflow를 여러 번 실행하면 job도 여러 개 생긴다.

```text
workflow: dance_highlight
job 1: video-a.mp4 분석
job 2: video-b.mp4 분석
job 3: video-c.mp4 분석
```

그래서 job에는 이런 것이 붙는다.

- jobId
- pluginName
- params
- status: waiting, starting, running, completed, failed, cancelled
- progress
- message
- result
- error
- history

### Plugin

Plugin은 Clipper2에서 조금 헷갈리는 단어다. 하나의 뜻만 있는 게 아니다.

현재는 크게 세 가지로 이해하면 된다.

```text
1. Python runtime plugin
2. NestJS-native workflow executor
3. Virtual workflow entry
```

이 셋이 모두 Plugin Store나 job 모델에 "비슷하게" 보일 수 있다. 그래서 `runtimeKind`로 구분한다.

```text
python_plugin
nestjs_executor
virtual_workflow
```

## Plugin의 세 종류

### 1. Python runtime plugin

실제 Python process로 뜨는 plugin이다.

예:

- `dance_highlight`
- `dialog_highlight`
- `clipper1_video_render`

이 plugin들은 `clipper_python` repo 안에 있다.

실행되면 FastAPI server처럼 떠서 이런 endpoint를 제공한다.

```text
GET  /health
POST /jobs
WS   /jobs/:jobId/events
DELETE /jobs/:jobId
```

예전 구조에서는 NestJS `JobsService`가 이 Python protocol을 직접 알고 있었다.

```text
JobsService
  -> PluginHost.ensureStarted()
  -> POST <python-plugin>/jobs
  -> WS <python-plugin>/jobs/:jobId/events
```

이번 수정 후에는 이 Python-specific 로직을 `PythonPluginWorkflowExecutor`가 맡는다.

```text
JobsService
  -> WorkflowExecutorRegistry.get(pluginName)
  -> PythonPluginWorkflowExecutor.run(context)
      -> PluginHost.ensureStarted()
      -> POST <python-plugin>/jobs
      -> WS <python-plugin>/jobs/:jobId/events
```

즉, Python plugin은 그대로 유지하지만, NestJS job layer가 Python protocol에 직접 묶이지 않게 한 것이다.

### 2. NestJS-native workflow executor

Python process 없이 NestJS 안에서 직접 실행하는 workflow다.

예:

- `simple_ffmpeg_transform`

이건 Python으로 만들 필요가 없다. NestJS에서도 `child_process.spawn('ffmpeg', ...)`로 충분히 처리할 수 있기 때문이다.

흐름은 이런 식이다.

```text
JobsService
  -> WorkflowExecutorRegistry.get('simple_ffmpeg_transform')
  -> NestjsFfmpegTransformExecutor.run(context)
      -> ffmpeg 실행
      -> context.publishProgress(...)
      -> context.complete(...)
```

중요한 점:

- Python HTTP server를 흉내내지 않는다.
- Python plugin port도 없다.
- 그래도 job history, progress, completed/failed/cancelled 모델은 똑같이 쓴다.
- 그래서 UI 입장에서는 "다른 plugin job처럼" 보일 수 있다.

### 3. Virtual workflow entry

아직 직접 실행되는 runtime은 아니지만, Store나 route에 보여야 하는 workflow entry다.

예:

- `clipper1`
- `variation`

이것들은 "Python process 하나를 시작해서 바로 `/jobs`로 실행"하는 구조가 아니다.

`clipper1`은 실제로는 여러 단계가 있다.

```text
입력
  -> script/source 처리
  -> workspace 생성
  -> 편집
  -> render recipe 생성
  -> render worker 실행
  -> project result 저장
```

그래서 `clipper1` 자체를 단순한 Python plugin process 하나로 보면 안 된다.

Virtual workflow는 이렇게 이해하면 쉽다.

```text
앱에 보이는 workflow 카드/입구다.
하지만 그 자체가 바로 실행되는 Python process는 아니다.
```

## WorkflowExecutor가 왜 생겼나

이전에는 job 실행 구조가 사실상 Python plugin 전용이었다.

```text
Job 실행 = Python plugin 시작 + Python /jobs 호출 + Python WebSocket 감시
```

Dance Highlight, Dialog Highlight만 있을 때는 이걸로 괜찮았다.

그런데 이런 요구가 생겼다.

```text
ffmpeg으로 간단히 영상 변환하는 plugin을 만들고 싶다.
근데 이건 Python이 없어도 NestJS에서 바로 할 수 있다.
그래도 Plugin Store, job history, start/stop 모델에는 같은 plugin처럼 보였으면 좋겠다.
```

이 요구를 기존 구조로 처리하려면 이상해진다.

NestJS에서 할 수 있는 일을 굳이 Python FastAPI server로 감싸야 하기 때문이다.

그래서 중간에 `WorkflowExecutor`를 둔 것이다.

```text
JobsService는 이제 실행 방식의 세부사항을 모른다.
그냥 executor를 찾아서 run(context)만 호출한다.
```

실행 방식은 executor가 알아서 처리한다.

```text
Python plugin이면:
  PythonPluginWorkflowExecutor

NestJS 안에서 처리하면:
  NestjsFfmpegTransformExecutor

카드/route만 있는 workflow면:
  VirtualWorkflowExecutor
```

## PluginHost는 이제 뭐냐

`PluginHost`는 없어진 게 아니다. 역할이 더 좁아졌다.

이전에는 사람들이 헷갈리기 쉬웠다.

```text
PluginHost = plugin 전체 실행 시스템?
```

이제는 이렇게 보면 된다.

```text
PluginHost = Python plugin process를 list/start/stop/status 하는 도구
```

즉, `PluginHost`는 Python process를 다루는 하위 계층이다.

```text
WorkflowExecutor
  -> PythonPluginWorkflowExecutor
      -> PluginHost
          -> LocalPluginHost
          -> ElectronPluginHost
          -> StaticPluginHost
```

### LocalPluginHost

`local`, `devapp`에서 쓴다.

NestJS가 직접 `clipper_python`의 plugin을 실행한다.

```text
uv run --directory ../clipper_python python -m dance_highlight <port>
```

### ElectronPluginHost

`packaged`에서 쓴다.

packaged 앱에서는 NestJS가 직접 Python runtime path, userData, bundled resources, venv를 다 관리하기 애매하다. 그래서 Electron이 Python process host가 된다.

```text
NestJS ElectronPluginHost
  -> Electron plugin host bridge
  -> Electron LocalPluginManager
  -> packaged Python plugin process
```

### StaticPluginHost

이미 떠 있는 plugin URL을 보는 compatibility mode다.

기본 개발/packaged 경로는 아니다.

## runtimeKind

`runtimeKind`는 plugin이 어떤 실행 방식인지 알려주는 값이다.

```text
python_plugin
nestjs_executor
virtual_workflow
```

예:

| name | runtimeKind | 뜻 |
| --- | --- | --- |
| `dance_highlight` | `python_plugin` | Python process로 실행 |
| `dialog_highlight` | `python_plugin` | Python process로 실행 |
| `clipper1_video_render` | `python_plugin` | Template/render 뒤에서 쓰는 Python worker |
| `simple_ffmpeg_transform` | `nestjs_executor` | NestJS 안에서 ffmpeg 실행 |
| `clipper1` | `virtual_workflow` | 사용자 workflow entry, 직접 Python process 아님 |
| `variation` | `virtual_workflow` | 사용자 workflow entry, 직접 Python process 아님 |

## Plugin Store는 뭘 보여주나

Plugin Store나 Dashboard는 단순히 Python process 목록만 보여주는 곳이 아니다.

현재 방향은 이렇다.

```text
사용자가 이해해야 하는 workflow/plugin entry를 보여준다.
그리고 실행 가능한 runtime 상태도 함께 보여준다.
```

그래서 Python plugin도 보일 수 있고, NestJS-native executor도 보일 수 있고, virtual workflow도 보일 수 있다.

다만 UI 정책은 다를 수 있다.

예:

- `python_plugin`: start/stop 버튼이 의미 있음.
- `nestjs_executor`: start는 readiness check, stop은 active job 정리 의미.
- `virtual_workflow`: start/stop보다 "화면으로 이동"이 더 자연스러움.

## JobsService는 이제 뭘 하나

`JobsService`는 job의 source of truth다.

담당:

- job 생성
- queue에 넣기
- 순서대로 실행
- cancel/retry/reorder
- job history 저장
- progress/result/error 저장
- realtime event로 Angular에 알리기

하지만 이제 Python protocol을 직접 알지 않는다.

이전:

```text
JobsService가 Python /jobs와 WebSocket까지 직접 처리
```

현재:

```text
JobsService가 WorkflowExecutor를 호출
executor가 자기 실행 방식을 처리
```

이게 구조적으로 중요하다.

새 실행 방식이 생겨도 `JobsService`를 계속 갈아엎지 않아도 된다.

## WorkflowRunContext

executor가 job 결과를 NestJS에 알려줄 때 쓰는 context다.

쉽게 말하면 executor에게 주는 "보고 도구"다.

executor는 이걸로 말한다.

```text
진행률 15%야.
완료됐어.
실패했어.
취소됐는지 확인해줘.
Python plugin baseUrl 저장해줘.
```

코드 느낌은 이렇다.

```ts
context.publishProgress(0.15, 'ffmpeg 변환 실행 중');
context.complete({ outputPath });
context.fail('ffmpeg failed');
context.isCancelled();
```

이 context 덕분에 Python executor든 NestJS-native executor든 job history에 같은 방식으로 기록된다.

## local, devapp, packaged 차이

### local

브라우저에서 Angular를 띄우고 NestJS를 따로 실행한다.

```text
Browser Angular
  -> NestJS
  -> WorkflowExecutor
      -> Python plugin이면 NestJS LocalPluginHost가 실행
      -> NestJS-native면 NestJS가 직접 실행
```

### devapp

Electron 창은 띄우지만 설치형 앱으로 빌드하지 않는다.

```text
Electron window
  -> Angular dev server
  -> NestJS devapp server
  -> WorkflowExecutor
      -> Python plugin이면 NestJS LocalPluginHost가 실행
      -> NestJS-native면 NestJS가 직접 실행
```

### packaged

설치형 앱이다.

```text
Electron packaged app
  -> packaged Angular
  -> packaged NestJS
  -> WorkflowExecutor
      -> Python plugin이면 Electron bridge가 Python process host
      -> NestJS-native면 packaged NestJS process 안에서 실행
```

여기서 중요한 규칙:

- packaged에서 `.env.local`을 읽거나 복사하지 않는다.
- plugin별 고정 port env를 만들지 않는다.
- Python plugin port는 runtime이 동적으로 잡는다.

## 예시로 다시 보기

### Dance Highlight

```text
사용자: Dance Highlight 시작
Angular: POST /jobs
NestJS JobsService: job 생성
WorkflowExecutorRegistry: dance_highlight executor 찾기
PythonPluginWorkflowExecutor:
  -> PluginHost.ensureStarted('dance_highlight')
  -> POST Python /jobs
  -> WS Python /jobs/:jobId/events 감시
JobsService:
  -> progress/history 저장
  -> Angular에 realtime event 전송
```

여기서 `dance_highlight`는 workflow이면서 Python runtime plugin이다.

### simple_ffmpeg_transform

```text
사용자: simple_ffmpeg_transform 시작
Angular: POST /jobs
NestJS JobsService: job 생성
WorkflowExecutorRegistry: simple_ffmpeg_transform executor 찾기
NestjsFfmpegTransformExecutor:
  -> ffmpeg readiness 확인
  -> ffmpeg child process 실행
  -> context.publishProgress()
  -> context.complete()
JobsService:
  -> progress/history 저장
  -> Angular에 realtime event 전송
```

여기에는 Python plugin process가 없다.

### Clipper1

```text
사용자: Clipper1 화면 진입
Angular: Clipper1 route로 이동
NestJS: workspace/source/template/render 관련 API 제공
필요 시 render worker:
  -> clipper1_video_render Python plugin 사용
```

`clipper1` 자체는 virtual workflow entry에 가깝다.

`clipper1_video_render`는 실제 Python runtime worker다.

둘을 같은 것으로 보면 헷갈린다.

## 자주 헷갈리는 질문

### plugin은 항상 Python인가?

아니다.

지금까지 주요 plugin이 Python이었기 때문에 그렇게 보였던 것이다.

앞으로는 세 가지가 있다.

```text
python_plugin
nestjs_executor
virtual_workflow
```

### workflow랑 job은 뭐가 다른가?

workflow는 기능 종류다.

job은 그 기능을 한 번 실행한 기록이다.

```text
workflow: dance_highlight
job: 2026-05-29 17:30에 video-a.mp4로 실행한 dance_highlight
```

### PluginHost랑 WorkflowExecutor는 뭐가 다른가?

`WorkflowExecutor`가 더 위다.

```text
WorkflowExecutor = job을 실제로 실행하는 방식
PluginHost = Python plugin process를 띄우고 끄는 도구
```

Python plugin executor는 내부에서 PluginHost를 사용한다.

NestJS-native executor는 PluginHost를 사용하지 않는다.

### Electron이 workflow를 결정하나?

아니다.

Electron은 OS/native/process host다.

workflow 결정, job queue, job history는 NestJS 책임이다.

### Angular가 plugin port를 알면 안 되는 이유는?

실행 모드마다 port가 달라지고, plugin이 늘어날수록 고정 port/env 방식은 관리가 안 된다.

Angular가 알아야 할 것은 하나다.

```text
NestJS base URL
```

나머지는 NestJS와 runtime이 알아서 처리한다.

### NestJS-native executor가 생기면 Electron 역할이 줄어드나?

Python process host 역할은 줄지 않는다.

다만 모든 작업을 Python process로 만들 필요가 없어질 뿐이다.

Electron은 여전히 packaged 앱에서:

- app window
- packaged NestJS process
- packaged Python process
- native file dialog
- ffmpeg/model download IPC
- packaged resources path

를 맡는다.

## 한 문장으로 정리

이번 구조 변경의 핵심은 이것이다.

```text
NestJS JobsService가 Python plugin protocol에 직접 묶여 있던 구조를 끊고,
WorkflowExecutor라는 실행 계층을 둬서
Python plugin, NestJS-native job, virtual workflow를 같은 plugin/job 모델로 다룰 수 있게 했다.
```

그래서 앞으로 새 기능을 만들 때 질문은 이렇게 하면 된다.

```text
이건 사용자가 보는 workflow인가?
이건 한 번 실행되는 job인가?
이 job은 Python process가 필요한가?
아니면 NestJS에서 직접 실행해도 되나?
아직 실행 runtime 없이 화면 entry만 필요한가?
```

답에 따라 위치가 정해진다.

```text
Python heavy/model/video 분석 -> python_plugin
NestJS에서 충분한 ffmpeg/간단 작업 -> nestjs_executor
화면/route/workflow entry만 우선 필요 -> virtual_workflow
```
