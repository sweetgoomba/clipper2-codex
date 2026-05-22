# Adlight -> Clipper2 프로젝트 변천사 및 현재 상태

작성 기준일: 2026-04-27

이 문서는 레거시 `adlight_*` 폴더에서 현재 `clipper_*` 폴더로 이어진 문서 기록을 한곳에 모은 정리본이다. 대상은 `adlight_angular`, `adlight_python`, `adlight_nestjs`, `clipper_angular`, `clipper_python`, `clipper_nestjs`, `clipper_electron`의 Markdown 문서와 루트 `.claude` 문서다. `node_modules`, `.git`, 빌드 산출물, 캐시성 문서는 제외했다.

## 1. 한 줄 요약

프로젝트는 처음에 `adlight_angular` + `adlight_python` 중심의 혼합형 데스크톱/서버 코드베이스에서 시작했다. 이후 D2X/Clipper 자동 숏폼 생성과 HighlightStudio 파이프라인이 같은 Angular/Python 저장소 안에 누적되면서 빌드, 런타임, 의존성, 배포 문제가 커졌고, 2026-04-13부터 "플러그인 단위로 런타임과 의존성을 격리한다"는 방향으로 재설계되었다. 현재 기준 구현 대상은 `clipper_angular`, `clipper_python`, `clipper_nestjs`, `clipper_electron` 네 폴더이며, 앱 이름은 Clipper2로 정리되고 있다.

## 2. 저장소 시대 구분

### 2.1 레거시 혼합 구조: `adlight_*`

원래 구조는 다음 세 폴더였다.

- `adlight_angular`: Angular 앱, Electron 셸, ClipperStudio/HighlightStudio 빌드 스크립트가 섞인 프론트엔드 저장소
- `adlight_python`: FastAPI 서버, D2X/Clipper 숏폼 생성, Highlight 파이프라인, PyInstaller 패키징, 모델/미디어 처리 로직이 섞인 Python 저장소
- `adlight_nestjs`: NestJS 기본 스타터에 가까운 레거시 폴더. 당시 실사용 대상은 아니었음

이 시기의 핵심 문제는 제품 경계가 코드 경계와 맞지 않았다는 점이다. 같은 Angular/Python 코드베이스가 ClipperStudio와 HighlightStudio를 동시에 품었고, 빌드 설정, 버전, 릴리스 스크립트, 서버 로직, 로컬 모델 런타임이 서로 영향을 주는 구조였다.

### 2.2 Highlight 파이프라인 안정화와 Windows 패키징 시기

2026-03-16부터 2026-03-25 전후까지 `adlight_python/docs/highlight`와 `adlight_angular/docs/highlight`에는 긴 영상 하이라이트, 댄스 하이라이트, Mac/Windows 데스크톱 배포 기록이 집중되어 있다.

이 시기에는 다음 일이 진행되었다.

- 긴 영상/dialog 파이프라인의 STT, 장면 분할, GPT 구간 선택, 제목 생성, 클립 내보내기 안정화
- 댄스 파이프라인의 YOLO 포즈, InsightFace 얼굴 임베딩, 멤버 클러스터링, ffmpeg 렌더링, 진행률 이벤트 추가
- Mac/Windows Electron 앱 빌드와 HighlightStudio 배포 스크립트 정리
- PyInstaller frozen 환경에서 CUDA, ONNX Runtime GPU, OpenMP, MSVC 런타임, AV1 디코딩, TorchVision ops 문제 해결

이 기록은 현재 Clipper2 설계의 중요한 배경이다. 특히 "하나의 frozen exe에 여러 무거운 파이프라인을 넣는 방식은 장기적으로 유지보수하기 어렵다"는 결론으로 이어졌다.

### 2.3 D2X/Clipper 기능 확장 시기

2026-04-01부터 2026-04-08 전후 문서에는 D2X/Clipper 내부 숏폼 생성 도구의 기능 확장이 기록되어 있다.

당시 흐름은 다음과 같았다.

- 사용자 입력 URL/prompt/text를 바탕으로 GPT가 스크립트, 키워드, 제목 생성
- 이미지/TTS/ffmpeg 조합으로 영상 생성
- FastAPI와 Angular가 프로젝트 상태, SSE 진행률, 관리자 화면을 관리
- PostgreSQL, S3, 미디어 서버, webhook 연동
- `CREATED`, `TEMP`, `QUEUED`, `PROCESSING`, `COMPLETED`, `ERROR` 상태 모델 사용

`Super Clone` 기능은 하나의 원본 프로젝트에서 템플릿, BGM, TTS 조합을 바꾼 다수의 변형 영상을 생성하는 방향으로 설계되었다. 초기에는 동기 실행 문제가 있었고, 이후 "Phase 1에서 셸 프로젝트를 즉시 만들고, Phase 2에서 FastAPI BackgroundTasks로 비동기 처리"하는 방식으로 개선되었다.

이 시기 문서에서 확인된 주요 결론은 다음과 같다.

- SSE는 프로토콜 자체가 문제가 아니라 구현상 세션 타겟팅이 문제였다.
- `_last_subscribe_key` 때문에 마지막 구독 세션으로 이벤트가 잘못 전달되는 문제가 있었고, request `session_id`를 큐와 emit 경로에 포함하는 방식으로 수정되었다.
- Angular에는 10초 polling과 focus/visibility 재동기화가 안전망으로 추가되었다.
- 관리자 로그인은 일반 사용자 JWT/session 흐름과 admin access token 흐름이 섞여 있어 interceptor/guard 수정이 필요했다.

이 D2X/Clipper 기능은 현재 `clipper_*` 새 구조의 직접 기반이라기보다는, "기능이 커질수록 혼합형 구조가 빠르게 복잡해진다"는 교훈으로 이어졌다.

### 2.4 아키텍처 재논의와 플러그인 전환

2026-04-13부터 2026-04-16까지의 `adlight_python/docs/*discussion*`, `plugin_*` 문서가 현재 아키텍처의 출발점이다.

초기 오해는 "Torch와 ONNX Runtime은 같이 쓸 수 없다" 또는 "로컬 런타임은 프로덕션에 부적합하다"는 쪽이었지만, 문서상 결론은 달랐다. 실제 문제는 여러 무거운 파이프라인이 하나의 frozen 실행 파일과 하나의 의존성 집합 안에 섞여 있다는 점이었다.

최종 방향은 다음과 같이 정리되었다.

- 플러그인이 배포, 의존성, 런타임 선택, 모델, 업데이트의 단위가 된다.
- 각 플러그인은 별도 프로세스로 실행되어 의존성과 크래시를 격리한다.
- 앱은 사용자 PC에서 계산을 수행하고, remote server는 인증, 구독, 카탈로그, LLM proxy처럼 로컬에 둘 수 없는 기능을 맡는다.
- PyInstaller exe는 소스 보호 효과도 제한적이고 패키징 복잡도가 너무 높으므로 중심 전략에서 제외한다.
- ComfyUI처럼 앱에 Python/소스/플러그인을 포함하고 `uv`로 실행 환경을 관리하는 방향이 선택되었다.
- IPC는 stdio JSON-RPC가 아니라 TCP loopback 기반 HTTP + WebSocket으로 정리되었다.
- 플러그인 lifetime은 기본 idle-kill, OOM 방어, 사용자 persistent 옵션 조합으로 설계되었다.
- 취소, heartbeat, crash recovery, OOM exit code, 재시도 정책이 SDK/런타임 레벨 요구사항으로 정리되었다.

이 단계에서 "NestJS를 내부 TypeScript 모듈로 쓸 것인가, 별도 프로세스로 둘 것인가", "Python job API를 Angular가 직접 호출할 것인가" 같은 결정이 계속 변했다. 현재 기준 결정은 뒤쪽의 "현재 기준 정리"가 우선이다.

### 2.5 현재 구조: `clipper_*`

2026-04-16 이후 새 구조는 네 개 폴더로 분리되었다.

- `clipper_python`: Python Plugin SDK와 실제 플러그인(`dialog_highlight`, `dance_highlight`)
- `clipper_angular`: 순수 Angular 19 SPA. Electron/NestJS 직접 의존 제거
- `clipper_nestjs`: 로컬 앱 API. pre-pipeline, 외부 API proxy, 향후 auth/billing/LLM proxy 담당
- `clipper_electron`: 데스크톱 셸. Angular 로딩, Python 플러그인 프로세스, NestJS 프로세스, 모델/ffmpeg 설치, 파일 선택, 패키징 담당

루트 `.claude` 폴더는 2026-04-27 기준 중앙 문서 허브로 추가되었고, 빌드 가이드, 런타임 가이드, 현재 태스크, 워크로그, 플러그인 스토어/대시보드 설계가 정리되어 있다.

## 3. 시간순 변천사

### 2026-03-16: Highlight 긴 영상 파이프라인 버그 수정

`adlight_python/docs/highlight` 기록상, 긴 영상 하이라이트 파이프라인에서 STT 텍스트가 클립 경계를 넘어가거나 제목과 실제 클립이 어긋나는 문제가 있었다. 해결 방향은 word-level timestamp를 사용하고, GPT 결과와 실제 clip export 순서를 start time 기준으로 맞추는 것이었다.

또한 GPT 문장 분할 호출이 샷 단위로 과도하게 발생하던 구조를 하나의 batched call로 줄여 비용과 지연을 줄였다.

### 2026-03-17: 긴 영상 분석과 댄스 파이프라인 개선

긴 영상/dialog 파이프라인은 silence detection, faster-whisper STT, PySceneDetect, OCR, OpenCLIP, MFCC, GPT selection/meta generation을 조합하는 구조로 문서화되었다.

댄스 파이프라인은 YOLO pose, InsightFace, sklearn clustering, ffmpeg 렌더링으로 구성되었다. 이때 GPU 감지, CUDA/MPS 분기, ffmpeg hardware encoder, `face_sample_frames` 제한, SSE progress, audio crossfade 같은 개선이 기록되었다.

멤버 이미지 검색은 Naver 우선, Kakao fallback, URL validation 흐름이었다. 다만 동기 HEAD 체크가 느릴 수 있고, 얼굴 매칭용 reference image 품질이 중요하다는 점이 확인되었다.

### 2026-03-18 ~ 2026-03-19: HighlightStudio 빌드와 배포 분리

`adlight_angular`에서 ClipperStudio와 HighlightStudio를 같은 Angular/Electron 프로젝트로 빌드하되, 앱 이름, 버전, S3 bucket, 빌드 산출물을 분리하는 방식이 문서화되었다.

이때 이미 ClipperStudio에는 실제 사용자가 있었기 때문에 HighlightStudio 작업이 ClipperStudio 배포에 영향을 주면 안 된다는 제약이 있었다. 하나의 프로젝트에서 두 제품을 나누기 위해 release script와 version hack이 늘어났고, 이후 새 저장소 분리의 근거가 되었다.

Windows 빌드에서는 `c10.dll` WinError 1114가 발생했고, PyInstaller에 포함된 오래된 MSVC runtime DLL을 제거해 시스템 runtime을 쓰도록 하는 방식으로 우회했다.

### 2026-03-20 ~ 2026-03-25: Windows CUDA/PyInstaller 문제 누적

이 기간 문서에는 frozen Python 배포에서 겪은 문제가 집중되어 있다.

- TorchVision `_has_ops=False` 문제: PyInstaller ctypes hook이 `name=None`을 전달하면서 ops 로딩이 실패. 원래 이름을 유지하도록 수정
- CUDA/CPU 빌드 스크립트 분리: Pipfile만으로 torch CUDA index와 onnxruntime variant를 안정적으로 표현하기 어려웠음
- NSIS 7GB CUDA installer 문제: `nsis-web`과 S3 payload 방식으로 전환
- OpenMP duplicate, DLL loading, `torch.cuda.is_available()` false, InsightFace와 YOLO CUDA context 충돌
- frozen 환경 YOLO FP16 crash로 FP16 비활성화
- AV1/libdav1d crash: ffmpeg/OpenCV thread 제한
- face extract 22분 병목: sequential read와 montage 병렬화로 개선
- OpenCV Unicode path: `np.fromfile` + `imdecode`로 우회
- ONNX Runtime GPU frozen 오류: 최신 버전 대신 1.19.2 pin, `capi` DLL 복사

현재 설계가 PyInstaller 중심 배포를 버린 이유가 이 시기 기록에서 가장 분명하게 드러난다.

### 2026-04-01 ~ 2026-04-08: D2X/Clipper Super Clone과 SSE 안정화

Super Clone은 하나의 프로젝트에서 여러 client variation을 생성하는 기능으로 설계되었다. variation은 `template_id`, `bgm_id`, `tts_id` 같은 값으로 구성되며, TTS가 달라지면 음성도 다시 생성해야 했다.

초기 구현은 동기 작업이 길어지는 문제가 있었고, 이후 shell project를 먼저 만들고 실제 media generation을 background로 넘기는 구조로 바뀌었다. Angular에서는 library status polling과 focus/visibility 재확인이 추가되었다.

SSE 세션 타겟팅 문제는 중요한 기록이다. 마지막 구독자의 세션 키를 전역처럼 쓰는 구조 때문에, 실제 작업 이벤트가 엉뚱한 세션으로 가는 문제가 있었다. 이후 job/request 단위 `session_id`를 명시적으로 전달하는 방식으로 고쳤다.

이때의 결론은 "SSE 대신 WebSocket이어야 한다"가 아니라, one-way 진행률에는 SSE도 충분하며 구현의 타겟팅과 안전망이 중요하다는 쪽이었다.

### 2026-04-13: 전체 리팩토링 필요성 확정

`architecture_discussion_2026-04-13.md`에서 전체 방향이 크게 바뀐다. 제품은 Clipper Studio SaaS이고, 앞으로 5~10개 이상의 플러그인이 생길 수 있으며, 계산은 사용자 PC에서 수행한다는 전제가 명시되었다.

문서상 핵심 판단은 다음과 같다.

- "모든 파이프라인을 하나의 런타임에 넣는다"가 문제다.
- 플러그인별로 Python/Torch/ONNX Runtime/DirectML/CUDA 같은 선택을 분리해야 한다.
- Windows 사용자 범위까지 고려하면 DirectML/ONNX Runtime도 의미가 있지만, 플러그인별로 torch를 선택할 수 있어야 한다.
- NestJS는 앱/API 경계 역할을 맡고, Python은 내부 연산 플러그인 쪽으로 이동한다.

### 2026-04-14 ~ 2026-04-16: 플러그인 런타임 설계 확정

이 시기 문서에서 플러그인 아키텍처의 핵심 축이 정리되었다.

- 배포 방식: PyInstaller exe가 아니라 embedded Python + plugin folder + `uv`
- IPC: 최종적으로 HTTP + WebSocket over loopback
- lifecycle: 기본 idle-kill 5분, OOM 방어, user persistent 옵션
- cancellation: `DELETE /jobs/{id}`와 SDK cancel flag
- health: polling과 progress heartbeat
- crash: detect, respawn, retry limit, user-facing error, queue continuation
- manifest v1: name/version/sdk_version/display_name/dependencies/models/accelerators/ipc/input/output/runtime_requirements 등
- LLM API key: 클라이언트 `.env`에 직접 넣는 것은 보안/비용 리스크. 장기적으로 LLM proxy 필요

주의할 점은 `plugin_ipc_design_2026-04-14.md`의 stdio JSON-RPC 설계가 이후 문서에서 명시적으로 "역사적/잘못된 결정"에 가깝게 취급된다는 것이다. 현재 기준은 HTTP + WebSocket이다.

### 2026-04-16 ~ 2026-04-17: `clipper_python` 생성

새 Python 저장소는 `clipper_plugin_sdk`와 `plugins/dialog_highlight`, `plugins/dance_highlight`로 구성되었다. Python 3.11과 `uv` workspace가 기준이 되었다.

기존 `adlight_python`의 비즈니스 로직은 포팅하되, PyInstaller, `.env`, `sys._MEIPASS`, 앱 내부 path utility 같은 cross-app 의존을 제거하는 방향으로 정리되었다.

설계적으로는 `PluginBase`가 플러그인 계약을 담당하고, `PluginRuntime`이 FastAPI route, job 관리, cancellation, health 같은 인프라를 담당하는 SOLID 분리가 진행되었다. Dance 쪽은 protocol/factory를 통해 pipeline 구현을 주입하는 방향으로 정리되었다.

이 시점에 unit test, E2E smoke, OOM subprocess test, cancel test가 추가되었다. 실제 샘플 pipeline 검증에서는 dialog는 6개 clip 생성까지 확인되었고, dance는 얼굴 reference 품질 이슈가 별도로 남았다.

### 2026-04-20 ~ 2026-04-21: `clipper_angular`, `clipper_electron`, `clipper_nestjs` 생성

`clipper_angular`는 Angular 19 standalone/zoneless/HashLocation 기반의 순수 SPA로 새로 만들어졌다. 기존 `adlight_angular`와 달리 Electron/NestJS 직접 의존을 제거하고, feature registry와 PluginLocator를 통해 런타임 플러그인 가용성을 확인하는 구조가 되었다.

`clipper_electron`은 BrowserWindow, preload bridge, PluginManager, ProcessManager, PortAllocator, ManifestLoader를 가진 새 Electron 셸로 만들어졌다. 실제 Python 플러그인은 `uv run`으로 spawn하고, `CLIPPER_PYTHON_ROOT`를 통해 sibling `clipper_python`을 찾는 방식이 기록되어 있다.

`clipper_nestjs`는 dance pre-pipeline과 key/proxy 역할을 맡는 로컬 앱 API로 새로 만들어졌다. 초기 기능은 artist/member/image 검색이다. artist detection은 로컬 JSON, member lookup은 Wikipedia/Wikidata, image search는 Naver/Kakao 연동으로 구성되었다. 2026-04-21에는 QID 관련 버그가 수정되었다.

이 단계에서 Electron 안에서 dance/dialog pipeline이 E2E로 `PIPELINE_DONE`까지 가는 것이 확인되었다.

### 2026-04-22 ~ 2026-04-23: 패키징, 모델/ffmpeg 다운로드 UX, 설정 주입

Electron 쪽에서는 `electron-builder` 패키징, Mac dmg, Windows nsis 설정, first-run `uv sync`, app renamed Clipper2, 로그 경로 정리, ffmpeg runtime download, model download IPC가 추가되었다.

Python 쪽에서는 모델 로딩 이벤트가 stdout JSON으로 흘러가고, dance/dialog 플러그인이 pipeline 시작 전 모델을 미리 로드하는 방향으로 개선되었다. Dance는 PoseEngine/FaceClusterService eager load, Dialog는 Whisper/OpenCLIP warm load가 기록되어 있다.

Angular 쪽에서는 ffmpeg/model download consent overlay, progress bar, BackendLocator, byte-level download progress, model name 표시가 추가되었다.

이때 first plugin install에서 health timeout만 보고 실패하는 문제가 있었고, `waitForHealthOrDeath`처럼 프로세스 종료도 함께 보는 방향으로 수정되었다.

### 2026-04-27: 루트 중앙 문서화와 현재 기준 아키텍처 정리

루트 `.claude`가 중앙 문서 허브로 생기고, `BUILD_GUIDE`, `PLUGIN_RUNTIME_GUIDE`, `ARCHITECTURE_REVIEW`, `PLUGIN_STORE_DASHBOARD_DESIGN`, `TASK`, `WORKLOG`가 추가되었다.

패키지 빌드는 `clipper_electron`에서 다음 흐름으로 정리되어 있다.

1. Angular build
2. NestJS bundle
3. Electron TypeScript compile
4. uv source bundle 준비
5. electron-builder 패키징

NestJS는 Option C로 정리되었다. 즉 Python plugin으로 옮기는 Option A가 아니라, NestJS를 별도 로컬 앱 API 프로세스로 유지하고 Electron이 `utilityProcess.fork`로 실행한다. `NEST_DATA_DIR`, `127.0.0.1` binding, CORS `null`, dynamic port, packaged resource 포함이 현재 방향이다.

모델 다운로드 UX는 byte-level progress, stderr parser, marker auto-restore, 실제 파일 존재 확인까지 정리되었다. 다만 marker와 실제 파일 불일치 처리는 계속 주의해야 한다.

## 4. 현재 기준 아키텍처

### 4.1 `clipper_angular`

역할:

- 사용자 UI
- feature registry 기반 기능 노출
- PluginLocator를 통한 plugin URL 확인
- BackendLocator를 통한 NestJS local app API URL 확인
- Python plugin `/jobs` 호출과 WebSocket progress 구독
- model/ffmpeg/download consent overlay와 progress UI

중요한 현재 기준:

- Angular는 Electron, NestJS, Python 구현체에 직접 빌드 의존하지 않는다.
- Electron 환경에서는 preload API를 통해 native 기능과 런타임 URL을 얻는다.
- browser/local 환경에서는 fallback locator를 쓴다.
- pipeline job은 현재 Angular가 Python plugin HTTP/WS endpoint를 직접 호출하는 구조로 보는 것이 맞다.

### 4.2 `clipper_electron`

역할:

- 데스크톱 앱 셸
- Angular 정적 파일 로드
- Python plugin process spawn/health/kill/log 관리
- NestJS local app API process spawn/health/backend URL 제공
- 파일 선택 dialog
- model/ffmpeg 다운로드 IPC
- `.env` 주입
- packaged app 빌드와 runtime resource 관리

현재 구현 기준:

- Python 플러그인은 `uv run` 기반으로 실행한다.
- packaged app에서는 source bundle과 `uv sync` 기반 런타임을 쓴다.
- 현재 패키징은 단일 `userData/clipper_venv`를 중심으로 정리되어 있다.
- 장기적으로는 SDK 공통 venv + plugin별 venv 같은 two-tier/per-plugin venv 방향이 더 적합하다는 논의가 있다.
- NestJS는 `utilityProcess.fork`로 실행하고 dynamic port를 Angular에 전달한다.

### 4.3 `clipper_python`

역할:

- Plugin SDK 제공
- `dialog_highlight`, `dance_highlight` 실제 plugin 구현
- FastAPI 기반 plugin runtime
- job lifecycle, progress, cancellation, health, shutdown 제공
- 모델 로딩 이벤트와 OOM/crash 대응 기반 제공

현재 구현 기준:

- `PluginBase`는 plugin contract, `PluginRuntime`은 infra/runtime 책임을 가진다.
- cancellation은 SDK cancel flag와 `/jobs/{id}` delete flow로 설계되었다.
- OOM/crash는 exit code와 subprocess test로 검증되었다.
- 모델 다운로드는 Electron이 UX와 설치를 관리하고, plugin은 모델 존재/로딩 상태를 노출한다.
- Dialog/Dance pipeline의 핵심 로직은 legacy `adlight_python`에서 가져오되, app-specific path와 PyInstaller 의존성을 제거하는 방향이다.

### 4.4 `clipper_nestjs`

역할:

- 로컬 앱 API / 제한적 gateway
- dance pre-pipeline API
- artist/member/image search
- 향후 LLM proxy, subscription/auth/billing, plugin catalog/CDN registry와 연결될 서버 성격의 기능

현재 구현 기준:

- NestJS는 legacy `adlight_nestjs`와 다른 새 프로젝트다.
- Electron이 NestJS를 로컬 프로세스로 실행한다.
- packaged app에서는 NestJS bundle과 data file을 resources 안에 포함한다.
- `127.0.0.1` binding과 dynamic port를 사용한다.
- CORS `null` origin 허용은 packaged Electron 환경을 위한 설정이다.

### 4.5 Root `.claude`

역할:

- 현재 프로젝트 전체의 중앙 문서 허브
- build/runtime/current task/worklog/plugin dashboard/store design 정리

주의:

- 일부 문서는 그날의 논의/상태를 기록하므로, 같은 주제에 대해 폴더별 `.claude`와 충돌할 수 있다.
- 현재 기준 결정은 루트 `.claude`의 2026-04-27 문서와 `clipper_electron`, `clipper_nestjs` 최신 WORKLOG를 우선해야 한다.

### 4.6 원래 설계에서 현재 구조로 바뀐 이유

초기 설계는 다음에 가까웠다.

```text
Angular
  -> NestJS only
    -> FastAPI pipeline servers
      -> Python pipeline 실행
```

즉 Angular가 통신하는 유일한 backend는 NestJS이고, pipeline 실행이 필요하면 NestJS가 FastAPI plugin 서버를 호출한 뒤 응답과 진행 상황을 Angular에 전달하는 구조였다.

현재 구현은 다음에 가깝다.

```text
Angular
  -> NestJS: dance 사전 단계, 외부 API, 향후 auth/LLM/catalog
  -> Electron IPC: plugin URL 요청, 파일 선택, 모델/ffmpeg 설치
  -> Python FastAPI plugin: /jobs, /jobs/{id}/events 직접 호출

Electron
  -> Python plugin process 실행/종료/포트/로그/venv 관리
  -> NestJS local process 실행/포트 관리
```

이 변화의 가장 큰 이유는 PluginManager의 책임 위치가 NestJS가 아니라 Electron main process 쪽으로 이동했기 때문이다. PluginManager는 단순 API proxy가 아니라 OS process spawn, port allocation, venv/env 주입, model/ffmpeg 준비, stdout/stderr log, packaged resource path, app shutdown 시 cleanup 같은 host-level 책임을 가진다. 이 책임은 NestJS HTTP server보다 Electron main process가 맡는 것이 자연스럽다.

그 외에 구조가 바뀐 이유는 다음과 같다.

- NestJS가 모든 pipeline traffic을 proxy하면 대부분의 `/jobs`, WebSocket progress, cancel 요청을 그대로 전달하는 thin pass-through가 된다.
- Plugin process의 실제 URL과 lifecycle은 Electron이 알고 있으므로, NestJS가 Python을 호출하려면 다시 Electron에 묻는 우회 구조가 필요해진다.
- 그러면 `Angular -> NestJS -> Electron -> Python` 또는 `NestJS -> Electron IPC -> Python`처럼 책임 경계가 더 복잡해진다.
- Python plugin SDK가 공통 `/jobs`, `/jobs/{id}`, `/jobs/{id}/events`, `/health` contract를 제공하면서 Angular가 표준 contract로 직접 붙는 것이 단순해졌다.
- 제품 성격이 일반 웹앱보다 "Electron 기반 로컬 plugin host"에 가까워졌고, 이 경우 Electron이 host/backend 책임 일부를 가져가는 것이 맞다.

따라서 현재 구조의 기준 원칙은 초기 원칙과 다르다.

초기 원칙:

```text
Angular는 NestJS만 호출한다.
NestJS가 Python/FastAPI를 호출한다.
```

현재 원칙:

```text
Angular는 Python process lifecycle을 직접 관리하지 않는다.
Angular는 Electron이 제공한 plugin URL에만 표준 /jobs 계약으로 접근한다.
앱/비즈니스/외부 API는 NestJS를 거친다.
OS/process/install 권한은 Electron만 가진다.
무거운 compute는 Python plugin process가 맡는다.
```

이렇게 보면 NestJS의 역할이 사라진 것이 아니라, "pipeline proxy" 역할을 버리고 "앱 API/local backend" 역할로 좁혀진 것이다.

### 4.7 `local gateway` 표현의 정확한 의미

이 문서에서 `clipper_nestjs`를 `local gateway`라고 부른 것은 "모든 요청이 반드시 통과하는 API gateway"라는 뜻이 아니다. 현재 기준으로 더 정확한 표현은 `local app API` 또는 `local backend service`다.

현재 `clipper_nestjs`의 의미:

- Electron 앱 안에서 로컬로 실행되는 NestJS API server
- Angular가 pipeline 실행 전에 필요한 app/business/API성 작업을 요청하는 backend
- dance artist detection, member resolve, image search 같은 pre-pipeline 작업 담당
- 향후 LLM proxy, subscription/auth/billing, plugin catalog/registry bridge가 들어갈 수 있는 위치

현재 `clipper_nestjs`가 아닌 것:

- 모든 Angular 요청을 통과시키는 단일 backend는 아님
- Python `/jobs` traffic의 필수 proxy는 아님
- plugin process lifecycle owner가 아님
- model/ffmpeg 설치 관리자도 아님

따라서 앞으로 문서에서는 `local gateway`라는 표현을 쓸 때 의미를 명시하는 것이 좋다. "Python pipeline 앞단 gateway"가 아니라 "로컬 앱 API gateway"에 가깝다.

## 5. 현재 주요 실행 흐름

### 5.1 앱 부팅

1. Electron main process가 시작된다.
2. packaged/dev 환경에 맞게 Angular asset 경로를 결정한다.
3. NestJS local app API를 `utilityProcess.fork` 또는 개발용 프로세스로 실행한다.
4. NestJS health를 확인하고 backend URL을 preload API로 노출한다.
5. Angular SPA가 로드된다.
6. Python plugin은 앱 부팅 시 모두 띄우기보다, 기능 진입 또는 job 시작 시 필요에 따라 준비되는 흐름이다.

### 5.2 Dance pre-pipeline

1. Angular가 BackendLocator로 NestJS URL을 얻는다.
2. artist detection, member lookup, image search 같은 pre-pipeline 요청을 NestJS로 보낸다.
3. NestJS는 로컬 JSON, Wikipedia/Wikidata, Naver/Kakao API를 조합한다.
4. Angular는 선택된 멤버와 reference image를 dance plugin job input으로 넘긴다.

### 5.3 Python plugin job

1. Angular가 PluginLocator/Electron preload를 통해 plugin URL을 얻는다.
2. Electron은 해당 plugin process가 없으면 `uv run`으로 실행한다.
3. Angular가 Python plugin에 `POST /jobs`를 호출한다.
4. Angular가 WebSocket으로 progress를 구독한다.
5. plugin runtime은 model loading, pipeline progress, completion/error를 이벤트로 보낸다.
6. 취소는 `DELETE /jobs/{id}` 흐름으로 처리한다.

### 5.4 모델/ffmpeg 설치

1. Angular가 필요한 runtime asset 상태를 확인한다.
2. 사용자 동의 overlay를 보여준다.
3. Electron IPC가 ffmpeg 또는 plugin model download를 시작한다.
4. Electron은 stderr/stdout/파일 상태를 파싱해 byte-level progress를 보낸다.
5. 설치 완료 후 marker와 실제 파일 존재를 확인한다.
6. 이후 plugin health/model load 단계로 넘어간다.

## 6. 현재까지 완료된 것

### 6.1 아키텍처

- 레거시 `adlight_*` 혼합 구조에서 `clipper_*` 4분할 구조로 전환
- 플러그인을 배포/런타임/의존성 격리 단위로 정의
- PyInstaller 중심 전략 폐기
- HTTP + WebSocket loopback IPC 결정
- idle-kill, cancellation, OOM/crash 대응 방향 정리
- NestJS Option C 확정: Python으로 흡수하지 않고 로컬 앱 API 프로세스로 유지

### 6.2 `clipper_python`

- Plugin SDK와 runtime 기본 구조 구현
- `dialog_highlight`, `dance_highlight` 포팅
- PyInstaller, `sys._MEIPASS`, legacy app path 의존 제거 진행
- unit test, E2E smoke, OOM subprocess test 추가
- dialog pipeline sample E2E 확인
- dance pipeline E2E는 동작하나 reference image 품질 검증 이슈가 남음
- model loading event와 eager load 개선

### 6.3 `clipper_angular`

- Angular 19 standalone/zoneless SPA 생성
- feature registry와 PluginLocator 도입
- dance/dialog UI 포팅
- Electron native file picker fallback
- job/progress 상태 관리
- model/ffmpeg consent overlay와 progress UI
- BackendLocator와 dynamic NestJS URL 연동
- Clipper2 rename 반영

### 6.4 `clipper_electron`

- 새 Electron shell 생성
- preload bridge, PluginManager, ProcessManager, PortAllocator, ManifestLoader 구현
- Python plugin `uv run` spawn
- packaged app build 흐름 정리
- first-run `uv sync`와 source bundle 방식 정리
- ffmpeg/model download IPC와 로그 개선
- NestJS utility process 실행과 backend URL IPC 추가
- Mac arm64 packaged build 흐름 확인

### 6.5 `clipper_nestjs`

- 새 NestJS local app API 생성
- dance pre-pipeline API 구현
- artist/member/image search 흐름 구현
- QID 관련 버그 수정
- Electron packaged resource로 포함하는 방향 확정
- `NEST_DATA_DIR`, CORS `null`, `127.0.0.1`, dynamic port 기준 정리

## 7. 아직 남은 일

현재 문서들 기준으로 남은 일은 다음 순서가 자연스럽다.

1. packaged app에서 NestJS 포함 빌드 재검증
2. Dance artist/member/image pre-pipeline E2E 재검증
3. ffmpeg/model download overlay의 실제 화면 검증
4. plugin store/dashboard 구현
5. resource monitoring과 plugin crash restart 정책 구현
6. LLM proxy와 subscription/auth/billing 연동
7. plugin registry/CDN/model CDN 설계 및 구현
8. Windows packaged build 검증
9. Mac code signing/notarization/auto-updater
10. 앱 icon/branding 마무리
11. dance reference image 품질과 결과 품질 재검증
12. first-run `uv sync` 진행률 UI 개선

보안/운영 관점에서 가장 중요한 미완료 항목은 LLM proxy다. 문서상 `.env`에 OpenAI 또는 외부 API key를 직접 넣는 방식은 비용과 키 유출 위험이 있으므로 장기 운영 구조로는 부적합하다고 이미 결론이 나 있다.

## 8. 현재 기준으로 폐기되었거나 주의해야 할 문서

### 8.1 `plugin_ipc_design_2026-04-14.md`

stdio JSON-RPC를 전제로 한 설계가 들어 있지만, 이후 재논의에서 현재 기준 IPC는 HTTP + WebSocket over loopback으로 정리되었다. 이 문서는 "당시 검토안"으로만 봐야 한다.

### 8.2 Option A 관련 기록

2026-04-22 전후 일부 `clipper_python`, `clipper_nestjs` WORKLOG에는 NestJS route를 Python plugin으로 옮기는 Option A 흐름이 남아 있다. 이후 2026-04-27 기준으로 Option C가 최종 기준이다.

현재 기준:

- NestJS는 로컬 앱 API로 유지
- Electron이 NestJS를 실행하고 URL을 Angular에 전달
- Dance pre-pipeline은 NestJS
- 실제 heavy pipeline job은 Python plugin

### 8.3 Angular와 Python 직접 통신 여부

일부 루트 런타임 문서는 Angular가 Python에 직접 연결하지 않는다는 표현을 포함할 수 있다. 그러나 현재 구현 흐름을 정확히 쓰면 다음이 맞다.

- Angular는 Electron preload를 통해 plugin URL을 얻는다.
- job API와 WebSocket progress는 Angular가 Python plugin endpoint에 직접 호출한다.
- Electron은 process manager와 URL provider 역할을 한다.

따라서 "Angular가 Python process lifecycle을 직접 관리하지 않는다"는 말은 맞지만, "Angular가 Python HTTP/WS endpoint를 전혀 호출하지 않는다"는 말은 현재 구조와 맞지 않을 수 있다.

### 8.4 `adlight_nestjs/README.md`

NestJS 기본 스타터 문서에 가까워 프로젝트 변천사에서 의미 있는 설계 기록으로 보기는 어렵다. 현재 `clipper_nestjs`와 직접 이어지는 구현 문서로 취급하면 안 된다.

### 8.5 OpenAI 모델 레퍼런스 문서

`adlight_python/docs/highlight/2026-03-17_openai_models_reference.md`는 작성 당시 참고자료다. 모델명, 가격, 지원 여부는 시간에 따라 바뀌므로 현재 의사결정에는 최신 공식 문서 확인이 필요하다.

## 9. 앞으로 문서화할 때의 권장 구조

앞으로는 문서를 여기저기 추가하기보다 다음 계층을 유지하는 것이 좋다.

- 루트 `.claude`: 현재 상태, 다음 세션 프롬프트, 전체 아키텍처, 빌드/런타임 가이드
- 각 `clipper_*`의 `.claude`: 해당 repo의 구현 상세, 결정 기록, TODO, WORKLOG
- `.codex`: Claude 문서들을 재검토해 정리한 통합본, 설계 리뷰, 누락/모호점 보완 문서

문서마다 상단에 다음 필드를 두면 추적이 쉬워진다.

```md
Status: current | historical | superseded
Last verified: YYYY-MM-DD
Supersedes:
Superseded by:
Applies to:
```

특히 Option A/Option C처럼 같은 주제의 결정이 바뀐 경우, 과거 문서를 지우기보다 `Status: superseded`와 `Superseded by`를 명시하는 편이 안전하다.

## 10. Codex 기준 보완 설계

문서를 전체적으로 읽었을 때 빠져 있거나 모호했던 부분을 현재 기준으로 보완하면 다음과 같다.

### 10.1 제품 경계

현재 제품 경계는 다음처럼 보는 것이 가장 일관된다.

- Clipper2 desktop app: Electron + Angular + local runtime manager
- Local app API / local gateway: NestJS
- Compute plugins: Python plugin processes
- Remote server: login, subscription, billing, entitlement, LLM proxy, update/plugin metadata처럼 로컬에 둘 수 없는 기능

즉 `clipper_nestjs`와 remote server를 혼동하면 안 된다. 현재 `clipper_nestjs`는 사용자 PC 안에서 Electron이 실행하는 로컬 NestJS 서버다. 설치형 앱 내부에서 처리할 수 있는 사전 처리, 로컬 API, 외부 API proxy/cache 성격의 기능은 `clipper_nestjs`가 맡을 수 있다. 반대로 로그인, 이용권/구독 검증, 결제, 사용자별 권한, LLM API key 보호처럼 로컬에 두면 안 되거나 중앙 검증이 필요한 기능은 별도의 remote server와 HTTP 통신으로 처리해야 한다. 또한 현재 `clipper_nestjs`는 Python plugin `/jobs` 호출의 필수 중계자가 아니다.

### 10.2 Plugin 설치 단위

현재 packaged implementation은 단일 `clipper_venv`에 가깝고, 문서상 장기 방향은 per-plugin/two-tier venv다. 이 둘을 다음처럼 명확히 나누는 것이 좋다.

- Now: bundled plugins + single app-managed venv + app resources
- Next: SDK/base venv + plugin-specific dependency layer
- Later: remote plugin registry + signed plugin package + per-plugin update channel

이렇게 쓰면 현재 구현과 장기 설계가 충돌하지 않는다.

### 10.3 Store/Dashboard의 위치

플러그인 스토어/대시보드는 아직 구현 전 설계 단계다. 현재 architecture에서 위치는 다음과 같다.

- Angular: store/dashboard UI와 user action
- Electron: install/uninstall/enable/disable, local filesystem, process control
- NestJS local app API: catalog cache/proxy가 필요하면 담당 가능
- Remote server: canonical catalog, entitlement, billing/subscription
- Python plugin: 설치 후 runtime health/job만 제공

스토어가 Python plugin runtime 안으로 들어가면 안 된다. 설치와 권한, 버전, 서명 검증은 runtime보다 바깥 계층의 책임이다.

### 10.4 Runtime 상태 모델

현재 문서들에는 install, download, health, model load, job state가 흩어져 있다. 통합 상태 모델은 다음처럼 나누는 것이 좋다.

- Install state: not_installed, installing, installed, update_available, install_failed
- Runtime state: stopped, starting, healthy, unhealthy, stopping, crashed
- Asset state: missing, downloading, ready, corrupted
- Model state: not_loaded, loading, ready, failed
- Job state: queued, running, cancelling, cancelled, completed, failed

이 다섯 층을 분리해야 UI와 Electron process manager, Python runtime event가 서로 덜 꼬인다.

### 10.5 로그와 디버깅 기준

현재 로그 위치는 문서화되어 있으나, 문제 재현에 필요한 bundle ID와 session/job/plugin 식별자를 통합하는 규칙은 더 명확히 필요하다.

권장 필드:

- `appVersion`
- `platform`
- `pluginId`
- `pluginVersion`
- `jobId`
- `runtimePort`
- `backendPort`
- `installSessionId`
- `modelId`
- `eventType`

이 필드가 Angular event, Electron log, Python plugin log, NestJS log에 공통으로 찍히면 packaged app 디버깅이 훨씬 쉬워진다.

## 11. 최종 현재 상태

현재 프로젝트는 "레거시 기능을 새 플러그인 아키텍처로 옮기는 중"이 아니라, 이미 새 아키텍처의 골격은 세워졌고 주요 파이프라인도 동작하는 단계다. 남은 핵심은 packaged 환경에서의 안정성 검증, store/dashboard, resource/crash 정책, Windows 배포, 원격 서비스 연동이다.

현재 기준 canonical 구조는 다음이다.

```text
clipper_angular
  UI, feature registry, locator, job/progress UX

clipper_electron
  desktop shell, process manager, model/ffmpeg installer, packaging

clipper_nestjs
  local app API, dance pre-pipeline, future LLM/auth/catalog bridge

clipper_python
  plugin SDK, dialog/dance compute plugins, job runtime
```

레거시 `adlight_*` 문서들은 기능과 문제 해결의 중요한 히스토리지만, 구현 기준으로는 `clipper_*`와 루트 `.claude` 최신 문서가 우선이다.

## 부록 A. 읽은 문서 인벤토리

루트 `.claude`:

- `.claude/ARCHITECTURE_REVIEW.md`
- `.claude/BUILD_GUIDE.md`
- `.claude/CLAUDE.md`
- `.claude/NEXT_SESSION_PROMPT.md`
- `.claude/PLUGIN_RUNTIME_GUIDE.md`
- `.claude/PLUGIN_STORE_DASHBOARD_DESIGN.md`
- `.claude/TASK.md`
- `.claude/WORKLOG.md`

`adlight_angular`:

- `adlight_angular/CHANGELOG.md`
- `adlight_angular/CLAUDE.md`
- `adlight_angular/README.md`
- `adlight_angular/TASK.md`
- `adlight_angular/WORKLOG.md`
- `adlight_angular/docs/clipper/2026-04-03_feat-library-status-polling.md`
- `adlight_angular/docs/clipper/admin-login-troubleshooting.md`
- `adlight_angular/docs/clipper/clipper-project-overview.md`
- `adlight_angular/docs/clipper/super-clone-feature-plan.md`
- `adlight_angular/docs/clipper/super-clone-implementation.md`
- `adlight_angular/docs/highlight/2026-03-17_project-strip-bugfix.md`
- `adlight_angular/docs/highlight/2026-03-18_highlight-mac-build-deploy-setup.md`
- `adlight_angular/docs/highlight/2026-03-18_highlightstudio-mac-build-deploy-guide.md`
- `adlight_angular/docs/highlight/2026-03-18_highlightstudio-windows-build-deploy-guide.md`
- `adlight_angular/docs/highlight/2026-03-19_c10dll-winerror1114-fix.md`
- `adlight_angular/docs/highlight/2026-03-26_issue-nsis-web-payload-version-mismatch.md`
- `adlight_angular/docs/highlight/2026-03-26_issue-port-9028-docker-wsl2.md`

`adlight_python`:

- `adlight_python/CLAUDE.md`
- `adlight_python/NEXT_SESSION_PROMPT.md`
- `adlight_python/README.md`
- `adlight_python/TASK.md`
- `adlight_python/WORKLOG.md`
- `adlight_python/docs/architecture_discussion_2026-04-13.md`
- `adlight_python/docs/plugin_architecture_design_2026-04-14.md`
- `adlight_python/docs/plugin_cancel_heartbeat_crash_2026-04-16.md`
- `adlight_python/docs/plugin_ipc_design_2026-04-14.md`
- `adlight_python/docs/plugin_ipc_rediscussion_2026-04-14.md`
- `adlight_python/docs/plugin_lifetime_discussion_2026-04-14.md`
- `adlight_python/docs/super_clone_code_issues.md`
- `adlight_python/docs/clipper/2026-04-03_fix-sse-session-id-targeting.md`
- `adlight_python/docs/clipper/2026-04-06_sse-vs-websocket-decision.md`
- `adlight_python/docs/clipper/clipper-project-overview.md`
- `adlight_python/docs/clipper/super-clone-feature-plan.md`
- `adlight_python/docs/highlight/2026-03-16_bugfix_clip_title_mismatch.md`
- `adlight_python/docs/highlight/2026-03-16_pipeline_clip_stt_and_title_bugfix.md`
- `adlight_python/docs/highlight/2026-03-16_pipeline_gpt_batching.md`
- `adlight_python/docs/highlight/2026-03-17_dance-pipeline-gpu-acceleration-applied.md`
- `adlight_python/docs/highlight/2026-03-17_dance-pipeline-gpu-acceleration.md`
- `adlight_python/docs/highlight/2026-03-17_dance-pipeline-review.md`
- `adlight_python/docs/highlight/2026-03-17_dance-pipeline-sse-progress.md`
- `adlight_python/docs/highlight/2026-03-17_gpt_calls_analysis.md`
- `adlight_python/docs/highlight/2026-03-17_longform_highlight_pipeline_analysis.md`
- `adlight_python/docs/highlight/2026-03-17_member-image-search.md`
- `adlight_python/docs/highlight/2026-03-17_openai_models_reference.md`
- `adlight_python/docs/highlight/2026-03-17_pipeline_improvements.md`
- `adlight_python/docs/highlight/2026-03-20_torchvision-has-ops-false-fix.md`
- `adlight_python/docs/highlight/2026-03-23_cuda-windows-setup-guide.md`
- `adlight_python/docs/highlight/2026-03-23_pipeline-gpu-bottleneck-analysis.md`
- `adlight_python/docs/highlight/2026-03-24_cuda-deploy-automation.md`
- `adlight_python/docs/highlight/2026-03-24_dance-pipeline-optimization-roadmap.md`
- `adlight_python/docs/highlight/2026-03-24_issue-av1-libdav1d-crash-ffmpeg.md`
- `adlight_python/docs/highlight/2026-03-24_issue-av1-libdav1d-crash-opencv.md`
- `adlight_python/docs/highlight/2026-03-24_issue-cuda-build-nsis-size-limit.md`
- `adlight_python/docs/highlight/2026-03-24_issue-cv2-unicode-path.md`
- `adlight_python/docs/highlight/2026-03-24_issue-dll-loading-loadlibraryexw.md`
- `adlight_python/docs/highlight/2026-03-24_issue-face-extract-22min-bottleneck.md`
- `adlight_python/docs/highlight/2026-03-24_issue-ffmpeg-frozen-path-bug.md`
- `adlight_python/docs/highlight/2026-03-24_issue-insightface-yolo-cuda-conflict.md`
- `adlight_python/docs/highlight/2026-03-24_issue-openmp-kmp-duplicate.md`
- `adlight_python/docs/highlight/2026-03-24_issue-pyinstaller-collect-all-cuda.md`
- `adlight_python/docs/highlight/2026-03-24_issue-torch-bundle-cleanup.md`
- `adlight_python/docs/highlight/2026-03-24_issue-torch-cuda-not-available-frozen.md`
- `adlight_python/docs/highlight/2026-03-24_issue-torchvision-has-ops-false.md`
- `adlight_python/docs/highlight/2026-03-24_issue-vcruntime-dll-conflict.md`
- `adlight_python/docs/highlight/2026-03-24_issue-yolo-fp16-crash-frozen.md`
- `adlight_python/docs/highlight/2026-03-24_milestone-timeline.md`
- `adlight_python/docs/highlight/2026-03-24_windows-build-publish-workflow.md`
- `adlight_python/docs/highlight/2026-03-24_windows-cuda-build-journey.md`
- `adlight_python/docs/highlight/2026-03-24_windows-remaining-tasks.md`
- `adlight_python/docs/highlight/2026-03-25_issue-onnxruntime-gpu-frozen-build.md`
- `adlight_python/docs/highlight/2026-04-07_pyinstaller-onefile-vs-onedir.md`

`adlight_nestjs`:

- `adlight_nestjs/README.md`

`clipper_angular`:

- `clipper_angular/.claude/CLAUDE.md`
- `clipper_angular/.claude/DESIGN_DECISIONS.md`
- `clipper_angular/.claude/TASK.md`
- `clipper_angular/.claude/WORKLOG.md`
- `clipper_angular/README.md`

`clipper_python`:

- `clipper_python/.claude/CLAUDE.md`
- `clipper_python/.claude/DESIGN_DECISIONS.md`
- `clipper_python/.claude/NEXT_SESSION_PROMPT.md`
- `clipper_python/.claude/TASK.md`
- `clipper_python/.claude/WORKLOG.md`

`clipper_nestjs`:

- `clipper_nestjs/.claude/CLAUDE.md`
- `clipper_nestjs/.claude/TASK.md`
- `clipper_nestjs/.claude/WORKLOG.md`

`clipper_electron`:

- `clipper_electron/.claude/CLAUDE.md`
- `clipper_electron/.claude/PLUGIN_INSTALL_FLOW.md`
- `clipper_electron/.claude/TASK.md`
- `clipper_electron/.claude/WORKLOG.md`
