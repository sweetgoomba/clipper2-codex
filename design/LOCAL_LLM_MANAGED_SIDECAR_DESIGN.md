# Codex 작업 지시문

## 목표

현재 Clipper2에 **제품 1차 로컬 LLM 런타임**을 추가한다.

확정한 방향은 다음이다.

```text
제품 1차 로컬 LLM:
  managed llama-server sidecar

Model:
  Gemma 4 E2B/E4B GGUF Q4

Runtime owner:
  Electron

Provider owner:
  NestJS

UI visibility:
  Store = GGUF model asset 준비 상태
  Dashboard = local LLM runtime process/resource 상태
```

이미 `Ollama` provider를 활성화해서 local Gemma 테스트는 완료했다. 이제 Ollama 외부 의존에서 벗어나, Clipper가 직접 `llama.cpp`의 `llama-server`를 관리하는 managed sidecar 구조로 제품 1차 local LLM runtime을 설계/구현한다.

---

## 현재 Clipper2 책임 분리 기준

현재 구조의 기준은 다음으로 유지한다.

```text
Angular
  → 사용자 화면, 입력, 편집, 상태 표시
  → NestJS API만 호출
  → local LLM/Ollama/llama-server를 직접 호출하지 않음

NestJS
  → local app API / control plane
  → workflow / source / job / queue / project / capability / provider routing
  → llm.script provider registry와 provider selection 소유
  → ProjectManifest / artifact / job state 소유

Electron
  → packaged desktop host / native/process adapter
  → local NestJS process 실행
  → local runtime process 실행/중지
  → port allocation
  → packaged resource path
  → model/binary path resolution
  → process lifecycle
  → host telemetry

Python/FastAPI
  → model-heavy / video-heavy compute worker
  → 현재 local LLM text generation의 기본 경로로 사용하지 않음
```

중요한 제약:

```text
- Angular는 llama-server URL, port, provider API shape을 직접 알면 안 된다.
- Workflow code는 특정 LLM vendor/model/runtime을 직접 알면 안 된다.
- Electron은 provider policy를 결정하지 않는다.
- Electron은 llama-server process lifecycle만 관리한다.
- NestJS가 llm.script capability/provider routing을 소유한다.
- local LLM은 workflow가 아니라 capability 뒤의 provider/runtime이다.
```

---

## Local LLM을 Clipper 안에서 보는 방식

local LLM은 Clipper 안에서 다음 계층으로 분류한다.

```text
Workflow:
  workflow.clipper_studio

Capability:
  llm.script
  llm.summarize
  llm.classify
  llm.embed

Provider:
  llm.script.openai
  llm.script.remote_proxy
  llm.script.ollama.external
  llm.script.llama_cpp_server.local
  llm.script.deterministic

Runtime process:
  ollama
  llama-server
  future local-llm-worker
```

`workflow.clipper_studio`는 사용자가 여는 제품 기능이다.

`llm.script`, `llm.summarize`, `llm.classify`, `llm.embed`은 여러 workflow가 공유할 수 있는 capability다.

`llm.script.llama_cpp_server.local`은 `llm.script` capability 뒤의 provider다.

`llama-server`는 실제로 로컬 PC의 CPU/RAM/GPU/Metal/Vulkan/CUDA 리소스를 점유하는 runtime process다.

따라서 `llama-server`는 Store에서 사용자가 “여는” workflow 카드가 아니다. Store/Dashboard에서는 dependency/runtime detail로 보여야 한다.

---

## 왜 managed llama-server sidecar인가

### 1. 현재 책임 분리와 가장 잘 맞음

NestJS가 provider registry/control plane을 소유하고, Electron은 process lifecycle만 관리하는 현재 구조와 맞다.

```text
Electron
  → local-llm-runtime manager
  → spawn llama-server

NestJS
  → llm.script.local_llama_cpp_server provider
  → OpenAI-compatible HTTP call

Store
  → GGUF model download/install state

Dashboard
  → local LLM process status/resource 표시
```

NestJS는 `llama-server`가 제공하는 local HTTP endpoint를 호출한다.

Electron은 `llama-server`를 실행하고, 포트/프로세스/상태를 관리한다.

Angular는 NestJS capability status와 project/job 결과만 본다.

---

### 2. Store/Dashboard 모델과 잘 맞음

현재 문서에는 Store가 plugin assets 준비 상태를 보여주고, Dashboard가 runtime state를 보여주는 구조가 잡혀 있다.

local LLM도 이 모델에 그대로 들어간다.

```text
Store:
  Local LLM assets
    - Gemma 4 E2B GGUF Q4
    - Gemma 4 E4B GGUF Q4
    - size
    - installed / missing
    - download required
    - download progress
    - checksum verification state

Dashboard:
  local_llm_runtime
    - stopped / starting / running / stopping / error
    - pid
    - port
    - model loaded
    - RSS memory
    - active request count
    - last error
    - last exit code
    - startedAt / updatedAt
```

Store는 모델 파일 준비 상태를 보여준다.

Dashboard는 실제 runtime process/resource 상태를 보여준다.

`local_llm_runtime`은 사용자가 “열기” 버튼으로 들어가는 workflow가 아니라, `workflow.clipper_studio`가 의존하는 runtime/provider dependency다.

---

### 3. Crash isolation이 좋음

`llama-server`가 죽어도 Clipper 전체가 죽으면 안 된다.

원하는 동작:

```text
llama-server crash
  → Electron detects exit
  → Dashboard status = error
  → NestJS capability/provider status = unavailable
  → NestJS provider fallback = remote/deterministic
  → Angular displays provider status
```

이미 Clipper Studio에는 provider fallback 상태를 capability endpoint로 노출하고, detail UI에서 provider status를 보여주는 구조가 있다. 이 경로에 `llm.script.llama_cpp_server.local`도 포함시킨다.

---

### 4. OpenAI-compatible API로 기존 provider boundary와 맞추기 쉬움

현재 Clipper Studio에는 remote proxy/OpenAI-compatible `llm.script` provider boundary와 response normalizer가 있다.

managed sidecar도 같은 계열로 붙인다.

```text
OpenAI remote:
  POST https://api.openai.com/v1/chat/completions

Ollama external:
  POST http://127.0.0.1:11434/api/generate
  또는
  POST http://127.0.0.1:11434/v1/chat/completions

llama-server managed:
  POST http://127.0.0.1:<port>/v1/chat/completions
```

즉 `llm.script.llama_cpp_server.local` provider는 기존 OpenAI-compatible provider/normalizer 구조를 최대한 재사용해야 한다.

---

## 구현 대상

### 1. Electron: local LLM runtime manager 추가

Electron에 `llama-server`를 관리하는 runtime manager를 추가한다.

예상 책임:

```text
- packaged resource에서 llama-server binary path 찾기
- userData/models 또는 app resources/models에서 GGUF model path 찾기
- 사용할 모델 선택
- 사용 가능한 random localhost port 할당
- llama-server spawn
- health check
- pid/port/runtimeState 저장
- stdout/stderr log 수집
- unexpected exit 감지
- start/stop/restart 지원
- status snapshot 제공
```

권장 상태 모델:

```ts
type LocalLlmRuntimeState =
  | 'stopped'
  | 'starting'
  | 'running'
  | 'stopping'
  | 'error';

interface LocalLlmRuntimeStatus {
  id: 'local_llm_runtime';
  runtimeState: LocalLlmRuntimeState;
  providerId: 'llm.script.llama_cpp_server.local';
  modelId?: string;
  modelPath?: string;
  port?: number;
  pid?: number;
  baseUrl?: string;
  message?: string;
  lastError?: string;
  lastExitCode?: number | null;
  startedAt?: string;
  updatedAt: string;
  activeRequestCount?: number;
  rssBytes?: number;
}
```

초기에는 `activeRequestCount`와 `rssBytes`가 best-effort여도 된다. Dashboard에서 표시할 수 있는 값부터 붙인다.

---

### 2. Electron IPC / Host Bridge 추가

NestJS가 Electron에게 local LLM runtime을 준비시키거나 상태를 조회할 수 있어야 한다.

필요한 host bridge 기능:

```text
localLlm.getStatus()
localLlm.ensureStarted(options)
localLlm.start(options)
localLlm.stop()
localLlm.restart(options)
localLlm.getModelAssets()
```

중요 제약:

```text
- status 조회는 절대 runtime을 spawn하지 않는다.
- ensureStarted는 필요할 때만 spawn한다.
- start는 모델 asset이 준비되지 않았으면 실패한다.
- stop은 이미 stopped 상태면 no-op이다.
- 모든 endpoint는 renderer가 아니라 NestJS/control plane에서 사용하는 경로로 유지한다.
```

---

### 3. llama-server binary/resource layout

초기 리소스 구조는 다음을 기준으로 설계한다.

```text
resources/
  bin/
    macos-arm64/
      llama-server
    windows-x64/
      llama-server.exe

userData/
  models/
    local-llm/
      gemma-4-e2b-q4.gguf
      gemma-4-e4b-q4.gguf
```

또는 packaged seed 모델을 포함하는 경우:

```text
resources/
  models/
    gemma-4-e2b-q4.gguf

userData/
  models/
    gemma-4-e4b-q4.gguf
```

모델 파일은 앱 번들에 무조건 포함하지 않아도 된다. E4B Q4는 수 GB 크기이므로, 제품 UX에서는 첫 사용 시 다운로드/동의/진행률/검증 흐름이 필요하다.

초기 PoC에서는 수동으로 model path를 지정해도 되지만, 제품 구현은 Store asset state와 연결해야 한다.

---

### 4. Store: Local LLM asset readiness 추가

Store는 local LLM runtime을 “열기” 대상으로 보여주지 않는다.

Store는 다음 asset 준비 상태를 보여준다.

```text
Local LLM assets:
  Gemma 4 E2B GGUF Q4
    - missing / ready
    - size
    - download progress
    - checksum verification

  Gemma 4 E4B GGUF Q4
    - missing / ready
    - size
    - download progress
    - checksum verification
```

초기 정책:

```text
- Gemma 4 E2B Q4: 저사양/빠른 fallback용
- Gemma 4 E4B Q4: 기본 추천 모델
- 사용자가 다운로드 동의 후 설치
- 다운로드 완료 후 checksum 검증
- 설치 상태는 model file 기준으로 판정
- stale marker가 있더라도 파일이 없으면 missing
```

Store의 액션은 다음처럼 둔다.

```text
missing:
  다운로드 / 설치

ready:
  준비됨

error:
  다시 다운로드
```

Store의 “열기”는 workflow인 `Clipper Studio`로 이동해야지, `llama-server`를 직접 여는 버튼이 아니어야 한다.

---

### 5. Dashboard: local LLM runtime 상태 추가

Dashboard는 `local_llm_runtime`을 runtime process/resource로 표시한다.

표시 항목:

```text
local_llm_runtime
  - runtimeState
  - providerId
  - modelId
  - pid
  - port
  - baseUrl
  - RSS memory
  - active request count
  - last error
  - last exit code
  - startedAt
  - updatedAt
```

액션:

```text
stopped:
  시작

starting:
  비활성화

running:
  중지 / 재시작

stopping:
  비활성화

error:
  다시 시작 / 로그 확인
```

중요:

```text
- Dashboard status refresh는 runtime을 자동으로 시작하면 안 된다.
- Dashboard start는 asset 준비 상태를 확인해야 한다.
- local LLM runtime은 workflow readiness와 별개로 runtime dependency로 표시한다.
```

---

### 6. NestJS: `llm.script.llama_cpp_server.local` provider 추가

NestJS에 local llama-server provider를 추가한다.

Provider id:

```text
llm.script.llama_cpp_server.local
```

Capability:

```text
llm.script
```

역할:

```text
- provider registry에 등록
- provider status/capability endpoint에 노출
- 필요 시 Electron Host Bridge로 local LLM runtime ensureStarted 요청
- llama-server OpenAI-compatible endpoint 호출
- 기존 response normalizer로 draft DTO 정규화
- 실패 시 fallback 정책 적용
```

호출 경로:

```text
NestJS llm.script provider registry
  → llm.script.llama_cpp_server.local
  → Electron Host Bridge ensureLocalLlmRuntime()
  → Electron spawns llama-server if needed
  → NestJS calls http://127.0.0.1:<port>/v1/chat/completions
  → response normalizer
  → ProjectManifest artifact/detail
```

요청 형식은 기존 OpenAI-compatible provider와 최대한 맞춘다.

```http
POST http://127.0.0.1:<port>/v1/chat/completions
```

응답은 기존 `llm.script` normalizer를 통과해야 한다.

---

### 7. Clipper Studio draft job 실행 구조

최종 실행 구조는 다음과 같다.

```text
Angular
  → NestJS POST /v1/projects/:id/clipper-studio/draft-jobs
  → NestJS llm.script provider registry
  → llm.script.llama_cpp_server.local
  → Electron Host Bridge ensureLocalLlmRuntime()
  → Electron spawns llama-server
  → NestJS calls http://127.0.0.1:<port>/v1/chat/completions
  → response normalizer
  → ProjectManifest artifact/detail
  → Angular polls job/provider status
```

Angular는 `localhost:<port>`를 몰라야 한다.

Angular는 `llm.script.llama_cpp_server.local`의 내부 request/response shape도 몰라야 한다.

---

## Provider fallback 정책

`llm.script.llama_cpp_server.local` 실패 시 fallback은 기존 provider status/fallback 모델과 연결한다.

권장 우선순위는 환경 설정으로 결정하되, 개념적으로는 다음을 지원한다.

```text
Primary:
  llm.script.llama_cpp_server.local

Fallback:
  llm.script.ollama.external
  llm.script.remote_proxy
  llm.script.openai
  llm.script.deterministic
```

실패 케이스:

```text
- GGUF model missing
- llama-server binary missing
- llama-server start failed
- health check failed
- request timeout
- invalid JSON / invalid response
- response normalizer failed
- process crashed during request
```

각 실패는 provider metadata에 기록한다.

```ts
interface LlmProviderResultMetadata {
  providerId: string;
  modelId?: string;
  runtimeId?: string;
  fallbackUsed?: boolean;
  fallbackFrom?: string;
  errorCode?: string;
  errorMessage?: string;
}
```

---

## 모델 선택 정책

초기 모델은 다음으로 둔다.

```text
Gemma 4 E2B GGUF Q4:
  - 빠른 분류/요약 fallback
  - 저사양 사용자
  - 추후 llm.classify / llm.summarize fast tier 후보

Gemma 4 E4B GGUF Q4:
  - 기본 llm.script local model
  - Clipper Studio script draft 생성 기본 후보
```

초기 제품 1차에서는 `Gemma 4 E4B GGUF Q4`를 기본으로 한다.

단, 사용자의 로컬 리소스가 부족하거나 모델 파일이 없는 경우 `E2B` 또는 remote/deterministic fallback이 가능해야 한다.

---

## Resource / telemetry 정책

local LLM runtime은 실제 메모리를 많이 쓰는 runtime이다.

Dashboard와 resource telemetry에 다음을 반영한다.

```text
- llama-server pid
- RSS memory
- CPU usage best-effort
- model id
- estimated model size
- active request count
- runtime state
```

초기에는 resource admission control을 강제하지 않아도 된다.

단, Store/Dashboard에서 다음 경고는 제공한다.

```text
- 모델 파일 크기가 큼
- 실행 시 수 GB 이상의 메모리를 사용할 수 있음
- 동시에 video render / Python worker와 실행하면 메모리 압박 가능
```

---

## 보안/네트워크 제약

local managed llama-server는 외부 네트워크에 노출하면 안 된다.

실행 시 원칙:

```text
--host 127.0.0.1
--port <random available port>
```

금지:

```text
--host 0.0.0.0
고정 포트만 사용
API key 없는 외부 접근 가능 상태
Angular renderer에서 직접 local llama-server 호출
```

권장:

```text
- random localhost port
- Dashboard/NestJS만 baseUrl 사용
- renderer에는 baseUrl/port 노출하지 않음
- request timeout 적용
- process crash 시 fallback
```

---

## llama-server 실행 옵션 초안

초기 PoC 예시:

```bash
llama-server \
  --model <modelPath> \
  --host 127.0.0.1 \
  --port <allocatedPort> \
  --ctx-size 8192 \
  --flash-attn on
```

옵션은 플랫폼/모델별로 조정 가능하게 둔다.

초기 configurable fields:

```ts
interface LocalLlmRuntimeOptions {
  modelId: 'gemma-4-e2b-q4' | 'gemma-4-e4b-q4';
  modelPath: string;
  ctxSize: number;
  port?: number;
  host: '127.0.0.1';
  threads?: number;
  extraArgs?: string[];
}
```

제품 기본값은 보수적으로 시작한다.

```text
ctx-size:
  4096 또는 8192

host:
  127.0.0.1

port:
  random available port

model:
  gemma-4-e4b-q4
```

---

## 구현 단계

### Phase 0. 코드 조사

먼저 현재 구현을 확인한다.

찾을 것:

```text
- llm.script provider registry
- deterministic provider
- remote proxy/OpenAI-compatible provider
- Ollama provider
- response normalizer
- Clipper Studio capability status endpoint
- provider fallback status 구현
- Electron plugin/runtime status model
- Store asset install state model
- Dashboard runtime status model
- Electron host bridge 경로
```

산출물:

```text
1. 관련 파일 목록
2. 현재 env key 목록
3. Ollama provider request/response shape
4. remote/OpenAI-compatible provider request/response shape
5. response normalizer expected DTO
6. Electron runtime status IPC/bridge 재사용 가능성
```

아키텍처 변경 없이 조사만 먼저 한다.

---

### Phase 1. Design doc 추가

`.codex/design/LOCAL_LLM_MANAGED_SIDECAR_DESIGN.md`를 추가한다.

포함할 내용:

```text
- 결정: product local LLM v1 = managed llama-server sidecar
- 왜 Ollama external provider가 아닌지
- 왜 node-llama-cpp가 v1이 아닌지
- 왜 llama-cpp-python이 기본 경로가 아닌지
- Workflow/Capability/Provider/Runtime 분류
- Store asset model
- Dashboard runtime model
- Electron/NestJS/Angular 책임 경계
- runtime lifecycle
- provider fallback
- security constraints
- test plan
```

---

### Phase 2. Electron local LLM runtime manager 구현

Electron에 local LLM runtime manager를 추가한다.

요구사항:

```text
- binary path resolution
- model path resolution
- random port allocation
- spawn llama-server
- health check
- stop/restart
- status snapshot
- stdout/stderr logging
- unexpected exit → error state
```

이름 예시:

```text
clipper_electron/src/main/local-llm/local-llm-runtime-manager.ts
clipper_electron/src/main/local-llm/local-llm-ipc.ts
clipper_electron/src/shared/local-llm-contract.ts
```

단, 실제 파일 위치와 naming은 현재 repo convention에 맞춘다.

---

### Phase 3. Store asset state 추가

Local LLM GGUF model asset 상태를 Store 모델에 추가한다.

요구사항:

```text
- model missing / ready 표시
- model size 표시
- model path 표시 또는 debug detail
- download/install action placeholder 또는 실제 구현
- checksum verification placeholder 또는 실제 구현
```

초기에는 수동으로 파일을 넣고 ready를 확인하는 방식이어도 된다.

하지만 상태 모델은 나중에 다운로드 UX로 확장 가능해야 한다.

---

### Phase 4. Dashboard runtime state 추가

Dashboard에 `local_llm_runtime`을 추가한다.

요구사항:

```text
- stopped / starting / running / stopping / error
- pid
- port
- model
- memory best-effort
- start/stop/restart
- error message
- refresh/polling
```

Dashboard 조회는 runtime을 자동으로 시작하지 않는다.

---

### Phase 5. NestJS provider 추가

NestJS에 `llm.script.llama_cpp_server.local` provider를 추가한다.

요구사항:

```text
- provider registry에 등록
- provider config/status/capability endpoint에 노출
- Electron Host Bridge로 ensureStarted 호출
- llama-server OpenAI-compatible endpoint 호출
- response normalizer 재사용
- provider metadata에 runtime/model/fallback 정보 기록
- failure 시 fallback
```

환경 설정 예시:

```bash
CLIPPER1_LLM_SCRIPT_PROVIDER=llama_cpp_server
CLIPPER1_LLM_SCRIPT_LLAMA_CPP_MODEL=gemma-4-e4b-q4
CLIPPER1_LLM_SCRIPT_LLAMA_CPP_CTX_SIZE=8192
```

실제 env key 이름은 현재 convention을 보고 결정한다.

---

### Phase 6. Smoke test

수동 smoke test:

```text
1. Gemma 4 E4B GGUF Q4 파일을 userData/models/local-llm 아래에 둔다.
2. Dashboard에서 local_llm_runtime status가 stopped인지 확인한다.
3. Dashboard에서 start 클릭.
4. pid/port/model/running 상태 확인.
5. NestJS capability endpoint에서 llm.script provider status 확인.
6. Clipper Studio draft job 실행.
7. draft가 llama-server provider를 통해 생성되는지 확인.
8. ProjectManifest detail/script/clips가 정상 업데이트되는지 확인.
9. llama-server process kill.
10. Dashboard status가 error로 바뀌는지 확인.
11. NestJS provider fallback이 remote/deterministic으로 동작하는지 확인.
12. Angular provider status card가 오류/fallback 상태를 표시하는지 확인.
```

---

## 성공 기준

최소 성공 기준:

```text
- Ollama 없이 Clipper가 llama-server를 managed sidecar로 실행할 수 있다.
- Electron이 llama-server pid/port/runtimeState를 관리한다.
- NestJS가 llama-server OpenAI-compatible endpoint를 통해 llm.script를 호출한다.
- Angular는 llama-server endpoint를 직접 알지 않는다.
- Store에서 Gemma GGUF model asset 준비 상태를 볼 수 있다.
- Dashboard에서 local_llm_runtime 상태를 볼 수 있다.
- llama-server crash 시 Clipper 앱 전체는 죽지 않는다.
- crash/error 상태가 Dashboard와 provider status에 반영된다.
- provider fallback이 동작한다.
- Clipper Studio draft job이 local LLM provider로 ProjectManifest를 업데이트한다.
```

제품 기준 성공 기준:

```text
- local LLM은 workflow가 아니라 capability/provider/runtime으로 모델링된다.
- Store는 model asset readiness를 보여준다.
- Dashboard는 runtime process/resource를 보여준다.
- NestJS는 provider routing/control plane을 유지한다.
- Electron은 process lifecycle/native host adapter 역할만 한다.
- Python/FastAPI 의존성 없이 text LLM runtime을 운영한다.
- Mac/Windows 공통 확장이 가능하다.
```

---

## 하지 말아야 할 것

```text
- Angular에서 llama-server를 직접 호출하지 않는다.
- Angular에 llama-server port/baseUrl을 노출하지 않는다.
- local LLM runtime을 Store의 user-facing workflow 카드로 만들지 않는다.
- workflow.clipper_studio 코드가 llama.cpp/Ollama/OpenAI 세부 API를 직접 알게 하지 않는다.
- Electron이 provider selection/fallback policy를 결정하게 하지 않는다.
- NestJS control plane process 안에 node-llama-cpp를 직접 로드하지 않는다.
- Python/FastAPI 또는 llama-cpp-python을 기본 local LLM text generation runtime으로 쓰지 않는다.
- Hugging Face Transformers/PyTorch notebook 방식을 제품 runtime으로 옮기지 않는다.
- local LLM server를 0.0.0.0에 바인딩하지 않는다.
- 고정 포트만 전제로 구현하지 않는다.
- model file 존재 여부보다 marker file만 믿지 않는다.
```

---

## 최종 결정

이번 구현의 최종 결정은 다음이다.

```text
Clipper2 product local LLM v1은 managed llama-server sidecar로 구현한다.

Electron:
  local LLM runtime process lifecycle owner

NestJS:
  llm.script provider owner
  provider routing/fallback owner
  ProjectManifest/job/capability status owner

Angular:
  Store asset readiness 표시
  Dashboard runtime state 표시
  Clipper Studio workflow UI 표시

Model:
  Gemma 4 E2B/E4B GGUF Q4

Provider id:
  llm.script.llama_cpp_server.local

Runtime id:
  local_llm_runtime
```

Ollama는 개발/외부 local provider로 유지한다.

```text
llm.script.ollama.external
```

하지만 제품 1차 managed local LLM은 Ollama가 아니라 `llama-server` sidecar를 기준으로 구현한다.
