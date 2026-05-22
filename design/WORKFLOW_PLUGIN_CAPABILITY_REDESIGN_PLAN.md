# Workflow Plugin / Shared Capability 재설계 계획

작성일: 2026-04-30

상태: 현재 기준 설계안

관련 문서:

- `WORKFLOW_CAPABILITY_RESOURCE_ARCHITECTURE.md`
- `NESTJS_CONTROL_PLANE_REDESIGN.md`
- `CLIPPER2_NEXT_ARCHITECTURE_PLAN.md`
- `../context/PROJECT_HISTORY_AND_STATUS.md`

## 0. 이 문서의 목적

이 문서는 Clipper2의 "플러그인" 개념을 다시 정리한다.

현재 앱에는 `dialog_highlight`, `dance_highlight` 같은 실행 가능한 플러그인이 있고, 대시보드에서는 이 플러그인들의 리소스 사용량과 실행 상태를 보여준다. 이 방향은 맞지만, 앞으로 Clipper1 통합, YouTube URL 입력, 템플릿 렌더링, 이미지-to-비디오, TTS, 미디어 검색 같은 기능이 들어오면 모든 것을 같은 층위의 "플러그인"으로 취급하기 어렵다.

핵심 문제는 다음이다.

- 어떤 기능은 사용자가 직접 실행하는 제품 기능이다.
- 어떤 기능은 여러 제품 기능이 공통으로 사용하는 내부 기능이다.
- 어떤 기능은 무겁게 떠 있는 런타임 프로세스라 리소스 모니터링 대상이다.
- 어떤 기능은 단순한 라이브러리/서비스라 대시보드에 독립 항목으로 보일 필요가 없다.

따라서 Clipper2는 "플러그인"을 하나의 단어로만 보지 않고, 다음 계층으로 나눠야 한다.

```text
Workflow Plugin
  사용자가 직접 선택하고 실행하는 제품 기능

Shared Capability
  여러 workflow가 재사용하는 공통 기능

Provider
  capability의 실제 구현체

Runtime Process / Resource
  로컬 PC에서 실제로 메모리/CPU/GPU를 점유하는 실행 단위
```

이 문서의 목표는 두 가지다.

1. 사용자가 말한 큰 그림을 Clipper2 용어와 구조로 명확히 정리한다.
2. 현재 Angular/NestJS/Electron/Python 구조를 어떤 순서로 바꿔야 하는지 실행 계획을 세운다.

## 1. 이해한 제품 방향

사용자가 말한 방향은 다음으로 이해한다.

Clipper2는 단순한 하이라이트 추출 앱이 아니라, 여러 AI 기반 영상 제작 workflow를 로컬 PC 위에서 운영하는 데스크톱 앱이 되어야 한다.

현재 있는 기능은 다음과 같다.

- `dialog_highlight`: 긴 영상에서 대사 중심 하이라이트 클립을 만든다.
- `dance_highlight`: 긴 영상에서 인물/안무 중심 하이라이트 클립을 만든다.

앞으로 들어올 수 있는 기능은 다음과 같다.

- Clipper1 계열: 텍스트, URL, 키워드, 복붙 입력 등을 받아 숏폼 영상을 자동 생성한다.
- 이미지-to-비디오: 이미지를 입력하면 영상을 생성한다.
- 기존 영상 리믹스/업그레이드: 기존 영상을 다른 스타일, 다른 템플릿, 다른 대본으로 재구성한다.

이 기능들은 사용자가 직접 실행하는 제품 기능이므로 `Workflow Plugin`으로 볼 수 있다.

하지만 Clipper1에 있던 템플릿 적용 기능은 `clipper_studio`에만 종속되면 안 된다. 대사 하이라이트에서 뽑힌 클립에도 템플릿을 입힐 수 있어야 하고, 이미지-to-비디오 결과물에도 같은 템플릿 시스템을 쓸 수 있어야 한다.

마찬가지로 다음 기능들도 특정 workflow에 갇히면 안 된다.

- YouTube URL 입력/다운로드/metadata 추출
- 미디어 검색/다운로드/cache
- TTS 합성
- 자막 segment 구성
- 템플릿 적용
- ffmpeg 렌더링
- 프로젝트 manifest 생성

이들은 사용자에게 독립 제품 기능처럼 보일 수도 있지만, 본질적으로는 여러 workflow가 재사용하는 `Shared Capability`다.

따라서 Clipper1을 "거대한 플러그인 하나"로 넣는 것은 맞지 않다. Clipper1은 `clipper_studio`라는 workflow feature로 들어오되, 내부 단계는 공통 capability를 조합해야 한다.

## 2. 핵심 결론

Clipper2의 장기 구조는 다음 원칙을 따른다.

- `Workflow Plugin`은 제품 기능 단위다.
- `Shared Capability`는 workflow들이 함께 쓰는 공통 기능 단위다.
- `Provider`는 capability의 실제 구현체다.
- `Runtime Process`는 리소스 모니터링과 lifecycle 제어의 대상이다.
- NestJS는 workflow, job, project, source, capability, provider routing의 control plane이다.
- Electron은 OS/native/process/telemetry host adapter다.
- Python/FastAPI는 model-heavy 또는 video-heavy compute worker다.
- Angular는 화면과 사용자 interaction만 담당하고 orchestration을 소유하지 않는다.

가장 중요한 결정:

> 사용자가 실행하는 기능과, 여러 기능이 공유하는 기능을 같은 "플러그인 목록"에 평평하게 놓지 않는다.

예를 들어 `dialog_highlight`, `dance_highlight`, `clipper_studio`, `image_to_video`는 사용자가 실행하는 workflow다.

반면 `source.ingest`, `template.apply`, `video.render`, `tts.synthesis`, `media.search`는 workflow들이 요청해서 쓰는 capability다.

그리고 `local ffmpeg`, `yt-dlp`, `OpenAI`, `Gemini`, `local TTS`, `remote render farm` 같은 것은 capability 뒤의 provider다.

추가 원칙:

> Provider는 언제든 갈아끼울 수 있는 구현체여야 한다.

예를 들어 script generation은 OpenAI API일 수도 있고, 회사 remote proxy일 수도 있고, Ollama로 서빙하는 Gemma 계열 local LLM일 수도 있다.
TTS는 Naver Clova일 수도 있고, Oute TTS local server일 수도 있고, 다른 open-source TTS runtime일 수도 있다.
이미지 입력은 Naver/Kakao search일 수도 있고, local image generation server일 수도 있고, user upload일 수도 있다.

이 차이는 provider adapter 내부에서만 다룬다.
Workflow, Angular editor, ProjectManifest presenter, RenderRecipe builder는 vendor/local runtime의 API shape을 직접 알면 안 된다.
새 provider를 붙일 때 core workflow를 고치고 있다면 abstraction이 부족한 것이다.

## 3. 용어 정의

### 3.1 Workflow Plugin

Workflow Plugin은 사용자가 직접 고르는 제품 기능이다.

예:

- `dialog_highlight`
- `dance_highlight`
- `clipper_studio`
- `image_to_video`
- `shortform_remix`
- `shortform_upgrade`

책임:

- 사용자 입력 schema 정의
- 어떤 source type을 받을 수 있는지 선언
- 어떤 capability가 필요한지 선언
- workflow pipeline graph 정의
- job/project/result 모델 정의
- 결과 화면에 필요한 summary/detail manifest 생성
- resource requirement 선언

가지면 안 되는 책임:

- 공통 YouTube 다운로드 구현을 직접 소유
- 공통 템플릿 엔진을 직접 소유
- 공통 TTS 구현을 직접 소유
- 공통 ffmpeg 렌더링을 workflow 안에 하드코딩
- Clipper1 전용 방식으로만 재사용 불가능한 output 구조 생성

### 3.2 Shared Capability

Shared Capability는 여러 workflow가 쓰는 공통 기능이다.

예:

- `source.ingest`: 로컬 파일, YouTube URL, 이미지, 텍스트 입력을 표준 source asset으로 변환
- `source.inspect`: duration, codec, resolution, title, thumbnail 같은 metadata 확인
- `video.analyze`: STT, scene, shot, face, pose, motion 분석
- `llm.script`: 대본, hook, keyword, summary, clip reason 생성
- `media.search`: 이미지/영상/GIF 검색
- `media.download`: 외부 미디어 다운로드/cache
- `tts.synthesis`: 음성 합성
- `subtitle.compose`: 자막 segment/style 구성
- `template.catalog`: 템플릿 목록, preview, preset 관리
- `template.apply`: 템플릿을 render recipe에 적용
- `video.render`: ffmpeg 또는 다른 렌더러로 최종 영상 생성
- `asset.store`: 프로젝트 산출물 저장
- `project.manifest`: 결과 manifest 표준화

Capability는 꼭 별도 프로세스일 필요가 없다. 어떤 capability는 NestJS service 하나로 충분하고, 어떤 capability는 Electron host 기능이 필요하고, 어떤 capability는 Python worker나 외부 API가 필요하다.

### 3.3 Provider

Provider는 capability의 실제 구현체다.

예:

```text
source.ingest
  provider: local_file
  provider: yt_dlp

llm.script
  provider: openai
  provider: gemini
  provider: remote_adlight_llm

tts.synthesis
  provider: elevenlabs
  provider: naver_clova
  provider: local_tts

video.render
  provider: local_ffmpeg
  provider: remote_render_farm
```

Workflow는 특정 provider에 직접 붙지 않는다. Workflow는 capability를 요청하고, NestJS control plane이 현재 환경, 권한, 설정, 리소스 상태에 맞는 provider를 고른다.

### 3.4 Runtime Process / Resource

Runtime Process는 실제로 로컬 PC 리소스를 점유하는 실행 단위다.

예:

- Electron main process
- NestJS local API process
- `dialog_highlight` Python worker process
- `dance_highlight` Python worker process
- 향후 `clipper_studio` Python worker process
- 향후 local model server

모든 capability가 대시보드에 독립 runtime으로 보여야 하는 것은 아니다. 대시보드의 리소스 모니터링 대상은 "실제로 떠 있고, 메모리/CPU/GPU를 점유하고, 시작/중지할 수 있는 것"이다.

## 4. 목표 아키텍처

목표 구조:

```text
Angular
  -> NestJS App API
      -> Workflow Registry
      -> Capability Registry
      -> Provider Registry
      -> Source Service
      -> Job / Queue Service
      -> Project Service
      -> Resource Policy Service
      -> Artifact Storage
      -> Electron Host Bridge
      -> Python Compute Workers
      -> Remote Providers

Electron Host Adapter
  -> native file dialog
  -> process spawn/kill
  -> packaged paths
  -> telemetry
  -> local asset/open file operations

Python Compute Workers
  -> model-heavy pipeline
  -> video-heavy pipeline
  -> plugin SDK job runtime

Remote Services
  -> auth/license
  -> LLM proxy
  -> hosted provider APIs
  -> plugin/capability catalog distribution
```

Angular의 기본 API 대상은 NestJS 하나다. Angular가 Python plugin URL, provider API key, yt-dlp, ffmpeg, model process lifecycle을 직접 알면 안 된다.

NestJS는 다음을 소유한다.

- 어떤 workflow가 있는지
- 어떤 workflow가 어떤 source/capability를 요구하는지
- 어떤 job을 어떤 순서로 실행할지
- 어떤 provider를 쓸지
- output/project manifest를 어떻게 저장하고 읽을지
- resource policy상 지금 실행해도 되는지

Electron은 다음을 소유한다.

- 앱 shell
- native 기능
- packaged runtime bootstrap
- local process lifecycle
- host telemetry
- 로컬 파일 경로와 OS integration

Python은 다음을 소유한다.

- AI/model-heavy 처리
- ffmpeg/video-heavy 처리 중 Python 생태계가 자연스러운 부분
- plugin SDK 기반 job progress/cancel/result

## 5. 현재 구조와의 차이

현재 구조는 이미 NestJS control plane 방향으로 많이 이동했다.

현재 존재하는 큰 축:

- Angular는 `JobApi`/NestJS API로 job enqueue를 요청한다.
- NestJS는 queue, job, project history를 소유한다.
- NestJS는 Python plugin job을 호출하고 progress를 받아 Angular에 전달한다.
- Electron은 packaged bridge와 plugin process host 역할을 한다.
- Dashboard는 resource/process 상태를 NestJS `/v1/resources`를 통해 본다.

남은 구조적 빈틈:

- 입력 source 모델이 아직 로컬 파일 중심이다.
- YouTube URL, 이미지, 텍스트 같은 입력을 표준 `SourceInput`으로 다루는 계층이 없다.
- 템플릿/렌더링이 아직 workflow별 산출물 형태에 묶여 있다.
- Clipper1의 템플릿, TTS, media search, script generation을 공통 capability로 받을 준비가 부족하다.
- Dashboard/Store에서 사용자 실행 workflow와 내부 provider/runtime 개념이 아직 명확히 분리되어 있지 않다.
- output manifest가 dialog/dance별로 점진적으로 정리되고 있지만, 모든 workflow가 공유할 표준 manifest까지는 아니다.

## 6. 계층별 모델

### 6.1 Workflow Registry

NestJS에 workflow registry가 필요하다.

초기에는 기존 plugin manifest를 확장해도 된다. 단, 개념상 `workflow`와 `runtime plugin`을 분리해야 한다.

예:

```json
{
  "id": "dialog_highlight",
  "kind": "workflow",
  "displayName": "대사 하이라이트",
  "supportedSources": ["local_video", "youtube_video"],
  "requiresCapabilities": [
    "source.ingest",
    "video.analyze.dialog",
    "video.render",
    "project.manifest"
  ],
  "defaultRenderTemplate": "shorts.basic_letterbox",
  "runtimeRequirements": {
    "workers": ["dialog_highlight_worker"],
    "maxConcurrentJobs": 1
  }
}
```

Workflow registry가 답해야 하는 질문:

- 이 workflow는 어떤 입력을 받는가?
- 실행 전에 어떤 capability가 준비되어야 하는가?
- 어떤 runtime worker가 필요한가?
- 어떤 resource profile이 필요한가?
- 결과 project detail은 어떤 presenter를 쓰는가?

### 6.2 Capability Registry

Capability registry는 "공통 기능"의 목록과 provider routing 정보를 갖는다.

예:

```json
{
  "id": "source.ingest",
  "displayName": "소스 가져오기",
  "inputTypes": ["local_file", "youtube_url"],
  "providers": ["local_file", "yt_dlp"],
  "resourceProfile": "light",
  "visibleInDashboard": false
}
```

```json
{
  "id": "video.render",
  "displayName": "영상 렌더링",
  "providers": ["local_ffmpeg"],
  "resourceProfile": "medium_cpu",
  "visibleInDashboard": false
}
```

```json
{
  "id": "video.analyze.dialog",
  "displayName": "대사 분석",
  "providers": ["dialog_highlight_worker"],
  "resourceProfile": "heavy_model",
  "visibleInDashboard": true
}
```

대시보드 노출 여부는 capability 자체가 아니라 provider/runtime 특성에 따라 정해야 한다.

### 6.3 Provider Registry

Provider registry는 provider의 실행 위치와 설정을 정의한다.

예:

```json
{
  "id": "yt_dlp",
  "capability": "source.ingest",
  "runtime": "host_tool",
  "requiresNetwork": true,
  "requiresUserCredential": false,
  "output": "local_asset"
}
```

```json
{
  "id": "dialog_highlight_worker",
  "capabilities": ["video.analyze.dialog"],
  "runtime": "python_worker",
  "pluginName": "dialog_highlight",
  "resourceProfile": {
    "estimatedRamMb": 4096,
    "estimatedVramMb": 0,
    "safeToEvictWhenIdle": true
  }
}
```

```json
{
  "id": "local_ffmpeg",
  "capabilities": ["video.render"],
  "runtime": "host_binary",
  "binary": "ffmpeg",
  "resourceProfile": {
    "estimatedRamMb": 512,
    "estimatedVramMb": 0
  }
}
```

Provider registry가 답해야 하는 질문:

- 이 capability를 실제로 누가 수행하는가?
- 로컬 프로세스가 필요한가?
- 외부 API key가 필요한가?
- 네트워크가 필요한가?
- 리소스 대시보드에 보여야 하는가?
- 유휴 상태에서 정리해도 되는가?

## 7. 표준 데이터 계약

### 7.1 SourceInput

사용자 입력은 workflow별 `video_path` 같은 단일 필드로 굳히지 말고, 표준 source 입력으로 받는다.

```ts
type SourceInput =
  | {
      type: 'local_file';
      path: string;
      mediaType: 'video' | 'image' | 'audio' | 'unknown';
    }
  | {
      type: 'youtube_url';
      url: string;
      requestedQuality?: 'best' | '1080p' | '720p' | 'audio_only';
    }
  | {
      type: 'text_prompt';
      text: string;
      language?: string;
    }
  | {
      type: 'image_file';
      path: string;
    };
```

### 7.2 SourceAsset

`source.ingest` capability는 입력을 로컬에서 처리 가능한 표준 asset으로 변환한다.

```ts
interface SourceAsset {
  id: string;
  type: 'video' | 'image' | 'audio' | 'text';
  originalInput: SourceInput;
  label: string;
  localPath?: string;
  thumbnailPath?: string;
  durationSec?: number;
  width?: number;
  height?: number;
  codec?: string;
  metadata: Record<string, unknown>;
  provenance: {
    provider: string;
    fetchedAt: string;
    originalUrl?: string;
  };
}
```

중요한 점:

- YouTube URL로 들어와도 workflow worker에는 가능하면 local video path를 넘긴다.
- workflow는 다운로드 방식이나 원본 URL parsing을 몰라도 된다.
- project에는 원본 출처와 로컬 asset 경로가 모두 남아야 한다.

### 7.3 Capability Request / Result

Capability 호출은 최소한 다음 공통 wrapper를 가진다.

```ts
interface CapabilityRequest<TInput = unknown> {
  capabilityId: string;
  providerId?: string;
  projectId: string;
  jobId: string;
  input: TInput;
  policy?: {
    allowNetwork?: boolean;
    allowRemoteProvider?: boolean;
    maxCostUsd?: number;
  };
}

interface CapabilityResult<TOutput = unknown> {
  capabilityId: string;
  providerId: string;
  status: 'completed' | 'failed' | 'cancelled';
  output?: TOutput;
  error?: {
    code: string;
    message: string;
  };
  artifacts?: ProjectArtifact[];
}
```

처음부터 모든 capability를 이 generic API로 구현할 필요는 없다. 하지만 DTO 사고방식은 이 구조를 따라야 한다.

### 7.4 RenderRecipe

템플릿과 렌더링을 workflow에서 분리하려면 최종 영상 생성 입력을 표준화해야 한다.

```ts
interface RenderRecipe {
  id: string;
  sourceClips: Array<{
    assetId: string;
    sourcePath: string;
    startSec?: number;
    endSec?: number;
    crop?: {
      x: number;
      y: number;
      width: number;
      height: number;
    };
  }>;
  tracks: {
    voice?: AudioTrack[];
    bgm?: AudioTrack[];
    subtitles?: SubtitleTrack[];
    overlays?: OverlayTrack[];
  };
  template: {
    templateId: string;
    params: Record<string, unknown>;
  };
  output: {
    aspectRatio: '9:16' | '16:9' | '1:1' | string;
    width: number;
    height: number;
    fps?: number;
    format: 'mp4' | 'mov';
  };
}
```

`dialog_highlight`와 `dance_highlight`는 나중에 이 recipe를 만들어 `template.apply`/`video.render`에 넘기는 방식으로 바뀌어야 한다.

### 7.5 Project Manifest

모든 workflow 결과는 공통 project manifest로 수렴해야 한다.

```ts
interface ProjectManifest {
  id: string;
  workflowId: string;
  title: string;
  status: 'completed' | 'failed' | 'cancelled';
  sourceAssets: SourceAsset[];
  outputs: ProjectOutput[];
  artifacts: ProjectArtifact[];
  summary: Record<string, unknown>;
  detail: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}
```

각 workflow의 고유 detail은 유지하되, project list/detail이 공통으로 이해할 수 있는 최소 필드는 반드시 맞춰야 한다.

## 8. YouTube URL 입력 설계

현재 사용자는 로컬 파일만 선택할 수 있다. 앞으로는 YouTube URL도 입력할 수 있어야 한다.

하지만 이 기능을 `dialog_highlight` Angular 화면 안에 직접 붙이면 안 된다. 그렇게 하면 `dance_highlight`, `clipper_studio`, 향후 다른 workflow에서도 같은 코드를 반복하게 된다.

권장 흐름:

```text
Angular workflow form
  -> SourceInput 생성
  -> NestJS POST /v1/sources/inspect
  -> NestJS POST /v1/jobs
      params.source = SourceInput

NestJS JobQueue
  -> source.ingest 실행
      local_file: metadata만 확인
      youtube_url: 다운로드/cache/thumbnail/metadata 생성
  -> SourceAsset 생성
  -> workflow worker에는 localPath 중심으로 전달
```

초기 API 예:

```text
POST /v1/sources/inspect
POST /v1/sources/ingest
GET  /v1/sources/:id
```

초기 구현 타협안:

- `source.ingest`는 먼저 NestJS service로 둔다.
- YouTube 다운로드 provider는 `yt-dlp`를 호출하는 host tool로 둘 수 있다.
- packaged app에서 binary/venv/path 문제가 있으면 Electron host bridge를 통해 실행한다.
- Python plugin에 이미 있는 helper를 써야 하면 NestJS가 worker capability endpoint를 호출하되, Angular는 모르게 한다.

중요 정책:

- workflow job이 실행 큐에 들어간 뒤 source ingest도 job 단계로 기록되어야 한다.
- 다운로드 산출물은 project output root 아래 또는 source cache 아래에 남겨야 한다.
- 원본 URL, 다운로드 시각, provider, local path를 manifest에 남겨야 한다.
- 같은 URL 재사용 시 cache hit 정책을 둘 수 있어야 한다.

## 9. 템플릿 / 렌더링 공통화 설계

Clipper1의 템플릿 기능은 `clipper_studio` 전용이 되면 안 된다.

목표:

- 대사 하이라이트 클립에도 템플릿을 적용할 수 있어야 한다.
- 안무 하이라이트 클립에도 템플릿을 적용할 수 있어야 한다.
- 이미지-to-비디오 결과물에도 템플릿을 적용할 수 있어야 한다.
- Clipper1의 여러 템플릿은 공통 템플릿 catalog로 들어와야 한다.

권장 계층:

```text
template.catalog
  템플릿 목록, preview, aspect ratio, slot schema 제공

template.apply
  workflow output + template preset + user params를 RenderRecipe로 변환

video.render
  RenderRecipe를 실제 mp4/mov 산출물로 렌더링
```

TemplatePreset 예:

```ts
interface TemplatePreset {
  id: string;
  name: string;
  category: 'shorts' | 'news' | 'education' | 'commerce' | string;
  aspectRatio: '9:16' | '16:9' | '1:1' | string;
  previewImagePath?: string;
  previewVideoPath?: string;
  slots: Array<{
    id: string;
    type: 'video' | 'image' | 'text' | 'subtitle' | 'audio';
    required: boolean;
  }>;
  defaultParams: Record<string, unknown>;
}
```

현재 대사/안무 하이라이트가 만드는 검은 패딩 기반 쇼츠 결과물은 `shorts.basic_letterbox` 같은 기본 템플릿으로 모델링하는 것이 좋다. 즉 검은 패딩은 workflow 고정 결과가 아니라 기본 렌더 템플릿 중 하나가 되어야 한다.

전환 원칙:

- 처음부터 모든 렌더링을 갈아엎지 않는다.
- 먼저 기존 output을 그대로 유지하되 manifest에 `renderTemplateId`를 기록한다.
- 다음 단계에서 현재 hardcoded render 옵션을 `RenderRecipe`로 추출한다.
- Clipper1 템플릿은 별도 workflow 전용 폴더가 아니라 공통 `templates/` catalog로 이관한다.

## 10. Clipper1 편입 설계

Clipper1은 단일 하이라이트 플러그인이 아니다.

Clipper1의 본질:

- 사용자가 입력을 준다.
- LLM이 대본/키워드/구성안을 만든다.
- 외부 미디어를 검색하거나 다운로드한다.
- TTS를 만든다.
- 자막을 구성한다.
- 템플릿을 적용한다.
- ffmpeg로 최종 숏폼을 렌더링한다.
- variation을 만들 수 있다.

따라서 Clipper1은 다음처럼 편입한다.

```text
clipper_studio Workflow Plugin
  -> source.ingest
  -> llm.script
  -> media.search
  -> media.download
  -> tts.synthesis
  -> subtitle.compose
  -> template.catalog
  -> template.apply
  -> video.render
  -> project.manifest
```

`clipper_studio`가 가져야 하는 책임:

- 사용자 workflow 화면
- 입력 방식 선택
- 생성 단계/variation 상태 표시
- 어떤 capability를 어떤 순서로 호출할지 정의
- Clipper1 프로젝트 detail presenter

`clipper_studio`가 가지면 안 되는 책임:

- 템플릿 엔진 독점
- TTS provider 독점
- 미디어 검색 provider 독점
- ffmpeg renderer 독점
- 다른 workflow가 쓸 수 없는 legacy output 구조 강제

초기 이식 방식:

1. Legacy Clipper1 기능을 완전히 재작성하지 않고 adapter로 감싼다.
2. Adapter의 output은 Clipper2 `ProjectManifest`와 `ProjectArtifact`로 변환한다.
3. Legacy 내부 단계 중 템플릿/TTS/media/render는 capability 후보로 목록화한다.
4. 가장 먼저 재사용 가치가 큰 `template.catalog`, `template.apply`, `video.render`를 공통화한다.
5. 이후 `tts.synthesis`, `media.search`, `llm.script`를 provider registry 뒤로 이동한다.

2026-05-04 status correction:

- `clipper1_video_render`는 위 구조의 `video.render` provider/runtime이다.
- 이것은 `clipper_studio Workflow Plugin`이 아니다.
- Store/Dashboard에 `clipper1_video_render`를 사용자-facing card로 보여주는 것은 이 문서의 분류 기준에 어긋난다.
- Clipper1 편입 완료 기준은 사용자가 `Clipper Studio` 화면에서 project를 만들고, draft/edit/render/output을 하나의 workflow로 다룰 수 있는 상태다.
- 별도 상세 설계는 `.codex/design/CLIPPER_STUDIO_WORKFLOW_REDESIGN.md`를 기준으로 한다.

## 11. Store / Dashboard UX 모델

현재 Store/Dashboard는 플러그인을 중심으로 설계되어 있다. 앞으로는 다음 두 관점을 분리해야 한다.

### 11.1 사용자가 실행하는 기능

Store나 홈 화면에서 사용자가 보는 것은 workflow 중심이어야 한다.

예:

- 대사 하이라이트
- 안무 하이라이트
- 클리퍼 스튜디오
- 이미지로 영상 만들기

사용자는 "ffmpeg provider"나 "yt-dlp capability"를 실행하고 싶어 하는 것이 아니다. 사용자는 제품 기능을 실행하고 싶어 한다.

### 11.2 운영/리소스 대상

Dashboard에서는 실제로 리소스를 쓰는 runtime/provider 중심으로 보여줘야 한다.

예:

- 대사 분석 worker
- 안무 분석 worker
- Clipper Studio worker
- NestJS
- Electron
- 향후 local model server

`source.ingest`나 `template.catalog` 같은 capability는 일반적으로 대시보드의 독립 카드가 될 필요가 없다. 다만 provider가 무겁거나 문제가 잦으면 운영 상세에서 보일 수 있다.

권장 UI 구분:

```text
Store / 기능 목록
  - Workflow 중심
  - 사용 가능 여부
  - 필요한 모델/asset 준비 상태

Dashboard / 운영 콘솔
  - Runtime process 중심
  - CPU/RAM/GPU/VRAM
  - active job count
  - start/stop/idle cleanup
  - capability/provider 상세는 접힌 부가 정보
```

이렇게 해야 "공통 유틸을 플러그인이라는 같은 층위에 둬야 하나?"라는 혼란이 줄어든다.

## 12. 현재 구조에서의 변경 계획

### Phase 0. 문서와 inventory 정리

목표:

- workflow/capability/provider/runtime 용어를 팀 기준으로 고정한다.
- Clipper1 legacy 기능을 capability 후보별로 나눠 목록화한다.
- 현재 dialog/dance output manifest와 Clipper1 output 구조 차이를 정리한다.

작업:

- 이 문서를 기준 설계로 추가한다.
- `.codex/design/WORKFLOW_CAPABILITY_RESOURCE_ARCHITECTURE.md`와 연결한다.
- Clipper1 legacy endpoint, service, template, media/TTS/render 파일을 목록화한다.
- 현재 `dialog_highlight`, `dance_highlight`가 실제로 어떤 산출물을 만드는지 manifest 기준으로 문서화한다.

산출물:

- workflow 목록
- capability 후보 목록
- provider 후보 목록
- legacy Clipper1 분해표
- output manifest gap list

### Phase 1. 공통 계약 추가

목표:

- NestJS와 Angular가 공유할 수 있는 source/job/project/capability DTO를 만든다.
- 기존 job API를 깨지 않고, 새 source 모델을 받을 수 있는 길을 연다.

작업:

- `SourceInput` DTO 추가
- `SourceAsset` DTO 추가
- `ProjectArtifact`/`ProjectOutput` 확장
- `WorkflowDescriptor` 모델 추가
- `CapabilityDescriptor` 모델 추가
- `ProviderDescriptor` 모델 추가
- 기존 plugin manifest의 `capabilities/resources` 필드를 이 모델에 맞춰 정리

주의:

- 이 단계에서 모든 workflow를 새 모델로 강제 이전하지 않는다.
- 기존 `video_path` 방식은 compatibility adapter로 유지한다.

완료 기준:

- Angular가 로컬 파일 입력도 `SourceInput`으로 표현할 수 있다.
- NestJS job params가 `source` 필드를 받을 수 있다.
- 기존 dialog/dance job이 깨지지 않는다.

### Phase 2. Source Ingest 도입

목표:

- 로컬 파일과 YouTube URL을 같은 source ingest 흐름으로 처리한다.

작업:

- NestJS `SourceModule` 또는 equivalent service 추가
- `POST /v1/sources/inspect` 추가
- `POST /v1/sources/ingest` 추가
- local file provider 구현
- YouTube provider 설계 및 1차 구현
- ingest 결과를 project/job snapshot에 저장
- workflow enqueue 시 `source.ingest`를 선행 단계로 실행

YouTube provider 위치:

- 1차: NestJS에서 provider interface를 두고, 실제 실행은 Electron host bridge 또는 Python helper를 사용할 수 있다.
- 장기: provider registry 뒤로 숨겨서 workflow가 실행 위치를 몰라도 되게 한다.

완료 기준:

- dialog/dance가 로컬 파일과 YouTube URL을 같은 job API로 받을 수 있다.
- YouTube 다운로드 결과가 local video asset으로 workflow에 전달된다.
- project detail에서 원본 출처와 local asset metadata를 확인할 수 있다.

### Phase 3. Project Manifest 표준화

목표:

- 모든 workflow 결과를 공통 project manifest로 읽을 수 있게 한다.
- workflow별 detail은 유지하되 list/detail 공통 필드는 통일한다.

작업:

- `ProjectManifest` 최소 schema 확정
- `ProjectDetailBuilder`가 workflow별 output을 공통 manifest로 변환
- dialog detail의 clip/title/segment/dialog/reason/thumbnail을 표준 clip artifact로 정리
- dance detail의 person/clip/person image를 표준 entity/clip artifact로 정리
- retry/cancel/error/history filter가 workflow별 output 형태에 덜 의존하도록 정리

완료 기준:

- `/v1/projects/:id`가 공통 필드와 workflow-specific detail을 함께 반환한다.
- Angular project history는 workflow 공통 필드로 목록을 그린다.
- workflow-specific UI는 detail presenter만 담당한다.

### Phase 4. Template Catalog / RenderRecipe 도입

목표:

- 현재 hardcoded shorts render를 공통 템플릿 시스템으로 옮길 준비를 한다.

작업:

- `TemplatePreset` schema 추가
- 기본 템플릿 catalog 추가
- 현재 dialog/dance 쇼츠 렌더 결과를 `shorts.basic_letterbox`로 명명
- output manifest에 `templateId`/`renderRecipeId` 기록
- `RenderRecipe` 초안 추가
- 기존 Python render output을 recipe로 역표현할 수 있는지 확인

완료 기준:

- 기존 결과물은 그대로 나오지만, manifest상 어떤 템플릿/렌더 설정으로 만들어졌는지 알 수 있다.
- Clipper1 템플릿을 공통 catalog로 옮길 기준이 생긴다.

### Phase 5. Template Apply / Video Render Capability 분리

목표:

- 템플릿 적용과 최종 렌더링을 workflow 공통 capability로 뺀다.

작업:

- `template.catalog` service 구현
- `template.apply` provider interface 추가
- `video.render` provider interface 추가
- local ffmpeg provider를 capability 뒤로 이동
- dialog/dance가 직접 최종 렌더 옵션을 결정하지 않고 recipe를 넘기는 구조로 단계적 전환
- 렌더 실패/취소/progress를 job event stream에 통합

완료 기준:

- 하나의 템플릿 preset을 dialog/dance 결과에 모두 적용할 수 있다.
- workflow는 "무엇을 보여줄지"를 정하고, 템플릿/render capability는 "어떻게 최종 영상으로 만들지"를 담당한다.

### Phase 6. Clipper1을 `clipper_studio` workflow로 편입

목표:

- Clipper1을 단일 거대 플러그인이 아니라 capability 조합 workflow로 편입한다.
- `video.render` provider 준비와 사용자-facing Clipper Studio workflow 완료를 혼동하지 않는다.

작업:

- `clipper_studio` workflow descriptor 추가
- 실제 Angular route/screen 추가. Store의 `열기`가 빈 동작이면 안 된다.
- legacy Clipper1 adapter 추가
- Clipper1 project state를 Clipper2 project/job model로 매핑
- legacy template 목록을 `template.catalog`로 이관
- legacy render 결과를 `video.render` output artifact로 매핑
- TTS/media/LLM 단계는 처음에는 legacy adapter 내부에 두되 capability boundary를 코드상 표시

완료 기준:

- 사용자는 Clipper2 안에서 Clipper Studio workflow를 실행할 수 있다.
- Clipper1 결과도 작업 보관함/project history에서 동일한 방식으로 보인다.
- 템플릿은 `clipper_studio` 전용이 아니라 dialog/dance에도 적용 가능한 catalog가 된다.

### Phase 7. Capability/Provider Resource Dashboard 정리

목표:

- Dashboard가 workflow와 runtime provider를 혼동하지 않게 한다.

작업:

- Workflow readiness와 Runtime process status를 분리해서 표시
- resource dashboard 카드의 기준을 provider/runtime으로 정리
- capability 목록은 세부 정보 또는 dependency tree로 노출
- active job count는 workflow/provider 양쪽에서 해석 가능하게 표시
- idle cleanup 가능 여부는 provider runtime 기준으로 계산

완료 기준:

- 사용자는 "어떤 기능을 실행할 수 있는지"와 "어떤 런타임이 리소스를 쓰는지"를 구분해서 볼 수 있다.
- 공통 capability가 불필요하게 user-facing plugin처럼 보이지 않는다.

### Phase 8. Remote Provider / 권한 / 비용 정책 확장

목표:

- LLM, TTS, media search, remote render 같은 외부 provider를 안전하게 붙인다.

작업:

- ProviderCredential boundary 추가
- remote LLM proxy 연동 설계
- capability request에 cost/network/remote policy 추가
- 사용자 license/permission에 따라 provider 사용 가능 여부 결정
- remote provider failure/retry/rate limit 정책 추가

완료 기준:

- API key가 packaged app에 고정으로 박히지 않는다.
- workflow는 provider 위치가 local인지 remote인지 몰라도 된다.
- 사용자의 권한/요금제/네트워크 상태에 따라 provider 선택이 가능하다.

## 13. 구현 우선순위

가장 먼저 해야 할 것은 YouTube URL 입력을 위한 `SourceInput`/`SourceAsset` 계층이다.

이유:

- 사용자가 당장 체감할 기능이다.
- dialog/dance 모두에 영향을 준다.
- Clipper1에서도 source ingest가 필요하다.
- source ingest를 잘 잡으면 이후 image/text/url 입력도 같은 모델로 확장된다.

권장 순서:

1. `SourceInput` DTO와 compatibility adapter 추가
2. local file을 `SourceInput`으로 감싸서 기존 workflow가 그대로 실행되게 만들기
3. `source.inspect`/`source.ingest` NestJS service 추가
4. YouTube provider 1차 구현
5. job snapshot/project manifest에 `sourceAssets` 저장
6. dialog/dance enqueue UI에 local file / YouTube URL 선택 추가
7. output detail에서 source provenance 표시
8. 템플릿 catalog 설계로 이동

이 순서가 좋은 이유:

- UI 요구와 장기 아키텍처가 동시에 맞는다.
- 기존 Python pipeline을 한 번에 갈아엎지 않아도 된다.
- workflow worker에는 여전히 local path를 넘길 수 있어 리스크가 낮다.

## 14. 피해야 할 방향

다음 방향은 피해야 한다.

- YouTube URL 입력을 `dialog_highlight` 컴포넌트 안에만 직접 구현한다.
- `dance_highlight`에도 같은 YouTube 다운로드 코드를 복사한다.
- Clipper1을 legacy 폴더째로 하나의 거대한 Python plugin으로 붙인다.
- Clipper1 템플릿을 `clipper_studio` 내부 private 기능으로 둔다.
- Angular가 multi-step workflow orchestration을 직접 관리한다.
- 모든 utility를 Store/Dashboard의 독립 플러그인 카드로 만든다.
- provider API key를 workflow plugin 코드에 직접 넣는다.
- output manifest 없이 파일 구조만 보고 결과를 추론한다.

## 15. 결정이 필요한 지점

아직 결정해야 하는 사항:

- YouTube provider를 처음에 NestJS child process로 둘지, Electron host bridge로 둘지, Python helper로 둘지
- source cache 위치를 project별 output 아래에 둘지, 전역 cache 아래에 둘지
- Clipper1 legacy adapter를 어느 repo에 둘지
- template catalog asset을 앱 번들에 포함할지, 사용자 데이터로 내려받을지
- `video.render`를 Python capability로 둘지, NestJS/Electron host ffmpeg wrapper로 둘지
- capability registry를 정적 JSON으로 시작할지, NestJS provider 코드로 시작할지
- Store에서 workflow와 dependency asset을 어떻게 묶어 보여줄지

권장 초기 결정:

- YouTube provider는 NestJS interface 뒤에 숨기고, packaged 실행은 Electron host bridge 또는 bundled tool을 통해 처리한다.
- source cache는 전역 cache + project manifest reference로 시작한다. 단, 최종 project export 시 필요한 asset은 project output에도 복사할 수 있게 한다.
- template catalog는 처음에는 앱 번들 static asset으로 시작하고, 나중에 remote catalog로 확장한다.
- `video.render`는 당장은 Python/ffmpeg 기존 경로를 유지하되, API 계약은 `RenderRecipe`로 옮긴다.
- capability registry는 정적 descriptor + NestJS service 조합으로 시작한다.

## 16. 한 줄 기준

앞으로 기능을 추가할 때 다음 질문을 먼저 한다.

```text
이것은 사용자가 직접 실행하는 workflow인가,
여러 workflow가 공유하는 capability인가,
아니면 capability 뒤의 provider/runtime인가?
```

이 질문에 답한 뒤에야 Store, Dashboard, NestJS module, Electron host, Python worker 중 어디에 둘지 결정한다.
