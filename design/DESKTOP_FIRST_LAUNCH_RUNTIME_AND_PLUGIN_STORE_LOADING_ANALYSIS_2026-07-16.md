# 데스크톱 첫 실행 Runtime 준비와 Plugin Store 장기 로딩 분석

작성일: 2026-07-16  
상태: 코드 기준 분석 완료, 저사양 Windows packaged 재현·개선은 보류  
관련 TODO: `.codex/todos/2026-07-16-desktop-first-launch-runtime-and-plugin-store-loading.md`

## 문제 제기

패키지 앱을 새로 설치한 뒤 첫 실행하면 관리 Python, base venv, `yt-dlp`와 EJS package 준비가 오래 걸릴 수 있다. 특히 성능이 낮은 Windows PC, 느린 디스크, 느린 네트워크 또는 실시간 백신 검사가 강한 환경에서는 사용자가 앱이 멈췄다고 느낄 가능성이 있다.

별도로 사용자가 Plugin Store에서 평소 빠르게 사라지는 `불러오는 중…` 문구가 오랫동안 남고 앱 전체도 정상적이지 않은 것처럼 느껴진 사례를 보고했다.

이 문서는 두 현상이 같은 작업에서 발생하는지 현재 코드 기준으로 구분하고, 추후 재현·개선 작업의 출발점을 남긴다.

## 먼저 내린 결론

현재 코드에서는 base Python runtime 준비가 메인 UI 뒤에서 계속되는 백그라운드 작업이 아니다.

```text
Electron app.whenReady
  → bootstrap
  → packaged runtime이면 preparePackagedYoutubeRuntime()
  → ensureVenv() 완료 대기
     ├─ 관리 Python 3.11 확인/설치
     ├─ base venv 생성 또는 복구
     ├─ yt-dlp[default] 설치
     └─ Python/yt-dlp/EJS 실행 검증
  → plugin host와 IPC 등록
  → openMainWindow()
  → Angular UI 표시
```

따라서 base runtime 설치가 오래 걸리는 동안에는 정상 Angular UI를 먼저 사용할 수 없다. 현재는 설치 진행을 보여주는 별도 first-run 창이나 splash도 없으므로, 저사양 환경에서는 창이 늦게 나타나거나 앱이 멈춘 것처럼 보일 수 있다.

반면 UI가 이미 표시된 뒤 Plugin Store의 `불러오는 중…`이 오래 남는 직접 대기 경로는 다음과 같다.

```text
Angular PluginStatusService.refreshAll()
  → BackendLocator.getBaseUrl()
  → Electron IPC
  → NestManager.ensureStarted()
     ├─ base runtime preflight 재확인
     ├─ NestJS utility process 시작
     └─ /v1/health 최대 30초 대기
  → GET /v1/plugins
     ├─ workflow/plugin manifest 탐색
     ├─ plugin install/runtime status 확인
     ├─ host resource snapshot 수집
     ├─ GPU/process 정보 조회
     └─ 일부 model/cache 파일 존재 확인
  → Angular items 갱신
  → loading=false
```

즉 다음처럼 구분해야 한다.

| 사용자가 보는 현상 | 현재 코드에서 가능성이 큰 대기 지점 |
|---|---|
| 실행 후 메인 창 자체가 오랫동안 나타나지 않음 | 관리 Python/base venv/yt-dlp/EJS 준비 |
| UI는 나타났지만 Plugin Store가 계속 `불러오는 중…` | NestJS 최초 기동 또는 `/v1/plugins` 내부 작업 |
| 특정 플러그인 설치·시작 뒤 오래 걸림 | plugin별 venv `uv sync`, model download 또는 plugin health 대기 |
| UI 전체가 버벅임 | CPU·디스크·네트워크·백신 검사 등 자원 경합 가능성 |

사용자가 겪은 전체적인 첫 실행 지연에는 runtime 설치가 영향을 줬을 수 있다. 그러나 UI가 보인 뒤 Plugin Store placeholder가 오래 남은 직접 원인을 “base venv가 UI 뒤에서 계속 설치됐기 때문”이라고 보기는 어렵다. 현재 코드에서는 base runtime이 준비된 뒤에야 메인 창을 열기 때문이다.

## 현재 구현에서 확인한 경계

### 1. Base runtime은 앱 진입 전 필수 hard gate다

`desktop/clipper_electron/src/main/main.ts`의 packaged bootstrap은 `preparePackagedYoutubeRuntime()`을 `await`한 뒤에만 `openMainWindow()`로 진행한다.

`desktop/clipper_electron/src/main/setup/first-run.ts`의 첫 실행 작업은 다음을 포함한다.

- 앱 내장 `uv`를 통한 관리 Python 3.11 설치
- app-owned base venv 생성 또는 호환되지 않는 venv 복구
- `yt-dlp[default]>=2025.12.8` binary package 설치
- Python, yt-dlp와 EJS runtime 실행 검증
- 모든 검증 성공 후 marker 기록

준비에 실패하면 현재 제품 정책은 `다시 시도` 또는 `앱 종료`만 허용한다. `로컬 파일로 계속` 분기는 2026-07-14 작업에서 제거됐다.

### 2. 무거운 plugin dependency는 첫 실행에서 전부 설치하지 않는다

첫 실행 base venv는 Python 전체 workspace 또는 모든 plugin dependency를 설치하지 않는다.

Python plugin별 dependency는 실제 plugin 시작 시 `desktop/clipper_electron/src/main/plugin/plugin-venv.ts`의 `ensurePluginVenv()`가 plugin 전용 venv에 `uv sync --package ...`를 수행한다.

이 작업은 UI가 열린 뒤 특정 plugin을 설치·시작할 때 발생한다. 해당 plugin은 완료될 때까지 사용할 수 없지만, 앱 전체의 최초 창 표시를 막는 base bootstrap과는 다른 단계다.

### 3. NestJS는 Angular의 첫 backend URL 요청 때 지연 시작된다

메인 창이 열린 시점에 NestJS가 이미 healthy인 것은 아니다.

Angular가 `BackendLocator.getBaseUrl()`을 호출하면 Electron IPC가 `NestManager.ensureStarted()`를 실행한다. NestJS utility process를 시작하고 `/v1/health`가 성공할 때까지 기다린 뒤 base URL을 반환한다. health 대기 제한은 현재 30초다.

Plugin Store의 첫 `refreshAll()`은 이 전체 시간을 `loading=true` 상태로 기다린다.

### 4. Plugin 목록 API는 단순 catalog read보다 많은 일을 한다

NestJS의 `GET /v1/plugins`는 manifest 문자열만 반환하지 않는다.

- workflow executor 목록 구성
- 각 executor manifest/status 조회
- Python plugin install/runtime 상태 조회
- host resource snapshot 조회
- plugin resource assessment 계산
- lifecycle/runtime diagnostics 결합

packaged 환경의 host resource snapshot은 Electron bridge를 통해 운영체제 정보를 수집한다. Windows에서는 PowerShell 기반 process/GPU 조회가 포함될 수 있고, plugin install 상태 확인은 model/cache 파일 탐색을 포함할 수 있다.

이 항목들은 모두 실제 지연 후보지만, 사용자가 겪은 특정 사례의 확정 원인으로 아직 측정한 것은 아니다.

### 5. Angular가 같은 refresh를 중복 시작할 수 있다

현재 `PluginStatusService.refreshAll()`은 다음 경로에서 호출된다.

- app initializer
- Plugin Store `ngOnInit`
- Dashboard `ngOnInit`과 3초 polling
- 일부 route guard/registry 경로

서비스에는 동일 시점의 refresh를 하나의 Promise로 합치는 single-flight 제어가 없다. 앱 초기화 직후 Store 또는 Dashboard에 진입하면 같은 목록 요청이 겹칠 가능성이 있다.

각 호출은 같은 global `loading` signal을 직접 true/false로 바꾸므로, 겹친 요청의 완료 순서가 UI 상태와 최신 결과를 이해하기 어렵게 만들 수도 있다.

### 6. Plugin 목록 요청에는 명시적인 UI timeout과 단계별 상태가 없다

Angular의 `refreshAll()`은 backend URL 조회와 `GET /plugins`가 끝날 때까지 동일한 `불러오는 중…`만 표시한다.

현재 UI만으로는 다음을 구분할 수 없다.

- 필수 runtime 준비
- 로컬 API 시작
- plugin 목록 조회
- 시스템 사양 확인
- model/install 상태 확인
- 실제 실패 또는 장기 hang

HTTP 요청에도 이 화면 전용 timeout이 없으므로 하위 요청이 반환되지 않으면 placeholder가 장시간 유지될 수 있다.

## 기존 로컬 로그에서 확인한 정상 순서

2026-07-14~15의 준비된 macOS userData 실행 로그에서는 대체로 다음 순서가 확인됐다.

```text
youtube.runtime.check.started
  → 약 0.1~0.3초
youtube.runtime.check.ready
  → 약 0.2초 안팎
[window] showing main window
  → 약 0.4~0.5초
[NestManager] ready
```

이는 이미 준비된 runtime의 warm launch 관찰이며, 저사양 Windows clean install 성능을 대표하지 않는다. 첫 Python 다운로드, 느린 package registry, Windows Defender 검사 또는 느린 HDD가 포함된 기준값은 아직 없다.

## 아직 확정하지 않은 원인

다음은 가능성이 있으나 계측 전에는 원인으로 단정하지 않는다.

- 관리 Python 다운로드 또는 package 설치가 느린 네트워크에 묶인 경우
- Windows Defender가 새 Python executable, wheel과 venv 파일을 검사하는 경우
- NestJS utility process cold start가 느린 경우
- PowerShell/CIM 기반 GPU·process 조회가 느리거나 불안정한 경우
- Hugging Face/model cache의 동기식 파일 탐색이 느린 디스크에서 오래 걸리는 경우
- app initializer, Store와 Dashboard의 `refreshAll()`이 겹친 경우
- backend 또는 `/plugins` 요청이 종료되지 않고 명시적 timeout도 없는 경우
- 첫 실행 직후 auto-update, 인증 복원 등 다른 startup 작업과 자원 경합이 생긴 경우

## 개선 방향

### 공통으로 먼저 필요한 것: 단계별 계측

UX나 구조를 바꾸기 전에 다음 구간을 같은 startup attempt id로 측정해야 한다.

```text
Electron
  runtime inspect start/end
  managed Python install start/end
  venv create start/end
  package install start/end
  main window create/show
  Nest ensureStarted start/process spawned/health ready

Angular
  refreshAll request id/start/end
  backend URL wait
  /plugins HTTP wait
  overlapping caller count

NestJS
  /plugins total
  executor registry
  host resource snapshot
  manifest/status
  resource assessment
```

로그에는 cookie, env 값, JWT, provider secret, Authorization, 사용자 입력 URL 또는 민감한 로컬 파일 내용을 남기지 않는다.

### Base runtime UX

현재 hard gate를 유지한다면 메인 Angular UI와 별개인 first-run 준비 화면이 필요하다.

```text
앱 시작
  → 작은 native/splash 준비 화면 즉시 표시
  → "필수 구성 요소 확인"
  → "Python runtime 준비"
  → "영상 도구 준비"
  → 완료 후 메인 창 전환
```

필요한 상태:

- 현재 단계
- 다운로드/설치 중이라는 명시
- 장시간 소요 가능성 안내
- 실패 원인의 안전한 범주
- 다시 시도
- 앱 종료

base runtime을 진짜 백그라운드로 돌리고 Angular UI를 먼저 여는 대안도 가능하지만, 이는 YouTube runtime을 앱 전체 필수 구성 요소로 취급하는 현재 제품 결정을 바꾸는 작업이다. 이 대안을 채택하려면 runtime 미준비 상태에서 어떤 화면과 기능을 허용할지 별도 제품 설계가 필요하다.

### Plugin Store 초기 로딩 경량화

우선 검토할 최소 변경 후보:

1. `PluginStatusService.refreshAll()`을 single-flight로 만들어 중복 요청을 합친다.
2. app initializer와 Store/Dashboard 중 목록 최초 로드의 단일 owner를 정한다.
3. Plugin catalog 응답에서 host resource assessment와 무거운 파일 탐색을 분리하거나 지연 로드한다.
4. NestJS를 창 표시 직후 명시적으로 warm-up하되 UI를 막지는 않게 할지 비교한다.
5. `runtime 준비 → 로컬 API 시작 → plugin 목록 조회` 상태를 UI에서 구분한다.
6. 각 단계에 합리적인 timeout, 오류 화면과 재시도 동작을 둔다.
7. 마지막 성공 목록을 안전하게 cache할 수 있는지 검토하되 stale install/runtime 상태를 현재 상태처럼 표시하지 않는다.

## 재현 매트릭스

| 환경 | userData | 네트워크 | 확인 목적 |
|---|---|---|---|
| Windows 저사양 실기기 | clean | 정상 | 실제 first-run 기준값 |
| Windows 저사양 실기기 | warm | 정상 | 두 번째 실행 회귀 여부 |
| Windows 저사양 실기기 | clean | 느림/불안정 | 다운로드·timeout·재시도 |
| Windows 저사양 실기기 | clean | offline | 실패 UX와 부분 설치 복구 |
| Windows Defender | 기본/강화 | 정상 | venv 파일 검사 영향 |
| macOS 지원 기기 | clean/warm | 정상 | 플랫폼 간 순서·기능 동일성 |

앱 실행이나 userData 초기화는 사용자의 명시 요청을 받은 QA 세션에서만 수행한다.

## 완료 조건

구현을 시작할 때 수치 목표는 측정된 baseline을 바탕으로 확정한다. 최소 제품 완료 조건은 다음과 같다.

- 첫 실행 준비 중 사용자가 앱이 죽었는지 판단하지 못하는 무창·무상태 구간이 없다.
- base runtime 단계와 Plugin Store/NestJS 단계가 서로 다른 상태로 표시된다.
- optional plugin dependency 설치는 앱 최초 진입을 막지 않는다.
- 동일 시점 Plugin Store refresh는 하나로 합쳐진다.
- plugin catalog의 필수 응답 경로에서 불필요한 host diagnostics가 분리된다.
- 장기 지연과 실패에 timeout, 원인 범주, 재시도 동작이 있다.
- warm launch에서는 Python/package 재설치가 반복되지 않는다.
- clean/warm/offline/부분 설치 복구를 Windows packaged 환경에서 검증한다.
- 실제 cookie, env 값, JWT key, provider secret을 로그·문서·fixture에 포함하지 않는다.

## 비범위

- 이 문서 작성 시점에는 Electron, Angular, NestJS 또는 Python 코드를 수정하지 않는다.
- runtime hard gate 유지/완화 제품 결정은 확정하지 않는다.
- 임의의 성능 목표 숫자를 측정 없이 확정하지 않는다.
- 앱 실행, packaged build, userData 초기화, 배포를 수행하지 않는다.

## 주요 코드 위치

- `desktop/clipper_electron/src/main/main.ts`
- `desktop/clipper_electron/src/main/setup/first-run.ts`
- `desktop/clipper_electron/src/main/backend/backend-ipc.ts`
- `desktop/clipper_electron/src/main/backend/nest-manager.ts`
- `desktop/clipper_electron/src/main/plugin/plugin-venv.ts`
- `desktop/clipper_electron/src/main/backend/plugin-host-bridge.ts`
- `desktop/clipper_angular/src/core/plugins/plugin-status.service.ts`
- `desktop/clipper_angular/src/app/app.config.ts`
- `desktop/clipper_angular/src/shell/store/store/store.component.ts`
- `desktop/clipper_nestjs/src/modules/plugins/application/plugins.service.ts`
- `desktop/clipper_nestjs/src/modules/workflows/application/workflow-executor-registry.service.ts`
- `desktop/clipper_nestjs/src/modules/resources/infrastructure/electron-resource-host.service.ts`

