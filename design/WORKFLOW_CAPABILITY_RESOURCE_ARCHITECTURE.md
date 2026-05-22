# Workflow, Capability, Resource Architecture

작성일: 2026-04-29

후속 상세 문서: `WORKFLOW_PLUGIN_CAPABILITY_REDESIGN_PLAN.md`

> 이 문서는 Workflow/Capability/Resource 계층의 큰 방향을 정의한다. YouTube 입력, 템플릿 공통화, Clipper1 편입, 현재 구조에서의 단계별 변경 계획은 `WORKFLOW_PLUGIN_CAPABILITY_REDESIGN_PLAN.md`를 기준으로 본다.

## 문제 정의

Clipper2는 단순히 Python 플러그인을 실행하는 앱이 아니다. 장기적으로는 제한된 로컬 PC 리소스 위에서 여러 AI workflow와 공통 media capability를 운영하는 desktop runtime이어야 한다.

현재 플러그인은 2개뿐이지만, 향후 10개 또는 100개의 workflow가 추가될 수 있다. 모든 workflow를 동시에 메모리에 올릴 수 없으므로 runtime resource visibility와 plugin lifecycle policy가 제품의 핵심 기능이 된다.

또한 Clipper1 기능을 하나의 거대한 plugin으로 이식하면, template/TTS/media search/render 같은 기능이 새 workflow마다 중복된다. Clipper1은 monolith plugin이 아니라 reusable capability layer로 분해해야 한다.

## 용어

- `Workflow Plugin`: 사용자가 직접 선택하고 실행하는 제품 기능 단위.
- `Capability`: 여러 workflow가 공통으로 사용하는 기능 단위.
- `Provider`: capability의 실제 구현체. 외부 API 또는 로컬 엔진.
- `Resource Telemetry`: host PC와 runtime process의 CPU/RAM/GPU/VRAM 상태.
- `Control Plane`: NestJS가 담당하는 workflow/job/project/resource orchestration 계층.
- `Host Adapter`: Electron이 담당하는 OS/native/process/telemetry 계층.
- `Compute Worker`: FastAPI/Python plugin이 담당하는 model/AI/video 처리 계층.

## 목표 구조

```text
Angular
  -> NestJS Control Plane
      -> Workflow registry
      -> Capability registry
      -> Job/Project queue
      -> Resource policy
      -> Electron Host Adapter
          -> Process lifecycle
          -> System/process telemetry
          -> Filesystem/native dialog
          -> Packaged Python env
      -> Python Compute Workers
          -> model-heavy or video-heavy execution
```

## Workflow Plugin

Workflow Plugin은 제품 화면에 노출되는 기능이다.

예:

- `dance_highlight`: 안무 롱폼에서 하이라이트 쇼츠 추출
- `dialog_highlight`: 대사 중심 롱폼에서 하이라이트 쇼츠 추출
- `clipper_studio`: 텍스트/URL/복붙 기반 자동 숏폼 생성
- `shortform_remix`: 기존 숏폼의 내용은 유지하되 대본/미디어/스타일 재구성
- `shortform_upgrade`: 기존 숏폼에 hook, pacing, visual enhancement 추가

Workflow Plugin이 가져야 하는 책임:

- 사용자 입력 schema 정의
- 실행 가능한 pipeline graph 정의
- 필요한 capability 목록 선언
- 필요한 model/resource 요구사항 선언
- 결과 project/output manifest 생성

Workflow Plugin이 가지면 안 되는 책임:

- 공통 template engine 직접 소유
- 공통 TTS 구현 직접 소유
- 공통 media search/download 구현 직접 소유
- 공통 render engine 중복 구현
- 다른 workflow에서도 쓰일 LLM prompt/runtime 공통 로직 독점

## Shared Capability

Capability는 여러 workflow가 공유하는 기능이다.

초기 capability 후보:

- `llm.script`: 대본/클립/키워드 생성
- `media.search`: 이미지/영상/GIF 검색
- `media.download`: 외부 media 다운로드/cache
- `tts.synthesis`: 대사 음성 합성
- `subtitle.compose`: 자막 segment/style 생성
- `template.apply`: 레이아웃, 폰트, 타이틀, overlay 적용
- `video.render`: ffmpeg 기반 최종 렌더링
- `video.analyze`: shot/scene/STT/vision 분석
- `asset.store`: project asset 저장소
- `project.manifest`: output manifest 표준화

Capability 구현 위치 기준:

- API orchestration, provider routing, key policy: NestJS 우선
- torch/onnx/STT/vision/video-heavy Python 처리: Python worker
- native filesystem/dialog/OS path/open: Electron host adapter
- UI state/display only: Angular

## Provider

Provider는 capability 뒤의 실제 구현체다.

예:

- `llm.script` provider: OpenAI, Gemini, remote in-house LLM
- `media.search` provider: Naver Image, Kakao, Unsplash, Giphy
- `tts.synthesis` provider: ElevenLabs, Naver Clova, local TTS
- `video.render` provider: local ffmpeg, remote render farm

Provider는 교체 가능해야 한다. Workflow가 특정 provider에 직접 의존하면 안 된다.

## Resource-Aware Plugin Management

Plugin Dashboard의 목표는 단순 상태 표시가 아니다. 로컬 runtime 운영 콘솔이어야 한다.

필수 정보:

- host OS/platform/arch
- logical CPU cores
- system memory total/free/used/usage ratio
- GPU/VRAM summary
- NestJS/Electron/plugin process 상태
- plugin별 PID/port/runtime state
- plugin별 RSS memory/cpu usage
- plugin별 active job count
- plugin별 last activity
- plugin별 model size/estimated RAM/VRAM
- start 가능 여부 또는 resource pressure warning

초기 정책:

- 모든 plugin을 자동으로 동시에 올리지 않는다.
- start 요청 시 resource snapshot을 확인한다.
- 리소스 부족 판단은 처음에는 warning 중심으로 시작한다.
- idle plugin 자동 종료는 기본 비활성화한다.
- 향후 user-confirmed eviction 또는 policy-based eviction을 도입한다.

리소스 예측은 완벽할 수 없다. 다음 세 가지를 조합한다.

- manifest의 estimated resource declaration
- runtime telemetry의 실제 측정값
- OOM/exit code 기반 사후 보정

## Plugin Manifest 확장 방향

현재 manifest는 기능 설명과 model 목록 중심이다. 다음 필드가 필요하다.

```json
{
  "capabilities": {
    "provides": ["workflow.dialog_highlight"],
    "requires": ["video.analyze", "video.render", "project.manifest"]
  },
  "resources": {
    "estimated_ram_mb": 4096,
    "estimated_vram_mb": 2048,
    "requires_gpu": false,
    "preferred_accelerators": ["cuda", "mps", "cpu"],
    "cold_start_cost": "high",
    "max_concurrency": 1,
    "idle_policy": {
      "default": "manual",
      "safe_to_evict_when_idle": true
    }
  }
}
```

이 필드는 처음에는 advisory metadata로 사용한다. 강제 스케줄링은 telemetry가 충분히 쌓인 뒤 도입한다.

## Clipper1 편입 원칙

Clipper1은 다음처럼 분해한다.

- `clipper_studio` workflow plugin
- `llm.script` capability
- `media.search` capability
- `media.download` capability
- `tts.synthesis` capability
- `template.apply` capability
- `subtitle.compose` capability
- `video.render` capability
- `project.manifest` capability

새 숏폼 workflow는 위 capability를 조합한다. 예를 들어 `shortform_remix`와 `shortform_upgrade`는 template/render/TTS/media capability를 공유한다.

## 1차 구현 범위

이번 vertical slice에서는 다음까지만 구현한다.

- [x] Electron host telemetry collector
- [x] packaged bridge `GET /resources`
- [x] NestJS `/v1/resources`
- [x] Angular Dashboard resource summary
- [x] Electron/NestJS process RSS/CPU 표시 기반
- [x] running plugin process RSS/CPU E2E 확인
- [x] manifest `capabilities/resources` advisory metadata 추가
- [x] Dashboard/Store resource profile 1차 표시

이번 slice에서 하지 않는 것:

- GPU/VRAM 정확 측정
- resource admission control
- automatic eviction
- manifest resource schema 강제 검증
- Clipper1 capability 실제 이식

## 구현 메모

2026-04-29 기준 구현된 resource telemetry 경로:

```text
Angular Dashboard
  -> NestJS GET /v1/resources
      -> packaged: ElectronResourceHost -> Electron bridge GET /resources
      -> local/dev: StaticResourceHost
          -> host/process telemetry snapshot
```

macOS에서는 `os.freemem()`만 사용하면 cache/reclaimable memory를 반영하지 못해 사용률이 과장된다. 현재 구현은 `vm_stat`의 free/inactive/speculative pages를 available memory로 보고 사용률을 계산한다.

현재 수집하는 process scope:

- Electron main process
- NestJS utility process
- running Python plugin process

현재 수집하는 accelerator scope:

- NVIDIA 환경: `nvidia-smi` 기반 GPU/VRAM total/used/free/utilization best-effort
- macOS: `system_profiler` 기반 GPU identity/Metal 지원 여부
- Windows fallback: PowerShell `Win32_VideoController` 기반 GPU identity/adapter RAM

아직 수집하지 않는 scope:

- renderer/GPU/network helper process
- child process tree 전체
- model별 실제 메모리 사용량

주의:

- Apple Silicon은 unified memory 구조라 dedicated free VRAM 값이 없다. 현재는 GPU identity와 Metal 지원 여부만 표시하고, `requiresGpu: false` plugin의 start confirmation을 VRAM telemetry 부재만으로 강제하지 않는다.
- Windows non-NVIDIA `AdapterRAM`은 free/used VRAM이 아니라 adapter 총량 추정치다. CUDA admission policy는 `nvidia-smi`와 CUDA runtime 배포 전략을 전제로 별도 설계한다.

2026-04-29 기준 manifest metadata 경로:

```text
clipper_python/plugins/*/manifest.json
  -> Electron ManifestLoader
  -> Electron bridge PluginManifestView
  -> NestJS /v1/plugins
  -> Angular Dashboard/Store
```

현재 resource metadata는 강제 정책이 아니라 advisory 표시용이다. 다음 단계에서 resource snapshot과 결합해 start warning/admission control/idle eviction에 사용한다.

## 다음 단계

1. Resource telemetry foundation 구현
2. manifest resource schema 확장
3. Dashboard를 runtime operations console로 고도화
4. Clipper1 기능을 capability 후보별로 코드 목록화
5. capability registry와 provider abstraction 설계
