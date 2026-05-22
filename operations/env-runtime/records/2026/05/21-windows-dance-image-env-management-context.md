# Windows dance image 0건 문제에서 env/run mode 재설계로 이어진 경과

작성일: 2026-05-21

관련 설계 문서:

- `.codex/operations/env-runtime/records/2026/05/21-execution-env-mode-design.md`

## 시작점

Windows PC에서 `clipper_electron` 설치형 앱을 빌드한 뒤 dance highlight plugin을 실행했을 때, 아티스트 멤버별 이미지 후보를 전부 0개만 가져오는 문제가 보고되었다.

맥에서는 `clipper_electron`에서 `npm run build:app:mac:arm64`로 빌드한 설치형 앱에서 같은 기능이 정상 동작했다. Windows에서는 `npm run build:app:win:x64`로 빌드한 앱에서 dance highlight plugin 설치와 실행 자체는 됐지만, 멤버별 이미지 후보 수집만 실패했다.

사용자는 macOS와 Windows 양쪽의 `clipper_nestjs`에 `.env`, `.env.local` 파일이 동일하게 존재한다고 설명했다. 따라서 단순히 코드 차이 문제가 아니라 실행 환경, env 파일 의미, packaged 앱에서 env가 어떤 경로로 복사되고 읽히는지의 문제로 조사가 확장되었다.

## 직전 Windows smoke/fix 흐름

이번 문제 직전에는 다른 Windows PC smoke 결과를 바탕으로 다음 문제가 수정되어 있었다.

### Template Builder local font/thumbnail preview

Windows packaged app에서 새 템플릿에 local `.ttf`/`.otf` 파일을 업로드한 뒤 Template Builder preview font가 바뀌지 않고, 새 템플릿 카드 썸네일이 깨지는 문제가 있었다.

수정 commit:

```text
clipper_angular b9e1052 Fix Windows template asset previews
```

### Dance highlight ffprobe download

Dance highlight plugin 설치 중 `@ffprobe-installer/win32-x64@5.0.1` tarball download가 HTTP 404로 실패했다.

원인은 ffprobe package version이 hardcoded 되어 있었기 때문이다. npm metadata에서 latest tarball을 resolve하도록 변경했다.

수정 commit:

```text
clipper_electron 1a7f1b9 Resolve ffprobe tarball dynamically
```

### Dialog highlight install-state

Windows packaged app에서 dialog highlight plugin 설치가 완료됐다고 표시되지만 Plugin Store card는 계속 다운로드 필요 상태로 남는 문제가 있었다.

원인은 HuggingFace cache layout 차이였다. Windows PC에서는 실제 모델 파일이 `snapshots/<revision>/...` 아래에 있었고 `blobs`가 비어 있었는데, 기존 install-state 판정은 `blobs` non-empty만 인정했다.

수정 commit:

```text
clipper_electron 19dafd3 Fix dialog model install detection on Windows
```

검증:

```text
clipper_electron npm.cmd run build
clipper_electron node --test test/plugin-install-state.test.mjs
```

## dance highlight 멤버 이미지 0건 조사 결과

멤버 이미지를 가져오는 기능은 Python dance plugin이 아니라 NestJS 쪽 이미지 검색 API 흐름에 있다.

확인된 흐름:

```text
Angular dance flow
  -> NestJS image search API
  -> Naver image search
  -> Kakao fallback
```

관련 코드 흐름:

```text
Angular DanceFlowStore.loadFirstPageFor()
NestJS ImageSearchService
```

Angular 쪽은 이미지 검색 실패를 UI에서 치명 오류로 터뜨리지 않고 빈 후보 목록으로 흡수한다. 그래서 실제 원인이 API key 누락 또는 backend image search 실패여도 사용자는 "0개 가져옴"처럼 보게 된다.

NestJS image search는 다음 env 값이 필요하다.

```text
NAVER_CLIENT_ID
NAVER_CLIENT_SECRET
KAKAO_REST_API_KEY
```

조사 시점의 Windows 환경에서는 다음 위치에 해당 key들이 없었다.

```text
clipper_nestjs/.env.local
clipper2-smoke-install/resources/clipper_nestjs/.env.local
%APPDATA%/Clipper2/.env
clipper_python/.env
clipper2-smoke-install/resources/clipper_python/.env
```

따라서 Windows에서 멤버 이미지 후보가 0개로 보인 직접 원인은 image search에 필요한 Naver/Kakao key가 packaged 앱 실행 환경에 제대로 주입되지 않은 것이다.

## 왜 Mac에서는 됐고 Windows에서는 안 됐는가

코드가 달라서라기보다 packaged 앱이 읽는 env 경로와 실제 빌드/설치 결과물에 포함된 env 파일 상태가 달랐을 가능성이 높다.

macOS에서는 다음 중 하나가 성립했을 수 있다.

```text
packaged resources 안에 필요한 key가 들어간 env 파일이 있었음
userData 또는 shell environment에 key가 있었음
기존 local 파일이 packaged 앱에 우연히 포함되어 동작했음
```

Windows에서는 packaged resources 또는 userData 쪽에서 image search key를 찾지 못했다.

이 차이는 "Windows만 image search API가 다르다"가 아니라, env 파일이 실행 모드별로 통제되지 않고 넓게 탐색/복사되는 구조에서 OS별 빌드 산출물과 로컬 파일 상태에 따라 결과가 달라진 것이다.

## env 파일 이름 논의

사용자는 팀 관습을 명확히 정정했다.

```text
.env.local = localhost 개발 실행용
```

즉 `.env.local`은 개인 PC override 파일이 아니다. 설치형 앱에서 `.env.local`을 읽거나 복사하는 것은 의미상 맞지 않다.

또한 테스트용 env 파일은 팀에서 사용하지 않으므로 `.env.test`는 도입하지 않는다.

모든 env 파일명은 `.env`로 시작해야 한다.

## 실행 모드 명칭 결정

처음에는 `local`, `local-electron`, `packaged` 같은 이름이 논의되었다.

사용자는 `local-electron`이 길고, `packaged`를 `electron`으로 대체하는 것도 모호하다고 판단했다. `electron`은 패키징하지 않은 개발용 Electron shell과 실제 설치형 Electron app을 모두 가리킬 수 있기 때문이다.

최종적으로 현재 문서화 기준 명칭은 다음으로 정리했다.

```text
local
devapp
packaged
```

의미:

```text
local     = 브라우저 기반 로컬 개발
devapp    = 패키징하지 않은 개발용 Electron 앱
packaged  = 실제 설치형 Electron 앱
```

## 포트 설계 논의와 수정

초기 답변에서는 plugin별 고정 포트 예시가 제시되었다.

```text
dialog 54821
dance 54822
render 54823
```

사용자는 플러그인이 수십 개로 늘어나면 이 방식은 불가능하다고 지적했다. 이 지적이 맞다.

정리된 결론은 다음과 같다.

```text
플러그인별 고정 포트는 env에 쓰지 않는다.
모드별 포트 범위만 env에 둔다.
런타임이 실행 시점에 사용 가능한 포트를 동적으로 할당한다.
```

예:

```text
PLUGIN_PORT_RANGE_START=54800
PLUGIN_PORT_RANGE_END=54999
```

실행 중 mapping은 plugin runtime registry가 관리한다.

```text
dialog_highlight -> 54800
dance_highlight -> 54801
future_plugin_37 -> 54837
```

이 mapping은 env 파일에 저장하지 않는다.

## env 파일 결론

각 repo는 자신이 소비하는 env 파일을 가진다. 루트 공통 env 파일은 두지 않는다.

기본 파일:

```text
.env.local
.env.devapp
.env.packaged
.env.example
```

`local`과 `devapp`은 서로 다른 실행 모드이므로 같은 env 파일을 공유하지 않는다.

```text
local    -> .env.local
devapp   -> .env.devapp
packaged -> .env.packaged
```

`clipper_nestjs`는 NestJS API, image search key, plugin orchestration 설정을 가진다.

`clipper_python`은 ML cache/model/runtime 관련 설정을 가진다.

`clipper_electron`은 Electron 자체가 실제로 소비하는 값이 있을 때만 env 파일을 가진다. 예를 들어 `devapp`에서 renderer URL과 NestJS base URL을 알아야 한다면 `clipper_electron/.env.devapp`을 둔다.

## 현재 코드에서 고쳐야 할 지점

### NestJS env loading

현재 NestJS는 여러 경로의 `.env.local`과 `.env`를 자동 탐색한다. 이 방식은 실행 모드별 env 파일 원칙과 충돌한다.

바꿀 방향:

```text
명령어가 실행 모드를 지정한다.
지정된 실행 모드의 env 파일만 읽는다.
.env.local은 local 모드에서만 읽는다.
.env.devapp은 devapp 모드에서만 읽는다.
.env.packaged는 packaged 모드에서만 읽는다.
```

### Electron devapp

현재 Electron dev 실행은 Angular dev server URL과 NestJS base URL을 고정 가정한다.

바꿀 방향:

```text
CLIPPER_RENDERER_URL
CLIPPER_NEST_BASE_URL
```

위 값들을 `clipper_electron/.env.devapp` 또는 명령어 config에서 읽는다.

### packaged env

현재 packaged build/provider는 NestJS `.env.local`까지 읽거나 복사할 수 있다. 이는 팀 관습과 충돌한다.

바꿀 방향:

```text
packaged에서는 .env.packaged만 사용한다.
.env.local은 packaged resources에 복사하지 않는다.
```

### plugin runtime

현재 NestJS에는 static plugin URL fallback이 있다. 플러그인 개수가 늘어나는 구조에는 맞지 않는다.

바꿀 방향:

```text
PluginRuntime abstraction
Port pool allocator
Runtime registry
Health check/status 관리
```

Angular는 plugin URL을 직접 알지 않고 NestJS API만 호출해야 한다.

## 현재 결론

Windows dance highlight 멤버 이미지 0건 문제의 직접 원인은 image search key가 Windows packaged 앱 실행 환경에 제대로 들어가지 않은 것이다.

하지만 이것은 단순히 key를 Windows env 파일에 추가하는 수준에서 끝낼 문제가 아니다. 현재 구조에서는 `.env.local`의 의미, packaged env 복사, Electron dev 실행 URL, NestJS env loading, plugin port 관리가 모두 느슨하게 연결되어 있어 OS별로 다른 결과가 나올 수 있다.

따라서 다음 구현은 단순한 key 복사가 아니라 실행 모드와 env loading을 먼저 바로잡는 방향으로 진행해야 한다.

기준 설계는 `.codex/operations/env-runtime/records/2026/05/21-execution-env-mode-design.md`를 따른다.

## 재검토 후 구현 범위 정정

처음에는 직접 버그 해결 관점에서 plugin runtime/port 정리를 후속 phase로 미루는 안이 나왔다. 사용자는 이번 목표가 단순한 Windows packaged image search 복구가 아니라 프로젝트 설계와 구조를 바로잡는 것임을 명확히 했다.

정정된 기준:

```text
직접 버그 해결은 필수 결과물이다.
그러나 성공 기준은 Windows에서 image search가 나온다는 것에 머물지 않는다.
실행 모드, env 파일 소유권, packaged env copy/read, devapp URL 주입,
plugin runtime/port 책임이 현재 코드에서 일관되게 정리되어야 한다.
```

이번 구현에 포함할 항목:

```text
NestJS env loading을 local/devapp/packaged mode 기반으로 명시화한다.
packaged build/runtime에서 .env.local copy/read를 제거한다.
packaged env는 clipper_nestjs/.env.packaged만 사용한다.
Electron devapp은 renderer URL과 NestJS base URL을 env/config에서 읽는다.
StaticPluginHost의 plugin별 default URL fallback을 제거한다.
local/devapp plugin runtime은 NestJS LocalPluginHost가 직접 실행한다.
plugin별 고정 포트 env는 사용하지 않는다.
```

이번 구현에서 제외할 항목은 plugin process spawn 자체가 아니라 더 큰 config/UX 정리다.

```text
RemoteConfigProvider/subscription config도 다음 phase다.
Angular UX 개편도 다음 phase다.
```

중요한 차이는 "후속 phase"가 구조 개선에서 제외된다는 뜻이 아니라는 점이다. 이번 phase에서는 숨은 default/plugin별 고정 URL을 제거하고, NestJS-owned local/devapp runtime을 얹어 잘못된 구조를 더 이상 기본값으로 유지하지 않는다.

## LocalPluginHost 구현

후속 구현에서 `clipper_nestjs`에 `LocalPluginHost`가 추가되었다.

책임:

```text
clipper_python/plugins/*/manifest.json discovery
manifest 기반 plugin list/status 제공
PLUGIN_PORT_RANGE_START/END 또는 OS ephemeral port에서 동적 port 할당
.env.<mode>를 직접 parse해 blank 값을 제외한 뒤 uv run으로 Python plugin process 실행
health check 이후 baseUrl 반환
stop/status/lifecycle 관리
```

PluginHost 선택 기준:

```text
ELECTRON_PLUGIN_HOST_URL 있음 -> ElectronPluginHost
CLIPPER_PLUGIN_HOST_MODE=static -> StaticPluginHost
그 외 local/devapp 기본값 -> LocalPluginHost
```

따라서 local/devapp에서 plugin별 고정 URL fallback은 더 이상 기본 경로가 아니다. 외부 plugin server를 수동으로 붙여야 하는 compatibility 상황에서만 `CLIPPER_PLUGIN_HOST_MODE=static`과 `PLUGIN_URLS` JSON을 사용한다.

## Packaged Electron plugin port range

Electron-owned packaged plugin process도 같은 port 정책을 쓰도록 정리했다.

```text
clipper_electron PortAllocator가 optional PLUGIN_PORT_RANGE_START/END를 지원한다.
main bootstrap에서 BundledEnvProvider가 읽은 packaged env로 plugin port range를 만든다.
LocalPluginManager는 plugin process start 시 range 내 available port를 동적으로 할당한다.
plugin stop/exit/start failure 시 claimed port를 release한다.
```

범위는 Python plugin process에만 적용한다. NestJS gateway port와 Electron plugin host bridge port는 내부 control-plane channel이므로 계속 OS ephemeral port를 사용한다.

## 2026-05-21 구현/검증 결과

구현된 내용:

```text
NestJS mode-based env loading 적용
packaged build/runtime에서 .env.local copy/read 제거
clipper_nestjs/.env.packaged, clipper_python/.env.packaged만 packaged resources에 포함
Electron devapp renderer/NestJS URL env 기반화
StaticPluginHost plugin별 default URL fallback 제거
NestJS LocalPluginHost 추가
local/devapp plugin port allocator 추가
Electron packaged plugin port range alignment 추가
Template Builder official DB는 런타임 필수 정책을 유지하고 .env.packaged/preflight를 보강
```

현재 workspace에는 다음 ignored secret env 파일을 준비했다. 값은 문서와 로그에 기록하지 않는다.

```text
clipper_nestjs/.env.devapp
clipper_nestjs/.env.packaged
clipper_python/.env.local
clipper_python/.env.devapp
clipper_python/.env.packaged
clipper_electron/.env.devapp
```

검증 결과:

```text
clipper_nestjs npm run build PASS
clipper_nestjs npm run bundle PASS
clipper_electron npm run build PASS
clipper_angular build:packaged/devapp PASS with Node 22 outside sandbox
macOS arm64 packaged build PASS
packaged resources env files = clipper_nestjs/.env.packaged, clipper_python/.env.packaged only
packaged app NestJS boot PASS
GET /v1/health PASS
GET /v1/template-builder/families PASS, DB-backed family count 25
GET /v1/plugins PASS
POST /v1/dance/members/images PASS, BLACKPINK/Jennie 후보 10개
```

## Env 파일 정리 및 후속 정정

정리 기준:

```text
mode env 파일은 blank placeholder를 맞추는 schema가 아니다.
각 .env.<mode>에는 해당 모드에서 실제로 설정할 값만 둔다.
컴퓨터마다 달라지는 absolute path는 기본 env에 요구하지 않는다.
필요 없는 legacy .env 파일은 제거한다.
Electron은 현재 .env.devapp만 직접 소비하므로 .env.local/.env.packaged를 만들지 않는다.
```

적용 결과:

```text
clipper_nestjs: image search key, Template Builder DB/S3 credential, Nest/plugin port range만 기본 env 대상으로 유지
clipper_python: dialog LLM credential만 기본 env 대상으로 유지
clipper_electron: .env.example/.env.devapp만 유지
clipper_nestjs/.env 제거
clipper_python/.env 제거
```

Python env에서 제거한 key:

```text
NAVER_CLIENT_ID
NAVER_CLIENT_SECRET
KAKAO_REST_API_KEY
```

이유:

```text
현재 멤버 이미지 검색은 NestJS image search API 경로가 owner다.
Python dance_highlight 안에 예전 image_search_service.py는 남아 있지만 현재 참조되지 않는다.
따라서 Naver/Kakao key는 clipper_nestjs env에만 둔다.
```

유지한 Python key:

```text
OPENAI_API_KEY
CLIPPER_LLM_PROXY_URL
CLIPPER_SUBSCRIPTION_TOKEN
```

이유:

```text
dialog_highlight LLM client가 직접 소비한다.
packaged/prod 방향은 CLIPPER_LLM_PROXY_URL + CLIPPER_SUBSCRIPTION_TOKEN이고,
OPENAI_API_KEY는 local/dev fallback이다.
```

blank env 안전 처리:

```text
Python plugin launcher는 .env.<mode>를 직접 parsing하고 blank value는 주입하지 않는다.
HF_HOME= 같은 blank 값이 실제 process env로 들어가 cache path를 망치지 않게 하기 위함이다.
NestJS gateway port parsing도 blank NEST_PORT를 무시한다.
```

2026-05-21 후속 정정:

```text
blank value를 무시하는 parser는 방어 장치일 뿐, blank placeholder를 env 파일에 넣어도 된다는 의미가 아니다.
.env.example도 기본 실행에 필요한 값 위주로 줄인다.
CLIPPER_PYTHON_ROOT 같은 path 값은 표준 sibling checkout에서 필요하지 않아야 한다.
PLUGIN_URLS={}는 StaticPluginHost compatibility mode에서만 직접 설정한다.
```

후속 commit:

```text
clipper_nestjs 9cd43f1 Trim optional env placeholders
clipper_python 88d22c6 Trim optional env placeholders
clipper_electron 06936ba Trim optional env placeholders
```

실제 ignored secret env 파일도 후속 정리했다. 이 파일들은 git commit 대상이 아니지만, 현재 Mac checkout에서 Windows checkout으로 그대로 복사할 기준 파일이다.

이것은 Windows용 env를 별도로 만든다는 뜻이 아니다. 현재 Mac checkout의 `.env.*` 파일을 OS-independent하게 정리했고, Windows checkout에는 같은 상대 경로로 그대로 복사한다. Windows에서 `CLIPPER_PYTHON_ROOT` 같은 경로값을 고치는 절차는 도입하지 않는다.

현재 key 구성:

```text
clipper_nestjs/.env.local: NEST_PORT, image search keys, plugin port range, Template Builder DB/S3 keys
clipper_nestjs/.env.devapp: NEST_PORT, image search keys, plugin port range, Template Builder DB/S3 keys
clipper_nestjs/.env.packaged: image search keys, plugin port range, Template Builder DB/S3 keys
clipper_python/.env.local: OPENAI_API_KEY
clipper_python/.env.devapp: OPENAI_API_KEY
clipper_python/.env.packaged: OPENAI_API_KEY
clipper_electron/.env.devapp: CLIPPER_RENDERER_URL, CLIPPER_NEST_BASE_URL
```

현재 실제 env 파일에 없어야 하는 key:

```text
CLIPPER_PYTHON_ROOT
CLIPPER_PLUGIN_HOST_MODE
PLUGIN_URLS
HF_HOME
HUGGINGFACE_HUB_CACHE
XDG_CACHE_HOME
INSIGHTFACE_HOME
IMAGEIO_FFMPEG_EXE
IMAGEIO_FFPROBE_EXE
CLIPPER_LEGACY_ASSETS_DIR
CLIPPER_LEGACY_FONTS_DIR
CLIPPER1_REMOTE_ASSET_TIMEOUT_SEC
CLIPPER1_REMOTE_FONT_MAX_BYTES
```

## 이번 세션 commit 목록

`clipper_nestjs`:

```text
1c8bd74 Clarify env modes and local plugin runtime
d064f5a Restore required template DB runtime
37c37e8 Align NestJS env schema
9cd43f1 Trim optional env placeholders
```

`clipper_electron`:

```text
96f9fd0 Use packaged env files for desktop runtime
fc17b29 Require template DB env for packaged builds
148248b Ignore blank plugin env values
06936ba Trim optional env placeholders
```

`clipper_angular`:

```text
72faaf7 Add devapp and packaged Angular modes
```

`clipper_python`:

```text
cae92e6 Document Python env mode files
f019ac4 Align Python plugin env schema
88d22c6 Trim optional env placeholders
```

현재 git 상태:

```text
clipper_nestjs clean, origin보다 ahead 1 until pushed
clipper_electron clean, origin보다 ahead 1 until pushed
clipper_angular clean
clipper_python clean, origin보다 ahead 1 until pushed
ignored local secret env files remain unstaged
```

남은 확인:

```text
Windows packaged build/smoke에서 같은 resources/env 규칙과 dance member image 결과를 확인한다.
```
