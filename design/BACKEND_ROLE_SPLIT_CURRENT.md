# Backend Role Split Current

작성일: 2026-05-06

## 기준 결론

Clipper2의 backend 역할은 다음처럼 나눈다.

```text
Angular
  -> NestJS App API
      -> workflow / source / job / queue / project / capability / provider routing
      -> Electron Host Bridge when native/process control is needed
      -> Python/FastAPI Compute Workers when Python-heavy execution is needed

Electron
  -> packaged desktop host and native/process adapter

Python/FastAPI
  -> model-heavy and video-heavy compute worker
```

## NestJS 책임

NestJS는 local app API와 control plane이다.

담당:

- Angular가 호출하는 기본 API surface.
- workflow/plugin catalog와 user-facing workflow routing 정보.
- source inspect/ingest, source asset normalization.
- job queue, retry/cancel/reorder, job history.
- project/workspace/project history 저장.
- ProjectManifest, TemplatePreset, RenderRecipe, VideoRenderJob contract.
- capability/provider registry와 provider 선택 정책.
- Python/FastAPI worker 호출과 progress/result 수신.
- packaged mode에서 Electron host bridge를 통한 plugin process/resource 제어 요청.

Clipper1 Phase 1에서 NestJS가 맡은 것:

- `ShortformWorkspace`, `ShortformClip`, `MediaSlot` core DTO.
- Clipper1 workspace create/update/generate API.
- `클립 생성`이 project history를 만들지 않도록 workspace repository 분리.
- `숏폼 생성`에서만 `pluginName: clipper1` ProjectSnapshot + `workflow.clipper1` ProjectManifest 생성.
- RenderRecipe 생성과 VideoRenderJob 시작.

## Python/FastAPI 책임

Python/FastAPI는 product backend가 아니라 compute worker다.

담당:

- torch/onnx/STT/vision/model inference.
- Python 생태계가 자연스러운 video-heavy/ffmpeg-heavy 처리.
- plugin SDK 기반 job progress/cancel/result.
- `clipper1_video_render`처럼 `video.render` provider/runtime 역할을 하는 worker.

담당하지 않음:

- user-facing workflow catalog.
- product-level queue/project history.
- auth/billing/entitlement.
- Angular에 노출되는 primary app API.

Clipper1 Phase 1에서 Python이 맡은 것:

- 실제 MP4 렌더링 provider/runtime은 `clipper1_video_render` worker 경로를 유지한다.
- NestJS는 RenderRecipe와 VideoRenderJob contract를 만들고, Python worker는 provider 구현체로 실행된다.

## Electron 책임

Electron은 backend가 아니라 desktop host adapter다.

담당:

- packaged Angular renderer 로딩.
- local NestJS process 실행.
- local Python plugin process 실행.
- port allocation, venv/uv/bootstrap, packaged resource path.
- native file dialog, OS file open/path handling.
- host telemetry와 process lifecycle bridge.

담당하지 않음:

- product workflow orchestration.
- project history source of truth.
- queue policy.
- provider/vendor API policy.

## 참고한 문서

- `.codex/standards/SOLID_AND_BOUNDARIES.md`
- `.codex/design/NESTJS_CONTROL_PLANE_REDESIGN.md`
- `.codex/design/WORKFLOW_PLUGIN_CAPABILITY_REDESIGN_PLAN.md`
- `.codex/design/WORKFLOW_CAPABILITY_RESOURCE_ARCHITECTURE.md`
- `.codex/design/SHORTFORM_PLUGIN_SPLIT_SHARED_CORE_DESIGN.md`
- `.codex/design/CLIPPER1_INVENTORY_AND_SHARED_CAPABILITY_PLAN.md`
- `.codex/context/PROJECT_HISTORY_AND_STATUS.md`

## 현재 예외와 이행 방향

과거 구현 일부에는 Angular가 Python plugin URL이나 WebSocket을 직접 알던 흐름이 남아 있을 수 있다. 새 구현과 Clipper1/Variation 쪽 작업은 NestJS control plane 방향으로 수렴한다.

새 기능을 추가할 때 질문:

- 이 기능은 product state/orchestration인가? 그러면 NestJS.
- Python model/video compute인가? 그러면 Python/FastAPI worker.
- OS/native/process/packaging인가? 그러면 Electron host adapter.
- 화면 상태와 사용자 interaction인가? 그러면 Angular.
