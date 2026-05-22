# Clipper2 Execution Mode Runbook

작성일: 2026-05-21

## 목적

`local`, `devapp`, `packaged` 실행 모드별로 어떤 프로세스를 어떤 명령으로 실행하는지 정리한다.

이 문서는 실행 절차용이다. 실행 모드/env 설계 기준은 `../design/2026-05-21-execution-env-mode-design.md`를 우선한다.

## 모드 요약

| 모드 | 용도 | UI | NestJS | Python plugin | env |
| --- | --- | --- | --- | --- | --- |
| `local` | 브라우저 localhost 개발 | Angular dev server | 직접 실행 | NestJS가 필요 시 실행 | `.env.local` |
| `devapp` | 패키징하지 않은 Electron 앱 개발 | Electron + Angular dev server | 직접 실행 | NestJS가 필요 시 실행 | `.env.devapp` |
| `packaged` | 실제 설치형 앱 | 빌드된 Electron 앱 | Electron이 내부 실행 | Electron/NestJS가 관리 | `.env.packaged` |

공통 원칙:

- Angular는 plugin URL/port를 모른다.
- Angular는 NestJS API만 호출한다.
- Python plugin port는 runtime이 port range에서 동적으로 할당한다.
- packaged 앱은 `.env.local`, `.env.devapp`, generic `.env`를 읽거나 복사하지 않는다.
- secret env 파일은 git commit 대상이 아니다.
- OS별 `.env` 파일을 따로 만들지 않는다. 현재 checkout의 OS-independent `.env.*`를 다른 PC의 같은 상대 경로에 그대로 복사한다.

## 사전 조건

Node 기반 빌드/실행은 Node 22 기준으로 맞춘다.

```bash
source ~/.zshrc
nvm use 22
```

모드별 env 파일이 준비되어 있어야 한다.

```text
clipper_nestjs/.env.local
clipper_nestjs/.env.devapp
clipper_nestjs/.env.packaged
clipper_python/.env.local
clipper_python/.env.devapp
clipper_python/.env.packaged
clipper_electron/.env.devapp
```

실제 env 파일에는 값을 넣을 항목만 둔다. blank placeholder를 schema 맞춤 목적으로 남기지 않는다.

`clipper_electron`은 직접 소비하는 mode env가 `devapp`뿐이다. `packaged`에서는 Electron이 `clipper_nestjs/.env.packaged`, `clipper_python/.env.packaged`를 packaged resources에서 읽는다.

`clipper_nestjs/.env.packaged`에는 Template Builder official DB 연결값이 있어야 한다. packaged build preflight는 `CLIPPER2_TEMPLATE_DB_*` 누락 시 실패해야 한다.

표준 repo 배치에서는 `CLIPPER_PYTHON_ROOT` 같은 absolute path를 설정하지 않는다. NestJS dev runtime은 sibling `../clipper_python`을 찾고, packaged runtime은 bundled resources에서 Python root를 계산한다.

## Secret Env 복사

`.env.*` 파일은 git에 올리지 않는다. 새 PC에서 빌드하거나 smoke를 돌릴 때는 현재 기준 checkout의 ignored secret env 파일을 같은 상대 경로로 복사한다.

복사 대상:

```text
clipper_nestjs/.env.local
clipper_nestjs/.env.devapp
clipper_nestjs/.env.packaged
clipper_python/.env.local
clipper_python/.env.devapp
clipper_python/.env.packaged
clipper_electron/.env.devapp
```

복사하지 않는 파일:

```text
clipper_electron/.env.local
clipper_electron/.env.packaged
clipper_nestjs/.env
clipper_python/.env
root .env
```

현재 실제 env 파일의 key 구성:

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

중요한 점:

```text
Windows용 env를 따로 만들지 않는다.
Mac용 env를 따로 만들지 않는다.
경로값을 Windows에 맞게 고치는 절차가 있으면 설계가 잘못된 것이다.
표준 repo sibling checkout과 packaged resources 기준으로 코드가 경로를 계산해야 한다.
```

## `local` 실행

브라우저에서 Angular dev server를 직접 열어 개발할 때 사용한다. Electron은 실행하지 않는다.

터미널 1: NestJS

```bash
cd /Users/jina/project/adlight/clipper_nestjs
npm run start:local
```

터미널 2: Angular

```bash
cd /Users/jina/project/adlight/clipper_angular
npm run start:local
```

접속 URL은 보통 다음과 같다.

```text
http://localhost:4200
```

읽는 env:

```text
clipper_nestjs/.env.local
clipper_python/.env.local
```

프로세스 흐름:

```text
Browser Angular
-> NestJS API
-> Python plugin, 필요 시 NestJS LocalPluginHost가 동적 실행
```

## `devapp` 실행

패키징하지 않은 Electron shell에서 실제 desktop 앱 흐름을 확인할 때 사용한다.

터미널 1: NestJS

```bash
cd /Users/jina/project/adlight/clipper_nestjs
npm run start:devapp
```

터미널 2: Angular dev server

```bash
cd /Users/jina/project/adlight/clipper_angular
npm run start:devapp
```

터미널 3: Electron

```bash
cd /Users/jina/project/adlight/clipper_electron
npm run start:devapp
```

읽는 env:

```text
clipper_nestjs/.env.devapp
clipper_python/.env.devapp
clipper_electron/.env.devapp
```

`clipper_electron/.env.devapp`의 핵심 값:

```env
CLIPPER_RENDERER_URL=http://localhost:4200
CLIPPER_NEST_BASE_URL=http://127.0.0.1:9019/v1
```

`clipper_electron/.env.devapp`에는 Python root나 plugin URL을 넣지 않는다. devapp Electron은 renderer URL과 NestJS base URL만 알아야 한다.

프로세스 흐름:

```text
Electron devapp
-> Angular dev server를 BrowserWindow에 로드
-> 외부에서 실행 중인 NestJS API 호출
-> Python plugin, 필요 시 NestJS LocalPluginHost가 동적 실행
```

## `packaged` 빌드

실제 설치형 앱을 만들 때 사용한다.

Mac ARM64:

```bash
cd /Users/jina/project/adlight/clipper_electron
source ~/.zshrc
nvm use 22
npm run build:app:mac:arm64
```

Mac x64:

```bash
cd /Users/jina/project/adlight/clipper_electron
source ~/.zshrc
nvm use 22
npm run build:app:mac:x64
```

Windows x64:

```powershell
cd C:\path\to\adlight\clipper_electron
node -v
npm run build:app:win:x64
```

Windows에서도 Node 22를 사용한다. `node -v`가 22가 아니면 Windows에서 사용하는 Node version manager로 먼저 22를 선택한다.

Windows에서 Microsoft PowerToys를 사용하는 경우, 빌드 중에는 `Command Palette`를 비활성화한다. `Command Palette`의 `Microsoft.CmdPal.UI.exe`가 새로 생성된 `dist-app\win-unpacked\Clipper2.exe`를 감지/매핑하면, electron-builder가 같은 exe에 ASAR integrity 리소스를 쓰는 순간 `EBUSY` / `SHARING VIOLATION`이 발생할 수 있다. `Keyboard Manager`만 필요한 경우에는 PowerToys 전체를 끄지 말고 `Command Palette` 기능만 끈다.

빌드 과정:

```text
Angular build:packaged
-> NestJS bundle
-> Electron TypeScript build
-> uv binary 준비
-> electron-builder packaging
```

packaged build가 포함해야 하는 env:

```text
clipper_nestjs/.env.packaged
clipper_python/.env.packaged
```

packaged build가 포함하면 안 되는 env:

```text
.env.local
.env.devapp
.env
```

## `packaged` 실행

Mac ARM64 빌드 결과를 터미널에서 실행하면 로그를 직접 볼 수 있다.

```bash
cd /Users/jina/project/adlight/clipper_electron
./dist-app/mac-arm64/Clipper2.app/Contents/MacOS/Clipper2
```

Finder 방식으로 실행할 수도 있다.

```bash
cd /Users/jina/project/adlight/clipper_electron
open dist-app/mac-arm64/Clipper2.app
```

packaged runtime 흐름:

```text
Electron packaged app
-> 내부 NestJS 실행
-> NestJS ready URL을 Electron/renderer에 전달
-> Python plugin은 필요 시 실행
-> plugin port는 port range에서 동적 할당
```

packaged에서는 NestJS port가 고정값이 아니다. 터미널 실행 로그에서 다음 형태를 확인한다.

```text
[NestManager] ready at http://127.0.0.1:<port>/v1
```

## 직접 NestJS packaged smoke

Electron packaged runtime을 대체하는 공식 실행 방식은 아니다. NestJS bundle/env 확인용 smoke로만 사용한다.

```bash
cd /Users/jina/project/adlight/clipper_nestjs
npm run build
npm run start:packaged
```

실제 packaged 앱에서는 Electron이 NestJS port와 desktop bridge 값을 주입한다.

## 빌드 전용 명령

Angular:

```bash
cd /Users/jina/project/adlight/clipper_angular
npm run build:local
npm run build:devapp
npm run build:packaged
```

NestJS:

```bash
cd /Users/jina/project/adlight/clipper_nestjs
npm run build
npm run bundle
```

Electron TypeScript:

```bash
cd /Users/jina/project/adlight/clipper_electron
npm run build
```

## Smoke 확인

`local` 또는 `devapp`에서 NestJS가 `9019`로 실행 중이면 다음으로 확인한다.

```bash
curl -s http://127.0.0.1:9019/v1/health
```

`packaged`에서는 로그에 출력된 동적 port를 사용한다.

```bash
curl -s http://127.0.0.1:<port>/v1/health
```

Dance member image search 경로를 확인하려면 NestJS API를 확인해야 한다. 현재 이미지 검색 key owner는 Python plugin이 아니라 NestJS다.

## 자주 헷갈리는 점

`.env.local`은 개인 PC override가 아니다. 브라우저 localhost 개발 모드의 env다.

`.env.devapp`은 패키징하지 않은 Electron 앱 개발 모드의 env다.

`.env.packaged`는 실제 설치형 앱 실행 모드의 env다.

`clipper_python`의 Naver/Kakao key는 현재 필요 없다. member image search는 NestJS image search API가 담당한다.

Electron `devapp`은 renderer URL과 NestJS base URL만 받아서 외부 개발 서버들을 연결한다.

Electron `packaged`는 NestJS를 내부 프로세스로 실행하고, bundled resources의 `.env.packaged`만 사용한다.
