# Clipper2 다음 구조 설계 초안

작성일: 2026-04-29

> 개정 필요: 이 문서는 Electron main process에 `PipelineQueueManager`를 두는 방향으로 작성된 초안이다. 이후 NestJS를 팀의 메인 백엔드/control plane으로 유지해야 한다는 기준을 반영해 `.codex/NESTJS_CONTROL_PLANE_REDESIGN.md`를 추가했다. 2026-05-29 기준으로는 NestJS `WorkflowExecutorRegistry`가 `/jobs` 실행 dispatch의 현재 기준이다. 앞으로의 기준 문서는 NestJS control plane 설계와 `WORKFLOW_EXECUTOR_PLUGIN_RUNTIME_DESIGN.md`를 우선한다.

이 문서는 현재 Clipper2 구조를 쉽게 다시 설명하고, 다음 큰 리팩터링 축을 어디에 둬야 하는지 정리한다. 핵심 결론은 다음이다.

> Clipper2의 다음 중심축은 "플러그인 실행"이 아니라 "앱 레벨 Pipeline Queue / Project Orchestration"이어야 한다.

현재는 플러그인 스토어와 대시보드가 생겼지만, 실제 제품 경험은 아직 각 파이프라인 화면이 직접 Python plugin job을 시작하는 구조다. Dance/Dialog만 있을 때는 버틸 수 있지만, YouTube 입력, 여러 작업 대기열, 결과 히스토리, Clipper1 통합까지 가면 이 구조는 빠르게 한계에 부딪힌다.

---

## 1. 현재 구조를 한 문장씩 이해하기

### Angular

Angular는 사용자가 보는 조종석이다.

- 화면, 입력 폼, 진행률 표시, 결과 표시를 담당한다.
- Electron preload bridge를 통해 파일 선택, 플러그인 URL, 다운로드 상태를 얻는다.
- 현재는 Python plugin의 `/jobs`와 WebSocket에 직접 연결해서 job을 시작하고 진행률을 받는다.
- 단, Python 프로세스를 직접 띄우거나 죽이지는 않는다. 그 책임은 Electron에 있다.

### Electron

Electron은 로컬 앱의 호스트이자 운영자다.

- Angular renderer를 띄운다.
- Python plugin process를 시작/중지하고, port를 배정하고, health check를 한다.
- NestJS local API process를 띄우고 URL을 Angular에 알려준다.
- ffmpeg/model 다운로드, venv 준비, 로그, 파일 다이얼로그, 패키징을 담당한다.
- 사용자의 PC 자원과 OS 기능에 직접 닿는 책임은 Electron에 모여 있다.

### NestJS

현재 NestJS는 파이프라인 실행 서버가 아니다.

- 지금은 dance pre-pipeline API를 담당한다.
- 예: 영상 제목에서 아티스트 후보 찾기, Wikidata로 멤버 조회, Naver/Kakao 이미지 검색.
- 앞으로는 LLM proxy, 구독/인증 bridge, remote server 연동 같은 "로컬 앱 API" 역할로 확장될 수 있다.
- Python heavy pipeline을 직접 중계하는 gateway로 쓰는 구조는 현재 방향이 아니다.

### Python Plugin

Python plugin은 무거운 계산을 수행하는 독립 실행 단위다.

- `dance_highlight`, `dialog_highlight`처럼 플러그인마다 별도 FastAPI 서버로 뜬다.
- SDK가 `/health`, `/jobs`, `/jobs/{id}/events`, cancel, progress, idle shutdown 같은 공통 런타임을 제공한다.
- 각 plugin은 자기 모델, 자기 의존성, 자기 파이프라인 코드를 가진다.
- 현재 앱 번들에는 plugin source가 포함되고, first-run에서 `uv sync`로 실행 환경을 만든다.

### Remote Server

아직 본격 구현되지 않았지만, 장기적으로 반드시 필요하다.

- 사용자 로그인, 구독, 결제
- LLM API key 보호
- plugin registry / CDN manifest
- 사용량 제한, 권한 제어

로컬 앱은 계산을 하고, remote server는 계정/권한/비밀키/배포 카탈로그를 맡는 구조가 맞다.

---

## 2. 현재 Clipper2가 이미 해결한 것

### 2.1 PyInstaller 단일 exe 문제에서 벗어남

레거시 HighlightStudio에서는 torch, onnxruntime, insightface, CUDA, PyInstaller frozen 환경이 한 실행파일 안에서 충돌했다. Clipper2는 이 문제를 "플러그인 프로세스 격리"와 "uv 기반 소스 실행"으로 풀고 있다.

이 결정은 맞다. 앞으로 플러그인이 5개, 10개로 늘어나도 모든 의존성을 하나의 exe에 넣지 않아도 된다.

### 2.2 플러그인 스토어/대시보드의 기본형이 생김

현재 구현된 의미는 다음과 같다.

- Store: 사용자가 플러그인 실행에 필요한 모델/ffmpeg asset을 준비하는 화면
- Dashboard: 설치된 플러그인 프로세스를 수동으로 시작/중지하고 상태를 보는 화면

주의할 점은 "설치"의 의미다. 현재 plugin package 자체는 앱 번들에 들어 있다. 사용자가 설치한다고 느끼는 대상은 모델 파일과 ffmpeg 같은 실행 asset이다.

### 2.3 모델/ffmpeg 다운로드 UX가 생김

기존에는 라이브러리가 조용히 모델을 다운로드했다. 지금은 동의 오버레이, 진행률, 모델별 상태, 로그가 생겼다.

이건 B2B 설치형 앱에서 중요하다. 사용자가 몇백 MB에서 몇 GB 파일이 갑자기 내려받아지는 상황을 설명할 수 있어야 한다.

### 2.4 Electron packaged app 빌드가 동작함

현재 build pipeline은 대략 다음이다.

1. Angular build
2. NestJS ncc bundle
3. Electron TypeScript compile
4. uv binary 준비
5. electron-builder packaging

즉 Clipper2는 이미 "설치형 앱으로 만들 수 있는 최소 구조"까지 도달했다.

---

## 3. 지금 구조의 가장 큰 빈틈

현재 가장 큰 빈틈은 "앱 레벨 작업 관리"가 없다는 점이다.

지금 흐름은 대략 이렇다.

```text
Angular dance/dialog page
  -> PluginJobService.startJob(pluginName, params)
  -> Electron에서 plugin URL 얻음
  -> Angular가 Python plugin /jobs 호출
  -> Angular가 WebSocket 구독
  -> 해당 화면의 store가 진행률/결과 보관
```

이 구조의 문제는 다음이다.

- 사용자가 화면을 떠나면 job 상태를 앱 전체에서 안정적으로 추적하기 어렵다.
- 여러 job을 순서대로 처리하는 queue가 없다.
- dance와 dialog를 동시에 실행하면 PC 자원 충돌을 앱이 통제하지 못한다.
- job history, retry, cancel, reorder, result reopen 같은 제품 기능이 들어갈 중심이 없다.
- YouTube 다운로드 같은 source preparation을 어디서 관리할지 불명확해진다.
- Clipper1처럼 복잡한 "프로젝트 생성 -> 클립 구성 -> 미디어/TTS -> 렌더" 흐름을 붙이면 Angular page가 너무 많은 책임을 갖게 된다.

따라서 다음 리팩터링은 새 UI를 더 붙이는 것이 아니라, 앱 내부에 `PipelineQueueManager`와 `Project` 개념을 세우는 것이다.

---

## 4. 다음 큰 축: Pipeline Queue / Project Orchestration

### 4.1 목표

목표는 Angular가 더 이상 plugin job을 직접 소유하지 않게 만드는 것이다.

권장 흐름:

```text
Angular
  -> Electron IPC: queue.enqueue(...)

Electron PipelineQueueManager
  -> plugin 설치 상태 확인
  -> plugin start/URL 확보
  -> Python /jobs 호출
  -> Python WebSocket 구독
  -> 진행률/결과/오류를 앱 레벨 job state에 저장
  -> Angular에 queue event push
```

Angular는 "작업을 제출하고 상태를 본다"에 집중한다. job 실행, 순서, 취소, 재시도, plugin lifecycle은 Electron이 맡는다.

### 4.2 왜 Electron에 QueueManager를 두는가

QueueManager는 Electron main process에 두는 것이 맞다.

이유:

- plugin process lifecycle이 Electron에 있다.
- port allocation, health check, stop/restart가 Electron 책임이다.
- app shutdown 때 진행 중 job을 어떻게 처리할지 Electron이 가장 잘 안다.
- userData 경로, 로그 경로, output root 기본값도 Electron이 안다.
- Angular는 reload될 수 있으므로 queue source of truth가 되면 안 된다.
- Python plugin 하나에 queue를 넣으면 여러 plugin을 가로지르는 전역 순서 제어가 불가능하다.

NestJS에 queue를 둘 수도 있지만, 지금 NestJS는 local API 프로세스이고 plugin host 권한이 없다. 결국 Electron과 강하게 결합해야 하므로 복잡도만 늘어난다.

### 4.3 핵심 모델

최소 모델은 `Project`와 `PipelineJob` 두 개다.

```ts
type PipelineJobStatus =
  | 'waiting'
  | 'starting'
  | 'running'
  | 'completed'
  | 'failed'
  | 'cancelled';

interface PipelineJob {
  id: string;
  projectId: string;
  pluginName: string;
  pipelineName: string;
  displayName: string;
  params: Record<string, unknown>;
  status: PipelineJobStatus;
  progress: number;
  message: string;
  outputRoot: string;
  result: Record<string, unknown> | null;
  error: string | null;
  createdAt: string;
  startedAt?: string;
  finishedAt?: string;
}

interface Project {
  id: string;
  title: string;
  sourceType: 'file' | 'youtube' | 'text' | 'url' | 'manual';
  sourceLabel: string;
  pipelineName: string;
  status: PipelineJobStatus;
  outputRoot: string;
  createdAt: string;
  updatedAt: string;
}
```

처음부터 완벽한 DB 모델을 만들 필요는 없다. 하지만 이 정도 개념은 있어야 Clipper1까지 품을 수 있다.

### 4.4 저장 방식

초기에는 `userData` 아래 JSON snapshot 파일로 시작하는 것이 가장 안전하다.

권장:

```text
~/Library/Application Support/Clipper2/
  queue/
    queue-state.json
  projects/
    {projectId}/
      project.json
      job.json
      outputs...
```

이유:

- native sqlite dependency를 바로 추가하지 않아도 된다.
- Electron packaging 리스크가 낮다.
- 현재 project 수가 많지 않다.
- 사람이 직접 열어보고 디버깅하기 쉽다.

다만 history 검색, 수백/수천 project 관리, 필터링이 중요해지면 SQLite로 옮긴다. 이때도 `ProjectRepository` 인터페이스를 먼저 두면 교체 가능하다.

### 4.5 실행 정책

기본 정책은 "무거운 pipeline job은 전역 1개만 실행"으로 시작하는 것이 맞다.

이유:

- dance와 dialog가 동시에 모델을 올리면 RAM/VRAM 충돌 가능성이 높다.
- 설치형 앱 사용자는 PC 사양이 다양하다.
- 처음부터 병렬 실행을 허용하면 실패 원인 분석이 어려워진다.

나중에 plugin manifest에 resource hint를 넣고 병렬 정책을 확장할 수 있다.

```json
{
  "resource": {
    "profile": "heavy_gpu",
    "max_concurrency": 1,
    "estimated_ram_mb": 6000,
    "estimated_vram_mb": 3000
  }
}
```

초기에는 단순하게 간다.

- heavy pipeline job: 전역 1개
- preflight/check API: 병렬 허용
- model install: pipeline 실행과 동시에 하지 않음

### 4.6 IPC 초안

Angular가 사용할 IPC는 다음 정도면 시작 가능하다.

```ts
queue.enqueue(req): Promise<PipelineJob>
queue.list(): Promise<PipelineJob[]>
queue.get(jobId): Promise<PipelineJob | null>
queue.cancel(jobId): Promise<void>
queue.retry(jobId): Promise<PipelineJob>
queue.reorder(jobId, beforeJobId | null): Promise<void>
queue.onChanged(cb): void
```

여기서 중요한 것은 `queue.enqueue`가 plugin URL을 Angular에 넘기지 않는다는 점이다. queue manager가 내부적으로 plugin job을 시작하고 WebSocket을 구독한다.

---

## 5. 기존 dance/dialog를 어떻게 바꿀지

현재 dance/dialog 화면은 setup form과 job runner가 섞여 있다.

목표 구조:

```text
DanceSetupComponent
  - 입력 수집
  - artist/member/image 선택
  - queue.enqueue(dance_highlight, params)
  - /queue 또는 /projects/{id}로 이동

DialogSetupComponent
  - 입력 수집
  - queue.enqueue(dialog_highlight, params)
  - /queue 또는 /projects/{id}로 이동
```

즉 각 feature page는 "job 실행 화면"이 아니라 "작업 생성 화면"이 된다.

진행률은 별도 Queue/Project 화면에서 보여준다.

- `/queue`: 대기/실행 중 작업 목록
- `/projects/:id`: 프로젝트 상세, 결과, 로그, output open
- `/dashboard`: plugin process 운영 상태
- `/store`: plugin asset 준비

이렇게 나누면 사용자가 화면을 옮겨도 실행 상태가 유지된다.

---

## 6. YouTube 입력은 어디에 넣을지

레거시 HighlightStudio에는 좋은 참고 구조가 있다.

- `/v1/highlight/check`: yt-dlp metadata 확인
- `/v1/highlight/start`: queue에 넣고 worker가 다운로드 후 pipeline 실행

Clipper2에서는 같은 흐름을 그대로 복사하지 말고, 책임을 나눠야 한다.

### 권장 Phase 1

각 plugin이 필요한 YouTube preflight API를 직접 제공한다.

예:

```text
dance_highlight plugin
  POST /preflight/youtube/check

dialog_highlight plugin
  POST /preflight/youtube/check
```

장점:

- yt-dlp Python 의존성을 plugin 내부에 둘 수 있다.
- plugin이 지원하는 source type을 plugin manifest와 맞출 수 있다.
- Electron/NestJS가 특정 source 처리 로직을 알 필요가 적다.

Angular가 직접 plugin URL을 알아서 호출하는 방식으로 가지 말고, 장기적으로는 Electron queue/source IPC가 plugin preflight를 대리 호출하는 편이 좋다.

```text
Angular
  -> source.check(pluginName, { type: 'youtube', url })
  -> Electron
  -> plugin preflight route
```

### 권장 Phase 2

YouTube 처리가 여러 plugin에서 완전히 중복되면 SDK 공통 utility로 뺀다.

- `clipper_plugin_sdk.sources.youtube`
- metadata check
- download helper
- thumbnail save
- duration limit
- progress callback

이렇게 하면 plugin 독립성은 유지하면서 중복만 줄일 수 있다.

---

## 7. Clipper1을 Clipper2에 포함시키는 방식

Clipper1은 단순한 "하이라이트 플러그인 하나"가 아니다.

Clipper1의 본질:

- 사용자가 prompt/news URL/text/image를 입력한다.
- AI가 script와 clip 구조를 만든다.
- 미디어 검색/다운로드를 한다.
- TTS를 만든다.
- 템플릿을 적용한다.
- ffmpeg로 최종 숏폼을 렌더한다.
- 사용자가 중간 clip을 수정할 수 있다.

따라서 Clipper1 통합은 "기능 하나 추가"가 아니라 "새로운 feature family 추가"로 보는 것이 맞다.

### 7.1 하지 말아야 할 방식

아래 방식은 피해야 한다.

- 레거시 `adlight_angular` 화면을 통째로 `clipper_angular`에 복붙
- 레거시 FastAPI 서버를 다시 monolithic하게 붙이기
- Clipper1 로직을 dance/dialog plugin 안에 섞기
- Angular page가 Clipper1의 긴 workflow를 직접 다 관리하기

이렇게 하면 Clipper2를 만든 이유가 사라진다.

### 7.2 권장 구조

Clipper1은 별도 plugin과 별도 Angular feature로 편입한다.

```text
clipper_angular
  src/features/clipper-studio/
    pages/input
    pages/project-editor
    pages/render

clipper_python
  plugins/clipper_studio/
    manifest.json
    clipper_studio/
      app.py
      services/
        script_generation.py
        media_search.py
        tts.py
        render.py
```

이 plugin은 dance/dialog보다 job 종류가 많을 수 있다.

예:

- `draft_project`: prompt/url/text -> script/clips/media candidates
- `refresh_media`: 특정 clip의 media 재검색
- `generate_tts`: clip 대사 -> audio
- `render_video`: 최종 ffmpeg render
- `super_clone`: 변형 영상 여러 개 생성

즉 Clipper1은 하나의 job으로 끝나는 pipeline이 아니라, 여러 단계 job을 가진 project feature다.

### 7.3 LLM API key는 remote server 쪽으로 빼야 한다

Clipper1은 GPT/Gemini 의존도가 높다. API key를 packaged app의 `.env`에 계속 넣으면 보안과 비용 관리가 위험하다.

권장:

```text
clipper_python plugin
  -> local NestJS or Electron config
  -> remote LLM proxy
  -> OpenAI/Gemini
```

초기 개발 중에는 BundledEnvProvider를 유지할 수 있지만, Clipper1을 실제 제품에 포함하려면 LLM proxy가 거의 필수다.

### 7.4 레거시 포팅 순서

권장 순서:

1. 레거시 Clipper1 endpoint와 output 구조 목록화
2. "MVP로 반드시 필요한 workflow"만 선택
3. `clipper_studio` plugin shell 생성
4. 레거시 Python service를 plugin 내부로 최소 이식
5. output manifest를 Clipper2 Project model에 맞게 adapter 작성
6. Angular는 새 `features/clipper-studio`로 작성
7. 이후 legacy 내부 코드를 service 단위로 천천히 정리

처음부터 레거시 전체를 완벽하게 리팩터링하려 하면 오래 걸린다. 우선 Clipper2 구조 안에서 돌아가는 얇은 adapter를 만들고, 그 다음 내부를 치는 편이 낫다.

---

## 8. Store / Dashboard / Queue / Project의 관계

이 네 화면의 역할을 분리해야 한다.

### Store

사용 준비 화면이다.

- plugin asset 설치
- 필요한 모델/용량 설명
- 설치 완료 후 feature 열기

### Dashboard

운영자 화면이다.

- plugin process 상태
- PID/port/error
- start/stop
- 나중에 CPU/RAM/VRAM 표시

### Queue

작업 운영 화면이다.

- 대기 중 작업
- 실행 중 작업
- 진행률
- 취소/재시도/순서 변경

### Project

결과와 편집 화면이다.

- 입력 정보
- 생성된 산출물
- clip 목록
- render 결과
- output folder 열기

Store와 Dashboard는 plugin 중심이고, Queue와 Project는 사용자 작업 중심이다. 제품의 핵심 UX는 결국 Queue/Project 쪽이다.

---

## 9. 추천 구현 Phase

### Phase 0: 현재 상태 정리

- 각 repo branch/push 상태 정리
- `.codex` 설계 문서 업데이트
- 각 repo의 실제 작업트리 상태를 확인하고 임시 로컬 변경은 장기 설계 조건으로 고정하지 않기

### Phase 1: Electron QueueManager 최소 구현

- `PipelineQueueManager` 추가
- in-memory queue + JSON snapshot 저장
- IPC: enqueue/list/cancel/onChanged
- heavy job 전역 1개 실행
- Electron이 Python `/jobs`와 WebSocket을 직접 관리

### Phase 2: dance/dialog를 queue 기반으로 전환

- `DanceFlowStore.startPipeline()`에서 직접 `PluginJobService` 호출 제거
- `DialogFlowStore.startPipeline()`도 동일하게 제거
- 두 feature는 `queue.enqueue()` 후 queue/project 화면으로 이동
- 기존 `PluginJobService`는 Angular에서 제거하거나 dev-only로 축소

### Phase 3: Queue/Project UI 추가

- 왼쪽 사이드바 또는 라우트 추가
- `/queue`: 현재 작업 목록
- `/projects/:id`: 결과 상세
- 완료된 job 다시 열기
- output folder 열기

### Phase 4: YouTube source 지원

- plugin preflight route 추가
- Electron `source.check()` IPC 추가
- queue job params에 `source: { type: 'youtube', url, metadata }` 포함
- plugin 실행 중 yt-dlp download 진행률을 job progress에 포함

### Phase 5: Clipper1 MVP plugin 편입

- `clipper_studio` plugin 생성
- legacy Clipper1 Python workflow 최소 이식
- Angular `features/clipper-studio` 생성
- Project model에 clips/script/media/render 결과 연결

### Phase 6: Remote server / LLM proxy / Registry

- API key를 app bundle에서 제거
- LLM proxy 도입
- plugin package CDN/registry
- update policy
- auth/subscription

---

## 10. 지금 당장 결정해야 할 것

### 결정 1: Queue 저장소

추천: JSON snapshot부터 시작.

이유는 native DB dependency 없이 빠르게 안정화할 수 있기 때문이다. 다만 `ProjectRepository` 인터페이스를 둬서 SQLite로 옮길 수 있게 만든다.

### 결정 2: job 동시 실행 정책

추천: heavy pipeline은 전역 1개만 실행.

이유는 사용자의 PC 자원 보호와 디버깅 단순화다.

### 결정 3: Clipper1 통합 단위

추천: `clipper_studio` 별도 plugin + Angular feature.

기존 dance/dialog와 섞지 않는다.

### 결정 4: YouTube 처리 위치

추천: 초기에는 plugin 내부 preflight/download route. 중복이 쌓이면 SDK common utility로 추출.

### 결정 5: LLM key 전략

추천: 개발 중에는 현재 BundledEnvProvider 허용. Clipper1 제품화 전에는 remote LLM proxy로 전환.

---

## 11. 결론

Clipper2는 이제 "플러그인을 띄울 수 있는 앱" 단계까지 왔다. 다음 단계는 "사용자 작업을 안정적으로 운영하는 앱"으로 넘어가는 것이다.

그 중심은 다음 세 가지다.

1. Electron main의 `PipelineQueueManager`
2. userData 기반 `Project` / `Job` 저장 구조
3. Angular의 Queue/Project 중심 UX

이 구조를 먼저 세우면 dance/dialog, YouTube, Clipper1, future plugin이 같은 운영 모델 위에 올라간다. 반대로 이 구조 없이 Clipper1을 바로 붙이면, Clipper2도 다시 레거시처럼 기능별 임시 연결이 누적될 가능성이 높다.
