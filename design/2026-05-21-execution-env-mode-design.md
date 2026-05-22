# Clipper2 실행 모드와 환경변수 관리 설계

작성일: 2026-05-21

## 목적

Clipper2는 Angular, Electron, NestJS, Python plugin 런타임이 분리된 다중 프로세스 앱이다. 현재는 설치형 Electron 앱 빌드를 중심으로 검증되어 왔고, 로컬 개발 실행과 개발용 Electron 앱 실행은 일부 가능하지만 명령어, env 파일, 포트, 플러그인 실행 책임이 명확하게 정리되어 있지 않다.

이 문서는 구현 전 기준을 맞추기 위한 실행 모드, env 파일, 포트 할당, 플러그인 런타임 책임의 설계 초안이다.

## 현재 문제

### `.env.local` 의미가 흐려져 있다

팀 관습상 `.env.local`은 "localhost 개발 실행용"이다. 개인 PC override 파일이 아니다.

현재 NestJS는 여러 경로의 `.env.local`과 `.env`를 넓게 자동 탐색한다. 이 방식은 설치형 앱 또는 다른 실행 모드에서 `.env.local`이 섞여 들어갈 수 있어 위험하다.

### 실행 모드가 명령어와 env에서 일관되지 않다

Angular에는 `start:local`, `start:electron` 계열이 있지만 NestJS/Electron/Python까지 같은 기준으로 정리되어 있지 않다.

Electron 개발 실행은 일부 가능하다. `clipper_electron npm run start:dev`는 패키징 없이 Electron 창을 띄우고 Angular dev server를 로드한다. 하지만 Angular, NestJS, Python plugin을 같이 띄우지 않고, URL과 포트 가정이 코드에 고정되어 있다.

### 플러그인 포트가 확장 가능하지 않다

현재 플러그인이 적을 때는 dialog, dance, render처럼 플러그인별 고정 포트를 둘 수 있다. 하지만 플러그인이 수십 개로 늘어나면 env에 플러그인별 포트를 나열하는 방식은 유지보수할 수 없다.

플러그인 포트는 플러그인별 고정값이 아니라 실행 모드별 포트 풀에서 런타임이 동적으로 할당해야 한다.

## 실행 모드

확정할 모드 이름은 다음 3개다.

```text
local
devapp
packaged
```

### `local`

브라우저 기반 로컬 개발 모드다.

예상 실행 형태:

```text
Angular dev server
NestJS dev server
Python plugin processes
Browser
```

브라우저가 Angular dev server에 직접 접속한다. Angular는 NestJS API만 호출하고, Python plugin 주소를 직접 알지 않는다.

### `devapp`

패키징하지 않은 개발용 Electron 앱 모드다.

예상 실행 형태:

```text
Angular dev server
NestJS dev server
Python plugin processes
Electron desktop shell
```

Electron은 설치형 앱처럼 빌드된 정적 Angular 파일을 로드하지 않고, Angular dev server URL을 로드한다. 이 모드는 "Electron 앱 형태로 개발 확인"하기 위한 모드이며 installer/package 산출물을 만들지 않는다.

### `packaged`

실제 설치형 Electron 앱 모드다.

예상 실행 형태:

```text
Electron packaged app
Bundled Angular static files
Bundled NestJS server
Bundled Python runtime/plugins
```

Electron은 앱 host/native adapter 역할을 한다. packaged 앱 내부에서 NestJS와 Python plugin 프로세스를 실행하고, 포트는 런타임에 동적으로 할당한다.

## Env 파일 규칙

모든 env 파일명은 `.env`로 시작한다.

각 repo는 자신이 소비하는 env 파일만 가진다. 공통 루트 env 파일은 두지 않는다.

OS별 env 파일도 두지 않는다. 예를 들어 `.env.packaged.windows`, `.env.packaged.mac` 같은 파일을 기본 전략으로 만들지 않는다. 표준 checkout과 packaged resources에서 경로를 계산할 수 있어야 하며, secret env 파일은 OS-independent하게 같은 상대 경로에 복사 가능해야 한다.

기본 파일명:

```text
.env.local
.env.devapp
.env.packaged
.env.example
```

### `.env.local`

브라우저 기반 localhost 개발 실행용이다.

예:

```text
NEST_PORT=9019
PLUGIN_PORT_RANGE_START=54800
PLUGIN_PORT_RANGE_END=54999
```

### `.env.devapp`

패키징하지 않은 개발용 Electron 앱 실행용이다.

`local`과 포트, renderer URL, backend URL, 프로세스 실행 방식이 다를 수 있으므로 `.env.local`과 분리한다.

예:

```text
NEST_PORT=9029
PLUGIN_PORT_RANGE_START=55800
PLUGIN_PORT_RANGE_END=55999
```

Electron이 devapp에서 필요로 하는 값이 있다면 `clipper_electron/.env.devapp`에 둔다.

예:

```text
CLIPPER_RENDERER_URL=http://127.0.0.1:4300
CLIPPER_NEST_BASE_URL=http://127.0.0.1:9029/v1
```

### `.env.packaged`

실제 설치형 앱에서 사용하는 env 파일이다.

`packaged`에서는 고정 포트를 원칙적으로 사용하지 않는다. NestJS와 plugin 프로세스는 동적 포트를 사용해야 한다. 따라서 `.env.packaged`에는 API key, DB credential, feature flag처럼 packaged 앱에서 실제로 필요한 설정만 둔다.

컴퓨터마다 달라지는 absolute path는 기본 env에 두지 않는다. 표준 repo 배치나 packaged resources에서 추론할 수 있어야 하며, env path는 비표준 배치 또는 임시 진단용 override일 때만 사용한다.

따라서 Windows PC에서 빌드 테스트를 위해 Mac에서 정리한 `.env.*`를 복사할 때 경로값을 수정하는 절차가 있으면 안 된다. 수정이 필요하다면 env 파일을 OS별로 나누는 문제가 아니라 runtime path resolution을 고쳐야 한다.

### `.env.example`

개발자가 필요한 키를 알 수 있게 하는 문서용 샘플 파일이다. 실제 secret 값을 넣지 않는다.

예:

```text
NAVER_CLIENT_ID=
NAVER_CLIENT_SECRET=
KAKAO_REST_API_KEY=
```

`.env.example`도 실제 env 파일처럼 복사될 수 있으므로, 기본값 없이 비워 둔 optional path/cache override를 대량으로 나열하지 않는다. 선택적 override는 별도 문서에 설명하거나 주석으로만 둔다.

## Repo별 env 소유권

### `clipper_nestjs`

NestJS API 서버, plugin orchestration, 외부 API key를 관리한다.

예상 파일:

```text
clipper_nestjs/.env.local
clipper_nestjs/.env.devapp
clipper_nestjs/.env.packaged
clipper_nestjs/.env.example
```

주요 값:

```text
NEST_PORT
PLUGIN_PORT_RANGE_START
PLUGIN_PORT_RANGE_END
NAVER_CLIENT_ID
NAVER_CLIENT_SECRET
KAKAO_REST_API_KEY
```

### `clipper_python`

Python plugin이 직접 소비하는 runtime credential을 관리한다.

예상 파일:

```text
clipper_python/.env.local
clipper_python/.env.devapp
clipper_python/.env.packaged
clipper_python/.env.example
```

주요 값:

```text
CLIPPER_LLM_PROXY_URL
CLIPPER_SUBSCRIPTION_TOKEN
OPENAI_API_KEY
```

`HF_HOME`, `HUGGINGFACE_HUB_CACHE`, `XDG_CACHE_HOME`, `INSIGHTFACE_HOME`, `IMAGEIO_FFMPEG_EXE`, `IMAGEIO_FFPROBE_EXE`, `CLIPPER_LEGACY_ASSETS_DIR`, `CLIPPER_LEGACY_FONTS_DIR` 같은 값은 optional override다. 정상 배치에서는 코드가 기본 cache, packaged userData, bundled ffmpeg, sibling `clipper_python/fonts` 같은 값을 추론해야 한다. 이 값들을 빈 값으로 env 파일에 넣지 않는다.

### `clipper_electron`

Electron 자체가 소비하는 값이 있을 때만 env 파일을 둔다.

예상 파일:

```text
clipper_electron/.env.devapp
clipper_electron/.env.example
```

주요 값:

```text
CLIPPER_RENDERER_URL
CLIPPER_NEST_BASE_URL
```

Electron이 소비하지 않는 Python/NestJS 전용 값은 Electron env에 두지 않는다.

### `clipper_angular`

Angular는 secret env를 직접 소비하지 않는다.

Angular는 빌드/serve configuration으로 실행 모드를 구분한다. 실제 backend URL은 가능한 한 NestJS 또는 Electron bridge를 통해 얻는다.

## 포트 설계

플러그인별 고정 포트는 사용하지 않는다.

잘못된 방식:

```text
DIALOG_PLUGIN_URL=http://127.0.0.1:54821
DANCE_PLUGIN_URL=http://127.0.0.1:54822
RENDER_PLUGIN_URL=http://127.0.0.1:54823
```

사용할 방식:

```text
PLUGIN_PORT_RANGE_START=54800
PLUGIN_PORT_RANGE_END=54999
```

런타임은 플러그인을 시작할 때 포트 풀에서 사용 가능한 포트를 하나 할당한다.

예:

```text
dialog_highlight -> 54800
dance_highlight -> 54801
clipper1_video_render -> 54802
future_plugin_37 -> 54837
```

이 매핑은 env 파일에 쓰지 않는다. 실행 중인 plugin runtime registry가 보관한다.

## 플러그인 런타임 책임

Angular는 플러그인 포트와 프로세스를 몰라야 한다.

Angular의 책임:

```text
NestJS API 호출
```

NestJS의 책임:

```text
플러그인 설치 상태 확인
플러그인 실행 요청
플러그인 health check
플러그인 endpoint routing 또는 URL registry 관리
```

Electron의 책임:

```text
desktop host/native adapter
packaged 앱에서 bundled process 실행 보조
OS별 path/resource/userData 처리
```

Python의 책임:

```text
plugin server 실행
plugin manifest/entrypoint 제공
ML model/cache 사용
```

## Runtime abstraction

NestJS에는 plugin runtime 경계를 둔다.

```text
PluginRuntime
  start(plugin)
  stop(plugin)
  getStatus(plugin)
  getEndpoint(plugin)
  health(plugin)
```

구현체는 실행 모드에 따라 달라질 수 있다.

```text
LocalPluginRuntime
  local/devapp에서 Python plugin을 직접 실행하거나 이미 실행 중인 local plugin을 관리한다.
  포트 풀에서 동적 포트를 할당한다.

PackagedPluginRuntime
  packaged에서 Electron/native process manager와 협력해 bundled plugin을 실행한다.
  포트는 동적으로 할당한다.
```

이름은 구현 시 코드 구조에 맞게 조정할 수 있지만, 중요한 원칙은 Angular가 plugin URL을 직접 알지 않고 NestJS가 runtime boundary를 통해 관리한다는 점이다.

## 명령어 방향

### Angular

```text
npm run start:local
npm run start:devapp
npm run build:packaged
```

`start:devapp`은 Electron shell이 로드할 Angular dev server를 실행한다.

### NestJS

```text
npm run start:local
npm run start:devapp
npm run start:packaged
```

각 명령어는 해당 env 파일만 읽는다.

```text
start:local    -> .env.local
start:devapp   -> .env.devapp
start:packaged -> .env.packaged
```

### Electron

```text
npm run start:devapp
npm run build:app:mac:arm64
npm run build:app:win:x64
```

`start:devapp`은 installer/package를 만들지 않고 Electron shell만 실행한다. renderer URL과 NestJS base URL은 `.env.devapp` 또는 명령어가 지정한 값에서 읽는다.

### Python

Python plugin은 모드별 env 파일을 받아 실행할 수 있어야 한다.

```text
.env.local
.env.devapp
.env.packaged
```

플러그인을 수동으로 하나씩 고정 포트에 띄우는 방식은 장기 설계가 아니다. NestJS plugin runtime이 필요한 플러그인을 포트 풀에서 동적으로 실행하는 방향으로 정리한다.

## 현재 코드와의 차이

현재 Angular는 `local`/`electron` configuration이 일부 존재한다. 다만 `devapp` 명칭과 포트/env 기준으로 재정리해야 한다.

현재 Electron dev 실행은 `http://localhost:4200` renderer URL과 `http://127.0.0.1:9019/v1` NestJS URL을 사실상 고정 가정한다. `devapp`에서는 이를 env/config 기반으로 바꿔야 한다.

현재 NestJS env 로딩은 `.env.local`과 `.env`를 넓게 자동 탐색한다. 명령어가 지정한 실행 모드의 env 파일만 읽도록 바꿔야 한다.

현재 NestJS static plugin URL fallback은 플러그인 수가 늘어날수록 부적절하다. 포트 풀 기반 동적 할당 runtime으로 교체해야 한다.

현재 packaged Electron env provider는 NestJS `.env.local`까지 읽거나 copy할 수 있다. packaged에서는 `.env.packaged`만 사용하도록 정리해야 한다.

## 구현 순서 초안

1. 실행 모드 이름을 `local`, `devapp`, `packaged`로 확정한다.
2. 각 repo의 env 파일 규칙을 정리하고 `.env.example`을 갱신한다.
3. NestJS env loading을 명령어 기반 explicit mode loading으로 변경한다.
4. Electron devapp 실행에서 renderer URL과 NestJS base URL을 config/env 기반으로 바꾼다.
5. NestJS plugin runtime abstraction을 추가한다.
6. static plugin URL fallback을 포트 풀 기반 동적 할당으로 대체한다.
7. packaged build에서 `.env.local` copy/read를 제거하고 `.env.packaged`만 사용한다.
8. Windows/macOS에서 `local`, `devapp`, `packaged`를 각각 smoke test한다.

## 2026-05-21 코드 재검토 후 정정

이번 작업의 목표는 Windows packaged 앱에서 Naver/Kakao image search key가 누락된 직접 버그만 고치는 것이 아니다. 이 버그는 실행 모드, env 소유권, packaged env copy/read, devapp URL 주입, plugin runtime/port 책임이 불명확한 구조에서 드러난 증상이다.

따라서 성공 기준은 다음으로 잡는다.

```text
Windows packaged image search가 동작한다.
packaged에서 .env.local을 읽거나 복사하지 않는다.
NestJS env loading은 실행 모드가 지정한 env 파일만 읽는다.
Electron devapp은 renderer/NestJS URL을 코드 상수 대신 env/config에서 받는다.
plugin별 고정 URL fallback은 현재 구조 개선 범위에서 제거한다.
Angular는 plugin URL/port를 모르고 NestJS API만 호출한다.
```

현재 코드 기준으로 이미 정리된 부분도 있다.

```text
Angular는 BackendLocator로 NestJS base URL만 얻고 plugin URL을 직접 사용하지 않는다.
packaged Electron plugin manager는 이미 OS dynamic port allocation으로 plugin을 실행한다.
packaged NestJS는 Electron plugin host bridge를 통해 Electron-owned plugin process를 제어한다.
```

따라서 이번 구현에서 새로 만들 범위와 만들지 않을 범위를 구분한다.

### 이번 구현에 포함

```text
NestJS mode-based env loading
packaged .env.local copy/read 제거
packaged .env.packaged 사용
Electron devapp renderer/NestJS URL env 기반화
NestJS StaticPluginHost의 plugin별 default URL fallback 제거
local/devapp plugin runtime은 NestJS-owned LocalPluginHost로 실행
local/devapp plugin port는 runtime allocator가 동적으로 할당
```

### 이번 구현에서 제외

```text
subscription/remote config provider 구현
Angular UX 개편
```

local/devapp plugin process ownership은 이번 구현에서 NestJS control plane 방향에 맞춰 `LocalPluginHost`로 구현한다. 호환이 필요한 외부 plugin server 연결은 `StaticPluginHost`로 분리하고, 기본 실행 경로에서는 plugin별 고정 포트/URL을 사용하지 않는다.

### 2026-05-21 LocalPluginHost 구현 반영

추가 구현 기준:

```text
local/devapp 기본 PluginHost = LocalPluginHost
packaged PluginHost = ElectronPluginHost
compatibility external URL mode = StaticPluginHost
```

`LocalPluginHost` 책임:

```text
clipper_python/plugins/*/manifest.json discovery
manifest -> PluginManifestView mapping
PLUGIN_PORT_RANGE_START/END가 있으면 해당 범위에서 동적 port 할당
범위가 없으면 OS ephemeral port 할당
.env.<mode>를 직접 parse해 blank 값을 제외한 뒤 uv run --directory <clipper_python> python -m <plugin> <port> 실행
health check/status/stop 관리
```

이 구현으로 local/devapp에서 `PLUGIN_URL_DIALOG_HIGHLIGHT=...` 같은 plugin별 포트 env는 필요하지 않다. `PLUGIN_URLS` JSON은 `CLIPPER_PLUGIN_HOST_MODE=static`을 명시한 compatibility mode에서만 사용한다.

### Packaged Electron port allocation

packaged에서 Python plugin process는 Electron이 OS process host/native adapter로 실행하지만, 포트 정책은 동일하다.

```text
BundledEnvProvider가 clipper_nestjs/.env.packaged 또는 userData repo별 .env.packaged를 읽는다.
Electron LocalPluginManager는 PLUGIN_PORT_RANGE_START/END가 있으면 그 범위에서 plugin port를 동적으로 할당한다.
범위가 없으면 OS ephemeral port를 사용한다.
plugin stop/exit 시 claimed port를 release한다.
```

주의:

```text
NestJS gateway port와 Electron plugin host bridge port는 plugin port가 아니다.
이 둘은 내부 control-plane channel이므로 계속 OS ephemeral port를 사용한다.
PLUGIN_PORT_RANGE_START/END는 Python plugin process HTTP server port에만 적용한다.
```

## 검증 기준

### local

브라우저에서 Angular를 열었을 때 NestJS API와 plugin 기능이 동작해야 한다.

### devapp

패키징 없이 Electron 앱을 실행했을 때 Angular dev server를 로드하고 NestJS API와 plugin 기능이 동작해야 한다.

### packaged

macOS/Windows 설치형 앱에서 NestJS, Python plugin, model/cache/env 설정이 모두 정상 동작해야 한다.

### plugin scalability

플러그인을 추가해도 env 파일에 플러그인별 포트를 추가하지 않아야 한다. 런타임 registry와 포트 풀만으로 실행되어야 한다.

## 2026-05-21 구현 결과

확정된 구현 기준:

```text
local/devapp: NestJS LocalPluginHost가 Python plugin process를 직접 실행한다.
packaged: Electron LocalPluginManager가 native adapter로 Python plugin process를 실행하고 NestJS는 ElectronPluginHost로 제어한다.
start:devapp/build:devapp/build:packaged 명령을 추가하고 기존 electron 명령은 compatibility alias로 유지한다.
packaged resources에는 repo별 .env.packaged만 포함한다.
Template Builder official DB는 packaged 런타임에서도 필수다. .env.packaged에 CLIPPER2_TEMPLATE_DB_*가 없으면 build/preflight 또는 boot에서 실패해야 한다.
mode env 파일은 blank placeholder를 맞추는 schema가 아니다. 각 env 파일에는 해당 모드에서 실제로 설정할 값만 둔다.
OS별 absolute path는 기본 env에 요구하지 않는다. 표준 repo sibling 경로나 packaged resources/userData에서 자동 추론한다.
Mac checkout의 ignored secret env 파일은 Windows checkout의 같은 상대 경로로 그대로 복사 가능해야 한다.
Python env의 Naver/Kakao key는 제거한다. 현재 image search owner는 NestJS다.
```

packaged smoke 결과:

```text
macOS arm64 packaged build PASS
resources env files = clipper_nestjs/.env.packaged, clipper_python/.env.packaged only
packaged app NestJS boot PASS
GET /v1/health PASS
GET /v1/template-builder/families PASS, DB-backed family count 25
GET /v1/plugins PASS
POST /v1/dance/members/images PASS, BLACKPINK/Jennie 후보 10개
```
