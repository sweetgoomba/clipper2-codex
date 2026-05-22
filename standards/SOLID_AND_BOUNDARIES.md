# SOLID and Boundary Rules

작성일: 2026-04-29

Clipper2 구현 시 반드시 지킬 원칙이다.

## 1. Single Responsibility

각 프로세스와 모듈은 한 가지 축의 책임만 가진다.

- Angular: UI state, user interaction, view rendering
- NestJS: app API, orchestration, project/job/queue state, DTO contract
- FastAPI plugin: Python compute, model inference, heavy pipeline execution
- Electron: desktop host, native OS integration, packaged runtime bootstrap

Angular 세부 규칙은 `ANGULAR_FRONTEND_RULES.md`를 따른다. 특히 `clipper_angular`는 zoneless 앱이므로 zone.js를 import하거나 zone 기반 테스트 helper로 되돌리면 안 된다.

금지:

- Angular가 plugin process lifecycle을 판단하는 것
- Electron이 product-level workflow/queue policy를 소유하는 것
- FastAPI plugin이 user auth/billing/project history를 소유하는 것
- NestJS가 Python model inference 코드를 재구현하는 것

## 2. Open/Closed

새 pipeline/plugin이 추가될 때 기존 core 코드를 최소 수정해야 한다.

권장:

- plugin manifest 기반 discovery
- NestJS `PluginHost` abstraction
- job type별 handler registry
- DTO 확장 시 backward-compatible field 추가

피해야 할 것:

- `if pluginName === 'dance_highlight'` 분기가 core service 곳곳에 퍼지는 구조
- Angular route와 plugin runtime 정책이 강하게 결합되는 구조

## 3. Liskov Substitution

실행 모드별 구현체는 같은 계약으로 교체 가능해야 한다.

예:

```ts
abstract class PluginHost {
  abstract list(): Promise<PluginManifestView[]>;
  abstract getStatus(name: string): Promise<PluginStatus>;
  abstract ensureStarted(name: string): Promise<string>;
  abstract stop(name: string): Promise<void>;
}
```

구현체:

- `ElectronPluginHost`
- `StaticPluginHost`
- `LocalProcessPluginHost`
- `RemotePluginHost`

Angular/NestJS 상위 service는 어떤 구현체인지 몰라야 한다.

## 4. Interface Segregation

큰 service 하나에 모든 기능을 넣지 않는다.

권장 분리:

- `PluginHost`: plugin runtime 접근
- `PluginCatalogService`: manifest/catalog 조회
- `PluginRuntimeService`: start/stop/status
- `JobQueueService`: enqueue/cancel/retry/reorder
- `ProjectRepository`: project/job 저장
- `SourceService`: file/youtube/text source preflight

작은 interface가 많아지는 것은 괜찮다. 대신 호출 방향과 책임이 명확해야 한다.

## 5. Dependency Inversion

상위 정책은 하위 구현에 직접 의존하지 않는다.

예:

- `JobQueueService`는 Electron IPC에 직접 의존하지 않는다.
- `JobQueueService`는 `PluginHost` interface에 의존한다.
- `PluginHost` 구현체가 Electron bridge, static URL, remote URL을 각각 처리한다.

AI/provider 기능에는 이 원칙을 더 엄격하게 적용한다.

상위 workflow는 다음 구현체를 직접 알면 안 된다.

- OpenAI, Gemini, Ollama, local Gemma, remote LLM proxy
- Naver/Kakao/Pixabay/Tenor image search, company/custom media search proxy
- local Stable Diffusion류 image generation server
- macOS `say`, Naver Clova, Oute TTS, 다른 local/remote TTS server
- local ffmpeg, Python worker, remote render farm

상위 workflow가 알아야 하는 것은 provider 이름이 아니라 capability contract다.

예:

```text
workflow.clipper_studio
  -> llm.script
  -> media.search 또는 image.generate
  -> tts.synthesis
  -> template.apply
  -> video.render
```

각 capability 뒤에는 여러 provider 구현체가 붙을 수 있어야 한다.

```text
llm.script
  -> llm.script.openai_responses
  -> llm.script.ollama.local
  -> llm.script.remote_proxy

tts.synthesis
  -> tts.local_os.say
  -> tts.clova.remote
  -> tts.oute.local_server

media.search / image.generate
  -> media.search.remote_proxy.image
  -> media.search.naver.image
  -> media.search.kakao.image
  -> image.generate.local_diffusion
```

금지:

- workflow service 안에서 특정 vendor API request/response shape을 직접 조립하는 것
- Angular가 OpenAI/Naver/Clova/Ollama 같은 provider 선택과 credential policy를 아는 것
- render recipe가 vendor-specific URL이나 API response를 직접 참조하는 것
- provider key/billing/retry/fallback 정책이 UI component나 workflow editor에 새는 것

허용:

- NestJS capability registry가 policy에 따라 provider를 선택한다.
- provider adapter가 vendor/local runtime별 request/response를 contract DTO로 정규화한다.
- provider 결과는 항상 ProjectManifest artifact 또는 typed draft DTO로 승격한다.
- provider 교체는 workflow/editor/render 코드 변경 없이 provider 등록/설정 변경 또는 adapter 교체로 끝나야 한다.

## 6. Process Boundary Rules

### Angular -> NestJS

Angular의 기본 backend 호출은 NestJS로 수렴한다.

허용:

- NestJS REST/WS/SSE API 호출
- Electron IPC를 통한 file dialog 등 native-only 기능

지양:

- Python plugin `/jobs` 직접 호출
- Python plugin WebSocket 직접 구독

### NestJS -> FastAPI Plugin

NestJS는 FastAPI plugin을 compute worker로 호출한다.

허용:

- `/health`
- `/jobs`
- `/jobs/:id/events`
- `/preflight/*`

지양:

- FastAPI plugin 내부 파일 구조에 직접 의존
- plugin별 Python implementation detail을 NestJS core에 하드코딩

### NestJS -> Electron

Packaged mode에서 NestJS는 Electron host bridge를 통해 desktop runtime 기능을 요청한다.

허용:

- plugin process start/stop/status
- userData/resource path 조회
- ffmpeg/model asset 준비 상태 확인

지양:

- NestJS business logic을 Electron main에 위임

## 7. Documentation Required for Architecture Changes

아키텍처 경계를 바꾸는 구현은 반드시 문서 업데이트를 동반한다.

필수 업데이트:

- `.codex/implementation/TASKS.md`
- `.codex/implementation/WORKLOG.md`
- 필요 시 `.codex/design/*.md`

## 8. Compatibility Rule

Electron packaged mode, local dev mode, docker/server mode를 모두 고려한다.

새 기능을 만들 때 질문:

- Electron 없이 Angular + NestJS + plugin만 띄워도 동작 가능한가?
- Docker에서 NestJS가 remote plugin URL만 알고 있어도 동작 가능한가?
- packaged Electron에서는 host bridge로 같은 계약을 만족할 수 있는가?

답이 모두 "예"가 되도록 abstraction을 설계한다.

## 9. Provider Substitution Rule

새 AI 기능을 붙일 때는 처음부터 provider 교체를 전제로 설계한다.

필수 질문:

- 이 기능이 hosted API, local server, local model, remote company proxy 중 무엇으로 바뀌어도 contract가 유지되는가?
- provider implementation만 바꾸고 workflow/editor/render code를 유지할 수 있는가?
- credential, billing, quota, retry, fallback, telemetry가 provider boundary 안에 있는가?
- provider output이 artifact/project manifest로 정규화되는가?
- 테스트에서 fake provider를 주입해 network 없이 검증할 수 있는가?

답이 "아니오"면 아직 구현이 아니라 vendor coupling이다. 이 경우 먼저 interface/registry/adapter 경계를 만든 뒤 실제 provider를 붙인다.
