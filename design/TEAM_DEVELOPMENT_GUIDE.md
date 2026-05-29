# Clipper2 Team Development Guide

작성 기준: 2026-05-29

이 문서는 새 팀원이 Clipper2 구조, 실행 모드, 브랜치 방식, env 파일 기준을 빠르게 이해하고 바로 개발을 시작하기 위한 가이드다. Notion import용 단일 문서로 작성했다.

## 1. 프로젝트 구성

표준 checkout은 아래처럼 4개 앱 repo가 같은 부모 폴더 아래 sibling으로 놓이는 구조다.

```text
adlight/
  clipper_angular/   # Angular UI
  clipper_nestjs/    # NestJS API/control plane
  clipper_electron/  # Electron desktop host/packaging
  clipper_python/    # Python plugin/worker runtime
  .codex/            # 설계/운영/세션 문서 repo, 앱 코드와 별도 git repo
```

중요한 점:

- `.codex`는 앱 코드가 아니라 문서 repo다.
- 앱 코드 변경과 `.codex` 문서 변경은 같은 commit에 섞지 않는다.
- 표준 sibling checkout을 기준으로 경로를 자동 탐색한다. 팀원이 임의로 absolute path env를 추가하는 방식은 피한다.

## 2. 전체 설계 구조

Clipper2는 하나의 데스크톱 앱처럼 보이지만 내부적으로는 여러 프로세스가 역할을 나눈다.

```text
Angular UI
  -> NestJS API/control plane
  -> WorkflowExecutor boundary
      -> Python plugin executor
      -> NestJS-native executor
      -> virtual workflow entry

Electron desktop host
  -> app window
  -> packaged NestJS process host
  -> packaged Python process host
  -> native IPC: file dialog, ffmpeg/model download, capture, auth
```

Repo별 책임:

| Repo | 책임 | 하지 않는 일 |
| --- | --- | --- |
| `clipper_angular` | 화면, 사용자 입력, 진행 상태 표시, NestJS API 호출 | Python plugin URL/port 직접 접근, secret env 소비 |
| `clipper_nestjs` | API gateway, project/template/source/job/workflow orchestration, WorkflowExecutor dispatch, local/devapp Python plugin 실행, NestJS-native executor 실행 | 데스크톱 창 생성, native file dialog, packaged Python process host |
| `clipper_electron` | Electron window, packaged NestJS/Python process host, native IPC, installer packaging | domain workflow 결정 |
| `clipper_python` | 영상 분석/렌더링/모델 작업 plugin runtime | UI 제공, NestJS API gateway |

기본 원칙:

- Angular는 NestJS API만 호출한다.
- Angular는 plugin URL이나 plugin port를 몰라야 한다.
- `/jobs` 실행은 NestJS `WorkflowExecutorRegistry`가 dispatch한다.
- Python plugin process 제어는 `PluginHost`가 맡고, NestJS-native executor는 Python HTTP server 없이 NestJS 내부에서 실행한다.
- plugin port는 runtime이 동적으로 할당한다.
- plugin별 고정 포트 env를 추가하지 않는다.
- packaged build/runtime은 `.env.local`, `.env.devapp`, generic `.env`를 읽거나 복사하지 않는다.

## 3. 실행 모드 요약

| 모드 | 용도 | UI | NestJS | Python plugin | Env |
| --- | --- | --- | --- | --- | --- |
| `local` | 브라우저 localhost 개발 | Angular dev server | 직접 실행 | NestJS가 필요 시 실행 | `.env.local` |
| `devapp` | 빌드 없이 Electron 앱 창으로 개발 | Electron + Angular dev server | 직접 실행 | NestJS가 필요 시 실행 | `.env.devapp` |
| `packaged` | 실제 설치형 앱 빌드/검증 | packaged renderer | Electron이 내부 실행 | Electron/NestJS가 관리 | `.env.packaged` |

Plugin/workflow runtime 기준:

- `python_plugin`: `dance_highlight`, `dialog_highlight`, `clipper1_video_render`처럼 Python process로 실행된다.
- `nestjs_executor`: `simple_ffmpeg_transform`처럼 NestJS service/child process로 실행된다.
- `virtual_workflow`: `clipper1`, `variation`처럼 Store/route/workflow entry 성격이고 직접 runtime job이 아닐 수 있다.

## 4. 최초 개발 환경 세팅

### 공통 요구사항

- Git
- Node.js 22 LTS
- npm
- uv
- macOS/Windows packaged build를 위해 `tar` 사용 가능해야 함

macOS에서 Node 버전을 맞출 때:

```bash
source ~/.zshrc
nvm use 22
node -v
npm -v
```

Windows PowerShell에서는 `npm` 대신 `npm.cmd`를 쓰면 execution policy 이슈를 피하기 쉽다.

```powershell
node -v
npm.cmd -v
tar --version
```

### Repo clone

이 문서의 macOS/Linux 명령은 `PROJECT_ROOT`를 기준으로 적는다. 각자 실제 checkout 위치에 맞춰 한 번만 지정한다.

```bash
export PROJECT_ROOT=/path/to/adlight
mkdir -p "$PROJECT_ROOT"
cd "$PROJECT_ROOT"

git clone https://github.com/OhMyMetabuzz/clipper_angular.git clipper_angular
git clone https://github.com/OhMyMetabuzz/clipper_nestjs.git clipper_nestjs
git clone https://github.com/OhMyMetabuzz/clipper_electron.git clipper_electron
git clone https://github.com/OhMyMetabuzz/clipper_python.git clipper_python
```

Windows PowerShell에서는 같은 의미로 `$ProjectRoot`를 지정한다.

```powershell
$ProjectRoot = 'C:\project\adlight'
New-Item -ItemType Directory -Force $ProjectRoot
Set-Location $ProjectRoot
```

팀 개발 기준 branch는 `main`이다.

```bash
cd "$PROJECT_ROOT/clipper_angular" && git switch main && git pull --ff-only
cd "$PROJECT_ROOT/clipper_nestjs" && git switch main && git pull --ff-only
cd "$PROJECT_ROOT/clipper_electron" && git switch main && git pull --ff-only
cd "$PROJECT_ROOT/clipper_python" && git switch main && git pull --ff-only
```

협업 시작 전 maintainer 확인사항:

- 4개 앱 repo의 remote `main`이 최신 작업 상태를 가리켜야 한다.
- `clipper_python`에서 `main...origin/main [ahead 103]`이 보이면 아직 feature 개발 이력 103개 commit이 remote `main`에 push되지 않은 상태다. 이는 파일 103개 변경이 아니라 commit count다.

### Dependency install

```bash
cd "$PROJECT_ROOT/clipper_angular"
npm install

cd "$PROJECT_ROOT/clipper_nestjs"
npm install

cd "$PROJECT_ROOT/clipper_electron"
npm install

cd "$PROJECT_ROOT/clipper_python"
uv sync
```

packaged build를 할 PC에서는 Electron repo에서 uv binary를 한 번 준비한다.

```bash
cd "$PROJECT_ROOT/clipper_electron"
npm run fetch-uv
```

## 5. 실행 방법 A: 브라우저 localhost 개발 (`local`)

Electron 앱 창 없이 브라우저에서 Angular dev server를 직접 연다. UI 개발, NestJS API 개발, 일반 기능 확인에 가장 가볍다.

읽는 env:

```text
clipper_nestjs/.env.local
clipper_python/.env.local
```

터미널 1: NestJS

```bash
cd "$PROJECT_ROOT/clipper_nestjs"
npm run start:local
```

터미널 2: Angular

```bash
cd "$PROJECT_ROOT/clipper_angular"
npm run start:local
```

브라우저:

```text
http://localhost:4200
```

Health check:

```bash
curl -s http://127.0.0.1:9019/v1/health
```

프로세스 흐름:

```text
Browser Angular
  -> NestJS API at http://127.0.0.1:9019/v1
  -> WorkflowExecutor
      -> Python plugin, 필요 시 NestJS LocalPluginHost가 uv로 동적 실행
      -> NestJS-native executor
```

Python plugin은 보통 수동으로 따로 띄우지 않는다. NestJS가 workflow/job 실행 시 필요한 plugin을 `uv run --directory ../clipper_python python -m <plugin>` 형태로 실행한다.

## 6. 실행 방법 B: 빌드 없이 Electron 앱 창 실행 (`devapp`)

설치형 앱으로 packaging하지 않고 Electron BrowserWindow만 띄워 desktop 흐름을 확인한다. file dialog, preload bridge, Electron IPC, app window 동작을 볼 때 사용한다.

읽는 env:

```text
clipper_nestjs/.env.devapp
clipper_python/.env.devapp
clipper_electron/.env.devapp
```

터미널 1: NestJS

```bash
cd "$PROJECT_ROOT/clipper_nestjs"
npm run start:devapp
```

터미널 2: Angular dev server

```bash
cd "$PROJECT_ROOT/clipper_angular"
npm run start:devapp
```

터미널 3: Electron app window

```bash
cd "$PROJECT_ROOT/clipper_electron"
npm run start:devapp
```

`clipper_electron/.env.devapp` 기본값:

```env
CLIPPER_RENDERER_URL=http://localhost:4200
CLIPPER_NEST_BASE_URL=http://127.0.0.1:9019/v1
```

프로세스 흐름:

```text
Electron devapp
  -> Angular dev server를 BrowserWindow에 로드
  -> Electron preload bridge로 NestJS base URL 제공
  -> 외부에서 실행 중인 NestJS API 호출
  -> WorkflowExecutor
      -> Python plugin, 필요 시 NestJS LocalPluginHost가 uv로 동적 실행
      -> NestJS-native executor
```

`devapp`은 앱 창은 띄우지만 installer나 `.app`/`.exe` 산출물을 만들지 않는다.

## 7. 실행 방법 C: 설치형 앱 빌드 (`packaged`)

실제 사용자에게 배포할 형태의 앱을 만든다. 기존에 주로 사용하던 `npm run build:app:mac:arm64` 방식이다.

읽는 env:

```text
clipper_nestjs/.env.packaged
clipper_python/.env.packaged
```

packaged build/runtime에서 사용하면 안 되는 env:

```text
.env.local
.env.devapp
.env
```

Mac Apple Silicon:

```bash
cd "$PROJECT_ROOT/clipper_electron"
source ~/.zshrc
nvm use 22
npm run fetch-uv
npm run build:app:mac:arm64
```

Mac Intel:

```bash
cd "$PROJECT_ROOT/clipper_electron"
source ~/.zshrc
nvm use 22
npm run fetch-uv
npm run build:app:mac:x64
```

Windows x64 PowerShell:

```powershell
$ProjectRoot = 'C:\project\adlight'
Set-Location (Join-Path $ProjectRoot 'clipper_electron')
node -v
npm.cmd run fetch-uv
npm.cmd run build:app:win:x64
```

Windows build 중에는 Microsoft PowerToys `Command Palette`를 끈다. `Keyboard Manager`는 켜져 있어도 된다. `Command Palette`가 `Clipper2.exe`를 잡으면 electron-builder 단계에서 `EBUSY` 또는 sharing violation이 발생할 수 있다.

packaged build pipeline:

```text
1. clipper_angular npm run build:packaged
2. clipper_nestjs npm run bundle
3. clipper_electron TypeScript compile
4. target platform uv binary 준비
5. electron-builder로 .app/.dmg 또는 Windows installer 생성
```

Mac ARM64 산출물 실행:

```bash
cd "$PROJECT_ROOT/clipper_electron"
./dist-app/mac-arm64/Clipper2.app/Contents/MacOS/Clipper2
```

Finder로 열기:

```bash
cd "$PROJECT_ROOT/clipper_electron"
open dist-app/mac-arm64/Clipper2.app
```

packaged runtime 흐름:

```text
Electron packaged app
  -> bundled Angular static files 로드
  -> bundled NestJS를 동적 port로 내부 실행
  -> NestJS ready URL을 Electron/renderer에 전달
  -> WorkflowExecutor
      -> Python plugin은 필요 시 Electron-managed packaged Python runtime에서 실행
      -> NestJS-native executor는 packaged NestJS process 안에서 실행
```

packaged mode에서는 NestJS port가 고정값이 아니다. 로그에서 아래 형태를 확인한다.

```text
[NestManager] ready at http://127.0.0.1:<port>/v1
```

## 8. 빌드/테스트 명령 모음

Angular:

```bash
cd "$PROJECT_ROOT/clipper_angular"
npm run build:local
npm run build:devapp
npm run build:packaged
npm test -- --watch=false
```

NestJS:

```bash
cd "$PROJECT_ROOT/clipper_nestjs"
npm run build
npm run bundle
```

Electron:

```bash
cd "$PROJECT_ROOT/clipper_electron"
npm run build
npm run start:devapp
npm run build:app:mac:arm64
```

Python:

```bash
cd "$PROJECT_ROOT/clipper_python"
uv sync
uv run pytest
```

작업 전후 기본 확인:

```bash
git status -sb
git log -1 --oneline
git diff --check
```

## 9. Branch 운영 방식

현재 협업 기준은 `main`이다.

과거에는 `feature/initial-scaffold`, `feature/plugin-architecture`, `feature/windows-packaging`처럼 긴 작업 branch를 여러 repo에 걸쳐 사용했다. 이제부터는 각 task 단위 branch를 새로 만들고, 작업 완료 후 `main`에 merge한다.

기본 흐름:

```bash
cd "$PROJECT_ROOT/<repo>"
git switch main
git pull --ff-only
git switch -c feature/<task-name>
```

버그 수정 branch:

```bash
git switch -c fix/<short-bug-name>
```

권장 규칙:

- task가 닿는 repo에만 branch를 만든다.
- 여러 repo가 필요한 task라면 같은 branch 이름을 각 repo에 쓰면 추적이 쉽다.
- 작업 branch는 짧게 유지한다.
- 오래된 `feature/windows-packaging`, `feature/initial-scaffold`, `feature/plugin-architecture`를 새 작업 base로 재사용하지 않는다.
- merge 전에는 해당 repo에서 build/test를 통과시킨다.
- `.codex` 문서 변경은 `.codex` repo에서 별도 branch/commit으로 관리한다.

Merge 전 체크리스트:

```text
1. git status -sb 가 의도한 변경만 보여준다.
2. git diff --check 가 통과한다.
3. 변경 repo의 최소 build/test를 실행했다.
4. env secret 파일은 commit에 포함되지 않았다.
5. packaged 관련 변경이면 .env.local/.env.devapp을 packaged에 읽히거나 복사하지 않았다.
6. plugin별 고정 port env를 추가하지 않았다.
```

## 10. Env 파일 기준

실제 env 파일은 git에 commit하지 않는다. 각 repo의 `.env.example`을 참고해서 필요한 key만 실제 `.env.<mode>` 파일에 둔다.

공통 규칙:

- real `.env.<mode>` 파일에는 실제 값이 있는 key만 둔다.
- blank placeholder를 real env 파일에 남기지 않는다.
- OS별 env 파일을 만들지 않는다.
- `.env.local`은 개인 PC override가 아니라 browser local 실행 모드용 env다.
- `.env.devapp`은 unpackaged Electron 개발 앱 모드용 env다.
- `.env.packaged`는 설치형 앱 모드용 env다.
- `clipper_python`에는 Naver/Kakao image search key를 두지 않는다. Dance member image search owner는 NestJS다.

Env 파일 목록:

| File | 사용 모드 | Owner | 주요 내용 |
| --- | --- | --- | --- |
| `clipper_nestjs/.env.local` | `local` | NestJS | `NEST_PORT`, image search keys, plugin port range, Template Builder DB/S3 |
| `clipper_nestjs/.env.devapp` | `devapp` | NestJS | local과 같은 계열, devapp 실행용 |
| `clipper_nestjs/.env.packaged` | `packaged` | NestJS/Electron packaged resource | image search keys, plugin port range, Template Builder DB/S3 |
| `clipper_python/.env.local` | `local` | Python plugins | LLM proxy/subscription token 또는 local fallback `OPENAI_API_KEY` |
| `clipper_python/.env.devapp` | `devapp` | Python plugins | devapp plugin runtime credential |
| `clipper_python/.env.packaged` | `packaged` | Python plugins/Electron packaged resource | packaged plugin runtime credential |
| `clipper_electron/.env.devapp` | `devapp` | Electron | `CLIPPER_RENDERER_URL`, `CLIPPER_NEST_BASE_URL` |

만들지 않거나 사용하지 않는 파일:

```text
clipper_electron/.env.local
clipper_electron/.env.packaged
clipper_nestjs/.env
clipper_python/.env
root .env
```

허용되는 plugin port 설정:

```env
PLUGIN_PORT_RANGE_START=54800
PLUGIN_PORT_RANGE_END=54999
```

금지되는 방식:

```text
PLUGIN_URL_DIALOG_HIGHLIGHT=http://127.0.0.1:...
PLUGIN_URL_DANCE_HIGHLIGHT=http://127.0.0.1:...
plugin별 고정 port/url 나열
```

## 11. Notion Env 첨부 섹션

Notion에 실제 env 파일을 첨부할 때는 아래 슬롯을 사용한다. 이 문서 본문에는 secret 값을 붙여 넣지 않는다.

| 첨부 파일 | 필수 대상 | 비고 |
| --- | --- | --- |
| `clipper_nestjs/.env.local` | local 개발자 | 브라우저 local 실행 |
| `clipper_nestjs/.env.devapp` | Electron devapp 개발자 | devapp 실행 |
| `clipper_nestjs/.env.packaged` | packaged build 담당자 | Template Builder official DB 값 필수 |
| `clipper_python/.env.local` | local 개발자 | Python plugin local runtime |
| `clipper_python/.env.devapp` | Electron devapp 개발자 | Python plugin devapp runtime |
| `clipper_python/.env.packaged` | packaged build 담당자 | packaged Python plugin runtime |
| `clipper_electron/.env.devapp` | Electron devapp 개발자 | 보통 secret 없음 |

첨부/공유 시 주의:

- Notion page 권한을 실제 개발자에게만 제한한다.
- env 파일을 Slack/메신저 일반 채널에 평문으로 붙여 넣지 않는다.
- 값이 비어 있는 placeholder 파일을 배포하지 않는다.
- packaged build 담당자는 `.env.packaged`를 `.env.local`에서 복사해서 만들지 않는다. 필요한 key만 mode 기준으로 작성한다.

## 12. 새 팀원이 자주 헷갈리는 점

### Angular가 Python plugin을 직접 호출하나?

아니다. Angular는 NestJS API만 호출한다. plugin URL/port는 Angular가 몰라야 한다.

### Electron devapp은 packaged 앱인가?

아니다. `npm run start:devapp`은 Electron 창을 띄우지만 installer나 `.app` 산출물을 만들지 않는다. Angular/NestJS는 외부 dev server를 사용한다.

### packaged mode에서 NestJS port는 9019인가?

고정값이 아니다. Electron이 동적 port로 NestJS를 실행하고 renderer에 base URL을 알려준다.

### Python plugin은 언제 실행되나?

workflow/job이 필요로 할 때 NestJS 또는 packaged Electron host가 실행한다. 일반 개발 중에는 Python plugin을 수동으로 계속 띄워둘 필요가 없다.

### WorkflowExecutor와 PluginHost는 뭐가 다른가?

`WorkflowExecutor`는 NestJS의 `/jobs` 실행 단위다. Python plugin, NestJS-native executor, virtual workflow를 같은 plugin/job 모델로 묶는다. `PluginHost`는 그중 Python plugin process를 list/start/stop/status 하는 하위 계층이다.

### 새 plugin은 반드시 Python으로 만들어야 하나?

아니다. 영상 분석, 모델 inference, Python SDK가 필요한 작업은 Python plugin이 맞다. 반대로 간단한 ffmpeg 변환처럼 NestJS에서 직접 child process로 처리할 수 있고 Plugin Store/job history/start-stop 모델에 들어와야 하는 작업은 NestJS-native `WorkflowExecutor`로 만들 수 있다.

### Windows build에서 PowerToys는 꺼야 하나?

PowerToys 전체를 끌 필요는 없다. `Command Palette`는 끈다. `Keyboard Manager`는 사용해도 된다.

## 13. 추천 개발 루틴

일반 UI/API 작업:

```text
1. 관련 repo에서 main pull
2. task branch 생성
3. local 모드로 Angular/NestJS 실행
4. 필요한 테스트/build 실행
5. PR로 main merge
```

Electron IPC 또는 desktop integration 작업:

```text
1. clipper_electron 포함 task branch 생성
2. NestJS start:devapp
3. Angular start:devapp
4. Electron start:devapp
5. Electron build 또는 targeted smoke 확인
```

packaging/runtime 작업:

```text
1. packaged env가 정확히 준비되어 있는지 확인
2. npm run fetch-uv
3. target platform build:app 실행
4. 산출 앱을 터미널에서 실행해 로그 확인
5. health/template/plugin smoke 확인
```

문서 작업:

```text
1. .codex repo에서 별도 branch 생성
2. 관련 README/runbook/session record 수정
3. 앱 코드 repo commit과 분리
```
